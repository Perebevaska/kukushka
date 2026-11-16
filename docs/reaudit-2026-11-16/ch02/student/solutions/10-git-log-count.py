log = """f0dd728 Выводы в README
a74c250 Слияние ветки loyalty
3e746ee Гипотеза: гости с картой тратят больше
5ae82cb Выручка по месяцам
3efd677 Фильтр доставки в отдельной переменной
375c1e4 Загрузка заказов и выручка
8c3c173 Структура проекта: README и .gitignore"""

rows=log.splitlines()
n_commits=len(rows)
last_hash=rows[0].split()[0]
first_message=rows[-1].split(" ",1)[1]
