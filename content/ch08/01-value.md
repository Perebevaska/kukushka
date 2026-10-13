---
title: "Из прогноза — в деньги"
lead: "Модель оттока из главы 7 говорит, кто, вероятно, уйдёт. Бизнесу нужен другой ответ: кому дать бонус, чтобы заработать. Переводим матрицу ошибок в рубли, выбираем порог по прибыли, проверяем, насколько решение зависит от допущений. Как проверить это обещание пилотом и разложить выручку на дерево метрик — в следующем уроке."
files: [guests_churn.csv]
recap:
  - "Каждой клетке матрицы ошибок можно назначить цену. Ожидаемая прибыль кампании = выгода × TP − расход × FP."
  - "Бонус выгоден гостю с вероятностью ухода p, если p × (доля удержанных × ценность гостя) > цена бонуса. Отсюда порог безубыточности."
  - "Порог 0.5 — соглашение библиотеки, а не бизнес-решение. Порог выбирают по прибыли."
  - "Прибыль считают и для простых стратегий: «никому», «всем», правило аналитика. Модель нужна, только если зарабатывает больше них."
  - "Формула порога работает, когда вероятности модели похожи на настоящие доли (калибровка) — это проверяют по группам."
  - "Допущения (сколько гостей удержит бонус) — самое шаткое место. Проверяют, как от них меняются порог и прибыль."
---

## Цена каждой ошибки

Отдел лояльности готовит кампанию: гостям, которые, вероятно, уйдут, дать бонус на 200 ₽. Договоримся о допущениях (их дал отдел маркетинга по прошлым акциям):

- бонус стоит **200 ₽** — его получает каждый, кому мы его отправили;
- если гость действительно собирался уйти, бонус удерживает его в **25 %** случаев;
- удержанный гость приносит **2400 ₽** маржи за следующие полгода.

Значит, бонус уходящему гостю в среднем приносит 0.25 × 2400 − 200 = **400 ₽**, а бонус тому, кто и так остался бы, — **−200 ₽**. Переведём матрицу ошибок из главы 7 в рубли:

::: figure bonus-economics
Два исхода одного бонуса в рублях. Отсюда и порог безубыточности 1/3 из раздела ниже.
:::

| | бонус отправили | бонус не отправили |
|---|---|---|
| гость уходит | TP: +400 ₽ | FN: 0 ₽ (упустили 400 ₽) |
| гость остаётся | FP: −200 ₽ | TN: 0 ₽ |

Ожидаемая прибыль кампании = 400 × TP − 200 × FP. «Ожидаемая» — потому что удержание случайно: из четырёх уходящих с бонусом останется в среднем один, и считаем мы среднее.

::: note
FN — не расход, а упущенная выгода. В отчёте о прибыли кампании его нет, но при сравнении стратегий он виден: кто ловит меньше уходящих, тот меньше зарабатывает.
:::

Обучим знакомую модель и посчитаем прибыль при обычном пороге 0.5:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

send = p > 0.5
tp = (send & (y_test == 1)).sum()
fp = (send & (y_test == 0)).sum()
print(f"бонусов {send.sum()}, TP {tp}, FP {fp}, прибыль {400 * tp - 200 * fp} ₽")
```

**Что здесь происходит:**

- `X` — признаки гостя без `guest_id`, ответа и утечки `card_blocked` (глава 6); пропуски среднего чека — у гостей без визитов, заменяем нулём.
- `stratify=y` — в тесте та же доля ушедших, что во всей таблице (22 %).
- `p` — вероятность ухода для каждого из 600 тестовых гостей.
- `send = p > 0.5` — маска «кому отправить бонус»; `send & (y_test == 1)` — отправили и гость правда уходил (TP), `send & (y_test == 0)` — отправили зря (FP).
- `.sum()` у маски считает `True` — как `COUNT(*) ... WHERE` в SQL.

105 бонусов, из них 87 попали к уходящим гостям: 87 × 400 − 18 × 200 = 31 200 ₽ на 600 гостей тестовой выборки.

{{practice: cost-matrix, p-profit}}

## С чем сравнивать

Прибыль сама по себе ничего не говорит — нужна точка отсчёта. Посчитаем простые стратегии на тех же гостях:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

print("никому:", profit(y_test < 0))      # y_test < 0 — маска из одних False: бонус не получает никто
print("всем:", profit(y_test >= 0))      # y_test >= 0 — одни True: бонус всем
print("давность > 45 дней:", profit(X_test["days_since_last"] > 45))
```

- **Никому** — 0 ₽: ничего не тратим и ничего не получаем.
- **Всем** — убыток 39 600 ₽: 466 бонусов уходят тем, кто и так остался бы.
- **Правило «не был больше 45 дней»** — 20 000 ₽: точное, но ловит меньше половины уходящих.
- **Модель с порогом 0.5** — 31 200 ₽.

Модель зарабатывает больше простых стратегий — значит, она полезна. Но порог 0.5 мы не выбирали, его выбрала библиотека.

::: predict
```python static
tp, fp = 30, 50
print(400 * tp - 200 * fp)
```

- `22000`
- [x] `2000`
- `-2000`

Почему: 30 × 400 = 12 000, 50 × 200 = 10 000. Кампания едва окупилась: на каждого пойманного уходящего пришлось почти два лишних бонуса.
:::

{{practice: rule-vs-model}}

## Порог безубыточности

Модель выдаёт вероятность ухода p. Отправлять бонус гостю выгодно, если ожидаемая выгода больше цены бонуса:

p × 0.25 × 2400 > 200, то есть p × 600 > 200, то есть **p > 1/3**.

Это порог безубыточности: гостю с вероятностью ухода 0.4 бонус выгоден, хотя модель с порогом 0.5 его бы не отправила.

::: tip Аналогия
Зонт берут не тогда, когда дождь вероятнее его отсутствия, а когда промокнуть дороже, чем зря носить зонт. Если костюм жалко, зонт оказывается в сумке и при небольшой вероятности дождя — прогноз тот же, изменились цены ошибок. С бонусом так же: лишний бонус дешевле упущенного гостя, поэтому порог ниже 0.5. Где аналогия хромает: зонт защищает от дождя всегда, а бонус удерживает лишь каждого четвёртого уходящего — это уже учтено в выгоде 600 ₽.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

for t in [0.5, 1 / 3]:
    send = p > t
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    print(f"порог {t:.2f}: бонусов {send.sum()}, прибыль {400 * tp - 200 * fp} ₽")
```

С порогом 1/3 бонусов больше (168 против 105), лишних бонусов втрое больше (55 против 18) — а прибыль выше: 34 200 ₽. Каждый дополнительный пойманный уходящий окупает два лишних бонуса.

В общем виде: если удержание даёт выгоду V, а контакт стоит C, порог безубыточности — **p = C / V** (у нас 200 / 600).

Обратите внимание: V здесь — выгода **до** вычета цены бонуса (0.25 × 2400 = 600), а не 400 из таблицы. Почему: бонус стоит 200 ₽ любому получателю, и уходящему, и остающемуся. Гость с вероятностью p приносит в среднем p × 600, а стоит 200 всегда. Проверка через таблицу даёт то же: p × 400 − (1 − p) × 200 > 0 ⇔ 600p > 200.

::: predict
```python static
cost, retain, value = 300, 0.25, 2400
print(round(cost / (retain * value), 2))
```

- `0.13`
- [x] `0.5`
- `0.33`

Почему: выгода от удержания 0.25 × 2400 = 600, бонус за 300 ₽ окупается, только если гость уходит с вероятностью больше половины. Дороже бонус — выше порог.
:::

::: quiz
Почему порог для бонуса 1/3, а не привычные 0.5?

- [x] Пойманный уходящий приносит +400 ₽, а лишний бонус стоит только 200 ₽ — выгодно рискнуть и при вероятности ухода ниже половины
  > Порог 0.5 одинаково наказывает обе ошибки. Когда ошибки стоят по-разному, порог считают из денег: p × 600 > 200.
- [ ] Так модель точнее
  > Accuracy при пороге 1/3 обычно ниже, но прибыль выше.
- [ ] 1/3 — стандарт для оттока
  > Стандарта нет: порог зависит от цены бонуса и ценности гостя.
- [ ] Модель занижает вероятности
  > Порог 1/3 следует из экономики, а не из калибровки.
:::

{{practice: break-even, best-threshold, margin}}

## Разберём вместе: десять гостей руками

Прежде чем доверять кодовым итогам, посчитаем маленький пример целиком. Десять гостей, прогноз и факт:

| гость | p | ушёл? |
|---|---|---|
| A | 0.90 | да |
| B | 0.80 | да |
| C | 0.60 | нет |
| D | 0.45 | да |
| E | 0.40 | нет |
| F | 0.35 | да |
| G | 0.30 | нет |
| H | 0.20 | нет |
| I | 0.10 | нет |
| J | 0.05 | нет |

**Порог 0.5.** Бонус получают A, B, C. TP = 2 (A, B), FP = 1 (C). Прибыль: 2 × 400 − 1 × 200 = **600 ₽**. Упустили D и F — 2 × 400 = 800 ₽ выгоды.

**Порог 1/3.** Добавляются D (0.45), E (0.40), F (0.35). TP = 4, FP = 2. Прибыль: 4 × 400 − 2 × 200 = **1200 ₽** — вдвое больше.

**Что получилось.** Три дополнительных бонуса стоили 600 ₽, а два из них попали к уходящим и принесли 2 × 600 = 1200 ₽ выгоды: +600 ₽ сверху. Гостя G (0.30) порог 1/3 не берёт — и правильно: его бонус в среднем приносит 0.30 × 600 − 200 = −20 ₽.

::: figure value-ten-guests
Те же десять гостей на шкале риска. Порог 1/3 добавляет полосу между 1/3 и 0.5: двое из трёх гостей в ней уходят, и их бонусы окупают лишний третий.
:::

```python
import numpy as np
p = np.array([0.9, 0.8, 0.6, 0.45, 0.4, 0.35, 0.3, 0.2, 0.1, 0.05])
y = np.array([1, 1, 0, 1, 0, 1, 0, 0, 0, 0])
for t in [0.5, 1 / 3]:
    send = p > t
    tp, fp = (send & (y == 1)).sum(), (send & (y == 0)).sum()
    print(f"порог {t:.2f}: TP {tp}, FP {fp}, прибыль {400 * tp - 200 * fp}")
```

::: sql
Это тот же CASE WHEN, только граница не «на глаз», а из экономики: `CASE WHEN p_churn * 600 > 200 THEN 'бонус' END`.
:::

{{practice: toy-guests}}

## Калибровка: можно ли верить вероятностям

Формула p > 1/3 честна, только если «0.4» у модели и правда означает «уходят 40 % таких гостей». Это называется **калибровкой** (урок «Что делать с вероятностями: ранжирование и калибровка» главы 6). Проверяют её так: делят гостей на группы по прогнозу и в каждой сравнивают средний прогноз с долей реально ушедших. Если модель откалибрована, числа близки:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

t = pd.DataFrame({"p": p, "fact": y_test.values})
t["group"] = pd.cut(t["p"], [0, 0.1, 0.3, 0.5, 0.7, 1], include_lowest=True)
t.groupby("group", observed=True).agg(guests=("fact", "size"), predicted=("p", "mean"), fact=("fact", "mean")).round(2)
```

Калибровка неидеальна. В группе 0.3–0.5 в среднем прогноз близок к факту (0.40 против 0.38), а в группе 0.1–0.3 лес завышает риск (0.18 против 0.07) и в верхней группе занижает (0.83, а уходят почти все). Для порога 1/3 важнее всего гости **около** него, а границы групп 0.3 и 0.5 режут это место пополам. Если взять окно 0.25–0.45 вокруг порога (задача «Калибровка у порога»), прогноз в среднем 0.35, а уходит около 25 %: часть завышения из группы 0.1–0.3 заходит и сюда. Значит, гости с прогнозом чуть выше 1/3 уходят реже, чем обещает модель, и настоящий выгодный порог немного выше. Поэтому формулу C / V используют как ориентир, а точный порог подбирают перебором по прибыли — как в задаче ниже.

{{practice: calib}}

## Допущения решают

«Бонус удерживает 25 % уходящих» — это оценка по прошлым акциям, а не закон природы. Посмотрим, что будет, если эффект окажется другим:

| удержание | выгода от TP | порог безубыточности |
|---|---|---|
| 15 % | 160 ₽ | 0.56 |
| 25 % | 400 ₽ | 0.33 |
| 35 % | 640 ₽ | 0.24 |

Как считается строка: при 15 % удержания V = 0.15 × 2400 = 360 ₽, выгода от TP = 360 − 200 = 160 ₽, порог = 200 / 360 ≈ 0.56.

При слабом эффекте бонус выгоден только почти наверняка уходящим, при сильном — почти всем подозрительным. Прибыль кампании меняется в разы, а модель — та же. Поэтому в отчёте указывают не одно число, а диапазон: «при удержании от 15 до 35 % кампания приносит от … до …». Самый надёжный способ узнать настоящий эффект бонуса — A/B-тест из главы 5: дать бонус случайной половине подозрительных гостей.

::: warn
Модель оттока предсказывает, **кто уйдёт**, но не **на кого подействует бонус**. Гость, который уйдёт при любом бонусе, — тоже «уходящий» для модели. Модели, которые предсказывают эффект воздействия, называют uplift-моделями; им нужны данные эксперимента.
:::

::: warn Типичные ошибки
- **Цена бонуса вычтена дважды.** Выгода от TP уже 400 = 600 − 200. Если затем вычесть 200 × (TP + FP), бонус уходящему посчитан дважды.
- **Порог = C / (выгода от TP).** 200 / 400 = 0.5 — неверно; в знаменателе выгода до вычета цены, 600.
- **Порог подобран на тесте и там же отчитан.** Прибыль на тесте после подбора порога — оптимистичная оценка. Честно: подбор на валидации, отчёт на тесте. В задачах этого урока для краткости подбираем на тесте; в итоговом проекте главы — честно, на прогнозах вне выборки.
- **FN считают расходом.** Упущенная выгода не попадает в прибыль кампании — иначе сравнение с «никому» перестаёт быть нулевым.
:::

::: quiz
Модель дала гостю риск ухода 0.95 — один из самых высоких в списке. Почему это ещё не значит, что бонус именно ему принесёт больше всего?

- [x] Модель предсказывает, уйдёт ли гость, а не подействует ли на него бонус: возможно, он уйдёт при любом бонусе
  > Расчёт прибыли держится на допущении «бонус удерживает 25 % уходящих» — одинаковом для всех. На кого бонус действует сильнее, показывают только данные эксперимента и uplift-модели.
- [ ] Вероятность 0.95 модель всегда завышает
  > Калибровку проверяют по группам, и в верхней группе лес, наоборот, занижает риск. Дело не в калибровке, а в том, что именно предсказывает модель.
- [ ] При риске выше 0.5 бонус невыгоден
  > Наоборот: при 25 % удержания бонус окупается уже при риске выше 1/3.
- [ ] Гостю с таким риском нужен бонус побольше — тогда он точно останется
  > Модель оттока ничего не знает о размере бонуса; его эффект — допущение маркетинга, а не вывод модели.
:::

{{practice: sensitivity, per-guest}}

## Практика

## task: cost-matrix | Прибыль по матрице ошибок | warmup

Кампания отправила бонусы 150 гостям, из них 90 действительно собирались уйти. Выгода от TP — 400 ₽, бонус стоит 200 ₽. Сохраните в `fp` число лишних бонусов, а в `profit` — ожидаемую прибыль кампании.

### starter
```python
tp = 90
sent = 150

```

### check
```python
assert need('fp') == 60, f'fp = {need("fp")}. Лишние бонусы — отправленные минус попавшие к уходящим.'
assert need('profit') == 90 * 400 - 60 * 200, f'profit = {need("profit")}. Прибыль = 400 × TP − 200 × FP.'
```

### hint
Отправили 150, к уходящим попали 90 — остальные получили бонус зря.

### hint
`fp = sent - tp`, затем `profit = 400 * tp - 200 * fp`.

### solution
```python
tp = 90
sent = 150
fp = sent - tp
profit = 400 * tp - 200 * fp
```

## task: break-even | Порог безубыточности | warmup

Новое предложение: бесплатный напиток за 150 ₽ удерживает 20 % уходящих, удержанный гость приносит 2400 ₽. Сохраните в `gain` ожидаемую выгоду от удержания одного уходящего (до вычета цены напитка), а в `threshold` — порог безубыточности по вероятности ухода (3 знака).

### starter
```python
cost = 150
retain = 0.20
value = 2400

```

### check
```python
assert close(need('gain'), 480), f'gain = {need("gain")}. Выгода = доля удержанных × ценность гостя.'
assert close(need('threshold'), round(150 / 480, 3)), f'threshold = {need("threshold")}. Порог = цена контакта / выгода.'
```

### hint
`gain = retain * value` — цену напитка из выгоды **не** вычитайте.

### hint
Порог — такое p, при котором p × gain = cost: `threshold = round(cost / gain, 3)`.

### solution
```python
cost = 150
retain = 0.20
value = 2400
gain = retain * value
threshold = round(cost / gain, 3)
```

### explain
Порог 0.31 — почти как у бонуса за 200 ₽ (0.33): напиток дешевле, но и удерживает хуже.

## task: toy-guests | Восемь гостей | warmup

Повторите «Разберём вместе» на своих данных. Для восьми гостей даны прогнозы `p` и факт `y`. Выгода от TP — 400 ₽, бонус — 200 ₽. Сохраните прибыль при пороге 0.5 в `profit_50`, при пороге 1/3 — в `profit_33`, и `extra` — сколько бонусов добавилось при снижении порога.

### starter
```python
import numpy as np
p = np.array([0.85, 0.70, 0.55, 0.42, 0.38, 0.31, 0.25, 0.12])
y = np.array([1, 0, 1, 1, 0, 0, 1, 0])

```

### check
```python
assert need('profit_50') == 600, f'profit_50 = {need("profit_50")}. При p > 0.5 бонус у трёх гостей: двое ушли, один остался.'
assert need('profit_33') == 800, f'profit_33 = {need("profit_33")}. При p > 1/3 бонус у пяти гостей.'
assert need('extra') == 2, f'extra = {need("extra")}.'
```

### hint
Посчитайте руками: при 0.5 бонус получают первые три (0.85, 0.70, 0.55); кто из них ушёл?

### hint
В коде: `send = p > 0.5`, `tp = (send & (y == 1)).sum()`, `fp = (send & (y == 0)).sum()`, прибыль `400 * tp - 200 * fp`. `extra` — разница `(p > 1/3).sum() - (p > 0.5).sum()`.

### solution
```python
import numpy as np
p = np.array([0.85, 0.70, 0.55, 0.42, 0.38, 0.31, 0.25, 0.12])
y = np.array([1, 0, 1, 1, 0, 0, 1, 0])

def profit(send):
    return int(400 * (send & (y == 1)).sum() - 200 * (send & (y == 0)).sum())

profit_50 = profit(p > 0.5)
profit_33 = profit(p > 1 / 3)
extra = int((p > 1 / 3).sum() - (p > 0.5).sum())
```

### explain
Два новых бонуса (0.42 и 0.38): один попал к уходящему (+400), другой — нет (−200). Итог +200 ₽. Гость с 0.25, который ушёл, остался без бонуса — порог 1/3 его не берёт, и в среднем это верно, даже если конкретно ему бонус бы помог.

## task: p-profit | Функция прибыли | warmup

Соберите функцию, которая считает ожидаемую прибыль кампании по маске «кому отправили бонус».

### parsons
```python
def profit(send, y, gain=400, cost=200):
    tp = (send & (y == 1)).sum()
    fp = (send & (y == 0)).sum()
    return int(gain * tp - cost * fp)
```

### check
```python
import pandas as _pd
f = need('profit')
y = _pd.Series([1, 0, 1, 0, 0])
s = _pd.Series([True, True, False, False, True])
assert f(s, y) == 400 - 400, f'profit на примере дала {f(s, y)}, а нужно 0: один TP (+400) и два FP (−400).'
assert f(s, y, gain=1000) == 600, 'Параметр gain должен использоваться вместо 400.'
```

### hint
Сначала считаем TP и FP, потом складываем.

### hint
Заголовок функции с параметрами по умолчанию идёт первым; `return` — последним, с отступом.

## task: rule-vs-model | Правило против модели | base

Сравните на тестовой выборке три стратегии: модель с порогом 0.5, модель с порогом 0.3 и правило «не был больше 30 дней» (`days_since_last > 30`). Сохраните прибыли в `p50`, `p30`, `rule30` (функция `profit` уже есть в заготовке) и в `best` — название лучшей: `"0.5"`, `"0.3"` или `"правило"`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
pp = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1]
def _pr(s):
    return int(400 * (s & (d == 1)).sum() - 200 * (s & (d == 0)).sum())
w = {'0.5': _pr(pp > 0.5), '0.3': _pr(pp > 0.3), 'правило': _pr(b['days_since_last'] > 30)}
assert need('p50') == w['0.5'], f'p50 = {need("p50")}, а нужно {w["0.5"]}: прибыль при p > 0.5.'
assert need('p30') == w['0.3'], f'p30 = {need("p30")}, а нужно {w["0.3"]}.'
assert need('rule30') == w['правило'], f'rule30 = {need("rule30")}, а нужно {w["правило"]}: маска X_test["days_since_last"] > 30.'
assert need('best') == max(w, key=w.get), f'best = {need("best")!r} — сравните три прибыли.'
```

### hint
Функция `profit` принимает маску «кому отправили». Для модели маска — сравнение вероятностей с порогом, для правила — сравнение признака с числом.

### hint
`profit(p > 0.5)`; для правила маска `X_test["days_since_last"] > 30`.

### hint
`res = {"0.5": p50, "0.3": p30, "правило": rule30}`, `best = max(res, key=res.get)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

p50 = profit(p > 0.5)
p30 = profit(p > 0.3)
rule30 = profit(X_test["days_since_last"] > 30)
res = {"0.5": p50, "0.3": p30, "правило": rule30}
best = max(res, key=res.get)
```

### explain
Порог 0.3 — 33 200 ₽, порог 0.5 — 31 200 ₽, правило «30 дней» — 21 400 ₽. Правило не бесполезно: 69 из 100 бонусов попадают к уходящим. Но модель с порогом около 1/3 ловит на 48 уходящих больше (117 против 69) — разница в 12 тысяч рублей на 600 гостях.

## task: margin | Средняя и предельная отдача | base

Финансист говорит: «При пороге 0.5 каждый бонус окупается лучше — зачем снижать?». Проверьте. Для порогов 0.5 и 0.35 сохраните `roi_50` и `roi_35` — прибыль, делённую на расходы на бонусы (200 × число бонусов), 3 знака. Затем возьмите только **дополнительных** гостей — с прогнозом выше 0.35, но не выше 0.5: сохраните их число `n_extra`, сколько из них ушли (`tp_extra`), и их вклад в прибыль `profit_extra`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
pp = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1]
def _pr(s):
    return int(400 * (s & (d == 1)).sum() - 200 * (s & (d == 0)).sum())
r50 = round(_pr(pp > 0.5) / (200 * (pp > 0.5).sum()), 3); r35 = round(_pr(pp > 0.35) / (200 * (pp > 0.35).sum()), 3)
assert close(need('roi_50'), r50, 0.0011) and close(need('roi_35'), r35, 0.0011), f'roi_50, roi_35 = {need("roi_50")}, {need("roi_35")}, а нужно {r50}, {r35}.'
m = (pp > 0.35) & (pp <= 0.5)
assert need('n_extra') == int(m.sum()), f'n_extra = {need("n_extra")}, а нужно {int(m.sum())}.'
assert need('tp_extra') == int((m & (d == 1)).sum()), f'tp_extra = {need("tp_extra")}.'
assert need('profit_extra') == _pr(m), f'profit_extra = {need("profit_extra")}, а нужно {_pr(m)}.'
```

### hint
ROI для порога t: `profit(p > t) / (200 * (p > t).sum())`.

### hint
Дополнительные гости: `extra = (p > 0.35) & (p <= 0.5)`; их вклад — та же функция `profit(extra)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

roi_50 = round(profit(p > 0.5) / (200 * (p > 0.5).sum()), 3)
roi_35 = round(profit(p > 0.35) / (200 * (p > 0.35).sum()), 3)
extra = (p > 0.35) & (p <= 0.5)
n_extra = int(extra.sum())
tp_extra = int((extra & (y_test == 1)).sum())
profit_extra = profit(extra)
```

### explain
Финансист прав про среднее: при 0.5 каждый вложенный рубль приносит 1.49 ₽ прибыли, при 0.35 — 1.07 ₽. Но решение принимают по **предельной** отдаче: 59 дополнительных бонусов попали к 26 уходящим и добавили 3 800 ₽. Пока очередная группа гостей приносит больше, чем стоит, её стоит включать, даже если средний ROI падает. Средний ROI имеет смысл максимизировать, только когда бюджет ограничен, — об этом урок «Когда бюджет ограничен».

## task: best-threshold | Порог по прибыли | base

Переберите пороги от 0.05 до 0.95 с шагом 0.05 (`np.arange(0.05, 0.96, 0.05).round(2)`) и найдите порог с наибольшей прибылью. Сохраните таблицу `curve` (DataFrame со столбцами `threshold` и `profit`), лучший порог в `best_t` и его прибыль в `best_profit`. Если максимум достигается на нескольких порогах, берите наименьший (так делает `idxmax`).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
pp = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1]
ts = _np.arange(0.05, 0.96, 0.05).round(2)
pr = [int(400 * ((pp > t) & (d == 1)).sum() - 200 * ((pp > t) & (d == 0)).sum()) for t in ts]
cv = need('curve', _pd.DataFrame)
assert {'threshold', 'profit'} <= set(cv.columns), f'Столбцы curve: {list(cv.columns)}, нужны threshold и profit.'
assert len(cv) == len(ts), f'В curve {len(cv)} строк, а порогов {len(ts)}.'
assert list(cv['profit'].astype(int)) == pr, 'Прибыли в curve не совпадают с ожидаемыми — проверьте маску p > threshold.'
i = int(_np.argmax(pr))
assert close(need('best_t'), ts[i]), f'best_t = {need("best_t")}, а нужно {ts[i]}.'
assert need('best_profit') == pr[i], f'best_profit = {need("best_profit")}.'
```

### hint
Соберите список словарей `{"threshold": t, "profit": profit(p > t)}` в цикле и превратите его в DataFrame.

### hint
Строка с максимумом: `curve.loc[curve["profit"].idxmax()]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

def profit(send):
    tp = (send & (y_test == 1)).sum()
    fp = (send & (y_test == 0)).sum()
    return int(400 * tp - 200 * fp)

rows = [{"threshold": t, "profit": profit(p > t)} for t in np.arange(0.05, 0.96, 0.05).round(2)]
curve = pd.DataFrame(rows)
top = curve.loc[curve["profit"].idxmax()]
best_t = top["threshold"]
best_profit = int(top["profit"])
```

### explain
Максимум 35 000 ₽ — при пороге 0.35, рядом с теоретическими 1/3; столько же даёт и 0.45 — кривая плоская около вершины: пороги 0.3–0.45 дают 33–35 тыс. Это хорошо — небольшая ошибка в пороге почти не стоит денег. Подбор порога на тесте — упрощение: честно подбирать на валидации или кросс-валидации (глава 6, урок «Честное сравнение моделей»).

## task: sensitivity | Что если бонус работает хуже | base

Посчитайте лучший порог и прибыль при трёх вариантах удержания: 15 %, 25 % и 35 %. Выгода от TP = удержание × 2400 − 200, расход на FP = 200. Пороги — те же `np.arange(0.05, 0.96, 0.05).round(2)`. Сохраните DataFrame `sens` со столбцами `retain`, `best_t`, `best_profit` (по строке на вариант, в порядке 0.15, 0.25, 0.35).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]
ts = np.arange(0.05, 0.96, 0.05).round(2)

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
pp = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1]
ts = _np.arange(0.05, 0.96, 0.05).round(2)
s = need('sens', _pd.DataFrame)
assert {'retain', 'best_t', 'best_profit'} <= set(s.columns), f'Столбцы sens: {list(s.columns)}.'
assert len(s) == 3, f'В sens {len(s)} строк, нужно 3.'
for k, r in enumerate([0.15, 0.25, 0.35]):
    gain = r * 2400 - 200
    pr = [gain * ((pp > t) & (d == 1)).sum() - 200 * ((pp > t) & (d == 0)).sum() for t in ts]
    i = int(_np.argmax(pr))
    row = s.iloc[k]
    assert close(row['retain'], r), f'Строка {k}: retain = {row["retain"]}, ожидалось {r}.'
    assert close(row['best_t'], ts[i]), f'При удержании {r}: best_t = {row["best_t"]}, а нужно {ts[i]}.'
    assert close(row['best_profit'], pr[i], 1), f'При удержании {r}: best_profit = {row["best_profit"]}, а нужно {round(pr[i])}.'
```

### hint
Внешний цикл по удержанию, внутри — перебор порогов. Для каждого удержания своя выгода `gain = r * 2400 - 200`.

### hint
Внутри: `profits = [gain * ((p > t) & (y_test == 1)).sum() - 200 * ((p > t) & (y_test == 0)).sum() for t in ts]`, лучший — `np.argmax(profits)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]
ts = np.arange(0.05, 0.96, 0.05).round(2)

rows = []
for r in [0.15, 0.25, 0.35]:
    gain = r * 2400 - 200
    profits = [gain * ((p > t) & (y_test == 1)).sum() - 200 * ((p > t) & (y_test == 0)).sum() for t in ts]
    i = int(np.argmax(profits))
    rows.append({"retain": r, "best_t": ts[i], "best_profit": profits[i]})
sens = pd.DataFrame(rows)
```

### explain
При удержании 15 % лучший порог 0.45 и прибыль около 10 800 ₽, при 35 % — порог 0.35 и около 62 000 ₽. Прибыль меняется вшестеро, а порог гораздо меньше. Вывод для отчёта: модель полезна при любом из вариантов, но сколько она принесёт, решает эффект бонуса — его стоит измерить экспериментом.

## task: calib | Калибровка у порога | plus

Проверьте калибровку леса около порога: возьмите гостей теста с прогнозом от 0.25 до 0.45 включительно. Сохраните в `n_near` их число, в `mean_p` — средний прогноз, в `fact` — долю реально ушедших (оба — 3 знака) и в `gap` — `fact - mean_p` (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
pp = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=d.index)
m = pp.between(0.25, 0.45)
mp, fa = round(pp[m].mean(), 3), round(d[m].mean(), 3)
assert need('n_near') == int(m.sum()), f'n_near = {need("n_near")}, а нужно {int(m.sum())}: прогноз от 0.25 до 0.45 включительно.'
assert close(need('mean_p'), mp) and close(need('fact'), fa), f'mean_p, fact = {need("mean_p")}, {need("fact")}, а нужно {mp}, {fa}.'
assert close(need('gap'), round(fa - mp, 3)), f'gap = {need("gap")}: fact − mean_p.'
```

### hint
«Включительно» — значит `>=` и `<=`.

### hint
Маска: `(p >= 0.25) & (p <= 0.45)`. Долю ушедших берите из `y_test` с той же маской: `y_test[mask].mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

mask = (p >= 0.25) & (p <= 0.45)
n_near = int(mask.sum())
mean_p = round(p[mask].mean(), 3)
fact = round(y_test[mask].mean(), 3)
gap = round(fact - mean_p, 3)
```

### explain
Около порога лес завышает риск примерно на 10 п.п.: обещает 0.35, а уходит четверть. Для 77 гостей это около двух стандартных ошибок — скорее всего, не случайность. Поэтому лучший порог по прибыли (0.35–0.45) оказался чуть выше теоретической 1/3. Что с этим делают: подбирают порог перебором по прибыли или калибруют вероятности (в sklearn для этого есть `CalibratedClassifierCV`).

## task: per-guest | Ценность гостя разная | star

Допущение «каждый удержанный приносит 2400 ₽» грубое. Пусть ценность гостя за полгода = 0.3 × `avg_check` × `visits_90d` × 2 (маржа 30 %, два квартала). Отправляйте бонус, если p × 0.25 × ценность > 200. Сохраните в `n_value` число бонусов по такому правилу, в `profit_value` — ожидаемую прибыль (сумма 0.25 × ценность по ушедшим получателям минус 200 × число получателей, округлите до целого), а в `share_low` — долю ушедших гостей теста с ценностью меньше 2400 ₽ (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
pp = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1]
v = 0.3 * b['avg_check'] * b['visits_90d'] * 2
s = pp * 0.25 * v > 200
pv = round((0.25 * v[s & (d == 1)]).sum() - 200 * s.sum())
assert need('n_value') == int(s.sum()), f'n_value = {need("n_value")}, а нужно {int(s.sum())}.'
assert close(need('profit_value'), pv, 1), f'profit_value = {need("profit_value")}, а нужно {pv}.'
sl = round((v[d == 1] < 2400).mean(), 3)
assert close(need('share_low'), sl), f'share_low = {need("share_low")}, а нужно {sl}: доля ушедших (y_test == 1) с ценностью < 2400.'
```

### hint
Ценность считайте по `X_test`: `value = 0.3 * X_test["avg_check"] * X_test["visits_90d"] * 2`. Пропуски `avg_check` уже заменены нулём.

### hint
Выгода по получателям, которые реально ушли: `(0.25 * value[send & (y_test == 1)]).sum()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

value = 0.3 * X_test["avg_check"] * X_test["visits_90d"] * 2
send = p * 0.25 * value > 200
n_value = int(send.sum())
profit_value = round((0.25 * value[send & (y_test == 1)]).sum() - 200 * send.sum())
share_low = round((value[y_test == 1] < 2400).mean(), 3)
```

### explain
Бонусов получается всего несколько десятков, а прибыль — в разы меньше, чем при «2400 ₽ каждому». Причина в данных: уходящие гости и так ходили редко, и почти у всех из них ценность по прошлым визитам ниже 2400 ₽. «Ценные» и «уходящие» — во многом разные люди. Какое допущение о ценности верное, решает бизнес, а не модель: прошлые визиты недооценивают гостя, который ходил редко, но остался бы надолго.
