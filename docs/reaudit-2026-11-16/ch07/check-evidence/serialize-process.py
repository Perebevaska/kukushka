"""A file, read by a fresh CPython process; no browser or site build."""
import json,os,sys,tempfile,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
tasks=json.loads((HERE/'tasks-pipe-acceptance.json').read_text())
t=next(t for t in tasks if t['lesson'].endswith('/08-tuning') and t['id']=='save-load')
result={'expected':{'returncode':0,'same':True},'contract':'08-tuning/save-load: actual serialized Pipeline on raw rows in a fresh process'}
with tempfile.TemporaryDirectory() as tmp:
 os.chdir(tmp)
 shutil.copy(HERE.parent/'technical/data-baseline/guests_churn.csv','guests_churn.csv')
 ns={'__name__':'__main__'};exec(t['setup'],ns);exec(t['solution'],ns)
 new=ns['X_test'].iloc[:4].copy();new['city']='unknown';new['avg_check']=float('nan')
 new.to_json('input.json',orient='split');expected=ns['pipe'].predict_proba(new)[:,1].tolist()
 code='''import json,joblib,pandas as pd,numpy as np
model=joblib.load('churn_model.joblib')
new=pd.read_json('input.json',orient='split')
expected=json.loads(open('expected.json').read())
actual=model.predict_proba(new[new.columns[::-1]])[:,1]
assert np.allclose(actual,expected)
print(json.dumps({'same':True,'rows':len(new),'probabilities':actual.tolist()}))
'''
 Path('expected.json').write_text(json.dumps(expected))
 env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'.venv/lib/python3.12/site-packages')
 r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,env=env)
 result.update(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
 assert r.returncode==0,result
(HERE/'serialize-process.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
