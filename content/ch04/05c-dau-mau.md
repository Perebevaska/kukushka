---
title: "Когорты в SQL и DAU/MAU: проверка и частота"
lead: "Матрицу удержания из прошлого урока проверяем вторым расчётом — SQL-запросом в DuckDB — и учимся находить, где два способа разошлись. Потом меряем, как часто гости с нами: DAU, WAU, MAU и sticky factor."
files: [preorders.csv, preorder_guests.csv]
recap:
  - "В SQL: CTE с `MIN(date)` по гостю, `date_trunc('month', …)`, `date_diff('month', …)`, `COUNT(DISTINCT guest_id)`. Результат сверяйте с pandas: та же форма, нулевая разница, одинаковые контрольные суммы."
  - "DAU, WAU, MAU — уникальные гости за день, неделю, месяц. Сумма DAU ≠ MAU. Sticky factor = средний DAU / MAU — какую долю месяца гость с нами."
---

Данные те же, что в уроке «Когорты и удержание»: `preorders.csv` — предзаказы в приложении «Зерна» за полгода (`order_id`, `guest_id`, `date`, `shop_id`, `amount`), `preorder_guests.csv` — справочник гостей с источником (`source`) и городом.

## То же в SQL: DuckDB и сверка с pandas

В работе когорты часто считают прямо в базе — SQL-запросом. DuckDB умеет выполнять SQL по таблице pandas (урок «SQL прямо по датафрейму — DuckDB»). Логика та же: первая дата по гостю, месяц когорты, разница в месяцах, уникальные гости.

```python
import pandas as pd
import duckdb

raw = pd.read_csv("preorders.csv", parse_dates=["date"])
sql = duckdb.sql("""
    WITH f AS (                                  -- первый заказ каждого гостя
        SELECT guest_id, MIN(date) AS first
        FROM raw
        GROUP BY guest_id
    )
    SELECT date_trunc('month', f.first) AS cohort,
           date_diff('month', date_trunc('month', f.first),
                              date_trunc('month', r.date)) AS age,
           COUNT(DISTINCT r.guest_id) AS guests
    FROM raw AS r
    JOIN f USING (guest_id)
    GROUP BY 1, 2
    ORDER BY 1, 2
""").df()
sql.head(7)
```

Что здесь происходит:

- CTE `f` — по строке на гостя с датой первого заказа (как `groupby(...).min()` в pandas);
- `JOIN f USING (guest_id)` приклеивает эту дату к каждому заказу — это аналог `transform`;
- `date_trunc('month', …)` — первое число месяца; `date_diff('month', a, b)` — сколько границ месяцев между `a` и `b`. Обе даты обрезаны до месяца, поэтому получаются календарные месяцы, как в pandas;
- `COUNT(DISTINCT r.guest_id)` — уникальные гости, как `nunique`;
- результат — **длинная** таблица: строка на пару (когорта, месяц жизни). В широкую матрицу её разворачивает `pivot_table`.

::: note
DuckDB не понимает столбцы pandas типа `period[M]` и падает с ошибкой «Data type 'period[M]' not recognized». Поэтому в SQL мы передаём свежую таблицу `raw` только с исходными столбцами, а не `o` с колонкой `cohort`.
:::

::: sql
Первую дату можно взять и оконной функцией (урок «Оконные функции SQL»): `MIN(date) OVER (PARTITION BY guest_id)` — тогда CTE и JOIN не нужны, дата появится прямо в каждой строке.
:::

### Сверка: два расчёта должны совпасть

Один и тот же показатель, посчитанный двумя независимыми способами, — лучшая проверка. Если цифры совпали до гостя, ошибки скорее всего нет ни там, ни там. Если не совпали — одна из реализаций считает не то, что вы думаете.

::: tip Аналогия
Вечером кассир сверяет деньги в ящике с отчётом кассы: два независимых счёта одной и той же выручки. Совпали до рубля — можно закрывать смену; разошлись — где-то ошибка, и искать её надо до того, как отчёт уйдёт дальше. Где аналогия хромает: у кассы «правильный» ответ один, а у когорт расхождение бывает и без ошибки в коде — если два расчёта по-разному понимают «месяц жизни».
:::

Чтобы сравнить, таблицы нужно привести к одному виду: у pandas индекс — `Period('2026-01')`, у DuckDB — дата `2026-01-01`; у pandas пустые ячейки `NaN` и дробные числа, у DuckDB ячеек просто нет.

```python
import pandas as pd
import duckdb

raw = pd.read_csv("preorders.csv", parse_dates=["date"])
o = raw.copy()
o["first"] = o.groupby("guest_id")["date"].transform("min")
o["cohort"] = o["first"].dt.to_period("M")
o["age"] = (o["date"].dt.year - o["first"].dt.year) * 12 + (o["date"].dt.month - o["first"].dt.month)
a = o.pivot_table(index="cohort", columns="age", values="guest_id", aggfunc="nunique", fill_value=0)
a.index = a.index.astype(str)                       # Period → '2026-01'

sql = duckdb.sql("""
    WITH f AS (SELECT guest_id, MIN(date) AS first FROM raw GROUP BY guest_id)
    SELECT date_trunc('month', f.first) AS cohort,
           date_diff('month', date_trunc('month', f.first), date_trunc('month', r.date)) AS age,
           COUNT(DISTINCT r.guest_id) AS guests
    FROM raw AS r JOIN f USING (guest_id)
    GROUP BY 1, 2
""").df()
b = sql.pivot_table(index="cohort", columns="age", values="guests",
                    aggfunc="sum", fill_value=0)     # sum — чтобы числа остались целыми
b.index = b.index.strftime("%Y-%m")                 # дата → '2026-01'

diff = a.sub(b, fill_value=0)
print("форма:", a.shape, b.shape)
print("ячеек с разницей:", int((diff != 0).sum().sum()))
print("гостей в месяце 0:", a[0].sum(), b[0].sum(), "| всего гостей:", raw["guest_id"].nunique())
```

Что здесь происходит:

- `fill_value=0` в обоих `pivot_table` — пустые ячейки становятся нулями, а не `NaN`;
- `aggfunc="sum"` у `b`: без `aggfunc` таблица `pivot_table` берёт **среднее** (`mean`), а среднее pandas всегда отдаёт дробным — `330.0`, `161.0`, и `fill_value=0` этого не меняет. В длинной таблице SQL на каждую пару (когорта, месяц) ровно одна строка, поэтому и `sum`, и `mean` дают то же число; `sum` просто оставляет его целым. Если увидите `330.0` — это не ошибка, для сравнения дробная запись не мешает;
- индексы приводим к строке `'2026-01'`: `astype(str)` для `Period`, `strftime("%Y-%m")` для дат;
- `a.sub(b, fill_value=0)` — вычитание с выравниванием по когортам и месяцам; если у одной таблицы есть лишний столбец, разница в нём будет видна, а не спрячется в `NaN`;
- **контрольная сумма**: в месяце 0 каждый гость считается ровно один раз, поэтому сумма столбца 0 обязана равняться числу гостей — 2 210.

Как читать: форма одинаковая (6 × 6), разница ноль во всех ячейках, контрольные суммы сошлись. Теперь матрице можно верить и показывать её с пометкой «посчитано двумя способами».

::: figure cohort-reconcile
Схема сверки: две независимые цепочки — pandas и SQL — приводятся к одному виду и вычитаются; форма, нулевая разница и контрольная сумма месяца 0 должны сойтись.
:::

::: warn Типичные ошибки
- **`a.equals(b)` вернул `False` — «расчёты разошлись».** Часто расходятся только типы: `float` против `int`, `Period` против даты в индексе. Сначала приведите к одному виду, потом сравнивайте значения.
- **`a - b` без `fill_value`.** Если у `b` есть лишний месяц жизни, которого нет у `a`, обычное вычитание даёт в этом столбце `NaN` во **всех** ячейках. Дальше два симптома, оба неверные:
  - `(a - b).fillna(0)` — `NaN` стали нулями, и настоящие расхождения в лишнем столбце **спрятались**: разниц меньше, чем на самом деле;
  - `(a - b != 0)` — `NaN != 0` даёт `True`, и **каждая** ячейка лишнего столбца засчитывается как разница, даже та, где у `b` ноль: разниц больше, чем на самом деле.

  Исправление одно: `a.sub(b, fill_value=0)` — недостающий столбец считается нулями, и разница честная.
- **`COUNT(*)` вместо `COUNT(DISTINCT guest_id)`.** Получится число заказов, а не гостей, — удержание выйдет больше 100 %.
- **Разные определения месяца.** `date_diff('day', …) // 30` в SQL и календарные месяцы в pandas дают разные матрицы; сверка это поймает — и это не ошибка кода, а разное понимание «месяца жизни». Договоритесь об одном.
:::

{{practice: duckdb-ret, reconcile}}

## DAU, WAU, MAU и sticky factor

Удержание отвечает на вопрос «возвращаются ли гости». Второй частый вопрос — **как часто** они с нами. Для него считают активную аудиторию:

- **DAU** (daily active users) — сколько разных гостей сделали хотя бы один предзаказ за день;
- **WAU** (weekly) — за неделю;
- **MAU** (monthly) — за месяц.

Главное слово — **разных**. Гость, который заказывал пять дней подряд, в DAU посчитан пять раз (по разу в каждом дне), а в WAU — один. И внутри дня гость считается один раз: 26 июня было 191 предзаказ, но 180 разных гостей — у кого-то утренний и дневной кофе.

### Игрушечный пример руками

Неделя, четыре гостя:

| день | пн | вт | ср | чт | пт | сб | вс |
|---|---|---|---|---|---|---|---|
| кто заказал | A, B | A | A, C | A | A, B | — | D |
| DAU | 2 | 1 | 2 | 1 | 2 | 0 | 1 |

1. Сумма DAU за неделю — 9, а **WAU — 4** (A, B, C, D): сумма дневных счётчиков считает A пять раз.
2. Средний DAU — 9 / 7 ≈ 1.29.
3. **Sticky factor** (липкость) = средний DAU / WAU = 1.29 / 4 ≈ **32 %**: в среднем гость был с нами примерно 32 % дней недели — около двух дней из семи. Чаще считают по месяцу: средний DAU / MAU.

$$\text{sticky} = \frac{\overline{DAU}}{MAU}$$

Здесь $\overline{DAU}$ — средний DAU за дни месяца, $MAU$ — число разных гостей за этот месяц. 100 % — все гости месяца заказывают каждый день; 3 % — в среднем гость заходит раз в месяц.

::: figure dau-wau
Та же неделя: DAU считают по каждому дню, WAU — разных гостей за всю неделю. Сумма дневных счётчиков 9, разных гостей 4; липкость — средний DAU, делённый на WAU.
:::

::: predict
```python static
days = [{"A", "B"}, {"A"}, {"A", "C"}, {"A"}, {"A", "B"}, set(), {"D"}]
print(sum(len(d) for d in days), len(set().union(*days)))
```

- `9 9`
- [x] `9 4`
- `4 4`

Почему: первое число — сумма дневных счётчиков, второе — размер объединения всех множеств, то есть разных гостей за неделю. Сумма DAU не равна WAU.
:::

На реальных данных — по календарным месяцам:

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])

dau = o.groupby("date")["guest_id"].nunique()                       # гостей в каждый день
month = o["date"].dt.to_period("M")
mau = o.groupby(month)["guest_id"].nunique()                         # гостей за месяц
dau_avg = dau.groupby(dau.index.to_period("M")).mean()               # средний DAU месяца

monthly = pd.DataFrame({"dau": dau_avg.round(1), "mau": mau})
monthly["sticky"] = (monthly["dau"] / monthly["mau"] * 100).round(1)
print(monthly)
print(dau.groupby(dau.index.dayofweek).mean().round(1))              # 0 — понедельник

wau = o.groupby(o["date"].dt.to_period("W"))["guest_id"].nunique()  # гостей за неделю
print(wau.tail(4))
```

Что здесь происходит:

- `groupby("date")["guest_id"].nunique()` — DAU: уникальные гости в каждый день, Series с датой в индексе;
- MAU считаем **по заказам**, а не суммой DAU: `groupby(month)["guest_id"].nunique()`;
- WAU — так же, но по неделе: `to_period("W")` превращает дату в неделю с понедельника по воскресенье (`2026-06-22/2026-06-28`);
- средний DAU месяца — `dau.groupby(dau.index.to_period("M")).mean()`. Это новый приём, он разобран ниже на трёх днях;
- `dau.index.dayofweek` — номер дня недели для каждой даты индекса: 0 — понедельник, 6 — воскресенье. Группировка по нему даёт средний DAU по дням недели.

**Группировка Series по её собственному индексу.** У `dau` дата — не столбец, а индекс, и группировать нужно не по самой дате, а по её месяцу — столбца с месяцем в `dau` нет. Но в `groupby` можно передать не имя столбца, а **готовый список меток** той же длины: какой месяц у каждого дня. Его и даёт `dau.index.to_period("M")`:

```python
import pandas as pd
dau = pd.Series([2, 1, 3], index=pd.to_datetime(["2026-01-30", "2026-01-31", "2026-02-01"]))
print(list(dau.index.to_period("M").astype(str)))   # месяц каждого дня
dau.groupby(dau.index.to_period("M")).mean()
```

Метки — `['2026-01', '2026-01', '2026-02']`: два январских дня и один февральский. Дальше всё как с обычным столбцом в `groupby`: январь — (2 + 1) / 2 = 1.5, февраль — 3.0. Так же работает `dau.groupby(dau.index.dayofweek)`: метки — номера дней недели.

Как читать: sticky factor вырос с 8.6 % в январе до 14.5 % в июне — гости стали заходить чаще: в июне в среднем около четырёх дней из тридцати. Январская цифра занижена: гости приходили в течение всего месяца, и в начале января их почти не было. В будни DAU около 110, в выходные — 42–44: предзаказ — привычка офисных гостей по дороге на работу. WAU в полных неделях июня — 455–499 гостей, а в последней строке всего 249: от недели 29 июня – 5 июля в выгрузке только два дня (об этом — в типичных ошибках ниже).

::: deep Скользящий MAU
Календарный MAU прыгает в начале месяца. Продуктовые команды часто считают **скользящий** MAU — уникальные гости за последние 28 или 30 дней на каждый день. Тогда sticky = DAU / MAU28 можно рисовать линией по дням.

```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
days = pd.date_range("2026-06-01", "2026-06-30")
mau28 = pd.Series(
    [o.loc[o["date"].between(d - pd.Timedelta(days=27), d), "guest_id"].nunique() for d in days],
    index=days,
)
dau = o.groupby("date")["guest_id"].nunique().reindex(days, fill_value=0)
print((dau / mau28 * 100).round(1).describe())
```
:::

::: warn Типичные ошибки
- **MAU = сумма DAU.** Сумма считает постоянного гостя по разу на каждый день; MAU — уникальные гости за месяц, его считают по исходным заказам.
- **Неполная неделя или месяц.** Последняя неделя июня (29–30 июня) с двумя днями даст WAU вдвое ниже соседних — это не падение (урок «Динамика во времени»).
- **Sticky в первый месяц запуска.** Пока база набирается, DAU в начале месяца маленький — липкость занижена.
- **Активность без определения.** «Открыл приложение» и «сделал заказ» — разные DAU. Пишите в отчёте, что считается активностью.
:::

{{practice: dau-max, sticky}}

## Практика

## task: duckdb-ret | Когорты в DuckDB | base

Напишите SQL-запрос в DuckDB к таблице `raw` и сохраните результат в `sql` (DataFrame) — длинную таблицу со столбцами `cohort` (первое число месяца первого заказа), `age` (календарные месяцы от когорты) и `guests` (разные гости). Затем разверните её в `wide` — матрицу «когорта × месяц жизни» через `pivot_table`.

### starter
```python
import pandas as pd
import duckdb
raw = pd.read_csv("preorders.csv", parse_dates=["date"])
sql = duckdb.sql("""
    WITH f AS (
        SELECT guest_id, MIN(date) AS first FROM raw GROUP BY guest_id
    )
    SELECT ...
""").df()
```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date'])
f = r.groupby('guest_id')['date'].transform('min')
r['cohort'] = f.dt.to_period('M').astype(str)
r['age'] = (r['date'].dt.year - f.dt.year) * 12 + (r['date'].dt.month - f.dt.month)
w = r.groupby(['cohort', 'age'])['guest_id'].nunique()
assert 'duckdb' in _code and calls('sql') >= 1, 'Посчитайте через duckdb.sql(...), а не pandas.'
s = need('sql', _pd.DataFrame)
for c in ('cohort', 'age', 'guests'):
    assert c in s.columns, f'В sql нет столбца {c}: дайте ему имя через AS {c}.'
got = {(str(a)[:7], int(b)): int(c) for a, b, c in zip(s['cohort'], s['age'], s['guests'])}
if len(got) > len(w):
    raise AssertionError(f'Пар (когорта, месяц) {len(got)}, а нужно {len(w)}: месяц жизни — date_diff("month") между обрезанными до месяца датами, не дни / 30.')
assert got == {k: int(v) for k, v in w.items()}, 'Числа не совпадают: COUNT(DISTINCT r.guest_id) и date_diff(\'month\', date_trunc(\'month\', f.first), date_trunc(\'month\', r.date)).'
wd = need('wide', _pd.DataFrame)
assert wd.shape == (6, 6), f'wide {wd.shape}, а нужно 6 когорт × 6 месяцев: pivot_table(index="cohort", columns="age", values="guests").'
```

### hint
После CTE `f` соедините заказы с первой датой: `FROM raw AS r JOIN f USING (guest_id)`, сгруппируйте по когорте и месяцу жизни.

### hint
`date_trunc('month', f.first) AS cohort`, `date_diff('month', date_trunc('month', f.first), date_trunc('month', r.date)) AS age`, `COUNT(DISTINCT r.guest_id) AS guests`, `GROUP BY 1, 2`.

### hint
Матрица — `wide = sql.pivot_table(index="cohort", columns="age", values="guests")`.

### solution
```python
import pandas as pd
import duckdb
raw = pd.read_csv("preorders.csv", parse_dates=["date"])
sql = duckdb.sql("""
    WITH f AS (
        SELECT guest_id, MIN(date) AS first FROM raw GROUP BY guest_id
    )
    SELECT date_trunc('month', f.first) AS cohort,
           date_diff('month', date_trunc('month', f.first), date_trunc('month', r.date)) AS age,
           COUNT(DISTINCT r.guest_id) AS guests
    FROM raw AS r
    JOIN f USING (guest_id)
    GROUP BY 1, 2
    ORDER BY 1, 2
""").df()
wide = sql.pivot_table(index="cohort", columns="age", values="guests")
wide
```

### explain
Запрос — та же логика, что в pandas, только по шагам SQL: CTE даёт первую дату гостя, JOIN приклеивает её к заказам, `date_diff` по обрезанным до месяца датам — календарный месяц жизни, `COUNT(DISTINCT)` — гости. В длинной таблице 21 строка: 6 + 5 + 4 + 3 + 2 + 1 — треугольник матрицы, «развёрнутый» в список. Частая ошибка — `COUNT(*)`: он посчитает заказы, и гость с десятью заказами в месяце даст десять «удержанных».

## task: reconcile | Сверка нашла расхождение | plus

Коллега прислал свой запрос: месяц жизни у него — `date_diff('day', f.first, r.date) // 30`. Сверьте его результат с матрицей pandas `a` (уже посчитана, индекс — строки `'2026-01'`, пустые ячейки — 0):

1. Разверните результат коллеги в `b` (тот же вид: индекс `'2026-01'`, `fill_value=0`).
2. Сохраните `n_diff` — число ячеек, где `a` и `b` расходятся (с выравниванием и `fill_value=0`).
3. Сохраните `extra_cols` — список месяцев жизни, которые есть в `b`, но нет в `a`.

### setup
```python
import pandas as _pd0
_r0 = _pd0.read_csv('preorders.csv', parse_dates=['date'])
_f0 = _r0.groupby('guest_id')['date'].transform('min')
_r0['cohort'] = _f0.dt.to_period('M')
_r0['age'] = (_r0['date'].dt.year - _f0.dt.year) * 12 + (_r0['date'].dt.month - _f0.dt.month)
a = _r0.pivot_table(index='cohort', columns='age', values='guest_id', aggfunc='nunique', fill_value=0)
a.index = a.index.astype(str)
```

### starter
```python
import pandas as pd
import duckdb
raw = pd.read_csv("preorders.csv", parse_dates=["date"])
theirs = duckdb.sql("""
    WITH f AS (SELECT guest_id, MIN(date) AS first FROM raw GROUP BY guest_id)
    SELECT date_trunc('month', f.first) AS cohort,
           date_diff('day', f.first, r.date) // 30 AS age,
           COUNT(DISTINCT r.guest_id) AS guests
    FROM raw AS r JOIN f USING (guest_id)
    GROUP BY 1, 2
""").df()
# a — матрица pandas с календарными месяцами
```

### check
```python
import pandas as _pd
import duckdb as _dk
raw0 = _pd.read_csv('preorders.csv', parse_dates=['date'])
t = _dk.sql("""
    WITH f AS (SELECT guest_id, MIN(date) AS first FROM raw0 GROUP BY guest_id)
    SELECT date_trunc('month', f.first) AS cohort, date_diff('day', f.first, r.date) // 30 AS age,
           COUNT(DISTINCT r.guest_id) AS guests
    FROM raw0 AS r JOIN f USING (guest_id) GROUP BY 1, 2
""").df()
bw = t.pivot_table(index='cohort', columns='age', values='guests', fill_value=0)
bw.index = bw.index.strftime('%Y-%m')
dw = a.sub(bw, fill_value=0)
bb = need('b', _pd.DataFrame)
assert [str(i)[:7] for i in bb.index] == list(bw.index), f'Индекс b: {list(bb.index)[:2]}… — приведите к строкам "2026-01" через strftime("%Y-%m").'
assert bb.shape == bw.shape and (bb.fillna(0).values == bw.values).all(), 'b — pivot_table(index="cohort", columns="age", values="guests", fill_value=0) по результату коллеги.'
nd = int((dw != 0).sum().sum())
got = int(need('n_diff'))
extra = ', '.join(str(int(c)) for c in bw.columns if c not in a.columns)
if got == int((a - bw).fillna(0).ne(0).sum().sum()) and got != nd:
    raise AssertionError(f'n_diff = {got}, а ячеек с разницей {nd}: вы спрятали расхождения. Обычное a - b даёт NaN в столбце {extra}, которого нет у a, а fillna(0) превращает эти NaN в «нет разницы». Используйте a.sub(b, fill_value=0).')
if got == int((a - bw).ne(0).sum().sum()) and got != nd:
    raise AssertionError(f'n_diff = {got}, а ячеек с разницей {nd}: вы посчитали NaN как разницу. В столбце {extra} у a нет значений, a - b даёт там NaN, а NaN != 0 — это True, поэтому засчиталась каждая ячейка столбца, даже где у b ноль. Используйте a.sub(b, fill_value=0).')
assert got == nd, f'n_diff = {got}, а ячеек с разницей {nd}. Считайте по diff = a.sub(b, fill_value=0): (diff != 0).sum().sum().'
assert sorted(int(x) for x in need('extra_cols')) == sorted(int(c) for c in bw.columns if c not in a.columns), f'extra_cols = {need("extra_cols")}.'
```

### hint
Шаги те же, что в разделе «Сверка: два расчёта должны совпасть»: развернуть длинную таблицу в матрицу, привести индекс к строкам `'2026-01'`, вычесть с выравниванием и посчитать ненулевые ячейки.

### hint
`b = theirs.pivot_table(index="cohort", columns="age", values="guests", aggfunc="sum", fill_value=0)`, затем `b.index = b.index.strftime("%Y-%m")`. Вычитание — `a.sub(b, fill_value=0)`, а не `a - b`: у `b` есть столбец, которого нет у `a`.

### hint
```python
diff = a.sub(b, fill_value=0)
n_diff = int((diff != 0).sum().sum())
extra_cols = [c for c in b.columns if c not in ...]
```

### solution
```python
import pandas as pd
import duckdb
raw = pd.read_csv("preorders.csv", parse_dates=["date"])
theirs = duckdb.sql("""
    WITH f AS (SELECT guest_id, MIN(date) AS first FROM raw GROUP BY guest_id)
    SELECT date_trunc('month', f.first) AS cohort,
           date_diff('day', f.first, r.date) // 30 AS age,
           COUNT(DISTINCT r.guest_id) AS guests
    FROM raw AS r JOIN f USING (guest_id)
    GROUP BY 1, 2
""").df()
b = theirs.pivot_table(index="cohort", columns="age", values="guests", aggfunc="sum", fill_value=0)
b.index = b.index.strftime("%Y-%m")
diff = a.sub(b, fill_value=0)
n_diff = int((diff != 0).sum().sum())
extra_cols = [c for c in b.columns if c not in a.columns]
print(diff)
```

### explain
Расходятся 17 ячеек, а у коллеги есть лишний «месяц» 6: 30-дневные периоды не совпадают с календарными месяцами. Гость, который впервые заказал 28 января и вернулся 2 марта, у нас в месяце 2, а у коллеги — в периоде 1. Столбец 0 совпал полностью: размеры когорт оба расчёта считают одинаково, поэтому контрольная сумма (2 210 гостей) сошлась бы, а ошибку определений нашла только поячеечная сверка. Код здесь ни у кого не сломан — разное определение. Решение: договориться об одном и написать его в отчёте.

Почему `a.sub(b, fill_value=0)`, а не `a - b`. У `a` нет столбца 6, поэтому `a - b` даёт в нём `NaN` во всех шести ячейках, хотя у `b` там только одно ненулевое число (1 гость январской когорты). Дальше легко ошибиться в обе стороны:

- `(a - b).fillna(0)` и затем `!= 0` — 16 вместо 17: единственное расхождение в столбце 6 спряталось;
- `(a - b != 0)` — 22 вместо 17: `NaN != 0` даёт `True`, и засчитались все шесть ячеек столбца 6, включая пять нулевых у `b`.

С `fill_value=0` недостающий столбец `a` считается нулями, и разница честная: 17.

## task: dau-max | Самый активный день | warmup

Посчитайте `dau` — число разных гостей с предзаказом в каждый день (Series, индекс — дата). Сохраните в `best_day` дату с наибольшим DAU, а в `best_dau` — сам этот DAU.

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])

```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date'])
w = r.groupby('date')['guest_id'].nunique()
s = need('dau', _pd.Series)
if len(s) == len(w) and int(s.sum()) == int(r.groupby('date').size().sum()):
    raise AssertionError('В dau — число заказов в день, а нужно число разных гостей: nunique вместо size.')
assert len(s) == len(w) and [int(v) for v in s.values] == [int(v) for v in w.values], 'dau — groupby("date")["guest_id"].nunique().'
assert _pd.Timestamp(need('best_day')) == w.idxmax(), f'best_day = {need("best_day")}: возьмите idxmax() у dau.'
assert int(need('best_dau')) == int(w.max()), f'best_dau = {need("best_dau")}.'
```

### hint
DAU — уникальные гости за день: `o.groupby("date")["guest_id"].nunique()`.

### hint
Дата максимума — `dau.idxmax()`, сам максимум — `dau.max()`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
dau = o.groupby("date")["guest_id"].nunique()
best_day = dau.idxmax()
best_dau = dau.max()
print(best_day.date(), best_dau)
```

## task: sticky | Липкость по месяцам | base

Соберите таблицу `monthly` по месяцам (индекс — месяц) со столбцами `dau` (средний DAU за дни месяца, 1 знак), `mau` (разные гости за месяц) и `sticky` (`dau / mau × 100`, 1 знак). Сохраните `best_month` — месяц с наибольшей липкостью строкой вида `"2026-01"` (подойдёт и `Period`, который вернёт `idxmax()`).

### starter
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])

```

### check
```python
import pandas as _pd
r = _pd.read_csv('preorders.csv', parse_dates=['date'])
dau = r.groupby('date')['guest_id'].nunique()
da = dau.groupby(dau.index.to_period('M')).mean().round(1)
mau = r.groupby(r['date'].dt.to_period('M'))['guest_id'].nunique()
st = (da / mau * 100).round(1)
m = need('monthly', _pd.DataFrame)
for c in ('dau', 'mau', 'sticky'):
    assert c in m.columns, f'В monthly нет столбца {c}.'
assert len(m) == 6, f'Строк {len(m)}, а месяцев 6.'
sum_dau = dau.groupby(dau.index.to_period('M')).sum()
if all(int(x) == int(y) for x, y in zip(m['mau'], sum_dau)):
    raise AssertionError('mau — это сумма DAU. Нужны разные гости за месяц по исходным заказам: groupby(месяц)["guest_id"].nunique().')
assert [int(x) for x in m['mau']] == [int(x) for x in mau], f'mau = {list(m["mau"])}, а нужно {list(mau)}.'
assert all(close(x, y, 0.051) for x, y in zip(m['dau'], da)), f'dau = {list(m["dau"])}: средний DAU за дни месяца.'
assert all(close(x, y, 0.15) for x, y in zip(m['sticky'], st)), f'sticky = {list(m["sticky"])}, а нужно {list(st)}.'
assert str(need('best_month'))[:7] == str(st.idxmax()), f'best_month = {need("best_month")!r}.'
```

### hint
DAU — `o.groupby("date")["guest_id"].nunique()`; средний за месяц — `dau.groupby(dau.index.to_period("M")).mean()`.

### hint
MAU — по заказам, а не по DAU: `o.groupby(o["date"].dt.to_period("M"))["guest_id"].nunique()`.

### hint
`monthly = pd.DataFrame({"dau": ..., "mau": ...})`, затем `monthly["sticky"] = (monthly["dau"] / monthly["mau"] * 100).round(1)`; лучший — `str(monthly["sticky"].idxmax())`.

### solution
```python
import pandas as pd
o = pd.read_csv("preorders.csv", parse_dates=["date"])
dau = o.groupby("date")["guest_id"].nunique()
dau_avg = dau.groupby(dau.index.to_period("M")).mean()
mau = o.groupby(o["date"].dt.to_period("M"))["guest_id"].nunique()
monthly = pd.DataFrame({"dau": dau_avg.round(1), "mau": mau})
monthly["sticky"] = (monthly["dau"] / monthly["mau"] * 100).round(1)
best_month = str(monthly["sticky"].idxmax())
monthly
```

### explain
Липкость выросла с 8.6 % в январе до 14.5 % в июне: средний гость месяца в июне заказывал около четырёх дней из тридцати. MAU с марта не рос (939 в марте, 874 в июне), а средний DAU рос (99.4 → 127.0) — значит, растёт не аудитория, а привычка. Если бы MAU посчитали суммой DAU, в январе вышло бы 885 вместо 330: постоянный гость посчитался бы по разу за каждый свой день, и липкость стала бы бессмысленной.
