---
title: "Оконные функции SQL"
lead: "Оконная функция считает итог, место или соседнее значение и кладёт его рядом с каждой строкой, не сворачивая таблицу. Так решаются доли от итога, топ-N в группе с ничьими, четверти гостей по тратам и «месяц к месяцу». Запросы выполняются в DuckDB прямо в браузере, а к каждой функции показан аналог на pandas. Накопительные итоги, скользящие средние и рамки окна — в следующем уроке."
files: [orders_3m.csv]
recap:
  - "Окно: `функция() OVER (PARTITION BY группа ORDER BY порядок рамка)`. В отличие от `GROUP BY`, строки не сворачиваются: результат встаёт рядом с каждой строкой."
  - "Доля от итога: `x / SUM(x) OVER ()` — от всей таблицы, `x / SUM(x) OVER (PARTITION BY g)` — от своей группы."
  - "Ранги на ничьих: `ROW_NUMBER` — 1, 2, 3, 4 (ничью разрывает случай — добавляйте второй ключ сортировки); `RANK` — 1, 2, 2, 4; `DENSE_RANK` — 1, 2, 2, 3."
  - "`NTILE(4)` делит упорядоченные строки на 4 почти равные группы; лишние строки достаются первым группам."
  - "`LAG(x)` — значение из предыдущей строки, `LEAD(x)` — из следующей; у краёв — `NULL`."
  - "`WHERE` выполняется до окон: фильтр по оконной функции — в `QUALIFY` (DuckDB) или во внешнем запросе (CTE)."
  - "`WINDOW w AS (...)` даёт окну имя, `OVER w` использует его в нескольких функциях."
  - "Аналоги оконных функций в pandas — в шпаргалке в конце урока; в задачах они не нужны."
---

## Окно: итог рядом с каждой строкой

::: note Что здесь обязательно
В задачах урока нужен только SQL. Аналоги на pandas вынесены в блоки «Аналог в pandas: …» — их можно пропустить и не запоминать. Все они собраны в шпаргалке в конце урока, к ней удобно вернуться, когда понадобится.
:::

Зачем: управляющий спрашивает, какую долю выручки сети даёт каждая кофейня. `GROUP BY` посчитает выручку кофеен, но общий итог сети при этом исчезнет: строки свернулись. Можно посчитать итог вторым запросом и поделить в pandas. Но удобнее, когда итог встаёт **рядом с каждой строкой** — тогда долю можно посчитать в том же запросе. Это и делает оконная функция.

::: tip Аналогия
`GROUP BY` — как сводная таблица в Excel: строки схлопнулись в итоги. Оконная функция — как столбец в исходной таблице с формулой `=СУММЕСЛИ(...)`: строки остаются на месте, а в каждой появляется итог её группы. Где аналогия хромает: окно умеет ещё и упорядочивать строки внутри группы — об этом следующие разделы.
:::

### Игрушечный пример руками

Четыре заказа: в PRM-1 на 300 и 200 ₽, в KZN-1 на 400 и 100 ₽. Всего 1000 ₽.

1. `SUM(amount) OVER ()` — пустые скобки значат «окно — вся таблица». В каждой из четырёх строк будет 1000.
2. `SUM(amount) OVER (PARTITION BY shop)` — окно — строки своей кофейни. У заказов PRM-1 будет 300 + 200 = 500, у KZN-1 — 400 + 100 = 500.
3. Доля заказа в сети: 300 / 1000 = 30 %, 200 / 1000 = 20 %, 400 / 1000 = 40 %, 100 / 1000 = 10 %.
4. Доля заказа в своей кофейне: 300 / 500 = 60 %, 200 / 500 = 40 %, 400 / 500 = 80 %, 100 / 500 = 20 %.

Строк в результате по-прежнему четыре — ни одна не свернулась.

::: figure window-vs-groupby
Те же четыре заказа двумя способами. `GROUP BY shop` оставляет по строке на кофейню, и сами заказы пропадают. Окно `OVER (PARTITION BY shop)` оставляет все четыре строки и дописывает к каждой итог её кофейни; из него в той же строке считается доля.
:::

```python
import duckdb
import pandas as pd

toy = pd.DataFrame({"shop": ["PRM-1", "PRM-1", "KZN-1", "KZN-1"],
                    "amount": [300, 200, 400, 100]})
duckdb.sql("""
    SELECT shop, amount,
           SUM(amount) OVER ()                    AS total,      -- итог всей таблицы
           SUM(amount) OVER (PARTITION BY shop)   AS shop_total, -- итог своей кофейни
           100 * amount / SUM(amount) OVER ()                  AS pct_net,
           100 * amount / SUM(amount) OVER (PARTITION BY shop) AS pct_shop
    FROM toy
""").df()
```

Что здесь происходит:

- `OVER (...)` превращает обычный агрегат `SUM` в оконный: он считается по «окну» строк, но результат пишется в каждую строку, а не сворачивает их.
- `PARTITION BY shop` режет таблицу на части по кофейням — как `GROUP BY`, только без свёртки. Каждая строка видит лишь свою часть.
- Порядок строк в результате DuckDB не гарантирует — если он важен, добавьте `ORDER BY` в конце запроса.

Пустые скобки и `PARTITION BY` — только начало. Полная запись окна состоит из четырёх частей, и весь урок — о том, что можно поставить в каждую:

::: figure window-anatomy
Оконная функция по частям. Функция говорит, **что** считать. `PARTITION BY` режет таблицу на группы, `ORDER BY` упорядочивает строки внутри группы, рамка `ROWS`/`RANGE` выбирает, какую часть группы видит текущая строка. Обязательны только функция и `OVER ( )`. Ранги и `LAG` требуют `ORDER BY`, а рамка — тема следующего урока «Рамки окна SQL: накопительные итоги и скользящие средние».
:::

::: deep Аналог в pandas: transform
В pandas тот же «итог рядом со строкой» даёт `transform`: он считает агрегат по группе и растягивает его обратно на все строки группы.

```python
import pandas as pd

toy = pd.DataFrame({"shop": ["PRM-1", "PRM-1", "KZN-1", "KZN-1"],
                    "amount": [300, 200, 400, 100]})
toy["total"] = toy["amount"].sum()                                    # SUM(amount) OVER ()
toy["shop_total"] = toy.groupby("shop")["amount"].transform("sum")    # SUM(...) OVER (PARTITION BY shop)
toy["pct_shop"] = 100 * toy["amount"] / toy["shop_total"]
toy
```
:::

### Доля кофейни в выручке сети

Теперь на трёх месяцах заказов. Окно можно поставить и **поверх группировки**: сначала `GROUP BY` сворачивает заказы в кофейни, потом `SUM(SUM(amount)) OVER ()` складывает выручки кофеен в итог сети.

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    SELECT shop_id,
           SUM(amount) AS revenue,
           ROUND(100 * SUM(amount) / SUM(SUM(amount)) OVER (), 1) AS pct
    FROM df
    GROUP BY shop_id
    ORDER BY revenue DESC
""").df()
```

Что здесь происходит:

- Внутренний `SUM(amount)` — обычный агрегат `GROUP BY`: выручка кофейни.
- Внешний `SUM(...) OVER ()` — оконный: сумма выручек всех кофеен, то есть итог сети. Так можно, потому что окна считаются **после** группировки (порядок выполнения из прошлого урока: `GROUP BY` → `HAVING` → `SELECT` с окнами).

Как читать результат: PRM-1 даёт 26.2 % выручки сети, KZN-1 — 25.5 %; две старые кофейни вместе — больше половины. Самая молодая из шести, UFA-1 (открыта в ноябре 2025-го), — 10.2 %. Сумма столбца `pct` — 100 % (с точностью до округления), это удобная самопроверка.

::: sql
Если вы считали доли в SQL Server через подзапрос `amount / (SELECT SUM(amount) FROM t)`, окно `SUM(amount) OVER ()` делает то же самое, но читается проще и легко превращается в долю внутри группы — достаточно добавить `PARTITION BY`.
:::

::: quiz
Запрос `SELECT shop_id, drink, COUNT(*) AS n, COUNT(*) OVER (PARTITION BY shop_id) AS m FROM df GROUP BY shop_id, drink` выполнился. Что окажется в столбце `m`?

- [x] Сколько разных напитков продавалось в кофейне: окно считает строки уже сгруппированной таблицы
  > Окна считаются после `GROUP BY`. В сгруппированной таблице одна строка — это пара «кофейня × напиток», поэтому `COUNT(*)` по окну кофейни — число таких пар, то есть число напитков.
- [ ] Число заказов кофейни
  > Число заказов дал бы `SUM(COUNT(*)) OVER (PARTITION BY shop_id)` — сумма счётчиков `n` по кофейне.
- [ ] То же, что `n`
  > `n` — заказы одного напитка, а окно `m` охватывает все строки кофейни.
- [ ] Запрос упадёт: агрегат и оконная функция в одном `SELECT` несовместимы
  > Совместимы: окно работает поверх результата группировки. Именно так считаются доли от итога.
:::

::: warn Типичные ошибки
- **Окно без `PARTITION BY` там, где нужна группа.** `SUM(amount) OVER ()` — итог всей таблицы. Доля напитка «в своей кофейне» получится, только если написать `OVER (PARTITION BY shop_id)`.
- **`SUM(amount) OVER ()` вместо `SUM(SUM(amount)) OVER ()` после `GROUP BY`.** DuckDB ответит ошибкой: столбец `amount` не входит в группировку, а в окне он стоит «голым». После `GROUP BY` окно видит только столбцы группировки и агрегаты.
- **Целочисленное деление в других базах.** В DuckDB `/` — обычное деление. В PostgreSQL и SQL Server `200 / 1000` для целых чисел даст 0. Там пишут `100.0 * amount / ...`.
:::

{{practice: w-share}}

## Нумерация и ранги

Зачем: «топ-2 напитка в каждой кофейне» — частый вопрос. В прошлом уроке вы решали похожий через `ROW_NUMBER`. Но что делать, если у двух напитков одинаковое число заказов? `ROW_NUMBER` молча выкинет один из них. Чтобы ничьи обрабатывались честно, есть ещё две функции нумерации, и важно понимать разницу.

::: tip Аналогия
Забег, где двое пришли одновременно. `ROW_NUMBER` — номерки в очереди за медалями: у всех разные, и кто из двоих раньше, решает случай. `RANK` — спортивный протокол: два вторых места, следующий — четвёртый. `DENSE_RANK` — ступени пьедестала: две вторых ступени, следующая — третья.
:::

### Игрушечный пример руками

Заказы напитков: латте — 5, капучино — 4, раф — 4, чай — 2. Нумеруем по убыванию заказов.

| напиток | заказов | `ROW_NUMBER` | `RANK` | `DENSE_RANK` |
|---|---|---|---|---|
| латте | 5 | 1 | 1 | 1 |
| капучино | 4 | 2 | 2 | 2 |
| раф | 4 | 3 | 2 | 2 |
| чай | 2 | 4 | **4** | **3** |

1. `ROW_NUMBER` раздаёт номера подряд: 1, 2, 3, 4. Капучино и раф равны, и кто из них второй, а кто третий, не определено.
2. `RANK` даёт равным одинаковое место, а следующее место **пропускает**: двое делят второе, чай — четвёртый. Место = 1 + сколько строк строго лучше.
3. `DENSE_RANK` даёт равным одно место, но **без пропуска**: чай — третий. Место = номер «уровня» значения.

::: figure rank-ties
Те же четыре напитка. Капучино и раф набрали поровну. `ROW_NUMBER` всё равно раздаёт им разные номера 2 и 3, и кто из них второй, решает второй ключ сортировки или случай. `RANK` и `DENSE_RANK` дают обоим место 2 и расходятся только на чае: `RANK` пропускает место 3 (чай — 4), `DENSE_RANK` не пропускает (чай — 3). Под именем функции — тот же способ в pandas.
:::

::: predict
```python static
import duckdb
import pandas as pd
t = pd.DataFrame({"drink": ["латте", "капучино", "раф", "чай"], "n": [5, 4, 4, 2]})
r = duckdb.sql("""
    SELECT drink,
           RANK() OVER (ORDER BY n DESC) AS r,
           DENSE_RANK() OVER (ORDER BY n DESC) AS d
    FROM t
    ORDER BY n DESC, drink
""").fetchall()
for drink, r_, d in r:
    print(drink, r_, d)
```

- `капучино 2 2 | латте 1 1 | раф 3 3 | чай 4 4`
- [x] `латте 1 1 | капучино 2 2 | раф 2 2 | чай 4 3`
- `латте 1 1 | капучино 2 2 | раф 2 2 | чай 3 3`

Почему: капучино и раф набрали по 4 заказа и делят второе место. `RANK` после ничьей пропускает третье место (чай — 4), `DENSE_RANK` — нет (чай — 3).
:::

### На реальных данных: топ-2 с ничьими

Посчитаем места напитков в каждой кофейне по числу заказов. Чтобы не повторять окно трижды, дадим ему имя через `WINDOW`, а отбор мест сделаем `QUALIFY` — это `WHERE` для оконных функций.

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    SELECT shop_id, drink, COUNT(*) AS n,
           ROW_NUMBER() OVER w AS rn,
           RANK()       OVER w AS rnk,
           DENSE_RANK() OVER w AS drnk
    FROM df
    GROUP BY shop_id, drink
    WINDOW w AS (PARTITION BY shop_id ORDER BY COUNT(*) DESC)
    QUALIFY drnk <= 3
    ORDER BY shop_id, drnk, drink
""").df()
```

Что здесь происходит:

- `WINDOW w AS (...)` описывает окно один раз; `OVER w` подставляет его в каждую функцию. Если окно поменяется, править придётся в одном месте.
- `ORDER BY COUNT(*) DESC` внутри окна: места раздаются по убыванию числа заказов.
- `QUALIFY drnk <= 3` выполняется **после** окон — как `HAVING` выполняется после группировки. В `WHERE` такое условие не написать: на шаге `WHERE` окон ещё нет.

Как читать результат: в KZN-1 американо и раф набрали по 62 заказа — оба на третьем месте и по `RANK`, и по `DENSE_RANK`, а `ROW_NUMBER` дал им 3 и 4. В UFA-1 латте и американо по 34 заказа: оба вторые, и флэт уайт получил `RANK` 4, но `DENSE_RANK` 3. Если бы мы отбирали «топ-3» по `ROW_NUMBER`, один из равных напитков пропал бы из отчёта случайным образом.

::: sql
`QUALIFY` есть в DuckDB, Snowflake, BigQuery и Teradata, но **нет** в PostgreSQL и SQL Server. Там то же самое пишут через CTE: окно считают внутри `WITH ranked AS (...)`, а `WHERE drnk <= 3` — снаружи. Результат одинаковый.
:::

::: deep Аналог в pandas: rank
`rank` с параметром `method` повторяет все три функции. Для `ROW_NUMBER` нужен `method="first"`: он разрывает ничью порядком строк в таблице, поэтому таблицу заранее сортируют по второму ключу.

```python
import pandas as pd

df = pd.read_csv("orders_3m.csv")
cnt = (df.groupby(["shop_id", "drink"], as_index=False).size()
         .sort_values(["shop_id", "drink"]))                  # второй ключ — по алфавиту
g = cnt.groupby("shop_id")["size"]
cnt["rn"] = g.rank(method="first", ascending=False).astype(int)   # ROW_NUMBER
cnt["rnk"] = g.rank(method="min", ascending=False).astype(int)    # RANK
cnt["drnk"] = g.rank(method="dense", ascending=False).astype(int) # DENSE_RANK
cnt[(cnt["shop_id"] == "UFA-1") & (cnt["drnk"] <= 3)].sort_values("drnk")
```

Что здесь происходит: `groupby("shop_id")["size"].rank(...)` ранжирует внутри каждой кофейни, как `PARTITION BY`; `ascending=False` — как `DESC`. Последняя строка — то же, что `QUALIFY`: обычный фильтр по готовому столбцу.
:::

::: quiz
Нужен список «три самых продаваемых напитка каждой кофейни». Если два напитка поделили третье место, в отчёт должны попасть оба. Какое условие выбрать?

- [x] `DENSE_RANK() ... <= 3` (или `RANK() ... <= 3`)
  > Обе функции дают равным одинаковое место, поэтому оба напитка с третьим местом пройдут фильтр. Разница проявится при ничьей выше: при местах 1, 2, 2 следующий напиток получит по `RANK` место 4 и в отчёт не попадёт, а по `DENSE_RANK` — место 3 и попадёт. Что из этого «правильно», решает формулировка отчёта: три напитка или три уровня продаж.
- [ ] `ROW_NUMBER() ... <= 3`
  > `ROW_NUMBER` никогда не даёт одинаковых номеров. Из двух равных напитков третий номер получит один, и какой — решит случай.
- [ ] `ORDER BY n DESC LIMIT 3`
  > `LIMIT` действует на всю таблицу, а не на каждую кофейню: получите три строки на всю сеть.
- [ ] `WHERE DENSE_RANK() OVER (...) <= 3`
  > Функция подходящая, но место неверное: `WHERE` выполняется до окон и упадёт с ошибкой. Нужен `QUALIFY` или внешний запрос.
:::

::: warn Типичные ошибки
- **`ROW_NUMBER` без второго ключа.** `ORDER BY n DESC` при ничьей отдаёт порядок на волю случая: два запуска могут дать разный «первый» напиток. Добавляйте второй ключ: `ORDER BY n DESC, drink`.
- **`RANK` вместо `DENSE_RANK` в «топ-N уровней».** При ничьей на первом месте `RANK` выдаст 1, 1, 3, и условие `= 2` не найдёт ни одной строки.
- **Фильтр по рангу в `WHERE`.** Ошибка `WHERE clause cannot contain window functions!`. Лечится `QUALIFY` или CTE.
:::

{{practice: w-number, w-ties, w-streak}}

## NTILE: разбить на равные группы

Зачем: маркетолог хочет понять, насколько выручка зависит от самых активных гостей. Классический приём — разложить гостей по сумме покупок на четыре равные по численности группы (**квартили**) и посмотреть, какую долю выручки даёт верхняя четверть. `NTILE(4)` делает такое разбиение одной функцией.

::: tip Аналогия
Очередь из десяти гостей рассаживают по порядку за четыре стола. Поровну не выходит, поэтому лишние двое садятся за первые столы: получается 3, 3, 2, 2. Кто за каким столом, решает только место в очереди, а не то, сколько гость потратил. Где аналогия хромает: в кафе гость сам выбирает стол, а `NTILE` рассаживает строго по порядку сортировки — поэтому порядок нужно задать однозначно, со вторым ключом.
:::

### Игрушечный пример руками

Десять гостей, отсортированных по сумме покупок, делим `NTILE(4)`. Поровну 10 на 4 не делится: 10 = 4 × 2 + 2. Правило `NTILE`: все группы получают по 2 гостя, а оставшиеся 2 достаются **первым** группам по одному. Размеры групп: 3, 3, 2, 2.

| место | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| группа | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 | 4 | 4 |

::: figure ntile-split
Сверху — игрушечный пример: десять гостей по убыванию трат, группы 3, 3, 2, 2. Снизу — настоящие гости с картой из следующего примера. `NTILE(4)` делит 260 гостей ровно по 65, но выручку они приносят очень по-разному: верхняя четверть — 41.5 %, нижняя — 10.3 %. Равное число строк — не равные суммы, и именно это показывает анализ.
:::

```python
import duckdb
import pandas as pd

toy = pd.DataFrame({"guest": list("ABCDEFGHIJ"),
                    "spent": [900, 850, 700, 640, 600, 420, 380, 300, 150, 120]})
q = duckdb.sql("SELECT guest, spent, NTILE(4) OVER (ORDER BY spent DESC) AS q FROM toy ORDER BY spent DESC").df()
print(q["q"].tolist())
```

Что здесь происходит: `NTILE(4) OVER (ORDER BY spent DESC)` выстраивает гостей по убыванию суммы и раздаёт номера групп от 1 до 4. Вывод — `[1, 1, 1, 2, 2, 2, 3, 3, 4, 4]`, размеры групп 3, 3, 2, 2.

### На реальных данных: вклад верхней четверти гостей

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv")
duckdb.sql("""
    WITH g AS (                                   -- шаг 1: сумма покупок каждого гостя
        SELECT client_id, SUM(amount) AS spent
        FROM df
        WHERE client_id IS NOT NULL
        GROUP BY client_id
    ),
    q AS (                                        -- шаг 2: номер четверти
        SELECT *, NTILE(4) OVER (ORDER BY spent DESC, client_id) AS quartile
        FROM g
    )
    SELECT quartile, COUNT(*) AS guests, SUM(spent) AS revenue,
           ROUND(100 * SUM(spent) / SUM(SUM(spent)) OVER (), 1) AS pct,
           MIN(spent) AS min_spent
    FROM q
    GROUP BY quartile
    ORDER BY quartile
""").df()
```

Что здесь происходит:

- В CTE `g` — по строке на гостя с картой; заказы без карты отброшены, их нельзя приписать конкретному человеку.
- `NTILE(4) OVER (ORDER BY spent DESC, client_id)` — `client_id` вторым ключом нужен, чтобы гости с одинаковой суммой не перескакивали между группами от запуска к запуску.
- Внешний запрос сворачивает четверти и считает долю каждой — уже знакомым приёмом `SUM(SUM(...)) OVER ()`.

Как читать результат: 260 гостей с картой делятся ровно по 65. Верхняя четверть (тратили от 2158 ₽ за три месяца) даёт 41.5 % выручки гостей с картой, нижняя — 10.3 %. Значит, программу удержания разумно начинать с первой четверти: потеря одного такого гостя стоит как потеря четырёх из нижней (177 659 ₽ против 43 928 ₽ на 65 гостей).

::: deep NTILE и pd.qcut — не одно и то же
`NTILE` делит **строки** на равные по численности группы. `pd.qcut(spent, 4)` делит по **значениям** — по квантилям. При ничьих на границе `qcut` положит равных гостей в одну группу, и группы выйдут неравными, а `NTILE` разведёт их по разным группам по второму ключу.

Точный аналог `NTILE` — функция `array_split` из **numpy**. numpy — библиотека для работы с массивами чисел, на ней построен сам pandas; в курсе она понадобится позже, здесь — только для сравнения. `np.array_split(строки, 4)` режет список на 4 части и тоже отдаёт лишние элементы первым частям:

```python
import numpy as np
parts = np.array_split(list(range(10)), 4)   # 10 строк → 4 части
print([len(p) for p in parts])               # [3, 3, 2, 2] — как NTILE(4)
```
:::

::: warn Типичные ошибки
- **Квартиль ≠ равные суммы.** `NTILE(4)` даёт равное число **гостей**, а не равную выручку. Выручка по четвертям как раз и отличается — в этом смысл анализа.
- **`NTILE` без второго ключа сортировки.** Гости с равной суммой на границе групп попадают то в одну, то в другую; итоговые доли меняются от запуска к запуску.
:::

{{practice: w-ntile}}

## Соседние строки: LAG и LEAD

Зачем: «на сколько выросла выручка кофейни к прошлому месяцу?», «через сколько дней гость вернулся?». Оба вопроса требуют сравнить строку с **соседней** — предыдущей или следующей в заданном порядке. В Excel вы бы сослались на ячейку строкой выше. В SQL для этого есть `LAG` (значение из предыдущей строки) и `LEAD` (из следующей).

### Игрушечный пример руками

Выручка трёх дней: 100, 120, 90.

| день | выручка | `LAG(выручка)` | разница | `LEAD(выручка)` |
|---|---|---|---|---|
| 1 | 100 | — (`NULL`) | — | 120 |
| 2 | 120 | 100 | 120 − 100 = +20 | 90 |
| 3 | 90 | 120 | 90 − 120 = −30 | — (`NULL`) |

У первой строки нет предыдущей, у последней — следующей: там `NULL`. Если нужен ноль или другое значение, его передают третьим аргументом: `LAG(revenue, 1, 0)`. Второй аргумент — на сколько строк смотреть назад: `LAG(revenue, 7)` — неделю назад, если строки — дни.

### Сколько дней до следующего заказа

`LEAD` часто берут от даты: «когда гость пришёл в следующий раз?». Тогда нужна ещё разница двух дат в днях. Гость заказывал 3, 10 и 12 сентября:

| день | `LEAD(день)` | дней до следующего |
|---|---|---|
| 3 сентября | 10 сентября | 10 − 3 = 7 |
| 10 сентября | 12 сентября | 12 − 10 = 2 |
| 12 сентября | `NULL` | `NULL` |

В DuckDB разницу дат в днях даёт обычное вычитание `next_day - day` или функция `date_diff('day', day, next_day)` — результат одинаковый, целое число дней.

```python
import duckdb
import pandas as pd

t = pd.DataFrame({"day": pd.to_datetime(["2026-09-03", "2026-09-10", "2026-09-12"])})
duckdb.sql("""
    WITH x AS (
        SELECT CAST(day AS DATE) AS day,
               LEAD(CAST(day AS DATE)) OVER (ORDER BY day) AS next_day
        FROM t
    )
    SELECT day, next_day,
           next_day - day                AS days,       -- вычитание дат: число дней
           date_diff('day', day, next_day) AS days2     -- то же функцией
    FROM x
    ORDER BY day
""").df()
```

`CAST(... AS DATE)` отрезает время. Без него вычитание двух моментов времени дало бы не число дней, а интервал: для заказов в 21:00 и в 9:00 следующего дня — `12:00:00`. В SQL Server то же делает `DATEDIFF(day, day, next_day)`.

::: predict
```python static
import duckdb
import pandas as pd
t = pd.DataFrame({"day": [1, 2, 3], "revenue": [100, 120, 90]})
r = duckdb.sql("""
    SELECT day, revenue - LAG(revenue) OVER (ORDER BY day) AS diff
    FROM t ORDER BY day
""").fetchall()
for day, diff in r:
    print(day, diff)
```

- `1 0 | 2 20 | 3 -30`
- [x] `1 None | 2 20 | 3 -30`
- `1 20 | 2 -30 | 3 None`

Почему: у первого дня предыдущего нет, `LAG` даёт `NULL`, а `120 - NULL` в SQL — тоже `NULL`; в Python он приходит как `None`. Ноль был бы только с `LAG(revenue, 1, 0)`.
:::

### На реальных данных: месяц к месяцу по кофейням

```python
import duckdb
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
duckdb.sql("""
    WITH m AS (
        SELECT shop_id, date_trunc('month', datetime) AS month, SUM(amount) AS revenue
        FROM df
        GROUP BY shop_id, month
    )
    SELECT shop_id, month, revenue,
           LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month) AS prev,
           ROUND(100 * (revenue / LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month) - 1), 1) AS growth_pct
    FROM m
    ORDER BY shop_id, month
""").df()
```

Что здесь происходит:

- `PARTITION BY shop_id` — у каждой кофейни своя цепочка месяцев. Без него все 18 строк выстроились бы в одну цепочку по месяцам, и «прошлым месяцем» для октября KZN-1 оказалась бы строка какой-то другой кофейни — сентябрьская или даже октябрьская.
- `ORDER BY month` внутри окна задаёт, что считать «предыдущим». Порядок строк в самом результате задаёт уже внешний `ORDER BY`.
- `revenue / prev - 1` — относительный рост: 1.05 − 1 = 0.05, то есть +5 %.

Как читать результат: в октябре выручка упала у двух старых кофеен — PRM-1 (−8.1 %) и KZN-1 (−5.1 %), а младшие росли, сильнее всех UFA-1 (+32.8 %). В ноябре PRM-1 и KZN-1 отыгрались (+14.5 % и +24.3 %), а PRM-2 просела на 6.0 %.

::: figure lag-partition
Две кофейни из этого запроса. Слева окно с `PARTITION BY shop_id`: у каждой кофейни своя цепочка, и первый месяц каждой получает `NULL`. Справа окно без `PARTITION BY`, только `ORDER BY shop_id, month`: шесть строк выстроились в одну цепочку. Сентябрь PRM-1 сравнился с ноябрём KZN-1 и получил «рост» −8.3 %. Запрос при этом не упал.
:::

::: deep Аналог в pandas: shift
В pandas `LAG` — это `shift(1)`, `LEAD` — `shift(-1)`, внутри групп — после `groupby`:

```python
import pandas as pd

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
m = (df.groupby(["shop_id", df["datetime"].dt.to_period("M")])["amount"].sum()
       .rename("revenue").reset_index()
       .sort_values(["shop_id", "datetime"]))                     # порядок важен: shift берёт соседа по таблице
m["prev"] = m.groupby("shop_id")["revenue"].shift(1)              # LAG(...) OVER (PARTITION BY shop_id ORDER BY month)
m["growth_pct"] = (100 * (m["revenue"] / m["prev"] - 1)).round(1)
m.head(6)
```

Разница в одном важном месте: в SQL порядок задан **внутри окна**, а `shift` берёт соседа по текущему порядку строк таблицы. Забыли `sort_values` — получили «прошлый месяц» из случайной строки.
:::

::: warn Типичные ошибки
- **`LAG` без `PARTITION BY`.** Все кофейни сливаются в одну цепочку, и строки разных кофеен сравниваются друг с другом: при `ORDER BY shop_id, month` первый месяц каждой кофейни — с последним месяцем предыдущей, при `ORDER BY month` — с соседней кофейней. Ошибки не будет, только неверные цифры — проверяйте, что у первого месяца каждой группы стоит `NULL`.
- **Пропуски в датах.** `LAG` берёт предыдущую **строку**, а не предыдущий день. Если 9 сентября заказов не было, у 10 сентября «вчера» окажется 8-м. Для календарных сравнений сначала достройте недостающие дни или используйте рамку `RANGE` — о ней урок «Рамки окна SQL: накопительные итоги и скользящие средние».
:::

{{practice: w-lag, w-lead}}

### Шпаргалка: оконная функция → pandas

Для справки, запоминать не нужно: в задачах этого урока pandas-аналоги не требуются.

| SQL | pandas |
|---|---|
| `SUM(x) OVER ()` | `df[x].sum()` |
| `SUM(x) OVER (PARTITION BY g)` | `df.groupby(g)[x].transform("sum")` |
| `ROW_NUMBER() OVER (PARTITION BY g ORDER BY t)` | `df.sort_values(t).groupby(g).cumcount() + 1` |
| `RANK()` / `DENSE_RANK()` | `groupby(g)[x].rank(method="min")` / `rank(method="dense")` |
| `NTILE(n) OVER (ORDER BY x)` | одной функции нет; см. блок «NTILE и pd.qcut — не одно и то же» |
| `LAG(x)` / `LEAD(x)` | `groupby(g)[x].shift(1)` / `shift(-1)` после сортировки |
| `QUALIFY условие` | фильтр по готовому столбцу: `df[df["rnk"] <= 3]` |

Накопительные итоги, скользящие средние и `FIRST_VALUE`/`LAST_VALUE` — в следующем уроке, там своя часть шпаргалки.

## Практика

## task: w-share | Доля кофеен в два шага | warmup

Соберите программу: сначала выручка по кофейням (`by_shop`), потом поверх неё — доля каждой кофейни в выручке сети через оконную функцию (`shares`, по убыванию доли).

### parsons
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_shop = duckdb.sql("SELECT shop_id, SUM(amount) AS revenue FROM df GROUP BY shop_id").df()
shares = duckdb.sql("SELECT shop_id, revenue, ROUND(100 * revenue / SUM(revenue) OVER (), 1) AS pct FROM by_shop ORDER BY pct DESC").df()
print(shares)
```

### check
```python
import pandas as _pd
_r = _pd.read_csv('orders_3m.csv').groupby('shop_id')['amount'].sum()
_w = (100 * _r / _r.sum()).round(1).sort_values(ascending=False)
s = need('shares', _pd.DataFrame)
assert s['shop_id'].tolist() == list(_w.index), f'Порядок кофеен: {s["shop_id"].tolist()}. Нужен по убыванию доли.'
assert all(abs(float(a) - b) < 0.051 for a, b in zip(s['pct'], _w.values)), 'Доли не совпадают с ожидаемыми.'
```

### hint
Второй запрос обращается к таблице `by_shop`, значит, она должна появиться раньше. А саму таблицу заказов `df` нужно загрузить ещё до неё.

### hint
`SUM(revenue) OVER ()` — сумма выручек всех кофеен, то есть итог сети. Порядок: импорт → `df` → `by_shop` → `shares` → `print`.

## task: w-number | Номер заказа гостя | warmup

Пронумеруйте заказы каждого гостя с картой по времени: `numbered` — DataFrame со столбцами `client_id`, `datetime`, `n`, где `n` = 1 у первого заказа гостя, 2 — у второго и так далее. Заказы без карты не нужны. Затем сохраните в `second_orders` число строк с `n = 2` — сколько гостей вернулись хотя бы раз.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

numbered = duckdb.sql("""
    SELECT client_id, datetime,
           ... AS n
    FROM df
    WHERE client_id IS NOT NULL
""").df()
second_orders = ...
print(second_orders)
```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime']).dropna(subset=['client_id'])
_w = (_d.groupby('client_id').size() >= 2).sum()
b = need('numbered', _pd.DataFrame)
assert list(b.columns) == ['client_id', 'datetime', 'n'], f'Столбцы: {list(b.columns)}, а нужны client_id, datetime, n.'
assert len(b) == len(_d), f'Строк {len(b)}, а заказов с картой {len(_d)}. Нумерация не должна ни сворачивать, ни терять строки.'
_m = b.merge(_d.assign(_k=_d.sort_values('datetime').groupby('client_id').cumcount() + 1)[['client_id', 'datetime', '_k']], on=['client_id', 'datetime'])
assert (_m['n'] == _m['_k']).all(), 'Номера не совпадают с порядком заказов. Внутри OVER нужны PARTITION BY client_id и ORDER BY datetime.'
assert int(need('second_orders')) == _w, f'second_orders = {need("second_orders")}, а гостей со вторым заказом {_w}.'
```

### hint
Нумерация внутри гостя по времени — `ROW_NUMBER()` с окном: части — гости, порядок — время заказа.

### hint
`ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime) AS n`; число строк с `n == 2` — `(numbered["n"] == 2).sum()`.

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

numbered = duckdb.sql("""
    SELECT client_id, datetime,
           ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime) AS n
    FROM df
    WHERE client_id IS NOT NULL
""").df()
second_orders = int((numbered["n"] == 2).sum())
print(second_orders)
```

## task: w-ties | Топ-2 напитка с ничьими | base

Найдите `top2` — напитки, которые занимают **первое или второе место** по числу заказов в своей кофейне; если напитки набрали одинаково, оба получают одно место и оба попадают в список. Столбцы: `shop_id`, `drink`, `n` (число заказов), `place`. Порядок строк: по `shop_id`, затем по `place`, затем по `drink`. Отбор по месту сделайте в SQL (`QUALIFY` или внешний запрос).

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
_c = _pd.read_csv('orders_3m.csv').groupby(['shop_id', 'drink']).size().rename('n').reset_index()
_c['place'] = _c.groupby('shop_id')['n'].rank(method='dense', ascending=False).astype(int)
_w = _c[_c['place'] <= 2].sort_values(['shop_id', 'place', 'drink']).reset_index(drop=True)
b = need('top2', _pd.DataFrame)
assert list(b.columns) == ['shop_id', 'drink', 'n', 'place'], f'Столбцы: {list(b.columns)}, а нужны shop_id, drink, n, place.'
assert len(b) != 12 or len(_w) == 12, 'Строк ровно 12 — по две на кофейню. Похоже, ничьи потерялись: ROW_NUMBER не даёт равным одно место.'
assert len(b) == len(_w), f'Строк {len(b)}, а нужно {len(_w)}. Проверьте функцию ранга: при ничьей на втором месте в список должны попасть оба напитка.'
assert b['drink'].tolist() == _w['drink'].tolist() and [int(x) for x in b['place']] == _w['place'].tolist(), 'Напитки или места не совпадают. Порядок: shop_id, place, drink.'
assert 'QUALIFY' in _code.upper() or 'WITH' in _code.upper() or _code.upper().count('SELECT') >= 2, 'Отберите места в SQL: QUALIFY или внешний запрос над CTE.'
```

### hint
Нужна функция, которая даёт равным одно место и не пропускает следующее: так «топ-2» останется топом двух **уровней**.

### hint
Сгруппируйте по `shop_id, drink`, посчитайте `COUNT(*) AS n` и добавьте `DENSE_RANK() OVER (PARTITION BY shop_id ORDER BY COUNT(*) DESC) AS place`. Отбор — `QUALIFY place <= 2`.

### hint
```python
top2 = duckdb.sql("""
    SELECT shop_id, drink, COUNT(*) AS n,
           DENSE_RANK() OVER (PARTITION BY shop_id ORDER BY ...) AS place
    FROM df
    GROUP BY shop_id, drink
    QUALIFY ...
    ORDER BY shop_id, place, drink
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

top2 = duckdb.sql("""
    SELECT shop_id, drink, COUNT(*) AS n,
           DENSE_RANK() OVER (PARTITION BY shop_id ORDER BY COUNT(*) DESC) AS place
    FROM df
    GROUP BY shop_id, drink
    QUALIFY place <= 2
    ORDER BY shop_id, place, drink
""").df()
top2
```

### explain
В списке 13 строк, а не 12: в UFA-1 латте и американо набрали по 34 заказа и оба стоят на втором месте. С `ROW_NUMBER` одна из них пропала бы, причём какая — решал бы случай. `RANK` здесь дал бы тот же результат, потому что ничья на последнем отбираемом месте. Разница была бы при ничьей на первом месте: `RANK` выдал бы 1, 1, 3, и «второго места» не было бы вовсе. В pandas: `cnt.groupby("shop_id")["n"].rank(method="dense", ascending=False)` и фильтр `<= 2`.

## task: w-ntile | Четверти гостей по тратам | base

Разбейте гостей с картой на четыре равные по численности группы по сумме покупок за три месяца (`NTILE(4)`, 1 — самые активные; при равных суммах вторым ключом — `client_id`). Результат `quart` — DataFrame со столбцами `quartile`, `guests`, `revenue`, `pct` (доля четверти в выручке гостей с картой, %, один знак), по возрастанию `quartile`. Сохраните `top_pct` — `pct` первой четверти.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd, numpy as _np
_g = _pd.read_csv('orders_3m.csv').dropna(subset=['client_id']).groupby('client_id')['amount'].sum().reset_index()
_g = _g.sort_values(['amount', 'client_id'], ascending=[False, True]).reset_index(drop=True)
_g['q'] = _np.concatenate([_np.full(len(p), i + 1) for i, p in enumerate(_np.array_split(_np.arange(len(_g)), 4))])
_w = _g.groupby('q')['amount'].agg(['size', 'sum'])
_p = (100 * _w['sum'] / _w['sum'].sum()).round(1)
b = need('quart', _pd.DataFrame)
assert list(b.columns) == ['quartile', 'guests', 'revenue', 'pct'], f'Столбцы: {list(b.columns)}.'
assert [int(x) for x in b['guests']] == _w['size'].tolist(), f'Гостей по четвертям: {b["guests"].tolist()}. В каждой четверти должно быть поровну гостей с картой.'
assert all(abs(float(a) - y) < 1e-6 for a, y in zip(b['revenue'], _w['sum'])), 'Выручка четвертей не совпадает. Проверьте порядок внутри NTILE: по убыванию суммы, потом client_id.'
assert all(abs(float(a) - y) < 0.051 for a, y in zip(b['pct'], _p)), 'pct не совпадает: доля от суммы всех четвертей, в процентах.'
assert abs(float(need('top_pct')) - _p.iloc[0]) < 0.051, f'top_pct = {need("top_pct")}, а нужна доля первой четверти.'
```

### hint
Три шага: сумма покупок на гостя → номер четверти для каждого гостя → свёртка по четвертям с долей от итога. Удобно оформить двумя CTE.

### hint
Второй шаг: `NTILE(4) OVER (ORDER BY spent DESC, client_id) AS quartile`. Третий: `GROUP BY quartile`, а доля — `100 * SUM(spent) / SUM(SUM(spent)) OVER ()`.

### hint
```python
quart = duckdb.sql("""
    WITH g AS (SELECT client_id, SUM(amount) AS spent FROM df WHERE ... GROUP BY client_id),
         q AS (SELECT *, NTILE(4) OVER (ORDER BY ...) AS quartile FROM g)
    SELECT quartile, COUNT(*) AS guests, SUM(spent) AS revenue,
           ROUND(100 * SUM(spent) / SUM(SUM(spent)) OVER (), 1) AS pct
    FROM q GROUP BY quartile ORDER BY quartile
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv")

quart = duckdb.sql("""
    WITH g AS (
        SELECT client_id, SUM(amount) AS spent
        FROM df
        WHERE client_id IS NOT NULL
        GROUP BY client_id
    ),
    q AS (
        SELECT *, NTILE(4) OVER (ORDER BY spent DESC, client_id) AS quartile
        FROM g
    )
    SELECT quartile, COUNT(*) AS guests, SUM(spent) AS revenue,
           ROUND(100 * SUM(spent) / SUM(SUM(spent)) OVER (), 1) AS pct
    FROM q
    GROUP BY quartile
    ORDER BY quartile
""").df()
top_pct = float(quart.loc[0, "pct"])
quart
```

### explain
Четверть самых активных гостей — 65 человек — приносит 41.5 % выручки гостей с картой, нижняя — 10.3 %. Если бы распределение было равным, каждая давала бы 25 %. Без `WHERE client_id IS NOT NULL` все заказы без карты собрались бы в одного «гостя» `NULL` с огромной суммой: он попал бы в первую четверть и исказил её долю. Без второго ключа `client_id` гости с равной суммой на границе четвертей могли бы меняться местами от запуска к запуску.

## task: w-lag | Где выручка упала | base

Посчитайте `mom_shop` — DataFrame со столбцами `shop_id`, `month`, `revenue`, `growth_pct`: выручка каждой кофейни по месяцам и рост к прошлому месяцу **этой же кофейни** в процентах с одним знаком (у первого месяца — пусто), по `shop_id` и `month`. Затем отберите в `falls` строки, где выручка упала (`growth_pct < 0`).

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
_m = _d.groupby(['shop_id', _d['datetime'].dt.to_period('M')])['amount'].sum().rename('revenue').reset_index()
_m['g'] = (100 * (_m['revenue'] / _m.groupby('shop_id')['revenue'].shift(1) - 1)).round(1)
b = need('mom_shop', _pd.DataFrame)
assert list(b.columns) == ['shop_id', 'month', 'revenue', 'growth_pct'], f'Столбцы: {list(b.columns)}.'
assert len(b) == len(_m), f'Строк {len(b)}, а пар «кофейня × месяц» {len(_m)}.'
assert b['shop_id'].tolist() == _m['shop_id'].tolist(), 'Порядок строк: по shop_id, затем по month.'
_g = b['growth_pct'].tolist()
_firsts = [i for i in range(len(_m)) if i == 0 or _m['shop_id'][i] != _m['shop_id'][i - 1]]
assert all(_pd.isna(_g[i]) for i in _firsts), 'У первого месяца каждой кофейни рост должен быть пустым. Похоже, в окне нет PARTITION BY shop_id.'
assert all(_pd.isna(x) and _pd.isna(y) or abs(float(x) - y) < 0.051 for x, y in zip(_g, _m['g'])), 'growth_pct не совпадает с ожидаемым.'
f = need('falls', _pd.DataFrame)
assert sorted(f['shop_id'].tolist()) == sorted(_m.loc[_m['g'] < 0, 'shop_id'].tolist()), f'В falls кофейни {sorted(f["shop_id"].tolist())}. Нужны все строки с отрицательным ростом.'
```

### hint
Сначала CTE «кофейня × месяц», потом `LAG(revenue)` с окном, где у каждой кофейни своя цепочка месяцев.

### hint
`LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month)`; рост — `ROUND(100 * (revenue / LAG(...) OVER (...) - 1), 1)`. Падения: `mom_shop[mom_shop["growth_pct"] < 0]` — строки с пустым ростом в этот фильтр не попадут.

### hint
```python
mom_shop = duckdb.sql("""
    WITH m AS (
        SELECT shop_id, date_trunc('month', datetime) AS month, SUM(amount) AS revenue
        FROM df GROUP BY shop_id, month
    )
    SELECT shop_id, month, revenue,
           ROUND(100 * (revenue / LAG(revenue) OVER (...) - 1), 1) AS growth_pct
    FROM m
    ORDER BY shop_id, month
""").df()
falls = mom_shop[...]
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

mom_shop = duckdb.sql("""
    WITH m AS (
        SELECT shop_id, date_trunc('month', datetime) AS month, SUM(amount) AS revenue
        FROM df
        GROUP BY shop_id, month
    )
    SELECT shop_id, month, revenue,
           ROUND(100 * (revenue / LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month) - 1), 1) AS growth_pct
    FROM m
    ORDER BY shop_id, month
""").df()
falls = mom_shop[mom_shop["growth_pct"] < 0]
falls
```

### explain
Падений три: KZN-1 и PRM-1 в октябре (−5.1 % и −8.1 %) и PRM-2 в ноябре (−6.0 %). Без `PARTITION BY shop_id` кофейни слились бы в одну цепочку. Если в окне `ORDER BY shop_id, month`, первый месяц каждой кофейни сравнится с ноябрём предыдущей по алфавиту: сентябрь KZN-2 (28 291 ₽) против ноября KZN-1 (68 368 ₽) дал бы мнимое падение на 58.6 %. Признак такой ошибки — у первых месяцев кофеен, кроме самой первой, рост не пустой. Фильтр по `growth_pct` можно было написать и в SQL: `QUALIFY growth_pct < 0`.

## task: w-lead | Через сколько дней гость возвращается | base

Для каждого заказа гостя с картой найдите дату его **следующего** заказа (`LEAD`) и число дней между ними. Результат `gaps` — DataFrame со столбцами `client_id`, `day`, `next_day`, `days` — только строки, у которых следующий заказ есть. Разница дат в днях — `next_day - day` или `date_diff('day', day, next_day)` (раздел «Сколько дней до следующего заказа»). Сохраните `avg_gap` — среднее `days`, округлённое до 1 знака, и `median_gap` — медиану `days`.

### starter
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime']).dropna(subset=['client_id']).sort_values('datetime')
_d['day'] = _d['datetime'].dt.normalize()
_d['nxt'] = _d.groupby('client_id')['day'].shift(-1)
_d = _d.dropna(subset=['nxt'])
_g = (_d['nxt'] - _d['day']).dt.days
b = need('gaps', _pd.DataFrame)
assert list(b.columns) == ['client_id', 'day', 'next_day', 'days'], f'Столбцы: {list(b.columns)}.'
assert b['next_day'].notna().all(), 'В gaps есть строки без следующего заказа — уберите их (у последнего заказа гостя LEAD даёт NULL).'
assert len(b) == len(_d), f'Строк {len(b)}, а пар «заказ → следующий заказ» {len(_d)}. Окно: PARTITION BY client_id ORDER BY datetime.'
assert abs(float(need('avg_gap')) - round(_g.mean(), 1)) < 0.051, f'avg_gap = {need("avg_gap")}. Считайте дни между датами, а не между отметками времени.'
assert abs(float(need('median_gap')) - _g.median()) < 1e-6, f'median_gap = {need("median_gap")}, а медиана другая.'
```

### hint
`LEAD(день) OVER (PARTITION BY client_id ORDER BY datetime)` даёт день следующего заказа того же гостя. Последний заказ гостя получит `NULL` — его отбросьте во внешнем запросе или через `QUALIFY`.

### hint
День заказа — `CAST(datetime AS DATE)`. Разница в днях — `next_day - day` (или `date_diff('day', day, next_day)`). Среднее и медиана — `gaps["days"].mean()` и `gaps["days"].median()`.

### hint
```python
gaps = duckdb.sql("""
    WITH x AS (
        SELECT client_id, CAST(datetime AS DATE) AS day,
               LEAD(CAST(datetime AS DATE)) OVER (PARTITION BY ... ORDER BY ...) AS next_day
        FROM df
        WHERE client_id IS NOT NULL
    )
    SELECT client_id, day, next_day, date_diff('day', day, next_day) AS days
    FROM x
    WHERE ...
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

gaps = duckdb.sql("""
    WITH x AS (
        SELECT client_id, CAST(datetime AS DATE) AS day,
               LEAD(CAST(datetime AS DATE)) OVER (PARTITION BY client_id ORDER BY datetime) AS next_day
        FROM df
        WHERE client_id IS NOT NULL
    )
    SELECT client_id, day, next_day, date_diff('day', day, next_day) AS days
    FROM x
    WHERE next_day IS NOT NULL
""").df()
avg_gap = round(float(gaps["days"].mean()), 1)
median_gap = float(gaps["days"].median())
print(avg_gap, median_gap)
```

### explain
Пар «заказ → следующий» 987: у 260 гостей 1247 заказов, и у каждого гостя последний заказ пары не имеет (1247 − 260 = 987). В среднем гость возвращается через 14.4 дня, медиана — 11 дней. Среднее больше медианы: несколько очень долгих перерывов тянут его вверх. Поэтому для «типичного» гостя честнее медиана. Если считать разницу между отметками времени, а не датами, заказы в 21:00 и в 9:00 следующего дня дадут 0 полных дней — и среднее уползёт вниз. В pandas `LEAD` — это `groupby("client_id")["day"].shift(-1)` после сортировки по времени.

## task: w-streak | Самая длинная серия дней без пропусков | star

Для каждой кофейни найдите самую длинную серию дней подряд, в каждый из которых был хотя бы один заказ. Результат `streaks` — DataFrame со столбцами `shop_id`, `start`, `finish`, `days`, по одной строке на кофейню (если серий одинаковой длины несколько — самую раннюю), по возрастанию `shop_id`.

Подсказка к идее: если пронумеровать дни кофейни по порядку, то у дней, идущих подряд, разность «дата минус номер» одинаковая.

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
_rows = []
for _s, _g in _d.groupby('shop_id'):
    _days = sorted(_g['datetime'].dt.normalize().unique())
    _best, _cur = None, [_days[0], _days[0], 1]
    for _a, _b in zip(_days, _days[1:]):
        if (_b - _a).days == 1:
            _cur = [_cur[0], _b, _cur[2] + 1]
        else:
            _best = _cur if _best is None or _cur[2] > _best[2] else _best
            _cur = [_b, _b, 1]
    _best = _cur if _best is None or _cur[2] > _best[2] else _best
    _rows.append((_s, str(_pd.Timestamp(_best[0]).date()), str(_pd.Timestamp(_best[1]).date()), _best[2]))
b = need('streaks', _pd.DataFrame)
assert list(b.columns) == ['shop_id', 'start', 'finish', 'days'], f'Столбцы: {list(b.columns)}.'
assert len(b) == 6, f'Строк {len(b)}, а кофеен 6: оставьте по одной серии на кофейню.'
_got = [(r.shop_id, str(r.start)[:10], str(r.finish)[:10], int(r.days)) for r in b.itertuples()]
for g, w in zip(_got, _rows):
    assert g[3] == w[3], f'{w[0]}: серия {g[3]} дн., а самая длинная — другой длины. Проверьте, что дни уникальны (DISTINCT) и что ключ серии — дата минус номер дня.'
    assert g == w, f'{w[0]}: длина верная, но даты {g[1]}–{g[2]} не те. Нужна самая ранняя из самых длинных серий.'
```

### hint
Шаг 1 — уникальные пары «кофейня × день» (`SELECT DISTINCT`). Шаг 2 — номер дня внутри кофейни `ROW_NUMBER()`. Если вычесть номер из даты, у всех дней одной серии получится одна и та же «опорная» дата — это ключ серии.

### hint
В DuckDB из даты можно вычесть целое число дней: `day - CAST(ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY day) AS INTEGER) AS grp`. Потом `GROUP BY shop_id, grp` с `MIN(day)`, `MAX(day)`, `COUNT(*)` — это серии.

### hint
```python
streaks = duckdb.sql("""
    WITH d AS (SELECT DISTINCT shop_id, CAST(datetime AS DATE) AS day FROM df),
         g AS (SELECT shop_id, day,
                      day - CAST(ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY day) AS INTEGER) AS grp
               FROM d),
         runs AS (SELECT shop_id, MIN(day) AS start, MAX(day) AS finish, COUNT(*) AS days
                  FROM g GROUP BY shop_id, grp)
    SELECT * FROM runs
    QUALIFY ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY ...) = 1
    ORDER BY shop_id
""").df()
```

### solution
```python
import duckdb
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

streaks = duckdb.sql("""
    WITH d AS (
        SELECT DISTINCT shop_id, CAST(datetime AS DATE) AS day
        FROM df
    ),
    g AS (
        SELECT shop_id, day,
               day - CAST(ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY day) AS INTEGER) AS grp
        FROM d
    ),
    runs AS (
        SELECT shop_id, MIN(day) AS start, MAX(day) AS finish, COUNT(*) AS days
        FROM g
        GROUP BY shop_id, grp
    )
    SELECT shop_id, start, finish, days
    FROM runs
    QUALIFY ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY days DESC, start) = 1
    ORDER BY shop_id
""").df()
streaks
```

### explain
Это классический приём «острова и пропуски» (gaps and islands). Дни 1, 2, 3 сентября получают номера 1, 2, 3, и «дата минус номер» у всех — 31 августа. После пропуска 9 сентября номер отстаёт от даты на день больше, и ключ меняется. KZN-1 и PRM-1 работали с заказами все 91 день, а у PRM-2 самая длинная серия — 25 дней (26 сентября — 20 октября). Без `DISTINCT` на первом шаге каждый заказ получил бы свой номер, и день с тремя заказами разорвал бы серию. В pandas ключ серии — `day - pd.to_timedelta(groupby("shop_id").cumcount(), unit="D")`.
