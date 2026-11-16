"""Freeze after programs without mutating the before package or executing ML."""
from pathlib import Path
import json,hashlib,datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
rows=[json.loads(s) for s in (HERE/'programs.jsonl').read_text().splitlines()]
items=[t for t in json.loads(Path('/private/tmp/kuch10round/revised.json').read_text()) if t['lesson'].startswith('ch10/')]
byid={t['lesson']+'/'+t['id']:t for t in items}
assert len(items)==88
for r in rows:
    r['phase']='after'
    if r['id']=='C36':
        r.update(expected=False,expected_before=True,expected_error=True,contract_changed=True,basis='New visible baselines evaluates April-June and setup supplies only pre-July history. Literal old July split has an empty evaluation period; expected rejection is a contract migration, not a false reject.')
(HERE/'after-tasks.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
(HERE/'after-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(HERE/'expected-after-before-execution.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='code'} for r in rows],ensure_ascii=False,indent=2))
extras=[]
r=next(r for r in rows if r['id']=='C36')
# Mechanical migration: only issue date/forecast cutoff changes; same historical freeze principle.
code=r['code'].replace('2025-07-01','2025-04-01')
extras.append(dict(id='C36M',lesson=r['lesson'],task=r['task'],code=code,expected=True,group='after-contract-migration',basis='Mechanical April-date migration of old July baselines program. Revised future facts after the issue cannot affect issued features/calendar forecasts.',code_sha256=hashlib.sha256(code.encode()).hexdigest()))
for task,lesson in [('compare','ch10/05-project'),('speed-table','ch10/06-libraries')]:
    code=byid[lesson+'/'+task]['solution']
    ticks=[]
    for i in range(5 if task=='compare' else 3):ticks.extend([float(i*1000),float(i*1000),float(i*1000+100),float(i*1000+100)])
    extras.append(dict(id='ZERO-'+task,lesson=lesson,task=task,code=code,expected=True,group='after-new-controlled-clock',basis='Actual estimator operations still run inside supplied timers. An externally injected coarse clock may register a zero interval; valid table and winners must remain accepted.',clock_ticks=ticks,code_sha256=hashlib.sha256(code.encode()).hexdigest()))
(HERE/'after-additional-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in extras))
(HERE/'expected-after-additional-before-execution.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='code'} for r in extras],ensure_ascii=False,indent=2))
files=['after-tasks.json','after-programs.jsonl','expected-after-before-execution.json','after-additional-programs.jsonl','expected-after-additional-before-execution.json']
(HERE/'after-frozen.sha256').write_text(''.join(hashlib.sha256((HERE/f).read_bytes()).hexdigest()+'  '+f+'\n' for f in files))
for line in (HERE/'frozen.sha256').read_text().splitlines():
    h,f=line.split('  ');assert hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h,f
assert all(a['code']==b['code'] for a,b in zip(rows,[json.loads(s) for s in (HERE/'programs.jsonl').read_text().splitlines()]))
print('Prepared after36 identical literal programs, separate April migration + 2 zero-clock programs; before immutable.')
