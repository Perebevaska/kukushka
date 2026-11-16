---
title: "Проект: о чём жалуются гости"
files: [reviews_text.csv, reviews_new.csv, reviews_new_gold.csv]
lead: "По учебным отзывам с карт найдите точку и неделю, где изменилась доля сигналов модели. Сравните долю сигналов и их основные темы в двух периодах, прочитайте примеры и предложите управляющей действие, которое поможет проверить причину."
recap:
  - "Сначала оцените модель на отложенных текстах. После оценки обучите её на полной исторической выборке."
  - "Проверьте F1 каждой темы, macro-F1 и количество прогнозов. Балансировка классов меняет и счётчики, и качество. Сравните их на одном тесте."
  - "Разметка карт может отличаться от ранних звёзд в приложении. Для вывода о реальных жалобах нужны независимо размеченные людьми отзывы из обоих периодов."
  - "У точки с самой большой долей сигналов в октябре и у точки с наибольшим приростом к сентябрю могут быть разные ID."
  - "Сначала определите, где изменилась доля сигналов. Проверьте гипотезу о причине по независимому операционному источнику."
  - "Поправка (p − FPR) / (TPR − FPR) требует переносимых на новую цель и период частот ошибок и ненулевого знаменателя."
  - "Покажите числители, знаменатели и исходные ID цитат. Цитата помогает понять конкретную ситуацию; распространённость темы оценивают по всем подходящим строкам."
---

## Задача

> С сентября собираем отзывы о наших кофейнях с онлайн-карт: файл `reviews_new.csv`, около 4800 отзывов за сентябрь и октябрь. Оценок там нет, тем тоже — только текст, дата и точка. Читать всё вручную некому.
>
> Хочу понимать: в какой кофейне гости стали недовольнее, чем раньше, с какой недели и на что жалуются. Подкрепите выводы цитатами — их я перешлю управляющим точек.
>
> *Управляющая сетью*

## Итог проекта — письмо управляющей

Подготовьте письмо по собственной сводной. Его можно написать по базовому маршруту; в карточках `weekly` и `why` те же расчёты разбираются подробнее. Укажите точку и понедельник, с которого начинается «после». Для каждого периода приведите **число сигналов / все отзывы точки**. Затем для выбранной темы дайте другую пару чисел — **сигналы этой темы / все сигналы точки в периоде**. Отметьте малые группы, если они меняют вашу интерпретацию.

Приведите дословную цитату и исходный `review_id`. Что именно она подтверждает? Что в ней осталось за пределами присвоенной основной темы? Назовите действие управляющей для проверки гипотезы. Например, по журналу доставок можно отдельно узнать число опозданий среди всех доставок. Если считать нужно обоснованные жалобы в реальном потоке, укажите, как получить независимую человеческую разметку **обоих периодов** по общей инструкции и оценить неопределённость. Сохраните письмо рядом со сводной.

## Перенос в службу поддержки

За каждую из двух недель поддержка получила по 1 000 обращений. В первую неделю прежняя версия классификатора отметила 100 обращений. Со второй недели работает новая версия, она отметила 140. Руководитель предлагает написать «доля обоснованных жалоб выросла на 4 процентных пункта» и перевести сотрудника из другой очереди.

Какое решение вы подпишете сегодня? Что запросите для следующего решения? Обоснуйте ответ числами. Запишите ответ перед открытием разбора.

<details>
<summary>Разбор после собственного решения</summary>

Очередь выросла со 100 до 140 сигналов на 1000 обращений. Если каждый сигнал проверяет сотрудник, нагрузка выросла на 40 проверок. Чтобы решить, выросла ли доля обоснованных жалоб, независимо разметьте выборки из всех обращений обеих недель, включая обращения без сигнала. Используйте одно определение жалобы и оцените неопределённость разницы. Прогон обеих версий по одним и тем же ID поможет отдельно измерить влияние смены классификатора.

</details>

## План

До открытия разбора выберите по собственной таблице проблемную точку, период и свидетельства: максимальный уровень и максимальный прирост — разные критерии. Не подставляйте готовую точку до расчёта. В отчёте единица — отзыв. Здесь нет ID гостя и общего числа посетителей.


1. Две модели на размеченных `reviews_text.csv`: низкий рейтинг (`rating <= 3`) и тема. Оценка на отложенной части, затем переобучение на всех данных.
   Для темы — не только доля правильных, но и F1 по каждой теме: в отчёте будут счётчики по темам, и редкая тема не должна теряться.
2. Присоедините к каждому отзыву его прогноз и тему по ID. В первом сравнении используйте календарные месяцы — сентябрь и октябрь.
3. Доля сигналов по точкам. Сравните уровень в октябре и прирост относительно сентября.
4. Постройте понедельную таблицу, выберите точку для разбора, проверьте объём наблюдений и найдите дату изменения.
5. Для выбранной точки и даты сравните темы до и после, приложите цитаты с ID и сформулируйте гипотезу.
6. Поправка доли на ошибки модели.

Обе модели — TF-IDF слов и биграмм + логистическая регрессия (урок «Классификация текстов»).

У отзывов 41 и 73 может быть одинаковый текст. При групповом разбиении эти отзывы должны попасть на одну сторону границы train/test (`GROUP BY text`). Если таблица прогнозов вернулась в порядке 73, 41 и первый прогноз высокий, он относится к ID 73. Присоедините прогноз по исходному `review_id` (`JOIN … USING (review_id)`), даже если pandas-индекс начинается с нуля. Если модель вернула только массив значений, сохраните рядом ID в том порядке, в каком подавали тексты.

Для одного отзыва проследите цепочку: исходный `review_id` → текст → прогноз и тема → ячейка недельной таблицы → цитата в письме.

Рассмотрим 1 000 отзывов. Из них 100 содержат жалобу. Модель отметила 90 из этих 100 (TPR = 90 %) и ошибочно отметила 45 из 900 отзывов без жалобы (FPR = 5 %).

::: figure share-adjust
В примере модель дала 135 сигналов на 1 000 отзывов, доля сигналов 13,5 %. По известным частотам ошибок восстанавливается доля отзывов с жалобой 10 %.
:::

::: quiz
Доля сигналов выросла с 10 % до 14 %. Частоты ошибок оценены на контрольной выборке, но перечитать все отзывы нельзя. Как оценить изменение доли жалоб?

- [x] Поправить доли на известные ошибки модели — при переносимых частотах ошибок это даёт оценку доли; переносимость и выборочный разброс проверяем отдельно
  > Сырые доли от модели смещены: часть «негатива» — ложные срабатывания, часть пропущена.
- [ ] Сообщить «рост на 4 п.п.» без оговорок
  > Цифра может быть артефактом ошибок модели.
- [ ] Не сообщать ничего, пока модель не станет идеальной
  > Идеальной она не станет. Важно учесть ошибки, а не ждать.
- [ ] Посчитать долю вручную по всем отзывам
  > Сплошная проверка по единой инструкции тоже дала бы ответ, но для этой задачи доступна лишь выборочная разметка.
:::

## task: models | Шаг 1. Две модели | base

Оцените на отложенной четверти (`train_test_split(..., test_size=0.25, random_state=42, stratify=...)`) две модели вида `make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))`: тональность (цель `(rating <= 3).astype(int)`) и тему (цель `topic`). Сохраните `acc_sent` и `acc_topic` — доли правильных на тесте (3 знака). Затем обучите такие же модели **на всех** 2400 отзывах: `sent` и `topic_model`.

Проверьте перенос на другие формулировки. Сохраните `text_quality` — DataFrame с индексом `повторы`, `новые`, `без пересечения` и колонками `n_sent`, `acc_sent`, `n_topic`, `acc_topic`, `macro_f1_topic`. В первых двух строках разделите тест каждой модели по точному совпадению текста с обучением. В третьей используйте общие индексы `GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42)` с `groups=r["text"]`: одинаковая фраза целиком попадает на одну сторону. Сохраните список ID из этой контрольной части в `group_test_ids`. Для каждой строки считайте macro-F1 по полному списку тем, с `zero_division=0`. Числа округлите до трёх знаков. Финальные модели для следующего шага по-прежнему обучаются на всех отзывах.

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

from sklearn.model_selection import GroupShuffleSplit as _GSS
from sklearn.metrics import f1_score as _f1
_gtrain, _gtest = next(_GSS(n_splits=1, test_size=.25, random_state=42).split(r0, groups=r0.text))
_ids = list(need('group_test_ids'))
assert len(_ids) == len(_gtest) and set(_ids) == set(r0.iloc[_gtest].review_id), 'Сверьте ID из test общего разбиения по текстам.'
_q = need('text_quality')
assert isinstance(_q, _pd.DataFrame) and _q.index.is_unique and _q.columns.is_unique, 'text_quality — таблица с уникальными группами и показателями.'
for _label, _target in [('sent', y0), ('topic', r0.topic)]:
    _tr, _te = _tts(r0.index, test_size=.25, random_state=42, stratify=_target)
    _seen = set(r0.loc[_tr, 'text'])
    for _group, _fit, _test in [('повторы', _tr, [i for i in _te if r0.text[i] in _seen]),
                                ('новые', _tr, [i for i in _te if r0.text[i] not in _seen]),
                                ('без пересечения', _gtrain, _gtest)]:
        _pred = _m().fit(r0.text.iloc[_fit], _target.iloc[_fit]).predict(r0.text.iloc[_test])
        _true = _target.iloc[_test]
        assert _group in _q.index and {'n_'+_label, 'acc_'+_label, 'macro_f1_topic'} <= set(_q.columns), 'Проверьте подписи групп и метрик text_quality.'
        assert _q.loc[_group, 'n_'+_label] == len(_test), f'{_group}: проверьте число текстов для {_label}.'
        assert close(_q.loc[_group, 'acc_'+_label], (_pred == _true).mean(), .0015), f'{_group}: пересчитайте accuracy для {_label}.'
        if _label == 'topic':
            assert close(_q.loc[_group, 'macro_f1_topic'], _f1(_true, _pred, labels=sorted(_target.unique()), average='macro', zero_division=0), .0015), f'{_group}: пересчитайте macro-F1 тем на этой же выборке.'

```

### hint
Функция `new_model()` возвращает каждый раз новый, необученный конвейер — используйте её для всех четырёх моделей (две оценочные и две финальные).

### hint
Для отметки дословных повторов удобно использовать `X_test.isin(X_train)`. Индексы разбиения по группам возвращает `next(splitter.split(r, groups=r["text"]))`. Два разбиения строк: для тональности `stratify=y`, для темы `stratify=r["topic"]`. Финальные модели: `new_model().fit(r["text"], y)` и `new_model().fit(r["text"], r["topic"])`.

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

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import f1_score

text_quality = pd.DataFrame(index=["повторы", "новые", "без пересечения"])
group_train, group_test = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42)
                               .split(r, groups=r["text"]))
group_test_ids = r.iloc[group_test]["review_id"].tolist()
assert set(r.iloc[group_train]["text"]).isdisjoint(r.iloc[group_test]["text"])
for label, target in [("sent", y), ("topic", r["topic"])]:
    train, test = train_test_split(r.index, test_size=.25, random_state=42, stratify=target)
    repeated = r.loc[test, "text"].isin(r.loc[train, "text"])
    for subset, fit_ids, test_ids in [("повторы", train, test[repeated]),
                                     ("новые", train, test[~repeated]),
                                     ("без пересечения", group_train, group_test)]:
        predicted = new_model().fit(r.loc[fit_ids, "text"], target.loc[fit_ids]).predict(r.loc[test_ids, "text"])
        truth = target.loc[test_ids]
        text_quality.loc[subset, "n_" + label] = len(truth)
        text_quality.loc[subset, "acc_" + label] = round(accuracy_score(truth, predicted), 3)
        if label == "topic":
            text_quality.loc[subset, "macro_f1_topic"] = round(f1_score(
                truth, predicted, average="macro", labels=sorted(target.unique()), zero_division=0), 3)
print(text_quality)
```

### explain
В случайном тесте по тональности accuracy равна 0,939 на 82 дословных повторах и 0,944 на 518 новых текстах. По теме на 81 повторе accuracy и macro-F1 равны 1,000, а на 519 новых текстах они равны 0,792 и 0,761. При разбиении по самой формулировке все 592 проверочных отзыва содержат фразы, отсутствующие в обучении. Здесь accuracy по тональности составила 0,953, по теме — 0,816, macro-F1 тем — 0,794. Размеры групп различаются, потому что случайные разбиения стратифицированы отдельно по каждой цели. Для отчёта о переносе на следующие формулировки укажите способ разделения вместе с результатом и единицей подсчёта.

## task: rare | Шаг 1 б. Редкая тема: F1 вместо доли правильных | plus

Доля правильных у модели тем — около 82 %, но в отчёте управляющей будут **счётчики по темам**, и важна каждая тема, в том числе редкая. Доля правильных усредняет по отзывам: частая тема «кофе» тянет её вверх, а провал на редкой теме почти не виден. Поэтому смотрят F1 по каждому классу и **macro-F1** — простое среднее F1 по классам, где редкая тема весит столько же, сколько частая.

На том же разбиении, что в шаге 1 (тема, `stratify=r["topic"]`), обучите модель `new_model()` и сохраните:

- `f1_by_topic` — словарь «тема → F1 на тесте» (3 знака), `macro_f1` (3 знака);
- `rarest` — тему, которой меньше всего в тесте, и `worst` — тему с наименьшим F1;
- `count_ratio` — во сколько раз модель недосчитывает редчайшую тему: число отзывов, которые модель **назвала** этой темой, делённое на настоящее число в тесте (3 знака);
- `f1_rare_balanced` — F1 редчайшей темы у той же модели с `LogisticRegression(max_iter=1000, class_weight="balanced")` (3 знака).


При расчёте F1 передавайте полный список шести тем через `labels=sorted(r["topic"].unique())` и `zero_division=0`. Тема без верных прогнозов получает F1 = 0; в macro-F1 она сохраняет тот же вес, что остальные.

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
f1_by_topic = {k: round(float(v), 3) for k, v in zip(labels, f1_score(t_test, pred, average=None, labels=labels, zero_division=0))}
macro_f1 = round(float(f1_score(t_test, pred, average="macro", labels=labels, zero_division=0)), 3)
rarest = t_test.value_counts().idxmin()
worst = min(f1_by_topic, key=f1_by_topic.get)
count_ratio = round(float((pred == rarest).sum() / (t_test == rarest).sum()), 3)

pred_b = new_model("balanced").fit(X_train, t_train).predict(X_test)
f1_rare_balanced = round(float(f1_score(t_test, pred_b, labels=[rarest], average=None, zero_division=0)[0]), 3)
print(f1_by_topic, macro_f1, rarest, worst, count_ratio, f1_rare_balanced)
```

### explain
Самая редкая тема — «атмосфера» (58 отзывов в тесте), и у неё же худший F1 — около 0.74 против 0.89 у «кофе». Macro-F1 около 0.79 — ниже доли правильных 0.82: среднее по классам честнее показывает слабые места. Главное для отчёта — `count_ratio` около 0.69: модель редко ошибается, когда говорит «атмосфера» (точность 0.90), но пропускает почти 40 % таких отзывов, и в счётчиках по темам атмосфера окажется занижена почти на треть. С `class_weight="balanced"` ошибка на редком классе стоит дороже, полнота «атмосферы» растёт до 0.76, F1 — до 0.76, а общая доля правильных падает до 0.81: модель жертвует частым «кофе». Какую модель брать, зависит от вопроса: для **счётчиков по темам** важнее не занижать редкие темы, для **одного прогноза на отзыв** — общая точность. Ошибка, которую легко сделать: смотреть `average="weighted"` — оно взвешивает по числу отзывов и почти совпадает с долей правильных, то есть прячет ту же проблему.

## task: score | Шаг 2. Разметка новых отзывов | base

Модели `sent` и `topic_model` обучены в заготовке. Присоединяйте вероятности и темы по `review_id`, сохраняя исходные `shop_id`, дату и текст. Перестановка прогнозов в отдельной таблице не должна менять, чьему отзыву они принадлежат. Загрузите `reviews_new.csv` в `n` (дата — `datetime`) и добавьте колонки: `p_neg` — вероятность недовольства, `neg` — 1, если `p_neg >= 0.5`, иначе 0, `topic` — предсказанная тема, `period` — `"после"` для дат с 2026-10-01 включительно и `"до"` для остальных. Сохраните `n_after` — число отзывов в периоде «после».

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
assert n['review_id'].is_unique and set(n['review_id'])==set(n0['review_id']), 'review_id должен совпадать с источником без дублей.'
n = n.set_index('review_id').reindex(n0['review_id']).reset_index()
for _key in ('date','shop_id','text'):
    assert n[_key].tolist()==n0[_key].tolist(), f'{_key}: исходное значение не соответствует review_id.'
assert len(n) == len(n0), f'Строк {len(n)}, а в файле {len(n0)}.'
assert _pd.api.types.is_datetime64_any_dtype(n['date']), 'Колонка date должна быть датой: parse_dates=["date"].'
p = need('sent').predict_proba(n0['text'])[:, 1]
assert _np.allclose(n['p_neg'].values, p, atol=1e-6), 'p_neg — вторая колонка predict_proba.'
assert (n['neg'].astype(int).values == (p >= 0.5).astype(int)).all(), 'neg = (p_neg >= 0.5).'
assert (n['topic'].values == need('topic_model').predict(n0['text'])).all(), 'topic — предсказание topic_model.'
want = _np.where(n0['date'] >= '2026-10-01', 'после', 'до')
assert (n['period'].values == want).all(), 'period: «после» — с 2026-10-01 включительно.'
assert need('n_after') == int((want == 'после').sum()), f'n_after = {need("n_after")}.'
```

### hint
Модели уже обучены — здесь только применение: `predict_proba` для вероятности, `predict` для темы.

### hint
`sent.predict_proba(n["text"])[:, 1]`; `np.where(n["date"] >= "2026-10-01", "после", "до")`.

### solution
```python
import numpy as np
import pandas as pd

n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
n["topic"] = topic_model.predict(n["text"])
n["period"] = np.where(n["date"] >= "2026-10-01", "после", "до")
n_after = int((n["period"] == "после").sum())
print(n.sample(5, random_state=1)[["text", "p_neg", "topic"]])
```

### explain
Цель старой модели — низкая оценка (`rating <= 3`), цель нового отчёта — жалоба в смысле текста по согласованной инструкции. Эти определения могут расходиться: низкая звезда без жалобы и жалоба с высокой звездой требуют отдельной ручной разметки. Перед любыми выводами стоит прочитать пару десятков размеченных строк: новые отзывы пришли из другого источника, и если бы там писали иначе (длиннее, с жаргоном, на другие темы), модель могла бы тихо ошибаться. Похожесть текстов не доказывает перенос качества: независимо и вслепую разметьте часть новой партии из обоих периодов по одному правилу; покажите численности и знаменатели.

## task: shops | Шаг 3. Уровень и рост | base

Для первой сверки сравните сентябрь и октябрь. Посчитайте по каждой точке долю отзывов с сигналом модели (`neg`) до 1 октября и начиная с этой даты. Сохраните `by_shop` — DataFrame с индексом `shop_id` и колонками `до`, `после`, `рост` (`после − до`), все — 3 знака, отсортированный по `рост` по убыванию. В `worst_level` — точку с наибольшей долей «после», в `worst_growth` — с наибольшим ростом.

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
n["period"] = np.where(n["date"] >= "2026-10-01", "после", "до")
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
Сравните лидера столбца «после» с лидером прироста. Доля сигналов модели относится к поступившим отзывам. Чтобы найти неделю изменения, понадобится другая группировка; граница календарных месяцев служила для предварительной сверки.

## task: weekly | Шаг 4. С какой недели | plus

Соберите `weekly`: индекс — понедельник недели, столбцы — точки, значение — доля отзывов с сигналом модели. Выберите точку `focus_shop` и найдите её `jump_week` — неделю наибольшего роста относительно предшествующей. В `sept_max` сохраните максимум недельной доли этой точки до `jump_week` (три знака). Постройте график и посмотрите, сколько отзывов было в неделю скачка и удержался ли уровень позже. Запишите, какую точку и дату возьмёте для разбора тем.


На графике покажите ту же зависимость: календарные недели и долю сигналов выбранной точки. Можно использовать линию или столбцы. Подписи, если вы их добавляете, должны соответствовать долям и выбранной точке. Порядок строк таблицы произвольный, если значения сохраняют свои даты и точки.


После вычисления `weekly` и самостоятельного выбора `focus_shop` в браузере для столбцов используйте прямой matplotlib:

```python
fig, ax = plt.subplots()
ax.bar(weekly.index.to_pydatetime(), weekly[focus_shop].to_numpy(), width=4)
ax.set(xlabel="Понедельник недели", ylabel="Доля сигналов", title=str(focus_shop))
```

В текущей браузерной версии pandas `Series.plot(kind="bar")` с `DatetimeIndex` может завершиться `ValueError` ещё до проверки. Пример выше показывает ту же зависимость через matplotlib и не выбирает точку за вас.

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
assert got.index.is_unique and got.columns.is_unique and set(got.index)==set(w.index) and set(got.columns)==set(w.columns), 'weekly: сохраните уникальные даты недель и точки.'
assert ((got.reindex(index=w.index,columns=w.columns).values-w.values)**2).max()<1e-12, 'Доли должны соответствовать своей неделе и точке.' 
_shop=need('focus_shop')
assert _shop in w.columns, 'Выберите точку из weekly.'
jw = w[_shop].diff().idxmax()
assert _pd.Timestamp(need('jump_week')) == jw, f'jump_week = {need("jump_week")}, а нужно {jw.date()}.'
sm = round(float(w.loc[w.index < jw, _shop].max()), 3)
assert close(need('sept_max'), sm, 0.0015), f'sept_max = {need("sept_max")}, а нужно {sm}.'

import numpy as _np
import matplotlib.dates as _md
from matplotlib.container import BarContainer as _BarContainer
_expected_dates = list(w.index)
_expected_values = w[_shop].to_numpy()
def _calendar_values(x, complete=True, axis=None, categorical=False):
    values=list(x)
    if not values: return None
    candidates=[]
    try: candidates.append([_pd.Timestamp(v.end_time).normalize() if isinstance(v,_pd.Period) else _pd.Timestamp(v).normalize() for v in values])
    except (ValueError,TypeError,OverflowError): pass
    try: candidates.append([_pd.Timestamp(_md.num2date(float(v))).tz_localize(None).normalize() for v in values])
    except (ValueError,TypeError,OverflowError): pass
    if categorical and axis is not None:
        try:
            locations=_np.asarray(axis.get_xticks(),dtype=float)
            labels=axis.get_xticklabels()
            mapped=[]
            for coordinate in values:
                matches=_np.flatnonzero(_np.isclose(locations,float(coordinate),rtol=0,atol=1e-8))
                if len(matches)!=1:
                    raise ValueError('Категориальный столбец должен иметь одну подпись даты на своей позиции.')
                text=labels[int(matches[0])].get_text().strip()
                mapped.append(_pd.Timestamp(text).normalize())
            candidates.append(mapped)
        except (ValueError,TypeError,OverflowError,IndexError):
            pass
    for dates in candidates:
        if complete and len(dates)==len(_expected_dates) and set(dates)==set(_expected_dates): return dates
        if not complete and all(date in _expected_dates for date in dates): return dates
    return None
def _matches_plot(x,y,shop=_shop,complete=True,axis=None,categorical=False):
    dates=_calendar_values(x,complete=complete,axis=axis,categorical=categorical)
    if dates is None: return False
    try:
        values=_np.asarray(y,dtype=float)
        expected=w.loc[dates,shop].to_numpy()
        return values.shape==expected.shape and _np.allclose(values,expected,atol=1e-6,rtol=0)
    except (ValueError,TypeError): return False
_plot_ok=False
for _fig in figs:
    for _ax in _fig.axes:
        _labels=' '.join([_ax.get_title(),*[_t.get_text() for _t in (_ax.get_legend().texts if _ax.get_legend() else [])]])
        _units=_ax.get_ylabel().lower()
        _mentioned_shops={str(_key) for _key in w.columns if str(_key) in _labels}
        if _mentioned_shops and _shop not in _mentioned_shops: continue
        if _units and not any(_unit in _units for _unit in ['дол','share','fraction']): continue
        for _line in _ax.lines:
            _named_shop=_line.get_label()
            if _named_shop in w.columns:
                assert _matches_plot(_line.get_xdata(orig=True),_line.get_ydata(),shop=_named_shop,complete=False), 'Каждая серия с названием точки должна показывать её действительные доли по датам, включая выделенную линию.'
            if _matches_plot(_line.get_xdata(orig=True),_line.get_ydata()): _plot_ok=True
        for _container in _ax.containers:
            if isinstance(_container,_BarContainer):
                _named_shop=_container.get_label()
                if _named_shop in w.columns:
                    assert _matches_plot([b.get_x()+b.get_width()/2 for b in _container.patches],[b.get_height() for b in _container.patches],shop=_named_shop,complete=False,axis=_ax,categorical=True), 'Каждая серия столбцов с названием точки должна показывать её действительные доли по датам.'
                if _matches_plot([b.get_x()+b.get_width()/2 for b in _container.patches],[b.get_height() for b in _container.patches],axis=_ax,categorical=True): _plot_ok=True
assert _plot_ok, 'Покажите недельные доли выбранной точки по реальным датам; подписи, если они есть, должны сохранять долю и выбранную точку. Подойдёт линия или столбцы.'
```

### hint
Неделя: `n["date"].dt.to_period("W").dt.start_time` — понедельник недели каждой даты.

### hint
`n.pivot_table(index="week", columns="shop_id", values="neg", aggfunc="mean")`; `weekly[focus_shop].diff().idxmax()`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

n["week"] = n["date"].dt.to_period("W").dt.start_time
weekly = n.pivot_table(index="week", columns="shop_id", values="neg", aggfunc="mean")
change_date,focus_shop=weekly.diff().stack().idxmax()
jump_week = weekly[focus_shop].diff().idxmax()
sept_max = round(float(weekly.loc[weekly.index < jump_week, focus_shop].max()), 3)
print(weekly.round(2))
print(jump_week.date(), sept_max)
ax = weekly.plot(figsize=(9, 4), color="lightgray", legend=False)
weekly[focus_shop].plot(ax=ax, color="crimson", lw=3, label=focus_shop)
ax.set_ylabel("доля сигналов модели"); ax.legend()
```

### explain
Положительная разность между неделями показывает момент изменения сигнала. Если в неделе всего два отзыва, одна дополнительная жалоба резко изменит долю. Для письма сравните объёмы до и после, а также несколько недель после скачка.

## task: why | Шаг 5. Темы и цитаты | plus

Сохраните выбранную точку в `focus_shop`, дату раздела в `change_date`. Проверьте, что в каждом из двух периодов у точки есть хотя бы 30 отзывов. Создайте `period` по своей дате. Для отзывов с сигналом модели посчитайте доли тем по периодам. Числитель — сигналы с данной основной темой, знаменатель — все сигналы соответствующего периода в той же группе. Для выбранной точки сохраните таблицу `kzn` (имя для сдачи), для остальных точек вместе — `others`. В `cause` запишите тему с наибольшим ростом доли. Из этой темы после границы возьмите пять текстов с наибольшей `p_neg` в порядке убывания и их исходные ID в том же порядке (`quotes` и `quote_ids`). Прочтите цитаты: действительно ли текст подтверждает тему модели?

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
n0 = need('n', _pd.DataFrame).copy()
_shop=need('focus_shop');_date=_pd.Timestamp(need('change_date'))
assert _shop in set(n0.shop_id), 'Выберите существующую точку.'
assert n0.date.min() < _date < n0.date.max(), 'Дата разделяет наблюдавшиеся периоды.'
n0['period']=__import__('numpy').where(n0.date>=_date,'после','до')
_counts=n0[n0.shop_id==_shop].groupby('period').size()
assert set(_counts.index)=={'до','после'} and (_counts>=30).all(), 'Для сравнения нужно не меньше30 отзывов точки в каждом периоде.'
bad=n0[n0['neg']==1]
k0 = bad[bad['shop_id'] == _shop]; o0 = bad[bad['shop_id'] != _shop]
kw = _pd.crosstab(k0['topic'], k0['period'], normalize='columns')
ow = _pd.crosstab(o0['topic'], o0['period'], normalize='columns')
k, o = need('kzn', _pd.DataFrame), need('others', _pd.DataFrame)
assert ((k[['до', 'после']] - kw[['до', 'после']]).abs() < 1e-6).all().all(), 'kzn не совпадает: только недовольные отзывы KZN-2, normalize="columns".'
assert ((o[['до', 'после']] - ow[['до', 'после']]).abs() < 1e-6).all().all(), 'others не совпадает: недовольные отзывы остальных точек.'
c = (kw['после'] - kw['до']).idxmax()
assert need('cause') == c, f'cause = {need("cause")!r}.'
qw = k0[(k0['period'] == 'после') & (k0['topic'] == c)].sort_values('p_neg', ascending=False)['text'].head(5).tolist()
assert need('quotes', list) == qw, 'quotes: пять текстов с наибольшей p_neg, по убыванию.'
_expected_ids=k0[(k0['period']=='после')&(k0['topic']==c)].sort_values('p_neg',ascending=False)['review_id'].head(5).tolist()
assert list(need('quote_ids'))==_expected_ids, 'Цитаты должны сопровождаться исходными review_id этой точки, периода и темы.'

```

### hint
Сначала пересчитайте период по `change_date`. Оставьте строки с `neg == 1`, затем разделите их по условию `shop_id == focus_shop`. Для каждой доли знаменатель — число отмеченных отзывов в соответствующей группе и периоде.

### hint
Фильтр по точке и `pd.crosstab(...)`; `cause = (kzn["после"] - kzn["до"]).idxmax()`. Для цитат — фильтр по периоду и теме, `.sort_values("p_neg", ascending=False)`, `.head(5)`.

### solution
```python
import pandas as pd

_weeks=n.assign(week=n['date'].dt.to_period('W').dt.start_time).pivot_table(index='week',columns='shop_id',values='neg',aggfunc='mean')
change_date,focus_shop=_weeks.diff().stack().idxmax()
change_date=pd.Timestamp(change_date)
n=n.copy()
n['period']=__import__('numpy').where(n['date']>=change_date,'после','до')
bad = n[n["neg"] == 1]
kb = bad[bad["shop_id"] == focus_shop]
ob = bad[bad["shop_id"] != focus_shop]
kzn = pd.crosstab(kb["topic"], kb["period"], normalize="columns")
others = pd.crosstab(ob["topic"], ob["period"], normalize="columns")
cause = (kzn["после"] - kzn["до"]).idxmax()
quotes = (kb[(kb["period"] == "после") & (kb["topic"] == cause)]
          .sort_values("p_neg", ascending=False)["text"].head(5).tolist())
print(kzn.round(2), others.round(2), cause, *quotes, sep="\n")
quote_ids = kb[(kb['period']=='после')&(kb['topic']==cause)].sort_values('p_neg',ascending=False)['review_id'].head(5).tolist()

```

### explain
Самая быстрорастущая тема у выбранной точки задаёт гипотезу. Например, жалобы на доставку можно сопоставить с долей опозданий в журнале заказов этой точки за те же недели. Укажите ID подходящих цитат и случаи, где тема модели расходится с содержанием.

## task: adjust | Шаг 6. Поправка на ошибки модели | star

Обозначим через q долю отзывов с жалобой, через p — долю сигналов. Тогда p = q · TPR + (1 − q) · FPR, откуда q = (p − FPR) / (TPR − FPR) при TPR ≠ FPR. Частоты ошибок должны относиться к той же цели, точке и периоду. Если они стабильны и TPR > FPR, рост p соответствует росту q. При TPR < FPR направление обратное. При TPR = FPR сигналы не позволяют восстановить долю жалоб. Смена частот ошибок тоже меняет картину: при доле жалоб 10 %, TPR 80 % и росте FPR с 2,22 % до 6,67 % доля сигналов вырастет с 10 % до 14 % без роста жалоб.

**1. Старый тест со звёздами.** Цель модели — рейтинг ≤ 3. На отложенной четверти размеченных отзывов вычислите `tpr` и `fpr`. Используйте разбиение и модель из шага 1. Примените эти две частоты к долям сигналов в KZN-2 до и после границы, сохраните поправки в словарь `adj = {"до": ..., "после": ...}` с точностью до трёх знаков.

В готовой таблице `n` граница — **5 октября 2026 года**. Отзывы с этой даты включительно входят в «после». В собственном отчёте из шага `why` укажите выбранную вами дату. В какой период попадёт отзыв от 3 октября при границе 1 октября? А при границе 5 октября?

**2. Новая партия с метками жалоб.** Соедините строки отзывов из `n` с `reviews_new_gold.csv` по `review_id`, затем выберите KZN-2. Соберите таблицу `audit` с индексом `period` и одной строкой на период.

| Поля | Что рассчитать в каждом периоде |
|---|---|
| `n`, `complaints` | Число размеченных отзывов и число жалоб по разметке. |
| `tpr`, `fpr` | Доля сигналов среди отзывов с жалобой и доля сигналов среди отзывов без жалобы. |
| `observed`, `manual` | Доля сигналов модели и доля жалоб по разметке среди всех размеченных отзывов. |
| `adjusted` | Поправка по частотам ошибок этого периода. |

Здесь метки жалоб создал генератор (`label_source = synthetic_kind_neg_or_mixed`). Почему совпадение с долей жалоб на тех же строках ещё не показывает точность на будущей неделе? Для вывода о реальном потоке потребуются новые отзывы обоих периодов с независимой человеческой разметкой и оценкой неопределённости.

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
_source_n = _pd.read_csv('reviews_new.csv',parse_dates=['date'])
assert n0.review_id.is_unique and set(n0.review_id)==set(_source_n.review_id), 'n должна содержать все исходные review_id без пропусков и дублей.'
_aligned_n=n0.set_index('review_id').reindex(_source_n.review_id)
for _key in ['shop_id','date','text']:
    assert _aligned_n[_key].tolist()==_source_n[_key].tolist(), f'n/{_key}: сохраните исходное значение по review_id.'
_expected_period = __import__('numpy').where(_source_n.date>='2026-10-05','после','до')
assert _aligned_n.period.tolist()==list(_expected_period), 'В готовой n граница — 5 октября включительно.'
obs = n0[n0['shop_id'] == 'KZN-2'].groupby('period')['neg'].mean()
w = {k: round((obs[k] - f0) / (t0 - f0), 3) for k in ['до', 'после']}
got = need('adj', dict)
assert all(close(got[k], w[k], 0.003) for k in w), f'adj = {got}, а нужно {w}.'
_gold=_pd.read_csv('reviews_new_gold.csv').copy(deep=True)
_labeled=n0.merge(_gold[['review_id','complaint']],on='review_id',validate='one_to_one')
_audit=need('audit',_pd.DataFrame)
assert _audit.index.is_unique and set(_audit.index)=={'до','после'}, 'audit: ровно два уникальных периода — до и после.'
assert _audit.columns.is_unique and {'n','complaints','tpr','fpr','observed','manual','adjusted'} <= set(_audit.columns), 'audit: сохраните семь обязательных показателей из условия без дублей; дополнительные диагностические колонки допустимы.'
_expected_audit={}
for _period,_part in _labeled[_labeled.shop_id=='KZN-2'].groupby('period'):
    _target=_part.complaint; _tp=float(_part.loc[_target==1,'neg'].mean()); _fp=float(_part.loc[_target==0,'neg'].mean());_obs=float(_part.neg.mean())
    _want=dict(n=len(_part),complaints=int(_target.sum()),tpr=_tp,fpr=_fp,observed=_obs,manual=float(_target.mean()),adjusted=(_obs-_fp)/(_tp-_fp))
    _expected_audit[_period] = _want.copy()
    for _key,_value in _want.items():
        assert close(_audit.loc[_period,_key],_value), f'audit {_period}/{_key}: разметка нового потока и исходные знаменатели, не частоты старых звёзд.'
# Source copies prevent aliasing with learner variables while reordering input only in memory.
_join_input = n0.copy(deep=True)
_join_gold = _gold.copy(deep=True)
_read_csv_original = _pd.read_csv
def _reordered_gold_reader(filename,*args,**kwargs):
    if str(filename).replace('\\','/').rsplit('/',1)[-1]=='reviews_new_gold.csv':
        return _join_gold.sample(frac=1,random_state=29).reset_index(drop=True).copy(deep=True)
    return _read_csv_original(filename,*args,**kwargs)
try:
    _pd.read_csv = _reordered_gold_reader
    _rerun = rerun_with(n=_join_input.copy(deep=True),sent=need('sent'))
finally:
    _pd.read_csv = _read_csv_original
_rerun_audit=_rerun.get('audit')
assert isinstance(_rerun_audit,_pd.DataFrame) and _rerun_audit.index.is_unique and set(_rerun_audit.index)=={'до','после'}, 'На переставленных строках разметки audit сохраняет оба периода.'
for _period,_values in _expected_audit.items():
    for _key,_value in _values.items():
        assert close(_rerun_audit.loc[_period,_key],_value), 'Соединяйте разметку по review_id: порядок строк gold не должен менять audit.'
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
gold = pd.read_csv('reviews_new_gold.csv')
labeled = n.merge(gold[['review_id','complaint']],on='review_id',validate='one_to_one')
rows=[]
for period,part in labeled[labeled.shop_id=='KZN-2'].groupby('period'):
    target=part.complaint
    tpr_new=float(part.loc[target==1,'neg'].mean())
    fpr_new=float(part.loc[target==0,'neg'].mean())
    observed=float(part.neg.mean())
    rows.append(dict(period=period,n=len(part),complaints=int(target.sum()),tpr=tpr_new,fpr=fpr_new,observed=observed,manual=float(target.mean()),adjusted=(observed-fpr_new)/(tpr_new-fpr_new) if abs(tpr_new-fpr_new)>1e-6 else float("nan")))
audit=pd.DataFrame(rows).set_index('period')

```

### explain
В `audit` сравните численности и частоты ошибок по синтетическим меткам новой партии по обе стороны границы. Поправка по старым звёздам предполагает перенос ошибок. Если состав отзывов или точность модели изменились, одна поправка на два периода может исказить величину роста.

После расчёта вернитесь к собственному письму из начала проекта. Подпишите доли сигналов, учебных меток жалобы и результат поправки.

::: tip
Чтобы отчёт был еженедельным, модели сохраняют (`joblib.dump(sent, "sent.joblib")`, глава 15) и раз в неделю прогоняют через них свежую выгрузку. Раз в квартал модель проверяют на свежей ручной разметке пары сотен отзывов — гости могут начать писать иначе.
:::
