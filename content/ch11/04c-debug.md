---
title: "Dropout, BatchNorm и smoke-test"
lead: "Три приёма, без которых не обходится настоящая сеть: dropout против переобучения, BatchNorm — нормировка внутри сети, и smoke-test — минутная проверка, которая ловит ошибку в цикле обучения до многочасового запуска на видеокарте."
files: [guests_churn.csv]
recap:
  - "Dropout на обучении случайно выключает долю нейронов — регуляризация против переобучения."
  - "BatchNorm нормирует выход каждого нейрона по батчу и возвращает масштаб обучаемыми γ и β; на прогнозе (`model.eval()`) использует скользящие средние, накопленные при обучении."
  - "Модель и каждый батч — на одно устройство: `.to(device)`. Перед долгим обучением — smoke-test: формы и nan, стартовая потеря ≈ ln 2 (ln K), переобучение на 16–32 объектах до потери около нуля."
---

Продолжаем работать с сетью из урока «PyTorch: то же самое, но в промышленном масштабе». Код на PyTorch, как и там, — для своего блокнота; задачи — на numpy.

## Dropout

Кроме `alpha` и ранней остановки из урока «Нейросеть в sklearn: MLP», с переобучением в сетях борются ещё одним способом — **dropout**: на каждом шаге обучения случайно «выключать» долю нейронов (обнулять их выход), а оставшиеся масштабировать, чтобы среднее не изменилось. Сеть не может полагаться на конкретный нейрон и учится более устойчивым признакам. На прогнозе dropout не применяется.

::: tip Аналогия
Это как смена в кофейне, где каждый день случайный бариста берёт выходной: команда не может держаться на одном незаменимом человеке, и каждый учится подхватывать чужие участки. В день ревизии — на прогнозе — выходят все. Хромает аналогия в одном: нейроны ничего не «подхватывают» сознательно — выходы оставшихся просто умножают на поправочный множитель, чтобы средний сигнал не изменился, а устойчивость возникает сама, потому что веса учатся без опоры на какой-то один нейрон.
:::

```python static
model = nn.Sequential(
    nn.Linear(64, 128), nn.ReLU(), nn.Dropout(0.3),
    nn.Linear(128, 10),
)
model.train()   # режим обучения: dropout включён
model.eval()    # режим прогноза: dropout выключен
```

**Что здесь происходит:**

- `nn.Dropout(0.3)` — на каждом шаге обучения обнуляет случайные 30 % выходов предыдущего слоя, а оставшиеся умножает на 1 / 0.7, чтобы среднее не изменилось.
- `model.train()` и `model.eval()` переключают режим всех слоёв сети сразу.

Переключение `train()` / `eval()` — обязательная часть кода на PyTorch: забыли `eval()` — прогнозы получаются случайными и хуже, чем могли бы.

::: figure nn-dropout
На обучении на каждом шаге выключается свой случайный набор нейронов (здесь 3 из 10), выходы остальных умножаются на 1 / 0.7. На прогнозе работают все нейроны без множителя. Какие именно нейроны выключены — условно.
:::

::: warn Типичные ошибки
- **Dropout на выходном слое.** `nn.Dropout` после последнего `nn.Linear` случайно обнуляет сам прогноз. Его ставят между скрытыми слоями, после активации.
- **Слишком большая доля.** При `p = 0.8` на каждом шаге остаётся пятая часть нейронов, и маленькая сеть на табличных данных просто недообучается. Обычный диапазон — 0.1…0.5; подбирают по валидации, как `alpha`.
:::

{{practice: dropout}}

## BatchNorm: нормировка внутри сети

**Зачем.** Признаки перед сетью мы масштабируем (`StandardScaler`, глава 7), иначе спуск идёт плохо. Но после первого слоя масштаб снова «плывёт»: выходы нейронов могут быть в сотнях у одного и в сотых у другого, и он меняется по мере обучения весов предыдущих слоёв. **Batch normalization** (BatchNorm, BN) — слой, который нормирует выходы каждого нейрона прямо внутри сети, на каждом батче. С ним глубокие сети учатся быстрее и меньше зависят от удачного шага `lr` и инициализации.

::: tip Аналогия
Это как приводить отчёты всех кофеен к общей шкале перед общим совещанием: выручку Перми и Казани показывают не в рублях, а в «насколько выше или ниже среднего по сети», и уже потом каждый руководитель может домножить на свой коэффициент. Хромает аналогия в одном: сеть сама учится, какой коэффициент и сдвиг вернуть каждому нейрону (γ и β ниже), а среднее берётся не по всей сети, а только по текущему батчу.
:::

**Игрушечный пример руками.** Один нейрон, батч из четырёх гостей, выходы 2, 4, 6 и 8:

1. среднее батча $\mu = (2 + 4 + 6 + 8) / 4 = 5$;
2. дисперсия $\sigma^2 = (9 + 1 + 1 + 9) / 4 = 5$, отклонение $\sqrt{5} \approx 2.236$;
3. нормировка: $(2 - 5) / 2.236 = -1.342$, затем $-0.447$, $0.447$, $1.342$ — среднее 0, отклонение 1;
4. обучаемые масштаб $\gamma = 2$ и сдвиг $\beta = 1$: $2 \cdot (-1.342) + 1 = -1.683$, затем 0.106, 1.894, 3.683.

$$
\hat{x} = \frac{x - \mu_B}{\sqrt{\sigma_B^2 + \varepsilon}}, \qquad y = \gamma \cdot \hat{x} + \beta
$$

Здесь $x$ — выход нейрона у объекта батча, $\mu_B$ и $\sigma_B^2$ — среднее и дисперсия этого нейрона по батчу, $\varepsilon$ — крошечное число (обычно $10^{-5}$), чтобы не делить на ноль, $\gamma$ и $\beta$ — обучаемые параметры слоя (по паре на нейрон): сеть может вернуть любой нужный ей масштаб, в том числе отменить нормировку.

**Обучение и прогноз ведут себя по-разному.** На прогнозе батча может не быть — например, оценить надо одного гостя. Поэтому во время обучения BN копит **скользящие** среднее и дисперсию: после каждого батча `running = 0.9 · running + 0.1 · батч` (0.1 называется momentum), а в режиме прогноза нормирует ими.

::: figure nn-batchnorm
Пример с четырьмя гостями из списка выше: нормировка по батчу, затем обучаемые γ и β. Внизу — чем режимы обучения и прогноза отличаются для этого слоя.
:::

Посмотрим на признаках гостей:

```python
import numpy as np
import pandas as pd

g = pd.read_csv("guests_churn.csv")
X = g[["tenure_months", "visits_90d", "days_since_last", "complaints"]].to_numpy(float)

def batchnorm_train(Xb, gamma, beta, run_mean, run_var, momentum=0.1, eps=1e-5):
    mu, var = Xb.mean(axis=0), Xb.var(axis=0)             # статистики ЭТОГО батча
    out = gamma * (Xb - mu) / np.sqrt(var + eps) + beta
    run_mean = (1 - momentum) * run_mean + momentum * mu   # скользящие средние — на будущее
    run_var = (1 - momentum) * run_var + momentum * var
    return out, run_mean, run_var

def batchnorm_eval(X, gamma, beta, run_mean, run_var, eps=1e-5):
    return gamma * (X - run_mean) / np.sqrt(run_var + eps) + beta

k = X.shape[1]
gamma, beta = np.ones(k), np.zeros(k)                      # обучаемые: масштаб и сдвиг
run_mean, run_var = np.zeros(k), np.ones(k)
order = np.random.default_rng(0).permutation(len(X))
for start in range(0, len(X), 64):                         # одна эпоха батчами по 64
    out, run_mean, run_var = batchnorm_train(X[order[start:start + 64]], gamma, beta, run_mean, run_var)

print("до BN, отклонения столбцов:", X.std(axis=0).round(1))
print("после BN, последний батч: среднее", out.mean(axis=0).round(2) + 0.0, "отклонение", out.std(axis=0).round(2))
print("скользящее среднее:", run_mean.round(1))
print("среднее по всем:   ", X.mean(axis=0).round(1))
one = batchnorm_eval(X[:1], gamma, beta, run_mean, run_var)
print("гость G-10001 в режиме прогноза:", one.round(2))
```

**Что здесь происходит:**

- `batchnorm_train` нормирует по статистикам текущего батча (`axis=0` — по объектам, отдельно для каждого столбца) и обновляет скользящие средние.
- `batchnorm_eval` не смотрит на батч вообще: только на `run_mean` и `run_var`. Поэтому один гость нормируется так же, как в составе любого батча.
- Цикл по батчам по 64 — одна эпоха (38 батчей).

**Как читать результат:** до BN разброс столбцов — от 0.3 (жалобы) до 35.6 (дней с последнего визита). После BN у батча среднее 0 и отклонение 1 по каждому столбцу. Скользящее среднее за эпоху почти догнало среднее по всем гостям (17.8 против 18.0 месяцев стажа): от стартового нуля осталось $0.9^{38} \approx 2\%$, плюс шум последних батчей. Гостю G-10001 в режиме прогноза достались числа от −0.27 до −0.46 — по всем четырём признакам он чуть ниже среднего, но в пределах полуотклонения.

В PyTorch BN ставят между линейным слоем и активацией:

```python static
model = nn.Sequential(
    nn.Linear(8, 32), nn.BatchNorm1d(32), nn.ReLU(),
    nn.Linear(32, 1),
)
bn = nn.BatchNorm1d(1)
x = torch.tensor([[2.0], [4.0], [6.0], [8.0]])
bn.train(); print(bn(x).detach().squeeze())       # [-1.342, -0.447, 0.447, 1.342]
print(bn.running_mean, bn.running_var)           # tensor([0.5000]) tensor([1.5667])
bn.eval();  print(bn(x).detach().squeeze())       # [1.198, 2.796, 4.394, 5.992]
```

После одного батча скользящее среднее — только $0.9 \cdot 0 + 0.1 \cdot 5 = 0.5$, и в режиме `eval()` числа получаются совсем другими. Поэтому BN в режиме прогноза честен только после того, как сеть обучилась на многих батчах.

::: deep Тонкости BatchNorm в PyTorch
- **Дисперсия с делением на $n - 1$.** В `running_var` PyTorch кладёт дисперсию батча с делением на $n - 1$, а не на $n$: $0.9 \cdot 1 + 0.1 \cdot 20/3 = 1.5667$ вместо $0.9 + 0.1 \cdot 5 = 1.4$. На батчах из десятков объектов разница незаметна.
- **Очень маленькие батчи (2–8 объектов).** Среднее и дисперсия по батчу шумные, BN мешает больше, чем помогает. Для таких случаев есть `nn.LayerNorm` — нормировка по нейронам одного объекта, без батча.
:::

::: quiz
Сеть с BatchNorm обучили, а при прогнозе для одного гостя в режиме `model.train()` PyTorch упал с ошибкой `Expected more than 1 value per channel when training`. В чём дело?

- [x] В режиме обучения BN нормирует по статистикам батча, а по одному объекту дисперсию не посчитать; на прогнозе нужно `model.eval()` — тогда BN берёт накопленные скользящие средние
  > Именно поэтому у BN две статистики: батчевая — для обучения, скользящая — для прогноза.
- [ ] BatchNorm вообще нельзя использовать для прогноза по одному объекту — нужно собрать батч
  > Можно: в режиме `eval()` слой нормирует скользящими средними и с батчем из одного объекта работает.
- [ ] Гость пришёл с пропусками в признаках
  > Пропуски дали бы `nan` в выходе, а не эту ошибку. Сообщение прямо говорит про «один объект на канал в режиме обучения».
- [ ] У гостя другие признаки, чем при обучении, — нужно заново обучить BN
  > BN не обучают отдельно; его γ и β обучаются вместе с сетью, а скользящие средние копятся сами при обучении.
:::

::: warn Типичные ошибки
- **Забыли `model.eval()`.** BN в режиме обучения нормирует по текущему батчу: прогноз гостя зависит от того, с кем он попал в батч, и меняется от запуска к запуску. Плюс скользящие средние продолжают «уезжать» на тестовых данных.
- **Батч из одного объекта при обучении.** Падает `ValueError: Expected more than 1 value per channel when training`. Чаще всего это последний короткий батч эпохи: у `DataLoader` есть `drop_last=True`.
:::

{{practice: batchnorm}}

## Видеокарта и smoke-test

**Зачем.** Сеть для распознавания анкет или текстов отзывов «Зерна» на процессоре может учиться часами. Видеокарта (GPU) считает умножения матриц параллельно и ускоряет это в разы, а иногда в десятки раз. Но долгий запуск страшен другим: через три часа выясняется, что в цикле была ошибка. Поэтому перед любым долгим обучением делают **smoke-test** — «дымовую проверку»: короткий прогон, который за минуту ловит грубые ошибки.

::: tip Аналогия
Название пришло от электроники: собрал плату, включил — если не задымилось, можно проверять всерьёз. В кофейне то же самое перед открытием новой точки: варят первые десять чашек для своих, а не сразу встречают очередь. Хромает аналогия в одном: «не задымилось» ещё не значит «работает правильно» — smoke-test ловит поломки, а качество модели проверяет только валидация.
:::

**Как перенести вычисления на видеокарту.** В PyTorch и модель, и каждый батч явно отправляют на одно и то же устройство:

```python static
import torch

if torch.cuda.is_available():
    device = "cuda"                       # видеокарта NVIDIA
elif torch.backends.mps.is_available():
    device = "mps"                        # видеоядро Mac на Apple Silicon
else:
    device = "cpu"

model = ChurnNet(n_in=8).to(device)      # веса — на устройство один раз (ChurnNet — из урока про PyTorch)
for xb, yb in train_loader:
    xb, yb = xb.to(device), yb.to(device) # каждый батч — на то же устройство
    ...
preds = model(X_test.to(device)).detach().cpu().numpy()   # назад в numpy — через .cpu()
```

**Что здесь происходит:**

- `torch.cuda.is_available()` — есть ли видеокарта NVIDIA с драйверами; `mps` — ускоритель на Mac с процессором Apple. Иначе — обычный процессор: код тот же, просто медленнее.
- `.to(device)` у модели переносит все её параметры; у тензора возвращает **копию** на устройстве — поэтому `xb = xb.to(device)`, а не просто `xb.to(device)`.
- `.cpu()` перед `.numpy()` — numpy живёт только в обычной памяти.

Своей видеокарты нет — подойдёт облачный блокнот с GPU (например, Google Colab или Kaggle Notebooks): там тот же Jupyter, а `torch.cuda.is_available()` вернёт `True`. Код, написанный с `device`, переносится туда без правок.

**Smoke-test — четыре проверки за минуту:**

1. **Один батч вперёд:** форма выхода совпадает с формой ответа, в выходе нет `nan`.
2. **Стартовая потеря разумна:** пока сеть ничего не знает, логиты маленькие, вероятности около 0.5, и бинарная потеря близка к $\ln 2 \approx 0.693$; для $K$ классов — к $\ln K$ (для 10 цифр — 2.303). Потеря в десятки раз больше — неудачный масштаб весов или признаков.
3. **Переобучиться на крошечном куске:** 16–32 объекта, несколько сотен шагов. Сеть с сотнями параметров обязана их «зазубрить», потеря должна упасть почти до нуля. Не падает — ошибка в цикле, градиентах или данных.
4. **Короткая эпоха на 1 % данных:** засечь время и умножить — станет ясно, сколько ждать полного обучения, и не упадёт ли что-то на сохранении результатов.

::: figure nn-smoke-test
Четыре проверки по порядку и что искать, если проверка не прошла. Синим — результаты проверок 1–3 на numpy-сети с полумесяцами из кода ниже.
:::

Проверки 1–3 на нашей numpy-сети с полумесяцами:

```python
import numpy as np
from sklearn.datasets import make_moons

X, y = make_moons(400, noise=0.2, random_state=0)

def init(hidden=16, seed=0):
    rng = np.random.default_rng(seed)
    return [rng.normal(size=(2, hidden)) * np.sqrt(2 / 2), np.zeros(hidden),   # He для слоя 2 → 16
            rng.normal(size=hidden) * np.sqrt(1 / hidden), 0.0]               # Xavier для выхода

def logits(params, X):
    W1, b1, w2, b2 = params
    return np.maximum(0, X @ W1 + b1) @ w2 + b2

def loss_of(params, X, y):
    z = logits(params, X)
    return float(np.mean(np.logaddexp(0, z) - y * z))                        # BCE по логитам

def step(params, X, y, lr):
    W1, b1, w2, b2 = params
    Z1 = X @ W1 + b1
    H = np.maximum(0, Z1)
    p = 1 / (1 + np.exp(-(H @ w2 + b2)))
    d2 = (p - y) / len(y)
    dH = np.outer(d2, w2) * (Z1 > 0)
    return [W1 - lr * X.T @ dH, b1 - lr * dH.sum(axis=0), w2 - lr * H.T @ d2, b2 - lr * d2.sum()]

params = init()
z = logits(params, X[:32])
print("1) форма выхода:", z.shape, "| есть nan:", bool(np.isnan(z).any()))
print("2) стартовая потеря:", round(loss_of(params, X, y), 3), "| ориентир ln 2 =", round(float(np.log(2)), 3))
Xs, ys = X[:16], y[:16]
for _ in range(300):
    params = step(params, Xs, ys, 0.5)
print("3) потеря на 16 объектах после 300 шагов:", round(loss_of(params, Xs, ys), 3))
```

**Что здесь происходит:**

- `init` — веса по He и Xavier (урок «Граф вычислений, инициализация и обрезка градиента»), `logits` — прямой проход без сигмоиды, `loss_of` — устойчивая логистическая потеря по логитам (раздел «Выход и потеря под тип задачи» урока «Softmax, выход под задачу и мини-батчи»), `step` — один шаг обучения из урока «Обучение сети: обратное распространение ошибки».
- Проверка 1 — один батч из 32 объектов: выход формы (32,), `nan` нет.
- Проверка 2 — потеря до обучения сравнивается с $\ln 2$.
- Проверка 3 — 300 шагов только на 16 объектах.

**Как читать результат:** стартовая потеря 0.687 почти совпадает с ориентиром 0.693 — масштабы в порядке. На 16 объектах потеря упала до 0.048 — сеть умеет учиться, значит, градиенты и шаг написаны верно. Теперь можно запускать полное обучение. Если бы на третьем шаге потеря застряла около 0.4 — искать ошибку, а не подбирать `lr`.

В PyTorch тот же тест — десяток строк перед долгим запуском:

```python static
xb, yb = next(iter(train_loader))                 # один батч
xb, yb = xb.to(device), yb.to(device)
logits = model(xb)
assert logits.shape == yb.shape and not torch.isnan(logits).any()
print("стартовая потеря:", loss_fn(logits, yb).item())          # ориентир ln 2 ≈ 0.693

opt = torch.optim.Adam(model.parameters(), lr=1e-2)
model.train()
for _ in range(300):                               # зазубрить один батч
    opt.zero_grad()
    loss = loss_fn(model(xb), yb)
    loss.backward()
    opt.step()
print("после 300 шагов на одном батче:", loss.item())            # должно быть близко к 0
```

На гостях «Зерна» такой тест дал стартовую потерю 0.676 и 0.061 после 300 шагов — можно запускать полное обучение. Условия прогона: батч — первые 64 гостя, 8 числовых признаков (стаж, приложение, визиты, дни с визита, средний чек с пропусками, заменёнными нулём, доля доставки, промо, жалобы) после стандартизации, сеть `ChurnNet` из раздела про `nn.Module` урока «PyTorch: то же самое, но в промышленном масштабе», `torch.manual_seed(0)`. До нуля потеря не дошла из-за dropout: в режиме `train()` он и при «зазубривании» выключает часть нейронов. Для smoke-теста dropout можно временно поставить в 0.

::: warn Типичные ошибки
- **`Expected all tensors to be on the same device`.** Модель на `cuda`, а батч остался на `cpu` (или наоборот). Каждый тензор, который входит в модель или в потерю, — через `.to(device)`.
- **`xb.to(device)` без присвоения.** Метод тензора возвращает копию, исходный тензор остаётся на старом месте — та же ошибка про устройства.
- **Smoke-test пропущен «потому что код маленький».** Сеть с ошибкой в градиентах часто всё равно учится — медленнее и хуже, и без теста это выглядит как «плохие гиперпараметры». Часы подбора `lr` вместо минуты проверки.
:::

{{practice: smoke-test}}

## Практика

## task: dropout | Dropout руками | base

Напишите функцию `dropout(H, rate, rng)`: маска «оставить» — `rng.random(H.shape) >= rate`, результат — `H * mask / (1 - rate)`. Примените к матрице из единиц 1000 × 50 с `rate = 0.3` и генератором `np.random.default_rng(0)`. Сохраните `kept_share` — долю ненулевых элементов (3 знака) и `mean_after` — среднее результата (3 знака).

### starter
```python
import numpy as np
H = np.ones((1000, 50))

```

### check
```python
import numpy as _np
m = _np.random.default_rng(0).random((1000, 50)) >= 0.3
out = _np.ones((1000, 50)) * m / 0.7
assert close(need('kept_share'), round((out != 0).mean(), 3), 0.0011), f'kept_share = {need("kept_share")}.'
assert close(need('mean_after'), round(out.mean(), 3), 0.0011), f'mean_after = {need("mean_after")}.'
```

### hint
`mask = rng.random(H.shape) >= rate`; генератор создайте один раз и передайте в функцию.

### hint
Оставшиеся значения масштабируйте: `H * mask / (1 - rate)`.

### solution
```python
import numpy as np
H = np.ones((1000, 50))

def dropout(H, rate, rng):
    mask = rng.random(H.shape) >= rate
    return H * mask / (1 - rate)

out = dropout(H, 0.3, np.random.default_rng(0))
kept_share = round((out != 0).mean(), 3)
mean_after = round(out.mean(), 3)
```

### explain
Выключено около 30 % значений, но среднее осталось около 1: оставшиеся выросли в 1 / 0.7 раза. Без этого масштабирования на прогнозе (когда dropout выключен) сеть видела бы «слишком громкие» сигналы.

## task: batchnorm | BatchNorm руками | base

Напишите две функции, как в теории: `batchnorm_train(Xb, gamma, beta, run_mean, run_var, momentum=0.1, eps=1e-5)` возвращает `(out, run_mean, run_var)` — нормированный батч и обновлённые скользящие средние (дисперсию считайте `Xb.var(axis=0)`); `batchnorm_eval(X, gamma, beta, run_mean, run_var, eps=1e-5)` нормирует по скользящим средним.

Данные — первые 6 гостей, три признака (`B` в заготовке), `gamma` и `beta` заданы, стартовые `run_mean` — нули, `run_var` — единицы. Пропустите через `batchnorm_train` сначала батч `B[:3]`, затем `B[3:]`. Сохраните `out1` — выход первого батча (3 знака), `run_mean` и `run_var` после двух батчей (4 знака) и `pred` — `batchnorm_eval` для первого гостя `B[:1]` после двух батчей (3 знака).

### starter
```python
import numpy as np
import pandas as pd
g = pd.read_csv("guests_churn.csv")
B = g[["visits_90d", "days_since_last", "complaints"]].head(6).to_numpy(float)
gamma = np.array([1.0, 2.0, 0.5])
beta = np.array([0.0, 1.0, -1.0])
run_mean, run_var = np.zeros(3), np.ones(3)

```

### check
```python
import numpy as _np
import pandas as _pd
B0 = _pd.read_csv("guests_churn.csv")[["visits_90d", "days_since_last", "complaints"]].head(6).to_numpy(float)
ga, be = _np.array([1.0, 2.0, 0.5]), _np.array([0.0, 1.0, -1.0])
def _bt(Xb, rm, rv):
    mu, var = Xb.mean(0), Xb.var(0)
    return ga * (Xb - mu) / _np.sqrt(var + 1e-5) + be, 0.9 * rm + 0.1 * mu, 0.9 * rv + 0.1 * var
o1, rm, rv = _bt(B0[:3], _np.zeros(3), _np.ones(3)); _, rm, rv = _bt(B0[3:], rm, rv)
pr = ga * (B0[:1] - rm) / _np.sqrt(rv + 1e-5) + be
f = need('batchnorm_train')
t_out, t_rm, t_rv = f(B0[:3], ga, be, _np.zeros(3), _np.ones(3))
assert _np.allclose(t_out, o1, atol=1e-6), 'batchnorm_train нормирует не так: среднее и дисперсия — по объектам батча (axis=0), затем gamma * x̂ + beta.'
assert _np.allclose(t_rm, 0.1 * B0[:3].mean(0)), 'Скользящее среднее: (1 - momentum) * run_mean + momentum * среднее батча.'
assert _np.allclose(need('out1'), o1.round(3), atol=1e-3), f'out1 = {need("out1")}.'
assert _np.allclose(need('run_mean'), rm.round(4), atol=1e-4) and _np.allclose(need('run_var'), rv.round(4), atol=1e-4), f'run_mean = {need("run_mean")}, run_var = {need("run_var")}. Проверьте, что второй батч продолжил обновлять скользящие средние после первого.'
assert _np.allclose(need('pred'), pr.round(3), atol=1e-3), f'pred = {need("pred")}, а нужно {pr.round(3)}. На прогнозе батч не нужен — только run_mean и run_var.'
```

### hint
Внутри `batchnorm_train`: `mu, var = Xb.mean(axis=0), Xb.var(axis=0)`, выход — `gamma * (Xb - mu) / np.sqrt(var + eps) + beta`, затем два обновления скользящих средних.

### hint
Два вызова подряд, каждый раз перезаписывая скользящие средние: `out1, run_mean, run_var = batchnorm_train(B[:3], gamma, beta, run_mean, run_var)`, потом то же для `B[3:]`. Округлять — только при сохранении результатов.

### solution
```python
import numpy as np
import pandas as pd
g = pd.read_csv("guests_churn.csv")
B = g[["visits_90d", "days_since_last", "complaints"]].head(6).to_numpy(float)
gamma = np.array([1.0, 2.0, 0.5])
beta = np.array([0.0, 1.0, -1.0])
run_mean, run_var = np.zeros(3), np.ones(3)

def batchnorm_train(Xb, gamma, beta, run_mean, run_var, momentum=0.1, eps=1e-5):
    mu, var = Xb.mean(axis=0), Xb.var(axis=0)
    out = gamma * (Xb - mu) / np.sqrt(var + eps) + beta
    run_mean = (1 - momentum) * run_mean + momentum * mu
    run_var = (1 - momentum) * run_var + momentum * var
    return out, run_mean, run_var

def batchnorm_eval(X, gamma, beta, run_mean, run_var, eps=1e-5):
    return gamma * (X - run_mean) / np.sqrt(run_var + eps) + beta

out1, run_mean, run_var = batchnorm_train(B[:3], gamma, beta, run_mean, run_var)
_, run_mean, run_var = batchnorm_train(B[3:], gamma, beta, run_mean, run_var)
pred = batchnorm_eval(B[:1], gamma, beta, run_mean, run_var).round(3)
out1, run_mean, run_var = out1.round(3), run_mean.round(4), run_var.round(4)
print(out1, run_mean, run_var, pred)
```

### explain
В первом батче у каждого столбца после нормировки среднее 0, а масштаб задают `gamma` и `beta`: второй столбец растянут вдвое и сдвинут на 1. Третий столбец — жалобы — у всех шести гостей нулевой: дисперсия 0, и без `eps` было бы деление 0 / 0 = `nan`; с `eps` выход равен просто `beta` = −1. Скользящие средние после двух батчей ещё далеки от правды: среднее визитов 0.64 при настоящем 3.33 — от стартового нуля ушли только на $1 - 0.9^2 = 19\%$ пути. Поэтому `pred` для первого гостя (2.44 и 1.43) совсем не похож на его же выход в режиме обучения (0.981 и −1.172). Это та же картина, что у PyTorch в теории: режим прогноза BN честен только после многих батчей обучения.

## task: smoke-test | Smoke-test находит ошибку | plus

Коллега прислал две версии шага обучения сети с полумесяцами из урока «Обучение сети: обратное распространение ошибки» — `step_a` и `step_b` (они уже загружены, код скрыт). Обе выглядят рабочими: на полумесяцах потеря у обеих падает. Найдите версию с ошибкой smoke-тестом. В заготовке есть данные `X`, `y`, функции `init()` и `loss_of(params, X, y)` из теории.

Напишите `smoke(step, n=16, steps=300, lr=0.5)`: берёт свежие веса `init()`, считает стартовую потерю на **всех** `X, y`, затем делает `steps` шагов `params = step(params, X[:n], y[:n], lr)` только на первых `n` объектах и возвращает `(стартовая потеря, потеря на этих n объектах после обучения)`. Сохраните:

- `res` — словарь `{"a": …, "b": …}` с парами для обеих версий (3 знака);
- `start_ok` — `True`, если стартовая потеря отличается от $\ln 2$ меньше чем на 0.1;
- `buggy` — `"a"` или `"b"`: у какой версии потеря на 16 объектах не опустилась ниже 0.1;
- `both_learn` — `True`, если у обеих версий потеря на 16 объектах после обучения меньше стартовой.

### setup
```python
import numpy as np
from sklearn.datasets import make_moons
X, y = make_moons(400, noise=0.2, random_state=0)
def init(hidden=16, seed=0):
    rng = np.random.default_rng(seed)
    return [rng.normal(size=(2, hidden)) * np.sqrt(2 / 2), np.zeros(hidden),
            rng.normal(size=hidden) * np.sqrt(1 / hidden), 0.0]
def loss_of(params, X, y):
    W1, b1, w2, b2 = params
    z = np.maximum(0, X @ W1 + b1) @ w2 + b2
    return float(np.mean(np.logaddexp(0, z) - y * z))
def _make_step(mask_sign):
    def step(params, X, y, lr):
        W1, b1, w2, b2 = params
        Z1 = X @ W1 + b1
        H = np.maximum(0, Z1)
        p = 1 / (1 + np.exp(-(H @ w2 + b2)))
        d2 = (p - y) / len(y)
        dH = np.outer(d2, w2) * ((Z1 > 0) if mask_sign > 0 else (Z1 < 0))
        return [W1 - lr * X.T @ dH, b1 - lr * dH.sum(axis=0), w2 - lr * H.T @ d2, b2 - lr * d2.sum()]
    return step
step_a = _make_step(1)
step_b = _make_step(-1)
```

### starter
```python
import numpy as np

def smoke(step, n=16, steps=300, lr=0.5):
    params = init()
    ...

```

### check
```python
import numpy as _np
X0, y0 = need('X'), need('y'); ini, lo = need('init'), need('loss_of')
def _sm(step):
    P = ini(); s = lo(P, X0, y0)
    for _ in range(300):
        P = step(P, X0[:16], y0[:16], 0.5)
    return round(s, 3), round(lo(P, X0[:16], y0[:16]), 3)
want = {'a': _sm(need('step_a')), 'b': _sm(need('step_b'))}
f = need('smoke')
got_a = tuple(f(need('step_a')))
assert len(got_a) == 2 and close(got_a[0], want['a'][0], 0.0011) and close(got_a[1], want['a'][1], 0.0011), f'smoke(step_a) = {got_a}, а нужно {want["a"]}. Стартовая потеря — на всех X, итоговая — на первых n.'
r = need('res', dict)
for k in want:
    assert k in r and all(close(u, v, 0.0011) for u, v in zip(r[k], want[k])), f'res[{k!r}] = {r.get(k)}, а нужно {want[k]}.'
assert need('start_ok') == (abs(want['a'][0] - _np.log(2)) < 0.1), f'start_ok = {need("start_ok")}.'
assert need('buggy') == [k for k in want if want[k][1] >= 0.1][0], f'buggy = {need("buggy")!r}.'
assert need('both_learn') == all(want[k][1] < want[k][0] for k in want), f'both_learn = {need("both_learn")}.'
```

### hint
Внутри `smoke`: `start = loss_of(params, X, y)`, цикл `for _ in range(steps): params = step(params, X[:n], y[:n], lr)`, затем `return start, loss_of(params, X[:n], y[:n])`.

### hint
`res = {k: tuple(round(v, 3) for v in smoke(s)) for k, s in {"a": step_a, "b": step_b}.items()}`. Сравнение с $\ln 2$ — через `np.log(2)`.

### hint
`buggy = [k for k in res if res[k][1] >= 0.1][0]`, `both_learn = all(res[k][1] < res[k][0] for k in res)`.

### solution
```python
import numpy as np

def smoke(step, n=16, steps=300, lr=0.5):
    params = init()
    start = loss_of(params, X, y)
    for _ in range(steps):
        params = step(params, X[:n], y[:n], lr)
    return start, loss_of(params, X[:n], y[:n])

res = {k: tuple(round(v, 3) for v in smoke(s)) for k, s in {"a": step_a, "b": step_b}.items()}
start_ok = abs(res["a"][0] - np.log(2)) < 0.1
buggy = [k for k in res if res[k][1] >= 0.1][0]
both_learn = all(res[k][1] < res[k][0] for k in res)
print(res, start_ok, buggy, both_learn)
```

### explain
Стартовая потеря у обеих версий одинаковая — 0.687 (веса одни и те же), и она близка к $\ln 2$: прямой проход и масштабы в порядке. Разница видна только на третьей проверке: версия `a` за 300 шагов «зазубрила» 16 объектов до 0.048, версия `b` застряла на 0.402. При этом обе учатся — потеря у `b` тоже ниже стартовой, — поэтому на графике обычного обучения ошибку легко принять за «неудачный `lr`». В `step_b` перепутана маска ReLU: `(Z1 < 0)` вместо `(Z1 > 0)`. Выходной слой учится правильно, а в скрытом градиент идёт к нейронам, которые на данном объекте выключены (их выход 0, на прогноз они не влияли), и не доходит до включённых. Веса скрытого слоя меняются не туда, и полезную работу делает фактически только последний слой. Числовая проверка градиента (урок «Обучение сети: обратное распространение ошибки») нашла бы эту ошибку точно, smoke-test — быстро и без знания формул.
