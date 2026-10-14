---
title: Ящик с усами и выбросы
lead: "Гистограмма хороша для одного распределения, но сравнить пять-шесть групп на ней трудно. Ящик с усами сжимает распределение до пяти чисел и ставит группы рядом. Разбираемся, как его читать, как он показывает выбросы и почему иногда нужно обрезать картинку, но не данные."
files: [deliveries.csv]
recap:
  - "Ящик с усами (boxplot): линия внутри — медиана, ящик — от Q1 до Q3 (середина данных, 50 %), усы — до крайних значений в пределах 1.5 × IQR, точки за усами — выбросы."
  - "`ax.boxplot(s)` — один ящик; `ax.boxplot([s1, s2], tick_labels=[\"a\", \"b\"])` — несколько рядом."
  - "`showfliers=False` — не рисовать точки-выбросы; `orientation=\"horizontal\"` — ящики лёжа."
  - "Огромные значения сжимают картинку: увеличьте нужную часть через `ax.set_ylim(0, 120)` — данные при этом не меняются."
  - "Числа к ящику: `s.quantile([0.25, 0.5, 0.75])`, по группам — `groupby(...)[col].quantile(0.75)`."
  - "Выбросы внутри своей группы: границу считают по группе через `transform`."
---

## Пять чисел вместо сотен

Ящик с усами (boxplot) показывает распределение пятью числами:

- **медиана** — линия внутри ящика;
- **ящик** — от первого квартиля Q1 (25 % значений меньше) до третьего Q3 (75 % меньше). В ящик попадает середина данных — половина всех значений;
- **усы** — тянутся до самого дальнего значения, которое ещё не выброс: не дальше 1.5 × IQR от края ящика (IQR = Q3 − Q1, правило из урока «Аномалии и проверка на здравый смысл»);
- **точки** за усами — выбросы по этому правилу.

::: figure boxplot-anatomy
Время доставок от 1 до 299 минут (1841 строка): ящик, медиана, усы и выбросы — те же числа, что в квантилях.
:::

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
fig, ax = plt.subplots(figsize=(4, 4))
ax.boxplot(d["distance_km"])
ax.set_title("Расстояние, км")
print(d["distance_km"].quantile([0.25, 0.5, 0.75]))
```

Ящик низко, а сверху — много точек: это тот же длинный хвост вправо, что мы видели на гистограмме в уроке «Распределения и гистограммы».

::: predict
```python static
import pandas as pd
s = pd.Series([10, 11, 12, 13, 50])
q1, q3 = s.quantile(0.25), s.quantile(0.75)
high = q3 + 1.5 * (q3 - q1)
print(high, (s > high).sum())
```

- `13.0 1`
- [x] `16.0 1`
- `16.0 0`

Почему: Q1 = 11, Q3 = 13, IQR = 2, верхняя граница 13 + 1.5 × 2 = 16. Значение 50 выше — это и будет точка над усом.
:::

### Разберём вместе: ящик для десяти доставок

Время десяти доставок курьера: 20, 24, 26, 28, 30, 31, 33, 35, 38, 75 минут (уже по возрастанию).

1. **Медиана** — середина между 5-м и 6-м значениями: (30 + 31) / 2 = **30.5**.
2. **Q1** (квантиль 0.25). Сначала находим его **номер** в отсортированном ряду: 1 + 0.25 × (10 − 1) = **3.25**. Номер дробный: Q1 стоит между 3-м значением (26) и 4-м (28), на четверти пути от 26 к 28. Расстояние между ними 2, четверть — 0.5: Q1 = 26 + 0.25 × 2 = **26.5**.
3. **Q3** (квантиль 0.75) — так же: номер 1 + 0.75 × 9 = **7.75**, между 7-м (33) и 8-м (35), на трёх четвертях пути: Q3 = 33 + 0.75 × 2 = **34.5**.
4. **IQR** = 34.5 − 26.5 = **8** минут — ширина ящика, в который попадает средняя половина доставок.
5. **Границы усов**: сверху 34.5 + 1.5 × 8 = **46.5**, снизу 26.5 − 1.5 × 8 = **14.5**.
6. Ус рисуется до самого дальнего значения **внутри** границ: сверху — до 38, снизу — до 20.
7. 75 выше 46.5 — это **точка-выброс** отдельно от уса.

::: figure quartile-position
Десять доставок по порядку. Номер квантиля — 1 + доля × (n − 1): медиана на месте 5.5, Q1 на месте 3.25 (четверть пути от 26 к 28), Q3 на месте 7.75 (три четверти пути от 33 к 35).
:::

Такой способ — брать точку на нужной доле пути между двумя соседними значениями — называется **линейной интерполяцией**. Так квантили считает `quantile` в pandas по умолчанию (и `np.percentile` в numpy). Если взять просто 3-е значение, получится 26 — тоже разумная оценка, но не та, что нарисует `boxplot`. На тысяче строк разница между способами почти исчезает.

```python
import pandas as pd
import matplotlib.pyplot as plt
x = pd.Series([20, 24, 26, 28, 30, 31, 33, 35, 38, 75])
q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
print(q1, med, q3, "верхняя граница:", q3 + 1.5 * (q3 - q1))
fig, ax = plt.subplots(figsize=(3, 4))
ax.boxplot(x)
```

Что здесь происходит:

- `x.quantile([0.25, 0.5, 0.75])` возвращает три числа сразу, и они раскладываются по трём переменным, как при распаковке кортежа;
- `ax.boxplot(x)` считает те же квартили сам: ящик от 26.5 до 34.5, линия медианы на 30.5.

Что получилось: ящик показывает «обычные» доставки курьера (от 26.5 до 34.5 минуты), а одна доставка за 75 минут вынесена точкой — её стоит разобрать отдельно: пробка, ошибка адреса или ошибка данных.

{{practice: box-km, quartiles}}

## Сравнение групп

Сила ящика — в сравнении. Время доставки по типу курьера, три ящика рядом:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
couriers = ["пеший", "вело", "авто"]
groups = [ok.loc[ok["courier"] == c, "actual_min"] for c in couriers]

fig, ax = plt.subplots(figsize=(6, 4))
ax.boxplot(groups, tick_labels=couriers)
ax.set_title("Время доставки по типу курьера")
ax.set_ylabel("минут")
```

`ax.boxplot` принимает список Series — по ящику на каждую — а `tick_labels` подписывает их. Список групп удобно собрать генератором списка (урок «Генераторы списков, zip, sorted»).

Если подписей много или они длинные (коды кофеен), ящики удобнее положить: `ax.boxplot(groups, tick_labels=couriers, orientation="horizontal")`. Тогда подписи идут по оси Y, а первый ящик из списка оказывается внизу.

::: note
`tick_labels=` появился в matplotlib 3.9, `orientation=` — в 3.10. В старых версиях и в старых примерах из интернета то же самое пишут как `labels=` и `vert=False`; если дома matplotlib старее и код падает с `TypeError`, замените аргументы или обновите библиотеку.
:::

Что видно: у пеших курьеров ящик выше — их типичная доставка дольше, хотя расстояния у них самые короткие. У всех групп есть точки сверху: долгие доставки бывают у всех.

::: tip
Сравнивая ящики, смотрите на три вещи: где медианы (кто типично быстрее), какой ширины ящики (у кого стабильнее) и сколько точек за усами (у кого чаще «провалы»).
:::

::: quiz
Ящик пеших курьеров сдвинут вверх относительно ящика авто, а по длине ящики почти одинаковые. Что это значит?

- [x] Доставки пеших в целом дольше, а разброс середины данных у обеих групп примерно одинаковый
  > Положение ящика — уровень: медиана у пеших 37 минут, у авто 31, края ящика тоже выше (31–45 против 25–39). Ящики при этом перекрываются на 31–39: часть доставок пеших быстрее части доставок авто. Длина — разброс середины данных: по 14 минут у обеих групп.
- [ ] Пеших курьеров больше
  > Ящик не показывает число наблюдений — его подписывают отдельно.
- [ ] У пеших больше выбросов
  > Выбросы — это точки за усами. Длина ящика о них не говорит.
- [ ] Пешие опаздывают всегда
  > Ящик показывает распределение времени, а не опоздания относительно обещания.
:::

{{practice: p-box, couriers, shops-sorted}}

## Обрезать картинку, а не данные

Если оставить в данных доставки на 1 000+ минут, ящики сожмутся в полоску у нуля:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv").dropna(subset=["actual_min"])
fig, axes = plt.subplots(1, 2, figsize=(9, 4))
axes[0].boxplot(d["actual_min"])
axes[0].set_title("Как есть")
axes[1].boxplot(d["actual_min"])
axes[1].set_ylim(0, 120)
axes[1].set_title("Масштаб 0–120 мин")
fig.tight_layout()
```

`set_ylim` меняет только видимую часть графика — как увеличительное стекло. Все значения по-прежнему участвуют в расчёте квартилей. Удалять строки ради красоты картинки нельзя: решения об аномалиях принимаются отдельно и записываются (урок «Аномалии и проверка на здравый смысл»).

Другой вариант — `showfliers=False`: ящики и усы те же, но точки-выбросы не рисуются, и масштаб подстраивается под ящики.

{{practice: zoom}}

## Числа к ящикам

Ящик — картинка, а в отчёт нужны числа. Квартили по группам:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
long = ok.groupby("courier")["actual_min"].quantile([0.25, 0.5, 0.75])
print(long)                      # до unstack: индекс (курьер, квантиль), 9 строк
q = long.unstack()               # после: курьер — строка, квантиль — столбец
q["iqr"] = q[0.75] - q[0.25]
q
```

`quantile` со списком внутри `groupby` даёт многоуровневый индекс (курьер, квантиль). `unstack()` разворачивает второй уровень в столбцы — получается аккуратная таблица.

::: warn Типичные ошибки
- **Выброс = ошибка.** Точка за усом — повод посмотреть, а не удалить: долгие доставки в снег настоящие.
- **Удалить данные ради картинки.** Чтобы увеличить ящик, ограничьте ось (`set_ylim`), данные не трогайте.
- **Ящики групп разного размера без числа наблюдений.** Ящик по 10 доставкам и по 900 выглядят одинаково уверенно — подпишите n.
- **Общая граница выбросов для всех групп.** Пешая доставка за 60 минут — норма, авто — нет; границы считают внутри группы.
:::

{{practice: spread}}

## Выбросы внутри группы

Доставка за 60 минут — выброс для авто-курьера, но вполне обычна для пешего на дальнее расстояние. Поэтому выбросы часто ищут **внутри группы**: граница своя для каждого типа курьера. Тут снова помогает `transform` (урок «Пропуски») — он возвращает значение группы для каждой строки:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
g = ok.groupby("courier")["actual_min"]
q1 = g.transform(lambda s: s.quantile(0.25))
q3 = g.transform(lambda s: s.quantile(0.75))
ok["high"] = q3 + 1.5 * (q3 - q1)
ok["slow"] = ok["actual_min"] > ok["high"]
ok.groupby("courier")["slow"].agg(["sum", "mean"]).round(3)
```

`lambda s: s.quantile(0.25)` — короткая безымянная функция: «взять группу `s` и вернуть её квартиль». Здесь `s` — все значения `actual_min` одной группы (например, всех пеших доставок) в виде Series; pandas вызывает функцию по разу на каждую группу. Её можно было бы написать и через `def`, но для одной строки `lambda` удобнее.

::: figure group-fences
Границы Q3 + 1.5 × IQR, посчитанные внутри каждого типа курьера, против одной общей (59.5 минуты). Доставка за 62 минуты — выброс для авто и вело, но обычное дело для пешего. Справа — квартили каждой группы.
:::

::: warn Типичные ошибки
- **`agg` вместо `transform`.** `g.quantile(0.75)` вернёт по числу на курьера — три строки; сравнить их с 1 841 доставкой построчно нельзя. `transform` повторяет значение группы в каждой её строке.
- **Общая граница «на всякий случай».** С одной границей 59.5 минуты обычные дальние доставки пеших попадут в аномалии, а настоящие задержки вело (их граница 54.5) спрячутся.
:::

{{practice: far, slow}}

## Практика

## task: box-km | Ящик расстояний | warmup

Нарисуйте ящик с усами для `distance_km` с заголовком «Расстояние, км».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
km = _pd.read_csv('deliveries.csv')['distance_km']
ax = ax_of()
flat = {round(float(l.get_ydata()[0]), 6) for l in ax.lines if len(l.get_ydata()) == 2 and l.get_ydata()[0] == l.get_ydata()[1]}
assert round(km.median(), 6) in flat, 'На графике не видно медианы расстояния — нарисуйте ax.boxplot(d["distance_km"]).'
assert ax.get_title() == 'Расстояние, км', f'Заголовок сейчас {ax.get_title()!r}, а нужен «Расстояние, км» — буква в букву, с запятой.'
```

### hint
Как в первом примере урока: полотно и ось `fig, ax = plt.subplots()`, затем ящик для одного столбца.

### hint
`ax.boxplot(d["distance_km"])` и `ax.set_title("Расстояние, км")` — заголовок буква в букву, с запятой.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
fig, ax = plt.subplots(figsize=(4, 4))
ax.boxplot(d["distance_km"])
ax.set_title("Расстояние, км")
```

## task: quartiles | Квартили времени | warmup

Для доставок с временем 1–299 минут сохраните `q1`, `q3` и `iqr` времени доставки.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
a = _pd.read_csv('deliveries.csv')['actual_min']
t = a[a.between(1, 299)]
assert close(need('q1'), t.quantile(0.25)) and close(need('q3'), t.quantile(0.75)), f'q1, q3 = {need("q1")}, {need("q3")}.'
assert close(need('iqr'), t.quantile(0.75) - t.quantile(0.25)), f'iqr = {need("iqr")}.'
```

### hint
`t = d.loc[d["actual_min"].between(1, 299), "actual_min"]`.

### hint
`t.quantile(0.25)`, `t.quantile(0.75)`, `iqr = q3 - q1`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]
q1 = t.quantile(0.25)
q3 = t.quantile(0.75)
iqr = q3 - q1
```

## task: p-box | Ящики по погоде | warmup

Соберите программу, которая рисует ящики времени доставки для ясной погоды и снега.

### parsons
```python
import pandas as pd
import matplotlib.pyplot as plt
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
groups = [ok.loc[ok["weather"] == w, "actual_min"] for w in ["ясно", "снег"]]
fig, ax = plt.subplots(figsize=(5, 4))
ax.boxplot(groups, tick_labels=["ясно", "снег"])
```

### check
```python
ax = ax_of()
assert [t.get_text() for t in ax.get_xticklabels()] == ['ясно', 'снег']
```

### hint
Сначала отфильтровать данные, потом собрать группы, потом рисовать.

### hint
`ax.boxplot` принимает **список** групп; подписи — `tick_labels=["ясно", "снег"]`.

## task: couriers | Курьеры рядом | base

Нарисуйте ящики времени доставки (1–299 минут) для курьеров в порядке «пеший», «вело», «авто», без точек-выбросов. Подпишите ось Y: «минут». Сохраните в `medians` словарь «тип курьера → медиана».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
ax = ax_of()
assert [t.get_text() for t in ax.get_xticklabels()] == ['пеший', 'вело', 'авто'], 'Порядок и подписи ящиков: пеший, вело, авто (tick_labels).'
assert not any(l.get_marker() not in ('None', None, '') and len(l.get_xdata()) > 0 and l.get_linestyle() in ('None', '') for l in ax.lines), 'Точки-выбросы рисовать не нужно: showfliers=False.'
assert ax.get_ylabel() == 'минут'
want = ok.groupby('courier')['actual_min'].median().to_dict()
got = dict(need('medians'))
assert set(got) == set(want) and all(close(got[k], want[k]) for k in want), f'medians = {got}.'
```

### hint
`groups = [ok.loc[ok["courier"] == c, "actual_min"] for c in ["пеший", "вело", "авто"]]`.

### hint
`ax.boxplot(groups, tick_labels=[...], showfliers=False)`. Медианы — `ok.groupby("courier")["actual_min"].median().to_dict()`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
couriers = ["пеший", "вело", "авто"]
groups = [ok.loc[ok["courier"] == c, "actual_min"] for c in couriers]
fig, ax = plt.subplots(figsize=(6, 4))
ax.boxplot(groups, tick_labels=couriers, showfliers=False)
ax.set_ylabel("минут")
medians = ok.groupby("courier")["actual_min"].median().to_dict()
```

### explain
Медианы: пеший — 37 минут, вело — 32, авто — 31. У пеших вверх сдвинута не только медиана, но и оба края ящика (Q1 31 против 25 у авто, Q3 45 против 39): медленнее у них и «быстрые», и «медленные» доставки. Без выбросов (`showfliers=False`) картинка спокойнее и сравнение групп читается лучше.

## task: far | Дальние доставки | base

По правилу 1.5 × IQR найдите верхнюю границу расстояния `high` и сохраните в `n_far` число доставок дальше неё, а в `far_share` — их долю в процентах (1 знак).

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
km = _pd.read_csv('deliveries.csv')['distance_km']
q1, q3 = km.quantile(0.25), km.quantile(0.75)
hi = q3 + 1.5 * (q3 - q1)
assert close(need('high'), hi), f'high = {need("high")}, а нужно {hi}.'
assert need('n_far') == (km > hi).sum(), f'n_far = {need("n_far")}.'
assert close(need('far_share'), round((km > hi).mean() * 100, 1)), f'far_share = {need("far_share")}.'
```

### hint
Квартили расстояния: `q1 = d["distance_km"].quantile(0.25)`, `q3 = ...quantile(0.75)`.

### hint
`high = q3 + 1.5 * (q3 - q1)`; `n_far = (d["distance_km"] > high).sum()`; доля — `.mean() * 100`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
km = d["distance_km"]
q1, q3 = km.quantile(0.25), km.quantile(0.75)
high = q3 + 1.5 * (q3 - q1)
n_far = (km > high).sum()
far_share = round((km > high).mean() * 100, 1)
```

### explain
Дальние доставки — не ошибка, а реальные заказы. Но их стоит рассматривать отдельно: по ним обещанное время другое, и курьеры на них — в основном авто.

## task: zoom | Увеличить, не удаляя | base

Нарисуйте ящик для **всех** непустых значений `actual_min` (аномалии не удаляйте) и ограничьте видимую часть оси Y диапазоном от 0 до 120.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
a = _pd.read_csv('deliveries.csv')['actual_min'].dropna()
ax = ax_of()
flat = {round(float(l.get_ydata()[0]), 6) for l in ax.lines if len(l.get_ydata()) == 2 and l.get_ydata()[0] == l.get_ydata()[1]}
assert round(a.median(), 6) in flat, 'Медиана ящика не совпадает с медианой всех значений — данные удалять не нужно, только dropna.'
lo, hi = ax.get_ylim()
assert abs(lo) < 1e-9 and abs(hi - 120) < 1e-9, f'Видимый диапазон оси Y: {lo}–{hi}. Нужно ax.set_ylim(0, 120).'
```

### hint
`ax.boxplot` не любит пропуски — уберите их `dropna()`, но аномально большие значения оставьте.

### hint
`ax.boxplot(d["actual_min"].dropna())`, затем `ax.set_ylim(0, 120)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
fig, ax = plt.subplots(figsize=(4, 4))
ax.boxplot(d["actual_min"].dropna())
ax.set_ylim(0, 120)
ax.set_title("Время доставки, видимая часть 0–120")
```

### explain
Есть два способа не дать аномалиям сплющить график: удалить их из данных или оставить данные целыми и ограничить видимую область. Здесь второй. Ящик и усы считаются по всем 1852 доставкам, включая пять значений больше 120 минут (максимум — 1281), а `set_ylim(0, 120)` только приближает картинку. Поэтому медиана (33 мин) и квартили (27 и 40 мин) на графике те же, что посчитаны по полным данным. Подпись «видимая часть 0–120» обязательна: читатель должен знать, что часть точек осталась за кадром.

## task: spread | Таблица разброса по погоде | base

Для доставок с временем 1–299 минут соберите `spread` — таблицу по погоде со столбцами `q1`, `median`, `q3`, `iqr`, отсортированную по медиане по убыванию.

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
ok = d[d['actual_min'].between(1, 299)]
g = ok.groupby('weather')['actual_min']
s = need('spread', _pd.DataFrame)
if 'weather' in s.columns:
    s = s.set_index('weather')
assert list(s.columns) == ['q1', 'median', 'q3', 'iqr'], f'Столбцы: {list(s.columns)}.'
for col, w in (('q1', g.quantile(0.25)), ('median', g.median()), ('q3', g.quantile(0.75))):
    assert all(close(s.loc[k, col], w[k]) for k in w.index), f'Столбец {col} не совпадает.'
assert all(close(s.loc[k, 'iqr'], s.loc[k, 'q3'] - s.loc[k, 'q1']) for k in s.index), 'iqr = q3 - q1.'
assert list(s['median']) == sorted(s['median'], reverse=True), 'Отсортируйте по медиане по убыванию.'
```

### hint
Сгруппируйте время по погоде и посчитайте три числа — Q1, медиану и Q3 — по отдельности. Каждое даст Series «погода → число»; из трёх Series соберите таблицу, потом добавьте `iqr` и отсортируйте.

### hint
`g = ok.groupby("weather")["actual_min"]`; у группы есть `g.quantile(0.25)`, `g.median()`, `g.quantile(0.75)`. Таблица из нескольких Series — `pd.DataFrame({"q1": ..., "median": ..., "q3": ...})`.

### hint
Почти готово: `spread = pd.DataFrame({"q1": g.quantile(0.25), "median": g.median(), "q3": g.quantile(0.75)})`, затем `spread["iqr"] = ...` и `spread = spread.sort_values(..., ascending=False)`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
g = ok.groupby("weather")["actual_min"]
spread = pd.DataFrame({"q1": g.quantile(0.25), "median": g.median(), "q3": g.quantile(0.75)})
spread["iqr"] = spread["q3"] - spread["q1"]
spread = spread.sort_values("median", ascending=False)
spread
```

### explain
Медиана выше всего в снег (36 минут) и в дождь (35), ниже — в ясную и облачную погоду (32). IQR у снега самый широкий — 14 минут: в снег не только дольше, но и непредсказуемее. Для обещания гостю важна именно ширина: обещать надо не медиану, а что-то ближе к Q3.

Ту же таблицу можно собрать именованными агрегатами: `ok.groupby("weather").agg(q1=("actual_min", lambda s: s.quantile(0.25)), ...)`. Здесь `s` — все значения `actual_min` одной группы (например, всех доставок в снег), а `lambda` возвращает для неё одно число. Подробнее про `lambda` с группами — в разделе «Выбросы внутри группы».

Частая ошибка — забыть `ascending=False`: тогда сверху окажется самая быстрая погода, а проверка попросит сортировку по убыванию.

## task: slow | Медленные внутри своей группы | plus

Найдите доставки, которые медленные **для своего типа курьера**: время выше `Q3 + 1.5 × IQR` своей группы (только время 1–299 минут). Добавьте в `ok` столбец `slow` и сохраните в `slow_by` словарь «тип курьера → число медленных доставок».

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
o = d[d['actual_min'].between(1, 299)].copy()
g = o.groupby('courier')['actual_min']
q1 = g.transform(lambda s: s.quantile(0.25))
q3 = g.transform(lambda s: s.quantile(0.75))
slow = o['actual_min'] > q3 + 1.5 * (q3 - q1)
okk = need('ok', _pd.DataFrame)
assert 'slow' in okk.columns, 'Нет столбца slow.'
assert (okk['slow'].values == slow.values).all(), 'slow не совпадает: границу нужно считать внутри каждой группы курьеров.'
want = {k: int(v) for k, v in slow.groupby(o['courier']).sum().items()}
got = {k: int(v) for k, v in dict(need('slow_by')).items()}
assert got == want, f'slow_by = {got}, а нужно {want}.'
```

### hint
`g = ok.groupby("courier")["actual_min"]`, `q1 = g.transform(lambda s: s.quantile(0.25))` — то же для Q3.

### hint
`ok["slow"] = ok["actual_min"] > q3 + 1.5 * (q3 - q1)`; подсчёт — `ok.groupby("courier")["slow"].sum()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
g = ok.groupby("courier")["actual_min"]
q1 = g.transform(lambda s: s.quantile(0.25))
q3 = g.transform(lambda s: s.quantile(0.75))
ok["slow"] = ok["actual_min"] > q3 + 1.5 * (q3 - q1)
slow_by = ok.groupby("courier")["slow"].sum().to_dict()
```

### explain
Медленных «для своей группы» больше всего у пеших (26) и вело (23), у авто — 8. По общей границе (для всех вместе, 59.5 минуты) медленными было бы 65 доставок, из них 43 — пешие: общая граница во многом просто повторила бы «пешие медленнее». Границы внутри группы находят то, что необычно **для этого курьера**.

## task: shops-sorted | Кофейни по медиане | star

Нарисуйте горизонтальные ящики времени доставки (1–299 минут) по кофейням, без выбросов, упорядоченные по медиане: самая медленная кофейня — наверху. Подписи — коды кофеен. У пяти кофеен медиана одинаковая, и порядок между ними может быть любым — так и должно быть; важно, какая кофейня окажется наверху.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
med = ok.groupby('shop_id')['actual_min'].median()
ax = ax_of()
labels = [t.get_text() for t in ax.get_yticklabels()]
assert sorted(labels) == sorted(med.index), f'Подписи по оси Y: {labels}. Нужны ящики лёжа: orientation="horizontal", подписи — коды кофеен.'
vals = [med[k] for k in labels]
assert vals == sorted(vals), 'Порядок не по медиане: у горизонтальных ящиков первый — внизу, поэтому сортируйте по возрастанию медианы.'
assert labels[-1] == 'KZN-2' or med[labels[-1]] == med.max(), 'Наверху должна быть самая медленная кофейня.'
```

### hint
Порядок кофеен: `order = ok.groupby("shop_id")["actual_min"].median().sort_values().index`. Группы — генератором списка по `order`.

### hint
Ящики лёжа — `orientation="horizontal"` (раздел «Сравнение групп»); первый ящик из списка окажется внизу, поэтому сортируйте по возрастанию медианы.

### hint
`ax.boxplot(groups, tick_labels=list(order), orientation="horizontal", showfliers=False)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
order = ok.groupby("shop_id")["actual_min"].median().sort_values().index
groups = [ok.loc[ok["shop_id"] == s, "actual_min"] for s in order]
fig, ax = plt.subplots(figsize=(7, 4))
ax.boxplot(groups, tick_labels=list(order), orientation="horizontal", showfliers=False)
ax.set_xlabel("минут")
ax.set_title("Время доставки по кофейням")
```

### explain
Одна кофейня заметно медленнее остальных — у неё сдвинут весь ящик, а не только хвост. Значит, дело не в редких сбоях, а в чём-то постоянном: например, в сборке заказа. Проверим это в проекте.
