---
title: "Метрики: чьё среднее и воронка"
lead: "Любое исследование начинается с метрики — и уже здесь можно поссориться на совещании. Средний чек на заказ, на гостя и на кофейню — три разных числа, и все верные. Разбираемся, какое из них отвечает на ваш вопрос, и строим воронку: на каком шаге приложение теряет гостей."
files: [preorders.csv, app_funnel.csv]
recap:
  - "Чьё среднее: `o[\"amount\"].mean()` — на заказ (частые гости весят больше), `groupby(\"guest_id\")[\"amount\"].mean().mean()` — на гостя, по кофейням — на кофейню. Пишите в отчёте, чьё это среднее."
  - "Воронка: разные сессии на шаге `groupby(\"step\")[\"session_id\"].nunique().reindex(steps)`, доля от начала и конверсия шага (`shift()`). Причину обрыва ищут срезом воронки — по платформе, периоду."
---

## Чьё среднее: заказа, гостя или кофейни

Любое исследование начинается с метрики. Кажется, что «средний чек» — одно число. Но на предзаказах в приложении (`preorders.csv`: один предзаказ на строку — `order_id`, `guest_id`, `date`, `shop_id`, `amount`) его можно посчитать тремя способами — и получить три разных ответа. На совещании это выглядит как спор, у кого правильные данные, хотя все считают верно — просто **разные** средние.

::: tip Аналогия
Спросите университет: «Какой у вас средний размер группы?» — он поделит студентов на число групп: например, 30. Спросите студентов: «Сколько человек в твоей группе?» — и усредните ответы: выйдет больше, потому что в больших группах больше студентов и они чаще отвечают. Обе цифры честные: одна — глазами университета, другая — глазами студента. С чеками, в отличие от университета, третий взгляд — кофейни — добавляет ещё одно число, а не просто выбирает одно из двух.
:::

### Игрушечный пример руками

Два гостя: Аня сделала 4 предзаказа по 200 ₽, Борис — 1 предзаказ на 600 ₽.

1. **Среднее на заказ** — вся выручка на все заказы: (4 × 200 + 600) / 5 = 1 400 / 5 = **280 ₽**. Аня дала 4 заказа из 5 и «перетянула» среднее к своим 200.
2. **Среднее на гостя** — сначала средний чек каждого гостя (Аня 200, Борис 600), потом среднее из них: (200 + 600) / 2 = **400 ₽**. Каждый гость весит одинаково, сколько бы ни заказывал.
3. Разница в 120 ₽ — не ошибка, а **вес**: частая гостья с маленьким чеком весит в первом способе вчетверо больше.

::: figure whose-mean
Пять заказов двух гостей: в среднем «на заказ» у Ани четыре голоса из пяти, в среднем «на гостя» после `groupby` — один из двух.
:::

::: predict
```python static
import pandas as pd
t = pd.DataFrame({"guest": ["Аня"] * 4 + ["Борис"], "amount": [200, 200, 200, 200, 600]})
print(t["amount"].mean(), t.groupby("guest")["amount"].mean().mean())
```

- `280.0 280.0`
- `400.0 400.0`
- [x] `280.0 400.0`

Почему: первое — среднее по строкам-заказам, второе — среднее из средних по гостям. Сначала `groupby` сжимает Аню в одну строку, и её четыре заказа превращаются в один голос.
:::

На реальных данных:

```python
import pandas as pd
o = pd.read_csv("preorders.csv")

per_order = o["amount"].mean()                                  # глазами кассы
per_guest = o.groupby("guest_id")["amount"].mean().mean()       # глазами гостя
per_shop = o.groupby("shop_id")["amount"].mean().mean()         # глазами сети
print(round(per_order, 1), round(per_guest, 1), round(per_shop, 1))

g = o.groupby("guest_id").agg(orders=("amount", "size"), check=("amount", "mean"))
g["частота"] = pd.cut(g["orders"], [0, 1, 5, 20, 1000], labels=["1", "2–5", "6–20", "21+"])
g.groupby("частота", observed=True).agg(guests=("orders", "size"), orders=("orders", "sum"), check=("check", "mean")).round(0)
```

Что здесь происходит:

- `o["amount"].mean()` — среднее по всем 17 598 строкам: каждый заказ — один голос;
- `groupby("guest_id")["amount"].mean()` — Series из 2 210 чисел, средний чек каждого гостя; `.mean()` от неё — каждый гость один голос;
- то же по `shop_id` — пять чисел, каждая кофейня один голос;
- `pd.cut` режет число заказов гостя на группы частоты, чтобы увидеть, кто тянет среднее.

Как читать: на заказ — **370.9 ₽**, на кофейню — **380.5 ₽**, на гостя — **392.7 ₽**. Почему «на заказ» меньше всех: 230 самых частых гостей (21+ заказ) сделали 8 257 заказов из 17 598 — почти половину, а их средний чек — 353 ₽: каждый день берут что-то простое. «На кофейню» выше, чем «на заказ», потому что маленькая TMN-1 с самым высоким чеком (453.7 ₽ при 1 672 заказах) весит как большие кофейни Перми.

Какое среднее брать — решает вопрос:

| вопрос | среднее |
|---|---|
| сколько выручки даст ещё 1 000 заказов | на заказ |
| какой чек у типичного гостя, сколько предложить в акции | на гостя |
| какой чек у типичной кофейни сети — ориентир для новой точки | на кофейню (`per_shop`): каждая кофейня — один голос, большая и маленькая весят одинаково |
| у какого управляющего кофейня работает лучше | ни одно общее среднее: таблица по каждой кофейне отдельно |

::: sql
`AVG(amount)` — на заказ. На гостя — среднее из средних: `SELECT AVG(avg_check) FROM (SELECT guest_id, AVG(amount) AS avg_check FROM preorders GROUP BY guest_id)`. А `SUM(amount) / COUNT(DISTINCT guest_id)` — третье число: выручка на гостя, а не средний чек.
:::

::: warn Типичные ошибки
- **Среднее из средних без мысли о весах.** `groupby(...).mean().mean()` уравнивает группы: кофейня на 1 672 заказа весит как кофейня на 4 086. Иногда это и нужно, но это надо решить, а не получить случайно.
- **Два отдела — два «средних чека».** Аналитик считает по заказам, маркетолог — по гостям, и они спорят о данных. Пишите в отчёте, чьё это среднее: «средний чек заказа», «средний чек гостя».
- **Выручка на гостя ≠ средний чек гостя.** Первое — сколько денег принёс гость за период (зависит от числа заказов), второе — сколько он тратит за раз.
:::

{{practice: whose-mean, per-guest-rev}}

## Воронка: где теряем гостей

Это тоже выбор метрики — только для процесса из нескольких шагов. (Выбор метрики — первый шаг плана исследования из следующего урока «EDA по плану: от вопроса к выводу».) Одно число «конверсия в заказ» говорит, что заказов мало, но не говорит, где их теряем.

Предзаказ — это путь из шагов: **открыл** приложение → **меню** → **корзина** → **оплата** → **заказ**. Из 100 открывших заказывают примерно 20. Вопрос «как поднять заказы» превращается в вопрос «на каком шаге теряем больше всего и почему». Таблица «сколько дошло до каждого шага» называется **воронкой**.

::: tip Аналогия
В кофейню зашли 100 человек, 80 подошли к витрине, 36 взяли поднос, 26 встали в очередь на кассу, 21 оплатил. Если между очередью и оплатой уходят пятеро, дело, скорее всего, в кассе — а не в витрине. Только в приложении «вернуться на шаг назад» и пройти шаг дважды можно за секунду, поэтому в журнале событий одна сессия оставляет несколько строк.
:::

### Игрушечный пример руками

100 сессий: до меню дошли 80, до корзины — 36, до оплаты — 26, до заказа — 21.

1. **Доля от начала** — шаг / первый шаг: 80 %, 36 %, 26 %, 21 %. Отвечает на вопрос «какая часть всех дошла сюда».
2. **Конверсия шага** — шаг / предыдущий шаг: 80 / 100 = 80 %, 36 / 80 = **45 %**, 26 / 36 = 72 %, 21 / 26 = 81 %. Отвечает на вопрос «где обрыв».
3. Самый большой обрыв — меню → корзина: больше половины посмотрели меню и ушли.

::: figure funnel-steps
Та же воронка: под каждым шагом — доля от начала, стрелками — конверсия от предыдущего шага. Обрыв ищут по стрелкам, а не по долям от начала.
:::

### На реальных данных: журнал событий

`app_funnel.csv` — журнал событий за июнь: одна строка — одно событие (`session_id`, `ts` — время, `platform`, `step`). Главная ловушка: строк больше, чем сессий.

```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]

rows = f["step"].value_counts().reindex(steps)                      # строк-событий
sessions = f.groupby("step")["session_id"].nunique().reindex(steps)  # разных сессий

funnel = pd.DataFrame({"rows": rows, "sessions": sessions})
funnel["from_start"] = (funnel["sessions"] / funnel["sessions"].iloc[0] * 100).round(1)
funnel["from_prev"] = (funnel["sessions"] / funnel["sessions"].shift() * 100).round(1)
funnel
```

Что здесь происходит:

- `value_counts()` считает **строки**: у меню 4 608 строк, но 3 774 сессии — часть гостей открывали меню дважды;
- `groupby("step")["session_id"].nunique()` — разные сессии на шаге; это и есть воронка;
- `reindex(steps)` ставит шаги в порядок пути. Без него `groupby` отсортирует их по алфавиту: «заказ, корзина, меню, оплата, открыл» — и `shift()` поделит не на тот шаг;
- `shift()` сдвигает столбец на строку вниз — делим каждый шаг на предыдущий.

Как читать: из 4 800 сессий заказом закончилась 1 016 — **21.2 %**. Самый большой обрыв — меню → корзина (45.6 %): люди смотрят цены и уходят, это нормально для витрины. Но оплата → заказ — **82.9 %**: из тех, кто уже нажал «оплатить», каждый шестой не дошёл до заказа. На шаге, где деньги почти в кассе, такое бывает редко.

### Срез воронки: платформа и период

Разрежем последний шаг по платформе и по дате выхода обновления Android 15 июня:

```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]
f["period"] = (f["ts"] >= "2026-06-15").map({True: "после 15.06", False: "до 15.06"})   # True/False → подпись периода
pv = f.pivot_table(index=["platform", "period"], columns="step", values="session_id", aggfunc="nunique")[steps]
pv["оплата → заказ, %"] = (pv["заказ"] / pv["оплата"] * 100).round(1)
pv
```

Что получилось: на iOS оплата → заказ — 91–93 % в обоих периодах, на Android до 15 июня — 90.6 %, **после — 60.7 %**. Остальные шаги на Android не изменились.

Сколько это заказов? В строке «android, после 15.06» до оплаты дошли **349** сессий, заказом закончились 212. При прежней конверсии 90.6 % заказов было бы 349 × 0.906 ≈ 316, то есть на 349 × (90.6 % − 60.7 %) ≈ **104** больше.

Вывод для команды приложения: «после обновления Android 15 июня оплату не завершают 39 % дошедших до неё (было 9 %); до конца июня это около 100 потерянных заказов. Нужен баг-репорт на шаг оплаты в Android». Общая воронка показывала только «82.9 % — многовато потерь», а срез нашёл, где именно.

::: warn Типичные ошибки
- **Строки вместо сессий.** `value_counts` по шагам считает события: повторные заходы раздувают шаги. По строкам до меню «дошли» 96.0 % (4 608 из 4 800) вместо 78.6 %, а корзина → оплата — 57.7 % (1 226 из 2 126) вместо 71.2 %: шаг «открыл → меню» выглядит почти без потерь, хотя там уходит каждый пятый, а у корзины появляется обрыв, которого нет.
- **Шаги по алфавиту.** `groupby` сортирует названия; без `reindex(steps)` конверсия шага считается между случайными соседями.
- **Воронка за весь период, когда что-то менялось.** Обновление приложения, акция, сбой — делите на «до» и «после», иначе изменение растворится в среднем.
- **Нестрогая воронка.** Если в журнале бывает «заказ» без «оплаты» (сбой логирования), шаг может оказаться больше предыдущего. Перед расчётом проверьте, что каждый шаг ≤ предыдущего.
:::

{{practice: funnel, funnel-rows, funnel-platform}}

## Практика

## task: whose-mean | Три средних чека | base

По предзаказам `preorders.csv` посчитайте три средних чека (все — 1 знак): `per_order` — среднее по заказам, `per_guest` — среднее из средних чеков гостей, `per_shop` — среднее из средних чеков кофеен. Сохраните в `heavy_share` долю заказов (%, 1 знак), которую сделали гости с 21 и более заказами.

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv")

```

### check
```python
import pandas as _pd
o = _pd.read_csv('preorders.csv')
po = round(o['amount'].mean(), 1)
pg = round(o.groupby('guest_id')['amount'].mean().mean(), 1)
ps = round(o.groupby('shop_id')['amount'].mean().mean(), 1)
got = {k: need(k) for k in ('per_order', 'per_guest', 'per_shop')}
if close(got['per_guest'], round(o['amount'].sum() / o['guest_id'].nunique(), 1), 0.051):
    raise AssertionError('per_guest — это выручка на гостя (сумма / число гостей), а нужен средний чек гостя: groupby("guest_id")["amount"].mean().mean().')
assert close(got['per_order'], po, 0.051), f'per_order = {got["per_order"]}, а нужно {po}.'
assert close(got['per_guest'], pg, 0.051), f'per_guest = {got["per_guest"]}: сначала средний чек каждого гостя, потом среднее из них.'
assert close(got['per_shop'], ps, 0.051), f'per_shop = {got["per_shop"]}: то же по shop_id.'
n = o.groupby('guest_id')['amount'].transform('size')
hs = round((n >= 21).mean() * 100, 1)
assert close(need('heavy_share'), hs, 0.051), f'heavy_share = {need("heavy_share")}, а нужно {hs}: доля заказов (строк), чьи гости сделали 21+ заказ.'
```

### hint
Среднее по заказам — `o["amount"].mean()`. Среднее из средних — сначала `groupby(...)["amount"].mean()`, потом ещё раз `.mean()`.

### hint
Число заказов гостя на каждой строке — `o.groupby("guest_id")["amount"].transform("size")`; доля строк с 21+ — `(n >= 21).mean() * 100`.

### hint
`per_guest = round(o.groupby("guest_id")["amount"].mean().mean(), 1)` — так же для `shop_id`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv")
per_order = round(o["amount"].mean(), 1)
per_guest = round(o.groupby("guest_id")["amount"].mean().mean(), 1)
per_shop = round(o.groupby("shop_id")["amount"].mean().mean(), 1)
n = o.groupby("guest_id")["amount"].transform("size")
heavy_share = round((n >= 21).mean() * 100, 1)
print(per_order, per_guest, per_shop, heavy_share)
```

### explain
370.9 ₽ на заказ, 380.5 ₽ на кофейню, 392.7 ₽ на гостя. Гости с 21+ заказами — это 230 человек из 2 210, но 46.9 % всех заказов, и чек у них ниже среднего. Поэтому «среднее на заказ» — это во многом среднее постоянных гостей. Если маркетолог спрашивает «сколько тратит обычный гость за раз», ответ — 392.7, а не 370.9. Частая ошибка — посчитать «на гостя» как `сумма / число гостей`: это 2 953 ₽ — выручка на гостя за полгода, совсем другой показатель.

## task: per-guest-rev | Третье число: выручка на гостя | warmup

Посчитайте по `preorders.csv` то самое «третье число» из блока SQL: `rev_per_guest` — вся выручка, делённая на число разных гостей (1 знак), и `orders_per_guest` — заказов на гостя в среднем (2 знака). Сохраните также `per_order` — средний чек заказа без округления.

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv")

```

### check
```python
import pandas as _pd
o = _pd.read_csv('preorders.csv')
g = o['guest_id'].nunique()
rv = round(o['amount'].sum() / g, 1)
if close(need('rev_per_guest'), round(o.groupby('guest_id')['amount'].mean().mean(), 1), 0.051):
    raise AssertionError('rev_per_guest — это средний чек гостя. Нужна выручка на гостя: o["amount"].sum() / o["guest_id"].nunique().')
assert close(need('rev_per_guest'), rv, 0.051), f'rev_per_guest = {need("rev_per_guest")}, а нужно {rv}: сумма amount / число разных гостей.'
assert close(need('orders_per_guest'), round(len(o) / g, 2), 0.0051), f'orders_per_guest = {need("orders_per_guest")}: число строк / число разных гостей.'
assert close(need('per_order'), o['amount'].mean(), 1e-6), 'per_order — o["amount"].mean() без округления.'
```

### hint
Число разных гостей — `o["guest_id"].nunique()`; число заказов — `len(o)`.

### hint
`rev_per_guest = round(o["amount"].sum() / o["guest_id"].nunique(), 1)`; так же для заказов на гостя с `len(o)`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv")
guests = o["guest_id"].nunique()
rev_per_guest = round(o["amount"].sum() / guests, 1)
orders_per_guest = round(len(o) / guests, 2)
per_order = o["amount"].mean()
print(rev_per_guest, orders_per_guest, round(per_order * len(o) / guests, 1))
```

### explain
Выручка на гостя за полгода — 2 953.3 ₽, заказов на гостя — 7.96. Последнее число в выводе то же самое, 2 953.3: выручка на гостя = средний чек заказа × заказов на гостя (370.9 × 7.96 ≈ 2 952; рубль разницы — от округления множителей). Поэтому её можно поднять двумя путями — чеком или частотой, — и в отчёте полезно показывать оба множителя. Средний чек гостя (392.7 ₽) в это равенство не входит: он отвечает на другой вопрос.

## task: funnel | Воронка предзаказа | base

По журналу `app_funnel.csv` постройте `funnel` — таблицу с индексом-шагами **в порядке пути** (`steps` уже задан) и столбцами `sessions` (разных сессий на шаге), `from_start` (% от первого шага, 1 знак) и `from_prev` (% от предыдущего шага, 1 знак; у первого шага — `NaN`). Сохраните в `worst` шаг с наименьшей конверсией от предыдущего.

### starter
```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]

```

### check
```python
import pandas as _pd
f = _pd.read_csv('app_funnel.csv')
steps = ['открыл', 'меню', 'корзина', 'оплата', 'заказ']
s = f.groupby('step')['session_id'].nunique().reindex(steps)
fs = (s / s.iloc[0] * 100).round(1)
fp = (s / s.shift() * 100).round(1)
t = need('funnel', _pd.DataFrame)
assert list(t.index) == steps, f'Порядок шагов: {list(t.index)}. Нужен порядок пути — reindex(steps).'
for c in ('sessions', 'from_start', 'from_prev'):
    assert c in t.columns, f'В funnel нет столбца {c}.'
rows = f['step'].value_counts().reindex(steps)
if [int(x) for x in t['sessions']] == [int(x) for x in rows]:
    raise AssertionError('sessions — это число строк-событий. Одна сессия может пройти шаг дважды: считайте nunique по session_id.')
assert [int(x) for x in t['sessions']] == [int(x) for x in s], f'sessions = {list(t["sessions"])}, а нужно {list(s)}.'
assert all(close(a, b, 0.051) for a, b in zip(t['from_start'], fs)), 'from_start — шаг / первый шаг × 100.'
assert _pd.isna(t['from_prev'].iloc[0]) and all(close(a, b, 0.051) for a, b in zip(t['from_prev'].iloc[1:], fp.iloc[1:])), 'from_prev — шаг / предыдущий шаг × 100 (shift()); у первого шага NaN.'
assert need('worst') == fp.iloc[1:].idxmin(), f'worst = {need("worst")!r}.'
```

### hint
Сессии на шаге — `f.groupby("step")["session_id"].nunique()`; порядок пути — `.reindex(steps)`.

### hint
Доля от начала — делите на `.iloc[0]`; от предыдущего — на `.shift()`.

### hint
`funnel = pd.DataFrame({"sessions": s})`, затем `funnel["from_prev"] = (funnel["sessions"] / funnel["sessions"].shift() * 100).round(1)`; худший шаг — `funnel["from_prev"].idxmin()` (NaN пропускается).

### solution
```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]
s = f.groupby("step")["session_id"].nunique().reindex(steps)
funnel = pd.DataFrame({"sessions": s})
funnel["from_start"] = (funnel["sessions"] / funnel["sessions"].iloc[0] * 100).round(1)
funnel["from_prev"] = (funnel["sessions"] / funnel["sessions"].shift() * 100).round(1)
worst = funnel["from_prev"].idxmin()
funnel
```

### explain
Худший шаг — корзина: до неё доходят 45.6 % посмотревших меню. Но «худший» не значит «сломанный»: на витрине многие просто смотрят. Подозрительнее другое — 82.9 % на шаге оплата → заказ, где гость уже решил купить. Срез по платформе в теории показал, что это Android после обновления. Воронка подсказывает, куда смотреть, а причину находит срез. Без `reindex(steps)` шаги встали бы по алфавиту, и `shift()` делил бы «заказ» на ничто, а «корзину» — на «заказ».

## task: funnel-rows | Строки против сессий | base

Посчитайте конверсию от предыдущего шага дважды: по строкам-событиям (`value_counts()`) и по разным сессиям (`nunique()`), оба ряда — в порядке `steps`. Сохраните `gap` — Series «конверсия по строкам − конверсия по сессиям» в процентных пунктах (индекс — шаги, у первого шага `NaN`, 1 знак; округляйте только разность). В `inflated` — шаг, где строки завышают конверсию сильнее всего, в `hidden` — шаг, где строки сильнее всего её занижают.

### starter
```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]

```

### check
```python
import pandas as _pd
f = _pd.read_csv('app_funnel.csv', parse_dates=['ts'])
st = ['открыл', 'меню', 'корзина', 'оплата', 'заказ']
r = f['step'].value_counts().reindex(st)
s = f.groupby('step')['session_id'].nunique().reindex(st)
w = ((r / r.shift() - s / s.shift()) * 100).round(1)
g = need('gap', _pd.Series)
assert list(g.index) == st, f'Индекс gap: {list(g.index)} — шаги в порядке пути (reindex(steps)).'
assert _pd.isna(g.iloc[0]), 'У первого шага предыдущего нет — там должен быть NaN.'
assert all(close(a, b, 0.051) for a, b in zip(g.iloc[1:], w.iloc[1:])), f'gap = {[float(x) for x in g.iloc[1:]]}, а нужно {[float(x) for x in w.iloc[1:]]}: (строки / строки.shift() − сессии / сессии.shift()) × 100.'
assert need('inflated') == w.idxmax(), f'inflated = {need("inflated")!r}: шаг с наибольшим gap.'
assert need('hidden') == w.idxmin(), f'hidden = {need("hidden")!r}: шаг с наименьшим (самым отрицательным) gap.'
```

### hint
Строки — `f["step"].value_counts().reindex(steps)`, сессии — `f.groupby("step")["session_id"].nunique().reindex(steps)`. Конверсия — ряд, делённый на `ряд.shift()`.

### hint
`gap = ((rows / rows.shift() - sessions / sessions.shift()) * 100).round(1)`; шаги — `gap.idxmax()` и `gap.idxmin()`.

### solution
```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]
rows = f["step"].value_counts().reindex(steps)
sessions = f.groupby("step")["session_id"].nunique().reindex(steps)
gap = ((rows / rows.shift() - sessions / sessions.shift()) * 100).round(1)
inflated = gap.idxmax()
hidden = gap.idxmin()
gap
```

### explain
На шаге «меню» строки завышают конверсию на 17.4 п.п. (96.0 % вместо 78.6 %): гости открывают меню по нескольку раз за сессию. На шаге «оплата» — наоборот, занижают на 13.5 п.п. (57.7 % вместо 71.2 %): делим на раздутое число строк корзины, и появляется обрыв, которого нет. На «корзине» и «заказе» разница почти нулевая. Ошибка в одну строку кода переставляет «главную проблему» воронки с одного шага на другой.

## task: funnel-platform | Срез воронки самостоятельно | plus

Повторите срез из раздела «Срез воронки» и доведите его до цифры для команды. Разделите события на периоды «до 15.06» и «после 15.06» (`ts >= "2026-06-15"`), постройте сводную «платформа × период» с числом разных сессий на каждом шаге и сохраните `pay_conv` — Series с конверсией оплата → заказ, % (1 знак), индекс — пары (платформа, период). Сохраните `lost` — сколько заказов Android недополучил после 15 июня по сравнению с прежней конверсией: сессии на оплате после × (конверсия до − конверсия после), целым числом (`round`), конверсии — без округления.

### starter
```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]

```

### check
```python
import pandas as _pd
f = _pd.read_csv('app_funnel.csv', parse_dates=['ts'])
f['p'] = (f['ts'] >= '2026-06-15').map({True: 'после 15.06', False: 'до 15.06'})
pv = f.pivot_table(index=['platform', 'p'], columns='step', values='session_id', aggfunc='nunique')
c = pv['заказ'] / pv['оплата']
pc = need('pay_conv', _pd.Series)
assert len(pc) == 4, f'В pay_conv {len(pc)} значений, а нужно 4: две платформы × два периода.'
got = sorted(round(float(x), 1) for x in pc.values)
want = sorted(round(float(x) * 100, 1) for x in c.values)
if got == sorted(round(float(x), 3) for x in c.values) or all(v < 1.5 for v in got):
    raise AssertionError('pay_conv — в процентах: умножьте долю на 100.')
assert all(close(a, b, 0.051) for a, b in zip(got, want)), f'pay_conv = {got}, а нужно {want}: заказ / оплата × 100 по разным сессиям.'
a_b, a_a = c[('android', 'до 15.06')], c[('android', 'после 15.06')]
lw = round(pv.loc[('android', 'после 15.06'), 'оплата'] * (a_b - a_a))
assert int(need('lost')) == int(lw), f'lost = {need("lost")}, а нужно {int(lw)}: сессии Android на оплате после 15.06 × (конверсия до − конверсия после).'
```

### hint
Период — `(f["ts"] >= "2026-06-15").map({True: "после 15.06", False: "до 15.06"})`: `map` со словарём заменяет `True`/`False` подписями. Сводная — `pivot_table(index=["platform", "period"], columns="step", values="session_id", aggfunc="nunique")`.

### hint
`pay_conv = (pv["заказ"] / pv["оплата"] * 100).round(1)`. Строка Android после 15.06 — `pv.loc[("android", "после 15.06")]`; конверсии для `lost` берите долями без округления.

### solution
```python
import pandas as pd
f = pd.read_csv("app_funnel.csv", parse_dates=["ts"])
steps = ["открыл", "меню", "корзина", "оплата", "заказ"]
f["period"] = (f["ts"] >= "2026-06-15").map({True: "после 15.06", False: "до 15.06"})
pv = f.pivot_table(index=["platform", "period"], columns="step", values="session_id", aggfunc="nunique")[steps]
conv = pv["заказ"] / pv["оплата"]
pay_conv = (conv * 100).round(1)
before, after = conv[("android", "до 15.06")], conv[("android", "после 15.06")]
lost = round(pv.loc[("android", "после 15.06"), "оплата"] * (before - after))
print(pay_conv)
print(lost)
```

### explain
iOS — 91.4 % и 93.1 %, Android до 15 июня — 90.6 %, после — 60.7 %. При прежней конверсии из 349 сессий на оплате получилось бы около 316 заказов, вышло 212 — минус 104. Это та же цифра, что в теории, но теперь вы получили её сами и можете пересчитать на любую дату или платформу. Оговорка для отчёта: «до» и «после» — разные дни, и часть разницы может давать что-то ещё, случившееся 15 июня. Но iOS в те же дни не просел — значит, причина в Android.
