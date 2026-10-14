---
title: "PyTorch: то же самое, но в промышленном масштабе"
files: [guests_churn.csv]
lead: "Нейросети на практике пишут на PyTorch. Он делает за вас самое трудоёмкое из обратного прохода — считает градиенты автоматически — и умеет обучать сети на видеокарте. Разбираем, как наш numpy-код превращается в PyTorch: тензоры, автоматические градиенты, класс сети `nn.Module`, цикл обучения и сохранение весов."
recap:
  - "Тензор (`torch.tensor`) — массив numpy, который умеет запоминать операции и считать градиенты."
  - "`loss.backward()` — автоматический обратный проход: градиенты всех весов появляются в `.grad`."
  - "`nn.Module` описывает сеть, `nn.Linear(n_in, n_out)` — слой X @ W + b, `nn.ReLU()` — активация."
  - "Цикл обучения: `optimizer.zero_grad()` → прогноз → `loss` → `loss.backward()` → `optimizer.step()`."
  - "`torch.from_numpy(a)` делит память с массивом, `torch.tensor(a, dtype=torch.float32)` — копия. Слои PyTorch ждут float32; назад в numpy — `t.detach().cpu().numpy()`, одно число — `t.item()`."
  - "Сеть описывают классом-наследником `nn.Module`: слои — в `__init__` (после `super().__init__()`), порядок вычислений — в `forward`. Веса `nn.Linear` хранятся как выходы × входы."
---

## Почему PyTorch

В уроке «Обучение сети: обратное распространение ошибки» мы писали обратный проход руками: для двух слоёв это 4 строки, для сети из 50 слоёв — невозможно. PyTorch решает три задачи:

1. **автоматические градиенты** — вы пишете только прямой проход, обратный PyTorch строит сам;
2. **готовые слои и оптимизаторы** — `nn.Linear`, `nn.Conv2d`, `Adam` и сотни других;
3. **видеокарта** — те же операции на GPU в десятки раз быстрее.

::: note
PyTorch не работает в браузере, поэтому код этого урока на PyTorch показан без кнопки «Запустить». Чтобы попробовать его, поставьте библиотеку в свой проект (глава 2): `uv add torch` и запустите код в Jupyter. Задачи урока — на numpy: они про те же идеи, и их можно проверить прямо здесь.

К главе есть и готовый блокнот с полной сетью на PyTorch, но открывать его лучше после урока «Dropout, BatchNorm и smoke-test»: в нём уже используются мини-батчи, dropout, BatchNorm и smoke-test, которые объясняются в двух следующих уроках. Ссылка и описание — в конце того урока.
:::

## Тензоры и автоматические градиенты

Тензор — это массив numpy с одним дополнительным умением: если попросить (`requires_grad=True`), он запоминает, какие операции с ним делали, и может посчитать производные.

```python static
import torch

w = torch.tensor(5.0, requires_grad=True)
km = torch.tensor([1.0, 2.0, 3.0, 4.5, 6.0])
minutes = torch.tensor([18.0, 25.0, 34.0, 44.0, 55.0])

loss = ((w * km - minutes) ** 2).mean()     # потеря из главы 10
loss.backward()                              # обратный проход — автоматически
print(w.grad)                                # tensor(-138.7000) — та же производная, что мы считали руками
```

**Что здесь происходит:**

- `torch.tensor(5.0, requires_grad=True)` — число-параметр, за которым PyTorch будет следить.
- `loss = ((w * km - minutes) ** 2).mean()` — обычная формула, но каждый шаг PyTorch записывает в «граф вычислений».
- `loss.backward()` — проход по графу назад по цепному правилу; результат кладётся в `w.grad`.

Сравните с главой 10: там мы вывели формулу $\operatorname{mean}\big(2 \cdot (w \cdot x - y) \cdot x\big)$ и получили −138.7. Здесь формулу никто не писал — PyTorch прошёл по цепочке операций назад сам.

::: note Практика — в своём блокноте
В браузере PyTorch не запускается, поэтому задач на этот раздел здесь нет — проверьте автоматический градиент у себя (`uv add torch`, глава 2):

1. Выполните код выше и сравните `w.grad` с −138.7 — значением, посчитанным по формуле в главе 10.
2. Не обнуляя градиент, ещё раз посчитайте `loss` и вызовите `loss.backward()`. В `w.grad` окажется −277.4: PyTorch **сложил** два градиента. Отсюда `optimizer.zero_grad()` в каждом шаге обучения (раздел ниже).
3. Возьмите `w = torch.tensor(9.0, requires_grad=True)` — градиент станет −26.3: ближе к минимуму потеря меняется медленнее.

Ручную проверку градиента числами (центральная разность) вы уже делали в задаче «Проверка формулы p − y» урока «Обучение сети: обратное распространение ошибки» — это тот же приём, которым проверяют и автоматический градиент.
:::

## Тензоры и numpy: туда и обратно

**Зачем.** Данные «Зерна» приходят в pandas и numpy, сеть работает с тензорами, а прогнозы снова нужны в DataFrame — для отчёта или выгрузки в базу. На этих переходах ошибаются чаще, чем в самой сети: тип чисел не тот, тензор «застрял» на видеокарте или массив неожиданно меняется вместе с тензором.

::: tip Аналогия
Есть два способа поделиться таблицей с коллегой: дать ссылку на общий документ или отправить копию файлом. По ссылке коллега видит все ваши правки, копия живёт своей жизнью. `torch.from_numpy` — это ссылка на ту же память, `torch.tensor(...)` — копия. Отличие: «по ссылке» нельзя поменять тип чисел — для float32 из float64 всё равно нужна копия.
:::

**Игрушечный пример руками** — то же явление в чистом numpy, на нём можно проверить себя прямо здесь. `np.asarray` не копирует массив, если он уже подходящий, а `np.array` копирует:

::: predict
```python static
import numpy as np
a = np.array([1.0, 2.0, 3.0])
b = np.asarray(a)        # тот же массив, что a
c = np.array(a)          # копия
a[0] = 10
print(b[0], c[0])
```

- `1.0 1.0`
- [x] `10.0 1.0`
- `10.0 10.0`

Почему: `b` смотрит в ту же память, что `a`, и видит правку; `c` — независимая копия, сделанная до правки.
:::

В PyTorch то же самое:

```python static
import numpy as np
import torch

a = np.array([1.5, 2.0, 3.0])                      # float64 — так numpy хранит дроби по умолчанию
t_shared = torch.from_numpy(a)                     # общая память с a, тип float64
t_copy = torch.tensor(a, dtype=torch.float32)      # копия, тип float32
a[0] = 100.0
print(t_shared[0].item(), t_copy[0].item())        # 100.0 1.5
print(t_shared.dtype, t_copy.dtype, torch.tensor([1.0]).dtype)
# torch.float64 torch.float32 torch.float32

w = torch.tensor([0.5, -1.0], requires_grad=True)
loss = (w * 2).sum()
loss.backward()
print(w.detach().numpy(), w.grad.numpy())          # [ 0.5 -1. ] [2. 2.]
```

**Что здесь происходит:**

- `torch.from_numpy(a)` — тензор поверх той же памяти: правка `a[0]` видна в `t_shared`. Тип сохраняется: float64.
- `torch.tensor(a, dtype=torch.float32)` — новая копия в типе float32, по умолчанию в PyTorch все слои и веса — float32.
- `.item()` — число из тензора с одним элементом в обычный Python-`float` (для печати и журналов).
- `w.detach().numpy()` — тензор с `requires_grad=True` напрямую в numpy не превращается: сначала `.detach()` («отцепить от графа вычислений»). Тензор на видеокарте — ещё и `.cpu()`: `t.detach().cpu().numpy()`.

| откуда → куда | как | копия? |
|---|---|---|
| numpy → тензор | `torch.from_numpy(a)` | нет, общая память, тип прежний |
| numpy или pandas → тензор | `torch.tensor(df[cols].to_numpy(), dtype=torch.float32)` | да |
| тензор → numpy | `t.numpy()` | нет — только для тензора на процессоре и без градиентов |
| тензор с градиентом или на GPU → numpy | `t.detach().cpu().numpy()` | на GPU — да |
| тензор из одного числа → Python | `t.item()` | — |

::: figure nn-tensor-memory
Пример из кода выше: `t_shared` смотрит в ту же память, что и массив `a`, поэтому правка `a[0]` видна в нём; `t_copy` — отдельная копия во float32, её правка не касается. Внизу — путь тензора с градиентом с видеокарты обратно в numpy.
:::

**Почему float32, а не float64.** float32 занимает вдвое меньше памяти и на видеокартах считается в разы быстрее, а точности в 7 значащих цифр сетям хватает: шум от батчей всё равно больше. Посмотрим, что теряется:

```python
import numpy as np
x64 = np.array([0.1, 123456789.12, 16_777_217.0])
x32 = x64.astype(np.float32)
print(x64.dtype, x64.nbytes, "байт;", x32.dtype, x32.nbytes, "байт")
print([float(v) for v in x32])
```

**Что получилось:** три числа занимают 24 байта во float64 и 12 во float32. Цена — около 7 значащих цифр: 0.1 хранится как 0.10000000149…, выручка 123 456 789.12 превратилась в 123 456 792, а 16 777 217 — в 16 777 216: float32 хранит 24 двоичных разряда значащих цифр, поэтому все целые он записывает точно только до $2^{24} = 16\,777\,216$, а дальше — через одно. Для весов сети это неважно, для денег в отчёте — критично: суммы и итоги считайте в pandas во float64, в тензоры отдавайте признаки.

::: warn Типичные ошибки
- **`RuntimeError: mat1 and mat2 must have the same dtype, but got Double and Float`.** Признаки пришли из numpy во float64 (`Double`), а веса слоя — float32 (`Float`). Лечится `torch.tensor(X, dtype=torch.float32)` или `X.float()`.
- **`RuntimeError: Can't call numpy() on Tensor that requires grad`.** Нужно `t.detach().numpy()`; для прогнозов удобнее сразу считать в `with torch.no_grad():`.
- **Массив «сам» поменялся.** После `torch.from_numpy(a)` операции на месте над тензором (`t += 1`, `t[0] = …`) меняют и `a`. Если массив ещё нужен — берите копию: `torch.tensor(a)`.
:::

{{practice: float32}}

## Наша numpy-сеть на PyTorch

Возьмём сеть с полумесяцами из урока «Обучение сети: обратное распространение ошибки» — 2 входа, 16 нейронов с ReLU, сигмоида на выходе — и перепишем её на PyTorch:

```python static
import torch
from torch import nn
from sklearn.datasets import make_moons

X, y = make_moons(400, noise=0.2, random_state=0)
X = torch.tensor(X, dtype=torch.float32)
y = torch.tensor(y, dtype=torch.float32)

torch.manual_seed(0)
model = nn.Sequential(
    nn.Linear(2, 16),      # X @ W1 + b1
    nn.ReLU(),
    nn.Linear(16, 1),      # H @ w2 + b2 — логит (оценка до сигмоиды)
)
loss_fn = nn.BCEWithLogitsLoss()            # сигмоида + логистическая потеря в одном
optimizer = torch.optim.SGD(model.parameters(), lr=0.5)

for step in range(2000):
    optimizer.zero_grad()                   # обнулить градиенты прошлого шага
    logits = model(X).squeeze(1)            # прямой проход
    loss = loss_fn(logits, y)
    loss.backward()                         # обратный проход
    optimizer.step()                        # шаг спуска: w -= lr * w.grad

acc = ((logits > 0).float() == y).float().mean()
print(f"потеря {loss.item():.3f}, верных {acc.item():.3f}")
```

Построчное соответствие с нашим numpy-кодом:

| numpy | PyTorch |
|---|---|
| `W1 = rng.normal(...) * 0.5` | `nn.Linear(2, 16)` (инициализация внутри) |
| `np.maximum(0, Z1)` | `nn.ReLU()` |
| `1 / (1 + np.exp(-z))` + логистическая потеря | `nn.BCEWithLogitsLoss()` |
| четыре строки градиентов (`d2`, `g_w2, g_b2`, `dH`, `g_W1, g_b1`) | `loss.backward()` |
| `W1 -= lr * g_W1` и т. д. | `optimizer.step()` |

`optimizer.zero_grad()` нужен потому, что PyTorch **складывает** градиенты от вызова к вызову (так удобно в сложных случаях). Забыть его — частая ошибка: градиенты копятся, и обучение идёт вразнос. Как это выглядит на числах, увидите в задаче «Забытый zero_grad».

::: figure nn-torch-loop
Пять вызовов одного шага обучения в PyTorch и что им соответствует в нашем numpy-коде. Обрезка градиента, если она нужна, встаёт между `backward()` и `step()`.
:::

::: tip
Вместо `torch.optim.SGD` почти всегда берут `torch.optim.Adam(model.parameters(), lr=1e-3)` — тот же Adam, что внутри `MLPClassifier`. Он менее чувствителен к выбору шага.
:::

{{practice: p-torch-order, zero-grad}}

## Сеть как класс: nn.Module

**Зачем.** `nn.Sequential` подходит, пока сеть — прямая цепочка слоёв. Но часто нужна сеть сложнее — например, общий скрытый слой и отдельные выходы («головы») для минут доставки, ухода гостя и его покупок; о таких выходах — урок «Softmax, выход под задачу и мини-батчи». Такую — и любую нестандартную — сеть описывают классом, наследником `nn.Module`. Так написан почти весь код на PyTorch, который вы встретите.

::: tip Аналогия
Класс сети похож на техкарту напитка: в шапке перечислено оборудование и ингредиенты (`__init__` — слои с их весами), а ниже — порядок действий (`forward` — как из входа получить ответ). Одна техкарта — сколько угодно чашек. Разница в одном: «ингредиенты» сети, веса, меняются при обучении, а техкарта — нет.
:::

**Игрушечный пример: тот же каркас на numpy.** Класс из главы 9 с `fit` и `predict` вы уже писали; у сети всё устроено так же — в конструкторе создаются веса, метод `forward` считает прогноз, `parameters` отдаёт список всех обучаемых массивов:

```python
import numpy as np

class NumpyNet:
    def __init__(self, n_in, hidden, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(size=(n_in, hidden)) * np.sqrt(2 / n_in)    # He для ReLU (урок «Граф вычислений, инициализация и обрезка градиента»)
        self.b1 = np.zeros(hidden)
        self.w2 = rng.normal(size=hidden) * np.sqrt(1 / hidden)
        self.b2 = np.zeros(1)

    def forward(self, X):
        H = np.maximum(0, X @ self.W1 + self.b1)
        return H @ self.w2 + self.b2                                       # логит, без сигмоиды

    def parameters(self):
        return [self.W1, self.b1, self.w2, self.b2]

net = NumpyNet(n_in=8, hidden=16)
X = np.random.default_rng(1).normal(size=(5, 8))                          # 5 гостей, 8 признаков
print(net.forward(X).shape, sum(p.size for p in net.parameters()))
```

**Что здесь происходит:**

- `__init__` создаёт веса и кладёт их в атрибуты `self.…` — они живут вместе с объектом.
- `forward(X)` — прямой проход: из таблицы 5 × 8 получается 5 логитов.
- `parameters()` — список всех обучаемых массивов: 8 · 16 + 16 + 16 + 1 = 161 число. Оптимизатору нужен именно такой список.

Оптимизатор обновляет только то, что вернул `parameters()`. Что в список не попало, не обучается, и никакой ошибки при этом нет:

::: predict
```python static
import numpy as np

class Net:
    def __init__(self):
        self.W1 = np.ones((3, 4))
        self.b1 = np.zeros(4)
    def parameters(self):
        return [self.W1]          # сдвиг b1 забыли

net = Net()
print(sum(p.size for p in net.parameters()))
```

- `16`
- [x] `12`
- `2`

Почему: в список попала только матрица 3 × 4, то есть 12 чисел. Сдвиги `b1` есть у объекта, но оптимизатор о них не узнает, и они навсегда останутся нулями. В PyTorch так же ведут себя слои, сложенные в обычный список вместо `nn.ModuleList` (см. «Типичные ошибки» ниже).
:::

На PyTorch — та же структура, но веса создают и регистрируют сами слои:

```python static
import torch
from torch import nn

class ChurnNet(nn.Module):
    def __init__(self, n_in, hidden=16, p_drop=0.2):
        super().__init__()                         # обязательно первой строкой
        self.layer1 = nn.Linear(n_in, hidden)
        self.drop = nn.Dropout(p_drop)
        self.out = nn.Linear(hidden, 1)

    def forward(self, x):
        h = torch.relu(self.layer1(x))
        return self.out(self.drop(h)).squeeze(1)   # логиты, форма (число гостей,)

model = ChurnNet(n_in=8)
print(model)
print(sum(p.numel() for p in model.parameters()))  # 161
for name, p in model.named_parameters():
    print(name, tuple(p.shape))
```

```text
ChurnNet(
  (layer1): Linear(in_features=8, out_features=16, bias=True)
  (drop): Dropout(p=0.2, inplace=False)
  (out): Linear(in_features=16, out_features=1, bias=True)
)
161
layer1.weight (16, 8)
layer1.bias (16,)
out.weight (1, 16)
out.bias (1,)
```

**Что здесь происходит:**

- `super().__init__()` подготавливает внутренности `nn.Module`; без неё присвоение `self.layer1 = …` падает.
- `nn.Dropout(p_drop)` — слой, который при обучении случайно обнуляет долю `p_drop` выходов скрытого слоя: так борются с переобучением. Весов у него нет, поэтому на число параметров он не влияет; подробно — в уроке «Dropout, BatchNorm и smoke-test», сейчас его можно пропустить.
- Каждый слой, записанный в атрибут, **регистрируется**: его веса попадают в `model.parameters()` и в `state_dict()` для сохранения.
- `forward` вызывают не напрямую, а через `model(x)` — так PyTorch заодно выполняет свою служебную работу.
- `layer1.weight` имеет форму (16, 8) — **выходы × входы**, наоборот по сравнению с нашим `W1` (8 × 16): слой считает `x @ W.T + b`. Число параметров то же — 161.

::: figure nn-module-anatomy
Две половины класса: в `__init__` слои записываются в атрибуты и регистрируются — их веса попадают в `model.parameters()` (те же 161 число, что напечатал код); `forward` описывает путь батча из n гостей от 8 признаков до n логитов.
:::

::: deep Если вы видели Keras
Keras — другая популярная библиотека для сетей; с версии 3 она умеет работать поверх PyTorch. Идеи те же, разница — в том, сколько кода пишете вы:

| Keras | PyTorch |
|---|---|
| `keras.Sequential([...])` | `nn.Sequential(...)` или класс-наследник `nn.Module` |
| `layers.Dense(16, activation="relu")` | `nn.Linear(n_in, 16)` + `nn.ReLU()`; число входов пишут явно |
| `layers.Dropout(0.3)`, `layers.BatchNormalization()` | `nn.Dropout(0.3)`, `nn.BatchNorm1d(n)` |
| `model.compile(optimizer="adam", loss="binary_crossentropy")` | `opt = torch.optim.Adam(model.parameters())`, `loss_fn = nn.BCEWithLogitsLoss()` |
| `model.fit(X, y, epochs=10, batch_size=32, validation_data=...)` | свой цикл: `DataLoader`, эпохи, `zero_grad` → `backward` → `step`, оценка на валидации |
| `callbacks.EarlyStopping(patience=5)` | своя проверка в цикле: лучшая валидационная потеря и счётчик эпох без улучшения |
| `model.predict(X)` | `model.eval()` и `with torch.no_grad(): model(X)` |
| `model.summary()` | `print(model)` и `sum(p.numel() for p in model.parameters())` |
| `model.save("churn.keras")` | `torch.save(model.state_dict(), "churn.pt")` |

Главное отличие — `fit`: в PyTorch цикл обучения пишут сами. Это больше кода, зато всё видно: где считается потеря, когда валидация, что пишется в журнал. Ещё одна ловушка при переносе: в Keras выход часто заканчивают `activation="sigmoid"` и считают потерю по вероятностям, а в PyTorch последний слой оставляют без активации и берут потерю по логитам (урок «Softmax, выход под задачу и мини-батчи», раздел «Выход и потеря под тип задачи»).
:::

::: warn Типичные ошибки
- **Забыли `super().__init__()`.** Падает `AttributeError: cannot assign module before Module.__init__() call`.
- **Слои в обычном списке.** `self.layers = [nn.Linear(2, 4), nn.Linear(4, 1)]` — PyTorch не видит слои внутри списка: `model.parameters()` пуст (0 параметров вместо 17), оптимизатор ничего не обучает, ошибки нет. Нужен `nn.ModuleList([...])`.
- **Сигмоида в `forward` и `BCEWithLogitsLoss`.** Потеря применит сигмоиду второй раз: ошибки нет, но сеть учится хуже и медленнее. В `forward` возвращайте логиты, вероятности — `torch.sigmoid(model(x))` на прогнозе.
:::

{{practice: module-class}}

## Разберём вместе: сохранить и загрузить сеть

Обученную сеть сохраняют так же, как модель sklearn в главе 7, только в PyTorch принято сохранять не объект целиком, а **веса** — словарь «имя слоя → тензор» (`state_dict`):

```python static
torch.save(model.state_dict(), "moons_net.pt")      # только веса

model2 = nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 1))   # та же архитектура
model2.load_state_dict(torch.load("moons_net.pt"))
model2.eval()                                        # режим прогноза
with torch.no_grad():
    print(torch.equal(model(X), model2(X)))           # True
```

**Что здесь происходит:**

- `state_dict()` — только числа: веса и сдвиги. Архитектуру (какие слои и в каком порядке) нужно описать в коде заново — поэтому её хранят рядом с весами, например в паспорте модели (глава 15).
- `load_state_dict` — заливает сохранённые числа в новую сеть той же формы. Если архитектура отличается хотя бы размером слоя, будет ошибка про несовпадение форм.
- `torch.no_grad()` — режим без записи графа вычислений: прогноз быстрее и не тратит память.

::: note Практика — в блокноте
PyTorch в браузере не запускается, поэтому задачи на сохранение здесь нет. Потренируйтесь в своём блокноте:

1. Обучите сеть из раздела «Наша numpy-сеть на PyTorch», сохраните `state_dict` и загрузите его в новую сеть той же архитектуры — `torch.equal(...)` должен дать `True`.
2. Посмотрите, что лежит в файле: `list(model.state_dict())` — четыре тензора `0.weight`, `0.bias`, `2.weight`, `2.bias` (номера — позиции слоёв в `nn.Sequential`, у `ReLU` весов нет), всего 65 чисел.
3. Попробуйте загрузить веса в сеть с 32 нейронами вместо 16 — получите `RuntimeError: … size mismatch for 0.weight: copying a param with shape torch.Size([16, 2]) …`. Так выглядит ошибка «архитектура не та».

Сохранение лучших весов во время обучения вы увидите в готовом блокноте главы (функция `train_loop`, раздел 4; ссылка — в конце урока «Dropout, BatchNorm и smoke-test»): она запоминает `state_dict` лучшей эпохи и в конце загружает его обратно в модель.
:::

{{practice: state-shapes}}

## Практика

## task: p-torch-order | Порядок шагов обучения | warmup

Соберите в правильном порядке шаги обучения в духе PyTorch — здесь они записаны на numpy, чтобы код можно было запустить.

### parsons
```python
import numpy as np
x = np.array([1.0, 2.0, 3.0]); y = np.array([2.0, 4.0, 6.0])
w, grad, lr = 0.0, 0.0, 0.05
for step in range(100):
    grad = 0.0
    pred = w * x
    loss = np.mean((pred - y) ** 2)
    grad = np.mean(2 * (pred - y) * x)
    w = w - lr * grad
print(round(w, 2))
```

### check
```python
assert _lines == ['2.0'], f'Сейчас: {_lines}.'
assert _code.index('grad = 0.0\n    pred') >= 0 if 'grad = 0.0\n    pred' in _code else False, 'Обнуление градиента (zero_grad) — первым шагом в цикле.'
```

### hint
Порядок как в PyTorch: обнулить градиент → прогноз → потеря → градиент (backward) → шаг (step).

### hint
Шаг нельзя сделать до того, как посчитан градиент, а градиент — до того, как посчитана потеря.

## task: zero-grad | Забытый zero_grad | base

Самая частая ошибка в цикле PyTorch — забытый `optimizer.zero_grad()`: градиенты копятся, и каждый шаг тянет за собой сумму всех прошлых. Воспроизведём её на numpy. В заготовке — минуты доставки по расстоянию из раздела «Тензоры и автоматические градиенты» и функция `run(zero_grad, lr, steps)`: один вес `w`, старт с 5.0, градиент MSE **прибавляется** к переменной `grad` (`+=`, как в PyTorch). Допишите в ней одну строку: если `zero_grad` истинно, в начале каждого шага обнулите `grad`. Функция возвращает `(w, losses)` — вес после обучения и список потерь до каждого шага.

Запустите `run(True)` и `run(False)` с `lr=0.01`, `steps=30`. Сохраните:

- `w_ok`, `w_bug` — веса после обучения с обнулением и без (3 знака);
- `final_ok`, `final_bug` — последние потери в списках (1 знак);
- `first_up` — номер шага (с нуля), на котором потеря без обнуления впервые **выросла** по сравнению с предыдущим шагом.

### starter
```python
import numpy as np
km = np.array([1.0, 2.0, 3.0, 4.5, 6.0])
minutes = np.array([18.0, 25.0, 34.0, 44.0, 55.0])

def run(zero_grad, lr=0.01, steps=30):
    w, grad = 5.0, 0.0
    losses = []
    for step in range(steps):
        # здесь — обнуление grad, если zero_grad
        pred = w * km
        losses.append(float(np.mean((pred - minutes) ** 2)))
        grad += np.mean(2 * (pred - minutes) * km)    # как loss.backward(): градиент копится
        w = w - lr * grad                             # как optimizer.step()
    return w, losses

```

### check
```python
import numpy as _np
k0 = _np.array([1.0, 2.0, 3.0, 4.5, 6.0]); m0 = _np.array([18.0, 25.0, 34.0, 44.0, 55.0])
def _run(z):
    w, g = 5.0, 0.0; L = []
    for _ in range(30):
        if z:
            g = 0.0
        p = w * k0; L.append(float(_np.mean((p - m0) ** 2)))
        g += _np.mean(2 * (p - m0) * k0); w = w - 0.01 * g
    return w, L
f = need('run')
wo, lo = f(True)
assert close(wo, _run(True)[0], 0.001), f'run(True) даёт w = {wo:.3f}, а нужно {_run(True)[0]:.3f}: при zero_grad=True в начале каждого шага grad = 0.0.'
wb, lb = f(False)
assert close(wb, _run(False)[0], 0.001), f'run(False) даёт w = {wb:.3f}, а нужно {_run(False)[0]:.3f}: без обнуления код не должен меняться.'
assert close(need('w_ok'), round(_run(True)[0], 3), 0.0011) and close(need('w_bug'), round(_run(False)[0], 3), 0.0011), f'w_ok, w_bug = {need("w_ok")}, {need("w_bug")}.'
assert close(need('final_ok'), round(_run(True)[1][-1], 1), 0.051) and close(need('final_bug'), round(_run(False)[1][-1], 1), 0.051), f'final_ok, final_bug = {need("final_ok")}, {need("final_bug")}: последние элементы списков потерь, 1 знак.'
L = _run(False)[1]
fu = [k for k in range(1, len(L)) if L[k] > L[k - 1]][0]
assert need('first_up') == fu, f'first_up = {need("first_up")}, а нужно {fu}: первый k, для которого losses[k] > losses[k - 1], в запуске без обнуления.'
```

### hint
Одна строка в начале тела цикла: `if zero_grad: grad = 0.0` (можно в две строки с отступом). Остальной код не трогайте.

### hint
`w_ok, losses_ok = run(True)`, `w_bug, losses_bug = run(False)`. Первый рост: `[k for k in range(1, len(losses_bug)) if losses_bug[k] > losses_bug[k - 1]][0]`.

### solution
```python
import numpy as np
km = np.array([1.0, 2.0, 3.0, 4.5, 6.0])
minutes = np.array([18.0, 25.0, 34.0, 44.0, 55.0])

def run(zero_grad, lr=0.01, steps=30):
    w, grad = 5.0, 0.0
    losses = []
    for step in range(steps):
        if zero_grad:
            grad = 0.0
        pred = w * km
        losses.append(float(np.mean((pred - minutes) ** 2)))
        grad += np.mean(2 * (pred - minutes) * km)
        w = w - lr * grad
    return w, losses

w_ok, losses_ok = run(True)
w_bug, losses_bug = run(False)
w_ok, w_bug = round(w_ok, 3), round(w_bug, 3)
final_ok, final_bug = round(losses_ok[-1], 1), round(losses_bug[-1], 1)
first_up = [k for k in range(1, len(losses_bug)) if losses_bug[k] > losses_bug[k - 1]][0]
print(w_ok, w_bug, final_ok, final_bug, first_up)
```

### explain
С обнулением потеря ровно падает с 368.4 до 26.1, вес приходит к 9.936. Без обнуления первые три шага выглядят нормально (368.4 → 203.1 → 45.2), а на шаге 3 потеря растёт до 59.8: накопленный градиент — сумма всех прошлых — продолжает толкать вес вправо, хотя минимум уже пройден. Дальше потеря качается между ≈ 26 и ≈ 394, и к 30-му шагу оказывается 389.1 при весе 13.994 — хуже, чем на старте. Симптом в журнале обучения узнаваемый: потеря сначала падает, а потом начинает «качаться» с растущим размахом. Первое, что проверять в этом случае, — есть ли `optimizer.zero_grad()` в начале шага.

## task: float32 | float64 → float32 | warmup

PyTorch по умолчанию работает во float32, а numpy и pandas отдают float64. Посмотрите, что меняется при переходе. В заготовке — признаки гостей `X64`. Сохраните:

- `X32` — та же матрица во float32 (`astype`);
- `ratio` — во сколько раз `X64` занимает больше байт, чем `X32` (`.nbytes`);
- `max_err` — наибольшее расхождение `|X64 − X32|` по всем клеткам, две значащие цифры: `float(f"{v:.2g}")`;
- `revenue32` — годовая выручка 123 456 789.12 рубля, записанная во float32 и возвращённая в обычный `float`, и `lost_rub` — на сколько рублей она отличается от исходной (2 знака).

### starter
```python
import numpy as np
import pandas as pd
g = pd.read_csv("guests_churn.csv")
X64 = g[["tenure_months", "visits_90d", "days_since_last", "delivery_share"]].to_numpy(float)

```

### check
```python
import numpy as _np
import pandas as _pd
_X = _pd.read_csv("guests_churn.csv")[["tenure_months", "visits_90d", "days_since_last", "delivery_share"]].to_numpy(float)
x32 = need('X32')
assert getattr(x32, 'dtype', None) == _np.float32, f'X32 должна быть во float32, сейчас dtype = {getattr(x32, "dtype", type(x32))}.'
assert x32.shape == _X.shape, f'Форма X32 {x32.shape}, а нужна {_X.shape}.'
assert close(need('ratio'), 2.0), f'ratio = {need("ratio")}: float64 — 8 байт на число, float32 — 4.'
me = float(f"{_np.abs(_X - _X.astype(_np.float32)).max():.2g}")
assert abs(need('max_err') / me - 1) < 0.01, f'max_err = {need("max_err")}, а нужно {me}. Разность считайте между X64 и X32 по модулю.'
r = float(_np.float32(123456789.12))
assert close(need('revenue32'), r), f'revenue32 = {need("revenue32")}, а нужно {r}: np.float32(...) и затем float(...).'
assert close(need('lost_rub'), round(r - 123456789.12, 2), 0.006), f'lost_rub = {need("lost_rub")}.'
```

### hint
Тип меняет `X64.astype(np.float32)`; размер в байтах — атрибут `.nbytes`. Расхождение — `np.abs(X64 - X32).max()`.

### hint
`revenue32 = float(np.float32(123456789.12))`, `lost_rub = round(revenue32 - 123456789.12, 2)`.

### solution
```python
import numpy as np
import pandas as pd
g = pd.read_csv("guests_churn.csv")
X64 = g[["tenure_months", "visits_90d", "days_since_last", "delivery_share"]].to_numpy(float)

X32 = X64.astype(np.float32)
ratio = X64.nbytes / X32.nbytes
max_err = float(f"{np.abs(X64 - X32).max():.2g}")
revenue32 = float(np.float32(123456789.12))
lost_rub = round(revenue32 - 123456789.12, 2)
print(ratio, max_err, revenue32, lost_rub)
```

### explain
Память — ровно вдвое меньше: 4 байта на число вместо 8. Признаки почти не пострадали: целые месяцы и визиты float32 хранит точно, а у долей доставки расхождение порядка $3 \cdot 10^{-8}$ — на прогноз сети это не влияет. А вот деньги: 123 456 789.12 рубля превратились в 123 456 792 — плюс 2.88 рубля из воздуха, копейки потеряны совсем. Поэтому суммы для отчётов считают в pandas во float64 (или в копейках целыми числами), а во float32 отдают сети только признаки.

## task: module-class | Сеть классом на numpy | base

Напишите класс `TinyNet` — сеть произвольной глубины в стиле `nn.Module`:

- `__init__(self, sizes, seed=0)` — `sizes` вроде `[4, 16, 8, 1]`; генератор `rng = np.random.default_rng(seed)` создаётся один раз, и для каждой пары соседних размеров `(a, b)` по порядку создаются веса `rng.normal(size=(a, b)) * np.sqrt(2 / a)` (He) и нулевые сдвиги длины `b`; храните их в списках `self.Ws` и `self.bs`;
- `forward(self, X)` — ReLU во всех слоях, кроме последнего; последний слой без активации; вернуть логиты формы `(число объектов,)`;
- `n_params(self)` — общее число весов и сдвигов.

Создайте `net = TinyNet([4, 16, 8, 1])` и примените к первым пяти гостям из стандартизованной матрицы `X` (она в заготовке). Сохраните `n_par`, `out_shape` — форму выхода и `p` — вероятности ухода этих гостей (сигмоида от логитов, 3 знака).

### starter
```python
import numpy as np
import pandas as pd
g = pd.read_csv("guests_churn.csv")
X = g[["tenure_months", "visits_90d", "days_since_last", "complaints"]].to_numpy(float)
X = (X - X.mean(axis=0)) / X.std(axis=0)

class TinyNet:
    def __init__(self, sizes, seed=0):
        rng = np.random.default_rng(seed)
        self.Ws, self.bs = [], []
        ...

    def forward(self, X):
        ...

    def n_params(self):
        ...

```

### check
```python
import numpy as _np
import pandas as _pd
_X = _pd.read_csv("guests_churn.csv")[["tenure_months", "visits_90d", "days_since_last", "complaints"]].to_numpy(float)
_X = (_X - _X.mean(axis=0)) / _X.std(axis=0)
def _ref(sizes, X, seed=0):
    r = _np.random.default_rng(seed); Ws, bs = [], []
    for a, b in zip(sizes[:-1], sizes[1:]):
        Ws.append(r.normal(size=(a, b)) * _np.sqrt(2 / a)); bs.append(_np.zeros(b))
    A = X
    for i, (W, b) in enumerate(zip(Ws, bs)):
        Z = A @ W + b; A = _np.maximum(0, Z) if i < len(Ws) - 1 else Z
    return A[:, 0], sum(W.size + b.size for W, b in zip(Ws, bs))
T = need('TinyNet')
small = T([4, 3, 1], seed=5)
zs, ns = _ref([4, 3, 1], _X[:7], 5)
assert small.n_params() == ns, f'Для sizes=[4, 3, 1] n_params() = {small.n_params()}, а нужно {ns}: веса a·b плюс b сдвигов на каждый слой.'
out = _np.asarray(small.forward(_X[:7]))
assert out.shape == (7,), f'forward должен возвращать логиты формы (число объектов,), сейчас {out.shape}. Последний столбец можно взять как A[:, 0].'
assert _np.allclose(out, zs), 'forward для sizes=[4, 3, 1] не совпал с эталоном. Проверьте порядок создания весов (W, затем следующий W — генератор один на все слои), He-масштаб np.sqrt(2 / a) и отсутствие ReLU на последнем слое.'
z5, n5 = _ref([4, 16, 8, 1], _X[:5])
assert need('n_par') == n5, f'n_par = {need("n_par")}, а нужно {n5}.'
assert tuple(need('out_shape')) == (5,), f'out_shape = {need("out_shape")}.'
assert _np.allclose(need('p'), (1 / (1 + _np.exp(-z5))).round(3), atol=1e-3), f'p = {need("p")}, а нужно {(1 / (1 + _np.exp(-z5))).round(3)}.'
```

### hint
В `__init__` — цикл `for a, b in zip(sizes[:-1], sizes[1:])`, внутри два `append`. В `forward` — цикл по слоям с `enumerate`, чтобы узнать, последний ли слой.

### hint
Внутри `forward`: `Z = A @ W + b`, затем `A = np.maximum(0, Z) if i < len(self.Ws) - 1 else Z`; в конце `return A[:, 0]`. Параметры: `sum(W.size + b.size for W, b in zip(self.Ws, self.bs))`.

### hint
После класса: `net = TinyNet([4, 16, 8, 1])`, `z = net.forward(X[:5])`, `p = (1 / (1 + np.exp(-z))).round(3)`.

### solution
```python
import numpy as np
import pandas as pd
g = pd.read_csv("guests_churn.csv")
X = g[["tenure_months", "visits_90d", "days_since_last", "complaints"]].to_numpy(float)
X = (X - X.mean(axis=0)) / X.std(axis=0)

class TinyNet:
    def __init__(self, sizes, seed=0):
        rng = np.random.default_rng(seed)
        self.Ws, self.bs = [], []
        for a, b in zip(sizes[:-1], sizes[1:]):
            self.Ws.append(rng.normal(size=(a, b)) * np.sqrt(2 / a))
            self.bs.append(np.zeros(b))

    def forward(self, X):
        A = X
        for i, (W, b) in enumerate(zip(self.Ws, self.bs)):
            Z = A @ W + b
            A = np.maximum(0, Z) if i < len(self.Ws) - 1 else Z
        return A[:, 0]

    def n_params(self):
        return sum(W.size + b.size for W, b in zip(self.Ws, self.bs))

net = TinyNet([4, 16, 8, 1])
z = net.forward(X[:5])
n_par = net.n_params()
out_shape = z.shape
p = (1 / (1 + np.exp(-z))).round(3)
print(n_par, out_shape, p)
```

### explain
225 параметров: 4·16 + 16 = 80, 16·8 + 8 = 136, 8·1 + 1 = 9. Сеть ещё не обучена, поэтому вероятности ухода у пяти гостей — 0.29…0.41: случайные веса дают случайные, но умеренные ответы, без 0 и 1 — так и должно быть при He-инициализации и стандартизованных признаках. Списки `self.Ws` и `self.bs` — numpy-аналог регистрации слоёв: всё, что лежит в них, попадает в `n_params()`, и оптимизатор знал бы, что обновлять. В PyTorch роль такого списка играет `nn.ModuleList`; если сложить слои в обычный Python-список, `model.parameters()` их не увидит. Последний слой без ReLU — иначе отрицательные логиты обнулялись бы, и вероятность никогда не опускалась бы ниже 0.5.

## task: state-shapes | Что лежит в state_dict | base

Напишите функцию `state_shapes(sizes)`, которая без PyTorch предсказывает содержимое `state_dict()` сети `nn.Sequential` из линейных слоёв с `nn.ReLU()` между ними. Например, для `sizes = [2, 16, 1]` это `nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 1))`, и функция должна вернуть словарь

`{"0.weight": (16, 2), "0.bias": (16,), "2.weight": (1, 16), "2.bias": (1,)}`.

Правила — из теории урока: ключ — позиция слоя в `nn.Sequential` и имя тензора; у `ReLU` весов нет, но позицию он занимает; форма весов `nn.Linear` — **выходы × входы**. Сохраните `shapes` — результат для `[8, 32, 16, 1]` и `n_total` — общее число чисел в нём.

### starter
```python
import numpy as np

def state_shapes(sizes):
    out = {}
    ...
    return out

```

### check
```python
f = need('state_shapes')
assert f([2, 16, 1]) == {"0.weight": (16, 2), "0.bias": (16,), "2.weight": (1, 16), "2.bias": (1,)}, f'state_shapes([2, 16, 1]) = {f([2, 16, 1])}. Ключи — позиции 0 и 2 (на позиции 1 — ReLU), формы — кортежи, веса выходы × входы.'
want = {"0.weight": (32, 8), "0.bias": (32,), "2.weight": (16, 32), "2.bias": (16,), "4.weight": (1, 16), "4.bias": (1,)}
got = need('shapes', dict)
assert got == want, f'shapes = {got}, а нужно {want}.'
assert need('n_total') == 833, f'n_total = {need("n_total")}: перемножьте числа в каждой форме и сложите.'
```

### hint
Линейный слой номер `i` (с нуля) стоит в `nn.Sequential` на позиции `2 * i`: перед ним `i` слоёв `Linear` и `i` слоёв `ReLU`. Пары размеров — `zip(sizes[:-1], sizes[1:])`.

### hint
В цикле `for i, (a, b) in enumerate(zip(sizes[:-1], sizes[1:])):` — `out[f"{2 * i}.weight"] = (b, a)` и `out[f"{2 * i}.bias"] = (b,)`. Число элементов формы — `int(np.prod(shape))`.

### solution
```python
import numpy as np

def state_shapes(sizes):
    out = {}
    for i, (a, b) in enumerate(zip(sizes[:-1], sizes[1:])):
        out[f"{2 * i}.weight"] = (b, a)
        out[f"{2 * i}.bias"] = (b,)
    return out

shapes = state_shapes([8, 32, 16, 1])
n_total = sum(int(np.prod(s)) for s in shapes.values())
print(shapes, n_total)
```

### explain
Для `[2, 16, 1]` получается ровно то, что печатает `list(model.state_dict())` в блокноте, — 65 чисел. Для `[8, 32, 16, 1]` — шесть тензоров и 833 числа: 256 + 32 весов и сдвигов первого слоя, 512 + 16 второго, 16 + 1 выходного. Эти же формы PyTorch печатает в ошибке `size mismatch`, когда архитектура при загрузке не совпала: увидев `torch.Size([16, 2])`, вы сразу понимаете, что это веса слоя «2 входа → 16 нейронов». В своём блокноте сверьте с PyTorch: `{k: tuple(v.shape) for k, v in model.state_dict().items()}` даёт тот же словарь.
