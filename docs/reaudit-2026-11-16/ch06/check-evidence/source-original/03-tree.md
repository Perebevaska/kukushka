---
title: Решающее дерево изнутри
lead: "Дерево — модель, которую можно прочитать как инструкцию: «если обещали 30 минут и в заказе больше двух позиций — скорее опоздает». Разбираемся, как дерево выбирает вопросы, как его нарисовать, откуда берётся вероятность опоздания и какими настройками удержать дерево от переобучения."
files: [deliveries.csv]
recap:
  - "Дерево — вложенные вопросы «признак ≤ порог?». В каждом листе ответ — класс большинства среди обучающих объектов, попавших в лист."
  - "Неоднородность Джини: 1 − p² − (1 − p)², где p — доля опозданий в группе. 0 — группа однородна, 0.5 — поровну."
  - "Дерево перебирает все признаки и пороги и выбирает вопрос, после которого взвешенная неоднородность частей меньше всего."
  - "`export_text(model, feature_names=...)` — дерево текстом, `plot_tree(model, feature_names=..., filled=True)` — картинкой."
  - "`model.predict_proba(X)[:, 1]` — вероятность класса `True`: доля опозданий в листе, куда попала доставка."
  - "Против переобучения: `max_depth` (глубина), `min_samples_leaf` (минимум объектов в листе), `max_leaf_nodes` (число листьев)."
  - "`model.feature_importances_` — насколько каждый признак уменьшил неоднородность; в сумме 1."
---

## Дерево как инструкция

В прошлых уроках дерево было для нас чёрным ящиком. Заглянем внутрь. Функция `export_text` печатает обученное дерево как вложенные правила:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)

model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
print(export_text(model, feature_names=cols, show_weights=True))
```

Как читать:

- каждая строка `|---` — вопрос «признак ≤ порог?»; отступ показывает уровень вложенности. Первый вопрос (**корень** дерева) — `promised_min <= 37.50`, то есть «обещали 30 минут?»;
- строки с `weights` — **листья**, конечные группы. `weights: [65.00, 122.00]` — в лист попало 65 обучающих доставок вовремя и 122 опоздавших (порядок — как в `model.classes_`: сначала `False`, потом `True`);
- `class` — ответ листа: класс большинства;
- числа `weights` в листьях печатает параметр `show_weights=True`; без него в листе был бы только `class`.

Ветка «обещали 30 минут, больше двух позиций, дальше 0.75 км» — единственная большая группа (187 доставок), где опозданий больше половины; лист из 6 очень дальних заказов (дальше 11.9 км) тоже отвечает «опоздает», но он слишком мал, чтобы на него опираться. Так дерево и находит рискованные заказы.

Пороги вроде 37.50 и 2.50 — середины между соседними значениями признака: обещание бывает 30 или 45, и дерево ставит границу посередине.

{{practice: p-text}}

## Как дерево выбирает вопрос

Хороший вопрос разделяет доставки на группы, в каждой из которых почти все ответы одинаковы. Меру «перемешанности» группы называют **неоднородностью** (impurity). В sklearn по умолчанию — **неоднородность Джини**:

$$
\text{Gini} = 1 - p^2 - (1 - p)^2
$$

где $p$ — доля опозданий в группе.

- все доставки вовремя ($p = 0$) или все опоздали ($p = 1$) — $\text{Gini} = 0$, группа однородна;
- опозданий ровно половина ($p = 0.5$) — $\text{Gini} = 0.5$, хуже некуда.

::: tip Аналогия
Представьте пакет зёрен, где перемешаны две обжарки — светлая и тёмная. Вытащите наугад зерно, верните его и вытащите ещё одно: с какой вероятностью два зерна окажутся разными? Если обжарка одна, вероятность 0 — пакет «чистый»; хуже всего, когда зёрен поровну, — тогда 0.5. Это не просто образ: формула Джини ровно эту вероятность и считает.
:::

::: predict
```python static
p = 0.25
print(round(1 - p**2 - (1 - p)**2, 3))
```

- `0.25`
- [x] `0.375`
- `0.5`

Почему: 1 − 0.0625 − 0.5625 = 0.375. Группа с четвертью опозданий заметно однороднее, чем «пополам» (0.5), но далеко не чистая.
:::

### Разберём вместе: два вопроса на десяти доставках

Десять доставок, четыре опоздали. До вопроса p = 0.4, Gini = 1 − 0.16 − 0.36 = **0.48**.

**Вопрос A** делит их на 6 и 4. Слева одно опоздание из шести, справа — три из четырёх.

- Слева: p = 1/6, Gini = 1 − (1/6)² − (5/6)² = 1 − 0.028 − 0.694 = **0.278**.
- Справа: p = 3/4, Gini = 1 − 0.5625 − 0.0625 = **0.375**.
- Взвешенно: 0.6 × 0.278 + 0.4 × 0.375 = 0.167 + 0.150 = **0.317**.

**Вопрос B** делит на 5 и 5, и в каждой половине по два опоздания: p = 0.4 слева и справа, Gini 0.48 и 0.48, взвешенно — те же **0.48**.

Что получилось: вопрос A снизил неоднородность с 0.48 до 0.317, вопрос B — ни на сколько. B разрезал группу, но не разделил опоздания и доставки вовремя: доли в частях такие же, как были. Дерево выберет A. Неважно, насколько «круглый» порог или красиво звучит признак, — важно, насколько чище стали части.

::: figure gini-toy
Разбор на десяти доставках. Вопрос A отделяет опоздания от доставок вовремя — взвешенный Gini падает до 0.317. Вопрос B режет группу пополам, но доли в частях прежние — Gini остаётся 0.48.
:::

Вопрос делит группу на две части. Его качество — **взвешенная** неоднородность частей: Gini каждой части, умноженный на её долю объектов. Посчитаем руками для корня нашего дерева:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

def gini(s):
    p = s.mean()
    return 1 - p**2 - (1 - p)**2

left = train.loc[train["promised_min"] <= 37.5, "late"]
right = train.loc[train["promised_min"] > 37.5, "late"]
split = (len(left) * gini(left) + len(right) * gini(right)) / len(train)
print(f"до вопроса: {gini(train['late']):.3f}")
print(f"слева {len(left)} доставок, опозданий {left.mean():.1%}, Gini {gini(left):.3f}")
print(f"справа {len(right)} доставок, опозданий {right.mean():.1%}, Gini {gini(right):.3f}")
print(f"после вопроса (взвешенно): {split:.3f}")
```

Было 0.367, стало 0.316: вопрос отделил рискованные 30-минутные заказы (опозданий около 46 %) от спокойных (около 12 %).

::: figure tree-split
Первый вопрос дерева на обучающих доставках: обещание 30 минут отделяет рискованные заказы от спокойных и уменьшает неоднородность.
:::

Дерево поступает просто и упорно: перебирает **все** признаки и **все** возможные пороги, для каждого считает взвешенную неоднородность и выбирает вопрос с наименьшей. Сравним несколько кандидатов:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
ok["late"] = ok["actual_min"] > ok["promised_min"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

def gini(s):
    p = s.mean()
    return 1 - p**2 - (1 - p)**2

for col, t in [("promised_min", 37.5), ("distance_km", 2.0), ("items", 3.5), ("hour", 17.5)]:
    left = train.loc[train[col] <= t, "late"]
    right = train.loc[train[col] > t, "late"]
    split = (len(left) * gini(left) + len(right) * gini(right)) / len(train)
    print(f"{col} <= {t}: {split:.4f}")
```

Победил вопрос про обещание. Потом то же самое повторяется отдельно в левой и в правой части — и так, пока не достигнут предел глубины или группы не станут однородными. Поэтому дерево и называют **жадным**: на каждом шаге оно берёт лучший вопрос прямо сейчас, не заглядывая вперёд.

::: sql
Один шаг дерева похож на перебор запросов `SELECT promised_min <= 37.5 AS grp, AVG(late), COUNT(*) ... GROUP BY grp` для каждого столбца и порога — и выбор того, где группы получились «чище» всего.
:::

::: deep
Вместо Джини можно взять **энтропию** — `DecisionTreeClassifier(criterion="entropy")`. Формула другая, смысл тот же: мера перемешанности группы. На практике деревья почти всегда получаются похожими.
:::

::: quiz
Вопрос отрезает от 1 000 доставок три — все вовремя, их Gini равен 0. В остальных 997 доля опозданий почти не изменилась. Почему дерево вряд ли выберет такой вопрос?

- [x] Неоднородность частей взвешивается по их размеру: три чистые доставки весят 0.3 %, и общий Gini почти не падает
  > Качество вопроса — взвешенная сумма. Огромная часть с прежней перемешанностью перевешивает крошечную чистую.
- [ ] Выберет: часть с Gini 0 — лучший возможный результат
  > Так было бы при простом среднем Gini двух частей. Именно поэтому дерево считает взвешенно — иначе оно гонялось бы за крошечными чистыми группами.
- [ ] Потому что листья меньше пяти объектов sklearn запрещает по умолчанию
  > По умолчанию `min_samples_leaf=1`, и такой лист разрешён. Вопрос проигрывает по неоднородности, а не по правилам.
- [ ] Потому что дерево ставит пороги только посередине шкалы признака
  > Порог ставится посередине между **соседними** значениями, и он может отрезать любую часть, хоть три строки.
:::

{{practice: gini, best-threshold, split-gini}}

## Дерево картинкой

Функция `plot_tree` рисует то же дерево в виде схемы:

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train)

fig, ax = plt.subplots(figsize=(11, 5))
plot_tree(model, feature_names=cols, class_names=["вовремя", "опоздает"], filled=True, ax=ax)
```

В каждом прямоугольнике: вопрос, `gini` — неоднородность, `samples` — сколько обучающих доставок сюда попало, `value` — сколько из них каждого класса, `class` — ответ. С `filled=True` цвет показывает класс большинства, а насыщенность — насколько группа однородна. Влево идут доставки, для которых ответ на вопрос «да».

Картинка удобна для глубины 2–3. Глубже прямоугольники становятся нечитаемыми — тогда лучше `export_text`.

{{practice: draw}}

## Вероятность — доля в листе

Кроме ответа «да/нет» дерево умеет давать вероятность. Метод `predict_proba` возвращает таблицу из двух столбцов: вероятность `False` и вероятность `True` (порядок — как в `model.classes_`):

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)

print(model.classes_)
proba = model.predict_proba(X_test.head(4))
print(proba.round(3))
print(model.predict(X_test.head(4)))
X_test.head(4)
```

Откуда 0.652 у четвёртой доставки (1.8 км, 3 позиции, обещали 30 минут)? Она попадает в лист `[65, 122]` из первого раздела: 122 / (65 + 122) ≈ 0.652. Вероятность дерева — это просто **доля опозданий среди обучающих доставок в том же листе**. Поэтому у дерева мало разных вероятностей — по одной на лист.

::: figure tree-path
Дерево глубины 3 из урока. Синим — путь четвёртой тестовой доставки: три вопроса приводят её в лист, где из 187 обучающих доставок 122 опоздали. Отсюда и вероятность 0.652.
:::

`predict` отвечает `True`, если вероятность `True` больше 0.5. Вероятность полезнее: по ней можно ранжировать заказы по риску или выбрать свой порог («предупреждать, если риск выше 40 %»). Подробнее о порогах — в уроке «Логистическая регрессия и вероятности».

Чтобы взять вероятность опоздания для всех доставок, берут второй столбец: `model.predict_proba(X)[:, 1]`.

::: predict
```python static
from sklearn.tree import DecisionTreeClassifier
X = [[1], [1], [1], [2]]
y = [0, 0, 1, 1]
model = DecisionTreeClassifier(max_depth=1, random_state=0).fit(X, y)
print(round(model.predict_proba([[1]])[0, 1], 2), model.predict([[1]])[0])
```

- `1.0 1`
- [x] `0.33 0`
- `0.5 0`

Почему: вопрос `x <= 1.5` отделяет три объекта с x = 1. Среди них одна единица из трёх — вероятность 1/3, а ответ — большинство, 0.
:::

::: quiz
В лист дерева попали 40 обучающих доставок, 10 из них опоздали. Что вернёт `predict_proba` для новой доставки, попавшей в этот лист?

- [x] 0.25 — долю опозданий среди обучающих доставок листа
  > Вероятность в дереве — просто доля класса в листе. Поэтому она меняется ступеньками и бывает очень грубой в маленьких листьях.
- [ ] 1, раз доставка попала в «опаздывающий» лист
  > Лист с 25 % опозданий — «скорее вовремя»: `predict` даст False, а вероятность 0.25.
- [ ] 10 — число опоздавших
  > Вероятность — доля, а не количество.
- [ ] Вероятность считается по расстоянию до порога
  > Дерево не смотрит, насколько далеко значение от порога: все доставки листа получают одну вероятность.
:::

{{practice: proba, leaf-share}}

## Настройки против переобучения

Без ограничений дерево растёт, пока листья не станут однородными, и запоминает шум — это мы видели в прошлом уроке. Рост дерева сдерживают **гиперпараметры** — настройки, которые человек задаёт до обучения, а не модель находит в данных (кратко они упоминались в уроке «Обучающая и тестовая выборки»):

| гиперпараметр | что ограничивает | эффект |
|---|---|---|
| `max_depth` | число вопросов подряд | дерево не уходит в мелкие детали |
| `min_samples_leaf` | минимум обучающих объектов в листе | нет листьев из 1–2 случайных доставок, вероятности надёжнее |
| `max_leaf_nodes` | общее число листьев | дерево растёт там, где это даёт больше всего пользы |

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)

for params in [{}, {"max_depth": 3}, {"min_samples_leaf": 50}, {"max_leaf_nodes": 8}]:
    m = DecisionTreeClassifier(random_state=0, **params).fit(X_train, y_train)
    print(params, "листьев", m.get_n_leaves(), "train", round(m.score(X_train, y_train), 3), "test", round(m.score(X_test, y_test), 3))
```

`m.get_n_leaves()` — число листьев. Запись `**params` подставляет словарь как именованные аргументы: `DecisionTreeClassifier(random_state=0, **{"max_depth": 3})` — то же, что `DecisionTreeClassifier(random_state=0, max_depth=3)`.

Дерево без ограничений вырастило около 400 листьев — почти по листу на каждые три доставки. Любое из ограничений сокращает его до 7–21 листа, разрыв train/test почти исчезает, а качество на тесте растёт. Какое ограничение выбрать и с каким значением — подбирают по данным; как делать это без подглядывания в тест — в уроке «Честное сравнение моделей».

::: tip
`min_samples_leaf` особенно полезен, когда нужны вероятности: в листе из трёх доставок «вероятность» 0.67 — это два случая из трёх, ей нельзя доверять. В листе из 50 доставок доля уже похожа на правду.
:::

{{practice: leaf-size}}

## Какие признаки важны

`model.feature_importances_` показывает, какой вклад каждый признак внёс в уменьшение неоднородности по всем вопросам дерева. Сумма важностей — 1.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)

pd.Series(model.feature_importances_, index=cols).sort_values(ascending=False).round(3)
```

Главный признак — обещанное время, час не использован вовсе (важность 0): ни один вопрос дерева глубины 3 про него не спрашивает.

Теперь дадим дереву то, чего ему не хватало, — тип курьера. Модели sklearn принимают только числа, поэтому сделаем **признак-флаг**: 1, если курьер пеший, и 0 иначе.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
ok["walk"] = (ok["courier"] == "пеший").astype(int)
cols = ["distance_km", "items", "promised_min", "hour", "walk"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)

print(f"test: {model.score(X_test, y_test):.3f}")
print(pd.Series(model.feature_importances_, index=cols).sort_values(ascending=False).round(3))
```

Качество на тесте подскочило с 78 до 90 %, а флаг «пеший» забрал около трёх четвертей всей важности — дерево само «открыло» правило аналитика и первым вопросом спрашивает про курьера. Но заметно обойти само правило (на этом тесте — тоже около 90 %) у него не вышло: одна причина доминирует, и уточнения дают немного. Как превращать в числа любые текстовые признаки, а не только один флаг, — в следующем уроке.

::: warn
Важность — не причинность. Высокая важность значит «модель часто опиралась на этот признак», а не «этот признак вызывает опоздания». Если два признака дублируют друг друга (расстояние и обещанное время, которое назначают по расстоянию), важность может достаться любому из них.
:::

::: warn Типичные ошибки
- **Gini без весов.** Среднее Gini двух частей без учёта их размеров переоценивает вопросы, которые отрезают крошечную «чистую» группу.
- **Порядок в `weights`.** Сначала `False`, потом `True` — как в `model.classes_`. Перепутав, вы прочитаете «вовремя» как «опоздала».
- **Вероятность из маленького листа.** Лист с 3 доставками и p = 1.0 — это 3 случая, а не уверенность; помогает `min_samples_leaf`.
- **Важность = причина.** `feature_importances_` говорит, какие вопросы задавало дерево, а не что вызывает опоздания.
:::

{{practice: walk-flag}}

## Практика

## task: gini | Функция Джини | warmup

Напишите функцию `gini_p(p)`, которая по **доле** опозданий `p` (числу от 0 до 1) возвращает неоднородность Джини. Имя другое, чем у `gini(s)` из теории: та принимает столбец True/False и сама считает долю, а эта — сразу долю. Затем сохраните в `g_train` неоднородность всей обучающей выборки (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
y_train, y_test = train_test_split(y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
ytr = _tts(y, test_size=0.25, random_state=42)[0]
f = need('gini_p')
assert callable(f), 'gini_p должна быть функцией: def gini_p(p): ...'
for p in (0, 1, 0.5, 0.25, 0.1):
    assert close(f(p), 1 - p**2 - (1 - p)**2), f'gini_p({p}) = {f(p)}. Формула: 1 − p² − (1 − p)².'
p = ytr.mean()
assert close(need('g_train'), round(1 - p**2 - (1 - p)**2, 3)), f'g_train = {need("g_train")}. Подставьте в gini_p долю опозданий в y_train.'
```

### hint
`def gini_p(p): return 1 - p**2 - (1 - p)**2`. Доля опозданий — `y_train.mean()`.

### hint
Проверьте функцию на крайних случаях: `gini_p(0)` и `gini_p(1)` должны дать 0 (в группе все одинаковые), `gini_p(0.5)` — 0.5 (максимальный беспорядок). Если так и есть, подставьте долю опозданий в обучающей части.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
y_train, y_test = train_test_split(y, test_size=0.25, random_state=42)

def gini_p(p):
    return 1 - p**2 - (1 - p)**2

g_train = round(gini_p(y_train.mean()), 3)
```

## task: p-text | Дерево текстом | warmup

Соберите программу: обучить дерево глубины 2 на обучающей части и напечатать его правила с названиями признаков.

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
cols = ["distance_km", "items", "promised_min"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train)
print(export_text(model, feature_names=cols))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T, export_text as _et
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
cols = ['distance_km', 'items', 'promised_min']
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(ok[cols], y, test_size=0.25, random_state=42)
want = [x.strip() for x in _et(_T(max_depth=2, random_state=0).fit(a, c), feature_names=cols).splitlines() if x.strip()]
assert _lines == want, 'Вывод не совпадает с правилами дерева. Проверьте порядок: данные → разбиение → обучение → печать.'
```

### hint
`cols` нужен раньше, чем разбиение; `export_text` — только после обучения.

## task: split-gini | Качество одного вопроса | base

Посчитайте руками, насколько хорош вопрос `distance_km <= 2.0` на обучающей выборке. Сохраните `g_left` и `g_right` — неоднородность Джини левой (`<= 2.0`) и правой частей, и `g_split` — взвешенную неоднородность после вопроса (все — 3 знака). В `better` запишите `True`, если этот вопрос лучше вопроса про обещание (`promised_min <= 37.5`, взвешенная неоднородность 0.316), иначе `False`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

def gini(s):
    p = s.mean()
    return 1 - p**2 - (1 - p)**2

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)].copy()
ok['late'] = ok['actual_min'] > ok['promised_min']
tr = _tts(ok, test_size=0.25, random_state=42)[0]
def G(s):
    p = s.mean(); return 1 - p**2 - (1 - p)**2
l, r = tr.loc[tr['distance_km'] <= 2.0, 'late'], tr.loc[tr['distance_km'] > 2.0, 'late']
gs = (len(l) * G(l) + len(r) * G(r)) / len(tr)
assert close(need('g_left'), round(G(l), 3)) and close(need('g_right'), round(G(r), 3)), f'g_left, g_right = {need("g_left")}, {need("g_right")}, а нужно {round(G(l), 3)}, {round(G(r), 3)}. Части — по обучающей выборке train.'
assert not close(need('g_split'), round((G(l) + G(r)) / 2, 3)) or close(need('g_split'), round(gs, 3)), 'g_split — не простое среднее двух Gini, а взвешенное по числу доставок в каждой части.'
assert close(need('g_split'), round(gs, 3)), f'g_split = {need("g_split")}, а нужно {round(gs, 3)}.'
assert need('better') == bool(gs < 0.316), f'better = {need("better")}. Меньшая взвешенная неоднородность — лучший вопрос.'
```

### hint
`left = train.loc[train["distance_km"] <= 2.0, "late"]`, аналогично `right` с `> 2.0`.

### hint
Взвешенная неоднородность: `(len(left) * gini(left) + len(right) * gini(right)) / len(train)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

def gini(s):
    p = s.mean()
    return 1 - p**2 - (1 - p)**2

left = train.loc[train["distance_km"] <= 2.0, "late"]
right = train.loc[train["distance_km"] > 2.0, "late"]
g_left, g_right = round(gini(left), 3), round(gini(right), 3)
g_split = round((len(left) * gini(left) + len(right) * gini(right)) / len(train), 3)
better = g_split < 0.316
```

### explain
Вопрос про расстояние почти так же хорош, как про обещание, — неудивительно: обещание назначают по расстоянию, и короткие доставки — это в основном 30-минутные. Разница 0.320 против 0.316 крошечная, но дерево всегда берёт строгий минимум: оно не взвешивает «почти одинаково», а выбирает лучший из вопросов, даже если он лучше на тысячные.

## task: proba | Вероятность опоздания | base

Обучите дерево глубины 3 и сохраните в `p_late` вероятности опоздания для всех тестовых доставок (массив из второго столбца `predict_proba`). Сохраните `n_risky` — сколько тестовых доставок имеют вероятность опоздания не меньше 0.6, и `n_values` — сколько **разных** значений встречается в `p_late`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
cols = ['distance_km', 'items', 'promised_min', 'hour']
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(ok[cols], y, test_size=0.25, random_state=42)
p = _T(max_depth=3, random_state=0).fit(a, c).predict_proba(b)[:, 1]
got = _np.asarray(need('p_late'), dtype=float)
assert got.shape == p.shape, f'В p_late {got.size} значений, а тестовых доставок {len(p)}. Нужен один столбец для всего X_test.'
assert _np.allclose(got, p), 'p_late не совпадает. Берите второй столбец — вероятность True: predict_proba(X_test)[:, 1].'
assert need('n_risky') == int((p >= 0.6).sum()), f'n_risky = {need("n_risky")}. Условие — «не меньше 0.6», то есть >= 0.6.'
assert need('n_values') == len(_np.unique(p)), f'n_values = {need("n_values")}. Разные значения — np.unique(p_late) или pd.Series(p_late).nunique().'
```

### hint
`p_late = model.predict_proba(X_test)[:, 1]`; число подходящих — `(p_late >= 0.6).sum()`.

### hint
Разных значений столько, сколько листьев, в которые попали тестовые доставки: `pd.Series(p_late).nunique()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
p_late = model.predict_proba(X_test)[:, 1]
n_risky = int((p_late >= 0.6).sum())
n_values = pd.Series(p_late).nunique()
```

### explain
У дерева глубины 3 не больше 8 листьев — значит, не больше 8 разных вероятностей. Все доставки одного листа получают одинаковый риск.

## task: draw | Нарисовать дерево | base

Обучите дерево с `max_leaf_nodes=4` на обучающей части и нарисуйте его через `plot_tree` с названиями признаков, подписями классов `"вовремя"` и `"опоздает"` и заливкой цветом. Сохраните число листьев в `n_leaves`.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
cols = ['distance_km', 'items', 'promised_min', 'hour']
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(ok[cols], y, test_size=0.25, random_state=42)
m = _T(max_leaf_nodes=4, random_state=0).fit(a, c)
assert need('n_leaves') == m.get_n_leaves(), f'n_leaves = {need("n_leaves")}. Число листьев — model.get_n_leaves().'
ax = ax_of()
boxes = [t for t in ax.texts if t.get_bbox_patch() is not None]
texts = [t.get_text() for t in boxes]
assert len(texts) == m.tree_.node_count, f'На рисунке {len(texts)} прямоугольников, а в дереве с max_leaf_nodes=4 их {m.tree_.node_count}.'
assert any('promised_min' in t for t in texts), 'В вопросах не видно названий признаков — передайте feature_names=cols.'
assert any('опоздает' in t for t in texts) and any('вовремя' in t for t in texts), 'Подпишите классы: class_names=["вовремя", "опоздает"].'
assert any(tuple(t.get_bbox_patch().get_facecolor()[:3]) != (1.0, 1.0, 1.0) for t in boxes), 'Включите заливку: filled=True.'
```

### hint
`model = DecisionTreeClassifier(max_leaf_nodes=4, random_state=0).fit(X_train, y_train)`.

### hint
`fig, ax = plt.subplots(figsize=(10, 5))`, затем `plot_tree(model, feature_names=cols, class_names=["вовремя", "опоздает"], filled=True, ax=ax)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_leaf_nodes=4, random_state=0).fit(X_train, y_train)
n_leaves = model.get_n_leaves()
fig, ax = plt.subplots(figsize=(10, 5))
plot_tree(model, feature_names=cols, class_names=["вовремя", "опоздает"], filled=True, ax=ax)
```

### explain
С ограничением по листьям дерево растёт не симметрично: каждый новый вопрос задаётся в той ветке, где он сильнее всего уменьшает неоднородность. Поэтому одна ветка может быть глубже другой.

## task: leaf-size | Минимум в листе | base

Обучите деревья **без** ограничения глубины, но с `min_samples_leaf` из списка `[1, 5, 20, 50, 100]`. Соберите словарь `test_by_leaf`: ключ — значение `min_samples_leaf`, значение — доля правильных ответов на тесте (3 знака). В `best_leaf` сохраните значение `min_samples_leaf` с лучшей долей.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
test_by_leaf = {}

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
cols = ['distance_km', 'items', 'promised_min', 'hour']
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(ok[cols], y, test_size=0.25, random_state=42)
w = {k: round(_T(min_samples_leaf=k, random_state=0).fit(a, c).score(b, e), 3) for k in [1, 5, 20, 50, 100]}
r = need('test_by_leaf', dict)
assert sorted(r) == sorted(w), f'Ключи test_by_leaf: {sorted(r)}, а нужны {sorted(w)}.'
for k in w:
    assert close(r[k], w[k]), f'test_by_leaf[{k}] = {r[k]}, а нужно {w[k]}. Дерево — только с min_samples_leaf и random_state=0, без max_depth.'
assert need('best_leaf') == max(w, key=w.get), f'best_leaf = {need("best_leaf")}. Это ключ test_by_leaf с наибольшей долей.'
```

### hint
`for k in [1, 5, 20, 50, 100]:` — внутри `DecisionTreeClassifier(min_samples_leaf=k, random_state=0)`, обучение и `test_by_leaf[k] = round(model.score(X_test, y_test), 3)`.

### hint
`max_depth` не задавайте вовсе — ограничивает дерево только `min_samples_leaf`. Лучшее значение — ключ словаря с наибольшей долей: `max(test_by_leaf, key=test_by_leaf.get)`, как в главе 1.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
test_by_leaf = {}
for k in [1, 5, 20, 50, 100]:
    model = DecisionTreeClassifier(min_samples_leaf=k, random_state=0).fit(X_train, y_train)
    test_by_leaf[k] = round(model.score(X_test, y_test), 3)
best_leaf = max(test_by_leaf, key=test_by_leaf.get)
```

### explain
Даже без ограничения глубины одно только требование «в листе не меньше N доставок» убирает переобучение. Слишком маленький минимум — дерево запоминает шум, слишком большой — снова недообучение.

## task: best-threshold | Перебор порогов | plus

Повторите работу дерева для одного признака `distance_km`. Возьмите все уникальные значения расстояния в обучающей выборке по возрастанию, кандидаты в пороги — середины между соседними значениями. Для каждого порога посчитайте взвешенную неоднородность Джини. Сохраните `best_t` — порог с наименьшей неоднородностью и `best_g` — эту неоднородность (оба — 3 знака), а в `tree_t` — порог, который выбрало дерево `DecisionTreeClassifier(max_depth=1, random_state=0)`, обученное только на `distance_km` (3 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

def gini(s):
    p = s.mean()
    return 1 - p**2 - (1 - p)**2

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)].copy()
ok['late'] = ok['actual_min'] > ok['promised_min']
tr = _tts(ok, test_size=0.25, random_state=42)[0]
def G(s):
    p = s.mean(); return 1 - p**2 - (1 - p)**2
v = _np.sort(tr['distance_km'].unique())
best = None
for t in (v[:-1] + v[1:]) / 2:
    l, r = tr.loc[tr['distance_km'] <= t, 'late'], tr.loc[tr['distance_km'] > t, 'late']
    g = (len(l) * G(l) + len(r) * G(r)) / len(tr)
    if best is None or g < best[1]:
        best = (t, g)
tt = _T(max_depth=1, random_state=0).fit(tr[['distance_km']], tr['late']).tree_.threshold[0]
assert close(need('tree_t'), round(tt, 3)), f'tree_t = {need("tree_t")}. Порог корня — model.tree_.threshold[0] у дерева, обученного на train[["distance_km"]].'
assert close(need('best_g'), round(best[1], 3)), f'best_g = {need("best_g")}, а нужно {round(best[1], 3)}. Проверьте, что кандидаты — середины между соседними уникальными значениями, а неоднородность взвешенная.'
assert close(need('best_t'), round(best[0], 3)), f'best_t = {need("best_t")}. Неоднородность найдена верно, но порог другой — возьмите порог, при котором она минимальна.'
```

### hint
Уникальные значения по возрастанию: `v = np.sort(train["distance_km"].unique())`. Середины соседних: `(v[:-1] + v[1:]) / 2`.

### hint
В цикле по порогам считайте взвешенную неоднородность и запоминайте лучший порог, если неоднородность меньше лучшей найденной. Или соберите все значения в список и найдите позицию минимума.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
train, test = train_test_split(ok, test_size=0.25, random_state=42)

def gini(s):
    p = s.mean()
    return 1 - p**2 - (1 - p)**2

v = np.sort(train["distance_km"].unique())
thresholds = (v[:-1] + v[1:]) / 2
scores = []
for t in thresholds:
    left = train.loc[train["distance_km"] <= t, "late"]
    right = train.loc[train["distance_km"] > t, "late"]
    scores.append((len(left) * gini(left) + len(right) * gini(right)) / len(train))
i = int(np.argmin(scores))
best_t, best_g = round(thresholds[i], 3), round(scores[i], 3)
model = DecisionTreeClassifier(max_depth=1, random_state=0).fit(train[["distance_km"]], train["late"])
tree_t = round(model.tree_.threshold[0], 3)
print(best_t, best_g, tree_t)
```

### explain
Порог совпал с тем, что выбрало дерево: ничего волшебного в обучении нет — полный перебор и минимум неоднородности. Дерево делает то же самое для всех признаков и потом повторяет это в каждой ветке. Лучший вопрос про расстояние даёт 0.319 — всё равно чуть хуже, чем 0.316 у вопроса про обещание, поэтому в корне дерева стоит `promised_min`.

## task: walk-flag | Флаг «пеший» | plus

Добавьте признак-флаг `walk` (1 — пеший курьер, 0 — нет) к признакам `distance_km`, `items`, `promised_min`, `hour` (флаг — последним столбцом). Обучите дерево глубины 3. Сохраните `top_feature` — признак с наибольшей важностью, `test_tree` — долю правильных ответов дерева на тесте и `test_rule` — долю правильных ответов правила «пеший — опоздает» на тех же тестовых доставках (обе — 3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
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
ok['walk'] = (ok['courier'] == 'пеший').astype(int)
cols = ['distance_km', 'items', 'promised_min', 'hour', 'walk']
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(ok[cols], y, test_size=0.25, random_state=42)
m = _T(max_depth=3, random_state=0).fit(a, c)
top = cols[m.feature_importances_.argmax()]
assert need('top_feature') == top, f'top_feature = {need("top_feature")!r}. Сопоставьте feature_importances_ с названиями столбцов.'
assert close(need('test_tree'), round(m.score(b, e), 3)), f'test_tree = {need("test_tree")}, а нужно {round(m.score(b, e), 3)}. Признаков пять, флаг — последний, разбиение 0.25 / 42.'
assert close(need('test_rule'), round(((b['walk'] == 1) == e).mean(), 3)), f'test_rule = {need("test_rule")}. Правило проверяйте только на тестовых доставках.'
```

### hint
`ok["walk"] = (ok["courier"] == "пеший").astype(int)`, затем разбивайте `ok[cols]` с пятью признаками.

### hint
Важности с названиями: `pd.Series(model.feature_importances_, index=cols)`, самый важный — `.idxmax()`. Правило на тесте: `((X_test["walk"] == 1) == y_test).mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
ok["walk"] = (ok["courier"] == "пеший").astype(int)
cols = ["distance_km", "items", "promised_min", "hour", "walk"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
top_feature = pd.Series(model.feature_importances_, index=cols).idxmax()
test_tree = round(model.score(X_test, y_test), 3)
test_rule = round(((X_test["walk"] == 1) == y_test).mean(), 3)
```

### explain
Дерево и правило на тесте почти равны — разница в десятые доли процента, меньше случайного разброса оценки. Модель нашла то же, что и аналитик, и лишь немного уточнила его правило.

## task: leaf-share | Вероятность своими руками | star

Докажите, что вероятность дерева — это доля опозданий в листе. Метод `model.apply(X)` возвращает для каждой строки номер листа, в который она попала. Обучите дерево глубины 3, посчитайте по **обучающей** выборке долю опозданий в каждом листе и с её помощью получите вероятности для тестовых доставок — массив или Series `p_manual` в порядке строк `X_test`. В `same` запишите `True`, если `p_manual` совпадает с `predict_proba(X_test)[:, 1]` с точностью до 1e-9.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
cols = ['distance_km', 'items', 'promised_min', 'hour']
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(ok[cols], y, test_size=0.25, random_state=42)
p = _T(max_depth=3, random_state=0).fit(a, c).predict_proba(b)[:, 1]
got = _np.asarray(need('p_manual'), dtype=float)
assert got.shape == p.shape, f'В p_manual {got.size} значений, а тестовых доставок {len(p)}.'
assert not _np.allclose(got, _np.asarray(e, dtype=float)), 'p_manual совпадает с фактическими ответами теста — доли нужно считать по обучающей выборке, а для теста только находить лист.'
assert _np.allclose(got, p, atol=1e-9), 'p_manual не совпадает с predict_proba. Доли — по y_train в разрезе листьев model.apply(X_train); для теста — лист model.apply(X_test).'
assert calls('apply') >= 2, 'Посчитайте p_manual через model.apply — для обучающей и для тестовой выборки; predict_proba нужен только для сравнения.'
assert need('same') == True, f'same = {need("same")}. Сравните p_manual с predict_proba(X_test)[:, 1] через np.allclose.'
```

### hint
`leaf_train = model.apply(X_train)` — номер листа для каждой обучающей доставки. Доля опозданий по листьям: `y_train.groupby(leaf_train).mean()`.

### hint
Для теста: `leaf_test = model.apply(X_test)`, затем подставьте доли по номеру листа — например, `share.loc[leaf_test].to_numpy()` или `pd.Series(leaf_test).map(share)`.

### hint
Сравнение массивов с точностью: `np.allclose(a, b, atol=1e-9)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[cols], y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
share = y_train.groupby(model.apply(X_train)).mean()
p_manual = share.loc[model.apply(X_test)].to_numpy()
same = bool(np.allclose(p_manual, model.predict_proba(X_test)[:, 1], atol=1e-9))
print(same)
```

### explain
Совпало полностью. Обученное дерево хранит только вопросы и доли классов в листьях — больше в нём ничего нет. Эта простота и делает дерево понятным, и ограничивает его: все доставки листа для модели одинаковы.
