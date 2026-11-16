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

print(build_report(clean))
