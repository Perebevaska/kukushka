import subprocess,sys,time,json,urllib.request,urllib.error
from pathlib import Path
p=subprocess.Popen([sys.executable,'-m','uvicorn','service:app','--host','127.0.0.1','--port','55586'],stdout=open('api-server.log','w'),stderr=subprocess.STDOUT)
try:
 for _ in range(100):
  try:
   r=urllib.request.urlopen('http://127.0.0.1:55586/docs');print('DOCS',r.status,len(r.read()));break
  except urllib.error.URLError:time.sleep(.1)
 good={'city':'Пермь','fav_category':'кофе','tenure_months':12,'app':0,'visits_90d':4,'days_since_last':8,'avg_check':446,'delivery_share':.04,'promo_used':1,'complaints':0}
 for name,payload in [('good',good),('bool',dict(good,app=True)),('string',dict(good,tenure_months='12')),('kopecks',dict(good,avg_check=44600)),('newcity',dict(good,city='Москва')),('null',dict(good,avg_check=None))]:
  req=urllib.request.Request('http://127.0.0.1:55586/predict',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  try:r=urllib.request.urlopen(req)
  except urllib.error.HTTPError as e:r=e
  print(name,r.status,r.read().decode())
finally:
 p.terminate();p.wait(timeout=10);print('SERVER STOPPED',p.returncode)
