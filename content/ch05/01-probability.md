---
title: "Вероятность: частота и симуляция"
lead: "Статистика начинается с вопроса «а не случайно ли это?». Чтобы на него отвечать, нужен язык вероятностей. Без формул-заклинаний: вероятность — это доля в длинной серии, её можно посчитать по данным или проверить симуляцией — заставить компьютер «прожить» ситуацию тысячи раз."
files: [deliveries.csv]
recap:
  - "Вероятность события — доля случаев, в которых оно происходит, если повторять опыт много раз. По данным: `(условие).mean()`."
  - "Закон больших чисел: чем больше опытов, тем ближе наблюдаемая доля к настоящей вероятности. На малых выборках доли «прыгают»."
  - "Условная вероятность P(A | B) — доля A среди строк, где выполнено B: `df[B][A].mean()`. Это и есть срез."
  - "События независимы, если P(A и B) = P(A) × P(B). Иначе они связаны."
  - "«Хотя бы один раз из n»: 1 − (1 − p)ⁿ."
  - "Симуляция: `rng = np.random.default_rng(42)`; `rng.random(n) < p` — n опытов с вероятностью успеха p. `seed` (42) делает случайность воспроизводимой."
---

## Зачем аналитику вероятность

В главе 4 мы нашли, что в снег опаздывают чаще: 34 % против 23 % в остальные дни. А если бы разница была 25 % против 23 %? Или 34 % против 23 %, но снежных доставок было бы всего десять? Где граница между «закономерность» и «так легли карты»?

Ответ дают вероятность и статистика. Эта глава — про то, как отличать настоящие эффекты от случайного шума. А начнём с основы — что такое вероятность.

## Вероятность — это доля

Вероятность события — доля случаев, в которых оно происходит, если повторять одно и то же много раз. Монетка: из тысячи бросков орёл выпадет примерно 500 раз — вероятность 0.5.

В данных вероятность события оценивают долей строк, где оно произошло, — как мы делали в главе 4:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
p_late = ok["late"].mean()
print(f"P(опоздание) ≈ {p_late:.3f}")
```

«≈» — потому что это **оценка** по 1 841 доставке. Настоящая вероятность — та, что получилась бы на бесконечном числе доставок в тех же условиях, — нам неизвестна. Насколько оценка может ошибаться — тема уроков «Выборки и центральная предельная теорема» и «Доверительные интервалы».

Вероятность — число от 0 (никогда) до 1 (всегда). Вероятность противоположного события — $1 - p$: если опаздывает 24 %, то вовремя — 76 %.

{{practice: p-late}}

## Симуляция: проживаем случайность

**Симуляция** — способ получить ответ, не выводя формулу: заставить компьютер повторить случайный опыт много раз и посчитать доли. Генератор случайных чисел — в библиотеке **numpy** (на ней построен pandas):

```python
import numpy as np
rng = np.random.default_rng(42)
x = rng.random(5)
print(x)
print(x < 0.24)
```

- `default_rng(42)` — генератор; число 42 — **seed** (зерно). С тем же seed вы получите те же «случайные» числа — результат воспроизводим;
- `rng.random(n)` — n случайных чисел от 0 до 1, все значения равновероятны;
- `x < 0.24` — каждое число меньше 0.24 с вероятностью 0.24. Это модель «доставка опоздала» с p = 0.24.

Смоделируем 10 000 доставок и посмотрим на долю опозданий:

```python
import numpy as np
rng = np.random.default_rng(1)
late = rng.random(10_000) < 0.24
print(late.mean())
```

{{practice: p-sim, shift}}

## Закон больших чисел

Доля в симуляции близка к 0.24, но не равна ему. Чем больше опытов, тем ближе. Посмотрим, как меняется доля опозданий по мере роста числа доставок:

```python
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
late = rng.random(2000) < 0.24
running = late.cumsum() / np.arange(1, 2001)

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(running)
ax.axhline(0.24, color="tab:red", linestyle="--")
ax.set_xlabel("доставок")
ax.set_ylabel("доля опозданий")
ax.set_title("Закон больших чисел")
```

`cumsum()` — накопленное число опозданий, `np.arange(1, 2001)` — номера доставок 1, 2, …, 2000. Их отношение — доля опозданий после каждой доставки.

Первые десятки доставок дают доли от 0 до 0.5 — чистый шум. К тысяче доля успокаивается около 0.24. Это **закон больших чисел**, и он объясняет главное правило аналитика: **доля по маленькой группе ненадёжна** (урок «Срезы: сравниваем группы» главы 4).

::: tip Аналогия
Вспомните рейтинг новой кофейни в картах. По первым трём отзывам он может быть и 2, и 5: одному гостю не понравилась пенка — и средняя оценка рухнула. После сотен отзывов рейтинг перестаёт скакать и показывает, какая кофейня на самом деле. Только закон больших чисел предполагает, что условия не меняются, а настоящая кофейня со временем может стать лучше или хуже.
:::

::: predict
```python static
import numpy as np
rng = np.random.default_rng(0)
small = (rng.random(10) < 0.5).mean()
big = (rng.random(100_000) < 0.5).mean()
print(abs(big - 0.5) < 0.01)
```

- [x] `True`
- `False`
- `Ошибка ValueError`

Почему: на 100 000 опытов доля почти наверняка в пределах 0.01 от 0.5. На 10 опытах так не повезло бы: доля могла оказаться и 0.3, и 0.7.
:::

{{practice: running, small-groups}}

## Условная вероятность — это срез

Вероятность опоздания **при условии**, что идёт снег, пишут $P(\text{опоздание} \mid \text{снег})$. Посчитать её — значит взять только снежные доставки и найти долю опозданий среди них. Это ровно срез из урока «Срезы: сравниваем группы» главы 4:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
snow = ok["weather"] == "снег"
print("P(опоздание)        =", round(ok["late"].mean(), 3))
print("P(опоздание | снег) =", round(ok.loc[snow, "late"].mean(), 3))
print("P(снег | опоздание) =", round(ok.loc[ok["late"], "weather"].eq("снег").mean(), 3))
```

Обратите внимание: $P(\text{опоздание} \mid \text{снег})$ и $P(\text{снег} \mid \text{опоздание})$ — **разные** вещи. Первое — «как часто опаздываем в снег», второе — «какая доля опозданий пришлась на снег». Их часто путают в отчётах.

### Разберём вместе: два вопроса к одной таблице

Сведём доставки в таблицу «пеший ли курьер × опоздала ли»:

| | опоздала | вовремя | всего |
|---|---|---|---|
| **пеший** | 298 | 105 | 403 |
| **не пеший** | 143 | 1295 | 1438 |
| **всего** | 441 | 1400 | 1841 |

1. **$P(\text{опоздание} \mid \text{пеший})$** — смотрим в строку «пеший»: 298 / 403 ≈ **0.74**. «Пешие опаздывают в трёх случаях из четырёх».
2. **$P(\text{пеший} \mid \text{опоздание})$** — смотрим в столбец «опоздала»: 298 / 441 ≈ **0.68**. «Две трети всех опозданий — пешие».
3. **$P(\text{опоздание})$** — 441 / 1841 ≈ **0.24**, **$P(\text{пеший})$** — 403 / 1841 ≈ **0.22**.

Числитель у первых двух один и тот же — 298, — а знаменатели разные: строка или столбец. Отсюда правило: прежде чем писать «вероятность», скажите, **среди кого** считаете долю.

::: figure cond-row-col
Одна и та же таблица, два вопроса. Слева делим на строку «пеший» (403 доставки) — получаем риск пешего курьера. Справа делим на столбец «опоздала» (441 доставка) — получаем долю пеших среди опозданий.
:::

Что получилось: ответы на вопросы «насколько рискован пеший курьер» (0.74) и «откуда берутся опоздания» (0.68) — разные числа и разные решения. Первое — про выбор курьера для конкретного заказа, второе — про то, где искать резерв: на пеших приходится две трети опозданий, там и искать причину.

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = pd.crosstab(ok["courier"] == "пеший", ok["late"], margins=True)
print(t)
print(round(t.loc[True, True] / t.loc[True, "All"], 3), round(t.loc[True, True] / t.loc["All", True], 3))
```

::: quiz
Среди опоздавших доставок 13 % пришлись на снег. Значит ли это, что в снег опаздывает 13 % доставок?

- [x] Нет: это P(снег | опоздание), а вопрос про P(опоздание | снег) — другой срез и другой знаменатель
  > Первое делят на число опозданий, второе — на число снежных доставок. Цифры могут сильно различаться.
- [ ] Да, это одно и то же
  > Условная вероятность несимметрична: «среди опоздавших» и «среди снежных» — разные группы.
- [ ] Нет, в снег опаздывают все 100 %
  > Из этих данных такого не следует.
- [ ] Да, если снежных дней 13 %
  > Даже тогда это разные величины: числитель общий (опоздания в снег), а знаменатели разные — число опоздавших и число снежных доставок. Совпадут они, только если опоздавших и снежных доставок поровну.
:::

{{practice: cond, snow-table}}

## Независимость

События **независимы**, если одно не меняет вероятность другого: $P(A \mid B) = P(A)$. Эквивалентная проверка: $P(A \text{ и } B) = P(A) \times P(B)$.

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
walk = ok["courier"] == "пеший"
both = (ok["late"] & walk).mean()
product = ok["late"].mean() * walk.mean()
print(f"P(опоздал и пеший) = {both:.3f}, P(опоздал) × P(пеший) = {product:.3f}")
```

Совместная вероятность втрое больше произведения — опоздания и пешие курьеры сильно связаны. Если бы они были независимы, числа совпали бы (с точностью до случайного шума).

::: quiz
Как по данным проверить, что опоздание не зависит от погоды?

- [x] Сравнить долю опозданий в снег с долей опозданий в целом: при независимости они совпадут с точностью до шума
  > Независимость означает, что условие не меняет вероятность: P(опоздание | снег) = P(опоздание).
- [ ] Убедиться, что P(опоздание и снег) маленькая
  > Совместная вероятность мала уже потому, что снежных дней мало. Сравнивать её нужно с произведением P(опоздание) × P(снег), а не с нулём.
- [ ] Проверить, что P(опоздание | снег) = P(снег | опоздание)
  > Эти величины почти всегда различаются — у них разные знаменатели, — и их равенство о независимости ничего не говорит.
- [ ] Посчитать, что снежных доставок меньше 10 %
  > Редкость события не делает его независимым: редкий снег может сильно влиять на опоздания.
:::

{{practice: independence, two-late}}

## Хотя бы один раз

Гость заказывает доставку трижды в неделю. Какова вероятность, что **хотя бы одна** доставка опоздает? Проще посчитать противоположное: все три вовремя — $(1 - p)^3$ (если опоздания независимы друг от друга). Значит, хотя бы одна опоздает с вероятностью $1 - (1 - p)^3$:

```python
p = 0.24
print("формула:", round(1 - (1 - p) ** 3, 3))

import numpy as np
rng = np.random.default_rng(3)
weeks = rng.random((100_000, 3)) < p          # 100 000 недель по 3 доставки
print("симуляция:", round(weeks.any(axis=1).mean(), 3))
```

`rng.random((100_000, 3))` — двумерный массив случайных чисел: 100 000 строк-недель по 3 доставки. Сравнение `< p` превращает каждое число в `True` (опоздала) или `False`. `any(axis=1)` — была ли в строке хоть одна `True`: `axis=1` значит «вдоль строки», как `sum(axis=1)` у сводной таблицы в главе 2. Первые три недели выглядят так:

```python
import numpy as np
weeks = np.random.default_rng(3).random((100_000, 3)) < 0.24
print(weeks[:3])
print(weeks[:3].any(axis=1))
```

::: figure at-least-one
Вероятность «хотя бы одно опоздание» удобнее считать через противоположное событие: все три доставки вовремя (0.76 × 0.76 × 0.76 ≈ 0.439), а всё остальное — хотя бы одно опоздание.
:::

Больше половины постоянных гостей хотя бы раз в неделю получают опоздавший кофе — хотя каждая отдельная доставка опаздывает «всего» в четверти случаев. Такие расчёты хорошо объясняют бизнесу, почему 24 % — это много.

::: warn Типичные ошибки
- **$P(A \mid B)$ вместо $P(B \mid A)$.** «68 % опозданий — у пеших» не то же, что «пешие опаздывают в 68 % случаев».
- **Независимость «по умолчанию».** Формула $1 - (1 - p)^n$ верна, только если опоздания не связаны; в снежную неделю они идут пачкой.
- **Доля по десяти строкам.** Маленькая группа даёт любую долю — закон больших чисел работает только на больших.
- **Seed внутри цикла.** Если создать генератор заново на каждом шаге — `for i in range(3): print(np.random.default_rng(42).random())`, — все три числа будут одинаковыми, и симуляция «замирает». Генератор создают один раз, до цикла.
:::

::: tip
Если сомневаетесь в формуле — проверьте симуляцией. Совпали числа — формула верна. Не совпали — ошиблись в формуле или в предположениях (например, о независимости).
:::

{{practice: at-least}}

## Практика

## task: p-late | Вероятность опоздания | warmup

Сохраните в `p_late` оценку вероятности опоздания по данным (время 1–299 минут), а в `p_on_time` — вероятность доставки вовремя. Обе — 3 знака.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
p = round((o['actual_min'] > o['promised_min']).mean(), 3)
assert close(need('p_late'), p), f'p_late = {need("p_late")}, а нужно {p}.'
assert close(need('p_on_time'), round(1 - (o['actual_min'] > o['promised_min']).mean(), 3)), 'p_on_time = 1 − p_late.'
```

### hint
Среднее столбца True/False — доля `True`: это и есть оценка вероятности.

### hint
`(ok["actual_min"] > ok["promised_min"]).mean()`; вовремя — `1 - …`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
late = ok["actual_min"] > ok["promised_min"]
p_late = round(late.mean(), 3)
p_on_time = round(1 - late.mean(), 3)
```

## task: two-late | Две доставки | warmup

Гость заказал две доставки, каждая опаздывает с вероятностью 0.24, независимо. Посчитайте по формулам (3 знака): `both` — обе опоздали, `none` — ни одна не опоздала, `exactly_one` — ровно одна. Проверьте себя: сумма трёх вероятностей должна быть 1.

### starter
```python
p = 0.24

```

### check
```python
assert close(need('both'), 0.058, 0.0011), f'both = {need("both")}. Обе — p × p.'
assert close(need('none'), 0.578, 0.0011), f'none = {need("none")}. Ни одна — (1 − p) × (1 − p).'
assert close(need('exactly_one'), 0.365, 0.0011), f'exactly_one = {need("exactly_one")}. Ровно одна — первая да и вторая нет, или наоборот.'
```

### hint
«Обе» — p × p, «ни одна» — (1 − p) × (1 − p): для независимых событий вероятности перемножаются.

### hint
«Ровно одна» — два варианта: p × (1 − p) + (1 − p) × p. Или проще: `1 - both - none`.

### solution
```python
p = 0.24
both = round(p * p, 3)
none = round((1 - p) * (1 - p), 3)
exactly_one = round(2 * p * (1 - p), 3)
```

### explain
0.058 + 0.578 + 0.365 = 1 (с точностью до округления): других исходов у двух доставок нет. Заметьте, что «ровно одна» почти в шесть раз вероятнее, чем «обе»: двойное опоздание подряд — редкость, если опоздания независимы. Если в данных двойных опозданий заметно больше 6 %, значит, они связаны — например, общей причиной вроде снегопада.

## task: cond | Условная вероятность | warmup

Сохраните `p_late_walk` — P(опоздание | пеший курьер) и `p_walk_late` — P(пеший курьер | опоздание). Обе — 3 знака.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
a = round(o.loc[o['courier'] == 'пеший', 'late'].mean(), 3)
b = round((o.loc[o['late'], 'courier'] == 'пеший').mean(), 3)
got_a, got_b = need('p_late_walk'), need('p_walk_late')
if close(got_a, b) and close(got_b, a):
    raise AssertionError('Перепутаны местами: P(A | B) — доля A среди строк, где выполнено B.')
assert close(got_a, a), f'p_late_walk = {got_a}, а нужно {a}.'
assert close(got_b, b), f'p_walk_late = {got_b}, а нужно {b}.'
```

### hint
P(опоздание | пеший) — доля опозданий среди пеших: `ok.loc[ok["courier"] == "пеший", "late"].mean()`.

### hint
P(пеший | опоздание) — доля пеших среди опоздавших: `(ok.loc[ok["late"], "courier"] == "пеший").mean()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
p_late_walk = round(ok.loc[ok["courier"] == "пеший", "late"].mean(), 3)
p_walk_late = round((ok.loc[ok["late"], "courier"] == "пеший").mean(), 3)
```

### explain
Три четверти пеших доставок опаздывают, а среди всех опозданий пешие — около двух третей. Это разные вопросы: первый — «насколько плохо работают пешие», второй — «какую часть проблемы они составляют».

## task: p-sim | Симуляция монетки | warmup

Соберите программу: симуляция 100 000 бросков монетки и вывод доли орлов, округлённой до 2 знаков.

### parsons
```python
import numpy as np
rng = np.random.default_rng(42)
heads = rng.random(100_000) < 0.5
share = heads.mean()
print(round(share, 2))
```

### check
```python
assert _lines in (['0.5'], ['0.49'], ['0.51']), f'Доля орлов должна быть около 0.5. Сейчас: {_lines}'
```

### hint
Генератор создаётся до бросков, доля считается после.

### hint
Порядок: импорт → `rng = ...` → `flips = rng.random(100_000) < 0.5` → `print(round(flips.mean(), 2))`.

## task: at-least | Хотя бы одна | base

Гость заказывает доставку `n = 5` раз за две недели, вероятность опоздания каждой — `p = 0.24`, опоздания независимы. Сохраните в `p_formula` вероятность, что опоздает **хотя бы одна** (по формуле, 3 знака), а в `p_sim` — оценку симуляцией по 100 000 повторений (3 знака).

### starter
```python
import numpy as np
p, n = 0.24, 5
rng = np.random.default_rng(5)

```

### check
```python
want = round(1 - (1 - 0.24) ** 5, 3)
assert close(need('p_formula'), want), f'p_formula = {need("p_formula")}, а нужно {want}: 1 − (1 − p)ⁿ.'
assert abs(need('p_sim') - want) < 0.01, f'p_sim = {need("p_sim")} — слишком далеко от {want}. Нужно 100 000 строк по n доставок и any(axis=1).'
assert 'rng.random' in _code, 'Посчитайте p_sim симуляцией: rng.random((100_000, n)) < p.'
```

### hint
Формула: `1 - (1 - p) ** n`.

### hint
Симуляция: `sims = rng.random((100_000, n)) < p`, затем `sims.any(axis=1).mean()`.

### solution
```python
import numpy as np
p, n = 0.24, 5
rng = np.random.default_rng(5)
p_formula = round(1 - (1 - p) ** n, 3)
sims = rng.random((100_000, n)) < p
p_sim = round(sims.any(axis=1).mean(), 3)
```

### explain
Формула даёт 0.746, симуляция — 0.745: совпадение до третьего знака. За две недели почти три гостя из четырёх хотя бы раз получат опоздавшую доставку — хотя каждая отдельная доставка опаздывает в 24 % случаев.

## task: independence | Независимы ли события | base

Проверьте, независимы ли опоздание и снег. Сохраните `p_joint` — P(опоздание и снег), `p_product` — P(опоздание) × P(снег) (обе — 4 знака) и `ratio` — их отношение (2 знака).

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
snow = ok["weather"] == "снег"

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
late = o['actual_min'] > o['promised_min']
s = o['weather'] == 'снег'
j, pr = (late & s).mean(), late.mean() * s.mean()
assert close(need('p_joint'), round(j, 4)), f'p_joint = {need("p_joint")}, а нужно {round(j, 4)}.'
assert close(need('p_product'), round(pr, 4)), f'p_product = {need("p_product")}.'
assert close(need('ratio'), round(j / pr, 2)), f'ratio = {need("ratio")}.'
```

### hint
Оба события сразу — `(ok["late"] & snow).mean()`.

### hint
Произведение — `ok["late"].mean() * snow.mean()`. Отношение считайте по неокруглённым значениям.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
snow = ok["weather"] == "снег"
joint = (ok["late"] & snow).mean()
product = ok["late"].mean() * snow.mean()
p_joint = round(joint, 4)
p_product = round(product, 4)
ratio = round(joint / product, 2)
```

### explain
Отношение больше 1 — опоздание и снег встречаются вместе чаще, чем было бы при независимости. Отношение `P(A и B) / (P(A) × P(B))` в маркетинге называют **lift** — им, например, ищут товары, которые чаще покупают вместе.

## task: snow-table | Снег в двух направлениях | plus

Постройте таблицу `t = pd.crosstab(ok["weather"] == "снег", ok["late"], margins=True)` и по её числам сохраните: `n_snow_late` — число опоздавших снежных доставок, `p_late_snow` — P(опоздание | снег) и `p_snow_late` — P(снег | опоздание) (3 знака), `extra` — сколько опозданий было бы в снег, если бы там опаздывали с общей частотой (число снежных доставок × P(опоздание), 1 знак), и `added` — сколько опозданий снег добавил сверх этого (`n_snow_late − extra`, 1 знак).

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d0 = _pd.read_csv('deliveries.csv'); o = d0[d0['actual_min'].between(1, 299)].copy(); o['late'] = o['actual_min'] > o['promised_min']
sn = o['weather'] == 'снег'
assert need('n_snow_late') == int((sn & o['late']).sum()), f'n_snow_late = {need("n_snow_late")}.'
assert close(need('p_late_snow'), round(o.loc[sn, 'late'].mean(), 3)), f'p_late_snow = {need("p_late_snow")} — делите на число снежных доставок.'
assert close(need('p_snow_late'), round(sn[o['late']].mean(), 3)), f'p_snow_late = {need("p_snow_late")} — делите на число опозданий.'
assert close(need('extra'), round(sn.sum() * o['late'].mean(), 1), 0.051), f'extra = {need("extra")}.'
assert close(need('added'), round(int((sn & o['late']).sum()) - sn.sum() * o['late'].mean(), 1), 0.051), f'added = {need("added")}. Это n_snow_late − extra.'
```

### hint
В таблице строки — снег (`True`) или нет, столбцы — опоздание, `All` — итоги. Опоздавшие в снег — `t.loc[True, True]`.

### hint
P(опоздание | снег) = `t.loc[True, True] / t.loc[True, "All"]`; P(снег | опоздание) = `t.loc[True, True] / t.loc["All", True]`. Для `extra`: `t.loc[True, "All"] * ok["late"].mean()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

t = pd.crosstab(ok["weather"] == "снег", ok["late"], margins=True)
n_snow_late = int(t.loc[True, True])
p_late_snow = round(t.loc[True, True] / t.loc[True, "All"], 3)
p_snow_late = round(t.loc[True, True] / t.loc["All", True], 3)
extra = round(t.loc[True, "All"] * ok["late"].mean(), 1)
added = round(n_snow_late - t.loc[True, "All"] * ok["late"].mean(), 1)
```

### explain
В снег опоздали 57 доставок из 166 — 34 %. Но среди всех 441 опоздания на снег приходится лишь 13 %: снежных дней мало. При обычной частоте опозданий в снег было бы около 40 опозданий — снег «добавил» примерно 17. Для отчёта это честнее, чем «в снег опаздываем в полтора раза чаще»: эффект заметный, но на общую картину опозданий влияет слабо.

## task: running | Закон больших чисел | base

Смоделируйте 5 000 доставок с вероятностью опоздания 0.24 (`rng = np.random.default_rng(11)`), посчитайте накопленную долю опозданий `running` (массив той же длины) и нарисуйте её линией вместе с горизонтальной линией на 0.24. В `after_100` и `after_5000` сохраните отклонение доли от 0.24 (по модулю) после 100-й и после 5 000-й доставки.

### starter
```python
import numpy as np
import matplotlib.pyplot as plt
rng = np.random.default_rng(11)

```

### check
```python
import numpy as _np
r = need('running')
assert len(r) == 5000, f'В running {len(r)} значений, а нужно 5000.'
l = _np.random.default_rng(11).random(5000) < 0.24
want = l.cumsum() / _np.arange(1, 5001)
assert _np.allclose(r, want), 'running — накопленная сумма опозданий, делённая на номер доставки (1, 2, …).'
assert close(need('after_100'), abs(want[99] - 0.24)) and close(need('after_5000'), abs(want[-1] - 0.24)), 'Отклонение — доля минус 0.24 по модулю. Проверьте номер элемента: нумерация с нуля.'
ax = ax_of()
assert ax.lines and len(ax.lines[0].get_ydata()) == 5000, 'Нарисуйте running линией.'
assert any(len(set(l.get_ydata())) == 1 for l in ax.lines[1:]), 'Добавьте горизонтальную линию: ax.axhline(0.24).'
```

### hint
`late = rng.random(5000) < 0.24`; `running = late.cumsum() / np.arange(1, 5001)`.

### hint
После 100-й доставки — элемент с индексом 99. Модуль — `abs(...)`.

### solution
```python
import numpy as np
import matplotlib.pyplot as plt
rng = np.random.default_rng(11)
late = rng.random(5000) < 0.24
running = late.cumsum() / np.arange(1, 5001)
after_100 = abs(running[99] - 0.24)
after_5000 = abs(running[-1] - 0.24)

fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(running)
ax.axhline(0.24, color="tab:red", linestyle="--")
```

### explain
После 100 доставок доля отклоняется от 0.24 на 0.09 — почти на половину самой вероятности. После 5 000 — на 0.005. Отклонение уменьшилось в 17 раз при росте числа доставок в 50 раз: точность растёт медленнее числа данных (примерно как корень — подробнее в уроке «Выборки и центральная предельная теорема»).

## task: small-groups | Почему маленькие группы шумят | base

Представьте 20 кофеен, у каждой ровно 30 доставок, и у **всех** настоящая вероятность опоздания одинаковая — 0.24. Смоделируйте долю опозданий каждой кофейни (`rng = np.random.default_rng(8)`, таблица 20 × 30) и сохраните `shares` (массив из 20 долей), `spread` — разницу между самой большой и самой маленькой долей (2 знака).

### starter
```python
import numpy as np
rng = np.random.default_rng(8)

```

### check
```python
import numpy as _np
s = need('shares')
assert len(s) == 20, f'В shares {len(s)} значений, а кофеен 20.'
w = (_np.random.default_rng(8).random((20, 30)) < 0.24).mean(axis=1)
assert _np.allclose(sorted(s), sorted(w)), 'shares — доля True в каждой строке таблицы 20 × 30: mean(axis=1).'
assert close(need('spread'), round(w.max() - w.min(), 2)), f'spread = {need("spread")}.'
```

### hint
`sims = rng.random((20, 30)) < 0.24` — строка = кофейня. Доля по строкам — `sims.mean(axis=1)`.

### hint
`spread = round(shares.max() - shares.min(), 2)`.

### solution
```python
import numpy as np
rng = np.random.default_rng(8)
sims = rng.random((20, 30)) < 0.24
shares = sims.mean(axis=1)
spread = round(shares.max() - shares.min(), 2)
shares.round(2)
```

### explain
Все кофейни работают одинаково, а «лучшая» и «худшая» различаются на десятки процентных пунктов — только из-за случайности при 30 доставках. Если бы это были настоящие данные, кто-то обязательно похвалил бы «лучшую» кофейню. Вот почему нужны статистические тесты — к ним идём.

## task: shift | Восемь опозданий за смену | star

Курьер за смену делает 20 доставок, каждая опаздывает с вероятностью 0.24 независимо от других. Смоделируйте 200 000 смен (`rng = np.random.default_rng(21)`) и сохраните в `p_8plus` оценку вероятности, что за смену опоздают **8 и более** доставок (4 знака). В `typical` — самое частое число опозданий за смену.

### starter
```python
import numpy as np
rng = np.random.default_rng(21)

```

### check
```python
import numpy as _np
from scipy import stats as _st
want = _st.binom.sf(7, 20, 0.24)
assert abs(need('p_8plus') - want) < 0.003, f'p_8plus = {need("p_8plus")} — далеко от ожидаемого ≈ {want:.4f}.'
assert int(need('typical')) == 4 or int(need('typical')) == 5, f'typical = {need("typical")}. Самое частое число опозданий — около 20 × 0.24.'
```

### hint
`late = rng.random((200_000, 20)) < 0.24`, число опозданий в смене — `late.sum(axis=1)`.

### hint
Самое частое значение: `np.bincount(counts).argmax()` — `bincount` считает, сколько раз встретилось каждое целое число.

### solution
```python
import numpy as np
rng = np.random.default_rng(21)
late = rng.random((200_000, 20)) < 0.24
counts = late.sum(axis=1)
p_8plus = round((counts >= 8).mean(), 4)
typical = np.bincount(counts).argmax()
```

### explain
Получилось распределение числа «успехов» в 20 независимых попытках. У него есть имя — **биномиальное**, и для него есть готовые формулы. О них — в следующем уроке.
