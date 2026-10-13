---
title: "Перенос обучения и дообучение"
lead: "Для обычных фотографий сеть с нуля почти не учат: берут готовую, обученную на миллионе снимков, и подстраивают под свои классы. Разбираем два способа — признаки готовой сети и дообучение по шагам, — загружаем фото из папок классов, где попадаются мусорные и битые файлы, и смотрим, почему ResNet может быть такой глубокой."
files: [showcase.npz]
recap:
  - "Перенос обучения: взять сеть, обученную на миллионах фотографий (ResNet и др.), отрезать последний слой и использовать её выходы как признаки или дообучить на своих данных."
  - "Фото для обучения лежат по папкам классов: `sorted(p for p in root.rglob(\"*\") if p.suffix.lower() == \".png\")`, метка — `p.parent.name`, классы нумеруются по алфавиту (как у `ImageFolder`). Мусор и битые файлы отсеивают фильтром расширений и `try/except`."
  - "Дообучение: своя голова → обучить её при замороженном теле → разморозить верхний блок с шагом в 10 раз меньше. Skip-связи ResNet (`y = x + F(x)`) пропускают градиент через десятки слоёв."
---

Урок продолжает урок «Свёрточные нейросети»: там разобраны свёрточные слои и сеть на PyTorch. Код с PyTorch здесь — для вашего компьютера; в браузере работает задача про папки с фото.

## Перенос обучения

Свою сеть с нуля учат, когда данных много или картинки необычные (как наши 32 × 32 серые вырезки). Для обычных фотографий — товаров, документов, людей, интерьеров — почти всегда берут **предобученную** сеть: ResNet, EfficientNet, ViT, обученные на миллионе фотографий ImageNet. Её первые слои уже умеют находить края, текстуры, формы — это знание переносится на любые фото.

::: tip Аналогия
Это как взять в «Зерно» бариста с опытом из другой сети: ему не нужно объяснять, как держать питчер и взбивать молоко, — достаточно показать ваше меню и пару фирменных напитков. Предобученная сеть так же приносит готовое умение видеть края, текстуры и формы, а учить остаётся последний слой под ваши классы. Хромает аналогия в одном: опытный бариста сам заметит, где старые привычки не подходят, а сеть — нет: чем меньше ваши картинки похожи на фотографии ImageNet, тем меньше пользы от переноса.
:::

Два варианта:

- **Сеть как извлекатель признаков.** Отрезать последний слой, прогнать свои фото и получить вектор из нескольких сотен чисел на фото. Дальше — логистическая регрессия или лес, как на любой таблице признаков (если проходили главу 13 — это те же эмбеддинги, что у текстов). Хватает сотни фото на класс.
- **Дообучение (fine-tuning).** Заменить последний слой на свой и дообучить всю сеть (или верхние слои) с маленьким шагом. Точнее, но нужно больше данных и времени.

```python static
# uv add torch torchvision pillow scikit-learn
import torch
from torch import nn
from torchvision import models
from PIL import Image

weights = models.ResNet18_Weights.DEFAULT
resnet = models.resnet18(weights=weights)       # веса скачаются при первом запуске (~45 МБ)
resnet.fc = nn.Identity()                       # отрезали классификатор ImageNet: выход — 512 признаков
resnet.eval()
prep = weights.transforms()                     # масштаб, обрезка, нормировка — как при обучении ResNet

def embed(paths):
    batch = torch.stack([prep(Image.open(p).convert("RGB")) for p in paths])
    with torch.no_grad():
        return resnet(batch).numpy()            # (число фото, 512)

# E = embed(список_путей_к_фото); дальше — LogisticRegression().fit(E, метки)
```

**Что здесь происходит:**

- `models.resnet18(weights=...)` — готовая сеть из 18 слоёв, обученная на ImageNet (1000 классов: от кошек до кофемашин).
- `resnet.fc = nn.Identity()` — последний слой (классификатор на 1000 классов) заменяем «ничем»: сеть теперь выдаёт 512 чисел — описание фото.
- `weights.transforms()` — та же подготовка фото, что при обучении ResNet: размер 224 × 224, нормировка каналов. Без неё признаки будут хуже.
- `.convert("RGB")` — ResNet ждёт 3 канала; чёрно-белое фото превращается в три одинаковых канала.

::: tip
Признаки предобученной сети считают один раз и сохраняют (`np.save`), как эмбеддинги текстов. Обучение модели поверх них занимает секунды, и можно спокойно перебирать модели и пороги.
:::

Схему «замороженный извлекатель признаков + простая модель сверху» вы уже пробовали без PyTorch: случайные фильтры с пулингом из урока «Свёрточные нейросети» тоже никто не обучал, а логистическая регрессия поверх них учится за секунды. Предобученная сеть — та же схема, только фильтры не случайные, а выученные на миллионе фотографий.

## Картинки из папок: `pathlib` и `ImageFolder`

`embed(paths)` выше принимает список путей к фото. Откуда он берётся? Фотографии для обучения почти всегда лежат на диске по договорённости «одна папка — один класс»:

```text
vitrina/
├── train/
│   ├── круассан/   0001.png  0002.png  …
│   ├── маффин/     …
│   ├── печенье/    …
│   └── пусто/      …
└── test/
    └── …те же папки…
```

Метка фото — имя папки, в которой оно лежит. Значит, загрузка — это обход папок: собрать пути, для каждого прочитать картинку и взять имя родительской папки.

::: sql
Структура папок — это таблица `files(path, class)`, где `class` хранится не в столбце, а в пути. «Сколько фото в каждом классе» — `SELECT class, COUNT(*) … GROUP BY class`, только `class` сначала надо вырезать из пути: у `pathlib` это `path.parent.name`.
:::

Игрушечный пример: разложим 12 кадров витрины по папкам классов, а затем загрузим обратно так, как загружали бы настоящие фото.

```python
from pathlib import Path
import numpy as np
from PIL import Image

d = np.load("showcase.npz")
X, y, classes = d["X"], d["y"], d["classes"]

root = Path("vitrina_demo/train")
for c in range(4):                                     # по 3 кадра каждого класса — в свою папку
    folder = root / classes[c]
    folder.mkdir(parents=True, exist_ok=True)
    for k, i in enumerate(np.flatnonzero(y == c)[:3]):
        Image.fromarray(X[i]).save(folder / f"{k:04d}.png")

paths = sorted(root.rglob("*.png"))                    # все PNG во всех подпапках
print(len(paths), paths[0], "→ класс:", paths[0].parent.name)

names = sorted({p.parent.name for p in paths})         # классы — по алфавиту, как у ImageFolder
to_idx = {name: i for i, name in enumerate(names)}
imgs = np.stack([np.array(Image.open(p).convert("L")) for p in paths])
labels = np.array([to_idx[p.parent.name] for p in paths])
print(imgs.shape, imgs.dtype, labels, to_idx)
```

**Что здесь происходит:**

- `Path("vitrina_demo/train") / classes[c]` — оператор `/` склеивает части пути правильно для любой системы (Windows, macOS, Linux). Строки через `+ "/" +` так не умеют.
- `folder.mkdir(parents=True, exist_ok=True)` — создать папку вместе с родительскими; если уже есть — не ошибка.
- `root.rglob("*.png")` — рекурсивный поиск файлов по шаблону во всех подпапках; `sorted` — чтобы порядок не зависел от файловой системы.
- `p.parent.name` — имя папки, в которой лежит файл: это и есть метка.
- `Image.open(p).convert("L")` — открыть и привести к серому (1 канал), `np.stack` — собрать список картинок 32 × 32 в массив (12, 32, 32).

**Что получилось:** 12 путей, у каждого класс — имя папки, массив картинок и метки. Номера классов назначены по алфавиту имён папок — так же это делает `ImageFolder`. Обратите внимание: в `showcase.npz` «пусто» — класс 0, а здесь — 3. Номер класса ничего не значит сам по себе, важно, чтобы при обучении и применении модели словарь «имя → номер» был один и тот же.

В PyTorch этот обход уже написан — `torchvision.datasets.ImageFolder`. Он же применяет к каждому фото преобразования, а `DataLoader` отдаёт фото пакетами — не нужно держать всё в памяти (урок «Файлы картинок и память»):

```python static
# uv add torch torchvision
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

prep = transforms.Compose([
    transforms.Grayscale(),                 # 1 канал, как наши кадры
    transforms.Resize((32, 32)),
    transforms.ToTensor(),                  # uint8 0–255 → float32 0–1, форма (каналы, высота, ширина)
])
train = datasets.ImageFolder("vitrina/train", transform=prep)
print(train.classes, train.class_to_idx)    # ['круассан', 'маффин', 'печенье', 'пусто'] → 0, 1, 2, 3
loader = DataLoader(train, batch_size=64, shuffle=True)
for xb, yb in loader:                       # xb: (64, 1, 32, 32), yb: (64,)
    ...
```

::: warn Типичные ошибки
- **Мусорные файлы в папках.** macOS кладёт `.DS_Store`, Windows — `Thumbs.db`, кто-то сохранит `заметки.txt`. Ищите по расширениям (`rglob("*.png")`, `*.jpg`, `*.jpeg` — с учётом регистра: `IMG_001.JPG`), а не «все файлы подряд».
- **Битые файлы.** Недокачанный файл падает при чтении с `PIL.UnidentifiedImageError`. Оборачивайте чтение в `try/except` и выводите список пропущенных, а не останавливайте загрузку на 5000-м фото.
- **Порядок классов.** `ImageFolder` нумерует классы по алфавиту имён папок. Если в тесте нет одной папки или имя набрано иначе («Круассан»), номера сдвинутся, и модель будет «ошибаться» во всём. Сравнивайте `class_to_idx` у обучения и теста.
- **Абсолютные пути в коде** (`C:\Users\…`) ломают блокнот на другом компьютере. Путь — относительно проекта: `Path("data") / "vitrina"`.
:::

{{practice: folders}}

## Дообучение по шагам

Вариант «сеть как извлекатель признаков» быстрый, но признаки ImageNet не знают ваших товаров. **Дообучение** (fine-tuning) подстраивает и сами признаки. Порядок работы, проверенный практикой:

1. **Заменить голову.** Последний слой ResNet — `nn.Linear(512, 1000)` под классы ImageNet. Ставим свой: `nn.Linear(512, 4)` под четыре класса витрины.
2. **Заморозить тело и обучить голову.** У всех слоёв, кроме нового, `requires_grad = False`: веса не меняются. Новый слой начинается со случайных весов, и пока он не обучен, его большие градиенты испортили бы хорошие предобученные признаки.
3. **Разморозить верхний блок с маленьким шагом.** Например, `layer4` (последние свёртки) с шагом в 10 раз меньше, чем у головы. Нижние слои (края, текстуры) универсальны — их часто не трогают совсем.
4. **Следить за валидацией.** На маленьких данных дообучение быстро переобучается: берите аугментацию (урок «Модели на пикселях: ошибки, аугментация, устойчивость») и останавливайтесь, когда качество на валидации перестало расти.

```python static
import torch
from torch import nn
from torchvision import models

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.fc = nn.Linear(model.fc.in_features, 4)           # своя голова: 512 → 4 класса

for p in model.parameters():                            # шаг 2: заморозить всё…
    p.requires_grad = False
for p in model.fc.parameters():                         # …кроме головы
    p.requires_grad = True
opt = torch.optim.Adam(model.fc.parameters(), lr=1e-3)
# … несколько эпох обучения головы …

for p in model.layer4.parameters():                     # шаг 3: разморозить верхний блок
    p.requires_grad = True
opt = torch.optim.Adam([
    {"params": model.fc.parameters(), "lr": 1e-3},
    {"params": model.layer4.parameters(), "lr": 1e-4},  # в 10 раз осторожнее
])
model.train()                                            # при обучении; перед проверкой — model.eval()
```

::: figure finetune-steps
Шаги 2 и 3 схемой: сначала учится только новая голова, тело заморожено; затем размораживается верхний блок `layer4` с шагом в 10 раз меньше, чем у головы.
:::

- `model.fc.in_features` — сколько чисел приходит в последний слой (512 у ResNet-18), чтобы не вписывать руками.
- `requires_grad = False` — для этих весов градиент не считается, оптимизатор их не меняет; обучение ещё и быстрее.
- Список словарей в `Adam` — **группы параметров** со своим шагом обучения.
- `model.train()` / `model.eval()` переключают слои, которые ведут себя по-разному при обучении и применении (dropout, BatchNorm).

::: deep Почему ResNet может быть глубокой: skip-связи
До ResNet (2015) сети глубже 20–30 слоёв обучались **хуже** мелких — причём хуже даже на обучающих данных, то есть дело не в переобучении, а в том, что такую сеть трудно оптимизировать. Одна из причин видна прямо из цепного правила (глава 11): градиент для первого слоя — произведение производных всех слоёв выше. Если каждая около 0.5, то через 30 слоёв остаётся 0.5³⁰ ≈ 9 · 10⁻¹⁰ — нижние слои не учатся.

ResNet складывает вход блока с его выходом: $y = x + F(x)$, где $F$ — пара свёрток. Это **skip-связь** («обходной путь»). Производная блока по входу — $1 + F'(x)$: даже если $F'$ маленькая, остаётся единица, и градиент проходит через блок почти без потерь. Блоку не нужно выучивать преобразование целиком, только **поправку** к входу; если поправка не нужна, достаточно $F \approx 0$ — блок становится «прозрачным».

```python
import numpy as np

rng = np.random.default_rng(0)
local = rng.normal(0, 0.1, size=30)          # небольшие производные F'(x) тридцати блоков
print("без skip-связей (каждый слой ×0.5):", 0.5 ** 30)
print("со skip-связями (каждый блок ×(1 + F')):", round(float(np.prod(1 + local)), 3))
```

Через 30 блоков со skip-связями градиент остаётся порядка единицы (здесь около 0.62), без них — исчезает. Поэтому ResNet бывают на 50, 101 и 152 слоя, а skip-связи с тех пор есть почти в каждой большой сети, включая трансформеры, на которых работают языковые модели.
:::

::: note Практика — в своём блокноте
ResNet в браузере не запустить, поэтому задачи на дообучение здесь нет. Проверьте шаги у себя (`uv add torch torchvision`), подсчитав обучаемые параметры после каждого шага: `sum(p.numel() for p in model.parameters() if p.requires_grad)`.

1. После шага 2 должно получиться **2 052** — только голова, 512 · 4 + 4, из 11 178 564 параметров сети (0.02 %). Формула та же, что в задаче «Считаем параметры».
2. После шага 3 — **8 395 780**: блок `layer4` один содержит 8 393 728 весов, три четверти сети. Поэтому его размораживают с шагом в 10 раз меньше.
3. Если после шага 2 число больше 2 052 — какой-то слой остался размороженным; если 0 — заморозили и голову.
:::

## Практика

## task: folders | Загрузить фото из папок | base

В заготовке на диске создана папка `vitrina/train` с подпапками классов — как приходят фото от фотографа. Кроме картинок там есть мусор: служебные файлы систем, заметки, один битый PNG, а одна фотография сохранена с расширением в верхнем регистре (`.PNG`). Загрузите все **читаемые** PNG (расширение без учёта регистра) в массив `X` формы (n, 32, 32), метки — в `y` (номер класса по алфавиту имён папок, как у `ImageFolder`), имена классов — в `classes` (список по алфавиту). Сохраните `counts` — словарь «класс → число фото» и `bad` — список имён файлов (`path.name`), которые не удалось прочитать.

### setup
```python
import numpy as _np
from pathlib import Path as _P
from PIL import Image as _I
_d = _np.load("showcase.npz")
_root = _P("vitrina/train")
for _c in range(4):
    _f = _root / str(_d["classes"][_c]); _f.mkdir(parents=True, exist_ok=True)
    for _k, _i in enumerate(_np.flatnonzero(_d["y"] == _c)[:10]):
        _I.fromarray(_d["X"][_i]).save(_f / f"{_k:04d}.png")
_I.fromarray(_d["X"][_np.flatnonzero(_d["y"] == 1)[50]]).save(_root / "круассан" / "IMG_7.PNG", format="PNG")
(_root / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1")
(_root / "маффин" / "Thumbs.db").write_bytes(b"\xd0\xcf\x11\xe0")
(_root.parent / "readme.txt").write_text("фото с витрины KZN-1, август", encoding="utf-8")
(_root / "печенье" / "битый.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"oops" * 5)
```

### starter
```python
from pathlib import Path
import numpy as np
from PIL import Image

root = Path("vitrina/train")
print(sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())[:6])

```

### check
```python
import numpy as _np
from pathlib import Path as _P
from PIL import Image as _I
_root = _P('vitrina/train')
ps = sorted(p for p in _root.rglob('*') if p.is_file() and p.suffix.lower() == '.png')
good, lab, badw = [], [], []
names = sorted({p.parent.name for p in ps})
for p in ps:
    try:
        good.append(_np.array(_I.open(p).convert('L'))); lab.append(names.index(p.parent.name))
    except Exception:
        badw.append(p.name)
assert list(need('classes')) == names, f'classes = {list(need("classes"))}, а нужно {names}: имена папок по алфавиту.'
Xs = _np.asarray(need('X'))
assert Xs.shape == (len(good), 32, 32), f'X.shape = {Xs.shape}, а нужно {(len(good), 32, 32)}. Проверьте, что нашлись файлы .PNG в верхнем регистре и пропущены битые и не-картинки.'
order = sorted(range(len(good)), key=lambda i: (lab[i], good[i].tobytes()))
mine = sorted(range(len(Xs)), key=lambda i: (int(need('y')[i]), Xs[i].astype(_np.uint8).tobytes()))
assert all(_np.array_equal(Xs[mine[k]], good[order[k]]) and int(need('y')[mine[k]]) == lab[order[k]] for k in range(len(good))), 'Картинки или метки не совпадают: метка — номер имени родительской папки в отсортированном списке classes.'
want = {n: lab.count(i) for i, n in enumerate(names)}
assert dict(need('counts', dict)) == want, f'counts = {need("counts")}, а нужно {want}.'
assert sorted(need('bad')) == sorted(badw), f'bad = {need("bad")}, а нужно {badw}: имена PNG-файлов, на которых Image.open упал.'
```

### hint
Соберите все файлы `root.rglob("*")`, оставьте те, у которых `p.is_file()` и `p.suffix.lower() == ".png"`, отсортируйте. Классы — `sorted({p.parent.name for p in paths})`.

### hint
Читайте в `try/except`: `img = np.array(Image.open(p).convert("L"))`; при ошибке добавьте `p.name` в `bad` и переходите к следующему файлу. Метку берите там же, где картинку, — только для удачно прочитанных.

### hint
```python
paths = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".png")
classes = sorted({p.parent.name for p in paths})
images, labels, bad = [], [], []
for p in paths:
    try:
        images.append(np.array(Image.open(p).convert("L")))
        labels.append(classes.index(p.parent.name))
    except Exception:
        bad.append(p.name)
X, y = ..., ...
counts = {c: ... for i, c in enumerate(classes)}
```

### solution
```python
from pathlib import Path
import numpy as np
from PIL import Image

root = Path("vitrina/train")
paths = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".png")
classes = sorted({p.parent.name for p in paths})

images, labels, bad = [], [], []
for p in paths:
    try:
        images.append(np.array(Image.open(p).convert("L")))
        labels.append(classes.index(p.parent.name))
    except Exception:
        bad.append(p.name)

X = np.stack(images)
y = np.array(labels)
counts = {c: int((y == i).sum()) for i, c in enumerate(classes)}
print(X.shape, classes, counts, bad)
```

### explain
Читаемых фото — 41: по 10 в каждой папке плюс `IMG_7.PNG` у круассанов, которую пропустил бы шаблон `rglob("*.png")` (на Linux регистр важен). `.DS_Store`, `Thumbs.db` и `readme.txt` отсеялись по расширению, а `битый.png` — по ошибке чтения: у него правильное начало файла, но дальше мусор. Без `try/except` загрузка остановилась бы на нём с `UnidentifiedImageError`, а без фильтра по расширению — на `Thumbs.db`. Типичная ошибка — добавлять метку до чтения картинки: тогда после битого файла метки «съедут» на одну позицию относительно картинок, и ошибки не будет, просто модель будет учиться на неверных ответах.
