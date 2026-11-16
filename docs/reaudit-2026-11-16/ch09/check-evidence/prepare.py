"""Freeze contract expectations without importing ML or executing submissions."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
items=json.loads((HERE.parent/'technical/baseline-export.json').read_text())
tasks={t['lesson']+'/'+t['id']:t for t in items if t['kind']=='task'}
rows=[]
def add(key,label,expected,change=lambda s:s,group='new'):
    t=tasks['ch09/'+key]
    rows.append(dict(id=f'C09-{len(rows)+1:02}',lesson=t['lesson'],task=t['id'],description=label,expected=expected,group=group,code=change(t['solution'])))
def sub(a,b):
    def f(s):
        assert a in s,a
        return s.replace(a,b)
    return f
def tail(s): return lambda code:code+'\n'+s
# Positive/negative pair in each of seven lessons; expectations precede execution.
add('01-vectors/dist','Euclidean distances via sum of squares',True,sub('np.linalg.norm(others - me, axis=1)','np.sqrt(((others-me)**2).sum(axis=1))'))
add('01-vectors/dist','Squared distances reported as distances, same nearest',False,sub('np.linalg.norm(others - me, axis=1)','((others-me)**2).sum(axis=1)'))
add('01-vectors/neighbors-scale','Stable sorting replaced by Python sorting with same ties',True,sub('np.argsort(d, kind="stable")[:k]','sorted(range(len(d)), key=lambda j:d[j])[:k]'))
add('01-vectors/neighbors-scale','nearest ignores i and k although current output remains correct',False,sub('d = np.linalg.norm(A - A[i], axis=1)\n    d[i] = np.inf\n    return [int(j) for j in np.argsort(d, kind="stable")[:k]]','d = np.linalg.norm(A - A[0], axis=1)\n    d[0] = np.inf\n    return [int(j) for j in np.argsort(d, kind="stable")[:5]]'))
add('02-matrices/gram','Covariance through np.cov',True,sub('C = Xc.T @ Xc / (n - 1)','C = np.cov(X, rowvar=False)'))
add('02-matrices/gram','Zero Gram matrix',False,tail('G=np.zeros_like(G)'))
add('02-matrices/intercept-col','Intercept column via hstack and concatenate',True,lambda s:s.replace('np.column_stack([np.ones(len(X)), X.values])','np.hstack((np.ones((len(X),1)),X.to_numpy()))').replace('np.r_[model.intercept_, model.coef_]','np.concatenate(([model.intercept_],model.coef_))'))
add('02-matrices/intercept-col','Replace ones with zero in augmented feature matrix',False,tail('X1[:,0]=0'))
add('02-matrices/predict-df','Explicit row-wise dot products',True,sub('manual = X.values @ model.coef_ + model.intercept_','manual = np.array([np.dot(row,model.coef_)+model.intercept_ for row in X.values])'))
add('02-matrices/predict-df','Positive invented maximum difference while same remains true',False,tail('max_diff=100.0'))
add('02-matrices/predict-df','Negative invented maximum absolute difference',False,tail('max_diff=-100.0'))
add('02b-vectorize/best-of','Equivalent running minimum',True,lambda s:s.replace('times = []','best = float("inf")').replace('times.append(time.perf_counter() - t0)','best = min(best,time.perf_counter()-t0)').replace('return min(times)','return best'))
add('02b-vectorize/best-of','Constant zero after actual repeats',False,sub('return min(times)','return 0.0'))
add('02b-vectorize/vectorize','Boolean arithmetic vectorization',True,lambda s:s.replace('p = 60 + 14 * km + np.where(km > 8, 100, 0)\n    return np.where(rain, p * 1.3, p)','return (60+14*km+100*(km>8))*(1+0.3*rain)'))
add('02b-vectorize/vectorize','Fabricated positive timings overwrite genuine measured durations',False,tail('t_loop,t_vec,speedup=.4,.1,4.0'))
add('02b-vectorize/vectorize','Loop implementation aliased as vector',False,tail('pay_vec=pay_loop\nt_loop,t_vec,speedup=.4,.1,4.0'))
add('03-normal-equation/my-ols','Stable direct least squares',True,sub('np.linalg.solve(X1.T @ X1, X1.T @ y)','np.linalg.lstsq(X1,y,rcond=None)[0]'))
add('03-normal-equation/my-ols','Mean signed error instead of mean absolute error',False,sub('np.abs(pred - y).mean()','(pred-y).mean()'))
add('03-normal-equation/many-solutions','Moore-Penrose solution',True,sub('np.linalg.lstsq(full, y, rcond=None)[0]','np.linalg.pinv(full)@y'))
add('03-normal-equation/many-solutions','Equal zero forecasts are not optimal',False,sub('np.linalg.lstsq(full, y, rcond=None)[0]','np.zeros(full.shape[1])'))
add('03b-own-model/my-class','Equivalent solve via matrix dot',True,lambda s:s.replace('X1.T @ X1','X1.T.dot(X1)').replace('X1.T @ np.asarray(y, dtype=float)','X1.T.dot(np.asarray(y,dtype=float))'))
add('03b-own-model/my-class','predict drops intercept',False,sub(' @ self.coef_ + self.intercept_',' @ self.coef_'))
add('03b-own-model/my-class','predict erroneously truncates any new two-feature input',False,sub('return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_','X=np.asarray(X,dtype=float)\n        if X.shape[1]==2: return X[:,0]*self.coef_[0]+self.intercept_\n        return X@self.coef_+self.intercept_'))
add('04-transform/weights','Solve instead of explicit matrix inverse',True,sub('np.linalg.inv(P) @ w','np.linalg.solve(P,w)'))
add('04-transform/weights','Wrong direction of transformed weights',False,sub('w_formula = np.linalg.inv(P) @ w','w_formula = P @ w'))
add('04-transform/attack','Equivalent inverse-free reconstruction',True,sub('restored = hidden @ np.linalg.inv(P_found)','restored = np.linalg.solve(P_found.T, hidden.T).T'))
add('04-transform/attack','Negative invented maximal absolute error',False,tail('max_err=-100.0\nleaked=True'))
add('05-project/hidden-quality','Equivalent trained linear model via lstsq wrapper',True,lambda s:s.replace('hidden_model = LinearRegression().fit(X_train @ P, y_train)','class LeastSquares:\n    def fit(self,X,y):\n        self.w=np.linalg.lstsq(np.column_stack([np.ones(len(X)),X]),y,rcond=None)[0]\n        return self\n    def predict(self,X):\n        return np.column_stack([np.ones(len(X)),X])@self.w\nhidden_model = LeastSquares().fit(X_train @ P,y_train)'))
add('05-project/hidden-quality','Only open model with copied rounded R2 and true flag',False,lambda s:s.replace('fit(X_train @ P, y_train)','fit(X_train, y_train)').replace('predict(X_test @ P)','predict(X_test)'))
add('05-project/hidden-quality','Round before same comparison',False,sub('abs(r2_full - r2_base)','abs(r2_hidden - r2_base)'))
add('05-project/hidden-quality','Wrong key in returned model',False,lambda s:s.replace('fit(X_train @ P, y_train)','fit(X_train @ (P*2), y_train)').replace('predict(X_test @ P)','predict(X_test @ (P*2))'))
add('05-project/weights','Solve instead of explicit inverse',True,sub('np.linalg.inv(P) @ w','np.linalg.solve(P,w)'))
add('05-project/weights','Negative declared norm',False,tail('max_diff=-100.0'))
add('05-project/attack','Least-squares reconstruction',True,sub('np.linalg.solve(known, hidden[:4])','np.linalg.lstsq(known,hidden[:4],rcond=None)[0]'))
add('05-project/attack','False degree of disclosure',False,tail('leaked=0.0'))
# Deterministic counterfactual clocks call the actual workloads; restored after four reads.
def controlled_clock(code,ticks):
    prefix="import time\n_clock_original=time.perf_counter\n_clock_ticks=iter("+repr(ticks)+")\n_clock_count=0\ndef _clock():\n    global _clock_count\n    value=next(_clock_ticks)\n    _clock_count+=1\n    if _clock_count==4: time.perf_counter=_clock_original\n    return value\ntime.perf_counter=_clock\n"
    return prefix+code
add('02b-vectorize/vectorize','True measured zero vector duration using coarse controlled clock',True,lambda s:controlled_clock(s,[0.,.01,1.,1.]))
add('02b-vectorize/vectorize','True measured slower vector duration: no universal speed threshold',True,lambda s:controlled_clock(s,[0.,.01,1.,1.02]))
add('02b-vectorize/apply-col','Correct fee function with zero timer; None ratio as promised by theory',True,lambda s:'_durations=iter([.01,0.])\ndef best_time(f,repeats=5):\n    f()\n    return next(_durations)\n'+s.replace('speedup = t_apply / t_col','speedup = t_apply/t_col if t_col else None').replace('{speedup:.0f}','{speedup}'))
add('02b-vectorize/apply-col','Real workload with correct minimum timer reports speedup 1.5',True,lambda s:'_durations=iter([.03,.02])\ndef best_time(f,repeats=5):\n    f()\n    return next(_durations)\n'+s)
add('02b-vectorize/nearest-shop','Equivalent broadcasting Manhattan distances',True,sub('D = np.column_stack([np.abs(orders - s).sum(axis=1) for s in shops])','D = np.abs(orders[:,None,:]-shops[None,:,:]).sum(axis=2)'))
add('02b-vectorize/nearest-shop','Euclidean distance replaces required Manhattan metric',False,sub('np.abs(orders - s).sum(axis=1)','np.linalg.norm(orders-s,axis=1)'))
add('02b-vectorize/nearest-shop','True measured speedup 1.5 is still correct',True,lambda s:controlled_clock(s,[0.,.03,1.,1.02]))
add('02b-vectorize/nearest-shop','True measured zero vector duration, guarded None ratio',True,lambda s:controlled_clock(s.replace('speedup = t_loop / t_vec','speedup = t_loop/t_vec if t_vec else None').replace('{speedup:.0f}','{speedup}'),[0.,.03,1.,1.]))
add('04-transform/same-quality','Negative maximal forecast difference',False,tail('max_pred_diff=-100.'))

# Exact source programs from the 69-program previous acceptance, selected chapter only.
for row in map(json.loads,(ROOT/'tools/checks/fixtures/reaudit_20261115.jsonl').read_text().splitlines()):
    if row['lesson'].startswith('ch09/'):
        rows.append(dict(row,id=f'C09-{len(rows)+1:02}',group='previous-69-exact'))
for row in rows:
    if row['task']=='neighbors-scale':
        row['oracle']="_A=_np.array([[0.,0.],[2.,0.],[5.,0.],[10.,0.]])\n_got=need('nearest')(_A,2,1)\nassert len(_got)==1 and int(_got[0])==1, 'nearest(A,2,1) must use i=2 and k=1'"
    if row['task']=='my-class':
        row['oracle']="_X=_np.array([[0.,0.],[1.,0.],[0.,1.],[1.,1.],[2.,-1.]])\n_y=2+3*_X[:,0]-4*_X[:,1]\n_m=need('MyLinearRegression')().fit(_X,_y)\nassert _np.allclose(_m.predict(_np.array([[2.,3.],[-1.,2.]])),[-4.,-9.]), 'predict must retain both fitted feature weights on new rows'"
(HERE/'before-tasks.json').write_text(json.dumps(list(tasks.values()),ensure_ascii=False,indent=2))
(HERE/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
manifest=[{k:v for k,v in r.items() if k!='code'} for r in rows]
(HERE/'expected-before-execution.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Complete static comparison of public text, setup, starter, hints, solution and check.
coverage=[]
for source in sorted((ROOT/'content/ch09').glob('*.md')):
    if source.stem in ('intro','test'): continue
    text=source.read_text()
    import re
    for block in re.split(r'(?m)(?=^## task: )',text)[1:]:
        task_id=block.split(' |')[0].split(': ',1)[1]
        key='ch09/'+source.stem+'/'+task_id
        contract=block.split('\n### ',1)[0]
        t=tasks[key]
        coverage.append(dict(lesson='ch09/'+source.stem,task=task_id,contract=contract,setup=t.get('setup',''),starter=t['starter'],hints=re.findall(r'### hint\n(.*?)(?=\n### |\Z)',block,re.S),solution=t['solution'],check=t['check'],probes=[r['id'] for r in rows if r['lesson']+'/'+r['task']==key]))
(HERE/'contract-map.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
print(f'Frozen {len(coverage)} contracts and {len(rows)} normative programs before execution')
