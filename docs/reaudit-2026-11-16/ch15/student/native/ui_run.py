import subprocess,sys,time,urllib.request,urllib.error
from pathlib import Path
p=subprocess.Popen([sys.executable,'-m','mlflow','ui','--backend-store-uri','sqlite:///'+str(Path('mlflow.db').resolve()),'--host','127.0.0.1','--port','55587'],stdout=open('mlflow-ui-server.log','w'),stderr=subprocess.STDOUT)
try:
 for _ in range(150):
  try:
   with urllib.request.urlopen('http://127.0.0.1:55587/',timeout=2) as r:
    body=r.read();print('MLFLOW UI',r.status,'bytes',len(body),'HTML',b'<html' in body.lower());break
  except urllib.error.URLError:time.sleep(.1)
 else:raise RuntimeError('UI did not become ready')
finally:p.terminate();p.wait(timeout=10);print('UI STOPPED',p.returncode)
