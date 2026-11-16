---
title: "Нейросеть в sklearn: MLP"
files: [guests_churn.csv, deliveries.csv]
lead: "Писать обратный проход руками для каждой задачи не нужно. В sklearn есть многослойный перцептрон — MLPClassifier и MLPRegressor. Учимся задавать архитектуру, регуляризацию и раннюю остановку, смотрим на кривую обучения и честно сравниваем сеть с бустингом на табличных данных."
recap:
  - "`MLPClassifier(hidden_layer_sizes=(32,), alpha=..., max_iter=...)` — сеть со скрытыми слоями; `(64, 32)` — два слоя по 64 и 32 нейрона."
  - "Сеть учится градиентным спуском (по умолчанию Adam — спуск с «умным» шагом), поэтому признаки обязательно масштабируют: `make_pipeline(StandardScaler(), MLPClassifier(...))`."
  - "`alpha` задаёт силу L2-штрафа. При тех же слоях увеличение alpha сильнее штрафует большие веса. Влияние на качество проверьте на валидации."
  - "`early_stopping=True` откладывает часть обучающих данных и останавливает обучение, когда качество на них перестаёт расти."
  - "`loss_curve_` — потеря по эпохам; `n_iter_` — сколько эпох прошло. ConvergenceWarning — «не дошёл до минимума за max_iter»."
  - "Сравнивайте модели на одних отложенных строках. Для оттока лучше большая AUC, для времени доставки — меньшая средняя абсолютная ошибка в минутах."
---

## MLP в две строки

**Многослойный перцептрон** (MLP, multilayer perceptron) — сеть из уроков «Нейрон и слои» и «Обучение сети: обратное распространение ошибки»: полносвязные слои, ReLU между ними, на выходе сигмоида (или softmax для многих классов). В этом примере и в сравнении alpha ниже мы обучаем модель на 1 800 гостях и смотрим AUC на 600 валидационных гостях. Отдельной оценки на финальном тесте у этой демонстрации нет.

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
X_train, X_validation, y_train, y_validation = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

mlp = make_pipeline(StandardScaler(),
                    MLPClassifier(hidden_layer_sizes=(32,), alpha=1.0, max_iter=500, random_state=0))
mlp.fit(X_train, y_train)
print("эпох:", mlp[-1].n_iter_)
print("AUC на валидации:", round(roc_auc_score(y_validation, mlp.predict_proba(X_validation)[:, 1]), 3))
```

**Что здесь происходит:**

- `pd.get_dummies(..., dtype=int)` — города и категории в столбцы 0/1 (глава 6); `fillna({"avg_check": 0})` — пропуск среднего чека у гостей без визитов заменяем нулём, сеть пропусков не принимает.
- `make_pipeline(StandardScaler(), MLPClassifier(...))` — масштабирование и сеть одним конвейером: масштаб считается только по обучающей части.
- `mlp[-1].n_iter_` — сколько эпох (полных проходов по обучающим данным) сделала сеть.
- `predict_proba(X_validation)[:, 1]` — вероятность ухода; по ней — AUC.

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

| alpha | AUC на обучении | AUC на валидации |
|---|---|---|
| 0.0001 (по умолчанию) | 0.946 | 0.908 |
| 0.1 | 0.945 | 0.910 |
| 1 | 0.916 | 0.910 |
| 10 | 0.887 | 0.899 |

Как работает штраф: к потере прибавляется $\dfrac{\alpha}{2n} \sum w^2$, где $\alpha$ — параметр `alpha`, $\sum w^2$ — сумма квадратов всех весов сети, $n$ — число обучающих объектов. Сеть теперь «платит» за каждый большой вес и использует большие веса, только если они сильно уменьшают ошибку. Так она хуже «запоминает» отдельных гостей.

При увеличении alpha с 0.0001 до 1 разрыв между AUC обучения и валидации уменьшается с 0.038 до 0.006. При alpha = 10 валидационная AUC опускается до 0.899. В упражнении ниже вы сравните значения alpha на другом разбиении с отдельным финальным тестом.

::: figure nn-alpha
Слева — таблица выше на графике: разрыв между AUC обучения и валидации уменьшается с 0.038 при alpha = 0.0001 до 0.006 при alpha = 1. Справа — что штраф делает с весами: сумма квадратов всех весов обученной сети (`sum((w ** 2).sum() for w in coefs_)`) падает с 83.1 до 2.5.
:::

::: warn Типичные ошибки
- **alpha путают с `C` логистической регрессии.** У `LogisticRegression` увеличение `C` ослабляет штраф. У `MLPClassifier` увеличение `alpha` усиливает штраф при том же числе параметров.
- **alpha принимают за шаг обучения.** Шаг спуска у `MLPClassifier` задаёт `learning_rate_init` (по умолчанию 0.001), а `alpha` — только штраф за большие веса.
- **alpha подбирают по тесту.** Тогда тест становится частью настройки и перестаёт быть честной оценкой. Подбирают кросс-валидацией на обучающей части, тест — один раз в конце.
:::

{{practice: alpha-sweep}}

## Ранняя остановка и кривая обучения

В отдельном примере со встроенной ранней остановкой 600 гостей резервируем для финального теста. Они не участвуют в выборе эпохи. Для сети `early` из остальных 1 800 гостей 1 620 используются для обновления весов, а 180 — для проверки после каждой эпохи.

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
- **Сравнение `n_iter_` разных сетей как меры качества.** Число эпох сообщает, когда завершилось обучение. Для выбора сети сравните кандидатов на одной валидации. После выбора оцените зафиксированную процедуру на тесте.
:::

{{practice: loss-curve, epoch-gap}}

## Сеть против бустинга

В каждой строке сравните две модели на одних и тех же отложенных объектах.

| задача | MLP | бустинг |
|---|---|---|
| Отток, AUC на 600 гостях, больше — лучше | ≈ 0.91, сеть после подбора | ≈ 0.93, HistGradientBoostingClassifier с 300 итерациями и глубиной 3 |
| Время доставки, MAE на отложенной четверти заказов, меньше — лучше | `mae_mlp`, сеть с 32 скрытыми нейронами | `mae_hgb`, HistGradientBoostingRegressor с настройками по умолчанию |

Первую строку вы воспроизведёте в задаче «Архитектура кросс-валидацией». В её разбиении бустинг лучше ранжирует гостей по риску ухода. Во вторую строку подставьте результаты задачи «Сеть для минут доставки». Разность двух MAE покажет, на сколько минут различаются средние абсолютные ошибки этих настроек на тех же заказах.

::: figure nn-tabular-vs-raw
В таблице гостей каждый столбец уже что-то значит, и дереву достаточно найти пороги. В картинке отдельный пиксель не значит ничего — смысл в сочетаниях, и их строят скрытые слои сети. Строки таблицы и пиксели — пример; «штрихи → петли → цифра» — условная иллюстрация того, что выучивают слои.
:::

::: quiz
На табличных данных об уходе гостей сеть дала AUC 0.91, а бустинг — чуть больше. Какой вывод разумен?

- [x] На этих отложенных гостях бустинг лучше ранжировал риск ухода
  > Большая AUC означает лучшее ранжирование. Для другого состава гостей потребуется своя проверка.
- [ ] Сеть плохо обучена — нужно больше слоёв
  > Эти две оценки относятся к уже обученным моделям. Эффект дополнительного слоя нужно отдельно проверить на валидации.
- [ ] Бустинг переобучился
  > Сравнение шло на одном тесте — нет признаков переобучения.
- [ ] Сети устарели
  > Для картинок и текстов сети — важный кандидат; выбор подтверждают сравнением на подходящих данных.
:::

{{practice: depth, regression-net, arch-grid}}

## Разберём вместе: переобучение на кривых

Вернёмся к демонстрационному разбиению на 1 800 обучающих и 600 валидационных гостей. Каждая команда `partial_fit` выполняет одну эпоху. Каждые 25 эпох сравним AUC на этих двух группах. По графику посмотрим, сопровождается ли дальнейший рост AUC на обучении улучшением на валидации.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_validation, y_train, y_validation = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
sc = StandardScaler().fit(X_train)
A, B = sc.transform(X_train), sc.transform(X_validation)

net = MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)
rows = []
for epoch in range(1, 151):
    net.partial_fit(A, y_train, classes=[0, 1])
    if epoch % 25 == 0:
        rows.append({"эпоха": epoch,
                     "AUC обучение": round(roc_auc_score(y_train, net.predict_proba(A)[:, 1]), 3),
                     "AUC валидация": round(roc_auc_score(y_validation, net.predict_proba(B)[:, 1]), 3)})
print(pd.DataFrame(rows).to_string(index=False))
```

**Что здесь происходит:**

- `partial_fit` — одна эпоха обучения; при первом вызове нужно перечислить все классы (`classes=[0, 1]`).
- Масштабирование вынесено из конвейера: `sc.transform` применяем к обеим частям сами.
- Сеть специально большая (128 нейронов) и почти без регуляризации — чтобы переобучение было видно.

К 150-й эпохе AUC на обучении достигла 0.945, а на валидации — 0.911. После примерно сотой эпохи обучение ещё улучшает AUC на знакомых гостях; у валидационной кривой такого роста не видно. На этом разбиении есть основания рассмотреть более раннюю остановку. Для итоговой оценки выбранной эпохи потребуются данные, отложенные до сравнения.

::: figure nn-overfit-epochs
На графике точки показаны каждые пять эпох. В конце AUC обучения выше AUC валидации на 0.034. Сравните последние участки обеих кривых.
:::

В упражнениях по выбору alpha, эпохи и глубины сразу откладывают 600 финальных гостей. На 1 350 обучают, на 450 сравнивают настройки. Масштабирование обучают на обучающей части. Финальную выборку используют после выбора конфигурации.

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

Для `alpha` в `[0.0001, 0.1, 1.0, 10.0]` обучите `make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), alpha=..., max_iter=500, random_state=0))` и посчитайте AUC на обучении и внутренней валидации. Сохраните DataFrame `res` (столбцы `alpha`, `train`, `validation`, 3 знака), `best_alpha` — alpha с наибольшим AUC на валидации, причём выбирайте **по округлённым значениям из `res`** (при равенстве — меньший alpha), и `gap_small`, `gap_big` — разрыв `train − validation` при alpha 0.0001 и 10 (3 знака).

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
X_development, X_final, y_development, y_final = train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
X_train, X_validation, y_train, y_validation = train_test_split(X_development,y_development,test_size=.25,random_state=43,stratify=y_development)

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
_dev,_final,_devy,_finaly = _tts(X0,y,test_size=.25,random_state=42,stratify=y)
a,b,c,d = _tts(_dev,_devy,test_size=.25,random_state=43,stratify=_devy)
w = {}
for al in [0.0001, 0.1, 1.0, 10.0]:
    m = _mp(_SS(), _MLP(hidden_layer_sizes=(32,), alpha=al, max_iter=500, random_state=0)).fit(a, c)
    w[al] = (round(_auc(c, m.predict_proba(a)[:, 1]), 3), round(_auc(d, m.predict_proba(b)[:, 1]), 3))
r = need('res', _pd.DataFrame)
assert {'alpha', 'train', 'validation'} <= set(r.columns), 'В res нужны столбцы alpha, train и validation. Для выбора регуляризации берите валидацию.'
for al, (t1, t2) in w.items():
    row = r[r['alpha'] == al]
    assert len(row) == 1, f'Нет строки для alpha = {al}.'
    assert close(row['train'].iloc[0], t1, 0.002) and close(row['validation'].iloc[0], t2, 0.002), f'alpha = {al}: train, validation = {row["train"].iloc[0]}, {row["validation"].iloc[0]}, а нужно {t1}, {t2}.'
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
X_development, X_final, y_development, y_final = train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
X_train, X_validation, y_train, y_validation = train_test_split(X_development,y_development,test_size=.25,random_state=43,stratify=y_development)

rows = []
for alpha in [0.0001, 0.1, 1.0, 10.0]:
    m = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), alpha=alpha, max_iter=500, random_state=0))
    m.fit(X_train, y_train)
    rows.append({"alpha": alpha,
                 "train": round(roc_auc_score(y_train, m.predict_proba(X_train)[:, 1]), 3),
                 "validation": round(roc_auc_score(y_validation, m.predict_proba(X_validation)[:, 1]), 3)})
res = pd.DataFrame(rows)
best = res.sort_values(["validation", "alpha"], ascending=[False, True]).iloc[0]
best_alpha = best["alpha"]
gap_small = round(res.loc[0, "train"] - res.loc[0, "validation"], 3)
gap_big = round(res.loc[3, "train"] - res.loc[3, "validation"], 3)
```

### explain
Упорядочьте строки по убыванию AUC валидации. Здесь при alpha = 1 получено 0.876, при 0.1 — 0.852. Между крайними значениями alpha разрыв «обучение − валидация» сократился с 0.106 до 0.018. Выбор делают по самой высокой валидационной AUC. При равенстве округлённых результатов возьмите меньшую alpha, как оговорено в задании.

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
import numpy as _np
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
assert _np.asarray(cv).shape == (len(lc),) and _np.allclose(cv, lc, rtol=1e-7, atol=1e-9), 'В curve нужны реальные потери каждой эпохи из loss_curve_, в исходном порядке.'
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

Повторите разбор из урока (сеть `MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)`, обучение по одной эпохе через `partial_fit` на масштабированных данных из заготовки) на 150 эпохах и сохраните после **каждой** эпохи AUC на обучении и валидации: списки `auc_train`, `auc_validation` (длины 150, без округления). Сохраните `best_epoch` — номер эпохи (от 1) с наибольшим AUC на валидации, `best_validation` (3 знака) и `gap_end` — разрыв «обучение − валидация» после последней эпохи (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_development, X_test, y_development, y_test = train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
X_train, X_validation, y_train, y_validation = train_test_split(X_development,y_development,test_size=.25,random_state=43,stratify=y_development)
sc = StandardScaler().fit(X_train)
A, B = sc.transform(X_train), sc.transform(X_validation)
```

### starter
```python
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

net = MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)
# Обучение: A и y_train, 1 350 гостей. Валидация: B и y_validation, 450 гостей.
print(A.shape, y_train.shape, B.shape, y_validation.shape)
auc_train, auc_validation = [], []

```

### check
```python
import numpy as _np
import warnings as _w
from sklearn.neural_network import MLPClassifier as _M
from sklearn.metrics import roc_auc_score as _auc
A0, B0, ya, yb = need('A'), need('B'), need('y_train'), need('y_validation')
n = _M(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0); tr, te = [], []
with _w.catch_warnings():
    _w.simplefilter('ignore')
    for _ in range(150):
        n.partial_fit(A0, ya, classes=[0, 1]); tr.append(_auc(ya, n.predict_proba(A0)[:, 1])); te.append(_auc(yb, n.predict_proba(B0)[:, 1]))
assert len(need('auc_train')) == 150 and _np.allclose(need('auc_validation'), te, atol=1e-9), 'auc_validation — AUC на валидации после каждой из 150 эпох.'
be = int(_np.argmax(te)) + 1
assert need('best_epoch') == be, f'best_epoch = {need("best_epoch")}, а нужно {be}.'
assert close(need('best_validation'), round(max(te), 3), 0.0011), f'best_validation = {need("best_validation")}.'
assert close(need('gap_end'), round(tr[-1] - te[-1], 3), 0.0011), f'gap_end = {need("gap_end")}.'
assert _np.asarray(need('auc_train')).shape == (150,) and _np.allclose(need('auc_train'), tr, atol=1e-9, rtol=1e-7), 'auc_train — AUC на обучении после каждой из 150 эпох, без округления.'
```

### hint
В цикле на 150 шагов: `net.partial_fit(A, y_train, classes=[0, 1])`, затем два `roc_auc_score` по `predict_proba(...)[:, 1]`.

### hint
Номер лучшей эпохи: `int(np.argmax(auc_validation)) + 1` — `argmax` считает с нуля, эпохи — с единицы.

### solution
```python
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

net = MLPClassifier(hidden_layer_sizes=(128,), alpha=0.0001, random_state=0)
auc_train, auc_validation = [], []
for epoch in range(150):
    net.partial_fit(A, y_train, classes=[0, 1])
    auc_train.append(roc_auc_score(y_train, net.predict_proba(A)[:, 1]))
    auc_validation.append(roc_auc_score(y_validation, net.predict_proba(B)[:, 1]))
best_epoch = int(np.argmax(auc_validation)) + 1
best_validation = round(max(auc_validation), 3)
gap_end = round(auc_train[-1] - auc_validation[-1], 3)
print(best_epoch, best_validation, gap_end)
```

### explain
Ищем максимальную AUC в списке auc_validation. Её индекс плюс один даёт номер эпохи. На этом разбиении максимум 0.873 достигнут на 59-й эпохе, а к 150-й разрыв между обучением и валидацией составил 0.088. Все 600 финальных гостей остаются для оценки выбранной процедуры.

## task: depth | Шире или глубже | plus

Сравните на оттоке три архитектуры при `alpha=1.0`, `max_iter=500`, `random_state=0` (конвейер со `StandardScaler`): `(8,)`, `(32,)`, `(64, 32)`. Сохраните `res` — словарь `{архитектура-строка: AUC на валидации}` с ключами `"8"`, `"32"`, `"64-32"` (3 знака), `params` — словарь с числом параметров каждой сети (сумма размеров `coefs_` и `intercepts_`), и `best` — ключ архитектуры с наибольшей AUC на 450 гостях внутренней валидации. При подборе используйте готовые пары X_train/y_train и X_validation/y_validation.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_development, X_final, y_development, y_final = train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
X_train, X_validation, y_train, y_validation = train_test_split(X_development,y_development,test_size=.25,random_state=43,stratify=y_development)
# Имена из предыдущей версии сохранены для старых решений.
X_test, y_test = X_validation, y_validation
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
Цикл по `archs.items()`: обучить конвейер с `hidden_layer_sizes=a`, AUC по `predict_proba(X_validation)[:, 1]`.

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
    res[key] = round(roc_auc_score(y_validation, m.predict_proba(X_validation)[:, 1]), 3)
    params[key] = int(sum(c.size for c in m[-1].coefs_) + sum(c.size for c in m[-1].intercepts_))
best = max(res, key=res.get)
print(res, params, best)
```

### explain
На этих 450 гостях AUC сетей (8,), (32,) и (64, 32) составила 0.869, 0.876 и 0.853. У варианта с 32 скрытыми нейронами в этом сравнении самая высокая AUC и 545 параметров. Более глубокая сеть имеет 3 137 параметров. При изменении разбиения порядок может измениться. Для устойчивого сравнения архитектур используйте кросс-валидацию на данных разработки.

## task: regression-net | Сеть для минут доставки | plus

Обучите `make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(32,), max_iter=2000, random_state=0))` на доставках (признаки — как в главе 10: `distance_km`, `items`, `hour`, флаги `courier`, `weather`, `shop_id`) и сравните с `HistGradientBoostingRegressor(random_state=0)`. При достижении предела в 2000 эпох возможно предупреждение `ConvergenceWarning`. Сохраните `mae_mlp`, `mae_hgb` (2 знака) и `winner` — `"сеть"` или `"бустинг"`.

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
Сопоставьте `mae_mlp` и `mae_hgb`. Меньшее число показывает, какая из двух моделей в среднем точнее предсказала длительность доставок на отложенных заказах. Чтобы сравнить скорость прогнозирования, измерьте время вызова `predict` на одной партии заказов на одном устройстве.

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
По средней AUC трёх валидационных фолдов в заданной сетке выбрана сеть с одним слоем из 16 нейронов и alpha = 1. Её средняя AUC равна 0.879. После обучения на всех 1 800 строках её AUC на 600 итоговых гостях составила около 0.91. У бустинга из условия на этих же гостях около 0.93. Это сравнение двух зафиксированных моделей на одном разбиении.
