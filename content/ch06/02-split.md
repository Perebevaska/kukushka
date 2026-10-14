---
title: Обучающая и тестовая выборки
lead: "В прошлом уроке мы проверяли модель на тех же доставках, на которых она училась, — это как давать на экзамене билеты, которые ученик уже видел. Учимся проверять честно: откладываем часть данных, на которые модель не смотрит, и разбираемся, что такое переобучение."
files: [deliveries.csv]
recap:
  - "Оценивать модель на данных, на которых она училась, нельзя: оценка завышена. Честная оценка — на отложенной **тестовой** выборке."
  - "`X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)` — 75 % на обучение, 25 % на тест; `random_state` делает разбиение повторяемым."
  - "`stratify=y` сохраняет долю классов одинаковой в обеих частях."
  - "`model.score(X, y)` — доля правильных ответов классификатора, то же, что `accuracy_score(y, model.predict(X))`."
  - "Переобучение: на обучении отлично, на тесте плохо — модель запомнила шум. Недообучение: плохо и там и там — модель слишком простая."
  - "Кривая «сложность → качество на train и test» показывает, где модель начинает переобучаться."
  - "Оценка на тесте — тоже выборочная: при другом разбиении она сдвигается на несколько п.п. (стандартное отклонение — около 2 п.п.). Разница между моделями в 1–2 п.п. может быть случайностью."
---

## Экзамен по известным билетам

Обучим дерево без ограничения глубины и проверим его на тех же доставках:

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]

deep = DecisionTreeClassifier(random_state=0).fit(X, y)
print(f"доля правильных ответов: {accuracy_score(y, deep.predict(X)):.1%}")
```

Около 93–94 % — намного лучше правила «пеший — опоздает» (87 %), хотя тип курьера модель по-прежнему не видит. Подозрительно. Без ограничения глубины дерево задаёт вопросы, пока почти каждая доставка не окажется в своей отдельной ветке, — то есть просто **запоминает** ответы. На новых заказах такая память бесполезна.

Чтобы узнать, как модель будет работать на новых данных, нужны данные, которых она не видела. Их берут из тех же исторических данных: часть доставок откладывают и не показывают модели при обучении.

- **обучающая выборка** (train) — на ней модель учится;
- **тестовая выборка** (test) — на ней модель проверяют, как на экзамене с новыми билетами.

## train_test_split

Разбить данные на две части случайным образом умеет функция `train_test_split` из `sklearn.model_selection`:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
print(X_train.shape, X_test.shape)
print(y_train.shape, y_test.shape)
```

- Функция возвращает **четыре** объекта в строгом порядке: признаки для обучения, признаки для теста, ответы для обучения, ответы для теста.
- `test_size=0.25` — доля строк в тесте. Обычно берут от 20 до 30 %: тест должен быть достаточно большим, чтобы оценка была надёжной, но и для обучения надо оставить побольше.
- `random_state=42` — фиксирует случайное перемешивание. С ним при каждом запуске получится одно и то же разбиение, без него — каждый раз новое. Число может быть любым, важно лишь, что оно одно и то же.

Строки `X` и `y` перемешиваются одинаково: ответ в `y_train` стоит напротив своей доставки в `X_train`. Индексы строк сохраняются, по ним можно найти доставку в исходной таблице. Разбивать можно и всю таблицу целиком: `train_test_split(ok, y, ...)` — тогда у тестовых строк останутся все столбцы, в том числе те, что не идут в модель (например, `courier` для сравнения с правилом).

::: figure train-test
Модель учится только на обучающей части. Тест она впервые видит при оценке — так же, как будущие заказы.
:::

::: sql
Похоже на то, как в SQL отбирают случайную выборку: «перемешать строки по фиксированному зерну (`ORDER BY` по хешу id), первые 25 % — в тест, остальные — в обучение». Каждая строка попадает ровно в одну часть, части не пересекаются, а при том же зерне разбиение повторяется.
:::

::: predict
```python static
from sklearn.model_selection import train_test_split
a, b = train_test_split(list(range(20)), test_size=0.25, random_state=0)
print(len(a), len(b))
```

- `5 15`
- [x] `15 5`
- `20 5`

Почему: функция возвращает сначала обучающую часть, потом тестовую. Четверть от 20 — 5 элементов в тест, остальные 15 — на обучение. Если передать один массив, частей две; если два (`X` и `y`) — четыре.
:::

{{practice: split, base-test}}

## Качество на обучении и на тесте

Теперь модель учится только на `X_train`, а проверяется на `X_test`. Для краткости воспользуемся методом `score`: у классификаторов `model.score(X, y)` — то же самое, что `accuracy_score(y, model.predict(X))`.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

for depth in [3, None]:
    model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    print(f"глубина {depth}: train {model.score(X_train, y_train):.3f}, test {model.score(X_test, y_test):.3f}")
print(f"базовая «всегда вовремя» на тесте: {(~y_test).mean():.3f}")
```

Картина поменялась:

- дерево без ограничений на обучении угадывает около 95 %, а на тесте — около 73 %. Это **хуже базовой модели** (около 77 %), которая всегда отвечает «вовремя»;
- дерево глубины 3 на обучении и на тесте даёт примерно одинаково — около 80 и 78 %. Ему можно верить: на новых доставках оно будет работать примерно так же.

::: warn
Тест — только для проверки. Модель не должна видеть тестовые строки при обучении: ни в `fit`, ни при подготовке данных. Если «подсмотреть» в тест хотя бы косвенно, оценка опять станет завышенной.
:::

::: quiz
Дерево угадывает 95 % доставок на обучении и 73 % на тесте. Базовая модель «всегда вовремя» на тесте даёт 77 %. Что это значит?

- [ ] Модель хорошая: 95 % — отличный результат
  > Число на обучении показывает, как хорошо модель выучила знакомые строки. О работе на новых заказах оно ничего не говорит.
- [x] Модель переобучилась и на новых заказах хуже простого правила
  > Большой разрыв между обучением и тестом — признак запоминания. Решает качество на тесте, а там модель проигрывает базовой.
- [ ] Тест слишком маленький, верить ему нельзя
  > Тест действительно даёт случайную оценку, но разрыв в 22 п.п. случайностью не объяснить. Это поведение самой модели. (Насколько оценка сдвигается от разбиения — в последнем разделе урока: на наших данных на несколько пунктов, не на двадцать.)
- [ ] Надо обучить модель на тесте, чтобы его результат вырос
  > Тогда тест перестанет быть новым для модели, и оценка станет такой же завышенной, как на обучении.
:::

{{practice: p-score, deep-gap, rule-test}}

## Разберём вместе: зубрила на шести доставках

Четыре доставки в обучении, две — в тесте. Признак один — расстояние.

| | км | опоздала? |
|---|---|---|
| train | 1.0 | нет |
| train | 1.3 | **да** (курьер заблудился) |
| train | 3.0 | да |
| train | 3.5 | да |
| test | 1.2 | нет |
| test | 3.2 | да |

**Простое правило** «опоздает, если больше 2 км». На обучении: верно 1.0, 3.0, 3.5, ошибка на 1.3 — **3 из 4**. На тесте: 1.2 — «нет», верно; 3.2 — «да», верно — **2 из 2**.

**Зубрила** — дерево без ограничений. Оно добивается 4 из 4 на обучении, проводя границы прямо между точками: «≤ 1.15 км — нет, больше — да»: граница прошла сразу за единственной доставкой «вовремя», чтобы «заблудившийся» курьер на 1.3 км оказался среди «да». На тесте: 1.2 больше 1.15 — ответ «да», **ошибка**. 3.2 — «да», верно. Итого **1 из 2**.

Что получилось: на обучении зубрила лучше (100 % против 75 %), на тесте — хуже (50 % против 100 %). Она выучила случайность — заблудившегося курьера — как правило. Это и есть переобучение, только в миниатюре. На тысячах доставок происходит то же самое, просто случайностей больше.

::: figure overfit-toy
Шесть доставок из разбора. Простое правило ошибается на заблудившемся курьере, но угадывает оба теста. Зубрила выделила для этого курьера отдельный отрезок — и на тестовой доставке в 1.2 км промахнулась.
:::

## Переобучение и недообучение

Большой разрыв между train и test — главный признак **переобучения** (overfitting): модель выучила не общие закономерности, а случайные особенности конкретных доставок — шум. Например, «заказ на 1.3 км с тремя позициями в 14 часов опоздал» — это случай, а не правило.

Обратная беда — **недообучение** (underfitting): модель слишком простая и плохо работает везде, даже на обучении. Дерево глубины 1 задаёт один вопрос, но в обеих ветках опозданий меньше половины, поэтому и там и там отвечает «вовремя» — то есть совпадает с базовой моделью: на графике ниже при глубине 1 линия теста лежит ровно на линии «всегда вовремя».

Чтобы найти золотую середину, построим **кривую обучения по сложности**: для разных глубин считаем качество на обучении и на тесте и рисуем обе линии.

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

depths = range(1, 16)
train_acc, test_acc = [], []
for depth in depths:
    model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    train_acc.append(model.score(X_train, y_train))
    test_acc.append(model.score(X_test, y_test))

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(depths, train_acc, marker="o", label="обучение")
ax.plot(depths, test_acc, marker="o", label="тест")
ax.axhline((~y_test).mean(), color="gray", linestyle="--", label="всегда «вовремя»")
ax.set_xlabel("максимальная глубина дерева")
ax.set_ylabel("доля правильных ответов")
ax.set_title("Чем глубже дерево, тем больше разрыв")
ax.legend()
```

Тот же график можно «пройти» ползунком:

::: widget tree-depth
Доля правильных ответов дерева на обучении и на тесте при разной глубине (доставки, тест — 25 %). Пунктир — правило «всегда вовремя».
:::

Как читать график:

- **слева** (глубина 1–2) обе линии низко и рядом — недообучение;
- **в середине** (глубина 3–5) линия теста выше всего — модель уловила закономерности;
- **справа** линия обучения уходит вверх, а линия теста — вниз: модель запоминает шум. Это переобучение.

::: note Почему на обучении не 100 %
Даже самое глубокое дерево не дотягивает до 100 % на обучении. Среди доставок есть «близнецы» — с одинаковыми расстоянием, числом позиций, обещанием и часом, но одна опоздала, а другая нет. Никакая модель на этих четырёх признаках не различит их. Это намёк: признаков не хватает (вспомните тип курьера).
:::

::: deep
Сложность есть у любой модели, не только у дерева: у дерева это глубина, у леса — число и глубина деревьев, у других моделей — свои настройки. Такие настройки, которые задаёт человек до обучения, называют **гиперпараметрами**, в отличие от параметров, которые модель подбирает сама (например, пороги в вопросах дерева — как дерево их выбирает, разберём в уроке «Решающее дерево изнутри»). Там же — подробно о гиперпараметрах дерева.
:::

{{practice: depth-curve, curve-plot, twins}}

## Стратификация: одинаковая доля классов

При случайном разбиении доля опозданий в train и test немного отличается. Если опоздания — редкость (например, 5 %), в тест может случайно попасть заметно больше или меньше редких случаев, и оценка исказится. Параметр `stratify=y` разбивает данные так, чтобы доля каждого класса в обеих частях была как во всех данных:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]

_, _, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
print(f"без stratify: train {y_tr.mean():.3f}, test {y_te.mean():.3f}")
_, _, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
print(f"со stratify:  train {y_tr.mean():.3f}, test {y_te.mean():.3f}, всего {y.mean():.3f}")
```

У нас классы не слишком несбалансированы, и разница невелика. Но `stratify=y` в задачах классификации ничего не стоит и защищает от неприятных случайностей, поэтому его часто ставят по умолчанию.

::: figure stratify-split
Игрушечный пример: 20 объектов, из них 4 единицы, в тест уходит 5. Сто разных `random_state`: без стратификации в тест попадает от 0 до 3 единиц, со `stratify=y` — всегда ровно одна, те же 20 %.
:::

::: predict
```python static
from sklearn.model_selection import train_test_split
y = [1] * 4 + [0] * 16
y_tr, y_te = train_test_split(y, test_size=0.25, random_state=0, stratify=y)
print(sum(y_te), len(y_te))
```

- `0 5`
- [x] `1 5`
- `4 5`

Почему: единиц 20 % (4 из 20). Стратификация сохраняет эту долю и в тесте: из 5 тестовых элементов ровно один — единица.
:::

::: quiz
Когда `stratify=y` особенно важен?

- [x] Когда один из классов редкий: без стратификации в тест может случайно попасть заметно больше или меньше редких случаев
  > На редком классе случайность разбиения особенно заметна, и оценка на тесте искажается. Стратификация держит долю класса одинаковой в обеих частях.
- [ ] Когда нужно, чтобы разбиение повторялось при каждом запуске
  > За повторяемость отвечает `random_state`. `stratify` управляет долями классов, а не случайностью.
- [ ] Когда данных очень много
  > На больших данных доли классов и так почти совпадают — стратификация там меньше всего нужна.
- [ ] Когда признаки в разных масштабах
  > `stratify` смотрит только на целевой признак `y`, масштабы признаков `X` ему безразличны.
:::

{{practice: strat}}

## Оценка на тесте тоже случайна

В тесте у нас 461 доставка. Доля правильных ответов на ней — такая же выборочная оценка, как доля опозданий в главе 5. При другом разбиении (другом `random_state`) в тест попадут другие доставки, и оценка сдвинется:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]

scores = []
for seed in range(20):
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=seed)
    model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_tr, y_tr)
    scores.append(model.score(X_te, y_te))
print(f"от {min(scores):.3f} до {max(scores):.3f}, среднее {np.mean(scores):.3f}, станд. отклонение {np.std(scores):.3f}")
```

Одна и та же модель на разных разбиениях получает от 75 до 83 % — разброс в несколько процентных пунктов. Стандартное отклонение около 2 п.п. — почти столько же, сколько даёт формула стандартной ошибки доли из главы 5: √(0.79 · 0.21 / 461) ≈ 0.019.

::: figure split-seeds
Одно и то же дерево глубины 3 на двадцати разных разбиениях. Каждая точка — доля правильных ответов на своём тесте; пунктир — среднее. Разница между крайними точками — больше 8 п.п.
:::

Вывод: если одна модель на тесте набрала 78.5 %, а другая — 79.2 %, это ещё не значит, что вторая лучше. Как сравнивать модели надёжнее (кросс-валидация), разберём в уроке «Честное сравнение моделей».

::: warn
Не подбирайте `random_state` разбиения, «при котором модель выглядит лучше». Это та же подгонка под тест. Число выбирают один раз до экспериментов и больше не трогают.
:::

{{practice: seeds}}

## Практика

::: warn Типичные ошибки
- **Перепутан порядок результатов.** `train_test_split` возвращает `X_train, X_test, y_train, y_test` — не «train, train, test, test».
- **Разбили `X` и `y` разными вызовами.** Строки перемешаются по-разному, ответы окажутся напротив чужих доставок.
- **Нет `random_state`.** Каждый запуск даёт новое разбиение — цифры в отчёте не повторить.
- **Глубину выбрали по тесту и по нему же отчитались.** Тест «износился»: оценка оптимистична (урок «Честное сравнение моделей» — валидация).
- **Стратификация забыта при редком классе.** Без `stratify=y` доля опозданий в тесте может заметно отличаться от общей.
:::

## task: split | Разбить данные | warmup

Разбейте `X` и `y` на обучающую и тестовую части: в тесте 25 %, `random_state=42`. Сохраните четыре переменные `X_train`, `X_test`, `y_train`, `y_test` и выведите размер обучающей и тестовой выборок (`len`) через пробел.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = ok[['distance_km', 'items', 'promised_min']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
Xtr, Xte = need('X_train', _pd.DataFrame), need('X_test', _pd.DataFrame)
ytr, yte = need('y_train', _pd.Series), need('y_test', _pd.Series)
assert len(Xte) == len(b), f'В X_test {len(Xte)} строк, а при test_size=0.25 должно быть {len(b)}. Проверьте test_size и порядок четырёх переменных: X_train, X_test, y_train, y_test.'
assert list(Xtr.index) == list(a.index) and list(Xte.index) == list(b.index), 'Строки попали не в ту часть. Проверьте random_state=42.'
assert list(ytr.index) == list(Xtr.index) and list(yte.index) == list(Xte.index), 'y_train и y_test должны соответствовать X_train и X_test — проверьте порядок переменных слева от знака =.'
assert _lines == [f'{len(a)} {len(b)}'], f'Вывод: {_lines}, а нужно две длины через пробел — сначала обучающей, потом тестовой.'
```

### hint
`X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)`.

### hint
Функция возвращает четыре объекта в строгом порядке: сначала обе части `X`, потом обе части `y`. Перепутать порядок при распаковке — частая ошибка: тогда `X_test` окажется ответами. `test_size=0.25` — четверть строк в тест.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
print(len(X_train), len(X_test))
```

## task: p-score | Train и test | warmup

Соберите программу: разбить данные, обучить дерево глубины 3 на обучающей части и вывести долю правильных ответов на обучении и на тесте (3 знака, две строки).

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0)
model.fit(X_train, y_train)
print(round(model.score(X_train, y_train), 3))
print(round(model.score(X_test, y_test), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = ok[['distance_km', 'items', 'promised_min']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
m = _T(max_depth=3, random_state=0).fit(a, c)
want = [str(round(m.score(a, c), 3)), str(round(m.score(b, e), 3))]
assert _lines == want, f'Сейчас: {_lines}, а нужно две строки: сначала обучение, потом тест.'
```

### hint
Разбиение — до создания модели, `fit` — только на обучающей части, вывод — в конце.

## task: base-test | Базовая модель на тесте | warmup

Модели сравнивают на одном и том же тесте. Разбейте данные (25 %, `random_state=42`) и сохраните в `base_test` долю правильных ответов модели «всегда вовремя» **на тестовой части** (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = ok[['distance_km', 'items', 'promised_min']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = round((~e).mean(), 3)
got = need('base_test')
assert not close(got, round((~y).mean(), 3)) or close(got, w), f'base_test = {got} — это доля по всем данным. Нужна доля только на тестовой части y_test.'
assert close(got, w), f'base_test = {got}. «Всегда вовремя» права там, где в y_test стоит False.'
```

### hint
`(~y_test).mean()` — доля доставок без опоздания в тесте.

### hint
Разбиение то же, что в прошлой задаче (25 %, `random_state=42`), но нужна только тестовая часть ответов `y_test`. Модель «всегда вовремя» права, где `y_test` равен False.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
base_test = round((~y_test).mean(), 3)
```

## task: deep-gap | Разрыв глубокого дерева | base

Обучите дерево **без ограничения глубины** (`DecisionTreeClassifier(random_state=0)`) на обучающей части признаков `distance_km`, `items`, `promised_min`, `hour`. Сохраните `train_acc`, `test_acc` (3 знака) и `gap` — разрыв в процентных пунктах (`(train_acc − test_acc) · 100`, 1 знак). В `overfit` запишите `True`, если тестовая доля ниже доли базовой модели «всегда вовремя» на тесте, иначе `False`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X = ok[['distance_km', 'items', 'promised_min', 'hour']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
m = _T(random_state=0).fit(a, c)
tr, te = round(m.score(a, c), 3), round(m.score(b, e), 3)
assert close(need('train_acc'), tr), f'train_acc = {need("train_acc")}, а нужно {tr}. Дерево — без max_depth, качество — на X_train, y_train.'
assert close(need('test_acc'), te), f'test_acc = {need("test_acc")}, а нужно {te}. Обучение — на train, оценка — на X_test, y_test.'
assert close(need('gap'), round((tr - te) * 100, 1)), f'gap = {need("gap")}. Разница в п.п.: (train_acc − test_acc) · 100.'
assert need('overfit') == bool(te < (~e).mean()), f'overfit = {need("overfit")}. Сравните test_acc с долей False в y_test.'
```

### hint
`model.score(X_train, y_train)` и `model.score(X_test, y_test)`.

### hint
Базовая модель на тесте — `(~y_test).mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(random_state=0).fit(X_train, y_train)
train_acc = round(model.score(X_train, y_train), 3)
test_acc = round(model.score(X_test, y_test), 3)
gap = round((train_acc - test_acc) * 100, 1)
overfit = bool(test_acc < (~y_test).mean())
```

### explain
Разрыв больше 20 п.п., а на тесте модель хуже, чем «всегда вовремя». Глубокое дерево выучило обучающие доставки почти наизусть, но на новых ошибается чаще, чем самый простой ответ.

## task: depth-curve | Подобрать глубину | base

Для глубин от 1 до 10 обучите деревья и соберите списки `train_scores` и `test_scores` — доли правильных ответов на обучении и тесте (без округления, по порядку глубин). В `best_depth` сохраните глубину с наибольшей долей на тесте (если таких несколько — самую маленькую).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
train_scores, test_scores = [], []

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X = ok[['distance_km', 'items', 'promised_min', 'hour']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
tr, te = [], []
for k in range(1, 11):
    m = _T(max_depth=k, random_state=0).fit(a, c)
    tr.append(m.score(a, c)); te.append(m.score(b, e))
gtr, gte = list(need('train_scores')), list(need('test_scores'))
assert len(gtr) == 10 and len(gte) == 10, f'В списках {len(gtr)} и {len(gte)} значений, а нужно по 10 — глубины от 1 до 10 включительно.'
assert all(close(x, w) for x, w in zip(gtr, tr)), 'train_scores не совпадают. Обучение — на X_train, y_train; качество — тоже на них.'
assert all(close(x, w) for x, w in zip(gte, te)), 'test_scores не совпадают. Качество на тесте — model.score(X_test, y_test).'
bd = 1 + te.index(max(te))
assert need('best_depth') == bd, f'best_depth = {need("best_depth")}. Найдите позицию максимума в test_scores и превратите её в глубину.'
```

### hint
Цикл `for depth in range(1, 11):`, внутри — обучить и добавить `model.score(...)` в оба списка через `append`.

### hint
Позиция максимума — `test_scores.index(max(test_scores))`; глубины начинаются с 1, а позиции — с 0.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
train_scores, test_scores = [], []
for depth in range(1, 11):
    model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    train_scores.append(model.score(X_train, y_train))
    test_scores.append(model.score(X_test, y_test))
best_depth = 1 + test_scores.index(max(test_scores))
```

### explain
Лучшая глубина — небольшая, а качество на тесте у глубин 3–5 почти одинаковое: разница в десятые доли процента меньше случайного разброса оценки. Заметьте: выбирая глубину по тесту, мы уже немного «подглядываем» в экзамен. Как этого избежать — отдельная валидационная выборка — в уроке «Честное сравнение моделей».

## task: curve-plot | График переобучения | base

Нарисуйте кривую «глубина → качество» для глубин 1–12: две линии `ax.plot` — сначала обучение, потом тест, с подписями `label` `"обучение"` и `"тест"`, легенду, подпись оси X `"глубина"` и любой заголовок.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X = ok[['distance_km', 'items', 'promised_min', 'hour']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
tr, te = [], []
for k in range(1, 13):
    m = _T(max_depth=k, random_state=0).fit(a, c)
    tr.append(m.score(a, c)); te.append(m.score(b, e))
ax = ax_of()
assert len(ax.lines) >= 2, f'На графике {len(ax.lines)} линий, а нужно две: обучение и тест.'
l1, l2 = ax.lines[0], ax.lines[1]
assert list(l1.get_xdata()) == list(range(1, 13)), 'По оси X — глубины от 1 до 12.'
assert all(close(u, v) for u, v in zip(l1.get_ydata(), tr)) and len(l1.get_ydata()) == 12, 'Первая линия — качество на обучающей выборке для глубин 1–12.'
assert all(close(u, v) for u, v in zip(l2.get_ydata(), te)) and len(l2.get_ydata()) == 12, 'Вторая линия — качество на тестовой выборке.'
assert l1.get_label() == 'обучение' and l2.get_label() == 'тест', f'Подписи линий: {l1.get_label()!r}, {l2.get_label()!r}, а нужны "обучение" и "тест" (параметр label).'
assert ax.get_legend() is not None, 'Добавьте легенду: ax.legend().'
assert ax.get_xlabel() == 'глубина', f'Подпись оси X: {ax.get_xlabel()!r}, а нужна "глубина".'
assert ax.get_title(), 'Добавьте заголовок.'
```

### hint
Сначала соберите два списка в цикле `for depth in range(1, 13)`, потом `ax.plot(range(1, 13), train_scores, label="обучение")`.

### hint
Внутри цикла для каждой глубины: обучить `DecisionTreeClassifier(max_depth=depth, random_state=0)` на `X_train, y_train`, затем `model.score(X_train, y_train)` и `model.score(X_test, y_test)` добавить в два списка. После цикла — две линии, `ax.legend()` и подписи.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
depths = range(1, 13)
train_scores, test_scores = [], []
for depth in depths:
    model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    train_scores.append(model.score(X_train, y_train))
    test_scores.append(model.score(X_test, y_test))
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(depths, train_scores, marker="o", label="обучение")
ax.plot(depths, test_scores, marker="o", label="тест")
ax.set_xlabel("глубина")
ax.set_ylabel("доля правильных ответов")
ax.set_title("Переобучение дерева")
ax.legend()
```

### explain
Линия обучения растёт всё время: 0.76 при глубине 1, 0.81 при 4, 0.93 при 12. Линия теста достигает вершины около глубины 4 (0.783) и потом сползает к 0.75 — ниже, чем у дерева глубины 1. После четвёртого уровня каждый новый вопрос дерева — это уже не закономерность, а запоминание отдельных доставок.

## task: strat | Стратификация | base

Разбейте данные дважды (25 %, `random_state=42`): без стратификации и со `stratify=y`. Сохраните доли опозданий в тестовой части: `late_plain` и `late_strat` (3 знака), а в `late_all` — долю опозданий во всех данных (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = ok[['distance_km', 'items', 'promised_min']]
y = ok['actual_min'] > ok['promised_min']
p = round(_tts(X, y, test_size=0.25, random_state=42)[3].mean(), 3)
s = round(_tts(X, y, test_size=0.25, random_state=42, stratify=y)[3].mean(), 3)
assert close(need('late_all'), round(y.mean(), 3)), f'late_all = {need("late_all")}. Это доля True во всём y.'
assert close(need('late_plain'), p), f'late_plain = {need("late_plain")}, а нужно {p}. Доля True в y_test при разбиении без stratify.'
assert close(need('late_strat'), s), f'late_strat = {need("late_strat")}. Проверьте stratify=y и что берёте y_test, а не y_train.'
```

### hint
`y_test` — четвёртый объект, который возвращает `train_test_split`. Доля опозданий — `y_test.mean()`.

### hint
Остальные три объекта из `train_test_split` в этой задаче не нужны, их можно принять в `_`: `_, _, _, y_test = train_test_split(...)`. Во втором вызове добавьте `stratify=y` — тогда доля опозданий в тесте почти совпадёт с долей во всех данных.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
_, _, _, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
late_plain = round(y_test.mean(), 3)
_, _, _, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
late_strat = round(y_test.mean(), 3)
late_all = round(y.mean(), 3)
```

### explain
Со стратификацией доля опозданий в тесте совпадает с общей до второго знака (0.239 против 0.240), без неё — 0.232, почти на 1 п.п. меньше. Для редких классов разница была бы заметнее.

## task: seeds | Разброс оценки | plus

Проверьте, насколько оценка зависит от разбиения. Для `random_state` разбиения от 0 до 29 обучите дерево глубины 3 и соберите список `scores` долей правильных ответов на тесте. Сохраните `low`, `high` — минимум и максимум, `spread` — разницу `high − low` в п.п. (1 знак). `low` и `high` — 3 знака; `spread` считайте из уже округлённых `low` и `high`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X = ok[['distance_km', 'items', 'promised_min', 'hour']]
y = ok['actual_min'] > ok['promised_min']
sc = []
for s in range(30):
    a, b, c, e = _tts(X, y, test_size=0.25, random_state=s)
    sc.append(_T(max_depth=3, random_state=0).fit(a, c).score(b, e))
got = list(need('scores'))
assert len(got) == 30, f'В scores {len(got)} значений, а нужно 30 — random_state от 0 до 29.'
assert all(close(u, v) for u, v in zip(got, sc)), 'scores не совпадают. В цикле меняется random_state разбиения, у дерева — всегда random_state=0.'
lo, hi = round(min(sc), 3), round(max(sc), 3)
assert close(need('low'), lo) and close(need('high'), hi), f'low, high = {need("low")}, {need("high")}, а нужно {lo}, {hi}.'
assert close(need('spread'), round((hi - lo) * 100, 1)), f'spread = {need("spread")}. Это (high − low) · 100.'
```

### hint
`for seed in range(30):` — внутри `train_test_split(X, y, test_size=0.25, random_state=seed)`, обучение и `scores.append(model.score(X_test, y_test))`.

### hint
Важно: меняется только `random_state` разбиения (`seed`), а у дерева он остаётся `random_state=0` — иначе вы будете измерять сразу два источника случайности. После цикла `min(scores)` и `max(scores)` округлите до 3 знаков, а `spread` посчитайте из округлённых значений.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
scores = []
for seed in range(30):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
    scores.append(model.score(X_test, y_test))
low, high = round(min(scores), 3), round(max(scores), 3)
spread = round((high - low) * 100, 1)
```

### explain
Одна и та же модель получает оценки с разбросом около 10 п.п. — только из-за того, какие доставки попали в тест. Сравнивая две модели, разбивайте данные для них одинаково и не придавайте значения разнице в 1–2 п.п.

## task: rule-test | Правило против моделей на тесте | plus

Сравните на одном тесте (25 %, `random_state=42`) три подхода: правило «пеший — опоздает», дерево глубины 3 и дерево без ограничения глубины (оба — на признаках `distance_km`, `items`, `promised_min`, `hour`). Сохраните словарь `results` с ключами `"правило"`, `"дерево 3"`, `"дерево без ограничений"` и долями правильных ответов на тесте (3 знака), а в `winner` — ключ с наибольшей долей.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
cols = ["distance_km", "items", "promised_min", "hour"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
cols = ['distance_km', 'items', 'promised_min', 'hour']
tr, te = _tts(ok, test_size=0.25, random_state=42)
ytr, yte = y[tr.index], y[te.index]
w = {'правило': round(((te['courier'] == 'пеший') == yte).mean(), 3),
     'дерево 3': round(_T(max_depth=3, random_state=0).fit(tr[cols], ytr).score(te[cols], yte), 3),
     'дерево без ограничений': round(_T(random_state=0).fit(tr[cols], ytr).score(te[cols], yte), 3)}
r = need('results', dict)
assert set(r) == set(w), f'Ключи results: {sorted(r)}, а нужны {sorted(w)}.'
for k in w:
    assert close(r[k], w[k]), f'results[{k!r}] = {r[k]}, а нужно {w[k]}. ' + ('Правило оценивайте только на тестовых доставках.' if k == 'правило' else 'Обучение — на train, оценка — на test.')
assert need('winner') == max(w, key=w.get), f'winner = {need("winner")!r}. Это ключ results с наибольшей долей.'
```

### hint
Разбейте всю таблицу `ok` вместе с `y`: `train, test, y_train, y_test = train_test_split(ok, y, test_size=0.25, random_state=42)`. Тогда у тестовых доставок есть и признаки, и столбец `courier`.

### hint
Правило на тесте: `((test["courier"] == "пеший") == y_test).mean()`. Деревья: `fit(train[cols], y_train)`, `score(test[cols], y_test)`.

### hint
Ключ с наибольшим значением: `max(results, key=results.get)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
cols = ["distance_km", "items", "promised_min", "hour"]
train, test, y_train, y_test = train_test_split(ok, y, test_size=0.25, random_state=42)
results = {"правило": round(((test["courier"] == "пеший") == y_test).mean(), 3)}
for name, depth in [("дерево 3", 3), ("дерево без ограничений", None)]:
    model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(train[cols], y_train)
    results[name] = round(model.score(test[cols], y_test), 3)
winner = max(results, key=results.get)
```

### explain
На тесте правило аналитика выигрывает с большим отрывом — около 90 % против 78 % у лучшего дерева. Модель не видит тип курьера, и никакая глубина этого не заменит. Разбиение одно и то же для всех подходов — только так сравнение честное.

## task: twins | Потолок для любой модели | star

Почему даже глубокое дерево не набирает 100 % на обучении? Найдите в обучающей части «близнецов» — доставки с одинаковыми значениями всех четырёх признаков. Для каждой группы близнецов лучшее, что может сделать любая модель, — ответить её большинством. Посчитайте `ceiling` — долю обучающих доставок, которые угадает такой «идеальный запоминатель» (3 знака), и `deep_train` — долю правильных ответов на обучении у дерева без ограничения глубины (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
ok["late"] = ok["actual_min"] > ok["promised_min"]
cols = ["distance_km", "items", "promised_min", "hour"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
ok['late'] = ok['actual_min'] > ok['promised_min']
cols = ['distance_km', 'items', 'promised_min', 'hour']
tr, te = _tts(ok, test_size=0.25, random_state=42)
g = tr.groupby(cols)['late'].agg(['sum', 'size'])
c = round((g['sum'].where(g['sum'] > g['size'] - g['sum'], g['size'] - g['sum'])).sum() / len(tr), 3)
dt = round(_T(random_state=0).fit(tr[cols], tr['late']).score(tr[cols], tr['late']), 3)
assert close(need('deep_train'), dt), f'deep_train = {need("deep_train")}, а нужно {dt}.'
assert close(need('ceiling'), c), f'ceiling = {need("ceiling")}. В каждой группе одинаковых признаков угадываются только доставки большинства: max(опоздавших, вовремя).'
```

### hint
Сгруппируйте по всем четырём признакам: `g = train.groupby(cols)["late"].agg(["sum", "size"])` — в группе `sum` опозданий из `size` доставок.

### hint
В группе угадываются `max(sum, size − sum)` доставок. Поэлементный максимум двух Series: `pd.concat([a, b], axis=1).max(axis=1)`. Сложите и разделите на `len(train)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
ok["late"] = ok["actual_min"] > ok["promised_min"]
cols = ["distance_km", "items", "promised_min", "hour"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)
g = train.groupby(cols)["late"].agg(["sum", "size"])
right = pd.concat([g["sum"], g["size"] - g["sum"]], axis=1).max(axis=1)
ceiling = round(right.sum() / len(train), 3)
model = DecisionTreeClassifier(random_state=0).fit(train[cols], train["late"])
deep_train = round(model.score(train[cols], train["late"]), 3)
print(ceiling, deep_train)
```

### explain
Числа совпадают: глубокое дерево дошло до потолка — запомнило всё, что вообще можно запомнить по этим признакам. Остальные ошибки на обучении — близнецы с разными ответами. Значит, рост качества даст не более сложная модель, а новые признаки.
