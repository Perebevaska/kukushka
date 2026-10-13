---
title: "Проект: распознать цифры в бумажных анкетах"
lead: "Финал главы. Гости до сих пор заполняют бумажные анкеты программы лояльности, и операторы вручную перебивают номера телефонов. Пробуем распознавать рукописные цифры: от логистической регрессии до своей нейросети на numpy и MLP из sklearn — и находим слабое место полносвязных сетей, которое исправят свёрточные сети в главе 14."
recap:
  - "Изображение для модели — таблица яркостей пикселей; картинка 8 × 8 — это 64 признака."
  - "Многоклассовая задача: 10 классов, softmax на выходе, метрика — доля правильных и матрица ошибок 10 × 10."
  - "На маленьких «чистых» картинках простые модели (логистическая регрессия, kNN) уже сильны; сеть даёт прирост, но не чудо."
  - "Матрица ошибок показывает, какие цифры путаются, — это подсказка, где модель слаба и где нужны данные."
  - "Полносвязная сеть не знает, что соседние пиксели связаны: сдвиг цифры на 1 пиксель роняет точность вдвое. Свёрточные сети (глава 14) решают это."
---

## Задача

> Каждую неделю операторы вручную перебивают в базу около 400 бумажных анкет: имя и номер телефона. Ошибки в номерах — главная причина, по которой гости не получают бонусы по SMS.
>
> Можно ли автоматически распознавать цифры, а оператору показывать только те, в которых модель не уверена? Какую точность можно ожидать и есть ли подводные камни?
>
> *Руководитель отдела лояльности*

## Данные

Для прототипа берём открытый набор рукописных цифр, встроенный в sklearn (`sklearn.datasets.load_digits`): 1 797 изображений 8 × 8 пикселей, яркость от 0 до 16, у каждого — правильная цифра. Это не наши анкеты, а учебная замена: на настоящих данных пришлось бы сначала вырезать отдельные цифры из скана.

```python
import matplotlib.pyplot as plt
from sklearn.datasets import load_digits

digits = load_digits()
print(digits.data.shape)                 # 1797 картинок × 64 пикселя
fig, axes = plt.subplots(1, 10, figsize=(10, 1.4))
for i, ax in enumerate(axes):
    ax.imshow(digits.images[i], cmap="gray_r")
    ax.set_title(str(digits.target[i]))
    ax.axis("off")
plt.show()
```

`digits.images` — картинки 8 × 8, `digits.data` — те же картинки, развёрнутые в строку из 64 чисел. Для полносвязной сети и логистической регрессии картинка — просто 64 признака.

::: figure nn-digit-pixels
Четвёртая картинка набора (цифра 3) как таблица яркостей и как строка признаков: первая строка картинки становится признаками x0…x7, вторая — x8…x15 и так далее.
:::

## План

1. Осмотреть данные: баланс классов, как выглядит «средняя» цифра.
2. Разделить на обучение и тест, привести яркость к 0–1.
3. Простые модели: логистическая регрессия и kNN.
4. Своя сеть на numpy: 64 → 32 → 10, с softmax на выходе (урок «Softmax, выход под задачу и мини-батчи»; все формулы — в условии шага).
5. MLP из sklearn.
6. Матрица ошибок: что с чем путается; доля «неуверенных» ответов для проверки оператором.
7. Слабое место: сдвиг картинки на один пиксель.

Разбиение во всех шагах: `X = digits.data / 16`, `train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)`.

::: figure nn-digits-pipeline
Путь одной цифры через проект: картинка 8 × 8 разворачивается в 64 признака, сеть шага 4 выдаёт 10 вероятностей, а правило шага 6 решает, записать ответ в базу или отдать оператору. Картинка — четвёртая в наборе (цифра 3).
:::

::: quiz
Сеть распознаёт цифры с точностью 0.98, но после сдвига картинок на один пиксель — 0.44. Что поможет?

- [x] Аугментация: добавить в обучение сдвинутые копии картинок
  > Сеть выучила положение пикселей, а не форму цифры. Показав ей сдвиги, мы учим её не обращать на них внимания.
- [ ] Больше эпох на тех же картинках
  > Сеть лучше запомнит те же положения, а сдвиги так и останутся незнакомыми.
- [ ] Уменьшить сеть
  > Проблема не в размере, а в том, чему сеть научилась.
- [ ] Ничего: сдвиги в жизни не бывают
  > В бумажных анкетах цифры почти всегда немного сдвинуты.
:::

Откуда такой провал, видно, если сравнить картинку до и после сдвига: человек видит ту же тройку, а для сети поменялась больше половины признаков. Это вы проверите сами в шаге 7.

::: figure nn-digit-shift
Та же цифра 3, сдвинутая на один пиксель вправо: в столбце 3 (признаки x3, x11, …) и в большинстве других клеток стоят совсем другие числа. Доли верных — для MLP из шага 5 на всём тесте.
:::

## task: look | Шаг 1. Классы и «средние» цифры | base

Сохраните `counts` — число картинок каждой цифры (массив длины 10), `balanced` — `True`, если самый редкий класс встречается не реже чем в 0.9 раза от самого частого. Нарисуйте «среднюю» картинку каждой цифры (среднее `digits.images` по картинкам этой цифры) — 10 изображений в ряд, заголовок каждого — цифра. Сохраните `mean_imgs` — массив формы (10, 8, 8).

### starter
```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_digits
digits = load_digits()
y = digits.target

```

### check
```python
import numpy as _np
from sklearn.datasets import load_digits as _ld
dg = _ld()
assert list(_np.asarray(need('counts'))) == list(_np.bincount(dg.target)), f'counts = {need("counts")}.'
c = _np.bincount(dg.target)
assert need('balanced') == bool(c.min() >= 0.9 * c.max()), f'balanced = {need("balanced")}.'
mi = _np.asarray(need('mean_imgs'))
assert mi.shape == (10, 8, 8) and _np.allclose(mi[3], dg.images[dg.target == 3].mean(axis=0)), 'mean_imgs[k] — среднее digits.images по картинкам цифры k.'
assert len(figs) >= 1 and len(figs[-1].axes) >= 10, 'Нарисуйте 10 картинок в один ряд (plt.subplots(1, 10)).'
```

### hint
Картинки лежат в `digits.images` (форма 1797 × 8 × 8), метки — в `digits.target`.

### hint
`np.bincount(y)`; средняя картинка: `digits.images[y == k].mean(axis=0)`; рисование — как в разделе «Данные».

### solution
```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_digits
digits = load_digits()
y = digits.target

counts = np.bincount(y)
balanced = bool(counts.min() >= 0.9 * counts.max())
mean_imgs = np.array([digits.images[y == k].mean(axis=0) for k in range(10)])
fig, axes = plt.subplots(1, 10, figsize=(10, 1.4))
for k, ax in enumerate(axes):
    ax.imshow(mean_imgs[k], cmap="gray_r")
    ax.set_title(str(k))
    ax.axis("off")
plt.show()
```

### explain
Классы сбалансированы (по 174–183 картинки), значит, долю правильных ответов можно использовать как метрику без оговорок из главы 7. «Средние» цифры узнаваемы — уже по ним понятно, что задача не безнадёжная: даже «сравнить с ближайшим средним» дало бы неплохой результат.

## task: simple | Шаг 2–3. Простые модели | base

Разделите данные (`X = digits.data / 16`) и сравните на тесте `LogisticRegression(max_iter=2000)` и `KNeighborsClassifier(n_neighbors=3)`. Сохраните `acc_lr`, `acc_knn` (3 знака).

### starter
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
from sklearn.datasets import load_digits as _ld
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.neighbors import KNeighborsClassifier as _KN
dg = _ld(); a, b, c, d = _tts(dg.data / 16, dg.target, test_size=0.25, random_state=42, stratify=dg.target)
l = round((_LR(max_iter=2000).fit(a, c).predict(b) == d).mean(), 3); k = round((_KN(n_neighbors=3).fit(a, c).predict(b) == d).mean(), 3)
assert close(need('acc_lr'), l, 0.002), f'acc_lr = {need("acc_lr")}, а нужно {l}: логистическая регрессия на X = digits.data / 16 без масштабирования.'
assert close(need('acc_knn'), k, 0.002), f'acc_knn = {need("acc_knn")}, а нужно {k}: kNN на X = digits.data / 16 без масштабирования.'
```

### hint
Две модели — логистическая регрессия и kNN — обучаются на `X_train` и проверяются на `X_test`; признаки уже в шкале 0–1 (яркость поделена на 16). Обучайте обе модели без масштабирования: со `StandardScaler` числа не совпадут с проверкой.

### hint
`(model.predict(X_test) == y_test).mean()`.

### solution
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

acc_lr = round((LogisticRegression(max_iter=2000).fit(X_train, y_train).predict(X_test) == y_test).mean(), 3)
acc_knn = round((KNeighborsClassifier(n_neighbors=3).fit(X_train, y_train).predict(X_test) == y_test).mean(), 3)
```

### explain
Логистическая регрессия — 96 %, ближайшие соседи — больше 98 %. Картинки маленькие, чистые и выровненные по центру, поэтому даже «найди самую похожую картинку из обучения» работает отлично. Это важный ориентир: сеть должна быть не хуже kNN, иначе она не нужна.

## task: own-net | Шаг 4. Своя сеть на numpy | base

Обучите сеть «64 → 32 (ReLU) → 10 (softmax)» на numpy: `rng = np.random.default_rng(0)`, `W1 = rng.normal(size=(64, 32)) * 0.1`, затем `W2 = rng.normal(size=(32, 10)) * 0.1`, смещения — нули, шаг 0.5, 300 шагов по всей обучающей выборке. Сохраните `acc_own` — долю правильных ответов на тесте (3 знака).

Цикл — как в уроке «Обучение сети: обратное распространение ошибки», отличается только выход:

- прямой проход: `Z1 = X_train @ W1 + b1`, `H = np.maximum(0, Z1)`, `P = softmax(H @ W2 + b2)` — матрица вероятностей «картинки × 10 цифр»;
- ошибка на выходе: `D = (P - Y_train) / n`, где `Y_train` — one-hot-ответы (в заготовке), `n` — число обучающих картинок. Для softmax с кросс-энтропией это та же формула «p − y», только для матрицы;
- ошибка скрытого слоя: `dH = D @ W2.T * (Z1 > 0)` — `D @ W2.T` заменяет `np.outer(d2, w2)`, потому что выходов теперь 10;
- градиенты: `H.T @ D` для `W2`, `D.sum(axis=0)` для `b2`, `X_train.T @ dH` для `W1`, `dH.sum(axis=0)` для `b1`.

Если вы решали задачу «Многоклассовая сеть на numpy» урока «Softmax, выход под задачу и мини-батчи», это тот же код с другими размерами.

### starter
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
Y_train = np.eye(10)[y_train]

def softmax(Z):
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)

```

### check
```python
import numpy as _np
from sklearn.datasets import load_digits as _ld
from sklearn.model_selection import train_test_split as _tts
dg = _ld(); a, b, c, d = _tts(dg.data / 16, dg.target, test_size=0.25, random_state=42, stratify=dg.target); Y0 = _np.eye(10)[c]
def sm(Z):
    Z = Z - Z.max(axis=1, keepdims=True); E = _np.exp(Z); return E / E.sum(axis=1, keepdims=True)
r = _np.random.default_rng(0); A = r.normal(size=(64, 32)) * 0.1; a1 = _np.zeros(32); B = r.normal(size=(32, 10)) * 0.1; b1 = _np.zeros(10)
for _ in range(300):
    Z = a @ A + a1; H = _np.maximum(0, Z); P = sm(H @ B + b1); D = (P - Y0) / len(c); dH = D @ B.T * (Z > 0)
    B -= 0.5 * H.T @ D; b1 -= 0.5 * D.sum(0); A -= 0.5 * a.T @ dH; a1 -= 0.5 * dH.sum(0)
w = round((sm(_np.maximum(0, b @ A + a1) @ B + b1).argmax(1) == d).mean(), 3)
assert close(need('acc_own'), w, 0.002), f'acc_own = {need("acc_own")}, а нужно {w}.'
```

### hint
Ответ для 10 классов — one-hot: `Y = np.eye(10)[y_train]`; выход — softmax.

### hint
`dH` считайте до обновления `W2` — по старым весам. Прогноз на тесте: `softmax(np.maximum(0, X_test @ W1 + b1) @ W2 + b2).argmax(axis=1)`.

### solution
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
Y_train = np.eye(10)[y_train]

def softmax(Z):
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)

rng = np.random.default_rng(0)
W1 = rng.normal(size=(64, 32)) * 0.1
b1 = np.zeros(32)
W2 = rng.normal(size=(32, 10)) * 0.1
b2 = np.zeros(10)
for _ in range(300):
    Z1 = X_train @ W1 + b1
    H = np.maximum(0, Z1)
    P = softmax(H @ W2 + b2)
    D = (P - Y_train) / len(y_train)
    dH = D @ W2.T * (Z1 > 0)
    W2 = W2 - 0.5 * H.T @ D
    b2 = b2 - 0.5 * D.sum(axis=0)
    W1 = W1 - 0.5 * X_train.T @ dH
    b1 = b1 - 0.5 * dH.sum(axis=0)
pred = softmax(np.maximum(0, X_test @ W1 + b1) @ W2 + b2).argmax(axis=1)
acc_own = round((pred == y_test).mean(), 3)
```

### explain
Около 97 % — уже лучше логистической регрессии. Сеть, которую вы написали с нуля двадцатью строками numpy, распознаёт рукописные цифры.

## task: mlp | Шаг 5. MLP из sklearn | base

Обучите `MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0)` (признаки уже в диапазоне 0–1, масштаб не нужен) и сохраните `acc_mlp` (3 знака) и `proba` — матрицу вероятностей на тесте (`predict_proba`).

### starter
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import numpy as _np
from sklearn.datasets import load_digits as _ld
from sklearn.model_selection import train_test_split as _tts
from sklearn.neural_network import MLPClassifier as _MLP
dg = _ld(); a, b, c, d = _tts(dg.data / 16, dg.target, test_size=0.25, random_state=42, stratify=dg.target)
m = _MLP(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(a, c)
w = round((m.predict(b) == d).mean(), 3)
assert close(need('acc_mlp'), w, 0.003), f'acc_mlp = {need("acc_mlp")}, а нужно {w}: MLPClassifier без масштабирования, как в условии (признаки уже 0–1).'
pr = _np.asarray(need('proba'))
assert pr.shape == (len(d), 10) and _np.allclose(pr.sum(axis=1), 1), 'proba — вероятности формы (число тестовых картинок, 10), сумма по строке 1.'
```

### hint
`MLPClassifier` сам переключится на softmax для 10 классов. Признаки уже в шкале 0–1, поэтому модель обучайте без конвейера и без `StandardScaler` — иначе число не совпадёт с проверкой.

### hint
`model.predict_proba(X_test)`.

### solution
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(X_train, y_train)
acc_mlp = round((model.predict(X_test) == y_test).mean(), 3)
proba = model.predict_proba(X_test)
```

### explain
MLP — около 98 %, на уровне kNN. На этих данных сеть не даёт огромного выигрыша: картинки слишком простые. Зато у сети есть то, чего нет у kNN, — быстрый прогноз (не нужно сравнивать с каждой картинкой обучения) и вероятности, которые пригодятся в следующем шаге.

## task: errors | Шаг 6. Что путается и что показать оператору | plus

Для MLP из прошлого шага (в заготовке) постройте матрицу ошибок `cm = confusion_matrix(y_test, pred)`. Сохраните `top_pair` — пару `(настоящая цифра, предсказанная)` с наибольшим числом ошибок (кортеж из двух int; при равенстве — первая в порядке строк и столбцов) и `n_errors` — всего ошибок. Затем правило для оператора: ответы с максимальной вероятностью меньше 0.9 отправляются на ручную проверку. Сохраните `review_share` — долю таких ответов и `errors_caught` — долю всех ошибок модели, которые попали на проверку (3 знака).

### starter
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(X_train, y_train)
proba = model.predict_proba(X_test)
pred = proba.argmax(axis=1)

```

### check
```python
import numpy as _np
from sklearn.metrics import confusion_matrix as _cm
from sklearn.datasets import load_digits as _ld
from sklearn.model_selection import train_test_split as _tts
from sklearn.neural_network import MLPClassifier as _MLP
dg = _ld(); a, b, c, d = _tts(dg.data / 16, dg.target, test_size=0.25, random_state=42, stratify=dg.target)
pr = _MLP(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(a, c).predict_proba(b); pd_ = pr.argmax(1)
cm = _cm(d, pd_); off = cm.copy(); _np.fill_diagonal(off, 0)
i, j = _np.unravel_index(off.argmax(), off.shape)
assert tuple(int(v) for v in need('top_pair')) == (int(i), int(j)), f'top_pair = {need("top_pair")}, а нужно {(int(i), int(j))}.'
assert need('n_errors') == int((pd_ != d).sum()), f'n_errors = {need("n_errors")}.'
rev = pr.max(1) < 0.9; err = pd_ != d
assert close(need('review_share'), round(rev.mean(), 3), 0.002), f'review_share = {need("review_share")}.'
assert close(need('errors_caught'), round((rev & err).sum() / err.sum(), 3), 0.002), f'errors_caught = {need("errors_caught")}.'
```

### hint
Обнулите диагональ копии матрицы (`np.fill_diagonal`) и найдите позицию максимума: `np.unravel_index(m.argmax(), m.shape)`.

### hint
Неуверенные ответы: `proba.max(axis=1) < 0.9`; ошибки: `pred != y_test`.

### solution
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(X_train, y_train)
proba = model.predict_proba(X_test)
pred = proba.argmax(axis=1)

cm = confusion_matrix(y_test, pred)
off = cm.copy()
np.fill_diagonal(off, 0)
i, j = np.unravel_index(off.argmax(), off.shape)
top_pair = (int(i), int(j))
n_errors = int((pred != y_test).sum())
review = proba.max(axis=1) < 0.9
errors = pred != y_test
review_share = round(review.mean(), 3)
errors_caught = round((review & errors).sum() / errors.sum(), 3)
```

### explain
Ошибок единицы, и чаще всего модель путает похожие по форме цифры (например, 8 и 1 с наклоном). Правило «неуверенные ответы — оператору» отправляет на проверку около 8 % цифр и ловит три четверти ошибок модели. Для бизнеса это и есть продукт: не «модель без ошибок», а «оператор проверяет 8 % цифр вместо 100 %».

## task: shift | Шаг 7. Сдвиг на один пиксель | star

Убедитесь сами, что будет со сдвигом: сдвиньте тестовые картинки на 1 пиксель вправо (`np.roll(..., 1, axis=2)` по массиву формы (n, 8, 8), освободившийся левый столбец заполните нулями) и посчитайте долю правильных ответов MLP на сдвинутых картинках (`acc_shift`, 3 знака). Затем обучите тот же MLP на обучающих картинках **вместе** с их сдвинутыми копиями (вправо на 1 пиксель) и проверьте на сдвинутом тесте (`acc_aug`, 3 знака).

### starter
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(X_train, y_train)

def shift_right(X):
    imgs = np.roll(X.reshape(-1, 8, 8), 1, axis=2)
    imgs[:, :, 0] = 0
    return imgs.reshape(-1, 64)

```

### check
```python
import numpy as _np
from sklearn.datasets import load_digits as _ld
from sklearn.model_selection import train_test_split as _tts
from sklearn.neural_network import MLPClassifier as _MLP
dg = _ld(); a, b, c, d = _tts(dg.data / 16, dg.target, test_size=0.25, random_state=42, stratify=dg.target)
def _sh(X):
    im = _np.roll(X.reshape(-1, 8, 8), 1, axis=2); im[:, :, 0] = 0; return im.reshape(-1, 64)
m = _MLP(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(a, c)
s1 = round((m.predict(_sh(b)) == d).mean(), 3)
m2 = _MLP(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(_np.vstack([a, _sh(a)]), _np.concatenate([c, c]))
s2 = round((m2.predict(_sh(b)) == d).mean(), 3)
assert close(need('acc_shift'), s1, 0.003), f'acc_shift = {need("acc_shift")}, а нужно {s1}.'
assert close(need('acc_aug'), s2, 0.003), f'acc_aug = {need("acc_aug")}, а нужно {s2}. Обучение — на X_train и shift_right(X_train) вместе (np.vstack), ответы — y_train дважды.'
```

### hint
Сдвиг картинки 8 × 8 на пиксель вправо: `np.roll(img, 1, axis=1)` с обнулением первого столбца; для таблицы 64 признаков сначала `reshape(-1, 8, 8)`.

### hint
Сдвинутый тест — `shift_right(X_test)`. Обучение с копиями: `np.vstack([X_train, shift_right(X_train)])` и `np.concatenate([y_train, y_train])`.

### solution
```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

digits = load_digits()
X, y = digits.data / 16, digits.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(X_train, y_train)

def shift_right(X):
    imgs = np.roll(X.reshape(-1, 8, 8), 1, axis=2)
    imgs[:, :, 0] = 0
    return imgs.reshape(-1, 64)

acc_shift = round((model.predict(shift_right(X_test)) == y_test).mean(), 3)
aug = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0)
aug.fit(np.vstack([X_train, shift_right(X_train)]), np.concatenate([y_train, y_train]))
acc_aug = round((aug.predict(shift_right(X_test)) == y_test).mean(), 3)
```

### explain
Сдвиг на **один** пиксель — и точность падает с 98 % до 44 %. Для полносвязной сети пиксель (2, 3) и пиксель (2, 4) — совершенно разные признаки; она не знает, что картинка «та же, только левее». Обучение на сдвинутых копиях (**аугментация данных**) возвращает точность — но так пришлось бы перебрать все сдвиги, повороты и наклоны. Свёрточные сети (глава 14) встраивают «одинаково в любом месте картинки» прямо в архитектуру.

## Итог для руководителя отдела лояльности

::: figure nn-operator-flow
Правило из шага 6 на тестовых цифрах: ответы с максимальной вероятностью ниже 0.9 уходят оператору, остальные — в базу автоматически.
:::

> **Можно.** На учебном наборе рукописных цифр нейросеть распознаёт около 98 % цифр. Если отправлять оператору только ответы, в которых модель не уверена (около 8 % цифр), три четверти ошибок модели будут исправлены вручную, а остальное пройдёт автоматически.
>
> **Подводный камень.** Простая нейросеть чувствительна к положению цифры: если в анкете цифры чуть сдвинуты относительно «клеточки», качество падает вдвое. Для реального внедрения нужна свёрточная сеть и аккуратное вырезание каждой цифры из скана; обучать её надо на наших анкетах, а не на учебном наборе.
>
> **Следующий шаг.** Собрать 2–3 тысячи размеченных цифр из наших анкет (оператор и так их перебивает) и проверить модель на них.
