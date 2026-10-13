---
title: Настройка бустинга
files: [deliveries.csv, guests_churn.csv]
lead: "У бустинга, в отличие от леса, слишком много деревьев вредит: в какой-то момент он начинает учить шум. Учимся видеть этот момент на кривой обучения, останавливаться вовремя, подбирать шаг и глубину и знакомимся с быстрым HistGradientBoosting, который сам справляется с пропусками и категориями."
recap:
  - "`staged_predict` выдаёт прогнозы после 1, 2, … деревьев — по ним строят кривую «число деревьев → ошибка»."
  - "Ошибка на обучении падает всегда, на отложенных данных — до минимума, потом растёт: это переобучение."
  - "Меньше learning_rate → нужно больше деревьев, но минимум обычно ниже и кривая пологая. Типичный шаг — 0.03–0.1."
  - "Раннюю остановку делают по валидации, а не по тесту: `n_iter_no_change` + `validation_fraction` в sklearn."
  - "`HistGradientBoostingRegressor/Classifier` — быстрый бустинг: бьёт признаки на интервалы, сам понимает пропуски и категориальные признаки."
---

## Кривая обучения бустинга

Лес можно растить сколько угодно — новые деревья лишь усредняются с остальными. В бустинге каждое дерево подгоняет модель под оставшиеся ошибки обучающей выборки, и в какой-то момент «оставшиеся ошибки» — это уже шум. Увидеть момент помогает `staged_predict`: он возвращает прогнозы после каждого добавленного дерева.

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

fig, ax = plt.subplots(figsize=(7, 4))
for lr in (0.3, 0.1, 0.03):
    gb = GradientBoostingRegressor(n_estimators=600, learning_rate=lr, max_depth=3, random_state=0).fit(X_train, y_train)
    curve = [mean_absolute_error(y_test, p) for p in gb.staged_predict(X_test)]
    ax.plot(range(1, 601), curve, label=f"шаг {lr}")
ax.set_ylim(3.6, 6)
ax.set_xlabel("число деревьев")
ax.set_ylabel("MAE на отложенных данных")
ax.legend()
plt.show()
```

**Что здесь происходит:**

- Для каждого шага обучаем бустинг сразу на 600 деревьях.
- `gb.staged_predict(X_test)` — генератор: выдаёт прогноз после первого дерева, после второго, … после 600-го. Переобучать модель 600 раз не нужно.
- `curve` — MAE после каждого числа деревьев; `ax.set_ylim(3.6, 6)` — обрезаем ось, чтобы разглядеть минимумы.

Три кривые — три характера:

- **шаг 0.3** — быстро падает до минимума (около 3.85 при ~80 деревьях), дальше заметно растёт: к 600 деревьям ошибка уже 4.4;
- **шаг 0.1** — минимум ниже и позже (около 3.80 при ~175 деревьях), потом растёт медленнее;
- **шаг 0.03** — за 600 деревьев ещё не дошёл до дна, но кривая гладкая и уже почти на уровне лучших.

На обучающих данных все три кривые падают до конца — переобучение видно только на отложенных.

::: figure boost-train-test
Кривые из кода выше для шагов 0.3 и 0.1 и ошибка того же бустинга с шагом 0.1 на обучающих строках. Пунктир падает до конца, а сплошные линии после минимума поднимаются: поздние деревья учат шум.
:::

::: warn
Мы рисовали кривую по тестовой выборке, чтобы показать явление. Выбирать число деревьев по тесту нельзя — это подглядывание из главы 6. Для выбора нужна отдельная валидация.
:::

::: quiz
С ростом числа деревьев ошибка бустинга на обучающих данных падает до самого конца, а на отложенных после минимума начинает расти. Почему кривые расходятся?

- [x] Поздние деревья подгоняют модель под оставшиеся ошибки обучающей выборки — то есть под её шум, которого в новых данных нет
  > Каждое дерево учится на остатках **обучающих** строк. Когда закономерности выучены, остатки — это случайность конкретной выборки, и подгонка под неё вредит на новых данных.
- [ ] В отложенных данных больше выбросов, поэтому ошибка на них растёт
  > Выбросы дали бы просто более высокий уровень ошибки, а не рост после минимума. Рост — признак переобучения.
- [ ] `staged_predict` на новых данных накапливает ошибку округления
  > Прогноз после сотого дерева — та же сумма, что дал бы `predict` у модели из ста деревьев. Округление тут ни при чём.
- [ ] Шаг обучения слишком маленький, и модель не успевает дойти до минимума
  > При слишком маленьком шаге ошибка на отложенных ещё падала бы, а не росла. Шаг 0.03 как раз не дошёл до дна, но и не начал расти.
:::

{{practice: staged, train-vs-test}}

## Ранняя остановка

`GradientBoostingRegressor` умеет останавливаться сам: откладывает часть обучающих данных (`validation_fraction`) и прекращает строить деревья, когда ошибка на них перестала улучшаться (точное правило — в разборе кода ниже). `n_estimators` при этом — только верхняя граница.

::: tip Аналогия
Так обжарщик не ставит таймер «на час», а снимает пробу каждые полминуты и выключает барабан, когда несколько проб подряд не стали вкуснее. Пробы при этом берут из отдельной горсти, а не из партии, которую потом отдадут гостям на дегустацию, — как валидацию откладывают из обучающих строк, не трогая тест. Хромает аналогия в одном: зерно с каждой минутой меняется необратимо, а в бустинге уже построенные деревья не портятся — просто новые начинают учить шум.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

gb = GradientBoostingRegressor(n_estimators=2000, learning_rate=0.1, max_depth=3,
                               n_iter_no_change=20, validation_fraction=0.15, random_state=0)
gb.fit(X_train, y_train)
print("деревьев построено:", gb.n_estimators_)
print("MAE на тесте:", round(mean_absolute_error(y_test, gb.predict(X_test)), 2))
```

**Что здесь происходит:**

- `n_estimators=2000` — верхняя граница, а не «сколько построить».
- `validation_fraction=0.15` — 15 % **обучающих** строк откладываются для проверки; тест не участвует.
- `n_iter_no_change=20` — правило остановки: sklearn прекращает обучение, когда новое дерево не улучшило ошибку на отложенных строках ни относительно одного из 20 предыдущих. На рисунке ниже это 155-е дерево.
- `gb.n_estimators_` (с подчёркиванием в конце) — сколько деревьев реально построено.

Из 2000 разрешённых модель построила около 150 деревьев и остановилась — без подглядывания в тест, с ошибкой около 3.9.

::: figure early-stop
Сверху — откуда берётся валидация: 15 % обучающих строк, тест не участвует. Снизу — ошибка на этих 207 строках по мере роста модели (мы повторили расчёт sklearn тем же разбиением). Лучшее дерево — 138-е; на 155-м ошибка оказалась хуже, чем у каждого из 20 предыдущих, и sklearn остановился.
:::

::: quiz
На валидации ошибка бустинга падала до 300-го дерева, потом начала расти. Что разумно сделать?

- [x] Остановиться около 300 деревьев: дальше модель подгоняется под шум обучающих данных
  > Это ранняя остановка: число деревьев выбирают по валидации, а не «чем больше, тем лучше».
- [ ] Взять 1000 деревьев — больше значит лучше
  > Для бустинга это неверно: каждое новое дерево доучивает и шум.
- [ ] Увеличить шаг обучения
  > Тогда переобучение начнётся ещё раньше.
- [ ] Выбрать число деревьев по тесту
  > Тест — только для итоговой оценки, выбирают по валидации.
:::

{{practice: p-early, early-stop}}

## Главные гиперпараметры

| параметр | что делает | с чего начать |
|---|---|---|
| `learning_rate` | длина шага; меньше — точнее, но нужно больше деревьев | 0.05–0.1 |
| `n_estimators` | сколько деревьев; лучше подбирать ранней остановкой | 100–1000 |
| `max_depth` | сложность одного дерева, то есть каких «сочетаний» признаков модель может выучить | 3–6 |
| `min_samples_leaf` | минимум строк в листе; защищает от подгонки под единичные случаи | 10–50 |
| `subsample` | доля строк для каждого дерева (как бутстрэп в лесу); меньше 1 — меньше переобучения | 0.7–1.0 |

Подбирают их как обычно — `GridSearchCV` или `RandomizedSearchCV` из главы 7. Порядок на практике: зафиксировать шаг 0.1, подобрать глубину и минимум в листе, затем уменьшить шаг и найти число деревьев ранней остановкой.

::: predict
```python static
lr_old, n_old = 0.1, 200
lr_new = 0.05
print(int(n_old * lr_old / lr_new))
```

- `100`
- [x] `400`
- `200`

Почему: эмпирическое правило — «шаг × число деревьев ≈ постоянно». Уменьшили шаг вдвое — деревьев нужно примерно вдвое больше.
:::

{{practice: shrink, subsample, grid-boost}}

## Быстрый бустинг: HistGradientBoosting

Классический `GradientBoostingRegressor` перебирает все возможные пороги в каждом узле — на сотнях тысяч строк это медленно. `HistGradientBoostingRegressor` (и `...Classifier`) сначала разбивает каждый признак на 255 интервалов («гистограмму») и ищет пороги только между ними. Это в десятки раз быстрее на больших данных, и ещё:

- **пропуски** обрабатываются сами — их не нужно заполнять;
- **категориальные признаки** можно отдать без `get_dummies`: тип `category` в pandas и `categorical_features="from_dtype"`;
- ранняя остановка включается автоматически, если строк больше 10 000.

::: figure hist-bins
Сверху — пороги-кандидаты обычного бустинга: между каждой парой соседних значений признака. Снизу — тот же признак `distance_km`, разбитый на 8 интервалов по квантилям: в каждом примерно поровну доставок (числа в прямоугольниках), пороги только на границах.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)   # avg_check с пропусками!
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

hgb = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0)
hgb.fit(X_train, y_train)
rf = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)
rf.fit(X_train.fillna(0), y_train)
print("бустинг AUC:", round(roc_auc_score(y_test, hgb.predict_proba(X_test)[:, 1]), 3))
print("лес AUC:    ", round(roc_auc_score(y_test, rf.predict_proba(X_test.fillna(0))[:, 1]), 3))
```

**Что здесь происходит:**

- `pd.get_dummies(...)` без `fillna` — в `avg_check` остаются пропуски у гостей без визитов.
- `HistGradientBoostingClassifier` принимает такую таблицу как есть: в каждом узле он решает, в какую ветку отправлять пропуски, — это тоже выучивается.
- Лесу из sklearn пропуски нужно заполнить (`fillna(0)`), иначе — ошибка.
- `max_iter` у HGB — то же, что `n_estimators` у обычного бустинга.

Бустинг съел пропуски в `avg_check` без `fillna` и дал AUC около 0.93 — чуть лучше леса. На маленьких данных разница между хорошо настроенными бустингом и лесом часто невелика; бустинг выигрывает на больших таблицах со сложными взаимодействиями.

В промышленности бустинг чаще берут из специализированных библиотек — CatBoost и LightGBM. Им посвящён урок «CatBoost и LightGBM в своём Jupyter» после проекта главы: там они сравниваются на данных проекта.

{{practice: hgb-nan}}

## Разберём вместе: категории без get_dummies

`HistGradientBoosting` умеет работать с категориями напрямую: вместо 10 столбцов-флагов для курьера, погоды и кофейни — 3 столбца типа `category`. Дерево само решает, какие категории отправить налево, а какие направо. Сравним на доставках:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "hour", "courier", "weather", "shop_id"]
y = ok["actual_min"]

X_dum = pd.get_dummies(ok[cols], dtype=int)
X_cat = ok[cols].copy()
for c in ["courier", "weather", "shop_id"]:
    X_cat[c] = X_cat[c].astype("category")              # тип «категория» — сигнал для бустинга

for name, X in [("get_dummies", X_dum), ("category", X_cat)]:
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
    m = HistGradientBoostingRegressor(max_iter=300, max_depth=3, categorical_features="from_dtype", random_state=0)
    m.fit(X_tr, y_tr)
    print(f"{name:12}: столбцов {X.shape[1]:2}, MAE {mean_absolute_error(y_te, m.predict(X_te)):.3f}")
```

**Что здесь происходит:**

- `.astype("category")` — pandas хранит столбец как набор категорий; `categorical_features="from_dtype"` говорит бустингу: «столбцы этого типа — категории».
- Одинаковый `random_state=42` в разбиении — строки в тесте те же, сравнение честное.

**Что получилось:** качество практически одинаковое (около 3.9), а столбцов вдвое меньше. На наших данных категорий мало, и `get_dummies` справляется. Выигрыш нативных категорий виден, когда значений сотни (например, тысячи кофеен или товаров): флаги раздувают таблицу, а бустинг с категориями — нет. CatBoost (урок «CatBoost и LightGBM в своём Jupyter») устроен ещё хитрее и особенно хорош именно в таких задачах.

{{practice: native-cat}}

## Практика

## task: staged | Кривая по деревьям | warmup

Обучите `GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=0)` и с помощью `staged_predict` соберите список `curve` — MAE на тесте после каждого дерева (100 чисел). Сохраните `best_n` — число деревьев с наименьшей ошибкой.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
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
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import GradientBoostingRegressor as _GB
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
cv = [_mae(dd, p) for p in _GB(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=0).fit(a, c).staged_predict(b)]
got = need('curve')
assert len(got) == 100 and _np.allclose(got, cv, atol=1e-6), 'curve — 100 значений MAE на тесте после каждого дерева.'
assert need('best_n') == int(_np.argmin(cv)) + 1, f'best_n = {need("best_n")}, а нужно {int(_np.argmin(cv)) + 1}. Число деревьев считается с 1.'
```

### hint
`staged_predict` возвращает прогнозы после каждого дерева — по ним можно посчитать MAE для каждого числа деревьев одним списковым выражением.

### hint
`[mean_absolute_error(y_test, p) for p in gb.staged_predict(X_test)]`; номер минимума — `np.argmin(curve) + 1`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=0).fit(X_train, y_train)
curve = [mean_absolute_error(y_test, p) for p in gb.staged_predict(X_test)]
best_n = int(np.argmin(curve)) + 1
```

### explain
При 100 деревьях с шагом 0.1 минимум приходится на самый конец — модель ещё не переобучилась. Переобучение начнётся позже, как видно на кривой в теории.

## task: shrink | Шаг обучения руками | warmup

Упрощённый бустинг на одном числе: ответ `y = 10`, стартовый прогноз 0, и каждое новое дерево **точно** угадывает текущий остаток, но добавляется с весом `lr = 0.1`. Тогда после каждого дерева прогноз растёт на 10 % оставшегося остатка. Посчитайте циклом список `preds` — прогнозы после 1, 2, …, 40 деревьев — и `n_needed` — первое число деревьев, при котором прогноз не меньше 9.5.

### starter
```python
y, lr = 10, 0.1
pred = 0
preds = []

```

### check
```python
p = 0; want = []
for _ in range(40):
    p += 0.1 * (10 - p); want.append(p)
got = need('preds')
assert len(got) == 40 and all(close(a, b, 1e-9) for a, b in zip(got, want)), 'preds не совпадает: на каждом шаге pred += lr * (y - pred).'
assert need('n_needed') == next(i + 1 for i, v in enumerate(want) if v >= 9.5), f'n_needed = {need("n_needed")}.'
```

### hint
Один шаг: остаток `y - pred`, к прогнозу прибавляем `lr * остаток`. Повторить 40 раз, складывая прогнозы в список.

### hint
Первое число деревьев с прогнозом ≥ 9.5: `next(i + 1 for i, v in enumerate(preds) if v >= 9.5)` — или цикл с `break`.

### solution
```python
y, lr = 10, 0.1
pred = 0
preds = []
for _ in range(40):
    pred += lr * (y - pred)
    preds.append(pred)
n_needed = next(i + 1 for i, v in enumerate(preds) if v >= 9.5)
```

### explain
После первого дерева прогноз — 1, после второго — 1.9, потом 2.71…: остаток каждый раз умножается на 0.9. До 9.5 нужно 29 деревьев (0.9²⁹ ≈ 0.047). С `lr = 1` хватило бы одного — но настоящие деревья ошибаются, и большой шаг повторяет их ошибки целиком. Маленький шаг — это «доверяй каждому дереву понемногу», за что платят числом деревьев.

## task: p-early | Ранняя остановка | warmup

Соберите обучение бустинга с ранней остановкой и печать числа построенных деревьев.

### parsons
```python
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
rng = np.random.default_rng(0)
X = rng.normal(size=(500, 3))
y = X[:, 0] * 3 + rng.normal(size=500)
gb = GradientBoostingRegressor(n_estimators=1000, n_iter_no_change=10, validation_fraction=0.2, random_state=0)
gb.fit(X, y)
print(gb.n_estimators_ < 1000)
```

### check
```python
assert _lines == ['True'], f'Сейчас: {_lines}.'
```

### hint
Сначала данные, потом модель с параметрами остановки, обучение и печать.

### hint
Число построенных деревьев — атрибут с подчёркиванием в конце: `n_estimators_`.

## task: train-vs-test | Где начинается переобучение | base

Обучите `GradientBoostingRegressor(n_estimators=400, learning_rate=0.3, max_depth=3, random_state=0)`. По `staged_predict` соберите MAE на обучении (`tr`) и на тесте (`te`) — по 400 чисел. Сохраните `best_n` (минимум на тесте), `te_best`, `te_last` (MAE на тесте при лучшем числе деревьев и при 400, 3 знака) и `tr_last` (MAE на обучении при 400, 3 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
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
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import GradientBoostingRegressor as _GB
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
g = _GB(n_estimators=400, learning_rate=0.3, max_depth=3, random_state=0).fit(a, c)
te = [_mae(dd, p) for p in g.staged_predict(b)]; tr = [_mae(c, p) for p in g.staged_predict(a)]
k = int(_np.argmin(te)) + 1
assert need('best_n') == k, f'best_n = {need("best_n")}, а нужно {k}.'
assert close(need('te_best'), round(te[k - 1], 3), 0.002) and close(need('te_last'), round(te[-1], 3), 0.002), f'te_best, te_last = {need("te_best")}, {need("te_last")}.'
assert close(need('tr_last'), round(tr[-1], 3), 0.002), f'tr_last = {need("tr_last")}.'
```

### hint
Два списка через `staged_predict(X_train)` и `staged_predict(X_test)`.

### hint
Лучшее число деревьев — номер минимума тестовой кривой: `int(np.argmin(te)) + 1`; MAE при нём — `te[best_n - 1]`, при 400 — `te[-1]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

gb = GradientBoostingRegressor(n_estimators=400, learning_rate=0.3, max_depth=3, random_state=0).fit(X_train, y_train)
tr = [mean_absolute_error(y_train, p) for p in gb.staged_predict(X_train)]
te = [mean_absolute_error(y_test, p) for p in gb.staged_predict(X_test)]
best_n = int(np.argmin(te)) + 1
te_best, te_last = round(te[best_n - 1], 3), round(te[-1], 3)
tr_last = round(tr[-1], 3)
```

### explain
С шагом 0.3 модель быстро доходит до минимума и потом переобучается: ошибка на обучении продолжает падать (до двух с небольшим минут), а на тесте растёт. Разрыв между ними — мера переобучения, как в главе 6.

## task: early-stop | Остановка по валидации | base

Найдите число деревьев честно: отделите от обучающих данных валидацию (`train_test_split(X_train, y_train, test_size=0.2, random_state=0)`), обучите бустинг на 600 деревьев (шаг 0.1, глубина 3, `random_state=0`) на оставшейся части, найдите по `staged_predict` лучшее число деревьев на валидации `best_n`, затем обучите модель с `n_estimators=best_n` на **всех** обучающих данных и сохраните `test_mae` (2 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
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
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import GradientBoostingRegressor as _GB
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
a1, v, c1, vy = _tts(a, c, test_size=0.2, random_state=0)
g = _GB(n_estimators=600, learning_rate=0.1, max_depth=3, random_state=0).fit(a1, c1)
k = int(_np.argmin([_mae(vy, p) for p in g.staged_predict(v)])) + 1
assert need('best_n') == k, f'best_n = {need("best_n")}, а нужно {k}. Выбирайте по валидации, а не по тесту.'
t = round(_mae(dd, _GB(n_estimators=k, learning_rate=0.1, max_depth=3, random_state=0).fit(a, c).predict(b)), 2)
assert close(need('test_mae'), t, 0.011), f'test_mae = {need("test_mae")}, а нужно {t}.'
```

### hint
Схема: обучающая часть делится ещё раз на «обучение» и «валидацию»; по валидации выбирают число деревьев, финальную модель проверяют на тесте.

### hint
Сначала второе разбиение — `X_fit, X_val, y_fit, y_val`. Тест в выборе числа деревьев не участвует.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

X_fit, X_val, y_fit, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=0)
gb = GradientBoostingRegressor(n_estimators=600, learning_rate=0.1, max_depth=3, random_state=0).fit(X_fit, y_fit)
val_curve = [mean_absolute_error(y_val, p) for p in gb.staged_predict(X_val)]
best_n = int(np.argmin(val_curve)) + 1
final = GradientBoostingRegressor(n_estimators=best_n, learning_rate=0.1, max_depth=3, random_state=0).fit(X_train, y_train)
test_mae = round(mean_absolute_error(y_test, final.predict(X_test)), 2)
```

### explain
Валидация выбрала около 220 деревьев, и на тесте получилось около 3.81 — почти как лучший результат «с подглядыванием». Так и выглядит честная процедура: тест видит только финальную модель.

## task: subsample | Помогает ли подвыборка | base

Параметр `subsample` строит каждое дерево на случайной доле строк — как бутстрэп в лесу. Проверьте на доставках: `GradientBoostingRegressor(n_estimators=300, learning_rate=0.1, max_depth=3, random_state=0)` с `subsample` из `[1.0, 0.7, 0.5]`. Сохраните `mae_by_sub` — словарь `{subsample: MAE на тесте}` (3 знака) и `helps` — `True`, если хоть одно значение меньше 1.0 улучшило MAE больше чем на 0.01.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
```

### starter
```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

```

### check
```python
from sklearn.ensemble import GradientBoostingRegressor as _G
from sklearn.metrics import mean_absolute_error as _mae
a, b, c, d_ = need('X_train'), need('X_test'), need('y_train'), need('y_test')
w = {sb: round(_mae(d_, _G(n_estimators=300, learning_rate=0.1, max_depth=3, subsample=sb, random_state=0).fit(a, c).predict(b)), 3) for sb in [1.0, 0.7, 0.5]}
g = {float(k): v for k, v in need('mae_by_sub', dict).items()}
assert all(close(g[k], w[k], 0.002) for k in w), f'mae_by_sub = {g}, а нужно {w}.'
assert bool(need('helps')) == any(w[1.0] - w[k] > 0.01 for k in [0.7, 0.5]), 'helps — улучшилась ли MAE больше чем на 0.01 хотя бы при одном subsample < 1.'
```

### hint
Словарное выражение по `subsample`; MAE — `mean_absolute_error(y_test, model.predict(X_test))`.

### hint
`helps = any(mae_by_sub[1.0] - mae_by_sub[s] > 0.01 for s in [0.7, 0.5])`.

### solution
```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

mae_by_sub = {}
for sub in [1.0, 0.7, 0.5]:
    gb = GradientBoostingRegressor(n_estimators=300, learning_rate=0.1, max_depth=3, subsample=sub, random_state=0)
    mae_by_sub[sub] = round(mean_absolute_error(y_test, gb.fit(X_train, y_train).predict(X_test)), 3)
helps = any(mae_by_sub[1.0] - mae_by_sub[s] > 0.01 for s in [0.7, 0.5])
print(mae_by_sub, helps)
```

### explain
Здесь подвыборка не помогает: 0.7 даёт ту же ошибку, а 0.5 — даже хуже. Это нормальный результат: «рецепты» из таблицы гиперпараметров — отправные точки, а не гарантии. Подвыборка помогает, когда бустинг переобучается (много деревьев, глубокие деревья, мало данных); у нас 300 неглубоких деревьев и шаг 0.1 — переобучения почти нет, и лечить нечего.

## task: native-cat | Категории без флагов | plus

Повторите разбор урока: `HistGradientBoostingRegressor(max_iter=300, max_depth=3, categorical_features="from_dtype", random_state=0)` на доставках в двух вариантах — признаки через `pd.get_dummies` и признаки с курьером, погодой и кофейней как `category`. Разбиение одинаковое: `train_test_split(..., test_size=0.25, random_state=42)`. Сохраните `res` — словарь `{"dummies": (число столбцов, MAE), "category": (число столбцов, MAE)}` (MAE — 3 знака) и `n_categories` — общее число разных значений в трёх категориальных столбцах.

### setup
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "hour", "courier", "weather", "shop_id"]
y = ok["actual_min"]
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

res = {}

```

### check
```python
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.metrics import mean_absolute_error as _mae
ok0, cols0, y0 = need('ok'), need('cols'), need('y')
import pandas as _pd
Xd = _pd.get_dummies(ok0[cols0], dtype=int)
Xc = ok0[cols0].copy()
for c in ['courier', 'weather', 'shop_id']: Xc[c] = Xc[c].astype('category')
w = {}
for k, X_ in [('dummies', Xd), ('category', Xc)]:
    a, b, c, d_ = _tts(X_, y0, test_size=0.25, random_state=42)
    m = _H(max_iter=300, max_depth=3, categorical_features='from_dtype', random_state=0).fit(a, c)
    w[k] = (X_.shape[1], round(_mae(d_, m.predict(b)), 3))
g = {k: tuple(v) for k, v in need('res', dict).items()}
assert all(g[k][0] == w[k][0] and close(g[k][1], w[k][1], 0.002) for k in w), f'res = {g}, а нужно {w}.'
assert need('n_categories') == sum(ok0[c].nunique() for c in ['courier', 'weather', 'shop_id']), f'n_categories = {need("n_categories")}.'
```

### hint
Категории: `X_cat = ok[cols].copy()`, затем для трёх столбцов `X_cat[c] = X_cat[c].astype("category")`.

### hint
Число разных значений столбца — `.nunique()`; сложите по трём столбцам.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

X_dum = pd.get_dummies(ok[cols], dtype=int)
X_cat = ok[cols].copy()
for c in ["courier", "weather", "shop_id"]:
    X_cat[c] = X_cat[c].astype("category")
res = {}
for name, X in [("dummies", X_dum), ("category", X_cat)]:
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
    m = HistGradientBoostingRegressor(max_iter=300, max_depth=3, categorical_features="from_dtype", random_state=0).fit(X_tr, y_tr)
    res[name] = (X.shape[1], round(mean_absolute_error(y_te, m.predict(X_te)), 3))
n_categories = sum(ok[c].nunique() for c in ["courier", "weather", "shop_id"])
print(res, n_categories)
```

### explain
Ошибка одинаковая с точностью до сотых, а столбцов 6 вместо 16. Флаги для 13 категорий — не проблема; проблема начинается, когда категорий тысячи (артикулы, адреса): `get_dummies` раздувает таблицу до тысяч почти пустых столбцов. Тогда нативные категории HGB или CatBoost не только экономят память, но часто и точнее — им не нужно собирать «группу похожих значений» из отдельных флагов.

## task: hgb-nan | Бустинг без заполнения пропусков | plus

На `guests_churn.csv` (признаки — `get_dummies` без `fillna`, `card_blocked` исключить) обучите `HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0)` и `RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)` (лесу пропуски заполните нулём). Сохраните `auc_hgb`, `auc_rf` (3 знака) и `nan_in_train` — число пропусков в `X_train`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import HistGradientBoostingClassifier as _H, RandomForestClassifier as _RF
from sklearn.metrics import roc_auc_score as _auc
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X0 = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
a, b, c, d = _tts(X0, y, test_size=0.25, random_state=42, stratify=y)
h = round(_auc(d, _H(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0).fit(a, c).predict_proba(b)[:, 1]), 3)
r = round(_auc(d, _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a.fillna(0), c).predict_proba(b.fillna(0))[:, 1]), 3)
assert close(need('auc_hgb'), h, 0.002), f'auc_hgb = {need("auc_hgb")}, а нужно {h}.'
assert close(need('auc_rf'), r, 0.002), f'auc_rf = {need("auc_rf")}, а нужно {r}.'
assert need('nan_in_train') == int(a.isna().sum().sum()), f'nan_in_train = {need("nan_in_train")}.'
```

### hint
Число пропусков во всей таблице: `X_train.isna().sum().sum()`.

### hint
HGB обучается прямо на `X_train` с пропусками; лесу передайте `X_train.fillna(0)` и `X_test.fillna(0)`. AUC — по `predict_proba(...)[:, 1]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

nan_in_train = int(X_train.isna().sum().sum())
hgb = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_depth=3, random_state=0).fit(X_train, y_train)
rf = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train.fillna(0), y_train)
auc_hgb = round(roc_auc_score(y_test, hgb.predict_proba(X_test)[:, 1]), 3)
auc_rf = round(roc_auc_score(y_test, rf.predict_proba(X_test.fillna(0))[:, 1]), 3)
```

### explain
Для пропуска `HistGradientBoosting` в каждом узле сам решает, в какую ветку его отправить, — по тому, где ошибка меньше. Это часто лучше ручного заполнения: «пропуск» сам по себе может быть сигналом (здесь — «гость вообще не приходил»).

## task: grid-boost | Подбор глубины и шага | star

Подберите для `HistGradientBoostingClassifier(max_iter=200, random_state=0)` на оттоке параметры по сетке `{"learning_rate": [0.05, 0.1], "max_depth": [2, 3, 5]}` через `GridSearchCV(..., cv=3, scoring="roc_auc")` на обучающей части. Сохраните `best_params` (словарь), `cv_auc` — лучший средний AUC на кросс-валидации и `test_auc` — AUC лучшей модели на тесте (оба 3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, GridSearchCV as _GS
from sklearn.ensemble import HistGradientBoostingClassifier as _H
from sklearn.metrics import roc_auc_score as _auc
_bp, _cv, _ta = need('best_params'), need('cv_auc'), need('test_auc')   # сначала — есть ли ответы (эталон считается долго)
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X0 = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
a, b, c, d = _tts(X0, y, test_size=0.25, random_state=42, stratify=y)
gs = _GS(_H(max_iter=200, random_state=0), {'learning_rate': [0.05, 0.1], 'max_depth': [2, 3, 5]}, cv=3, scoring='roc_auc').fit(a, c)
assert dict(need('best_params')) == gs.best_params_, f'best_params = {need("best_params")}, а нужно {gs.best_params_}.'
assert close(need('cv_auc'), round(gs.best_score_, 3), 0.002), f'cv_auc = {need("cv_auc")}.'
assert close(need('test_auc'), round(_auc(d, gs.predict_proba(b)[:, 1]), 3), 0.002), f'test_auc = {need("test_auc")}.'
```

### hint
Имена параметров в сетке — как у самой модели (`max_depth`, `learning_rate`), если `GridSearchCV` получает модель без конвейера.

### hint
После `fit` у `GridSearchCV` есть `best_params_`, `best_score_`, а `predict_proba` сам использует лучшую модель (глава 7).

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

grid = GridSearchCV(HistGradientBoostingClassifier(max_iter=200, random_state=0),
                    {"learning_rate": [0.05, 0.1], "max_depth": [2, 3, 5]}, cv=3, scoring="roc_auc")
grid.fit(X_train, y_train)
best_params = grid.best_params_
cv_auc = round(grid.best_score_, 3)
test_auc = round(roc_auc_score(y_test, grid.predict_proba(X_test)[:, 1]), 3)
```

### explain
На оттоке побеждают неглубокие деревья с маленьким шагом: данных немного (1800 строк в обучении), и сложной модели легко переобучиться. На больших таблицах оптимальная глубина обычно больше.
