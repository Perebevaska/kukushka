import sys,os,json,shutil,tempfile,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'site/assets')]
import harness
import numpy,pandas,scipy,statsmodels
base=Path(__file__).parent
export=Path(sys.argv[1]) if len(sys.argv)>1 else base/'original-course.json'
output=Path(sys.argv[2]) if len(sys.argv)>2 else base/'native-original.jsonl'
tasks={(x['lesson'],x['id']):x for x in json.loads(export.read_text()) if x['kind']=='task'}
meta=dict(runtime='CPython',python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,scipy=scipy.__version__,statsmodels=statsmodels.__version__)
with output.open('w') as out:
 out.write(json.dumps(meta)+'\n')
 for case in json.loads((Path(sys.argv[4]) if len(sys.argv)>4 else base/'cases.json').read_text()):
  if len(sys.argv)>3 and sys.argv[3] and case['name'] != sys.argv[3]: continue
  t=tasks[case['lesson'],case['id']]
  with tempfile.TemporaryDirectory() as d:
   for f in t.get('files',[]):shutil.copy(ROOT/'site/data'/f,Path(d)/f)
   prev=os.getcwd();os.chdir(d)
   try:r=harness.run(case['code'],t['check'],t.get('setup'),False)
   finally:os.chdir(prev)
  passed=bool(r.get('ok') and r.get('check',{}).get('passed'))
  record={**case,'actual':passed,'matches':passed==case['expected'],'result':r}
  out.write(json.dumps(record,ensure_ascii=False)+'\n');out.flush()
  print(case['lesson'],case['id'],case['name'],case['expected'],passed,flush=True)
