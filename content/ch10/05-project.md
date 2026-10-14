---
title: "Проект: прогноз дневной выручки"
files: [daily_sales.csv]
lead: "Финал главы. Управляющие кофейнями планируют смены и закупки по ощущениям. Строим прогноз выручки каждой кофейни на каждый день: честная проверка «по времени», простые ориентиры, линейная модель с ручными взаимодействиями, бустинг с подбором по валидации — и ловушка, которую деревья не видят: рост бизнеса."
recap:
  - "Данные во времени проверяют «по времени»: обучаемся на прошлом, проверяем на будущем. Случайное разбиение подглядывает в будущее."
  - "Первый ориентир для дневных рядов — «как неделю назад» (lag 7)."
  - "Линейная модель не видит взаимодействий (выходной × формат кофейни), пока их не добавить вручную. Бустинг находит их сам."
  - "Валидацию для подбора гиперпараметров тоже берут из последнего периода обучающих данных."
  - "Деревья не продолжают тренд: за пределами обучающих данных прогноз «застывает». Тренд снимают отдельно (делят на него ответ), а бустинг учит остальное."
  - "Модели сравнивают одной таблицей «модель | RMSE | MAE | fit, с | predict, мс». Время — `time.perf_counter()` вплотную вокруг `fit` и `predict`; CatBoost и LightGBM добавляют в ту же таблицу в своём Jupyter."
---

## Задача

> У нас шесть кофеен трёх форматов: на улице, в торговом центре и в бизнес-центре. Управляющие планируют смены бариста и закупку молока «на глаз», и мы то переплачиваем за лишние смены, то не успеваем обслужить гостей.
>
> Нужен прогноз выручки каждой кофейни на каждый день следующего полугодия: с учётом дня недели, праздников, погоды из прогноза и запланированных акций. Насколько точным он получится и стоит ли он того, чтобы на него переходить?
>
> *Операционный директор*

## Данные

`daily_sales.csv` — выручка по дням за 2024–2025 годы:

| столбец | что это |
|---|---|
| `date` | дата |
| `shop_id`, `city` | кофейня и город |
| `format` | формат: улица, ТЦ, бизнес-центр |
| `temp` | средняя температура дня, °C |
| `rain` | был ли дождь (1/0) |
| `holiday` | праздничный день (1/0) |
| `promo` | в этот день шла акция (1/0) |
| `revenue_k` | выручка, тыс. ₽ (целевой признак) |

Погоду на ближайшие дни берём из прогноза, праздники и акции известны заранее — поэтому все признаки можно использовать для прогноза на будущее.

## План

1. Осмотреть данные: как выручка зависит от формата и дня недели.
2. Подготовить признаки и разделить данные **по времени**: обучение — до 1 июля 2025, тест — июль–декабрь 2025.
3. Посчитать ориентиры: «как неделю назад» и линейную регрессию.
4. Добавить в линейную модель взаимодействия вручную.
5. Обучить бустинг и лес.
6. Подобрать бустинг на валидации (апрель–июнь 2025).
7. Разобраться с трендом.
8. Свести модели в одну таблицу: качество и время обучения и прогноза. В своём Jupyter добавить к ней CatBoost и LightGBM.

Признаки во всех шагах (функция `prep` в заготовках): температура, дождь, праздник, акция, день недели, месяц, выходной, номер дня от начала данных (`day_n`), флаги кофейни и формата.

::: figure sales-split
Как делим данные в шагах 2 и 6: обучение — до апреля 2025, валидация для подбора — апрель–июнь, тест — второе полугодие. Внизу для контраста — случайное разбиение, при котором тестовые дни перемешаны с обучающими.
:::

Заранее о ловушке шага 7. Сеть растёт, а деревья не продолжают тренд: для всех дат теста номер дня `day_n` больше любого известного, и каждое дерево отвечает так же, как для последних дней обучения.

::: figure trend-trap
Средняя дневная выручка по месяцам (все кофейни) и прогнозы бустинга на тесте: красный пунктир — бустинг по умолчанию, синяя линия — бустинг со снятым трендом из шага 7. Числа справа — декабрь 2025.
:::

::: quiz
Прогноз дневной выручки: почему разбиение на train и test делают по времени, а не случайно?

- [x] Модель будут применять к будущим дням; при случайном разбиении она «подсматривает» соседние дни и тренд из будущего
  > Честная проверка повторяет работу: учимся на прошлом, проверяем на следующем периоде.
- [ ] Так тест получается больше
  > Размер теста задают отдельно.
- [ ] Случайное разбиение не работает с датами
  > Работает технически, но даёт завышенную оценку.
- [ ] Чтобы train был меньше
  > Размер train тут ни при чём — важен порядок во времени.
:::

## task: look | Шаг 1. Формат и выходные | base

Посчитайте среднюю выручку по формату и выходным (суббота и воскресенье) — таблицу `pivot` (строки — формат, столбцы — 0/1 «выходной», 1 знак). Сохраните `weekend_ratio` — для каждого формата отношение выручки в выходной к будней (Series, 2 знака), и `most_weekday` — формат, который сильнее всего зависит от будней (наименьшее отношение).

### starter
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])
s["weekend"] = (s["date"].dt.weekday >= 5).astype(int)

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('daily_sales.csv', parse_dates=['date']); s0['weekend'] = (s0['date'].dt.weekday >= 5).astype(int)
pv = s0.groupby(['format', 'weekend'])['revenue_k'].mean().unstack()
p = need('pivot', _pd.DataFrame)
for f in pv.index:
    for w in (0, 1):
        assert close(p.loc[f, w], round(pv.loc[f, w], 1), 0.06), f'pivot[{f}, {w}] = {p.loc[f, w]}, а нужно {round(pv.loc[f, w], 1)}.'
r = (pv[1] / pv[0]).round(2)
wr = need('weekend_ratio', _pd.Series)
assert all(close(wr[f], r[f], 0.011) for f in r.index), f'weekend_ratio: ожидалось {r.to_dict()}.'
assert need('most_weekday') == r.idxmin(), f'most_weekday = {need("most_weekday")!r}.'
```

### hint
Столбец `weekend` уже есть в заготовке. Таблица — `s.groupby(["format", "weekend"])["revenue_k"].mean().unstack()`: формат в строках, выходной в столбцах.

### hint
Отношение — столбец `1`, делённый на столбец `0`: `pivot[1] / pivot[0]`. Формат с наименьшим отношением — `.idxmin()`.

### solution
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])
s["weekend"] = (s["date"].dt.weekday >= 5).astype(int)

pivot = s.groupby(["format", "weekend"])["revenue_k"].mean().unstack().round(1)
weekend_ratio = (pivot[1] / pivot[0]).round(2)
most_weekday = weekend_ratio.idxmin()
```

### explain
Форматы ведут себя противоположно: кофейня в бизнес-центре в выходные теряет две трети выручки, в торговом центре — получает на треть больше, уличная — чуть больше. Средний «эффект выходного» по сети ничего не говорит ни об одной кофейне. Это и есть **взаимодействие** признаков — запомним его.

## task: split | Шаг 2. Признаки и разбиение по времени | base

Напишите функцию `prep(s)`, которая добавляет `weekday`, `month`, `weekend`, `day_n` (дней от первой даты в данных) и возвращает таблицу признаков: `temp`, `rain`, `holiday`, `promo`, `weekday`, `month`, `weekend`, `day_n` плюс флаги `shop_id` и `format` (`pd.get_dummies(..., columns=["shop_id", "format"], dtype=int)`). Разделите данные по времени: `train` — даты до 2025-07-01, `test` — с этой даты. Сохраните `X`, маску `tr` (True для обучающих строк), `n_train`, `n_test`.

### starter
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('daily_sales.csv', parse_dates=['date'])
X0 = need('X', _pd.DataFrame)
assert len(X0) == len(s0), f'В X {len(X0)} строк, а в данных {len(s0)}.'
need_cols = {'temp', 'rain', 'holiday', 'promo', 'weekday', 'month', 'weekend', 'day_n'}
assert need_cols <= set(X0.columns), f'Не хватает столбцов: {need_cols - set(X0.columns)}.'
assert any(c.startswith('shop_id_') for c in X0.columns) and any(c.startswith('format_') for c in X0.columns), 'Нужны флаги shop_id_… и format_….'
assert 'revenue_k' not in X0.columns and 'date' not in X0.columns and 'city' not in X0.columns, 'В признаках не должно быть revenue_k, date и city.'
assert X0['day_n'].min() == 0 and X0['day_n'].max() == 730, 'day_n — дней от первой даты (от 0 до 730).'
w = (s0['date'] < '2025-07-01')
assert need('n_train') == int(w.sum()) and need('n_test') == int((~w).sum()), f'n_train, n_test = {need("n_train")}, {need("n_test")}.'
```

### hint
Признаки — календарь, формат кофейни (через `get_dummies`) и номер дня от начала данных; разбиение — по дате, без перемешивания.

### hint
`day_n = (s["date"] - s["date"].min()).dt.days`. Маска — `s["date"] < "2025-07-01"`.

### solution
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])

def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)

X = prep(s)
tr = s["date"] < "2025-07-01"
n_train, n_test = int(tr.sum()), int((~tr).sum())
```

### explain
Почему не `train_test_split`: при случайном разбиении в обучении оказались бы и 10, и 12 декабря 2025, а проверяли бы мы на 11-м — модель «знала бы» соседние дни из будущего. В жизни прогноз на декабрь делается в ноябре. Поэтому всё, что про время, проверяют только «прошлое → будущее».

## task: baselines | Шаг 3. Ориентиры | base

Посчитайте на тесте MAE двух ориентиров:

- `mae_lag7` — прогноз «как в тот же день неделю назад» для той же кофейни (`groupby("shop_id")["revenue_k"].shift(7)` после сортировки по кофейне и дате);
- `mae_lin` — `LinearRegression` на признаках `X` (обучение на `tr`).

Оба — 2 знака. В `lin_better` — `True`, если линейная модель лучше «недели назад».

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])
def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
```

### starter
```python
# уже есть: s (таблица) и prep(s) из шага 2
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

s = s.sort_values(["shop_id", "date"]).reset_index(drop=True)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"

```

### check
```python
import pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae
s0 = _pd.read_csv('daily_sales.csv', parse_dates=['date']).sort_values(['shop_id', 'date']).reset_index(drop=True)
X0 = prep(s0); y0 = s0['revenue_k']; t0 = s0['date'] < '2025-07-01'
lag = s0.groupby('shop_id')['revenue_k'].shift(7)
ml = round(_mae(y0[~t0], lag[~t0]), 2)
mn = round(_mae(y0[~t0], _LR().fit(X0[t0], y0[t0]).predict(X0[~t0])), 2)
assert close(need('mae_lag7'), ml, 0.011), f'mae_lag7 = {need("mae_lag7")}, а нужно {ml}.'
assert close(need('mae_lin'), mn, 0.011), f'mae_lin = {need("mae_lin")}, а нужно {mn}.'
assert need('lin_better') == (mn < ml), f'lin_better = {need("lin_better")}.'
```

### hint
«Как неделю назад» — `shift(7)` внутри `groupby("shop_id")`: таблица уже отсортирована по кофейне и дате, поэтому сдвиг на 7 строк — это тот же день неделю назад. Линейная модель — обучение на `X[tr]`, прогноз на `X[~tr]`.

### hint
`lag7 = s.groupby("shop_id")["revenue_k"].shift(7)`; тестовые строки — `~tr`.

### solution
```python
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

s = s.sort_values(["shop_id", "date"]).reset_index(drop=True)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"

lag7 = s.groupby("shop_id")["revenue_k"].shift(7)
mae_lag7 = round(mean_absolute_error(y[~tr], lag7[~tr]), 2)
lin = LinearRegression().fit(X[tr], y[tr])
mae_lin = round(mean_absolute_error(y[~tr], lin.predict(X[~tr])), 2)
lin_better = mae_lin < mae_lag7
```

### explain
Линейная модель (около 13 тыс. ₽ ошибки) **хуже** наивного «как неделю назад» (около 10). Причина — шаг 1: эффект выходного у форматов противоположный, а линейная модель умеет только «выходной: +X ко всем». Наивный прогноз этих сложностей не знает, но день недели и кофейня в нём «зашиты» автоматически.

## task: interactions | Шаг 4. Взаимодействия руками | base

Помогите линейной модели: добавьте к `X` три признака-произведения — `bc_off` (бизнес-центр × (выходной или праздник)), `mall_off` (ТЦ × (выходной или праздник)) и `street_rain` (улица × дождь). Обучите `LinearRegression` и сохраните `mae_inter` (2 знака) и `gain` — на сколько тысяч рублей ошибка меньше, чем у простой линейной модели (2 знака).

### setup
```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"
mae_lin = mean_absolute_error(y[~tr], LinearRegression().fit(X[tr], y[tr]).predict(X[~tr]))
```

### starter
```python
# уже есть: s, X, y, tr и mae_lin — ошибка простой линейной модели
off = ((X["weekend"] + X["holiday"]) > 0).astype(int)     # выходной или праздник

```

### check
```python
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae
X0 = prep(s); off0 = ((X0['weekend'] + X0['holiday']) > 0).astype(int)
X0['bc_off'] = X0['format_бизнес-центр'] * off0; X0['mall_off'] = X0['format_ТЦ'] * off0; X0['street_rain'] = X0['format_улица'] * X0['rain']
m = round(_mae(y[~tr], _LR().fit(X0[tr], y[tr]).predict(X0[~tr])), 2)
assert close(need('mae_inter'), m, 0.011), f'mae_inter = {need("mae_inter")}, а нужно {m}. Проверьте три новых признака.'
assert close(need('gain'), round(mae_lin - m, 2), 0.02), f'gain = {need("gain")}.'
```

### hint
Взаимодействие — произведение двух признаков: оно равно 1, только когда оба условия выполнены (бизнес-центр и выходной).

### hint
`X2 = X.copy()`, `X2["bc_off"] = X2["format_бизнес-центр"] * off` и так далее.

### solution
```python
off = ((X["weekend"] + X["holiday"]) > 0).astype(int)
X2 = X.copy()
X2["bc_off"] = X2["format_бизнес-центр"] * off
X2["mall_off"] = X2["format_ТЦ"] * off
X2["street_rain"] = X2["format_улица"] * X2["rain"]
lin2 = LinearRegression().fit(X2[tr], y[tr])
mae_inter = round(mean_absolute_error(y[~tr], lin2.predict(X2[~tr])), 2)
gain = round(mae_lin - mae_inter, 2)
```

### explain
Три признака, придуманные по результатам осмотра, вдвое уменьшили ошибку — до 6 тыс. ₽. Это мощный приём, но он требует знать, какие взаимодействия искать. Посмотрим, найдёт ли их бустинг сам.

## task: boosting | Шаг 5. Бустинг и лес | base

На исходных признаках `X` (без ручных взаимодействий) обучите `HistGradientBoostingRegressor(random_state=0)` и `RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0)`. Сохраните `mae_hgb`, `mae_rf` (2 знака) и `best_model` — `"бустинг"`, `"лес"` или `"линейная с взаимодействиями"` (её ошибка — `mae_inter` в заготовке).

### setup
```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"
_off = ((X["weekend"] + X["holiday"]) > 0).astype(int)
_X2 = X.copy(); _X2["bc_off"] = _X2["format_бизнес-центр"] * _off; _X2["mall_off"] = _X2["format_ТЦ"] * _off; _X2["street_rain"] = _X2["format_улица"] * _X2["rain"]
mae_inter = mean_absolute_error(y[~tr], LinearRegression().fit(_X2[tr], y[tr]).predict(_X2[~tr]))
```

### starter
```python
# уже есть: s, X, y, tr и mae_inter — ошибка линейной модели с взаимодействиями
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

```

### check
```python
from sklearn.ensemble import HistGradientBoostingRegressor as _H, RandomForestRegressor as _RF
from sklearn.metrics import mean_absolute_error as _mae
h = round(_mae(y[~tr], _H(random_state=0).fit(X[tr], y[tr]).predict(X[~tr])), 2)
r = round(_mae(y[~tr], _RF(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X[tr], y[tr]).predict(X[~tr])), 2)
assert close(need('mae_hgb'), h, 0.011), f'mae_hgb = {need("mae_hgb")}, а нужно {h}.'
assert close(need('mae_rf'), r, 0.011), f'mae_rf = {need("mae_rf")}, а нужно {r}.'
res = {'бустинг': h, 'лес': r, 'линейная с взаимодействиями': round(mae_inter, 2)}
assert need('best_model') == min(res, key=res.get), f'best_model = {need("best_model")!r}.'
```

### hint
Обучение на `X[tr], y[tr]`, прогноз на `X[~tr]`.

### hint
Обе модели — с `random_state=0`; MAE — `mean_absolute_error(y[~tr], pred)`.

### solution
```python
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

hgb = HistGradientBoostingRegressor(random_state=0).fit(X[tr], y[tr])
rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X[tr], y[tr])
mae_hgb = round(mean_absolute_error(y[~tr], hgb.predict(X[~tr])), 2)
mae_rf = round(mean_absolute_error(y[~tr], rf.predict(X[~tr])), 2)
res = {"бустинг": mae_hgb, "лес": mae_rf, "линейная с взаимодействиями": round(mae_inter, 2)}
best_model = min(res, key=res.get)
```

### explain
Бустинг без всякой ручной работы — около 5.3 тыс. ₽, лучше линейной модели с подсказками. Деревья сами нашли «бизнес-центр × выходной» и всё остальное. Лес почти так же хорош: на этих данных разница между ними невелика.

## task: tune | Шаг 6. Подбор на валидации | plus

Подберите бустинг честно. Валидация — апрель–июнь 2025 (`val`: обучающие строки с датой от 2025-04-01), обучение для подбора — даты до 2025-04-01 (`fit`). Для каждой пары `learning_rate` в `[0.05, 0.1]` и `max_depth` в `[3, 6, None]` обучите `HistGradientBoostingRegressor(learning_rate=..., max_depth=..., max_iter=500, early_stopping=False, random_state=0)` на `fit`, по `staged_predict` найдите лучшее число итераций на `val` и его MAE. Сохраните DataFrame `grid` (столбцы `lr`, `depth`, `n_iter`, `val_mae`), лучшую строку — в `best` (Series), затем обучите модель с лучшими параметрами и `max_iter=n_iter` на **всём** обучении (`tr`) и сохраните `test_mae` (2 знака). Осторожно: в DataFrame глубина `None` превращается в `NaN`, а `HistGradientBoostingRegressor(max_depth=nan)` падает с ошибкой. Переведите её обратно: `None if pd.isna(best["depth"]) else int(best["depth"])`.

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"
```

### starter
```python
# уже есть: s, X, y, tr
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

fit = s["date"] < "2025-04-01"
val = tr & ~fit

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.metrics import mean_absolute_error as _mae
f0 = s['date'] < '2025-04-01'; v0 = tr & ~f0; rows = []
for lr in [0.05, 0.1]:
    for md in [3, 6, None]:
        m = _H(learning_rate=lr, max_depth=md, max_iter=500, early_stopping=False, random_state=0).fit(X[f0], y[f0])
        cv = [_mae(y[v0], p) for p in m.staged_predict(X[v0])]; k = int(_np.argmin(cv)) + 1
        rows.append((lr, md, k, cv[k - 1]))
g = need('grid', _pd.DataFrame)
assert len(g) == 6, f'В grid {len(g)} строк, нужно 6.'
for (lr, md, k, v), (_, row) in zip(rows, g.iterrows()):
    assert row['n_iter'] == k and close(row['val_mae'], v, 0.01), f'lr={lr}, depth={md}: n_iter, val_mae = {row["n_iter"]}, {row["val_mae"]}, а нужно {k}, {round(v, 3)}.'
b = min(rows, key=lambda r: r[3])
fm = _H(learning_rate=b[0], max_depth=b[1], max_iter=b[2], early_stopping=False, random_state=0).fit(X[tr], y[tr])
t = round(_mae(y[~tr], fm.predict(X[~tr])), 2)
assert close(need('test_mae'), t, 0.011), f'test_mae = {need("test_mae")}, а нужно {t}. Финальная модель — с лучшими параметрами, на всём обучении.'
```

### hint
`max_depth=None` — без ограничения глубины (ограничивает число листьев). Строки grid собирайте словарями в список в порядке: lr 0.05 (depth 3, 6, None), потом lr 0.1.

### hint
Лучшая строка: `grid.loc[grid["val_mae"].idxmin()]`. Числа из неё приходят как `float`: `max_iter` переведите через `int(...)`, а глубину — как сказано в условии, через `pd.isna(...)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

fit = s["date"] < "2025-04-01"
val = tr & ~fit

rows = []
for lr in [0.05, 0.1]:
    for depth in [3, 6, None]:
        m = HistGradientBoostingRegressor(learning_rate=lr, max_depth=depth, max_iter=500,
                                          early_stopping=False, random_state=0).fit(X[fit], y[fit])
        curve = [mean_absolute_error(y[val], p) for p in m.staged_predict(X[val])]
        k = int(np.argmin(curve)) + 1
        rows.append({"lr": lr, "depth": depth, "n_iter": k, "val_mae": curve[k - 1]})
grid = pd.DataFrame(rows)
best = grid.loc[grid["val_mae"].idxmin()]
depth = None if pd.isna(best["depth"]) else int(best["depth"])
final = HistGradientBoostingRegressor(learning_rate=best["lr"], max_depth=depth, max_iter=int(best["n_iter"]),
                                      early_stopping=False, random_state=0).fit(X[tr], y[tr])
test_mae = round(mean_absolute_error(y[~tr], final.predict(X[~tr])), 2)
```

### explain
Подбор немного помог (около 5.2 против 5.3 по умолчанию). Варианты в сетке отличаются на валидации в пределах нескольких десятых — бустинг не слишком капризен, если остановить его вовремя. Посмотрите на строку `lr = 0.05, depth = 3`: лучшее `n_iter` у неё ровно 500, то есть верхняя граница `max_iter`. Это сигнал, что модели не хватило деревьев и её ошибка на валидации (5.19) — ещё не предел: границу надо поднять и проверить снова. Если лучшее число итераций упирается в границу перебора, граница мала.

## task: trend | Шаг 7. Ловушка тренда | plus

Посмотрите на ошибки бустинга по умолчанию (`HistGradientBoostingRegressor(random_state=0)`) на тесте по месяцам: средняя ошибка `факт − прогноз` больше нуля значит, что модель занижает прогноз. Сеть растёт, а деревья не умеют продолжать тренд за пределы обучающих данных: для всех дат после июня 2025 `day_n` «как самый поздний известный день».

Исправим: оцените тренд линейной регрессией логарифма выручки на `day_n` по обучающим строкам, `trend = np.exp(модель.predict(s[["day_n"]]))`. Обучите бустинг (`random_state=0`) на признаках **без** `day_n` с ответом `y / trend`, а прогноз умножьте обратно на `trend`. Сохраните `bias_by_month` — среднюю ошибку `факт − прогноз` бустинга по умолчанию по месяцам теста (Series с индексом-номером месяца, 2 знака), `bias_before` и `bias_after` — среднюю ошибку `факт − прогноз` на всём тесте до и после (2 знака), `mae_after` (2 знака) и `growth` — годовой рост по тренду (`np.exp(коэффициент × 365)`, 3 знака).

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"
s["day_n"] = X["day_n"]
```

### starter
```python
# уже есть: s (со столбцом day_n), X, y, tr
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.metrics import mean_absolute_error as _mae
p0 = _H(random_state=0).fit(X[tr], y[tr]).predict(X[~tr])
tl = _LR().fit(s.loc[tr, ['day_n']], _np.log(y[tr])); trd = _np.exp(tl.predict(s[['day_n']]))
Xn = X.drop(columns=['day_n'])
p1 = _H(random_state=0).fit(Xn[tr], (y / trd)[tr]).predict(Xn[~tr]) * trd[~tr]
bm = (y[~tr] - p0).groupby(s.loc[~tr, 'date'].dt.month).mean().round(2)
gb = need('bias_by_month', _pd.Series)
assert sorted(int(k) for k in gb.index) == list(range(7, 13)), f'Индекс bias_by_month — номера месяцев теста 7…12, а сейчас {[int(k) for k in gb.index]}.'
assert all(close(gb[k], bm[k], 0.011) for k in bm.index), f'bias_by_month: ожидалось {({int(k): float(v) for k, v in bm.items()})}.'
assert close(need('bias_before'), round((y[~tr] - p0).mean(), 2), 0.011), f'bias_before = {need("bias_before")}.'
assert close(need('bias_after'), round((y[~tr] - p1).mean(), 2), 0.011), f'bias_after = {need("bias_after")}.'
assert close(need('mae_after'), round(_mae(y[~tr], p1), 2), 0.011), f'mae_after = {need("mae_after")}.'
assert close(need('growth'), round(_np.exp(tl.coef_[0] * 365), 3), 0.0011), f'growth = {need("growth")}.'
```

### hint
Ошибки по месяцам: `(y[~tr] - p_before).groupby(s.loc[~tr, "date"].dt.month).mean().round(2)`. Деревья не продолжают тренд: за пределами обучения прогноз «застывает» на уровне последних листьев. Поэтому тренд снимают отдельно линейной моделью, а бустинг учат на остатке.

### hint
Тренд: `tl = LinearRegression().fit(s.loc[tr, ["day_n"]], np.log(y[tr]))`. Коэффициент — `tl.coef_[0]`.

### hint
`trend` — массив numpy, поэтому его часть для теста — `trend[~tr.values]` или просто `trend[~tr]`.

### solution
```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

p_before = HistGradientBoostingRegressor(random_state=0).fit(X[tr], y[tr]).predict(X[~tr])
bias_by_month = (y[~tr] - p_before).groupby(s.loc[~tr, "date"].dt.month).mean().round(2)
bias_before = round((y[~tr] - p_before).mean(), 2)
print(bias_by_month)

tl = LinearRegression().fit(s.loc[tr, ["day_n"]], np.log(y[tr]))
trend = np.exp(tl.predict(s[["day_n"]]))
growth = round(np.exp(tl.coef_[0] * 365), 3)

Xn = X.drop(columns=["day_n"])
m = HistGradientBoostingRegressor(random_state=0).fit(Xn[tr], (y / trend)[tr])
p_after = m.predict(Xn[~tr]) * trend[~tr]
bias_after = round((y[~tr] - p_after).mean(), 2)
mae_after = round(mean_absolute_error(y[~tr], p_after), 2)
```

### explain
Тренд около +9 % в год. Без него бустинг занижал прогноз, и `bias_by_month` показывает где: в июле–ноябре средняя ошибка в пределах ±1.5 тыс. ₽, а в декабре — +5.27 тыс. ₽. Декабрь — пиковый месяц, где ошибка в процентах даёт больше всего рублей. После снятия тренда ошибка падает примерно до 5 тыс. ₽, а систематическое занижение сменилось небольшим завышением: тренд оценён по полутора годам и немного «перелетает». На практике тренд пересчитывают каждый месяц.

## task: compare | Шаг 8. Сравнение: качество и время | plus

Операционный директор спрашивает не только «насколько точно», но и «сколько это стоит в работе»: модель будут переобучать каждую ночь на свежих данных. Сведите модели проекта в одну таблицу. Для каждой модели из словаря `models` в заготовке обучите её на `tr`, спрогнозируйте тест и запишите:

- `rmse` и `mae` — ошибки на тесте, тыс. ₽ (2 знака);
- `fit_s` — время обучения в секундах, `predict_ms` — время прогноза на тесте в миллисекундах (`time.perf_counter()`).

Сохраните `table` (индекс — названия моделей, строки по возрастанию `rmse`), `best` — лучшую модель по `rmse`, `gain_vs_linear` — на сколько тыс. ₽ RMSE линейной модели больше, чем у лучшей (по значениям таблицы, 2 знака), и `nightly_ok` — `True`, если каждая модель обучается быстрее минуты.

Дальше — в своём Jupyter: в блокноте [ch10-catboost-lightgbm.ipynb](../notebooks/extra/ch10-catboost-lightgbm.ipynb) к той же таблице добавлены CatBoost и LightGBM; разбираем их в уроке «CatBoost и LightGBM в своём Jupyter» сразу после проекта. В браузере их нет, а в блокноте строка таблицы для них собирается так же:

```python static
# X_raw — те же признаки, но кофейня и формат строками (без get_dummies);
# fit — до апреля 2025, val — апрель–июнь: по нему ранняя остановка выбирает число деревьев
cb = CatBoostRegressor(iterations=3000, learning_rate=0.05, random_seed=0, verbose=0, early_stopping_rounds=100)
t0 = time.perf_counter()
cb.fit(X_raw[fit], y[fit], cat_features=["shop_id", "format"], eval_set=(X_raw[val], y[val]), use_best_model=True)
fit_s = time.perf_counter() - t0
```

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s):
    s = s.copy()
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - s["date"].min()).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    return pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"
```

### starter
```python
# уже есть: s, X, y, tr
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

models = {
    "линейная": LinearRegression(),
    "лес": RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0),
    "GradientBoosting": GradientBoostingRegressor(random_state=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(random_state=0),
}

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import GradientBoostingRegressor as _GB, HistGradientBoostingRegressor as _H, RandomForestRegressor as _RF
from sklearn.metrics import mean_absolute_error as _mae, mean_squared_error as _mse
ref = {}
for k, m in {'линейная': _LR(), 'лес': _RF(n_estimators=100, min_samples_leaf=3, random_state=0),
             'GradientBoosting': _GB(random_state=0), 'HistGradientBoosting': _H(random_state=0)}.items():
    p = m.fit(X[tr], y[tr]).predict(X[~tr])
    ref[k] = (round(float(_np.sqrt(_mse(y[~tr], p))), 2), round(float(_mae(y[~tr], p)), 2))
t = need('table', _pd.DataFrame)
assert set(t.index) == set(ref), f'Индекс table — названия моделей {sorted(ref)}, а сейчас {list(t.index)}.'
assert {'rmse', 'mae', 'fit_s', 'predict_ms'} <= set(t.columns), f'Нужны столбцы rmse, mae, fit_s, predict_ms, а сейчас {list(t.columns)}.'
for k, (r, a) in ref.items():
    assert close(t.loc[k, 'rmse'], r, 0.011), f'{k}: rmse = {t.loc[k, "rmse"]}, а нужно {r}. Обучение на tr, ошибка на ~tr.'
    assert close(t.loc[k, 'mae'], a, 0.011), f'{k}: mae = {t.loc[k, "mae"]}, а нужно {a}.'
assert (t['fit_s'] > 0).all() and (t['fit_s'] < 600).all(), f'fit_s = {t["fit_s"].round(3).tolist()}: время обучения в секундах.'
assert (t['predict_ms'] > 0).all() and t['predict_ms'].max() > 1, f'predict_ms = {t["predict_ms"].round(4).tolist()}: похоже на секунды, умножьте на 1000.'
assert list(t.index) == list(t.sort_values('rmse').index), 'Строки table должны идти по возрастанию rmse.'
assert need('best') == t['rmse'].idxmin(), f'best = {need("best")!r}.'
g = round(float(t.loc['линейная', 'rmse'] - t['rmse'].min()), 2)
assert close(need('gain_vs_linear'), g, 0.011), f'gain_vs_linear = {need("gain_vs_linear")}, а по таблице {g}: RMSE линейной минус RMSE лучшей.'
assert need('nightly_ok') == bool((t['fit_s'] < 60).all()), f'nightly_ok = {need("nightly_ok")}: все ли fit_s меньше 60 секунд по вашей таблице?'
```

### hint
Один цикл по `models.items()`: засечь время, обучить, остановить секундомер; засечь, спрогнозировать, остановить. Строку таблицы — словарём в список, в конце `pd.DataFrame(rows).set_index("model")`.

### hint
`fit_s = time.perf_counter() - t0` после `model.fit(X[tr], y[tr])`, `predict_ms = (time.perf_counter() - t0) * 1000` после `model.predict(X[~tr])`. RMSE — `np.sqrt(mean_squared_error(y[~tr], pred))`.

### hint
`table = pd.DataFrame(rows).set_index("model").sort_values("rmse")`, `best = table.index[0]`, `gain_vs_linear = round(float(table.loc["линейная", "rmse"] - table["rmse"].min()), 2)`, `nightly_ok = bool((table["fit_s"] < 60).all())`.

### solution
```python
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

models = {
    "линейная": LinearRegression(),
    "лес": RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0),
    "GradientBoosting": GradientBoostingRegressor(random_state=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(random_state=0),
}

rows = []
for name, model in models.items():
    t0 = time.perf_counter()
    model.fit(X[tr], y[tr])
    fit_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    pred = model.predict(X[~tr])
    predict_ms = (time.perf_counter() - t0) * 1000

    rows.append({"model": name,
                 "rmse": round(float(np.sqrt(mean_squared_error(y[~tr], pred))), 2),
                 "mae": round(float(mean_absolute_error(y[~tr], pred)), 2),
                 "fit_s": fit_s, "predict_ms": predict_ms})

table = pd.DataFrame(rows).set_index("model").sort_values("rmse")
best = table.index[0]
gain_vs_linear = round(float(table.loc["линейная", "rmse"] - table["rmse"].min()), 2)
nightly_ok = bool((table["fit_s"] < 60).all())
print(table.round(3))
print(best, gain_vs_linear, nightly_ok)
```

### explain
Лучший по RMSE — `HistGradientBoosting` (7.15), рядом лес (7.30), классический `GradientBoosting` со 100 неглубокими деревьями по умолчанию заметно хуже (8.61), линейная модель — вдвое хуже лучшей (15.91). Все модели обучаются за секунды, так что ночное переобучение не проблема ни для одной: на этих данных выбор делается по качеству. Время станет аргументом, когда кофеен будут сотни, а прогноз понадобится по часам. Тогда пригодится та же таблица, только с CatBoost и LightGBM. В нашем блокноте CatBoost с ранней остановкой по апрелю–июню дал RMSE 6.55 против 7.27 у HGB из того же блокнота. Там HGB тоже с ранней остановкой по апрелю–июню и с нативными категориями, поэтому его число не 7.15, как в вашей таблице. Подробно — в уроке «CatBoost и LightGBM в своём Jupyter» после проекта. Если бы вы замеряли время вместе с подсчётом метрик или печатью, `fit_s` включал бы лишнее. Секундомер ставят вплотную вокруг `fit` и `predict`.

## Итог для операционного директора

> **Точность.** Прогноз выручки кофейни на день ошибается в среднем примерно на 5 тыс. ₽ при средней дневной выручке во втором полугодии около 66 тыс. — меньше 8 %. Привычный ориентир «как неделю назад» ошибается вдвое сильнее (около 10 тыс. ₽).
>
> **Что важно для прогноза.** Формат кофейни определяет, как она реагирует на выходные и погоду: бизнес-центр в выходные теряет две трети выручки, торговый центр выигрывает треть, уличная кофейня проседает в дождь. Модель учитывает это сама.
>
> **Стоимость в работе.** Модель обучается на двух годах истории за секунды, поэтому её можно переобучать каждую ночь. Промышленная библиотека CatBoost в нашей проверке без снятия тренда ошибалась на 4.93 тыс. ₽ в день — почти столько же, сколько наш бустинг с поправкой на тренд (4.98). При переносе прогноза в рабочую систему её стоит проверить вместе со снятием тренда: выигрыш возможен, но пока не доказан.
>
> **Ограничения.** Модель учится на прошлом: рост сети, новые форматы или резкие изменения (ремонт рядом, новый конкурент) нужно учитывать отдельно. Тренд пересчитываем ежемесячно, качество проверяем по фактам каждую неделю (мониторинг из главы 8).
>
> **Рекомендация.** Перейти на прогноз для планирования смен и закупок, начав с двух кофеен на месяц и сравнив расходы на смены и списания с остальными.
