"""Independent algebraic probes, including rank and intercept counterexamples."""
import json
from pathlib import Path
import numpy as np

def extended(x):
    return np.column_stack((np.ones(len(x)), x))

def predict(x,y,z):
    return extended(z) @ np.linalg.lstsq(extended(x),y,rcond=None)[0]

x=np.array([[0,0],[1,1],[2,2]],float)
y=x[:,0]
p=np.diag([1,2])
z=np.array([[2,0],[0,2]])
v=np.array([.5,.5])
small=np.array([[1],[1+1e-8],[1-1e-8]])
a=extended(small)
target=1-small.ravel()
try:
    normal=np.linalg.solve(a.T@a,a.T@target).tolist()
except np.linalg.LinAlgError as err:
    normal=str(err)
xs=np.array([[0,0],[0,1],[1,0],[1,1]])
drop=np.diag([1,0])
singular={}
for n in [0,1]:
    yt=xs[:,n]
    singular[n]=1-np.mean((predict(xs@drop,yt,xs@drop)-yt)**2)/np.var(yt)
scores = [(0.81234561,0.8123456103),(0.81234561,0.81234563),(0.,1e-9)]
rows=[dict(a=a,b=b,unrounded_accept=abs(a-b)<=1e-9,rounded_accept=abs(round(a,4)-round(b,4))<=1e-9,report=round(b,4)) for a,b in scores]
out=dict(
    fixed_raw=(z@v).tolist(),fixed_hidden=(z@p@np.linalg.solve(p,v)).tolist(),
    rank=int(np.linalg.matrix_rank(extended(x))),fit_raw=predict(x,y,z).tolist(),
    fit_hidden=predict(x@p,y,z@p).tolist(),fit_train=predict(x@p,y,x@p).tolist(),
    unary_temperature_C=2+.5*20,unary_temperature_F=2-32*.5/1.8+68*.5/1.8,
    without_intercept_zero=(0.,32.),gram_rank=int(np.linalg.matrix_rank(a.T@a)),design_rank=int(np.linalg.matrix_rank(a)),
    solve_gram=normal,stable_fit=np.linalg.lstsq(a,target,rcond=None)[0].tolist(),singular_r2=singular,
    raw_r2=rows,partial_pair_rank=int(np.linalg.matrix_rank(np.tile([1,3,7,2],(4,1)))),
    broadcasting=(np.array([7,8])+np.array([2])).tolist(),axes={'price_by_label':2*10+1*3,'wrong_position':2*3+1*10})
Path(__file__).with_name('arithmetic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
