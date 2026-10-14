---
title: "Тренд, сезонность и остаток"
files: [app_orders.csv]
lead: "Любой ряд удобно представить как сумму трёх частей: медленный тренд, повторяющаяся сезонность и всё остальное — остаток. Раскладываем заказы на части, смотрим на автокорреляцию — «похожесть ряда на самого себя со сдвигом» — и разбираемся, что такое стационарность и зачем её добиваются разностями."
recap:
  - "Аддитивная модель ряда: значение = тренд + сезонность + остаток. `seasonal_decompose(s, period=...)` из statsmodels делает такое разложение."
  - "Период сезонности задаёт аналитик: 24 для суточного ритма в часовых данных, 7 — для недельного в дневных."
  - "Автокорреляция `s.autocorr(lag)` — корреляция ряда с самим собой, сдвинутым на lag шагов. Пики на лагах 24 и 168 выдают суточную и недельную сезонность."
  - "Стационарный ряд — без тренда и с постоянным разбросом; его статистики не зависят от времени. Многие классические модели требуют стационарности."
  - "Разность `s.diff()` убирает тренд, сезонная разность `s.diff(24)` — суточную сезонность. Тест Дики — Фуллера (`adfuller`) проверяет стационарность."
---

## Три части ряда

Посмотрим на дневные заказы как на сумму трёх слагаемых:

- **тренд** — медленное изменение уровня (приложение набирает аудиторию);
- **сезонность** — то, что повторяется с постоянным периодом (дни недели, часы суток);
- **остаток** — всё, что не объясняется первыми двумя: шум, акции, сбои.

::: figure ts-decompose
Игрушечный ряд из двух недель как сумма частей: прямая «100 + 2 в день», недельный узор (+10 по пятницам, −5 в выходные) и остаток. В игрушке шума нет, поэтому остаток — ноль; в настоящих данных в нём шум, акции и сбои.
:::

::: tip Аналогия
Разложение похоже на чек за коммунальные услуги: общая сумма складывается из постоянно растущего тарифа (тренд), сезонной добавки за отопление зимой (сезонность) и разовых строк вроде перерасчёта (остаток). Глядя только на итог, не понять, почему он вырос; по строкам — понятно. Разница в том, что в чеке строки известны точно, а разложение ряда — оценка, и её результат зависит от выбранного периода.
:::

Модуль `statsmodels` раскладывает ряд на эти части. Тренд он оценивает скользящим средним длиной в период, сезонность — средним отклонением от тренда для каждой позиции внутри периода.

Проверим идею на ряду, который мы соберём сами и потому знаем ответ: две недели, тренд «100 + 2 в день» и недельный узор «по пятницам +10, в выходные −5».

```python
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

idx = pd.date_range("2026-06-01", periods=14, freq="D")       # 1 июня 2026 — понедельник
trend = 100 + 2 * np.arange(14)
weekly = np.tile([0, 0, 0, 0, 10, -5, -5], 2)                    # пн … вс, дважды
toy = pd.Series(trend + weekly, index=idx)

parts = seasonal_decompose(toy, period=7)
print("скользящее среднее за 7 дней:", toy.rolling(7, center=True).mean().round(1).tolist())
print("тренд из разложения:         ", parts.trend.round(1).tolist())
print("сезонность за неделю:", (parts.seasonal[:7].round(1) + 0.0).tolist())
```

**Что здесь происходит:**

- `np.tile(узор, 2)` повторяет недельный узор дважды — 14 значений.
- `rolling(7, center=True)` — среднее по окну из 7 дней, **центрированному** на текущем дне (3 дня до, сам день, 3 дня после). Внутри окна ровно одна неделя, и узор (+10, −5, −5 — в сумме 0) усредняется в ноль: остаётся чистый тренд.
- `seasonal_decompose` делает то же самое и затем считает, на сколько каждый день недели в среднем отклоняется от тренда.
- `+ 0.0` в печати — косметика: без неё нулевые поправки печатаются как `-0.0`. Это тот же ноль, просто вычисление дало крошечное отрицательное число, а округление сохранило знак.

::: figure ts-center-window
Как центрированное окно отделяет тренд от узора: в окно из 7 дней попадает ровно одна неделя, узор (+10, −5, −5) в сумме даёт ноль, и среднее окна — это тренд в середине окна.
:::

**Что получилось:** тренд 106, 108, 110… — ровно наши «100 + 2t» (первые и последние три значения — пропуски: для них нет полного окна). Сезонность — 0, 0, 0, 0, +10, −5, −5: узор восстановлен точно. На настоящих данных всё то же, только к сумме добавляется остаток — шум и события.

```python
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
parts = seasonal_decompose(daily, model="additive", period=7)

fig, axes = plt.subplots(4, 1, figsize=(8, 7), sharex=True)
for ax, (name, part) in zip(axes, [("ряд", daily), ("тренд", parts.trend),
                                    ("сезонность", parts.seasonal), ("остаток", parts.resid)]):
    part.plot(ax=ax)
    ax.set_ylabel(name)
plt.show()
print("недельная сезонность:", parts.seasonal[:7].round(1).tolist())
```

**Что здесь происходит:**

- `seasonal_decompose(daily, model="additive", period=7)` — разложение «ряд = тренд + сезонность + остаток» с недельным циклом.
- `parts.trend`, `parts.seasonal`, `parts.resid` — три Series той же длины, что ряд.
- Четыре графика друг под другом с общей осью времени (`sharex=True`) — стандартный способ показать разложение.
- `parts.seasonal[:7]` — первая неделя сезонной части: дальше она повторяется.

`period=7` — недельный цикл в дневных данных. Тренд растёт со 159 до 261 заказа в день. Недельная сезонность небольшая, кроме пятницы (+18): это вклад ежемесячных пятничных акций, размазанный по всем пятницам (урок «Временной ряд: индекс-дата, resample и скользящие окна»). Ряд начинается в воскресенье 1 марта, поэтому список поправок тоже начинается с воскресенья, и пятница в нём — шестое число. Остаток — с разбросом около 24 заказов, в нём видны всплески акций и провал 3 июня.

::: note
Модель бывает и **мультипликативной**: значение = тренд × сезонность × остаток (`model="multiplicative"`). Она подходит, когда размах сезонных колебаний растёт вместе с уровнем — например, утренний пик вырос вместе с аудиторией не на 5 заказов, а в 1.5 раза.
:::

{{practice: decompose, toy-trend, multiplicative, residual-days}}

## Суточная сезонность

В часовых данных главный цикл — сутки. Разложим две недели августа с периодом 24:

```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
two_weeks = s["2026-08-03":"2026-08-16"]
parts = seasonal_decompose(two_weeks, period=24)
print(parts.seasonal[:24].round(1).tolist())
```

**Что здесь происходит:**

- `s["2026-08-03":"2026-08-16"]` — две недели часовых данных, 336 значений.
- `period=24` — суточный цикл; `model` по умолчанию аддитивная.

Сезонная часть — 24 числа, повторяющиеся каждые сутки: ночью −9…−10 к тренду, утренний пик около +7, вечерний +11. Обратите внимание: разложение с одним периодом видит только один цикл. Будни и выходные в этом ряду устроены по-разному (задача «Суточный профиль» в уроке «Временной ряд: индекс-дата, resample и скользящие окна»), и «средние сутки» их смешивают — для прогноза такой цикл задают признаками (урок «Признаки для прогноза ряда»).

{{practice: hour-season}}

## Автокорреляция

Как найти сезонность, не глядя на график? Через **автокорреляцию**: насколько ряд похож на самого себя, сдвинутого на lag шагов. Это обычная корреляция (глава 4) между `s` и `s.shift(lag)`.

```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
for lag in (1, 2, 12, 24, 168):
    print(f"лаг {lag:>3}: {s.autocorr(lag):.3f}")
```

**Что здесь происходит:**

- `s.autocorr(lag)` — корреляция ряда с самим собой, сдвинутым на `lag` часов. То же самое, что `s.corr(s.shift(lag))`.
- Корреляция от −1 до 1 (глава 4): 1 — сдвинутый ряд повторяет исходный, 0 — связи нет, отрицательная — «когда здесь много, там мало».

Что видно:

- лаг 1 (час назад) — 0.72: соседние часы похожи;
- лаг 12 — отрицательная: через полсуток день сменяется ночью;
- лаг 24 — 0.71: то же время вчера снова похоже, это суточный цикл;
- лаг 168 (неделя) — 0.74: самая сильная связь, потому что совпадает и час, и тип дня.

::: predict
```python static
import pandas as pd
s = pd.Series([1, 2, 3, 1, 2, 3, 1, 2, 3])
print(round(s.autocorr(3), 2))
```

- `0.0`
- [x] `1.0`
- `-1.0`

Почему: ряд повторяется с периодом 3, поэтому сдвинутый на 3 шага он совпадает сам с собой — корреляция 1.
:::

::: figure ts-acf
Слева — что значит «сравнить ряд с ним же со сдвигом»: при сдвиге на сутки пики ложатся на пики, при сдвиге на полсуток — на провалы. Справа — автокорреляция часовых заказов на пяти лагах.
:::

::: tip Аналогия
Автокорреляция — как наложить на просвет две страницы расписания кофейни: сегодняшнюю и вчерашнюю. Если очереди в одни и те же часы, рисунки совпадают; сдвиньте вторую страницу на 12 часов — утренний пик ляжет на ночь, и совпадения не будет.
:::

Именно эти лаги станут лучшими признаками для прогноза в следующем уроке. В statsmodels есть функция `acf` и график `plot_acf` — они считают автокорреляцию сразу для многих лагов.

::: quiz
Автокорреляция часовых заказов на лаге 24 высокая. Что это значит?

- [x] В одно и то же время суток заказов похоже много или мало — есть суточный ритм
  > Высокая автокорреляция на лаге k — признак периодичности с периодом k. Её используют как лаг-признак.
- [ ] Каждые 24 часа заказов становится больше
  > Автокорреляция говорит о похожести, а не о росте.
- [ ] Ряд стационарен
  > Автокорреляция показывает периодичность, а не стационарность. По определению ряд с сезонностью нестационарен (среднее зависит от часа); на практике стационарность проверяют тестом из следующего раздела, и регулярную сезонность он часто не замечает.
- [ ] Модель переобучилась
  > Автокорреляция — свойство данных, а не модели.
:::

{{practice: p-acf, acf-plot}}

## Стационарность и разности

Ряд **стационарен**, если его свойства не меняются со временем: среднее и разброс постоянны, нет тренда. У наших дневных заказов есть тренд — значит, нет.

Для моделей из глав 6–10 (бустинг, линейная регрессия на признаках) стационарность не обязательна, но тренд мешает и им: модель, обученная на ряде со средним 170, будет промахиваться, когда среднее станет 260, а деревья тренд не продолжают (глава 10). Поэтому из этого раздела нам нужны две вещи: как проверить, есть ли тренд, и как его убрать **разностью**.

::: deep Зачем стационарность классическим моделям
Классические модели временных рядов (ARIMA и её семейство) строят прогноз как комбинацию прошлых значений и прошлых ошибок с постоянными коэффициентами. Это работает, только если свойства ряда не меняются, поэтому такие модели прямо требуют стационарности: ряд сначала приводят к ней разностями (буква I в ARIMA — «интегрированная», то есть число разностей), а прогноз потом «собирают» обратно. В курсе мы прогнозируем бустингом на признаках, поэтому ARIMA не разбираем.
:::

::: tip Аналогия
Стационарный ряд похож на выручку давно работающей кофейни у вокзала: день на день не приходится, но колебания идут вокруг одного и того же уровня и с одним и тем же размахом — по любому месяцу можно судить о любом другом. Выручка новой кофейни, которая набирает гостей, нестационарна: уровень марта ничего не говорит о том, каким будет август. Строго говоря, у кофейни у вокзала всё равно есть недельный ритм, а ряд с сезонностью по определению нестационарен: его среднее зависит от дня недели. Как с этим обходится тест — ниже.
:::

Разность — это изменение вместо уровня: `s.diff()`. А проверяют стационарность тестом **Дики — Фуллера** (`adfuller` из statsmodels): нулевая гипотеза — «ряд нестационарен», маленький p-value — повод её отвергнуть (логика из главы 5).

```python
import pandas as pd
from statsmodels.tsa.stattools import adfuller

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()
print("ряд:     p =", round(adfuller(daily)[1], 3))
print("разность: p =", adfuller(daily.diff().dropna())[1])
```

**Что здесь происходит:**

- `adfuller(ряд)` возвращает кортеж; `[1]` — p-value теста.
- Как читать: p-value — вероятность увидеть такие данные, если ряд на самом деле **нестационарен**. Маленькое (меньше 0.05) — отвергаем нестационарность, ряд можно считать стационарным; большое — нет оснований.
- `daily.diff().dropna()` — разности без первого пропуска: тест не принимает пропуски.

Что именно ловит тест. Дики — Фуллер проверяет в первую очередь одно: «блуждает» ли уровень ряда — уходит ли он в сторону и не возвращается (тренд, случайное блуждание). Регулярную сезонность, которая каждые сутки возвращается к тому же уровню, он часто не замечает. Поэтому часовой ряд с сильным суточным циклом может пройти тест как стационарный (задача «Тест на стационарность»), хотя по строгому определению он нестационарен. Вывод: тест — про тренд и блуждание; сезонность ищут автокорреляцией и разложением.

::: figure ts-diff-trend
Слева — дневные заказы: уровень растёт, тест Дики — Фуллера не отвергает нестационарность. Справа — разность за день: колебания вокруг нуля без тренда.
:::

У самого ряда p ≈ 0.8 — тренд не даёт считать его стационарным. У разностей p — микроскопическое: «изменение за день» колеблется вокруг нуля без тренда. Для сезонности есть **сезонная разность**: `s.diff(24)` — «на сколько больше, чем в этот час вчера». По той же причине и в моделях на признаках иногда прогнозируют не уровень, а разность или отношение к недавнему уровню.

::: quiz
Чем `s.diff(24)` отличается от `s.diff()` для часового ряда заказов?

- [x] `diff(24)` — разница с тем же часом вчера: суточный ритм вычитается; `diff()` — разница с прошлым часом: убирает уровень, но утренний подъём и ночной спад остаются
  > Аргумент `diff` — лаг. Сезонная разность с лагом, равным периоду, убирает и тренд, и сезонность этого периода.
- [ ] Ничем: оба вычитают предыдущее значение
  > Предыдущее вычитает только `diff()` (лаг 1). `diff(24)` вычитает значение 24 шагами раньше.
- [ ] `diff(24)` — сумма изменений за последние сутки
  > Суммы за окно — это `rolling(24).sum()`. `diff(24)` — одна разность двух значений.
- [ ] `diff(24)` делит изменение на 24, чтобы получить среднее за час
  > Деления нет: это просто `s - s.shift(24)`.
:::

::: warn Типичные ошибки
- **Тренд из `seasonal_decompose` — в признаки модели.** Тренд считается центрированным окном, то есть по дням **после** текущего. Для анализа это нормально, для прогноза — утечка из будущего: в момент прогноза этих дней ещё нет.
- **Не тот период.** `period` задаёт аналитик: 7 для недельного цикла в дневных данных, 24 — для суточного в часовых. Период 7 в часовых данных ничего осмысленного не найдёт, а разложение всё равно отработает без ошибок.
- **Разность «на всякий случай».** Разность убирает тренд, но и уровень: прогноз разности надо потом сложить с последним известным значением. Для бустинга на признаках разность часто не нужна вовсе — тренд ловят лаги и скользящие средние.
:::

{{practice: diff, adf}}

## Разберём вместе: какая разность «спокойнее»

У часового ряда два цикла — сутки и неделя. Какая разность лучше убирает предсказуемую часть: с прошлым часом, с тем же часом вчера или с тем же часом неделю назад? Чем меньше разброс разности, тем больше предсказуемого она убрала.

**План:** посчитать стандартное отклонение самого ряда и трёх разностей — `diff(1)`, `diff(24)`, `diff(168)` — и сравнить.

```python
import pandas as pd

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
print("сам ряд:          ", round(s.std(), 2))
for lag, name in [(1, "час назад"), (24, "сутки назад"), (168, "неделя назад")]:
    print(f"разность с «{name}»:", round(s.diff(lag).std(), 2))
```

**Что получилось:** все три разности спокойнее самого ряда (около 5 против 7), а самая спокойная — недельная: «этот час в этот же день недели неделю назад» лучше всего предсказывает текущий. Это совпадает с автокорреляцией (лаг 168 — самый сильный) и подсказывает простейший прогноз — «как неделю назад» (урок «Прогноз: ориентиры, горизонт и метрики»). Разница между тремя разностями небольшая: основной разброс часовых заказов — случайный шум, который никакая разность не уберёт.

{{practice: seasonal-diff}}

## Практика

## task: decompose | Разложение дневного ряда | warmup

Разложите дневные заказы с `period=7` и сохраните `trend_growth` — разницу между последним и первым непустыми значениями тренда (1 знак) и `best_dow` — номер дня недели (0 — понедельник) с наибольшей сезонной поправкой.

### starter
```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

```

### check
```python
import pandas as _pd
from statsmodels.tsa.seasonal import seasonal_decompose as _sd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
p = _sd(s0.resample('D').sum(), model='additive', period=7)
t = p.trend.dropna()
assert close(need('trend_growth'), round(t.iloc[-1] - t.iloc[0], 1), 0.06), f'trend_growth = {need("trend_growth")}.'
se = p.seasonal[:7]
assert need('best_dow') == int(se.idxmax().dayofweek), f'best_dow = {need("best_dow")}.'
```

### hint
Разложение: `seasonal_decompose(daily, model="additive", period=7)` — результат хранит `.trend`, `.seasonal`, `.resid`.

### hint
`parts.trend.dropna()`; день недели максимума сезонности: `parts.seasonal[:7].idxmax().dayofweek`.

### solution
```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

parts = seasonal_decompose(daily, model="additive", period=7)
t = parts.trend.dropna()
trend_growth = round(t.iloc[-1] - t.iloc[0], 1)
best_dow = int(parts.seasonal[:7].idxmax().dayofweek)
```

## task: toy-trend | Тренд скользящим средним | warmup

В заготовке — ряд `toy` из 21 дня: тренд «50 + 3 в день» и недельный узор. Посчитайте `trend7` — центрированное скользящее среднее за 7 дней и `seasonal_week` — среднее отклонение `toy − trend7` по дням недели (Series с индексом 0–6, 1 знак). В `pattern_sum` — сумму `seasonal_week` (1 знак).

### setup
```python
import numpy as np
import pandas as pd
toy = pd.Series(50 + 3 * np.arange(21) + np.tile([2, 2, 2, 2, 8, -8, -8], 3),
                index=pd.date_range("2026-06-01", periods=21, freq="D"))
```

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
t0 = need('toy')
tr = t0.rolling(7, center=True).mean()
assert _pd.Series(need('trend7')).round(6).equals(tr.round(6)), 'trend7 — toy.rolling(7, center=True).mean().'
sw = (t0 - tr).groupby(t0.index.dayofweek).mean().round(1)
g = need('seasonal_week', _pd.Series)
assert list(g.index) == list(range(7)) and all(close(g[k], sw[k], 0.051) for k in range(7)), f'seasonal_week = {g.tolist()}, а нужно {sw.tolist()}.'
assert close(need('pattern_sum'), round(sw.sum(), 1), 0.051), f'pattern_sum = {need("pattern_sum")}.'
```

### hint
Центрированное окно: `toy.rolling(7, center=True).mean()`.

### hint
Отклонение от тренда — `toy - trend7`; среднее по дням недели — `.groupby(toy.index.dayofweek).mean()` (пропуски `mean` пропустит сам).

### solution
```python
import pandas as pd

trend7 = toy.rolling(7, center=True).mean()
seasonal_week = (toy - trend7).groupby(toy.index.dayofweek).mean().round(1)
pattern_sum = round(seasonal_week.sum(), 1)
print(trend7.round(1).tolist(), seasonal_week.tolist(), pattern_sum)
```

## task: p-acf | Автокорреляция по лагам | warmup

Соберите код, который печатает лаг с наибольшей автокорреляцией среди 1, 24 и 168.

### parsons
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
lags = [1, 24, 168]
values = [s.autocorr(lag) for lag in lags]
best = lags[values.index(max(values))]
print(best)
```

### check
```python
assert _lines == ['168'], f'Сейчас: {_lines}.'
```

### hint
Сначала список лагов, потом значения, потом выбор максимума.

### hint
`s.autocorr(lag)` для каждого лага из списка.

## task: diff | Разности | warmup

Посчитайте для дневного ряда разность `d1 = daily.diff()` и недельную разность `d7 = daily.diff(7)`. Сохраните средние значения `mean_d1`, `mean_d7` (2 знака, без пропусков) и `std_ratio` — отношение стандартного отклонения `daily` к стандартному отклонению `d1` (2 знака).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d0 = s0.resample('D').sum()
assert close(need('mean_d1'), round(d0.diff().mean(), 2), 0.006) and close(need('mean_d7'), round(d0.diff(7).mean(), 2), 0.006), f'mean_d1, mean_d7 = {need("mean_d1")}, {need("mean_d7")}.'
assert close(need('std_ratio'), round(d0.std() / d0.diff().std(), 2), 0.006), f'std_ratio = {need("std_ratio")}.'
```

### hint
`mean()` и `std()` пропуски пропускают сами.

### hint
Обычная разность — `daily.diff()`, недельная — `daily.diff(7)`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

d1 = daily.diff()
d7 = daily.diff(7)
mean_d1 = round(d1.mean(), 2)
mean_d7 = round(d7.mean(), 2)
std_ratio = round(daily.std() / d1.std(), 2)
```

### explain
Средняя дневная разность — меньше одного заказа в день: так выглядит тренд на языке разностей. Недельная разность — около 4 заказов: рост за неделю. Но разброс разностей почти такой же, как у самого ряда: день ото дня заказы прыгают сильно, и шум никуда не делся.

## task: adf | Тест на стационарность | base

Проверьте тестом Дики — Фуллера часовой ряд за август (`s["2026-08"]`), его суточную разность (`diff(24)`) и дневной ряд за всё время. Сохраните p-value `p_hour_aug`, `p_hour_diff24`, `p_daily` (4 знака) и список `stationary` — названия рядов (`"часы август"`, `"часы разность 24"`, `"дни"`), для которых p < 0.05.

### starter
```python
import pandas as pd
from statsmodels.tsa.stattools import adfuller
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
from statsmodels.tsa.stattools import adfuller as _adf
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
a = s0['2026-08']; w = {'часы август': _adf(a)[1], 'часы разность 24': _adf(a.diff(24).dropna())[1], 'дни': _adf(s0.resample('D').sum())[1]}
assert close(need('p_hour_aug'), round(w['часы август'], 4), 2e-4) and close(need('p_hour_diff24'), round(w['часы разность 24'], 4), 2e-4) and close(need('p_daily'), round(w['дни'], 4), 2e-4), 'p-value не совпадают — проверьте ряды и dropna у разности.'
assert list(need('stationary')) == [k for k, v in w.items() if v < 0.05], f'stationary = {need("stationary")}.'
```

### hint
Тест: `from statsmodels.tsa.stattools import adfuller`; пропусков в ряду быть не должно.

### hint
`adfuller(ряд)[1]` — p-value. У разности первые 24 значения — пропуски: `.dropna()`.

### solution
```python
import pandas as pd
from statsmodels.tsa.stattools import adfuller
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

aug = s["2026-08"]
p_hour_aug = round(adfuller(aug)[1], 4)
p_hour_diff24 = round(adfuller(aug.diff(24).dropna())[1], 4)
p_daily = round(adfuller(s.resample("D").sum())[1], 4)
res = {"часы август": p_hour_aug, "часы разность 24": p_hour_diff24, "дни": p_daily}
stationary = [k for k, v in res.items() if v < 0.05]
```

### explain
Часовой ряд за месяц тест признаёт стационарным, хотя суточный цикл в нём сильный. Противоречия с определением нет, а есть то, о чём сказано в разделе «Стационарность и разности»: тест ищет в первую очередь блуждание уровня и тренд, а регулярную сезонность, которая каждые сутки возвращается к тому же уровню, часто не замечает. На коротком отрезке тренд почти незаметен, вот ряд и проходит тест. Дневной ряд за полгода — нет: тренд виден. Это напоминание: стационарность — свойство ряда на конкретном отрезке, а тест — инструмент с ошибками I и II рода (глава 5), а не окончательный вердикт.

## task: hour-season | Сезонная поправка по часам | base

Разложите две недели (`s["2026-08-03":"2026-08-16"]`) с `period=24`. Сохраните `season24` — 24 значения сезонной части за первые сутки (Series с индексом-часом 0–23, 1 знак), `night_min` — час с наименьшей поправкой (если после округления до 1 знака минимумов несколько, подойдёт любой из них) и `amplitude` — разницу максимума и минимума (1 знак).

### starter
```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
from statsmodels.tsa.seasonal import seasonal_decompose as _sd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
se = _sd(s0['2026-08-03':'2026-08-16'], period=24).seasonal[:24]
got = need('season24', _pd.Series)
assert list(got.index) == list(range(24)), 'Индекс season24 — часы 0–23 (например, .index.hour).'
assert all(close(got[h], round(se.iloc[h], 1), 0.06) for h in range(24)), 'Значения сезонной части не совпадают.'
_r = se.round(1).values; _ok = [h for h in range(24) if _r[h] == _r.min()]
assert need('night_min') in _ok, f'night_min = {need("night_min")}, а подходит {" или ".join(str(h) for h in _ok)}: час с наименьшей сезонной поправкой.'
assert close(need('amplitude'), round(se.max() - se.min(), 1), 0.11), f'amplitude = {need("amplitude")}.'
```

### hint
Разложите часовой ряд нужного периода с `period=24`; сезонность одинакова для всех суток.

### hint
Первые сутки — `parts.seasonal[:24]`; индекс-час: `.set_axis(range(24))` или `pd.Series(x.values, index=x.index.hour)`.

### solution
```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

parts = seasonal_decompose(s["2026-08-03":"2026-08-16"], period=24)
first_day = parts.seasonal[:24]
season24 = pd.Series(first_day.values, index=first_day.index.hour).round(1)
night_min = int(first_day.values.argmin())
amplitude = round(first_day.max() - first_day.min(), 1)
```

### explain
Сезонная часть — средняя поправка к тренду для каждого часа суток, одинаковая во все дни. Ночью заказов меньше обычного примерно на 8–10 (минимум в 3–4 утра: −9.92 и −9.94, после округления оба −9.9), днём видны два пика: утренний в 8 часов (+7.5) и вечерний в 18 часов (+11.3). Размах 21.3 заказа в час — насколько час пик отличается от глубокой ночи при одинаковом тренде. С этим числом работают при планировании смен: оно показывает, на сколько бариста нужно больше в пиковые часы.

## task: seasonal-diff | Какая разность лучше | base

Для часового ряда посчитайте стандартные отклонения: `std_level` — самого ряда, `std_by_lag` — словарь `{1: …, 24: …, 168: …}` для разностей с этими лагами (все — 2 знака). Сохраните `best_lag` — лаг с наименьшим разбросом, и `gain` — во сколько раз разброс лучшей разности меньше разброса ряда (2 знака).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
w = {k: round(float(s0.diff(k).std()), 2) for k in [1, 24, 168]}
g = {int(k): v for k, v in need('std_by_lag', dict).items()}
assert all(close(g[k], w[k], 0.006) for k in w), f'std_by_lag = {g}, а нужно {w}.'
assert close(need('std_level'), round(float(s0.std()), 2), 0.006), f'std_level = {need("std_level")}.'
b = min(w, key=w.get)
assert need('best_lag') == b, f'best_lag = {need("best_lag")}.'
assert close(need('gain'), round(s0.std() / s0.diff(b).std(), 2), 0.011), f'gain = {need("gain")}.'
```

### hint
Разность с лагом `k` — `s.diff(k)`; её разброс — `.std()` (пропуски в начале `std` пропускает сам).

### hint
`std_by_lag = {k: round(float(s.diff(k).std()), 2) for k in [1, 24, 168]}`; лучший — `min(std_by_lag, key=std_by_lag.get)`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

std_level = round(float(s.std()), 2)
std_by_lag = {k: round(float(s.diff(k).std()), 2) for k in [1, 24, 168]}
best_lag = min(std_by_lag, key=std_by_lag.get)
gain = round(s.std() / s.diff(best_lag).std(), 2)
print(std_level, std_by_lag, best_lag, gain)
```

### explain
Недельная разность выигрывает, но ненамного: разброс падает примерно в 1.4 раза. Основная часть колебаний часовых заказов — случайность конкретного часа. Отсюда реалистичные ожидания от прогноза: ошибка в 4–5 заказов в час почти неизбежна, и модель, которая «обещает» точность до заказа, скорее всего, переобучилась или подглядела в будущее.

## task: multiplicative | Растёт ли размах | plus

Аддитивная модель предполагает, что суточные колебания одинаковы при любом уровне, мультипликативная — что они растут вместе с уровнем. Для марта и августа посчитайте средний суточный профиль (среднее по часу суток), его размах (`max − min`) и средний уровень (среднее заказов в час). Сохраните `amp` — словарь `{"03": размах, "08": размах}` (1 знак), `level` — то же для уровня (2 знака), `amp_growth` и `level_growth` — во сколько раз август больше марта (2 знака), и `model_type` — `"multiplicative"`, если отношения размахов и уровней отличаются меньше чем на 10 %, иначе `"additive"`.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
a, l = {}, {}
for m in ['03', '08']:
    x = s0['2026-' + m]; p = x.groupby(x.index.hour).mean()
    a[m] = round(float(p.max() - p.min()), 1); l[m] = round(float(x.mean()), 2)
ga = {str(k): v for k, v in need('amp', dict).items()}; gl = {str(k): v for k, v in need('level', dict).items()}
assert all(close(ga[m], a[m], 0.051) for m in a), f'amp = {ga}, а нужно {a}.'
assert all(close(gl[m], l[m], 0.006) for m in l), f'level = {gl}, а нужно {l}.'
ag, lg = a['08'] / a['03'], l['08'] / l['03']
assert close(need('amp_growth'), round(ag, 2), 0.011) and close(need('level_growth'), round(lg, 2), 0.011), 'amp_growth, level_growth — август / март.'
mt = 'multiplicative' if abs(ag / lg - 1) < 0.1 else 'additive'
assert need('model_type') == mt, f'model_type = {need("model_type")!r}.'
```

### hint
Месяц — `s["2026-03"]`; профиль — `x.groupby(x.index.hour).mean()`; размах — `p.max() - p.min()`.

### hint
Отношения: `amp_growth = amp["08"] / amp["03"]`, `level_growth = level["08"] / level["03"]`. Сравните их: `abs(amp_growth / level_growth - 1) < 0.1`.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

amp, level = {}, {}
for m in ["03", "08"]:
    x = s["2026-" + m]
    profile = x.groupby(x.index.hour).mean()
    amp[m] = round(float(profile.max() - profile.min()), 1)
    level[m] = round(float(x.mean()), 2)
amp_growth = round(amp["08"] / amp["03"], 2)
level_growth = round(level["08"] / level["03"], 2)
model_type = "multiplicative" if abs(amp_growth / level_growth - 1) < 0.1 else "additive"
print(amp, level, amp_growth, level_growth, model_type)
```

### explain
Уровень вырос примерно в 1.5 раза, и размах суточных колебаний — тоже в 1.5 раза: пики растут пропорционально аудитории. Значит, ряд мультипликативный: в любом месяце размах суток — примерно два средних уровня, то есть колебания описываются «во столько-то раз», а не «на столько-то заказов». Для разложения это `model="multiplicative"`, а для моделей на признаках — повод прогнозировать отношение к уровню или логарифм заказов. Аддитивная модель на таком ряду недооценивает пики в конце периода и переоценивает в начале.

Почему же дальше в главе мы не переходим на мультипликативную запись? Разложение здесь — инструмент анализа, а прогноз строим бустингом на признаках. Лаги вроде «тот же час неделю назад» уже несут нынешний уровень, и пик, выросший в 1.5 раза, модель видит через них. Посмотреть мультипликативное разложение можно одной строкой на дневном ряду: `seasonal_decompose(daily, model="multiplicative", period=7)` — сезонность там множители около 1, а не добавки в заказах: у пятницы 1.078, то есть +7.8 % к тренду. На часовом ряду так не выйдет: в нём есть ночные нули, а мультипликативная модель принимает только положительные значения и падает с ошибкой.

## task: acf-plot | Автокорреляция по лагам | plus

Посчитайте автокорреляцию часового ряда для лагов 1…200 (`[s.autocorr(l) for l in range(1, 201)]`) и нарисуйте её столбцами (`ax.bar`), ось X — `"лаг, часов"`. Сохраните список `acf_vals`, `top3` — три лага с наибольшей автокорреляцией (по убыванию значения) и `near_day` — лаг с максимумом среди лагов 20–28.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import numpy as _np, pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
v = [s0.autocorr(l) for l in range(1, 201)]
assert _np.allclose(need('acf_vals'), v), 'acf_vals — автокорреляция для лагов 1…200.'
top = [int(i) + 1 for i in _np.argsort(v)[::-1][:3]]
assert [int(x) for x in need('top3')] == top, f'top3 = {need("top3")}, а нужно {top}.'
assert need('near_day') == 20 + int(_np.argmax(v[19:28])), f'near_day = {need("near_day")}.'
ax = ax_of(0)
assert len(ax.patches) == 200, f'Столбцов на графике {len(ax.patches)}, нужно 200.'
assert ax.get_xlabel() == 'лаг, часов', 'Подпишите ось X: «лаг, часов».'
```

### hint
Значения автокорреляции для лагов 1…N удобно собрать списковым выражением: `[s.autocorr(k) for k in range(1, N + 1)]`.

### hint
Номер лага = позиция в списке + 1. Три наибольших: `np.argsort(acf_vals)[::-1][:3] + 1`.

### solution
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

lags = list(range(1, 201))
acf_vals = [s.autocorr(l) for l in lags]
top3 = [int(i) + 1 for i in np.argsort(acf_vals)[::-1][:3]]
near_day = 20 + int(np.argmax(acf_vals[19:28]))

fig, ax = plt.subplots(figsize=(8, 3))
ax.bar(lags, acf_vals)
ax.set_xlabel("лаг, часов")
ax.set_ylabel("автокорреляция")
plt.show()
```

### explain
На графике — «гребёнка» с зубцами каждые 24 часа и самым высоким на 168 (неделя). Лаг 1 тоже высокий: ближайший час похож на текущий. Такой график — быстрый способ понять, какие лаги брать в признаки.

## task: residual-days | Остаток показывает аномалии | star

По разложению дневного ряда (`period=7`) найдите дни, где остаток по модулю больше трёх стандартных отклонений остатка. Сохраните список дат `outliers` (как `datetime.date`, по возрастанию) и `kinds` — для каждой даты `"всплеск"`, если остаток положительный, иначе `"провал"`.

### starter
```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

```

### check
```python
import pandas as _pd
from statsmodels.tsa.seasonal import seasonal_decompose as _sd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
r = _sd(s0.resample('D').sum(), model='additive', period=7).resid.dropna()
m = r[r.abs() > 3 * r.std()]
assert list(need('outliers')) == [t.date() for t in m.index], f'outliers = {need("outliers")}, а нужно {[t.date() for t in m.index]}.'
assert list(need('kinds')) == ['всплеск' if v > 0 else 'провал' for v in m.values], f'kinds = {need("kinds")}.'
```

### hint
`r = parts.resid.dropna()`, маска `r.abs() > 3 * r.std()`.

### hint
Даты аномалий — индекс отобранных значений: `r[mask].index`; для красоты — `.date`.

### solution
```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
daily = s.resample("D").sum()

r = seasonal_decompose(daily, model="additive", period=7).resid.dropna()
big = r[r.abs() > 3 * r.std()]
outliers = [t.date() for t in big.index]
kinds = ["всплеск" if v > 0 else "провал" for v in big.values]
```

### explain
Правило «три стандартных отклонения» поймало и акции, и сбой. Обратите внимание: акции сами «раздувают» стандартное отклонение остатка, поэтому часть из них может не пройти порог. Устойчивее брать медиану абсолютных отклонений (MAD), но идея та же — искать аномалии в остатке, а не в самом ряде, где их маскируют тренд и сезонность.
