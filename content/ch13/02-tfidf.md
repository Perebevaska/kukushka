---
title: "Мешок слов и TF-IDF в sklearn"
files: [reviews_text.csv]
lead: "Превращаем отзывы в таблицу признаков: столбец на каждое слово, в клетке — сколько раз оно встретилось. Знакомимся с CountVectorizer и TfidfVectorizer, разреженными матрицами, биграммами и весом TF-IDF, который отличает характерные слова от просто частых."
recap:
  - "`CountVectorizer().fit_transform(texts)` — мешок слов для всех текстов: строка — текст, столбец — слово."
  - "Результат — разреженная матрица (sparse): хранятся только ненулевые клетки. `X.shape`, `X.nnz`, `X.toarray()` для маленьких кусков."
  - "`get_feature_names_out()` — какому слову соответствует столбец."
  - "`ngram_range=(1, 2)` добавляет пары соседних слов (биграммы): «не советую» становится отдельным признаком. `min_df` отбрасывает редкие."
  - "TF-IDF = частота слова в тексте × редкость слова в коллекции (idf). Частые везде слова получают маленький вес, характерные — большой."
  - "Векторайзер обучают (fit) только на обучающих текстах, к тестовым применяют `transform` — как StandardScaler."
---

## CountVectorizer

В уроке «Текст как данные: очистка и токены» мы строили мешок слов руками. В sklearn это делает `CountVectorizer`:

```python
from sklearn.feature_extraction.text import CountVectorizer

docs = ["Кофе вкусный, но дорого.", "Кофе горький, кофе холодный.", "Не советую."]
cv = CountVectorizer()
X = cv.fit_transform(docs)
print(cv.get_feature_names_out())
print(X.toarray())
```

**Что здесь происходит:**

- `fit` собирает словарь — все слова из текстов (по умолчанию в нижнем регистре, слова из 2+ букв и цифр);
- `transform` считает для каждого текста, сколько раз встретилось каждое слово;
- `fit_transform` — оба шага сразу;
- `get_feature_names_out()` — названия столбцов по порядку (алфавитному);
- `cv.vocabulary_` — обратный словарь «слово → номер столбца»: `cv.vocabulary_["кофе"]` сразу даёт столбец слова;
- `X.toarray()` — показать матрицу обычной таблицей чисел (для маленьких примеров).

**Что получилось:** 3 строки (отзыва) и 8 столбцов (слов). Во второй строке у «кофе» стоит 2 — слово встретилось дважды. Это ровно та таблица, которую мы собирали руками в уроке «Текст как данные: очистка и токены», только словарь и подсчёт сделал sklearn.

::: sql
`CountVectorizer` делает то же, что запрос `SELECT review_id, word, COUNT(*) FROM tokens GROUP BY review_id, word` с последующим разворотом (PIVOT) слов в столбцы. Только столбцов — сотни, а большинство клеток — нули.
:::

По умолчанию шаблон слова — «две и больше буквы или цифры подряд». Однобуквенные «и», «в», «с» отбрасываются сами, а «не» — сохраняется. Шаблон меняется параметром `token_pattern`. Поэтому на всех отзывах словарь `CountVectorizer` — 485 слов, а не 491, как при `re.findall`: ушли 9 однобуквенных слов, зато добавились числа «10», «20» и склейка «из10».

{{practice: count, min-df}}

## Разреженные матрицы

На всех отзывах таблица получается большой и почти пустой: в каждом отзыве десяток слов из нескольких сотен.

```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

r = pd.read_csv("reviews_text.csv")
X = CountVectorizer().fit_transform(r["text"])
print("форма:", X.shape)
print("ненулевых клеток:", X.nnz, f"({X.nnz / (X.shape[0] * X.shape[1]):.1%})")
print(type(X).__name__)
```

**Что здесь происходит:**

- `X.shape` — (число отзывов, размер словаря).
- `X.nnz` (number of non-zeros) — сколько клеток не равны нулю.
- `X.nnz / (строк × столбцов)` — доля заполненных клеток, **плотность** матрицы.
- `type(X).__name__` — тип объекта: `csr_matrix` (или `csr_array`) — разреженная матрица по строкам.

::: figure sparse-matrix
Три отзыва из первого примера урока: в обычной таблице 24 клетки, из них ненулевых 9. Разреженная матрица хранит только их — по сути тройки «строка, столбец, значение».
:::

Ненулевых клеток — около 1.6 %. Поэтому sklearn возвращает **разреженную матрицу** (sparse matrix): она хранит только ненулевые значения и их координаты. На миллионе отзывов и сотне тысяч слов обычная таблица заняла бы сотни гигабайт, а разреженная — мегабайты. Модели sklearn (логистическая регрессия, наивный Байес, SGD) принимают её напрямую. Для просмотра небольшого куска есть `X[:5].toarray()`.

## Биграммы

Мешок слов теряет порядок, а вместе с ним — и отрицание: «не понравился» превращается в «не» + «понравился». **N-граммы** — последовательности из n соседних слов — частично возвращают порядок. `ngram_range=(1, 2)` берёт и отдельные слова, и пары:

```python
from sklearn.feature_extraction.text import CountVectorizer
cv = CountVectorizer(ngram_range=(1, 2))
cv.fit(["Больше не приду", "Обязательно приду ещё"])
print(cv.get_feature_names_out())
```

Признак «не приду» теперь отдельный — и он однозначно негативный, тогда как «приду» встречается в обоих отзывах.

::: figure ngram-window
Отзыв «Больше не приду» при `ngram_range=(1, 2)`: окно из одного слова даёт три признака, окно из двух соседних — ещё два. Отрицание живёт в паре «не приду».
:::

Цена — размер словаря. На наших отзывах пары слов увеличивают его примерно в пять раз. Редкие n-граммы, встретившиеся в паре отзывов, только мешают; `min_df=5` оставляет признаки, которые есть хотя бы в 5 текстах.

::: deep Символьные n-граммы
N-граммы бывают не только из слов, но и из букв. `CountVectorizer(analyzer="char_wb", ngram_range=(3, 4))` режет каждое слово на кусочки по 3–4 буквы, добавив пробел по краям: «выпечка» → « вы», «вып», «ыпе», «печ», «ечк», «чка», «ка », « вып», «выпе»… У опечатки «ыпечка» почти все эти кусочки те же, поэтому в символьном представлении слова оказываются похожими, а в словном — совсем разными. Плата — словарь в несколько раз больше. Попробовать можно в задаче «Символьные n-граммы».
:::

::: predict
```python static
from sklearn.feature_extraction.text import CountVectorizer
cv = CountVectorizer(ngram_range=(1, 2)).fit(["кофе очень вкусный"])
print(len(cv.get_feature_names_out()))
```

- `3`
- [x] `5`
- `6`

Почему: три слова и две пары соседних слов — «кофе очень» и «очень вкусный».
:::

::: quiz
Зачем при анализе тональности добавлять биграммы (`ngram_range=(1, 2)`)?

- [x] Пара «не приду» становится отдельным признаком — мешок слов частично возвращает порядок, а с ним и отрицание
  > Само по себе «приду» встречается и в довольных, и в недовольных отзывах, а пара «не приду» однозначно негативная.
- [ ] Чтобы уменьшить словарь
  > Наоборот: на наших отзывах пары слов увеличивают словарь примерно в пять раз — поэтому и нужен `min_df`.
- [ ] Биграммы заменяют отдельные слова и убирают лишние признаки
  > `ngram_range=(1, 2)` берёт и отдельные слова, и пары; отдельные слова никуда не деваются.
- [ ] Чтобы модель справлялась с опечатками
  > От опечаток помогают буквенные n-граммы — кусочки слов. Биграммы слов опечатку не исправят.
:::

{{practice: ngrams, char-ngrams}}

## TF-IDF

Не все слова одинаково полезны. «Не» и «кофе» есть в каждом пятом отзыве; «водянистый» — в нескольких, зато сразу говорит, о чём жалоба. **TF-IDF** учитывает это:

- **TF** (term frequency) — сколько раз слово встречается в этом тексте;
- **IDF** (inverse document frequency) — насколько слово редкое во всей коллекции: $\mathrm{idf} = \ln\dfrac{1 + N}{1 + \mathrm{df}} + 1$, где $N$ — число текстов, $\mathrm{df}$ — в скольких из них слово встречается.

Вес слова = TF × IDF, а затем вектор каждого текста нормируется к длине 1 — каждое число делится на √(сумму квадратов всех чисел строки), как в примере ниже, — чтобы длинные отзывы не получали преимущества.

::: tip Аналогия
idf — как приметы постоянного гостя для бариста. «Заказывает кофе» верно почти для каждого и никого не выделяет, а «просит латте на овсяном с корицей» верно для немногих — по такой примете гостя узнают сразу. Чем реже примета по всей сети, тем больше её вес. Хромает аналогия в одном: редкость ещё не значит полезность — опечатка, встретившаяся один раз, получает максимальный idf, хотя смысла в ней мало; поэтому совсем редкие слова отсекают параметром `min_df`.
:::

Посчитаем руками на трёх текстах ($N = 3$):

1. «кофе вкусный»
2. «кофе горький»
3. «кофе вкусный вкусный»

| слово | в скольких текстах (df) | $\mathrm{idf} = \ln\frac{1 + 3}{1 + \mathrm{df}} + 1$ |
|---|---|---|
| кофе | 3 | ln(4/4) + 1 = **1.00** |
| вкусный | 2 | ln(4/3) + 1 ≈ **1.29** |
| горький | 1 | ln(4/2) + 1 ≈ **1.69** |

«Кофе» есть везде — минимальный вес, «горький» — только в одном тексте — максимальный. Для третьего текста: TF × IDF = кофе 1 × 1.00 = 1.00, вкусный 2 × 1.29 = 2.58. Длина вектора √(1.00² + 2.58²) ≈ 2.77; после нормировки — кофе 0.36, вкусный 0.93. Проверим кодом:

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

docs = ["кофе вкусный", "кофе горький", "кофе вкусный вкусный"]
tf = TfidfVectorizer()
T = tf.fit_transform(docs)
print(pd.Series(tf.idf_, index=tf.get_feature_names_out()).round(2).to_dict())
print(pd.DataFrame(T.toarray(), columns=tf.get_feature_names_out()).round(2))
```

**Что здесь происходит:**

- `tf.idf_` — idf каждого слова словаря после `fit`, в порядке столбцов.
- Строки матрицы `T` — уже нормированные векторы: сумма квадратов в каждой строке равна 1.

::: figure tfidf-steps
Тот же расчёт таблицами: счётчики умножаются на idf по столбцам, затем каждая строка делится на свою длину. «Кофе» есть во всех трёх текстах — у него самый маленький вес.
:::

Числа совпали с ручным расчётом. Теперь — на всех отзывах.

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

r = pd.read_csv("reviews_text.csv")
tf = TfidfVectorizer()
T = tf.fit_transform(r["text"])
idf = pd.Series(tf.idf_, index=tf.get_feature_names_out()).sort_values()
print("самые частые (маленький idf):", idf.head(5).round(2).to_dict())

print(r["text"][0])
row = pd.Series(T[0].toarray()[0], index=tf.get_feature_names_out())
print(row[row > 0].sort_values(ascending=False).round(3))
```

**Что здесь происходит:**

- `pd.Series(tf.idf_, index=...)` — idf всех слов с подписями; `sort_values()` — от самых частых (маленький idf) к редким.
- `T[0]` — первая строка разреженной матрицы, `.toarray()[0]` — она же как обычный массив.
- `row[row > 0]` — только слова, которые есть в этом отзыве.

В первом отзыве самый большой вес у «дороговато» — редкого и характерного слова, а у «кофе» и «но» — самые маленькие: они есть почти везде. Для классификации TF-IDF обычно чуть лучше простых счётчиков.

::: warn
Векторайзер — такой же шаг предобработки, как StandardScaler (глава 7): словарь и idf считаются по обучающим текстам (`fit_transform(train)`), а к тестовым применяется `transform(test)`. Слова, которых не было в обучении, тестовые тексты просто игнорируют. Удобнее всего — в `Pipeline` вместе с моделью.
:::

::: figure vec-fit-transform
Словарь и idf запоминаются при `fit` на обучающих текстах. Тестовый текст проходит через `transform` с тем же словарём: знакомые слова получают веса, незнакомое «остыл» пропадает без ошибки.
:::

{{practice: train-only}}

::: quiz
Слово «кофе» встречается почти в каждом отзыве. Какой у него будет вес в TF-IDF по сравнению с редким словом «грубил»?

- [x] Маленький: idf наказывает слова, которые есть везде, — они не отличают один отзыв от другого
  > TF-IDF поднимает слова, частые в этом тексте, но редкие в коллекции.
- [ ] Большой: оно самое частое
  > Частота в тексте (tf) большая, но idf близок к минимуму.
- [ ] Нулевой
  > В sklearn idf сглажен и никогда не бывает нулевым — вес маленький, но не ноль.
- [ ] Такой же, как у «грубил»
  > Редкие слова получают заметно больший idf.
:::

{{practice: p-tfidf, idf, idf-by-hand, keywords}}

## Практика

## task: count | Матрица счётчиков | warmup

Постройте `CountVectorizer` по всем отзывам. Сохраните `shape` (форма матрицы), `density` — долю ненулевых клеток (4 знака) и `n_kofe` — сколько раз слово «кофе» встречается во всех отзывах суммарно.

### starter
```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import pandas as _pd
from sklearn.feature_extraction.text import CountVectorizer as _CV
r0 = _pd.read_csv('reviews_text.csv'); cv = _CV(); X = cv.fit_transform(r0['text'])
assert tuple(need('shape')) == X.shape, f'shape = {need("shape")}.'
assert close(need('density'), round(X.nnz / (X.shape[0] * X.shape[1]), 4), 2e-4), f'density = {need("density")}.'
assert need('n_kofe') == int(X[:, cv.vocabulary_['кофе']].sum()), f'n_kofe = {need("n_kofe")}.'
```

### hint
Форма — `X.shape`, ненулевые — `X.nnz`, плотность — `X.nnz / (X.shape[0] * X.shape[1])`.

### hint
Номер столбца слова — `cv.vocabulary_["кофе"]`; сумма по столбцу — `X[:, j].sum()`.

### solution
```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

cv = CountVectorizer()
X = cv.fit_transform(r["text"])
shape = X.shape
density = round(X.nnz / (X.shape[0] * X.shape[1]), 4)
n_kofe = int(X[:, cv.vocabulary_["кофе"]].sum())
```

## task: p-tfidf | TF-IDF для двух текстов | warmup

Соберите код, который считает TF-IDF и печатает, сумма квадратов весов каждой строки равна 1.

### parsons
```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
docs = ["кофе вкусный", "кофе горький и холодный"]
T = TfidfVectorizer().fit_transform(docs).toarray()
norms = (T ** 2).sum(axis=1)
print(np.allclose(norms, 1))
```

### check
```python
assert _lines == ['True'], f'Сейчас: {_lines}.'
```

### hint
Сначала тексты, потом матрица, потом нормы.

### hint
`fit_transform` нужен до того, как считать что-то по строкам матрицы.

## task: idf | Редкие и частые | warmup

Обучите `TfidfVectorizer` на всех отзывах и сохраните `idf` — Series весов idf с индексом-словами. В `common3` — три слова с наименьшим idf, в `idf_ne` — idf слова «не» (3 знака).

### starter
```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import pandas as _pd
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
r0 = _pd.read_csv('reviews_text.csv'); tf = _TF().fit(r0['text'])
s = _pd.Series(tf.idf_, index=tf.get_feature_names_out())
assert _pd.Series(need('idf')).sort_index().round(6).equals(s.sort_index().round(6)), 'idf — Series(tf.idf_, index=tf.get_feature_names_out()).'
assert list(need('common3')) == list(s.sort_values().index[:3]), f'common3 = {need("common3")}.'
assert close(need('idf_ne'), round(s['не'], 3), 0.002), f'idf_ne = {need("idf_ne")}.'
```

### hint
Векторайзер нужно обучить (`fit`) на всех отзывах — только после этого у него появляется `idf_`.

### hint
`pd.Series(tf.idf_, index=tf.get_feature_names_out())`, затем `.sort_values()` — в начале частые слова, в конце редкие.

### solution
```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
r = pd.read_csv("reviews_text.csv")

tf = TfidfVectorizer().fit(r["text"])
idf = pd.Series(tf.idf_, index=tf.get_feature_names_out())
common3 = list(idf.sort_values().index[:3])
idf_ne = round(idf["не"], 3)
```

## task: idf-by-hand | Формула idf | base

Проверьте формулу: для слова «доставка» посчитайте вручную `df` — в скольких отзывах оно встречается (используйте `CountVectorizer(binary=True)`, где клетка — 0 или 1), и idf = ln((1 + N) / (1 + df)) + 1. Сохраните `df_word`, `idf_manual` (4 знака) и `idf_sklearn` — из `TfidfVectorizer` (4 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.feature_extraction.text import CountVectorizer as _CV, TfidfVectorizer as _TF
r0 = _pd.read_csv('reviews_text.csv'); cv = _CV(binary=True); B = cv.fit_transform(r0['text'])
dfw = int(B[:, cv.vocabulary_['доставка']].sum()); n = len(r0)
assert need('df_word') == dfw, f'df_word = {need("df_word")}, а нужно {dfw}.'
assert close(need('idf_manual'), round(_np.log((1 + n) / (1 + dfw)) + 1, 4), 2e-4), f'idf_manual = {need("idf_manual")}.'
tf = _TF().fit(r0['text'])
assert close(need('idf_sklearn'), round(tf.idf_[tf.vocabulary_['доставка']], 4), 2e-4), f'idf_sklearn = {need("idf_sklearn")}.'
```

### hint
df слова — в скольких отзывах оно встречается хотя бы раз; удобно взять из бинарного мешка: `CountVectorizer(binary=True)` и сумма по столбцу.

### hint
Натуральный логарифм — `np.log`. N — число отзывов `len(r)`. Формула: `np.log((1 + N) / (1 + df)) + 1`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
r = pd.read_csv("reviews_text.csv")

cv = CountVectorizer(binary=True)
B = cv.fit_transform(r["text"])
df_word = int(B[:, cv.vocabulary_["доставка"]].sum())
n = len(r)
idf_manual = round(np.log((1 + n) / (1 + df_word)) + 1, 4)
tf = TfidfVectorizer().fit(r["text"])
idf_sklearn = round(tf.idf_[tf.vocabulary_["доставка"]], 4)
```

### explain
«Доставка» встречается в 88 отзывах из 2400, поэтому idf = ln(2401 / 89) + 1 ≈ 4.295 — ровно столько хранит и `TfidfVectorizer`. Единицы в числителе и знаменателе — сглаживание: формула не делит на ноль даже для слова, которого нет в обучающих текстах. Чем реже слово, тем больше idf. В этом словаре idf меняется от ≈ 2.59 у самого частого слова до ≈ 8.09 у слов, которые встретились один раз. Частое слово почти ничего не говорит о конкретном отзыве, а редкое выделяет его.

## task: ngrams | Размер словаря | base

Сравните размер словаря `CountVectorizer` на всех отзывах для трёх настроек: только слова; слова и биграммы; слова и биграммы с `min_df=5`. Сохраните словарь `sizes` с ключами `"1"`, `"1-2"`, `"1-2 min5"` и `has_ne_pridu` — есть ли среди признаков третьей настройки биграмма «не приду».

### starter
```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import pandas as _pd
from sklearn.feature_extraction.text import CountVectorizer as _CV
r0 = _pd.read_csv('reviews_text.csv')
w = {'1': len(_CV().fit(r0['text']).vocabulary_), '1-2': len(_CV(ngram_range=(1, 2)).fit(r0['text']).vocabulary_)}
c3 = _CV(ngram_range=(1, 2), min_df=5).fit(r0['text']); w['1-2 min5'] = len(c3.vocabulary_)
assert dict(need('sizes')) == w, f'sizes = {need("sizes")}, а нужно {w}.'
assert need('has_ne_pridu') == ('не приду' in c3.vocabulary_), f'has_ne_pridu = {need("has_ne_pridu")}.'
```

### hint
Размер словаря — `len(cv.vocabulary_)` после `fit`.

### hint
Для каждого варианта создайте новый `CountVectorizer` с нужными параметрами (`ngram_range`, `min_df`) и обучите его на всех текстах.

### solution
```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

sizes = {}
sizes["1"] = len(CountVectorizer().fit(r["text"]).vocabulary_)
sizes["1-2"] = len(CountVectorizer(ngram_range=(1, 2)).fit(r["text"]).vocabulary_)
cv3 = CountVectorizer(ngram_range=(1, 2), min_df=5).fit(r["text"])
sizes["1-2 min5"] = len(cv3.vocabulary_)
has_ne_pridu = "не приду" in cv3.vocabulary_
```

### explain
Биграммы увеличивают словарь в пять с лишним раз: 485 слов, но 2565 признаков со словосочетаниями. Большинство биграмм встречаются один-два раза и для модели — шум. `min_df=5` оставляет только устойчивые словосочетания, и словарь сжимается до 690. Среди них «не приду» — то, ради чего биграммы и нужны: по отдельности «не» и «приду» тональность не передают, а вместе это явная жалоба.

## task: min-df | Сколько слов оставить | base

Параметр `min_df` выкидывает слова, которые встречаются меньше чем в `min_df` отзывах. Для `min_df` из `[1, 2, 5, 20]` обучите `CountVectorizer(min_df=...)` на всех отзывах и сохраните `vocab_by_min_df` — словарь `{min_df: размер словаря}`. Для `min_df=5` сохраните `kept_share` — какую долю всех употреблений слов (сумма матрицы) сохраняет урезанный словарь по сравнению с полным (4 знака), и `dropped_examples` — 5 первых по алфавиту слов, которые есть в полном словаре, но выпали при `min_df=5`.

### starter
```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import pandas as _pd
from sklearn.feature_extraction.text import CountVectorizer as _CV
r0 = _pd.read_csv('reviews_text.csv')
w = {m: len(_CV(min_df=m).fit(r0['text']).vocabulary_) for m in [1, 2, 5, 20]}
g = {int(k): v for k, v in need('vocab_by_min_df', dict).items()}
assert g == w, f'vocab_by_min_df = {g}, а нужно {w}.'
full = _CV().fit(r0['text']); cut = _CV(min_df=5).fit(r0['text'])
ks = round(cut.transform(r0['text']).sum() / full.transform(r0['text']).sum(), 4)
assert close(need('kept_share'), ks, 2e-4), f'kept_share = {need("kept_share")}, а нужно {ks}.'
de = sorted(set(full.vocabulary_) - set(cut.vocabulary_))[:5]
assert list(need('dropped_examples')) == de, f'dropped_examples = {need("dropped_examples")}, а нужно {de}.'
```

### hint
Словарь размеров — словарное выражение по `min_df`: `len(CountVectorizer(min_df=m).fit(r["text"]).vocabulary_)`.

### hint
Употреблений слов — сумма всех клеток матрицы: `cv.transform(r["text"]).sum()`. Посчитайте её для полного и урезанного векторайзера и поделите.

### hint
Выпавшие слова — разность множеств ключей словарей: `sorted(set(full.vocabulary_) - set(cut.vocabulary_))[:5]`.

### solution
```python
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

vocab_by_min_df = {m: len(CountVectorizer(min_df=m).fit(r["text"]).vocabulary_) for m in [1, 2, 5, 20]}
full = CountVectorizer().fit(r["text"])
cut = CountVectorizer(min_df=5).fit(r["text"])
kept_share = round(cut.transform(r["text"]).sum() / full.transform(r["text"]).sum(), 4)
dropped_examples = sorted(set(full.vocabulary_) - set(cut.vocabulary_))[:5]
print(vocab_by_min_df, kept_share, dropped_examples)
```

### explain
Уже `min_df=2` выбрасывает почти половину словаря (485 → 258), а `min_df=5` оставляет 213 слов — и эти 213 слов покрывают больше 98 % всех употреблений. Выпавшие слова — опечатки вроде «аветренный» и «адес»: модели они не помогли бы, потому что встречаются один-два раза. Дальше рост `min_df` почти ничего не меняет (213 → 210): «костяк» словаря — слова, которые встречаются десятки раз. Типичная ошибка — поставить слишком большой `min_df` на маленьких данных и выбросить редкие, но важные слова; проверяйте, что именно выпало.

## task: keywords | Ключевые слова отзыва | plus

TF-IDF удобно использовать и без модели — как «ключевые слова» текста. Обучите `TfidfVectorizer()` на всех отзывах. Напишите `keywords(i, k=3)` — список из `k` слов отзыва номер `i` с наибольшим весом TF-IDF (по убыванию веса). Сохраните `kw` — словарь `{i: keywords(i)}` для `i` от 0 до 4 и `share_topic_word` — долю из первых 200 отзывов, у которых хотя бы одно из трёх ключевых слов совпадает с одним из слов-маркеров темы этого отзыва (словарь `MARKERS` — в заготовке).

### setup
```python
import pandas as pd
r = pd.read_csv("reviews_text.csv")
MARKERS = {
    "кофе": {"кофе", "капучино", "латте", "раф", "флэт", "уайт", "зерно", "молоко"},
    "еда": {"круассаны", "круассан", "сырники", "десерты", "десерт", "сэндвич", "выпечка", "чизкейк", "завтраки", "салате"},
    "обслуживание": {"бариста", "персонал", "кассе", "сотрудники", "обслужили", "поздоровался", "заказ", "оплату"},
    "доставка": {"курьер", "доставка", "доставили", "привезли", "адрес", "пакете", "крышки"},
    "цена": {"дорого", "цены", "дороговато", "недорого", "бонусы", "скидки", "акция", "деньги", "цена"},
    "атмосфера": {"уютно", "музыка", "столы", "шумно", "душно", "интерьер", "туалете", "светло", "тихо"},
}
```

### starter
```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

tf = TfidfVectorizer()
T = tf.fit_transform(r["text"])
names = tf.get_feature_names_out()

def keywords(i, k=3):
    ...

```

### check
```python
import numpy as _np
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
r0, M = need('r'), need('MARKERS')
tf0 = _TF(); T0 = tf0.fit_transform(r0['text']); nm = tf0.get_feature_names_out()
def _kw(i, k=3):
    row = T0[i].toarray()[0]
    idx = [j for j in _np.argsort(-row, kind='stable') if row[j] > 0][:k]
    return [str(nm[j]) for j in idx]
f = need('keywords')
for i in range(5):
    assert set(f(i)) == set(_kw(i)), f'keywords({i}) = {f(i)}, а нужно {_kw(i)}.'
g = need('kw', dict)
assert sorted(g) == [0, 1, 2, 3, 4], 'kw — словарь для отзывов 0…4.'
w = _np.mean([bool(set(_kw(i)) & M[r0.loc[i, 'topic']]) for i in range(200)])
assert close(need('share_topic_word'), round(float(w), 3), 0.006), f'share_topic_word = {need("share_topic_word")}, а нужно {w:.3f}.'
```

### hint
Строка отзыва `i` как обычный массив — `T[i].toarray()[0]`. Номера столбцов по убыванию веса — `np.argsort(-row)`.

### hint
Отбросьте нулевые веса (слов, которых в отзыве нет): `[j for j in np.argsort(-row) if row[j] > 0][:k]`, затем `names[j]`.

### hint
Совпадение с темой: `bool(set(keywords(i)) & MARKERS[r.loc[i, "topic"]])` — пересечение множеств непусто. Среднее таких `True/False` по 200 отзывам — доля.

### solution
```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

tf = TfidfVectorizer()
T = tf.fit_transform(r["text"])
names = tf.get_feature_names_out()

def keywords(i, k=3):
    row = T[i].toarray()[0]
    idx = [j for j in np.argsort(-row, kind="stable") if row[j] > 0][:k]
    return [str(names[j]) for j in idx]

kw = {i: keywords(i) for i in range(5)}
share_topic_word = round(float(np.mean([bool(set(keywords(i)) & MARKERS[r.loc[i, "topic"]]) for i in range(200)])), 3)
print(kw, share_topic_word)
```

### explain
Ключевые слова первых отзывов осмысленные: «дороговато» — у отзыва про цену, «кислое молоко» — про кофе. Но есть и мусор: «10» (из «10 из 10»), «даже», «было» — редкие в коллекции, но не о теме. Совпадение с темой — около половины отзывов: TF-IDF выделяет редкое, а не важное. Для быстрого просмотра это полезно (например, подсветить слова в интерфейсе), а для определения темы нужна модель, обученная на разметке, — урок «Классификация текстов».

## task: train-only | Обучение векторайзера без утечки | plus

Разделите отзывы `train_test_split(r["text"], test_size=0.25, random_state=42)`. Обучите `TfidfVectorizer` только на обучающей части и преобразуйте обе. Сохраните `X_train`, `X_test`, `n_unseen` — сколько разных слов тестовой части нет в словаре векторайзера (токены — `re.findall(r"(?u)\b\w\w+\b", text.lower())`, так же, как в sklearn) и `empty_test` — число тестовых отзывов, у которых вектор целиком нулевой.

### starter
```python
import re
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
r = pd.read_csv("reviews_text.csv")
text_train, text_test = train_test_split(r["text"], test_size=0.25, random_state=42)

```

### check
```python
import re as _re, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
r0 = _pd.read_csv('reviews_text.csv'); a, b = _tts(r0['text'], test_size=0.25, random_state=42)
tf = _TF().fit(a); Xb = tf.transform(b)
assert need('X_train').shape == (len(a), len(tf.vocabulary_)) and need('X_test').shape == Xb.shape, 'Векторайзер обучается на text_train, к text_test — только transform.'
words = {w for t in b for w in _re.findall(r'(?u)\b\w\w+\b', t.lower())}
un = len([w for w in words if w not in tf.vocabulary_])
assert need('n_unseen') == un, f'n_unseen = {need("n_unseen")}, а нужно {un}.'
assert need('empty_test') == int((Xb.getnnz(axis=1) == 0).sum()), f'empty_test = {need("empty_test")}.'
```

### hint
Векторайзер — `fit` только на `text_train`, к `text_test` — `transform`. Слова теста, которых нет в словаре, просто пропадут.

### hint
Ненулевых клеток в каждой строке разреженной матрицы — `X.getnnz(axis=1)`.

### hint
Новые слова теста: токенизируйте тест тем же шаблоном и возьмите разность множеств со словарём `set(vec.vocabulary_)`.

### solution
```python
import re
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
r = pd.read_csv("reviews_text.csv")
text_train, text_test = train_test_split(r["text"], test_size=0.25, random_state=42)

tf = TfidfVectorizer()
X_train = tf.fit_transform(text_train)
X_test = tf.transform(text_test)
test_words = {w for t in text_test for w in re.findall(r"(?u)\b\w\w+\b", t.lower())}
n_unseen = len([w for w in test_words if w not in tf.vocabulary_])
empty_test = int((X_test.getnnz(axis=1) == 0).sum())
```

### explain
Новые слова в тесте — это в основном опечатки: «недоого», «ыпечка», «рекоменую». Векторайзер их просто не видит. В живых отзывах таких слов много, и это одна из причин, почему для текстов придумали признаки на уровне кусочков слов (символьные n-граммы, `analyzer="char_wb"`) и эмбеддинги (урок «Эмбеддинги: векторы слов и отзывов»).

## task: char-ngrams | Символьные n-граммы | star

Сравните два векторайзера на опечатках. Обучите `TfidfVectorizer()` и `TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))` на всех отзывах. Для пары «правильное слово — опечатка» `("выпечка", "ыпечка")` посчитайте косинусное сходство их TF-IDF-векторов (`sklearn.metrics.pairwise.cosine_similarity`) в обоих представлениях. Косинусное сходство меряет, насколько похожи два вектора: от 0 (ни одного общего признака) до 1 (векторы одинаковые по направлению); подробно оно разобрано в уроке «Эмбеддинги: векторы слов и отзывов». Что такое `char_wb`, сказано во врезке «Символьные n-граммы» раздела «Биграммы». Сохраните `sim_words`, `sim_chars` (3 знака) и `vocab_chars` — размер словаря символьного векторайзера.

### starter
```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
r = pd.read_csv("reviews_text.csv")

```

### check
```python
import pandas as _pd
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.metrics.pairwise import cosine_similarity as _cs
r0 = _pd.read_csv('reviews_text.csv')
w = _TF().fit(r0['text']); c = _TF(analyzer='char_wb', ngram_range=(3, 4)).fit(r0['text'])
sw = round(float(_cs(w.transform(['выпечка']), w.transform(['ыпечка']))[0, 0]), 3)
sc = round(float(_cs(c.transform(['выпечка']), c.transform(['ыпечка']))[0, 0]), 3)
assert close(need('sim_words'), sw, 0.002) and close(need('sim_chars'), sc, 0.002), f'sim_words, sim_chars = {need("sim_words")}, {need("sim_chars")}, а нужно {sw}, {sc}.'
assert need('vocab_chars') == len(c.vocabulary_), f'vocab_chars = {need("vocab_chars")}.'
```

### hint
Нужны два векторайзера: словный (`TfidfVectorizer()`) и символьный (`TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))`), оба обученные на отзывах.

### hint
`cosine_similarity(vec.transform(["выпечка"]), vec.transform(["ыпечка"]))[0, 0]`.

### solution
```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
r = pd.read_csv("reviews_text.csv")

words = TfidfVectorizer().fit(r["text"])
chars = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4)).fit(r["text"])
sim_words = round(float(cosine_similarity(words.transform(["выпечка"]), words.transform(["ыпечка"]))[0, 0]), 3)
sim_chars = round(float(cosine_similarity(chars.transform(["выпечка"]), chars.transform(["ыпечка"]))[0, 0]), 3)
vocab_chars = len(chars.vocabulary_)
```

### explain
Для словного векторайзера «ыпечка» — либо незнакомое, либо совсем другое слово, сходство с «выпечкой» нулевое. Символьные кусочки («печ», «ечк», «чка») у них почти все общие, и сходство 0.615 — высокое: по шкале от 0 до 1 это заметно ближе к «одинаковым», чем к «ничего общего». Цена — словарь в разы больше. В отзывах с опечатками и разными формами слов символьные n-граммы часто дают прирост качества.
