---
title: "Временной ряд: индекс-дата, resample и скользящие окна"
files: [app_orders.csv]
lead: "Временной ряд — значения, упорядоченные во времени: заказы по часам, выручка по дням. У него свои инструменты: дата как индекс таблицы, переход между частотами (часы → дни → недели), скользящие средние и сдвиги. Осваиваем их на заказах через приложение «Зерна»."
recap:
  - "Ряд удобно хранить как Series с индексом-датой: `pd.read_csv(..., parse_dates=[...], index_col=...)`. Индекс должен быть отсортирован."
  - "Срез по датам: `s['2026-06']`, `s['2026-06-01':'2026-06-07']`."
  - "`s.resample('D').sum()` — переход к другой частоте с агрегацией (как GROUP BY по началу дня). Частоты: 'h', 'D', 'W', 'MS'."
  - "`s.rolling(7).mean()` — скользящее среднее по 7 последним значениям; сглаживает шум и показывает тренд."
  - "`s.shift(1)` — значение на шаг раньше; `s.diff()` — разница с предыдущим значением; `s.pct_change()` — та же разница в долях: `s.diff() / s.shift(1)`."
  - "Части индекса-даты — `s.index.hour`, `s.index.dayofweek`, `s.index.date`; по ним группируют: `s.groupby(s.index.hour).mean()`."
  - "Аномалии (сбои, акции) видны на графике и в разности с типичным значением — их отмечают перед моделированием."
---

## Дата как индекс

Файл `app_orders.csv` — число заказов через приложение по часам с марта по август 2026 года. Загрузим его так, чтобы дата стала индексом, а сам ряд — Series:

```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
print(s.head())
print("строк:", len(s), "| с", s.index.min(), "по", s.index.max())
print("индекс монотонный:", s.index.is_monotonic_increasing)
```

**Что здесь происходит:**

- `parse_dates=["datetime"]` превращает текст «2026-03-01 00:00:00» в дату-время (глава 2), `index_col="datetime"` делает этот столбец индексом;
- `["orders"]` в конце берёт единственный столбец как Series — ряд «время → число заказов»;
- `s.index.min()`, `s.index.max()` — первый и последний час;
- `is_monotonic_increasing` — идут ли даты строго по возрастанию.

**Что получилось:** 4416 часов — ровно 184 дня по 24 часа, с 1 марта по 31 августа. Пропущенных часов нет: шаг между соседними метками везде ровно час (проверить можно так: `s.index.to_series().diff().value_counts()`).

Временной ряд почти всегда хранят так: индекс — время, значение — величина. Многие инструменты pandas работают только с отсортированным временным индексом, поэтому проверка `is_monotonic_increasing` — первое, что стоит сделать (если False — `s = s.sort_index()`).

С таким индексом срезы пишутся датами:

```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
print(s["2026-06-03 09:00":"2026-06-03 18:00"])
print("всего за июнь:", s["2026-06"].sum())
```

**Что здесь происходит:**

- `s["2026-06-03 09:00":"2026-06-03 18:00"]` — срез по датам. В отличие от срезов по номерам, **правая граница включается**: 18:00 попадёт в результат.
- `s["2026-06"]` — все часы июня: pandas понимает неполную дату как «весь этот период».

В середине 3 июня — пять часов подряд с нулём заказов. В дни работы это подозрительно: скорее всего, приложение не работало. Такие места отмечают до любого анализа.

У индекса-даты можно взять части, как у столбца с датами через `.dt` (глава 2), только без `.dt`: `s.index.hour` — час, `s.index.dayofweek` — день недели (0 — понедельник), `s.index.date` — дата без времени. По этим частям группируют сам ряд: `s.groupby(s.index.hour).mean()` — средний заказ в каждый час суток. Это тот же GROUP BY, только ключ берётся не из столбца, а из индекса.

{{practice: load, slice}}

## Другая частота: resample

Часовой ряд шумный. Чтобы увидеть общую картину, переходят к более крупной частоте — **resample** (передискретизация). Это группировка по интервалам времени.

Сначала на игрушечном ряду из шести часов, чтобы всё посчитать глазами:

```python
import pandas as pd

idx = pd.date_range("2026-06-01 08:00", periods=6, freq="h")   # 08:00, 09:00, …, 13:00
toy = pd.Series([5, 7, 12, 10, 3, 9], index=idx)
print(toy)
print(toy.resample("2h").sum())      # корзины по 2 часа: 08–09, 10–11, 12–13
print(toy.resample("3h").mean())     # корзины по 3 часа, среднее
```

**Что здесь происходит:**

- `pd.date_range(начало, periods=6, freq="h")` — шесть меток времени с шагом в час.
- `resample("2h").sum()` — делит время на корзины по 2 часа и складывает: 5 + 7 = 12 (08:00), 12 + 10 = 22 (10:00), 3 + 9 = 12 (12:00). Метка корзины — её **начало**.
- `resample("3h").mean()` — корзины по 3 часа, среднее. Здесь сюрприз: корзины отсчитываются **от полуночи**, а не от первой строки. Границы — 06:00, 09:00, 12:00, поэтому в первую корзину (06–08) попал только час 08:00 → 5; во вторую (09–11) — (7 + 12 + 10) / 3 ≈ 9.67; в третью (12–14) — (3 + 9) / 2 = 6. С корзинами по 2 часа этого не видно: 08:00 и так делится на 2.

::: figure ts-resample-bins
Игрушечный ряд из шести часов: сверху корзины по 2 часа (сумма), снизу — по 3 часа (среднее). Корзины по 3 часа начинаются в 06:00, 09:00, 12:00 — от полуночи, поэтому первая неполная.
:::

::: tip Аналогия
resample — как сдача выручки в бухгалтерию: кассир не отчитывается за каждый чек, а приносит по одной сумме за смену. Смены идут по расписанию заведения (с полуночи), а не с того момента, когда пришёл первый гость, — поэтому первая «смена» может оказаться неполной.
:::

::: warn Типичные ошибки
- **Ждать, что корзины начнутся с первой строки.** Они привязаны к полуночи (для дней — к началу суток, для `"W"` — к воскресенью). Если нужно «от первой строки», есть параметр `origin="start"`; чаще правильнее оставить календарные границы и просто помнить о неполной первой корзине.
- **Сравнивать неполные корзины с полными.** Первая и последняя неделя (месяц) часто неполные — их сумма меньше не из-за спада. Проверяйте число значений в корзине: `.resample("W").count()`.
- **`resample` на неотсортированном или строковом индексе.** Нужен индекс-дата (`parse_dates`, `index_col`); иначе — `TypeError: Only valid with DatetimeIndex…`.
:::

Теперь на настоящих данных:

```python
import pandas as pd
import matplotlib.pyplot as plt
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

daily = s.resample("D").sum()
weekly = s.resample("W").sum()
print(daily.head(3))
print("месяцы:", s.resample("MS").sum().tolist())

fig, ax = plt.subplots(figsize=(8, 3.5))
daily.plot(ax=ax, label="за день")
daily.rolling(7).mean().plot(ax=ax, label="среднее за 7 дней")
ax.set_ylabel("заказов")
ax.legend()
plt.show()
```

**Что здесь происходит:**

- `s.resample("D").sum()` — сумма заказов за каждый день; `"W"` — за неделю, `"MS"` — за месяц.
- `daily.rolling(7).mean()` — скользящее среднее за 7 дней (подробно — в следующем разделе).
- `.plot(ax=ax, label=...)` — две линии на одном графике; `ax.legend()` — подписи.

Коды частот: `"h"` — час, `"D"` — день, `"W"` — неделя (по воскресеньям), `"MS"` — месяц с меткой на первое число. Вместо `sum` может быть любая агрегация: `mean`, `max`, `count`.

Где стоит метка корзины, зависит от частоты. У `"h"`, `"D"` и `"MS"` метка — **начало** периода (как в игрушечном примере). У `"W"` метка — **конец** недели, воскресенье: корзина с меткой 2026-03-08 — это дни с понедельника 2 марта по воскресенье 8 марта. Так же ведёт себя месячный код `"ME"` (метка — последнее число месяца). Поэтому первая недельная корзина нашего ряда помечена 2026-03-01: 1 марта — воскресенье, и в эту «неделю» попал один день. Последняя помечена 2026-09-06, хотя данных в сентябре нет: в неё попал один день — понедельник 31 августа.

::: sql
`s.resample("D").sum()` — это `SELECT date_trunc('day', datetime), SUM(orders) FROM app_orders GROUP BY 1`.
:::

На графике видно главное: заказов становится больше (приложением пользуется всё больше гостей), а дневные значения прыгают вокруг этого роста. Отдельные всплески — пятничные акции, провал 3 июня — сбой.

{{practice: daily, by-hour, months}}

## Скользящее среднее

`rolling(7).mean()` для каждого дня берёт среднее по 7 последним дням (включая текущий). Получается сглаженная линия, на которой недельные колебания и случайные всплески почти не видны, — **тренд**. Первые 6 значений — пропуски: для них ещё нет семи предыдущих дней.

```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
r = daily.rolling(7).mean()
print("первые значения:", r.head(8).round(1).tolist())
print(f"рост за полгода: с {r.iloc[6]:.0f} до {r.iloc[-1]:.0f} заказов в день")
```

**Что здесь происходит:**

- `daily.rolling(7)` — «окно» из 7 последних значений, которое сдвигается на день; `.mean()` — среднее в каждом положении окна.
- `r.head(8)` — первые 8 значений: шесть пропусков, потом первые средние.
- `r.iloc[6]` — первое непустое значение (седьмой день), `r.iloc[-1]` — последнее.

Как окно движется, проще увидеть на игрушечном ряду из раздела про resample (5, 7, 12, 10, 3, 9) с окном в 3 часа: `toy.rolling(3).mean()` даёт пропуск, пропуск, 8, 9.67, 8.33, 7.33 — по значению на каждый час. Корзины resample стоят встык и сжимают ряд.

::: figure ts-rolling-vs-resample
Сверху: окно из трёх часов сдвигается на час, окна перекрываются, на выходе столько же значений, сколько на входе (первые два — NaN). Снизу: resample("2h") — корзины встык, из шести значений получается три.
:::

::: warn Типичные ошибки
- **Удивляться NaN в начале.** У `rolling(7)` первые 6 значений пустые — окну не хватает истории. Для графика это нормально; если пропуски мешают, есть `min_periods` (`rolling(7, min_periods=1)`), но тогда первые значения — среднее по меньшему числу дней.
- **Путать окно с центрированным.** По умолчанию окно смотрит только назад. `center=True` берёт дни и до, и после — для графика это красиво, а для признаков модели это подглядывание в будущее (урок «Признаки для прогноза ряда»).
- **Окно в строках, а не во времени.** `rolling(7)` — 7 строк: если дни пропущены, это уже не неделя (для такого ряда есть `rolling("7D")`; в нашем пропусков нет).
:::

::: predict
```python static
import pandas as pd
s = pd.Series([10, 20, 30, 40])
print(s.rolling(2).mean().tolist())
```

- `[15.0, 25.0, 35.0, nan]`
- [x] `[nan, 15.0, 25.0, 35.0]`
- `[10.0, 15.0, 25.0, 35.0]`

Почему: окно из 2 значений заканчивается на текущем. Для первого значения второго ещё нет — пропуск. Дальше: (10+20)/2, (20+30)/2, (30+40)/2.
:::

::: quiz
Чем `daily.rolling(7).mean()` отличается от перехода к неделям через `resample("W")`?

- [x] Скользящее среднее даёт значение на каждый день — окно сдвигается на день, и ряд остаётся дневным; resample сжимает ряд до одной точки на неделю
  > Поэтому скользящим средним сглаживают ряд, не теряя частоты, а resample меняет саму частоту ряда.
- [ ] Ничем: оба считают среднее за неделю, просто разными функциями
  > Числа считаются по-разному: у rolling окна перекрываются и сдвигаются на день, у resample недели идут встык и не пересекаются.
- [ ] `rolling(7)` берёт 3 дня до текущего, сам день и 3 дня после
  > По умолчанию окно заканчивается на текущем дне и смотрит только назад. Центрированное окно — отдельная опция `center=True`.
- [ ] На первых днях `rolling(7)` усредняет столько дней, сколько есть
  > Нет: пока в окне меньше 7 значений, получается пропуск — у дневного ряда первые 6 значений пустые.
:::

{{practice: p-roll, growth}}

## Сдвиг и разность

Два самых частых преобразования ряда:

- `s.shift(1)` — значение на шаг раньше (вчера, час назад). Основа признаков для прогноза (урок «Признаки для прогноза ряда»);
- `s.diff()` — разница с предыдущим значением: s − s.shift(1). Показывает изменения, а не уровень;
- `s.pct_change()` — то же изменение в долях от предыдущего значения: `s.diff() / s.shift(1)`. Умножьте на 100 — получится привычный «рост, %». Первое значение — пропуск, как у `diff()`.

```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
t = pd.DataFrame({"заказы": daily, "вчера": daily.shift(1), "изменение": daily.diff()})
print(t.head(4))
print("самый резкий рост за день:", t["изменение"].idxmax().date(), int(t["изменение"].max()))
```

Как это выглядит на четырёх днях:

| день | заказы | `shift(1)` (вчера) | `diff()` (изменение) |
|---|---|---|---|
| пн | 200 | — | — |
| вт | 210 | 200 | +10 |
| ср | 190 | 210 | −20 |
| чт | 230 | 190 | +40 |

`pct_change()` для этих дней: пропуск, 10 / 200 = 0.05, −20 / 210 ≈ −0.095, 40 / 190 ≈ 0.211 — то есть +5 %, −9.5 %, +21.1 %.

::: figure ts-shift-diff
Те же четыре дня: `shift(1)` опускает каждое значение на строку вниз (в строке вторника — понедельник), `diff()` — разница с этой строкой. `shift(-1)` поднимает значения вверх — это завтрашний день, в признаки его класть нельзя.
:::

**Что здесь происходит в коде:**

- `daily.shift(1)` — весь ряд сдвинут на день вперёд: в строке вторника стоит значение понедельника.
- `daily.diff()` — то же, что `daily - daily.shift(1)`.
- `t["изменение"].idxmax()` — дата, когда рост был наибольшим; `.date()` — без времени.

Самый резкий рост — в дни акций: 22 мая заказов почти на 140 больше, чем накануне.

::: predict
```python static
import pandas as pd
s = pd.Series([3, 5, 4, 8])
print(s.diff().tolist(), s.shift(-1).tolist())
```

- `[nan, 2.0, -1.0, 4.0] [nan, 3.0, 5.0, 4.0]`
- [x] `[nan, 2.0, -1.0, 4.0] [5.0, 4.0, 8.0, nan]`
- `[2.0, -1.0, 4.0, nan] [5.0, 4.0, 8.0, nan]`

Почему: `diff()` — разница с предыдущим (у первого предыдущего нет — пропуск). `shift(-1)` сдвигает в обратную сторону: в каждой строке — **следующее** значение. Такой сдвиг используют, чтобы поставить рядом с признаками «завтрашний» ответ, — но в признаки модели его класть нельзя: это подглядывание в будущее (урок «Признаки для прогноза ряда»).
:::

::: quiz
`s.shift(1)` для часового ряда — это:

- [x] Значение предыдущего часа напротив текущего: прошлое, доступное в момент прогноза
  > Поэтому из сдвигов строят лаги. `s.shift(-1)` дал бы следующий час — это утечка.
- [ ] Значение следующего часа
  > Это `shift(-1)`, заглядывание в будущее.
- [ ] Разница с прошлым часом
  > Разница — `s.diff()` или `s - s.shift(1)`.
- [ ] Среднее за час
  > Средние — `rolling` или `resample`.
:::

{{practice: zeros, anomalies}}

## Разберём вместе: есть ли недельный ритм

Кофейни живут по неделе: в будни утром — по пути на работу, в выходные — позже. Видно ли это в заказах через приложение?

**План:** дневной ряд → номер дня недели у каждого дня → среднее по дням недели → сравнить с общим средним.

```python
import pandas as pd

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
names = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
by_wd = daily.groupby(daily.index.dayofweek).mean()
by_wd.index = names
print(by_wd.round(1))
print("отношение к среднему:", (by_wd / daily.mean()).round(2).to_dict())
```

**Что здесь происходит:**

- `daily.index.dayofweek` — номер дня недели каждой даты: 0 — понедельник, 6 — воскресенье.
- `groupby(...).mean()` — среднее число заказов в понедельники, вторники и т. д.
- `by_wd.index = names` — заменяем номера названиями для читаемости.
- Делим на общее среднее: 1.05 значит «на 5 % больше обычного дня».

**Что получилось:** будни и выходные почти одинаковы — около 204–214 заказов в день, — а пятница заметно выше (около 231). Сильного недельного ритма у **дневных** сумм нет; пятница выделяется из-за акций, которые проходят по пятницам (задача со звёздочкой). Зато сильный ритм есть **внутри суток** — это задача «Суточный профиль».

{{practice: friday}}

## Практика

## task: load | Ряд из файла | warmup

Загрузите `app_orders.csv` как Series `s` с индексом-датой. Сохраните `n` — число часов в ряду, `start` и `end` — первую и последнюю дату (значения индекса), `zero_hours` — сколько часов с нулём заказов.

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
s1 = need('s', _pd.Series)
assert isinstance(s1.index, _pd.DatetimeIndex), 'Индекс s должен быть датами: parse_dates и index_col.'
assert need('n') == len(s0), f'n = {need("n")}.'
assert need('start') == s0.index.min() and need('end') == s0.index.max(), f'start, end = {need("start")}, {need("end")}.'
assert need('zero_hours') == int((s0 == 0).sum()), f'zero_hours = {need("zero_hours")}.'
```

### hint
`s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]`.

### hint
Первая и последняя дата — `s.index.min()` и `s.index.max()`; часы с нулём — `(s == 0).sum()`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
n = len(s)
start, end = s.index.min(), s.index.max()
zero_hours = int((s == 0).sum())
```

### explain
Часов с нулём заказов довольно много — почти все они ночные (в 3–4 часа утра заказы через приложение редки). Днём (с 8 до 20) нулей шесть: пять — 3 июня с 12:00 до 16:00 и один — 6 марта в 16:00. Ночной ноль — норма, дневной — аномалия. Одна и та же цифра значит разное в зависимости от времени.

## task: slice | Один день акции | warmup

Ряд `s` загружен в заготовке. Сохраните `day_total` — сколько заказов было 22 мая 2026 года за весь день, `morning` — с 08:00 до 10:00 включительно и `share_morning` — долю утра в дне (3 знака).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d, m = int(s0['2026-05-22'].sum()), int(s0['2026-05-22 08:00':'2026-05-22 10:00'].sum())
assert need('day_total') == d, f'day_total = {need("day_total")}, а нужно {d}.'
assert need('morning') == m, f'morning = {need("morning")}, а нужно {m}: срез по датам включает правую границу 10:00.'
assert close(need('share_morning'), round(m / d, 3), 0.0011), f'share_morning = {need("share_morning")}.'
```

### hint
Весь день — `s["2026-05-22"]`; интервал — `s["2026-05-22 08:00":"2026-05-22 10:00"]`.

### hint
Сумма заказов — `.sum()`; доля — `round(morning / day_total, 3)`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

day_total = int(s["2026-05-22"].sum())
morning = int(s["2026-05-22 08:00":"2026-05-22 10:00"].sum())
share_morning = round(morning / day_total, 3)
print(day_total, morning, share_morning)
```

## task: daily | Дни и недели | warmup

Сохраните `daily` — заказы по дням (сумма), `weekly_mean` — среднее число заказов в день по неделям (сначала дни, потом среднее по неделям: `daily.resample("W").mean()`) и `week_days` — сколько дней попало в каждую неделю (`daily.resample("W").count()`). В `best_week` — метку (воскресенье, конец недели) **полной** недели (7 дней) с наибольшим средним, в `best_mean` — это среднее (1 знак).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d0 = s0.resample('D').sum(); w0 = d0.resample('W').mean()
assert need('daily', _pd.Series).equals(d0), 'daily — s.resample("D").sum().'
assert _pd.Series(need('weekly_mean')).round(6).equals(w0.round(6)), 'weekly_mean — daily.resample("W").mean().'
c0 = d0.resample('W').count()
assert list(_pd.Series(need('week_days')).values) == list(c0.values), 'week_days — daily.resample("W").count().'
full = w0[c0 == 7]
assert need('best_week') != w0.idxmax(), f'best_week = {need("best_week")}: в эту «неделю» попал один день, 31 августа. Нужна лучшая полная неделя: week_days == 7.'
assert need('best_week') == full.idxmax(), f'best_week = {need("best_week")}, а нужно {full.idxmax().date()}.'
assert close(need('best_mean'), round(full.max(), 1), 0.06), f'best_mean = {need("best_mean")}, а нужно {round(float(full.max()), 1)}.'
```

### hint
Сначала дневной ряд `s.resample("D").sum()`, потом по нему `resample("W").mean()`. Если взять `s.resample("W").mean()` сразу от часового ряда, получится среднее за час, а не за день.

### hint
Полные недели — `weekly_mean[week_days == 7]`; у них `.idxmax()` и `.max()`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
weekly_mean = daily.resample("W").mean()
week_days = daily.resample("W").count()
full = weekly_mean[week_days == 7]
best_week = full.idxmax()
best_mean = round(full.max(), 1)
print(weekly_mean.idxmax(), week_days[weekly_mean.idxmax()], best_week, best_mean)
```

### explain
Если взять `weekly_mean.idxmax()` без фильтра, «лучшей» окажется неделя с меткой 2026-09-06 — среднее 286, но в ней один день, понедельник 31 августа. Это ловушка неполной корзины из блока «Типичные ошибки»: среднее по одному дню нельзя сравнивать со средним по семи. Лучшая полная неделя кончается 16 августа: 265.6 заказа в день. Первая корзина (2026-03-01) тоже неполная — один день.

## task: p-roll | Скользящее среднее | warmup

Соберите код, который считает 7-дневное скользящее среднее и печатает число пропусков в нём.

### parsons
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
trend = daily.rolling(7).mean()
print(int(trend.isna().sum()))
```

### check
```python
assert _lines == ['6'], f'Сейчас: {_lines}.'
```

### hint
Сначала ряд, потом дни, потом скользящее среднее.

### hint
`rolling` применяют к дневному ряду, а не к часовому.

## task: by-hour | Суточный профиль | base

Посчитайте средний заказ по часу суток отдельно для будней и выходных: DataFrame `profile` (индекс — час 0–23, столбцы `будни` и `выходные`, 1 знак). Сохраните `peak_weekday`, `peak_weekend` — час максимума в каждом столбце.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
we = s0.index.dayofweek >= 5
wd = s0[~we].groupby(s0[~we].index.hour).mean().round(1); wk = s0[we].groupby(s0[we].index.hour).mean().round(1)
p = need('profile', _pd.DataFrame)
assert list(p.index) == list(range(24)), 'Индекс profile — часы 0–23.'
assert all(close(p.loc[h, 'будни'], wd[h], 0.06) and close(p.loc[h, 'выходные'], wk[h], 0.06) for h in range(24)), 'Средние по часам не совпадают. Будни — dayofweek < 5.'
assert need('peak_weekday') == int(wd.idxmax()) and need('peak_weekend') == int(wk.idxmax()), f'peak_weekday, peak_weekend = {need("peak_weekday")}, {need("peak_weekend")}.'
```

### hint
Сначала отберите нужные дни: будни — `s[s.index.dayofweek < 5]`, выходные — `s[s.index.dayofweek >= 5]`.

### hint
День недели — `s.index.dayofweek` (0 — понедельник), час — `s.index.hour`. Группировка по часу: `part.groupby(part.index.hour).mean()`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
weekend = s.index.dayofweek >= 5
wd = s[~weekend]
we = s[weekend]
profile = pd.DataFrame({
    "будни": wd.groupby(wd.index.hour).mean(),
    "выходные": we.groupby(we.index.hour).mean(),
}).round(1)
peak_weekday = int(profile["будни"].idxmax())
peak_weekend = int(profile["выходные"].idxmax())
```

### explain
В будни три пика — утренний перед работой, обеденный и вечерний; в выходные утро «сдвигается» к полудню и пиков почти нет — ровное плато днём. Модели прогноза нужно знать и час, и тип дня — пригодится в уроке «Признаки для прогноза ряда».

## task: growth | Рост по скользящему среднему | base

По дневному ряду посчитайте 28-дневное скользящее среднее `trend28`. Сохраните `first_value` — его первое непустое значение, `last_value` — последнее (оба целые, округлением) и `growth_pct` — рост в процентах (1 знак). Рост считайте по неокруглённым значениям скользящего среднего, а не по `first_value` и `last_value`.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
t = s0.resample('D').sum().rolling(28).mean().dropna()
f, l = round(t.iloc[0]), round(t.iloc[-1])
assert need('first_value') == f and need('last_value') == l, f'first_value, last_value = {need("first_value")}, {need("last_value")}, а нужно {f}, {l}.'
assert close(need('growth_pct'), round((t.iloc[-1] / t.iloc[0] - 1) * 100, 1), 0.06), f'growth_pct = {need("growth_pct")}, а нужно {round(float((t.iloc[-1] / t.iloc[0] - 1) * 100), 1)}: считайте по неокруглённым t.iloc[0] и t.iloc[-1].'
```

### hint
`trend28.dropna()` уберёт первые 27 пропусков; первое и последнее — `.iloc[0]`, `.iloc[-1]`.

### hint
Рост в процентах считайте по неокруглённым значениям: `(t.iloc[-1] / t.iloc[0] - 1) * 100`, затем `round(..., 1)`. Если взять уже округлённые 171 и 258, получится 50.9 вместо 50.6.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
trend28 = daily.rolling(28).mean()
t = trend28.dropna()
first_value, last_value = round(t.iloc[0]), round(t.iloc[-1])
growth_pct = round((t.iloc[-1] / t.iloc[0] - 1) * 100, 1)
```

### explain
Скользящее среднее за 28 дней включает ровно четыре полные недели, поэтому недельная сезонность (выходные против будней) в нём взаимно гасится, и остаётся тренд. Первые 27 значений пустые — для них ещё не набралось 28 дней. Поэтому сравниваем первое непустое значение (28 марта, ≈ 171 заказ в день) с последним (31 августа, ≈ 258): рост на 50.6 %. Сравнивать отдельные дни было бы ненадёжно: один дождливый понедельник легко исказил бы результат на десятки процентов.

## task: months | Рост по месяцам | base

Посчитайте `monthly` — сумму заказов по месяцам (`"MS"`) и `growth` — рост к предыдущему месяцу в процентах (`pct_change() * 100`, 1 знак). Месяцы разной длины, поэтому посчитайте и `per_day` — среднее число заказов в день по месяцам (1 знак) и `growth_per_day` — его рост в процентах (1 знак). В `slowest_month` — месяц (число 1–12) с наименьшим ростом `growth`, а в `slowest_month_per_day` — с наименьшим ростом `growth_per_day`.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
m = s0.resample('MS').sum(); g = (m.pct_change() * 100).round(1)
pdm = s0.resample('D').sum().resample('MS').mean().round(1); gp = (pdm.pct_change() * 100).round(1)
assert list(need('monthly').values) == list(m.values), 'monthly — s.resample("MS").sum().'
assert all(close(a, b, 0.06) for a, b in zip(need('growth').dropna().values, g.dropna().values)), f'growth = {list(need("growth").round(1))}, а нужно {list(g)}.'
assert all(close(a, b, 0.06) for a, b in zip(need('per_day').values, pdm.values)), f'per_day = {list(need("per_day"))}, а нужно {list(pdm)}.'
assert all(close(a, b, 0.06) for a, b in zip(need('growth_per_day').dropna().values, gp.dropna().values)), f'growth_per_day = {list(need("growth_per_day"))}.'
assert need('slowest_month') == g.idxmin().month and need('slowest_month_per_day') == gp.idxmin().month, f'slowest_month = {need("slowest_month")}, slowest_month_per_day = {need("slowest_month_per_day")}.'
```

### hint
Месячные суммы — `s.resample("MS").sum()`; рост — `.pct_change() * 100`. Первое значение роста — пропуск: у марта нет предыдущего месяца.

### hint
Среднее в день по месяцам: сначала дневные суммы, потом среднее по месяцу — `s.resample("D").sum().resample("MS").mean()`.

### hint
Месяц с минимальным ростом: `growth.idxmin().month` (индекс — дата первого числа месяца).

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

monthly = s.resample("MS").sum()
growth = (monthly.pct_change() * 100).round(1)
per_day = s.resample("D").sum().resample("MS").mean().round(1)
growth_per_day = (per_day.pct_change() * 100).round(1)
slowest_month = growth.idxmin().month
slowest_month_per_day = growth_per_day.idxmin().month
print(pd.DataFrame({"заказов": monthly, "рост %": growth, "в день": per_day, "рост в день %": growth_per_day}))
print(slowest_month, slowest_month_per_day)
```

### explain
По сумме самый слабый месяц — июнь (рост около 3 %), а по среднему в день июнь растёт примерно на 6 %, и слабейшим оказывается май (около 4.5 %). Разница в длине: в июне 30 дней, в мае 31 — минус целый день заказов. Плюс в июне был сбой 3 июня. А апрель по сумме вырос на 9 %, по среднему в день — почти на 13 %: в марте на день больше. Сравнивать месяцы по суммам — классическая ловушка отчётов; для темпов роста берут средние в день (или выравнивают на число рабочих дней).

## task: zeros | Ночь или сбой | plus

Нули в часовом ряду бывают двух видов: ночью заказов просто нет, а днём ноль — подозрение на сбой. Посчитайте `zero_by_hour` — долю нулевых часов для каждого часа суток (Series с индексом 0–23, 2 знака) и `night_hours` — список часов, где эта доля больше 0.3. Затем найдите **дневные** нули — часы с 8 до 20 включительно с нулём заказов: `n_day_zeros` — их число и `outage_dates` — отсортированный список дат (`datetime.date`), когда они были.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
z = (s0 == 0).groupby(s0.index.hour).mean().round(2)
g = need('zero_by_hour', _pd.Series)
assert list(g.index) == list(range(24)) and all(close(g[h], z[h], 0.006) for h in range(24)), 'zero_by_hour — доля нулей по s.index.hour.'
assert list(need('night_hours', list)) == [h for h in range(24) if z[h] > 0.3], f'night_hours = {need("night_hours")}.'
day = s0[(s0.index.hour >= 8) & (s0.index.hour <= 20)]; zz = day[day == 0]
assert need('n_day_zeros') == len(zz), f'n_day_zeros = {need("n_day_zeros")}.'
assert list(need('outage_dates', list)) == sorted(set(zz.index.date)), f'outage_dates = {need("outage_dates")}.'
```

### hint
Доля нулей по часу: `(s == 0).groupby(s.index.hour).mean()` — среднее от `True/False` и есть доля.

### hint
Дневные часы: `day = s[(s.index.hour >= 8) & (s.index.hour <= 20)]`; нули среди них — `day[day == 0]`.

### hint
Даты нулей: `sorted(set(zeros.index.date))` — `.date` у индекса даёт даты без времени, `set` убирает повторы.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

zero_by_hour = (s == 0).groupby(s.index.hour).mean().round(2)
night_hours = [h for h in range(24) if zero_by_hour[h] > 0.3]
day = s[(s.index.hour >= 8) & (s.index.hour <= 20)]
day_zeros = day[day == 0]
n_day_zeros = len(day_zeros)
outage_dates = sorted(set(day_zeros.index.date))
print(night_hours, n_day_zeros, outage_dates)
```

### explain
Ночью (с 1 до 5 часов) нули — норма: в треть и больше ночей заказов нет вовсе. Днём нулей всего несколько, и они собраны в два дня — 6 марта и 3 июня. Это и есть подозрения на сбои приложения. Такие часы перед моделированием отмечают отдельным признаком или исключают из обучения: иначе модель «выучит», что в июне бывают часы без заказов, и будет занижать прогноз.

## task: anomalies | Поиск аномальных часов | plus

Найдите часы, где заказов намного меньше обычного для этого часа и типа дня. «Обычное» — медиана заказов за этот час суток в этот же день недели за 4 предыдущие недели: `s.shift(168 * k)` для k = 1…4, медиана по строке. Отметьте часы с 10 до 20 включительно, где обычное значение не меньше 8, а фактическое меньше 20 % обычного. Сохраните список `bad_hours` (значения индекса) и `bad_days` — отсортированный список уникальных дат этих часов (как `datetime.date`).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
usual = _pd.concat([s0.shift(168 * k) for k in range(1, 5)], axis=1).median(axis=1)
h = s0.index.hour
m = (h >= 10) & (h <= 20) & (usual >= 8) & (s0 < 0.2 * usual)
want = list(s0.index[m])
assert list(need('bad_hours')) == want, f'bad_hours: найдено {len(need("bad_hours"))} часов, а нужно {len(want)}.'
assert list(need('bad_days')) == sorted({t.date() for t in want}), f'bad_days = {need("bad_days")}.'
```

### hint
`usual = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).median(axis=1)` — 168 часов = неделя.

### hint
Маска из четырёх условий через `&`; часы — `s.index.hour`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

usual = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).median(axis=1)
hour = s.index.hour
mask = (hour >= 10) & (hour <= 20) & (usual >= 8) & (s < 0.2 * usual)
bad_hours = list(s.index[mask])
bad_days = sorted({t.date() for t in bad_hours})
```

### explain
Нашлись три дня, но выглядят они по-разному: 3 июня — четыре из пяти нулевых часов (сбой приложения; час 15:00 не попал: «обычное» там 7.5, меньше порога 8 — порог сам отсекает часть сбоя), а 18 марта и 31 июля — по одному часу, что похоже на случайный провал. Отличить сбой от шума помогает длительность: алерт обычно поднимают, если аномальных часов несколько подряд. Медиана за 4 прошлые недели в тот же час — простой и устойчивый способ задать «норму» с учётом суточного и недельного ритма. Такой расчёт — основа автоматических алертов «заказов подозрительно мало».

## task: friday | Почему пятницы | star

Пятницы выделяются: посчитайте среднее число заказов в день по дням недели (`daily.groupby(daily.index.dayofweek).mean()`) и сохраните `dow_mean` (Series, 1 знак). Затем найдите 5 дней с наибольшим отношением «заказы / 7-дневное скользящее среднее, сдвинутое на 1 день» (`daily.shift(1).rolling(7).mean()`) — это всплески относительно недавнего уровня. Сохраните их даты `spikes` (список `datetime.date` в порядке убывания отношения) и `all_fridays` — `True`, если все они пятницы.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d0 = s0.resample('D').sum()
dm = d0.groupby(d0.index.dayofweek).mean().round(1)
assert all(close(need('dow_mean')[k], dm[k], 0.06) for k in range(7)), f'dow_mean: ожидалось {dm.to_dict()}.'
ratio = (d0 / d0.shift(1).rolling(7).mean()).dropna()
top = [t.date() for t in ratio.nlargest(5).index]
assert list(need('spikes')) == top, f'spikes = {need("spikes")}, а нужно {top}.'
assert need('all_fridays') == all(t.weekday() == 4 for t in top), f'all_fridays = {need("all_fridays")}.'
```

### hint
«Обычный уровень» дня — среднее за 7 предыдущих дней: `daily.shift(1).rolling(7).mean()`. `shift(1)` нужен, чтобы сам день не попадал в своё же среднее. Отношение `daily / уровень` — во сколько раз день выше обычного; первые пропуски уберите `dropna()`.

### hint
Отношение — Series; `ratio.nlargest(5).index` даёт даты всплесков. День недели даты — `.weekday()` (пятница — 4).

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

dow_mean = daily.groupby(daily.index.dayofweek).mean().round(1)
ratio = (daily / daily.shift(1).rolling(7).mean()).dropna()
spikes = [t.date() for t in ratio.nlargest(5).index]
all_fridays = all(t.weekday() == 4 for t in spikes)
```

### explain
Пять самых сильных всплесков — пятницы раз в месяц: это акции в приложении. Средний «эффект пятницы» в таблице по дням недели создан именно ими, а обычная пятница не отличается от других будней. Прежде чем строить признак «пятница», стоит понять, откуда эффект, — здесь правильный признак «день акции».
