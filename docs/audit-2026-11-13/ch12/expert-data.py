"""Independent replay of August forecasts, staffing, as-of cuts and stationarity."""
import importlib.util
from pathlib import Path
import random
import tempfile

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from statsmodels.tsa.stattools import adfuller

ROOT = Path(__file__).resolve().parents[3]
datafile = ROOT / "site/data/app_orders.csv"
spec = importlib.util.spec_from_file_location("generator", ROOT / "tools/gen_data.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
with tempfile.TemporaryDirectory() as tmp:
    generator.OUT = Path(tmp)
    generator.gen_chapter12(random.Random(12012))
    assert (generator.OUT / datafile.name).read_bytes() == datafile.read_bytes()

s = pd.read_csv(datafile,parse_dates=["datetime"]).set_index("datetime")["orders"]
assert s.index.equals(pd.date_range(s.index.min(),s.index.max(),freq="h")) and not s.isna().any()
days = pd.to_datetime(["2026-04-17","2026-05-22","2026-06-19","2026-07-24","2026-08-21"])
print("bounds, total, min/max, zero",s.index[[0,-1]], s.sum(), s.min(),s.max(),(s==0).sum())
print("daily grow, ACF 1/24/168",s.resample("MS").mean().round(2).to_dict(),[round(s.autocorr(k),3) for k in [1,24,168]])
print("outage hours",s["2026-06-03 12":"2026-06-03 16"].tolist())
aug = s["2026-08"]
print("ADF p-values August raw, seasonal diff, aggregated daily",[adfuller(series)[1] for series in (aug,aug.diff(24).dropna(),s.resample("D").sum())])
rng=np.random.default_rng(77)
seasonal=np.tile([0.,10.,20.,10.],180)+rng.normal(0,.3,720)
print("nonconstant periodic mean and ADF default", np.round([seasonal[j::4].mean() for j in range(4)],2),adfuller(seasonal)[1])
def features(series):
    df = pd.DataFrame(index=series.index)
    df["hour"] = series.index.hour
    df["dow"] = series.index.dayofweek
    df["weekend"] = (df.dow >= 5).astype(int)
    df["promo"] = (series.index.normalize().isin(days) & df.hour.between(10,20)).astype(int)
    for lag in [48,168]:
        df[f"lag_{lag}"] = series.shift(lag)
    df["roll"] = series.shift(28).rolling(24).mean()
    weeks = pd.concat([series.shift(168*k) for k in range(1,5)],axis=1)
    df["mean4w"] = weeks.mean(axis=1)
    return df

X = features(s).dropna()
y = s.loc[X.index]
march_june = X.index < "2026-07-01"
july = (X.index >= "2026-07-01") & (X.index < "2026-08-01")
train = X.index < "2026-08-01"
test = ~train
print("model rows and 1–3 vs 4 weeks", march_june.sum(), july.sum(), test.sum(),(X.index<s.index[0]+pd.Timedelta(weeks=4)).sum())
aug_dates = X.index[test].normalize().unique()
for day in aug_dates:
    target = X.index.normalize()==day
    last_known = day - pd.Timedelta(hours=5)
    obscured = s.mask(s.index>last_known,-100000)
    np.testing.assert_allclose(features(obscured).loc[X.index[target]], X[target])
print("prefix invariant, days",len(aug_dates))

def reg(**kw):
    return HistGradientBoostingRegressor(random_state=0,**kw)
for name, model in [("LR", LinearRegression()),("HGB", reg()),("depth3",reg(max_depth=3)),("l2",reg(l2_regularization=1.0))]:
    pred = model.fit(X[march_june],y[march_june]).predict(X[july])
    print("July RMSE", name,root_mean_squared_error(y[july],pred))
search = GridSearchCV(reg(), {"max_depth":[2,3,None],"learning_rate":[.05,.1]},
                      cv=TimeSeriesSplit(n_splits=3), scoring="neg_root_mean_squared_error")
search.fit(X[train],y[train])
print("course grid",search.best_params_,-search.best_score_)
for a,b in search.cv.split(X[train]):
    first = X.index[b[0]]
    last_known = first.normalize()-pd.Timedelta(hours=5)
    print("first valid, last training, rows after decision",first,X.index[a[-1]],(X.index[a]>last_known).sum())

# Construct folds on whole days; trim labels unavailable for the first forecast of each fold.
days_train=X[train].index.normalize().unique()
legal_folds=[]
for a,b in TimeSeriesSplit(n_splits=3).split(days_train):
    first,last=days_train[b[0]],days_train[b[-1]]
    fit=X.index[train] <= first-pd.Timedelta(hours=5)
    val=(X.index[train].normalize()>=first)&(X.index[train].normalize()<=last)
    legal_folds.append((np.flatnonzero(fit),np.flatnonzero(val)))
search.set_params(cv=legal_folds).fit(X[train],y[train])
print("as-of day-grid",search.best_params_,-search.best_score_)
params = {"learning_rate":.05,"max_depth":3}
ref=reg(**params).fit(X[train],y[train])
p=np.maximum(0,ref.predict(X[test]))
before_first = X.index <= pd.Timestamp("2026-07-31 19")
p_fair=np.maximum(0,reg(**params).fit(X[before_first],y[before_first]).predict(X[test]))
print("RMSE published, fit as of first issue, baseline; MAE published",
      root_mean_squared_error(y[test],p),root_mean_squared_error(y[test],p_fair),
      root_mean_squared_error(y[test],X[test].mean4w),mean_absolute_error(y[test],p))
print("first-day RMSE",root_mean_squared_error(y[test].iloc[:24],p[:24]),root_mean_squared_error(y[test].iloc[:24],p_fair[:24]))
truth=y[test]
work=truth.index.hour.isin(range(7,23))
q=np.maximum(0,reg(loss="quantile",quantile=.8,**params).fit(X[train],y[train]).predict(X[test]))
def staff(p):
    return np.ceil(np.maximum(p,1)/6).astype(int)
def staff_stats(pred):
    plan=staff(pred)[work]
    actual=staff(truth.to_numpy())[work]
    return {"short_hours":int((plan<actual).sum()),"missing_staff_hours":int(np.maximum(actual-plan,0).sum()),
            "extra_staff_hours":int(np.maximum(plan-actual,0).sum()),
            "capacity_gap_orders":int(np.maximum(truth.to_numpy()[work]-6*plan,0).sum())}
for name,pred in [("baseline",X[test].mean4w),("mean",p),("q80",q)]:
    print("schedule",name,staff_stats(np.asarray(pred)))
by_group=pd.DataFrame({"covered":truth<=q,"short":staff(q)<staff(truth),"n":1},index=truth.index)
print("q80 coverage all/open",by_group.covered.mean(),by_group[work].covered.mean())
for name,key in [("hour",truth.index.hour),("weekday",truth.index.dayofweek)]:
    gr=by_group[work].groupby(key[work]).agg(n=("n","sum"),covered=("covered","mean"),short=("short","mean"))
    print(name,gr.round(3).to_string())
print("promo 11 hours", by_group[X[test].promo==1].agg({"covered":"mean","short":"mean","n":"sum"}).to_dict())
print("quantile example", np.mean([12,14,15,15,16,17,18,19,21,24]),np.quantile([12,14,15,15,16,17,18,19,21,24],.8))

# A lead at t+1 depends exclusively on hidden data, while changing only y[t] leaves it unchanged.
t=pd.Timestamp("2026-07-15 12")
for corrupt in [t,t+pd.Timedelta(hours=1)]:
    perturbed=s.copy()
    perturbed.loc[corrupt]+=1000
    print("future lead test, corrupt",corrupt,"changed at t",s.shift(-1).loc[t]!=perturbed.shift(-1).loc[t])

# Every seasonal baseline below is operationally available at 20:00 before the target day.
for k in (1,2,4,8,12):
    hist=pd.concat([s.shift(168*j) for j in range(1,k+1)],axis=1)
    baseline=hist.mean(axis=1,skipna=False)
    print("seasonal weeks, July, August",k,root_mean_squared_error(y[july],baseline.loc[y[july].index]),
          root_mean_squared_error(truth,baseline.loc[truth.index]))
    if k==8:
        print("8-week staff",staff_stats(baseline.loc[truth.index].to_numpy()))
partial = pd.concat([s.shift(168*j) for j in range(1,5)],axis=1)
print("number of historical weeks used in training feature",partial.reindex(X[march_june].index).count(axis=1).value_counts().sort_index().to_dict())
# Resample entire days to illustrate (paired) monthly RMSE uncertainty; weekdays and serial correlation constrain inference.
block_loss=pd.DataFrame({"m":(truth-p)**2,"b":(truth-X[test].mean4w)**2}).groupby(truth.index.normalize()).sum()
ix=np.random.default_rng(77).integers(0,len(block_loss),size=(5000,len(block_loss)))
paired=np.sqrt(block_loss.m.to_numpy()[ix].sum(1)/len(truth))-np.sqrt(block_loss.b.to_numpy()[ix].sum(1)/len(truth))
print("paired whole-day bootstrap sensitivity, RMSE diff 2.5–97.5%",np.quantile(paired,[.025,.975]))
