---
title: "Проект: новое обещание доставки"
lead: "Финал главы. В главе 4 мы выяснили, что пешим курьерам обещают нереальные 30 минут. Бизнес провёл эксперимент: половине гостей в пешей зоне стали обещать 40 минут. Помогло ли это — и не испортило ли продажи? Анализируем A/B-тест целиком: от проверки дизайна до решения."
files: [ab_promise.csv]
recap:
  - "Анализ эксперимента начинают с проверки дизайна: SRM и то, что изменение действует ровно там, где задумано."
  - "Главная метрика отвечает на вопрос «сработало ли», защитные — «чем заплатили»."
  - "Каждую разницу сопровождают интервалом и p-value; незначимое ≠ нулевое."
  - "Сегменты, заданные заранее, — часть дизайна; найденные после теста — повод для нового теста."
  - "Решение — правило, записанное до анализа, плюс честный рассказ о неопределённости."
---

## Задача

> После разбора опозданий мы с 1 по 21 декабря провели эксперимент. Гостей случайно делили пополам. В группе B тем, кто заказывает в пределах 2 км (пешая зона), приложение обещало доставку за 40 минут вместо 30. Дальние зоны не меняли. Нужен вывод: внедрять новое обещание или нет.

Данные — `ab_promise.csv`: каждая строка — сессия в приложении доставки.

Столбцы: `session_id`, `ts` — время сессии, `group` — A или B, `city`, `distance_km`, `promise_min` — какое обещание увидел гость, `ordered` — сделал ли заказ (1/0). Для заказов: `courier`, `amount` — сумма (у сессий без заказа — 0), `actual_min`, `late` — опоздал ли (1/0), `rating` — оценка, если поставлена.

## План

1. Проверить, что эксперимент устроен как задумано.
2. Главная метрика: доля опозданий.
3. Конверсия — в целом и в пешей зоне: откуда могут уйти деньги.
4. Оценки гостей.
5. Защитная метрика правила: выручка на сессию.
6. Устойчивость: эффект по городам с поправкой.
7. График для руководителя.
8. Отчёт и решение одной функцией.

Правило решения зафиксировано заранее: **внедрять**, если опоздания значимо снизились, а выручка на сессию значимо не упала.

Почему защитная метрика в правиле — выручка, а не конверсия: более долгое обещание может отпугнуть часть заказов, но и вернуть гостей, которых раньше злили опоздания. Конверсия показывает только первую половину этой истории, выручка на сессию — итог обеих. Поэтому конверсию мы тоже посчитаем (шаг 3) — она подскажет, откуда могут уйти деньги, — но решение по правилу принимает выручка.

::: quiz
Другой тест, то же правило: внедрять, если главная метрика значимо улучшилась, а выручка на сессию значимо не упала. Итоги: опоздания −10 п.п. (p < 0.001), конверсия в зоне изменения −5 п.п. (p = 0.02), выручка на сессию −8 ₽ (p = 0.30, интервал от −23 до +7 ₽). Какое решение?

- [x] По правилу — внедрять, но в отчёте честно показать падение конверсии и широкий интервал по деньгам и предложить следить за выручкой
  > Правило зафиксировано до теста, и выручка значимо не упала. Падение конверсии — важная оговорка, а интервал до −23 ₽ — повод следить за деньгами после запуска или продлить тест.
- [ ] Не внедрять: конверсия значимо упала
  > Конверсия в этом правиле — не защитная метрика. Поменять правило, увидев результат, — та же подгонка, что и односторонний тест задним числом.
- [ ] Внедрять без оговорок: правило выполнено
  > Решение — да, но без оговорок отчёт скроет и потерю заказов, и то, что падение выручки до 23 ₽ тест не исключил.
- [ ] Перезапускать тест, пока конверсия не перестанет падать
  > Повтор до нужного результата — ловушка множественных попыток.
:::

## Разберём вместе: главная метрика на салфетке

Прежде чем писать код, прикинем главное число руками. Заказов в A — 1 365, из них опоздали 362; в B — 1 301 и 175.

1. Доли опозданий: A — 362 / 1365 ≈ **26.5 %**, B — 175 / 1301 ≈ **13.5 %**. Разница **−13.1 п.п.**
2. SE разницы: √(0.265 × 0.735 / 1365 + 0.135 × 0.865 / 1301) ≈ √(0.000143 + 0.000090) ≈ **0.0153**, то есть 1.5 п.п.
3. Интервал: −13.1 ± 1.96 × 1.5 → примерно **от −16.1 до −10.1 п.п.**
4. Разница почти в 9 стандартных ошибок — p астрономически мало.

Что получилось: первая половина правила («опоздания значимо снизились») выполнена с огромным запасом. Но решение ещё не принято: правило требует проверить и деньги — более долгое обещание могло отпугнуть заказы. Ради этого и нужны шаги 3–5.

::: warn Типичные ошибки проекта
- **Опоздания по сессиям.** Доля опозданий считается среди **заказов** (`orders`), а не среди всех сессий — у сессий без заказа опоздания нет.
- **Конверсия только в целом.** Эффект обещания касается пешей зоны; в целом он «разбавлен» дальними заказами.
- **Правило решения после результатов.** Оно зафиксировано заранее — им и пользуемся, даже если результат хочется трактовать иначе.
- **Города без поправки.** Четыре города — четыре проверки; Холм обязателен.
:::

Начиная со второго шага, перед задачей курс сам загружает `ab` (вся выгрузка) и `orders` (только сессии с заказом).

::: figure promise-denoms
Три уровня данных проекта и знаменатель каждой метрики: конверсию и выручку считают на сессию, долю опозданий — на заказ.
:::

## Практика

## task: design | Шаг 1. Проверка эксперимента | base

Загрузите `ab_promise.csv` (`ts` — датой) в `ab`. Проверьте, что эксперимент устроен как задумано:

- `srm_p` — p-value проверки SRM по числу сессий в группах;
- `promise_ok` — `True`, если в зоне до 2 км **все** сессии группы A видели обещание 30 минут, а группы B — 40 минут;
- `far_same` — `True`, если в зоне от 2 км набор обещаний у групп одинаковый (множества значений `promise_min` совпадают).

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
```

### starter
```python
import pandas as pd
from scipy import stats
```

### check
```python
import pandas as _pd
from scipy import stats as _st
a = _ref_ab()
x = need('ab', _pd.DataFrame)
assert len(x) == len(a) and _pd.api.types.is_datetime64_any_dtype(x['ts']), 'ab — вся выгрузка, ts — датой (parse_dates).'
assert close(need('srm_p'), _st.chisquare(a['group'].value_counts()).pvalue, 6e-5), f'srm_p = {need("srm_p")}.'
s = a[a['distance_km'] < 2]
ok = bool((s.loc[s['group'] == 'A', 'promise_min'] == 30).all() and (s.loc[s['group'] == 'B', 'promise_min'] == 40).all())
assert need('promise_ok') == ok, f'promise_ok должно быть {ok}.'
f = a[a['distance_km'] >= 2]
same = set(f.loc[f['group'] == 'A', 'promise_min']) == set(f.loc[f['group'] == 'B', 'promise_min'])
assert need('far_same') == same, f'far_same должно быть {same}.'
```

### hint
Урок «A/B-тест: от дизайна до решения»: `stats.chisquare(ab["group"].value_counts()).pvalue`.

### hint
Проверка «все равны 30»: `(short.loc[short["group"] == "A", "promise_min"] == 30).all()`.

### solution
```python
import pandas as pd
from scipy import stats
ab = pd.read_csv("ab_promise.csv", parse_dates=["ts"])
srm_p = stats.chisquare(ab["group"].value_counts()).pvalue
short = ab[ab["distance_km"] < 2]
promise_ok = bool((short.loc[short["group"] == "A", "promise_min"] == 30).all()
                  and (short.loc[short["group"] == "B", "promise_min"] == 40).all())
far = ab[ab["distance_km"] >= 2]
far_same = set(far.loc[far["group"] == "A", "promise_min"]) == set(far.loc[far["group"] == "B", "promise_min"])
```

### explain
Прежде чем считать эффект, убеждаемся, что тест вообще проверял то, что задумано: группы сбалансированы, изменение действует только там, где должно. Ошибка в настройке эксперимента обесценивает любой анализ.

## task: late | Шаг 2. Главная метрика: опоздания | base

Главная метрика — доля опозданий среди **заказов** (`ordered == 1`). Сохраните `late_a`, `late_b` (доли, 4 знака), `diff_pp` (B − A в п.п., 1 знак), `ci` — кортеж (нижняя, верхняя граница 95 % ДИ разницы в п.п., 1 знак) и `p_late` — p-value z-теста (без округления: оно меньше 0.0001).

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
ab = _ref_ab()
orders = ab[ab["ordered"] == 1]
```

### starter
```python
import numpy as np
from statsmodels.stats.proportion import proportions_ztest
# ab — вся выгрузка, orders — только сессии с заказом
```

### check
```python
la, lb, d, lo, hi, p = _ref_share(_ref_ab().query('ordered == 1'), 'late')
assert close(need('late_a'), round(la, 4)) and close(need('late_b'), round(lb, 4)), f'late_a, late_b = {need("late_a")}, {need("late_b")}.'
assert close(need('diff_pp'), round(d * 100, 1)), f'diff_pp = {need("diff_pp")}.'
c = tuple(need('ci'))
assert len(c) == 2 and close(c[0], round(lo * 100, 1)) and close(c[1], round(hi * 100, 1)), f'ci = {c}, а нужно {(round(lo * 100, 1), round(hi * 100, 1))}.'
assert close(need('p_late'), p, 6e-5), f'p_late = {need("p_late")}.'
```

### hint
Уроки «Доверительные интервалы» и «A/B-тест: от дизайна до решения»: доли групп, SE разницы, интервал ±1.96·SE, `proportions_ztest`.

### hint
`late` в данных — 1.0/0.0 (у сессий без заказа — пусто), поэтому сумма и среднее считаются как обычно.

### solution
```python
import numpy as np
from statsmodels.stats.proportion import proportions_ztest
g = orders.groupby("group")["late"].agg(["sum", "size", "mean"])
a, b = g.loc["A"], g.loc["B"]
late_a, late_b = round(a["mean"], 4), round(b["mean"], 4)
d = b["mean"] - a["mean"]
se = np.sqrt(a["mean"] * (1 - a["mean"]) / a["size"] + b["mean"] * (1 - b["mean"]) / b["size"])
diff_pp = round(d * 100, 1)
ci = (round((d - 1.96 * se) * 100, 1), round((d + 1.96 * se) * 100, 1))
z, p_late = proportions_ztest([b["sum"], a["sum"]], [b["size"], a["size"]])
g
```

### explain
Опозданий стало вдвое меньше, и интервал далеко от нуля. Главная цель эксперимента достигнута. Теперь важно проверить, чем за это заплатили.

## task: conversion | Шаг 3. Конверсия: откуда могут уйти деньги | base

Более долгое обещание может отпугнуть гостей. Сравните конверсию сессий в заказ (`ordered`): в целом, в зоне до 2 км и в зоне от 2 км. Сохраните p-values z-тестов `p_all`, `p_short`, `p_far` и разницы B − A в п.п. (2 знака): `d_all`, `d_short`, `d_far`.

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
ab = _ref_ab()
orders = ab[ab["ordered"] == 1]
```

### starter
```python
import numpy as np
from statsmodels.stats.proportion import proportions_ztest
```

### check
```python
a = _ref_ab()
for nm, x in (('all', a), ('short', a[a['distance_km'] < 2]), ('far', a[a['distance_km'] >= 2])):
    _, _, d, _, _, p = _ref_share(x, 'ordered')
    assert close(need('p_' + nm), p, 6e-5), f'p_{nm} = {need("p_" + nm)}, а нужно около {p:.6f}.'
    assert close(need('d_' + nm), round(d * 100, 2)), f'd_{nm} = {need("d_" + nm)}, а нужно {round(d * 100, 2)}.'
```

### hint
Удобно написать маленькую функцию `test(x)`, которая возвращает разницу и p для таблицы `x`, и вызвать её трижды.

### hint
Зоны: `short = ab[ab["distance_km"] < 2]`, `far = ab[ab["distance_km"] >= 2]`. Внутри `test`: сводка `x.groupby("group")["ordered"].agg(["sum", "size", "mean"])` и `proportions_ztest`.

### solution
```python
import numpy as np
from statsmodels.stats.proportion import proportions_ztest

def test(x):
    g = x.groupby("group")["ordered"].agg(["sum", "size", "mean"])
    z, p = proportions_ztest([g.loc["B", "sum"], g.loc["A", "sum"]], [g.loc["B", "size"], g.loc["A", "size"]])
    return round((g.loc["B", "mean"] - g.loc["A", "mean"]) * 100, 2), p

d_all, p_all = test(ab)
d_short, p_short = test(ab[ab["distance_km"] < 2])
d_far, p_far = test(ab[ab["distance_km"] >= 2])
```

### explain
В целом падение конверсии на грани значимости, а в зоне до 2 км — значимо: гости, увидевшие «40 минут» вместо «30», чуть реже заказывают. В дальней зоне, где обещание не менялось, разницы нет — это подтверждает, что эффект вызван именно новым обещанием, а не чем-то ещё. Обратите внимание: сегмент «до 2 км» был задуман заранее (в нём и было изменение), поэтому поправка на множественность здесь не нужна.

## task: ratings | Шаг 4. Оценки гостей | base

Сравните оценки доставки (среди заказов с оценкой) в группах: средние `rating_a`, `rating_b` (2 знака), доли «не пятёрок» `low_a`, `low_b` (оценка ≤ 4, 3 знака) и `p_rating` — p-value теста Манна — Уитни.

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
ab = _ref_ab()
orders = ab[ab["ordered"] == 1]
```

### starter
```python
import pandas as pd
from scipy import stats
```

### check
```python
o = _ref_ab().query('ordered == 1').dropna(subset=['rating'])
m = o.groupby('group')['rating'].mean()
low = o.assign(l=o['rating'] <= 4).groupby('group')['l'].mean()
assert close(need('rating_a'), round(m['A'], 2)) and close(need('rating_b'), round(m['B'], 2)), 'Средние оценки не совпадают.'
assert close(need('low_a'), round(low['A'], 3)) and close(need('low_b'), round(low['B'], 3)), 'Доли «не пятёрок» не совпадают.'
p = _st0.mannwhitneyu(o.loc[o['group'] == 'B', 'rating'], o.loc[o['group'] == 'A', 'rating']).pvalue
assert close(need('p_rating'), p, 6e-5), f'p_rating = {need("p_rating")}, а нужно около {p:.6f}.'
```

### hint
Урок «Статистические тесты: какой выбрать»: оценки порядковые — Манна — Уитни. Сначала `r = orders.dropna(subset=["rating"])`.

### hint
«Не пятёрка» — флаг `r["rating"] <= 4`, его среднее по группе — доля. Тест — `stats.mannwhitneyu(r.loc[r["group"] == "B", "rating"], r.loc[r["group"] == "A", "rating"]).pvalue`.

### solution
```python
import pandas as pd
from scipy import stats
r = orders.dropna(subset=["rating"])
m = r.groupby("group")["rating"].mean()
rating_a, rating_b = round(m["A"], 2), round(m["B"], 2)
low = (r["rating"] <= 4).groupby(r["group"]).mean()
low_a, low_b = round(low["A"], 3), round(low["B"], 3)
p_rating = stats.mannwhitneyu(r.loc[r["group"] == "B", "rating"], r.loc[r["group"] == "A", "rating"]).pvalue
```

### explain
Средняя оценка выросла с 4.46 до 4.64, доля «не пятёрок» упала с 36 % до 27 %, p ≈ 0.00007. Гости ценят не обещание «30 минут», а то, что обещание выполнено: честные 40 минут лучше сорванных 30.

## task: money | Шаг 5. Деньги на сессию | plus

Выручка на сессию (`amount`, у сессий без заказа — 0) — итог «меньше опозданий» против «меньше заказов». Сохраните `rev_a`, `rev_b` (1 знак), `p_rev` — p-value t-теста Уэлча и 95 %-й бутстрэп-интервал разницы B − A: `rev_lo`, `rev_hi` (3 000 перевыборок, `rng = np.random.default_rng(0)`).

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
ab = _ref_ab()
orders = ab[ab["ordered"] == 1]
```

### starter
```python
import numpy as np
from scipy import stats
rng = np.random.default_rng(0)
```

### check
```python
a = _ref_ab()
A = a.loc[a['group'] == 'A', 'amount']
B = a.loc[a['group'] == 'B', 'amount']
assert close(need('rev_a'), round(A.mean(), 1)) and close(need('rev_b'), round(B.mean(), 1)), f'rev_a, rev_b = {need("rev_a")}, {need("rev_b")}.'
assert close(need('p_rev'), _st0.ttest_ind(B, A, equal_var=False).pvalue, 6e-5), f'p_rev = {need("p_rev")}.'
lo, hi = need('rev_lo'), need('rev_hi')
assert -35 < lo < -20 and -2 < hi < 6 and lo < B.mean() - A.mean() < hi, f'Интервал {lo:.1f}…{hi:.1f} не похож на ожидаемый (примерно −28…+2).'
```

### hint
Урок «A/B-тест: от дизайна до решения», задача «Бутстрэп выручки».

### hint
Выручка — по **всем** сессиям `ab` (нули тоже): `a = ab.loc[ab["group"] == "A", "amount"].to_numpy()`, так же `b`. t-тест — `stats.ttest_ind(b, a, equal_var=False)`.

### solution
```python
import numpy as np
from scipy import stats
rng = np.random.default_rng(0)
A = ab.loc[ab["group"] == "A", "amount"].to_numpy()
B = ab.loc[ab["group"] == "B", "amount"].to_numpy()
rev_a, rev_b = round(A.mean(), 1), round(B.mean(), 1)
p_rev = stats.ttest_ind(B, A, equal_var=False).pvalue
boot = [rng.choice(B, len(B)).mean() - rng.choice(A, len(A)).mean() for _ in range(3000)]
rev_lo, rev_hi = np.percentile(boot, [2.5, 97.5])
```

### explain
Выручка на сессию в B ниже примерно на 13 ₽, но интервал захватывает ноль: падение может быть и нулевым, и заметным (до 25–30 ₽). Тест не даёт уверенного ответа про деньги — это важно честно сказать в отчёте. Что делать дальше, тоже можно посчитать: чтобы интервал разницы сузился до ±10 ₽, нужно SE разницы ≈ 10 / 1.96 ≈ 5.1 ₽. При σ около 350 ₽ в каждой группе это (350² + 350²) / 5.1² ≈ 9 400 сессий на группу — в 2.4 раза больше, чем сейчас, то есть около семи недель теста вместо трёх (правило √n из урока «Выборки и центральная предельная теорема»).

## task: cities | Шаг 6. Эффект по городам | plus

Проверьте, снижаются ли опоздания во всех городах. Для каждого города посчитайте долю опозданий среди заказов в A и B, разницу в п.п. и p-value z-теста. Соберите таблицу `by_city` со столбцами `late_a`, `late_b`, `diff_pp`, `p`, `p_holm` (p после поправки Холма). В `all_cities` — `True`, если после поправки эффект значим во всех городах. Доли и разницу округлять не обязательно — проверка примет и округлённые (доли — до 3 знаков, разницу — до 1), и точные значения; `p` и `p_holm` оставьте без округления.

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
ab = _ref_ab()
orders = ab[ab["ordered"] == 1]
```

### starter
```python
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests
```

### check
```python
from statsmodels.stats.multitest import multipletests as _m
o = _ref_ab().query('ordered == 1')
rows = {}
for c, x in o.groupby('city'):
    la, lb, d, _, _, p = _ref_share(x, 'late')
    rows[c] = (la, lb, d * 100, p)
ph = _m([v[3] for v in rows.values()], method='holm')[1]
t = need('by_city', _pd0.DataFrame)
if 'city' in t.columns:
    t = t.set_index('city')
assert list(t.columns) == ['late_a', 'late_b', 'diff_pp', 'p', 'p_holm'], f'Столбцы: {list(t.columns)}.'
for (c, v), h in zip(rows.items(), ph):
    assert close(t.loc[c, 'late_a'], v[0], 1e-3) and close(t.loc[c, 'late_b'], v[1], 1e-3), f'{c}: доли не совпадают.'
    assert close(t.loc[c, 'diff_pp'], v[2], 0.06), f'{c}: diff_pp не совпадает.'
    assert close(t.loc[c, 'p_holm'], h, 1e-6), f'{c}: p_holm не совпадает.'
assert need('all_cities') == bool((ph < 0.05).all())
```

### hint
Урок «Ловушки статистики», задача «Города после теста» — тот же цикл, только метрика `late` и данные `orders`.

### hint
Поправка — `multipletests(by_city["p"], method="holm")[1]` во второй столбец; `all_cities = bool((by_city["p_holm"] < 0.05).all())`.

### solution
```python
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests
rows = []
for city, x in orders.groupby("city"):
    g = x.groupby("group")["late"].agg(["sum", "size", "mean"])
    z, p = proportions_ztest([g.loc["B", "sum"], g.loc["A", "sum"]], [g.loc["B", "size"], g.loc["A", "size"]])
    rows.append({"city": city, "late_a": g.loc["A", "mean"], "late_b": g.loc["B", "mean"],
                 "diff_pp": (g.loc["B", "mean"] - g.loc["A", "mean"]) * 100, "p": p})
by_city = pd.DataFrame(rows).set_index("city")
by_city["p_holm"] = multipletests(by_city["p"], method="holm")[1]
all_cities = bool((by_city["p_holm"] < 0.05).all())
by_city.round(4)
```

### explain
Здесь сегменты подтверждают общий вывод, а не ищут неожиданный: эффект большой, и его хватает, чтобы быть значимым даже в маленьких городах после поправки. Так выглядит устойчивый результат.

## task: chart | Шаг 7. График для руководителя | plus

Нарисуйте два графика рядом: слева — доля опозданий в группах A и B (столбцы, %), справа — конверсия в зоне до 2 км (столбцы, %). На каждом столбце — подпись значения с 1 знаком и «усы» 95 %-го интервала Уилсона (`yerr` в `ax.bar`). Заголовки — выводы (любой непустой текст).

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
ab = _ref_ab()
orders = ab[ab["ordered"] == 1]
```

### starter
```python
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
```

### check
```python
o = _ref_ab().query('ordered == 1')
s = _ref_ab().query('distance_km < 2')
w1 = (o.groupby('group')['late'].mean() * 100).values
w2 = (s.groupby('group')['ordered'].mean() * 100).values
assert len(figs) == 1 and len(figs[0].axes) == 2, 'Два графика рядом: plt.subplots(1, 2).'
a1, a2 = figs[0].axes
for ax, w, nm in ((a1, w1, 'опозданий'), (a2, w2, 'конверсии')):
    h = [p.get_height() for p in ax.patches]
    assert len(h) == 2 and all(close(x, y, 1e-6) for x, y in zip(h, w)), f'Столбцы {nm}: {h}, а нужно {list(w.round(2))} (в процентах, A и B).'
    assert len(ax.texts) == 2, f'Подпишите значения на графике {nm}: ax.bar_label(bars, fmt="%.1f").'
    assert ax.get_title().strip(), 'Добавьте заголовок-вывод.'
    assert ax.lines or ax.collections, f'На графике {nm} нет «усов» интервала: передайте yerr.'
```

### hint
Усы на столбцах рисуют так же, как в задаче «Интервалы на графике» урока «Доверительные интервалы»: `yerr` — расстояния от вершины вниз и вверх. Для каждого графика: `g = x.groupby("group")[col].agg(["sum", "size", "mean"])`, `lo, hi = proportion_confint(g["sum"], g["size"], method="wilson")`.

### hint
`bars = ax.bar(g.index, g["mean"] * 100, yerr=[(g["mean"] - lo) * 100, (hi - g["mean"]) * 100], capsize=6)`, затем `ax.bar_label(bars, fmt="%.1f")`.

### solution
```python
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

def panel(ax, x, col, title):
    g = x.groupby("group")[col].agg(["sum", "size", "mean"])
    lo, hi = proportion_confint(g["sum"], g["size"], method="wilson")
    bars = ax.bar(g.index, g["mean"] * 100, yerr=[(g["mean"] - lo) * 100, (hi - g["mean"]) * 100],
                  capsize=6, color=["lightgray", "tab:blue"])
    ax.bar_label(bars, fmt="%.1f", padding=8)
    ax.set_ylabel("%")
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
panel(axes[0], orders, "late", "Опозданий вдвое меньше")
panel(axes[1], ab[ab["distance_km"] < 2], "ordered", "До 2 км заказывают чуть реже")
fig.tight_layout()
```

### explain
Два столбца рядом с «усами» читаются за секунду: опозданий вдвое меньше, а конверсия в пешей зоне просела на несколько пунктов — и по «усам» видно, насколько эта просадка надёжна. Подписи значений избавляют руководителя от необходимости угадывать по оси, а «усы» сразу показывают, где разница больше шума. Заголовок-вывод («Опозданий вдвое меньше») важнее заголовка-описания («Доля опозданий по группам»).

## task: decision | Шаг 8. Отчёт и решение | star

Напишите `promise_report(ab)`: принимает выгрузку эксперимента и возвращает словарь:

- `"srm_ok"` — p SRM не меньше 0.01;
- `"late_diff_pp"` и `"late_p"` — изменение доли опозданий среди заказов (B − A, п.п., 1 знак) и p-value;
- `"conv_short_diff_pp"` и `"conv_short_p"` — изменение конверсии в зоне до 2 км (п.п., 2 знака) и p-value;
- `"rev_diff"` и `"rev_p"` — изменение выручки на сессию (₽, 1 знак) и p-value Уэлча;
- `"decision"` — `"внедрять"`, если SRM в порядке, опоздания **значимо снизились** и выручка на сессию **значимо не упала** (не «p < 0.05 и разница < 0»); иначе — `"не внедрять"`.

Функция должна работать на любой части данных — например, только на одном городе.

### setup
```python
import pandas as _pd0
import numpy as _np0
from scipy import stats as _st0
from statsmodels.stats.proportion import proportions_ztest as _z0
def _ref_ab():
    return _pd0.read_csv('ab_promise.csv', parse_dates=['ts'])
def _ref_share(x, flag):
    g = x.groupby('group')[flag].agg(['sum', 'size', 'mean'])
    a, b = g.loc['A'], g.loc['B']
    se = _np0.sqrt(a['mean'] * (1 - a['mean']) / a['size'] + b['mean'] * (1 - b['mean']) / b['size'])
    d = b['mean'] - a['mean']
    p = _z0([b['sum'], a['sum']], [b['size'], a['size']])[1]
    return a['mean'], b['mean'], d, d - 1.96 * se, d + 1.96 * se, p
```

### starter
```python
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

def promise_report(ab):
    ...

ab = pd.read_csv("ab_promise.csv", parse_dates=["ts"])
promise_report(ab)
```

### check
```python
a = _ref_ab()
f = need('promise_report')
def _w(x):
    srm = _st0.chisquare(x['group'].value_counts()).pvalue
    _, _, dl, _, _, pl = _ref_share(x[x['ordered'] == 1], 'late')
    _, _, dc, _, _, pc = _ref_share(x[x['distance_km'] < 2], 'ordered')
    A, B = x.loc[x['group'] == 'A', 'amount'], x.loc[x['group'] == 'B', 'amount']
    pr = _st0.ttest_ind(B, A, equal_var=False).pvalue
    rd = B.mean() - A.mean()
    dec = 'внедрять' if srm >= 0.01 and pl < 0.05 and dl < 0 and not (pr < 0.05 and rd < 0) else 'не внедрять'
    return {'srm_ok': bool(srm >= 0.01), 'late_diff_pp': round(dl * 100, 1), 'late_p': pl, 'conv_short_diff_pp': round(dc * 100, 2),
            'conv_short_p': pc, 'rev_diff': round(rd, 1), 'rev_p': pr, 'decision': dec}
fake = a.copy()
fake.loc[fake['group'] == 'B', 'amount'] = (fake.loc[fake['group'] == 'B', 'amount'] * 0.7).round()
for x, name in ((a, 'весь тест'), (a[a['city'] == 'Казань'], 'только Казань'), (fake, 'выручка B упала на 30 %')):
    got, want = f(x.copy()), _w(x)
    for k, v in want.items():
        assert k in got, f'Нет ключа {k!r}.'
        ok = (got[k] == v) if isinstance(v, (str, bool)) else close(got[k], v, 6e-5 if k.endswith('_p') else 1e-6)
        assert ok, f'{name}: {k} = {got[k]!r}, а нужно {v!r}.'
```

### hint
Внутри — шаги 2, 3 и 5. Удобно завести вспомогательную функцию для разницы долей и p.

### hint
Условие решения: `srm_ok and late_p < 0.05 and late_diff < 0 and not (rev_p < 0.05 and rev_diff < 0)`.

### solution
```python
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

def share_test(x, col):
    g = x.groupby("group")[col].agg(["sum", "size", "mean"])
    z, p = proportions_ztest([g.loc["B", "sum"], g.loc["A", "sum"]], [g.loc["B", "size"], g.loc["A", "size"]])
    return g.loc["B", "mean"] - g.loc["A", "mean"], p

def promise_report(ab):
    srm_p = stats.chisquare(ab["group"].value_counts()).pvalue
    late_d, late_p = share_test(ab[ab["ordered"] == 1], "late")
    conv_d, conv_p = share_test(ab[ab["distance_km"] < 2], "ordered")
    A = ab.loc[ab["group"] == "A", "amount"]
    B = ab.loc[ab["group"] == "B", "amount"]
    rev_d = B.mean() - A.mean()
    rev_p = stats.ttest_ind(B, A, equal_var=False).pvalue
    ok = srm_p >= 0.01 and late_p < 0.05 and late_d < 0 and not (rev_p < 0.05 and rev_d < 0)
    return {
        "srm_ok": bool(srm_p >= 0.01),
        "late_diff_pp": round(late_d * 100, 1), "late_p": late_p,
        "conv_short_diff_pp": round(conv_d * 100, 2), "conv_short_p": conv_p,
        "rev_diff": round(rev_d, 1), "rev_p": rev_p,
        "decision": "внедрять" if ok else "не внедрять",
    }

ab = pd.read_csv("ab_promise.csv", parse_dates=["ts"])
promise_report(ab)
```

### explain
Глава 5 пройдена. Итог для руководителя: новое обещание для пешей зоны вдвое сокращает опоздания и заметно поднимает оценки; конверсия в пешей зоне падает примерно на 3.6 п.п.; выручка на сессию, возможно, снижается, но тест не может это ни подтвердить, ни исключить. Рекомендация «внедрять» следует из правила, выбранного заранее: защитная метрика в нём — выручка, а она значимо не упала. Падение конверсии — главная оговорка отчёта. Условие — следить за выручкой, а лучше продлить тест примерно до семи недель (около 9 400 сессий на группу), чтобы сузить интервал по деньгам до ±10 ₽. Следующая глава — машинное обучение: научимся не только проверять гипотезы, но и предсказывать.
