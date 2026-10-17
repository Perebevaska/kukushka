---
title: "CatBoost и LightGBM в своём Jupyter"
lead: "В работе бустинг чаще берут из специализированных библиотек — CatBoost и LightGBM. Внутри у них тот же бустинг, что мы собирали руками, а снаружи — интерфейс как у sklearn. Запускаем обе библиотеки в своём Jupyter на данных проекта о выручке кофеен и сравниваем модели таблицей «качество и время»."
files: [deliveries.csv]
recap:
  - "CatBoost, LightGBM и XGBoost — тот же градиентный бустинг, интерфейс как у sklearn (`fit`, `predict`). В браузере их нет, работают в своём Jupyter; шпаргалка по параметрам — таблица в начале урока."
  - "Для ранней остановки нужна отдельная валидация — последний период обучающих данных, не тест: три части `fit`, `val`, `test`."
  - "Модели сравнивают одной таблицей «модель | RMSE | деревьев | fit, с | predict, мс»; время меряют `time.perf_counter()` вплотную вокруг `fit` и `predict`, в одном запуске на одном компьютере."
  - "Признаки и честная проверка дают больше, чем выбор библиотеки: разница между библиотеками на данных проекта — около 1.3 тыс. ₽ RMSE, выигрыш бустинга у линейной модели — больше 7 тыс. ₽."
---

Этот урок — после проекта «Прогноз дневной выручки»: данные, функция `prep` и разбиение по времени (`fit` — до апреля 2025, `val` — апрель–июнь, `test` — второе полугодие) взяты оттуда.

## CatBoost и LightGBM на своём компьютере

В работе бустинг чаще берут не из sklearn, а из специализированных библиотек: **CatBoost** (Яндекс) и **LightGBM** (Microsoft). Ещё одна известная — **XGBoost**. Внутри у всех тот же `boost` из урока «Бустинг: каждое дерево исправляет ошибки предыдущих»: деревья по очереди исправляют ошибки, шаг обучения, ранняя остановка. Сверху — годы инженерной работы: быстрее на миллионах строк, лучше с категориями, больше настроек. Для «Зерна» это значит, что прогноз по тысячам товаров и сотням кофеен можно переобучать каждую ночь.

Урок устроен иначе, чем остальные: это чтение и блокнот для своего Jupyter, а в браузере — только одна задача на sklearn. Почему не в браузере: код урока проверен в обычном Python с LightGBM 4.7 и новее (параметры `eval_X`/`eval_y` появились в 4.7) и с CatBoost. Для Python в браузере (Pyodide) собрана только часть таких библиотек и других версий — например, LightGBM 4.6, где этих параметров нет, — а CatBoost там нет. Поэтому код ниже — для своего Jupyter, а целиком всё собрано в блокноте [ch10-catboost-lightgbm.ipynb](../notebooks/extra/ch10-catboost-lightgbm.ipynb). Установка в окружение курса из главы 2: `uv add catboost lightgbm` (или `pip install catboost lightgbm`).

::: tip Аналогия
`HistGradientBoosting` из sklearn — хорошая кофемашина для дома, а CatBoost и LightGBM — профессиональные машины для сети. Устроены они одинаково: вода, давление, помол. Но у профессиональных больше настроек, и они рассчитаны на поток. При этом «профессиональная» библиотека не всегда точнее на маленьких данных: на четырёх тысячах строк разница часто сводится к настройкам по умолчанию.
:::

| | CatBoost | LightGBM |
|---|---|---|
| сильная сторона | категории, хорошие настройки «из коробки» | скорость на больших таблицах |
| категории | строками, список имён в `cat_features=` | столбцы типа `category` |
| ранняя остановка | `eval_set=(X_val, y_val)`, `early_stopping_rounds=` | `eval_X=`, `eval_y=` и `callbacks=[lgb.early_stopping(...)]` |
| сложность дерева | `depth=` — глубина | `num_leaves=` — число листьев |
| случайность | `random_seed=` | `random_state=` |

### CatBoost

Данные — из проекта: выручка кофеен по дням. Признаки те же, что в функции `prep` (шаг 2 проекта), только кофейня и формат остаются строками, без `get_dummies`. Разбиение по времени, как в шаге 6: `fit` — до апреля 2025, `val` — апрель–июнь для ранней остановки, `test` — второе полугодие.

Сначала — как CatBoost превращает категорию в число, на игрушке. Упрощённо: каждая строка получает среднюю выручку **предыдущих** строк той же кофейни. Для первой строки кофейни предыдущих нет, и ставится заглушка, возьмём 50. Пять дней по порядку:

| день | кофейня | выручка | предыдущие строки этой кофейни | число для модели |
|---|---|---|---|---|
| 1 | A | 60 | нет | 50 (заглушка) |
| 2 | B | 40 | нет | 50 (заглушка) |
| 3 | A | 70 | 60 | 60 |
| 4 | A | 50 | 60, 70 | 65 |
| 5 | B | 44 | 40 | 40 |

Почему не среднее по всем строкам кофейни? Тогда в число для дня 3 вошла бы его же выручка 70, и модель училась бы на подсказке из ответа. На редкой категории с одной строкой такое «среднее» просто равно ответу, и модель переобучается. Это утечка, от которой CatBoost защищается порядком строк.

::: figure ordered-te
Таблица из игрушки: число для модели в каждой строке — среднее выручки только предыдущих строк той же кофейни. Для дня 4 это дни 1 и 3, а его собственная выручка в расчёт не входит.
:::

```python
import pandas as pd
toy = pd.DataFrame({"shop": ["A", "B", "A", "A", "B"], "revenue": [60, 40, 70, 50, 44]})
g = toy.groupby("shop")["revenue"]
prev_sum = g.cumsum() - toy["revenue"]           # сумма предыдущих строк той же кофейни
prev_cnt = g.cumcount()                          # сколько их было
toy["shop_code"] = (prev_sum / prev_cnt).fillna(50)    # 0 / 0 даёт NaN → заглушка
print(toy)
```

**Что здесь происходит:**

- `g.cumsum()` — накопленная сумма внутри каждой кофейни. Вычитаем текущую выручку, чтобы осталась сумма только предыдущих строк.
- `g.cumcount()` — номер строки внутри кофейни, начиная с 0. Это и есть число предыдущих строк.
- Для первой строки кофейни получается 0 / 0, то есть `NaN`, и `fillna(50)` ставит заглушку.

Настоящий CatBoost устроен сложнее: перемешивает строки несколько раз и смешивает среднее с общим уровнем. Но идея та же, и делать это руками не нужно: достаточно перечислить категории в `cat_features`.

```python static
from catboost import CatBoostRegressor

cb = CatBoostRegressor(iterations=3000, learning_rate=0.05, depth=6,
                       random_seed=0, verbose=0, early_stopping_rounds=100)
cb.fit(X[fit], y[fit],
       cat_features=["shop_id", "format"],     # категории строками, без get_dummies
       eval_set=(X[val], y[val]),              # по ней выбирается число деревьев
       use_best_model=True)                    # оставить лучшее число деревьев
print(cb.get_best_iteration() + 1)             # сколько деревьев осталось
pred = cb.predict(X[test])
```

**Что здесь происходит:**

- `iterations=3000` — верхняя граница числа деревьев. Реально их будет меньше: остановит ранняя остановка.
- `cat_features` — имена столбцов-категорий. CatBoost заменяет категорию средним ответом по ней, посчитанным только по «предыдущим» строкам. Так ответ строки не подсказывает сам себе, и модель меньше переобучается на редких категориях.
- `early_stopping_rounds=100` — если 100 деревьев подряд не улучшили ошибку на `eval_set`, обучение останавливается. `use_best_model=True` обрезает модель до лучшего числа деревьев.
- `verbose=0` — без отчёта на каждом дереве (по умолчанию CatBoost печатает много).

### LightGBM

```python static
import lightgbm as lgb

X_c = X.astype({"shop_id": "category", "format": "category"})   # категории — тип category
lg = lgb.LGBMRegressor(n_estimators=3000, learning_rate=0.05, num_leaves=7, min_child_samples=10,
                       random_state=0, verbose=-1)
lg.fit(X_c[fit], y[fit], eval_X=X_c[val], eval_y=y[val],
       callbacks=[lgb.early_stopping(100, verbose=False)])
print(lg.best_iteration_)
pred = lg.predict(X_c[test])                   # прогноз — по лучшему числу деревьев
```

**Что здесь происходит:**

- `astype({...: "category"})` — LightGBM сам находит категории по типу столбца, как HGB с `categorical_features="from_dtype"`.
- `num_leaves=7`, `min_child_samples=10` — LightGBM растит дерево не уровень за уровнем, а «по листьям»: каждый раз делит самый выгодный лист. Поэтому сложность задаёт число листьев, а не глубина. По умолчанию 31 лист и не меньше 20 строк в листе — это настройки для больших таблиц.

- `eval_X`, `eval_y` — валидация (так с версии 4.7; в старых версиях `eval_set=[(X_val, y_val)]`). `lgb.early_stopping(100)` — та же ранняя остановка.

::: figure leafwise
Условная схема: два дерева по 4 листа. Слева рост по уровням, как у `GradientBoosting` и CatBoost. Справа рост по листьям, как у LightGBM: дерево однобокое, а его сложность задаёт `num_leaves`.
:::

### Сравнение: качество и время

Время обучения и прогноза меряют тем же секундомером, что в главе 9: `t0 = time.perf_counter()` до `fit` и `time.perf_counter() - t0` после. Прогноз быстрый, поэтому его повторяют несколько раз и берут лучшее время. В блокноте так собрана таблица по всем моделям. Вот она с нашего компьютера (секунды у вас будут другими, качество — тем же с точностью до версий библиотек):

| модель | RMSE, тыс. ₽ | деревьев | fit, с | predict, мс |
|---|---|---|---|---|
| CatBoost | 6.55 | 706 | 3.64 | 3.6 |
| LightGBM, 7 листьев | 6.98 | 702 | 0.23 | 32.4 |
| HGB, категории | 7.27 | 191 | 0.49 | 15.6 |
| HGB, get_dummies | 7.35 | 163 | 0.35 | 8.8 |
| LightGBM | 7.88 | 137 | 0.13 | 7.7 |

**Как читать результат.**

- **Главное: признаки и честная проверка важнее выбора библиотеки.** Между лучшей и худшей моделью в таблице 1.3 тыс. ₽ RMSE (6.55 против 7.88). А в проекте бустинг выиграл у линейной модели больше 7 тыс. ₽ — за счёт того, что сам нашёл взаимодействия признаков.
- **Качество.** Лучший — CatBoost. LightGBM с настройками по умолчанию — худший, а с мелкими деревьями (7 листьев) поднимается на второе место. На маленьких данных сравнение «из коробки» — во многом сравнение настроек по умолчанию.
- **Тренд.** Ловушка шага 7 проекта никуда не делась: HGB и LightGBM занижают прогноз второго полугодия на 1.75–3.49 тыс. ₽ в день. CatBoost на этом периоде почти не смещён (0.12), но рассчитывать на это нельзя — тренд лучше снимать явно.
- **Время.** На четырёх тысячах строк все модели обучаются за секунды, и время ничего не решает. В таблице быстрее всех обучился LightGBM с настройками по умолчанию (0.13 с), но при повторном запуске у нас первой оказалась строка «LightGBM, 7 листьев» (0.12 с), а LightGBM по умолчанию и оба HGB — около 0.3 с: на долях секунды порядок меняется от запуска к запуску. Устойчиво одно: дольше всех обучается CatBoost, у него около 700 деревьев глубины 6. Зато прогноз у CatBoost самый быстрый: его деревья симметричные, на каждом уровне одно и то же условие, и такое дерево применяется к строке очень быстро.

::: quiz
Для ранней остановки CatBoost нужен `eval_set`. Какие данные туда передать в прогнозе выручки по дням?

- [x] Последний период обучающих данных (апрель–июнь), который не входит в `fit`
  > Валидация повторяет будущее относительно обучения, а тест остаётся нетронутым до финальной оценки.
- [ ] Тест (второе полугодие): так модель остановится там, где лучше всего на нём
  > Тогда число деревьев подобрано по тесту, и оценка на нём получится оптимистичной. Тест смотрят один раз, в самом конце.
- [ ] Те же данные, что в `fit`
  > На обучающих данных ошибка падает всегда, и ранняя остановка не сработает: деревья будут добавляться до `iterations`.
- [ ] Случайные 20 % всех строк
  > Для данных во времени случайная валидация подглядывает в будущее: соседние дни попадают и в обучение, и в валидацию.
:::

::: warn Типичные ошибки
- **Тест вместо валидации в `eval_set`.** Симптом — подозрительно хорошее качество на тесте, которое не повторяется на новых данных. Нужно три части: `fit`, `val`, `test`.
- **Забыли `cat_features` у CatBoost.** Ошибка `CatBoostError: Bad value for num_feature[...]="KZN-1": Cannot convert 'KZN-1' to float`: CatBoost пытается прочитать название кофейни как число. Перечислите столбцы-категории в `cat_features`.
- **Строки вместо `category` в LightGBM.** Ошибка `ValueError: pandas dtypes must be int, float or bool. Fields with bad pandas dtypes: shop_id: str, format: str`. Переведите столбцы через `.astype("category")`.
- **Сравнили время с разных запусков.** Время зависит от компьютера, числа потоков и того, что ещё запущено: при повторных запусках на нашем компьютере секунды менялись в полтора-два раза, и устойчивыми оставались только крайние места. Сравнивайте модели в одном блокноте, подряд, на одном компьютере.
:::

{{practice: speed-table}}

## Практика

## task: speed-table | Таблица «качество и время» | base

Соберите в браузере такую же таблицу, как в блокноте с CatBoost и LightGBM, для трёх моделей sklearn на доставках. Модели и разбиение уже в заготовке. Для каждой модели замерьте `time.perf_counter()` время обучения в секундах (`fit_s`) и время прогноза на тесте в миллисекундах (`predict_ms`), посчитайте RMSE на тесте (`rmse`, 3 знака). Сохраните DataFrame `table`: индекс — названия моделей из словаря `models`, столбцы `rmse`, `fit_s`, `predict_ms`, строки отсортированы по `rmse` от лучшей. Ещё сохраните `best` — название модели с наименьшей ошибкой и `fastest_fit` — название модели, которая обучилась быстрее всех.

### starter
```python
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)

models = {
    "GradientBoosting": GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=200, max_depth=3, random_state=0),
    "RandomForest": RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=0),
}

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import GradientBoostingRegressor as _GB, HistGradientBoostingRegressor as _H, RandomForestRegressor as _RF
from sklearn.metrics import mean_squared_error as _mse
ref = {}
for k, m in {'GradientBoosting': _GB(n_estimators=200, max_depth=3, random_state=0), 'HistGradientBoosting': _H(max_iter=200, max_depth=3, random_state=0),
             'RandomForest': _RF(n_estimators=100, min_samples_leaf=5, random_state=0)}.items():
    ref[k] = round(float(_np.sqrt(_mse(y_te, m.fit(X_tr, y_tr).predict(X_te)))), 3)
t = need('table', _pd.DataFrame)
assert set(t.index) == set(ref), f'Индекс table — названия моделей {sorted(ref)}, а сейчас {list(t.index)}.'
assert {'rmse', 'fit_s', 'predict_ms'} <= set(t.columns), f'Нужны столбцы rmse, fit_s, predict_ms, а сейчас {list(t.columns)}.'
for k in ref:
    assert close(t.loc[k, 'rmse'], ref[k], 0.0011), f'{k}: rmse = {t.loc[k, "rmse"]}, а нужно {ref[k]}. RMSE — корень из mean_squared_error на тесте.'
assert (t['fit_s'] > 0).all() and (t['fit_s'] < 600).all(), f'fit_s = {t["fit_s"].tolist()}: время обучения в секундах — разность двух показаний perf_counter().'
assert (t['predict_ms'] > 0).all(), 'predict_ms должно быть положительным.'
assert t['predict_ms'].max() > 1, f'predict_ms = {t["predict_ms"].round(4).tolist()}: похоже на секунды. Время прогноза в миллисекундах — разность perf_counter(), умноженная на 1000.'
assert list(t.index) == list(t.sort_values('rmse').index), 'Строки table должны идти по возрастанию rmse: .sort_values("rmse").'
assert need('best') == t['rmse'].idxmin(), f'best = {need("best")!r}, а меньше всего ошибка у {t["rmse"].idxmin()!r}.'
assert need('fastest_fit') == t['fit_s'].idxmin(), f'fastest_fit = {need("fastest_fit")!r}, а по вашей же таблице быстрее всех обучилась {t["fit_s"].idxmin()!r}.'
```

### hint
В цикле по `models.items()` для каждой модели: засечь время, обучить, остановить секундомер; затем так же с прогнозом. Строки таблицы удобно копить словарями в списке.

### hint
`t0 = time.perf_counter(); model.fit(X_tr, y_tr); fit_s = time.perf_counter() - t0`. Для прогноза — то же, умноженное на 1000. RMSE — `np.sqrt(mean_squared_error(y_te, pred))`.

### hint
```python
rows = []
for name, model in models.items():
    ...
    rows.append({"model": name, "rmse": round(float(rmse), 3), "fit_s": fit_s, "predict_ms": predict_ms})
table = pd.DataFrame(rows).set_index("model").sort_values("rmse")
best = table.index[0]
fastest_fit = table["fit_s"].idxmin()
```

### solution
```python
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)

models = {
    "GradientBoosting": GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=200, max_depth=3, random_state=0),
    "RandomForest": RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=0),
}

rows = []
for name, model in models.items():
    t0 = time.perf_counter()
    model.fit(X_tr, y_tr)
    fit_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    pred = model.predict(X_te)
    predict_ms = (time.perf_counter() - t0) * 1000

    rmse = np.sqrt(mean_squared_error(y_te, pred))
    rows.append({"model": name, "rmse": round(float(rmse), 3), "fit_s": fit_s, "predict_ms": predict_ms})

table = pd.DataFrame(rows).set_index("model").sort_values("rmse")
best = table.index[0]
fastest_fit = table["fit_s"].idxmin()
print(table.round(3))
print("лучший:", best, "| быстрее всех обучился:", fastest_fit)
```

### explain
Лучшая ошибка у классического `GradientBoosting` (RMSE 4.907), чуть хуже `HistGradientBoosting` (5.053) с теми же 200 деревьями глубины 3, у леса — 5.811. Время — ваше собственное, поэтому проверка сравнивает `fastest_fit` с вашей же таблицей. В браузере у нас быстрее всех обучился `HistGradientBoosting`, но на 1400 строках разница — доли секунды (у нас 0.2 с против 0.4–0.5 с). Его преимущество растёт с размером данных: он ищет пороги только между 255 интервалами каждого признака, а не перебирает все значения. Если в таблицу попали секунды вместо миллисекунд для прогноза, числа будут вида 0.03 вместо 30 — это видно сразу, поэтому единицы измерения пишут прямо в названии столбца.
