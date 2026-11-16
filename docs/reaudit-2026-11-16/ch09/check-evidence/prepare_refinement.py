"""Freeze <=12 narrow refinement programs and their expectations without ML imports."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
BASE=json.loads((HERE/'after-tasks.json').read_text());tasks=[]
keys={'ch09/03b-own-model/my-class','ch09/02b-vectorize/vectorize','ch09/02b-vectorize/nearest-shop','ch09/02b-vectorize/apply-col'}
for task in BASE:
    if task.get('kind')!='task' or task['lesson']+'/'+task['id'] not in keys:continue
    task=dict(task);source=ROOT/'content'/Path(task['lesson']).with_suffix('.md');text=source.read_text()
    block=re.split(r'(?m)(?=^## task: )',text)
    block=next(b for b in block if b.startswith('## task: '+task['id']+' |'))
    for field in ['setup','starter','check','solution']:
        m=re.search(r'(?m)^### '+field+r'\n```python\n(.*?)\n```',block,re.S)
        task[field]=m[1] if m else ''
    tasks.append(task)
lookup={t['id']:t for t in tasks};rows=[]
def add(ident,name,expected,description,change=lambda c:c):
    t=lookup[name];code=change(t['solution']);compile(code,ident,'exec')
    rows.append(dict(id=ident,lesson=t['lesson'],task=t['id'],expected=expected,description=description,code=code,group='final-narrow-refinement'))
add('R09-M01','my-class',True,'Direct lstsq handles near-constant and exact duplicate features')
add('R09-M02','my-class',False,'Old normal-equation solve loses near-singular/exact-rank stability',lambda c:c.replace('np.linalg.lstsq(X1, np.asarray(y, dtype=float), rcond=None)[0]','np.linalg.solve(X1.T@X1,X1.T@np.asarray(y,dtype=float))'))
add('R09-M03','my-class',True,'Equivalent direct pseudoinverse without normal equations',lambda c:c.replace('np.linalg.lstsq(X1, np.asarray(y, dtype=float), rcond=None)[0]','np.linalg.pinv(X1)@np.asarray(y,dtype=float)'))
outer='def own_time(label,function,*args):\n    trials=[timed_call(label,function,*args) for _ in range(3)]\n    return min(trials,key=lambda pair:pair[1])\n'
for name,prefix,loop,vec,args in [('vectorize','R09-V','pay_loop','pay_vec','km, rain'),('nearest-shop','R09-N','nearest_loop','nearest_vec','orders, shops')]:
    def wrapper(c,loop=loop,vec=vec,args=args):
        new=outer+c
        for label,f in [('loop',loop),('vec',vec)]:
            new=new.replace(f'timed_call("{label}", {f}, {args})',f'own_time("{label}", lambda left,right: {f}(left,right), {args})')
        return new
    add(prefix+'01',name,True,'Outer timing minimum and callbacks delegate actual operation on passed arrays',wrapper)
    for index,label,f in [(2,'loop',loop),(3,'vec',vec)]:
        def cached(c,label=label,f=f,args=args):
            marker=f'timed_call("{label}", {f}, {args})'
            assert marker in c
            return c.replace(marker,f'timed_call("{label}", lambda *_args:_cached_result, {args})').replace('a, t_loop =',f'_cached_result={f}({args})\na, t_loop =',1)
        add(prefix+f'{index:02}',name,False,'Measured '+label+' callback returns precomputed full result instead of applying its arguments',cached)
add('R09-A01','apply-col',True,'Packaging callbacks and outer timing minimum accept new DataFrame',lambda c:outer+c.replace('timed_call("apply",','own_time("apply",').replace('timed_call("col",','own_time("col",'))
for ident,label,marker,cache in [('R09-A02','apply','timed_call("apply", lambda table: table.apply(fee_apply, axis=1), d)','d.apply(fee_apply,axis=1)'),('R09-A03','col','timed_call("col", fee_col, d)','fee_col(d)')]:
    def cached(c,marker=marker,label=label,cache=cache):
        assert marker in c
        return c.replace(marker,f'timed_call("{label}", lambda frame:_cached_result, d)').replace('a, t_apply =',f'_cached_result={cache}\na, t_apply =',1)
    add(ident,'apply-col',False,'Packaging '+label+' callback returns a cached result independent of new frame',cached)
assert len(rows)==12
(HERE/'refine-before-tasks.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2))
(HERE/'refine-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(HERE/'refine-expected-before-execution.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='code'} for r in rows],ensure_ascii=False,indent=2))
print('Frozen',len(tasks),'tasks and',len(rows),'programs; expectations declared before any new run')
