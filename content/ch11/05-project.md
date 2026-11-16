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
3. Простые модели: логистическая регрессия и kNN. Подумайте, почему kNN так хорош именно на картинках 8 × 8 и что это значит для выбора модели.
4. Своя сеть на numpy: 64 → 32 → 10, с softmax на выходе (урок «Softmax, выход под задачу и мини-батчи»; все формулы — в условии шага).
5. MLP из sklearn.
6. Матрица ошибок: что с чем путается; доля «неуверенных» ответов для проверки оператором.
7. Слабое место: сдвиг картинки на один пиксель.

Разбиение во всех шагах: `X = digits.data / 16`, `train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)`.

::: figure nn-digits-pipeline
Путь одной цифры через проект: картинка 8 × 8 разворачивается в 64 признака, сеть шага 4 выдаёт 10 вероятностей, а правило шага 6 решает, записать ответ в базу или отдать оператору. Картинка — четвёртая в наборе (цифра 3).
:::

::: quiz
Сеть хорошо распознаёт цифры на тесте, но на тех же картинках, сдвинутых на один пиксель, ошибается гораздо чаще. Что поможет?

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

## Проверьте порядок обновления весов

После шага «Своя сеть на numpy» разберите один шаг другой сети: два входа, два скрытых нейрона и один выход. В прямом проходе получены `H = [1, 2]`, ошибка выхода `D = 1`, оба скрытых нейрона активны. До шага веса выхода `W2 = [0.4, 0.8]`, шаг обучения 0,1. Коллега сначала выполнил `W2 = W2 - 0.1 * H * D`, а затем рассчитал ошибку скрытого слоя как `D * W2`.

Какие две величины получит коллега? Какие соответствуют прямому проходу и в каком порядке следует выполнять операции? Проверьте своё объяснение на числах, прежде чем открывать разбор.

<details><summary>Сверить один шаг</summary>

После обновления выйдет [0,3; 0,6]. Ошибке исходного прямого прохода соответствуют [0,4; 0,8]. Сначала вычислите оба градиента по тем весам, с которыми был выполнен прогноз. Затем обновите веса обоих слоёв.

</details>

## Перенос: новое размытие и очередь оператора

После шага 7 попробуйте необязательный перенос на размытие: сначала разберите одну уверенную ошибку на размеченной валидации, затем сохраните правило очереди на 37 **цифр** новой партии. Лишь после фиксации позиций открывайте её метки и считайте ошибки, оставшиеся без ручной проверки. В самостоятельной карточке предусмотрены два понятных правила: меньшая максимальная вероятность или меньший отрыв первого класса от второго. Оба используют прогнозы, а при равенстве — меньшую позицию, без обращения к итоговым меткам.

Отбор цифр — ещё не оценка целых телефонов. Для неё нужны связь цифр с одной анкетой, порядок позиций, правильный и распознанный номер целиком и результат работы оператора. Сохранённое до меток правило позволяет оценить его перенос, даже если итог неудобен для выбранной стратегии.

{{practice: blur-transfer}}

## task: look | Шаг 1. Классы и «средние» цифры | base

Сохраните `counts` — число картинок каждой цифры (массив длины 10), `balanced` — `True`, если самый редкий класс встречается не реже чем в 0.9 раза от самого частого. Нарисуйте «среднюю» картинку каждой цифры (среднее `digits.images` по картинкам этой цифры) — 10 панелей в один ряд, слева направо от 0 до 9. Заголовок каждой панели — соответствующая цифра. Подойдут `ax.imshow(...)` и `ax.matshow(...)`; для рисунка можно привести яркость из 0–16 в 0–1. Сохраните `mean_imgs` — массив формы (10, 8, 8) в исходной шкале 0–16.

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
import re as _re
from sklearn.datasets import load_digits as _ld
dg = _ld()
c = _np.bincount(dg.target)
assert _np.array_equal(_np.asarray(need('counts')),c), f'counts = {need("counts")}.'
assert need('balanced') == bool(c.min() >= 0.9 * c.max()), f'balanced = {need("balanced")}.'
expected = _np.array([dg.images[dg.target==k].mean(axis=0) for k in range(10)])
mi = _np.asarray(need('mean_imgs'))
assert mi.shape==(10,8,8) and _np.isfinite(mi).all() and _np.allclose(mi,expected), 'mean_imgs[k] — средняя картинка именно цифры k, для всех десяти цифр, в шкале 0–16.'
assert figs and len(figs[-1].axes)>=10, 'Нужны 10 панелей в один ряд. Пока рисунка с десятью панелями нет.'
panels = [a for a in figs[-1].axes if a.get_visible() and a.images]
assert len(panels)==10, f'Пустые панели: изображения найдены только в {len(panels)} из 10 панелей. Выведите среднюю картинку в каждой.'
panels.sort(key=lambda a:a.get_position().x0)
centers = [a.get_position().y0+a.get_position().height/2 for a in panels]
assert max(centers)-min(centers)<.1*min(a.get_position().height for a in panels), 'Расположите десять панелей в один ряд, от 0 до 9 слева направо.'
for k,ax in enumerate(panels):
    visible = [im for im in ax.images if im.get_visible() and (im.get_alpha() is None or _np.any(_np.asarray(im.get_alpha())>0))]
    assert len(visible)==1, f'Панель {k} слева: нужна одна видимая средняя картинка.'
    image = _np.asarray(visible[0].get_array())
    assert image.shape==(8,8) and _np.isfinite(image).all() and (_np.allclose(image,expected[k]) or _np.allclose(image,expected[k]/16)), f'Панель {k} слева: картинка перепутана или не является средним изображением цифры {k}. Сверьте класс и порядок панелей.'
    assert _re.findall(r'(?<!\d)\d(?!\d)',ax.get_title())==[str(k)], f'Панель {k} слева: подпишите изображённую цифру {k} в заголовке, сейчас {ax.get_title()!r}.'
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
Логистическая регрессия — 96 %, ближайшие соседи — больше 98 %. Картинки маленькие, чистые и выровненные по центру, поэтому даже «найди самую похожую картинку из обучения» работает отлично. Это важный ориентир: сеть должна быть не хуже kNN, иначе она не нужна. Забегая вперёд: MLP в шаге 5 даст почти столько же (0.982 против 0.984), и выбирать между ними придётся не по точности, а по тому, что ещё нужно бизнесу, — об этом итог проекта.

## task: own-net | Шаг 4. Своя сеть на numpy | base

Обучите сеть «64 → 32 (ReLU) → 10 (softmax)» на numpy: `rng = np.random.default_rng(0)`, `W1 = rng.normal(size=(64, 32)) * 0.1`, затем `W2 = rng.normal(size=(32, 10)) * 0.1`, смещения — нули, шаг 0.5, 300 шагов по всей обучающей выборке. Сохраните обученные веса и смещения `W1, b1, W2, b2`. Вычислите `own_proba` для тестовых картинок в их исходном порядке и `acc_own` — долю совпадений цифры с максимальной вероятностью и правильного ответа (3 знака).

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
_weights = [need(v) for v in ('W1','b1','W2','b2')]
_W1,_b1,_W2,_b2 = _weights
_manual = sm(_np.maximum(0,b@_W1+_b1)@_W2+_b2)
_got = _np.asarray(need('own_proba'))
assert _got.shape==(len(d),10) and _np.isfinite(_got).all() and (_got>=0).all() and _np.allclose(_got.sum(1),1), 'own_proba: допустимые вероятности десяти классов.'
assert _np.allclose(_got,_manual), 'own_proba должна получаться из переданных весов сети.'
assert close(need('acc_own'),round((_got.argmax(1)==d).mean(),3)), 'acc_own пересчитывается по собственным прогнозам.'

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
own_proba = softmax(np.maximum(0, X_test @ W1 + b1) @ W2 + b2)

```

### explain
Около 97 % — уже лучше логистической регрессии. Сеть, которую вы написали с нуля двадцатью строками numpy, распознаёт рукописные цифры.

## task: mlp | Шаг 5. MLP из sklearn | base

Обучите `MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0)` (признаки уже в диапазоне 0–1, масштаб не нужен) и сохраните `acc_mlp` (3 знака) и `proba` — матрицу вероятностей на тесте (`predict_proba`).

Оставьте обученный классификатор в `model`, а вероятности его десяти классов в порядке картинок `X_test` — в `proba`. Из этой же матрицы вычислите точность.

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
_submitted = need('model')
assert _np.isfinite(pr).all() and (pr >= 0).all() and (pr <= 1).all(), 'Вероятности должны быть конечными числами от0 до1.'
assert _np.allclose(pr,_submitted.predict_proba(b)), 'proba не соответствует переданной model и порядку тестовых картинок.'
assert close(need('acc_mlp'),round((pr.argmax(1)==d).mean(),3)), 'accuracy не соответствует argmax ваших вероятностей.'

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

Теперь у оператора есть ровно 37 мест. Сравните MLP с `KNeighborsClassifier(n_neighbors=3)` на тех же обучающих и тестовых строках. Для обеих моделей возьмите 37 картинок с наименьшей максимальной вероятностью. При равенстве первой идёт меньшая позиция в тесте. Сохраните позиции в `queue_mlp` и `queue_knn`, а число ошибочных цифр **вне** каждой очереди — в `missed_mlp` и `missed_knn`.

Одна анкета может содержать несколько сомнительных цифр. Напишите `operator_queue(phone_ids, digit_review)`: для параллельных списков ID и признаков ручной проверки верните каждый отмеченный ID один раз, в порядке первого отмеченного появления. На трёх цифрах анкет A, A, B с флагами True, True, False оператор получит одну карточку A.

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
_submitted_cm = _np.asarray(need('cm'))
assert _submitted_cm.shape==(10,10) and _np.array_equal(_submitted_cm,cm), 'cm должна содержать реальные числа ошибок и правильных ответов, а не нулевую матрицу.'
from sklearn.neighbors import KNeighborsClassifier as _KNN
_knn = _KNN(n_neighbors=3).fit(a,c).predict_proba(b)
_qm = _np.argsort(pr.max(1),kind='stable')[:37]
_qk = _np.argsort(_knn.max(1),kind='stable')[:37]
assert list(need('queue_mlp'))==_qm.tolist() and list(need('queue_knn'))==_qk.tolist(), 'Обе очереди: ровно37 цифр, сначала меньшая уверенность, при ничьей меньшая позиция в тесте.'
assert need('missed_mlp')==int(_np.delete(pr.argmax(1)!=d,_qm).sum()), 'missed_mlp — ошибки среди автоматически принятых.'
assert need('missed_knn')==int(_np.delete(_knn.argmax(1)!=d,_qk).sum()), 'missed_knn — ошибки среди автоматически принятых.'
_cardfn = need('operator_queue')
assert list(_cardfn(['A','A','B'],[True,True,False]))==['A'], 'Две сомнительные цифры одного телефона дают одну карточку.'
assert list(_cardfn(['A','A','B'],[True,False,True]))==['A','B'], 'Сомнительные цифры двух телефонов дают две карточки.'

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
from sklearn.neighbors import KNeighborsClassifier
knn_proba = KNeighborsClassifier(n_neighbors=3).fit(X_train,y_train).predict_proba(X_test)
queue_mlp = np.argsort(proba.max(1),kind='stable')[:37].tolist()
queue_knn = np.argsort(knn_proba.max(1),kind='stable')[:37].tolist()
missed_mlp = int(np.delete(pred!=y_test,queue_mlp).sum())
missed_knn = int(np.delete(knn_proba.argmax(1)!=y_test,queue_knn).sum())
def operator_queue(phone_ids, digit_review):
    return list(dict.fromkeys(phone for phone, review in zip(phone_ids,digit_review) if review))

```

### explain
Ошибок единицы, и чаще всего модель путает похожие по форме цифры (например, 8 и 1 с наклоном). Правило «неуверенные ответы — оператору» отправляет на проверку около 8 % цифр и ловит три четверти ошибок модели. Это нагрузка **по отдельным цифрам**; качество ручного исправления ещё предстоит измерить. Набор load_digits не содержит ID анкет/позиции цифр в телефоне и не определяет долю целиком верных телефонов или карточек оператора.

## task: shift | Шаг 7. Сдвиг на один пиксель | star

Зарезервируйте финальный набор из заготовки. Из оставшихся 1347 картинок выделите четверть на валидацию (`random_state=7, stratify=y_train`). На остальных обучите два одинаковых MLP из шага 5 — обычный и с дополнительными копиями, сдвинутыми вправо на пиксель. Освободившийся край заполните нулями.

1. На **валидации** со сдвигом вправо запишите точности `acc_shift` и `acc_aug` (три знака). В `defense` укажите `"augment"`, если точность с копиями выше, иначе `"plain"`.
2. На той же валидации найдите уверенную ошибку обычной сети. В `example_idx` укажите позицию в валидации, где модель ошиблась с уверенностью не ниже 0.9. Покажите картинку и подпишите истинную цифру, прогноз и вероятность.
3. Переобучите выбранную процедуру на всех 1347 картинках. Для проверки другого искажения сдвиньте только финальные картинки **влево** на пиксель и заполните правый край нулями. В `holdout_accuracy` запишите точность с тремя знаками. Объясните, переносится ли защита на другой сдвиг.

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

X_fit, X_val, y_fit, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=7, stratify=y_train)

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
fit, val, yf, yv = _tts(a, c, test_size=.25, random_state=7, stratify=c)
def _fit(x, labels, aug=False):
    if aug:
        x, labels = _np.vstack([x, _sh(x)]), _np.tile(labels, 2)
    return _MLP(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(x, labels)
p = _fit(fit, yf).predict_proba(_sh(val))
q = _fit(fit, yf, True).predict(_sh(val))
s1, s2 = (p.argmax(1)==yv).mean(), (q==yv).mean()
assert close(need('acc_shift'), round(s1,3), .00051) and close(need('acc_aug'),round(s2,3),.00051), 'Сравните обе версии на одной валидации со сдвигом вправо.'
mode = 'augment' if s2 > s1 else 'plain'
assert need('defense') == mode, 'Защита выбирается до просмотра отдельного искажения.'
idx = need('example_idx')
assert 0 <= idx < len(val) and p[idx].argmax() != yv[idx] and p[idx].max() >= .9, 'Покажите уверенную ошибку на валидации.'
ax = ax_of()
assert len(ax.images) and _np.allclose(_np.asarray(ax.images[-1].get_array()), _sh(val)[idx].reshape(8,8)), 'Покажите сдвинутую картинку выбранной ошибки.'
left = _np.zeros_like(b.reshape(-1,8,8))
left[:, :, :-1] = b.reshape(-1,8,8)[:, :, 1:]
expected = (_fit(a, c, mode == 'augment').predict(left.reshape(-1,64)) == d).mean()
assert close(need('holdout_accuracy'), round(expected,3), .00051), 'Проверьте выбранную процедуру на новых финальных картинках со сдвигом влево.'

```

### hint
Сдвиг картинки 8 × 8 на пиксель вправо: `np.roll(img, 1, axis=1)` с обнулением первого столбца; для таблицы 64 признаков сначала `reshape(-1, 8, 8)`.

### hint
Для искажённой валидации получите вероятности обычной сети; маску ошибок и уверенность можно совместить. Финальный сдвиг влево копирует столбцы 1…7 в позиции 0…6 новой картинки.

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


X_fit, X_val, y_fit, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=7, stratify=y_train)
def fit_model(rows, labels, augment=False):
    if augment:
        rows, labels = np.vstack([rows, shift_right(rows)]), np.tile(labels, 2)
    return MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(rows, labels)

right = shift_right(X_val)
plain = fit_model(X_fit, y_fit).predict_proba(right)
augmented = fit_model(X_fit, y_fit, True).predict(right)
acc_shift = round((plain.argmax(1) == y_val).mean(), 3)
acc_aug = round((augmented == y_val).mean(), 3)
defense = "augment" if acc_aug > acc_shift else "plain"
example_idx = int(np.flatnonzero((plain.argmax(1) != y_val) & (plain.max(1) >= .9))[0])
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.imshow(right[example_idx].reshape(8,8), cmap="gray")
ax.set_title(f"Цифра {y_val[example_idx]}, прогноз {plain[example_idx].argmax()}, p={plain[example_idx].max():.2f}")
final = fit_model(X_train, y_train, defense == "augment")
left = np.zeros_like(X_test.reshape(-1,8,8))
left[:, :, :-1] = X_test.reshape(-1,8,8)[:, :, 1:]
holdout_accuracy = round((final.predict(left.reshape(-1,64)) == y_test).mean(), 3)
print(acc_shift, acc_aug, defense, holdout_accuracy)
```

### explain
Прочитайте три точности отдельно. Улучшение на знакомом направлении можно проверить на другом искажении только после выбора защиты. Сохраните уверенную ошибку в письме оператору как пример случая, который порог вероятности способен пропустить.

## task: blur-transfer | Перенос: размытие и 37 мест у оператора | star

В новой партии цифры размыты гауссовым фильтром (`sigma=0.65`, нулевой край). Обученная сеть уже готова. На `validation` доступны изображения, вероятности и метки, на `blind` пока только изображения и вероятности. Позиции в каждой партии отсчитываются с нуля.

**До открытия меток.** Какую ошибку модель может допустить с высокой уверенностью и оставить вне очереди из 37 цифр?

1. Найдите в `validation` любую ошибку с уверенностью от 0.90 включительно. В `example` запишите `position`, `truth`, `prediction`, `confidence` и `observation` — что на изображении затрудняет чтение цифры.
2. Покажите это изображение. Подпишите четыре величины, например `Позиция …; истина …; прогноз …; p=…` или `position=…; truth=…; prediction=…; confidence=…`. Вероятность можно округлить до двух или трёх знаков либо показать в процентах.
3. Выберите `rule_name`. При `"confidence"` первыми идут цифры с меньшей максимальной вероятностью, при `"margin"` — с меньшей разностью двух наибольших вероятностей. При равенстве берите меньшую позицию. Запишите причину в `rule_reason`, затем сохраните в `queue` ровно 37 разных позиций из `blind` в выбранном порядке.
4. Откройте `final_labels = open_blur_labels(example, rule_name, queue, rule_reason)`. Функция фиксирует правило и очередь до выдачи меток. На той же очереди посчитайте `total_errors`, `caught_errors` и `missed_errors`. Назовите одну позицию с ошибкой вне очереди, если такая есть.
5. Сохраните `evaluation_unit="digit"`, `phone_accuracy=None` и `phone_note`. Какие данные о целых номерах и результате работы оператора нужны для оценки? Автопроверка сверяет единицу и расчёты. Преподаватель может обсудить с вами описание картинки и этот вывод.

### setup
```python
import numpy as np
import matplotlib.pyplot as plt
import re as _blur_re
from scipy.ndimage import gaussian_filter
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

def _prepare_blur_transfer():
    digits = load_digits()
    ids = np.arange(len(digits.target))
    development, holdout = train_test_split(ids, test_size=.25, random_state=42, stratify=digits.target)
    fit, val = train_test_split(development, test_size=.25, random_state=7, stratify=digits.target[development])
    def batch(train, other):
        model = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=500, random_state=0).fit(digits.data[train]/16, digits.target[train])
        images = gaussian_filter(digits.images[other]/16, sigma=(0,.65,.65), mode="constant", cval=0)
        return images, model.predict_proba(images.reshape(-1,64))
    val_images, val_proba = batch(fit,val)
    blind_images, blind_proba = batch(development,holdout)
    val_target, holdout_target = digits.target[val].copy(), digits.target[holdout].copy()
    state = {}
    def ordered_queue(rule, proba):
        top = np.sort(proba,axis=1)
        score = top[:,-1] if rule=="confidence" else top[:,-1]-top[:,-2]
        return np.lexsort((np.arange(len(proba)),score))[:37]
    def open_labels(example, rule_name, queue, reason):
        assert isinstance(example,dict), 'До меток сохраните example — словарь с разбором уверенной ошибки валидации.'
        for name in ('position','truth','prediction','confidence','observation'):
            assert name in example, f'В example нет поля {name}.'
        i=example['position']
        assert isinstance(i,(int,np.integer)) and 0<=i<len(val_target), 'position — целая позиция внутри validation.'
        pred=int(val_proba[i].argmax()); confidence=float(val_proba[i].max())
        assert pred!=val_target[i] and confidence>=.9, 'Выберите уверенную ошибку на валидации, а не правильный или неуверенный ответ.'
        assert example['truth']==val_target[i] and example['prediction']==pred and np.isclose(example['confidence'],confidence,rtol=0,atol=.0051), 'В example сверьте истинную цифру, прогноз и уверенность выбранной позиции.'
        assert isinstance(example['observation'],str) and len(example['observation'].strip())>=15, 'Добавьте своё наблюдение о видимом затруднении чтения; не ограничивайтесь номером класса.'
        image_axes=[ax for number in plt.get_fignums() for ax in plt.figure(number).axes if any(im.get_visible() and np.shape(im.get_array())==(8,8) and np.allclose(im.get_array(),val_images[i]) for im in ax.images)]
        assert image_axes, 'До открытия меток покажите размытое изображение выбранной ошибки валидации.'
        def caption_error(title):
            # Match named values, rather than one literal Russian sentence.
            text=title.casefold().replace("ё","е")
            fields=[('position/позиция',r'position|позиция|id',i,0),
                    ('truth/истина',r'truth|true|истина|(?:истинная|верная)\s+цифра',int(val_target[i]),0),
                    ('prediction/прогноз',r'prediction|pred|прогноз',pred,0),
                    ('confidence/уверенность',r'confidence|уверенность|вероятность|p',confidence,.0051)]
            number=r'([+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:e[+-]?\d+)?)(\s*%)?'
            for name,aliases,expected,tolerance in fields:
                matches=_blur_re.findall(r'(?<!\w)(?:'+aliases+r')(?!\w)\s*[:=]?\s*'+number,text)
                if len(matches)!=1:
                    return f'поле {name} отсутствует или указано неоднозначно'
                value=float(matches[0][0].replace(",","."))
                if matches[0][1]:
                    if name!='confidence/уверенность':return f'поле {name} не выражается в процентах'
                    value/=100
                if not np.isfinite(value) or not np.isclose(value,expected,rtol=0,atol=tolerance):
                    return f'{name}={value:g}, а у выбранного примера {expected:g}'
            return None
        caption_errors=[caption_error(ax.get_title()) for ax in image_axes]
        assert any(error is None for error in caption_errors), 'Подпись выбранного примера: '+caption_errors[0]+'. Используйте русские или английские названия четырёх полей: позиция, истина, прогноз, уверенность.'
        assert rule_name in ('confidence','margin'), 'rule_name — confidence или margin; правило фиксируется до меток.'
        assert isinstance(reason,str) and len(reason.strip())>=15, 'Запишите rule_reason: почему выбрали это правило очереди.'
        q=np.asarray(queue)
        assert q.shape==(37,) and np.issubdtype(q.dtype,np.integer) and len(np.unique(q))==37 and (q>=0).all() and (q<len(holdout)).all(), 'queue — ровно 37 разных целых позиций второй партии.'
        expected=ordered_queue(rule_name,blind_proba)
        assert np.array_equal(q,expected), 'Очередь не соответствует записанному правилу. Сначала меньший score, при равенстве меньшая позиция; используйте blind.proba, без меток.'
        if state:
            assert state['rule']==rule_name and state['queue']==tuple(int(v) for v in q), 'Метки уже открыты: правило и очередь этой попытки зафиксированы.'
        else:
            state.update(rule=rule_name, queue=tuple(int(v) for v in q), reason=reason, example=dict(example))
        return holdout_target.copy()
    def assessment_after_open():
        assert state, "Сначала зафиксируйте пример, правило и очередь через open_blur_labels."
        return holdout_target.copy(), blind_proba.copy()
    # Labels stay in the closure until the queue has been saved.
    return dict(images=val_images,proba=val_proba,target=val_target), dict(images=blind_images,proba=blind_proba), open_labels, state, assessment_after_open
validation, blind, open_blur_labels, _blur_state, _blur_assessment = _prepare_blur_transfer()
del _prepare_blur_transfer
```

### starter
```python
# Готово: validation (с target), blind (без target), np, plt, open_blur_labels.
# Первый запуск: осмотрите валидацию, сохраните example, правило и очередь.
val_pred = validation["proba"].argmax(axis=1)
val_confidence = validation["proba"].max(axis=1)
print("Размер валидации:", len(val_pred), "вторая партия:", len(blind["proba"]))
# После своей записи правила:
# final_labels = open_blur_labels(example, rule_name, queue, rule_reason)
# Затем оцените пропуски и запишите ограничение для целых номеров.
```

### check
```python
import numpy as _np
assert _blur_state, 'Итоговые метки ещё не открыты. Сначала разберите уверенную ошибку, сохраните правило/очередь, затем вызовите open_blur_labels.'
assert need('rule_name')==_blur_state['rule'] and list(need('queue'))==list(_blur_state['queue']), 'После открытия меток используйте сохранённые правило и очередь; не подбирайте их по итоговым ошибкам.'
_blur_labels,_blur_proba=_blur_assessment()
assert _np.array_equal(need('final_labels'),_blur_labels), 'final_labels — метки, возвращённые open_blur_labels после фиксации очереди.'
errors=_blur_proba.argmax(1)!=_blur_labels
caught=int(errors[list(_blur_state['queue'])].sum())
for name,expected in [('total_errors',int(errors.sum())),('caught_errors',caught),('missed_errors',int(errors.sum())-caught)]:
    assert need(name)==expected, f'{name}: сверьте ошибки по предсказаниям второй партии и сохранённым 37 позициям. Ошибки вне очереди — все ошибки минус пойманные.'
assert need('evaluation_unit')=='digit' and need('phone_accuracy') is None, 'Единица этой оценки — digit. Доля верных целых номеров здесь не измерена: phone_accuracy=None.'
assert isinstance(need('phone_note'),str) and len(need('phone_note').strip())>=30, 'Запишите ограничение для целых номеров и нужные связанные данные. Содержательность этого объяснения обсуждают вручную.'
```

### hint
Сначала объедините маску `val_pred != validation["target"]` с `val_confidence >= .90`. Любая подходящая позиция допустима. Подпись: `f"Позиция {i}; истина {truth}; прогноз {pred}; p={confidence:.2f}"`.

### hint
Для margin отсортируйте вероятности в каждой строке: `top = np.sort(proba, axis=1)`, затем `score = top[:, -1] - top[:, -2]`. `np.argsort(score, kind="stable")[:37]` сохраняет порядок позиций при равенстве.

### solution
```python
p=validation["proba"]
pred=p.argmax(1); confidence=p.max(1)
i=int(np.flatnonzero((pred!=validation["target"]) & (confidence>=.9))[0])
example=dict(position=i,truth=int(validation["target"][i]),prediction=int(pred[i]),confidence=float(confidence[i]),observation="Размытие сгладило различия штрихов; сравню замкнутые области и края с прогнозом.")
fig,ax=plt.subplots()
ax.imshow(validation["images"][i],cmap="gray")
ax.set_title(f"Позиция {i}; истина {example['truth']}; прогноз {example['prediction']}; p={example['confidence']:.2f}")
rule_name="margin"
rule_reason="Отправлю оператору случаи, где две наиболее вероятные цифры близки; при равенстве сохраню порядок позиций."
top=np.sort(blind["proba"],axis=1)
score=top[:,-1]-top[:,-2]
queue=np.argsort(score,kind="stable")[:37].tolist()
final_labels=open_blur_labels(example,rule_name,queue,rule_reason)
errors=blind["proba"].argmax(1)!=final_labels
total_errors=int(errors.sum())
caught_errors=int(errors[queue].sum())
missed_errors=total_errors-caught_errors
evaluation_unit="digit"
phone_accuracy=None
phone_note="Здесь оценены отдельные цифры. Нужны ID анкеты, порядок цифр внутри телефона, эталон и распознанный целый номер, а также фактические исправления оператора; по ним оценим номера и нагрузку."
print("Ошибки вне сохранённой очереди:",missed_errors)
```

### explain
Сверьте три числа: все ошибки равны пойманным плюс оставшимся вне очереди. Очередь фиксированного размера не гарантирует, что остальные ответы верны: уверенная ошибка валидации показывает этот риск. Ошибки по отдельным цифрам нельзя напрямую переводить в долю верных телефонов. Для следующего пилота нужны связанные цифры одного номера и фактический результат проверки человеком.

Нейтральная обратная связь после первой попытки: «Как вы отдельно проверили, какую ошибку очередь поймала и какую оставила? Были ли метки второй партии доступны при записи правила?»

## Итог для руководителя отдела лояльности

::: figure nn-operator-flow
Правило из шага 6 на тестовых цифрах: ответы с максимальной вероятностью ниже 0.9 уходят оператору, остальные — в базу автоматически.
:::

> **Можно.** На учебном наборе рукописных цифр нейросеть распознаёт около 98 % цифр. Если отправлять оператору только ответы, в которых модель не уверена (около 8 % цифр), три четверти ошибок модели попадут на ручную проверку; исправление оператором остаётся предположением, а остальное пройдёт автоматически.
>
> **Почему нейросеть, а не метод попроще.** Метод ближайших соседей («найди самую похожую картинку») на этих данных так же точен — 98.4 % против 98.2 % у сети. Для сравнения ручной очереди задайте обеим моделям одинаковое целое число мест. Сортируйте по уверенности по возрастанию, а при равенстве — по ID изображения; это особенно важно при дискретных оценках kNN. Покажите число ошибок в очереди и в автоматической части. Одинаковый порог при разных нагрузках не выбирает победителя.
>
> **Подводный камень.** Простая нейросеть чувствительна к положению цифры: если в анкете цифры чуть сдвинуты относительно «клеточки», качество падает вдвое. Для реального внедрения нужна свёрточная сеть и аккуратное вырезание каждой цифры из скана; обучать её надо на наших анкетах, а не на учебном наборе.
>
> **Следующий шаг.** Собрать 2–3 тысячи размеченных цифр из наших анкет (оператор и так их перебивает) и проверить модель на них.
