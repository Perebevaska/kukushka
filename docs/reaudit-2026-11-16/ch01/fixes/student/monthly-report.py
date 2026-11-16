# 1. Здесь ваш код чтения и удаления дублей.
import csv
from datetime import date

clean = []
first = {}
bad_ids = []
conflicts = []
n_rows = 0
n_bad = 0
n_dupes = 0
n_exact = 0
period = None
with open('orders.csv', encoding='utf-8') as source:
    for row in csv.DictReader(source):
        n_rows += 1
        row['date'] = date.fromisoformat(row['date'])
        period = row['date'].isoformat()[:7]
        try:
            row['amount'] = int(row['amount'])
        except ValueError:
            n_bad += 1
            bad_ids.append(row['order_id'])
            continue
        order_id = row['order_id']
        if order_id in first:
            n_dupes += 1
            old = first[order_id]
            if row == old:
                n_exact += 1
            else:
                fields = [field for field in row if row[field] != old[field]]
                conflicts.append(
                    f"- Конфликт {order_id}: учтена первая читаемая запись {old['amount']} ₽; "
                    f"другая запись {row['amount']} ₽ (отличаются {', '.join(fields)}). "
                    "Изменение порядка записей может изменить выбранную запись и итог; "
                    "при одинаковых суммах меняются поля, сумма заказа не меняется. "
                    "Запросить первичный чек."
                )
            continue
        first[order_id] = row
        clean.append(row)
print(len(clean), n_bad, n_dupes)

# 2. Здесь ваше определение build_report.
def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"

    period = orders[0]["date"].isoformat()[:7]
    lines = [f"# Отчёт за {period}", f"Принято заказов: {len(orders)}"]
    revenue = sum(order['amount'] for order in orders)
    lines.append(f'Учтённая выручка: {revenue} ₽')
    lines.append(f'Средний чек: {revenue / len(orders):.0f} ₽')
    cities = {}
    drinks = {}
    days = {}
    for order in orders:
        city = order['city']
        drink = order['drink']
        day = order['date'].weekday()
        cities[city] = cities.get(city, 0) + order['amount']
        drinks[drink] = drinks.get(drink, 0) + 1
        days[day] = days.get(day, 0) + order['amount']
    best_city = max(cities, key=cities.get)
    lines.append(f'Лучший город: {best_city} ({cities[best_city]} ₽)')
    top3 = sorted(drinks.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
    top_text = ', '.join(f'{drink} ({count})' for drink, count in top3)
    lines.append(f'Топ-3 напитка по числу принятых заказов: {top_text}')
    others = len(orders) - sum(count for drink, count in top3)
    lines.append(f'Заказов остальных напитков: {others}')
    best_day = max(days, key=days.get)
    day_names = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    lines.append(f'День с наибольшей выручкой: {day_names[best_day]} ({days[best_day]} ₽)')
    return '\n'.join(lines)


text = build_report(clean)
if not clean and period:
    text = text.replace('# Отчёт', f'# Отчёт за {period}', 1)
print(text)

# 3. Здесь запись текста и журнала в report.md.
journal = [
    '', '## Качество данных',
    f'- Строк в выгрузке: {n_rows}',
    f'- Битых строк: {n_bad}',
    f'- Дублей: {n_dupes}',
    f'- Точных повторов: {n_exact}',
    f'- Конфликтующих строк: {len(conflicts)}',
]
if bad_ids:
    journal.append('- Нечитаемые суммы: ' + ', '.join(bad_ids) + '. Запросить читаемые суммы из первичных чеков.')
journal.extend(conflicts)
if bad_ids or conflicts:
    journal.append('- Полная выручка неизвестна: есть нечитаемые суммы или конфликтующие записи. Учтённая выручка относится только к принятым записям по правилу выбора первой читаемой записи.')
else:
    journal.append('- Полная выручка по выгрузке учтена; точные повторы исключены.')
with open('report.md', 'w', encoding='utf-8') as output:
    output.write(text + '\n' + '\n'.join(journal) + '\n')
