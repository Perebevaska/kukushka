---
title: Когда бюджет ограничен
lead: "Финансовый отдел выделил деньги только на 60 бонусов. Порог тут не поможет — нужен список «кому в первую очередь». Учимся ранжировать гостей по риску, читать кривую охвата и сравнивать модель с правилом при одном и том же бюджете."
files: [guests_churn.csv]
recap:
  - "При ограниченном бюджете берут k гостей с наибольшим прогнозом: `s.nlargest(k)` или сортировка."
  - "Точность в топ-k (precision@k) — доля уходящих среди k выбранных; охват (recall@k) — доля всех уходящих, попавших в топ-k."
  - "Кривая охвата: по оси X — доля гостей, которым отправили бонус, по Y — доля пойманных уходящих. Чем выше над диагональю, тем лучше ранжирование."
  - "Случайный выбор ловит уходящих пропорционально бюджету — это базовая линия."
  - "Бюджет не обязательно тратить целиком: если в топ-k попадают гости ниже порога безубыточности, они приносят убыток."
  - "Модели сравнивают при одинаковом бюджете — так сравнение честное."
---

## Топ-k вместо порога

В уроке «Из прогноза — в деньги» мы отправляли бонус всем, у кого прогноз выше порога. Деньги в этом уроке считаем по тому же допущению — бонус удерживает 25 % уходящих (+400 ₽ за уходящего, −200 ₽ за лишний бонус), чтобы числа были сопоставимы. Пилот из урока «Пилот и P&L» показал 20 %; чтобы считать по нему, достаточно поменять 400 на 2400 × 0.20 − 200 = 280. Но бюджет часто фиксирован: «есть 12 000 ₽ — это 60 бонусов». Тогда вопрос другой: **кому отдать эти 60**. Ответ — тем, у кого модель видит наибольший риск.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

top = risk.nlargest(60).index          # 60 гостей с наибольшим риском
send = X_test.index.isin(top)          # маска True/False для всех 600
print("уходящих среди выбранных:", y_test[send].mean().round(3))
print("пойманных уходящих:", y_test[send].sum(), "из", y_test.sum())
```

**Что здесь происходит:**

- `risk` — вероятности, сложенные в Series **с индексом гостей** `X_test.index`. Без индекса `nlargest` вернул бы позиции, и связать их с `y_test` было бы сложнее.
- `risk.nlargest(60).index` — номера 60 гостей с наибольшим риском.
- `X_test.index.isin(top)` — маска на всех 600: `True` у выбранных.
- `y_test[send].mean()` — доля уходящих среди выбранных (среднее нулей и единиц — доля единиц).

`nlargest(60)` — 60 наибольших значений Series, как `ORDER BY risk DESC LIMIT 60`. Вероятности мы сложили в Series с индексом гостей, чтобы потом легко найти их в `X_test` и `y_test`.

Из 60 выбранных уходят 57 — точность 95 %. Но всего уходящих в тесте 134, и бюджет позволил поймать только 42 %.

::: sql
```sql
SELECT guest_id FROM scores ORDER BY risk DESC LIMIT 60
```
:::

::: quiz
Бюджета хватает ровно на 100 бонусов. Как выбрать гостей?

- [x] Отсортировать по риску и взять 100 самых рискованных
  > При фиксированном бюджете порог не нужен: важен порядок. Поэтому модель оценивают метриками «в топ-k».
- [ ] Всем с вероятностью выше 0.5, сколько бы их ни было
  > Таких может оказаться 40 или 300 — бюджет не совпадёт.
- [ ] Случайные 100 гостей
  > Это базовая линия для сравнения, а не стратегия.
- [ ] Самых давних гостей
  > Давность — одно из правил, но модель обычно ранжирует лучше.
:::

{{practice: top-mask}}

## Две метрики для топ-k

Для ранжирования удобны две простые величины:

- **точность в топ-k** (precision@k) — какая доля выбранных действительно уходит;
- **охват в топ-k** (recall@k) — какую долю всех уходящих мы поймали.

Руками на шести гостях, отсортированных по риску:

| гость | риск | ушёл? |
|---|---|---|
| A | 0.9 | да |
| B | 0.8 | да |
| C | 0.6 | нет |
| D | 0.4 | да |
| E | 0.3 | нет |
| F | 0.1 | нет |

Всего уходящих трое. При k = 2: выбраны A, B — оба уходят, точность 2/2 = **1.0**, охват 2/3 = **0.67**. При k = 4: A, B, C, D — уходят трое, точность 3/4 = **0.75**, охват 3/3 = **1.0**. Больше бюджет — выше охват, ниже точность.

::: figure topk-denoms
Один и тот же числитель — уходящие в рамке топ-k. Точность делит его на k, охват — на всех уходящих (их трое при любом k).
:::

::: predict
```python static
import pandas as pd
risk = pd.Series([0.9, 0.8, 0.6, 0.4, 0.3, 0.1])
y = pd.Series([1, 1, 0, 1, 0, 0])
top = risk.nlargest(3).index
print(y[top].mean().round(2), (y[top].sum() / y.sum()).round(2))
```

- `0.67 1.0`
- [x] `0.67 0.67`
- `1.0 0.67`

Почему: в топ-3 — A, B, C, уходят двое из трёх (точность 0.67), а из трёх уходящих поймано двое (охват тоже 0.67). Знаменатели разные: у точности — k, у охвата — все уходящие.
:::

На тесте:

| k | точность в топ-k | охват | прибыль |
|---|---|---|---|
| 25 | 1.00 | 0.19 | 10 000 ₽ |
| 60 | 0.95 | 0.43 | 22 200 ₽ |
| 100 | 0.85 | 0.63 | 31 000 ₽ |
| 168 | 0.67 | 0.84 | 34 200 ₽ |
| 300 | 0.42 | 0.93 | 15 000 ₽ |

С ростом k точность падает, охват растёт, а прибыль сначала растёт, потом падает. Максимум — около k = 150–170: дальше в список попадают гости с прогнозом ниже порога безубыточности 1/3, и каждый новый бонус в среднем теряет деньги.

::: tip
Если бюджет больше, чем выгодно потратить, — не тратьте весь. Правило: k = min(бюджет, число гостей с прогнозом выше порога безубыточности).
:::

{{practice: at-k}}

## Случайный выбор как базовая линия

Что было бы, если бы бонусы раздавали случайным 60 гостям? Уходит 22.3 % гостей, значит, в среднем среди них окажется 60 × 0.223 ≈ 13 уходящих, а прибыль на одного получателя 0.223 × 400 − 0.777 × 200 ≈ −66 ₽. Случайная раздача убыточна при любом бюджете.

::: predict
```python static
rate = 0.25
k = 80
print(k * rate * 400 - k * (1 - rate) * 200)
```

- `8000.0`
- [x] `-4000.0`
- `4000.0`

Почему: 20 уходящих × 400 = 8000, 60 лишних × 200 = 12 000. Чтобы случайная раздача окупилась, уходящих должно быть больше трети.
:::

{{practice: random-base}}

## Кривая охвата

Удобно смотреть на все бюджеты сразу. Сортируем гостей по риску и считаем, какую долю уходящих мы поймали, отправив бонус первым 1 %, 2 %, … 100 % гостей. Это **кривая охвата** (её ещё называют gain-кривой):

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = model.predict_proba(X_test)[:, 1]

def gains(score, y):
    order = np.argsort(-score)                 # от большего риска к меньшему
    caught = np.cumsum(y.values[order])        # сколько уходящих поймали после каждого гостя
    share_sent = np.arange(1, len(y) + 1) / len(y)
    return share_sent, caught / y.sum()

x1, y1 = gains(risk, y_test)
x2, y2 = gains(X_test["days_since_last"].values, y_test)
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(x1, y1, label="модель")
ax.plot(x2, y2, label="давность визита")
ax.plot([0, 1], [0, 1], "--", color="grey", label="случайно")
ax.set_xlabel("доля гостей с бонусом")
ax.set_ylabel("доля пойманных уходящих")
ax.legend()
plt.show()
```

**Что здесь происходит:**

- `gains(score, y)` — функция для любого «списка приоритетов»: прогноза модели или просто признака.
- `np.argsort(-score)` — номера гостей от большего значения к меньшему.
- `y.values[order]` — ответы в этом порядке; `np.cumsum` — сколько уходящих накопилось после 1-го, 2-го, … гостя. На шести гостях выше: 1, 2, 2, 3, 3, 3 → доли 0.33, 0.67, 0.67, 1, 1, 1.
- `share_sent` — доля списка, которой отправили бонус: 1/600, 2/600, …
- Для давности визита сортировка по самому признаку: дольше не был — выше в списке.

::: figure gains-toy
Кривая охвата на шести гостях из примера выше: каждая точка — ещё один гость из списка. Уходящий поднимает кривую на 1/3, оставшийся сдвигает её только вправо.
:::

Диагональ — случайный выбор: 30 % бонусов ловят 30 % уходящих. Кривая модели поднимается круче: 10 % бонусов ловят больше 40 % уходящих. Сортировка по давности визита — тоже неплохой список, но ниже модели почти на всём протяжении.

::: note
Площадь под кривой охвата тесно связана с ROC-AUC из главы 7: обе меряют качество **ранжирования**, а не конкретного порога. Если бизнес работает со списками «топ-N», ранжирование важнее точной вероятности.
:::

::: quiz
Кривая охвата новой модели почти лежит на диагонали. Что это значит?

- [x] Модель ранжирует гостей не лучше случайного выбора: при любом бюджете она ловит столько же уходящих, сколько раздача наугад
  > Диагональ — это случайный выбор: x % бонусов ловят x % уходящих. Польза модели видна только как подъём над ней.
- [ ] Модель плохо откалибрована, но ранжирует хорошо
  > Кривая охвата зависит только от порядка гостей, а не от точных вероятностей. Хорошее ранжирование подняло бы её над диагональю.
- [ ] Бюджет слишком мал, чтобы модель проявила себя
  > Кривая показывает сразу все бюджеты — от 0 до 100 % гостей. Если она на диагонали везде, дело не в бюджете.
- [ ] Модель идеальна: она ловит уходящих ровно пропорционально бюджету
  > Идеальная модель сначала собрала бы всех уходящих — кривая круто взлетела бы у левого края.
:::

{{practice: p-gains, gains-plot}}

## Сравнение при одном бюджете

Две модели или модель и правило честно сравнивать при **одинаковом** k. Правило «давность визита» при 60 бонусах даёт 19 800 ₽, модель — 22 200 ₽. При 100 бонусах разрыв больше: 21 400 против 31 000 ₽. Чем больше бюджет, тем сильнее модель выигрывает: самых очевидных уходящих находят оба способа, а модель лучше видит неочевидных — новичков, гостей с жалобами на доставку.

{{practice: profit-k, budget-cap, two-offers, rule-gains}}

## Разберём вместе: во сколько раз лучше случайного

Финансисту проще одно число, чем кривая. Это **лифт** (lift@k) — во сколько раз точность в топ-k выше доли уходящих среди всех:

- доля уходящих в тесте: 134 / 600 = **0.223** — столько поймает случайная раздача;
- точность в топ-60: 57 / 60 = **0.95**;
- лифт: 0.95 / 0.223 ≈ **4.3**.

::: tip Аналогия
Бариста раздаёт 60 пробников нового латте. Если раздать первым встречным, напиток купит примерно обычная доля гостей; если тем, кто уже берёт сладкие напитки, — заметно больше. Топ-k — это «кому достанутся 60 пробников», а лифт — во сколько раз прицельная раздача лучше раздачи наугад. Где аналогия хромает: лифт говорит о точности попадания, а не о деньгах — при k = 100 лифт ниже, чем при k = 60, а прибыль выше.
:::

Что получилось: каждый бонус по списку модели попадает к уходящему в 4.3 раза чаще, чем случайный. При k = 100 лифт 0.85 / 0.223 ≈ 3.8, при k = 150 — около 3.2. Лифт падает с ростом бюджета так же, как точность: самые очевидные уходящие уже в списке.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

base = y_test.mean()
for k in [60, 100, 150]:
    prec = y_test[risk.nlargest(k).index].mean()
    print(f"k={k}: точность {prec:.2f}, лифт {prec / base:.1f}")
```

::: warn Типичные ошибки
- **Охват делят на k.** Знаменатель охвата — все уходящие теста (134), а не число выбранных.
- **`nlargest` на массиве.** У numpy-массива его нет; сложите прогнозы в Series с индексом `X_test.index`.
- **Модели сравнивают при разных k.** «Модель A: точность 0.95, модель B: 0.85» ничего не значит, если A выбирала 60 гостей, а B — 100.
- **Тратят весь бюджет.** Если в топ-k попали гости с прогнозом ниже порога безубыточности, лишние бонусы уменьшают прибыль.
:::

{{practice: lift}}

## Практика

## task: top-mask | Маска топ-k | warmup

Даны прогнозы шести гостей. Сохраните в `send` маску (Series `True/False` с тем же индексом) для двух гостей с наибольшим риском.

### starter
```python
import pandas as pd
risk = pd.Series([0.1, 0.8, 0.3, 0.9, 0.5, 0.2], index=["A", "B", "C", "D", "E", "F"])

```

### check
```python
import pandas as _pd
s = need('send', _pd.Series)
assert list(s.index) == list('ABCDEF'), 'Индекс send должен совпадать с индексом risk — используйте risk.index.isin(...).'
assert list(s.astype(bool)) == [False, True, False, True, False, False], f'send = {list(s)}: выбраны должны быть B и D.'
```

### hint
Сначала найдите двух гостей с наибольшим риском — `risk.nlargest(2)`. Вам нужен их индекс.

### hint
`top = risk.nlargest(2).index`, затем `risk.index.isin(top)` — это массив; оберните его в `pd.Series(..., index=risk.index)`.

### solution
```python
import pandas as pd
risk = pd.Series([0.1, 0.8, 0.3, 0.9, 0.5, 0.2], index=["A", "B", "C", "D", "E", "F"])
top = risk.nlargest(2).index
send = pd.Series(risk.index.isin(top), index=risk.index)
```

## task: p-gains | Нарастающий охват | warmup

Соберите код, который печатает долю пойманных уходящих после каждого гостя в порядке убывания риска.

### parsons
```python
import numpy as np
risk = np.array([0.2, 0.9, 0.6, 0.1])
y = np.array([0, 1, 0, 1])
order = np.argsort(-risk)
caught = np.cumsum(y[order])
print((caught / y.sum()).tolist())
```

### check
```python
assert _lines == ['[0.5, 0.5, 0.5, 1.0]'], f'Сейчас: {_lines}. Сначала порядок, потом нарастающая сумма, потом доля.'
```

### hint
Порядок нужен раньше нарастающей суммы, а сумма — раньше деления.

### hint
Проверьте руками: порядок по риску — 0.9, 0.6, 0.2, 0.1, ответы в этом порядке 1, 0, 0, 1; нарастающая сумма 1, 1, 1, 2; доли 0.5, 0.5, 0.5, 1.0.

## task: at-k | Точность и охват в топ-k | warmup

Посчитайте для модели при бюджете 100 бонусов точность в топ-k `prec_k` и охват `rec_k` (оба — 3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
top = r.nlargest(100).index
pk, rk = round(d[top].mean(), 3), round(d[top].sum() / d.sum(), 3)
assert close(need('prec_k'), pk), f'prec_k = {need("prec_k")}, а нужно {pk}: доля уходящих среди 100 выбранных.'
assert close(need('rec_k'), rk), f'rec_k = {need("rec_k")}, а нужно {rk}: пойманные уходящие / все уходящие теста.'
```

### hint
`top = risk.nlargest(100).index`, затем `y_test[top]` — ответы для выбранных.

### hint
Точность — `y_test[top].mean()`; охват — `y_test[top].sum() / y_test.sum()`: в знаменателе все уходящие теста.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

top = risk.nlargest(100).index
prec_k = round(y_test[top].mean(), 3)
rec_k = round(y_test[top].sum() / y_test.sum(), 3)
```

## task: profit-k | Прибыль по бюджетам | base

Посчитайте прибыль (400 ₽ за уходящего, −200 ₽ за лишний бонус) для бюджетов k = 20, 40, …, 300 (`range(20, 301, 20)`). Сохраните DataFrame `by_k` со столбцами `k` и `profit`, а в `best_k` — бюджет с наибольшей прибылью (при равенстве — меньший).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
want = []
for k in range(20, 301, 20):
    yy = d[r.nlargest(k).index]
    want.append(int(400 * yy.sum() - 200 * (len(yy) - yy.sum())))
t = need('by_k', _pd.DataFrame)
assert list(t['k']) == list(range(20, 301, 20)), f'Столбец k: {list(t["k"])[:5]}…, нужен range(20, 301, 20).'
assert [int(v) for v in t['profit']] == want, f'Прибыли не совпадают. Первые три ожидались {want[:3]}, у вас {[int(v) for v in t["profit"]][:3]}.'
bk = list(range(20, 301, 20))[want.index(max(want))]
assert need('best_k') == bk, f'best_k = {need("best_k")}, а нужно {bk}.'
```

### hint
Цикл `for k in range(20, 301, 20)`, на каждом шаге — словарь `{"k": k, "profit": ...}` в список, в конце `pd.DataFrame(rows)`.

### hint
Для каждого k: `yy = y_test[risk.nlargest(k).index]`, прибыль `400 * yy.sum() - 200 * (k - yy.sum())`.

### hint
`best_k = int(by_k.loc[by_k["profit"].idxmax(), "k"])` — `idxmax` при равенстве берёт первую строку, то есть меньший k.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

rows = []
for k in range(20, 301, 20):
    yy = y_test[risk.nlargest(k).index]
    rows.append({"k": k, "profit": int(400 * yy.sum() - 200 * (k - yy.sum()))})
by_k = pd.DataFrame(rows)
best_k = int(by_k.loc[by_k["profit"].idxmax(), "k"])
```

### explain
Максимум 35 600 ₽ при k = 140. Дальше прибыль падает: при 300 бонусах — 15 000 ₽, меньше половины. Около вершины кривая плоская (120–180 бонусов дают 33–36 тыс.), поэтому точное k не критично, а вот «раздать всем подозрительным» — дорогая ошибка.

## task: random-base | Случайная раздача | base

Посчитайте ожидаемую прибыль случайной раздачи k бонусов по формуле k × (rate × 400 − (1 − rate) × 200), где rate — доля уходящих в тесте. Сохраните `rnd_60` для k = 60 (округлите до целого) и `gain_60` — на сколько рублей модель при k = 60 лучше случайной раздачи (тоже до целого).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
rate = d.mean()
rn = round(60 * (rate * 400 - (1 - rate) * 200))
yy = d[r.nlargest(60).index]
m = 400 * yy.sum() - 200 * (60 - yy.sum())
assert close(need('rnd_60'), rn, 1), f'rnd_60 = {need("rnd_60")}, а нужно {rn}.'
assert close(need('gain_60'), round(m - 60 * (rate * 400 - (1 - rate) * 200)), 1), f'gain_60 = {need("gain_60")}: прибыль модели при k = 60 минус rnd_60.'
```

### hint
`rate = y_test.mean()`. Прибыль модели при k = 60 считайте как в прошлой задаче.

### hint
Случайная раздача попадает в уходящих с той же долей, что и в целом по тесту: из k бонусов в среднем `k × rate` достанутся уходящим (+400 каждому), остальные — остающимся (−200). Подставьте `rate = y_test.mean()` в формулу и округлите в самом конце. Прибыль модели — как в прошлой задаче: `nlargest(60)` по риску, затем +400 за уходящего и −200 за остальных.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

rate = y_test.mean()
rnd = 60 * (rate * 400 - (1 - rate) * 200)
rnd_60 = round(rnd)
yy = y_test[risk.nlargest(60).index]
model_60 = 400 * yy.sum() - 200 * (60 - yy.sum())
gain_60 = round(model_60 - rnd)
```

### explain
Случайная раздача 60 бонусов теряет около 4 000 ₽, модель зарабатывает 22 200 ₽: польза модели — больше 26 тыс. ₽ на 600 гостей. Именно эту разницу, а не прибыль кампании, честно записывать в заслуги модели.

## task: lift | Лифт для финансиста | base

Сохраните долю уходящих в тесте `base` (3 знака), лифт модели для бюджетов 60 и 150 — `lift_60`, `lift_150` (2 знака), и лифт правила «давность визита» для 60 гостей с наибольшим `days_since_last` — `lift_rule_60` (2 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
bs = d.mean()
l60 = round(d[r.nlargest(60).index].mean() / bs, 2); l150 = round(d[r.nlargest(150).index].mean() / bs, 2)
lr = round(d[b['days_since_last'].nlargest(60).index].mean() / bs, 2)
assert close(need('base'), round(bs, 3)), f'base = {need("base")}.'
assert close(need('lift_60'), l60, 0.011) and close(need('lift_150'), l150, 0.011), f'lift_60, lift_150 = {need("lift_60")}, {need("lift_150")}, а нужно {l60}, {l150}.'
assert close(need('lift_rule_60'), lr, 0.011), f'lift_rule_60 = {need("lift_rule_60")}, а нужно {lr}.'
```

### hint
Лифт = точность в топ-k / `base`. Точность: `y_test[risk.nlargest(k).index].mean()`.

### hint
Для правила ранжируйте по признаку: `X_test["days_since_last"].nlargest(60).index`. Делите на неокруглённую `base`, округляйте в конце.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

rate = y_test.mean()
base = round(rate, 3)
lift_60 = round(y_test[risk.nlargest(60).index].mean() / rate, 2)
lift_150 = round(y_test[risk.nlargest(150).index].mean() / rate, 2)
lift_rule_60 = round(y_test[X_test["days_since_last"].nlargest(60).index].mean() / rate, 2)
```

### explain
Модель в топ-60 — лифт 4.25, в топ-150 — 3.19. Правило «давность визита» в топ-60 даёт 3.96: 53 уходящих из 60 против 57 у модели. На маленьком бюджете простой список почти так же хорош — самых давно не приходивших найти легко. Разница растёт с бюджетом, а лифт удобен для отчёта: «каждый бонус попадает к уходящему вчетверо чаще случайного».

## task: gains-plot | Кривая охвата | base

Постройте кривую охвата для модели и диагональ случайного выбора на одном графике. Подпишите оси: X — `"доля гостей с бонусом"`, Y — `"доля пойманных уходящих"`. Сохраните в `at10` долю пойманных уходящих, если бонус получили первые 10 % гостей (60 человек), 3 знака.

### setup
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = model.predict_proba(X_test)[:, 1]
```

### starter
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1]
cg = _np.cumsum(d.values[_np.argsort(-r)]) / d.sum()
ax = ax_of(0)
assert len(ax.lines) >= 2, f'На графике {len(ax.lines)} линий, нужны кривая модели и диагональ.'
assert ax.get_xlabel() == 'доля гостей с бонусом' and ax.get_ylabel() == 'доля пойманных уходящих', 'Проверьте подписи осей — они должны совпадать с условием дословно.'
ys = [l.get_ydata() for l in ax.lines]
assert any(len(v) == len(d) and close(v[59], cg[59]) for v in ys), 'Не нашёл кривую модели: 600 точек, по Y — доля пойманных уходящих.'
assert close(need('at10'), round(cg[59], 3)), f'at10 = {need("at10")}, а нужно {round(cg[59], 3)}.'
```

### hint
Как в теории: `order = np.argsort(-risk)`, `caught = np.cumsum(y_test.values[order]) / y_test.sum()`, по X — `np.arange(1, 601) / 600`.

### hint
Значение после 60 гостей — элемент с номером 59: `caught[59]`.

### hint
Диагональ — линия из двух точек: `ax.plot([0, 1], [0, 1], "--")`.

### solution
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = model.predict_proba(X_test)[:, 1]

order = np.argsort(-risk)
caught = np.cumsum(y_test.values[order]) / y_test.sum()
share = np.arange(1, len(y_test) + 1) / len(y_test)
fig, ax = plt.subplots()
ax.plot(share, caught, label="модель")
ax.plot([0, 1], [0, 1], "--", color="grey", label="случайно")
ax.set_xlabel("доля гостей с бонусом")
ax.set_ylabel("доля пойманных уходящих")
ax.legend()
plt.show()
at10 = round(caught[59], 3)
```

### explain
10 % бонусов ловят 42.5 % уходящих — в 4 с лишним раза больше, чем диагональ (10 %). Это тот же лифт 4.3 из «Разберём вместе», только прочитанный по кривой: кривая охвата показывает лифт сразу для всех бюджетов.

## task: budget-cap | Не тратить лишнее | base

Финансисты выделили 250 бонусов. Примените правило из подсказки урока: k = min(бюджет, число гостей с прогнозом выше 1/3). Сохраните `n_above` — число гостей выше порога, `k_use` — сколько бонусов отправить, `profit_all` — прибыль, если раздать все 250 по списку модели, `profit_cap` — если отправить только `k_use`, и `saved` — разницу.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
budget = 250
def profit_top(k):
    yy = y_test[risk.nlargest(k).index]
    return int(400 * yy.sum() - 200 * (k - yy.sum()))
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk, budget

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
def _pt(k):
    yy = d[r.nlargest(k).index]; return int(400 * yy.sum() - 200 * (k - yy.sum()))
na = int((r > 1 / 3).sum()); ku = min(250, na)
assert need('n_above') == na, f'n_above = {need("n_above")}, а нужно {na}: (risk > 1/3).sum().'
assert need('k_use') == ku, f'k_use = {need("k_use")}, а нужно {ku}.'
assert need('profit_all') == _pt(250) and need('profit_cap') == _pt(ku), f'profit_all, profit_cap = {need("profit_all")}, {need("profit_cap")}, а нужно {_pt(250)}, {_pt(ku)}.'
assert need('saved') == _pt(ku) - _pt(250), f'saved = {need("saved")}.'
```

### hint
`n_above = int((risk > 1 / 3).sum())`, `k_use = min(budget, n_above)`.

### hint
Функция `profit_top(k)` уже в заготовке: `profit_all = profit_top(budget)`, `profit_cap = profit_top(k_use)`.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
budget = 250

def profit_top(k):
    yy = y_test[risk.nlargest(k).index]
    return int(400 * yy.sum() - 200 * (k - yy.sum()))

n_above = int((risk > 1 / 3).sum())
k_use = min(budget, n_above)
profit_all = profit_top(budget)
profit_cap = profit_top(k_use)
saved = profit_cap - profit_all
```

### explain
Выше порога безубыточности 168 гостей. Если отправить им — 34 200 ₽, если раздать все 250 — 24 400 ₽: последние 82 бонуса уничтожили почти 10 тысяч. Остаток бюджета — не «недоосвоение», а сэкономленные деньги. Учтите: оптимум по задаче «Прибыль по бюджетам» (k = 140) чуть левее 168 — из-за калибровки, о которой шла речь в прошлом уроке.

## task: two-offers | Бонус или звонок | plus

У отдела есть второй инструмент — звонок менеджера: стоит 500 ₽, удерживает 50 % уходящих (удержанный приносит 2400 ₽). Для звонка: выгода от уходящего 0.5 × 2400 − 500 = 700 ₽, лишний звонок −500 ₽. Бюджет на звонки — 30 000 ₽ (60 звонков), на бонусы — тоже 30 000 ₽ (150 бонусов). Получатели выбираются по одной и той же модели. Сохраните прибыль `calls_profit` (60 звонков самым рискованным) и `bonus_profit` (150 бонусов самым рискованным), а в `better` — `"звонки"` или `"бонусы"`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
y1 = d[r.nlargest(60).index]; cp = int(700 * y1.sum() - 500 * (60 - y1.sum()))
y2 = d[r.nlargest(150).index]; bp = int(400 * y2.sum() - 200 * (150 - y2.sum()))
assert need('calls_profit') == cp, f'calls_profit = {need("calls_profit")}, а нужно {cp}: 60 самых рискованных, +700 / −500.'
assert need('bonus_profit') == bp, f'bonus_profit = {need("bonus_profit")}, а нужно {bp}: 150 самых рискованных, +400 / −200.'
assert need('better') == ('звонки' if cp > bp else 'бонусы'), f'better = {need("better")!r}.'
```

### hint
Та же схема, что в задаче «Прибыль по бюджетам», с другими k, выгодой и ценой.

### hint
Звонки: `yc = y_test[risk.nlargest(60).index]`, прибыль `700 * yc.sum() - 500 * (60 - yc.sum())`. Бонусы — то же с 150, 400 и 200.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

yc = y_test[risk.nlargest(60).index]
calls_profit = int(700 * yc.sum() - 500 * (60 - yc.sum()))
yb = y_test[risk.nlargest(150).index]
bonus_profit = int(400 * yb.sum() - 200 * (150 - yb.sum()))
better = "звонки" if calls_profit > bonus_profit else "бонусы"
```

### explain
Звонки выигрывают: дорогой инструмент выгоден, когда его направляют точно, а в топ-60 модель почти не ошибается (95 % уходящих). Бонусы при 150 получателях уже задевают гостей со средним риском. На практике инструменты совмещают: звонок — самым рискованным, бонус — следующим в списке.

## task: rule-gains | Модель против давности при одном бюджете | star

Сравните модель и сортировку по давности визита (`days_since_last`, больше — рискованнее) при бюджетах 60, 100 и 150. Если у нескольких гостей одинаковая давность, берите тех, кто раньше в `X_test` — так работает `nlargest` по умолчанию. Сохраните DataFrame `cmp` со столбцами `k`, `model`, `days` (прибыль, +400 / −200) и в `gap_grows` — `True`, если разница «модель − давность» растёт с бюджетом (строго на каждом шаге).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, risk

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
r = _pd.Series(_RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1], index=b.index)
def _p(score, k):
    yy = d[score.nlargest(k).index]
    return int(400 * yy.sum() - 200 * (k - yy.sum()))
t = need('cmp', _pd.DataFrame)
assert list(t['k']) == [60, 100, 150], f'Столбец k: {list(t["k"])}.'
wm = [_p(r, k) for k in (60, 100, 150)]; wd = [_p(b['days_since_last'], k) for k in (60, 100, 150)]
assert [int(v) for v in t['model']] == wm, f'Прибыль модели: {list(t["model"])}, а нужно {wm}.'
assert [int(v) for v in t['days']] == wd, f'Прибыль сортировки по давности: {list(t["days"])}, а нужно {wd}.'
gp = [m - x for m, x in zip(wm, wd)]
assert need('gap_grows') == (gp[0] < gp[1] < gp[2]), f'gap_grows = {need("gap_grows")}; разницы по бюджетам: {gp}.'
```

### hint
Напишите функцию `profit_top(score, k)`, которая принимает Series оценок с индексом гостей. Для давности оценка — сам столбец `X_test["days_since_last"]`.

### hint
Функция `profit_top(score, k)`: `yy = y_test[score.nlargest(k).index]`, а прибыль — `400 * yy.sum() - 200 * (k - yy.sum())`. Одна функция работает и для риска модели, и для давности — обе передаются как Series с индексом гостей. Для `gap_grows` посчитайте разницу по строкам и проверьте, что каждое следующее значение строго больше предыдущего: `is_monotonic_increasing` допускает равенство, поэтому дополнительно нужен `is_unique`. Проще и тоже верно: `(gap.diff().dropna() > 0).all()` — каждая следующая разница больше предыдущей.

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
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

def profit_top(score, k):
    yy = y_test[score.nlargest(k).index]
    return int(400 * yy.sum() - 200 * (k - yy.sum()))

rows = [{"k": k, "model": profit_top(risk, k), "days": profit_top(X_test["days_since_last"], k)} for k in (60, 100, 150)]
cmp = pd.DataFrame(rows)
gap = cmp["model"] - cmp["days"]
gap_grows = bool(gap.is_monotonic_increasing and gap.is_unique)
```

### explain
Разница растёт: при маленьком бюджете оба способа находят очевидных — тех, кто давно не приходил. Дальше давность перестаёт различать гостей, а модель продолжает находить уходящих среди недавних посетителей: новичков и тех, кто жаловался на доставку.
