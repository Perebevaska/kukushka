"""Run in the native course environment. Computes from the four distributed NPZ."""
import hashlib
import os
from pathlib import Path
from collections import Counter
from itertools import groupby
from operator import itemgetter
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[name] = "1"

import numpy as np
from sklearn.ensemble import RandomForestClassifier

repo = Path(__file__).resolve().parents[4]
data = repo / "site/data"
def load(name):
    path = data / (name + ".npz")
    with np.load(path) as archive:
        result = dict(archive)
    print(name, hashlib.sha256(path.read_bytes()).hexdigest(),
          {k: [v.shape,str(v.dtype)] for k,v in result.items()})
    return result

def minute(t):
    h, m = map(int,t.split(":"))
    return h * 60 + m

def norm(x):
    a = (x / 255).reshape(len(x),-1)
    return (a-a.mean(1,keepdims=True))/a.std(1,keepdims=True)

def outcomes(labels,k):
    lo, hi = min(t for t,s in labels), max(t for t,s in labels)
    slots = sorted({s for t,s in labels})
    signals = set()
    miss = repeat = fp = 0
    delay = []
    for slot in slots:
        run = 0
        observations = []
        for t in range(lo,hi+1,15):
            pred, truth = labels.get((t,slot), (None,None))
            run = run + 1 if pred == 0 else 0
            hit = run == k
            if hit:
                signals.add((t,slot))
            fp += int(hit and truth != 0)
            observations.append((truth == 0,t,hit))
        for is_empty, values in groupby(observations,key=itemgetter(0)):
            if is_empty:
                episode = list(values)
                hits = [t for _,t,hit in episode if hit]
                if hits:
                    repeat += len(hits) - 1
                    delay.append(hits[0] - episode[0][1])
                else:
                    miss += 1
    total = sum(delay)
    cost = fp*120 + miss*300 + repeat*30 + total
    return signals, dict(n_alerts=len(signals),false=fp,missed=miss,repeated=repeat,
                         delay_minutes=total/len(delay) if delay else None,delay_total=total,cost=cost)

training = load("showcase")
first = load("showcase_day")
stock = load("showcase_inventory")
print("training class counts", dict(zip(training["classes"],np.bincount(training["y"]).tolist())))
print("training unique image hashes",len(set(map(bytes,training["X"]))))
xf = norm(training["X"])
forest = RandomForestClassifier(100,random_state=0,n_jobs=1).fit(xf,training["y"])
raw_forest = RandomForestClassifier(100,random_state=0,n_jobs=1).fit(
    training["X"].reshape(len(xf),-1)/255, training["y"])
def keys_and_metrics(day):
    x,y,slot,t = (day[k] for k in ("X","y","slot","time"))
    keys = [(minute(tm),int(s)) for tm,s in zip(t,slot)]
    assert len(set(keys))==len(keys)==61*12
    assert set(keys)=={(m,s) for m in range(420,1321,15) for s in range(12)}
    assert set(np.unique(y))==set(range(4))
    assert np.all((y==0)|(y==1+slot//4))
    assert np.isfinite(x).all()
    pred = forest.predict(norm(x))
    raw = raw_forest.predict(x.reshape(len(x),-1)/255)
    dusk = t >= '18:00'
    print("class counts",np.bincount(y),"brightness ratio",x[dusk].mean()/x[~dusk].mean())
    for name,labels in [("raw",raw),("normalized",pred)]:
        print(name,"day/evening accuracy",*[round(np.mean(labels[m]==y[m]),4) for m in (~dusk,dusk)],
              "evening true empty/recognized",int((y[dusk]==0).sum()),int(((labels==0)&(y==0)&dusk).sum()))
    return dict(zip(keys,zip(pred,y)))

one = keys_and_metrics(first)
costs = {}
for k in (1,2,3):
    hits, stats = outcomes(one,k)
    shuffled = dict(sorted(one.items(),key=lambda kv: (kv[0][1],-kv[0][0])))
    assert outcomes(shuffled,k)==(hits,stats)
    costs[k] = stats["cost"]
    print("day 1", k, stats)
chosen = min(costs, key=lambda k:(costs[k],k))
print("chosen before opening day 2",chosen,flush=True)
two = keys_and_metrics(load("showcase_day_next"))
print("day 2",chosen,outcomes(two,chosen)[1])
fixture = {(t,s):(0,0) for t in (660,675,690) for s in range(12)}
del fixture[675,4]
assert outcomes(fixture,2)[0]=={(675,s) for s in range(12) if s!=4}
print("gapped slot 4 is silent; other 11 each alert once at 11:15")
observed = Counter()
for (t,s),(_,y) in one.items():
    if 660 <= t < 780 and y==0:
        observed[s//4] += .25
print("observation 11–13",sorted(observed.items()),sum(observed.values()))
for name, refills in [("baseline",{780:0,1020:1}),("shift",{660:0,1020:1}),
                      ("extra",{660:0,780:0,1020:1})]:
    morning = afternoon = daily = added = 0
    for s,initial in enumerate(stock["initial"]):
        level = int(initial)
        for j,d in enumerate(stock["demand"]):
            t = 420+j*15
            if t in refills and level==0:
                level = int(stock["refill"][refills[t],s])
                added += level
            level = max(0,level-int(d[s]))
            if name=="baseline":
                assert (level==0)==(one[t,s][1]==0)
            if level==0:
                morning += .25*(660<=t<780)
                afternoon += .25*(780<=t<1020)
                daily += .25*(420<=t<1320)
    print(name,"morning afternoon whole day",morning,afternoon,daily,"units added in cells",added)
