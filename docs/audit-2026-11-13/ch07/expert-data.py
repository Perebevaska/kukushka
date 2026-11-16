"""Reproduce chapter 7 calculations with CPython, scikit-learn 1.8 and pandas."""
import hashlib
import importlib.util
import random
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site/data"


def load_module(filename):
    spec = importlib.util.spec_from_file_location(filename, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


with tempfile.TemporaryDirectory() as folder:
    generator = load_module("gen_data.py")
    generator.OUT = Path(folder)
    generator.gen_chapter6(random.Random(6006))
    generator.gen_chapter7(random.Random(7007))
    tiers_generator = load_module("gen_ch07_tiers.py")
    tiers_generator.DATA = generator.OUT
    tiers_generator.main()
    for name in ("guests_churn", "guest_tiers", "catering_leads"):
        original = (DATA / f"{name}.csv").read_bytes()
        assert (generator.OUT / f"{name}.csv").read_bytes() == original
        print(name, hashlib.sha256(original).hexdigest()[:12])

g = pd.read_csv(DATA / "guests_churn.csv")
tiers = pd.read_csv(DATA / "guest_tiers.csv")
leads = pd.read_csv(DATA / "catering_leads.csv")
for df, key in [(g, "guest_id"), (tiers, "guest_id"), (leads, "lead_id")]:
    assert df[key].is_unique
    na = df.isna().sum()
    print(key, len(df), "missing", na[na > 0].to_dict())
assert g.guest_id.equals(tiers.guest_id)
assert g.avg_check.isna().equals(g.visits_90d.eq(0))
assert leads.contract_rub.notna().equals(leads.converted.eq(1))
print("churn, tiers", g.churned.sum(), tiers.card_tier.value_counts().to_dict())
print("leads coverage, positives", leads.created.min(), leads.created.max(), leads.converted.sum())
print("conversion conditional on missing", {col: leads.groupby(leads[col].isna()).converted.mean().round(3).to_dict()
                                           for col in ("budget_pp", "company_size")})

def split_idx(y):
    return train_test_split(y.index, test_size=0.25, stratify=y, random_state=42)


y = g.churned
tr, te = split_idx(y)
x = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
rf = RandomForestClassifier(n_estimators=100, random_state=0)
p = rf.fit(x.loc[tr], y.loc[tr]).predict_proba(x.loc[te])[:, 1]
print("RF CM, AUC, ties at 100th", confusion_matrix(y[te], p >= .5).tolist(), roc_auc_score(y[te], p),
      np.sort(p)[-100], (p >= np.sort(p)[-100]).sum())
for label, model in (
    ("forest-50", RandomForestClassifier(n_estimators=50, random_state=0)),
    ("balanced LR", LogisticRegression(class_weight="balanced", max_iter=2000)),
    ("raw kNN", KNeighborsClassifier(n_neighbors=15)),
    ("scaled kNN", make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=15))),
    ("L1", make_pipeline(StandardScaler(), LogisticRegression(C=.01, solver="liblinear", l1_ratio=1))),
):
    model.fit(x.loc[tr], y[tr])
    pred = model.predict(x.loc[te])
    scores = model.predict_proba(x.loc[te])[:, 1]
    print(label, "CM / F1 / AUC", confusion_matrix(y[te], pred).tolist(),
          round(f1_score(y[te], pred), 4), round(roc_auc_score(y[te], scores), 4))
    if label == "L1":
        print("L1 selection", x.columns[(model[-1].coef_ != 0).ravel()].tolist())
fit, val = train_test_split(tr, test_size=.25, random_state=0, stratify=y[tr])
rf.fit(x.loc[fit], y[fit])
grid = np.arange(.05, 1, .05).round(2)

def values(index, benefit):
    score = rf.predict_proba(x.loc[index])[:, 1]
    return np.array([benefit * y[index][score >= t].sum() - 200 * (score >= t).sum() for t in grid])

for benefit in (1000, 400):
    v = values(val, benefit)
    idx = v.argmax()
    print("benefit, t_val, val/test value, test .5", benefit, grid[idx], v[idx], values(te, benefit)[idx],
          values(te, benefit)[grid == .5][0])

kf = KFold(n_splits=5, shuffle=True, random_state=42)
extended = x.assign(is_new=g.tenure_months.le(3).astype(int),
                    compl_x_deliv=g.complaints * g.delivery_share, log_days=np.log1p(g.days_since_last))
for features in (x, extended):
    for prefit in (True, False):
        data = features.loc[tr].to_numpy()
        if prefit:
            data = StandardScaler().fit_transform(data)
        cms, f1, auc = [], [], []
        for a, b in kf.split(data):
            model = LogisticRegression(max_iter=2000)
            if not prefit:
                model = make_pipeline(StandardScaler(), model)
            model.fit(data[a], y[tr[a]])
            pred = model.predict(data[b])
            cms.append(confusion_matrix(y[tr[b]], pred))
            f1.append(f1_score(y[tr[b]], pred))
            auc.append(roc_auc_score(y[tr[b]], model.predict_proba(data[b])[:, 1]))
        print("churn cols, prefit, OOF CM, fold mean F1, AUC", data.shape[1], prefit,
              np.sum(cms, axis=0).tolist(), round(np.mean(f1), 6), round(np.mean(auc), 6))

# Same group-mean algorithm as RateBy. Unique keys isolate own-label information.
labels = np.tile([0, 1], 25)
keys = pd.Series([f"item-{i}" for i in range(len(labels))], name="key")
rates = pd.Series(labels).groupby(keys).mean()
encoder = TargetEncoder(smooth=0.0, target_type="binary", cv=5, shuffle=True, random_state=42)
fold_rates = encoder.fit_transform(keys.to_frame(), labels).ravel()
print("singleton encodings: plain train AUC / cross-fitted train AUC, unseen default",
      roc_auc_score(labels, keys.map(rates)), roc_auc_score(labels, fold_rates), labels.mean())

time = pd.to_datetime(leads.created)
y = leads.converted
raw = leads.drop(columns=["lead_id", "created", "converted", "contract_rub"]).assign(
    hour=time.dt.hour, weekday=time.dt.dayofweek, evening=(time.dt.hour >= 19).astype(int))
cats = ["channel", "event_type", "city", "company_size", "manager"]
nums = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting", "hour", "weekday", "evening"]

def estimator(c=1, weight=None, columns=nums):
    mapping = ColumnTransformer([
        ("number", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), columns),
        ("category", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                                   OneHotEncoder(handle_unknown="ignore")), cats),
    ])
    return make_pipeline(mapping, LogisticRegression(C=c, class_weight=weight, max_iter=2000))


def hits(target, p, k):
    idx = np.argsort(-p, kind="stable")[:k]
    return int(np.asarray(target)[idx].sum())


tr, te = split_idx(y)
print("project baselines", len(tr), len(te), y[tr].sum(), y[te].sum())
now = estimator(columns=[col for col in nums if col != "response_hours"]).fit(raw.iloc[tr], y[tr])
print("without response hours, deals among 225", hits(y[te], now.predict_proba(raw.iloc[te])[:, 1], 225))
for label, train, test in (("course", tr, te), ("chronological", np.arange(2250), np.arange(2250, 3000))):
    yy = y[test]
    score = estimator().fit(raw.iloc[train], y[train]).predict_proba(raw.iloc[test])[:, 1]
    rule = raw.iloc[test].repeat_client.eq(1) | raw.iloc[test].channel.eq("рекомендация")
    k = int(rule.sum())
    rounded_k = int(round(rule.mean(), 3) * len(yy))
    alternative = estimator(weight="balanced").fit(raw.iloc[train], y[train]).predict_proba(raw.iloc[test])[:, 1]
    print(label, "test AUC, hits/positives top225, rule k/hits, equal-k model hits, rounded k, overlap with weighted",
          round(roc_auc_score(yy, score), 5), hits(yy, score, 225), yy.sum(), k, yy[rule].sum(),
          (hits(yy, score, k), hits(yy, score, rounded_k)), rounded_k, len(set(np.argsort(-score)[:225]) & set(np.argsort(-alternative)[:225])))
for c in (.01, .1, 1, 10):
    for weight in (None, "balanced"):
        auc, recall, positives_in_top = [], [], []
        for train, test in kf.split(tr):
            a, b = tr[train], tr[test]
            p = estimator(c, weight).fit(raw.iloc[a], y[a]).predict_proba(raw.iloc[b])[:, 1]
            count = hits(y[b], p, int(.3 * len(b)))
            auc.append(roc_auc_score(y[b], p))
            recall.append(count / y[b].sum())
            positives_in_top.append(count)
        print("grid C, weight, mean AUC / recall@30, top positives", c, weight,
              round(np.mean(auc), 6), round(np.mean(recall), 6), positives_in_top)
