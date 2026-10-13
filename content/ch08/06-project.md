---
title: "Проект: где поставить кофейные автоматы"
lead: "Проект главы (итоговый проект первой части курса про ML — следующий урок). «Зерно» выходит в новый формат — кофейные автоматы в бизнес-центрах, вузах и на вокзалах. Есть деньги на 40 автоматов в одном из трёх городов. Нужно выбрать город и места так, чтобы заработать — и не рискнуть деньгами сверх допустимого."
files: [sites.csv]
recap:
  - "Решение «где инвестировать» — это модель + экономика + риск: прогноз прибыли места, выбор лучших по прогнозу, бутстрэп итоговой прибыли."
  - "Модель полезна не точностью сама по себе, а тем, насколько выбранные по ней места лучше случайных."
  - "Средняя прибыль — не единственный критерий: город с наибольшим средним может не пройти по риску убытка."
  - "Чем хуже модель предсказывает (ниже R², выше RMSE), тем шире разброс итоговой прибыли и выше риск."
  - "Правило решения (порог риска, критерий выбора) фиксируют до расчёта."
  - "Более сложная модель не всегда лучше: на почти линейной связи линейная регрессия выигрывает у леса."
---

## Задача

> Мы запускаем кофейные автоматы. Бюджет — 40 автоматов в одном городе на ближайший год; каждый обходится в 140 тыс. ₽ в год (аренда оборудования, обслуживание, логистика). Команда обследовала по 1 500 мест в Перми, Казани и Екатеринбурге и по похожим точкам оценила годовую прибыль места до вычета стоимости автомата.
>
> В реальном запуске разведка успевает обследовать около 300 мест в выбранном городе, из них мы поставим автоматы в 40 лучших. Помогите выбрать город. Условие совета директоров: **вероятность убытка — не больше 2.5 %**. Среди городов, которые проходят это условие, выбираем город с наибольшей средней прибылью.
>
> *Директор по развитию*

## Данные

`sites.csv` — обследованные места:

| столбец | что это |
|---|---|
| `site_id` | номер места |
| `city` | город |
| `place` | тип места: бизнес-центр, вуз, больница, вокзал, ТЦ, завод |
| `traffic` | людей в день рядом с местом |
| `offices` | офисов в радиусе 300 м |
| `competitors` | кофеен и автоматов поблизости |
| `rent_k` | аренда места, тыс. ₽ в год |
| `hours24` | доступ круглосуточно (1/0) |
| `profit_k` | годовая прибыль места без стоимости автомата, тыс. ₽ (целевой признак) |

## План

1. Осмотреть данные: сколько мест в каждом городе окупают автомат.
2. Подготовить признаки.
3. Обучить линейную регрессию отдельно для каждого города и оценить качество.
4. Выбрать 40 лучших мест на тестовой выборке и сравнить со случайным выбором.
5. Оценить риск бутстрэпом: 1000 раз «обследовать» 300 мест, выбрать 40 лучших по прогнозу, посчитать прибыль.
6. Применить правило совета директоров.
7. Проверить, не изменит ли решение другая модель.

::: quiz
Допустим, в городе А средняя прибыль от 40 мест выше, чем в городе Б, но в 8 % бутстрэп-выборок город А уходит в минус. По правилу совета допустимо не больше 2.5 %. Что делать?

- [x] Не выбирать город А: его риск выше порога, а правило совета важнее средней прибыли
  > Средняя прибыль не учитывает риск. Решение принимают по заранее согласованному правилу.
- [ ] Выбрать город А: средняя прибыль выше
  > Совет заранее ограничил допустимый риск — его нельзя игнорировать задним числом.
- [ ] Пересчитать бутстрэп с другим зерном, пока риск не станет ниже
  > Подбор зерна под нужный ответ — самообман.
- [ ] Взять 80 мест вместо 40
  > Условие задачи — 40 мест. Менять его ради нужного результата нельзя.
:::

## Разберём вместе: одно «обследование» руками

Прежде чем запускать 1000 повторов, разберём один на игрушке. Пусть разведка обследовала 6 мест, а поставить можем 2 автомата по 140 тыс. ₽:

| место | прогноз, тыс. ₽ | факт, тыс. ₽ |
|---|---|---|
| A | 210 | 190 |
| B | 180 | 95 |
| C | 150 | 230 |
| D | 90 | 60 |
| E | 70 | 85 |
| F | 40 | 20 |

1. **Выбор по прогнозу:** два наибольших прогноза — A (210) и B (180).
2. **Прибыль по факту:** 190 + 95 − 2 × 140 = **5 тыс. ₽**. Едва в плюсе.
3. **Обещание модели:** 210 + 180 − 280 = **110 тыс. ₽**. Модель переоценила выбранные места.
4. **Лучший возможный выбор** (A и C по факту): 190 + 230 − 280 = **140 тыс. ₽** — модель его не нашла, потому что недооценила C.

Что получилось. Во-первых, прибыль считается по **факту** выбранных мест, а выбираются они по **прогнозу** — в этом весь смысл проверки. Во-вторых, места выбираются как раз там, где прогноз высок, а высокий прогноз часто — удачная ошибка в плюс (место B). Поэтому «обещание» выбранного топа систематически выше реальности; это называют **проклятием победителя**. В-третьих, при другом наборе из 6 мест результат был бы другим — отсюда бутстрэп: повторяем «обследование» 1000 раз и смотрим на распределение.

::: figure winners-curse
Шесть мест игрушечного примера: прогноз и факт каждого. Выбранные по прогнозу A и B обещали 110 тыс. ₽, а дали 5: место B попало в топ благодаря ошибке прогноза в плюс.
:::

::: tip Аналогия
На аукционе картину чаще всего выигрывает не тот, кто оценил её точнее, а тот, кто сильнее всех её переоценил. Отбор «лучших по прогнозу» работает так же: в топ чаще попадают места, где модель ошиблась в плюс. Где аналогия хромает: на аукционе переплата видна сразу, а у автомата — только через год работы. Поэтому прибыль проверяют по факту на отложенных местах.
:::

Почему «обследуем» именно тестовые места и с возвращением. Обучающие места модель уже видела, их прогнозы слишком хороши — для честной проверки нужны те, которых она не видела, то есть тест (375 мест на город). Выборка 300 мест из 375 с возвращением имитирует другой результат разведки: разведка найдёт не те же самые места, а другой набор похожих. Повторив это 1000 раз, видим, насколько итог зависит от того, какие места попались.

Один повтор бутстрэпа делает с 300 местами то же, что мы только что сделали руками с шестью:

::: figure sites-boot
Цикл шага 5: «обследовать» 300 мест с возвращением, взять 40 лучших по прогнозу, посчитать прибыль по факту — и так 1000 раз. Из 1000 прибылей получаются среднее, интервал и вероятность убытка.
:::

::: tip
Модели — отдельные для каждого города: связь трафика с прибылью в городах разная, и общая модель смешала бы их.
:::

## task: look | Шаг 1. Сколько мест окупается | base

Посчитайте по городам число мест, среднюю прибыль (1 знак) и долю мест, где прибыль больше стоимости автомата (140 тыс. ₽), 3 знака. Сохраните DataFrame `overview` (индекс — город, столбцы `sites`, `mean_profit`, `pays_off`) и в `best_avg_city` — город с наибольшей средней прибылью.

### starter
```python
import pandas as pd
s = pd.read_csv("sites.csv")

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('sites.csv')
o = need('overview', _pd.DataFrame)
for city, part in s0.groupby('city'):
    assert city in o.index, f'Нет города {city} в индексе overview.'
    assert o.loc[city, 'sites'] == len(part), f'{city}: sites = {o.loc[city, "sites"]}.'
    assert close(o.loc[city, 'mean_profit'], round(part['profit_k'].mean(), 1)), f'{city}: mean_profit = {o.loc[city, "mean_profit"]}.'
    assert close(o.loc[city, 'pays_off'], round((part['profit_k'] > 140).mean(), 3)), f'{city}: pays_off = {o.loc[city, "pays_off"]} — доля мест с profit_k > 140.'
assert need('best_avg_city') == s0.groupby('city')['profit_k'].mean().idxmax(), f'best_avg_city = {need("best_avg_city")!r}.'
```

### hint
Сначала добавьте флаг окупаемости: `s["pays"] = s["profit_k"] > 140` — среднее флага и есть доля.

### hint
`s.groupby("city").agg(sites=("profit_k", "size"), mean_profit=("profit_k", "mean"), pays_off=("pays", "mean"))`, затем округление столбцов.

### solution
```python
import pandas as pd
s = pd.read_csv("sites.csv")
s["pays"] = s["profit_k"] > 140
overview = s.groupby("city").agg(sites=("profit_k", "size"), mean_profit=("profit_k", "mean"), pays_off=("pays", "mean"))
overview["mean_profit"] = overview["mean_profit"].round(1)
overview["pays_off"] = overview["pays_off"].round(3)
best_avg_city = overview["mean_profit"].idxmax()
```

### explain
Средняя прибыль места — около 65–71 тыс. ₽, вдвое меньше стоимости автомата: случайное место скорее всего убыточно: окупается только от 16 до 29 % мест. Значит, всё решает выбор мест. Екатеринбург выглядит лучшим по среднему и по доле окупаемых мест — запомним это.

## task: prep | Шаг 2. Признаки | base

Напишите функцию `prep(part)`, которая из таблицы мест делает матрицу признаков: столбцы `place`, `traffic`, `offices`, `competitors`, `rent_k`, `hours24`, тип места — через `pd.get_dummies(..., dtype=int)`, а `traffic` заменён натуральным логарифмом (`np.log`). Сохраните `X_perm = prep(...)` для мест Перми.

### starter
```python
import numpy as np
import pandas as pd
s = pd.read_csv("sites.csv")

```

### check
```python
import numpy as _np, pandas as _pd
s0 = _pd.read_csv('sites.csv'); p0 = s0[s0['city'] == 'Пермь']
f = need('prep')
Xp = need('X_perm', _pd.DataFrame)
assert len(Xp) == len(p0), f'В X_perm {len(Xp)} строк, а мест в Перми {len(p0)}.'
assert 'profit_k' not in Xp.columns and 'city' not in Xp.columns and 'site_id' not in Xp.columns, 'В признаках не должно быть profit_k, city и site_id.'
assert any(c.startswith('place_') for c in Xp.columns), 'Тип места должен превратиться в флаги place_… через get_dummies.'
assert _np.allclose(Xp['traffic'].values, _np.log(p0['traffic'].values)), 'traffic должен быть заменён на np.log(traffic).'
assert set(Xp.columns) == {'traffic', 'offices', 'competitors', 'rent_k', 'hours24'} | {f'place_{v}' for v in p0['place'].unique()}, f'Столбцы X_perm: {list(Xp.columns)}.'
```

### hint
Функция принимает часть таблицы и возвращает новую таблицу признаков — `city`, `site_id` и `profit_k` в неё не попадают.

### hint
Внутри функции: `X = pd.get_dummies(part[[...]], dtype=int)`, затем `X["traffic"] = np.log(X["traffic"])`.

### solution
```python
import numpy as np
import pandas as pd
s = pd.read_csv("sites.csv")

def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X

X_perm = prep(s[s["city"] == "Пермь"])
```

### explain
Логарифм трафика — из главы 7: прибыль растёт с трафиком, но всё медленнее (тысяча дополнительных прохожих у вокзала значат меньше, чем у маленького вуза). Линейная модель на логарифме описывает это одной прямой.

## task: models | Шаг 3. Модели по городам | base

Для каждого города разделите места на обучение и тест (`train_test_split(X, y, test_size=0.25, random_state=42)`), обучите `LinearRegression` и посчитайте на тесте R² (3 знака) и RMSE (1 знак). Сохраните DataFrame `quality` (индекс — город, столбцы `r2`, `rmse`) и в `most_predictable` — город с наибольшим R².

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

s = pd.read_csv("sites.csv")

def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import r2_score as _r2, mean_squared_error as _mse
s0 = _pd.read_csv('sites.csv'); q = need('quality', _pd.DataFrame); want = {}
for city, part in s0.groupby('city'):
    X = _pd.get_dummies(part[['place', 'traffic', 'offices', 'competitors', 'rent_k', 'hours24']], dtype=int); X['traffic'] = _np.log(X['traffic'])
    a, b, c, d = _tts(X, part['profit_k'], test_size=0.25, random_state=42)
    pr = _LR().fit(a, c).predict(b)
    want[city] = (round(_r2(d, pr), 3), round(_mse(d, pr) ** 0.5, 1))
    assert city in q.index, f'Нет города {city} в quality.'
    assert close(q.loc[city, 'r2'], want[city][0]) and close(q.loc[city, 'rmse'], want[city][1], 0.15), f'{city}: r2, rmse = {q.loc[city, "r2"]}, {q.loc[city, "rmse"]}, а нужно {want[city]}.'
assert need('most_predictable') == max(want, key=lambda k: want[k][0]), f'most_predictable = {need("most_predictable")!r}.'
```

### hint
Цикл `for city, part in s.groupby("city")`; внутри — `prep(part)`, разбиение, обучение, метрики. RMSE: `mean_squared_error(y_test, pred) ** 0.5`.

### hint
Складывайте результаты в словарь `rows[city] = {"r2": ..., "rmse": ...}`, затем `pd.DataFrame(rows).T` — города станут индексом.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

s = pd.read_csv("sites.csv")

def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X

rows = {}
for city, part in s.groupby("city"):
    X_train, X_test, y_train, y_test = train_test_split(prep(part), part["profit_k"], test_size=0.25, random_state=42)
    pred = LinearRegression().fit(X_train, y_train).predict(X_test)
    rows[city] = {"r2": round(r2_score(y_test, pred), 3), "rmse": round(mean_squared_error(y_test, pred) ** 0.5, 1)}
quality = pd.DataFrame(rows).T
most_predictable = quality["r2"].idxmax()
```

### explain
Города очень разные: в Перми модель объясняет почти три четверти разброса прибыли (R² ≈ 0.73, ошибка ≈ 38 тыс. ₽), в Казани — половину, а в Екатеринбурге — меньше четверти (ошибка ≈ 113 тыс. ₽, почти как стоимость автомата). Признаки там те же, но прибыль сильнее зависит от того, чего в данных нет.

## task: top40 | Шаг 4. Сорок лучших мест | base

В заготовке для каждого города уже есть прогнозы и факты на тесте: `fits[city] = (pred, fact)` — две Series с одинаковым индексом. Для каждого города выберите 40 мест с наибольшим прогнозом и посчитайте прибыль: сумма фактической `profit_k` по выбранным минус 40 × 140. Для сравнения посчитайте ожидаемую прибыль 40 случайных мест теста: 40 × средняя `profit_k` теста − 40 × 140. Сохраните DataFrame `top` (индекс — город, столбцы `model`, `random`, оба — до целого).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
s = pd.read_csv("sites.csv")
def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X
fits = {}
for _city, _part in s.groupby("city"):
    _a, _b, _c, _d = train_test_split(prep(_part), _part["profit_k"], test_size=0.25, random_state=42)
    fits[_city] = (pd.Series(LinearRegression().fit(_a, _c).predict(_b), index=_d.index), _d)
_ref_fits = {k: (v[0].copy(), v[1].copy()) for k, v in fits.items()}
```

### starter
```python
# уже есть: s, prep(part), fits[city] = (pred, fact) — прогноз и факт на тестовых местах города
COST, K = 140, 40

```

### check
```python
import pandas as _pd
t = need('top', _pd.DataFrame)
for city, (pr, fa) in _ref_fits.items():
    m = round(fa[pr.nlargest(40).index].sum() - 40 * 140)
    r = round(40 * fa.mean() - 40 * 140)
    assert close(t.loc[city, 'model'], m, 1), f'{city}: model = {t.loc[city, "model"]}, а нужно {m}.'
    assert close(t.loc[city, 'random'], r, 1), f'{city}: random = {t.loc[city, "random"]}, а нужно {r}.'
```

### hint
`best = pred.nlargest(K).index`, затем `fact[best].sum() - K * COST`.

### hint
Случайный выбор в среднем даёт среднюю прибыль места: `K * fact.mean() - K * COST`. Цикл — `for city, (pred, fact) in fits.items()`.

### solution
```python
COST, K = 140, 40
import pandas as pd

rows = {}
for city, (pred, fact) in fits.items():
    best = pred.nlargest(K).index
    rows[city] = {"model": round(fact[best].sum() - K * COST), "random": round(K * fact.mean() - K * COST)}
top = pd.DataFrame(rows).T
```

### explain
Случайные 40 мест приносят убыток около 2.8–3.1 млн ₽ в любом городе, а 40 мест по модели — прибыль: около 1.5 млн ₽ в Перми и Екатеринбурге и 0.6 млн ₽ в Казани. Но это один тестовый набор из 375 мест. В реальности разведка обследует только 300 мест, и какие именно — дело случая. Нужен бутстрэп.

## task: promise | Шаг 4б. Обещание против факта | base

Проверьте проклятие победителя из «Разберём вместе» на тесте. Для каждого города возьмите 40 мест с наибольшим прогнозом и посчитайте `promised` — прибыль по **прогнозам** (сумма прогнозов − 40 × 140) и `actual` — по **фактам**. Сохраните DataFrame `promise` (индекс — город, столбцы `promised`, `actual`, `gap = actual − promised`, все — до целого) и `overpromised` — список городов, где модель пообещала больше, чем получилось.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
s = pd.read_csv("sites.csv")
def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X
fits = {}
for _city, _part in s.groupby("city"):
    _a, _b, _c, _d = train_test_split(prep(_part), _part["profit_k"], test_size=0.25, random_state=42)
    fits[_city] = (pd.Series(LinearRegression().fit(_a, _c).predict(_b), index=_d.index), _d)
_ref_fits = {k: (v[0].copy(), v[1].copy()) for k, v in fits.items()}
```

### starter
```python
# уже есть: s, prep(part), fits[city] = (pred, fact)
COST, K = 140, 40

```

### check
```python
import pandas as _pd
t = need('promise', _pd.DataFrame); over = []
for city, (pr, fa) in _ref_fits.items():
    best = pr.nlargest(40).index
    pm, ac = round(pr[best].sum() - 5600), round(fa[best].sum() - 5600)
    assert close(t.loc[city, 'promised'], pm, 1) and close(t.loc[city, 'actual'], ac, 1), f'{city}: promised, actual = {t.loc[city, "promised"]}, {t.loc[city, "actual"]}, а нужно {pm}, {ac}.'
    assert close(t.loc[city, 'gap'], ac - pm, 2), f'{city}: gap = {t.loc[city, "gap"]}.'
    if ac < pm: over.append(city)
assert sorted(need('overpromised')) == sorted(over), f'overpromised = {need("overpromised")}, а нужно {over}.'
```

### hint
Выбор один и тот же: `best = pred.nlargest(K).index`. Обещание — `pred[best].sum() - K * COST`, факт — `fact[best].sum() - K * COST`.

### hint
`overpromised = [c for c in promise.index if promise.loc[c, "gap"] < 0]`.

### solution
```python
import pandas as pd
COST, K = 140, 40

rows = {}
for city, (pred, fact) in fits.items():
    best = pred.nlargest(K).index
    promised = round(pred[best].sum() - K * COST)
    actual = round(fact[best].sum() - K * COST)
    rows[city] = {"promised": promised, "actual": actual, "gap": actual - promised}
promise = pd.DataFrame(rows).T
overpromised = [c for c in promise.index if promise.loc[c, "gap"] < 0]
```

### explain
Честный результат: на этом тесте проклятие победителя проявилось только в Казани — обещано около 1.0 млн ₽, получено 0.62 млн. В Перми и Екатеринбурге факт даже выше обещания (≈ 1.48 млн против 1.18–1.19). Одна выборка может качнуться в любую сторону, поэтому вывод «модель занижает» по ней делать нельзя — как и «модель не ошибается». Именно поэтому дальше бутстрэп: он показывает, как результат гуляет от обследования к обследованию.

## task: boot | Шаг 5. Риск по городам | plus

Напишите функцию `boot_city(pred, fact)`: генератор `np.random.default_rng(0)`, 1000 повторов; в каждом — 300 номеров мест с возвращением `rng.integers(0, len(fact), 300)`, из них 40 с наибольшим прогнозом (`np.argsort(-p[i])[:40]` по массиву прогнозов), прибыль = сумма фактов выбранных − 40 × 140. Функция возвращает массив из 1000 прибылей. Соберите DataFrame `risk` (индекс — город, столбцы `mean`, `low`, `high`, `p_loss`): среднее и 2.5-й / 97.5-й процентили (до целого), доля убыточных повторов (3 знака).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
s = pd.read_csv("sites.csv")
def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X
fits = {}
for _city, _part in s.groupby("city"):
    _a, _b, _c, _d = train_test_split(prep(_part), _part["profit_k"], test_size=0.25, random_state=42)
    fits[_city] = (pd.Series(LinearRegression().fit(_a, _c).predict(_b), index=_d.index), _d)
_ref_fits = {k: (v[0].copy(), v[1].copy()) for k, v in fits.items()}
def _ref_boot(pred, fact):
    rng = np.random.default_rng(0)
    p, f = pred.values, fact.values
    out = []
    for _ in range(1000):
        i = rng.integers(0, len(f), 300)
        out.append(f[i[np.argsort(-p[i])[:40]]].sum() - 40 * 140)
    return np.array(out)
```

### starter
```python
# уже есть: s, prep(part), fits[city] = (pred, fact)
import numpy as np
COST, K, SURVEY = 140, 40, 300

```

### check
```python
import numpy as _np, pandas as _pd
f = need('boot_city')
pr0, fa0 = _ref_fits['Пермь']
got = _np.asarray(f(pr0, fa0))
assert len(got) == 1000, f'boot_city вернула {len(got)} значений, нужно 1000.'
assert close(float(got.mean()), float(_ref_boot(pr0, fa0).mean()), 1), 'Средняя прибыль по Перми не совпадает. Генератор default_rng(0) внутри функции, integers(0, len(fact), 300), выбор argsort(-p[i])[:40].'
r = need('risk', _pd.DataFrame)
for city, (pr, fa) in _ref_fits.items():
    b = _ref_boot(pr, fa)
    lo, hi = _np.percentile(b, [2.5, 97.5])
    assert close(r.loc[city, 'mean'], round(b.mean()), 1), f'{city}: mean = {r.loc[city, "mean"]}, а нужно {round(b.mean())}.'
    assert close(r.loc[city, 'low'], round(lo), 1) and close(r.loc[city, 'high'], round(hi), 1), f'{city}: интервал {r.loc[city, "low"]}…{r.loc[city, "high"]}, а нужно {round(lo)}…{round(hi)}.'
    assert close(r.loc[city, 'p_loss'], round((b < 0).mean(), 3)), f'{city}: p_loss = {r.loc[city, "p_loss"]}.'
```

### hint
Работайте с массивами: `p, f = pred.values, fact.values`. Выбранные номера: `chosen = i[np.argsort(-p[i])[:K]]`, прибыль — `f[chosen].sum() - K * COST`.

### hint
Генератор создаётся внутри функции — тогда все города проверяются на одинаковых «обследованиях».

### solution
```python
import numpy as np
import pandas as pd
COST, K, SURVEY = 140, 40, 300

def boot_city(pred, fact):
    rng = np.random.default_rng(0)
    p, f = pred.values, fact.values
    out = []
    for _ in range(1000):
        i = rng.integers(0, len(f), SURVEY)
        chosen = i[np.argsort(-p[i])[:K]]
        out.append(f[chosen].sum() - K * COST)
    return np.array(out)

rows = {}
for city, (pred, fact) in fits.items():
    b = boot_city(pred, fact)
    lo, hi = np.percentile(b, [2.5, 97.5])
    rows[city] = {"mean": round(b.mean()), "low": round(lo), "high": round(hi), "p_loss": round((b < 0).mean(), 3)}
risk = pd.DataFrame(rows).T
```

### explain
Картина меняется:

- **Екатеринбург** — наибольшая средняя прибыль (≈ 1.43 млн ₽), но интервал от убытка 0.24 млн до прибыли почти 3 млн, вероятность убытка ≈ 4.6 %;
- **Казань** — средняя ≈ 0.5 млн ₽, вероятность убытка ≈ 12 %;
- **Пермь** — средняя ≈ 1.12 млн ₽, интервал целиком выше нуля, вероятность убытка ≈ 0.1 %.

Риск растёт там, где модель хуже предсказывает: в Екатеринбурге среди «лучших по прогнозу» мест много случайно провальных.

## task: decision | Шаг 6. Решение | base

Примените правило совета директоров к таблице `risk` из прошлого шага (в заготовке она уже посчитана): оставьте города с вероятностью убытка не больше 0.025 и выберите среди них город с наибольшей средней прибылью. Сохраните список прошедших городов `passed` (в порядке индекса `risk`) и `choice` — выбранный город. В `cost_of_safety` сохраните, сколько средней прибыли (тыс. ₽) мы отдаём за безопасность: средняя у лидера по среднему минус средняя у выбранного города.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
s = pd.read_csv("sites.csv")
def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X
def _boot(pred, fact):
    rng = np.random.default_rng(0)
    p, f = pred.values, fact.values
    out = []
    for _ in range(1000):
        i = rng.integers(0, len(f), 300)
        out.append(f[i[np.argsort(-p[i])[:40]]].sum() - 40 * 140)
    return np.array(out)
_rows = {}
for _city, _part in s.groupby("city"):
    _a, _b, _c, _d = train_test_split(prep(_part), _part["profit_k"], test_size=0.25, random_state=42)
    _bb = _boot(pd.Series(LinearRegression().fit(_a, _c).predict(_b), index=_d.index), _d)
    _lo, _hi = np.percentile(_bb, [2.5, 97.5])
    _rows[_city] = {"mean": round(_bb.mean()), "low": round(_lo), "high": round(_hi), "p_loss": round((_bb < 0).mean(), 3)}
risk = pd.DataFrame(_rows).T
_ref_risk = risk.copy()
```

### starter
```python
# уже есть: risk — таблица из шага 5 (mean, low, high, p_loss по городам)
print(risk)

```

### check
```python
ok = _ref_risk[_ref_risk['p_loss'] <= 0.025]
assert list(need('passed')) == list(ok.index), f'passed = {need("passed")}, а нужно {list(ok.index)}.'
assert need('choice') == ok['mean'].idxmax(), f'choice = {need("choice")!r}.'
assert close(need('cost_of_safety'), _ref_risk['mean'].max() - ok['mean'].max(), 1), f'cost_of_safety = {need("cost_of_safety")}.'
```

### hint
«Не больше 2.5 %» — это `<= 0.025`.

### hint
`ok = risk[risk["p_loss"] <= 0.025]`, затем `ok["mean"].idxmax()`. Цена безопасности — `risk["mean"].max() - ok.loc[choice, "mean"]`.

### solution
```python
print(risk)
ok = risk[risk["p_loss"] <= 0.025]
passed = list(ok.index)
choice = ok["mean"].idxmax()
cost_of_safety = risk["mean"].max() - ok.loc[choice, "mean"]
```

### explain
Проходит только Пермь. По среднему мы отдаём около 300 тыс. ₽ в год по сравнению с Екатеринбургом, зато покупаем почти полную уверенность, что не уйдём в минус. Это и есть цена правила риска — её стоит показать совету директоров явно, а не прятать.

## task: profile | Шаг 6б. Какие места выбирает модель | base

Директору нужен не только город, но и понимание, какие места модель считает лучшими. Для Перми возьмите 40 лучших по прогнозу мест теста и сохраните: `bc_share` — долю бизнес-центров среди них (3 знака), `pays_top` и `pays_all` — долю окупаемых мест (`profit_k > 140`) среди выбранных и среди всех мест теста (3 знака), `traffic_top` и `traffic_all` — медианный трафик выбранных и всех мест теста, `comp_top` и `comp_all` — медианное число конкурентов рядом, `rent_top` и `rent_all` — медианную аренду (тыс. ₽).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
s = pd.read_csv("sites.csv")
def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X
fits = {}
for _city, _part in s.groupby("city"):
    _a, _b, _c, _d = train_test_split(prep(_part), _part["profit_k"], test_size=0.25, random_state=42)
    fits[_city] = (pd.Series(LinearRegression().fit(_a, _c).predict(_b), index=_d.index), _d)
_ref_fits = {k: (v[0].copy(), v[1].copy()) for k, v in fits.items()}
```

### starter
```python
# уже есть: s, prep(part), fits[city] = (pred, fact)
pred, fact = fits["Пермь"]

```

### check
```python
pr, fa = _ref_fits['Пермь']; best = pr.nlargest(40).index
w = {'bc_share': round((s.loc[best, 'place'] == 'бизнес-центр').mean(), 3), 'pays_top': round((fa[best] > 140).mean(), 3),
     'pays_all': round((fa > 140).mean(), 3), 'traffic_top': s.loc[best, 'traffic'].median(), 'traffic_all': s.loc[fa.index, 'traffic'].median(),
     'comp_top': s.loc[best, 'competitors'].median(), 'comp_all': s.loc[fa.index, 'competitors'].median(),
     'rent_top': s.loc[best, 'rent_k'].median(), 'rent_all': s.loc[fa.index, 'rent_k'].median()}
for k, v in w.items():
    assert close(need(k), v, 0.6 if ('traffic' in k or 'comp' in k or 'rent' in k) else 0.0011), f'{k} = {need(k)}, а нужно {v}.'
```

### hint
Индексы `pred` и `fact` — это индексы строк исходной таблицы `s`, поэтому свойства мест берутся так: `s.loc[best, "place"]`.

### hint
`best = pred.nlargest(40).index`; доля бизнес-центров — `(s.loc[best, "place"] == "бизнес-центр").mean()`; медиана трафика всех тестовых мест — `s.loc[fact.index, "traffic"].median()`.

### solution
```python
pred, fact = fits["Пермь"]
best = pred.nlargest(40).index
bc_share = round((s.loc[best, "place"] == "бизнес-центр").mean(), 3)
pays_top = round((fact[best] > 140).mean(), 3)
pays_all = round((fact > 140).mean(), 3)
traffic_top = s.loc[best, "traffic"].median()
traffic_all = s.loc[fact.index, "traffic"].median()
comp_top, comp_all = s.loc[best, "competitors"].median(), s.loc[fact.index, "competitors"].median()
rent_top, rent_all = s.loc[best, "rent_k"].median(), s.loc[fact.index, "rent_k"].median()
```

### explain
Портрет понятный: 29 из 40 выбранных мест — бизнес-центры (среди всех мест теста их 42 %), медианный трафик вдвое выше (≈ 1 540 против 740 человек в день), рядом обычно нет конкурентов (медиана 0 против 1), аренда ниже (50 тыс. ₽ против 70). Окупается 77.5 % выбранных мест против 15 % случайных. Такой портрет полезен разведке: она может сразу искать бизнес-центры без кофеен рядом, а не обследовать всё подряд.

## task: forest | Шаг 7. А если взять лес | star

Проверьте, не изменит ли решение более сложная модель. Повторите шаги 3–5 для Перми и Екатеринбурга с `RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=0)` вместо линейной регрессии (те же признаки и то же разбиение). Сохраните DataFrame `rf_risk` (индекс — эти два города, столбцы `r2` (3 знака), `mean` (до целого), `p_loss` (3 знака)) и `same_choice` — `True`, если по правилу совета (только эти два города) выбор тот же, что с линейной моделью (Пермь).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

s = pd.read_csv("sites.csv")

def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X

def boot_city(pred, fact):
    rng = np.random.default_rng(0)
    p, f = pred.values, fact.values
    out = []
    for _ in range(1000):
        i = rng.integers(0, len(f), 300)
        out.append(f[i[np.argsort(-p[i])[:40]]].sum() - 40 * 140)
    return np.array(out)

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestRegressor as _RFR
from sklearn.metrics import r2_score as _r2
s0 = _pd.read_csv('sites.csv'); r = need('rf_risk', _pd.DataFrame); want = {}
for city in ['Пермь', 'Екатеринбург']:
    part = s0[s0['city'] == city]
    X = _pd.get_dummies(part[['place', 'traffic', 'offices', 'competitors', 'rent_k', 'hours24']], dtype=int); X['traffic'] = _np.log(X['traffic'])
    a, b, c, d = _tts(X, part['profit_k'], test_size=0.25, random_state=42)
    pr = _pd.Series(_RFR(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict(b), index=d.index)
    rng = _np.random.default_rng(0); p, f = pr.values, d.values; out = []
    for _ in range(1000):
        i = rng.integers(0, len(f), 300); out.append(f[i[_np.argsort(-p[i])[:40]]].sum() - 5600)
    out = _np.array(out)
    want[city] = (round(_r2(d, pr), 3), round(out.mean()), round((out < 0).mean(), 3))
    assert city in r.index, f'Нет города {city} в rf_risk.'
    assert close(r.loc[city, 'r2'], want[city][0]), f'{city}: r2 = {r.loc[city, "r2"]}, а нужно {want[city][0]}.'
    assert close(r.loc[city, 'mean'], want[city][1], 1) and close(r.loc[city, 'p_loss'], want[city][2]), f'{city}: mean, p_loss = {r.loc[city, "mean"]}, {r.loc[city, "p_loss"]}, а нужно {want[city][1:]}.'
ok = {k: v for k, v in want.items() if v[2] <= 0.025}
ch = max(ok, key=lambda k: ok[k][1]) if ok else None
assert need('same_choice') == (ch == 'Пермь'), f'same_choice = {need("same_choice")}; по лесу проходит: {list(ok)}.'
```

### hint
Тот же цикл, что в шаге 3, но с лесом и только для двух городов; прогнозы оберните в Series с индексом `y_test`, чтобы передать в `boot_city`.

### hint
Внутри цикла по двум городам: `part = s[s["city"] == city]`, разбиение `train_test_split(prep(part), part["profit_k"], test_size=0.25, random_state=42)`, обучение леса, `pred = pd.Series(rf.predict(X_test), index=y_test.index)` и `boot_city(pred, y_test)`. Результаты соберите в словарь «город → словарь метрик» и превратите в таблицу через `pd.DataFrame(rows).T`. Правило совета: из городов с `p_loss <= 0.025` выбрать город с наибольшей средней прибылью.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

s = pd.read_csv("sites.csv")

def prep(part):
    X = pd.get_dummies(part[["place", "traffic", "offices", "competitors", "rent_k", "hours24"]], dtype=int)
    X["traffic"] = np.log(X["traffic"])
    return X

def boot_city(pred, fact):
    rng = np.random.default_rng(0)
    p, f = pred.values, fact.values
    out = []
    for _ in range(1000):
        i = rng.integers(0, len(f), 300)
        out.append(f[i[np.argsort(-p[i])[:40]]].sum() - 40 * 140)
    return np.array(out)

rows = {}
for city in ["Пермь", "Екатеринбург"]:
    part = s[s["city"] == city]
    X_train, X_test, y_train, y_test = train_test_split(prep(part), part["profit_k"], test_size=0.25, random_state=42)
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
    pred = pd.Series(rf.predict(X_test), index=y_test.index)
    b = boot_city(pred, y_test)
    rows[city] = {"r2": round(r2_score(y_test, pred), 3), "mean": round(b.mean()), "p_loss": round((b < 0).mean(), 3)}
rf_risk = pd.DataFrame(rows).T
ok = rf_risk[rf_risk["p_loss"] <= 0.025]
same_choice = (len(ok) > 0) and (ok["mean"].idxmax() == "Пермь")
```

### explain
Лес предсказывает хуже линейной регрессии в обоих городах: связь прибыли с признаками почти линейная (особенно после логарифма трафика), и лесу нечего добавить, кроме шума. Решение не меняется — Пермь. Это хороший пример к главе 6: начинайте с простой модели и усложняйте, только если сложная честно выигрывает на проверке.

::: warn Типичные ошибки проекта
- **Прибыль по прогнозу.** Сумма прогнозов выбранных мест — обещание модели, а не результат. Результат — сумма фактов.
- **Забыли стоимость автомата.** `profit_k` — прибыль до вычета 140 тыс. ₽; без вычета любой город «прибыльный».
- **Бутстрэп по всему городу вместо теста.** Модель видела обучающие места — на них её выбор выглядит лучше, чем будет в жизни.
- **Правило решения после расчёта.** «Возьмём порог 5 %, раз Екатеринбург проходит» — подгонка правила под желаемый ответ.
:::

## Итог для директора по развитию

::: figure city-rule
Правило совета в картинке: сначала отсев по риску убытка (не больше 2.5 %), потом выбор по средней прибыли среди прошедших. Числа — из шага 5.
:::

> **Рекомендация: Пермь.** 40 автоматов на местах, выбранных моделью, принесут в среднем около 1.1 млн ₽ в год; в 95 % сценариев — от 0.4 до 1.8 млн ₽; вероятность убытка — около 0.1 %.
>
> Екатеринбург в среднем выгоднее (около 1.4 млн ₽), но прибыль мест там плохо предсказуема, и вероятность убытка (около 4.6 %) выше допустимых 2.5 %. Казань не проходит ни по среднему, ни по риску.
>
> Без модели (случайные места) любой город дал бы убыток около 3 млн ₽ в год. Слабое место расчёта — оценки прибыли по похожим точкам: первые месяцы работы стоит сравнивать факт с прогнозом и пересматривать модель (урок «Модель в работе: мониторинг»).
