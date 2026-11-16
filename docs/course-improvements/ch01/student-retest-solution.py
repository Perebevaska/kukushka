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

print(len(clean), n_bad, n_dupes)

def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"
    period = orders[0]["date"].isoformat()[:7]
    lines = [f"# Отчёт за {period}", f"Принято заказов: {len(orders)}"]
    revenue = 0
    for order in orders:
        revenue += order["amount"]
    avg_check = round(revenue / len(orders))
    lines.append(f"Учтённая выручка: {revenue} ₽")
    lines.append(f"Средний чек: {avg_check} ₽")
    by_city = {}
    for order in orders:
        city = order["city"]
        by_city[city] = by_city.get(city, 0) + order["amount"]
    city_rank = sorted(by_city.items(), key=lambda pair: pair[1], reverse=True)
    city, amount = city_rank[0]
    lines.append(f"Лучший город: {city} ({amount} ₽)")
    counts = {}
    for order in orders:
        drink = order["drink"]
        counts[drink] = counts.get(drink, 0) + 1
    top3 = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
    drink_labels = []
    for drink, count in top3:
        drink_labels.append(f"{drink} ({count})")
    lines.append("Напитки по числу заказов: " + ", ".join(drink_labels))
    DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    by_day = {}
    for order in orders:
        day = order["date"].weekday()
        by_day[day] = by_day.get(day, 0) + order["amount"]
    best_number = max(by_day, key=by_day.get)
    best_day = DAYS[best_number]
    best_day_revenue = by_day[best_number]
    lines.append(f"День с наибольшей выручкой: {best_day} ({best_day_revenue} ₽)")
    return "\n".join(lines)

text = build_report(clean)
print(text)

quality = [
    "## Качество данных",
    f"- Строк в выгрузке: {len(clean) + n_bad + n_dupes}",
    f"- Битых строк: {n_bad}",
    f"- Дублей: {n_dupes}",
]
with open("report.md", "w", encoding="utf-8") as report:
    report.write(text + "\n\n" + "\n".join(quality) + "\n")
with open("report.md", encoding="utf-8") as report:
    print(report.read())
