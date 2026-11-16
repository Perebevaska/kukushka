"""From any directory, run with pandas and scikit-learn 1.8 (versions in expert.md)."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

DATA = Path(__file__).resolve().parents[3] / "site/data"


def load(name, key):
    df = pd.read_csv(DATA / f"{name}.csv")
    assert not df.duplicated(key).any() and not df.duplicated().any()
    missing = df.isna().sum()
    print(name, len(df), "missing", missing[missing > 0].to_dict())
    return df


d = load("deliveries", "delivery_id")
d = d[d.actual_min.between(1, 299)].copy()
d["hour"] = pd.to_datetime(d.created).dt.hour
x = pd.get_dummies(d[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = d.actual_min > d.promised_min
a, b = train_test_split(x.index, test_size=.25, random_state=42)
lr = LogisticRegression(max_iter=2000).fit(x.loc[a], y[a])
p = lr.predict_proba(x.loc[b])[:, 1]
q = p >= .6
print("Delivery test: positive, n, rule correct, selected and late at .6", y[b].sum(), len(b),
      (y[b] == (d.loc[b, "courier"] == "пеший")).sum(), q.sum(), y[b][q].sum())
learn, validate = train_test_split(a, test_size=1/3, random_state=42)
m_valid = LogisticRegression(max_iter=2000).fit(x.loc[learn], y[learn])
pv = m_valid.predict_proba(x.loc[validate])[:, 1]
t_valid = next(t for t in np.arange(.1, .90, .05).round(2) if y[validate][pv >= t].mean() >= .8)
pt = m_valid.predict_proba(x.loc[b])[:, 1]
sel = pt >= t_valid
print("Independent 3-way threshold / valid and test precision, test alerts", t_valid,
      y[validate][pv >= t_valid].mean(), y[b][sel].mean(), sel.sum())
model = LinearRegression().fit(x.loc[a], d.actual_min[a])
pred = model.predict(x.loc[b])
print("MAE median, linear; R2 correct, R2 y reversed",
      np.abs(d.actual_min[b] - d.actual_min[a].median()).mean(), mean_absolute_error(d.actual_min[b], pred),
      r2_score(d.actual_min[b], pred), r2_score(d.actual_min[b][::-1], pred))
reg = RandomForestRegressor(n_estimators=100, random_state=0).fit(x.loc[a], d.actual_min[a])
pred_rf = reg.predict(x.loc[b])
print("Unrestricted forest MAE/RMSE/R2", mean_absolute_error(d.actual_min[b], pred_rf),
      mean_squared_error(d.actual_min[b], pred_rf)**.5, r2_score(d.actual_min[b], pred_rf))

o = load("guest_orders", "order_id")
print("orders dates, orders per guest", o.datetime.min(), o.datetime.max(), o.groupby('guest_id').size().agg(['min','max']).to_dict())
x = o[["weekday", "hour", "items", "amount", "distance_km"]]
kfold = KFold(5, shuffle=True, random_state=42)
for model in (RandomForestClassifier(n_estimators=50, random_state=0), LogisticRegression(max_iter=2000)):
    plain = cross_val_score(model, x, o.dessert, cv=kfold)
    grouped = cross_val_score(model, x, o.dessert, cv=GroupKFold(5), groups=o.guest_id)
    print("dessert", type(model).__name__, plain.mean(), grouped.mean())
a, b = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=4).split(x, groups=o.guest_id))
print("Group holdout guests, orders, overlap", o.guest_id[b].nunique(), len(b), len(set(o.guest_id[a]) & set(o.guest_id[b])))

g = load("guests_churn", "guest_id")
print("Churn labels and blocked by label", g.churned.value_counts().to_dict(), pd.crosstab(g.card_blocked, g.churned).to_dict())
assert g.avg_check.isna().equals(g.visits_90d == 0)
y = g.churned
a, b = train_test_split(g.index, test_size=.25, random_state=42, stratify=y)
feat = g.drop(columns=["guest_id", "card_blocked", "churned"]).fillna({"avg_check": 0})
x = pd.get_dummies(feat.loc[a], dtype=int)
test = pd.get_dummies(feat.loc[b], dtype=int).reindex(columns=x.columns, fill_value=0)
print("Accuracy baselines on test", (y[b] == 0).mean(), ((test.days_since_last > 45) == y[b]).mean())
models = {"RF": RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0),
          "LR": LogisticRegression(max_iter=2000)}
tree_scores = [cross_val_score(DecisionTreeClassifier(max_depth=i, random_state=0), x, y[a], cv=kfold).mean()
               for i in range(1, 11)]
depth = int(np.argmax(tree_scores)) + 1
print("Chosen depth", depth)
models["tree"] = DecisionTreeClassifier(max_depth=depth, random_state=0)
for name, model in models.items():
    acc, precision = [], []
    for tr, va in kfold.split(x):
        m = clone(model).fit(x.iloc[tr], y[a].iloc[tr])
        label = y[a].iloc[va]
        acc.append(m.score(x.iloc[va], label))
        risk = pd.Series(m.predict_proba(x.iloc[va])[:, 1], index=label.index)
        precision.append(label.loc[risk.nlargest(len(label)//10).index].mean())
    print("OOF mean accuracy and mean precision@10%", name, np.mean(acc), np.mean(precision))
m = models["RF"].fit(x, y[a])
risk = pd.Series(m.predict_proba(test)[:, 1], index=b)
top = risk.nlargest(60).index
rule = test.days_since_last
print("Test accuracy labels, capture, known and n by 45 days",
      m.score(test, y[b]), y[b].sum(), y[top].sum(), (rule[top] > 45).sum(), (rule > 45).sum())
by_days = rule.nlargest(60).index
print("At same budget (60) positives forest / recency", y[top].sum(), y[by_days].sum())
quiet = rule[rule <= 45]
k = len(quiet)//10
print("Quiet: n, positives, k, captured forest vs recency",
      len(quiet), y[quiet.index].sum(), k,
      y[risk.loc[quiet.index].nlargest(k).index].sum(), y[quiet.nlargest(k).index].sum())
num = ['tenure_months','app','visits_90d','days_since_last','avg_check','delivery_share','promo_used','complaints','card_blocked']
for cols in (num, num[:-1]):
    xx = g[cols].fillna(0)
    mt = DecisionTreeClassifier(max_depth=3, random_state=0).fit(xx.loc[a], y[a])
    print("Leak diagnostic; same test IDs; accuracy", cols[-1], mt.score(xx.loc[b], y[b]))
