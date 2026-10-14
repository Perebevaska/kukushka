---
title: Признаки для прогноза ряда
files: [app_orders.csv]
lead: "Чтобы предсказать заказы в следующий час обычной моделью — линейной регрессией или бустингом, — ряд превращают в таблицу признаков: календарь, значения в прошлом (лаги), скользящие средние. Главное правило — в признаках только то, что известно на момент прогноза. Нарушить его здесь проще, чем кажется, поэтому в конце урока пишем автоматический тест на утечку. Как честно делить ряд на обучение и тест — в следующем уроке."
recap:
  - "Календарные признаки: час, день недели, выходной, праздник, акция — известны заранее на любой срок."
  - "Лаги: `s.shift(k)` — значение k шагов назад. Для часовых заказов полезны лаги 1, 24 и 168."
  - "Скользящие статистики считают по прошлому: `s.shift(1).rolling(24).mean()`. Без `shift(1)` в окно попадает текущее значение — утечка."
  - "Строки с пропусками в начале ряда (нет истории для лагов) удаляют."
  - "Подозрительно хорошее качество на временном ряде — почти всегда признак из будущего."
  - "Тест на утечку: испортить ответ в часе t и посмотреть, какие признаки строки t изменились. Изменился — значит, видит ответ."
  - "Для проверки в этом уроке — маска по дате: обучение до августа, тест — август. Подробно о проверке по времени — в следующем уроке."
---

## Ряд как таблица

Модели из глав 6–10 работают с таблицей «признаки → ответ». Чтобы применить их к ряду, каждый час превращают в строку: ответ — заказы в этот час, признаки — то, что мы знаем к началу этого часа.

Сначала на пяти часах, чтобы увидеть, как ряд становится таблицей:

| время | y (ответ) | hour | lag_1 (час назад) | lag_2 (два часа назад) |
|---|---|---|---|---|
| 08:00 | 12 | 8 | — | — |
| 09:00 | 15 | 9 | 12 | — |
| 10:00 | 11 | 10 | 15 | 12 |
| 11:00 | 13 | 11 | 11 | 15 |
| 12:00 | 18 | 12 | 13 | 11 |

::: figure ts-to-table
Та же таблица со стрелками: каждое значение ряда «спускается» по диагонали — на строку ниже в `lag_1`, на две строки ниже в `lag_2`. У первых двух строк истории нет, их удаляют.
:::

::: tip Аналогия
Это как дневник кофейни, где на каждой странице выписаны вчерашние и позавчерашние продажи: чтобы угадать сегодняшние, не нужно листать назад — всё нужное уже на странице. Первые страницы дневника неполные: «вчера» для них ещё не было.
:::

Каждая строка — «что мы знали к началу часа» и «что случилось». Первые строки без лагов (нечего брать из прошлого) удаляют. Теперь то же на всём ряду:

```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

df = pd.DataFrame({"y": s})
df["hour"] = df.index.hour
df["dow"] = df.index.dayofweek
df["weekend"] = (df["dow"] >= 5).astype(int)
df["lag_1"] = s.shift(1)          # час назад
df["lag_24"] = s.shift(24)        # это же время вчера
df["lag_168"] = s.shift(168)      # это же время неделю назад
df["roll_24"] = s.shift(1).rolling(24).mean()   # среднее за предыдущие сутки
print(df.iloc[166:170])
print("пропусков в начале:", df.isna().any(axis=1).sum())
df = df.dropna()
```

**Что здесь происходит:**

- `pd.DataFrame({"y": s})` — таблица с одним столбцом-ответом и временным индексом.
- `df.index.hour`, `df.index.dayofweek` — календарные признаки берутся прямо из индекса.
- `(df["dow"] >= 5).astype(int)` — флаг выходного: 1 для субботы и воскресенья.
- `s.shift(k)` — лаг: значение ряда `k` часов назад.
- `s.shift(1).rolling(24).mean()` — среднее за 24 часа **до** текущего: сначала сдвиг, потом окно (почему так — раздел про утечку ниже).
- `df.isna().any(axis=1)` — строки, где пропущен хотя бы один признак; `dropna()` их удаляет.

Первые 168 строк (неделя) без лага 168 — их удаляем. Это нормальная плата за «память» модели.

{{practice: make-features}}

## Календарь и лаги

Признаки делятся на две группы, и у них разный смысл:

- **календарь** (час, день недели, выходной, акция) — известен на любой срок вперёд. Описывает регулярный ритм;
- **лаги и скользящие средние** — что было недавно. Описывают текущий уровень: если приложение сегодня в ударе (или в сбое), лаги это видят.

::: warn Лаги и горизонт прогноза
В этом уроке прогноз — на **один час вперёд**: в 11:59 мы знаем всё до 11:00 включительно и предсказываем 12:00. Поэтому лаг 1 здесь честен. Если прогноз нужен на сутки или на неделю вперёд (например, для графика смен), лага 1 в момент прогноза ещё не будет: честны только лаги не короче горизонта. Как считать горизонт и какие лаги тогда остаются — урок «Прогноз: ориентиры, горизонт и метрики».
:::

Сравним бустинг на разных наборах признаков. Обучение — март–июль, тест — август.

| признаки | RMSE на августе |
|---|---|
| только календарь | ≈ 4.60 |
| + лаги 1, 24, 168 | ≈ 4.33 |
| + среднее за сутки | ≈ 4.26 |

Как получены эти числа — в задаче «Какие признаки помогают»: одна и та же модель (`HistGradientBoostingRegressor`), одно и то же разбиение по времени, меняется только список столбцов. Числа посчитаны в sklearn 1.9; в другой версии бустинг может дать разницу в третьем знаке, порядок наборов от этого не меняется.

RMSE — корень из средней квадратичной ошибки (глава 6), в заказах в час. Календарь даёт основное, лаги добавляют знание о текущем уровне. У линейной регрессии без лагов дела совсем плохи (около 7.8): «час» для неё — просто число, и суточный профиль с тремя пиками прямой не описать. С теми же лагами, что у бустинга в таблице, она подтягивается до 4.5: лаг 24 и лаг 168 сами несут этот профиль. Другой способ помочь линейной модели — закодировать час категорией; он разобран в задаче «Час как число и как категория».

::: predict
```python static
import pandas as pd
s = pd.Series([5, 7, 9, 11])
print(s.shift(1).rolling(2).mean().tolist())
```

- `[nan, 6.0, 8.0, 10.0]`
- [x] `[nan, nan, 6.0, 8.0]`
- `[6.0, 8.0, 10.0, nan]`

Почему: `shift(1)` даёт `[nan, 5, 7, 9]`, а окно из двух значений по нему — `[nan, nan, 6, 8]`. Для третьего часа среднее считается по первому и второму — по прошлому.
:::

{{practice: calendar, p-lags, feature-sets, onehot-hours, promo-feature}}

## Утечка через скользящее окно

Самая частая ошибка: `s.rolling(24).mean()` **без** `shift(1)`. Окно заканчивается на текущем значении — то есть в признак «среднее за сутки» попадают заказы того самого часа, который мы предсказываем.

::: tip Аналогия
Это как предсказывать выручку кофейни за вечер по «средней выручке за сегодня», в которую уже вписан и сам вечер: прогноз выходит отличным, потому что ответ частично лежит в признаке. Днём, когда прогноз действительно нужен, такого числа ещё нет. В нашем окне подсказка слабее: текущий час — лишь одно значение из 24, поэтому «улучшение» скромное, но это всё равно подглядывание.
:::

Разберём на четырёх часах из «Предскажите вывод» выше — 5, 7, 9, 11 заказов в 09:00…12:00 — и окне из двух часов. Предсказываем 12:00. Честный признак `s.shift(1).rolling(2).mean()` в строке 12:00 — (7 + 9) / 2 = 8: только прошлое. Признак без сдвига `s.rolling(2).mean()` — (9 + 11) / 2 = 10: в нём уже сидит ответ 11.

::: figure ts-roll-shift
Окно признака для строки 12:00. Со сдвигом оно заканчивается в 11:00 — до момента прогноза. Без сдвига оно захватывает сам 12:00, то есть ответ.
:::

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

def make(s, leak):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    for k in (1, 24, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll_24"] = s.rolling(24).mean() if leak else s.shift(1).rolling(24).mean()
    return df.dropna()

for leak in (False, True):
    df = make(s, leak)
    train = df.index < "2026-08-01"
    X, y = df.drop(columns="y"), df["y"]
    p = HistGradientBoostingRegressor(random_state=0).fit(X[train], y[train]).predict(X[~train])
    print("с утечкой" if leak else "честно   ", "RMSE:", round(float(np.sqrt(((y[~train] - p) ** 2).mean())), 3))
```

**Что здесь происходит:**

- `make(s, leak)` строит одну и ту же таблицу признаков; отличается только `roll_24`: с `leak=True` окно включает текущий час.
- `train = df.index < "2026-08-01"` — маска обучающих строк: всё до августа. Тест — август (`~train`).
- RMSE считается вручную: корень из среднего квадрата ошибок.

С утечкой RMSE заметно лучше — и это обман: в реальной работе в момент прогноза текущего часа ещё нет. Утечка небольшая (один час из 24 в окне), поэтому и «улучшение» скромное. Если бы окно было короче, например 3 часа, разрыв был бы огромным.

::: warn
Правило для любого признака временного ряда: для строки «время t» в нём могут быть только данные до t (не включая). Проверка на пальцах — представьте, что сейчас 11:59 и вы считаете признаки для 12:00. Всё, что нельзя посчитать в 11:59, — утечка. Это правило для прогноза на час вперёд; при прогнозе на сутки «сейчас» отодвигается на сутки назад, и лаги короче суток тоже становятся утечкой.
:::

::: quiz
Признак `roll_24 = s.rolling(24).mean()` без сдвига. Чем он плох?

- [x] Окно включает текущий час — то самое значение, которое модель должна предсказать
  > Правильно: `s.shift(1).rolling(24).mean()` — среднее только по прошлым часам.
- [ ] Окно 24 слишком короткое
  > Длина окна — вопрос качества, а утечка от длины не зависит.
- [ ] В первых 23 строках пропуски
  > Их просто отбрасывают — это не проблема.
- [ ] Скользящие средние нельзя использовать как признаки
  > Можно, если окно заканчивается до момента прогноза.
:::

{{practice: leak-check}}

## Разберём вместе: тест на утечку для любого признака

Проверка «на пальцах» из предупреждения выше легко превращается в код. Идея: если признак для часа t честный, он не должен меняться, когда мы **испортим** значение ряда в час t. Испортим ряд в одной точке и посмотрим, у каких признаков изменилось значение в этой же строке.

```python
import pandas as pd

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

def features(s):
    df = pd.DataFrame(index=s.index)
    df["lag_1"] = s.shift(1)
    df["roll_24_honest"] = s.shift(1).rolling(24).mean()
    df["roll_24_leak"] = s.rolling(24).mean()
    df["diff_next"] = s.shift(-1) - s          # «на сколько изменится к следующему часу»
    return df

t = pd.Timestamp("2026-07-15 12:00")
spoiled = s.copy()
spoiled[t] = spoiled[t] + 1000                  # портим только час t
changed = features(spoiled).loc[t] != features(s).loc[t]
print(changed)
```

**Что здесь происходит:**

- `spoiled[t] + 1000` — меняем ответ в одном часе на заведомо невозможное значение.
- Строим признаки по исходному и по испорченному ряду и сравниваем строку `t`.
- Если признак строки `t` изменился, значит, он «видит» ответ этого часа — это утечка.

::: figure ts-leak-test
Идея теста: испортили ответ одного часа — и смотрим, какие признаки той же строки «почувствовали» это. Почувствовал — значит, видит ответ.
:::

**Что получилось:** лаг и честное среднее не изменились, а `roll_24_leak` и `diff_next` — изменились: оба используют ответ часа t (второй — даже будущий час). Такой тест стоит прогонять для любой новой функции признаков — он ловит утечки, которые не видны глазами.

{{practice: leak-test}}

## Практика

## task: calendar | Календарные признаки | warmup

Соберите DataFrame `df` со столбцами `y` (заказы), `hour`, `dow`, `weekend` (1 для субботы и воскресенья). Сохраните `weekend_share` — долю выходных часов (3 знака).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = need('df', _pd.DataFrame)
assert {'y', 'hour', 'dow', 'weekend'} <= set(d.columns), f'Столбцы df: {list(d.columns)}.'
assert (d['hour'].values == s0.index.hour).all() and (d['dow'].values == s0.index.dayofweek).all(), 'hour и dow — из индекса: .index.hour, .index.dayofweek.'
assert close(need('weekend_share'), round((s0.index.dayofweek >= 5).mean(), 3)), f'weekend_share = {need("weekend_share")}.'
```

### hint
`df = pd.DataFrame({"y": s})`, затем `df["hour"] = df.index.hour` и т. д.

### hint
Выходной — `(df.index.dayofweek >= 5).astype(int)`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
df["hour"] = df.index.hour
df["dow"] = df.index.dayofweek
df["weekend"] = (df["dow"] >= 5).astype(int)
weekend_share = round(df["weekend"].mean(), 3)
```

## task: p-lags | Лаги | warmup

Соберите код, который добавляет лаги 1 и 24 и печатает, сколько строк остаётся после удаления пропусков.

### parsons
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
df["lag_1"] = s.shift(1)
df["lag_24"] = s.shift(24)
df = df.dropna()
print(len(df))
```

### check
```python
assert _lines == ['4392'], f'Сейчас: {_lines}.'
```

### hint
Лаги — до удаления пропусков.

### hint
Лаг k — `s.shift(k)`; строки с пропусками удаляет `dropna()`.

## task: leak-check | Найти утечку | warmup

Ниже — четыре признака для строки «час t». Сохраните список `leaky` — названия тех, в которые попадают данные часа t или позже.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
features = {
    "a": s.shift(1),
    "b": s.rolling(3).mean(),
    "c": s.shift(1).rolling(3).mean(),
    "d": s.shift(-1),
}

```

### check
```python
assert sorted(need('leaky')) == ['b', 'd'], f'leaky = {need("leaky")}. b включает текущий час, d — следующий.'
```

### hint
Для каждого признака задайте вопрос: можно ли его посчитать в 11:59 для строки 12:00?

### hint
`rolling(3)` без сдвига включает текущее значение, `shift(-1)` — это значение следующего часа.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
features = {
    "a": s.shift(1),
    "b": s.rolling(3).mean(),
    "c": s.shift(1).rolling(3).mean(),
    "d": s.shift(-1),
}
leaky = ["b", "d"]
```

## task: make-features | Функция признаков | base

Напишите функцию `make_features(s)`, которая возвращает DataFrame без пропусков со столбцами: `y`, `hour`, `dow`, `weekend`, `lag_1`, `lag_24`, `lag_168`, `roll_24` (среднее за предыдущие 24 часа). Сохраните `df = make_features(s)` и `first_ts` — время первой строки.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = need('make_features')(s0)
cols = ['y', 'hour', 'dow', 'weekend', 'lag_1', 'lag_24', 'lag_168', 'roll_24']
assert set(cols) <= set(d.columns), f'Столбцы: {list(d.columns)}.'
assert not d.isna().any().any(), 'В результате не должно быть пропусков — dropna().'
t = d.index[0]
assert t == s0.index[168], f'Первая строка должна быть {s0.index[168]} (после недели истории), а у вас {t}.'
assert close(d.loc[t, 'roll_24'], s0.iloc[144:168].mean()), 'roll_24 — среднее 24 часов ДО текущего: s.shift(1).rolling(24).mean().'
assert d.loc[t, 'lag_168'] == s0.iloc[0], 'lag_168 — значение неделю назад: s.shift(168).'
assert need('first_ts') == s0.index[168], f'first_ts = {need("first_ts")}.'
```

### hint
Код из начала теории, обёрнутый в функцию; в конце — `return df.dropna()`.

### hint
Функция должна строить признаки по переданному ряду, а не по глобальной переменной: используйте её параметр внутри.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

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

df = make_features(s)
first_ts = df.index[0]
```

### explain
Функция строит признаки по ряду, который ей передали, поэтому её можно вызвать и для другой кофейни, и для новых данных без правок. Первая строка — 8 марта: самому длинному лагу (`lag_168`, неделя назад) нужно 168 часов истории, и `dropna()` отрезает первые 7 суток ряда, который начинается 1 марта. `roll_24` считается от `s.shift(1)`, то есть только по прошлым часам: среднее, включающее текущий час, было бы утечкой ответа в признаки.

## task: feature-sets | Какие признаки помогают | base

С помощью `make_features` из заготовки сравните `HistGradientBoostingRegressor(random_state=0)` на трёх наборах признаков: только календарь (`hour`, `dow`, `weekend`), календарь + лаги (`lag_1`, `lag_24`, `lag_168`), всё. Обучение — до 2026-08-01, тест — август. Сохраните словарь `rmse` (`{"календарь": ..., "лаги": ..., "всё": ...}`, 3 знака).

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
# уже есть: make_features(s) из прошлой задачи
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
train = df.index < "2026-08-01"

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = make_features(s0); tr = d.index < '2026-08-01'; y = d['y']
sets = {'календарь': ['hour', 'dow', 'weekend'], 'лаги': ['hour', 'dow', 'weekend', 'lag_1', 'lag_24', 'lag_168'],
        'всё': ['hour', 'dow', 'weekend', 'lag_1', 'lag_24', 'lag_168', 'roll_24']}
got = need('rmse', dict)
for k, c in sets.items():
    p = _H(random_state=0).fit(d.loc[tr, c], y[tr]).predict(d.loc[~tr, c])
    w = round(float(_np.sqrt(((y[~tr] - p) ** 2).mean())), 3)
    assert k in got and close(got[k], w, 0.002), f'rmse[{k!r}] = {got.get(k)}, а нужно {w}.'
```

### hint
Сначала таблица признаков и разбиение по дате (`df.index < "2026-08-01"`), потом цикл по наборам столбцов.

### hint
Словарь наборов столбцов и цикл; RMSE: `np.sqrt(((y_test - p) ** 2).mean())`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make_features(s)
train = df.index < "2026-08-01"

sets = {
    "календарь": ["hour", "dow", "weekend"],
    "лаги": ["hour", "dow", "weekend", "lag_1", "lag_24", "lag_168"],
    "всё": ["hour", "dow", "weekend", "lag_1", "lag_24", "lag_168", "roll_24"],
}
y = df["y"]
rmse = {}
for name, cols in sets.items():
    p = HistGradientBoostingRegressor(random_state=0).fit(df.loc[train, cols], y[train]).predict(df.loc[~train, cols])
    rmse[name] = round(float(np.sqrt(((y[~train] - p) ** 2).mean())), 3)
```

### explain
Календарь знает типичный профиль (час, день недели), но не знает, какая сейчас неделя — удачная или нет: RMSE ≈ 4.596. Лаги добавляют свежую информацию о самом ряде, и ошибка падает до ≈ 4.332. Скользящее среднее за сутки сглаживает шум отдельных часов и даёт ещё немного: ≈ 4.256 (числа из sklearn 1.9; в другой версии третий знак может отличаться — проверка сравнивает с тем, что посчитала ваша среда). Сравнение наборов на одном тесте — честный способ решить, нужен ли признак: если ошибка не уменьшается, признак только усложняет модель.

## task: leak-test | Автоматический тест на утечку | base

Функция `features(s)` из заготовки строит шесть признаков, и часть из них подглядывает в ответ. Три приёма в ней вам пока не встречались:

- `s.expanding().max()` — окно, которое начинается в начале ряда и растёт до текущей строки включительно: «максимум до сих пор»;
- `s.ewm(span=12).mean()` — экспоненциальное среднее: среднее по всему прошлому, где у свежих значений вес больше, а старые затухают; `span=12` задаёт скорость затухания: чем больше `span`, тем дольше помнится прошлое;
- `s.groupby(s.index.hour).transform(f)` — применяет `f` отдельно к ряду каждого часа суток (все 9:00 подряд, все 10:00 подряд…) и возвращает результат на места исходных строк.

Честны ли признаки по смыслу, определит ваш тест. Напишите `leak_test(features, s, t)`: испортите ряд в момент `t` (прибавьте 1000), постройте признаки по исходному и испорченному ряду и верните отсортированный список названий признаков, у которых значение **в строке `t`** изменилось. Примените к `t = pd.Timestamp("2026-07-15 12:00")` — результат в `leaking`.

### setup
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
def features(s):
    df = pd.DataFrame(index=s.index)
    df["lag_24"] = s.shift(24)                                   # то же время вчера
    df["change"] = s - s.shift(1)                                 # изменение к прошлому часу
    df["max_so_far"] = s.expanding().max()                        # максимум от начала ряда до этой строки
    df["ewm_prev"] = s.shift(1).ewm(span=12).mean()               # среднее с затухающими весами по прошлым часам
    df["hour_mean_prev_days"] = s.groupby(s.index.hour).transform(lambda x: x.shift(1).rolling(7).mean())  # этот час за 7 прошлых дней
    df["share_of_day"] = s / s.groupby(s.index.date).transform("sum")  # доля часа в сумме своего дня
    return df
```

### starter
```python
import pandas as pd

def leak_test(features, s, t):
    ...

```

### check
```python
import pandas as _pd
s0, f0 = need('s'), need('features')
t = _pd.Timestamp('2026-07-15 12:00')
sp = s0.copy(); sp[t] += 1000
ch = sorted(c for c in f0(s0).columns if f0(sp).loc[t, c] != f0(s0).loc[t, c])
assert need('leaking', list) == ch, f'leaking = {need("leaking")}, а нужно {ch}.'
lt = need('leak_test')
assert lt(f0, s0, _pd.Timestamp('2026-05-10 09:00')) == ch, 'leak_test должна работать для любого момента t, а не только для 15 июля.'
```

### hint
Копия ряда — `spoiled = s.copy()`, порча — `spoiled[t] = spoiled[t] + 1000`. Исходный ряд при этом не меняется.

### hint
Строки `t` двух таблиц признаков: `features(s).loc[t]` и `features(spoiled).loc[t]`; сравнение `!=` даст Series из `True/False` по столбцам.

### hint
Названия изменившихся: `sorted(changed[changed].index)`.

### solution
```python
import pandas as pd

def leak_test(features, s, t):
    spoiled = s.copy()
    spoiled[t] = spoiled[t] + 1000
    changed = features(spoiled).loc[t] != features(s).loc[t]
    return sorted(changed[changed].index)

leaking = leak_test(features, s, pd.Timestamp("2026-07-15 12:00"))
print(leaking)
```

### explain
Три признака из шести подглядывают: «изменение за час» `s − s.shift(1)` включает текущий час; «максимум до сих пор» `expanding().max()` — тоже (окно заканчивается на текущем значении); «доля часа в дне» — делит на сумму **всего дня**, включая будущие часы. Честные — лаг, экспоненциальное среднее **после** сдвига и среднее того же часа за прошлые дни. Обратите внимание: «доля в дне» выглядит безобидно, а подглядывает сильнее всех — в ней сразу и текущий час, и весь остаток дня.

## task: onehot-hours | Час как число и как категория | plus

Линейная регрессия на признаке «час» как числе не может описать суточный профиль с несколькими пиками. Сравните три линейные регрессии (обучение — до 1 августа, тест — август): `num` — признаки `hour` и `dow` числами; `onehot` — те же признаки, закодированные `pd.get_dummies(df[["hour", "dow"]].astype(str))`; `onehot_trend` — `onehot` плюс номер часа от начала ряда `t = np.arange(len(df))`. Сохраните `rmse` — словарь `{"num": …, "onehot": …, "onehot_trend": …}` (3 знака) и `n_onehot_cols` — число столбцов после кодирования.

### setup
```python
import numpy as np
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
df["hour"] = df.index.hour
df["dow"] = df.index.dayofweek
train = df.index < "2026-08-01"
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

def rmse(a, b):
    return round(float(np.sqrt(((a - b) ** 2).mean())), 3)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
d0, tr = need('df'), need('train')
y = d0['y']
def _r(X):
    p = _LR().fit(X[tr], y[tr]).predict(X[~tr]); return round(float(_np.sqrt(((y[~tr] - p) ** 2).mean())), 3)
X1 = d0[['hour', 'dow']]; X2 = _pd.get_dummies(d0[['hour', 'dow']].astype(str)); X3 = X2.assign(t=_np.arange(len(d0)))
w = {'num': _r(X1), 'onehot': _r(X2), 'onehot_trend': _r(X3)}
g = need('rmse', dict)
assert all(close(g[k], w[k], 0.006) for k in w), f'rmse = {g}, а нужно {w}.'
assert need('n_onehot_cols') == X2.shape[1], f'n_onehot_cols = {need("n_onehot_cols")}.'
```

### hint
`astype(str)` нужен, чтобы `get_dummies` увидел в часах категории, а не числа: иначе он оставит столбец как есть.

### hint
Для каждого набора признаков — одна и та же процедура: `LinearRegression().fit(X[train], y[train]).predict(X[~train])` и RMSE с `y[~train]`.

### hint
Признак тренда: `X_onehot.assign(t=np.arange(len(df)))`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

def rmse(a, b):
    return round(float(np.sqrt(((a - b) ** 2).mean())), 3)

y = df["y"]
def score(X):
    p = LinearRegression().fit(X[train], y[train]).predict(X[~train])
    return rmse(y[~train], p)

X_num = df[["hour", "dow"]]
X_onehot = pd.get_dummies(df[["hour", "dow"]].astype(str))
X_trend = X_onehot.assign(t=np.arange(len(df)))
rmse_vals = {"num": score(X_num), "onehot": score(X_onehot), "onehot_trend": score(X_trend)}
rmse = rmse_vals
n_onehot_cols = X_onehot.shape[1]
print(rmse, n_onehot_cols)
```

### explain
Час числом — RMSE около 7.8: прямая не может подняться утром, опуститься днём и снова подняться вечером. Тот же час, закодированный 24 флагами, — около 5.0: у каждого часа свой коэффициент, и профиль описывается точно. Добавленный тренд (номер часа) снимает ещё часть ошибки (около 4.5): заказов в августе больше, чем в среднем за обучение. Это та же мысль, что в главе 6: для линейной модели категория должна быть закодирована, а не записана числом. Деревьям это не так важно — они сами режут «час» на интервалы.

Почему здесь 31 столбец без `drop_first` (урок «Категориальные признаки и утечки» главы 6)? Полный набор флагов вместе со свободным членом — мультиколлинеарность: коэффициенты определены неоднозначно, и читать их нельзя. Но прогноз от этого не меняется: с `drop_first=True` получается 29 столбцов и тот же RMSE 5.034. Для прогноза хватает полного набора, для интерпретации коэффициентов берите `drop_first=True`.

## task: promo-feature | Признак «день акции» | star

В уроке «Временной ряд: индекс-дата, resample и скользящие окна» (задача «Почему пятницы») выяснилось, что всплески — пятничные акции, о которых известно заранее: 17 апреля, 22 мая, 19 июня, 24 июля, 21 августа, с 10 до 20 часов. Добавьте к `make_features(s)` признак `promo` (1 в эти часы) и сравните RMSE бустинга на августе с ним и без него. Отдельно посчитайте RMSE только на часах акции 21 августа. Сохраните `rmse_without`, `rmse_with`, `promo_without`, `promo_with` (3 знака).

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
promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
pdays = _pd.to_datetime(['2026-04-17', '2026-05-22', '2026-06-19', '2026-07-24', '2026-08-21'])
d = make_features(s0)
d['promo'] = (d.index.normalize().isin(pdays) & (d.index.hour >= 10) & (d.index.hour <= 20)).astype(int)
tr = d.index < '2026-08-01'; y = d['y']
pm = (d.index[~tr].normalize() == _pd.Timestamp('2026-08-21')) & (d.index[~tr].hour >= 10) & (d.index[~tr].hour <= 20)
r = lambda a, b: float(_np.sqrt(((a - b) ** 2).mean()))
c0 = [c for c in d.columns if c not in ('y', 'promo')]
p0 = _H(random_state=0).fit(d.loc[tr, c0], y[tr]).predict(d.loc[~tr, c0])
p1 = _H(random_state=0).fit(d.loc[tr, c0 + ['promo']], y[tr]).predict(d.loc[~tr, c0 + ['promo']])
yt = y[~tr].values
w = {'rmse_without': r(yt, p0), 'rmse_with': r(yt, p1), 'promo_without': r(yt[pm], p0[pm]), 'promo_with': r(yt[pm], p1[pm])}
for k, v in w.items():
    assert close(need(k), round(v, 3), 0.002), f'{k} = {need(k)}, а нужно {round(v, 3)}.'
```

### hint
Признак: `df.index.normalize().isin(promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)`. `normalize()` обнуляет время, оставляя дату.

### hint
Часы акции в тесте — та же маска для 21 августа; прогнозы обеих моделей сравнивайте на этих часах.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])

df = make_features(s)
hours = df.index.hour
df["promo"] = (df.index.normalize().isin(promo_days) & (hours >= 10) & (hours <= 20)).astype(int)
train = df.index < "2026-08-01"
y = df["y"]
base_cols = [c for c in df.columns if c not in ("y", "promo")]

def rmse(a, b):
    return float(np.sqrt(((a - b) ** 2).mean()))

p_without = HistGradientBoostingRegressor(random_state=0).fit(df.loc[train, base_cols], y[train]).predict(df.loc[~train, base_cols])
p_with = HistGradientBoostingRegressor(random_state=0).fit(df.loc[train, base_cols + ["promo"]], y[train]).predict(df.loc[~train, base_cols + ["promo"]])
y_test = y[~train].values
test_idx = df.index[~train]
promo_mask = (test_idx.normalize() == pd.Timestamp("2026-08-21")) & (test_idx.hour >= 10) & (test_idx.hour <= 20)
rmse_without = round(rmse(y_test, p_without), 3)
rmse_with = round(rmse(y_test, p_with), 3)
promo_without = round(rmse(y_test[promo_mask], p_without[promo_mask]), 3)
promo_with = round(rmse(y_test[promo_mask], p_with[promo_mask]), 3)
```

### explain
За весь август разница небольшая — акция одна. Но в часы акции ошибка без признака огромная: модель не знает, что будет всплеск, и узнаёт о нём только через лаг 1, с опозданием на час. С признаком она готова заранее. Для бизнеса именно эти часы самые важные: в акцию не хватает рук.
