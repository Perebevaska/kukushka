---
title: "Рамки окна SQL: накопительные итоги и скользящие средние"
lead: "Окно может видеть не всю свою группу, а только её часть, привязанную к текущей строке, — рамку. На рамках строятся накопительный итог, скользящее среднее за 7 дней и «первый и последний заказ гостя». Разбираем `ROWS` и `RANGE`, рамку по умолчанию и почему фильтр периода в `WHERE` портит края, а в конце собираем месячный отчёт по кофейням из всех окон сразу."
files: [orders_3m.csv, daily_sales.csv]
recap:
  - "С `ORDER BY` окно по умолчанию — от начала до текущей строки **и всех строк с тем же значением** (`RANGE`). Для накопительного итога по уникальному ключу это то, что нужно; при повторах в ключе пишите `ROWS`."
  - "Скользящее среднее: `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` — 7 строк, `RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW` — 7 календарных дней (с пропусками это разные вещи)."
  - "`LAST_VALUE` с `ORDER BY` и без явной рамки возвращает текущую строку (и её соседей по значению). Нужна рамка `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`."
  - "Фильтр периода в `WHERE` срабатывает до окна, и края периода считаются по неполной рамке. Сначала окно в CTE, потом фильтр снаружи."
  - "Один запрос может держать несколько окон: `WINDOW by_month AS (...), by_shop AS (...)` — доля и место по месяцу, рост к прошлому месяцу по кофейне."
  - "Аналоги в pandas: `cumsum()`, `rolling(7)` и `rolling(\"7D\")`, `transform(\"first\")`/`(\"last\")` — в шпаргалке урока; в задачах они не нужны."
---

В уроке «Оконные функции SQL» окно видело всю свою группу: итог кофейни, место напитка, соседний месяц. Здесь окно сузим до части группы — **рамки**. Запись `OVER (PARTITION BY … ORDER BY …)`, именованное окно `WINDOW` и фильтр `QUALIFY` — оттуда же.

::: note Что здесь обязательно
В задачах урока нужен только SQL. Блоки «Аналог в pandas: …» можно пропустить; аналоги собраны в шпаргалке в разделе про `FIRST_VALUE`.
:::

## Рамки окна: ROWS и RANGE

Зачем: накопительный итог выручки с начала квартала, скользящее среднее за 7 дней — это суммы и средние не по всей группе, а по её **части**, привязанной к текущей строке. Эту часть задаёт **рамка** окна.

::: tip Аналогия
Рамка — как окно в поезде: поезд (текущая строка) едет, и в окне видны то последние 7 столбов (`ROWS` — считаем строки), то всё, что проехали за последние 7 минут (`RANGE` — считаем значения). На равномерной дороге это одно и то же, а если поезд стоял на станции, картинки расходятся.
:::

Синтаксис рамки: `ROWS BETWEEN начало AND конец` или `RANGE BETWEEN начало AND конец`, где границы — это:

| граница | смысл |
|---|---|
| `UNBOUNDED PRECEDING` | с самой первой строки окна |
| `6 PRECEDING` | за 6 строк до текущей (для `RANGE` — за 6 единиц значения) |
| `CURRENT ROW` | текущая строка |
| `1 FOLLOWING` | следующая строка |
| `UNBOUNDED FOLLOWING` | до самой последней строки окна |

### Игрушечный пример руками

Выручка четырёх дней: 100, 120, 90, 150.

1. **Накопительный итог** — рамка от начала до текущей строки: 100; 100 + 120 = 220; 220 + 90 = 310; 310 + 150 = 460.
2. **Скользящее среднее за 3 дня** — рамка `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`: день 1 — только 100 (раньше строк нет), среднее 100; день 2 — (100 + 120) / 2 = 110; день 3 — (100 + 120 + 90) / 3 ≈ 103.3; день 4 — (120 + 90 + 150) / 3 = 120.

```python
import duckdb
import pandas as pd

toy = pd.DataFrame({"day": [1, 2, 3, 4], "revenue": [100, 120, 90, 150]})
duckdb.sql("""
    SELECT day, revenue,
           SUM(revenue) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
           ROUND(AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS ma3
    FROM toy
    ORDER BY day
""").df()
```

::: deep Аналог в pandas: cumsum и rolling
В pandas первая рамка — `cumsum()`, вторая — `rolling(3, min_periods=1).mean()`. `min_periods=1` нужен, чтобы первые дни считались по тем строкам, что есть, — как в SQL; без него там будет `NaN`.

```python
import pandas as pd
toy = pd.DataFrame({"day": [1, 2, 3, 4], "revenue": [100, 120, 90, 150]})
toy["running"] = toy["revenue"].cumsum()
toy["ma3"] = toy["revenue"].rolling(3, min_periods=1).mean().round(1)
toy
```
:::

### Рамка по умолчанию и повторы в ORDER BY

Если в окне есть `ORDER BY`, а рамка не указана, SQL подставляет `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Слово `RANGE` здесь важно: «до текущей строки» значит «до текущего **значения** ключа сортировки включительно». Все строки с тем же значением — **соседи по значению** — попадают в рамку вместе.

Игрушечный пример: заказы (день 1, 100 ₽), (день 1, 50 ₽), (день 2, 70 ₽), накопительная сумма `ORDER BY day`. У обоих заказов первого дня значение ключа одно — «день 1», поэтому для каждого из них в рамку попадают оба: 100 + 50 = 150. У заказа второго дня — 150 + 70 = 220.

::: predict
```python static
import duckdb
import pandas as pd
t = pd.DataFrame({"order_id": ["a", "b", "c"], "day": [1, 1, 2], "amount": [100, 50, 70]})
r = duckdb.sql("""
    SELECT order_id, SUM(amount) OVER (ORDER BY day) AS running
    FROM t ORDER BY order_id
""").fetchall()
for oid, s in r:
    print(oid, s)
```

- `a 100 | b 150 | c 220`
- [x] `a 150 | b 150 | c 220`
- `a 100 | b 50 | c 70`

Почему: без явной рамки работает `RANGE ... CURRENT ROW`. Заказы `a` и `b` — оба из дня 1, это одно значение ключа, поэтому каждый видит сумму обоих: 150.
:::

Для накопительного итога **по дням** это ровно то, что нужно: каждый день получает итог на конец дня. А вот если нужен итог «после каждого заказа», ключ должен быть уникальным (время заказа, номер заказа) или рамка — `ROWS`. Но `ROWS` при повторах в ключе сортировки складывает строки одного дня в случайном порядке — значит, нужен ещё и уникальный второй ключ.

На трёх месяцах заказов — накопительная выручка сети по дням:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
duckdb.sql("""
    WITH d AS (
        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        GROUP BY day
    )
    SELECT day, revenue,
           SUM(revenue) OVER (ORDER BY day) AS running   -- day уникален: RANGE и ROWS совпадут
    FROM d
    ORDER BY day
""").df()
```

Как читать результат: в первую строку попадает выручка 1 сентября (6608 ₽), в последнюю — итог трёх месяцев, 710 195 ₽. Половину этой суммы сеть набрала к 18 октября — чуть позже середины периода: выручка к концу квартала росла.

### Скользящее среднее: строки против календаря

Скользящее среднее за 7 дней сглаживает колебания будней и выходных. Его можно задать двумя рамками:

- `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` — **7 строк**: текущая и 6 предыдущих;
- `RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW` — все строки, чья дата не раньше чем за 6 **дней** до текущей.

Если у каждого дня есть строка, результаты совпадают. Но в UFA-1 бывают дни без заказов — для этих дней в таблице «кофейня × день» строк нет вовсе:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
duckdb.sql("""
    WITH d AS (
        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        WHERE shop_id = 'UFA-1'
        GROUP BY day
    )
    SELECT day, revenue,
           ROUND(AVG(revenue) OVER (ORDER BY day ROWS  BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS ma_rows,
           ROUND(AVG(revenue) OVER (ORDER BY day RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW), 1) AS ma_range
    FROM d
    ORDER BY day
    LIMIT 12
""").df()
```

Что здесь происходит:

- Пока дни идут подряд (1–8 сентября), столбцы совпадают.
- 9 сентября в UFA-1 не было ни одного заказа. Для 10 сентября рамка `ROWS` берёт текущую строку и 6 предыдущих и дотягивается до 3 сентября — это уже 8 календарных дней: среднее 736.9 ₽. Рамка `RANGE` берёт только 4–10 сентября, в них 6 строк: среднее 590.7 ₽.
- `INTERVAL 6 DAYS` работает, потому что `day` — дата. DuckDB поймёт и `RANGE BETWEEN 6 PRECEDING ...` по дате — число он считает днями. Но это его особенность: PostgreSQL для даты требует интервал. Пишите `INTERVAL 6 DAYS` — так запрос переедет в другую базу без правок.

::: figure frame-rows-range
Первые десять дней сентября в UFA-1; у 9 сентября строки нет. Для текущей строки (10 сентября) рамка `ROWS` отсчитывает 7 строк назад и захватывает 3 сентября — это 8 календарных дней. Рамка `RANGE` отсчитывает 6 дней по дате: 4–10 сентября, в них 6 строк. Отсюда 736.9 ₽ против 590.7 ₽.
:::

::: deep Аналог в pandas: rolling("7D")
В pandas календарная рамка — `rolling("7D")` по столбцу дат: окно «7 дней до текущей даты включительно».

```python
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
u = (df[df["shop_id"] == "UFA-1"]
       .groupby(df["datetime"].dt.normalize())["amount"].sum()
       .rename("revenue"))                         # индекс — даты
ma = pd.DataFrame({
    "revenue": u,
    "ma_rows": u.rolling(7, min_periods=1).mean().round(1),   # ROWS: 7 строк
    "ma_range": u.rolling("7D").mean().round(1),              # RANGE: 7 календарных дней
})
ma.head(12)
```
:::

::: deep Что делать с пустыми днями
Даже `RANGE` усредняет только дни, в которые были заказы: день без заказов в него не входит, хотя выручка в этот день — ноль. Если нужно «среднее с учётом нулей», считают `SUM(revenue) OVER (... RANGE ...) / 7` или заранее достраивают календарь: `generate_series` в DuckDB, `reindex(pd.date_range(...), fill_value=0)` в pandas.
:::

::: quiz
По таблице «кофейня × день» считают скользящее среднее `AVG(revenue) OVER (PARTITION BY shop_id ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`. В некоторые дни в кофейне не было заказов. Что не так?

- [x] Для дней после пропуска рамка захватит больше 7 календарных дней: `ROWS` считает строки, а не даты
  > Строк для пустых дней в таблице нет, и 7 строк растягиваются на 8–9 дней. Календарную неделю даёт `RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW` или достроенный календарь.
- [ ] Всё верно: `ROWS BETWEEN 6 PRECEDING` — это ровно 7 дней
  > Ровно 7 строк. Днями они становятся, только если у каждого дня есть строка.
- [ ] Нужен `LAG(revenue, 6)` вместо рамки
  > `LAG` вернёт одно значение шесть строк назад, а не среднее, и споткнётся о пропуски так же.
- [ ] Ошибка в `PARTITION BY`: со скользящим средним его не используют
  > Используют: без него окно одной кофейни захватывало бы последние дни соседней.
:::

Последняя ловушка рамок — фильтр периода. Отчёт нужен «с 1 октября», и рука сама пишет `WHERE day >= '2026-10-01'` в том же запросе, где считается скользящее среднее. Но `WHERE` выполняется раньше окон: сентябрьские строки выброшены до того, как рамка их увидела.

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
d = duckdb.sql("""
    SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
    FROM df
    GROUP BY day
""").df()

wrong = duckdb.sql("""
    SELECT day, ROUND(AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS ma7
    FROM d
    WHERE day >= DATE '2026-10-01'          -- фильтр до окна
    ORDER BY day
""").df()

right = duckdb.sql("""
    WITH w AS (                              -- окно по всем дням
        SELECT day, ROUND(AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS ma7
        FROM d
    )
    SELECT * FROM w
    WHERE day >= DATE '2026-10-01'          -- фильтр после окна
    ORDER BY day
""").df()
print(wrong.head(7))
print(right.head(7))
```

Что получилось: у 1 октября в первом запросе «скользящее среднее» — 6221.0 ₽, это выручка одного дня. Во втором — 7610.1 ₽, честное среднее за 25 сентября – 1 октября. Расходятся первые шесть дней периода, а с 7 октября значения совпадают: рамка целиком помещается внутри октября.

::: figure window-filter-edge
Выручка сети по дням вокруг 1 октября. Сверху `WHERE` отбросил сентябрь раньше окна, и рамка 1 октября состоит из одной строки — 6221.0 ₽. Снизу окно посчитано в CTE по всем дням, а период отобран снаружи: рамка 1 октября — семь строк с 25 сентября, среднее 7610.1 ₽.
:::

::: warn Типичные ошибки
- **Повторы в ключе сортировки.** `SUM(amount) OVER (ORDER BY day)` по заказам даёт всем заказам дня одно и то же значение. Это не ошибка, а `RANGE` по умолчанию. Нужен итог после каждого заказа — сортируйте по уникальному ключу.
- **Фильтр периода до окна.** `WHERE day >= '2026-10-01'` срабатывает раньше окна, и у 1 октября «скользящее за 7 дней» посчитано по одному дню. Окно считают по всем данным в CTE, а период отбирают снаружи.
- **`rolling(7)` без `min_periods`.** Первые 6 значений — `NaN`, тогда как SQL посчитает их по неполной рамке. При сверке SQL и pandas это расхождение легко принять за ошибку.
:::

{{practice: w-running, w-ma7, w-range}}

## FIRST_VALUE и LAST_VALUE

Зачем: «с какого напитка гость начал знакомство с сетью и на каком остановился?» Нужно первое и последнее значение в группе, упорядоченной по времени. Их возвращают `FIRST_VALUE` и `LAST_VALUE`. Главная ловушка этого раздела — опять рамка по умолчанию.

### Игрушечный пример руками

Гость заказывал три дня подряд: латте, раф, чай. С `ORDER BY day` рамка по умолчанию — от первой строки до текущей:

| день | напиток | рамка | `FIRST_VALUE` | `LAST_VALUE` без рамки | `LAST_VALUE` с полной рамкой |
|---|---|---|---|---|---|
| 1 | латте | день 1 | латте | латте | чай |
| 2 | раф | дни 1–2 | латте | **раф** | чай |
| 3 | чай | дни 1–3 | латте | чай | чай |

`FIRST_VALUE` правильный в любой строке: начало рамки всегда первая строка. А «последнее значение рамки» без явной рамки — это текущая строка: `LAST_VALUE` просто повторяет столбец. Чтобы он увидел весь ряд, рамку растягивают до конца: `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.

::: figure frame-default
Рамка как матрица: строка — текущая строка, закрашенные клетки — строки, попавшие в её рамку. Слева — пример из прошлого раздела. Без явной рамки окно идёт до текущего **значения** `day`, поэтому заказы `a` и `b` из дня 1 видят друг друга, и у обоих 150. Справа — `LAST_VALUE`. Без рамки последняя закрашенная клетка — сама текущая строка (у дня 2 — «раф»). С полной рамкой у всех строк последняя клетка — «чай».
:::

```python
import duckdb
import pandas as pd

toy = pd.DataFrame({"day": [1, 2, 3], "drink": ["латте", "раф", "чай"]})
duckdb.sql("""
    SELECT day, drink,
           FIRST_VALUE(drink) OVER (ORDER BY day) AS first_drink,
           LAST_VALUE(drink)  OVER (ORDER BY day) AS last_wrong,
           LAST_VALUE(drink)  OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING
                                                     AND UNBOUNDED FOLLOWING) AS last_drink
    FROM toy
    ORDER BY day
""").df()
```

### На реальных данных: первый и последний напиток гостя

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
fl = duckdb.sql("""
    SELECT DISTINCT client_id,
           FIRST_VALUE(drink) OVER w AS first_drink,
           LAST_VALUE(drink)  OVER w AS last_drink,
           COUNT(*)           OVER w AS orders
    FROM df
    WHERE client_id IS NOT NULL
    WINDOW w AS (PARTITION BY client_id ORDER BY datetime
                 ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    ORDER BY client_id
""").df()
print(len(fl))
fl.head()
```

Что здесь происходит:

- Окно `w` описано один раз и используется тремя функциями. С полной рамкой в каждой строке гостя видны все его заказы.
- В каждой строке гостя все три значения одинаковые, поэтому `DISTINCT` оставляет по одной строке на гостя: 260 строк.
- `COUNT(*) OVER w` с полной рамкой — число заказов гостя. Это тот же `COUNT`, что и в `GROUP BY`, только без свёртки.

Как читать результат: у каждого из 260 гостей видно, с чего он начал и чем закончил. В задаче вы посчитаете, у какой доли гостей с двумя заказами и больше эти напитки различаются.

::: deep Аналог в pandas: first и last
В pandas первый и последний элемент группы дают `"first"` и `"last"` — после сортировки по времени. Рамки в pandas нет: группа всегда видна целиком.

```python
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
c = df.dropna(subset=["client_id"]).sort_values("datetime")
fl = c.groupby("client_id").agg(first_drink=("drink", "first"),
                                last_drink=("drink", "last"),
                                orders=("drink", "size"))
fl.head()
```
:::

### Шпаргалка: рамки → pandas

Для справки, запоминать не нужно: в задачах этого урока pandas-аналоги не требуются. Аналоги долей, рангов, `NTILE` и `LAG` — в шпаргалке урока «Оконные функции SQL».

| SQL | pandas |
|---|---|
| `SUM(x) OVER (ORDER BY t)` | `groupby(g)[x].cumsum()` после сортировки |
| `AVG(x) OVER (... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` | `rolling(7, min_periods=1).mean()` |
| `AVG(x) OVER (... RANGE BETWEEN INTERVAL 6 DAYS PRECEDING ...)` | `rolling("7D").mean()` по датам |
| `FIRST_VALUE` / `LAST_VALUE` с полной рамкой | `groupby(g)[x].transform("first")` / `("last")` |

::: warn Типичные ошибки
- **`LAST_VALUE` без полной рамки.** Возвращает текущую строку, и «последний напиток» каждой строки равен её собственному. Симптом: `last_drink` совпадает со столбцом `drink`.
- **Забыли `DISTINCT` или `QUALIFY ROW_NUMBER() ... = 1`.** Оконная функция не сворачивает строки: у гостя с 12 заказами будет 12 одинаковых строк.
- **`FIRST_VALUE` без второго ключа сортировки.** Если у гостя два заказа в одну минуту, «первый» выбирается случайно.
:::

{{practice: w-firstlast}}

## Разберём вместе: месячный отчёт по кофейням

Этот разбор собирает окна обоих уроков: доля, место (`RANK`), `LAG` и именованное окно `WINDOW` — из урока «Оконные функции SQL». Задача: для каждой кофейни и каждого месяца показать выручку, долю кофейни в выручке сети за месяц, место среди кофеен в этом месяце и рост к прошлому месяцу. Четыре показателя — три разных окна, и все они строятся над одной таблицей «кофейня × месяц».

1. **Таблица «кофейня × месяц».** CTE `m` с `GROUP BY shop_id, month`: 6 кофеен × 3 месяца = 18 строк.
2. **Доля в сети за месяц.** Итог месяца — сумма по всем кофейням **этого месяца**: окно `PARTITION BY month`. Доля = `revenue / SUM(revenue) OVER by_month`.
3. **Место в месяце.** То же окно, но с порядком: `RANK() OVER (by_month ORDER BY revenue DESC)`. Именованное окно можно дополнить своим `ORDER BY`.
4. **Рост к прошлому месяцу.** Окно другое: своя кофейня, по порядку месяцев — `PARTITION BY shop_id ORDER BY month`, и в нём `LAG`.

::: figure window-report-grid
Таблица «кофейня × месяц» как сетка 6 × 3. Окно `by_month` — столбец: шесть кофеен одного месяца. В нём считаются итог месяца для доли и место (`RANK`), у ноября места подписаны рядом с выручкой. Окно `by_shop` — строка: три месяца одной кофейни по порядку. В нём `LAG` берёт соседа слева, отсюда рост UFA-1: +32.8 % в октябре и +0.1 % в ноябре.
:::

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
report = duckdb.sql("""
    WITH m AS (
        SELECT shop_id, date_trunc('month', datetime) AS month, SUM(amount) AS revenue
        FROM df
        GROUP BY shop_id, month
    )
    SELECT shop_id, month, revenue,
           ROUND(100 * revenue / SUM(revenue) OVER by_month, 1)         AS pct_net,
           RANK() OVER (by_month ORDER BY revenue DESC)                 AS place,
           ROUND(100 * (revenue / LAG(revenue) OVER by_shop - 1), 1)    AS growth_pct
    FROM m
    WINDOW by_month AS (PARTITION BY month),
           by_shop  AS (PARTITION BY shop_id ORDER BY month)
    ORDER BY month, place
""").df()
report.tail(6)
```

Что получилось: в ноябре лидер сменился — KZN-1 (68 368 ₽, 26.7 % сети) обошла PRM-1, которая лидировала в сентябре и октябре. UFA-1 в ноябре почти не выросла (+0.1 %), но всё равно поднялась на пятое место, потому что PRM-2 просела на 6.0 %.

::: deep Аналог в pandas: весь отчёт
Три отдельных шага, по одному на окно:

```python
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
m = (df.groupby(["shop_id", df["datetime"].dt.to_period("M").rename("month")])["amount"]
       .sum().rename("revenue").reset_index().sort_values(["shop_id", "month"]))
m["pct_net"] = (100 * m["revenue"] / m.groupby("month")["revenue"].transform("sum")).round(1)
m["place"] = m.groupby("month")["revenue"].rank(method="min", ascending=False).astype(int)
m["growth_pct"] = (100 * (m["revenue"] / m.groupby("shop_id")["revenue"].shift(1) - 1)).round(1)
m.sort_values(["month", "place"]).tail(6)
```
:::

SQL-версия держит весь отчёт в одном запросе, и его можно перенести в рабочую базу почти без изменений: заменить `date_trunc` на функцию дат её диалекта и проверить, понимает ли она именованные окна `WINDOW` (PostgreSQL понимает, SQL Server — с версии 2022; иначе окно расписывают в каждом `OVER`).

## Практика

## task: w-running | Накопительная выручка сети | warmup

Посчитайте `cum` — DataFrame со столбцами `day`, `revenue`, `running`: выручка сети по дням и накопительный итог с начала периода, по возрастанию дня. Затем найдите `half_day` — первый день, когда накопленная выручка достигла половины выручки за весь период.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

cum = duckdb.sql("""
    WITH d AS (
        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        GROUP BY day
    )
    SELECT day, revenue, ... AS running
    FROM d
    ORDER BY day
""").df()
half_day = ...
print(half_day)
```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
_r = _d.groupby(_d['datetime'].dt.normalize())['amount'].sum().cumsum()
b = need('cum', _pd.DataFrame)
assert list(b.columns) == ['day', 'revenue', 'running'], f'Столбцы: {list(b.columns)}.'
assert len(b) == len(_r), f'Строк {len(b)}, а дней с заказами {len(_r)}.'
assert all(abs(float(a) - y) < 1e-6 for a, y in zip(b['running'], _r.values)), 'running не совпадает с накопительным итогом. Окно: SUM(revenue) OVER (ORDER BY day).'
_h = _r[_r >= _r.iloc[-1] / 2].index[0]
assert str(need('half_day'))[:10] == str(_h.date()), f'half_day = {need("half_day")}, а половина выручки набрана в другой день.'
```

### hint
Накопительный итог — сумма от первой строки до текущей в порядке дней: окно с `ORDER BY day`.

### hint
`SUM(revenue) OVER (ORDER BY day) AS running`. Первый день, где `running` не меньше половины `revenue.sum()`: `cum.loc[cum["running"] >= cum["revenue"].sum() / 2, "day"].iloc[0]`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

cum = duckdb.sql("""
    WITH d AS (
        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        GROUP BY day
    )
    SELECT day, revenue, SUM(revenue) OVER (ORDER BY day) AS running
    FROM d
    ORDER BY day
""").df()
half_day = cum.loc[cum["running"] >= cum["revenue"].sum() / 2, "day"].iloc[0]
print(half_day)
```

## task: w-ma7 | Скользящее среднее с правильным началом | base

Новый файл `daily_sales.csv` — дневная выручка шести кофеен за 2024–2025 годы: по строке на пару «кофейня × день», без пропусков. Столбец `revenue_k` — выручка дня в **тысячах рублей**; остальные столбцы (город, формат, погода, праздник, акция) в этой задаче не нужны.

Посчитайте 7-дневное скользящее среднее `revenue_k` кофейни TMN-1 и покажите его **за декабрь 2025 года**. Результат `dec` — DataFrame со столбцами `date`, `revenue_k`, `ma7` (среднее за текущий и 6 предыдущих дней, округлённое до 1 знака), 31 строка по возрастанию даты. Среднее для 1 декабря должно учитывать последние дни ноября. Сохраните `peak_date` — дату с максимальным `ma7` в декабре.

### starter
```python
import duckdb
import pandas as pd
ds = pd.read_csv("daily_sales.csv", parse_dates=["date"])

```

### check
```python
import pandas as _pd
_s = _pd.read_csv('daily_sales.csv', parse_dates=['date'])
_s = _s[_s['shop_id'] == 'TMN-1'].sort_values('date').set_index('date')['revenue_k']
_ma = _s.rolling(7, min_periods=1).mean().round(1)
_dec = _ma['2025-12-01':'2025-12-31']
b = need('dec', _pd.DataFrame)
assert list(b.columns) == ['date', 'revenue_k', 'ma7'], f'Столбцы: {list(b.columns)}.'
assert len(b) == 31, f'Строк {len(b)}, а в декабре 31 день.'
_first = float(b['ma7'].iloc[0])
assert abs(_first - float(_s.loc['2025-12-01'])) > 0.05 or abs(_dec.iloc[0] - float(_s.loc['2025-12-01'])) < 0.05, 'ma7 1 декабря равно выручке одного дня: окно посчитано уже после фильтра по декабрю. Посчитайте окно по всем дням, а декабрь отберите снаружи.'
assert all(abs(float(a) - y) < 0.051 for a, y in zip(b['ma7'], _dec.values)), 'ma7 не совпадает с ожидаемым. Рамка: ROWS BETWEEN 6 PRECEDING AND CURRENT ROW, окно — по всем дням TMN-1.'
assert str(need('peak_date'))[:10] == str(_dec.idxmax().date()), f'peak_date = {need("peak_date")}, а максимум ma7 в другой день.'
```

### hint
`WHERE` выполняется раньше окна. Если отфильтровать декабрь сразу, окно 1 декабря увидит только один день. Значит, окно — во внутреннем запросе по всем дням TMN-1, а декабрь — во внешнем.

### hint
Внутри CTE: `AVG(revenue_k) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` с `WHERE shop_id = 'TMN-1'`. Снаружи: `WHERE date >= '2025-12-01'`. Пик — `dec.loc[dec["ma7"].idxmax(), "date"]`.

### hint
```python
dec = duckdb.sql("""
    WITH t AS (
        SELECT date, revenue_k,
               ROUND(AVG(revenue_k) OVER (ORDER BY date ROWS BETWEEN ... AND CURRENT ROW), 1) AS ma7
        FROM ds
        WHERE shop_id = 'TMN-1'
    )
    SELECT * FROM t
    WHERE ...
    ORDER BY date
""").df()
```

### solution
```python
import duckdb
import pandas as pd
ds = pd.read_csv("daily_sales.csv", parse_dates=["date"])

dec = duckdb.sql("""
    WITH t AS (
        SELECT date, revenue_k,
               ROUND(AVG(revenue_k) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS ma7
        FROM ds
        WHERE shop_id = 'TMN-1'
    )
    SELECT date, revenue_k, ma7
    FROM t
    WHERE date >= '2025-12-01' AND date < '2026-01-01'
    ORDER BY date
""").df()
peak_date = dec.loc[dec["ma7"].idxmax(), "date"]
print(peak_date)
```

### explain
Пик сглаженной выручки TMN-1 в декабре — 26 декабря, 79.4 тыс. ₽ в среднем за неделю: предновогодние дни. Если поставить `date >= '2025-12-01'` в тот же `WHERE`, что и `shop_id`, окно 1 декабря увидит только одну строку, и `ma7` первого дня совпадёт с его выручкой, а первые шесть дней месяца будут посчитаны по неполной неделе. Ошибки при этом не будет — только неверные цифры в начале периода. В pandas то же — `rolling(7, min_periods=1).mean()` по всему ряду и срез декабря после.

## task: w-range | Неделя строками и неделя календарём | plus

У UFA-1 есть дни без заказов. Посчитайте `ufa` — DataFrame со столбцами `day`, `revenue`, `ma_rows`, `ma_range` по заказам UFA-1 из `orders_3m.csv`: дневная выручка и два скользящих средних — по 7 **строкам** и по 7 **календарным дням** (текущий и 6 предыдущих), по возрастанию дня, без округления. Сохраните `differ` — число дней, где два средних различаются больше чем на 1 ₽.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
_u = _d[_d['shop_id'] == 'UFA-1'].groupby(_d['datetime'].dt.normalize())['amount'].sum()
_r = _u.rolling(7, min_periods=1).mean()
_g = _u.rolling('7D').mean()
b = need('ufa', _pd.DataFrame)
assert list(b.columns) == ['day', 'revenue', 'ma_rows', 'ma_range'], f'Столбцы: {list(b.columns)}.'
assert len(b) == len(_u), f'Строк {len(b)}, а дней с заказами в UFA-1 {len(_u)}.'
assert all(abs(float(a) - y) < 0.01 for a, y in zip(b['ma_rows'], _r.values)), 'ma_rows не совпадает: рамка ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.'
assert all(abs(float(a) - y) < 0.01 for a, y in zip(b['ma_range'], _g.values)), 'ma_range не совпадает: рамка RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW, ключ сортировки — дата.'
_w = int(((_r - _g).abs() > 1).sum())
assert int(need('differ')) == _w, f'differ = {need("differ")}, а дней с расхождением больше 1 ₽ — {_w}.'
```

### hint
Сначала CTE с дневной выручкой UFA-1 (`CAST(datetime AS DATE) AS day`). Потом два окна с одинаковым `ORDER BY day` и разными рамками.

### hint
`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` и `RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW`. Расхождения: `((ufa["ma_rows"] - ufa["ma_range"]).abs() > 1).sum()`.

### hint
```python
ufa = duckdb.sql("""
    WITH d AS (
        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df WHERE shop_id = 'UFA-1' GROUP BY day
    )
    SELECT day, revenue,
           AVG(revenue) OVER (ORDER BY day ROWS BETWEEN ...) AS ma_rows,
           AVG(revenue) OVER (ORDER BY day RANGE BETWEEN ...) AS ma_range
    FROM d ORDER BY day
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

ufa = duckdb.sql("""
    WITH d AS (
        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        WHERE shop_id = 'UFA-1'
        GROUP BY day
    )
    SELECT day, revenue,
           AVG(revenue) OVER (ORDER BY day ROWS  BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_rows,
           AVG(revenue) OVER (ORDER BY day RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW) AS ma_range
    FROM d
    ORDER BY day
""").df()
differ = int(((ufa["ma_rows"] - ufa["ma_range"]).abs() > 1).sum())
print(differ)
```

### explain
У UFA-1 87 дней с заказами из 91, и четыре пустых дня портят «неделю строками» в 18 днях из 87 — в каждом из них 7 строк растянулись больше чем на 7 календарных дней. Например, 10 сентября: 736.9 ₽ по строкам против 590.7 ₽ по календарю. Если ваш отчёт подписан «за неделю», правильна рамка `RANGE`. В pandas — `rolling("7D")` по индексу-дате. А если нужен честный учёт дней без заказов (выручка 0), делите `SUM(...)` в рамке `RANGE` на 7.

## task: w-firstlast | С чего начал и чем закончил | plus

Для каждого гостя с картой найдите первый и последний напиток по времени заказа. Результат `fl` — DataFrame со столбцами `client_id`, `first_drink`, `last_drink`, `orders` (число заказов гостя), по одной строке на гостя, по возрастанию `client_id`. Используйте `FIRST_VALUE` и `LAST_VALUE`. Затем посчитайте `switch_pct` — долю (%, один знак) гостей **с двумя заказами и больше**, у которых последний напиток отличается от первого.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
_c = _pd.read_csv('orders_3m.csv', parse_dates=['datetime']).dropna(subset=['client_id']).sort_values('datetime')
_w = _c.groupby('client_id').agg(f=('drink', 'first'), l=('drink', 'last'), n=('drink', 'size')).sort_index()
b = need('fl', _pd.DataFrame)
assert list(b.columns) == ['client_id', 'first_drink', 'last_drink', 'orders'], f'Столбцы: {list(b.columns)}.'
assert len(b) == len(_w), f'Строк {len(b)}, а гостей с картой {len(_w)}. Нужна одна строка на гостя: DISTINCT или QUALIFY ROW_NUMBER() ... = 1.'
assert b['client_id'].tolist() == list(_w.index), 'Порядок строк: по возрастанию client_id.'
assert b['first_drink'].tolist() == _w['f'].tolist(), 'first_drink не совпадает. Окно: PARTITION BY client_id ORDER BY datetime.'
assert b['last_drink'].tolist() == _w['l'].tolist(), 'last_drink не совпадает. Если он равен напитку из той же строки, а не последнему заказу гостя, — у LAST_VALUE не та рамка: нужна ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.'
assert [int(x) for x in b['orders']] == _w['n'].tolist(), 'orders не совпадает с числом заказов гостя.'
_r = _w[_w['n'] >= 2]
_p = round(100 * (_r['f'] != _r['l']).mean(), 1)
assert abs(float(need('switch_pct')) - _p) < 0.051, f'switch_pct = {need("switch_pct")}. Считайте долю только среди гостей с orders >= 2.'
assert 'LAST_VALUE' in _code.upper(), 'Решите задачу через LAST_VALUE — в этом её смысл.'
```

### hint
Опишите одно окно `WINDOW w AS (PARTITION BY client_id ORDER BY datetime ROWS BETWEEN ...)` с полной рамкой и используйте его в трёх функциях.

### hint
`FIRST_VALUE(drink) OVER w`, `LAST_VALUE(drink) OVER w`, `COUNT(*) OVER w`; одна строка на гостя — `SELECT DISTINCT`. Доля: `r = fl[fl["orders"] >= 2]`, затем `100 * (r["first_drink"] != r["last_drink"]).mean()`.

### hint
```python
fl = duckdb.sql("""
    SELECT DISTINCT client_id,
           FIRST_VALUE(drink) OVER w AS first_drink,
           LAST_VALUE(drink)  OVER w AS last_drink,
           COUNT(*)           OVER w AS orders
    FROM df
    WHERE client_id IS NOT NULL
    WINDOW w AS (PARTITION BY client_id ORDER BY datetime
                 ROWS BETWEEN ... AND ...)
    ORDER BY client_id
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

fl = duckdb.sql("""
    SELECT DISTINCT client_id,
           FIRST_VALUE(drink) OVER w AS first_drink,
           LAST_VALUE(drink)  OVER w AS last_drink,
           COUNT(*)           OVER w AS orders
    FROM df
    WHERE client_id IS NOT NULL
    WINDOW w AS (PARTITION BY client_id ORDER BY datetime
                 ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    ORDER BY client_id
""").df()
r = fl[fl["orders"] >= 2]
switch_pct = round(100 * float((r["first_drink"] != r["last_drink"]).mean()), 1)
print(switch_pct)
```

### explain
Из 253 гостей с двумя заказами и больше 88.5 % закончили не тем напитком, с которого начали: гости в этих данных охотно пробуют меню. Гостей с одним заказом мы исключили, ведь у них первый и последний напиток — это один заказ, и они занизили бы долю. Без полной рамки `LAST_VALUE` вернул бы напиток текущей строки, а `COUNT(*) OVER w` с той же рамкой стал бы накопительным счётчиком 1, 2, 3, … Тогда строки гостя перестали бы совпадать, и `DISTINCT` не свернул бы ничего: вместо 260 строк получилось бы 1247 — по строке на заказ. Эту ошибку ловит первая же проверка числа строк. В pandas: сортировка по времени и `groupby("client_id")["drink"].agg(["first", "last", "size"])`.
