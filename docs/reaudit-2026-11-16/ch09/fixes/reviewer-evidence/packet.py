"""Create independent before/after replicates from real published pages and saved attempts."""
import hashlib
import json
import re
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
student = here.parents[1]/'student'
site = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
after = phase=='after'
tasks = {}
for page in sorted((site/'ch09').glob('*.html')):
    m=re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>',page.read_text(),re.S)
    if m:
        lesson=json.loads(m[1])
        for t in lesson['tasks']:
            tasks[page.stem+'/'+t['id']]=dict(t,files=lesson['files'])
catalog=json.loads((site/'notebooks/tasks/ch09.json').read_text())['tasks']
rows=[]
def row(label,key,code,expected):
    t=tasks[key]
    for field in ['setup','starter','solution','check']:
        assert (t.get(field) or '') == (catalog['ch09/'+key].get(field) or ''),(key,field)
    rows.append(dict(id=label,key='ch09/'+key,expected=expected,code=code,setup=t.get('setup') or '',check=t['check'],files=t['files'],
                     check_sha256=hashlib.sha256(t['check'].encode()).hexdigest()))
def attempt(key,num):
    lesson,task=key.split('/')
    file=student/lesson/('attempt-%02d.jsonl'%num)
    return next(a['code'] for a in map(json.loads,file.read_text().splitlines()) if a['task']==task)
def solution(key): return tasks[key]['solution']
k='02b-vectorize/best-of'
s=solution(k).replace('import time','from time import perf_counter as now').replace('time.perf_counter()', 'now()')
row('alias-clock',k,s,True)
row('attribute-clock',k,solution(k),True)
row('constant-best',k,s.replace('return min(times)','return 0.0'),False)
k='02b-vectorize/vectorize'
row('legacy-wrapper-unchanged',k,attempt(k,1),not after)
row('legacy-direct-unchanged',k,attempt(k,3),not after)
if after:
    s=attempt(k,1).split('import time\ndef best_time')[0]+'''
def timed_min(name, fun, *args):
    observations=[timed_call(name,fun,*args) for _ in range(5)]
    return min(observations,key=lambda item:item[1])
a,t_loop=timed_min('loop',pay_loop,km,rain)
b,t_vec=timed_min('vec',pay_vec,km,rain)
same=bool(np.allclose(a,b))
total=int(round(b.sum()))
speedup=t_loop/t_vec if t_vec else None
'''
    row('new-five-wrapper',k,s,True)
    fee='02b-vectorize/apply-col'
    fc=solution(fee)
    line='b, t_col = timed_call("col", fee_col, d)'
    assert line in fc
    row('precomputed-fee-col',fee,fc.replace(line,'saved_fees=fee_col(d)\nb,t_col=timed_call("col",lambda frame:saved_fees,d)'),False)
    row('applied-real-pass',fee,fc,True)

    row('precomputed-vector-duration',k,s.replace("b,t_vec=timed_min('vec',pay_vec,km,rain)",
        "cached_vector=pay_vec(km,rain)\nb,t_vec=timed_min('vec',lambda x,r:cached_vector,km,rain)"),False)
    row('wrong-measured-input',k,s.replace("timed_min('vec',pay_vec,km,rain)","timed_min('vec',pay_vec,km[:5],rain[:5])\nb=pay_vec(km,rain)"),False)
k='02-matrices/predict-df'
row('manual-valid',k,solution(k),True)
row('manual-negative',k,solution(k)+'\nmax_diff=-14.0',False)
row('submitted-model-wrong',k,solution(k)+'\nmodel.intercept_+=8.',False)
k='04-transform/same-quality'
row('same-quality-valid',k,solution(k),True)
row('same-quality-negative',k,solution(k)+'\nmax_pred_diff=-14.0',False)
row('submitted-predictions-shifted',k,solution(k)+'\npred_p=pred_p+2.',False)
k='04-transform/attack'
row('restored-negative',k,solution(k)+'\nmax_err=-.125',False)
k='05-project/hidden-quality'
row('real-hidden',k,solution(k),True)
row('proxy-repeat-first',k,solution(k)+"\nhidden_model.predict=lambda matrix: np.repeat(21.27,len(matrix))",False)
row('rounded-comparison',k,solution(k).replace('abs(r2_full - r2_base)', 'abs(round(r2_full,4) - round(r2_base,4))').replace('abs(hidden - base)', 'abs(round(hidden,4) - round(base,4))'),False)
if after:
    s=solution(k)
    needle='abs(hidden - base) <= tol'
    assert needle in s
    row('strict-boundary',k,s.replace(needle,'abs(hidden-base) < tol'),False)
    row('absolute-isclose',k,s.replace(needle,'np.isclose(base,hidden,atol=tol,rtol=0.0)'),True)
    row('ignores-supplied-tol',k,s.replace(needle,'abs(hidden-base)<=1e-9'),False)
    k='03b-own-model/my-class'
    s=solution(k)
    row('lstsq-full-and-rank-deficient',k,s,True)
    old_catalog=Path(sys.argv[3]) if len(sys.argv)>3 else Path('/private/tmp/kuch09round/original/site')
    old=json.loads((old_catalog/'notebooks/tasks/ch09.json').read_text())['tasks']['ch09/'+k]['solution']
    row('gram-inversion-on-near-singular',k,old,False)
    # Preserve correct training calculation, but drop the second feature on a
    # new two-feature matrix only. This passes the historical 1/3-column checks.
    s=s.replace('return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_', 
        'test = np.asarray(X, dtype=float).copy()\n        if test.shape[1] == 2:\n            test[:,1] = 0.0\n        return test @ self.coef_ + self.intercept_')
    assert 'test.shape' in s
    row('two-feature-broken',k,s,False)
k='03b-own-model/group-mean'
row('ndarray-y',k,attempt(k,1),True)
row('series-y',k,attempt(k,2),True)
(here/(phase+'-cases.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=1)+'\n')
