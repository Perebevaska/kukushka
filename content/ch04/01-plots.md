---
title: "Первый график: matplotlib и pandas"
lead: "Таблица из сотни чисел почти ничего не говорит, а график показывает рост, провал или выброс за секунду. Знакомимся с matplotlib — главной библиотекой графиков в Python: линия, столбцы, подписи, несколько графиков рядом. И с короткой записью через pandas."
files: [orders_3m.csv]
recap:
  - "`import matplotlib.pyplot as plt`; `fig, ax = plt.subplots(figsize=(8, 4))` — полотно `fig` и область графика `ax`."
  - "Линия — `ax.plot(x, y)`, столбцы — `ax.bar(x, высоты)`, горизонтальные столбцы — `ax.barh(y, длины)`."
  - "Подписи: `ax.set_title(...)`, `ax.set_xlabel(...)`, `ax.set_ylabel(...)`."
  - "Короткая запись через pandas: `s.plot(kind=\"bar\", ax=ax)`; `kind` — `\"line\"`, `\"bar\"`, `\"barh\"`, `\"hist\"`, `\"box\"`, `\"scatter\"`."
  - "Подписи значений над столбцами: `bars = ax.bar(...)`, затем `ax.bar_label(bars)`; цвет — `color=` (один цвет или список, по цвету на столбец)."
  - "Несколько графиков: `fig, axes = plt.subplots(1, 2, figsize=(10, 4))`, затем `axes[0]`, `axes[1]`."
  - "У столбчатой диаграммы сортируйте столбцы по значению — так сравнивать легче."
---

## Зачем графики

В главах 2–3 мы смотрели на данные таблицами. Таблица хороша, когда нужно точное число. Но вопросы «растёт ли выручка», «есть ли провалы», «какая кофейня выбивается» таблица отвечает плохо: глазу приходится сравнивать десятки чисел.

График отвечает на такие вопросы сразу. Поэтому **исследовательский анализ данных** (EDA, Exploratory Data Analysis) — первый взгляд на новые данные — почти всегда начинается с картинок. Им и посвящена эта глава.

## matplotlib: полотно и оси

Графики в Python рисует библиотека **matplotlib**. Общепринятое сокращение — `plt`. Начинаем всегда одинаково:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 3))
ax.plot([1, 2, 3, 4], [10, 30, 20, 40])
ax.set_title("Первый график")
```

Здесь два объекта:

- `fig` (figure) — **полотно**, вся картинка целиком. `figsize=(7, 3)` — её размер: ширина и высота в дюймах;
- `ax` (axes) — **область графика** на полотне: оси, линии, подписи. Почти всё рисование — это методы `ax`.

`ax.plot(x, y)` соединяет точки линией: первая точка (1, 10), вторая (2, 30) и так далее.

::: figure plt-anatomy
Тот же график по частям: полотно `fig` — вся картинка, область `ax` — рамка с осями; заголовок, линия и подписи осей — методы `ax`.
:::

::: tip Аналогия
`fig` — лист бумаги, `ax` — рамка для рисунка на этом листе. На одном листе можно начертить одну рамку или несколько, и рисовать каждый раз в конкретной рамке. Где аналогия хромает: размер «листа» задают в дюймах через `figsize`, а рамки matplotlib раскладывает по листу сам.
:::

В Jupyter и в этом курсе график показывается сам после запуска ячейки. В обычном скрипте `.py` в конце пишут `plt.show()` — у нас эта строка тоже работает, но не обязательна.

::: predict
```python static
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.bar(["a", "b", "c"], [5, 3, 8])
print(len(ax.patches))
```

- `1`
- [x] `3`
- `16`

Почему: каждый столбец — отдельная фигура (patch) на оси. Столбцов три — фигур три. Так же проверяют графики в задачах курса.
:::

{{practice: p-plot}}

## Линия: динамика

Линейный график — для того, что меняется во времени. Выручка сети по дням: сначала сгруппируем заказы по дням (урок «Даты и время» главы 2), потом нарисуем:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(daily.index, daily.values)
ax.set_title("Выручка сети по дням")
ax.set_xlabel("дата")
ax.set_ylabel("выручка, ₽")
```

Сразу видно, что выручка скачет вверх-вниз с недельным ритмом, а в ноябре она выше. «Зубцы» пилы — выходные: в субботу и воскресенье заказов больше. Подробнее — в уроке «Динамика во времени».

`daily.index` — даты (подписи по оси X), `daily.values` — числа (высота точек).

{{practice: line}}

## Столбцы: сравнение

Столбчатая диаграмма — для сравнения категорий: кофеен, напитков, каналов.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
by_shop = df.groupby("shop_id")["amount"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(by_shop.index, by_shop.values)
ax.set_title("Выручка по кофейням за осень")
ax.set_ylabel("выручка, ₽")
```

`sort_values` перед графиком — важная привычка. Столбцы, стоящие по убыванию, сравнивать гораздо легче, чем стоящие по алфавиту.

**Подписи значений и цвет.** Читателю отчёта часто нужно точное число, а не «примерно 180 тысяч по оси». Его пишут прямо над столбцом. Для этого пригодится то, что `ax.bar` не только рисует, но и **возвращает** набор нарисованных столбцов. Сохраним его в переменную и отдадим в `ax.bar_label`:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
by_shop = df.groupby("shop_id")["amount"].sum().sort_values(ascending=False)
colors = ["tab:orange"] + ["lightgray"] * (len(by_shop) - 1)

fig, ax = plt.subplots(figsize=(7, 3.5))
bars = ax.bar(by_shop.index, by_shop.values, color=colors)  # bars — все 6 столбцов
ax.bar_label(bars)                                          # число над каждым
ax.set_title("PRM-1 — лидер по выручке")
```

Что здесь происходит:

- `bars = ax.bar(...)` — столбцы нарисованы, и их набор сохранён в `bars` (тип `BarContainer`, по элементу на столбец);
- `ax.bar_label(bars)` — над каждым столбцом из `bars` пишет его высоту: 186163, 181365, …;
- `color=colors` — список цветов, по одному на столбец, в том же порядке. Первый столбец (лидер) оранжевый, остальные серые. Можно передать и один цвет: `color="tab:orange"` — тогда все столбцы одного цвета.

На графике видно: PRM-1 и KZN-1 почти вровень, по 181–186 тыс., у остальных кофеен — от 72 до 98 тыс., примерно вдвое меньше.

Когда подписей много или они длинные (названия напитков), удобнее горизонтальные столбцы — `barh`. Подписи тогда читаются без поворота:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
by_drink = df.groupby("drink")["amount"].sum().sort_values()

fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(by_drink.index, by_drink.values)
ax.set_title("Выручка по напиткам")
ax.set_xlabel("выручка, ₽")
```

У `barh` первый столбец рисуется внизу. Поэтому сортируем по возрастанию: самый большой окажется наверху.

::: quiz
Нужно показать выручку по дням за три месяца. Линия или столбцы?

- [x] Линия: дни идут по порядку, и глаз читает форму — рост, провалы, недельный ритм
  > Линию выбирают для упорядоченной оси, обычно времени. Соседние точки связаны, и важна динамика.
- [ ] Столбцы: так точнее видна каждая сумма
  > Девяносто узких столбцов сольются в «забор», и общая форма читается хуже. Столбцы хороши для сравнения нескольких категорий.
- [ ] Круговая диаграмма: доля каждого дня
  > Девяносто секторов не прочитать, да и вопрос про динамику, а не про доли.
- [ ] Неважно, это дело вкуса
  > Тип графика определяет вопрос: «как менялось» — линия, «кто больше» — столбцы.
:::

{{practice: bar-shop, barh, labeled, highlight}}

## Короткая запись: pandas.plot

У Series и DataFrame есть метод `plot` — он вызывает matplotlib сам. Тип графика задаёт параметр `kind`:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
fig, ax = plt.subplots(figsize=(6, 3))
df["channel"].value_counts().plot(kind="bar", ax=ax, title="Заказы по каналам", rot=0)
ax.set_ylabel("заказов")
```

- `ax=ax` — нарисовать на нашей области (иначе pandas создаст свою);
- `title` — заголовок;
- `rot=0` — не поворачивать подписи по оси X.

`plot` удобен для быстрого взгляда. Тонкую настройку (подписи, цвета) по-прежнему делают через `ax`.

| `kind` | График | Когда |
|---|---|---|
| `"line"` | линия | динамика во времени |
| `"bar"`, `"barh"` | столбцы | сравнение категорий |
| `"hist"` | гистограмма | распределение чисел (урок «Распределения и гистограммы») |
| `"box"` | ящик с усами | распределение и выбросы (урок «Ящик с усами и выбросы») |
| `"scatter"` | точки | связь двух чисел (урок «Связи: рассеяние и корреляция») |

{{practice: pandas-plot}}

## Несколько линий и несколько графиков

Если у DataFrame несколько столбцов, `plot` нарисует линию для каждого и добавит легенду. Выручка по месяцам в каждом городе:

```python
import pandas as pd
import matplotlib.pyplot as plt

orders = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
orders["month"] = orders["datetime"].dt.to_period("M").astype(str)
orders["city"] = orders["shop_id"].str[:3]
pv = orders.pivot_table(index="month", columns="city", values="amount", aggfunc="sum")

fig, ax = plt.subplots(figsize=(7, 3.5))
pv.plot(ax=ax, marker="o", title="Выручка по городам")
ax.set_ylabel("выручка, ₽")
```

Что здесь происходит:

- `dt.to_period("M")` превращает дату в месяц (`2026-09`), а `astype(str)` — в обычную строку `"2026-09"`. Строки pandas подписывает по оси X как есть, по одной на точку — так подписи месяцев получаются ровными;
- `pivot_table(index="month", columns="city", ...)` — строки-месяцы, **столбец на каждый город** (как сводная таблица в Excel). `plot` у DataFrame рисует по линии на столбец, поэтому линий столько же, сколько городов, и легенду pandas добавляет сам;
- `marker="o"` — кружок в каждой точке. Точек всего три (месяца), и без кружков не видно, где они.

А если нужны не месяцы, а **недели**? Отдельную колонку можно не делать: в `index` вместо имени колонки передают `pd.Grouper(key="datetime", freq="W")` — «сгруппируй колонку `datetime` по неделям». Это тот же `resample("W")`, только внутри `pivot_table` или `groupby`:

```python
import pandas as pd

orders = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
orders["city"] = orders["shop_id"].str[:3]
weekly = orders.pivot_table(index=pd.Grouper(key="datetime", freq="W"),
                            columns="city", values="amount", aggfunc="sum")
print(weekly.shape)
print(weekly.head(3))
```

`weekly.shape` — `(14, 4)`: 14 строк-недель и 4 столбца-города; дата в строке — воскресенье, которым неделя заканчивается.

Чтобы поставить два графика рядом, у `subplots` указывают число строк и столбцов. Тогда `axes` — массив областей:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
df["size"].value_counts().sort_index().plot(kind="bar", ax=axes[0], title="Размеры", rot=0)
df["channel"].value_counts().plot(kind="bar", ax=axes[1], title="Каналы", rot=0)
fig.tight_layout()
```

`fig.tight_layout()` раздвигает графики, чтобы подписи не наезжали друг на друга.

::: figure subplots-grid
Что возвращает `plt.subplots`: одну область `ax`, ряд `axes[0]`, `axes[1]` или сетку, где область берут по двум номерам — строке и столбцу.
:::

::: sql
Почти любой график — это результат `GROUP BY`, нарисованный картинкой. Сначала в pandas получаем маленькую таблицу-итог, потом рисуем её. Рисовать сырые 2000 строк приходится редко.
:::

{{practice: two, cities}}

## Разберём вместе: от вопроса к графику

Управляющий спрашивает: «Какой размер стакана нам выгоднее?» Пройдём путь от вопроса до картинки по шагам.

1. **Какая таблица-итог нужна?** Выручка по размерам и число заказов: `groupby("size")["amount"].agg(["sum", "count"])`.
2. **Посмотрим на числа:**

| размер | заказов | выручка, ₽ | средний чек, ₽ |
|---|---|---|---|
| S | 641 | 170 730 | 266 |
| M | 1 036 | 368 750 | 356 |
| L | 412 | 170 715 | 414 |

3. **Какой график?** Сравниваем три категории — столбцы. Порядок — не по убыванию, а естественный S, M, L: у размеров есть свой порядок, и читатель его ждёт.
4. **Что подписать?** Заголовок-вывод и ось «выручка, ₽».

::: figure rows-to-chart
Путь от сырых строк к картинке: 2 089 заказов → `groupby("size")` → таблица-итог из трёх строк → три столбца.
:::

Что видно уже из таблицы: S и L приносят почти одинаковую выручку (по 171 тыс.), но L — на 229 заказов меньше. Каждый заказ L в полтора раза дороже S. Отсюда вопрос для маркетинга: что если предлагать L чаще? График должен показать эту мысль сразу — поэтому два графика рядом: выручка и средний чек.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
by = df.groupby("size")["amount"].agg(["sum", "mean"]).reindex(["S", "M", "L"])
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
axes[0].bar(by.index, by["sum"])
axes[0].set_title("Выручка: S и L вровень")
axes[1].bar(by.index, by["mean"], color="tab:orange")
axes[1].set_title("Средний чек: L в 1.5 раза дороже S")
fig.tight_layout()
```

::: warn Типичные ошибки
- **Линия для категорий.** Линия соединяет точки и намекает на порядок и время; для кофеен и напитков — столбцы.
- **Столбцы по алфавиту.** Сортируйте по значению, если у категорий нет своего порядка; если есть (S, M, L; дни недели) — держите его.
- **Нет подписей.** График без заголовка и единиц по оси читатель расшифровывает сам — и часто ошибается.
- **Рисовать сырые строки.** 2000 точек заказов — шум; сначала `groupby`, потом график.
- **Новое полотно не создано.** Без `plt.subplots()` следующий график ляжет поверх предыдущего.
:::

## Практика

## task: line | Выручка по дням | warmup

Нарисуйте линию выручки сети по дням с заголовком «Выручка по дням».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

```

### check
```python
ax = ax_of()
assert ax.lines, 'На графике нет линии. Используйте ax.plot(...).'
y = list(ax.lines[0].get_ydata())
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime']).set_index('datetime').resample('D')['amount'].sum()
assert len(y) == len(d) and [float(v) for v in y] == [float(v) for v in d.values], 'Линия должна показывать выручку по дням — значения daily.'
assert ax.get_title() == 'Выручка по дням', f'Заголовок: {ax.get_title()!r}.'
```

### hint
Выручка по дням — `df.set_index("datetime").resample("D")["amount"].sum()`, как в теории.

### hint
`fig, ax = plt.subplots(figsize=(9, 3.5))`, затем `ax.plot(daily.index, daily.values)` и `ax.set_title(...)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
daily = df.set_index("datetime").resample("D")["amount"].sum()

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(daily.index, daily.values)
ax.set_title("Выручка по дням")
```

## task: bar-shop | Заказы по кофейням | warmup

Нарисуйте столбчатую диаграмму: число заказов по кофейням, столбцы — по убыванию. Подпишите ось Y: «заказов».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv')['shop_id'].value_counts()
ax = ax_of()
h = [p.get_height() for p in ax.patches]
assert len(h) == len(want), f'Столбцов {len(h)}, а кофеен {len(want)}.'
assert sorted(h, reverse=True) == sorted(want.values, reverse=True), 'Высоты столбцов должны быть числом заказов.'
assert h == sorted(h, reverse=True), 'Отсортируйте столбцы по убыванию.'
assert ax.get_ylabel() == 'заказов', f'Подпись оси Y: {ax.get_ylabel()!r}.'
```

### hint
Число заказов по кофейням — `df["shop_id"].value_counts()`.

### hint
`value_counts()` уже сортирует по убыванию. Дальше `ax.bar(s.index, s.values)` и `ax.set_ylabel("заказов")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
counts = df["shop_id"].value_counts()

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.bar(counts.index, counts.values)
ax.set_ylabel("заказов")
```

## task: p-plot | Соберите график | warmup

Соберите программу, которая рисует средний чек по каналам продаж.

### parsons
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv")
avg = df.groupby("channel")["amount"].mean()
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(avg.index, avg.values)
ax.set_title("Средний чек по каналам")
```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv').groupby('channel')['amount'].mean()
ax = ax_of()
h = [round(p.get_height(), 6) for p in ax.patches]
assert len(h) == len(want), f'Столбцов {len(h)}, а каналов {len(want)}. Рисует строка ax.bar(...) — она должна идти после plt.subplots.'
assert h == [round(v, 6) for v in want.values], 'Высоты столбцов не совпадают со средним чеком по каналам: avg должен быть посчитан до строки с ax.bar.'
assert ax.get_title() == 'Средний чек по каналам', f'Заголовок {ax.get_title()!r}: строка с set_title должна идти после plt.subplots.'
```

### hint
Сначала данные, потом полотно, потом рисование и подпись.

### hint
Порядок: импорты → `read_csv` → средний чек `avg` → `plt.subplots` → строка с `ax.bar(...)` → `ax.set_title(...)`. Рисовать на `ax` можно только после того, как `plt.subplots` его создал.

## task: barh | Напитки горизонтально | base

Нарисуйте горизонтальные столбцы: число заказов по каждому напитку. Самый популярный напиток — наверху. Заголовок — «Заказы по напиткам».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
vc = _pd.read_csv('orders_3m.csv')['drink'].value_counts()
ax = ax_of()
w = [p.get_width() for p in ax.patches]
assert len(w) == len(vc), f'Столбцов {len(w)}, а напитков {len(vc)}. Нужен ax.barh.'
assert sorted(w) == sorted(vc.values), 'Длины столбцов — число заказов напитка.'
assert w == sorted(w), 'Самый популярный должен быть наверху: у barh первый столбец — внизу, поэтому сортируйте по возрастанию.'
assert ax.get_title() == 'Заказы по напиткам', f'Заголовок: {ax.get_title()!r}.'
```

### hint
`ax.barh(s.index, s.values)`. У `barh` первый элемент рисуется внизу.

### hint
`df["drink"].value_counts().sort_values()` — по возрастанию, тогда самый большой окажется последним, то есть наверху.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
counts = df["drink"].value_counts().sort_values()

fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(counts.index, counts.values)
ax.set_title("Заказы по напиткам")
```

### explain
Наверху — капучино (365 заказов) и латте (345), внизу — сезонный напиток и матча (по 81–82). Горизонтальные столбцы позволяют прочитать длинные названия без поворота, а сортировка превращает график в рейтинг: первая строка — главный ответ.

## task: pandas-plot | Через pandas | base

Нарисуйте выручку по размерам напитка (S, M, L — в этом порядке) через `plot(kind="bar")` у Series. Заголовок передайте параметром `title="Выручка по размерам"`.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv').groupby('size')['amount'].sum().reindex(['S', 'M', 'L'])
ax = ax_of()
h = [p.get_height() for p in ax.patches]
assert h == [float(v) for v in want.values], f'Высоты: {h}. Нужна выручка по размерам в порядке S, M, L.'
labels = [t.get_text() for t in ax.get_xticklabels()]
assert labels == ['S', 'M', 'L'], f'Подписи по оси X: {labels}. Порядок S, M, L задаётся через reindex(["S", "M", "L"]).'
assert ax.get_title() == 'Выручка по размерам'
assert '.plot(' in _code, 'Нарисуйте через метод plot у Series.'
```

### hint
`df.groupby("size")["amount"].sum()` отсортирует размеры по алфавиту (L, M, S). Нужный порядок — `.reindex(["S", "M", "L"])`.

### hint
`s.plot(kind="bar", ax=ax, title="Выручка по размерам", rot=0)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
by_size = df.groupby("size")["amount"].sum().reindex(["S", "M", "L"])

fig, ax = plt.subplots(figsize=(5, 3))
by_size.plot(kind="bar", ax=ax, title="Выручка по размерам", rot=0)
```

### explain
M приносит больше выручки, чем S и L вместе (369 тыс. против 341 тыс.), а S и L — почти поровну, по 171 тыс. Порядок S, M, L важнее сортировки по значению: читатель сразу видит «средний размер — главный», а не гадает, где какой.

## task: two | Два графика рядом | base

Постройте полотно с двумя графиками рядом: слева — число заказов по часу дня (`dt.hour`, линия), справа — число заказов по дню недели (`dt.dayofweek`, столбцы). Заголовки: «По часам» и «По дням недели».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
assert len(figs) == 1 and len(figs[0].axes) == 2, 'Нужно одно полотно с двумя графиками: plt.subplots(1, 2).'
a, b = figs[0].axes
assert a.get_title() == 'По часам' and b.get_title() == 'По дням недели', f'Заголовки: {a.get_title()!r}, {b.get_title()!r}.'
hh = d['datetime'].dt.hour.value_counts().sort_index()
assert a.lines and [float(v) for v in a.lines[0].get_ydata()] == [float(v) for v in hh.values], 'Слева — линия: число заказов по часу, по возрастанию часа.'
ww = d['datetime'].dt.dayofweek.value_counts().sort_index()
assert [p.get_height() for p in b.patches] == [float(v) for v in ww.values], 'Справа — столбцы: заказы по дню недели (0 — понедельник), по порядку дней.'
```

### hint
`fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))`, затем рисуйте на `axes[0]` и `axes[1]`.

### hint
Счёт по часу в порядке часов: `df["datetime"].dt.hour.value_counts().sort_index()`.

### hint
```python static
by_hour = df["datetime"].dt.hour.value_counts().sort_index()
by_day = ...  # то же для dt.dayofweek
fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
axes[0].plot(by_hour.index, by_hour.values)
axes[0].set_title("По часам")
axes[1].bar(...)
axes[1].set_title(...)
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
by_hour = df["datetime"].dt.hour.value_counts().sort_index()
by_day = df["datetime"].dt.dayofweek.value_counts().sort_index()

fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
axes[0].plot(by_hour.index, by_hour.values)
axes[0].set_title("По часам")
axes[1].bar(by_day.index, by_day.values)
axes[1].set_title("По дням недели")
fig.tight_layout()
```

### explain
Слева два пика: утро (9 ч — 255 заказов, больше всего за день) и обед (13 ч — 202). Вечером заказов меньше: в 18 ч — 155. Справа — рост к выходным: в субботу 380 заказов и в воскресенье 358 против 260–277 в будни. Из таблицы это пришлось бы вычитывать долго, на графике видно сразу.

Типичная ошибка — забыть `sort_index()`: `value_counts()` упорядочит часы по числу заказов (9, 10, 13, …), и линия начнёт прыгать по оси X туда-обратно.

## task: cities | Линии по городам | plus

Нарисуйте выручку по **неделям** отдельной линией для каждого города (город — первые три буквы `shop_id`, колонка `city` уже есть в заготовке). Нужна таблица «строки — недели, столбцы — города» и `plot` у DataFrame, который нарисует по линии на город. Неделю можно взять любым способом: `pd.Grouper` из раздела «Несколько линий и несколько графиков» или колонкой `df["datetime"].dt.to_period("W")`. Заголовок — «Выручка по неделям», легенда с городами.

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
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
d['city'] = d['shop_id'].str[:3]
w = d.pivot_table(index=_pd.Grouper(key='datetime', freq='W'), columns='city', values='amount', aggfunc='sum')
ax = ax_of()
assert len(ax.lines) == w.shape[1], f'Линий {len(ax.lines)}, а городов {w.shape[1]}.'
got = sorted(sum(float(v) for v in l.get_ydata()) for l in ax.lines)
assert all(abs(a - b) < 1e-6 for a, b in zip(got, sorted(w.sum().values))), 'Сумма значений линий не совпадает с выручкой городов.'
assert all(len(l.get_ydata()) == len(w) for l in ax.lines), f'В каждой линии должно быть {len(w)} недель.'
assert ax.get_title() == 'Выручка по неделям', f'Заголовок: {ax.get_title()!r}.'
assert ax.get_legend() is not None, 'Нужна легенда — какой город какой линией.'
```

### hint
Это тот же пример «Выручка по городам» из теории, только вместо месяцев — недели. Сначала сводная таблица (строки — недели, столбцы — города), потом одна строка `plot`.

### hint
`pivot_table(index=..., columns="city", values="amount", aggfunc="sum")`. В `index` — неделя: `pd.Grouper(key="datetime", freq="W")`. Легенду `plot` у DataFrame добавит сам.

### hint
```python static
pv = df.pivot_table(index=pd.Grouper(key="datetime", freq="W"),
                    columns=..., values=..., aggfunc="sum")
fig, ax = plt.subplots(figsize=(9, 3.5))
pv.plot(ax=ax, title=...)
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
df["city"] = df["shop_id"].str[:3]
pv = pd.pivot_table(df, index=pd.Grouper(key="datetime", freq="W"),
                    columns="city", values="amount", aggfunc="sum")

fig, ax = plt.subplots(figsize=(9, 3.5))
pv.plot(ax=ax, title="Выручка по неделям")
ax.set_ylabel("выручка, ₽")
```

### explain
`pd.Grouper(key="datetime", freq="W")` — способ сгруппировать по неделям прямо внутри `pivot_table` или `groupby`, не делая дату индексом. Другие пути тоже верны: колонка недели через `dt.to_period("W")` и `pivot_table` по ней или `groupby("city").resample("W", on="datetime")` → `reset_index()` → `pivot_table` (без `on=` `resample` требует дату в индексе и падает с `TypeError`) — недели получаются те же. В таблице 14 недель и 4 города: KZN и PRM идут вровень и выше всех, UFA — ниже всех. Последняя «неделя» (до 6 декабря) — это один день, 30 ноября, поэтому в конце все линии обрываются вниз; первая неделя тоже неполная (с 1 по 6 сентября). Об этой ловушке — в уроке «Динамика во времени».

## task: highlight | Выделить лучший день | star

Нарисуйте выручку по дням недели столбцами (подписи — «пн», «вт», …, «вс») и выделите столбец с максимальной выручкой другим цветом: все столбцы серые (`"lightgray"`), лучший — `"tab:orange"`. Над каждым столбцом подпишите значение (`ax.bar_label`).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

```

### check
```python
import pandas as _pd
from matplotlib.colors import to_hex as _hex
d = _pd.read_csv('orders_3m.csv', parse_dates=['datetime'])
by = d.groupby(d['datetime'].dt.dayofweek)['amount'].sum()
ax = ax_of()
assert [p.get_height() for p in ax.patches] == [float(v) for v in by.values], 'Высоты — выручка по дням недели, с понедельника.'
labels = [t.get_text() for t in ax.get_xticklabels()]
assert labels == ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'], f'Подписи: {labels}.'
cols = [_hex(p.get_facecolor()) for p in ax.patches]
best = int(by.values.argmax())
assert cols[best] == _hex('tab:orange'), 'Лучший день должен быть оранжевым ("tab:orange").'
assert all(c == _hex('lightgray') for i, c in enumerate(cols) if i != best), 'Остальные столбцы — "lightgray".'
assert len(ax.texts) == 7, f'Подписей значений {len(ax.texts)}, а нужно 7: ax.bar_label(bars).'
```

### hint
Три шага: выручка по `dt.dayofweek` (0 — понедельник, поэтому порядок дней уже верный), список цветов по одному на столбец, график с подписями — как в примере с кофейнями в разделе «Столбцы: сравнение».

### hint
Цвета соберите генератором списка: `["tab:orange" if v == by_day.max() else "lightgray" for v in by_day.values]`. Подписи дней — список `days` первым аргументом `ax.bar`.

### hint
```python static
by_day = df.groupby(df["datetime"].dt.dayofweek)["amount"].sum()
colors = [... for v in by_day.values]
fig, ax = plt.subplots(figsize=(7, 3.5))
bars = ax.bar(days, by_day.values, color=colors)
ax.bar_label(...)
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
by_day = df.groupby(df["datetime"].dt.dayofweek)["amount"].sum()
colors = ["tab:orange" if v == by_day.max() else "lightgray" for v in by_day.values]

fig, ax = plt.subplots(figsize=(7, 3.5))
bars = ax.bar(days, by_day.values, color=colors)
ax.bar_label(bars)
ax.set_title("Лучший день недели — по выручке")
```

### explain
Один цвет-акцент на сером фоне — самый простой способ сказать читателю, куда смотреть. Больше о понятных графиках — в уроке «Понятный график».

## task: labeled | Подписи на столбцах | base

Нарисуйте выручку по каналам продаж столбцами по убыванию и подпишите над каждым столбцом его значение (`ax.bar_label`). Заголовок — любой вывод (не пустой). Сохраните в `top_channel` канал с наибольшей выручкой.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
rev = _pd.read_csv('orders_3m.csv').groupby('channel')['amount'].sum().sort_values(ascending=False)
ax = ax_of(0)
assert len(ax.patches) == 3, f'Столбцов на графике {len(ax.patches)}, а каналов 3.'
hs = [p.get_height() for p in ax.patches]
assert hs == sorted(hs, reverse=True), 'Столбцы должны идти по убыванию.'
assert len(ax.texts) >= 3, 'Не вижу подписей над столбцами — ax.bar_label(bars).'
assert ax.get_title().strip(), 'Добавьте заголовок.'
assert need('top_channel') == rev.index[0], f'top_channel = {need("top_channel")!r}.'
```

### hint
Как в примере с подписями в разделе «Столбцы: сравнение»: сначала выручка по каналам по убыванию, потом столбцы, и набор столбцов, который вернул `ax.bar`, — в `ax.bar_label`.

### hint
`rev = df.groupby("channel")["amount"].sum().sort_values(ascending=False)`. После сортировки лидер стоит первым — `rev.index[0]`.

### hint
```python static
rev = ...
fig, ax = plt.subplots(figsize=(6, 3.5))
bars = ax.bar(rev.index, rev.values)
ax.bar_label(bars)
ax.set_title(...)
top_channel = ...
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv")
rev = df.groupby("channel")["amount"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(6, 3.5))
bars = ax.bar(rev.index, rev.values)
ax.bar_label(bars)
ax.set_title("Зал приносит больше всего выручки")
top_channel = rev.index[0]
```

### explain
Подписи избавляют читателя от сравнения высот «на глаз» и от поиска значений по оси. Заголовок-вывод говорит главное сразу: зал — основной канал, доставка — самый маленький.
