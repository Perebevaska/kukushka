"""Frozen independent synthetic log checks. No training, no file pixel reads."""
import ast,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
B=Path(__file__).resolve().parent
t=next(t for t in json.loads((B/'tasks.json').read_text()) if t['id']=='alerts')
ns={'np':np,'pd':pd}
for source,names in [(t['solution'],{'alert_table'}),(t['setup'],{'episode_metrics'})]:
 for node in ast.parse(source).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen public function>','exec'),ns)
def log(start,truth,model,slot=0):
 times=pd.date_range('2000-01-01 '+start,periods=len(truth),freq='15min').strftime('%H:%M')
 return pd.DataFrame({'time':times,'slot':slot,'true':truth,'pred':model})
def evaluate(name,actual,expected):
 print(json.dumps({'name':name,'actual':actual,'expected':expected,'passed':actual==expected},ensure_ascii=False),flush=True)
r=ns['alert_table'];metrics=ns['episode_metrics']
# A=class0 empty, one start signal per k, nonzero class occupied.
base=log('12:00',[2,0,0,0,3],[2,0,0,0,3])
for k,when in [(1,'12:15'),(2,'12:30'),(3,'12:45')]:
 s=r(base,k);evaluate('empty_class0_k'+str(k),list(s.index[s[0]]),[when])
gap=base[base.time!='12:30'];s=r(gap,2);evaluate('missing_15min_breaks_series',int(s.to_numpy().sum()),0)
allslots=pd.concat([base.assign(slot=i) for i in range(12)],ignore_index=True);s=r(allslots.sample(frac=1,random_state=7),2)
evaluate('all12slots_shuffled',[int(s[i].sum()) for i in range(12)],[1]*12)
# Separate two short days. Expected costs fixed before the execution, class0 translated explicitly.
first=log('09:00',[1,1,1,0,0,0,1,1,1,1],[0,1,1,0,0,0,1,0,1,1]);second=log('12:30',[1,0,0,1,1,1],[0,0,1,1,0,1])
def costs(frame,fee):
 out={}
 for k in (1,2,3):
  m=metrics(frame,r(frame,k));out[k]=fee*m['false']+300*m['missed']+30*m['repeated']+m['delay_total']
 return out
for fee,expected in [(45,{1:90,2:15,3:30}),(6,{1:12,2:15,3:30})]:evaluate('firstday_fee'+str(fee),costs(first,fee),expected)
chosen=min(costs(first,6),key=costs(first,6).get);evaluate('chosen_before_day2',chosen,1)
c=costs(second,6);evaluate('second_day_allcosts',c,{1:312,2:0,3:300});evaluate('second_day_cost_fixed_k',c[chosen],312)
