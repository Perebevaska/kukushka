---
title: "Сводные таблицы: широкий и длинный формат"
lead: "Строим таблицу для руководителя — кофейни по строкам, месяцы или каналы по столбцам, итоги в углу, как сводная в Excel. Учимся брать из неё нужную ячейку, класть в неё две метрики сразу и переворачивать обратно в длинный список «кофейня — месяц — число», по которому удобно считать дальше."
files: [orders_3m.csv]
recap:
  - "`pd.pivot_table(df, index=…, columns=…, values=…, aggfunc=…)` — сводная таблица, как в Excel: группировка по двум ключам, развёрнутая в строки и столбцы."
  - "По умолчанию `pivot_table` считает **среднее** (`aggfunc=\"mean\"`): для выручки пишите `aggfunc=\"sum\"`, для числа заказов — `\"count\"`. Пустая пара ключей даёт `NaN`, `fill_value=0` ставит ноль."
  - "Длинный формат (строка = наблюдение) → широкий: `pivot_table(index, columns, values, margins=True)` или `unstack()`. Обратно — `reset_index().melt(id_vars=…)` или `stack()`."
  - "`axis=0` — вниз по строкам (итог на столбец), `axis=1` — вдоль строки (итог на строку). Доля внутри строки — `t.div(t.sum(axis=1), axis=0)`; `idxmax()`/`idxmin()` — подпись строки с максимумом/минимумом."
  - "Таблицу с `margins=True` читают глазами, а считают дальше по длинной таблице: строка «Итого» попадёт в любое среднее."
  - "Несколько `values` в `pivot_table` дают `MultiIndex` в столбцах: `t[\"amount\"]`, `t[(\"amount\", \"2026-10\")]`. Для выгрузки уровни склеивают: `[f\"{a}_{b}\" for a, b in t.columns]`."
---

## Сводная таблица: группировка, развёрнутая в квадрат

Зачем: в уроке «Группировки: GROUP BY и HAVING» `df.groupby(["shop_id", "channel"])["amount"].sum()` дал выручку по парам «кофейня, канал» — длинную Series из 18 строк с двухуровневым индексом. Читать её глазами неудобно: чтобы сравнить каналы одной кофейни, надо найти три строки подряд, а чтобы сравнить кофейни по доставке — шесть строк вразброс. Руководитель ждёт квадрат: кофейни по строкам, каналы по столбцам. Это **сводная таблица** — та же группировка по двум ключам, только второй ключ развёрнут в столбцы.

::: tip Аналогия
Это сводная таблица Excel: одно поле перетаскиваете в «Строки», другое — в «Столбцы», третье — в «Значения» и выбираете «Сумма». В pandas те же четыре решения — четыре параметра `pivot_table`.
:::

**Пример руками.** Три заказа:

| кофейня | размер | сумма |
|---|---|---|
| A | S | 100 |
| A | L | 300 |
| B | S | 200 |

Сводная «кофейня × размер», в ячейке — сумма:

| кофейня | L | S |
|---|---|---|
| A | 300 | 100 |
| B | пусто | 200 |

1. **Строки** — разные значения ключа `index`: A и B.
2. **Столбцы** — разные значения ключа `columns`: L и S (по алфавиту).
3. **Ячейка** — все заказы с этой парой ключей, к ним применяется `aggfunc`: у A × L один заказ на 300, у A × S — на 100.
4. У пары B × L нет ни одного заказа — ячейка пустая (`NaN`).

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"shop": ["A", "A", "B"], "size": ["S", "L", "S"], "amount": [100, 300, 200]})
pv = pd.pivot_table(df, index="shop", columns="size", values="amount", aggfunc="sum")
print(pv.shape)
```

- `(3, 2)`
- [x] `(2, 2)`
- `(2, 3)`

Почему: строк столько, сколько разных кофеен (A и B), столбцов — сколько разных размеров (L и S). Число заказов на форму не влияет, а пустая пара B × L остаётся ячейкой с `NaN`.
:::

На реальных данных — число заказов каждого канала в каждой кофейне:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

pd.pivot_table(df, index="shop_id", columns="channel", values="order_id", aggfunc="count")
```

Что здесь происходит:

- `index="shop_id"` — что пойдёт в строки: шесть кофеен;
- `columns="channel"` — что пойдёт в столбцы: каналы «доставка», «зал», «с собой»;
- `values="order_id"` и `aggfunc="count"` — что и как считать в ячейке: число заказов с этой парой.

Как читать: зал — главный канал во всех кофейнях, но в UFA-1 «с собой» почти догнал его (84 заказа против 89), а в PRM-2 доставкой пользуются реже всего — 27 заказов за три месяца. С `margins=True` добавятся итоги по строкам и столбцам, с `fill_value=0` пустые ячейки станут нулями.

**Одна ячейка.** Чтобы взять из сводной одно число, нужен `loc` с двумя подписями: **сначала подпись строки, потом подпись столбца**. Это тот же `loc[строки, столбцы]` из урока «Выбор столбцов и строк», только вместо маски и списка — по одной подписи:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

pv = pd.pivot_table(df, index="shop_id", columns="channel", values="order_id", aggfunc="count")
print(pv.loc["UFA-1", "с собой"])    # строка UFA-1, столбец «с собой»
print(pv.loc["PRM-2", "доставка"])
```

Что здесь происходит:

- `"UFA-1"` — подпись строки (значение из `index`), `"с собой"` — подпись столбца (значение из `columns`). Результат — одно число, 84.
- Порядок важен: `pv.loc["с собой", "UFA-1"]` упадёт с `KeyError` — строки «с собой» в таблице нет.

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"shop": ["A", "A", "B"], "size": ["S", "L", "S"], "amount": [100, 300, 200]})
pv = pd.pivot_table(df, index="shop", columns="size", values="amount", aggfunc="sum")
print(pv.loc["A", "L"])
```

- `100.0`
- [x] `300.0`
- `Ошибка KeyError`

Почему: строка A, столбец L — заказ на 300. Число дробное, потому что в таблице есть пустая ячейка B × L (`NaN`), а с `NaN` pandas хранит числа как дробные.
:::

::: sql
`pivot_table` — это `GROUP BY shop_id, channel`, развёрнутый так, чтобы каналы стали столбцами. В SQL для этого пишут по столбцу на каждый канал: `COUNT(CASE WHEN channel = 'зал' THEN 1 END) AS "зал"`. pandas строит список столбцов сам — из данных.
:::

::: quiz
Аналитик написал `pd.pivot_table(df, index="shop_id", columns="month", values="amount")` и подписал таблицу «Выручка кофеен по месяцам». Что на самом деле в ячейках?

- [x] Средний чек: по умолчанию `aggfunc="mean"`
  > Без `aggfunc` сводная усредняет `amount` в каждой ячейке. Для выручки нужно `aggfunc="sum"` — и в подписи, и в коде.
- [ ] Выручка: `pivot_table` по умолчанию складывает
  > Так ведёт себя сводная Excel, но не pandas: у `pivot_table` значение по умолчанию — среднее.
- [ ] Число заказов
  > Число заказов дал бы `aggfunc="count"` (или `"size"`).
- [ ] Ошибка: без `aggfunc` таблица не строится
  > Строится, просто со средним — поэтому ошибку легко не заметить.
:::

{{practice: p-pivot, pivot}}

## Таблица для руководителя: широкий и длинный формат

Руководителю удобно читать таблицу «кофейни по строкам, месяцы по столбцам, в углу итоги» — так устроены отчёты в Excel. Это **широкий** формат: одно наблюдение (выручка кофейни за месяц) — ячейка на пересечении. А pandas, SQL и графики любят **длинный** формат: одна строка — одно наблюдение, у каждого признака свой столбец (`shop_id`, `month`, `revenue`). В длинном формате удобно фильтровать, группировать и соединять, в широком — смотреть глазами. Аналитик постоянно переводит таблицы туда и обратно.

::: tip Аналогия
Длинный формат — журнал продаж, куда каждую запись пишут новой строкой. Широкий — сводная таблица Excel, построенная по этому журналу. Из журнала сводная строится всегда, а вот считать что-то новое по сводной неудобно — её сначала «разворачивают» обратно в журнал.
:::

**Пример руками.** Длинная таблица из четырёх строк и та же информация в широкой:

| shop_id | month | revenue |
|---|---|---|
| PRM-1 | 09 | 100 |
| PRM-1 | 10 | 120 |
| KZN-1 | 09 | 90 |
| KZN-1 | 10 | 80 |

| shop_id | 09 | 10 |
|---|---|---|
| KZN-1 | 90 | 80 |
| PRM-1 | 100 | 120 |

Из длинной в широкую: значения столбца `month` становятся **заголовками столбцов**, `revenue` — ячейками. Обратно: каждый столбец-месяц превращается в строки «кофейня, месяц, значение» — из 2 строк × 2 месяца получается 4 строки.

::: figure long-wide
Одни и те же четыре числа в двух форматах. Цвет — месяц: в длинной таблице он в столбце `month`, в широкой стал заголовком.
:::

```python
import pandas as pd
long = pd.DataFrame({"shop_id": ["PRM-1", "PRM-1", "KZN-1", "KZN-1"],
                     "month": ["09", "10", "09", "10"],
                     "revenue": [100, 120, 90, 80]})

wide = long.pivot_table(index="shop_id", columns="month", values="revenue", aggfunc="sum")
print(wide)
back = wide.reset_index().melt(id_vars="shop_id", var_name="month", value_name="revenue")
print(back)
```

Что здесь происходит:

- `pivot_table(index=…, columns=…, values=…)` — длинная → широкая: строки по `shop_id`, столбцы по значениям `month`.
- `reset_index()` — возвращает `shop_id` из индекса в обычный столбец: `melt` работает со столбцами.
- `melt(id_vars="shop_id", …)` — широкая → длинная: `id_vars` — столбцы, которые остаются как есть, все остальные «плавятся» в пары `var_name` (бывший заголовок) и `value_name` (значение).

### Разберём вместе: отчёт «кофейни × месяцы» с итогами

Задача: руководитель просит выручку кофеен по месяцам — с итогами по строкам и столбцам (`margins=True`). Ход решения: 1) получить столбец месяца; 2) решить, что в строках (кофейни), что в столбцах (месяцы), что в ячейках (сумма `amount`); 3) добавить итоги и подписать их по-русски.

Месяц возьмём первыми семью символами даты (`2026-09`). Срез строки из главы 1 работает и для целого столбца, если поставить перед ним `.str`: `df["datetime"].str[:7]` режет каждую строку столбца. Настоящие даты — в уроке «Даты и время».

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

report = pd.pivot_table(df, index="shop_id", columns="month", values="amount",
                        aggfunc="sum", margins=True, margins_name="Итого")
report
```

Как читать: справа — выручка кофейни за три месяца, снизу — выручка сети по месяцам, в углу — 710 195 ₽ за всё. Сразу видно, что KZN-1 просела в октябре (55 012 после 57 985) и выросла в ноябре до 68 368.

### Итоги по строкам и по столбцам: axis

`margins=True` считает итоги за вас. Свои итоги по широкой таблице считают теми же `sum()`, `mean()` — с параметром **`axis`** («ось»): он говорит, в какую сторону сворачивать таблицу.

- `axis=0` (по умолчанию) — **вниз по строкам**: один итог на столбец. `base.sum(axis=0)` — выручка сети по месяцам.
- `axis=1` — **вдоль строки**: один итог на строку. `base.sum(axis=1)` — выручка каждой кофейни за три месяца.

Частый вопрос — доля внутри строки: какую часть выручки кофейни дал каждый месяц. Каждую строку надо поделить на итог **своей** строки. Обычное `base / base.sum(axis=1)` так не сделает: pandas выравнивает Series по **столбцам**, ищет столбцы `KZN-1`, `KZN-2`… и выдаёт таблицу из `NaN`. Для деления строк есть метод `div` с `axis=0` — «прикладывать итоги вдоль строк, по индексу»:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

base = pd.pivot_table(df, index="shop_id", columns="month", values="amount", aggfunc="sum")
print(base.sum(axis=0))                       # итог каждого месяца
print(base.sum(axis=1))                       # итог каждой кофейни
share = base.div(base.sum(axis=1), axis=0)    # доля месяца в выручке своей кофейни
print(share.round(3))
print(share["2026-11"].idxmax(), share["2026-11"].idxmin())
```

Как читать: каждая строка `share` в сумме даёт 1. Ноябрь — самый сильный месяц почти у всех: у KZN-1 на него пришлось 37.7 % выручки за квартал, у PRM-2 — 34.2 %, меньше всех. `idxmax()` и `idxmin()` возвращают **подпись** строки с наибольшим и наименьшим значением (а не само значение) — как `index[0]` после сортировки.

::: predict
```python static
import pandas as pd
wide = pd.DataFrame({"shop_id": ["A", "B", "C"], "09": [1, 2, 3], "10": [4, 5, 6]})
print(wide.melt(id_vars="shop_id").shape)
```

- `(3, 3)`
- [x] `(6, 3)`
- `(6, 2)`

Почему: два столбца-месяца у трёх кофеен «плавятся» в 3 × 2 = 6 строк. Столбцов три: `shop_id`, `variable` (бывший заголовок) и `value`.
:::

::: warn Типичные ошибки
- **Считать по широкой таблице как по длинной.** `report.mean()` усреднит и строку «Итого» — итоги, добавленные `margins=True`, попадут в среднее. Для расчётов берите таблицу без `margins` или длинный формат.
- **`melt` без `reset_index()`.** Если ключ сидит в индексе, `melt(id_vars="shop_id")` упадёт с `KeyError`: столбца `shop_id` нет — он в индексе.
- **`pivot` вместо `pivot_table` на повторах.** `df.pivot(...)` не агрегирует и падает с `ValueError: Index contains duplicate entries, cannot reshape`, если у пары (строка, столбец) больше одного значения. `pivot_table` в этом случае просто сложит или усреднит.
:::

::: quiz
Руководитель прислал план выручки в широком виде: кофейни по строкам, месяцы по столбцам. Нужно сложить план сети по месяцам и сравнить его с фактом из `groupby(["shop_id", "month"])`. Что сделать первым?

- [x] Перевести план в длинный формат через `melt`: строка — кофейня за месяц
  > Факт из `groupby` устроен так же — строка на пару «кофейня, месяц». В одинаковом формате план и факт складываются, группируются и соединяются обычными средствами.
- [ ] Сложить столбцы плана как есть и вписать итоги руками
  > Суммы по месяцам получатся, но сравнение с фактом по кофейням придётся делать вручную, и при новом плане всё повторять.
- [ ] Посчитать `plan.mean()` — среднее по месяцам
  > Среднее не отвечает на вопрос про сумму плана сети, а со строкой итогов ещё и исказится.
- [ ] Сначала превратить факт в широкую таблицу с `margins=True`
  > Таблицу с итогами удобно читать, но не считать: строка «Итого» встанет в один ряд с кофейнями.
:::

{{practice: wide, melt, ch-share}}

## MultiIndex: две метрики в одной таблице

Руководитель просит в той же таблице и число заказов. Если передать в `values` два столбца, у результата будет **двухуровневый заголовок** — `MultiIndex`: сверху метрика, под ней месяц.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

t = pd.pivot_table(df, index="shop_id", columns="month",
                   values=["amount", "order_id"],
                   aggfunc={"amount": "sum", "order_id": "count"})
print(t.columns.tolist()[:2])
avg_check = (t["amount"] / t["order_id"]).round(1)   # средний чек: кофейня × месяц
avg_check
```

Что здесь происходит:

- `aggfunc={"amount": "sum", "order_id": "count"}` — свой агрегат для каждого столбца.
- Заголовки столбцов теперь — пары: `('amount', '2026-09')`. Это и есть `MultiIndex`.
- `t["amount"]` — верхний уровень: обычная широкая таблица «кофейня × месяц» с выручкой. Одна ячейка — `t[("amount", "2026-10")]` или `t.loc["KZN-1", ("order_id", "2026-11")]`.
- `t["amount"] / t["order_id"]` — две широкие таблицы одинаковой формы делятся ячейка на ячейку: средний чек по каждой кофейне и месяцу.

::: figure multiindex
Двухуровневый заголовок на данных урока (две кофейни из шести): `t["amount"]` берёт весь левый блок, пара `("amount", "2026-10")` — один столбец.
:::

Тот же `MultiIndex` получается и у `groupby` по двум ключам — только в строках. Метод `unstack()` переносит внутренний уровень индекса в столбцы (длинная → широкая), `stack()` — обратно:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

g = df.groupby(["shop_id", "month"])["amount"].sum()   # Series: 18 строк, индекс из двух уровней
wide = g.unstack()                                       # 6 кофеен × 3 месяца
print(g.shape, wide.shape, wide.stack().shape)
```

Для выгрузки в Excel или CSV двухуровневые заголовки обычно склеивают в один: `t.columns = [f"{a}_{b}" for a, b in t.columns]` даст `amount_2026-09`, `order_id_2026-09` и так далее.

::: sql
Широкая таблица в SQL — это `SUM(CASE WHEN month = '2026-09' THEN amount END) AS "2026-09"` для каждого месяца руками. В pandas — один `pivot_table`, а список столбцов он построит сам из данных.
:::

::: warn Типичные ошибки
- **Обращение к столбцу MultiIndex одной строкой.** `t["2026-09"]` — `KeyError`: сверху метрика, а не месяц. Нужно `t["amount"]["2026-09"]` или `t[("amount", "2026-09")]`.
- **`unstack` на неполных парах.** Если у кофейни не было заказов в каком-то месяце, в длинной Series этой пары просто нет, а в широкой таблице на её месте появится `NaN`. Для сумм это ноль: `unstack(fill_value=0)`.
- **Склеенные заголовки потеряли уровни.** После `t.columns = [f"{a}_{b}" …]` обращение `t["amount"]` уже не работает — склеивайте только перед выгрузкой.
:::

{{practice: g-unstack, multi, flat-cols}}

## Практика

## task: p-pivot | Соберите сводную по каналам | warmup

Соберите программу: сводная таблица выручки «кофейня × канал» и вывод одной ячейки — выручки UFA-1 в канале «с собой».

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
pv = pd.pivot_table(df, index="shop_id", columns="channel", values="amount", aggfunc="sum")
cell = pv.loc["UFA-1", "с собой"]
print(cell)
```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv')
_want = int(_d[(_d['shop_id'] == 'UFA-1') & (_d['channel'] == 'с собой')]['amount'].sum())
assert _lines == [str(_want)], f'Должно вывестись {_want}. Сейчас: {_lines}'
```

### hint
Порядок такой же, как всегда: загрузить данные → построить таблицу → взять из неё ячейку → вывести.

### hint
Ячейка сводной — `pv.loc[строка, столбец]`: строка — кофейня, столбец — канал.

## task: pivot | Сводная: размеры по кофейням | base

Постройте сводную таблицу `pv`: строки — кофейни, столбцы — размеры (`size`, порядок столбцов не важен), значения — число заказов. Сохраните в `ufa_l` число заказов размера L в `UFA-1`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
p = need('pv', _pd.DataFrame)
assert p.shape == (6, 3), f'Размер сводной {p.shape}, а нужно 6 строк × 3 столбца.'
assert need('ufa_l') == ((d['shop_id'] == 'UFA-1') & (d['size'] == 'L')).sum(), f'ufa_l = {need("ufa_l")}.'
```

### hint
Сводная таблица — это группировка по двум ключам, развёрнутая в строки и столбцы: что в строках (`index`), что в столбцах (`columns`), что и как считать (`values`, `aggfunc`).

### hint
`pd.pivot_table(df, index="shop_id", columns="size", values="order_id", aggfunc="count")`. Ячейка — `pv.loc[строка, столбец]`: сначала кофейня, потом размер.

### hint
```python
pv = pd.pivot_table(df, index=..., columns=..., values="order_id", aggfunc="count")
ufa_l = pv.loc[..., ...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
pv = pd.pivot_table(df, index="shop_id", columns="size", values="order_id", aggfunc="count")
ufa_l = pv.loc["UFA-1", "L"]
```

### explain
В UFA-1 размер L заказывали 46 раз. Сводная таблица — та же группировка по двум ключам, но в виде, который удобно читать глазами: кофейни строками, размеры столбцами.

## task: g-unstack | Из groupby — в широкую таблицу | warmup

Посчитайте выручку по парам «кофейня, канал» через `groupby` и разверните результат методом `unstack()` в широкую таблицу `wide`: кофейни по строкам, каналы по столбцам. В `wide_shape` сохраните её форму.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv')
_want = _d.groupby(['shop_id', 'channel'])['amount'].sum().unstack()
w = need('wide', _pd.DataFrame)
assert w.shape == _want.shape, f'Форма wide — {w.shape}, а нужна {_want.shape}: кофейни по строкам, каналы по столбцам. Группируйте по списку ["shop_id", "channel"].'
assert list(w.columns) == list(_want.columns), f'Столбцы wide: {list(w.columns)}. В столбцы должен уйти внутренний уровень индекса — канал.'
assert int(w.loc['KZN-1', 'доставка']) == int(_want.loc['KZN-1', 'доставка']), 'В ячейках должна быть сумма amount.'
assert tuple(need('wide_shape')) == _want.shape, f'wide_shape = {need("wide_shape")}, а нужно {_want.shape}.'
assert calls('unstack'), 'Разверните Series методом unstack().'
```

### hint
Сначала длинная Series: группировка по двум ключам — списком. Потом `unstack()` переносит внутренний уровень индекса (канал) в столбцы.

### hint
`df.groupby(["shop_id", "channel"])["amount"].sum().unstack()`; форма — атрибут `.shape`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
wide = df.groupby(["shop_id", "channel"])["amount"].sum().unstack()
wide_shape = wide.shape
```

## task: wide | Отчёт: кофейни × месяцы | base

Соберите для руководителя таблицу `report`: кофейни по строкам, месяцы (`2026-09`, `2026-10`, `2026-11`) по столбцам, в ячейках — выручка, с итогами по строкам и столбцам под названием `"Итого"`. Сохраните в `oct_total` выручку сети за октябрь, взяв её **из таблицы**.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

```

### check
```python
import pandas as _pd
r = need('report', _pd.DataFrame)
assert r.shape == (7, 4), f'Форма report — {r.shape}, а нужна (7, 4): 6 кофеен + строка итогов, 3 месяца + столбец итогов. Не забыли margins=True?'
assert 'Итого' in r.index and 'Итого' in r.columns, 'Итоги должны называться «Итого»: параметр margins_name.'
_d = _pd.read_csv('orders_3m.csv')
_want = int(_d.loc[_d['datetime'].str.startswith('2026-10'), 'amount'].sum())
assert int(r.loc['KZN-1', '2026-10']) == 55012, f'В ячейке KZN-1 × 2026-10 — {r.loc["KZN-1", "2026-10"]}. В ячейках нужна сумма amount.'
assert need('oct_total') == _want, f'oct_total = {need("oct_total")}, а нужно {_want}. Это ячейка на пересечении строки «Итого» и столбца октября.'
assert not has_literal(_want), 'Возьмите итог из таблицы через loc, а не вписывайте число.'
```

### hint
Сводная таблица — `pd.pivot_table`: `index` — кофейни, `columns` — месяц, `values` и `aggfunc` — что и как считать. Итоги добавляет `margins=True`.

### hint
Название строки и столбца итогов задаёт `margins_name="Итого"`. Ячейка — `report.loc["Итого", "2026-10"]`.

### hint
```python
report = pd.pivot_table(df, index=..., columns=..., values="amount",
                        aggfunc="sum", margins=True, margins_name=...)
oct_total = report.loc[..., ...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]
report = pd.pivot_table(df, index="shop_id", columns="month", values="amount",
                        aggfunc="sum", margins=True, margins_name="Итого")
oct_total = report.loc["Итого", "2026-10"]
```

### explain
Выручка сети в октябре — 233 756 ₽, на 13 515 ₽ больше сентября. Это таблица «для глаз»: руководитель читает её как сводную в Excel. Но считать по ней дальше осторожно — строка «Итого» стоит наравне с кофейнями, и `report.mean()` усреднит её вместе с ними. Если бы вы забыли `aggfunc="sum"`, pandas посчитал бы в ячейках **среднее** — по умолчанию у `pivot_table` `aggfunc="mean"`, и вместо выручки получился бы средний чек.

## task: melt | План в длинный формат | base

Руководитель прислал план выручки в широком виде: кофейни по строкам, месяцы по столбцам. Переведите его в длинный формат `plan_long` со столбцами `shop_id`, `month`, `plan` (одна строка — кофейня за месяц). Затем по длинной таблице посчитайте `plan_by_month` — **словарь** «месяц → план сети».

### starter
```python
import pandas as pd
plan = pd.DataFrame({
    "shop_id": ["KZN-1", "KZN-2", "PRM-1", "PRM-2", "TMN-1", "UFA-1"],
    "2026-09": [60000, 30000, 60000, 25000, 30000, 20000],
    "2026-10": [62000, 32000, 62000, 26000, 31000, 24000],
    "2026-11": [65000, 34000, 65000, 27000, 33000, 26000],
})

```

### check
```python
import pandas as _pd
pl = need('plan_long', _pd.DataFrame)
assert list(pl.columns) == ['shop_id', 'month', 'plan'], f'Столбцы plan_long: {list(pl.columns)}. Нужны shop_id, month, plan — их задают var_name и value_name.'
assert len(pl) == 18, f'В plan_long {len(pl)} строк, а нужно 18: 6 кофеен × 3 месяца.'
_b = {str(k): int(v) for k, v in dict(need('plan_by_month')).items()}
assert _b == {'2026-09': 225000, '2026-10': 237000, '2026-11': 250000}, f'plan_by_month = {_b}. Сгруппируйте plan_long по month и сложите plan.'
assert calls('melt'), 'Переведите таблицу в длинный формат методом melt.'
```

### hint
`melt` превращает столбцы-месяцы в строки. Столбец, который должен остаться как есть, передают в `id_vars`.

### hint
`plan.melt(id_vars="shop_id", var_name="month", value_name="plan")`. Дальше — обычный `groupby("month")["plan"].sum()` и `dict(...)`.

### hint
```python
plan_long = plan.melt(id_vars=..., var_name=..., value_name=...)
plan_by_month = dict(plan_long.groupby(...)["plan"].sum())
```

### solution
```python
import pandas as pd
plan = pd.DataFrame({
    "shop_id": ["KZN-1", "KZN-2", "PRM-1", "PRM-2", "TMN-1", "UFA-1"],
    "2026-09": [60000, 30000, 60000, 25000, 30000, 20000],
    "2026-10": [62000, 32000, 62000, 26000, 31000, 24000],
    "2026-11": [65000, 34000, 65000, 27000, 33000, 26000],
})
plan_long = plan.melt(id_vars="shop_id", var_name="month", value_name="plan")
plan_by_month = dict(plan_long.groupby("month")["plan"].sum())
```

### explain
План сети: 225 000 ₽ в сентябре, 237 000 — в октябре, 250 000 — в ноябре. В длинном формате план устроен так же, как факт `groupby(["shop_id", "month"])`, и в следующем уроке их можно соединить по двум ключам и сравнить построчно: план выполнен в 10 кофейне-месяцах из 18. Без `var_name` и `value_name` столбцы назывались бы `variable` и `value` — работать можно, но читать отчёт труднее.

## task: flat-cols | Заголовки для выгрузки | base

Бухгалтерия просит таблицу «кофейня × месяц» с выручкой и числом заказов в CSV, где у каждого столбца одно простое имя. Постройте сводную `t` с двумя метриками (`values=["amount", "order_id"]`, сумма и число), склейте двухуровневые заголовки в один через `_` (`amount_2026-09`, …) и сохраните в `cols` **список** имён столбцов, а в `prm2_oct_orders` — число заказов PRM-2 в октябре, взятое из таблицы по новому имени столбца.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

```

### check
```python
import pandas as _pd
t_ = need('t', _pd.DataFrame)
assert not isinstance(t_.columns, _pd.MultiIndex), 'У t по-прежнему двухуровневые заголовки. Присвойте t.columns список склеенных имён.'
_want = ['amount_2026-09', 'amount_2026-10', 'amount_2026-11', 'order_id_2026-09', 'order_id_2026-10', 'order_id_2026-11']
assert list(need('cols')) == _want, f'cols = {list(need("cols"))}. Нужны имена вида «метрика_месяц» в порядке столбцов сводной.'
_d = _pd.read_csv('orders_3m.csv')
_n = int(((_d['shop_id'] == 'PRM-2') & _d['datetime'].str.startswith('2026-10')).sum())
assert int(t_.loc['PRM-2', 'amount_2026-10']) == int(_d[(_d['shop_id'] == 'PRM-2') & _d['datetime'].str.startswith('2026-10')]['amount'].sum()), 'В столбцах amount_… нужна сумма выручки.'
assert need('prm2_oct_orders') == _n, f'prm2_oct_orders = {need("prm2_oct_orders")}, а нужно {_n}. Столбец order_id_2026-10, строка PRM-2.'
assert not has_literal(_n), 'Возьмите число из таблицы через loc, а не вписывайте его.'
```

### hint
Сначала — сводная с двумя метриками, как в разделе про `MultiIndex`. Заголовки у неё — пары `(метрика, месяц)`.

### hint
Пройдите по парам и склейте их f-строкой: `[f"{a}_{b}" for a, b in t.columns]` — и присвойте результат `t.columns`.

### hint
```python
t = pd.pivot_table(df, index="shop_id", columns="month",
                   values=["amount", "order_id"], aggfunc={"amount": "sum", "order_id": ...})
t.columns = [f"{a}_{b}" for a, b in ...]
cols = list(t.columns)
prm2_oct_orders = t.loc["PRM-2", ...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]
t = pd.pivot_table(df, index="shop_id", columns="month",
                   values=["amount", "order_id"],
                   aggfunc={"amount": "sum", "order_id": "count"})
t.columns = [f"{a}_{b}" for a, b in t.columns]
cols = list(t.columns)
prm2_oct_orders = t.loc["PRM-2", "order_id_2026-10"]
```

### explain
В октябре PRM-2 приняла 76 заказов. Склеенные имена удобны для CSV и Excel: каждый столбец читается сам по себе, и файл открывается без «двухэтажной» шапки. Цена — уровни пропали: `t["amount"]` теперь падает с `KeyError`, потому что столбца с таким именем нет. Поэтому склеивают в самом конце, прямо перед `to_csv`. Если бы вы склеили в обратном порядке (`f"{b}_{a}"`), получилось бы `2026-09_amount` — тоже работает, но столбцы одной метрики при сортировке по имени разъедутся.

## task: multi | Средний чек: кофейня × месяц | plus

Соберите сводную `t`: кофейни по строкам, месяцы по столбцам, а в ячейках сразу две метрики — выручка (сумма `amount`) и число заказов (`count` по `order_id`). У таблицы получится двухуровневый заголовок. Из неё посчитайте `avg_check` — широкую таблицу среднего чека (выручка / заказы), округлённую до одного знака, и `kzn_nov` — средний чек KZN-1 в ноябре 2026.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]

```

### check
```python
import pandas as _pd
t_ = need('t', _pd.DataFrame)
assert isinstance(t_.columns, _pd.MultiIndex), 'У t одноуровневые столбцы. Передайте в values список из двух столбцов — тогда заголовок станет двухуровневым.'
assert ('amount', '2026-09') in t_.columns and ('order_id', '2026-09') in t_.columns, f'Столбцы t: {t_.columns.tolist()[:4]}…. Сверху должны быть amount и order_id.'
assert int(t_.loc['KZN-1', ('order_id', '2026-11')]) == 188, 'Число заказов KZN-1 в ноябре не сходится: для order_id нужен агрегат count.'
a = need('avg_check', _pd.DataFrame)
assert a.shape == (6, 3), f'Форма avg_check — {a.shape}, а нужна (6, 3): кофейни × месяцы.'
_d = _pd.read_csv('orders_3m.csv')
_n = _d[_d['datetime'].str.startswith('2026-11') & (_d['shop_id'] == 'KZN-1')]
_want = round(_n['amount'].sum() / len(_n), 1)
assert close(need('kzn_nov'), _want, 0.05), f'kzn_nov = {need("kzn_nov")}, а нужно {_want}.'
assert close(float(a.loc['UFA-1', '2026-09']), 291.4, 0.05), f'avg_check для UFA-1 в сентябре — {a.loc["UFA-1", "2026-09"]}. Делите выручку на число заказов той же ячейки.'
```

### hint
Две метрики со своими агрегатами — `values=["amount", "order_id"]` и `aggfunc={"amount": "sum", "order_id": "count"}`.

### hint
`t["amount"]` и `t["order_id"]` — две широкие таблицы одной формы. Их частное — средний чек в каждой ячейке. Одна ячейка — `avg_check.loc["KZN-1", "2026-11"]`.

### hint
```python
t = pd.pivot_table(df, index="shop_id", columns="month",
                   values=[..., ...], aggfunc={"amount": ..., "order_id": ...})
avg_check = (t[...] / t[...]).round(1)
kzn_nov = avg_check.loc[..., ...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["month"] = df["datetime"].str[:7]
t = pd.pivot_table(df, index="shop_id", columns="month",
                   values=["amount", "order_id"],
                   aggfunc={"amount": "sum", "order_id": "count"})
avg_check = (t["amount"] / t["order_id"]).round(1)
kzn_nov = avg_check.loc["KZN-1", "2026-11"]
```

### explain
Средний чек KZN-1 в ноябре — 363.7 ₽, а в октябре был 303.9: октябрьский провал выручки кофейни — это провал чека, а не числа заказов (их стало даже больше — 181 против 168 в сентябре). Деление `t["amount"] / t["order_id"]` работает ячейка к ячейке, потому что у обеих таблиц одинаковые строки и столбцы — pandas совмещает их по подписям. Если бы вы усреднили `amount` через `aggfunc="mean"`, получили бы то же число, но тогда в таблице не было бы числа заказов, которое руководитель тоже просил.

## task: ch-share | Доля каналов внутри кофейни | star

Руководитель спрашивает: в какой кофейне доставка приносит **наименьшую долю** её собственной выручки? Постройте сводную `pv` (кофейни × каналы, сумма `amount`), затем `share` — ту же таблицу, где каждая строка поделена на выручку своей кофейни (доли, сумма по строке — 1). Сохраните в `low_delivery` код кофейни с наименьшей долей доставки, а в `low_share` — эту долю, округлённую до трёх знаков.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv')
_pv = _pd.pivot_table(_d, index='shop_id', columns='channel', values='amount', aggfunc='sum')
_sh = _pv.div(_pv.sum(axis=1), axis=0)
s = need('share', _pd.DataFrame)
assert s.shape == _sh.shape, f'Форма share — {s.shape}, а нужна {_sh.shape}: те же кофейни и каналы, что в pv.'
_rows = s.sum(axis=1)
assert (_rows - 1).abs().max() < 1e-6, f'Сумма долей по строке должна быть 1, а у share она {round(float(_rows.iloc[0]), 3)} и т. д. Делите каждую строку на сумму своей строки (axis=1), а не на сумму столбца.'
_low = _sh['доставка'].idxmin()
assert need('low_delivery') == _low, f'low_delivery = {need("low_delivery")}, а нужна другая кофейня. Минимум ищите в столбце «доставка» таблицы долей, а не выручки.'
assert close(need('low_share'), round(float(_sh.loc[_low, 'доставка']), 3), 0.0005), f'low_share = {need("low_share")}.'
```

### hint
Доля внутри строки — это значение, делённое на итог своей строки. Итоги строк — `pv.sum(axis=1)`: одна сумма на кофейню.

### hint
Обычное `pv / pv.sum(axis=1)` выравнивает по **столбцам** и даст `NaN`. Делить строки нужно методом `div` с `axis=0`: `pv.div(pv.sum(axis=1), axis=0)`.

### hint
```python
pv = pd.pivot_table(df, index=..., columns=..., values="amount", aggfunc="sum")
share = pv.div(pv.sum(axis=1), axis=0)
low_delivery = share["доставка"].idxmin()
low_share = round(share.loc[low_delivery, ...], 3)
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
pv = pd.pivot_table(df, index="shop_id", columns="channel", values="amount", aggfunc="sum")
share = pv.div(pv.sum(axis=1), axis=0)
low_delivery = share["доставка"].idxmin()
low_share = round(share.loc[low_delivery, "доставка"], 3)
```

### explain
В PRM-2 доставка даёт 10.9 % выручки кофейни, у остальных — 18–20 %. По абсолютной выручке это не так заметно: PRM-2 вообще меньше остальных, и её доставка (8 247 ₽) теряется на фоне больших кофеен. Доля внутри строки убирает размер кофейни и показывает структуру — поэтому для вопроса «как устроены продажи» берут доли, а для вопроса «где больше денег» — суммы. Типичная ошибка — `pv / pv.sum()`: так каждая ячейка делится на итог **столбца**, и получится доля кофейни в канале, другой вопрос.
