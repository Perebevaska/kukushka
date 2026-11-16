import argparse,json,os,sys,tempfile,shutil
from pathlib import Path
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parents[1]/'check-evidence'))
import harness
p=argparse.ArgumentParser()
p.add_argument('cases',type=Path)
p.add_argument('output',type=Path)
p.add_argument('names',nargs='*')
a=p.parse_args()
cases=json.loads(a.cases.read_text())
data=here.parents[1]/'technical/data-baseline'
with a.output.open('w') as out,tempfile.TemporaryDirectory() as tmp:
    os.chdir(tmp)
    for row in cases:
        if a.names and row['id'] not in a.names: continue
        for name in row['files']: shutil.copy(data/name,name)
        r=harness.run(row['code'],row['check'],row['setup'])
        obs=dict(id=row['id'],expected=row['expected'],observed=r['check']['passed'],check_sha256=row['check_sha256'],msg=r['check']['msg'],error=r['error'],stdout=r['out'][-400:])
        print(json.dumps(obs,ensure_ascii=False),file=out,flush=True)
        print(row['id'],row['expected'],obs['observed'],obs['msg'][:180],flush=True)
