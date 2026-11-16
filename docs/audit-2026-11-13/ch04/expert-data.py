"""Run from any directory with CPython. Reads only the five delivered CSV files."""
import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median, quantiles

DATA = Path(__file__).resolve().parents[3] / "site/data"


def read(name, key=None):
    with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len({tuple(r.values()) for r in rows}) == len(rows)
    if key:
        assert len({r[key] for r in rows}) == len(rows)
    blanks = Counter(k for r in rows for k, v in r.items() if not v)
    print(name, len(rows), "пустые поля", dict(blanks))
    return rows


sales = read("orders_3m", "order_id")
print("Осенняя выручка, ₽", sum(int(r["amount"]) for r in sales))
raw = read("deliveries", "delivery_id")
valid = [r for r in raw if r["actual_min"] and 1 <= int(r["actual_min"]) <= 299]
for r in valid:
    r["delay"] = int(r["actual_min"]) - int(r["promised_min"])
late = [r["delay"] for r in valid if r["delay"] > 0]
print("Валидные, поздние, медиана и P90 задержки", len(valid), len(late), median(late),
      quantiles(late, n=10, method="inclusive")[-1])
for courier in ("авто", "вело", "пеший"):
    group = [r for r in valid if r["courier"] == courier]
    print(courier, "опоздало/всего", sum(r["delay"] > 0 for r in group), len(group))
walk = [r for r in valid if r["courier"] == "пеший" and r["promised_min"] == "30"]
print("Пешие 30, поздние, с фактом <=40", len(walk), sum(r["delay"] > 0 for r in walk),
      sum(int(r["actual_min"]) <= 40 for r in walk))
for name, group in [("вовремя", [r for r in valid if r["delay"] <= 0]),
                    ("опоздание >10", [r for r in valid if r["delay"] > 10])]:
    ratings = [int(r["rating"]) for r in group if r["rating"]]
    print(name, "всего, ответы, оценки <=3", len(group), len(ratings), sum(x <= 3 for x in ratings))
print("7 октября, валидные и пешие 30", *(sum(r["created"].startswith("2026-10-07") for r in rows)
                                            for rows in [valid, walk]))

orders = read("preorders", "order_id")
sources = {r["guest_id"]: r["source"] for r in read("preorder_guests", "guest_id")}
by_guest = defaultdict(list)
for r in orders:
    by_guest[r["guest_id"]].append(r)
assert by_guest.keys() == sources.keys()
for source in sorted(set(sources.values())):
    cohort = [rows for guest, rows in by_guest.items() if sources[guest] == source and
              min(r["date"] for r in rows).startswith("2026-03")]
    rev = sum(int(r["amount"]) for rows in cohort for r in rows if r["date"] < "2026-06")
    active = sum(any(r["date"].startswith("2026-06") for r in rows) for rows in cohort)
    print("Когорта марта", source, "гостей, выручка M0–M2, активны M3", len(cohort), rev, active)
june = [r for r in orders if r["date"].startswith("2026-06")]
guest_days = {(r["guest_id"], r["date"]) for r in june}
print("Июнь MAU, средний DAU", len({g for g, _ in guest_days}), len(guest_days) / 30)

events = read("app_funnel")
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]
print("Воронка", [len({r["session_id"] for r in events if r["step"] == step}) for step in steps])
for platform in ["android", "ios"]:
    for after in [False, True]:
        part = [r for r in events if r["platform"] == platform and (r["ts"] >= "2026-06-15") == after]
        pay, buy = [len({r["session_id"] for r in part if r["step"] == step}) for step in steps[-2:]]
        print(platform, "после" if after else "до", pay, buy, f"{100 * buy / pay:.2f}%")
