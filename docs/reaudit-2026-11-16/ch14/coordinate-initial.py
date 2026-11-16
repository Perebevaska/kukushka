"""Read-only evidence reconciliation (stdlib); writes coordinator outputs only."""
from pathlib import Path
import json,hashlib,collections,re,datetime,csv
D=Path(__file__).resolve().parent;W=Path('/private/tmp/kuch14round');S=D/'student'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def can(x):return json.dumps(x,ensure_ascii=False,sort_keys=True)
def stats(rr):return {'events':len(rr),'graded':sum(type(r.get('passed')) is bool for r in rr),'true':sum(r.get('passed') is True for r in rr),'false':sum(r.get('passed') is False for r in rr),'browserError':sum('browserError' in r for r in rr),'hint':sum('hint' in r for r in rr)}
b=read(D/'technical/baseline.json');inv=read(D/'technical/inventory.json');exp=read(D/'technical/baseline-export.json')
assert sha(W/'course.json')==b['full_export_sha256'];assert all(sha(W/'original'/p)==v for p,v in b['source_sha256'].items());assert all(sha(D/'technical/data-baseline'/p)==v for p,v in b['data_sha256'].items())
assert {r['lesson'][5:]+'/'+r['id'] for r in exp if r['kind']=='task'}=={k for k,v in inv.items() if v=='task'}
actual=[];pairs=[];joined_by_source={}
for p in sorted(S.glob('*-feedback.jsonl')):
 q=p.with_name(p.name.replace('-feedback','-input'));aa,ff=rows(q),rows(p);assert len(aa)==len(ff),p
 joined_by_source[p.name]=[]
 for a,f in zip(aa,ff):
  assert (a.get('question') or a['lesson']+'/'+a['task'])==f['id'];assert all(a.get(k) for k in ['Q1','Q2','Q3'])
  e={**a,**f};actual.append(e);joined_by_source[p.name].append((a,f))
 pairs.append({'input':q.name,'feedback':p.name,**stats(ff),'input_sha256':sha(q),'feedback_sha256':sha(p)})
savedraw=rows(S/'initial-attempts.jsonl');saved=[{k:v for k,v in e.items() if k!='at'} for e in savedraw]
assert [r['at'] for r in savedraw]==sorted(r['at'] for r in savedraw)
graded=[r for r in actual if type(r.get('passed')) is bool];assert collections.Counter(map(can,graded))==collections.Counter(map(can,saved))
walk=rows(S/'walkthrough.jsonl');expected=[{'source':p,'input':a,'actual':f} for p,v in joined_by_source.items() for a,f in v]
assert all(e.get('Q4') for e in walk);assert collections.Counter(can({k:e[k] for k in ['source','input','actual']}) for e in walk)==collections.Counter(map(can,expected))
first={};fg={};latest={}
for lesson in b['lesson_order']:
 p=S/(lesson+'-feedback.jsonl')
 if p.exists():
  for r in rows(p):first.setdefault(r['id'],r)
for e in saved:fg.setdefault(e['id'],e);latest[e['id']]=e
assert set(first)==set(fg)==set(latest)==set(inv)
freeze={'status':'not yet frozen; file SHA snapshot provisional'}
if (S/'SHA256SUMS').exists():
 manifest={s.split('  ',1)[1]:s.split('  ',1)[0] for s in (S/'SHA256SUMS').read_text().splitlines() if s.strip()};assert all(sha(S/p)==v for p,v in manifest.items());freeze={'status':'frozen SHA all match','entries':len(manifest),'manifest_sha256':sha(S/'SHA256SUMS'),'outside_manifest':sorted(str(p.relative_to(S)) for p in S.rglob('*') if p.is_file() and str(p.relative_to(S)) not in manifest)}
checks={}
for name,folder in [('main',D/'technical/checks'),('supplement',D/'technical/checks/key-supplement')]:
 pp=rows(folder/'programs.jsonl');runs={}
 for rt in ['native','pyodide']:
  rr=rows(folder/('before-'+rt+'.jsonl'));assert len(pp)==len(rr)
  for p,r in zip(pp,rr):
   assert all(r[k]==v for k,v in p.items()),(name,rt,r.get('index'));assert hashlib.sha256(p['code'].encode()).hexdigest()==p['code_sha256']
  runs[rt]={'count':len(rr),'passed':sum(r['passed'] is True for r in rr),'normative_mismatch':[{'index':i,'label':r['label'],'expected':r['expected'],'actual':r['passed']} for i,r in enumerate(rr) if r['passed']!=r['expected']],'sha256':sha(folder/('before-'+rt+'.jsonl'))}
 checks[name]={'programs':len(pp),'programs_sha256':sha(folder/'programs.jsonl'),'runs':runs}
prior=read(D/'previous.json')['rows'];current=[]
for filename,prefix in [('expert.md','E14-'),('methodist.md','M14-26-'),('business.md','B14-'),('checks.md','A14-'),('test-review.md','Q14-')]:
 text=(D/filename).read_text();ids=list(dict.fromkeys(re.findall(r'\b'+re.escape(prefix)+r'\d{2}\b',text)))
 for ident in ids:current.append({'source':filename,'id':ident,'stage':'before','reviewer':'see review-before.md; execution pending reviewer own runtime','after':'pending'})
for ident in list(dict.fromkeys(re.findall(r'\b(?:ST-14-(?:H)?\d{2})\b',(S/'report.md').read_text()))):current.append({'source':'student/report.md','id':ident,'stage':'before','reviewer':'pending observation vs recommendation adjudication','after':'pending'})
current.append({'source':'review-before.md','id':'REVIEW14-FLAT','stage':'before','reviewer':'independent reviewer source finding; own execution pending','after':'pending'})
o={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'initial before only; stdlib evidence read/hash/payload reconciliation; no course execution','baseline_head':b['head'],'inventory':{'student':len(inv),'kinds':dict(collections.Counter(inv.values())),'technical':len(exp),'technical_kinds':dict(collections.Counter(r['kind'] for r in exp))},'freeze':freeze,'student':{'pairs':pairs,'raw':stats(actual),'aggregate':stats(saved),'full_graded_payload_multiset_equal':True,'walkthrough_full_input_Q1_Q3_actual_equal':True,'walkthrough_Q4_nonempty':True,'walkthrough_count':len(walk),'first_raw':stats(list(first.values())),'first_graded':stats(list(fg.values())),'latest_graded':stats(list(latest.values())),'by_kind':{kind:{'count':sum(v==kind for v in inv.values()),'first_raw_pass':sum(inv[k]==kind and r.get('passed') is True for k,r in first.items()),'first_graded_pass':sum(inv[k]==kind and r.get('passed') is True for k,r in fg.items()),'latest_pass':sum(inv[k]==kind and r.get('passed') is True for k,r in latest.items())} for kind in sorted(set(inv.values()))},'nonpass_full_payload':[r for r in actual if r.get('passed') is not True],'aggregate_timestamp_range':[savedraw[0]['at'],savedraw[-1]['at']]},'checks':checks,'source_ledger':{'historical_count':len(prior),'historical':prior,'current_count':len(current),'current':current,'meaning':'source messages and aspects retained; overlaps not unique defects'},'independence_limitation':'Student pre-read all theory/19figures during CPU hold, including published transfer evening aggregates of day2. Own project k/model freeze precedes own second-day calculation, but initial cannot be labelled blind. Unseen audit seed14016 is a separate pending denominator.'}
(D/'coordination-initial.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');(D/'coverage.json').write_text(json.dumps({'inventory':inv,'initial':o['student']['by_kind'],'historical_source_ledger':prior,'current_source_ledger':current,'pending':['student immutable SHA freeze','reviewer own before runtime','holdout14016 prediction freeze and evaluation','source changes and after runtimes','addressed student retake','methodist after score and independent final review']},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:o[k] for k in ['inventory','freeze']},ensure_ascii=False));print({k:o['student'][k] for k in ['raw','aggregate','first_raw','first_graded','latest_graded']});print('source ledger',len(prior),len(current))
