---
title: "Группировки: GROUP BY и HAVING"
lead: "Самая частая операция аналитика — посчитать что-то по группам. В главе 1 для этого был словарь-накопитель, в pandas — groupby. Плюс доли и одна ловушка, на которой ошибаются даже опытные. Метрики на гостя — в следующем уроке, сводные таблицы для руководителя — после него."
files: [orders_3m.csv]
recap:
  - "`df.groupby(\"shop_id\")[\"amount\"].sum()` — сумма по группам; ещё `mean`, `count`, `size`, `nunique`, `median`, `max`."
  - "Несколько агрегатов с именами: `.agg(revenue=(\"amount\", \"sum\"), orders=(\"order_id\", \"count\"))`."
  - "`as_index=False` или `.reset_index()` — ключи группировки становятся обычными столбцами."
  - "HAVING — фильтр уже по результату группировки: `t[t[\"orders\"] > 100]`."
  - "`size()` считает строки, `count()` — непустые значения. `nunique()` — разные значения (COUNT DISTINCT)."
  - "Среднее средних ≠ общее среднее: считайте средние из сумм и количеств."
---

## groupby: разделить, посчитать, собрать

Зачем: «какая кофейня приносит больше», «какой канал растёт», «сколько гостей у каждой точки» — почти любой вопрос руководителя звучит как «посчитай по группам». Начнём с выручки по кофейням:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df.groupby("shop_id")["amount"].sum()
```

Читается так: «сгруппировать `df` по `shop_id`, взять столбец `amount`, в каждой группе посчитать сумму». Результат — Series, у которой индекс — значения ключа группировки.

Всё, что мы делали в уроке «Словари — GROUP BY своими руками» главы 1 словарём-накопителем, — здесь одна строка. Внутри pandas делает то же самое: делит таблицу на группы, считает агрегат в каждой и собирает результаты вместе.

::: sql
`df.groupby("shop_id")["amount"].sum()` — `SELECT shop_id, SUM(amount) FROM orders GROUP BY shop_id`.
:::

Агрегаты — те же, что у столбца: `sum`, `mean`, `median`, `min`, `max`, `count`, `nunique`. И отдельно `size()` — число строк в группе:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

print(df.groupby("channel").size())
print(df.groupby("shop_id")["client_id"].nunique())
```

Группировать можно по нескольким столбцам — списком:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

df.groupby(["shop_id", "channel"])["amount"].sum().head(6)
```

Индекс у такого результата — **пары** «кофейня, канал». Поэтому одно значение достают тоже парой — кортежем в квадратных скобках:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

by_pair = df.groupby(["shop_id", "channel"])["amount"].sum()
print(by_pair[("KZN-1", "доставка")])   # выручка доставки KZN-1 — одно число
```

Что здесь происходит:

- `by_pair[("KZN-1", "доставка")]` — сначала значение первого ключа, потом второго, в том же порядке, что в `groupby`. Результат — одно число, 32 587.
- Если вы сделали группировку с `as_index=False` и отобрали строку маской, получится не число, а таблица из одной строки. Одно значение из её столбца — `.iloc[0]`: `t.loc[маска, "amount"].iloc[0]`.

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"g": ["a", "b", "a"], "v": [1, 2, 3]})
print(df.groupby("g")["v"].sum().tolist())
```

- `[1, 2, 3]`
- [x] `[4, 2]`
- `[2, 4]`

Почему: в группе «a» значения 1 и 3 (сумма 4), в группе «b» — 2. Группы упорядочены по ключу: сначала «a», потом «b».
:::

### Разберём вместе: группировка шести заказов руками

| заказ | кофейня | сумма |
|---|---|---|
| 1 | PRM-1 | 300 |
| 2 | KZN-1 | 250 |
| 3 | PRM-1 | 400 |
| 4 | KZN-1 | 350 |
| 5 | PRM-1 | 200 |
| 6 | UFA-1 | 500 |

1. **Разделить** по `shop_id`: PRM-1 — заказы 1, 3, 5; KZN-1 — 2, 4; UFA-1 — 6.
2. **Посчитать** в каждой группе: PRM-1 — 300 + 400 + 200 = 900; KZN-1 — 600; UFA-1 — 500.
3. **Собрать** в одну Series с индексом-кофейней: KZN-1 600, PRM-1 900, UFA-1 500 (индекс по алфавиту).

::: figure groupby
Пример из «Разберём вместе»: шесть заказов делятся на группы по кофейне, в каждой считается сумма, итог собирается в одну Series.
:::

Средний чек — тот же путь, только на шаге 2 `mean`: PRM-1 — 300, KZN-1 — 300, UFA-1 — 500. По выручке лидирует PRM-1, по среднему чеку — UFA-1 с единственным заказом. Поэтому рядом со средним всегда показывают размер группы.

```python
import pandas as pd
t = pd.DataFrame({"shop_id": ["PRM-1", "KZN-1", "PRM-1", "KZN-1", "PRM-1", "UFA-1"],
                  "amount": [300, 250, 400, 350, 200, 500]})
print(t.groupby("shop_id")["amount"].agg(["sum", "mean", "size"]))
```

{{practice: by-shop, by-channel, two-keys}}

## agg: несколько агрегатов сразу

Отчёт обычно требует нескольких цифр по каждой группе. Для этого есть `agg` с **именованными агрегатами**: имя нового столбца = (какой столбец, какая функция).

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

shops = df.groupby("shop_id").agg(
    revenue=("amount", "sum"),
    orders=("order_id", "count"),
    avg_check=("amount", "mean"),
    clients=("client_id", "nunique"),
)
shops.round(1)
```

::: sql
Это ровно `SELECT shop_id, SUM(amount) AS revenue, COUNT(order_id) AS orders, AVG(amount) AS avg_check, COUNT(DISTINCT client_id) AS clients FROM orders GROUP BY shop_id`.
:::

### Ключи — обратно в столбцы

После `groupby` ключ уходит в индекс. Чтобы получилась обычная плоская таблица (например, для дальнейших фильтров или выгрузки), добавьте `.reset_index()` или сразу `as_index=False`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

t = df.groupby("drink", as_index=False).agg(
    orders=("order_id", "count"),
    revenue=("amount", "sum"),
)
t.sort_values("revenue", ascending=False).head()
```

{{practice: p-agg, shop-stats}}

## HAVING: фильтр по результату

В SQL условие на агрегат пишут в `HAVING`. В pandas всё проще: результат группировки — обычная таблица, и её фильтруют обычной маской:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

t = df.groupby("drink", as_index=False).agg(orders=("order_id", "count"))
t[t["orders"] > 200]
```

::: sql
`… GROUP BY drink HAVING COUNT(*) > 200`.
:::

Часто нужен не кусок таблицы, а просто **список названий** прошедших групп — например, чтобы вставить его в письмо. Где лежат названия, зависит от того, как вы группировали:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

cnt = df.groupby("drink").size()          # названия — в индексе
print(list(cnt[cnt > 200].index))

t = df.groupby("drink", as_index=False).agg(orders=("order_id", "count"))
print(t[t["orders"] > 200]["drink"].tolist())   # названия — в столбце drink
```

Что здесь происходит:

- `cnt[cnt > 200]` — Series, отфильтрованная маской; названия напитков у неё в **индексе**, поэтому `list(… .index)`.
- При `as_index=False` напиток — обычный столбец, и список берут из него: `["drink"].tolist()`.
- Сама отфильтрованная Series — не список: сравнить её со списком или проверить «одним значением» нельзя.

{{practice: having}}

## count и size — не одно и то же

`size()` считает строки в группе, `count()` — **непустые** значения в столбце. Разница проявляется на столбцах с пропусками:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

g = df.groupby("shop_id")
print(pd.DataFrame({"строк": g.size(), "с картой": g["client_id"].count()}))
```

::: figure count-size
Одна группа из четырёх заказов: `size` считает все строки, `count` — непустые значения, `nunique` — разные непустые.
:::

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"g": ["a", "a"], "c": ["x", None]})
print(df.groupby("g")["c"].count().tolist())
```

- `[2]`
- [x] `[1]`
- `[0]`

Почему: `count` не считает пустые значения (`None` превратился в `NaN`). Строк в группе две — это показал бы `size()`.
:::

А если пустое значение не в считаемом столбце, а в самом **ключе** группировки? Такие строки `groupby` по умолчанию просто не учитывает (параметр `dropna=True`): `df.groupby("client_id")` даст 260 групп — по одной на гостя с картой, а 842 заказа без карты в результат не попадут. Поэтому перед группировкой по `client_id` отдельный фильтр `notna()` не обязателен — но и не вреден: так в коде видно, что заказы без карты отброшены намеренно.

::: quiz
Нужно узнать, сколько **разных** гостей с картой лояльности заходили в каждую кофейню. Какой агрегат по `client_id` выбрать?

- [x] `nunique()` — число разных значений в группе
  > Это `COUNT(DISTINCT client_id)`: постоянный гость с десятью заказами посчитается один раз, а пустые значения не учитываются.
- [ ] `count()` — он ведь не считает пустые значения
  > Пустые он и правда пропускает, но гость с десятью заказами даст 10. Получится число заказов с картой, а не число гостей.
- [ ] `size()` — число строк в группе
  > `size()` считает все заказы, включая заказы без карты, и повторы одного гостя.
:::

## Доли внутри итога

Часто нужны не абсолютные числа, а доли. У `value_counts` есть `normalize=True`, а для сумм долю считают делением на общий итог:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

print(df["channel"].value_counts(normalize=True).round(3))

by_drink = df.groupby("drink")["amount"].sum()
(by_drink / by_drink.sum() * 100).round(1).sort_values(ascending=False).head()
```

{{practice: shares, pareto}}

## Ловушка: среднее средних

Каков средний чек сети? Соблазнительно посчитать средний чек каждой кофейни и усреднить. Но это неправильно: маленькая кофейня с сотней заказов получит тот же вес, что и большая с пятьюстами.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

per_shop = df.groupby("shop_id")["amount"].mean()
print("среднее средних:", round(per_shop.mean(), 2))
print("настоящий средний чек:", round(df["amount"].mean(), 2))
```

Разница здесь небольшая, но на реальных данных бывает огромной. Правило: средние по группам **не усредняют**. Нужное среднее считают из исходных строк или как сумма сумм, делённая на сумму количеств — как в уроке «Таблица из списков» главы 1.

::: warn Типичные ошибки
- **Средний чек без числа заказов.** «UFA-1 — лучший средний чек» по одному заказу ничего не значит.
- **`count` вместо `size`.** `count` не считает пустые значения выбранного столбца; число строк группы — `size`.
- **Среднее средних.** Среднее из средних чеков кофеен ≠ средний чек сети, если кофейни разного размера.
- **Фильтр до или после.** `WHERE` — маска до `groupby`, `HAVING` — маска по результату после.
:::

::: quiz
В одной кофейне 100 заказов со средним чеком 300 ₽, в другой — 10 заказов со средним 600 ₽. Каков средний чек сети?

- [x] ≈ 327 ₽: (100·300 + 10·600) / 110 = 327.27
  > Средний чек сети — вся выручка, делённая на все заказы. Большая кофейня весит больше.
- [ ] 450 ₽: (300 + 600) / 2
  > Это «среднее средних»: маленькая кофейня с 10 заказами получила тот же вес, что большая.
- [ ] 600 ₽ — берём лучший
  > Максимум ничего не говорит о сети в целом.
- [ ] Посчитать нельзя без исходных заказов
  > Можно: зная число заказов и средний чек, восстанавливаем выручку каждой кофейни.
:::

::: figure avg-of-avg
Пример из вопроса выше: две кофейни с 100 и 10 заказами. Ширина полосы — вес кофейни в среднем.
:::

{{practice: avg-of-avg}}

## Практика

## task: by-shop | Выручка по кофейням | warmup

Сохраните в `by_shop` выручку по кофейням (Series: `shop_id` → сумма).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv').groupby('shop_id')['amount'].sum()
b = need('by_shop')
assert isinstance(b, _pd.Series), 'by_shop должен быть Series — один столбец после groupby.'
assert b.to_dict() == want.to_dict(), f'by_shop = {b.to_dict()}.'
```

### hint
Схема: по чему группируем → какой столбец считаем → какой агрегат.

### hint
`df.groupby("shop_id")["amount"].sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_shop = df.groupby("shop_id")["amount"].sum()
```

## task: by-channel | Заказы по каналам | warmup

Сохраните в `channels` **словарь** «канал → число заказов», посчитанный через `groupby(...).size()`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = {k: int(v) for k, v in _pd.read_csv('orders_3m.csv').groupby('channel').size().items()}
got = {k: int(v) for k, v in dict(need('channels')).items()}
assert got == want, f'channels = {got}.'
assert calls('size'), 'Используйте size().'
```

### hint
`size()` считает строки в каждой группе; результат — Series, его превращаем в словарь.

### hint
`dict(df.groupby("channel").size())`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
channels = dict(df.groupby("channel").size())
```

## task: p-agg | Соберите отчёт по кофейням | warmup

Соберите программу, которая выводит номер кофейни с наибольшим средним чеком.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
t = df.groupby("shop_id").agg(avg_check=("amount", "mean"))
best = t["avg_check"].idxmax()
print(best)
```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv').groupby('shop_id')['amount'].mean().idxmax()
assert _lines == [want], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
`idxmax()` возвращает индекс (здесь — номер кофейни) максимального значения.

### hint
Средний чек по кофейням — `df.groupby("shop_id")["amount"].mean()`; печатаем его `idxmax()`.

## task: shop-stats | Отчёт по кофейням | base

Соберите таблицу `stats`, где строки — кофейни, а столбцы — `revenue` (сумма), `orders` (число заказов) и `avg_check` (средний чек, округлённый до одного знака).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
s = need('stats', _pd.DataFrame)
if 'shop_id' in s.columns:
    s = s.set_index('shop_id')
assert list(s.columns) == ['revenue', 'orders', 'avg_check'], f'Столбцы: {list(s.columns)}.'
g = d.groupby('shop_id')
assert s['revenue'].to_dict() == g['amount'].sum().to_dict(), 'revenue не совпадает.'
assert s['orders'].to_dict() == g.size().to_dict(), 'orders не совпадает.'
assert (s['avg_check'] - g['amount'].mean().round(1)).abs().max() < 1e-9, 'avg_check не совпадает — округлили до одного знака?'
```

### hint
Именованные агрегаты: `новое_имя=("столбец", "функция")`.

### hint
`df.groupby("shop_id").agg(revenue=("amount", "sum"), orders=("order_id", "count"), avg_check=("amount", "mean"))`, затем округлите столбец `avg_check`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
stats = df.groupby("shop_id").agg(
    revenue=("amount", "sum"),
    orders=("order_id", "count"),
    avg_check=("amount", "mean"),
)
stats["avg_check"] = stats["avg_check"].round(1)
```

### explain
Две большие кофейни, PRM-1 и KZN-1, делают по 180 тыс. ₽ — вдвое больше остальных. Средний чек при этом почти одинаковый (328–355 ₽): разница в выручке — от числа заказов, а не от чека.

## task: having | Популярные напитки | base

Получите `popular` — **отсортированный по алфавиту список** напитков, которые заказывали больше 200 раз.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
vc = _pd.read_csv('orders_3m.csv').groupby('drink').size()
want = sorted(vc[vc > 200].index)
_p = need('popular')
assert not isinstance(_p, (_pd.Series, _pd.DataFrame)), f'В popular лежит {type(_p).__name__} — отфильтрованный результат группировки, а нужен список названий. Названия — в индексе (list(… .index)) или в столбце drink при as_index=False.'
assert isinstance(_p, list), f'В popular лежит {type(_p).__name__}, а нужен обычный список: sorted(...) или list(...).'
assert sorted(_p) == want, f'popular = {_p}, а должны быть другие напитки. Условие — больше 200 заказов.'
assert _p == want, 'Напитки верные, но список не отсортирован по алфавиту: sorted(...).'
```

### hint
Это `HAVING`: сначала считаем по группам, потом фильтруем результат.

### hint
Посчитайте `size()` по напиткам и отфильтруйте результат маской `> 200`. Названия напитков у результата — в индексе: `sorted(t.index)` даст отсортированный список.

### hint
```python
cnt = df.groupby("drink").size()
popular = sorted(cnt[cnt > ...].index)
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
cnt = df.groupby("drink").size()
popular = sorted(cnt[cnt > 200].index)
```

### explain
Больше 200 раз заказывали четыре напитка: американо, капучино, латте и флэт уайт. Фильтр применяется к результату группировки — как `HAVING COUNT(*) > 200` в SQL.

## task: two-keys | Кофейня × канал | base

Посчитайте выручку по парам «кофейня, канал» в `by_pair` и сохраните в `kzn1_delivery` выручку доставки кофейни `KZN-1`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
import numbers as _num
want = d[(d['shop_id'] == 'KZN-1') & (d['channel'] == 'доставка')]['amount'].sum()
_k = need('kzn1_delivery')
if isinstance(_k, _pd.DataFrame):
    assert False, 'В kzn1_delivery лежит таблица (DataFrame), а нужно одно число. Возьмите значение по паре ключей: by_pair[("KZN-1", "доставка")]; из строки таблицы — столбец и .iloc[0].'
if isinstance(_k, _pd.Series):
    assert len(_k) == 1, f'В kzn1_delivery лежит Series из {len(_k)} значений, а нужно одно число — выручка доставки KZN-1.'
    assert False, 'В kzn1_delivery лежит Series из одной строки, а нужно само число. Возьмите его через .iloc[0] — или сразу by_pair[("KZN-1", "доставка")].'
assert isinstance(_k, _num.Number), f'В kzn1_delivery лежит {type(_k).__name__} ({_k!r}), а нужно число.'
assert _k == want, f'kzn1_delivery = {_k}, а нужно {want}.'
assert 'groupby' in _code, 'Посчитайте через groupby по двум столбцам.'
```

### hint
Два ключа группировки — список: `groupby(["shop_id", "channel"])`.

### hint
`by_pair = df.groupby(["shop_id", "channel"])["amount"].sum()`. Значение по паре ключей — `by_pair[("KZN-1", "доставка")]`.

### hint
```python
by_pair = df.groupby([..., ...])["amount"].sum()
kzn1_delivery = by_pair[(..., ...)]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_pair = df.groupby(["shop_id", "channel"])["amount"].sum()
kzn1_delivery = by_pair[("KZN-1", "доставка")]
```

### explain
Доставка в KZN-1 — 32 587 ₽. Группировка по двум ключам даёт Series с двухуровневым индексом, и обращаться к значению нужно парой `(кофейня, канал)`.

## task: shares | Доли напитков | base

Посчитайте `share` — долю каждого напитка в выручке в процентах (с одним знаком), отсортированную по убыванию, и сохраните в `top3` **список** трёх первых названий.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
b = _pd.read_csv('orders_3m.csv').groupby('drink')['amount'].sum()
want = (b / b.sum() * 100).round(1).sort_values(ascending=False)
assert need('top3') == list(want.index[:3]), f'top3 = {need("top3")}, а нужно {list(want.index[:3])}.'
s = need('share')
assert abs(float(s.iloc[0]) - want.iloc[0]) < 1e-9, f'Первое значение share = {s.iloc[0]}, а нужно {want.iloc[0]}.'
```

### hint
`by_drink = df.groupby("drink")["amount"].sum()`, доля — `by_drink / by_drink.sum() * 100`.

### hint
После `sort_values(ascending=False)` первые три названия — `list(share.index[:3])`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_drink = df.groupby("drink")["amount"].sum()
share = (by_drink / by_drink.sum() * 100).round(1).sort_values(ascending=False)
top3 = list(share.index[:3])
```

### explain
Доли складываются в 100 %, поэтому их удобно сравнивать между периодами: «латте — 17.6 % выручки» понятно без знания общей суммы.

## task: avg-of-avg | Средний чек гостя | plus

Сравните две цифры по заказам с картой лояльности:

- `client_avg` — среднее из средних чеков гостей (сначала средний чек каждого гостя, потом среднее этих значений);
- `order_avg` — обычный средний чек по всем заказам с картой.

Округлите обе до одного знака.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
c = d[d['client_id'].notna()]
assert close(need('client_avg'), round(c.groupby('client_id')['amount'].mean().mean(), 1)), f'client_avg = {need("client_avg")}.'
assert close(need('order_avg'), round(c['amount'].mean(), 1)), f'order_avg = {need("order_avg")}.'
```

### hint
Сначала отберите строки с непустым `client_id`. Средний чек гостя — `groupby("client_id")["amount"].mean()`.

### hint
`client_avg` — `.mean()` от этой Series; `order_avg` — просто `c["amount"].mean()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
c = df[df["client_id"].notna()]
client_avg = round(c.groupby("client_id")["amount"].mean().mean(), 1)
order_avg = round(c["amount"].mean(), 1)
```

### explain
Это разные вопросы: «какой чек у типичного гостя» и «какой чек у типичного заказа». Гости, которые заходят часто, сильнее влияют на второе число. Выбирайте метрику под вопрос и подписывайте, что именно посчитано.

## task: pareto | Правило 80/20 | star

Сколько напитков приносят 80 % выручки? Отсортируйте напитки по выручке по убыванию, посчитайте накопленную долю и найдите `n80` — минимальное число напитков, чья суммарная доля достигает 80 %.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
b = _pd.read_csv('orders_3m.csv').groupby('drink')['amount'].sum().sort_values(ascending=False)
cum = b.cumsum() / b.sum()
want = int((cum < 0.8).sum() + 1)
assert need('n80') != want - 1, f'n80 = {need("n80")} — на один меньше. Похоже, вы посчитали напитки, у которых доля ещё не дошла до 80 %. Добавьте и тот напиток, на котором порог 80 % достигнут.'
assert need('n80') == want, f'n80 = {need("n80")}, а нужно {want}.'
```

### hint
Накопленная сумма — метод `cumsum()`. Доля — накопленная сумма, делённая на общую выручку.

### hint
Число напитков, у которых накопленная доля ещё **меньше** 0.8, плюс один — тот, на котором порог достигнут.

### hint
```python
rev = df.groupby("drink")["amount"].sum().sort_values(ascending=False)
cum_share = rev.cumsum() / rev....()
n80 = int((cum_share < ...).sum() + 1)
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum().sort_values(ascending=False)
cum_share = rev.cumsum() / rev.sum()
n80 = int((cum_share < 0.8).sum() + 1)
```

### explain
Это анализ Парето, частый вопрос бизнеса: какие позиции дают основную выручку и на чём сосредоточиться. `cumsum()` — тот самый накопительный итог из урока «Цикл for» главы 1.
