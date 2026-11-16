"""Small, deterministic evidence for chapter 9. No estimators or timed workloads."""
import csv
import contextlib
import hashlib
import io
import random
import sys
import tempfile
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
data = ROOT / 'site/data'
report = {}
tables = {}
for name in ['deliveries', 'guests_churn', 'family_members']:
    path = data / (name + '.csv')
    with path.open() as f:
        rows = list(csv.DictReader(f))
    tables[name] = rows
    cols = list(rows[0])
    report[name] = {
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'rows': len(rows),
        'unique_ids': len({r[cols[0]] for r in rows}),
        'full_duplicates': len(rows) - len({tuple(r.values()) for r in rows}),
        'missing': {c: sum(not r[c] for r in rows) for c in cols if any(not r[c] for r in rows)},
    }
d = tables['deliveries']
ok = [r for r in d if r['actual_min'] and 1 <= float(r['actual_min']) <= 299]
x = np.array([[float(r['distance_km']), int(r['items']), int(r['courier']=='пеший')] for r in ok])
report['deliveries'].update({'included':len(ok), 'dates': [min(r['created'] for r in d),max(r['created'] for r in d)],
                             'gram_km_km': (x.T@x)[0,0], 'gram_km_items':(x.T@x)[0,1]})
g = np.array([[float(r[c]) for c in ['visits_90d','days_since_last','tenure_months']] for r in tables['guests_churn']])
def near(matrix):
    dist = np.linalg.norm(matrix-matrix[0],axis=1)
    dist[0] = np.inf
    return np.argsort(dist,kind='stable')[:5].tolist()

raw, scaled = near(g),near((g-g.mean(axis=0))/g.std(axis=0))
report['guests_churn'].update(raw=raw,scaled=scaled,common=len(set(raw)&set(scaled)))
f = tables['family_members']
features = ['gender','age','income_k','family_size']
a = np.array([[float(row[key]) for key in features] for row in f])
y = np.array([float(row['spend_k']) for row in f])
report['family_members'].update(unique_profiles=len(set(map(tuple,a))), feature_ranges=dict(zip(features,zip(a.min(axis=0),a.max(axis=0)))),average_spend_k=y.mean())
# Exact sklearn ShuffleSplit ordering for the specified integer seed and holdout size.
perm = np.random.RandomState(42).permutation(len(f))
te,tr = perm[:1250],perm[1250:]
P = np.random.default_rng(42).normal(size=(4,4))
def design(a):
    return np.column_stack((np.ones(len(a)),a))
def coef(a,y):
    return np.linalg.lstsq(design(a),y,rcond=None)[0]
def score(y,p):
    return 1-float(np.sum((y-p)**2)/np.sum((y-y.mean())**2))
wo, wh = coef(a[tr],y[tr]),coef(a[tr]@P,y[tr])
open_p,hidden_p = design(a[te])@wo,design(a[te]@P)@wh
new = np.array([[1,34,95,3]])
q=np.random.default_rng(43).normal(size=(4,4))
report['holdout']={'train':len(tr),'test':len(te),'augmented_rank':int(np.linalg.matrix_rank(design(a[tr]))),'key_condition':float(np.linalg.cond(P)),
                   'open_r2':score(y[te],open_p),'hidden_r2':score(y[te],hidden_p),'rounded_r2':round(score(y[te],hidden_p),4),
                   'max_prediction_difference':float(abs(open_p-hidden_p).max()),'open_new':float((design(new)@wo)[0]),
                   'hidden_new':float((design(new@P)@wh)[0]),'wrong_key_new':float((design(new@q)@wh)[0])}
bad=P.copy()
bad[:,3]=bad[:,0]+bad[:,1]
report['holdout']['bad_r2']=score(y[te],design(a[te]@bad)@coef(a[tr]@bad,y[tr]))
C=np.array([[1,1],[1,1+1e-8],[1,1-1e-8]])
v=C@np.array([1.,-1.])
try:
    normal=np.linalg.solve(C.T@C,C.T@v).tolist()
except np.linalg.LinAlgError as exc:
    normal=type(exc).__name__
report['near_dependent']={'rank':int(np.linalg.matrix_rank(C)), 'gram_rank':int(np.linalg.matrix_rank(C.T@C)),
                          'normal_solution':normal,'lstsq':np.linalg.lstsq(C,v,rcond=None)[0].tolist()}
z=np.array([[0.,0.],[1.,1.],[2.,2.]])
ystar=np.arange(3.)
p2=np.diag([1.,2.])
off=np.array([[2.,0.]])
report['off_training_space']={'original':float((design(off)@coef(z,ystar))[0]),'hidden':float((design(off@p2)@coef(z@p2,ystar))[0])}
reduced=np.array([[0,0],[0,1],[1,0],[1,1]])
h=reduced@np.diag([1,0])
report['singular_key']={key:score(reduced[:,i],design(h)@coef(h,reduced[:,i])) for i,key in enumerate(['target_x1','target_x2'])}
c = np.array([0.,10.,20.])
yy = 1+0.2*c
fahrenheit = (32+1.8*c)[:,None]
report['units']={'celsius_at_30':float(design([[30]])[0]@coef(c[:,None],yy)),'fahrenheit_at_86':float(design([[86]])[0]@coef(fahrenheit,yy))}
report['score_pairs']=[{'base':b,'hidden':s,'raw_same':abs(b-s)<=1e-9,'rounded_same':round(b,4)==round(s,4),'hidden_report':round(s,4)} for b,s in [(0.81234561,0.8123456103),(0.81234561,0.81234563),(0.,1e-9)]]
report['ridge_no_intercept']=[x*x/(x*x+1) for x in [1.,2.]]
report['tariff_discount']={'equals_500':500,'saved':round(sum(x*.1 for x in [320,540,500,1250,80,760,499,501] if x>500),1)}
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

sk_hidden = LinearRegression().fit(a[tr]@P,y[tr])
sk_open = LinearRegression().fit(a[tr],y[tr])
report['sklearn_prediction'] = {'R2':sk_hidden.score(a[te]@P,y[te]),'new_hidden':sk_hidden.predict(new@P)[0],
                               'new_open':sk_open.predict(new)[0],'max_abs_error':abs(sk_open.predict(a[te])-sk_hidden.predict(a[te]@P)).max()}
report['tree_scores'] = {depth: {k: DecisionTreeRegressor(max_depth=depth,random_state=0).fit(A[tr],y[tr]).score(A[te],y[te]) for k,A in [('open',a),('hidden',a@P)]} for depth in [3,5,8]}
target=np.array([float(r['actual_min']) for r in ok])
w=coef(x,target)
resid=target-design(x)@w
fold_mae=[]
for hold in np.array_split(np.arange(len(ok)),5):
    mask=np.ones(len(ok),dtype=bool)
    mask[hold]=False
    prediction=design(x[hold])@coef(x[mask],target[mask])
    fold_mae.append([np.abs(target[hold]-target[mask].mean()).mean(),np.abs(target[hold]-prediction).mean()])
report['delivery_ols']={'coef':w.tolist(),'mae':abs(resid).mean(),'r2_train':score(target,design(x)@w),'fivefold_mean_mae':np.mean(fold_mae,axis=0).tolist()}
report['matrix_predictions']=(np.array([[1,2,1],[4,1,0],[6,4,0]])@np.array([3.9,1.7,18.5])+8).tolist()
report['minimum_tick']={}
for measured in [0.,0.25]:
    try:
        result=f"{1/measured:.0f}"
    except ZeroDivisionError as error:
        result=type(error).__name__
    report['minimum_tick'][str(measured)]=result
sys.path.insert(0,str(ROOT/'tools'))
import gen_data
with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
    gen_data.OUT=Path(td)
    for chapter,seed in [(4,4004),(6,6006),(9,9009)]:
        getattr(gen_data,f'gen_chapter{chapter}')(random.Random(seed))
    report['generator_bytes_equal']={name: (Path(td)/(name+'.csv')).read_bytes()==(data/(name+'.csv')).read_bytes() for name in tables}
print(json.dumps(report,ensure_ascii=False,indent=2))
