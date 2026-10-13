---
title: Свёрточные нейросети
files: [showcase.npz]
lead: "Свёрточная сеть — это фильтры и пулинг из урока «Свёртка и фильтры», только веса фильтров она подбирает сама градиентным спуском, а слои складывает друг на друга. Разбираем, как через сеть проходит картинка и почему у неё так мало параметров, считаем рецептивное поле, проверяем, что даже случайные фильтры с пулингом дают сильные признаки, и пишем сеть на PyTorch для своего компьютера. Перенос обучения и задачи кроме классификации — в следующих уроках."
recap:
  - "Свёрточный слой: `C_out` фильтров размера `k × k × C_in` + сдвиги; параметров `(k·k·C_in + 1)·C_out` — не зависит от размера картинки."
  - "Типовой блок: свёртка → ReLU → max-pooling. Каждый следующий слой видит всё большую область картинки и находит всё более сложные формы."
  - "Глобальный пулинг в конце делает ответ почти независимым от положения объекта."
  - "Форма тензора в PyTorch: `(батч, каналы, высота, ширина)`; чёрно-белая картинка — 1 канал, цветная — 3."
  - "Свёрточная сеть устойчивее к сдвигу и освещению, чем модели на пикселях, но не неуязвима: проверка на изменённых данных обязательна."
---

## От фильтров к слоям

В уроке «Свёртка и фильтры» мы сами придумали четыре фильтра и получили признаки, на которых логистическая регрессия поднялась с 0.68 до 0.88. Свёрточная сеть (CNN, convolutional neural network) делает то же, но:

1. **Веса фильтров — параметры модели.** Их подбирает градиентный спуск, как веса нейронов в главе 11.
2. **Слоёв несколько.** Первый слой находит края и пятна. Второй применяет свои фильтры к картам признаков первого и находит сочетания краёв — дуги, углы. Третий — части объектов.
3. **В конце — обычные полносвязные слои** и softmax, как в главе 11.

Через слои картинка превращается из «32 × 32 яркостей» в «64 числа: насколько здесь есть каждая из 64 найденных форм».

## Сколько параметров

У полносвязного слоя каждый нейрон связан с каждым пикселем. У свёрточного — небольшой фильтр, один и тот же для всех мест картинки (**общие веса**). Поэтому параметров на порядки меньше.

```python
def dense_params(n_in, n_out):
    return n_in * n_out + n_out                   # веса + сдвиги

def conv_params(k, c_in, c_out):
    return (k * k * c_in + 1) * c_out             # каждый фильтр k × k × c_in и свой сдвиг

print("полносвязный, 1024 → 64:   ", dense_params(32 * 32, 64))
print("свёрточный 3 × 3, 1 → 16:  ", conv_params(3, 1, 16))
print("свёрточный 3 × 3, 16 → 32: ", conv_params(3, 16, 32))
```

::: figure conv-vs-dense
Слева — полносвязный слой: каждая линия — свой вес. Справа — свёрточный: один и тот же фильтр 3 × 3 прикладывается к каждому месту картинки, поэтому весов у него 9 плюс сдвиг, сколько бы ни было пикселей.
:::

Посчитаем руками. Свёрточный слой 3 × 3, 1 канал → 16 фильтров: у каждого фильтра 3 · 3 · 1 = 9 весов и 1 сдвиг, итого 10; фильтров 16 — **160** параметров. Полносвязный слой 1024 → 64: каждый из 64 нейронов связан со всеми 1024 пикселями — 65 536 весов и 64 сдвига, итого **65 600**. Разница в 400 раз, а выход у свёрточного слоя даже больше (16 карт 32 × 32).

**Что здесь происходит:**

- `dense_params(n_in, n_out)` — у каждого из `n_out` нейронов `n_in` весов и один сдвиг.
- `conv_params(k, c_in, c_out)` — у каждого из `c_out` фильтров `k · k · c_in` весов (фильтр смотрит на все входные каналы сразу) и один сдвиг.
- Во втором свёрточном слое `c_in = 16`: фильтр 3 × 3 смотрит на все 16 карт первого слоя, поэтому весов у него 3 · 3 · 16 = 144.

::: predict
```python static
def conv_params(k, c_in, c_out):
    return (k * k * c_in + 1) * c_out
print(conv_params(5, 3, 8))
```

- `200`
- [x] `608`
- `600`

Почему: фильтр 5 × 5 на цветной картинке (3 канала) — 5 · 5 · 3 = 75 весов плюс 1 сдвиг = 76; фильтров 8 — 76 · 8 = 608. Частая ошибка — забыть сдвиги (получится 600) или каналы (200).
:::

Свёрточному слою всё равно, 32 × 32 картинка или 1000 × 1000: число его параметров зависит только от размера фильтра и числа каналов. А общие веса дают важное свойство: фильтр «полумесяц» найдёт полумесяц в любом месте кадра — не нужно учиться отдельно для каждого положения, как приходилось лесу на пикселях.

::: note
**Каналы.** У цветной картинки 3 канала (R, G, B), и фильтр первого слоя имеет форму `3 × 3 × 3` — он смотрит на все три цвета сразу. После слоя с 16 фильтрами получается 16 карт признаков — 16 каналов, и фильтры следующего слоя имеют форму `3 × 3 × 16`.
:::

::: quiz
Почему у свёрточного слоя намного меньше параметров, чем у полносвязного на той же картинке?

- [x] Один и тот же маленький фильтр применяется ко всем местам картинки — веса общие
  > Фильтр 3 × 3 — это 9 весов плюс смещение, сколько бы пикселей ни было. Полносвязный слой связывает каждый пиксель с каждым нейроном.
- [ ] Свёрточный слой не учит веса
  > Учит — веса фильтров.
- [ ] Картинка уменьшается до свёртки
  > Уменьшает пулинг, причём после свёртки.
- [ ] У свёрточного слоя нет смещения
  > Смещение есть, по одному на фильтр.
:::

{{practice: params}}

## Проход через сеть руками

Прогоним одну картинку через свёрточный слой из 8 фильтров со случайными весами, ReLU, max-pooling и полносвязный слой с softmax — проследим за формами.

```python
import numpy as np
from scipy import ndimage as ndi

rng = np.random.default_rng(0)
d = np.load("showcase.npz")
img = d["X"][0] / 255                                   # (32, 32)

W1 = rng.normal(0, 0.3, size=(8, 3, 3))                 # 8 фильтров 3 × 3
b1 = np.zeros(8)
maps = np.stack([ndi.correlate(img, w, mode="nearest") + b for w, b in zip(W1, b1)])
print("после свёртки:", maps.shape)                     # (8, 32, 32)

maps = np.maximum(maps, 0)                              # ReLU
pooled = maps.reshape(8, 16, 2, 16, 2).max(axis=(2, 4))
print("после пулинга:", pooled.shape)                   # (8, 16, 16)

flat = pooled.ravel()
W2 = rng.normal(0, 0.01, size=(flat.size, 4))
logits = flat @ W2
probs = np.exp(logits - logits.max()) / np.exp(logits - logits.max()).sum()
print("вектор:", flat.shape, "→ вероятности классов:", probs.round(3))
```

**Что здесь происходит:**

| Шаг | Код | Форма после шага |
|---|---|---|
| картинка | `d["X"][0] / 255` | `(32, 32)` |
| 8 фильтров + сдвиги | `ndi.correlate(img, w) + b` для каждого фильтра, `np.stack` | `(8, 32, 32)` — 8 карт признаков |
| ReLU | `np.maximum(maps, 0)` — отрицательные отклики → 0 | `(8, 32, 32)` |
| max-pooling 2 × 2 | `reshape(8, 16, 2, 16, 2).max(axis=(2, 4))` | `(8, 16, 16)` |
| в вектор | `pooled.ravel()` | `(2048,)` |
| полносвязный слой | `flat @ W2`, `W2` формы `(2048, 4)` | `(4,)` — по числу классов |
| softmax | `exp(logits − max) / сумма` | 4 вероятности, сумма 1 |

::: figure cnn-shapes
Та же таблица схемой: форма данных после каждого шага прохода.
:::

- `rng.normal(0, 0.3, size=(8, 3, 3))` — случайные начальные веса: так начинает и настоящая сеть перед обучением.
- `logits - logits.max()` перед экспонентой — защита от переполнения (глава 11); на вероятности это не влияет.

Веса случайные, поэтому и ответ пока бессмыслен. Обучение сети — подбор `W1`, `b1`, `W2` так, чтобы вероятность правильного класса была высокой, тем же backprop, что в главе 11: производные через свёртку и пулинг считаются по тем же правилам цепочки.

{{practice: p-shapes, layer, softmax}}

## Что «видит» каждый слой

Фильтр первого слоя 3 × 3 смотрит на кусочек картинки 3 × 3. А второй слой? Его фильтр 3 × 3 смотрит на 3 × 3 пикселя карты первого слоя, но каждый из них сам собран из окна 3 × 3 исходной картинки. Вместе они покрывают 5 × 5. А если между слоями стоит пулинг 2, каждый пиксель карты «отвечает» уже за блок 2 × 2, и окно второго слоя покрывает гораздо больше.

Размер области исходной картинки, от которой зависит один выход слоя, называют **рецептивным полем**. Посчитаем его для сети из урока (свёртка 3 → пулинг 2 → свёртка 3 → пулинг 2 → свёртка 3):

```python
def receptive_field(layers):
    rf, jump = 1, 1                        # поле одного пикселя и «шаг» пикселя слоя в пикселях картинки
    for kind, k in layers:
        rf += (k - 1) * jump               # окно k добавляет (k − 1) шагов текущего масштаба
        if kind == "pool":
            jump *= k                      # после пулинга k пиксель слоя — это k пикселей предыдущего
    return rf

net = [("conv", 3), ("pool", 2), ("conv", 3), ("pool", 2), ("conv", 3)]
for i in range(1, len(net) + 1):
    print(net[i - 1], "→ поле", receptive_field(net[:i]))
```

**Что здесь происходит:**

- `rf` — текущий размер поля, `jump` — сколько пикселей исходной картинки между соседними пикселями текущей карты.
- Свёртка `k × k` расширяет поле на `(k − 1) · jump`; пулинг тоже расширяет и, главное, увеличивает `jump`.

::: figure receptive-field
Рецептивное поле по слоям сети урока, по одной стороне кадра: 3 → 4 → 8 → 10 → 18 пикселей. Пулинг не только расширяет поле, но и увеличивает шаг, поэтому следующая свёртка расширяет его сильнее.
:::

**Что получилось:** после трёх свёрток с двумя пулингами один выход видит область 18 × 18 — больше половины кадра 32 × 32 по каждой стороне. Поэтому третий слой может откликаться на целый круассан, а не на кусочек края. А глобальный пулинг в конце сети собирает отклики со всего кадра.

{{practice: receptive}}

## Случайные фильтры — уже хорошие признаки

Удивительный факт: даже фильтры со **случайными** весами плюс ReLU и пулинг дают признаки лучше пикселей. Пулинг делает их терпимыми к сдвигу, а случайных фильтров много и разных — среди них найдутся «детекторы» и краёв, и пятен.

```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)

def random_conv_features(Z, W, s=4):
    out = []
    for w in W:
        f = np.maximum(np.stack([ndi.correlate(z, w, mode="nearest") for z in Z]), 0)   # свёртка + ReLU
        n = len(Z)
        out.append(f.reshape(n, 32 // s, s, 32 // s, s).max(axis=(2, 4)).reshape(n, -1))
    return np.hstack(out)

W = np.random.default_rng(0).normal(size=(16, 5, 5))          # 16 случайных фильтров 5 × 5
F = random_conv_features(X, W)
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(F[tr], y[tr])
print(F.shape, "→ доля верных:", round(model.score(F[te], y[te]), 3))
```

**Что здесь происходит:**

- `W` — 16 фильтров 5 × 5 со случайными весами из нормального распределения. Их **не обучают**.
- Для каждого фильтра: свёртка всех картинок → ReLU (`np.maximum(..., 0)`) → max-pooling 4 × 4 → 64 числа на картинку. 16 фильтров × 64 = 1024 признака.
- Обучается только логистическая регрессия сверху — как «последний слой» сети.

Около 0.94 — лучше наших четырёх продуманных фильтров с тем же пулингом 4 (0.88) и лучше леса из 100 деревьев на пикселях (0.91). Обученная сеть подбирает фильтры осмысленно и добавляет ещё слои — и идёт дальше.

::: deep
Почему это работает? Модель после фильтров линейная, а линейной модели нужно много разнообразных нелинейных признаков. Случайные фильтры + ReLU + пулинг — дешёвый способ их получить. На этом же наблюдении основан **перенос обучения**: фильтры чужой обученной сети, даже обученной на совсем других картинках, дают признаки куда лучше случайных.
:::

{{practice: random, rand-light}}

## Сеть на PyTorch

В браузерном Python PyTorch нет, поэтому код ниже — для вашего компьютера (`uv add torch numpy scikit-learn`, файл `showcase.npz` — рядом со скриптом). Обучение 25 эпох на ноутбуке занимает меньше минуты.

```python static
import numpy as np
import torch
from torch import nn
from sklearn.model_selection import train_test_split

torch.manual_seed(0)
d = np.load("showcase.npz")
X = torch.tensor(d["X"] / 255, dtype=torch.float32).unsqueeze(1)   # (2000, 1, 32, 32): канал — второе измерение
y = torch.tensor(d["y"])
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=d["y"])

net = nn.Sequential(
    nn.Conv2d(1, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 16 × 16 × 16
    nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 32 × 8 × 8
    nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(),
    nn.AdaptiveMaxPool2d(1), nn.Flatten(),                                    # глобальный пулинг → 64 числа
    nn.Linear(64, 4),
)
print("параметров:", sum(p.numel() for p in net.parameters()))

opt = torch.optim.Adam(net.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()
for epoch in range(25):
    net.train()
    for idx in torch.tensor(tr)[torch.randperm(len(tr))].split(64):   # мини-батчи по 64
        xb = X[idx]
        if torch.rand(1) < 0.5:
            xb = xb.flip(-1)                                          # аугментация: отражение
        loss = loss_fn(net(xb), y[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    net.eval()
    with torch.no_grad():
        acc = (net(X[te]).argmax(1) == y[te]).float().mean().item()
    print(f"эпоха {epoch + 1}: точность на тесте {acc:.3f}")

with torch.no_grad():                                                 # стресс-тест, как в уроке «Модели на пикселях»
    for name, Z in {"сдвиг на 4": torch.roll(X[te], 4, dims=3), "тусклее на 30 %": X[te] * 0.7}.items():
        print(name, round((net(Z).argmax(1) == y[te]).float().mean().item(), 3))
```

**Что здесь происходит:**

- `torch.tensor(..., dtype=torch.float32).unsqueeze(1)` — массив numpy превращается в тензор PyTorch, `unsqueeze(1)` добавляет ось каналов: `(2000, 32, 32)` → `(2000, 1, 32, 32)`.
- `nn.Conv2d(1, 16, kernel_size=3, padding=1)` — 16 фильтров 3 × 3 на одном входном канале; `padding=1` сохраняет размер 32 × 32.
- `nn.MaxPool2d(2)` — пулинг 2 × 2: 32 → 16 → 8.
- `nn.AdaptiveMaxPool2d(1)` — глобальный max-pooling: из каждой карты 8 × 8 остаётся одно число (максимум). 64 карты → 64 числа.
- `nn.Linear(64, 4)` — полносвязный слой на 4 класса; softmax прячется внутри `CrossEntropyLoss`.
- Цикл обучения — как в главе 11: перемешать индексы (`randperm`), разбить на мини-батчи по 64 (`split(64)`), для каждого — прямой проход, потеря, `zero_grad` → `backward` → `step`.
- `xb.flip(-1)` — с вероятностью 1/2 батч отражается по горизонтали: аугментация «на лету», каждый раз новая.
- `net.eval()` и `torch.no_grad()` — режим проверки: без подсчёта градиентов, быстрее.

Что получится (числа немного зависят от компьютера и версии PyTorch): у сети около 23,5 тыс. параметров — почти втрое меньше, чем у одного полносвязного слоя 1024 → 64 из раздела «Сколько параметров» (65 600), хотя свёрточных слоёв три. Точность на тесте к 25-й эпохе — около 0.98. На сдвинутых кадрах — почти столько же (0.97): глобальный пулинг сделал своё дело. А на тусклых — около 0.86: лучше, чем 0.47 у леса, но заметно хуже обычного теста. Сеть тоже выучила кое-что про абсолютную яркость, и от этого лечат так же — нормировкой входа и аугментацией яркости.

::: warn
`padding=1` дополняет края так, чтобы свёртка 3 × 3 не уменьшала картинку, — как `mode="constant"` в scipy: нулями. В уроке «Свёртка и фильтры» нули за краем давали ложный край, но там фильтры были ручные. Сеть видит эти нули при обучении на каждом кадре и подбирает веса так, чтобы рамка из нулей не мешала; у ручного фильтра такой возможности нет.

`nn.MaxPool2d(2)` — окно 2 × 2 с **шагом** (`stride`) 2: окно прыгает сразу на 2 пикселя, блоки не перекрываются, и карта уменьшается вдвое. У свёрток в нашей сети шаг 1 — окно сдвигается на пиксель, как в уроке «Свёртка и фильтры». Свёртка с шагом 2 тоже уменьшает карту вдвое; так делают в ResNet вместо части пулингов. Размер выхода при любом шаге считает формула из задачи «Размер выхода слоя».

Если перепутать порядок осей (PyTorch ждёт `(батч, каналы, высота, ширина)`), получите ошибку о несовпадении размеров — первым делом проверяйте `.shape`.
:::

Число параметров этой сети можно посчитать и без PyTorch — пересчитайте его в задаче «Считаем параметры». Размеры карт после каждого блока считает задача «Размер выхода слоя».

{{practice: out-size}}

## Разберём вместе: размер пулинга против сдвига

Глобальный пулинг делает признаки нечувствительными к сдвигу. Но не теряем ли мы что-то, если сразу сжать карту 32 × 32 в одно число? Проверим на случайных фильтрах: пулинг 4, 8 и 32 (последний — глобальный), обычный тест и тест со сдвигом на 4 пикселя.

```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
W = np.random.default_rng(0).normal(size=(16, 5, 5))

def features(Z, s):
    out = []
    for w in W:
        f = np.maximum(np.stack([ndi.correlate(z, w, mode="nearest") for z in Z]), 0)
        out.append(f.reshape(len(Z), 32 // s, s, 32 // s, s).max(axis=(2, 4)).reshape(len(Z), -1))
    return np.hstack(out)

X_shift = np.roll(X[te], 4, axis=2)
for s in [4, 8, 32]:
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(features(X[tr], s), y[tr])
    print(f"пулинг {s:2}: признаков {16 * (32 // s) ** 2:4}, тест {m.score(features(X[te], s), y[te]):.3f}, "
          f"сдвиг {m.score(features(X_shift, s), y[te]):.3f}")
```

**Что получилось:**

- пулинг 4 — лучшая точность на обычном тесте (0.94), но сдвиг отнимает 12 пунктов;
- пулинг 32 (глобальный) — сдвиг почти ничего не меняет, но и точность ниже (0.86): от каждого фильтра осталось одно число, и 16 чисел мало, чтобы описать форму;
- пулинг 8 — компромисс.

Обученная сеть решает этот конфликт слоями: первые слои с маленьким пулингом сохраняют детали, а глобальный пулинг ставится в самом конце, когда 64 карты уже описывают не края, а целые формы. Тогда и деталей хватает, и сдвиг не страшен.

::: quiz
Глобальный пулинг почти не боится сдвига. Почему же его не ставят сразу после первой свёртки?

- [x] От каждого фильтра останется одно число, и деталей формы не хватит: на случайных фильтрах точность падает с 0.94 до 0.86. В сети его ставят в конце, когда карты уже описывают целые формы
  > Ранние слои с маленьким пулингом сохраняют детали, поздние — собирают их в формы, и только потом глобальный пулинг убирает зависимость от положения.
- [ ] Глобальный пулинг добавляет слишком много параметров
  > У пулинга нет весов вовсе, а признаков после него меньше всего — 16, по одному на фильтр.
- [ ] После глобального пулинга сдвиг снова начинает мешать
  > Наоборот: со сдвигом точность почти не меняется. Проблема — в потере деталей, а не в сдвиге.
- [ ] Глобальный пулинг можно сделать только в PyTorch
  > В разборе он сделан на numpy — это обычный max-pooling с блоком во всю карту 32 × 32.
:::

{{practice: pool-size}}

## Практика

## task: params | Считаем параметры | warmup

Напишите `dense_params(n_in, n_out)` и `conv_params(k, c_in, c_out)`. Посчитайте `p_net` — число параметров сети из урока на PyTorch: три свёрточных слоя 3 × 3 (1 → 16, 16 → 32, 32 → 64) и полносвязный 64 → 4 (у пулинга, ReLU и Flatten параметров нет).

### starter
```python
def dense_params(n_in, n_out):
    ...

def conv_params(k, c_in, c_out):
    ...

p_net = ...
print(p_net)
```

### check
```python
f, g = need('dense_params'), need('conv_params')
assert f(10, 3) == 33, f'dense_params(10, 3) = {f(10, 3)}, а нужно 33: веса 10·3 и 3 сдвига.'
assert g(5, 3, 8) == 608, f'conv_params(5, 3, 8) = {g(5, 3, 8)}, а нужно 608: (5·5·3 + 1)·8.'
assert need('p_net') == 23556, f'p_net = {need("p_net")}.'
```

### hint
Сначала проверьте формулы на маленьких числах: слой 10 → 3 — это 30 весов и 3 сдвига.

### hint
Сдвиг — по одному на выход (нейрон или фильтр). Сеть: `conv_params(3, 1, 16) + conv_params(3, 16, 32) + conv_params(3, 32, 64) + dense_params(64, 4)`.

### solution
```python
def dense_params(n_in, n_out):
    return n_in * n_out + n_out

def conv_params(k, c_in, c_out):
    return (k * k * c_in + 1) * c_out

p_net = conv_params(3, 1, 16) + conv_params(3, 16, 32) + conv_params(3, 32, 64) + dense_params(64, 4)
print(p_net)
```

## task: p-shapes | Формы по слоям | warmup

Соберите код, который печатает размер стороны карты признаков после каждого блока «свёртка 3 × 3 без дополнения → пулинг 2» для картинки 32 × 32 (два блока подряд).

### parsons
```python
n = 32
n = n - 3 + 1
n = n // 2
print(n)
n = n - 3 + 1
n = n // 2
print(n)
```

### check
```python
assert _lines == ['15', '6'], f'Сейчас: {_lines}.'
```

### hint
Свёртка без дополнения: n − k + 1. Пулинг 2: целочисленное деление на 2.

### hint
32 → 30 → 15 → 13 → 6.

## task: layer | Свёрточный слой | base

Напишите `conv_layer(img, W, b)`: `img` — картинка `(h, w)`, `W` — фильтры `(c_out, k, k)`, `b` — сдвиги `(c_out,)`. Вернуть массив `(c_out, h, w)`: для каждого фильтра `ndi.correlate(img, W[c], mode="nearest") + b[c]`, затем ReLU. Напишите `pool2(maps)` — max-pooling 2 × 2 для массива `(c, h, w)`. Примените к `X[0]` с весами `W1`, `b1` из заготовки: `out = pool2(conv_layer(X[0], W1, b1))`. В `active` — долю положительных чисел в `out` (3 знака).

### setup
```python
import numpy as np
from scipy import ndimage as ndi
X = np.load("showcase.npz")["X"] / 255
_r = np.random.default_rng(1)
W1 = _r.normal(0, 0.3, size=(6, 3, 3))
b1 = _r.normal(0, 0.1, size=6)
```

### starter
```python
import numpy as np
from scipy import ndimage as ndi

def conv_layer(img, W, b):
    ...

def pool2(maps):
    ...

```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
X0 = need('X'); W, b = need('W1'), need('b1')
f, g = need('conv_layer'), need('pool2')
c = _np.maximum(_np.stack([_ndi.correlate(X0[0], w, mode='nearest') + bb for w, bb in zip(W, b)]), 0)
got = _np.asarray(f(X0[0], W, b))
assert got.shape == (6, 32, 32), f'conv_layer(...).shape = {got.shape}, а нужно (6, 32, 32).'
assert _np.allclose(got, c), 'conv_layer: свёртка каждым фильтром + сдвиг, потом ReLU (np.maximum(..., 0)).'
p = c.reshape(6, 16, 2, 16, 2).max(axis=(2, 4))
assert _np.allclose(g(c), p), 'pool2: максимум в блоках 2 × 2 для каждого канала.'
o = need('out')
assert o.shape == (6, 16, 16) and _np.allclose(o, p), f'out.shape = {o.shape}.'
assert close(need('active'), round(float((p > 0).mean()), 3), 0.0015), f'active = {need("active")}.'
```

### hint
В `conv_layer` цикл по парам «фильтр — сдвиг»: `for w, bb in zip(W, b)`. Для каждой — `ndi.correlate(img, w, mode="nearest") + bb`.

### hint
`np.stack([...])` по фильтрам, `np.maximum(..., 0)`. Пулинг: `maps.reshape(c, h // 2, 2, w // 2, 2).max(axis=(2, 4))`.

### hint
Доля положительных — `(out > 0).mean()`; после ReLU и пулинга нули остаются там, где все отклики блока были отрицательными.

### solution
```python
import numpy as np
from scipy import ndimage as ndi

def conv_layer(img, W, b):
    maps = np.stack([ndi.correlate(img, w, mode="nearest") + bb for w, bb in zip(W, b)])
    return np.maximum(maps, 0)

def pool2(maps):
    c, h, w = maps.shape
    return maps.reshape(c, h // 2, 2, w // 2, 2).max(axis=(2, 4))

out = pool2(conv_layer(X[0], W1, b1))
active = round(float((out > 0).mean()), 3)
print(out.shape, active)
```

### explain
Это ровно то, что делает слой `nn.Conv2d` + `nn.ReLU` + `nn.MaxPool2d(2)` в PyTorch, только для одной картинки и одного входного канала. Доля «активных» чисел после ReLU зависит от знаков сдвигов и фильтров: у фильтра с отрицательной суммой весов на светлом фоне отклик почти везде отрицательный, и его карта почти вся обнулится. В обученной сети такие «мёртвые» фильтры — признак проблем с инициализацией или слишком большим шагом обучения.

## task: softmax | Голова сети | base

К выходу `out` (форма `(6, 16, 16)`, вычислен в заготовке) приделайте «голову»: вытянуть в вектор, умножить на `W2` (форма `(1536, 4)`), прибавить `b2`, применить softmax. Сохраните `logits`, `probs` (вероятности 4 классов, сумма 1) и `pred_class` — название класса с наибольшей вероятностью (из `classes`). Для устойчивости вычитайте максимум логита перед экспонентой.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, classes = d["X"] / 255, d["classes"]
_r = np.random.default_rng(1)
W1 = _r.normal(0, 0.3, size=(6, 3, 3)); b1 = _r.normal(0, 0.1, size=6)
_m = np.maximum(np.stack([ndi.correlate(X[0], w, mode="nearest") + b for w, b in zip(W1, b1)]), 0)
out = _m.reshape(6, 16, 2, 16, 2).max(axis=(2, 4))
W2 = _r.normal(0, 0.05, size=(1536, 4)); b2 = np.zeros(4)
```

### starter
```python
import numpy as np

```

### check
```python
import numpy as _np
o, W, b, c = need('out'), need('W2'), need('b2'), need('classes')
lg = o.ravel() @ W + b
pr = _np.exp(lg - lg.max()); pr = pr / pr.sum()
assert _np.allclose(need('logits'), lg), 'logits = out.ravel() @ W2 + b2.'
p = _np.asarray(need('probs'))
assert close(p.sum(), 1, 1e-9), f'Сумма probs = {p.sum()}, а должна быть 1.'
assert _np.allclose(p, pr), 'probs — softmax от logits.'
assert str(need('pred_class')) == str(c[pr.argmax()]), f'pred_class = {need("pred_class")}.'
```

### hint
Вектор — `out.ravel()` (6 · 16 · 16 = 1536 чисел); логиты — `out.ravel() @ W2 + b2`.

### hint
`z = np.exp(logits - logits.max())`, `probs = z / z.sum()`, `classes[probs.argmax()]`.

### solution
```python
import numpy as np

logits = out.ravel() @ W2 + b2
z = np.exp(logits - logits.max())
probs = z / z.sum()
pred_class = str(classes[probs.argmax()])
print(probs.round(3), pred_class)
```

### explain
Это полный прямой проход маленькой свёрточной сети. С случайными весами её ответ — случайность. Всё, что делает обучение, — подбирает `W1`, `b1`, `W2`, `b2`.

## task: random | Сколько случайных фильтров нужно | plus

Повторите эксперимент со случайными фильтрами (функция `random_conv_features` и разбиение `tr, te` — в заготовке) для 4, 8, 16 и 32 фильтров. Веса для каждого варианта — `np.random.default_rng(0).normal(size=(n, 5, 5))` (каждый раз новый генератор с seed 0). Модель — `StandardScaler` + `LogisticRegression(max_iter=3000)`. Сохраните `acc_by_n` — словарь `{n: доля верных}` (3 знака) и `n_enough` — наименьшее `n`, при котором доля верных выше 0.93.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
def random_conv_features(Z, W, s=4):
    out = []
    for w in W:
        f = np.maximum(np.stack([ndi.correlate(z, w, mode="nearest") for z in Z]), 0)
        n = len(Z)
        out.append(f.reshape(n, 32 // s, s, 32 // s, s).max(axis=(2, 4)).reshape(n, -1))
    return np.hstack(out)
```

### starter
```python
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

```

### check
```python
import numpy as _np
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
X0, y0, tr0, te0, rcf = need('X'), need('y'), need('tr'), need('te'), need('random_conv_features')
w = {}
for n in [4, 8, 16, 32]:
    F = rcf(X0, _np.random.default_rng(0).normal(size=(n, 5, 5)))
    w[n] = round(float(_mp(_SS(), _LR(max_iter=3000)).fit(F[tr0], y0[tr0]).score(F[te0], y0[te0])), 3)
g = {int(k): v for k, v in need('acc_by_n', dict).items()}
assert sorted(g) == [4, 8, 16, 32], f'Ключи: {sorted(g)}.'
assert all(close(g[k], w[k], 0.006) for k in w), f'acc_by_n = {g}, а нужно {w}.'
ne = min([k for k in w if w[k] > 0.93], default=None)
assert need('n_enough') == ne, f'n_enough = {need("n_enough")}, а нужно {ne}.'
```

### hint
Генератор создавайте заново внутри цикла: `np.random.default_rng(0).normal(size=(n, 5, 5))` — тогда первые фильтры одинаковы во всех вариантах, как в эталоне.

### hint
Цикл по `n`; внутри — веса, признаки, модель, `score`. `min([n for n in acc_by_n if acc_by_n[n] > 0.93])`.

### solution
```python
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

acc_by_n = {}
for n in [4, 8, 16, 32]:
    F = random_conv_features(X, np.random.default_rng(0).normal(size=(n, 5, 5)))
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(F[tr], y[tr])
    acc_by_n[n] = round(m.score(F[te], y[te]), 3)
n_enough = min([n for n in acc_by_n if acc_by_n[n] > 0.93])
print(acc_by_n, n_enough)
```

### explain
Четырёх случайных фильтров мало (около 0.86 — даже хуже наших продуманных), к 16 — около 0.94, дальше рост замедляется. Больше фильтров — больше признаков и дольше расчёт. Обученная сеть получает то же качество гораздо меньшим числом фильтров, потому что они подобраны под задачу.

## task: rand-light | Случайные фильтры и вечерний свет | star

Проверьте признаки из 16 случайных фильтров на тусклых кадрах (`X[te] * 0.7`) — с нормировкой кадров перед фильтрами и без. Нормировка кадра: вычесть его среднее, разделить на его стандартное отклонение (форма `(n, 32, 32)` сохраняется). Модель — `StandardScaler` + `LogisticRegression(max_iter=3000)`, веса — `np.random.default_rng(0).normal(size=(16, 5, 5))`. Сохраните `res` — словарь `{"без нормировки": (обычный, тусклый), "с нормировкой": (обычный, тусклый)}` (3 знака).

### setup
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
def random_conv_features(Z, W, s=4):
    out = []
    for w in W:
        f = np.maximum(np.stack([ndi.correlate(z, w, mode="nearest") for z in Z]), 0)
        n = len(Z)
        out.append(f.reshape(n, 32 // s, s, 32 // s, s).max(axis=(2, 4)).reshape(n, -1))
    return np.hstack(out)
```

### starter
```python
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

W = np.random.default_rng(0).normal(size=(16, 5, 5))

def norm_frames(Z):
    ...

```

### check
```python
import numpy as _np
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
X0, y0, tr0, te0, rcf = need('X'), need('y'), need('tr'), need('te'), need('random_conv_features')
W = _np.random.default_rng(0).normal(size=(16, 5, 5))
nf = lambda Z: (Z - Z.mean(axis=(1, 2), keepdims=True)) / Z.std(axis=(1, 2), keepdims=True)
def _run(prep):
    m = _mp(_SS(), _LR(max_iter=3000)).fit(rcf(prep(X0[tr0]), W), y0[tr0])
    return (round(float(m.score(rcf(prep(X0[te0]), W), y0[te0])), 3), round(float(m.score(rcf(prep(X0[te0] * 0.7), W), y0[te0])), 3))
w = {'без нормировки': _run(lambda Z: Z), 'с нормировкой': _run(nf)}
g = need('res', dict)
assert set(g) == set(w), f'Ключи: {list(g)}.'
assert all(close(g[k][i], w[k][i], 0.006) for k in w for i in range(2)), f'res = {g}, а нужно {w}.'
```

### hint
Нормировка кадров здесь сохраняет форму `(n, 32, 32)` — фильтрам нужны картинки. Среднее и отклонение — по осям 1 и 2.

### hint
`(Z - Z.mean(axis=(1, 2), keepdims=True)) / Z.std(axis=(1, 2), keepdims=True)`. Нормируйте и обучающие, и тестовые, и тусклые кадры — одинаково.

### hint
Удобна функция `run(prep)`, которая принимает функцию подготовки (`lambda Z: Z` или `norm_frames`) и возвращает пару точностей.

### solution
```python
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

W = np.random.default_rng(0).normal(size=(16, 5, 5))

def norm_frames(Z):
    return (Z - Z.mean(axis=(1, 2), keepdims=True)) / Z.std(axis=(1, 2), keepdims=True)

def run(prep):
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    m.fit(random_conv_features(prep(X[tr]), W), y[tr])
    normal = m.score(random_conv_features(prep(X[te]), W), y[te])
    dim = m.score(random_conv_features(prep(X[te] * 0.7), W), y[te])
    return round(normal, 3), round(dim, 3)

res = {"без нормировки": run(lambda Z: Z), "с нормировкой": run(norm_frames)}
print(res)
```

### explain
Без нормировки тусклые кадры ломают и эти признаки (около 0.64 вместо 0.94): отклики фильтров пропорциональны яркости, а модель помнит дневной масштаб. С нормировкой разница между обычными и тусклыми кадрами исчезает — ценой пары пунктов на обычных кадрах (около 0.91): нормировка заодно стирает полезную информацию об абсолютной яркости. Устойчивость часто стоит немного точности. Вход нормируют и в больших сетях: `weights.transforms()` у ResNet вычитает средние и делит на разбросы каналов — правда, общие для всех фото ImageNet, а не свои у каждого кадра. От перепадов освещения там спасает аугментация яркости и контраста при обучении.

## task: out-size | Размер выхода слоя | base

Напишите `out_size(n, k, pad=0, stride=1)` — размер стороны выхода свёртки (или пулинга) для входа `n × n`, окна `k`, дополнения `pad` с каждой стороны и шага `stride`: `(n + 2·pad − k) // stride + 1`. Посчитайте `sizes` — список размеров после каждого слоя сети из урока для входа 32: свёртка 3 (`pad=1`), пулинг 2 (`stride=2`), свёртка 3 (`pad=1`), пулинг 2 (`stride=2`), свёртка 3 (`pad=1`). В `no_pad` — то же, но все свёртки без дополнения.

### starter
```python
def out_size(n, k, pad=0, stride=1):
    ...

```

### check
```python
f = need('out_size')
assert f(5, 3) == 3 and f(32, 3, pad=1) == 32 and f(32, 2, stride=2) == 16 and f(7, 3, stride=2) == 3, 'out_size: (n + 2·pad − k) // stride + 1.'
assert need('sizes', list) == [32, 16, 16, 8, 8], f'sizes = {need("sizes")}.'
assert need('no_pad', list) == [30, 15, 13, 6, 4], f'no_pad = {need("no_pad")}.'
```

### hint
Пулинг 2 × 2 — это окно `k=2` с шагом `stride=2` и без дополнения.

### hint
Цепочка: начните с `n = 32`, на каждом слое `n = out_size(n, ...)` и добавляйте `n` в список.

### hint
```python
n, sizes = 32, []
for k, pad, stride in [(3, 1, 1), (2, 0, 2), (3, 1, 1), (2, 0, 2), (3, 1, 1)]:
    n = out_size(n, k, pad, stride)
    sizes.append(n)
```

### solution
```python
def out_size(n, k, pad=0, stride=1):
    return (n + 2 * pad - k) // stride + 1

def chain(layers, n=32):
    out = []
    for k, pad, stride in layers:
        n = out_size(n, k, pad, stride)
        out.append(n)
    return out

sizes = chain([(3, 1, 1), (2, 0, 2), (3, 1, 1), (2, 0, 2), (3, 1, 1)])
no_pad = chain([(3, 0, 1), (2, 0, 2), (3, 0, 1), (2, 0, 2), (3, 0, 1)])
print(sizes, no_pad)
```

### explain
Без дополнения каждая свёртка 3 × 3 «съедает» по пикселю с каждой стороны, и к последнему слою от 32 остаётся 4. В глубоких сетях это быстро съело бы всю картинку, поэтому почти всегда ставят `padding` так, чтобы свёртка сохраняла размер, а уменьшение делал только пулинг или шаг. Формулу `(n + 2p − k) // s + 1` полезно помнить: ошибка «size mismatch» в PyTorch почти всегда означает, что размер на каком-то слое посчитан не так, как ожидает следующий.

## task: receptive | Рецептивное поле | base

Напишите `receptive_field(layers)` как в уроке: `layers` — список пар `(вид, k)`, где вид `"conv"` (свёртка k × k с шагом 1) или `"pool"` (пулинг k × k с шагом k). Посчитайте `rf_lesson` — поле для сети из урока, `rf_no_pool` — для пяти свёрток 3 подряд без пулингов и `n_convs_needed` — сколько свёрток 3 подряд (без пулингов) нужно, чтобы поле стало не меньше 32.

### starter
```python
def receptive_field(layers):
    rf, jump = 1, 1
    ...
    return rf

```

### check
```python
f = need('receptive_field')
assert f([('conv', 3)]) == 3 and f([('conv', 3), ('conv', 3)]) == 5 and f([('conv', 3), ('pool', 2), ('conv', 3)]) == 8, 'Проверьте формулу: свёртка добавляет (k − 1)·jump, пулинг ещё и умножает jump на k.'
assert need('rf_lesson') == 18, f'rf_lesson = {need("rf_lesson")}.'
assert need('rf_no_pool') == 11, f'rf_no_pool = {need("rf_no_pool")}.'
assert need('n_convs_needed') == 16, f'n_convs_needed = {need("n_convs_needed")}.'
```

### hint
Каждый слой расширяет поле на `(k − 1) * jump`. После пулинга `jump` умножается на `k`.

### hint
Число свёрток подберите циклом `while`: добавляйте по `("conv", 3)`, пока поле меньше 32.

### hint
```python
n = 0
while receptive_field([("conv", 3)] * n) < 32:
    n += 1
```

### solution
```python
def receptive_field(layers):
    rf, jump = 1, 1
    for kind, k in layers:
        rf += (k - 1) * jump
        if kind == "pool":
            jump *= k
    return rf

rf_lesson = receptive_field([("conv", 3), ("pool", 2), ("conv", 3), ("pool", 2), ("conv", 3)])
rf_no_pool = receptive_field([("conv", 3)] * 5)
n_convs_needed = 0
while receptive_field([("conv", 3)] * n_convs_needed) < 32:
    n_convs_needed += 1
print(rf_lesson, rf_no_pool, n_convs_needed)
```

### explain
Без пулинга каждая свёртка 3 × 3 расширяет поле всего на 2 пикселя: чтобы «увидеть» весь кадр 32 × 32, понадобилось бы 16 слоёв. С двумя пулингами три свёртки уже видят 18 × 18 — больше половины кадра. Это вторая (помимо экономии вычислений) причина ставить пулинг: он позволяет глубоким слоям смотреть на большие части картинки при небольшом числе слоёв.

## task: pool-size | Пулинг против сдвига | plus

Повторите разбор из урока для пулинга `s` из `[4, 8, 32]` на 16 случайных фильтрах (функция `features(Z, s)` и разбиение — в заготовке). Сохраните `res` — DataFrame с индексом `s` и столбцами `n_features`, `test`, `shifted` (3 знака; сдвиг — `np.roll(X[te], 4, axis=2)`), `best_test` — `s` с лучшей точностью на обычном тесте и `most_robust` — `s` с наименьшим падением от сдвига.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
W = np.random.default_rng(0).normal(size=(16, 5, 5))
def features(Z, s):
    out = []
    for w in W:
        f = np.maximum(np.stack([ndi.correlate(z, w, mode="nearest") for z in Z]), 0)
        out.append(f.reshape(len(Z), 32 // s, s, 32 // s, s).max(axis=(2, 4)).reshape(len(Z), -1))
    return np.hstack(out)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

X_shift = np.roll(X[te], 4, axis=2)
rows = []

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
X0, y0, tr0, te0, ft = need('X'), need('y'), need('tr'), need('te'), need('features')
Xs = _np.roll(X0[te0], 4, axis=2)
w = {}
for s_ in [4, 8, 32]:
    m = _mp(_SS(), _LR(max_iter=3000)).fit(ft(X0[tr0], s_), y0[tr0])
    w[s_] = (16 * (32 // s_) ** 2, round(m.score(ft(X0[te0], s_), y0[te0]), 3), round(m.score(ft(Xs, s_), y0[te0]), 3))
r = need('res', _pd.DataFrame)
assert sorted(int(i) for i in r.index) == [4, 8, 32] and {'n_features', 'test', 'shifted'} <= set(r.columns), f'res: индекс 4, 8, 32; столбцы n_features, test, shifted. Сейчас {list(r.index)}, {list(r.columns)}.'
for s_, (nf, t, sh) in w.items():
    assert int(r.loc[s_, 'n_features']) == nf and close(r.loc[s_, 'test'], t, 0.006) and close(r.loc[s_, 'shifted'], sh, 0.006), f'Для s={s_}: {dict(r.loc[s_])}, а нужно {nf}, {t}, {sh}.'
assert int(need('best_test')) == max(w, key=lambda k: w[k][1]), f'best_test = {need("best_test")}.'
assert int(need('most_robust')) == min(w, key=lambda k: w[k][1] - w[k][2]), f'most_robust = {need("most_robust")}.'
```

### hint
Для каждого `s`: признаки обучения, обычного и сдвинутого теста — все через `features(..., s)`; модель обучается один раз на обучении.

### hint
Число признаков: 16 фильтров × `(32 // s) ** 2` чисел от каждого.

### hint
`res = pd.DataFrame(rows).set_index("s")`; самый устойчивый — `(res["test"] - res["shifted"]).idxmin()`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

X_shift = np.roll(X[te], 4, axis=2)
rows = []
for s in [4, 8, 32]:
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(features(X[tr], s), y[tr])
    rows.append({"s": s, "n_features": 16 * (32 // s) ** 2,
                 "test": round(m.score(features(X[te], s), y[te]), 3),
                 "shifted": round(m.score(features(X_shift, s), y[te]), 3)})
res = pd.DataFrame(rows).set_index("s")
best_test = int(res["test"].idxmax())
most_robust = int((res["test"] - res["shifted"]).idxmin())
print(res, best_test, most_robust)
```

### explain
Лучший на обычном тесте и самый устойчивый — разные варианты. Это типичный компромисс «точность против устойчивости», и выбирать между ними должна задача: если камеру никогда не двигают, берите пулинг 4; если сдвиги неизбежны, нужен больший пулинг или — лучше — аугментация сдвигами и глубокая сеть, у которой есть и детали, и глобальный пулинг в конце.
