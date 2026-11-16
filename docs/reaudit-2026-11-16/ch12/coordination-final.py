"""Final independent reconciliation: standard library only, no course/model execution."""
import collections, csv, datetime, hashlib, json, math, re
from pathlib import Path
D=Path(__file__).resolve().parent
ROOT=D.parents[2]
W=Path('/private/tmp/kuch12round')
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True)
def require(v,msg):
    if not v:raise AssertionError(msg)
def counter(v):return collections.Counter(map(canon,v))
def freeze(folder):
    manifest=read(folder/'SHA256SUMS.json')
    require(all(sha(folder/n)==h for n,h in manifest.items()),'frozen evidence '+str(folder))
    return {'count':len(manifest),'manifest_sha256':sha(folder/'SHA256SUMS.json'),'verified':True}
def events(folder,q4):
    result=[];trace=[]
    for p in sorted(folder.glob('*.feedback.jsonl')):
        inp=p.with_name(p.name.replace('.feedback.','.input.'));a,b=rows(inp),rows(p)
        require(len(a)==len(b),'pair length '+p.name)
        for n,(x,y) in enumerate(zip(a,b),1):
            require((x.get('question') or x['lesson']+'/'+x['task'])==y['id'],'pair ID')
            result.append({**x,**y});trace.append({'input':inp.name,'feedback':p.name,'line':n})
    ww=[{**r['input'],**r[q4]} for p in sorted(folder.glob('*.walkthrough.jsonl')) for r in rows(p)]
    require(counter(result)==counter(ww),'FULL input/Q4 multiset '+str(folder))
    return result,trace
out={'status':'accepted','scope':'chapter12 only','reference_head':'b3291d4238a7579a8ceb13bded7c027a2d90a2a0','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution':'stdlib read/hash/CSV arithmetic only; no ML/Node/Jupyter'}
S=D/'student';R=D/'fixes/student/retest';C=D/'fixes/student/decision-closure'
out['freezes']={n:freeze(p) for n,p in [('initial',S),('retake',R),('decision',C)]}
initial,itrace=events(S,'Q4');retake,rtrace=events(R,'Q4_raw');decision,dtrace=events(C,'Q4_raw')
aggregate=[{k:v for k,v in x.items() if k!='at'} for x in rows(S/'initial-attempts.jsonl')]
require(counter(aggregate)==counter([x for x in initial if type(x.get('passed')) is bool]),'aggregate FULL graded payload except at')
require(len(initial)==90 and len(aggregate)==87,'initial scope')
require(sum(e.get('passed') is True for e in aggregate)==79 and sum(e.get('passed') is False for e in aggregate)==8,'initial grading')
require(len(retake)==47 and len({e['id'] for e in retake})==47 and all(e.get('passed') is True for e in retake),'retake first pass')
require(len(decision)==1 and decision[0]['passed'] is True and decision[0]['id'] in {e['id'] for e in retake},'closure repeats existing ID')
inv=read(D/'technical/inventory.json');aliases={k:k.rsplit('/',1)[0]+'/predict/'+k.rsplit('/',1)[1][1:] for k,v in inv.items() if v=='predict'};inv={aliases.get(k,k):v for k,v in inv.items()}
require({e['id'] for e in initial}==set(inv),'initial inventory coverage')
targets=read(R/'targets.json')['targets'];require({x['id'] for x in targets}=={x['id'] for x in retake},'target IDs')
first={};firstgraded={}
for lesson in ['01-resample','02-decompose','03-features','03b-time-split','04-forecast','05-project','test']:
    for e in rows(S/(lesson+'.feedback.jsonl')):first[e['id']]=e
for e in aggregate:firstgraded.setdefault(e['id'],e)
out['student']={'inventory':len(inv),'kinds':dict(collections.Counter(inv.values())),'initial_raw':len(initial),'initial_graded':len(aggregate),'initial_true':79,'initial_false':8,'initial_transport':sum('browserError'in e for e in initial),'initial_hints':sum('hint'in e for e in initial),'ungraded_traces':[t for e,t in zip(initial,itrace) if type(e.get('passed')) is not bool],'first_event_accepted':sum(e.get('passed') is True for e in first.values()),'first_graded_accepted':sum(e['passed'] is True for e in firstgraded.values()),'initial_eventual_accepted':len({e['id'] for e in initial if e.get('passed') is True}),'initial_select_caveat':'latest accepted fit was diagnostic, not a correct availability solution','raw_full_walkthrough_parity':True,'aggregate_full_graded_payload_parity':True,'retake_events':47,'retake_unique':47,'retake_first_pass':47,'retake_kinds':dict(collections.Counter(x['kind'] for x in targets)),'retake_hints':sum('hint'in e for e in retake),'closure_events':1,'closure_id':decision[0]['id'],'positive_retake_plus_closure_events':48,'unique_retake_plus_closure_ids':len({e['id'] for e in retake+decision})}
checks=D/'check-evidence';phase=read(checks/'expected-phase.json');programs={r['id']:r for r in rows(checks/'programs.jsonl')}
require(set(programs)==set(phase),'phase IDs')
checked={}
for suffix,programfile in [('', 'programs.jsonl'),('-supplement','supplement-programs.jsonl'),('-migration','migration-programs.jsonl')]:
    pp={r['id']:r for r in rows(checks/programfile)};vs=[];ms=[];olds=[]
    for runtime in ['native','pyodide']:
        rr=rows(checks/f'after{suffix}-{runtime}.jsonl');require(len(rr)==len(pp) and {r['id'] for r in rr}==set(pp),'after IDs '+suffix)
        for r in rr:require(r['code']==pp[r['id']]['code'] and hashlib.sha256(r['code'].encode()).hexdigest()==r['code_sha256'],'literal executed code')
        expect={k:(phase[k]['expected_current_contract'] if not suffix else v['expected']) for k,v in pp.items()}
        require(all(r['passed']==expect[r['id']] for r in rr),'after expected '+suffix)
        vs.append({r['id']:r['passed'] for r in rr})
        ms.append(sum(r['passed']==expect[r['id']] for r in rr))
        if not suffix:olds.append(sum(r['passed']==phase[r['id']]['expected_original'] for r in rr))
    require(vs[0]==vs[1],'runtime parity '+suffix)
    checked[suffix or 'original132']={'count':len(pp),'expected_matches_each_runtime':ms,'original_expected_matches_each_runtime':olds,'ids':sorted(pp),'verdict_parity':True}
out['checks']=checked
out['explicit_migrations']=[k for k,v in phase.items() if v['expected_original']!=v['expected_current_contract']]
require(len(out['explicit_migrations'])==7,'seven explicit migrations')
# Reviewer cases have their own stable IDs and one deliberately retained error.
F=D/'fixes/reviewer-evidence';exp=read(F/'expected-after.json');allreview=[];reviewgroups={}
for suf,pfile in [('', 'programs.jsonl'),('-additional','additional.jsonl'),('-revised','revised-programs.jsonl')]:
    pp=rows(F/pfile);ids={p['id'] for p in pp};pair=[]
    for runtime in ['native','pyodide']:
        rr=rows(F/f'after{suf}-{runtime}.jsonl');require({r['id'] for r in rr}==ids and len(rr)==len(ids),'reviewer IDs')
        require(all(r['passed']==(exp[r['id']]['after'] if r['id'] in exp else next(p['expected'] for p in pp if p['id']==r['id'])) for r in rr),'reviewer outcomes')
        pair.append({r['id']:r['passed'] for r in rr})
    require(pair[0]==pair[1],'reviewer parity');allreview.extend(ids);reviewgroups[suf or 'original']={'count':len(ids),'ids':sorted(ids),'expected_matches_each_runtime':len(ids)}
require(len(allreview)==len(set(allreview))==24,'unique reviewer cases')
out['reviewer_cases']={'groups':reviewgroups,'unique':24,'content_checks':23,'recorded_own_error':'future-no-target KeyError; corrected future-public-roll is separate'}
ledger=(D/'fixes/ledger-after.md').read_text();ids=re.findall(r'^\| ([A-Z][A-Z0-9-]*\d[A-Z0-9-]*) \|',ledger,re.M);cross=[i for i in ids if i.startswith('CH12-ST-R')];source=[i for i in ids if i not in cross]
require(len(source)==len(set(source))==59 and len(cross)==len(set(cross))==9,'59 source and9 crosswalk IDs')
out['ledger']={'source_ids':source,'source_id_count':59,'verification_crosswalk_ids':cross,'verification_id_count':9,'not_independent_bug_count':True,'review_sha256':sha(D/'fixes/review.md')}
require('Глава принята' in (D/'fixes/review.md').read_text(),'official accepted reviewer')
# Recalculate saved predictions and every pre-fact batch, without fitting models.
a=list(csv.DictReader((R/'native-august-predictions.csv').open()));before=list(csv.DictReader((S/'native-august-predictions.csv').open()));require(len(a)==744 and len({r['datetime'] for r in a})==744,'744 unique hours');work=[r for r in a if r['work'].lower()=='true'];require(len(work)==496,'496 work hours')
metrics={}
for name in ['model','baseline','quantile']:
    need=[max(1,math.ceil(float(r['fact'])/6)) for r in work];staff=[max(1,math.ceil(float(r[name])/6)) for r in work]
    for r in a:require(int(r['staff_'+name])==(max(1,math.ceil(float(r[name])/6)) if r['work'].lower()=='true' else 0),'schedule zero outside work')
    deficit=sum(max(n-p,0) for n,p in zip(need,staff));extra=sum(max(p-n,0) for n,p in zip(need,staff))
    metrics[name]={'all_rmse':math.sqrt(sum((float(r[name])-float(r['fact']))**2 for r in a)/744),'work_rmse':math.sqrt(sum((float(r[name])-float(r['fact']))**2 for r in work)/496),'deficit':deficit,'extra':extra,'cost3_1':3*deficit+extra,'covered_work':sum(float(r['fact'])<=float(r[name]) for r in work),'short_hours':sum(n>p for n,p in zip(need,staff)),'changed_vs_initial':[r['datetime'] for r,b in zip(a,before) if float(r[name])!=float(b[name])]}
lookup={r['datetime']:r for r in a};batch=[]
for p in sorted((R/'issued').glob('*.csv')):
    rr=list(csv.DictReader(p.open()));require(len(rr)==24 and len({r[''] for r in rr})==24,'24 unique targets')
    for r in rr:
        target=datetime.datetime.fromisoformat(r['']);issue=datetime.datetime.fromisoformat(r['issue']);cut=datetime.datetime.fromisoformat(r['cutoff']);require(issue.hour==20 and cut==issue-datetime.timedelta(hours=1) and issue.date()==target.date()-datetime.timedelta(days=1),'issue cutoff dates')
        require(all(float(r[k])==float(lookup[r['']][k]) for k in ['model','baseline','quantile']),'batch forecast equals saved CSV')
    require('fact' not in rr[0],'pre fact batch');batch.append(p.name)
require(len(batch)==31,'31 issued batches')
out['native_csv_recalculation']={'all_hours':744,'work_hours':496,'plans':metrics,'batches':31,'pre_fact_values':31*24*3,'limitation':'saved CSV arithmetic only; independent model refit belongs to business critic'}
capacity={}
for c in [6,5]:capacity[str(c)]={str(staff):sum(180*max(max(1,math.ceil(y/c))-staff,0)+100*max(staff-max(1,math.ceil(y/c)),0) for y in [13,0,11]) for staff in [2,3]}
require(capacity=={'6':{'2':280,'3':300},'5':{'2':460,'3':200}},'capacity-only decision')
out['capacity_only']=capacity
release=read(D/'technical/release.json');require(all(sha(ROOT/p)==h for p,h in release['files'].items()),'actual release SHA')
require(sha(W/'final.json')==release['full_course_export_sha256'],'final export SHA')
closure=read(D/'technical/business-closure-reference.json');require(sha(ROOT/'content/ch12/05-project.md')==closure['source_sha256'],'late public source phase')
retakeref=read(R/'final-reference.json');out['phase_references']={'frozen_retake':retakeref,'late_business_closure':closure,'frozen_retake_is_not_overwritten':True}
out['session_closure']=read(D/'technical/session-closure.json')
out['release']={'files':len(release['files']),'export_sha256':release['full_course_export_sha256'],'standard_records':79,'notebook_solutions':46,'notebook_starters':46,'verification':read(D/'technical/release-verification.json'),'ui':read(D/'technical/test-ui.json'),'static_test':read(D/'technical/test-after-checks.json')}
require(out['release']['static_test']['html_sha256']==sha(ROOT/'site/ch12/test.html'),'static test current actual HTML')
require(not out['release']['verification']['issues'],'release verification no issues')
out['methodist']={'initial':[4,4,3,3,3],'final':[5,5,4,4,5],'initial_mean':3.4,'final_mean':4.6,'external':'human letter handoff, pace and retention after break; unseen period; real staffing prices and productivity'}
out['roles']={'student':'Sol medium','expert':'Astra high','checks':'Sol high','test_critic':'Sol medium','methodist':'Astra high','business':'Astra high','reviewer':'Astra high','coordinator':'Sol medium'}
(D/'coordination-final.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
coverage={'status':'accepted','student_inventory':inv,'coverage':out['student'],'freezes':out['freezes'],'review_ledger':out['ledger'],'technical_sets':out['checks'],'release_export_sha256':out['release']['export_sha256']};(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':out['status'],'freezes':out['freezes'],'retake':out['student']['retake_unique'],'closure':1,'source_ids':59,'crosswalk':9,'reviewer_cases':24,'release_files':len(release['files'])},ensure_ascii=False,indent=2))
