---
title: "Какую форму ожидать: Пуассон и ровные минуты"
lead: "Прежде чем рисовать гистограмму, опытный аналитик спрашивает: какая форма тут должна получиться? Учимся предсказывать форму по тому, как рождаются значения, считаем распределение Пуассона для доставок за день и проверяем «ровность» правилом √n."
files: [deliveries.csv]
recap:
  - "Форму ждут заранее по тому, как рождаются значения: длительности и деньги — хвост вправо, счётчики событий за день — Пуассон, суммы многих вкладов — колокол, минута часа — ровно. Несовпадение — повод искать ошибку или историю."
  - "Пуассон: доля интервалов с k событиями — `lam ** k * math.exp(-lam) / math.factorial(k)`, где `lam` — среднее. Счётчик по дням достраивайте пустыми днями: `reindex(days, fill_value=0)`."
  - "Ориентир для «ровно или нет»: если в корзину в среднем попадает n значений, случайный разброс — около √n штук. Отклонение в 1–2 таких шага — случайность, в 3 и больше — повод присмотреться."
---

Данные те же, что в уроке «Распределения и гистограммы»: `deliveries.csv` — доставки сети за осень. Гистограммы рисовать уже умеем; теперь учимся заранее знать, какой они должны получиться.

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
Врач, прежде чем смотреть анализ, знает, какой у здорового человека должна быть температура. 36.6 — норма, 42 — либо болезнь, либо сломанный градусник. С данными так же: ожидание формы — это «норма», а отклонение от неё — повод для вопроса. Только «нормы» для данных никто не утверждал — ожидание вы выводите сами из того, как данные появляются, и иногда ошибаетесь в нём.
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

{{practice: poisson-hand}}

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

{{practice: poisson-day, ufa-empty}}

Равномерную форму проверить ещё проще: минута, в которую создан заказ, ни от чего не зависит, поэтому по корзинам в 5 минут заказы должны лечь ровно. Пик на минуте 0 значил бы, что время кто-то вводил вручную и округлял.

«Ровно» не значит «одинаково до штуки»: даже у честного счётчика корзины случайно отличаются. Ориентир для оценки на глаз: если в корзину в среднем попадает $n$ значений, обычный случайный разброс — около $\sqrt{n}$ штук. Пока примите это правило как ориентир; откуда оно — в главе 5 (урок «Распределения: мат. ожидание, биномиальное, Пуассона»: у счётчика случайных событий дисперсия равна среднему, а разброс — корню из него). При 100 значениях на корзину это ±10, то есть ±10 %, при 400 — ±20, то есть ±5 %. Отклонение в 1–2 таких шага — случайность, в 3 и больше — повод присмотреться.

::: warn Типичные ошибки
- **Ждать колокол от всего подряд.** Время, деньги и счётчики почти никогда не бывают симметричными; колокол получается у сумм и средних многих мелких вкладов.
- **Счётчик без пустых интервалов.** `groupby` по дням не создаёт дней без событий: среднее завышено, доля нулей потеряна. Достраивайте полный календарь через `reindex(..., fill_value=0)`.
- **Подгонять ожидание под картинку.** Сначала запишите, какую форму ждёте и почему, потом рисуйте. Иначе любая форма «объяснится» задним числом.
- **Искать точное совпадение с формулой.** На 91 дне доли будут отличаться на несколько пунктов просто из-за случайности; смотрите на общую форму.
:::

{{practice: minute-flat, weekday-sqrt}}

## Практика

## task: poisson-hand | Пуассон цепочкой | warmup

Кофейня в среднем делает $\lambda = 3$ доставки в день. Посчитайте, как в игрушечном примере, цепочкой: `p0` = $e^{-\lambda}$ (`math.exp`), каждая следующая доля — предыдущая, умноженная на $\lambda / k$. Сохраните `p0`, `p1`, `p2` и `p3plus` — долю дней с тремя доставками и больше (1 минус первые три доли). Все — с 3 знаками.

### starter
```python
import math
lam = 3

```

### check
```python
import math as _m
q0 = _m.exp(-3); q1 = q0 * 3; q2 = q1 * 3 / 2
assert close(need('p0'), round(q0, 3), 0.0006), f'p0 = {need("p0")}: math.exp(-lam).'
if close(need('p1'), round(q0 * 3 / 2, 3), 0.0006):
    raise AssertionError('p1: умножайте p0 на lam / k с k = 1, то есть на 3.')
assert close(need('p1'), round(q1, 3), 0.0006), f'p1 = {need("p1")}: p0 · lam / 1.'
assert close(need('p2'), round(q2, 3), 0.0006), f'p2 = {need("p2")}: p1 · lam / 2.'
assert close(need('p3plus'), round(1 - q0 - q1 - q2, 3), 0.0011), f'p3plus = {need("p3plus")}: 1 − (p0 + p1 + p2).'
```

### hint
`p0 = math.exp(-lam)`; дальше `p1 = p0 * lam / 1`, `p2 = p1 * lam / 2`.

### hint
`p3plus = 1 - (p0 + p1 + p2)`; округляйте в конце: `round(p0, 3)` и т. д.

### solution
```python
import math
lam = 3
p0 = math.exp(-lam)
p1 = p0 * lam / 1
p2 = p1 * lam / 2
p3plus = 1 - (p0 + p1 + p2)
p0, p1, p2, p3plus = (round(x, 3) for x in (p0, p1, p2, p3plus))
print(p0, p1, p2, p3plus)
```

### explain
При среднем 3 доставки пустой день бывает в 5 % дней, одна доставка — в 14.9 %, две — в 22.4 %, а в 57.7 % дней доставок три и больше. Больше половины дней — «не ниже среднего», хотя и пустые дни случаются примерно раз в три недели.

## task: ufa-empty | Пустые дни в Уфе | base

У кофейни UFA-1 доставок меньше, чем у остальных, и пустые дни случаются чаще. Посчитайте `per_day` — доставки UFA-1 за каждый день с 1 сентября по 30 ноября (пустые дни — нулём). Сохраните `lam` — среднее число доставок в день (2 знака), `empty` — сколько дней без доставок было на деле, и `exp_empty` — сколько пустых дней из 91 ждёт формула Пуассона: $91 \cdot e^{-\lambda}$ (1 знак; в формулу — неокруглённое среднее).

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
u = d[d['shop_id'] == 'UFA-1']
days = _pd.date_range('2026-09-01', '2026-11-30')
raw = u.groupby(u['created'].dt.normalize()).size()
pdw = raw.reindex(days, fill_value=0)
lw = pdw.mean()
if close(need('lam'), round(raw.mean(), 2), 0.006):
    raise AssertionError(f'lam = {need("lam")} — это среднее только по дням с доставками ({len(raw)} дней). Добавьте пустые дни: reindex(days, fill_value=0).')
s = need('per_day', _pd.Series)
assert len(s) == len(days) and [int(x) for x in s.values] == [int(x) for x in pdw.values], 'per_day — доставки UFA-1 по дням (dt.normalize()) с нулями в пустых днях, 91 значение.'
assert close(need('lam'), round(lw, 2), 0.006), f'lam = {need("lam")}: среднее per_day, 2 знака.'
assert int(need('empty')) == int((pdw == 0).sum()), f'empty = {need("empty")}: (per_day == 0).sum().'
assert close(need('exp_empty'), round(91 * _m.exp(-lw), 1), 0.051), f'exp_empty = {need("exp_empty")}: 91 · e^(−λ) с неокруглённым средним.'
```

### hint
Как в разделе «На реальных данных»: строки UFA-1, `groupby(...dt.normalize()).size()`, затем `.reindex(days, fill_value=0)`.

### hint
`mean = per_day.mean()`, `empty = (per_day == 0).sum()`, `exp_empty = round(len(days) * math.exp(-mean), 1)`.

### solution
```python
import math
import pandas as pd

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
days = pd.date_range("2026-09-01", "2026-11-30")
u = d[d["shop_id"] == "UFA-1"]
per_day = u.groupby(u["created"].dt.normalize()).size().reindex(days, fill_value=0)
mean = per_day.mean()
lam = round(mean, 2)
empty = int((per_day == 0).sum())
exp_empty = round(len(days) * math.exp(-mean), 1)
print(lam, empty, exp_empty)
```

### explain
У UFA-1 в среднем 2.02 доставки в день. Пустых дней было 14, формула ждёт 12.0 — близко, разница в пределах случайности ($\sqrt{12} ≈ 3.5$). Значит, пустые дни — не сбой выгрузки и не закрытая кофейня, а обычное следствие малого потока. Без `reindex` эти 14 дней пропали бы: среднее стало бы 2.39, а вопрос «сколько пустых дней» вообще не имел бы ответа.

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

Для кофейни KZN-1 посчитайте `per_day` — число доставок за **каждый** день с 1 сентября по 30 ноября (дни без доставок — с нулём). Сохраните `lam` — среднее число доставок в день (2 знака) и таблицу `table` с индексом «доставок за день» (0, 1, 2, … — только встречавшиеся значения) и столбцами `obs` (доля дней на деле) и `exp` (доля по формуле Пуассона; в формулу подставляйте неокруглённое среднее, округляйте только ответ `lam`). В `worst_k` — число доставок, где `obs` и `exp` расходятся сильнее всего.

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

## task: weekday-sqrt | Ровно ли по дням недели | plus

За осень (91 день) каждый день недели встретился ровно 13 раз. Если бы день недели на доставку не влиял, заказы легли бы по дням недели ровно. Проверьте правилом $\sqrt{n}$: посчитайте `counts` — число доставок по `created.dt.dayofweek` (0 — понедельник, 6 — воскресенье; `dt.dayofweek` — то же, что `dt.weekday` из главы 2), `expected` — сколько пришлось бы на день при ровном распределении (1 знак), и `steps` — отклонение каждого дня в «шагах»: `(counts − expected) / √expected`, 1 знак, в `expected` — неокруглённое значение. В `loud` сохраните список дней (номеров), где отклонение по модулю 2 шага и больше.

### starter
```python
import math
import pandas as pd

d = pd.read_csv("deliveries.csv", parse_dates=["created"])

```

### check
```python
import math as _m
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
c = d['created'].dt.dayofweek.value_counts().sort_index()
e = len(d) / 7
st = ((c - e) / _m.sqrt(e)).round(1)
cc = need('counts', _pd.Series)
assert [int(i) for i in cc.sort_index().index] == list(range(7)) and [int(x) for x in cc.sort_index().values] == [int(x) for x in c.values], 'counts — d["created"].dt.dayofweek.value_counts().sort_index().'
assert close(need('expected'), round(e, 1), 0.051), f'expected = {need("expected")}: все доставки / 7.'
s = need('steps', _pd.Series).sort_index()
assert len(s) == 7 and all(close(a, b, 0.051) for a, b in zip(s.values, st.values)), f'steps = {[float(x) for x in s.values]}, а нужно {[float(x) for x in st.values]}: (counts − expected) / √expected.'
want = sorted(int(i) for i in st.index[st.abs() >= 2])
assert sorted(int(x) for x in need('loud')) == want, f'loud = {need("loud")}, а нужно {want}: дни, где |steps| ≥ 2.'
```

### hint
`counts = d["created"].dt.dayofweek.value_counts().sort_index()`, `e = len(d) / 7`.

### hint
`steps = ((counts - e) / math.sqrt(e)).round(1)`; дни с большим отклонением — `list(steps.index[steps.abs() >= 2])`.

### solution
```python
import math
import pandas as pd

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
counts = d["created"].dt.dayofweek.value_counts().sort_index()
e = len(d) / 7
expected = round(e, 1)
steps = ((counts - e) / math.sqrt(e)).round(1)
loud = list(steps.index[steps.abs() >= 2])
print(counts.tolist(), expected, steps.tolist(), loud)
```

### explain
На день недели в среднем 268.1 доставки, шаг случайного разброса — $\sqrt{268} ≈ 16$. Будни отклоняются на 0.4–1.8 шага вниз, а суббота (+2.4) и воскресенье (+3.0) — вверх: 308 и 318 доставок. Число самих дней одинаковое (по 13), значит, перекос не от календаря. Это не ошибка данных, а история: в выходные гости чаще заказывают доставку домой. Ровной формы здесь ждать было нельзя — день недели, в отличие от минуты часа, на поведение гостей влияет.
