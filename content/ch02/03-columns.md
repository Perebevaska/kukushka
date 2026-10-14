---
title: "Сортировка и новые столбцы: ORDER BY, CASE"
lead: "Сортируем, берём топы, добавляем вычисляемые столбцы и категории. Плюс одно важное правило pandas 3 о том, как менять значения в таблице."
files: [orders_3m.csv]
recap:
  - "`df.sort_values(\"amount\", ascending=False)` — ORDER BY … DESC; по нескольким столбцам — списки: `by=[\"a\", \"b\"], ascending=[True, False]`."
  - "`head(n)` после сортировки — LIMIT n; `df.nlargest(n, \"amount\")` — то же короче."
  - "Новый столбец — присваивание: `df[\"price\"] = df[\"amount\"] / df[\"qty\"]`. Операции идут по всем строкам сразу."
  - "CASE: `.map({\"S\": \"маленький\", …})` для замены по словарю, `pd.cut(...)` для диапазонов."
  - "Менять часть строк — только через `df.loc[маска, \"столбец\"] = значение`. Цепочка `df[маска][\"столбец\"] = …` в pandas 3 ничего не меняет."
  - "`rename(columns={...})` — переименовать, `drop(columns=[...])` — убрать столбцы."
---

## ORDER BY: сортировка

`sort_values` сортирует таблицу по столбцу. По умолчанию — по возрастанию, `ascending=False` — по убыванию:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df.sort_values("amount", ascending=False).head()
```

Сортировка по нескольким столбцам — списками: сначала по первому, внутри одинаковых — по второму. Направление можно задать для каждого:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df.sort_values(["shop_id", "amount"], ascending=[True, False]).head(8)
```

::: figure sort-multi
Шесть заказов до и после сортировки по двум столбцам: сначала по кофейне, внутри кофейни — по сумме от большей к меньшей.
:::

Для «топ-N» есть короткая запись `nlargest` (и `nsmallest`):

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df.nlargest(3, "amount")[["order_id", "drink", "qty", "amount"]]
```

::: sql
`df.sort_values("amount", ascending=False).head(5)` — это `ORDER BY amount DESC LIMIT 5`.
:::

`sort_values` возвращает **новую** таблицу и не меняет исходную — как `sorted` для списков из главы 1.

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"x": [2, 9, 4]})
print(df.sort_values("x", ascending=False)["x"].tolist())
```

- `[2, 4, 9]`
- [x] `[9, 4, 2]`
- `[2, 9, 4]`

Почему: `ascending=False` — по убыванию. `tolist()` превращает столбец в обычный список Python.
:::

{{practice: top5, nlargest, p-sort}}

## Вычисляемый столбец

Новый столбец создаётся присваиванием по новому имени. Арифметика со столбцами выполняется **для всех строк сразу** — циклы не нужны:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df["price"] = df["amount"] / df["qty"]           # цена одной чашки
df["amount_k"] = (df["amount"] / 1000).round(2)  # сумма в тысячах
df["is_big"] = df["amount"] > 600                # флаг: True / False
df[["drink", "qty", "amount", "price", "amount_k", "is_big"]].head()
```

::: sql
`SELECT amount / qty AS price FROM orders` — то же самое, только в pandas столбец добавляется к таблице и остаётся в ней.
:::

Текстовые столбцы склеиваются так же, через `+`; методы строк — через `.str`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["label"] = df["drink"] + " " + df["size"]
df["drink_upper"] = df["drink"].str.upper()
df[["label", "drink_upper"]].head(3)
```

{{practice: price, hour}}

## CASE: категории

### Замена по словарю — map

Когда каждому значению нужно сопоставить другое, используйте `map` со словарём:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

size_name = {"S": "маленький", "M": "средний", "L": "большой"}
df["size_name"] = df["size"].map(size_name)
df[["size", "size_name"]].head()
```

Значений, которых нет в словаре, `map` превратит в `NaN` — это частая причина «пропавших» данных.

::: predict
```python static
import pandas as pd
print(pd.Series(["S", "L"]).map({"S": 1, "M": 2}).tolist())
```

- `[1, 'L']`
- `[1, None]`
- [x] `[1.0, nan]`

Почему: для «L» в словаре нет пары, получается `NaN`. А раз в столбце есть `NaN`, pandas хранит числа как дробные — `1.0`.
:::

### Диапазоны — pd.cut

Чтобы разложить числа по диапазонам («до 300», «300–600», «больше 600»), есть `pd.cut`. Ему передают границы и названия:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df["segment"] = pd.cut(df["amount"], bins=[0, 300, 600, 10_000],
                       labels=["до 300", "300–600", "больше 600"])
df["segment"].value_counts()
```

Интервалы по умолчанию включают правую границу: 300 попадёт в «до 300».

Результат `value_counts()` — Series «сегмент → число заказов». Если нужен обычный словарь Python (например, чтобы вставить числа в текст отчёта), Series легко превратить в него: `dict(df["segment"].value_counts())` — ключи берутся из индекса, значения — из самой Series.

::: figure cut-bins
Интервалы `pd.cut` с границами 0, 300, 600, 10 000: у каждого левая граница не входит, правая входит.
:::

::: sql
`map` и `pd.cut` — это `CASE WHEN … THEN … END`: первый для точных значений, второй для диапазонов.
:::

{{practice: map, cut}}

## Менять значения — только через loc

Допустим, для доставки нужно уменьшить сумму на 10 % в новом столбце. Логично было бы написать так:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df["amount_net"] = df["amount"] * 1.0      # дробный столбец: значения со скидкой будут дробными
df[df["channel"] == "доставка"]["amount_net"] = df["amount"] * 0.9   # не сработает!
print(df.loc[df["channel"] == "доставка", ["amount", "amount_net"]].head(3))
```

Значения не изменились, а pandas вывел предупреждение `ChainedAssignmentError`. Дело в том, что `df[маска]` создаёт **новую** таблицу-выборку, и присваивание уходит в неё, а не в `df`. В pandas 3 это правило строгое: изменить исходную таблицу можно только одним шагом через `loc`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df["amount_net"] = df["amount"] * 1.0
is_delivery = df["channel"] == "доставка"
df.loc[is_delivery, "amount_net"] = df.loc[is_delivery, "amount"] * 0.9
print(df.loc[is_delivery, ["amount", "amount_net"]].head(3))
```

::: figure loc-assign
Сверху: `df[маска]` создаёт отдельную таблицу, присваивание меняет её, и она пропадает. Снизу: `loc` меняет ячейку прямо в `df`.
:::

::: tip Аналогия
Попросили исправить сумму в договоре, а исправили ксерокопию и выбросили её — оригинал в папке прежний. `df[маска]` — такая ксерокопия, а `loc[маска, "столбец"]` — правка прямо в оригинале. Правда, pandas хотя бы предупреждает (`ChainedAssignmentError`), а ксерокопия молчит.
:::

::: warn Цепочка df[…][…] = …
Запомните шаблон: **`df.loc[маска, "столбец"] = значение`**. Любое изменение части таблицы — так. В старых учебниках и ответах на форумах встречается цепочка `df[...][...] = ...`; в pandas 3 она ничего не меняет.
:::

::: warn Дробные в целый столбец
Ещё одно правило pandas 3: в целочисленный столбец нельзя записать дробные значения. Например, `df["amount_net"] = df["amount"]` — это копия целого столбца (`int64`), а `amount * 0.9` у доставок даёт дробные 235.8, 324.0… Запись через `loc` упадёт с длинной ошибкой:

```text
TypeError: Invalid value '[ 235.8  324.   405.   214.2 …]' for dtype 'int64'
```

В скобках — сотни чисел, которые не влезли в целый столбец; читать их не нужно. Важен хвост `for dtype 'int64'`: «в целый столбец пишете дробные числа». Курс под такой ошибкой подскажет то же самое. Исправить можно двумя способами: округлить записываемые значения (`(…).round()`) или сразу завести столбец дробным (`df["amount"] * 1.0` или `.astype(float)`).
:::

::: sql
`df.loc[mask, "col"] = value` — это `UPDATE orders SET col = value WHERE …`.
:::

### Разберём вместе: скидка на трёх заказах

Три заказа: 380 ₽ в зале, 240 ₽ с собой, 500 ₽ доставкой. Нужна сумма со скидкой 10 % только для доставки.

1. **Копия столбца**: `df["amount_net"] = df["amount"]` → 380, 240, 500.
2. **Маска**: `is_delivery = df["channel"] == "доставка"` → False, False, True.
3. **Правая часть**: `df.loc[is_delivery, "amount"] * 0.9` — считается только для третьей строки: 500 × 0.9 = 450.
4. **Присваивание**: `df.loc[is_delivery, "amount_net"] = ...` — меняется только ячейка третьей строки.
5. Итог: **380, 240, 450**.

```python
import pandas as pd
df = pd.DataFrame({"amount": [380, 240, 500], "channel": ["зал", "с собой", "доставка"]})
df["amount_net"] = df["amount"]
is_delivery = df["channel"] == "доставка"
df.loc[is_delivery, "amount_net"] = (df.loc[is_delivery, "amount"] * 0.9).round()
print(df)
```

Почему не `df[is_delivery]["amount_net"] = ...`? Такая запись сначала создаёт **отдельную** маленькую таблицу, меняет её и выбрасывает — исходная `df` остаётся прежней (в новых версиях pandas — с предупреждением или без изменений вовсе). `loc[строки, столбец]` меняет именно нужные ячейки исходной таблицы.

::: warn Типичные ошибки
- **Цепочка `df[маска]["столбец"] = ...`.** Меняет копию, а не таблицу — используйте `loc`.
- **`sort_values` без сохранения.** Метод возвращает новую таблицу; `df.sort_values(...)` без присваивания ничего не меняет.
- **`map` с неполным словарём.** Значения, которых нет в словаре, станут `NaN`.
- **`pd.cut` и границы.** По умолчанию правая граница включается: 300 — «до 300», 300.01 — уже «300–600».
- **`Invalid value '[…]' for dtype 'int64'`.** В целый столбец через `loc` пишутся дробные числа. Округлите их (`.round()`) или сделайте столбец дробным (`* 1.0`).
:::

::: quiz
Нужно дать скидку 10 % заказам с доставкой. Какая запись **надёжно** изменит столбец `amount_net` в самой таблице `df`?

- [x] `df.loc[df["channel"] == "доставка", "amount_net"] = df["amount"] * 0.9`
  > `loc` с маской и названием столбца меняет нужные клетки прямо в `df` — одним шагом.
- [ ] `df[df["channel"] == "доставка"]["amount_net"] = df["amount"] * 0.9`
  > Это цепочка из двух шагов: первый создаёт выборку-копию, и присваивание уходит в неё. pandas 3 выведет предупреждение, а `df` не изменится.
- [ ] `df["amount_net"] = df["amount"] * 0.9`
  > Так скидка достанется всем заказам, а не только доставке.
- [ ] `df.query('channel == "доставка"')["amount_net"] *= 0.9`
  > `query` тоже возвращает новую таблицу — изменения в `df` не попадут.
:::

{{practice: loc-update}}

## Переименовать и убрать столбцы

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

short = df.drop(columns=["client_id", "channel"]).rename(columns={"amount": "sum_rub", "qty": "cups"})
list(short.columns)
```

Обе операции возвращают новую таблицу — исходная не меняется. Их удобно ставить цепочкой, как методы строк.

{{practice: rename}}

## Практика

## task: top5 | Пять самых крупных | warmup

Сохраните в `top5` пять самых дорогих заказов (таблицу), отсортированных по убыванию суммы.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
t = need('top5', _pd.DataFrame)
want = _pd.read_csv('orders_3m.csv')['amount'].nlargest(5).tolist()
assert len(t) == 5 and t['amount'].tolist() == want, f'Суммы в top5: {t["amount"].tolist()}, а нужно {want}.'
```

### hint
Сортировка по убыванию — `ascending=False`; первые пять строк — `head(5)`.

### hint
`df.sort_values("amount", ascending=False).head(5)` или `df.nlargest(5, "amount")`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
top5 = df.sort_values("amount", ascending=False).head(5)
```

## task: price | Цена чашки | warmup

Добавьте в `df` столбец `price` — цену одной чашки (сумма делить на количество).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
assert 'price' in df.columns, 'Нет столбца price.'
assert (df['price'] * df['qty'] - df['amount']).abs().max() < 1e-9, 'price должен быть amount / qty.'
```

### hint
Новый столбец создаётся присваиванием: слева — `df["price"]`, справа — выражение из других столбцов.

### hint
`df["price"] = df["amount"] / df["qty"]`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["price"] = df["amount"] / df["qty"]
```

## task: p-sort | Соберите топ напитков по цене | warmup

Соберите программу: столбец цены, сортировка по ней по убыванию и вывод названия самой дорогой позиции.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["price"] = df["amount"] / df["qty"]
top = df.sort_values("price", ascending=False)
print(top["drink"].iloc[0])
```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
d['price'] = d['amount'] / d['qty']
want = d.sort_values('price', ascending=False)['drink'].iloc[0]
assert _lines == [want], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Столбец `price` должен появиться до сортировки по нему.

### hint
После сортировки самая дорогая позиция — первая строка. Возьмите столбец названий и его первый элемент: `top["drink"].iloc[0]` (`iloc[0]` — первый по порядку, как в разделе «Уникальные значения и частоты» урока «DataFrame — таблица в Python»).

## task: nlargest | Номера крупнейших заказов | base

Сохраните в `ids` **список** номеров (`order_id`) трёх самых дорогих заказов — от большего к меньшему.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv').nlargest(3, 'amount')['order_id'].tolist()
assert need('ids') == want, f'ids = {need("ids")}, а нужно {want}.'
```

### hint
`nlargest(3, "amount")` — три строки с наибольшей суммой, уже по убыванию.

### hint
`df.nlargest(3, "amount")["order_id"].tolist()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
ids = df.nlargest(3, "amount")["order_id"].tolist()
```

### explain
Три самых дорогих заказа — по три стакана: сезонный напиток на 1 260 ₽ и два рафа по 1 170 ₽. `nlargest` короче, чем сортировка + `head`, и сразу говорит, что нам нужно: «три наибольших».

## task: map | Каналы по-английски | base

Для отчёта зарубежным партнёрам добавьте столбец `channel_en`: `"зал"` → `"dine-in"`, `"с собой"` → `"takeaway"`, `"доставка"` → `"delivery"`. Затем посчитайте `n_takeaway` — число заказов `"takeaway"` по новому столбцу.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
assert 'channel_en' in df.columns, 'Нет столбца channel_en.'
assert df['channel_en'].notna().all(), 'В channel_en есть пустые значения — проверьте написание ключей словаря.'
assert set(df['channel_en']) == {'dine-in', 'takeaway', 'delivery'}, f'Значения: {sorted(set(df["channel_en"]))}.'
assert need('n_takeaway') == (df['channel'] == 'с собой').sum(), f'n_takeaway = {need("n_takeaway")}.'
```

### hint
`map` со словарём заменяет каждое значение по словарю: ключ — старое, значение — новое.

### hint
`df["channel_en"] = df["channel"].map({"зал": "dine-in", "с собой": "takeaway", "доставка": "delivery"})`, затем сумма маски `== "takeaway"`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["channel_en"] = df["channel"].map({"зал": "dine-in", "с собой": "takeaway", "доставка": "delivery"})
n_takeaway = (df["channel_en"] == "takeaway").sum()
```

### explain
С собой — 730 заказов. Английские названия удобно держать отдельным столбцом: исходный `channel` остаётся для русских отчётов, и ничего не нужно переводить обратно.

## task: cut | Сегменты чеков | base

Разложите заказы по сегментам: до 250 включительно — `"малый"`, до 500 включительно — `"средний"`, дороже — `"крупный"`. Сохраните столбец `segment` и `counts` — число заказов в каждом сегменте: словарь «сегмент → число» (подойдёт и Series из `value_counts`).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
a = _pd.read_csv('orders_3m.csv')['amount']
want = {'малый': int((a <= 250).sum()), 'средний': int(((a > 250) & (a <= 500)).sum()), 'крупный': int((a > 500).sum())}
got = {str(k): int(v) for k, v in dict(need('counts')).items()}
assert got == want, f'counts = {got}, а нужно {want}.'
assert 'segment' in df.columns, 'Нет столбца segment.'
```

### hint
Диапазоны — `pd.cut`: ему нужны границы `bins` (от нуля до заведомо большого числа) и подписи `labels` — на одну меньше, чем границ.

### hint
`pd.cut(df["amount"], bins=[0, 250, 500, 100_000], labels=["малый", "средний", "крупный"])`. Частоты — `value_counts()`, словарь из них — `dict(...)`.

### hint
```python
df["segment"] = pd.cut(df["amount"], bins=[0, 250, 500, ...], labels=[...])
counts = dict(df["segment"]....())
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["segment"] = pd.cut(df["amount"], bins=[0, 250, 500, 100_000], labels=["малый", "средний", "крупный"])
counts = dict(df["segment"].value_counts())
```

### explain
Средних чеков (251–500 ₽) — 864, малых — 833, крупных — 392. Почти пятая часть заказов — крупные: они делают заметную долю выручки, и их стоит смотреть отдельно.

## task: loc-update | Скидка для доставки | base

Создайте столбец `amount_net`, равный `amount`, а для заказов с доставкой — на 10 % меньше (округлите до целого). Меняйте значения через `loc`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["amount_net"] = df["amount"]   # копия целого столбца (int64): дробные значения в него не запишутся — округляйте

```

### check
```python
d = df
dl = d['channel'] == 'доставка'
assert (d.loc[~dl, 'amount_net'] == d.loc[~dl, 'amount']).all(), 'Для заказов без доставки amount_net должен совпадать с amount.'
assert (d.loc[dl, 'amount_net'] == (d.loc[dl, 'amount'] * 0.9).round()).all(), 'Для доставки amount_net = round(amount × 0.9). Если значения не изменились — проверьте, что меняете через df.loc[маска, "amount_net"].'
```

### hint
Сначала `df["amount_net"] = df["amount"]` — копия для всех строк, потом меняем только доставку.

### hint
`df.loc[маска, "amount_net"] = (df.loc[маска, "amount"] * 0.9).round()`. Без `.round()` будет `TypeError: Invalid value … for dtype 'int64'`: в целый столбец нельзя записать 235.8.

### hint
```python
is_delivery = df["channel"] == ...
df.loc[is_delivery, "amount_net"] = (df.loc[is_delivery, ...] * 0.9).round()
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["amount_net"] = df["amount"]
is_delivery = df["channel"] == "доставка"
df.loc[is_delivery, "amount_net"] = (df.loc[is_delivery, "amount"] * 0.9).round()
```

### explain
Скидка меняет только строки доставки: 500 → 450, остальные суммы прежние. Такой столбец удобно сравнивать с исходным: `(df["amount"] - df["amount_net"]).sum()` — сколько стоит скидка в рублях.

## task: rename | Таблица для выгрузки | plus

Подготовьте `export` — таблицу без столбцов `client_id` и `channel`, где `amount` переименован в `sum_rub`, отсортированную по `sum_rub` по убыванию. Исходный `df` не меняйте.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
e = need('export', _pd.DataFrame)
assert list(e.columns) == ['order_id', 'datetime', 'shop_id', 'drink', 'size', 'qty', 'sum_rub'], f'Столбцы: {list(e.columns)}.'
assert e['sum_rub'].is_monotonic_decreasing, 'Таблица должна быть отсортирована по sum_rub по убыванию.'
assert 'amount' in df.columns and 'client_id' in df.columns, 'Исходный df не должен меняться.'
```

### hint
Цепочка: `df.drop(columns=[...]).rename(columns={...}).sort_values(...)`.

### hint
Сортируйте уже по новому имени `sum_rub` — после `rename` старого `amount` нет.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
export = (df.drop(columns=["client_id", "channel"])
            .rename(columns={"amount": "sum_rub"})
            .sort_values("sum_rub", ascending=False))
```

### explain
Длинную цепочку удобно взять в скобки и разнести по строкам — Python разрешает переносы внутри скобок.

## task: hour | Час пик | star

Добавьте столбец `hour` — час заказа числом (из текста `datetime` вида `2026-09-01 10:31`), и найдите `peak_hour` — час, на который пришлось больше всего заказов.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
h = d['datetime'].str[11:13].astype(int)
assert 'hour' in df.columns and (df['hour'] == h).all(), 'hour должен быть числом часа из datetime.'
assert need('peak_hour') == h.value_counts().idxmax(), f'peak_hour = {need("peak_hour")}.'
```

### hint
Срез строк в pandas — `df["datetime"].str[11:13]`. Превратить в число — `.astype(int)`.

### hint
Час пик — `df["hour"].value_counts().idxmax()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["hour"] = df["datetime"].str[11:13].astype(int)
peak_hour = df["hour"].value_counts().idxmax()
```

### explain
Больше всего заказов в 9 утра — 255, затем 10 и 13 часов. Утренний пик — кофе по дороге на работу. Пока дата — текст, час достаём срезом символов; в уроке «Даты и время» то же даст `dt.hour`.
