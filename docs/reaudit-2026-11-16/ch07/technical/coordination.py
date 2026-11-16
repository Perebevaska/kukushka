"""Independent inventory, raw submission, release and historical-ledger reconciliation."""
import json,re,collections,hashlib,datetime
from pathlib import Path
D=Path(__file__).resolve().parents[1]; ROOT=D.parents[2]; S=D/'student'
def read(p):
 return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def sig(r): return json.dumps({k:r[k] for k in ('id','code','question','choice','expect','passed','feedback','visible_output','score') if k in r},ensure_ascii=False,sort_keys=True)
pairs=[]; merged=[]; nonbool=[]; errors=[]
for f in sorted(S.glob('*.jsonl')):
 if f.name.startswith(('initial-','retest-','final-')) or 'feedback' in f.name: continue
 if 'attempt' in f.name: out=f.with_name(f.name.replace('attempt','feedback'))
 elif f.stem.endswith('1'): out=f.with_name(f.stem[:-1]+'-feedback1.jsonl')
 elif f.stem.endswith('-hints'): out=f.with_name(f.stem+'-feedback.jsonl')
 else: continue
 a,b=read(f),read(out)
 if len(a)!=len(b): errors.append([f.name,'length',len(a),len(b)])
 for i,(x,y) in enumerate(zip(a,b),1):
  id=x.get('question') or x.get('lesson','')+'/'+x.get('task','')
  if id!=y['id']: errors.append([f.name,i,'id',id,y['id']])
  z={'id':id,**x,**y}; ref={'input':f.name,'feedback':out.name,'line':i,'id':id}
  if isinstance(y.get('passed'),bool): merged.append(z);pairs.append(ref)
  else: nonbool.append({**ref,**y})
initial=read(S/'initial-attempts.jsonl'); retest=read(S/'retest-attempts.jsonl')
a=collections.Counter(map(sig,merged));b=collections.Counter(map(sig,initial))
retest_merged=[];retest_pairs=[];retest_errors=[]
for name in ('retest-attempt1','final-attempt1','final-attempt2','final-attempt3'):
 f=S/(name+'.jsonl');out=f.with_name(f.name.replace('attempt','feedback'))
 inputs,outputs=read(f),read(out)
 if len(inputs)!=len(outputs): retest_errors.append([name,'length',len(inputs),len(outputs)])
 for i,(x,y) in enumerate(zip(inputs,outputs),1):
  id=x.get('question') or x.get('lesson','')+'/'+x.get('task','')
  if id!=y['id']: retest_errors.append([name,i,'id',id,y['id']])
  retest_merged.append({'id':id,**x,**y})
  retest_pairs.append({'input':f.name,'feedback':out.name,'line':i,'id':id})
ra=collections.Counter(map(sig,retest_merged));rb=collections.Counter(map(sig,retest))
export=json.loads((D/'technical/chapter-export.json').read_text()); release=json.loads((D/'technical/release.json').read_text())
inv={}
for p in sorted((ROOT/'content/ch07').glob('*.md')):
 for id in re.findall(r'^## task: ([\w-]+)\s*\|',p.read_text(),re.M): inv[p.stem+'/'+id]='task'
 for k in ('predict','quiz'):
  for i,_ in enumerate(re.finditer(r'^::: '+k+r'\b',p.read_text(),re.M),1): inv[p.stem+'/'+k+'/'+str(i)]='final_quiz' if p.stem=='test' else k
exids={r['lesson'].removeprefix('ch07/')+'/'+r['id'] for r in export if r['kind']=='task'}
# Predict export IDs need numbering because export IDs use a different namespace.
expredict=collections.Counter(r['lesson'].removeprefix('ch07/') for r in export if r['kind']=='predict')
rawpredict=collections.Counter(k.split('/')[0] for k,v in inv.items() if v=='predict')
source_mismatch=[p for p,v in release['files'].items() if not (ROOT/p).exists() or h(ROOT/p)!=v]
data_mismatch=[p for p,v in release['data'].items() if h(ROOT/'site/data'/p)!=v]
full_candidates={str(p):h(p) for p in Path('/tmp/kuch07round').glob('*.json') if h(p)==release['full_course_export_sha256']}
course=(ROOT/'content/course.yaml').read_text().split('  - id: ch07\n',1)[1].split('  - id: ch08\n',1)[0]
lessons=re.findall(r'- \{id: ([\w-]+),',course)
ledger=[]
for prefix,name,count in [('S07','student',2),('E7','expert',6),('M07','methodist',6)]:
 p=ROOT/f'docs/audit-2026-11-13/ch07/{name}.md'; lines=p.read_text().splitlines()
 for i in range(1,count+1):
  id=f'{prefix}-{i:02}'; refs=[n for n,l in enumerate(lines,1) if id in l]
  ledger.append({'id':id,'source':str(p.relative_to(ROOT)),'lines':refs,'current_expert_lines':[n for n,l in enumerate((D/'expert.md').read_text().splitlines(),1) if '| '+id+' |' in l]})
p=ROOT/'docs/course-improvements/reaudit/fixes/review/ch07.md'
for id,line in [('T05',3),('T06',3),('M07-budget-2026-11-15',5)]: ledger.append({'id':id,'source':str(p.relative_to(ROOT)),'lines':[line]})
def stat(rows):
 latest={r['id']:r['passed'] for r in rows}
 return {'rows':len(rows),'true':sum(r['passed'] is True for r in rows),'false':sum(r['passed'] is False for r in rows),'unique':len(latest),'latest_true':sum(v is True for v in latest.values()),'latest_failed':[k for k,v in latest.items() if v is not True]}
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'final mechanical reconciliation; peer decisions in fixes/review.md','inventory':dict(collections.Counter(inv.values())),'lessons_course_yaml':lessons,'context_units':{'lessons':len(lessons),'intro':1,'final_test':1,'note':'14 lesson contexts if intro is included; final test is a separate 15th page'},'export':{'rows':len(export),'kinds':dict(collections.Counter(r['kind'] for r in export)),'task_missing':sorted({k for k,v in inv.items() if v=='task'}-exids),'task_unknown':sorted(exids-set(inv)),'predict_counts_equal':expredict==rawpredict,'quiz_absent_from_export':30},'initial':stat(initial),'retest':stat(retest),'raw':{'boolean_rows':len(merged),'pair_errors':errors,'not_in_initial':list((a-b).elements()),'not_in_raw':list((b-a).elements()),'nonboolean':nonbool,'missing_visible_output_bool':sum('visible_output' not in r for r in merged),'row_provenance':pairs},'retest_raw':{'rows':len(retest_merged),'pair_errors':retest_errors,'not_in_retest':list((ra-rb).elements()),'not_in_raw':list((rb-ra).elements()),'row_provenance':retest_pairs},'release':{'snapshot_hash':h(D/'technical/chapter-export.json'),'snapshot_matches':h(D/'technical/chapter-export.json')==release['chapter_snapshot_sha256'],'source_mismatch':source_mismatch,'data_mismatch':data_mismatch,'full_course_hash_matches':full_candidates},'historical_ledger':ledger}
(D/'technical/coordination.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('raw','historical_ledger')},ensure_ascii=False,indent=2)); print('RAW',len(merged),'errors',errors,'not_initial',len(list((a-b).elements())),'not_raw',len(list((b-a).elements())),'nonbool',len(nonbool),'missing_output',result['raw']['missing_visible_output_bool']); print('LEDGER',ledger)
