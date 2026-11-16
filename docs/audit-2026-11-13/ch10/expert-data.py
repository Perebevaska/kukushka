"""Reproduce chapter 10 and check the native notebook with --native (requires CatBoost and LightGBM)."""
from contextlib import chdir
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site/data"

if "--native" in sys.argv:
    notebook = ROOT / "site/notebooks/extra/ch10-catboost-lightgbm.ipynb"
    ns = {}
    with chdir(notebook.parent):
        for i, cell in enumerate(json.loads(notebook.read_text())["cells"]):
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                exec(compile(source, f"native-cell-{i}", "exec"),ns)
    print("native final", ns["rows"])
    sys.exit()

spec = importlib.util.spec_from_file_location("generator", ROOT / "tools/gen_data.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
with tempfile.TemporaryDirectory() as tmp:
    generator.OUT = Path(tmp)
    for chapter, seed, name in [(4,4004,"deliveries"),(6,6006,"guests_churn"),(10,10010,"daily_sales")]:
        getattr(generator, f"gen_chapter{chapter}")(random.Random(seed))
        assert (generator.OUT / f"{name}.csv").read_bytes() == (DATA / f"{name}.csv").read_bytes()

d = pd.read_csv(DATA / "deliveries.csv")
d = d[d.actual_min.between(1,299)].copy()
km = np.array([1.,2.,3.,4.5,6.])
minutes = np.array([18,25,34,44,55])
w = np.dot(km,minutes) / np.dot(km,km)
print("1D optimum, grad, true late share at 48", w,np.mean(2*(w*km-minutes)*km), (d.actual_min > 48).mean())
for courier, part in d.groupby("courier"):
    series = part.actual_min
    t = next(k for k in range(301) if (series>k).mean() <= .1)
    print("SLA minute/share at t and t-1",courier,t,round((series>t).mean(),4),round((series>t-1).mean(),4))
x = d[["distance_km","items"]].assign(walk=d.courier.eq("пеший").astype(int)).to_numpy()
x = np.column_stack([np.ones(len(x)), (x-x.mean(axis=0))/x.std(axis=0)])
y = d.actual_min.to_numpy()
hessian = 2*x.T@x/len(x)
print("batch MSE alpha max",2/np.linalg.eigvalsh(hessian).max())
w = np.array([2.,-1.,3.,.5])
reg = .25
loss = lambda weights: np.mean((x@weights-y)**2)+reg*(weights[1:]@weights[1:])
analytic = 2*x.T@(x@w-y)/len(x) + 2*reg*np.r_[0,w[1:]]
eps = 1e-5
fd = np.array([(loss(w+eps*e)-loss(w-eps*e))/(2*eps) for e in np.eye(len(w))])
print("finite-difference penalized gradient max error",np.max(np.abs(fd-analytic)))
# At step 1 bias correction gives mhat=g, vhat=g**2.
g = np.array([1.,-4.,0.])
print("first Adam step, lr=.1", -0.1*g/(np.abs(g)+1e-8))

# Reconstruct squared-loss boosting using the mean as a constant starting model.
delivery_features = d.assign(hour=pd.to_datetime(d.created).dt.hour)
delivery_x = pd.get_dummies(delivery_features[["distance_km","items","hour","courier","weather","shop_id"]],dtype=int)
tx, vx, ty, vy = train_test_split(delivery_x, d.actual_min, test_size=.25, random_state=42)
ft = np.full(len(ty),ty.mean())
fv = np.full(len(vy),ty.mean())
for _ in range(50):
    tree = DecisionTreeRegressor(max_depth=3,random_state=0).fit(tx,ty-ft)
    ft = ft + .1*tree.predict(tx)
    fv = fv + .1*tree.predict(vx)
compiled = GradientBoostingRegressor(n_estimators=50,max_depth=3,learning_rate=.1,random_state=0).fit(tx,ty).predict(vx)
print("hand boost vs sklearn MAE, corr", mean_absolute_error(vy,fv),mean_absolute_error(vy,compiled),np.corrcoef(fv,compiled)[0,1])
s = pd.read_csv(DATA / "daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id","date"]).reset_index(drop=True)
assert not s.isna().any().any() and not s.duplicated(["date","shop_id"]).any()
print("data",s.date.min(),s.date.max(),s.shop_id.nunique(),s.date.nunique(),len(s))
print("range, mean, reporting branches",s.revenue_k.agg(["min","max","mean"]).to_dict(),s.groupby("format").shop_id.nunique().to_dict())
EPOCH = s.date.min()

def prepare(frame):
    features = frame[["temp","rain","promo","holiday","shop_id","format"]].copy()
    features["weekday"] = frame.date.dt.weekday
    features["month"] = frame.date.dt.month
    features["weekend"] = (features.weekday >= 5).astype(int)
    features["day_n"] = (frame.date - EPOCH).dt.days
    canonical = ["temp","rain","holiday","promo","weekday","month","weekend","day_n","shop_id","format"]
    return pd.get_dummies(features[canonical], columns=["shop_id","format"], dtype=int)


x = prepare(s)
y = s.revenue_k
fit = s.date < "2025-04-01"
tr = s.date < "2025-07-01"
val = tr & ~fit
te = ~tr
print("sizes fit,val,test",fit.sum(),val.sum(),te.sum())
print("weekend ratios", (s.groupby(["format",s.date.dt.weekday>=5]).revenue_k.mean().unstack().pipe(lambda t:t[True]/t[False])).round(3).to_dict())

def metrics(true, pred):
    return np.round([mean_absolute_error(true,pred),root_mean_squared_error(true,pred),np.mean(true-pred)],4)


lag = s.groupby("shop_id").revenue_k.shift(7)
# A fixed forecast origin has only the last week's actual revenue. Each later weekly value repeats recursively.
last_week = s[tr & (s.date>=pd.Timestamp("2025-06-24"))].copy()
last_week["weekday"] = last_week.date.dt.weekday
fixed = s[te].assign(weekday=s.loc[te,"date"].dt.weekday).merge(last_week[["shop_id","weekday","revenue_k"]],
                       on=["shop_id","weekday"],suffixes=("","_prior"))
print("lag7, daily rolling vs fixed June origin, test rows using later labels",metrics(y[te],lag[te]),
      metrics(fixed.revenue_k,fixed.revenue_k_prior),((s.date-pd.Timedelta(days=7)>=pd.Timestamp("2025-07-01"))&te).sum())
base = {}
for name,model in [("linear",LinearRegression()),("forest",RandomForestRegressor(n_estimators=100,min_samples_leaf=3,random_state=0)),
                   ("GB",GradientBoostingRegressor(random_state=0)),("HGB",HistGradientBoostingRegressor(random_state=0))]:
    pred = model.fit(x[tr],y[tr]).predict(x[te])
    base[name] = pred
    print(name,"MAE/RMSE/bias",metrics(y[te],pred))

x2 = x.copy()
off = (x2.weekend+x2.holiday>0).astype(int)
x2["bc_off"] = x2["format_бизнес-центр"]*off
x2["mall_off"] = x2["format_ТЦ"]*off
x2["street_rain"] = x2["format_улица"]*x2.rain
print("linear + interactions",metrics(y[te],LinearRegression().fit(x2[tr],y[tr]).predict(x2[te])))

rows = []
for lr in [.05,.1]:
    for depth in [3,6,None]:
        model = HistGradientBoostingRegressor(learning_rate=lr,max_depth=depth,max_iter=500,early_stopping=False,random_state=0).fit(x[fit],y[fit])
        scores = [mean_absolute_error(y[val],p) for p in model.staged_predict(x[val])]
        idx = int(np.argmin(scores))
        rows.append((scores[idx],lr,depth,idx+1))
best,lr,depth,k = min(rows,key=lambda r:r[0])
tuned = HistGradientBoostingRegressor(learning_rate=lr,max_depth=depth,max_iter=k,early_stopping=False,random_state=0).fit(x[tr],y[tr])
print("validation winner, test",best,lr,depth,k,metrics(y[te],tuned.predict(x[te])))

trend_lr = LinearRegression().fit(x.loc[tr,["day_n"]],np.log(y[tr]))
trend = np.exp(trend_lr.predict(x[["day_n"]]))
features = x.drop(columns="day_n")
model = HistGradientBoostingRegressor(random_state=0).fit(features[tr],(y/trend)[tr])
p = model.predict(features[te])*trend[te]
print("trend growth, MAE/RMSE/bias and MAE/mean",np.exp(trend_lr.coef_[0]*365),metrics(y[te],p),np.mean(np.abs(y[te]-p))/y[te].mean())
# Scenario errors shared by coffee shops in one city/date. This is not archived meteorological data.
scenario = s.loc[te].copy()
city_day = scenario[["city","date"]].drop_duplicates().copy()
rng = np.random.default_rng(42)
city_day["temp_err"] = rng.normal(0,3,len(city_day))
city_day["rain_flip"] = rng.random(len(city_day)) < .2
scenario = scenario.merge(city_day,on=["city","date"],validate="many_to_one")
scenario.temp += scenario.temp_err
scenario.rain = scenario.rain.astype(bool).ne(scenario.rain_flip).astype(int)
p2 = model.predict(prepare(scenario).drop(columns="day_n"))*trend[te]
print("scenario temperature sigma=3 and 20% flipped rain, MAE/RMSE/bias",metrics(y[te],p2))

# Consequence of recomputing the epoch on a fresh batch, as in the published prep function.
x_new = x.loc[te].copy()
x_new.day_n -= x_new.day_n.min()
m = LinearRegression().fit(x[tr],y[tr])
print("batch local day_n: correct vs reset first day and mean absolute prediction change",
      x.loc[te,"day_n"].iloc[0],x_new.day_n.iloc[0],np.mean(np.abs(m.predict(x.loc[te])-m.predict(x_new))))
