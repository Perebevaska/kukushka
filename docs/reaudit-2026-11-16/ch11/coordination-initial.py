"""Read-only initial reconciliation; standard library only, no model execution."""
import collections
import csv
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
W = Path('/private/tmp/kuch11round')
def read(p):
    return json.loads(p.read_text())
def rows(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)
def require(test, msg):
    if not test:
        raise AssertionError(msg)

out = {'scope': 'ch11 initial only', 'status': 'not accepted', 'execution': 'stdlib JSON/CSV/SHA only'}
baseline = read(D/'technical/baseline.json')
out['baseline'] = baseline
out['source_hashes'] = {s: sha(W/'original'/s) for s in baseline['sources']}
require(out['source_hashes'] == baseline['sources'], 'immutable baseline source hashes')
full = read(W/'course.json')
chapter = read(D/'technical/baseline-export.json')
require([x for x in full if x['lesson'].startswith('ch11/')] == chapter, 'full export filter')
require(sha(W/'course.json') == baseline['export_sha256'], 'full export hash')
out['export'] = {'full_count': len(full), 'chapter_count': len(chapter), 'chapter_sha256': sha(D/'technical/baseline-export.json'), 'kinds': dict(collections.Counter(x['kind'] for x in chapter))}
inventory = read(D/'technical/inventory.json')
out['inventory'] = {'count': len(inventory), 'kinds': dict(collections.Counter(inventory.values()))}
require({x['lesson'][5:]+'/'+x['id'] for x in chapter if x['kind']=='task'} == {k for k,v in inventory.items() if v=='task'}, 'task IDs')

events, pair_summary = [], []
for feedback in sorted((D/'student').glob('*.feedback.jsonl'), key=lambda p:p.stat().st_mtime_ns):
    source = feedback.with_name(feedback.name.replace('.feedback.', '.input.'))
    inputs, replies = rows(source), rows(feedback)
    require(len(inputs)==len(replies), str(feedback)+' row count')
    summary = {'input': str(source.relative_to(D)), 'feedback': str(feedback.relative_to(D)), 'count': len(inputs)}
    for line, (a,b) in enumerate(zip(inputs,replies),1):
        aid = a.get('question') or (a['lesson']+'/'+a.get('task', ''))
        require(b['id'] == aid, f'{source}:{line} ID')
        e = {**a, **b}
        events.append((e, {'input':str(source.relative_to(D)), 'feedback':str(feedback.relative_to(D)), 'line':line}))
    summary['passed'] = sum(b.get('passed') is True for b in replies)
    summary['false'] = sum(b.get('passed') is False for b in replies)
    summary['browser_errors'] = sum('browserError' in b for b in replies)
    pair_summary.append(summary)
actual = [e for e,t in events]
saved = [{k:v for k,v in x.items() if k!='at'} for x in rows(D/'student/initial-attempts.jsonl')]
require(collections.Counter(map(canonical,actual)) == collections.Counter(map(canonical,saved)), 'entire input-feedback multiset except at')
# The saved sequence supplies actual submission order; pairing above proves its payload.
first,last={},{}
for e in saved:
    first.setdefault(e['id'],e)
    last[e['id']]=e
require(set(last)==set(inventory), 'inventory/submission coverage')
out['student'] = {'pairs':pair_summary, 'event_count':len(actual), 'graded':sum(type(e.get('passed')) is bool for e in actual), 'true':sum(e.get('passed') is True for e in actual), 'false':sum(e.get('passed') is False for e in actual), 'browser_errors':sum('browserError' in e for e in actual), 'full_payload_multiset_equal':True, 'first_accepted':sum(e.get('passed') is True for e in first.values()), 'latest_accepted':sum(e.get('passed') is True for e in last.values()), 'by_kind': {kind:{'count':sum(v==kind for v in inventory.values()),'first':sum(e.get('passed') is True and inventory[k]==kind for k,e in first.items()),'last':sum(e.get('passed') is True and inventory[k]==kind for k,e in last.items())} for kind in set(inventory.values())}, 'non_true':[{'payload':e,'trace':t,'code_sha256':hashlib.sha256(e.get('code','').encode()).hexdigest()} for e,t in events if e.get('passed') is not True], 'nonempty_expect':sum(bool(e.get('expect')) for e in actual)}
freeze=[]
for line in (D/'student/FREEZE.sha256').read_text().splitlines():
    h,name=line.split(maxsplit=1)
    require(sha(D/'student'/name)==h, 'student freeze '+name)
    freeze.append(name)
out['student']['frozen_count']=len(freeze)

def bundle(folder, suffix='', expected_key='expected'):
    n=rows(folder/f'before{suffix}-native.jsonl')
    p=rows(folder/f'before{suffix}-pyodide.jsonl')
    programs=rows(folder/('programs.jsonl' if not suffix else 'supplement-programs.jsonl'))
    if folder.name=='reviewer-evidence':
        exp={r['id']:r[expected_key] for r in programs}
    else:
        declared=read(folder/('expected-before-execution.json' if not suffix else 'supplement-expected-before-execution.json'))
        exp={r['id']:r['expected'] for r in declared}
        declared_hash={r['id']:r['code_sha256'] for r in declared}
        require(declared_hash=={r['id']:hashlib.sha256(r['code'].encode()).hexdigest() for r in programs},'frozen expectations/program hashes')
    require(set(exp)=={r['id'] for r in n}=={r['id'] for r in p},'bundle ID sets')
    require({r['id']:r['passed'] for r in n}=={r['id']:r['passed'] for r in p},'runtime verdict parity')
    for r in n+p:
        if 'code' in r:
            require(hashlib.sha256(r['code'].encode()).hexdigest()==r['code_sha256'],'code SHA')
            require(r['code']==next(p['code'] for p in programs if p['id']==r['id']),'literal executed program')
    return {'count':len(n),'matches':sum(r['passed']==exp[r['id']] for r in n),'parity':len(n),'false_accept':[r['id'] for r in n if r['passed'] and not exp[r['id']]],'false_reject':[r['id'] for r in n if not r['passed'] and exp[r['id']]],'program_sha256':{r['id']:hashlib.sha256(r['code'].encode()).hexdigest() for r in programs},'groups':dict(collections.Counter(r.get('group','reviewer') for r in programs))}
out['checks_main']=bundle(D/'check-evidence')
out['checks_supplement']=bundle(D/'check-evidence','-supplement')
out['reviewer']=bundle(D/'fixes/reviewer-evidence',expected_key='expected_before')
ledger=list(csv.DictReader((D/'fixes/ledger.csv').open()))
prior=read(D/'technical/prior-findings.json')
require(len({r['id'] for r in ledger})==len(ledger),'unique ledger IDs')
require({r['id'] for r in prior} <= {r['id'] for r in ledger},'prior decisions')
out['ledger']={'prior_count':len(prior),'rows':ledger,'current_count':len(ledger),'additional_recipient':'RCP11-01','total_including_recipient':len(ledger)+('RCP11-01' not in {r['id'] for r in ledger})}
manifest=read(D/'fixes/recipient-evidence/manifest.json')
for package, files in manifest.items():
    for name,h in files.items():
        require(sha(D/'fixes/recipient-evidence/first-inputs'/package/name)==h,'recipient frozen '+name)
out['recipient']={'frozen_input_count':sum(map(len,manifest.values())),'verification':read(D/'fixes/recipient-evidence/verification.json'),'full450_reprediction':False}
evaluation=list(csv.DictReader((D/'fixes/recipient-evidence/first-inputs/digits/evaluation.csv').open()))
require(len({r['position'] for r in evaluation})==len(evaluation),'unique positions')
require(len({r['original_index'] for r in evaluation})==len(evaluation),'unique original indices')
selected=sorted(evaluation,key=lambda r:(float(r['confidence']),int(r['position'])))[:37]
queue={r['position'] for r in selected}
errors=[r for r in evaluation if r['truth']!=r['prediction']]
require(all((r['review'].lower()=='true')==(r['position'] in queue) for r in evaluation),'review flags')
out['own_csv_recalculation']={'n':len(evaluation),'correct':len(evaluation)-len(errors),'accuracy':1-len(errors)/len(evaluation),'errors':len(errors),'queue':len(queue),'caught':sum(r['position'] in queue for r in errors),'missed':sum(r['position'] not in queue for r in errors),'review_share':len(queue)/len(evaluation),'selected_positions':[int(r['position']) for r in selected], 'limitation':'recalculation of supplied table, not new predictions from pixels'}
(D/'coordination-initial.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k in ['export','inventory','checks_main','checks_supplement','reviewer','own_csv_recalculation']},ensure_ascii=False,indent=2))
