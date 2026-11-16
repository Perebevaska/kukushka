"""Verify the corrected project from the original orders and frozen specification."""
import csv
import hashlib
import json
import math
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path

for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'student'
RETEST = HERE / 'student/retest'
DAY = timedelta(days=1)
HOUR = timedelta(hours=1)
START = datetime(2026, 8, 1)
JULY = datetime(2026, 7, 1)
CUTOFF = datetime(2026, 7, 31, 20)
JUNE_CUTOFF = datetime(2026, 6, 30, 20)

def read_rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))

def read_json(path):
    return json.loads(path.read_text())

def frozen(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_manifest(root):
    manifest=read_json(root/'SHA256SUMS.json')
    for file,digest in manifest.items():
        assert frozen(root/file)==digest,file
    return len(manifest)

def issue_for(t):
    return datetime.combine(t.date()-DAY,time(20))

data_file=RETEST/'data/app_orders.csv'
assert frozen(data_file)==frozen(HERE.parent/'technical/data-baseline/app_orders.csv')
old_spec=read_json(OLD/'native-model-spec.json')
spec=read_json(RETEST/'own-fixed-before-run.json')
assert all(spec[k]==v for k,v in old_spec.items())
promo=set(map(date.fromisoformat,spec['new_public_calendar']))
assert len(promo)==5 and date(2026,8,21) in promo
orders={datetime.fromisoformat(r['datetime']):int(r['orders']) for r in read_rows(data_file)}

def features(t):
    week_lags=[7*24*n for n in range(1,5)]
    if t-week_lags[-1]*HOUR < min_time:
        return None
    for lag in [48, *week_lags, *range(28,52)]:
        assert t-lag*HOUR<issue_for(t)
    return [t.hour,t.weekday(),int(t.weekday()>=5),int(t.date() in promo and 10<=t.hour<=20),
            orders[t-48*HOUR],orders[t-168*HOUR],sum(orders[t-k*HOUR] for k in range(28,52))/24,
            sum(orders[t-k*HOUR] for k in week_lags)/4]

min_time=min(orders)
X={t:row for t in orders if (row:=features(t)) is not None}

def xy(ts):
    return np.array([X[t] for t in ts]),np.array([orders[t] for t in ts])

def fitted(times,**params):
    return HistGradientBoostingRegressor(random_state=spec['random_state'],**spec['params'],**params).fit(*xy(times))

valid=[t for t in X if JULY<=t<CUTOFF]
vx,vy=xy(valid)
vm=fitted([t for t in X if t<JUNE_CUTOFF])
july_rmse=float(np.mean((vm.predict(vx).clip(0)-vy)**2)**.5)
assert len(valid)==740
train=[t for t in X if t<CUTOFF]
model=fitted(train)
quant=fitted(train,loss='quantile',quantile=spec['quantile'])
test=[t for t in X if t>=START]
tx,ty=xy(test)
independent={'model':model.predict(tx).clip(0),'quantile':quant.predict(tx).clip(0),'baseline':tx[:,-1]}

issued={}
for day,p in enumerate(sorted((RETEST/'issued').glob('*.csv'))):
    rows=read_rows(p)
    assert len(rows)==24 and 'fact' not in rows[0] and 'y' not in rows[0]
    for h,r in enumerate(rows):
        t=datetime.fromisoformat(r[''])
        assert t==START+day*DAY+h*HOUR and t not in issued
        assert p.stem==str(t.date())
        assert datetime.fromisoformat(r['issue'])==issue_for(t)
        assert datetime.fromisoformat(r['cutoff'])==issue_for(t)-HOUR
        issued[t]={k:float(r[k]) for k in independent}
assert list(issued)==test and len(test)==744
after=read_rows(RETEST/'native-august-predictions.csv')
before=read_rows(OLD/'native-august-predictions.csv')
work=[i for i,t in enumerate(test) if 7<=t.hour<=22]
result={'july_rmse':july_rmse,'july_score_rows':len(valid),'final_fit_rows':len(train),
        'june_fit_last':str(max(t for t in X if t<JUNE_CUTOFF)),'final_fit_last':str(train[-1]),
        'issued_files':len(list((RETEST/'issued').glob('*.csv'))),'issued_rows':len(test),'work':len(work)}
for k,v in independent.items():
    errors=[]; changed=[]; deficit=extra=short=covered_work=covered_all=0
    for i,(r,o,t,expected) in enumerate(zip(after,before,test,v,strict=True)):
        fact=orders[t]
        pred=issued[t][k]
        assert datetime.fromisoformat(r['datetime'])==datetime.fromisoformat(o['datetime'])==t
        assert int(r['fact'])==fact and float(r[k])==pred
        errors.append(abs(pred-expected))
        if abs(float(o[k])-pred)>1e-12:
            changed.append(t)
        needed=max(1,math.ceil(fact/6))
        assert needed==int(r['needed'])
        if i in work:
            plan=max(1,math.ceil(pred/6))
            short+=int(needed>plan)
            deficit+=max(needed-plan,0)
            extra+=max(plan-needed,0)
            covered_work+=int(fact<=pred)
        else:
            plan=0
        assert int(r['staff_'+k])==plan
        covered_all+=int(fact<=pred)
    expect_changes=[] if k=='baseline' else [datetime(2026,8,21,h) for h in range(10,21)]
    assert changed==expect_changes and max(errors)<1e-10
    result[k]={'max_abs_diff':max(errors),'changed_rows':len(changed),'rmse':float(np.mean((v-ty)**2)**.5),
               'understaffed':short,'deficit':deficit,'extra':extra,'cost3':3*deficit+extra,
               'covered_work':covered_work,'covered_all':covered_all}

# Reconstruct the shortened shift and threshold from an hourly record.
hours=[(8,17),(9,13),(10,0),(11,10),(12,17),(13,24)]
transfer=[]
for c,u in [(6,300),(5,180)]:
    req=[max(1,math.ceil(n/c)) for h,n in hours if 9<=h<12]
    costs=[sum(max(0,r-s)*u+max(0,s-r)*100 for r in req) for s in (2,3)]
    transfer.append(dict(capacity=c,unit_short=u,need=req,costs=costs))
assert [p['costs'] for p in transfer]==[[400,300],[280,300]]
assert math.ceil(8/6)==math.ceil(11/6) and (11-8)**2==9
result['transfer']=transfer
result['original_manifest_verified']=verify_manifest(OLD)
print(json.dumps(result,ensure_ascii=False,indent=2))
