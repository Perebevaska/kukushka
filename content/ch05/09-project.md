---
revisions: {c1: loss-limit-25}
title: "Проект: новое обещание доставки"
lead: "Финал главы. В главе 4 мы выяснили, что пешим курьерам обещают нереальные 30 минут. Бизнес провёл эксперимент: половине сессий в пешей зоне стали обещать 40 минут. Помогло ли это — и не испортило ли продажи? Анализируем A/B-тест целиком: от проверки дизайна до решения."
files: [ab_promise.csv]
recap:
  - "Анализ эксперимента начинают с проверки дизайна: SRM и то, что изменение действует ровно там, где задумано."
  - "Главная метрика отвечает на вопрос «сработало ли», защитные — «чем заплатили»."
  - "Каждую разницу сопровождают интервалом и p-value; незначимое ≠ нулевое."
  - "Сегменты, заданные заранее, — часть дизайна; найденные после теста — повод для нового теста."
  - "Решение — правило, записанное до анализа, плюс честный рассказ о неопределённости."
  - "Защитная метрика проверяется порогом допустимого ухудшения δ: «значимо не упала» не доказывает, что вреда нет."
---

## Задача

> После разбора опозданий мы с 1 по 21 декабря провели эксперимент. Сессии случайно делили пополам. Назначение выполнено на сессию, а не на постоянный ID гостя. В группе B тем, кто заказывает на расстоянии строго меньше 2 км (пешая зона), приложение обещало доставку за 40 минут вместо 30. Дальние зоны не меняли. Нужен вывод: внедрять новое обещание или нет.

Данные — `ab_promise.csv`: каждая строка — сессия в приложении доставки. Ровно 2.0 км относится к дальней зоне (обещание 45 минут). Постоянного ID гостя нет: нельзя проверить закрепление группы между его визитами или измерить удержание людей.

До открытия разбора запишите свой план: единица назначения; H₀ для главной метрики; защитная метрика и допустимая потеря 10 ₽; дата единственного анализа (после 21 декабря); правило решения. После расчёта сдайте три предложения руководителю: решение по правилу, число с интервалом, ограничение. Это часть обязательного блокнота. На основном маршруте посчитайте выручку на все назначенные сессии, включая нули, и 95%-й интервал разницы B−A: они нужны для решения по защитной границе. Карточка money помогает оформить этот расчёт. Готовая функция решения из шага 8 остаётся углублением.

Столбцы: `session_id`, `ts` — время сессии, `group` — A или B, `city`, `distance_km`, `promise_min` — какое обещание увидел гость, `ordered` — сделал ли заказ (1/0). Для заказов: `courier`, `amount` — сумма (у сессий без заказа — 0), `actual_min`, `late` — опоздал ли (1/0), `rating` — оценка, если поставлена.

Для самостоятельной работы скачайте [шаблон статистического отчёта](../notebooks/ch05-project-template.ipynb) и [check_notebook.py](../notebooks/check_notebook.py). Положите [ab_promise.csv](../data/ab_promise.csv) в `data/` рядом с блокнотом. В шаблоне план расположен до вычисления эффектов. Перед передачей выполните **Restart Kernel and Run All Cells**, сохраните результаты и запустите `python check_notebook.py promise.ipynb`.

## План

1. Проверить, что эксперимент устроен как задумано.
2. Главная метрика: доля опозданий.
3. Конверсия — в целом и в пешей зоне: откуда могут уйти деньги.
4. Оценки гостей.
5. Защитная метрика правила: выручка на сессию и допустимое снижение.
6. Устойчивость: эффект по городам с поправкой.
7. График для руководителя.
8. Отчёт и решение одной функцией.

Правило решения зафиксировано заранее. Бизнес согласен потерять на новом обещании не больше **δ = 10 ₽ выручки на сессию** (около 5 % от нынешних ~206 ₽). Тогда:

- **внедрять** — опоздания значимо снизились, а нижняя граница 95 %-го интервала разницы выручки (B − A) выше −10 ₽: потеря больше допустимой исключена;
- **не внедрять** — если значимое снижение опозданий не подтверждено либо верхняя граница интервала по выручке ниже −10 ₽. Во втором случае весь интервал указывает на недопустимую потерю;
- **неопределённо** — опоздания снизились, но интервал по выручке захватывает −10 ₽: данных не хватает, чтобы исключить недопустимую потерю.

Почему не «внедрять, если выручка значимо не упала»: незначимость — это отсутствие доказательства вреда, а не доказательство его отсутствия. Чем меньше тест и шире интервал, тем легче «не найти» падение, — такое правило поощряло бы короткие тесты.

Почему защитная метрика в правиле — выручка, а не конверсия: более долгое обещание может отпугнуть часть заказов, но и вернуть гостей, которых раньше злили опоздания. Эта выгрузка измеряет конверсию и выручку на назначенную сессию; предполагаемый возврат людей без постоянного ID гостя здесь не измерен. Поэтому конверсию мы тоже посчитаем (шаг 3) — она подскажет, откуда могут уйти деньги, — но решение по правилу принимает выручка.

**До просмотра результата.** Другая команда до запуска выбрала допустимую потерю **25 ₽ на сессию**. Запишите в своих заметках, с какой границей интервала и каким числом вы сравните результат, если опоздания значимо снизятся. Для проекта кофеен продолжает действовать его первоначальный предел 10 ₽.

## Примените своё правило

::: quiz
В новом тесте распределение сессий между группами прошло проверку. Опоздания снизились на 10 п.п. (p < 0.001). Выручка на сессию изменилась на −8 ₽, 95%-й интервал B − A от −23 до +7 ₽. Какое решение следует из заранее согласованного предела 25 ₽?

- [x] Внедрять: опоздания снизились, а нижняя граница выручки выше −25 ₽
  > Верно. −23 ₽ выше −25 ₽. Интервал допускает снижение, но весь диапазон укладывается в заранее принятую границу. При исходном пределе 10 ₽ на тех же данных вывод был бы неопределённым.
- [ ] Пока неопределённо: интервал включает ноль
  > Ноль отвечает на вопрос о наличии изменения. Для решения этой команды сравните нижнюю границу интервала с допустимой потерей −25 ₽.
- [ ] Не внедрять: средняя выручка упала на 8 ₽
  > Точечная оценка показывает наблюдаемое изменение. Правило требует посмотреть, какую потерю ещё допускает нижняя граница интервала.
- [ ] Пока неопределённо: возможна потеря больше 10 ₽
  > Десять рублей были пределом команды кофеен. Для этого эксперимента до начала согласовали 25 ₽. Найдите соответствующую запись в своём плане.
:::

## Разберём вместе: главная метрика на салфетке

Разберём другой эксперимент на небольших числах. Из 100 доставок со старым обещанием опоздали 20, с новым — 10 из 100.

1. Доли опозданий равны 20 % и 10 %. Разница B − A составляет −10 процентных пунктов.
2. Стандартная ошибка разницы равна √(0.20 × 0.80 / 100 + 0.10 × 0.90 / 100) = 0.05.
3. Приближённый 95 %-й интервал для разницы равен −0.10 ± 1.96 × 0.05, то есть от −19.8 до −0.2 п.п.

Этот расчёт описывает опоздания в примере. Для решения о внедрении понадобится также интервал для выручки. Запишите правило, а затем откройте выгрузку «Зерна» и получите оба результата самостоятельно.

::: warn Типичные ошибки проекта
- **Опоздания по сессиям.** Доля опозданий считается среди **заказов** (`orders`), а не среди всех сессий — у сессий без заказа опоздания нет.
- **Конверсия только в целом.** Эффект обещания касается пешей зоны; в целом он «разбавлен» дальними заказами.
- **Правило решения после результатов.** Оно зафиксировано заранее — им и пользуемся, даже если результат хочется трактовать иначе.
- **«Незначимо» = «безопасно».** p > 0.05 по выручке не исключает потерю; смотрим, где нижняя граница интервала относительно −δ.
- **Города без поправки.** Четыре города — четыре проверки; Холм обязателен.
:::

Начиная со второго шага, перед задачей курс сам загружает `ab` (вся выгрузка) и `orders` (только сессии с заказом).

::: figure promise-denoms
Продолжение примера с двумя группами по 100 доставок. Пусть в A было 200 сессий, в B — 250, а выручка каждой группы составила 30 000 ₽. Проследите, почему при одинаковом числе заказов и одинаковой сумме получилась разная выручка на сессию.
:::

## Вопрос из другой области

Образовательная платформа назначает новую программу целым классам, а результаты сохраняет по ученикам. Какую единицу считать независимой при сравнении? Объясните, почему один класс из 30 учеников не даёт 30 независимых назначений. Какие сведения нужны, если нас интересует средний эффект на ученика?

## Практика

## task: design | Шаг 1. Проверка эксперимента | base

Загрузите `ab_promise.csv` (`ts` — датой) в `ab`. Проверьте, что эксперимент устроен как задумано:

- `srm_p` — p-value проверки SRM по числу сессий в группах;
- `promise_ok` — `True`, если в зоне до 2 км **все** сессии группы A видели обещание 30 минут, а группы B — 40 минут;
- `far_same` — `True`, если в каждой сессии обеих групп обещание равно 45 минут при `2 <= distance_km < 5` и 60 минут при `distance_km >= 5`. Совпадение множеств без проверки строк недостаточно.

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
same = bool((f['promise_min'] == f['distance_km'].map(lambda x: 45 if x < 5 else 60)).all())
assert need('far_same') == same, f'far_same должно быть {same}.'
assert 0 <= need('srm_p') <= 1, 'srm_p должен быть вероятностью от 0 до 1.'
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
far_same = bool((far["promise_min"] == far["distance_km"].map(lambda x: 45 if x < 5 else 60)).all())
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
assert 0 <= need('p_late') <= 1, 'p_late — вероятность от 0 до 1.'
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
При новом обещании доля опозданий среди оформленных заказов примерно вдвое ниже. Это результат относительно срока, который увидел клиент. Срок стал длиннее, и после показа обещания клиент решал, заказывать ли. Поэтому различие долей само по себе не означает, что курьеры стали быстрее. Далее проверьте конверсию и выручку на назначенную сессию.

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
В пешей зоне после назначения нового обещания реже оформляли заказы. В дальней зоне срок остался прежним, и данные совместимы с равной конверсией. Сопоставление двух p-value не проверяет различие эффектов между зонами. Пешая зона выбрана до эксперимента. Общий и дальний срезы служат диагностике. Если решение зависит от любой из нескольких проверок, заранее определите, как контролировать ошибку для всей группы сравнений.

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
assert 0 <= need('p_rating') <= 1, 'p_rating должен быть вероятностью от 0 до 1.'
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
Средняя оценка выросла с 4.46 до 4.64, доля «не пятёрок» упала с 36 % до 27 %, p ≈ 0.00007. Это оценки **ответивших**:709 из 1365 заказов A и 729 из 1301 B. Состав заказавших и ответивших мог измениться после назначения; вывод о всех сессиях или всех людях по этим оценкам не следует.

## task: money | Шаг 5. Деньги на сессию | plus

Выручка на сессию (`amount`, у сессий без заказа — 0) — итог «меньше опозданий» против «меньше заказов». Сохраните `rev_a`, `rev_b` (1 знак), `p_rev` — p-value t-теста Уэлча и 95 %-й интервал разницы B − A по заранее выбранной нормальной аппроксимации: `rev_lo`, `rev_hi`. Разность средних ± `1.96 * sqrt(var_A / n_A + var_B / n_B)`, дисперсии с `ddof=1`.

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
_se = _np0.sqrt(A.var() / len(A) + B.var() / len(B))
_diff = B.mean() - A.mean()
assert close(lo, _diff - 1.96 * _se, 0.051) and close(hi, _diff + 1.96 * _se, 0.051), 'Интервал: B−A ±1.96*SE на всех сессиях; тот же метод используем в финальном решении.'
assert 0 <= need('p_rev') <= 1, 'p_rev должен быть вероятностью от 0 до 1.'
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
se = np.sqrt(A.var(ddof=1) / len(A) + B.var(ddof=1) / len(B))
rev_lo, rev_hi = B.mean() - A.mean() - 1.96 * se, B.mean() - A.mean() + 1.96 * se
```

### explain
Выручка на сессию в B ниже примерно на 13 ₽, интервал — примерно от −28 до +2 ₽. Он захватывает ноль, поэтому падение незначимо, но захватывает и −10 ₽: потерю больше допустимой тест не исключает. По правилу это «неопределённо», а не «внедрять». Тест не даёт уверенного ответа про деньги — это важно честно сказать в отчёте. Что делать дальше, тоже можно посчитать: чтобы интервал разницы сузился до ±10 ₽, нужно SE разницы ≈ 10 / 1.96 ≈ 5.1 ₽. При σ около 350 ₽ в каждой группе это (350² + 350²) / 5.1² ≈ 9 400 сессий на группу — в 2.4 раза больше, чем сейчас, это ориентир для планирования нового этапа по правилу √n. Он не разрешает просто дописывать строки до удобного результата: задайте независимый подтверждающий этап или последовательную процедуру до следующего просмотра.

Значимый результат в одном сегменте и незначимый в другом не доказывают различия эффектов. Для такого вопроса оценивают контраст эффектов либо взаимодействие «вариант × сегмент»; поправка Холма решает другой вопрос — семейство отдельных проверок.

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
    assert 0 <= t.loc[c, 'p'] <= 1 and close(t.loc[c, 'p'], v[3], 6e-5), f'{c}: пересчитайте исходное p-value до поправки Холма.'
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

Для вопроса о разнице групп дополнительно приведите рассчитанный интервал B−A в тексте блокнота; отдельные усы Уилсона относятся к каждой доле.

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
# include-check: ch05_plot_identity.py
from statsmodels.stats.proportion import proportion_confint as _pc
_o = _ref_ab().query('ordered == 1')
_s = _ref_ab().query('distance_km < 2')
assert len(figs) == 1 and len(figs[0].axes) == 2, 'Два графика рядом: plt.subplots(1, 2).'
for _ax, _data, _column in zip(figs[0].axes, (_o, _s), ('late', 'ordered')):
    _g = _data.groupby('group')[_column].agg(['sum', 'size', 'mean'])
    _lo, _hi = _pc(_g['sum'], _g['size'], method='wilson')
    _want = {name: (row['mean'] * 100, low * 100, high * 100) for (name, row), low, high in zip(_g.iterrows(), _lo, _hi)}
    _ticks = _category_ticks(_ax, _g.index)
    _bars = [p for p in _ax.patches if _artist_visible(p) and _color_visible(p.get_facecolor()) and p.get_width() > 0]
    assert len(_bars) == 2, 'Для каждой группы нужен видимый столбец.'
    for _x, _name in _ticks:
        _height, _low, _high = _want[_name]
        _bar_points = [_p.get_transform().transform([[.5, 0], [.5, 1]]) for _p in _bars]
        _expected = _np.array([[_x, _ax.transData.transform((0, 0))[1]], [_x, _ax.transData.transform((0, _height))[1]]])
        assert any(_np.allclose(_points, _expected, rtol=0, atol=1e-5) for _points in _bar_points), f'{_name}: высота столбца должна соответствовать фактической подписи группы на оси X.'
        assert _has_interval(_ax, _visible_interval_segments(_ax), _x, _low, _high), f'{_name}: нужны видимые усы 95% интервала Уилсона этой группы.'
    _labels = [t for t in _ax.texts if _artist_visible(t) and t.get_text().strip()]
    assert len(_labels) == 2, 'Подпишите значение на каждом столбце.'
    _seen = set()
    for _text in _labels:
        _name = _text_group(_text, _ticks)
        assert _name not in _seen, 'Каждому столбцу нужна собственная подпись значения.'
        _seen.add(_name)
        _value = float(_text.get_text().replace('%', '').strip())
        assert close(_value, _want[_name][0], .051), f'{_name}: подпись должна показывать процент этой группы.'
    assert _ax.get_title().strip(), 'Добавьте заголовок-вывод.'
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
Два столбца рядом с «усами» читаются за секунду: опозданий вдвое меньше, а конверсия в пешей зоне просела на несколько пунктов — но отдельные групповые интервалы не являются интервалом разницы B−A. Для вывода о различии прочтите интервал нужного контраста из расчёта и его тест. Подписи значений избавляют руководителя от необходимости угадывать по оси, а «усы» показывают неопределённость каждой доли. Их перекрытие само по себе не заменяет тест разницы. Заголовок-вывод («Опозданий вдвое меньше») важнее заголовка-описания («Доля опозданий по группам»).

В этом дополнительном шаге интервал денег рассчитывается нормальной аппроксимацией; в шаге money используется та же заранее выбранная нормальная аппроксимация. Укажите метод рядом с результатом; бутстрэп остаётся отдельной практикой. Новый независимый этап планируется до получения его данных.

## task: decision | Шаг 8. Отчёт и решение | star

Допустимая потеря выручки — 10 ₽ на сессию. Какую нижнюю границу вы сравните с −10 ₽ и какую покажете руководителю? Например, −9,96 и −10,04 ₽ в отчёте обе выглядят как −10,0 ₽. Сохраните в блокноте неокруглённые границы интервала рядом с решением. Сравните их с порогом и затем округлите поля итогового словаря для вывода. Так по сохранённому анализу можно проверить, почему одинаковые подписи привели к разным решениям.

Напишите `promise_report(ab)`. Функция принимает выгрузку эксперимента и возвращает словарь:

- `"srm_ok"` — p SRM не меньше 0.01;
- `"late_diff_pp"` и `"late_p"` — изменение доли опозданий среди заказов (B − A, п.п., 1 знак) и p-value;
- `"conv_short_diff_pp"` и `"conv_short_p"` — изменение конверсии в зоне до 2 км (п.п., 2 знака) и p-value;
- `"rev_diff"` и `"rev_p"` — изменение выручки на сессию (₽, 1 знак) и p-value Уэлча;
- `"rev_lo"` и `"rev_hi"` — 95 %-й интервал этой разницы по нормальному приближению: `rev_diff ± 1.96 × se`, где `se = √(var_A / n_A + var_B / n_B)` (₽, 1 знак);
- `"decision"` по правилу с δ = 10 ₽:
  - `"не внедрять"` — SRM не в порядке, опоздания значимо не снизились или `rev_hi < −10`;
  - `"внедрять"` — опоздания значимо снизились и `rev_lo > −10`;
  - `"неопределённо"` — всё остальное.

Проверьте функцию на полной выгрузке и отдельно на каждом городе. В этих входах есть A и B, заказы обеих групп и сессии ближней зоны обеих групп. Перед срезом сначала убедитесь, что все группы, необходимые для метрик отчёта, представлены.

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
    se = _np0.sqrt(A.var() / len(A) + B.var() / len(B))
    lo, hi = rd - 1.96 * se, rd + 1.96 * se
    if srm < 0.01 or not (pl < 0.05 and dl < 0) or hi < -10:
        dec = 'не внедрять'
    elif lo > -10:
        dec = 'внедрять'
    else:
        dec = 'неопределённо'
    return {'srm_ok': bool(srm >= 0.01), 'late_diff_pp': round(dl * 100, 1), 'late_p': pl, 'conv_short_diff_pp': round(dc * 100, 2),
            'conv_short_p': pc, 'rev_diff': round(rd, 1), 'rev_p': pr, 'rev_lo': round(lo, 1), 'rev_hi': round(hi, 1), 'decision': dec}
def _scaled(k):
    x = a.copy()
    x.loc[x['group'] == 'B', 'amount'] = (x.loc[x['group'] == 'B', 'amount'] * k).round()
    return x
def _near_revenue_limit(target, lower):
    # Scale only money in an isolated frame; zeros and group assignment remain.
    from scipy.optimize import brentq as _root
    x = a.copy()
    x['amount'] = x['amount'].astype(float)
    A = x.loc[x['group'] == 'A', 'amount']
    B = x.loc[x['group'] == 'B', 'amount']
    def endpoint(k):
        d = k * B.mean() - A.mean()
        se = _np0.sqrt(A.var() / len(A) + k*k * B.var() / len(B))
        return d + (-1 if lower else 1) * 1.96 * se
    k = _root(lambda k: endpoint(k) - target, 0.1, 3)
    x.loc[x['group'] == 'B', 'amount'] *= k
    return x
_late_boundary = a.iloc[:4000].copy()
_late_boundary['group'] = ['A'] * 2000 + ['B'] * 2000
_late_boundary['ordered'] = ([1] * 1000 + [0] * 1000) * 2
_late_boundary['distance_km'] = 1.0
_late_boundary['late'] = [1] * 162 + [0] * 1838 + [1] * 131 + [0] * 1869
_late_boundary['amount'] = _np0.r_[_np0.tile([100., 102.], 500), _np0.zeros(1000), _np0.tile([101., 103.], 500), _np0.zeros(1000)]
assert .04995 < _w(_late_boundary)['late_p'] < .05
_cases = ((a, 'весь тест'), (a[a['city'] == 'Казань'], 'только Казань'),
          (_scaled(0.7), 'выручка B упала на 30 %'), (_scaled(1.15), 'выручка B выросла на 15 %'),
          (_near_revenue_limit(-9.96, True), 'нижняя граница −9.96 до округления'),
          (_near_revenue_limit(-10.04, True), 'нижняя граница −10.04 до округления'),
          (_near_revenue_limit(-9.96, False), 'верхняя граница −9.96 до округления'),
          (_near_revenue_limit(-10.04, False), 'верхняя граница −10.04 до округления'),
          (_late_boundary, 'p опозданий чуть ниже 0.05 до округления'))
assert {_w(x)['decision'] for x, _ in _cases} == {'внедрять', 'не внедрять', 'неопределённо'}
for x, name in _cases:
    got, want = f(x.copy()), _w(x)
    for k, v in want.items():
        assert k in got, f'Нет ключа {k!r}.'
        ok = (got[k] == v) if isinstance(v, (str, bool)) else close(got[k], v, 6e-5 if k.endswith('_p') else 0.051 if k in ('rev_lo', 'rev_hi') else 1e-6)
        assert ok, f'{name}: {k} = {got[k]!r}, а нужно {v!r}.'
```

### hint
Внутри — шаги 2, 3 и 5. Удобно завести вспомогательную функцию для разницы долей и p.

### hint
Решение — цепочка `if / elif / else`: сначала «не внедрять» (SRM, опоздания не снизились или `rev_hi < -10`), потом «внедрять» (`rev_lo > -10`), остальное — «неопределённо».

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
    se = np.sqrt(A.var() / len(A) + B.var() / len(B))
    rev_lo, rev_hi = rev_d - 1.96 * se, rev_d + 1.96 * se
    DELTA = 10  # допустимое снижение выручки на сессию, ₽ — зафиксировано до теста
    if srm_p < 0.01 or not (late_p < 0.05 and late_d < 0) or rev_hi < -DELTA:
        decision = "не внедрять"
    elif rev_lo > -DELTA:
        decision = "внедрять"
    else:
        decision = "неопределённо"
    return {
        "srm_ok": bool(srm_p >= 0.01),
        "late_diff_pp": round(late_d * 100, 1), "late_p": late_p,
        "conv_short_diff_pp": round(conv_d * 100, 2), "conv_short_p": conv_p,
        "rev_diff": round(rev_d, 1), "rev_p": rev_p,
        "rev_lo": round(rev_lo, 1), "rev_hi": round(rev_hi, 1),
        "decision": decision,
    }

ab = pd.read_csv("ab_promise.csv", parse_dates=["ts"])
promise_report(ab)
```

### explain
Передайте руководителю решение по записанному правилу. Назовите разницу в опозданиях, интервал изменения выручки и его положение относительно допустимой потери. Если понадобится ещё один этап, заранее запишите его объём, дату окончания и метод анализа. В следующей главе вы построите первую модель прогноза.
