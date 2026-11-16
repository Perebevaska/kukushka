"""Summarize actual before/after without altering any frozen code or expectation."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def rows(name):return [json.loads(x) for x in (HERE/name).read_text().splitlines()]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
original=rows('programs.jsonl');before=rows('before-native.jsonl');after=rows('after-native.jsonl');web=rows('after-pyodide.jsonl');phase=json.loads((HERE/'expected-phase.json').read_text())
assert len(original)==len(before)==len(after)==len(web)==132
for p,a,b,w in zip(original,before,after,web):
 assert (p['id'],p['code'],p['expected'],p['code_sha256'])==(a['id'],a['code'],a['expected'],a['code_sha256'])==(b['id'],b['code'],b['expected'],b['code_sha256'])==(w['id'],w['code'],w['expected'],w['code_sha256'])
assert (HERE/'programs.jsonl').read_bytes()==(HERE/'after-programs.jsonl').read_bytes()
assert all((a['ok'],a['passed'])==(w['ok'],w['passed']) for a,w in zip(after,web))
for kind,count in [('supplement',2),('migration',14)]:
 for env in ('native','pyodide'):
  if kind=='migration':
   shutil.copyfile(HERE/f'migration-{env}.jsonl',HERE/f'after-migration-{env}.jsonl')
   shutil.copyfile(HERE/f'migration-{env}-environment.json',HERE/f'after-migration-{env}-environment.json')
  rs=rows(f'after-{kind}-{env}.jsonl');assert len(rs)==count
  assert all(r['passed']==r['expected'] for r in rs),(kind,env)
  for r in rs:
   if r.get('oracle_expected') is not None:assert r['transfer_oracle']['check']['passed']==r['oracle_expected']
# Before independent oracle proves C066 is a real wrong implementation, not an indistinguishable correct alternative.
for env in ('native','pyodide'):
 rs=rows(f'before-supplement-{env}.jsonl');assert rs[0]['passed'] and rs[0]['transfer_oracle']['check']['passed']
 assert rs[1]['passed'] and not rs[1]['transfer_oracle']['check']['passed']
check_diffs=[];field_diffs=[]
oldtasks={x['lesson']+'/'+x['id']:x for x in json.loads((HERE/'before-tasks.json').read_text())}
newtasks=json.loads((HERE/'after-tasks.json').read_text())
for t in newtasks:
 key=t['lesson']+'/'+t['id']
 for f in ('setup','starter','check','solution'):
  if t[f].strip()!=oldtasks[key][f].strip():
   field_diffs.append({'task':key,'field':f})
   if f=='check':check_diffs.append(key)
assert all(x['actual'].strip()==x['proposal'].strip() for x in json.loads((HERE/'actual-proposal-field-differences.json').read_text()))
summary=dict(programs=132,tasks=50,after_tasks_sha256=digest(HERE/'after-tasks.json'),programs_sha256=digest(HERE/'programs.jsonl'),original_expectations_sha256=digest(HERE/'expected-before-execution.json'),expected_phase_sha256=digest(HERE/'expected-phase.json'),same_verdicts_native_pyodide=True,original_expected_matches=sum(r['passed']==r['expected'] for r in after),current_contract_expected_matches=sum(r['passed']==phase[r['id']]['expected_current_contract'] for r in after),intentional_contract_migrations=[{'id':r['id'],'reason':phase[r['id']]['contract_change'],'actual_passed':r['passed'],'ok':r['ok'],'message':r['message']} for r in after if phase[r['id']]['contract_change']],unexpected_current_contract_mismatches=[r['id'] for r in after if r['passed']!=phase[r['id']]['expected_current_contract']],changed_checks=len(check_diffs),changed_code_cards=len(set(x['task'] for x in field_diffs)),changed_code_fields=len(field_diffs),changed_fields=field_diffs,supplement=dict(before=2,after=2,oracle_false_positive_reproduced=True),migrations=dict(programs=14,matched_native=14,matched_pyodide=14))
assert summary['original_expected_matches']==125 and summary['current_contract_expected_matches']==132 and not summary['unexpected_current_contract_mismatches']
(HERE/'after-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
lines=['# After: охват автопроверок главы12','', 'Actual after-tasks получены из реального build-export revised.json; 50×4 поля семантически совпали с proposal. 18 текстовых отличий — только концевые переводы строк.','', '| Карточка | Программ исходного132 | Before→after неверные зачёты | Before→after отказы позитивам | Намеренные миграции старых позитивов |','|---|---:|---|---|---|']
for key in sorted(oldtasks):
 pairs=[(b,a) for b,a in zip(before,after) if a['lesson']+'/'+a['task']==key]
 fps=[a['id'] for b,a in pairs if not a['expected'] and b['passed'] and not a['passed']]
 fns=[a['id'] for b,a in pairs if a['expected'] and not b['passed'] and a['passed']]
 changed=[a['id'] for _,a in pairs if phase[a['id']]['contract_change']]
 lines.append('| '+key+' | '+str(len(pairs))+' | '+', '.join(fps)+' | '+', '.join(fns)+' | '+', '.join(changed)+' |')
(HERE/'after-coverage.md').write_text('\n'.join(lines)+'\n')
oldhashes=json.loads((HERE/'before-source-hashes.json').read_text());newhashes={p:digest(ROOT/p) for p in oldhashes}
(HERE/'after-source-hashes.json').write_text(json.dumps(newhashes,indent=2)+'\n')
assert digest(HERE/'data-baseline/app_orders.csv')==digest(ROOT/'site/data/app_orders.csv')=='53c3351867d2c2bbf8decdd70daba5aa7eea2b5010154c52a115e29810666235'
assert all(oldhashes[p]==newhashes[p] for p in oldhashes if p.startswith('site/assets/'))
artifacts=['after-tasks.json','programs.jsonl','after-programs.jsonl','expected-before-execution.json','expected-phase.json','after-native.jsonl','after-pyodide.jsonl','before-supplement-native.jsonl','before-supplement-pyodide.jsonl','after-supplement-native.jsonl','after-supplement-pyodide.jsonl','migration-programs.jsonl','after-migration-native.jsonl','after-migration-pyodide.jsonl','after-source-hashes.json']
(HERE/'actual-acceptance-sha256.json').write_text(json.dumps({p:digest(HERE/p) for p in artifacts},indent=2)+'\n')
for name in ['after-native','after-pyodide','before-supplement-native','before-supplement-pyodide','after-supplement-native','after-supplement-pyodide','after-migration-native','after-migration-pyodide']:
 src=Path('/private/tmp/kuch12round')/(name+'.log')
 if src.exists():shutil.copyfile(src,HERE/(name+'.log'))
print(json.dumps({k:summary[k] for k in ['original_expected_matches','current_contract_expected_matches','changed_checks','changed_code_cards','changed_code_fields','after_tasks_sha256']},ensure_ascii=False))
