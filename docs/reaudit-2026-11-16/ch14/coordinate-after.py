"""Read/hash complete after evidence; excludes any partial student retake."""
from pathlib import Path
import json,hashlib,collections,re
D=Path(__file__).resolve().parent;R=D.parents[2];C=D/'technical/checks';EXPORT='bdce6f6b7ce042789cf94ffbe6a07b49a14845f41da0c6ad7f7460e2bfe8417d'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
o={'scope':'published after technical evidence only; no partial student retake counted','stages':{}}
for name,folder in [('main206',C),('keyed6',C/'key-supplement'),('extra27',C/'acceptance-extra')]:
 pp=rows(folder/'programs.jsonl');stage={}
 for rt in ['native','pyodide']:
  rr=rows(folder/('after-'+rt+'.jsonl'));assert len(pp)==len(rr)
  meta=read(folder/('after-'+rt+'-meta.json'));assert meta.get('tasks_sha256',meta.get('task_sha256'))==EXPORT;assert meta['programs_sha256']==sha(folder/'programs.jsonl')
  for p,r in zip(pp,rr):assert all(r[k]==v for k,v in p.items());assert hashlib.sha256(p['code'].encode()).hexdigest()==p['code_sha256']
  mismatch=[{'index':i,'label':r['label'],'expected':r['expected'],'passed':r['passed']} for i,r in enumerate(rr) if r['expected']!=r['passed']]
  if name=='main206':assert [r['index'] for r in mismatch]==[5,196]
  else:assert not mismatch
  stage[rt]={'programs':len(pp),'expectations_match':len(pp)-len(mismatch),'mismatches':mismatch,'result_sha256':sha(folder/('after-'+rt+'.jsonl')),'meta_sha256':sha(folder/('after-'+rt+'-meta.json')),'raw_error_entries':[{'index':i,'label':r['label'],'expected':r['expected'],'passed':r['passed'],'error':r['raw'].get('error')} for i,r in enumerate(rr) if not r['raw'].get('ok')]}
 o['stages'][name]=stage
short={}
for rt in ['native','pyodide']:
 rr=rows(C/('after-short/after-'+rt+'.jsonl'));assert len(rr)==10 and all(r['passed'] for r in rr);short[rt]={'assertions':10,'matching':10,'sha256':sha(C/('after-short/after-'+rt+'.jsonl'))}
o['short']=short
pp=rows(D/'technical/reviewer/programs.jsonl');reviewer={}
for rt in ['native','pyodide']:
 rr=read(D/('technical/reviewer/after-'+rt+'.json'));assert rr['task_sha256']==EXPORT;assert rr['programs_sha256']==sha(D/'technical/reviewer/programs.jsonl');assert len(rr['entries'])==len(pp)==24
 for p,r in zip(pp,rr['entries']):assert p['name']==r['name'] and p['expected']==r['expected']==r['passed'];assert r['code_sha256']==hashlib.sha256(p['code'].encode()).hexdigest();assert r['ok']
 reviewer[rt]={'programs':24,'valid_accepted':sum(r['expected'] for r in rr['entries']),'wrong_rejected':sum(not r['expected'] for r in rr['entries']),'FA':0,'FR':0,'runtime_errors':0,'sha256':sha(D/('technical/reviewer/after-'+rt+'.json'))}
o['reviewer']=reviewer
o['root_standard']={'text':(D/'technical/after-standard.log').read_text().strip(),'sha256':sha(D/'technical/after-standard.log')};assert '98, проблем: 0' in o['root_standard']['text']
o['root_notebooks']={}
for mode in ['solution','starter']:
 p=D/('technical/notebook-'+mode+'.log');s=p.read_text();assert 'задач 57, проблем 0' in s;o['root_notebooks'][mode]={'text':s.strip(),'sha256':sha(p)}
ui=read(D/'technical/test-ui.json');assert [(r['correct'],r['passed']) for r in ui]==[(11,False),(12,True)] and all(r['reload_identical'] for r in ui);o['test_UI']={'threshold_cases':ui,'sha256':sha(D/'technical/test-ui.json')}
q=read(D/'fixes/test-validation.json');assert len(q['questions'])==15 and all(r['n_options']==r['n_explanations']==4 and r['stem_equal'] and r['all_options_equal'] and r['all_explanations_equal'] for r in q['questions']);o['test_content']={'questions':15,'options':60,'all_published_equal_source':True,'sha256':sha(D/'fixes/test-validation.json')}
o['release_verification']=read(D/'technical/verify-release.json');o['retake_status']='issued38, active; no incomplete counts or assessment claimed';o['assessment']='methodist provisional published4.4=4/5/4/4/5, pending retake final review'
(D/'coordination-after.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print('All complete after payload/code SHA/meta validated:239full programs +10short per runtime,24reviewer per runtime,root98,NB57+57,quiz15/60,UI11/12; retake excluded')
