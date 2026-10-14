---
title: Классификация текстов
files: [reviews_text.csv]
lead: "Соединяем TF-IDF и логистическую регрессию в один конвейер и учим модель отличать недовольных гостей от довольных, а потом — определять тему отзыва. Смотрим, на какие слова опирается модель, и разбираем её ошибки — среди них оказываются ошибки самих гостей. Как проверять саму разметку — в уроке «Качество разметки: голосование, каппа, золотой набор»."
recap:
  - "`make_pipeline(TfidfVectorizer(), LogisticRegression())` — конвейер «текст → признаки → модель»; fit и predict принимают сырые тексты."
  - "Веса логистической регрессии по словам объясняют модель: слова с большим положительным весом тянут к классу 1, отрицательным — к классу 0."
  - "MultinomialNB (наивный Байес) — быстрый классический классификатор текстов, хорошая базовая модель."
  - "Разбор ошибок: часть «ошибок» — это неверные метки (гость промахнулся оценкой). Точность выше качества разметки не поднимется."
  - "Для нескольких тем — та же модель (softmax), анализ — по матрице ошибок."
  - "Смешанные отзывы («вкусно, но долго») — естественный предел модели «одна тема на отзыв»."
---

## Конвейер для текстов

Векторайзер — шаг предобработки, поэтому его ставят в `Pipeline` вместе с моделью (глава 7). Тогда `fit` сам обучит словарь только на обучающих текстах, а `predict` примет сырые строки.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)           # 1 — гость недоволен
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
model.fit(X_train, y_train)
pred = model.predict(X_test)
print("доля правильных:", round(accuracy_score(y_test, pred), 3), "| F1:", round(f1_score(y_test, pred), 3))
print(model.predict(["Курьер опоздал, кофе остыл", "Очень уютно, вернусь"]))
```

**Что здесь происходит:**

- `y = (r["rating"] <= 3).astype(int)` — целевая переменная: 1, если оценка 3 и ниже (гость недоволен), иначе 0.
- `train_test_split(r["text"], y, ...)` — разбиваем **тексты**, а не готовую матрицу: векторайзер внутри конвейера сам обучится только на обучающих текстах (урок «Мешок слов и TF-IDF», задача «Обучение векторайзера без утечки»).
- `make_pipeline(TfidfVectorizer(), LogisticRegression(...))` — два шага: тексты → матрица TF-IDF → модель. `fit` обучает оба шага по очереди.
- `model.predict(["...", "..."])` — на вход подаются **сырые строки**: конвейер сам превратит их в признаки тем же словарём.
- `accuracy_score` — доля верных ответов; `f1_score` — баланс точности и полноты для класса 1 (глава 7).

94 % правильных ответов — против 80 % у правила «не или но» из урока «Текст как данные: очистка и токены» (там правило считали на всех отзывах; на этом же тесте оно даёт 78 %). И модель работает с новыми фразами, которых не было в обучении: «курьер опоздал» — недовольство.

{{practice: pipe, baseline, recall95}}

## На что смотрит модель

Модель линейная, и каждое слово получает вес (глава 7). Посмотрим на самые сильные:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)

vec, lr = model[0], model[-1]
w = pd.Series(lr.coef_[0], index=vec.get_feature_names_out()).sort_values()
print("за довольного:", w.head(6).round(2).to_dict())
print("за недовольного:", w.tail(6).round(2).to_dict())
```

**Что здесь происходит:**

- `model[0]`, `model[-1]` — первый и последний шаги конвейера: векторайзер и модель.
- `lr.coef_[0]` — веса логистической регрессии, по одному на столбец TF-IDF, то есть на слово. Порядок весов совпадает с порядком `get_feature_names_out()`.
- `sort_values()` — от самых отрицательных (тянут к классу 0, «доволен») к самым положительным (класс 1, «недоволен»).

Как веса превращаются в ответ для одного отзыва: каждое слово отзыва даёт вклад «вес TF-IDF × вес модели», вклады складываются со свободным членом, и сумма проходит через сигмоиду (глава 7).

::: figure text-logreg-contrib
Отзыв из тестовой части «Курьер вежливый, но выпечка вчерашняя.» (оценка гостя — 3 и ниже). «Курьер» и «вежливый» тянут к «доволен», но «но» с большим положительным весом и «вчерашняя» перевешивают: P(недоволен) = 0.85.
:::

Самые «недовольные» слова — «но» и «не», затем «грубил», «разочарована», «слишком», «шумно» (чуть ниже — «горький» и «пересушены»). Самые «довольные» — «спасибо», «ещё» (из «приду ещё»), «всем» (из «всем советую»). Модель по сути выучила правило «не или но» и десятки уточнений к нему.

::: tip
Список весов — первое, что стоит показать заказчику. Если среди важных слов есть странные (название кофейни, имя сотрудника, артефакт выгрузки), модель выучила что-то, кроме смысла, — это повод разобраться до внедрения.
:::

{{practice: top-words}}

## Разбор ошибок

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)

errors = pd.DataFrame({"текст": X_test, "оценка": r.loc[X_test.index, "rating"], "модель": pred})[pred != y_test]
print("ошибок:", len(errors))
print(errors.head(6).to_string())
```

**Что здесь происходит:**

- `pd.DataFrame({...})` — таблица с текстом, исходной оценкой гостя и ответом модели. Индекс у неё — индекс тестовых строк, поэтому оценку берём через `r.loc[X_test.index, "rating"]`.
- `[pred != y_test]` — оставляем только строки, где модель ошиблась.
- `.to_string()` — печать без обрезания длинных текстов.

Читаем ошибки глазами — и видим: «Круассаны свежие. Рекомендую.» с оценкой 2, «Доставили через полтора часа. Не советую.» с оценкой 4. Модель здесь права, ошибся гость — промахнулся звёздочкой. Сколько таких отзывов, можно оценить по уверенным ошибкам — модель уверена больше чем на 80 %, а метка противоположная: в тестовой части их 28 из 600, около 5 %, и почти все при чтении оказываются промахом звёздочкой (их найдёт задача «Ошибки или неверные метки»). Это **потолок**: никакая модель не превзойдёт качество разметки, если метки сами ошибаются.

::: note
Разбор ошибок — самый полезный шаг в работе с текстами. Он показывает, где модель действительно слаба (смешанные отзывы, редкие слова), а где виноваты данные. Найденные неверные метки исправляют — и модель на следующем обучении становится лучше.
:::

::: predict
```python static
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
m = make_pipeline(CountVectorizer(), MultinomialNB())
m.fit(["вкусно спасибо", "грубо долго", "вкусно уютно", "долго холодно"], [0, 1, 0, 1])
print(m.predict(["долго и холодно"]).tolist())
```

- `[0]`
- [x] `[1]`
- `Ошибка ValueError`

Почему: «долго» и «холодно» встречались только в отзывах класса 1. Незнакомое «и» (однобуквенное слово) векторайзер вообще не видит.
:::

::: quiz
Модель тональности ошиблась на отзыве «Вкусно, но долго ждали и грубили». Что разумно сделать при разборе ошибок?

- [x] Посмотреть, какие слова потянули прогноз в неверную сторону, и проверить, нет ли ошибки в самой разметке
  > Часть «ошибок» модели — неверные метки. Остальные подсказывают признаки: биграммы, обработку «но».
- [ ] Удалить отзыв из данных
  > Трудные примеры — самые полезные для улучшения модели.
- [ ] Поднять порог, пока ошибка не исчезнет
  > Подгонка порога под один отзыв испортит остальные.
- [ ] Переобучить модель на тесте
  > Тест — не для обучения.
:::

{{practice: errors, unsure}}

## Наивный Байес

Классическая модель для текстов — **наивный Байес** (`MultinomialNB`). Он считает, как часто каждое слово встречается в отзывах каждого класса, и предполагает («наивно»), что слова не зависят друг от друга. Обучается мгновенно, на коротких текстах работает почти как логистическая регрессия (у нас 93.8 % против 94.3 %) — хорошая первая модель. Работает со счётчиками (`CountVectorizer`), а не с TF-IDF.

Как он рассуждает, видно на игрушечном примере из вопроса выше. В отзывах класса 1 («грубо долго», «долго холодно») слово «долго» — 2 раза из 4 слов, «холодно» — 1 из 4. В отзывах класса 0 этих слов нет совсем. Для нового отзыва «долго холодно» Байес перемножает «насколько типично каждое слово для класса» и сравнивает классы: для класса 1 оба слова типичны, для класса 0 — нет. Побеждает класс 1. Чтобы слово, ни разу не встреченное в классе, не обнуляло всё произведение, к каждому счётчику прибавляют единицу (сглаживание, параметр `alpha=1`).

::: figure nb-toy
Тот же игрушечный пример числами: счётчики слов по классам, вероятности со сглаживанием +1, произведение по словам нового отзыва. Ответ совпадает с `predict_proba` sklearn.
:::

::: tip Аналогия
Наивный Байес рассуждает как бариста, угадывающий заказ по паре слов гостя: «овсяное» чаще слышно от любителей латте, «двойной» — от любителей эспрессо; бариста перемножает впечатления от каждого слова и выбирает, что вероятнее. «Наивность» в том, что слова считаются независимыми: «не» и «советую» оцениваются по отдельности, хотя смысл у них общий.
:::

::: warn Типичные ошибки
- **TF-IDF вместо счётчиков по привычке.** `MultinomialNB` построен на модели «сколько раз слово встретилось»; на TF-IDF он обучится и иногда работает не хуже, но начинать стоит со счётчиков (`CountVectorizer`), а замену проверять на отложенной части.
- **Верить вероятностям Байеса.** Перемножение по словам, которые на деле зависят друг от друга, считает одну улику несколько раз, и вероятности получаются слишком близкими к 0 или 1. Для ранжирования отзывов это не мешает, для порога «звоним гостю, если P > 0.7» — мешает: вероятности калибруют или берут логистическую регрессию.
:::

{{practice: p-nb, compare}}

## Темы отзывов

Тема — задача на шесть классов. Конвейер тот же: `LogisticRegression` сама перейдёт в многоклассовый режим — вместо одного набора весов учит по набору на каждый класс, а вероятности классов получает обобщением сигмоиды на несколько классов (его называют softmax):

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

r = pd.read_csv("reviews_text.csv")
X_train, X_test, y_train, y_test = train_test_split(r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)
print("доля правильных:", round((pred == y_test).mean(), 3))
pd.crosstab(y_test, pred, rownames=["тема"], colnames=["модель"])
```

**Что здесь происходит:**

- Целевая переменная теперь — текстовый столбец `topic` с шестью значениями; `stratify=r["topic"]` сохраняет доли тем в обеих частях.
- Для нескольких классов логистическая регрессия учит по набору весов на каждый класс и выбирает класс с наибольшей вероятностью.
- `pd.crosstab(правда, ответ)` — матрица ошибок с подписями: строки — настоящие темы, столбцы — ответы модели.

Около 79 % — заметно хуже тональности. В матрице ошибок видно, где именно: хуже всего находятся редкие темы — модель узнаёт только 32 из 58 отзывов про атмосферу (полнота 0.55) и 38 из 61 про цену (0.62), а кофе — 163 из 176. Самый частый неверный ответ — «кофе»: 36 из 129 ошибок, по нескольку отзывов из каждой темы. Причина в данных — в смешанных отзывах две темы («кофе отличный, но курьер опоздал»), а разметчик выбрал одну. Модель «одна тема на отзыв» здесь упирается в постановку задачи: честнее размечать **все** темы отзыва (multi-label классификация).

::: quiz
Тональность модель угадывает в 94 % случаев, а тему — около 79 %. В чём главная причина разрыва?

- [x] В смешанных отзывах две темы, а разметчик выбрал одну: модель «одна тема на отзыв» упирается в постановку задачи
  > Поэтому честнее размечать все темы отзыва (multi-label), а не пытаться выжать из той же разметки ещё несколько процентов.
- [ ] Логистическая регрессия плохо работает больше чем с двумя классами
  > Для нескольких классов она сама учит набор весов на каждый класс — это обычный режим работы.
- [ ] TF-IDF не подходит для тем, нужны другие признаки
  > Векторайзер тот же, что и для тональности. Ошибки видны в матрице: модель чаще всего отвечает «кофе» там, где отзыв про две темы сразу.
- [ ] Модели не хватает отзывов про кофе
  > Ошибки идут в обратную сторону: модель слишком часто отвечает «кофе», а не пропускает его.
:::

{{practice: topics}}

## Практика

## task: pipe | Конвейер тональности | warmup

Соберите конвейер `make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))`, обучите на обучающей части и сохраните `acc`, `f1` на тесте (3 знака) и `preds` — прогнозы для трёх новых отзывов из заготовки (список 0/1).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
new = ["Бариста грубил, кофе холодный", "Всё понравилось, спасибо", "Вкусно, но очень долго ждали"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import accuracy_score as _acc, f1_score as _f1
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
m = _mp(_TF(), _LR(max_iter=1000)).fit(a, c); p = m.predict(b)
assert close(need('acc'), round(_acc(d, p), 3), 0.002) and close(need('f1'), round(_f1(d, p), 3), 0.002), f'acc, f1 = {need("acc")}, {need("f1")}.'
w = [int(v) for v in m.predict(['Бариста грубил, кофе холодный', 'Всё понравилось, спасибо', 'Вкусно, но очень долго ждали'])]
assert [int(v) for v in need('preds')] == w, f'preds = {need("preds")}, а нужно {w}.'
```

### hint
Конвейер обучается одной строкой: `model = make_pipeline(...).fit(X_train, y_train)`; доля верных — `accuracy_score(y_test, model.predict(X_test))`.

### hint
`model.predict(new)` принимает список строк; `.tolist()` превратит ответ в обычный список.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
new = ["Бариста грубил, кофе холодный", "Всё понравилось, спасибо", "Вкусно, но очень долго ждали"]

model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)
acc = round(accuracy_score(y_test, pred), 3)
f1 = round(f1_score(y_test, pred), 3)
preds = [int(v) for v in model.predict(new)]
```

## task: p-nb | Наивный Байес | warmup

Соберите конвейер наивного Байеса и напечатайте долю правильных ответов на тесте (3 знака).

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(CountVectorizer(), MultinomialNB()).fit(X_train, y_train)
print(round(float((model.predict(X_test) == y_test).mean()), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import CountVectorizer as _CV
from sklearn.naive_bayes import MultinomialNB as _NB
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
w = round(float((_mp(_CV(), _NB()).fit(a, c).predict(b) == d).mean()), 3)
assert _lines == [str(w)], f'Сейчас: {_lines}.'
```

### hint
Данные → разбиение → конвейер → печать.

### hint
Наивный Байес работает со счётчиками, поэтому в конвейере `CountVectorizer`, а не `TfidfVectorizer`.

## task: baseline | С чем сравнивать | base

Прежде чем радоваться точности модели, сравните её с базовой. Обучите `DummyClassifier(strategy="most_frequent")` на тех же обучающих текстах и посчитайте на тесте `acc_dummy`, `f1_dummy` (`zero_division=0`) и те же метрики конвейера TF-IDF + логистическая регрессия — `acc_model`, `f1_model` (все — 3 знака). В `share_bad` сохраните долю недовольных во всех отзывах (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TV
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.dummy import DummyClassifier as _D
from sklearn.metrics import accuracy_score as _acc, f1_score as _f1
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
pd_ = _D(strategy='most_frequent').fit(a, c).predict(b); pm = _mp(_TV(), _LR(max_iter=1000)).fit(a, c).predict(b)
for k, v in {'acc_dummy': _acc(d, pd_), 'f1_dummy': _f1(d, pd_, zero_division=0), 'acc_model': _acc(d, pm), 'f1_model': _f1(d, pm), 'share_bad': y0.mean()}.items():
    assert close(need(k), round(v, 3), 0.0011), f'{k} = {need(k)}, а нужно {round(v, 3)}.'
```

### hint
У `DummyClassifier` тот же интерфейс: `fit(X_train, y_train)` и `predict(X_test)` — тексты он даже не читает.

### hint
`f1_score(y_test, pred, zero_division=0)` — у базовой модели нет ни одного ответа «недоволен», и без параметра будет предупреждение.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

dummy = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
pd_ = dummy.predict(X_test)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pm = model.predict(X_test)
acc_dummy = round(accuracy_score(y_test, pd_), 3)
f1_dummy = round(f1_score(y_test, pd_, zero_division=0), 3)
acc_model = round(accuracy_score(y_test, pm), 3)
f1_model = round(f1_score(y_test, pm), 3)
share_bad = round(y.mean(), 3)
```

### explain
Недовольных — 46 %, классы почти сбалансированы, поэтому «всегда доволен» даёт лишь 54 % и F1 = 0. Модель — 94 % и F1 0.94: выигрыш огромный и честный. На оттоке гостей (22 % ушедших) та же базовая модель давала 78 % — поэтому смотреть на долю классов нужно до того, как радоваться accuracy.

## task: top-words | Слова-сигналы | base

Для конвейера из задачи «Конвейер тональности» (обучен в заготовке) сохраните `weights` — Series весов с индексом-словами, `top_bad` — 5 слов с наибольшим весом (по убыванию) и `top_good` — 5 с наименьшим (от самого отрицательного). В `w_ne` — вес слова «не» (2 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
```

### starter
```python
# уже есть: model — конвейер TF-IDF + логистическая регрессия, обученный на тональности
import pandas as pd

```

### check
```python
import pandas as _pd
w0 = _pd.Series(model[-1].coef_[0], index=model[0].get_feature_names_out())
wt = need('weights', _pd.Series)
assert set(wt.index) == set(w0.index), 'Индекс weights — слова get_feature_names_out().'
assert list(need('top_bad')) == list(w0.sort_values(ascending=False).index[:5]), f'top_bad = {need("top_bad")}.'
assert list(need('top_good')) == list(w0.sort_values().index[:5]), f'top_good = {need("top_good")}.'
assert close(need('w_ne'), round(w0['не'], 2), 0.006), f'w_ne = {need("w_ne")}.'
```

### hint
Векторайзер — `model[0]`, регрессия — `model[-1]`.

### hint
`weights = pd.Series(model[-1].coef_[0], index=model[0].get_feature_names_out())`; дальше `sort_values(ascending=False).head(5)` для «плохих» слов и `sort_values().head(5)` для «хороших».

### hint
Вес одного слова — `weights["не"]`.

### solution
```python
import pandas as pd
weights = pd.Series(model[-1].coef_[0], index=model[0].get_feature_names_out())
top_bad = list(weights.sort_values(ascending=False).index[:5])
top_good = list(weights.sort_values().index[:5])
w_ne = round(weights["не"], 2)
```

### explain
У логистической регрессии каждое слово — отдельный вес: положительный тянет к классу «негатив», отрицательный — к «позитиву». Самые «плохие» слова — «но» (6.85) и «не» (4.59): в отзывах «вкусно, но…» и «не понравилось» главное идёт после них. Самые «хорошие» — «спасибо», «ещё», «всем», «10», «вкусный»: «приду ещё», «советую всем», «10 из 10». Такой список — быстрая проверка модели на здравый смысл. Если бы наверху оказались название кофейни или номер заказа, это был бы признак утечки или перекоса в данных.

## task: errors | Ошибки или неверные метки | warmup

Для той же модели найдите ошибки на тесте и разделите их на две группы: «подозрение на неверную метку» — модель уверена (вероятность класса, который она выбрала, больше 0.8), и остальные. Сохраните `n_errors`, `n_confident` и `confident_share` (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
```

### starter
```python
# уже есть: model, X_test, y_test
import numpy as np

```

### check
```python
import numpy as _np
pr = model.predict_proba(X_test); p = pr.argmax(1); err = p != y_test.values
conf = err & (pr.max(1) > 0.8)
assert need('n_errors') == int(err.sum()) and need('n_confident') == int(conf.sum()), f'n_errors, n_confident = {need("n_errors")}, {need("n_confident")}.'
assert close(need('confident_share'), round(conf.sum() / err.sum(), 3), 0.002), f'confident_share = {need("confident_share")}.'
```

### hint
Ошибки — строки теста, где `model.predict(X_test) != y_test`.

### hint
`proba = model.predict_proba(X_test)`; уверенность в выбранном классе — `proba.max(axis=1)`.

### hint
«Уверенная ошибка» — ошибка, где уверенность больше порога из условия: `(conf[wrong] > порог).sum()`.

### solution
```python
import numpy as np
proba = model.predict_proba(X_test)
pred = proba.argmax(axis=1)
errors = pred != y_test.values
confident = errors & (proba.max(axis=1) > 0.8)
n_errors = int(errors.sum())
n_confident = int(confident.sum())
confident_share = round(n_confident / n_errors, 3)
```

### explain
Большая часть ошибок — уверенные: текст однозначно хвалит или ругает, а оценка противоположная. Это кандидаты на исправление разметки: их можно показать модератору. На практике так и чистят данные — «модель против метки», а спорные случаи решает человек.

## task: unsure | Где модель сомневается | base

Для конвейера тональности (обучен в заготовке) посчитайте вероятности недовольства на тесте `p`. Разделите тестовые отзывы на «уверенные» (`p < 0.2` или `p > 0.8`) и «сомнительные» (остальные). Сохраните `share_unsure` — долю сомнительных (3 знака), `acc_sure` и `acc_unsure` — долю верных ответов (по порогу 0.5) в каждой группе (3 знака), и `unsure_examples` — тексты трёх сомнительных отзывов с вероятностью, ближайшей к 0.5.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
```

### starter
```python
import numpy as np
import pandas as pd

p = model.predict_proba(X_test)[:, 1]

```

### check
```python
import numpy as _np
m, Xt, yt = need('model'), need('X_test'), need('y_test')
p = m.predict_proba(Xt)[:, 1]
uns = (p >= 0.2) & (p <= 0.8)
ok = (p >= 0.5).astype(int) == yt.values
assert close(need('share_unsure'), round(float(uns.mean()), 3), 0.0011), f'share_unsure = {need("share_unsure")}.'
assert close(need('acc_sure'), round(float(ok[~uns].mean()), 3), 0.0011), f'acc_sure = {need("acc_sure")}.'
assert close(need('acc_unsure'), round(float(ok[uns].mean()), 3), 0.0011), f'acc_unsure = {need("acc_unsure")}.'
idx = _np.argsort(_np.abs(p - 0.5), kind='stable')[:3]
assert list(need('unsure_examples')) == list(Xt.values[idx]), 'unsure_examples — три текста с вероятностью ближе всего к 0.5.'
```

### hint
Маска сомнительных: `unsure = (p >= 0.2) & (p <= 0.8)`; верность ответа — `(p >= 0.5).astype(int) == y_test.values`.

### hint
Доля верных в группе — среднее маски верности по нужным строкам: `ok[unsure].mean()` и `ok[~unsure].mean()`.

### hint
Ближайшие к 0.5: `idx = np.argsort(np.abs(p - 0.5), kind="stable")[:3]`, тексты — `X_test.values[idx]`.

### solution
```python
import numpy as np
import pandas as pd

p = model.predict_proba(X_test)[:, 1]
unsure = (p >= 0.2) & (p <= 0.8)
ok = (p >= 0.5).astype(int) == y_test.values
share_unsure = round(float(unsure.mean()), 3)
acc_sure = round(float(ok[~unsure].mean()), 3)
acc_unsure = round(float(ok[unsure].mean()), 3)
idx = np.argsort(np.abs(p - 0.5), kind="stable")[:3]
unsure_examples = list(X_test.values[idx])
print(share_unsure, acc_sure, acc_unsure, *unsure_examples, sep="\n")
```

### explain
Неожиданный результат: среди «уверенных» ответов модель ошибается не реже, чем среди сомнительных (около 94 % и 95 % верных). Причина — шум разметки: если гость промахнулся звёздочкой, текст однозначно хороший, модель уверенно говорит «доволен», а метка — «недоволен». Такие уверенные «ошибки» на самом деле ошибки данных (задача «Ошибки или неверные метки»). А сомнительные отзывы — это короткие тексты без сильных слов («Чисто исветло.», «Зашёл утром перед работой. Красивый интерьер.») и смешанные, где «но» потерялось в опечатке («Хорошие скидки по карте, о бариста грубил»): их стоит отдавать человеку. В работе часто делают именно так: уверенные ответы — автоматически, сомнительные (здесь каждый пятый) — на ручной разбор.

## task: recall95 | Не пропустить жалобу | plus

Отдел заботы о гостях хочет видеть почти все жалобы: полнота класса «недоволен» на тесте — не ниже 0.95. Для конвейера тональности (обучен в заготовке) найдите наибольший порог `thr` из сетки `np.arange(0.05, 0.96, 0.01)`, при котором полнота ≥ 0.95 (округлите до 2 знаков). Сохраните `precision_at` — точность при этом пороге (3 знака), `n_flagged` — сколько тестовых отзывов отправится на разбор и `precision_05`, `recall_05` — точность и полноту при пороге 0.5 (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
```

### starter
```python
import numpy as np
from sklearn.metrics import precision_score, recall_score

p = model.predict_proba(X_test)[:, 1]

```

### check
```python
import numpy as _np
from sklearn.metrics import precision_score as _ps, recall_score as _rs
m, Xt, yt = need('model'), need('X_test'), need('y_test')
p = m.predict_proba(Xt)[:, 1]
ok = [t for t in _np.arange(0.05, 0.96, 0.01) if _rs(yt, (p >= t).astype(int)) >= 0.95]
t = max(ok)
assert close(need('thr'), round(t, 2), 0.0051), f'thr = {need("thr")}, а нужно {round(t, 2)}.'
assert close(need('precision_at'), round(_ps(yt, (p >= t).astype(int)), 3), 0.0011), f'precision_at = {need("precision_at")}.'
assert need('n_flagged') == int((p >= t).sum()), f'n_flagged = {need("n_flagged")}.'
assert close(need('precision_05'), round(_ps(yt, (p >= 0.5).astype(int)), 3), 0.0011) and close(need('recall_05'), round(_rs(yt, (p >= 0.5).astype(int)), 3), 0.0011), 'precision_05, recall_05 — при пороге 0.5.'
```

### hint
Перебор: для каждого порога `t` из сетки — `recall_score(y_test, (p >= t).astype(int))`. Оставьте пороги с полнотой ≥ 0.95 и возьмите наибольший.

### hint
Чем ниже порог, тем больше отзывов помечено и тем выше полнота. Поэтому «наибольший порог с полнотой ≥ 0.95» даёт максимально короткий список при нужной полноте.

### hint
```python
good = [t for t in np.arange(0.05, 0.96, 0.01) if recall_score(y_test, (p >= t).astype(int)) >= 0.95]
thr = round(max(good), 2)
```

### solution
```python
import numpy as np
from sklearn.metrics import precision_score, recall_score

p = model.predict_proba(X_test)[:, 1]
good = [t for t in np.arange(0.05, 0.96, 0.01) if recall_score(y_test, (p >= t).astype(int)) >= 0.95]
t = max(good)
thr = round(t, 2)
pred_t = (p >= t).astype(int)
precision_at = round(precision_score(y_test, pred_t), 3)
n_flagged = int(pred_t.sum())
pred_05 = (p >= 0.5).astype(int)
precision_05 = round(precision_score(y_test, pred_05), 3)
recall_05 = round(recall_score(y_test, pred_05), 3)
print(thr, precision_at, n_flagged, precision_05, recall_05)
```

### explain
При пороге 0.5 модель находит около 92 % жалоб, и 96 % найденного — действительно жалобы. Чтобы поймать 95 %, порог приходится опустить до 0.11 — и точность падает до 0.60: на разбор уходит 438 отзывов из 600 тестовых, из них почти 40 % — довольные гости. Последние проценты полноты стоят дорого, потому что оставшиеся жалобы — это неверные метки и смешанные отзывы, похожие на хорошие. Требование «не ниже 0.95» стоит обсудить с заказчиком, показав эту цену.

## task: topics | Темы | plus

Обучите конвейер на темах (`r["topic"]`, разбиение со `stratify` по теме). Сохраните `acc_topic` (3 знака), `cm` — `pd.crosstab(y_test, pred)` и `worst_topic` — тему с наименьшей полнотой (доля правильно найденных отзывов этой темы).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
X_train, X_test, y_train, y_test = train_test_split(r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.linear_model import LogisticRegression as _LR
r0 = _pd.read_csv('reviews_text.csv'); a, b, c, d = _tts(r0['text'], r0['topic'], test_size=0.25, random_state=42, stratify=r0['topic'])
p = _mp(_TF(), _LR(max_iter=1000)).fit(a, c).predict(b)
assert close(need('acc_topic'), round((p == d).mean(), 3), 0.002), f'acc_topic = {need("acc_topic")}.'
rec = _pd.Series({t: (p[d.values == t] == t).mean() for t in d.unique()})
assert need('worst_topic') == rec.idxmin(), f'worst_topic = {need("worst_topic")!r}, а нужно {rec.idxmin()!r}.'
assert need('cm', _pd.DataFrame).values.sum() == len(d), 'cm — crosstab настоящих тем и прогнозов.'
```

### hint
Матрица ошибок с подписями — `pd.crosstab(y_test, pred)`.

### hint
Полнота темы t: среди отзывов с настоящей темой t — доля, где модель сказала t. Удобно из `cm`: диагональ / сумма строки.

### hint
`recall = pd.Series(np.diag(cm.values) / cm.values.sum(axis=1), index=cm.index)`; худшая тема — `recall.idxmin()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
X_train, X_test, y_train, y_test = train_test_split(r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])

model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)
acc_topic = round((pred == y_test).mean(), 3)
cm = pd.crosstab(y_test, pred)
recall = pd.Series({t: cm.loc[t, t] / cm.loc[t].sum() for t in cm.index})
worst_topic = recall.idxmin()
```

### explain
Хуже всего модель находит «атмосферу»: отзывов этой темы мало, а в смешанных отзывах про атмосферу почти всегда упоминается и что-то ещё. Редкие классы и размытые границы между ними — частая беда классификации тем.

## task: compare | Сравнение векторайзеров | star

Сравните на тональности кросс-валидацией (`cross_val_score`, `cv=5`, `scoring="f1"`, на обучающей части) четыре конвейера: TF-IDF слов + логрегрессия; TF-IDF слов и биграмм + логрегрессия; символьные n-граммы `TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))` + логрегрессия; `CountVectorizer` + `MultinomialNB`. Сохраните словарь `cv_f1` с ключами `"words"`, `"bigrams"`, `"chars"`, `"nb"` (средние, 3 знака) и `best`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, cross_val_score as _cvs
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TF, CountVectorizer as _CV
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.naive_bayes import MultinomialNB as _NB
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
ms = {'words': _mp(_TF(), _LR(max_iter=1000)), 'bigrams': _mp(_TF(ngram_range=(1, 2)), _LR(max_iter=1000)),
      'chars': _mp(_TF(analyzer='char_wb', ngram_range=(2, 4)), _LR(max_iter=1000)), 'nb': _mp(_CV(), _NB())}
w = {k: round(_cvs(m, a, c, cv=5, scoring='f1').mean(), 3) for k, m in ms.items()}
got = need('cv_f1', dict)
assert all(k in got and close(got[k], v, 0.002) for k, v in w.items()), f'cv_f1 = {got}, а нужно {w}.'
top = max(w.values()); ok_best = sorted(k for k, v in w.items() if v == top)
assert need('best') in ok_best, f'best = {need("best")!r}, а подходит {" или ".join(ok_best)} — у них наибольшее среднее F1 после округления.'
```

### hint
Четыре конвейера удобно положить в словарь `{"words": ..., "bigrams": ..., "chars": ..., "nb": ...}`.

### hint
Словарь конвейеров и цикл с `cross_val_score(model, X_train, y_train, cv=5, scoring="f1").mean()`.

### hint
`best = max(cv_f1, key=cv_f1.get)` — ключ с наибольшим значением.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

models = {
    "words": make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)),
    "bigrams": make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)),
    "chars": make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)), LogisticRegression(max_iter=1000)),
    "nb": make_pipeline(CountVectorizer(), MultinomialNB()),
}
cv_f1 = {k: round(cross_val_score(m, X_train, y_train, cv=5, scoring="f1").mean(), 3) for k, m in models.items()}
best = max(cv_f1, key=cv_f1.get)
```

### explain
Все четыре подхода в пределах процента, а слова и биграммы после округления сравнялись (0.941) — годится любой из двух ключей: на коротких однотипных отзывах качество упирается в шум разметки, а не в представление текста. На длинных и разнообразных текстах разница между ними больше — и там же впереди окажутся эмбеддинги (урок «Эмбеддинги: векторы слов и отзывов»).
