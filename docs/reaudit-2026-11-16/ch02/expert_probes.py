"""Независимые предметные расчёты главы 2. Python 3, без внешних пакетов."""
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


DATA = Path(__file__).resolve().parents[3] / "site" / "data"


def read(name):
    with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def leaders(values):
    return {key for key, value in values.items() if value == max(values.values())}


def shop_metrics(revenue, reference):
    seats = {shop: places for shop, places in reference if shop in revenue}
    per_seat = {shop: revenue[shop] / places for shop, places in seats.items()}
    return leaders(revenue), leaders(per_seat), leaders(revenue) & leaders(seats)


def autumn():
    orders = read("orders_3m")
    shops = [(r["shop_id"], int(r["seats"])) for r in read("shops")]
    menu = {r["drink"]: r for r in read("menu")}
    assert len(orders) == len({r["order_id"] for r in orders}) == 2089
    totals, costs, sales, rubles = Counter(), Counter(), Counter(), Counter()
    months, channels = Counter(), Counter()
    factors = {"S": 1, "M": 1.25, "L": 1.5}
    for row in orders:
        item, amount = menu[row["drink"]], int(row["amount"])
        category = item["category"]
        costs[category] += int(item["cost_s"]) * int(row["qty"]) * factors[row["size"]]
        sales[category] += amount
        totals[row["shop_id"]] += amount
        months[row["datetime"][:7]] += amount
        channels[row["channel"]] += amount
    for name in ("Чай", "Матча"):
        rubles[name] = int(menu[name]["price_s"]) - int(menu[name]["cost_s"])
    assert rubles == {"Чай": 105, "Матча": 170}
    assert (2 * factors["M"] * 50, 3 * factors["L"] * 40) == (125, 180)
    assert (sales["кофе"], costs["кофе"]) == (604196, 145381.25)
    assert (sales["не кофе"], costs["не кофе"]) == (105999, 24075)
    assert shop_metrics(totals, shops[::-1]) == ({"PRM-1"}, {"PRM-1"}, set())
    alternative = {"A": 600, "B": 900, "C": 900}
    reference = [("C", 30), ("A", 10), ("B", 30)]
    assert shop_metrics(alternative, reference) == ({"B", "C"}, {"A"}, {"B", "C"})
    assert shop_metrics(alternative, reference[::-1]) == shop_metrics(alternative, reference)
    print("Выручка по месяцам / каналам", dict(sorted(months.items())), dict(channels))
    print("Маржинальность, %", {c: 100 * (1 - costs[c] / sales[c]) for c in sales})


def loyalty():
    guests, orders = read("zdb_guests"), read("zdb_orders")
    times = defaultdict(list)
    for row in orders:
        if row["guest_id"]:
            times[row["guest_id"]].append(datetime.fromisoformat(row["ordered_at"]))
    for values in times.values():
        values.sort()
    cutoff = datetime(2026, 8, 1)
    observed, eligible, calendars, durations, august_first = (Counter() for _ in range(5))
    for guest in guests:
        source = guest["source"]
        visits = times[guest["guest_id"]]
        if visits:
            observed[source] += 1
            august_first[source] += visits[0].date() == cutoff.date()
        if visits and visits[0] < cutoff:
            eligible[source] += 1
            if len(visits) >= 2:
                calendars[source] += (visits[1].date() - visits[0].date()).days <= 30
                durations[source] += visits[1] - visits[0] <= timedelta(days=30)
    app = [g for g in guests if g["source"] == "приложение"]
    mature = [g for g in app if g["reg_date"] <= "2026-08-19"]
    within = sum(bool(times[g["guest_id"]]) and
                 (times[g["guest_id"]][0].date() - datetime.fromisoformat(g["reg_date"]).date()).days <= 12
                 for g in mature)
    assert (len(app), observed["приложение"], len(mature), within) == (646, 565, 614, 544)
    assert (eligible["касса"], calendars["касса"], durations["касса"]) == (756, 591, 590)
    assert (eligible["приложение"], calendars["приложение"], durations["приложение"]) == (494, 422, 420)
    assert august_first == {"касса": 10, "приложение": 2}
    print("Возврат по датам / по времени / знаменатель", dict(calendars), dict(durations), dict(eligible))


if __name__ == "__main__":
    autumn()
    loyalty()
