---
title: "CatBoost и LightGBM в своём Jupyter"
lead: "В работе бустинг чаще берут из специализированных библиотек — CatBoost и LightGBM. Внутри у них тот же бустинг, что мы собирали руками, а снаружи — интерфейс как у sklearn. Запускаем обе библиотеки в своём Jupyter на данных проекта о выручке кофеен и сравниваем модели таблицей «качество и время»."
files: [deliveries.csv]
recap:
  - "CatBoost, LightGBM и XGBoost — тот же градиентный бустинг, интерфейс как у sklearn (`fit`, `predict`). В поставке браузера нет CatBoost; LightGBM есть в версии 4.6, а показанный API 4.7+ запускаем в своём Jupyter. Браузерная карточка использует sklearn; шпаргалка по параметрам — в начале урока."
  - "Для ранней остановки нужна отдельная валидация — последний период обучающих данных, не тест: три части `fit`, `val`, `test`."
  - "Модели сравнивают одной таблицей «модель | RMSE | деревьев | fit, с | predict, мс»; время меряют `time.perf_counter()` вплотную вокруг `fit` и `predict`, в одном запуске на одном компьютере."
  - "Сравнивайте библиотеки при одной дате выпуска и одной информации о погоде. Выигрыш в RMSE и затраты времени берите из одной таблицы собственного прогона."
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

cb_params = dict(learning_rate=0.05, depth=6, random_seed=0, verbose=0,
                 thread_count=1, allow_writing_files=False)
cats = ["shop_id", "format"]
probe = CatBoostRegressor(iterations=3000, early_stopping_rounds=100, **cb_params)
probe.fit(X_dev[fit], y[fit], cat_features=cats,
          eval_set=(X_dev[val], y[val]), use_best_model=True)
chosen = probe.get_best_iteration() + 1
cb = CatBoostRegressor(iterations=chosen, **cb_params)
refit = fit | val
cb.fit(X[refit], y[refit], cat_features=cats)   # вся история до июля
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

cat_types = {"shop_id": "category", "format": "category"}
dev_cat = X_dev.astype(cat_types)
X_c = X.astype(cat_types)
lg_params = dict(learning_rate=0.05, num_leaves=7, min_child_samples=10,
                 random_state=0, verbose=-1, n_jobs=1)
probe = lgb.LGBMRegressor(n_estimators=3000, **lg_params)
probe.fit(dev_cat[fit], y[fit], eval_X=dev_cat[val], eval_y=y[val],
          callbacks=[lgb.early_stopping(100, verbose=False)])
chosen = probe.best_iteration_
lg = lgb.LGBMRegressor(n_estimators=chosen, **lg_params)
refit = fit | val
lg.fit(X_c[refit], y[refit])                    # вся история до июля
pred = lg.predict(X_c[test])
```

**Что здесь происходит:**

- `astype({...: "category"})` — LightGBM сам находит категории по типу столбца, как HGB с `categorical_features="from_dtype"`.
- `num_leaves=7`, `min_child_samples=10` — LightGBM растит дерево не уровень за уровнем, а «по листьям»: каждый раз делит самый выгодный лист. Поэтому сложность задаёт число листьев, а не глубина. По умолчанию 31 лист и не меньше 20 строк в листе — это настройки для больших таблиц.

- `eval_X`, `eval_y` — валидация (так с версии 4.7; в старых версиях `eval_set=[(X_val, y_val)]`). `lgb.early_stopping(100)` — та же ранняя остановка.

::: figure leafwise
Условная схема: два дерева по 4 листа. Слева рост по уровням, как у `GradientBoosting` и CatBoost. Справа рост по листьям, как у LightGBM: дерево однобокое, а его сложность задаёт `num_leaves`.
:::

### Сравнение: качество и время

Пример прогона с scikit-learn 1.8.0, CatBoost 1.2.10 и LightGBM 4.7.0. При подготовке апрельского и июльского выпусков для будущей погоды использованы средние из доступной на тот момент истории. После ранней остановки модель обучена с выбранным числом деревьев на всех данных до июля. Три колонки времени измерены на одном компьютере при одинаковом числе потоков.

| Модель | RMSE, тыс. ₽ | Деревья | Подбор и финальный fit, с | Только финальный fit, с | Пакетный predict, мс |
|---|---:|---:|---:|---:|---:|
| CatBoost | 9.02 | 225 | 0.75 | 0.31 | 0.69 |
| HGB, категории | 9.12 | 56 | 0.63 | 0.04 | 2.19 |
| HGB, get_dummies | 9.13 | 67 | 0.77 | 0.06 | 1.39 |
| LightGBM | 12.65 | 120 | 0.08 | 0.02 | 2.42 |
| LightGBM, 7 листьев | 13.26 | 330 | 0.05 | 0.02 | 3.65 |

В этом полугодии ошибка CatBoost и обеих версий HGB близка. Уменьшение числа листьев LightGBM на этом наборе увеличило ошибку. Для планирования ночного запуска важна длительность подбора и повторного обучения, а для ежедневной выдачи — время прогноза на одинаковом пакете. Повторите замер в своём окружении.

::: quiz
Для ранней остановки CatBoost нужен `eval_set`. Какие данные туда передать в прогнозе выручки по дням?

- [x] Последний период обучающих данных (апрель–июнь), который не входит в `fit`
  > Валидация повторяет будущее относительно обучения, а тест остаётся нетронутым до финальной оценки.
- [ ] Тест (второе полугодие): так модель остановится там, где лучше всего на нём
  > Тогда число деревьев подобрано по тесту, и оценка на нём получится оптимистичной. Тест смотрят один раз, в самом конце.
- [ ] Те же данные, что в `fit`
  > Те же строки не проверяют перенос на другой период. Для ранней остановки нужна отдельная валидация, которая не входит в fit.
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

В локальном блокноте запишите фактические версии CatBoost/LightGBM, доступность каждой библиотеки и отдельно время подбора/ранней остановки и финального fit. Сравнивайте одинаковую операцию, горизонт и доступные признаки; отсутствие библиотеки отмечается как пропущенный запуск, а не как нулевая длительность.

## Практика

## task: speed-table | Таблица «качество и время» | base

Соберите в браузере такую же таблицу, как в блокноте с CatBoost и LightGBM, для трёх моделей sklearn на доставках. Модели и разбиение уже в заготовке. Для каждой модели вызовите `fit_s = timed_fit(name, model, X_tr, y_tr)`, затем `pred, predict_ms = timed_predict(name, model, X_te)`. Эти готовые функции сами вызывают fit/predict и измеряют интервал через `time.perf_counter()` непосредственно вокруг вызова: `fit_s` — секунды, `predict_ms` — миллисекунды. Сохраните возвращённые интервалы без округления; посчитайте RMSE на тесте (`rmse`, 3 знака). Сохраните DataFrame `table`: индекс — названия моделей из словаря `models`, столбцы `rmse`, `fit_s`, `predict_ms`, строки отсортированы по `rmse` от лучшей. Ещё сохраните `best` — название модели с наименьшей ошибкой и `fastest_fit` — название модели, которая обучилась быстрее всех.



Для замера используйте процедуры из заготовки. Допустима своя обёртка, если её fit и predict действительно вызывают соответствующие операции входящих в процедуру оценщиков. Обучение до секундомера с возвратом готовой модели внутри timed_fit не является замером обучения.

### setup
```python
from time import perf_counter as _measurement_clock
_measurements = {}
def _timed_estimator_call(method, operation):
    # Install and remove observers outside the measured interval. A delegating
    # wrapper may call any of the supplied estimators; returning a cache is not fit.
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                                  HistGradientBoostingRegressor)
    classes = (LinearRegression, RandomForestRegressor,
               GradientBoostingRegressor, HistGradientBoostingRegressor)
    originals = [(cls, getattr(cls, method), method in cls.__dict__) for cls in classes]
    calls = []
    def observe(original):
        def wrapped(estimator, *args, **kwargs):
            calls.append(estimator)
            return original(estimator, *args, **kwargs)
        return wrapped
    try:
        for cls, original, _owned in originals:
            setattr(cls, method, observe(original))
        start = _measurement_clock()
        result = operation()
        elapsed = _measurement_clock() - start
    finally:
        for cls, original, owned in originals:
            if owned:
                setattr(cls, method, original)
            else:
                delattr(cls, method)
    assert calls, ('Внутри timed_' + method + ' должен выполняться настоящий ' +
                   method + ' оценщика из процедуры. Возврат заранее готового ' +
                   'результата не измеряет эту операцию; обёртка должна делегировать вызов.')
    return result, elapsed

def timed_fit(name, model, features, target):
    """Обучить модель; вернуть длительность вызова fit в секундах."""
    _, elapsed = _timed_estimator_call('fit', lambda: model.fit(features, target))
    _measurements[name] = dict(model=model, train=features.copy(), target=target.copy(), fit_s=elapsed)
    return elapsed

def timed_predict(name, model, features):
    """Вернуть (пакетный прогноз, длительность predict в миллисекундах)."""
    prediction, elapsed = _timed_estimator_call('predict', lambda: model.predict(features))
    elapsed_ms = elapsed * 1000
    record = _measurements[name]
    assert record['model'] is model, 'Передайте в timed_predict ту же модель, что в timed_fit.'
    record.update(test=features.copy(), predict_ms=elapsed_ms)
    return prediction, elapsed_ms
```

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
assert t.index.is_unique, 'Названия моделей в table не должны повторяться.'
for _name in t.index:
    assert _name in _measurements, f'{_name}: вызовите timed_fit для финального обучения.'
    _record = _measurements[_name]
    assert 'predict_ms' in _record, f'{_name}: вызовите timed_predict после timed_fit.'
    assert _record['train'].equals(X_tr) and _record['target'].equals(y_tr), f'{_name}: timed_fit должен обучать на финальной тренировочной части.'
    assert _record['test'].equals(X_te), f'{_name}: timed_predict должен получать весь финальный тест.'
    for _col in ('fit_s', 'predict_ms'):
        assert _np.isfinite(t.loc[_name, _col]) and close(t.loc[_name, _col], _record[_col], 1e-9), f'{_name}: {_col} не совпало с фактическим интервалом. Запишите результат timed_fit/timed_predict без подмены и округления.'
assert list(t.index) == list(t.sort_values('rmse').index), 'Строки table должны идти по возрастанию rmse: .sort_values("rmse").'
assert need('best') == t['rmse'].idxmin(), f'best = {need("best")!r}, а меньше всего ошибка у {t["rmse"].idxmin()!r}.'
assert need('fastest_fit') == t['fit_s'].idxmin(), f'fastest_fit = {need("fastest_fit")!r}, а по вашей же таблице быстрее всех обучилась {t["fit_s"].idxmin()!r}.'
```

### hint
В цикле по `models.items()` вызовите `fit_s = timed_fit(name, model, X_tr, y_tr)` и `pred, predict_ms = timed_predict(name, model, X_te)`. Готовые функции сами вызывают модель и меряют время; сохраните их интервалы без округления. RMSE на доставках укажите в минутах. Строки удобно копить словарями в списке.

### hint
`fit_s = timed_fit(name, model, X_tr, y_tr)`, затем `pred, predict_ms = timed_predict(name, model, X_te)`. Единицы уже преобразованы внутри функций. RMSE — `np.sqrt(mean_squared_error(y_te, pred))`.

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
    fit_s = timed_fit(name, model, X_tr, y_tr)
    pred, predict_ms = timed_predict(name, model, X_te)

    rmse = np.sqrt(mean_squared_error(y_te, pred))
    rows.append({"model": name, "rmse": round(float(rmse), 3), "fit_s": fit_s, "predict_ms": predict_ms})

table = pd.DataFrame(rows).set_index("model").sort_values("rmse")
best = table.index[0]
fastest_fit = table["fit_s"].idxmin()
print(table.round(3))
print("лучший:", best, "| быстрее всех обучился:", fastest_fit)
```

### explain
Лучшая ошибка у классического `GradientBoosting` (RMSE 4.907), чуть хуже `HistGradientBoosting` (5.053) с теми же 200 деревьями глубины 3, у леса — 5.811. Время — ваше собственное: проверка связывает строки таблицы с интервалами, возвращёнными timed_fit/timed_predict, и сравнивает fastest_fit с минимумом этой таблицы. В браузере у нас быстрее всех обучился `HistGradientBoosting`, но на 1400 строках разница — доли секунды (у нас 0.2 с против 0.4–0.5 с). Его преимущество растёт с размером данных: он ищет пороги только между 255 интервалами каждого признака, а не перебирает все значения. Если в таблицу попали секунды вместо миллисекунд для прогноза, числа будут вида 0.03 вместо 30 — это видно сразу, поэтому единицы измерения пишут прямо в названии столбца.
