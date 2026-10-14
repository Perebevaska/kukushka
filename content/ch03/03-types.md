---
title: "Типы: из текста в числа и даты"
lead: "Число, записанное как текст, нельзя сложить, а дату-строку нельзя сравнить с другой датой. Учимся читать выгрузки с нестандартным форматом, превращать текст в числа и даты и проверять, что при этом ничего не потерялось. Книги Excel с листами и шапкой — в следующем уроке."
files: [pos_december.csv, clients_raw.csv, reviews.csv]
recap:
  - "Тип столбца — `df.dtypes`. Основные: `int64`, `float64`, `str`, `bool`, `datetime64`."
  - "Выгрузка из Excel: `pd.read_csv(\"файл.csv\", sep=\";\", decimal=\",\")`."
  - "Текст → число: `pd.to_numeric(s, errors=\"coerce\")`. Всё, что не число, станет `NaN`."
  - "После преобразования проверьте потери: `s[num.isna() & s.notna()]` — что было, но не превратилось."
  - "Перед преобразованием текст чистят: `s.str.replace(\"%\", \"\")`, `s.str.replace(\" \", \"\")`."
  - "Целые с пропусками — тип `\"Int64\"` (с большой буквы): `s.astype(\"Int64\")`. Обычный `int` с `NaN` не работает."
  - "Даты: `pd.to_datetime(s, format=\"%d.%m.%Y %H:%M\", errors=\"coerce\")`. Несколько форматов — несколько проходов и `fillna`."
---

## Почему тип важен

В уроке «Первый осмотр: что не так с данными» `bonus` прочитался как текст. Чем это плохо — видно на простых примерах:

::: predict
```python static
import pandas as pd
s = pd.Series(["1", "2"])
print(s.sum())
```

- `3`
- [x] `12`
- `Ошибка TypeError`

Почему: `+` для строк — это склейка. `sum()` по текстовому столбцу склеивает строки в одну, а не складывает числа.
:::

::: predict
```python static
import pandas as pd
print(pd.Series(["10", "9"]).sort_values().tolist())
```

- `['9', '10']`
- [x] `['10', '9']`
- `[9, 10]`

Почему: строки сравниваются по символам, как слова в словаре. «1» идёт раньше «9», поэтому «10» < «9».
:::

Ошибки не будет ни в одном из случаев — просто неверный результат. Поэтому типы проверяют сразу после загрузки: `df.dtypes` или `df.info()`.

| Тип | Что хранит | Пример |
|---|---|---|
| `int64` | целые числа | 2, 150 |
| `float64` | дробные числа и `NaN` | 262.5 |
| `str` | текст | «Латте» |
| `bool` | `True` / `False` | результат сравнения |
| `datetime64` | дата и время | 2026-12-01 08:36 |

## Выгрузка с точкой с запятой

В декабре в кофейнях поставили новую кассу. Её выгрузка — `pos_december.csv` — выглядит иначе. Попробуем прочитать как обычно:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv")
print(pos.shape)
pos.head(3)
```

Получился один столбец со всем текстом. Причина — разделитель: касса, как и русский Excel, разделяет поля точкой с запятой, а `read_csv` по умолчанию ждёт запятую. Указываем `sep=";"`:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";")
print(pos.dtypes)
pos.head(3)
```

Столбцы на месте, но `price` — текст: «262,50». Запятая в дробных числах — тоже привычка русского Excel. Её задаёт параметр `decimal=","`:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
print(pos["price"].dtype)
print("выручка без скидок:", (pos["price"] * pos["qty"]).sum())
```

::: tip
Если CSV открылся одним столбцом или числа стали текстом — первым делом проверьте `sep` и `decimal`. Посмотреть на «сырые» строки файла можно и без pandas: `print(open("pos_december.csv").read()[:300])`.
:::

{{practice: read-pos}}

## Текст → число: to_numeric

Не всё решается параметрами `read_csv`. В столбце `discount` скидка записана как «10%» — с этим `read_csv` не справится. Знак процента нужно убрать, а оставшееся превратить в число функцией `pd.to_numeric`:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
d = pos["discount"].str.replace("%", "")
pos["disc"] = pd.to_numeric(d) / 100
pos[["discount", "disc"]].drop_duplicates()
```

В выводе есть и строка, где `discount` пустой, а `disc` — `NaN`: у 28 чеков из 293 скидка не записана. Если сложить выручку со скидками как есть, эти 28 чеков молча выпадут из суммы: выйдет 96 067 ₽ вместо 103 249.50 ₽. Что означает пустая скидка и чем её заменить, вы решите в задаче «Выручка со скидками».

Если среди значений есть что-то, что числом не станет, `to_numeric` упадёт с ошибкой. Параметр `errors="coerce"` («принудить») вместо этого превращает такие значения в `NaN`:

```python
import pandas as pd
s = pd.Series(["320", "1 250", "—", None])
print(pd.to_numeric(s, errors="coerce").tolist())
```

::: warn
`errors="coerce"` удобен, но опасен: он молча превращает в `NaN` всё, что не понял. «1 250» исчезло — а это настоящий баланс! Поэтому после преобразования **всегда** смотрите, что потерялось: значения, которые были, но не превратились в число.
:::

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
num = pd.to_numeric(df["bonus"], errors="coerce")
lost = df["bonus"][num.isna() & df["bonus"].notna()]
lost.value_counts()
```

Почти все потери — числа с пробелом. Убираем пробелы перед преобразованием и проверяем ещё раз:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
clean = df["bonus"].str.replace(" ", "")
num = pd.to_numeric(clean, errors="coerce")
df["bonus"][num.isna() & df["bonus"].notna()].value_counts()
```

Осталось только «—» — его и правда нужно превратить в пропуск. Вот это и есть правильный порядок: очистить → преобразовать → проверить потери.

::: figure coerce-check
Четыре значения через `to_numeric(errors="coerce")` до и после чистки пробелов. «Потеря» — значение было, а числом не стало: так находят настоящие балансы, которые `coerce` молча превратил в `NaN`.
:::

::: sql
`pd.to_numeric(s, errors="coerce")` — это `TRY_CAST(bonus AS INT)` (или `SAFE_CAST` в BigQuery): не получилось — `NULL`.
:::

::: quiz
`pd.to_numeric(df["bonus"], errors="coerce")` — и пропусков в столбце стало 54 вместо 15. Почему?

- [x] Значения вроде «1 200» с пробелом не разобрались как число и молча стали `NaN`
  > `errors="coerce"` ничего не сообщает: всё, что не похоже на число, становится пропуском. Сначала чистят текст (`str.replace(" ", "")`), потом переводят в число.
- [ ] `to_numeric` удаляет строки с ошибками
  > Строки остаются на месте, меняется только значение в клетке.
- [ ] Так и должно быть: бонусы не бывают числами
  > Бонусы — числа, просто записанные текстом с пробелами.
- [ ] Нужно было `errors="raise"`, тогда пропусков не будет
  > С `raise` программа упадёт на первом же «1 200» — пропусков не будет, но и результата тоже.
:::

{{practice: stars, discount, bonus-num}}

## Целые числа с пропусками: Int64

Количество, оценка, число заказов — целые числа. Но если в столбце есть `NaN`, pandas хранит его как `float64`, и вместо 5 вы увидите 5.0. Привести к обычному `int` не получится:

```python error
import pandas as pd
s = pd.Series([5.0, None, 3.0])
s.astype(int)
```

Для таких случаев в pandas есть тип **`Int64`** — с большой буквы. Он хранит целые числа и пропуски (`<NA>`):

```python
import pandas as pd
s = pd.Series([5.0, None, 3.0])
s.astype("Int64")
```

Пример из жизни — оценки в отзывах. В `reviews.csv` рейтинг записан по-разному: «5», «5/5», «4 из 5». Оценка всегда одна цифра, поэтому достаточно взять первый символ: `str[0]` работает со строками в столбце так же, как с одной строкой:

```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
reviews["stars"] = pd.to_numeric(reviews["rating"].str[0]).astype("Int64")
reviews[["rating", "stars"]].drop_duplicates().head(8)
```

{{practice: int64}}

## Текст → дата: to_datetime

Даты с главы 2 нам знакомы. В кассовой выгрузке время записано по-русски: «01.12.2026 08:36». Формат лучше указать явно — тогда pandas не будет гадать, где день, а где месяц:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
pos["time"] = pd.to_datetime(pos["time"], format="%d.%m.%Y %H:%M")
print(pos["time"].dtype)
pos.groupby(pos["time"].dt.date).size()
```

Коды формата: `%d` — день, `%m` — месяц, `%Y` — год из четырёх цифр, `%H` — часы, `%M` — минуты. Остальные символы (точки, пробелы, двоеточия) пишутся как есть.

### Несколько форматов в одном столбце

В анкетах дата рождения записана то как «1990-05-12», то как «12.05.1990». Надёжный способ — разобрать столбец два раза, каждым форматом с `errors="coerce"`, а потом объединить: где первый проход дал `NaT` (пропуск для дат), взять результат второго.

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
iso = pd.to_datetime(df["birth_date"], format="%Y-%m-%d", errors="coerce")
ru = pd.to_datetime(df["birth_date"], format="%d.%m.%Y", errors="coerce")
born = iso.fillna(ru)
print("разобрано:", born.notna().sum(), "из", df["birth_date"].notna().sum())
df["birth_date"][born.isna() & df["birth_date"].notna()].value_counts()
```

Не разобралось только «не указано» — так и должно быть. Проверка потерь работает и для дат.

::: figure date-two-pass
Два прохода `to_datetime`: каждый понимает только свой формат, `fillna` собирает результат, а то, что не стало датой ни в одном проходе, проверяют глазами.
:::

Есть и ленивый способ — `format="mixed"`: pandas угадывает формат каждой строки отдельно. Проверьте, чем это грозит.

::: predict
```python static
import pandas as pd
s = pd.Series(["2001-12-03", "03.12.2001"])
d = pd.to_datetime(s, format="mixed", dayfirst=True)
print(*d.dt.date)
```

- `2001-12-03 2001-12-03`
- [x] `2001-03-12 2001-12-03`
- `Ошибка ValueError`

Почему: `format="mixed"` угадывает формат каждой строки отдельно, а `dayfirst=True` велит считать первое число днём — и pandas применил это даже к ISO-дате «2001-12-03», переставив день и месяц. Ошибки нет, дата неверная. Поэтому форматы лучше задавать явно.
:::

{{practice: p-days, shop-hours, born, age}}

## Разберём вместе: одна строка кассы от сырого текста до числа

Первая строка `pos_december.csv` в файле выглядит так:

```text
D-0001;01.12.2026 08:36;UFA-1;Американо;M;1;187,50;10%
```

Пройдём её путь по шагам.

1. **`pd.read_csv("pos_december.csv")`** — разделитель по умолчанию запятая, а в заголовке запятых нет. Получится таблица из **одного** столбца с длинным названием `id;time;shop;…`, а запятая в «187,50» ещё и отрежет копейки в индекс. Ошибки нет — и это опаснее ошибки.
2. **`sep=";"`** — восемь столбцов, но `price` — текст «187,50»: запятая не считается десятичной точкой.
3. **`decimal=","`** — `price` становится числом **187.5**.
4. **`discount`** — текст «10%». Убираем знак процента, `to_numeric` даёт 10, делим на 100 — **0.10**. Здесь `row["discount"]` — одна строка, а не столбец, поэтому `.str` не нужен: это обычный `replace` строки из главы 1.
5. **`time`** — текст «01.12.2026 08:36». `to_datetime(..., format="%d.%m.%Y %H:%M")` — дата-время, у которой есть `.dt.hour` = **8**.
6. Выручка строки с учётом скидки: 187.5 × 1 × (1 − 0.10) = **168.75** ₽.

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
row = pos.iloc[0]
disc = pd.to_numeric(row["discount"].replace("%", "")) / 100
when = pd.to_datetime(row["time"], format="%d.%m.%Y %H:%M")
print(row["price"], disc, when.hour, row["price"] * row["qty"] * (1 - disc))
```

Что получилось: каждое преобразование отвечает на свой вопрос — «где границы столбцов», «какой знак у дробей», «что значит процент», «в каком формате дата». Пропустите любой шаг, и сумма за неделю со скидками (103 249.50 ₽ — её вы посчитали в задаче «Выручка со скидками») превратится в ошибку или склейку строк.

::: warn Типичные ошибки
- **Тип «на глаз».** «187,50» выглядит как число, но `dtypes` скажет `str` — проверяйте типы сразу после загрузки.
- **`errors="coerce"` без проверки потерь.** Всё непонятное станет `NaN` молча; сравните число пропусков до и после.
- **Дата без формата.** «01.12.2026» pandas может прочитать как 12 января; указывайте `format=`.
- **`astype(int)` на столбце с пропусками.** Упадёт — для целых с пропусками есть `Int64`.
:::

## Практика

## task: read-pos | Прочитать кассу | warmup

Загрузите `pos_december.csv` в `pos` так, чтобы получилось 8 столбцов, а `price` стал числом. Сохраните в `gross` выручку без учёта скидок (сумма `price × qty`).

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv")

```

### check
```python
import pandas as _pd
p0 = _pd.read_csv('pos_december.csv', sep=';', decimal=',')
p = need('pos', _pd.DataFrame)
assert p.shape[1] == 8, f'В pos {p.shape[1]} столбцов. Разделитель в файле — точка с запятой.'
assert _pd.api.types.is_float_dtype(p['price']), f'price — {p["price"].dtype}. Дробная часть отделена запятой: decimal=",".'
assert close(need('gross'), (p0['price'] * p0['qty']).sum()), f'gross = {need("gross")}.'
```

### hint
Откройте первую строку файла глазами: какой символ разделяет столбцы и какой — целую и дробную часть?

### hint
`pd.read_csv("pos_december.csv", sep=";", decimal=",")`; выручка — `(pos["price"] * pos["qty"]).sum()`.

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
gross = (pos["price"] * pos["qty"]).sum()
```

## task: stars | Средняя оценка | warmup

Превратите `rating` в число (первый символ строки) и сохраните в `avg_stars` среднюю оценку, округлённую до двух знаков.

### starter
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")

```

### check
```python
import pandas as _pd
r = _pd.read_csv('reviews.csv')
want = round(_pd.to_numeric(r['rating'].str[0]).mean(), 2)
assert close(need('avg_stars'), want), f'avg_stars = {need("avg_stars")}, а нужно {want}.'
```

### hint
Оценки записаны по-разному: «4», «5/5», «2/5». Общее у всех — первый символ.

### hint
`pd.to_numeric(reviews["rating"].str[0])`, затем `mean()` и `round(..., 2)`.

### solution
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
stars = pd.to_numeric(reviews["rating"].str[0])
avg_stars = round(stars.mean(), 2)
```

## task: p-days | Заказы по дням | warmup

Соберите программу, которая выводит дату, в которую по кассе было больше всего заказов.

### parsons
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
pos["time"] = pd.to_datetime(pos["time"], format="%d.%m.%Y %H:%M")
by_day = pos.groupby(pos["time"].dt.date).size()
print(by_day.idxmax())
```

### check
```python
import pandas as _pd
p = _pd.read_csv('pos_december.csv', sep=';', decimal=',')
t = _pd.to_datetime(p['time'], format='%d.%m.%Y %H:%M')
want = str(p.groupby(t.dt.date).size().idxmax())
assert _lines == [want], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Сначала столбец превращают в дату, потом группируют по `dt.date`.

### hint
День с наибольшим числом заказов — `value_counts().idxmax()` или `groupby(...).size().idxmax()`.

## task: discount | Выручка со скидками | base

Превратите `discount` («10%», «0%», пусто) в долю: 10% → 0.1, пустая скидка → 0. Сохраните долю в столбец `disc`, а в `net` — выручку с учётом скидок (сумма `price × qty × (1 − disc)`), округлённую до двух знаков.

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")

```

### check
```python
import pandas as _pd
p = _pd.read_csv('pos_december.csv', sep=';', decimal=',')
dd = _pd.to_numeric(p['discount'].str.replace('%', '')).fillna(0) / 100
pp = need('pos', _pd.DataFrame)
assert 'disc' in pp.columns, 'Нет столбца disc.'
assert pp['disc'].notna().all(), 'В disc остались пропуски — пустая скидка значит 0.'
assert pp['disc'].max() < 1, 'disc — доля: 10% → 0.1, а не 10.'
assert (pp['disc'] - dd).abs().max() < 1e-9, 'disc не совпадает с ожидаемым.'
assert close(need('net'), round((p['price'] * p['qty'] * (1 - dd)).sum(), 2)), f'net = {need("net")}.'
```

### hint
`pos["discount"].str.replace("%", "")` → `pd.to_numeric(...)` → делим на 100.

### hint
Пустая скидка после `to_numeric` — `NaN`. Здесь пусто действительно значит «без скидки», поэтому `fillna(0)`.

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
pos["disc"] = pd.to_numeric(pos["discount"].str.replace("%", "")).fillna(0) / 100
net = round((pos["price"] * pos["qty"] * (1 - pos["disc"])).sum(), 2)
```

### explain
Без скидок — 105 590 ₽, со скидками — 103 249.50 ₽: скидки «съели» 2.2 % выручки. У 28 чеков скидка пустая — здесь это действительно «без скидки», поэтому 0. Если бы пустота означала «скидка не записалась», правильнее было бы выяснить, а не заполнять нулём.

## task: bonus-num | Бонусы без потерь | base

Превратите `bonus` в число через `pd.to_numeric(..., errors="coerce")` так, чтобы потерялся **только** прочерк. Сохраните результат в `bonus`, а в `lost` — **список** исходных непустых значений, которые не превратились в число (без повторов).

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
bonus = pd.to_numeric(df["bonus"], errors="coerce")
```

### check
```python
import pandas as _pd
raw = _pd.read_csv('clients_raw.csv')['bonus']
want = _pd.to_numeric(raw.str.replace(' ', ''), errors='coerce')
got = need('bonus', _pd.Series)
assert got.isna().sum() == want.isna().sum(), f'В bonus {got.isna().sum()} пропусков, а должно быть {want.isna().sum()}. Числа с пробелом («1 250») потерялись?'
assert (got.fillna(-1) == want.fillna(-1)).all(), 'Значения bonus не совпадают с ожидаемыми.'
assert sorted(need('lost')) == ['—'], f'lost = {need("lost")}. Должен остаться только прочерк.'
```

### hint
Перед `to_numeric` уберите пробелы: `df["bonus"].str.replace(" ", "")`.

### hint
Потери: `df["bonus"][bonus.isna() & df["bonus"].notna()]`, без повторов — `.unique()`, список — `list(...)`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
bonus = pd.to_numeric(df["bonus"].str.replace(" ", ""), errors="coerce")
lost = list(df["bonus"][bonus.isna() & df["bonus"].notna()].unique())
```

### explain
В сыром столбце бонусы вроде «1 200» записаны с пробелом между разрядами. Если сразу вызвать `to_numeric(errors="coerce")`, все такие значения молча превратятся в `NaN`, и пропусков станет заметно больше, чем было. Поэтому сначала убираем пробел, и только потом переводим в число. Список `lost` — контроль: после чистки в нём остаётся один «—», то есть потерян только прочерк, а все суммы с пробелами разобраны.

## task: int64 | Оценки — целые | base

Добавьте в `reviews` столбец `stars` — оценку целым числом с поддержкой пропусков (тип `Int64`). Сохраните в `n_no_stars` число отзывов без оценки.

### starter
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")

```

### check
```python
import pandas as _pd
r = need('reviews', _pd.DataFrame)
assert 'stars' in r.columns, 'Нет столбца stars.'
assert str(r['stars'].dtype) == 'Int64', f'Тип stars — {r["stars"].dtype}, а нужен Int64 (с большой буквы).'
r0 = _pd.read_csv('reviews.csv')
assert (r['stars'].fillna(0) == _pd.to_numeric(r0['rating'].str[0]).fillna(0)).all(), 'Значения stars не совпадают с первой цифрой rating.'
assert need('n_no_stars') == r0['rating'].isna().sum(), f'n_no_stars = {need("n_no_stars")}.'
```

### hint
`pd.to_numeric(reviews["rating"].str[0]).astype("Int64")`.

### hint
Отзывы без оценки — `reviews["stars"].isna().sum()`; у `Int64` пропуск выглядит как `<NA>`.

### solution
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
reviews["stars"] = pd.to_numeric(reviews["rating"].str[0]).astype("Int64")
n_no_stars = reviews["stars"].isna().sum()
```

### explain
Целый тип с пропусками `Int64` удобнее `float`: оценка 4 печатается как «4», а не «4.0», и видно, что это целые числа. Отзывов без оценки — 9: их не нужно удалять из таблицы отзывов, текст отзыва полезен и без звёзд.

## task: shop-hours | Время по кассе | base

Превратите `time` в дату-время и сохраните в `last_hour` **самый поздний час** (число от 0 до 23), в который пробивали заказы за всю неделю.

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")

```

### check
```python
import pandas as _pd
p = _pd.read_csv('pos_december.csv', sep=';', decimal=',')
want = _pd.to_datetime(p['time'], format='%d.%m.%Y %H:%M').dt.hour.max()
assert need('last_hour') == want, f'last_hour = {need("last_hour")}, а нужно {want}.'
assert 'format' in _code, 'Укажите формат даты явно — format="%d.%m.%Y %H:%M".'
```

### hint
`pd.to_datetime(pos["time"], format="%d.%m.%Y %H:%M")`, час — `.dt.hour`, наибольший — `max()`.

### hint
Формат: `%d` — день, `%m` — месяц, `%Y` — год из четырёх цифр, `%H:%M` — часы и минуты.

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
pos["time"] = pd.to_datetime(pos["time"], format="%d.%m.%Y %H:%M")
last_hour = pos["time"].dt.hour.max()
```

### explain
Последний заказ за неделю пробит в 21 час. Без `format` pandas мог бы прочитать «01.12.2026» как 12 января — и все дни недели перемешались бы. Явный формат — дешёвая страховка.

## task: born | Дата рождения в двух форматах | plus

Превратите `birth_date` в дату: в столбце встречаются форматы «1990-05-12» и «12.05.1990». Сохраните результат в `born` (Series дат), а в `n_born` — сколько дат удалось разобрать.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
b = _pd.read_csv('clients_raw.csv')['birth_date']
want = _pd.to_datetime(b, format='%Y-%m-%d', errors='coerce').fillna(_pd.to_datetime(b, format='%d.%m.%Y', errors='coerce'))
got = need('born', _pd.Series)
assert _pd.api.types.is_datetime64_any_dtype(got), f'born — {got.dtype}, а нужны даты.'
same = (got.fillna(_pd.Timestamp(0)) == want.fillna(_pd.Timestamp(0)))
assert same.all(), f'Не совпадает {(~same).sum()} дат. Например, исходное {b[~same].iloc[0]!r} → {got[~same].iloc[0]}. Формат mixed путает день и месяц — разберите два формата отдельно.'
assert need('n_born') == want.notna().sum(), f'n_born = {need("n_born")}.'
```

### hint
Два прохода: `pd.to_datetime(..., format="%Y-%m-%d", errors="coerce")` и то же с `format="%d.%m.%Y"`.

### hint
Объедините: `iso.fillna(ru)` — где первый проход не справился, возьмётся значение из второго.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
iso = pd.to_datetime(df["birth_date"], format="%Y-%m-%d", errors="coerce")
ru = pd.to_datetime(df["birth_date"], format="%d.%m.%Y", errors="coerce")
born = iso.fillna(ru)
n_born = born.notna().sum()
```

### explain
Каждый проход понимает только свой формат: строки другого вида он превращает в `NaT`, а не в ошибочную дату. `iso.fillna(ru)` склеивает два результата: где ISO-формат не подошёл, берётся дата из русского формата. Разобрано 267 дат: 209 в формате «год-месяц-день» и 58 в формате «день.месяц.год». Из 288 непустых значений не разобрались 21 — все это слово «не указано», и для даты рождения это тот же пропуск.

## task: age | Возраст гостей | star

Посчитайте возраст гостей на 1 декабря 2026 года: число дней между датой рождения и этой датой, делённое на 365.25 и округлённое вниз до целого. Сохраните в `median_age` медианный возраст.

Подвох: среди дат есть те, что не могут быть датой рождения гостя кофейни. Их в расчёт не включайте — считайте только возрасты от 14 до 100 лет.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
b = _pd.read_csv('clients_raw.csv')['birth_date']
born = _pd.to_datetime(b, format='%Y-%m-%d', errors='coerce').fillna(_pd.to_datetime(b, format='%d.%m.%Y', errors='coerce'))
age = ((_pd.Timestamp('2026-12-01') - born).dt.days // 365.25)
want = age[age.between(14, 100)].median()
assert close(need('median_age'), want), f'median_age = {need("median_age")}, а нужно {want}. Отфильтровали возрасты вне 14–100?'
```

### hint
Разница дат — `pd.Timestamp("2026-12-01") - born`, в днях — `.dt.days`. Округление вниз при делении — `//`.

### hint
Посмотрите на `age.describe()`: минимальный и максимальный возраст подскажут, что не так. Отфильтруйте маской `age.between(14, 100)`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
iso = pd.to_datetime(df["birth_date"], format="%Y-%m-%d", errors="coerce")
ru = pd.to_datetime(df["birth_date"], format="%d.%m.%Y", errors="coerce")
born = iso.fillna(ru)
age = (pd.Timestamp("2026-12-01") - born).dt.days // 365.25
median_age = age[age.between(14, 100)].median()
```

### explain
Среди дат рождения есть 1900-01-01 (так старая CRM заполняла пустое поле) и дата из будущего. Это аномалии — значения, которые формально правильные, но по смыслу невозможные. Ими займёмся в уроке «Аномалии и проверка на здравый смысл».
