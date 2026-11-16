"""Chapter 11 numerical tests. --native also runs every code cell of the extra notebook."""
from contextlib import chdir
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile

import numpy as np
import pandas as pd
from scipy.special import logsumexp, softmax
from scipy.stats import binomtest
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site/data"

if "--native" in sys.argv:
    import torch
    torch.set_num_threads(1)
    cells = json.loads((ROOT / "site/notebooks/extra/ch11-pytorch-tabular.ipynb").read_text())["cells"]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "data").symlink_to(DATA, target_is_directory=True)
        with chdir(tmp):
            ns = {}
            for i, cell in enumerate(cells):
                if cell["cell_type"] == "code":
                    exec(compile("".join(cell["source"]), f"notebook-cell-{i}", "exec"), ns)
            print("Re-executed notebook", ns["summary"].to_string(index=False))
    bn = torch.nn.BatchNorm1d(1)
    batch = torch.tensor([[2.0],[4.0],[6.0],[8.0]])
    bn(batch)
    print("torch and exercise running variances",bn.running_var.item(), .9 + .1*float(batch.var(correction=0)))
    sys.exit()

spec = importlib.util.spec_from_file_location("generator", ROOT / "tools/gen_data.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
with tempfile.TemporaryDirectory() as tmp:
    generator.OUT = Path(tmp)
    for chapter, seed, filename in [(4, 4004, "deliveries.csv"), (6, 6006, "guests_churn.csv")]:
        getattr(generator, f"gen_chapter{chapter}")(random.Random(seed))
        assert (generator.OUT / filename).read_bytes() == (DATA / filename).read_bytes()
        print("byte match", filename)
d = pd.read_csv(DATA/"deliveries.csv",parse_dates=["created"])
g = pd.read_csv(DATA/"guests_churn.csv")
print("churn rows, unique, events, blanks",len(g),g.guest_id.nunique(),g.churned.sum(),g.avg_check.isna().sum())
print("delivery rows, clean, nulls",len(d),d.actual_min.between(1,299).sum(),d.isna().sum().loc[lambda s:s>0].to_dict())
print("dates", d.created.min(), d.created.max())

# Independent derivative of mean softmax CE through a tanh hidden layer.
rng = np.random.default_rng(37)
x = rng.normal(size=(5, 3))
w1, w2 = rng.normal(size=(3,4)), rng.normal(size=(4,3))
y = np.array([0,1,2,0,2])
def loss(w):
    scores = np.tanh(x @ w) @ w2
    return np.mean(logsumexp(scores, axis=1) - scores[np.arange(len(y)),y])
h = np.tanh(x @ w1)
delta = (softmax(h @ w2,axis=1) - np.eye(3)[y]) / len(y)
grad = x.T @ ((delta @ w2.T)*(1-h*h))
step = 1e-5
finite = np.array([(loss(w1 + e*step)-loss(w1-e*step))/(2*step)
                   for e in np.eye(w1.size).reshape(-1,*w1.shape)]).reshape(w1.shape)
print("finite difference maximum discrepancy", np.max(abs(finite-grad)))
print("tied low temperature", softmax(np.array([2,2,1])/.001))

digits = load_digits()
a,b,c,d = train_test_split(digits.data/16, digits.target, test_size=.25,random_state=42,stratify=digits.target)
print("data, classes, unique images",digits.data.shape, np.bincount(digits.target),np.unique(digits.data,axis=0).shape[0])
def shifted(x, dy, dx):
    img = x.reshape(-1,8,8)
    target = np.zeros_like(img)
    target[:, max(0,dy):min(8,8+dy), max(0,dx):min(8,8+dx)] = img[:,max(0,-dy):min(8,8-dy),max(0,-dx):min(8,8-dx)]
    return target.reshape(-1,64)
def examine(label, model, features):
    pr = model.predict_proba(features)
    error = pr.argmax(1) != d
    review = pr.max(1) < .9
    print(label, "correct, sent, errors sent, auto errors, auto total",
          (~error).sum(), review.sum(), (error & review).sum(), (error & ~review).sum(), (~review).sum())
def mlp():
    return MLPClassifier(hidden_layer_sizes=(64,),alpha=.001,max_iter=500,random_state=0)

model = mlp().fit(a,c)
examine("logistic",LogisticRegression(max_iter=2000).fit(a,c),b)
knn = KNeighborsClassifier(n_neighbors=3).fit(a,c)
examine("3NN",knn,b)
examine("MLP original",model,b)
for dy, dx in [(0,1),(0,-1),(1,0),(-1,0)]:
    examine(f"MLP shift {dy},{dx}",model,shifted(b,dy,dx))
aug = mlp().fit(np.concatenate((a,shifted(a,0,1))),np.tile(c,2))
examine("MLP augmented original",aug,b)
examine("MLP augmented right",aug,shifted(b,0,1))
examine("MLP augmented left",aug,shifted(b,0,-1))
print("caught errors Wilson 95%",binomtest(6,8).proportion_ci(method="wilson"))
print("iid illustration, 10-digit field review",1-(1-(model.predict_proba(b).max(1)<.9).mean())**10)

# Simulate a fixed review budget (37 images). Rank by scores without seeing test labels.
distances, neighbors = knn.kneighbors(b,n_neighbors=len(a))
guesses = knn.predict(b)
same_vote_class = c[neighbors] == guesses[:,None]
nearest_same = np.where(same_vote_class, distances, np.inf).min(1)
nearest_other = np.where(~same_vote_class,distances,np.inf).min(1)
confidence = (nearest_other - nearest_same) / np.maximum(nearest_other, 1e-12)
send = np.argsort(confidence,kind="stable")[:37]
print("3NN at equal budget, reviewed, found, auto errors",len(send),(guesses[send]!=d[send]).sum(),
      (guesses!=d).sum() - (guesses[send]!=d[send]).sum())
print("3NN max vote on actual test",np.unique(knn.predict_proba(b).max(1),return_counts=True))

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
orders = pd.read_csv(DATA/"deliveries.csv",parse_dates=["created"]).sort_values("created")
orders = orders[orders.actual_min.between(1,299)]
features = pd.get_dummies(orders.assign(hour=orders.created.dt.hour)[["distance_km","items","hour","courier","weather","shop_id"]],dtype=int)
train = orders.created < "2026-11-01"
for name, reg in [("HGB mean", HistGradientBoostingRegressor(random_state=42)),
                  ("HGB q90", HistGradientBoostingRegressor(loss="quantile",quantile=.9,random_state=42))]:
    reg.fit(features[train], orders.actual_min[train])
    target = orders.actual_min[~train]
    predicted = reg.predict(features[~train])
    print("Nov deliveries",name,len(target),"MAE, fraction late and mean promise",mean_absolute_error(target,predicted),
          (target>predicted).mean(), predicted.mean())

# Keep the chapter's trained networks fixed; give the held-out 540 points separate roles.
import ast
import re
from sklearn.datasets import make_moons
source = (ROOT/"content/ch11/04c-debug.md").read_text().split("## task: dropout-net")[1].split("## task:")[0]
code = re.search(r"### solution\s+```python\n(.*?)\n```",source,re.S).group(1)
train_def = next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=="train_drop")
namespace={"np":np}
exec(compile(ast.Module(body=[train_def],type_ignores=[]),"fixed-course-trainer","exec"),namespace)
moon_x, moon_y = make_moons(600,noise=.3,random_state=1)
mx, hx, my, hy = train_test_split(moon_x, moon_y, train_size=60,random_state=0)
networks = {}
for rate in (0,.3,.5):
    w1,b1,w2,b2 = namespace["train_drop"](mx,my,64,.5,2000,0,rate)
    networks[rate]=(np.maximum(0,hx@w1+b1)@w2+b2)>0
valid, final = train_test_split(np.arange(len(hy)),test_size=.5, stratify=hy,random_state=42)
scores = {rate:tuple(np.mean(pred[ix]==hy[ix]).round(4) for ix in [valid,final])
          for rate,pred in networks.items()}
print("dropout fixed train; validation, final", scores,
      "winner by validation",max(scores,key=lambda rate:scores[rate][0]))
