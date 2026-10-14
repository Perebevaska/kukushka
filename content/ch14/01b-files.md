---
title: "Файлы картинок и память"
lead: "Камера пишет тысячи цветных JPEG в день, а в памяти каждый кадр занимает столько, сколько в нём пикселей, как бы он ни был сжат на диске. Считаем память под кадры руками, сравниваем PNG и JPEG на кадрах витрины и разбираем ошибки, из-за которых ноутбук зависает на загрузке фото."
files: [showcase.npz]
recap:
  - "Память под картинки — ширина × высота × каналы × байт на число, как бы файл ни был сжат: 1920 × 1080 × 3 в `uint8` — 6.2 МБ, в `float32` — в 4 раза больше. Читают пакетами, сразу уменьшают, в `float32` переводят только текущий пакет."
  - "PNG — без потерь (маски, разметка), JPEG — с потерями, но намного меньше (фотографии). `PIL.Image.open` читает файл, `np.array(...)` превращает в массив, `.convert(\"RGB\")` / `.convert(\"L\")` приводит к нужным каналам."
---

Короткий урок в стороне от основной линии главы: в задачах дальше он не нужен, но пригодится, когда фото придут не готовым массивом, а файлами с настоящей камеры. Массивы картинок и тип `uint8` разобраны в уроке «Картинка — это массив чисел».

## Файлы картинок и память

Наш набор — аккуратный массив 2000 × 32 × 32. В жизни камера над витриной пишет JPEG-файлы 1920 × 1080 в цвете, тысячи в день. Прежде чем загружать их в numpy, аналитик прикидывает две вещи: сколько это займёт **на диске** и сколько **в памяти** — это разные числа, и разница бывает в десятки раз.

::: tip Аналогия
Файл JPEG — как вакуумная упаковка кофе: на полке занимает мало места, но перед варкой её вскрывают, и зерно занимает свой полный объём. В памяти картинка всегда «распакована»: ширина × высота × каналы × байт на число, как бы сильно она ни была сжата на диске.
:::

**Память — считаем руками.** Один кадр камеры: 1920 × 1080 пикселей × 3 канала = 6 220 800 чисел.

- В `uint8` (1 байт на число) — 6.2 МБ на кадр. 10 000 кадров — 62 ГБ.
- После `astype(np.float32)` (4 байта) — в 4 раза больше, 249 ГБ; после `astype(float)` (`float64`, 8 байт) — в 8 раз.
- Отсюда два правила: картинки читают с диска **пакетами** и сразу уменьшают (до 224 × 224 — стандартный размер входа готовых сетей, о них урок «Перенос обучения и дообучение» ближе к концу главы), а в `float32`, а не в `float64` переводят только текущий пакет.

**Форматы на диске.**

| формат | сжатие | что теряется | когда использовать |
|---|---|---|---|
| PNG | без потерь | ничего: после чтения те же числа | разметка, маски, скриншоты, схемы |
| JPEG | с потерями, степень задаёт `quality` | мелкие детали, резкие края, появляются «квадратики» 8 × 8 | фотографии: в 5–20 раз меньше PNG |
| BMP, `.npy` | без сжатия | ничего | промежуточные массивы, быстрое чтение |

Проверим на кадре витрины. Библиотека `Pillow` (`PIL`) читает и пишет картинки; в браузере она есть, на компьютере ставится вместе с matplotlib.

```python
import io
import numpy as np
from PIL import Image

X = np.load("showcase.npz")["X"]
img = X[0]                                          # 32 × 32, uint8
print("в памяти:", img.nbytes, "байт | весь набор:", X.nbytes, "байт, в float64:", X.astype(float).nbytes)

for fmt, opts in [("PNG", {}), ("JPEG", {"quality": 75}), ("JPEG", {"quality": 30})]:
    buf = io.BytesIO()                              # «файл» в памяти, чтобы не писать на диск
    Image.fromarray(img).save(buf, format=fmt, **opts)
    back = np.array(Image.open(io.BytesIO(buf.getvalue())))
    err = np.abs(back.astype(int) - img.astype(int))
    print(f"{fmt:<4} {opts}: {len(buf.getvalue())} байт, ошибка: средняя {err.mean():.1f}, максимальная {err.max()}")
```

**Что здесь происходит:**

- `img.nbytes` — сколько байт массив занимает в памяти: 32 × 32 × 1 = 1024.
- `Image.fromarray(img)` — массив numpy → картинка Pillow; `.save(buf, format=...)` — сохранить в нужном формате. `io.BytesIO()` ведёт себя как файл, но живёт в памяти.
- `np.array(Image.open(...))` — обратно: файл → массив той же формы и типа `uint8`.
- `err` — разница с исходными числами; переводим в `int`, чтобы `uint8` не переполнился при вычитании.

**Что получилось:** весь набор — около 2 МБ в `uint8` и 16 МБ в `float64`. PNG вернул ровно те же числа (ошибка 0), но почти не сжал маленький зашумлённый кадр — шум не сжимается. JPEG меньше, но каждый пиксель сдвинулся в среднем на 7 уровней яркости, а отдельные — на 30 с лишним. При `quality=30` файл ещё меньше (456 байт против 648), а ошибка растёт: в среднем 11.4, максимальная — 59. Для обучения на фотографиях это обычно не страшно, а для масок сегментации (урок «Регрессия по фото, детекция и сегментация») JPEG недопустим: на границе маски появятся значения вроде 3 и 252 вместо 0 и 255.

::: warn Типичные ошибки
- **`MemoryError` или зависший ноутбук** при `np.array([np.array(Image.open(p)) for p in paths])` на тысячах фото. Сначала посчитайте объём: `n × высота × ширина × 3` байт. Читайте и уменьшайте пакетами: `Image.open(p).convert("L").resize((64, 64))`.
- **`float64` по привычке.** `X / 255` даёт `float64` — в 8 раз больше памяти, чем `uint8`. Пишите `X.astype(np.float32) / 255`.
- **Маски и разметку в JPEG.** Сжатие с потерями портит точные значения: классы «0» и «1» в маске превратятся в 0, 1, 2, 3… Маски — только PNG.
- **Ширина и высота наоборот.** В Pillow размер — `(ширина, высота)`, а у массива numpy форма — `(высота, ширина)`. `Image.fromarray(a).resize((48, 32))` даёт массив формы `(32, 48)`.
- **Режим картинки.** PNG бывает с прозрачностью (`RGBA`, 4 канала) или с палитрой (`P`). Если сеть ждёт 3 канала, приводите явно: `.convert("RGB")`; для серого — `.convert("L")`.
:::

{{practice: small, memory, batches, formats, quality, mask}}

## Практика

## task: memory | Сколько памяти нужно кадрам | warmup

Камера пишет цветные кадры 1920 × 1080 (3 канала). Посчитайте, сколько гигабайт (1 ГБ = 10⁹ байт) займут в памяти 10 000 кадров в `uint8` — `gb_uint8` — и в `float32` — `gb_float32` (оба — 3 знака). Затем посчитайте `frames_224` — сколько цветных кадров, уменьшенных до 224 × 224, поместится в 8 ГБ в `uint8` (целое число).

### starter
```python
import numpy as np
h, w, ch = 1080, 1920, 3
n = 10_000

```

### check
```python
b = 1080 * 1920 * 3
assert close(need('gb_uint8'), round(b * 10_000 / 1e9, 3), 0.0015), f'gb_uint8 = {need("gb_uint8")}: пикселей × каналов × кадров × 1 байт, делённое на 10⁹.'
assert close(need('gb_float32'), round(b * 4 * 10_000 / 1e9, 3), 0.0015), f'gb_float32 = {need("gb_float32")}: у float32 4 байта на число.'
assert need('frames_224') == int(8e9 // (224 * 224 * 3)), f'frames_224 = {need("frames_224")}. Кадр 224 × 224 × 3 байт; сколько целых таких кадров в 8·10⁹ байт.'
```

### hint
Байт на кадр — `h * w * ch` (по байту на число в `uint8`); у `float32` — в 4 раза больше. Можно проверить себя: `np.zeros((h, w, ch), dtype=np.uint8).nbytes`.

### hint
Целое число кадров — деление без остатка: `int(8e9 // (224 * 224 * 3))`.

### solution
```python
import numpy as np
h, w, ch = 1080, 1920, 3
n = 10_000

frame_bytes = np.zeros((h, w, ch), dtype=np.uint8).nbytes      # 6 220 800 байт
gb_uint8 = round(frame_bytes * n / 1e9, 3)
gb_float32 = round(frame_bytes * 4 * n / 1e9, 3)
frames_224 = int(8e9 // (224 * 224 * 3))
print(gb_uint8, gb_float32, frames_224)
```

### explain
62 ГБ в `uint8` и почти 250 ГБ в `float32` — столько памяти нет ни в одном ноутбуке, хотя на диске те же 10 000 кадров в JPEG займут единицы гигабайт. После уменьшения до 224 × 224 в 8 ГБ влезает около 53 тысяч кадров. Поэтому картинки не загружают «все сразу», а читают пакетами по 32–256 штук прямо перед подачей в модель.

## task: formats | PNG против JPEG | base

Сохраните первые 100 кадров `X[:100]` в память (`io.BytesIO`) дважды — в PNG и в JPEG с `quality=75` — и прочитайте обратно. Посчитайте: `share_png` и `share_jpeg` — суммарный размер файлов как доля от `X[:100].nbytes` (3 знака), `mae_jpeg` — среднюю абсолютную ошибку пикселя после JPEG по всем 100 кадрам (2 знака) и `lossless` — `True`, если после PNG **все** кадры совпали с исходными до единого пикселя.

### starter
```python
import io
import numpy as np
from PIL import Image

X = np.load("showcase.npz")["X"]

def roundtrip(img, fmt, **opts):
    """Сохранить картинку в память и прочитать обратно: (размер в байтах, массив)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt, **opts)
    data = buf.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)))

```

### check
```python
import io as _io, numpy as _np
from PIL import Image as _I
X0 = _np.load('showcase.npz')['X'][:100]
def _rt(img, fmt, **o):
    b = _io.BytesIO(); _I.fromarray(img).save(b, format=fmt, **o); d = b.getvalue()
    return len(d), _np.array(_I.open(_io.BytesIO(d)))
sp = sj = 0; errs = []; ok = True
for img in X0:
    n, back = _rt(img, 'PNG'); sp += n; ok = ok and _np.array_equal(back, img)
    n, back = _rt(img, 'JPEG', quality=75); sj += n; errs.append(_np.abs(back.astype(int) - img.astype(int)))
assert close(need('share_png'), round(sp / X0.nbytes, 3), 0.0015), f'share_png = {need("share_png")}, а нужно {sp / X0.nbytes:.3f}. Сумма размеров PNG-файлов / X[:100].nbytes.'
assert close(need('share_jpeg'), round(sj / X0.nbytes, 3), 0.0015), f'share_jpeg = {need("share_jpeg")}, а нужно {sj / X0.nbytes:.3f}.'
m = round(float(_np.mean(errs)), 2)
assert close(need('mae_jpeg'), m, 0.011), f'mae_jpeg = {need("mae_jpeg")}, а нужно {m}. Вычитайте в int: в uint8 разность «переворачивается» (3 − 5 = 254).'
assert need('lossless') is True or need('lossless') == True, 'lossless: PNG — сжатие без потерь, все кадры должны совпасть (np.array_equal).'
```

### hint
Цикл по `X[:100]`: для каждого кадра `roundtrip(img, "PNG")` и `roundtrip(img, "JPEG", quality=75)`; размеры складывайте, ошибки JPEG копите в список.

### hint
Ошибка кадра — `np.abs(back.astype(int) - img.astype(int))`. Совпадение — `np.array_equal(back, img)`; «все кадры» — `all(...)`.

### hint
```python
size_png = size_jpeg = 0
errors, same = [], []
for img in X[:100]:
    n, back = roundtrip(img, "PNG")
    size_png += n
    same.append(np.array_equal(back, img))
    ...
share_png = round(size_png / X[:100].nbytes, 3)
```

### solution
```python
import io
import numpy as np
from PIL import Image

X = np.load("showcase.npz")["X"]

def roundtrip(img, fmt, **opts):
    """Сохранить картинку в память и прочитать обратно: (размер в байтах, массив)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt, **opts)
    data = buf.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)))

size_png = size_jpeg = 0
errors, same = [], []
for img in X[:100]:
    n, back = roundtrip(img, "PNG")
    size_png += n
    same.append(np.array_equal(back, img))
    n, back = roundtrip(img, "JPEG", quality=75)
    size_jpeg += n
    errors.append(np.abs(back.astype(int) - img.astype(int)))

raw = X[:100].nbytes
share_png = round(size_png / raw, 3)
share_jpeg = round(size_jpeg / raw, 3)
mae_jpeg = round(float(np.mean(errors)), 2)
lossless = all(same)
print(share_png, share_jpeg, mae_jpeg, lossless)
```

### explain
PNG сжал кадры всего примерно до 95 % исходного объёма и вернул их без единой ошибки; JPEG — примерно до 62 %, но каждый пиксель сдвинулся в среднем на 7 уровней яркости из 255. На маленьких зашумлённых вырезках выигрыш скромный: шум не сжимается. На настоящих фотографиях 1920 × 1080 с плавными участками JPEG обычно в 5–20 раз меньше PNG. Если бы вы вычитали `back - img` прямо в `uint8`, отрицательные разности «перевернулись» бы в числа около 250, и средняя ошибка вышла бы в разы больше настоящей — это та же ловушка переполнения, что в задаче «Сделать ярче без поломки» урока «Картинка — это массив чисел».

## task: small | Серый и маленький | warmup

В `rgb` — цветной кадр витрины 64 × 96 при тёплом вечернем свете. Модель ждёт серые картинки вдвое меньше. С помощью Pillow переведите кадр в серый (`.convert("L")`) и уменьшите до ширины 48 и высоты 32. Результат как массив numpy сохраните в `small`, а в `ratio` — во сколько раз `small` занимает меньше памяти, чем `rgb` (через `.nbytes`).

### setup
```python
import numpy as np
X = np.load("showcase.npz")["X"]
frame = np.vstack([np.hstack(X[0:3]), np.hstack(X[3:6])])                     # 64 × 96
rgb = np.stack([frame, (frame * 0.9).astype(np.uint8), (frame * 0.7).astype(np.uint8)], axis=-1)
```

### starter
```python
import numpy as np
from PIL import Image
# готово, как в теории: rgb — массив (64, 96, 3) типа uint8

```

### check
```python
import numpy as _np
from PIL import Image as _I
_X = _np.load('showcase.npz')['X']
_f = _np.vstack([_np.hstack(_X[0:3]), _np.hstack(_X[3:6])])
_rgb = _np.stack([_f, (_f * 0.9).astype(_np.uint8), (_f * 0.7).astype(_np.uint8)], axis=-1)
want = _np.array(_I.fromarray(_rgb).convert('L').resize((48, 32)))
got = need('small', _np.ndarray)
assert got.ndim == 2, f'small.shape = {got.shape}: серая картинка — двумерный массив, один канал. Нужен .convert("L").'
assert got.shape == (32, 48), f'small.shape = {got.shape}, а нужно (32, 48). В Pillow размер пишут как (ширина, высота): resize((48, 32)).'
assert got.dtype == _np.uint8, f'small.dtype = {got.dtype}, а нужен uint8 — np.array(картинки Pillow) без astype.'
assert _np.abs(got.astype(int) - want.astype(int)).max() <= 1, 'Числа в small не совпадают с convert("L").resize((48, 32)) — проверьте порядок шагов.'
assert close(need('ratio'), _rgb.nbytes / want.nbytes, 0.01), f'ratio = {need("ratio")}, а нужно {_rgb.nbytes / want.nbytes:g}: rgb.nbytes / small.nbytes.'
```

### hint
Цепочка: `Image.fromarray(rgb)` → `.convert("L")` → `.resize(...)` → `np.array(...)`.

### hint
Pillow принимает размер как `(ширина, высота)`: `.resize((48, 32))`. Массив получится формы `(32, 48)` — у numpy сначала строки.

### solution
```python
import numpy as np
from PIL import Image

small = np.array(Image.fromarray(rgb).convert("L").resize((48, 32)))
ratio = rgb.nbytes / small.nbytes
print(small.shape, small.dtype, ratio)
```

### explain
Три канала превратились в один, а сторона уменьшилась вдвое — пикселей стало в 4 раза меньше. Вместе это 3 × 4 = 12: кадр занимает в 12 раз меньше памяти (18 432 байт против 1 536). Если написать `resize((32, 48))`, получится кадр высотой 48 и шириной 32 — картинка «сплющится» без всякой ошибки, поэтому форму результата стоит печатать каждый раз.

## task: batches | Пакеты вместо «всё сразу» | base

10 000 кадров уменьшены до 224 × 224, в цвете (3 канала), и подаются в сеть пакетами по 64 кадра в `float32`. Посчитайте `batch_mb` — сколько мегабайт (1 МБ = 10⁶ байт) занимает один пакет (1 знак), `n_batches` — сколько пакетов нужно на все кадры, `last_size` — сколько кадров в последнем, неполном пакете, и `all_gb` — сколько гигабайт заняли бы все 10 000 кадров в `float32` разом (2 знака).

### starter
```python
import numpy as np
n, side, ch, batch = 10_000, 224, 3, 64

```

### check
```python
fb = 224 * 224 * 3 * 4
assert close(need('batch_mb'), round(fb * 64 / 1e6, 1), 0.051), f'batch_mb = {need("batch_mb")}: 224 × 224 × 3 чисел × 4 байта × 64 кадра, делённое на 10⁶.'
assert need('n_batches') == 157, f'n_batches = {need("n_batches")}. 10 000 / 64 не делится нацело — последний неполный пакет тоже считается.'
assert need('last_size') == 10_000 - 156 * 64, f'last_size = {need("last_size")}: остаток от деления 10 000 на 64.'
assert close(need('all_gb'), round(fb * 10_000 / 1e9, 2), 0.0051), f'all_gb = {need("all_gb")}: байт на кадр × 10 000 / 10⁹.'
```

### hint
Байт на кадр в `float32` — `side * side * ch * 4`. Пакет — это 64 таких кадра.

### hint
Пакетов — деление с округлением вверх: `int(np.ceil(n / batch))` или `(n + batch - 1) // batch`. Остаток — `n % batch`.

### solution
```python
import numpy as np
n, side, ch, batch = 10_000, 224, 3, 64

frame_bytes = side * side * ch * 4                 # float32 — 4 байта на число
batch_mb = round(frame_bytes * batch / 1e6, 1)
n_batches = int(np.ceil(n / batch))
last_size = n % batch
all_gb = round(frame_bytes * n / 1e9, 2)
print(batch_mb, n_batches, last_size, all_gb)
```

### explain
Пакет из 64 кадров весит около 38.5 МБ — это помещается в память любого ноутбука и видеокарты, а все кадры разом заняли бы 6.02 ГБ. Пакетов 157: 156 полных и последний из 16 кадров. Про неполный пакет стоит помнить — если код ждёт ровно 64 кадра, на последнем он упадёт.

## task: quality | Цена качества JPEG | base

Сохраните первые 100 кадров `X[:100]` в JPEG с качеством `[90, 75, 50, 30, 10]`. Для каждого качества посчитайте долю суммарного размера файлов от `X[:100].nbytes` и среднюю абсолютную ошибку пикселя. Сохраните `table` — DataFrame с индексом «качество» и столбцами `share` (3 знака) и `mae` (2 знака), а `q_half` — самое высокое качество, при котором файлы меньше половины исходного объёма.

### starter
```python
import io
import numpy as np
import pandas as pd
from PIL import Image

X = np.load("showcase.npz")["X"]

def roundtrip(img, fmt, **opts):
    """Сохранить картинку в память и прочитать обратно: (размер в байтах, массив)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt, **opts)
    data = buf.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)))

```

### check
```python
import pandas as _pd
want = {90: (0.8, 3.04), 75: (0.619, 7.08), 50: (0.492, 9.81), 30: (0.432, 10.93), 10: (0.362, 13.1)}
t = need('table', _pd.DataFrame)
assert sorted(int(q) for q in t.index) == sorted(want), f'В индексе table — {sorted(int(q) for q in t.index)}, а нужны качества {sorted(want)}.'
for q, (sh, m) in want.items():
    assert close(t.loc[q, 'share'], sh, 0.0015), f'share при quality={q}: {float(t.loc[q, "share"])}, а нужно {sh}.'
    assert close(t.loc[q, 'mae'], m, 0.011), f'mae при quality={q}: {float(t.loc[q, "mae"])}, а нужно {m}. Вычитайте в int, а не в uint8.'
assert need('q_half') == max(q for q in want if want[q][0] < 0.5), f'q_half = {need("q_half")}. Ищите самое высокое качество, у которого share < 0.5.'
```

### hint
Внешний цикл — по качествам, внутренний — по кадрам: `roundtrip(img, "JPEG", quality=q)`. Размеры складывайте, ошибки `np.abs(back.astype(int) - img.astype(int))` копите в список и усредняйте.

### hint
Строки таблицы удобно копить в словарь `{q: {"share": ..., "mae": ...}}`, а потом `pd.DataFrame(rows).T`. Ответ: `max(q for q in table.index if table.loc[q, "share"] < 0.5)`.

### solution
```python
import io
import numpy as np
import pandas as pd
from PIL import Image

X = np.load("showcase.npz")["X"]

def roundtrip(img, fmt, **opts):
    """Сохранить картинку в память и прочитать обратно: (размер в байтах, массив)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt, **opts)
    data = buf.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)))

raw = X[:100].nbytes
rows = {}
for q in [90, 75, 50, 30, 10]:
    size, errors = 0, []
    for img in X[:100]:
        n, back = roundtrip(img, "JPEG", quality=q)
        size += n
        errors.append(np.abs(back.astype(int) - img.astype(int)))
    rows[q] = {"share": round(size / raw, 3), "mae": round(float(np.mean(errors)), 2)}
table = pd.DataFrame(rows).T
q_half = max(q for q in table.index if table.loc[q, "share"] < 0.5)
print(table)
print(q_half)
```

### explain
При `quality=90` файлы занимают 80 % исходного объёма с ошибкой около 3 уровней, при 75 — 62 % и ошибка 7, при 50 — уже меньше половины (49 %), но ошибка почти 10. Дальше выигрыш в размере маленький (43 % и 36 %), а ошибка продолжает расти до 13. Качество 75–90 — разумный выбор для архива кадров: на маленьких шумных вырезках сильнее не сожмёшь, а детали начинают теряться.

## task: mask | Маска в JPEG | plus

Маска выпечки — кадр, где тёмные пиксели (меньше 100) помечены 255, а остальные — 0. Для первых 100 кадров постройте маски и сохраните их в JPEG (`quality=90`) и в PNG. Посчитайте: `share_gray` — долю пикселей, которые после JPEG стали не 0 и не 255 (3 знака); `share_flipped` — долю пикселей, у которых после JPEG и порога `>= 128` поменялся класс (3 знака); `jpeg_share` и `png_share` — суммарный размер файлов JPEG и PNG как долю от объёма масок в памяти (3 знака).

### starter
```python
import io
import numpy as np
from PIL import Image

X = np.load("showcase.npz")["X"]
masks = ((X[:100] < 100) * 255).astype(np.uint8)

def roundtrip(img, fmt, **opts):
    """Сохранить картинку в память и прочитать обратно: (размер в байтах, массив)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt, **opts)
    data = buf.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)))

```

### check
```python
import io as _io, numpy as _np
from PIL import Image as _I
_M = ((_np.load('showcase.npz')['X'][:100] < 100) * 255).astype(_np.uint8)
def _rt(img, fmt, **o):
    b = _io.BytesIO(); _I.fromarray(img).save(b, format=fmt, **o); d = b.getvalue()
    return len(d), _np.array(_I.open(_io.BytesIO(d)))
_g, _f, _sj, _sp = [], [], 0, 0
for _m in _M:
    n, b = _rt(_m, 'JPEG', quality=90); _sj += n
    _g.append(~_np.isin(b, [0, 255])); _f.append((b >= 128) != (_m == 255))
    _sp += _rt(_m, 'PNG')[0]
w = {'share_gray': round(float(_np.mean(_g)), 3), 'share_flipped': round(float(_np.mean(_f)), 3),
     'jpeg_share': round(_sj / _M.nbytes, 3), 'png_share': round(_sp / _M.nbytes, 3)}
tips = {'share_gray': 'ищите пиксели после JPEG, которых нет среди 0 и 255: ~np.isin(back, [0, 255])',
        'share_flipped': 'класс после порога — back >= 128, исходный — mask == 255',
        'jpeg_share': 'сумма размеров JPEG / masks.nbytes', 'png_share': 'сумма размеров PNG / masks.nbytes'}
for k, v in w.items():
    assert close(need(k), v, 0.0015), f'{k} = {need(k)}, а нужно {v}: {tips[k]}.'
```

### hint
Цикл по `masks`: `roundtrip(m, "JPEG", quality=90)` и `roundtrip(m, "PNG")`. Для JPEG копите два массива `True/False`: `~np.isin(back, [0, 255])` и `(back >= 128) != (m == 255)`; среднее по списку таких массивов — доля.

### hint
```python
gray, flipped = [], []
size_jpeg = size_png = 0
for m in masks:
    n, back = roundtrip(m, "JPEG", quality=90)
    size_jpeg += n
    gray.append(~np.isin(back, [0, 255]))
    ...
share_gray = round(float(np.mean(gray)), 3)
```

### solution
```python
import io
import numpy as np
from PIL import Image

X = np.load("showcase.npz")["X"]
masks = ((X[:100] < 100) * 255).astype(np.uint8)

def roundtrip(img, fmt, **opts):
    """Сохранить картинку в память и прочитать обратно: (размер в байтах, массив)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt, **opts)
    data = buf.getvalue()
    return len(data), np.array(Image.open(io.BytesIO(data)))

gray, flipped = [], []
size_jpeg = size_png = 0
for m in masks:
    n, back = roundtrip(m, "JPEG", quality=90)
    size_jpeg += n
    gray.append(~np.isin(back, [0, 255]))
    flipped.append((back >= 128) != (m == 255))
    n, _ = roundtrip(m, "PNG")
    size_png += n

share_gray = round(float(np.mean(gray)), 3)
share_flipped = round(float(np.mean(flipped)), 3)
jpeg_share = round(size_jpeg / masks.nbytes, 3)
png_share = round(size_png / masks.nbytes, 3)
print(share_gray, share_flipped, jpeg_share, png_share)
```

### explain
После JPEG 11.5 % пикселей маски стали «серыми» — ни 0, ни 255: сжатие размазало границы. Здесь порог 128 вернул все классы на место, но так везёт не всегда: при низком качестве и узких деталях пиксели меняют класс, а у масок с номерами классов 0, 1, 2, 3 порога «посередине» вообще нет. И главное: PNG для маски не только точнее, но и в 5 раз меньше JPEG (11 % против 53 % объёма). Большие одноцветные области PNG сжимает отлично, а JPEG тратит байты на «квадратики» у границ.
