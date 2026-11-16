"""Execute published notebook solutions with the same dsc.run_task used by %%task."""
import contextlib,io,json,sys,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parents[4]
sys.path.insert(0,str(root/'site/notebooks'))
import dsc
import matplotlib.pyplot as plt
from probes import cases
def main(site,output):
    dsc.TASKS_DIR=site/'notebooks/tasks'
    dsc.DATA=here.parents[1]/'technical/data-baseline'
    catalog=json.loads((dsc.TASKS_DIR/'ch08.json').read_text())['tasks']
    tasks={t['id']:t for t in catalog.values()}
    paths={t['id']:path for path,t in catalog.items()}
    with tempfile.TemporaryDirectory() as tmp,output.open('w') as out:
        dsc.WORK=Path(tmp)
        for name,key,expected,code in cases(tasks):
            # Each exercise is submitted fresh, like a fresh notebook.
            plt.close('all')
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                r=dsc.run_task(paths[key],code,{'__name__':'__main__'})
            record=dict(id=name,expected=expected,observed=r['passed'],msg=r['msg'],stdout=stdout.getvalue()[-350:])
            print(json.dumps(record,ensure_ascii=False),file=out,flush=True)
            print(name,expected,record['observed'],flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
