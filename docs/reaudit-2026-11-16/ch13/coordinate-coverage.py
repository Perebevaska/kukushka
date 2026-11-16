"""Read-only stdlib reconciliation of chapter-13 evidence by exact execution phase.
Writes only coverage.json; never executes lesson code or changes student inputs.
"""
import collections,datetime,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[2];W=Path('/private/tmp/kuch13round');P=D/'fixes/student/retest'
if (D/'fixes/student/weekly-closure-2/SHA256SUMS').exists() and 'Итог независимой приёмки' in (D/'fixes/review.md').read_text():
 import runpy
 runpy.run_path(str(D/'coordination-final.py'),run_name='__main__')
 raise SystemExit(0)
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x,m):
 if not x:raise AssertionError(m)
initial=read(D/'coordination-initial.json');release=read(D/'technical/release.json');reference=read(P/'final-reference.json');manifest=read(P/'public-package-manifest.json')
require(sha(W/'final.json')==release['full_course_export_sha256']==reference['final_export_sha256'],'final export alignment')
require(all(sha(ROOT/name)==h for name,h in release['files'].items()),'57 release files unchanged')
require(all(sha(ROOT/'site/data'/name)==h for name,h in release['data'].items()),'six released CSV hashes')
require(all(sha(W/'student-retest'/name)==h for name,h in manifest['files'].items()),'58 learner input hashes')
frozen={l.split('  ',1)[1]:l.split('  ',1)[0] for l in (D/'student/SHA256SUMS').read_text().splitlines()}
require(all(sha(D/'student'/n)==h for n,h in frozen.items()),'73 original learner hashes')
o={'status':'pending retake final reconciliation and independent final acceptance','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':initial['reference']['head'],'final_export_sha256':sha(W/'final.json'),'student_inventory':initial['inventory'],'initial':initial['student'],'initial_freeze':{'files':len(frozen),'all_match':True},'retake_assignment':read(P/'selection.json'),'retake_package':{'files':manifest['file_count'],'all_hashes_match':True,'manifest_sha256':sha(P/'public-package-manifest.json')},'release':{'files':len(release['files']),'data':len(release['data']),'all_hashes_match':True},'quality':{'before':[4,4,4,3,3],'before_mean':3.6,'after':None},'findings':initial['finding_ledger'],'phases':{},'retake_results':{'status':'running; not counted from unfinished files'},'own_project_after':{'status':'pending self-contained letter, CSV and saved execution verification'},'future_observations':{'retake_student_IDs':[],'crosswalk_status':'pending actual findings; never infer IDs from directory names'}}
C=D/'technical/checks'
first=read(C/'first-full-after-summary.json');prog=rows(C/'programs.jsonl');current=first['records']
require(len(current)==len(prog)==235,'235 frozen records')
vv=[]
for runtime in ['native','pyodide']:
 rr=rows(C/('after-'+runtime+'.jsonl'));require(len(rr)==235,'after235 count')
 for i,(p,r,c) in enumerate(zip(prog,rr,current)):
  require(r['code']==p['code'] and r['code_sha256']==p['code_sha256']==c['code_sha256'],'whole original program and SHA')
  require(r['passed']==c['cpython' if runtime=='native' else 'pyodide'],'first-phase summary verdict')
 vv.append([r['passed'] for r in rr])
require(vv[0]==vv[1],'first235 runtime parity')
o['phases']['first_after']={'export_sha256':first['first_full_after_source']['actual_export_sha256'],'programs':235,'matches_current_phase':sum(r['matches_current_phase'] for r in current),'remaining':[r for r in current if not r['matches_current_phase']],'original_program_sha256':sha(C/'programs.jsonl'),'migration_notes':read(C/'output-contract-migrations.json'),'runtime_parity':True,'runtimes':['CPython','Pyodide'],'coverage':'full original235 on first-after export only'}
for key,pfile,prefix in [('extra18','extra-programs.jsonl','extra-after-'),('migration8','migration-programs.jsonl','migration-after-'),('weekly_closure14','weekly-closure-programs.jsonl','weekly-final-')]:
 pp=rows(C/pfile);vv=[];stats={}
 for runtime in ['native','pyodide']:
  rr=rows(C/(prefix+runtime+'.jsonl'));require(len(rr)==len(pp),'phase count '+key)
  for p,r in zip(pp,rr):require(r['code']==p['code'] and r['code_sha256']==p['code_sha256'],'literal phase program '+key)
  vv.append([r['passed'] for r in rr]);stats[runtime]={'count':len(rr),'matches':sum(r['passed']==p['expected'] for p,r in zip(pp,rr)),'result_sha256':sha(C/(prefix+runtime+'.jsonl'))}
 require(vv[0]==vv[1],'phase parity '+key)
 o['phases'][key]={'program_count':len(pp),'program_sha256':sha(C/pfile),'runtimes':stats,'runtime_parity':True,'export_sha256':first['first_full_after_source']['actual_export_sha256'] if key!='weekly_closure14' else read(D/'technical/weekly-closure-parity.json')['final_export_sha256']}
# Independently compare each full exported record across the two narrow closures.
for key,left,right in [('weekly','revised.json','weekly-final.json'),('feedback','weekly-final.json','final.json')]:
 def index(p):return {(r['lesson'],r['kind'],r['id']):r for r in read(p) if r['lesson'].startswith('ch13/')}
 a,b=index(W/left),index(W/right);require(set(a)==set(b),'closure record sets')
 diffs={str(k):[f for f in set(a[k])|set(b[k]) if a[k].get(f)!=b[k].get(f)] for k in a if a[k]!=b[k]}
 expected=('ch13/05-project','task','weekly') if key=='weekly' else ('ch13/04c-llm','task','parse-llm')
 require(diffs=={str(expected):['check']},'only declared closure check changed')
 o['phases'][key+'_parity']={'before_export_sha256':sha(W/left),'after_export_sha256':sha(W/right),'record_count':len(a),'only_changed_record_fields':diffs,'other_64_tasks_31cells_5predict_equal':True}
R=D/'fixes/reviewer-evidence';expect=read(R/'expectations-after.json');emap={r['id']:r['expected_current'] for r in expect};combined=read(R/'combined-after.json')
rev={};v=[]
for runtime in ['native','pyodide']:
 rr=rows(R/('after-'+runtime+'.jsonl'));require([r['id'] for r in rr]==[r['id'] for r in combined],'reviewer33 IDs')
 require(all(r['check']['passed']==emap[r['id']] for r in rr),'reviewer33 expectations')
 v.append([r['check']['passed'] for r in rr]);rev[runtime]={'count':len(rr),'matches':len(rr),'accepted':sum(r['check']['passed'] for r in rr),'rejected':sum(not r['check']['passed'] for r in rr),'sha256':sha(R/('after-'+runtime+'.jsonl'))}
require(v[0]==v[1],'reviewer33 parity')
o['phases']['reviewer33']={'export_sha256':sha(W/'weekly-final.json'),'runtimes':rev,'migration':'R01 old string-only parser rejected after explicit None contract; R26 correct migration accepted'}
rrs={}
for runtime in ['native','pyodide']:
 rr=rows(R/('feedback-closure-'+runtime+'.jsonl'));require([r['id'] for r in rr]==['R01','R26'],'feedback targeted IDs')
 require([r['check']['passed'] for r in rr]==[False,True],'feedback targeted verdicts')
 require('None' in rr[0]['check']['msg'] and 'SDK' in rr[0]['check']['msg'],'specific missing SDK text feedback')
 rrs[runtime]={'count':2,'matches':2,'sha256':sha(R/('feedback-closure-'+runtime+'.jsonl'))}
o['phases']['reviewer_feedback2']={'export_sha256':sha(W/'final.json'),'runtimes':rrs,'scope':'targeted feedback and verdict preservation; not a new full33'}
sdk=read(D/'technical/sdk-lane-final.log');require(len(sdk)==32 and all(r['match'] for r in sdk),'SDK final32')
o['phases']['SDK32']={'cases':len(sdk),'matches':sum(r['match'] for r in sdk),'sha256':sha(D/'technical/sdk-lane-final.log'),'scope':'actual source extracted code, offline fixtures, no live model/API'}
o['shared_harness']=read(D/'technical/shared-harness-scope.json');o['test_UI']=read(D/'technical/test-ui.json')
require(o['test_UI'][0]['correct']==11 and o['test_UI'][0]['passed'] is False and o['test_UI'][1]['correct']==12 and o['test_UI'][1]['passed'] is True and all(r['reload_identical'] for r in o['test_UI']),'published UI boundary/reload')
o['limits']={'standard101':'baseline only; final export inventory is not an execution','notebook59':'recorded starter/solution59 logs are their own earlier execution phase; not rerun on final68157','current_68157':'release hashes + narrow feedback2 + SDK32 + published quiz UI + later learner retake; do not claim full235/full101/full notebook rerun','retake_log_location':'bridge phase=retest appends student/retest-attempts.jsonl and student/retest-images; raw input/feedback and authored files in fixes/student/retest; original initial-attempts and 73 frozen files remain protected'}
o['open_actions']=[{'id':'retake42','owner':'Sol medium student, then Sol medium coordinator','action':'Finish 42 selected IDs, preserve all raw input/feedback/Q1-Q4; coordinator compare full payloads and all final IDs against selected inventory'},{'id':'letter_after','owner':'student then Astra high business critic and independent reviewer','action':'Submit new self-contained letter with both volumes, numerators, boundary, original quote IDs and meaning; independently recompute CSV and semantic evidence'},{'id':'final_ledger','owner':'Astra high independent reviewer and Sol medium coordinator','action':'Map all63 source IDs and any after-ST findings to explicit after decision with evidence and external owner'},{'id':'quality_after','owner':'Astra high methodist','action':'Give separate five-criterion after assessment if warranted by revised published flow and actual retake; preserve before3.6'},{'id':'M13-01','owner':'owner of real support/review flow','action':'Collect independent human-labelled samples of both periods under one rubric, record sampling, numerators/denominators and uncertainty before claims about real complaint prevalence'},{'id':'human_learning','owner':'course methodist and SQL-analyst pilot organizer','action':'Observe new-point/new-period task after a break; record first action, help, source/denominator reconstruction; agent runtime is not human learning measurement'}]
(D/'coverage.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':o['status'],'findings':o['findings']['count'],'release':o['release'],'first_after_matches':o['phases']['first_after']['matches_current_phase'],'remaining_first_indices':[r['index'] for r in o['phases']['first_after']['remaining']],'retake_selection':o['retake_assignment']['count']},ensure_ascii=False,indent=2))
