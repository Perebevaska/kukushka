"""Frozen own model/policy inference. No labels, fitting, or policy selection."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import json,pickle,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
D=Path(__file__).resolve().parent
W=Path('/private/tmp/kuch14round/student-holdout')
def normalize(Z):
    f=Z.reshape(len(Z),-1).astype(float)
    return (f-f.mean(1,keepdims=True))/(f.std(1,keepdims=True)+1e-8)
def signals(df,k):
    empty=df.pivot(index='time',columns='slot',values='pred').sort_index().eq(0)
    ticks=pd.date_range('2000-01-01 '+empty.index.min(),'2000-01-01 '+empty.index.max(),freq='15min').strftime('%H:%M')
    empty=empty.reindex(ticks,fill_value=False).fillna(False)
    run=empty.copy()
    for j in range(1,k):run &= empty.shift(j,fill_value=False)
    run &= ~run.shift(1,fill_value=False)
    return pd.DataFrame([(t,int(s)) for (t,s),v in run.stack().items() if v],columns=['time','slot'])
if (D/'predictions.csv').exists():raise RuntimeError('Predictions already frozen; do not overwrite')
policy=json.loads((W/'project-freeze.json').read_text())
assert policy['chosen_k']==2
assert policy['normalization']=='per frame mean/std +1e-8'
with open(W/'project-model.pkl','rb') as f:model=pickle.load(f)
with np.load(W/'frames.npz') as z:
    assert 'y' not in z.files
    assert z['X'].shape==(732,32,32)
    keys=pd.DataFrame({'time':z['time'],'slot':z['slot']})
    assert len(keys)==732 and not keys.duplicated(['time','slot']).any()
    pred=model.predict(normalize(z['X']/255))
frame=keys.assign(pred=pred).sort_values(['time','slot']).reset_index(drop=True)
assert len(frame)==732 and set(frame.pred)<=set(range(4))
sig=signals(frame,policy['chosen_k'])
assert sig.equals(signals(frame.sample(frac=1,random_state=7),policy['chosen_k']))
frame.to_csv(D/'predictions.csv',index=False)
sig.to_csv(D/'signals.csv',index=False)
summary=dict(rows=len(frame),unique_keys=len(frame.drop_duplicates(['time','slot'])),times=frame.time.nunique(),slots=frame.slot.nunique(),classes_predicted={str(k):int(v) for k,v in frame.pred.value_counts().sort_index().items()},signals=len(sig),chosen_k=policy['chosen_k'],normalization=policy['normalization'],shuffle_invariant=True,labels_available=False,source_hashes={n:hashlib.sha256((W/n).read_bytes()).hexdigest() for n in ['frames.npz','project-model.pkl','project-freeze.json','own-project.py']})
(D/'key-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
