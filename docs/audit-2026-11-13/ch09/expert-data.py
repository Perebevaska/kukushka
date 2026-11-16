"""Independent chapter 9 calculations. Run from any directory with sklearn 1.8, pandas and NumPy."""
from itertools import combinations
from pathlib import Path
import importlib.util
import random
import tempfile

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.tree import DecisionTreeRegressor

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site/data"
spec = importlib.util.spec_from_file_location("generator", ROOT / "tools/gen_data.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
with tempfile.TemporaryDirectory() as tmp:
    generator.OUT = Path(tmp)
    generator.gen_chapter4(random.Random(4004))
    generator.gen_chapter6(random.Random(6006))
    generator.gen_chapter9(random.Random(9009))
    for name in ("deliveries", "guests_churn", "family_members"):
        csv = f"{name}.csv"
        assert (generator.OUT / csv).read_bytes() == (DATA / csv).read_bytes(), name

d = pd.read_csv(DATA / "deliveries.csv")
g = pd.read_csv(DATA / "guests_churn.csv")
family = pd.read_csv(DATA / "family_members.csv")
for df in (d, g, family):
    assert df.iloc[:, 0].is_unique
    missing = df.isna().sum()
    print("rows, ID, missing", len(df), df.columns[0], missing[missing > 0].to_dict())

valid = d[d.actual_min.between(1,299)]
print("delivery dates, canceled, bad, valid", d.created.min(), d.created.max(), d.actual_min.isna().sum(),
      ((d.actual_min<=0) | (d.actual_min>=300)).sum(), len(valid))
x = valid[["distance_km", "items"]].assign(walk=valid.courier.eq("пеший").astype(int)).to_numpy()
y = valid.actual_min.to_numpy()
design = np.column_stack([np.ones(len(x)),x])
w = np.linalg.lstsq(design,y,rcond=None)[0]
p = design @ w
print("OLS weights, MAE, R2, maximum residual dot",w.round(4),mean_absolute_error(y,p),r2_score(y,p),np.max(np.abs(design.T @ (y-p))))
gram = x[:,:2].T @ x[:,:2]
print("Gram product, corr(km,items)",gram.round(2),np.corrcoef(x[:,:2].T)[0,1])
n = len(valid)
cv_results = []
for train,test in KFold(5).split(x):
    model = LinearRegression().fit(x[train],y[train])
    cv_results.append([mean_absolute_error(y[test],np.repeat(y[train].mean(),len(test))),
                       mean_absolute_error(y[test],model.predict(x[test]))])
print("fivefold mean baseline, OLS MAE",np.mean(cv_results,axis=0))
matrix = g[["visits_90d","days_since_last","tenure_months"]].to_numpy()
nearest = []
for features in (matrix, (matrix-matrix.mean(axis=0))/matrix.std(axis=0)):
    distances = np.linalg.norm(features-features[0],axis=1)
    distances[0] = np.inf
    nearest.append(np.argsort(distances,kind="stable")[:5])
print("guest 0 neighbors raw/scaled, overlap", *nearest, len(set(nearest[0]) & set(nearest[1])))
# Equal distances or zero vectors need an explicit tie and zero-norm policy.
u = np.array([5,3,2])
print("distance/cosine ten times sales", np.linalg.norm(10*u-u), np.dot(u,10*u)/np.linalg.norm(u)/np.linalg.norm(10*u))
km = np.array([8,8.1,8,8.1])
rain = np.array([False,False,True,True])
print("vector boundary payment", (60+14*km+100*(km>8))*np.where(rain,1.3,1))

rng = np.random.default_rng(1)
distances = rng.uniform(.5,12,100000).round(1)
wet = rng.random(100000)<.2
pay = (60+14*distances+100*(distances>8))*np.where(wet,1.3,1)
print("100k vector payments total RUB",round(pay.sum()))

cols = ["gender","age","income_k","family_size"]
x = family[cols].to_numpy()
y = family.spend_k.to_numpy()
print("profiles unique, identical spends, spend mean, features and target ranges",len(np.unique(x,axis=0)),
      family.duplicated(subset=cols+["spend_k"]).sum(),y.mean(),family[cols+["spend_k"]].agg(["min","max"]).to_dict())
a,b = train_test_split(np.arange(len(y)), test_size=.25,random_state=42)
key = np.random.default_rng(42).normal(size=(4,4))
z = x @ key
base = LinearRegression().fit(x[a], y[a])
hidden = LinearRegression().fit(z[a],y[a])
po,ph = base.predict(x[b]), hidden.predict(z[b])
print("project ranks, cond, heldout R2, MAE, max prediction and coef error", np.linalg.matrix_rank(key),
      np.linalg.matrix_rank(x[a]-x[a].mean(axis=0)), np.linalg.cond(key),r2_score(y[b],po),
      mean_absolute_error(y[b],po), np.abs(po-ph).max(),np.abs(np.linalg.solve(key,base.coef_)-hidden.coef_).max())
damaged = key.copy()
damaged[:,3] = damaged[:,0] + damaged[:,1]
print("rank-3 key test",LinearRegression().fit(x[a] @ damaged,y[a]).score(x[b] @ damaged,y[b]))
for depth in (3,5,8):
    print("tree depth, open / mixed R2",depth,*(DecisionTreeRegressor(max_depth=depth,random_state=0)
          .fit(mat[a],y[a]).score(mat[b],y[b]) for mat in (x,z)))
new = np.array([[1,34,95,3]])
print("new same/different key",base.predict(new)[0],hidden.predict(new @ key)[0],
      hidden.predict(new @ np.random.default_rng(43).normal(size=(4,4)))[0])
recovered = np.linalg.solve(x[:4], z[:4])
print("known-key reconstruction max error", np.abs(np.linalg.solve(recovered.T,z.T).T-x).max())

# Full-rank key preserves the set of linear predictors. Nonunique minimum-norm fits
# may choose different representatives, so predictions on points outside the train span can differ.
collinear = np.array([[0.,0.],[1.,1.],[2.,2.]])
target = np.array([0.,1.,2.])
new = np.array([[1.,0.]])
key2 = np.diag([2.,1.])
for transform in (np.eye(2),key2):
    model = LinearRegression().fit(collinear @ transform,target)
    print("rank-deficient train: R2, prediction at [1,0]",model.score(collinear @ transform,target),
          model.predict(new @ transform)[0])
design2 = np.array([[0.,0.],[1.,0.],[0.,1.],[1.,1.]])
projection = design2 @ np.diag([1.,0.])
print("rank loss: fixed targets x1, x2 R2",*[LinearRegression().fit(projection,column).score(projection,column)
                                             for column in design2.T])
# Forming X.T@X squares the spectral condition number.
near = np.array([[1.,1.],[1.,1.+1e-8],[1.,1.-1e-8]])
target = near @ np.array([1.,-1.])
print("ill-conditioned direct least squares",np.linalg.cond(near),np.linalg.lstsq(near,target,rcond=None)[0])
try:
    print("Gram solve result",np.linalg.solve(near.T @ near, near.T @ target))
except np.linalg.LinAlgError as err:
    print("Gram solve error",err)


def recover_discrete_fields(mixed):
    """Look only at released rows and the public domains {0,1} and {1,...,6}."""
    points = np.unique(mixed,axis=0)
    nn = NearestNeighbors(n_neighbors=12).fit(points)
    indices = nn.kneighbors(points,return_distance=False)[:,1:]
    differences = (points[indices]-points[:,None,:]).reshape(-1,4)
    differences *= np.where(differences[:,0]>0,1,-1)[:,None]
    # Select common directions; round solely to count equal floating-point differences.
    _, first, counts = np.unique(np.round(differences,5),axis=0,return_index=True,return_counts=True)
    frequent = differences[first[np.argsort(-counts)[:24]]]
    fields = {}
    for rows in combinations(frequent,3):
        directions = np.asarray(rows)
        if np.linalg.matrix_rank(directions,tol=1e-6)<3:
            continue
        normal = np.linalg.svd(directions)[2][-1]
        projected = mixed @ normal
        levels = np.unique(np.round(projected,3))
        if len(levels)==2 and np.min(np.abs(levels))<0.001:
            fields[2] = (np.abs(projected)>.001).astype(int)
        elif len(levels)==6:
            levels = np.sort(np.abs(levels))
            if levels[0]>0 and np.allclose(levels/levels[0],np.arange(1,7),atol=.02):
                fields[6] = np.rint(np.abs(projected)/levels[0]).astype(int)
        if len(fields)==2:
            return fields
    return fields


for seed in (42,43,44,45):
    # The recovery function receives no key, seed, IDs or known original rows.
    recovered_fields = recover_discrete_fields(x @ np.random.default_rng(seed).normal(size=(4,4)))
    print("blind recovery seed for validation, gender and family hits",seed,
          {k: int((v == x[:,{2:0,6:3}[k]]).sum()) for k,v in recovered_fields.items()})
    if seed==42:
        assert np.array_equal(recovered_fields[2],x[:,0]) and np.array_equal(recovered_fields[6],x[:,3])
