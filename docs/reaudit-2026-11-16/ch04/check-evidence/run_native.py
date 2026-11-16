"""Export and run explicit probes with shipped harness; never builds site."""
import json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'site/assets')]
import build,harness,pandas as pd
print(sys.version,'pandas',pd.__version__)
after='--after' in sys.argv
build.CH_DISPLAY['ch04']=True
lessons={('ch04',p.stem):build.parse_lesson(p) for p in (ROOT/'content/ch04').glob('*.md') if p.stem not in ('intro','test')}
if after: build.export(lessons,D/'tasks-after.json')
T={(x['lesson'].split('/')[-1],x['id']):x for x in json.loads((D/('tasks-after.json' if after else 'tasks-before.json')).read_text()) if x['kind']=='task'}
cases=json.loads((D/'probes-before.json').read_text())
if after:
 for x in cases: t=T[x['lesson'],x['task']]; x['check']=t['check'];x['setup']=t.get('setup')
 for l,t in sorted(T):
  x=T[l,t];cases.append(dict(lesson=l,task=t,case='current-author-solution',expected=True,code=x['solution'],check=x['check'],setup=x.get('setup'),files=x.get('files',[])))
results=[]
for x in cases:
 old=Path.cwd()
 with tempfile.TemporaryDirectory(prefix='ch04-probe-') as folder:
  try:
   os.chdir(folder)
   for f in x['files']: shutil.copy(ROOT/'site/data'/f,f)
   if x.get('prepare'): exec(x['prepare'],{})
   r=harness.run(x['code'],x['check'],x.get('setup'),False)
  finally: os.chdir(old)
 actual=bool(r.get('check',{}).get('passed'));match=actual==x['expected'];results.append(dict(x,result=r,actual=actual,match=match))
 print(('OK' if match else 'DEFECT'),x['lesson']+'/'+x['task'],x['case'],r.get('check',{}).get('msg',(r.get('error') or {}).get('text','')))
(D/('native-results-after.json' if after else 'native-results-before.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Final',sum(x['match'] for x in results),'of',len(results))
if after: assert all(x['match'] for x in results)
