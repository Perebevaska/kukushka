---
title: "Срезы: сравниваем группы"
lead: "Срез — это одна метрика, посчитанная отдельно для каждой группы: доля опозданий по погоде, по часам, по кофейням. Срезы — основной инструмент поиска причин. Учимся строить их правильно (всегда вместе с размером группы), рисовать и сочетать два признака сразу."
files: [deliveries.csv]
recap:
  - "Срез = `groupby(признак).agg(метрика, размер)`. Размер группы показывайте всегда: доля по 15 доставкам и по 500 — разная надёжность."
  - "Доля событий — среднее от `True/False`: `groupby(\"weather\")[\"late\"].mean()`."
  - "Порядок на графике: для категорий — по значению метрики, для упорядоченных признаков (час, месяц) — по самому признаку."
  - "Два признака: `pivot_table(index=…, columns=…, values=…, aggfunc=\"mean\")`, график — `pv.plot(kind=\"bar\")`."
  - "Таблица сопряжённости: `pd.crosstab(a, b)` — счётчики, `normalize=\"index\"` — доли по строкам."
  - "Доли внутри целого — составные столбцы: `ct.plot(kind=\"bar\", stacked=True)`."
  - "Цепочка методов: `(df.query(\"weather in @bad\").assign(late=lambda x: …).groupby(…).agg(…))` — шаги сверху вниз, как в SQL. `@` подставляет переменную Python, `lambda` в `assign` получает таблицу с предыдущего шага, `pipe(f, …)` встраивает свою функцию."
---

## Что такое срез

Общая доля опозданий — одно число на всю сеть. Чтобы понять **почему** опаздываем, это число разбивают по признакам: погода, час, кофейня, тип курьера. Если в какой-то группе доля заметно выше — признак связан с опозданиями, и в него стоит копать.

::: figure slice-split
Срез по погоде: одна доля на всю сеть превращается в четыре — по группе на каждый вид погоды, и у каждой доли рядом её размер n.
:::

Подготовим данные — уберём невозможное время (урок «Распределения и гистограммы») и добавим флаг опоздания:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
print("доля опозданий:", round(ok["late"].mean() * 100, 1), "%")
ok.groupby("weather")["late"].agg(["mean", "size"]).round(3)
```

`mean` от столбца `True/False` — доля `True` (урок «DataFrame — таблица в Python»). `size` — сколько доставок в группе.

{{practice: late-share, hours}}

## Размер группы — всегда рядом

Доля без размера группы может обмануть. Сравните: 2 опоздания из 5 доставок — это 40 %, и 200 из 500 — тоже 40 %. Но первой цифре верить нельзя: ещё одна доставка вовремя — и уже 33 %.

::: warn
Правило: в любом срезе рядом с метрикой — число наблюдений. Группы из нескольких десятков строк и меньше подписывайте как ненадёжные или объединяйте с соседними. В главе 5 научимся проверять различия статистически.
:::

Удобная форма среза — именованные агрегаты:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
by_shop = ok.groupby("shop_id").agg(
    deliveries=("late", "size"),
    late_pct=("late", "mean"),
    median_min=("actual_min", "median"),
)
by_shop["late_pct"] = (by_shop["late_pct"] * 100).round(1)
by_shop.sort_values("late_pct", ascending=False)
```

::: sql
`SELECT shop_id, COUNT(*), AVG(CASE WHEN actual_min > promised_min THEN 1.0 ELSE 0 END) FROM deliveries GROUP BY shop_id` — тот же срез.
:::

::: quiz
Представьте, что в срезе по кофейням у новой EKB-1 доля опозданий 60 %, а у остальных — от 19 до 32 %. Какой вопрос задать первым?

- [x] Сколько доставок у EKB-1?
  > При 5 доставках 60 % — это 3 опоздания, и следующая неделя может дать совсем другую цифру. Размер группы показывают рядом с долей.
- [ ] Кто управляющий EKB-1?
  > Искать виноватого рано: сначала убедитесь, что цифра надёжная.
- [ ] Почему у остальных так мало опозданий?
  > Интересно, но сначала стоит проверить подозрительную цифру.
- [ ] Как перекрасить столбец EKB-1 в красный?
  > Акцент на графике — после того, как вывод подтвердился.
:::

{{practice: shop-slice}}

## Срез на графике

Для категорий без естественного порядка (погода, кофейня) столбцы сортируют по метрике. Количество удобно подписать прямо на столбцах:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = ok.groupby("weather")["late"].agg(["mean", "size"]).sort_values("mean", ascending=False)

fig, ax = plt.subplots(figsize=(6, 3.5))
bars = ax.bar(t.index, t["mean"] * 100)
ax.bar_label(bars, labels=[f"n={n}" for n in t["size"]])
ax.set_ylabel("опозданий, %")
ax.set_title("Доля опозданий по погоде")
```

`bar_label(bars, labels=…)` подписывает столбцы своими текстами — здесь размерами групп.

Для упорядоченных признаков — час, день, месяц — порядок задаёт сам признак, а не метрика. Час суток лучше показать линией:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
by_hour = ok.groupby(ok["created"].dt.hour)["late"].mean() * 100

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(by_hour.index, by_hour.values, marker="o")
ax.set_xticks(by_hour.index)
ax.set_xlabel("час")
ax.set_ylabel("опозданий, %")
ax.set_title("Опоздания по часам")
```

Два пика — обед и вечер. Это часы, когда заказов больше всего: кофейни собирают заказы дольше, а авто-курьеры стоят в пробках.

{{practice: weather-bar}}

## Два признака сразу

Один срез может обмануть: признаки бывают связаны между собой. Например, пешие курьеры чаще возят заказы с обещанием «30 минут» — и непонятно, кто виноват: курьер или обещание. Разобраться помогает срез сразу по двум признакам:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
pv = ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean")
(pv * 100).round(1)
```

Строки — обещанное время, столбцы — тип курьера, в ячейках — доля опозданий. Пешие опаздывают при любом обещании, а вело и авто — заметно реже. Значит, дело в типе курьера, а не только в обещании.

Ту же таблицу — как сгруппированные столбцы:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
pv = ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean") * 100

fig, ax = plt.subplots(figsize=(7, 3.5))
pv.plot(kind="bar", ax=ax, rot=0)
ax.set_xlabel("обещано, мин")
ax.set_ylabel("опозданий, %")
ax.set_title("Опоздания: обещание × курьер")
```

Пустая ячейка (`NaN`) — значит, такой комбинации нет: пешие не возят на дальние расстояния.

### Разберём вместе: снег опаснее, чем кажется

В снег опаздывает 34 % доставок, в ясную погоду — 24 %. Разница 10 пунктов. Разрежем по второму признаку — типу курьера:

| курьер | ясно: доставок | ясно: опозданий | снег: доставок | снег: опозданий |
|---|---|---|---|---|
| авто | 173 | 7.5 % | 75 | 6.7 % |
| вело | 331 | 13.6 % | 56 | 33.9 % |
| пеший | 145 | 69.0 % | 35 | 94.3 % |

1. Внутри каждого типа курьера снег бьёт сильнее, чем видно в общей цифре: у вело опозданий в 2.5 раза больше, у пеших — почти все.
2. Но в снег диспетчер чаще отправляет машины: в ясную погоду авто — 27 % доставок (173 из 649), в снег — 45 % (75 из 166). Машинам снег почти не мешает.
3. **Состав курьеров в ясную погоду** (всего 173 + 331 + 145 = 649 доставок): авто 173 / 649 ≈ **0.27**, вело 331 / 649 ≈ **0.51**, пешие 145 / 649 ≈ **0.22**. В сумме 1.
4. Теперь вопрос: сколько было бы опозданий в снег, если бы в снег ездил **тот же состав**, что в ясную погоду? Берём снежную долю опозданий каждого типа и взвешиваем ясным составом: 0.27 × 6.7 % + 0.51 × 33.9 % + 0.22 × 94.3 % ≈ 1.8 + 17.3 + 20.7 ≈ **40 %**, а не 34 %. Против 24 % в ясную погоду это разница не 10 пунктов, а около 16.

Такой приём называют **пересчётом на одинаковый состав** (в учебниках — стандартизация): доли внутри групп берём из одного периода, а веса групп — из другого. Зачем он аналитику: когда две группы различаются составом (кто возит, какие клиенты, какие кофейни), прямое сравнение общих долей смешивает «стало хуже внутри» и «поменялся состав». Пересчёт оставляет только первое.

Что получилось: общая доля 34 % смешивает два эффекта — «снег замедляет» и «в снег едут машины». Срез по одному признаку показал эффект слабее, чем он есть. Перед выводом «снег добавляет 10 пунктов» стоит спросить: а не отличаются ли группы ещё чем-то?

::: figure snow-mix
Слева — кто везёт в ясную погоду и в снег, справа — как часто опаздывает каждый тип курьера. Если подставить в снежные доли опозданий ясный состав курьеров, выйдет около 40 %, а не 34 %.
:::

::: tip Аналогия
Средний балл класса за контрольную вырос, хотя каждый ученик написал как обычно: просто в этом году в классе больше отличников. Общая цифра меняется и от того, **как** справился каждый, и от того, **кто** вошёл в группу. Где аналогия хромает: состав класса меняется случайно, а состав курьеров в снег выбирает диспетчер — он сам отправляет машины туда, где велосипед не справится.
:::

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
x = ok[ok["weather"].isin(["снег", "ясно"])]
print(x.pivot_table(index="courier", columns="weather", values="late", aggfunc=["size", "mean"]).round(3))
```

{{practice: grouped, heatmap}}

## Таблица сопряжённости: crosstab

Часто нужно просто посчитать, сколько строк в каждой комбинации двух признаков. Для этого есть `pd.crosstab`:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
pd.crosstab(d["created"].dt.month, d["weather"])
```

С `normalize="index"` вместо количеств получатся доли внутри каждой строки (сумма по строке — 1):

::: predict
```python static
import pandas as pd
a = pd.Series(["x", "x", "y", "y"])
b = pd.Series(["p", "q", "p", "p"])
print(pd.crosstab(a, b, normalize="index").loc["x", "p"])
```

- `0.25`
- [x] `0.5`
- `0.333…`

Почему: строка «x» — две записи, из них одна с «p». Доля внутри строки — 1 из 2.
:::

::: figure crosstab-norm
Одна таблица счётчиков и две нормировки на условных 80 доставках: `normalize="index"` отвечает «как распределяются доставки этого курьера», `normalize="columns"` — «кто возит в эту погоду».
:::

::: warn Типичные ошибки
- **Доля без размера группы.** 100 % опозданий по 3 доставкам — не вывод; рядом с долей всегда число строк.
- **Не та нормировка `crosstab`.** `normalize="index"` — доли внутри строки, `"columns"` — внутри столбца; ответ на вопрос «кто возит в снег» и «что происходит с вело» — разные таблицы.
- **Один срез — один вывод.** Группы могут отличаться ещё чем-то (состав курьеров), и эффект окажется сильнее или слабее.
- **Составные столбцы для сравнения малых долей.** Глаз плохо сравнивает «плавающие» сегменты; для точного сравнения — сгруппированные столбцы.
:::

{{practice: p-crosstab, share-snow}}

## Доли внутри целого: составные столбцы

Как менялась погода по месяцам? Каждый месяц — 100 %, внутри — доли видов погоды. Это составной (stacked) столбец:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ct = pd.crosstab(d["created"].dt.month, d["weather"], normalize="index") * 100

fig, ax = plt.subplots(figsize=(6, 3.5))
ct.plot(kind="bar", stacked=True, ax=ax, rot=0)
ax.set_xlabel("месяц")
ax.set_ylabel("% доставок")
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
ax.set_title("Погода по месяцам")
```

`bbox_to_anchor` выносит легенду справа от графика, чтобы она не закрывала столбцы.

Снег появился только в ноябре. Если в ноябре опозданий больше, это может быть из-за снега — а может, из-за чего-то ещё, что тоже изменилось в ноябре. Срезы находят связи, но не доказывают причины. Об этом — в уроке «Связи: рассеяние и корреляция».

{{practice: stacked}}

## Срез одной цепочкой: query, assign, pipe

В каждом примере урока повторяются одни и те же шаги: прочитать файл → отфильтровать время → добавить `late` → сгруппировать. Каждый шаг — отдельная переменная (`d`, `ok`), а `ok["late"] = …` ещё и требует `.copy()`, чтобы pandas не ругался. Когда шагов становится десять, легко перепутать, какая таблица какая. **Цепочка методов** записывает те же шаги одним выражением сверху вниз — как SQL-запрос.

::: sql
```sql
SELECT courier, COUNT(*) AS n, AVG(CASE WHEN actual_min > promised_min THEN 1.0 ELSE 0 END) AS late_pct
FROM deliveries
WHERE actual_min BETWEEN 1 AND 299 AND weather IN ('дождь', 'снег')
GROUP BY courier
ORDER BY late_pct DESC
```
Цепочка pandas ниже читается так же: каждая строка — следующий шаг.
:::

Три метода делают цепочку возможной:

- **`query("условие")`** — фильтр строк текстом условия, как `WHERE`. Внешняя переменная Python подставляется через `@`: `query("weather in @bad")`;
- **`assign(новый=функция)`** — добавляет столбец и возвращает **новую** таблицу (исходная не меняется, `.copy()` не нужен). Функция `lambda x: …` получает таблицу, которая пришла с предыдущего шага цепочки;
- **`pipe(функция, аргументы)`** — передаёт всю таблицу в вашу функцию: `t.pipe(f, "shop_id")` — то же, что `f(t, "shop_id")`, но не ломает чтение сверху вниз.

### Игрушечный пример руками

Четыре доставки:

| курьер | погода | факт | обещано |
|---|---|---|---|
| вело | дождь | 35 | 30 |
| вело | ясно | 25 | 30 |
| пеший | снег | 50 | 30 |
| авто | дождь | 0 | 45 |

1. `query("actual_min >= 1")` убирает четвёртую строку (0 минут — невозможное время). Остаются три.
2. `query("weather in @bad")` при `bad = ["дождь", "снег"]` оставляет первую и третью.
3. `assign(late=lambda x: x["actual_min"] > x["promised_min"])` добавляет `late`: 35 > 30 — `True`, 50 > 30 — `True`.
4. `groupby("courier")["late"].mean()` — вело 1.0, пеший 1.0.

::: figure query-chain
Четыре доставки проходят цепочку: первый `query` убирает невозможное время, второй оставляет плохую погоду, `assign` добавляет `late`, `groupby` сворачивает в доли по курьерам.
:::

```python
import pandas as pd
toy = pd.DataFrame({"courier": ["вело", "вело", "пеший", "авто"],
                    "weather": ["дождь", "ясно", "снег", "дождь"],
                    "actual_min": [35, 25, 50, 0], "promised_min": [30, 30, 30, 45]})
bad = ["дождь", "снег"]
(
    toy
    .query("actual_min >= 1")
    .query("weather in @bad")
    .assign(late=lambda x: x["actual_min"] > x["promised_min"])
    .groupby("courier")["late"].mean()
)
```

::: predict
```python static
import pandas as pd
t = pd.DataFrame({"x": [1, 5, 9]})
limit = 4
print(t.query("x > @limit").assign(y=lambda d: d["x"] * 2)["y"].tolist())
```

- `[2, 10, 18]`
- [x] `[10, 18]`
- `Ошибка UndefinedVariableError`

Почему: `@limit` подставляет переменную Python — остаются строки с 5 и 9, затем `assign` удваивает их. Ошибка была бы, если написать `x > limit` без `@`: внутри `query` имена без `@` ищутся среди столбцов.
:::

### На реальных данных

Опоздания по типу курьера в плохую погоду — одним выражением:

```python
import pandas as pd
bad = ["дождь", "снег"]
t = (
    pd.read_csv("deliveries.csv")
    .query("actual_min >= 1 and actual_min <= 299")
    .query("weather in @bad")
    .assign(late=lambda x: x["actual_min"] > x["promised_min"])
    .groupby("courier")
    .agg(n=("late", "size"), late_pct=("late", "mean"))
    .assign(late_pct=lambda x: (x["late_pct"] * 100).round(1))
    .sort_values("late_pct", ascending=False)
)
t
```

Что здесь происходит:

- вся цепочка в круглых скобках — так Python разрешает переносить её по строкам, и каждый шаг стоит на своей строке;
- `query("actual_min >= 1 and actual_min <= 299")` — то же, что `between(1, 299)`; в условии `query` работают `and`, `or`, `not`, `in`;
- первый `assign` получает отфильтрованную таблицу и добавляет `late`; второй — уже таблицу после `agg` и переводит долю в проценты;
- `lambda x:` нужна, потому что у промежуточной таблицы нет имени. Если написать `assign(late=d["actual_min"] > …)`, pandas возьмёт столбцы из **исходной** `d`, а не из того, что пришло с предыдущего шага.

Что получилось: в дождь и снег пешие курьеры опаздывают в 88.1 % доставок (118 доставок), вело — в 18.8 %, авто — в 5.5 %. Таблица готова целиком, без промежуточных `ok`.

`pipe` встраивает в цепочку свою функцию — например, функцию, которая строит срез вроде `by_shop` выше по любому признаку:

```python
import pandas as pd

def slice_table(df, by):
    return (df.groupby(by)["late"].agg(n="size", late_pct="mean")
              .sort_values("late_pct", ascending=False))

(
    pd.read_csv("deliveries.csv")
    .query("1 <= actual_min <= 299")
    .assign(late=lambda x: x["actual_min"] > x["promised_min"])
    .pipe(slice_table, "shop_id")
    .round(3)
)
```

Внутри функции новая запись агрегатов: `.agg(n="size", late_pct="mean")` — без кортежей. Раньше мы писали `deliveries=("late", "size")`: столбец и функцию. Здесь после `["late"]` столбец уже выбран, поэтому достаточно имени функции.

`query("1 <= actual_min <= 299")` — двойное сравнение, как в математике. `.pipe(slice_table, "shop_id")` вызывает `slice_table(таблица, "shop_id")`, и цепочка продолжается дальше с её результатом.

::: warn Типичные ошибки
- **Забыли `@`.** `query("weather in bad")` ищет **столбец** `bad` и падает с `UndefinedVariableError: name 'bad' is not defined`. Переменные Python — только через `@`.
- **`assign` без `lambda`.** `assign(late=d["actual_min"] > d["promised_min"])` берёт столбцы исходной `d`. Сразу после фильтра это случайно сработает (pandas выровняет строки по индексу), но столбца, созданного выше в цепочке, в `d` нет — `KeyError`, а после `groupby` индекс другой — в столбце окажутся `NaN`.
- **Имя столбца с пробелом в `query`.** `query("actual min > 30")` — синтаксическая ошибка; такие имена берут в обратные кавычки: ``query("`actual min` > 30")``.
- **Цепочка на 20 строк без проверки.** Ошибку в середине трудно найти. Отлаживайте по частям: закомментируйте хвост и посмотрите промежуточный результат, а длинные блоки выносите в функции и подключайте через `pipe`.
:::

{{practice: chain}}

## Практика

## task: late-share | Доля опозданий | warmup

Оставьте доставки с временем 1–299 минут, добавьте флаг `late` и сохраните в `late_pct` общую долю опозданий в процентах (1 знак), а в `by_courier` — словарь «тип курьера → доля опозданий в процентах» (1 знак).

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
late = o['actual_min'] > o['promised_min']
assert close(need('late_pct'), round(late.mean() * 100, 1)), f'late_pct = {need("late_pct")}.'
want = (late.groupby(o['courier']).mean() * 100).round(1).to_dict()
got = dict(need('by_courier'))
assert set(got) == set(want) and all(close(got[k], want[k]) for k in want), f'by_courier = {got}, а нужно {want}.'
```

### hint
`ok["late"] = ok["actual_min"] > ok["promised_min"]`, доля — `mean()`.

### hint
По курьерам: `(ok.groupby("courier")["late"].mean() * 100).round(1).to_dict()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
late_pct = round(ok["late"].mean() * 100, 1)
by_courier = (ok.groupby("courier")["late"].mean() * 100).round(1).to_dict()
```

## task: weather-bar | Опоздания по погоде | warmup

Нарисуйте столбцы: доля опозданий (%) по погоде, по убыванию. Заголовок — «Опоздания по погоде».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
w = ((o['actual_min'] > o['promised_min']).groupby(o['weather']).mean() * 100).sort_values(ascending=False)
ax = ax_of()
h = [p.get_height() for p in ax.patches]
assert len(h) == len(w) and all(close(a, b) for a, b in zip(h, w.values)), 'Высоты — доля опозданий в процентах, по убыванию.'
assert [t.get_text() for t in ax.get_xticklabels()] == list(w.index), 'Подписи столбцов — виды погоды в порядке убывания доли.'
assert ax.get_title() == 'Опоздания по погоде', f'Заголовок сейчас {ax.get_title()!r}, а нужен «Опоздания по погоде» — буква в букву.'
```

### hint
Сначала флаг опоздания и фильтр времени 1–299 минут, как в предыдущей задаче.

### hint
`t = (ok.groupby("weather")["late"].mean() * 100).sort_values(ascending=False)`, затем `ax.bar(t.index, t.values)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = (ok.groupby("weather")["late"].mean() * 100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(6, 3.5))
ax.bar(t.index, t.values)
ax.set_title("Опоздания по погоде")
ax.set_ylabel("опозданий, %")
```

## task: p-crosstab | Курьеры в погоду | warmup

Соберите программу, которая выводит, сколько доставок вело-курьеры сделали в снег.

### parsons
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ct = pd.crosstab(d["courier"], d["weather"])
print(ct.loc["вело", "снег"])
```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
want = ((d['courier'] == 'вело') & (d['weather'] == 'снег')).sum()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Ячейка таблицы — `ct.loc[строка, столбец]`.

### hint
Порядок: импорт → чтение файла → таблица сопряжённости (строки — курьеры, столбцы — погода) → печать одной ячейки.

## task: hours | Часы пик | base

Посчитайте долю опозданий (%) по часу создания заказа и нарисуйте её линией с точками (`marker="o"`), часы — по порядку. Сохраните в `peak_hours` отсортированный список часов, где доля опозданий больше 25 %.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = d[d['actual_min'].between(1, 299)]
s = (o['actual_min'] > o['promised_min']).groupby(o['created'].dt.hour).mean() * 100
ax = ax_of()
assert ax.lines, 'Нужна линия: ax.plot(...).'
l = ax.lines[0]
assert [int(x) for x in l.get_xdata()] == list(s.index), 'По оси X — часы по порядку.'
assert all(close(a, b) for a, b in zip(l.get_ydata(), s.values)), 'По оси Y — доля опозданий в процентах.'
assert l.get_marker() == 'o', 'Добавьте точки: marker="o".'
assert need('peak_hours') == [int(h) for h in s[s > 25].index], f'peak_hours = {need("peak_hours")}, а нужно {[int(h) for h in s[s > 25].index]}.'
```

### hint
`by_hour = ok.groupby(ok["created"].dt.hour)["late"].mean() * 100` — индекс уже по порядку часов.

### hint
`peak_hours = list(by_hour[by_hour > 25].index)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
by_hour = ok.groupby(ok["created"].dt.hour)["late"].mean() * 100
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(by_hour.index, by_hour.values, marker="o")
ax.set_title("Опоздания по часам")
peak_hours = list(by_hour[by_hour > 25].index)
```

### explain
Два пика: 12–13 часов (обед, 29–31 %) и 18–19 часов (вечер, 31–35 %). В остальное время — 15–22 %. Час пик — признак, который стоит учитывать в обещании: те же 30 минут в 19:00 и в 15:00 — разные обещания.

## task: shop-slice | Срез по кофейням | base

Соберите `by_shop` — таблицу по кофейням со столбцами `deliveries` (число доставок), `late_pct` (доля опозданий, %, 1 знак) и `median_min` (медиана времени), отсортированную по `late_pct` по убыванию. В `worst` — кофейня с наибольшей долей опозданий.

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
g = o.groupby('shop_id')
b = need('by_shop', _pd.DataFrame)
if 'shop_id' in b.columns:
    b = b.set_index('shop_id')
assert list(b.columns) == ['deliveries', 'late_pct', 'median_min'], f'Столбцы: {list(b.columns)}.'
assert b['deliveries'].to_dict() == g.size().to_dict(), 'deliveries не совпадает.'
assert all(close(b.loc[k, 'late_pct'], round(v * 100, 1)) for k, v in g['late'].mean().items()), 'late_pct не совпадает (проценты, 1 знак).'
assert all(close(b.loc[k, 'median_min'], v) for k, v in g['actual_min'].median().items()), 'median_min не совпадает.'
assert list(b['late_pct']) == sorted(b['late_pct'], reverse=True), 'Отсортируйте по late_pct по убыванию.'
assert need('worst') == g['late'].mean().idxmax(), f'worst = {need("worst")!r}.'
```

### hint
`ok.groupby("shop_id").agg(deliveries=("late", "size"), late_pct=("late", "mean"), median_min=("actual_min", "median"))`.

### hint
Доля в процентах — `by_shop["late_pct"] = (by_shop["late_pct"] * 100).round(1)`; затем `sort_values("late_pct", ascending=False)`, `worst = by_shop.index[0]`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
by_shop = ok.groupby("shop_id").agg(
    deliveries=("late", "size"),
    late_pct=("late", "mean"),
    median_min=("actual_min", "median"),
)
by_shop["late_pct"] = (by_shop["late_pct"] * 100).round(1)
by_shop = by_shop.sort_values("late_pct", ascending=False)
worst = by_shop.index[0]
by_shop
```

### explain
Хуже всех KZN-2: 32 % опозданий при медиане 37 минут — у остальных медиана 32. Это не одна неудачная неделя: 272 доставки — уже не маленькая группа. UFA-1 лучше всех (18.9 %), но по 180 доставкам её преимущество перед PRM-2 (20.4 %) — в пределах шума.

## task: share-snow | Кто возит в снег | base

По доставкам с временем 1–299 минут (таблица `ok` уже в заготовке) постройте таблицу сопряжённости «тип курьера × погода» с долями **внутри погоды** (каждый столбец в сумме даёт 1) и сохраните в `ct`. В `velo_snow_pct` сохраните долю вело-курьеров среди доставок в снег, в процентах (1 знак), а в `velo_clear_pct` — то же для ясной погоды.

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
want = _pd.crosstab(o['courier'], o['weather'], normalize='columns')
c = need('ct', _pd.DataFrame)
assert c.shape == want.shape and all(close(v, 1) for v in c.sum()), 'Каждый столбец (погода) в сумме должен давать 1: normalize="columns".'
raw = _pd.crosstab(d['courier'], d['weather'], normalize='columns')
_vs, _ws = need('velo_snow_pct'), round(want.loc['вело', 'снег'] * 100, 1)
if close(_vs, round(raw.loc['вело', 'снег'] * 100, 1)) and not close(_vs, _ws):
    raise AssertionError(f'velo_snow_pct = {_vs}: похоже, таблица построена по d. Нужны доставки 1–299 минут — таблица ok, тогда получится {_ws}.')
assert close(_vs, _ws), f'velo_snow_pct = {_vs}, а нужно {_ws}: доля строки «вело» в столбце «снег», × 100, 1 знак.'
_vc, _wc = need('velo_clear_pct'), round(want.loc['вело', 'ясно'] * 100, 1)
assert close(_vc, _wc), f'velo_clear_pct = {_vc}, а нужно {_wc}: доля строки «вело» в столбце «ясно».'
```

### hint
Нужны доли **внутри погоды**, то есть внутри столбца. У `crosstab` три варианта нормировки: `"index"` — по строкам, `"columns"` — по столбцам, `"all"` — по всей таблице.

### hint
`pd.crosstab(ok["courier"], ok["weather"], normalize="columns")`; одна ячейка — `ct.loc[строка, столбец]`.

### hint
Почти готово: `ct = pd.crosstab(ok["courier"], ok["weather"], normalize="columns")`, `velo_snow_pct = round(ct.loc["вело", "снег"] * 100, 1)`, `velo_clear_pct = round(ct.loc[..., ...] * 100, 1)`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
ct = pd.crosstab(ok["courier"], ok["weather"], normalize="columns")
velo_snow_pct = round(ct.loc["вело", "снег"] * 100, 1)
velo_clear_pct = round(ct.loc["вело", "ясно"] * 100, 1)
```

### explain
В снег вело-курьеры везут 33.7 % доставок (56 из 166 — те же числа, что в «Разберём вместе»), в ясную погоду — 51.0 %: часть заказов передали авто. Поэтому сравнивать опоздания «в снег» и «в ясную погоду» нужно аккуратно: изменилась не только погода, но и состав курьеров.

## task: chain | Две кофейни одной цепочкой | base

Сравните кофейни Казани одной цепочкой методов, без промежуточных переменных. Для кофеен из списка `shops` (уже задан) и доставок с временем 1–299 минут постройте `t` — таблицу по паре (кофейня, тип курьера) со столбцами `n` (доставок), `late_pct` (доля опозданий, %, 1 знак) и `delay_med` (медиана опоздания `actual_min − promised_min`, мин). Используйте `query` с `@shops` и `assign` с `lambda`.

### starter
```python
import pandas as pd
shops = ["KZN-1", "KZN-2"]
t = (
    pd.read_csv("deliveries.csv")
    # ваши шаги
)
t
```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299) & d['shop_id'].isin(['KZN-1', 'KZN-2'])].copy()
o['late'] = o['actual_min'] > o['promised_min']
o['delay'] = o['actual_min'] - o['promised_min']
w = o.groupby(['shop_id', 'courier']).agg(n=('late', 'size'), late_pct=('late', 'mean'), delay_med=('delay', 'median'))
w['late_pct'] = (w['late_pct'] * 100).round(1)
assert '.query(' in _code and '@shops' in _code, 'Отфильтруйте кофейни через query с переменной: query("shop_id in @shops").'
assert '.assign(' in _code and 'lambda' in _code, 'Новые столбцы добавьте через assign(...=lambda x: ...).'
tt = need('t', _pd.DataFrame)
if 'shop_id' in tt.columns:
    tt = tt.set_index(['shop_id', 'courier'])
for c in ('n', 'late_pct', 'delay_med'):
    assert c in tt.columns, f'В t нет столбца {c}.'
assert len(tt) == len(w), f'Строк в t {len(tt)}, а пар (кофейня, курьер) {len(w)}.'
if close(tt['late_pct'].max(), w['late_pct'].max() / 100, 0.01):
    raise AssertionError('late_pct в долях — переведите в проценты: assign(late_pct=lambda x: (x["late_pct"] * 100).round(1)).')
for k in w.index:
    assert int(tt.loc[k, 'n']) == int(w.loc[k, 'n']), f'n для {k}: {tt.loc[k, "n"]}, а нужно {w.loc[k, "n"]}. Проверьте фильтр 1–299 минут.'
    assert close(tt.loc[k, 'late_pct'], w.loc[k, 'late_pct'], 0.051), f'late_pct для {k}: {tt.loc[k, "late_pct"]}.'
    assert close(tt.loc[k, 'delay_med'], w.loc[k, 'delay_med']), f'delay_med для {k}: {tt.loc[k, "delay_med"]}.'
```

### hint
Фильтры: `.query("actual_min >= 1 and actual_min <= 299 and shop_id in @shops")`. Два новых столбца можно добавить одним `assign`: `late=lambda x: ...`, `delay=lambda x: ...`.

### hint
Дальше `.groupby(["shop_id", "courier"]).agg(n=("late", "size"), late_pct=("late", "mean"), delay_med=("delay", "median"))` и ещё один `assign` для процентов.

### hint
Почти готово: `.assign(late=lambda x: x["actual_min"] > x["promised_min"], delay=lambda x: x["actual_min"] - x["promised_min"])` … `.assign(late_pct=lambda x: (x["late_pct"] * 100).round(1))`.

### solution
```python
import pandas as pd
shops = ["KZN-1", "KZN-2"]
t = (
    pd.read_csv("deliveries.csv")
    .query("actual_min >= 1 and actual_min <= 299 and shop_id in @shops")
    .assign(
        late=lambda x: x["actual_min"] > x["promised_min"],
        delay=lambda x: x["actual_min"] - x["promised_min"],
    )
    .groupby(["shop_id", "courier"])
    .agg(n=("late", "size"), late_pct=("late", "mean"), delay_med=("delay", "median"))
    .assign(late_pct=lambda x: (x["late_pct"] * 100).round(1))
)
t
```

### explain
Внутри каждого типа курьера KZN-2 опаздывает чаще KZN-1: авто — 12.0 % против 2.4 %, вело — 20.2 % против 10.3 %, пешие — 85.0 % против 72.2 %. Медиана опоздания у KZN-2 тоже выше на 4–5 минут. Значит, дело не только в составе курьеров — к этому вопросу вернёмся в проекте главы. Цепочка читается как рецепт: отфильтровать → добавить столбцы → сгруппировать → оформить. Второй `assign` без `lambda` не написать вовсе: столбца `late_pct` нет ни в одной именованной таблице — он появился только внутри цепочки, и `lambda x:` — единственный способ до него дотянуться.

## task: grouped | Обещание × курьер | plus

Постройте сводную таблицу доли опозданий (%): строки — `promised_min`, столбцы — `courier`. Нарисуйте её сгруппированными столбцами (`kind="bar"`) с легендой. Сохраните в `walk_30` долю опозданий пеших курьеров при обещании 30 минут (1 знак).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

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
pv = o.pivot_table(index='promised_min', columns='courier', values='late', aggfunc='mean') * 100
ax = ax_of()
assert ax.get_legend() is not None and sorted(t.get_text() for t in ax.get_legend().get_texts()) == sorted(pv.columns), 'Нужна легенда с типами курьеров.'
assert len(ax.patches) == pv.size, f'Столбцов {len(ax.patches)}, а нужно {pv.size} (3 обещания × 3 типа курьера).'
assert close(need('walk_30'), round(pv.loc[30, 'пеший'], 1)), f'walk_30 = {need("walk_30")}.'
```

### hint
`pv = ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean") * 100`.

### hint
`pv.plot(kind="bar", ax=ax, rot=0)`; значение — `pv.loc[30, "пеший"]`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
pv = ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean") * 100
fig, ax = plt.subplots(figsize=(7, 3.5))
pv.plot(kind="bar", ax=ax, rot=0)
ax.set_ylabel("опозданий, %")
walk_30 = round(pv.loc[30, "пеший"], 1)
```

### explain
Пешие при обещании 30 минут опаздывают в 70 % случаев, при 45 — в 90 %: им дают длинное обещание на далёкие для пешехода адреса. У машин и велосипедов при обещании 45 минут опозданий почти нет (1.4 % и 7.8 %). Но при 60 минутах у вело их снова 21.4 % (у авто 4.3 %). Дело в расстоянии: 60 минут обещают на самые дальние адреса, медиана около 6 км — вдвое больше, чем при обещании 45 минут (3 км). Да и вело-доставок с таким обещанием всего 42 — цифра шаткая. Сгруппированные столбцы сразу показывают, что «обещать больше» работает не для всех курьеров одинаково.

## task: stacked | Погода по месяцам | plus

Нарисуйте составные столбцы: для каждого месяца (`dt.month`) — доли доставок по погоде в процентах (каждый столбец — 100 %). Сохраните таблицу долей в `ct`, а в `snow_nov` — долю снежных доставок в ноябре (%, 1 знак).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
want = _pd.crosstab(d['created'].dt.month, d['weather'], normalize='index') * 100
c = need('ct', _pd.DataFrame)
assert c.shape == want.shape and all(close(v, 100) for v in c.sum(axis=1)), 'Каждая строка-месяц в сумме — 100 %: normalize="index" и × 100.'
ax = ax_of()
assert len(ax.patches) == want.size, f'Прямоугольников {len(ax.patches)}, а нужно {want.size}.'
bottoms = {round(p.get_y(), 6) for p in ax.patches}
assert len(bottoms) > 1, 'Столбцы должны стоять друг на друге: stacked=True.'
assert close(need('snow_nov'), round(want.loc[11, 'снег'], 1)), f'snow_nov = {need("snow_nov")}.'
```

### hint
`ct = pd.crosstab(d["created"].dt.month, d["weather"], normalize="index") * 100`.

### hint
`ct.plot(kind="bar", stacked=True, ax=ax, rot=0)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ct = pd.crosstab(d["created"].dt.month, d["weather"], normalize="index") * 100
fig, ax = plt.subplots(figsize=(6, 3.5))
ct.plot(kind="bar", stacked=True, ax=ax, rot=0)
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
snow_nov = round(ct.loc[11, "снег"], 1)
```

### explain
Снег появляется только в ноябре — 27.5 % доставок. В сентябре больше всего ясных дней (52 %), в октябре — облачных. Составные столбцы хорошо показывают, как меняется состав целого; поэтому сравнение «опоздания в ноябре против сентября» надо делать с оглядкой на погоду.

## task: heatmap | Тепловая карта | star

Постройте тепловую карту доли опозданий: строки — день недели (`dt.dayofweek`, 0 — понедельник), столбцы — час. Нарисуйте её через `ax.imshow(pv.values, aspect="auto", cmap="Reds")`, добавьте шкалу цветов `fig.colorbar(...)`, подпишите столбцы часами (`ax.set_xticks`, `ax.set_xticklabels`). Сохраните таблицу в `pv`, а в `worst_cell` — пару `(день, час)` с наибольшей долей опозданий.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["dow"] = ok["created"].dt.dayofweek
ok["hour"] = ok["created"].dt.hour

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
want = o.pivot_table(index=o['created'].dt.dayofweek, columns=o['created'].dt.hour, values='late', aggfunc='mean')
p = need('pv', _pd.DataFrame)
assert p.shape == want.shape, f'Размер pv {p.shape}, а нужно {want.shape} (7 дней × 13 часов).'
ax = ax_of()
assert ax.images, 'Нужна картинка-матрица: ax.imshow(pv.values, ...).'
assert ax.images[0].get_array().shape == want.shape
assert len(figs[0].axes) == 2, 'Добавьте шкалу цветов: fig.colorbar(im, ax=ax).'
labels = [t.get_text() for t in ax.get_xticklabels()]
assert labels == [str(h) for h in want.columns], f'Подписи по X: {labels[:4]}… — часы по порядку.'
st = want.stack()
k = st.idxmax()
assert tuple(int(x) for x in need('worst_cell')) == (int(k[0]), int(k[1])), f'worst_cell = {need("worst_cell")}, а нужно {k}.'
```

### hint
`pv = ok.pivot_table(index="dow", columns="hour", values="late", aggfunc="mean")`; `im = ax.imshow(pv.values, aspect="auto", cmap="Reds")`; `fig.colorbar(im, ax=ax)`.

### hint
Подписи: `ax.set_xticks(range(len(pv.columns)))` и `ax.set_xticklabels(pv.columns)`. Наибольшая ячейка: `pv.stack().idxmax()` — вернёт пару (день, час).

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["dow"] = ok["created"].dt.dayofweek
ok["hour"] = ok["created"].dt.hour
pv = ok.pivot_table(index="dow", columns="hour", values="late", aggfunc="mean")

fig, ax = plt.subplots(figsize=(9, 3.5))
im = ax.imshow(pv.values, aspect="auto", cmap="Reds")
fig.colorbar(im, ax=ax, label="доля опозданий")
ax.set_xticks(range(len(pv.columns)))
ax.set_xticklabels(pv.columns)
ax.set_yticks(range(7))
ax.set_yticklabels(["пн", "вт", "ср", "чт", "пт", "сб", "вс"])
ax.set_title("Опоздания: день недели × час")
worst_cell = pv.stack().idxmax()
```

### explain
В ячейках тепловой карты бывает всего по 10–20 доставок, поэтому отдельные «горячие» клетки могут быть случайностью. Смотрите на полосы и пятна — например, тёмные столбцы обеда и вечера через всю неделю. Это устойчивая картина; одиночная яркая клетка — нет.
