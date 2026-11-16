import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import json,hashlib,ast
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
P=D.parent/'holdout-predictions'
I=D.parents[2]/'student'
W=Path('/private/tmp/kuch14round/student-holdout-labels')
# Verify existing frozen predictions; never rewrite them.
for line in (P/'SHA256SUMS').read_text().splitlines():
    h,n=line.split('  ',1)
    assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h
pred=pd.read_csv(P/'predictions.csv',dtype={'time':str,'slot':int,'pred':int})
labels=pd.read_csv(W/'labels.csv',dtype={'time':str,'slot':int,'true':int})
sig=pd.read_csv(P/'signals.csv',dtype={'time':str,'slot':int})
assert len(pred)==len(labels)==732
assert not pred.duplicated(['time','slot']).any() and not labels.duplicated(['time','slot']).any()
a=pred.merge(labels,on=['time','slot'],how='outer',validate='one_to_one',indicator=True)
assert len(a)==732 and a['_merge'].eq('both').all()
a=a.drop(columns='_merge').sort_values(['time','slot']).reset_index(drop=True)
b=pred.sample(frac=1,random_state=7).merge(labels.sample(frac=1,random_state=8),on=['time','slot'],validate='one_to_one').sort_values(['time','slot']).reset_index(drop=True)
assert a.equals(b[a.columns])
policy=json.loads(Path('/private/tmp/kuch14round/student-holdout/project-freeze.json').read_text())
PRICES=policy['prices']
assert PRICES==dict(false=120,missed=300,repeated=30,delay_minute=1)
assert policy['chosen_k']==2
# Reuse own previous metric definitions without changing episode or cost rules.
source=ast.parse((I/'project.py').read_text())
for node in source.body:
    if isinstance(node,ast.FunctionDef) and node.name in ['grid','minute','metrics']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'own-frozen-metric-functions','exec'))
signals=list(sig.itertuples(index=False,name=None))
result,episodes=metrics(a,signals)
result.update(accuracy=float(a.true.eq(a.pred).mean()),rows=len(a),unique_keys=len(a.drop_duplicates(['time','slot'])),signals_frozen=len(sig),chosen_k=2,prices=PRICES,shuffle_join_equal=True)
rows=[]
for slot,ticks in episodes:
    found=sorted(t for t,s in signals if s==slot and t in ticks)
    rows.append(dict(slot=slot,start=ticks[0],end=ticks[-1],frames=len(ticks),signal_count=len(found),first_signal=found[0] if found else None,delay_minutes=minute(found[0])-minute(ticks[0]) if found else None))
ep=pd.DataFrame(rows).sort_values(['start','slot']).reset_index(drop=True)
ep.to_csv(D/'episodes.csv',index=False)
a.to_csv(D/'joined.csv',index=False)
false=sig.merge(a[['time','slot','true','pred']],on=['time','slot'],validate='one_to_one').query('true != 0')
false.to_csv(D/'false-signals.csv',index=False)
missed=ep[ep.signal_count==0]
if len(missed):
    chosen=missed.iloc[0];slot=int(chosen.slot)
    lo=minute(chosen.start)-15;hi=minute(chosen.end)+15
    trace=a[(a.slot==slot)&a.time.map(lambda t:lo<=minute(t)<=hi)].copy()
    error=dict(type='missed_episode',slot=slot,start=chosen.start,end=chosen.end)
elif len(false):
    chosen=false.sort_values(['time','slot']).iloc[0];slot=int(chosen.slot)
    lo=minute(chosen.time)-30;hi=minute(chosen.time)+30
    trace=a[(a.slot==slot)&a.time.map(lambda t:lo<=minute(t)<=hi)].copy()
    error=dict(type='false_signal',slot=slot,time=chosen.time)
else:trace=pd.DataFrame();error=dict(type='none_observed')
if len(trace):
    trace['signal']=[(t,slot) in signals for t in trace.time]
    trace.to_csv(D/'error-trace.csv',index=False)
    fig,ax=plt.subplots(figsize=(8,3))
    xx=np.arange(len(trace))
    ax.step(xx,trace.true.eq(0).astype(int),where='mid',label='true empty')
    ax.scatter(xx,trace.pred.eq(0).astype(int)+.03,label='pred empty')
    ax.set_xticks(xx,trace.time,rotation=45);ax.set_ylabel('empty=1, occupied=0');ax.set_title(f"slot{slot}: {error['type']}");ax.legend();fig.tight_layout();fig.savefig(D/'error-trace.png');plt.close(fig)
(D/'error-choice.json').write_text(json.dumps(error,ensure_ascii=False,indent=2))
(D/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(D/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'predictions.csv',P/'signals.csv',W/'labels.csv',I/'project.py']},indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2));print('ERROR',error);print(trace.to_string(index=False))
