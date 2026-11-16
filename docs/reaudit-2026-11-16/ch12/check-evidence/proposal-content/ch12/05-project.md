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
  - "Обычный прогноз нацелен на среднее и не задаёт, как часто факт окажется выше. Если нехватка дороже избытка, планируют по верхнему квантилю — он задаёт эту долю прямо."
  - "Квантиль 0.8 задаёт цель покрытия 80 %, но фактическое покрытие на новой партии и в рабочих часах проверяют отдельно; округление до сотрудников меняет долю дефицитных часов."
---

## Задача

> График смен на выдаче заказов из приложения составляем накануне к 20:00 на весь следующий день. Сейчас ставим по среднему за этот час за 4 прошлые недели, и то бариста скучает, то очередь из курьеров.
>
> Нужна модель, которая прогнозирует число заказов на каждый час завтрашнего дня. Требование: RMSE на августе — не больше 4.3 заказа в час, и модель должна быть лучше нашего правила «среднее за этот час за 4 прошлые недели». Один бариста на выдаче успевает около 6 заказов в час; с 7 до 22 часов на выдаче всегда хотя бы один человек.
>
> *Операционный менеджер*

## План

Момент выпуска — 20:00 накануне; последняя полностью завершённая часовая метка — 19:00. Для первой выдачи на 1 августа исключите из fit ответы 31 июля 20:00–23:00; для июльской валидации аналогично исключите 30 июня 20:00–23:00. Наличие правильных лагов не делает будущие метки доступными для fit.

Подготовка будущих признаков отделяется от y: выпущенный прогноз содержит все 24 часа следующих суток, даже когда их спрос неизвестен. Не вызывайте dropna по неизвестной будущей цели. Даты выдачи, источников лагов, обучающих меток и выходных строк проверяются отдельно.


0. Момент прогноза и горизонт: какие признаки законны при решении в 20:00 (раздел ниже).
1. Признаки для горизонта «завтра» (раздел «Разберём вместе» урока «Прогноз: ориентиры, горизонт и метрики») и признак акции (задача «Признак „день акции“» урока «Признаки для прогноза ряда»); разбиение по времени: обучение — март–июнь, валидация — июль, тест — август.
2. Ориентир: «среднее за 4 недели» на тесте и проверка требования.
3. Выбор модели на валидации.
   Затем — подбор параметров победителя кросс-валидацией по времени: `GridSearchCV` с `cv=TimeSeriesSplit(n_splits=3)` на марте–июле. Обычное `cv=3` здесь — ошибка: это KFold, который не знает о времени.
4. Финальная модель — с параметрами из шага 3 б — на обучении + валидации, проверка на тесте.
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

Для единого выпуска в 20:00 выберите признаки, которые уже известны для каждого из 24 будущих часов. Лаг 24 для последнего часа завтрашнего дня обращается к сегодняшним 23:00, которых в момент выпуска ещё нет. Ошибка финального прогноза будет измерена после фиксации модели.

Функция признаков `make(s)` с этими признаками дана в заготовках: календарь, флаг акции, лаги 48 и 168, среднее за сутки со сдвигом 28 и `mean4w` — среднее за этот час в 4 прошлые недели.

## От прогноза к людям: зачем квантиль (шаги 5–6)

Шаги 1–4 отвечают на вопрос «сколько заказов будет». Менеджеру нужен другой ответ — «сколько человек поставить». В шаге 5 прогноз переводят в бариста: `max(1, ceil(заказы / 6))`. Обычная модель прогнозирует среднее: оно минимизирует квадратичную ошибку, но не обещает, в какой доле часов факт окажется выше. Это свойство медианы, а не среднего, и при скошенном спросе они расходятся. К тому же `ceil` до целого бариста даёт запас, так что факт выше прогноза ещё не значит нехватку. Долю часов с нехваткой средний прогноз не контролирует — её измеряют отдельно, это шаг 5.

Если нехватка дороже лишнего человека, план строят не по середине, а по **квантилю** (глава 4: квантиль 0.8 — значение, ниже которого 80 % данных). Пример: в 10 прошлых пятниц в 18:00 было 12, 14, 15, 15, 16, 17, 18, 19, 21 и 24 заказа. Среднее — 17.1, по нему нужно 3 бариста (17.1 / 6 ≈ 2.85, вверх — 3), и в трёх пятницах из десяти (19, 21, 24 заказа) рук бы не хватило. Квантиль 0.8 — 19.4 (`np.quantile(x, 0.8)`), по нему 4 бариста, и их хватило бы во все десять пятниц: квантиль задаёт целевую долю часов, где заказов меньше плана (80 %), а округление вверх до человека сдвигает фактическую долю ещё выше. Цена — лишний человек в обычные пятницы.

Модель умеет прогнозировать квантиль напрямую: `HistGradientBoostingRegressor(loss="quantile", quantile=0.8)` учится выдавать значение, которое факт превышает лишь примерно в 20 % случаев. Это шаг 6 — после того как в шаге 5 вы увидите, как часто план по среднему оставляет смены без рук.

::: quiz
Прогноз заказов переводят в число бариста. Почему план строят по квантилю 0.8, а не по среднему прогнозу?

- [x] Нехватка бариста в час пик стоит дороже лишнего человека: с запасом ошибаемся реже в опасную сторону
  > Квантиль — ответ на вопрос «сколько нужно, чтобы в 80 % часов хватило людей». Цена — лишние часы работы.
- [ ] Квантиль точнее среднего
  > Не точнее, а осторожнее: он намеренно сдвинут вверх.
- [ ] Так требует модель
  > Модель умеет оба варианта, выбор за бизнесом.
- [ ] Среднее нельзя перевести в людей
  > Можно, но средний прогноз не задаёт, в какой доле часов людей хватит: это надо мерить отдельно, а квантиль задаёт её прямо.
:::


## task: split | Шаг 1. Разбиение по времени | base

Постройте `df = make(s)`, `X`, `y` и три маски: `train` (до 2026-07-01), `valid` (июль), `test` (август). Сохраните `sizes` — словарь `{"train": ..., "valid": ..., "test": ...}` с числом строк.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
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
_df = need('df'); _X = need('X'); _y = need('y')
assert _X.index.equals(d.index) and list(_X.columns)==list(d.columns.drop('y')), 'X: сверяем схему и даты, target не должен быть признаком.'
assert _X.equals(d.drop(columns='y')) and _y.equals(d['y']), 'Сверьте все значения признаков/меток по времени.'
for _name,_mask in [('train',d.index<'2026-07-01'),('valid',(d.index>='2026-07-01')&(d.index<'2026-08-01')),('test',d.index>='2026-08-01')]:
    assert (need(_name)==_mask).all(), f'{_name}: состав строк не соответствует временной границе.'
_hidden=s0.copy(); _hidden.loc[_hidden.index>='2026-07-31 20:00']=float('nan')
_future=make(_hidden).loc['2026-08-01':'2026-08-01 23:00']
assert len(_future)==24 and _future.drop(columns='y').notna().all().all(), 'make должен строить24 будущие строки без y на1августа.'
import numpy as _np, pandas as _pd
def _same_frame(got, expected):
    assert isinstance(got, _pd.DataFrame), 'Сохраните DataFrame.'
    assert set(expected.columns)<=set(got.columns), 'Не хватает заявленных столбцов.'
    assert got.index.is_unique and len(got)==len(expected), 'Проверьте число строк и уникальность дат.'
    assert got.index.sort_values().equals(expected.index.sort_values()), 'Даты результата не совпадают.'
    assert _np.allclose(got.reindex(expected.index)[expected.columns].to_numpy(), expected.to_numpy(), atol=1e-8, rtol=0, equal_nan=True), 'Сверьте все значения по временным ключам.'

_same_frame(need('df'),d)
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
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
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
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
# rmse_base — 740 известных июльских часов; base_meets не является приёмкой августа.
```

### check
```python
vm = (valid & (y.index < '2026-07-31 20:00') & y.notna())
import numpy as _np
w = round(float(_np.sqrt(((y[vm] - X.loc[vm, 'mean4w']) ** 2).mean())), 3)
assert close(need('rmse_base'), w, 0.002), f'rmse_base = {need("rmse_base")}, а нужно {w}.'
assert need('base_meets') == (w <= 4.3), f'base_meets = {need("base_meets")}.'
```

### hint
Ориентир уже лежит среди признаков: столбец `mean4w` — это и есть прогноз «среднее за 4 недели».

### hint
`np.sqrt(((y[test] - X.loc[test, "mean4w"]) ** 2).mean())`.

### solution
```python
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
import numpy as np
rmse_base = round(float(np.sqrt(((y[valid_score] - X.loc[valid_score, "mean4w"]) ** 2).mean())), 3)
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
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
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
fit_mask = (train & (y.index < "2026-06-30 20:00") & y.notna())
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
```

### check
```python
import numpy as _np
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import HistGradientBoostingRegressor as _H
ms = {'linear': _LR(), 'hgb': _H(random_state=0), 'hgb_depth3': _H(max_depth=3, random_state=0), 'hgb_l2': _H(l2_regularization=1.0, random_state=0)}
fm = (train & (y.index < '2026-06-30 20:00') & y.notna())
vm = (valid & (y.index < '2026-07-31 20:00') & y.notna())
assert _np.array_equal(need('fit_mask'),fm), 'fit_mask исключает неизвестные ответы 30 июня 20:00–23:00.'
assert _np.array_equal(need('valid_score'),vm), 'valid_score — 740 июльских часов до 31 июля 20:00.'
w = {k: round(float(_np.sqrt(((y[vm] - m.fit(X[fm], y[fm]).predict(X[vm])) ** 2).mean())), 3) for k, m in ms.items()}
got = need('valid_rmse', dict)
assert all(k in got and close(got[k], v, 0.002) for k, v in w.items()), f'valid_rmse = {got}, а нужно {w}.'
assert need('best') == min(w, key=w.get), f'best = {need("best")!r}.'
# Check that unavailable fit labels and unavailable validation labels cannot affect selection.
for _start,_end in [('2026-06-30 20:00','2026-07-01'),('2026-07-31 20:00','2026-08-01')]:
    for _sign in (1,-1):
        _probe=dict(globals())
        _probe['X']=X.copy(); _probe['y']=y.copy()
        _unknown=(_probe['y'].index>=_start)&(_probe['y'].index<_end)
        _probe['y'].loc[_unknown]+=_sign*1000
        exec(_code,_probe)
        assert all(close(_probe['valid_rmse'][k],got[k],0.002) for k in w), 'Выбор модели зависит от ответов, неизвестных к моменту выпуска: исключите последние четыре часа из fit и из оценки июля.'
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
fit_mask = (train & (y.index < "2026-06-30 20:00") & y.notna())
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
valid_rmse = {}
for name, m in models.items():
    p = m.fit(X[fit_mask], y[fit_mask]).predict(X[valid_score])
    valid_rmse[name] = round(float(np.sqrt(((y[valid_score] - p) ** 2).mean())), 3)
best = min(valid_rmse, key=valid_rmse.get)
```

### explain
Неглубокий бустинг (4.059) и линейная регрессия (4.084) почти неразличимы, бустинг по умолчанию — хуже: признаки уже содержат сезонность (`mean4w`, лаги), и сложной модели нечего добавить, кроме шума. Сравнение модели/признаков и анализ ошибок выполняются на ранних периодах до открытия августа. При такой разнице обычно берут модель попроще — её легче объяснить и поддерживать. Здесь мы всё же идём дальше с неглубоким бустингом, и причина практическая: у него есть параметры, которые стоит подобрать по времени (шаг 3 б), и квантильная версия `loss="quantile"` для шага 6 — план смен по верхней оценке. Обычная `LinearRegression` прогнозирует только середину. По точности выбор почти ничего не стоит: август остаётся финальной оценкой уже выбранной процедуры; его результат не должен выбирать семейство.

## task: grid | Шаг 3 б. Подбор параметров по времени | plus

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
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
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

fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
# cv=TimeSeriesSplit(n_splits=3, gap=28); август здесь не оцениваем.
```

### check
```python
import numpy as _np
from sklearn.model_selection import GridSearchCV as _GS, TimeSeriesSplit as _TS, cross_val_score as _cvs
from sklearn.ensemble import HistGradientBoostingRegressor as _H
g = need('gs', _GS)
assert hasattr(g, 'best_params_'), 'gs ещё не обучен: вызовите gs.fit(X[fit_mask], y[fit_mask]).'
assert isinstance(g.cv, _TS) and g.cv.n_splits == 3 and g.cv.gap == 28, f'cv = {g.cv!r}. Для ряда нужен TimeSeriesSplit(n_splits=3, gap=28), а не число фолдов: cv=3 означает обычный KFold без учёта времени.'
assert g.scoring == 'neg_root_mean_squared_error', f'scoring = {g.scoring!r}; нужен "neg_root_mean_squared_error".'
pg = {k: list(v) for k, v in g.param_grid.items()}
assert pg == {'max_depth': [2, 3, None], 'learning_rate': [0.05, 0.1]}, f'Сетка параметров: {pg}.'
fm = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
assert g.n_features_in_ == X.shape[1] and len(g.cv_results_['split0_test_score']) == 6, 'Обучайте gs на X[fit_mask], y[fit_mask].'
bp = dict(g.best_params_)
ref = -_cvs(_H(random_state=0, **bp), X[fm], y[fm], cv=_TS(n_splits=3,gap=28), scoring='neg_root_mean_squared_error').mean()
assert close(-g.best_score_, ref, 1e-6), 'gs обучен не на ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna()): лучший результат не совпадает с пересчётом на марте–июле.'
assert dict(need('best_params', dict)) == bp, f'best_params = {need("best_params")}, а у gs — {bp}.'
assert close(need('cv_rmse'), round(float(ref), 3), 0.002), f'cv_rmse = {need("cv_rmse")}, а нужно {ref:.3f}. best_score_ отрицательный — поменяйте знак.'
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

fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
gs = GridSearchCV(
    HistGradientBoostingRegressor(random_state=0),
    {"max_depth": [2, 3, None], "learning_rate": [0.05, 0.1]},
    cv=TimeSeriesSplit(n_splits=3, gap=28),
    scoring="neg_root_mean_squared_error",
)
gs.fit(X[fit_mask], y[fit_mask])
best_params = gs.best_params_
cv_rmse = round(float(-gs.best_score_), 3)
print(best_params, cv_rmse)
```

### explain
Три фолда по времени: обучение с 8 марта до 13 апреля → проверка до 19 мая; затем до 19 мая → до 25 июня; затем до 25 июня → до конца июля (по 876 часов в каждой проверке). Лучшим оказался неглубокий бустинг с медленным шагом (`max_depth=3`, `learning_rate=0.05`) со средним RMSE около 3.88, на августе — около 4.21: требование выполнено, и чуть лучше, чем победитель шага 3 с шагом по умолчанию (4.23). Август труднее фолдов: заказов больше, и ошибки в штуках крупнее.

Что было бы с привычным `cv=3`: это обычный KFold, в котором обучающие куски лежат и до, и после проверочного. Кросс-валидация показала бы около 3.70, а с перемешиванием `KFold(3, shuffle=True, random_state=0)` — около 3.64: на 0.2 оптимистичнее честной оценки. Параметры здесь выбраны те же, поэтому август бы не пострадал, но оценка 3.6–3.7 пообещала бы менеджеру точность, которой нет. На других данных перемешанные фолды выбирают и другие параметры: они вознаграждают модель за «подглядывание» в соседние часы, а не за умение прогнозировать вперёд. Заметить ошибку можно по самому объекту: `gs.cv` должен быть `TimeSeriesSplit`, а не число.

## task: final | Шаг 4. Финальная проверка | base

В заготовке `best_params` — параметры бустинга, найденные по времени в шаге 3 б. Обучите `HistGradientBoostingRegressor(random_state=0, **best_params)` на `train | valid`, обрежьте прогноз снизу нулём (`np.clip(p, 0, None)`) и посчитайте RMSE на тесте — `rmse_final` (3 знака). Сохраните `pred_test` (массив прогнозов) и `meets` — выполнено ли требование целиком: RMSE ≤ 4.3 **и** лучше ориентира `rmse_base`.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
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
# В этом шаге rmse_base уже рассчитан на августе: сравниваем две зафиксированные политики.
# fit_mask исключает 31 июля 20:00–23:00; эти ответы на первую дату выпуска неизвестны.
```

### check
```python
import numpy as _np
fit = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
p = _np.clip(_ref_model.fit(X[fit], y[fit]).predict(X[test]), 0, None)
r = round(float(_np.sqrt(((y[test] - p) ** 2).mean())), 3)
assert _np.allclose(need('pred_test'), p, atol=1e-6), 'pred_test — прогноз HistGradientBoostingRegressor(random_state=0, **best_params), обученного на ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna()), обрезанный нулём.'
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
fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
model = HistGradientBoostingRegressor(random_state=0, **best_params)
pred_test = np.clip(model.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)
rmse_final = round(float(np.sqrt(((y[test] - pred_test) ** 2).mean())), 3)
meets = (rmse_final <= 4.3) and (rmse_final < rmse_base)
```

### explain
На августе RMSE зафиксированной модели — 4,216 заказа в час, у среднего четырёх прошлых недель — 4,353. Разница около 0,14 заказа в час. Для решения по сменам ещё предстоит сравнить нехватку людей и лишние бариста-часы.

## task: staffing | Шаг 5. Прогноз в людях | plus

Одна строка — час работы. Мощность одного бариста — шесть заказов в час. Если в 10:00 прогноз равен 7, а спрос — 11 заказам, план предусматривает двух бариста, и фактически нужны двое. План смены достаточен, хотя сам прогноз ниже спроса. Что произойдёт при прогнозе 6 и спросе 7?

Переведите прогноз в бариста: нужно `max(1, ceil(заказы / 6))` человек в час (с 7 до 22 включительно; ночью выдачу не планируем). Посчитайте для теста:

- `needed` — сколько бариста нужно было по факту;
- план по модели (`pred_test` в заготовке) и план по ориентиру (`mean4w`).

Для каждого плана сохраните в словарь `plans` (`{"модель": {...}, "ориентир": {...}}`) долю часов с нехваткой людей `short` (план < нужного, 3 знака) и число лишних бариста-часов `extra` (сумма положительных `план − нужно`). Добавьте `deficit` — суммарное число недостающих бариста-часов и `coverage_work` — долю рабочих часов, когда прогноз заказов покрыл наблюдаемый спрос (3 знака). Сохраните `needed` для каждого часа теста по порядку; при подсчёте четырёх показателей применяйте маску рабочих часов.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
pred_test = np.clip(HistGradientBoostingRegressor(random_state=0, **best_params).fit(X[((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())], y[((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())]).predict(X[test]), 0, None)
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
assert _np.array_equal(need('needed'), nd), 'Проверьте needed для каждого часа теста по порядку: фактические заказы делим на шесть, округляем вверх и берём не меньше одного.'
w = {}
for k, p in [('модель', _ref_pred), ('ориентир', X.loc[test, 'mean4w'].values)]:
    pl = _np.maximum(1, _np.ceil(p / 6))
    w[k] = (round(float(((pl < nd) & oh).sum() / oh.sum()), 3), float(_np.clip(pl - nd, 0, None)[oh].sum()))
got = need('plans', dict)
for k, (sh, ex) in w.items():
    assert k in got, f'Нет ключа {k!r} в plans.'
    assert close(got[k]['short'], sh, 0.002) and close(got[k]['extra'], ex, 0.5), f'{k}: short, extra = {got[k]["short"]}, {got[k]["extra"]}, а нужно {sh}, {ex}.'
for _name,_p in [('модель',_ref_pred),('ориентир',X.loc[test,'mean4w'].values)]:
    _plan=_np.maximum(1,_np.ceil(_p/6))
    assert close(got[_name]['deficit'],float(_np.clip(nd-_plan,0,None)[oh].sum())), 'deficit: нехватка человеко-часов в рабочее время.'
    assert close(got[_name]['coverage_work'],round(float((yt.values[oh]<=_p[oh]).mean()),3)), 'coverage_work: покрытие спроса прогнозом в рабочие часы.'

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
    plans[name] = {"short": short, "extra": extra, "deficit": float(np.clip(needed-plan,0,None)[open_hours].sum()), "coverage_work": round(float((y_test.values[open_hours]<=p[open_hours]).mean()),3)}
```

### explain
Неожиданный результат: по RMSE модель лучше, а нехватка людей у неё случается почти в трети рабочих часов — даже чаще, чем у ориентира. Причина в самой постановке: модель прогнозирует среднее и никак не ограничивает долю часов, где факт выше прогноза, а округление вверх лишь частично это компенсирует. К тому же в августе заказов больше, чем в среднем в обучающих месяцах. Точность в среднем не равна хорошему решению — дальше шаг 6.

## task: quantile | Шаг 6. План по верхнему квантилю | star

Перед сравнением смен задайте стоимость дефицитного и избыточного человеко-часа. Рядом с покрытием спроса и долей часов нехватки покажите суммарную нехватку мощности и лишние бариста-часы **в рабочих часах**; лучшая RMSE сама по себе не выбирает самый выгодный план. Если нехватка рук дороже лишней смены, планируют не по середине, а по **верхнему квантилю**: значение, которое факт превышает лишь в ~20 % случаев. Обучите `HistGradientBoostingRegressor(loss="quantile", quantile=0.8, random_state=0, **best_params)` (параметры из шага 3 б есть в заготовке) на `train | valid`, обрежьте нулём и постройте план как в шаге 5. Сохраните `coverage` — долю часов теста, где факт не выше прогноза (3 знака), `short_q` (доля часов нехватки, 3 знака) и `extra_q` (лишние бариста-часы) — по рабочим часам.

Для рабочих часов с 07:00 до 22:00 включительно отдельно сохраните `coverage_work` — долю исходных фактов не выше квантильного прогноза (три знака) и `deficit_q` — суммарное число недостающих бариста-часов после округления плана до работников. При мощности шесть заказов в час сравните нужное и запланированное число людей отдельно для каждого часа.

### setup
```python
import numpy as np
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
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
fm = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
pq = _np.clip(_H(loss='quantile', quantile=0.8, learning_rate=0.05, max_depth=3, random_state=0).fit(X[fm], y[fm]).predict(X[test]), 0, None)
yt = y[test]; oh = (yt.index.hour >= 7) & (yt.index.hour <= 22)
nd = _np.maximum(1, _np.ceil(yt.values / 6)); pl = _np.maximum(1, _np.ceil(pq / 6))
assert close(need('coverage'), round(float((yt.values <= pq).mean()), 3), 0.002), f'coverage = {need("coverage")}.'
assert close(need('short_q'), round(float(((pl < nd) & oh).sum() / oh.sum()), 3), 0.002), f'short_q = {need("short_q")}.'
assert close(need('extra_q'), float(_np.clip(pl - nd, 0, None)[oh].sum()), 0.5), f'extra_q = {need("extra_q")}.'
assert close(need('deficit_q'),float(_np.clip(nd-pl,0,None)[oh].sum())), 'deficit_q — нехватка человеко-часов.'
assert close(need('coverage_work'),round(float((yt.values[oh]<=pq[oh]).mean()),3)), 'coverage_work — рабочие часы, а не все24.'

```

### hint
Квантильная модель — `HistGradientBoostingRegressor(loss="quantile", quantile=0.8, ...)`; обучение — на тех же данных, что финальная модель.

### hint
Покрытие: `(y_test.values <= p).mean()`. План и подсчёт — как в шаге 5.

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
q = HistGradientBoostingRegressor(loss="quantile", quantile=0.8, random_state=0, **best_params)
p = np.clip(q.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)
y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)
coverage = round(float((y_test.values <= p).mean()), 3)
needed = np.maximum(1, np.ceil(y_test.values / 6))
plan = np.maximum(1, np.ceil(p / 6))
short_q = round(float(((plan < needed) & open_hours).sum() / open_hours.sum()), 3)
extra_q = float(np.clip(plan - needed, 0, None)[open_hours].sum())
deficit_q = float(np.clip(needed-plan,0,None)[open_hours].sum())
coverage_work = round(float((y_test.values[open_hours]<=p[open_hours]).mean()),3)

```

### explain
В августе квантильный прогноз покрывает фактический спрос в 73,9 % всех часов и в 69,8 % рабочих. После пересчёта прогнозов в целое число людей нехватка осталась в 14,9 % рабочих часов. Суммарно недоставало 90 бариста-часов, а избыточно было запланировано 296. Цель квантиля, фактическое покрытие и доля обеспеченных людьми часов здесь различаются.

## Итог для операционного менеджера

> Августовская проверка охватывает 744 часа, из них 496 рабочих (07:00–22:00 включительно). У модели на среднее RMSE 4,216 заказа в час, у ориентира — 4,353. Для смен полезнее посмотреть, сколько сотрудников не хватило и сколько было лишними при мощности шесть заказов на человека в час.
>
> | План | Покрытие спроса прогнозом в рабочие часы | Рабочих часов с нехваткой людей | Нехватка, бариста-часы | Избыток, бариста-часы |
> |---|---:|---:|---:|---:|
> | Среднее четырёх прошлых недель | 49,4 % | 28,8 % | 185 | 142 |
> | Модель на среднее | 44,0 % | 30,2 % | 192 | 118 |
> | Квантиль 0,8 | 69,8 % | 14,9 % | 90 | 296 |
>
> Квантильный план сокращает нехватку против ориентира на 95 бариста-часов и добавляет 154 избыточных. При одинаковой цене недостающего и лишнего часа их сумма у ориентира равна 327, у модели на среднее — 310, у квантиля — 386. Если недостающий час обходится втрое дороже лишнего, условные затраты составят 697, 694 и 566 соответственно. Для письма используйте ставки, выбранные до сравнения, и назовите план, который выбрали бы при этих ставках.

::: figure ts-staffing
От заказов к людям на одном часе августа и итог за месяц: прогноз «по середине» недобирает бариста почти в трети рабочих часов, план по квантилю 0.8 — вдвое реже, но ценой лишних смен. Числа сверены с решениями шагов 5 и 6.
:::
