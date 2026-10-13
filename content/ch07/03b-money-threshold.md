---
title: "Порог по деньгам"
lead: "Точность и полнота — промежуточные цифры, бизнесу важнее деньги. Считаем прибыль акции удержания для каждого порога, находим лучший, укладываемся в бюджет на бонусы — и выбираем порог честно, не подглядывая в тест."
files: [guests_churn.csv]
recap:
  - "Порог по деньгам: прибыль = TP × выгода − (TP + FP) × стоимость акции; считаем для сетки порогов и берём лучший."
  - "Порог подбирают на обучающей части (или отдельной валидации), а не на тесте — иначе тест перестаёт быть честным."
---

Модель — лес из урока «Порог, PR- и ROC-кривые»: он выдаёт вероятность ухода каждого гостя, а мы решаем, с какой вероятности давать бонус.

## Порог по деньгам

Точность и полнота — промежуточные цифры. Бизнесу важнее деньги. Допустим:

- бонус стоит «Зерну» **200 ₽** — его получат и уходящие, и оставшиеся гости;
- бонус, отправленный уходящему гостю, в среднем приносит **1000 ₽** выручки, которую мы иначе потеряли бы (уже с учётом того, что срабатывает он не всегда).

Тогда для порога t прибыль акции = TP × 1000 − (TP + FP) × 200: выгода от пойманных уходящих минус стоимость всех бонусов. Это та же схема, что в уроке «Матрица ошибок»: бонус платим всем, кому отправили. Там мы считали потери от пропущенных (FN), здесь — выгоду от пойманных (TP); это одно и то же, потому что TP + FN — все уходящие, и их число от порога не зависит. Посчитаем её для сетки порогов и нарисуем **кривую прибыли**:

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
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

COST, GAIN = 200, 1000
rows = []
for t in np.arange(0.05, 1, 0.05).round(2):
    bonus = p >= t
    tp = int((y_test[bonus] == 1).sum())
    rows.append({"threshold": float(t), "bonuses": int(bonus.sum()), "profit": tp * GAIN - int(bonus.sum()) * COST})
profit = pd.DataFrame(rows)
print(profit.sort_values("profit").tail(3))
print("бонус всем:", int(y_test.sum()) * GAIN - len(y_test) * COST)

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(profit["threshold"], profit["profit"], marker="o")
ax.set_xlabel("порог")
ax.set_ylabel("прибыль на тесте, ₽")
ax.set_title("Кривая прибыли")
```

**Что здесь происходит:**

- `np.arange(0.05, 1, 0.05).round(2)` — сетка порогов; `.round(2)` убирает хвосты вроде 0.30000000000000004.
- `y_test[bonus] == 1` — среди получивших бонус находим ушедших: это TP.
- Прибыль: выгода с каждого TP минус стоимость **всех** бонусов, и TP, и FP.
- «Бонус всем» — точка отсчёта: модель полезна, если зарабатывает больше неё.

Лучший порог здесь около 0.25: прибыль около 79 тыс. ₽ на 600 тестовых гостях против примерно 68 тыс. при пороге 0.5. Бонус всем подряд почти не окупается — 14 тыс. ₽. Модель с правильным порогом зарабатывает в пять с лишним раз больше.

Почему оптимум так низко? Бонус выгодно дать гостю, если ожидаемая выгода больше стоимости: p × 1000 > 200, то есть p > 0.2. Когда бонус дешёвый, а уход дорогой, порог должен быть низким — даже ценой точности. Это правило работает, только если вероятностям можно верить как числам — то есть модель **откалибрована**: среди гостей с p ≈ 0.3 уходит действительно около 30 %. Как это проверить — урок «Что делать с вероятностями: ранжирование и калибровка» главы 6.

::: figure profit-ev
Ожидаемый результат одного бонуса при вероятности ухода p: выгода p × 1000 минус стоимость 200 ₽. Прямая пересекает ноль в p = 0.2 — правее бонус в среднем окупается.
:::

::: warn Порог тоже подгоняется
Мы выбрали порог, глядя на тестовые данные, — это подглядывание из урока «Честное сравнение моделей» главы 6. Для отчёта порог выбирают на обучающей части (отдельная валидация или кросс-валидация), а на тесте один раз проверяют, сколько денег он принёс. Этим займёмся в задаче со звёздочкой.
:::

{{practice: profit, budget, honest-t}}

## Практика

## task: profit | Прибыль при дорогом бонусе | base

Бонус подорожал: теперь он стоит **300 ₽**, а выгода от бонуса уходящему гостю — **900 ₽**. Для порогов `[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]` посчитайте прибыль на тесте: TP × 900 − (число бонусов) × 300, бонус — при p ≥ порога. Сохраните `profits` — **список** прибылей (целые числа) в порядке порогов, `best_t` — порог с наибольшей прибылью и `best_profit` — эту прибыль.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]
thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_ts = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
_w = [int((_d[_p >= t] == 1).sum()) * 900 - int((_p >= t).sum()) * 300 for t in _ts]
_got = need('profits')
assert len(_got) == len(_ts), f'В profits {len(_got)} значений, а порогов {len(_ts)}.'
_got = [int(v) for v in _got]
assert _got == _w, f'profits = {_got}, а ожидалось {_w}. TP — ушедшие среди получивших бонус; стоимость — за все бонусы, а не только за TP.'
_i = _w.index(max(_w))
assert close(need('best_t'), _ts[_i]), f'best_t = {need("best_t")}, а ожидался порог с наибольшей прибылью.'
assert int(need('best_profit')) == _w[_i], f'best_profit = {need("best_profit")}, а ожидалось {_w[_i]}.'
```

### hint
Для одного порога: `bonus = p >= t`, `tp = int((y_test[bonus] == 1).sum())`, прибыль `tp * 900 - int(bonus.sum()) * 300`.

### hint
Индекс максимума списка: `profits.index(max(profits))`, по нему берите порог из `thresholds`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]
thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

profits = []
for t in thresholds:
    bonus = p >= t
    tp = int((y_test[bonus] == 1).sum())
    profits.append(tp * 900 - int(bonus.sum()) * 300)
i = profits.index(max(profits))
best_t = thresholds[i]
best_profit = profits[i]
```

### explain
Порог безубыточности теперь 300 / 900 ≈ 0.33: бонус выгоден гостю с вероятностью ухода выше трети. Лучший порог сдвинулся вверх по сравнению с примером в теории — дорогой бонус требует большей уверенности.

## task: budget | Бюджет на 100 бонусов | plus

Бюджета хватает примерно на 100 бонусов на тестовую группу. Возьмите в качестве порога `t100` вероятность 100-го по риску гостя (отсортируйте `p` по убыванию). Бонус получают все с `p >= t100` — из-за одинаковых вероятностей их может оказаться чуть больше 100. Сохраните `t100` (3 знака), `n_bonus` — сколько бонусов раздадут, `prec` и `rec` — точность и полноту при этом пороге (3 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_score as _ps, recall_score as _rs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_t = _np.sort(_p)[::-1][99]
_s = _p >= _t
assert close(need('t100'), round(float(_t), 3)), f't100 = {need("t100")}, а ожидалось {round(float(_t), 3)}. Сортируйте по убыванию и берите элемент с индексом 99 — это сотый гость.'
assert int(need('n_bonus')) == int(_s.sum()), f'n_bonus = {need("n_bonus")}, а ожидалось {int(_s.sum())}: все гости с p ≥ t100.'
assert close(need('prec'), round(_ps(_d, _s), 3)), f'prec = {need("prec")}, а ожидалось {round(_ps(_d, _s), 3)}.'
assert close(need('rec'), round(_rs(_d, _s), 3)), f'rec = {need("rec")}, а ожидалось {round(_rs(_d, _s), 3)}.'
```

### hint
`np.sort(p)` сортирует по возрастанию; `[::-1]` разворачивает массив. Сотый элемент — индекс 99.

### hint
Дальше как обычно: `bonus = p >= t100`, `int(bonus.sum())`, `precision_score(y_test, bonus)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

t_raw = np.sort(p)[::-1][99]
bonus = p >= t_raw
t100 = round(float(t_raw), 3)
n_bonus = int(bonus.sum())
prec = round(precision_score(y_test, bonus), 3)
rec = round(recall_score(y_test, bonus), 3)
```

### explain
Когда ограничен бюджет, порог задаёт не бизнес-правило, а число бонусов: «топ-N по риску», как в главе 6. Порог получается выше 0.5, и примерно восемь бонусов из десяти попадают по адресу, но поймано лишь около 60 % уходящих — денег на остальных нет.

## task: honest-t | Честный выбор порога | star

В теории мы выбрали порог по прибыли прямо на тесте — это подглядывание. Сделайте честно:

1. Разделите `X_train, y_train` ещё раз: `train_test_split(X_train, y_train, test_size=0.25, random_state=0, stratify=y_train)` → `X_fit, X_val, y_fit, y_val`.
2. Обучите `RandomForestClassifier(n_estimators=100, random_state=0)` на `X_fit`.
3. На `X_val` посчитайте прибыль (бонус 200 ₽, выгода 1000 ₽) для порогов `np.arange(0.05, 1, 0.05).round(2)` и выберите лучший — `t_val` (если лучших несколько, берите первый).
4. Той же моделью оцените тест: `profit_test` — прибыль на тесте при пороге `t_val`, `profit_05` — при пороге 0.5 (целые числа).

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

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_af, _av, _cf, _cv = _tts(_a, _c, test_size=0.25, random_state=0, stratify=_c)
_m = _RF(n_estimators=100, random_state=0).fit(_af, _cf)
_pv, _pt = _m.predict_proba(_av)[:, 1], _m.predict_proba(_b)[:, 1]
def _pr(yy, pp, t):
    s = pp >= t
    return int((yy[s] == 1).sum()) * 1000 - int(s.sum()) * 200
_grid = _np.arange(0.05, 1, 0.05).round(2)
_vals = [_pr(_cv, _pv, t) for t in _grid]
_tv = float(_grid[int(_np.argmax(_vals))])
assert close(need('t_val'), _tv), f't_val = {need("t_val")}, а ожидался другой порог. Выбирайте по прибыли на X_val (не на тесте!), модель обучайте только на X_fit.'
assert int(need('profit_test')) == _pr(_d, _pt, _tv), f'profit_test = {need("profit_test")}, а ожидалось {_pr(_d, _pt, _tv)}. Прибыль на тесте при пороге t_val той же моделью.'
assert int(need('profit_05')) == _pr(_d, _pt, 0.5), f'profit_05 = {need("profit_05")}, а ожидалось {_pr(_d, _pt, 0.5)}.'
```

### hint
Функция прибыли пригодится дважды: `def profit(y_true, p, t):` → `bonus = p >= t`, `tp = int((y_true[bonus] == 1).sum())`, `return tp * 1000 - int(bonus.sum()) * 200`.

### hint
Список прибылей по сетке на валидации, затем `grid[int(np.argmax(vals))]` — `argmax` возвращает первый максимум.

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

X_fit, X_val, y_fit, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=0, stratify=y_train)
model = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_fit, y_fit)
p_val = model.predict_proba(X_val)[:, 1]
p_test = model.predict_proba(X_test)[:, 1]

def profit(y_true, p, t):
    bonus = p >= t
    tp = int((y_true[bonus] == 1).sum())
    return tp * 1000 - int(bonus.sum()) * 200

grid = np.arange(0.05, 1, 0.05).round(2)
vals = [profit(y_val, p_val, t) for t in grid]
t_val = float(grid[int(np.argmax(vals))])
profit_test = profit(y_test, p_test, t_val)
profit_05 = profit(y_test, p_test, 0.5)
```

### explain
Порог, найденный на валидации, — это честная оценка того, что будет «в бою»: тест его не видел. Он снова получается заметно ниже 0.5 и на тесте приносит больше денег, чем порог по умолчанию. Дальше в этой главе вы увидите, как подбирать настройки модели кросс-валидацией — порог выбирают по тому же принципу.
