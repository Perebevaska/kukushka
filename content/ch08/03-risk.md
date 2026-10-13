---
title: "Риск: сколько можно потерять"
lead: "«Кампания принесёт 34 тысячи» — это одно число по одной выборке гостей при одном допущении. Бизнесу нужно знать и разброс: как плохо может пойти и с какой вероятностью мы уйдём в минус. Считаем риск бутстрэпом и симуляцией."
files: [guests_churn.csv]
recap:
  - "Прибыль на тесте — оценка по одной выборке. Бутстрэп (глава 5) показывает, как она менялась бы на других выборках гостей."
  - "Схема: много раз выбрать строки с возвращением → посчитать прибыль → смотреть среднее, 2.5-й и 97.5-й процентили, долю убыточных повторов."
  - "У результата несколько источников случайности: какие гости придут, сработает ли бонус, верно ли допущение об эффекте. Их можно добавить в симуляцию по очереди."
  - "Маленький пилот рискованнее большой кампании: разброс прибыли относительно среднего тем больше, чем меньше гостей."
  - "Решение формулируют через риск: «запускаем, если вероятность убытка меньше 2.5 %» или «если нижняя граница интервала выше нуля»."
  - "Фиксируйте генератор (`np.random.default_rng(0)`), чтобы расчёт повторялся."
---

## Одно число — это мало

### Сначала на пяти гостях

Пять гостей, и для каждого уже известен результат кампании: +400 (бонус уходящему), −200 (лишний бонус) или 0 (бонуса не было).

| номер | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| прибыль | +400 | +400 | −200 | +400 | 0 |

Итог на этих гостях: 400 + 400 − 200 + 400 + 0 = **1000 ₽**. Теперь представим другой «месяц» — вытянем 5 номеров с возвращением:

- номера 0, 0, 3, 2, 4 → 400 + 400 + 400 − 200 + 0 = **1000 ₽**;
- номера 1, 3, 3, 0, 1 → пять раз по 400 = **2000 ₽**;
- номера 2, 2, 4, 1, 2 → −200 − 200 + 0 + 400 − 200 = **−200 ₽**.

Один и тот же список гостей даёт и вдвое больше, и убыток — всё зависит от того, кто придёт. Бутстрэп делает так тысячу раз и смотрит, как распределились итоги. На пяти гостях разброс огромный; на 600 он гораздо меньше — это мы и увидим.

::: figure boot-toy5
Три «месяца» из тех же пяти гостей. Номера тянем с возвращением, поэтому один гость может попасть дважды, а другой — ни разу; итог гуляет от убытка до удвоения.
:::

### Теперь на тесте

В уроке «Из прогноза — в деньги» модель с порогом 1/3 дала 34 200 ₽ на 600 гостях теста. В следующем месяце гости будут другими: кто-то из уходящих окажется «попроще», кто-то — посложнее. Сколько мы получим тогда? Ответить помогает **бутстрэп** из главы 5: делаем вид, что тестовая выборка — это весь мир, и много раз вытаскиваем из неё новые «месяцы» с возвращением.

::: tip Аналогия
Представьте, что 600 гостей теста — 600 чеков в коробке. Вытягиваем чек, записываем, кладём обратно — и так 600 раз: получился правдоподобный «другой месяц» из тех же гостей; повторяем тысячу раз и смотрим, как гуляет итог. Где аналогия хромает: из коробки не вытянуть чек, которого в ней нет, — если в следующем месяце придут совсем другие гости, бутстрэп этого не покажет.
:::

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

send = p > 1 / 3
yv = y_test.values
rng = np.random.default_rng(0)
profits = []
for _ in range(1000):
    i = rng.integers(0, len(yv), len(yv))       # 600 номеров строк с повторами
    s, yy = send[i], yv[i]
    profits.append(400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum())
profits = np.array(profits)

print("среднее:", profits.mean().round())
print("95% интервал:", np.percentile(profits, [2.5, 97.5]))
print("доля убыточных:", (profits < 0).mean())
```

- `rng.integers(0, 600, 600)` — 600 случайных номеров строк от 0 до 599; одни строки попадут несколько раз, другие ни разу. Это и есть выборка с возвращением.
- Решение «кому бонус» (`send`) мы не пересчитываем: модель уже обучена, меняются только гости.
- `np.percentile(profits, [2.5, 97.5])` — границы, между которыми лежат 95 % значений.

Среднее около 34 000 ₽, а 95 % «месяцев» дают от 25 800 до 42 200 ₽. Убыточных повторов нет.

::: note
Почему `send[i]`, а не новый прогноз: в бутстрэпе мы проверяем устойчивость **решения** к составу гостей. Переобучать модель в каждом повторе тоже можно — тогда в разброс войдёт и случайность обучения, — но это в сотни раз дольше.
:::

::: figure boot-pairs
Строка — это пара «решение о бонусе + факт ухода» одного гостя. Один набор номеров `i` для обоих массивов тянет пары целиком; разные номера склеивают решение одного гостя с исходом другого.
:::

{{practice: resample, p-boot, boot-profit, broken-pairs}}

## Сработает ли бонус

У прибыли есть второй источник случайности: удержание. «25 %» — это средняя доля; из 113 уходящих с бонусом может остаться и 20, и 35. Каждый уходящий с бонусом — как монетка с вероятностью 0.25, а число удержанных подчиняется **биномиальному распределению** (глава 5). Добавим его в симуляцию: теперь считаем не ожидаемую, а «настоящую» прибыль — 2400 ₽ за каждого удержанного минус 200 ₽ за каждый бонус.

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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values

rng = np.random.default_rng(2)
profits = []
for _ in range(2000):
    i = rng.integers(0, len(yv), len(yv))
    s, yy = send[i], yv[i]
    tp = (s & (yy == 1)).sum()
    kept = rng.binomial(tp, 0.25)                # сколько из tp уходящих удержалось
    profits.append(2400 * kept - 200 * s.sum())
profits = np.array(profits)
print("среднее:", profits.mean().round())
print("95% интервал:", np.percentile(profits, [2.5, 97.5]))
print("доля убыточных:", (profits < 0).mean())
```

**Что здесь происходит:**

- Первые строки цикла — тот же бутстрэп: новый «месяц» гостей.
- `tp` — сколько уходящих получили бонус в этом «месяце».
- `rng.binomial(tp, 0.25)` — бросаем `tp` монеток с вероятностью 0.25: сколько уходящих бонус действительно удержал.
- `2400 * kept - 200 * s.sum()` — реальная прибыль: маржа удержанных минус все бонусы. Это уже не «ожидаемые» 400 за TP, а конкретный исход.

Среднее почти то же, а интервал стал втрое шире: примерно от 12 до 59 тыс. ₽. Случайность удержания добавляет риска больше, чем состав гостей: каждый удержанный стоит 2400 ₽, и разница в десяток удержанных — это 24 тыс. ₽.

Прикинем руками. Стандартное отклонение числа удержанных из 113 при p = 0.25 — √(113 × 0.25 × 0.75) ≈ **4.6** человека. В рублях — 4.6 × 2400 ≈ **11 000 ₽**, а 95 % интервал — примерно ± 2 таких отклонения, ± 22 000 ₽ вокруг 34 000. Это и есть «от 12 до 59 тыс.» из симуляции: формула и бутстрэп согласны. Вероятность убытка всё ещё близка к нулю.

::: predict
```python static
import numpy as np
rng = np.random.default_rng(0)
kept = rng.binomial(100, 0.25, size=10_000)
print(round(kept.mean()))
```

- `100`
- [x] `25`
- `0`

Почему: среднее биномиального распределения — n × p = 100 × 0.25. Отдельные значения разбросаны вокруг 25, а среднее по 10 000 повторов почти точно равно 25.
:::

::: quiz
Когда в симуляцию добавили случайность удержания, среднее почти не изменилось, а интервал стал втрое шире. Почему?

- [x] К случайности состава гостей добавился второй источник — сколько уходящих бонус удержит, а каждый удержанный стоит 2400 ₽
  > Разбросы двух источников накладываются друг на друга. Удержание при этом в среднем то же — 25 %, — поэтому центр почти не сдвинулся.
- [ ] Повторов стало 2000 вместо 1000 — больше повторов, шире интервал
  > Число повторов уточняет оценку интервала, но не расширяет его: ширину задаёт разброс исходов, а не число симуляций.
- [ ] Поменялся seed генератора
  > Другой seed даёт немного другие цифры, но не утроение ширины.
- [ ] Биномиальное распределение занижает удержание
  > Его среднее — n × p, ровно 25 % от уходящих с бонусом. Оно не смещает прибыль, а добавляет разброс.
:::

{{practice: binom, binom-sd}}

## Маленький пилот рискованнее

Перед большой кампанией бизнес часто делает пилот — например, в одной кофейне на 100 гостей. Кажется, что это безопаснее. Но доля шума в маленьком пилоте гораздо больше:

| сколько гостей в кампании | средняя прибыль | 95 % интервал | полуширина интервала / среднее | вероятность убытка |
|---|---|---|---|---|
| 100 | ≈ 5 800 ₽ | от −3 000 до 16 000 ₽ | ≈ 1.6 | ≈ 11 % |
| 600 | ≈ 34 000 ₽ | от 12 000 до 59 000 ₽ | ≈ 0.7 | ≈ 0 % |

Ожидаемая прибыль растёт пропорционально числу гостей, а разброс — медленнее (примерно как корень из числа гостей, вспомните SE из главы 5). Поэтому у маленького пилота каждый девятый исход — убыток. Это не значит, что пилот плохой; это значит, что по одному маленькому пилоту нельзя судить, работает ли кампания.

::: quiz
Пилот на 20 гостях и раскатка на 2000 дают одинаковую ожидаемую прибыль на гостя. Чем они различаются?

- [x] У пилота разброс результата намного больше: на 20 гостях легко уйти в минус просто случайно
  > Разброс суммы относительно размера падает с ростом выборки. Поэтому по маленькому пилоту выводы делают осторожно.
- [ ] Ничем: ожидание одинаковое
  > Ожидание то же, а риск — разный.
- [ ] Пилот всегда прибыльнее
  > Нет причин для этого: случайность может сработать в любую сторону.
- [ ] Раскатка рискованнее: больше денег
  > В рублях — возможно, но вероятность уйти в минус у большой раскатки меньше.
:::

{{practice: pilot}}

## Если допущение неточно

Самое шаткое в расчёте — 25 % удержания. Если маркетинг честно говорит «где-то от 15 до 35 %», добавим и это: в каждом повторе берём случайное удержание из этого диапазона (`rng.uniform(0.15, 0.35)`). Интервал расширяется до «от 0 до 71 тыс. ₽», а вероятность убытка вырастает примерно до 2 %. Модель та же, гости те же — риск вырос только из-за того, что мы честно признали незнание.

::: figure risk-layers
Сводка урока: каждый новый источник случайности расширяет интервал прибыли, хотя среднее почти не меняется. Пилот на 100 гостях рискованнее раскатки на 600 — каждый девятый его исход убыточен.
:::

::: tip
Решение формулируют заранее, как в A/B-тесте: например, «запускаем, если вероятность убытка меньше 2.5 %». Тогда спор идёт не о том, нравится ли нам число, а о том, выполнено ли правило.
:::

{{practice: unsure-retain, break-retain}}

## Риск разных стратегий

Порог тоже влияет на риск. Сравним бутстрэпом (только состав гостей, ожидаемая прибыль) четыре порога:

| порог | средняя прибыль | 5-й процентиль |
|---|---|---|
| 0.20 | ≈ 27 400 ₽ | ≈ 19 600 ₽ |
| 0.33 | ≈ 34 000 ₽ | ≈ 27 200 ₽ |
| 0.50 | ≈ 31 100 ₽ | ≈ 25 400 ₽ |
| 0.70 | ≈ 17 200 ₽ | ≈ 13 200 ₽ |

**5-й процентиль** — сумма, ниже которой прибыль падает только в 5 % случаев («плохой, но не катастрофический месяц»). Здесь порог 1/3 выигрывает и по среднему, и по плохому сценарию. Так бывает не всегда: иногда стратегия с чуть меньшим средним гораздо надёжнее — и осторожный бизнес выберет её.

::: predict
```python static
import numpy as np
send = np.array([True, True, False, True])
y = np.array([1, 0, 0, 1])
i = np.array([0, 0, 3, 1])
print((send[i] & (y[i] == 1)).sum())
```

- `2`
- [x] `3`
- `1`

Почему: строки 0, 0, 3, 1 — гость 0 попал дважды. У гостей 0 и 3 бонус и уход, у гостя 1 бонус без ухода. TP = 1 + 1 + 1 + 0 = 3. Индекс `i` один для обоих массивов — пары «решение — факт» сохраняются.
:::

::: warn Типичные ошибки
- **Генератор внутри цикла.** `rng = np.random.default_rng(0)` в каждом повторе даёт одну и ту же выборку тысячу раз — интервал нулевой ширины.
- **Разные номера для решения и факта.** `send[i]` и `yv[j]` с разными `i`, `j` рвут пары «гость — его исход»: модель превращается в случайную раздачу (в задачах увидите, во что это обходится).
- **Интервал по среднему вместо процентилей.** «Среднее ± 2 × SE» годится для среднего, а вопрос бизнеса — «как плохо может быть в одном месяце», это процентили распределения исходов.
- **Решение по одной симуляции без seed.** Без фиксированного генератора цифры в отчёте не воспроизвести.
:::

{{practice: compare-risk}}

## Практика

## task: resample | Выборка с возвращением | warmup

Сгенерируйте генератором `np.random.default_rng(0)` 10 номеров строк от 0 до 9 (`rng.integers(0, 10, 10)`). Сохраните их в `idx`, а в `n_unique` — сколько разных номеров попало в выборку.

### starter
```python
import numpy as np
rng = np.random.default_rng(0)

```

### check
```python
import numpy as _np
w = _np.random.default_rng(0).integers(0, 10, 10)
assert list(need('idx')) == list(w), f'idx = {list(need("idx"))}. Используйте rng.integers(0, 10, 10) один раз сразу после создания генератора.'
assert need('n_unique') == len(set(w.tolist())), f'n_unique = {need("n_unique")}, а нужно {len(set(w.tolist()))}.'
```

### hint
`idx = rng.integers(0, 10, 10)` — сразу после создания генератора, без других вызовов между ними.

### hint
Число разных значений: `len(np.unique(idx))` или `len(set(idx))`.

### solution
```python
import numpy as np
rng = np.random.default_rng(0)
idx = rng.integers(0, 10, 10)
n_unique = len(np.unique(idx))
```

### explain
Обычно в выборку с возвращением попадает около 63 % разных строк — как и в бутстрэпе случайного леса (глава 6).

## task: p-boot | Цикл бутстрэпа | warmup

Соберите бутстрэп средней прибыли на гостя по массиву `gain` (прибыль каждого гостя).

### parsons
```python
import numpy as np
gain = np.array([400, -200, 0, 400, -200, 0, 0, 400])
rng = np.random.default_rng(0)
means = []
for _ in range(1000):
    i = rng.integers(0, len(gain), len(gain))
    means.append(gain[i].mean())
print(round(float(np.mean(means))))
```

### check
```python
import numpy as _np
g = _np.array([400, -200, 0, 400, -200, 0, 0, 400]); r = _np.random.default_rng(0)
m = [g[r.integers(0, 8, 8)].mean() for _ in range(1000)]
assert _lines == [str(round(float(_np.mean(m))))], f'Сейчас: {_lines}. Генератор — до цикла, выборка — внутри цикла.'
```

### hint
Генератор создаётся один раз до цикла, иначе все повторы будут одинаковыми.

### hint
Внутри цикла две строки: номера `i`, затем `means.append(...)`. `print` — после цикла, без отступа.

## task: binom | Сколько удержится | warmup

Бонус получили 120 уходящих гостей, каждый удерживается с вероятностью 0.25. Сгенерируйте 10 000 повторов числа удержанных: `rng.binomial(120, 0.25, size=10_000)` с `rng = np.random.default_rng(1)`. Сохраните в `p_low` долю повторов, где удержалось меньше 20 гостей (3 знака).

### starter
```python
import numpy as np
rng = np.random.default_rng(1)

```

### check
```python
import numpy as _np
k = _np.random.default_rng(1).binomial(120, 0.25, size=10_000)
w = round((k < 20).mean(), 3)
assert close(need('p_low'), w), f'p_low = {need("p_low")}, а нужно {w}: доля повторов с числом удержанных < 20.'
```

### hint
В среднем удержится 120 × 0.25 = 30 гостей; «меньше 20» — заметно хуже ожиданий, такая доля будет небольшой.

### hint
`kept = rng.binomial(120, 0.25, size=10_000)`, затем `(kept < 20).mean()`.

### solution
```python
import numpy as np
rng = np.random.default_rng(1)
kept = rng.binomial(120, 0.25, size=10_000)
p_low = round((kept < 20).mean(), 3)
```

## task: boot-profit | Интервал прибыли | base

Бутстрэпом (1000 повторов, `rng = np.random.default_rng(0)`, номера строк `rng.integers(0, len(yv), len(yv))`) оцените ожидаемую прибыль стратегии «бонус при прогнозе > 0.5»: +400 ₽ за уходящего, −200 ₽ за лишний бонус. Сохраните массив прибылей `profits`, границы 95 % интервала `low` и `high` (`np.percentile`, округлите до целого) и долю убыточных повторов `p_loss`.

### setup
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
send = model.predict_proba(X_test)[:, 1] > 0.5
yv = y_test.values
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, send, yv

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
s0 = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1] > 0.5
yv = d.values; r = _np.random.default_rng(0); out = []
for _ in range(1000):
    i = r.integers(0, len(yv), len(yv)); s, yy = s0[i], yv[i]
    out.append(400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum())
out = _np.array(out)
pr = _np.asarray(need('profits'))
assert len(pr) == 1000, f'В profits {len(pr)} значений, нужно 1000.'
assert close(float(_np.mean(pr)), float(out.mean()), 1), 'Среднее profits не совпадает с ожидаемым. Создайте генератор один раз перед циклом и берите номера rng.integers(0, len(yv), len(yv)).'
lo, hi = _np.percentile(out, [2.5, 97.5]).round()
assert close(need('low'), lo, 1) and close(need('high'), hi, 1), f'low, high = {need("low")}, {need("high")}, а нужно {lo}, {hi}.'
assert close(need('p_loss'), (out < 0).mean()), f'p_loss = {need("p_loss")}.'
```

### hint
Скопируйте цикл из теории — порог уже задан в `send`.

### hint
Границы: `low, high = np.percentile(profits, [2.5, 97.5]).round()`, доля убыточных — `(profits < 0).mean()`.

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
send = model.predict_proba(X_test)[:, 1] > 0.5
yv = y_test.values

rng = np.random.default_rng(0)
profits = []
for _ in range(1000):
    i = rng.integers(0, len(yv), len(yv))
    s, yy = send[i], yv[i]
    profits.append(400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum())
profits = np.array(profits)
low, high = np.percentile(profits, [2.5, 97.5]).round()
p_loss = (profits < 0).mean()
```

### explain
Порог 0.5: в среднем 31 100 ₽, 95 % «месяцев» — от 24 400 до 38 000 ₽, убыточных нет. У порога 1/3 интервал 25 800–42 200: он выше целиком, хоть и чуть шире. Сравнивайте стратегии не только по среднему, но и по нижней границе — здесь 1/3 выигрывает по обоим.

## task: broken-pairs | Разорванные пары | base

Повторите бутстрэп прибыли для порога 1/3 (1000 повторов, `rng = np.random.default_rng(0)`) двумя способами. Правильный: один набор номеров `i` для `send` и `yv`. Ошибочный: `i` для `send` и отдельный `j = rng.integers(...)` для `yv` (в ошибочном цикле генерируйте сначала `i`, потом `j`; для каждого способа — свой новый генератор с seed 0). Сохраните средние прибыли `mean_ok` и `mean_broken` (округлите до целого) и `p_loss_broken` — долю убыточных повторов в ошибочном способе.

### setup
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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values
def profit(s, yy):
    return 400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum()
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, send, yv

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
s0 = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1] > 1 / 3
yv = d.values
def _p(s, yy): return 400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum()
r = _np.random.default_rng(0); ok = []
for _ in range(1000):
    i = r.integers(0, 600, 600); ok.append(_p(s0[i], yv[i]))
r = _np.random.default_rng(0); br = []
for _ in range(1000):
    i = r.integers(0, 600, 600); j = r.integers(0, 600, 600); br.append(_p(s0[i], yv[j]))
ok, br = _np.array(ok), _np.array(br)
assert close(need('mean_ok'), round(ok.mean()), 1), f'mean_ok = {need("mean_ok")}, а нужно {round(ok.mean())}.'
assert close(need('mean_broken'), round(br.mean()), 1), f'mean_broken = {need("mean_broken")}, а нужно {round(br.mean())}. Сначала i, потом j, новый генератор с seed 0.'
assert close(need('p_loss_broken'), (br < 0).mean(), 0.002), f'p_loss_broken = {need("p_loss_broken")}.'
```

### hint
Два цикла по 1000 повторов. Перед каждым — `rng = np.random.default_rng(0)`. В правильном: `profit(send[i], yv[i])`.

### hint
В ошибочном: `i = rng.integers(0, len(yv), len(yv))`, затем `j = rng.integers(0, len(yv), len(yv))`, и `profit(send[i], yv[j])`.

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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values

def profit(s, yy):
    return 400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum()

rng = np.random.default_rng(0)
ok = []
for _ in range(1000):
    i = rng.integers(0, len(yv), len(yv))
    ok.append(profit(send[i], yv[i]))

rng = np.random.default_rng(0)
broken = []
for _ in range(1000):
    i = rng.integers(0, len(yv), len(yv))
    j = rng.integers(0, len(yv), len(yv))
    broken.append(profit(send[i], yv[j]))

mean_ok = round(np.mean(ok))
mean_broken = round(np.mean(broken))
p_loss_broken = np.mean(np.array(broken) < 0)
```

### explain
Правильный бутстрэп — около 34 000 ₽, ошибочный — около −11 000 ₽ и убыток почти в 100 % повторов. Разорвав пары, мы отправили бонусы 168 случайным гостям: из них уходит 22 %, и кампания убыточна, как в прошлом уроке. Модель тут ни при чём — сломан расчёт. Если бутстрэп выдаёт результат, противоречащий исходной цифре, первым делом проверьте, что строки берутся одним индексом.

## task: pilot | Риск пилота | base

Оцените риск пилота на 100 гостях: в каждом из 2000 повторов выберите 100 строк теста с возвращением (`rng.integers(0, len(yv), 100)`), посчитайте число уходящих с бонусом `tp`, число удержанных `rng.binomial(tp, 0.25)` и прибыль 2400 × удержанные − 200 × бонусы. Генератор — `np.random.default_rng(3)`, бонус — при прогнозе > 1/3. Проверка сравнивает с допуском, поэтому порядок вызовов генератора не важен; чтобы совпасть с разбором до рубля, вызывайте сначала `integers`, потом `binomial`. Сохраните `mean_pilot` (среднее, до целого) и `p_loss` (доля повторов с прибылью < 0, 3 знака).

### setup
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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, send, yv

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
s0 = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1] > 1 / 3
yv = d.values; r = _np.random.default_rng(3); out = []
for _ in range(2000):
    i = r.integers(0, len(yv), 100); s, yy = s0[i], yv[i]
    tp = (s & (yy == 1)).sum()
    out.append(2400 * r.binomial(tp, 0.25) - 200 * s.sum())
out = _np.array(out)
assert abs(need('mean_pilot') - out.mean()) <= 400, f'mean_pilot = {need("mean_pilot")}, а ожидается около {round(out.mean())} (с другим порядком вызовов генератора — в пределах ±400 ₽). Проверьте: 100 строк с возвращением, удержание 25 %, прибыль 2400 × удержанные − 200 × бонусы.'
assert abs(need('p_loss') - (out < 0).mean()) <= 0.02, f'p_loss = {need("p_loss")}, а ожидается около {round((out < 0).mean(), 3)}: доля повторов с прибылью меньше нуля.'
```

### hint
Как во втором примере теории, только `rng.integers(0, len(yv), 100)` и 2000 повторов.

### hint
Внутри цикла: `i = rng.integers(0, len(yv), 100)`, `s, yy = send[i], yv[i]`, `tp = (s & (yy == 1)).sum()`, `kept = rng.binomial(tp, 0.25)`, прибыль `2400 * kept - 200 * s.sum()`. Порядок вызовов генератора — как здесь.

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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values

rng = np.random.default_rng(3)
profits = []
for _ in range(2000):
    i = rng.integers(0, len(yv), 100)
    s, yy = send[i], yv[i]
    tp = (s & (yy == 1)).sum()
    profits.append(2400 * rng.binomial(tp, 0.25) - 200 * s.sum())
profits = np.array(profits)
mean_pilot = round(profits.mean())
p_loss = round((profits < 0).mean(), 3)
```

### explain
Около 11 % пилотов на 100 гостях уходят в минус, хотя кампания в целом выгодна. Если пилот окажется убыточным, это ещё не доказательство, что идея плохая: нужно смотреть, вписывается ли результат в ожидаемый разброс.

## task: binom-sd | Формула против симуляции | base

Проверьте прикидку из теории. Сгенерируйте 10 000 повторов числа удержанных из 113 уходящих (`rng = np.random.default_rng(3)`, `rng.binomial(113, 0.25, size=10_000)`). Сохраните `sd_sim` — стандартное отклонение симуляции, `sd_formula` — √(n × p × (1 − p)) (оба — 2 знака), и `sd_rub` — разброс прибыли в рублях по формуле (`sd_formula` × 2400, округлите до целого).

### starter
```python
import numpy as np
rng = np.random.default_rng(3)
n, p = 113, 0.25

```

### check
```python
import numpy as _np
k = _np.random.default_rng(3).binomial(113, 0.25, size=10_000)
f = (113 * 0.25 * 0.75) ** 0.5
assert close(need('sd_sim'), round(k.std(), 2), 0.011), f'sd_sim = {need("sd_sim")}, а нужно {round(k.std(), 2)}.'
assert close(need('sd_formula'), round(f, 2), 0.011), f'sd_formula = {need("sd_formula")}, а нужно {round(f, 2)}.'
assert close(need('sd_rub'), round(round(f, 2) * 2400), 30), f'sd_rub = {need("sd_rub")}.'
```

### hint
`kept = rng.binomial(n, p, size=10_000)`, `sd_sim = round(kept.std(), 2)`.

### hint
`sd_formula = round(np.sqrt(n * p * (1 - p)), 2)`, `sd_rub = round(sd_formula * 2400)`.

### solution
```python
import numpy as np
rng = np.random.default_rng(3)
n, p = 113, 0.25

kept = rng.binomial(n, p, size=10_000)
sd_sim = round(kept.std(), 2)
sd_formula = round(np.sqrt(n * p * (1 - p)), 2)
sd_rub = round(sd_formula * 2400)
```

### explain
Симуляция даёт 4.66, формула — 4.60: совпадение с точностью до шума симуляции. В рублях это около 11 000 ₽ одного стандартного отклонения. Формула удобна для быстрой прикидки на встрече, симуляция — когда источников случайности несколько и формулы для них уже не сложить.

## task: compare-risk | Порог по плохому сценарию | base

Сравните бутстрэпом пороги 0.2, 0.35 и 0.5 (ожидаемая прибыль +400 / −200, 1000 повторов). Для каждого порога создавайте **новый** генератор `np.random.default_rng(0)`, чтобы все пороги проверялись на одних и тех же «месяцах». Сохраните DataFrame `risk` со столбцами `threshold`, `mean`, `p5` (среднее и 5-й процентиль, до целого) и в `safest` — порог с наибольшим `p5`.

### setup
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
yv = y_test.values
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, p, yv

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
yv = d.values; want = []
for t in (0.2, 0.35, 0.5):
    r = _np.random.default_rng(0); out = []
    for _ in range(1000):
        i = r.integers(0, len(yv), len(yv)); s, yy = (pp > t)[i], yv[i]
        out.append(400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum())
    want.append((t, round(_np.mean(out)), round(_np.percentile(out, 5))))
t = need('risk', _pd.DataFrame)
assert list(t['threshold']) == [0.2, 0.35, 0.5], f'Столбец threshold: {list(t["threshold"])}.'
for (th, m, q), (_, row) in zip(want, t.iterrows()):
    assert close(row['mean'], m, 1) and close(row['p5'], q, 1), f'Порог {th}: mean, p5 = {row["mean"]}, {row["p5"]}, а нужно {m}, {q}. Новый генератор для каждого порога.'
best = max(want, key=lambda w: w[2])[0]
assert close(need('safest'), best), f'safest = {need("safest")}, а нужно {best}.'
```

### hint
Оберните бутстрэп в функцию `boot(send)`, внутри которой создаётся генератор, и вызовите её для трёх масок.

### hint
Для каждого порога: `pr = boot(p > t)`, строка `{"threshold": t, "mean": round(pr.mean()), "p5": round(np.percentile(pr, 5))}`. `safest = risk.loc[risk["p5"].idxmax(), "threshold"]`.

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
yv = y_test.values

def boot(send):
    rng = np.random.default_rng(0)
    out = []
    for _ in range(1000):
        i = rng.integers(0, len(yv), len(yv))
        s, yy = send[i], yv[i]
        out.append(400 * (s & (yy == 1)).sum() - 200 * (s & (yy == 0)).sum())
    return np.array(out)

rows = []
for t in (0.2, 0.35, 0.5):
    b = boot(p > t)
    rows.append({"threshold": t, "mean": round(b.mean()), "p5": round(np.percentile(b, 5))})
risk = pd.DataFrame(rows)
safest = risk.loc[risk["p5"].idxmax(), "threshold"]
```

### explain
Один и тот же генератор для всех стратегий — приём «общих случайных чисел»: стратегии сравниваются на одинаковых «месяцах», и разница между ними меньше зашумлена.

## task: unsure-retain | Неточное допущение | plus

Добавьте неуверенность в эффекте: в каждом из 2000 повторов сначала берите удержание `r = rng.uniform(0.15, 0.35)`, затем строки теста с возвращением (`rng.integers(0, len(yv), len(yv))`), затем удержанных `rng.binomial(tp, r)`. Генератор — `np.random.default_rng(4)` (порядок вызовов не важен — проверка с допуском), бонус при прогнозе > 1/3, прибыль 2400 × удержанные − 200 × бонусы. Сохраните `p_loss` (3 знака) и `launch` — `True`, если вероятность убытка меньше 2.5 %.

### setup
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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, send, yv

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
s0 = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1] > 1 / 3
yv = d.values; rg = _np.random.default_rng(4); out = []
for _ in range(2000):
    r = rg.uniform(0.15, 0.35); i = rg.integers(0, len(yv), len(yv)); s, yy = s0[i], yv[i]
    out.append(2400 * rg.binomial((s & (yy == 1)).sum(), r) - 200 * s.sum())
pl = round((_np.array(out) < 0).mean(), 3)
assert abs(need('p_loss') - pl) <= 0.01, f'p_loss = {need("p_loss")}, а ожидается около {pl} (±0.01 — допуск на порядок вызовов генератора). Удержание — своё в каждом повторе: uniform(0.15, 0.35).'
assert need('launch') == (need('p_loss') < 0.025), f'launch = {need("launch")} при вашем p_loss = {need("p_loss")}: правило — запускать, если вероятность убытка меньше 2.5 %.'
```

### hint
Порядок вызовов генератора важен: от него зависят случайные числа. В каждом повторе — `uniform`, потом `integers`, потом `binomial`.

### hint
`launch = bool(p_loss < 0.025)` — сравнивайте неокруглённую или округлённую долю, результат тот же.

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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values

rng = np.random.default_rng(4)
profits = []
for _ in range(2000):
    r = rng.uniform(0.15, 0.35)
    i = rng.integers(0, len(yv), len(yv))
    s, yy = send[i], yv[i]
    tp = (s & (yy == 1)).sum()
    profits.append(2400 * rng.binomial(tp, r) - 200 * s.sum())
p_loss = round((np.array(profits) < 0).mean(), 3)
launch = bool(p_loss < 0.025)
```

### explain
Вероятность убытка около 2 % — на грани правила 2.5 %. Небольшое ухудшение допущений (например, удержание от 10 %) перевело бы кампанию в «не запускать». Самый дешёвый способ снизить риск — не другая модель, а A/B-тест, который сузит диапазон удержания.

## task: break-retain | При каком удержании риск приемлем | star

Найдите наименьшее удержание из `np.arange(0.10, 0.31, 0.02).round(2)`, при котором вероятность убытка кампании (порог 1/3, 1000 повторов: строки с возвращением + `rng.binomial(tp, r)`, прибыль 2400 × удержанные − 200 × бонусы) меньше 2.5 %. Для каждого значения удержания создавайте новый генератор `np.random.default_rng(5)`. Сохраните найденное значение в `min_retain`.

### setup
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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# готово, как в теории: g, y, X, X_train, X_test, y_train, y_test, model, send, yv

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
s0 = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c).predict_proba(b)[:, 1] > 1 / 3
yv = d.values; ans = None
for r in _np.arange(0.10, 0.31, 0.02).round(2):
    rg = _np.random.default_rng(5); out = []
    for _ in range(1000):
        i = rg.integers(0, len(yv), len(yv)); s, yy = s0[i], yv[i]
        out.append(2400 * rg.binomial((s & (yy == 1)).sum(), r) - 200 * s.sum())
    if (_np.array(out) < 0).mean() < 0.025:
        ans = r; break
assert abs(need('min_retain') - ans) <= 0.021, f'min_retain = {need("min_retain")}, а ожидается {ans} (±один шаг сетки — допуск на случайность повторов).'
```

### hint
Внешний цикл по удержанию, внутри — бутстрэп; как только доля убытков меньше 0.025, сохраните значение и выйдите из цикла (`break`).

### hint
Для скорости можно не считать дальше после первого подходящего значения.

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
send = model.predict_proba(X_test)[:, 1] > 1 / 3
yv = y_test.values

min_retain = None
for r in np.arange(0.10, 0.31, 0.02).round(2):
    rng = np.random.default_rng(5)
    profits = []
    for _ in range(1000):
        i = rng.integers(0, len(yv), len(yv))
        s, yy = send[i], yv[i]
        tp = (s & (yy == 1)).sum()
        profits.append(2400 * rng.binomial(tp, r) - 200 * s.sum())
    if (np.array(profits) < 0).mean() < 0.025:
        min_retain = r
        break
```

### explain
Это «точка безубыточности по риску»: если эксперимент покажет удержание ниже найденного значения, кампанию на 600 гостей запускать нельзя по правилу 2.5 %. Такую цифру удобно отдать маркетингу как цель для A/B-теста. А теперь сравните с пилотом из урока «Пилот и P&L»: он показал удержание около 20 % — ровно на найденной границе. Кампания по пилоту проходит правило 2.5 % впритык, и это честный аргумент для обсуждения с финансистом.
