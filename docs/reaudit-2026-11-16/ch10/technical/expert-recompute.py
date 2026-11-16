"""Run from the course root on its single-threaded scientific Python."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"

import contextlib
import hashlib
import io
import json
import platform
import random
import sys
import tempfile
from pathlib import Path
from importlib.metadata import version

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import root_mean_squared_error as rmse, mean_absolute_error as mae
from threadpoolctl import threadpool_limits

root = Path.cwd()
sys.path.insert(0, str(root / "tools"))
import gen_data
data = root / "site/data"
result = {"versions": {p: version(p) for p in ["numpy", "pandas", "scikit-learn", "scipy"]}, "python": platform.python_version()}
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
    gen_data.OUT = Path(tmp)
    for file, func, seed, key in [
        ("deliveries", gen_data.gen_chapter4, 4004, ["delivery_id"]),
        ("guests_churn", gen_data.gen_chapter6, 6006, ["guest_id"]),
        ("daily_sales", gen_data.gen_chapter10, 10010, ["shop_id", "date"])]:
        func(random.Random(seed))
        name = file + ".csv"
        df = pd.read_csv(data / name)
        result[file] = {"rows": len(df), "duplicate_key": int(df.duplicated(key).sum()),
                        "missing": {c: int(df[c].isna().sum()) for c in df if df[c].isna().any()},
                        "sha256": digest(data / name), "generated_equal": digest(data / name) == digest(Path(tmp) / name)}

d = pd.read_csv(data / "deliveries.csv")
ok = d[d.actual_min.between(1,299)].copy()
ok["walk"] = (ok.courier == "пеший").astype(int)
def threshold(group):
    t = next(t for t in range(300) if (group.actual_min.gt(t)).mean() <= .1)
    return [t, int(group.actual_min.gt(t-1).sum()), int(group.actual_min.gt(t).sum()), len(group)]
result["deliveries"].update(period=[d.created.min(), d.created.max()], valid=len(ok),
                           sla={"all": threshold(ok), **{k:threshold(g) for k,g in ok.groupby("courier")}})
g = pd.read_csv(data / "guests_churn.csv")
result["guests_churn"].update(events=int(g.churned.sum()), no_visits=int(g.visits_90d.eq(0).sum()))
x = np.array([1,2,3,4.5,6])
y = np.array([18,25,34,44,55])
loss = lambda w: float(np.mean((w*x-y)**2))
grad = lambda w: float(np.mean(2*(w*x-y)*x))
opt = np.dot(x,y)/np.dot(x,x)
w = 0.
steps = []
for _ in range(3):
    w -= .01*grad(w)
    steps.append([w, loss(w)])
result["scalar"] = {"opt":opt, "MSE_min":loss(opt), "L0":loss(0), "L5":loss(5), "g5":grad(5), "g0":grad(0), "steps":steps,
                    "tiny_lr_loss_delta":loss(0)-loss(-1e-12*grad(0))}
features = ok[["distance_km","items","walk","amount"]].to_numpy()
std = (features - features.mean(axis=0))/features.std(axis=0)
Y = ok.actual_min
for name, X in [("raw",features), ("scaled",std)]:
    mat = np.column_stack([np.ones(len(ok)), X])
    ev = np.linalg.eigvalsh(2*mat.T@mat/len(ok))
    result[name] = dict(max_lr=2/ev[-1], condition=ev[-1]/ev[0])
rr = Ridge(alpha=len(Y)).fit(std,Y)
result["ridge"] = [rr.intercept_,np.linalg.norm(rr.coef_),np.mean((Y-rr.predict(std))**2)]
s = pd.read_csv(data / "daily_sales.csv",parse_dates=["date"]).sort_values(["shop_id","date"]).reset_index(drop=True)
s["weekday"] = s.date.dt.weekday
s["month"] = s.date.dt.month
s["weekend"] = s.weekday.ge(5).astype(int)
s["day_n"] = (s.date-pd.Timestamp("2024-01-01")).dt.days
def prep(s, issued):
    df = s.copy()
    prev = df.date.lt(issued)
    for key in ["rain","temp"]:
        df[key] = df[key].astype(float)
        df.loc[~prev,key] = df.loc[~prev,"month"].map(df[prev].groupby("month")[key].mean())
    return pd.get_dummies(df[["temp","rain","holiday","promo","weekday","month","weekend","day_n","shop_id","format"]], columns=["shop_id","format"],dtype=int)
a = "2025-04-01"
j = "2025-07-01"
fit = s.date.lt(a)
train = s.date.lt(j)
val = train & ~fit
test = ~train
Y = s.revenue_k
result["daily_sales"].update(period=[str(s.date.min().date()),str(s.date.max().date())], shops=s.shop_id.nunique(), cities=s.city.nunique(), days=s.date.nunique(), masks=[int(m.sum()) for m in [fit,val,test]],
                            promo_test=int(s.loc[test,"promo"].sum()))
def pivot(source):
    return {fmt: [round(row[0],2),round(row[1],2)] for fmt,row in source.groupby(["format","weekend"]).revenue_k.mean().unstack().iterrows()}
changed=s.copy()
changed.loc[test & changed.weekend.eq(1) & changed["format"].eq("бизнес-центр"),"revenue_k"] += 1000
result["look"] = {"before_april":pivot(s[fit]),"full":pivot(s), "changed_future_full":pivot(changed),
                  "changed_future_pre_april_equal":pivot(changed[fit])==pivot(s[fit])}
source=s[train].groupby(["shop_id","weekday"],sort=False).tail(1).set_index(["shop_id","weekday"])
p=s[test][["shop_id","weekday"]].join(source.revenue_k,on=["shop_id","weekday"]).revenue_k
result["baseline"]={"issued_mae":mae(Y[test],p),"issued_rmse":rmse(Y[test],p), "rolling_mae":mae(Y[test],Y.groupby(s.shop_id).shift(7)[test]),
                    "rolling_source_after_issue":int((s.loc[test,"date"]-pd.Timedelta(days=7)).ge(j).sum())}
dev=prep(s,a)
final=prep(s,j)
mut=s.copy()
mut.loc[test,["temp","rain","revenue_k"]]=[90,0,999]
result["asof"]={"dev_input_equal":prep(mut,a).equals(dev), "final_input_equal":prep(mut,j).equals(final)}
result["release_row"]=s.loc[(s.shop_id=="PRM-1") & (s.date=="2025-07-25"),"revenue_k"].item()
def scores(true,pred):
    return {"MAE":mae(true,pred), "RMSE":rmse(true,pred)}
with threadpool_limits(1):
    grid=[]
    for lr in [.05,.1]:
        for depth in [3,6,None]:
            probe=HGB(learning_rate=lr,max_depth=depth,max_iter=500,early_stopping=False,random_state=0).fit(dev[fit],Y[fit])
            curve=np.array([mae(Y[val],p) for p in probe.staged_predict(dev[val])])
            k=curve.argmin()
            grid.append({"lr":lr,"depth":depth,"k":int(k+1),"val_MAE":curve[k]})
    best=min(grid,key=lambda r:r["val_MAE"])
    result["tune"]=grid
    result["candidate"]={}
    for name,params in [("default",{}),("tuned",dict(learning_rate=best["lr"],max_depth=best["depth"],max_iter=best["k"]))]:
        row={}
        for key,x,tr,te in [("apr",dev,fit,val),("jul",final,train,test)]:
            p=HGB(**params,random_state=0).fit(x[tr],Y[tr]).predict(x[te])
            row[key]=scores(Y[te],p)
            if key=="jul":
                row["dec_avg"]=np.mean(p[s.loc[te,"month"]==12])
        result["candidate"][name]=row
    for key,x,tr,te in [("apr",dev,fit,val),("jul",final,train,test)]:
        z=x.copy()
        off=(z.weekend+z.holiday).gt(0)
        z["bc_off"]=z["format_бизнес-центр"]*off
        z["mall_off"]=z["format_ТЦ"]*off
        z["street_rain"]=z["format_улица"]*z.rain
        result["candidate"].setdefault("linear_interactions",{})[key]=scores(Y[te],LinearRegression().fit(z[tr],Y[tr]).predict(z[te]))
        level=np.exp(LinearRegression().fit(x.loc[tr,["day_n"]],np.log(Y[tr])).predict(x[["day_n"]]))
        m=HGB(random_state=0).fit(x[tr].drop(columns="day_n"),Y[tr]/level[tr])
        p=m.predict(x[te].drop(columns="day_n"))*level[te]
        result["candidate"].setdefault("trend",{})[key]=scores(Y[te],p)
        if key=="jul":
            result["candidate"]["trend"]["dec_avg"]=np.mean(p[s.loc[te,"month"]==12])
    for n in [255,256]:
        X=pd.DataFrame({"shop":pd.Series([str(i) for i in range(n)],dtype="category")})
        try:
            HGB(max_iter=1,categorical_features="from_dtype").fit(X,np.arange(n))
            verdict="fit OK"
        except ValueError as exc:
            verdict=str(exc)
        result.setdefault("category",{})[n]=verdict
print(json.dumps(result,ensure_ascii=False,indent=2))
