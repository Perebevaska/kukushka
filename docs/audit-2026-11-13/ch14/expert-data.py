"""Reproduce the sensor day; evaluate new simulated days and same-demand restocking."""
from itertools import groupby
import importlib.util
import inspect
from pathlib import Path
import tempfile

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/"site/data"
spec=importlib.util.spec_from_file_location("generator",ROOT/"tools/gen_data.py")
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

# Record draws already made by the original generator. Assert its output is unchanged.
source=inspect.getsource(gen.gen_chapter14)
source=source.replace("    times, slots, labels, frames", "    observations['start']=stock.copy()\n    times, slots, labels, frames")
source=source.replace("            stock = np.where(stock == 0, rng.integers(4, 9, 12), stock)",
    "            supply=rng.integers(4,9,12)\n            observations[hhmm]=supply.copy()\n            stock=np.where(stock==0,supply,stock)")
source=source.replace("        stock = np.maximum(stock - (rng.random(12) < busy), 0)",
    "        demand=(rng.random(12)<busy)\n        observations['attempts'].append(demand)\n        stock=np.maximum(stock-demand,0)")

def scalars(x):
    return x.reshape(len(x),-1).astype(float)/255
def norm(x):
    flat=scalars(x)
    return (flat-flat.mean(1,keepdims=True))/np.maximum(flat.std(1,keepdims=True),1e-9)

def events(truth,pred,times,slots):
    times,slots=np.array(times),np.array(slots)
    alarms=[]
    episodes=[]
    for slot in np.unique(slots):
        order=np.flatnonzero(slots==slot)
        order=order[np.argsort(times[order])]
        p=pred[order]==0
        y=truth[order]==0
        starts=np.flatnonzero(p & np.r_[True,~p[:-1]])
        alarms_for_slot=np.array([i+1 for i in starts if i+1<len(p) and p[i+1]], dtype=int)
        alarms.extend((slot,i,y[i]) for i in alarms_for_slot)
        for empty,group in groupby(enumerate(y),key=lambda v:v[1]):
            inds=[i for i,_ in group]
            if empty:
                detected=[i for i in alarms_for_slot if inds[0]<=i<=inds[-1]]
                episodes.append((slot,inds[0],inds[-1],detected))
    return dict(alerts=len(alarms),false=sum(not a[2] for a in alarms),
                episodes=len(episodes),missed=sum(not e[3] for e in episodes),
                repeat=sum(max(0,len(e[3])-1) for e in episodes),
                delay_minutes=[int(15*(e[3][0]-e[1])) for e in episodes if e[3]])

def episode_summary(truth,pred,times,slots):
    res=events(truth,pred,times,slots)
    delays=res.pop("delay_minutes")
    return {**res,"delay_minmax":(min(delays),max(delays)) if delays else None}

def schedule(obs,first_replenish):
    stock=obs["start"].copy()
    empty=[]
    lost=[]
    for k,attempts in enumerate(obs["attempts"]):
        if k==first_replenish: stock=np.where(stock==0,obs["13:00"],stock)
        if k==40: stock=np.where(stock==0,obs["17:00"],stock)
        lost.append((stock==0)&attempts)
        stock=np.maximum(stock-attempts,0)
        empty.append(stock==0)
    return np.array(empty),np.array(lost)

with tempfile.TemporaryDirectory() as tmp:
    out=Path(tmp)
    ns=dict(gen.__dict__, OUT=out,observations={"attempts":[]})
    exec(compile(source,"instrumented-gen-ch14","exec"),ns)
    ns["gen_chapter14"](14014)
    for name in ["showcase.npz","showcase_day.npz"]:
        with np.load(out/name) as regen,np.load(DATA/name) as source_np:
            assert regen.files==source_np.files and all(np.array_equal(regen[k],source_np[k]) for k in regen.files)
            print("identical arrays",name,"byte-identical",(out/name).read_bytes()==(DATA/name).read_bytes())
    obs=ns["observations"]
    with np.load(out/"showcase.npz") as d: x,y=d["X"],d["y"]
    with np.load(out/"showcase_day.npz") as d: xd,yd,times,slots=d["X"],d["y"],d["time"],d["slot"]
    print("shape/class", x.shape,np.bincount(y),xd.shape,np.bincount(yd))
    eval_keys=set(zip(times,slots)); print("unique time/slot",len(eval_keys))
    train_images={im.tobytes() for im in x}; day_images={im.tobytes() for im in xd}
    print("train unique, day unique, intersect",len(train_images),len(day_images),len(train_images&day_images))
    raw=RandomForestClassifier(n_estimators=100,random_state=0).fit(scalars(x),y)
    fixed=RandomForestClassifier(n_estimators=100,random_state=0).fit(norm(x),y)
    ev=times>="18:00"
    print("ratio raw brightness",xd[ev].mean()/xd[~ev].mean())
    for name,f,fn in [("raw",raw,scalars),("normalized",fixed,norm)]:
        pred=f.predict(fn(xd))
        for split,mask in [("day",~ev),("eve",ev)]:
            print(name,split,"rows/correct",mask.sum(),(yd[mask]==pred[mask]).sum(),
                  "confusion",confusion_matrix(yd[mask],pred[mask],labels=[0,1,2,3]).tolist())
        print(name,episode_summary(yd,pred,times,slots))
    pred=fixed.predict(norm(xd))
    print("factual morning/interval",[(yd[(times>=a)&(times<b)]==0).sum()*.25 for a,b in [("07:00","13:00"),("11:00","13:00"),("13:00","17:00")]])
    factual,lost_old=schedule(obs,24)
    earlier,lost_new=schedule(obs,16)
    assert np.array_equal(factual,yd.reshape(-1,12)==0)
    # Exclude 22:00 from occupancy-duration integration, as the next reading is unavailable.
    for title,start,stop in [("11–13",16,24),("13–17",24,40),("whole 07–22",0,60)]:
        sec=slice(start,stop)
        print("restock",title,"historical and earlier empty-slot hours, attempted sales unmet",
              factual[sec].sum()/4,earlier[sec].sum()/4,lost_old[sec].sum(),lost_new[sec].sum())

    # The normalizer and forest are frozen before generating these separate simulated days.
    totals=[]
    for seed in (14015,14016,14017,14018,14019,14020,14021,14022):
        gen.OUT=out
        gen.gen_chapter14(seed)
        with np.load(out/"showcase_day.npz") as d:
            y2,t2,s2=d["y"],d["time"],d["slot"]
            p2=fixed.predict(norm(d["X"]))
        mask=t2>="18:00"
        result=episode_summary(y2,p2,t2,s2)
        totals.append([result[k] for k in ["episodes","missed","false","repeat"]])
        print("unseen day",seed,"evening accuracy",round((y2[mask]==p2[mask]).mean(),3),result)
    print("8-day totals episodes/missed/false/repeat",np.sum(totals,axis=0))

    # Compare an actual background-filled translation with toroidal wrapping.
    xr=np.roll(x[:250],4,axis=2)
    filled=np.empty_like(xr)
    filled[:,:,4:]=x[:250,:,:-4]
    filled[:,:,:4]=np.median(x[:250,:,:1],axis=(1,2)).astype(np.uint8)[:,None,None]
    print("opposite edge mean absolute difference (uint8)",np.mean(abs(xr[:,:,:4].astype(float)-filled[:,:,:4].astype(float))))

for rule in ["zero camera","constant gray camera"]:
    val=0 if rule=="zero camera" else 128
    a=np.full((1,32,32),val,dtype=np.uint8)
    with np.errstate(divide="ignore",invalid="ignore"):
        unsafe=(scalars(a)-scalars(a).mean(1,keepdims=True))/scalars(a).std(1,keepdims=True)
    print(rule,"finite fraction with lesson normalize",np.isfinite(unsafe).mean(),
          "finite guarded normalizer",np.isfinite(norm(a)).all())

# In scene coordinates these boxes do not intersect despite overlapping y.
a=(0,0,4,4); b=(6,0,10,4)
w=min(a[2],b[2])-max(a[0],b[0])
h=min(a[3],b[3])-max(a[1],b[1])
wrong=abs(w)*max(0,h)
print("disjoint horizontal boxes: correct, abs-width",0,wrong/(32-wrong))
