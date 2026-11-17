from pathlib import Path
import json,hashlib,collections,re
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch15';W=Path('/private/tmp/kuch15round');S=D/'fixes/student/retest'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
proof={}
for label,path,base,count in [('initial128',D/'student/initial-freeze-manifest.json',D/'student',128),('revised95',S/'project-revision-freeze.json',S/'own-project',95),('browser33',S/'browser-retake-freeze.json',S,33)]:
 x=json.loads(path.read_text());assert len(x['files'])==count,(label,len(x['files']))
 for f in x['files']:assert sha(base/f['path'])==f['sha256'],(label,f['path'])
 proof[label]={'count':count,'manifest_sha256':sha(path),'all_hashes_verified':True}
for label,path,base,count in [('original83',D/'technical/public-package-manifest.json',W/'student',83),('public208',D/'technical/retest-package/public-package-manifest.json',W/'student-retest',208),('project_input139',D/'technical/retest-package/project-revision-input.json',W/'student-project-revision',139),('delta2',D/'technical/release-v3/public-delta-manifest.json',W/'student-retest-v3-delta',2)]:
 x=json.loads(path.read_text());assert len(x['files'])==count
 for n,h in x['files'].items():assert sha(base/n)==h,(label,n)
 proof[label]={'count':count,'manifest_sha256':sha(path),'all_hashes_verified':True}
rows=[json.loads(l)for l in(S/'attempts.jsonl').read_text().splitlines()if l.strip()];target=json.loads((W/'student-retest/targets.json').read_text());expected=set(target['tasks'])|set(target['questions']);by=collections.defaultdict(list)
for row in rows:
 assert isinstance(row.get('passed'),bool);assert all(k in row for k in ['id','Q1','Q2','Q3','expect','feedback']);assert ('code'in row)!=('question'in row);by[row['id']].append(row)
assert set(by)==expected and len(rows)==48 and len(by)==47
assert sum(v[0]['passed']for v in by.values())==46 and all(v[-1]['passed']for v in by.values());assert not any(r.get('action')=='hint'for r in rows)
assert [i for i,v in by.items()if not v[0]['passed']]==['03-experiments/log-csv']
assert all(by[i][0]['passed']for i in expected if i.startswith('test/'))
coverage={'baseline':json.loads((D/'coordination-initial.json').read_text()),'retake':{'unique_targets':47,'tasks':28,'embedded_quiz':2,'full_test':17,'graded_payloads':48,'first_passed':46,'final_passed':47,'hints':0,'failed_first':['03-experiments/log-csv'],'core_UI':{'core':'5/5','extra':'12/12','full':'17/17'},'payload_file_sha256':sha(S/'attempts.jsonl'),'targets':[]},'immutable_manifests':proof}
for ident in sorted(expected):coverage['retake']['targets'].append({'id':ident,'attempts':len(by[ident]),'first_passed':by[ident][0]['passed'],'final_passed':by[ident][-1]['passed'],'full_payload_sha256':[hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()for r in by[ident]]})
# Keep payload metadata, omit duplicated huge initial93 payload list from coverage summary.
coverage['baseline'].pop('attempt_payloads',None);dump(D/'coverage.json',coverage)
release=D/'technical/release-v4';release.mkdir(exist_ok=True);paths=list((R/'content/ch15').glob('*.md'))+list((R/'site/ch15').glob('*.html'))+list((R/'site/assets').glob('*'))+[R/'content/course.yaml',R/'site/notebooks/ch15-practice.ipynb',R/'site/notebooks/project-template.ipynb',R/'site/notebooks/dsc.py',R/'site/notebooks/check_notebook.py']+[R/'site/data'/f for f in ['guests_churn.csv','office.db','service_log.jsonl']];paths += [R/'content/figures'/(f['figure']+'.svg') for f in json.loads((W/'figures-retest.json').read_text())];paths=sorted(set(p for p in paths if p.is_file()));assert sha(W/'final-v4.json')=='38165f990972354091d6cdef11bf093451a45bbd9cf05258f06fbd7cd25c574c'
dump(release/'release-manifest.json',{'export_sha256':sha(W/'final-v4.json'),'hashes':{str(p.relative_to(R)):sha(p)for p in paths},'scope':'APPENDIX only; v3student47 and all sealed prior inputs remain unchanged','diagnostic_only_binding':'../../fixes/technical/root/final-v4-diagnostic-proof.json','wide_rerun_on_v4':False,'student47_rerun_on_v4':False,'immutable_manifests':proof})
print('verified83/128/208/139/delta2/95/33immutable;full48payload47targets46first47final0hint;v4appendixsnapshot done')
