---
title: "Прогноз: ориентиры, горизонт и метрики"
files: [app_orders.csv]
lead: "Прежде чем хвалить модель, сравните её с простыми прогнозами вроде «как неделю назад» — у рядов они бывают пугающе сильными. Разбираемся с метриками прогноза, с тем, почему MAPE ломается на нулях, и с горизонтом: прогноз на час вперёд и на завтра — разные задачи с разными признаками."
recap:
  - "Наивные прогнозы: «как час назад», «как вчера в этот час», «как неделю назад», «среднее за этот час в 4 прошлые недели». Модель должна их обгонять."
  - "MAE — средняя ошибка в штуках, RMSE — сильнее штрафует большие промахи, WAPE = сумма |ошибок| / сумма факта — доля в процентах, не ломается на нулях."
  - "MAPE (средняя ошибка в процентах по строкам) делит на факт и взрывается при нулевых значениях — для рядов с нулями не годится."
  - "Горизонт прогноза определяет признаки: на час вперёд можно взять лаг 1, на завтра с отсечкой в полночь — только лаги от 24, с решением в 20:00 — от 28."
  - "Хороший наивный прогноз полезно добавить в модель признаком — модель будет его уточнять."
---

## Наивные прогнозы

У временного ряда есть естественные «глупые» прогнозы, и с ними обязательно сравнивают любую модель:

- **как час назад** — `s.shift(1)`;
- **как вчера в этот час** — `s.shift(24)`;
- **как неделю назад в этот час** — `s.shift(168)`;
- **среднее за этот час в 4 прошлые недели** — сглаживает случайности одной недели.

```python
import numpy as np
import pandas as pd

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s.loc[:"2026-07-31"]
test = s["2026-07-01":]

def rmse(pred):
    return float(np.sqrt(((test - pred[test.index]) ** 2).mean()))

naive = {
    "час назад": s.shift(1),
    "вчера": s.shift(24),
    "неделю назад": s.shift(168),
    "среднее за 4 недели": pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1),
}
for name, pred in naive.items():
    print(f"{name:>20}: RMSE {rmse(pred):.2f}")
```

**Что здесь происходит:**

- `test = s["2026-07-01":]` — июльская валидация. Август оставляем для финального проекта.
- Каждый наивный прогноз — это просто сдвинутый ряд: в строке «12:00 18 июля» у `s.shift(168)` стоит значение «12:00 11 июля».
- `pred[test.index]` — берём прогнозы только для часов теста.
- `pd.concat([...], axis=1).mean(axis=1)` — четыре сдвинутых ряда ставим рядом столбцами и усредняем по строке: среднее «этого часа» за 4 прошлые недели.

Для субботы 18 июля в 12:00 факт составил 14 заказов. В таблице одна колонка описывает этот час, другая — все часы июльской проверки.

| Способ | Прогноз на этот час, заказов | RMSE за июль, заказов в час |
|---|---:|---:|
| Час назад | 19 | 5,58 |
| Вчера в тот же час | 10 | 5,73 |
| Неделю назад | 14 | 5,30 |
| Среднее четырёх прошлых недель | 19 | 4,24 |

В выбранный час недельный лаг попал точно. По всему июлю среднее четырёх недель даёт меньшую ошибку. Поэтому ориентир выбирают по всему заранее выделенному периоду.

::: quiz
Представьте другой сервис с одинаковым горизонтом и одними часами проверки. У бустинга RMSE 3,41 заказа в час, у простого недельного среднего — 3,46. Какой вывод разумен?

- [x] Модель почти ничего не добавила к «как обычно в это время»; её ценность измеряют именно приростом над таким ориентиром
  > Без сравнения с наивным прогнозом 3,41 выглядело бы как успех модели, хотя основную работу делает сезонность.
- [ ] Бустинг лучше — значит, всё в порядке, сравнение с наивным прогнозом лишнее
  > Разница меньше десятой доли заказа: стоит ли модель своей сложности, видно только рядом с простым ориентиром.
- [ ] Наивный прогноз нечестный: он подглядывает в будущее
  > «Среднее за 4 прошлые недели» строится из сдвигов на 168 часов и больше — только из прошлого, это законный прогноз.
- [ ] Наивный прогноз не может быть так близок к модели — где-то ошибка в расчёте
  > У рядов с сильной сезонностью это обычная картина: «как обычно в это время» уже хороший прогноз.
:::

{{practice: naive, mean4w}}

## Какой метрикой мерить

- **MAE** — средняя абсолютная ошибка, в заказах: «в среднем ошибаемся на 3 заказа в час». Понятна бизнесу.
- **RMSE** — корень из среднего квадрата ошибки. Сильнее наказывает большие промахи, поэтому всегда ≥ MAE. Удобна, когда один большой промах хуже нескольких маленьких (не хватило рук в пик).
- **MAPE** — средняя ошибка в процентах по каждой строке: $\dfrac{|\text{факт} - \text{прогноз}|}{\text{факт}}$. Кажется понятной, но ночью заказов 0 или 1 — и деление на ноль или на единицу превращает ошибку в бесконечность или в 300 %.
- **WAPE** — сумма абсолютных ошибок, делённая на сумму факта: $\dfrac{\sum |\text{факт} - \text{прогноз}|}{\sum \text{факт}}$. Тоже проценты, но «взвешенные»: часы с большим числом заказов весят больше, нули не мешают.

```python
import numpy as np
import pandas as pd

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s.loc[:"2026-07-31"]
test = s["2026-07-01":]
pred = s.shift(168)[test.index]
err = test - pred
print("MAE: ", round(float(err.abs().mean()), 2))
print("RMSE:", round(float(np.sqrt((err ** 2).mean())), 2))
print("WAPE:", round(float(err.abs().sum() / test.sum()), 3))
print("часов с нулём в тесте:", int((test == 0).sum()))
```

Посчитаем все три метрики руками на трёх часах: факт 10, 0, 20; прогноз 12, 1, 18. Ошибки: −2, −1, +2.

- MAE = (2 + 1 + 2) / 3 ≈ **1.67** заказа;
- RMSE $= \sqrt{(4 + 1 + 4) / 3} = \sqrt{3} \approx$ **1.73** — чуть больше MAE, потому что крупные ошибки весят больше;
- MAPE = (2/10 + 1/0 + 2/20) / 3 — **не считается**: во втором часу деление на ноль;
- WAPE = (2 + 1 + 2) / (10 + 0 + 20) = 5 / 30 ≈ **0.17**.

::: figure ts-metrics-toy
Те же три часа таблицей: одни и те же ошибки сводятся в число четырьмя способами. MAPE ломается на часе с нулём заказов, WAPE делит сумму ошибок на сумму факта и не ломается.
:::

**Что здесь происходит в коде:**

- `err = test - pred` — ошибка по каждому часу (Series).
- `err.abs().mean()` — MAE; `np.sqrt((err ** 2).mean())` — RMSE; `err.abs().sum() / test.sum()` — WAPE.

В тесте есть часы с нулём заказов — на них MAPE не посчитать вовсе. WAPE около 0,376: наивный прогноз «как неделю назад» в сумме ошибается на 37,6 % суммарного числа заказов.

::: predict
```python static
import numpy as np
fact = np.array([10, 0, 20])
pred = np.array([12, 1, 18])
print(round(float(np.abs(fact - pred).sum() / fact.sum()), 2))
```

- `0.2`
- [x] `0.17`
- `inf`

Почему: сумма ошибок 2 + 1 + 2 = 5, сумма факта 30, WAPE = 5 / 30 ≈ 0.17. MAPE для второй строки делил бы на ноль.
:::

::: quiz
Почему MAPE плохо подходит для часовых заказов, где ночью бывают нули?

- [x] MAPE делит ошибку на факт: при нуле заказов процент не определён, а при одном заказе ошибка в два заказа даёт 200 %
  > WAPE делит сумму ошибок на сумму фактов, и маленькие часы не раздувают её.
- [ ] MAPE не учитывает знак ошибки
  > MAE тоже не учитывает — дело не в этом.
- [ ] MAPE слишком сложно считать
  > Считать просто, проблема в делении на маленькие числа.
- [ ] MAPE всегда больше 100 %
  > Нет: обычно он меньше, но ночные часы его раздувают.
:::

::: warn Типичные ошибки
- **Сравнивать метрики на разных периодах.** Вычисляйте их для модели и ориентира на одних часах и с одинаковым горизонтом. Так изменение состава выборки не повлияет на сравнение.
- **MAPE на ряду с нулями.** Деление на ноль даёт `inf`, а ночной час с одним заказом раздувает среднее. Для таких рядов — WAPE или MAE.
- **Одна метрика без знака ошибки.** MAE и RMSE не говорят, в какую сторону ошибается модель. Средняя ошибка со знаком `(факт − прогноз).mean()` показывает систематический недопрогноз (задача «Систематический недопрогноз»).
:::

{{practice: metrics, wape, bias, by-hour-error}}

## Горизонт прогноза

Что значит «прогноз»? Если управляющему нужно знать, сколько будет заказов **в следующий час** (вызвать ли второго бариста с перерыва), — горизонт 1 час, и признак «час назад» законен. Если график смен составляется **в конце дня, около полуночи**, на весь завтрашний день, горизонт до 24 часов: для 18:00 завтра значения за 17:00 завтра ещё нет. Тогда лаг 1 — утечка, и годятся только лаги ≥ 24. Если же решение принимают раньше, например в 20:00, горизонт длиннее, и законных лагов ещё меньше — это случай на рисунке ниже, подробно — в разделе «Разберём вместе».

::: figure ts-horizon
Прогноз «на завтра» с решением в 20:00. Для 23:00 завтра лаг 24 указывает на 23:00 сегодня — этого часа в момент решения ещё нет; лаг 48 указывает на вчера — он законен.
:::

::: tip Аналогия
Горизонт — как разница между «долить молоко в питчер сейчас» и «вечером заказать молоко на завтра у поставщика». Для питчера бариста смотрит на очередь у стойки — самые свежие данные; для заказа на завтра завтрашней очереди ещё не видно, и опираться приходится на сегодняшние продажи и тот же день прошлой недели. Только бариста и так знает, когда принимает решение, а для модели момент прогноза надо записать явно — иначе лаг «из будущего» незаметно попадёт в признаки.
:::

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s.loc[:"2026-07-31"]

def make(s, lags, roll_shift):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    for k in lags:
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(roll_shift).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()

for name, lags, roll_shift in [("на час вперёд", (1, 24, 168), 1), ("на завтра", (24, 48, 168), 24)]:
    df = make(s, lags, roll_shift)
    train = df.index < "2026-07-01"
    X, y = df.drop(columns="y"), df["y"]
    p = LinearRegression().fit(X[train], y[train]).predict(X[~train])
    print(f"{name}: RMSE {np.sqrt(((y[~train] - p) ** 2).mean()):.2f}")
```

**Что здесь происходит:**

- `make(s, lags, roll_shift)` строит таблицу признаков под нужный горизонт: набор лагов и сдвиг скользящего среднего — параметры.
- Для горизонта «на час» — лаги 1, 24, 168 и среднее за сутки, сдвинутое на 1 час. Для горизонта «на завтра» — лаги не короче 24 часов (24, 48, 168) и среднее, сдвинутое на 24 часа: в момент прогноза (полночь) завтрашних часов ещё нет. В этом разделе и в задачах урока отсечка — полночь, поэтому лаг 24 законен.
- `mean4w` — наивный прогноз как признак: его можно посчитать заранее на любой день вперёд в пределах недели.

На июльской валидации эта линейная модель даёт примерно 3,95 заказа в час при прогнозе на час и 4,13 при выпуске в полночь на завтра. Для второго горизонта часть свежих фактов ещё недоступна.

::: deep Рекурсивный прогноз
Ещё один способ прогнозировать на много шагов: обучить модель на час вперёд и применять её по очереди — спрогнозировали 00:00, подставили прогноз как «лаг 1» для 01:00 и так далее. Это **рекурсивный** прогноз; ошибки в нём накапливаются. Подход из примера выше — отдельная модель с подходящими лагами — называется **прямым**.
:::

{{practice: p-horizon, horizon-gap, leak-horizon}}

## Разберём вместе: как выбрать горизонт и признаки

Практическое правило в виде вопросов, которые задают заказчику **до** построения признаков:

1. **Когда принимается решение?** «Накануне в 20:00» — значит, данные есть до 19:59 вчерашнего дня.
2. **На какой период?** «Весь завтрашний день, по часам». Горизонт считаем от **последнего часа с данными**, а не от момента решения: в 20:00 последний известный час — 19:00. Тогда полночь — через 5 часов, а 23:00 завтра — через 28. Горизонт — от 5 до 28 часов.
3. **Какой самый короткий лаг законен для самого дальнего часа?** Лаг k в строке «час t» указывает на час t − k; он законен, если t − k не позже 19:00 сегодня, то есть k не меньше горизонта этого часа. Для полуночи нужен лаг ≥ 5, для 23:00 завтра — ≥ 28. Одна модель на весь завтрашний день берёт лаги, законные для самого дальнего часа: ≥ 28. Лаг 24 законен лишь для часов до 19:00 завтра включительно.

Обычно упрощают: берут лаги, кратные суткам и не короче горизонта (48, 168, …), или прогнозируют «на завтра» с отсечкой в полночь (лаги ≥ 24 — если расписание составляют в самом конце дня). Главное — ответить на эти вопросы явно и записать: в проекте главы именно с этого начинается работа.

::: warn Типичные ошибки
- **Признаки под горизонт «на час», а прогноз нужен на завтра.** Модель с `lag_1` на тесте выглядит отлично, но в работе в 20:00 значения «час назад» для завтрашних часов просто нет — модель не запустится или получит пропуски.
- **Скользящее среднее со сдвигом 1 при горизонте в сутки.** `s.shift(1).rolling(24)` для завтрашних часов тоже заглядывает в неизвестное. Сдвиг окна должен быть не меньше горизонта: `s.shift(24).rolling(24)` или больше.
- **Горизонт «в голове», а не в коде.** Запишите момент прогноза и горизонт в начале ноутбука и проверьте каждый признак: можно ли посчитать его в момент прогноза для самого дальнего часа.
:::

::: predict
```python static
horizon_hours = 28
lags = [1, 24, 48, 168]
print([k for k in lags if k >= horizon_hours])
```

- `[24, 48, 168]`
- [x] `[48, 168]`
- `[1, 24, 48, 168]`

Почему: для самого дальнего часа (23:00 завтра — 28 часов после последнего известного часа 19:00) лаги 1 и 24 указывают на часы, которых в момент прогноза ещё нет. Законны только лаги не короче горизонта.
:::

Для среднего по четырём неделям заранее задайте поведение короткой истории: если нужны все четыре сопоставимых часа, при нехватке истории результат отсутствует и используется явно выбранный резерв. Среднее по одному доступному часу не называют средним четырёх недель. Окно и резерв выбираются на раннем периоде.

## Практика

## task: naive | Наивные прогнозы | warmup

Посчитайте на июльской валидации MAE трёх наивных прогнозов: `s.shift(1)`, `s.shift(24)`, `s.shift(168)`. Сохраните словарь `mae` (`{1: ..., 24: ..., 168: ...}`, 3 знака) и `best_lag`.

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]
```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']; s0 = s0[s0.index < '2026-08-01']; t = s0['2026-07-01':]
s0 = s0[s0.index < '2026-08-01']
w = {k: round(float((t - s0.shift(k)[t.index]).abs().mean()), 3) for k in (1, 24, 168)}
got = need('mae', dict)
assert all(k in got and close(got[k], v, 0.002) for k, v in w.items()), f'mae = {got}, а нужно {w}.'
assert need('best_lag') == min(w, key=w.get), f'best_lag = {need("best_lag")}.'
```

### hint
Прогноз на тест: `s.shift(k)[test.index]`.

### hint
MAE одного прогноза: `(test - pred).abs().mean()`; удобно написать функцию `mae_of(pred)` и вызвать её для трёх сдвигов.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]
mae = {k: round(float((test - s.shift(k)[test.index]).abs().mean()), 3) for k in (1, 24, 168)}
best_lag = min(mae, key=mae.get)
```

## task: metrics | Метрики своими руками | warmup

Напишите функции `mae(fact, pred)`, `rmse(fact, pred)` и `wape(fact, pred)` для массивов numpy. Посчитайте их для `fact` и `pred` из заготовки: `m` — словарь `{"mae": …, "rmse": …, "wape": …}` (3 знака).

### setup
```python
import numpy as np
fact = np.array([10, 0, 20, 14, 6])
pred = np.array([12, 1, 18, 9, 6])
```

### starter
```python
import numpy as np

def mae(fact, pred):
    ...

def rmse(fact, pred):
    ...

def wape(fact, pred):
    ...
```

### check
```python
import numpy as _np
a, b = _np.array([3.0, 5.0]), _np.array([1.0, 5.0])
assert close(need('mae')(a, b), 1.0) and close(need('rmse')(a, b), _np.sqrt(2)) and close(need('wape')(a, b), 0.25), 'Проверьте формулы на [3, 5] и [1, 5]: MAE 1, RMSE √2, WAPE 2/8.'
f, p = need('fact'), need('pred')
w = {'mae': round(float(_np.abs(f - p).mean()), 3), 'rmse': round(float(_np.sqrt(((f - p) ** 2).mean())), 3), 'wape': round(float(_np.abs(f - p).sum() / f.sum()), 3)}
g = need('m', dict)
assert all(close(g[k], w[k], 0.0011) for k in w), f'm = {g}, а нужно {w}.'
```

### hint
Ошибка — `fact - pred`. MAE — среднее модулей, RMSE — корень из среднего квадратов, WAPE — сумма модулей / сумма факта.

### hint
`np.abs(e).mean()`, `np.sqrt((e ** 2).mean())`, `np.abs(e).sum() / fact.sum()`.

### solution
```python
import numpy as np

def mae(fact, pred):
    return float(np.abs(fact - pred).mean())

def rmse(fact, pred):
    return float(np.sqrt(((fact - pred) ** 2).mean()))

def wape(fact, pred):
    return float(np.abs(fact - pred).sum() / fact.sum())

m = {"mae": round(mae(fact, pred), 3), "rmse": round(rmse(fact, pred), 3), "wape": round(wape(fact, pred), 3)}
print(m)
```

## task: wape | WAPE против MAPE | warmup

Напишите функцию `wape(fact, pred)`. Для прогноза «неделю назад» на июле сохраните `w` (3 знака) и `zeros` — число часов теста с нулевым фактом (на них MAPE не определена).

### starter
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]
pred = s.shift(168)[test.index]
```

### check
```python
import numpy as _np, pandas as _pd
f = need('wape')
assert close(f(_np.array([10, 0, 20]), _np.array([12, 1, 18])), 5 / 30), 'wape([10, 0, 20], [12, 1, 18]) должна быть 5/30.'
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']; s0 = s0[s0.index < '2026-08-01']; t = s0['2026-07-01':]; p = s0.shift(168)[t.index]
s0 = s0[s0.index < '2026-08-01']
assert close(need('w'), round(float((t - p).abs().sum() / t.sum()), 3), 0.002), f'w = {need("w")}.'
assert need('zeros') == int((t == 0).sum()), f'zeros = {need("zeros")}.'
```

### hint
WAPE — сумма модулей ошибок, делённая на сумму факта; MAPE — среднее отношений |ошибка| / факт по строкам.

### hint
`return np.abs(fact - pred).sum() / fact.sum()` (или через методы pandas).

### solution
```python
import numpy as np
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]
pred = s.shift(168)[test.index]

def wape(fact, pred):
    return np.abs(fact - pred).sum() / fact.sum()

w = round(float(wape(test, pred)), 3)
zeros = int((test == 0).sum())
```

## task: p-horizon | Признаки на завтра | warmup

Соберите признаки для прогноза на сутки вперёд (только лаги от 24) и напечатайте их названия.

### parsons
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = pd.DataFrame({"y": s})
for k in (24, 48, 168):
    df[f"lag_{k}"] = s.shift(k)
df["roll"] = s.shift(24).rolling(24).mean()
print(list(df.columns[1:]))
```

### check
```python
assert _lines == ["['lag_24', 'lag_48', 'lag_168', 'roll']"], f'Сейчас: {_lines}.'
```

### hint
Сначала таблица с ответом, потом лаги в цикле, потом скользящее среднее.

### hint
Для прогноза на завтра скользящее среднее сдвигают на 24 часа: `s.shift(24).rolling(24).mean()`.

## task: bias | Систематический недопрогноз | base

У прогноза бывает не только разброс, но и **смещение** — средняя ошибка со знаком. Для прогноза «среднее за 4 недели» (`m4` в заготовке) на июле посчитайте `bias` — среднюю ошибку `факт − прогноз` (3 знака), `share_under` — долю часов, где прогноз меньше факта (3 знака), и `ratio` — сумма факта / сумма прогноза (3 знака). В заготовке есть и поправленный прогноз `adj`: `m4`, умноженный на коэффициент `_k` — во сколько раз факт за последнюю неделю выше прогноза `m4` за ту же неделю. Если прогноз отстаёт от роста, `_k > 1` и подтягивает его вверх. Для `adj` — посчитайте для него `bias_adj` и сравните RMSE: `rmse_m4`, `rmse_adj` (3 знака).

### setup
```python
import numpy as np
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]
_m4 = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
m4 = _m4[test.index]
# _k: средний факт за последнюю неделю / средний прогноз m4 за ту же неделю (shift(1) — только прошлое)
_k = s.rolling(168).mean().shift(1) / _m4.rolling(168).mean().shift(1)
adj = m4 * _k[test.index]
```

### starter
```python
import numpy as np
```

### check
```python
import numpy as _np
t, a, b = need('test'), need('m4'), need('adj')
e, e2 = t - a, t - b
assert close(need('bias'), round(float(e.mean()), 3), 0.0011), f'bias = {need("bias")}.'
assert close(need('share_under'), round(float((a < t).mean()), 3), 0.0011), f'share_under = {need("share_under")}.'
assert close(need('ratio'), round(float(t.sum() / a.sum()), 3), 0.0011), f'ratio = {need("ratio")}.'
assert close(need('bias_adj'), round(float(e2.mean()), 3), 0.0011), f'bias_adj = {need("bias_adj")}.'
assert close(need('rmse_m4'), round(float(_np.sqrt((e ** 2).mean())), 3), 0.0011) and close(need('rmse_adj'), round(float(_np.sqrt((e2 ** 2).mean())), 3), 0.0011), 'rmse_m4, rmse_adj — RMSE двух прогнозов.'
```

### hint
Смещение — `(test - m4).mean()`: положительное значит, что прогноз в среднем ниже факта.

### hint
Доля недопрогноза — `(m4 < test).mean()`; отношение сумм — `test.sum() / m4.sum()`.

### hint
Те же формулы для `adj`; RMSE — `np.sqrt(((test - pred) ** 2).mean())`.

### solution
```python
import numpy as np

e = test - m4
bias = round(float(e.mean()), 3)
share_under = round(float((m4 < test).mean()), 3)
ratio = round(float(test.sum() / m4.sum()), 3)
e2 = test - adj
bias_adj = round(float(e2.mean()), 3)
rmse_m4 = round(float(np.sqrt((e ** 2).mean())), 3)
rmse_adj = round(float(np.sqrt((e2 ** 2).mean())), 3)
print(bias, share_under, ratio, bias_adj, rmse_m4, rmse_adj)
```

### explain
В июле средняя ошибка со знаком равна +0,406 заказа в час. Отношение суммарного факта к прогнозу — 1,044. Поправка по предыдущей неделе уменьшает среднюю ошибку до −0,044, но увеличивает RMSE с 4,239 до 4,271. Выбор зависит от принятой меры потерь.

Недопрогноз возник в 49,6 % часов. Его доля и сумма нехватки отвечают на разные вопросы: вклад часа с недостачей десяти заказов больше вклада часа с недостачей одного.

## task: mean4w | Сильный наивный прогноз | base

Постройте прогноз «среднее за этот час в k прошлых недель» для k = 1, 2, 4, 8 и посчитайте RMSE на июле. Сохраните словарь `rmse_k` (3 знака) и `best_k`. Нужная история для k = 8 есть: к началу июля уже есть история для восьми недель.

### starter
```python
import numpy as np
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]
```

### check
```python
import numpy as _np, pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']; s0 = s0[s0.index < '2026-08-01']; t = s0['2026-07-01':]
s0 = s0[s0.index < '2026-08-01']
w = {}
for k in (1, 2, 4, 8):
    p = _pd.concat([s0.shift(168 * j) for j in range(1, k + 1)], axis=1).mean(axis=1)
    w[k] = round(float(_np.sqrt(((t - p[t.index]) ** 2).mean())), 3)
got = need('rmse_k', dict)
assert all(k in got and close(got[k], v, 0.002) for k, v in w.items()), f'rmse_k = {got}, а нужно {w}.'
assert need('best_k') == min(w, key=w.get), f'best_k = {need("best_k")}.'
```

### hint
Среднее за k прошлых недель — это k сдвинутых рядов (`s.shift(168)`, `s.shift(336)`, …), усреднённых по строке.

### hint
`pd.concat([s.shift(168 * j) for j in range(1, k + 1)], axis=1).mean(axis=1)`.

### solution
```python
import numpy as np
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
test = s["2026-07-01":]

rmse_k = {}
for k in (1, 2, 4, 8):
    pred = pd.concat([s.shift(168 * j) for j in range(1, k + 1)], axis=1).mean(axis=1)
    rmse_k[k] = round(float(np.sqrt(((test - pred[test.index]) ** 2).mean())), 3)
best_k = min(rmse_k, key=rmse_k.get)
```

### explain
При окнах 1, 2, 4 и 8 недель июльский RMSE равен примерно 5,301, 4,535, 4,239 и 4,089. На июльской проверке лучшим оказалось окно в восемь недель. Зафиксируйте выбор до оценки на следующем месяце.

## task: horizon-gap | Цена горизонта | base

Сравните бустинг `HistGradientBoostingRegressor(random_state=0)` для двух горизонтов на признаках из теории (функция `make` в заготовке): на час вперёд и на завтра. Здесь, как в теории, отсечка — полночь, поэтому лаг 24 для завтрашних часов законен; с решением в 20:00 разберёмся в проекте главы. Сохраните `rmse_hour`, `rmse_day` (3 знака) и `gap_pct` — на сколько процентов RMSE на завтра больше (1 знак).

### setup
```python
import pandas as pd
def make(s, lags, roll_shift):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    for k in lags:
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(roll_shift).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
```

### starter
```python
# уже есть: make(s, lags, roll_shift) из теории
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
s0 = s0[s0.index < '2026-08-01']
w = {}
for k, lags, rs in [('h', (1, 24, 168), 1), ('d', (24, 48, 168), 24)]:
    d = make(s0, lags, rs); tr = d.index < '2026-07-01'; X, y = d.drop(columns='y'), d['y']
    p = _H(random_state=0).fit(X[tr], y[tr]).predict(X[~tr]); w[k] = float(_np.sqrt(((y[~tr] - p) ** 2).mean()))
assert close(need('rmse_hour'), round(w['h'], 3), 0.002) and close(need('rmse_day'), round(w['d'], 3), 0.002), f'rmse_hour, rmse_day = {need("rmse_hour")}, {need("rmse_day")}.'
assert close(need('gap_pct'), round((w['d'] / w['h'] - 1) * 100, 1), 0.15), f'gap_pct = {need("gap_pct")}.'
```

### hint
Как в теории, только модель — бустинг.

### hint
Функция `make` из теории принимает набор лагов и сдвиг среднего; два вызова — для часа вперёд и для завтра.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']

res = {}
for name, lags, roll_shift in [("hour", (1, 24, 168), 1), ("day", (24, 48, 168), 24)]:
    df = make(s, lags, roll_shift)
    train = df.index < "2026-07-01"
    X, y = df.drop(columns="y"), df["y"]
    p = HistGradientBoostingRegressor(random_state=0).fit(X[train], y[train]).predict(X[~train])
    res[name] = float(np.sqrt(((y[~train] - p) ** 2).mean()))
rmse_hour, rmse_day = round(res["hour"], 3), round(res["day"], 3)
gap_pct = round((res["day"] / res["hour"] - 1) * 100, 1)
```

### explain
В июле RMSE бустинга вырос с 4,160 для часового горизонта до 4,366 для выпуска в полночь на завтра. Для всех часов завтрашнего дня можно использовать лаг 24. Лаг 1 оказался бы неизвестен при выпуске для большинства этих часов.

## task: leak-horizon | Утечка из-за горизонта | plus

Проверьте, что будет, если для прогноза «на завтра» (отсечка — полночь, как в теории) по ошибке оставить лаг 1. Обучите `LinearRegression` на признаках `make(s, (1, 24, 48, 168), 1)` и на честных `make(s, (24, 48, 168), 24)`. Сохраните `rmse_leak`, `rmse_fair` (3 знака) и `fooled` — `True`, если «прогноз с утечкой» выглядит лучше.

### setup
```python
import pandas as pd
def make(s, lags, roll_shift):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    for k in lags:
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(roll_shift).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
```

### starter
```python
# уже есть: make(s, lags, roll_shift)
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
s0 = s0[s0.index < '2026-08-01']
w = {}
for k, lags, rs in [('leak', (1, 24, 48, 168), 1), ('fair', (24, 48, 168), 24)]:
    d = make(s0, lags, rs); tr = d.index < '2026-07-01'; X, y = d.drop(columns='y'), d['y']
    p = _LR().fit(X[tr], y[tr]).predict(X[~tr]); w[k] = round(float(_np.sqrt(((y[~tr] - p) ** 2).mean())), 3)
assert close(need('rmse_leak'), w['leak'], 0.002) and close(need('rmse_fair'), w['fair'], 0.002), f'rmse_leak, rmse_fair = {need("rmse_leak")}, {need("rmse_fair")}, а нужно {w["leak"]}, {w["fair"]}.'
assert need('fooled') == (w['leak'] < w['fair']), f'fooled = {need("fooled")}.'
```

### hint
Две таблицы через `make`, две модели, два RMSE.

### hint
Утечка возникает, если для прогноза «на завтра» оставить лаг 1 или среднее, сдвинутое на 1 час: такие признаки в момент прогноза недоступны.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']

res = {}
for name, lags, roll_shift in [("leak", (1, 24, 48, 168), 1), ("fair", (24, 48, 168), 24)]:
    df = make(s, lags, roll_shift)
    train = df.index < "2026-07-01"
    X, y = df.drop(columns="y"), df["y"]
    p = LinearRegression().fit(X[train], y[train]).predict(X[~train])
    res[name] = round(float(np.sqrt(((y[~train] - p) ** 2).mean())), 3)
rmse_leak, rmse_fair = res["leak"], res["fair"]
fooled = rmse_leak < rmse_fair
```

### explain
С лагом 1 прогноз «на завтра» выглядит лучше — но в реальности вечером накануне значения «час назад» для завтрашних часов нет. Модель с утечкой на бумаге выигрывает, а в работе её просто нечем будет кормить. Горизонт определяет, какие признаки законны, — это нужно решить до обучения.

## task: by-hour-error | Где модель ошибается | star

Для честного прогноза «на завтра» с отсечкой в полночь (`LinearRegression`, признаки `make(s, (24, 48, 168), 24)`) посчитайте MAE по часам суток на тесте. Сохраните Series `mae_by_hour` (индекс 0–23, 2 знака), `worst_hour` и `night_share` — долю суммарной абсолютной ошибки, приходящуюся на часы 0–5 (3 знака).

### setup
```python
import pandas as pd
def make(s, lags, roll_shift):
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    for k in lags:
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(roll_shift).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna()
```

### starter
```python
# уже есть: make(s, lags, roll_shift)
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
s0 = s0[s0.index < '2026-08-01']
d = make(s0, (24, 48, 168), 24); tr = d.index < '2026-07-01'; X, y = d.drop(columns='y'), d['y']
e = (y[~tr] - _LR().fit(X[tr], y[tr]).predict(X[~tr])).abs()
mh = e.groupby(e.index.hour).mean()
got = need('mae_by_hour', _pd.Series)
assert all(close(got[h], round(mh[h], 2), 0.006) for h in range(24)), 'MAE по часам не совпадает.'
assert need('worst_hour') == int(mh.idxmax()), f'worst_hour = {need("worst_hour")}.'
assert close(need('night_share'), round(e[e.index.hour <= 5].sum() / e.sum(), 3), 0.002), f'night_share = {need("night_share")}.'
```

### hint
Ошибки — Series с индексом-временем: `(y_test - p).abs()`, затем `groupby(err.index.hour).mean()`.

### hint
Прогноз модели — массив без индекса; чтобы получить Series с датами, оберните: `pd.Series(p, index=y_test.index)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']

df = make(s, (24, 48, 168), 24)
train = df.index < "2026-07-01"
X, y = df.drop(columns="y"), df["y"]
p = LinearRegression().fit(X[train], y[train]).predict(X[~train])
err = (y[~train] - p).abs()
mae_by_hour = err.groupby(err.index.hour).mean().round(2)
worst_hour = int(err.groupby(err.index.hour).mean().idxmax())
night_share = round(err[err.index.hour <= 5].sum() / err.sum(), 3)
```

### explain
Ошибки сосредоточены в пиковые часы — где и заказов больше, и цена ошибки выше. На часы 0–5 приходится меньше 10 % всей ошибки. Отдельный нюанс: линейная модель в принципе может выдать отрицательный прогноз заказов. На практике прогноз обрезают снизу нулём (`np.clip(p, 0, None)`) — и для честности, и для красоты отчёта.
