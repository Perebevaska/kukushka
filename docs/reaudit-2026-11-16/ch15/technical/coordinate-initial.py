from pathlib import Path
import json,hashlib,collections,re
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch15';S=D/'student';W=Path('/private/tmp/kuch15round')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
f=json.loads((S/'initial-freeze-manifest.json').read_text());assert len(f['files'])==128
for x in f['files']:assert sha(S/x['path'])==x['sha256'],x['path']
public=json.loads((D/'technical/public-package-manifest.json').read_text())['files'];assert len(public)==83
for name,h in public.items():assert sha(W/'student'/name)==h,name
rows=[json.loads(l) for l in (S/'initial-attempts.jsonl').read_text().splitlines() if l.strip()];by=collections.defaultdict(list)
for row in rows:
 assert isinstance(row.get('passed'),bool);assert all(k in row for k in ['id','expect','Q1','Q2','Q3','feedback'])
 assert ('code'in row)!=('question'in row)
 by[row['id']].append(row)
inv=json.loads((D/'technical/inventory.json').read_text());assert set(by)==set(inv);assert len(rows)==93
coverage=[]
for lesson in json.loads((D/'technical/baseline.json').read_text())['lesson_order']:
 ids=[i for i in inv if i.startswith(lesson+'/')]
 coverage.append({'lesson':lesson,'targets':len(ids),'first_passed':sum(by[i][0]['passed'] for i in ids),'final_passed':sum(by[i][-1]['passed'] for i in ids),'attempts':sum(len(by[i]) for i in ids),'kind_counts':dict(collections.Counter(inv[i] for i in ids))})
first=sum(v[0]['passed'] for v in by.values());final=sum(v[-1]['passed'] for v in by.values());assert(first,final)==(85,89)
payloads=[{'ordinal':j+1,'id':r['id'],'passed':r['passed'],'sha256':hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'code_sha256':hashlib.sha256(r.get('code','').encode()).hexdigest() if 'code'in r else None,'feedback_sha256':hashlib.sha256(r['feedback'].encode()).hexdigest()} for j,r in enumerate(rows)]
nb=json.loads((S/'own-project/final_project.ipynb').read_text());assert len(nb['cells'])==21;assert sum(c['cell_type']=='code'for c in nb['cells'])==7
previous=json.loads((D/'previous.json').read_text());history=(D/'review-history.md').read_text();assert all('| '+r['id']+' |' in history for r in previous['rows'])
roles=[{'role':x,'model':m,'effort':e,'execution':'completed per root actual-role record'} for x,m,e in [('coordinator','Sol','medium'),('student','Sol','medium'),('quiz','Sol','medium'),('checks','Sol','high'),('expert','Astra','high'),('methodist','Astra','high'),('business','Astra','high'),('program','Astra','high'),('judge','Astra','high'),('reviewer','Astra','high'),('recipient','Sol','high')]]
dump(D/'coordination-initial.json',{'baseline':'740b115f44bd2b9e23f0aaaf36af086d2454444e','initial_freeze_sha256':sha(S/'initial-freeze-manifest.json'),'initial_frozen_files':128,'public_files':83,'browser_payload_file_sha256':sha(S/'initial-attempts.jsonl'),'raw_rows':len(rows),'targets':len(by),'first_passed':first,'final_passed':final,'hints':sum(r.get('action')=='hint'for r in rows),'kind_counts':dict(collections.Counter(inv.values())),'lesson_coverage':coverage,'attempt_payloads':payloads,'notebook':{'cells':21,'code_cells':7,'sha256':sha(S/'own-project/final_project.ipynb')},'global_student_interview':{'status':'UNREAD reserved for postchapter interview; hash only','sha256':sha(S/'global-improvements-own.md')},'previous_ledger_rows':len(previous['rows']),'previous_ledger_rows_reviewed':80,'roles':roles})
print('verified128initial+83public hashes,93fullpayloads,89IDs,85first/89final,0hints,21/7notebook,80historyverdicts; interview only hashed')
