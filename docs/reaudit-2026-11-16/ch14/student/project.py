"""Собственный проект из публичной теории. Два отдельных запуска: day1, затем day2."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import sys,json,pickle,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
D=Path(__file__).resolve().parent
W=Path('/private/tmp/kuch14round/student/data')
PRICES=dict(false=120,missed=300,repeated=30,delay_minute=1)
def normalize(Z):
 f=Z.reshape(len(Z),-1).astype(float)
 return (f-f.mean(1,keepdims=True))/(f.std(1,keepdims=True)+1e-8)
def frame(day,m):
 z=np.load(W/day)
 return pd.DataFrame(dict(time=z['time'],slot=z['slot'],true=z['y'],pred=m.predict(normalize(z['X']/255))))
def grid(df,col):
 a=df.pivot(index='time',columns='slot',values=col).sort_index()
 ticks=pd.date_range('2000-01-01 '+a.index.min(),'2000-01-01 '+a.index.max(),freq='15min').strftime('%H:%M')
 return a.reindex(ticks)
def signals(df,k):
 a=grid(df,'pred').eq(0)
 r=a.copy()
 for j in range(1,k):r &= a.shift(j,fill_value=False)
 r &= ~r.shift(1,fill_value=False)
 return [(t,int(s)) for (t,s),v in r.stack().items() if v]
def minute(t):return int(t[:2])*60+int(t[3:])
def metrics(df,sig):
 truth=grid(df,'true').eq(0)
 episodes=[]
 for s in truth.columns:
  current=[]
  for t,v in truth[s].items():
   if v:current.append(t)
   elif current:episodes.append((int(s),current));current=[]
  if current:episodes.append((int(s),current))
 false=sum(not bool(truth.loc[t,s]) for t,s in sig)
 missed=0;repeat=0;delays=[]
 for s,ticks in episodes:
  found=sorted(t for t,ss in sig if ss==s and t in ticks)
  if not found:missed+=1
  else:repeat+=len(found)-1;delays.append(minute(found[0])-minute(ticks[0]))
 out=dict(n_alerts=len(sig),false=int(false),missed=missed,repeated=repeat,delay_total=sum(delays),delay_minutes=float(np.mean(delays)) if delays else None,n_episodes=len(episodes))
 out['cost']=false*PRICES['false']+missed*PRICES['missed']+repeat*PRICES['repeated']+sum(delays)*PRICES['delay_minute']
 return out,episodes
if sys.argv[1]=='day1':
 if (D/'project-freeze.json').exists():raise RuntimeError('Выбор уже зафиксирован, не перезаписываю')
 z=np.load(W/'showcase.npz');m=RandomForestClassifier(100,random_state=0,n_jobs=1).fit(normalize(z['X']/255),z['y'])
 df=frame('showcase_day.npz',m);df.to_csv(D/'project-day1.csv',index=False)
 table={k:metrics(df,signals(df,k))[0] for k in [1,2,3]}
 chosen=min(table,key=lambda k:(table[k]['cost'],k))
 frozen=dict(chosen_k=chosen,prices=PRICES,selection_day='showcase_day.npz',normalization='per frame mean/std +1e-8',policy_table=table,model='RF100 random_state0 n_jobs1')
 (D/'project-freeze.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2))
 with open(D/'project-model.pkl','wb') as f:pickle.dump(m,f)
 print(json.dumps(frozen,ensure_ascii=False,indent=2))
 # Key trace and shuffle invariance
 sig=signals(df,chosen);assert sorted(sig)==sorted(signals(df.sample(frac=1,random_state=7),chosen))
 trace=df[df.slot==0].copy();trace['signal']=[(t,0) in sig for t in trace.time];trace.to_csv(D/'project-slot0.csv',index=False)
 fig,ax=plt.subplots(figsize=(12,3));ax.step(range(len(trace)),trace.true.eq(0),where='mid',label='истинно пусто');ax.scatter([i for i,t in enumerate(trace.time) if (t,0) in sig],[1.08]*sum((t,0) in sig for t in trace.time),label='сигнал');idx=np.arange(0,len(trace),8);ax.set_xticks(idx,trace.time.to_numpy()[idx]);ax.set_ylabel('ячейка0: пустота / сигнал');ax.legend();fig.tight_layout();fig.savefig(D/'project-slot0.png');plt.close(fig)
 inv=np.load(W/'showcase_inventory.npz');times=np.array(pd.date_range('2000-01-01 07:00',periods=len(inv['demand']),freq='15min').strftime('%H:%M'))
 def simulate(events):
  stock=inv['initial'].copy();empty=[]
  for t,demand in zip(times,inv['demand']):
   if t in events:stock+=inv['refill'][events[t]]*(stock==0)
   stock=np.maximum(stock-demand,0);empty.append(stock==0)
  empty=np.array(empty)
  return [float(empty[(times>=a)&(times<b)].sum()*.25) for a,b in [('11:00','13:00'),('13:00','17:00'),('07:00','22:00')]]
 scenarios=pd.DataFrame([simulate({'13:00':0,'17:00':1}),simulate({'11:00':0,'17:00':1}),simulate({'11:00':0,'13:00':0,'17:00':1})],index=['исходный','перенос','добавочная'],columns=['morning','afternoon','whole_day']);scenarios.to_csv(D/'project-scenarios.csv');print(scenarios.to_string())
 truth=grid(df,'true').eq(0);obs=truth.loc[(truth.index>='11:00')&(truth.index<'13:00')].sum().sum()*.25;print('observed_empty_cell_hours',obs)
elif sys.argv[1]=='day2':
 frozen=json.loads((D/'project-freeze.json').read_text());assert frozen['prices']==PRICES
 with open(D/'project-model.pkl','rb') as f:m=pickle.load(f)
 df=frame('showcase_day_next.npz',m);df.to_csv(D/'project-day2.csv',index=False)
 out,episodes=metrics(df,signals(df,frozen['chosen_k']));out['chosen_k']=frozen['chosen_k'];out['accuracy']=float(df.true.eq(df.pred).mean());out['accuracy_evening']=float(df[df.time>='18:00'].true.eq(df[df.time>='18:00'].pred).mean())
 (D/'project-day2-metrics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
else:raise ValueError('day1/day2')
