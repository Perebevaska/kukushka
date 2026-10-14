---
title: "Выбор столбцов и строк: SELECT и WHERE"
lead: "Как в pandas выбрать нужные столбцы и отфильтровать строки по условиям. Главная идея урока — «маска»: столбец из True/False, по которому таблица отбирает строки."
files: [orders_3m.csv]
recap:
  - "`df[[\"a\", \"b\"]]` — несколько столбцов (двойные скобки), `df[\"a\"]` — один столбец."
  - "Условие на столбец даёт маску: `df[\"amount\"] > 500`. `df[маска]` — строки, где `True`."
  - "Несколько условий: `&` (и), `|` (или), `~` (не), каждое условие — в скобках. `and`/`or` с таблицами не работают."
  - "`isin([...])` — как `IN`, `between(a, b)` — как `BETWEEN`, `.str.startswith()` / `.str.contains()` — как `LIKE`."
  - "`df.loc[маска, [\"столбцы\"]]` — строки и столбцы за раз; `df.query(\"amount > 500\")` — фильтр строкой."
  - "В `query` переменные Python — через `@`: `df.query(\"amount > @min_amount and shop_id in @shops\")`."
  - "Сколько строк подходит — `маска.sum()`; доля — `маска.mean()`."
---

## SELECT: выбрать столбцы

Один столбец — `df["имя"]`, это Series. Несколько столбцов — список имён в скобках, получается DataFrame. Отсюда двойные скобки: внешние — «выбрать», внутренние — список.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df[["order_id", "drink", "amount"]].head()
```

::: sql
`df[["order_id", "drink", "amount"]]` — это `SELECT order_id, drink, amount FROM orders`.
:::

{{practice: cols}}

## WHERE: маска

Отбор строк в pandas устроен через **маску**. Сравните столбец с числом — получится столбец из `True` и `False`, по одному значению на строку:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

mask = df["amount"] > 600
mask.head(8)
```

Если передать маску в квадратных скобках, таблица оставит только строки, где `True`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

big = df[df["amount"] > 600]
print(len(big), "крупных заказов")
big.head()
```

Запись `df[df["amount"] > 600]` поначалу выглядит странно, но читается так: «из `df` взять строки, где `df["amount"] > 600`».

::: figure mask-filter
Пять заказов из «Разберём вместе» ниже: сравнение даёт маску, `df[маска]` оставляет строки с True. Индекс строк сохраняется.
:::

::: tip Аналогия
Трафарет для покраски: краска ложится только там, где в листе прорезано окошко. Маска — трафарет для строк: `True` — окошко открыто, строка попадает в результат; `False` — закрыто.
:::

::: sql
`df[df["amount"] > 600]` — `SELECT * FROM orders WHERE amount > 600`.
:::

Сколько строк прошло фильтр, можно узнать и без самой таблицы: в маске `True` считается как 1.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
print((df["channel"] == "доставка").sum(), "доставок")
print(round((df["channel"] == "доставка").mean() * 100, 1), "% заказов — доставка")
```

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"x": [5, 10, 15]})
print(len(df[df["x"] > 5]))
```

- `3`
- [x] `2`
- `1`

Почему: условию «больше 5» удовлетворяют 10 и 15. Пятёрка не проходит — она не больше пяти.
:::

{{practice: big, delivery}}

## Несколько условий: &, |, ~

Условия объединяют знаками `&` (и), `|` (или) и `~` (не). **Каждое условие — в своих скобках**:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

delivery_big = df[(df["channel"] == "доставка") & (df["amount"] > 500)]
print(len(delivery_big))

not_hall = df[~(df["channel"] == "зал")]
print(len(not_hall))
```

::: warn
Привычные `and` и `or` с таблицами не работают — Python не знает, как превратить целый столбец в одно `True` или `False`, и падает:

```python error
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df[(df["channel"] == "доставка") and (df["amount"] > 500)]
```

Правило: условия соединяют `&` (и) и `|` (или), а каждое условие берут в свои скобки.
:::

::: deep Три причины ошибки `The truth value of a Series is ambiguous`
1. В коде `and` или `or` между условиями — замените на `&` и `|`.
2. Целый столбец (Series) попал туда, где ждут одно значение, — в `if`, в сравнение с числом, в проверку задачи. Так бывает, когда вместо одного числа в переменной оказался кусок таблицы. Ищите переменную, в которой лежит Series.
3. Забытые скобки вокруг числовых условий — о них ниже.
:::

**Если забыть скобки.** У `&` приоритет выше, чем у `==` и `>`: Python сначала попробует выполнить `"S" & df["channel"]` — «и» между строкой и столбцом — и упадёт:

```python error
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df[df["size"] == "S" & df["channel"] == "зал"]
```

`TypeError: unsupported operand type(s) for &: 'str' and 'StringArray'` — читается как «`&` не умеет работать со строкой и текстовым столбцом». Дело не в типах, а в скобках. Правило: увидели `unsupported operand type(s) for &` или `|` — возьмите каждое условие в свои скобки.

Если же оба условия числовые — `df["amount"] > 500 & df["qty"] > 1`, — то `500 & df["qty"]` посчитается без ошибки (`&` для целых чисел определён), а дальше Python склеит два сравнения в цепочку и упадёт с уже знакомым `The truth value of a Series is ambiguous` — хотя `and` в коде нет. Поэтому при любой из этих двух ошибок сначала проверьте, что каждое условие стоит в своих скобках.

### Разберём вместе: маски на пяти заказах

| заказ | канал | сумма | доставка? | > 500? | `&` | `\|` |
|---|---|---|---|---|---|---|
| 1 | зал | 320 | False | False | False | False |
| 2 | доставка | 610 | True | True | **True** | True |
| 3 | доставка | 450 | True | False | False | True |
| 4 | с собой | 720 | False | True | False | True |
| 5 | зал | 290 | False | False | False | False |

1. Каждое сравнение даёт свой столбец `True/False` — по значению на строку.
2. `&` сравнивает два столбца построчно: `True` только там, где оба `True` — заказ 2.
3. `|` даёт `True`, если хотя бы одно `True` — заказы 2, 3, 4.
4. `~(канал == "доставка")` переворачивает первый столбец: `True` у заказов 1, 4, 5.

```python
import pandas as pd
t = pd.DataFrame({"channel": ["зал", "доставка", "доставка", "с собой", "зал"],
                  "amount": [320, 610, 450, 720, 290]})
d, big = t["channel"] == "доставка", t["amount"] > 500
print((d & big).tolist())
print((d | big).tolist())
print((~d).tolist())
```

Что получилось: маска — это просто ещё один столбец. Его можно посмотреть, сложить (`sum` — число строк) и усреднить (`mean` — доля), прежде чем фильтровать таблицу. Если фильтр даёт странный результат, распечатайте маску — ошибка почти всегда видна сразу.

::: warn Типичные ошибки
- **`and` / `or` вместо `&` / `|`.** Ошибка `The truth value of a Series is ambiguous`.
- **Нет скобок вокруг условий.** `df["a"] > 1 & df["b"] < 2` выполнит `&` раньше сравнений. Признак — `TypeError: unsupported operand type(s) for &`, а у числовых условий — `The truth value of a Series is ambiguous`.
- **Одинарные скобки для нескольких столбцов.** `df["drink", "amount"]` — ошибка; список столбцов — `df[["drink", "amount"]]`.
- **`=` вместо `==`.** Внутри маски нужно сравнение, а не присваивание.
:::

::: quiz
Почему `df[df["amount"] > 500 and df["channel"] == "доставка"]` падает с ошибкой?

- [x] `and` работает с одним True/False, а здесь сравниваются целые столбцы — нужен `&` и скобки
  > Маска — столбец из тысяч True/False. Поэлементное «и» в pandas — `&`, а каждое условие берут в скобки: `(df["amount"] > 500) & (df["channel"] == "доставка")`.
- [ ] Нельзя фильтровать по двум столбцам сразу
  > Можно сколько угодно условий, если соединять их через `&` или `|`.
- [ ] Строку «доставка» нужно писать в одинарных кавычках
  > Одинарные и двойные кавычки в Python равноправны.
- [ ] Сначала нужно отфильтровать по сумме, потом отдельно по каналу
  > Так тоже получится, но причина ошибки не в этом, а в `and`.
:::

{{practice: and, fix-and, share}}

## IN, BETWEEN, LIKE

Для частых условий есть готовые методы:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

kazan = df[df["shop_id"].isin(["KZN-1", "KZN-2"])]                # IN (...)
mid = df[df["amount"].between(300, 500)]                         # BETWEEN 300 AND 500
october = df[df["datetime"].str.startswith("2026-10")]           # LIKE '2026-10%'
with_f = df[df["drink"].str.contains("ф", case=False)]           # LIKE '%ф%' без учёта регистра
print(len(kazan), len(mid), len(october), len(with_f))
```

`between` включает обе границы — как в SQL. У текстовых столбцов есть набор строковых методов после `.str`: `startswith`, `contains`, `lower`, `len` и другие — те же, что у обычных строк из урока «Строки и f-строки» главы 1.

::: sql
| SQL | pandas |
|---|---|
| `WHERE a = 1` | `df[df["a"] == 1]` |
| `WHERE a IN (1, 2)` | `df[df["a"].isin([1, 2])]` |
| `WHERE a BETWEEN 1 AND 5` | `df[df["a"].between(1, 5)]` |
| `WHERE s LIKE 'abc%'` | `df[df["s"].str.startswith("abc")]` |
| `WHERE s LIKE '%abc%'` | `df[df["s"].str.contains("abc")]` |
| `WHERE a IS NULL` | `df[df["a"].isna()]` |
| `WHERE NOT (…)` | `df[~(…)]` |
:::

{{practice: isin, october}}

## loc: строки и столбцы сразу

Чтобы сразу отфильтровать строки и выбрать столбцы, используют `loc`: сначала строки (маска), через запятую — столбцы.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df.loc[df["size"] == "L", ["drink", "qty", "amount"]].head()
```

::: figure loc-grid
Маска выбирает строки, список — столбцы; `loc` возвращает их пересечение (зелёные ячейки).
:::

`loc` — основной и самый надёжный способ «и отобрать, и изменить» в pandas. Он ещё пригодится в следующем уроке, когда будем менять значения.

Есть и `iloc` — по номерам позиций, как срезы списка: `df.iloc[:3]` — первые три строки, `df.iloc[:3, :2]` — и первые два столбца.

{{practice: p-loc, loc}}

## query: условие строкой

Длинные условия иногда удобнее записать строкой — почти как `WHERE` в SQL:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df.query("channel == 'доставка' and amount > 500 and size == 'L'").head()
```

Внутри `query` можно писать `and`, `or`, `not`, `in`. Это просто удобная запись — результат тот же, что у маски.

### Переменные внутри query: @

Порог «крупного заказа» и список кофеен для отчёта обычно задают один раз — в начале блокнота, как параметры. Вписывать числа прямо в строку условия неудобно: порог поменялся — ищи его по всему коду. В `query` можно сослаться на обычную переменную Python, поставив перед её именем **`@`**.

::: sql
Это то же, что параметр запроса: `WHERE amount > :min_amount AND shop_id IN (:shops)`. Само условие остаётся неизменным, меняются только значения параметров.
:::

**Пример руками.** Пять заказов, порог `min_amount = 400`, список `kazan = ["KZN-1", "KZN-2"]`:

| shop_id | amount | `amount > 400` | `shop_id in kazan` | итог |
|---|---|---|---|---|
| KZN-1 | 300 | нет | да | нет |
| PRM-1 | 520 | да | нет | нет |
| KZN-2 | 610 | да | да | **да** |
| KZN-1 | 450 | да | да | **да** |
| UFA-1 | 700 | да | нет | нет |

Подходят две строки — 610 и 450. Кодом:

```python
import pandas as pd
t = pd.DataFrame({"shop_id": ["KZN-1", "PRM-1", "KZN-2", "KZN-1", "UFA-1"],
                  "amount": [300, 520, 610, 450, 700]})

min_amount = 400                 # параметры отчёта — в одном месте
kazan = ["KZN-1", "KZN-2"]
t.query("amount > @min_amount and shop_id in @kazan")
```

Что здесь происходит:

- `@min_amount` — «возьми значение переменной `min_amount` из Python». Без `@` pandas искал бы **столбец** с таким именем.
- `shop_id in @kazan` — то же, что маска `t["shop_id"].isin(kazan)`: строка проходит, если её кофейня есть в списке.
- Чтобы получить отчёт по другому порогу или городу, меняют только две строки с параметрами — условие не трогают.

::: figure query-at
В строке `query` имя без `@` — столбец таблицы, имя с `@` — переменная Python.
:::

На настоящих данных — сколько заказов дороже 500 ₽ в казанских кофейнях:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

min_amount = 500
kazan = ["KZN-1", "KZN-2"]
big_kzn = df.query("amount > @min_amount and shop_id in @kazan")
print(len(big_kzn), big_kzn["amount"].sum())
```

Таких заказов 152 на 97 913 ₽. Маской было бы `df[(df["amount"] > min_amount) & df["shop_id"].isin(kazan)]` — результат тот же, а с `@` условие читается как фраза.

::: warn Типичные ошибки
- **Забыли `@`.** `df.query("amount > min_amount")` падает с `UndefinedVariableError: name 'min_amount' is not defined`: pandas ищет столбец `min_amount` и не находит.
- **f-строка вместо `@`.** `df.query(f"drink == {name}")` превратится в `drink == Раф` без кавычек — и pandas решит, что `Раф` — имя столбца. С `@name` кавычки не нужны: значение передаётся как есть.
- **`@` вне `query`.** `df[df["amount"] > @min_amount]` — `SyntaxError`: `@` понимает только строка условия `query`. В обычной маске переменную пишут как есть: `df["amount"] > min_amount`.
:::

::: predict
```python static
import pandas as pd
print((pd.Series([1, 5, 9]) > 4).sum())
```

- `14`
- [x] `2`
- `[False, True, True]`

Почему: сравнение дало `[False, True, True]`, а сумма считает `True` как 1.
:::

{{practice: query-at, query}}

## Практика

## task: cols | Два столбца | warmup

Сохраните в `sub` таблицу только из столбцов `drink` и `amount` (в этом порядке).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
s = need('sub', _pd.DataFrame)
assert list(s.columns) == ['drink', 'amount'], f'Столбцы sub: {list(s.columns)}.'
assert len(s) == len(df), 'Строки при выборе столбцов не должны теряться.'
```

### hint
Внешние скобки — «взять из таблицы», внутренние — список столбцов.

### hint
Двойные скобки: `df[["drink", "amount"]]`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
sub = df[["drink", "amount"]]
```

## task: big | Крупные заказы | warmup

Сохраните в `big` заказы дороже 800 рублей и в `n_big` — их количество.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = d[d['amount'] > 800]
b = need('big', _pd.DataFrame)
assert len(b) == len(want) and (b['amount'] > 800).all(), f'В big {len(b)} строк, а заказов дороже 800 — {len(want)}.'
assert need('n_big') == len(want), f'n_big = {need("n_big")}.'
```

### hint
Сначала маска `df["amount"] > 800`, потом таблица по маске.

### hint
`big = df[df["amount"] > 800]`, `n_big = len(big)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
big = df[df["amount"] > 800]
n_big = len(big)
```

## task: p-loc | Соберите выборку через loc | warmup

Соберите программу, которая показывает напиток и сумму для заказов размера L с доставкой.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
mask = (df["size"] == "L") & (df["channel"] == "доставка")
result = df.loc[mask, ["drink", "amount"]]
print(len(result))
```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = ((d['size'] == 'L') & (d['channel'] == 'доставка')).sum()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Маска создаётся до того, как используется в `loc`.

### hint
Два условия — размер `"L"` и канал `"доставка"` — через `&`, каждое в скобках; в `loc` вторым аргументом — список `["drink", "amount"]`.

## task: delivery | Сколько доставок | warmup

Посчитайте `n_delivery` — число заказов с каналом `"доставка"`, без создания отфильтрованной таблицы: суммой маски.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = (_pd.read_csv('orders_3m.csv')['channel'] == 'доставка').sum()
assert need('n_delivery') == want, f'n_delivery = {need("n_delivery")}.'
assert 'sum()' in _code, 'Посчитайте суммой маски: (условие).sum().'
```

### hint
Сумма маски — число `True`, то есть строк, прошедших условие.

### hint
`n_delivery = (df["channel"] == "доставка").sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
n_delivery = (df["channel"] == "доставка").sum()
```

## task: and | Два условия | base

Посчитайте `revenue_big_delivery` — выручку от доставок дороже 500 рублей.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = d[(d['channel'] == 'доставка') & (d['amount'] > 500)]['amount'].sum()
assert need('revenue_big_delivery') == want, f'revenue_big_delivery = {need("revenue_big_delivery")}, а нужно {want}.'
```

### hint
Условия: канал равен «доставка» и сумма больше 500.

### hint
`df[(условие1) & (условие2)]["amount"].sum()` — каждое условие в скобках.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue_big_delivery = df[(df["channel"] == "доставка") & (df["amount"] > 500)]["amount"].sum()
```

### explain
Доставки дороже 500 ₽ принесли 46 885 ₽. В SQL это `WHERE channel = 'доставка' AND amount > 500` — в pandas то же самое, только `AND` пишется как `&`, а условия обязательно в скобках.

## task: fix-and | Почините фильтр | base

Код падает. Исправьте условие, чтобы `n` стало числом заказов размера S в зале.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
n = len(df[df["size"] == "S" and df["channel"] == "зал"])
print(n)
```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = len(d[(d['size'] == 'S') & (d['channel'] == 'зал')])
assert need('n') == want, f'n = {need("n")}, а нужно {want}.'
```

### hint
Сообщение об ошибке про «truth value» — подсказка: с таблицами `and` не работает.

### hint
Замените `and` на `&` и возьмите каждое сравнение в скобки.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
n = len(df[(df["size"] == "S") & (df["channel"] == "зал")])
print(n)
```

### explain
Маленьких стаканов в зале — 298 заказов. Ошибка с `and` — самая частая у тех, кто пришёл из SQL: в SQL слово `AND` работает с таблицами, в Python — только с одиночными `True/False`.

## task: isin | Казань | base

Посчитайте `kazan_revenue` — выручку двух казанских кофеен (`KZN-1` и `KZN-2`) с помощью `isin`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = d[d['shop_id'].isin(['KZN-1', 'KZN-2'])]['amount'].sum()
assert need('kazan_revenue') == want, f'kazan_revenue = {need("kazan_revenue")}.'
assert calls('isin'), 'Используйте isin.'
```

### hint
`isin` принимает список значений — как `IN (...)` в SQL.

### hint
`df[df["shop_id"].isin(["KZN-1", "KZN-2"])]["amount"].sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
kazan_revenue = df[df["shop_id"].isin(["KZN-1", "KZN-2"])]["amount"].sum()
```

### explain
Две казанские кофейни — 279 705 ₽, почти 40 % выручки сети. `isin` удобнее, чем `(... == "KZN-1") | (... == "KZN-2")`: список можно расширить, не переписывая условие.

## task: loc | Строки и столбцы сразу | base

С помощью `loc` получите таблицу `large`: только заказы размера L и только столбцы `order_id`, `drink`, `amount`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
l = need('large', _pd.DataFrame)
assert list(l.columns) == ['order_id', 'drink', 'amount'], f'Столбцы: {list(l.columns)}.'
assert len(l) == (d['size'] == 'L').sum(), f'Строк {len(l)}, а заказов размера L — {(d["size"] == "L").sum()}.'
assert calls('loc') or '.loc[' in _code, 'Используйте loc.'
```

### hint
`loc[строки, столбцы]`: строки — маской, столбцы — списком названий.

### hint
`df.loc[df["size"] == "L", ["order_id", "drink", "amount"]]`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
large = df.loc[df["size"] == "L", ["order_id", "drink", "amount"]]
```

### explain
`loc` делает за один шаг то, что иначе потребовало бы двух: отбора строк и отбора столбцов. Результат — компактная таблица, которую удобно показать или выгрузить.

## task: october | Выручка за октябрь | plus

Дата и время в `datetime` пока записаны текстом вида `2026-10-05 14:20`. Посчитайте `october` — выручку за октябрь, отобрав строки по началу текста. (С настоящими датами будем работать в уроке «Даты и время».)

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = d[d['datetime'].str.startswith('2026-10')]['amount'].sum()
assert need('october') == want, f'october = {need("october")}, а нужно {want}.'
```

### hint
Даты здесь — текст, а у текста есть методы `.str`.

### hint
`df["datetime"].str.startswith("2026-10")` — маска; выручка — `df[маска]["amount"].sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
october = df[df["datetime"].str.startswith("2026-10")]["amount"].sum()
```

### explain
Выручка октября — 233 756 ₽. Отбор по началу текста работает, пока даты записаны в одном формате; в уроке «Даты и время» тот же расчёт сделаем через настоящие даты — надёжнее и короче.

## task: query-at | Параметры отчёта | base

В начале блокнота заданы параметры отчёта: порог `threshold` и список «сладких» напитков `drinks`. Посчитайте через `query` с `@`:

- `n_sweet` — число заказов сладких напитков на сумму **не меньше** порога;
- `rev_sweet` — их выручку.

Числа и названия напитков в строку условия не вписывайте — только ссылки на переменные.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

threshold = 450
drinks = ["Раф", "Мокко", "Какао"]

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv')
_q = _d[_d['drink'].isin(['Раф', 'Мокко', 'Какао']) & (_d['amount'] >= 450)]
assert calls('query'), 'Используйте метод query.'
assert '@threshold' in _code and '@drinks' in _code, 'Сошлитесь на параметры через @: @threshold и @drinks.'
assert '450' not in _code.replace('threshold = 450', '').replace('threshold=450', ''), 'Число 450 встречается не только в параметре. Внутри условия — @threshold.'
assert need('n_sweet') == len(_q), f'n_sweet = {need("n_sweet")}, а нужно {len(_q)}. Проверьте знак: «не меньше» — это >=.'
assert need('rev_sweet') == _q['amount'].sum(), f'rev_sweet = {need("rev_sweet")}. Нужна сумма amount по отобранным заказам.'
```

### hint
Два условия: напиток — один из списка (`in`), сумма — не меньше порога (`>=`). Обе переменные — через `@`.

### hint
Строка условия: `"drink in @drinks and amount >= @threshold"`.

### hint
```python
sweet = df.query("drink in @... and amount >= @...")
n_sweet = len(sweet)
rev_sweet = sweet["amount"]....
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

threshold = 450
drinks = ["Раф", "Мокко", "Какао"]
sweet = df.query("drink in @drinks and amount >= @threshold")
n_sweet = len(sweet)
rev_sweet = sweet["amount"].sum()
```

### explain
Крупных заказов сладких напитков — 141 на 93 895 ₽ (а всего заказов этих трёх напитков — 445). Теперь, чтобы посмотреть порог 600 или добавить в список «Сезонный», меняют одну строку параметров. Если бы вместо `>=` стояло `>`, выпали бы 11 заказов ровно на 450 ₽ — граница «не меньше» включает само значение.

## task: query | Тот же фильтр через query | plus

Посчитайте `n_q` — число заказов дороже 400 рублей **не** в зале, у которых указан гость (`client_id` не пустой). Используйте `query` для первых двух условий и маску `notna()` для третьего.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
want = len(d[(d['amount'] > 400) & (d['channel'] != 'зал') & d['client_id'].notna()])
_no_client = len(d[(d['amount'] > 400) & (d['channel'] != 'зал')])
assert calls('query'), 'Используйте query.'
assert need('n_q') != _no_client, f'n_q = {need("n_q")} — столько заказов вообще без условия на client_id. Похоже, условие «гость указан» не сработало: внутри query сравнение с None не ловит NaN. Отберите непустые маской снаружи: notna().'
assert need('n_q') == want, f'n_q = {need("n_q")}, а нужно {want}.'
```

### hint
Внутри `query` можно писать `and` — это строка, её разбирает pandas, а не Python.

### hint
Пустой `client_id` — это `NaN`, а не `None`: `client_id != None` внутри `query` пропустит все строки. Проверку «не пусто» сделайте обычной маской `notna()` уже после `query`.

### hint
```python
q = df.query("amount > 400 and channel != 'зал'")
n_q = len(q[q["client_id"]....()])
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
q = df.query("amount > 400 and channel != 'зал'")
n_q = len(q[q["client_id"].notna()])
```

### explain
Таких заказов — 171. `query` читается почти как SQL, а для проверок вроде «не пусто» удобнее обычная маска — в одной цепочке можно сочетать оба способа.

## task: share | Доля доставки в Казани | star

Посчитайте `share` — долю выручки от доставок в выручке казанских кофеен (в процентах с одним знаком).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
k = d[d['shop_id'].str.startswith('KZN')]
want = round(k[k['channel'] == 'доставка']['amount'].sum() / k['amount'].sum() * 100, 1)
assert close(need('share'), want), f'share = {need("share")}, а нужно {want}.'
```

### hint
Сначала отберите Казань в отдельную таблицу. Доля — выручка доставки внутри неё, делённая на всю её выручку.

### hint
`kzn = df[df["shop_id"].str.startswith("KZN")]`; числитель — `kzn[kzn["channel"] == "доставка"]["amount"].sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
kzn = df[df["shop_id"].str.startswith("KZN")]
share = round(kzn[kzn["channel"] == "доставка"]["amount"].sum() / kzn["amount"].sum() * 100, 1)
```

### explain
В Казани доставка — 18.6 % выручки, почти как в среднем по сети (около 18 % заказов). Доля «внутри группы» требует двух шагов: сначала сузить таблицу до группы, потом делить её части на её же итог — иначе знаменателем окажется вся сеть.
