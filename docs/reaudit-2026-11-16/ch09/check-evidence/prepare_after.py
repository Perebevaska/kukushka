"""Export current chapter without building site; make explicit timer-API migrations.
Run only after coordinator applies reviewed changes. Frozen before evidence stays intact.
"""
import json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
if len(sys.argv)>1:
    snapshot=Path(sys.argv[1])
    items=[t for t in json.loads(snapshot.read_text()) if t['lesson'].startswith('ch09/')]
    (HERE/'after-tasks.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
else:
    sys.path.insert(0,str(ROOT/'tools')); import build
    build.CH_DISPLAY['ch09']=True
    lessons={('ch09',p.stem):build.parse_lesson(p) for p in (ROOT/'content/ch09').glob('*.md') if p.stem not in ('intro','test')}
    build.export(lessons,HERE/'after-tasks.json')
items=json.loads((HERE/'after-tasks.json').read_text());tasks={t['lesson']+'/'+t['id']:t for t in items if t['kind']=='task'}
rows=[json.loads(s) for s in (HERE/'programs.jsonl').read_text().splitlines()]
for row in rows:
    code=row['code']; original=code
    if row['task'] in ('vectorize','nearest-shop'):
        # Private deterministic hook now belongs to grader setup, not learner code.
        if 'time.perf_counter=_clock\n' in code: code=code.split('time.perf_counter=_clock\n',1)[1]
        loop,vec=('pay_loop','pay_vec') if row['task']=='vectorize' else ('nearest_loop','nearest_vec')
        pattern=r't0 = time.perf_counter\(\)\na = '+loop+r'\(([^\n]*)\)\nt_loop = time.perf_counter\(\) - t0\n\nt0 = time.perf_counter\(\)\nb = '+vec+r'\(([^\n]*)\)\nt_vec = time.perf_counter\(\) - t0'
        code,n=re.subn(pattern,lambda m:f'a, t_loop = timed_call("loop", {loop}, {m[1]})\nb, t_vec = timed_call("vec", {vec}, {m[2]})',code)
        assert n==1,(row['id'],n)
        if 'zero vector duration' in row['description']: row['clock_ticks']=[0.,.03,1.,1.]
        if 'slower vector duration' in row['description']:row['clock_ticks']=[0.,.01,1.,1.02]
        if 'speedup 1.5' in row['description']:row['clock_ticks']=[0.,.03,1.,1.02]
    if row['task']=='apply-col' and row['description'].startswith(('Correct fee function','Real workload')):
        code=code[code.index('import numpy as np'):]
        code=code.replace('t_apply = best_time(lambda: d.apply(fee_apply, axis=1))','a, t_apply = timed_call("apply", lambda table: table.apply(fee_apply, axis=1), d)').replace('t_col = best_time(lambda: fee_col(d))','b, t_col = timed_call("col", fee_col, d)')
        row['clock_ticks']=[0.,.01,1.,1.] if 'zero timer' in row['description'] else [0.,.03,1.,1.02]
    if row['task']=='hidden-quality':
        code='def quality_equal(base, hidden, tol=1e-9):\n    return bool(abs(hidden-base)<=tol)\n\n'+code
        row['quality_api_migration']='Add public quality_equal only; original same/model/r2 computations are retained exactly.'
    if row['task']=='same-quality':
        row['prediction_contract']='Explicit pred_x/pred_p outputs; both already exist in this original program, no value is replaced.'
    row['code']=code
    if code!=original:
        row['migration']='Public timing or quality_equal API migration; original result calculations and normative verdict retained.'
        row['original_program_id']=row['id']
    if row.get('clock_ticks'):
        task=tasks[row['lesson']+'/'+row['task']]
        assert '_measurement_clock' in task.get('setup',''),row['id']
# Additional positive regression for delegated real measurements, declared before after execution.
item=tasks['ch09/02b-vectorize/vectorize']
wrapper="def registered_best(label,function,*args):\n    trials=[timed_call(label,function,*args) for _ in range(5)]\n    return min(trials,key=lambda pair:pair[1])\n"
code=wrapper+item['solution'].replace('a, t_loop = timed_call("loop", pay_loop, km, rain)','a, t_loop = registered_best("loop", pay_loop, km, rain)').replace('b, t_vec = timed_call("vec", pay_vec, km, rain)','b, t_vec = registered_best("vec", pay_vec, km, rain)')
rows.append(dict(id='C09-W01',lesson=item['lesson'],task=item['id'],description='Delegating wrapper selects minimum of five genuinely registered function calls',expected=True,group='after-wrapper-regression',code=code))

# New timing-contract negatives, expected verdicts declared before proposal refinement.
for ident,length in [('C09-T01',0),('C09-T02',3)]:
    code=item['solution'].replace('b, t_vec = timed_call("vec", pay_vec, km, rain)',f'_measured, t_vec = timed_call("vec", pay_vec, km[:{length}], rain[:{length}])\nb=pay_vec(km,rain)')
    rows.append(dict(id=ident,lesson=item['lesson'],task=item['id'],description=f'pay_vec timed on {length} rows while complete outputs are computed separately',expected=False,group='timer-input-binding',code=code))
fee=tasks['ch09/02b-vectorize/apply-col']
code=fee['solution'].replace('a, t_apply = timed_call("apply", lambda table: table.apply(fee_apply, axis=1), d)','a, t_apply = timed_call("apply", lambda table: 0., d)')
rows.append(dict(id='C09-T03',lesson=fee['lesson'],task=fee['id'],description='Dummy packaging operation is timed while fee_col and total remain correct',expected=False,group='timer-result-binding',code=code))
# Imported-clock correctness and constant-zero pair; originals in the first 46 stay frozen.
best=tasks['ch09/02b-vectorize/best-of']
alias=best['solution'].replace('import time','from time import perf_counter as now').replace('time.perf_counter()','now()')
rows.append(dict(id='C09-B01',lesson=best['lesson'],task=best['id'],description='Equivalent imported-clock alias',expected=True,group='clock-alias-regression',code=alias))
rows.append(dict(id='C09-B02',lesson=best['lesson'],task=best['id'],description='Imported-clock alias returns constant zero',expected=False,group='clock-alias-regression',code=alias.replace('return min(times)','return 0.0')))
quality=tasks['ch09/05-project/hidden-quality']
variants=[('C09-Q01',True,'import math\n','math.isclose(base,hidden,rel_tol=0.,abs_tol=tol)'),('C09-Q02',False,'','bool(abs(hidden-base)<tol)'),('C09-Q03',False,'','bool(abs(round(hidden,4)-round(base,4))<=tol)'),('C09-Q04',False,'','bool(np.isclose(base,hidden,atol=tol))'),('C09-Q05',False,'','bool(abs(hidden-base)<=1e-9)'),('C09-Q06',False,'','True')]
for ident,expected,prefix,expression in variants:
    code=prefix+quality['solution'].replace('return bool(abs(hidden - base) <= tol)','return '+expression)
    assert code!=quality['solution'],ident
    rows.append(dict(id=ident,lesson=quality['lesson'],task=quality['id'],description='Public quality_equal transfer: '+ident,expected=expected,group='quality-equal-transfer',code=code))
predict=tasks['ch09/02-matrices/predict-df']
rows.append(dict(id='C09-P01',lesson=predict['lesson'],task=predict['id'],description='Returned model is broken after correct manual and same are stored',expected=False,group='submitted-model-binding',code=predict['solution']+'\nmodel.intercept_+=100.'))
same=tasks['ch09/04-transform/same-quality']
rows.append(dict(id='C09-S01',lesson=same['lesson'],task=same['id'],description='Equivalent submitted prediction vectors as lists',expected=True,group='submitted-vector-binding',code=same['solution']+'\npred_x=list(pred_x)\npred_p=list(pred_p)'))
rows.append(dict(id='C09-S02',lesson=same['lesson'],task=same['id'],description='Submitted prediction vector corrupted after summary',expected=False,group='submitted-vector-binding',code=same['solution']+'\npred_p=pred_p.copy()\npred_p[0]+=100.'))
# Exact student ndarray answer and mechanically equivalent Series target, separate from own answers.
student_source=HERE.parent/'student/03b-own-model/attempt-01.jsonl'
student=next(r for r in map(json.loads,student_source.read_text().splitlines()) if r['task']=='group-mean')
code=student['code']
assert 'y = ok["actual_min"].values' in code
for ident,program in [('C09-G01',code),('C09-G02',code.replace('y = ok["actual_min"].values','y = ok["actual_min"]'))]:
    rows.append(dict(id=ident,lesson='ch09/03b-own-model',task='group-mean',description='Equivalent target container: '+('exact student ndarray' if ident.endswith('01') else 'Series with same rows/index'),expected=True,group='target-container-equivalence',source=str(student_source),code=program))

expected_additions={r['id']:r['expected'] for r in json.loads((HERE/'expected-after-additions.json').read_text())}
assert {r['id']:r['expected'] for r in rows if r['id'] in expected_additions}==expected_additions
original_count=len((HERE/'programs.jsonl').read_text().splitlines())
assert len(rows)==original_count+len(expected_additions),(len(rows),original_count,len(expected_additions))
for row in rows:
    compile(row['code'],'<'+row['id']+'>','exec')

(HERE/'after-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
print('Exported after tasks and',len(rows),'programs;',sum('migration' in r for r in rows),'explicit API migrations')
