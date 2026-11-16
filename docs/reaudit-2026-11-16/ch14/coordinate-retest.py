"""Run only after root confirms retake immutable freeze. stdlib, no course execution.
Preserves complete input/feedback/aggregate payloads, Q1–4 and multiplicity.
Known deliberate format diagnostics remain separate from natural attempts.
"""
from pathlib import Path
import argparse,collections,hashlib,json
D=Path(__file__).resolve().parent;S=D/'fixes/student/retest';M=D/'technical/retest-package'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def can(x):return json.dumps(x,ensure_ascii=False,sort_keys=True)
def counts(es):return {'events':len(es),'graded':sum(type(e.get('passed')) is bool for e in es),'true':sum(e.get('passed') is True for e in es),'false':sum(e.get('passed') is False for e in es),'browserError':sum('browserError' in e for e in es),'hint':sum('hint' in e for e in es)}
a=argparse.ArgumentParser();a.add_argument('--frozen',action='store_true');arg=a.parse_args()
if not arg.frozen:print('HOLD: run --frozen only after root confirms final student retake manifest; no partial retake read or counted');raise SystemExit
manifest={s.split('  ',1)[1]:s.split('  ',1)[0] for s in (S/'SHA256SUMS').read_text().splitlines() if s.strip()};assert all(sha(S/p)==v for p,v in manifest.items())
reference=read(M/'reference.json');targets=set(reference['selection']['tasks']+reference['selection']['questions']);actual=[];pairs=[];expected_walk=[];diagnostics=[];natural=[];source_for_event={}
for p in sorted(S.glob('*-feedback.jsonl')):
 q=p.with_name(p.name.replace('-feedback','-input'));aa,ff=rows(q),rows(p);assert len(aa)==len(ff),p
 for i,(a,f) in enumerate(zip(aa,ff),1):
  assert (a.get('question') or a['lesson']+'/'+a['task'])==f['id'];assert all(a.get(k) for k in ['Q1','Q2','Q3']);e={**a,**f};actual.append(e);expected_walk.append({'source':p.name,'input':a,'actual':f});source_for_event.setdefault(can(e),[]).append({'source':p.name,'line':i})
  diagnostic=bool(a.get('diagnostic')) or 'diagnostic' in p.name.lower() or 'known-format' in p.name.lower()
  (diagnostics if diagnostic else natural).append(e)
 pairs.append({'input':q.name,'feedback':p.name,'input_sha256':sha(q),'feedback_sha256':sha(p),**counts(ff)})
assert actual,'no retake raw pairs'
savedraw=rows(S/'attempts.jsonl');saved=[{k:v for k,v in e.items() if k!='at'} for e in savedraw];graded=[e for e in actual if type(e.get('passed')) is bool]
assert [e['at'] for e in savedraw]==sorted(e['at'] for e in savedraw)
assert collections.Counter(map(can,graded))==collections.Counter(map(can,saved)),'FULL code/choice/prompt/output/images/multiplicity equality excluding onlyat'
walk=rows(S/'walkthrough.jsonl');assert all(e.get('Q4') for e in walk);assert collections.Counter(can({k:e[k] for k in ['source','input','actual']}) for e in walk)==collections.Counter(map(can,expected_walk)),'FULL walkthrough input Q1–3 + actual equality'
latest={};firstgraded={}
for e in saved:
 if e['id'] in targets:firstgraded.setdefault(e['id'],e);latest[e['id']]=e
assert targets==set(latest),'all38 target IDs graded'
firstnatural={}
# Q4 order is retained by the learner; source mapping identifies known diagnostic files.
for e in walk:
 a,f=e['input'],e['actual'];diag=bool(a.get('diagnostic')) or 'diagnostic' in e['source'].lower() or 'known-format' in e['source'].lower()
 if not diag and f['id'] in targets:firstnatural.setdefault(f['id'],{**a,**f})
assert targets==set(firstnatural),'all38 natural target first actions present'
initial={}
for name,root in [('initial',D/'student'),('holdout_predictions',D/'fixes/student/holdout-predictions'),('holdout_evaluation',D/'fixes/student/holdout-evaluation')]:
 mm={s.split('  ',1)[1]:s.split('  ',1)[0] for s in (root/'SHA256SUMS').read_text().splitlines() if s.strip()};assert all(sha(root/p)==v for p,v in mm.items());initial[name]={'count':len(mm),'manifest_sha256':sha(root/'SHA256SUMS'),'unchanged':True}
out={'scope':'addressed retake38 only; known diagnostics separate; no synthetic full final94rerun claimed','manifest':{'count':len(manifest),'SHA':sha(S/'SHA256SUMS'),'all_match':True,'outside_manifest':sorted(str(p.relative_to(S)) for p in S.rglob('*') if p.is_file() and str(p.relative_to(S)) not in manifest)},'selection':reference['selection'],'pairs':pairs,'raw':counts(actual),'aggregate':counts(saved),'natural':counts(natural),'known_deliberate_diagnostics':counts(diagnostics),'full_graded_payload_multiset_equal':True,'walkthrough_count':len(walk),'walkthrough_full_Q1_Q3_actual_equal':True,'Q4_all_present':True,'first_natural_action_on_targets':counts(list(firstnatural.values())),'first_graded_on_targets_including_any_known_diagnostic_if_earlier':counts(list(firstgraded.values())),'latest_graded_on_targets':counts(list(latest.values())),'nonpass_full_payload':[{'payload':e,'raw_trace':source_for_event[can(e)]} for e in actual if e.get('passed') is not True],'per_ID':{i:{'events':sum(e['id']==i for e in actual),'latest_pass':latest[i].get('passed'),'first_natural_pass':firstnatural[i].get('passed')} for i in sorted(targets)},'prior_freezes':initial,'caveat':'Any intentionally wrong known-format diagnostic not explicitly marked by field or filename remains visible in natural counts until coordinator adjudicates; never silently reclassify an unknown failure.'}
(D/'coordination-retest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['manifest','raw','aggregate','natural','known_deliberate_diagnostics','first_natural_action_on_targets','latest_graded_on_targets','prior_freezes']},ensure_ascii=False,indent=2))
