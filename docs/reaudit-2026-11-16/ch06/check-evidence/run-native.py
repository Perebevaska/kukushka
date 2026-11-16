import json,sys,os,tempfile,shutil,hashlib,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import harness,numpy,pandas,sklearn
phase=sys.argv[1] if len(sys.argv)>1 else 'original'
tasks={t['lesson'].split('/')[-1]+'/'+t['id']:t for t in json.loads((HERE/f'tasks-{phase}.json').read_text())}
probes=json.loads((HERE/f'probes-{phase}.json').read_text())
with tempfile.TemporaryDirectory() as temp:
 os.chdir(temp)
 for filename in set(f for t in tasks.values() for f in t.get('files',[])):shutil.copy((HERE/'data-baseline'/filename if (HERE/'data-baseline'/filename).exists() else ROOT/'site/data'/filename),filename)
 result_path=HERE/f'native-{phase}.jsonl'
 rerun=1
 while result_path.exists():
  result_path=HERE/f'native-{phase}-rerun{rerun}.jsonl';rerun+=1
 with result_path.open('w') as output:
  output.write(json.dumps(dict(kind='environment',python=sys.version,numpy=numpy.__version__,pandas=pandas.__version__,sklearn=sklearn.__version__))+'\n')
  for p in probes:
   t=tasks[p['key']]
   for filename in t.get('files',[]): shutil.copy(HERE/p.get('file_variants',{}).get(filename,'') if filename in p.get('file_variants',{}) else (HERE/'data-baseline'/filename if (HERE/'data-baseline'/filename).exists() else ROOT/'site/data'/filename),filename)
   setup=(t.get('setup') or '')+'\n'+p.get('setup_append','')
   r=harness.run(p['code'],t['check'],setup,False)
   record={**p,'result':r,'observed':bool(r.get('check',{}).get('passed'))}
   if p.get('diagnostic'):
    d=harness.run(p['code']+'\nimport json as _auditjson\nprint(_auditjson.dumps('+p['diagnostic']+'))',None,setup,False)
    record['diagnostic_result']=d
   output.write(json.dumps(record,ensure_ascii=False)+'\n');output.flush()
   print(p['id'],p['key'],p['expected'],record['observed'],r.get('check',{}).get('msg') or (r.get('error') or {}).get('text',''),flush=True)
