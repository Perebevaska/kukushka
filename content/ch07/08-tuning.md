---
title: Подбор гиперпараметров
lead: "У модели и подготовки есть настройки, которые не выучиваются из данных: сила регуляризации, веса классов, глубина деревьев. Учимся перебирать их честно и автоматически — `GridSearchCV` по всему конвейеру, — читать таблицу результатов, один раз проверять итог на тесте и сохранять готовую модель в файл."
files: [guests_churn.csv]
recap:
  - "Гиперпараметр — настройка, которую задаём мы, а не модель выучивает сама: `C`, `class_weight`, `max_depth`, стратегия заполнения пропусков."
  - "`GridSearchCV(pipe, param_grid, scoring=..., cv=kf)` перебирает все сочетания из сетки и для каждого делает кросс-валидацию. Обучений — сочетания × фолды (+1 итоговое)."
  - "Параметр шага конвейера называется `шаг__параметр`: `model__C`, `prep__num__simpleimputer__strategy`. Все имена — в `pipe.get_params()`."
  - "`best_params_` — лучшие настройки, `best_score_` — их средняя оценка на CV, `best_estimator_` — конвейер с ними, переобученный на всей обучающей части."
  - "`pd.DataFrame(search.cv_results_)` — таблица всех сочетаний: `mean_test_score`, `std_test_score`, `rank_test_score`. Разница меньше разброса — не повод выбирать сложное."
  - "`RandomizedSearchCV(..., n_iter=k, random_state=...)` проверяет k случайных сочетаний — когда полная сетка слишком велика."
  - "Тест — один раз, в самом конце. Готовую модель сохраняют `joblib.dump(model, файл)` и загружают `joblib.load(файл)`."
---

## Настройки, которые не выучиваются

Модель учится на данных: логистическая регрессия подбирает коэффициенты, дерево — вопросы и пороги. Но часть решений принимаем мы сами ещё до обучения: сила регуляризации `C` (урок «Регуляризация: штраф за большие веса»), веса классов `class_weight` (урок «Дисбаланс классов»), глубина дерева и размер листа, даже стратегия заполнения пропусков. Такие настройки называют **гиперпараметрами** — «параметрами над параметрами».

В главе 6 (урок «Честное сравнение моделей») мы подбирали глубину дерева циклом по валидации. Сделаем так же для `C` логистической регрессии — но уже с конвейером из прошлого урока и кросс-валидацией по F1:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

for C in [0.01, 0.1, 1, 10]:
    pipe.set_params(model__C=C)
    f1 = cross_val_score(pipe, X_train, y_train, cv=kf, scoring="f1")
    print(C, round(f1.mean(), 3))
```

`pipe.set_params(model__C=C)` меняет параметр `C` у шага `model` прямо внутри конвейера. Двойное подчёркивание `__` разделяет имя шага и имя параметра.

Сильная регуляризация (`C=0.01`) заметно портит F1 — около 0.56; дальше F1 растёт до 0.62 и почти перестаёт меняться. Цикл понятный, но если добавить второй гиперпараметр — веса классов, — понадобится вложенный цикл, словарь результатов, поиск лучшего… Всё это уже собрано в один инструмент.

{{practice: grid-keys}}

## GridSearchCV: перебор по сетке

**GridSearchCV** — «поиск по сетке с кросс-валидацией». Ему передают конвейер и **сетку** — словарь «имя параметра → список значений». Он перебирает все сочетания значений, для каждого делает кросс-валидацию и запоминает лучшее.

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

param_grid = {
    "model__C": [0.01, 0.1, 1, 10],
    "model__class_weight": [None, "balanced"],
}
search = GridSearchCV(pipe, param_grid, scoring="f1", cv=kf)
search.fit(X_train, y_train)
print(search.best_params_)
print(round(search.best_score_, 3))
```

- `param_grid` — 4 значения `C` × 2 варианта весов = 8 сочетаний;
- `scoring="f1"` — по какой метрике выбирать (те же названия, что в `cross_val_score`);
- `cv=kf` — наши фолды; каждое сочетание обучается 5 раз — всего 40 обучений;
- `best_params_` — сочетание с лучшим средним F1, `best_score_` — этот средний F1.

Веса классов `"balanced"` поднимают F1 примерно до 0.67 — так же, как в уроке «Дисбаланс классов» они поднимали полноту. А вот какое именно `C` победило — дело случая, это видно в таблице ниже.

После перебора `GridSearchCV` делает ещё одно, 41-е обучение: конвейер с лучшими настройками заново учится на **всей** обучающей части. Готовый конвейер лежит в `search.best_estimator_`, а сам `search` можно использовать как модель: `search.predict(X)` и `search.predict_proba(X)` вызывают именно его. Но `search` — это обёртка: внутри неё таблица перебора, все настройки и лучший конвейер. В работу и в файл отдают только чистый конвейер — `search.best_estimator_`.

::: figure grid-cost
Сетка из примера: 4 значения `C` × 2 варианта весов. Каждое сочетание проходит 5 фолдов, и ещё одно обучение — лучшего сочетания на всей обучающей части.
:::

::: tip Аналогия
Бариста настраивает новую кофемолку: три степени помола × три температуры воды. Он варит пробную чашку для каждого из девяти сочетаний и каждую пробует несколько раз, чтобы не обмануться одной удачной. Потом выставляет лучшее сочетание и варит уже на нём. GridSearchCV — та же дегустация: сочетания × проверки + одна финальная настройка.
:::

::: predict
```python static
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier
X = [[i] for i in range(20)]
y = [0] * 10 + [1] * 10
grid = {"max_depth": [1, 2, 3], "min_samples_leaf": [1, 5]}
s = GridSearchCV(DecisionTreeClassifier(random_state=0), grid, cv=5).fit(X, y)
print(len(s.cv_results_["params"]))
```

- `5`
- [x] `6`
- `30`

Почему: в `cv_results_` одна запись на **сочетание** — 3 × 2 = 6. Обучений было больше: 6 сочетаний × 5 фолдов = 30 (и ещё одно итоговое), но в таблице каждое сочетание — одна строка со средней оценкой по фолдам.
:::

### Как называются параметры

Имя в сетке — путь до параметра через имена шагов: `model__C` — параметр `C` шага `model`. Если шаг вложен глубже, путь длиннее: заполнитель пропусков в нашем `pre` — это `prep__num__simpleimputer__strategy` (шаг `prep` → его часть `num` → шаг `simpleimputer`, имя которому дал `make_pipeline` → параметр `strategy`).

Все доступные имена перечисляет `pipe.get_params()` — словарь «имя → текущее значение». Искать в нём удобно так:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

print([k for k in pipe.get_params() if k.startswith("model__")][:6])
print([k for k in pipe.get_params() if "imputer" in k])
```

::: predict
```python static
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
pipe = make_pipeline(StandardScaler(), LogisticRegression())
params = pipe.get_params()
print("model__C" in params, "logisticregression__C" in params)
```

- `True False`
- [x] `False True`
- `True True`

Почему: `make_pipeline` называет шаги по классу — `logisticregression`. Шага `model` нет, и сетка с ключом `model__C` упала бы с ошибкой «Invalid parameter».
:::

::: warn Сетки растут быстро
Число сочетаний — произведение длин списков: 4 × 2 = 8, но 5 × 4 × 3 × 2 = 120, а с кросс-валидацией на 5 фолдах — 600 обучений. В браузере держите сетку небольшой: до десятка сочетаний, лес — не больше 50 деревьев.
:::

{{practice: p-grid, grid-lr}}

## Разберём вместе: сколько стоит перебор

Прежде чем запускать перебор, полезно прикинуть, сколько раз будет обучаться модель, — в браузере каждое обучение конвейера занимает доли секунды, но они складываются.

1. Сетка из примера: 4 значения `C` × 2 варианта весов = **8 сочетаний**.
2. Каждое сочетание — 5 фолдов: 8 × 5 = **40 обучений**.
3. Плюс одно финальное обучение лучшего сочетания на всей обучающей части (`refit=True` по умолчанию): **41**.

Добавим третий гиперпараметр — стратегию заполнения пропусков из трёх вариантов: 4 × 2 × 3 = 24 сочетания, 24 × 5 + 1 = **121 обучение**, втрое больше. Четвёртый параметр с пятью значениями — уже 601. Сетка растёт как произведение, а не как сумма.

Случайный поиск (ниже) с `n_iter=20` и теми же 5 фолдами всегда стоит 20 × 5 + 1 = **101** обучение — сколько бы параметров и значений вы в него ни положили.

Что получилось: число обучений = сочетания × фолды + 1. Эту арифметику стоит делать до запуска, а не после того, как вкладка браузера зависла.

## Таблица результатов

Лучшее сочетание — ещё не вся правда. Полный отчёт лежит в `search.cv_results_` — словаре, который удобно превратить в таблицу:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

param_grid = {"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]}
search = GridSearchCV(pipe, param_grid, scoring="f1", cv=kf).fit(X_train, y_train)

res = pd.DataFrame(search.cv_results_)
cols = ["param_model__C", "param_model__class_weight", "mean_test_score", "std_test_score", "rank_test_score"]
res[cols].sort_values("rank_test_score").round(3)
```

- `param_…` — значения гиперпараметров (вариант без весов `None` таблица показывает как `NaN` — «пусто»);
- `mean_test_score` — среднее по фолдам, `std_test_score` — разброс между фолдами, как в главе 6;
- `rank_test_score` — место: 1 — лучшее;
- ещё там есть оценки по каждому фолду (`split0_test_score`…) и время обучения (`mean_fit_time`).

Таблица рассказывает больше, чем `best_params_`. Все четыре варианта с `"balanced"` дают F1 около 0.67 и отличаются в третьем-четвёртом знаке, а разброс между фолдами — около 0.03. Победитель среди них выбран случайностью фолдов: `C` здесь почти ни на что не влияет. Решает другое — веса классов: без них F1 на 5–11 п.п. ниже.

::: tip Как выбирать из почти равных
Если несколько сочетаний отличаются меньше, чем на `std_test_score`, считайте их равными и берите самое простое или привычное — например, `C=1` (значение по умолчанию). Гнаться за третьим знаком на CV — значит подгонять модель под конкретные фолды, как монетки в главе 6.
:::

::: quiz
В таблице `cv_results_` четыре сочетания с `"balanced"` отличаются по `mean_test_score` в третьем-четвёртом знаке, а `std_test_score` у них около 0.03. Как выбрать `C`?

- [x] Считать варианты равными и взять самый простой или привычный, например `C=1`
  > Разница меньше разброса между фолдами — это шум конкретного разбиения. Победитель среди равных выбран случайностью, а не качеством.
- [ ] Взять `best_params_`: на то он и лучший
  > «Лучший» здесь — на тысячные на тех же фолдах. С другим `random_state` фолдов победить мог бы другой `C`.
- [ ] Проверить все четыре на тесте и выбрать лучший
  > Тогда тест станет частью выбора, и итоговая цифра на нём окажется завышенной.
- [ ] Сузить сетку вокруг победителя и перебирать, пока разница не станет заметной
  > Более мелкая сетка лишь найдёт новые «победы» в пределах шума: `C` здесь почти ни на что не влияет.
:::

{{practice: cv-table}}

## Метрика выбора решает

`scoring` — не формальность: от него зависит, какое сочетание победит. Переберём ту же сетку по ROC-AUC:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

param_grid = {"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]}
search = GridSearchCV(pipe, param_grid, scoring="roc_auc", cv=kf).fit(X_train, y_train)

res = pd.DataFrame(search.cv_results_)
print(res["mean_test_score"].round(3).min(), "…", res["mean_test_score"].round(3).max())
print(search.best_params_)
```

По AUC все восемь сочетаний почти одинаковы — около 0.88. Это подтверждает урок «Дисбаланс классов»: веса классов сдвигают вероятности и меняют ответы при пороге 0.5 (поэтому F1 растёт), но почти не меняют **порядок** гостей по риску — а AUC оценивает именно порядок.

Отсюда правило: выбирайте `scoring` под то, как модель будут использовать.

- Решение «да / нет» при пороге 0.5 — `"f1"` (или `"precision"`, `"recall"`, если одна ошибка дороже);
- список «самые рискованные гости первыми», порог выберем потом по деньгам (урок «Порог, PR- и ROC-кривые») — `"roc_auc"`.

::: deep
`scoring` можно передать и своей функцией вида `f(модель, X, y) → число`: GridSearchCV вызовет её на каждом проверочном фолде. Так считают метрики, которых нет в sklearn, — например, прибыль от акции или долю ушедших среди 30 % самых рискованных гостей.
:::

::: quiz
Сетка `C`: `[0.01, 0.1, 1, 10]`. `GridSearchCV` выбрал `C=10` — крайнее значение. Тест ещё не открывали. Что делать?

- [x] Расширить сетку вправо (`[1, 10, 100, 1000]`) и повторить перебор на тех же фолдах: оптимум может лежать за краем
  > Победа крайнего значения значит лишь «больше — лучше в пределах сетки». Пока тест не открыт, сетку можно менять сколько угодно — это всё ещё выбор по валидации.
- [ ] Принять `C=10` и проверить на тесте
  > Можно, но тогда вы не знаете, не лучше ли `C=100`. Сначала убедитесь, что оптимум внутри сетки.
- [ ] Расширить сетку и выбрать `C` по тесту
  > Выбор по тесту превращает тест в валидацию. Сетку расширяют, но выбирают по-прежнему кросс-валидацией.
- [ ] Взять среднее значение сетки — оно надёжнее
  > Среднее значение сетки ничем не лучше: выбор делают по оценкам, а не по положению в списке.
:::

{{practice: top30, prep-params}}

## Случайный поиск

Когда гиперпараметров много, полная сетка не помещается ни в браузер, ни в рабочий день. **RandomizedSearchCV** — «случайный поиск» — берёт те же списки значений, но проверяет только `n_iter` случайных сочетаний. Опыт показывает, что обычно это почти не хуже полного перебора: важны, как правило, один-два гиперпараметра, а случайные сочетания перебирают их значения разнообразнее.

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

forest = Pipeline([("prep", pre), ("model", RandomForestClassifier(n_estimators=50, random_state=0))])
dist = {
    "model__max_depth": [3, 5, 8, None],
    "model__min_samples_leaf": [1, 5, 10],
    "model__class_weight": [None, "balanced"],
}
rs = RandomizedSearchCV(forest, dist, n_iter=4, scoring="f1", cv=kf, random_state=0)
rs.fit(X_train, y_train)

res = pd.DataFrame(rs.cv_results_)
print(res[["params", "mean_test_score"]].round(3).to_string())
print("лучшее:", rs.best_params_)
```

Из 4 × 3 × 2 = 24 сочетаний проверено 4 — в шесть раз меньше обучений. `random_state` делает выбор сочетаний воспроизводимым. Столбец `params` хранит сочетание целиком — словарём.

::: figure random-grid
Все 24 сочетания сетки леса; синим — четыре, которые выбрал `RandomizedSearchCV` с `random_state=0`. Остальные просто не проверялись — и лучшее из них могло оказаться среди пропущенных.
:::

Масштабирование числовых признаков лесу не нужно (урок «Масштабирование и ближайшие соседи»), но и не мешает, поэтому мы взяли тот же `pre`. Лучший из проверенных лесов — с весами классов — даёт F1 около 0.68–0.69 (в разных версиях sklearn лес получается чуть разным: 0.688 в браузере, 0.681 в sklearn 1.9), логистическая регрессия с весами — 0.67. Разница меньше разброса между фолдами (около 0.03), так что на этих данных простая модель почти не уступает сложной.

{{practice: random-forest}}

## Финал: тест один раз и сохранение

Подбор закончен — теперь, и только теперь, открываем тест. Если после этого вернуться и «чуть подправить сетку», тест станет ещё одной валидацией (глава 6, урок «Честное сравнение моделей»).

::: figure final-flow
Финальная цепочка: перебор только на обучающей части, лучший конвейер переобучается на всём train, тест — один раз для отчёта, потом сохранение. Возврат к сетке после взгляда на тест делает тест валидацией.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

param_grid = {"model__C": [0.1, 1], "model__class_weight": [None, "balanced"]}
search = GridSearchCV(pipe, param_grid, scoring="f1", cv=kf).fit(X_train, y_train)
final = search.best_estimator_

print("CV F1:", round(search.best_score_, 3))
print("тест F1:", round(f1_score(y_test, final.predict(X_test)), 3))
print("тест AUC:", round(roc_auc_score(y_test, final.predict_proba(X_test)[:, 1]), 3))
```

F1 на тесте — около 0.70, рядом с оценкой кросс-валидации (0.67): модель не переобучена под фолды, и цифре можно верить. Небольшая разница в любую сторону — обычный шум 600 тестовых гостей.

Обученный конвейер — это объект Python, и его можно сохранить в файл, чтобы завтра не обучать заново. Для этого есть библиотека **joblib** (она ставится вместе с sklearn):

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
import joblib

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

pipe.set_params(model__class_weight="balanced").fit(X_train, y_train)
joblib.dump(pipe, "churn_model.joblib")

model = joblib.load("churn_model.joblib")
print(type(model).__name__, list(model.named_steps))
print((model.predict(X_test) == pipe.predict(X_test)).all())
```

`joblib.dump(объект, файл)` записывает конвейер целиком — и подготовку, и модель со всем, что они выучили. `joblib.load(файл)` возвращает его обратно: можно сразу вызывать `predict_proba` для сырой выгрузки новых гостей, как в прошлом уроке.

::: tip Куда класть модели
В своём Jupyter сохраняйте модели в отдельную папку, а не рядом с данными: `joblib.dump(pipe, "models/churn_model.joblib")` (папку `models` создайте заранее). В курсе файл живёт в браузере, поэтому в примерах путь короткий.
:::

::: warn
Загружайте модель той же версией sklearn, которой её сохраняли: между версиями внутреннее устройство объектов меняется, и старый файл может не загрузиться или работать иначе. И открывайте только свои файлы `.joblib` — загрузка чужого файла может выполнить произвольный код.
:::

::: sql
Сохранённый конвейер похож на представление (`VIEW`) с зафиксированной логикой: один раз описали, как из сырых таблиц получить ответ, и дальше просто обращаетесь к нему, не повторяя шаги.
:::

::: warn Типичные ошибки
- **Перебор на всех данных.** `search.fit(X, y)` вместе с тестом — и тест уже не «новые гости». Перебор — только на train.
- **`best_score_` в отчёт.** Это лучший из многих вариантов на тех же фолдах — оценка оптимистичная. В отчёт идёт тест, посчитанный один раз.
- **Имя параметра без шага.** `"C"` вместо `"model__C"` — ошибка `Invalid parameter`.
- **Граница сетки.** Если лучшее значение — крайнее в сетке (`C=10` из `[0.01, …, 10]`), расширьте сетку: оптимум может быть дальше.
- **Метрика выбрана по привычке.** `scoring` — это и есть бизнес-цель; F1, AUC и деньги могут выбрать разные модели.
:::

{{practice: final-test, save-load}}

## Практика

## task: grid-keys | Сетка для конвейера | warmup

Конвейер `pipe` (шаги `"prep"` и `"model"` — логистическая регрессия) уже готов. Составьте сетку `param_grid`: параметр `C` модели — значения `0.1, 1, 10`, веса классов `class_weight` — `None` и `"balanced"`.

В `n_fits` сохраните, сколько обучений сделает `GridSearchCV` с этой сеткой и `cv=kf` (5 фолдов) — без итогового обучения на всей обучающей части. Посчитайте через длины списков в сетке, а не вписывайте число руками.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
param_grid = {
    "C": [0.1, 1, 10],
}
n_fits = 0
```

### check
```python
_pg = need('param_grid', dict)
_p = pipe.get_params()
for _key in _pg:
    assert _key in _p, f'Ключа {_key!r} нет среди параметров конвейера. Имя параметра шага пишется как шаг__параметр, например model__C.'
assert set(_pg) == {'model__C', 'model__class_weight'}, f'Ключи сетки: {sorted(_pg)}, а нужны C и class_weight шага model.'
assert sorted(float(v) for v in _pg['model__C']) == [0.1, 1.0, 10.0], f'Значения C: {list(_pg["model__C"])}, а нужны 0.1, 1, 10.'
assert list(_pg['model__class_weight']) in ([None, 'balanced'], ['balanced', None]), f'Значения class_weight: {list(_pg["model__class_weight"])}, а нужны None и "balanced".'
assert need('n_fits') == 30, f'n_fits = {need("n_fits")}. Сочетаний 3 × 2, и каждое обучается на каждом из 5 фолдов.'
assert not has_literal(30), 'Посчитайте n_fits из сетки: len(param_grid["model__C"]) и т. д., а не числом 30.'
```

### hint
Ключи сетки: `"model__C"` и `"model__class_weight"`. Проверить имя можно так: `"model__C" in pipe.get_params()`.

### hint
`n_fits = len(param_grid["model__C"]) * len(param_grid["model__class_weight"]) * 5`.

### solution
```python
param_grid = {
    "model__C": [0.1, 1, 10],
    "model__class_weight": [None, "balanced"],
}
n_fits = len(param_grid["model__C"]) * len(param_grid["model__class_weight"]) * 5
print(n_fits)
```

## task: p-grid | Собери перебор | warmup

`pipe`, `kf`, `X_train`, `y_train` уже готовы. Соберите программу: сетка по весам классов, поиск по F1, обучение, вывод лучших настроек и лучшего среднего F1 (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### parsons
```python
from sklearn.model_selection import GridSearchCV
param_grid = {"model__class_weight": [None, "balanced"]}
search = GridSearchCV(pipe, param_grid, scoring="f1", cv=kf)
search.fit(X_train, y_train)
print(search.best_params_)
print(round(search.best_score_, 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.model_selection import GridSearchCV as _GS
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_pipe = _P([('prep', _pre), ('model', _LR(max_iter=2000))])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_s = _GS(_pipe, {'model__class_weight': [None, 'balanced']}, scoring='f1', cv=_k).fit(_Xtr, _ytr)
_w = [str(_s.best_params_), str(round(_s.best_score_, 3))]
assert _lines == _w, f'Программа вывела {_lines}, а ожидалось {_w}. Сначала сетка, потом поиск, обучение — до вывода результатов.'
```

### hint
Порядок: импорт → сетка → `GridSearchCV(...)` → `fit` → вывод `best_params_` и `best_score_`.

## task: save-load | Сохранить и загрузить | warmup

Конвейер `pipe` уже обучен на `X_train`. Сохраните его в файл `churn_model.joblib`, загрузите обратно в переменную `model2` и проверьте, что ответы не изменились:

- `same` — `True`, если `model2.predict(X_test)` совпадает с `pipe.predict(X_test)` во всех строках;
- `n_flag` — сколько гостей теста загруженная модель относит к уходящим (ответ 1).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
pipe.set_params(model__class_weight="balanced").fit(X_train, y_train)
```

### starter
```python
import joblib
model2 = pipe
```

### check
```python
import os as _os
from sklearn.pipeline import Pipeline as _Pl
assert _os.path.exists('churn_model.joblib'), 'Файла churn_model.joblib нет — сохраните конвейер через joblib.dump(pipe, "churn_model.joblib").'
_m = need('model2', _Pl)
assert _m is not pipe, 'model2 — это тот же самый объект pipe. Загрузите модель из файла: joblib.load("churn_model.joblib").'
_pr = pipe.predict(X_test)
assert need('same') is True or need('same') == True, f'same = {need("same")}: сравните предсказания двух моделей и проверьте .all().'
assert (_m.predict(X_test) == _pr).all(), 'Загруженная модель отвечает иначе, чем pipe. Сохраняйте обученный pipe.'
assert need('n_flag') == int(_pr.sum()), f'n_flag = {need("n_flag")}, а загруженная модель отмечает другое число гостей теста. Сложите ответы model2.predict(X_test).'
```

### hint
`joblib.dump(pipe, "churn_model.joblib")`, затем `model2 = joblib.load("churn_model.joblib")`.

### hint
`same = bool((model2.predict(X_test) == pipe.predict(X_test)).all())`, `n_flag = int(model2.predict(X_test).sum())`.

### solution
```python
import joblib
joblib.dump(pipe, "churn_model.joblib")
model2 = joblib.load("churn_model.joblib")
pred = model2.predict(X_test)
same = bool((pred == pipe.predict(X_test)).all())
n_flag = int(pred.sum())
print(same, n_flag)
```

### explain
С `class_weight="balanced"` модель отмечает около 170 гостей теста — больше, чем там реально ушедших (134): это плата за высокую полноту (урок «Дисбаланс классов»). Файл `churn_model.joblib` в курсе живёт в браузере и пропадёт с вкладкой; в своём Jupyter он останется в рабочей папке — это и есть цель: модель можно передать в работу или загрузить завтра без переобучения.

## task: grid-lr | Подбор для логистической регрессии | base

`pipe`, `kf`, `X_train`, `y_train` уже готовы. Переберите `GridSearchCV` по сетке: `C` — `0.01, 0.1, 1, 10`, `class_weight` — `None` и `"balanced"`; метрика — F1, фолды — `kf`. Сохраните:

- `search` — обученный поиск;
- `best_params` — лучшие настройки (`best_params_`);
- `best_f1` — их средний F1 (3 знака);
- `gain` — насколько лучший средний F1 выше, чем у настроек по умолчанию (`C=1`, без весов), 3 знака. Средний F1 настроек по умолчанию возьмите из `cv_results_`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.model_selection import GridSearchCV
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.model_selection import GridSearchCV as _GS
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_pipe = _P([('prep', _pre), ('model', _LR(max_iter=2000))])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_s = _GS(_pipe, {'model__C': [0.01, 0.1, 1, 10], 'model__class_weight': [None, 'balanced']}, scoring='f1', cv=_k).fit(_Xtr, _ytr)
_r = _pd.DataFrame(_s.cv_results_)
_d = float(_r.loc[(_r['param_model__C'] == 1) & _r['param_model__class_weight'].isna(), 'mean_test_score'].iloc[0])
_st = need('search')
assert hasattr(_st, 'best_params_'), 'search не обучен: вызовите search.fit(X_train, y_train).'
assert len(_st.cv_results_['params']) == 8, f'В поиске {len(_st.cv_results_["params"])} сочетаний, а в сетке должно быть 4 × 2 = 8.'
assert dict(need('best_params')) == _s.best_params_, f'best_params = {need("best_params")}, а ожидалось {_s.best_params_}. Проверьте scoring="f1" и cv=kf.'
assert close(need('best_f1'), round(_s.best_score_, 3), 0.0011), f'best_f1 = {need("best_f1")}, а ожидалось {round(_s.best_score_, 3)}. Это search.best_score_.'
_gw = round(_s.best_score_ - _d, 3)
assert close(need('gain'), _gw, 0.0021), f'gain = {need("gain")}, а ожидалось {_gw}. Найдите в cv_results_ строку с C=1 и class_weight=None — её mean_test_score.'
```

### hint
Сетка: `{"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]}`; поиск — `GridSearchCV(pipe, сетка, scoring="f1", cv=kf).fit(X_train, y_train)`.

### hint
Строка настроек по умолчанию: `res = pd.DataFrame(search.cv_results_)`, фильтр `(res["param_model__C"] == 1) & res["param_model__class_weight"].isna()` — вариант `None` в таблице хранится как пустое значение.

### hint
Можно и без фильтра: в `cv_results_["params"]` сочетания идут списком словарей. Номер нужного — `search.cv_results_["params"].index({"model__C": 1, "model__class_weight": None})`.

### solution
```python
import pandas as pd
from sklearn.model_selection import GridSearchCV
param_grid = {"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]}
search = GridSearchCV(pipe, param_grid, scoring="f1", cv=kf).fit(X_train, y_train)
best_params = search.best_params_
best_f1 = round(search.best_score_, 3)
res = pd.DataFrame(search.cv_results_)
default = res.loc[(res["param_model__C"] == 1) & res["param_model__class_weight"].isna(), "mean_test_score"].iloc[0]
gain = round(search.best_score_ - default, 3)
print(best_params, best_f1, gain)
```

### explain
Прирост около 5 п.п. F1 почти целиком дают веса классов, а не `C`. Перебор по сетке это показал, но вывод делаем по таблице, а не по одному `best_params_`.

## task: cv-table | Читаем таблицу перебора | base

Поиск `search` (сетка `C` × `class_weight`, метрика F1) уже обучен. Соберите из `search.cv_results_` таблицу `table` со столбцами `param_model__C`, `param_model__class_weight`, `mean_test_score`, `std_test_score`, отсортированную по `rank_test_score` (лучшее сочетание — первой строкой).

В `n_close` сохраните, у скольких сочетаний (включая лучшее) средний F1 не ниже, чем «F1 лучшего минус его `std_test_score`», — то есть сколько сочетаний неотличимы от лучшего в пределах разброса. В `cw_close` — множество (`set`) значений `class_weight` у этих сочетаний.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
search = GridSearchCV(pipe, {"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]},
                      scoring="f1", cv=kf).fit(X_train, y_train)
```

### starter
```python
import pandas as pd
res = pd.DataFrame(search.cv_results_)
```

### check
```python
import pandas as _pd
_r = _pd.DataFrame(search.cv_results_).sort_values('rank_test_score')
_cols = ['param_model__C', 'param_model__class_weight', 'mean_test_score', 'std_test_score']
_t = need('table', _pd.DataFrame)
assert list(_t.columns) == _cols, f'Столбцы table: {list(_t.columns)}, а нужны {_cols}.'
assert len(_t) == 8, f'В table {len(_t)} строк, а сочетаний 8.'
assert _t['mean_test_score'].round(6).tolist() == _r['mean_test_score'].round(6).tolist(), 'Порядок строк не тот: отсортируйте по rank_test_score — по возрастанию, первое место сверху.'
_b = _r.iloc[0]
_ok = _r[_r['mean_test_score'] >= _b['mean_test_score'] - _b['std_test_score']]
assert need('n_close') == len(_ok), f'n_close = {need("n_close")}, а ожидалось {len(_ok)}. Порог — mean_test_score лучшего минус его std_test_score; лучшее сочетание тоже считается.'
_cw = {None if (v is None or v != v) else v for v in _ok['param_model__class_weight']}
_g = {None if (v is None or v != v) else v for v in need('cw_close')}
assert _g == _cw, f'cw_close = {need("cw_close")}, а ожидалось {_cw}.'
```

### hint
`table = res.sort_values("rank_test_score")[[...четыре столбца...]]`. Сортировать нужно до выбора столбцов — или включить `rank_test_score` и потом убрать.

### hint
Лучшая строка — `table.iloc[0]`. Порог: `best["mean_test_score"] - best["std_test_score"]`, дальше — фильтр и `len`.

### hint
`set(close["param_model__class_weight"])` — множество значений.

### solution
```python
import pandas as pd
res = pd.DataFrame(search.cv_results_)
table = res.sort_values("rank_test_score")[["param_model__C", "param_model__class_weight", "mean_test_score", "std_test_score"]]
best = table.iloc[0]
close_rows = table[table["mean_test_score"] >= best["mean_test_score"] - best["std_test_score"]]
n_close = len(close_rows)
cw_close = set(close_rows["param_model__class_weight"])
print(table.round(3))
print(n_close, cw_close)
```

### explain
Все сочетания с `"balanced"` неотличимы от лучшего, все без весов — хуже. Вывод для отчёта: «веса классов важны, `C` — нет», а конкретное `C` можно оставить по умолчанию.

## task: final-test | Один раз на тесте | base

Поиск `search` (сетка `C` × `class_weight`, метрика F1) уже обучен на `X_train`. Пора проверить итог. Сохраните:

- `final` — конвейер с лучшими настройками, обученный на всей обучающей части (его готовит сам поиск);
- `test_f1` и `test_auc` — F1 и ROC-AUC `final` на тесте (3 знака);
- `cv_gap` — `test_f1` минус средний F1 лучшего сочетания на кросс-валидации, 3 знака.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
search = GridSearchCV(pipe, {"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]},
                      scoring="f1", cv=kf).fit(X_train, y_train)
```

### starter
```python
from sklearn.metrics import f1_score, roc_auc_score
final = pipe
```

### check
```python
from sklearn.metrics import f1_score as _f1, roc_auc_score as _auc
_fin = need('final')
assert _fin is search.best_estimator_, 'final — не тот объект. search — обёртка с результатами перебора; чистый лучший конвейер, переобученный на всей обучающей части, — search.best_estimator_. Его и сохраняют.'
_f = round(_f1(y_test, search.predict(X_test)), 3)
_a = round(_auc(y_test, search.predict_proba(X_test)[:, 1]), 3)
assert close(need('test_f1'), _f), f'test_f1 = {need("test_f1")}, а ожидалось {_f}. F1 — по ответам final.predict(X_test).'
assert close(need('test_auc'), _a), f'test_auc = {need("test_auc")}, а ожидалось {_a}. Для AUC нужны вероятности: final.predict_proba(X_test)[:, 1].'
_gap = round(_f - search.best_score_, 3)
assert close(need('cv_gap'), _gap, 0.0021), f'cv_gap = {need("cv_gap")}, а ожидалось {_gap}. Средний F1 лучшего сочетания на CV — search.best_score_.'
```

### hint
`final = search.best_estimator_`.

### hint
`test_f1 = round(f1_score(y_test, final.predict(X_test)), 3)`; `cv_gap = round(test_f1 - search.best_score_, 3)`.

### solution
```python
from sklearn.metrics import f1_score, roc_auc_score
final = search.best_estimator_
test_f1 = round(f1_score(y_test, final.predict(X_test)), 3)
test_auc = round(roc_auc_score(y_test, final.predict_proba(X_test)[:, 1]), 3)
cv_gap = round(test_f1 - search.best_score_, 3)
print(test_f1, test_auc, cv_gap)
```

### explain
Тест оказался чуть лучше кросс-валидации — так бывает: 600 гостей теста — это одно случайное разбиение, а разброс F1 между фолдами около 0.03. Главное, что тест не провалился относительно CV: модель не подогнана под фолды.

## task: prep-params | Настройка подготовки | plus

`pipe`, `kf`, `X_train`, `y_train` уже готовы. Перебирать можно не только параметры модели, но и параметры подготовки. Проверим гипотезу: может, пропуски в числовых столбцах лучше заполнять медианой, а не нулём?

Соберите сетку: стратегия заполнителя в числовой части подготовки — `"constant"` и `"median"`; `C` модели — `0.1` и `1`; `class_weight` — только `"balanced"`. Обучите `search` по F1 с `cv=kf` и сохраните:

- `imp_key` — имя параметра стратегии заполнителя (строка, как в сетке);
- `best_params` — лучшие настройки;
- `delta` — насколько лучший средний F1 со стратегией `"median"` выше лучшего среднего F1 со стратегией `"constant"` (может быть и отрицательным), 3 знака.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.model_selection import GridSearchCV
imp_key = "strategy"
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.model_selection import GridSearchCV as _GS
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_pipe = _P([('prep', _pre), ('model', _LR(max_iter=2000))])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_key = 'prep__num__simpleimputer__strategy'
assert need('imp_key') == _key, f'imp_key = {need("imp_key")!r} — такого параметра нет или это не стратегия заполнителя. Поищите в pipe.get_params() ключ, где есть "imputer" и "strategy".'
_s = _GS(_pipe, {_key: ['constant', 'median'], 'model__C': [0.1, 1], 'model__class_weight': ['balanced']}, scoring='f1', cv=_k).fit(_Xtr, _ytr)
_st = need('search')
assert hasattr(_st, 'best_params_'), 'search не обучен: вызовите search.fit(X_train, y_train).'
assert len(_st.cv_results_['params']) == 4, f'В поиске {len(_st.cv_results_["params"])} сочетаний, а должно быть 2 × 2 × 1 = 4.'
assert dict(need('best_params')) == _s.best_params_, f'best_params = {need("best_params")}, а ожидалось {_s.best_params_}.'
_r = _pd.DataFrame(_s.cv_results_)
_d = round(_r.loc[_r['param_' + _key] == 'median', 'mean_test_score'].max() - _r.loc[_r['param_' + _key] == 'constant', 'mean_test_score'].max(), 3)
assert close(need('delta'), _d, 0.0021), f'delta = {need("delta")}, а ожидалось {_d}. Возьмите максимум mean_test_score по строкам с "median" и вычтите максимум по строкам с "constant".'
```

### hint
Ключ найдётся так: `[k for k in pipe.get_params() if "imputer" in k]`. Путь идёт через `prep` → `num` → `simpleimputer`.

### hint
Значение по умолчанию `fill_value=0` при стратегии `"median"` просто не используется — менять его не нужно.

### hint
`res = pd.DataFrame(search.cv_results_)`; столбец со стратегией называется `"param_" + imp_key`.

### solution
```python
import pandas as pd
from sklearn.model_selection import GridSearchCV
imp_key = "prep__num__simpleimputer__strategy"
param_grid = {imp_key: ["constant", "median"], "model__C": [0.1, 1], "model__class_weight": ["balanced"]}
search = GridSearchCV(pipe, param_grid, scoring="f1", cv=kf).fit(X_train, y_train)
best_params = search.best_params_
res = pd.DataFrame(search.cv_results_)
col = "param_" + imp_key
delta = round(res.loc[res[col] == "median", "mean_test_score"].max()
              - res.loc[res[col] == "constant", "mean_test_score"].max(), 3)
print(best_params, delta)
```

### explain
Пропуски есть только в `avg_check`, и формально медиана выиграла — но меньше чем на 1 п.п., при разбросе между фолдами около 3 п.п. Это ничья. По смыслу честнее ноль: у гостя без визитов чека нет (проект главы 6). Перебор подсказывает, но решение остаётся за аналитиком.

## task: random-forest | Случайный поиск для леса | plus

`pre`, `kf`, `X_train`, `y_train` уже готовы. Соберите конвейер `forest`: шаг `"prep"` — `pre`, шаг `"model"` — `RandomForestClassifier(n_estimators=50, random_state=0)`. Запустите `RandomizedSearchCV` по F1 с `cv=kf`, `n_iter=5`, `random_state=0` и распределением:

- `max_depth` — `3, 5, 8, None`;
- `min_samples_leaf` — `1, 3, 5, 10`;
- `class_weight` — `None`, `"balanced"`.

Сохраните `rs` (обученный поиск), `best_params` и `best_f1` (3 знака). В `beats_lr` — `True`, если лес лучше логистической регрессии с весами классов: её средний CV-F1 уже лежит в `lr_f1`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
lr_f1 = round(cross_val_score(pipe.set_params(model__class_weight="balanced"), X_train, y_train, cv=kf, scoring="f1").mean(), 3)
```

### starter
```python
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.model_selection import RandomizedSearchCV as _RS, ParameterSampler as _PS, cross_val_score as _cvs
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_pipe = _P([('prep', _pre), ('model', _LR(max_iter=2000))])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_dist = {'model__max_depth': [3, 5, 8, None], 'model__min_samples_leaf': [1, 3, 5, 10], 'model__class_weight': [None, 'balanced']}
_rs = need('rs')
assert isinstance(_rs, _RS), 'rs должен быть RandomizedSearchCV.'
assert hasattr(_rs, 'best_params_'), 'rs не обучен: вызовите rs.fit(X_train, y_train).'
_m = _rs.estimator.named_steps.get('model') if hasattr(_rs.estimator, 'named_steps') else None
assert isinstance(_m, _RF) and _m.n_estimators == 50 and _m.random_state == 0, 'В конвейере forest шаг "model" — RandomForestClassifier(n_estimators=50, random_state=0).'
assert _rs.n_iter == 5 and _rs.random_state == 0, f'Нужны n_iter=5 и random_state=0, а у вас n_iter={_rs.n_iter}, random_state={_rs.random_state}.'
assert _rs.scoring == 'f1', f'Метрика поиска — {_rs.scoring!r}, а нужна "f1".'
_want = list(_PS(_dist, n_iter=5, random_state=0))
assert [dict(p) for p in _rs.cv_results_['params']] == _want, 'Проверены не те сочетания. Проверьте списки значений в распределении (порядок как в условии), n_iter=5 и random_state=0.'
_bp = _rs.best_params_
_fr = _P([('prep', _pre), ('model', _RF(n_estimators=50, random_state=0))]).set_params(**_bp)
_bf = _cvs(_fr, _Xtr, _ytr, cv=_k, scoring='f1').mean()
assert close(_rs.best_score_, _bf, 1e-6), 'Оценка лучшего сочетания не совпала с проверочной. Фолды — cv=kf, обучение — на X_train, y_train.'
assert dict(need('best_params')) == _bp, f'best_params = {need("best_params")}, а лучшее сочетание поиска — {_bp}.'
assert close(need('best_f1'), round(_bf, 3), 0.0011), f'best_f1 = {need("best_f1")}, а ожидалось {round(_bf, 3)}.'
assert need('beats_lr') == (round(_bf, 3) > lr_f1), f'beats_lr = {need("beats_lr")}: сравните best_f1 с lr_f1 = {lr_f1}.'
```

### hint
`forest = Pipeline([("prep", pre), ("model", RandomForestClassifier(n_estimators=50, random_state=0))])`. Ключи распределения — с приставкой `model__`.

### hint
`rs = RandomizedSearchCV(forest, dist, n_iter=5, scoring="f1", cv=kf, random_state=0).fit(X_train, y_train)`.

### solution
```python
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
forest = Pipeline([("prep", pre), ("model", RandomForestClassifier(n_estimators=50, random_state=0))])
dist = {
    "model__max_depth": [3, 5, 8, None],
    "model__min_samples_leaf": [1, 3, 5, 10],
    "model__class_weight": [None, "balanced"],
}
rs = RandomizedSearchCV(forest, dist, n_iter=5, scoring="f1", cv=kf, random_state=0).fit(X_train, y_train)
best_params = rs.best_params_
best_f1 = round(rs.best_score_, 3)
beats_lr = best_f1 > lr_f1
print(best_params, best_f1, lr_f1, beats_lr)
```

### explain
Лучший лес — с весами классов и ограниченной глубиной — по F1 формально чуть выше логистической регрессии с весами, но разница в тысячных. Разница меньше разброса между фолдами, а логистическая регрессия проще, быстрее и её коэффициенты можно объяснить отделу лояльности.

## task: top30 | Своя метрика: топ-30 % | star

Отдел лояльности может дать акцию удержания только 30 % гостей — самым рискованным по модели. Важно одно: какую долю всех уходящих гостей поймают эти 30 %. Сделайте эту долю метрикой подбора.

Напишите функцию `top30_recall(model, X, y)`:

1. вероятности ухода `p = model.predict_proba(X)[:, 1]`;
2. `k = int(len(p) * 0.3)` гостей с наибольшими `p`;
3. вернуть, какая доля всех ушедших (`y == 1`) попала в эти `k`.

Передайте функцию в `GridSearchCV` как `scoring=top30_recall` (без кавычек и скобок) и переберите `C` — `0.01, 0.1, 1` и `class_weight` — `None`, `"balanced"` с `cv=kf`. Сохраните `search`, `best_params` и `best_top30` (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
import numpy as np
from sklearn.model_selection import GridSearchCV

def top30_recall(model, X, y):
    return 0
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.model_selection import GridSearchCV as _GS
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_pipe = _P([('prep', _pre), ('model', _LR(max_iter=2000))])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
def _t30(model, X, y):
    _p = model.predict_proba(X)[:, 1]
    _kk = int(len(_p) * 0.3)
    _y = _np.asarray(y)
    return _y[_np.argsort(-_p, kind='stable')[:_kk]].sum() / _y.sum()
_fn = need('top30_recall')
_m = _P([('prep', _pre), ('model', _LR(max_iter=2000))]).fit(_Xtr, _ytr)
_v, _w = float(_fn(_m, _Xte, _yte)), float(_t30(_m, _Xte, _yte))
assert close(_v, _w, 0.0001), f'На тесте ваша функция дала {_v:.4f}, а ожидалось {_w:.4f}. Возьмите k = int(len(p) * 0.3) гостей с наибольшими p и поделите число ушедших среди них на число всех ушедших.'
_s = _GS(_pipe, {'model__C': [0.01, 0.1, 1], 'model__class_weight': [None, 'balanced']}, scoring=_t30, cv=_k).fit(_Xtr, _ytr)
_st = need('search')
assert hasattr(_st, 'best_params_'), 'search не обучен: вызовите search.fit(X_train, y_train).'
assert len(_st.cv_results_['params']) == 6, f'В поиске {len(_st.cv_results_["params"])} сочетаний, а нужно 3 × 2 = 6.'
assert close(_st.best_score_, _s.best_score_, 0.0005), f'Лучшая оценка поиска {_st.best_score_:.4f}, а ожидалось {_s.best_score_:.4f}. Передайте функцию в scoring=top30_recall и используйте cv=kf.'
assert dict(need('best_params')) == _s.best_params_, f'best_params = {need("best_params")}, а ожидалось {_s.best_params_}.'
assert close(need('best_top30'), round(_s.best_score_, 3), 0.0011), f'best_top30 = {need("best_top30")}, а ожидалось {round(_s.best_score_, 3)}.'
```

### hint
Номера `k` самых рискованных: `np.argsort(-p)[:k]` — `argsort` выдаёт номера элементов по возрастанию (как в задаче «Соседи руками» урока «Масштабирование и ближайшие соседи»), а минус перед `p` разворачивает порядок. `y` может прийти как Series — переведите в массив: `y = np.asarray(y)`.

### hint
Доля пойманных: `y[top].sum() / y.sum()`.

### hint
GridSearchCV сам вызывает `top30_recall(модель_фолда, X_фолда, y_фолда)` на каждом проверочном фолде — вызывать функцию самим не нужно.

### solution
```python
import numpy as np
from sklearn.model_selection import GridSearchCV

def top30_recall(model, X, y):
    p = model.predict_proba(X)[:, 1]
    k = int(len(p) * 0.3)
    y = np.asarray(y)
    top = np.argsort(-p)[:k]
    return y[top].sum() / y.sum()

param_grid = {"model__C": [0.01, 0.1, 1], "model__class_weight": [None, "balanced"]}
search = GridSearchCV(pipe, param_grid, scoring=top30_recall, cv=kf).fit(X_train, y_train)
best_params = search.best_params_
best_top30 = round(search.best_score_, 3)
print(best_params, best_top30)
```

### explain
Акция для 30 % гостей ловит около трёх четвертей всех уходящих — против 30 % при случайном выборе. Как и AUC, эта метрика смотрит на порядок гостей, а не на порог, поэтому все сочетания почти равны: веса классов и `C` порядок почти не меняют. Заметьте: победил крайний `C=0.01` (0.767). По правилу «Граница сетки» сетку стоило бы расширить влево. Но `C=0.1` с весами отстаёт лишь в четвёртом знаке (0.7669 против 0.7671) при разбросе по фолдам около 0.03, так что продолжать перебор ради такой разницы смысла нет.
