"""Independent reviewer programs against current parsed sources, without rebuilding site."""
import json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'site/assets')]
import build,harness
task_file=sys.argv[2] if len(sys.argv)>2 else 'tasks-review.json'
if task_file=='tasks-review.json':
 build.CH_DISPLAY['ch04']=True
 lessons={('ch04',p.stem):build.parse_lesson(p) for p in (ROOT/'content/ch04').glob('*.md') if p.stem not in ('intro','test')}
 build.export(lessons,D/task_file)
tasks={(x['lesson'].split('/')[-1],x['id']):x for x in json.loads((D/task_file).read_text()) if x['kind']=='task'}
stem=sys.argv[1] if len(sys.argv)>1 else 'review'
cases=json.loads((D/(stem+'-programs.json')).read_text())
results=[]
for p in cases:
 task=tasks[p['lesson'],p['task']]
 old=Path.cwd()
 with tempfile.TemporaryDirectory(prefix='ch04-review-') as folder:
  try:
   os.chdir(folder)
   for f in task['files']:shutil.copy(ROOT/'site/data'/f,f)
   if p.get('prepare'):exec(p['prepare'],{})
   r=harness.run(p['code'],task['check'],task.get('setup'),False)
  finally:os.chdir(old)
 actual=bool(r.get('check',{}).get('passed'));results.append(dict(p,check=task['check'],setup=task.get('setup'),files=task['files'],task_snapshot=task_file,actual=actual,match=actual==p['expected'],result=r))
 print('OK' if actual==p['expected'] else 'DEFECT',p['lesson']+'/'+p['task'],p['case'],r.get('check',{}).get('msg',''),flush=True)
(D/(stem+('' if task_file=='tasks-review.json' else '-'+Path(task_file).stem)+'-native.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Final',sum(x['match'] for x in results),'of',len(results))
if not all(x['match'] for x in results):sys.exit(1)
