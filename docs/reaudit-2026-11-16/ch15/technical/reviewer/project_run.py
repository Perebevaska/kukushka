"""Clear every saved output, rebuild only from the student's sources and pinned input."""
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

here=Path(__file__).resolve().parent
project=here.parent.parent/"student/own-project"
phase=sys.argv[1] if len(sys.argv)>1 else "before"
if len(sys.argv)>2:project=Path(sys.argv[2]).resolve()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def shape(nb):
    return [{"number":i,"type":c.cell_type,"heading":next(iter(c.source.splitlines()),"")[:100],
             "execution_count":c.get("execution_count"),"outputs":[o.output_type for o in c.get("outputs",[])]} for i,c in enumerate(nb.cells,1)]
with tempfile.TemporaryDirectory(prefix="ch15-independent-project-") as td:
    work=Path(td)/"submission";work.mkdir()
    for name in ["final_project.ipynb","README.md","requirements.txt","score.py"]:shutil.copy2(project/name,work/name)
    shutil.copytree(project/'src',work/'src',ignore=shutil.ignore_patterns('__pycache__'))
    (work/'data').mkdir()
    db=project/'data/office.db'
    if not db.is_file():db=here.parent/'data-baseline/office.db'
    shutil.copyfile(db,work/'data/office.db')
    nb=nbformat.read(work/'final_project.ipynb',as_version=4)
    results={"input_sha":sha(project/'final_project.ipynb'),"db_sha":sha(db),"python":sys.version,"initial":shape(nb),"reports_and_models_at_start":[]}
    for c in nb.cells:
        if c.cell_type=="code":c.outputs=[];c.execution_count=None
    temp=Path(td)/"jupyter";kernels=temp/'kernels';ks=kernels/'audit';ks.mkdir(parents=True)
    (ks/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Pinned project runtime','language':'python'}))
    os.environ.update(JUPYTER_PATH=str(temp),JUPYTER_RUNTIME_DIR=str(Path(td)/"runtime"),MPLCONFIGDIR=str(Path(td)/'mpl'),IPYTHONDIR=str(Path(td)/'ipython'),OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",VECLIB_MAXIMUM_THREADS="1")
    try:
        NotebookClient(nb,kernel_name='audit',timeout=240,resources={'metadata':{'path':str(work)}}).execute()
        results["restarted"]=shape(nb)
        results["checks"]={}
        for name in ["reports/test-metrics.json","selection-before-test.json","reports/call_list_2026-09-30.csv","reports/sensitivity.csv","models/office_churn/1.0/golden.csv","reports/industry-ablation.json","reports/hypothesis.json"]:
            fresh=work/name
            results["checks"][name]={"regenerated":fresh.exists(),"matches_published_bytes":sha(fresh)==sha(project/name) if fresh.exists() and (project/name).exists() else None}
        for limit in [3,150]:
            run=subprocess.run([sys.executable,"score.py","--cutoff","2026-09-30","--call-limit",str(limit)],cwd=work,check=True,capture_output=True,text=True)
            results[f"CLI_{limit}"]=json.loads(run.stdout)
            out=work/f'reports/rescore/call_list_2026-09-30_limit{limit}.csv'
            results[f"CLI_{limit}"]["top_rows"]=out.read_text().splitlines()[:4]
            if limit==150:results["CLI_150"]["byte_matches_release"]=out.read_bytes()==(project/"reports/call_list_2026-09-30.csv").read_bytes()
        results["additional"]=subprocess.run([sys.executable,'-c',"""
from src.features import read_tables,build_features,active_at
import pandas as pd
t=read_tables('data/office.db')
cid=active_at(t,'2026-09-30').index[0]
t['orders']=t['orders'].iloc[:1].assign(client_id=cid,order_date='2026-09-29',status='возврат',amount=-1.)
print('revenue_trend[-1,0]',build_features(t,'2026-09-30').loc[cid,'revenue_trend'])
"""],cwd=work,check=True,capture_output=True,text=True).stdout.strip()
    except BaseException as err:
        results['failure']=str(err)
        raise
    finally:
        (here/(phase+"-project-run.json")).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
