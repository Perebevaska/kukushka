---
title: SQL прямо по датафрейму — DuckDB
lead: "Вы знаете SQL — так пользуйтесь им и в Python. DuckDB выполняет обычные SQL-запросы прямо по таблицам pandas и CSV-файлам, без сервера и загрузки в базу. Разбираем `duckdb.sql`, запрос к файлу, JOIN и сверку одной цифры на SQL и pandas. Подзапросы, CTE и порядок выполнения запроса — в следующем уроке."
files: [orders_3m.csv, shops.csv, menu.csv]
recap:
  - "`import duckdb`; `duckdb.sql(\"SELECT … FROM df\").df()` — запрос к датафрейму `df` по его имени, результат — снова DataFrame."
  - "`.fetchone()[0]` — одно значение; `.df()` — таблица."
  - "Прямо из файла: `FROM 'orders_3m.csv'` — DuckDB сам определит столбцы и типы."
  - "В DuckDB `/` — обычное деление (`7/2 = 3.5`), целочисленное — `//`."
  - "`date_trunc('month', t)` обрезает дату до начала месяца (`2026-09-14 10:31` → `2026-09-01`); в SQL Server 2022 — `DATETRUNC`."
  - "SQL и pandas можно смешивать: что проще выразить запросом — запросом, остальное — методами pandas."
---

## SQL по датафрейму

Зачем: вы годами пишете SQL, а pandas пока даётся медленнее. DuckDB позволяет считать на Python **привычными запросами** и переходить на методы pandas там, где это удобнее.

DuckDB — встраиваемая аналитическая база данных: она работает прямо внутри Python, без сервера. Главное для нас — она умеет выполнять SQL **по таблицам pandas**, обращаясь к ним по имени переменной:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    SELECT shop_id, SUM(amount) AS revenue, COUNT(*) AS orders
    FROM df
    GROUP BY shop_id
    ORDER BY revenue DESC
""").df()
```

`duckdb.sql(...)` выполняет запрос, `.df()` превращает результат в DataFrame — дальше с ним можно работать как обычно. Текст запроса удобно писать в тройных кавычках: так он помещается на нескольких строках.

Если результат — одно число, его достают через `fetchone()` — он возвращает первую строку кортежем:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
revenue = duckdb.sql("SELECT SUM(amount) FROM df").fetchone()[0]
print(revenue)
```

::: figure duckdb-flow
Слева — откуда DuckDB берёт данные: датафрейм по имени переменной или файл по имени в кавычках. В середине — сам запрос; его результат ещё не DataFrame, его нужно «достать» одним из трёх методов. `.df()` даёт таблицу, `.fetchall()` — список кортежей, `.fetchone()` — один кортеж `(710195,)`, а `[0]` вынимает из него число — выручку сети за три месяца.
:::

{{practice: total, group, having}}

## Прямо из CSV

Зачем: чтобы посчитать что-то по большому CSV, не обязательно загружать его в pandas. Файл можно читать прямо в запросе — достаточно написать его имя в кавычках во `FROM`. DuckDB сам определит столбцы и типы (дату и время — тоже):

```python
import duckdb
duckdb.sql("""
    SELECT date_trunc('month', datetime) AS month, SUM(amount) AS revenue
    FROM 'orders_3m.csv'
    GROUP BY month
    ORDER BY month
""").df()
```

Что здесь происходит:

- `FROM 'orders_3m.csv'` — имя файла в одинарных кавычках вместо имени таблицы.
- `date_trunc('month', datetime)` обрезает дату-время до начала месяца: `2026-09-14 10:31` → `2026-09-01 00:00:00`. У всех заказов сентября одно и то же значение, поэтому по нему удобно группировать. В SQL Server 2022 то же делает `DATETRUNC(month, datetime)`, в более старых версиях — `DATEFROMPARTS(YEAR(d), MONTH(d), 1)`; в PostgreSQL — тот же `date_trunc`.

Как читать результат: три строки — сентябрь, октябрь и ноябрь 2026 года, выручка 220 241, 233 756 и 256 198 ₽.

{{practice: p-sql, from-file}}

## JOIN — как вы привыкли

```python
import duckdb
duckdb.sql("""
    SELECT s.city, SUM(o.amount) AS revenue
    FROM 'orders_3m.csv' AS o
    JOIN 'shops.csv' AS s USING (shop_id)
    GROUP BY s.city
    ORDER BY revenue DESC
""").df()
```

::: note
Диалект DuckDB близок к PostgreSQL. Отличия от SQL Server, которые чаще всего мешают: `LIMIT 5` вместо `TOP 5`, строки — в одинарных кавычках, а `/` между целыми — обычное, а не целочисленное деление.
:::

::: predict
```python static
import duckdb
print(duckdb.sql("SELECT 7 / 2").fetchone()[0])
```

- `3`
- [x] `3.5`
- `Ошибка`

Почему: в DuckDB `/` — всегда обычное деление, как `/` в Python. Целочисленное — `//`. В SQL Server тот же запрос вернул бы 3.
:::

{{practice: join}}

## Когда что

- **pandas** — когда нужно много шагов подряд: почистить, добавить столбцы, построить график; когда задача «естественно» ложится на методы.
- **SQL в DuckDB** — когда запрос привычнее написать на SQL: сложные JOIN, оконные функции, CTE; когда нужно быстро проверить гипотезу на большом CSV.
- **Сверка** — хорошая практика: посчитать ключевую цифру двумя способами. Расхождение сразу покажет ошибку в фильтре или соединении.

::: predict
```python static
import duckdb
import pandas as pd
t = pd.DataFrame({"x": [1, 2, 3]})
print(duckdb.sql("SELECT COUNT(*) FROM t WHERE x > 1").fetchone()[0])
```

- `3`
- [x] `2`
- `(2,)`

Почему: условию `x > 1` подходят 2 и 3. `fetchone()` вернул кортеж `(2,)`, а `[0]` достал из него число.
:::

::: quiz
Отчёт уже собран в pandas, и нужно посчитать скользящую сумму по дням внутри каждой кофейни. Вы привыкли к оконным функциям SQL. Что разумно сделать?

- [x] Написать запрос с `SUM(...) OVER (PARTITION BY ... ORDER BY ...)` через duckdb прямо по датафрейму
  > duckdb читает датафрейм как таблицу без копирования. Что удобнее выразить на SQL, то и пишите на SQL.
- [ ] Выгрузить таблицу в CSV, загрузить в базу и посчитать там
  > Лишние шаги: duckdb работает с датафреймом прямо в памяти.
- [ ] Переписать всё на чистый Python с циклами
  > Это медленнее и длиннее. И в pandas, и в SQL для этого есть готовые средства.
- [ ] Оконные функции доступны только в настоящей базе данных
  > duckdb — встроенная аналитическая база, оконные функции в ней есть.
:::

## Разберём вместе: один вопрос — два языка

Вопрос: «Выручка и число заказов по городам, только города с выручкой больше 90 тысяч, по убыванию». Переведём его по частям:

| шаг | SQL | pandas |
|---|---|---|
| соединить со справочником | `FROM df JOIN shops USING (shop_id)` | `df.merge(shops, on="shop_id")` |
| сгруппировать | `GROUP BY city` | `.groupby("city")` |
| посчитать | `SUM(amount) AS revenue, COUNT(*) AS orders` | `.agg(revenue=("amount", "sum"), orders=("amount", "size"))` |
| отфильтровать итог | `HAVING SUM(amount) > 90000` | `t[t["revenue"] > 90_000]` |
| отсортировать | `ORDER BY revenue DESC` | `.sort_values("revenue", ascending=False)` |

По шагам выйдет: Казань — 279 705 ₽, Пермь — 261 540 ₽, Тюмень — 96 489 ₽; Уфа (72 461 ₽) не проходит фильтр.

```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
a = duckdb.sql("""
    SELECT city, SUM(amount) AS revenue, COUNT(*) AS orders
    FROM df JOIN shops USING (shop_id)
    GROUP BY city HAVING SUM(amount) > 90000
    ORDER BY revenue DESC
""").df()
t = df.merge(shops, on="shop_id").groupby("city").agg(revenue=("amount", "sum"), orders=("amount", "size"))
b = t[t["revenue"] > 90_000].sort_values("revenue", ascending=False)
print(a)
print(b)
```

Что получилось: шаги одни и те же, меняется только запись. Если в pandas что-то не выходит, можно сформулировать запрос на SQL, а потом перевести строку за строкой — или оставить SQL: DuckDB работает с теми же таблицами.

::: warn Типичные ошибки
- **`.fetchone()` для таблицы.** Он вернёт только первую строку; таблица целиком — `.df()`.
- **Кавычки.** Строки в SQL — в одинарных кавычках (`'доставка'`), а весь запрос — в тройных двойных `"""…"""`.
- **Имя таблицы ≠ имя переменной.** DuckDB видит DataFrame по имени переменной Python; переименовали переменную — меняйте и запрос.
- **Сравнение после `ROUND`.** `ROUND` в SQL и `round` в Python могут по-разному округлять половинки; сверяйте с допуском.
:::

{{practice: reconcile}}

## Практика

## task: total | Выручка запросом | warmup

Посчитайте `revenue` — сумму `amount` по таблице `df` SQL-запросом через DuckDB.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv')['amount'].sum()
assert close(need('revenue'), want), f'revenue = {need("revenue")}, а нужно {want}.'
assert 'duckdb.sql' in _code, 'Посчитайте через duckdb.sql.'
```

### hint
В запросе таблица называется так же, как переменная Python, — `df`.

### hint
`duckdb.sql("SELECT SUM(amount) FROM df").fetchone()[0]` — `fetchone()` возвращает строку-кортеж, `[0]` — её первое значение.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue = duckdb.sql("SELECT SUM(amount) FROM df").fetchone()[0]
```

## task: group | GROUP BY запросом | warmup

Получите `by_channel` — DataFrame со столбцами `channel` и `orders` (число заказов), отсортированный по убыванию `orders`.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
b = need('by_channel', _pd.DataFrame)
assert list(b.columns) == ['channel', 'orders'], f'Столбцы: {list(b.columns)}.'
want = _pd.read_csv('orders_3m.csv')['channel'].value_counts()
assert b['channel'].tolist() == list(want.index) and [int(x) for x in b['orders']] == [int(x) for x in want.values], f'by_channel не совпадает: {b.values.tolist()}.'
```

### hint
Результат запроса превращается в DataFrame методом `.df()`.

### hint
`SELECT channel, COUNT(*) AS orders FROM df GROUP BY channel ORDER BY orders DESC`, в конце — `.df()`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_channel = duckdb.sql("""
    SELECT channel, COUNT(*) AS orders
    FROM df
    GROUP BY channel
    ORDER BY orders DESC
""").df()
```

## task: p-sql | Соберите запрос к файлу | warmup

Соберите программу, которая выводит число заказов размера L прямо из CSV.

### parsons
```python
import duckdb
query = "SELECT COUNT(*) FROM 'orders_3m.csv' WHERE size = 'L'"
n = duckdb.sql(query).fetchone()[0]
print(n)
```

### check
```python
import pandas as _pd
want = (_pd.read_csv('orders_3m.csv')['size'] == 'L').sum()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Сначала импорт и текст запроса, потом выполнение и вывод.

### hint
Имя файла в запросе — в одинарных кавычках: `FROM 'orders_3m.csv' WHERE size = 'L'`.

## task: join | Города запросом | base

Соберите `by_city` — DataFrame `city`, `revenue` с выручкой по городам, отсортированный по убыванию. Соедините `df` и `shops` в SQL.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

```

### check
```python
import pandas as _pd
f = _pd.read_csv('orders_3m.csv').merge(_pd.read_csv('shops.csv'), on='shop_id')
want = f.groupby('city')['amount'].sum().sort_values(ascending=False)
b = need('by_city', _pd.DataFrame)
assert list(b.columns) == ['city', 'revenue'], f'Столбцы: {list(b.columns)}.'
assert b['city'].tolist() == list(want.index), f'Порядок городов: {b["city"].tolist()}.'
assert all(abs(float(x) - float(y)) < 1e-6 for x, y in zip(b['revenue'], want.values)), 'Выручка не совпадает.'
```

### hint
`FROM df JOIN shops USING (shop_id)` — и обычный `GROUP BY city`.

### hint
Выручку назовите `revenue` (`SUM(amount) AS revenue`) и отсортируйте `ORDER BY revenue DESC`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
by_city = duckdb.sql("""
    SELECT s.city, SUM(d.amount) AS revenue
    FROM df AS d
    JOIN shops AS s USING (shop_id)
    GROUP BY s.city
    ORDER BY revenue DESC
""").df()
```

### explain
Казань лидирует (279 705 ₽), за ней Пермь (261 540 ₽). Запрос — привычный SQL, только таблицы — это DataFrame в памяти Python: никакой базы данных поднимать не нужно.

## task: having | HAVING | base

Получите `rare` — **список** напитков (по алфавиту), которые заказывали меньше 100 раз, одним SQL-запросом с `HAVING`.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
vc = _pd.read_csv('orders_3m.csv')['drink'].value_counts()
want = sorted(vc[vc < 100].index)
assert need('rare') == want, f'rare = {need("rare")}, а нужно {want}.'
assert 'HAVING' in _code.upper(), 'Используйте HAVING.'
```

### hint
`HAVING` фильтрует уже посчитанные группы — как маска после `groupby` в pandas.

### hint
`SELECT drink FROM df GROUP BY drink HAVING COUNT(*) < 100 ORDER BY drink`, затем `.df()["drink"].tolist()`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
rare = duckdb.sql("""
    SELECT drink FROM df
    GROUP BY drink
    HAVING COUNT(*) < 100
    ORDER BY drink
""").df()["drink"].tolist()
```

### explain
Реже 100 раз заказывали матчу (81) и сезонный напиток (82). Тот же результат в pandas — `size()` по напиткам и маска; в SQL — `HAVING`, выбирайте то, что быстрее пишется вам.

## task: from-file | Прямо из файла | base

Не загружая данные в pandas, посчитайте `avg_check_delivery` — средний чек доставки, округлённый до двух знаков (`ROUND` в SQL).

### starter
```python
import duckdb

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = round(d[d['channel'] == 'доставка']['amount'].mean(), 2)
assert close(need('avg_check_delivery'), want, 0.006), f'avg_check_delivery = {need("avg_check_delivery")}, а нужно {want}.'
assert 'read_csv' not in _code, 'Решите без pandas — запросом к файлу.'
```

### hint
DuckDB читает CSV прямо по имени файла в `FROM`.

### hint
`SELECT ROUND(AVG(amount), 2) FROM 'orders_3m.csv' WHERE channel = 'доставка'`, затем `.fetchone()[0]`.

### solution
```python
import duckdb
avg_check_delivery = duckdb.sql("""
    SELECT ROUND(AVG(amount), 2) FROM 'orders_3m.csv' WHERE channel = 'доставка'
""").fetchone()[0]
```

### explain
Средний чек доставки — 337.36 ₽, почти как в зале. Запрос к файлу удобен, когда файл большой: DuckDB читает только нужные столбцы и не загружает всё в память.

## task: reconcile | Сверка двух способов | star

Посчитайте средний чек по каналам двумя способами — pandas (`pd_avg`) и SQL (`sql_avg`), оба как словари «канал → средний чек, округлённый до 2 знаков». Сохраните `match = True`, если результаты совпадают.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv').groupby('channel')['amount'].mean().round(2).to_dict()
p = {k: round(float(v), 2) for k, v in dict(need('pd_avg')).items()}
s = {k: round(float(v), 2) for k, v in dict(need('sql_avg')).items()}
assert p == want, f'pd_avg = {p}.'
assert s == want, f'sql_avg = {s}.'
assert need('match') == True, 'match должно быть True.'
```

### hint
pandas: `df.groupby("channel")["amount"].mean().round(2).to_dict()`.

### hint
SQL: запрос с `ROUND(AVG(amount), 2)`, затем `dict(zip(t["channel"], t["avg"]))`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
pd_avg = df.groupby("channel")["amount"].mean().round(2).to_dict()
t = duckdb.sql("SELECT channel, ROUND(AVG(amount), 2) AS avg FROM df GROUP BY channel").df()
sql_avg = dict(zip(t["channel"], t["avg"]))
match = pd_avg == sql_avg
```

### explain
Порядок ключей у словарей может отличаться — сравнение `==` его не учитывает. Сверка двумя способами — лучшая страховка от ошибок в фильтрах и соединениях перед тем, как отправлять цифры руководству.
