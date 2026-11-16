import io
import pandas as pd

log = """f0dd728|2026-11-26|Аня Петрова|Выводы в README
a74c250|2026-11-25|Аня Петрова|Слияние ветки loyalty
3e746ee|2026-11-25|Аня Петрова|Гипотеза: гости с картой тратят больше
5ae82cb|2026-11-25|Аня Петрова|Выручка по месяцам
3efd677|2026-11-24|Аня Петрова|Фильтр доставки в отдельной переменной
375c1e4|2026-11-24|Аня Петрова|Загрузка заказов и выручка
8c3c173|2026-11-24|Аня Петрова|Структура проекта: README и .gitignore"""

commits=pd.read_csv(io.StringIO(log),sep="|",names=["hash","date","author","message"],parse_dates=["date"])
per_day=commits.groupby("date").size().sort_index()
busiest=per_day.idxmax()
