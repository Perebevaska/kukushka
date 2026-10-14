---
title: "Подзапросы, CTE и порядок выполнения SQL"
lead: "Когда вопрос не решается одним `GROUP BY`, нужен запрос внутри запроса. Разбираем подзапросы в `WHERE`, `IN` и `FROM`, CTE `WITH` для цепочки шагов, ловушку `NOT IN` с `NULL`, топ-1 в каждой группе через `ROW_NUMBER` и порядок, в котором база на самом деле выполняет запрос. Все запросы — в DuckDB по датафреймам, как в прошлом уроке."
files: [orders_3m.csv, shops.csv, menu.csv]
recap:
  - "Топ-1 в каждой группе: `ROW_NUMBER() OVER (PARTITION BY группа ORDER BY … DESC, второй_ключ)` и `WHERE rn = 1` во внешнем запросе. Остальные оконные функции — в уроке «Оконные функции SQL»."
  - "Подзапрос — запрос в скобках: одно число в `WHERE x > (…)`, список в `IN (…)`, таблица в `FROM (…)`. CTE `WITH имя AS (…)` — тот же подзапрос с именем; шаги через запятую."
  - "`NOT IN` со списком, где есть `NULL`, не пропускает ни одной строки: добавьте в подзапрос `IS NOT NULL` или пишите `NOT EXISTS`."
  - "Порядок выполнения: FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT (и окна) → DISTINCT → ORDER BY → LIMIT. Поэтому агрегаты фильтруют в HAVING, а по оконной функции — уровнем выше (CTE)."
  - "`EXPLAIN запрос` показывает план выполнения; читают снизу вверх, от чтения таблицы к результату."
---

В уроке «SQL прямо по датафрейму — DuckDB» каждый вопрос решался одним запросом: `SELECT … FROM df GROUP BY …`. Здесь вопросы в два-три шага. Запросы пишем так же: `duckdb.sql("…")`, таблицы — датафреймы по имени переменной, результат — `.df()` или `.fetchone()[0]`.

## Подзапросы и CTE

Зачем: вопрос «сколько заказов дороже среднего чека?» требует двух шагов. Сначала посчитать средний чек, потом отобрать заказы дороже него. Можно выполнить два запроса и переписать число из первого во второй руками. Но тогда при новой выгрузке число устареет. **Подзапрос** — это запрос внутри запроса: база сама посчитает первый шаг и подставит результат во второй.

::: sql
Всё это — обычный SQL, который вы, скорее всего, писали в SQL Server или PostgreSQL. В DuckDB он работает так же; разница только в том, что таблицы — это датафреймы и CSV-файлы.
:::

### Игрушечный пример руками

Пять заказов на 200, 300, 400, 500 и 600 ₽.

1. Средний чек: (200 + 300 + 400 + 500 + 600) / 5 = 2000 / 5 = **400 ₽**.
2. Дороже 400 ₽ — заказы на 500 и 600 ₽, то есть **2 заказа**. Заказ на 400 ₽ не проходит: `>` строгое.

То же одним запросом: внутренний `SELECT` в скобках считает 400, внешний сравнивает с ним каждую строку.

```python
import duckdb
import pandas as pd

toy = pd.DataFrame({"amount": [200, 300, 400, 500, 600]})
n = duckdb.sql("""
    SELECT COUNT(*)
    FROM toy
    WHERE amount > (SELECT AVG(amount) FROM toy)   -- подзапрос вернёт одно число: 400
""").fetchone()[0]
print(n)
```

Что здесь происходит:

- `(SELECT AVG(amount) FROM toy)` — **скалярный подзапрос**: он возвращает одну строку с одним столбцом, то есть одно число. Его можно поставить везде, где стоит число.
- Внешний запрос сравнивает `amount` каждой строки с этим числом и считает подходящие строки.

### Три места, где живут подзапросы

| где | что возвращает | пример |
|---|---|---|
| в `WHERE … > (…)` | одно значение | `amount > (SELECT AVG(amount) FROM df)` |
| в `WHERE … IN (…)` | список значений — один столбец | `shop_id IN (SELECT shop_id FROM shops WHERE city = 'Казань')` |
| в `FROM (…) AS t` | целую таблицу | `FROM (SELECT shop_id, SUM(amount) AS revenue FROM df GROUP BY shop_id) AS t` |

::: figure subquery-kinds
Форма результата подзапроса решает, где его можно поставить. Ячейка 1 × 1 — средний чек 339.97 ₽ — встаёт вместо числа в сравнении. Столбец — две казанские кофейни — служит списком для `IN`. Таблица из шести строк «кофейня — выручка» читается во `FROM`, как обычная таблица, и обязательно получает псевдоним.
:::

На реальных данных: сколько заказов дороже среднего по сети и сколько заказов было в казанских кофейнях. Список кофеен Казани запрос берёт из справочника, а не из нашей памяти:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

above = duckdb.sql("""
    SELECT COUNT(*) FROM df
    WHERE amount > (SELECT AVG(amount) FROM df)
""").fetchone()[0]

kazan = duckdb.sql("""
    SELECT COUNT(*) AS orders, SUM(amount) AS revenue
    FROM df
    WHERE shop_id IN (SELECT shop_id FROM shops WHERE city = 'Казань')
""").df()
print(above)
print(kazan)
```

Что получилось: средний чек сети — около 340 ₽, дороже него 702 заказа из 2089, то есть примерно треть. Казанские кофейни дали 833 заказа на 279 705 ₽ — ту же выручку, что и JOIN по городам в уроке «SQL прямо по датафрейму — DuckDB». Откроется в Казани третья кофейня — запрос подхватит её из справочника сам.

::: predict
```python static
import duckdb
import pandas as pd
t = pd.DataFrame({"x": [10, 20, 30, 40]})
print(duckdb.sql("SELECT COUNT(*) FROM t WHERE x >= (SELECT AVG(x) FROM t)").fetchone()[0])
```

- `3`
- [x] `2`
- `4`

Почему: среднее — (10 + 20 + 30 + 40) / 4 = 25. Не меньше 25 только 30 и 40.
:::

### CTE: подзапрос с именем

Когда шагов больше двух, подзапросы вкладываются друг в друга, и запрос приходится читать изнутри наружу. **CTE** (common table expression, «обобщённое табличное выражение») — то же самое, но шаги выносятся вперёд и получают имена: `WITH имя AS (запрос)`. Дальше по имени к ним обращаются как к обычным таблицам.

::: tip Аналогия
CTE — как вспомогательные листы в Excel. На листе «по дням» вы считаете выручку каждого дня, на листе «средние» — среднее по листу «по дням», а итоговый лист ссылается на оба. Каждый лист можно открыть и проверить отдельно, только «листы» CTE живут лишь во время одного запроса.
:::

Вопрос, который без промежуточного шага не решить: «Сколько дней каждая кофейня заработала больше своей обычной дневной выручки?» Нужны три шага: выручка по дням → средняя дневная выручка кофейни → сравнение каждого дня со своей средней.

::: figure cte-chain
Три шага CTE: 2089 заказов сворачиваются в 530 строк «кофейня × день», те — в 6 средних. На последнем шаге `daily` читается ещё раз: каждый день встаёт рядом со средней своей кофейни. Внизу тот же путь для UFA-1: три заказа 1 сентября дают 1552 ₽ за день, средняя кофейни — 833 ₽, выше неё 35 дней из 87.
:::

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    WITH daily AS (                       -- шаг 1: кофейня × день
        SELECT shop_id, CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        GROUP BY shop_id, day
    ),
    avg_shop AS (                         -- шаг 2: средняя дневная выручка кофейни
        SELECT shop_id, AVG(revenue) AS avg_rev
        FROM daily                        -- ссылаемся на шаг 1 по имени
        GROUP BY shop_id
    )
    SELECT d.shop_id,
           ROUND(a.avg_rev) AS avg_rev,
           COUNT(*) AS days,
           COUNT(*) FILTER (WHERE d.revenue > a.avg_rev) AS good_days
    FROM daily AS d
    JOIN avg_shop AS a USING (shop_id)    -- шаг 3: каждый день рядом со своей средней
    GROUP BY d.shop_id, a.avg_rev
    ORDER BY d.shop_id
""").df()
```

Что здесь происходит:

- `WITH daily AS (…)` — первый шаг: одна строка на пару «кофейня × день».
- `avg_shop AS (…)` — второй шаг идёт через запятую и читает `daily`, как обычную таблицу. Слово `WITH` пишется один раз.
- Основной `SELECT` соединяет дни со средними и считает два числа: всего дней и «хороших» дней. `COUNT(*) FILTER (WHERE …)` считает только строки, где условие верно, — это короче, чем `SUM(CASE WHEN … THEN 1 ELSE 0 END)`.

Как читать результат: средняя дневная выручка у кофеен разная — от 833 ₽ в Уфе до 2046 ₽ на PRM-1, поэтому сравнивать дни с общей средней по сети было бы нечестно. Своё среднее каждая кофейня перекрывает в 40–49 % дней (у UFA-1 — 35 из 87, у TMN-1 — 44 из 89), то есть меньше чем в половине. Это нормально: несколько очень удачных дней поднимают среднее, и большинство дней оказывается ниже него.

::: note pandas делает то же переменными
CTE в pandas — это просто промежуточные переменные: `daily = df.groupby(...)`, затем `avg_shop = daily.groupby(...)`, затем `merge`. Логика та же: шаг — имя — следующий шаг.
:::

::: warn Типичные ошибки
- **Скалярный подзапрос вернул несколько строк.** `WHERE amount > (SELECT amount FROM df WHERE shop_id = 'PRM-1')` падает с ошибкой `More than one row returned by a subquery used as an expression`. Сравнивать с «несколькими числами сразу» нельзя: нужен агрегат (`AVG`, `MAX`) или `IN`.
- **`NOT IN` и пустые значения.** Вопрос: «сколько гостей с картой ни разу не заказывали доставку?» Запрос `client_id NOT IN (SELECT client_id FROM df WHERE channel = 'доставка')` вернёт **0** гостей. Причина — среди доставок есть заказы без карты, и в списке оказался `NULL`. Сравнение с `NULL` даёт «неизвестно», поэтому `NOT IN` не пропускает ни одной строки. Исправление: в подзапросе добавить `AND client_id IS NOT NULL` (получится 110 гостей) или писать `NOT EXISTS`.
- **Запятая и `WITH`.** Второй CTE пишется через запятую, без второго `WITH`; после последнего CTE запятой нет.
:::

Почему `NOT IN` ломается из-за одного `NULL`: база раскрывает `x NOT IN (a, b, NULL)` в цепочку `x <> a AND x <> b AND x <> NULL`. Сравнение с `NULL` даёт не «ложь», а «неизвестно». Цепочка `AND`, в которой есть «неизвестно» и нет ни одной «лжи», тоже даёт «неизвестно», а `WHERE` пропускает только «истину».

::: figure not-in-null
Гость C1000 доставку не заказывал. Сравнения с C1002 и C1003 дают «истину», а сравнение с `NULL` — «неизвестно». Поэтому вся цепочка — «неизвестно», и строка отброшена. Так у каждого гостя, отсюда 0. Без `NULL` в списке цепочка — «истина»: 110 гостей из 260.
:::

Убедитесь сами, как `NULL` ломает `NOT IN`:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
wrong = duckdb.sql("""
    SELECT COUNT(DISTINCT client_id) FROM df
    WHERE client_id NOT IN (SELECT client_id FROM df WHERE channel = 'доставка')
""").fetchone()[0]
right = duckdb.sql("""
    SELECT COUNT(DISTINCT client_id) FROM df
    WHERE client_id NOT IN (SELECT client_id FROM df
                            WHERE channel = 'доставка' AND client_id IS NOT NULL)
""").fetchone()[0]
print(wrong, right)
```

{{practice: cheap, subquery, not-l, cte}}

## Оконные функции: топ-1 в каждой группе

Зачем: «самый популярный напиток в **каждой** кофейне» — частый вопрос. `GROUP BY shop_id, drink` посчитает заказы, но не выберет лучший напиток внутри каждой кофейни. Для этого есть оконная функция `ROW_NUMBER()`: она нумерует строки внутри каждой группы — 1 получает лучшая. Остаётся оставить строки с номером 1.

Здесь — только этот приём: он нужен в задачах урока. Остальные оконные функции: ранги с ничьими и `LAG` — в уроке «Оконные функции SQL», накопительные итоги и скользящие средние — в уроке «Рамки окна SQL: накопительные итоги и скользящие средние».

::: figure top1-rn
Путь запроса ниже на двух кофейнях из шести. CTE `counts` — по строке на пару «кофейня × напиток», 66 строк. `ROW_NUMBER()` с `PARTITION BY shop_id` начинает нумерацию заново в каждой кофейне, по убыванию `n`. Внешний `WHERE rn = 1` оставляет первую строку каждой кофейни — 6 строк. В UFA-1 американо и латте набрали по 34 заказа: номера 2 и 3 им раздал второй ключ `drink`, без него — случай.
:::

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    WITH counts AS (
        SELECT shop_id, drink, COUNT(*) AS n
        FROM df
        GROUP BY shop_id, drink
    )
    SELECT shop_id, drink, n
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY n DESC, drink) AS rn
        FROM counts
    )
    WHERE rn = 1
    ORDER BY shop_id
""").df()
```

Что здесь происходит:

- CTE `counts` — обычный `GROUP BY`: сколько раз заказывали каждый напиток в каждой кофейне.
- `OVER (PARTITION BY shop_id ORDER BY n DESC, drink)` — «окно»: нумеровать внутри каждой кофейни по убыванию `n`. Второй ключ `drink` решает ничьи: без него из двух напитков с равным `n` первым может оказаться любой.
- `WHERE rn = 1` стоит во **внешнем** запросе. В том же запросе, где считается `rn`, так написать нельзя — почему, разберём в следующем разделе.

{{practice: window}}

## В каком порядке выполняется запрос

Зачем: в прошлом разделе понадобился подзапрос, чтобы отфильтровать `rn = 1`. Почему нельзя было написать `WHERE rn = 1` прямо в том же запросе? И почему `HAVING` нельзя заменить на `WHERE`? Ответ один: запрос **пишется** в одном порядке, а **выполняется** в другом.

::: tip Аналогия
Запрос — как заказ в кофейне. Вы говорите: «Капучино, большой, на овсяном, с собой», но бариста делает всё в своём порядке: берёт стакан, варит эспрессо, взбивает молоко, надевает крышку. Крышку нельзя надеть до того, как налит кофе, как бы вы ни перечисляли пожелания.
:::

Логический порядок выполнения:

| шаг | что делает | что уже можно использовать |
|---|---|---|
| 1. `FROM` и `JOIN` | берёт таблицы и соединяет их | исходные столбцы |
| 2. `WHERE` | отбрасывает строки | исходные столбцы |
| 3. `GROUP BY` | сворачивает строки в группы | столбцы группировки |
| 4. `HAVING` | отбрасывает группы | агрегаты: `SUM`, `COUNT` |
| 5. `SELECT` | считает выражения, псевдонимы и **оконные функции** | всё выше |
| 6. `DISTINCT` | убирает повторы | столбцы результата |
| 7. `ORDER BY` | сортирует | псевдонимы из `SELECT` |
| 8. `LIMIT` | оставляет первые строки | — |

::: figure sql-order
Слева — порядок, в котором запрос пишут, справа — в котором база его выполняет. Все стрелки идут почти горизонтально, кроме одной: `SELECT` пишут первым, а выполняется он пятым, вместе с оконными функциями. Поэтому `WHERE` (шаг 2) ещё не знает ни сумм, ни `rn`, а `ORDER BY` (шаг 7) уже видит псевдонимы.
:::

Отсюда три правила, которые объясняют почти все ошибки «а почему так нельзя?»:

1. **Агрегат в `WHERE` — ошибка.** На шаге 2 групп ещё нет, считать `SUM` не по чему. Фильтр по сумме группы — в `HAVING` (шаг 4).
2. **Оконная функция в `WHERE` — ошибка.** Окна считаются на шаге 5, когда `WHERE` уже отработал. Чтобы отфильтровать по номеру строки, нужен ещё один уровень запроса: CTE или подзапрос (или `QUALIFY` — о нём в уроке «Оконные функции SQL»).
3. **Псевдоним из `SELECT` можно использовать в `ORDER BY`** — сортировка идёт после `SELECT`.

### Игрушечный пример руками

Таблица из четырёх чисел: 5, 1, 4, 2. Запрос нумерует строки по возрастанию и оставляет только числа больше 1.

1. `WHERE x > 1` — остаются 5, 4, 2.
2. `ROW_NUMBER() OVER (ORDER BY x)` — нумерует **оставшиеся**: 2 → 1, 4 → 2, 5 → 3.
3. `ORDER BY x` — выводит по возрастанию.

::: predict
```python static
import duckdb
import pandas as pd
t = pd.DataFrame({"x": [5, 1, 4, 2]})
r = duckdb.sql("""
    SELECT x, ROW_NUMBER() OVER (ORDER BY x) AS rn
    FROM t
    WHERE x > 1
    ORDER BY x
""").fetchall()
for x, rn in r:
    print(x, rn)
```

- `2 2 | 4 3 | 5 4`
- [x] `2 1 | 4 2 | 5 3`
- `1 1 | 2 2 | 4 3 | 5 4`

Почему: `WHERE` (шаг 2) срабатывает раньше оконной функции (шаг 5). Строка с единицей выброшена до нумерации, поэтому нумерация начинается с двойки.
:::

А вот что будет, если поставить оконную функцию в `WHERE`:

```python error
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    SELECT order_id, shop_id, amount,
           ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY amount DESC) AS rn
    FROM df
    WHERE rn = 1          -- на шаге WHERE столбца rn ещё нет
""").df()
```

DuckDB отвечает: `WHERE clause cannot contain window functions!` Исправление — вынести нумерацию на уровень ниже и фильтровать снаружи:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    WITH ranked AS (
        SELECT order_id, shop_id, amount,
               ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY amount DESC, order_id) AS rn
        FROM df
    )
    SELECT shop_id, order_id, amount
    FROM ranked
    WHERE rn = 1          -- здесь rn — обычный столбец таблицы ranked
    ORDER BY shop_id
""").df()
```

Что здесь происходит: внутри CTE `ranked` нумерация уже посчитана и стала обычным столбцом. Внешний запрос начинает свой порядок заново — с `FROM ranked`, и для его `WHERE` столбец `rn` существует. Получается самый дорогой заказ каждой кофейни. `order_id` в `ORDER BY` окна — на случай двух заказов с одинаковой суммой: так результат не зависит от случая.

::: note DuckDB добрее других баз
DuckDB разрешает ссылаться на псевдоним из `SELECT` в `WHERE` и `GROUP BY`: `SELECT amount * 2 AS a FROM df WHERE a > 1000` в нём работает. В PostgreSQL и SQL Server этот же запрос упадёт: там нужно повторить выражение (`WHERE amount * 2 > 1000`) или вынести его в CTE. Если запрос потом переедет в рабочую базу, лучше сразу писать «по-строгому».
:::

### EXPLAIN: как база собирается выполнять запрос

::: note Можно пропустить
Этот подраздел — на будущее, для долгих запросов к большой базе. В задачах урока `EXPLAIN` не нужен.
:::

Логический порядок — это про смысл: какой результат получится. Как именно база будет считать, решает её **оптимизатор**. Например, он может отфильтровать строки прямо при чтении файла, если результат от этого не меняется. Посмотреть план выполнения можно, если написать перед запросом `EXPLAIN`:

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
plan = duckdb.sql("""
    EXPLAIN
    SELECT shop_id, SUM(amount) AS revenue
    FROM df
    WHERE channel = 'доставка'
    GROUP BY shop_id
    ORDER BY revenue DESC
""").fetchall()
print(plan[0][1])   # первая строка результата, второй столбец — текст плана
```

Как читать план: **снизу вверх**. Внизу — чтение таблицы (`PANDAS_SCAN` для датафрейма, `READ_CSV` для файла) и список столбцов, которые реально читаются, — только три из девяти. Выше — `FILTER` по каналу, затем группировка `HASH_GROUP_BY` и сортировка `ORDER_BY`. Числа вида `~417 rows` — оценка, сколько строк дойдёт до шага.

::: figure explain-plan
План запроса «выручка доставки по кофейням» — дерево узлов. Данные текут снизу вверх: чтение трёх нужных столбцов, фильтр по каналу, группировка, сортировка. Справа — часть запроса, из которой вырос каждый узел. Оценки строк у вашей версии DuckDB могут немного отличаться.
:::

Аналитику `EXPLAIN` нужен в двух случаях: запрос к большой базе идёт подозрительно долго (смотрят, не читается ли лишнее и не соединяются ли таблицы «каждая с каждой»), или результат странный и хочется понять, какие шаги вообще выполняются. `EXPLAIN ANALYZE` выполняет запрос и показывает время каждого шага. В PostgreSQL и SQL Server тоже есть `EXPLAIN` (в SQL Server — «план выполнения» в SSMS), вид плана у каждой базы свой.

::: quiz
Запрос `SELECT shop_id, SUM(amount) AS revenue FROM df WHERE revenue > 50000 GROUP BY shop_id` должен оставить кофейни с выручкой больше 50 000 ₽, но падает с ошибкой. Как исправить и почему?

- [x] Перенести условие в `HAVING SUM(amount) > 50000`: `WHERE` выполняется до группировки, когда сумм по кофейням ещё нет
  > `WHERE` отбирает строки-заказы (шаг 2), а `HAVING` — готовые группы (шаг 4). Условие на сумму группы — это условие на группу.
- [ ] Поставить `WHERE` после `GROUP BY` — порядок слов в запросе и есть порядок выполнения
  > Порядок слов в SQL фиксирован, и он не совпадает с порядком выполнения. `WHERE` после `GROUP BY` — синтаксическая ошибка.
- [ ] Заменить `revenue` на `SUM(amount)` в `WHERE`
  > Агрегат в `WHERE` тоже запрещён: `WHERE clause cannot contain aggregates`. На шаге `WHERE` групп ещё нет.
- [ ] Добавить `ORDER BY revenue` — тогда псевдоним станет доступен
  > `ORDER BY` выполняется в самом конце и на `WHERE` никак не влияет.
:::

{{practice: order-fix}}

## Практика

## task: cheap | Заказы дешевле среднего | warmup

Посчитайте `cheap` — число заказов, сумма которых **меньше** среднего чека по сети. Средний чек возьмите скалярным подзапросом, число руками не вписывайте.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv')
want = int((_d['amount'] < _d['amount'].mean()).sum())
assert '339' not in _code and '340' not in _code, 'Средний чек вписан числом — пусть его посчитает подзапрос (SELECT AVG(amount) FROM df).'
assert _code.upper().count('SELECT') >= 2, 'Нужен подзапрос: WHERE amount < (SELECT AVG(amount) FROM df).'
assert int(need('cheap')) == want, f'cheap = {need("cheap")}, а нужно другое число. Сравнение строгое: amount < среднего.'
```

### hint
Это зеркало примера из теории: там считали заказы **дороже** среднего, здесь — дешевле.

### hint
`SELECT COUNT(*) FROM df WHERE amount < (SELECT AVG(amount) FROM df)`, затем `.fetchone()[0]`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
cheap = duckdb.sql("""
    SELECT COUNT(*) FROM df
    WHERE amount < (SELECT AVG(amount) FROM df)
""").fetchone()[0]
```

### explain
Дешевле среднего — 1387 заказов из 2089, около двух третей. Вместе с 702 заказами дороже среднего получается ровно 2089: заказа на сумму, равную среднему (339.97 ₽), нет. Средний чек выше «типичного» заказа: несколько дорогих заказов тянут его вверх, и большинство заказов оказывается ниже.

## task: subquery | Дорогие заказы Казани | base

Посчитайте `big_kzn` — число заказов в кофейнях **Казани**, сумма которых больше среднего чека **по всей сети**. Список казанских кофеен возьмите из `shops` подзапросом с `IN`, средний чек — скалярным подзапросом. Номера кофеен руками не вписывайте.

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
_d = _pd.read_csv('orders_3m.csv'); _s = _pd.read_csv('shops.csv')
_k = _d[_d['shop_id'].isin(_s.loc[_s['city'] == 'Казань', 'shop_id'])]
want = int((_k['amount'] > _d['amount'].mean()).sum())
got = need('big_kzn')
assert 'KZN-' not in _code, 'Номера кофеен вписаны руками — возьмите их из shops подзапросом: shop_id IN (SELECT shop_id FROM shops WHERE ...).'
assert 'IN' in _code.upper() and _code.upper().count('SELECT') >= 3, 'Нужны два подзапроса: IN (SELECT …) для кофеен и (SELECT AVG …) для среднего чека.'
assert int(got) == want, f'big_kzn = {got}, а нужно другое число. Средний чек — по всей сети (без фильтра по городу), сравнение строгое: amount > среднего.'
```

### hint
Два условия в `WHERE` через `AND`: кофейня из Казани и сумма больше среднего. Каждое условие — со своим подзапросом.

### hint
`shop_id IN (SELECT shop_id FROM shops WHERE city = 'Казань')` и `amount > (SELECT AVG(amount) FROM df)`.

### hint
```python
big_kzn = duckdb.sql("""
    SELECT COUNT(*) FROM df
    WHERE shop_id IN (SELECT ... FROM shops WHERE ...)
      AND amount > (SELECT ... FROM df)
""").fetchone()[0]
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
big_kzn = duckdb.sql("""
    SELECT COUNT(*) FROM df
    WHERE shop_id IN (SELECT shop_id FROM shops WHERE city = 'Казань')
      AND amount > (SELECT AVG(amount) FROM df)
""").fetchone()[0]
```

### explain
Дороже среднего по сети (около 340 ₽) — 283 казанских заказа из 833, примерно 34 %. По всей сети таких заказов 702 из 2089, тоже около трети: Казань здесь не выделяется. Типичная ошибка — посчитать средний чек внутри подзапроса только по Казани (`SELECT AVG(amount) FROM df WHERE shop_id IN …`): тогда сравнение идёт с другим порогом, и число заказов получится другим. В pandas то же самое — две маски: `df["shop_id"].isin(kzn_ids) & (df["amount"] > df["amount"].mean())`.

## task: not-l | Гости без больших стаканов | base

Посчитайте `no_l` — сколько гостей с картой **ни разу** не брали напиток размера `L`. Список «кто брал L» возьмите подзапросом. Заказы без карты (`client_id` пустой) гостями не считаются.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv').dropna(subset=['client_id'])
_took = set(_d.loc[_d['size'] == 'L', 'client_id'])
want = len(set(_d['client_id']) - _took)
got = int(need('no_l'))
assert got != 0, 'no_l = 0. Похоже, в списке подзапроса есть NULL: L брали и без карты. Добавьте в подзапрос AND client_id IS NOT NULL или перепишите через NOT EXISTS.'
assert _code.upper().count('SELECT') >= 2, 'Список гостей, бравших L, возьмите подзапросом.'
assert got == want, f'no_l = {got}, а нужно другое число. Считайте разных гостей: COUNT(DISTINCT client_id).'
```

### hint
Гостей считайте через `COUNT(DISTINCT client_id)`: у одного гостя много заказов. Подзапрос — `SELECT client_id FROM df WHERE size = 'L'`.

### hint
Если вышел 0 — это ловушка `NOT IN` из теории: большие стаканы брали и без карты, и в списке оказался `NULL`. Добавьте в подзапрос `AND client_id IS NOT NULL`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
no_l = duckdb.sql("""
    SELECT COUNT(DISTINCT client_id) FROM df
    WHERE client_id NOT IN (SELECT client_id FROM df
                            WHERE size = 'L' AND client_id IS NOT NULL)
""").fetchone()[0]
```

### explain
95 гостей из 260 ни разу не брали большой стакан. Без `IS NOT NULL` запрос вернул бы 0: из 412 заказов размера L 155 сделаны без карты, и `NULL` попал в список. Тот же ответ даёт `NOT EXISTS (SELECT 1 FROM df AS o WHERE o.client_id = df.client_id AND o.size = 'L')`: `NOT EXISTS` к `NULL` в подзапросе нечувствителен. `COUNT(DISTINCT …)` сам пропускает `NULL`, поэтому заказы без карты в ответ не попадают.

## task: cte | Средняя дневная выручка городов | base

Соберите `city_daily` — DataFrame со столбцами `city` и `avg_daily`: средняя **дневная** выручка города, округлённая до целого, по убыванию. Сначала в CTE посчитайте выручку «город × день» (соедините заказы со `shops`), потом усредните её по городам.

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
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime']).merge(_pd.read_csv('shops.csv'), on='shop_id')
_w = _d.groupby(['city', _d['datetime'].dt.date])['amount'].sum().groupby(level=0).mean().round().sort_values(ascending=False)
b = need('city_daily', _pd.DataFrame)
assert list(b.columns) == ['city', 'avg_daily'], f'Столбцы: {list(b.columns)}, а нужны city и avg_daily.'
assert 'WITH' in _code.upper(), 'Решите через CTE: WITH daily AS (...) SELECT ...'
assert b['city'].tolist() == list(_w.index), f'Порядок городов: {b["city"].tolist()}. Нужна сортировка по avg_daily по убыванию.'
_a = [float(x) for x in b['avg_daily']]
if any(abs(x - y) > 0.51 for x, y in zip(_a, _w.values)):
    assert False, f'avg_daily = {_a}. Это не средняя дневная выручка. Похоже на среднее по заказам? Сначала сложите выручку внутри дня, потом усредняйте дни.'
```

### hint
В одном `GROUP BY` это не посчитать: сначала нужна сумма за каждый день, а потом среднее этих сумм. Это два уровня — CTE и основной запрос.

### hint
CTE: `SELECT city, CAST(datetime AS DATE) AS day, SUM(amount) AS revenue FROM df JOIN shops USING (shop_id) GROUP BY city, day`. Основной запрос: `AVG(revenue)` по `city`.

### hint
```python
city_daily = duckdb.sql("""
    WITH daily AS (
        SELECT city, CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df JOIN shops USING (shop_id)
        GROUP BY ...
    )
    SELECT city, ROUND(AVG(...)) AS avg_daily
    FROM daily
    GROUP BY city
    ORDER BY ...
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
city_daily = duckdb.sql("""
    WITH daily AS (
        SELECT city, CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        JOIN shops USING (shop_id)
        GROUP BY city, day
    )
    SELECT city, ROUND(AVG(revenue)) AS avg_daily
    FROM daily
    GROUP BY city
    ORDER BY avg_daily DESC
""").df()
```

### explain
Казань в среднем приносит 3074 ₽ в день, Пермь — 2874 ₽, Тюмень — 1084 ₽, Уфа — 833 ₽. Каждый город — две кофейни или одна, и дневная выручка города складывается из всех его кофеен. Если бы вы написали `AVG(amount)` без CTE, получился бы средний **чек** (около 340 ₽ во всех городах) — совсем другая метрика. В pandas этот запрос — две группировки подряд: `full.groupby(["city", full["datetime"].dt.date])["amount"].sum().groupby(level=0).mean()`.

## task: window | Лучший день каждой кофейни | plus

С помощью оконной функции найдите для каждой кофейни день с максимальной выручкой. Результат `best_days` — DataFrame со столбцами `shop_id`, `day`, `revenue`, по одной строке на кофейню, отсортированный по `shop_id`.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
daily = d.groupby(['shop_id', d['datetime'].dt.date])['amount'].sum()
want = daily.groupby(level=0).max()
b = need('best_days', _pd.DataFrame)
assert list(b.columns) == ['shop_id', 'day', 'revenue'], f'Столбцы: {list(b.columns)}.'
assert b['shop_id'].tolist() == list(want.index), 'Должно быть по одной строке на кофейню, по порядку shop_id.'
assert all(abs(float(x) - float(y)) < 1e-6 for x, y in zip(b['revenue'], want.values)), 'Выручка лучших дней не совпадает.'
```

### hint
Два шага: сначала выручка «кофейня × день», потом нумерация дней внутри каждой кофейни по убыванию выручки.

### hint
CTE с выручкой по `shop_id` и `CAST(datetime AS DATE) AS day`, затем `ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY revenue DESC)` и `WHERE rn = 1`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
best_days = duckdb.sql("""
    WITH daily AS (
        SELECT shop_id, CAST(datetime AS DATE) AS day, SUM(amount) AS revenue
        FROM df
        GROUP BY shop_id, day
    )
    SELECT shop_id, day, revenue
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY revenue DESC) AS rn
        FROM daily
    )
    WHERE rn = 1
    ORDER BY shop_id
""").df()
```

### explain
Для каждой кофейни — одна строка с её лучшим днём. `ROW_NUMBER` нумерует дни внутри кофейни по убыванию выручки, а `WHERE rn = 1` оставляет первый; в pandas это потребовало бы сортировки и `groupby(...).head(1)`.

## task: order-fix | Почините запрос: первый заказ гостя | base

Аналитик хотел получить первый заказ каждого гостя с картой, но запрос в заготовке падает с ошибкой `WHERE clause cannot contain window functions!`. Почините его, чтобы `first_orders` стал DataFrame со столбцами `client_id`, `datetime`, `amount`: по одной строке на гостя (заказы без карты не нужны), по возрастанию `client_id`. Нумерацию оставьте оконной функцией.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

first_orders = duckdb.sql("""
    SELECT client_id, datetime, amount,
           ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime) AS rn
    FROM df
    WHERE client_id IS NOT NULL AND rn = 1
    ORDER BY client_id
""").df()
```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime']).dropna(subset=['client_id'])
_w = _d.sort_values('datetime').groupby('client_id').head(1).sort_values('client_id')
b = need('first_orders', _pd.DataFrame)
assert list(b.columns) == ['client_id', 'datetime', 'amount'], f'Столбцы: {list(b.columns)}. Во внешнем SELECT перечислите только client_id, datetime, amount — без rn.'
assert b['client_id'].notna().all(), 'В результате есть строка с пустым client_id — уберите заказы без карты.'
assert len(b) == len(_w), f'Строк {len(b)}, а гостей с картой {len(_w)}: нужна ровно одна строка на гостя.'
assert b['client_id'].tolist() == _w['client_id'].tolist(), 'Порядок строк: по возрастанию client_id.'
assert [str(x)[:16] for x in b['datetime']] == [str(x)[:16] for x in _w['datetime']], 'Даты не совпадают с первыми заказами. Проверьте ORDER BY datetime внутри окна (по возрастанию).'
assert 'ROW_NUMBER' in _code.upper(), 'Оставьте нумерацию ROW_NUMBER() — дело не в ней, а в месте, где по ней фильтруют.'
```

### hint
По шагам выполнения: `WHERE` срабатывает раньше, чем `SELECT` посчитает `rn`. Значит, фильтр `rn = 1` должен стоять на уровень выше — во внешнем запросе.

### hint
Перенесите текущий запрос (без `rn = 1`) в `WITH ranked AS (...)`, а снаружи напишите `SELECT client_id, datetime, amount FROM ranked WHERE rn = 1 ORDER BY client_id`.

### hint
```python
first_orders = duckdb.sql("""
    WITH ranked AS (
        SELECT client_id, datetime, amount,
               ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime) AS rn
        FROM df
        WHERE client_id IS NOT NULL
    )
    SELECT ...
    FROM ranked
    WHERE ...
    ORDER BY client_id
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

first_orders = duckdb.sql("""
    WITH ranked AS (
        SELECT client_id, datetime, amount,
               ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime) AS rn
        FROM df
        WHERE client_id IS NOT NULL
    )
    SELECT client_id, datetime, amount
    FROM ranked
    WHERE rn = 1
    ORDER BY client_id
""").df()
```

### explain
У 260 гостей с картой — 260 первых заказов. Фильтр `client_id IS NOT NULL` остался внутри CTE: он относится к исходным строкам и честно работает на шаге `WHERE`. А `rn = 1` переехал наружу, где `rn` уже обычный столбец. Если оставить `WHERE client_id IS NOT NULL` снаружи, результат будет тем же, но окно зря пронумерует и заказы без карты (они соберутся в одну «пустую» группу). В pandas тот же результат даёт `df.dropna(subset=["client_id"]).sort_values("datetime").groupby("client_id").head(1)`.
