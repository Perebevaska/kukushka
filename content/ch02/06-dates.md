---
title: Даты и время
lead: "Пока дата была текстом, мы резали её срезами. Превращаем её в настоящую дату — и получаем месяцы, дни недели, часы, фильтры по периодам, недельные итоги и разницу между датами."
files: [orders_3m.csv]
recap:
  - "`pd.to_datetime(df[\"datetime\"])` или `pd.read_csv(..., parse_dates=[\"datetime\"])` — текст в дату (`datetime64`)."
  - "`.dt.year`, `.dt.month`, `.dt.day`, `.dt.hour`, `.dt.weekday` (0 — понедельник), `.dt.date`, `.dt.to_period(\"M\")` — части даты."
  - "Фильтр по периоду: `df[(df[\"datetime\"] >= \"2026-10-01\") & (df[\"datetime\"] < \"2026-11-01\")]` — правая граница не включается."
  - "Итоги по неделям или месяцам: `df.resample(\"W\", on=\"datetime\")[\"amount\"].sum()`; частоты `\"D\"`, `\"W\"`, `\"ME\"` (конец месяца), `\"h\"`."
  - "`dt.floor(\"30min\")` — к началу интервала (в какой получас попал заказ), `dt.round` — к ближайшей отметке, `dt.ceil` — вверх. Дата сохраняется."
  - "Разница дат — `Timedelta`; `.dt.days` — в днях. `pct_change()` — изменение к предыдущему периоду."
---

## Текст → дата

Зачем: пока дата — текст, «выручка за неделю», «заказы по выходным» или «сколько дней гость с нами» решаются только срезами строк, и то не все. Настоящая дата умеет сравниваться, вычитаться и делиться на периоды. Сейчас `datetime` — это текст:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
print(df["datetime"].dtype, df["datetime"].iloc[0])
```

`pd.to_datetime` превращает его в настоящую дату. Можно и сразу при загрузке — параметром `parse_dates`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
print(df["datetime"].dtype)
df["datetime"].head(3)
```

Тип `datetime64` — это дата и время, с которыми pandas умеет считать: сравнивать, вычитать, группировать по периодам.

::: sql
`pd.to_datetime(...)` — как `CAST(datetime AS timestamp)`. Формат `ГГГГ-ММ-ДД чч:мм` pandas узнаёт сам; для других форматов есть параметр `format`, например `format="%d.%m.%Y"` для «15.09.2026».
:::

{{practice: to-dt}}

## Части даты: .dt

У столбца-даты есть набор свойств после `.dt` — как `.str` у текстовых:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

parts = pd.DataFrame({
    "дата": df["datetime"].dt.date,
    "месяц": df["datetime"].dt.month,
    "день недели": df["datetime"].dt.weekday,   # 0 — понедельник, 6 — воскресенье
    "час": df["datetime"].dt.hour,
})
parts.head()
```

Теперь выручка по месяцам или часам — обычный `groupby` по такому столбцу:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

df["month"] = df["datetime"].dt.to_period("M")
df.groupby("month")["amount"].sum()
```

`to_period("M")` превращает дату в «месяц» (`2026-09`) — удобный ключ для группировки и подписей.

Когда по такому ключу посчитана группировка — например, заказы по часам или выручка по дням, — часто нужен не максимум, а **где** он: в каком часу, в какой день. Это `idxmax()`: он возвращает подпись строки с наибольшим значением — как `index[0]` после сортировки по убыванию. `idxmin()` — то же для наименьшего.

Отбросить время можно двумя способами. `dt.date` даёт обычные даты Python (без времени, это уже не `datetime64`). `dt.normalize()` оставляет тип `datetime64`, но ставит время 00:00: `2026-09-01 10:31` → `2026-09-01 00:00`. Второй удобен, если дальше нужны `.dt`, `resample` или сравнение с другими датами.

::: sql
`dt.month` — `EXTRACT(MONTH FROM datetime)`, `dt.to_period("M")` — `DATE_TRUNC('month', datetime)`, `dt.weekday` — `EXTRACT(DOW …)` (только нумерация дней недели другая).
:::

::: predict
```python static
import pandas as pd
print(pd.Timestamp("2026-10-05").weekday())
```

- `5`
- [x] `0`
- `1`

Почему: 5 октября 2026 года — понедельник, а `weekday()` нумерует дни с нуля, начиная с понедельника. Число месяца тут ни при чём.
:::

{{practice: months, p-month, weekend, hours}}

## Фильтр по периоду

Даты можно сравнивать с текстом в формате `ГГГГ-ММ-ДД` — pandas сам поймёт:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

october = df[(df["datetime"] >= "2026-10-01") & (df["datetime"] < "2026-11-01")]
print(len(october), october["amount"].sum())
```

::: warn
Для периода берите правую границу **строго меньше следующего дня**: `< "2026-11-01"`. Условие `<= "2026-10-31"` потеряет заказы 31 октября после полуночи — дата без времени означает 00:00.
:::

### Разберём вместе: куда пропал вечер 15 октября

Нужна выручка с 1 по 15 октября включительно. Первая мысль — `df["datetime"] <= "2026-10-15"`. Посмотрим, что происходит с тремя заказами 15-го числа:

| заказ | время | `<= "2026-10-15"` | `< "2026-10-16"` |
|---|---|---|---|
| A | 2026-10-14 18:05 | True | True |
| B | 2026-10-15 09:12 | **False** | True |
| C | 2026-10-15 20:40 | **False** | True |

1. Строка «2026-10-15» превращается в момент **2026-10-15 00:00** — полночь в начале дня.
2. Заказ в 09:12 15-го числа позже этой полуночи — и условие `<=` его отбрасывает.
3. Правильная граница — «меньше начала следующего дня»: `< "2026-10-16"`.

::: figure date-bound
Три заказа из таблицы на оси времени. Граница `<= "2026-10-15"` стоит в полночь в начале 15-го, граница `< "2026-10-16"` — в полночь в конце.
:::

::: tip Аналогия
Объявление «акция до 15 октября» люди читают как «весь день 15-го включительно», а pandas — как «до полуночи, с которой 15-е начинается». Надёжнее писать как в расписании поездов: «до 00:00 16 октября» — `< "2026-10-16"`. Только в расписании полночь пишут явно, а в строке «2026-10-15» время 00:00 скрыто.
:::

На наших данных разница — 113 790 ₽ против 107 355 ₽: с `<=` из отчёта пропал весь день 15 октября, **6 435 ₽**.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
a = df[(df["datetime"] >= "2026-10-01") & (df["datetime"] <= "2026-10-15")]["amount"].sum()
b = df[(df["datetime"] >= "2026-10-01") & (df["datetime"] < "2026-10-16")]["amount"].sum()
print(a, b, b - a)
```

Что получилось: у даты со временем «включительно» по последнему дню почти всегда пишется как «строго меньше следующего дня». Это та же ловушка, что в SQL с `BETWEEN '2026-10-01' AND '2026-10-15'` на столбце `timestamp`.

::: quiz
`datetime` — дата со временем. Почему фильтр `df[df["datetime"] <= "2026-10-15"]` теряет заказы 15 октября?

- [x] Строка «2026-10-15» превращается в полночь 15 октября, и все заказы позже 00:00 не проходят
  > Граница — момент времени, а не целый день. Надёжный способ — строгое «меньше» со следующего дня: `< "2026-10-16"`.
- [ ] Сравнивать даты со строкой нельзя
  > Можно: pandas сам превращает строку в дату. Подвох в том, во что именно она превращается.
- [ ] `<=` для дат работает как `<`
  > Работает как обычное «меньше или равно», просто равны полуночи только заказы ровно в 00:00.
- [ ] Нужно сначала отсортировать таблицу по дате
  > Порядок строк на фильтр не влияет.
:::

{{practice: period}}

## Недели и месяцы: resample

Для итогов по равным интервалам времени есть `resample`: он режет время на куски — дни, недели, месяцы — и считает агрегат в каждом:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

weekly = df.resample("W", on="datetime")["amount"].sum()
weekly.head()
```

Частоты: `"D"` — день, `"W"` — неделя (по воскресеньям), `"ME"` — месяц (метка — последний день), `"h"` — час.

Индекс результата — метки интервалов, каждая из них — одиночная дата `Timestamp`. Чтобы получить из неё дату без времени, у одной метки вызывают `.date()` — то же, что `.dt.date` у целого столбца: `weekly.idxmax().date()` — день, которым закончилась лучшая неделя.

В отличие от `groupby` по части даты, `resample` не пропускает пустые интервалы: если в какой-то день заказов не было, он всё равно попадёт в результат с нулём. Для графиков и временных рядов это важно.

::: figure resample-gaps
Условные заказы за пять дней, 3 октября — ни одного. `groupby` по дате просто не знает об этом дне, `resample` показывает его нулём.
:::

::: tip
В старых материалах встречаются частоты `"M"` и `"H"` — в pandas 3 они переименованы в `"ME"` и `"h"`. Если увидите ошибку про неизвестную частоту, дело, скорее всего, в этом.
:::

::: quiz
Строите линейный график выручки по дням. Почему для него `resample("D", ...)` надёжнее, чем `groupby` по `dt.date`?

- [x] `resample` оставляет дни без заказов с нулём, а `groupby` их пропускает — и линия молча «перепрыгнет» через провал
  > `groupby` создаёт группы только из того, что есть в данных. Для временного ряда пустой день — тоже информация.
- [ ] `resample` считает быстрее, а результат тот же
  > Результаты различаются как раз в днях без заказов: у `groupby` таких строк нет вовсе.
- [ ] `groupby` не умеет группировать по датам, только по тексту
  > Умеет: `groupby(df["datetime"].dt.date)` — обычная группировка по значению.
- [ ] `groupby` по `dt.date` теряет заказы после полуночи
  > `dt.date` отбрасывает только время, заказ остаётся в своём дне. Это ловушка фильтра `<=`, а не группировки.
:::

{{practice: weekly, best-day}}

## Округление времени: dt.floor и dt.round

`dt.hour` отвечает на вопрос «в каком часу», но теряет дату и не умеет «по 15 минут». А бариста планирует смены получасами: «сколько заказов приходится на 9:00–9:30». Для этого время **округляют до интервала**: каждый заказ приписывают к началу своего получаса — так же, как `to_period("M")` приписывает дату к месяцу.

::: tip Аналогия
Парковка с тарификацией по 15 минут: заехали в 10:07 — для кассы это «интервал с 10:00». `floor` — «к началу интервала», как на этой парковке; `round` — «к ближайшей отметке», как округление цены до рубля.
:::

**Пример руками.** Четыре заказа: 08:07, 08:29, 08:31, 08:52. Интервал — 30 минут, отметки 08:00, 08:30, 09:00.

| время | `floor("30min")` — вниз | `round("30min")` — к ближайшей | `ceil("30min")` — вверх |
|---|---|---|---|
| 08:07 | 08:00 | 08:00 (до 08:00 — 7 мин, до 08:30 — 23) | 08:30 |
| 08:29 | 08:00 | 08:30 (1 мин против 29) | 08:30 |
| 08:31 | 08:30 | 08:30 | 09:00 |
| 08:52 | 08:30 | 09:00 | 09:00 |

Для «в какой получас пришёл заказ» нужен `floor`: 08:29 — это ещё получас 08:00–08:30, хотя `round` отнёс бы его к 08:30.

::: figure time-floor
Четыре заказа из таблицы. Сверху цветные полосы — получасы, `floor` ведёт к началу своего. Снизу полосы — зоны «ближе к отметке», `round` ведёт к ближайшей.
:::

```python
import pandas as pd
t = pd.Series(pd.to_datetime(["2026-10-05 08:07", "2026-10-05 08:29",
                              "2026-10-05 08:31", "2026-10-05 08:52"]))
pd.DataFrame({
    "время": t.dt.strftime("%H:%M"),
    "floor": t.dt.floor("30min").dt.strftime("%H:%M"),
    "round": t.dt.round("30min").dt.strftime("%H:%M"),
    "ceil": t.dt.ceil("30min").dt.strftime("%H:%M"),
})
```

Что здесь происходит:

- `t.dt.floor("30min")` — к началу получаса; `"15min"`, `"h"`, `"D"` — другие шаги. Дата при этом сохраняется: `floor("h")` от `2026-09-01 10:31` — `2026-09-01 10:00`, а не просто `10`.
- `dt.round` — к ближайшей отметке, `dt.ceil` — вверх.
- `dt.strftime("%H:%M")` — время как текст «часы:минуты», только для красивого вывода.

**На реальных данных:** какие получасы самые загруженные за три месяца?

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

slot = df["datetime"].dt.floor("30min").dt.strftime("%H:%M")   # получас дня, без даты
slot.value_counts().head(5)
```

Как читать: пик — получас 09:00–09:30, 129 заказов за три месяца, рядом 09:30 (126). Это интервалы, на которые нужен второй бариста. Без `strftime` получасы разных дней были бы разными значениями: `floor` сохраняет дату, и `value_counts` считал бы заказы в конкретный получас конкретного дня.

::: warn Типичные ошибки
- **`round` вместо `floor` для интервалов.** Заказ в 08:29 попадёт в «08:30», и границы получасов съедут. Для «в какой интервал попал» — `floor`.
- **Частота `"30m"`.** `m` — это не минуты. Пишите `"30min"`; час — `"h"`, день — `"D"`.
- **Ждали только время, а получили дату.** `floor` возвращает полную дату-время. Время суток — `.dt.time` или `.dt.strftime("%H:%M")`.
- **`dt.hour` вместо `floor("h")` для ряда по часам.** `dt.hour` смешает 10 часов всех дней в одну группу. Для «по часам каждого дня» — `floor("h")` или `resample("h")`.
:::

{{practice: floor}}

## Разница между датами

Разность двух дат — интервал (`Timedelta`). Из него можно достать число дней:

```python
import pandas as pd
a = pd.Timestamp("2026-09-01 10:00")
b = pd.Timestamp("2026-09-15 18:30")
print(b - a)
print((b - a).days)
```

С целыми столбцами — так же, через `.dt.days`. Например, сколько дней прошло между первым и последним заказом гостя:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

life = df.groupby("client_id")["datetime"].agg(["min", "max"])
life["days"] = (life["max"] - life["min"]).dt.days
life.head()
```

::: predict
```python static
import pandas as pd
print((pd.Timestamp("2026-10-10") - pd.Timestamp("2026-10-01")).days)
```

- `10`
- [x] `9`
- `8`

Почему: от 1-го до 10-го — 9 полных суток. Как с индексами: разность концов, а не число дней в списке.
:::

{{practice: lifetime}}

## Изменение к прошлому периоду

`pct_change()` считает изменение к предыдущему значению в долях — то, что в уроке «Цикл for» главы 1 мы писали циклом:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

monthly = df.resample("ME", on="datetime")["amount"].sum()
(monthly.pct_change() * 100).round(1)
```

Первое значение — `NaN`: его не с чем сравнить. Октябрь вырос к сентябрю на 6.1 %, ноябрь к октябрю — на 9.6 %: `pct_change` делает `(текущий − прошлый) / прошлый` для каждой пары соседних значений.

::: warn Типичные ошибки
- **Дата осталась текстом.** Без `parse_dates` или `to_datetime` у столбца нет `.dt`, а сравнение идёт по алфавиту.
- **`<=` по последнему дню.** Теряется всё, что было после полуночи этого дня.
- **Неполные периоды.** Первая и последняя неделя `resample` бывают неполными — их сумма занижена.
- **`dt.date` против `dt.normalize()`.** Первый даёт объекты `date` (без времени), второй — даты в полночь (тип `datetime64`, см. раздел «Части даты»); для группировки подходят оба. Но сравнивать с датой-временем (`pd.Timestamp`) или строкой-датой можно только результат `normalize()`: у `dt.date` проверка `== pd.Timestamp("2026-10-15")` молча даёт `False` у всех строк, а `>=` падает с `TypeError`.
:::

{{practice: mom-net, mom}}

## Практика

## task: to-dt | Настоящая дата | warmup

Превратите столбец `datetime` в дату с помощью `pd.to_datetime`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
assert _pd.api.types.is_datetime64_any_dtype(df['datetime']), f'Тип столбца: {df["datetime"].dtype}. Нужно datetime64.'
```

### hint
Результат нужно записать обратно в столбец — иначе таблица не изменится.

### hint
`df["datetime"] = pd.to_datetime(df["datetime"])`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
```

## task: months | Выручка по месяцам | warmup

Посчитайте `by_month` — словарь «номер месяца → выручка».

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
want = {int(k): int(v) for k, v in d.groupby(d['datetime'].dt.month)['amount'].sum().items()}
got = {int(k): int(v) for k, v in dict(need('by_month')).items()}
assert got == want, f'by_month = {got}, а нужно {want}.'
```

### hint
Номер месяца — `df["datetime"].dt.month`.

### hint
`dict(df.groupby(df["datetime"].dt.month)["amount"].sum())` — группировать можно прямо по выражению.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
by_month = dict(df.groupby(df["datetime"].dt.month)["amount"].sum())
```

## task: p-month | Соберите итог по месяцам | warmup

Соберите программу, которая выводит выручку ноября.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
df["month"] = df["datetime"].dt.month
print(df.groupby("month")["amount"].sum()[11])
```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
want = d[d['datetime'].dt.month == 11]['amount'].sum()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Сначала превращение в дату, потом извлечение месяца, потом группировка.

### hint
Ноябрь — месяц 11: значение группировки по ключу `[11]`.

## task: weekend | Доля выходных | base

Посчитайте `weekend_share` — долю выручки, пришедшуюся на субботы и воскресенья, в процентах с одним знаком.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
w = d['datetime'].dt.weekday >= 5
want = round(d.loc[w, 'amount'].sum() / d['amount'].sum() * 100, 1)
assert close(need('weekend_share'), want), f'weekend_share = {need("weekend_share")}, а нужно {want}.'
```

### hint
`dt.weekday`: понедельник — 0, воскресенье — 6.

### hint
Выходные — `df["datetime"].dt.weekday >= 5`; доля — выручка по маске / вся выручка × 100.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
is_weekend = df["datetime"].dt.weekday >= 5
weekend_share = round(df.loc[is_weekend, "amount"].sum() / df["amount"].sum() * 100, 1)
```

### explain
На выходные приходится 35.2 % выручки — ровно столько же, какова их доля в заказах (35.3 %). Выходные — это больше заказов, а не более дорогие заказы: средний чек в субботу почти такой же.

## task: period | Первая половина октября | base

Посчитайте `rev_1_15` — выручку с 1 по 15 октября включительно (до конца дня 15-го).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
want = d[(d['datetime'] >= '2026-10-01') & (d['datetime'] < '2026-10-16')]['amount'].sum()
assert need('rev_1_15') == want, f'rev_1_15 = {need("rev_1_15")}, а нужно {want}. Проверьте правую границу: 15-е включительно — это «меньше 16-го».'
```

### hint
«До конца дня 15-го» — это «раньше начала 16-го».

### hint
`(df["datetime"] >= "2026-10-01") & (df["datetime"] < "2026-10-16")`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
rev_1_15 = df[(df["datetime"] >= "2026-10-01") & (df["datetime"] < "2026-10-16")]["amount"].sum()
```

### explain
С 1 по 15 октября — 113 790 ₽. Граница `< "2026-10-16"` честно включает весь день 15-го; с `<= "2026-10-15"` вышло бы 107 355 ₽.

## task: hours | Часы работы | base

Посчитайте `orders_by_hour` — число заказов по часам (Series «час → заказы», по возрастанию часа) и `peak` — час с максимумом.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
want = d.groupby(d['datetime'].dt.hour).size()
got = need('orders_by_hour')
assert list(got.values) == list(want.values) and list(got.index) == list(want.index), 'orders_by_hour не совпадает с числом заказов по часам.'
assert need('peak') == want.idxmax(), f'peak = {need("peak")}.'
```

### hint
`df.groupby(df["datetime"].dt.hour).size()` — уже по возрастанию часа.

### hint
Час с максимумом — `orders_by_hour.idxmax()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
orders_by_hour = df.groupby(df["datetime"].dt.hour).size()
peak = orders_by_hour.idxmax()
```

### explain
`.dt.hour` вытаскивает час из даты-времени, и группировка идёт по этому вычисленному признаку — отдельный столбец создавать не нужно. `size()` считает строки в каждой группе, а индекс результата — сами часы, поэтому `idxmax()` возвращает час, а не позицию. Пик — 9 утра (255 заказов), второй всплеск — обед, 12–13 часов. Для кофейни это прямой ответ, когда ставить больше бариста.

## task: best-day | Лучший день | base

Найдите `best_date` — дату (без времени) с максимальной выручкой — и `best_revenue` — эту выручку.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
s = d.groupby(d['datetime'].dt.date)['amount'].sum()
assert str(need('best_date')) == str(s.idxmax()), f'best_date = {need("best_date")}, а нужно {s.idxmax()}.'
assert need('best_revenue') == s.max(), f'best_revenue = {need("best_revenue")}.'
```

### hint
`dt.date` отрезает время: все заказы одного дня попадут в одну группу.

### hint
Группировка по `df["datetime"].dt.date`, затем `idxmax()` и `max()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.groupby(df["datetime"].dt.date)["amount"].sum()
best_date = daily.idxmax()
best_revenue = daily.max()
```

### explain
Лучший день — суббота, 14 ноября: 12 957 ₽. `dt.date` убирает время, и все заказы дня складываются вместе — иначе каждый заказ был бы отдельной группой.

## task: mom-net | Рост выручки сети по месяцам | base

Посчитайте `monthly` — выручку сети по месяцам через `resample("ME")`, затем `growth` — изменение каждого месяца к предыдущему в процентах с одним знаком (через `pct_change`). Сохраните в `nov_growth` рост ноября к октябрю — одно число.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
import numbers as _num
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
_m = _d.resample('ME', on='datetime')['amount'].sum()
_g = (_m.pct_change() * 100).round(1)
m_ = need('monthly')
assert isinstance(m_, _pd.Series) and len(m_) == 3, f'monthly должна быть Series из трёх месяцев, а сейчас {type(m_).__name__} длиной {len(m_) if hasattr(m_, "__len__") else "—"}.'
assert list(m_) == list(_m), f'monthly = {list(m_)}, а нужно {list(_m)}: сумма amount по месяцам.'
g_ = need('growth', _pd.Series)
assert calls('pct_change'), 'Посчитайте изменение методом pct_change().'
assert _pd.isna(g_.iloc[0]), 'Первое значение growth должно быть NaN: сентябрь не с чем сравнить.'
assert close(g_.iloc[1], _g.iloc[1], 0.05) or not close(g_.iloc[1], _g.iloc[1] / 100, 0.001), 'В growth доли, а нужны проценты: умножьте на 100.'
assert close(g_.iloc[1], _g.iloc[1], 0.05), f'Рост октября в growth — {g_.iloc[1]}, а нужно {_g.iloc[1]}.'
_n = need('nov_growth')
assert not isinstance(_n, (_pd.Series, _pd.DataFrame)), f'В nov_growth лежит {type(_n).__name__}, а нужно одно число. Последнее значение growth — .iloc[-1] (или .iloc[2]).'
assert isinstance(_n, _num.Number) and close(_n, _g.iloc[2], 0.05), f'nov_growth = {_n!r}, а нужно {_g.iloc[2]}.'
```

### hint
Сначала итоги по месяцам — `resample("ME", on="datetime")`. Потом `pct_change()` у получившейся Series: каждое значение сравнивается с предыдущим.

### hint
`monthly = df.resample("ME", on="datetime")["amount"].sum()`, `growth = (monthly.pct_change() * 100).round(1)`. Ноябрь — последний месяц: `growth.iloc[-1]`.

### hint
```python
monthly = df.resample(..., on="datetime")["amount"].sum()
growth = (monthly....() * 100).round(1)
nov_growth = growth.iloc[...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
monthly = df.resample("ME", on="datetime")["amount"].sum()
growth = (monthly.pct_change() * 100).round(1)
nov_growth = growth.iloc[-1]
```

### explain
Выручка сети растёт: октябрь +6.1 % к сентябрю, ноябрь +9.6 % к октябрю. У сентября — `NaN`: предыдущего месяца в данных нет, и это честнее, чем ноль. `pct_change` экономит ручную формулу `(текущий − прошлый) / прошлый` и не путается в порядке месяцев, потому что `resample` уже выстроил их по времени. Типичная ошибка — забыть `* 100`: получится 0.096, доля вместо процентов.

## task: floor | Самый загруженный получас | base

Управляющий планирует смены по получасам. Припишите каждый заказ к началу его получаса (09:00–09:30 → `"09:00"`), посчитайте заказы в каждом получасе дня за все три месяца и сохраните:

- `peak_slot` — самый загруженный получас строкой вида `"ЧЧ:ММ"`;
- `peak_n` — сколько в нём заказов.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
_vc = _d['datetime'].dt.floor('30min').dt.strftime('%H:%M').value_counts()
_ps = need('peak_slot')
assert isinstance(_ps, str), f'peak_slot = {_ps!r} ({type(_ps).__name__}). Нужна строка вида "09:00": dt.strftime("%H:%M").'
assert _ps == _vc.idxmax(), f'peak_slot = {_ps!r}, а нужно {_vc.idxmax()!r}. Округляйте вниз (floor), а не к ближайшему (round).'
_pn = need('peak_n')
assert _pn != _d['datetime'].dt.floor('30min').value_counts().max(), f'peak_n = {_pn} — это пик в один конкретный день. Уберите дату: оставьте только время «ЧЧ:ММ».'
assert _pn == _vc.max(), f'peak_n = {_pn}, а нужно {_vc.max()}.'
assert calls('floor'), 'Используйте dt.floor.'
```

### hint
Сначала `dt.floor("30min")` — начало получаса. Но `floor` сохраняет дату, а нужны получасы «вообще», по всем дням: превратите результат в текст «часы:минуты».

### hint
`slot = df["datetime"].dt.floor("30min").dt.strftime("%H:%M")`, потом `slot.value_counts()`: у `value_counts` первая строка — самая частая, `idxmax()` — её подпись, `max()` — число.

### hint
```python
slot = df["datetime"].dt.floor(...).dt.strftime("%H:%M")
counts = slot.value_counts()
peak_slot = counts.idxmax()
peak_n = int(counts....())
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
slot = df["datetime"].dt.floor("30min").dt.strftime("%H:%M")
counts = slot.value_counts()
peak_slot = counts.idxmax()
peak_n = int(counts.max())
```

### explain
Пик — получас 09:00–09:30, 129 заказов за три месяца, и сразу за ним 09:30 со 126: утро с 9 до 10 — главный кандидат на второго бариста. Если оставить дату, получится 6 заказов — это максимум в одном получасе одного дня (31 октября, 10:30), совсем другой вопрос. А с `round` заказ в 09:29 попал бы в «09:30», и пиковые получасы перемешались бы.

## task: weekly | Недели | plus

Постройте `weekly` — выручку по неделям через `resample` и сохраните `n_weeks` — сколько недель в результате, и `best_week_end` — **дату** (`date`) конца недели с наибольшей выручкой.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
w = d.resample('W', on='datetime')['amount'].sum()
assert need('n_weeks') == len(w), f'n_weeks = {need("n_weeks")}, а недель {len(w)}.'
assert str(need('best_week_end'))[:10] == str(w.idxmax().date()), f'best_week_end = {need("best_week_end")}, а нужно {w.idxmax().date()}.'
assert calls('resample'), 'Используйте resample.'
```

### hint
`df.resample("W", on="datetime")["amount"].sum()`. Метка недели — её последний день (воскресенье); `.idxmax().date()` даст дату.

### hint
Число недель — `len(weekly)`; первая и последняя недели могут быть неполными, но в подсчёте участвуют.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
weekly = df.resample("W", on="datetime")["amount"].sum()
n_weeks = len(weekly)
best_week_end = weekly.idxmax().date()
```

### explain
14 «недель» — включая неполные по краям; лучшая неделя закончилась 22 ноября. Для сравнения недель между собой неполные края лучше отбросить — их сумма занижена.

## task: lifetime | Сколько дней с нами гость | plus

Для гостей с картой посчитайте число дней между первым и последним заказом и сохраните `avg_days` — среднее по гостям (с одним знаком) и `loyal` — сколько гостей заказывали на протяжении 60 дней и больше.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
g = d.groupby('client_id')['datetime'].agg(['min', 'max'])
days = (g['max'] - g['min']).dt.days
assert close(need('avg_days'), round(days.mean(), 1)), f'avg_days = {need("avg_days")}, а нужно {round(days.mean(), 1)}.'
assert need('loyal') == (days >= 60).sum(), f'loyal = {need("loyal")}.'
```

### hint
`df.groupby("client_id")["datetime"].agg(["min", "max"])` — пустые `client_id` groupby сам пропускает.

### hint
Разница дат — `(life["max"] - life["min"]).dt.days`; «60 и больше» — `(days >= 60).sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
life = df.groupby("client_id")["datetime"].agg(["min", "max"])
days = (life["max"] - life["min"]).dt.days
avg_days = round(days.mean(), 1)
loyal = (days >= 60).sum()
```

### explain
В среднем между первым и последним заказом гостя — 54 дня, 125 гостей заказывали два месяца и дольше. Это заготовка метрики удержания: «гость с нами N дней».

## task: mom | Рост по кофейням | star

Посчитайте для каждой кофейни рост выручки ноября к октябрю в процентах (с одним знаком) и сохраните в `growth` — Series «кофейня → рост», а в `fastest` — кофейню с самым быстрым ростом.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
p = _pd.pivot_table(d, index='shop_id', columns=d['datetime'].dt.month, values='amount', aggfunc='sum')
want = ((p[11] - p[10]) / p[10] * 100).round(1)
g = need('growth')
assert {k: round(float(v), 1) for k, v in dict(g).items()} == want.to_dict(), f'growth = {dict(g)}, а нужно {want.to_dict()}.'
assert need('fastest') == want.idxmax(), f'fastest = {need("fastest")!r}.'
```

### hint
Сводная таблица: строки — кофейни, столбцы — номер месяца, значения — сумма. Тогда октябрь — столбец `10`, ноябрь — `11`. Месяц можно сначала положить в отдельный столбец (`df["month"] = df["datetime"].dt.month`) — или, как в `groupby`, передать в `columns` сразу выражение-Series.

### hint
`pd.pivot_table(df, index="shop_id", columns=df["datetime"].dt.month, values="amount", aggfunc="sum")`. Рост — `(ноябрь − октябрь) / октябрь × 100` по столбцам `11` и `10`.

### hint
```python
pv = pd.pivot_table(df, index="shop_id", columns=df["datetime"].dt.month, values="amount", aggfunc="sum")
growth = ((pv[...] - pv[...]) / pv[...] * 100).round(1)
fastest = growth.idxmax()
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
pv = pd.pivot_table(df, index="shop_id", columns=df["datetime"].dt.month, values="amount", aggfunc="sum")
growth = ((pv[11] - pv[10]) / pv[10] * 100).round(1)
fastest = growth.idxmax()
```

### explain
KZN-1 выросла в ноябре на 24.3 % — сильнее всех; PRM-2 — единственная, где выручка упала (−6 %). Рост в процентах честнее сравнения рублей: большой и маленькой кофейне одни и те же +5 000 ₽ значат разное. То же даёт `pct_change` вдоль строки: `pv.pct_change(axis=1)[11]` — изменение каждого месяца к предыдущему столбцу.
