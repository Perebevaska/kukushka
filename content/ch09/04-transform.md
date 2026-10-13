---
title: Преобразовать признаки матрицей
files: [deliveries.csv]
lead: "Если умножить таблицу признаков на матрицу, получатся новые признаки — смеси старых. Разбираемся, когда такое преобразование ничего не теряет, почему линейная регрессия его «не замечает», а дерево — замечает. Это основа проекта главы."
recap:
  - "X @ P — новая таблица: каждый новый признак — взвешенная сумма старых (столбец P — веса смеси)."
  - "Масштабирование — частный случай: умножение на диагональную матрицу (и сдвиг на среднее)."
  - "Если P обратима, исходные данные восстанавливаются: X = (X @ P) @ P⁻¹. Информация не теряется."
  - "Линейная регрессия на X @ P даёт те же прогнозы, что на X: веса просто становятся P⁻¹ @ w."
  - "Деревья, kNN и важности признаков к таким преобразованиям чувствительны: у них другие пороги и расстояния."
  - "Необратимая P (например, выкинуть столбец) теряет информацию, и качество может упасть."
---

## Новые признаки как смеси старых

Возьмём три признака доставки: расстояние, число позиций, флаг пешего курьера. Умножим таблицу $X$ ($n \times 3$) на матрицу $P$ ($3 \times 3$) — получим новую таблицу той же формы. Каждый новый признак — смесь старых с весами из столбца $P$:

```python
import numpy as np
X = np.array([[1.0, 2, 1],
              [4.0, 1, 0]])
P = np.array([[1.0, 0, 0.5],
              [0, 1, 0],
              [0, 0.5, 2]])
print(X @ P)
```

**Что здесь происходит:** каждая строка $X$ умножается на каждый столбец $P$. Первая строка [1, 2, 1] (1 км, 2 позиции, пеший):

- новый признак 1: 1 · 1 + 2 · 0 + 1 · 0 = **1**;
- новый признак 2: 1 · 0 + 2 · 1 + 1 · 0.5 = **2.5**;
- новый признак 3: 1 · 0.5 + 2 · 0 + 1 · 2 = **2.5**.

Вторая строка [4, 1, 0] даёт 4, 1 и 0.5 · 4 + 0 = **2**. Итог — [[1, 2.5, 2.5], [4, 1, 2]].

::: figure mix-features
Первая доставка до и после умножения на P. Выделен второй столбец P — «рецепт» признака f2: взять 0 частей км, 1 часть позиций и 0.5 части флага пешего.
:::

Форма: (n × **3**) @ (**3** × 3) → (n × 3). Сколько столбцов у P — столько новых признаков.

::: sql
В SQL это вычисляемые столбцы: `SELECT distance_km AS f1, items + 0.5 * walk AS f2, 0.5 * distance_km + 2 * walk AS f3 FROM deliveries`. Матрица P — компактная запись всех таких формул сразу.
:::

Первый новый признак — просто расстояние (столбец $P$: 1, 0, 0). Второй — «позиции + половина флага пешего». Третий — «половина расстояния + два флага». Смысла у них немного, но числа содержат всю исходную информацию — если $P$ можно «отменить».

::: tip Аналогия
Матрица P — как карта купажа у обжарщика: каждый бленд (новый признак) — это смесь сортов (старых признаков) в своих долях, по одному столбцу на бленд. Если знать карту и блендов столько же, сколько сортов, а доли не повторяют друг друга, по составу блендов можно вычислить, сколько было каждого сорта. Хромает аналогия в одном: настоящий кофе после смешивания уже не разделить, а числа — можно, умножив на обратную матрицу.
:::

{{practice: mix}}

## Масштаб — тоже матрица

Знакомый `StandardScaler` (глава 7) — тоже такое преобразование: вычесть среднее и умножить на диагональную матрицу с числами $1/\sigma$ на диагонали.

```python
import numpy as np
from sklearn.preprocessing import StandardScaler
X = np.array([[1.0, 2, 1], [4.0, 1, 0], [6.0, 4, 0], [2.5, 3, 1]])
D = np.diag(1 / X.std(axis=0))                 # диагональная матрица 1/σ
manual = (X - X.mean(axis=0)) @ D
print(np.allclose(manual, StandardScaler().fit_transform(X)))
```

**Что здесь происходит:**

- `X.std(axis=0)` — разброс каждого столбца; `1 / ...` — во сколько раз его сжать.
- `np.diag(...)` — матрица 3 × 3 с этими числами на диагонали и нулями вокруг.
- `(X - X.mean(axis=0)) @ D` — сначала сдвиг (центрирование), потом растяжение. Нули вне диагонали гарантируют, что столбцы не смешиваются: новый первый признак зависит только от старого первого.

`np.diag(v)` строит матрицу с вектором `v` на диагонали и нулями вокруг. Умножение на неё растягивает каждый столбец в своё число раз. То же самое делает поэлементное `X * v` — матричная запись нужна, чтобы увидеть масштабирование как частный случай общего P.

::: predict
```python static
import numpy as np
X = np.ones((100, 3))
P = np.array([[1, 0], [0, 1], [0, 0]])
print((X @ P).shape)
```

- `(100, 3)`
- [x] `(100, 2)`
- `(3, 2)`

Почему: у P два столбца — значит, два новых признака. Третий исходный признак умножается на нули и пропадает. Такая P (3 × 2) не квадратная, обратной у неё нет, и выкинутый столбец уже не восстановить.
:::

{{practice: diag}}

## Обратимо — значит, ничего не потеряли

Если у $P$ есть обратная матрица, исходные признаки восстанавливаются:

$$
(XP)P^{-1} = X(PP^{-1}) = XI = X
$$

```python
import numpy as np
X = np.array([[1.0, 2, 1], [4.0, 1, 0], [6.0, 4, 0]])
P = np.random.default_rng(1).normal(size=(3, 3))     # случайная матрица — почти всегда обратима
hidden = X @ P
print(hidden.round(2))                               # по этим числам ничего не понятно
print((hidden @ np.linalg.inv(P)).round(6))          # а с ключом P всё восстанавливается
```

**Что здесь происходит:**

- `default_rng(1).normal(size=(3, 3))` — 9 случайных чисел, фиксированный seed делает P воспроизводимой.
- `hidden = X @ P` — каждый столбец `hidden` смешивает все три исходных признака со случайными весами, в том числе отрицательными.
- `hidden @ np.linalg.inv(P)` — умножение на обратную справа; `.round(6)` прячет хвосты вроде 0.9999999999.

Случайная матрица почти наверняка обратима. Без знания $P$ по числам `hidden` трудно понять, что было в исходной таблице, — а с $P$ восстанавливается всё. На этом построен проект главы.

::: figure key-roundtrip
Сверху — обратимый ключ: X → X @ P → обратно X, а линейная регрессия на смесях даёт тот же прогноз с весами P⁻¹ · w (раздел ниже). Снизу — необратимая P 3 × 2: один признак пропал, и вернуть его нечем.
:::

::: warn
Это **не** шифрование в строгом смысле: если у злоумышленника есть хотя бы несколько пар «исходная строка — преобразованная строка», $P$ находится решением системы уравнений (урок «Как обучается линейная регрессия»). Такое преобразование скрывает данные от случайного взгляда, но не от целенаправленной атаки.
:::

::: quiz
Аналитик предлагает передавать подрядчику не таблицу доставок `X` с тремя признаками, а `X @ P` со случайной обратимой `P` 3 × 3: «без `P` ничего не восстановить». В чём слабое место?

- [x] Если у подрядчика окажутся несколько пар «исходная строка — преобразованная», `P` находится решением системы уравнений
  > Преобразование линейное, а линейные системы решаются легко. Оно скрывает данные от случайного взгляда, но не от целенаправленной атаки.
- [ ] Случайная `P` почти всегда необратима, поэтому часть данных просто пропадёт
  > Наоборот: случайная квадратная матрица почти наверняка обратима, и с `P` восстанавливается всё.
- [ ] Слабого места нет: смешанные признаки нельзя связать с исходными без ключа
  > Ключ `P` — всего девять чисел, а каждая известная пара строк даёт три уравнения на них. Трёх независимых пар уже достаточно.
- [ ] Линейная регрессия на `X @ P` обучится хуже, и подрядчик это заметит
  > Качество линейной регрессии не меняется вовсе. И это вопрос не защиты, а пользы данных.
:::

{{practice: p-restore, invertible, drop-col}}

## Линейная регрессия ничего не замечает

Обучим линейную регрессию на исходных признаках и на $XP$:

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(1).normal(size=(3, 3))

lr = LinearRegression().fit(X, y)
lr_p = LinearRegression().fit(X @ P, y)
print("R² исходные:", round(r2_score(y, lr.predict(X)), 4))
print("R² X @ P:   ", round(r2_score(y, lr_p.predict(X @ P)), 4))
print("веса X @ P: ", lr_p.coef_.round(2))
print("P⁻¹ @ w:    ", (np.linalg.inv(P) @ lr.coef_).round(2))
```

**Что здесь происходит:**

- `lr` и `lr_p` — две модели на одних и тех же строках, но на разных признаках: исходных и смешанных.
- `r2_score(y, ...)` — доля объяснённого разброса; сравниваем на обучающих данных, нам важна не обобщающая способность, а то, что модели умеют одно и то же.
- `np.linalg.inv(P) @ lr.coef_` — веса первой модели, «переведённые» на язык смешанных признаков.

Качество одинаковое до четвёртого знака, а веса новой модели — ровно $P^{-1} w$. Почему: прогноз $(XP)w' = X(Pw')$. Здесь мы переставили скобки — в произведении матриц так можно: $(AB)C = A(BC)$. Переставлять сами множители нельзя ($AB \ne BA$), а скобки — можно, как у чисел $(2 \cdot 3) \cdot 4 = 2 \cdot (3 \cdot 4)$. Если взять $w' = P^{-1} w$, получится $Xw$ — тот же прогноз. Модель на $XP$ может выразить всё, что выражала модель на $X$, и наоборот, поэтому лучшие прогнозы у них совпадают.

::: predict
```python static
import numpy as np
P = np.array([[2, 0], [0, 4]])
print(np.linalg.inv(P).tolist())
```

- `[[2.0, 0.0], [0.0, 4.0]]`
- [x] `[[0.5, 0.0], [0.0, 0.25]]`
- `[[-2.0, 0.0], [0.0, -4.0]]`

Почему: диагональная матрица растягивает каждый столбец в своё число раз, обратная — сжимает обратно: 1/2 и 1/4.
:::

::: quiz
Признаки умножили на обратимую матрицу P (перемешали и смасштабировали). Что станет с качеством линейной регрессии?

- [x] Не изменится: веса пересчитаются (w' = P⁻¹w), а прогнозы останутся теми же
  > Обратимое преобразование ничего не теряет, и линейная модель подстраивается под новые координаты.
- [ ] Ухудшится: признаки перемешались
  > Для линейной модели это просто другие координаты того же пространства.
- [ ] Улучшится
  > Информации не прибавилось — качество то же.
- [ ] Изменится так же, как у дерева
  > Дерево режет по отдельным признакам, и для него смеси признаков — другие данные.
:::

{{practice: same-quality, weights, attack}}

## А дерево замечает

Решающее дерево задаёт вопросы «признак ≤ порог» по одному признаку за раз. После перемешивания признаков у него другие вопросы, и качество меняется. С kNN то же самое: меняются расстояния. Поэтому трюк с матрицей «бесплатен» только для линейных моделей.

Та же $P$ из `default_rng(1)`, что в разделе выше, R² на обучающих данных:

| модель | R² на $X$ | R² на $XP$ |
|---|---|---|
| линейная регрессия | 0.505 | 0.505 |
| дерево глубины 4 | 0.603 | 0.399 |
| kNN, 15 соседей | 0.610 | 0.585 |

Дерево потеряло треть качества: «пеший курьер» больше не отдельный столбец 0/1, а размазан по трём смесям, и найти его одним вопросом нельзя. kNN потерял меньше, 0.025: расстояния между доставками исказились, но соседи в основном остались соседями. Насколько сильно изменится качество, зависит от конкретной $P$: с другой случайной матрицей цифры будут другими, а линейная регрессия останется ровно той же. В задаче ниже эту таблицу можно собрать самому.

{{practice: tree-vs-linear}}

## Разберём вместе: куда пропал пеший курьер

Посмотрим на дерево глубины 2 — его видно целиком (`export_text`, глава 6). Обучим два дерева: на исходных признаках и на $XP$ с той же $P$ из `default_rng(1)`. Смеси назовём a, b, c.

```python
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(1).normal(size=(3, 3))

for title, data, names in [("исходные", X, ["km", "items", "walk"]),
                           ("X @ P", X @ P, ["a", "b", "c"])]:
    tree = DecisionTreeRegressor(max_depth=2, random_state=0).fit(data, y)
    print(title, "| R²:", round(r2_score(y, tree.predict(data)), 3))
    print(export_text(tree, feature_names=names, decimals=2))
```

**Что здесь происходит:**

- цикл обучает одно и то же дерево на двух таблицах: `X` и `X @ P`;
- `export_text(..., feature_names=names)` печатает вопросы дерева с нашими именами признаков; `value` в листе — среднее время доставки в этой группе.

На исходных признаках первый вопрос — про расстояние (`km <= 3.15`), второй — про пешего курьера. В листьях 28.6, 37.0, 38.9 и **68.7** минуты: дерево нашло главную группу риска — пеший на дальнем заказе, почти 69 минут.

На $XP$ вопросы задаются по смесям: сначала `b <= 5.43`, потом `c <= 1.53` или ещё раз `b <= 7.57`. В листьях 27.2, 33.7, 39.0 и 48.8 минуты. Группы «68.7 минуты» больше нет. Пеший сидит внутри b и c, но вместе с расстоянием и позициями, и ни один порог по одной смеси не отделяет его чисто. R² дерева глубины 2: **0.385 → 0.296**.

::: figure tree-mix
Два дерева глубины 2 из разбора. Слева вопросы про км и пешего курьера находят группу риска 68.7 минуты. Справа пеший растворён в смесях b и c, и такой группы нет; R² падает с 0.385 до 0.296.
:::

Что получилось — и одна оговорка: при глубине 1 смесь даже чуть лучше (0.191 против 0.166), удачная комбинация признаков иногда даёт хороший первый вопрос. Но чем глубже дерево, тем сильнее разрыв: глубина 3 — 0.542 против 0.346, глубина 4 — 0.603 против 0.399. Дерево сильно, когда признаки осмысленны сами по себе, и смешивание это ломает.

::: warn Типичные ошибки
- **Не с той стороны.** Признаки смешивает `X @ P` (P справа). `P @ X` смешивает строки — то есть разных клиентов между собой, и форма обычно даже не сходится.
- **Разные P для train и test.** Модель, обученная на `X_train @ P`, ждёт ту же P и на новых данных. Сгенерировали P заново — прогнозы мусорные.
- **`inv` для неквадратной P.** P 3 × 2 обратной не имеет — информация выброшена, и `np.linalg.inv` выдаст ошибку.
- **Вывод про веса.** Качество линейной модели не меняется, но веса смешанных признаков читать бессмысленно — «минуты на единицу смеси» ничего не значат.
:::

## Практика

## task: mix | Смесь признаков | warmup

Новый признак `score = 0.5 × km + 2 × items`. Задайте матрицу `P` (2 × 1) так, чтобы `X @ P` давала этот признак, и сохраните `score = X @ P`.

### starter
```python
import numpy as np
X = np.array([[1.0, 2], [4.0, 1], [6.0, 4]])

```

### check
```python
import numpy as _np
X0 = _np.array([[1.0, 2], [4.0, 1], [6.0, 4]])
P0 = _np.asarray(need('P'))
assert P0.shape == (2, 1), f'Форма P: {P0.shape}, нужна (2, 1).'
assert _np.allclose(need('score'), X0 @ _np.array([[0.5], [2]])), f'score = {need("score")}.'
```

### hint
Форма P — (число старых признаков) × (число новых): 2 × 1. Первое число столбца — вес km, второе — вес items.

### hint
Столбец P — веса смеси: `P = np.array([[0.5], [2]])`.

### solution
```python
import numpy as np
X = np.array([[1.0, 2], [4.0, 1], [6.0, 4]])
P = np.array([[0.5], [2]])
score = X @ P
```

## task: diag | Масштаб диагональной матрицей | warmup

Переведите расстояние из километров в метры, а время из минут в часы, умножив `X` (столбцы: км, минуты) на диагональную матрицу `D`. Сохраните `D` и `converted`.

### starter
```python
import numpy as np
X = np.array([[1.2, 30.0], [4.0, 45.0], [6.5, 72.0]])

```

### check
```python
import numpy as _np
X0 = _np.array([[1.2, 30.0], [4.0, 45.0], [6.5, 72.0]])
assert _np.allclose(need('D'), _np.diag([1000, 1 / 60])), f'D = {need("D")}. На диагонали — множители 1000 и 1/60.'
assert _np.allclose(need('converted'), X0 * [1000, 1 / 60]), 'converted = X @ D.'
```

### hint
Километры в метры — × 1000, минуты в часы — × 1/60. Эти множители стоят на диагонали.

### hint
`D = np.diag([1000, 1 / 60])`, `converted = X @ D`.

### solution
```python
import numpy as np
X = np.array([[1.2, 30.0], [4.0, 45.0], [6.5, 72.0]])
D = np.diag([1000, 1 / 60])
converted = X @ D
```

## task: p-restore | Спрятать и восстановить | warmup

Соберите код, который прячет таблицу случайной матрицей и восстанавливает её.

### parsons
```python
import numpy as np
X = np.array([[1.0, 2.0], [3.0, 4.0]])
P = np.random.default_rng(0).normal(size=(2, 2))
hidden = X @ P
restored = hidden @ np.linalg.inv(P)
print(np.allclose(restored, X))
```

### check
```python
assert _lines == ['True'], f'Сейчас: {_lines}.'
```

### hint
Восстановление — умножение на обратную матрицу справа.

### hint
Порядок: данные → ключ P → спрятать → восстановить → проверить.

## task: invertible | Обратима ли матрица | base

Для трёх матриц `P1`, `P2`, `P3` сохраните список рангов `ranks` и список `usable` — названия матриц (`"P1"`, …), которыми можно прятать данные без потерь (ранг равен размеру).

### starter
```python
import numpy as np
P1 = np.array([[1, 2, 0], [0, 1, 3], [1, 0, 1]])
P2 = np.array([[1, 2, 3], [2, 4, 6], [0, 1, 1]])
P3 = np.array([[2, 0, 0], [0, 0, 0], [0, 0, 5]])

```

### check
```python
import numpy as _np
Ps = [_np.array([[1, 2, 0], [0, 1, 3], [1, 0, 1]]), _np.array([[1, 2, 3], [2, 4, 6], [0, 1, 1]]), _np.array([[2, 0, 0], [0, 0, 0], [0, 0, 5]])]
r = [int(_np.linalg.matrix_rank(p)) for p in Ps]
assert [int(x) for x in need('ranks')] == r, f'ranks = {need("ranks")}, а нужно {r}.'
assert list(need('usable')) == [f'P{i + 1}' for i in range(3) if r[i] == 3], f'usable = {need("usable")}.'
```

### hint
`np.linalg.matrix_rank(P)` для каждой матрицы. Размер — 3, значит пригодны матрицы ранга 3.

### hint
Удобно сложить матрицы в словарь `{"P1": P1, ...}` и пройти по нему циклом: ранги — в одном списке, подходящие имена — в другом.

### solution
```python
import numpy as np
P1 = np.array([[1, 2, 0], [0, 1, 3], [1, 0, 1]])
P2 = np.array([[1, 2, 3], [2, 4, 6], [0, 1, 1]])
P3 = np.array([[2, 0, 0], [0, 0, 0], [0, 0, 5]])
mats = {"P1": P1, "P2": P2, "P3": P3}
ranks = [int(np.linalg.matrix_rank(m)) for m in mats.values()]
usable = [name for name, m in mats.items() if np.linalg.matrix_rank(m) == 3]
```

### explain
В P2 вторая строка — удвоенная первая, в P3 нулевой столбец просто стирает второй признак. После умножения на такие матрицы часть информации пропадает навсегда.

## task: drop-col | Необратимое преобразование | base

Матрица `Pd` (3 × 2) оставляет расстояние и позиции и выбрасывает флаг пешего. Сохраните её ранг `rank_d`, форму результата `shape_d` (кортеж), R² линейной регрессии на `X` (`r2_full`) и на `X @ Pd` (`r2_drop`, оба 4 знака) и `lost` — сколько R² потеряно (`r2_full − r2_drop`, 4 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Pd = np.array([[1, 0], [0, 1], [0, 0]])

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import r2_score as _r2
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
P0 = _np.array([[1, 0], [0, 1], [0, 0]])
a = round(_r2(y0, _LR().fit(X0, y0).predict(X0)), 4); b = round(_r2(y0, _LR().fit(X0 @ P0, y0).predict(X0 @ P0)), 4)
assert need('rank_d') == 2, f'rank_d = {need("rank_d")}.'
assert tuple(need('shape_d')) == (len(X0), 2), f'shape_d = {need("shape_d")}.'
assert close(need('r2_full'), a) and close(need('r2_drop'), b), f'r2_full, r2_drop = {need("r2_full")}, {need("r2_drop")}, а нужно {a}, {b}.'
assert close(need('lost'), round(a - b, 4), 0.0002), f'lost = {need("lost")}.'
```

### hint
Ранг — `np.linalg.matrix_rank(Pd)`, форма — `(X @ Pd).shape`.

### hint
Две модели: `LinearRegression().fit(X, y)` и `LinearRegression().fit(X @ Pd, y)`, каждую оцените `r2_score` на её же признаках.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Pd = np.array([[1, 0], [0, 1], [0, 0]])

rank_d = int(np.linalg.matrix_rank(Pd))
Xd = X @ Pd
shape_d = Xd.shape
r2_full = round(r2_score(y, LinearRegression().fit(X, y).predict(X)), 4)
r2_drop = round(r2_score(y, LinearRegression().fit(Xd, y).predict(Xd)), 4)
lost = round(r2_full - r2_drop, 4)
```

### explain
R² упал с 0.5053 до 0.2817 — почти половина объяснённого разброса держалась на флаге пешего. Обратимое P линейная регрессия «не замечает», а необратимое — замечает сразу: выброшенную информацию никакие веса не вернут.

## task: same-quality | Регрессия не замечает | base

На доставках (признаки `distance_km`, `items`, `walk`; цель `actual_min`, время 1–299) возьмите `P = np.random.default_rng(7).normal(size=(3, 3))`. Обучите `LinearRegression` на `X` и на `X @ P`. Сохраните `r2_x`, `r2_p` (4 знака) и `max_pred_diff` — наибольшую разницу прогнозов двух моделей.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(7).normal(size=(3, 3))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import r2_score as _r2
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
P0 = _np.random.default_rng(7).normal(size=(3, 3))
a = _LR().fit(X0, y0).predict(X0); b = _LR().fit(X0 @ P0, y0).predict(X0 @ P0)
assert close(need('r2_x'), round(_r2(y0, a), 4)) and close(need('r2_p'), round(_r2(y0, b), 4)), f'r2_x, r2_p = {need("r2_x")}, {need("r2_p")}.'
assert need('max_pred_diff') < 1e-6, f'max_pred_diff = {need("max_pred_diff")} — прогнозы должны совпасть.'
```

### hint
`Xp = X @ P`; прогнозы каждой модели — на своих признаках.

### hint
`pred_x = LinearRegression().fit(X, y).predict(X)`, `pred_p = LinearRegression().fit(Xp, y).predict(Xp)`, `max_pred_diff = np.abs(pred_x - pred_p).max()`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(7).normal(size=(3, 3))

Xp = X @ P
pred_x = LinearRegression().fit(X, y).predict(X)
pred_p = LinearRegression().fit(Xp, y).predict(Xp)
r2_x = round(r2_score(y, pred_x), 4)
r2_p = round(r2_score(y, pred_p), 4)
max_pred_diff = np.abs(pred_x - pred_p).max()
```

### explain
R² совпадает до четвёртого знака, а прогнозы различаются на величину порядка 10⁻¹² — это ошибки округления, а не разница моделей. Линейная регрессия на X @ P может выразить ровно те же прогнозы, что и на X, поэтому находит то же лучшее решение.

## task: weights | Веса переводятся матрицей | plus

Для моделей из прошлой задачи проверьте формулу w' = P⁻¹ @ w. Сохраните `w` (веса модели на X), `w_p` (веса модели на X @ P), `w_formula = np.linalg.inv(P) @ w` и `match` — `True`, если `w_p` и `w_formula` совпадают (`np.allclose`). Совпадают ли свободные члены? Сохраните `same_intercept`.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(7).normal(size=(3, 3))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
P0 = _np.random.default_rng(7).normal(size=(3, 3))
m1 = _LR().fit(X0, y0); m2 = _LR().fit(X0 @ P0, y0)
assert _np.allclose(need('w'), m1.coef_) and _np.allclose(need('w_p'), m2.coef_, atol=1e-6), 'w и w_p — coef_ двух моделей.'
assert _np.allclose(need('w_formula'), _np.linalg.inv(P0) @ m1.coef_), 'w_formula = np.linalg.inv(P) @ w.'
assert need('match') == True, 'match должно быть True.'
assert need('same_intercept') == bool(_np.isclose(m1.intercept_, m2.intercept_)), f'same_intercept = {need("same_intercept")}.'
```

### hint
Обучите `m1` на `X` и `m2` на `X @ P`; веса — `coef_`, свободный член — `intercept_`.

### hint
`w_formula = np.linalg.inv(P) @ w`, `match = bool(np.allclose(w_p, w_formula, atol=1e-6))`, `same_intercept = bool(np.isclose(m1.intercept_, m2.intercept_))`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(7).normal(size=(3, 3))

m1 = LinearRegression().fit(X, y)
m2 = LinearRegression().fit(X @ P, y)
w, w_p = m1.coef_, m2.coef_
w_formula = np.linalg.inv(P) @ w
match = bool(np.allclose(w_p, w_formula, atol=1e-6))
same_intercept = bool(np.isclose(m1.intercept_, m2.intercept_))
```

### explain
Свободный член тот же: преобразование P перемешивает признаки, но не сдвигает их, а свободный член отвечает за сдвиг. Если бы мы ещё и прибавляли к признакам константу (как StandardScaler вычитает среднее), свободный член изменился бы, а прогнозы — всё равно нет.

## task: attack | Ключ по трём строкам | plus

Проверьте предупреждение из теории: «перемешивание» матрицей — не шифрование. Подрядчик получил `hidden = X @ P`, а P не знает. Но ему случайно достались исходные значения первых трёх строк `X[:3]`. Найдите `P_found` из системы `X[:3] @ P = hidden[:3]` через `np.linalg.solve`, восстановите всю таблицу `restored = hidden @ np.linalg.inv(P_found)` и сохраните `max_err` — наибольшее отклонение `restored` от `X`, и `leaked` — `True`, если `max_err < 1e-6`.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values.astype(float)
hidden = X @ np.random.default_rng(1).normal(size=(3, 3))   # P подрядчику неизвестна
known = X[:3]                                               # а эти три строки — известны

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values.astype(float)
P0 = _np.random.default_rng(1).normal(size=(3, 3))
assert _np.allclose(need('P_found'), P0), 'P_found не совпала с настоящей P. Решите solve(known, hidden[:3]).'
assert _np.allclose(need('restored'), X0), 'restored должна совпасть с X.'
assert need('max_err') < 1e-6, f'max_err = {need("max_err")}.'
assert need('leaked') == True, 'leaked должно быть True.'
```

### hint
Система `known @ P = hidden[:3]` — это `A @ x = b` сразу для трёх столбцов: `np.linalg.solve(known, hidden[:3])` вернёт всю матрицу 3 × 3.

### hint
`restored = hidden @ np.linalg.inv(P_found)`, `max_err = np.abs(restored - X).max()`.

### hint
Три строки сработают, только если они независимы: проверьте `np.linalg.matrix_rank(known)` — должно быть 3.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values.astype(float)
hidden = X @ np.random.default_rng(1).normal(size=(3, 3))
known = X[:3]

P_found = np.linalg.solve(known, hidden[:3])
restored = hidden @ np.linalg.inv(P_found)
max_err = np.abs(restored - X).max()
leaked = bool(max_err < 1e-6)
```

### explain
Трёх известных строк хватило, чтобы восстановить все 1841 доставку с точностью 10⁻¹⁴. У P 9 неизвестных, каждая известная строка даёт 3 уравнения — три независимые строки дают 9 уравнений и однозначный ответ. Поэтому такое преобразование годится, чтобы данные не «читались глазами», но не заменяет настоящую защиту: если утекло хотя бы n строк для n признаков, ключ найден.

## task: tree-vs-linear | Кто чувствителен к смешиванию | star

Соберите таблицу из раздела «А дерево замечает». Возьмите ту же `P`, что в теории (`default_rng(1)`; в двух прошлых задачах была другая, `default_rng(7)`), и три модели: `LinearRegression`, `DecisionTreeRegressor(max_depth=4, random_state=0)` и `KNeighborsRegressor(n_neighbors=15)`. Для каждой посчитайте R² на обучающих данных на X и на X @ P. Сохраните DataFrame `cmp` (индекс — `"linear"`, `"tree"`, `"knn"`, столбцы `x`, `xp`, 3 знака) и список `sensitive` — названия моделей, у которых R² изменился больше чем на 0.02 (порядок в списке не важен).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(1).normal(size=(3, 3))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.tree import DecisionTreeRegressor as _T
from sklearn.neighbors import KNeighborsRegressor as _K
from sklearn.metrics import r2_score as _r2
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
P0 = _np.random.default_rng(1).normal(size=(3, 3))
ms = {'linear': _LR(), 'tree': _T(max_depth=4, random_state=0), 'knn': _K(n_neighbors=15)}
c = need('cmp', _pd.DataFrame); sens = []
for k, m in ms.items():
    a = round(_r2(y0, m.fit(X0, y0).predict(X0)), 3); b = round(_r2(y0, m.fit(X0 @ P0, y0).predict(X0 @ P0)), 3)
    assert close(c.loc[k, 'x'], a, 0.002) and close(c.loc[k, 'xp'], b, 0.002), f'{k}: x, xp = {c.loc[k, "x"]}, {c.loc[k, "xp"]}, а нужно {a}, {b}.'
    if abs(a - b) > 0.02: sens.append(k)
assert sorted(str(v) for v in need('sensitive')) == sorted(sens), f'sensitive = {[str(v) for v in need("sensitive")]}, а нужно {sens} (порядок не важен).'
```

### hint
Словарь `{"linear": LinearRegression(), ...}` и цикл: для каждой модели два `fit` — на `X` и на `X @ P`.

### hint
Собирайте результаты в словарь `rows[name] = {"x": ..., "xp": ...}`, затем `pd.DataFrame(rows).T` — модели станут индексом.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import r2_score

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
P = np.random.default_rng(1).normal(size=(3, 3))

models = {"linear": LinearRegression(), "tree": DecisionTreeRegressor(max_depth=4, random_state=0),
          "knn": KNeighborsRegressor(n_neighbors=15)}
Xp = X @ P
rows = {}
for name, m in models.items():
    rows[name] = {"x": round(r2_score(y, m.fit(X, y).predict(X)), 3),
                  "xp": round(r2_score(y, m.fit(Xp, y).predict(Xp)), 3)}
cmp = pd.DataFrame(rows).T
sensitive = [k for k in cmp.index if abs(cmp.loc[k, "x"] - cmp.loc[k, "xp"]) > 0.02]
```

### explain
Числа те же, что в таблице теории: линейная регрессия 0.505 и 0.505, дерево 0.603 → 0.399, kNN 0.610 → 0.585. Линейная регрессия не изменилась, а дерево и kNN — изменились: у дерева другие вопросы, у kNN другие расстояния и, значит, другие соседи. С другой матрицей величина потерь другая: на `default_rng(7)` дерево теряет меньше (0.603 → 0.513), а kNN даже чуть растёт (0.610 → 0.622). Гарантии «качество то же» у этих моделей нет ни в какую сторону. Вывод для проекта: если данные передают подрядчику «перемешанными» матрицей, гарантировать то же качество можно только для линейных моделей.
