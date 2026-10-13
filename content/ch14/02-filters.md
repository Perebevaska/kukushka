---
title: Свёртка и фильтры
files: [showcase.npz]
lead: "Свёртка — главная операция компьютерного зрения: маленькое окно-фильтр проходит по картинке и в каждом месте считает взвешенную сумму пикселей. Разные веса — разные фильтры: размытие убирает шум, фильтр Собеля находит края. Пишем свёртку руками, применяем готовую из scipy и собираем из фильтров и пулинга признаки, с которыми простая модель видит гораздо лучше."
recap:
  - "Свёртка: окно k × k проходит по картинке; в каждой позиции — сумма произведений пикселей окна на веса фильтра. Без дополнения краёв выход меньше: n − k + 1."
  - "`scipy.ndimage.correlate(img, kernel, mode='nearest')` — то же быстро и с дополнением краёв (размер не меняется). В нейросетях «свёрткой» называют именно эту операцию."
  - "Размытие (среднее по окну) подавляет шум; фильтры Собеля откликаются на перепады яркости — края; модуль градиента `np.hypot(gx, gy)` — сила края."
  - "На шумной картинке края находит и шум: сначала размывают, потом ищут края."
  - "Пулинг (max-pooling) берёт максимум в каждом блоке s × s: картинка уменьшается, а признаки становятся терпимее к сдвигу."
  - "Свёртка → модуль → пулинг → таблица признаков: логистическая регрессия на таких признаках заметно точнее, чем на сырых пикселях."
---

## Окно, которое скользит

Возьмём крошечную картинку 5 × 5 и фильтр 3 × 3. Фильтр ставят в левый верхний угол, перемножают поэлементно с пикселями под ним и складывают — получается одно число. Затем сдвигают окно на пиксель и повторяют.

::: tip Аналогия
Представьте контролёра с трафаретом, который идёт по подносу с выпечкой клетка за клеткой: в каждом месте прикладывает один и тот же трафарет и записывает одно число — насколько то, что под ним, похоже на рисунок трафарета. Трафарет один на весь поднос, поэтому один и тот же узор находится в любом месте. Хромает аналогия в одном: трафарет отвечает «похоже или нет», а фильтр считает взвешенную сумму — число может быть отрицательным и зависит не только от формы, но и от яркости пикселей.
:::

Картинка: слева три тёмных столбца (0), справа два светлых (9). Фильтр: левый столбец весов −1, средний 0, правый +1 — он спрашивает «насколько справа светлее, чем слева?».

Посчитаем одну позицию руками. Окно стоит так, что накрывает столбцы 1, 2, 3 (строки 0–2). Под ним пиксели:

| | столбец 1 | столбец 2 | столбец 3 |
|---|---|---|---|
| строка 0 | 0 | 0 | 9 |
| строка 1 | 0 | 0 | 9 |
| строка 2 | 0 | 0 | 9 |

Умножаем каждый на вес из той же клетки фильтра и складываем: в каждой строке 0·(−1) + 0·0 + 9·1 = 9, три строки — **27**. А если окно стоит над столбцами 0, 1, 2 — там все пиксели 0, и сумма 0. Вот и весь принцип. Теперь то же кодом по всем позициям:

::: figure convolution
Пример из раздела: фильтр «справа светлее?» над картинкой с границей тёмного и светлого. Выделенное окно даёт 27.
:::

```python
import numpy as np

img = np.array([
    [0, 0, 0, 9, 9],
    [0, 0, 0, 9, 9],
    [0, 0, 0, 9, 9],
    [0, 0, 0, 9, 9],
    [0, 0, 0, 9, 9],
], dtype=float)
kernel = np.array([[-1, 0, 1],
                   [-1, 0, 1],
                   [-1, 0, 1]], dtype=float)       # «справа светлее, чем слева?»

k = kernel.shape[0]
out = np.zeros((img.shape[0] - k + 1, img.shape[1] - k + 1))
for i in range(out.shape[0]):
    for j in range(out.shape[1]):
        out[i, j] = (img[i:i + k, j:j + k] * kernel).sum()
print(out)
```

**Что здесь происходит:**

- `out` — заготовка результата. Окно 3 × 3 помещается в картинку 5 × 5 только в 3 × 3 положениях: `5 − 3 + 1 = 3` по каждой стороне.
- Двойной цикл перебирает положения окна: `i` — сдвиг вниз, `j` — сдвиг вправо.
- `img[i:i + k, j:j + k]` — кусок картинки под окном, 3 × 3.
- `(кусок * kernel).sum()` — поэлементное произведение (не матричное!) и сумма — одно число.

Фильтр откликнулся (27) ровно там, где тёмное сменяется светлым, а на ровных участках дал 0. Это и есть детектор вертикального края. Выход меньше входа: 5 − 3 + 1 = 3 по каждой стороне.

Циклы на Python медленные. `scipy.ndimage.correlate` делает то же на C и умеет дополнять края, чтобы выход был того же размера, что вход: `mode="nearest"` повторяет крайние пиксели.

```python
import numpy as np
from scipy import ndimage as ndi

img = np.array([[0, 0, 0, 9, 9]] * 5, dtype=float)
kernel = np.array([[-1, 0, 1]] * 3, dtype=float)
print(ndi.correlate(img, kernel, mode="nearest"))
```

Выход теперь 5 × 5: средние столбцы совпадают с ручным результатом, а крайние появились за счёт дополнения.

**Что здесь происходит:**

- `[[0, 0, 0, 9, 9]] * 5` — список из пяти одинаковых строк; так короче записать нашу картинку.
- `ndi.correlate(картинка, фильтр, mode=...)` — та же операция, что в цикле, но для **каждого** пикселя: окно центрируется на пикселе, а за краем картинку дополняют.
- `mode` — чем дополнять края:

| `mode` | Чем заполняется край | Чем грозит |
|---|---|---|
| `"nearest"` | повторяется крайний пиксель | почти ничего — край продолжается «как есть» |
| `"reflect"` | зеркальное отражение | то же, что `nearest`, для плавных картинок |
| `"constant"` | нули (`cval=0`) | ложный «край» на границе картинки: светлый фон встречает чёрную рамку |

Проверьте сами: с `mode="constant"` у правого края появится отрицательный отклик −27 (в угловых клетках −18: там нули дописаны ещё и сверху или снизу) — фильтр «увидел» переход от светлого к чёрной рамке, которой на картинке нет. Поэтому для наших кадров берём `nearest`.

::: figure pad-modes
Средняя строка картинки 5 × 5 с дописанными за краем значениями. `nearest` продолжает край «как есть», и отклик у правого края — 0. `constant` дописывает нули, и фильтр находит несуществующий край: −27.
:::

::: deep Свёртка или корреляция
Строго по математике свёртка ещё и переворачивает фильтр. То, что мы считали выше (без переворота), называется **взаимной корреляцией** — и именно её считают слои нейросетей, хотя называют свёрткой. В `scipy.ndimage` есть обе: `correlate` и `convolve`. Для симметричных фильтров разницы нет; мы везде используем `correlate`.
:::

{{practice: conv, p-size, modes}}

## Размытие и края

Три фильтра, которые знает любой графический редактор:

- **размытие** — все веса по 1/9: каждый пиксель заменяется средним по окрестности, случайный шум усредняется;
- **Собель по x** — `[[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]`: перепад слева направо (вертикальные края);
- **Собель по y** — то же, повёрнутое: перепад сверху вниз (горизонтальные края).

Силу края в точке считают как длину вектора из двух откликов: `np.hypot(gx, gy)`.

Сначала посмотрим, как размытие действует на одиночную «крапинку» шума — в одном измерении, чтобы всё было видно глазами:

```python
import numpy as np

signal = np.array([0, 0, 9, 0, 0], dtype=float)     # один яркий пиксель среди тёмных
window = np.ones(3) / 3                              # среднее по трём соседям
print(np.convolve(signal, window, mode="same"))
```

`np.convolve` — одномерная свёртка из numpy. Дополнять край она умеет только нулями, а не `nearest`; для игрушечного примера в центре строки это не важно, а у края строки нули дадут ложный спад (это видно в «Предскажите вывод» ниже).

::: figure blur-1d
Слева — одиночный всплеск шума до и после размытия: пик 9 стал тремя тройками. Справа — ступенька-край из «Предскажите вывод» ниже: после размытия она плавнее, но никуда не делась.
:::

Яркость 9 «размазалась» по трём соседям по 3: пик стал втрое ниже. Случайный шум — это и есть такие одиночные пики, поэтому размытие его гасит. А настоящий край (длинная граница тёмного и светлого) от размытия только чуть смягчается: по обе стороны от него соседи одинаковые.

Теперь — все три фильтра на настоящем круассане:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage as ndi

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
img = X[np.flatnonzero(y == 1)[0]]

BLUR = np.ones((3, 3)) / 9
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
SY = SX.T

blur = ndi.correlate(img, BLUR, mode="nearest")
gx = ndi.correlate(blur, SX, mode="nearest")
gy = ndi.correlate(blur, SY, mode="nearest")
edges = np.hypot(gx, gy)

views = {"исходная": img, "размытие": blur, "Собель x": gx, "Собель y": gy, "сила края": edges}
fig, axes = plt.subplots(1, 5, figsize=(11, 2.4))
for ax, (name, v) in zip(axes, views.items()):
    ax.imshow(v, cmap="gray"); ax.set_title(name, fontsize=9); ax.axis("off")
```

**Что здесь происходит:**

- `d["X"] / 255` — переводим яркости в доли 0–1 (и заодно в `float`, так что переполнение `uint8` не грозит).
- `BLUR = np.ones((3, 3)) / 9` — девять весов по 1/9: результат — среднее окрестности.
- `SY = SX.T` — транспонирование: строки становятся столбцами, и фильтр «вертикальных» перепадов превращается в фильтр «горизонтальных».
- Порядок: сначала размываем (`blur`), потом ищем края на размытой картинке.
- `np.hypot(gx, gy)` — это `√(gx² + gy²)` для каждого пикселя: сила края независимо от его направления.
- `imshow(v, cmap="gray")` без `vmin/vmax` — здесь намеренно: у карт откликов свой диапазон (бывают и отрицательные значения), и автоматическое растягивание помогает их разглядеть.

На карте силы края круассан превращается в контур, а ровный поднос — в тёмное поле. Карта отклика фильтра называется **картой признака** (feature map).

::: predict
```python static
import numpy as np
print(np.convolve([0, 0, 9, 9, 9], np.ones(3) / 3, mode="same").round(1).tolist())
```

- `[0.0, 3.0, 3.0, 3.0, 0.0]`
- [x] `[0.0, 3.0, 6.0, 9.0, 6.0]`
- `[0.0, 0.0, 9.0, 9.0, 9.0]`

Почему: в каждой позиции — среднее трёх соседей (за краем — нули). У самого края ступеньки соседи (0, 9, 9) дают 6, внутри светлой области (9, 9, 9) — 9, а последнее значение — (9, 9, 0) → 6 из-за нулевого дополнения. Ступенька не исчезла, а стала плавнее: край размытие сохраняет, только смягчает.
:::

::: warn
Если искать края сразу на шумной картинке, фильтр Собеля откликается на каждую случайную крапинку — шум ведь тоже перепад яркости. На наших кадрах средняя сила края у пустого подноса без размытия (0.29) почти как у печенья (0.35). После размытия 3 × 3 разрыв больше: 0.12 против 0.19, а у круассана — 0.24. Порядок «сначала сгладить, потом дифференцировать» — стандартный.
:::

::: quiz
Почему края ищут на размытой картинке, а не сразу на исходной?

- [x] Шум — тоже перепады яркости, и Собель откликается на каждую крапинку; размытие гасит одиночные пики, а длинные края только слегка смягчает
  > Поэтому после размытия разрыв между пустым подносом и выпечкой по силе края становится больше.
- [ ] Размытие делает края резче, и Собелю проще их найти
  > Наоборот, размытие края смягчает. Выигрыш в том, что шум гаснет сильнее, чем настоящие края.
- [ ] Фильтр Собеля работает только с дробными числами, а размытие переводит картинку во `float`
  > Во `float` картинку переводят делением на 255 ещё до фильтров. Порядок «сгладить, потом искать края» нужен из-за шума.
- [ ] Без размытия выход фильтра получится меньше картинки
  > Размер выхода зависит от дополнения краёв (`mode="nearest"`), а не от размытия.
:::

{{practice: denoise, orient}}

## Пулинг

Карта признака того же размера, что картинка, — всё ещё 1024 числа, и она так же чувствительна к сдвигу. **Max-pooling** делит карту на блоки s × s и оставляет из каждого максимум. Картинка 32 × 32 при s = 4 превращается в 8 × 8.

```python
import numpy as np

def max_pool(img, s):
    h, w = img.shape
    return img.reshape(h // s, s, w // s, s).max(axis=(1, 3))

a = np.arange(16).reshape(4, 4)
print(a)
print(max_pool(a, 2))
```

**Что здесь происходит:**

- Картинка 4 × 4 при `s = 2` превращается в массив формы `(2, 2, 2, 2)`: номер блока по вертикали, строка внутри блока, номер блока по горизонтали, столбец внутри блока.
- `.max(axis=(1, 3))` — максимум по осям «внутри блока» (1 и 3); остаются оси «номер блока» — результат 2 × 2.
- Работает, только если размеры делятся на `s` нацело: 32 × 32 делится на 2, 4, 8, 16.

::: figure max-pool
Слева — карта 4 × 4 из «Предскажите вывод» ниже, цветом выделены блоки 2 × 2 и их максимумы. Справа — почему пулинг терпим к сдвигу: край сместился на пиксель внутри блока, а максимум блока тот же.
:::

::: tip Аналогия
Max-pooling — как отчёт управляющему по залам: ему не нужно знать, за каким именно столиком сидел гость с жалобой, достаточно «в этом зале жалоба была». Сдвиньте гостя на соседний столик того же зала — отчёт не изменится. Хромает аналогия в одном: если гость перейдёт в соседний зал (край пересечёт границу блока), отчёт уже изменится.
:::

`reshape(h // s, s, w // s, s)` раскладывает картинку на блоки, `max(axis=(1, 3))` берёт максимум внутри каждого. Если край сдвинулся на пиксель, но остался в том же блоке, после пулинга ничего не изменится. Проверим на сдвинутом круассане — насколько (в долях) меняется картинка:

```python
import numpy as np

def max_pool(img, s):
    h, w = img.shape
    return img.reshape(h // s, s, w // s, s).max(axis=(1, 3))

d = np.load("showcase.npz")
x0 = d["X"][np.flatnonzero(d["y"] == 1)[0]] / 255
for s in [1, 2, 4]:
    base = max_pool(x0, s)
    ch = [np.linalg.norm(base - max_pool(np.roll(x0, k, axis=1), s)) / np.linalg.norm(base) for k in [1, 2, 3]]
    print(f"пулинг {s}: сдвиг на 1, 2, 3 пикселя меняет картинку на", np.round(ch, 2))
```

**Что здесь происходит:**

- `max_pool(x0, 1)` — пулинг с блоком 1 × 1 ничего не меняет; это строка «без пулинга» для сравнения.
- Для каждого сдвига `k` считаем расстояние между описанием исходной и сдвинутой картинки и делим на «размер» исходного описания — получается относительное изменение (0.2 — изменилось на 20 %).

С пулингом 4 × 4 сдвиг на 3 пикселя меняет описание примерно вдвое меньше, чем без него.

::: predict
```python static
import numpy as np
F = np.array([[1, 5, 0, 0],
              [2, 3, 0, 7],
              [0, 0, 1, 1],
              [4, 0, 1, 1]])
print(F.reshape(2, 2, 2, 2).max(axis=(1, 3)).tolist())
```

- `[[5, 0], [4, 1]]`
- [x] `[[5, 7], [4, 1]]`
- `[[3, 7], [4, 1]]`

Почему: блоки 2 × 2 — левый верхний (1, 5, 2, 3), правый верхний (0, 0, 0, 7), левый нижний (0, 0, 4, 0), правый нижний (1, 1, 1, 1). Максимумы: 5, 7, 4, 1.
:::

::: quiz
Зачем после свёртки делают пулинг 2 × 2 (максимум в каждом квадрате)?

- [x] Он уменьшает картинку и делает признаки устойчивее к небольшим сдвигам: важно, что край есть рядом, а не в каком точно пикселе
  > Максимум из квадрата не меняется, если край сдвинулся внутри него.
- [ ] Чтобы картинка стала ярче
  > Яркость не цель пулинга.
- [ ] Чтобы увеличить разрешение
  > Пулинг уменьшает картинку вдвое по каждой стороне.
- [ ] Он обучает фильтры
  > У пулинга нет весов — он ничего не учит.
:::

{{practice: pool, global}}

## Признаки из фильтров

Соберём конвейер вручную: несколько фильтров → модуль отклика → пулинг 4 × 4 → вытягиваем в строку. Из каждой картинки получается 4 × 64 = 256 признаков.

```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]

SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
KERNELS = [SX, SX.T, np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]), -np.ones((3, 3)) / 9]

def max_pool(F, s):
    n, h, w = F.shape
    return F.reshape(n, h // s, s, w // s, s).max(axis=(2, 4))

def conv_features(Z):
    maps = []
    for i, k in enumerate(KERNELS):
        f = np.stack([ndi.correlate(z, k, mode="nearest") for z in Z])
        if i < 3:
            f = np.abs(f)                       # края любого знака
        maps.append(max_pool(f, 4).reshape(len(Z), -1))
    return np.hstack(maps)

F = conv_features(X)
tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
def make_lr():                                  # каждый вызов — новый, необученный конвейер
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))

print("пиксели:  ", round(make_lr().fit(X[tr].reshape(len(tr), -1), y[tr]).score(X[te].reshape(len(te), -1), y[te]), 3))
print("фильтры:  ", round(make_lr().fit(F[tr], y[tr]).score(F[te], y[te]), 3))
```

**Что здесь происходит:**

- `KERNELS` — четыре фильтра: Собель по x, Собель по y, лапласиан (откликается на пятна и точки) и «минус размытие» (большое значение там, где темно).
- `np.stack([ndi.correlate(z, k, ...) for z in Z])` — применяем фильтр к каждой картинке и складываем результаты в массив `(n, 32, 32)`.
- `np.abs(f)` для краёв: перепад «светлое → тёмное» и «тёмное → светлое» одинаково важны, знак не нужен.
- `max_pool(f, 4)` — `(n, 8, 8)`, затем `.reshape(len(Z), -1)` — строка из 64 чисел на картинку.
- `np.hstack(maps)` — склеиваем четыре блока по 64 признака: 256 признаков на картинку.
- Разбиение по индексам `tr, te` — чтобы одними и теми же индексами брать и пиксели, и признаки.
- `make_lr()` возвращает новый конвейер при каждом вызове: пиксели и признаки обучаются на двух разных моделях, и вторая не затирает первую.

::: figure filter-features
Конвейер признаков по шагам: из кадра 32 × 32 получается 256 чисел, в которых записано, где в кадре есть края и тёмные пятна. Модель та же — меняется только то, что ей дали на вход.
:::

Та же логистическая регрессия: на сырых пикселях около 0.68, на признаках из фильтров — около 0.88. Размер блока пулинга (4) мы выбрали наугад; какой лучше на наших кадрах, проверите в задаче «Пиксели против фильтров». Модель не стала умнее — ей дали описание, где «тёмное пятно с краями где-то в этой четверти кадра» записано явно. Четвёртый фильтр (минус размытие) после max-pooling отвечает за «самое тёмное место в блоке».

::: deep
Мы выбрали фильтры сами: края по x и y, лапласиан (точки и пятна), размытие. Свёрточная нейросеть делает следующий шаг — **учит веса фильтров** из данных, как логистическая регрессия учит веса признаков. И складывает слои: фильтры второго слоя смотрят на карты признаков первого и находят уже не края, а «полумесяц» или «шапку маффина». Об этом урок «Свёрточные нейросети».
:::

{{practice: features, edges}}

## Разберём вместе: у кого горизонтальные края

Фильтры по x и y видят разное: Собель по x — вертикальные границы, по y — горизонтальные. Есть ли у какого-то вида выпечки «характерное направление» краёв? Шапка маффина — широкая горизонтальная граница, круассан и печенье — округлые, края у них во все стороны.

**План:** для каждой картинки посчитать суммарную силу горизонтальных краёв (по `|gy|`) и вертикальных (по `|gx|`), взять их отношение и сравнить медианы по классам.

```python
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

d = np.load("showcase.npz")
X, y, classes = d["X"] / 255, d["y"], d["classes"]
BLUR = np.ones((3, 3)) / 9
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])

ratio = []
for z in X:
    b = ndi.correlate(z, BLUR, mode="nearest")
    vert = np.abs(ndi.correlate(b, SX, mode="nearest")).sum()      # вертикальные края
    horiz = np.abs(ndi.correlate(b, SX.T, mode="nearest")).sum()   # горизонтальные края
    ratio.append(horiz / vert)
print(pd.Series(ratio).groupby(classes[y]).median().round(2))
```

**Что получилось:** у круассана, печенья и пустого подноса отношение около 1 — краёв поровну в обе стороны. У маффина — около 1.37: горизонтальных краёв на треть больше. Это отличительная черта, которую мы нашли одним числом, — и именно такие черты свёрточная сеть учится находить сама, комбинируя фильтры разных направлений.

{{practice: edge-rule}}

## Практика

## task: conv | Свёртка руками | warmup

Напишите функцию `conv2d(img, kernel)` — свёртку без дополнения краёв (как в первом примере урока, без переворота фильтра) для квадратного фильтра. Примените её к `img` из заготовки с фильтром `blur` — результат в `out`.

### setup
```python
import numpy as np
img = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]], dtype=float)
blur = np.ones((3, 3)) / 9
```

### starter
```python
import numpy as np

def conv2d(img, kernel):
    ...

out = conv2d(img, blur)
print(out)
```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
f = need('conv2d')
r = _np.random.default_rng(0)
for n, k in [(6, 3), (7, 3), (5, 5), (8, 2)]:
    a, kk = r.normal(size=(n, n)), r.normal(size=(k, k))
    got = _np.asarray(f(a, kk), dtype=float)
    w = _np.array([[(a[i:i + k, j:j + k] * kk).sum() for j in range(n - k + 1)] for i in range(n - k + 1)])
    assert got.shape == w.shape, f'Для картинки {n}×{n} и фильтра {k}×{k} выход должен быть {w.shape}, а сейчас {got.shape}.'
    assert _np.allclose(got, w), 'Значения не совпадают: в каждой позиции — сумма произведений окна на фильтр, без переворота.'
assert _np.allclose(need('out'), [[6, 7], [10, 11]]), f'out = {need("out")}.'
```

### hint
Повторите ручной расчёт из начала урока: окно ставится в каждую допустимую позицию, и в каждой — сумма произведений.

### hint
Размер выхода — `n - k + 1`. Двойной цикл по `i`, `j`; окно — `img[i:i + k, j:j + k]`.

### hint
```python
k = kernel.shape[0]
out = np.zeros((img.shape[0] - k + 1, img.shape[1] - k + 1))
for i in range(out.shape[0]):
    for j in range(out.shape[1]):
        out[i, j] = ...
return out
```

### solution
```python
import numpy as np

def conv2d(img, kernel):
    k = kernel.shape[0]
    h, w = img.shape[0] - k + 1, img.shape[1] - k + 1
    out = np.zeros((h, w))
    for i in range(h):
        for j in range(w):
            out[i, j] = (img[i:i + k, j:j + k] * kernel).sum()
    return out

out = conv2d(img, blur)
print(out)
```

## task: p-size | Размер выхода | warmup

Соберите код, который печатает размер выхода свёртки без дополнения для картинки 32 × 32 и фильтра 5 × 5, а затем — размер после max-pooling 2 × 2.

### parsons
```python
n, k, s = 32, 5, 2
out = n - k + 1
print(out)
print(out // s)
```

### check
```python
assert _lines == ['28', '14'], f'Сейчас: {_lines}.'
```

### hint
Сначала параметры, потом размер свёртки, потом — после пулинга.

### hint
32 − 5 + 1 = 28; после пулинга 2 — 28 // 2 = 14.

## task: edges | Сила края по классам | base

Для всех картинок (`X` уже в долях 0–1) посчитайте карту силы края: размытие 3 × 3 (`BLUR`), затем Собель по x и y (`SX`, `SX.T`), `np.hypot`. Везде `ndi.correlate(..., mode="nearest")`. Для каждой картинки возьмите 95-й процентиль силы края (`np.percentile(..., 95)`) и сохраните `edge95` — массив длины 2000 и `edge_by_class` — Series средних `edge95` по названиям классов (3 знака). То же без размытия — `edge_by_class_raw`.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, y, classes = d["X"] / 255, d["y"], d["classes"]
BLUR = np.ones((3, 3)) / 9
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
```

### starter
```python
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

def edge_map(img, smooth=True):
    ...

```

### check
```python
import numpy as _np
import pandas as _pd
from scipy import ndimage as _ndi
d0 = _np.load('showcase.npz'); X0, y0, c0 = d0['X'] / 255, d0['y'], d0['classes']
B = _np.ones((3, 3)) / 9; S = _np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
def _em(z, sm):
    if sm: z = _ndi.correlate(z, B, mode='nearest')
    return _np.hypot(_ndi.correlate(z, S, mode='nearest'), _ndi.correlate(z, S.T, mode='nearest'))
e = _np.array([_np.percentile(_em(z, True), 95) for z in X0])
er = _np.array([_np.percentile(_em(z, False), 95) for z in X0])
assert _np.allclose(_np.asarray(need('edge95')), e, atol=1e-6), 'edge95: 95-й процентиль силы края после размытия, по каждой картинке.'
w = _pd.Series(e).groupby(c0[y0]).mean().round(3); wr = _pd.Series(er).groupby(c0[y0]).mean().round(3)
g, gr = need('edge_by_class', _pd.Series), need('edge_by_class_raw', _pd.Series)
assert all(close(g[k], w[k], 0.0015) for k in w.index), f'edge_by_class:\n{g}\nа нужно\n{w}'
assert all(close(gr[k], wr[k], 0.0015) for k in wr.index), f'edge_by_class_raw:\n{gr}\nа нужно\n{wr}'
```

### hint
Начните с функции `edge_map(img, smooth=True)` для **одной** картинки: при `smooth` — размыть, потом два Собеля и `np.hypot`.

### hint
Функция: при `smooth` сначала `img = ndi.correlate(img, BLUR, mode="nearest")`, потом `np.hypot(ndi.correlate(img, SX, ...), ndi.correlate(img, SX.T, ...))`. Средние по классам: `pd.Series(edge95).groupby(classes[y]).mean()`.

### hint
Процентиль одной картинки — `np.percentile(edge_map(z), 95)`; для всех — `np.array([... for z in X])`. То же с `smooth=False` — для `edge_by_class_raw`.

### solution
```python
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

def edge_map(img, smooth=True):
    if smooth:
        img = ndi.correlate(img, BLUR, mode="nearest")
    return np.hypot(ndi.correlate(img, SX, mode="nearest"), ndi.correlate(img, SX.T, mode="nearest"))

edge95 = np.array([np.percentile(edge_map(z), 95) for z in X])
edge95_raw = np.array([np.percentile(edge_map(z, smooth=False), 95) for z in X])
edge_by_class = pd.Series(edge95).groupby(classes[y]).mean().round(3)
edge_by_class_raw = pd.Series(edge95_raw).groupby(classes[y]).mean().round(3)
print(pd.DataFrame({"с размытием": edge_by_class, "без": edge_by_class_raw}))
```

### explain
После размытия у пустого подноса сильных краёв почти нет, а у маффина с тёмной шапкой — больше всех. Без размытия шум поднимает «края» у всех классов, и разница между ними относительно меньше. 95-й процентиль, а не максимум, — чтобы одна случайная крапинка не решала за всю картинку.

## task: pool | Пулинг для всего набора | base

Напишите `max_pool(F, s)` для массива карт формы `(n, h, w)` (h и w делятся на s): результат — `(n, h // s, w // s)`. Напишите и `avg_pool(F, s)` — то же со средним. Примените обе к `X` с `s=4`: `P_max`, `P_avg`. В `ratio` — во сколько раз уменьшилось число чисел на картинку.

### setup
```python
import numpy as np
X = np.load("showcase.npz")["X"] / 255
```

### starter
```python
import numpy as np

def max_pool(F, s):
    ...

def avg_pool(F, s):
    ...

```

### check
```python
import numpy as _np
X0 = _np.load('showcase.npz')['X'] / 255
f, g = need('max_pool'), need('avg_pool')
t = _np.arange(32, dtype=float).reshape(2, 4, 4)
assert _np.asarray(f(t, 2)).tolist() == [[[5, 7], [13, 15]], [[21, 23], [29, 31]]], f'max_pool(t, 2) = {_np.asarray(f(t, 2)).tolist()}.'
assert _np.allclose(g(t, 2), [[[2.5, 4.5], [10.5, 12.5]], [[18.5, 20.5], [26.5, 28.5]]]), 'avg_pool: среднее в каждом блоке.'
Pm, Pa = need('P_max'), need('P_avg')
assert Pm.shape == (2000, 8, 8) and Pa.shape == (2000, 8, 8), f'Формы: {Pm.shape}, {Pa.shape}.'
assert _np.allclose(Pm, X0.reshape(2000, 8, 4, 8, 4).max(axis=(2, 4))), 'P_max не совпадает.'
assert close(need('ratio'), 16), f'ratio = {need("ratio")}.'
```

### hint
Это `max_pool` из урока, только у массива на одну ось больше: первая ось — номер картинки, её не трогаем.

### hint
`F.reshape(n, h // s, s, w // s, s)` и `.max(axis=(2, 4))` / `.mean(axis=(2, 4))`.

### hint
`ratio` — отношение числа значений: `X[0].size / P_max[0].size` (1024 / 64).

### solution
```python
import numpy as np

def max_pool(F, s):
    n, h, w = F.shape
    return F.reshape(n, h // s, s, w // s, s).max(axis=(2, 4))

def avg_pool(F, s):
    n, h, w = F.shape
    return F.reshape(n, h // s, s, w // s, s).mean(axis=(2, 4))

P_max, P_avg = max_pool(X, 4), avg_pool(X, 4)
ratio = X[0].size / P_max[0].size
print(P_max.shape, ratio)
```

### explain
Max- и average-pooling отвечают на разные вопросы: «есть ли где-то в блоке что-то яркое?» и «насколько блок светлый в целом?». Для наших кадров (тёмная выпечка на светлом фоне) max-pooling от самой картинки почти везде вернёт яркий фон — тёмное пятно потеряется. Поэтому в уроке max-pooling применяется не к картинке, а к картам откликов фильтров, где «интересное» — это большие значения. Типичная ошибка — забыть первую ось: `F.reshape(h // s, s, w // s, s)` для массива из 2000 картинок упадёт с ошибкой формы.

## task: denoise | Размытие против шума | plus

Шум удобно мерить на пустых подносах: там нет выпечки, и разброс яркости в центре кадра (`[4:28, 4:28]`) — это шум плюс плавный градиент подноса. Для пустых картинок посчитайте средний по картинкам `np.std` центра до размытия (`noise_raw`) и после размытия фильтрами 3 × 3 и 5 × 5 (`noise_3`, `noise_5`), все — 4 знака. Сохраните `reduction_3` — во сколько раз размытие 3 × 3 уменьшило разброс (2 знака).

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
```

### starter
```python
import numpy as np
from scipy import ndimage as ndi

empty = X[y == 0]

```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
d0 = _np.load('showcase.npz'); E = d0['X'][d0['y'] == 0] / 255
def _n(k):
    if k == 1: return round(float(_np.mean([z[4:28, 4:28].std() for z in E])), 4)
    K = _np.ones((k, k)) / k ** 2
    return round(float(_np.mean([_ndi.correlate(z, K, mode='nearest')[4:28, 4:28].std() for z in E])), 4)
w = {'noise_raw': _n(1), 'noise_3': _n(3), 'noise_5': _n(5)}
for k, v in w.items():
    assert close(need(k), v, 0.0002), f'{k} = {need(k)}, а нужно {v}.'
assert close(need('reduction_3'), round(w['noise_raw'] / w['noise_3'], 2), 0.011), f'reduction_3 = {need("reduction_3")}.'
```

### hint
Работайте только с пустыми кадрами: `empty = X[y == 0]`. Для каждого — разброс центра, потом среднее по всем.

### hint
Фильтр k × k — `np.ones((k, k)) / k**2`. Разброс одной картинки — `z[4:28, 4:28].std()`, потом среднее по пустым.

### hint
Удобно написать функцию `spread(k)`: при `k == 1` — без размытия, иначе — `ndi.correlate(z, K, mode="nearest")[4:28, 4:28].std()`.

### solution
```python
import numpy as np
from scipy import ndimage as ndi

empty = X[y == 0]

def spread(k):
    if k == 1:
        return np.mean([z[4:28, 4:28].std() for z in empty])
    K = np.ones((k, k)) / k ** 2
    return np.mean([ndi.correlate(z, K, mode="nearest")[4:28, 4:28].std() for z in empty])

noise_raw, noise_3, noise_5 = (round(float(spread(k)), 4) for k in [1, 3, 5])
reduction_3 = round(noise_raw / noise_3, 2)
print(noise_raw, noise_3, noise_5, reduction_3)
```

### explain
Размытие 3 × 3 уменьшает разброс почти вдвое; для чистого независимого шума усреднение 9 пикселей дало бы уменьшение в √9 = 3 раза, но часть разброса — градиент подноса и крошки, их размытие не убирает. Окно 5 × 5 сглаживает сильнее, но и края выпечки размывает: сильнее — не всегда лучше.

## task: features | Пиксели против фильтров | plus

Повторите эксперимент из урока: признаки `conv_features` (4 фильтра, модуль для первых трёх, max-pooling 4) и логистическая регрессия со `StandardScaler` (`max_iter=3000`). Разбиение — `train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)`. Сохраните `acc_pixels`, `acc_filters` (3 знака) и `acc_pool2` — то же с пулингом 2 вместо 4.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
KERNELS = [SX, SX.T, np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]), -np.ones((3, 3)) / 9]
```

### starter
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

def conv_features(Z, s=4):
    ...

```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
d0 = _np.load('showcase.npz'); X0, y0 = d0['X'] / 255, d0['y']
S = _np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
KS = [S, S.T, _np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]), -_np.ones((3, 3)) / 9]
def _cf(Z, s):
    out = []
    for i, k in enumerate(KS):
        f = _np.stack([_ndi.correlate(z, k, mode='nearest') for z in Z])
        if i < 3: f = _np.abs(f)
        n, h, w = f.shape
        out.append(f.reshape(n, h // s, s, w // s, s).max(axis=(2, 4)).reshape(n, -1))
    return _np.hstack(out)
tr, te = _tts(_np.arange(len(X0)), test_size=0.25, random_state=42, stratify=y0)
_sc = lambda A: round(float(_mp(_SS(), _LR(max_iter=3000)).fit(A[tr], y0[tr]).score(A[te], y0[te])), 3)
w = {'acc_pixels': _sc(X0.reshape(len(X0), -1)), 'acc_filters': _sc(_cf(X0, 4)), 'acc_pool2': _sc(_cf(X0, 2))}
for k, v in w.items():
    assert close(need(k), v, 0.005), f'{k} = {need(k)}, а нужно {v}.'
```

### hint
Скопируйте `conv_features` из урока и добавьте параметр `s`. Пиксели — `X.reshape(len(X), -1)`.

### hint
Чтобы не повторять обучение трижды, напишите `score(A)`: конвейер `StandardScaler` + `LogisticRegression(max_iter=3000)`, обучение на `A[tr]`, `score` на `A[te]`.

### hint
`acc_pixels = score(X.reshape(len(X), -1))`, `acc_filters = score(conv_features(X, 4))`, `acc_pool2 = score(conv_features(X, 2))`.

### solution
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

def conv_features(Z, s=4):
    maps = []
    for i, k in enumerate(KERNELS):
        f = np.stack([ndi.correlate(z, k, mode="nearest") for z in Z])
        if i < 3:
            f = np.abs(f)
        n, h, w = f.shape
        maps.append(f.reshape(n, h // s, s, w // s, s).max(axis=(2, 4)).reshape(n, -1))
    return np.hstack(maps)

tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)

def score(A):
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(A[tr], y[tr])
    return round(m.score(A[te], y[te]), 3)

acc_pixels = score(X.reshape(len(X), -1))
acc_filters = score(conv_features(X, 4))
acc_pool2 = score(conv_features(X, 2))
print(acc_pixels, acc_filters, acc_pool2)
```

### explain
На наших кадрах пулинг 2 заметно выиграл: около 0.94 против 0.88 у пулинга 4. Он оставляет 4 × 256 = 1024 признака — больше деталей формы, и 1500 обучающих кадров хватает, чтобы логистическая регрессия в них разобралась. Терпимость к сдвигу при этом не пострадала: если сдвинуть тестовые кадры на 4 пикселя, оба варианта падают примерно до 0.79 — сдвиг на целый блок не прощает и пулинг 4. Значит, пулинг 4 в уроке был не лучшим выбором, а просто первым. Размер блока — такой же гиперпараметр, как глубина дерева: его выбирают на валидации, а не на глаз. На других данных победить может и крупный блок.

## task: global | Девять чисел вместо тысячи | star

Пулинг по всей картинке (**global pooling**) полностью убирает зависимость от положения. Для каждой картинки посчитайте 9 признаков: для фильтров `SX`, `SX.T`, `LAP` — среднее и максимум модуля отклика; для размытия `BLUR` — минимум, среднее и долю пикселей темнее 0.4. Сохраните `G` — массив `(2000, 9)` в этом порядке. Обучите `RandomForestClassifier(300, random_state=0)` на `G` и на сырых пикселях (разбиение как в прошлой задаче): `acc_raw`, `acc_global` (3 знака).

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
LAP = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
BLUR = np.ones((3, 3)) / 9
```

### starter
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
d0 = _np.load('showcase.npz'); X0, y0 = d0['X'] / 255, d0['y']
S = _np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]); L = _np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]); B = _np.ones((3, 3)) / 9
fm = lambda k: _np.stack([_ndi.correlate(z, k, mode='nearest') for z in X0]).reshape(len(X0), -1)
cols = []
for k in [S, S.T, L]:
    a = _np.abs(fm(k)); cols += [a.mean(1), a.max(1)]
b = fm(B); cols += [b.min(1), b.mean(1), (b < 0.4).mean(1)]
G0 = _np.column_stack(cols)
g = _np.asarray(need('G'))
assert g.shape == (2000, 9), f'G.shape = {g.shape}.'
assert _np.allclose(g, G0, atol=1e-6), 'Признаки G не совпадают: проверьте порядок и mode="nearest".'
tr, te = _tts(_np.arange(len(X0)), test_size=0.25, random_state=42, stratify=y0)
_s = lambda A: round(float(_RF(300, random_state=0).fit(A[tr], y0[tr]).score(A[te], y0[te])), 3)
wr, wg = _s(X0.reshape(len(X0), -1)), _s(G0)
assert close(need('acc_raw'), wr, 0.005), f'acc_raw = {need("acc_raw")}, а нужно {wr}.'
assert close(need('acc_global'), wg, 0.005), f'acc_global = {need("acc_global")}, а нужно {wg}.'
```

### hint
Каждый признак — одно число на картинку, то есть массив длины 2000. Девять таких массивов → `np.column_stack` → таблица `(2000, 9)`.

### hint
Карты всех картинок для фильтра `k`: `np.stack([ndi.correlate(z, k, mode="nearest") for z in X]).reshape(len(X), -1)` — дальше `.mean(1)`, `.max(1)` по строкам. Столбцы соберите `np.column_stack`.

### hint
Порядок важен: для `SX`, `SX.T`, `LAP` по очереди — `[a.mean(axis=1), a.max(axis=1)]` от `a = np.abs(карты)`; затем для размытия — `b.min(axis=1)`, `b.mean(axis=1)`, `(b < 0.4).mean(axis=1)`.

### solution
```python
import numpy as np
from scipy import ndimage as ndi
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

def fmap(k):
    return np.stack([ndi.correlate(z, k, mode="nearest") for z in X]).reshape(len(X), -1)

cols = []
for k in [SX, SX.T, LAP]:
    a = np.abs(fmap(k))
    cols += [a.mean(axis=1), a.max(axis=1)]
b = fmap(BLUR)
cols += [b.min(axis=1), b.mean(axis=1), (b < 0.4).mean(axis=1)]
G = np.column_stack(cols)

tr, te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=42, stratify=y)
acc_raw = round(RandomForestClassifier(300, random_state=0).fit(X[tr].reshape(len(tr), -1), y[tr]).score(X[te].reshape(len(te), -1), y[te]), 3)
acc_global = round(RandomForestClassifier(300, random_state=0).fit(G[tr], y[tr]).score(G[te], y[te]), 3)
print(acc_raw, acc_global)
```

### explain
Девять чисел, не знающих, где лежит выпечка, дают лесу около 0.96 — больше, чем 1024 пикселя. Но удивительнее другое: лес на сырых пикселях тоже силён, около 0.94, хотя логистическая регрессия на тех же пикселях давала 0.68, а ближайшая средняя картинка в уроке «Картинка — это массив чисел» — меньше половины. Лес сам выбирает «важные» пиксели и пороги по ним, а выпечка почти всегда лежит недалеко от центра кадра — на этом он и держится. В уроке «Модели на пикселях: ошибки, аугментация, устойчивость» проверим, что с ним будет, если кадры сдвинуть или затемнить: девяти глобальным признакам сдвиг не страшен по построению, а лесу на пикселях — страшен. Это идея, на которой держится вся глава: хорошее представление картинки важнее модели. Свёрточная сеть находит такое представление сама — урок «Свёрточные нейросети».

## task: modes | Чем дополнять края | warmup

Для картинки `img` (светлый квадрат 6 × 6, все пиксели 0.8) примените Собель по x (`SX`) с тремя способами дополнения: `"nearest"`, `"reflect"`, `"constant"`. Сохраните `max_abs` — словарь `{режим: наибольший модуль отклика}` (2 знака) и `fake_edge_mode` — режим, который «нашёл» край на пустом ровном квадрате.

### setup
```python
import numpy as np
img = np.full((6, 6), 0.8)
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
```

### starter
```python
import numpy as np
from scipy import ndimage as ndi

```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
i0, S = need('img'), need('SX')
w = {m: round(float(_np.abs(_ndi.correlate(i0, S, mode=m)).max()), 2) for m in ['nearest', 'reflect', 'constant']}
g = need('max_abs', dict)
assert set(g) == set(w) and all(close(g[m], w[m], 0.006) for m in w), f'max_abs = {g}, а нужно {w}.'
assert need('fake_edge_mode') == 'constant', f'fake_edge_mode = {need("fake_edge_mode")!r}.'
```

### hint
Цикл по трём режимам: `ndi.correlate(img, SX, mode=m)`; от результата — `np.abs(...).max()`.

### hint
Ровный квадрат не имеет краёв: «правильный» режим даёт 0. Тот режим, где максимум не 0, и придумал край.

### solution
```python
import numpy as np
from scipy import ndimage as ndi

max_abs = {m: round(float(np.abs(ndi.correlate(img, SX, mode=m)).max()), 2) for m in ["nearest", "reflect", "constant"]}
fake_edge_mode = max(max_abs, key=max_abs.get)
print(max_abs, fake_edge_mode)
```

## task: orient | Направление краёв | base

Повторите разбор из урока: для каждой картинки (`X` — в долях 0–1) размойте её (`BLUR`), посчитайте суммы модулей откликов Собеля по x (`vert`) и по y (`horiz`) и их отношение `horiz / vert`. Сохраните `ratio` — массив длины 2000, `ratio_by_class` — Series медиан по названиям классов (2 знака) и `most_horizontal` — класс с наибольшей медианой.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, y, classes = d["X"] / 255, d["y"], d["classes"]
BLUR = np.ones((3, 3)) / 9
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
```

### starter
```python
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

```

### check
```python
import numpy as _np
import pandas as _pd
from scipy import ndimage as _ndi
X0, y0, c0, B, S = need('X'), need('y'), need('classes'), need('BLUR'), need('SX')
r = []
for z in X0:
    b = _ndi.correlate(z, B, mode='nearest')
    r.append(_np.abs(_ndi.correlate(b, S.T, mode='nearest')).sum() / _np.abs(_ndi.correlate(b, S, mode='nearest')).sum())
r = _np.array(r)
assert _np.allclose(_np.asarray(need('ratio')), r, atol=1e-6), 'ratio — горизонтальные (SX.T) / вертикальные (SX) края, после размытия.'
w = _pd.Series(r).groupby(c0[y0]).median().round(2)
g = need('ratio_by_class', _pd.Series)
assert all(close(g[k], w[k], 0.006) for k in w.index), f'ratio_by_class:\n{g}\nа нужно\n{w}'
assert str(need('most_horizontal')) == str(w.idxmax()), f'most_horizontal = {need("most_horizontal")!r}.'
```

### hint
Цикл по картинкам: размыть → два отклика → суммы модулей → отношение. Отношения копите в список и превратите в массив.

### hint
Горизонтальные края находит `SX.T` (перепад сверху вниз), вертикальные — `SX`.

### hint
Медианы: `pd.Series(ratio).groupby(classes[y]).median().round(2)`; класс-лидер — `.idxmax()`.

### solution
```python
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

ratio = []
for z in X:
    b = ndi.correlate(z, BLUR, mode="nearest")
    vert = np.abs(ndi.correlate(b, SX, mode="nearest")).sum()
    horiz = np.abs(ndi.correlate(b, SX.T, mode="nearest")).sum()
    ratio.append(horiz / vert)
ratio = np.array(ratio)
ratio_by_class = pd.Series(ratio).groupby(classes[y]).median().round(2)
most_horizontal = ratio_by_class.idxmax()
print(ratio_by_class, most_horizontal)
```

### explain
У маффина горизонтальных краёв примерно на треть больше, чем вертикальных: широкая граница шапки и стаканчика. У остальных классов отношение около 1. Значит, отношение краёв — полезный признак, отличающий маффин, и он не зависит от того, где маффин лежит в кадре (суммы считаются по всей картинке). Такие признаки и нужны моделям: в уроке «Модели на пикселях: ошибки, аугментация, устойчивость» сравним, что дают модели сырые пиксели и что — признаки.

## task: edge-rule | Правило по краям | plus

Признак «сила краёв» тоже может отличать пустой поднос. Для каждой картинки посчитайте `strong` — долю пикселей, где сила края (размытие `BLUR`, затем `np.hypot` двух Собелей) больше 0.5. Правило: «товар есть», если `strong >= t`. Переберите `t` из `[0.005, 0.01, 0.02, 0.04]` и сохраните `acc_by_t` (3 знака), `best_t`, а в `vs_dark` — разность лучшей точности этого правила и правила по тёмным пикселям из урока «Картинка — это массив чисел» (`(X < 100/255)` доля ≥ 0.005), 3 знака.

### setup
```python
import numpy as np
from scipy import ndimage as ndi
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
BLUR = np.ones((3, 3)) / 9
SX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
```

### starter
```python
import numpy as np
from scipy import ndimage as ndi

```

### check
```python
import numpy as _np
from scipy import ndimage as _ndi
X0, y0, B, S = need('X'), need('y'), need('BLUR'), need('SX')
st = []
for z in X0:
    b = _ndi.correlate(z, B, mode='nearest')
    st.append((_np.hypot(_ndi.correlate(b, S, mode='nearest'), _ndi.correlate(b, S.T, mode='nearest')) > 0.5).mean())
st = _np.array(st)
assert _np.allclose(_np.asarray(need('strong')), st, atol=1e-9), 'strong — доля пикселей с силой края > 0.5 (после размытия).'
w = {t: round(float(((st >= t) == (y0 != 0)).mean()), 3) for t in [0.005, 0.01, 0.02, 0.04]}
g = need('acc_by_t', dict)
assert all(close(g[t], w[t], 0.0011) for t in w), f'acc_by_t = {g}, а нужно {w}.'
assert close(need('best_t'), max(w, key=w.get)), f'best_t = {need("best_t")}.'
dark = ((X0 < 100 / 255).reshape(len(X0), -1).mean(1) >= 0.005) == (y0 != 0)
assert close(need('vs_dark'), round(max(w.values()) - float(dark.mean()), 3), 0.0021), f'vs_dark = {need("vs_dark")}.'
```

### hint
Карта силы краёв одной картинки — как в задаче «Сила края по классам»; доля сильных — `(edges > 0.5).mean()`.

### hint
Точность правила при пороге `t` — `((strong >= t) == (y != 0)).mean()`; правило по тёмным — то же с `dark >= 0.005`, где `dark = (X < 100 / 255).reshape(len(X), -1).mean(axis=1)`.

### hint
`vs_dark = round(max(acc_by_t.values()) - dark_acc, 3)`.

### solution
```python
import numpy as np
from scipy import ndimage as ndi

strong = []
for z in X:
    b = ndi.correlate(z, BLUR, mode="nearest")
    edges = np.hypot(ndi.correlate(b, SX, mode="nearest"), ndi.correlate(b, SX.T, mode="nearest"))
    strong.append((edges > 0.5).mean())
strong = np.array(strong)
acc_by_t = {t: round(float(((strong >= t) == (y != 0)).mean()), 3) for t in [0.005, 0.01, 0.02, 0.04]}
best_t = max(acc_by_t, key=acc_by_t.get)
dark = (X < 100 / 255).reshape(len(X), -1).mean(axis=1)
dark_acc = float(((dark >= 0.005) == (y != 0)).mean())
vs_dark = round(max(acc_by_t.values()) - dark_acc, 3)
print(acc_by_t, best_t, vs_dark)
```

### explain
Правило по краям даёт около 0.95 — немного хуже, чем правило по тёмным пикселям (около 0.97). Причина видна из задачи про размытие: шум и крошки на подносе тоже дают «края», и порог приходится ставить выше, теряя светлое печенье. Вывод не «края хуже», а «один признак — слабая модель»: тёмные пиксели и края ошибаются на **разных** кадрах, и модель, которая видит оба признака сразу, ошибётся реже каждого правила. Именно это делают признаки из нескольких фильтров в задаче «Пиксели против фильтров».
