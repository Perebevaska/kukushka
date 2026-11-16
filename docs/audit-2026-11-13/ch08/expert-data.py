"""Run from any directory with NumPy, pandas and sklearn 1.8. All regenerated files are temporary."""
import importlib.util
import random
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "site/data"
NUM = ["orders_n", "orders_per_week", "recency_days", "avg_check", "delivery_share", "morning_share",
       "shops_n", "tenure_days", "coffee_share", "app_sessions", "complaints_n"]
CAT = ["source", "city"]


def load_generator(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def database_tables(path):
    with sqlite3.connect(path) as con:
        names = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        return {name: pd.read_sql_query(f'select * from "{name}"', con) for name in names}


db = database_tables(DATA / "final1.db")
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    generator = load_generator("gen_data")
    generator.OUT = out
    generator.gen_chapter6(random.Random(6006))
    generator.gen_chapter7(random.Random(7007))
    generator.gen_chapter8(random.Random(8033))
    extra = load_generator("gen_ch08_extra")
    extra.OUT = out
    extra.main()
    for f in out.glob("*.csv"):
        assert f.read_bytes() == (DATA / f.name).read_bytes(), f.name
    final = load_generator("gen_final1")
    final.OUT = out / "final1.db"
    final.main()
    rebuilt = database_tables(final.OUT)
    assert rebuilt.keys() == db.keys()
    for name in db:
        pd.testing.assert_frame_equal(db[name], rebuilt[name])
print("DB regenerated", {k: len(v) for k, v in db.items()})
for name, keys in {"guests": ["guest_id"], "orders": ["order_id"], "order_items": ["order_id", "item_id", "price"],
                   "app_sessions": ["guest_id", "month"], "complaints": ["complaint_id"], "pilot": ["guest_id"],
                   "shops": ["shop_id"], "menu": ["item_id"]}.items():
    assert not db[name].duplicated(keys).any(), name
    missing = db[name].isna().sum()
    print(name, "missing", missing[missing > 0].to_dict())
subscriber_orders = db["orders"].query("payment == 'абонемент'").copy()
daily = subscriber_orders.groupby(["guest_id", subscriber_orders.ordered_at.str[:10]]).size()
print("days with repeated redemptions / extra redemptions / daily max",
      (daily > 1).sum(), (daily - 1).clip(lower=0).sum(), daily.max())
print("item ID repeats within order with different prices", db["order_items"].duplicated(["order_id","item_id"]).sum())
comp = db["complaints"].merge(db["guests"], on="guest_id", validate="many_to_one")
print("complaints before registration, of which before cutoff",
      (comp.created_at < comp.reg_date).sum(), ((comp.created_at < comp.reg_date) & (comp.created_at < "2026-07-01")).sum())

f = pd.read_csv(DATA / "shop_funnel.csv")
assert not f.duplicated(["month", "shop_id"]).any()
months = f.groupby("month")[["visitors", "checks", "revenue"]].sum()
fac = months.assign(conv=months.checks / months.visitors, avg=months.revenue / months.checks)
a, b = fac.loc["2026-08"], fac.loc["2026-09"]
parts = [(b.visitors-a.visitors)*a.conv*a.avg, b.visitors*(b.conv-a.conv)*a.avg,
         b.visitors*b.conv*(b.avg-a.avg)]
print("network revenue delta, chain components RUB", b.revenue-a.revenue, np.rint(parts).astype(int))

b = pd.read_csv(DATA / "bonus_pilot.csv")
z = b.groupby("group").churned.agg(["mean", "sum", "size"])
delta = z.loc["контроль", "mean"] - z.loc["бонус", "mean"]
se = np.sqrt((z["mean"] * (1-z["mean"]) / z["size"]).sum())
print("bonus", z.to_dict("index"), "pnl n=3000 with 90% Wald", (3000 * (2400 * (delta + np.array([-1.645, 0, 1.645]) * se) - 200)).round())

g = pd.read_csv(DATA / "guests_churn.csv").merge(pd.read_csv(DATA / "guests_age.csv"), validate="one_to_one")
x = pd.get_dummies(g.drop(columns=["guest_id", "card_blocked", "churned", "age_group"]), dtype=int).fillna(0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)
pr = cross_val_predict(forest, x, g.churned, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")[:, 1]
for age, group in g.assign(p=pr).groupby("age_group"):
    print("age n/churn/recall", age, len(group), group.churned.sum(), round(recall_score(group.churned, group.p > 1/3), 4))

# Risk-based bonus and gains for a fixed budget.
a, b = train_test_split(g.index, test_size=.25, stratify=g.churned, random_state=42)
forest.fit(x.loc[a], g.churned[a])
p = forest.predict_proba(x.loc[b])[:,1]
scores = pd.Series(p, index=b)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(x.loc[a], g.churned[a])
lp = logit[-1].intercept_[0] + np.dot(logit[0].transform(x.loc[[1605]])[0],logit[-1].coef_[0])
print("guest row1605 sigmoid of contributions / predict_proba",1/(1+np.exp(-lp)),
      logit.predict_proba(x.loc[[1605]])[0,1])
top = scores.nlargest(100).index
selected = scores > 1/3
print("at 100 caught, recall, expected net; at 1/3 sent and expected net",
      g.churned[top].sum(), round(g.churned[top].sum() / g.churned[b].sum(),3),
      g.churned[top].sum()*600 - 200*len(top), selected.sum(),
      g.churned[selected.index[selected]].sum()*600 - 200*selected.sum())
print("binomial realized below 20of120 at .25", (np.random.default_rng(1).binomial(120,.25,10000)<20).mean())

# Unit drift and segment support for the deployed catering model.
leads = pd.read_csv(DATA / "catering_leads.csv")
months = pd.to_datetime(leads.created).dt.month
num = ["guests","budget_pp","days_to_event","response_hours","repeat_client","tasting"]
cat = ["channel","event_type","city","company_size","manager"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
                         ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                                               OneHotEncoder(handle_unknown="ignore")), cat)])
catering = make_pipeline(pre, LogisticRegression(max_iter=1000)).fit(leads[months<=4], leads.converted[months<=4])
live = leads[months>=5].copy()
live["p"] = catering.predict_proba(live)[:,1]
sep = live[months.loc[live.index]==9].copy()
sep["response_hours"] = 60*sep.response_hours
broken = catering.predict_proba(sep)[:,1]
print("September clean and broken mean prob/AUC", sep.p.mean(), roc_auc_score(sep.converted,sep.p),
      broken.mean(), roc_auc_score(sep.converted,broken))
soc = live[live.channel.eq("соцсети")]
print("social n, buyers, AUC, mean p",len(soc),soc.converted.sum(),roc_auc_score(soc.converted,soc.p),soc.p.mean())

sites = pd.read_csv(DATA / "sites.csv")
for city, s in sites.groupby("city"):
    x = pd.get_dummies(s[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    x.traffic = np.log(x.traffic)
    tr, te = train_test_split(s.index, test_size=.25, random_state=42)
    y = s.profit_k
    p = LinearRegression().fit(x.loc[tr], y[tr]).predict(x.loc[te])
    fact = y[te].to_numpy()
    draws = np.random.default_rng(0).integers(0, len(te), size=(1000, 300))
    ranks = np.argsort(-p[draws], axis=1)[:, :40]
    selected = np.take_along_axis(draws, ranks, axis=1)
    margin = fact[selected].sum(axis=1) - 40*140
    print("city mean/quantiles/loss/duplicates/real top40", city, round(margin.mean()), np.percentile(margin, [2.5,97.5]),
          (margin < 0).mean(), round(np.mean([40-len(np.unique(row)) for row in selected]), 2),
          fact[np.argsort(-p)[:40]].sum() - 40*140)


def features(cutoff):
    cutoff = pd.Timestamp(cutoff)
    guest = db["guests"].merge(db["shops"][["shop_id","city"]], left_on="home_shop_id", right_on="shop_id").set_index("guest_id")
    order = db["orders"].copy()
    order["time"] = pd.to_datetime(order.ordered_at)
    start = cutoff - pd.DateOffset(months=4)
    order = order[(order.time >= start) & (order.time < cutoff)].copy()
    order["morning"] = (order.time.dt.hour < 10) & (order.time.dt.dayofweek < 5)
    order["delivery"] = order.channel.eq("доставка")
    by_guest = order.groupby("guest_id")
    feats = by_guest.agg(orders_n=("order_id", "size"), avg_check=("amount","mean"),
                         delivery_share=("delivery","mean"), morning_share=("morning","mean"),
                         shops_n=("shop_id","nunique"), last=("time","max"))
    feats["recency_days"] = (cutoff - feats.pop("last")).dt.total_seconds() / 86400
    lines = order[["guest_id","order_id"]].merge(db["order_items"], on="order_id").merge(db["menu"], on="item_id")
    feats["coffee_share"] = lines.category.eq("кофе").groupby(lines.guest_id).mean()
    sessions = db["app_sessions"]
    resp = sessions[(sessions.month >= start.strftime("%Y-%m")) & (sessions.month < cutoff.strftime("%Y-%m"))]
    complaint_time = pd.to_datetime(db["complaints"].created_at)
    complaints = db["complaints"][(complaint_time >= start) & (complaint_time < cutoff)]
    result = guest.join(feats).join(resp.groupby("guest_id").sessions.sum().rename("app_sessions")).join(
        complaints.groupby("guest_id").size().rename("complaints_n"))
    for col in ("orders_n","app_sessions","complaints_n"):
        result[col] = result[col].fillna(0)
    result["tenure_days"] = (cutoff-pd.to_datetime(result.reg_date)).dt.days
    result["orders_per_week"] = result.orders_n / (result.tenure_days.clip(upper=122)/7)
    return result


def classifier():
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return make_pipeline(pre, LogisticRegression(max_iter=1000))


features_july = features("2026-07-01")
pilot = db["pilot"].set_index("guest_id").join(features_july)
offer = pilot[pilot.group_name.eq("предложение")]
ctrl = pilot[pilot.group_name.eq("контроль")]
rest = features_july[~features_july.index.isin(pilot.index) & (features_july.orders_n > 0)]
tr, te = train_test_split(offer.index, stratify=offer.bought, test_size=.25, random_state=42)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof = cross_val_predict(classifier(), offer.loc[tr], offer.bought[tr], cv=cv, method="predict_proba")[:, 1]
on_train = classifier().fit(offer.loc[tr], offer.bought[tr])
control_risk = on_train.predict_proba(ctrl)[:, 1]
grid = np.arange(.02,.41,.02).round(2)
rows = []
for t in grid:
    send = oof > t
    org = ctrl.bought[control_risk > t].mean()
    buyers = offer.bought[tr][send].sum()
    gross = 1600 * buyers - 150 * send.sum()
    rows.append([t, send.sum(), buyers, org, gross, gross - 1600 * org * send.sum()])
curve = pd.DataFrame(rows,columns=["t","sent","bought","org","gross","net"])
print("OOF grid top", curve.sort_values("net", ascending=False).head(5).round(3).to_dict("records"))
t = curve.loc[curve.net.idxmax(), "t"]
test_p = on_train.predict_proba(offer.loc[te])[:, 1]
print("held-out offer AUC, sent/buyers", roc_auc_score(offer.bought[te], test_p), (test_p > t).sum(), offer.bought[te][test_p > t].sum())
# Pre-specified synthetic policies, with equal send cost but differing organic purchase rates.
for name, sent, purchases, organic in [("broad",100,30,.20),("narrow",50,20,.04)]:
    print("toy gross/incremental",name,1600*purchases-150*sent,
          1600*(purchases-organic*sent)-150*sent)
# Compare one out-of-sample control split without reusing outcomes for the final decision.
# This is an illustrative retrospective sensitivity analysis using the originally fixed course features.
ct_tr, ct_te = train_test_split(ctrl.index, test_size=.5, stratify=ctrl.bought, random_state=17)
policy_values = []
for threshold in grid:
    s = oof > threshold
    rate = ctrl.loc[ct_tr].loc[on_train.predict_proba(ctrl.loc[ct_tr])[:,1] > threshold, "bought"].mean()
    policy_values.append(1600*(offer.bought[tr][s].sum()-s.sum()*rate)-150*s.sum())
t_split = grid[np.nanargmax(policy_values)]
ct_hold = ctrl.loc[ct_te].loc[on_train.predict_proba(ctrl.loc[ct_te])[:,1] > t_split]
ot_hold = offer.loc[te].loc[test_p > t_split]
print("separate control/offer holdout, chosen t, test offered selected/buyers, ctrl selected/buyers, net per sent",
      t_split,len(ot_hold),ot_hold.bought.sum(),len(ct_hold),ct_hold.bought.sum(),
      1600*(ot_hold.bought.mean()-ct_hold.bought.mean()) - 150)
full = classifier().fit(offer, offer.bought)
selected_ctrl = ctrl[full.predict_proba(ctrl)[:, 1] > t]
p = full.predict_proba(rest)[:,1]
send = p > t
ns = send.sum()
expected = p[send].sum()
gross = 1600 * expected - 150 * ns
org = selected_ctrl.bought.mean()
print("control purchases/size; candidates, sent, expected, gross/reference/3100-base/offer all",
      selected_ctrl.bought.sum(),len(selected_ctrl),len(rest),ns,round(expected,2),
      *np.rint([gross,gross - 1600 * org * ns,gross - 3100 * org * ns,
                1600 * (p.sum() - ctrl.bought.mean()*len(rest)) - 150 * len(rest)]).astype(int))
wilson = binomtest(int(selected_ctrl.bought.sum()),len(selected_ctrl)).proportion_ci(method="wilson")
print("95% Wilson partial control-only bounds RUB",
      np.rint([gross - 1600 * ns * wilson.high,gross - 1600 * ns * wilson.low]).astype(int))
new = rest.reg_date >= "2026-06-01"
print("June registrations within rest and selected", new.sum(), (new & send).sum())
# Shift the four-month feature window by one month, holding the fitted model fixed.
aug = features("2026-08-01")
cand_aug = aug[~aug.index.isin(pilot.index) & (aug.orders_n > 0)]
asof_aug = cand_aug.index[full.predict_proba(cand_aug)[:, 1] > t]
print("next snapshot, n candidates/sent/overlap with July",len(cand_aug),len(asof_aug),len(asof_aug.intersection(rest.index[send])))
