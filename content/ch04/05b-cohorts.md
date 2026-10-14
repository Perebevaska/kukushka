---
title: "Когорты и удержание"
lead: "Гостей в приложении с каждым месяцем больше. Значит, всё хорошо? Не обязательно: новые гости могут прятать тех, кто ушёл. Учимся делить гостей на когорты по месяцу первого заказа, строить матрицу удержания и тепловую карту и читать её для бизнеса. Проверка матрицы в SQL и DAU/MAU — в следующем уроке."
files: [preorders.csv, preorder_guests.csv]
recap:
  - "Когорта — гости, у которых первый заказ пришёлся на один и тот же месяц. Месяц жизни (`age`) — сколько календарных месяцев прошло от месяца первого заказа: 0 — сам этот месяц."
  - "Первый заказ гостя на каждой строке: `o.groupby(\"guest_id\")[\"date\"].transform(\"min\")`; когорта — `.dt.to_period(\"M\")`."
  - "Месяц жизни: `(год заказа − год первого) × 12 + (месяц заказа − месяц первого)`. Не делите дни на 30 — это другое определение."
  - "Матрица гостей: `pivot_table(index=\"cohort\", columns=\"age\", values=\"guest_id\", aggfunc=\"nunique\")`; удержание — `active.div(active[0], axis=0)`."
  - "Тепловая карта удержания — `ax.imshow` без столбца 0 (он всегда 100 %) и с подписями когорт."
  - "Читать матрицу: столбец — когорты одного возраста (кого лучше удерживаем), строка — жизнь одной когорты, диагональ — один календарный месяц (событие для всех)."
---

## Новые данные: предзаказ в приложении

С января 2026 года в приложении «Зерна» можно сделать **предзаказ**: выбрал напиток заранее — забрал без очереди. Выгрузка за полгода:

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
g = pd.read_csv("preorder_guests.csv")
print(o.shape, "гостей:", o["guest_id"].nunique())
print(o["date"].min().date(), "—", o["date"].max().date())
o.head()
```

`preorders.csv` — один предзаказ на строку: `order_id`, `guest_id`, `date` (день заказа), `shop_id`, `amount` (сумма, ₽). `preorder_guests.csv` — справочник гостей: `source` — откуда гость пришёл в приложение («приложение» — сам нашёл в магазине приложений, «QR на стойке» — по наклейке на кассе, «акция» — по мартовской акции «первый предзаказ за 1 ₽»), и `city`.

Вопрос продакт-менеджера: **возвращаются ли гости после первого предзаказа и окупилась ли мартовская акция?** Чтобы ответить, нужны когорты.

## Зачем когорты

Посчитаем самое простое — сколько разных гостей делали предзаказ в каждом месяце:

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o.groupby(o["date"].dt.to_period("M"))["guest_id"].nunique()
```

В январе 330 гостей, в июне — 874. Рост почти в 2.7 раза. Но из этой цифры не видно главного: в июне заказывают **те же** гости, что и зимой, или в основном новые, а старые давно ушли? Если каждый месяц приходит 300 новых гостей, а уходит 280 старых, общий счётчик всё равно растёт — и скрывает, что приложение почти никого не удерживает.

**Когорта** — группа гостей, которые начали в одно время. У нас — **месяц первого предзаказа**: «январская когорта» — все, кто впервые заказал в январе. Дальше за каждой когортой следят отдельно: сколько из неё вернулось через месяц, через два, через три. Так новые гости не смешиваются со старыми.

::: tip Аналогия
Школа следит не за «всеми учениками сразу», а за выпусками: сколько из набора 2020 года дошло до выпускного. Если смотреть только на общее число учеников, хороший новый набор скроет, что из прошлых классов половина ушла. Одно отличие: в школу приходят в один день, а в когорту — в течение всего месяца, поэтому «месяц 0» у разных гостей неодинаково длинный.
:::

::: sql
В SQL то же самое: сначала `MIN(date)` по гостю — дата первого заказа, затем `GROUP BY` по месяцу этой даты. Полный запрос с CTE — в следующем уроке «Когорты в SQL и DAU/MAU: проверка и частота»: там тот же расчёт сделан в DuckDB и сверен с pandas.
:::

### Игрушечный пример руками

Четыре гостя и девять заказов:

| гость | заказы |
|---|---|
| A | 5 янв, 20 янв, 3 фев |
| B | 28 янв, 2 мар |
| C | 10 фев, 15 фев, 1 мар |
| D | 25 фев |

1. **Первый заказ и когорта.** У A — 5 января (январская когорта), у B — 28 января (январская), у C — 10 февраля (февральская), у D — 25 февраля (февральская).
2. **Месяц жизни** каждого заказа — сколько календарных месяцев прошло от месяца первого заказа. Заказ A 3 февраля — месяц 1. Заказ B 2 марта — месяц 2 (январь → март), хотя прошло всего 33 дня. Заказ C 1 марта — месяц 1.
3. **Сколько гостей когорты активны в каждом месяце жизни.** Январская: в месяце 0 — двое (A, B), в месяце 1 — один (A), в месяце 2 — один (B). Февральская: в месяце 0 — двое (C, D), в месяце 1 — один (C).
4. **Удержание** — доля от размера когорты: январская — 100 %, 50 %, 50 %; февральская — 100 %, 50 %.

Обратите внимание: B не заказывал в феврале, но вернулся в марте, — удержание месяца 2 может быть не меньше удержания месяца 1. Удержание здесь значит «был активен в этом месяце», а не «ни разу не пропал».

::: figure cohort-toy
Четыре гостя на календаре: первый заказ задаёт когорту, номер календарного месяца от него — месяц жизни. Справа — те же гости матрицей: число разных гостей и удержание в процентах.
:::

```python
import pandas as pd
t = pd.DataFrame({
    "guest_id": list("AAABBCCCD"),
    "date": pd.to_datetime(["2026-01-05", "2026-01-20", "2026-02-03", "2026-01-28", "2026-03-02",
                            "2026-02-10", "2026-02-15", "2026-03-01", "2026-02-25"]),
})
t["first"] = t.groupby("guest_id")["date"].transform("min")
t["cohort"] = t["first"].dt.to_period("M")
t["age"] = (t["date"].dt.year - t["first"].dt.year) * 12 + (t["date"].dt.month - t["first"].dt.month)
print(t)
t.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")
```

Что здесь происходит:

- `groupby("guest_id")["date"].transform("min")` — для **каждой строки** дата первого заказа её гостя. `transform` возвращает столько же строк, сколько было, а `agg("min")` дал бы одну строку на гостя (урок «Группировки: GROUP BY и HAVING»);
- `.dt.to_period("M")` превращает дату в месяц: `2026-01-28` → `2026-01`;
- `age` — разница в месяцах через годы и номера месяцев: `(2026 − 2026) × 12 + (3 − 1) = 2` для заказа B 2 марта;
- `pivot_table(..., aggfunc="nunique")` — в ячейке число **разных** гостей: у A два заказа в январе, но гость один.

::: predict
```python static
import pandas as pd
first = pd.Timestamp("2026-01-31")
date = pd.Timestamp("2026-02-01")
print((date.year - first.year) * 12 + (date.month - first.month), (date - first).days // 30)
```

- `0 0`
- [x] `1 0`
- `1 1`

Почему: календарных месяцев прошло один (январь → февраль), хотя между датами всего один день. Деление дней на 30 даёт 0 — это другое определение месяца жизни. В следующем уроке «Когорты в SQL и DAU/MAU: проверка и частота» такая разница всплывёт при сверке pandas и SQL.
:::

::: quiz
Число гостей, которые делали предзаказ, растёт каждый месяц: 330 в январе, 874 в июне. Можно ли по этой цифре сказать, что гости хорошо возвращаются?

- [x] Нет: рост может давать приток новых гостей, а старые при этом уходят — нужно смотреть на каждую когорту отдельно
  > Общий счётчик складывает новых и вернувшихся. Чтобы увидеть возвраты, гостей делят по месяцу первого заказа и следят за каждой группой.
- [ ] Да: раз гостей больше, значит, они возвращаются
  > Если каждый месяц приходит 300 новых и уходит 280 старых, счётчик растёт, а удержание почти нулевое.
- [ ] Нет: нужно смотреть на число заказов, а не гостей
  > Число заказов тоже смешивает новых и старых — проблема в смешении, а не в единице счёта.
- [ ] Да, если рост больше 50 %
  > Порог не помогает: любой рост может целиком объясняться новыми гостями.
:::

{{practice: first-month, p-cohort}}

## Когорта и месяц жизни на реальных данных

Те же три строки — на всей выгрузке:

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)

print(o.groupby("cohort")["guest_id"].nunique())   # размер когорт
o[["guest_id", "date", "first", "cohort", "age"]].head()
```

Что здесь происходит:

- размер когорты — число разных гостей с этим месяцем первого заказа: в январе 330, в феврале 300, в марте **620** — вдвое больше соседних месяцев. Это мартовская акция;
- `age` у первой строки каждого гостя — 0, у последующих — 0, 1, 2… Отрицательных значений быть не может: первый заказ — самый ранний.

Как читать: размеры когорт — уже полезная цифра для бизнеса (сколько новых гостей привёл каждый месяц), но ещё не ответ на вопрос «возвращаются ли». Для него нужна матрица.

::: warn Типичные ошибки
- **`agg` вместо `transform`.** `o.groupby("guest_id")["date"].min()` — одна строка на гостя (2 210 строк), её нельзя просто записать столбцом в таблицу из 17 598 заказов. Нужен `transform("min")` или `merge` со справочником первых дат.
- **Когорта по дате регистрации, а вопрос — про заказы.** Если гость зарегистрировался в январе, а заказал впервые в апреле, январская когорта получит «спящего» гостя с нулевым месяцем 0. Определение когорты выбирают под вопрос и пишут в отчёте.
- **Месяц жизни через `.days // 30`.** Это 30-дневные периоды, а не календарные месяцы: заказы 31 января и 1 февраля окажутся в одном периоде. Можно и так, но тогда везде — и в SQL, и в отчёте.
:::

{{practice: age}}

## Матрица удержания

Сначала — сколько разных гостей каждой когорты были активны в каждом месяце жизни. Потом делим каждую строку на размер когорты — столбец `0`:

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)

active = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")
ret = (active.div(active[0], axis=0) * 100).round(1)
print(active)
ret
```

Что здесь происходит:

- `active` — **гости**: строка — когорта, столбец — месяц жизни, в ячейке — сколько гостей этой когорты делали хотя бы один предзаказ в этом месяце жизни;
- `active[0]` — первый столбец, размеры когорт; `div(..., axis=0)` делит **каждую строку** на своё число (`axis=0` — выравнивание по строкам). Без `axis=0` pandas попытался бы делить по столбцам и выдал бы почти сплошные `NaN`;
- `ret` — **удержание в процентах**; столбец 0 всегда 100.

Как читать результат:

- **Треугольник.** Январская когорта прожила у нас 6 месяцев (0–5), июньская — только месяц 0. Пустые ячейки справа внизу — не «ноль удержания», а «ещё не наступило».
- **Строка** — жизнь одной когорты: январская 100 → 56.4 → 42.1 → 30.6 → 26.7 → 20.0 %. После первого месяца уходит почти половина, дальше потери замедляются.
- **Столбец** — когорты одного возраста: удержание месяца 1 у всех, кроме марта, — 56–61 %, у мартовской — **37.4 %**.

::: predict
```python static
import pandas as pd
active = pd.DataFrame({0: [200, 100], 1: [50, 40]}, index=["янв", "фев"])
print(active.div(active[0], axis=0)[1].tolist())
```

- `[0.25, 0.2]`
- [x] `[0.25, 0.4]`
- `[0.5, 0.4]`

Почему: каждая строка делится на свой размер когорты: 50 / 200 = 0.25 и 40 / 100 = 0.4. У февральской когорты удержание выше, хотя вернувшихся гостей меньше.
:::

{{practice: retention}}

## Тепловая карта удержания

Таблица из 21 числа читается тяжело. Тепловая карта красит ячейки: чем выше удержание, тем темнее. Столбец 0 рисовать не нужно — там всегда 100 %, и он забрал бы всю шкалу цвета.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
active = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")
ret = active.div(active[0], axis=0) * 100
show = ret.drop(columns=0)                         # месяцы 1–5

fig, ax = plt.subplots(figsize=(7, 4))
im = ax.imshow(show.values, cmap="YlGn", aspect="auto", vmin=0)
fig.colorbar(im, ax=ax, label="удержание, %")
ax.set_xticks(range(show.shape[1]))
ax.set_xticklabels(show.columns)
ax.set_yticks(range(show.shape[0]))
ax.set_yticklabels([f"{c} (n={n:.0f})" for c, n in zip(show.index.astype(str), active[0])])
for i in range(show.shape[0]):
    for j in range(show.shape[1]):
        v = show.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9)
ax.set_xlabel("месяц жизни")
ax.set_title("Мартовская когорта удерживается хуже остальных")
```

Что здесь происходит:

- `ax.imshow(матрица)` рисует таблицу цветными клетками: строка `i` — по оси Y, столбец `j` — по оси X. `aspect="auto"` растягивает клетки под размер полотна, `vmin=0` — шкала начинается с нуля;
- ячейки `NaN` (будущие месяцы) imshow оставляет пустыми — треугольник виден сразу;
- подписи когорт с размером `n=` — чтобы читатель видел, на скольких гостях держится строка;
- двойной цикл с `ax.text(j, i, …)` подписывает числа в клетках; `if not np.isnan(v)` пропускает пустые.

Что видно: строка марта светлее всех во всех столбцах, а остальные когорты почти одного тона — удержание стабильное. Заголовок — уже вывод; почему так лучше, разберём в уроке «Понятный график» дальше в главе.

{{practice: heat}}

## Как читать матрицу удержания для бизнеса

У матрицы три направления, и каждое отвечает на свой вопрос:

| направление | что сравниваем | вопрос |
|---|---|---|
| **столбец** | когорты в одном месяце жизни | каких гостей мы удерживаем лучше: привлечённых в январе или в марте? |
| **строка** | одна когорта во времени | как быстро уходят гости и где кривая выходит на «полку» |
| **диагональ** | один календарный месяц у всех когорт | было ли событие, которое задело всех сразу: сбой приложения, новое меню, праздники |

Диагональ — потому что январская когорта в месяце 2, февральская в месяце 1 и мартовская в месяце 0 — это один и тот же календарный март.

::: figure cohort-directions
Матрица удержания предзаказа: синяя рамка — строка января, красная — столбец «месяц 1», пунктир — диагональ календарного марта. Провал только в строке мартовской когорты, а не на диагонали.
:::

Кривые удержания — та же матрица линиями: по линии на когорту.

```python
import pandas as pd
import matplotlib.pyplot as plt

o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
active = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")
ret = active.div(active[0], axis=0) * 100

fig, ax = plt.subplots(figsize=(7, 3.5))
for cohort, row in ret.iterrows():
    row = row.dropna()
    style = "-" if str(cohort) != "2026-03" else "--"
    ax.plot(row.index, row.values, style, marker="o", label=str(cohort))
ax.set_xlabel("месяц жизни")
ax.set_ylabel("удержание, %")
ax.set_ylim(0, 105)
ax.legend(ncol=3)
ax.set_title("Кривые удержания когорт")
```

Что здесь происходит:

- `ret.iterrows()` перебирает таблицу по строкам и на каждом шаге отдаёт пару: имя строки (здесь когорта, `Period('2026-01', 'M')`) и саму строку как Series. У этой Series индекс — месяцы жизни 0–5, значения — удержание в процентах;
- `row.dropna()` убирает `NaN` — месяцы, которые для этой когорты ещё не наступили. У июньской когорты остаётся одна точка (месяц 0), у январской — шесть: рисуем только то, что уже наблюдали;
- `style` — вид линии: `"-"` — сплошная, `"--"` — пунктир. Пунктиром рисуем мартовскую когорту, чтобы выделить её среди остальных;
- `ax.plot(row.index, row.values, style, ...)` — по X месяцы жизни, по Y удержание; `label=str(cohort)` — подпись для легенды.

Что получилось:

1. **Столбец 1.** Мартовская когорта — 37.4 %, остальные — от 56.4 до 60.9 %. Отличается именно мартовская **когорта**, а не март как месяц: у январской и февральской когорт в марте провала нет (42.1 % и 60.0 % — в линию с их кривыми).
2. **Строки.** Самые большие потери — между месяцами 0 и 1, дальше кривые становятся положе. Кто пережил первый месяц, скорее всего, останется ещё на несколько.
3. **В абсолютных числах.** В месяце жизни 3 из январской когорты остался 101 гость, из февральской — 99, из мартовской — 85. Мартовская когорта была почти вдвое больше, а постоянных гостей дала меньше.

::: quiz
В столбце «месяц 1» у мартовской когорты 37 %, у остальных — 56–61 %. При этом у январской и февральской когорт в марте удержание обычное. Какой вывод честнее?

- [x] Дело в составе мартовских гостей: акция привела много людей, которые пришли за скидкой и не вернулись
  > Плохая ячейка — во всей строке когорты, а не на диагонали марта. Значит, отличается состав когорты; срез по источнику (`source`) это подтверждает.
- [ ] В марте что-то сломалось в приложении, поэтому все гости заказывали реже
  > Тогда провал был бы на диагонали — у всех когорт в календарном марте. У январской и февральской когорт его нет.
- [ ] Мартовская когорта самая большая, поэтому её удержание ниже — так всегда бывает
  > Размер сам по себе не снижает долю. Он делает цифру точнее, но не меньше.
- [ ] Удержание месяца 1 у мартовской когорты ещё «не дозрело»
  > Март закончился, апрель — тоже: месяц 1 у мартовской когорты полностью наблюдён. «Не дозрели» только ячейки текущего месяца.
:::

::: warn Типичные ошибки
- **Сравнивать когорты разного возраста.** «У июньской когорты удержание за всё время выше январской» — у июньской есть только месяц 0. Сравнивайте одинаковые месяцы жизни — столбцы.
- **Среднее удержание по всей матрице.** Старые когорты дают больше ячеек, молодые — меньше; среднее по всем клеткам смешивает возраст и качество.
- **Срез по источнику без учёта возраста.** Гостей «по акции» привлекали только в марте, а «из приложения» — все полгода. Сравнивать источники нужно на одинаковых месяцах жизни и только по когортам, у которых этот месяц уже наступил.
- **Маленькие когорты.** Когорта из 30 гостей даёт скачки по 3 пункта от одного человека — подписывайте размер `n=` и не делайте выводов по одной клетке.
:::

{{practice: by-source, promo-payoff}}

## Разберём вместе: окупилась ли мартовская акция

Продакт-менеджер спрашивает: «Акция привела 620 гостей вместо обычных 300. Повторим её?» Пройдём по шагам.

1. **Размер.** Мартовская когорта — 620 гостей, из них 342 пришли по акции.
2. **Удержание по источнику внутри мартовской когорты** (месяцы 0–3):

| источник | гостей | месяц 1 | месяц 2 | месяц 3 |
|---|---|---|---|---|
| акция | 342 | 23.7 % | 5.0 % | 1.5 % |
| QR на стойке | 129 | 49.6 % | 33.3 % | 27.1 % |
| приложение | 149 | 58.4 % | 42.3 % | 30.2 % |

3. **Что это значит.** Гости, пришедшие без акции, удерживаются как обычные когорты. А из 342 «акционных» в месяце жизни 3 заказывают 5 человек. Акция привлекла не постоянных гостей, а охотников за скидкой.
4. **Деньги.** Выручка на гостя за первые три месяца жизни (месяцы 0–2): «акция» — 989 ₽, «приложение» — 3 517 ₽, «QR на стойке» — 2 942 ₽. В `amount` уже стоит то, что гость заплатил со скидкой, но не вычтена себестоимость чашки, отданной за 1 ₽, — с ней «акционные» гости выглядят ещё хуже.
5. **Вывод.** «Акция "первый предзаказ за 1 ₽" удвоила мартовский приток (620 гостей против 300–330), но из 342 акционных гостей в месяце жизни 3 осталось 5 (1.5 %); за три месяца они принесли по 989 ₽ — втрое меньше органических. Повторять акцию в таком виде не стоит; вариант — скидка не на первый, а на третий заказ, чтобы награждать привычку. Ограничение: данные только за полгода, и акция была одна».

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
g = pd.read_csv("preorder_guests.csv")
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M").astype(str)
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
m = o[o["cohort"] == "2026-03"].merge(g, on="guest_id")

t = m.pivot_table(index="source", columns="age", values="guest_id", aggfunc="nunique")
print((t.div(t[0], axis=0) * 100).round(1))
size = m.groupby("source")["guest_id"].nunique()
print((m[m["age"] <= 2].groupby("source")["amount"].sum() / size).round(0))
```

Что получилось: одна матрица, разрезанная по источнику, превратила «акция привела много гостей» в «акция привела много гостей на один раз». Когортный взгляд показывает то, чего не видно в общем счётчике: качество привлечённых гостей.

## Практика

## task: first-month | Месяц первого заказа | warmup

Добавьте в `o` столбец `first` — дату первого предзаказа гостя (на каждой строке) и столбец `cohort` — месяц этой даты (`to_period("M")`). Сохраните в `sizes` число разных гостей в каждой когорте (Series, индекс — когорта).

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])

```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date'])
f = r.groupby('guest_id')['date'].transform('min')
oo = need('o', _pd.DataFrame)
assert 'first' in oo.columns, 'В o нет столбца first.'
assert len(oo) == len(r), f'В o {len(oo)} строк, а заказов {len(r)}: first нужен на каждой строке — transform, а не agg.'
assert (_pd.to_datetime(oo['first']).values == f.values).all(), 'first не совпадает с первой датой гостя: groupby("guest_id")["date"].transform("min").'
assert 'cohort' in oo.columns, 'В o нет столбца cohort.'
assert [str(x)[:7] for x in oo['cohort']] == [str(x) for x in f.dt.to_period('M')], 'cohort — месяц даты first: .dt.to_period("M").'
want = r.assign(c=f.dt.to_period('M')).groupby('c')['guest_id'].nunique()
s = need('sizes', _pd.Series)
assert [int(v) for v in s.values] == [int(v) for v in want.values], f'sizes = {list(s.values)}, а нужно столько разных гостей в когорте: nunique, а не size.'
```

### hint
Первая дата гостя на каждой строке — `transform`: `o.groupby("guest_id")["date"].transform("min")`.

### hint
`o["cohort"] = o["first"].dt.to_period("M")`; размер когорты — `o.groupby("cohort")["guest_id"].nunique()`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
sizes = o.groupby("cohort")["guest_id"].nunique()
sizes
```

## task: p-cohort | Месяц жизни | warmup

Соберите программу, которая добавляет к заказам месяц жизни `age`: сколько календарных месяцев прошло от месяца первого заказа гостя.

### parsons
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
years = o["date"].dt.year - o["first"].dt.year
months = o["date"].dt.month - o["first"].dt.month
o["age"] = years * 12 + months
```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date'])
f = r.groupby('guest_id')['date'].transform('min')
oo = need('o', _pd.DataFrame)
assert 'age' in oo.columns, 'В o нет столбца age: последняя строка должна его создать.'
assert (oo['age'].values == ((r['date'].dt.year - f.dt.year) * 12 + (r['date'].dt.month - f.dt.month)).values).all(), 'age не совпадает с календарными месяцами от первого заказа: годы × 12 + месяцы, и first — до них.'
```

### hint
Сначала нужна дата первого заказа — без неё не из чего вычитать.

### hint
Порядок: чтение → `first` через `transform` → разница лет → разница месяцев → `age = years * 12 + months`.

## task: age | Гости по месяцам жизни | base

Постройте `active` — таблицу «когорта × месяц жизни», в ячейке — число разных гостей когорты, сделавших предзаказ в этом месяце жизни. Сохраните в `jan_m3` число гостей январской когорты, активных в месяце 3, а в `total_m0` — сумму столбца 0 (должна совпасть с числом всех гостей).

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)

```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date'])
f = r.groupby('guest_id')['date'].transform('min')
r['cohort'] = f.dt.to_period('M')
r['age'] = (r['date'].dt.year - f.dt.year) * 12 + (r['date'].dt.month - f.dt.month)
w = r.pivot_table(index='cohort', columns='age', values='guest_id', aggfunc='nunique').fillna(0)
a = need('active', _pd.DataFrame).fillna(0)
assert a.shape == w.shape, f'Размер active {a.shape}, а нужно {w.shape}: строки — когорты, столбцы — месяцы жизни.'
if a.values.sum() > w.values.sum() * 1.5:
    raise AssertionError('В ячейках похоже число заказов, а нужно число разных гостей: aggfunc="nunique".')
assert (a.values == w.values).all(), 'Значения active не совпадают: pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique").'
assert int(need('jan_m3')) == int(w.iloc[0][3]), f'jan_m3 = {need("jan_m3")}: строка января, столбец 3.'
assert int(need('total_m0')) == r['guest_id'].nunique(), f'total_m0 = {need("total_m0")}, а гостей {r["guest_id"].nunique()}.'
```

### hint
Широкая таблица из длинной — `pivot_table` с `aggfunc="nunique"` по `guest_id`.

### hint
`active = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")`. Ячейка — `active.iloc[0][3]` или `active.loc["2026-01", 3]`.

### hint
Сумма столбца — `active[0].sum()`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
active = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique")
jan_m3 = active.iloc[0][3]
total_m0 = active[0].sum()
active
```

### explain
Из 330 гостей январской когорты в месяце 3 (апрель) заказывал 101. Сумма столбца 0 — 2 210, ровно столько гостей в выгрузке: каждый гость попадает в месяц 0 своей когорты ровно один раз. Это простая контрольная сумма: если бы она не сошлась, значит, когорта или месяц жизни посчитаны неверно (например, `age` вышел отрицательным). С `aggfunc="size"` в ячейках оказалось бы число заказов — 17 598 в сумме, — и «удержание» вышло бы больше 100 %.

## task: retention | Удержание в процентах | base

По таблице `active` (уже посчитана) постройте `ret` — удержание в процентах (каждая строка делится на размер своей когорты), с одним знаком. Сохраните `m1_march` — удержание мартовской когорты в месяце 1, и `best_m1` — когорту с наибольшим удержанием месяца 1. Подойдёт и то, что вернёт `idxmax()`, — значение вида `Period('2026-02', 'M')`, то есть «месяц» в pandas, — и строка вида `"2026-02"` (её даёт `str(...)`).

### setup
```python
import pandas as _pd0
_r0 = _pd0.read_csv('preorders.csv', parse_dates=['date'])
_f0 = _r0.groupby('guest_id')['date'].transform('min')
_r0['cohort'] = _f0.dt.to_period('M')
_r0['age'] = (_r0['date'].dt.year - _f0.dt.year) * 12 + (_r0['date'].dt.month - _f0.dt.month)
active = _r0.pivot_table(index='cohort', columns='age', values='guest_id', aggfunc='nunique')
```

### starter
```python
import pandas as pd
# active — гости по когортам (строки) и месяцам жизни (столбцы)
active
```

### check
```python
import pandas as _pd
a = active
w = (a.div(a[0], axis=0) * 100).round(1)
r = need('ret', _pd.DataFrame)
assert r.shape == w.shape, f'Размер ret {r.shape}, а нужно {w.shape}.'
x, y = r.fillna(-1).values, w.fillna(-1).values
if abs(x[0][1] - y[0][1] / 100) < 0.01:
    raise AssertionError('ret в долях, а нужно в процентах: умножьте на 100.')
assert all(close(p, q, 0.051) for p, q in zip(x.ravel(), y.ravel())), 'Значения ret не совпадают: active.div(active[0], axis=0) * 100, округление до 1 знака.'
assert close(need('m1_march'), w.iloc[2][1], 0.051), f'm1_march = {need("m1_march")}.'
assert str(need('best_m1'))[:7] == str(w[1].idxmax()), f'best_m1 = {need("best_m1")!r}: у какой когорты больше всего в столбце 1?'
```

### hint
Делить строку на её первое число — `active.div(active[0], axis=0)`. Без `axis=0` выравнивание пойдёт по столбцам.

### hint
`ret = (active.div(active[0], axis=0) * 100).round(1)`; мартовская строка — третья: `ret.iloc[2][1]`.

### hint
Когорта с максимумом в столбце — `ret[1].idxmax()`. Он вернёт `Period` — когорту как «месяц» pandas; если хотите строку — оберните в `str(...)`, проверка примет оба варианта.

### solution
```python
import pandas as pd
ret = (active.div(active[0], axis=0) * 100).round(1)
m1_march = ret.iloc[2][1]
best_m1 = str(ret[1].idxmax())
ret
```

### explain
Удержание месяца 1 у мартовской когорты — 37.4 %, у остальных — от 56.4 до 60.9 %, лучшее — у майской (60.9 %). `idxmax` по столбцу пропускает `NaN`, поэтому июньская когорта без месяца 1 не мешает. Если забыть `axis=0`, pandas поделит таблицу на Series, сопоставляя её индекс (когорты) со столбцами (месяцы жизни), — почти все ячейки станут `NaN`. Это быстрый признак ошибки.

## task: heat | Тепловая карта | base

Нарисуйте тепловую карту удержания (`ret` — уже посчитано, в процентах) **без столбца 0**: `ax.imshow`, шкала цветов `fig.colorbar`, подписи по оси Y — когорты строками (`"2026-01"` …), по оси X — месяцы жизни 1–5. Подпишите ось X: «месяц жизни».

### setup
```python
import pandas as _pd0
_r0 = _pd0.read_csv('preorders.csv', parse_dates=['date'])
_f0 = _r0.groupby('guest_id')['date'].transform('min')
_r0['cohort'] = _f0.dt.to_period('M')
_r0['age'] = (_r0['date'].dt.year - _f0.dt.year) * 12 + (_r0['date'].dt.month - _f0.dt.month)
_a0 = _r0.pivot_table(index='cohort', columns='age', values='guest_id', aggfunc='nunique')
ret = _a0.div(_a0[0], axis=0) * 100
```

### starter
```python
import matplotlib.pyplot as plt
# ret — удержание, %: строки — когорты, столбцы — месяцы жизни 0–5
ret.round(1)
```

### check
```python
import numpy as _np
w = ret.drop(columns=0)
ax = ax_of()
assert ax.images, 'Нужна картинка-матрица: ax.imshow(...).'
arr = _np.ma.filled(_np.ma.asarray(ax.images[0].get_array(), dtype=float), _np.nan)
if arr.shape == ret.shape:
    raise AssertionError('В карте 6 столбцов: уберите месяц 0 — ret.drop(columns=0). Он всегда 100 % и съедает шкалу цвета.')
assert arr.shape == w.shape, f'Размер картинки {arr.shape}, а нужно {w.shape}.'
ok = _np.isnan(arr) == _np.isnan(w.values)
assert ok.all() and _np.allclose(_np.nan_to_num(arr), _np.nan_to_num(w.values), atol=0.06), 'Значения картинки не совпадают с удержанием в процентах.'
assert len(figs[0].axes) == 2, 'Добавьте шкалу цветов: fig.colorbar(im, ax=ax).'
ylab = [t.get_text()[:7] for t in ax.get_yticklabels()]
assert ylab == [str(c) for c in w.index], f'Подписи по Y: {ylab} — когорты по порядку (set_yticks и set_yticklabels).'
xlab = [t.get_text() for t in ax.get_xticklabels()]
assert xlab == [str(c) for c in w.columns], f'Подписи по X: {xlab} — месяцы 1–5.'
assert ax.get_xlabel() == 'месяц жизни', f'Подпись оси X: {ax.get_xlabel()!r}, а нужно «месяц жизни» — ax.set_xlabel(...).'
```

### hint
`show = ret.drop(columns=0)`; `im = ax.imshow(show.values, cmap="YlGn", aspect="auto")`; `fig.colorbar(im, ax=ax)`.

### hint
Подписи: `ax.set_xticks(range(show.shape[1]))`, `ax.set_xticklabels(show.columns)`; так же по Y с `show.index.astype(str)`.

### solution
```python
import matplotlib.pyplot as plt
show = ret.drop(columns=0)
fig, ax = plt.subplots(figsize=(7, 4))
im = ax.imshow(show.values, cmap="YlGn", aspect="auto", vmin=0)
fig.colorbar(im, ax=ax, label="удержание, %")
ax.set_xticks(range(show.shape[1]))
ax.set_xticklabels(show.columns)
ax.set_yticks(range(show.shape[0]))
ax.set_yticklabels(show.index.astype(str))
ax.set_xlabel("месяц жизни")
ax.set_title("Удержание когорт, %")
```

### explain
Без столбца 0 шкала цвета идёт от 0 до 61 %, и разница между мартовской когортой (37 %) и остальными (56–61 %) видна сразу. Если оставить столбец 0, 100 % заберут самый тёмный цвет, а все остальные клетки сольются в похожие оттенки. Пустые клетки в правом нижнем углу — месяцы, которые для молодых когорт ещё не наступили; imshow оставляет их пустыми, и это правильно: это не нули.

## task: by-source | Удержание по источнику | plus

Сравните удержание месяца 1 по источнику гостя (`source` из `preorder_guests.csv`). Берите только когорты, у которых месяц 1 уже наступил (январь–май). Сохраните `m1_by_source` — словарь «источник → удержание месяца 1, %» (1 знак) и `worst` — источник с наименьшим удержанием.

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
g = pd.read_csv("preorder_guests.csv")
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M").astype(str)
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)

```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date']).merge(_pd.read_csv('preorder_guests.csv'), on='guest_id')
f = r.groupby('guest_id')['date'].transform('min')
r['cohort'] = f.dt.to_period('M').astype(str)
r['age'] = (r['date'].dt.year - f.dt.year) * 12 + (r['date'].dt.month - f.dt.month)
def _m1(x):
    t = x.pivot_table(index='source', columns='age', values='guest_id', aggfunc='nunique')
    return (t[1] / t[0] * 100).round(1)
w = _m1(r[r['cohort'] <= '2026-05'])
allc = _m1(r)
got = {k: float(v) for k, v in dict(need('m1_by_source')).items()}
assert set(got) == set(w.index), f'Ключи: {sorted(got)} — нужны все три источника.'
if all(close(got[k], allc[k], 0.051) for k in got) and not all(close(got[k], w[k], 0.051) for k in got):
    raise AssertionError('В расчёт попала июньская когорта: у неё месяц 1 ещё не наступил, и она занижает удержание. Оставьте когорты январь–май.')
assert all(close(got[k], w[k], 0.051) for k in w.index), f'm1_by_source = {got}, а нужно {w.to_dict()}.'
assert need('worst') == w.idxmin(), f'worst = {need("worst")!r}.'
```

### hint
Присоедините источник: `o.merge(g, on="guest_id")`. Отфильтруйте когорты: `o["cohort"] <= "2026-05"` — строки вида `"2026-05"` сравниваются по порядку.

### hint
`t = x.pivot_table(index="source", columns="age", values="guest_id", aggfunc="nunique")`; удержание месяца 1 — `t[1] / t[0] * 100`.

### hint
`m1_by_source = (t[1] / t[0] * 100).round(1).to_dict()`; худший — `min(m1_by_source, key=m1_by_source.get)` или `idxmin()` у Series.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
g = pd.read_csv("preorder_guests.csv")
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M").astype(str)
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
x = o[o["cohort"] <= "2026-05"].merge(g, on="guest_id")
t = x.pivot_table(index="source", columns="age", values="guest_id", aggfunc="nunique")
m1 = (t[1] / t[0] * 100).round(1)
m1_by_source = m1.to_dict()
worst = m1.idxmin()
m1
```

### explain
Месяц 1: «приложение» — 62.8 %, «QR на стойке» — 52.3 %, «акция» — 23.7 %. Сами нашедшие приложение возвращаются лучше всех: у них уже было намерение. Если оставить июньскую когорту, её 310 гостей попадут в знаменатель месяца 0, но в месяце 1 у них ещё не может быть заказов — удержание всех источников, кроме акции (её гости только мартовские), занизится. Это та же ловушка «незрелых» ячеек, только спрятанная внутри среза.

## task: promo-payoff | Окупилась ли акция | star

Для мартовской когорты (`"2026-03"`) посчитайте выручку на гостя за первые три месяца жизни (месяцы 0–2) по источнику: сумма `amount` заказов с `age <= 2`, делённая на число гостей источника в когорте. Сохраните `rev3` — словарь «источник → выручка на гостя, ₽» (целое, округление до рубля) и `times` — во сколько раз выручка на гостя из «приложения» больше, чем из «акции» (1 знак).

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
g = pd.read_csv("preorder_guests.csv")

```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date']).merge(_pd.read_csv('preorder_guests.csv'), on='guest_id')
f = r.groupby('guest_id')['date'].transform('min')
r['cohort'] = f.dt.to_period('M').astype(str)
r['age'] = (r['date'].dt.year - f.dt.year) * 12 + (r['date'].dt.month - f.dt.month)
m = r[r['cohort'] == '2026-03']
size = m.groupby('source')['guest_id'].nunique()
w = (m[m['age'] <= 2].groupby('source')['amount'].sum() / size).round(0)
got = {k: float(v) for k, v in dict(need('rev3')).items()}
assert set(got) == set(w.index), f'Ключи rev3: {sorted(got)}.'
bad = (m[m['age'] <= 2].groupby('source')['amount'].sum() / m[m['age'] <= 2].groupby('source').size()).round(0)
if all(close(got[k], bad[k], 1) for k in got):
    raise AssertionError('Это выручка на заказ, а нужна на гостя: делите на число разных гостей источника в когорте.')
assert all(close(got[k], w[k], 1) for k in w.index), f'rev3 = {got}, а нужно {w.to_dict()}.'
assert close(need('times'), round(w['приложение'] / w['акция'], 1), 0.051), f'times = {need("times")}.'
```

### hint
Нужны когорта, месяц жизни и источник: `transform("min")`, формула `age` и `merge(g, on="guest_id")`. Потом оставьте `cohort == "2026-03"`.

### hint
Знаменатель — гости источника во всей когорте: `m.groupby("source")["guest_id"].nunique()`. Числитель — выручка только за `age <= 2`.

### hint
`rev = m[m["age"] <= 2].groupby("source")["amount"].sum() / size`; затем `.round(0)`, `times = round(rev["приложение"] / rev["акция"], 1)`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
g = pd.read_csv("preorder_guests.csv")
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M").astype(str)
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
m = o[o["cohort"] == "2026-03"].merge(g, on="guest_id")
size = m.groupby("source")["guest_id"].nunique()
rev = (m[m["age"] <= 2].groupby("source")["amount"].sum() / size).round(0)
rev3 = rev.to_dict()
times = round(rev["приложение"] / rev["акция"], 1)
rev
```

### explain
За три месяца гость «из приложения» принёс 3 517 ₽, «с QR на стойке» — 2 942 ₽, «по акции» — 989 ₽: в 3.6 раза меньше. Окно одинаковое для всех (месяцы 0–2 одной когорты), поэтому сравнение честное. Делить нужно на всех гостей источника, а не на тех, кто заказывал: иначе ушедшие гости выпадут из знаменателя, и акция будет выглядеть лучше, чем есть. Ограничение: в `amount` — уже оплаченная сумма со скидкой, но себестоимость чашки, отданной за 1 ₽, не вычтена; с ней разница ещё больше.
