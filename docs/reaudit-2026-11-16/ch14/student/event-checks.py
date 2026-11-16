"""Небольшие проверки своего кода событий, без ML и чужих функций."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import ast
from pathlib import Path
import pandas as pd
import numpy as np
D=Path(__file__).resolve().parent
source=ast.parse((D/'project.py').read_text())
for node in source.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['grid','signals','minute','metrics']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'own-project-functions','exec'))
PRICES=dict(false=100,missed=300,repeated=30,delay_minute=1)
full=pd.DataFrame(dict(time=['12:00','12:15','12:30'],slot=[0]*3,true=[2,0,0],pred=[2,0,0]))
missing=full[full.time!='12:15']
assert signals(full,2)==[('12:30',0)]
assert signals(missing,2)==[]
assert signals(full.sample(frac=1,random_state=7),2)==signals(full,2)
parking=pd.DataFrame(dict(time=['09:00','09:15','09:30','10:00','10:15','10:30'],slot=[0]*6,true=[1,1,0,0,0,1],pred=[0,1,0,0,0,1]))
sig=signals(parking,2)
assert sig==[('10:15',0)]
parking['signal']=[(t,0) in sig for t in parking.time]
parking.to_csv(D/'parking-check.csv',index=False)
print('2,0,0 full:',signals(full,2),'missing12:15:',signals(missing,2),'shuffle: equal')
print(parking.to_string(index=False))
print('Parking delay from first observed free09:30:',minute('10:15')-minute('09:30'),'minutes; unresolved continuity across09:45: unknown')
print('Observed-episode metrics split at missing:',metrics(parking,sig)[0])
