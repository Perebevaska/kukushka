---
title: Доверительные интервалы
lead: "«Средняя доставка в KZN-2 — 37.8 минуты» звучит точно, но по выборке из 272 доставок это лишь оценка. Доверительный интервал честно говорит, где, скорее всего, лежит настоящее значение: «от 36.6 до 39.0 минут». Строим интервалы для среднего, для доли, для медианы — и для разницы двух групп."
files: [deliveries.csv]
recap:
  - "95 %-й доверительный интервал: если повторять сбор данных много раз, 95 % таких интервалов накроют настоящее значение."
  - "Для среднего: среднее ± t · SE, где SE = s / √n, t = `stats.t.ppf(0.975, n − 1)` (≈ 1.96 при больших n). Готовая функция: `stats.t.interval(0.95, n − 1, loc=среднее, scale=SE)`."
  - "Для доли: p ± 1.96 · √(p(1−p)/n) или точнее — `proportion_confint(успехов, n, method=\"wilson\")` из statsmodels."
  - "Бутстрэп — интервал для чего угодно (медиана, квантиль): много раз перевыбрать данные с возвращением и взять 2.5-й и 97.5-й перцентили статистики."
  - "Разница двух долей: (p₁ − p₂) ± 1.96 · √(p₁q₁/n₁ + p₂q₂/n₂). Если ноль не внутри интервала — разница, скорее всего, не случайна."
  - "Шире интервал — меньше данных или выше уровень доверия. Сужается как √n."
---

## Оценка с погрешностью

Из урока «Выборки и центральная предельная теорема» мы знаем: выборочное среднее отклоняется от настоящего примерно на одну стандартную ошибку, а в 95 % случаев — не дальше 1.96 SE. Значит, интервал

$$
\text{среднее} \pm 1.96 \cdot SE
$$

в 95 % случаев накрывает настоящее среднее. Это и есть **95 %-й доверительный интервал** (ДИ, confidence interval).

::: tip Аналогия
Доверительный интервал похож на сеть, которую забрасывают в пруд за невидимой рыбой. Рыба — настоящее среднее — стоит на месте, а сеть каждый раз ложится по-разному, потому что каждая выборка своя. «95 %» — свойство способа забрасывать: из ста забросов около 95 накроют рыбу. Про конкретный заброс мы не знаем, попал ли он, — знаем только, что способ надёжный.
:::

::: figure ci-coverage
Двадцать пять случайных выборок по 30 доставок и их 95 %-е интервалы. Пунктир — настоящее среднее всех доставок. Почти все интервалы его накрывают; красный — тот случай из двадцати, когда метод промахнулся.
:::

```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
k = ok.loc[ok["shop_id"] == "KZN-2", "actual_min"]
n, m, se = len(k), k.mean(), k.std() / np.sqrt(len(k))
print(f"n = {n}, среднее {m:.1f} мин, SE = {se:.2f}")
print(f"95 % ДИ: от {m - 1.96 * se:.1f} до {m + 1.96 * se:.1f} мин")
```

Теперь ответ звучит честно: «средняя доставка в KZN-2 — 37.8 минуты (95 % ДИ: 36.6–39.0)».

::: warn
Правильное толкование: «метод, которым построен интервал, в 95 % случаев даёт интервал, накрывающий настоящее значение». Неправильное, но частое: «настоящее среднее с вероятностью 95 % лежит в этом интервале». Почему вторая неверна: настоящее среднее — не случайное число, оно одно, и в этот интервал оно либо попало, либо нет. Случаен сам интервал — в другой выборке он сдвинется, — поэтому 95 % относятся к методу, а не к конкретному интервалу. Для работы этой разницы хватает знать; для отчёта годится простая формулировка: «настоящее значение, скорее всего, где-то здесь».
:::

::: quiz
95-процентный доверительный интервал для среднего времени доставки — от 32 до 36 минут. Как это понимать?

- [x] Если много раз повторять выборку и строить так интервалы, примерно 95 % из них накроют настоящее среднее
  > 95 % — свойство метода. Про один конкретный интервал говорят «мы на 95 % уверены», понимая под этим надёжность процедуры.
- [ ] 95 % доставок длятся от 32 до 36 минут
  > Интервал — про **среднее**, а не про отдельные доставки. Они разбросаны гораздо шире.
- [ ] Среднее точно лежит в этом интервале
  > Гарантии нет: в 5 % случаев метод промахивается.
- [ ] Среднее равно 34, а 32 и 36 — ошибки округления
  > Границы — честная оценка неопределённости, а не округление.
:::

{{practice: ci-mean}}

## t вместо 1.96

Формула с 1.96 немного занижает ширину на маленьких выборках: $\sigma$ мы тоже оцениваем по данным и ошибаемся. Поправку даёт **распределение Стьюдента** (t-распределение) — у него хвосты толще, чем у нормального. Вместо 1.96 берут его квантиль:

```python
from scipy import stats
for n in (5, 10, 30, 100, 1000):
    print(f"n = {n:>4}: t = {stats.t.ppf(0.975, n - 1):.3f}")
```

При n = 5 множитель 2.78, а уже от сотни наблюдений — практически 1.96. В scipy есть готовая функция:

```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
k = ok.loc[ok["shop_id"] == "KZN-2", "actual_min"]
se = k.std() / np.sqrt(len(k))
lo, hi = stats.t.interval(0.95, len(k) - 1, loc=k.mean(), scale=se)
print(round(lo, 2), round(hi, 2))
```

Аргументы: уровень доверия, число степеней свободы ($n - 1$), центр (среднее) и масштаб (SE). Степени свободы — тот же $n - 1$, что в делителе стандартного отклонения выборки (урок «Стандартное отклонение: разброс одним числом» главы 4): одно число «потрачено» на оценку среднего. Для нас это просто $n - 1$; чем их меньше, тем шире t-множитель.

{{practice: t-interval, coverage-small}}

## Интервал для доли

Для доли $SE = \sqrt{p(1 - p)/n}$ (урок «Выборки и центральная предельная теорема»), и интервал строится так же: $p \pm 1.96 \cdot SE$. На маленьких выборках и долях около 0 или 1 эта формула ошибается (может даже выйти за пределы 0–1). Надёжнее **интервал Уилсона** из библиотеки statsmodels:

```python
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = ok["actual_min"] > ok["promised_min"]
lo, hi = proportion_confint(late.sum(), len(late), method="wilson")
print(f"доля опозданий {late.mean():.3f}, 95 % ДИ {lo:.3f}–{hi:.3f}")
```

`proportion_confint(успехов, всего, method="wilson")` возвращает границы интервала.

::: predict
```python static
from statsmodels.stats.proportion import proportion_confint
lo, hi = proportion_confint(0, 20, method="wilson")
print(lo == 0, hi > 0)
```

- `True False`
- [x] `True True`
- `False True`

Почему: 0 опозданий из 20 не значит, что опаздывать невозможно. Интервал Уилсона начинается с нуля, но верхняя граница — около 16 %: при такой маленькой выборке настоящая доля может быть заметной. Простая формула дала бы интервал нулевой ширины — это неверно.
:::

{{practice: p-wilson, courier-ci}}

## Ширина интервала

От чего зависит ширина:

- **размер выборки** — сужается как $\sqrt{n}$ (вчетверо больше данных — вдвое уже);
- **разброс данных** — чем больше $\sigma$, тем шире;
- **уровень доверия** — 99 % шире 95 %, 90 % уже. Чем увереннее хотим быть, тем шире «сеть».

```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
k = d.loc[(d["shop_id"] == "KZN-2") & d["actual_min"].between(1, 299), "actual_min"]
se = k.std() / np.sqrt(len(k))
for level in (0.90, 0.95, 0.99):
    lo, hi = stats.t.interval(level, len(k) - 1, loc=k.mean(), scale=se)
    print(f"{level:.0%}: {lo:.1f}–{hi:.1f} (ширина {hi - lo:.2f})")
```

Интервалы удобно показывать на графике точкой с «усами» — `ax.errorbar`. Тонкость: `yerr` — это **расстояния** от точки вниз и вверх, а не сами границы:

```python
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
d = pd.read_csv("deliveries.csv")
k = d.loc[(d["shop_id"] == "KZN-2") & d["actual_min"].between(1, 299), "actual_min"]
se = k.std() / np.sqrt(len(k))
levels = [0.90, 0.95, 0.99]
lo, hi = stats.t.interval(levels, len(k) - 1, loc=k.mean(), scale=se)
fig, ax = plt.subplots(figsize=(6, 3))
ax.errorbar(["90 %", "95 %", "99 %"], [k.mean()] * 3, yerr=[k.mean() - lo, hi - k.mean()], fmt="o", capsize=4)
ax.set_ylabel("среднее время, мин")
```

`yerr=[вниз, вверх]` — два массива расстояний; для симметричного интервала можно передать один. `capsize` рисует «шляпки» на концах усов.

{{practice: widths, errorbars}}

## Разберём вместе: интервал по пяти доставкам руками

Новый курьер сделал пять доставок: 30, 35, 40, 28 и 42 минуты. Какое у него среднее время?

1. Среднее: (30 + 35 + 40 + 28 + 42) / 5 = **35**.
2. Отклонения от среднего: −5, 0, 5, −7, 7; квадраты: 25, 0, 25, 49, 49 — сумма 148.
3. Стандартное отклонение выборки (делим на n − 1 = 4): √(148 / 4) = √37 ≈ **6.08**.
4. SE = 6.08 / √5 ≈ **2.72**.
5. Множитель: для n = 5 — не 1.96, а t с 4 степенями свободы: `stats.t.ppf(0.975, 4)` ≈ **2.78**.
6. Интервал: 35 ± 2.78 × 2.72 = 35 ± 7.6 → **от 27.4 до 42.6** минуты.

С множителем 1.96 вышло бы 35 ± 5.3 — интервал на треть уже и обманчиво уверенный. На пяти наблюдениях SE сама оценена неточно, и t-множитель честно расширяет интервал.

::: figure ci-t-vs-z
Два интервала по одним и тем же пяти доставкам: с t-множителем 2.78 и с 1.96. Точки внизу — сами доставки. На маленькой выборке 1.96 даёт обманчиво узкий интервал.
:::

```python
import numpy as np
from scipy import stats
x = np.array([30, 35, 40, 28, 42])
se = x.std(ddof=1) / np.sqrt(len(x))
print(round(se, 2), round(stats.t.ppf(0.975, len(x) - 1), 2))
print(np.round(stats.t.interval(0.95, len(x) - 1, loc=x.mean(), scale=se), 1))
```

Что получилось: по пяти доставкам можно сказать только «где-то между 27 и 43 минутами». Это не провал анализа — это честный ответ, и он говорит, что для решения о курьере нужно больше данных.

## Бутстрэп: интервал для чего угодно

Для медианы, квантиля или любой другой статистики простой формулы нет. Выручает **бутстрэп** (bootstrap): «вытащить себя за шнурки». Идея:

1. Сделать из выборки новую выборку того же размера, выбирая строки **с возвращением** (одна и та же строка может попасть несколько раз).
2. Посчитать на ней статистику (например, медиану).
3. Повторить тысячи раз — получится распределение статистики.
4. 2.5-й и 97.5-й перцентили этого распределения — 95 %-й интервал.

::: tip Аналогия
Повар пробует суп одной ложкой и хочет понять, насколько можно верить пробе. Сварить суп заново нельзя, но можно много раз зачерпнуть из той же кастрюли и посмотреть, как сильно отличаются пробы. Бутстрэп так же «черпает» из нашей выборки, раз других данных нет. Хромает аналогия в одном: если сама кастрюля не похожа на остальные (выборка смещена), никакие пробы из неё этого не покажут.
:::

::: figure bootstrap-steps
Бутстрэп на пяти доставках нового курьера (30, 35, 40, 28 и 42 минуты — их интервал мы только что посчитали руками): перевыборки с повторами, медиана каждой, распределение 5 000 медиан и его средние 95 % — интервал. На пяти точках интервал почти во всю выборку — данных мало, и бутстрэп это честно показывает.
:::

```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299) & (d["shop_id"] == "KZN-2"), "actual_min"].to_numpy()
rng = np.random.default_rng(0)
boot = [np.median(rng.choice(t, size=len(t), replace=True)) for _ in range(5000)]
lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"медиана {np.median(t)}, 95 % бутстрэп-ДИ: {lo}–{hi}")
```

`replace=True` — выбор с возвращением. `np.percentile(arr, [2.5, 97.5])` — два перцентиля сразу.

Бутстрэп требует только одного: выборка должна быть похожа на совокупность. Тогда перевыборки из неё ведут себя как новые выборки из совокупности.

{{practice: bootstrap}}

## Интервал для разницы

Чаще всего нас интересует не одно значение, а **разница** между группами: «в снег опаздывают чаще?» Интервал для разницы двух долей:

$$
(p_1 - p_2) \pm 1.96 \cdot \sqrt{\frac{p_1(1 - p_1)}{n_1} + \frac{p_2(1 - p_2)}{n_2}}
$$

```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
snow = ok["weather"] == "снег"
p1, n1 = ok.loc[snow, "late"].mean(), snow.sum()
p2, n2 = ok.loc[~snow, "late"].mean(), (~snow).sum()
diff = p1 - p2
se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
print(f"разница {diff * 100:.1f} п.п., 95 % ДИ {(diff - 1.96 * se) * 100:.1f}…{(diff + 1.96 * se) * 100:.1f} п.п.")
```

Почему под корнем сумма: ошибки двух независимых долей складываются не сами, а как дисперсии — квадраты SE. Поэтому SE разницы — корень из суммы квадратов двух SE, и она больше каждой из них, но меньше их суммы.

Ноль не попал в интервал — значит, разница, скорее всего, не случайна: в снег действительно опаздывают чаще. Насколько чаще — от 4 до 19 процентных пунктов; интервал широкий, потому что снежных доставок всего 166.

Это первый шаг к проверке гипотез: «ноль вне интервала» почти то же самое, что «тест показал значимую разницу».

::: quiz
95 %-й интервал для разницы долей опозданий «снег минус остальная погода» — от 4 до 19 п.п. Какой вывод честный?

- [x] В снег опаздывают чаще, но насколько — известно грубо: от небольшой прибавки до очень заметной
  > Ноль вне интервала — разница, скорее всего, не случайна. Ширина интервала честно показывает, как мало снежных доставок.
- [ ] Раз интервал такой широкий, разницы, скорее всего, нет
  > Ширина говорит о точности, а не о наличии эффекта. Главное — что весь интервал лежит выше нуля.
- [ ] В снег опаздывают от 4 до 19 % доставок
  > Интервал построен для **разницы** долей, а не для самой доли опозданий в снег.
- [ ] Разница точно равна середине интервала
  > Середина — лишь лучшая оценка. Настоящая разница может оказаться где угодно в интервале, а изредка и вне его.
:::

{{practice: diff-ci}}

::: warn Типичные ошибки
- **Интервал для одной доставки.** ДИ — про среднее, а не про то, сколько займёт следующая доставка; отдельные доставки разбросаны гораздо шире.
- **1.96 на маленькой выборке.** До нескольких десятков наблюдений — t-интервал.
- **Простая формула для доли около 0 или 1.** $p \pm 1.96 \cdot SE$ при 1 опоздании из 20 даст отрицательную границу; для долей — Уилсон.
- **«Интервалы пересекаются — значит, разницы нет».** Сравнивают интервал **разницы**, а не два интервала по отдельности.
:::

## Практика

## task: ci-mean | Интервал для среднего | warmup

Постройте 95 %-й ДИ для среднего времени доставки кофейни `PRM-1` (время 1–299 минут) по формуле «среднее ± 1.96 · SE». Сохраните `lo` и `hi` (2 знака).

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
p = ok.loc[ok["shop_id"] == "PRM-1", "actual_min"]

```

### check
```python
import numpy as _np
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
p = ok.loc[ok['shop_id'] == 'PRM-1', 'actual_min']
se = p.std() / _np.sqrt(len(p))
assert close(need('lo'), round(p.mean() - 1.96 * se, 2)) and close(need('hi'), round(p.mean() + 1.96 * se, 2)), f'lo, hi = {need("lo")}, {need("hi")}, а нужно {round(p.mean() - 1.96 * se, 2)}, {round(p.mean() + 1.96 * se, 2)}.'
```

### hint
`p` — Series времени доставок кофейни; `len(p)` — число доставок.

### hint
`se = p.std() / np.sqrt(len(p))`; границы — `p.mean() - 1.96 * se` и `p.mean() + 1.96 * se`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
p = ok.loc[ok["shop_id"] == "PRM-1", "actual_min"]
se = p.std() / np.sqrt(len(p))
lo = round(p.mean() - 1.96 * se, 2)
hi = round(p.mean() + 1.96 * se, 2)
```

### explain
PRM-1: 453 доставки, среднее 34.2 минуты, SE ≈ 0.53, интервал примерно 33.2–35.3. На такой выборке среднее известно с точностью около минуты — хотя отдельные доставки разбросаны на ±11 минут.

## task: t-interval | Через scipy | warmup

Постройте тот же интервал для `PRM-1` функцией `stats.t.interval` и сохраните `lo_t`, `hi_t` (2 знака), а в `t_mult` — множитель t для этой выборки (`stats.t.ppf(0.975, n − 1)`, 3 знака).

### starter
```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
p = ok.loc[ok["shop_id"] == "PRM-1", "actual_min"]

```

### check
```python
import numpy as _np
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
p = ok.loc[ok['shop_id'] == 'PRM-1', 'actual_min']
lo, hi = _st.t.interval(0.95, len(p) - 1, loc=p.mean(), scale=p.std() / _np.sqrt(len(p)))
assert close(need('lo_t'), round(lo, 2)) and close(need('hi_t'), round(hi, 2)), f'lo_t, hi_t = {need("lo_t")}, {need("hi_t")}.'
assert close(need('t_mult'), round(_st.t.ppf(0.975, len(p) - 1), 3)), f't_mult = {need("t_mult")}.'
```

### hint
`stats.t.interval(0.95, len(p) - 1, loc=p.mean(), scale=se)`.

### hint
Функция возвращает пару чисел: `lo, hi = stats.t.interval(...)`.

### solution
```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
p = ok.loc[ok["shop_id"] == "PRM-1", "actual_min"]
se = p.std() / np.sqrt(len(p))
lo, hi = stats.t.interval(0.95, len(p) - 1, loc=p.mean(), scale=se)
lo_t, hi_t = round(lo, 2), round(hi, 2)
t_mult = round(stats.t.ppf(0.975, len(p) - 1), 3)
```

### explain
При сотнях наблюдений множитель t почти равен 1.96, и интервалы совпадают до сотых.

## task: p-wilson | Интервал Уилсона | warmup

Соберите программу, которая выводит 95 %-й интервал Уилсона для 12 опозданий из 40 доставок (границы через пробел, 3 знака).

### parsons
```python
from statsmodels.stats.proportion import proportion_confint
late, n = 12, 40
lo, hi = proportion_confint(late, n, method="wilson")
print(round(lo, 3), round(hi, 3))
```

### check
```python
from statsmodels.stats.proportion import proportion_confint as _pc
lo, hi = _pc(12, 40, method='wilson')
assert _lines == [f'{round(lo, 3)} {round(hi, 3)}'], f'Сейчас: {_lines}'
```

### hint
Импорт — первым, вывод — последним.

### hint
`proportion_confint(12, 40, method="wilson")` возвращает две границы; печатайте их округлёнными через пробел.

## task: courier-ci | Интервалы по курьерам | base

Соберите таблицу `ci` по типу курьера со столбцами `n`, `late` (доля опозданий), `lo`, `hi` (границы интервала Уилсона, 95 %). Все доли — 3 знака.

### starter
```python
import pandas as pd
from statsmodels.stats.proportion import proportion_confint
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from statsmodels.stats.proportion import proportion_confint as _pc
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
g = o.groupby('courier')['late'].agg(['sum', 'size'])
c = need('ci', _pd.DataFrame)
if 'courier' in c.columns:
    c = c.set_index('courier')
assert list(c.columns) == ['n', 'late', 'lo', 'hi'], f'Столбцы: {list(c.columns)}.'
for k, r in g.iterrows():
    lo, hi = _pc(r['sum'], r['size'], method='wilson')
    assert c.loc[k, 'n'] == r['size'] and close(c.loc[k, 'late'], round(r['sum'] / r['size'], 3)), f'{k}: n или late не совпадают.'
    assert close(c.loc[k, 'lo'], round(lo, 3)) and close(c.loc[k, 'hi'], round(hi, 3)), f'{k}: границы {c.loc[k, "lo"]}–{c.loc[k, "hi"]}, а нужно {round(lo, 3)}–{round(hi, 3)}.'
```

### hint
`g = ok.groupby("courier")["late"].agg(["sum", "size"])` — опозданий и всего по группе.

### hint
Пройдите по строкам `for name, row in g.iterrows():` и посчитайте `proportion_confint(row["sum"], row["size"], method="wilson")`. Результаты соберите в список словарей и превратите в DataFrame.

### hint
Каркас: `rows = []`, в цикле `rows.append({"courier": name, "n": int(row["size"]), "share": ..., "lo": lo, "hi": hi})`, после цикла `pd.DataFrame(rows).set_index("courier")`.

### solution
```python
import pandas as pd
from statsmodels.stats.proportion import proportion_confint
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
g = ok.groupby("courier")["late"].agg(["sum", "size"])
rows = []
for name, r in g.iterrows():
    lo, hi = proportion_confint(r["sum"], r["size"], method="wilson")
    rows.append({"courier": name, "n": r["size"], "late": round(r["sum"] / r["size"], 3),
                 "lo": round(lo, 3), "hi": round(hi, 3)})
ci = pd.DataFrame(rows).set_index("courier")
ci
```

### explain
Интервалы трёх типов курьеров не пересекаются, и пешие отстоят от остальных очень далеко. Это уже почти доказательство, что разница не случайна.

## task: widths | Уровень доверия и ширина | base

Для времени доставки кофейни `UFA-1` (1–299 минут) постройте t-интервалы на уровнях 90 %, 95 % и 99 %. Сохраните в `widths` словарь «уровень → ширина интервала» (ключи 0.90, 0.95, 0.99; ширина — 2 знака).

### starter
```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
u = d.loc[d["actual_min"].between(1, 299) & (d["shop_id"] == "UFA-1"), "actual_min"]

```

### check
```python
import numpy as _np
import pandas as _pd
from scipy import stats as _st
d = _pd.read_csv('deliveries.csv')
u = d.loc[d['actual_min'].between(1, 299) & (d['shop_id'] == 'UFA-1'), 'actual_min']
se = u.std() / _np.sqrt(len(u))
want = {}
for lv in (0.90, 0.95, 0.99):
    lo, hi = _st.t.interval(lv, len(u) - 1, loc=u.mean(), scale=se)
    want[lv] = round(hi - lo, 2)
got = dict(need('widths'))
assert set(round(k, 2) for k in got) == {0.9, 0.95, 0.99}, f'Ключи: {list(got)}.'
assert all(close(got[k], want[round(k, 2)]) for k in got), f'widths = {got}, а нужно {want}.'
```

### hint
SE и число степеней свободы не зависят от уровня — посчитайте их до цикла.

### hint
Цикл `for level in (0.90, 0.95, 0.99):` — внутри `stats.t.interval(level, ...)` и ширина `hi - lo`.

### solution
```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
u = d.loc[d["actual_min"].between(1, 299) & (d["shop_id"] == "UFA-1"), "actual_min"]
se = u.std() / np.sqrt(len(u))
widths = {}
for level in (0.90, 0.95, 0.99):
    lo, hi = stats.t.interval(level, len(u) - 1, loc=u.mean(), scale=se)
    widths[level] = round(hi - lo, 2)
widths
```

### explain
90 % — 2.78 минуты, 95 % — 3.32, 99 % — 4.38. Чем увереннее мы хотим быть, тем шире интервал: за каждый «девяточный» пункт уверенности платим точностью. 95 % — договорённость, а не закон; для дорогих решений берут 99 %.

## task: bootstrap | Бутстрэп для медианы | base

Постройте 95 %-й бутстрэп-интервал для **медианы** времени доставки вело-курьеров (1–299 минут): 5 000 перевыборок с возвращением, `rng = np.random.default_rng(12)`. Сохраните `med`, `lo`, `hi`.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299) & (d["courier"] == "вело"), "actual_min"].to_numpy()
rng = np.random.default_rng(12)

```

### check
```python
import numpy as _np
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
t = d.loc[d['actual_min'].between(1, 299) & (d['courier'] == 'вело'), 'actual_min'].to_numpy()
assert close(need('med'), _np.median(t)), f'med = {need("med")}.'
lo, hi = need('lo'), need('hi')
assert lo <= _np.median(t) <= hi and 0 < hi - lo <= 4, f'Интервал {lo}–{hi} не похож на бутстрэп-ДИ медианы: он должен накрывать медиану и быть шириной в пару минут.'
assert 'choice(' in _code, 'Перевыборка — с возвращением: rng.choice(t, size=len(t), replace=True).'
```

### hint
`boot = [np.median(rng.choice(t, size=len(t), replace=True)) for _ in range(5000)]`.

### hint
`lo, hi = np.percentile(boot, [2.5, 97.5])`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299) & (d["courier"] == "вело"), "actual_min"].to_numpy()
rng = np.random.default_rng(12)
boot = [np.median(rng.choice(t, size=len(t), replace=True)) for _ in range(5000)]
med = np.median(t)
lo, hi = np.percentile(boot, [2.5, 97.5])
```

### explain
Медиана вело-доставок — 32 минуты, бутстрэп-интервал — 31–33. Для медианы нет простой формулы SE, а бутстрэп даёт интервал одной и той же схемой для любой статистики. Ступенчатые границы (целые минуты) — потому что медиана целых чисел сама почти всегда целая.

## task: errorbars | Интервалы на графике | plus

Нарисуйте долю опозданий по кофейням точками с «усами» 95 %-го интервала Уилсона (`ax.errorbar`), кофейни отсортированы по доле. Подпись оси Y — «доля опозданий».

### starter
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
g = ok.groupby("shop_id")["late"].agg(["sum", "size", "mean"]).sort_values("mean")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
m = o.groupby('shop_id')['late'].mean().sort_values()
ax = ax_of()
pts = [l for l in ax.lines if len(l.get_ydata()) == len(m)]
assert pts, 'Нужны точки ax.errorbar(x, y, yerr=..., fmt="o").'
ys = [float(v) for v in pts[0].get_ydata()]
assert all(close(a, b) for a, b in zip(ys, m.values)), 'Точки — доля опозданий по кофейням, по возрастанию.'
assert ax.collections, 'Не видно «усов» интервала: передайте yerr.'
assert ax.get_ylabel() == 'доля опозданий'
```

### hint
Границы для каждой кофейни: `lo, hi = proportion_confint(g["sum"], g["size"], method="wilson")` — функция принимает и Series.

### hint
`ax.errorbar(g.index, g["mean"], yerr=[g["mean"] - lo, hi - g["mean"]], fmt="o", capsize=4)` — `yerr` — расстояние вниз и вверх от точки.

### solution
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
g = ok.groupby("shop_id")["late"].agg(["sum", "size", "mean"]).sort_values("mean")
lo, hi = proportion_confint(g["sum"], g["size"], method="wilson")

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.errorbar(g.index, g["mean"], yerr=[g["mean"] - lo, hi - g["mean"]], fmt="o", capsize=4)
ax.set_ylabel("доля опозданий")
ax.set_title("Опоздания по кофейням с 95 % интервалами")
```

### explain
Интервалы соседних кофеен перекрываются — различия между ними могут быть случайными. А у KZN-2 нижняя граница выше верхних границ у трёх кофеен из пяти — это уже серьёзный сигнал.

## task: diff-ci | Интервал для разницы | plus

Постройте 95 %-й ДИ для разницы долей опозданий в часы пик (12, 13, 18, 19) и в остальные часы. Сохраните `diff` (пик минус остальные), `lo`, `hi` (все — в процентных пунктах, 1 знак) и `zero_inside` — попадает ли ноль в интервал.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
peak = ok["created"].dt.hour.isin([12, 13, 18, 19])

```

### check
```python
import numpy as _np
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
pk = o['created'].dt.hour.isin([12, 13, 18, 19])
p1, n1, p2, n2 = o.loc[pk, 'late'].mean(), pk.sum(), o.loc[~pk, 'late'].mean(), (~pk).sum()
se = _np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
df_ = p1 - p2
assert close(need('diff'), round(df_ * 100, 1)), f'diff = {need("diff")}, а нужно {round(df_ * 100, 1)}.'
assert close(need('lo'), round((df_ - 1.96 * se) * 100, 1)) and close(need('hi'), round((df_ + 1.96 * se) * 100, 1)), f'lo, hi = {need("lo")}, {need("hi")}.'
assert need('zero_inside') == bool(df_ - 1.96 * se <= 0 <= df_ + 1.96 * se), 'zero_inside — попадает ли 0 между lo и hi.'
```

### hint
Маска пика: `ok["created"].dt.hour.isin([12, 13, 18, 19])`.

### hint
Как в примере со снегом: `p1, n1` — для пика, `p2, n2` — для остальных; `se = np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
peak = ok["created"].dt.hour.isin([12, 13, 18, 19])
p1, n1 = ok.loc[peak, "late"].mean(), peak.sum()
p2, n2 = ok.loc[~peak, "late"].mean(), (~peak).sum()
se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
d_ = p1 - p2
diff = round(d_ * 100, 1)
lo = round((d_ - 1.96 * se) * 100, 1)
hi = round((d_ + 1.96 * se) * 100, 1)
zero_inside = bool(lo <= 0 <= hi)
```

### explain
В часы пик опаздывает 31.4 % доставок, в остальное время — 18.0 %: разница 13.3 п.п., интервал 9.4–17.3. Ноль далеко за пределами — эффект пика устойчивый. Нижняя граница (9 п.п.) полезнее для планирования, чем точечная оценка: «как минимум на 9 пунктов больше» — это то, на что можно опереться.

## task: coverage-small | Когда 95 % — не 95 % | star

Проверьте, сколько на самом деле накрывает 95 %-й t-интервал на **маленьких** выборках из скошенных данных. «Совокупность» — все времена доставки 1–299 минут. Сделайте 4 000 выборок по 8 доставок (`rng = np.random.default_rng(13)`), для каждой постройте t-интервал и сохраните в `coverage` долю интервалов, накрывших настоящее среднее совокупности (3 знака).

### starter
```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"].to_numpy()
mu = t.mean()
rng = np.random.default_rng(13)

```

### check
```python
c = need('coverage')
if 0.905 <= c < 0.92:
    raise AssertionError(f'coverage = {c}. Похоже, σ выборки посчитана с делением на n: s.std() у массива numpy — ddof=0. Нужно s.std(ddof=1).')
assert 0.92 <= c <= 0.94, f'coverage = {c} — для 8 наблюдений из скошенных данных ожидается около 0.93.'
assert 't.interval' in _code or 't.ppf' in _code, 'Стройте именно t-интервал.'
```

### hint
В цикле: `s = rng.choice(t, size=8)`, `lo, hi = stats.t.interval(0.95, 7, loc=s.mean(), scale=s.std(ddof=1) / np.sqrt(8))`, засчитать попадание `lo <= mu <= hi`.

### hint
`ddof=1` — стандартное отклонение выборки с делением на n − 1, как у pandas `std()`.

### solution
```python
import numpy as np
import pandas as pd
from scipy import stats
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"].to_numpy()
mu = t.mean()
rng = np.random.default_rng(13)
hits = 0
for _ in range(4000):
    s = rng.choice(t, size=8)
    lo, hi = stats.t.interval(0.95, 7, loc=s.mean(), scale=s.std(ddof=1) / np.sqrt(8))
    hits += lo <= mu <= hi
coverage = round(hits / 4000, 3)
```

### explain
Обещанные 95 % держатся, когда выборка большая или данные близки к нормальным. На 8 наблюдениях из скошенного распределения ЦПТ ещё не сработала, и интервал промахивается чаще. Для маленьких выборок из несимметричных данных надёжнее бутстрэп или преобразование (логарифм).
