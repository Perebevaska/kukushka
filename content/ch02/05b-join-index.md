---
title: "Соединения по индексу, anti join и UNION"
lead: "merge — не единственный способ соединить таблицы. Обычное присваивание столбца тоже ищет пару — по индексу, и молча портит данные, если индексы не совпали. Разбираем этот «тихий JOIN», join по индексу, ключи разного типа, поиск строк без пары и склейку выгрузок."
files: [orders_3m.csv, shops.csv, menu.csv]
recap:
  - "Присвоение Series — тихий JOIN по индексу: `shops[\"revenue\"] = rev` при разных индексах даёт `NaN`. Правильно — `shops[\"shop_id\"].map(rev)` или `set_index`; список (`tolist()`) ложится по позициям — молча не туда."
  - "`a.join(b)` — LEFT JOIN по индексу; `shops.join(stats, on=\"shop_id\")` — столбец слева с индексом справа."
  - "Ключи разного типа (`int64` и `str`) — `ValueError`; приведите к одному (`astype(str)`, `str.zfill`) и проверьте, сколько пар нашлось (`indicator=True`)."
  - "Строк без пары: `indicator=True` и столбец `_merge` (`left_only`) или `~df[\"key\"].isin(other[\"key\"])` — anti join."
  - "`pd.concat([a, b])` — UNION ALL; `.drop_duplicates()` — UNION."
---

## Тихий JOIN: присваивание столбца выравнивается по индексу

Есть способ соединить данные, который не похож на соединение, — обычное присваивание столбца: `shops["revenue"] = rev`. Если справа **Series**, pandas не кладёт значения по порядку, а **ищет пару по индексу** — так же, как JOIN ищет пару по ключу. Отсюда и название: это JOIN, только без слова `merge` и без предупреждений. Работает он отлично, если индексы совпадают, и молча портит данные, если нет.

::: tip Аналогия
Раздать ведомость с баллами по классу. Список — раздаём листки по порядку парт: если кто-то пересел, баллы достанутся не тем. Series — на каждом листке написана фамилия, и листок находит своего хозяина, где бы тот ни сидел. Но если фамилии на листках записаны по-другому («Иванов А.» вместо «Иванов»), никто свой листок не получит.
:::

**Пример руками.** Таблица из трёх строк с индексом 0, 1, 2 и два способа добавить столбец:

| индекс | drink | Series `[10, 20, 30]` с индексом `[2, 0, 1]` | список `[10, 20, 30]` |
|---|---|---|---|
| 0 | Латте | ищем индекс 0 → **20** | первое значение → **10** |
| 1 | Раф | индекс 1 → **30** | второе → **20** |
| 2 | Чай | индекс 2 → **10** | третье → **30** |

::: figure index-align
Series раздаёт значения по индексу (цвет — индекс), список — по порядку строк. Одни и те же три числа легли по-разному.
:::

```python
import pandas as pd
t = pd.DataFrame({"drink": ["Латте", "Раф", "Чай"]})
s = pd.Series([10, 20, 30], index=[2, 0, 1])

t["by_index"] = s              # Series: значения ищут свою строку по индексу
t["by_order"] = [10, 20, 30]   # список: значения ложатся по порядку
t
```

Что здесь происходит:

- `t["by_index"] = s` — для каждой строки `t` pandas берёт из `s` значение с **тем же индексом**: строке 0 достаётся 20, потому что в `s` у индекса 0 стоит 20.
- `t["by_order"] = [...]` — у списка нет индекса, значения раскладываются по позициям. Длина списка обязана совпасть с числом строк.

**На реальных данных — три ловушки.** Добавим в справочник кофеен выручку, посчитанную `groupby`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

rev = df.groupby("shop_id")["amount"].sum()   # индекс — shop_id
print(rev.index.tolist())
print(shops.index.tolist())                   # индекс — 0…6
shops["revenue"] = rev                        # ловушка 1: индексы не пересекаются
shops[["shop_id", "revenue"]]
```

Ловушка 1 — **все `NaN`**, без ошибки. У `rev` индекс — коды кофеен, у `shops` — номера строк 0…6. Ни одна пара не нашлась.

Ловушка 2 — «тогда возьму список». У `rev` 6 значений, у `shops` 7 строк (у EKB-1 заказов нет) — и pandas падает с `ValueError: Length of values (6) does not match length of index (7)`. Хуже, если длины совпадут: отбросим EKB-1 — и список ляжет **молча и неправильно**:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
rev = df.groupby("shop_id")["amount"].sum()     # порядок: KZN-1, KZN-2, PRM-1, …

open_shops = shops[shops["shop_id"] != "EKB-1"].copy()   # порядок: PRM-1, PRM-2, KZN-1, …
open_shops["revenue"] = rev.tolist()                     # по позициям — не туда!
open_shops[["shop_id", "revenue"]].head(3)
```

PRM-1 получила выручку KZN-1 (181 365 вместо 186 163): `groupby` сортирует ключи по алфавиту, а справочник идёт в своём порядке. Ни ошибки, ни предупреждения.

**Как правильно.** Сделать так, чтобы индексы совпадали по смыслу, — или соединять явно:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
rev = df.groupby("shop_id")["amount"].sum()

shops["revenue"] = shops["shop_id"].map(rev)     # способ 1: map ищет каждый shop_id в индексе rev
print(shops[["shop_id", "revenue"]])

by_code = shops.set_index("shop_id")             # способ 2: справочник с тем же индексом
by_code["revenue2"] = rev
print(by_code["revenue2"].tail(2))
```

Что здесь происходит:

- `shops["shop_id"].map(rev)` — для каждого кода из столбца берёт значение из `rev` по индексу. Это LEFT JOIN одного столбца: у EKB-1 пары нет — `NaN`.
- `set_index("shop_id")` делает коды кофеен индексом справочника. Теперь индексы обеих сторон — коды, и присваивание находит пары.
- Тот же результат дал бы `merge` из начала урока — он нагляднее и проверяется `validate`.

**Дубли в индексе.** Если в индексе правой Series значение повторяется, pandas не знает, какое из них взять, и падает: `ValueError: cannot reindex on an axis with duplicate labels`. Так бывает, если сделать индексом столбец заказов: `df.set_index("shop_id")["amount"]` — у каждой кофейни сотни строк. Это полезная ошибка: она останавливает ту же беду, от которой `merge` защищает `validate`.

::: predict
```python static
import pandas as pd
t = pd.DataFrame({"x": [1, 2, 3]})
s = pd.Series([100, 300], index=[0, 2])
t["y"] = s
print(t["y"].tolist())
```

- `[100, 300, nan]`
- [x] `[100.0, nan, 300.0]`
- `Ошибка ValueError`

Почему: значения ищут строку по индексу. У строки 0 пара — 100, у строки 2 — 300, у строки 1 пары нет — `NaN`. Из-за `NaN` числа стали дробными.
:::

::: warn Типичные ошибки
- **Столбец целиком из `NaN`.** Индексы не совпадают по смыслу: справа коды кофеен, слева номера строк. Лечится `map` или `set_index`.
- **`.tolist()` или `.values`, чтобы «убрать NaN».** Значения лягут по позициям — молча и, скорее всего, не на свои строки. Это хуже, чем `NaN`.
- **Присваивание после фильтра.** `df["big"] = df[df["amount"] > 500]["amount"]` — у отобранных строк индекс сохранился, и они попадут на свои места, а остальные получат `NaN`. Иногда это и нужно, но знать об этом надо.
- **`cannot reindex on an axis with duplicate labels`.** В индексе справа повторы — сначала агрегируйте (`groupby`), потом присваивайте.
:::

{{practice: align}}

## join и ключи разного типа

### DataFrame.join: соединение по индексу

После `groupby` ключ оказывается в индексе, и `merge` по столбцу требует `reset_index()`. Для таблиц, у которых ключ — индекс, есть короткий метод `join`. По умолчанию он делает LEFT JOIN **по индексу**:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

rev = df.groupby("shop_id").agg(revenue=("amount", "sum"))
guests = df.groupby("shop_id").agg(guests=("client_id", "nunique"))
rev.join(guests).head(3)        # обе таблицы — индекс shop_id
```

Если у левой таблицы ключ — обычный столбец, его называют в `on`, а у правой ключ по-прежнему ищется в индексе:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

stats = df.groupby("shop_id").agg(revenue=("amount", "sum"), guests=("client_id", "nunique"))
shops.join(stats, on="shop_id")[["shop_id", "city", "revenue", "guests"]]
```

Что здесь происходит:

- `rev.join(guests)` — пары ищутся по индексу обеих таблиц; это `merge(rev, guests, left_index=True, right_index=True, how="left")` одной короткой строкой.
- `shops.join(stats, on="shop_id")` — столбец `shop_id` слева сравнивается с индексом `stats`. Все 7 кофеен справочника на месте, у EKB-1 — `NaN`.

| | `merge` | `join` |
|---|---|---|
| по чему соединяет | по столбцам (`on`, `left_on`/`right_on`) | по индексу правой таблицы |
| тип по умолчанию | `inner` | `left` |
| когда удобнее | две «плоские» таблицы | результаты `groupby` с ключом в индексе |

### Ключ разного типа

Гости программы лояльности хранятся в двух системах. В кассовой выгрузке номер гостя — число `101`, а в отзывах из онлайн-формы — текст `"101"`. Для человека это одно и то же, для pandas — нет:

```python error
import pandas as pd
guests = pd.DataFrame({"guest_id": [101, 102, 103], "city": ["Пермь", "Казань", "Уфа"]})
reviews = pd.DataFrame({"guest_id": ["101", "103", "104"], "score": [5, 4, 2]})
guests.merge(reviews, on="guest_id", how="left")
```

`ValueError: You are trying to merge on int64 and str columns for key 'guest_id'` — pandas честно отказывается сравнивать число с текстом. Ключи приводят к **одному** типу:

```python
import pandas as pd
guests = pd.DataFrame({"guest_id": [101, 102, 103], "city": ["Пермь", "Казань", "Уфа"]})
reviews = pd.DataFrame({"guest_id": ["101", "103", "104"], "score": [5, 4, 2]})

guests["guest_id"] = guests["guest_id"].astype(str)        # число → текст
full = guests.merge(reviews, on="guest_id", how="left",
                    validate="one_to_one", indicator=True)
full
```

Что здесь происходит:

- `astype(str)` превращает `101` в `"101"` — теперь ключи сравнимы.
- `validate="one_to_one"` — у каждого гостя не больше одной строки с обеих сторон; если гость оставил два отзыва, merge упадёт, а не размножит строки.
- `indicator=True` показывает, у кого пара нашлась (`both`), — у гостя 102 отзыва нет.

Опаснее случай, когда ошибки **нет**. В одной системе номер записан с ведущими нулями, `"0101"`, в другой — `101`. После `astype(str)` получится `"101"`, merge пройдёт, но ни одна пара не найдётся: все отзывы — `NaN`. Поэтому после соединения по «починенному» ключу всегда смотрят, сколько пар нашлось (`_merge` или `notna().sum()`), а ведущие нули добавляют `str.zfill(4)`: `"101"` → `"0101"`.

::: warn Типичные ошибки
- **`ValueError: You are trying to merge on int64 and str columns`.** Ключи разного типа. Приведите обе стороны к одному: `astype(str)` или `astype(int)`.
- **Ключ «починили», но пар ноль.** Ведущие нули, пробелы по краям (`"101 "`), разный регистр (`"prm-1"`). Проверяйте `indicator=True` и чистите ключ: `str.strip()`, `str.upper()`, `str.zfill()`.
- **`astype(int)` на числовом столбце с пропусками.** Падает `IntCastingNaNError: Cannot convert non-finite values (NA or inf) to integer`. Либо сначала уберите пропуски, либо приводите к тексту.
- **`join` вместо `merge` по столбцу.** `a.join(b)` без `on` ищет пары по индексу **обеих** таблиц. Если ключ у них — одноимённый столбец, pandas упадёт: `ValueError: columns overlap but no suffix specified`. Хуже, если общих столбцов нет: тогда соединятся номера строк 0, 1, 2 — тихий JOIN по ничего не значащим номерам.
:::

::: quiz
После `reviews.merge(guests, on="guest_id", how="left")` ошибки не было, но у всех отзывов город — `NaN`. Ключ в обеих таблицах — текст. Что проверить первым?

- [x] Совпадает ли запись ключей: ведущие нули, пробелы, регистр
  > Тип одинаковый, значит pandas сравнивал честно — и не нашёл ни одного равного значения. Значит, значения записаны по-разному: `"0101"` и `"101"`, `"101 "` и `"101"`.
- [ ] Нужно было `how="inner"`
  > Inner просто выбросит все строки без пары — и вместо столбца `NaN` получится пустая таблица.
- [ ] Не указан `validate`
  > `validate` ловит дубли ключа, а не отсутствие пар.
- [ ] В `guests` дубли гостей
  > Дубли размножили бы строки, а не обнулили город у всех.
:::

{{practice: join, key-type}}

## Anti join: у кого нет пары

«Какие кофейни без заказов?», «какие позиции меню не продавались?» — это anti join. Проще всего через `isin`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

shops[~shops["shop_id"].isin(df["shop_id"])]
```

Или через `indicator=True` — merge добавит столбец `_merge` со значениями `both`, `left_only`, `right_only`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
menu = pd.read_csv("menu.csv")

sold = df[["drink"]].drop_duplicates()
m = pd.merge(menu, sold, on="drink", how="left", indicator=True)
m["_merge"].value_counts()
```

::: figure merge-indicator
Условный пример: `outer` с `indicator=True` показывает происхождение каждой строки. `left_only` — кофейни без продаж (это и есть anti join), `right_only` — коды, которых нет в справочнике.
:::

::: sql
`shops[~shops["shop_id"].isin(df["shop_id"])]` — `SELECT * FROM shops WHERE shop_id NOT IN (SELECT shop_id FROM orders)`.
:::

{{practice: anti}}

## concat: UNION

Выгрузки часто приходят частями — по месяцам или по кофейням. Склеить таблицы с одинаковыми столбцами «одна под другой» — `pd.concat`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

sep_df = df[df["datetime"].str.startswith("2026-09")]
oct_df = df[df["datetime"].str.startswith("2026-10")]
both = pd.concat([sep_df, oct_df], ignore_index=True)
print(len(sep_df), len(oct_df), len(both))
```

`ignore_index=True` заново нумерует строки 0, 1, 2… — иначе номера из исходных таблиц повторятся.

::: sql
`pd.concat([a, b])` — `UNION ALL`. Чтобы получить `UNION` (без повторов), добавьте `.drop_duplicates()`.
:::

::: predict
```python static
import pandas as pd
a = pd.DataFrame({"k": [1, 2]})
b = pd.DataFrame({"k": [1]})
m = pd.merge(a, b, on="k", how="left", indicator=True)
print(m["_merge"].tolist())
```

- `['both', 'both']`
- [x] `['both', 'left_only']`
- `['both']`

Почему: `left` сохраняет обе строки из `a`. У ключа 1 пара есть (`both`), у ключа 2 — нет (`left_only`).
:::

::: warn Типичные ошибки
- **Не проверили число строк.** После LEFT JOIN к справочнику строк должно остаться столько же.
- **INNER по умолчанию.** `merge` без `how` — внутреннее соединение: заказы без пары в справочнике молча пропадут.
- **Справочник не той стороной.** «Все кофейни в отчёте» — справочник слева, иначе кофейни без заказов исчезнут.
- **`concat` без `ignore_index=True`.** Номера строк повторятся, и `loc` начнёт возвращать по две строки.
:::

{{practice: concat}}

## Практика

## task: align | Почините тихий JOIN | base

Коллега хотел добавить в справочник кофеен выручку за три месяца, но столбец `revenue` получился целиком из `NaN`. Почините присваивание так, чтобы у каждой кофейни в `shops` стояла её выручка, а у кофейни без заказов — `0`. В `shops` должны остаться все 7 строк и столбец `shop_id`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

rev = df.groupby("shop_id")["amount"].sum()
shops["revenue"] = rev
shops[["shop_id", "revenue"]]
```

### check
```python
import pandas as _pd
sh = need('shops', _pd.DataFrame)
assert len(sh) == 7, f'В shops {len(sh)} строк, а в справочнике 7 кофеен. Кофейня без заказов тоже должна остаться.'
assert 'shop_id' in sh.columns, 'Столбец shop_id пропал из shops (ушёл в индекс?). Оставьте его обычным столбцом — например, через map.'
assert 'revenue' in sh.columns, 'В shops нет столбца revenue.'
assert sh['revenue'].notna().all(), 'В revenue остались NaN. У кофейни без заказов нужен 0: fillna(0).'
_d = _pd.read_csv('orders_3m.csv')
_want = _d.groupby('shop_id')['amount'].sum().to_dict()
_got = dict(zip(sh['shop_id'], sh['revenue']))
assert _got['PRM-1'] == _want['PRM-1'], f'У PRM-1 выручка {_got["PRM-1"]}, а должна быть {_want["PRM-1"]}. Похоже, значения легли по порядку, а не по коду кофейни.'
for _k, _v in _want.items():
    assert _got[_k] == _v, f'У {_k} выручка {_got[_k]}, а должна быть {_v}.'
assert _got['EKB-1'] == 0, f'У EKB-1 выручка {_got["EKB-1"]}, а заказов нет — нужен 0.'
assert 'tolist' not in _code and '.values' not in _code, 'Список значений ложится по позициям, а не по кофейням. Найдите пару по коду: map.'
```

### hint
У `rev` индекс — коды кофеен, у `shops` — номера строк 0…6. Пару нужно искать по столбцу `shop_id`, а не по индексу.

### hint
`shops["shop_id"].map(rev)` — для каждого кода берёт выручку из `rev`. У EKB-1 пары нет — `NaN`, его заменит `fillna(0)`.

### hint
```python
shops["revenue"] = shops["shop_id"].map(...).fillna(...)
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

rev = df.groupby("shop_id")["amount"].sum()
shops["revenue"] = shops["shop_id"].map(rev).fillna(0)
shops[["shop_id", "revenue"]]
```

### explain
`map` — это LEFT JOIN одного столбца: справочник слева, все 7 кофеен на месте, выручка нашла свою кофейню по коду, а у EKB-1 — 0. Соблазнительная «починка» `shops["revenue"] = rev.tolist()` здесь упала бы (6 значений на 7 строк), а на таблице без EKB-1 прошла бы молча и раздала бы выручку не тем кофейням: PRM-1 получила бы 181 365 ₽ из KZN-1.

## task: join | Справочник + показатели через join | base

Посчитайте по заказам таблицу `stats` с индексом `shop_id` и двумя столбцами: `revenue` (выручка) и `guests` (число разных гостей с картой). Присоедините её к справочнику методом `join` — результат `report`: все 7 кофеен справочника со столбцами справочника и показателями. Сохраните в `n_empty` число кофеен, у которых выручки нет.

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
assert len(r) == 7, f'В report {len(r)} строк, а кофеен в справочнике 7. Справочник — слева.'
assert {'city', 'seats', 'revenue', 'guests'} <= set(r.columns), f'Столбцы report: {list(r.columns)}. Нужны столбцы справочника и revenue, guests.'
_d = _pd.read_csv('orders_3m.csv')
_g = _d.groupby('shop_id')['client_id'].nunique().to_dict()
_row = r[r['shop_id'] == 'KZN-1'] if 'shop_id' in r.columns else r.loc[['KZN-1']]
assert int(_row['guests'].iloc[0]) == _g['KZN-1'], f'guests у KZN-1 — {_row["guests"].iloc[0]}, а нужно {_g["KZN-1"]}: разные гости — nunique.'
assert int(_row['revenue'].iloc[0]) == 181365, f'revenue у KZN-1 — {_row["revenue"].iloc[0]}.'
assert need('n_empty') == 1, f'n_empty = {need("n_empty")}. Посчитайте пустые значения revenue в report.'
assert calls('join'), 'Соедините таблицы методом join.'
```

### hint
Сначала `groupby("shop_id").agg(...)` с двумя именованными агрегатами — ключ окажется в индексе. Потом `join`: у справочника ключ — столбец, поэтому его называют в `on`.

### hint
`stats = df.groupby("shop_id").agg(revenue=("amount", "sum"), guests=("client_id", "nunique"))`, затем `shops.join(stats, on="shop_id")`. Пустые — `report["revenue"].isna().sum()`.

### hint
```python
stats = df.groupby("shop_id").agg(revenue=(..., "sum"), guests=(..., "nunique"))
report = shops.join(stats, on=...)
n_empty = int(report["revenue"].isna().sum())
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
stats = df.groupby("shop_id").agg(revenue=("amount", "sum"), guests=("client_id", "nunique"))
report = shops.join(stats, on="shop_id")
n_empty = int(report["revenue"].isna().sum())
```

### explain
Выручки нет только у EKB-1 — она открывается 15 октября, и в выгрузке её заказов нет. `join` по умолчанию — LEFT, поэтому справочник слева сохранил все 7 кофеен. Если бы вы написали `shops.join(stats)` без `on`, pandas стал бы искать пары между номерами строк 0…6 и кодами кофеен — ни одной пары, и все показатели стали бы `NaN`: тот же тихий JOIN, что в разделе выше.

## task: key-type | Ключ разного типа | plus

Бонусы гостей пришли из кассы, где номер гостя — число, а визиты — из приложения, где номер — текст из четырёх цифр с ведущими нулями. Соберите `full` — все строки `visits` и бонус к каждой (LEFT JOIN по гостю) — и защитите соединение проверкой `validate="one_to_one"`. Сохраните в `matched` число гостей из `visits`, у которых бонус нашёлся.

### starter
```python
import pandas as pd
visits = pd.DataFrame({"guest": ["0101", "0102", "0103", "0104", "0105"],
                       "visits": [5, 2, 7, 1, 3]})
bonus = pd.DataFrame({"guest": [101, 102, 104, 106],
                      "bonus": [150, 0, 300, 50]})

```

### check
```python
import pandas as _pd
f = need('full', _pd.DataFrame)
assert len(f) == 5, f'В full {len(f)} строк, а в visits 5. Нужен LEFT JOIN: visits слева.'
assert 'bonus' in f.columns and 'visits' in f.columns, f'Столбцы full: {list(f.columns)}.'
_b = f['bonus'].tolist()
assert sum(_pd.notna(x) for x in _b) > 0, 'Ни один бонус не нашёлся. Ключи сравнимы по типу, но записаны по-разному: «0101» и «101». Добавьте ведущие нули (zfill) или приведите обе стороны к числу.'
_want = [150, 0, None, 300, None]
for _i, (_g, _w) in enumerate(zip(_b, _want)):
    assert (_w is None and _pd.isna(_g)) or (_w is not None and _g == _w), f'Строка {_i}: бонус {_g}, а нужно {"NaN" if _w is None else _w}. Проверьте, что строки full идут в порядке visits.'
assert need('matched') == 3, f'matched = {need("matched")}. Посчитайте непустые бонусы в full.'
assert 'validate' in _code and 'one_to_one' in _code, 'Добавьте в merge проверку validate="one_to_one".'
```

### hint
Сначала попробуйте соединить как есть — сообщение об ошибке скажет, что не так с типами. После приведения к тексту проверьте, сколько пар нашлось: `101` станет `"101"`, а в `visits` — `"0101"`.

### hint
Два рабочих пути: `bonus["guest"].astype(str).str.zfill(4)` — число в текст с ведущими нулями; или `visits["guest"].astype(int)` — текст в число. Потом `visits.merge(bonus, on="guest", how="left", validate="one_to_one")`.

### hint
```python
bonus["guest"] = bonus["guest"].astype(str).str.zfill(...)
full = visits.merge(bonus, on="guest", how=..., validate=...)
matched = int(full["bonus"].notna().sum())
```

### solution
```python
import pandas as pd
visits = pd.DataFrame({"guest": ["0101", "0102", "0103", "0104", "0105"],
                       "visits": [5, 2, 7, 1, 3]})
bonus = pd.DataFrame({"guest": [101, 102, 104, 106],
                      "bonus": [150, 0, 300, 50]})
bonus["guest"] = bonus["guest"].astype(str).str.zfill(4)
full = visits.merge(bonus, on="guest", how="left", validate="one_to_one")
matched = int(full["bonus"].notna().sum())
```

### explain
Бонус нашёлся у трёх гостей из пяти: 0101, 0102 и 0104; у 0103 и 0105 бонусов нет, а гость 106 есть только в кассе и в LEFT JOIN не попал. Обратите внимание на гостя 0102: бонус у него 0, а не `NaN` — «ноль бонусов» и «нет данных» различаются, и `notna()` это учитывает. Если бы вы ограничились `astype(str)`, ошибки бы не было, но и пар тоже: `"101"` ≠ `"0101"` — `matched` оказался бы 0. Поэтому после любого «ремонта» ключа считайте, сколько пар нашлось.

## task: anti | Кофейни без заказов | base

Получите `no_orders` — **список** `shop_id` кофеен из справочника, у которых нет ни одного заказа.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")

```

### check
```python
import pandas as _pd
s = _pd.read_csv('shops.csv'); d = _pd.read_csv('orders_3m.csv')
want = s[~s['shop_id'].isin(d['shop_id'])]['shop_id'].tolist()
assert need('no_orders') == want, f'no_orders = {need("no_orders")}, а нужно {want}.'
```

### hint
Anti join: из справочника берём те кофейни, чьих кодов **нет** среди заказов — `isin` и `~`.

### hint
`shops[~shops["shop_id"].isin(df["shop_id"])]["shop_id"].tolist()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
shops = pd.read_csv("shops.csv")
no_orders = shops[~shops["shop_id"].isin(df["shop_id"])]["shop_id"].tolist()
```

### explain
Без заказов — EKB-1: кофейня открылась 15 октября 2026 года, но в выгрузке её заказов нет. Anti join — проверка, которая находит «потеряшек»: либо кофейня ещё не работает, либо её данные не доехали.

## task: concat | Склеить месяцы | plus

Выгрузку разрезали на три таблицы по месяцам. Склейте их обратно в `all3` с новой нумерацией строк и проверьте, что строк столько же, сколько в исходной таблице: сохраните `same = True/False`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
sep_df = df[df["datetime"].str.startswith("2026-09")]
oct_df = df[df["datetime"].str.startswith("2026-10")]
nov_df = df[df["datetime"].str.startswith("2026-11")]

```

### check
```python
import pandas as _pd
a = need('all3', _pd.DataFrame)
assert len(a) == len(df), f'В all3 {len(a)} строк, а должно быть {len(df)}.'
assert list(a.index) == list(range(len(a))), 'Нумерация строк должна быть новой: ignore_index=True.'
assert need('same') is True or need('same') == True, 'same должно быть True.'
```

### hint
Месяцы режутся по началу текста даты: `df["datetime"].str.startswith("2026-09")`.

### hint
`pd.concat([sep_df, oct_df, nov_df], ignore_index=True)`; `same = len(all3) == len(df)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
sep_df = df[df["datetime"].str.startswith("2026-09")]
oct_df = df[df["datetime"].str.startswith("2026-10")]
nov_df = df[df["datetime"].str.startswith("2026-11")]
all3 = pd.concat([sep_df, oct_df, nov_df], ignore_index=True)
same = len(all3) == len(df)
```

### explain
Три месяца склеились обратно в те же 2 089 строк. Если бы `same` оказалось `False`, значит, какие-то заказы не попали ни в один месяц — например, с датой в другом формате.
