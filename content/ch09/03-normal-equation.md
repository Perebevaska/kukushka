---
title: Как обучается линейная регрессия
files: [deliveries.csv]
lead: "В главе 6 мы вызывали `LinearRegression().fit` и получали веса. Теперь посчитаем их сами одной формулой из матриц — и поймём, откуда берутся ошибки «матрица вырождена» и странные веса при дублирующихся признаках. Как упаковать расчёт в свою модель-класс — в следующем уроке."
recap:
  - "Обратная матрица A⁻¹: A⁻¹ @ A = I. Есть только у квадратных невырожденных матриц. `np.linalg.inv(A)`."
  - "Система линейных уравнений A @ x = b решается `np.linalg.solve(A, b)` — точнее и быстрее, чем `inv(A) @ b`."
  - "Линейная регрессия выбирает веса, при которых сумма квадратов ошибок минимальна. Решение: w = (XᵀX)⁻¹ Xᵀ y, где в X добавлен столбец единиц."
  - "Если один признак выражается через другие (метры и километры, все флаги get_dummies + свободный член), XᵀX вырождена: решений бесконечно много, веса теряют смысл."
  - "`np.linalg.matrix_rank(X)` меньше числа столбцов — признак вырожденности. Лечится удалением лишнего признака (`drop_first=True`) или регуляризацией."
---

## Обратная матрица

Для чисел деление — умножение на обратное: $x = \frac{b}{a} = a^{-1} \cdot b$. У квадратной матрицы $A$ тоже может быть **обратная** $A^{-1}$ — такая, что $A^{-1} A = I$ (единичная матрица). Тогда систему уравнений $Ax = b$ можно решить: $x = A^{-1} b$.

::: tip Аналогия
Матрица $A$ работает как касса: получает цены напитков и выдаёт суммы чеков. Обратная матрица — касса наоборот: по суммам чеков восстанавливает цены. Если же чеки повторяют друг друга (второй — тот же заказ, только удвоенный), «обратной кассы» быть не может: из одной суммы не понять, как она сложилась, — это и есть вырожденная матрица.
:::

Пример. В двух чеках без расшифровки: 2 капучино и 1 латте — 590 ₽, 1 капучино и 3 латте — 820 ₽. Сколько стоит каждый напиток?

```python
import numpy as np
A = np.array([[2, 1],
              [1, 3]])
b = np.array([590, 820])
print(np.linalg.inv(A))          # обратная матрица
print(np.linalg.inv(A) @ b)      # решение через обратную
print(np.linalg.solve(A, b))     # то же, но надёжнее
```

**Что здесь происходит:**

- `A` — матрица системы: строка — чек, столбец — напиток (капучино, латте). `b` — суммы чеков.
- `np.linalg.inv(A)` — обратная матрица. Для 2 × 2 её можно найти руками. Понадобится **определитель** — число, на которое делят при обращении матрицы. Для матрицы 2 × 2 с элементами $\begin{pmatrix} a & b \\ c & d \end{pmatrix}$ он равен $ad - bc$, в numpy — `np.linalg.det(A)`. Если определитель 0, делить не на что и обратной нет. У нашей матрицы определитель 2 · 3 − 1 · 1 = **5**, переставляем диагональ, меняем знак у остальных и делим на 5: $A^{-1} = \frac{1}{5} \begin{pmatrix} 3 & -1 \\ -1 & 2 \end{pmatrix} = \begin{pmatrix} 0.6 & -0.2 \\ -0.2 & 0.4 \end{pmatrix}$.
- `inv(A) @ b` — капучино: 0.6 · 590 − 0.2 · 820 = 354 − 164 = **190**; латте: −0.2 · 590 + 0.4 · 820 = −118 + 328 = **210**.
- `np.linalg.solve(A, b)` — тот же ответ без явной обратной.

Проверка подстановкой: 2 · 190 + 210 = 590 и 190 + 3 · 210 = 820. Сходится.

Капучино 190 ₽, латте 210 ₽. `np.linalg.solve` решает систему, не вычисляя обратную матрицу явно, — это быстрее и меньше страдает от ошибок округления. В коде пользуйтесь им.

Обратная есть не у всех матриц. Если одно уравнение повторяет другое («2 капучино и 1 латте — 590», «4 капучино и 2 латте — 1180»), информации на два неизвестных не хватает: матрица **вырождена**. Руками это видно по определителю: 2 · 2 − 1 · 4 = 0, а обратная получается делением на определитель — делить на ноль нельзя.

Второй признак вырожденности — **ранг**: сколько в матрице по-настоящему независимых строк (столбцов независимых ровно столько же). У чека-дубля вторая строка — первая, умноженная на 2, новой информации в ней нет, и ранг 1. Считает его `np.linalg.matrix_rank(A)`. Если ранг меньше числа неизвестных, единственного решения нет. В обычном Python `inv` и `solve` на такой матрице падают с ошибкой `LinAlgError`, а сборка numpy в браузере может молча вернуть `nan`. Поэтому надёжнее проверить ранг или определитель **до** решения.

::: predict
```python static
import numpy as np
A = np.array([[2, 1], [4, 2]])
b = np.array([590, 1180])
print(np.linalg.matrix_rank(A) == A.shape[1])
```

- `True`
- [x] `False`
- ошибка

Почему: второй чек — первый, умноженный на 2, ранг 1 при двух неизвестных. Системе подходят и (190, 210), и (200, 190), и (295, 0) — бесконечно много пар цен. Такую проверку стоит делать перед `solve`.
:::

{{practice: solve2, inverse}}

## Откуда берутся веса регрессии

Линейная регрессия ищет веса $w$, при которых прогнозы $Xw$ ближе всего к ответам $y$ — точнее, при которых **сумма квадратов ошибок** минимальна. Интуиция такая: веса подобраны лучше некуда, когда в ошибках не осталось линейного следа ни одного признака — ошибки не растут вместе с расстоянием, не растут вместе с числом позиций и в среднем равны нулю. Записанное матрицами, это условие и есть система $X^\top X w = X^\top y$; ниже проверим его руками на игрушке. Решение системы называют **нормальным уравнением**:

$$
w = (X^\top X)^{-1} X^\top y
$$

Свободный член прячется в первый столбец единиц (трюк из урока «Матрицы»).

### Сначала на игрушке

Четыре заказа: расстояние $x = 1, 2, 3, 4$ км, время $y = 3, 4, 8, 9$ минут. Ищем $y \approx w_0 + w_1 \cdot x$.

X1 — столбец единиц и столбец $x$:

| 1 | x |
|---|---|
| 1 | 1 |
| 1 | 2 |
| 1 | 3 |
| 1 | 4 |

Считаем две маленькие матрицы руками:

- $X^\top X = \begin{pmatrix} 1+1+1+1 & 1+2+3+4 \\ 1+2+3+4 & 1+4+9+16 \end{pmatrix} = \begin{pmatrix} \mathbf{4} & \mathbf{10} \\ \mathbf{10} & \mathbf{30} \end{pmatrix}$ — число строк, сумма $x$, сумма $x^2$.
- $X^\top y = [3+4+8+9,\ 1 \cdot 3 + 2 \cdot 4 + 3 \cdot 8 + 4 \cdot 9] = [\mathbf{24},\ \mathbf{71}]$ — сумма $y$ и сумма $x \cdot y$.

Остаётся система из двух уравнений: $4w_0 + 10w_1 = 24$ и $10w_0 + 30w_1 = 71$. Из первого, умноженного на 2.5: $10w_0 + 25w_1 = 60$; вычитаем: $5w_1 = 11$, $\mathbf{w_1 = 2.2}$, тогда $w_0 = \frac{24 - 22}{4} = \mathbf{0.5}$.

```python
import numpy as np
x = np.array([1, 2, 3, 4.])
y = np.array([3, 4, 8, 9.])
X1 = np.column_stack([np.ones(4), x])
print(X1.T @ X1)
print(X1.T @ y)
print(np.linalg.solve(X1.T @ X1, X1.T @ y))
```

Прямая $0.5 + 2.2x$: прогнозы 2.7, 4.9, 7.1, 9.3. Ни одна точка на неё не легла — но любая другая прямая даст сумму квадратов ошибок больше, чем 0.3² + 0.9² + 0.9² + 0.3² = 1.8.

::: figure ols-toy
Четыре заказа и прямая из нормального уравнения. Красные отрезки — ошибки: их квадраты в сумме дают 1.8, меньше нельзя. Справа — свойство, которое разберём ниже: сумма ошибок и сумма «x × ошибка» равны нулю.
:::

::: predict
```python static
import numpy as np
X1 = np.column_stack([np.ones(5), [2, 4, 1, 3, 5]])
print((X1.T @ X1)[0, 0])
```

- [x] `5.0`
- `15.0`
- `1.0`

Почему: левый верхний элемент XᵀX — скалярное произведение столбца единиц на себя, то есть число строк. Сумма x (15) стоит рядом, в позиции [0, 1].
:::

### Теперь на доставках

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values

X1 = np.column_stack([np.ones(len(X)), X])          # столбец единиц + признаки
w = np.linalg.solve(X1.T @ X1, X1.T @ y)            # (XᵀX) w = Xᵀy
print("руками:  ", w.round(3))

model = LinearRegression().fit(X, y)
print("sklearn: ", np.r_[model.intercept_, model.coef_].round(3))
```

**Что здесь происходит:**

- `ok` — доставки без явных ошибок во времени (1841 строка); `walk` — флаг пешего курьера.
- `X1` — 1841 × 4: единицы, расстояние, позиции, флаг. `X1.T @ X1` — всего 4 × 4, `X1.T @ y` — 4 числа: сколько бы ни было строк, решаем систему из четырёх уравнений.
- `np.linalg.solve(...)` — веса в порядке столбцов: свободный член, км, позиции, пеший.
- `np.r_[model.intercept_, model.coef_]` — склеиваем веса sklearn в тот же порядок, чтобы сравнить.

::: figure xtx-shrink
Почему система маленькая: X1ᵀ @ X1 складывает вклад всех 1841 строки в таблицу 4 × 4, а X1ᵀ @ y — в 4 числа. Справа — что лежит в этих клетках на игрушке из четырёх заказов.
:::

Веса совпадают: 16 минут базово, 3.9 минуты на километр, 1.6 на позицию и 13.6 надбавка пешему курьеру. Внутри `LinearRegression` нет ничего, кроме этой линейной алгебры (sklearn решает её чуть другим, более устойчивым способом, но ответ тот же).

::: deep Откуда формула
Сумма квадратов ошибок — это $|y - Xw|^2$. Её минимум там, где производная по $w$ равна нулю: $-2X^\top (y - Xw) = 0$, то есть $X^\top X w = X^\top y$. Геометрически: прогноз $Xw$ — проекция вектора ответов $y$ на «пространство», натянутое на столбцы $X$, а ошибка $y - Xw$ перпендикулярна каждому столбцу.
:::

::: quiz
Доставок 1841, а `np.linalg.solve` решает систему всего из четырёх уравнений. Почему так можно?

- [x] `X1.T @ X1` и `X1.T @ y` уже сложили вклад всех строк: уравнений столько, сколько весов, а каждое собирает суммы по всем доставкам
  > Размер системы задаёт число столбцов (свободный член и три признака), а не число строк. Строки «спрятаны» в суммах вроде «сумма x» и «сумма x²».
- [ ] Берутся четыре случайные доставки, по одной на каждый вес
  > Четырёх точек хватило бы, чтобы провести через них модель, но тогда веса зависели бы от случайного выбора. Нормальное уравнение использует все строки.
- [ ] Остальные доставки отбрасываются как выбросы
  > Выбросы мы отсеяли заранее фильтром по времени. В суммах участвуют все оставшиеся строки — 1841.
- [ ] Система из 1841 уравнения решается так же, просто numpy это скрывает
  > Система «прогноз = ответ» для каждой строки не имеет точного решения: никакие веса не дают ровно нулевую ошибку на всех доставках сразу. Нормальное уравнение заменяет её на систему 4 × 4, у которой решение есть.
:::

{{practice: p-normal, my-ols, no-ones, gd-preview}}

## Разберём вместе: что значит «ошибка перпендикулярна»

Вернёмся к игрушке. Ошибки прогноза $y - X_1 w$: 3 − 2.7, 4 − 4.9, 8 − 7.1, 9 − 9.3 = **0.3, −0.9, 0.9, −0.3**.

Умножим этот вектор на каждый столбец X1:

- на столбец единиц: 0.3 − 0.9 + 0.9 − 0.3 = **0** — сумма ошибок равна нулю, модель в среднем не ошибается ни вверх, ни вниз;
- на столбец x: 1 · 0.3 + 2 · (−0.9) + 3 · 0.9 + 4 · (−0.3) = 0.3 − 1.8 + 2.7 − 1.2 = **0** — в ошибках не осталось ничего, что объяснялось бы расстоянием.

Это и есть условие $X^\top X w = X^\top y$, переписанное как $X^\top (y - Xw) = 0$. Практический смысл: если бы в ошибках остался линейный след признака, вес можно было бы сдвинуть и уменьшить ошибку. Нулевые произведения означают, что сдвигать больше нечего.

```python
import numpy as np
x = np.array([1, 2, 3, 4.]); y = np.array([3, 4, 8, 9.])
X1 = np.column_stack([np.ones(4), x])
w = np.linalg.solve(X1.T @ X1, X1.T @ y)
resid = y - X1 @ w
print(resid.round(2), (X1.T @ resid).round(10))
```

Что получилось: ноль с точностью до $10^{-15}$. На доставках то же самое — средняя ошибка линейной регрессии со свободным членом всегда 0, проверите в задачах.

{{practice: orthogonal}}

## Ловушка: признаки, которые повторяют друг друга

Нормальное уравнение требует, чтобы матрица $X^\top X$ была обратимой. Это ломается, когда один признак точно выражается через другие. Классический пример — **все** флаги `get_dummies` вместе со столбцом единиц: «авто + вело + пеший = 1» в каждой строке, то есть сумма флагов повторяет столбец единиц.

```python
import numpy as np
import pandas as pd

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
flags = pd.get_dummies(ok["courier"], dtype=int)            # все три флага
X2 = np.column_stack([np.ones(len(ok)), ok["distance_km"], flags])
print("столбцов:", X2.shape[1], "| ранг:", np.linalg.matrix_rank(X2))
```

Ранг (число по-настоящему независимых столбцов) — 4 при 5 столбцах.

::: predict
```python static
import numpy as np
A = np.array([[1, 2], [2, 4]])
print(np.linalg.matrix_rank(A))
```

- `2`
- [x] `1`
- `0`

Почему: второй столбец — первый, умноженный на 2: один и тот же признак в разных единицах. Независимый столбец один, ранг 1 при двух столбцах — матрица вырождена, как `X2` с флагами.
:::

Вернёмся к `X2`. Решений бесконечно много: можно прибавить 10 к свободному члену и вычесть 10 из каждого флага — прогнозы не изменятся. Из-за ошибок округления `inv` при этом может и не упасть, а молча вернуть бессмысленные огромные веса — это опаснее ошибки.

::: figure dummy-trap
Флаги трёх курьеров в каждой строке складываются в 1 — ровно столбец единиц. Поэтому веса можно сдвигать: +10 к свободному члену и −10 к каждому флагу дают те же прогнозы. Исходные веса — у модели «км + флаги вело и пеший» на доставках.
:::

Отсюда правило главы 6: для линейных моделей `drop_first=True`. Тогда один флаг уходит, ранг равен числу столбцов, и веса однозначны.

::: warn
Почти-повторы тоже вредят. Расстояние в км и в метрах — точная копия (ранг упадёт). А «расстояние» и «время в пути по навигатору» — почти копия: матрица формально обратима, но веса становятся неустойчивыми и могут менять знак от небольшой правки данных. Это называют **мультиколлинеарностью**. Помогает убрать один из признаков или регуляризация (Ridge, глава 7).
:::

::: warn Типичные ошибки
- **Забыли столбец единиц.** Модель вынуждена проходить через ноль: на доставках без свободного члена MAE растёт с 5.87 до 7.56 минуты, а «базовые 16 минут» расползаются по другим весам.
- **`inv(XᵀX) @ Xᵀy` вместо `solve`.** Работает на учебных данных, но на почти вырожденных матрицах теряет точность первым.
- **Сравнение через `==`.** 0.30000000000000004 ≠ 0.3 — для чисел с плавающей точкой `np.allclose`.
- **Перепутан порядок.** Веса идут в порядке столбцов X1. Если собрали X1 как [единицы, items, distance_km], то `w[1]` — уже про позиции, а не про километры.
:::

::: quiz
В модель взяли флаги всех трёх курьеров (авто, вело, пеший) и столбец единиц. Что пойдёт не так?

- [x] Флаги в сумме всегда дают 1 — ровно столбец единиц, матрица вырождена, и единственных весов нет
  > Признаки линейно зависимы: веса можно сдвигать между флагами и свободным членом без изменения прогноза. Поэтому один флаг выбрасывают (`drop_first`).
- [ ] Ничего: больше признаков — точнее модель
  > Новый столбец не добавляет информации — он уже выражен через остальные.
- [ ] Модель не обучится на текстовых данных
  > Флаги — числа, дело не в типе.
- [ ] Прогнозы станут случайными
  > Прогнозы могут остаться нормальными, а вот веса — нет.
:::

{{practice: dup-receipt, rank, many-solutions}}

## Практика

## task: solve2 | Цены из чеков | warmup

Два чека: 3 эспрессо и 2 капучино — 740 ₽; 1 эспрессо и 4 капучино — 880 ₽. Сохраните матрицу системы `A`, вектор `b` и решение `prices = np.linalg.solve(A, b)` (цена эспрессо, цена капучино).

### starter
```python
import numpy as np

```

### check
```python
import numpy as _np
assert _np.allclose(need('A'), [[3, 2], [1, 4]]), f'A = {need("A")}. Строка — чек, столбцы — эспрессо и капучино.'
assert _np.allclose(need('b'), [740, 880]), f'b = {need("b")}.'
assert _np.allclose(need('prices'), [120, 190]), f'prices = {need("prices")}.'
```

### hint
Строка матрицы — один чек, столбец — один напиток: в первом чеке 3 эспрессо и 2 капучино, значит первая строка `[3, 2]`.

### hint
`A = np.array([[3, 2], [1, 4]])`, `b = np.array([740, 880])`.

### hint
Проверьте ответ подстановкой: `A @ prices` должно дать `[740, 880]`.

### solution
```python
import numpy as np
A = np.array([[3, 2], [1, 4]])
b = np.array([740, 880])
prices = np.linalg.solve(A, b)
```

## task: dup-receipt | Чек-дубль | warmup

Второй чек повторяет первый в двойном размере: 2 капучино и 1 латте — 590 ₽; 4 капучино и 2 латте — 1180 ₽. Сохраните ранг матрицы `rank`, модуль определителя `det_abs` (округлите до 6 знаков) и флаг `solvable` — `True`, если ранг равен числу неизвестных. Затем исправьте второй чек на «1 капучино и 3 латте — 820 ₽», сохраните исправленную матрицу `A2`, её ранг `rank2` и решение `prices2`.

### starter
```python
import numpy as np
A = np.array([[2, 1], [4, 2]])
b = np.array([590, 1180])

```

### check
```python
import numpy as _np
assert need('rank') == 1, f'rank = {need("rank")}. Вторая строка — первая × 2.'
assert abs(need('det_abs')) < 1e-6, f'det_abs = {need("det_abs")} — у вырожденной матрицы определитель 0.'
assert need('solvable') == False, 'solvable должно быть False: ранг 1 при двух неизвестных.'
assert _np.allclose(need('A2'), [[2, 1], [1, 3]]), f'A2 = {need("A2")}.'
assert need('rank2') == 2, f'rank2 = {need("rank2")}.'
assert _np.allclose(need('prices2'), [190, 210]), f'prices2 = {need("prices2")}. Не забудьте исправить и b.'
```

### hint
`rank = np.linalg.matrix_rank(A)`, `det_abs = round(abs(np.linalg.det(A)), 6)`, `solvable = bool(rank == A.shape[1])`.

### hint
Исправляется и матрица, и вектор сумм: `A2 = np.array([[2, 1], [1, 3]])`, `b2 = np.array([590, 820])`.

### solution
```python
import numpy as np
A = np.array([[2, 1], [4, 2]])
b = np.array([590, 1180])
rank = np.linalg.matrix_rank(A)
det_abs = round(abs(np.linalg.det(A)), 6)
solvable = bool(rank == A.shape[1])

A2 = np.array([[2, 1], [1, 3]])
b2 = np.array([590, 820])
rank2 = np.linalg.matrix_rank(A2)
prices2 = np.linalg.solve(A2, b2)
```

## task: inverse | Обратная матрица | warmup

Для матрицы `A` сохраните обратную `A_inv` и проверку `check = A_inv @ A`. В `is_identity` сохраните `True`, если `check` совпадает с `np.eye(3)` с учётом округления (`np.allclose`).

### starter
```python
import numpy as np
A = np.array([[2, 0, 1],
              [1, 3, 0],
              [0, 1, 4]])

```

### check
```python
import numpy as _np
A0 = _np.array([[2, 0, 1], [1, 3, 0], [0, 1, 4]])
assert _np.allclose(need('A_inv'), _np.linalg.inv(A0)), 'A_inv — np.linalg.inv(A).'
assert _np.allclose(need('check'), _np.eye(3)), 'check — A_inv @ A, должна получиться единичная матрица.'
assert need('is_identity') == True, 'is_identity должно быть True — используйте np.allclose(check, np.eye(3)).'
```

### hint
`A_inv = np.linalg.inv(A)`, `check = A_inv @ A`.

### hint
Прямое сравнение `==` может подвести из-за округлений вроде 0.9999999999. Для чисел с плавающей точкой — `np.allclose`.

### solution
```python
import numpy as np
A = np.array([[2, 0, 1],
              [1, 3, 0],
              [0, 1, 4]])
A_inv = np.linalg.inv(A)
check = A_inv @ A
is_identity = np.allclose(check, np.eye(3))
```

## task: p-normal | Нормальное уравнение | warmup

Соберите код, который считает веса линейной регрессии по нормальному уравнению для маленькой таблицы.

### parsons
```python
import numpy as np
X = np.array([[1.0], [2.0], [3.0], [4.0]])
y = np.array([3.0, 5.0, 7.0, 9.0])
X1 = np.column_stack([np.ones(len(X)), X])
w = np.linalg.solve(X1.T @ X1, X1.T @ y)
print(w.round(2).tolist())
```

### check
```python
assert _lines == ['[1.0, 2.0]'], f'Сейчас: {_lines}. y = 1 + 2x — веса должны быть [1, 2].'
```

### hint
Сначала данные, потом столбец единиц, потом решение системы.

### hint
`X1` нужен до `solve`, а `solve` — до `print`. Импорт — самая первая строка.

## task: my-ols | Веса руками | base

На доставках (время 1–299 минут) посчитайте веса линейной регрессии нормальным уравнением для признаков `distance_km`, `items` и флага `auto` (`courier == "авто"`). Сохраните вектор `w` (свободный член первым) и прогнозы `pred = X1 @ w`. В `mae` сохраните среднюю абсолютную ошибку прогнозов на тех же данных (2 знака).

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["auto"] = (ok["courier"] == "авто").astype(int)
y = ok["actual_min"].values

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['auto'] = (ok['courier'] == 'авто').astype(int)
X0 = ok[['distance_km', 'items', 'auto']]; m = _LR().fit(X0, ok['actual_min'])
ww = _np.r_[m.intercept_, m.coef_]
assert _np.allclose(need('w'), ww, atol=1e-6), f'w = {_np.round(need("w"), 3)}, а нужно {ww.round(3)}. Свободный член первым, затем distance_km, items, auto.'
pr = m.predict(X0)
assert _np.allclose(need('pred'), pr), 'pred не совпадает с прогнозами модели.'
assert close(need('mae'), round(_np.abs(pr - ok['actual_min'].values).mean(), 2)), f'mae = {need("mae")}.'
```

### hint
`X1 = np.column_stack([np.ones(len(ok)), ok[["distance_km", "items", "auto"]].values])`, затем `np.linalg.solve(X1.T @ X1, X1.T @ y)`.

### hint
`pred = X1 @ w`, `mae = round(np.abs(pred - y).mean(), 2)`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["auto"] = (ok["courier"] == "авто").astype(int)
y = ok["actual_min"].values

X1 = np.column_stack([np.ones(len(ok)), ok[["distance_km", "items", "auto"]].values])
w = np.linalg.solve(X1.T @ X1, X1.T @ y)
pred = X1 @ w
mae = round(np.abs(pred - y).mean(), 2)
```

### explain
Флаг «авто» получил отрицательный вес: при том же расстоянии машина быстрее. Но модель всё равно хуже, чем с флагом «пеший» из теории, — пешие доставки отличаются от остальных сильнее, чем машины.

## task: no-ones | Без свободного члена | base

Посчитайте нормальным уравнением две модели на доставках с признаками `distance_km`, `items`, `walk`: `w_no` — **без** столбца единиц (3 веса), `w_with` — со столбцом единиц (4 веса, свободный член первым). Сохраните `mae_no` и `mae_with` (2 знака) и `bias_no` — среднюю ошибку `y − pred` модели без единиц (2 знака).

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
y = ok["actual_min"].values
X = ok[["distance_km", "items", "walk"]].values.astype(float)

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int); y = ok['actual_min'].values
X = ok[['distance_km', 'items', 'walk']].values.astype(float); X1 = _np.column_stack([_np.ones(len(X)), X])
wn = _np.linalg.solve(X.T @ X, X.T @ y); ww = _np.linalg.solve(X1.T @ X1, X1.T @ y)
assert _np.allclose(need('w_no'), wn), f'w_no = {_np.round(need("w_no"), 3)}, а нужно {wn.round(3)}. Без столбца единиц: solve(X.T @ X, X.T @ y).'
assert _np.allclose(need('w_with'), ww), f'w_with = {_np.round(need("w_with"), 3)}, а нужно {ww.round(3)}.'
assert close(need('mae_no'), round(_np.abs(y - X @ wn).mean(), 2)), f'mae_no = {need("mae_no")}.'
assert close(need('mae_with'), round(_np.abs(y - X1 @ ww).mean(), 2)), f'mae_with = {need("mae_with")}.'
assert close(need('bias_no'), round((y - X @ wn).mean(), 2)), f'bias_no = {need("bias_no")}. Среднее y − pred, без модуля.'
```

### hint
Без единиц: `np.linalg.solve(X.T @ X, X.T @ y)`. С единицами — сначала `X1 = np.column_stack([np.ones(len(X)), X])`.

### hint
Прогнозы — `X @ w_no` и `X1 @ w_with`. Для `bias_no` модуль не берите: нужна средняя ошибка со знаком.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
y = ok["actual_min"].values
X = ok[["distance_km", "items", "walk"]].values.astype(float)

w_no = np.linalg.solve(X.T @ X, X.T @ y)
X1 = np.column_stack([np.ones(len(X)), X])
w_with = np.linalg.solve(X1.T @ X1, X1.T @ y)
mae_no = round(np.abs(y - X @ w_no).mean(), 2)
mae_with = round(np.abs(y - X1 @ w_with).mean(), 2)
bias_no = round((y - X @ w_no).mean(), 2)
```

### explain
Без свободного члена MAE 7.56 вместо 5.87, а средняя ошибка 2.1 — модель систематически занижает время. Базовые 16 минут, которые нужны любой доставке, ей некуда положить, и она «размазывает» их по другим весам: километр стоит уже 4.0 минуты вместо 3.9, а надбавка пешему — 19.9 вместо 13.6. Веса стали больше и при этом хуже описывают реальность.

## task: rank | Ловушка флагов | base

Соберите две матрицы признаков для доставок: `full` — столбец единиц + `distance_km` + **все** флаги `get_dummies(ok["courier"])`, и `fixed` — то же, но флаги с `drop_first=True`. Сохраните ранги `rank_full`, `rank_fixed` и числа столбцов `cols_full`, `cols_fixed`. В `ok_fixed` — `True`, если у `fixed` ранг равен числу столбцов.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import numpy as _np, pandas as _pd
assert need('cols_full') == 5 and need('rank_full') == 4, f'full: {need("cols_full")} столбцов, ранг {need("rank_full")}. Ожидалось 5 и 4.'
assert need('cols_fixed') == 4 and need('rank_fixed') == 4, f'fixed: {need("cols_fixed")} столбцов, ранг {need("rank_fixed")}. Ожидалось 4 и 4.'
assert need('ok_fixed') == True, 'ok_fixed должно быть True.'
```

### hint
Число столбцов `full` — 1 (единицы) + 1 (расстояние) + 3 (флаги) = 5; у `fixed` флагов на один меньше.

### hint
`np.column_stack([np.ones(len(ok)), ok["distance_km"], pd.get_dummies(ok["courier"], dtype=int)])`. Ранг — `np.linalg.matrix_rank`, число столбцов — `.shape[1]`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

ones = np.ones(len(ok))
full = np.column_stack([ones, ok["distance_km"], pd.get_dummies(ok["courier"], dtype=int)])
fixed = np.column_stack([ones, ok["distance_km"], pd.get_dummies(ok["courier"], drop_first=True, dtype=int)])
rank_full, cols_full = np.linalg.matrix_rank(full), full.shape[1]
rank_fixed, cols_fixed = np.linalg.matrix_rank(fixed), fixed.shape[1]
ok_fixed = bool(rank_fixed == cols_fixed)
```

### explain
У `full` 5 столбцов, но ранг 4: сумма трёх флагов в каждой строке равна 1 и повторяет столбец единиц. Один флаг лишний — `drop_first=True` убирает его, и ранг сравнивается с числом столбцов. Удалённый флаг не пропал: его категория стала «базовой», и её эффект сидит в свободном члене.

## task: orthogonal | Ошибки перпендикулярны | plus

Проверьте свойство из «Разберём вместе» на доставках. Посчитайте веса нормальным уравнением для `distance_km`, `items`, `walk` (со столбцом единиц), ошибки `resid = y − X1 @ w` и вектор `dots = X1.T @ resid`. Сохраните `max_dot` — наибольший модуль в `dots`, `resid_mean` — среднюю ошибку и `is_orth` — `True`, если `max_dot < 1e-6`. Затем испортите веса: `w_bad` — копия `w` с весом расстояния больше на 0.5, и сохраните `sse_ratio` — во сколько раз сумма квадратов ошибок `w_bad` больше, чем у `w` (3 знака).

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
y = ok["actual_min"].values
X1 = np.column_stack([np.ones(len(ok)), ok[["distance_km", "items", "walk"]].values])

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int); y = ok['actual_min'].values
X1 = _np.column_stack([_np.ones(len(ok)), ok[['distance_km', 'items', 'walk']].values])
w = _np.linalg.solve(X1.T @ X1, X1.T @ y); wb = w.copy(); wb[1] += 0.5
assert _np.asarray(need('dots')).shape == (4,), 'dots — вектор из 4 чисел: X1.T @ resid.'
assert need('max_dot') < 1e-6, f'max_dot = {need("max_dot")} — должно быть почти 0.'
assert abs(need('resid_mean')) < 1e-6, f'resid_mean = {need("resid_mean")} — средняя ошибка должна быть 0.'
assert need('is_orth') == True, 'is_orth должно быть True.'
r = ((y - X1 @ wb) ** 2).sum() / ((y - X1 @ w) ** 2).sum()
assert close(need('sse_ratio'), round(r, 3), 0.0011), f'sse_ratio = {need("sse_ratio")}, а нужно {round(r, 3)}.'
```

### hint
`resid = y - X1 @ w`, `dots = X1.T @ resid`, `max_dot = np.abs(dots).max()`.

### hint
Вес расстояния — `w_bad[1]` (нулевой — свободный член). Сумма квадратов ошибок — `((y - X1 @ w) ** 2).sum()`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
y = ok["actual_min"].values
X1 = np.column_stack([np.ones(len(ok)), ok[["distance_km", "items", "walk"]].values])

w = np.linalg.solve(X1.T @ X1, X1.T @ y)
resid = y - X1 @ w
dots = X1.T @ resid
max_dot = np.abs(dots).max()
resid_mean = resid.mean()
is_orth = bool(max_dot < 1e-6)

w_bad = w.copy()
w_bad[1] += 0.5
sse_ratio = round(((y - X1 @ w_bad) ** 2).sum() / ((y - X1 @ w) ** 2).sum(), 3)
```

### explain
Все четыре произведения — ноль с точностью до округления, средняя ошибка тоже ноль: в ошибках не осталось линейного следа ни одного признака. Стоит сдвинуть вес километра всего на 0.5 минуты — и сумма квадратов ошибок растёт на 5% (в 1.052 раза), а средняя ошибка становится −1.48: средняя доставка 3 км, и модель начинает завышать каждую примерно на полторы минуты. Нормальное уравнение находит ровно ту точку, где любой сдвиг хуже.

## task: many-solutions | Бесконечно много решений | plus

Покажите, что при всех трёх флагах веса неоднозначны. Возьмите `full` из прошлой задачи и любое решение `w_a = np.linalg.lstsq(full, y, rcond=None)[0]` (`lstsq` находит решение и для вырожденных систем). Постройте другое решение `w_b`: прибавьте 10 к свободному члену и вычтите 10 из каждого из трёх весов флагов. Сохраните `max_diff` — наибольшую разницу прогнозов `full @ w_a` и `full @ w_b`, и `weights_differ` — наибольшую разницу самих весов.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"].values
full = np.column_stack([np.ones(len(ok)), ok["distance_km"], pd.get_dummies(ok["courier"], dtype=int)])

```

### check
```python
import numpy as _np
wa = _np.asarray(need('w_a')); wb = _np.asarray(need('w_b'))
assert wa.shape == (5,) and wb.shape == (5,), 'w_a и w_b — векторы из 5 весов.'
assert close(wb[0] - wa[0], 10) and _np.allclose(wb[2:] - wa[2:], -10) and close(wb[1], wa[1]), 'w_b: +10 к первому весу, −10 к трём последним, вес расстояния без изменений.'
assert need('max_diff') < 1e-6, f'max_diff = {need("max_diff")} — прогнозы должны совпасть.'
assert close(need('weights_differ'), 10), f'weights_differ = {need("weights_differ")}.'
```

### hint
Порядок весов: свободный член, расстояние, три флага. Сдвигать нужно `w[0]` и `w[2:]`, вес расстояния `w[1]` не трогаем.

### hint
`w_b = w_a.copy()`, `w_b[0] += 10`, `w_b[2:] -= 10`. Без `.copy()` вы измените и `w_a`.

### hint
`max_diff = np.abs(full @ w_a - full @ w_b).max()`, `weights_differ = np.abs(w_a - w_b).max()`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"].values
full = np.column_stack([np.ones(len(ok)), ok["distance_km"], pd.get_dummies(ok["courier"], dtype=int)])

w_a = np.linalg.lstsq(full, y, rcond=None)[0]
w_b = w_a.copy()
w_b[0] += 10
w_b[2:] -= 10
max_diff = np.abs(full @ w_a - full @ w_b).max()
weights_differ = np.abs(w_a - w_b).max()
```

### explain
Два разных набора весов дают одинаковые прогнозы — значит, данные не могут выбрать между ними. Прогнозы такой модели в порядке, а вот веса читать нельзя: «надбавка пешему» может быть и 15, и 5, и −100 минут в зависимости от того, какое решение выдал алгоритм.

## task: gd-preview | Сколько стоит сантиметр | star

Добавьте к признакам `distance_km`, `items`, `walk` почти-копию расстояния: `noisy = distance_km * 1000 + шум`, шум — `np.random.default_rng(0).normal(0, 50, len(ok))` (ошибка навигатора ±50 м). Посчитайте нормальным уравнением веса без `noisy` (`w_base`) и с ним (`w_noisy`; свободный член первым, `noisy` последним). Сохраните `km_base` — вес `distance_km` в первой модели, `km_noisy` — во второй, и `km_total` — суммарный эффект километра во второй модели: вес `distance_km` + 1000 × вес `noisy` (все — 2 знака).

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
y = ok["actual_min"].values
noise = np.random.default_rng(0).normal(0, 50, len(ok))
ok["noisy"] = ok["distance_km"] * 1000 + noise

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int); y = ok['actual_min'].values
ok['noisy'] = ok['distance_km'] * 1000 + _np.random.default_rng(0).normal(0, 50, len(ok))
def _ols(cols):
    X1 = _np.column_stack([_np.ones(len(ok)), ok[cols].values]); return _np.linalg.solve(X1.T @ X1, X1.T @ y)
wb = _ols(['distance_km', 'items', 'walk']); wn = _ols(['distance_km', 'items', 'walk', 'noisy'])
assert close(need('km_base'), round(wb[1], 2), 0.011), f'km_base = {need("km_base")}, а нужно {round(wb[1], 2)}.'
assert close(need('km_noisy'), round(wn[1], 2), 0.011), f'km_noisy = {need("km_noisy")}, а нужно {round(wn[1], 2)}.'
assert close(need('km_total'), round(wn[1] + 1000 * wn[4], 2), 0.011), f'km_total = {need("km_total")}, а нужно {round(wn[1] + 1000 * wn[4], 2)}.'
```

### hint
Напишите функцию `ols(cols)`, которая собирает `X1` со столбцом единиц и решает систему.

### hint
`noisy` — пятый столбец X1 (после единиц, км, позиций, флага), то есть `w_noisy[4]`. Километр в метрах — 1000 единиц `noisy`, отсюда множитель 1000.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
y = ok["actual_min"].values
noise = np.random.default_rng(0).normal(0, 50, len(ok))
ok["noisy"] = ok["distance_km"] * 1000 + noise

def ols(cols):
    X1 = np.column_stack([np.ones(len(ok)), ok[cols].values])
    return np.linalg.solve(X1.T @ X1, X1.T @ y)

w_base = ols(["distance_km", "items", "walk"])
w_noisy = ols(["distance_km", "items", "walk", "noisy"])
km_base = round(w_base[1], 2)
km_noisy = round(w_noisy[1], 2)
km_total = round(w_noisy[1] + 1000 * w_noisy[4], 2)
```

### explain
Вес километра «переехал» между двумя почти одинаковыми признаками: по отдельности их веса заметно отличаются от честных 3.9 минуты, а суммарный эффект остался почти прежним. Прогнозам это не мешает, а вот читать веса как «минуты на километр» уже нельзя — в этом и беда мультиколлинеарности.

Название задачи — задел на главу 10. Там те же веса будем искать не формулой, а градиентным спуском: шагами «под горку», без решения системы с $X^\top X$. Спуск — другой способ найти веса, а не лекарство от почти-копий: признаки, которые повторяют друг друга, остаются проблемой и для него.
