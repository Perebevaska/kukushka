"""Recalculate using delivered CSV and independent formulas. Run with numpy, pandas and scipy."""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parents[3] / "site/data"


def load(name, key):
    df = pd.read_csv(DATA / f"{name}.csv")
    assert not df.duplicated().any() and not df.duplicated(key).any()
    missing = df.isna().sum()
    print(name, len(df), "nulls", missing[missing > 0].to_dict())
    return df


def compare(ab, outcome):
    a, b = [ab.loc[ab.group == group, outcome].dropna().astype(float) for group in "AB"]
    diff = b.mean() - a.mean()
    se = math.sqrt(a.var() / len(a) + b.var() / len(b))
    print(outcome, "n A/B", len(a), len(b), "means", a.mean(), b.mean(),
          "diff/CI", diff, diff - 1.96 * se, diff + 1.96 * se)
    if set(ab[outcome].dropna()) <= {0, 1}:
        pooled = (a.sum() + b.sum()) / (len(a) + len(b))
        z = diff / math.sqrt(pooled * (1 - pooled) * (1 / len(a) + 1 / len(b)))
        print("pooled z, p", z, 2 * stats.norm.sf(abs(z)))


d = load("deliveries", "delivery_id")
ok = d[d.actual_min.between(1, 299)].copy()
ok["late"] = ok.actual_min > ok.promised_min
print("late n and snow contingency", len(ok), ok.late.sum(), pd.crosstab(ok.weather, ok.late).to_dict())
g = load("guests_churn", "guest_id")
print("guest profiles avg_check missing == zero visits", (g.avg_check.isna() == (g.visits_90d == 0)).all())
print("churn overall, app=1 and app=0", g.churned.mean(), g.groupby('app').churned.mean().to_dict())
arr = load("arrivals", ["shop_id", "date", "slot"])
ufa = arr[arr.shop_id == "UFA-1"]
model = stats.poisson.sf(3, ufa.guests.mean())
print("UFA intervals", len(ufa), ufa.guests.mean(), ufa.guests.var() / ufa.guests.mean(), ">=4 count, days",
      (ufa.guests >= 4).sum(), (ufa.assign(high=ufa.guests >= 4).groupby('date').high.sum() > 0).sum(),
      "model >=4 in at least one slot per day", 1 - (1 - model) ** 24)
push = load("ab_push", "user_id")
compare(push, "ordered")
compare(push, "revenue")
p = load("ab_promise", "session_id")
o = p[p.ordered == 1].copy()
near = p[p.distance_km < 2]
for group, sub in p.groupby("group"):
    orders = sub[sub.ordered == 1]
    print(group, "sessions, orders, late, ratings", len(sub), len(orders), int(orders.late.sum()), orders.rating.notna().sum())
compare(p, "ordered")
compare(near, "ordered")
compare(o, "late")
compare(p.assign(late_session=p.late.fillna(0)), "late_session")
compare(o, "actual_min")
compare(p, "amount")
compare(o, "rating")
print("SRM", stats.chisquare(p.group.value_counts()).pvalue)
for group, sub in o[o.distance_km < 2].groupby('group'):
    print("near group", group, "orders", len(sub), "share actual>30", (sub.actual_min > 30).mean(),
          "mean actual", sub.actual_min.mean(), "share late", sub.late.mean())
f = p[p.distance_km >= 2].copy()
f.loc[f.group == "B", "promise_min"] = f.loc[f.group == "B", "promise_min"].map({45: 60, 60: 45})
print("far: wrong promises in B yet sets equal", (f.group == "B").sum(),
      set(f.loc[f.group == "A", "promise_min"]) == set(f.loc[f.group == "B", "promise_min"]))

rng = np.random.default_rng(505)
n_trials = 200000
z1 = rng.normal(size=n_trials)
z_final = math.sqrt(3 / 7) * z1 + math.sqrt(4 / 7) * rng.normal(size=n_trials)
unsafe = (z1 > 1.96) | ((abs(z1) <= 1.96) & (z_final > 1.96))
print("at true revenue diff=-10, rollout false positive: one look, two looks", (z1 > 1.96).mean(), unsafe.mean())
print("n per arm, half-width 10; power 80%, true diff 0; SD 350 per arm",
      *(math.ceil(2 * 350**2 * z**2 / 10**2) for z in [1.96, 1.96 + stats.norm.ppf(.8)]))
a, b = np.array([0] * 90 + [10] * 10), np.ones(100)
print("same means, different distributions", a.mean(), b.mean(), stats.mannwhitneyu(a, b).pvalue)
x = np.arange(12)
y = np.arange(100, 112)
rng = np.random.default_rng(0)
observed = abs(x.mean() - y.mean())
extreme = 0
for _ in range(2000):
    perm = rng.permutation(np.r_[x, y])
    extreme += abs(perm[:12].mean() - perm[12:].mean()) >= observed
print("2000 permutations extremes, naive p, corrected MC p, exact two-sided p",
      extreme, extreme / 2000, (extreme + 1) / 2001, 2 / math.comb(24, 12))
