---
title: "Качество разметки: голосование, каппа, золотой набор"
lead: "На 450 учебных отзывах сравним три набора голосов, имитирующих работу разметчиков. Как определить согласие, проверить метку по эталону и решить, какие тексты отдать на перепроверку?"
files: [review_labels.csv, review_gold.csv, reviews_text.csv]
recap:
  - "Разметку проверяют: итог по нескольким разметчикам — голосованием большинством, согласие — каппой Коэна κ = (pₒ − pₑ) / (1 − pₑ), которая вычитает случайные совпадения (`cohen_kappa_score`)."
  - "Кому доверять, показывает золотой набор — отзывы с известным ответом, незаметно подмешанные в задания. Голосование с одним плохим разметчиком бывает хуже лучшего разметчика."
  - "Генератор задаёт topic до появления текста. Для учебного золотого набора 50 исходных тем скопированы по ID. Для независимой оценки реальной работы нужно отдельно проверить тексты."
---

Модель тем в предыдущем уроке дала около 79 % совпадений с исходной темой. Чтобы понять эту цифру, полезно знать, откуда взялась эталонная метка и что происходит при её замене.

## Качество разметки: голосование, золотой набор, каппа

В этих данных Аня, Борис и Вика — три учебных профиля. Для 450 текстов генератор взял основную тему и с разными вероятностями внёс ошибки в три набора ответов. В профиле Вики часть ответов независимо от текста получает «атмосферу». Сравним согласие и точность этих профилей.

::: tip Аналогия
Разметка — как судейство в фигурном катании: один судья может ошибиться или симпатизировать, поэтому оценок несколько, а крайние отбрасывают. Но если двое судей ставят всем одинаковые баллы не глядя, их «согласие» ничего не стоит — нужно сравнивать с тем, сколько совпадений вышло бы случайно.
:::

**Голосование большинством.** Тема отзыва — та, которую выбрали хотя бы двое из трёх. Игрушечный пример:

| отзыв | Аня | Борис | Вика | итог |
|---|---|---|---|---|
| 1 | кофе | кофе | кофе | кофе — единогласно |
| 2 | доставка | доставка | обслуживание | доставка — 2 из 3 |
| 3 | еда | цена | атмосфера | нет большинства — на перепроверку |

**Согласие с поправкой на случай — каппа Коэна.** Доля совпадений обманчива, когда один класс встречается часто. Пусть двое размечают 10 отзывов «жалоба / не жалоба», и каждый ставит «жалобу» двум отзывам из десяти, но общий у них только один — отзыв 1. Совпали отзыв 1 и ещё семь «не жалоб», не совпали два.

- Наблюдаемое согласие: 8 совпадений из 10, $p_o = 0.8$.
- Случайное согласие: если бы оба ставили метки наугад с теми же долями, «жалоба» совпадала бы с вероятностью 0.2 · 0.2 = 0.04, «не жалоба» — 0.8 · 0.8 = 0.64. Всего $p_e = 0.68$.
- Каппа — какую долю **возможного сверх случайного** согласия они набрали: (0.8 − 0.68) / (1 − 0.68) = 0.12 / 0.32 = **0.375**.

::: figure kappa-toy
Десять отзывов, два разметчика: 8 совпадений, но 68 % совпадений дал бы случай при таких долях «жалоб». Каппа показывает, сколько согласия набрано сверх случая.
:::

$$\kappa = \frac{p_o - p_e}{1 - p_e}$$

Здесь $p_o$ — доля отзывов, где метки совпали; $p_e$ — ожидаемая доля случайных совпадений: сумма по классам произведений долей этого класса у первого и у второго разметчика. $\kappa = 1$ — полное согласие, $0$ — не лучше случая, меньше нуля — хуже случая. Чтобы решить, нужна ли доработка инструкции, прочитайте спорные отзывы и сопоставьте голоса с независимым эталоном. Порог каппы сам по себе причину спора не показывает.

Проверим игрушечный пример руками и функцией sklearn:

```python
from sklearn.metrics import cohen_kappa_score

a = ["ж", "н", "н", "н", "н", "н", "н", "ж", "н", "н"]
b = ["ж", "н", "н", "н", "н", "н", "н", "н", "ж", "н"]

p_o = sum(x == y for x, y in zip(a, b)) / len(a)
p_e = sum((a.count(c) / len(a)) * (b.count(c) / len(b)) for c in set(a) | set(b))
print(p_o, round(p_e, 2), round((p_o - p_e) / (1 - p_e), 3), round(cohen_kappa_score(a, b), 3))
```

Теперь рассмотрим смоделированные голоса. В `review_labels.csv` по строке на один ответ одного разметчика, всего 1350 строк.

```python
import pandas as pd
from sklearn.metrics import cohen_kappa_score

labels = pd.read_csv("review_labels.csv")
wide = labels.pivot(index="review_id", columns="annotator", values="label")   # 450 × 3

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

wide["vote"] = wide[["аня", "борис", "вика"]].apply(majority, axis=1)
print(wide.head(4))
print("единогласно:", round((wide[["аня", "борис", "вика"]].nunique(axis=1) == 1).mean(), 3),
      "| без большинства:", wide["vote"].isna().sum())
for x, y in [("аня", "борис"), ("аня", "вика"), ("борис", "вика")]:
    print(f"{x}–{y}: совпадений {(wide[x] == wide[y]).mean():.3f}, каппа {cohen_kappa_score(wide[x], wide[y]):.3f}")
```

**Что здесь происходит:**

- `pivot(index="review_id", columns="annotator", values="label")` — из длинной таблицы делаем широкую: строка на отзыв, столбец на разметчика (как сводная таблица в Excel).
- `majority(row)` — `value_counts()` по строке считает голоса за каждую тему; если у лидера хотя бы 2 голоса, это итог, иначе `None`.
- `nunique(axis=1) == 1` — во всех трёх ячейках строки одна и та же тема.
- `cohen_kappa_score(x, y)` — каппа для каждой пары разметчиков.

У 27 отзывов нет большинства. Аня и Борис совпали примерно в 80 % случаев, каппа 0,76. Для двух пар с Викой каппа 0,43 и 0,47. Различие подсказывает, чьи спорные ответы изучить. Чтобы установить причину в работе людей, нужны примеры и проверка инструкции.

**Золотой набор** — примеры с заранее установленным эталоном. Для проверки людей тему обычно независимо определяют по инструкции, а контрольные отзывы смешивают с остальными. В нашем упражнении 50 строк `review_gold.csv` получены копированием `topic` по ID. По ним можно измерить, как часто имитированные ответы совпадают с темой генератора.

```python
import pandas as pd

labels = pd.read_csv("review_labels.csv")
gold = pd.read_csv("review_gold.csv").set_index("review_id")["label"]
wide = labels.pivot(index="review_id", columns="annotator", values="label")

check = wide.loc[gold.index]                        # только отзывы золотого набора
print((check.eq(gold, axis=0)).mean().round(2))     # доля верных у каждого
print(wide["вика"].value_counts().head(3))
```

Из 50 контрольных тем Аня правильно назвала 46 (92 %), Борис 39 (78 %), Вика 27 (54 %). У Вики «атмосфера» — самый частый ответ. Здесь причина известна из генератора. В реальном проекте такой перекос можно заметить по частотам, а объяснение проверить на спорных текстах.

::: quiz
Два разметчика согласны в 95 % отзывов о доставке «опоздал / не опоздал», а каппа Коэна — 0.1. Как такое возможно?

- [x] «Не опоздал» — почти все отзывы, и при таких долях даже случайные метки совпадали бы почти так же часто; сверх случая разметчики согласны мало
  > Каппа вычитает ожидаемое случайное согласие $p_e$. Если оба почти всегда ставят «не опоздал», $p_e$ близко к 0.95, и 95 % совпадений почти ничего не добавляют.
- [ ] Каппа посчитана с ошибкой: при 95 % согласия она не может быть ниже 0.9
  > Может: каппа зависит не только от совпадений, но и от долей классов. При сильном дисбалансе высокое согласие бывает почти случайным.
- [ ] Каппа меряет точность разметчиков, а не их согласие
  > Каппа сравнивает разметчиков друг с другом и ничего не знает о правильных ответах. Точность меряют на золотом наборе.
- [ ] Каппа низкая, потому что разметчиков только двое
  > Для двух разметчиков каппа Коэна и придумана. Число разметчиков тут ни при чём.
:::

::: warn Типичные ошибки
- **Судить о разметке по доле совпадений.** При дисбалансе классов 90 % совпадений бывают и у разметчиков, отвечающих наугад. Считайте каппу — она вычитает случайное согласие.
- **Голосовать вслепую.** Большинство из трёх с одним плохим разметчиком может быть **хуже** лучшего разметчика: плохой голос перевешивает в спорных случаях. Сначала золотой набор — потом решайте, чьи голоса учитывать.
- **Показывать золотой набор разметчикам.** Если золотые отзывы узнаваемы (всегда первые, отдельный файл), разметчики размечают их внимательнее, и оценка завышена. Их подмешивают случайно и не помечают.
- **`pivot` с повторами.** Если разметчик разметил отзыв дважды, `pivot` упадёт с `ValueError: Index contains duplicate entries`. Сначала найдите дубли (`labels.duplicated(["review_id", "annotator"])`) и решите, какую метку оставить.
:::

{{practice: p-vote, vote, kappa, golden}}

## Чья разметка лежит в `topic`

В учебном наборе сначала задаётся исходная тема `topic`, затем по ней создаются текст, голоса и золотой набор. Проверьте, что дают сравнения с одной и той же исходной темой.

```python
import pandas as pd

r = pd.read_csv("reviews_text.csv").set_index("review_id")
wide = pd.read_csv("review_labels.csv").pivot(index="review_id", columns="annotator", values="label")
gold = pd.read_csv("review_gold.csv").set_index("review_id")["label"]

topic = r.loc[wide.index, "topic"]                      # итоговая тема тех же 450 отзывов
print("с золотом:", (r.loc[gold.index, "topic"] == gold).mean())
print(wide.eq(topic, axis=0).mean().round(3).to_dict())
```

Совпадение `topic` с золотом на 50 из 50 строк следует из копирования. На 450 строках совпадения с Аней, Борисом и Викой составляют 93 %, 86 % и 58 %. В следующей задаче заменим исходные темы имитированными ответами и сравним модели на тех же отложенных отзывах.

{{practice: topic-check, train-labels}}

## Практика

## task: p-vote | Сколько отзывов единогласно | warmup

Соберите код, который переводит разметку в широкую таблицу и печатает, во скольких отзывах все три разметчика выбрали одну тему.

### parsons
```python
import pandas as pd
labels = pd.read_csv("review_labels.csv")
wide = labels.pivot(index="review_id", columns="annotator", values="label")
same = wide.nunique(axis=1) == 1
print(int(same.sum()))
```

### check
```python
import pandas as _pd
_w = _pd.read_csv('review_labels.csv').pivot(index='review_id', columns='annotator', values='label')
_n = int((_w.nunique(axis=1) == 1).sum())
assert _lines == [str(_n)], f'Сейчас вывод: {_lines}. Сначала таблица, потом сравнение по строке, потом печать.'
```

### hint
`pivot` нужен раньше, чем `nunique`: считать разные темы можно только в широкой таблице.

### hint
`nunique(axis=1)` — сколько разных значений в каждой строке; единогласно — когда оно равно 1.

## task: vote | Голосование большинством | base

Переведите `review_labels.csv` в широкую таблицу `wide` (строка — отзыв, столбцы — `аня`, `борис`, `вика`) и посчитайте итоговую тему голосованием: тема, за которую не меньше двух голосов, иначе `None`. Сохраните `vote` — Series с итогом (индекс — `review_id`), `n_no_majority` — число отзывов без большинства и `share_2of3` — долю отзывов, где согласны **ровно** двое (3 знака).

### starter
```python
import pandas as pd
labels = pd.read_csv("review_labels.csv")

```

### check
```python
import pandas as _pd
w = _pd.read_csv('review_labels.csv').pivot(index='review_id', columns='annotator', values='label')
def _m(row):
    c = row.value_counts()
    return c.index[0] if c.iloc[0] >= 2 else None
v0 = w.apply(_m, axis=1)
v = need('vote', _pd.Series)
assert len(v) == len(w), f'В vote {len(v)} значений, а отзывов {len(w)}.'
v = v.reindex(w.index)
assert v.fillna('—').eq(v0.fillna('—')).all(), 'vote не совпадает с голосованием: тема с 2–3 голосами, иначе None. Индекс — review_id.'
assert need('n_no_majority') == int(v0.isna().sum()), f'n_no_majority = {need("n_no_majority")}.'
s = round(float((w.nunique(axis=1) == 2).mean()), 3)
assert close(need('share_2of3'), s, 0.0015), f'share_2of3 = {need("share_2of3")}. Ровно двое согласны — в строке ровно две разные темы.'
```

### hint
Широкая таблица — `labels.pivot(index="review_id", columns="annotator", values="label")`. Голосование — функция от строки и `wide.apply(функция, axis=1)`.

### hint
Внутри функции: `counts = row.value_counts()`; лидер — `counts.index[0]`, его голоса — `counts.iloc[0]`. Ровно двое согласны, когда в строке две разные темы: `wide.nunique(axis=1) == 2`.

### hint
```python
def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

vote = wide.apply(majority, axis=1)
n_no_majority = int(vote.isna().sum())
share_2of3 = ...
```

### solution
```python
import pandas as pd
labels = pd.read_csv("review_labels.csv")
wide = labels.pivot(index="review_id", columns="annotator", values="label")

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

vote = wide.apply(majority, axis=1)
n_no_majority = int(vote.isna().sum())
share_2of3 = round(float((wide.nunique(axis=1) == 2).mean()), 3)
print(vote.value_counts(), n_no_majority, share_2of3)
```

### explain
Из 450 отзывов в 211 все три голоса совпали, в 212 совпали ровно два, в 27 большинства нет. Эти 27 строк можно вынести на перепроверку. Условие `counts.iloc[0] > 2` оставило бы только единогласные ответы и потеряло бы 212 решений большинства.

## task: kappa | Каппа Коэна руками | base

Напишите функцию `kappa(x, y)` — каппу Коэна для двух списков меток: $p_o$ — доля совпадений, $p_e$ — сумма по всем темам произведений долей темы у `x` и у `y`, итог $(p_o - p_e) / (1 - p_e)$. Посчитайте ей каппу для пар Аня–Борис (`kappa_ab`) и Аня–Вика (`kappa_av`), 3 знака. Сверьтесь с `cohen_kappa_score`.

### starter
```python
import pandas as pd
from sklearn.metrics import cohen_kappa_score
wide = pd.read_csv("review_labels.csv").pivot(index="review_id", columns="annotator", values="label")

def kappa(x, y):
    x, y = list(x), list(y)
    ...

```

### check
```python
import pandas as _pd
from sklearn.metrics import cohen_kappa_score as _k
f = need('kappa')
t1 = ['ж', 'н', 'н', 'н', 'н', 'н', 'н', 'ж', 'н', 'н']; t2 = ['ж', 'н', 'н', 'н', 'н', 'н', 'н', 'н', 'ж', 'н']
r1 = f(t1, t2)
assert r1 is not None and close(r1, 0.375, 1e-6), f'kappa на примере из урока = {r1}, а нужно 0.375. Проверьте p_e: доли считаются отдельно для x и для y.'
assert close(f(['а', 'б', 'в'], ['а', 'б', 'в']), 1.0, 1e-9), 'При полном совпадении каппа равна 1.'
w = _pd.read_csv('review_labels.csv').pivot(index='review_id', columns='annotator', values='label')
assert close(f(w['аня'], w['вика']), _k(w['аня'], w['вика']), 1e-9), 'kappa(аня, вика) не совпадает с cohen_kappa_score. В p_e доли каждой темы берутся отдельно у x и у y и перемножаются.'
assert close(need('kappa_ab'), round(_k(w['аня'], w['борис']), 3), 0.0015), f'kappa_ab = {need("kappa_ab")}.'
assert close(need('kappa_av'), round(_k(w['аня'], w['вика']), 3), 0.0015), f'kappa_av = {need("kappa_av")}.'
```

### hint
Две части формулы: $p_o$ — `sum(a == b for a, b in zip(x, y)) / len(x)`; $p_e$ — цикл по темам из `set(x) | set(y)`.

### hint
Для темы `c` доля у первого — `x.count(c) / len(x)`, у второго — `y.count(c) / len(y)`; $p_e$ — сумма их произведений.

### hint
```python
def kappa(x, y):
    x, y = list(x), list(y)
    n = len(x)
    p_o = sum(a == b for a, b in zip(x, y)) / n
    p_e = sum((x.count(c) / n) * (y.count(c) / n) for c in set(x) | set(y))
    return ...
```

### solution
```python
import pandas as pd
from sklearn.metrics import cohen_kappa_score
wide = pd.read_csv("review_labels.csv").pivot(index="review_id", columns="annotator", values="label")

def kappa(x, y):
    x, y = list(x), list(y)
    n = len(x)
    p_o = sum(a == b for a, b in zip(x, y)) / n
    p_e = sum((x.count(c) / n) * (y.count(c) / n) for c in set(x) | set(y))
    return (p_o - p_e) / (1 - p_e)

kappa_ab = round(kappa(wide["аня"], wide["борис"]), 3)
kappa_av = round(kappa(wide["аня"], wide["вика"]), 3)
print(kappa_ab, kappa_av, round(cohen_kappa_score(wide["аня"], wide["вика"]), 3))
```

### explain
Для Ани и Бориса каппа 0,76 при доле совпадений 0,80. Для Ани и Вики — 0,47 при доле совпадений 0,55. Чтобы рассчитать ожидаемое согласие, нужны отдельные доли тем у каждого из двух разметчиков. У Вики доля «атмосферы» особенно велика.

## task: golden | Кому доверять: золотой набор | plus

Для 50 отзывов из `review_gold.csv` правильная тема известна. Посчитайте `gold_acc` — словарь «разметчик → доля верных на золотом наборе» (3 знака) и `worst` — имя худшего. Затем посчитайте `vote_gold` — долю верных у голосования трёх (отзыв без большинства — ошибка), 3 знака. Наконец, решите, что делать: сохраните `n_recheck` — сколько из 450 отзывов придётся перепроверять, если голос худшего разметчика не учитывать и брать тему, только когда два оставшихся согласны.

### starter
```python
import pandas as pd
labels = pd.read_csv("review_labels.csv")
gold = pd.read_csv("review_gold.csv").set_index("review_id")["label"]
wide = labels.pivot(index="review_id", columns="annotator", values="label")

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

```

### check
```python
import pandas as _pd
w = _pd.read_csv('review_labels.csv').pivot(index='review_id', columns='annotator', values='label')
g = _pd.read_csv('review_gold.csv').set_index('review_id')['label']
acc = {a: round(float((w.loc[g.index, a] == g).mean()), 3) for a in ['аня', 'борис', 'вика']}
got = need('gold_acc', dict)
assert all(k in got and close(got[k], v, 0.0015) for k, v in acc.items()), f'gold_acc = {got}, а нужно {acc}. Сравнивайте только 50 отзывов золотого набора: wide.loc[gold.index].'
wst = min(acc, key=acc.get)
assert need('worst') == wst, f'worst = {need("worst")!r}.'
def _m(row):
    c = row.value_counts()
    return c.index[0] if c.iloc[0] >= 2 else None
vg = w.loc[g.index, ['аня', 'борис', 'вика']].apply(_m, axis=1)
vv = round(float((vg == g).mean()), 3)
assert close(need('vote_gold'), vv, 0.0015), f'vote_gold = {need("vote_gold")}, а нужно {vv}. Отзыв без большинства (None) считается ошибкой.'
rest = [a for a in ['аня', 'борис', 'вика'] if a != wst]
assert need('n_recheck') == int((w[rest[0]] != w[rest[1]]).sum()), f'n_recheck = {need("n_recheck")}: отзывы из всех 450, где два оставшихся разметчика выбрали разные темы.'
```

### hint
Сравнение со столбцом золотых ответов: `wide.loc[gold.index, "аня"] == gold` — индексы совпадают, `.mean()` даёт долю верных.

### hint
Голосование на золотом наборе — `wide.loc[gold.index].apply(majority, axis=1)`; сравнение `== gold` для `None` даёт `False`, так что отзывы без большинства сами станут ошибками.

### hint
```python
gold_acc = {a: round(float((wide.loc[gold.index, a] == gold).mean()), 3) for a in wide.columns}
worst = min(gold_acc, key=gold_acc.get)
rest = [a for a in wide.columns if a != worst]
n_recheck = int((wide[rest[0]] != wide[rest[1]]).sum())
```

### solution
```python
import pandas as pd
labels = pd.read_csv("review_labels.csv")
gold = pd.read_csv("review_gold.csv").set_index("review_id")["label"]
wide = labels.pivot(index="review_id", columns="annotator", values="label")

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

gold_acc = {a: round(float((wide.loc[gold.index, a] == gold).mean()), 3) for a in wide.columns}
worst = min(gold_acc, key=gold_acc.get)
vote_gold = round(float((wide.loc[gold.index].apply(majority, axis=1) == gold).mean()), 3)
rest = [a for a in wide.columns if a != worst]
n_recheck = int((wide[rest[0]] != wide[rest[1]]).sum())
print(gold_acc, worst, vote_gold, n_recheck)
```

### explain
В имитации на 50 контрольных текстах точность Ани 0,92, Бориса 0,78, Вики 0,54; у голосования трёх — 0,88. При правиле «принять согласие Ани и Бориса, иначе перечитать» на проверку уйдут 88 из всех 450 отзывов. Если выбрать эталоном само голосование, Вика получит 0,60 совпадений с ним: её собственный голос участвует в результате.

## task: topic-check | Откуда взялся `topic` | base

Сопоставьте основной `topic` с тремя наборами имитированных голосов. Для тех же 450 отзывов сохраните: `n_ab_agree` — в скольких отзывах Аня и Борис выбрали одну тему; `match_ab` — долю этих отзывов, где `topic` совпадает с их общей темой; `match_vote` — долю всех 450 отзывов, где `topic` совпадает с голосованием трёх (отзыв без большинства — несовпадение). Доли — 3 знака.

### setup
```python
import pandas as pd
r = pd.read_csv("reviews_text.csv").set_index("review_id")
wide = pd.read_csv("review_labels.csv").pivot(index="review_id", columns="annotator", values="label")

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None
```

### starter
```python
topic = r.loc[wide.index, "topic"]

```

### check
```python
import pandas as _pd
w = _pd.read_csv('review_labels.csv').pivot(index='review_id', columns='annotator', values='label')
t = _pd.read_csv('reviews_text.csv').set_index('review_id').loc[w.index, 'topic']
ag = w['аня'] == w['борис']
assert need('n_ab_agree') == int(ag.sum()), f'n_ab_agree = {need("n_ab_agree")}, а нужно {int(ag.sum())}.'
m = round(float((w.loc[ag, 'аня'] == t[ag]).mean()), 3)
assert close(need('match_ab'), m, 0.0015), f'match_ab = {need("match_ab")}, а нужно {m}. Сравнивайте только отзывы, где Аня и Борис согласны.'
def _m(row):
    c = row.value_counts()
    return c.index[0] if c.iloc[0] >= 2 else None
v = round(float((w.apply(_m, axis=1) == t).mean()), 3)
assert close(need('match_vote'), v, 0.0015), f'match_vote = {need("match_vote")}, а нужно {v}.'
```

### hint
Маска согласия: `agree = wide["аня"] == wide["борис"]`; число — `int(agree.sum())`. Индексы `wide` и `topic` одинаковые, поэтому их можно сравнивать напрямую.

### hint
`match_ab = round(float((wide.loc[agree, "аня"] == topic[agree]).mean()), 3)`; голосование — `wide.apply(majority, axis=1)`, сравнение `== topic` для `None` даёт `False`.

### solution
```python
topic = r.loc[wide.index, "topic"]
agree = wide["аня"] == wide["борис"]
n_ab_agree = int(agree.sum())
match_ab = round(float((wide.loc[agree, "аня"] == topic[agree]).mean()), 3)
match_vote = round(float((wide.apply(majority, axis=1) == topic).mean()), 3)
print(n_ab_agree, match_ab, match_vote)
```

### explain
В 362 из 450 отзывов Аня и Борис согласны. Из этих 362 их общая тема совпала с `topic` в 359 случаях (0,992). Например, у R-41526 оба выбрали «обслуживание», исходная тема — «доставка». Совпадение с голосованием трёх составляет около 90 %. Сами совпадения не устанавливают, как появилась исходная тема.

## task: train-labels | Модель на разной разметке | plus

Обучите модель тем (`make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))`) на 450 размеченных отзывах трижды: на итоговой теме `topic`, на метках Ани и на метках Вики. Каждую модель проверьте на остальных 1950 отзывах по столбцу `topic`. Сохраните `acc` — словарь `{"topic": ..., "аня": ..., "вика": ...}` с долей верных ответов (3 знака).

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv").set_index("review_id")
wide = pd.read_csv("review_labels.csv").pivot(index="review_id", columns="annotator", values="label")
```

### starter
```python
train_text = r.loc[wide.index, "text"]
rest = r.drop(wide.index)                 # 1950 отзывов для проверки

```

### check
```python
import pandas as _pd
from sklearn.pipeline import make_pipeline as _mp
from sklearn.feature_extraction.text import TfidfVectorizer as _T
from sklearn.linear_model import LogisticRegression as _LR
r0 = _pd.read_csv('reviews_text.csv').set_index('review_id')
w = _pd.read_csv('review_labels.csv').pivot(index='review_id', columns='annotator', values='label')
rs = r0.drop(w.index)
labs = {'topic': r0.loc[w.index, 'topic'], 'аня': w['аня'], 'вика': w['вика']}
want = {k: round(float((_mp(_T(), _LR(max_iter=1000)).fit(r0.loc[w.index, 'text'], v).predict(rs['text']) == rs['topic']).mean()), 3) for k, v in labs.items()}
got = need('acc', dict)
assert set(got) == set(want), f'Ключи acc: {sorted(got)}, а нужны {sorted(want)}.'
for k in want:
    assert close(got[k], want[k], 0.004), f'acc[{k!r}] = {got[k]}, а нужно около {want[k]}. Обучение — на 450 размеченных, проверка — на остальных 1950 по topic.'
```

### hint
Метки для обучения — три Series с индексом `wide.index`: `r.loc[wide.index, "topic"]`, `wide["аня"]`, `wide["вика"]`. Тексты для всех трёх одни — `train_text`.

### hint
```python
labels = {"topic": r.loc[wide.index, "topic"], "аня": wide["аня"], "вика": wide["вика"]}
for name, y in labels.items():
    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(train_text, y)
    ...
```

### solution
```python
train_text = r.loc[wide.index, "text"]
rest = r.drop(wide.index)

labels = {"topic": r.loc[wide.index, "topic"], "аня": wide["аня"], "вика": wide["вика"]}
acc = {}
for name, y in labels.items():
    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(train_text, y)
    acc[name] = round(float((model.predict(rest["text"]) == rest["topic"]).mean()), 3)
print(acc)
```

### explain
При обучении на 450 исходных темах генератора точность относительно `topic` на оставшихся 1950 строках составила около 0,76. При обучении на ответах Ани получилось 0,74, на ответах Вики — 0,35. Частое ошибочное назначение «атмосферы» в последнем наборе влияет и на то, что предсказывает модель.
