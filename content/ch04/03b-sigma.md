---
title: "Стандартное отклонение: разброс одним числом"
lead: "Ящик с усами показывает разброс пятью числами. Статистике нужно одно — стандартное отклонение σ: на нём держатся доверительные интервалы, тесты и A/B. Считаем σ руками на пяти доставках, разбираемся, почему pandas и numpy дают разные ответы, и видим, как один выброс раздувает σ в разы."
files: [deliveries.csv]
recap:
  - "Стандартное отклонение σ — корень из среднего квадрата отклонения от среднего: `s.std()`. Оно в тех же единицах, что данные; дисперсия `s.var()` — в квадрате."
  - "`ddof` задаёт знаменатель `n − ddof`: у pandas по умолчанию `ddof=1` (выборка), у `np.std` — `ddof=0`. Пишите явно."
  - "σ очень чувствительна к выбросам (49 минут против 11 после очистки), IQR — нет (13 и 13). Для скошенных данных в отчёт — квантили."
---

## Дисперсия и стандартное отклонение

В уроке «Ящик с усами и выбросы» разброс мерили IQR — шириной середины данных. Есть и другая мера разброса, на которой построена почти вся статистика следующей главы (доверительные интервалы, тесты, A/B): **стандартное отклонение** σ (сигма). Оно отвечает на вопрос: «насколько в среднем значения отходят от своего среднего». Без него не посчитать, например, точность среднего чека и не сравнить два варианта акции.

::: tip Аналогия
Два бариста в среднем готовят капучино за 5 минут. У первого — всегда 4–6 минут, у второго — то 2, то 8. Среднее одно, а гостю второго бариста не угадать, когда будет кофе. Стандартное отклонение — это число, которое отличает «стабильного» бариста от «непредсказуемого». При этом σ меряет не только «непредсказуемость человека» — в разброс доставок вносят вклад и погода, и расстояние.
:::

### Игрушечный пример руками

Время четырёх капучино у бариста А: 4, 5, 5, 6 минут; у бариста Б: 2, 4, 6, 8. Среднее у обоих — 5.

1. **Отклонения от среднего.** А: −1, 0, 0, +1. Б: −3, −1, +1, +3. Их сумма всегда 0 — плюсы и минусы гасят друг друга, поэтому просто усреднить отклонения нельзя.
2. **Квадраты отклонений** убирают знак. А: 1, 0, 0, 1 — сумма **2**. Б: 9, 1, 1, 9 — сумма **20**.
3. **Дисперсия** — средний квадрат отклонения. Делим сумму на n − 1 = 3 (почему не на 4 — чуть ниже): А — 2 / 3 ≈ **0.67**, Б — 20 / 3 ≈ **6.67** минуты в квадрате.
4. **Стандартное отклонение** — корень из дисперсии, чтобы вернуться в минуты: А — √0.67 ≈ **0.82** мин, Б — √6.67 ≈ **2.58** мин.

У Б разброс в три с лишним раза больше — при одинаковом среднем.

::: figure sigma-steps
Те же четыре шага на картинке: стрелки — отклонения от среднего 5, затем квадраты, их сумма делится на n − 1 = 3, корень возвращает минуты.
:::

$$s^2 = \frac{\sum (x_i - \bar{x})^2}{n - 1}, \qquad s = \sqrt{s^2}$$

Здесь $x_i$ — отдельные значения, $\bar{x}$ — их среднее, $\sum$ — сумма по всем значениям, $n$ — их число, $s^2$ — дисперсия, $s$ — стандартное отклонение. Его часто обозначают и греческой σ.

```python
import pandas as pd
a = pd.Series([4, 5, 5, 6])
b = pd.Series([2, 4, 6, 8])
for name, x in [("А", a), ("Б", b)]:
    dev = x - x.mean()                          # отклонения
    var = (dev ** 2).sum() / (len(x) - 1)       # дисперсия, делим на n − 1
    print(name, dev.tolist(), round(var, 2), round(var ** 0.5, 2), round(x.std(), 2))
```

Что здесь происходит:

- `x - x.mean()` — Series отклонений: pandas вычитает среднее из каждого значения;
- `(dev ** 2).sum() / (len(x) - 1)` — формула дисперсии буквально;
- `var ** 0.5` — квадратный корень; `x.std()` даёт то же число одной командой.

### `ddof`: делить на n или на n − 1

В формуле выше мы делили на n − 1. Можно делить и на n — получится «средний квадрат отклонения» в буквальном смысле. Какой вариант выбрать, задаёт параметр **`ddof`** (delta degrees of freedom): знаменатель равен `n − ddof`.

- `ddof=0` — делим на n. Так считают, когда перед вами **все** значения, которые вас интересуют (вся генеральная совокупность).
- `ddof=1` — делим на n − 1. Так считают по **выборке**, когда по ней хотят судить о большем: по 4 капучино — о бариста вообще. Отклонения мы меряем от среднего этой же выборки, а оно всегда «подстроено» под неё — поэтому разброс получается чуть заниженным. Деление на n − 1 вместо n эту заниженность исправляет. Подробнее — в главе 5.

Схема справа проверяет это перебором. Бариста варит за 2, 4, 6 или 8 минут, все четыре времени одинаково вероятны. Дисперсия самого ряда 2, 4, 6, 8 при делении на n — 5: это «истинная» дисперсия бариста. Возьмём четыре чашки: у каждой 4 варианта времени, всего 4⁴ = 256 сочетаний. Посчитаем дисперсию каждого сочетания и усредним.

::: figure ddof-why
Слева: для чашек 2, 4, 4, 6 сумма квадратов отклонений от своего среднего 4 равна 8, от истинного среднего 5 — 12; своё среднее всегда ближе к точкам. Справа: бариста варит за 2, 4, 6 или 8 минут одинаково часто (истинная дисперсия 5); по всем 256 вариантам четырёх чашек дисперсия выборки с `ddof=0` в среднем 3.75, с `ddof=1` — ровно 5.
:::

Ловушка в том, что у pandas и numpy **разные значения по умолчанию**:

::: predict
```python static
import numpy as np
import pandas as pd
x = [1, 2, 3, 4]
print(round(pd.Series(x).std(), 2), round(np.std(x), 2))
```

- `1.29 1.29`
- [x] `1.29 1.12`
- `1.12 1.12`

Почему: `pd.Series.std()` по умолчанию делит на n − 1 (`ddof=1`): √(5 / 3) ≈ 1.29. `np.std` — на n (`ddof=0`): √(5 / 4) ≈ 1.12. Одинаковые данные — разные ответы. Чтобы не гадать, пишите `ddof` явно.
:::

Чем больше n, тем меньше разница: при 1 841 доставке n и n − 1 почти не отличаются, а при 4–5 значениях разница заметная. В pandas знаменатель задают явно: `s.std(ddof=0)` или `s.std(ddof=1)`.

::: sql
`STDDEV_SAMP(x)` — с делением на n − 1 (в большинстве СУБД `STDDEV` — то же самое), `STDDEV_POP(x)` — на n. Так же для дисперсии: `VAR_SAMP` и `VAR_POP`.
:::

{{practice: sigma-hand, ddof-small}}

### На реальных данных: σ, IQR и выбросы

```python
import pandas as pd
import numpy as np
d = pd.read_csv("deliveries.csv")
raw = d["actual_min"].dropna()
ok = d.loc[d["actual_min"].between(1, 299), "actual_min"]

for name, s in [("все значения", raw), ("1–299 минут", ok)]:
    iqr = s.quantile(0.75) - s.quantile(0.25)
    print(f"{name}: σ = {s.std():.2f}, np.std = {np.std(s):.2f}, IQR = {iqr:.1f}")

m, sd = ok.mean(), ok.std()
print("в пределах среднее ± σ:", round(ok.between(m - sd, m + sd).mean() * 100, 1), "%")
```

Что здесь происходит:

- `s.std()` и `np.std(s)` на 1 841 значении совпадают до сотых — разница между n и n − 1 тут не важна;
- σ по всем значениям — **49.37** минуты, после очистки — **11.02**. Пять «забытых» заказов на 735–1 281 минуту раздули σ в 4.5 раза. Почему так сильно — видно в цифрах. Среднее всех значений 36.8 минуты. Доставка на 1 281 минуту отклоняется от него на 1 281 − 36.8 ≈ 1 244, её квадрат ≈ 1.55 млн. Обычное отклонение — около 11 минут, его квадрат ≈ 121. Получается, одна такая строка весит в сумме квадратов как ~13 000 обычных доставок (1.55 млн / 121);
- IQR в обоих случаях — **13.0** минуты: квартили на хвосты не смотрят;
- `between(m - sd, m + sd)` — доля доставок не дальше одного σ от среднего: **74.7 %**.

Как читать: «типичная доставка отклоняется от средних 34.5 минуты примерно на 11 минут». Для симметричного колокола (нормального распределения — оно подробно разобрано в уроке «Нормальное распределение, приближение и z-оценка» главы 5) в пределах ±σ лежит около 68 % значений, в пределах ±2σ — около 95 %. У нас в ±σ больше, 74.7 %, потому что распределение скошенное и с острым горбом. Поэтому для скошенных данных в отчёте лучше квантили и IQR, а σ нужна для формул главы 5.

::: quiz
Аналитик посчитал разброс времени доставки в pandas, а коллега в numpy — и получил другое число. Данные одни и те же. В чём причина?

- [x] У них разный `ddof` по умолчанию: pandas делит на n − 1, numpy — на n
  > `pd.Series.std()` — `ddof=1`, `np.std` — `ddof=0`. На больших данных разница исчезает, на маленьких группах заметна. Лекарство — явно писать `ddof`.
- [ ] numpy не умеет считать стандартное отклонение по Series
  > Умеет: `np.std(series)` работает, просто с другим знаменателем.
- [ ] pandas выбрасывает выбросы перед расчётом
  > Нет, σ считается по всем значениям — поэтому она так чувствительна к аномалиям.
- [ ] Один из них посчитал дисперсию, а не σ
  > Возможно и такое, но тогда разница была бы огромной (121 против 11), а не в сотых.
:::

::: warn Типичные ошибки
- **σ по данным с аномалиями.** Одна доставка «1281 минута» раздувает σ в разы; сначала очистка, либо — устойчивая мера (IQR).
- **Не тот `ddof`.** `np.std` и `pd.Series.std` дают разные ответы на маленьких группах; пишите `ddof=1` или `ddof=0` явно.
- **Дисперсия в отчёте.** 121.4 «минуты в квадрате» никто не поймёт; в отчёт — σ в минутах, а лучше квантили.
- **«±σ — это 68 %» для любых данных.** Правило верно для колокола; для скошенного времени доставки — 74.7 %.
:::

{{practice: sigma-courier, sigma-shops, two-sigma}}

## Практика

## task: sigma-hand | Сигма руками | warmup

Время пяти доставок одного курьера: 28, 35, 31, 40, 26 минут. Посчитайте **по формуле**, без `.std()` и `.var()`:

- `dev` — список отклонений от среднего;
- `var1` — дисперсию с делением на n − 1;
- `sd1` — стандартное отклонение (корень из `var1`);
- `sd0` — стандартное отклонение с делением на n.

`var1`, `sd1`, `sd0` округлите до 2 знаков.

### starter
```python
x = [28, 35, 31, 40, 26]

```

### check
```python
import math as _m
x = [28, 35, 31, 40, 26]
mu = sum(x) / len(x)
ss = sum((v - mu) ** 2 for v in x)
assert [float(v) for v in need('dev')] == [v - mu for v in x], f'dev = {need("dev")}: каждое значение минус среднее {mu}.'
assert calls('std') == 0 and calls('var') == 0, 'Здесь нужно посчитать по формуле — без .std() и .var().'
assert close(need('var1'), round(ss / 4, 2)), f'var1 = {need("var1")}: сумма квадратов отклонений / (n − 1).'
assert close(need('sd1'), round(_m.sqrt(ss / 4), 2)), f'sd1 = {need("sd1")}: корень из дисперсии.'
if close(need('sd0'), round(_m.sqrt(ss / 4), 2)):
    raise AssertionError('sd0 совпал с sd1: для sd0 делите сумму квадратов на n = 5, а не на 4.')
assert close(need('sd0'), round(_m.sqrt(ss / 5), 2)), f'sd0 = {need("sd0")}.'
```

### hint
Среднее — `sum(x) / len(x)`; отклонения — генератор списка `[v - mean for v in x]`.

### hint
Сумма квадратов — `sum(d ** 2 for d in dev)`; дисперсия — она же, делённая на `len(x) - 1`; корень — `** 0.5`.

### hint
`ss = sum(d ** 2 for d in dev)`, `var1 = round(ss / (len(x) - 1), 2)`, `sd1 = round((ss / (len(x) - 1)) ** 0.5, 2)`, `sd0 = round((ss / len(x)) ** 0.5, 2)`.

### solution
```python
x = [28, 35, 31, 40, 26]
mean = sum(x) / len(x)
dev = [v - mean for v in x]
ss = sum(d ** 2 for d in dev)
var1 = round(ss / (len(x) - 1), 2)
sd1 = round((ss / (len(x) - 1)) ** 0.5, 2)
sd0 = round((ss / len(x)) ** 0.5, 2)
print(dev, var1, sd1, sd0)
```

## task: ddof-small | ddof на пяти и на тридцати пяти | plus

Пеших доставок в снег (время 1–299 минут) — 35. Отсортируйте их по `created` и возьмите **пять последних** — `last5`. Для `last5` и для всех 35 посчитайте стандартное отклонение с `ddof=1` и с `ddof=0` и сохраните, на сколько процентов первое больше второго (1 знак): `gap5` и `gap35`.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
w = o[(o['weather'] == 'снег') & (o['courier'] == 'пеший')].sort_values('created')['actual_min']
l5 = w.tail(5)
g5 = round((l5.std(ddof=1) / l5.std(ddof=0) - 1) * 100, 1)
g35 = round((w.std(ddof=1) / w.std(ddof=0) - 1) * 100, 1)
x = need('last5')
vals = sorted(float(v) for v in (x['actual_min'] if isinstance(x, _pd.DataFrame) else x))
assert vals == sorted(float(v) for v in l5), f'В last5 значения {vals}, а нужны пять последних по created пеших доставок в снег: {sorted(float(v) for v in l5)}.'
assert close(need('gap5'), g5, 0.051), f'gap5 = {need("gap5")}, а нужно {g5}: (std(ddof=1) / std(ddof=0) − 1) × 100 по пяти доставкам.'
assert close(need('gap35'), g35, 0.051), f'gap35 = {need("gap35")}, а нужно {g35}: то же по всем 35.'
```

### hint
Фильтр — два условия через `&`: `ok[(ok["weather"] == "снег") & (ok["courier"] == "пеший")]`; затем `sort_values("created")` и `.tail(5)`.

### hint
`s1 = x.std(ddof=1)`, `s0 = x.std(ddof=0)`, разница в процентах — `round((s1 / s0 - 1) * 100, 1)`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
walk = ok[(ok["weather"] == "снег") & (ok["courier"] == "пеший")].sort_values("created")["actual_min"]
last5 = walk.tail(5)
gap5 = round((last5.std(ddof=1) / last5.std(ddof=0) - 1) * 100, 1)
gap35 = round((walk.std(ddof=1) / walk.std(ddof=0) - 1) * 100, 1)
print(last5.tolist(), gap5, gap35)
```

### explain
На пяти доставках (39, 41, 46, 35, 36 минут) σ с `ddof=1` — 4.39, с `ddof=0` — 3.93: разница 11.8 %. На всех 35 — 15.48 против 15.26, разница 1.5 %. Отношение двух σ зависит только от n: это $\sqrt{n / (n - 1)}$, $\sqrt{5/4} ≈ 1.118$ и $\sqrt{35/34} ≈ 1.015$. Поэтому на маленьких срезах (одна кофейня в снег, один курьер за неделю) выбор `ddof` меняет ответ на десятки процентов, а на тысячах строк — нет.

## task: sigma-courier | Разброс по курьерам | base

Для доставок с временем 1–299 минут соберите `spread` — таблицу по типу курьера со столбцами `mean`, `std` (стандартное отклонение по выборке, `ddof=1`) и `iqr`, все с 1 знаком. Сохраните `most_stable` — тип курьера с наименьшим `std`.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
g = o.groupby('courier')['actual_min']
w = _pd.DataFrame({'mean': g.mean(), 'std': g.std(), 'iqr': g.quantile(0.75) - g.quantile(0.25)}).round(1)
s = need('spread', _pd.DataFrame)
if 'courier' in s.columns:
    s = s.set_index('courier')
for c in ('mean', 'std', 'iqr'):
    assert c in s.columns, f'В spread нет столбца {c}.'
assert set(s.index) == set(w.index), f'Строки spread: {list(s.index)} — типы курьеров.'
g0 = o.groupby('courier')['actual_min'].std(ddof=0).round(1)
if all(close(s.loc[k, 'std'], g0[k], 0.051) for k in w.index) and not all(close(s.loc[k, 'std'], w.loc[k, 'std'], 0.051) for k in w.index):
    raise AssertionError('std посчитан с ddof=0 (как в numpy). Нужно по выборке: ddof=1 — это значение по умолчанию у pandas.')
for c in ('mean', 'std', 'iqr'):
    assert all(close(s.loc[k, c], w.loc[k, c], 0.051) for k in w.index), f'Столбец {c} не совпадает.'
assert need('most_stable') == w['std'].idxmin(), f'most_stable = {need("most_stable")!r}.'
```

### hint
`g = ok.groupby("courier")["actual_min"]`; у группы есть `g.mean()`, `g.std()`, `g.quantile(0.75)`.

### hint
`spread = pd.DataFrame({"mean": g.mean(), "std": g.std(), "iqr": g.quantile(0.75) - g.quantile(0.25)}).round(1)`; самый стабильный — `spread["std"].idxmin()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
g = ok.groupby("courier")["actual_min"]
spread = pd.DataFrame({
    "mean": g.mean(),
    "std": g.std(ddof=1),
    "iqr": g.quantile(0.75) - g.quantile(0.25),
}).round(1)
most_stable = spread["std"].idxmin()
spread
```

### explain
У вело-курьеров σ = 9.1 минуты, у авто — 10.7, у пеших — 13.3: велосипедисты самые предсказуемые. IQR у авто и пеших одинаковый (14 минут), а σ у пеших заметно больше — значит, у пеших длиннее хвосты: середина такая же, но чаще бывают очень долгие доставки. Две меры разброса вместе говорят больше, чем каждая отдельно. На сотнях доставок в группе `ddof=0` и `ddof=1` почти не отличаются (у авто 10.6 вместо 10.7), но на группах из 5–10 значений разница заметная — привычка писать `ddof` явно спасает.

## task: sigma-shops | Кто раздул σ | base

Посчитайте σ времени доставки (`ddof=1`) по каждой кофейне дважды: по всем непустым значениям `actual_min` и после очистки (1–299 минут). Соберите таблицу `shops` (индекс — `shop_id`) со столбцами `raw`, `clean` и `ratio = raw / clean`, все с 1 знаком (`ratio` считайте по уже округлённым `raw` и `clean`). Сохраните `inflated` — список кофеен, у которых `ratio` больше 2.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
a = d.dropna(subset=['actual_min']).groupby('shop_id')['actual_min'].std().round(1)
b = d[d['actual_min'].between(1, 299)].groupby('shop_id')['actual_min'].std().round(1)
w = _pd.DataFrame({'raw': a, 'clean': b})
w['ratio'] = (w['raw'] / w['clean']).round(1)
s = need('shops', _pd.DataFrame)
if 'shop_id' in s.columns:
    s = s.set_index('shop_id')
for c in ('raw', 'clean', 'ratio'):
    assert c in s.columns, f'В shops нет столбца {c}.'
assert set(s.index) == set(w.index), f'Строки shops: {list(s.index)} — кофейни.'
for c in ('raw', 'clean'):
    assert all(close(s.loc[k, c], w.loc[k, c], 0.051) for k in w.index), f'Столбец {c} не совпадает: {c} — std() по {"всем непустым значениям" if c == "raw" else "доставкам 1–299 минут"}.'
assert all(close(s.loc[k, 'ratio'], w.loc[k, 'ratio'], 0.051) for k in w.index), 'ratio = raw / clean, 1 знак.'
exp = sorted(w.index[w['ratio'] > 2])
assert sorted(str(x) for x in need('inflated')) == exp, f'inflated = {need("inflated")}, а нужно {exp}.'
```

### hint
Два `groupby("shop_id")["actual_min"].std()`: один по `d` (пустые значения `std` пропускает сам), второй — по `d[d["actual_min"].between(1, 299)]`. Соберите их в `pd.DataFrame({"raw": ..., "clean": ...})`.

### hint
`shops["ratio"] = (shops["raw"] / shops["clean"]).round(1)`; список — `list(shops.index[shops["ratio"] > 2])`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
raw = d.groupby("shop_id")["actual_min"].std().round(1)
clean = d[d["actual_min"].between(1, 299)].groupby("shop_id")["actual_min"].std().round(1)
shops = pd.DataFrame({"raw": raw, "clean": clean})
shops["ratio"] = (shops["raw"] / shops["clean"]).round(1)
inflated = list(shops.index[shops["ratio"] > 2])
shops
```

### explain
После очистки σ у всех кофеен почти одинаковая — 10.0–11.5 минуты. До очистки у PRM-1 она 76.2 (в 6.7 раза больше), у KZN-2 — 54.0, у PRM-2 — 59.5: именно там лежат пять «забытых» заказов на 735–1 281 минуту (у PRM-1 их три). У KZN-1 тоже есть мусор — 0 и −12 минут, — но σ выросла только с 10.7 до 11.2: значения рядом с нулём отстоят от среднего на десятки минут, а не на тысячу. σ по сырым данным показывает не «какая кофейня нестабильна», а «где больше всего забытых заказов».

## task: two-sigma | Правило ±2σ на скошенных данных | base

Для доставок 1–299 минут посчитайте среднее `m` и σ `sd` (`ddof=1`). Сохраните `share2` — долю доставок в пределах `m ± 2·sd` в процентах (1 знак), `above` — сколько доставок дальше `m + 2·sd`, и `below` — сколько ближе `m − 2·sd`.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
s = d.loc[d["actual_min"].between(1, 299), "actual_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
s = d.loc[d['actual_min'].between(1, 299), 'actual_min']
m, sd = s.mean(), s.std()
sh = round(s.between(m - 2 * sd, m + 2 * sd).mean() * 100, 1)
assert close(need('share2'), sh, 0.051), f'share2 = {need("share2")}, а нужно {sh}: between(m - 2 * sd, m + 2 * sd).mean() × 100.'
assert int(need('above')) == int((s > m + 2 * sd).sum()), f'above = {need("above")}: (s > m + 2 * sd).sum().'
assert int(need('below')) == int((s < m - 2 * sd).sum()), f'below = {need("below")}: (s < m - 2 * sd).sum().'
```

### hint
Как в разделе «На реальных данных»: `s.between(m - 2 * sd, m + 2 * sd).mean()` — доля; умножьте на 100 и округлите.

### hint
Число значений выше границы — сумма `True`: `(s > m + 2 * sd).sum()`; так же для нижней.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
s = d.loc[d["actual_min"].between(1, 299), "actual_min"]
m, sd = s.mean(), s.std()
share2 = round(s.between(m - 2 * sd, m + 2 * sd).mean() * 100, 1)
above = int((s > m + 2 * sd).sum())
below = int((s < m - 2 * sd).sum())
print(round(m - 2 * sd, 1), round(m + 2 * sd, 1), share2, above, below)
```

### explain
Границы — 12.4 и 56.5 минуты, внутри 95.5 % доставок — почти как у колокола. Но за границами всё несимметрично: 82 доставки дольше 56.5 минуты и ни одной быстрее 12.4 (самая быстрая — 14 минут). У колокола хвосты были бы примерно поровну. Значит, «±2σ» здесь не описывает риски: опасный хвост один — справа, и его лучше описывать квантилем, например «10 % доставок дольше N минут».
