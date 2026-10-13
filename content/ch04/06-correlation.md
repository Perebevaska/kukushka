---
title: "Связи: рассеяние и корреляция"
lead: "Чем дальше везти, тем дольше доставка — это очевидно. А насколько сильно? И связана ли сумма заказа со временем? Диаграмма рассеяния показывает связь двух чисел глазами, коэффициент корреляции — одним числом. Разбираемся, когда этому числу можно верить и почему связь — ещё не причина."
files: [deliveries.csv]
recap:
  - "Диаграмма рассеяния: `ax.scatter(x, y, s=8, alpha=0.4)` — точка на каждую строку. `alpha` спасает от слипания точек."
  - "Корреляция Пирсона: `x.corr(y)` — от −1 до 1. Около 0 — линейной связи нет, ±1 — точки лежат на прямой."
  - "Матрица корреляций: `df[[...]].corr()`. Сильные пары ищите глазами, затем смотрите на их scatter."
  - "Тысячи точек — `ax.hexbin(x, y, gridsize=20, mincnt=1)` и `fig.colorbar`: цвет соты — сколько точек внутри. Все пары признаков сразу — `pd.plotting.scatter_matrix(df[cols], diagonal=\"hist\")`."
  - "Выбросы ломают корреляцию — сначала очистка. Устойчивый вариант — корреляция Спирмена: Пирсон по рангам, `x.rank().corr(y.rank())`."
  - "Корреляция ловит только прямолинейную связь: у параболы она может быть около нуля."
  - "Смешение групп ослабляет или искажает связь — проверяйте корреляцию внутри групп."
  - "Корреляция ≠ причина: часто за обоими признаками стоит третий (число позиций → и сумма, и время сборки)."
---

## Диаграмма рассеяния

Чтобы увидеть связь двух чисел, каждую строку рисуют точкой: по X — одно число, по Y — другое.

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(ok["distance_km"], ok["actual_min"], s=8, alpha=0.4)
ax.set_xlabel("расстояние, км")
ax.set_ylabel("время, мин")
ax.set_title("Расстояние и время доставки")
```

- `s=8` — размер точки;
- `alpha=0.4` — прозрачность: там, где точки слипаются, цвет гуще, и видно, где их много.

Облако точек идёт вверх-вправо: чем дальше, тем дольше. Но разброс большой — при одном расстоянии время отличается в разы. Видно и «веер» из нескольких полос: это разные типы курьеров со своей скоростью.

{{practice: scatter}}

## Коэффициент корреляции

**Коэффициент корреляции Пирсона** — одно число о том, насколько точки ложатся на прямую:

- **1** — все точки на прямой, идущей вверх;
- **−1** — на прямой, идущей вниз;
- **0** — прямолинейной связи нет;
- по модулю около 0.3 — слабая связь, около 0.5 — заметная, 0.7 и выше — сильная. Это ориентиры, а не закон.

::: figure corr-shapes
Четыре условных облака по 40 точек и их r. Последнее — парабола: y полностью задан x, но связь не прямая, и коэффициент Пирсона около нуля.
:::

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
print(round(ok["distance_km"].corr(ok["actual_min"]), 2))
```

::: sql
`SELECT CORR(distance_km, actual_min) FROM deliveries` — в PostgreSQL, ClickHouse и многих других СУБД.
:::

### Разберём вместе: корреляция пяти доставок руками

Расстояние 1, 2, 3, 4, 5 км; время 20, 26, 29, 35, 40 минут. Средние — 3 км и 30 минут.

| км | мин | отклонение км | отклонение мин | произведение |
|---|---|---|---|---|
| 1 | 20 | −2 | −10 | +20 |
| 2 | 26 | −1 | −4 | +4 |
| 3 | 29 | 0 | −1 | 0 |
| 4 | 35 | +1 | +5 | +5 |
| 5 | 40 | +2 | +10 | +20 |

1. Сумма произведений — **49**: у далёких доставок оба отклонения со знаком «плюс», у близких — оба «минус», и произведения положительны.
2. Сумма квадратов отклонений: по км — 4 + 1 + 0 + 1 + 4 = **10**, по минутам — 100 + 16 + 1 + 25 + 100 = **242**.
3. r = 49 / √(10 × 242) = 49 / 49.2 ≈ **0.996** — точки почти на прямой.

Если бы у далёких доставок время было то больше, то меньше среднего, произведения разных знаков взаимно погасились бы и r оказался бы около нуля. Корреляция — это мера того, насколько согласованно два признака отклоняются от своих средних.

::: figure corr-quadrants
Пять доставок и линии средних делят плоскость на четверти. В зелёных произведение отклонений положительное, в красных — отрицательное; у нас все точки в зелёных, отсюда r ≈ 0.996.
:::

```python
import numpy as np
km = np.array([1, 2, 3, 4, 5])
mins = np.array([20, 26, 29, 35, 40])
dx, dy = km - km.mean(), mins - mins.mean()
print((dx * dy).sum(), (dx ** 2).sum(), (dy ** 2).sum())
print(round((dx * dy).sum() / np.sqrt((dx ** 2).sum() * (dy ** 2).sum()), 3), round(np.corrcoef(km, mins)[0, 1], 3))
```

Что здесь происходит:

- `dx`, `dy` — отклонения от средних, те же столбцы, что в таблице выше; первая строка вывода — 49.0, 10.0 и 242.0 (суммы из шагов 1 и 2);
- вторая строка — r по формуле из шага 3 и для сверки готовая функция numpy;
- `np.corrcoef(km, mins)` возвращает не одно число, а матрицу 2 × 2 — как `corr()` у таблицы из двух столбцов: на диагонали единицы (каждый ряд с самим собой), вне диагонали — r пары. `[0, 1]` — ячейка «строка 0, столбец 1», то есть «первый ряд со вторым». То же число даёт уже знакомое `pd.Series(km).corr(pd.Series(mins))`.

{{practice: r, p-corr}}

## Матрица корреляций

Чтобы не перебирать пары вручную, считают корреляцию всех со всеми — `corr()` у таблицы:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["delay"] = ok["actual_min"] - ok["promised_min"]
ok[["distance_km", "items", "amount", "actual_min", "delay", "rating"]].corr().round(2)
```

По диагонали — единицы (каждый признак идеально связан с собой). Что видно:

- `items` и `amount` — 0.95: больше позиций — больше сумма, это ожидаемо;
- `actual_min` и `rating` — около −0.5: дольше везём — ниже оценка;
- `distance_km` и `delay` — **отрицательная**: дальние доставки опаздывают реже. Неожиданно! Объяснение — в устройстве обещаний: на дальние заказы обещают 60 минут и отправляют авто.

Пропуски в `rating` не мешают: `corr` считает каждую пару по строкам, где известны оба значения.

{{practice: matrix}}

## Много точек и много пар: hexbin и scatter_matrix

У диаграммы рассеяния две слабости. Когда точек тысячи, они слипаются в пятно, и даже `alpha` не показывает, где их **больше всего**. А когда признаков пять, пар для рассеяния — десять, и рисовать их по одной долго. Для первого есть **hexbin**, для второго — **scatter_matrix**.

::: figure hexbin-matrix
Слева — `hexbin` по 1 841 доставке с крупными сотами (`gridsize=8`, в примере ниже — 20): непустых сот 45, в самой плотной — 372 доставки около 2 км и 35 минут; чем гуще цвет, тем больше доставок. Справа — сетка `scatter_matrix` для четырёх признаков: на диагонали гистограммы, под ней — точки пар (70 случайных доставок). Над диагональю здесь вместо точек — коэффициент r той же пары; в настоящей сетке там тоже точки, зеркально.
:::

### hexbin: соты вместо точек

`hexbin` делит плоскость на шестиугольные ячейки-соты и красит каждую по числу точек внутри. Это гистограмма, только двумерная: вместо корзин на оси — соты на плоскости.

::: tip Аналогия
Карта плотности населения не рисует каждого жителя точкой — их миллионы, и всё слилось бы. Она делит территорию на клетки и красит их: темнее — где людей больше. Где аналогия хромает: на карте клетки — это районы с границами по смыслу, а соты hexbin — просто одинаковые ячейки, их размер вы выбираете сами.
:::

Игрушечный пример: четыре доставки — (1 км, 1 у. е.), (1.1, 1), (1.2, 0.9) и (3, 3). При крупных сотах (`gridsize=2` — две соты по ширине) первые три точки попадают в одну ячейку, четвёртая — в другую. Счётчики сот — 3 и 1: левая сота темнее, и видно, что там «гуще», хотя точки в ней почти слились бы.

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(3, 3))
hb = ax.hexbin([1, 1.1, 1.2, 3], [1, 1, 0.9, 3], gridsize=2, mincnt=1)
print(hb.get_array())
```

На реальных данных:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(7, 4))
hb = ax.hexbin(ok["distance_km"], ok["actual_min"], gridsize=20, cmap="Blues", mincnt=1)
fig.colorbar(hb, ax=ax, label="доставок в соте")
ax.set_xlabel("расстояние, км")
ax.set_ylabel("время, мин")
ax.set_title("Больше всего доставок — около 1.8 км и 29 минут")
counts = hb.get_array()
print("сот:", len(counts), "| точек всего:", int(counts.sum()), "| в самой плотной:", int(counts.max()))
```

Что здесь происходит:

- `gridsize=20` — сколько сот укладывается по ширине; больше — мельче соты и детальнее картинка, но шумнее;
- `mincnt=1` — не рисовать пустые соты, иначе весь фон закрасится цветом «ноль»;
- `cmap="Blues"` — шкала цвета; `fig.colorbar(hb, …)` — легенда «цвет → число доставок»;
- `hb.get_array()` — счётчики непустых сот: их сумма равна числу точек (1 841).

Как читать: самая плотная сота — 81 доставка около 1.8 км и 29 минут. На схеме выше числа другие — 372 доставки около 2 км и 35 минут, — потому что там соты крупнее (`gridsize=8`): в большую соту попадает больше точек, а её центр — середина широкой ячейки, поэтому и координаты грубее. Само место скопления то же — короткие доставки примерно на полчаса; от размера сот зависят счёт в самой плотной соте и точность её координат. На обычном scatter этот центр тяжести не виден: там все области выглядят одинаково залитыми. Хвост дальних долгих доставок светлый — он есть, но редкий.

### scatter_matrix: все пары сразу

`pd.plotting.scatter_matrix` рисует сетку: в ячейке (строка i, столбец j) — рассеяние признака i против признака j, а на диагонали — гистограмма самого признака. Это «картинка» к матрице корреляций: число говорит, насколько сильна связь, сетка показывает её форму.

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
cols = ["distance_km", "items", "amount", "actual_min"]
axes = pd.plotting.scatter_matrix(ok[cols], figsize=(7, 7), alpha=0.3, diagonal="hist")
print(axes.shape)
```

Что здесь происходит:

- функция сама создаёт полотно и возвращает массив осей `axes` размером 4 × 4 — по одной на пару признаков;
- `diagonal="hist"` — на диагонали гистограммы; рассеяние признака с самим собой было бы бесполезной прямой;
- сетка симметрична: ячейка (1, 2) — та же пара, что (2, 1), только оси поменяны местами.

Как читать: `items` × `amount` — плотная «лестница» вверх (корреляция 0.95: почти один признак); `distance_km` × `actual_min` — облако-веер (0.48); `items` × `distance_km` — бесформенное пятно (0.01). На диагонали видно, что `distance_km` и `actual_min` скошены вправо, а `items` — целые значения 1–6 (столбики).

::: warn Типичные ошибки
- **hexbin без `mincnt=1`.** Пустые соты закрашиваются цветом минимума, и картинка превращается в сплошной прямоугольник.
- **Слишком мелкие соты.** При `gridsize=80` на 1 841 точке большинство сот содержат 1–2 доставки — получится шум вместо формы.
- **scatter_matrix на 15 признаков.** 225 крошечных графиков не прочитать; берите 4–6 признаков, отобранных по матрице корреляций или по вопросу.
- **Аномалии в scatter_matrix.** Одна доставка «1 281 минута» сожмёт все графики со временем в полоску — сначала очистка.
:::

{{practice: hexbin, pairs}}

## Ловушка 1: выбросы

Посчитаем ту же корреляцию, не убирая аномалии (доставки на 1 000+ минут и отрицательные):

```python
import pandas as pd
d = pd.read_csv("deliveries.csv").dropna(subset=["actual_min"])
ok = d[d["actual_min"].between(1, 299)]
print("с аномалиями:", round(d["distance_km"].corr(d["actual_min"]), 2))
print("без аномалий:", round(ok["distance_km"].corr(ok["actual_min"]), 2))
print("Спирмен с аномалиями:", round(d["distance_km"].rank().corr(d["actual_min"].rank()), 2))
```

Пять «забытых» заказов и несколько сбоев часов из почти двух тысяч строк уничтожили связь: 0.10 вместо 0.48. Коэффициент Пирсона очень чувствителен к выбросам.

**Корреляция Спирмена** сравнивает не сами значения, а их **ранги** — места в упорядоченном ряду. Ранги даёт метод `rank()`: самое маленькое значение получает 1, следующее — 2 и так далее. Доставка на 1 281 минуту становится просто «последней по скорости» и испортить картину сильно не может.

::: figure spearman-ranks
Условные шесть доставок, одна «забытая» на 1 281 минуту. По значениям Пирсон уходит в минус; по рангам выброс — просто 6-е место, и связь видна.
:::

::: note
Короткая запись — `x.corr(y, method="spearman")` — даёт то же самое. Внутри она использует библиотеку scipy (с ней мы подробно познакомимся в главе 5). Запись через `rank()` полезна тем, что показывает, как Спирмен устроен.
:::

::: quiz
Почему корреляция Спирмена почти не реагирует на доставку «за 1 281 минуту», а Пирсон — сильно?

- [x] Спирмен работает с рангами: огромное значение становится просто последним местом, и величина его отрыва не важна
  > У Пирсона в расчёт идут отклонения от среднего, и одно гигантское отклонение перевешивает сотни обычных. Ранг у самой долгой доставки один — последний, на сколько бы она ни затянулась.
- [ ] Спирмен сам удаляет выбросы перед расчётом
  > Ничего не удаляется: все строки участвуют, просто через ранги.
- [ ] Спирмен считается по медианам, а не по средним
  > Это Пирсон, применённый к рангам: средние там тоже есть, только средние рангов, а не минут.
- [ ] Спирмен ловит любую связь, а не только прямую
  > Он ловит монотонную связь «больше — значит больше». На параболе он, как и Пирсон, покажет около нуля.
:::

{{practice: spearman}}

## Ловушка 2: связь не прямая

Корреляция Пирсона ловит только **прямолинейную** связь. Если связь есть, но изогнутая, число может оказаться около нуля:

::: predict
```python static
import pandas as pd
x = pd.Series([-3, -2, -1, 0, 1, 2, 3])
y = x ** 2
print(round(x.corr(y), 2))
```

- `1.0`
- [x] `0.0`
- `-1.0`

Почему: y полностью определяется x, но связь в форме параболы: слева y падает, справа растёт. Прямая через такие точки горизонтальна — корреляция 0. Поэтому сначала смотрят на scatter, потом на число.
:::

Одно число r не говорит, **какой формы** связь: прямая, изгиб или «полка», после которой рост прекращается. Форму показывает картинка. Когда точек тысячи, удобнее не облако, а **линия медиан по корзинам**: делим X на интервалы (как в гистограмме) и в каждом считаем медиану Y. Прямая линия медиан — связь линейная, и r ей подходит; изгиб — r занижает или искажает связь.

{{practice: binned}}

## Ловушка 3: смешанные группы

В облаке «расстояние — время» смешаны три типа курьеров с разной скоростью. Внутри каждого типа связь гораздо сильнее, чем в общей куче:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(6, 4))
for c in ["пеший", "вело", "авто"]:
    t = ok[ok["courier"] == c]
    r = t["distance_km"].corr(t["actual_min"])
    ax.scatter(t["distance_km"], t["actual_min"], s=8, alpha=0.4, label=f"{c}: r = {r:.2f}")
ax.legend()
ax.set_xlabel("расстояние, км")
ax.set_ylabel("время, мин")
```

Что здесь происходит:

- цикл рисует **три** `scatter` на одних осях — по одному на тип курьера; matplotlib сам даёт каждому свой цвет;
- `t = ok[ok["courier"] == c]` — строки одного типа; `r` — корреляция только внутри них;
- `label=f"{c}: r = {r:.2f}"` — подпись этого набора точек; после цикла `ax.legend()` собирает подписи всех наборов в легенду. Без `label=` легенда будет пустой.

Раскраска по группам — простой способ увидеть, что облако на самом деле состоит из нескольких. Общая корреляция 0.48 «размыта» смешением, а внутри групп — 0.7–0.9.

::: note Если в выводе np.float64(0.88)
Если положить такие r в словарь и напечатать его, увидите `{'авто': np.float64(0.73), 'вело': np.float64(0.71), 'пеший': np.float64(0.88)}`. Это не ошибка: pandas возвращает число numpy, а numpy так показывает его тип внутри словарей и списков. Работать с ним можно как с обычным `float`, проверка его принимает. Для красивого вывода оберните в `float(...)` или печатайте значения по одному: `print(r)` покажет просто `0.88`.
:::

::: warn Типичные ошибки
- **Корреляция без картинки.** Одно число не покажет выбросы, кривую связь и смешанные группы — сначала рассеяние.
- **Близкая к нулю r = «связи нет».** Пирсон меряет только линейную связь; U-образная зависимость даст r ≈ 0.
- **Аномалии в данных.** Одно время «1440 минут» может сдвинуть r на десятые; либо очистите, либо возьмите Спирмена.
- **Сумма и позиции как два признака.** Корреляция 0.95 значит, что это почти один и тот же признак — не считайте их двумя независимыми причинами.
:::

{{practice: by-group, colored, confounder}}

## Ловушка 4: корреляция ≠ причина

Сумма заказа и время доставки связаны (корреляция около 0.2). Значит ли это, что дорогие заказы везут медленнее, потому что они дорогие? Нет. За обоими признаками стоит **третий** — число позиций: больше позиций → больше сумма и дольше сборка.

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
ok.groupby("items")[["amount", "actual_min"]].mean().round(1)
```

Такой третий признак называют **конфаундером** (смешивающим фактором). Классический пример: продажи мороженого и число солнечных ожогов растут вместе — но не мороженое вызывает ожоги, а жаркая погода стоит за обоими.

::: figure confounder
Число позиций связано и с суммой, и со временем сборки; связь «сумма — время» идёт через него. Проверяют её внутри заказов с одинаковым числом позиций.
:::

::: tip Аналогия
Два пассажира в одном вагоне метро одновременно разгоняются и тормозят, но ни один не толкает другого — обоих везёт поезд. Корреляция видит только то, что они движутся вместе, и не отличает «везёт поезд» от «один тянет другого». Где аналогия хромает: бывает, что один признак и правда тянет другой (дальше везти — дольше ехать), — корреляция просто не умеет сама различить эти случаи.
:::

::: warn
Корреляция говорит «эти числа меняются вместе», но не говорит, что одно вызывает другое. Причину можно доказать экспериментом (A/B-тест, глава 5) или аккуратным анализом с учётом конфаундеров. В отчёте пишите «связано», а не «влияет», если не проверяли.
:::

::: quiz
По кофейням корреляция между числом пирожных в витрине и выручкой — 0.7. Значит, если выставить больше пирожных, выручка вырастет?

- [x] Не обязательно: большие кофейни и витрину держат больше, и выручку имеют больше — общая причина в размере
  > Корреляция показывает совместное изменение, но не причину. Причинность проверяют экспериментом или сравнением внутри похожих групп.
- [ ] Да, 0.7 — сильная связь
  > Сила связи ничего не говорит о том, что здесь причина, а что следствие.
- [ ] Нет, корреляция 0.7 — это слабо
  > 0.7 — сильная связь по нашим ориентирам. Дело не в силе, а в том, что связь может быть не причинной.
- [ ] Да, если корреляция положительная
  > Знак показывает направление совместного изменения, а не то, что одно вызывает другое.
:::

## Практика

## task: scatter | Расстояние и время | warmup

Нарисуйте диаграмму рассеяния: по X — `distance_km`, по Y — `actual_min` (только время 1–299 минут), размер точек 8, прозрачность 0.4. Подпишите оси: «км» и «мин».

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
assert ax.collections, 'Нет точек: ax.scatter(...).'
pts = ax.collections[0].get_offsets()
assert len(pts) == len(ok), f'Точек {len(pts)}, а доставок с временем 1–299 — {len(ok)}.'
assert abs(ax.collections[0].get_alpha() - 0.4) < 1e-9, 'Прозрачность — alpha=0.4.'
assert ax.get_xlabel() == 'км' and ax.get_ylabel() == 'мин', f'Подписи осей: {ax.get_xlabel()!r}, {ax.get_ylabel()!r}.'
```

### hint
Фильтр времени: `ok = d[d["actual_min"].between(1, 299)]`.

### hint
`ax.scatter(ok["distance_km"], ok["actual_min"], s=8, alpha=0.4)`; подписи — `ax.set_xlabel("км")`, `ax.set_ylabel("мин")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(ok["distance_km"], ok["actual_min"], s=8, alpha=0.4)
ax.set_xlabel("км")
ax.set_ylabel("мин")
```

## task: r | Коэффициент корреляции | warmup

Сохраните в `r` корреляцию Пирсона между расстоянием и временем доставки (время 1–299 минут), округлённую до 2 знаков.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
want = round(ok['distance_km'].corr(ok['actual_min']), 2)
got = need('r')
if close(got, round(d['distance_km'].corr(d['actual_min']), 2)) and not close(got, want):
    raise AssertionError(f'r = {got} — посчитано вместе с аномалиями. Оставьте время 1–299 минут.')
assert close(got, want), f'r = {got}, а нужно {want}.'
```

### hint
`ok["distance_km"].corr(ok["actual_min"])`.

### hint
Округление — `round(..., 2)` вокруг всего выражения.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
r = round(ok["distance_km"].corr(ok["actual_min"]), 2)
```

## task: p-corr | Оценка и опоздание | warmup

Соберите программу, которая выводит корреляцию между опозданием и оценкой гостя (2 знака).

### parsons
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["delay"] = ok["actual_min"] - ok["promised_min"]
print(round(ok["delay"].corr(ok["rating"]), 2))
```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
want = round((ok['actual_min'] - ok['promised_min']).corr(ok['rating']), 2)
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Столбец `delay` нужно создать до того, как считать корреляцию.

### hint
`delay = actual_min − promised_min`; корреляция — `d["delay"].corr(d["rating"])`. Пропуски в оценках `corr` пропускает сам.

## task: matrix | Матрица корреляций | base

Для доставок с временем 1–299 минут постройте матрицу корреляций столбцов `distance_km`, `items`, `amount`, `actual_min`, `rating` и сохраните её в `cm`. В `strongest` сохраните **кортеж** из двух названий столбцов с самой сильной по модулю корреляцией (не считая диагонали), в порядке, в котором они идут в списке.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
cols = ["distance_km", "items", "amount", "actual_min", "rating"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
cols = ['distance_km', 'items', 'amount', 'actual_min', 'rating']
want = ok[cols].corr()
c = need('cm', _pd.DataFrame)
assert c.shape == (5, 5) and all(close(a, b, 1e-9) for a, b in zip(c.values.ravel(), want.values.ravel())), 'cm — ok[cols].corr().'
assert tuple(need('strongest')) == ('items', 'amount'), f'strongest = {need("strongest")}.'
```

### hint
`cm = ok[cols].corr()`. Самую сильную пару найдите глазами или перебором двух циклов по `cols` (пары `i < j`).

### hint
Перебор: `for i in range(len(cols)): for j in range(i + 1, len(cols)): v = abs(cm.iloc[i, j])` — запоминайте пару с наибольшим `v`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
cols = ["distance_km", "items", "amount", "actual_min", "rating"]
cm = ok[cols].corr()
best = 0
for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        if abs(cm.iloc[i, j]) > best:
            best = abs(cm.iloc[i, j])
            strongest = (cols[i], cols[j])
cm.round(2)
```

### explain
Самая сильная пара — `items` и `amount`, 0.95: сумма почти целиком определяется числом позиций. Следующая по силе — `actual_min` и `rating`, −0.51: чем дольше везли, тем ниже оценка. Связь расстояния и времени (0.48) слабее, чем можно было ожидать, — потому что в ней смешаны разные курьеры.

## task: spearman | Пирсон против Спирмена | base

Посчитайте корреляцию расстояния и времени по **всем** непустым `actual_min` (с аномалиями) двумя способами: Пирсона — в `r_pearson`, Спирмена — в `r_spearman` (оба — 2 знака). В `diff` — насколько Спирмен больше (2 знака).

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv").dropna(subset=["actual_min"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv').dropna(subset=['actual_min'])
p = round(d['distance_km'].corr(d['actual_min']), 2)
s = round(d['distance_km'].rank().corr(d['actual_min'].rank()), 2)
assert close(need('r_pearson'), p) and close(need('r_spearman'), s), f'r_pearson, r_spearman = {need("r_pearson")}, {need("r_spearman")}, а нужно {p}, {s}.'
assert close(need('diff'), round(s - p, 2)), f'diff = {need("diff")}.'
```

### hint
Спирмен — Пирсон по рангам: `d["distance_km"].rank().corr(d["actual_min"].rank())`.

### hint
Пирсон — обычный `.corr()`, Спирмен — тот же `.corr()`, но по рангам. Округлите оба коэффициента до 2 знаков, а `diff` посчитайте как разность уже округлённых значений. Ожидайте, что Спирмен выйдет заметно больше: рангам безразлично, длилась аномальная доставка 300 минут или 1281.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv").dropna(subset=["actual_min"])
r_pearson = round(d["distance_km"].corr(d["actual_min"]), 2)
r_spearman = round(d["distance_km"].rank().corr(d["actual_min"].rank()), 2)
diff = round(r_spearman - r_pearson, 2)
```

### explain
Спирмен почти не заметил аномалий, а Пирсон — заметил. Если корреляции Пирсона и Спирмена сильно расходятся, ищите выбросы.

## task: by-group | Связь внутри групп | base

Для доставок с временем 1–299 минут посчитайте корреляцию расстояния и времени **внутри** каждого типа курьера. Сохраните словарь `r_by` «тип курьера → корреляция» (2 знака), а в `r_all` — общую корреляцию (2 знака).

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
want = {c: round(t['distance_km'].corr(t['actual_min']), 2) for c, t in ok.groupby('courier')}
got = dict(need('r_by'))
assert set(got) == set(want) and all(close(got[k], want[k]) for k in want), f'r_by = {got}, а нужно {want}.'
assert close(need('r_all'), round(ok['distance_km'].corr(ok['actual_min']), 2)), f'r_all = {need("r_all")}.'
```

### hint
Цикл по группам: `for c, t in ok.groupby("courier"):` — `c` — тип курьера, `t` — его строки.

### hint
Внутри цикла: `r_by[c] = round(t["distance_km"].corr(t["actual_min"]), 2)`; общая — по всему `ok`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
r_by = {}
for c, t in ok.groupby("courier"):
    r_by[c] = round(t["distance_km"].corr(t["actual_min"]), 2)
r_all = round(ok["distance_km"].corr(ok["actual_min"]), 2)
```

### explain
Внутри каждого типа курьера связь сильная: 0.73 у авто, 0.71 у вело, 0.88 у пеших. А в целом — только 0.48. Разные курьеры ездят с разной скоростью, и общее облако «размывает» три чёткие линии. Это ловушка 3: прежде чем писать «связь слабая», проверьте группы.

## task: colored | Рассеяние по группам | base

Нарисуйте рассеяние «расстояние — время» (время 1–299 минут) отдельным цветом для каждого типа курьера, с легендой из названий типов.

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
assert len(ax.collections) == 3, f'Наборов точек {len(ax.collections)}, а нужно 3 — по одному scatter на тип курьера.'
assert sorted(len(c.get_offsets()) for c in ax.collections) == sorted(ok['courier'].value_counts().values), 'В каждом наборе — точки своего типа курьера.'
labels = sorted(t.get_text().split(':')[0] for t in ax.get_legend().get_texts()) if ax.get_legend() else []
assert labels == sorted(['пеший', 'вело', 'авто']), f'Легенда: {labels}.'
```

### hint
Цикл по типам, внутри — `ax.scatter(..., label=c)`; после цикла `ax.legend()`.

### hint
`for c, t in ok.groupby("courier"): ax.scatter(t["distance_km"], t["actual_min"], s=8, alpha=0.4, label=c)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(6, 4))
for c in ["пеший", "вело", "авто"]:
    t = ok[ok["courier"] == c]
    ax.scatter(t["distance_km"], t["actual_min"], s=8, alpha=0.4, label=c)
ax.legend()
ax.set_xlabel("км")
ax.set_ylabel("мин")
```

### explain
Три цвета показывают то, что числа уже сказали: у пеших облако круче (каждый километр дороже по времени), у авто — пологое. Общая корреляция смешивает эти три наклона.

## task: hexbin | Соты вместо точек | base

Для доставок с временем 1–299 минут нарисуйте `hexbin`: по X — расстояние, по Y — время, `gridsize=15`, без пустых сот (`mincnt=1`), со шкалой цветов. Подпишите оси «расстояние, км» и «время, мин». Сохраните в `max_cell` число доставок в самой плотной соте.

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
import numpy as _np
from matplotlib.figure import Figure as _Fig
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
ref = _Fig().subplots().hexbin(o['distance_km'], o['actual_min'], gridsize=15, mincnt=1).get_array()
ax = ax_of()
hb = [c for c in ax.collections if c.get_array() is not None]
assert hb, 'Не вижу сот: нарисуйте ax.hexbin(x, y, gridsize=15, mincnt=1).'
arr = _np.asarray(hb[0].get_array())
assert int(arr.sum()) == len(o), f'В сотах {int(arr.sum())} доставок, а после очистки {len(o)}.'
assert arr.min() >= 1, 'Пустые соты закрашены — добавьте mincnt=1.'
assert sorted(arr.tolist()) == sorted(ref.tolist()), 'Соты не совпадают с эталоном: X — distance_km, Y — actual_min, gridsize=15.'
assert len(figs[0].axes) == 2, 'Добавьте шкалу цветов: fig.colorbar(hb, ax=ax).'
assert ax.get_xlabel() == 'расстояние, км' and ax.get_ylabel() == 'время, мин', 'Подпишите оси.'
assert int(need('max_cell')) == int(ref.max()), f'max_cell = {need("max_cell")}: максимум счётчиков сот — hb.get_array().max().'
```

### hint
`hb = ax.hexbin(ok["distance_km"], ok["actual_min"], gridsize=15, mincnt=1, cmap="Blues")`, затем `fig.colorbar(hb, ax=ax)`.

### hint
Счётчики сот — `hb.get_array()`; самая плотная — `.max()`, в целое — `int(...)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(7, 4))
hb = ax.hexbin(ok["distance_km"], ok["actual_min"], gridsize=15, mincnt=1, cmap="Blues")
fig.colorbar(hb, ax=ax, label="доставок")
ax.set_xlabel("расстояние, км")
ax.set_ylabel("время, мин")
max_cell = int(hb.get_array().max())
max_cell
```

### explain
Соты крупнее, чем в примере (`gridsize=15` вместо 20), поэтому в самую плотную попадает больше доставок — 135 вместо 81. Размер сот — как ширина корзин у гистограммы: от него зависит конкретное число в соте, но не место скопления — самая плотная сота и здесь около 1.8 км и 29 минут. Если поставить `gridsize=80`, большинство сот будут по 1–2 доставки, и картинка снова станет похожа на шумный scatter.

## task: pairs | Все пары сразу | plus

Добавьте к доставкам (время 1–299 минут) столбец `delay` = `actual_min − promised_min` и нарисуйте `scatter_matrix` для столбцов `distance_km`, `items`, `amount`, `actual_min`, `delay` с гистограммами на диагонали. Сохраните `top_pair` — кортеж из двух **разных** столбцов с наибольшей по модулю корреляцией, а `second_pair` — следующую по силе пару.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
cols = ["distance_km", "items", "amount", "actual_min", "delay"]

```

### check
```python
import pandas as _pd
import numpy as _np
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['delay'] = o['actual_min'] - o['promised_min']
cols = ['distance_km', 'items', 'amount', 'actual_min', 'delay']
c = o[cols].corr().abs()
pairs = sorted(((c.iloc[i, j], cols[i], cols[j]) for i in range(5) for j in range(i + 1, 5)), reverse=True)
assert figs and len(figs[-1].axes) >= 25, f'На полотне {len(figs[-1].axes) if figs else 0} графиков, а нужно 5 × 5: pd.plotting.scatter_matrix(ok[cols], diagonal="hist").'
tp = need('top_pair')
assert len(tp) == 2 and tp[0] != tp[1], 'top_pair — два разных столбца: диагональ (корреляция признака с собой = 1) не считается.'
assert set(tp) == {pairs[0][1], pairs[0][2]}, f'top_pair = {tuple(tp)}.'
sp = need('second_pair')
assert set(sp) == {pairs[1][1], pairs[1][2]}, f'second_pair = {tuple(sp)}: следующая по модулю корреляции пара (знак не важен).'
```

### hint
Матрица корреляций `ok[cols].corr()`; по модулю — `.abs()`. Диагональ (единицы) надо исключить.

### hint
Разверните матрицу в Series пар: `s = ok[cols].corr().abs().stack()`, уберите пары вида (a, a): `s = s[[a != b for a, b in s.index]]`, отсортируйте по убыванию.

### hint
Каждая пара встречается дважды — (a, b) и (b, a). После `sort_values(ascending=False)` первые две строки — одна и та же пара; следующая другая пара — на третьей позиции: `top_pair = s.index[0]`, `second_pair = s.index[2]`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
cols = ["distance_km", "items", "amount", "actual_min", "delay"]
ok["delay"] = ok["actual_min"] - ok["promised_min"]
axes = pd.plotting.scatter_matrix(ok[cols], figsize=(8, 8), alpha=0.3, diagonal="hist")

s = ok[cols].corr().abs().stack()
s = s[[a != b for a, b in s.index]].sort_values(ascending=False)
top_pair = s.index[0]
second_pair = s.index[2]
s.head(6)
```

### explain
Самая сильная пара — `items` и `amount` (0.95): это почти один признак, а не две причины. Вторая — `actual_min` и `delay` (0.63): опоздание считается из фактического времени, поэтому связь заложена в саму формулу. Обе «победы» — не открытия, а напоминание: сначала исключите пары, связанные по построению, и только потом ищите интересное. На сетке видно и то, чего нет в числах: `delay` против `distance_km` — наклонное облако **вниз**, корреляция −0.25 (дальним заказам обещают больше времени), а на диагонали `items` — столбики целых значений.

## task: confounder | Третий признак | plus

Проверьте, что связь «сумма — время» объясняется числом позиций. Посчитайте корреляцию `amount` и `actual_min` (время 1–299 минут) в целом — `r_all`, и внутри заказов с одинаковым числом позиций — словарь `r_within` «число позиций → корреляция» (оба — 2 знака). В `max_within` — наибольшее по модулю значение из `r_within`.

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
assert close(need('r_all'), round(ok['amount'].corr(ok['actual_min']), 2)), f'r_all = {need("r_all")}.'
want = {int(k): round(t['amount'].corr(t['actual_min']), 2) for k, t in ok.groupby('items')}
got = {int(k): v for k, v in dict(need('r_within')).items()}
assert set(got) == set(want) and all(close(got[k], want[k]) for k in want), f'r_within = {got}.'
m = max(want.values(), key=abs)
assert close(abs(need('max_within')), abs(m)), f'max_within = {need("max_within")}.'
```

### hint
Как в задаче про группы курьеров, только группировка по `items`.

### hint
Наибольшее по модулю: `max(r_within.values(), key=abs)` — аргумент `key` из урока «Генераторы списков, zip, sorted»: сравниваем значения по модулю, а возвращается само значение со знаком.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
r_all = round(ok["amount"].corr(ok["actual_min"]), 2)
r_within = {}
for n, t in ok.groupby("items"):
    r_within[n] = round(t["amount"].corr(t["actual_min"]), 2)
max_within = max(r_within.values(), key=abs)
```

### explain
Внутри групп с одинаковым числом позиций связь суммы и времени почти исчезает. Значит, «дорогие заказы везут дольше» — неверный вывод: и сумму, и время увеличивает число позиций. Так проверяют подозрение на конфаундер: фиксируют третий признак и смотрят, осталась ли связь.

## task: binned | Связь по корзинам | star

Одно число r скрывает форму связи (ловушка 2). Линия медиан по корзинам её показывает: прямая она, изгибается или выходит на «полку». Покажите связь «расстояние — время» не облаком, а **медианой по корзинам**: разбейте расстояние на корзины по 1 км от 0 до 8 (`pd.cut`), посчитайте по каждой медиану времени и число доставок (время 1–299 минут). Сохраните таблицу в `bins_t` (столбцы `median_min` и `n`), а затем нарисуйте линию медиан с точками по серединам корзин (0.5, 1.5, …, 7.5).

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
b = _pd.cut(ok['distance_km'], bins=range(0, 9))
want = ok.groupby(b, observed=False)['actual_min'].agg(['median', 'size'])
t = need('bins_t', _pd.DataFrame)
assert list(t.columns) == ['median_min', 'n'], f'Столбцы: {list(t.columns)}.'
assert len(t) == 8, f'Корзин {len(t)}, а нужно 8 (0–1, 1–2, …, 7–8).'
assert all(close(a, b) for a, b in zip(t['median_min'], want['median'])), 'median_min не совпадает.'
assert [int(x) for x in t['n']] == [int(x) for x in want['size']], 'n не совпадает.'
ax = ax_of()
assert ax.lines, 'Нарисуйте линию медиан.'
xs = [round(float(x), 6) for x in ax.lines[0].get_xdata()]
assert xs == [i + 0.5 for i in range(8)], f'По оси X — середины корзин: {xs}.'
```

### hint
`b = pd.cut(ok["distance_km"], bins=range(0, 9))`; затем `ok.groupby(b, observed=False)["actual_min"].agg(median_min="median", n="size")`.

### hint
Середины корзин: `[i + 0.5 for i in range(8)]`.

### hint
```python
b = pd.cut(ok["distance_km"], bins=range(0, 9))
bins_t = ok.groupby(b, observed=False)["actual_min"].agg(median_min=..., n=...)
fig, ax = plt.subplots()
ax.plot([i + 0.5 for i in range(8)], bins_t[...], marker="o")
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
b = pd.cut(ok["distance_km"], bins=range(0, 9))
bins_t = ok.groupby(b, observed=False)["actual_min"].agg(median_min="median", n="size")

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot([i + 0.5 for i in range(8)], bins_t["median_min"], marker="o")
ax.set_xlabel("расстояние, км")
ax.set_ylabel("медиана времени, мин")
bins_t
```

### explain
Линия медиан по корзинам читается лучше облака из двух тысяч точек и устойчива к выбросам. Форма здесь — почти прямая, которая растёт медленно: от 28 минут в первом километре до 45 минут в восьмом, в среднем около 2.4 минуты на километр ((45 − 28) / 7). Значит, связь монотонная и близка к линейной, и r = 0.48 её не искажает — он слабый из-за разброса и смешения курьеров, а не из-за изгиба. Корзина справа — с малым `n`: её точке можно верить меньше. Этот приём пригодится в моделях: так смотрят, как признак связан с целевой переменной.
