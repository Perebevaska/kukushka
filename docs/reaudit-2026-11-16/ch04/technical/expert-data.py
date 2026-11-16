"""Run against shipped CSVs. An optional chapter task export adds the coverage inventory."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET

import matplotlib
import numpy as np
import pandas as pd

from transfer_data import make_extract

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "site/data"
print("CPython", sys.version.split()[0], "pandas", pd.__version__, "NumPy", np.__version__, "Matplotlib", matplotlib.__version__)


def read(name, key, when=None):
    path = DATA / f"{name}.csv"
    t = pd.read_csv(path)
    assert not t.duplicated().any()
    if key:
        assert t[key].is_unique and t[key].notna().all()
    print(name, "rows", len(t), "missing", t.isna().sum()[lambda s: s > 0].to_dict(),
          "period", (t[when].min(), t[when].max()) if when else "справочник",
          "sha256", hashlib.sha256(path.read_bytes()).hexdigest())
    return t


sales = read("orders_3m", "order_id", "datetime")
raw = read("deliveries", "delivery_id", "created")
orders = read("preorders", "order_id", "date")
guests = read("preorder_guests", "guest_id")
events = read("app_funnel", None, "ts")
print("sale by size", sales.groupby("size").amount.agg(["size", "sum"]).to_dict())
day_sales = sales.groupby(sales.datetime.str[:10]).amount.sum()
before = day_sales.loc["2026-10-11":"2026-10-31"].mean()
after = day_sales.loc["2026-11-01":"2026-11-21"].mean()
print("before/after daily ₽", before, after, "uplift %", (after / before - 1) * 100)

ok = raw[raw.actual_min.between(1, 299)].copy()
ok["delay"] = ok.actual_min - ok.promised_min
ok["late"] = ok.delay > 0
excluded = raw.actual_min.dropna()[lambda s: ~s.between(1, 299)]
print("excluded times", sorted(excluded.tolist()), "quantiles", ok.actual_min.quantile([.25, .5, .75, .9]).to_dict(),
      "late", int(ok.late.sum()), "missing-status bounds (%)", 100 * np.array([ok.late.sum(), ok.late.sum() + len(raw) - len(ok)]) / len(raw))
print("five number group", ok.groupby("courier").actual_min.quantile([.25, .5, .75]).unstack())
print("sd raw/clean", raw.actual_min.std(), ok.actual_min.std(), "IQR raw/clean",
      *(s.quantile(.75)-s.quantile(.25) for s in (raw.actual_min, ok.actual_min)))
for shop in ("KZN-1", "UFA-1"):
    counts = raw.loc[raw.shop_id.eq(shop)].groupby(raw.created.str[:10]).size().reindex(
        pd.date_range("2026-09-01", "2026-11-30").strftime("%Y-%m-%d"), fill_value=0)
    print("calendar", shop, "rows", counts.sum(), "lambda", counts.mean(), "zero days", counts.eq(0).sum())
print("hist density", np.histogram([1]*4 + [3]*6 + [15], bins=[0, 2, 4], density=True)[0])
comparison = ok[ok.weather.isin(["снег", "ясно"])].groupby(["weather", "courier"]).late.agg(["size", "sum", "mean"])
print(comparison)
weights = comparison.loc["ясно", "size"] / comparison.loc["ясно", "size"].sum()
print("snow, clear mix", weights.dot(comparison.loc["снег", "mean"]))
s1 = raw.dropna(subset=["distance_km", "actual_min"])
p = s1.distance_km.corr(s1.actual_min)
s = s1.distance_km.corr(s1.actual_min, method="spearman")
assert np.isclose(s, s1.distance_km.rank().corr(s1.actual_min.rank()))
print("Pearson/Spearman/diff/early rounding", p, s, round(s-p, 2), round(round(s, 2)-round(p, 2), 2))
print("r km/time, items/time, amount/time", ok.distance_km.corr(ok.actual_min), ok["items"].corr(ok.actual_min), ok.amount.corr(ok.actual_min))
print("r amount/time by items", {k: round(t.amount.corr(t.actual_min), 2) for k,t in ok.groupby("items")})
print("r km/time by courier", {k: round(t.distance_km.corr(t.actual_min), 2) for k,t in ok.groupby("courier")})
for label, t in ok.groupby("late"):
    print("rating received", label, t.rating.count(), "/", len(t), "mean", t.rating.mean(),
          "bounds assigning missing 1 or 5", t.rating.fillna(1).mean(), t.rating.fillna(5).mean())
for label,t in ok.groupby(ok.delay.gt(10)):
    print("delay>10", label, len(t), "rated", t.rating.count(), "mean", t.rating.mean(), "rated <=3", t.rating.le(3).sum())

def summarize(frame):
    d = frame.loc[frame.actual_min.between(1,299)].copy()
    d["late"] = d.actual_min > d.promised_min
    grouped = d.groupby("courier").late.agg(["size","sum","mean"])
    leader = grouped["mean"].idxmax()
    chosen = d[d.courier.eq(leader) & d.promised_min.eq(30)]
    x = chosen.actual_min.quantile(.8)
    promise = np.ceil(x/5)*5
    print("walkers", grouped.to_dict(), "selected", leader, "selected 30min", len(chosen), "p80", x,
          "scenario", promise, "within", chosen.actual_min.le(promise).sum())
    return leader
assert summarize(raw) == "пеший"
with TemporaryDirectory() as tmp:
    path = Path(tmp) / "deliveries.csv"
    make_extract(path)
    assert summarize(pd.read_csv(path)) == "авто"

o = orders.merge(guests, on="guest_id", validate="many_to_one")
assert len(o) == len(orders) and o.guest_id.nunique() == len(guests)
o["date"] = pd.to_datetime(o.date)
o["month"] = o.date.dt.to_period("M")
o["cohort"] = o.groupby("guest_id").month.transform("min")
o["age"] = o.month.astype("int64") - o.cohort.astype("int64")
active = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")
print("cohort sizes and retention %", active[0].to_dict(), active.div(active[0], axis=0).mul(100).round(1), sep="\n")
promo = o[o.cohort.eq(pd.Period("2026-03", freq="M")) & o.source.eq("акция")]
print("promo", promo.guest_id.nunique(), promo.loc[promo.age.eq(3)].guest_id.nunique(), promo.loc[promo.age.lt(3)].amount.sum()/promo.guest_id.nunique())
for month,t in o.groupby("month"):
    print("month", month, "MAU", t.guest_id.nunique(), "DAU", t[["date","guest_id"]].drop_duplicates().shape[0]/month.days_in_month)
print("weighted checks ₽", o.amount.mean(), o.groupby("shop_id").amount.mean().mean(), o.groupby("guest_id").amount.mean().mean())
def city(active):
    counts = active[["city","date","guest_id"]].drop_duplicates().groupby("city").size()
    return (100 * counts / (30 * active.groupby("city").guest_id.nunique())).round(1)
j = o[o.month.eq(pd.Period("2026-06",freq="M"))]
mut = j[~(j.city.eq("Пермь") & j.date.eq(pd.Timestamp("2026-06-01")))]
print("sticky-city baseline", city(j).to_dict(), "modified", city(mut).to_dict(),
      "observed-only", (mut.pivot_table(index="date",columns="city",values="guest_id",aggfunc="nunique").mean()/mut.groupby("city").guest_id.nunique()*100).round(1).to_dict())

steps = ["открыл","меню","корзина","оплата","заказ"]
for key,g in events.sort_values("ts").groupby("session_id"):
    journey = list(dict.fromkeys(g.step))
    assert journey == steps[:len(journey)]
    assert g.platform.nunique() == 1 and g.ts.ge("2026-06-15").nunique() == 1
by_step = events.groupby("step").session_id.agg(["size","nunique"]).reindex(steps)
print("funnel: counts and rates", by_step, (by_step/by_step.shift()*100).round(1), sep="\n")
t = events.groupby(["platform",events.ts.ge("2026-06-15"),"step"]).session_id.nunique().unstack()[steps]
print("by platform and period",t)
print("step rates",(t.div(t.shift(axis=1))*100).round(2))
android=t.loc["android"]
lost = android.loc[True,"оплата"] * android.loc[False,"заказ"] / android.loc[False,"оплата"] - android.loc[True,"заказ"]
print("scenario",lost)
assert round(lost) == 104

if len(sys.argv) > 1:
    export = json.loads(Path(sys.argv[1]).read_text())
    for lesson in sorted({x["lesson"] for x in export if x["lesson"].startswith("ch04/")}):
        entries = [x for x in export if x["lesson"] == lesson]
        md = (ROOT / "content" / (lesson + ".md")).read_text()
        figures = re.findall(r"^::: figure (.+)$",md,re.M)
        for name in figures:
            fig = ET.parse(ROOT / "content/figures" / (name + ".svg")).getroot()
            assert fig.find("{http://www.w3.org/2000/svg}title") is not None
        print("coverage", lesson, {k:sum(x["kind"] == k for x in entries) for k in ("task","cell","predict")}, "figures",",".join(figures))
