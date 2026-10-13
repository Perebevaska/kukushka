---
title: "Что делать с вероятностями: ранжирование и калибровка"
lead: "Логистическая регрессия выдаёт вероятность. Ею можно не только ставить порог: можно отсортировать заказы по риску и работать с верхом списка — и проверить, можно ли самой вероятности верить как числу. Ранжирование, лифт и калибровка — то, чем аналитик пользуется чаще, чем accuracy."
files: [deliveries.csv]
recap:
  - "Ранжирование: доля опозданий среди 10 % самых рискованных заказов против средней показывает, насколько модель полезна для приоритетов."
  - "Калибровка: разбить вероятности на группы (`pd.cut`) и сравнить среднюю вероятность с фактической долей опозданий в группе."
---

Модель та же, что в уроке «Логистическая регрессия и вероятности»: логистическая регрессия на признаках доставки, обученная на 75 % доставок; оцениваем её на остальных 25 %.

## Ранжирование по риску

Часто от модели нужен не ответ «да/нет», а **список приоритетов**: у диспетчера есть время на звонки по 10 % заказов — каким именно? Сортируем тестовые заказы по вероятности и берём верхние 10 %:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

risk = pd.DataFrame({"p": p, "late": y_test})
k = int(len(risk) * 0.1)
top = risk.sort_values("p", ascending=False).head(k)
print(f"заказов в топе: {k}")
print(f"опаздывают в топ-10 %: {top['late'].mean():.0%}, в среднем: {risk['late'].mean():.0%}")
```

Среди 10 % самых рискованных заказов опаздывают больше 80 % — примерно в три с половиной раза чаще, чем в среднем. Это отношение называют **лифтом** (lift): во сколько раз в отобранной группе целевое событие встречается чаще, чем в целом. Для обзвона это очень полезный список, хотя доля правильных ответов модели почти не отличается от правила «пеший — опоздает».

::: sql
Это тот же запрос «топ-N по метрике», что вы пишете в SQL: `ORDER BY p DESC LIMIT k`, только метрику `p` посчитала модель.
:::

{{practice: top10, bikes}}

## Можно ли верить вероятностям

Модель сказала «70 %». Значит ли это, что из ста таких заказов опоздают около семидесяти? Если да, модель **откалибрована** (calibrated), и её вероятности можно использовать как есть: умножать на стоимость опоздания, сравнивать с порогами. Проверка простая: разбить заказы на группы по вероятности и в каждой сравнить среднюю вероятность с фактической долей опозданий.

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

risk = pd.DataFrame({"p": p, "late": y_test})
risk["group"] = pd.cut(risk["p"], [0, 0.2, 0.4, 0.6, 0.8, 1])
cal = risk.groupby("group", observed=True).agg(pred=("p", "mean"), fact=("late", "mean"), n=("p", "size"))
print(cal.round(2))

fig, ax = plt.subplots(figsize=(4.5, 4.5))
ax.plot([0, 1], [0, 1], color="grey", linestyle="--")
ax.plot(cal["pred"], cal["fact"], marker="o")
ax.set_xlabel("предсказанная вероятность")
ax.set_ylabel("фактическая доля опозданий")
ax.set_title("Калибровка")
```

`pd.cut` из главы 3 режет числа на интервалы, `observed=True` убирает пустые группы. Точки близко к диагонали — вероятности правдивы. У нас самые большие группы (до 0.2 и 0.2–0.4) почти на диагонали. В средних группах модель занижает риск: где она обещает около 50 %, опоздали две трети. В верхней — немного завышает: около 89 % против 82 %. Но в средних группах всего по 25–35 заказов, и расхождение в 10–15 пунктов на таких группах может быть отчасти случайным. Для обзвона по риску этого достаточно, а для расчётов «вероятность × стоимость» стоило бы проверить на большей выборке.

::: warn
Высокая доля правильных ответов не гарантирует хорошую калибровку, и наоборот. Если вероятности будут использоваться как числа (умножаться на деньги), калибровку нужно проверять отдельно. Глубокое дерево, например, часто выдаёт вероятности 0 и 1 — а это заведомо самоуверенно.
:::

::: warn Типичные ошибки
- **`predict_proba(X)[:, 0]`.** Это вероятность «вовремя»; опоздание — второй столбец `[:, 1]`.
- **Сравнивать веса в разных единицах.** «−0.18 за минуту» и «2.5 за флаг» несравнимы без масштабирования (глава 7).
- **Вес = причина.** Отрицательный вес обещания — эффект «при прочих равных», а не «дальние заказы опаздывают реже».
- **Порог 0.5 по привычке.** Порог выбирают по цене ошибок: тревога диспетчера и бонус гостю стоят по-разному.
- **Игнорировать `ConvergenceWarning`.** Веса могут быть недообученными; увеличьте `max_iter` или масштабируйте признаки.
:::

::: quiz
Про модель говорят, что она хорошо откалибрована. Что это значит?

- [x] Среди заказов, которым она даёт около 30 %, опаздывает примерно 30 %
  > Калибровка — согласие вероятностей с фактическими долями: на графике точки лежат около диагонали.
- [ ] У неё высокая доля правильных ответов на тесте
  > Accuracy и калибровка — разные свойства: модель может часто угадывать класс и при этом систематически завышать или занижать вероятности.
- [ ] Порог тревоги у неё подобран оптимально
  > Порог — отдельное решение бизнеса поверх вероятностей. Калибровка говорит о самих вероятностях, а не о пороге.
- [ ] Её вероятности близки к 0 и 1, то есть она уверена в ответах
  > Уверенность не равна правдивости. Вероятности 0 и 1 у глубокого дерева как раз пример самоуверенной, плохо откалиброванной модели.
:::

{{practice: calib}}

## Практика

## task: top10 | Топ-10 % по риску | base

Возьмите 10 % тестовых доставок с наибольшей вероятностью опоздания (`k = int(len(...) * 0.1)` штук). Сохраните `top_rate` — долю опозданий среди них (3 знака), `all_rate` — долю опозданий во всём тесте (3 знака) и `lift` — во сколько раз первая больше второй (2 знака, считайте по неокруглённым долям).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = _LR(max_iter=2000).fit(a, c).predict_proba(b)[:, 1]
r = _pd.DataFrame({'p': w, 'late': e})
k = int(len(r) * 0.1)
t = r.sort_values('p', ascending=False).head(k)['late'].mean()
m = r['late'].mean()
assert close(need('all_rate'), round(m, 3)), f'all_rate = {need("all_rate")}, а нужно {round(m, 3)} — доля опозданий во всём тесте.'
assert close(need('top_rate'), round(t, 3)), f'top_rate = {need("top_rate")}, а нужно {round(t, 3)}. Сортировать — по убыванию вероятности, взять {k} верхних.'
assert close(need('lift'), round(t / m, 2)), f'lift = {need("lift")}, а нужно {round(t / m, 2)}.'
```

### hint
Соберите таблицу `pd.DataFrame({"p": p, "late": y_test})` и отсортируйте её `sort_values("p", ascending=False)`.

### hint
`.head(k)["late"].mean()` — доля опозданий среди первых `k`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]
risk = pd.DataFrame({"p": p, "late": y_test})
k = int(len(risk) * 0.1)
top = risk.sort_values("p", ascending=False).head(k)
top_rate_raw = top["late"].mean()
all_rate_raw = risk["late"].mean()
top_rate = round(top_rate_raw, 3)
all_rate = round(all_rate_raw, 3)
lift = round(top_rate_raw / all_rate_raw, 2)
```

### explain
Среди 10 % самых рискованных доставок опаздывают 83 %, а в среднем — 23 %: лифт около 3.6. Если диспетчер может проконтролировать только каждую десятую доставку, список по модели находит опоздания в три с половиной раза чаще случайного выбора.

## task: bikes | Риск внутри вело-доставок | star

Правило «пеший — опоздает» всем вело-доставкам отвечает одинаково: «вовремя». Проверьте, умеет ли модель различать риск **внутри** вело-доставок. Отберите тестовые доставки вело-курьеров, отсортируйте их по вероятности опоздания и разделите пополам: в `high_rate` — доля опозданий в более рискованной половине, в `low_rate` — в менее рискованной (обе — 3 знака). Если таких доставок нечётное число, лишняя доставка идёт в менее рискованную половину: `half = n // 2` верхних — это рискованная половина.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = _LR(max_iter=2000).fit(a, c).predict_proba(b)[:, 1]
r = _pd.DataFrame({'p': w, 'late': e, 'bike': b['courier_вело'] == 1})
r = r[r['bike']].sort_values('p', ascending=False)
h = len(r) // 2
hi, lo = round(r['late'].iloc[:h].mean(), 3), round(r['late'].iloc[h:].mean(), 3)
assert close(need('high_rate'), hi), f'high_rate = {need("high_rate")}, а нужно {hi}. Отбирайте только вело-доставки (столбец courier_вело в X_test), сортируйте по убыванию p и берите первые {h}.'
assert close(need('low_rate'), lo), f'low_rate = {need("low_rate")}, а нужно {lo}. Это оставшиеся {len(r) - h} вело-доставок.'
```

### hint
Признак «вело» уже есть в тестовой таблице: `X_test["courier_вело"] == 1`. Соберите `pd.DataFrame({"p": p, "late": y_test})` и отфильтруйте по этой маске.

### hint
После сортировки по убыванию `p`: `.iloc[:half]` — рискованная половина, `.iloc[half:]` — остальные.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

risk = pd.DataFrame({"p": p, "late": y_test})
bike = risk[X_test["courier_вело"] == 1].sort_values("p", ascending=False)
half = len(bike) // 2
high_rate = round(bike["late"].iloc[:half].mean(), 3)
low_rate = round(bike["late"].iloc[half:].mean(), 3)
```

### explain
Для правила все вело-доставки одинаково безопасны, а модель видит разницу: в рискованной половине опаздывает около 18 %, в спокойной — почти никто. Ответ «да/нет» этого не покажет: почти у всех вело-доставок вероятность ниже 0.5, и `predict` для них тоже «вовремя». Разница видна, только когда мы смотрим на вероятности и ранжирование. Внутри пеших доставок модель различает риск гораздо хуже (около 82 % против 77 %) — там почти все опаздывают.

## task: calib | Калибровка | plus

Проверьте калибровку модели на тесте. Разбейте вероятности на группы `pd.cut(..., [0, 0.25, 0.5, 0.75, 1])` и сохраните в `cal` таблицу с индексом-группой и тремя столбцами: `pred` — средняя вероятность в группе, `fact` — фактическая доля опозданий, `n` — число доставок. Пустые группы не нужны. В `worst` сохраните наибольшее по модулю расхождение `pred − fact` среди групп (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = _LR(max_iter=2000).fit(a, c).predict_proba(b)[:, 1]
r = _pd.DataFrame({'p': w, 'late': e})
g = _pd.cut(r['p'], [0, 0.25, 0.5, 0.75, 1])
ref = r.groupby(g, observed=True).agg(pred=('p', 'mean'), fact=('late', 'mean'), n=('p', 'size'))
t = need('cal', _pd.DataFrame)
assert {'pred', 'fact', 'n'} <= set(t.columns), f'Столбцы cal: {list(t.columns)}. Нужны pred, fact и n.'
assert len(t) == len(ref), f'В cal {len(t)} строк, а групп с доставками {len(ref)}. Границы: [0, 0.25, 0.5, 0.75, 1]; пустые группы убирает observed=True.'
assert [int(x) for x in t['n']] == [int(x) for x in ref['n']], f'Размеры групп n = {list(t["n"])}, а нужно {list(ref["n"])}.'
assert all(close(x, z, 1e-3) for x, z in zip(t['pred'], ref['pred'])), 'pred не совпадает: это средняя вероятность в группе.'
assert all(close(x, z, 1e-3) for x, z in zip(t['fact'], ref['fact'])), 'fact не совпадает: это доля опозданий (среднее late) в группе.'
wv = round((ref['pred'] - ref['fact']).abs().max(), 3)
assert close(need('worst'), wv), f'worst = {need("worst")}, а нужно {wv}. Возьмите модуль разницы .abs() и максимум.'
```

### hint
Соберите `risk = pd.DataFrame({"p": p, "late": y_test})` и добавьте столбец группы: `risk["group"] = pd.cut(risk["p"], [0, 0.25, 0.5, 0.75, 1])`.

### hint
Именованная агрегация: `groupby("group", observed=True).agg(pred=("p", "mean"), fact=("late", "mean"), n=("p", "size"))`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]
risk = pd.DataFrame({"p": p, "late": y_test})
risk["group"] = pd.cut(risk["p"], [0, 0.25, 0.5, 0.75, 1])
cal = risk.groupby("group", observed=True).agg(pred=("p", "mean"), fact=("late", "mean"), n=("p", "size"))
worst = round((cal["pred"] - cal["fact"]).abs().max(), 3)
```

### explain
Калибровка неплохая, но не идеальная: в группе 0–0.25 модель обещает 6.8 % опозданий, а их 4.6 %; в средних группах (0.25–0.75) модель **занижает** риск на 6–12 п.п.; в верхней — немного завышает. Самое большое расхождение — в группе 0.5–0.75 (0.64 против 0.76). Помните, что в средних группах всего по 42–45 доставок, и часть расхождения — случайность.
