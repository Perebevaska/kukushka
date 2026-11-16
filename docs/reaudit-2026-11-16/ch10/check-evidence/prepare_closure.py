"""Freeze four tests for the two previously identified static boundaries only."""
from pathlib import Path
import json,hashlib,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
current=[t for t in json.loads(Path('/private/tmp/kuch10round/final.json').read_text()) if t['lesson'].startswith('ch10/')]
items={t['lesson']+'/'+t['id']:t for t in current}
baseline={t['lesson']+'/'+t['id']:t for t in json.loads((HERE/'before-tasks.json').read_text())}
rows=[]
def add(id,key,desc,code,expected,basis):
 lesson,task=key.rsplit('/',1)
 rows.append(dict(id=id,lesson=lesson,task=task,description=desc,code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),expected=expected,basis=basis,group='bounded-static-closure'))
k='ch10/04-tuning/train-vs-test';s=items[k]['solution']
add('SC01',k,'Correct full train/test staged MAE arrays',s,True,'Visible task requires 400 MAE for each of tr and te plus derived scalar metrics; this program computes all requested outputs.')
add('SC02',k,'Wrong eleventh test-curve point, original scalar metrics retained',s+'\nte[10] += 10',False,'Visible task requires all 400 test-stage MAE, not only the reported minimum and final value. te[10] is no longer its staged MAE.')
k='ch10/05-project/tune';s=items[k]['solution']
add('SC03',k,'Correct grid rows reordered with their keys and metrics',s+'\ngrid = grid.iloc[::-1].copy()',True,'Task requires the six learning_rate/max_depth combinations and corresponding metrics but prescribes no row order. Reordering full rows preserves their meaning and best is unchanged.')
add('SC04',k,'One grid learning-rate label changed, old metrics retained',s+'\ngrid.loc[0, "lr"] = 0.9',False,'Required learning rates are 0.05 and 0.1. A row relabelled 0.9 neither belongs to the required grid nor describes the model that produced its metrics.')
(HERE/'closure-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(HERE/'closure-expected-before-execution.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='code'} for r in rows],ensure_ascii=False,indent=2))
(HERE/'closure-before-tasks.json').write_text(json.dumps(current,ensure_ascii=False,indent=2))
comparison={}
for key in dict.fromkeys(r['lesson']+'/'+r['task'] for r in rows):
 comparison[key]={}
 for field in ['setup','check','solution']:
  a=items[key][field];b=baseline[key][field]
  comparison[key][field]=dict(equal_to_original_baseline=a==b,current_sha256=hashlib.sha256(a.encode()).hexdigest(),original_sha256=hashlib.sha256(b.encode()).hexdigest())
  assert a==b,(key,field)
(HERE/'closure-original-comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2))
files=['closure-programs.jsonl','closure-expected-before-execution.json','closure-before-tasks.json','closure-original-comparison.json']
(HERE/'closure-before-frozen.sha256').write_text(''.join(hashlib.sha256((HERE/f).read_bytes()).hexdigest()+'  '+f+'\n' for f in files))
# Same supplied harness and baseline data; isolated bundle names prevent any overwrite.
s=(HERE/'run_native.py').read_text()
s=s.replace("bundle=a.bundle or a.phase","bundle='closure-'+a.phase")
s=s.replace("HERE/f'{a.phase}-tasks.json'","HERE/f'closure-{a.phase}-tasks.json'")
start=s.index('programs=HERE/');end=s.index('\n',start)
s=s[:start]+"programs=HERE/'closure-programs.jsonl'"+s[end:]
(HERE/'run_closure_native.py').write_text(s)
s=(HERE/'run_pyodide.mjs').read_text()
s=s.replace("const bundle=process.argv[3]||phase;","const bundle='closure-'+phase;")
s=s.replace("path.join(here,phase+'-tasks.json')","path.join(here,'closure-'+phase+'-tasks.json')")
s=s.replace("process.argv[3]?(bundle+'-programs.jsonl'):(phase==='after'?'after-programs.jsonl':'programs.jsonl')","'closure-programs.jsonl'")
(HERE/'run_closure_pyodide.mjs').write_text(s)
print('Frozen 4 closure programs, expectations and equal baseline/setup/check/solution hashes; no ML executed.')
