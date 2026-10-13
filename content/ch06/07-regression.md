---
title: "Регрессия: сколько минут"
lead: "«Опоздает или нет» — грубый ответ. Гостю полезнее услышать «привезём примерно через 42 минуты». Предсказываем число — фактическое время доставки: линейная регрессия, дерево и лес для чисел, метрики MAE, RMSE и R², разбор ошибок. И увидим, где машинное обучение наконец заметно обгоняет правило аналитика."
files: [deliveries.csv]
recap:
  - "Регрессия предсказывает число. Базовая модель — всегда отвечать медианой (или средним) обучающей выборки."
  - "`LinearRegression`: прогноз = `intercept_` + Σ `coef_` · признак. Вес расстояния — «сколько минут добавляет километр при прочих равных»."
  - "`DecisionTreeRegressor` и `RandomForestRegressor` отвечают средним по похожим объектам и сами ловят взаимодействия признаков (пеший × расстояние)."
  - "MAE — средняя ошибка в минутах: `mean_absolute_error`. RMSE — `mean_squared_error(...) ** 0.5`, сильнее штрафует крупные промахи."
  - "R² (`r2_score`) — какая доля разброса объяснена: 1 — идеально, 0 — не лучше среднего, меньше 0 — хуже среднего."
  - "Остаток = факт − прогноз. График «факт против прогноза» и таблица крупнейших ошибок показывают, где модель ошибается."
  - "Регрессию можно превратить в классификацию: «прогноз минут > обещания» — значит, опоздание."
---

## Предсказываем число

Целевой признак теперь — `actual_min`, фактическое время доставки в минутах. Признаки те же, что и для опозданий: всё, что известно до отправки курьера. Это **регрессия** (урок «Что такое машинное обучение»): ответ — число, а не категория.

Сначала — базовая модель. Для средней абсолютной ошибки лучший постоянный ответ — медиана, а не среднее: в задаче «Регрессия: базовая модель» урока «Что такое машинное обучение» медиана давала MAE 8.10 против 8.23 у среднего. Считаем её **только по обучающей части**: тест — это «будущее», которого мы не видели.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

base = y_train.median()
pred_base = [base] * len(y_test)
print(f"медиана train: {base} мин")
print(f"MAE базовой модели: {mean_absolute_error(y_test, pred_base):.1f} мин")
```

**MAE** (mean absolute error, средняя абсолютная ошибка) — среднее модулей «факт − прогноз», та же формула, что в уроке «Что такое машинное обучение», только готовой функцией `mean_absolute_error(факт, прогноз)`. Читается просто: «в среднем ошибаемся на 8 минут». Это планка, которую должна побить модель.

## Линейная регрессия

**Линейная регрессия** (linear regression) — это знакомая по логистической регрессии (урок «Логистическая регрессия и вероятности») линейная оценка, только без сигмоиды: $\text{прогноз минут} = b_0 + w_1 x_1 + w_2 x_2 + \ldots$ Веса подбираются так, чтобы прогнозы были как можно ближе к фактам (точнее, чтобы сумма квадратов ошибок была наименьшей). Начнём с одного признака — расстояния:

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

lin = LinearRegression().fit(ok[["distance_km"]], ok["actual_min"])
print(f"минуты ≈ {lin.intercept_:.1f} + {lin.coef_[0]:.2f} × км")

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.scatter(ok["distance_km"], ok["actual_min"], s=6, alpha=0.4)
km = pd.DataFrame({"distance_km": [0, 15]})
ax.plot(km["distance_km"], lin.predict(km), color="black")
ax.set_xlabel("расстояние, км")
ax.set_ylabel("минут")
ax.set_title("Время доставки и расстояние")
```

- `intercept_` — свободный член: около 26 минут «на старте» (сборка заказа, выход курьера);
- `coef_` — веса признаков, по одному на признак. Здесь один вес: около 2.8 минуты на каждый километр.

Обратите внимание: `X` — это таблица (двойные скобки `[["distance_km"]]`), даже если признак один. sklearn всегда ждёт таблицу признаков.

::: sql
В Excel это линия тренда на точечной диаграмме или функция ЛИНЕЙН. Разница в том, что здесь признаков может быть сколько угодно, и модель подберёт вес каждому.
:::

Теперь — все признаки:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

lin = LinearRegression().fit(X_train, y_train)
print(f"MAE: {mean_absolute_error(y_test, lin.predict(X_test)):.2f} мин")
print(pd.Series(lin.coef_, index=X.columns).round(1).sort_values())
```

MAE упала примерно с 8 до 5.5 минуты. Веса читаются в минутах и — как в логистической регрессии — при прочих равных:

- `distance_km` ≈ 3.9 — каждый километр добавляет около 4 минут;
- `items` ≈ 1.7 — каждая позиция в заказе добавляет почти 2 минуты на сборку;
- флаги сравнивают категории между собой: пеший курьер против авто — разница около 18 минут (10.2 − (−8.3)), снег против ясной погоды — около 5 минут.

::: warn
Как и в логистической регрессии, веса флагов одного признака читаются парами: смысл имеет разница весов внутри признака, а не каждый вес отдельно (урок «Логистическая регрессия и вероятности», раздел «Коэффициенты»).
:::

{{practice: p-line, linear, interaction}}

## Как мерить ошибку: MAE, RMSE, R²

Одной метрики мало — каждая отвечает на свой вопрос.

- **MAE** — средняя ошибка в минутах. Понятна заказчику: «ошибаемся в среднем на 5 минут».
- **RMSE** (root mean squared error, корень из средней квадратичной ошибки) — тоже в минутах, но ошибки сначала возводятся в квадрат. Один промах на 20 минут весит как сто промахов на 2 минуты, поэтому RMSE всегда не меньше MAE и сильнее растёт от крупных ошибок. Если опоздание на 20 минут для бизнеса намного хуже двух опозданий по 10 — смотрите на RMSE. В sklearn: `mean_squared_error(факт, прогноз) ** 0.5`.
- **R²** (коэффициент детерминации) — какую долю разброса целевого признака объясняет модель. 1 — идеальный прогноз, 0 — модель не лучше постоянного ответа «среднее», меньше 0 — хуже даже его. `r2_score(факт, прогноз)`. R² удобен, чтобы сравнивать задачи с разными единицами, но заказчику понятнее MAE.

::: predict
```python static
errors = [1, -1, 10]
mae = sum(abs(e) for e in errors) / len(errors)
rmse = (sum(e ** 2 for e in errors) / len(errors)) ** 0.5
print(round(mae, 2), round(rmse, 2))
```

- `4.0 4.0`
- [x] `4.0 5.83`
- `3.33 5.83`

Почему: MAE берёт модули — (1 + 1 + 10) / 3 = 4. RMSE возводит в квадрат — (1 + 1 + 100) / 3 = 34, корень ≈ 5.83. Одна крупная ошибка раздула RMSE заметно сильнее, чем MAE.
:::

::: predict
```python static
from sklearn.metrics import r2_score
print(r2_score([10, 20, 30], [20, 20, 20]))
```

- [x] `0.0`
- `0.5`
- `-1.0`

Почему: прогноз «всегда 20» — это и есть среднее фактов. По определению R² такой модели равен нулю: она ничего не объясняет сверх среднего.
:::

### Разберём вместе: три метрики на четырёх доставках

Факт: 20, 30, 40, 50 минут. Прогноз: 22, 27, 41, 40. Ошибки (факт − прогноз): −2, +3, −1, **+10**.

1. **MAE** = (2 + 3 + 1 + 10) / 4 = **4.0** минуты.
2. **RMSE**: квадраты 4, 9, 1, 100, среднее 114 / 4 = 28.5, корень ≈ **5.34**. Одна ошибка на 10 минут дала 100 из 114 — почти всю сумму.
3. **R²**. Среднее факта — 35. Если бы мы всем отвечали «35», квадраты ошибок были бы 225, 25, 25, 225 — сумма 500. У модели сумма квадратов 114. R² = 1 − 114 / 500 = **0.772**: модель убрала 77 % того разброса, который остался бы при ответе «среднее».

::: figure reg-metrics
Разбор на четырёх доставках. MAE складывает модули ошибок, RMSE — их квадраты (площади), поэтому промах на 10 минут даёт 100 из 114. R² сравнивает сумму квадратов модели с ответом «всегда 35».
:::

::: tip Аналогия
Два курьера опаздывают в сумме на одно и то же время. Первый — каждый день на 5 минут, второй — обычно вовремя, но раз в неделю на 35 минут. MAE у них одинаковая, а гости второго злее: одно большое опоздание запоминается сильнее многих мелких. RMSE ведёт себя как гость — возводит ошибки в квадрат и сильнее наказывает за крупные промахи.
:::

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
fact = [20, 30, 40, 50]
pred = [22, 27, 41, 40]
print(mean_absolute_error(fact, pred), round(mean_squared_error(fact, pred) ** 0.5, 2), round(r2_score(fact, pred), 3))
```

Что получилось: MAE — «насколько ошибаемся обычно», RMSE — «насколько больно от худших промахов», R² — «насколько лучше ответа "среднее"». Разрыв между RMSE и MAE (5.34 против 4.0) — сигнал, что среди ошибок есть крупные: стоит посмотреть, где именно.

::: quiz
У двух моделей MAE одинаковая — 6 минут, но у первой RMSE 8, у второй — 14. Чем они различаются?

- [x] Вторая иногда ошибается очень сильно: RMSE возводит ошибки в квадрат и больше наказывает за крупные промахи
  > При одинаковой средней ошибке большой RMSE означает редкие, но большие промахи. Для доставки это обиженные гости.
- [ ] Вторая модель лучше: RMSE больше
  > Для ошибки «больше» значит «хуже».
- [ ] Ничем, раз MAE одинаковая
  > MAE не различает много мелких ошибок и несколько крупных, RMSE различает.
- [ ] У второй больше данных
  > Метрики не зависят от размера теста так прямо — дело в распределении ошибок.
:::

{{practice: mae-hand, base-median}}

## Дерево и лес для чисел

У деревьев и леса есть версии для регрессии: `DecisionTreeRegressor` и `RandomForestRegressor`. Устроены они так же, как в уроках «Решающее дерево изнутри» и «Случайный лес», но в листе дерево отвечает не самым частым классом, а **средним** целевого признака по обучающим объектам, попавшим в лист. Лес усредняет ответы своих деревьев.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

models = {
    "линейная": LinearRegression(),
    "дерево, глубина 5": DecisionTreeRegressor(max_depth=5, random_state=0),
    "лес, 50 деревьев": RandomForestRegressor(n_estimators=50, random_state=0),
}
pred_base = [y_train.median()] * len(y_test)          # базовая модель: медиана для каждой доставки
rows = [{"модель": "медиана", "MAE": mean_absolute_error(y_test, pred_base),
         "RMSE": mean_squared_error(y_test, pred_base) ** 0.5, "R2": r2_score(y_test, pred_base)}]
for name, m in models.items():
    pred = m.fit(X_train, y_train).predict(X_test)
    rows.append({"модель": name, "MAE": mean_absolute_error(y_test, pred),
                 "RMSE": mean_squared_error(y_test, pred) ** 0.5, "R2": r2_score(y_test, pred)})
print(pd.DataFrame(rows).round(2).to_string(index=False))
```

Лес ошибается в среднем примерно на 4.6 минуты против 5.5 у линейной модели и 8 у медианы, а R² у него около 0.73. У медианы R² чуть ниже нуля: её считали по train, а R² сравнивает со средним теста — постоянный ответ не может быть лучше него. Вот где машинное обучение по-настоящему выигрывает: на опозданиях все модели упирались в правило «пеший — опоздает», а здесь причин много, и они переплетаются.

Почему линейная модель отстаёт? Она даёт **одну** цену километра для всех. Посмотрим, так ли это в данных:

```python
import pandas as pd
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
for courier, part in ok.groupby("courier"):
    m = LinearRegression().fit(part[["distance_km"]], part["actual_min"])
    print(f"{courier}: {m.coef_[0]:.1f} мин на км")
```

Пешему курьеру каждый километр стоит около 13 минут, авто — около 3. Влияние расстояния зависит от типа курьера — это называют **взаимодействием** признаков. Линейная модель сама взаимодействия не видит: она складывает вклады, а не умножает. Дерево и лес ловят их автоматически: сначала спрашивают «пеший?», а потом в каждой ветке по-своему делят по расстоянию.

::: figure interaction-slopes
Отдельная прямая для каждого типа курьера: пешему километр стоит около 13 минут, вело и авто — 3–5. Пунктир — одна прямая по всем доставкам, как в начале урока: одна цена километра для всех.
:::

::: quiz
На одних и тех же признаках лес предсказывает минуты доставки точнее линейной регрессии. В чём главная причина?

- [x] Линейная модель даёт одну цену километра для всех, а у пешего и у авто она разная — лес ловит это взаимодействие сам
  > Линейная модель складывает вклады признаков. Дерево сначала спрашивает «пеший?» и уже внутри ветки по-своему учитывает расстояние.
- [ ] Лес видит признаки, которых нет у линейной модели
  > Таблица признаков у них одна и та же. Различается способ, которым модели их комбинируют.
- [ ] Линейная регрессия годится только для классификации
  > Наоборот, линейная регрессия — модель для чисел. Для классификации у нас была логистическая.
- [ ] Лесу досталось больше обучающих данных
  > Обе модели учились на одном и том же `X_train`. Бутстрэп в лесу перевыбирает те же строки, новых данных он не добавляет.
:::

{{practice: forest-metrics, depth}}

## Разбор ошибок

Средняя метрика скрывает, **где** модель ошибается. **Остаток** (residual) — это факт − прогноз: плюс — доставка шла дольше прогноза, минус — быстрее. Первый взгляд — график «факт против прогноза»: у идеальной модели все точки лежат на диагонали.

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestRegressor(n_estimators=50, random_state=0).fit(X_train, y_train)

res = pd.DataFrame({"fact": y_test, "pred": forest.predict(X_test).round(1)})
res["err"] = res["fact"] - res["pred"]

fig, ax = plt.subplots(figsize=(5, 5))
ax.scatter(res["pred"], res["fact"], s=8, alpha=0.5)
ax.plot([10, 100], [10, 100], color="grey", linestyle="--")
ax.set_xlabel("прогноз, мин")
ax.set_ylabel("факт, мин")
ax.set_title("Лес: факт против прогноза")

res["abs_err"] = res["err"].abs()
worst = res.nlargest(5, "abs_err")
print(worst.join(ok[["courier", "distance_km", "weather", "items", "promised_min"]]).to_string())
```

- `nlargest(5, "abs_err")` — пять строк с самой большой ошибкой по модулю (знак не важен: и «переоценили», и «недооценили» — промахи);
- `join` подтягивает к ошибкам исходные столбцы по индексу — тому же, что был у строк в `ok`.

Что видно:

- облако вытянуто вдоль диагонали — модель в целом понимает, какие доставки долгие;
- самый крупный промах — авто на 15 км: модель ждала больше 70 минут, а доставка заняла 48. Таких дальних заказов в данных единицы, и модели не на чем было учиться;
- пеший курьер на 1.1 км вёз почти час. Ничего в признаках не предвещало такой задержки — это случай, который модель предсказать не может в принципе (курьер заблудился, гость не открыл дверь).

Разбор крупнейших ошибок — обычная работа аналитика после обучения модели: часть промахов подсказывает новые признаки, часть — проблемы в данных, часть — честный шум.

::: tip
Остатки удобно разбивать по группам: `res.join(ok["courier"]).groupby("courier")["err"].mean()`. Если в какой-то группе средний остаток заметно отличается от нуля, модель систематически ошибается на ней.
:::

{{practice: fact-pred, residuals}}

## Опоздание из прогноза минут

Прогноз минут легко превратить в ответ на старый вопрос: если модель ждёт больше минут, чем обещано, — доставка опоздает.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestRegressor(n_estimators=50, random_state=0).fit(X_train, y_train)

late_fact = y_test > X_test["promised_min"]
late_pred = forest.predict(X_test) > X_test["promised_min"]
rule = X_test["courier_пеший"] == 1
print(f"прогноз минут > обещания: {(late_pred == late_fact).mean():.1%}")
print(f"правило «пеший»:          {(rule == late_fact).mean():.1%}")
```

Доля правильных ответов — около 89 %, на уровне классификаторов из прошлых уроков и правила «пеший — опоздает»: как и в уроке «Случайный лес», на вопрос «опоздает или нет» модель почти ничего не добавляет к правилу аналитика. Зато регрессия даёт больше, чем «да/нет»: она говорит, **на сколько** опоздает доставка, — а это можно сообщить гостю.

::: warn Типичные ошибки
- **R² на обучающих данных.** Как и accuracy, на train он завышен — считайте на тесте.
- **Сравнивать MAE разных задач.** «5 минут» для доставки и «5 тысяч» для выручки несравнимы; для сравнения задач — R².
- **Знак остатка.** `err = fact − pred`: плюс — модель занизила (доставка дольше прогноза), минус — завысила.
- **Медиана теста как базовая модель.** Базовый ответ берут из обучающей части, иначе базовая модель подглядывает.
- **Читать вес линейной модели без «при прочих равных».** «18 минут пешему» — при том же расстоянии, позициях и погоде.
:::

{{practice: late-minutes}}

## Практика

## task: mae-hand | MAE и RMSE для пяти доставок | warmup

Модель предсказала время пяти доставок. Посчитайте `mae` и `rmse` (обе — 2 знака) функциями sklearn `mean_absolute_error` и `mean_squared_error`.

### starter
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error
fact = [30, 42, 25, 55, 38]
pred = [33, 40, 25, 45, 36]

```

### check
```python
fact = [30, 42, 25, 55, 38]
pred = [33, 40, 25, 45, 36]
e = [f - p for f, p in zip(fact, pred)]
m = round(sum(abs(x) for x in e) / 5, 2)
r = round((sum(x * x for x in e) / 5) ** 0.5, 2)
assert close(need('mae'), m), f'mae = {need("mae")}, а нужно {m}. Это среднее модулей ошибок.'
assert close(need('rmse'), r), f'rmse = {need("rmse")}, а нужно {r}. RMSE — корень из mean_squared_error: ** 0.5.'
assert not has_literal(m) and not has_literal(r), 'Похоже, ответ вписан руками — посчитайте его функциями.'
```

### hint
`mean_absolute_error(fact, pred)`; RMSE — `mean_squared_error(fact, pred) ** 0.5`.

### hint
Посчитайте ошибки руками, чтобы понять разницу метрик: модули ошибок — 3, 2, 0, 10, 2. MAE — их среднее. RMSE сначала возводит ошибки в квадрат, и одна ошибка в 10 минут весит в нём больше, чем все остальные вместе, поэтому RMSE выйдет заметно больше MAE.

### solution
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error
fact = [30, 42, 25, 55, 38]
pred = [33, 40, 25, 45, 36]
mae = round(mean_absolute_error(fact, pred), 2)
rmse = round(mean_squared_error(fact, pred) ** 0.5, 2)
```

### explain
MAE — 3.4 минуты, RMSE — около 5. Почти всю разницу дала одна ошибка в 10 минут (55 против 45).

## task: p-line | Минут на километр | warmup

Соберите программу: обучить линейную регрессию времени доставки на расстоянии и вывести вес (минут на км) и свободный член, оба — 2 знака, через пробел.

### parsons
```python
import pandas as pd
from sklearn.linear_model import LinearRegression
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
lin = LinearRegression()
lin.fit(ok[["distance_km"]], ok["actual_min"])
print(round(lin.coef_[0], 2), round(lin.intercept_, 2))
```

### check
```python
import pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
m = _LR().fit(ok[['distance_km']], ok['actual_min'])
want = f'{round(m.coef_[0], 2)} {round(m.intercept_, 2)}'
assert _lines == [want], f'Программа вывела {_lines}, а должна — одну строку «вес свободный_член».'
```

### hint
Модель создаётся, потом обучается, потом из неё берут `coef_` и `intercept_`.

## task: base-median | Базовая модель на тесте | warmup

Посчитайте базовую модель для регрессии честно: медиану возьмите **по обучающей части**, а ошибку — на тестовой. Сохраните `base` — медиану `y_train` и `mae_base` — MAE постоянного прогноза `base` на тесте (2 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
a, b = _tts(ok['actual_min'], test_size=0.25, random_state=42)
assert close(need('base'), a.median()), f'base = {need("base")}, а медиана y_train — {a.median()}. Медиана всей выборки или теста здесь не подходит.'
w = round((b - a.median()).abs().mean(), 2)
assert close(need('mae_base'), w), f'mae_base = {need("mae_base")}, а нужно {w}. Ошибка считается на y_test.'
```

### hint
`base = y_train.median()`; прогноз — список `[base] * len(y_test)`.

### hint
Медиана — единственное число, «обученное» по данным, поэтому берём её по `y_train`: тест модель видеть не должна. Сравните результат с MAE модели из теории — базовую модель нужно обыгрывать, иначе модель не нужна.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
base = y_train.median()
mae_base = round(mean_absolute_error(y_test, [base] * len(y_test)), 2)
```

## task: linear | Линейная регрессия на всех признаках | base

Обучите `LinearRegression` на `X_train`. Сохраните модель в `lin`, `mae_lin` — MAE на тесте (2 знака), `r2_lin` — R² на тесте (3 знака), `per_km` — вес признака `distance_km` (2 знака) и `walk_vs_auto` — на сколько минут, по мнению модели, пеший курьер медленнее авто при прочих равных (разница весов, 1 знак).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae, r2_score as _r2
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
m = _LR().fit(a, c)
w = _pd.Series(m.coef_, index=X.columns)
assert isinstance(need('lin'), _LR), 'lin — обученная LinearRegression.'
assert close(need('mae_lin'), round(_mae(e, m.predict(b)), 2)), f'mae_lin = {need("mae_lin")}, а нужно {round(_mae(e, m.predict(b)), 2)}. Метрика — на тесте.'
assert close(need('r2_lin'), round(_r2(e, m.predict(b)), 3)), f'r2_lin = {need("r2_lin")}, а нужно {round(_r2(e, m.predict(b)), 3)}. Порядок аргументов: r2_score(факт, прогноз).'
assert close(need('per_km'), round(w['distance_km'], 2), 0.006), f'per_km = {need("per_km")}, а нужно {round(w["distance_km"], 2)}.'
g = round(w['courier_пеший'] - w['courier_авто'], 1)
assert close(need('walk_vs_auto'), g, 0.051), f'walk_vs_auto = {need("walk_vs_auto")}, а нужно {g}. Это вес courier_пеший минус вес courier_авто.'
```

### hint
Веса удобно взять из Series: `w = pd.Series(lin.coef_, index=X.columns)`, затем `w["distance_km"]`.

### hint
Разница весов: `w["courier_пеший"] - w["courier_авто"]`. Аргументы метрик — сначала факт, потом прогноз.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
lin = LinearRegression().fit(X_train, y_train)
pred = lin.predict(X_test)
mae_lin = round(mean_absolute_error(y_test, pred), 2)
r2_lin = round(r2_score(y_test, pred), 3)
w = pd.Series(lin.coef_, index=X.columns)
per_km = round(w["distance_km"], 2)
walk_vs_auto = round(w["courier_пеший"] - w["courier_авто"], 1)
```

### explain
MAE 5.52, R² 0.573. Модель считает, что километр добавляет около 3.9 минуты, а пеший курьер при прочих равных медленнее машины примерно на 18.5 минуты. Веса читаются как формула для диспетчера — в этом сила линейной регрессии, даже если по точности её обгонят.

## task: forest-metrics | Три метрики для леса | base

Обучите `RandomForestRegressor(n_estimators=50, random_state=0)` и посчитайте на тесте `mae_rf`, `rmse_rf` (2 знака) и `r2_rf` (3 знака). В `gain` сохраните, на сколько минут MAE леса меньше MAE медианы обучающей части (2 знака, считайте по неокруглённым значениям).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestRegressor as _RF
from sklearn.metrics import mean_absolute_error as _mae, mean_squared_error as _mse, r2_score as _r2
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
p = _RF(n_estimators=50, random_state=0).fit(a, c).predict(b)
assert close(need('mae_rf'), round(_mae(e, p), 2)), f'mae_rf = {need("mae_rf")}, а нужно {round(_mae(e, p), 2)}. Лес — n_estimators=50, random_state=0; метрика — на тесте.'
assert close(need('rmse_rf'), round(_mse(e, p) ** 0.5, 2)), f'rmse_rf = {need("rmse_rf")}, а нужно {round(_mse(e, p) ** 0.5, 2)}. Не забудьте корень: ** 0.5.'
assert close(need('r2_rf'), round(_r2(e, p), 3)), f'r2_rf = {need("r2_rf")}, а нужно {round(_r2(e, p), 3)}.'
g = round(_mae(e, [c.median()] * len(e)) - _mae(e, p), 2)
assert close(need('gain'), g), f'gain = {need("gain")}, а нужно {g}. Медиана — по y_train, обе MAE — на тесте.'
```

### hint
`forest = RandomForestRegressor(n_estimators=50, random_state=0).fit(X_train, y_train)`, `pred = forest.predict(X_test)`.

### hint
MAE медианы: `mean_absolute_error(y_test, [y_train.median()] * len(y_test))`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestRegressor(n_estimators=50, random_state=0).fit(X_train, y_train)
pred = forest.predict(X_test)
mae_rf = round(mean_absolute_error(y_test, pred), 2)
rmse_rf = round(mean_squared_error(y_test, pred) ** 0.5, 2)
r2_rf = round(r2_score(y_test, pred), 3)
gain = round(mean_absolute_error(y_test, [y_train.median()] * len(y_test)) - mean_absolute_error(y_test, pred), 2)
```

### explain
Лес: MAE 4.55, RMSE 5.76, R² 0.726. Медиана обучающей части ошибается в среднем на 8.15 минуты, лес — на 3.6 минуты меньше. RMSE заметно больше MAE: у леса есть редкие крупные промахи, их разберём в задаче про остатки.

## task: depth | Глубина дерева для минут | base

Обучите `DecisionTreeRegressor(random_state=0)` с глубиной 2, 5 и без ограничения (`max_depth=None`). Сохраните в `mae_by_depth` словарь `{2: ..., 5: ..., None: ...}` с MAE на тесте (2 знака), а в `best_depth` — глубину с наименьшей MAE.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeRegressor as _T
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
want = {k: round(_mae(e, _T(max_depth=k, random_state=0).fit(a, c).predict(b)), 2) for k in (2, 5, None)}
got = need('mae_by_depth', dict)
assert set(got) == {2, 5, None}, f'Ключи словаря: {list(got)}. Нужны 2, 5 и None.'
for k in want:
    assert close(got[k], want[k]), f'Для глубины {k} MAE = {got[k]}, а нужно {want[k]}.'
assert need('best_depth') == min(want, key=want.get), f'best_depth = {need("best_depth")!r}. Это ключ с наименьшей MAE.'
```

### hint
Цикл `for depth in [2, 5, None]:` и внутри — модель с `max_depth=depth`.

### hint
Ключ с наименьшим значением: `min(mae_by_depth, key=mae_by_depth.get)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
mae_by_depth = {}
for depth in [2, 5, None]:
    tree = DecisionTreeRegressor(max_depth=depth, random_state=0).fit(X_train, y_train)
    mae_by_depth[depth] = round(mean_absolute_error(y_test, tree.predict(X_test)), 2)
best_depth = min(mae_by_depth, key=mae_by_depth.get)
```

### explain
Как и в классификации, дерево без ограничения глубины запоминает обучающие доставки (на train его ошибка почти нулевая) и хуже работает на новых. Слишком мелкое дерево не успевает уловить закономерности. Подбирать глубину по тесту, как мы сейчас сделали, на самом деле нечестно — правильный способ с валидационной выборкой будет в следующем уроке.

## task: fact-pred | График «факт против прогноза» | base

Нарисуйте для линейной регрессии точечный график: по оси X — прогноз на тесте, по оси Y — факт. Добавьте серую пунктирную диагональ `ax.plot([10, 100], [10, 100], ...)`, подписи осей `прогноз, мин` и `факт, мин` и заголовок, в котором есть слово `линейная`.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
pred = LinearRegression().fit(X_train, y_train).predict(X_test)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
p = _LR().fit(a, c).predict(b)
ax = ax_of()
assert ax.collections, 'Точек на графике нет — нужен ax.scatter(...).'
pts = _np.asarray(ax.collections[0].get_offsets())
assert len(pts) == len(e), f'На графике {len(pts)} точек, а тестовых доставок {len(e)}.'
assert _np.allclose(_np.sort(pts[:, 0]), _np.sort(p), atol=1e-6), 'По оси X должен быть прогноз, а по оси Y — факт. Проверьте порядок аргументов scatter.'
assert _np.allclose(_np.sort(pts[:, 1]), _np.sort(e.to_numpy(dtype=float))), 'По оси Y должен быть факт y_test.'
assert any(list(l.get_xdata()) == [10, 100] and list(l.get_ydata()) == [10, 100] for l in ax.lines), 'Не вижу диагонали: ax.plot([10, 100], [10, 100], ...).'
assert ax.get_xlabel() == 'прогноз, мин' and ax.get_ylabel() == 'факт, мин', f'Подписи осей: {ax.get_xlabel()!r} и {ax.get_ylabel()!r}, а нужны "прогноз, мин" и "факт, мин".'
assert 'линейная' in ax.get_title().lower(), f'Заголовок {ax.get_title()!r} — в нём должно быть слово «линейная».'
```

### hint
`fig, ax = plt.subplots(figsize=(5, 5))`, затем `ax.scatter(pred, y_test, s=8)`.

### hint
Диагональ: `ax.plot([10, 100], [10, 100], color="grey", linestyle="--")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
pred = LinearRegression().fit(X_train, y_train).predict(X_test)

fig, ax = plt.subplots(figsize=(5, 5))
ax.scatter(pred, y_test, s=8, alpha=0.5)
ax.plot([10, 100], [10, 100], color="grey", linestyle="--")
ax.set_xlabel("прогноз, мин")
ax.set_ylabel("факт, мин")
ax.set_title("Линейная регрессия: факт против прогноза")
```

### explain
Сравните с графиком леса из теории: облако линейной модели шире. Особенно заметно на долгих доставках (от 50 минут): там прогнозы линейной модели в среднем примерно на 10 минут ниже факта. Отчасти дело в том, что одна цена километра для всех не подходит пешим курьерам.

## task: residuals | Где ошибается лес | plus

Для леса `RandomForestRegressor(n_estimators=50, random_state=0)` соберите таблицу `res` со столбцами `fact`, `pred` и `err` (факт − прогноз) по тестовым доставкам и добавьте к ней столбец `courier` из `ok` (через `join`). Сохраните:

- `big_share` — долю доставок, где модель ошиблась больше чем на 10 минут в любую сторону (3 знака);
- `err_by_courier` — Series: средний остаток по типу курьера (индекс — тип курьера, значения — 2 знака);
- `worst_courier` — тип курьера в строке с самой большой по модулю ошибкой.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestRegressor(n_estimators=50, random_state=0).fit(X_train, y_train)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestRegressor as _RF
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
r = _pd.DataFrame({'fact': e, 'pred': _RF(n_estimators=50, random_state=0).fit(a, c).predict(b)})
r['err'] = r['fact'] - r['pred']
r = r.join(ok['courier'])
t = need('res', _pd.DataFrame)
assert {'fact', 'pred', 'err', 'courier'} <= set(t.columns), f'Столбцы res: {list(t.columns)}. Нужны fact, pred, err и courier.'
assert len(t) == len(r), f'В res {len(t)} строк, а тестовых доставок {len(r)}.'
assert close(need('big_share'), round((r['err'].abs() > 10).mean(), 3)), f'big_share = {need("big_share")}, а нужно {round((r["err"].abs() > 10).mean(), 3)}. Ошибка в любую сторону — по модулю: .abs().'
g = r.groupby('courier')['err'].mean().round(2)
s = need('err_by_courier', _pd.Series)
assert set(s.index) == set(g.index), f'Индекс err_by_courier: {list(s.index)}. Нужны типы курьеров.'
assert all(close(s[k], g[k], 0.006) for k in g.index), f'err_by_courier = {dict(s)}, а нужно {dict(g)}. Это среднее err по группам courier.'
wc = r.loc[r['err'].abs().idxmax(), 'courier']
assert need('worst_courier') == wc, f'worst_courier = {need("worst_courier")!r}. Найдите строку с наибольшим |err|.'
```

### hint
`res = pd.DataFrame({"fact": y_test, "pred": forest.predict(X_test)})`, `res["err"] = res["fact"] - res["pred"]`, затем `res = res.join(ok["courier"])`.

### hint
Строка с наибольшей по модулю ошибкой: `res.loc[res["err"].abs().idxmax(), "courier"]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestRegressor(n_estimators=50, random_state=0).fit(X_train, y_train)

res = pd.DataFrame({"fact": y_test, "pred": forest.predict(X_test)})
res["err"] = res["fact"] - res["pred"]
res = res.join(ok["courier"])
big_share = round((res["err"].abs() > 10).mean(), 3)
err_by_courier = res.groupby("courier")["err"].mean().round(2)
worst_courier = res.loc[res["err"].abs().idxmax(), "courier"]
```

### explain
Только 7 % доставок лес промахнулся больше чем на 10 минут. Средние остатки по курьерам слегка отрицательны (−0.6…−0.85): на тесте лес немного завышает время всем — систематического перекоса для пеших нет. Самая большая ошибка — у машины: прогноз 73 минуты, приехала за 48. Это дальний заказ, а для очень дальних доставок в данных мало примеров, и лес «усредняет» их неточно.

## task: late-minutes | Опоздание из линейной модели | plus

Превратите прогноз минут **линейной регрессии** в прогноз опоздания: «прогноз > обещания». Сохраните `acc_lin` — долю правильных ответов на тесте (3 знака), `late_minutes` — на сколько минут в среднем опаздывают те тестовые доставки, которые модель пометила как опаздывающие (среднее `факт − обещание` по ним, 1 знак; учитываются все такие доставки, даже приехавшие вовремя).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
pred = LinearRegression().fit(X_train, y_train).predict(X_test)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
p = _LR().fit(a, c).predict(b)
lp = p > b['promised_min']
lf = e > b['promised_min']
w1 = round((lp == lf).mean(), 3)
w2 = round((e - b['promised_min'])[lp].mean(), 1)
assert close(need('acc_lin'), w1), f'acc_lin = {need("acc_lin")}, а нужно {w1}. Сравните «прогноз > обещания» с «факт > обещания».'
assert close(need('late_minutes'), w2), f'late_minutes = {need("late_minutes")}, а нужно {w2}. Среднее (факт − обещание) только по доставкам, где прогноз > обещания.'
```

### hint
Обещание для тестовых доставок — `X_test["promised_min"]`. Маска прогноза: `late_pred = pred > X_test["promised_min"]`.

### hint
`(y_test - X_test["promised_min"])[late_pred].mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
pred = LinearRegression().fit(X_train, y_train).predict(X_test)

late_pred = pred > X_test["promised_min"]
late_fact = y_test > X_test["promised_min"]
acc_lin = round((late_pred == late_fact).mean(), 3)
late_minutes = round((y_test - X_test["promised_min"])[late_pred].mean(), 1)
```

### explain
Даже простая линейная модель, обученная на минутах, отвечает на вопрос об опоздании не хуже классификаторов. И добавляет то, чего у них нет: по помеченным доставкам видно, на сколько минут ждать опоздания, — это можно честно сообщить гостю.

## task: interaction | Помочь линейной модели | star

Линейная модель не видит, что пешему курьеру километр стоит дороже. Помогите ей: добавьте в `X` признак-взаимодействие `walk_km` — расстояние, умноженное на флаг пешего курьера (у остальных курьеров 0). Обучите `LinearRegression` заново на том же разбиении и сохраните `mae_before` и `mae_after` — MAE на тесте без нового признака и с ним (2 знака), а также `walk_km_coef` — вес нового признака (2 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
m0 = round(_mae(e, _LR().fit(a, c).predict(b)), 2)
X2 = X.copy()
X2['walk_km'] = X2['distance_km'] * X2['courier_пеший']
a2, b2, c2, e2 = _tts(X2, y, test_size=0.25, random_state=42)
m = _LR().fit(a2, c2)
m1 = round(_mae(e2, m.predict(b2)), 2)
k = round(_pd.Series(m.coef_, index=X2.columns)['walk_km'], 2)
assert close(need('mae_before'), m0), f'mae_before = {need("mae_before")}, а нужно {m0}. Это линейная модель на исходных признаках.'
assert close(need('mae_after'), m1), f'mae_after = {need("mae_after")}, а нужно {m1}. Признак walk_km = distance_km * courier_пеший; разбиение — то же (0.25, random_state=42).'
assert close(need('walk_km_coef'), k, 0.006), f'walk_km_coef = {need("walk_km_coef")}, а нужно {k}.'
```

### hint
Флаг пешего курьера уже есть в `X`: столбец `courier_пеший` (0 или 1). Новый признак: `X["walk_km"] = X["distance_km"] * X["courier_пеший"]`.

### hint
Посчитайте MAE «до» раньше, чем добавите столбец, или сделайте копию `X2 = X.copy()`. Разбивайте оба варианта с `test_size=0.25, random_state=42` — тогда в тест попадут те же доставки.

### hint
Вес признака по названию: `pd.Series(model.coef_, index=X2.columns)["walk_km"]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
mae_before = round(mean_absolute_error(y_test, LinearRegression().fit(X_train, y_train).predict(X_test)), 2)

X2 = X.copy()
X2["walk_km"] = X2["distance_km"] * X2["courier_пеший"]
X_train, X_test, y_train, y_test = train_test_split(X2, y, test_size=0.25, random_state=42)
model = LinearRegression().fit(X_train, y_train)
mae_after = round(mean_absolute_error(y_test, model.predict(X_test)), 2)
walk_km_coef = round(pd.Series(model.coef_, index=X2.columns)["walk_km"], 2)
```

### explain
Один признак, придуманный аналитиком, снизил ошибку линейной модели примерно с 5.5 до 4.8 минуты — почти до уровня леса. Вес `walk_km` показывает, сколько минут на километр пеший курьер добавляет **сверх** общей цены километра. Лес нашёл это взаимодействие сам, а линейной модели его пришлось подсказать. Понимание данных по-прежнему важно: хороший признак иногда стоит больше, чем сложная модель.
