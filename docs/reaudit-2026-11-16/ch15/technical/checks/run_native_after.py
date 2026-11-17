import os,sys,json,hashlib,shutil,tempfile,time,platform,importlib.metadata
from pathlib import Path
BASE=Path(__file__).resolve().parent; ROOT=BASE.parents[4]
phase=sys.argv[1] if len(sys.argv)>1 else 'before';taskfile=Path(sys.argv[2]) if len(sys.argv)>2 else BASE/'tasks.json'
sys.path.insert(0,str(BASE));import after_harness as harness
rows=[json.loads(l) for l in (BASE/'programs.jsonl').read_text().splitlines()];ts={(t['lesson'],t['id']):t for t in json.loads(taskfile.read_text())}
meta={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'libraries':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','matplotlib']},'tasks_sha256':hashlib.sha256(taskfile.read_bytes()).hexdigest(),'programs_sha256':hashlib.sha256((BASE/'programs.jsonl').read_bytes()).hexdigest(),'harness_sha256':hashlib.sha256((BASE/'after_harness.py').read_bytes()).hexdigest()}
(BASE/(phase+'-native-meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2));output=BASE/(phase+'-native.jsonl')
seen={}
if output.exists():seen={r['index']:r for r in map(json.loads,output.read_text().splitlines())}
for i,row in enumerate(rows):
 if i in seen:continue
 t=ts[row['lesson'],row['task']];start=time.time()
 with tempfile.TemporaryDirectory() as folder:
  for f in t['files']:shutil.copy2(BASE/'data'/f,Path(folder)/f)
  prev=os.getcwd();os.chdir(folder)
  try:result=harness.run(row['code'],row.get('check_override',t['check']),t['setup'],bool(t.get('display')))
  except BaseException as e:result={'transport_error':repr(e)}
  finally:os.chdir(prev)
 stage='transport' if 'transport_error' in result else ('submission_execution' if not result.get('ok') else ('check' if not result.get('check',{}).get('passed') else 'accepted'))
 record=dict(row,index=i,phase=phase,runtime='CPython',task_sha256=hashlib.sha256(json.dumps(t,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),duration_s=time.time()-start,stage=stage,passed=bool(result.get('check',{}).get('passed')),raw=result)
 with output.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
 print(i,row['task'],row['label'],record['passed'],row['expected'],stage,flush=True)
