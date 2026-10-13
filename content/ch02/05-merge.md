---
title: "Соединения: JOIN и UNION"
lead: "В заказах есть номер кофейни, но нет города; есть название напитка, но нет себестоимости. Эти данные лежат в справочниках — соединяем таблицы через merge, как JOIN в SQL, и ловим дубли в справочниках. Соединения по индексу, anti join и UNION — в следующем уроке."
files: [orders_3m.csv, shops.csv, menu.csv]
recap:
  - "`pd.merge(left, right, on=\"key\", how=\"left\")` — JOIN. `how`: `\"inner\"` (по умолчанию), `\"left\"`, `\"right\"`, `\"outer\"`."
  - "Ключи с разными именами — `left_on=…, right_on=…`; одинаковые не-ключевые столбцы получат суффиксы `_x`/`_y`."
  - "`validate=\"many_to_one\"` — проверить, что справочник не размножит строки. Дубли в ключе справочника — самая частая ошибка JOIN."
  - "Пустые после LEFT JOIN — `NaN`; заменить нулями — `fillna(0)`."
---

## Справочники

Кроме заказов, у сети есть два справочника:

```python
import pandas as pd
shops = pd.read_csv("shops.csv")
shops
```

```python
import pandas as pd
menu = pd.read_csv("menu.csv")
menu.head()
```

В `shops` — город, название, дата открытия и число посадочных мест каждой кофейни. В `menu` — категория напитка, цена и себестоимость маленького размера. Чтобы посчитать выручку по **городам** или маржу по **категориям**, их нужно присоединить к заказам.

## merge: JOIN в pandas

Зачем: в заказах есть только код кофейни `shop_id`, а вопрос «сколько заработала Казань» требует города. Город лежит в справочнике — значит, к каждому заказу надо подтянуть строку справочника с тем же кодом. Это JOIN, в pandas — `merge`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

full = pd.merge(df, shops, on="shop_id", how="left")
full[["order_id", "shop_id", "city", "name", "amount"]].head()
```

- `on` — по какому столбцу соединять (ключ есть в обеих таблицах);
- `how` — тип соединения, как в SQL.

Теперь выручка по городам — обычная группировка:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

full = df.merge(shops, on="shop_id", how="left")
full.groupby("city")["amount"].sum().sort_values(ascending=False)
```

`df.merge(shops, …)` — то же, что `pd.merge(df, shops, …)`; левая таблица — та, у которой вызвали метод.

::: sql
`pd.merge(df, shops, on="shop_id", how="left")` — `SELECT * FROM orders o LEFT JOIN shops s ON o.shop_id = s.shop_id`.
:::

{{practice: city, by-city, p-merge, category}}

## Типы соединений

| `how=` | SQL | Какие строки останутся |
|---|---|---|
| `"inner"` | `INNER JOIN` | только те, у которых нашлась пара (по умолчанию) |
| `"left"` | `LEFT JOIN` | все из левой, пустые `NaN` там, где пары нет |
| `"right"` | `RIGHT JOIN` | все из правой |
| `"outer"` | `FULL OUTER JOIN` | все из обеих |

Посмотрим на разницу. В справочнике есть кофейня `EKB-1` — она открывается только 15 октября, и заказов у неё в выгрузке нет:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

rev = df.groupby("shop_id", as_index=False).agg(revenue=("amount", "sum"))
print(len(pd.merge(shops, rev, on="shop_id", how="inner")), "строк при inner")
pd.merge(shops, rev, on="shop_id", how="left")[["shop_id", "city", "revenue"]]
```

При `left` Екатеринбург остался, а выручка у него — `NaN`. Для отчёта такие пустые обычно заменяют нулями: `fillna(0)`.

::: figure merge-types
Справочник из трёх кофеен и выручка двух из них. `inner` оставляет только пары, `left` — все строки левой таблицы.
:::

::: predict
```python static
import pandas as pd
a = pd.DataFrame({"k": [1, 2, 3]})
b = pd.DataFrame({"k": [1, 1, 4], "v": ["x", "y", "z"]})
print(len(pd.merge(a, b, on="k")))
```

- `3`
- [x] `2`
- `1`

Почему: `inner` по умолчанию. Пара есть только у ключа 1, но в `b` он встречается дважды — поэтому строка из `a` повторилась два раза. Ключи 2, 3 и 4 пары не нашли.
:::

::: quiz
Управляющему нужен отчёт о выручке **всех** кофеен сети, включая `EKB-1`, у которой ещё нет заказов. Как соединить справочник `shops` и таблицу выручки `rev`?

- [x] `pd.merge(shops, rev, on="shop_id", how="left")` — справочник слева
  > `left` сохраняет все строки левой таблицы. Справочник слева — все кофейни в отчёте, у `EKB-1` выручка `NaN`, её заменяют нулём.
- [ ] `pd.merge(rev, shops, on="shop_id", how="left")`
  > Слева теперь выручка, а в ней `EKB-1` нет — кофейня без заказов из отчёта пропадёт.
- [ ] `pd.merge(shops, rev, on="shop_id")` — по умолчанию
  > По умолчанию `inner`: остаются только кофейни, у которых нашлась пара, и `EKB-1` исчезает.
- [ ] `pd.merge(shops, rev, on="shop_id", how="right")`
  > `right` сохраняет все строки правой таблицы — выручки, а в ней `EKB-1` нет.
:::

{{practice: all-shops, per-seat, margin}}

## Главная ловушка: дубли в справочнике

Пример выше показывает опасность: если ключ в «справочнике» повторяется, строки основной таблицы **размножаются**, и все суммы молча растут. Защита — параметр `validate`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

ok = df.merge(shops, on="shop_id", how="left", validate="many_to_one")
print(len(df), len(ok))
```

`"many_to_one"` значит «в правой таблице каждый ключ — не больше одного раза». Если это не так, merge упадёт с ошибкой `MergeError`, а не испортит данные. Её полное имя — `pd.errors.MergeError`: так её пишут в `except`, если ошибку нужно перехватить (`try/except` — из урока «Исключения — как не падать на грязных данных»). Ставьте `validate` каждый раз, когда присоединяете справочник.

::: tip
Простая самопроверка после любого JOIN: число строк до и после. Для `left` со справочником оно не должно меняться.
:::

### Разберём вместе: как один дубль в справочнике меняет выручку

Три заказа: PRM-1 — 300 ₽, KZN-1 — 250 ₽, PRM-1 — 400 ₽. Выручка — **950 ₽**. Справочник кофеен по ошибке содержит KZN-1 дважды:

| shop_id | city |
|---|---|
| PRM-1 | Пермь |
| KZN-1 | Казань |
| KZN-1 | Казань |
| EKB-1 | Екатеринбург |

Что делает `merge(orders, shops, on="shop_id", how="left")`:

1. Заказ 1 (PRM-1) находит одну пару — одна строка.
2. Заказ 2 (KZN-1) находит **две** пары — две строки, обе по 250 ₽.
3. Заказ 3 (PRM-1) — одна строка.
4. EKB-1 из справочника заказов не имеет — при `how="left"` (заказы слева) он в результат не попадает.

Итог: 4 строки вместо 3, выручка **1 200 ₽** вместо 950. Ни ошибки, ни предупреждения. По городам Казань «заработала» 500 ₽ вместо 250.

::: figure merge-dup
Заказ KZN-1 нашёл в справочнике две пары и превратился в две строки — выручка выросла без единого предупреждения.
:::

::: tip Аналогия
Рассылка приглашений по адресной книге: если коллега записан в книге дважды, письмо придёт ему два раза, а в отчёте «отправлено» окажется на одно больше. JOIN со справочником работает так же: каждая строка заказа «отправляется» по всем совпавшим записям. Хромает аналогия в одном: два письма коллега заметит, а лишнюю строку в таблице не заметит никто, пока не сверит итоги.
:::

```python
import pandas as pd
orders = pd.DataFrame({"shop_id": ["PRM-1", "KZN-1", "PRM-1"], "amount": [300, 250, 400]})
shops = pd.DataFrame({"shop_id": ["PRM-1", "KZN-1", "KZN-1", "EKB-1"],
                      "city": ["Пермь", "Казань", "Казань", "Екатеринбург"]})
full = orders.merge(shops, on="shop_id", how="left")
print(len(orders), "→", len(full), "| выручка", orders["amount"].sum(), "→", full["amount"].sum())
```

Что получилось: проверка «строк столько же, сколько было» и `validate="many_to_one"` — дешёвая страховка от самой дорогой ошибки соединения.

::: quiz
После `merge` заказов со справочником кофеен строк стало больше, чем было заказов. Что, скорее всего, случилось?

- [x] В справочнике у какой-то кофейни две строки — её заказы задвоились
  > Каждая строка заказа соединяется со **всеми** подходящими строками справочника. Защита — `validate="many_to_one"`.
- [ ] `merge` всегда добавляет строки
  > При ключе, уникальном в справочнике, `left` сохраняет число строк левой таблицы.
- [ ] Нужно было `how="inner"`
  > `inner` может только убрать строки без пары, а задвоение останется.
- [ ] В заказах есть пропуски в `shop_id`
  > Строки с пустым ключом не размножаются — они просто не найдут пары.
:::

{{practice: validate}}

## Ключи с разными именами и одинаковые столбцы

Зачем: справочники ведут разные люди, и один и тот же ключ называется по-разному — в меню `drink`, в прайсе прошлого года `name`. А столбцы с одинаковым смыслом, наоборот, часто называются одинаково — `price_s` и там и там.

Если ключ в таблицах называется по-разному, используют `left_on` и `right_on`. А если кроме ключа в обеих таблицах есть столбцы с одинаковым именем, pandas добавит к ним суффиксы `_x` и `_y` — их можно задать через `suffixes`. Сравним цены маленького размера в 2026 и 2025 годах:

```python
import pandas as pd
menu = pd.read_csv("menu.csv")                      # столбцы: drink, category, price_s, cost_s
prices_2025 = pd.DataFrame({"name": ["Латте", "Раф"], "price_s": [195, 240]})

cmp = pd.merge(menu, prices_2025, left_on="drink", right_on="name",
               suffixes=("_2026", "_2025"))
print(cmp.columns.tolist())
cmp[["drink", "name", "price_s_2026", "price_s_2025"]]
```

Что здесь происходит:

- `left_on="drink", right_on="name"` — в левой таблице ключ берётся из `drink`, в правой — из `name`. Пары: «Латте» с «Латте», «Раф» с «Раф».
- `price_s` есть в обеих таблицах, и это не ключ. Без `suffixes` получились бы `price_s_x` (из левой) и `price_s_y` (из правой); с `suffixes=("_2026", "_2025")` — понятные `price_s_2026` и `price_s_2025`. Первый суффикс — левой таблице, второй — правой.
- Суффиксы достаются **только** столбцам с совпадающими именами: `category` и `cost_s` остались как были.
- Оба ключевых столбца остаются в результате — и `drink`, и `name`: при разных именах pandas не знает, какой из них выбросить. Лишний убирают сами: `.drop(columns="name")`.
- `merge` по умолчанию `inner`, поэтому строк две: в прайсе 2025 года были только латте и раф. Латте подорожал с 195 до 210 ₽, раф — с 240 до 260.

## Практика

## task: city | Город к заказу | warmup

Присоедините к заказам справочник кофеен (LEFT JOIN по `shop_id`) и сохраните результат в `full`. Число строк должно остаться прежним.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

```

### check
```python
import pandas as _pd
f = need('full', _pd.DataFrame)
assert 'city' in f.columns and 'seats' in f.columns, 'В full должны появиться столбцы справочника: city, seats…'
assert len(f) == len(df), f'Строк стало {len(f)}, а было {len(df)}. Для LEFT JOIN со справочником число строк не меняется.'
```

### hint
Заказы — слева (все остаются), справочник — справа (добавляет столбцы).

### hint
`pd.merge(df, shops, on="shop_id", how="left")`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
full = pd.merge(df, shops, on="shop_id", how="left")
```

## task: by-city | Выручка по городам | warmup

Посчитайте `by_city` — выручку по городам (Series), отсортированную по убыванию, и `best_city` — город-лидер.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

```

### check
```python
import pandas as _pd
f = _pd.read_csv('orders_3m.csv').merge(_pd.read_csv('shops.csv'), on='shop_id')
want = f.groupby('city')['amount'].sum().sort_values(ascending=False)
assert need('by_city').to_dict() == want.to_dict(), f'by_city = {need("by_city").to_dict()}.'
assert need('best_city') == want.index[0], f'best_city = {need("best_city")!r}.'
```

### hint
Сначала merge, потом `groupby("city")["amount"].sum().sort_values(ascending=False)`.

### hint
Лидер — первый индекс отсортированной Series: `by_city.index[0]`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
full = df.merge(shops, on="shop_id", how="left")
by_city = full.groupby("city")["amount"].sum().sort_values(ascending=False)
best_city = by_city.index[0]
```

## task: p-merge | Соберите выручку по категориям | warmup

Соберите программу, которая выводит выручку категории «кофе».

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
menu = pd.read_csv("menu.csv")
full = df.merge(menu, on="drink", how="left")
by_cat = full.groupby("category")["amount"].sum()
print(by_cat["кофе"])
```

### check
```python
import pandas as _pd
f = _pd.read_csv('orders_3m.csv').merge(_pd.read_csv('menu.csv'), on='drink')
want = f.groupby('category')['amount'].sum()['кофе']
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Обе таблицы загружаются до соединения, группировка — после.

### hint
Категория — в `menu.csv`, соединяем по `drink`; выручка категории — `groupby("category")["amount"].sum()["кофе"]`.

## task: category | Не кофе | base

Посчитайте `non_coffee_share` — долю выручки напитков категории «не кофе» в процентах с одним знаком.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
menu = pd.read_csv("menu.csv")

```

### check
```python
import pandas as _pd
f = _pd.read_csv('orders_3m.csv').merge(_pd.read_csv('menu.csv'), on='drink')
want = round(f[f['category'] == 'не кофе']['amount'].sum() / f['amount'].sum() * 100, 1)
assert close(need('non_coffee_share'), want), f'non_coffee_share = {need("non_coffee_share")}, а нужно {want}.'
```

### hint
Присоедините `menu` по `drink`, затем доля: выручка с маской на категорию, делённая на всю выручку.

### hint
`full[full["category"] == "не кофе"]["amount"].sum() / full["amount"].sum() * 100`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
menu = pd.read_csv("menu.csv")
full = df.merge(menu, on="drink", how="left", validate="many_to_one")
non_coffee_share = round(full[full["category"] == "не кофе"]["amount"].sum() / full["amount"].sum() * 100, 1)
```

### explain
«Не кофе» (чай, какао, матча) — 14.9 % выручки. Категории нет в заказах — она живёт в справочнике меню, и без соединения этот вопрос не задать.

## task: all-shops | Все кофейни в отчёте | base

Соберите `report` — таблицу **всех** кофеен справочника (7 строк) со столбцами `shop_id`, `city`, `revenue`. У кофеен без заказов выручка должна быть 0, а не `NaN`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

```

### check
```python
import pandas as _pd
r = need('report', _pd.DataFrame)
assert len(r) == 7, f'Строк {len(r)}, а кофеен в справочнике 7.'
assert list(r.columns) == ['shop_id', 'city', 'revenue'], f'Столбцы: {list(r.columns)}.'
assert r['revenue'].notna().all(), 'В revenue есть NaN — замените на 0 через fillna(0).'
assert r.set_index('shop_id').loc['EKB-1', 'revenue'] == 0, 'У EKB-1 выручка должна быть 0.'
want = _pd.read_csv('orders_3m.csv').groupby('shop_id')['amount'].sum()
assert r.set_index('shop_id').loc['PRM-1', 'revenue'] == want['PRM-1'], 'Выручка PRM-1 не совпадает.'
```

### hint
Сначала выручка по кофейням (`as_index=False`), потом `pd.merge(shops, rev, on="shop_id", how="left")` — справочник слева.

### hint
`report["revenue"] = report["revenue"].fillna(0)`, лишние столбцы уберите выбором `[["shop_id", "city", "revenue"]]`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
rev = df.groupby("shop_id", as_index=False).agg(revenue=("amount", "sum"))
report = pd.merge(shops, rev, on="shop_id", how="left")[["shop_id", "city", "revenue"]]
report["revenue"] = report["revenue"].fillna(0)
```

### explain
В отчёте семь кофеен, у EKB-1 — 0. Без `fillna(0)` там был бы `NaN`, и сумма выручки по отчёту всё равно сошлась бы, а вот сортировка и графики вели бы себя странно.

## task: per-seat | Выручка на посадочное место | base

Какая кофейня зарабатывает больше всего **на одно посадочное место**? Сохраните её `shop_id` в `best_per_seat`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

```

### check
```python
import pandas as _pd
s = _pd.read_csv('shops.csv').set_index('shop_id')
rev = _pd.read_csv('orders_3m.csv').groupby('shop_id')['amount'].sum()
import numbers as _num
want = (rev / s.loc[rev.index, 'seats']).idxmax()
_b = need('best_per_seat')
assert not isinstance(_b, (_pd.Series, _pd.DataFrame)), f'В best_per_seat лежит {type(_b).__name__}, а нужен один код кофейни — строка вида "KZN-1".'
assert not isinstance(_b, _num.Integral), f'best_per_seat = {_b} — это номер строки, а нужен код кофейни. После merge индекс таблицы — номера 0, 1, 2…, и idxmax возвращает номер. Возьмите по нему shop_id: t.loc[номер, "shop_id"] — или отсортируйте таблицу.'
assert _b == want, f'best_per_seat = {_b!r}, а нужна другая кофейня. Делите выручку кофейни на её seats и ищите максимум.'
```

### hint
Три шага: выручка по кофейням → merge со справочником (там число мест `seats`) → новый столбец `revenue / seats` и его максимум.

### hint
Выручку посчитайте с `as_index=False`, чтобы `shop_id` остался столбцом для merge. Но тогда индекс у таблицы — номера строк 0…5, и `t["per_seat"].idxmax()` вернёт **номер строки**, а не код кофейни. Код достают по этому номеру: `t.loc[t["per_seat"].idxmax(), "shop_id"]` — или сортируют таблицу и берут первый `shop_id`.

### hint
```python
rev = df.groupby("shop_id", as_index=False).agg(revenue=("amount", "sum"))
t = rev.merge(shops, on=..., how="left")
t["per_seat"] = t["revenue"] / t[...]
best_per_seat = t.loc[t["per_seat"].idxmax(), ...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
rev = df.groupby("shop_id", as_index=False).agg(revenue=("amount", "sum"))
t = rev.merge(shops, on="shop_id", how="left", validate="one_to_one")
t["per_seat"] = t["revenue"] / t["seats"]
best_per_seat = t.sort_values("per_seat", ascending=False)["shop_id"].iloc[0]
```

### explain
PRM-1 — 7 757 ₽ на место за осень, почти в два с половиной раза больше UFA-1 (3 294 ₽). KZN-1 по выручке почти равна PRM-1, но на 30 местах — на место она зарабатывает меньше. Типичная ошибка — `t["per_seat"].idxmax()` без `loc`: после `merge` индекс — номера строк, и ответом стало бы число 2 (строка PRM-1), а не код кофейни. `idxmax` возвращает подпись строки, а подпись здесь — номер.

## task: margin | Маржа по напиткам | plus

Себестоимость в `menu.csv` дана для размера S. Для M она в 1,25 раза больше, для L — в 1,5 раза. Посчитайте для каждого заказа себестоимость `cost` (с учётом размера и количества), затем маржу по напиткам в процентах: `(выручка − себестоимость) / выручка × 100`. Сохраните в `best_margin` напиток с наибольшей маржой.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
menu = pd.read_csv("menu.csv")
SIZE_K = {"S": 1.0, "M": 1.25, "L": 1.5}

```

### check
```python
import pandas as _pd
f = _pd.read_csv('orders_3m.csv').merge(_pd.read_csv('menu.csv'), on='drink')
f['cost'] = f['cost_s'] * f['size'].map({'S': 1.0, 'M': 1.25, 'L': 1.5}) * f['qty']
g = f.groupby('drink')[['amount', 'cost']].sum()
want = ((g['amount'] - g['cost']) / g['amount']).idxmax()
assert need('best_margin') == want, f'best_margin = {need("best_margin")!r}, а нужно {want!r}.'
```

### hint
После merge: `full["cost"] = full["cost_s"] * full["size"].map(SIZE_K) * full["qty"]`.

### hint
Суммы по напиткам двух столбцов сразу: `full.groupby("drink")[["amount", "cost"]].sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
menu = pd.read_csv("menu.csv")
SIZE_K = {"S": 1.0, "M": 1.25, "L": 1.5}
full = df.merge(menu, on="drink", how="left", validate="many_to_one")
full["cost"] = full["cost_s"] * full["size"].map(SIZE_K) * full["qty"]
g = full.groupby("drink")[["amount", "cost"]].sum()
g["margin"] = (g["amount"] - g["cost"]) / g["amount"] * 100
best_margin = g["margin"].idxmax()
```

### explain
Самая высокая маржа — у чая (87.5 %), самая низкая — у матчи (68 %). Разница почти в 20 пунктов: продвигать чай выгоднее, чем матчу, даже если матча дороже в чеке.

## task: validate | Ловим дубль в справочнике | star

В справочник по ошибке попала строка-дубль. Сделайте merge заказов со справочником `shops_bad` **с проверкой** `validate="many_to_one"` и перехватите ошибку в `try/except` — ловите именно `pd.errors.MergeError`, а не любую ошибку: в `caught` должно оказаться `True`. Затем посчитайте `extra` — на сколько строк выросла бы таблица, если сделать merge без проверки.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
shops_bad = pd.concat([shops, shops[shops["shop_id"] == "KZN-1"]], ignore_index=True)

```

### check
```python
import pandas as _pd
assert need('caught') is True, 'caught должно быть True — merge с validate должен упасть с MergeError.'
want = int((df['shop_id'] == 'KZN-1').sum())
assert need('extra') == want, f'extra = {need("extra")}, а нужно {want}: каждая строка KZN-1 размножилась.'
assert 'MergeError' in _code, 'Перехватите именно pd.errors.MergeError: except Exception поймает и любую другую ошибку — например, опечатку в имени столбца, — и caught станет True по неверной причине.'
```

### hint
Ошибку перехватывают конструкцией `try/except`: в `try` — merge с `validate`, в `except` — что делать, если он упал. Имя ошибки — `pd.errors.MergeError`. Лишние строки — разница длин таблицы после merge без проверки и исходной.

### hint
`extra = len(pd.merge(df, shops_bad, on="shop_id")) - len(df)`

### hint
```python static
try:
    pd.merge(..., validate="many_to_one")
    caught = False
except pd.errors.MergeError:
    caught = True
extra = len(pd.merge(df, shops_bad, on="shop_id", how="left")) - len(...)
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
shops_bad = pd.concat([shops, shops[shops["shop_id"] == "KZN-1"]], ignore_index=True)
try:
    pd.merge(df, shops_bad, on="shop_id", how="left", validate="many_to_one")
    caught = False
except pd.errors.MergeError:
    caught = True
extra = len(pd.merge(df, shops_bad, on="shop_id", how="left")) - len(df)
```

### explain
Без проверки все заказы KZN-1 задвоились бы, и выручка Казани выросла бы почти на 200 тысяч — никакой ошибки, просто неверный отчёт. `validate` превращает тихую ошибку в громкую.
