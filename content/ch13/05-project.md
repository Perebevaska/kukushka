---
title: "Проект: о чём жалуются гости"
files: [reviews_text.csv, reviews_new.csv]
lead: "Финал главы. С сентября сеть собирает отзывы с карт — без оценок и без тем, просто тексты. Управляющая хочет каждую неделю видеть, где гости стали недовольнее и почему. Обучаем две модели на размеченных отзывах, размечаем ими новые, находим кофейню, где что-то сломалось, и причину — и поправляем долю негатива на ошибки самой модели."
recap:
  - "Модель для разметки обучают на старых размеченных данных и честно оценивают на отложенной части; для работы её переобучают на всех данных."
  - "Для многоклассовой модели смотрят F1 по каждому классу и macro-F1: доля правильных прячет провал на редкой теме. Если модель недосчитывает редкий класс, счётчики по темам в отчёте занижены; `class_weight=\"balanced\"` поднимает полноту редкого класса ценой общей точности."
  - "Перенос на новый источник — риск: тексты могут отличаться. Перед выводами читают примеры и смотрят, правдоподобна ли разметка."
  - "Сравнивают «до» и «после», а не только уровень: самая недовольная точка и точка, где стало хуже, — разные вопросы."
  - "Причину ищут в разрезе: структура жалоб по темам до и после и сравнение с остальными точками."
  - "Доля по модели смещена её ошибками. Зная полноту (TPR) и долю ложных срабатываний (FPR), долю исправляют: (p − FPR) / (TPR − FPR)."
  - "Цитаты из отзывов убеждают руководителя лучше процентов — давайте и то и другое."
---

## Задача

> С сентября собираем отзывы о наших кофейнях с онлайн-карт: файл `reviews_new.csv`, около 4800 отзывов за сентябрь и октябрь. Оценок там нет, тем тоже — только текст, дата и точка. Читать всё вручную некому.
>
> Хочу понимать: в какой кофейне гости стали недовольнее, чем раньше, с какой недели и на что жалуются. Подкрепите выводы цитатами — их я перешлю управляющим точек.
>
> *Управляющая сетью*

## План

1. Две модели на размеченных `reviews_text.csv`: тональность (`rating <= 3` — недоволен) и тема. Оценка на отложенной части, затем переобучение на всех данных.
   Для темы — не только доля правильных, но и F1 по каждой теме: в отчёте будут счётчики по темам, и редкая тема не должна теряться.
2. Разметка новых отзывов: вероятность недовольства, флаг, тема, период — до и после 5 октября (понедельник: сравниваем целые недели; частей поровну не будет — после 5 октября меньше половины отзывов).
3. Доля недовольных по точкам: уровень и рост.
4. Причина: темы жалоб в проблемной точке до и после, сравнение с остальными, цитаты.
5. С какой недели: понедельная динамика.
6. Поправка доли на ошибки модели.

Обе модели — TF-IDF слов и биграмм + логистическая регрессия (урок «Классификация текстов»).

::: figure reviews-project-flow
Шаги проекта: модели учатся на размеченных отзывах, размечают новые, а дальше — сравнение точек до и после, причина и поправка доли на ошибки модели.
:::

Как работает поправка из шага 6, проще увидеть на игрушечных числах: пусть по-настоящему недовольны 10 % гостей, модель ловит 90 % из них (TPR) и ошибочно называет недовольными 5 % довольных (FPR).

::: figure share-adjust
Игрушечный пример поправки: модель видит 13.5 % «недовольных» вместо настоящих 10 % — ложные срабатывания на большой группе довольных перевешивают пропуски. Формула возвращает 10 %.
:::

::: quiz
Доля негативных отзывов в кофейне выросла с 10 % до 14 %, но классификатор ошибается. Как честно сказать о росте?

- [x] Поправить доли на известные ошибки модели — тогда видно, реальный ли это рост
  > Сырые доли от модели смещены: часть «негатива» — ложные срабатывания, часть пропущена.
- [ ] Сообщить «рост на 4 п.п.» без оговорок
  > Цифра может быть артефактом ошибок модели.
- [ ] Не сообщать ничего, пока модель не станет идеальной
  > Идеальной она не станет. Важно учесть ошибки, а не ждать.
- [ ] Посчитать долю вручную по всем отзывам
  > Идеально, но дорого. Поправка на ошибки модели — разумный компромисс.
:::

## task: models | Шаг 1. Две модели | base

Оцените на отложенной четверти (`train_test_split(..., test_size=0.25, random_state=42, stratify=...)`) две модели вида `make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))`: тональность (цель `(rating <= 3).astype(int)`) и тему (цель `topic`). Сохраните `acc_sent` и `acc_topic` — доли правильных на тесте (3 знака). Затем обучите такие же модели **на всех** 2400 отзывах: `sent` и `topic_model`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

def new_model():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.linear_model import LogisticRegression as _LR
_m = lambda: _mp(_TF(ngram_range=(1, 2)), _LR(max_iter=1000))
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
w1 = round(float((_m().fit(a, c).predict(b) == d).mean()), 3)
a, b, c, d = _tts(r0['text'], r0['topic'], test_size=0.25, random_state=42, stratify=r0['topic'])
w2 = round(float((_m().fit(a, c).predict(b) == d).mean()), 3)
assert close(need('acc_sent'), w1, 0.002), f'acc_sent = {need("acc_sent")}, а нужно {w1}.'
assert close(need('acc_topic'), w2, 0.002), f'acc_topic = {need("acc_topic")}, а нужно {w2}.'
s, t = need('sent'), need('topic_model')
n0 = _pd.read_csv('reviews_new.csv')['text']
ref_s = _m().fit(r0['text'], y0).predict(n0)
ref_t = _m().fit(r0['text'], r0['topic']).predict(n0)
assert (s.predict(n0) == ref_s).mean() > 0.99, 'sent должна быть обучена на всех 2400 отзывах.'
assert (t.predict(n0) == ref_t).mean() > 0.99, 'topic_model должна быть обучена на всех 2400 отзывах.'
```

### hint
Функция `new_model()` возвращает каждый раз новый, необученный конвейер — используйте её для всех четырёх моделей (две оценочные и две финальные).

### hint
Два разбиения: для тональности `stratify=y`, для темы `stratify=r["topic"]`. Финальные модели: `new_model().fit(r["text"], y)` и `new_model().fit(r["text"], r["topic"])`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

def new_model():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))

X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
acc_sent = round(accuracy_score(y_test, new_model().fit(X_train, y_train).predict(X_test)), 3)

X_train, X_test, t_train, t_test = train_test_split(r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])
acc_topic = round(accuracy_score(t_test, new_model().fit(X_train, t_train).predict(X_test)), 3)

sent = new_model().fit(r["text"], y)
topic_model = new_model().fit(r["text"], r["topic"])
print(acc_sent, acc_topic)
```

### explain
Тональность — около 94 %, тема — около 82 %. В уроке «Классификация текстов» модель тем давала 79 %: здесь к словам добавлены биграммы (`ngram_range=(1, 2)`), и это подняло тему на 3 п. п.; тональность почти не изменилась. Темы хуже, и это надо помнить при выводах: каждый пятый отзыв попадёт не в свою тему. Финальные модели обучены на всех данных — оценка на отложенной части остаётся честной оценкой их качества (чуть пессимистичной: данных при обучении стало больше).

## task: rare | Шаг 1б. Редкая тема: F1 вместо доли правильных | plus

Доля правильных у модели тем — около 82 %, но в отчёте управляющей будут **счётчики по темам**, и важна каждая тема, в том числе редкая. Доля правильных усредняет по отзывам: частая тема «кофе» тянет её вверх, а провал на редкой теме почти не виден. Поэтому смотрят F1 по каждому классу и **macro-F1** — простое среднее F1 по классам, где редкая тема весит столько же, сколько частая.

На том же разбиении, что в шаге 1 (тема, `stratify=r["topic"]`), обучите модель `new_model()` и сохраните:

- `f1_by_topic` — словарь «тема → F1 на тесте» (3 знака), `macro_f1` (3 знака);
- `rarest` — тему, которой меньше всего в тесте, и `worst` — тему с наименьшим F1;
- `count_ratio` — во сколько раз модель недосчитывает редчайшую тему: число отзывов, которые модель **назвала** этой темой, делённое на настоящее число в тесте (3 знака);
- `f1_rare_balanced` — F1 редчайшей темы у той же модели с `LogisticRegression(max_iter=1000, class_weight="balanced")` (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

r = pd.read_csv("reviews_text.csv")

def new_model(class_weight=None):
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2)),
                         LogisticRegression(max_iter=1000, class_weight=class_weight))

X_train, X_test, t_train, t_test = train_test_split(
    r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _TF
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import f1_score as _f1
r0 = _pd.read_csv('reviews_text.csv')
a, b, c, d = _tts(r0['text'], r0['topic'], test_size=0.25, random_state=42, stratify=r0['topic'])
p = _mp(_TF(ngram_range=(1, 2)), _LR(max_iter=1000)).fit(a, c).predict(b)
labs = sorted(r0['topic'].unique())
f = dict(zip(labs, [round(float(v), 3) for v in _f1(d, p, average=None, labels=labs)]))
got = need('f1_by_topic', dict)
assert all(k in got and close(got[k], v, 0.0015) for k, v in f.items()), f'f1_by_topic = {got}, а нужно {f}. f1_score(..., average=None, labels=...) возвращает F1 по каждому классу в порядке labels.'
assert close(need('macro_f1'), round(float(_f1(d, p, average="macro")), 3), 0.0015), f'macro_f1 = {need("macro_f1")}.'
rare = d.value_counts().idxmin()
assert need('rarest') == rare, f'rarest = {need("rarest")!r}. Считайте по тесту: t_test.value_counts().'
assert need('worst') == min(f, key=f.get), f'worst = {need("worst")!r}.'
cr = round(float((p == rare).sum() / (d == rare).sum()), 3)
assert close(need('count_ratio'), cr, 0.0015), f'count_ratio = {need("count_ratio")}, а нужно {cr}: (pred == тема).sum() / (t_test == тема).sum().'
pb = _mp(_TF(ngram_range=(1, 2)), _LR(max_iter=1000, class_weight='balanced')).fit(a, c).predict(b)
fb = round(float(_f1(d, pb, labels=[rare], average=None)[0]), 3)
assert close(need('f1_rare_balanced'), fb, 0.0015), f'f1_rare_balanced = {need("f1_rare_balanced")}, а нужно {fb}.'
```

### hint
F1 по каждой теме сразу — `f1_score(t_test, pred, average=None, labels=labels)`, где `labels = sorted(r["topic"].unique())`; результат — массив в том же порядке, что `labels`. Macro-F1 — `average="macro"`.

### hint
Редчайшая тема — `t_test.value_counts().idxmin()`, худшая по F1 — `min(f1_by_topic, key=f1_by_topic.get)`. Сколько раз модель назвала тему: `(pred == rarest).sum()`.

### hint
```python
pred = new_model().fit(X_train, t_train).predict(X_test)
labels = sorted(r["topic"].unique())
f1_by_topic = {k: round(float(v), 3) for k, v in zip(labels, f1_score(t_test, pred, average=None, labels=labels))}
...
pred_b = new_model("balanced").fit(X_train, t_train).predict(X_test)
f1_rare_balanced = round(float(f1_score(t_test, pred_b, labels=[rarest], average=None)[0]), 3)
```

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

r = pd.read_csv("reviews_text.csv")

def new_model(class_weight=None):
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2)),
                         LogisticRegression(max_iter=1000, class_weight=class_weight))

X_train, X_test, t_train, t_test = train_test_split(
    r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])

pred = new_model().fit(X_train, t_train).predict(X_test)
labels = sorted(r["topic"].unique())
f1_by_topic = {k: round(float(v), 3) for k, v in zip(labels, f1_score(t_test, pred, average=None, labels=labels))}
macro_f1 = round(float(f1_score(t_test, pred, average="macro")), 3)
rarest = t_test.value_counts().idxmin()
worst = min(f1_by_topic, key=f1_by_topic.get)
count_ratio = round(float((pred == rarest).sum() / (t_test == rarest).sum()), 3)

pred_b = new_model("balanced").fit(X_train, t_train).predict(X_test)
f1_rare_balanced = round(float(f1_score(t_test, pred_b, labels=[rarest], average=None)[0]), 3)
print(f1_by_topic, macro_f1, rarest, worst, count_ratio, f1_rare_balanced)
```

### explain
Самая редкая тема — «атмосфера» (58 отзывов в тесте), и у неё же худший F1 — около 0.74 против 0.89 у «кофе». Macro-F1 около 0.79 — ниже доли правильных 0.82: среднее по классам честнее показывает слабые места. Главное для отчёта — `count_ratio` около 0.69: модель редко ошибается, когда говорит «атмосфера» (точность 0.90), но пропускает почти 40 % таких отзывов, и в счётчиках по темам атмосфера окажется занижена почти на треть. С `class_weight="balanced"` ошибка на редком классе стоит дороже, полнота «атмосферы» растёт до 0.76, F1 — до 0.76, а общая доля правильных падает до 0.81: модель жертвует частым «кофе». Какую модель брать, зависит от вопроса: для **счётчиков по темам** важнее не занижать редкие темы, для **одного прогноза на отзыв** — общая точность. Ошибка, которую легко сделать: смотреть `average="weighted"` — оно взвешивает по числу отзывов и почти совпадает с долей правильных, то есть прячет ту же проблему.

## task: score | Шаг 2. Разметка новых отзывов | base

Модели `sent` и `topic_model` обучены в заготовке. Загрузите `reviews_new.csv` в `n` (дата — `datetime`) и добавьте колонки: `p_neg` — вероятность недовольства, `neg` — 1, если `p_neg >= 0.5`, иначе 0, `topic` — предсказанная тема, `period` — `"после"` для дат с 2026-10-05 включительно и `"до"` для остальных. Сохраните `n_after` — число отзывов в периоде «после».

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
_r = pd.read_csv("reviews_text.csv")
sent = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], (_r["rating"] <= 3).astype(int))
topic_model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], _r["topic"])
```

### starter
```python
import numpy as np
import pandas as pd

n = pd.read_csv("reviews_new.csv", parse_dates=["date"])

```

### check
```python
import numpy as _np
import pandas as _pd
n = need('n', _pd.DataFrame)
n0 = _pd.read_csv('reviews_new.csv', parse_dates=['date'])
assert len(n) == len(n0), f'Строк {len(n)}, а в файле {len(n0)}.'
assert _pd.api.types.is_datetime64_any_dtype(n['date']), 'Колонка date должна быть датой: parse_dates=["date"].'
p = need('sent').predict_proba(n0['text'])[:, 1]
assert _np.allclose(n['p_neg'].values, p, atol=1e-6), 'p_neg — вторая колонка predict_proba.'
assert (n['neg'].astype(int).values == (p >= 0.5).astype(int)).all(), 'neg = (p_neg >= 0.5).'
assert (n['topic'].values == need('topic_model').predict(n0['text'])).all(), 'topic — предсказание topic_model.'
want = _np.where(n0['date'] >= '2026-10-05', 'после', 'до')
assert (n['period'].values == want).all(), 'period: «после» — с 2026-10-05 включительно.'
assert need('n_after') == int((want == 'после').sum()), f'n_after = {need("n_after")}.'
```

### hint
Модели уже обучены — здесь только применение: `predict_proba` для вероятности, `predict` для темы.

### hint
`sent.predict_proba(n["text"])[:, 1]`; `np.where(n["date"] >= "2026-10-05", "после", "до")`.

### solution
```python
import numpy as np
import pandas as pd

n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
n["topic"] = topic_model.predict(n["text"])
n["period"] = np.where(n["date"] >= "2026-10-05", "после", "до")
n_after = int((n["period"] == "после").sum())
print(n.sample(5, random_state=1)[["text", "p_neg", "topic"]])
```

### explain
Перед любыми выводами стоит прочитать пару десятков размеченных строк: новые отзывы пришли из другого источника, и если бы там писали иначе (длиннее, с жаргоном, на другие темы), модель могла бы тихо ошибаться. Здесь тексты похожи на обучающие — разметке можно доверять примерно настолько, насколько показал шаг 1.

## task: shops | Шаг 3. Уровень и рост | base

Посчитайте по точкам долю недовольных (`neg`) до и после 5 октября. Сохраните `by_shop` — DataFrame с индексом `shop_id` и колонками `до`, `после`, `рост` (`после − до`), все — 3 знака, отсортированный по `рост` по убыванию. В `worst_level` — точку с наибольшей долей «после», в `worst_growth` — с наибольшим ростом.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
_r = pd.read_csv("reviews_text.csv")
sent = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], (_r["rating"] <= 3).astype(int))
topic_model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], _r["topic"])
n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
n["topic"] = topic_model.predict(n["text"])
n["period"] = np.where(n["date"] >= "2026-10-05", "после", "до")
```

### starter
```python
by_shop = ...
```

### check
```python
import pandas as _pd
n0 = need('n', _pd.DataFrame)
w = n0.groupby(['shop_id', 'period'])['neg'].mean().unstack()[['до', 'после']]
w['рост'] = w['после'] - w['до']
w = w.round(3).sort_values('рост', ascending=False)
b = need('by_shop', _pd.DataFrame)
assert list(b.columns) == ['до', 'после', 'рост'], f'Колонки: {list(b.columns)}.'
assert list(b.index) == list(w.index), f'Порядок точек: {list(b.index)}, а нужно {list(w.index)}.'
assert ((b - w).abs() < 0.0015).all().all(), 'Значения долей не совпадают.'
assert need('worst_level') == w['после'].idxmax(), f'worst_level = {need("worst_level")!r}.'
assert need('worst_growth') == w['рост'].idxmax(), f'worst_growth = {need("worst_growth")!r}.'
```

### hint
`n.groupby(["shop_id", "period"])["neg"].mean().unstack()` даст таблицу точки × периоды.

### hint
Рост — новый столбец `после − до`; сортировка — `.sort_values("рост", ascending=False)`; лидеры — `.idxmax()` по нужному столбцу.

### solution
```python
by_shop = n.groupby(["shop_id", "period"])["neg"].mean().unstack()[["до", "после"]]
by_shop["рост"] = by_shop["после"] - by_shop["до"]
by_shop = by_shop.round(3).sort_values("рост", ascending=False)
worst_level = by_shop["после"].idxmax()
worst_growth = by_shop["рост"].idxmax()
print(by_shop, worst_level, worst_growth)
```

### explain
Самая недовольная точка — TMN-1, но она такая весь период: около 56 % недовольных ещё в сентябре. А в KZN-2 доля выросла с ~37 % до ~60 % — это и есть «стало хуже». Если смотреть только на уровень, управляющая поедет разбираться не туда. В остальных точках изменения до 6–7 п. п. При ~400 отзывах на период стандартная ошибка разницы двух долей — около 3.5 п. п.: рост на 6 п. п. — на грани случайности, на 23 — точно нет.

## task: why | Шаг 4. Почему и цитаты | plus

Таблица `n` размечена в заготовке. Для недовольных отзывов KZN-2 посчитайте структуру тем до и после: `kzn` — `pd.crosstab(topic, period, normalize="columns")`. То же для недовольных отзывов остальных пяти точек — `others`. Сохраните `cause` — тему, доля которой в жалобах KZN-2 выросла сильнее всего, и `quotes` — список из пяти текстов: недовольные отзывы KZN-2 «после» с темой `cause` и наибольшей `p_neg` (по убыванию).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
_r = pd.read_csv("reviews_text.csv")
sent = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], (_r["rating"] <= 3).astype(int))
topic_model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], _r["topic"])
n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
n["topic"] = topic_model.predict(n["text"])
n["period"] = np.where(n["date"] >= "2026-10-05", "после", "до")
```

### starter
```python
bad = n[n["neg"] == 1]

```

### check
```python
import pandas as _pd
n0 = need('n', _pd.DataFrame); bad = n0[n0['neg'] == 1]
k0 = bad[bad['shop_id'] == 'KZN-2']; o0 = bad[bad['shop_id'] != 'KZN-2']
kw = _pd.crosstab(k0['topic'], k0['period'], normalize='columns')
ow = _pd.crosstab(o0['topic'], o0['period'], normalize='columns')
k, o = need('kzn', _pd.DataFrame), need('others', _pd.DataFrame)
assert ((k[['до', 'после']] - kw[['до', 'после']]).abs() < 1e-6).all().all(), 'kzn не совпадает: только недовольные отзывы KZN-2, normalize="columns".'
assert ((o[['до', 'после']] - ow[['до', 'после']]).abs() < 1e-6).all().all(), 'others не совпадает: недовольные отзывы остальных точек.'
c = (kw['после'] - kw['до']).idxmax()
assert need('cause') == c, f'cause = {need("cause")!r}.'
qw = k0[(k0['period'] == 'после') & (k0['topic'] == c)].sort_values('p_neg', ascending=False)['text'].head(5).tolist()
assert need('quotes', list) == qw, 'quotes: пять текстов с наибольшей p_neg, по убыванию.'
```

### hint
Сначала только недовольные: `bad = n[n["neg"] == 1]`, затем две части — `bad[bad["shop_id"] == "KZN-2"]` и остальные.

### hint
Фильтр по точке и `pd.crosstab(...)`; `cause = (kzn["после"] - kzn["до"]).idxmax()`. Для цитат — фильтр по периоду и теме, `.sort_values("p_neg", ascending=False)`, `.head(5)`.

### solution
```python
bad = n[n["neg"] == 1]
kb = bad[bad["shop_id"] == "KZN-2"]
ob = bad[bad["shop_id"] != "KZN-2"]
kzn = pd.crosstab(kb["topic"], kb["period"], normalize="columns")
others = pd.crosstab(ob["topic"], ob["period"], normalize="columns")
cause = (kzn["после"] - kzn["до"]).idxmax()
quotes = (kb[(kb["period"] == "после") & (kb["topic"] == cause)]
          .sort_values("p_neg", ascending=False)["text"].head(5).tolist())
print(kzn.round(2), others.round(2), cause, *quotes, sep="\n")
```

### explain
В KZN-2 доставка была четвертью жалоб, а стала больше половины; в остальных точках её доля не изменилась (~17 %). Значит, причина местная — что-то случилось с доставкой именно в этой кофейне, а не с меню или ценами по сети. Цитаты — про курьеров, которые не могут найти адрес, пролитый кофе и перепутанные заказы: управляющей точки этого достаточно, чтобы начать разбор.

## task: weekly | Шаг 5. С какой недели | plus

Таблица `n` размечена в заготовке. Добавьте `week` — понедельник недели (`n["date"].dt.to_period("W").dt.start_time`). Сохраните `weekly` — сводную таблицу долей недовольных: строки — недели, столбцы — точки. Найдите `jump_week` — неделю (Timestamp), в которую доля KZN-2 выросла сильнее всего по сравнению с предыдущей неделей, и `sept_max` — максимум недельной доли KZN-2 в неделях, начавшихся до 2026-10-01 (3 знака). Нарисуйте доли по неделям и выделите KZN-2 цветом — график не проверяется, но ступеньку на нём видно сразу.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
_r = pd.read_csv("reviews_text.csv")
sent = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], (_r["rating"] <= 3).astype(int))
n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
```

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

```

### check
```python
import pandas as _pd
n0 = need('n', _pd.DataFrame).copy()
n0['week'] = n0['date'].dt.to_period('W').dt.start_time
w = n0.pivot_table(index='week', columns='shop_id', values='neg', aggfunc='mean')
got = need('weekly', _pd.DataFrame)
assert got.shape == w.shape, f'weekly.shape = {got.shape}, а нужно {w.shape}.'
assert ((got[w.columns].values - w.values) ** 2).max() < 1e-12, 'Доли по неделям не совпадают.'
jw = w['KZN-2'].diff().idxmax()
assert _pd.Timestamp(need('jump_week')) == jw, f'jump_week = {need("jump_week")}, а нужно {jw.date()}.'
sm = round(float(w.loc[w.index < '2026-10-01', 'KZN-2'].max()), 3)
assert close(need('sept_max'), sm, 0.0015), f'sept_max = {need("sept_max")}, а нужно {sm}.'
```

### hint
Неделя: `n["date"].dt.to_period("W").dt.start_time` — понедельник недели каждой даты.

### hint
`n.pivot_table(index="week", columns="shop_id", values="neg", aggfunc="mean")`; `weekly["KZN-2"].diff().idxmax()`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

n["week"] = n["date"].dt.to_period("W").dt.start_time
weekly = n.pivot_table(index="week", columns="shop_id", values="neg", aggfunc="mean")
jump_week = weekly["KZN-2"].diff().idxmax()
sept_max = round(float(weekly.loc[weekly.index < "2026-10-01", "KZN-2"].max()), 3)
print(weekly.round(2))
print(jump_week.date(), sept_max)
ax = weekly.plot(figsize=(9, 4), color="lightgray", legend=False)
weekly["KZN-2"].plot(ax=ax, color="crimson", lw=3, label="KZN-2")
ax.set_ylabel("доля недовольных"); ax.legend()
```

### explain
Скачок — в неделю с 5 октября: с ~0.35 сразу до ~0.60, и обратно доля не возвращается. Все сентябрьские недели KZN-2 держались не выше ~0.43 — новый уровень выше любой из них. Ступенька, а не плавный рост, — признак конкретного события: смена подрядчика, новый курьер, изменение зоны доставки. Это вопрос к управляющей точки.

## task: adjust | Шаг 6. Поправка на ошибки модели | star

Доля «недовольных по модели» — не настоящая доля: модель пропускает часть недовольных и иногда ошибается в другую сторону. Если TPR — доля пойманных недовольных, а FPR — доля довольных, ошибочно названных недовольными, то наблюдаемая доля p = q · TPR + (1 − q) · FPR, откуда настоящая q = (p − FPR) / (TPR − FPR).

Оцените `tpr` и `fpr` на отложенной четверти размеченных данных (разбиение и модель — как в шаге 1, тональность). Затем исправьте доли KZN-2 до и после: `adj` — словарь `{"до": ..., "после": ...}` (3 знака). Таблица `n` размечена в заготовке.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
_r = pd.read_csv("reviews_text.csv")
sent = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(_r["text"], (_r["rating"] <= 3).astype(int))
n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
n["period"] = np.where(n["date"] >= "2026-10-05", "после", "до")
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

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
from sklearn.linear_model import LogisticRegression as _LR
r0 = _pd.read_csv('reviews_text.csv'); y0 = (r0['rating'] <= 3).astype(int)
a, b, c, d = _tts(r0['text'], y0, test_size=0.25, random_state=42, stratify=y0)
p = _mp(_TF(ngram_range=(1, 2)), _LR(max_iter=1000)).fit(a, c).predict(b)
t0 = float(((p == 1) & (d == 1)).sum() / (d == 1).sum()); f0 = float(((p == 1) & (d == 0)).sum() / (d == 0).sum())
assert close(need('tpr'), t0, 0.002), f'tpr = {need("tpr")}, а нужно {t0:.3f}.'
assert close(need('fpr'), f0, 0.002), f'fpr = {need("fpr")}, а нужно {f0:.3f}.'
n0 = need('n', _pd.DataFrame)
obs = n0[n0['shop_id'] == 'KZN-2'].groupby('period')['neg'].mean()
w = {k: round((obs[k] - f0) / (t0 - f0), 3) for k in ['до', 'после']}
got = need('adj', dict)
assert all(close(got[k], w[k], 0.003) for k in w), f'adj = {got}, а нужно {w}.'
```

### hint
TPR и FPR считаются на **старых размеченных** отзывах: обучите модель на обучающей части и предскажите отложенную.

### hint
`tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()`; `tpr = tp / (tp + fn)`, `fpr = fp / (fp + tn)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
pred = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(X_train, y_train).predict(X_test)
tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
tpr, fpr = tp / (tp + fn), fp / (fp + tn)

obs = n[n["shop_id"] == "KZN-2"].groupby("period")["neg"].mean()
adj = {k: round((obs[k] - fpr) / (tpr - fpr), 3) for k in ["до", "после"]}
print(round(tpr, 3), round(fpr, 3), obs.round(3).to_dict(), adj)
```

### explain
Модель ловит около 92 % недовольных и ошибочно метит около 3 % довольных. Поправка поднимает долю «до» примерно на 1 п. п., а «после» — на 4: модель недосчитывает недовольных, и сильнее там, где их больше. Рост в KZN-2 после поправки — около 26 п. п. вместо 23. Вывод от поправки не меняется, но в отчёт идут исправленные цифры. Оговорка: TPR и FPR оценены на старых отзывах; если новый источник отличается, поправка тоже будет неточной. И ещё одна: TPR и FPR посчитаны для модели, обученной на 75 % данных, а размечала отзывы финальная модель на всех данных — она, скорее всего, чуть точнее (данных при обучении больше), поэтому поправка может быть слегка завышена. На вывод о KZN-2 это не влияет: рост больше 20 п. п. и без поправки.

## Итог для управляющей сетью

> **Отзывы с карт, сентябрь–октябрь 2026, ~4800 отзывов, разметка моделью (тональность — 94 % верных, тема — 82 %).**
>
> 1. **KZN-2: резкий рост недовольства с недели 5 октября.** Доля недовольных гостей — около 38 % до 5 октября и около 64 % после (с поправкой на ошибки модели; по модели без поправки — 37 % и 60 %). Рост — ступенькой, не возвращается.
> 2. **Причина — доставка.** Жалобы на доставку в KZN-2 выросли с четверти до больше чем половины всех жалоб точки; в остальных кофейнях их доля не изменилась. Типичные отзывы: курьер не может найти адрес, кофе пролился, привезли не тот заказ (цитаты приложены).
> 3. **TMN-1 — самая недовольная точка весь период:** 56 % недовольных до и 62 % после, рост на 6–7 п. п. — на грани случайности. Это хроническая проблема, а не новая; разбирать стоит отдельно, по темам жалоб, и следить, не продолжится ли рост.
> 4. В остальных точках изменения до 6–7 п. п. — на грани случайности; наблюдаем.
>
> **Рекомендация:** выяснить, что изменилось в доставке KZN-2 в начале октября (подрядчик, курьеры, зона), и следить за долей жалоб на доставку по неделям. Отчёт можно пересчитывать каждую неделю тем же кодом.

::: tip
Чтобы отчёт был еженедельным, модели сохраняют (`joblib.dump(sent, "sent.joblib")`, глава 15) и раз в неделю прогоняют через них свежую выгрузку. Раз в квартал модель проверяют на свежей ручной разметке пары сотен отзывов — гости могут начать писать иначе.
:::
