"""Run the text's real artifact, service and tracking snippets in a fresh temp directory."""
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from importlib.metadata import version
from pathlib import Path

root = Path(__file__).resolve().parents[5]
http_only = len(sys.argv) == 3 and sys.argv[1] == '--http-only'
os.chdir(sys.argv[2] if http_only else tempfile.mkdtemp(prefix='expert15-live-'))
for name in ('guests_churn.csv',):
    shutil.copy(root/'site/data'/name,name)
for name in ['scikit-learn','pandas','fastapi','uvicorn','pydantic','mlflow','skops','httpx']:
    print(name,version(name))
print('cwd',Path.cwd(),'python',sys.version,flush=True)
def blocks(lesson):
    return re.findall(r'^\x60{3}python(?: static)?\n(.*?)^\x60{3}$',(root/'content/ch15'/lesson).read_text(),re.M|re.S)
def take(lesson,snippet):
    return next(b for b in blocks(lesson) if snippet in b)
def run(code,ns):
    exec(compile(code,'<published lesson>','exec'),ns)
if not http_only:
    art = {}
    run(take('01-artifact.md','os.makedirs("models/churn/1.0"'),art)
    run(take('01-artifact.md','"trained_at": date.today()'),art)
    shutil.copy('card.json','models/churn/1.0/card.json')
    Path('service.py').write_text(take('02b-service-run.md','class Guest(BaseModel):'))
sys.path.insert(0,str(Path.cwd()))
from service import app
from fastapi.testclient import TestClient
from httpx import Client
good=dict(city="Пермь", fav_category="кофе", tenure_months=12, app=0, visits_90d=4,days_since_last=8, avg_check=446, delivery_share=.04,promo_used=1, complaints=0)
def requests(c):
    for tag,changes,expected in [('valid',{},200),('zero',{'visits_90d':0},200),('null check',{'avg_check':None},200),('negative',{'visits_90d':-1},422),('bool',{'visits_90d':True},422),('bad city',{'city':'Томск'},422),('two',{'visits_90d':-1,'delivery_share':3},422),('missing',{},422)]:
        payload = {**good,**changes}
        if tag=='missing': del payload['avg_check']
        response=c.post('/predict',json=payload)
        print(tag,response.status_code,response.json(),flush=True)
        assert response.status_code==expected
        if tag=='two': assert {item['loc'][-1] for item in response.json()['detail']}==set(changes)
print('in-process ASGI')
with TestClient(app) as c:
    requests(c)
def tcp():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','service:app','--host','127.0.0.1','--port',str(port)])
    try:
        with Client(base_url=f'http://127.0.0.1:{port}',trust_env=False) as c:
            for i in range(100):
                try:
                    if c.get('/docs').status_code==200:break
                except OSError:pass
                except Exception as err:
                    if type(err).__name__!='ConnectError':raise
                time.sleep(.1)
            requests(c)
    finally:
        proc.terminate()
        proc.wait(timeout=15)
print('local HTTP',flush=True)
try: tcp()
except PermissionError as e: print('TCP sandbox blocked',repr(e))
if http_only: sys.exit(0)
ns = {}
os.environ['MLFLOW_TRACKING_URI']='sqlite:///'+str(Path('mlflow.db').absolute())
os.environ['MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING']='false'
os.environ['MLFLOW_DISABLE_TELEMETRY']='true'
print('real MLflow CV, selected run and alias',flush=True)
run(take('03-experiments.md','def log_run(name, estimator, note='),ns)
run(take('03-experiments.md','skops_trusted_types='),ns)
run(take('03-experiments.md','set_registered_model_alias'),ns)
import numpy as np
print(ns['runs'][['run_id','metrics.cv_auc_mean']].to_string(index=False))
print('golden rows',len(ns['rows']),'max abs',np.abs(ns['loaded'].predict_proba(ns['rows'])-ns['expected']).max(),'registry version',ns['version'].version)
