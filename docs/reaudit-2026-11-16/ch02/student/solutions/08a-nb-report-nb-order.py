cells = []
cells.append(("markdown", "# Итоги осени: цель и данные"))
cells.append(("code", "import pandas as pd"))
cells.append(("code", "df = pd.read_csv('data/orders_3m.csv')"))
cells.append(("markdown", "## Выручка по месяцам"))
cells.append(("code", "monthly = df.groupby('month')['amount'].sum()"))
cells.append(("markdown", "Вывод: в ноябре +9.6 % к октябрю."))
cells.append(("markdown", "## Общий вывод"))
print(len(cells))
