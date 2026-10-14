---
title: "Оптимизаторы: инерция, Adam и затухание весов"
lead: "Обычный шаг спуска ползёт по пологим склонам и боится признаков разного масштаба. Нейросети учатся не голым спуском, а оптимизаторами — правилами шага, которые чинят обе беды. Разбираем инерцию и Adam руками и на доставках, а заодно смотрим, как L2-штраф из Ridge выглядит внутри шага."
files: [deliveries.csv]
recap:
  - "Инерция: v ← β·v + g, w ← w − η·v — на пологих склонах шаги разгоняются. Adam добавляет деление на сглаженный размер градиента √ŝ: у каждого веса свой шаг, разный масштаб признаков не страшен; первый шаг — ровно η."
  - "L2-штраф λ·Σw² добавляет к градиенту 2λw (кроме свободного члена): веса «затухают» на каждом шаге. Спуск со штрафом приходит к Ridge с alpha = λ·n."
---

## Умнее шаг: инерция, Adam и L2-штраф

У обычного шага два слабых места, и оба мы уже видели. Первое: на длинном пологом склоне спуск ползёт, как свободный член модели «минуты = w·км + b» в уроке «Градиентный спуск: шаг за шагом к минимуму». Второе: шаг один на все веса, поэтому без масштабирования признаков он либо взрывается, либо стоит на месте. Нейросети в главе 11 и `MLPClassifier` учатся не голым спуском, а **оптимизаторами** — правилами шага, которые чинят обе проблемы. Разберём два главных: инерцию и Adam. А заодно посмотрим, как выглядит внутри шага L2-штраф из Ridge (глава 7).

Зачем это в главе про бустинг? Бустингу из следующих уроков оптимизаторы не понадобятся: он строит деревья, а не двигает веса шагами. Урок — задел для главы 11: там Adam — оптимизатор по умолчанию и в `MLPClassifier`, и в PyTorch. Он стоит здесь, потому что обе беды обычного шага вы только что видели своими глазами.

### Инерция (momentum)

::: tip Аналогия
Тележка с мешками кофе на пологом пандусе. Каждый толчок (градиент) добавляет ей скорости, и скорость не пропадает между толчками: на длинном пологом участке тележка разгоняется, хотя каждый толчок слабый. У инерции в спуске роль трения играет число β: какая доля скорости сохраняется к следующему шагу.
:::

Правило шага с инерцией:

$$
v \leftarrow \beta \cdot v + g, \qquad w \leftarrow w - \eta \cdot v
$$

Здесь $g$ — градиент на текущем шаге, $v$ — накопленная «скорость» (в начале 0), $\beta$ — доля скорости, которая сохраняется (обычно 0.9), $\eta$ — шаг обучения. При $\beta = 0$ получается обычный спуск.

Игрушка: пологий склон, градиент всё время −2, $\eta = 0.1$, $\beta = 0.9$. Обычный спуск сдвигал бы вес на 0.1 · 2 = 0.2 за шаг. С инерцией:

- шаг 1: $v = 0.9 \cdot 0 - 2 = -2$, сдвиг 0.2, $w = 0.2$;
- шаг 2: $v = 0.9 \cdot (-2) - 2 = -3.8$, сдвиг 0.38, $w = 0.58$;
- шаг 3: $v = 0.9 \cdot (-3.8) - 2 = -5.42$, сдвиг 0.542, $w = 1.122$.

```python
g, lr, beta = -2.0, 0.1, 0.9          # склон с постоянным наклоном
v, w = 0.0, 0.0
for step in range(1, 6):
    v = beta * v + g                  # копим скорость
    w = w - lr * v                    # шагаем по скорости, а не по градиенту
    print(step, round(v, 3), round(w, 3))
```

Шаги растут: 0.2, 0.38, 0.542… и стремятся к $\eta \cdot |g| / (1 - \beta) = 0.1 \cdot 2 / 0.1 = 2$, то есть в 10 раз больше обычного шага. Там, где градиент меняет знак (у дна ямы), накопленная скорость, наоборот, гасится. Насколько это ускоряет спуск на доставках, вы посчитаете в задаче «Спуск с инерцией».

::: figure momentum-steps
Пологий склон с постоянным градиентом −2, η = 0.1. Обычный спуск каждый раз шагает на 0.2, спуск с инерцией разгоняется и приближается к пределу 2.
:::

{{practice: momentum-hand, momentum}}

### Adam: свой шаг для каждого веса

**Adam** добавляет к инерции вторую идею: делить шаг каждого веса на типичный размер его градиента. Тогда вес с огромным градиентом (как у суммы заказа в рублях) и вес с маленьким шагают одинаково осторожно.

Сначала на числах. Возьмём три доставки из урока «Спуск для многих признаков» (раздел «Градиент одной формулой»): при весах $(0, 5)$ градиент там вышел $g = (-32, -82)$. Обычный спуск с шагом 0.1 сдвинул бы веса на 3.2 и 8.2 — пропорционально градиенту. На первом шаге Adam делит каждую координату градиента на её же размер: $-32 / 32 = -1$, $-82 / 82 = -1$. Сдвиг — $0.1 \cdot 1$ по каждому весу, новые веса $(0.1, 5.1)$. От градиента осталось только направление.

На следующих шагах «размер» — это уже не текущий $|g|$, а сглаженный по прошлым шагам, и к нему добавляется инерция. Полностью правило такое, на каждом шаге $t = 1, 2, \ldots$:

$$
m \leftarrow \beta_1 m + (1 - \beta_1)\, g, \qquad s \leftarrow \beta_2 s + (1 - \beta_2)\, g^2
$$

$$
\hat m = \frac{m}{1 - \beta_1^t}, \qquad \hat s = \frac{s}{1 - \beta_2^t}, \qquad w \leftarrow w - \eta \cdot \frac{\hat m}{\sqrt{\hat s} + \varepsilon}
$$

Расшифровка:

- $m$ — сглаженный градиент (инерция), $s$ — сглаженный **квадрат** градиента, то есть его типичный размер. Оба считаются для каждого веса отдельно и в начале равны 0.
- $\beta_1 = 0.9$, $\beta_2 = 0.999$ — насколько долго «помнится» прошлое; это стандартные значения, их почти не меняют.
- $\hat m$, $\hat s$ — поправка на старт с нуля: без неё первые $m$ и $s$ были бы заниженными.
- $\varepsilon = 10^{-8}$ — крошечное число, чтобы не делить на ноль.
- Все операции — поэлементные: у каждого веса свои $m$, $s$ и свой шаг.

Проверим по формулам, что первый шаг на тех же трёх доставках ($g = (-32, -82)$, $\eta = 0.1$) действительно такой, как мы посчитали на числах:

- $m = 0.1 \cdot g = (-3.2, -8.2)$, $s = 0.001 \cdot g^2 = (1.024, 6.724)$;
- поправка при $t = 1$: $\hat m = m / 0.1 = (-32, -82)$, $\hat s = s / 0.001 = (1024, 6724)$;
- $\sqrt{\hat s} = (32, 82)$, и шаг $= 0.1 \cdot (-32 / 32, -82 / 82) = (-0.1, -0.1)$;
- новые веса $w = (0, 5) - (-0.1, -0.1) = (0.1, 5.1)$.

Градиенты отличались в 2.5 раза, а сдвиги одинаковые: на первом шаге Adam двигает каждый вес ровно на $\eta$ в сторону уменьшения ошибки. Размер градиента влияет только на направление, а не на длину шага. Поэтому Adam не боится признаков разного масштаба. Проверим на сумме заказа в рублях, которая в уроке «Спуск для многих признаков» ломала обычный спуск:

::: figure adam-first
Первый шаг на трёх доставках при весах (0, 5). Обычный спуск сдвигает веса на 3.2 и 8.2 — пропорционально градиенту; Adam сдвигает каждый ровно на η = 0.1.
:::

```python
import numpy as np
import pandas as pd

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)   # без масштаба!
y = ok["actual_min"].values
X1 = np.column_stack([np.ones(len(X)), X])
n = len(y)

def mse(w):
    return np.mean((X1 @ w - y) ** 2)

w = np.zeros(5)                                  # обычный спуск с предельным шагом
for _ in range(2000):
    w = w - 2e-6 * 2 / n * X1.T @ (X1 @ w - y)
print("обычный спуск:", round(mse(w), 1))

w, m, s = np.zeros(5), np.zeros(5), np.zeros(5)  # Adam
b1, b2, eps, lr = 0.9, 0.999, 1e-8, 0.05
for t in range(1, 2001):
    g = 2 / n * X1.T @ (X1 @ w - y)
    m = b1 * m + (1 - b1) * g
    s = b2 * s + (1 - b2) * g ** 2
    m_hat, s_hat = m / (1 - b1 ** t), s / (1 - b2 ** t)
    w = w - lr * m_hat / (np.sqrt(s_hat) + eps)
print("Adam:", round(mse(w), 1), "| веса:", [round(float(v), 3) for v in w])
print("минимум:", round(mse(np.linalg.lstsq(X1, y, rcond=None)[0]), 1))
```

**Что здесь происходит:**

- Признаки **не** масштабированы: сумма заказа — сотни и тысячи рублей.
- Обычный спуск идёт с шагом 2e-6, почти предельным: с 1e-5 он взрывается (урок «Спуск для многих признаков»).
- Adam — те же 2000 шагов, пять строк вместо одной. `g ** 2`, `np.sqrt`, деление — поэлементные, поэтому у каждого веса свой шаг.
- `[round(float(v), 3) for v in w]` — печатаем веса списком: так numpy не переходит на запись вида `1.5969e+01` из-за крошечного веса суммы заказа (−0.002).
- `np.linalg.lstsq` — точное решение для сравнения: тот же ответ, что нормальное уравнение.

**Как читать результат.** Обычный спуск застрял на MSE около 348: по пологим направлениям он почти не сдвинулся. Adam дошёл до минимума 60.0, а его веса почти совпали с точным решением: около 15.97 минуты базово, 3.88 на километр и 13.65 надбавки пешему против точных 16.04, 3.868 и 13.612. Масштабирование всё равно полезно, Adam с ним сходится быстрее. Но Adam прощает то, что ломает обычный спуск, поэтому он — оптимизатор по умолчанию для нейросетей (`solver="adam"` в `MLPClassifier`, `torch.optim.Adam` в главе 11).

### L2-штраф внутри шага

Ridge (глава 7) учит веса, добавляя к ошибке штраф за их размер: $L(w) = \text{MSE} + \lambda \cdot (w_1^2 + \ldots + w_d^2)$. Свободный член $w_0$ не штрафуют: он отвечает за средний уровень, а не за силу признаков. Производная $\lambda w_j^2$ по $w_j$ — это $2 \lambda w_j$, поэтому к градиенту просто прибавляется $2 \lambda w$:

$$
w \leftarrow w - \eta \, (g + 2 \lambda w) = (1 - 2 \eta \lambda)\, w - \eta \, g
$$

Вторая запись объясняет второе имя L2-штрафа — **затухание весов** (weight decay): перед обычным шагом каждый вес умножается на число чуть меньше единицы. Игрушка: $w = 10$, $\eta = 0.1$, $\lambda = 0.5$, множитель $1 - 2 \cdot 0.1 \cdot 0.5 = 0.9$. Вес сначала «усыхает» до 9 и только потом делает шаг по градиенту. Так выглядит регуляризация изнутри: признак получает большой вес, только если градиент снова и снова тянет его вверх сильнее, чем штраф тянет вниз.

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])
n = len(y)

for lam in [0.05, 0.5, 2.0]:
    w = np.zeros(5)
    for _ in range(1000):
        g = 2 / n * X1.T @ (X1 @ w - y)
        penalty = 2 * lam * w
        penalty[0] = 0                           # свободный член не штрафуем
        w = w - 0.1 * (g + penalty)
    ridge = Ridge(alpha=lam * n).fit(Xs, y)
    same = np.allclose(w, np.r_[ridge.intercept_, ridge.coef_], atol=1e-6)
    print(f"λ = {lam}: веса {w[1:].round(2)}, MSE {np.mean((X1 @ w - y) ** 2):.2f}, как Ridge: {same}")
```

**Что здесь происходит:**

- `penalty = 2 * lam * w`, `penalty[0] = 0` — добавка к градиенту для всех весов, кроме свободного члена.
- `Ridge(alpha=lam * n)` — у sklearn штраф прибавляется к **сумме** квадратов ошибок, а у нас — к **среднему**. Поэтому их сила отличается в $n$ раз: $\alpha = \lambda \cdot n$.
- `same` — веса спуска со штрафом совпали с весами Ridge.

**Как читать результат.** Чем больше λ, тем меньше веса: вес расстояния (на стандартизированных признаках) — 6.89 при λ = 0.05, 4.27 при 0.5 и 1.91 при 2. Ошибка на обучении при этом растёт: 60.37, 71.12, 93.27. Это цена штрафа, а платят её ради устойчивости весов и качества на новых данных. Во всех трёх случаях спуск со штрафом пришёл ровно к решению Ridge. `SGDRegressor` из урока «Спуск для многих признаков», кстати, по умолчанию тоже со штрафом: `penalty="l2"`, `alpha=0.0001`.

::: figure l2-shrink
Веса того же спуска (1000 шагов, η = 0.1, стандартизированные признаки доставок) при λ = 0, 0.05, 0.5 и 2. С ростом λ веса расстояния, пешего курьера и числа позиций сжимаются к нулю, множитель «усыхания» 1 − 2ηλ падает с 1 до 0.6, а MSE на обучении растёт с 60.00 до 93.27. Сумма заказа почти дублирует число позиций (r = 0.95): без штрафа её вес −0.69, со штрафом он становится положительным — штраф делит вес между похожими признаками.
:::

::: quiz
Шаг Adam: $w \leftarrow w - \eta \cdot \hat m / (\sqrt{\hat s} + \varepsilon)$. Градиент по весу суммы заказа в 1000 раз больше, чем по весу расстояния. Что будет с их сдвигами на первом шаге?

- [x] Сдвиги будут одинаковой длины, $\eta$: на первом шаге $\hat m = g$ и $\sqrt{\hat s} = |g|$, их отношение равно ±1
  > Adam делит градиент на его же типичный размер. Большой градиент не даёт большого шага, поэтому разный масштаб признаков ему не страшен.
- [ ] Вес суммы сдвинется в 1000 раз сильнее, как в обычном спуске
  > Так было бы без деления на $\sqrt{\hat s}$. Именно это деление и отличает Adam.
- [ ] Вес суммы сдвинется в 1000 раз слабее
  > Деление на размер градиента уравнивает шаги, а не переворачивает соотношение.
- [ ] Оба веса останутся на месте: на первом шаге $m$ и $s$ ещё нулевые
  > Они нулевые только до первого шага. Уже на первом шаге $m = 0.1 \cdot g$, а поправка $\hat m$ делает из этого полный градиент.
:::

::: warn Типичные ошибки
- **Штрафуют свободный член.** Тогда модель тянет средний уровень прогноза к нулю, и все прогнозы систематически занижены. Обнулите штраф для `w[0]`, как `penalty[0] = 0`.
- **Сравнивают λ и `alpha` из Ridge напрямую.** Штраф к среднему и штраф к сумме отличаются в $n$ раз. Сверяйте `alpha = λ · n`.
- **Забыли поправку $\hat m$, $\hat s$ в Adam.** На первом шаге $m / \sqrt{s} = 0.1 / \sqrt{0.001} \approx 3.16$, и вместо шага $\eta$ получается шаг около $3.16 \eta$. Спуск дёргается в начале, а при большом $\eta$ может уйти далеко от дна.
- **«Adam сходится при любом шаге».** Не при любом: на тех же доставках с $\eta = 1$ спуск не успокаивается у дна. После 2000 шагов MSE — сотни вместо 60 (точное число зависит от окружения: спуск скачет), а между 1000-м и 5000-м шагами она временами подскакивает до 50 тысяч. Шаг Adam тоже подбирают, обычно от 0.001 до 0.1.
:::

{{practice: adam-step, adam-lr, decay, l2-grad}}

## Практика

## task: momentum-hand | Три шага с инерцией | warmup

Склон с постоянным градиентом `g = -1`, шаг `lr = 0.2`, `beta = 0.5`, старт `v = 0`, `w = 0`. Сделайте три шага с инерцией по правилу урока (v ← β·v + g, w ← w − lr·v) и сохраните:

- `ws` — список весов после каждого шага (3 числа, 4 знака);
- `plain_step` — длину шага обычного спуска без инерции: `lr * abs(g)`;
- `limit_step` — к какой длине стремится шаг с инерцией: `lr * abs(g) / (1 - beta)`.

### starter
```python
g, lr, beta = -1.0, 0.2, 0.5
v, w = 0.0, 0.0

```

### check
```python
want = [0.2, 0.5, 0.85]
got = [float(x) for x in need('ws', list)]
assert len(got) == 3, f'В ws {len(got)} чисел, а шагов три.'
assert all(close(a, b, 1e-4) for a, b in zip(got, want)), f'ws = {got}, а нужно {want}. Сначала обновите v, потом w = w - lr * v.'
assert close(need('plain_step'), 0.2, 1e-9), f'plain_step = {need("plain_step")}, а нужно 0.2.'
assert close(need('limit_step'), 0.4, 1e-9), f'limit_step = {need("limit_step")}, а нужно 0.4.'
```

### hint
Шаг 1: v = 0.5 · 0 + (−1) = −1, w = 0 − 0.2 · (−1) = 0.2. Дальше то же самое в цикле из трёх повторов.

### hint
```python
ws = []
for _ in range(3):
    v = beta * v + g
    w = w - lr * v
    ws.append(round(w, 4))
```

### solution
```python
g, lr, beta = -1.0, 0.2, 0.5
v, w = 0.0, 0.0
ws = []
for _ in range(3):
    v = beta * v + g
    w = w - lr * v
    ws.append(round(w, 4))
plain_step = lr * abs(g)
limit_step = lr * abs(g) / (1 - beta)
print(ws, plain_step, limit_step)
```

### explain
Скорости −1, −1.5, −1.75, веса 0.2, 0.5, 0.85: шаги 0.2, 0.3, 0.35 растут к пределу 0.4. При β = 0.5 инерция лишь удваивает шаг, при β = 0.9 из урока — удесятеряет: предел равен обычному шагу, делённому на 1 − β. Поэтому β = 0.9 и даёт заметное ускорение на пологих склонах.

## task: momentum | Спуск с инерцией | plus

Проверим инерцию на модели «минуты = w·км + b» с пяти доставок урока «Градиентный спуск: шаг за шагом к минимуму» — той самой, где свободный член «тянулся» медленно. Правило шага — из раздела выше: v ← β·v + градиент, w ← w − lr·v, отдельно для `w` и для `b`. Запустите 3000 шагов с `lr = 0.02` и β из `[0, 0.5, 0.9]` (β = 0 — обычный спуск). Для каждого β найдите номер первого шага, после которого MSE отличается от минимально возможной `best_mse` (она уже посчитана в заготовке по точному решению `np.polyfit`) меньше чем на 0.01: `steps_by_beta` — словарь `{β: шаг}`. В `final_wb` — `(w, b)` при β = 0.9 после 3000 шагов (3 знака).

### setup
```python
import numpy as np
km = np.array([1.0, 2.0, 3.0, 4.5, 6.0])
minutes = np.array([18.0, 25.0, 34.0, 44.0, 55.0])
_c = np.polyfit(km, minutes, 1)
best_mse = float(np.mean((_c[0] * km + _c[1] - minutes) ** 2))
```

### starter
```python
# уже есть: km, minutes (пять доставок) и best_mse — MSE точного решения np.polyfit
import numpy as np

def run(beta, lr=0.02, steps=3000):
    w, b, vw, vb = 0.0, 0.0, 0.0, 0.0
    history = []
    ...
    return w, b, history

```

### check
```python
import numpy as _np
km0, m0, bm = need('km'), need('minutes'), need('best_mse')
def _r(beta):
    w, b, vw, vb, h = 0.0, 0.0, 0.0, 0.0, []
    for _ in range(3000):
        e = w * km0 + b - m0; dw, db = _np.mean(2 * e * km0), _np.mean(2 * e)
        vw, vb = beta * vw + dw, beta * vb + db; w, b = w - 0.02 * vw, b - 0.02 * vb
        h.append(_np.mean((w * km0 + b - m0) ** 2))
    return w, b, next(i + 1 for i, v in enumerate(h) if v < bm + 0.01)
w = {bt: _r(bt) for bt in [0, 0.5, 0.9]}
g = {float(k): v for k, v in need('steps_by_beta', dict).items()}
assert all(g[k] == w[k][2] for k in w), f'steps_by_beta = {g}, а нужно {({k: v[2] for k, v in w.items()})}.'
fw = need('final_wb')
assert close(fw[0], round(w[0.9][0], 3), 0.0011) and close(fw[1], round(w[0.9][1], 3), 0.0011), f'final_wb = {fw}.'
```

### hint
Внутри цикла: ошибки, две производные, затем скорости `vw = beta * vw + dw`, `vb = beta * vb + db`, затем `w -= lr * vw`, `b -= lr * vb`; в конце — MSE в `history`.

### hint
Номер первого «достаточно хорошего» шага: `next(i + 1 for i, v in enumerate(history) if v < best_mse + 0.01)`.

### solution
```python
import numpy as np

def run(beta, lr=0.02, steps=3000):
    w, b, vw, vb = 0.0, 0.0, 0.0, 0.0
    history = []
    for _ in range(steps):
        err = w * km + b - minutes
        dw, db = np.mean(2 * err * km), np.mean(2 * err)
        vw, vb = beta * vw + dw, beta * vb + db
        w, b = w - lr * vw, b - lr * vb
        history.append(np.mean((w * km + b - minutes) ** 2))
    return w, b, history

steps_by_beta = {}
for beta in [0, 0.5, 0.9]:
    w, b, h = run(beta)
    steps_by_beta[beta] = next(i + 1 for i, v in enumerate(h) if v < best_mse + 0.01)
    if beta == 0.9:
        final_wb = (round(float(w), 3), round(float(b), 3))
print(steps_by_beta, final_wb)
```

### explain
С β = 0.9 спуск доходит до дна почти в 6 раз быстрее, чем обычный (около 75 шагов против 430). Причина — та самая медленная «тяга» свободного члена из урока «Градиентный спуск: шаг за шагом к минимуму»: его градиент маленький, но постоянный по знаку, и инерция его накапливает. Ответ при этом тот же — около 7.42 мин/км и 10.72 мин. Adam из следующего раздела использует ту же инерцию плюс свой шаг для каждого веса.

## task: adam-step | Шаг Adam руками | base

Напишите функцию `adam_step(w, g, m, s, t, lr=0.1, b1=0.9, b2=0.999, eps=1e-8)`: она делает один шаг Adam по формулам урока и возвращает тройку `(w, m, s)` — новые веса, сглаженный градиент и сглаженный квадрат градиента. `t` — номер шага, начиная с 1.

На трёх доставках из разбора первого шага Adam (заготовка: `X1`, `y`, старт `w = (0, 5)`) сделайте 3 шага Adam с `lr = 0.1`. Градиент на каждом шаге — `2 / n * X1.T @ (X1 @ w - y)`. Сохраните:

- `history` — список весов после каждого шага (3 массива по 2 числа, округлите до 4 знаков);
- `first_step` — сдвиг весов на первом шаге, `w` после шага минус `w` до (4 знака);
- `raw_first` — каким был бы первый сдвиг **без** поправки: `-lr * m / (np.sqrt(s) + eps)` с неисправленными `m` и `s` после первого шага (4 знака).

### starter
```python
import numpy as np
X1 = np.array([[1, 1], [1, 2], [1, 4.0]])    # столбец единиц и км
y = np.array([18, 25, 40.0])
n = len(y)

def adam_step(w, g, m, s, t, lr=0.1, b1=0.9, b2=0.999, eps=1e-8):
    ...

```

### check
```python
import numpy as _np
f = need('adam_step')
r = f(_np.array([1.0, -2.0]), _np.array([4.0, -0.5]), _np.array([0.2, 0.1]), _np.array([0.5, 0.01]), 3, lr=0.01)
assert isinstance(r, tuple) and len(r) == 3, 'adam_step возвращает тройку (w, m, s).'
_m = 0.9 * _np.array([0.2, 0.1]) + 0.1 * _np.array([4.0, -0.5]); _s = 0.999 * _np.array([0.5, 0.01]) + 0.001 * _np.array([16.0, 0.25])
_w = _np.array([1.0, -2.0]) - 0.01 * (_m / (1 - 0.9 ** 3)) / (_np.sqrt(_s / (1 - 0.999 ** 3)) + 1e-8)
assert _np.allclose(r[1], _m) and _np.allclose(r[2], _s), 'm или s посчитаны не так: m = b1·m + (1 − b1)·g, s = b2·s + (1 − b2)·g².'
assert _np.allclose(r[0], _w), 'Новые веса не сходятся. Проверьте поправку: m / (1 − b1**t), s / (1 − b2**t), и шаг lr · m̂ / (√ŝ + eps).'
Xt = _np.array([[1, 1], [1, 2], [1, 4.0]]); yt = _np.array([18, 25, 40.0])
w, m, s, H = _np.array([0, 5.0]), _np.zeros(2), _np.zeros(2), []
for t in range(1, 4):
    g = 2 / 3 * Xt.T @ (Xt @ w - yt); m = 0.9 * m + 0.1 * g; s = 0.999 * s + 0.001 * g * g
    if t == 1: raw = -0.1 * m / (_np.sqrt(s) + 1e-8)
    w = w - 0.1 * (m / (1 - 0.9 ** t)) / (_np.sqrt(s / (1 - 0.999 ** t)) + 1e-8); H.append(w.round(4))
h = need('history', list)
assert len(h) == 3, f'В history {len(h)} элементов, а шагов было 3.'
for i in range(3):
    assert _np.allclose(h[i], H[i], atol=1e-4), f'После шага {i + 1} веса {_np.round(h[i], 4)}, а нужно {H[i]}. Градиент пересчитывайте на каждом шаге по новым весам.'
assert _np.allclose(need('first_step'), (H[0] - _np.array([0, 5.0])).round(4), atol=1e-4), f'first_step = {need("first_step")}.'
assert _np.allclose(need('raw_first'), raw.round(4), atol=1e-4), f'raw_first = {need("raw_first")}, а нужно {raw.round(4)}: m после первого шага делится на √s без поправок.'
```

### hint
Внутри функции четыре шага: обновить `m`, обновить `s`, посчитать поправленные `m_hat` и `s_hat`, сдвинуть `w`. Все операции поэлементные, numpy делает их сразу для обоих весов.

### hint
`m = b1 * m + (1 - b1) * g`, `s = b2 * s + (1 - b2) * g ** 2`, `m_hat = m / (1 - b1 ** t)`, `s_hat = s / (1 - b2 ** t)`, `w = w - lr * m_hat / (np.sqrt(s_hat) + eps)`.

### hint
```python
w, m, s = np.array([0, 5.0]), np.zeros(2), np.zeros(2)
history = []
for t in range(1, 4):
    g = 2 / n * X1.T @ (X1 @ w - y)
    w_old = w
    w, m, s = adam_step(w, g, m, s, t)
    if t == 1:
        first_step = ...
        raw_first = ...
    history.append(w.round(4))
```

### solution
```python
import numpy as np
X1 = np.array([[1, 1], [1, 2], [1, 4.0]])    # столбец единиц и км
y = np.array([18, 25, 40.0])
n = len(y)

def adam_step(w, g, m, s, t, lr=0.1, b1=0.9, b2=0.999, eps=1e-8):
    m = b1 * m + (1 - b1) * g
    s = b2 * s + (1 - b2) * g ** 2
    m_hat = m / (1 - b1 ** t)
    s_hat = s / (1 - b2 ** t)
    w = w - lr * m_hat / (np.sqrt(s_hat) + eps)
    return w, m, s

w, m, s = np.array([0, 5.0]), np.zeros(2), np.zeros(2)
history = []
for t in range(1, 4):
    g = 2 / n * X1.T @ (X1 @ w - y)
    w_old = w
    w, m, s = adam_step(w, g, m, s, t)
    if t == 1:
        first_step = (w - w_old).round(4)
        raw_first = (-0.1 * m / (np.sqrt(s) + 1e-8)).round(4)
    history.append(w.round(4))
print(history, first_step, raw_first)
```

### explain
Первый шаг — ровно (0.1, 0.1), как в разборе урока: каждый вес сдвинулся на `lr`, хотя градиенты (−32 и −82) отличались в 2.5 раза. Следующие шаги чуть короче (0.0999, 0.0998): градиент немного уменьшился, а сглаженный размер `s_hat` ещё помнит прошлые большие значения. Без поправки первый сдвиг был бы 0.3162 — втрое больше задуманного `lr`. Поправка и нужна, чтобы первые шаги не зависели от того, что `m` и `s` стартуют с нуля. Если бы вы считали градиент один раз до цикла, все три шага были бы одинаковыми по 0.1. За три шага разница крошечная (0.3 против 0.2998), но на длинном спуске Adam шёл бы по устаревшему направлению и проскочил бы дно.

## task: adam-lr | Шаг Adam тоже подбирают | base

Adam прощает немасштабированные признаки, но не любой шаг. На доставках без масштаба (заготовка: `X1` со столбцом единиц и суммой заказа в рублях, `y`) запустите Adam по 2000 шагов из нулевых весов с каждым `lr` из `[0.005, 0.01, 0.05, 0.2, 1.0]`. Функция одного шага `adam_step` уже есть — та же, что в задаче «Шаг Adam руками». Сохраните:

- `mse_by_lr` — словарь `{lr: MSE после 2000 шагов}` (1 знак);
- `good` — список `lr` (по возрастанию), при которых MSE меньше 61 (минимум на этих данных — 60.0).

### setup
```python
import numpy as np
def adam_step(w, g, m, s, t, lr=0.1, b1=0.9, b2=0.999, eps=1e-8):
    m = b1 * m + (1 - b1) * g
    s = b2 * s + (1 - b2) * g ** 2
    w = w - lr * (m / (1 - b1 ** t)) / (np.sqrt(s / (1 - b2 ** t)) + eps)
    return w, m, s
```

### starter
```python
# уже есть: adam_step(w, g, m, s, t, lr) из задачи «Шаг Adam руками»
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)   # без масштаба
y = ok["actual_min"].values
X1 = np.column_stack([np.ones(len(X)), X])
n = len(y)

```

### check
```python
import numpy as _np, pandas as _pd
d0 = _pd.read_csv('deliveries.csv'); ok0 = d0[d0['actual_min'].between(1, 299)].copy(); ok0['walk'] = (ok0['courier'] == 'пеший').astype(int)
Xa = _np.column_stack([_np.ones(len(ok0)), ok0[['distance_km', 'items', 'walk', 'amount']].values.astype(float)]); ya = ok0['actual_min'].values
W = {}
for lr in [0.005, 0.01, 0.05, 0.2, 1.0]:
    w, m, s = _np.zeros(5), _np.zeros(5), _np.zeros(5)
    for t in range(1, 2001):
        g = 2 / len(ya) * Xa.T @ (Xa @ w - ya); m = 0.9 * m + 0.1 * g; s = 0.999 * s + 0.001 * g * g
        w = w - lr * (m / (1 - 0.9 ** t)) / (_np.sqrt(s / (1 - 0.999 ** t)) + 1e-8)
    W[lr] = round(float(_np.mean((Xa @ w - ya) ** 2)), 1)
got = {float(k): v for k, v in need('mse_by_lr', dict).items()}
assert set(got) == set(W), f'Ключи mse_by_lr — шаги {sorted(W)}, а сейчас {sorted(got)}.'
for lr in W:
    if lr == 1.0:   # при lr = 1 спуск скачет: точное число зависит от порядка операций, важно лишь, что далеко от 60
        assert got[lr] > 61, f'mse_by_lr[1.0] = {got[lr]}: при таком шаге Adam не должен успокоиться у дна. Каждый запуск — с нулевых w, m, s и t от 1 до 2000.'
        continue
    assert close(got[lr], W[lr], 0.11), f'mse_by_lr[{lr}] = {got[lr]}, а нужно {W[lr]}. Каждый запуск — с нулевых w, m, s и t от 1 до 2000.'
want_good = sorted(lr for lr, v in W.items() if v < 61 and lr != 1.0)
assert [float(x) for x in need('good', list)] == want_good, f'good = {need("good")}, а нужно {want_good}.'
```

### hint
Для каждого `lr` начинайте с `w, m, s = np.zeros(5), np.zeros(5), np.zeros(5)`; внутри цикла `for t in range(1, 2001)` считайте градиент по текущим весам и вызывайте `adam_step(..., t, lr=lr)`.

### hint
```python
mse_by_lr = {}
for lr in [0.005, 0.01, 0.05, 0.2, 1.0]:
    w, m, s = np.zeros(5), np.zeros(5), np.zeros(5)
    for t in range(1, 2001):
        g = 2 / n * X1.T @ (X1 @ w - y)
        w, m, s = adam_step(w, g, m, s, t, lr=lr)
    mse_by_lr[lr] = round(float(np.mean((X1 @ w - y) ** 2)), 1)
```

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]].values.astype(float)
y = ok["actual_min"].values
X1 = np.column_stack([np.ones(len(X)), X])
n = len(y)

mse_by_lr = {}
for lr in [0.005, 0.01, 0.05, 0.2, 1.0]:
    w, m, s = np.zeros(5), np.zeros(5), np.zeros(5)
    for t in range(1, 2001):
        g = 2 / n * X1.T @ (X1 @ w - y)
        w, m, s = adam_step(w, g, m, s, t, lr=lr)
    mse_by_lr[lr] = round(float(np.mean((X1 @ w - y) ** 2)), 1)
good = sorted(lr for lr, v in mse_by_lr.items() if v < 61)
print(mse_by_lr, good)
```

### explain
MSE после 2000 шагов: 85.3 при шаге 0.005, 65.1 при 0.01, 60.0 при 0.05 и 0.2, а при 1.0 — сотни (у нас 470 в браузере и 215 в Jupyter: спуск скачет, и точное число зависит от мельчайших различий в округлении). Слишком маленький шаг не успевает дойти: первые шаги Adam — около `lr` на вес, и при 0.005 до свободного члена 16 идти тысячи шагов. Слишком большой не даёт успокоиться у дна. Хорошие шаги — 0.05 и 0.2, но и у них путь не гладкий: на немасштабированных данных MSE по дороге временами подскакивает (при 0.2 — почти до 2000 около 1600-го шага) и снова успокаивается. Adam снимает проблему масштаба признаков, но шаг обучения остаётся гиперпараметром.

## task: decay | Затухание веса | warmup

Затухание весов из раздела про L2-штраф: на каждом шаге вес умножается на $1 - 2\eta\lambda$. Пусть градиент по весу равен нулю (признак ничего не объясняет), $w = 10$, $\eta = 0.1$, $\lambda = 0.5$. Сохраните:

- `factor` — множитель $1 - 2\eta\lambda$;
- `w5` — вес после 5 таких шагов (4 знака);
- `w5_small` — вес после 5 шагов при $\lambda = 0.05$ (4 знака).

### starter
```python
w0, lr, lam = 10.0, 0.1, 0.5

```

### check
```python
assert close(need('factor'), 0.9, 1e-9), f'factor = {need("factor")}, а нужно 0.9: 1 − 2 · 0.1 · 0.5.'
assert close(need('w5'), 5.9049, 1e-4), f'w5 = {need("w5")}, а нужно 5.9049: 10 · 0.9⁵.'
assert close(need('w5_small'), 9.5099, 1e-4), f'w5_small = {need("w5_small")}, а нужно 9.5099: множитель 1 − 2 · 0.1 · 0.05 = 0.99.'
```

### hint
Без градиента шаг — просто `w = factor * w`. Пять шагов — `w0 * factor ** 5`.

### hint
`factor = 1 - 2 * lr * lam`, `w5 = round(w0 * factor ** 5, 4)`, для малого λ множитель `1 - 2 * lr * 0.05`.

### solution
```python
w0, lr, lam = 10.0, 0.1, 0.5
factor = 1 - 2 * lr * lam
w5 = round(w0 * factor ** 5, 4)
w5_small = round(w0 * (1 - 2 * lr * 0.05) ** 5, 4)
print(factor, w5, w5_small)
```

### explain
При λ = 0.5 вес за пять шагов «усох» с 10 до 5.90 — почти вдвое, хотя градиент ничего не делал. При λ = 0.05 — лишь до 9.51. Признак, который не помогает предсказывать, со штрафом постепенно теряет вес; признак, который помогает, удерживается градиентом, тянущим вес обратно.

## task: l2-grad | L2-штраф в спуске и Ridge | plus

Напишите функцию `gd_l2(X1, y, lam, lr=0.1, steps=1000)`: спуск по MSE со штрафом $\lambda \sum w_j^2$, где свободный член `w[0]` не штрафуется. Признаки в заготовке уже стандартизированы, первый столбец `X1` — единицы. Для `lam` из `[0, 0.1, 1.0]` сохраните словари с ключами-λ:

- `weights` — веса после спуска (массивы, свободный член первым);
- `norms` — длина вектора весов **без** свободного члена, `np.linalg.norm(w[1:])` (3 знака);
- `mse_train` — MSE на этих данных (2 знака).

Ещё сохраните `alpha_ridge` — какой `alpha` у `Ridge` соответствует `lam = 1.0` на этих данных, и `same_as_ridge` — совпадают ли веса спуска при `lam = 1.0` с `Ridge(alpha=alpha_ridge)` (`np.allclose(..., atol=1e-6)`).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values.astype(float)
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

def gd_l2(X1, y, lam, lr=0.1, steps=1000):
    ...

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import Ridge as _R
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy(); ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']].values.astype(float); y0 = ok['actual_min'].values
Xs0 = (X0 - X0.mean(axis=0)) / X0.std(axis=0); n0 = len(y0)
f = need('gd_l2')
wt = _np.asarray(f(_np.column_stack([_np.ones(n0), Xs0]), y0, 0.5), dtype=float)
rr = _R(alpha=0.5 * n0).fit(Xs0, y0)
assert wt.shape == (4,), f'gd_l2 вернула форму {wt.shape}, а нужно 4 веса.'
assert abs(wt[0] - y0.mean()) < 1e-4, f'Свободный член {wt[0]:.3f}, а при стандартизированных признаках он должен остаться средним y ({y0.mean():.3f}). Не штрафуйте w[0].'
assert _np.allclose(wt, _np.r_[rr.intercept_, rr.coef_], atol=1e-5), 'gd_l2(X1, y, 0.5) не совпадает с Ridge(alpha=0.5·n). Штраф в градиенте — 2·lam·w (кроме w[0]).'
W, N, M = {}, {}, {}
X10 = _np.column_stack([_np.ones(n0), Xs0])
for lam in [0, 0.1, 1.0]:
    w = _np.zeros(4)
    for _ in range(1000):
        g = 2 / n0 * X10.T @ (X10 @ w - y0); p = 2 * lam * w; p[0] = 0; w = w - 0.1 * (g + p)
    W[lam] = w; N[lam] = round(float(_np.linalg.norm(w[1:])), 3); M[lam] = round(float(_np.mean((X10 @ w - y0) ** 2)), 2)
gw, gn, gm = need('weights', dict), need('norms', dict), need('mse_train', dict)
for lam in W:
    assert _np.allclose(gw[lam], W[lam], atol=1e-6), f'weights[{lam}] = {_np.round(gw[lam], 3)}, а нужно {W[lam].round(3)}.'
    assert close(gn[lam], N[lam], 0.0011), f'norms[{lam}] = {gn[lam]}, а нужно {N[lam]}. Длина без свободного члена: w[1:].'
    assert close(gm[lam], M[lam], 0.011), f'mse_train[{lam}] = {gm[lam]}, а нужно {M[lam]}.'
assert close(need('alpha_ridge'), 1.0 * n0, 1e-6), f'alpha_ridge = {need("alpha_ridge")}. У Ridge штраф к сумме квадратов ошибок, у нас к среднему: alpha = lam · n.'
assert bool(need('same_as_ridge')) is True, 'same_as_ridge должно быть True. Сравните weights[1.0] с np.r_[ridge.intercept_, ridge.coef_].'
```

### hint
Это спуск из урока «Спуск для многих признаков», только к градиенту прибавляется штраф `2 * lam * w`, у которого первый элемент обнулён.

### hint
Внутри цикла: `g = 2 / len(y) * X1.T @ (X1 @ w - y)`, `penalty = 2 * lam * w`, `penalty[0] = 0`, `w = w - lr * (g + penalty)`. Не забудьте `return w`.

### hint
`alpha_ridge = 1.0 * len(y)`; `ridge = Ridge(alpha=alpha_ridge).fit(Xs, y)`; сравнение — с `np.r_[ridge.intercept_, ridge.coef_]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values.astype(float)
y = ok["actual_min"].values
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
X1 = np.column_stack([np.ones(len(Xs)), Xs])

def gd_l2(X1, y, lam, lr=0.1, steps=1000):
    w = np.zeros(X1.shape[1])
    for _ in range(steps):
        g = 2 / len(y) * X1.T @ (X1 @ w - y)
        penalty = 2 * lam * w
        penalty[0] = 0
        w = w - lr * (g + penalty)
    return w

weights, norms, mse_train = {}, {}, {}
for lam in [0, 0.1, 1.0]:
    w = gd_l2(X1, y, lam)
    weights[lam] = w
    norms[lam] = round(float(np.linalg.norm(w[1:])), 3)
    mse_train[lam] = round(float(np.mean((X1 @ w - y) ** 2)), 2)

alpha_ridge = 1.0 * len(y)
ridge = Ridge(alpha=alpha_ridge).fit(Xs, y)
same_as_ridge = bool(np.allclose(weights[1.0], np.r_[ridge.intercept_, ridge.coef_], atol=1e-6))
print(norms, mse_train, alpha_ridge, same_as_ridge)
```

### explain
Длина вектора весов падает с 9.589 до 8.312 и 3.824, а ошибка на обучении растёт с 60.04 до 61.1 и 81.89. Свободный член во всех трёх случаях один и тот же, 34.48 — средняя длительность доставки. Так и должно быть: его не штрафуют, а при стандартизированных признаках он равен среднему ответу. Спуск со штрафом λ = 1 дал ровно веса `Ridge(alpha=1841)`: `Ridge` — это та же MSE со штрафом, только формула у sklearn записана через сумму. Если бы вы штрафовали и `w[0]`, свободный член тоже «усыхал» бы: при стандартизированных признаках он стал бы средним, делённым на $1 + \lambda$. При λ = 0.1 все прогнозы занижены примерно на 3 минуты, при λ = 1 — вдвое, около 17 минут вместо 34.5.
