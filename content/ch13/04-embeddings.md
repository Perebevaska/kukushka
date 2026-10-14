---
title: "Эмбеддинги: векторы слов и отзывов"
files: [reviews_text.csv]
lead: "Мешок слов не знает, что «латте» и «капучино» — почти одно и то же. Эмбеддинги превращают слово или целый отзыв в плотный вектор, где близкие по смыслу тексты оказываются рядом. Считаем косинусное сходство, строим простые эмбеддинги сами — LSA и идею word2vec, — ищем похожие отзывы и смотрим, где такой поиск ошибается."
recap:
  - "Эмбеддинг — плотный вектор фиксированной длины (сотни чисел) вместо разреженного вектора длиной в словарь."
  - "Близость векторов меряют косинусом: `a @ b / (|a| · |b|)`; 1 — одно направление, 0 — ничего общего."
  - "Вектор текста из векторов слов — среднее (mean pooling); после нормировки косинус — это просто скалярное произведение."
  - "LSA (`TruncatedSVD` поверх TF-IDF) — эмбеддинги «на коленке»: ловят совместную встречаемость, но не смысл (дороговато ≈ недорого)."
  - "word2vec учит векторы слов на учебной задаче «по слову угадай соседей» (пары в окне ±k + случайные отрицательные пары). Слова с одинаковым окружением получают близкие векторы — и антонимы тоже."
  - "Предобученные модели (например, `rubert-tiny2` через `transformers`) дают смысловые эмбеддинги; их кладут в обычный классификатор или поиск по сходству."
---

## Слово как точка

В TF-IDF у каждого слова свой столбец, и все слова одинаково далеки друг от друга: «латте» и «капучино» различаются так же, как «латте» и «курьер». **Эмбеддинг** (embedding, «вложение») — это вектор из нескольких сотен чисел, подобранный так, чтобы слова, встречающиеся в похожих контекстах, оказались рядом.

::: tip Аналогия
Эмбеддинг — как адрес слова на карте города: «латте» и «капучино» живут на одной улице, «курьер» и «опоздал» — в другом районе, и по расстоянию на карте видно, насколько слова похожи. Отличий от карты два: у настоящей карты две подписанные оси, а у эмбеддинга — сотни безымянных; и соседями становятся слова из похожих контекстов, а не обязательно близкие по смыслу, — поэтому рядом могут оказаться даже антонимы.
:::

::: figure bow-vs-emb
Слева — мешок слов: у каждого слова свой столбец, и любые два разных слова «перпендикулярны» (косинус 0). Справа — игрушечные эмбеддинги урока: «латте» и «капучино» смотрят почти в одну сторону, «курьер» — в другую.
:::

Возьмём игрушечные эмбеддинги из четырёх чисел. Пусть оси значат «напитки», «доставка», «деньги», «удовольствие» — в настоящих моделях оси не подписаны, но принцип тот же.

```python
import numpy as np

vec = {
    "кофе":     np.array([0.9, 0.0, 0.1, 0.3]),
    "латте":    np.array([0.8, 0.0, 0.1, 0.5]),
    "капучино": np.array([0.8, 0.1, 0.0, 0.4]),
    "курьер":   np.array([0.0, 0.9, 0.1, 0.0]),
    "опоздал":  np.array([0.0, 0.7, 0.0, -0.6]),
    "дорого":   np.array([0.1, 0.0, 0.9, -0.4]),
    "вкусно":   np.array([0.4, 0.0, 0.0, 0.9]),
}

def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

for w in ["латте", "капучино", "курьер", "дорого"]:
    print(f"кофе ~ {w}: {cosine(vec['кофе'], vec[w]):.2f}")
```

Посчитаем одно сходство руками — «кофе» и «латте»:

- скалярное произведение: 0.9·0.8 + 0·0 + 0.1·0.1 + 0.3·0.5 = 0.72 + 0 + 0.01 + 0.15 = **0.88**;
- длины: |кофе| = √(0.81 + 0 + 0.01 + 0.09) ≈ 0.954, |латте| = √(0.64 + 0 + 0.01 + 0.25) ≈ 0.949;
- косинус: 0.88 / (0.954 · 0.949) ≈ **0.97**.

**Что здесь происходит в коде:**

- `vec` — словарь «слово → вектор из 4 чисел».
- `a @ b` — скалярное произведение (сумма попарных произведений), `np.linalg.norm(a)` — длина вектора.
- Цикл печатает сходство «кофе» с четырьмя словами.

**Косинусное сходство** — косинус угла между векторами. Длина вектора на него не влияет, важно только направление: 1 — смотрят в одну сторону, 0 — перпендикулярны (ничего общего), −1 — противоположны.

::: predict
```python static
import numpy as np
kur = np.array([0.0, 0.9, 0.1, 0.0])
late = np.array([0.0, 0.7, 0.0, -0.6])
tasty = np.array([0.4, 0.0, 0.0, 0.9])
cos = lambda a, b: a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
print(round(cos(kur, late), 2) > 0, round(cos(tasty, late), 2) > 0)
```

- `True True`
- [x] `True False`
- `False False`

Почему: «курьер» и «опоздал» — оба про доставку, косинус около 0.75. У «вкусно» и «опоздал» ось удовольствия разных знаков, и это перевешивает: около −0.6.
:::

::: figure embeddings
Схема в двух измерениях: слова, которые встречаются в похожих контекстах, оказываются рядом. Близость измеряют косинусом.
:::

{{practice: cos, nearest}}

## Вектор целого отзыва

Простейший способ получить вектор фразы — усреднить векторы её слов (**mean pooling**). Для сравнения векторы нормируют на длину 1 — тогда косинус превращается в обычное скалярное произведение, и сходство одного запроса со всеми текстами считается одним умножением матрицы на вектор.

```python
import numpy as np

vec = {
    "кофе": np.array([0.9, 0.0, 0.1, 0.3]), "латте": np.array([0.8, 0.0, 0.1, 0.5]),
    "капучино": np.array([0.8, 0.1, 0.0, 0.4]), "курьер": np.array([0.0, 0.9, 0.1, 0.0]),
    "опоздал": np.array([0.0, 0.7, 0.0, -0.6]), "дорого": np.array([0.1, 0.0, 0.9, -0.4]),
    "вкусно": np.array([0.4, 0.0, 0.0, 0.9]),
}

def embed(text):
    words = [w for w in text.lower().split() if w in vec]
    v = np.mean([vec[w] for w in words], axis=0)
    return v / np.linalg.norm(v)

docs = ["латте вкусно", "курьер опоздал", "кофе дорого"]
E = np.array([embed(d) for d in docs])     # матрица 3 × 4
q = embed("капучино вкусно")
print((E @ q).round(2))                     # сходство запроса с каждым текстом
```

**Что здесь происходит:**

- `embed(text)` — делит текст на слова, берёт векторы известных слов, усредняет (`np.mean(..., axis=0)` — среднее по словам для каждой из 4 координат) и нормирует на длину 1.
- `E` — матрица: строка на каждый текст, 4 столбца.
- `E @ q` — умножение матрицы на вектор: скалярное произведение запроса с каждой строкой сразу. Так как все векторы длины 1, это и есть косинусы.

::: figure mean-pool-search
Пример выше по шагам: векторы слов запроса усредняются и нормируются, получается `q`; строки матрицы `E` — так же полученные векторы текстов; `E @ q` — три сходства сразу.
:::

Запрос «капучино вкусно» ближе всего к «латте вкусно», хотя общих слов у них — одно. В мешке слов «капучино» и «латте» не совпали бы вовсе.

::: note
Усреднение теряет порядок слов: «не вкусно, но быстро» и «быстро, но не вкусно» получат один вектор. Современные модели строят вектор текста целиком (трансформер учитывает порядок и контекст), а усреднение делают уже над векторами, которые знают своё окружение.
:::

{{practice: p-pool, char-search}}

## Эмбеддинги на коленке: LSA

Настоящие эмбеддинги учатся на миллиардах слов. Но похожую идею можно получить из наших отзывов: сжать разреженную матрицу TF-IDF до 50 столбцов **усечённым SVD** (`TruncatedSVD`). Метод называется **LSA** (латентно-семантический анализ).

Как понимать эти 50 новых столбцов без линейной алгебры: каждый из них — «тема-смесь» слов с весами. Например, у одной из 50 смесей на наших отзывах самые большие веса у слов «через», «приложение», «заказывала», «доставили» — это смесь про заказ доставки. Смеси подобраны так, чтобы по 50 числам отзыва можно было почти восстановить его исходную строку из 485 столбцов. Слова, которые часто встречаются вместе, попадают в одни и те же смеси, — поэтому отзывы с похожим набором слов получают похожие векторы.

```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
tfidf = TfidfVectorizer()
X = tfidf.fit_transform(r["text"])                 # 2400 × 485, почти все нули
svd = TruncatedSVD(n_components=50, random_state=0)
Z = svd.fit_transform(X)                            # 2400 × 50, плотная
print(X.shape, "→", Z.shape, "| сохранено дисперсии:", round(svd.explained_variance_ratio_.sum(), 2))

Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)  # нормируем — косинус = скалярное произведение
sim = Zn @ Zn[0]
top = np.argsort(-sim)[1:4]                         # [0] — сам отзыв
print("запрос:", r.loc[0, "text"])
for i in top:
    print(f"{sim[i]:.2f}", r.loc[i, "text"])
```

**Что здесь происходит:**

::: figure lsa-shapes
Формы матриц в LSA: разреженная TF-IDF 2400 × 485 раскладывается на плотную 2400 × 50 (векторы отзывов) и `components_` 50 × 485, из которой получаются векторы слов. 50 компонент сохраняют около 71 % разброса.
:::

- `TruncatedSVD(n_components=50)` — подбирает 50 смесей слов, которые лучше всего описывают таблицу TF-IDF, и переводит каждый отзыв в 50 чисел — насколько в нём выражена каждая смесь. «Усечённое» — потому что оставляем только 50 самых важных смесей из возможных 485. Работает прямо с разреженной матрицей.
- `explained_variance_ratio_.sum()` — какую долю разброса исходных данных сохранили 50 компонент (около 70 %).
- `Zn = Z / norm` — нормировка строк на длину 1, чтобы скалярное произведение было косинусом.
- `Zn @ Zn[0]` — сходство первого отзыва со всеми 2400; `np.argsort(-sim)` — номера по убыванию сходства, `[1:4]` — пропускаем сам отзыв (он на первом месте со сходством 1).

Ближайшие соседи — отзывы, которые начинаются с той же фразы. LSA ловит общие слова и слова, которые часто стоят рядом, но не смысл. Видно это на соседях отдельных слов (строки `svd.components_` — векторы слов):

```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
tfidf = TfidfVectorizer()
svd = TruncatedSVD(n_components=50, random_state=0).fit(tfidf.fit_transform(r["text"]))
W = svd.components_.T * svd.singular_values_        # вектор каждого слова
W = W / np.linalg.norm(W, axis=1, keepdims=True)
words = tfidf.get_feature_names_out()
pos = {w: i for i, w in enumerate(words)}

for w in ["дороговато", "курьер"]:
    s = W @ W[pos[w]]
    near = np.argsort(-s)[1:5]
    print(w, "→", [words[i] for i in near])
```

**Что здесь происходит:**

- `svd.components_` — матрица 50 × 485: каждая строка — одна смесь, то есть веса слов в ней. Транспонированная (`.T`) — 485 × 50: у каждого слова 50 чисел — с каким весом оно входит в каждую смесь. Это и есть вектор слова.
- `* svd.singular_values_` — вес каждой смеси: первые смеси описывают таблицу сильнее, и их координаты умножаются на большее число. На соседей слов это влияет слабо, можно и без умножения.
- `pos` — словарь «слово → номер строки», чтобы найти вектор нужного слова.

::: warn
Рядом с «дороговато» оказывается «недорого»: антонимы встречаются в одинаковых контекстах («… для такого качества»). LSA, как и любые эмбеддинги, обученные на совместной встречаемости, путает «похоже по теме» и «похоже по смыслу». Для тональности это опасно — поэтому эмбеддинги почти всегда используют как признаки для обученного классификатора, а не сами по себе.
:::

::: quiz
Почему в LSA рядом с «дороговато» оказалось «недорого»?

- [x] Антонимы встречаются в одинаковых контекстах, а LSA учится на совместной встречаемости слов — она ловит «похоже по теме», а не «похоже по смыслу»
  > Отсюда правило: эмбеддинги используют как признаки для обученного классификатора, а не судят по ним о тональности напрямую.
- [ ] 50 компонент слишком мало — с большим числом компонент слова разошлись бы
  > Число компонент меняет детали, но не причину: метод по-прежнему видит только, какие слова стоят рядом, а у антонимов окружение одинаковое.
- [ ] Ошибка нормировки: без деления на длину слова оказались бы далеко
  > Нормировка меняет длину вектора, а не направление, — косинусное сходство от неё не зависит.
- [ ] Это формы одного слова, и LSA правильно их объединила
  > «Дороговато» и «недорого» — разные слова с противоположным смыслом, а не формы одного слова.
:::

{{practice: lsa, lsa-clf, zero-shot}}

## Откуда берутся векторы слов: идея word2vec

LSA получает векторы из таблицы счётчиков одним разложением. **word2vec** (2013) делает иначе: придумывает себе учебную задачу и решает её миллионы раз — «по слову угадай его соседей». Векторы слов — побочный продукт: чтобы угадывать соседей, у слов с похожим окружением должны получиться похожие векторы.

::: tip Аналогия
«Скажи мне, кто твой друг, и я скажу, кто ты». О незнакомом слове «флэт» вы догадаетесь по соседям: «заказал флэт», «флэт был холодный», «флэт с собой» — это напиток. word2vec поступает так же, только для каждого слова и по всему корпусу сразу. Подводит этот принцип там же, где LSA: «друзья» у «дороговато» и «недорого» одни и те же — и word2vec сочтёт их похожими.
:::

**Шаг 1 — пары «слово → сосед».** Идём по тексту, каждое слово по очереди — центральное, соседи в окне ±k слов — контекст. Для фразы «курьер привёз холодный кофе» и окна 1:

| центральное | соседи | пары |
|---|---|---|
| курьер | привёз | (курьер, привёз) |
| привёз | курьер, холодный | (привёз, курьер), (привёз, холодный) |
| холодный | привёз, кофе | (холодный, привёз), (холодный, кофе) |
| кофе | холодный | (кофе, холодный) |

::: figure skipgram-window
Окно ±1 идёт по фразе «курьер привёз холодный кофе»: на каждом шаге центральное слово (синее) образует пары со своими соседями (зелёные). Всего 6 настоящих пар; случайная пара вроде «курьер — чизкейк» — отрицательный пример.
:::

**Шаг 2 — учебная задача.** У каждого слова два вектора: «как центральное» $v$ и «как сосед» $u$. Для настоящей пары скалярное произведение $v \cdot u$ должно быть большим, для случайной пары («курьер», «чизкейк» — их выбирают наугад, это **отрицательные примеры**) — маленьким. Обучение идёт маленькими шагами: на каждой паре векторы чуть-чуть сдвигаются в ту сторону, где ошибка угадывания меньше, — и так, пока модель не начнёт отличать настоящие пары от случайных. Слова, у которых одни и те же соседи, тянутся к одним и тем же $u$ — и их векторы $v$ сближаются.

Шаг 1 легко сделать на наших отзывах и посмотреть, какое окружение увидит модель:

```python
import re
from collections import Counter
import pandas as pd

def skipgram_pairs(tokens, window=2):
    pairs = []
    for i, center in enumerate(tokens):
        for j in range(max(0, i - window), min(len(tokens), i + window + 1)):
            if j != i:
                pairs.append((center, tokens[j]))
    return pairs

print(skipgram_pairs("курьер привёз холодный кофе".split(), window=1))

r = pd.read_csv("reviews_text.csv")
pairs = [p for t in r["text"] for p in skipgram_pairs(re.findall(r"[а-яё]+", t.lower()))]
print("пар:", len(pairs))
for w in ["курьер", "дороговато", "недорого"]:
    print(w, Counter(c for x, c in pairs if x == w).most_common(4))
```

**Что здесь происходит:**

- `range(max(0, i - window), min(len(tokens), i + window + 1))` — номера слов в окне вокруг `i`, обрезанные по краям текста; `j != i` — само слово себе не сосед.
- `pairs` — все пары по всем отзывам: это и есть обучающие примеры word2vec.
- `Counter(...).most_common(4)` — самые частые соседи слова.

**Что получилось:** около 63 тысяч пар. У «курьера» соседи «раньше», «приехал», «вежливый» — модель свяжет его с доставкой. А у «дороговато» и «недорого» самые частые соседи одни и те же — «для» и «такого». word2vec, как и LSA, сделает их векторы близкими: антонимы живут в одинаковом окружении.

На своём компьютере word2vec обучают библиотекой `gensim` (в браузере её нет):

```python static
# uv add gensim
import re
import pandas as pd
from gensim.models import Word2Vec

r = pd.read_csv("reviews_text.csv")
sentences = [re.findall(r"[а-яё]+", t.lower()) for t in r["text"]]
w2v = Word2Vec(sentences, vector_size=50, window=2, min_count=5,
               sg=1, negative=5, epochs=30, seed=42, workers=1)
print(w2v.wv["латте"].shape)                  # (50,) — вектор слова
print(w2v.wv.most_similar("латте", topn=5))   # ближайшие по косинусу
```

- `sg=1` — вариант skip-gram (по слову угадать соседей), `window=2` — окно, `negative=5` — пять случайных «не-соседей» на каждую настоящую пару.
- `min_count=5` — редкие слова (опечатки) выкидываются: по трём упоминаниям хороший вектор не выучить.
- `workers=1` и `seed` — для воспроизводимости: в несколько потоков результат от запуска к запуску немного разный.

На 2400 коротких шаблонных отзывах word2vec учится плохо — ему нужны миллионы предложений. Поэтому на практике берут **готовые** векторы, обученные на большом корпусе (для русского — модели RusVectōrēs, fastText), или сразу эмбеддинги предложений из следующего раздела.

::: warn Типичные ошибки
- **Ждать от word2vec смысла.** Он ловит окружение: «дороговато» ≈ «недорого», «горячий» ≈ «холодный» — у антонимов одни и те же соседи. Для тональности векторы слов — признаки для классификатора, а не готовый ответ.
- **Слово не из словаря.** `w2v.wv["флэтуайт"]` падает с `KeyError`: слова, которого не было при обучении (или реже `min_count`), у модели нет. Проверяйте `"слово" in w2v.wv` или берите fastText — он собирает вектор из кусочков слова.
- **Обучать на сырых формах.** Для русского «курьер», «курьера», «курьером» — три разных слова с тремя слабыми векторами. Лемматизация (урок «Леммы и словарь исключений») перед word2vec заметно помогает на небольших корпусах.
:::

{{practice: skipgram}}

## Предобученные эмбеддинги

На практике векторы берут у готовой модели, обученной на огромном корпусе текстов. Возьмём `cointegrated/rubert-tiny2` — маленькую русскую модель (около 120 МБ), которая превращает отзыв в вектор из 312 чисел с учётом порядка слов и контекста. Ей нужен PyTorch, а в браузерном Python его нет, поэтому код ниже — для вашего компьютера. Как модель устроена внутри (токены, маска, пулинг), разберём в следующем уроке «Внутри трансформера: токены, маска, пулинг»; здесь она — чёрный ящик «текст → вектор».

```python static
# uv add transformers torch
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

name = "cointegrated/rubert-tiny2"                 # скачается при первом запуске
tok = AutoTokenizer.from_pretrained(name)
model = AutoModel.from_pretrained(name).eval()

def embed(texts):
    """Вектор каждого текста: среднее векторов его токенов, длина 1."""
    enc = tok(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
    with torch.no_grad():
        H = model(**enc).last_hidden_state
    m = enc["attention_mask"].unsqueeze(-1)
    E = ((H * m).sum(1) / m.sum(1)).numpy()
    return E / np.linalg.norm(E, axis=1, keepdims=True)

texts = r["text"].tolist()
E = np.vstack([embed(texts[i:i + 32]) for i in range(0, len(texts), 32)])   # 2400 × 312

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
f1_emb = cross_val_score(LogisticRegression(max_iter=2000), E, y, cv=cv, scoring="f1")
tfidf = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))
f1_tfidf = cross_val_score(tfidf, r["text"], y, cv=cv, scoring="f1")
print(f"эмбеддинги: F1 = {f1_emb.mean():.3f} ± {f1_emb.std():.3f}")
print(f"TF-IDF:     F1 = {f1_tfidf.mean():.3f} ± {f1_tfidf.std():.3f}")

# поиск по смыслу: запрос не обязан совпадать словами с отзывами
q = embed(["долго везли заказ"])[0]
print(r.loc[(E @ q).argsort()[::-1][:5], "text"].tolist())
```

**Что здесь происходит:**

- `AutoTokenizer` и `AutoModel` с одним и тем же именем — токенизатор и модель всегда берут парой.
- `embed` — тексты пакетом по 32 превращаются в векторы длины 1. Строки внутри функции разберём в уроке «Внутри трансформера: токены, маска, пулинг».
- Дальше обычная логистическая регрессия: вместо TF-IDF-матрицы на вход идёт матрица эмбеддингов `E`. Обе модели сравниваются на одних и тех же пяти фолдах.
- Поиск по смыслу: вектор запроса `q`, сходство `E @ q`, пять самых похожих отзывов.

**Что получилось** (замер на ноутбуке с torch 2.14 и transformers 5.17). Векторы модели детерминированы: она в режиме `eval()` и не обучается, а фолды заданы `random_state=42`, поэтому у вас должно выйти то же с точностью до третьего знака. TF-IDF-часть замера можно проверить и в браузере — это обычный sklearn:

```text
эмбеддинги: F1 = 0.930 ± 0.016
TF-IDF:     F1 = 0.940 ± 0.015
['Брали с собой. Перепутали заказ.', 'Были сегодня. Перепутали заказ.', 'Были сегодня. Перепутали заказ.', 'Заказывала через приложение. Кофе привезли горячим, но сырник пересушены.', 'Хожу сюда давно. Долго не могли принять оплату, заказ привезли не тот.']
```

На наших отзывах готовая модель не выиграла: TF-IDF со словами и биграммами чуть лучше, а разница меньше разброса по фолдам. Причина — отзывы «Зерна» короткие и шаблонные, и TF-IDF уже почти упёрся в шум разметки: в уроке «Классификация текстов» уверенных ошибок, где гость промахнулся звёздочкой, около 5 % теста (28 из 600).

От эмбеддингов ждут другого — силы на синонимах и перефразах, где TF-IDF бессилен: «долго везли» и «курьер опоздал» не имеют общих слов. Последняя строка кода это проверяет, и проверка честно не проходит. Все пять ближайших к запросу «долго везли заказ» отзывов содержат «заказ» или «привезли», но говорят о другом: перепутали заказ, кофе привезли горячим. Первый отзыв про опоздавшую доставку стоит только на 74-м месте (сходство 0.651 против 0.731 у первого). Маленькая модель на коротком запросе держится за общие слова почти так же, как TF-IDF. На запросе «курьер опоздал» выдача хорошая — пять отзывов «Доставка опоздала на час», хотя слова «курьер» в них нет. А на «не дорого» модель находит «Слишком дорого»: отрицание она почти не замечает.

Вывод: поиск по смыслу на готовых эмбеддингах — не магия. Его проверяют на десятке своих типичных запросов, прежде чем отдавать операторам. Большие модели эмбеддингов и длинные живые тексты с жаргоном дают заметный выигрыш чаще, а на таких отзывах, как наши, простой TF-IDF остаётся честным выбором.

Матрица `E` — обычные числовые признаки: с ней работают логистическая регрессия, кластеризация (`KMeans` по тем же векторам) и поиск ближайших. Тот же расчёт с кэшем векторов и проверкой маски — в локальном блокноте [ch13-transformers.ipynb](../notebooks/extra/ch13-transformers.ipynb); поиск по смыслу на пяти запросах (в том числе «долго везли заказ» и «не дорого») — там же, в разделе 5; сравните его выдачу с поиском на LSA из раздела «Разберём вместе» ниже.

::: tip
Эмбеддинги удобно считать один раз и сохранять (`np.save("emb.npy", E)`): кодирование — самая медленная часть, а модели поверх них обучаются за секунды.
:::

В браузере этот раздел не запускается, поэтому задач к нему нет — попробуйте код в блокноте.

## Разберём вместе: поиск похожих отзывов как сервис

Частая задача: оператор видит жалобу и хочет найти похожие — вдруг это массовая проблема. Соберём простой поиск на LSA-векторах: запрос — текст, ответ — пять самых похожих отзывов со сходством.

**План:**

1. Обучить TF-IDF и SVD на всех отзывах, получить нормированные векторы `Zn`.
2. Запрос пропустить через **те же** `tfidf.transform` и `svd.transform` (не `fit`!) и нормировать.
3. Сходство — `Zn @ q`, вывести топ-5.

```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
tfidf = TfidfVectorizer()
svd = TruncatedSVD(n_components=100, random_state=0)
Z = svd.fit_transform(tfidf.fit_transform(r["text"]))
Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)

def search(query, k=5):
    q = svd.transform(tfidf.transform([query]))[0]
    q = q / np.linalg.norm(q)
    sim = Zn @ q
    top = np.argsort(-sim)[:k]
    return pd.DataFrame({"сходство": sim[top].round(2), "отзыв": r.loc[top, "text"].values})

print(search("курьер опоздал"))
print(search("кофе остыл пока везли"))
```

**Что получилось:** результат поучительный — и плохой. На «курьер опоздал» поиск выдаёт «Курьер вежливый»: слова «опоздал» в словаре нет (в отзывах пишут «доставка опоздала»), и от запроса осталось одно слово «курьер». На «кофе остыл пока везли» первым идёт «Кофе привезли горячим» — противоположный смысл: «остыл» тоже незнаком, а «кофе» и «привезли» совпали. Поиск по словам и их совместной встречаемости не понимает ни форм слов, ни отрицаний, ни антонимов.

Как это лечат: формы слов — лемматизацией или символьными n-граммами (уроки «Леммы и словарь исключений» и «Мешок слов и TF-IDF», задача «Поиск по кусочкам слов» выше); смысл — предобученными эмбеддингами (раздел «Предобученные эмбеддинги» выше): они обучены на огромном корпусе и могут связать «курьер опоздал» с «доставка опоздала», но на «долго везли заказ» маленькая модель уже промахивается (см. выше), поэтому насколько хорошо они работают, проверяют на своих запросах (раздел 5 блокнота). И в любом случае результаты поиска проверяют глазами на десятке типичных запросов, прежде чем отдавать операторам.

## Практика

## task: cos | Косинусное сходство | warmup

Напишите функцию `cosine(a, b)` и посчитайте `s_latte` — сходство «кофе» и «латте» и `s_late` — сходство «курьер» и «опоздал» (оба — числа, без округления). Словарь `vec` уже загружен.

### setup
```python
import numpy as np
vec = {
    "кофе": np.array([0.9, 0.0, 0.1, 0.3]), "латте": np.array([0.8, 0.0, 0.1, 0.5]),
    "капучино": np.array([0.8, 0.1, 0.0, 0.4]), "курьер": np.array([0.0, 0.9, 0.1, 0.0]),
    "опоздал": np.array([0.0, 0.7, 0.0, -0.6]), "дорого": np.array([0.1, 0.0, 0.9, -0.4]),
    "вкусно": np.array([0.4, 0.0, 0.0, 0.9]),
}
```

### starter
```python
import numpy as np

def cosine(a, b):
    ...

s_latte = ...
s_late = ...
```

### check
```python
import numpy as _np
_c = lambda a, b: float(a @ b / (_np.linalg.norm(a) * _np.linalg.norm(b)))
f = need('cosine')
assert close(float(f(_np.array([1.0, 0]), _np.array([0, 2.0]))), 0, 1e-9), 'Перпендикулярные векторы должны давать 0.'
assert close(float(f(_np.array([1.0, 1]), _np.array([3.0, 3]))), 1, 1e-9), 'Векторы одного направления (разной длины) должны давать 1.'
v = need('vec', dict)
assert close(need('s_latte'), _c(v['кофе'], v['латте']), 1e-6), f's_latte = {need("s_latte")}.'
assert close(need('s_late'), _c(v['курьер'], v['опоздал']), 1e-6), f's_late = {need("s_late")}.'
```

### hint
Формула: косинус = скалярное произведение / (длина a × длина b).

### hint
`a @ b` — скалярное произведение, `np.linalg.norm(a)` — длина вектора.

### solution
```python
import numpy as np

def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

s_latte = cosine(vec["кофе"], vec["латте"])
s_late = cosine(vec["курьер"], vec["опоздал"])
```

## task: p-pool | Вектор фразы | warmup

Соберите вектор фразы «капучино вкусно» усреднением и нормировкой и напечатайте его сходство с вектором «латте» (2 знака).

### parsons
```python
import numpy as np
vec = {"латте": np.array([0.8, 0.0, 0.1, 0.5]), "капучино": np.array([0.8, 0.1, 0.0, 0.4]), "вкусно": np.array([0.4, 0.0, 0.0, 0.9])}
words = "капучино вкусно".split()
v = np.mean([vec[w] for w in words], axis=0)
v = v / np.linalg.norm(v)
latte = vec["латте"] / np.linalg.norm(vec["латте"])
print(round(float(v @ latte), 2))
```

### check
```python
import numpy as _np
a = _np.mean([_np.array([0.8, 0.1, 0.0, 0.4]), _np.array([0.4, 0.0, 0.0, 0.9])], axis=0)
b = _np.array([0.8, 0.0, 0.1, 0.5])
w = round(float(a @ b / _np.linalg.norm(a) / _np.linalg.norm(b)), 2)
assert _lines == [str(w)], f'Сейчас: {_lines}.'
```

### hint
Словарь → слова → среднее → нормировка → сходство.

### hint
`np.mean([...], axis=0)` усредняет векторы поэлементно — по каждой из 4 координат.

## task: nearest | Ближайшие слова | base

Для каждого слова из `vec`, кроме самого «кофе», посчитайте косинус с «кофе». Сохраните `sims` — Series (индекс — слова, значения — сходство), отсортированную по убыванию, и `top3` — список трёх ближайших слов.

### setup
```python
import numpy as np
vec = {
    "кофе": np.array([0.9, 0.0, 0.1, 0.3]), "латте": np.array([0.8, 0.0, 0.1, 0.5]),
    "капучино": np.array([0.8, 0.1, 0.0, 0.4]), "курьер": np.array([0.0, 0.9, 0.1, 0.0]),
    "опоздал": np.array([0.0, 0.7, 0.0, -0.6]), "дорого": np.array([0.1, 0.0, 0.9, -0.4]),
    "вкусно": np.array([0.4, 0.0, 0.0, 0.9]),
}
```

### starter
```python
import numpy as np
import pandas as pd

```

### check
```python
import numpy as _np
import pandas as _pd
v = need('vec', dict)
_c = lambda a, b: float(a @ b / (_np.linalg.norm(a) * _np.linalg.norm(b)))
w = _pd.Series({k: _c(v['кофе'], x) for k, x in v.items() if k != 'кофе'}).sort_values(ascending=False)
s = need('sims', _pd.Series)
assert 'кофе' not in s.index, 'Само слово «кофе» в sims не нужно.'
assert list(s.index) == list(w.index), f'Порядок: {list(s.index)}, а нужно {list(w.index)}.'
assert _np.allclose(s.values, w.values, atol=1e-6), 'Значения сходства не совпадают.'
assert need('top3', list) == list(w.index[:3]), f'top3 = {need("top3")}.'
```

### hint
Сначала функция `cosine`, как в первой задаче; потом сходство «кофе» с каждым другим словом словаря `vec`.

### hint
Словарь `{слово: cosine(...)}` → `pd.Series(...)` → `.sort_values(ascending=False)`; `top3 = list(sims.index[:3])`.

### solution
```python
import numpy as np
import pandas as pd

def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

sims = pd.Series({w: cosine(vec["кофе"], v) for w, v in vec.items() if w != "кофе"}).sort_values(ascending=False)
top3 = list(sims.index[:3])
```

### explain
Ближе всех «латте» и «капучино», дальше всех — «опоздал». Это и есть то, чего не умеет мешок слов: у разных слов появляется мера похожести.

## task: lsa | Похожие отзывы | base

Постройте LSA-эмбеддинги отзывов: `TfidfVectorizer()` на всех текстах, затем `TruncatedSVD(n_components=50, random_state=0)`. Нормируйте строки на длину 1. Сохраните `explained` — долю сохранённой дисперсии (2 знака), `Zn` — нормированную матрицу и `neighbours` — список `review_id` трёх отзывов, ближайших к отзыву `R-40002` (сам отзыв не включайте).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.decomposition import TruncatedSVD as _SVD
r0 = _pd.read_csv('reviews_text.csv')
s0 = _SVD(n_components=50, random_state=0)
Z0 = s0.fit_transform(_TF().fit_transform(r0['text']))
Z0 = Z0 / _np.linalg.norm(Z0, axis=1, keepdims=True)
i0 = int(_np.flatnonzero(r0['review_id'] == 'R-40002')[0])
sim = Z0 @ Z0[i0]
order = [i for i in _np.argsort(-sim) if i != i0][:3]
assert close(need('explained'), round(float(s0.explained_variance_ratio_.sum()), 2), 0.011), f'explained = {need("explained")}.'
Zs = need('Zn')
assert Zs.shape == (2400, 50), f'Zn.shape = {Zs.shape}.'
assert _np.allclose(_np.linalg.norm(Zs, axis=1), 1, atol=1e-6), 'Строки Zn должны иметь длину 1.'
got = need('neighbours', list)
want = list(r0.loc[order, 'review_id'])
assert len(got) == 3 and 'R-40002' not in got, f'neighbours = {got}.'
assert set(got) == set(want), f'neighbours = {got}, а нужно {want}.'
```

### hint
Номер отзыва `R-40002` в таблице: `i = r.index[r["review_id"] == "R-40002"][0]`.

### hint
`Zn @ Zn[i]` — сходство всех отзывов с i-м. `np.argsort(-sim)` упорядочит по убыванию; первым будет сам отзыв.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
svd = TruncatedSVD(n_components=50, random_state=0)
Z = svd.fit_transform(TfidfVectorizer().fit_transform(r["text"]))
explained = round(svd.explained_variance_ratio_.sum(), 2)
Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)

i = r.index[r["review_id"] == "R-40002"][0]
sim = Zn @ Zn[i]
order = [j for j in np.argsort(-sim) if j != i][:3]
neighbours = list(r.loc[order, "review_id"])
print(r.loc[i, "text"])
print(r.loc[order, "text"].tolist())
```

### explain
Соседи снова делят с запросом целые фразы. Для поиска дублей и шаблонных отзывов этого хватает, для поиска по смыслу нужны предобученные эмбеддинги.

## task: char-search | Поиск по кусочкам слов | base

Сравните два поисковика по отзывам: на словном TF-IDF (`TfidfVectorizer()`) и на символьном (`TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))`), оба обучены на всех отзывах. Сходство запроса со всеми отзывами — `(T @ vec.transform([q]).T).toarray().ravel()` (строки TF-IDF уже нормированы). Напишите `search(vec, T, q, k=5)` — список текстов `k` самых похожих отзывов (порядок по убыванию сходства, `np.argsort(-sim, kind="stable")`). Для запроса `"курьер опоздал"` сохраните `top_words` и `top_chars`, а также `share_late_words` и `share_late_chars` — долю отзывов в каждом топ-5, где встречается подстрока `"опоздал"` (без учёта регистра).

### setup
```python
import pandas as pd
r = pd.read_csv("reviews_text.csv")
```

### starter
```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

w_vec = TfidfVectorizer()
W = w_vec.fit_transform(r["text"])
c_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))
C = c_vec.fit_transform(r["text"])

def search(vec, T, q, k=5):
    ...

```

### check
```python
import numpy as _np
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
r0 = need('r')
def _s(vec, q, k=5):
    T = vec.transform(r0['text']); sim = (T @ vec.transform([q]).T).toarray().ravel()
    return list(r0['text'].values[_np.argsort(-sim, kind='stable')[:k]])
ww = _s(_TF().fit(r0['text']), 'курьер опоздал'); wc = _s(_TF(analyzer='char_wb', ngram_range=(3, 4)).fit(r0['text']), 'курьер опоздал')
assert list(need('top_words')) == ww, f'top_words не совпадает: {need("top_words")}.'
assert list(need('top_chars')) == wc, f'top_chars не совпадает: {need("top_chars")}.'
sw = sum('опоздал' in t.lower() for t in ww) / 5; sc = sum('опоздал' in t.lower() for t in wc) / 5
assert close(need('share_late_words'), sw) and close(need('share_late_chars'), sc), f'share_late_words = {need("share_late_words")}, share_late_chars = {need("share_late_chars")}.'
```

### hint
Сходство: `sim = (T @ vec.transform([q]).T).toarray().ravel()` — массив длины 2400. Номера лучших — `np.argsort(-sim, kind="stable")[:k]`.

### hint
Тексты по номерам: `list(r["text"].values[idx])`.

### hint
Доля с «опоздал»: `sum("опоздал" in t.lower() for t in top) / 5`.

### solution
```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

w_vec = TfidfVectorizer()
W = w_vec.fit_transform(r["text"])
c_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))
C = c_vec.fit_transform(r["text"])

def search(vec, T, q, k=5):
    sim = (T @ vec.transform([q]).T).toarray().ravel()
    idx = np.argsort(-sim, kind="stable")[:k]
    return list(r["text"].values[idx])

top_words = search(w_vec, W, "курьер опоздал")
top_chars = search(c_vec, C, "курьер опоздал")
share_late_words = sum("опоздал" in t.lower() for t in top_words) / 5
share_late_chars = sum("опоздал" in t.lower() for t in top_chars) / 5
print(top_words, top_chars, share_late_words, share_late_chars, sep="\n")
```

### explain
Словный поиск не знает слова «опоздал» (в отзывах только «опоздала»), и в выдаче — «Курьер вежливый». Символьный находит общие кусочки «опо», «поз», «озд», «здал» и выдаёт «Доставка опоздала на час» — все пять результатов про опоздание. Формы слов и опечатки символьные n-граммы лечат хорошо. Но смысл — нет: попробуйте сами запрос «кофе остыл пока везли» — символьный поиск выдаст «Кофе привезли горячим». Для этого нужны эмбеддинги, обученные на большом корпусе.

## task: lsa-clf | Сколько измерений нужно | plus

Обучите на тональности (`rating <= 3`, разбиение как в уроке «Классификация текстов») конвейеры `TfidfVectorizer() → TruncatedSVD(k, random_state=0) → LogisticRegression(max_iter=1000)` для `k` из `[10, 20, 50, 100]`. Сохраните `acc_by_k` — словарь `{k: доля правильных на тесте}` (3 знака), `acc_full` — то же для конвейера без SVD и `best_k` — `k` с наибольшей долей (при равенстве — меньшее).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.decomposition import TruncatedSVD as _SVD
from sklearn.linear_model import LogisticRegression as _LR
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
w = {k: round(float((_mp(_TF(), _SVD(k, random_state=0), _LR(max_iter=1000)).fit(a, c).predict(b) == d).mean()), 3) for k in [10, 20, 50, 100]}
full = round(float((_mp(_TF(), _LR(max_iter=1000)).fit(a, c).predict(b) == d).mean()), 3)
got = need('acc_by_k', dict)
assert sorted(got) == [10, 20, 50, 100], f'Ключи: {sorted(got)}.'
assert all(close(got[k], w[k], 0.002) for k in w), f'acc_by_k = {got}, а нужно {w}.'
assert close(need('acc_full'), full, 0.002), f'acc_full = {need("acc_full")}.'
bk = max(sorted(w), key=lambda k: w[k])
assert need('best_k') == bk, f'best_k = {need("best_k")}, а нужно {bk}.'
```

### hint
SVD встаёт в конвейер между векторайзером и моделью: `make_pipeline(TfidfVectorizer(), TruncatedSVD(k, random_state=0), LogisticRegression(max_iter=1000))`.

### hint
Цикл по `k`, внутри — `make_pipeline(...)`, `.fit(X_train, y_train)`, `accuracy_score(y_test, model.predict(X_test))`. `max(sorted(acc), key=acc.get)` при равенстве вернёт меньший ключ.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

acc_by_k = {}
for k in [10, 20, 50, 100]:
    m = make_pipeline(TfidfVectorizer(), TruncatedSVD(k, random_state=0), LogisticRegression(max_iter=1000))
    acc_by_k[k] = round(accuracy_score(y_test, m.fit(X_train, y_train).predict(X_test)), 3)
full = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
acc_full = round(accuracy_score(y_test, full.predict(X_test)), 3)
best_k = max(sorted(acc_by_k), key=acc_by_k.get)
print(acc_by_k, acc_full, best_k)
```

### explain
Десяти измерений мало (около 0.82), к 100 компонентам точность догоняет полный TF-IDF с его 485 столбцами. Сжатие почти без потерь — полезно, когда признаки нужно хранить или искать по ним быстро; но и выигрыша на этих данных оно не даёт.

## task: skipgram | Соседи слов для word2vec | base

Напишите функцию `skipgram_pairs(tokens, window=2)`, которая возвращает список пар `(центральное, сосед)` для всех слов в окне ±`window` (само слово себе не сосед). Посчитайте `n_pairs` — число пар по всем отзывам (токены — `tokenize` из заготовки, окно 2), `top_courier` — список трёх самых частых соседей слова «курьер» и `shared` — множество общих слов среди **трёх** самых частых соседей «дороговато» и «недорого».

### starter
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

```

### check
```python
import re as _re, pandas as _pd
from collections import Counter as _C
f = need('skipgram_pairs')
assert list(f(['а', 'б', 'в'], window=1)) == [('а', 'б'), ('б', 'а'), ('б', 'в'), ('в', 'б')], f'skipgram_pairs(["а", "б", "в"], window=1) = {f(["а", "б", "в"], window=1)}. Нужны пары (центральное, сосед) по порядку слов.'
assert len(f(['а', 'б', 'в', 'г'], window=2)) == 10, 'Окно ±2 у краёв обрезается: для 4 слов должно быть 10 пар.'
def _p(t, w=2):
    return [(c, t[j]) for i, c in enumerate(t) for j in range(max(0, i - w), min(len(t), i + w + 1)) if j != i]
P = [p for t in _pd.read_csv('reviews_text.csv')['text'] for p in _p(_re.findall(r'[а-яё]+', t.lower()))]
assert need('n_pairs') == len(P), f'n_pairs = {need("n_pairs")}, а нужно {len(P)}.'
ctx = lambda w, k: [c for c, _ in _C(o for x, o in P if x == w).most_common(k)]
assert list(need('top_courier')) == ctx('курьер', 3), f'top_courier = {need("top_courier")}. Считайте соседей, у которых центральное слово — «курьер».'
s = set(ctx('дороговато', 3)) & set(ctx('недорого', 3))
assert set(need('shared')) == s, f'shared = {need("shared")}. Пересечение множеств трёх самых частых соседей.'
```

### hint
Два вложенных цикла: внешний по позициям `i`, внутренний по `j` от `i - window` до `i + window`, с обрезкой по краям списка и пропуском `j == i`.

### hint
Границы окна: `range(max(0, i - window), min(len(tokens), i + window + 1))`. Частые соседи слова `w`: `Counter(c for x, c in pairs if x == w).most_common(3)` — это список пар (слово, счётчик).

### hint
```python
pairs = [p for t in r["text"] for p in skipgram_pairs(tokenize(t))]
def top(w, k):
    return [c for c, _ in Counter(c for x, c in pairs if x == w).most_common(k)]
top_courier = top("курьер", 3)
shared = set(top("дороговато", 3)) & set(top("недорого", 3))
```

### solution
```python
import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

def skipgram_pairs(tokens, window=2):
    pairs = []
    for i, center in enumerate(tokens):
        for j in range(max(0, i - window), min(len(tokens), i + window + 1)):
            if j != i:
                pairs.append((center, tokens[j]))
    return pairs

pairs = [p for t in r["text"] for p in skipgram_pairs(tokenize(t))]
n_pairs = len(pairs)

def top(w, k):
    return [c for c, _ in Counter(c for x, c in pairs if x == w).most_common(k)]

top_courier = top("курьер", 3)
shared = set(top("дороговато", 3)) & set(top("недорого", 3))
print(n_pairs, top_courier, shared)
```

### explain
Около 63 тысяч обучающих пар из 2400 коротких отзывов — для word2vec это крохи: обычно счёт идёт на сотни миллионов. Соседи «курьера» («раньше», «приехал», «вежливый») связывают его с доставкой, а у «дороговато» и «недорого» два главных соседа одни и те же — «для» и «такого» (из фраз «недорого для такого качества» и «дороговато для такого кофе»): word2vec поставит антонимы рядом. Частая ошибка — забыть обрезку окна по краям: `range(i - window, i + window + 1)` у начала текста даёт отрицательные `j`, и `tokens[j]` молча возьмёт слова **с конца** текста — пары станут бессмысленными без всякой ошибки (а у конца текста код упадёт с `IndexError`).

## task: zero-shot | Темы без обучения | star

Попробуйте определить тему отзыва вообще без разметки — сходством с описанием темы. Постройте LSA, как в задаче «Похожие отзывы» (TF-IDF и SVD обучены на всех текстах), переведите в то же пространство описания тем `desc` (`svd.transform(tfidf.transform(...))`), нормируйте и припишите каждому отзыву тему с наибольшим косинусом. Сохраните `zs_pred` (массив или Series тем), `zs_acc` — долю совпадений с колонкой `topic` (3 знака) и `base_acc` — долю самой частой темы (3 знака).

### setup
```python
desc = {
    "доставка": "доставка курьер привезли заказ опоздал",
    "еда": "еда вкусно выпечка блюда порции",
    "кофе": "кофе капучино латте зерно",
    "обслуживание": "персонал сотрудники бариста вежливо обслуживание",
    "цена": "цена дорого цены стоимость",
    "атмосфера": "атмосфера уютно музыка интерьер шумно",
}
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.decomposition import TruncatedSVD as _SVD
r0 = _pd.read_csv('reviews_text.csv'); d0 = need('desc', dict)
tf0 = _TF(); s0 = _SVD(n_components=50, random_state=0)
Z0 = s0.fit_transform(tf0.fit_transform(r0['text'])); Z0 = Z0 / _np.linalg.norm(Z0, axis=1, keepdims=True)
D0 = s0.transform(tf0.transform(list(d0.values()))); D0 = D0 / _np.linalg.norm(D0, axis=1, keepdims=True)
p0 = _np.array(list(d0))[_np.argmax(Z0 @ D0.T, axis=1)]
acc = round(float((p0 == r0['topic']).mean()), 3)
got = _np.asarray(need('zs_pred'))
assert len(got) == 2400, f'В zs_pred {len(got)} значений.'
assert (got == p0).mean() > 0.98, f'Предсказания совпадают с эталоном лишь на {(got == p0).mean():.0%}.'
assert close(need('zs_acc'), acc, 0.006), f'zs_acc = {need("zs_acc")}, а нужно {acc}.'
assert close(need('base_acc'), round(float(r0['topic'].value_counts(normalize=True).iloc[0]), 3), 0.001), f'base_acc = {need("base_acc")}.'
```

### hint
Сначала LSA по всем отзывам, как в задаче «Похожие отзывы»: `Z`, затем `Zn`.

### hint
`D = svd.transform(tfidf.transform(list(desc.values())))`; после нормировки `Zn @ Dn.T` — матрица 2400 × 6, `argmax(axis=1)` — номер темы, `np.array(list(desc))[...]` — её название.

### hint
Доля самой частой темы: `r["topic"].value_counts(normalize=True).iloc[0]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
tfidf = TfidfVectorizer()
svd = TruncatedSVD(n_components=50, random_state=0)
Z = svd.fit_transform(tfidf.fit_transform(r["text"]))
Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)
D = svd.transform(tfidf.transform(list(desc.values())))
Dn = D / np.linalg.norm(D, axis=1, keepdims=True)

zs_pred = np.array(list(desc))[np.argmax(Zn @ Dn.T, axis=1)]
zs_acc = round(float((zs_pred == r["topic"]).mean()), 3)
base_acc = round(float(r["topic"].value_counts(normalize=True).iloc[0]), 3)
print(zs_acc, base_acc)
print(pd.crosstab(r["topic"], zs_pred))
```

### explain
Без единой размеченной строки — около 47 % против 29 % у «всегда кофе»; обученная модель из урока «Классификация текстов» даёт около 79 %. Описание из пяти слов плохо покрывает тему, а LSA не знает синонимов. Предобученные эмбеддинги или LLM на этом же приёме работают заметно лучше — но и их результат проверяют так же: на размеченной выборке, с матрицей ошибок.
