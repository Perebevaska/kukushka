"""Run only the frozen final narrow set, never the previous 63 programs."""
import json,os,shutil,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'site/assets'));import harness
phase=sys.argv[1];assert phase in ('before','after')
tasks={t['lesson']+'/'+t['id']:t for t in json.loads((HERE/f'refine-{phase}-tasks.json').read_text())}
rows=[json.loads(s) for s in (HERE/'refine-programs.jsonl').read_text().splitlines()];out=[]
for row in rows:
    t=tasks[row['lesson']+'/'+row['task']];old=Path.cwd()
    with tempfile.TemporaryDirectory() as folder:
        try:
            os.chdir(folder)
            for name in t['files']:shutil.copy(HERE.parent/'technical/data-baseline'/name,name)
            r=harness.run(row['code'],t['check'],t.get('setup'),False)
        finally:os.chdir(old)
    record=dict(row,ok=r['ok'],passed=r['check']['passed'],message=r['check']['msg'],error=r['error'],stdout=r['out']);out.append(record)
    (HERE/f'refine-{phase}-native.jsonl').write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in out))
    print(json.dumps({k:record[k] for k in ['id','expected','ok','passed','message']},ensure_ascii=False),flush=True)
import numpy,pandas,sklearn,scipy
(HERE/f'refine-{phase}-native-environment.json').write_text(json.dumps(dict(python=sys.version,numpy=numpy.__version__,pandas=pandas.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),indent=2))
print('Narrow set',len(out),'completed; normative matches',sum(r['ok'] and r['expected']==r['passed'] for r in out))
