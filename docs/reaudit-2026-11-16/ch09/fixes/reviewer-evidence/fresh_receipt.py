"""Verify the delivered archives, then use the student's documented CLI twice."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

here=Path(__file__).resolve().parent
student=here.parent/'student/retest'
data=here.parents[1]/'technical/data-baseline'
features=['gender','age','income_k','family_size']
f=pd.read_csv(data/'family_members.csv').set_index('member_id')
with tarfile.open(here/'first-receipt.tar') as archive:
    def historical(name):
        with archive.extractfile('artifacts/internal/'+name) as obj:
            return [row['member_id'] for row in csv.DictReader(io.TextIOWrapper(obj))]
    train=historical('train-ids.csv')
    test=historical('test-predictions.csv')
assert not set(train)&set(test) and set(train)|set(test)==set(f.index)
X=f.loc[train,features].to_numpy(); T=f.loc[test,features].to_numpy()
y=f.loc[train,'spend_k'].to_numpy(); target=f.loc[test,'spend_k'].to_numpy()
base=LinearRegression().fit(X,y)
published={}
for name in ['README.md','own_model.py','run_project.py','project.ipynb','inputs','artifacts']:
    src=student/name
    assert src.exists(),name
    for p in ([src] if src.is_file() else sorted(src.rglob('*'))):
        if p.is_file() and not p.name.startswith('.'):
            published[str(p.relative_to(student))]=hashlib.sha256(p.read_bytes()).hexdigest()
out={'sha256_of_delivered_files':published,'runs':{}}
def verify(directory, expected_key, new):
    mixed=directory/'contractor-demo'; private=directory/'internal'
    names=sorted(x.name for x in mixed.iterdir() if x.is_file())
    assert names==['new-hidden.csv','test-hidden.csv','train-hidden.csv']
    user_ids=pd.read_csv(private/'test-predictions.csv')
    assert list(pd.read_csv(private/'train-ids.csv').member_id)==train and list(user_ids.member_id)==test
    assert np.allclose(np.load(private/'key.npy'),expected_key)
    model=joblib.load(private/'hidden-model.joblib')
    pred=model.predict(T@expected_key)
    assert np.allclose(user_ids.actual_spend_k,target) and np.allclose(pred,user_ids.hidden_pred_k)
    public_train=pd.read_csv(mixed/'train-hidden.csv')
    public_test=pd.read_csv(mixed/'test-hidden.csv')
    public_new=pd.read_csv(mixed/'new-hidden.csv')
    labels=['f1','f2','f3','f4']
    assert list(public_train)==labels+['spend_k'] and list(public_test)==list(public_new)==labels
    assert np.allclose(public_train[labels],X@expected_key) and np.allclose(public_train.spend_k,y)
    assert np.allclose(public_test,T@expected_key) and np.allclose(public_new,new@expected_key)
    recipient=LinearRegression().fit(public_train[labels],public_train.spend_k)
    n_open=float(base.predict(new)[0]); n_model=float(model.predict(new@expected_key)[0]); n_pub=float(recipient.predict(public_new)[0])
    assert np.isclose(n_open,n_model) and np.isclose(n_open,n_pub) and np.allclose(pred,recipient.predict(public_test))
    return dict(train=len(train),test=len(test),identical_original_order=True,public_files=names,
                rank=int(np.linalg.matrix_rank(expected_key)),new_input=new.tolist()[0],
                r2=r2_score(target,pred),mae=mean_absolute_error(target,pred),max_delta=float(np.max(np.abs(pred-base.predict(T)))),
                new_raw=n_open,new_serialized=n_model,new_public=n_pub)
with tempfile.TemporaryDirectory() as td:
    work=Path(td)/'project'
    work.mkdir()
    for name in ['run_project.py','own_model.py','README.md']:
        shutil.copyfile(student/name,work/name)
    shutil.copytree(student/'inputs',work/'inputs')
    sys.path.insert(0,str(work))
    default=np.random.default_rng(42).normal(size=(4,4))
    altkey=np.array(json.loads((work/'inputs/alternate-key.json').read_text()))
    altrow=np.array(json.loads((work/'inputs/alternate-member.json').read_text())).reshape(1,4)
    out['runs']['delivered-default']=verify(student/'artifacts/default',default,np.array([[1,34,95,3]]))
    out['runs']['delivered-alternate']=verify(student/'artifacts/alternate',altkey,altrow)
    def run(name,keyfile,rowfile,key,row):
        reloutput='artifacts/'+name
        command=[sys.executable,'run_project.py','--key',str(keyfile),'--new',str(rowfile),'--output',reloutput]
        env=dict(os.environ,COURSE_DATA=str(data))
        result=subprocess.run(command,cwd=work,env=env,capture_output=True,text=True,timeout=100)
        if result.returncode: raise RuntimeError(result.stderr[-3000:])
        out['runs'][name]=dict(command=['python',*command[1:]],returncode=result.returncode,**verify(work/reloutput,key,row))
    run('readme-repeat','inputs/alternate-key.json','inputs/alternate-member.json',altkey,altrow)
    mine=np.random.default_rng(317).normal(size=(4,4)); new=np.array([[0,48,137,2]])
    assert not np.any(np.all(f[features].to_numpy()==new,axis=1))
    (work/'inputs/reviewer-key.json').write_text(json.dumps(mine.tolist()))
    (work/'inputs/reviewer-member.json').write_text(json.dumps(new[0].tolist()))
    run('reviewer-new','inputs/reviewer-key.json','inputs/reviewer-member.json',mine,new)
(here/'fresh-receipt.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
