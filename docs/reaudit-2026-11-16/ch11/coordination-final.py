"""Stdlib-only release reconciliation; writes coordinator-owned files only."""
import collections,csv,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent; ROOT=D.parents[2]; W=Path('/private/tmp/kuch11round')
def js(p):return json.loads(p.read_text())
def jl(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,ensure_ascii=False)
def require(x,message):
 if not x:raise AssertionError(message)
def reconcile(raw,aggregate):
 events=[];pairs=[];unpaired=[]
 for f in sorted(raw.glob('*.feedback.jsonl')):
  p=f.with_name(f.name.replace('.feedback.','.input.'));a,b=jl(p),jl(f)
  if len(a)!=len(b):
   unpaired.append(str(f.relative_to(D))+': incomplete write');continue
  for line,(x,y) in enumerate(zip(a,b),1):
   require((x.get('question') or x['lesson']+'/'+x['task'])==y['id'],str(p)+':'+str(line))
   events.append({'payload':dict(x,**y),'input':str(p.relative_to(D)),'feedback':str(f.relative_to(D)),'line':line})
  pairs.append({'input':str(p.relative_to(D)),'feedback':str(f.relative_to(D)),'rows':len(a),'input_sha256':sha(p),'feedback_sha256':sha(f)})
 for p in raw.glob('*.input.jsonl'):
  if not p.with_name(p.name.replace('.input.','.feedback.')).exists():unpaired.append(str(p.relative_to(D)))
 saved=[{k:v for k,v in x.items() if k!='at'} for x in jl(aggregate)] if aggregate.exists() else []
 exact=collections.Counter(canon(x['payload']) for x in events)==collections.Counter(map(canon,saved))
 # Aggregate is the submission order; raw pairs prove every payload including images.
 first={};last={}
 for x in saved:
  first.setdefault(x['id'],x);last[x['id']]=x
 return {'events':len(events),'graded':sum(type(e['payload'].get('passed')) is bool for e in events),'true':sum(e['payload'].get('passed') is True for e in events),'false':sum(e['payload'].get('passed') is False for e in events),'first_accepted':sum(e.get('passed') is True for e in first.values()),'latest_accepted':sum(e.get('passed') is True for e in last.values()),'unique_ids':len(last),'ids':sorted(last),'pairs':pairs,'unpaired':unpaired,'exact_full_payload_multiset':exact,'non_true':[e for e in events if e['payload'].get('passed') is not True],'by_id':{k:{'first':first[k],'last':last[k]} for k in last}}
initial_json_sha=sha(D/'coordination-initial.json');initial=reconcile(D/'student',D/'student/initial-attempts.jsonl');require(initial['exact_full_payload_multiset'],'initial payload multiset');require((initial['events'],initial['true'],initial['false'],initial['unique_ids'])==(91,89,2,89),'initial denominators')
for s in (D/'student/FREEZE.sha256').read_text().splitlines():
 h,name=s.split(maxsplit=1);require(sha(D/'student'/name)==h,'initial freeze '+name)
release=js(D/'technical/release.json')
for name,h in release['files'].items():require(sha(ROOT/name)==h,'release '+name)
for name,h in release['data'].items():require(sha(ROOT/'site/data'/name)==h,'data '+name)
require(sha(W/'final.json')==release['full_course_export_sha256'],'full export')
chapter=js(D/'technical/chapter-export.json');require(sha(D/'technical/chapter-export.json')==release['chapter_snapshot_sha256'],'chapter export')
require([x for x in js(W/'final.json') if x['lesson'].startswith('ch11/')]==chapter,'chapter filter')
prose=js(D/'technical/prose-closure-parity.json');require(prose['four_code_fields_unchanged'] and prose['final_task_fields_59_equal'],'prose closure')
# Independently compare all executable task fields with revised snapshot.
a={x['lesson']+'/'+x['id']:x for x in js(W/'revised.json') if x['lesson'].startswith('ch11/') and x['kind']=='task'}
b={x['lesson']+'/'+x['id']:x for x in chapter if x['kind']=='task'}
require(a.keys()==b.keys() and len(a)==59,'task keys')
require(all(a[k].get(f)==b[k].get(f) for k in a for f in ['setup','starter','check','solution']),'four executable fields parity')
sets={}
for label,suffix in [('main',''),('supplement','-supplement')]:
 before=jl(D/f'check-evidence/{"programs" if not suffix else "supplement-programs"}.jsonl');after=jl(D/f'check-evidence/after{suffix}-programs.jsonl')
 require([(r['id'],r['code']) for r in before]==[(r['id'],r['code']) for r in after],'literal critic before/after')
 outputs=[jl(D/f'check-evidence/after{suffix}-{surface}.jsonl') for surface in ['native','pyodide']]
 for out in outputs:
  require(len(out)==len(after),'critic counts')
  for p,r in zip(after,out):
   require(p['id']==r['id'] and p['code']==r['code'],'critic execution code')
   require(hashlib.sha256(p['code'].encode()).hexdigest()==p['code_sha256']==r['code_sha256'],'critic SHA')
   require(r['passed']==p['expected'],'critic expected '+r['id'])
 require([r['passed'] for r in outputs[0]]==[r['passed'] for r in outputs[1]],'critic parity')
 sets[label]={'count_per_surface':len(after),'matches_per_surface':len(after),'accepted':sum(r['passed'] for r in outputs[0]),'ids':[r['id'] for r in after]}
programs=jl(D/'fixes/reviewer-evidence/programs.jsonl');routs=[jl(D/f'fixes/reviewer-evidence/after-{s}.jsonl') for s in ['native','pyodide']]
for out in routs:
 require(len(programs)==len(out)==16,'reviewer count')
 for p,r in zip(programs,out):require(p['id']==r['id'] and p['expected_after']==r['passed'],'reviewer expected '+r['id'])
require([r['passed'] for r in routs[0]]==[r['passed'] for r in routs[1]],'reviewer parity')
retake=reconcile(D/'fixes/student/retest/raw',D/'student/retest-attempts.jsonl');targets=js(D/'fixes/student/retest/targets.json');target_ids=[r['id'] for r in targets['targets']];require(len(target_ids)==len(set(target_ids))==31,'target31')
inv=js(D/'technical/inventory.json');require(set(initial['ids'])==set(inv),'initial inventory')
ledger=list(csv.DictReader((D/'fixes/ledger.csv').open()));require(len(ledger)==len({r['id'] for r in ledger}),'ledger unique')
prior=js(D/'technical/prior-findings.json');require({r['id'] for r in prior}<={r['id'] for r in ledger},'prior coverage')
accept='--accept' in sys.argv
freeze_paths=[]
for line in (D/'fixes/student/retest/FREEZE.sha256').read_text().splitlines():
 h,name=line.split(maxsplit=1);require(sha(D/'fixes/student/retest'/name)==h,'retake freeze '+name);freeze_paths.append(name)
require(len(freeze_paths)==89,'retake freeze89')
recipient=js(D/'fixes/recipient-evidence/verification2.json')
require(recipient['status']=='passed' and len(recipient['commands'])==13,'recipient commands13')
require(all(r['returncode']==0 for r in recipient['commands']),'recipient command exit')
require(recipient['fits']==recipient['optimizer_steps']==0 and not recipient['external_data'],'saved model only')
manifest_checks={}
for manifest_name,folder,count in [('manifest.json','first-inputs',19),('second-manifest.json','second-inputs',29)]:
 manifest=js(D/'fixes/recipient-evidence'/manifest_name);checks={}
 for package,files in manifest.items():
  for name,h in files.items():
   path=D/'fixes/recipient-evidence'/folder/package/name;checks[package+'/'+name]=sha(path)==h
 require(len(checks)==count and all(checks.values()),folder+' SHA')
 manifest_checks[folder]=checks
csv_recalculation={}
for condition in ['clean','blur']:
 p=D/f'fixes/recipient-evidence/second-outputs/{condition}-all450-row-verification.csv'
 rows=list(csv.DictReader(p.open()));require(len(rows)==450,'450 CSV')
 require(len({r['position'] for r in rows})==len({r['original_index'] for r in rows})==450,'450 keys')
 require(all(r['prediction_match']=='True' and r['review_match']=='True' and float(r['confidence_absdiff'])==0 for r in rows),'row exact')
 selected={r['position'] for r in sorted(rows,key=lambda r:(float(r['confidence_actual']),int(r['position'])))[:37]}
 require(all((r['review_actual']=='True')==(r['position'] in selected) for r in rows),'queue rule')
 errors=[r for r in rows if r['prediction_actual']!=r['truth']]
 calc={'n':450,'correct':450-len(errors),'errors':len(errors),'caught_errors':sum(r['position'] in selected for r in errors),'missed_errors':sum(r['position'] not in selected for r in errors),'queue_n':37}
 expected=recipient['digits']['full450'][condition]
 require(all(calc[k]==expected[k] for k in calc),'own recipient CSV metrics')
 require(expected['maxdiff_proba']==expected['maxdiff_confidence']==0,'full proba diff')
 csv_recalculation[condition]=calc
closure=reconcile(D/'fixes/student/epoch-closure',D/'student/epoch-closure-attempts.jsonl')
closure_valid=closure['exact_full_payload_multiset'] and closure['events']==closure['true']==closure['unique_ids']==1 and closure['ids']==['03-mlp/epoch-gap']
if closure_valid:
 code=closure['by_id']['03-mlp/epoch-gap']['last']['code']
 require('y_validation' in code and 'read_csv' not in code and 'train_test_split' not in code,'closure uses provided arrays')
if accept:require(closure_valid,'successful independent epoch closure')
status='accepted' if accept else 'pending final reviewer'
coverage={'chapter':11,'status':status,'inventory_counts':dict(collections.Counter(inv.values())),'initial':initial,'retake':retake,'retake_targets':targets['targets'],'retake_missing':sorted(set(target_ids)-set(retake['ids'])),'retake_extra':sorted(set(retake['ids'])-set(target_ids)),'ledger':[{**r,'decision_source':'fixes/ledger.csv','historical':r['id'] in {p['id'] for p in prior}} for r in ledger],'observation_count':len({r['id'] for r in ledger}|{'RCP11-01'}),'closure1':closure}
require(coverage['observation_count']==41,'41 observations')
pending=[]
require(retake['exact_full_payload_multiset'] and not coverage['retake_missing'] and not coverage['retake_extra'] and not retake['unpaired'],'final retake payload')
require((retake['events'],retake['true'],retake['false'],retake['unique_ids'],retake['latest_accepted'])==(32,31,1,31,31),'retake exact counts')
require((D/'fixes/student/retest/report.md').exists(),'student report')
require('4,4 из 5 после редакции' in (D/'fixes/methodist.md').read_text(),'methodist final')
if not closure_valid:pending.append('epoch-gap closure using provided arrays')
if not accept:pending.append('final reviewer per-ID acceptance')
if accept:
 require(len(ledger)==41,'final ledger41')
 require(all(r.get('состояние_после') and r.get('свидетельство_после') and not any(t in r['состояние_после'].lower() for t in ['ожида','проверки','pending']) for r in ledger),'final per-ID decisions')
result={'status':status,'baseline':release['baseline'],'full_export_sha256':sha(W/'final.json'),'chapter_export_sha256':sha(D/'technical/chapter-export.json'),'release_files_verified':len(release['files']),'data_files_verified':len(release['data']),'initial_json_sha256_unchanged':initial_json_sha,'initial_multiset_exact':True,'initial_freeze83_valid':True,'retake_freeze_count':len(freeze_paths),'critic':sets,'reviewer':{'count_per_surface':16,'matches_per_surface':16,'accepted':sum(r['passed'] for r in routs[0])},'retake_summary':{k:v for k,v in retake.items() if k not in ['pairs','by_id','non_true']},'recipient':recipient,'recipient_manifest_checks':manifest_checks,'own_recipient_csv_recalculation':csv_recalculation,'methodist':{'before':3.6,'after':4.4,'scores':[5,4,4,4,5]},'closure1':closure,'pending':pending,'technical_standard_log':'technical/final-standard.log','notebook_solution_log':'technical/notebook-solution.log','notebook_starter_log':'technical/notebook-starter.log','test_ui':js(D/'technical/test-ui.json'),'session_closure':js(D/'technical/session-closure.json')}
(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n');(D/'coordination-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
require(sha(D/'coordination-initial.json')==initial_json_sha,'initial JSON preserved')
print(json.dumps({k:result[k] for k in ['status','release_files_verified','data_files_verified','retake_summary','pending']},ensure_ascii=False,indent=2))
