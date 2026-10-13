---
title: "Проверка по времени: хвост ряда и TimeSeriesSplit"
lead: "Признаки без утечек — половина дела. Вторая половина — проверка: ряд нельзя делить случайно, иначе модель учится на часах после теста и оценка выходит оптимистичной. Разбираем честные способы — маску по дате, `train_test_split(shuffle=False)` и кросс-валидацию `TimeSeriesSplit` — и измеряем, насколько обманывает перемешивание."
files: [app_orders.csv]
recap:
  - "Проверка — только по времени: обучение на прошлом, тест на будущем. Для кросс-валидации — `TimeSeriesSplit`."
  - "Отложенная часть для ряда — хвост: `train_test_split(X, y, test_size=0.2, shuffle=False)` на таблице, отсортированной по времени. `stratify` с `shuffle=False` не работает."
  - "Маска по дате (`df.index < \"2026-08-01\"`) и `shuffle=False` дают одно и то же — хвост ряда в тесте; граница задаётся датой или долей строк."
  - "Перемешанное разбиение ряда оптимистично: модель видит соседние часы до и после каждого тестового. Проверка честности: `X_tr.index.max() < X_te.index.min()`."
---

Признаки без утечек мы построили в уроке «Признаки для прогноза ряда». Здесь та же таблица признаков — функция `make_features(s)`: календарь, лаги 1, 24, 168 и среднее за предыдущие сутки. Вопрос теперь другой: как поделить её на обучение и тест, чтобы оценка совпала с тем, что будет в работе.

## Отложенная выборка по времени: маска по дате и `shuffle=False`

Правило одно: модель обучается на прошлом и проверяется на будущем — как будет в работе. Самый простой способ — маска по дате, как в уроке «Признаки для прогноза ряда»: `train = df.index < "2026-08-01"`, всё до августа — обучение, август (`~train`) — тест. Тест здесь — **хвост** ряда.

Тот же хвост можно отрезать привычной `train_test_split`, если задать долю, а не дату. Но по привычке из глав 6–7 тут легко ошибиться: `train_test_split` по умолчанию **перемешивает** строки.

::: tip Аналогия
Перемешанный тест — как экзамен, где билеты раздали заранее вперемешку с учебником: часть ответов студент видел накануне. Отложенный «хвост» ряда — экзамен по материалу следующей недели, которой ещё не было.
:::

Игрушечный пример: 10 часов с номерами 0…9, в тест отправляем 30 %, то есть 3 часа.

- С перемешиванием (`random_state=0`) в тест попадают часы 2, 8 и 4. В обучении остаются 9, 1, 6, 7, 3, 0, 5 — и часы 5, 6, 7, 9 идут **позже** тестового часа 4: модель учится на будущем относительно теста.
- С `shuffle=False` тест — последние три часа 7, 8, 9, обучение — 0…6. Всё обучение раньше теста, как в жизни.

::: figure ts-noshuffle
Десять часов, 30 % в тест. С перемешиванием тестовые часы 2, 8, 4 разбросаны по ряду, и пять обучающих часов идут позже начала теста. С `shuffle=False` тест — хвост ряда.
:::

```python
from sklearn.model_selection import train_test_split

hours = list(range(10))
print("перемешали:  ", train_test_split(hours, test_size=0.3, random_state=0))
print("по времени:  ", train_test_split(hours, test_size=0.3, shuffle=False))
```

Теперь на заказах. Строим те же признаки, что в `make_features(s)`, откладываем 20 % строк и сравниваем две оценки одной и той же модели:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
df["hour"], df["dow"] = df.index.hour, df.index.dayofweek
df["weekend"] = (df["dow"] >= 5).astype(int)
for k in (1, 24, 168):
    df[f"lag_{k}"] = s.shift(k)
df["roll_24"] = s.shift(1).rolling(24).mean()
df = df.dropna().sort_index()                       # строки строго по времени
X, y = df.drop(columns="y"), df["y"]

for shuffle in (True, False):
    kw = {"random_state": 0} if shuffle else {}
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, shuffle=shuffle, **kw)
    p = HistGradientBoostingRegressor(random_state=0).fit(X_tr, y_tr).predict(X_te)
    rmse = np.sqrt(((y_te - p) ** 2).mean())
    later = (X_tr.index > X_te.index.min()).sum()   # обучающих часов позже начала теста
    print(f"shuffle={shuffle}: тест с {X_te.index.min():%d.%m %H:%M}, "
          f"обучающих часов из «будущего»: {later}, RMSE = {rmse:.2f}")
```

**Что здесь происходит:**

- `df.dropna().sort_index()` — убираем строки без истории и на всякий случай сортируем по времени: `shuffle=False` берёт **последние строки таблицы**, а не последние даты. Если таблица не отсортирована, «хвост» окажется случайным.
- `train_test_split(..., shuffle=False)` — первые 80 % строк в обучение, последние 20 % в тест. `random_state` тут не нужен: случайности нет.
- `later` — сколько обучающих часов идут позже первого тестового часа. Для честной проверки по времени должно быть 0.

Маска по дате и `shuffle=False` дают одно и то же — хвост ряда; отличаются только тем, как задана граница. Маска удобнее, когда граница календарная («тест — август»), `shuffle=False` — когда нужна доля строк.

**Что получилось:** при перемешивании тест «размазан» по всему ряду с 8 марта, и 3397 обучающих часов лежат позже его начала. Модель видела соседние часы до и после каждого тестового — RMSE 3.60. При `shuffle=False` тест — последние 850 часов (с 27 июля), RMSE 4.29. Разница — это и есть оптимизм перемешивания: в работе модели предстоит прогнозировать будущее, и честная оценка — вторая.

::: predict
```python static
from sklearn.model_selection import train_test_split
a, b = train_test_split([10, 20, 30, 40, 50], test_size=0.4, shuffle=False)
print(a, b)
```

- [x] `[10, 20, 30] [40, 50]`
- `[40, 50] [10, 20, 30]`
- `[10, 30, 50] [20, 40]`

Почему: без перемешивания первые 60 % строк — обучение, последние 40 % — тест. Порядок внутри частей сохраняется.
:::

::: warn Типичные ошибки
- **`stratify=` вместе с `shuffle=False`.** Получите `ValueError: Stratified train/test split is not implemented for shuffle=False`: стратификация требует перемешивания. Для рядов она и не нужна — доли классов меняются во времени, и это часть задачи.
- **Таблица не по порядку.** После `concat` или `merge` строки могут перепутаться — тогда «хвост» будет случайным набором часов. Перед разбиением — `sort_index()` (или `sort_values("datetime")`) и проверка `X_tr.index.max() < X_te.index.min()`.
- **Лаги после разбиения.** Если считать `shift` отдельно в обучении и тесте, первые часы теста потеряют историю. Признаки строят на всём ряду, а делят уже готовую таблицу.
:::

{{practice: noshuffle}}

## Кросс-валидация по времени: TimeSeriesSplit

Одна отложенная часть — один экзамен: на августе модели могло повезти или не повезти. Когда сравнивают модели или подбирают параметры, нужна кросс-валидация. Обычный KFold для ряда не годится по той же причине, что и перемешивание: в обучение попадут часы после теста. Для рядов есть `TimeSeriesSplit`: каждый фолд обучается на прошлом и проверяется на следующем куске.

::: figure ts-split
`TimeSeriesSplit(n_splits=4)` на часовом ряду марта — августа: обучение растёт, тест всегда идёт после него.
:::

```python
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
for i, (tr, te) in enumerate(TimeSeriesSplit(n_splits=4).split(s)):
    print(f"фолд {i}: обучение до {s.index[tr[-1]]:%d.%m %H:%M}, тест {s.index[te[0]]:%d.%m %H:%M} — {s.index[te[-1]]:%d.%m %H:%M}")
```

**Что здесь происходит:**

- `TimeSeriesSplit(n_splits=4).split(s)` выдаёт пары массивов номеров строк: `tr` — обучение, `te` — тест.
- `s.index[tr[-1]]` — последний обучающий час, `s.index[te[0]]` и `s.index[te[-1]]` — границы теста. Печатаем с часом (`%d.%m %H:%M`): тест начинается в следующий час после обучения, например обучение до 06.04 19:00, тест с 06.04 20:00. Без часа даты совпали бы, и казалось бы, что фолды перекрываются.

Схема для 4 фолдов (каждый символ — кусок ряда, О — обучение, Т — тест, · — не используется):

```text
фолд 0:  О Т · · ·
фолд 1:  О О Т · ·
фолд 2:  О О О Т ·
фолд 3:  О О О О Т
```

Обучающая часть растёт от фолда к фолду, тест всегда идёт сразу после неё. В `cross_val_score` его передают как `cv=TimeSeriesSplit(5)`.

::: quiz
Почему для часового ряда нельзя взять обычный `KFold` с перемешиванием?

- [x] В обучение попадут часы, которые идут после тестовых: модель будет «знать будущее», и оценка выйдет оптимистичнее, чем в реальной работе
  > В реальности модель всегда обучена на прошлом и прогнозирует будущее — проверка должна повторять это.
- [ ] `KFold` не умеет работать с индексом-датой
  > Ему всё равно, какой индекс: он делит номера строк. Проблема не техническая, а в том, какие часы оказываются в обучении.
- [ ] Перемешивание перепутает лаги: в строке окажется чужой `lag_1`
  > Лаги считаются до разбиения и хранятся в своей строке; перемешивание строк их не меняет. Беда в том, что соседние, почти одинаковые часы оказываются по разные стороны от теста.
- [ ] `TimeSeriesSplit` просто работает быстрее
  > Скорость тут ни при чём: обучение на прошлом и проверка на будущем — вопрос честности оценки.
:::

{{practice: folds, tscv}}

## Практика

## task: noshuffle | Хвост ряда в тест | base

Таблица признаков `df = make_features(s)` готова. Отложите последние 20 % строк функцией `train_test_split(X, y, test_size=0.2, shuffle=False)`, обучите `HistGradientBoostingRegressor(random_state=0)` и сохраните `test_start` — время первой тестовой строки (`Timestamp`) и `rmse_time` — RMSE на тесте (3 знака). Затем повторите с перемешиванием (`random_state=0` вместо `shuffle=False`) — `rmse_shuffled` (3 знака). В `gap` сохраните, на сколько перемешанная оценка оптимистичнее: `rmse_time - rmse_shuffled` (3 знака).

### setup
```python
import pandas as pd
def make_features(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["lag_1"] = s.shift(1)
    df["lag_24"] = s.shift(24)
    df["lag_168"] = s.shift(168)
    df["roll_24"] = s.shift(1).rolling(24).mean()
    return df.dropna()
```

### starter
```python
# уже есть: make_features(s)
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import HistGradientBoostingRegressor as _H
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = make_features(s0); X0, y0 = d.drop(columns='y'), d['y']
def _r(**kw):
    a, b, c, e = _tts(X0, y0, test_size=0.2, **kw)
    return b.index.min(), round(float(_np.sqrt(((e - _H(random_state=0).fit(a, c).predict(b)) ** 2).mean())), 3)
t0, rt = _r(shuffle=False)
_, rs = _r(random_state=0)
assert _pd.Timestamp(need('test_start')) == t0, f'test_start = {need("test_start")}. Без перемешивания тест — последние 20 % строк; первая из них — X_test.index.min().'
assert close(need('rmse_time'), rt, 0.002), f'rmse_time = {need("rmse_time")}, а нужно {rt}. Модель — HistGradientBoostingRegressor(random_state=0), обучение на первых 80 %.'
assert close(need('rmse_shuffled'), rs, 0.002), f'rmse_shuffled = {need("rmse_shuffled")}, а нужно {rs}. Перемешанное разбиение — random_state=0 без shuffle=False.'
assert close(need('gap'), round(rt - rs, 3), 0.003), f'gap = {need("gap")}: разность rmse_time − rmse_shuffled.'
```

### hint
Два разбиения отличаются одним аргументом: `shuffle=False` в первом и `random_state=0` во втором. Всё остальное — одинаково.

### hint
`X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, shuffle=False)`; первая тестовая строка — `X_te.index.min()`; RMSE — `np.sqrt(((y_te - p) ** 2).mean())`.

### hint
Удобно завернуть обучение и оценку в функцию:

```python
def rmse_for(**kw):
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, **kw)
    p = HistGradientBoostingRegressor(random_state=0).fit(X_tr, y_tr).predict(X_te)
    return X_te.index.min(), round(float(np.sqrt(((y_te - p) ** 2).mean())), 3)
test_start, rmse_time = rmse_for(shuffle=False)
...
```

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

def rmse_for(**kw):
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, **kw)
    p = HistGradientBoostingRegressor(random_state=0).fit(X_tr, y_tr).predict(X_te)
    return X_te.index.min(), round(float(np.sqrt(((y_te - p) ** 2).mean())), 3)

test_start, rmse_time = rmse_for(shuffle=False)
_, rmse_shuffled = rmse_for(random_state=0)
gap = round(rmse_time - rmse_shuffled, 3)
print(test_start, rmse_time, rmse_shuffled, gap)
```

### explain
Тест по времени начинается 27 июля в 14:00 — это последние 850 часов. На нём RMSE около 4.29, а при перемешивании — около 3.60: оценка «улучшилась» почти на 0.7 заказа в час только из-за того, что модель видела соседние часы до и после каждого тестового. Если бы вы пообещали менеджеру точность 3.6, в августе получили бы 4.3 — и объяснять разницу пришлось бы задним числом. Заметить ошибку просто: у честного разбиения по времени `X_tr.index.max() < X_te.index.min()`.

## task: folds | Границы фолдов | warmup

Разбейте часовой ряд `s` с помощью `TimeSeriesSplit(n_splits=4)`. Сохраните `train_sizes` — список длин обучающей части в каждом фолде и `test_starts` — список первых тестовых часов (значения индекса `s`). Проверьте себя: каждый тест должен начинаться ровно через час после конца своего обучения.

### starter
```python
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import TimeSeriesSplit as _TS
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
sp = list(_TS(n_splits=4).split(s0))
ws = [int(len(a)) for a, b in sp]; wt = [s0.index[b[0]] for a, b in sp]
gs = [int(v) for v in need('train_sizes')]
assert gs == ws, f'train_sizes = {gs}, а нужно {ws}: длина tr в каждом фолде.'
gt = [_pd.Timestamp(v) for v in need('test_starts')]
assert gt == wt, f'test_starts = {[str(v) for v in gt]}, а нужно {[str(v) for v in wt]}: s.index[te[0]].'
```

### hint
Цикл `for tr, te in TimeSeriesSplit(n_splits=4).split(s):` — `tr` и `te` здесь номера строк.

### hint
Длина обучения — `len(tr)`, первый тестовый час — `s.index[te[0]]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

train_sizes, test_starts = [], []
for tr, te in TimeSeriesSplit(n_splits=4).split(s):
    train_sizes.append(len(tr))
    test_starts.append(s.index[te[0]])
print(train_sizes, test_starts)
```

### explain
Обучение растёт на одинаковый шаг — 884, 1767, 2650, 3533 часа, — а тесты по 883 часа идут встык друг за другом: 6 апреля 20:00, 13 мая 15:00, 19 июня 10:00, 26 июля 05:00. Последний тест заканчивается в последний час ряда. Границы попадают на середину дня, потому что `TimeSeriesSplit` делит номера строк, а не календарь; если нужны тесты ровно по месяцам, их задают масками по дате.

## task: tscv | Кросс-валидация по времени | plus

Оцените бустинг на всех признаках `make_features(s)` кросс-валидацией `TimeSeriesSplit(n_splits=5)` по RMSE (`scoring="neg_root_mean_squared_error"`). Сохраните `scores` — RMSE на фолдах (положительные числа, 2 знака) и `mean_rmse` (3 знака). Затем посчитайте то же с обычным `KFold(5, shuffle=True, random_state=0)` — `mean_rmse_kfold` (3 знака).

### setup
```python
import pandas as pd
def make_features(s):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["lag_1"] = s.shift(1)
    df["lag_24"] = s.shift(24)
    df["lag_168"] = s.shift(168)
    df["roll_24"] = s.shift(1).rolling(24).mean()
    return df.dropna()
```

### starter
```python
# уже есть: make_features(s)
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit, KFold, cross_val_score
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

```

### check
```python
import pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.model_selection import TimeSeriesSplit as _TS, KFold as _KF, cross_val_score as _cvs
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = make_features(s0); X0, y0 = d.drop(columns='y'), d['y']
a = -_cvs(_H(random_state=0), X0, y0, cv=_TS(n_splits=5), scoring='neg_root_mean_squared_error')
b = -_cvs(_H(random_state=0), X0, y0, cv=_KF(5, shuffle=True, random_state=0), scoring='neg_root_mean_squared_error')
assert [round(float(v), 2) for v in need('scores')] == [round(float(v), 2) for v in a], f'scores = {need("scores")}, а нужно {a.round(2)}.'
assert close(need('mean_rmse'), round(a.mean(), 3), 0.002), f'mean_rmse = {need("mean_rmse")}.'
assert close(need('mean_rmse_kfold'), round(b.mean(), 3), 0.002), f'mean_rmse_kfold = {need("mean_rmse_kfold")}.'
```

### hint
Разбиение задаётся объектом: `cv=TimeSeriesSplit(n_splits=5)`.

### hint
`cross_val_score` возвращает отрицательные значения для `neg_...` — поменяйте знак.

### solution
```python
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit, KFold, cross_val_score
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

raw = -cross_val_score(HistGradientBoostingRegressor(random_state=0), X, y,
                       cv=TimeSeriesSplit(n_splits=5), scoring="neg_root_mean_squared_error")
scores = [round(float(v), 2) for v in raw]
mean_rmse = round(raw.mean(), 3)
kf = -cross_val_score(HistGradientBoostingRegressor(random_state=0), X, y,
                      cv=KFold(5, shuffle=True, random_state=0), scoring="neg_root_mean_squared_error")
mean_rmse_kfold = round(kf.mean(), 3)
```

### explain
Обычный KFold даёт чуть более оптимистичную оценку: модель обучается и на часах после проверяемых, а соседние часы похожи. Разница здесь небольшая, но на рядах с сильным трендом или сменой режима она бывает огромной. По времени — всегда честнее.
