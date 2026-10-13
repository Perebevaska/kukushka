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
- Отсюда два правила: картинки читают с диска **пакетами** и сразу уменьшают (до 224 × 224 — стандартный размер входа готовых сетей, о них урок «Перенос обучения и дообучение»), а в `float32`, а не в `float64` переводят только текущий пакет.

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

**Что получилось:** весь набор — около 2 МБ в `uint8` и 16 МБ в `float64`. PNG вернул ровно те же числа (ошибка 0), но почти не сжал маленький зашумлённый кадр — шум не сжимается. JPEG меньше, но каждый пиксель сдвинулся в среднем на 7 уровней яркости, а отдельные — на 30 с лишним; при `quality=30` ещё сильнее. Для обучения на фотографиях это обычно не страшно, а для масок сегментации (урок «Регрессия по фото, детекция и сегментация») JPEG недопустим: на границе маски появятся значения вроде 3 и 252 вместо 0 и 255.

::: warn Типичные ошибки
- **`MemoryError` или зависший ноутбук** при `np.array([np.array(Image.open(p)) for p in paths])` на тысячах фото. Сначала посчитайте объём: `n × высота × ширина × 3` байт. Читайте и уменьшайте пакетами: `Image.open(p).convert("L").resize((64, 64))`.
- **`float64` по привычке.** `X / 255` даёт `float64` — в 8 раз больше памяти, чем `uint8`. Пишите `X.astype(np.float32) / 255`.
- **Маски и разметку в JPEG.** Сжатие с потерями портит точные значения: классы «0» и «1» в маске превратятся в 0, 1, 2, 3… Маски — только PNG.
- **Режим картинки.** PNG бывает с прозрачностью (`RGBA`, 4 канала) или с палитрой (`P`). Если сеть ждёт 3 канала, приводите явно: `.convert("RGB")`; для серого — `.convert("L")`.
:::

{{practice: memory, formats}}

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
