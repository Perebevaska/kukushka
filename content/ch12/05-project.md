---
title: "Проект: сколько бариста поставить на смену"
files: [app_orders.csv]
lead: "Финал главы. Заказы из приложения собирает отдельный бариста на выдаче, и график смен составляется накануне. Строим прогноз заказов на завтра по часам с требованием к точности, честно выбираем модель на валидации — и переводим прогноз в людей, где выясняется, что «точный в среднем» прогноз систематически оставляет смены без рук."
recap:
  - "Требование к модели формулируют заранее: метрика, порог и наивный прогноз, который нужно обогнать."
  - "Момент прогноза задаёт признаки: при решении в 20:00 последний известный час — 19:00, и для 23:00 завтра законны только лаги ≥ 28 — здесь лаги 48, 168 и среднее `s.shift(28).rolling(24)`."
  - "Три части по времени: обучение → валидация для выбора модели → тест один раз. Финальную модель переобучают на обучении + валидации."
  - "Параметры для ряда подбирают `GridSearchCV(..., cv=TimeSeriesSplit(n_splits=3))`: каждый фолд обучается на прошлом и проверяется на следующем куске. `cv=3` — обычный KFold, он оптимистичен и может выбрать не те параметры."
  - "Прогноз ряда используют для решения — здесь штатного расписания. Метрика решения (часы нехватки, лишние смены) важнее RMSE."
  - "Обычный прогноз нацелен на «середину»: в половине случаев факт выше. Если нехватка дороже избытка, планируют по верхнему квантилю."
  - "`HistGradientBoostingRegressor(loss='quantile', quantile=0.8)` прогнозирует значение, которое факт превышает лишь в ~20 % случаев."
---

## Задача

> График смен на выдаче заказов из приложения составляем накануне к 20:00 на весь следующий день. Сейчас ставим по среднему за этот час за 4 прошлые недели, и то бариста скучает, то очередь из курьеров.
>
> Нужна модель, которая прогнозирует число заказов на каждый час завтрашнего дня. Требование: RMSE на августе — не больше 4.3 заказа в час, и модель должна быть лучше нашего правила «среднее за этот час за 4 прошлые недели». Один бариста на выдаче успевает около 6 заказов в час; с 7 до 22 часов на выдаче всегда хотя бы один человек.
>
> *Операционный менеджер*

## План

0. Момент прогноза и горизонт: какие признаки законны при решении в 20:00 (раздел ниже).
1. Признаки для горизонта «завтра» (раздел «Разберём вместе» урока «Прогноз: ориентиры, горизонт и метрики») и признак акции (задача «Признак „день акции“» урока «Признаки для прогноза ряда»); разбиение по времени: обучение — март–июнь, валидация — июль, тест — август.
2. Ориентир: «среднее за 4 недели» на тесте и проверка требования.
3. Выбор модели на валидации.
   Затем — подбор параметров победителя кросс-валидацией по времени: `GridSearchCV` с `cv=TimeSeriesSplit(n_splits=3)` на марте–июле. Обычное `cv=3` здесь — ошибка: это KFold, который не знает о времени.
4. Финальная модель — с параметрами из шага 3б — на обучении + валидации, проверка на тесте.
5. Перевод прогноза в бариста: сколько часов будет нехватка и сколько лишних смен.
6. План по верхнему квантилю.

::: figure ts-project-split
Все разбиения проекта на одной шкале времени. Выбор модели — обучение до июля, проверка на июле; подбор параметров — три фолда `TimeSeriesSplit` внутри марта–июля; финал — обучение на марте–июле и один взгляд на август.
:::

## Момент прогноза и признаки

Прежде чем строить признаки, ответим на три вопроса из урока «Прогноз: ориентиры, горизонт и метрики».

1. **Когда принимается решение?** В 20:00 накануне. Последний полностью известный час — 19:00 сегодня.
2. **На какой период?** Весь завтрашний день по часам: от 00:00 до 23:00 завтра.
3. **Какой лаг законен для самого дальнего часа?** От 19:00 сегодня до 23:00 завтра — 28 часов. Лаг 24 для 23:00 завтра указывает на 23:00 сегодня, а в 20:00 этого часа ещё нет. Значит, для всех часов годятся только лаги от 28.

Отсюда признаки. Календарь и флаг акции известны заранее (даты акций — в календаре маркетинга). Из лагов берём 48 (тот же час позавчера) и 168 (тот же час неделю назад). Среднее за сутки сдвигаем на 28 часов: `s.shift(28).rolling(24).mean()` — окно заканчивается не позже 19:00 сегодня для любого часа завтра. `mean4w` строится из сдвигов от 168 часов — он законен. Лаг 24 подошёл бы утренним часам завтра, но ради одной модели на все часы мы от него отказываемся.

Цена честности здесь почти нулевая: финальная модель проекта (шаг 4) с лагом 24 и сдвигом окна 24, то есть с отсечкой в полночь, дала бы на августе те же 4.21 (4.208 против 4.209). Зато наша модель действительно запустится в 20:00: каждый её признак к этому времени уже известен.

Функция признаков `make(s)` с этими признаками дана в заготовках: календарь, флаг акции, лаги 48 и 168, среднее за сутки со сдвигом 28 и `mean4w` — среднее за этот час в 4 прошлые недели.

## От прогноза к людям: зачем квантиль (шаги 5–6)

Шаги 1–4 отвечают на вопрос «сколько заказов будет». Менеджеру нужен другой ответ — «сколько человек поставить». В шаге 5 прогноз переводят в бариста: `max(1, ceil(заказы / 6))`. Обычная модель прогнозирует «середину»: примерно в половине часов факт выше прогноза, и в части таких часов рук не хватит.

Если нехватка дороже лишнего человека, план строят не по середине, а по **квантилю** (глава 4: квантиль 0.8 — значение, ниже которого 80 % данных). Пример: в 10 прошлых пятниц в 18:00 было 12, 14, 15, 15, 16, 17, 18, 19, 21 и 24 заказа. Среднее — 17.1, по нему нужно 3 бариста (17.1 / 6 ≈ 2.85, вверх — 3), и в трёх пятницах из десяти (19, 21, 24 заказа) рук бы не хватило. Квантиль 0.8 — 19.4 (`np.quantile(x, 0.8)`), по нему 4 бариста, и их хватило бы во все десять пятниц. Цена — лишний человек в обычные пятницы.

Модель умеет прогнозировать квантиль напрямую: `HistGradientBoostingRegressor(loss="quantile", quantile=0.8)` учится выдавать значение, которое факт превышает лишь примерно в 20 % случаев. Это шаг 6 — после того как в шаге 5 вы увидите, как часто «середина» оставляет смены без рук.

::: quiz
Прогноз заказов переводят в число бариста. Почему план строят по квантилю 0.8, а не по среднему прогнозу?

- [x] Нехватка бариста в час пик стоит дороже лишнего человека: с запасом ошибаемся реже в опасную сторону
  > Квантиль — ответ на вопрос «сколько нужно, чтобы в 80 % часов хватило людей». Цена — лишние часы работы.
- [ ] Квантиль точнее среднего
  > Не точнее, а осторожнее: он намеренно сдвинут вверх.
- [ ] Так требует модель
  > Модель умеет оба варианта, выбор за бизнесом.
- [ ] Среднее нельзя перевести в людей
  > Можно, но в половине часов людей не хватит.
:::


## task: split | Шаг 1. Разбиение по времени | base

Постройте `df = make(s)`, `X`, `y` и три маски: `train` (до 2026-07-01), `valid` (июль), `test` (август). Сохраните `sizes` — словарь `{"train": ..., "valid": ..., "test": ...}` с числом строк.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
```

### starter
```python
# уже есть: make(s) — таблица признаков для прогноза на завтра
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = make(s0)
w = {'train': int((d.index < '2026-07-01').sum()), 'valid': int(((d.index >= '2026-07-01') & (d.index < '2026-08-01')).sum()), 'test': int((d.index >= '2026-08-01').sum())}
assert dict(need('sizes')) == w, f'sizes = {need("sizes")}, а нужно {w}.'
```

### hint
Таблица признаков — `df = make(s)`, ответ — `y = df["y"]`, признаки — `X = df.drop(columns="y")`.

### hint
Маски — сравнения индекса со строками-датами: `df.index < "2026-07-01"`. Июль: `(df.index >= "2026-07-01") & (df.index < "2026-08-01")`.

### hint
Размеры — `int(train.sum())` и т. д.: сумма `True` в маске — число строк.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
sizes = {"train": int(train.sum()), "valid": int(valid.sum()), "test": int(test.sum())}
```

### explain
Для временного ряда части берутся по времени, а не случайно: обучение — март–июнь (2760 часов), валидация — июль (744 часа = 31 × 24), тест — август (744 часа). Случайное разбиение позволило бы модели «подсмотреть» соседние часы из будущего, и оценка вышла бы завышенной. Обучение начинается с 8 марта, а не с 1-го: первую неделю съедают лаги. Валидация нужна для выбора модели и параметров, тест — только для финальной проверки один раз.

## task: baseline | Шаг 2. Ориентир и требование | base

Посчитайте RMSE прогноза «среднее за 4 недели» (столбец `mean4w`) на тесте — `rmse_base` (3 знака). В `base_meets` сохраните, проходит ли ориентир требование «RMSE ≤ 4.3».

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
```

### starter
```python
# уже есть: df, X, y и маски train, valid, test
import numpy as np

```

### check
```python
import numpy as _np
w = round(float(_np.sqrt(((y[test] - X.loc[test, 'mean4w']) ** 2).mean())), 3)
assert close(need('rmse_base'), w, 0.002), f'rmse_base = {need("rmse_base")}, а нужно {w}.'
assert need('base_meets') == (w <= 4.3), f'base_meets = {need("base_meets")}.'
```

### hint
Ориентир уже лежит среди признаков: столбец `mean4w` — это и есть прогноз «среднее за 4 недели».

### hint
`np.sqrt(((y[test] - X.loc[test, "mean4w"]) ** 2).mean())`.

### solution
```python
import numpy as np
rmse_base = round(float(np.sqrt(((y[test] - X.loc[test, "mean4w"]) ** 2).mean())), 3)
base_meets = rmse_base <= 4.3
```

### explain
Ориентир не проходит требование — но не так уж далёк (около 4.35). Значит, модели нужно не «научиться прогнозировать с нуля», а аккуратно уточнить и без того хороший прогноз.

## task: select | Шаг 3. Выбор на валидации | plus

Обучите на `train` и проверьте на `valid` четыре модели: `LinearRegression()`, `HistGradientBoostingRegressor(random_state=0)`, `HistGradientBoostingRegressor(max_depth=3, random_state=0)`, `HistGradientBoostingRegressor(l2_regularization=1.0, random_state=0)`. Сохраните словарь `valid_rmse` с ключами `"linear"`, `"hgb"`, `"hgb_depth3"`, `"hgb_l2"` (3 знака) и `best` — ключ лучшей.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
```

### starter
```python
# уже есть: df, X, y и маски train, valid, test
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor

```

### check
```python
import numpy as _np
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import HistGradientBoostingRegressor as _H
ms = {'linear': _LR(), 'hgb': _H(random_state=0), 'hgb_depth3': _H(max_depth=3, random_state=0), 'hgb_l2': _H(l2_regularization=1.0, random_state=0)}
w = {k: round(float(_np.sqrt(((y[valid] - m.fit(X[train], y[train]).predict(X[valid])) ** 2).mean())), 3) for k, m in ms.items()}
got = need('valid_rmse', dict)
assert all(k in got and close(got[k], v, 0.002) for k, v in w.items()), f'valid_rmse = {got}, а нужно {w}.'
assert need('best') == min(w, key=w.get), f'best = {need("best")!r}.'
```

### hint
Каждая модель обучается на `train` и проверяется на `valid` — тест в этом шаге не трогаем.

### hint
Словарь моделей и цикл; лучшая — `min(valid_rmse, key=valid_rmse.get)`.

### solution
```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor

models = {
    "linear": LinearRegression(),
    "hgb": HistGradientBoostingRegressor(random_state=0),
    "hgb_depth3": HistGradientBoostingRegressor(max_depth=3, random_state=0),
    "hgb_l2": HistGradientBoostingRegressor(l2_regularization=1.0, random_state=0),
}
valid_rmse = {}
for name, m in models.items():
    p = m.fit(X[train], y[train]).predict(X[valid])
    valid_rmse[name] = round(float(np.sqrt(((y[valid] - p) ** 2).mean())), 3)
best = min(valid_rmse, key=valid_rmse.get)
```

### explain
Неглубокий бустинг (4.059) и линейная регрессия (4.084) почти неразличимы, бустинг по умолчанию — хуже: признаки уже содержат сезонность (`mean4w`, лаги), и сложной модели нечего добавить, кроме шума. При такой разнице обычно берут модель попроще — её легче объяснить и поддерживать. Здесь мы всё же идём дальше с неглубоким бустингом, и причина практическая: у него есть параметры, которые стоит подобрать по времени (шаг 3б), и квантильная версия `loss="quantile"` для шага 6 — план смен по верхней оценке. Обычная `LinearRegression` прогнозирует только середину. По точности выбор почти ничего не стоит: на августе линейная регрессия дала бы те же 4.21 (4.213 против 4.209 у бустинга из шага 4).

## task: grid | Шаг 3б. Подбор параметров по времени | plus

В шаге 3 модель выбрана на одном месяце (июль): впереди неглубокий бустинг, но его параметры взяты наугад. Надёжнее проверить параметры на нескольких кусках прошлого — кросс-валидацией **по времени**. Подберите параметры бустинга на `train | valid` (март–июль) — найденные `best_params` станут параметрами финальной модели в шаге 4:

```python static
GridSearchCV(HistGradientBoostingRegressor(random_state=0),
             {"max_depth": [2, 3, None], "learning_rate": [0.05, 0.1]},
             cv=TimeSeriesSplit(n_splits=3), scoring="neg_root_mean_squared_error")
```

Сохраните обученный объект в `gs`, лучшие параметры — в `best_params` (словарь), их RMSE на кросс-валидации — `cv_rmse` (положительное число, 3 знака). Затем посчитайте RMSE лучшей модели на августе с обрезкой нулём — `rmse_test_grid` (3 знака) и сравните с требованием 4.3.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
```

### starter
```python
# уже есть: df, X, y и маски train, valid, test
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

fit_mask = train | valid

```

### check
```python
import numpy as _np
from sklearn.model_selection import GridSearchCV as _GS, TimeSeriesSplit as _TS, cross_val_score as _cvs
from sklearn.ensemble import HistGradientBoostingRegressor as _H
g = need('gs', _GS)
assert hasattr(g, 'best_params_'), 'gs ещё не обучен: вызовите gs.fit(X[fit_mask], y[fit_mask]).'
assert isinstance(g.cv, _TS) and g.cv.n_splits == 3, f'cv = {g.cv!r}. Для ряда нужен TimeSeriesSplit(n_splits=3), а не число фолдов: cv=3 означает обычный KFold без учёта времени.'
assert g.scoring == 'neg_root_mean_squared_error', f'scoring = {g.scoring!r}; нужен "neg_root_mean_squared_error".'
pg = {k: list(v) for k, v in g.param_grid.items()}
assert pg == {'max_depth': [2, 3, None], 'learning_rate': [0.05, 0.1]}, f'Сетка параметров: {pg}.'
fm = train | valid
assert g.n_features_in_ == X.shape[1] and len(g.cv_results_['split0_test_score']) == 6, 'Обучайте gs на X[fit_mask], y[fit_mask].'
bp = dict(g.best_params_)
ref = -_cvs(_H(random_state=0, **bp), X[fm], y[fm], cv=_TS(n_splits=3), scoring='neg_root_mean_squared_error').mean()
assert close(-g.best_score_, ref, 1e-6), 'gs обучен не на train | valid: лучший результат не совпадает с пересчётом на марте–июле.'
assert dict(need('best_params', dict)) == bp, f'best_params = {need("best_params")}, а у gs — {bp}.'
assert close(need('cv_rmse'), round(float(ref), 3), 0.002), f'cv_rmse = {need("cv_rmse")}, а нужно {ref:.3f}. best_score_ отрицательный — поменяйте знак.'
pt = _np.clip(_H(random_state=0, **bp).fit(X[fm], y[fm]).predict(X[test]), 0, None)
rt = round(float(_np.sqrt(((y[test] - pt) ** 2).mean())), 3)
assert close(need('rmse_test_grid'), rt, 0.002), f'rmse_test_grid = {need("rmse_test_grid")}, а нужно {rt}. Прогноз gs.predict(X[test]) обрежьте нулём.'
```

### hint
Объект `GridSearchCV` из условия создаётся как есть, потом `gs.fit(X[fit_mask], y[fit_mask])`. Он сам переберёт 6 сочетаний на 3 фолдах по времени и переобучит лучшее на всех данных `fit_mask` (`refit=True` по умолчанию).

### hint
Лучшие параметры — `gs.best_params_`, лучший результат — `gs.best_score_` (отрицательный RMSE, поэтому `-gs.best_score_`). Прогноз на август — `gs.predict(X[test])`.

### hint
```python
gs = GridSearchCV(..., cv=TimeSeriesSplit(n_splits=3), scoring="neg_root_mean_squared_error")
gs.fit(X[fit_mask], y[fit_mask])
best_params = gs.best_params_
cv_rmse = round(-gs.best_score_, 3)
p = np.clip(gs.predict(X[test]), 0, None)
rmse_test_grid = ...
```

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

fit_mask = train | valid
gs = GridSearchCV(
    HistGradientBoostingRegressor(random_state=0),
    {"max_depth": [2, 3, None], "learning_rate": [0.05, 0.1]},
    cv=TimeSeriesSplit(n_splits=3),
    scoring="neg_root_mean_squared_error",
)
gs.fit(X[fit_mask], y[fit_mask])
best_params = gs.best_params_
cv_rmse = round(float(-gs.best_score_), 3)
p = np.clip(gs.predict(X[test]), 0, None)
rmse_test_grid = round(float(np.sqrt(((y[test] - p) ** 2).mean())), 3)
print(best_params, cv_rmse, rmse_test_grid)
```

### explain
Три фолда по времени: обучение с 8 марта до 13 апреля → проверка до 19 мая; затем до 19 мая → до 25 июня; затем до 25 июня → до конца июля (по 876 часов в каждой проверке). Лучшим оказался неглубокий бустинг с медленным шагом (`max_depth=3`, `learning_rate=0.05`) со средним RMSE около 3.88, на августе — около 4.21: требование выполнено, и чуть лучше, чем победитель шага 3 с шагом по умолчанию (4.23). Август труднее фолдов: заказов больше, и ошибки в штуках крупнее.

Что было бы с привычным `cv=3`: это обычный KFold, в котором обучающие куски лежат и до, и после проверочного. Кросс-валидация показала бы около 3.70, а с перемешиванием `KFold(3, shuffle=True, random_state=0)` — около 3.64: на 0.2 оптимистичнее честной оценки. Параметры здесь выбраны те же, поэтому август бы не пострадал, но оценка 3.6–3.7 пообещала бы менеджеру точность, которой нет. На других данных перемешанные фолды выбирают и другие параметры: они вознаграждают модель за «подглядывание» в соседние часы, а не за умение прогнозировать вперёд. Заметить ошибку можно по самому объекту: `gs.cv` должен быть `TimeSeriesSplit`, а не число.

## task: final | Шаг 4. Финальная проверка | base

В заготовке `best_params` — параметры бустинга, найденные по времени в шаге 3б. Обучите `HistGradientBoostingRegressor(random_state=0, **best_params)` на `train | valid`, обрежьте прогноз снизу нулём (`np.clip(p, 0, None)`) и посчитайте RMSE на тесте — `rmse_final` (3 знака). Сохраните `pred_test` (массив прогнозов) и `meets` — выполнено ли требование целиком: RMSE ≤ 4.3 **и** лучше ориентира `rmse_base`.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
rmse_base = float(np.sqrt(((y[test] - X.loc[test, "mean4w"]) ** 2).mean()))
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
_ref_model = HistGradientBoostingRegressor(random_state=0, learning_rate=0.05, max_depth=3)
```

### starter
```python
# уже есть: X, y, маски train/valid/test, rmse_base и best_params из шага 3б
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

```

### check
```python
import numpy as _np
fit = train | valid
p = _np.clip(_ref_model.fit(X[fit], y[fit]).predict(X[test]), 0, None)
r = round(float(_np.sqrt(((y[test] - p) ** 2).mean())), 3)
assert _np.allclose(need('pred_test'), p, atol=1e-6), 'pred_test — прогноз HistGradientBoostingRegressor(random_state=0, **best_params), обученного на train | valid, обрезанный нулём.'
assert close(need('rmse_final'), r, 0.002), f'rmse_final = {need("rmse_final")}, а нужно {r}.'
assert need('meets') == (r <= 4.3 and r < rmse_base), f'meets = {need("meets")}.'
```

### hint
Перед тестом выбранную модель переобучают на всём прошлом — обучении и валидации вместе.

### hint
`fit_mask = train | valid`; `model = HistGradientBoostingRegressor(random_state=0, **best_params)`; `p = np.clip(model.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)`. Запись `**best_params` раскрывает словарь в именованные аргументы.

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
fit_mask = train | valid
model = HistGradientBoostingRegressor(random_state=0, **best_params)
pred_test = np.clip(model.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)
rmse_final = round(float(np.sqrt(((y[test] - pred_test) ** 2).mean())), 3)
meets = (rmse_final <= 4.3) and (rmse_final < rmse_base)
```

### explain
Около 4.21 — требование выполнено, и ориентир (4.35) побеждён. Победа скромная, примерно на 0.14 заказа в час, но честная: семейство модели выбрано на июле, параметры — на фолдах по времени внутри марта–июля, а август модель увидела один раз. Победитель шага 3 с параметрами по умолчанию дал бы 4.23: подбор по времени добавил немного, но и это улучшение получено без подглядывания в тест.

## task: staffing | Шаг 5. Прогноз в людях | plus

Переведите прогноз в бариста: нужно `max(1, ceil(заказы / 6))` человек в час (с 7 до 22 включительно; ночью выдачу не планируем). Посчитайте для теста:

- `needed` — сколько бариста нужно было по факту;
- план по модели (`pred_test` в заготовке) и план по ориентиру (`mean4w`).

Для каждого плана сохраните в словарь `plans` (`{"модель": {...}, "ориентир": {...}}`) долю часов с нехваткой людей `short` (план < нужного, 3 знака) и число лишних бариста-часов `extra` (сумма положительных `план − нужно`).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
pred_test = np.clip(HistGradientBoostingRegressor(random_state=0, **best_params).fit(X[train | valid], y[train | valid]).predict(X[test]), 0, None)
_ref_pred = pred_test.copy()
```

### starter
```python
# уже есть: X, y, маски и pred_test — прогноз модели на август
import numpy as np

y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)

```

### check
```python
import numpy as _np
yt = y[test]; oh = (yt.index.hour >= 7) & (yt.index.hour <= 22)
nd = _np.maximum(1, _np.ceil(yt.values / 6))
w = {}
for k, p in [('модель', _ref_pred), ('ориентир', X.loc[test, 'mean4w'].values)]:
    pl = _np.maximum(1, _np.ceil(p / 6))
    w[k] = (round(float(((pl < nd) & oh).sum() / oh.sum()), 3), float(_np.clip(pl - nd, 0, None)[oh].sum()))
got = need('plans', dict)
for k, (sh, ex) in w.items():
    assert k in got, f'Нет ключа {k!r} в plans.'
    assert close(got[k]['short'], sh, 0.002) and close(got[k]['extra'], ex, 0.5), f'{k}: short, extra = {got[k]["short"]}, {got[k]["extra"]}, а нужно {sh}, {ex}.'
```

### hint
Бариста нужно столько, чтобы обслужить все заказы часа: заказы / 6, округлённые вверх; в часы работы — не меньше одного.

### hint
Нужно по факту: `needed = np.maximum(1, np.ceil(y_test.values / 6))`. План — та же формула от прогноза. Считайте только по маске `open_hours`.

### solution
```python
import numpy as np

y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)
needed = np.maximum(1, np.ceil(y_test.values / 6))
plans = {}
for name, p in [("модель", pred_test), ("ориентир", X.loc[test, "mean4w"].values)]:
    plan = np.maximum(1, np.ceil(p / 6))
    short = round(float(((plan < needed) & open_hours).sum() / open_hours.sum()), 3)
    extra = float(np.clip(plan - needed, 0, None)[open_hours].sum())
    plans[name] = {"short": short, "extra": extra}
```

### explain
Неожиданный результат: по RMSE модель лучше, а нехватка людей у неё случается почти в трети рабочих часов — даже чаще, чем у ориентира. Причина в самой постановке: модель прогнозирует «середину», то есть примерно в половине часов факт выше прогноза, а округление вверх лишь частично это компенсирует. К тому же в августе заказов больше, чем в среднем в обучающих месяцах. Точность в среднем не равна хорошему решению — дальше шаг 6.

## task: quantile | Шаг 6. План по верхнему квантилю | star

Если нехватка рук дороже лишней смены, планируют не по середине, а по **верхнему квантилю**: значение, которое факт превышает лишь в ~20 % случаев. Обучите `HistGradientBoostingRegressor(loss="quantile", quantile=0.8, random_state=0, **best_params)` (параметры из шага 3б есть в заготовке) на `train | valid`, обрежьте нулём и постройте план как в шаге 5. Сохраните `coverage` — долю часов теста, где факт не выше прогноза (3 знака), `short_q` (доля часов нехватки, 3 знака) и `extra_q` (лишние бариста-часы) — по рабочим часам.

### setup
```python
import numpy as np
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
```

### starter
```python
# уже есть: X, y, маски train, valid, test и best_params
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

```

### check
```python
import numpy as _np
from sklearn.ensemble import HistGradientBoostingRegressor as _H
fm = train | valid
pq = _np.clip(_H(loss='quantile', quantile=0.8, learning_rate=0.05, max_depth=3, random_state=0).fit(X[fm], y[fm]).predict(X[test]), 0, None)
yt = y[test]; oh = (yt.index.hour >= 7) & (yt.index.hour <= 22)
nd = _np.maximum(1, _np.ceil(yt.values / 6)); pl = _np.maximum(1, _np.ceil(pq / 6))
assert close(need('coverage'), round(float((yt.values <= pq).mean()), 3), 0.002), f'coverage = {need("coverage")}.'
assert close(need('short_q'), round(float(((pl < nd) & oh).sum() / oh.sum()), 3), 0.002), f'short_q = {need("short_q")}.'
assert close(need('extra_q'), float(_np.clip(pl - nd, 0, None)[oh].sum()), 0.5), f'extra_q = {need("extra_q")}.'
```

### hint
Квантильная модель — `HistGradientBoostingRegressor(loss="quantile", quantile=0.8, ...)`; обучение — на тех же данных, что финальная модель.

### hint
Покрытие: `(y_test.values <= p).mean()`. План и подсчёт — как в шаге 5.

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

fit_mask = train | valid
q = HistGradientBoostingRegressor(loss="quantile", quantile=0.8, random_state=0, **best_params)
p = np.clip(q.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)
y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)
coverage = round(float((y_test.values <= p).mean()), 3)
needed = np.maximum(1, np.ceil(y_test.values / 6))
plan = np.maximum(1, np.ceil(p / 6))
short_q = round(float(((plan < needed) & open_hours).sum() / open_hours.sum()), 3)
extra_q = float(np.clip(plan - needed, 0, None)[open_hours].sum())
```

### explain
Покрытие около 74 % — меньше заданных 80 %: модель обучена на месяцах, когда заказов было меньше, и рост августа она недооценивает. Тем не менее часов нехватки стало вдвое меньше (около 15 % против 30 % у модели «по середине»), а платим за это примерно 290 лишними бариста-часами за месяц (у плана «по середине» их 120). Какая точка лучше — решает бизнес, сравнивая цену часа бариста с ценой потерянного заказа. Аналитик показывает этот выбор, а не прячет его за одним RMSE.

## Итог для операционного менеджера

> **Модель.** Прогноз заказов на каждый час завтрашнего дня строится в 20:00 накануне только по данным, которые к этому времени уже есть. Он ошибается в среднем примерно на 4.2 заказа в час (RMSE) против 4.35 у правила «среднее за 4 недели» — требование выполнено. Главное в модели — та же логика, что у правила, плюс учёт акций и текущего уровня заказов.
>
> **Как планировать смены.** Три плана на август, по рабочим часам с 7 до 22:
>
> | план | часов с нехваткой людей | лишних бариста-часов за месяц |
> |---|---|---|
> | нынешнее правило (среднее за 4 недели) | 28.8 % | 142 |
> | модель «по середине» | 30.4 % | 120 |
> | модель по верхней оценке (квантиль 0.8) | 14.9 % | 291 |
>
> Скажем честно: модель точнее правила по RMSE, но для смен сама по себе выигрыша не даёт — нехватка людей у неё даже чуть чаще, чем у правила. Оба прогноза нацелены на середину, а заказов в августе больше, чем в обучающих месяцах. Выигрыш даёт только план по верхней оценке: нехватка — вдвое реже, цена — около 290 лишних бариста-часов в месяц вместо 120–140. Предлагаем его.
>
> **Что дальше.** Переобучать модель каждую неделю (рост аудитории быстро делает её «осторожной»), заносить даты акций в календарь заранее и следить за прогнозом по мониторингу из главы 8.

::: figure ts-staffing
От заказов к людям на одном часе августа и итог за месяц: прогноз «по середине» недобирает бариста почти в трети рабочих часов, план по квантилю 0.8 — вдвое реже, но ценой лишних смен. Числа — из решений шагов 5 и 6.
:::
