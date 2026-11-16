import csv
import datetime as dt
orders = []
n_bad = 0
n_source = 0
with open("orders.csv", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        n_source += 1
        try:
            row["amount"] = int(row["amount"])
        except ValueError:
            n_bad += 1
            continue
        row["date"] = dt.date.fromisoformat(row["date"])
        orders.append(row)
seen = set()
clean = []
n_dupes = 0
for o in orders:
    if o["order_id"] in seen:
        n_dupes += 1
        continue
    seen.add(o["order_id"])
    clean.append(o)

print(len(clean), n_bad, n_dupes)
def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"
    period = orders[0]["date"].isoformat()[:7]
    lines = [f"# Отчёт за {period}", f"Принято заказов: {len(orders)}"]
    revenue = sum(o["amount"] for o in orders)
    avg_check = round(revenue / len(orders))
    lines.append(f"Учтённая выручка: {revenue:,} ₽".replace(",", " "))
    lines.append(f"Средний чек: {avg_check} ₽")
    by_city = {}
    counts = {}
    by_day = {}
    for o in orders:
        city = o["city"]
        by_city[city] = by_city.get(city, 0) + o["amount"]
        drink = o["drink"]
        counts[drink] = counts.get(drink, 0) + 1
        day = o["date"].weekday()
        by_day[day] = by_day.get(day, 0) + o["amount"]
    best_city = max(by_city, key=by_city.get)
    lines.append(f"Лучший город: {best_city} ({by_city[best_city]:,} ₽)".replace(",", " "))
    top3 = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    drinks = ", ".join(f"{d} ({n})" for d, n in top3)
    lines.append(f"Напитки по числу заказов: {drinks}")
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    best = max(by_day, key=by_day.get)
    lines.append(f"День с наибольшей выручкой: {days[best]} ({by_day[best]:,} ₽)".replace(",", " "))
    return "\n".join(lines)

text = build_report(clean)
text += (
    "\n\n## Качество данных\n"
    f"- Строк в выгрузке: {n_source}\n"
    f"- Битых строк: {n_bad}\n"
    f"- Дублей: {n_dupes}\n"
)
text += "\nПолная выручка неизвестна: строки с нечитаемой суммой исключены.\n" if n_bad else ""
with open("report.md", "w", encoding="utf-8") as f:
    f.write(text)
with open("report.md", encoding="utf-8") as f:
    print(f.read())
