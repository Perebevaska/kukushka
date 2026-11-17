"""Independent clean-kernel replay of the frozen 95-file revision and semantic checks."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import nbformat
from nbclient import NotebookClient

here=Path(__file__).resolve().parent
chapter=here.parent.parent
stage=chapter/'fixes/student/retest'
source=stage/'own-project'
manifest=stage/'project-revision-freeze.json'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(manifest)=='b406b853a46185258d6f0236d12f4a6acc39d6f94cad18da382a87309942b114'
entries=json.loads(manifest.read_text())['files']
assert len(entries)==95
assert all(digest(source/e['path'])==e['sha256'] for e in entries)
results={"manifest_sha256":digest(manifest),"inputs_verified":len(entries),"runtime":sys.version,"discarded_outputs_from_submission":True,"copied_first_release_for_replay":True}
with tempfile.TemporaryDirectory(prefix='ch15-revised-review-') as tmp:
    scratch=Path(tmp)
    work=scratch/'submission'
    for e in entries:
        name=e['path']
        if name.startswith('reports/revision/') or name=='reports/industry-ablation.json':continue
        origin=source/name
        path=work/name
        path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(origin,path)
    held=['models/office_churn/1.0/model.joblib','models/office_churn/1.0/golden.csv','reports/call_list_2026-09-30.csv','selection-before-test.json']
    frozen={n:digest(work/n) for n in held}
    nb=nbformat.read(work/'final_project.ipynb',as_version=4)
    for c in nb.cells:
        if c.cell_type=='code':c.outputs=[];c.execution_count=None
    ker=scratch/'jupyter/kernels/audit'
    ker.mkdir(parents=True)
    (ker/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Pinned revision review','language':'python'}))
    os.environ.update({k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']})
    os.environ.update(JUPYTER_PATH=str(scratch/'jupyter'),JUPYTER_RUNTIME_DIR=str(scratch/'runtime'),MPLCONFIGDIR=str(scratch/'mpl'),IPYTHONDIR=str(scratch/'ipy'),PYTHONDONTWRITEBYTECODE='1')
    try:
        NotebookClient(nb,kernel_name='audit',timeout=240,resources={'metadata':{'path':str(work)}}).execute()
        results['cells']=[{'cell':i,'type':c.cell_type,'execution':c.get('execution_count'),'output_types':[o.output_type for o in c.get('outputs',[])]} for i,c in enumerate(nb.cells,1)]
        out=work/'reports/revision'
        fresh={p.relative_to(work).as_posix():digest(p) for p in out.rglob('*') if p.is_file()}
        results['fresh_revision_matches']={n:(digest(source/n)==h) for n,h in fresh.items() if (source/n).is_file()}
        for name in ['industry-ablation','trend-transfer','ticket-availability-summary','future-event-check']:
            results[name]=json.loads((out/(name+'.json')).read_text())
        read=lambda name:list(csv.DictReader((out/(name+'.csv')).open()))
        singles=read('single-feature-folds')
        results['single_feature']={'rows':len(singles),'features':len({r['feature'] for r in singles}),'strongest':read('single-feature-summary')[0]}
        assert len(singles)==80 and all(len({int(x['fold']) for x in singles if x['feature']==key})==5 for key in {r['feature'] for r in singles})
        results['sensitivity']=read('ticket-count-comparison')
        results['frozen_first_release_hashes_match']={n:digest(work/n)==h for n,h in frozen.items()}
        assert all(results['frozen_first_release_hashes_match'].values())
        r=subprocess.run([sys.executable,'score.py','--cutoff','2026-09-30','--call-limit','3','--out-dir','reports/revision/rescore'],cwd=work,check=True,capture_output=True,text=True)
        results['CLI3']=json.loads(r.stdout)
        calls=out/'rescore/call_list_2026-09-30_limit3.csv'
        results['CLI3']['rows']=list(csv.DictReader(calls.open()))
        results['CLI3']['matches']=digest(calls)==digest(source/'reports/revision/rescore'/calls.name)
    except BaseException as e:
        results['failure']=str(e);raise
    finally:
        results['source_unchanged']=all(digest(source/e['path'])==e['sha256'] for e in entries)
        (here/'project-revision-run.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
