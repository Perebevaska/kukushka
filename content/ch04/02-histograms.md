---
title: Распределения и гистограммы
lead: "Среднее время доставки — около 35 минут. Это много или мало? Зависит от того, как время распределено: все ли доставки около 35 минут или половина приезжает за 20, а часть — через час. Учимся смотреть на распределение целиком: гистограмма, форма, квантили."
files: [deliveries.csv]
recap:
  - "Распределение — какие значения встречаются и как часто. Его рисует гистограмма: `ax.hist(s, bins=30)`."
  - "Сначала уберите невозможные значения и пропуски, иначе один выброс сожмёт картинку в один столбец."
  - "`bins` — число корзин; `range=(0, 120)` — какой диапазон показывать."
  - "Хвост вправо (скошенное распределение): среднее больше медианы. Для таких данных опирайтесь на медиану и квантили."
  - "Форму ждут заранее по тому, как рождаются значения: длительности и деньги — хвост вправо, счётчики событий за день — Пуассон, суммы многих вкладов — колокол, минута часа — ровно. Несовпадение — повод искать ошибку или историю."
  - "Пуассон: доля интервалов с k событиями — `lam ** k * math.exp(-lam) / math.factorial(k)`, где `lam` — среднее. Счётчик по дням достраивайте пустыми днями: `reindex(days, fill_value=0)`."
  - "Квантиль: `s.quantile(0.9)` — 90 % значений не больше этого числа. Понятная бизнесу фраза: «90 % доставок — быстрее 48 минут»."
  - "Целые значения с несколькими вариантами (число позиций) — не гистограмма, а столбцы `value_counts().sort_index()`."
  - "Вертикальная линия-отметка: `ax.axvline(x, color=\"red\", linestyle=\"--\")`."
---

## Новые данные: доставка

С осени «Зерно» возит кофе курьерами. Выгрузка `deliveries.csv` — все доставки за сентябрь–ноябрь:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
print(d.shape)
d.head()
```

Столбцы: `created` — когда создан заказ, `shop_id` — кофейня, `courier` — тип курьера (пеший, вело, авто), `distance_km` — расстояние, `weather` — погода, `items` — позиций в заказе, `amount` — сумма, `promised_min` — обещанное время доставки, `actual_min` — фактическое, `rating` — оценка гостя (если поставил).

Главный вопрос этой главы: **почему доставка опаздывает**. В проекте мы ответим на него целиком, а в уроках научимся инструментам.

## Что такое распределение

`describe()` даёт несколько чисел: среднее, медиану, квартили. **Распределение** — более полная картина: какие значения встречаются и как часто. Рисуют его **гистограммой**: ось X делят на одинаковые отрезки (корзины, bins), высота столбца — сколько значений попало в отрезок.

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(d["distance_km"], bins=30)
ax.set_title("Расстояние доставки")
ax.set_xlabel("км")
ax.set_ylabel("доставок")
```

Большая часть доставок — в пределах 1–4 км, а справа тянется длинный редкий «хвост» до 15 км. Это видно только на картинке: в `describe()` хвост прячется за одним числом `max`.

::: predict
```python static
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
counts, edges, bars = ax.hist([1, 2, 2, 3, 10], bins=3)
print(counts.tolist())
```

- `[1.0, 2.0, 1.0]`
- [x] `[4.0, 0.0, 1.0]`
- `[3.0, 1.0, 1.0]`

Почему: диапазон от 1 до 10 делится на три равные корзины: 1–4, 4–7, 7–10. В первую попали 1, 2, 2, 3, во вторую — ничего, в третью — 10. `hist` возвращает и сами количества — их удобно проверять.
:::

{{practice: hist-km, p-hist}}

## Сначала — невозможные значения

Попробуем нарисовать фактическое время доставки:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
print(d["actual_min"].describe())
fig, ax = plt.subplots(figsize=(8, 3))
ax.hist(d["actual_min"].dropna(), bins=30)
ax.set_title("Время доставки — как есть")
```

Почти все доставки слились в один столбец слева. Виноваты аномалии (урок «Аномалии и проверка на здравый смысл» главы 3): доставки «за 1 281 минуту» — курьер забыл закрыть заказ, и отрицательные — сбой часов. Ось растянулась до 1 300 минут, а настоящие данные заняли её крошечную часть.

Правило: перед гистограммой уберите невозможные значения. Для доставки оставим время от 1 до 299 минут. Почему именно 299? Посмотрите на сами «долгие» доставки — `d[d["actual_min"] > 299]`: их пять, и все от 735 до 1 281 минуты, то есть 12–21 час на заказ, обещанный за 30–60 минут. Так кофе не возят — это незакрытые заказы. Самая долгая настоящая доставка — 96 минут, а между 96 и 735 нет ни одного значения. Порог «меньше 5 часов» (299 минут) стоит в этом пустом промежутке с запасом: он отрезает все забытые заказы и не задевает ни одной настоящей доставки.

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
print("убрали:", len(d) - len(ok), "из", len(d))

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(ok["actual_min"], bins=40)
ax.set_title("Время доставки, мин")
ax.set_xlabel("минут")
ax.set_ylabel("доставок")
```

Теперь видна форма: горб около 30 минут и хвост вправо. Пропуски (`NaN`) `between` тоже отбросил: сравнение с `NaN` даёт `False`.

## Корзины: сколько и какие

Число корзин меняет картинку. Слишком мало — форма теряется; слишком много — столбцы «шумят»:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]["actual_min"]
fig, axes = plt.subplots(1, 3, figsize=(12, 3))
for ax, bins in zip(axes, [5, 30, 300]):
    ax.hist(ok, bins=bins)
    ax.set_title(f"bins={bins}")
fig.tight_layout()
```

Удобно задавать корзины «круглой» ширины, тогда столбцы легко читать. `range` ограничивает диапазон: `bins=24, range=(0, 120)` — 24 корзины по 5 минут от 0 до 120.

### Разберём вместе: гистограмма руками

Десять доставок: 12, 18, 22, 25, 27, 31, 33, 38, 45, 70 минут. Разложим по корзинам шириной 10 минут:

| корзина | какие попали | сколько |
|---|---|---|
| 10–20 | 12, 18 | 2 |
| 20–30 | 22, 25, 27 | 3 |
| 30–40 | 31, 33, 38 | 3 |
| 40–50 | 45 | 1 |
| 50–60 | — | 0 |
| 60–70 | — | 0 |
| 70–80 | 70 | 1 |

Высота столбца — число доставок в корзине. Две пустые корзины между 45 и 70 сразу показывают: 70 минут — одиночка, далеко от остальных. В таблице из десяти чисел это легко пропустить, на картинке — нет.

Граница корзины принадлежит правой корзине: 70 попадает в 70–80, а не в 60–70. Поэтому одно и то же значение на границе может «переехать» при сдвиге корзин — ещё одна причина пробовать разную ширину.

Исключение одно — **самая последняя корзина**: она включает и свою правую границу, иначе максимальное значение не попало бы никуда. Так было в предикте выше: при `bins=3` корзины — 1–4, 4–7, 7–10, и 10 стоит на правой границе последней, но посчитано в ней.

::: figure hist-by-hand
Десять доставок по корзинам в 10 минут: высота стопки — число в корзине. Две пустые корзины отделяют 70 минут от остальных; 70 стоит на границе и уходит в правую корзину.
:::

```python
import numpy as np
counts, edges = np.histogram([12, 18, 22, 25, 27, 31, 33, 38, 45, 70], bins=range(10, 90, 10))
print(counts.tolist())
print(edges.tolist())
```

Что здесь происходит:

- **numpy** (`np`) — библиотека для вычислений над массивами чисел, на ней построены pandas и matplotlib. Здесь из неё нужна одна функция;
- `np.histogram` считает то же, что `ax.hist`, но **без картинки**: только высоты столбцов `counts` и границы корзин `edges`. Удобно, когда нужны сами числа;
- в `bins` здесь передано не число корзин, а **список границ**: `range(10, 90, 10)` — это 10, 20, …, 80. Восемь границ дают семь корзин 10–20, …, 70–80 — ровно как в таблице. `ax.hist` понимает `bins` так же: число — «раздели диапазон поровну», список — «вот границы».

{{practice: five-min}}

## Форма распределения

Три формы встречаются чаще всего:

- **симметричное** — горб посередине, хвосты одинаковые; среднее ≈ медиана;
- **скошенное вправо** — длинный хвост больших значений (время, деньги, расстояния); среднее **больше** медианы;
- **с двумя горбами** — обычно в данных смешаны две разные группы (например, пешие и авто-курьеры).

У скошенного распределения хвост тянет среднее за собой, а медиана остаётся на месте:

::: predict
```python static
import pandas as pd
s = pd.Series([20, 25, 30, 35, 200])
print(s.mean(), s.median())
```

- `30.0 30.0`
- [x] `62.0 30.0`
- `62.0 62.0`

Почему: одно большое значение 200 подняло среднее до 62, а медиана — середина упорядоченного ряда — осталась 30. Поэтому для времени, денег и расстояний медиана обычно честнее среднего.
:::

::: figure mean-median
Тот же ряд 20, 25, 30, 35, 200 на оси: медиана — третье значение по порядку, а среднее одна долгая доставка утащила к 62.
:::

::: tip Аналогия
За стойкой девять гостей заплатили по 300 ₽, а десятый взял кофе на весь офис за 3000 ₽. Средний чек — 570 ₽, хотя так не платил никто, а медиана — 300 ₽, чек типичного гостя. Где аналогия хромает: медиана честнее не всегда — для выручки за день нужна сумма, а в ней большой заказ законно весит много.
:::

Покажем среднее и медиану прямо на гистограмме вертикальными линиями:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
km = d["distance_km"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(km, bins=30, color="lightgray")
ax.axvline(km.median(), color="tab:blue", linestyle="--", label=f"медиана {km.median():.1f}")
ax.axvline(km.mean(), color="tab:red", linestyle="--", label=f"среднее {km.mean():.1f}")
ax.legend()
ax.set_title("Расстояние доставки, км")
```

`label` у линии и `ax.legend()` — подпись в легенде.

::: quiz
У времени доставки среднее заметно больше медианы. Что это говорит о распределении?

- [x] У него длинный хвост вправо: немного очень долгих доставок тянут среднее вверх
  > Медиана устойчива к хвосту, среднее — нет. Поэтому для типичной доставки в отчёте лучше медиана.
- [ ] Большинство доставок дольше среднего
  > Наоборот: при хвосте вправо больше половины доставок короче среднего.
- [ ] В данных ошибка: среднее и медиана должны совпадать
  > Они совпадают только у симметричных распределений.
- [ ] Хвост влево: есть очень быстрые доставки
  > Хвост влево тянул бы среднее вниз, ниже медианы.
:::

{{practice: skew, vline}}

## Какую форму ожидать

Опытный аналитик, прежде чем рисовать гистограмму, спрашивает себя: **какая форма тут должна получиться?** Форму часто можно угадать по тому, как рождаются значения. Если картинка совпала с ожиданием — данные, скорее всего, в порядке. Если нет — это либо ошибка в данных, либо история, которую стоит раскопать.

| как рождается значение | пример в «Зерне» | ожидаемая форма |
|---|---|---|
| длительность, сумма, расстояние: не меньше нуля, иногда очень большие | время доставки, сумма заказа, км | хвост вправо |
| счётчик редких независимых событий за отрезок времени | доставок у кофейни за день | распределение Пуассона: горб около среднего, при маленьком среднем — хвост вправо |
| сумма или среднее многих мелких независимых вкладов | выручка кофейни за день, средний чек за неделю | колокол (нормальное распределение) — подробнее в главе 5 |
| момент внутри цикла, на который никто не влияет | минута часа, когда создан заказ | ровная (равномерное распределение) |
| оценка по шкале, где почти все довольны | оценка гостя 1–5 | гора у верхнего края: из 1 055 оценок 707 — пятёрки |
| смесь разных групп | время пеших и авто-курьеров вместе | два горба |

::: tip Аналогия
Врач, прежде чем смотреть анализ, знает, какой у здорового человека должна быть температура. 36.6 — норма, 42 — либо болезнь, либо сломанный градусник. С данными так же: ожидание формы — это «норма», а отклонение от неё — повод для вопроса. Где аналогия хромает: «нормы» для данных никто не утверждал — ожидание вы выводите сами из того, как данные появляются, и иногда ошибаетесь в нём.
:::

### Пуассон: сколько доставок бывает за день

**Зачем.** Кофейня KZN-1 делает в среднем 4.7 доставки в день. Курьеров надо держать не под средний день, а под плохой: сколько доставок бывает в загруженный день и как часто такие дни случаются? Среднее на это не отвечает — нужно распределение «доставок за день». И его форму можно предсказать заранее.

Если события происходят **независимо друг от друга** и с постоянной средней частотой — гости заказывают доставку каждый сам по себе, — число событий за день подчиняется **распределению Пуассона**. Его форма задаётся одним числом — средним числом событий за день $\lambda$ (лямбда).

Игрушечный пример: кофейня в среднем делает $\lambda = 2$ доставки в день. Какая доля дней будет с 0, 1, 2 доставками? Каждая следующая доля получается из предыдущей умножением на $\lambda / k$:

1. $k = 0$ (ни одной доставки): $e^{-2} \approx 0.135$ — в 13.5 % дней доставок нет совсем. Здесь $e \approx 2.718$ — постоянная, как $\pi$; $e^{-2}$ на калькуляторе — `math.exp(-2)`.
2. $k = 1$: $0.135 \cdot 2 / 1 = 0.271$.
3. $k = 2$: $0.271 \cdot 2 / 2 = 0.271$.

Дальше считать руками незачем — то же самое в общем виде записывают формулой:

$$P(k) = \frac{\lambda^k \, e^{-\lambda}}{k!}$$

Здесь $k$ — число доставок за день (0, 1, 2, …), $P(k)$ — доля дней, когда их ровно $k$, $k!$ — факториал: $1 \cdot 2 \cdot \ldots \cdot k$ (а $0! = 1$). Остальные $k$ посчитает код:

```python
import math
lam = 2
for k in range(7):
    print(k, round(lam ** k * math.exp(-lam) / math.factorial(k), 3))
```

Горб на 1–2, хвост вправо: дни с 5–6 доставками бывают (около 4 % и 1 %), а дней «минус одна доставка» не бывает. Чем больше $\lambda$, тем симметричнее горб.

::: predict
```python static
import math
lam = 1
print(round(math.exp(-lam), 3))
```

- `0.0`
- [x] `0.368`
- `1.0`

Почему: при $k = 0$ формула превращается в $e^{-\lambda}$. Даже если в среднем случается одно событие в день, примерно в 37 % дней не случается ни одного. Пустые дни — нормальная часть картины, а не сбой.
:::

### На реальных данных: доставки KZN-1 по дням

Проверим ожидание на кофейне KZN-1: посчитаем доставки за каждый из 91 дня осени и сравним доли с формулой Пуассона.

```python
import math
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
k = d[d["shop_id"] == "KZN-1"]
days = pd.date_range("2026-09-01", "2026-11-30")              # все дни, включая пустые
per_day = k.groupby(k["created"].dt.normalize()).size().reindex(days, fill_value=0)
lam = per_day.mean()

obs = per_day.value_counts(normalize=True).sort_index()       # доля дней с k доставками
exp = pd.Series({j: lam ** j * math.exp(-lam) / math.factorial(j) for j in obs.index})
print("λ =", round(lam, 2), "| дней:", len(per_day))

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.bar(obs.index - 0.2, obs.values, width=0.4, label="на деле")
ax.bar(exp.index + 0.2, exp.values, width=0.4, label="по Пуассону")
ax.set_xlabel("доставок за день")
ax.set_ylabel("доля дней")
ax.legend()
ax.set_title("KZN-1: доставки за день похожи на Пуассона")
```

Что здесь происходит:

- `dt.normalize()` обрезает время до полуночи — получается день; `groupby(...).size()` — доставок в каждый день;
- `reindex(days, fill_value=0)` добавляет дни **без** доставок с нулём. Без этого `groupby` просто не знает о пустых днях, и среднее завысится;
- `value_counts(normalize=True).sort_index()` — доля дней с 0, 1, 2… доставками;
- `exp` — формула Пуассона с $\lambda$, равной среднему по данным;
- `obs.index - 0.2` и `+ 0.2` сдвигают пары столбцов, чтобы они стояли рядом, а не друг на друге.

::: figure empty-days
Почему нужен `reindex`: `groupby` по дням возвращает только дни с доставками. На условной неделе среднее без пустых дней — 1.75, с ними — 1.00, а доля дней без доставок теряется совсем.
:::

Как читать: $\lambda = 4.71$, и столбцы «на деле» идут за столбцами формулы — горб на 4–5, хвост до 10. Отличия в отдельных столбцах — не больше 5 с небольшим пунктов; при 91 дне это обычный случайный разброс. Вывод для бизнеса: доставки приходят «по одной», независимо, без явных всплесков. Ответ на вопрос из начала раздела: дней с 8 и больше доставками было 10 из 91 (11 %), формула ждёт 10.5 % — примерно каждый десятый день; максимум за осень — 10 доставок. Такой день — не аномалия, а нормальный хвост; планировать курьеров надо под него, а не под среднее 4.7.

Равномерную форму проверить ещё проще: минута, в которую создан заказ, ни от чего не зависит, поэтому по корзинам в 5 минут заказы должны лечь ровно. Пик на минуте 0 значил бы, что время кто-то вводил вручную и округлял.

«Ровно» не значит «одинаково до штуки»: даже у честного счётчика корзины случайно отличаются. Ориентир для оценки на глаз: если в корзину в среднем попадает $n$ значений, обычный случайный разброс — около $\sqrt{n}$ штук. При 100 значениях на корзину это ±10, то есть ±10 %, при 400 — ±20, то есть ±5 %. Отклонение в 1–2 таких шага — случайность, в 3 и больше — повод присмотреться.

::: warn Типичные ошибки
- **Ждать колокол от всего подряд.** Время, деньги и счётчики почти никогда не бывают симметричными; колокол получается у сумм и средних многих мелких вкладов.
- **Счётчик без пустых интервалов.** `groupby` по дням не создаёт дней без событий: среднее завышено, доля нулей потеряна. Достраивайте полный календарь через `reindex(..., fill_value=0)`.
- **Подгонять ожидание под картинку.** Сначала запишите, какую форму ждёте и почему, потом рисуйте. Иначе любая форма «объяснится» задним числом.
- **Искать точное совпадение с формулой.** На 91 дне доли будут отличаться на несколько пунктов просто из-за случайности; смотрите на общую форму.
:::

{{practice: minute-flat, poisson-day}}

## Квантили: язык для бизнеса

Медиана — это квантиль 0.5: половина значений меньше. Так же определяют любые другие: квантиль 0.9 — значение, меньше которого 90 % данных.

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d[d["actual_min"].between(1, 299)]["actual_min"]
print(t.quantile([0.5, 0.75, 0.9, 0.95]))
```

Это готовые фразы для отчёта: «половина доставок — быстрее 33 минут, 90 % — быстрее 48». Такие формулировки понятнее, чем «среднее 34,5 минуты» плюс отдельная мера разброса (её разберём в уроке «Ящик с усами и выбросы»).

::: sql
`PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY actual_min)` — квантиль 0.9 в SQL.
:::

{{practice: p90}}

## Целые значения: столбцы, а не гистограмма

Число позиций в заказе — от 1 до 6. Гистограмма для таких данных неудобна: корзины ложатся между целыми числами. Лучше просто посчитать каждое значение:

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
counts = d["items"].value_counts().sort_index()
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(counts.index, counts.values)
ax.set_title("Позиций в заказе")
ax.set_xlabel("позиций")
ax.set_ylabel("заказов")
```

::: warn Типичные ошибки
- **Гистограмма без очистки.** Одно время «1440 минут» растянет ось, и все нормальные доставки сожмутся в один столбец.
- **Корзин слишком мало или много.** 5 корзин прячут форму, 500 — превращают её в шум; пробуйте 2–3 варианта.
- **Гистограмма для целых значений.** Позиции 1–6 — это категории, рисуйте столбцы `value_counts().sort_index()`.
- **Среднее как «типичное».** При хвосте вправо типичное значение — медиана.
:::

{{practice: items}}

## Сравнить два распределения

Две гистограммы на одной оси с прозрачностью `alpha` показывают, чем группы отличаются. Если группы разного размера, выручит `density=True`: высота столбцов станет долей, а не количеством, и формы можно сравнивать честно.

```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
fig, ax = plt.subplots(figsize=(8, 3.5))
for courier in ["пеший", "авто"]:
    ax.hist(ok.loc[ok["courier"] == courier, "actual_min"], bins=30, range=(0, 90),
            alpha=0.5, density=True, label=courier)
ax.legend()
ax.set_title("Время доставки: пешие и авто")
```

Пешие курьеры в среднем возят дольше, хотя ездят на короткие расстояния. Запомним это — вернёмся в проекте.

::: warn Типичная ошибка
**Сравнение групп разного размера по высоте.** Без `density=True` группа, где доставок больше, выше почти во всех корзинах, и кажется, что «у неё больше долгих доставок», хотя форма может быть та же. Для групп разного объёма сравнивайте доли: `density=True`.
:::

::: quiz
После очистки доставок на авто почти в полтора раза больше, чем пеших. Зачем при сравнении их гистограмм на одной оси ставить `density=True`?

- [x] Чтобы высота столбцов была долей, а не количеством: иначе большая группа выглядит выше почти везде, и формы не сравнить
  > Вопрос «чем распределения отличаются» — про форму: где горб, насколько длинный хвост. `density=True` приводит группы к одному масштабу.
- [ ] Чтобы убрать выбросы из обеих групп
  > `density` не отбрасывает значения; выбросы убирают отдельно — через `between` или `range`.
- [ ] Чтобы у обеих групп было одинаковое число корзин
  > Число корзин задаёт `bins` (а общую сетку — `range`), `density` на это не влияет.
- [ ] Чтобы гистограммы не перекрывали друг друга
  > Перекрытие делает читаемым прозрачность `alpha`, а не `density`.
:::

{{practice: compare, delay}}

## Практика

## task: hist-km | Гистограмма расстояний | warmup

Нарисуйте гистограмму расстояния доставки (`distance_km`) с 30 корзинами и заголовком «Расстояние, км».

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
assert len(ax.patches) == 30, f'Корзин {len(ax.patches)}, а нужно 30: bins=30.'
assert sum(p.get_height() for p in ax.patches) == len(km), 'Сумма высот должна равняться числу доставок.'
assert ax.get_title() == 'Расстояние, км', f'Заголовок: {ax.get_title()!r}.'
```

### hint
`fig, ax = plt.subplots()` — полотно; гистограмма — метод `ax.hist`.

### hint
`ax.hist(d["distance_km"], bins=30)` и `ax.set_title("Расстояние, км")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(d["distance_km"], bins=30)
ax.set_title("Расстояние, км")
```

## task: p90 | 90 % доставок | warmup

Оставьте доставки с временем от 1 до 299 минут и сохраните в `p90` квантиль 0.9 времени доставки, а в `p50` — медиану.

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
p50 = need('p50')
if close(p50, a.median()) and not close(p50, t.median()):
    raise AssertionError('p50 посчитан по всем данным, вместе с невозможными временами. Медиану считайте по отфильтрованным 1–299 минутам.')
assert close(p50, t.median()), f'p50 = {p50} не совпадает с медианой времени 1–299 минут. Проверьте фильтр between(1, 299) и что берёте median() (или quantile(0.5)).'
got = need('p90')
if close(got, a.quantile(0.9)) and not close(got, t.quantile(0.9)):
    raise AssertionError('p90 посчитан по всем данным. Сначала оставьте время от 1 до 299 минут.')
assert close(got, t.quantile(0.9)), f'p90 = {got} не совпадает с квантилем 0.9 времени 1–299 минут. Проверьте аргумент quantile: 0.9, а не 90.'
```

### hint
`t = d.loc[d["actual_min"].between(1, 299), "actual_min"]`, затем `t.quantile(0.9)`.

### hint
Медиана — `t.median()` или `t.quantile(0.5)`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]
p50 = t.median()
p90 = t.quantile(0.9)
```

## task: p-hist | Гистограмма суммы | warmup

Соберите программу, которая рисует гистограмму суммы заказа доставки.

### parsons
```python
import pandas as pd
import matplotlib.pyplot as plt
d = pd.read_csv("deliveries.csv")
fig, ax = plt.subplots(figsize=(8, 3))
ax.hist(d["amount"], bins=25)
ax.set_title("Сумма заказа, ₽")
```

### check
```python
ax = ax_of()
assert len(ax.patches) == 25, f'Столбцов {len(ax.patches)}, а нужно 25: гистограмма рисуется строкой ax.hist(...) после plt.subplots.'
assert ax.get_title() == 'Сумма заказа, ₽', f'Заголовок {ax.get_title()!r}: строка с set_title должна идти после plt.subplots.'
```

### hint
Полотно создаётся до рисования, заголовок — после.

### hint
Порядок: импорты → чтение `deliveries.csv` → `fig, ax = plt.subplots()` → `ax.hist(d["amount"], bins=...)` → `ax.set_title(...)`.

## task: five-min | Корзины по 5 минут | base

Нарисуйте гистограмму времени доставки (только от 1 до 299 минут) в диапазоне от 0 до 120 минут с корзинами по 5 минут. Подпишите ось X: «минут».

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
a = _pd.read_csv('deliveries.csv')['actual_min']
t = a[a.between(1, 299)]
ax = ax_of()
assert len(ax.patches) == 24, f'Корзин {len(ax.patches)}: от 0 до 120 по 5 минут — это 24 корзины.'
x0 = ax.patches[0].get_x()
w = ax.patches[0].get_width()
assert abs(x0) < 1e-9 and abs(w - 5) < 1e-9, f'Первая корзина начинается с {x0} шириной {w}. Нужно range=(0, 120).'
total = sum(p.get_height() for p in ax.patches)
assert total == t.between(0, 120).sum(), f'В корзинах {total} доставок — проверьте фильтр 1–299.'
assert ax.get_xlabel() == 'минут'
```

### hint
Сначала отфильтруйте время: `t = d.loc[d["actual_min"].between(1, 299), "actual_min"]`.

### hint
`ax.hist(t, bins=24, range=(0, 120))` — 120 / 24 = 5 минут на корзину. Подпись — `ax.set_xlabel("минут")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(t, bins=24, range=(0, 120))
ax.set_xlabel("минут")
ax.set_title("Время доставки")
```

### explain
Пик — около 30–35 минут (одна корзина 30–35 вмещает почти 400 доставок), справа — длинный хвост до 90+. Корзины по 5 минут удобны тем, что совпадают с тем, как говорит бизнес: «за полчаса», «за 45 минут». Ширину корзин выбирают по смыслу, а не по умолчанию.

## task: skew | Среднее против медианы | base

Сохраните в `mean_km` и `median_km` среднее и медиану расстояния (округлите до 2 знаков), а в `right_tail` — `True`, если среднее больше медианы (признак хвоста вправо).

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
km = _pd.read_csv('deliveries.csv')['distance_km']
assert close(need('mean_km'), round(km.mean(), 2)), f'mean_km = {need("mean_km")}.'
assert close(need('median_km'), round(km.median(), 2)), f'median_km = {need("median_km")}.'
assert need('right_tail') == bool(km.mean() > km.median()), 'right_tail — результат сравнения среднего и медианы.'
```

### hint
`mean_km = round(d["distance_km"].mean(), 2)`, так же медиана.

### hint
`right_tail = mean_km > median_km`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
mean_km = round(d["distance_km"].mean(), 2)
median_km = round(d["distance_km"].median(), 2)
right_tail = mean_km > median_km
```

### explain
Среднее расстояние — 2.96 км, медиана — 2.5. Среднее больше: несколько дальних заказов тянут его вверх, а медиана на них не реагирует. Для отчёта «типичная доставка — 2.5 км» честнее, чем «в среднем 3 км».

## task: items | Позиции в заказе | base

Нарисуйте столбцы: сколько заказов с 1, 2, …, 6 позициями (по порядку числа позиций). В `share_1_2` сохраните долю заказов с одной или двумя позициями в процентах (1 знак).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
it = _pd.read_csv('deliveries.csv')['items']
vc = it.value_counts().sort_index()
ax = ax_of()
assert [p.get_height() for p in ax.patches] == [float(v) for v in vc.values], 'Высоты — число заказов для 1, 2, …, 6 позиций по порядку. Нужны столбцы (bar), а не hist.'
assert close(need('share_1_2'), round(it.isin([1, 2]).mean() * 100, 1)), f'share_1_2 = {need("share_1_2")}.'
```

### hint
`d["items"].value_counts().sort_index()` и `ax.bar(...)`.

### hint
Доля: `d["items"].isin([1, 2]).mean() * 100`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
counts = d["items"].value_counts().sort_index()
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(counts.index, counts.values)
ax.set_title("Позиций в заказе")
share_1_2 = round(d["items"].isin([1, 2]).mean() * 100, 1)
```

### explain
Одна или две позиции — 60 % заказов, дальше число заказов плавно падает: шесть позиций — лишь 94 случая. Столбцы по порядку числа позиций (а не по убыванию) сохраняют смысл шкалы: глаз видит «чем больше позиций, тем реже».

## task: vline | Линия медианы | base

Нарисуйте гистограмму времени доставки (от 1 до 299 минут, 40 корзин) и отметьте медиану вертикальной пунктирной линией (`linestyle="--"`).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]

```

### check
```python
import pandas as _pd
a = _pd.read_csv('deliveries.csv')['actual_min']
med = a[a.between(1, 299)].median()
ax = ax_of()
assert len(ax.patches) == 40, f'Корзин {len(ax.patches)}, нужно 40.'
v = [l for l in ax.lines if len(set(l.get_xdata())) == 1]
assert v, 'Нет вертикальной линии: ax.axvline(...).'
assert close(float(v[0].get_xdata()[0]), med), f'Линия стоит на {v[0].get_xdata()[0]}, а должна — на медиане времени 1–299 минут: t.median() по отфильтрованным данным.'
assert v[0].get_linestyle() == '--', 'Линия должна быть пунктирной: linestyle="--".'
```

### hint
Сначала гистограмма: `ax.hist(t, bins=40)`, где `t` — время 1–299 минут.

### hint
`ax.axvline(t.median(), linestyle="--", color="red")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(t, bins=40)
ax.axvline(t.median(), linestyle="--", color="red")
ax.set_title("Время доставки и медиана")
```

### explain
Медиана — 33 минуты. Пунктир делит площадь гистограммы пополам, и видно, что правее него хвост длиннее, чем слева: половина доставок укладывается в 33 минуты, но «вторая половина» растянута до 90+.

## task: minute-flat | Ровные минуты | base

Минута, в которую создан заказ, ожидаемо распределена равномерно. Проверьте: нарисуйте гистограмму минут `created.dt.minute` с корзинами по 5 минут от 0 до 60. Сохраните `expected` — сколько заказов приходилось бы на корзину при идеально ровном распределении (1 знак), и `max_dev_pct` — наибольшее отклонение корзины от `expected` **по модулю** (`abs`: корзина и выше, и ниже ожидания считается отклонением) в процентах от `expected` (1 знак).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])

```

### check
```python
import pandas as _pd
import numpy as _np
m = _pd.read_csv('deliveries.csv', parse_dates=['created'])['created'].dt.minute
c, _ = _np.histogram(m, bins=12, range=(0, 60))
e = len(m) / 12
ax = ax_of()
assert len(ax.patches) == 12, f'Корзин {len(ax.patches)}: от 0 до 60 по 5 минут — 12 корзин, range=(0, 60).'
assert [int(p.get_height()) for p in ax.patches] == [int(x) for x in c], 'Высоты не совпадают с числом заказов по минутам: ax.hist(d["created"].dt.minute, bins=12, range=(0, 60)).'
assert close(need('expected'), round(e, 1), 0.051), f'expected = {need("expected")}: все заказы, делённые на число корзин.'
want = round(max(abs(c - e)) / e * 100, 1)
assert close(need('max_dev_pct'), want, 0.051), f'max_dev_pct = {need("max_dev_pct")} не совпадает. Нужно наибольшее |корзина − expected| / expected × 100: модуль отклонения (abs), максимум по 12 корзинам, деление на неокруглённое expected.'
```

### hint
Минута — `d["created"].dt.minute`. `ax.hist` возвращает высоты: `counts, edges, bars = ax.hist(...)`.

### hint
`expected = round(len(d) / 12, 1)`; отклонение — `abs(counts - len(d) / 12).max() / (len(d) / 12) * 100`.

### hint
Почти готово: `counts, edges, bars = ax.hist(minute, bins=12, range=(0, 60))`, затем `e = len(minute) / 12`, `max_dev_pct = round(abs(counts - e).max() / e * 100, 1)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
minute = d["created"].dt.minute
fig, ax = plt.subplots(figsize=(8, 3))
counts, edges, bars = ax.hist(minute, bins=12, range=(0, 60))
e = len(minute) / 12
ax.axhline(e, color="red", linestyle="--")
ax.set_xlabel("минута часа")
ax.set_title("Минута создания заказа: ровно, как и ожидали")
expected = round(e, 1)
max_dev_pct = round(abs(counts - e).max() / e * 100, 1)
```

### explain
На корзину приходится в среднем 156.4 заказа, а самая «неровная» корзина отклоняется на 12.5 %. Много это или мало? По ориентиру из раздела «Какую форму ожидать» случайный разброс — около $\sqrt{156} \approx 12$ штук, то есть 8 %. Отклонение в полтора таких шага — обычная случайность, никакого пика на минуте 0 нет: время записывает система, а не человек. Если бы корзина 0–5 оказалась вдвое выше остальных, это был бы признак ручного ввода с округлением.

## task: poisson-day | Доставки за день и Пуассон | plus

Для кофейни KZN-1 посчитайте `per_day` — число доставок за **каждый** день с 1 сентября по 30 ноября (дни без доставок — с нулём). Сохраните `lam` — среднее число доставок в день (2 знака) и таблицу `table` с индексом «доставок за день» (0, 1, 2, … — только встречавшиеся значения) и столбцами `obs` (доля дней на деле) и `exp` (доля по формуле Пуассона с этим `lam`). В `worst_k` — число доставок, где `obs` и `exp` расходятся сильнее всего.

### starter
```python
import math
import pandas as pd

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
days = pd.date_range("2026-09-01", "2026-11-30")

```

### check
```python
import math as _m
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
k = d[d['shop_id'] == 'KZN-1']
days = _pd.date_range('2026-09-01', '2026-11-30')
pdw = k.groupby(k['created'].dt.normalize()).size().reindex(days, fill_value=0)
lw = pdw.mean()
s = need('per_day', _pd.Series)
if len(s) < len(days):
    raise AssertionError(f'В per_day {len(s)} дней, а в периоде {len(days)}: добавьте пустые дни через reindex(days, fill_value=0).')
assert [int(x) for x in s.values] == [int(x) for x in pdw.values], 'per_day не совпадает: доставки KZN-1 по дням (dt.normalize()) с нулями в пустых днях.'
assert close(need('lam'), round(lw, 2), 0.006), f'lam = {need("lam")}: среднее per_day с нулями в пустых днях, округлённое до 2 знаков.'
obs = pdw.value_counts(normalize=True).sort_index()
exp = _pd.Series({j: lw ** j * _m.exp(-lw) / _m.factorial(j) for j in obs.index})
t = need('table', _pd.DataFrame)
assert list(t.columns[:2]) == ['obs', 'exp'] or set(['obs', 'exp']) <= set(t.columns), f'Столбцы table: {list(t.columns)} — нужны obs и exp.'
assert [int(i) for i in t.index] == [int(i) for i in obs.index], f'Индекс table: {list(t.index)} — встречавшиеся значения по возрастанию.'
assert all(close(a, b, 0.001) for a, b in zip(t['obs'], obs)), 'obs — доли дней: value_counts(normalize=True).sort_index().'
assert all(close(a, b, 0.001) for a, b in zip(t['exp'], exp)), 'exp — λ^k · e^(−λ) / k! для каждого k из индекса.'
assert int(need('worst_k')) == int((obs - exp).abs().idxmax()), f'worst_k = {need("worst_k")}.'
```

### hint
Доставки по дням — `k.groupby(k["created"].dt.normalize()).size()`, где `k` — строки KZN-1. Пустые дни — `.reindex(days, fill_value=0)`.

### hint
`obs = per_day.value_counts(normalize=True).sort_index()`; формула для каждого `j` из `obs.index`: `lam ** j * math.exp(-lam) / math.factorial(j)`.

### hint
`table = pd.DataFrame({"obs": obs, "exp": exp})`; `worst_k = (table["obs"] - table["exp"]).abs().idxmax()`. Для формулы берите точное среднее, а округляйте только `lam` для ответа.

### solution
```python
import math
import pandas as pd

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
days = pd.date_range("2026-09-01", "2026-11-30")
k = d[d["shop_id"] == "KZN-1"]
per_day = k.groupby(k["created"].dt.normalize()).size().reindex(days, fill_value=0)
mean = per_day.mean()
lam = round(mean, 2)
obs = per_day.value_counts(normalize=True).sort_index()
exp = pd.Series({j: mean ** j * math.exp(-mean) / math.factorial(j) for j in obs.index})
table = pd.DataFrame({"obs": obs, "exp": exp})
worst_k = (table["obs"] - table["exp"]).abs().idxmax()
table.round(3)
```

### explain
У KZN-1 4.71 доставки в день; сильнее всего формула расходится с данными на семи доставках: 14.3 % дней против ожидаемых 9.2 %. Это 13 дней вместо 8 — для 91 дня в пределах случайности. Пустой день за осень был всего один, и формула тоже ждёт около одного (0.9 %). Если бы забыли `reindex`, этот день пропал бы, среднее стало бы 4.77, а нулей не оказалось бы вовсе — расхождение с Пуассоном появилось бы из-за ошибки подсчёта, а не из-за данных.

## task: compare | Вело против авто | plus

Сравните распределения времени доставки у вело- и авто-курьеров (только время 1–299 минут): две гистограммы на одной оси, по 30 корзин в диапазоне 0–90 минут, `density=True`, `alpha=0.5`, с легендой («вело», «авто»). Сохраните в `medians` словарь «тип курьера → медиана времени» для этих двух типов.

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
assert len(ax.patches) == 60, f'Столбцов {len(ax.patches)}, а нужно 60: две гистограммы по 30 корзин.'
labels = [t.get_text() for t in ax.get_legend().get_texts()] if ax.get_legend() else []
assert sorted(labels) == ['авто', 'вело'], f'Легенда: {labels}. Передайте label=... в hist и вызовите ax.legend().'
area = sum(p.get_height() * p.get_width() for p in ax.patches[:30])
assert area < 1.01, 'Высоты — доли (density=True), а не количества.'
want = {c: ok.loc[ok['courier'] == c, 'actual_min'].median() for c in ('вело', 'авто')}
got = dict(need('medians'))
assert set(got) == set(want), f'Ключи medians: {sorted(got)} — нужны ровно "вело" и "авто".'
assert all(close(got[k], want[k]) for k in want), f'medians = {got}: медианы не совпадают. Считайте по ok (время 1–299 минут), отдельно для каждого типа курьера: ok.loc[ok["courier"] == c, "actual_min"].median().'
```

### hint
Как в примере раздела «Сравнить два распределения»: цикл по двум типам курьера, в каждом шаге — своя гистограмма на той же оси `ax` с подписью `label`, в конце `ax.legend()`.

### hint
Внутри цикла: `t = ok.loc[ok["courier"] == c, "actual_min"]` и `ax.hist(t, bins=30, range=(0, 90), density=True, alpha=0.5, label=c)`. Медиану той же `t` можно сразу положить в словарь.

### hint
```python static
medians = {}
fig, ax = plt.subplots(figsize=(8, 3.5))
for c in ["вело", "авто"]:
    t = ...
    ax.hist(t, bins=30, range=(0, 90), density=True, alpha=0.5, label=c)
    medians[c] = ...
ax.legend()
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
medians = {}
fig, ax = plt.subplots(figsize=(8, 3.5))
for c in ["вело", "авто"]:
    t = ok.loc[ok["courier"] == c, "actual_min"]
    ax.hist(t, bins=30, range=(0, 90), density=True, alpha=0.5, label=c)
    medians[c] = t.median()
ax.legend()
ax.set_title("Время доставки: вело и авто")
```

### explain
Медианы почти равны — 32 минуты у вело и 31 у авто, а формы различаются: у авто хвост вправо длиннее (дальние заказы), у вело пик выше. `density=True` делает площадь каждой гистограммы равной 1 — без него группа с большим числом доставок выглядела бы «выше» просто из-за объёма.

## task: delay | Опоздание | star

Посчитайте опоздание `delay = actual_min − promised_min` (только доставки с временем 1–299 минут). Нарисуйте гистограмму опоздания с корзинами по 5 минут в диапазоне от −40 до 40 и отметьте ноль вертикальной линией. Сохраните в `late_pct` долю доставок, привезённых позже обещанного (`delay > 0`), в процентах с одним знаком.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
dl = ok['actual_min'] - ok['promised_min']
ax = ax_of()
assert len(ax.patches) == 16 and abs(ax.patches[0].get_x() + 40) < 1e-9, 'Нужно 16 корзин по 5 минут от −40 до 40: bins=16, range=(-40, 40).'
assert any(len(set(l.get_xdata())) == 1 and float(l.get_xdata()[0]) == 0 for l in ax.lines), 'Отметьте ноль: ax.axvline(0).'
lp = need('late_pct')
all_dl = d['actual_min'] - d['promised_min']
if close(lp, round((all_dl > 0).mean() * 100, 1)) and not close(lp, round((dl > 0).mean() * 100, 1)):
    raise AssertionError(f'late_pct = {lp} посчитан без фильтра: сначала оставьте доставки с временем 1–299 минут.')
assert close(lp, round((dl > 0).mean() * 100, 1)), f'late_pct = {lp}. Нужна доля delay > 0 (строго позже обещанного) среди доставок 1–299 минут, в процентах (× 100) с 1 знаком.'
```

### hint
Три шага: отфильтровать время 1–299, вычесть обещанное из фактического, нарисовать гистограмму с `range` и отметкой нуля (`ax.axvline`, как линия медианы в разделе «Форма распределения»).

### hint
`delay = ok["actual_min"] - ok["promised_min"]`. От −40 до 40 — 80 минут, по 5 минут — 16 корзин. Доля опозданий — среднее от условия `delay > 0`: `True` считается как 1, `False` — как 0.

### hint
```python static
ok = d[d["actual_min"].between(1, 299)]
delay = ...
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(delay, bins=16, range=(-40, 40))
ax.axvline(0, color="red")
late_pct = round(... * 100, 1)
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
delay = ok["actual_min"] - ok["promised_min"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(delay, bins=16, range=(-40, 40))
ax.axvline(0, color="red")
ax.set_title("Опоздание, мин (справа от нуля — опоздали)")
late_pct = round((delay > 0).mean() * 100, 1)
```

### explain
Гистограмма опоздания отвечает сразу на два вопроса: как часто опаздываем (площадь справа от нуля) и насколько сильно (как далеко тянется хвост). Почти каждая четвёртая доставка опаздывает — с этой цифры начнётся проект главы.
