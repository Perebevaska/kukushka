---
title: "Модели на пикселях: ошибки, аугментация, устойчивость"
files: [showcase.npz]
lead: "Обучаем знакомые модели sklearn прямо на пикселях: логистическую регрессию, kNN, лес и полносвязную сеть. Смотрим, где они путаются, учим лес на отражённых и сдвинутых копиях кадров, а затем устраиваем стресс-тест: сдвиг выпечки и вечерний свет. Выясняется, что точность на тесте ничего не говорит об устойчивости."
recap:
  - "Картинки → таблица: `X.reshape(len(X), -1)` — 1024 признака-пикселя на кадр. Дальше работает любая модель sklearn."
  - "На пикселях лес из 100 деревьев (0.91) сильнее логистической регрессии (0.68) и kNN с 5 соседями (0.83), а kNN с одним соседом даже чуть точнее леса (0.92). Лес путает похожие по силуэту классы (круассан ↔ печенье) — видно по матрице ошибок."
  - "Аугментация — добавить в обучение изменённые копии (отражения, сдвиги, яркость). Применяется только к обучающей части; тест не трогают."
  - "Стресс-тест: проверить модель на намеренно изменённом тесте (сдвиг, затемнение). Высокая точность на обычном тесте не гарантирует устойчивости."
  - "От изменения яркости спасает нормировка каждого кадра: вычесть его среднее и разделить на его стандартное отклонение."
---

## Картинки как таблица

Модели sklearn принимают таблицу: строка — объект, столбец — признак. Картинку 32 × 32 вытягиваем в строку из 1024 чисел — и сравниваем модели, как в главах 6–7.

```python
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

d = np.load("showcase.npz")
X, y, classes = d["X"] / 255, d["y"], d["classes"]
X2d = X.reshape(len(X), -1)                         # 2000 × 1024
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)

models = {
    "логрегрессия": make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
    "kNN, 5 соседей": KNeighborsClassifier(5),
    "лес, 100 деревьев": RandomForestClassifier(100, random_state=0),
}
for name, m in models.items():
    m.fit(X2d[tr], y[tr])
    print(f"{name:18} {m.score(X2d[te], y[te]):.3f}")
```

**Что здесь происходит:**

- `X2d = X.reshape(len(X), -1)` — таблица 2000 × 1024: строка — кадр, столбец — пиксель с определённым номером (например, столбец 0 — левый верхний пиксель).
- Разбиваем **индексы** (`np.arange(len(X))`), а не сами массивы: так по одним и тем же `tr`, `te` можно брать и картинки `X`, и таблицу `X2d`, и метки `y`.
- `make_pipeline(StandardScaler(), LogisticRegression(...))` — для логистической регрессии пиксели масштабируем (глава 7); лесу и kNN по нашим данным это не нужно — все пиксели и так в одной шкале 0–1.
- `m.score(...)` — доля верных ответов на тесте.

| Модель | Как «смотрит» на кадр | Чем мешает то, что выпечка гуляет |
|---|---|---|
| логистическая регрессия | у каждого пикселя свой вес, ответ — взвешенная сумма | вес пикселя (10, 12) не знает, что круассан сегодня лежит на 5 пикселей левее |
| kNN | ищет самые похожие кадры по расстоянию | расстояние больше зависит от положения, чем от формы (урок «Картинка — это массив чисел») |
| лес | много вопросов «пиксель (r, c) темнее порога?» и их комбинации | гибче, но каждое дерево тоже спрашивает про конкретные места |

Лес — около 0.91, kNN с 5 соседями — 0.83, логистическая регрессия — 0.68. Почему так: линейная модель даёт каждому пикселю один вес, а выпечка лежит где угодно — веса не могут сказать «тёмное пятно где-то в кадре». kNN сравнивает кадры по пиксельному расстоянию, которое, как мы видели в уроке «Картинка — это массив чисел», плохо отражает форму. Лес задаёт много вопросов про разные пиксели и комбинирует их — получается гибче. Одна оговорка: kNN с одним соседом неожиданно даёт около 0.92 — чуть больше леса; почему, разберём в задаче «Сколько соседей брать».

::: note
Полносвязная сеть `MLPClassifier(max_iter=500, random_state=0)` на тех же пикселях (без масштабирования, как лес) даёт около 0.85 — не лучше леса. Ей тоже приходится учиться заново для каждого положения выпечки. Сети начинают выигрывать, когда в них встроена свёртка (урок «Свёрточные нейросети»).
:::

{{practice: flat, p-knn, knn-k}}

## Где модель ошибается

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

d = np.load("showcase.npz")
X, y, classes = d["X"] / 255, d["y"], d["classes"]
X2d = X.reshape(len(X), -1)
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(100, random_state=0).fit(X2d[tr], y[tr])
pred = forest.predict(X2d[te])

print(pd.DataFrame(confusion_matrix(y[te], pred), index=classes, columns=classes))

wrong = np.flatnonzero(pred != y[te])[:8]
fig, axes = plt.subplots(1, 8, figsize=(12, 2))
for ax, k in zip(axes, wrong):
    ax.imshow(X[te][k], cmap="gray", vmin=0, vmax=1); ax.axis("off")
    ax.set_title(f"{classes[y[te][k]]}\n→ {classes[pred[k]]}", fontsize=8)
```

**Что здесь происходит:**

- `confusion_matrix(y[te], pred)` — таблица 4 × 4: в клетке (i, j) — сколько кадров класса i модель назвала классом j. Диагональ — верные ответы.
- `np.flatnonzero(pred != y[te])[:8]` — номера (внутри теста) первых восьми ошибок.
- `X[te][k]` — сначала берём тестовые картинки, потом k-ю из них. Индексы `k` относятся к тестовой части, поэтому `X[k]` здесь было бы ошибкой — это другая картинка.
- `f"{правда}\n→ {ответ}"` — подпись в две строки над каждой картинкой.

Как читать матрицу: возьмите строку «круассан». Число на диагонали — сколько круассанов узнано, остальные числа строки — куда ушли неузнанные. Сумма строки — сколько всего круассанов в тесте.

Строки — правда, столбцы — ответ модели. Больше всего ошибок между круассаном и печеньем: оба — тёмные пятна средней величины. Маффин с его тёмной шапкой путают редко, пустой поднос — почти никогда.

{{practice: confusion}}

## Разберём вместе: куда смотрит лес

У леса есть `feature_importances_` — насколько каждый признак помогал разделять классы (глава 6). Признаки у нас — пиксели, значит важности можно сложить обратно в картинку 32 × 32 и увидеть, на какие места кадра лес смотрит.

**План:** обучить лес → `feature_importances_` (1024 числа) → `reshape(32, 32)` → нарисовать → посчитать, какая доля важности приходится на центр 16 × 16 (это четверть площади кадра).

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(100, random_state=0).fit(X[tr].reshape(len(tr), -1), y[tr])

imp = forest.feature_importances_.reshape(32, 32)
print("сумма важностей:", round(imp.sum(), 3))
print("доля центра 16 × 16:", round(imp[8:24, 8:24].sum(), 3))
print("доля рамки шириной 4 пикселя:", round(imp.sum() - imp[4:28, 4:28].sum(), 3))
plt.imshow(imp, cmap="hot"); plt.colorbar(); plt.title("важность пикселей")
```

**Что получилось:** важности в сумме дают 1, и около 62 % приходится на центральный квадрат, который занимает лишь 25 % кадра. Лес выучил «смотри в середину — выпечка обычно там». Но вспомните задачу «Где лежит выпечка» из урока «Картинка — это массив чисел»: почти у двух третей кадров выпечка сдвинута от середины больше чем на 4 пикселя. Значит, лес полагается на то, что положение примерно такое же, как в обучении, — и стресс-тест ниже покажет, чем это грозит.

{{practice: importance}}

## Аугментация

Отражённый круассан — тоже круассан, сдвинутый — тоже. Значит, можно бесплатно увеличить обучающую выборку: добавить отражённые по горизонтали и случайно сдвинутые копии кадров. Модель увидит выпечку в большем числе положений.

```python
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)

def augment(Z, labels, rng):
    flipped = Z[:, :, ::-1]
    shifts = rng.integers(-4, 5, size=(len(Z), 2))
    shifted = np.stack([np.roll(z, tuple(s), axis=(0, 1)) for z, s in zip(Z, shifts)])
    return np.concatenate([Z, flipped, shifted]), np.concatenate([labels, labels, labels])

X_aug, y_aug = augment(X[tr], y[tr], np.random.default_rng(0))
print(X[tr].shape, "→", X_aug.shape)

flat = lambda Z: Z.reshape(len(Z), -1)
base = RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr])
aug = RandomForestClassifier(100, random_state=0).fit(flat(X_aug), y_aug)
print("без аугментации:", round(base.score(flat(X[te]), y[te]), 3))
print("с аугментацией: ", round(aug.score(flat(X[te]), y[te]), 3))
```

**Что здесь происходит:**

- `Z[:, :, ::-1]` — отражение по горизонтали сразу у всех кадров (третья ось — столбцы).
- `rng.integers(-4, 5, size=(len(Z), 2))` — для каждого кадра пара случайных сдвигов `(dy, dx)` от −4 до 4 (правая граница 5 не входит).
- `np.roll(z, tuple(s), axis=(0, 1))` — сдвиг одной картинки сразу по двум осям.
- `np.concatenate([Z, flipped, shifted])` — склеиваем три набора: 1500 исходных + 1500 отражённых + 1500 сдвинутых = 4500. Метки повторяем трижды в том же порядке.
- `rng = np.random.default_rng(0)` — генератор с фиксированным зерном: аугментация воспроизводима.

Точность выросла с 0.91 до 0.96 — без единой новой фотографии.

::: figure augment-split
Порядок действий: сначала разбиение, потом аугментация обучающей части — 1500 кадров превращаются в 4500. Тестовые 500 кадров остаются как есть.
:::

::: warn
Аугментируют **только обучающую часть** и только после разбиения. Если размножить весь набор до разбиения, копия тестового кадра попадёт в обучение, и тест станет нечестным — та же утечка, что с балансировкой классов в главе 7.
:::

::: tip
`np.roll` переносит пиксели, ушедшие за край, на противоположную сторону. Для сдвига на 4 пикселя по краю светлого подноса это почти незаметно. В библиотеках для нейросетей сдвиг делают аккуратнее — с дополнением края, — а ещё поворачивают, масштабируют, меняют яркость и контраст.
:::

::: quiz
Почему аугментацию делают только после разбиения и только на обучающей части?

- [x] Иначе отражённая или сдвинутая копия тестового кадра попадёт в обучение — модель фактически увидит тест, и оценка станет нечестной
  > Тест должен изображать новые кадры, которых модель не видела ни в каком виде.
- [ ] Тестовые кадры нельзя отражать — модель перестанет их узнавать
  > Отражённый круассан — всё ещё круассан. Проблема не в самих копиях, а в том, что они оказываются по обе стороны разбиения.
- [ ] Аугментация всего набора занимает слишком много времени
  > Время здесь ни при чём: размножить 2000 кадров почти так же быстро, как 1500. Дело в утечке.
- [ ] Чтобы не нарушить баланс классов
  > Каждый кадр получает ровно по копии каждого вида, так что доли классов не меняются ни в одном случае.
:::

{{practice: augment, bright-aug}}

## Стресс-тест

Тестовая выборка похожа на обучающую — поэтому точность на ней и высокая. А что, если камеру чуть сдвинули, или вечером в зале другой свет? Когда кадры в работе отличаются от тех, на которых модель училась, это называют **сдвигом данных**. Проверим, как модель его переносит, не собирая новых данных: изменим тестовые кадры сами.

```python
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
forest = RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr])

tests = {
    "как есть": X[te],
    "сдвиг на 4 пикселя": np.roll(X[te], 4, axis=2),
    "свет тусклее на 30 %": X[te] * 0.7,
}
for name, Z in tests.items():
    print(f"{name:22} {forest.score(flat(Z), y[te]):.3f}")
```

**Что здесь происходит:**

- `np.roll(X[te], 4, axis=2)` — у всех тестовых кадров сдвиг на 4 пикселя вправо (ось 2 — столбцы; ось 0 — номер кадра, её не трогаем).
- `X[te] * 0.7` — все пиксели темнее на 30 %, как при тусклом вечернем свете.
- Модель одна и та же, обучена один раз; меняем только тест.

Сдвиг стоит леса около 9 пунктов точности. А тусклый свет обрушивает её до 0.47 — модель угадывает хуже, чем через раз. Она выучила не «форму», а «тёмные пиксели темнее такого-то порога»: в тусклом кадре тёмным становится весь поднос.

::: predict
```python static
import numpy as np
img = np.array([[0.8, 0.8, 0.3, 0.3]])
dim = img * 0.7
norm = lambda z: (z - z.mean()) / z.std()
print(np.allclose(norm(img), norm(dim)))
```

- `False`
- [x] `True`
- `Ошибка: деление на ноль`

Почему: умножение на 0.7 уменьшает в 0.7 раза и среднее, и стандартное отклонение. После вычитания среднего и деления на разброс множитель сокращается. Нормированный кадр не зависит от общей яркости.
:::

Проверим на цифрах. Кадр `[0.8, 0.8, 0.3, 0.3]`: среднее 0.55, стандартное отклонение 0.25. Нормированный: (0.8 − 0.55) / 0.25 = 1 и (0.3 − 0.55) / 0.25 = −1 → `[1, 1, −1, −1]`. Тусклый кадр `[0.56, 0.56, 0.21, 0.21]`: среднее 0.385, отклонение 0.175 → (0.56 − 0.385) / 0.175 = 1 и −1 — то же самое.

::: figure frame-norm
Кадр из примера днём и вечером (× 0.7): числа разные, а после вычитания среднего и деления на разброс — одинаковые `[1, 1, −1, −1]`.
:::

::: tip Аналогия
Нормировка кадра — как оценка «на фоне класса»: учитель, который ставит оценки относительно среднего по классу, одинаково выделит лучшего ученика и в сильном, и в слабом классе. Модели нужно «темнее остального в этом кадре», а не «темнее 0.4». Хромает аналогия в одном: если в кадре почти нет разброса (пустой ровный поднос), деление на маленький разброс раздувает шум — к стандартному отклонению прибавляют небольшое число.
:::

Это подсказывает лечение: перед моделью нормировать каждый кадр по его собственным среднему и разбросу. Тогда «тёмное» означает «темнее остального в этом кадре», а не «темнее 0.4».

::: quiz
Модель отлично распознаёт выпечку на дневных снимках, но вечером ошибается. Что это?

- [x] Сдвиг данных: при другом освещении пиксели другие, а модель училась только на дне
  > Решения — добавить вечерние снимки в обучение, аугментацию яркостью или нормировку картинок.
- [ ] Модель переобучилась на тесте
  > Тест был дневным — модель с ним справляется. Проблема в новых условиях.
- [ ] Вечером выпечка другая
  > Выпечка та же — изменилось освещение.
- [ ] Нужно больше деревьев в лесу
  > Больше деревьев не научит модель вечернему свету.
:::

{{practice: stress, light}}

## Практика

## task: flat | Картинки в таблицу | warmup

Превратите `X` (форма `(2000, 32, 32)`) в таблицу `X2d` формы `(2000, 1024)`. Сохраните `n_features` — число признаков, и `back` — первую строку `X2d`, превращённую обратно в картинку 32 × 32.

### setup
```python
import numpy as np
X = np.load("showcase.npz")["X"] / 255
```

### starter
```python
import numpy as np

```

### check
```python
import numpy as _np
X0 = _np.load('showcase.npz')['X'] / 255
a = need('X2d')
assert a.shape == (2000, 1024), f'X2d.shape = {a.shape}.'
assert _np.allclose(a[5], X0[5].ravel()), 'Строки X2d — картинки, вытянутые построчно (reshape).'
assert need('n_features') == 1024, f'n_features = {need("n_features")}.'
assert _np.asarray(need('back')).shape == (32, 32) and _np.allclose(need('back'), X0[0]), 'back — X2d[0].reshape(32, 32).'
```

### hint
`-1` в `reshape` значит «посчитай этот размер сам»: 2000 × 32 × 32 = 2000 × 1024.

### hint
`X.reshape(len(X), -1)`; обратно — `.reshape(32, 32)`.

### solution
```python
import numpy as np

X2d = X.reshape(len(X), -1)
n_features = X2d.shape[1]
back = X2d[0].reshape(32, 32)
```

## task: p-knn | kNN на пикселях | warmup

Соберите код, который обучает kNN с 5 соседями и печатает долю верных на тесте (3 знака).

### parsons
```python
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
d = np.load("showcase.npz")
X2d, y = d["X"].reshape(2000, -1) / 255, d["y"]
X_train, X_test, y_train, y_test = train_test_split(X2d, y, test_size=0.25, random_state=42, stratify=y)
knn = KNeighborsClassifier(5).fit(X_train, y_train)
print(round(knn.score(X_test, y_test), 3))
```

### check
```python
import numpy as _np
from sklearn.model_selection import train_test_split as _tts
from sklearn.neighbors import KNeighborsClassifier as _K
d0 = _np.load('showcase.npz'); A, y0 = d0['X'].reshape(2000, -1) / 255, d0['y']
a, b, c, e = _tts(A, y0, test_size=0.25, random_state=42, stratify=y0)
w = round(_K(5).fit(a, c).score(b, e), 3)
assert _lines == [str(w)], f'Сейчас: {_lines}.'
```

### hint
Данные → разбиение → модель → печать.

### hint
`X2d` строится из картинок `reshape(2000, -1)`, и только потом его можно разбивать.

## task: confusion | Кого с кем путают | base

Обучите `RandomForestClassifier(100, random_state=0)` на пикселях (разбиение по индексам `tr, te` дано в заготовке). Сохраните `cm` — DataFrame матрицы ошибок с названиями классов в индексе и столбцах, `per_class` — Series доли верных по каждому истинному классу (полнота, 3 знака), и `worst_pair` — кортеж `(истинный класс, ответ модели)` с наибольшим числом ошибок.

### setup
```python
import numpy as np
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y, classes = d["X"] / 255, d["y"], d["classes"]
X2d = X.reshape(len(X), -1)
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import confusion_matrix as _cmf
d0 = _np.load('showcase.npz'); A, y0, c0 = d0['X'].reshape(2000, -1) / 255, d0['y'], [str(c) for c in d0['classes']]
tr, te = _tts(_np.arange(2000), test_size=0.25, random_state=42, stratify=y0)
p = _RF(100, random_state=0).fit(A[tr], y0[tr]).predict(A[te])
M = _pd.DataFrame(_cmf(y0[te], p), index=c0, columns=c0)
g = need('cm', _pd.DataFrame)
assert [str(i) for i in g.index] == c0 and [str(i) for i in g.columns] == c0, 'Индекс и столбцы cm — названия классов по порядку.'
assert (g.values == M.values).all(), f'cm не совпадает:\n{M}'
pc = _pd.Series(_np.diag(M.values) / M.values.sum(1), index=c0).round(3)
gp = need('per_class', _pd.Series)
assert all(close(gp[k], pc[k], 0.0015) for k in c0), f'per_class:\n{gp}\nа нужно\n{pc}'
off = M.values.copy(); _np.fill_diagonal(off, 0)
i, j = _np.unravel_index(off.argmax(), off.shape)
assert tuple(str(v) for v in need('worst_pair')) == (c0[i], c0[j]), f'worst_pair = {need("worst_pair")}, а нужно {(c0[i], c0[j])}.'
```

### hint
Сначала обучите лес на `X2d[tr]` и получите `pred = forest.predict(X2d[te])`.

### hint
`confusion_matrix(y[te], pred)` → `pd.DataFrame(..., index=classes, columns=classes)`. Полнота — диагональ (`np.diag`), делённая на суммы строк (`.sum(axis=1)`).

### hint
Для худшей пары скопируйте матрицу, обнулите диагональ (`np.fill_diagonal(off, 0)`) и найдите максимум: `i, j = np.unravel_index(off.argmax(), off.shape)` — номера строки (правда) и столбца (ответ).

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

forest = RandomForestClassifier(100, random_state=0).fit(X2d[tr], y[tr])
pred = forest.predict(X2d[te])
names = [str(c) for c in classes]
cm = pd.DataFrame(confusion_matrix(y[te], pred), index=names, columns=names)
per_class = pd.Series(np.diag(cm.values) / cm.values.sum(axis=1), index=names).round(3)
off = cm.values.copy()
np.fill_diagonal(off, 0)
i, j = np.unravel_index(off.argmax(), off.shape)
worst_pair = (names[i], names[j])
print(cm, per_class, worst_pair, sep="\n\n")
```

### explain
Хуже всего лес узнаёт круассаны — и чаще всего называет их печеньем. Для дела это не страшно: перепутать два вида выпечки обидно, но витрина не пустая. Для задачи «допечь вовремя» важнее строка и столбец «пусто» — там ошибок единицы.

## task: importance | Куда смотрит лес | base

Обучите `RandomForestClassifier(100, random_state=0)` на пикселях обучающей части. Сложите `feature_importances_` в картинку `imp` 32 × 32. Сохраните `center_share` — долю важности в центре 16 × 16 (строки и столбцы 8…23), `border_share` — в рамке шириной 4 пикселя по краю кадра (всё, кроме `[4:28, 4:28]`), обе — 3 знака, и `top_pixel` — кортеж `(строка, столбец)` самого важного пикселя.

### setup
```python
import numpy as np
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
```

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

```

### check
```python
import numpy as _np
from sklearn.ensemble import RandomForestClassifier as _RF
X0, y0, tr0 = need('X'), need('y'), need('tr')
im = _RF(100, random_state=0).fit(X0[tr0].reshape(len(tr0), -1), y0[tr0]).feature_importances_.reshape(32, 32)
assert _np.asarray(need('imp')).shape == (32, 32) and _np.allclose(need('imp'), im), 'imp — feature_importances_.reshape(32, 32) леса, обученного на X[tr].'
assert close(need('center_share'), round(float(im[8:24, 8:24].sum()), 3), 0.0011), f'center_share = {need("center_share")}.'
assert close(need('border_share'), round(float(im.sum() - im[4:28, 4:28].sum()), 3), 0.0011), f'border_share = {need("border_share")}.'
r, c = _np.unravel_index(im.argmax(), im.shape)
assert tuple(int(v) for v in need('top_pixel')) == (int(r), int(c)), f'top_pixel = {need("top_pixel")}, а нужно {(int(r), int(c))}.'
```

### hint
Лес обучается на таблице: `flat(X[tr])`. Важности — `forest.feature_importances_`, 1024 числа в порядке пикселей; `reshape(32, 32)` возвращает их на места.

### hint
Рамка = всё − внутренний квадрат: `imp.sum() - imp[4:28, 4:28].sum()`.

### hint
Координаты максимума в двумерном массиве: `np.unravel_index(imp.argmax(), imp.shape)`.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

forest = RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr])
imp = forest.feature_importances_.reshape(32, 32)
center_share = round(float(imp[8:24, 8:24].sum()), 3)
border_share = round(float(imp.sum() - imp[4:28, 4:28].sum()), 3)
r, c = np.unravel_index(imp.argmax(), imp.shape)
top_pixel = (int(r), int(c))
print(center_share, border_share, top_pixel)
```

### explain
Центр — четверть площади, но больше половины важности. Рамка шириной 4 пикселя — почти половина площади (1024 − 576 = 448 пикселей из 1024), а важности у неё лишь около шестой части: туда выпечка заходит редко, и лес почти не задаёт про неё вопросов. Это и делает лес уязвимым к сдвигу: выпечка, съехавшая к краю, оказывается в зоне, где у модели почти нет «знаний».

## task: knn-k | Сколько соседей брать | base

Обучите `KNeighborsClassifier(k)` на пикселях для `k` из `[1, 3, 5, 15, 40]`. Сохраните `acc_by_k` — словарь `{k: доля верных на тесте}` (3 знака) и `best_k`. В `drop_1_to_40` — насколько упала точность от `k=1` до `k=40` (3 знака).

### setup
```python
import numpy as np
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
```

### starter
```python
from sklearn.neighbors import KNeighborsClassifier

```

### check
```python
from sklearn.neighbors import KNeighborsClassifier as _K
X0, y0, tr0, te0 = need('X'), need('y'), need('tr'), need('te')
fl = lambda Z: Z.reshape(len(Z), -1)
w = {k: round(_K(k).fit(fl(X0[tr0]), y0[tr0]).score(fl(X0[te0]), y0[te0]), 3) for k in [1, 3, 5, 15, 40]}
g = {int(k): v for k, v in need('acc_by_k', dict).items()}
assert all(close(g[k], w[k], 0.0011) for k in w), f'acc_by_k = {g}, а нужно {w}.'
assert need('best_k') == max(w, key=w.get), f'best_k = {need("best_k")}.'
assert close(need('drop_1_to_40'), round(w[1] - w[40], 3), 0.0021), f'drop_1_to_40 = {need("drop_1_to_40")}.'
```

### hint
Словарное выражение по `k`: обучить на `flat(X[tr])`, оценить на `flat(X[te])`.

### hint
`acc_by_k = {k: round(KNeighborsClassifier(k).fit(flat(X[tr]), y[tr]).score(flat(X[te]), y[te]), 3) for k in [...]}`; `best_k = max(acc_by_k, key=acc_by_k.get)`.

### solution
```python
from sklearn.neighbors import KNeighborsClassifier

acc_by_k = {k: round(KNeighborsClassifier(k).fit(flat(X[tr]), y[tr]).score(flat(X[te]), y[te]), 3)
            for k in [1, 3, 5, 15, 40]}
best_k = max(acc_by_k, key=acc_by_k.get)
drop_1_to_40 = round(acc_by_k[1] - acc_by_k[40], 3)
print(acc_by_k, best_k, drop_1_to_40)
```

### explain
Обычно больше соседей — устойчивее ответ (глава 6). Здесь наоборот: лучше всего один ближайший сосед, и с ростом `k` точность падает. Причина — пиксельное расстояние из урока «Картинка — это массив чисел». Самый близкий кадр — обычно кадр той же выпечки, лежащей почти в том же месте; это хороший сосед. А следующие десятки «близких» уже определяются в основном совпадением фона и положения, а не формой, — среди них много чужих классов. Когда мера сходства плохая, «голосование большинства» её не спасает.

Заметьте ещё: 1-NN (около 0.92) на обычном тесте даже чуть обходит лес из 100 деревьев (0.91). Вы не ошиблись — среди 1500 обучающих кадров почти для каждого тестового находится та же выпечка почти в том же месте. Устойчивее леса он от этого не становится: на тусклых кадрах (× 0.7) 1-NN падает примерно до 0.56 — он сравнивает те же пиксели, что и лес. Дальше в уроке мы работаем с лесом не потому, что он точнее, а потому, что у него есть важности пикселей и его удобно переучивать на расширенной выборке.

## task: augment | Аугментация | plus

Напишите `augment(Z, labels, rng)` как в уроке: исходные кадры + отражённые по горизонтали + сдвинутые на случайные `(dy, dx)` из `rng.integers(-4, 5, size=(len(Z), 2))`. Примените к обучающей части с `rng = np.random.default_rng(0)` и обучите лес `RandomForestClassifier(100, random_state=0)`. Сохраните `acc_base`, `acc_aug` (3 знака на обычном тесте) и `n_train_aug` — размер расширенной выборки.

### setup
```python
import numpy as np
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
```

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def augment(Z, labels, rng):
    ...

```

### check
```python
import numpy as _np
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
d0 = _np.load('showcase.npz'); X0, y0 = d0['X'] / 255, d0['y']
tr, te = _tts(_np.arange(2000), test_size=0.25, random_state=42, stratify=y0)
f = need('augment')
Za, la = f(X0[tr][:5], y0[tr][:5], _np.random.default_rng(1))
assert len(Za) == 15 and len(la) == 15, 'augment должна вернуть втрое больше кадров и меток.'
assert _np.allclose(Za[5], X0[tr][0][:, ::-1]), 'Вторая треть — отражения по горизонтали (Z[:, :, ::-1]).'
r = _np.random.default_rng(0); sh = r.integers(-4, 5, size=(len(tr), 2))
Xs = _np.stack([_np.roll(z, tuple(s), axis=(0, 1)) for z, s in zip(X0[tr], sh)])
Xa = _np.concatenate([X0[tr], X0[tr][:, :, ::-1], Xs]); ya = _np.concatenate([y0[tr]] * 3)
fl = lambda Z: Z.reshape(len(Z), -1)
wb = round(_RF(100, random_state=0).fit(fl(X0[tr]), y0[tr]).score(fl(X0[te]), y0[te]), 3)
wa = round(_RF(100, random_state=0).fit(fl(Xa), ya).score(fl(X0[te]), y0[te]), 3)
assert need('n_train_aug') == 4500, f'n_train_aug = {need("n_train_aug")}.'
assert close(need('acc_base'), wb, 0.005), f'acc_base = {need("acc_base")}, а нужно {wb}.'
assert close(need('acc_aug'), wa, 0.006), f'acc_aug = {need("acc_aug")}, а нужно {wa}.'
```

### hint
Функция возвращает две вещи: склеенные кадры и склеенные метки. Порядок кусков — исходные, отражённые, сдвинутые.

### hint
Сдвиг одной картинки: `np.roll(z, (dy, dx), axis=(0, 1))`. Метки — `np.concatenate([labels, labels, labels])`.

### hint
Сдвиги удобно получить одним вызовом `rng.integers(-4, 5, size=(len(Z), 2))` до цикла — по паре `(dy, dx)` на кадр.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def augment(Z, labels, rng):
    flipped = Z[:, :, ::-1]
    shifts = rng.integers(-4, 5, size=(len(Z), 2))
    shifted = np.stack([np.roll(z, tuple(s), axis=(0, 1)) for z, s in zip(Z, shifts)])
    return np.concatenate([Z, flipped, shifted]), np.concatenate([labels, labels, labels])

X_aug, y_aug = augment(X[tr], y[tr], np.random.default_rng(0))
n_train_aug = len(X_aug)
acc_base = round(RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr]).score(flat(X[te]), y[te]), 3)
acc_aug = round(RandomForestClassifier(100, random_state=0).fit(flat(X_aug), y_aug).score(flat(X[te]), y[te]), 3)
print(n_train_aug, acc_base, acc_aug)
```

### explain
Аугментация добавила пять пунктов точности на обычном тесте: лес увидел выпечку в большем числе положений и меньше полагается на «центр кадра». Две ошибки, которые встречаются чаще всего: аугментировать весь набор до разбиения (копии тестовых кадров попадают в обучение — тест завышен) и забыть повторить метки (тогда `fit` упадёт: кадров 4500, а меток 1500). Ещё одна тонкость: отражение подходит не для всего — для цифр или надписей зеркальная «5» уже не «5».

## task: stress | Стресс-тест сдвигом | plus

Сравните устойчивость к сдвигу трёх моделей: лес на пикселях, лес на пикселях с аугментацией (`X_aug`, `y_aug` — в заготовке) и лес на 9 глобальных признаках из урока «Свёртка и фильтры» (функция `global_features` — в заготовке). Все леса — `RandomForestClassifier(100, random_state=0)`. Тестовые кадры сдвиньте на 4 пикселя вправо: `np.roll(X[te], 4, axis=2)`. Сохраните `stress` — DataFrame с индексом `["пиксели", "пиксели + аугментация", "глобальные признаки"]` и столбцами `обычный`, `сдвиг` (доли верных, 3 знака).

### setup
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
_r = np.random.default_rng(0); _sh = _r.integers(-4, 5, size=(len(tr), 2))
X_aug = np.concatenate([X[tr], X[tr][:, :, ::-1], np.stack([np.roll(z, tuple(s), axis=(0, 1)) for z, s in zip(X[tr], _sh)])])
y_aug = np.concatenate([y[tr]] * 3)
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
LAP = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
BLUR = np.ones((3, 3)) / 9
def global_features(Z):
    fm = lambda k: np.stack([ndi.correlate(z, k, mode="nearest") for z in Z]).reshape(len(Z), -1)
    cols = []
    for k in [SX, SX.T, LAP]:
        a = np.abs(fm(k)); cols += [a.mean(1), a.max(1)]
    b = fm(BLUR); cols += [b.min(1), b.mean(1), (b < 0.4).mean(1)]
    return np.column_stack(cols)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

X_shift = np.roll(X[te], 4, axis=2)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
X0, y0, tr0, te0 = need('X'), need('y'), need('tr'), need('te')
gf, fl = need('global_features'), need('flat')
Xs = _np.roll(X0[te0], 4, axis=2)
m1 = _RF(100, random_state=0).fit(fl(X0[tr0]), y0[tr0])
m2 = _RF(100, random_state=0).fit(fl(need('X_aug')), need('y_aug'))
m3 = _RF(100, random_state=0).fit(gf(X0[tr0]), y0[tr0])
w = _pd.DataFrame({'обычный': [m1.score(fl(X0[te0]), y0[te0]), m2.score(fl(X0[te0]), y0[te0]), m3.score(gf(X0[te0]), y0[te0])],
                   'сдвиг': [m1.score(fl(Xs), y0[te0]), m2.score(fl(Xs), y0[te0]), m3.score(gf(Xs), y0[te0])]},
                  index=['пиксели', 'пиксели + аугментация', 'глобальные признаки']).round(3)
g = need('stress', _pd.DataFrame)
assert list(g.index) == list(w.index) and list(g.columns) == ['обычный', 'сдвиг'], f'Индекс {list(g.index)}, столбцы {list(g.columns)}.'
assert ((g - w).abs() < 0.006).all().all(), f'stress:\n{g}\nа нужно\n{w}'
```

### hint
Сдвинутый тест — один раз: `X_shift = np.roll(X[te], 4, axis=2)`. Его используют все три модели.

### hint
Три модели, каждая — `.fit(...)` и два `.score(...)`. Для глобальных признаков и обучение, и оба теста пропустите через `global_features`.

### hint
`pd.DataFrame({"обычный": [три числа], "сдвиг": [три числа]}, index=[...]).round(3)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

X_shift = np.roll(X[te], 4, axis=2)
m_pix = RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr])
m_aug = RandomForestClassifier(100, random_state=0).fit(flat(X_aug), y_aug)
m_glob = RandomForestClassifier(100, random_state=0).fit(global_features(X[tr]), y[tr])

stress = pd.DataFrame({
    "обычный": [m_pix.score(flat(X[te]), y[te]), m_aug.score(flat(X[te]), y[te]), m_glob.score(global_features(X[te]), y[te])],
    "сдвиг": [m_pix.score(flat(X_shift), y[te]), m_aug.score(flat(X_shift), y[te]), m_glob.score(global_features(X_shift), y[te])],
}, index=["пиксели", "пиксели + аугментация", "глобальные признаки"]).round(3)
print(stress)
```

### explain
Лес на пикселях теряет около 9 пунктов. С аугментацией точность выше в обоих столбцах (на сдвинутых кадрах около 0.87 против 0.82), но падение почти такое же: обучающие сдвиги были случайными в обе стороны и редко ровно на 4 вправо. На глобальных признаках сдвиг почти ничего не меняет (около 0.95): признаки по построению не знают, где лежит выпечка. Аугментация учит терпимости «на примерах», признаки дают её «по конструкции». Свёрточные сети используют оба приёма сразу.

## task: bright-aug | Аугментация яркостью | plus

Нормировка — не единственное лекарство от вечернего света. Добавьте к обучающей части её копию, где каждый кадр умножен на свой случайный множитель из `rng.uniform(0.6, 1.1, size=len(tr))` (`rng = np.random.default_rng(0)`). Обучите `RandomForestClassifier(100, random_state=0)` на 3000 кадрах. Сохраните `acc_normal` и `acc_dim` — точность на обычном тесте и на тесте × 0.7 (3 знака), и `acc_dim_base` — точность на тесте × 0.7 у леса без аугментации.

### setup
```python
import numpy as np
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
```

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

rng = np.random.default_rng(0)

```

### check
```python
import numpy as _np
from sklearn.ensemble import RandomForestClassifier as _RF
X0, y0, tr0, te0 = need('X'), need('y'), need('tr'), need('te')
fl = lambda Z: Z.reshape(len(Z), -1)
fac = _np.random.default_rng(0).uniform(0.6, 1.1, size=len(tr0))
Xa = _np.concatenate([X0[tr0], X0[tr0] * fac[:, None, None]]); ya = _np.concatenate([y0[tr0], y0[tr0]])
m = _RF(100, random_state=0).fit(fl(Xa), ya); b = _RF(100, random_state=0).fit(fl(X0[tr0]), y0[tr0])
assert close(need('acc_normal'), round(m.score(fl(X0[te0]), y0[te0]), 3), 0.006), f'acc_normal = {need("acc_normal")}.'
assert close(need('acc_dim'), round(m.score(fl(X0[te0] * 0.7), y0[te0]), 3), 0.006), f'acc_dim = {need("acc_dim")}.'
assert close(need('acc_dim_base'), round(b.score(fl(X0[te0] * 0.7), y0[te0]), 3), 0.006), f'acc_dim_base = {need("acc_dim_base")}.'
```

### hint
Множители — массив длины 1500. Чтобы умножить каждый кадр `(32, 32)` на свой множитель, добавьте множителю две оси: `fac[:, None, None]`.

### hint
`X_aug = np.concatenate([X[tr], X[tr] * fac[:, None, None]])`, `y_aug = np.concatenate([y[tr], y[tr]])`.

### hint
Базовый лес — обычный `fit(flat(X[tr]), y[tr])`; оба леса проверьте на `flat(X[te] * 0.7)`.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

rng = np.random.default_rng(0)
fac = rng.uniform(0.6, 1.1, size=len(tr))
X_aug = np.concatenate([X[tr], X[tr] * fac[:, None, None]])
y_aug = np.concatenate([y[tr], y[tr]])
aug = RandomForestClassifier(100, random_state=0).fit(flat(X_aug), y_aug)
base = RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr])
acc_normal = round(aug.score(flat(X[te]), y[te]), 3)
acc_dim = round(aug.score(flat(X[te] * 0.7), y[te]), 3)
acc_dim_base = round(base.score(flat(X[te] * 0.7), y[te]), 3)
print(acc_normal, acc_dim, acc_dim_base)
```

### explain
Лес, который видел тёмные копии, на тусклом тесте даёт около 0.90 вместо 0.47 — и на обычном тесте не хуже прежнего (даже чуть лучше: аугментация добавила разнообразия). Нормировка из следующей задачи делает модель нечувствительной к яркости «по построению», аугментация — «на примерах». Аугментация защищает только от того, что вы предусмотрели: если вечером свет окажется 0.5, а копии были от 0.6, модель снова начнёт ошибаться.

## task: light | Вечерний свет | star

Проверьте модели на «вечерних» кадрах: тест, умноженный на 0.7. Напишите `normalize(Z)` — для массива кадров `(n, 32, 32)` вернуть таблицу `(n, 1024)`, где каждая строка — кадр минус его среднее, делённый на его стандартное отклонение. Обучите `RandomForestClassifier(100, random_state=0)` на сырых пикселях и на нормированных. Сохраните `light` — словарь `{"сырые": (обычный, тусклый), "нормированные": (обычный, тусклый)}` с долями верных (3 знака).

### setup
```python
import numpy as np
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
flat = lambda Z: Z.reshape(len(Z), -1)
```

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def normalize(Z):
    ...

X_dim = X[te] * 0.7

```

### check
```python
import numpy as _np
from sklearn.ensemble import RandomForestClassifier as _RF
X0, y0, tr0, te0 = need('X'), need('y'), need('tr'), need('te')
f = need('normalize')
t = f(X0[:3])
assert t.shape == (3, 1024), f'normalize(X[:3]).shape = {t.shape}, а нужно (3, 1024).'
assert _np.allclose(t.mean(1), 0, atol=1e-9) and _np.allclose(t.std(1), 1), 'У каждой строки среднее 0 и стандартное отклонение 1.'
fl = lambda Z: Z.reshape(len(Z), -1)
nz = lambda Z: (fl(Z) - fl(Z).mean(1, keepdims=True)) / fl(Z).std(1, keepdims=True)
Xd = X0[te0] * 0.7
a = _RF(100, random_state=0).fit(fl(X0[tr0]), y0[tr0]); b = _RF(100, random_state=0).fit(nz(X0[tr0]), y0[tr0])
w = {'сырые': (round(a.score(fl(X0[te0]), y0[te0]), 3), round(a.score(fl(Xd), y0[te0]), 3)),
     'нормированные': (round(b.score(nz(X0[te0]), y0[te0]), 3), round(b.score(nz(Xd), y0[te0]), 3))}
g = need('light', dict)
assert set(g) == set(w), f'Ключи: {list(g)}.'
assert all(close(g[k][i], w[k][i], 0.006) for k in w for i in range(2)), f'light = {g}, а нужно {w}.'
```

### hint
Нормировать нужно каждую строку (кадр) отдельно: среднее и отклонение — по `axis=1`. `keepdims=True` оставляет форму `(n, 1)`, чтобы вычитание шло построчно.

### hint
`A = Z.reshape(len(Z), -1)`; `(A - A.mean(axis=1, keepdims=True)) / A.std(axis=1, keepdims=True)`. Модель на нормированных признаках проверяйте тоже на нормированных кадрах: `normalize(X_dim)`.

### hint
Две модели: `raw` на `flat(X[tr])` и `nrm` на `normalize(X[tr])`. Каждую — на своём обычном и тусклом тесте.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def normalize(Z):
    A = Z.reshape(len(Z), -1)
    return (A - A.mean(axis=1, keepdims=True)) / A.std(axis=1, keepdims=True)

X_dim = X[te] * 0.7
raw = RandomForestClassifier(100, random_state=0).fit(flat(X[tr]), y[tr])
nrm = RandomForestClassifier(100, random_state=0).fit(normalize(X[tr]), y[tr])
light = {
    "сырые": (round(raw.score(flat(X[te]), y[te]), 3), round(raw.score(flat(X_dim), y[te]), 3)),
    "нормированные": (round(nrm.score(normalize(X[te]), y[te]), 3), round(nrm.score(normalize(X_dim), y[te]), 3)),
}
print(light)
```

### explain
Сырая модель на тусклых кадрах падает примерно до 0.47, нормированная не замечает разницы: умножение на 0.7 после нормировки исчезает полностью. Нормировка подняла точность и на обычном тесте — около 0.94 против 0.91: у дневных кадров тоже разная общая яркость, и лесу, похоже, больше не приходится тратить на неё вопросы. В жизни вечерний свет — не только «темнее», но и другой контраст и цвет, поэтому нормировка помогает не на 100 %. Насколько — проверим в проекте на настоящих вечерних кадрах.
