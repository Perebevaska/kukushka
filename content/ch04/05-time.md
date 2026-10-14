---
title: Динамика во времени
lead: "«Выручка растёт?» — самый частый вопрос к аналитику. Ответить на него по дневному графику трудно: мешают выходные, праздники и случайные всплески. Учимся сглаживать шум, правильно сравнивать периоды, не попадаться на неполные недели и отмечать события на графике."
files: [orders_3m.csv, deliveries.csv]
recap:
  - "Дневные данные шумят. Агрегируйте по неделям — `resample(\"W\")` — или сглаживайте скользящим средним: `s.rolling(7).mean()`."
  - "Неполные периоды по краям (первая и последняя неделя) занижают сумму. Отбрасывайте их или сравнивайте средние за день."
  - "Профиль по дням недели — среднее **дневной** выручки по дню недели, а не сумма: понедельников и суббот может быть разное число."
  - "Событие на графике: `ax.axvline(pd.Timestamp(\"2026-11-01\"), linestyle=\"--\")` и подпись `ax.text(x, y, \"текст\")`."
  - "До/после события сравнивайте одинаковые по длине и составу дней периоды."
  - "Две величины в разных единицах — вторая ось `ax2 = ax.twinx()`; пользуйтесь осторожно."
---

## Шум и сигнал

Дневная выручка скачет: выходные выше будней, бывают случайно удачные и неудачные дни. За этими скачками трудно увидеть **тренд** — общее направление движения.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(daily.index, daily.values, color="lightgray")
ax.set_title("Выручка по дням — шумно")
```

Есть два способа убрать шум: укрупнить период или сгладить.

## Укрупнить: недели и неполные периоды

`resample("W")` складывает дни в недели (неделя заканчивается в воскресенье):

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
weekly = daily.resample("W").agg(["sum", "count"])
weekly
```

Недель всего 14, поэтому таблица показана целиком. Столбец `count` — сколько дней попало в неделю (подпись строки — воскресенье, которым неделя заканчивается). Данные начинаются во вторник 1 сентября и заканчиваются в понедельник 30 ноября: первая неделя — 6 дней, последняя — всего один. Их суммы будут заниженными, и на графике появятся «провалы», которых в жизни не было.

::: figure partial-weeks
Недельная выручка сети: первая «неделя» — 6 дней (данные начинаются во вторник), последняя — один понедельник 30 ноября. Её провал — артефакт календаря, а не падение продаж.
:::

::: warn
Неполные периоды по краям — одна из самых частых ловушек в отчётах. «Выручка в декабре упала на 70 %!» — а декабрь только начался. Отбрасывайте неполные периоды или сравнивайте **средние за день**.
:::

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
weekly = daily.resample("W").agg(["sum", "count"])
full = weekly[weekly["count"] == 7]

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(weekly.index, weekly["sum"], color="lightgray", label="все недели")
ax.plot(full.index, full["sum"], marker="o", label="только полные")
ax.legend()
ax.set_title("Выручка по неделям")
```

::: quiz
Данные заканчиваются в понедельник, и на недельном графике последняя точка резко падает. Что это, скорее всего?

- [x] Последняя неделя неполная: в ней всего пара дней
  > `resample("W")` складывает всё, что попало в неделю. Неполные первую и последнюю недели убирают или помечают.
- [ ] Резкое падение продаж — надо бить тревогу
  > Сначала проверьте число дней в периоде: падение может быть артефактом.
- [ ] Ошибка `resample`
  > Функция работает правильно, просто неделя ещё не закончилась.
- [ ] Праздники
  > Возможно, но первая проверка — полнота периода.
:::

{{practice: weekly, full-weeks}}

## Сгладить: скользящее среднее

**Скользящее среднее** за 7 дней — для каждого дня среднее за этот день и шесть предыдущих. Неделя всегда содержит все дни недели, поэтому недельный ритм исчезает, а тренд остаётся:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
smooth = daily.rolling(7).mean()

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(daily.index, daily.values, color="lightgray", label="по дням")
ax.plot(smooth.index, smooth.values, color="tab:blue", label="среднее за 7 дней")
ax.legend()
ax.set_title("Выручка: дни и скользящее среднее")
```

::: tip Аналогия
Вы сравниваете температуру за окном не по одному дню, а «в среднем за последнюю неделю». Одна холодная ночь почти не сдвигает такую цифру, а потепление, которое держится несколько дней, — сдвигает. Каждое утро самый старый день выпадает из недели, а вчерашний добавляется. У погоды, правда, нет строгого недельного ритма, а у выручки он есть — поэтому окно берут именно 7 дней, чтобы в нём всегда была ровно одна пара выходных.
:::

::: predict
```python static
import pandas as pd
print(pd.Series([1, 2, 3, 4]).rolling(3).mean().tolist())
```

- `[2.0, 3.0]`
- [x] `[nan, nan, 2.0, 3.0]`
- `[1.0, 1.5, 2.0, 3.0]`

Почему: для первых двух значений ещё нет трёх точек — результат `NaN`. Третье — среднее 1, 2, 3; четвёртое — среднее 2, 3, 4. Длина ряда сохраняется.
:::

::: sql
`AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` — скользящее среднее за 7 дней в SQL. Рамки окна `ROWS` и `RANGE` подробно — в уроке «Рамки окна SQL: накопительные итоги и скользящие средние» главы 2 (углубление).
:::

### Разберём вместе: скользящее среднее руками

Выручка первых девяти дней сентября: 6 608, 7 629, 8 417, 6 701, 9 860, 9 061, 6 265, 6 235, 6 568 ₽.

1. **Дни 1–6** — значения нет (`NaN`): для окна в 7 дней ещё не хватает данных.
2. **День 7**: среднее первых семи — (6 608 + 7 629 + 8 417 + 6 701 + 9 860 + 9 061 + 6 265) / 7 = 54 541 / 7 ≈ **7 792**.
3. **День 8**: окно сдвигается на день — уходит 6 608, приходит 6 235: (54 541 − 6 608 + 6 235) / 7 = 54 168 / 7 ≈ **7 738**.
4. **День 9**: уходит 7 629, приходит 6 568: 53 107 / 7 ≈ **7 587**.

Каждое значение сглаженной линии — средняя за последнюю неделю. В окне всегда ровно одни выходные, поэтому недельная «пила» исчезает, а медленные изменения остаются.

::: figure rolling-window
Окно в 7 дней скользит по ряду: для дней 1–6 значения нет (`NaN`), день 7 — среднее дней 1–7, день 8 — окно сдвинулось на один день. Жёлтые клетки — выходные.
:::

```python
import pandas as pd
daily = pd.Series([6608, 7629, 8417, 6701, 9860, 9061, 6265, 6235, 6568])
print(daily.rolling(7).mean().round(0).tolist())
```

Что получилось: скользящее среднее отстаёт от событий — резкий скачок появится на сглаженной линии не сразу, а «размажется» на неделю. Для поиска тренда это хорошо, для поиска даты события — плохо: дату ищут по сырому ряду.

{{practice: rolling, p-roll, two-lines}}

## Профиль по дням недели

Какой день недели самый выручечный? Соблазнительно сложить выручку по дню недели. Но сумма зависит от того, сколько раз этот день встретился в периоде: в месяце из 31 дня три дня недели повторяются пять раз, остальные — четыре. Правильно сравнивать **среднюю** дневную выручку по дню недели:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
by_dow = daily.groupby(daily.index.dayofweek).agg(["mean", "count"])
by_dow.index = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
print(by_dow.round(0))

fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(by_dow.index, by_dow["mean"])
ax.set_title("Средняя выручка за день")
```

`daily.index.dayofweek` — номер дня недели каждой даты индекса (0 — понедельник); это то же самое, что `.dt.weekday` из урока «Даты и время» главы 2, только у индекса пишут без `.dt`. `count` показывает, сколько дней каждого типа было. В наших данных ровно 13 недель, и каждого дня по 13 — но в отчёте за месяц или квартал так бывает редко. Привычка считать среднее за день защищает от ошибки всегда.

{{practice: dow}}

## События на графике

1 ноября в меню появился сезонный напиток. Отметим это вертикальной линией с подписью — так читатель сразу свяжет изменение на графике с событием:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
smooth = daily.rolling(7).mean()
launch = pd.Timestamp("2026-11-01")

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(smooth.index, smooth.values)
ax.axvline(launch, color="tab:red", linestyle="--")
ax.text(launch, smooth.max(), " сезонный напиток", color="tab:red", va="top")
ax.set_title("Выручка, среднее за 7 дней")
```

`ax.text(x, y, текст)` пишет текст в точке графика; `va="top"` — выравнивание по верхнему краю.

## До и после: честное сравнение

Чтобы оценить эффект события, сравнивают периоды до и после. Правила честного сравнения:

- периоды одинаковой длины;
- в каждом — одинаковый набор дней недели (лучше всего — целые недели);
- сравниваются средние за день, а не суммы.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
before = daily["2026-10-18":"2026-10-31"]
after = daily["2026-11-01":"2026-11-14"]
print(len(before), len(after))
print("до:", round(before.mean()), "после:", round(after.mean()))
print("рост, %:", round((after.mean() / before.mean() - 1) * 100, 1))
```

Срез по датам `daily["2026-10-18":"2026-10-31"]` включает обе границы (у индекса-даты это удобно). Две недели до и две недели после.

::: figure before-after
Две половины по 14 дней вокруг 1 ноября: в каждой по два воскресенья и две субботы, поэтому сравнение средних за день честное.
:::

::: warn
Рост после события не доказывает, что его вызвало событие. В ноябре могло измениться что-то ещё: погода, акции конкурентов, сезон. Аккуратная проверка эффекта — A/B-тест, о нём в главе 5.
:::

::: warn Типичные ошибки
- **Неполная неделя на краю.** Последняя «неделя» из одного дня даёт провал на графике, которого не было.
- **Сравнение сумм периодов разной длины.** Октябрь (31 день) и ноябрь (30) сравнивают средними за день.
- **До/после без учёта дней недели.** Сравнивайте целые недели — иначе разное число выходных создаст «эффект».
- **Окно сглаживания не кратно сезонности.** Окно 5 дней на недельном ритме оставляет «пилу»; берите 7.
- **Две оси без подписей.** На графике с `twinx` читатель не поймёт, какая линия к какой оси.
:::

{{practice: uplift}}

## Две величины, две оси

Иногда хочется на одном графике показать число доставок и долю опозданий. Единицы разные (штуки и проценты), поэтому нужна вторая ось Y — `ax.twinx()`:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
w = ok.set_index("created").resample("W")["late"].agg(["size", "mean"])
w = w.iloc[1:-1]   # без неполных недель по краям

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.bar(w.index, w["size"], width=5, color="lightgray", label="доставок")   # на оси дат ширина столбца — в днях
ax.set_ylabel("доставок за неделю")
ax2 = ax.twinx()
ax2.plot(w.index, w["mean"] * 100, color="tab:red", marker="o")
ax2.set_ylabel("опозданий, %", color="tab:red")
ax.set_title("Доставки и опоздания по неделям")
```

::: tip
Двумя осями легко обмануть: меняя масштаб второй оси, можно «совместить» любые две линии. Подписывайте обе оси и цвета. Если можно обойтись двумя графиками друг под другом — лучше так.
:::

{{practice: twin, index100}}

## Практика

## task: weekly | Недели | warmup

Сложите дневную выручку в недельную (`resample("W")`) и сохраните в `weekly` (Series сумм). В `n_weeks` — сколько недель получилось.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

```

### check
```python
import pandas as _pd
df = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
w = df.set_index('datetime').resample('D')['amount'].sum().resample('W').sum()
got = need('weekly', _pd.Series)
assert len(got) == len(w) and [int(x) for x in got] == [int(x) for x in w], 'weekly — сумма по неделям: daily.resample("W").sum().'
assert need('n_weeks') == len(w), f'n_weeks = {need("n_weeks")}.'
```

### hint
Сначала дневной ряд: `daily = df.set_index("datetime").resample("D")["amount"].sum()`.

### hint
`weekly = daily.resample("W").sum()`, `n_weeks = len(weekly)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
weekly = daily.resample("W").sum()
n_weeks = len(weekly)
```

## task: rolling | Скользящее среднее | warmup

Посчитайте скользящее среднее дневной выручки за 7 дней и сохраните в `smooth`. В `last_smooth` — его последнее значение, округлённое до целого.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

```

### check
```python
import pandas as _pd
df = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
s = df.set_index('datetime').resample('D')['amount'].sum().rolling(7).mean()
got = need('smooth', _pd.Series)
assert len(got) == len(s) and got.isna().sum() == 6, 'smooth — rolling(7).mean(): та же длина, первые 6 значений — NaN.'
assert need('last_smooth') == round(s.iloc[-1]), f'last_smooth = {need("last_smooth")}.'
```

### hint
`daily.rolling(7).mean()`; последнее значение — `.iloc[-1]`.

### hint
Округление до целого — `round(smooth.iloc[-1])`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
smooth = daily.rolling(7).mean()
last_smooth = round(smooth.iloc[-1])
```

## task: p-roll | Сглаженный график | warmup

Соберите программу, которая рисует скользящее среднее числа заказов за 7 дней.

### parsons
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["order_id"].count()
smooth = daily.rolling(7).mean()
fig, ax = plt.subplots(figsize=(9, 3))
ax.plot(smooth.index, smooth.values)
```

### check
```python
ax = ax_of()
assert ax.lines and len(ax.lines[0].get_ydata()) == 91
```

### hint
Сначала дневной ряд, потом сглаживание, потом рисование.

### hint
Число заказов по дням — `["order_id"].count()`: сколько заказов попало в день (а не `sum`, который сложил бы номера заказов).

## task: dow | Лучший день недели | base

Посчитайте **среднюю** дневную выручку по дню недели (`daily.index.dayofweek`, 0 — понедельник) и сохраните в `by_dow` (Series из 7 значений). В `best_dow` — номер дня с наибольшей средней выручкой, в `ratio` — во сколько раз средняя выручка этого дня больше, чем у самого слабого (2 знака).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

```

### check
```python
import pandas as _pd
df = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
daily = df.set_index('datetime').resample('D')['amount'].sum()
m = daily.groupby(daily.index.dayofweek).mean()
got = need('by_dow', _pd.Series)
assert len(got) == 7, 'by_dow — 7 значений, по дню недели.'
assert all(close(a, b) for a, b in zip(got.values, m.values)), 'by_dow — среднее дневной выручки, а не сумма.'
assert need('best_dow') == m.idxmax(), f'best_dow = {need("best_dow")}.'
assert close(need('ratio'), round(m.max() / m.min(), 2)), f'ratio = {need("ratio")}.'
```

### hint
`daily.groupby(daily.index.dayofweek).mean()`.

### hint
`best_dow = int(by_dow.idxmax())`, `ratio = round(by_dow.max() / by_dow.min(), 2)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
by_dow = daily.groupby(daily.index.dayofweek).mean()
best_dow = by_dow.idxmax()
ratio = round(by_dow.max() / by_dow.min(), 2)
```

### explain
Лучший день — суббота (номер 5): в среднем 9 832 ₽ против 6 828 ₽ в четверг, в 1.44 раза больше. Выходные — суббота и воскресенье — заметно выше будней. Это и есть «зубцы» дневного графика.

## task: two-lines | Дни и сглаживание | base

Нарисуйте на одной оси две линии: дневную выручку (серым, `color="lightgray"`, подпись «по дням») и скользящее среднее за 7 дней (подпись «7 дней»). Добавьте легенду.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

```

### check
```python
from matplotlib.colors import to_hex as _hex
ax = ax_of()
assert len(ax.lines) == 2, f'Линий {len(ax.lines)}, а нужно 2.'
labels = [t.get_text() for t in ax.get_legend().get_texts()] if ax.get_legend() else []
assert sorted(labels) == sorted(['по дням', '7 дней']), f'Легенда: {labels}.'
gray = [l for l in ax.lines if _hex(l.get_color()) == _hex('lightgray')]
assert gray and gray[0].get_label() == 'по дням', 'Дневная линия — светло-серая (color="lightgray").'
import math
other = [l for l in ax.lines if l is not gray[0]][0]
ys = list(other.get_ydata())
assert sum(1 for v in ys if isinstance(v, float) and math.isnan(v)) == 6, 'Вторая линия — rolling(7).mean().'
```

### hint
Два вызова `ax.plot(...)` с параметром `label=...`, затем `ax.legend()`.

### hint
Сначала серая дневная линия, потом сглаженная — так сглаженная окажется сверху: `ax.plot(daily.index, daily.rolling(7).mean(), label="7 дней")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(daily.index, daily.values, color="lightgray", label="по дням")
ax.plot(daily.index, daily.rolling(7).mean().values, label="7 дней")
ax.legend()
```

### explain
Серая линия скачет с недельным ритмом, сглаженная — спокойно растёт к ноябрю. Две линии вместе честнее, чем одна сглаженная: читатель видит и тренд, и то, насколько сильно колеблются отдельные дни.

## task: uplift | До и после запуска | base

Сравните среднюю дневную выручку за **три** полные недели до 1 ноября (с 11 по 31 октября) и за три недели после (с 1 по 21 ноября). Сохраните средние в `before_avg`, `after_avg` (округлите до целого) и рост в процентах в `uplift_pct` (1 знак).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

```

### check
```python
import pandas as _pd
df = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
daily = df.set_index('datetime').resample('D')['amount'].sum()
b, a = daily['2026-10-11':'2026-10-31'], daily['2026-11-01':'2026-11-21']
assert need('before_avg') == round(b.mean()) and need('after_avg') == round(a.mean()), f'before_avg, after_avg = {need("before_avg")}, {need("after_avg")}, а нужно {round(b.mean())}, {round(a.mean())}. Обе даты включительно.'
assert close(need('uplift_pct'), round((a.mean() / b.mean() - 1) * 100, 1)), f'uplift_pct = {need("uplift_pct")}.'
```

### hint
`daily["2026-10-11":"2026-10-31"]` — обе даты включаются. Должно получиться по 21 дню.

### hint
Рост: `(after.mean() / before.mean() - 1) * 100`. Средние считайте до округления.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()
before = daily["2026-10-11":"2026-10-31"]
after = daily["2026-11-01":"2026-11-21"]
before_avg = round(before.mean())
after_avg = round(after.mean())
uplift_pct = round((after.mean() / before.mean() - 1) * 100, 1)
```

### explain
Средняя дневная выручка: 7 454 ₽ до 1 ноября и 8 383 ₽ после — рост 12.5 %. Сравниваем ровно по три полные недели: в каждом окне одинаковое число суббот и воскресений, и недельный ритм не создаёт ложного эффекта. Но это всё ещё не доказательство, что рост вызвало событие 1 ноября: в ноябре может расти и сезонный спрос.

## task: full-weeks | Опоздания по полным неделям | plus

По доставкам (время 1–299 минут) посчитайте по неделям (`resample("W")` по `created`) долю опозданий и число **дней** с доставками в неделе. Дни считайте так же, как столбец `count` в разделе «Укрупнить»: сначала дневная сводка `resample("D")`, затем по ней `resample("W").count()` (не `count` по доставкам — это число доставок, а не дней). Оставьте только недели, где доставки были все 7 дней. Сохраните результат в `weekly_late` (Series: неделя → доля опозданий в процентах, 1 знак) и нарисуйте его линией с точками.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
s = o.set_index('created')
share = s.resample('W')['late'].mean()
days = s.resample('W')['late'].apply(lambda x: x.index.normalize().nunique())
want = (share[days == 7] * 100).round(1)
got = need('weekly_late', _pd.Series)
assert len(got) == len(want), f'Недель {len(got)}, а полных недель {len(want)}. Неполные — первая и последняя.'
assert all(close(a, b) for a, b in zip(got.values, want.values)), 'Значения не совпадают: доля опозданий в процентах, 1 знак.'
ax = ax_of()
assert ax.lines and len(ax.lines[0].get_ydata()) == len(want), 'Нарисуйте weekly_late линией.'
```

### hint
Нужны две недельные сводки: доля опозданий по неделям и число дней в неделе. Число дней — как в примере с `weekly["count"] == 7` из раздела «Укрупнить»: сначала сводка по дням, потом по неделям с `count`.

### hint
`s = ok.set_index("created")`. Доля: `s.resample("W")["late"].mean()`. Дни: `s.resample("D")["late"].mean()` — дневная сводка (в день без доставок там будет `NaN`), затем `.resample("W").count()` — `count` считает только непустые дни.

### hint
Почти готово: `share = s.resample("W")["late"].mean()`, `days = s.resample("D")["late"].mean().resample("W").count()`, `weekly_late = (share[days == ...] * 100).round(1)`, затем `ax.plot(weekly_late.index, weekly_late.values, marker="o")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
s = ok.set_index("created")
share = s.resample("W")["late"].mean()                       # доля опозданий по неделям
days = s.resample("D")["late"].mean().resample("W").count()  # дней с доставками в неделе
weekly_late = (share[days == 7] * 100).round(1)

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(weekly_late.index, weekly_late.values, marker="o")
ax.set_ylabel("опозданий, %")
ax.set_title("Опоздания по неделям")
```

### explain
`resample("W")` режет время на недели, заканчивающиеся воскресеньем, и первая и последняя неделя данных почти всегда неполные. Здесь в первой неделе доставки были 6 дней, в последней — 1 день. Доля опозданий в такой неделе считается по нескольким дням и может прыгнуть на ровном месте, а на графике это выглядит как событие. Фильтр `days == 7` оставляет 12 полных недель, и колебания доли опозданий от 18.4 % до 29.9 % уже можно обсуждать как настоящие.

Почему дни считаем через дневную сводку, а не `s.resample("W")["late"].count()`: так получится число **доставок** в неделе (в полной неделе их больше сотни), а не дней. Типичная ошибка — сравнить его с 7: ни одна неделя не пройдёт фильтр, `weekly_late` окажется пустой.

Другой способ посчитать дни без промежуточной дневной сводки: `s.resample("W")["late"].apply(lambda x: x.index.normalize().nunique())`. Здесь `x` — доставки одной недели, `normalize()` обрезает время до полуночи, `nunique()` считает разные даты.

## task: twin | Две оси | plus

Нарисуйте по дням: число доставок — серыми столбцами на основной оси, долю опозданий как скользящее среднее за 7 дней (`rolling(7)` по дневной доле, %) — красной линией на второй оси (`twinx`). Подпишите обе оси Y: «доставок» и «опозданий, %».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
day = ok.set_index("created").resample("D")["late"].agg(["size", "mean"])

```

### check
```python
assert len(figs) == 1 and len(figs[0].axes) == 2, 'Нужна вторая ось: ax2 = ax.twinx().'
a, b = figs[0].axes
assert len(a.patches) == 91, f'На основной оси должно быть 91 столбец (дни), сейчас {len(a.patches)}.'
assert a.get_ylabel() == 'доставок' and b.get_ylabel() == 'опозданий, %', f'Подписи осей: {a.get_ylabel()!r}, {b.get_ylabel()!r}.'
assert b.lines, 'На второй оси нужна линия.'
import math
ys = list(b.lines[0].get_ydata())
assert sum(1 for v in ys if isinstance(v, float) and math.isnan(v)) == 6 and max(v for v in ys if not math.isnan(v)) > 1, 'Линия — rolling(7).mean() доли опозданий × 100.'
```

### hint
Дневная сводка: `day = ok.set_index("created").resample("D")["late"].agg(["size", "mean"])`.

### hint
`ax.bar(day.index, day["size"], color="lightgray")`; `ax2 = ax.twinx()`; `ax2.plot(day.index, day["mean"].rolling(7).mean() * 100, color="tab:red")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
day = ok.set_index("created").resample("D")["late"].agg(["size", "mean"])

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.bar(day.index, day["size"], color="lightgray")
ax.set_ylabel("доставок")
ax2 = ax.twinx()
ax2.plot(day.index, day["mean"].rolling(7).mean() * 100, color="tab:red")
ax2.set_ylabel("опозданий, %")
```

### explain
Две величины в разных единицах (штуки и проценты) не помещаются на одну ось: доставок в день от 14 до 29, а доля опозданий — проценты. `twinx()` создаёт вторую ось Y справа с общей осью X. Серые столбцы уходят на фон, красная линия — главный сюжет. Скользящее среднее за 7 дней нужно потому, что дневная доля при 14–29 доставках очень шумная: одно опоздание сдвигает её на несколько процентов. Подписи обеих осей обязательны — без них не понять, какая шкала к какой линии относится.

## task: index100 | Рост городов: индекс | star

Чтобы сравнить рост городов с разной выручкой, переведите недельную выручку каждого города в **индекс**: первая полная неделя = 100. Используйте только полные недели (без первой и последней). Сохраните таблицу индексов в `idx` (строки — недели, столбцы — города, первые три буквы `shop_id`), нарисуйте её линиями и сохраните в `leader` город с наибольшим индексом в последней полной неделе.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
df["city"] = df["shop_id"].str[:3]

```

### check
```python
import pandas as _pd
df = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
df['city'] = df['shop_id'].str[:3]
pv = df.pivot_table(index=_pd.Grouper(key='datetime', freq='W'), columns='city', values='amount', aggfunc='sum').iloc[1:-1]
want = pv / pv.iloc[0] * 100
got = need('idx', _pd.DataFrame)
assert got.shape == want.shape, f'Размер idx {got.shape}, а нужно {want.shape}: только полные недели.'
assert all(close(v, 100) for v in got.iloc[0]), 'Первая строка индекса — 100 у всех городов.'
assert all(close(a, b, 1e-6) for a, b in zip(got.values.ravel(), want[got.columns].values.ravel())), 'Значения индекса не совпадают.'
assert need('leader') == want.iloc[-1].idxmax(), f'leader = {need("leader")!r}.'
ax = ax_of()
assert len([l for l in ax.lines if not l.get_label().startswith('_')]) == want.shape[1], 'Нарисуйте линию для каждого города (idx.plot(ax=ax)).'
```

### hint
Недельная выручка по городам — `pivot_table` с `pd.Grouper(key="datetime", freq="W")` (урок «Первый график: matplotlib и pandas»). Полные недели — `.iloc[1:-1]`.

### hint
Деление таблицы на её первую строку делит каждый столбец на своё первое значение: `pv / pv.iloc[0] * 100`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
df["city"] = df["shop_id"].str[:3]
pv = df.pivot_table(index=pd.Grouper(key="datetime", freq="W"), columns="city",
                    values="amount", aggfunc="sum").iloc[1:-1]
idx = pv / pv.iloc[0] * 100
leader = idx.iloc[-1].idxmax()

fig, ax = plt.subplots(figsize=(9, 3.5))
idx.plot(ax=ax, title="Выручка по городам, индекс (первая неделя = 100)")
ax.axhline(100, color="gray", linewidth=0.8)
```

### explain
Индекс отвечает на вопрос «кто растёт быстрее», не смешивая его с «кто больше». На графике абсолютной выручки маленький город выглядел бы плоской линией у дна, а в индексе видно его собственное движение. Но индекс шумит, если база (первая неделя) была случайно низкой или высокой: тогда за базу берут среднее нескольких недель.
