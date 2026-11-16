"""Executed by expert-run.mjs inside the bundled Pyodide."""
import json
import sys

import numpy as np
import pandas as pd
import scipy
import statsmodels
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest


def metric(df, column, binary=False):
    samples = [x[column].dropna().to_numpy() for _, x in df.groupby("group", sort=True)]
    a, b = samples
    change = b.mean() - a.mean()
    if binary:
        se = np.sqrt(sum(x.mean() * (1 - x.mean()) / len(x) for x in samples))
        p = proportions_ztest([x.sum() for x in samples], [len(x) for x in samples])[1]
    else:
        se = np.sqrt(sum(x.var(ddof=1) / len(x) for x in samples))
        p = stats.ttest_ind(b, a, equal_var=False).pvalue
    return dict(n=[len(x) for x in samples], mean=[x.mean() for x in samples],
                diff=change, ci=[change - 1.96 * se, change + 1.96 * se], p=p)


frames = {key: pd.read_csv(key + ".csv") for key in
          ["deliveries", "guests_churn", "arrivals", "ab_push", "ab_promise"]}
keys = {"deliveries":["delivery_id"], "guests_churn":["guest_id"],
        "arrivals":["shop_id","date","slot"], "ab_push":["user_id"], "ab_promise":["session_id"]}
profiles = {k:dict(n=len(d),key=keys[k],duplicate_keys=int(d.duplicated(keys[k]).sum()),
                   na=d.isna().sum().to_dict()) for k,d in frames.items()}
d = frames["deliveries"]
v = d[d.actual_min.between(1,299)].copy()
v["late"] = v.actual_min > v.promised_min
v["month"] = pd.to_datetime(v.created).dt.month
t = v[v.shop_id == "KZN-2"].actual_min
delivery = dict(raw_date=[d.created.min(),d.created.max()],valid=len(v),late=int(v.late.sum()),
                walk=pd.crosstab(v.courier.eq("пеший"),v.late).values.tolist(),
                weather=v.groupby("weather").late.agg(["size","mean"]).to_dict(),
                shop_ci=stats.t.interval(0.95,len(t)-1,loc=t.mean(),scale=t.sem()),
                paired=v.pivot_table(index="shop_id",columns="month",values="late",aggfunc="mean").to_dict())
g=frames["guests_churn"].visits_90d
arr=frames["arrivals"]
push=frames["ab_push"]
promise=frames["ab_promise"]
orders=promise[promise.ordered.eq(1)]
rating=orders.dropna(subset=["rating"])
urban={k:metric(s,"late",True) for k,s in orders.groupby("city")}
for (city,val),p in zip(urban.items(),multipletests([v["p"] for v in urban.values()],method="holm")[1]):
    val["p_holm"]=p
def srm(df):
    return stats.chisquare(df.groupby("group").size()).pvalue
def power(p_b,n):
    return NormalIndPower().solve_power(proportion_effectsize(p_b,.09),nobs1=n,alpha=.05)
a, b = [x.revenue.to_numpy() for _, x in push.groupby("group")]
bootstrap_intervals = {}
for seed in (0, 1):
    rng = np.random.default_rng(seed)
    differences = [rng.choice(b, len(b)).mean() - rng.choice(a, len(a)).mean() for _ in range(3000)]
    bootstrap_intervals[seed] = np.percentile(differences, [2.5, 97.5]).tolist()
aa=[1]*9+[91]
bb=[10]*10
expected_promise = np.where(promise.distance_km < 2, np.where(promise.group.eq("B"),40,30),
                            np.where(promise.distance_km < 5,45,60))
metrics=dict(
    versions=dict(python=sys.version.split()[0],numpy=np.__version__,pandas=pd.__version__,
                  scipy=scipy.__version__,statsmodels=statsmodels.__version__),
    profiles=profiles, deliveries=delivery,
    visits=dict(mean=g.mean(),weighted=np.average(g,weights=g)),
    arrivals=dict(date=[arr.date.min(),arr.date.max()],means=arr.groupby("shop_id").guests.mean().to_dict()),
    push=dict(bootstrap_intervals=bootstrap_intervals,srm=srm(push),conversion=metric(push,"ordered",True),revenue=metric(push,"revenue"),
              buyers=metric(push[push.ordered==1],"revenue"),sample_80=NormalIndPower().solve_power(
              proportion_effectsize(.11,.09),power=.8,alpha=.05),
              power_at_just_below_mde=power(.10999,3524),power_for_actual_n=power(.11,3000)),
    equal_means_example=dict(a=aa,b=bb,means=[np.mean(aa),np.mean(bb)],
        welch=stats.ttest_ind(aa,bb,equal_var=False).pvalue,rank=stats.mannwhitneyu(aa,bb).pvalue),
    promise=dict(dates=[promise.ts.min(),promise.ts.max()],srm=srm(promise),
        wrong_promise=int((expected_promise!=promise.promise_min).sum()),
        amount_nonorder_nonzero=int((promise.loc[promise.ordered==0,"amount"]!=0).sum()),
        late_mismatch=int((orders.actual_min.gt(orders.promise_min)!=orders.late).sum()),
        late=metric(orders,"late",True),conv=metric(promise,"ordered",True),
        near=metric(promise[promise.distance_km<2],"ordered",True),
        far=metric(promise[promise.distance_km>=2],"ordered",True),
        rating=rating.groupby("group").rating.agg(["mean","size"]).to_dict(),
        rating_rank_p=stats.mannwhitneyu(*(x.rating for _,x in rating.groupby("group"))).pvalue,
        revenue=metric(promise,"amount"),by_city=urban))
json.dumps(metrics,default=lambda obj:obj.item(),ensure_ascii=False)
