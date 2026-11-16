"""Independent initial reconciliation. Standard library only; never executes course code."""
import collections
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
W = Path('/private/tmp/kuch12round')
def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def code_sha(s): return hashlib.sha256(s.encode()).hexdigest()
def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True)
def require(test, message):
    if not test: raise AssertionError(message)
def verdict_count(events):
    return {'events': len(events), 'graded': sum(type(e.get('passed')) is bool for e in events),
            'passed': sum(e.get('passed') is True for e in events), 'failed': sum(e.get('passed') is False for e in events),
            'transport_errors': sum('browserError' in e for e in events), 'hint_events': sum('hint' in e for e in events)}

out = {'scope':'ch12 initial only', 'status':'pending after and reviewer', 'execution':'stdlib JSON/CSV/hash/arithmetic only; no ML, Node, Jupyter execution', 'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
baseline = read(D/'technical/baseline.json')
out['reference'] = baseline
require(baseline['head']=='b3291d4238a7579a8ceb13bded7c027a2d90a2a0','reference HEAD')
require({s:sha(W/'original'/s) for s in baseline['source_sha256']}==baseline['source_sha256'],'frozen source SHA')
require(sha(W/'course.json')==baseline['full_export_sha256'],'full export SHA')
full, chapter, inventory = read(W/'course.json'), read(D/'technical/baseline-export.json'), read(D/'technical/inventory.json')
require([r for r in full if r['lesson'].startswith('ch12/')]==chapter,'export filter')
require({r['lesson'][5:]+'/'+r['id'] for r in chapter if r['kind']=='task'}=={k for k,v in inventory.items() if v=='task'},'task ID sets')
out['inventory'] = {'student_count':len(inventory),'student_kinds':dict(collections.Counter(inventory.values())), 'technical_count':len(chapter), 'technical_kinds':dict(collections.Counter(r['kind'] for r in chapter)), 'technical_sha256':sha(D/'technical/baseline-export.json'), 'equal_total_is_coincidental':True}
out['inventory']['predict_id_aliases']={k:k.rsplit('/',1)[0]+'/predict/'+k.rsplit('/',1)[1][1:] for k,v in inventory.items() if v=='predict'}
inventory={out['inventory']['predict_id_aliases'].get(k,k):v for k,v in inventory.items()}
S = D/'student'
manifest=read(S/'SHA256SUMS.json')
require(all(sha(S/name)==digest for name,digest in manifest.items()),'student immutable SHA')
actual_files={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}
out['student_freeze']={'manifest_entries':len(manifest),'all_hashes_match':True,'files_outside_manifest':sorted(actual_files-set(manifest)), 'missing':sorted(set(manifest)-actual_files),'manifest_sha256':sha(S/'SHA256SUMS.json')}
actual, traces, pairs=[], [], []
for p in sorted(S.glob('*.feedback.jsonl')):
    q=p.with_name(p.name.replace('.feedback.','.input.'))
    inputs, replies=rows(q), rows(p)
    require(len(inputs)==len(replies),f'paired lengths {p.name}')
    for line,(a,b) in enumerate(zip(inputs,replies),1):
        ident=a.get('question') or a['lesson']+'/'+a.get('task','')
        require(ident==b['id'],f'paired ID {p.name}:{line}')
        actual.append({**a,**b}); traces.append({'input':q.name,'feedback':p.name,'line':line})
    pairs.append({'input':q.name,'feedback':p.name,**verdict_count(replies)})
saved_raw=rows(S/'initial-attempts.jsonl')
saved=[{k:v for k,v in r.items() if k!='at'} for r in saved_raw]
raw_counter, saved_counter = collections.Counter(map(canonical,actual)), collections.Counter(map(canonical,saved))
raw_only = [json.loads(s) for s,n in (raw_counter-saved_counter).items() for _ in range(n)]
saved_only = [json.loads(s) for s,n in (saved_counter-raw_counter).items() for _ in range(n)]
require(not saved_only, 'saved payload must have exact raw counterpart')
graded_counter=collections.Counter(canonical(e) for e in actual if type(e.get('passed')) is bool)
require(graded_counter==saved_counter,'FULL graded payload multiset excluding only at')
walk=[]
for p in sorted(S.glob('*.walkthrough.jsonl')):
    for r in rows(p):
        require('Q4' in r and 'input' in r,'walkthrough full records')
        walk.append({**r['input'],**r['Q4']})
require(collections.Counter(map(canonical,walk))==collections.Counter(map(canonical,actual)),'full walkthrough Q4/input multiset')
first,first_graded,last,last_graded={}, {}, {}, {}
for lesson in ['01-resample','02-decompose','03-features','03b-time-split','04-forecast','05-project','test']:
    p=S/(lesson+'.feedback.jsonl'); q=S/(lesson+'.input.jsonl')
    for a,b in zip(rows(q),rows(p)): first[b['id']]={**a,**b}
for e in saved:
    if e.get('action')=='hint': continue
    first.setdefault(e['id'],e); last[e['id']]=e
    if type(e.get('passed')) is bool:
        first_graded.setdefault(e['id'],e); last_graded[e['id']]=e
require(set(first)==set(inventory),'student coverage ID sets')
hints=[{'id':e['id'],'hint':e['hint']} for e in actual if 'hint' in e]
require(all(bool(e.get(k)) for e in saved for k in ('Q1','Q2','Q3')),'pre-action Q1-3')
out['student']={'pairs':pairs,**verdict_count(actual),'saved_log_counts':verdict_count(saved),'full_payload_multiset_equal':raw_counter==saved_counter,'raw_only_events':raw_only,'saved_only_events':saved_only,'full_graded_payload_multiset_equal':True,'aggregate_scope':'bridge intentionally aggregates only boolean passed events; ungraded raw events are preserved in raw pairs and walkthrough, not lost','bridge_sha256':sha(W/'bridge.cjs'),'walkthrough_full_payload_equal':True,'walkthrough_events':len(walk),'first_event':verdict_count(list(first.values())),'first_graded':verdict_count(list(first_graded.values())),'latest_event':verdict_count(list(last.values())),'latest_graded':verdict_count(list(last_graded.values())),'hints':hints,'saved_time_range':[saved_raw[0]['at'],saved_raw[-1]['at']], 'event_order_sources':'first-event from seven primary lesson feedback files; first/latest graded from saved chronological log, whose entire87 graded payloads match raw; transport/hints lack saved timestamp', 'unpaired_input_files':[p.name for p in S.glob('*.input.jsonl') if not p.with_name(p.name.replace('.input.','.feedback.')).exists()], 'by_kind':{kind:{'count':sum(v==kind for v in inventory.values()),'first_event_pass':sum(e.get('passed') is True and inventory[k]==kind for k,e in first.items()),'first_graded_pass':sum(e.get('passed') is True and inventory[k]==kind for k,e in first_graded.items()),'latest_pass':sum(e.get('passed') is True and inventory[k]==kind for k,e in last.items())} for kind in sorted(set(inventory.values()))},'non_true_events':[{'payload':e,'trace':t} for e,t in zip(actual,traces) if e.get('passed') is not True], 'assistance_caveat':'select/grid each used one hint; select latest accepted is a diagnostic fit without honest cutoff, not a correct independent solution'}
# Freeze and verify each executed program, not just summary counts.
C=D/'check-evidence'
for name,digest in read(C/'frozen.sha256').items(): require(sha(C/('data-baseline/'+name if name=='app_orders.csv' else name))==digest,'checks freeze '+name)
programs=rows(C/'programs.jsonl'); expected=read(C/'expected-before-execution.json')
require(len({r['id'] for r in programs})==len(programs),'unique programs')
require(set(expected)=={r['id'] for r in programs},'declared expectations ID set')
for p in programs: require(code_sha(p['code'])==p['code_sha256']==expected[p['id']]['code_sha256'],'program SHA and declared SHA')
runtimes={}
verdicts=[]
for runtime in ('native','pyodide'):
    rr=rows(C/f'before-{runtime}.jsonl'); require({r['id'] for r in rr}==set(expected) and len(rr)==len(expected),'runtime IDs')
    source={p['id']:p for p in programs}
    for r in rr: require(r['code']==source[r['id']]['code'] and code_sha(r['code'])==r['code_sha256'],'literal runtime program')
    vv={r['id']:r['passed'] for r in rr}; verdicts.append(vv)
    mismatches=[{'id':r['id'],'group':source[r['id']]['group'],'expected':expected[r['id']]['expected'],'passed':r['passed']} for r in rr if r['passed']!=expected[r['id']]['expected']]
    runtimes[runtime]={'count':len(rr),'normative_matches':len(rr)-len(mismatches),'normative_mismatches':mismatches,'author_baselines':sum(source[r['id']]['group']=='baseline' for r in rr),'author_baselines_passed':sum(source[r['id']]['group']=='baseline' and r['passed'] is True for r in rr),'execution_failures':[r['id'] for r in rr if r.get('failure_stage')=='execution']}
require(verdicts[0]==verdicts[1],'runtime verdict parity')
out['checks']={'runtimes':runtimes,'verdict_parity':True,'groups':dict(collections.Counter(r['group'] for r in programs)),'literal_historical_WAPE':['C001','C002'],'historical_expressions_on_current_author':['C003','C004','C005','C006'],'historical_assertions_isolated_driver':['C132'],'normative_is_not_final_adjudication':True,'checks_report_sha256':sha(D/'checks.md')}
# Recompute aggregate metrics from student predictions; do not train or execute notebook.
pred=list(csv.DictReader((S/'native-august-predictions.csv').open()))
out['native_csv_columns']=list(pred[0])
require(len(pred)==744 and len({r['datetime'] for r in pred})==744,'744 unique prediction hours')
work=[r for r in pred if r['work'].lower()=='true']
require(len(work)==496,'496 work hours')
metrics={}
for name in ['model','baseline','quantile']:
    rmse=math.sqrt(sum((float(r[name])-float(r['fact']))**2 for r in pred)/len(pred))
    needed=[max(1,math.ceil(float(r['fact'])/6)) for r in work]
    staff=[max(1,math.ceil(float(r[name])/6)) for r in work]
    require(all(int(float(r['needed']))==n and int(float(r['staff_'+name]))==p for r,n,p in zip(work,needed,staff)),'staff CSV '+name)
    deficit=sum(max(n-p,0) for n,p in zip(needed,staff)); extra=sum(max(p-n,0) for n,p in zip(needed,staff))
    metrics[name]={'rmse':rmse,'deficit':deficit,'extra':extra,'cost3_1':3*deficit+extra,'short_hours':sum(n>p for n,p in zip(needed,staff)),'working_hours':len(work),'forecast_cover':sum(float(r['fact'])<=float(r[name]) for r in work)}
require(abs(metrics['model']['rmse']-read(S/'native-metrics.json')['rmse_final'])<1e-12,'native recorded RMSE')
out['native_own_csv_recalculation']=metrics
out['native_own_csv_recalculation_limitation']='Independent arithmetic on submitted predictions, not regeneration from trained models.'
out['native_recorded']=read(S/'native-metrics.json')
out['notebook_checker']={'log_sha256':sha(S/'notebook-check.log'),'fix':0,'inspect':0,'no_run':True,'business_goal_fulfilled':False}
out['interpretation']={'methodist_independent_scores':[4,4,3,3,3],'methodist_mean':3.4,'historical_numbered_findings':14,'business_new_ids':['B12-01','B12-02','B12-03','B12-04'],'test_questions':13,'test_options':52,'test_explanations':52,'test_new_ids':['T12-01','T12-02','T12-03','T12-04','T12-05','T12-06'],'native_result_negative':True,'calendar_defect':'August 21 exists in hidden setup but is absent from initial public student package; not student fault','full_history_with_published_august_calendar_rmse':4.227,'retake_and_reviewer_required':True}
out['report_reference_sha256']={name:sha(D/name) for name in ['expert.md','previous.md','methodist.md','business.md','test-review.md','checks.md']}
(D/'coordination-initial.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['inventory','student_freeze','native_csv_columns']},ensure_ascii=False,indent=2))
print('student raw',verdict_count(actual),'saved',verdict_count(saved),'first',out['student']['first_event'],'first graded',out['student']['first_graded'],'latest',out['student']['latest_event'])
print('checks',[(k,v['count'],v['normative_matches']) for k,v in runtimes.items()])
