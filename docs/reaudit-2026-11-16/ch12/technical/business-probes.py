"""Native, one process. Run with cwd at the repo root and four BLAS/OpenMP threads set to 1."""
from datetime import date, datetime, time, timedelta
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import sys

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[name] = "1"
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "data-baseline/app_orders.csv"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == "53c3351867d2c2bbf8decdd70daba5aa7eea2b5010154c52a115e29810666235"
HOUR = timedelta(hours=1)
END = datetime(2026, 7, 31, 20)
JUNE = datetime(2026, 6, 30, 20)
AUG = datetime(2026, 8, 1)
PROMO = {date(2026, m, d) for m, d in [(4,17),(5,22),(6,19),(7,24),(8,21)]}
with SOURCE.open() as f:
    observed = {datetime.fromisoformat(row["datetime"]): int(row["orders"]) for row in csv.DictReader(f)}

def issued(t):
    return datetime.combine(t.date() - timedelta(days=1), time(20))

def row(t, full_history, august_promo):
    weeks = [168 * n for n in range(1, 5) if t-168*n*HOUR in observed]
    if t-168*HOUR not in observed or (full_history and len(weeks) < 4):
        return None
    for k in [48, 168, *weeks, *range(28, 52)]:
        assert t-k*HOUR < issued(t)
    return [t.hour,t.weekday(),int(t.weekday()>=5),int(t.date() in PROMO and (august_promo or t.month!=8) and 10<=t.hour<=20),
            observed[t-48*HOUR],observed[t-168*HOUR],
            sum(observed[t-k*HOUR] for k in range(28,52))/24,
            sum(observed[t-k*HOUR] for k in weeks)/len(weeks)]

def staffing(x, c, open_now):
    return max(1, math.ceil(x/c)) if open_now else 0

def metrics(ts, obs, forecasts, c):
    off = deficit = excess = covered = working = all_cover = sq = paid = 0
    for t, fact, p in zip(ts, obs, forecasts, strict=True):
        sq += (fact-p)**2
        all_cover += int(fact<=p)
        if not 7<=t.hour<=22:
            continue
        working += 1
        nd, pl = staffing(fact,c,True), staffing(p,c,True)
        paid += pl
        covered += int(fact<=p)
        off += int(nd>pl)
        deficit += max(0,nd-pl)
        excess += max(0,pl-nd)
    return dict(rmse=(sq/len(ts))**0.5, all_cover=all_cover, forecast_cover=covered, working=working,
                short=off, adequate=working-off, deficit=deficit, extra=excess, planned_hours=paid,
                cost4=4*deficit+excess, cost1_5=1.5*deficit+excess)

assert staffing(0,6,True)==1 and staffing(0,6,False)==0
assert [staffing(i,6,True) for i in [7,11,6,7]]==[2,2,1,2]
assert [staffing(2,6,7<=h<=22) for h in [6,7,22,23]]==[0,1,1,0]
# One operator per five-hour shift; excess and shortages cannot cancel across or within shifts.
center = [(h, 2 if h in (8,9,14,18,19) else 1, 1) for h in range(8,20)]
assert [h for h,need,p in center if 9<=h<19 and p<need]==[9,14,18]
assert sum(max(0,need-p) for h,need,p in center if 9<=h<19)==3
result = dict(sklearn=sklearn.__version__,numpy=np.__version__,python=sys.version.split()[0])
with (HERE.parent/"student/native-august-predictions.csv").open() as f:
    student = list(csv.DictReader(f))
for full,august_promo,label in [(False,True,"course"),(True,True,"full4"),(True,False,"student"),(False,False,"partial_no_august_promo")]:
    features = {t:r for t in observed if (r:=row(t,full,august_promo)) is not None}
    train = [t for t in features if t<END]
    jul = [t for t in features if datetime(2026,7,1)<=t<END]
    test = [t for t in features if t>=AUG]
    xx = lambda ts: np.array([features[t] for t in ts])
    yy = lambda ts: np.array([observed[t] for t in ts])
    cv = TimeSeriesSplit(n_splits=3,gap=28)
    folds = []
    for tr, va in cv.split(train):
        a,b=train[tr[-1]],train[va[0]]
        assert a < issued(b)
        folds.append([str(a),str(b),str(issued(b))])
    assert train[-1] < issued(test[0]) and len(test)==744
    grid=GridSearchCV(HistGradientBoostingRegressor(random_state=0), dict(max_depth=[2,3,None],learning_rate=[.05,.1]),
                      cv=cv,scoring="neg_root_mean_squared_error",n_jobs=1).fit(xx(train),yy(train))
    preds={"history": xx(test)[:,-1], "mean": grid.predict(xx(test)).clip(0),
           "q80": HistGradientBoostingRegressor(loss="quantile",quantile=.8,random_state=0,**grid.best_params_)
                   .fit(xx(train),yy(train)).predict(xx(test)).clip(0)}
    entry = dict(trainrows=len(train),first=str(train[0]),last=str(train[-1]),folds=folds,params=grid.best_params_,
                 calendar_rows=len(test),zero_work=sum(observed[t]==0 and 7<=t.hour<=22 for t in test),
                 by_capacity={c:{k:metrics(test,yy(test),v,c) for k,v in preds.items()} for c in (6,8)})
    if label=="course":
        valid={}
        for cutoff in (JUNE,datetime(2026,7,1)):
            ts=[t for t in features if t<cutoff]
            valid[str(cutoff)]={}
            for name, model in [("linear",LinearRegression()),("default",HistGradientBoostingRegressor(random_state=0)),
                          ("depth3",HistGradientBoostingRegressor(max_depth=3,random_state=0)),
                          ("l2",HistGradientBoostingRegressor(l2_regularization=1,random_state=0))]:
                pv=model.fit(xx(ts),yy(ts)).predict(xx(jul))
                valid[str(cutoff)][name]=float(np.mean((pv-yy(jul))**2)**.5)
        entry["valid_scores_available_by_jul31_20"]=valid
        entry["example"]=next({"hour":str(t),"baseline":float(p),"fact":observed[t],"staff":staffing(p,6,True)}
                              for t,p in zip(test,preds["history"]) if 7<=t.hour<=22 and p<observed[t]
                              and staffing(p,6,True)==staffing(observed[t],6,True))
    elif label=="student":
        assert [datetime.fromisoformat(r["datetime"]) for r in student]==test
        assert list(yy(test))==[int(r["fact"]) for r in student]
        entry["max_student_csv_abs_difference"]={ours:float(np.max(np.abs(v-[float(r[s]) for r in student])))
              for (ours,v),s in zip(preds.items(),("baseline","model","quantile"),strict=True)}
        assert max(entry["max_student_csv_abs_difference"].values()) < 1e-8
    result[label]=entry
print(json.dumps(result, indent=2, ensure_ascii=False))
