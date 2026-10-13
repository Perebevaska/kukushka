---
title: "EDA по плану: от вопроса к выводу"
lead: "Инструменты есть: гистограммы, ящики, срезы, корреляции, метрики. Но без плана исследование превращается в сотню случайных графиков. Собираем порядок работы, разбираем ловушку, в которой срез по одному признаку говорит одно, а по двум — обратное, и учимся записывать выводы так, чтобы им верили."
files: [deliveries.csv]
recap:
  - "План EDA: вопрос и метрика → осмотр и очистка → каждый признак отдельно → метрика по признакам → проверка смешения → выводы."
  - "Гипотезы записывайте списком и закрывайте каждую: подтвердилась, нет, не хватает данных."
  - "Сравнивая признаки, смотрите на разброс метрики между группами, но только по группам достаточного размера."
  - "Парадокс Симпсона: в каждой группе A лучше B, а в сумме — хуже. Причина — разный состав групп. Лекарство — срез по двум признакам."
  - "Когда базовые доли групп сильно различаются, эффект сравнивают и разницей (п.п.), и отношением (во сколько раз) — и пишут, что именно сравнили."
  - "Вывод = наблюдение + цифра + размер группы + ограничение: «В снег вело-курьеры опаздывают в 34 % доставок против 12 % в другую погоду (56 и 816 доставок); снег был только в ноябре»."
  - "Повторяющиеся расчёты — в функции: `slice_table(df, by, col)`."
---

## План исследования

Хорошее исследование отвечает на **вопрос**, а не «смотрит на данные». Порядок, который работает почти всегда:

1. **Вопрос и метрика.** «Почему доставки опаздывают?» → метрика: доля доставок позже обещанного. Как не перепутать, чьё это среднее и на каком шаге воронки считать долю, — урок «Метрики: чьё среднее и воронка».
2. **Осмотр и очистка** — глава 3: пропуски, типы, дубли, аномалии. Записать, что убрали и почему.
3. **Каждый признак отдельно** — распределения (уроки «Распределения и гистограммы» и «Ящик с усами и выбросы»): какие значения, есть ли перекосы и редкие группы.
4. **Метрика по признакам** — срезы, динамика и связи (уроки «Срезы», «Динамика во времени», «Связи»): где метрика выше, где ниже.
5. **Проверка смешения** — не объясняется ли найденное другим признаком (этот урок).
6. **Выводы** — с цифрами, размерами групп и ограничениями.

Шаги 3–5 удобно вести как **список гипотез**: «опаздывают в снег», «опаздывает одна кофейня», «опаздывают в часы пик». Каждую проверяете и закрываете: подтвердилась, не подтвердилась, данных не хватает.

::: figure eda-plan
Шесть шагов плана. Шаги 3–5 крутятся вокруг списка гипотез: каждую проверяют по очереди и закрывают, прежде чем писать выводы.
:::

{{practice: rating-dist, p-plan}}

## Функция для среза

Срезы придётся считать много раз по разным признакам. Вместо копирования кода — функция:

```python
import pandas as pd

def slice_table(df, by, col):
    t = df.groupby(by)[col].agg(n="size", mean="mean")
    return t.sort_values("mean", ascending=False)

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
for by in ["weather", "courier", "items"]:
    print(slice_table(ok, by, "late").round(3), end="\n\n")
```

{{practice: slice-fn, min-size}}

## Какой признак важнее

Зачем: признаков у доставки пять-шесть, а разобрать каждый до конца сразу не выйдет. Нужна быстрая прикидка — с какого признака начать.

Простая оценка — **разброс** (размах) метрики между группами признака: максимум минус минимум. Пример руками: доли опозданий у типов курьера — 5.3 % (авто), 13.0 % (вело) и 73.9 % (пеший), разброс 73.9 − 5.3 = **68.6 п.п.** (процентных пунктов). У погоды доли от 19.3 % (облачно) до 34.3 % (снег), разброс 15.0 п.п. Если все группы опаздывают одинаково, разброс близок к нулю: признак с метрикой, похоже, не связан.

```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["hour"] = ok["created"].dt.hour

spread = {}
for by in ["courier", "items", "hour", "weather", "shop_id"]:
    g = ok.groupby(by)["late"].agg(["mean", "size"])
    g = g[g["size"] >= 50]                 # только надёжные группы
    spread[by] = round(g["mean"].max() - g["mean"].min(), 3)
pd.Series(spread).sort_values(ascending=False)
```

```text
courier    0.686
items      0.223
hour       0.209
weather    0.150
shop_id    0.131
dtype: float64
```

Что здесь происходит:

- `agg(["mean", "size"])` — по каждой группе доля опозданий и число доставок;
- `g[g["size"] >= 50]` — оставляем только надёжные группы. Без этой строки признак с маленькими группами (например, группа из десятка доставок) получит большой разброс просто из-за случайности;
- `g["mean"].max() - g["mean"].min()` — разброс; словарь `spread` собирает по числу на признак.

Что получилось: тип курьера с большим отрывом впереди (68.6 п.п.), дальше почти вровень число позиций (22.3) и час заказа (20.9), затем погода (15.0) и кофейня (13.1). Начинать разбор стоит с курьеров.

::: note Разброс растёт с числом групп
Чем больше групп, тем больше шансов, что среди них случайно окажутся крайние значения. У `hour` 13 групп, у `items` — 6, у `courier` — 3. Часть разброса `hour` даёт само число групп, поэтому 22.3 у `items` и 20.9 у `hour` — по сути ничья. Разброс помогает выбрать, с чего начать, но это не точная мера силы связи. А вот курьер при трёх группах впереди втрое — такой отрыв числом групп не объяснить.
:::

::: quiz
Почему, сравнивая разброс доли опозданий между группами признака, группы меньше 50 доставок отбрасывают?

- [x] В маленькой группе доля опозданий сильно скачет просто случайно — и признак получит большой разброс без реальной причины
  > В группе из 15 доставок две-три случайные задержки сдвигают долю на 13–20 процентных пунктов. Разброс должен отражать связь с метрикой, а не шум.
- [ ] Маленькие группы — почти всегда ошибки данных
  > Редкая группа может быть вполне настоящей (например, новая кофейня в первую неделю работы). Её не удаляют из данных — просто не используют для сравнения разброса.
- [ ] В маленьких группах опозданий всегда меньше
  > У случайности нет направления: маленькая группа может оказаться и лучшей, и худшей.
- [ ] Чтобы расчёт шёл быстрее
  > Групп немного, скорость тут ни при чём.
:::

{{practice: ranking}}

## Ловушка: парадокс Симпсона

Представьте две кофейни, которые возят короткие и длинные заказы:

```python
import pandas as pd
t = pd.DataFrame({
    "shop":  ["A", "A", "B", "B"],
    "route": ["короткие", "длинные", "короткие", "длинные"],
    "n":     [20, 80, 80, 20],
    "late":  [2, 40, 16, 12],
})
t["late_pct"] = t["late"] / t["n"] * 100
print(t)
total = t.groupby("shop")[["late", "n"]].sum()
print((total["late"] / total["n"] * 100).round(1))
```

В каждой группе маршрутов A лучше (10 % против 20 % и 50 % против 60 %), а в сумме A хуже: 42 % против 28 %. Причина — состав: A возит в основном длинные маршруты, где опаздывают все, а B — короткие.

::: figure simpson
Слева — доли опозданий внутри каждого типа маршрута (A лучше в обоих), справа — состав маршрутов. Общая доля — смесь групп с весами состава, поэтому в сумме A хуже.
:::

Это **парадокс Симпсона**: связь в целом может быть противоположна связи внутри каждой группы. Защита — срез по двум признакам (урок «Срезы: сравниваем группы»): прежде чем сказать «A работает хуже», проверьте, сравнимы ли условия.

::: tip Аналогия
Аня готовит любой напиток быстрее Бори — и американо, и раф. Но Ане достаются в основном долгие рафы, а Боре — быстрые американо, и по среднему времени на заказ Аня проигрывает: общее среднее сравнивает не бариста, а их заказы. Где аналогия хромает: здесь скрытый признак один и очевиден, а в данных их бывает несколько — найти их помогает только срез по двум признакам.
:::

::: predict
```python static
late_a, n_a = 2 + 40, 20 + 80
late_b, n_b = 16 + 12, 80 + 20
print(late_a / n_a > late_b / n_b)
```

- [x] `True`
- `False`
- `Ошибка ZeroDivisionError`

Почему: суммарно у A 42 опоздания из 100, у B — 28 из 100. В сумме A хуже, хотя в каждой группе маршрутов лучше.
:::

::: quiz
Условный пример: у кофейни А доля опозданий в целом ниже, чем у кофейни Б, но в каждой погоде отдельно — выше. Как это возможно?

- [x] А чаще возит в ясную погоду, где опозданий мало, — общая цифра смешивает разные условия
  > Это парадокс Симпсона: состав групп разный. Сравнивать нужно внутри одинаковых условий.
- [ ] Это ошибка в расчётах — так не бывает
  > Бывает, и довольно часто: общее среднее — взвешенная смесь групп.
- [ ] Значит, верна общая цифра, а погоду можно не учитывать
  > Как раз внутри групп сравнение честнее: при равных условиях А опаздывает чаще.
- [ ] Значит, погода не влияет на опоздания
  > Наоборот: погода влияет сильно, и поэтому смешение групп переворачивает вывод.
:::

{{practice: simpson}}

## Проверка смешения на наших данных

Зачем: в снег опаздывают в 34.3 % доставок, в другую погоду — в 22.9 %. Но в снег меньше вело-курьеров (урок «Срезы: сравниваем группы») — может, дело в составе курьеров, а не в снеге? Это ровно ловушка Симпсона из прошлого раздела. Сравним снег и не-снег **внутри** каждого типа курьера:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["snow"] = ok["weather"] == "снег"
pv = ok.pivot_table(index="courier", columns="snow", values="late", aggfunc=["mean", "size"])
pv.round(3)
```

```text
          mean         size
snow     False  True  False True
courier
авто     0.051  0.067   491    75
вело     0.115  0.339   816    56
пеший    0.720  0.943   368    35
```

Что здесь происходит:

- `aggfunc=["mean", "size"]` — две функции сразу, поэтому у таблицы **две строки заголовка**. Верхняя — функция: `mean` — доля опозданий, `size` — число доставок. Нижняя — значение `snow`: `False` — другая погода, `True` — снег;
- имя столбца здесь — пара «функция, значение». Доля опозданий вело в снег: `pv.loc["вело", ("mean", True)]` → 0.339;
- `pv["mean"]` оставляет только верхний блок `mean` — обычную таблицу со столбцами `False` и `True`. Если две строки заголовка мешают, постройте две отдельные сводные: с `aggfunc="mean"` и с `aggfunc="size"`.

Что получилось: внутри каждого типа курьера доля опозданий в снег выше — значит, эффект снега не объясняется составом курьеров. А вот «у кого он сильнее» зависит от того, как мерить:

| курьер | другая погода | снег | разница, п.п. | во сколько раз |
|---|---|---|---|---|
| авто | 5.1 % | 6.7 % | +1.6 | 1.3 |
| вело | 11.5 % | 33.9 % | +22.4 | 2.9 |
| пеший | 72.0 % | 94.3 % | +22.3 | 1.3 |

В процентных пунктах у вело и пеших эффект почти одинаковый: +22.4 и +22.3, отрыв в 0.1 п.п. ничего не значит. Но у вело доля опозданий почти **утраивается**, а пешие опаздывают почти в трёх доставках из четырёх и без снега — в разах снег добавляет им немного. У авто прибавка маленькая, и по 75 доставкам в снег её не отличить от случайности. Поэтому в выводе называйте, что сравниваете: «в снег вело-курьеры опаздывают втрое чаще: 34 % против 12 %».

::: warn Разница или отношение
Когда базовые доли сильно различаются (12 % у вело и 72 % у пеших), одинаковая разница в п.п. значит разное. Пешим до 100 % осталось всего 28 п.п. — вырасти втрое они не могут. Пишите обе цифры или явно говорите, какую сравниваете.
:::

{{practice: snow-within}}

## Разберём вместе: «почему падают оценки» по плану

Пройдём план на одном вопросе управляющего.

1. **Метрика.** Оценку ставят 56 % гостей, средняя — 4.55. Оценки нет у почти половины доставок, и это ловушка: если бы недовольные опозданием чаще молчали, средняя оценка опоздавших выглядела бы лучше, чем есть на самом деле. Поэтому сначала проверим, не связано ли само решение поставить оценку с опозданием: среди опоздавших оценку оставили 58 %, среди вовремя — 56 %. Почти одинаково — значит, сравнивать средние оценки групп можно.
2. **Срез по опозданию.** Вовремя — 4.77, с опозданием — 3.88. Разница почти в целый балл.
3. **Срез по величине опоздания** — не только «да / нет»:

| опоздание, мин | оценок | средняя |
|---|---|---|
| раньше на 10+ | 443 | 4.78 |
| 0–10 раньше | 335 | 4.76 |
| до 10 позже | 181 | 4.33 |
| 10–20 позже | 48 | 3.31 |
| 20+ позже | 27 | 1.89 |

4. **Что видно.** Привезти раньше — не плюс: 4.78 против 4.76. Опоздание до 10 минут отнимает около 0.4 балла, 10–20 минут — почти 1.5, больше 20 — почти 3 балла.
5. **Вывод.** «Оценки падают из-за опозданий больше 10 минут: их 75 из 1 034 оценённых, но средняя оценка у них 2.8 против 4.7. Короткие опоздания гости почти прощают. Предлагаю мерить не "долю опозданий", а "долю опозданий больше 10 минут"».

Что получилось: план превратил расплывчатый вопрос в конкретную метрику для бизнеса. Каждый шаг — один `groupby`, но порядок (метрика → проверка пропусков → срез → уточнение) не даёт сделать вывод раньше времени.

::: warn Типичные ошибки
- **Срез без размера группы.** Средняя 1.89 по 27 оценкам — повод присмотреться, а не «точное» число.
- **Не проверили, кто ставит оценку.** Если бы недовольные оценивали вдвое чаще, сравнение средних было бы перекошено.
- **Один признак — один вывод.** Эффект снега может быть эффектом курьеров (смешение) — проверяйте внутри групп.
- **Вывод без действия.** «Опоздания влияют на оценку» — наблюдение; «мерить опоздания больше 10 минут» — вывод.
:::

{{practice: rating-late, delay-bins}}

## Как записать вывод

Вывод, которому поверят, состоит из четырёх частей:

- **наблюдение** — что увидели;
- **цифра** — насколько;
- **размер групп** — по скольким наблюдениям;
- **ограничение** — чего мы не знаем или не проверили.

Плохо: «Снег влияет на опоздания».

Хорошо: «В снег вело-курьеры опаздывают в 34 % доставок против 12 % в другую погоду (56 и 816 доставок). Снег был только в ноябре, поэтому эффект может частично объясняться другими ноябрьскими изменениями».

Числа в выводах лучше подставлять из расчёта f-строкой, а не переписывать вручную — тогда они не разойдутся с данными.

## Практика

## task: slice-fn | Функция среза | warmup

Напишите `slice_table(df, by, col)`: возвращает таблицу по группам `by` со столбцами `n` (размер группы) и `mean` (среднее `col`), отсортированную по `mean` по убыванию.

### starter
```python
import pandas as pd

def slice_table(df, by, col):
    ...

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
slice_table(ok, "weather", "late")
```

### check
```python
import pandas as _pd
f = need('slice_table')
t = _pd.DataFrame({'g': ['a', 'a', 'b', 'c', 'c', 'c'], 'v': [1, 3, 10, 0, 0, 3]})
r = f(t, 'g', 'v')
assert list(r.columns) == ['n', 'mean'], f'Столбцы: {list(r.columns)}.'
assert list(r.index) == ['b', 'a', 'c'], f'Порядок групп: {list(r.index)} — по убыванию mean.'
assert r.loc['a', 'n'] == 2 and r.loc['c', 'mean'] == 1, 'n — размер группы, mean — среднее.'
```

### hint
Функция принимает таблицу и названия двух столбцов и **возвращает** результат (`return`), ничего не печатая.

### hint
`df.groupby(by)[col].agg(n="size", mean="mean")`, затем `sort_values("mean", ascending=False)`.

### solution
```python
import pandas as pd

def slice_table(df, by, col):
    t = df.groupby(by)[col].agg(n="size", mean="mean")
    return t.sort_values("mean", ascending=False)

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
slice_table(ok, "weather", "late")
```

## task: rating-dist | Распределение оценок | warmup

Шаг 3 плана — признак отдельно. Сохраните в `rating_pct` долю каждой оценки (1–5) среди поставленных, в процентах (1 знак), по порядку оценок, а в `rated_pct` — долю доставок с оценкой (%, 1 знак). Время доставки — 1–299 минут.

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
want = (ok['rating'].value_counts(normalize=True).sort_index() * 100).round(1)
got = need('rating_pct', _pd.Series)
assert [float(i) for i in got.index] == [float(i) for i in want.index], 'Порядок — по оценкам 1, 2, 3, 4, 5: sort_index().'
assert all(close(a, b) for a, b in zip(got.values, want.values)), 'Доли не совпадают.'
assert close(need('rated_pct'), round(ok['rating'].notna().mean() * 100, 1)), f'rated_pct = {need("rated_pct")}.'
```

### hint
`ok["rating"].value_counts(normalize=True).sort_index() * 100` — `value_counts` пропуски не считает.

### hint
Доля с оценкой — `ok["rating"].notna().mean() * 100`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
rating_pct = (ok["rating"].value_counts(normalize=True).sort_index() * 100).round(1)
rated_pct = round(ok["rating"].notna().mean() * 100, 1)
```

### explain
Две трети поставленных оценок — пятёрки. Такое распределение типично для отзывов: довольные ставят 5, а разницу видно по доле четвёрок и ниже. Поэтому средняя оценка меняется слабо, а доля «не пятёрок» — сильно.

## task: p-plan | Порядок исследования | warmup

Соберите короткое исследование в правильном порядке: загрузка, очистка, метрика, срез, вывод.

### parsons
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = ok.groupby("courier")["late"].mean().sort_values(ascending=False)
print(f"Чаще всего опаздывают: {t.index[0]} ({t.iloc[0]:.0%})")
```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)]
t = (o['actual_min'] > o['promised_min']).groupby(o['courier']).mean().sort_values(ascending=False)
want = f'Чаще всего опаздывают: {t.index[0]} ({t.iloc[0]:.0%})'
assert _lines == [want], f'Должно вывестись {want!r}. Сейчас: {_lines}'
```

### hint
`:.0%` в f-строке превращает долю 0.739 в «74%».

### hint
Очистка (фильтр 1–299 минут) — до флага опоздания; срез — после флага; вывод — последним.

## task: rating-late | Оценка и опоздание | base

Шаги 1–2 разбора «почему падают оценки». Сравните среднюю оценку доставок, привезённых вовремя и с опозданием (время 1–299 минут). Сохраните `avg_on_time`, `avg_late` (2 знака) и `gap` — разницу (вовремя минус с опозданием, 2 знака).

Затем проверьте пропуски: в `rated_on_time` и `rated_late` — доля доставок **с оценкой** в каждой группе (%, 1 знак). Зачем: если опоздавшие гости чаще не ставят оценку, сравнение средних перекошено (шаг 1 разбора).

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
m = o.groupby('late')['rating'].mean()
c = o.groupby('late')['rating'].apply(lambda s: s.notna().mean() * 100)
assert close(need('avg_on_time'), round(m[False], 2)) and close(need('avg_late'), round(m[True], 2)), f'avg_on_time, avg_late = {need("avg_on_time")}, {need("avg_late")}.'
assert close(need('gap'), round(m[False] - m[True], 2)), f'gap = {need("gap")}.'
assert close(need('rated_on_time'), round(c[False], 1)) and close(need('rated_late'), round(c[True], 1)), 'Доли доставок с оценкой не совпадают.'
```

### hint
Обе части — срез по флагу `late`: группа `False` — вовремя, `True` — с опозданием. `mean()` пропуски в `rating` пропускает сам.

### hint
`ok.groupby("late")["rating"].mean()` — Series с индексом `False` и `True`. Доля с оценкой по группе: `ok.groupby("late")["rating"].apply(lambda s: s.notna().mean() * 100)`.

### hint
```python static
m = ok.groupby("late")["rating"].mean()
avg_on_time = round(m[False], 2)
avg_late = round(m[...], 2)
gap = round(... - ..., 2)
cover = ok.groupby("late")["rating"].apply(lambda s: s.notna().mean() * 100)
rated_on_time = round(cover[...], 1)
rated_late = ...
```

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
m = ok.groupby("late")["rating"].mean()
avg_on_time = round(m[False], 2)
avg_late = round(m[True], 2)
gap = round(m[False] - m[True], 2)
cover = ok.groupby("late")["rating"].apply(lambda s: s.notna().mean() * 100)
rated_on_time = round(cover[False], 1)
rated_late = round(cover[True], 1)
```

### explain
Проверка пропусков здесь не формальность. Если бы недовольные гости чаще не ставили оценку, средняя оценка опоздавших доставок выглядела бы лучше, чем есть. Доли с оценкой в двух группах близки — значит, сравнение средних честное.

## task: delay-bins | Оценка по величине опоздания | base

Шаг 3 разбора «почему падают оценки»: соберите его таблицу сами. Разбейте опоздание `delay = actual_min − promised_min` на корзины `[-60, -10, 0, 10, 20, 60]` (`pd.cut`, правая граница включается — как по умолчанию) и посчитайте по каждой среднюю оценку и число **поставленных** оценок. Сохраните таблицу в `by_delay` со столбцами `rating` (2 знака) и `n`.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["delay"] = ok["actual_min"] - ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['delay'] = o['actual_min'] - o['promised_min']
b = _pd.cut(o['delay'], [-60, -10, 0, 10, 20, 60])
w = o.groupby(b, observed=False)['rating'].agg(['mean', 'count'])
t = need('by_delay', _pd.DataFrame)
assert list(t.columns) == ['rating', 'n'], f'Столбцы: {list(t.columns)}.'
assert len(t) == 5 and all(close(a, round(b2, 2)) for a, b2 in zip(t['rating'], w['mean'])), 'rating — средняя оценка по корзине, 2 знака.'
assert [int(x) for x in t['n']] == [int(x) for x in w['count']], 'n — число поставленных оценок (count, без пропусков).'
```

### hint
Два шага: сначала `pd.cut` превращает минуты опоздания в корзины, потом `groupby` по этим корзинам считает среднюю оценку и число оценок.

### hint
`count`, а не `size`: `size` считает все доставки корзины, а `count` — только строки, где оценка есть.

### hint
```python static
b = pd.cut(ok["delay"], [-60, -10, 0, 10, 20, 60])
by_delay = ok.groupby(b, observed=False)["rating"].agg(rating="mean", n=...)
by_delay["rating"] = ...
```

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["delay"] = ok["actual_min"] - ok["promised_min"]
b = pd.cut(ok["delay"], [-60, -10, 0, 10, 20, 60])
by_delay = ok.groupby(b, observed=False)["rating"].agg(rating="mean", n="count")
by_delay["rating"] = by_delay["rating"].round(2)
by_delay
```

### explain
Пока доставка приезжает вовремя, гостю почти всё равно, на 2 или на 15 минут раньше. А после обещанного времени оценка падает быстро. Это аргумент для бизнеса: важнее не «везти быстрее», а «не нарушать обещание» — например, обещать реалистичное время.

## task: ranking | Какой признак важнее | plus

Для признаков `courier`, `weather`, `shop_id`, `items` и часа заказа (`hour`) посчитайте разброс доли опозданий между группами (максимум минус минимум), учитывая только группы, где **не меньше 50** доставок. Сохраните результат в `ranking` — Series «признак → разброс в процентных пунктах (1 знак)», отсортированную по убыванию.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["hour"] = ok["created"].dt.hour

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
o['hour'] = o['created'].dt.hour
w = {}
for by in ['courier', 'weather', 'shop_id', 'items', 'hour']:
    g = o.groupby(by)['late'].agg(['mean', 'size'])
    g = g[g['size'] >= 50]
    w[by] = round((g['mean'].max() - g['mean'].min()) * 100, 1)
w = _pd.Series(w).sort_values(ascending=False)
r = need('ranking', _pd.Series)
assert set(r.index) == set(w.index), f'Признаки: {sorted(r.index)}.'
assert all(close(r[k], w[k]) for k in w.index), f'Разбросы: {r.to_dict()}, а нужно {w.to_dict()}. Группы меньше 50 доставок исключены? Значения — в процентных пунктах.'
assert list(r.values) == sorted(r.values, reverse=True), 'Отсортируйте по убыванию.'
```

### hint
Сначала добавьте `hour = created.dt.hour` и флаг `late`.

### hint
Цикл по списку признаков. Внутри: `g = ok.groupby(by)["late"].agg(["mean", "size"])`, `g = g[g["size"] >= 50]`, разброс — `(g["mean"].max() - g["mean"].min()) * 100`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["hour"] = ok["created"].dt.hour
spread = {}
for by in ["courier", "weather", "shop_id", "items", "hour"]:
    g = ok.groupby(by)["late"].agg(["mean", "size"])
    g = g[g["size"] >= 50]
    spread[by] = round((g["mean"].max() - g["mean"].min()) * 100, 1)
ranking = pd.Series(spread).sort_values(ascending=False)
ranking
```

### explain
Курьер — с огромным отрывом (разброс 68.6 п.п.), дальше число позиций (22.3) и час заказа (20.9), погода (15.0) и кофейня (13.1). Порог «не меньше 50 доставок» не даёт маленьким группам победить случайно: без него редкий час или большой заказ мог бы выдать разброс 100 п.п. по трём доставкам.

## task: simpson | Парадокс на маленьком примере | plus

Две кофейни и два типа маршрутов. По таблице `t` посчитайте:

- `a_better_everywhere` — `True`, если доля опозданий A меньше, чем у B, **в каждом** типе маршрута;
- `a_better_total` — `True`, если суммарная доля опозданий A меньше, чем у B.

### starter
```python
import pandas as pd
t = pd.DataFrame({
    "shop":  ["A", "A", "B", "B"],
    "route": ["короткие", "длинные", "короткие", "длинные"],
    "n":     [30, 70, 90, 10],
    "late":  [3, 28, 18, 5],
})

```

### check
```python
assert need('a_better_everywhere') is True or need('a_better_everywhere') == True, 'a_better_everywhere неверно. Посчитайте долю опозданий в каждой строке (late / n), разверните таблицу: строки — route, столбцы — shop, и сравните A и B в каждой строке. Все ли A < B?'
assert need('a_better_total') == False, 'a_better_total неверно. Суммарная доля — это все опоздания кофейни на все её доставки: сначала сложите late и n по кофейне, потом делите. Среднее из долей маршрутов не подходит — оно не учитывает, сколько доставок в каждом маршруте.'
assert 'groupby' in _code or 'pivot' in _code, 'Посчитайте через pandas, а не вписывайте ответ.'
```

### hint
Две разные доли. «В каждом маршруте» — доля по строкам таблицы, сравнение A и B внутри маршрута. «Суммарно» — все опоздания кофейни на все её доставки.

### hint
Доля по строкам: `t["pct"] = t["late"] / t["n"]`; по маршрутам удобно развернуть `t.pivot(index="route", columns="shop", values="pct")`. Суммарно: `s = t.groupby("shop")[["late", "n"]].sum()`, доля — `s["late"] / s["n"]`.

### hint
```python static
t["pct"] = t["late"] / t["n"]
by_route = t.pivot(index="route", columns="shop", values="pct")
a_better_everywhere = bool((by_route["A"] < by_route[...]).all())
s = t.groupby("shop")[["late", "n"]].sum()
total = s["late"] / s[...]
a_better_total = bool(total["A"] < ...)
```

### solution
```python
import pandas as pd
t = pd.DataFrame({
    "shop":  ["A", "A", "B", "B"],
    "route": ["короткие", "длинные", "короткие", "длинные"],
    "n":     [30, 70, 90, 10],
    "late":  [3, 28, 18, 5],
})
t["pct"] = t["late"] / t["n"]
by_route = t.pivot(index="route", columns="shop", values="pct")
a_better_everywhere = bool((by_route["A"] < by_route["B"]).all())
s = t.groupby("shop")[["late", "n"]].sum()
total = s["late"] / s["n"]
a_better_total = bool(total["A"] < total["B"])
```

### explain
В каждом типе маршрута A лучше B (10 % против 20 % на коротких, 40 % против 50 % на длинных), а в сумме A хуже (31 из 100 против 23 из 100). Причина — состав: у A 70 % маршрутов длинные, у B — 10 %. Это и есть парадокс Симпсона: сравнивать суммы можно, только если группы похожи по составу. Типичная ошибка — усреднить доли маршрутов: у A (10 % + 40 %) / 2 = 25 %, у B (20 % + 50 %) / 2 = 35 %, и A «лучше». Такое среднее делает вид, что у обеих кофеен маршруты поровну, — то есть выбрасывает как раз состав, из-за которого всё и происходит.

## task: snow-within | Снег внутри групп | star

Проверьте, не объясняется ли эффект снега составом курьеров (раздел «Проверка смешения на наших данных»). Для каждого типа курьера посчитайте долю опозданий в снег и в другую погоду и число доставок в снег и в другую погоду. Сохраните:

- `snow_effect` — словарь «тип курьера → разница долей (снег минус другая погода), п.п., 1 знак»;
- `snow_ratio` — словарь «тип курьера → во сколько раз доля в снег больше доли в другую погоду (снег / другая погода), 2 знака»;
- `conclusion` — вывод для типа курьера с **наибольшим `snow_ratio`**, собранный f-строкой по шаблону:

«В снег <тип> опаздывают в <X> % доставок против <Y> % в другую погоду (<N1> и <N2> доставок)» — X и Y округлены до целого, N1 — доставок в снег, N2 — в другую погоду.

Почему лидера выбираем по отношению, а не по разнице: в п.п. у двух типов курьеров эффект почти равный, и «победитель» по разнице определялся бы десятой долей пункта.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["snow"] = ok["weather"] == "снег"

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
o = d[d['actual_min'].between(1, 299)].copy()
o['late'] = o['actual_min'] > o['promised_min']
o['snow'] = o['weather'] == 'снег'
m = o.pivot_table(index='courier', columns='snow', values='late', aggfunc='mean')
n = o.pivot_table(index='courier', columns='snow', values='late', aggfunc='size')
eff = ((m[True] - m[False]) * 100).round(1)
rat = (m[True] / m[False]).round(2)
got = dict(need('snow_effect'))
assert set(got) == set(eff.index), f'Ключи snow_effect: {sorted(got)} — нужны все типы курьера.'
assert all(close(got[k], eff[k], 0.051) for k in eff.index), f'snow_effect = {got}. Нужна разница долей «снег минус другая погода» в процентных пунктах (× 100), 1 знак.'
gr = dict(need('snow_ratio'))
assert set(gr) == set(rat.index), f'Ключи snow_ratio: {sorted(gr)} — нужны все типы курьера.'
assert all(close(gr[k], rat[k], 0.006) for k in rat.index), f'snow_ratio = {gr}. Нужно отношение долей: снег / другая погода, 2 знака (не разница).'
c = rat.idxmax()
want = f'В снег {c} опаздывают в {round(m.loc[c, True] * 100)} % доставок против {round(m.loc[c, False] * 100)} % в другую погоду ({n.loc[c, True]} и {n.loc[c, False]} доставок)'
assert need('conclusion') == want, f'conclusion = {need("conclusion")!r}. Сверьте с шаблоном: тип с наибольшим snow_ratio, доли — целые проценты, сначала доставки в снег, потом в другую погоду.'
assert uses_fstring(), 'Соберите вывод f-строкой из рассчитанных чисел.'
```

### hint
Нужны две сводные таблицы по курьерам и флагу `snow`: в одной доли опозданий, в другой число доставок. Из таблицы долей получаются и разница, и отношение.

### hint
Доля — `pivot_table(index="courier", columns="snow", values="late", aggfunc="mean")`, размер — то же с `aggfunc="size"`. Столбцы называются `True` и `False`. Тип с наибольшим отношением — `idxmax()`, округление до целого — `round(x * 100)`.

### hint
```python static
m = ok.pivot_table(index="courier", columns="snow", values="late", aggfunc="mean")
n = ok.pivot_table(index="courier", columns="snow", values="late", aggfunc=...)
snow_effect = ((m[True] - m[False]) * 100).round(1).to_dict()
ratio = (m[True] / m[False]).round(2)
snow_ratio = ratio.to_dict()
c = ratio.idxmax()
conclusion = f"В снег {c} опаздывают в {round(m.loc[c, True] * 100)} % доставок против ... % в другую погоду (... и ... доставок)"
```

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["snow"] = ok["weather"] == "снег"
m = ok.pivot_table(index="courier", columns="snow", values="late", aggfunc="mean")
n = ok.pivot_table(index="courier", columns="snow", values="late", aggfunc="size")
eff = ((m[True] - m[False]) * 100).round(1)
snow_effect = eff.to_dict()
ratio = (m[True] / m[False]).round(2)
snow_ratio = ratio.to_dict()
c = ratio.idxmax()
conclusion = (f"В снег {c} опаздывают в {round(m.loc[c, True] * 100)} % доставок "
              f"против {round(m.loc[c, False] * 100)} % в другую погоду "
              f"({n.loc[c, True]} и {n.loc[c, False]} доставок)")
conclusion
```

### explain
Эффект снега есть внутри каждого типа курьера — значит, он не объясняется тем, что в снег возят другие курьеры. По разнице вело и пешие почти равны (+22.4 и +22.3 п.п.), а по отношению вело впереди явно: 2.95 против 1.31 у пеших и авто. Вывод: «В снег вело опаздывают в 34 % доставок против 12 % в другую погоду (56 и 816 доставок)». Если бы лидера выбирали по разнице, результат зависел бы от десятой доли пункта — на данных за другой месяц он мог бы смениться. Ограничение остаётся: снег был только в ноябре, и с ним совпали другие ноябрьские изменения. Эту оговорку стоит добавить к выводу.

## task: min-size | Срез с порогом размера | base

Шаг плана «срез + размер группы». По доставкам (время 1–299 минут) посчитайте срез по числу позиций в заказе (`items`): столбцы `n` (число доставок) и `late_pct` (доля опозданий, %, 1 знак). Оставьте только группы, где `n >= 100`, отсортируйте по убыванию `late_pct` и сохраните в `by_items`. В `worst_items` — число позиций с наибольшей долей опозданий среди оставшихся групп.

Одна из шести групп меньше 100 доставок — после фильтра её в таблице быть не должно.

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
g0 = o.groupby('items')['late'].agg(n='size', late_pct='mean'); g0['late_pct'] = (g0['late_pct'] * 100).round(1)
g = g0[g0['n'] >= 100].sort_values('late_pct', ascending=False)
t = need('by_items', _pd.DataFrame)
for c in ('n', 'late_pct'):
    assert c in t.columns, f'В by_items нет столбца {c}.'
small = [k for k in g0.index if g0.loc[k, 'n'] < 100]
left = [k for k in small if k in list(t.index)]
assert not left, f'В таблице осталась группа items = {left[0]}: в ней {g0.loc[left[0], "n"]} доставок. Фильтр n >= 100 должен её убрать — фильтруйте по столбцу n после groupby.'
assert sorted(t.index) == sorted(g.index), f'Группы в by_items: {sorted(t.index)}. Нужны все группы, где не меньше 100 доставок.'
assert all(close(t.loc[k, 'late_pct'], g.loc[k, 'late_pct']) for k in g.index), 'late_pct не совпадает: доля опозданий × 100, 1 знак.'
assert list(t.index) == list(g.index), 'Группы на месте, но порядок не тот: sort_values("late_pct", ascending=False).'
assert need('worst_items') == g.index[0], f'worst_items = {need("worst_items")!r} — возьмите первую строку отсортированной таблицы.'
```

### hint
Сначала срез — `groupby` по `items` с двумя показателями, потом фильтр по размеру, потом сортировка. Фильтр — по готовой таблице среза, а не по исходным строкам.

### hint
`ok.groupby("items")["late"].agg(n="size", late_pct="mean")`, затем доля в проценты и округление. Фильтр `t[t["n"] >= 100]`, лидер — `index[0]`.

### hint
```python static
t = ok.groupby("items")["late"].agg(n="size", late_pct="mean")
t["late_pct"] = (t["late_pct"] * 100).round(1)
by_items = t[t["n"] >= ...].sort_values(..., ascending=False)
worst_items = by_items.index[...]
```

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
t = ok.groupby("items")["late"].agg(n="size", late_pct="mean")
t["late_pct"] = (t["late_pct"] * 100).round(1)
by_items = t[t["n"] >= 100].sort_values("late_pct", ascending=False)
worst_items = by_items.index[0]
by_items
```

### explain
Порог отсекает одну группу — заказы из 6 позиций: 90 доставок, 36.7 % опозданий. Лидер — 5 позиций (39.3 %, 135 доставок). Здесь лидер от фильтра не поменялся, но разница 39.3 и 36.7 % при 135 и 90 доставках — в пределах случайности: на данных за другой месяц маленькая группа «6 позиций» легко обогнала бы соседей. Порог размера стоит держать в функции среза всегда: на других данных одна редкая группа из пяти строк легко «победит» с долей 80 %. Типичная ошибка — отфильтровать исходные строки (`ok[ok["items"] ...]`) вместо готовой таблицы: размер группы известен только после `groupby`.
