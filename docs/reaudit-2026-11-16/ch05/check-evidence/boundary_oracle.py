"""Independent numeric witness: no author solution or author check is executed."""
from pathlib import Path
import json,numpy as np,pandas as pd
from scipy.stats import norm,chi2
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[4]
x=pd.read_csv(ROOT/'site/data/ab_promise.csv')
A=x.loc[x.group.eq('A'),'amount'].to_numpy(float)
B=x.loc[x.group.eq('B'),'amount'].to_numpy(float)
orders=x[x.ordered.eq(1)]
a,b=[orders.loc[orders.group.eq(g),'late'].to_numpy() for g in ['A','B']]
pool=(a.sum()+b.sum())/(a.size+b.size)
z=(b.mean()-a.mean())/np.sqrt(pool*(1-pool)*(1/a.size+1/b.size))
late_p=float(2*norm.sf(abs(z)))
def intervals(k):
 d=float(np.mean(k*B)-np.mean(A))
 e=1.96*np.sqrt(np.var(A,ddof=1)/A.size+np.var(k*B,ddof=1)/B.size)
 return d-e,d+e
def decide(lo,hi):
 if late_p>=.05 or b.mean()>=a.mean() or hi < -10:return 'не внедрять'
 if lo > -10:return 'внедрять'
 return 'неопределённо'
rows=[]
for i,label in [(0,'lower'),(1,'upper')]:
 for target in [-9.96,-10.04]:
  k=float(brentq(lambda v:intervals(v)[i]-target,.1,3))
  lo,hi=map(float,intervals(k))
  rows.append(dict(endpoint=label,target=target,k=k,raw_lo=lo,raw_hi=hi,shown_lo=round(lo,1),shown_hi=round(hi,1),expected=decide(lo,hi),rounded_decision=decide(round(lo,1),round(hi,1))))
pool=(131+162)/2000
p=float(2*norm.sf(abs((162-131)/1000/np.sqrt(pool*(1-pool)*2/1000))))
srm=float(chi2.sf((514-600)**2/(514+600),1))
result=dict(basis='Independent pooled normal z and sample-variance interval, direct array operations; input CSV read-only.',original_late_p=late_p,revenue_boundaries=rows,p_boundary=dict(raw=p,shown=round(p,4),raw_significant=p<.05,rounded_significant=round(p,4)<.05),srm_boundary=dict(raw=srm,shown=round(srm,4),raw_ok=srm>=.01,rounded_ok=round(srm,4)>=.01))
Path(__file__).with_name('boundary-oracle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
