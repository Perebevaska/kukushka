---
title: Картинка — это массив чисел
files: [showcase.npz]
lead: "Над витриной «Зерна» висит камера: если товар закончился, его нужно вовремя допечь. Чтобы научить компьютер видеть пустую ячейку, сначала разбираемся, что такое изображение для Python: таблица чисел-яркостей. Смотрим на кадры, режем, отражаем, считаем простые признаки — и видим, почему сравнивать картинки «пиксель к пикселю» плохо."
recap:
  - "Чёрно-белое изображение — матрица `(высота, ширина)` чисел яркости; цветное — `(высота, ширина, 3)`: красный, зелёный, синий."
  - "Обычный тип — `uint8`, целые 0–255. При арифметике он переполняется (200 + 100 = 44): перед вычислениями переводите в `float`."
  - "Набор картинок — массив `(n, высота, ширина)`; `X[i]` — одна картинка, `X[:, 8:24, 8:24]` — вырезка у всех сразу."
  - "`plt.imshow(img, cmap='gray', vmin=0, vmax=255)` показывает картинку без автоматического растягивания яркости."
  - "Отражение `img[:, ::-1]`, поворот `np.rot90`, яркость `img * k` — простые преобразования и основа аугментации."
  - "Расстояние между картинками по пикселям плохо отражает сходство формы: сдвинутый на 3 пикселя круассан далёк от исходного."
---

## Картинка из чисел руками

Начнём с картинки, которую можно нарисовать в уме. Пусть экран — сетка 5 × 5 клеток, и в каждой клетке записана яркость: 0 — чёрный, 255 — белый. Нарисуем тёмный крест на светлом фоне:

```python
import numpy as np
import matplotlib.pyplot as plt

img = np.full((5, 5), 230, dtype=np.uint8)     # 5 × 5, все клетки светло-серые (230)
img[2, :] = 40                                  # строка 2 (третья сверху) — тёмная
img[:, 2] = 40                                  # столбец 2 — тёмный
print(img)

plt.imshow(img, cmap="gray", vmin=0, vmax=255)
plt.xticks(range(5)); plt.yticks(range(5))
```

**Что здесь происходит:**

- `np.full((5, 5), 230, dtype=np.uint8)` — массив 5 × 5, заполненный числом 230. Первое число формы — высота (строки), второе — ширина (столбцы).
- `img[2, :] = 40` — в строке с номером 2 (нумерация с нуля) все столбцы делаем тёмными. `img[:, 2]` — то же для столбца.
- `plt.imshow(..., cmap="gray")` — рисует массив: каждое число — квадратик соответствующей серости.

::: figure img-axes
Тот же крест 5 × 5 матрицей: номера строк слева, номера столбцов сверху. Начало координат — левый верхний угол, `img[2, 3]` — третья строка сверху, четвёртый столбец.
:::

Напечатанная матрица и картинка — одно и то же, просто в разном виде. Строка `img[0]` — верхний ряд пикселей, `img[:, 0]` — левый столбец, `img[2, 3]` — пиксель в третьей строке и четвёртом столбце. Начало координат — **левый верхний угол**, ось «вниз» идёт первой. Это непривычно после графиков, где ось y смотрит вверх, — и это частая причина путаницы.

::: sql
Картинку можно представить таблицей `pixels(row, col, brightness)` на 25 строк. Тогда «тёмных пикселей» — это `SELECT COUNT(*) FROM pixels WHERE brightness < 100`, а «вырезать центр» — `WHERE row BETWEEN 1 AND 3 AND col BETWEEN 1 AND 3`. numpy делает то же, но хранит пиксели плотной матрицей и считает в сотни раз быстрее.
:::

{{practice: load}}

## Кадр витрины

Камера снимает витрину, а программа нарезает кадр на ячейки — по одной выпечке в каждой. В файле `showcase.npz` 2000 таких вырезок 32 × 32 пикселя с разметкой: пусто, круассан, маффин или печенье. Формат `.npz` — несколько массивов numpy в одном файле.

```python
import numpy as np

d = np.load("showcase.npz")
X, y, classes = d["X"], d["y"], d["classes"]
print(X.shape, X.dtype)          # 2000 картинок 32 × 32
print(classes)                   # номер класса → название
print(np.bincount(y))            # сколько картинок каждого класса
print(X[0, :5, :5])              # левый верхний угол первой картинки
```

**Что здесь происходит:**

- `np.load("showcase.npz")` открывает архив; к массивам внутри обращаются по именам, как к словарю: `d["X"]`, `d["y"]`, `d["classes"]`.
- `X.shape` — `(2000, 32, 32)`: 2000 картинок, у каждой 32 строки и 32 столбца. Набор картинок — трёхмерный массив, первая ось — номер картинки.
- `y` — метка каждой картинки числом 0–3, `classes` — названия: `classes[y[i]]` — название класса картинки `i`.
- `np.bincount(y)` — сколько раз встречается каждое число 0, 1, 2, 3, то есть размер каждого класса.
- `X[0, :5, :5]` — первая картинка, первые 5 строк и 5 столбцов: левый верхний угол.

**Что получилось:** классы примерно равны — по 470–515 картинок. Угол первой картинки — числа около 160–220: светлый поднос.

::: figure img-batch-shape
Набор — стопка из 2000 матриц. Индекс по первой оси выбирает кадр, срезы по второй и третьей режут все кадры сразу, `reshape` превращает набор в таблицу для sklearn.
:::

Каждая картинка — матрица 32 × 32 чисел от 0 (чёрный) до 255 (белый). Тип `uint8` — целое без знака в одном байте: ровно 256 значений, поэтому картинки компактны: весь набор — 2000 × 32 × 32 = 2 млн байт, около 2 МБ. Для вычислений кадры переводят в дробные числа: `float32` занимает 4 байта на число, то есть в 4 раза больше памяти, `float64` — в 8 раз. Как прикинуть память под тысячи настоящих фото с камеры и чем PNG отличается от JPEG — в коротком уроке «Файлы картинок и память».

```python
import numpy as np
import matplotlib.pyplot as plt

d = np.load("showcase.npz")
X, y, classes = d["X"], d["y"], d["classes"]

fig, axes = plt.subplots(4, 6, figsize=(8, 5.5))
for c in range(4):
    for j, i in enumerate(np.flatnonzero(y == c)[:6]):
        ax = axes[c, j]
        ax.imshow(X[i], cmap="gray", vmin=0, vmax=255)
        ax.set_xticks([]); ax.set_yticks([])
    axes[c, 0].set_ylabel(classes[c])
plt.tight_layout()
```

**Что здесь происходит:**

- `plt.subplots(4, 6)` — сетка 4 × 6 маленьких графиков; `axes[c, j]` — график в строке `c`, столбце `j`.
- `np.flatnonzero(y == c)` — номера всех картинок класса `c`; `[:6]` — первые шесть из них.
- `enumerate(...)` даёт пары «позиция в строке сетки `j`, номер картинки `i`».
- `ax.set_xticks([])` убирает подписи осей — для картинок они не нужны.
- `axes[c, 0].set_ylabel(classes[c])` подписывает строку сетки названием класса.

Кадры неидеальны, как в жизни: выпечка лежит не по центру, бывает разного размера, свет то ярче, то тусклее, на части кадров — ценник или край салфетки, на пустом подносе — крошки.

::: tip
`vmin=0, vmax=255` важны: без них `imshow` растягивает яркость каждой картинки на всю шкалу, и тусклый кадр выглядит таким же контрастным, как яркий. Для сравнения кадров между собой шкала должна быть общей.
:::

{{practice: p-show}}

## Цвет

Цветное изображение — три матрицы: красный, зелёный и синий канал (RGB). Массив имеет форму `(высота, ширина, 3)`. Наши кадры уже переведены в оттенки серого — так проще, а для выпечки цвет почти ничего не добавляет.

```python
import numpy as np
import matplotlib.pyplot as plt

img = np.zeros((4, 6, 3), dtype=np.uint8)     # 4 × 6 пикселей, 3 канала
img[:, :2] = [200, 30, 30]                     # красная полоса
img[:, 2:4] = [240, 230, 210]                  # цвет молочной пены
img[:, 4:] = [110, 70, 40]                     # цвет кофе

gray = (0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]).round().astype(np.uint8)
print(img.shape, "→", gray.shape)
print(gray[0])

fig, (a1, a2) = plt.subplots(1, 2, figsize=(6, 2))
a1.imshow(img); a2.imshow(gray, cmap="gray", vmin=0, vmax=255)
```

**Что здесь происходит:**

- `np.zeros((4, 6, 3))` — 4 строки, 6 столбцов и 3 числа в каждом пикселе (красный, зелёный, синий).
- `img[:, :2] = [200, 30, 30]` — всем пикселям первых двух столбцов присваиваем цвет: numpy сам «размножает» тройку чисел на все пиксели среза.
- `img[..., 0]` — красный канал всей картинки (матрица 4 × 6). Многоточие значит «все предыдущие оси».
- Серый = 0.299·R + 0.587·G + 0.114·B — взвешенная сумма трёх каналов. Для красной полосы: 0.299·200 + 0.587·30 + 0.114·30 ≈ 81 — тёмно-серый.

::: figure rgb-gray
Первая строка картинки из примера: три канала по шесть чисел превращаются в одну строку серого. Ярко-красная полоса и полоса цвета кофе в сером почти одинаковы — 81 и 79.
:::

Веса 0.299, 0.587, 0.114 учитывают, что глаз чувствительнее всего к зелёному. Ярко-красный становится тёмно-серым — цветовая информация теряется, остаётся яркость.

{{practice: gray}}

## Срезы и преобразования

Картинка — массив, значит, всё из главы про numpy работает. Срез вырезает фрагмент, шаг −1 отражает, `np.rot90` поворачивает.

```python
import numpy as np
import matplotlib.pyplot as plt

d = np.load("showcase.npz")
X, y = d["X"], d["y"]
img = X[np.flatnonzero(y == 1)[0]]          # первый круассан

views = {
    "исходная": img,
    "центр 16 × 16": img[8:24, 8:24],
    "отражение": img[:, ::-1],
    "поворот 90°": np.rot90(img),
    "ярче": np.clip(img.astype(float) * 1.3, 0, 255).astype(np.uint8),
}
fig, axes = plt.subplots(1, 5, figsize=(10, 2.3))
for ax, (name, v) in zip(axes, views.items()):
    ax.imshow(v, cmap="gray", vmin=0, vmax=255); ax.set_title(name, fontsize=9); ax.axis("off")
```

**Что здесь происходит:**

- `img[8:24, 8:24]` — строки 8…23 и столбцы 8…23: центральный квадрат 16 × 16. Правая граница среза не включается.
- `img[:, ::-1]` — все строки, а столбцы в обратном порядке: зеркальное отражение слева направо. `img[::-1, :]` отразил бы сверху вниз.
- `np.rot90(img)` — поворот на 90° против часовой стрелки.
- «Ярче»: перевод в `float`, умножение, обрезка `np.clip(..., 0, 255)` и возврат в `uint8` — почему именно так, покажет вопрос ниже.
- `views` — словарь «название → картинка»; `zip(axes, views.items())` раскладывает картинки по пяти графикам.

Отражённый или повёрнутый круассан — всё ещё круассан. Это используют при обучении: добавляют в выборку изменённые копии картинок (**аугментация**), чтобы модель не зависела от положения и освещения.

::: predict
```python static
import numpy as np
img = np.array([[200, 100]], dtype=np.uint8)
print(img + 100)
```

- `[[300 200]]`
- [x] `[[ 44 200]]`
- `[[255 200]]`

Почему: `uint8` хранит только 0–255, и при переполнении счёт идёт по кругу: 300 − 256 = 44. Numpy не ругается. Поэтому перед арифметикой — `img.astype(float)`, а обратно — через `np.clip(..., 0, 255)`.
:::

::: predict
```python static
import numpy as np
X = np.zeros((2000, 32, 32), dtype=np.uint8)
print(X[:, 8:24, 8:24].shape, X[5].shape)
```

- `(16, 16) (32, 32)`
- [x] `(2000, 16, 16) (32, 32)`
- `(2000, 16, 16) (2000, 32)`

Почему: срез `X[:, 8:24, 8:24]` берёт **все** картинки (первая ось — `:`) и у каждой вырезает центр 16 × 16. `X[5]` — одна картинка целиком. Одной строкой кода можно обрезать сразу весь набор.
:::

{{practice: crop, overflow, cells}}

## Признаки из пикселей

Простейший признак кадра — средняя яркость. Пустой поднос светлее, но разница с выпечкой небольшая: выпечка занимает лишь часть кадра.

```python
import numpy as np
import pandas as pd

d = np.load("showcase.npz")
X, y, classes = d["X"].astype(float), d["y"], d["classes"]
names = classes[y]

mean_br = X.reshape(len(X), -1).mean(axis=1)            # средняя яркость кадра
dark = (X < 100).reshape(len(X), -1).mean(axis=1)        # доля тёмных пикселей
print(pd.DataFrame({"яркость": mean_br, "тёмных": dark}).groupby(names).median().round(3))
```

**Что здесь происходит:**

- `X.reshape(len(X), -1)` — каждую картинку 32 × 32 вытягиваем в строку из 1024 чисел; `-1` значит «посчитай сам». Получается таблица 2000 × 1024 «объекты × признаки» — с такой работает sklearn.
- `.mean(axis=1)` — среднее по строке, то есть по всем пикселям одной картинки.
- `X < 100` — массив `True/False` той же формы: тёмный пиксель или нет. Среднее от `True/False` — доля `True`: `True` считается как 1, `False` — как 0.
- `groupby(names).median()` — медиана признаков по каждому классу, как `GROUP BY` в SQL.

Доля тёмных пикселей различает классы гораздо лучше: у пустого подноса их почти нет, у маффина с тёмной шапкой — больше всего. Это и есть ручной **признак**: мы сами придумали, что считать. Дальше в главе признаки научатся находить фильтры и нейросеть.

::: quiz
Почему доля тёмных пикселей различает классы лучше, чем средняя яркость кадра?

- [x] Выпечка занимает лишь часть кадра: в среднем по всем пикселям её вклад тонет в светлом подносе, а доля тёмных пикселей считает именно её
  > Хороший признак выделяет то, что отличает классы, а не усредняет его вместе с фоном.
- [ ] Средняя яркость искажается из-за переполнения `uint8`
  > В примере кадры переведены во `float` до подсчёта — переполнения нет. Дело в том, что именно усредняется.
- [ ] Доля тёмных пикселей учитывает, где в кадре лежит выпечка
  > Наоборот, она одинакова, где бы ни лежала выпечка, — и это её плюс. Положение она не видит вовсе.
- [ ] Средняя яркость у всех классов одинаковая
  > Разница есть — пустой поднос светлее, — но небольшая, потому что выпечка занимает лишь часть кадра.
:::

{{practice: dark-rule, centroid}}

## Разберём вместе: от кадра витрины к ячейкам

Камера снимает витрину целиком, а модель работает с ячейками. Соберём «кадр витрины» из шести вырезок (2 ряда × 3 ячейки), а потом разрежем обратно — ровно так, как это делает программа у камеры.

**Шаг 1. Склеить кадр.** `np.hstack` ставит массивы рядом по горизонтали, `np.vstack` — друг под другом.

**Шаг 2. Разрезать.** Ячейка в ряду `r` и колонке `c` — это строки `32*r … 32*r + 31` и столбцы `32*c … 32*c + 31`.

**Шаг 3. Для каждой ячейки посчитать долю тёмных пикселей** и решить: пусто или нет.

```python
import numpy as np
import matplotlib.pyplot as plt

d = np.load("showcase.npz")
X, y, classes = d["X"], d["y"], d["classes"]
picked = [np.flatnonzero(y == c)[k] for c, k in [(1, 0), (0, 0), (2, 0), (3, 0), (0, 1), (1, 1)]]

row1 = np.hstack([X[i] for i in picked[:3]])          # 32 × 96
row2 = np.hstack([X[i] for i in picked[3:]])
frame = np.vstack([row1, row2])                        # 64 × 96 — «кадр витрины»
print("кадр:", frame.shape)

for r in range(2):
    for c in range(3):
        cell = frame[32 * r: 32 * (r + 1), 32 * c: 32 * (c + 1)]
        dark = (cell < 100).mean()
        print(f"ряд {r}, ячейка {c}: тёмных {dark:.3f} → {'пусто' if dark < 0.005 else 'есть товар'}")

plt.imshow(frame, cmap="gray", vmin=0, vmax=255)
```

**Что получилось:** кадр 64 × 96 разрезан на 6 ячеек. Простое правило «меньше 0.5 % тёмных пикселей — пусто» нашло только одну из двух пустых ячеек. Во второй (верхний ряд, в середине) тёмных пикселей 2.4 % — посмотрите на картинку: на пустом подносе лежит тёмный ценник. Правило не знает, что такое «ценник», оно считает тёмные точки. Порог 0.005 мы поставили между медианами из таблицы выше — 0 у пустых подносов и 0.02 у печенья, — но ближе к нулю: на пустом подносе бывают крошки, и они дают немного тёмных точек. В задачах подберём порог по данным и посчитаем, как часто правило ошибается.

{{practice: where}}

## Почему пиксели — плохие соседи

Можно ли сравнивать картинки напрямую — как точки в пространстве из 1024 координат? Посчитаем расстояние от круассана до той же картинки, сдвинутой на 3 пикселя, до других круассанов и до пустых подносов:

```python
import numpy as np

d = np.load("showcase.npz")
X, y = d["X"].astype(float), d["y"]
i = np.flatnonzero(y == 1)[0]
x0 = X[i]

shifted = np.linalg.norm(x0 - np.roll(x0, 3, axis=1))
same = np.mean([np.linalg.norm(x0 - X[j]) for j in np.flatnonzero(y == 1) if j != i])
empty = np.mean([np.linalg.norm(x0 - X[j]) for j in np.flatnonzero(y == 0)])
print(f"сдвиг на 3 пикселя: {shifted:.0f}")
print(f"другие круассаны:   {same:.0f}")
print(f"пустые подносы:     {empty:.0f}")
```

**Что здесь происходит:**

- `np.roll(x0, 3, axis=1)` — сдвиг картинки на 3 пикселя вправо (то, что ушло за край, появляется слева).
- `np.linalg.norm(a - b)` — евклидово расстояние: корень из суммы квадратов разностей по всем 1024 пикселям. Чем меньше, тем «похожее» картинки по пикселям.
- Средние расстояния считаем по всем остальным круассанам (кроме самого `x0`) и по всем пустым подносам.

::: figure pixel-shift
Игрушка из одной строки в 8 пикселей: у двух одинаковых силуэтов в разных местах не совпадают 6 клеток, у силуэта и пустого подноса — 3. Пиксельное расстояние «считает» положение, а не форму.
:::

::: warn
В среднем круассан по пикселям ближе к пустому подносу, чем к другому круассану. Причина: у двух круассанов в разных местах кадра тёмные пиксели не совпадают, и расстояние складывается из двух несовпавших силуэтов. А пустой поднос «не совпадает» только с одним. Поэтому модели, которые сравнивают пиксели по местам, на картинках работают плохо, — нужны признаки, не зависящие от положения: об этом следующие уроки.
:::

::: quiz
Две фотографии одного маффина: на второй он сдвинут на 3 пикселя вправо. Что покажет расстояние между ними «по пикселям»?

- [x] Большое расстояние: почти каждый пиксель изменился, хотя на снимке тот же маффин
  > Пиксельное сравнение не знает, что такое «тот же предмет». Поэтому дальше нужны признаки, устойчивые к сдвигу: фильтры и пулинг.
- [ ] Почти ноль: предмет тот же
  > Сравниваются числа в клетках, а они сдвинулись.
- [ ] Ровно 3
  > Расстояние считается по всем пикселям, а не по величине сдвига.
- [ ] Бесконечность
  > Расстояние конечно — просто большое.
:::

{{practice: shift}}

## Практика

## task: load | Что в файле | warmup

Загрузите `showcase.npz` и сохраните `X`, `y`, `classes`, а также `counts` — словарь `{название класса: число картинок}` и `size` — кортеж `(высота, ширина)` одной картинки.

### starter
```python
import numpy as np

```

### check
```python
import numpy as _np
d0 = _np.load('showcase.npz')
assert need('X').shape == (2000, 32, 32), 'X — массив d["X"].'
assert (need('y') == d0['y']).all(), 'y — массив d["y"].'
w = {str(c): int((d0['y'] == k).sum()) for k, c in enumerate(d0['classes'])}
got = {str(k): int(v) for k, v in need('counts', dict).items()}
assert got == w, f'counts = {got}, а нужно {w}.'
assert tuple(need('size')) == (32, 32), f'size = {need("size")}.'
```

### hint
Массивы из архива достаются по именам: `d = np.load("showcase.npz")`, затем `d["X"]`, `d["y"]`, `d["classes"]`.

### hint
`np.bincount(y)` считает метки; пройдите `zip(classes, np.bincount(y))`. Размер — `X.shape[1:]`.

### hint
`counts = {str(c): int(n) for c, n in zip(classes, np.bincount(y))}` — `str` и `int` превращают типы numpy в обычные.

### solution
```python
import numpy as np

d = np.load("showcase.npz")
X, y, classes = d["X"], d["y"], d["classes"]
counts = {str(c): int(n) for c, n in zip(classes, np.bincount(y))}
size = X.shape[1:]
print(counts, size)
```

## task: p-show | Показать маффин | warmup

Соберите код, который рисует первый маффин в общей шкале яркости и печатает его форму.

### parsons
```python
import numpy as np
import matplotlib.pyplot as plt
d = np.load("showcase.npz")
X, y = d["X"], d["y"]
img = X[np.flatnonzero(y == 2)[0]]
plt.imshow(img, cmap="gray", vmin=0, vmax=255)
print(img.shape)
```

### check
```python
assert _lines == ['(32, 32)'], f'Сейчас: {_lines}.'
ax = ax_of(0)
assert len(ax.images) == 1, 'Нужна одна картинка через imshow.'
im = ax.images[0]
assert im.get_clim() == (0, 255), 'Задайте vmin=0, vmax=255.'
```

### hint
Загрузка → выбор картинки → рисунок → печать.

### hint
Номер первого маффина — `np.flatnonzero(y == 2)[0]`: маффин — класс 2.

## task: crop | Центр всех кадров | warmup

Вырежьте центральный квадрат 16 × 16 (строки и столбцы 8…23) у **всех** картинок сразу — одной строкой, без цикла. Результат — `centers`. В `n_numbers` — сколько всего чисел в `centers`, в `share_kept` — какая доля чисел исходного `X` осталась (2 знака).

### setup
```python
import numpy as np
X = np.load("showcase.npz")["X"]
```

### starter
```python
import numpy as np

```

### check
```python
import numpy as _np
X0 = need('X')
c = need('centers')
assert c.shape == (2000, 16, 16), f'centers.shape = {c.shape}, а нужно (2000, 16, 16).'
assert (c == X0[:, 8:24, 8:24]).all(), 'centers — строки и столбцы 8…23 у каждой картинки: X[:, 8:24, 8:24].'
assert need('n_numbers') == c.size, f'n_numbers = {need("n_numbers")}.'
assert close(need('share_kept'), 0.25, 1e-9), f'share_kept = {need("share_kept")}.'
```

### hint
Первая ось — номер картинки, её берём целиком: `:`. Две другие — строки и столбцы.

### hint
`centers = X[:, 8:24, 8:24]`; число элементов массива — `.size`; доля — `centers.size / X.size`.

### solution
```python
import numpy as np

centers = X[:, 8:24, 8:24]
n_numbers = centers.size
share_kept = round(centers.size / X.size, 2)
print(centers.shape, n_numbers, share_kept)
```

## task: overflow | Сделать ярче без поломки | base

Напишите функцию `brighten(img, k)`, которая умножает яркость картинки `uint8` на `k`, обрезает значения до 0–255, округляет и возвращает снова `uint8`. Примените её к `X[0]` с `k=1.5` — результат в `bright`. В `n_sat` — сколько пикселей `bright` стали ровно 255.

### setup
```python
import numpy as np
X = np.load("showcase.npz")["X"]
```

### starter
```python
import numpy as np

def brighten(img, k):
    ...

```

### check
```python
import numpy as _np
f = need('brighten')
t = _np.array([[200, 100, 0]], dtype=_np.uint8)
r = f(t, 1.5)
assert isinstance(r, _np.ndarray) and r.dtype == _np.uint8, 'Функция должна вернуть массив uint8.'
assert r.tolist() == [[255, 150, 0]], f'brighten([[200, 100, 0]], 1.5) = {r.tolist()}, а нужно [[255, 150, 0]].'
assert f(_np.array([[3]], dtype=_np.uint8), 0.5).tolist() == [[2]], 'Округляйте: 1.5 → 2 (np.round).'
X0 = need('X')
w = _np.clip(_np.round(X0[0].astype(float) * 1.5), 0, 255).astype(_np.uint8)
b = need('bright', _np.ndarray)
assert (b == w).all(), 'bright = brighten(X[0], 1.5).'
assert need('n_sat') == int((w == 255).sum()), f'n_sat = {need("n_sat")}.'
```

### hint
Четыре шага: перевести в `float` (иначе переполнение), умножить, округлить и обрезать до 0–255, вернуть в `uint8`.

### hint
`img.astype(float) * k` → `np.round(...)` → `np.clip(..., 0, 255)` → `.astype(np.uint8)`.

### hint
Число пикселей, равных 255: `(bright == 255).sum()` — сумма `True` считает их количество.

### solution
```python
import numpy as np

def brighten(img, k):
    return np.clip(np.round(img.astype(float) * k), 0, 255).astype(np.uint8)

bright = brighten(X[0], 1.5)
n_sat = int((bright == 255).sum())
print(n_sat)
```

### explain
Фон светлый, поэтому после умножения на 1.5 больше трети пикселей упирается в 255 — детали фона теряются безвозвратно (это называют **пересветом**). При аугментации яркость меняют умеренно.

## task: dark-rule | Правило «есть ли товар» | base

Посчитайте для каждой картинки `dark` — долю пикселей темнее 100. Правило: «товар есть», если `dark >= t`. Переберите пороги `[0.005, 0.01, 0.02, 0.05]` и сохраните `acc_by_t` — словарь `{порог: доля верных ответов}` (3 знака) для задачи «пусто / не пусто», `best_t` — лучший порог и `dark_median` — Series медиан `dark` по названиям классов (3 знака).

### setup
```python
import numpy as np
d = np.load("showcase.npz")
X, y, classes = d["X"], d["y"], d["classes"]
```

### starter
```python
import numpy as np
import pandas as pd

```

### check
```python
import numpy as _np
import pandas as _pd
d0 = _np.load('showcase.npz'); X0, y0, c0 = d0['X'], d0['y'], d0['classes']
dk = (X0 < 100).reshape(len(X0), -1).mean(axis=1)
w = {t: round(float(((dk >= t) == (y0 != 0)).mean()), 3) for t in [0.005, 0.01, 0.02, 0.05]}
got = need('acc_by_t', dict)
assert sorted(got) == sorted(w), f'Ключи: {sorted(got)}.'
assert all(close(got[t], w[t], 0.0015) for t in w), f'acc_by_t = {got}, а нужно {w}.'
assert close(need('best_t'), max(w, key=w.get)), f'best_t = {need("best_t")}.'
m = _pd.Series(dk).groupby(c0[y0]).median().round(3)
got_m = need('dark_median', _pd.Series)
assert all(close(got_m[k], m[k], 0.0015) for k in m.index), f'dark_median:\n{got_m}'
```

### hint
Сначала признак для всех картинок сразу: `(X < 100).reshape(len(X), -1).mean(axis=1)` — массив из 2000 долей.

### hint
Ответ правила — `dark >= t`, правильный ответ «товар есть» — `y != 0`. Доля совпадений — `((dark >= t) == (y != 0)).mean()`.

### hint
Словарь по порогам: `{t: round(float(...), 3) for t in [0.005, 0.01, 0.02, 0.05]}`; лучший — `max(acc_by_t, key=acc_by_t.get)`. Медианы: `pd.Series(dark).groupby(classes[y]).median()`.

### solution
```python
import numpy as np
import pandas as pd

dark = (X < 100).reshape(len(X), -1).mean(axis=1)
acc_by_t = {t: round(float(((dark >= t) == (y != 0)).mean()), 3) for t in [0.005, 0.01, 0.02, 0.05]}
best_t = max(acc_by_t, key=acc_by_t.get)
dark_median = pd.Series(dark).groupby(classes[y]).median().round(3)
print(acc_by_t, best_t)
print(dark_median)
```

### explain
Правило в одну строку отличает пустую ячейку от занятой примерно в 97 % случаев: у пустого подноса тёмных пикселей почти нет. Ошибки — пустые кадры с тёмным ценником и печенье, которое светлее остальной выпечки. Лучший порог оказался крайним в списке — это повод расширить перебор вниз: пороги 0.002 и 0.003 дают 0.973, чуть больше, чем 0.005 (0.967). Запомните это число — модели должны его обогнать. И порог подобран при дневном свете: что будет вечером, разберём в проекте.

## task: centroid | Средняя картинка класса | plus

Разбейте индексы на обучение и тест: `train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)`. По обучающим картинкам посчитайте `means` — массив `(4, 32, 32)` средних картинок классов. Классифицируйте тестовые картинки по ближайшей средней (евклидово расстояние по всем пикселям) и сохраните `centroid_acc` — долю верных (3 знака). Нарисуйте четыре средние картинки.

### setup
```python
import numpy as np
d = np.load("showcase.npz")
X, y, classes = d["X"].astype(float), d["y"], d["classes"]
```

### starter
```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

```

### check
```python
import numpy as _np
from sklearn.model_selection import train_test_split as _tts
d0 = _np.load('showcase.npz'); X0, y0 = d0['X'].astype(float), d0['y']
tr, te = _tts(_np.arange(len(X0)), test_size=0.25, random_state=42, stratify=y0)
M = _np.stack([X0[tr][y0[tr] == c].mean(0) for c in range(4)])
got = _np.asarray(need('means'))
assert got.shape == (4, 32, 32), f'means.shape = {got.shape}.'
assert _np.allclose(got, M, atol=1e-6), 'Средние считаются только по обучающим картинкам каждого класса.'
dist = ((X0[te][:, None] - M[None]) ** 2).sum(axis=(2, 3))
w = round(float((dist.argmin(1) == y0[te]).mean()), 3)
assert close(need('centroid_acc'), w, 0.0015), f'centroid_acc = {need("centroid_acc")}, а нужно {w}.'
assert len(figs) >= 1, 'Нарисуйте средние картинки.'
```

### hint
Средняя картинка класса — среднее по первой оси (по картинкам): `X[tr][y[tr] == c].mean(axis=0)`, форма `(32, 32)`. Четыре таких — `np.stack([...])`.

### hint
Классификация циклом: для каждой тестовой картинки `img` из `X[te]` — четыре расстояния `[np.linalg.norm(img - means[c]) for c in range(4)]`, ответ — номер наименьшего (`np.argmin`). Доля верных — среднее совпадений ответов с `y[te]`.

### solution
```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
means = np.stack([X[tr][y[tr] == c].mean(axis=0) for c in range(4)])
pred = np.array([np.argmin([np.linalg.norm(img - means[c]) for c in range(4)]) for img in X[te]])
centroid_acc = round(float((pred == y[te]).mean()), 3)
print(centroid_acc)

fig, axes = plt.subplots(1, 4, figsize=(8, 2.3))
for c, ax in enumerate(axes):
    ax.imshow(means[c], cmap="gray", vmin=0, vmax=255); ax.set_title(classes[c]); ax.axis("off")
```

### explain
Цикл можно заменить одной строкой: `((X[te][:, None] - means[None]) ** 2).sum(axis=(2, 3))` — `None` вставляет ось, и numpy сразу считает разности всех тестовых картинок со всеми четырьмя средними (форма `(n_test, 4)`); дальше `argmin(axis=1)`. Корень для выбора ближайшей не нужен: он не меняет порядок.

Средние картинки — размытые пятна: выпечка лежит в разных местах, и силуэты усредняются в облако. Классификатор по ближайшей средней угадывает меньше половины — хуже, чем правило из одной строки. Пиксели на своих местах — плохое описание формы.

## task: shift | Сдвиг против смысла | star

Возьмите первый круассан `x0` (в `float`). Посчитайте `d_shift` — средние евклидовы расстояния от `x0` до его копий, сдвинутых `np.roll` по горизонтали на 1, 2, …, 6 пикселей, — словарь `{сдвиг: расстояние}` (целые, `round`). Посчитайте `d_same` — среднее расстояние до остальных круассанов и `d_empty` — до пустых подносов (целые). В `max_safe_shift` — наибольший сдвиг, при котором копия ещё ближе к `x0`, чем `d_empty`.

### setup
```python
import numpy as np
d = np.load("showcase.npz")
X, y = d["X"].astype(float), d["y"]
```

### starter
```python
import numpy as np

i = np.flatnonzero(y == 1)[0]
x0 = X[i]

```

### check
```python
import numpy as _np
d0 = _np.load('showcase.npz'); X0, y0 = d0['X'].astype(float), d0['y']
i = _np.flatnonzero(y0 == 1)[0]; x = X0[i]
ws = {k: round(float(_np.linalg.norm(x - _np.roll(x, k, axis=1)))) for k in range(1, 7)}
wsame = round(float(_np.mean([_np.linalg.norm(x - X0[j]) for j in _np.flatnonzero(y0 == 1) if j != i])))
we = round(float(_np.mean([_np.linalg.norm(x - X0[j]) for j in _np.flatnonzero(y0 == 0)])))
got = {int(k): v for k, v in need('d_shift', dict).items()}
assert sorted(got) == list(range(1, 7)), f'Ключи d_shift: {sorted(got)}.'
assert all(abs(got[k] - ws[k]) <= 1 for k in ws), f'd_shift = {got}, а нужно {ws}.'
assert abs(need('d_same') - wsame) <= 1, f'd_same = {need("d_same")}, а нужно {wsame}.'
assert abs(need('d_empty') - we) <= 1, f'd_empty = {need("d_empty")}, а нужно {we}.'
mss = max([k for k in ws if ws[k] < we], default=0)
assert need('max_safe_shift') == mss, f'max_safe_shift = {need("max_safe_shift")}, а нужно {mss}.'
```

### hint
Расстояние до сдвинутой копии: `np.linalg.norm(x0 - np.roll(x0, k, axis=1))` — для `k` от 1 до 6 в словарном выражении.

### hint
Для остальных круассанов: `[np.linalg.norm(x0 - X[j]) for j in np.flatnonzero(y == 1) if j != i]` — и `np.mean` от списка. Для пустых — то же с `y == 0`.

### hint
`max_safe_shift = max([k for k in d_shift if d_shift[k] < d_empty], default=0)`.

### solution
```python
import numpy as np

i = np.flatnonzero(y == 1)[0]
x0 = X[i]
d_shift = {k: round(float(np.linalg.norm(x0 - np.roll(x0, k, axis=1)))) for k in range(1, 7)}
d_same = round(float(np.mean([np.linalg.norm(x0 - X[j]) for j in np.flatnonzero(y == 1) if j != i])))
d_empty = round(float(np.mean([np.linalg.norm(x0 - X[j]) for j in np.flatnonzero(y == 0)])))
max_safe_shift = max([k for k in d_shift if d_shift[k] < d_empty], default=0)
print(d_shift, d_same, d_empty, max_safe_shift)
```

### explain
После сдвига всего на 6 пикселей тот же самый круассан «по пикселям» дальше от себя, чем в среднем пустой поднос, и почти так же далёк, как другие круассаны. Глаз человека этого даже не заметит. Нужны признаки, которым безразлично, где именно лежит выпечка, — их дают свёртки и пулинг из урока «Свёртка и фильтры».

## task: gray | Из цвета в серое | base

Напишите `to_gray(rgb)`: для массива формы `(высота, ширина, 3)` типа `uint8` вернуть серую картинку `(высота, ширина)` типа `uint8` по формуле `0.299·R + 0.587·G + 0.114·B` с округлением. Примените её к `cup` из заготовки (картинка 6 × 6: пена, кофе и красный край стакана) — результат в `cup_gray`. В `darkest_color` — какой из трёх исходных цветов (`"пена"`, `"кофе"`, `"стакан"`) стал самым тёмным серым.

### setup
```python
import numpy as np
cup = np.zeros((6, 6, 3), dtype=np.uint8)
cup[:, :] = [200, 30, 30]          # стакан — красный
cup[1:5, 1:5] = [110, 70, 40]      # кофе
cup[2:4, 2:4] = [240, 230, 210]    # пена
```

### starter
```python
import numpy as np

def to_gray(rgb):
    ...

cup_gray = to_gray(cup)
print(cup_gray)
```

### check
```python
import numpy as _np
f = need('to_gray')
t = _np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255], [10, 20, 30]]], dtype=_np.uint8)
r = f(t)
assert isinstance(r, _np.ndarray) and r.shape == (1, 4), f'Форма результата должна быть (высота, ширина), а сейчас {getattr(r, "shape", None)}.'
assert r.dtype == _np.uint8, 'Верните uint8: .round().astype(np.uint8).'
assert r.tolist() == [[76, 150, 29, 18]], f'to_gray для чистых красного, зелёного, синего и (10, 20, 30) = {r.tolist()}, а нужно [[76, 150, 29, 18]].'
g = need('cup_gray')
assert g.shape == (6, 6) and int(g[0, 0]) == 81 and int(g[1, 1]) == 79 and int(g[2, 2]) == 231, f'cup_gray: углы и центр не совпадают — {g[0, 0]}, {g[1, 1]}, {g[2, 2]}.'
assert need('darkest_color') == 'кофе', f'darkest_color = {need("darkest_color")!r}.'
```

### hint
Каналы: `rgb[..., 0]` — красный, `rgb[..., 1]` — зелёный, `rgb[..., 2]` — синий. Каждый — матрица `(высота, ширина)`.

### hint
Перемножать лучше во `float`: `rgb.astype(float)`, иначе можно получить переполнение на промежуточных шагах.

### hint
`return (0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]).round().astype(np.uint8)`, где `c = rgb.astype(float)`.

### solution
```python
import numpy as np

def to_gray(rgb):
    c = rgb.astype(float)
    return (0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]).round().astype(np.uint8)

cup_gray = to_gray(cup)
values = {"стакан": int(cup_gray[0, 0]), "кофе": int(cup_gray[1, 1]), "пена": int(cup_gray[2, 2])}
darkest_color = min(values, key=values.get)
print(cup_gray, values, darkest_color)
```

### explain
Ярко-красный стакан (81) и коричневый кофе (79) в сером почти не различаются, хотя глазу они совсем разные. Это и есть цена перехода в оттенки серого: цвета с похожей яркостью сливаются. Для выпечки на подносе это не страшно — силуэт виден по яркости, — но для задачи «отличить капучино от латте по цвету» серый не годится.

## task: cells | Разрезать кадр на ячейки | base

В заготовке — кадр витрины `frame` 64 × 96 (2 ряда × 3 ячейки 32 × 32). Разрежьте его на ячейки: `cells` — список из 6 массивов 32 × 32 в порядке «слева направо, сверху вниз». Для каждой ячейки посчитайте долю пикселей темнее 100 — `dark_shares` (список, 3 знака) — и решите, пуста ли она (доля < 0.005): `empty` — список `True/False`. В `n_empty` — сколько пустых.

### setup
```python
import numpy as np
_d = np.load("showcase.npz")
_X, _y = _d["X"], _d["y"]
_pick = [np.flatnonzero(_y == c)[k] for c, k in [(3, 2), (0, 3), (1, 4), (0, 5), (2, 6), (0, 7)]]
frame = np.vstack([np.hstack([_X[i] for i in _pick[:3]]), np.hstack([_X[i] for i in _pick[3:]])])
```

### starter
```python
import numpy as np

cells = []

```

### check
```python
import numpy as _np
fr = need('frame')
want = [fr[32 * r:32 * (r + 1), 32 * c:32 * (c + 1)] for r in range(2) for c in range(3)]
cl = need('cells', list)
assert len(cl) == 6 and all(_np.asarray(a).shape == (32, 32) for a in cl), 'cells — 6 массивов 32 × 32.'
assert all((_np.asarray(a) == b).all() for a, b in zip(cl, want)), 'Порядок ячеек: сначала верхний ряд слева направо, потом нижний.'
ds = [round(float((b < 100).mean()), 3) for b in want]
assert all(close(a, b, 0.0011) for a, b in zip(need('dark_shares', list), ds)), f'dark_shares = {need("dark_shares")}, а нужно {ds}.'
assert [bool(v) for v in need('empty', list)] == [x < 0.005 for x in [(b < 100).mean() for b in want]], f'empty = {need("empty")}.'
assert need('n_empty') == sum((b < 100).mean() < 0.005 for b in want), f'n_empty = {need("n_empty")}.'
```

### hint
Ячейка в ряду `r` и колонке `c`: `frame[32 * r: 32 * (r + 1), 32 * c: 32 * (c + 1)]`. Двойной цикл: внешний по рядам, внутренний по колонкам — тогда порядок будет нужный.

### hint
Доля тёмных в ячейке — `(cell < 100).mean()`; решение — `доля < 0.005`.

### hint
```python
for r in range(2):
    for c in range(3):
        cells.append(frame[32 * r: 32 * (r + 1), 32 * c: 32 * (c + 1)])
dark_shares = [round(float((cell < 100).mean()), 3) for cell in cells]
```

### solution
```python
import numpy as np

cells = []
for r in range(2):
    for c in range(3):
        cells.append(frame[32 * r: 32 * (r + 1), 32 * c: 32 * (c + 1)])
dark_shares = [round(float((cell < 100).mean()), 3) for cell in cells]
empty = [(cell < 100).mean() < 0.005 for cell in cells]
n_empty = sum(empty)
print(dark_shares, empty, n_empty)
```

### explain
Так и работает программа у камеры: кадр — один большой массив, ячейки — его срезы по известной сетке. Обратите внимание на границы: `32 * (r + 1)` не включается в срез, поэтому соседние ячейки не перекрываются и ничего не теряется. Если сетка сдвинута хотя бы на пару пикселей (камеру задели при уборке), в ячейку попадёт кусок соседней выпечки — и правило по тёмным пикселям начнёт ошибаться. Поэтому сетку ячеек на практике периодически перепроверяют.

## task: where | Где лежит выпечка | plus

Насколько сильно выпечка «гуляет» по кадру? Для каждой **непустой** картинки найдите центр тёмного пятна: средний номер строки и средний номер столбца среди пикселей темнее 100. Сохраните `rows_c` и `cols_c` — массивы этих центров (по всем непустым картинкам, у которых есть хотя бы один тёмный пиксель), `spread` — кортеж из стандартных отклонений центров по строкам и столбцам (1 знак), и `frac_off_center` — долю картинок, у которых центр отстоит от середины кадра (15.5, 15.5) больше чем на 4 пикселя по какой-либо оси (2 знака).

### setup
```python
import numpy as np
d = np.load("showcase.npz")
X, y = d["X"], d["y"]
```

### starter
```python
import numpy as np

rows_c, cols_c = [], []

```

### check
```python
import numpy as _np
X0, y0 = need('X'), need('y')
rr, cc = [], []
for img in X0[y0 != 0]:
    r, c = _np.nonzero(img < 100)
    if len(r):
        rr.append(r.mean()); cc.append(c.mean())
rr, cc = _np.array(rr), _np.array(cc)
assert len(need('rows_c')) == len(rr), f'Центров должно быть {len(rr)}: по непустым картинкам с тёмными пикселями.'
assert _np.allclose(need('rows_c'), rr) and _np.allclose(need('cols_c'), cc), 'Центр — средний номер строки (столбца) тёмных пикселей: np.nonzero(img < 100).'
sp = (round(float(rr.std()), 1), round(float(cc.std()), 1))
assert all(close(a, b, 0.051) for a, b in zip(need('spread'), sp)), f'spread = {need("spread")}, а нужно {sp}.'
fo = round(float(((_np.abs(rr - 15.5) > 4) | (_np.abs(cc - 15.5) > 4)).mean()), 2)
assert close(need('frac_off_center'), fo, 0.0051), f'frac_off_center = {need("frac_off_center")}, а нужно {fo}.'
```

### hint
`np.nonzero(img < 100)` возвращает два массива — номера строк и номера столбцов тёмных пикселей. Их средние и есть центр пятна.

### hint
Цикл по `X[y != 0]`; если тёмных пикселей нет (`len(r) == 0`) — картинку пропускаем. В конце превратите списки в массивы `np.array(...)`.

### hint
Доля «далеко от центра»: `((np.abs(rows_c - 15.5) > 4) | (np.abs(cols_c - 15.5) > 4)).mean()` — `|` значит «или».

### solution
```python
import numpy as np

rows_c, cols_c = [], []
for img in X[y != 0]:
    r, c = np.nonzero(img < 100)
    if len(r):
        rows_c.append(r.mean())
        cols_c.append(c.mean())
rows_c, cols_c = np.array(rows_c), np.array(cols_c)
spread = (round(float(rows_c.std()), 1), round(float(cols_c.std()), 1))
frac_off_center = round(float(((np.abs(rows_c - 15.5) > 4) | (np.abs(cols_c - 15.5) > 4)).mean()), 2)
print(spread, frac_off_center)
```

### explain
Центр пятна «гуляет» на несколько пикселей в каждую сторону, и почти у двух третей кадров выпечка сдвинута от середины больше чем на 4 пикселя хотя бы по одной оси. Вспомните разбор расстояний: уже такой сдвиг делает круассан «по пикселям» почти чужим самому себе. Это количественное объяснение, почему модели на сырых пикселях будут ошибаться, — и почему дальше нам понадобятся признаки, нечувствительные к положению.
