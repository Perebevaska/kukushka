"""Предметная сверка главы 3. Запуск из корня проекта."""
import os
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd


ROOT = Path.cwd()
DATA = ROOT / "site/data"
os.chdir(DATA)
print("Python, pandas, numpy, openpyxl", sys.version.split()[0], pd.__version__, np.__version__, openpyxl.__version__)
raw = pd.read_csv("clients_raw.csv")
orders = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
shops = pd.read_csv("shops.csv")
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
reviews = pd.read_csv("reviews.csv")

print("01 raw shape, missing per column, literal birth missing", raw.shape, raw.isna().sum().to_dict(), raw.birth_date.eq("не указано").sum())
bonus = pd.to_numeric(raw.bonus.str.replace(" ", ""), errors="coerce")
print("02 balances", bonus.count(), bonus.sum(), round(bonus.mean(), 1), round(bonus.fillna(0).mean(), 1), bonus[raw.city.isna()].sum())
wrong = pd.read_csv("pos_december.csv")
gross = pos.price.mul(pos.qty)
fraction = pd.to_numeric(pos.discount.str.rstrip("%")) / 100
net = gross.mul(1 - fraction.fillna(0))
print("03 POS first wrongly parsed index and value", wrong.index[0], wrong.iloc[0, 0])
print("03 POS rows, gross/net, net dedup", len(pos), gross.sum(), net.sum(), net[~pos.id.duplicated()].sum())
print("03 missing discount rows, omitted revenue if left NA", fraction.isna().sum(), gross.mul(1 - fraction).sum())
print("03 reviews", len(reviews), pd.to_numeric(reviews.rating.str[0]).mean().round(2))

months = "Янв Фев Мар Апр Май Июн Июл Авг Сен".split()
def finance(book):
    first = pd.read_excel(book, sheet_name=["План", "Факт"], header=None)
    heads = {name: int(sheet.iloc[:, 0].eq("Код").to_numpy().nonzero()[0].item()) for name, sheet in first.items()}
    tables = {}
    for name, header in heads.items():
        tab = pd.read_excel(book, sheet_name=name, header=header).set_index("Код")
        body = tab.drop("Итого")[months]
        assert np.allclose(body.sum(), tab.loc["Итого", months].astype(float))
        tables[name] = body
    return heads, tables

book = "zerno_finance.xlsx"
heads, tables = finance(book)
wb = openpyxl.load_workbook(book)
for name, displacement in [("План", 4), ("Факт", 2)]:
    wb[name].insert_rows(1, displacement)
    wb[name].cell(1, 1, "Новая строка")
buffer = BytesIO()
wb.save(buffer)
shifted, comparison = finance(buffer)
for name in heads:
    pd.testing.assert_frame_equal(comparison[name], tables[name])
print("03b headers before and after", heads, shifted)
plan, fact = (tables[name].sum(axis=1) for name in heads)
print("03b finance", plan.sum().round(1), fact.sum().round(1), (fact.sum()/plan.sum()*100).round(1), (fact/plan*100).round(1).to_dict())
print("03b EKB counts", {name: int(table.loc["EKB-1"].count()) for name, table in tables.items()})
quarter = pd.DataFrame([[None, None, None], [0, 0, 0], [None, 0, 14]], index=["пусто", "ноль", "частично"])
print("03b quarter sum/count", list(zip(quarter.sum(axis=1), quarter.count(axis=1))))

def versions(frame):
    first = frame.drop_duplicates()
    normal = first.assign(client_id=first.client_id.str.strip().str.upper())
    latest = normal.sort_values("signup_date").drop_duplicates("client_id", keep="last").set_index("client_id")
    return latest, [len(frame), len(first), len(normal), len(latest)]

def source(series):
    return series.str.strip().str.lower().replace({"2гис": "карты", "яндекс карты": "карты", "от друзей":"друзья", "проходил мимо":"мимо", "соц. сети":"соцсети"})

def births(frame):
    return pd.to_datetime(frame.birth_date, format="%Y-%m-%d", errors="coerce").fillna(pd.to_datetime(frame.birth_date, format="%d.%m.%Y", errors="coerce"))

def age(dates):
    return 2026 - dates.dt.year - dates.dt.strftime("%m%d").gt("1201").astype(int)

clients, log = versions(raw)
print("04/08 clean log, POS duplicated ID", log, pos.id.duplicated().sum())
flat = pd.read_csv("delivery_flat.csv")
print("04 flat orders/shops/date range", len(flat), flat.shop_id.nunique(), flat.date.min(), flat.date.max())
digits = raw.phone.str.replace(r"\D", "", regex=True)
phone = digits.where(digits.str.fullmatch(r"[78]?\d{10}")).str[-10:]
phone_map = pd.DataFrame({"phone": phone, "id": raw.client_id.str.strip().str.upper()}).groupby("phone").id.nunique()
print("05 shops before/after, shared phones", pos.shop.nunique(), pos.shop.str.strip().str.upper().str.replace(" ","-").nunique(), phone_map.gt(1).sum())
print("06 2GIS raw rows, latest cards, source counts", raw.source.str.lower().eq("2гис").sum(), clients.source.str.lower().eq("2гис").sum(), source(raw.source).value_counts(dropna=False).to_dict())
years = age(births(raw))
print("07 average full years with and without 1900 only", years.mean().round(3), years[~births(raw).eq("1900-01-01")].mean().round(3))
flag = pos.qty.eq(0) | pos.qty.gt(10)
print("07 flags/gross means", flag.sum(), gross.mean().round(2), gross[~flag].mean().round(2))

def crm(frame, window):
    latest, counts = versions(frame)
    src = source(latest.source).fillna("не указано")
    src = src.where(src.map(src.value_counts()).ge(10), "прочее")
    grouped = window.groupby("client_id").amount.agg(["size", "sum"]).reindex(latest.index, fill_value=0)
    active = grouped["size"].gt(0)
    revenue = grouped.groupby(src)["sum"].agg(["count", "mean"]).round(0)
    return counts, int(active.sum()), round(active.mean()*100, 1), grouped.loc[active, "sum"].mean().round(1), revenue, grouped.loc[src.eq("прочее"), "sum"]

for label, frame, window in [("autumn", raw, orders), ("november", raw, orders[orders.datetime.dt.month.eq(11)])]:
    counts, active, pct, avg, source_table, small = crm(frame, window)
    print("09", label, counts, active, pct, avg)
    if label == "autumn":
        print("09 per source", source_table.to_dict("index"), "remove max/min", small.drop(small.idxmax()).mean().round(), small.drop(small.idxmin()).mean().round())

fresh = raw.iloc[[0]].copy()
card = fresh.client_id.iloc[0].strip().upper()
fresh["client_id"] = " " + card.lower()
fresh["signup_date"] = "2026-11-29"
fresh["source"] = "2ГИС"
unused = fresh.assign(client_id="C-NEW", source="от друзей")
updated = pd.concat([raw, fresh, fresh, unused], ignore_index=True)
latest, counts = versions(updated)
assert source(latest.source)[card] == "карты" and card in clients.index
print("08/09 CRM change", card, source(clients.source)[card], "→", source(latest.source)[card], "plus inactive card", *crm(updated, orders)[:4])

home = clients.city.str.strip().str.lower().str.removeprefix("г.").str.strip().replace({"екб":"екатеринбург"}).str.capitalize()
pairs = orders.assign(shop=orders.shop_id.map(shops.set_index("shop_id").city), home=orders.client_id.map(home))
matched = pairs.dropna(subset=["shop","home"])
away = matched[matched.shop.ne(matched.home)]
east = away[away.home.isin(["Москва","Екатеринбург"])]
travel = pairs.groupby("client_id").shop.nunique().ge(2)
print("09 home all/known/matches/away/other cities/unique cards/Kazan/travel/no home",
      len(orders), len(matched), matched.shop.eq(matched.home).sum(), len(away),
      len(east), east.client_id.nunique(), east.shop.eq("Казань").sum(),
      travel.sum(), home.reindex(travel[travel].index).isna().sum())

baseline = "6201fa939fbb25f8230f8d3d9e65f7bf5875c4e6"
for snapshot in ["baseline", "working"]:
    path = "content/ch03/08-pipeline.md"
    md = subprocess.check_output(["git", "show", baseline+":"+path], cwd=ROOT, text=True) if snapshot == "baseline" else (ROOT/path).read_text()
    code = re.search(r"```python\n(.*?)```", md.split("## Вся очистка анкет", 1)[1], re.S).group(1).split("clients = clean_clients")[0]
    env = {}
    exec(code, env)
    print("08 theory", snapshot, env["clean_gender"](pd.Series(["море", "жен", "желаю пропустить"])).fillna("NA").tolist(), env["parse_birth"](pd.Series(["1925-12-02","1926-05-01","1925-12-01"])).notna().tolist(), env["clean_clients"](raw).source.eq("карты").sum())

print("02 unique cards behind known raw bonuses", raw.loc[bonus.notna(), "client_id"].str.strip().str.upper().nunique())
churn = pd.read_csv("guests_churn.csv")
print("02 app and missing avg check", churn.groupby("app").avg_check.agg(["size", "count"]).to_dict("index"), churn.loc[churn.avg_check.isna(), "visits_90d"].unique().tolist())
print("07 amounts Q1,Q3, above upper", orders.amount.quantile([.25,.75]).tolist(), orders.amount.gt(637.5).sum())
valid_ages = age(births(clients)).where(lambda a:a.between(14,100))
print("09 age valid/missing/median", valid_ages.count(), valid_ages.isna().sum(), valid_ages.median())
print("09 age groups", pd.cut(valid_ages, bins=[14,25,35,45,60,101], right=False).value_counts().to_dict())
print("09 top home cities", home.value_counts().head(2).to_dict())

# Генерируем только использованные в главе наборы во временной папке.
import random
from tempfile import TemporaryDirectory
sys.path.insert(0, str(ROOT / "tools"))
import gen_data
import gen_excel
import gen_flat_export

with TemporaryDirectory() as folder:
    temp = Path(folder)
    gen_data.OUT = temp
    gen_flat_export.OUT = temp
    gen_data.gen_chapter3(random.Random(3003))
    gen_flat_export.main()
    for name in ["clients_raw.csv","pos_december.csv","reviews.csv","delivery_flat.csv"]:
        assert (temp/name).read_bytes() == (DATA/name).read_bytes(), name
    for rows, name in zip(gen_excel.build(), ["finance_plan.csv","finance_fact.csv"]):
        gen_excel.write_csv(rows, temp/name)
        assert (temp/name).read_bytes() == (DATA/name).read_bytes(), name
    for sheet, csv in [("План", "finance_plan.csv"), ("Факт", "finance_fact.csv")]:
        xl = pd.read_excel(book, sheet_name=sheet, skiprows=heads[sheet], usecols=["Код",*months])
        generated = pd.read_csv(temp/csv, sep=";", decimal=",", skiprows=heads[sheet], usecols=["Код",*months])
        pd.testing.assert_frame_equal(xl, generated)
    print("Source provenance: 6 CSV identical, two workbook sheets agree by code/month.")
