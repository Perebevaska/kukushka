import json,hashlib
from pathlib import Path
B=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch14/technical/checks');summary={}
for phase in ['','key-supplement/','acceptance-extra/']:
 lane=phase.strip('/') or 'main206';summary[lane]={}
 for rt in ['native','pyodide']:
  p=B/phase/f'after-{rt}.jsonl';rows=list(map(json.loads,p.read_text().splitlines())) if p.exists() else []
  ignore={5,196} if not phase else set()
  summary[lane][rt]=dict(completed=len(rows),raw_false_accept=sum(r['passed'] and not r['expected'] for r in rows),raw_false_reject=sum(not r['passed'] and r['expected'] for r in rows),submission_execution_failures=sum(r['stage']=='submission_execution' for r in rows),transport_failures=sum(r['stage']=='transport' for r in rows),meaningful_checked=sum(r['index'] not in ignore for r in rows),meaningful_matching=sum(r['index'] not in ignore and r['passed']==r['expected'] for r in rows),mismatches=[dict(index=r['index'],label=r['label'],stage=r['stage'],expected=r['expected'],passed=r['passed'],feedback=r['raw'].get('check')) for r in rows if r['passed']!=r['expected']])
# Verify format feedback semantics independently of the task's pass flag.
f=B/'acceptance-extra/ST14-format-expectation.json';expected=json.loads(f.read_text());formats={}
for rt in ['native','pyodide']:
 p=B/'acceptance-extra'/f'after-{rt}.jsonl'
 if not p.exists():continue
 rows=list(map(json.loads,p.read_text().splitlines()));bad=next((r for r in rows if r['label']==expected['label']),None);good=next((r for r in rows if r['label']==expected['correct_pair_label']),None)
 if bad is None or good is None:continue
 raw=bad['raw'];error=raw.get('error') or {};message=str(error.get('text',''));formats[rt]=dict(bad_stage=bad['stage'],bad_passed=bad['passed'],error_type=error.get('type'),message=message,required_parts={part:part in message for part in expected['required_message_parts']},correct_pair_passed=good['passed'])
 formats[rt]['meets_frozen_expectation']=bad['stage']==expected['expected_stage'] and error.get('type')==expected['expected_error_type'] and all(formats[rt]['required_parts'].values()) and good['passed']
summary['ST14-format']=formats
(B/'after-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({lane:{rt:{k:v for k,v in row.items() if k not in ['mismatches','message','required_parts']} for rt,row in runs.items()} for lane,runs in summary.items()},ensure_ascii=False))
