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

- С перемешиванием (`random_state=0`) в тест попадают часы 2, 8 и 4. В обучении остаются 9, 1, 6, 7, 3, 0, 5 — и пять из них (3, 5, 6, 7, 9) идут **позже** первого тестового часа 2: модель учится на будущем относительно теста.
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

**Что получилось:** при перемешивании тест «размазан» по всему ряду и начинается 8 марта в 01:00 — со второй строки таблицы. Поэтому позже его начала лежит практически всё обучение: 3397 часов из 3398. Модель видела соседние часы до и после каждого тестового — RMSE 3.60. При `shuffle=False` тест — последние 850 часов (с 27 июля), RMSE 4.29.

Не вся разница 0.7 — оптимизм перемешивания. Тесты тут разные: перемешанный — весь март–август, честный — конец июля и август, где заказов больше (в среднем 10.6 в час против 8.5 в обучении) и шум крупнее. Часть разницы — просто более трудный период. Если сравнить на одном и том же периоде, разрыв меньше: это задачи «Тот же период — другая оценка» и «Кросс-валидация по времени» (там около 0.3). Но и он не ноль, а в работе модели предстоит прогнозировать будущее — честная оценка вторая.

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

{{practice: noshuffle, check-order, same-period}}

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

{{practice: folds, tscv, month-folds}}

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
Тест по времени начинается 27 июля в 14:00 — это последние 850 часов. На нём RMSE около 4.29, а при перемешивании — около 3.60: оценка «улучшилась» почти на 0.7 заказа в час. Часть этого — оттого, что модель видела соседние часы до и после каждого тестового, а часть — оттого, что август труднее: уровень и шум выше. Сколько приходится на каждую причину, разбирает задача «Тот же период — другая оценка». Если бы вы пообещали менеджеру точность 3.6, в августе получили бы 4.3 — и объяснять разницу пришлось бы задним числом. Заметить ошибку просто: у честного разбиения по времени `X_tr.index.max() < X_te.index.min()`.

## task: check-order | Проверка честности разбиения | warmup

Напишите функцию `is_time_split(X_tr, X_te)`: она возвращает `True`, если все обучающие строки раньше всех тестовых (по индексу-времени), иначе `False`. Примените её к двум разбиениям таблицы `X` с `test_size=0.2`: по времени (`shuffle=False`) — результат в `honest_ok`, с перемешиванием (`random_state=0`) — в `shuffled_ok`. В `n_later` сохраните, сколько обучающих строк перемешанного разбиения идут позже его первой тестовой строки.

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
from sklearn.model_selection import train_test_split
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

def is_time_split(X_tr, X_te):
    ...

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
f = need('is_time_split')
_i = _pd.date_range('2026-01-01', periods=6, freq='h')
_a = _pd.DataFrame({'v': range(6)}, index=_i)
assert f(_a.iloc[:4], _a.iloc[4:]) is not None, 'is_time_split ничего не возвращает: нужен return.'
assert bool(f(_a.iloc[:4], _a.iloc[4:])) is True, 'Обучение — первые 4 часа, тест — последние 2: функция должна вернуть True.'
assert bool(f(_a.iloc[[0, 1, 5]], _a.iloc[[2, 3, 4]])) is False, 'Час 05:00 в обучении позже тестовых 02:00–04:00: функция должна вернуть False.'
assert bool(f(_a.iloc[[3, 1, 0]], _a.iloc[[5, 4]])) is True, 'Порядок строк внутри частей не важен — сравнивайте максимум обучения и минимум теста.'
d = make_features(need('s')); X0 = d.drop(columns='y')
a, b = _tts(X0, test_size=0.2, random_state=0)
nl = int((a.index > b.index.min()).sum())
assert need('honest_ok') == True, f'honest_ok = {need("honest_ok")}: разбиение с shuffle=False честное.'
assert need('shuffled_ok') == False, f'shuffled_ok = {need("shuffled_ok")}: перемешанное разбиение кладёт будущее в обучение.'
assert int(need('n_later')) == nl, f'n_later = {need("n_later")}, а нужно {nl}: (X_tr.index > X_te.index.min()).sum() для перемешанного разбиения.'
```

### hint
Все обучающие строки раньше всех тестовых — значит, самая поздняя обучающая раньше самой ранней тестовой: `X_tr.index.max() < X_te.index.min()`.

### hint
Два разбиения: `train_test_split(X, test_size=0.2, shuffle=False)` и `train_test_split(X, test_size=0.2, random_state=0)` — каждое возвращает пару `X_tr, X_te`. Сравнение даёт `numpy.bool_`; для печати и проверки удобно обернуть в `bool(...)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

def is_time_split(X_tr, X_te):
    return bool(X_tr.index.max() < X_te.index.min())

X_tr, X_te = train_test_split(X, test_size=0.2, shuffle=False)
honest_ok = is_time_split(X_tr, X_te)
X_tr_s, X_te_s = train_test_split(X, test_size=0.2, random_state=0)
shuffled_ok = is_time_split(X_tr_s, X_te_s)
n_later = int((X_tr_s.index > X_te_s.index.min()).sum())
print(honest_ok, shuffled_ok, n_later, len(X_tr_s))
```

### explain
Честное разбиение проходит проверку, перемешанное — нет. В перемешанном первая тестовая строка — 8 марта 01:00, вторая строка таблицы, поэтому позже неё 3397 обучающих строк из 3398: почти всё обучение. Такую проверку стоит ставить в каждый конвейер с рядом одной строкой `assert is_time_split(X_tr, X_te)` — она ловит и перемешивание, и неотсортированную таблицу.

## task: same-period | Тот же период — другая оценка | plus

Разница 4.29 против 3.60 в задаче «Хвост ряда в тест» смешивает две причины: перемешивание и более трудный конец лета. Разделите их. Обучите бустинг `HistGradientBoostingRegressor(random_state=0)` на двух разбиениях `test_size=0.2` — по времени (`shuffle=False`) и перемешанном (`random_state=0`). Сохраните `rmse_time` и `rmse_shuffled` (3 знака) как раньше. Затем у перемешанной модели возьмите только те её тестовые строки, что попадают в период честного теста (не раньше его первой строки): `n_tail` — их число, `rmse_shuffled_tail` — RMSE на них (3 знака). Наконец, `part_period = rmse_shuffled_tail - rmse_shuffled` — вклад трудного периода и `part_shuffle = rmse_time - rmse_shuffled_tail` — вклад перемешивания (оба 3 знака).

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
d = make_features(need('s')); X0, y0 = d.drop(columns='y'), d['y']
_r = lambda a, b: float(_np.sqrt(((a - b) ** 2).mean()))
a, b, c, e = _tts(X0, y0, test_size=0.2, shuffle=False); rt = _r(e, _H(random_state=0).fit(a, c).predict(b)); t0 = b.index.min()
a, b, c, e = _tts(X0, y0, test_size=0.2, random_state=0); pb = _H(random_state=0).fit(a, c).predict(b); rs = _r(e, pb)
m = b.index >= t0; rtail = _r(e[m], pb[m])
assert close(need('rmse_time'), round(rt, 3), 0.002) and close(need('rmse_shuffled'), round(rs, 3), 0.002), f'rmse_time, rmse_shuffled = {need("rmse_time")}, {need("rmse_shuffled")}, а нужно {round(rt, 3)}, {round(rs, 3)}.'
assert int(need('n_tail')) == int(m.sum()), f'n_tail = {need("n_tail")}, а нужно {int(m.sum())}: тестовые строки перемешанного разбиения с индексом >= первой строки честного теста.'
assert close(need('rmse_shuffled_tail'), round(rtail, 3), 0.002), f'rmse_shuffled_tail = {need("rmse_shuffled_tail")}, а нужно {round(rtail, 3)}.'
assert close(need('part_period'), round(rtail - rs, 3), 0.004) and close(need('part_shuffle'), round(rt - rtail, 3), 0.004), f'part_period, part_shuffle = {need("part_period")}, {need("part_shuffle")}, а нужно {round(rtail - rs, 3)}, {round(rt - rtail, 3)}.'
```

### hint
Предсказания перемешанной модели сохраните в переменную, а не только RMSE: понадобятся строки по маске. Маска периода — `X_te_s.index >= test_start`, где `test_start = X_te.index.min()` у честного разбиения.

### hint
RMSE на части строк: `np.sqrt(((y_te_s[mask] - p_s[mask]) ** 2).mean())`. Маска — массив `True/False`, им можно отбирать и Series, и массив предсказаний.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

def rmse(a, b):
    return float(np.sqrt(((a - b) ** 2).mean()))

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, shuffle=False)
p = HistGradientBoostingRegressor(random_state=0).fit(X_tr, y_tr).predict(X_te)
rmse_time = round(rmse(y_te, p), 3)
test_start = X_te.index.min()

X_tr_s, X_te_s, y_tr_s, y_te_s = train_test_split(X, y, test_size=0.2, random_state=0)
p_s = HistGradientBoostingRegressor(random_state=0).fit(X_tr_s, y_tr_s).predict(X_te_s)
rmse_shuffled = round(rmse(y_te_s, p_s), 3)

tail = X_te_s.index >= test_start
n_tail = int(tail.sum())
rmse_shuffled_tail = round(rmse(y_te_s[tail], p_s[tail]), 3)
part_period = round(rmse_shuffled_tail - rmse_shuffled, 3)
part_shuffle = round(rmse_time - rmse_shuffled_tail, 3)
print(rmse_time, rmse_shuffled, n_tail, rmse_shuffled_tail, part_period, part_shuffle)
```

### explain
На тех же 163 часах конца июля — августа перемешанная модель ошибается на 3.825, а не на 3.597, как на всём своём тесте: примерно 0.23 из разницы — это трудный период, а не перемешивание. Оставшиеся около 0.47 — сам оптимизм перемешивания: на одном и том же периоде честная модель ошибается на 4.293, а подсмотревшая соседние часы — на 3.825. Вывод тот же, что в теории: перемешивание завышает качество, но сравнивать оценки надо на одинаковом периоде, иначе разница смешивает две причины.

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
Обычный KFold даёт более оптимистичную оценку: около 3.73 против 4.03 у `TimeSeriesSplit`, разрыв около 0.3. Модель обучается и на часах после проверяемых, а соседние часы похожи. Заметьте и рост ошибки по фолдам: последний (4.28) хуже первого (4.01) — поздние фолды приходятся на период с бо́льшим уровнем заказов. На рядах с сильным трендом или сменой режима разрыв между KFold и проверкой по времени бывает огромным. По времени — всегда честнее.

## task: month-folds | Тесты по месяцам | plus

`TimeSeriesSplit` режет ряд по номерам строк, а отчитываться удобнее по месяцам. Сделайте проверку «по месяцам» вручную: для каждого из месяцев июнь, июль, август обучите `HistGradientBoostingRegressor(random_state=0)` на всех строках таблицы до начала месяца и проверьте на строках этого месяца. Сохраните словари с ключами `"06"`, `"07"`, `"08"`: `month_rmse` — RMSE (3 знака), `month_mean` — среднее число заказов в час в тесте (2 знака) и `rel_error` — отношение RMSE к среднему (3 знака).

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
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
d = make_features(need('s')); X0, y0 = d.drop(columns='y'), d['y']
w_r, w_m, w_e = {}, {}, {}
for k in ('06', '07', '08'):
    st = _pd.Timestamp(f'2026-{k}-01'); en = st + _pd.offsets.MonthBegin(1)
    tr = X0.index < st; te = (X0.index >= st) & (X0.index < en)
    p = _H(random_state=0).fit(X0[tr], y0[tr]).predict(X0[te]); r = float(_np.sqrt(((y0[te] - p) ** 2).mean()))
    w_r[k], w_m[k], w_e[k] = round(r, 3), round(float(y0[te].mean()), 2), round(r / float(y0[te].mean()), 3)
g_r, g_m, g_e = need('month_rmse', dict), need('month_mean', dict), need('rel_error', dict)
assert sorted(g_r) == ['06', '07', '08'], f'Ключи month_rmse: {sorted(g_r)}, а нужны "06", "07", "08".'
assert all(close(g_m[k], w_m[k], 0.006) for k in w_m), f'month_mean = {g_m}, а нужно {w_m}: среднее y в строках месяца.'
assert all(close(g_r[k], w_r[k], 0.002) for k in w_r), f'month_rmse = {g_r}, а нужно {w_r}: обучение — все строки до 1-го числа месяца, тест — строки месяца.'
assert all(close(g_e[k], w_e[k], 0.002) for k in w_e), f'rel_error = {g_e}, а нужно {w_e}.'
```

### hint
Границы месяца: `start = pd.Timestamp("2026-06-01")`, конец — `start + pd.offsets.MonthBegin(1)` (1 июля). Маски: `train = X.index < start`, `test = (X.index >= start) & (X.index < end)`.

### hint
Цикл по `["06", "07", "08"]`, внутри — `pd.Timestamp(f"2026-{m}-01")`, обучение на `X[train]`, предсказание на `X[test]` и три числа в три словаря.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
X, y = df.drop(columns="y"), df["y"]

month_rmse, month_mean, rel_error = {}, {}, {}
for m in ["06", "07", "08"]:
    start = pd.Timestamp(f"2026-{m}-01")
    end = start + pd.offsets.MonthBegin(1)
    train = X.index < start
    test = (X.index >= start) & (X.index < end)
    p = HistGradientBoostingRegressor(random_state=0).fit(X[train], y[train]).predict(X[test])
    r = float(np.sqrt(((y[test] - p) ** 2).mean()))
    month_rmse[m] = round(r, 3)
    month_mean[m] = round(float(y[test].mean()), 2)
    rel_error[m] = round(r / float(y[test].mean()), 3)
print(month_rmse, month_mean, rel_error)
```

### explain
RMSE растёт от месяца к месяцу: 3.963, 4.142, 4.256 — хотя обучение каждый раз длиннее. Но и заказов больше: 8.95, 9.73, 10.63 в час. Относительная ошибка, наоборот, падает: 0.443, 0.426, 0.400. Модель не становится хуже — растёт масштаб ряда, а с ним и ошибка в заказах. Это та же поправка, что в теории: август «труднее» в абсолютных числах, поэтому сравнивать RMSE разных периодов напрямую нельзя.
