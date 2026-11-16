"""Run delivered notebooks in an empty project directory, using the README command.

Inputs: delivered project folder, public data folder, receipt path. No precomputed
artifact is copied into the working directory, so stale results cannot hide errors.
"""
from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,sys,tempfile
folder,data,out=map(lambda s:Path(s).resolve(),sys.argv[1:])
here=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as scratch:
    work=Path(scratch)
    for p in folder.iterdir():
        if p.is_file() and p.suffix in ['.ipynb','.py','.txt','.md']:
            shutil.copy2(p,work/p.name)
    env={**os.environ,'COURSE_DATA':str(data),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
        'MPLBACKEND':'Agg','MPLCONFIGDIR':str(work/'mpl'),'IPYTHONDIR':str(work/'ipython'),
        'JUPYTER_RUNTIME_DIR':str(work/'runtime'),'PYTHONDONTWRITEBYTECODE':'1'}
    # Work with the installed, matching python3 kernelspec and the interpreter of this venv.
    cmd=[sys.executable,'execute_notebooks.py']
    r=subprocess.run(cmd,cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    states={}
    for p in sorted(work.glob('*artifacts/*')):
        delivered=folder/p.relative_to(work)
        states[str(p.relative_to(work))]=dict(regenerated_sha=digest(p),delivered_sha=digest(delivered) if delivered.is_file() else None)
    result=dict(command=['python','execute_notebooks.py'],exit_code=r.returncode,output=r.stdout[-3000:],outputs=states)
    if r.returncode==0:
        verified=work/'receipt.json'
        subprocess.run([sys.executable,str(here/'recipient.py'),str(work),str(data),str(verified)],check=True)
        result['checks']=json.loads(verified.read_text())
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(r.returncode,r.stdout[-600:],len(states),'regenerated')
    sys.exit(r.returncode)
