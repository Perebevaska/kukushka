import csv
import datetime as dt
orders = []
n_bad = 0
with open("orders.csv", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        try:
            row["amount"] = int(row["amount"])
        except ValueError:
            n_bad += 1
            continue
        row["date"] = dt.date.fromisoformat(row["date"])
        orders.append(row)

clean = []
seen = set()
n_dupes = 0
for row in orders:
    if row["order_id"] in seen:
        n_dupes += 1
    else:
        seen.add(row["order_id"])
        clean.append(row)

def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"
    period = orders[0]["date"].isoformat()[:7]
    revenue = sum(row["amount"] for row in orders)
    cities = {}
    drinks = {}
    days = {}
    for row in orders:
        city = row["city"]
        drink = row["drink"]
        day = row["date"].weekday()
        cities[city] = cities.get(city, 0) + row["amount"]
        drinks[drink] = drinks.get(drink, 0) + 1
        days[day] = days.get(day, 0) + row["amount"]
    best_city = max(cities, key=cities.get)
    best_day = max(days, key=days.get)
    top3 = sorted(drinks.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
    top_text = ", ".join(f"{name} ({count})" for name, count in top3)
    DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    return "\n".join([
        f"# Отчёт за {period}",
        f"Принято заказов: {len(orders)}",
        f"Учтённая выручка: {revenue} ₽",
        f"Средний чек: {round(revenue / len(orders))} ₽",
        f"Лучший город: {best_city} ({cities[best_city]} ₽)",
        f"Напитки по числу заказов: {top_text}",
        f"День с наибольшей выручкой: {DAYS[best_day]} ({days[best_day]} ₽)",
    ])

text = build_report(clean)
text += f"\n\n## Качество данных\n- Строк в выгрузке: {len(orders) + n_bad}\n- Битых строк: {n_bad}\n- Дублей: {n_dupes}\n"
with open("report.md", "w", encoding="utf-8") as f:
    f.write(text)
with open("report.md", encoding="utf-8") as f:
    print(f.read())
