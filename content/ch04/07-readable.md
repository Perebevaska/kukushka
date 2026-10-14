---
title: Понятный график
lead: "График для себя можно нарисовать как угодно. График для коллег и руководителя должен за пять секунд донести одну мысль. Разбираем простые правила, которые превращают «картинку по умолчанию» в понятный аргумент: правильный тип, заголовок-вывод, сортировка, ноль на оси, один акцент и минимум лишнего."
files: [orders_3m.csv, deliveries.csv]
recap:
  - "Тип графика — по вопросу: сравнение → столбцы, динамика → линия, распределение → гистограмма или ящик, связь → рассеяние, доля в целом → столбцы (не круг)."
  - "Заголовок — вывод, а не название: «Пешие курьеры опаздывают в 3 из 4 доставок», а не «Опоздания по типу курьера»."
  - "Столбцы сортируйте по значению и начинайте ось с нуля: `ax.set_ylim(0, …)`. У линии ноль не обязателен."
  - "Один акцентный цвет на сером фоне: `color=[\"tab:red\" if … else \"lightgray\" …]`."
  - "Подписи значений — `ax.bar_label(bars, fmt=\"%.1f\")`; единицы — в подписях осей («тыс. ₽», «%»)."
  - "Меньше лишнего: `ax.spines[[\"top\", \"right\"]].set_visible(False)`; много категорий — топ-N и «прочее»."
  - "Несколько групп — маленькие графики с общей шкалой: `plt.subplots(2, 3, sharey=True)`."
---

## Кому этот график

Графики бывают двух видов. **Исследовательские** вы рисуете для себя десятками, чтобы найти закономерность, — им не нужна красота. **Объясняющие** вы показываете другим, чтобы донести вывод. Для них работает одно правило: **один график — одна мысль**, и читатель должен понять её за несколько секунд.

Дальше — правила для объясняющих графиков. Каждое простое, но вместе они заметно меняют восприятие.

## Тип — по вопросу

| Вопрос | График |
|---|---|
| Кто больше, кто меньше? | столбцы (горизонтальные, если подписи длинные) |
| Как менялось во времени? | линия |
| Как распределены значения? | гистограмма, ящик с усами |
| Связаны ли два числа? | рассеяние |
| Из чего состоит целое? | столбцы с долями или составной столбец |

Круговая диаграмма (pie) — частый выбор для долей, но глаз плохо сравнивает углы и площади секторов. Если секторов больше трёх, столбцы почти всегда понятнее.

::: figure chart-choice
Шпаргалка выбора: сначала формулируем вопрос читателя, потом берём график, который на него отвечает.
:::

### Горизонтальные столбцы: `barh`

Когда категорий много или подписи длинные («флэт уайт», «доставка»), столбцы кладут набок — `ax.barh(подписи, значения)`. Напоминание из урока «Первый график: matplotlib и pandas»: первый элемент `barh` рисуется **внизу**, поэтому, чтобы самый большой оказался наверху, данные сортируют **по возрастанию** (`sort_values()`), а у вертикальных `bar` — по убыванию.

{{practice: no-pie}}

## Заголовок — это вывод

Сравните два заголовка одного и того же графика:

- «Доля опозданий по типу курьера»;
- «Пешие курьеры опаздывают в 3 из 4 доставок».

Первый говорит, **что** нарисовано, — это и так видно по осям. Второй говорит, **что из этого следует**. Руководитель, который прочтёт только заголовок, уже получит главное.

{{practice: title}}

## До и после

Нарисуем «график по умолчанию» и улучшенный:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = (ok.groupby("shop_id")["late"].mean() * 100).round(1)

fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(t.index, t.values)
ax.set_title("late by shop_id")
```

Что не так: подписи на техническом языке, нет единиц, порядок по алфавиту, все столбцы одинаковые — непонятно, куда смотреть.

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = (ok.groupby("shop_id")["late"].mean() * 100).round(1).sort_values(ascending=False)
colors = ["tab:red" if v == t.max() else "lightgray" for v in t.values]

fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.bar(t.index, t.values, color=colors)
ax.bar_label(bars, fmt="%.1f")
ax.set_ylim(0, t.max() * 1.15)
ax.set_ylabel("опозданий, %")
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("KZN-2 опаздывает чаще остальных кофеен")
```

Что изменилось:

1. **Заголовок-вывод** вместо названия.
2. **Сортировка** — столбцы по убыванию, сравнение мгновенное.
3. **Акцент** — один цвет на главное, остальное серое.
4. **Подписи значений** над столбцами — не нужно водить глазами к оси. `fmt="%.1f"` — один знак после запятой.
5. **Единицы** в подписи оси.
6. **Меньше лишнего** — убраны верхняя и правая рамки.

## Ноль на оси столбцов

Длина столбца — это и есть значение. Если ось начинается не с нуля, длины врут:

```python
import matplotlib.pyplot as plt

values = [96.5, 97.2, 98.1]
names = ["Пермь", "Казань", "Тюмень"]
fig, axes = plt.subplots(1, 2, figsize=(9, 3))
axes[0].bar(names, values)
axes[0].set_ylim(96, 98.5)
axes[0].set_title("Ось с 96: Тюмень «в 4 раза лучше»")
axes[1].bar(names, values)
axes[1].set_ylim(0, 100)
axes[1].set_title("Ось с нуля: почти одинаково")
fig.tight_layout()
```

На левом графике разница в 1,6 процентного пункта выглядит огромной. Так случайно — или намеренно — обманывают в презентациях.

::: figure axis-zero
Те же три числа с осью от 96 и от нуля. Слева столбец Тюмени над отметкой 96 в 4.2 раза выше пермского, хотя на деле разница 1.6 п.п.
:::

У **линии** ноль не обязателен: она показывает изменение, а не величину. Если линия выручки колеблется между 9 и 11 тысячами, ось от нуля прижмёт её в полоску.

::: predict
```python static
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.bar(["a", "b"], [96, 98])
ax.set_ylim(0, 100)
lo, hi = ax.get_ylim()
print(lo, hi)
```

- `96.0 98.0`
- [x] `0.0 100.0`
- `0 98`

Почему: `set_ylim` задаёт видимый диапазон оси, и `get_ylim` его возвращает. Так же проверяют графики в задачах этого урока.
:::

::: quiz
Ось Y столбцов начинается с 300, а не с нуля. Средний чек двух кофеен — 320 и 340 ₽. Что увидит читатель?

- [x] Что у второй кофейни чек вдвое больше: над отметкой 300 видны отрезки 20 и 40 ₽, хотя разница 6 %
  > Длина столбца читается как величина. Обрезанная ось раздувает разницу, поэтому столбцы рисуют от нуля.
- [ ] Ничего особенного: подписи же есть
  > Подписи читают не все. Глаз сначала сравнивает длины.
- [ ] Так честнее: виднее разница
  > Видно преувеличенную разницу, а не настоящую.
- [ ] Это правило и для линий
  > Линии допускают обрезанную ось: там читают изменение, а не длину.
:::

{{practice: sort-zero, honest, percent-axis}}

## Много категорий — топ и «прочее»

Двадцать столбцов никто не прочтёт. Оставьте самые важные, остальное сложите в «прочее» (как в уроке «Категоризация: CASE WHEN в pandas»):

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum().sort_values(ascending=False)
top = rev.head(5).copy()
top["прочее"] = rev.iloc[5:].sum()
top = top / 1000

fig, ax = plt.subplots(figsize=(6, 3))
bars = ax.barh(top.index[::-1], top.values[::-1], color="tab:blue")
ax.bar_label(bars, fmt="%.0f")
ax.set_xlabel("выручка, тыс. ₽")
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Пять напитков дают основную выручку")
```

Что здесь происходит:

- `top` идёт по убыванию, а «прочее» — последним. Сортировать по возрастанию нельзя: «прочее» уехало бы со своего места внизу;
- поэтому порядок просто переворачиваем: `[::-1]` — срез с шагом −1, тот же ряд задом наперёд (`[1, 2, 3][::-1]` → `[3, 2, 1]`). Теперь первым идёт «прочее» — оно внизу, а последним лидер — он наверху (у `barh` первый элемент рисуется внизу, см. раздел «Тип — по вопросу»);
- деление на 1 000 и «тыс. ₽» в подписи — вместо шестизначных чисел.

{{practice: top5}}

## Маленькие графики вместо одного запутанного

Шесть линий на одном графике сливаются в клубок. Лучше шесть маленьких графиков с **общей шкалой** — `sharey=True`, чтобы их можно было сравнивать между собой:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
weekly = df.pivot_table(index=pd.Grouper(key="datetime", freq="W"), columns="shop_id",
                        values="amount", aggfunc="sum").iloc[1:-1]

fig, axes = plt.subplots(2, 3, figsize=(10, 5), sharex=True, sharey=True)
for ax, shop in zip(axes.flat, weekly.columns):
    ax.plot(weekly.index, weekly[shop])
    ax.set_title(shop)
    ax.tick_params(axis="x", labelrotation=45)
fig.suptitle("Недельная выручка кофеен — общая шкала")
fig.tight_layout()
```

Что здесь происходит:

- `pd.Grouper(key="datetime", freq="W")` — группировка по неделям; в ячейке — выручка кофейни за неделю;
- `.iloc[1:-1]` отбрасывает первую и последнюю строки — неполные недели. Неделя здесь — с понедельника по воскресенье, а выгрузка начинается во вторник 1 сентября и кончается в понедельник 30 ноября: в первой неделе шесть дней, в последней — один, и их выручка выглядела бы как провал (урок «Динамика во времени»);
- `sharex=True, sharey=True` — общие шкалы X и Y у всех шести графиков: одинаковая высота линии значит одинаковую выручку;
- `axes.flat` перебирает области сетки 2 × 3 по очереди, `zip` ставит каждой свою кофейню;
- `tick_params(axis="x", labelrotation=45)` наклоняет подписи дат на 45°, чтобы они не налезали друг на друга;
- `suptitle` — общий заголовок над всеми графиками.

::: note Чек-лист перед отправкой
- Заголовок — вывод одной фразой?
- Подписаны оси и единицы?
- Столбцы отсортированы и начинаются с нуля?
- Есть акцент на главном?
- Нет ли лишнего: рамок, легенды для одной серии, десятков категорий?
:::

{{practice: small-multiples}}

## Разберём вместе: переделка графика за пять шагов

Исходник: круговая диаграмма «Выручка по напиткам» — 11 разноцветных секторов, легенда сбоку. Пройдём чек-лист.

1. **Вопрос.** Что хочет понять читатель? «Какие напитки делают выручку». Это сравнение категорий — столбцы, а не круг: глаз сравнивает длины лучше, чем углы.
2. **Числа.** Доли в выручке: латте 17.6 %, капучино 16.1 %, флэт уайт 13.4 %, раф 12.4 %, американо 9.8 %, остальные шесть — от 7.2 % до 2.9 %.
3. **Сократить.** Шесть мелких напитков вместе — 30.7 %. Топ-5 и «прочее» — шесть столбцов вместо одиннадцати секторов.
4. **Порядок и ось.** Горизонтальные столбцы по убыванию сверху вниз, «прочее» — в самом низу, ось от нуля, подпись «доля выручки, %».
5. **Заголовок-вывод.** Не «Выручка по напиткам», а «Латте и капучино — треть выручки» (17.6 + 16.1 = 33.7 %).

::: figure top-other
Переделка на картинке: круг из 11 секторов, где раф и флэт уайт почти не различить, → пять столбцов по убыванию и серое «прочее» внизу.
:::

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum().sort_values(ascending=False)
share = rev / rev.sum() * 100
top = share.head(5).copy()
top["прочее"] = share.iloc[5:].sum()

fig, ax = plt.subplots(figsize=(7, 3.2))
# после [::-1] «прочее» стало первым — ему серый, пяти напиткам — синий
bars = ax.barh(top.index[::-1], top.values[::-1], color=["lightgray"] + ["tab:blue"] * 5)
ax.bar_label(bars, fmt="%.1f")
ax.set_xlabel("доля выручки, %")
ax.set_title("Латте и капучино — треть выручки")
ax.spines[["top", "right"]].set_visible(False)
```

Что получилось: тот же набор чисел, но вывод читается за три секунды, и его можно произнести вслух. «Прочее» покрашено серым — оно нужно для полноты, но не для внимания.

::: warn Типичные ошибки
- **Заголовок-описание.** «Выручка по напиткам» говорит, что нарисовано, а не что из этого следует.
- **Обрезанная ось у столбцов.** Разница в 1.6 п.п. превращается в «в 4 раза».
- **Круг на 11 секторов.** Углы не сравнить; больше 3–4 секторов — столбцы.
- **Радуга без смысла.** Цвет — для акцента; если всё разноцветное, акцента нет.
- **Подписи с лишней точностью.** 17.6342 % — шум; один знак после запятой достаточно.
:::

{{practice: labels, p-accent}}

## Практика

## task: sort-zero | Отсортировать и от нуля | warmup

Исправьте график: столбцы должны идти по убыванию, а ось Y — начинаться с нуля.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
avg = df.groupby("shop_id")["amount"].mean()
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(avg.index, avg.values)
ax.set_ylim(avg.min() - 5, avg.max() + 5)
ax.set_ylabel("средний чек, ₽")
```

### check
```python
ax = ax_of()
h = [p.get_height() for p in ax.patches]
assert h == sorted(h, reverse=True), 'Столбцы должны идти по убыванию.'
assert ax.get_ylim()[0] == 0, f'Ось Y начинается с {ax.get_ylim()[0]}, а должна с нуля.'
```

### hint
`avg.sort_values(ascending=False)` перед рисованием и `ax.set_ylim(0, …)` вместо обрезанной оси.

### hint
Сортировать удобно сразу после группировки: `df.groupby("shop_id")["amount"].mean().sort_values(ascending=False)`. Для нуля по оси: `ax.set_ylim(0, avg.max() * 1.1)` — запас 10 % сверху, чтобы самый высокий столбец не упирался в рамку.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
avg = df.groupby("shop_id")["amount"].mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(avg.index, avg.values)
ax.set_ylim(0, avg.max() * 1.1)
ax.set_ylabel("средний чек, ₽")
```

### explain
Средние чеки кофеен отличаются на несколько процентов. Обрезанная ось превращала это в «разницу в разы».

## task: labels | Подписи значений | warmup

Добавьте над столбцами подписи значений с одним знаком после запятой и уберите верхнюю и правую рамки.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = (ok.groupby("courier")["late"].mean() * 100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(5, 3))
bars = ax.bar(t.index, t.values)
ax.set_ylabel("опозданий, %")
```

### check
```python
ax = ax_of()
texts = [t.get_text() for t in ax.texts]
assert len(texts) == 3, f'Подписей {len(texts)}, а нужно 3: ax.bar_label(bars, fmt="%.1f").'
assert all(len(x.split('.')[-1]) == 1 for x in texts), f'Подписи: {texts} — нужен один знак после запятой.'
assert not ax.spines['top'].get_visible() and not ax.spines['right'].get_visible(), 'Уберите верхнюю и правую рамки.'
```

### hint
`bars = ax.bar(...)` — сохраните результат рисования, он нужен для подписей.

### hint
`ax.bar_label(bars, fmt="%.1f")` и `ax.spines[["top", "right"]].set_visible(False)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = (ok.groupby("courier")["late"].mean() * 100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(5, 3))
bars = ax.bar(t.index, t.values)
ax.set_ylabel("опозданий, %")
ax.bar_label(bars, fmt="%.1f")
ax.spines[["top", "right"]].set_visible(False)
```

### explain
Подписи значений избавляют от необходимости «прикладывать линейку» к оси, а лишние рамки — визуальный шум. Мелочи, но вместе они превращают «график из Excel по умолчанию» в график для руководителя.

## task: p-accent | Акцент на главном | warmup

Соберите программу, которая выделяет красным самый популярный канал продаж, а остальные рисует серым.

### parsons
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv")
vc = df["channel"].value_counts()
colors = ["tab:red" if v == vc.max() else "lightgray" for v in vc.values]
fig, ax = plt.subplots(figsize=(5, 3))
ax.bar(vc.index, vc.values, color=colors)
```

### check
```python
from matplotlib.colors import to_hex as _hex
ax = ax_of()
cols = [_hex(p.get_facecolor()) for p in ax.patches]
assert len(cols) == 3, f'Столбцов {len(cols)}, а каналов продаж 3: ax.bar(vc.index, vc.values, color=colors).'
if cols[0] == _hex('lightgray') and _hex('tab:red') in cols[1:]:
    raise AssertionError('Красный достался не самому большому столбцу. Первый (самый большой) должен быть tab:red, остальные — lightgray. Проверьте генератор списка: "tab:red" — при условии v == vc.max(), "lightgray" — после else.')
assert cols[0] == _hex('tab:red') and all(c == _hex('lightgray') for c in cols[1:]), f'Цвета столбцов: {cols}. Первый (самый большой) должен быть tab:red, остальные — lightgray. Проверьте условие в генераторе списка: v == vc.max(), и что colors передан в ax.bar через color=.'
```

### hint
Цвета нужны до рисования, данные — до цветов.

### hint
Цвета собираются генератором списка: красный — там, где значение равно максимуму, серый — у остальных. Поэтому сначала нужны подсчёты `vc`, потом `colors`, потом `ax.bar`.

## task: no-pie | Круг → столбцы | base

Маркетинг прислал круговую диаграмму долей напитков в выручке. Перерисуйте её горизонтальными столбцами: доля в процентах, самый большой — наверху, подпись оси X — «доля выручки, %», заголовок — любой вывод (не пустой). Круговую диаграмму удалите.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum()
fig, ax = plt.subplots(figsize=(5, 5))
ax.pie(rev.values, labels=rev.index)
```

### check
```python
import pandas as _pd
from matplotlib.patches import Wedge as _W
r = _pd.read_csv('orders_3m.csv').groupby('drink')['amount'].sum()
share = (r / r.sum() * 100).sort_values()
ax = ax_of()
assert not any(isinstance(p, _W) for p in ax.patches), 'На графике остался круг — уберите ax.pie.'
w = [p.get_width() for p in ax.patches]
assert len(w) == len(share), f'Столбцов {len(w)}, а напитков {len(share)}: нужен ax.barh по всем напиткам.'
if all(close(a, b) for a, b in zip(w, share.values[::-1])):
    raise AssertionError('Самый большой столбец оказался внизу: у barh первый элемент рисуется внизу. Чтобы лидер был наверху, сортируйте по возрастанию — .sort_values() без ascending=False.')
if sorted(round(x, 3) for x in w) != sorted(round(x, 3) for x in share.values) and close(max(w), r.max()):
    raise AssertionError('Длины столбцов — выручка в рублях, а нужна доля в процентах: rev / rev.sum() * 100.')
assert all(close(a, b) for a, b in zip(w, share.values)), 'Длины столбцов — доля выручки в процентах по возрастанию снизу вверх (лидер наверху): rev / rev.sum() * 100, затем .sort_values().'
assert ax.get_xlabel() == 'доля выручки, %', f'Подпись оси X: {ax.get_xlabel()!r}.'
assert ax.get_title().strip(), 'Добавьте заголовок-вывод.'
```

### hint
Круг заменяем горизонтальными столбцами: строку с `ax.pie` удалите, вместо неё — `ax.barh`. Длина столбца — доля в процентах, а не рубли.

### hint
Доля: `rev / rev.sum() * 100`. У `barh` первый элемент рисуется внизу, поэтому для «лидер наверху» сортируйте **по возрастанию** — `.sort_values()`.

### hint
```python
share = (rev / rev.sum() * 100).sort_values()
fig, ax = plt.subplots(figsize=(6, 4))
ax.barh(share.index, ...)
ax.set_xlabel(...)
ax.set_title(f"{share.index[-1]} — ...")
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum()
share = (rev / rev.sum() * 100).sort_values()
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.barh(share.index, share.values)
ax.bar_label(bars, fmt="%.1f")
ax.set_xlabel("доля выручки, %")
ax.set_title(f"{share.index[-1]} — лидер по выручке")
ax.spines[["top", "right"]].set_visible(False)
```

### explain
Горизонтальные столбцы, отсортированные по доле, сразу дают рейтинг: латте (17.6 %) и капучино (16.1 %) впереди, эспрессо (2.9 %) — последний. Круговая диаграмма с одиннадцатью секторами не позволяла даже отличить латте от капучино.

## task: title | Заголовок-вывод | base

Нарисуйте медианное время доставки по типу курьера (время 1–299 минут, столбцы по убыванию) и сделайте заголовок-вывод, который **вычисляется из данных**: «<тип> — самые медленные: медиана N мин», где тип и N берутся из таблицы (N — целое). Подпишите ось Y: «минут».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
m = ok.groupby('courier')['actual_min'].median().sort_values(ascending=False)
ax = ax_of()
want = f'{m.index[0]} — самые медленные: медиана {int(m.iloc[0])} мин'
assert ax.get_title() == want, f'Заголовок: {ax.get_title()!r}, а нужно {want!r}.'
assert uses_fstring(), 'Соберите заголовок f-строкой из данных, а не впишите руками.'
h = [p.get_height() for p in ax.patches]
assert h == sorted(h, reverse=True) and close(h[0], m.iloc[0]), 'Столбцы — медианы по убыванию.'
assert ax.get_ylabel() == 'минут'
```

### hint
`m = ok.groupby("courier")["actual_min"].median().sort_values(ascending=False)`; первый — `m.index[0]`, значение — `int(m.iloc[0])`.

### hint
Заголовок f-строкой: `ax.set_title(f"{m.index[0]} — самые медленные: медиана {int(m.iloc[0])} мин")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
m = ok.groupby("courier")["actual_min"].median().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(5, 3))
ax.bar(m.index, m.values)
ax.set_ylabel("минут")
ax.set_title(f"{m.index[0]} — самые медленные: медиана {int(m.iloc[0])} мин")
```

### explain
Заголовок из данных обновится сам, если данные изменятся. Вписанный руками заголовок однажды разойдётся с графиком — и это самая неловкая ошибка в презентации.

## task: top5 | Топ-5 и прочее | base

Соберите Series `top`: выручка пяти самых выручечных напитков и шестой элемент «прочее» — сумма остальных, всё в **тысячах** рублей. Нарисуйте горизонтальные столбцы (самый большой — наверху, «прочее» — внизу), подпись оси X — «выручка, тыс. ₽».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum().sort_values(ascending=False)

```

### check
```python
import pandas as _pd
r = _pd.read_csv('orders_3m.csv').groupby('drink')['amount'].sum().sort_values(ascending=False)
t = need('top', _pd.Series)
assert list(t.index) == list(r.index[:5]) + ['прочее'], f'Индекс top: {list(t.index)}.'
assert close(t['прочее'], r.iloc[5:].sum() / 1000) and close(t.iloc[0], r.iloc[0] / 1000), 'Значения — в тысячах рублей.'
ax = ax_of()
labels = [x.get_text() for x in ax.get_yticklabels()]
assert labels[-1] == r.index[0] and labels[0] == 'прочее', f'Порядок по оси Y снизу вверх: {labels}. Наверху — лидер, внизу — «прочее».'
assert ax.get_xlabel() == 'выручка, тыс. ₽'
```

### hint
`top = rev.head(5).copy()`, затем `top["прочее"] = rev.iloc[5:].sum()` и `top = top / 1000`.

### hint
У `barh` первый элемент внизу — передайте перевёрнутые данные: `top.index[::-1]`, `top.values[::-1]`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_3m.csv")
rev = df.groupby("drink")["amount"].sum().sort_values(ascending=False)
top = rev.head(5).copy()
top["прочее"] = rev.iloc[5:].sum()
top = top / 1000
fig, ax = plt.subplots(figsize=(6, 3))
ax.barh(top.index[::-1], top.values[::-1])
ax.set_xlabel("выручка, тыс. ₽")
```

### explain
Латте, капучино, флэт уайт, раф и американо — 492 тыс. ₽, все остальные вместе — 218 тыс. «Прочее» в конце списка сохраняет полноту (сумма — вся выручка), но не отвлекает от главных напитков.

## task: honest | Честная ось | plus

На слайде «доля доставок вовремя по городам» ось начинается с 70 %, и разница кажется огромной. Нарисуйте два графика рядом: слева — как на слайде (ось Y от 70 до 85), справа — честный (от 0 до 100). Данные — доля доставок без опоздания по городу (город — первые три буквы `shop_id`, время 1–299 минут), в процентах. Заголовки: «Как на слайде» и «С нуля».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["on_time"] = ok["actual_min"] <= ok["promised_min"]
ok["city"] = ok["shop_id"].str[:3]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
v = ((o['actual_min'] <= o['promised_min']).groupby(o['shop_id'].str[:3]).mean() * 100)
assert len(figs) == 1 and len(figs[0].axes) == 2, 'Нужны два графика рядом: plt.subplots(1, 2).'
a, b = figs[0].axes
for ax in (a, b):
    h = sorted(p.get_height() for p in ax.patches)
    assert len(h) == len(v) and all(close(x, y) for x, y in zip(h, sorted(v.values))), 'Высоты — доля вовремя в процентах по городам.'
assert a.get_ylim() == (70.0, 85.0) and a.get_title() == 'Как на слайде', f'Левый: ось {a.get_ylim()}, заголовок {a.get_title()!r}.'
assert b.get_ylim() == (0.0, 100.0) and b.get_title() == 'С нуля', f'Правый: ось {b.get_ylim()}, заголовок {b.get_title()!r}.'
```

### hint
`t = ok.groupby("city")["on_time"].mean() * 100`; `fig, axes = plt.subplots(1, 2, figsize=(9, 3))`.

### hint
Город — `ok["shop_id"].str[:3]`, «вовремя» — `ok["actual_min"] <= ok["promised_min"]`. Границы осей — `axes[0].set_ylim(70, 85)` и `axes[1].set_ylim(0, 100)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["on_time"] = ok["actual_min"] <= ok["promised_min"]
ok["city"] = ok["shop_id"].str[:3]
t = (ok.groupby("city")["on_time"].mean() * 100).sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(9, 3))
for ax, lim, title in zip(axes, [(70, 85), (0, 100)], ["Как на слайде", "С нуля"]):
    ax.bar(t.index, t.values)
    ax.set_ylim(*lim)
    ax.set_title(title)
fig.tight_layout()
```

### explain
`ax.set_ylim(*lim)` — звёздочка раскладывает кортеж `(70, 85)` на два аргумента, как будто написали `set_ylim(70, 85)`.

## task: small-multiples | Маленькие графики | star

Постройте сетку 2 × 3 маленьких графиков: для каждой кофейни — доля опозданий (%) по неделям (только полные недели, без первой и последней), линией. У всех графиков общая шкала Y (`sharey=True`), заголовок каждого — код кофейни, общий заголовок полотна — любой непустой. В `top_avg_shop` сохраните кофейню с самой высокой **средней** недельной долей опозданий (среднее по её полным неделям). Максимум одной недели для этого не годится: в неделе у кофейни бывает всего 9–40 доставок, и одна неудачная неделя — ещё не вывод.

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
w = o.pivot_table(index=_pd.Grouper(key='created', freq='W'), columns='shop_id', values='late', aggfunc='mean').iloc[1:-1] * 100
assert len(figs) == 1 and len(figs[0].axes) == 6, 'Нужна сетка 2 × 3: plt.subplots(2, 3, ...).'
axs = figs[0].axes
assert sorted(a.get_title() for a in axs) == sorted(w.columns), 'Заголовки графиков — коды кофеен.'
assert len({a.get_ylim() for a in axs}) == 1, 'Шкала Y должна быть общей: sharey=True.'
for a in axs:
    s = w[a.get_title()]
    assert a.lines and all(close(x, y) for x, y in zip(a.lines[0].get_ydata(), s.values)), f'Линия {a.get_title()} не совпадает с долей опозданий по полным неделям.'
assert figs[0]._suptitle is not None and figs[0]._suptitle.get_text().strip(), 'Добавьте общий заголовок: fig.suptitle(...).'
assert need('top_avg_shop') == w.mean().idxmax(), f'top_avg_shop = {need("top_avg_shop")!r}: среднее по неделям у каждой кофейни — w.mean(), затем idxmax().'
```

### hint
Таблица «неделя × кофейня»: `ok.pivot_table(index=pd.Grouper(key="created", freq="W"), columns="shop_id", values="late", aggfunc="mean").iloc[1:-1] * 100`.

### hint
`for ax, shop in zip(axes.flat, w.columns):` — рисуйте `w[shop]`. Кофейня-лидер по опозданиям — `w.mean().idxmax()`: среднее по каждому столбцу, затем подпись наибольшего.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
w = ok.pivot_table(index=pd.Grouper(key="created", freq="W"), columns="shop_id",
                   values="late", aggfunc="mean").iloc[1:-1] * 100

fig, axes = plt.subplots(2, 3, figsize=(10, 5), sharex=True, sharey=True)
for ax, shop in zip(axes.flat, w.columns):
    ax.plot(w.index, w[shop])
    ax.set_title(shop)
    ax.tick_params(axis="x", labelrotation=45)
fig.suptitle("Доля опозданий по неделям, %")
fig.tight_layout()
top_avg_shop = w.mean().idxmax()
print(w.mean().round(1).sort_values())
```

### explain
Общая шкала — главное в маленьких графиках: без неё каждый график растянется под свои данные, и маленькая кофейня с колебаниями от 20 до 25 % будет выглядеть так же «драматично», как большая с колебаниями от 10 до 40 %. Средняя недельная доля выше всех у KZN-2 — 33.3 %, следом TMN-1 (30.0 %); у остальных четырёх — 20–23 %. Самая «горячая» отдельная неделя тоже у KZN-2 (45.5 %), но там всего 11–25 доставок в неделю: по одной неделе вывод делать нельзя, по среднему за 12 недель — можно.

## task: percent-axis | Доли с нуля | base

Нарисуйте горизонтальные столбцы: доля заказов по каналам продаж в процентах, самый большой канал — наверху. Ось X — от 0 до 100, подпись оси X — «доля заказов, %». Сохраните в `shares` Series долей (в процентах, 1 знак).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = (_pd.read_csv('orders_3m.csv')['channel'].value_counts(normalize=True) * 100).round(1)
sh = need('shares', _pd.Series)
assert all(close(sh[k], v) for k, v in want.items()), f'shares = {sh.to_dict()}, а нужно {want.to_dict()}.'
ax = ax_of(0)
assert len(ax.patches) == 3, 'Нужно три горизонтальных столбца.'
ws = [p.get_width() for p in ax.patches]
assert ws[-1] == max(ws), 'Самый большой канал должен быть наверху — у barh это последний столбец. Сортируйте по возрастанию: shares.sort_values().'
assert ax.get_xlim()[0] == 0 and ax.get_xlim()[1] == 100, f'Ось X: {ax.get_xlim()}, нужна от 0 до 100.'
assert ax.get_xlabel() == 'доля заказов, %', 'Подпись оси X должна быть «доля заказов, %».'
```

### hint
`shares = (df["channel"].value_counts(normalize=True) * 100).round(1)`; для `barh` отсортируйте по возрастанию — `shares.sort_values()`.

### hint
`ax.set_xlim(0, 100)` и `ax.set_xlabel("доля заказов, %")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("orders_3m.csv")
shares = (df["channel"].value_counts(normalize=True) * 100).round(1)
s = shares.sort_values()
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.barh(s.index, s.values)
ax.set_xlim(0, 100)
ax.set_xlabel("доля заказов, %")
ax.set_title("Почти половина заказов — в зале")
```

### explain
Шкала от 0 до 100 показывает доли честно: зал — 47 %, с собой — 35 %, доставка — 18 %. Обрезанная ось сделала бы разницу между «с собой» и доставкой визуально огромной, а «пустое место» справа напоминает, что это части одного целого.
