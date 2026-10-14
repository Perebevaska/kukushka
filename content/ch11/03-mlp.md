---
title: "Нейросеть в sklearn: MLP"
files: [guests_churn.csv, deliveries.csv]
lead: "Писать обратный проход руками для каждой задачи не нужно. В sklearn есть многослойный перцептрон — MLPClassifier и MLPRegressor. Учимся задавать архитектуру, регуляризацию и раннюю остановку, смотрим на кривую обучения и честно сравниваем сеть с бустингом на табличных данных."
recap:
  - "`MLPClassifier(hidden_layer_sizes=(32,), alpha=..., max_iter=...)` — сеть со скрытыми слоями; `(64, 32)` — два слоя по 64 и 32 нейрона."
  - "Сеть учится градиентным спуском (по умолчанию Adam — спуск с «умным» шагом), поэтому признаки обязательно масштабируют: `make_pipeline(StandardScaler(), MLPClassifier(...))`."
  - "`alpha` — L2-регуляризация весов, как C в логистической регрессии наоборот: больше alpha — проще модель, меньше переобучения."
  - "`early_stopping=True` откладывает часть обучающих данных и останавливает обучение, когда качество на них перестаёт расти."
  - "`loss_curve_` — потеря по эпохам; `n_iter_` — сколько эпох прошло. ConvergenceWarning — «не дошёл до минимума за max_iter»."
  - "На табличных данных сети редко обгоняют бустинг. Их сила — изображения, звук, тексты, где признаки нужно строить из «сырых» данных."
---

## MLP в две строки

**Многослойный перцептрон** (MLP, multilayer perceptron) — сеть из уроков «Нейрон и слои» и «Обучение сети: обратное распространение ошибки»: полносвязные слои, ReLU между ними, на выходе сигмоида (или softmax для многих классов). В sklearn он собирается как любая модель:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

mlp = make_pipeline(StandardScaler(),
                    MLPClassifier(hidden_layer_sizes=(32,), alpha=1.0, max_iter=500, random_state=0))
mlp.fit(X_train, y_train)
print("эпох:", mlp[-1].n_iter_)
print("AUC на тесте:", round(roc_auc_score(y_test, mlp.predict_proba(X_test)[:, 1]), 3))
```

**Что здесь происходит:**

- `pd.get_dummies(..., dtype=int)` — города и категории в столбцы 0/1 (глава 6); `fillna({"avg_check": 0})` — пропуск среднего чека у гостей без визитов заменяем нулём, сеть пропусков не принимает.
- `make_pipeline(StandardScaler(), MLPClassifier(...))` — масштабирование и сеть одним конвейером: масштаб считается только по обучающей части.
- `mlp[-1].n_iter_` — сколько эпох (полных проходов по обучающим данным) сделала сеть.
- `predict_proba(X_test)[:, 1]` — вероятность ухода; по ней — AUC.

Параметры сети:

- `hidden_layer_sizes=(32,)` — один скрытый слой из 32 нейронов (запятая делает из числа кортеж); `(64, 32)` — два слоя;
- `alpha` — сила регуляризации весов (о ней ниже);
- `max_iter` — максимум эпох;
- `random_state` — фиксирует случайную инициализацию весов (урок «Обучение сети: обратное распространение ошибки») и порядок мини-батчей.

::: figure nn-mlp-arch
В `hidden_layer_sizes` перечисляют только скрытые слои. Вход sklearn берёт из числа столбцов X (у гостей после `get_dummies` их 15), выход — из числа классов в y.
:::

AUC около 0.91 — уровень логистической регрессии и леса из главы 7.

::: warn
Масштабирование для сети обязательно: внутри — градиентный спуск (глава 10), и признаки в рублях рядом с признаками 0/1 делают обучение медленным и нестабильным. В sklearn по умолчанию используется **Adam** — вариант спуска, который подбирает шаг для каждого веса отдельно, но и ему масштаб помогает.
:::

{{practice: first-mlp, count-params, p-mlp}}

## Регуляризация: alpha

Сеть из 32 нейронов на 15 признаках — это 15 · 32 + 32 + 32 + 1 = 545 весов и сдвигов на 1 800 гостей обучения. Переобучиться легко. Параметр `alpha` добавляет к потере штраф за большие веса (L2, как в Ridge и логистической регрессии из главы 7):

| alpha | AUC на обучении | AUC на тесте |
|---|---|---|
| 0.0001 (по умолчанию) | 0.946 | 0.908 |
| 0.1 | 0.945 | 0.910 |
| 1 | 0.916 | 0.910 |
| 10 | 0.887 | 0.899 |

Как работает штраф: к потере прибавляется $\dfrac{\alpha}{2n} \sum w^2$, где $\alpha$ — параметр `alpha`, $\sum w^2$ — сумма квадратов всех весов сети, $n$ — число обучающих объектов. Сеть теперь «платит» за каждый большой вес и использует большие веса, только если они сильно уменьшают ошибку. Так она хуже «запоминает» отдельных гостей.

С ростом alpha разрыв «обучение − тест» исчезает: при alpha = 1 сеть уже не переобучена, а при alpha = 10 зажата слишком сильно и начинает недообучаться. Подбирают alpha, как любой гиперпараметр, — кросс-валидацией.

::: figure nn-alpha
Слева — таблица выше на графике: разрыв между обучением и тестом при alpha = 0.0001 равен 0.038 и закрывается к alpha = 1. Справа — что штраф делает с весами: сумма квадратов всех весов обученной сети (`sum((w ** 2).sum() for w in coefs_)`) падает с 83.1 до 2.5.
:::

::: warn Типичные ошибки
- **alpha путают с `C` логистической регрессии.** У `LogisticRegression` `C` — обратная сила: больше `C` — *слабее* регуляризация. У `MLPClassifier` `alpha` — прямая: больше `alpha` — сильнее штраф и проще модель.
- **alpha принимают за шаг обучения.** Шаг спуска у `MLPClassifier` задаёт `learning_rate_init` (по умолчанию 0.001), а `alpha` — только штраф за большие веса.
- **alpha подбирают по тесту.** Тогда тест становится частью настройки и перестаёт быть честной оценкой. Подбирают кросс-валидацией на обучающей части, тест — один раз в конце.
:::

{{practice: alpha-sweep}}

## Ранняя остановка и кривая обучения

`loss_curve_` — потеря на обучении после каждой эпохи. С `early_stopping=True` sklearn откладывает 10 % обучающих данных (`validation_fraction`) и останавливается, если качество на них не растёт `n_iter_no_change` эпох подряд (по умолчанию 10):

::: tip Аналогия
Новый бариста отрабатывает латте-арт на одних и тех же десяти чашках из учебного набора, а раз в день старший бариста оценивает его рисунок на случайной чашке «из зала». Пока оценки «из зала» растут — тренировка полезна. Если неделю они не растут, хотя учебные чашки получаются всё лучше, — бариста просто привык к учебным чашкам, и тренировку пора заканчивать. Разница: sklearn не просто останавливается, а возвращает веса из лучшего дня, как будто последних дней тренировки не было.
:::

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

full = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), max_iter=300, random_state=0)).fit(X_train, y_train)
early = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), max_iter=300, early_stopping=True, random_state=0)).fit(X_train, y_train)

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(full[-1].loss_curve_, label="без остановки")
ax.plot(early[-1].loss_curve_, label="ранняя остановка")
ax.set_xlabel("эпоха")
ax.set_ylabel("потеря на обучении")
ax.legend()
plt.show()
print("эпох:", full[-1].n_iter_, "и", early[-1].n_iter_)
```

**Что здесь происходит:**

- Две одинаковые сети, у второй — `early_stopping=True`.
- `loss_curve_` — список потерь по эпохам; рисуем обе кривые на одном графике.
- `n_iter_` — сколько эпох реально прошло: у второй сети — меньше.

Без остановки потеря на обучении падает все 300 эпох (и sklearn предупреждает `ConvergenceWarning`: минимум не достигнут), а сеть всё сильнее подгоняется под обучающих гостей. Ранняя остановка обрывает обучение через несколько десятков эпох. На маленьких данных она бывает слишком ранней — 10 % от 1 800 строк это всего 180 гостей, и их шум решает, когда остановиться. Тогда помогает увеличить `n_iter_no_change` или регуляризовать через `alpha`.

::: figure nn-early-stop
Как это устроено для сети `early` из кода выше: из 1 800 обучающих гостей sklearn откладывает 180 на валидацию, после каждой эпохи меряет на них долю верных ответов и останавливается, когда больше 10 эпох подряд нет улучшения; веса сети он возвращает из лучшей эпохи.
:::

::: predict
```python static
from sklearn.neural_network import MLPClassifier
m = MLPClassifier(hidden_layer_sizes=(64, 32, 8))
print(len(m.hidden_layer_sizes))
```

- `104`
- [x] `3`
- `64`

Почему: кортеж задаёт три скрытых слоя — по 64, 32 и 8 нейронов. Входной и выходной слои sklearn добавляет сам по форме данных.
:::

::: quiz
Почему момент остановки нельзя выбирать по `loss_curve_` — потере на обучении?

- [x] Потеря на обучении падает почти всегда, даже когда сеть уже подгоняется под обучающих гостей; момент, когда пора остановиться, виден только на отложенных данных
  > Поэтому `early_stopping=True` следит за качеством на отложенных 10 % обучающей выборки, а не за `loss_curve_`.
- [ ] Можно: как только потеря на обучении перестала падать, сеть начала переобучаться
  > Переобучение начинается раньше и незаметно для этой кривой: потеря на обучении продолжает снижаться, а качество на новых данных уже стоит или падает.
- [ ] Лучше останавливаться по тестовой выборке — она самая честная
  > Если по тесту выбирать момент остановки, он становится частью настройки и перестаёт быть честной оценкой. Для этого откладывают валидацию из обучающих данных.
- [ ] `loss_curve_` и так показывает потерю на тесте
  > Это потеря на обучающих данных после каждой эпохи; тестовых данных `fit` вообще не видит.
:::

::: warn Типичные ошибки
- **Смотрят на `loss_curve_` и делают вывод «сеть не переобучилась».** Эта кривая — по обучающим данным, она падает почти всегда. Переобучение видно только на отложенных данных: у сети с `early_stopping=True` их качество лежит в `validation_scores_`.
- **Ранняя остановка вместо масштабирования.** Сеть без `StandardScaler` учится медленно, и ранняя остановка обрывает её ещё недоученной — выглядит как «сеть хуже бустинга». Сначала конвейер с масштабированием, потом настройка остановки.
- **Сравнение `n_iter_` разных сетей как меры качества.** Меньше эпох — не значит лучше или хуже: это лишь момент, когда валидация перестала расти. Сравнивают качество на тесте.
:::

{{practice: loss-curve, epoch-gap}}

## Сеть против бустинга

Сравним на двух табличных задачах — оттоке и времени доставки:

| задача | MLP | бустинг |
|---|---|---|
| отток, AUC | ≈ 0.91 | ≈ 0.93 (урок «Настройка бустинга» главы 10; пересчитаете в задаче «Архитектура кросс-валидацией») |
| минуты доставки, MAE | ≈ 4.8 | ≈ 4.2 по умолчанию, ≈ 3.8 у 300 деревьев (глава 10) |

Бустинг выигрывает и требует меньше настройки. Это типичная картина для **табличных** данных: признаки уже осмысленные (дни, жалобы, расстояние), и деревья хорошо ловят пороги и взаимодействия. Сети раскрываются там, где признаков в привычном смысле нет: пиксели изображения, звук, текст. Там скрытые слои строят признаки сами (урок «Нейрон и слои») — и никакой ручной feature engineering не сравнится. Об этом главы 13–14.

::: figure nn-tabular-vs-raw
В таблице гостей каждый столбец уже что-то значит, и дереву достаточно найти пороги. В картинке отдельный пиксель не значит ничего — смысл в сочетаниях, и их строят скрытые слои сети. Строки таблицы и пиксели — пример; «штрихи → петли → цифра» — условная иллюстрация того, что выучивают слои.
:::

::: quiz
На табличных данных об уходе гостей сеть дала AUC 0.91, а бустинг — чуть больше. Какой вывод разумен?

- [x] Для табличных данных бустинг обычно сильнее и проще в настройке; сети раскрываются на изображениях, тексте и звуке
  > Выбор модели — по задаче и по валидации, а не по моде.
- [ ] Сеть плохо обучена — нужно больше слоёв
  > Возможно, но разница типична для таблиц и без ошибок в настройке.
- [ ] Бустинг переобучился
  > Сравнение шло на одном тесте — нет признаков переобучения.
- [ ] Сети устарели
  > Для картинок и текстов они вне конкуренции.
:::

{{practice: depth, regression-net, arch-grid}}

## Разберём вместе: переобучение на кривых

Потеря на обучении почти всегда падает — это ничего не говорит о тесте. Чтобы увидеть переобучение, нужно следить за качеством на **отложенных** данных после каждой эпохи. В sklearn это можно сделать вручную: `partial_fit` делает одну эпоху, и после неё мы меряем AUC на обучении и на тесте.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
sc = StandardScaler().fit(X_train)
A, B = sc.transform(X_train), sc.transform(X_test)

net = MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)
rows = []
for epoch in range(1, 151):
    net.partial_fit(A, y_train, classes=[0, 1])
    if epoch % 25 == 0:
        rows.append({"эпоха": epoch,
                     "AUC обучение": round(roc_auc_score(y_train, net.predict_proba(A)[:, 1]), 3),
                     "AUC тест": round(roc_auc_score(y_test, net.predict_proba(B)[:, 1]), 3)})
print(pd.DataFrame(rows).to_string(index=False))
```

**Что здесь происходит:**

- `partial_fit` — одна эпоха обучения; при первом вызове нужно перечислить все классы (`classes=[0, 1]`).
- Масштабирование вынесено из конвейера: `sc.transform` применяем к обеим частям сами.
- Сеть специально большая (128 нейронов) и почти без регуляризации — чтобы переобучение было видно.

**Что получилось:** AUC на обучении растёт всё время (с 0.90 до 0.95), а на тесте — растёт до сотой эпохи и дальше стоит около 0.91. Разрыв «обучение − тест» увеличивается с нуля до трёх сотых: всё, что сеть выучила после сотой эпохи, — особенности обучающих гостей, которые на новых не повторяются. Продолжать обучение бессмысленно, а для большей сети или меньших данных — вредно. Ранняя остановка ищет этот момент автоматически, только по отложенной части обучения, а не по тесту.

::: figure nn-overfit-epochs
Те же замеры каждые 5 эпох на графике: обучающая кривая растёт всё время, тестовая выходит на плато около сотой эпохи, и разрыв между ними — то, что сеть «запомнила» про обучающих гостей.
:::

## Практика

## task: first-mlp | Первая сеть | warmup

Обучите `make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16,), max_iter=300, random_state=0))` на оттоке и сохраните `auc` на тесте (3 знака) и `n_weights` — число весов в первом слое (`model[-1].coefs_[0].size`).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neural_network import MLPClassifier as _MLP
from sklearn.metrics import roc_auc_score as _auc
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X0 = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X0, y, test_size=0.25, random_state=42, stratify=y)
m = _mp(_SS(), _MLP(hidden_layer_sizes=(16,), max_iter=300, random_state=0)).fit(a, c)
assert close(need('auc'), round(_auc(d, m.predict_proba(b)[:, 1]), 3), 0.002), f'auc = {need("auc")}.'
assert need('n_weights') == X0.shape[1] * 16, f'n_weights = {need("n_weights")}, а нужно {X0.shape[1] * 16}: признаков × нейронов.'
```

### hint
Обученная сеть — последний шаг конвейера: `model[-1]`.

### hint
Веса слоёв — список `model[-1].coefs_`; первый элемент — матрица «признаки × нейроны первого слоя».

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16,), max_iter=300, random_state=0))
model.fit(X_train, y_train)
auc = round(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]), 3)
n_weights = model[-1].coefs_[0].size
```

## task: count-params | Сколько параметров | warmup

Напишите функцию `n_params(n_in, layers, n_out)`, которая считает число параметров (весов и смещений) полносвязной сети: вход `n_in` признаков, скрытые слои `layers` (кортеж), выход `n_out` нейронов. Сохраните `p1 = n_params(15, (32,), 1)` — сеть из раздела про `alpha` — и `p2 = n_params(64, (128, 64), 10)`.

### starter
```python

```

### check
```python
f = need('n_params')
assert f(2, (3,), 1) == 2 * 3 + 3 + 3 * 1 + 1, 'Для сети 2 → 3 → 1 параметров должно быть 13.'
assert need('p1') == 15 * 32 + 32 + 32 + 1, f'p1 = {need("p1")}.'
assert need('p2') == 64 * 128 + 128 + 128 * 64 + 64 + 64 * 10 + 10, f'p2 = {need("p2")}.'
```

### hint
Это та же функция, что в уроке «Нейрон и слои»: число весов и сдвигов между соседними слоями.

### hint
Между слоями размеров a и b — a × b весов и b смещений. Пройдите по списку размеров `[n_in, *layers, n_out]` парами.

### solution
```python
def n_params(n_in, layers, n_out):
    sizes = [n_in, *layers, n_out]
    return sum(a * b + b for a, b in zip(sizes[:-1], sizes[1:]))

p1 = n_params(15, (32,), 1)
p2 = n_params(64, (128, 64), 10)
```

### explain
`p1` = 545 — ровно столько весов и сдвигов у сети на 15 признаках гостей из раздела про `alpha`. Сеть 64 → 128 → 64 → 10 — это уже почти 17 тысяч параметров. Для 1 800 обучающих строк столько параметров — гарантия переобучения без регуляризации. Для миллионов изображений — скромная сеть.

## task: p-mlp | Конвейер с сетью | warmup

Соберите обучение регрессионной сети на маленьких данных.

### parsons
```python
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
rng = np.random.default_rng(0)
X = rng.uniform(0, 10, size=(300, 1))
y = np.sin(X[:, 0]) * 10
model = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(32,), max_iter=3000, random_state=0))
model.fit(X, y)
print(model.score(X, y) > 0.9)
```

### check
```python
assert _lines and _lines[-1] == 'True', f'Сейчас: {_lines}.'
```

### hint
Сначала данные, потом модель, потом `fit` и печать.

### hint
В конвейере сначала масштабирование, потом сеть.

## task: alpha-sweep | Подбор регуляризации | base

Для `alpha` в `[0.0001, 0.1, 1.0, 10.0]` обучите `make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), alpha=..., max_iter=500, random_state=0))` и посчитайте AUC на обучении и на тесте. Сохраните DataFrame `res` (столбцы `alpha`, `train`, `test`, 3 знака), `best_alpha` — alpha с наибольшим AUC на тесте, причём выбирайте **по округлённым значениям из `res`** (при равенстве — меньший alpha), и `gap_small`, `gap_big` — разрыв `train − test` при alpha 0.0001 и 10 (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neural_network import MLPClassifier as _MLP
from sklearn.metrics import roc_auc_score as _auc
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X0 = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X0, y, test_size=0.25, random_state=42, stratify=y)
w = {}
for al in [0.0001, 0.1, 1.0, 10.0]:
    m = _mp(_SS(), _MLP(hidden_layer_sizes=(32,), alpha=al, max_iter=500, random_state=0)).fit(a, c)
    w[al] = (round(_auc(c, m.predict_proba(a)[:, 1]), 3), round(_auc(d, m.predict_proba(b)[:, 1]), 3))
r = need('res', _pd.DataFrame)
for al, (t1, t2) in w.items():
    row = r[r['alpha'] == al]
    assert len(row) == 1, f'Нет строки для alpha = {al}.'
    assert close(row['train'].iloc[0], t1, 0.002) and close(row['test'].iloc[0], t2, 0.002), f'alpha = {al}: train, test = {row["train"].iloc[0]}, {row["test"].iloc[0]}, а нужно {t1}, {t2}.'
best = min(w, key=lambda k: (-w[k][1], k))
assert need('best_alpha') == best, f'best_alpha = {need("best_alpha")}, а нужно {best}.'
assert close(need('gap_small'), round(w[0.0001][0] - w[0.0001][1], 3), 0.003) and close(need('gap_big'), round(w[10.0][0] - w[10.0][1], 3), 0.003), f'gap_small, gap_big = {need("gap_small")}, {need("gap_big")}.'
```

### hint
Для каждого alpha создайте новый конвейер со `StandardScaler` и `MLPClassifier(alpha=...)`; AUC считают по `predict_proba(...)[:, 1]`.

### hint
Цикл по alpha, внутри — обучение и два AUC; строки — словари в список, потом DataFrame.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

rows = []
for alpha in [0.0001, 0.1, 1.0, 10.0]:
    m = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), alpha=alpha, max_iter=500, random_state=0))
    m.fit(X_train, y_train)
    rows.append({"alpha": alpha,
                 "train": round(roc_auc_score(y_train, m.predict_proba(X_train)[:, 1]), 3),
                 "test": round(roc_auc_score(y_test, m.predict_proba(X_test)[:, 1]), 3)})
res = pd.DataFrame(rows)
best = res.sort_values(["test", "alpha"], ascending=[False, True]).iloc[0]
best_alpha = best["alpha"]
gap_small = round(res.loc[0, "train"] - res.loc[0, "test"], 3)
gap_big = round(res.loc[3, "train"] - res.loc[3, "test"], 3)
```

### explain
При слабой регуляризации разрыв обучение − тест около 0.04, при alpha = 10 он становится отрицательным: модель настолько проста, что на обучении не лучше, чем на тесте. Лучшее — посередине. По округлённым AUC alpha = 0.1 и alpha = 1 дают одинаковые 0.910, и правило «при равенстве — меньший» выбирает 0.1. Без округления чуть выше alpha = 1 (0.9101 против 0.9098), но разница в четвёртом знаке — это шум одного разбиения: на тесте эти два варианта неразличимы. Поэтому проверка и просит выбирать по `res`. Это та же история «смещение против разброса», что и с глубиной дерева.

## task: loss-curve | Кривая потерь | base

Обучите `MLPClassifier(hidden_layer_sizes=(32,), max_iter=200, random_state=0)` (в конвейере со StandardScaler) и сохраните `curve` — список `loss_curve_`, `first`, `last` — потери в первую и последнюю эпоху (3 знака) и `halved_at` — номер первой эпохи (считая с 1), где потеря стала меньше половины первой.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neural_network import MLPClassifier as _MLP
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X0 = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X0, y, test_size=0.25, random_state=42, stratify=y)
lc = _mp(_SS(), _MLP(hidden_layer_sizes=(32,), max_iter=200, random_state=0)).fit(a, c)[-1].loss_curve_
cv = need('curve')
assert len(cv) == len(lc), f'В curve {len(cv)} значений, а эпох {len(lc)}.'
assert close(need('first'), round(lc[0], 3), 0.002) and close(need('last'), round(lc[-1], 3), 0.002), f'first, last = {need("first")}, {need("last")}.'
h = next(i + 1 for i, v in enumerate(lc) if v < lc[0] / 2)
assert need('halved_at') == h, f'halved_at = {need("halved_at")}, а нужно {h}.'
```

### hint
Кривая потерь появляется у обученной сети: `model[-1].loss_curve_` — обычный список чисел.

### hint
`curve = model[-1].loss_curve_`; номер — `next(i + 1 for i, v in enumerate(curve) if v < curve[0] / 2)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), max_iter=200, random_state=0))
model.fit(X_train, y_train)
curve = model[-1].loss_curve_
first, last = round(curve[0], 3), round(curve[-1], 3)
halved_at = next(i + 1 for i, v in enumerate(curve) if v < curve[0] / 2)
```

### explain
`loss_curve_` хранит среднюю кросс-энтропию на обучающих данных после каждой эпохи. Первые эпохи дают основной выигрыш: потеря падает с 0.761 вдвое уже к 21-й эпохе, а дальше снижается медленно и к 200-й доходит до 0.27. Все 200 эпох использованы полностью, поэтому sklearn и предупреждает, что сеть не сошлась. Но низкая потеря на обучении ещё не значит хорошее качество на тесте: при долгом обучении сеть начинает подгоняться под обучающие данные. Для этого и нужны `early_stopping` и проверка на отложенной выборке.

## task: epoch-gap | Разрыв по эпохам | base

Повторите разбор из урока (сеть `MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)`, обучение по одной эпохе через `partial_fit` на масштабированных данных из заготовки) на 150 эпохах и сохраните после **каждой** эпохи AUC на обучении и тесте: списки `auc_train`, `auc_test` (длины 150, без округления). Сохраните `best_epoch` — номер эпохи (от 1) с наибольшим AUC на тесте, `best_test` (3 знака) и `gap_end` — разрыв «обучение − тест» после последней эпохи (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
sc = StandardScaler().fit(X_train)
A, B = sc.transform(X_train), sc.transform(X_test)
```

### starter
```python
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

net = MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)
auc_train, auc_test = [], []

```

### check
```python
import numpy as _np
import warnings as _w
from sklearn.neural_network import MLPClassifier as _M
from sklearn.metrics import roc_auc_score as _auc
A0, B0, ya, yb = need('A'), need('B'), need('y_train'), need('y_test')
n = _M(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0); tr, te = [], []
with _w.catch_warnings():
    _w.simplefilter('ignore')
    for _ in range(150):
        n.partial_fit(A0, ya, classes=[0, 1]); tr.append(_auc(ya, n.predict_proba(A0)[:, 1])); te.append(_auc(yb, n.predict_proba(B0)[:, 1]))
assert len(need('auc_train')) == 150 and _np.allclose(need('auc_test'), te, atol=1e-9), 'auc_test — AUC на тесте после каждой из 150 эпох.'
be = int(_np.argmax(te)) + 1
assert need('best_epoch') == be, f'best_epoch = {need("best_epoch")}, а нужно {be}.'
assert close(need('best_test'), round(max(te), 3), 0.0011), f'best_test = {need("best_test")}.'
assert close(need('gap_end'), round(tr[-1] - te[-1], 3), 0.0011), f'gap_end = {need("gap_end")}.'
```

### hint
В цикле на 150 шагов: `net.partial_fit(A, y_train, classes=[0, 1])`, затем два `roc_auc_score` по `predict_proba(...)[:, 1]`.

### hint
Номер лучшей эпохи: `int(np.argmax(auc_test)) + 1` — `argmax` считает с нуля, эпохи — с единицы.

### solution
```python
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

net = MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)
auc_train, auc_test = [], []
for epoch in range(150):
    net.partial_fit(A, y_train, classes=[0, 1])
    auc_train.append(roc_auc_score(y_train, net.predict_proba(A)[:, 1]))
    auc_test.append(roc_auc_score(y_test, net.predict_proba(B)[:, 1]))
best_epoch = int(np.argmax(auc_test)) + 1
best_test = round(max(auc_test), 3)
gap_end = round(auc_train[-1] - auc_test[-1], 3)
print(best_epoch, best_test, gap_end)
```

### explain
Лучшая эпоха на тесте наступает задолго до 150-й, а после неё AUC на тесте почти не меняется, тогда как на обучении продолжает расти. Обратите внимание: выбирать эпоху по **тесту** в работе нельзя — это та же подгонка под тест, что в главе 6. Правильно — отложить часть обучения (как делает `early_stopping`) или выбрать число эпох кросс-валидацией, а тест оставить для финальной проверки.

## task: depth | Шире или глубже | plus

Сравните на оттоке три архитектуры при `alpha=1.0`, `max_iter=500`, `random_state=0` (конвейер со `StandardScaler`): `(8,)`, `(32,)`, `(64, 32)`. Сохраните `res` — словарь `{архитектура-строка: AUC на тесте}` с ключами `"8"`, `"32"`, `"64-32"` (3 знака), `params` — словарь с числом параметров каждой сети (сумма размеров `coefs_` и `intercepts_`), и `best` — ключ лучшей.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
```

### starter
```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

archs = {"8": (8,), "32": (32,), "64-32": (64, 32)}
res, params = {}, {}

```

### check
```python
import warnings as _w
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neural_network import MLPClassifier as _M
from sklearn.metrics import roc_auc_score as _auc
Xa, Xb, ya, yb = need('X_train'), need('X_test'), need('y_train'), need('y_test')
w, pw = {}, {}
with _w.catch_warnings():
    _w.simplefilter('ignore')
    for k, a in {'8': (8,), '32': (32,), '64-32': (64, 32)}.items():
        m = _mp(_SS(), _M(hidden_layer_sizes=a, alpha=1.0, max_iter=500, random_state=0)).fit(Xa, ya)
        w[k] = round(_auc(yb, m.predict_proba(Xb)[:, 1]), 3)
        pw[k] = sum(c.size for c in m[-1].coefs_) + sum(c.size for c in m[-1].intercepts_)
g_ = need('res', dict)
assert all(close(g_[k], w[k], 0.0011) for k in w), f'res = {g_}, а нужно {w}.'
assert {k: int(v) for k, v in need('params', dict).items()} == pw, f'params = {need("params")}, а нужно {pw}.'
assert need('best') == max(w, key=w.get), f'best = {need("best")!r}.'
```

### hint
Цикл по `archs.items()`: обучить конвейер с `hidden_layer_sizes=a`, AUC по `predict_proba(X_test)[:, 1]`.

### hint
Параметры обученной сети: `sum(c.size for c in m[-1].coefs_) + sum(c.size for c in m[-1].intercepts_)`.

### solution
```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

archs = {"8": (8,), "32": (32,), "64-32": (64, 32)}
res, params = {}, {}
for key, arch in archs.items():
    m = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=arch, alpha=1.0, max_iter=500, random_state=0))
    m.fit(X_train, y_train)
    res[key] = round(roc_auc_score(y_test, m.predict_proba(X_test)[:, 1]), 3)
    params[key] = int(sum(c.size for c in m[-1].coefs_) + sum(c.size for c in m[-1].intercepts_))
best = max(res, key=res.get)
print(res, params, best)
```

### explain
Глубокая сеть (64, 32) немного лучше — около 0.914 против 0.910 у (32,) и 0.905 у (8,), — но параметров у неё в шесть раз больше (3137 против 545). Разница в тысячные доли AUC на 600 тестовых гостях — в пределах шума (вспомните доверительные интервалы из главы 5: на 600 объектах такая разница ничего не доказывает). Для табличных данных такого размера глубина почти ничего не даёт; бустинг из главы 10 всё равно сильнее (около 0.93). Если сравнивать архитектуры всерьёз — кросс-валидацией и с несколькими `random_state`, как в задаче со звёздочкой.

## task: regression-net | Сеть для минут доставки | plus

Обучите `make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(32,), max_iter=2000, random_state=0))` на доставках (признаки — как в главе 10: `distance_km`, `items`, `hour`, флаги `courier`, `weather`, `shop_id`) и сравните с `HistGradientBoostingRegressor(random_state=0)`. Сеть использует все 2000 эпох, поэтому предупреждение `ConvergenceWarning` ожидаемо, а обучение в браузере займёт заметное время — от нескольких секунд до десятков. Сохраните `mae_mlp`, `mae_hgb` (2 знака) и `winner` — `"сеть"` или `"бустинг"`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neural_network import MLPRegressor as _MR
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, e = _tts(X0, y0, test_size=0.25, random_state=42)
m1 = round(_mae(e, _mp(_SS(), _MR(hidden_layer_sizes=(32,), max_iter=2000, random_state=0)).fit(a, c).predict(b)), 2)
m2 = round(_mae(e, _H(random_state=0).fit(a, c).predict(b)), 2)
assert close(need('mae_mlp'), m1, 0.02), f'mae_mlp = {need("mae_mlp")}, а нужно {m1}.'
assert close(need('mae_hgb'), m2, 0.011), f'mae_hgb = {need("mae_hgb")}, а нужно {m2}.'
assert need('winner') == ('сеть' if m1 < m2 else 'бустинг'), f'winner = {need("winner")!r}.'
```

### hint
Для регрессии — `MLPRegressor`; целевую переменную масштабировать не обязательно, но признаки — обязательно.

### hint
Две модели, два `mean_absolute_error`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

mlp = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(32,), max_iter=2000, random_state=0)).fit(X_train, y_train)
hgb = HistGradientBoostingRegressor(random_state=0).fit(X_train, y_train)
mae_mlp = round(mean_absolute_error(y_test, mlp.predict(X_test)), 2)
mae_hgb = round(mean_absolute_error(y_test, hgb.predict(X_test)), 2)
winner = "сеть" if mae_mlp < mae_hgb else "бустинг"
```

### explain
Бустинг точнее и обучается за доли секунды. Сеть могла бы догнать его подбором архитектуры и регуляризации, но на табличных данных это редко окупается.

## task: arch-grid | Архитектура кросс-валидацией | star

Подберите архитектуру и регуляризацию сети для оттока: `GridSearchCV` по конвейеру `make_pipeline(StandardScaler(), MLPClassifier(max_iter=300, random_state=0))` с сеткой `{"mlpclassifier__hidden_layer_sizes": [(16,), (32, 16)], "mlpclassifier__alpha": [0.1, 1.0]}`, `cv=3`, `scoring="roc_auc"`. Сохраните `best_params`, `cv_auc` и `test_auc` (3 знака). Для сравнения обучите на том же `X_train` бустинг из главы 10 — `HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0)` — и сохраните `hgb_auc`, его AUC на тесте (3 знака). Предупреждения `ConvergenceWarning` во время подбора ожидаемы: на части комбинаций 300 эпох не хватает, чтобы потеря перестала меняться.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, GridSearchCV as _GS
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neural_network import MLPClassifier as _MLP
from sklearn.metrics import roc_auc_score as _auc
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X0 = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X0, y, test_size=0.25, random_state=42, stratify=y)
gs = _GS(_mp(_SS(), _MLP(max_iter=300, random_state=0)), {'mlpclassifier__hidden_layer_sizes': [(16,), (32, 16)], 'mlpclassifier__alpha': [0.1, 1.0]}, cv=3, scoring='roc_auc').fit(a, c)
assert dict(need('best_params')) == gs.best_params_, f'best_params = {need("best_params")}, а нужно {gs.best_params_}.'
assert close(need('cv_auc'), round(gs.best_score_, 3), 0.002), f'cv_auc = {need("cv_auc")}.'
assert close(need('test_auc'), round(_auc(d, gs.predict_proba(b)[:, 1]), 3), 0.002), f'test_auc = {need("test_auc")}.'
from sklearn.ensemble import HistGradientBoostingClassifier as _HGB
hw = round(_auc(d, _HGB(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0).fit(a, c).predict_proba(b)[:, 1]), 3)
assert close(need('hgb_auc'), hw, 0.002), f'hgb_auc = {need("hgb_auc")}, а нужно {hw}: бустинг с параметрами из условия на X_train, AUC на X_test.'
```

### hint
Имена параметров в конвейере из `make_pipeline` — имя класса строчными буквами, два подчёркивания, параметр (глава 7).

### hint
Сетка: `{"mlpclassifier__hidden_layer_sizes": [...], "mlpclassifier__alpha": [...]}`; лучшие параметры — `grid.best_params_`, AUC кросс-валидации — `grid.best_score_`. Бустинг: `from sklearn.ensemble import HistGradientBoostingClassifier`, `.fit(X_train, y_train)` и `roc_auc_score` по `predict_proba(X_test)[:, 1]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

pipe = make_pipeline(StandardScaler(), MLPClassifier(max_iter=300, random_state=0))
grid = GridSearchCV(pipe, {"mlpclassifier__hidden_layer_sizes": [(16,), (32, 16)],
                           "mlpclassifier__alpha": [0.1, 1.0]}, cv=3, scoring="roc_auc")
grid.fit(X_train, y_train)
best_params = grid.best_params_
cv_auc = round(grid.best_score_, 3)
test_auc = round(roc_auc_score(y_test, grid.predict_proba(X_test)[:, 1]), 3)

from sklearn.ensemble import HistGradientBoostingClassifier
hgb = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0)
hgb.fit(X_train, y_train)
hgb_auc = round(roc_auc_score(y_test, hgb.predict_proba(X_test)[:, 1]), 3)
print(best_params, cv_auc, test_auc, hgb_auc)
```

### explain
Лучшей оказывается простая сеть с заметной регуляризацией — один слой из 16 нейронов и alpha = 1: на 1 800 строках глубина не нужна. AUC кросс-валидации (0.879) ниже, чем на тесте (0.91), и это не ошибка: в каждом фолде сеть учится на 1 200 строках вместо 1 800, а сами фолды заметно различаются (от 0.863 до 0.895) — тестовая четверть на этом разбиении просто «удобнее» средней. У бустинга то же самое: на тех же трёх фолдах его AUC от 0.881 до 0.921, а на тесте 0.93. Сравнивать модели честно на одной и той же схеме — и на тесте бустинг даёт 0.93 против 0.91 у сети: даже после подбора сеть его не обгоняет, для табличных данных это нормальный итог.
