---
title: Спуск для многих признаков
files: [deliveries.csv]
lead: "Переносим градиентный спуск на настоящую таблицу: градиент для всех весов сразу одной матричной формулой, масштабирование, без которого спуск буксует или взрывается, и стохастический спуск по маленьким порциям данных — так учатся модели на миллионах строк. Как сделать сам шаг умнее — в следующем уроке."
recap:
  - "Градиент MSE для линейной модели: 2/n · Xᵀ(Xw − y). Одна строка numpy считает производные по всем весам."
  - "Признаки разного масштаба делают «яму» вытянутой: шаг, безопасный для одного веса, взрывает другой. Масштабирование (StandardScaler) выравнивает яму."
  - "`nan` в весах или растущая ошибка — почти всегда слишком большой шаг или немасштабированные признаки."
  - "Стохастический спуск (SGD) считает градиент по случайной порции строк (mini-batch). Шаги шумные, зато дешёвые; один проход по всем данным — эпоха."
  - "В sklearn: `make_pipeline(StandardScaler(), SGDRegressor())` — линейная регрессия, обученная стохастическим спуском."
---

## Градиент одной формулой

В уроке «Градиентный спуск: шаг за шагом к минимуму» производные по $w$ и $b$ мы писали отдельно. Если признаков много, удобнее матрицы (глава 9). Пусть $X_1$ — признаки со столбцом единиц, $w$ — все веса вместе со свободным членом. Тогда ошибки — вектор $X_1 w - y$, а градиент MSE по всем весам сразу:

$$
g = \frac{2}{n} \cdot X_1^\top (X_1 w - y)
$$

Каждая координата $g$ — производная по своему весу. Разберём формулу на трёх доставках с одним признаком (км) и свободным членом, при весах $w = (0, 5)$:

| | 1 (столбец единиц) | км | факт $y$ | прогноз $X_1 w$ | ошибка |
|---|---|---|---|---|---|
| доставка 1 | 1 | 1 | 18 | 5 | −13 |
| доставка 2 | 1 | 2 | 25 | 10 | −15 |
| доставка 3 | 1 | 4 | 40 | 20 | −20 |

$X_1^\top \cdot$ ошибки — это две суммы: по столбцу единиц (−13 − 15 − 20 = −48) и по столбцу км (−13·1 − 15·2 − 20·4 = −123). Умножаем на $\frac{2}{n} = \frac{2}{3}$: градиент ≈ (−32, −82). Обе производные отрицательные — оба веса нужно увеличивать. Те же числа дали бы отдельные формулы для $w$ и $b$ из урока «Градиентный спуск: шаг за шагом к минимуму»; матричная запись просто считает все веса сразу.

::: figure grad-matrix
Разбор формулы на трёх доставках: каждая координата градиента — сумма «ошибка × признак» по своему столбцу, умноженная на 2/n.
:::

Проверим на доставках, что спуск приходит к решению `LinearRegression`:

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values

X1 = np.column_stack([np.ones(len(X)), X])
w = np.zeros(X1.shape[1])
for _ in range(500):
    g = 2 / len(y) * X1.T @ (X1 @ w - y)
    w = w - 0.05 * g

lr = LinearRegression().fit(X, y)
print("спуск:  ", w.round(2))
print("точно:  ", np.r_[lr.intercept_, lr.coef_].round(2))
```

**Что здесь происходит:**

- `ok = d[d["actual_min"].between(1, 299)]` — убираем выбросы времени доставки (глава 6).
- `np.column_stack([np.ones(len(X)), X])` — добавляем столбец единиц: вес при нём — свободный член.
- `X1.T @ (X1 @ w - y)` — для каждого признака сумма «ошибка × значение признака»; `2 / len(y)` превращает сумму в производную среднего квадрата.
- `np.r_[lr.intercept_, lr.coef_]` — склеиваем свободный член и веса `LinearRegression` в один вектор для сравнения.

Спуск пришёл к тем же весам: 16 минут базово, 3.9 на километр, 1.6 на позицию, 13.6 надбавка пешему.

{{practice: grad-vec, one-step, gd-fit}}

## Когда признаки разного масштаба

Добавим сумму заказа `amount` — она в рублях, сотни и тысячи. Теперь яма потерь вытянута: по весу суммы она очень крутая (маленькое изменение веса × тысячи рублей = большая ошибка), по остальным — пологая. Шаг, подходящий для пологих направлений, на крутом сразу «выстреливает»:

```python
import numpy as np
import pandas as pd

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)
y = ok["actual_min"].values

def gd(X, y, lr, steps):
    X1 = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X1.shape[1])
    for _ in range(steps):
        w = w - lr * 2 / len(y) * X1.T @ (X1 @ w - y)
    return np.mean((X1 @ w - y) ** 2)

for lr in [1e-6, 2e-6, 1e-5]:
    print("без масштаба, шаг", lr, "→ MSE", round(float(gd(X, y, lr, 500)), 1))

Xs = (X - X.mean(axis=0)) / X.std(axis=0)
print("с масштабом, шаг 0.1, 100 шагов → MSE", round(float(gd(Xs, y, 0.1, 100)), 1))
```

**Что здесь происходит:**

- `gd(X, y, lr, steps)` — тот же спуск, обёрнутый в функцию; возвращает итоговую MSE.
- `(X - X.mean(axis=0)) / X.std(axis=0)` — стандартизация каждого столбца: среднее 0, разброс 1 (глава 7).
- Сравниваем три шага без масштаба и один — с масштабом.

Без масштаба выбор плохой в обе стороны: шаг 1e-5 уже взрывается (`nan` — «не число», результат переполнения), а безопасные шаги за 500 итераций почти никуда не сдвинулись (MSE около 360 против возможных 60). После масштабирования яма становится «круглой»: хватает 100 шагов с шагом 0.1, чтобы дойти до минимума.

::: figure scale-pit
Условная схема с двумя весами вместо пяти: линии — уровни одинаковой ошибки, точки — шаги спуска. Внизу — настоящие числа для доставок из разбора «Почему шаг ограничен сверху» ниже: предельный шаг и во сколько раз самое крутое направление круче самого пологого.
:::

::: warn
Если веса стали `nan` или ошибка растёт — первым делом проверьте масштаб признаков и уменьшите шаг. Для моделей, которые учатся спуском (логистическая регрессия, SGD, нейросети), масштабирование — не косметика, а условие обучения. Вспомните предупреждение `ConvergenceWarning` из главы 6: это тот же эффект.
:::

::: quiz
Один признак — расстояние в км (1–10), другой — сумма заказа в рублях (200–3000). Почему спуск без масштабирования не сходится при разумном шаге?

- [x] Градиент по «рублёвому» весу в сотни раз больше: шаг, безопасный для одного веса, разносит другой
  > Шаг один на все веса. Стандартизация выравнивает масштабы, и один шаг подходит всем.
- [ ] Рубли нельзя использовать в регрессии
  > Можно, но перед спуском признаки приводят к одному масштабу.
- [ ] Признаки коррелируют
  > Корреляция тут ни при чём — проблема в разнице масштабов.
- [ ] Нужно больше эпох
  > Если спуск разошёлся, лишние эпохи не помогут.
:::

## Разберём вместе: почему шаг ограничен сверху

Почему без масштаба шаг 1e-5 взрывается, а 2e-6 — нет? Для MSE у линейной модели есть точный ответ. Сначала разберём его на игрушке с двумя весами.

Пусть яма потерь устроена так, что вдоль первого веса её стенки крутые, а вдоль второго — пологие: крутизна 10 и 1. Отклонение весов от дна обозначим $v = (v_1, v_2)$. Градиент такой ямы — $(10 \cdot v_1,\ 1 \cdot v_2)$, и шаг спуска $v \leftarrow v - \eta \cdot \text{градиент}$ умножает каждое отклонение на своё число: $v_1$ на $(1 - 10\eta)$, $v_2$ на $(1 - \eta)$. Спуск сходится, если оба множителя по модулю меньше 1. Для крутого направления это значит $\eta < 2 / 10 = 0.2$. При $\eta = 0.15$ множитель $1 - 1.5 = -0.5$: первый вес качается через дно, но отклонение каждый раз уменьшается вдвое. При $\eta = 0.25$ множитель $-1.5$, и качание раскачивается. Пологое направление при этом сходится медленно: множитель 0.85 при $\eta = 0.15$.

```python
import numpy as np
H = np.array([[10.0, 0.0], [0.0, 1.0]])   # крутизна ямы: 10 вдоль первого веса, 1 вдоль второго
print(np.linalg.eigvalsh(H))               # собственные числа: [ 1. 10.]
for lr in [0.15, 0.25]:
    v = np.array([1.0, 1.0])               # отклонение весов от дна
    for _ in range(5):
        v = v - lr * H @ v                  # градиент этой ямы — H @ v
    print(lr, v.round(3))
```

После пяти шагов при $\eta = 0.15$ отклонения (−0.031, 0.444): крутое направление почти у дна, пологое прошло лишь половину пути. При $\eta = 0.25$ — (−7.594, 0.237): крутое направление улетело.

Числа «крутизна вдоль главных направлений ямы» называют **собственными числами** матрицы. У нашей игрушки матрица диагональная, и её собственные числа — просто числа на диагонали, 10 и 1. Когда признаки связаны между собой, яма повёрнута: её самые крутое и самое пологое направления — уже не отдельные веса, а их сочетания. Но крутизну вдоль них по-прежнему находит `np.linalg.eigvalsh`. Для MSE линейной модели роль `H` играет матрица $\frac{2}{n} \cdot X_1^\top X_1$: её произведение на отклонение весов от дна — это и есть градиент. Правило то же, что в игрушке: спуск сходится, пока шаг меньше $2 / \lambda_{\max}$, где $\lambda_{\max}$ — наибольшее собственное число. Посчитаем его на доставках до и после масштабирования:

```python
import numpy as np
import pandas as pd

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)
Xs = (X - X.mean(axis=0)) / X.std(axis=0)

for name, A in [("без масштаба", X), ("с масштабом", Xs)]:
    X1 = np.column_stack([np.ones(len(A)), A])
    ev = np.linalg.eigvalsh(2 / len(A) * X1.T @ X1)      # собственные числа, по возрастанию
    print(f"{name}: самое крутое {ev[-1]:.3g}, самое пологое {ev[0]:.3g}, "
          f"предельный шаг {2 / ev[-1]:.3g}, вытянутость {ev[-1] / ev[0]:.3g}")
```

**Что здесь происходит:**

- `np.linalg.eigvalsh` — собственные числа симметричной матрицы по возрастанию: крутизна ямы вдоль каждого главного направления. `ev[-1]` — самое крутое, `ev[0]` — самое пологое.
- Предельный шаг `2 / λ_max` — больше него спуск по самому крутому направлению перепрыгивает дно всё дальше и расходится.
- «Вытянутость» $\lambda_{\max} / \lambda_{\min}$ — во сколько раз самое крутое направление круче самого пологого.

**Что получилось:** без масштаба предельный шаг около $2 \cdot 10^{-6}$ — ровно поэтому 2e-6 ещё работает, а 1e-5 уже взрывается. А вытянутость — около пяти миллионов: при таком шаге вдоль пологих направлений спуск ползёт миллионы шагов. После масштабирования предельный шаг около 0.5, вытянутость около 40 — яма почти «круглая», и 100 шагов хватает. Масштабирование — это не косметика: оно меняет форму ямы.

{{practice: max-lr, to-goal}}

## Стохастический спуск

Каждый шаг обычного спуска проходит по **всем** строкам. На миллионе строк это дорого. **Стохастический градиентный спуск** (SGD) считает градиент по маленькой случайной порции — **мини-батчу**, например 32 строки. Градиент получается шумным, но в среднем указывает в нужную сторону, а шагов за то же время можно сделать в тысячи раз больше.

::: tip Аналогия
Обычный спуск — как настраивать рецепт нового бленда, каждый раз опрашивая всех гостей сети: точно, но одна правка занимает неделю. Стохастический — как спрашивать по 32 случайных гостя и сразу подкручивать рецепт: каждый маленький опрос шумный и может увести чуть в сторону, но в среднем указывает верно, а правок за ту же неделю получается во много раз больше. Под конец мнения маленьких групп продолжают тянуть рецепт в разные стороны — поэтому шаг правок постепенно уменьшают.
:::

Один проход по всем данным порциями называется **эпохой**.

::: figure sgd-epoch
Одна эпоха на доставках: 1841 строка в новом случайном порядке, 57 батчей по 32 строки и последний из 17. Каждый батч — отдельный шаг спуска.
:::

```python
import numpy as np
import pandas as pd

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

rng = np.random.default_rng(0)
w = np.zeros(X1.shape[1])
for epoch in range(5):
    order = rng.permutation(len(y))                 # перемешиваем строки каждую эпоху
    for start in range(0, len(y), 32):
        b = order[start:start + 32]                 # номера строк батча
        g = 2 / len(b) * X1[b].T @ (X1[b] @ w - y[b])
        w = w - 0.05 * g
    print(f"эпоха {epoch + 1}: MSE {np.mean((X1 @ w - y) ** 2):.1f}")
```

**Что здесь происходит:**

- `rng.permutation(len(y))` — новый случайный порядок строк в каждой эпохе.
- `order[start:start + 32]` — номера строк очередного батча; `X1[b]`, `y[b]` — сам батч.
- Градиент считается только по батчу и делится на его размер `len(b)` (последний батч короче).
- MSE печатаем по всем данным после каждой эпохи.

Уже после первой эпохи (около 58 маленьких шагов) ошибка почти минимальная — около 60. Дальше она «дрожит» вокруг минимума: каждый батч тянет веса немного в свою сторону. Поэтому шаг SGD обычно постепенно уменьшают.

::: predict
```python static
n, batch = 1000, 50
print(n // batch)
```

- `50`
- [x] `20`
- `1000`

Почему: за эпоху каждая строка используется один раз, порциями по 50 — значит, 1000 / 50 = 20 шагов.
:::

::: quiz
После первой эпохи стохастического спуска MSE почти минимальная, но дальше от эпохи к эпохе не убывает ровно, а «дрожит». Почему?

- [x] Каждый батч даёт свой, шумный градиент и тянет веса немного в свою сторону — у дна эти рывки уже сравнимы с оставшимся путём
  > Градиент по 32 строкам лишь в среднем совпадает с градиентом по всем данным. Поэтому шаг SGD к концу обучения обычно уменьшают.
- [ ] Шаг слишком большой, и спуск начал расходиться
  > При расходимости ошибка росла бы всё сильнее и ушла бы в `nan`. Здесь она колеблется около минимума.
- [ ] Модель переобучилась на последних батчах
  > MSE считается по всем данным, а у линейной модели с тремя признаками переобучаться почти нечему. Дрожь — от шума градиента.
- [ ] Перемешивание строк в каждой эпохе сбрасывает накопленный прогресс
  > Веса между эпохами сохраняются, перемешивание меняет только порядок батчей. Оно как раз помогает не застревать в одном и том же порядке.
:::

{{practice: p-batch, minibatch, decay}}

## SGD в sklearn

В sklearn стохастический спуск для линейной регрессии — `SGDRegressor` (для классификации — `SGDClassifier`). Масштабирование ставим в конвейер:

```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDRegressor

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]

model = make_pipeline(StandardScaler(), SGDRegressor(random_state=0)).fit(X, y)
sgd = model[-1]
print("веса (на масштабированных признаках):", sgd.coef_.round(2))
print("эпох до остановки:", sgd.n_iter_)
```

**Что здесь происходит:**

- `make_pipeline(StandardScaler(), SGDRegressor(random_state=0))` — масштаб и SGD одним конвейером.
- `model[-1].coef_` — веса на **масштабированных** признаках: их нельзя напрямую читать как «минут на км», в отличие от весов `LinearRegression` на исходных.

`SGDRegressor` сам останавливается, когда ошибка перестаёт заметно падать (`n_iter_` — сколько эпох понадобилось). Для двух тысяч строк он не нужен — `LinearRegression` быстрее и точнее. SGD нужен, когда данные не помещаются в память или приходят потоком: `partial_fit` дообучает модель на каждой новой порции.

{{practice: sgd-sklearn}}

## Практика

## task: grad-vec | Градиент матрицей | warmup

Для маленькой таблицы `X1` (уже со столбцом единиц) и весов `w` посчитайте градиент MSE формулой `2 / n * X1.T @ (X1 @ w - y)` и сохраните его в `g`. В `direction` сохраните список: для каждого веса `"вверх"`, если вес надо увеличивать (градиент отрицательный), иначе `"вниз"`.

### starter
```python
import numpy as np
X1 = np.array([[1, 1.0], [1, 2.0], [1, 3.0]])
y = np.array([5.0, 7.0, 9.0])
w = np.array([0.0, 4.0])

```

### check
```python
import numpy as _np
X0 = _np.array([[1, 1.0], [1, 2.0], [1, 3.0]]); y0 = _np.array([5.0, 7.0, 9.0]); w0 = _np.array([0.0, 4.0])
gg = 2 / 3 * X0.T @ (X0 @ w0 - y0)
assert _np.allclose(need('g'), gg), f'g = {need("g")}, а нужно {gg.round(3)}.'
assert list(need('direction')) == ['вверх' if v < 0 else 'вниз' for v in gg], f'direction = {need("direction")}.'
```

### hint
Ошибки — `X1 @ w - y` (вектор длины n); градиент — X1ᵀ, умноженное на ошибки, и множитель 2/n.

### hint
`g = 2 / len(y) * X1.T @ (X1 @ w - y)`.

### solution
```python
import numpy as np
X1 = np.array([[1, 1.0], [1, 2.0], [1, 3.0]])
y = np.array([5.0, 7.0, 9.0])
w = np.array([0.0, 4.0])
g = 2 / len(y) * X1.T @ (X1 @ w - y)
direction = ["вверх" if v < 0 else "вниз" for v in g]
```

### explain
Данные точно ложатся на y = 3 + 2x. При w = [0, 4] прогнозы 4, 8, 12, ошибки −1, 1, 3, и градиент g = (2, 6.67): обе координаты положительные, оба веса надо **уменьшать**. Наклон — понятно: 4 больше нужных 2. А свободный член? Истинный — 3, у нас 0, но градиент велит его тоже уменьшать. Из-за слишком большого наклона прогнозы в среднем выше фактов (средняя ошибка +1), и сдвиг всей прямой вниз сейчас уменьшает ошибку. Градиент показывает лучшее направление из текущей точки, а не путь к ответу. Спуск сначала опустит наклон, и только потом свободный член пойдёт вверх, к 3.

## task: one-step | Один шаг руками | warmup

Три доставки, один признак и столбец единиц: `X1 = [[1, 1], [1, 2], [1, 3]]`, ответы `y = [3, 5, 7]`, стартовые веса `w = [0, 0]`. Посчитайте градиент MSE `g = 2 / n * X1.T @ (X1 @ w - y)` и веса после одного шага `w_new = w - lr * g` при `lr = 0.1`. Сохраните также `mse_before` и `mse_after` — MSE до и после шага.

### starter
```python
import numpy as np
X1 = np.array([[1, 1], [1, 2], [1, 3]], dtype=float)
y = np.array([3, 5, 7], dtype=float)
w = np.zeros(2)
lr = 0.1

```

### check
```python
import numpy as _np
X1 = _np.array([[1, 1], [1, 2], [1, 3]], dtype=float); y = _np.array([3, 5, 7], dtype=float)
g = 2 / 3 * X1.T @ (X1 @ _np.zeros(2) - y); wn = -0.1 * g
assert _np.allclose(need('g'), g), f'g = {need("g")}, а нужно {g.round(3)}.'
assert _np.allclose(need('w_new'), wn), f'w_new = {need("w_new")}, а нужно {wn.round(3)}.'
assert close(need('mse_before'), ((y) ** 2).mean()) and close(need('mse_after'), ((X1 @ wn - y) ** 2).mean(), 1e-6), 'mse_before / mse_after не совпадают.'
```

### hint
Прогноз с нулевыми весами — нули, ошибки `X1 @ w - y` = `[-3, -5, -7]`. Градиент: `2 / 3 * X1.T @ ошибки`.

### hint
`w_new = w - lr * g`; MSE — `((X1 @ веса - y) ** 2).mean()`.

### solution
```python
import numpy as np
X1 = np.array([[1, 1], [1, 2], [1, 3]], dtype=float)
y = np.array([3, 5, 7], dtype=float)
w = np.zeros(2)
lr = 0.1
n = len(y)
g = 2 / n * X1.T @ (X1 @ w - y)
w_new = w - lr * g
mse_before = ((X1 @ w - y) ** 2).mean()
mse_after = ((X1 @ w_new - y) ** 2).mean()
```

### explain
Руками: ошибки −3, −5, −7. Первая координата градиента — 2/3 × (−3 − 5 − 7) = −10, вторая — 2/3 × (−3 − 10 − 21) ≈ −22.67. Оба отрицательные — оба веса надо увеличить. После шага w ≈ [1.0, 2.27], MSE падает с 27.67 до примерно 0.33: один шаг уже почти нашёл прямую y = 1 + 2x.

## task: p-batch | Нарезка на батчи | warmup

Соберите код, который перемешивает номера 10 строк и печатает размеры батчей по 4.

### parsons
```python
import numpy as np
rng = np.random.default_rng(0)
order = rng.permutation(10)
sizes = []
for start in range(0, 10, 4):
    batch = order[start:start + 4]
    sizes.append(len(batch))
print(sizes)
```

### check
```python
assert _lines == ['[4, 4, 2]'], f'Сейчас: {_lines}.'
```

### hint
Последний батч короче — в нём остаток строк.

### hint
Начала батчей — `range(0, n, size)`; батч — срез `[start:start + size]`.

## task: gd-fit | Спуск на доставках | base

Напишите функцию `gd(X1, y, lr, steps)`, возвращающую веса после `steps` шагов спуска из нулей. Обучите линейную модель на масштабированных признаках `distance_km`, `items`, `walk` (`Xs` уже в заготовке) со столбцом единиц: `lr = 0.1`, 200 шагов. Сохраните веса `w` и `mse` — MSE на тех же данных (2 знака).

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
Xs0 = (X0 - X0.mean(axis=0)) / X0.std(axis=0); X10 = _np.column_stack([_np.ones(len(Xs0)), Xs0])
w0 = _np.zeros(4)
for _ in range(200): w0 = w0 - 0.1 * 2 / len(y0) * X10.T @ (X10 @ w0 - y0)
assert _np.allclose(need('w'), w0, atol=1e-6), f'w = {_np.round(need("w"), 3)}, а нужно {w0.round(3)}. Столбец единиц — первым.'
assert close(need('mse'), round(_np.mean((X10 @ w0 - y0) ** 2), 2)), f'mse = {need("mse")}.'
assert len(need('gd')(X10, y0, 0.1, 1)) == 4, 'gd должна возвращать вектор весов.'
```

### hint
Масштабируйте признаки до спуска: `Xs = (X - X.mean(axis=0)) / X.std(axis=0)`.

### hint
Внутри функции: `w = np.zeros(X1.shape[1])`, цикл, `return w`. Столбец единиц: `np.column_stack([np.ones(len(Xs)), Xs])`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)

def gd(X1, y, lr, steps):
    w = np.zeros(X1.shape[1])
    for _ in range(steps):
        w = w - lr * 2 / len(y) * X1.T @ (X1 @ w - y)
    return w

X1 = np.column_stack([np.ones(len(Xs)), Xs])
w = gd(X1, y, 0.1, 200)
mse = round(np.mean((X1 @ w - y) ** 2), 2)
```

### explain
Первый вес — свободный член, на масштабированных признаках он равен среднему времени доставки (около 34 минут): у «среднего» заказа все признаки после масштаба равны нулю.

## task: max-lr | Самый большой безопасный шаг | base

Для масштабированных признаков (как в прошлой задаче, со столбцом единиц) найдите среди шагов `[0.1, 0.3, 0.5, 0.7, 0.9, 1.1]` самый большой, при котором после 100 шагов MSE меньше 61. Сохраните словарь `res` `{шаг: MSE после 100 шагов}` (для взорвавшихся значений будет `inf` или `nan` — это нормально) и `best_lr`.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
Xs0 = (X0 - X0.mean(axis=0)) / X0.std(axis=0); X10 = _np.column_stack([_np.ones(len(Xs0)), Xs0])
want = {}
with _np.errstate(all='ignore'):
    for lr in [0.1, 0.3, 0.5, 0.7, 0.9, 1.1]:
        w = _np.zeros(4)
        for _ in range(100): w = w - lr * 2 / len(y0) * X10.T @ (X10 @ w - y0)
        want[lr] = _np.mean((X10 @ w - y0) ** 2)
r = need('res', dict)
for lr, v in want.items():
    got = r.get(lr)
    assert got is not None, f'Нет шага {lr} в res.'
    assert (not _np.isfinite(v) and not _np.isfinite(got)) or (_np.isfinite(v) and close(got, v, 0.01)) or (v > 1e6 and got > 1e6), f'res[{lr}] = {got}, а ожидалось {v:.4g}.'
ok_lrs = [lr for lr, v in want.items() if _np.isfinite(v) and v < 61]
assert need('best_lr') == max(ok_lrs), f'best_lr = {need("best_lr")}, а нужно {max(ok_lrs)}.'
```

### hint
Перебор шагов в цикле; условие — `np.isfinite(mse) and mse < 61`.

### hint
Из разбора «Почему шаг ограничен сверху»: предельный шаг равен 2 / λ_max. У трёх признаков этой задачи он около 0.72 — посчитайте сами: `2 / np.linalg.eigvalsh(2 / len(y) * X1.T @ X1)[-1]`. Число 0.5 из разбора — для четырёх признаков, с суммой заказа.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

res = {}
with np.errstate(all="ignore"):              # не показывать предупреждения о переполнении
    for lr in [0.1, 0.3, 0.5, 0.7, 0.9, 1.1]:
        w = np.zeros(X1.shape[1])
        for _ in range(100):
            w = w - lr * 2 / len(y) * X1.T @ (X1 @ w - y)
        res[lr] = np.mean((X1 @ w - y) ** 2)
best_lr = max(lr for lr, v in res.items() if np.isfinite(v) and v < 61)
```

### explain
Граница резкая: предельный шаг для этих трёх признаков ≈ 0.72. При 0.7 спуск сходится (MSE 60.04), при 0.9 взрывается. Положение границы зависит от данных (от «крутизны» самой крутой стенки ямы), поэтому универсального хорошего шага нет — его подбирают.

## task: minibatch | Мини-батчи | plus

Обучите модель стохастическим спуском: батчи по 64 строки, шаг 0.05, 3 эпохи, генератор `np.random.default_rng(1)`, порядок строк перемешивается в начале каждой эпохи (`rng.permutation`). Сохраните список `epoch_mse` — MSE на всех данных после каждой эпохи (3 числа) и `steps` — сколько всего шагов (обновлений весов) было сделано.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

```

### check
```python
import numpy as _np, pandas as _pd
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values; y0 = ok['actual_min'].values
Xs0 = (X0 - X0.mean(axis=0)) / X0.std(axis=0); X10 = _np.column_stack([_np.ones(len(Xs0)), Xs0])
rng = _np.random.default_rng(1); w = _np.zeros(4); em = []; st = 0
for _ in range(3):
    o = rng.permutation(len(y0))
    for s in range(0, len(y0), 64):
        b = o[s:s + 64]; w = w - 0.05 * 2 / len(b) * X10[b].T @ (X10[b] @ w - y0[b]); st += 1
    em.append(_np.mean((X10 @ w - y0) ** 2))
assert _np.allclose(need('epoch_mse'), em), f'epoch_mse = {need("epoch_mse")}, а нужно {_np.round(em, 2)}.'
assert need('steps') == st, f'steps = {need("steps")}, а нужно {st}.'
```

### hint
Перемешивание — в начале каждой эпохи: `order = rng.permutation(len(y))`.

### hint
Градиент батча делите на размер батча `len(b)` — последний батч короче 64.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

rng = np.random.default_rng(1)
w = np.zeros(X1.shape[1])
epoch_mse, steps = [], 0
for _ in range(3):
    order = rng.permutation(len(y))
    for start in range(0, len(y), 64):
        b = order[start:start + 64]
        w = w - 0.05 * 2 / len(b) * X1[b].T @ (X1[b] @ w - y[b])
        steps += 1
    epoch_mse.append(np.mean((X1 @ w - y) ** 2))
```

### explain
Одна эпоха — один проход по всем 1841 строкам батчами по 64: это 29 шагов (последний батч короче, 49 строк). За 3 эпохи — 87 обновлений весов, тогда как обычный спуск за те же 3 прохода сделал бы всего 3. Поэтому мини-батчи сходятся быстрее: MSE после эпох — 63.9, 60.4, 60.2. Перемешивание в начале каждой эпохи нужно, чтобы батчи не повторялись: если данные упорядочены (например, по дате), без перемешивания модель каждый раз видела бы одни и те же куски в одном порядке.

## task: to-goal | Сколько шагов до цели | base

Посчитайте, за сколько шагов полного (не стохастического) спуска MSE на доставках с четырьмя признаками (`distance_km`, `items`, `walk`, `amount`; таблицы `X`, `Xs` и ответ `y` уже есть в заготовке) опустится ниже 61. Напишите `steps_to(A, lr, goal=61, max_steps=20000)` — номер первого шага, после которого MSE < goal, или `None`, если не дошли. Сохраните `scaled` — словарь `{lr: шаги}` для масштабированных признаков и `lr` из `[0.1, 0.5]`, и `raw` — то же для исходных признаков и `lr` из `[1e-6, 2e-6]`.

### setup
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
```

### starter
```python
# уже есть: X — четыре признака (distance_km, items, walk, amount) без масштаба,
# Xs — они же масштабированные, y — время доставки
import numpy as np

def steps_to(A, lr, goal=61, max_steps=20000):
    X1 = np.column_stack([np.ones(len(A)), A])
    w = np.zeros(X1.shape[1])
    ...

```

### check
```python
import numpy as _np
y0, X0, Xs0 = need('y'), need('X'), need('Xs')
def _st(A, lr, goal=61, ms=20000):
    X1 = _np.column_stack([_np.ones(len(A)), A]); w = _np.zeros(X1.shape[1])
    for i in range(1, ms + 1):
        w = w - lr * 2 / len(y0) * X1.T @ (X1 @ w - y0)
        if _np.mean((X1 @ w - y0) ** 2) < goal: return i
    return None
ws = {lr: _st(Xs0, lr) for lr in [0.1, 0.5]}
g = {float(k): v for k, v in need('scaled', dict).items()}
assert g == ws, f'scaled = {g}, а нужно {ws}.'
gr = {float(k): v for k, v in need('raw', dict).items()}
assert gr == {1e-6: None, 2e-6: None}, f'raw = {gr}: без масштаба за 20 000 шагов цель не достигается.'
```

### hint
Цикл по шагам от 1 до `max_steps`: обновление весов, затем проверка `np.mean((X1 @ w - y) ** 2) < goal` — если да, `return i`.

### hint
Если цикл закончился, а цель не достигнута, верните `None` (просто `return None` после цикла).

### solution
```python
import numpy as np

def steps_to(A, lr, goal=61, max_steps=20000):
    X1 = np.column_stack([np.ones(len(A)), A])
    w = np.zeros(X1.shape[1])
    for i in range(1, max_steps + 1):
        w = w - lr * 2 / len(y) * X1.T @ (X1 @ w - y)
        if np.mean((X1 @ w - y) ** 2) < goal:
            return i
    return None

scaled = {lr: steps_to(Xs, lr) for lr in [0.1, 0.5]}
raw = {lr: steps_to(X, lr) for lr in [1e-6, 2e-6]}
print(scaled, raw)
```

### explain
С масштабом цель достигается примерно за 20 шагов. Шаг 0.5 в пять раз больше, а шагов почти столько же (20 против 19): 0.5 близок к предельному 0.51 для этих четырёх признаков. По самому крутому направлению спуск каждый раз перескакивает дно и качается, поэтому выигрыша нет; шаг 0.3 дошёл бы за 5. Без масштаба — не достигается и за 20 000: шаг нельзя сделать больше 2·10⁻⁶ (иначе расходится), а с таким шагом веса у «пологих» признаков почти не двигаются. Это та самая вытянутость ямы в пять миллионов раз из разбора. Вывод для практики: если модель на спуске учится подозрительно долго — сначала масштаб, потом всё остальное.

## task: decay | Уменьшающийся шаг | plus

SGD с постоянным шагом «дрожит» вокруг минимума. Сравните постоянный шаг 0.05 и уменьшающийся `lr_t = 0.05 / (1 + t / 200)`, где t — номер шага с начала обучения (с 0). Признаки — масштабированные `distance_km`, `items`, `walk` (заготовка: `X1` уже со столбцом единиц), батч 32, 20 эпох, порядок строк — `rng = np.random.default_rng(0)` (свой генератор для каждого варианта). После каждой эпохи запишите MSE на всех данных. Сохраните `last5_const`, `last5_decay` — MSE последних пяти эпох (списки, 3 знака) и `jitter` — словарь `{"const": …, "decay": …}` с размахом (max − min) этих пяти значений (3 знака).

### setup
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values.astype(float)
y = ok["actual_min"].values
X1 = np.column_stack([np.ones(len(y)), (X - X.mean(axis=0)) / X.std(axis=0)])
```

### starter
```python
import numpy as np

def sgd(decay, epochs=20, lr0=0.05, size=32):
    rng = np.random.default_rng(0)
    w = np.zeros(X1.shape[1])
    t = 0
    history = []
    ...
    return history

```

### check
```python
import numpy as _np
A, y0 = need('X1'), need('y')
def _s(decay):
    rng = _np.random.default_rng(0); w = _np.zeros(A.shape[1]); t = 0; h = []
    for _ in range(20):
        order = rng.permutation(len(y0))
        for st in range(0, len(y0), 32):
            b = order[st:st + 32]; g = 2 / len(b) * A[b].T @ (A[b] @ w - y0[b])
            lr = 0.05 / (1 + t / 200) if decay else 0.05; w = w - lr * g; t += 1
        h.append(_np.mean((A @ w - y0) ** 2))
    return [round(float(v), 3) for v in h[-5:]]
c, dd = _s(False), _s(True)
assert all(close(a, b, 0.002) for a, b in zip(need('last5_const'), c)), f'last5_const = {need("last5_const")}, а нужно {c}.'
assert all(close(a, b, 0.002) for a, b in zip(need('last5_decay'), dd)), f'last5_decay = {need("last5_decay")}, а нужно {dd}.'
j = need('jitter', dict)
assert close(j['const'], round(max(c) - min(c), 3), 0.003) and close(j['decay'], round(max(dd) - min(dd), 3), 0.003), f'jitter = {j}.'
```

### hint
Два вложенных цикла: эпохи и батчи. Шаг на каждом батче: `lr = lr0 / (1 + t / 200) if decay else lr0`, затем `t += 1`.

### hint
Перемешивание — `order = rng.permutation(len(y))` в начале каждой эпохи; MSE — после эпохи, по всем строкам: `np.mean((X1 @ w - y) ** 2)`.

### hint
Последние пять — `history[-5:]`; размах — `max(...) - min(...)`.

### solution
```python
import numpy as np

def sgd(decay, epochs=20, lr0=0.05, size=32):
    rng = np.random.default_rng(0)
    w = np.zeros(X1.shape[1])
    t = 0
    history = []
    for _ in range(epochs):
        order = rng.permutation(len(y))
        for start in range(0, len(y), size):
            b = order[start:start + size]
            g = 2 / len(b) * X1[b].T @ (X1[b] @ w - y[b])
            lr = lr0 / (1 + t / 200) if decay else lr0
            w = w - lr * g
            t += 1
        history.append(np.mean((X1 @ w - y) ** 2))
    return history

last5_const = [round(float(v), 3) for v in sgd(False)[-5:]]
last5_decay = [round(float(v), 3) for v in sgd(True)[-5:]]
jitter = {"const": round(max(last5_const) - min(last5_const), 3), "decay": round(max(last5_decay) - min(last5_decay), 3)}
print(last5_const, last5_decay, jitter)
```

### explain
С постоянным шагом MSE в последних эпохах прыгает в пределах пары единиц (каждый батч тянет веса в свою сторону), а с уменьшающимся — почти не меняется и держится у минимума около 60.04. Это стандартная практика: в начале большие шаги, чтобы быстро дойти до дна, в конце — маленькие, чтобы не болтаться вокруг него. В PyTorch за это отвечают «планировщики шага» (`torch.optim.lr_scheduler`).

## task: sgd-sklearn | SGDRegressor и порядок данных | star

Сравните `make_pipeline(StandardScaler(), SGDRegressor(random_state=r))` для `r` в `[0, 1, 2, 3, 4]` на доставках (признаки `distance_km`, `items`, `walk`; цель `actual_min`). Сохраните список `maes` — MAE на тех же данных для каждого `r` (3 знака), `spread` — разницу между наибольшей и наименьшей (3 знака) и `mae_exact` — MAE `LinearRegression` (3 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDRegressor, LinearRegression
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]

```

### check
```python
import pandas as _pd
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import SGDRegressor as _SGD, LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy()
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']]; y0 = ok['actual_min']
w = [round(_mae(y0, _mp(_SS(), _SGD(random_state=r)).fit(X0, y0).predict(X0)), 3) for r in range(5)]
got = [round(float(v), 3) for v in need('maes')]
assert len(got) == 5 and all(close(a, b, 0.002) for a, b in zip(got, w)), f'maes = {got}, а нужно {w}.'
assert close(need('spread'), round(max(w) - min(w), 3), 0.003), f'spread = {need("spread")}.'
assert close(need('mae_exact'), round(_mae(y0, _LR().fit(X0, y0).predict(X0)), 3)), f'mae_exact = {need("mae_exact")}.'
```

### hint
Цикл по `r` в `range(5)`; `random_state` у SGD отвечает за порядок перемешивания строк.

### hint
`spread = round(max(maes) - min(maes), 3)`; MAE — `mean_absolute_error(y, model.predict(X))`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDRegressor, LinearRegression
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]

maes = []
for r in range(5):
    m = make_pipeline(StandardScaler(), SGDRegressor(random_state=r)).fit(X, y)
    maes.append(round(mean_absolute_error(y, m.predict(X)), 3))
spread = round(max(maes) - min(maes), 3)
mae_exact = round(mean_absolute_error(y, LinearRegression().fit(X, y).predict(X)), 3)
```

### explain
Результат SGD немного зависит от порядка строк — разброс — тысячные доли минуты, а точное решение лишь чуть лучше. Для таких данных это неважно, но в нейросетях (глава 11), где спуск — единственный способ обучения, `random_state` фиксируют всегда, иначе результат не повторить.
