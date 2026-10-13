---
title: DataFrame — таблица в Python
lead: "Знакомимся с pandas — главной библиотекой аналитика на Python. Таблица с именованными столбцами, загрузка CSV одной строкой, первые итоги — то, что в главе 1 требовало десятка строк цикла."
files: [orders_3m.csv, supplier_prices.csv]
recap:
  - "`import pandas as pd`; таблица — `DataFrame`, один столбец — `Series`."
  - "`pd.read_csv(\"файл.csv\")` — загрузить CSV. `df.head()`, `df.shape`, `df.columns`, `df.dtypes`, `df.info()` — первый осмотр."
  - "`df[\"amount\"]` — столбец; у него есть `sum()`, `mean()`, `median()`, `min()`, `max()`, `count()`, `nunique()`, `value_counts()`."
  - "Русские выгрузки: `pd.read_csv(f, sep=\";\", encoding=\"cp1251\", decimal=\",\", thousands=\" \")`. После загрузки — всегда `df.dtypes`: числа не должны остаться `str`."
  - "`read_csv` читает и по адресу в интернете; Google Таблица — через адрес `…/d/<id>/export?format=csv&gid=<лист>` при доступе «все, у кого есть ссылка»."
  - "Пустые ячейки в pandas — `NaN`. `isna()` / `notna()` — проверка; `mean()` от `True/False` — доля."
  - "Последнее выражение в ячейке показывается само — как в Jupyter. Таблицы — таблицей."
---

## Зачем pandas

В мини-проекте главы 1 мы читали CSV циклом, превращали суммы в числа, считали словарями. Работает, но для каждой мелочи — несколько строк. **pandas** — библиотека, которая даёт Python настоящие таблицы: со столбцами по именам, типами и сотнями готовых операций. Почти любой анализ данных на Python начинается со строки:

```python
import pandas as pd
print(pd.__version__)
```

`pd` — общепринятое сокращение, его используют все.

## DataFrame: таблица

Главный объект pandas — **DataFrame**, таблица. Её можно собрать из словаря «столбец → список значений»:

```python
import pandas as pd

menu = pd.DataFrame({
    "drink": ["Латте", "Капучино", "Раф"],
    "price": [210, 190, 260],
})
menu
```

Обратите внимание: в последней строке нет `print`, а таблица появилась. С этой главы в курсе работает правило Jupyter: **значение последнего выражения показывается само**, а таблицы pandas — в виде таблицы. `print(menu)` тоже работает, но выводит обычный текст.

Слева у таблицы — **индекс**: номера строк 0, 1, 2. Это «имена» строк; пока они просто номера по порядку.

::: figure df-anatomy
DataFrame — это индекс, названия столбцов и сами столбцы. Один столбец, `menu["price"]`, — это Series: значения вместе с тем же индексом.
:::

Или из списка словарей — ровно такой структуры, как в уроке «Словари — GROUP BY своими руками» главы 1:

```python
import pandas as pd

orders = [
    {"city": "Пермь", "drink": "Латте", "amount": 450},
    {"city": "Казань", "drink": "Раф", "amount": 320},
]
pd.DataFrame(orders)
```

::: sql
DataFrame — это результат `SELECT`: строки, столбцы с именами и типами. Только он живёт в памяти Python, и с ним можно делать всё, что умеет pandas.
:::

{{practice: menu}}

## Загрузка CSV и первый осмотр

Выгрузка за три месяца — `orders_3m.csv`, больше двух тысяч заказов. Загрузка — одна строка:

```python
import pandas as pd

df = pd.read_csv("orders_3m.csv")
df.head()
```

`head()` показывает первые 5 строк (`head(10)` — десять), `tail()` — последние. Первое, что делают с любой новой таблицей, — осматривают её:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

print(df.shape)          # (строк, столбцов)
print(list(df.columns))  # названия столбцов
print(df.dtypes)         # типы столбцов
```

Типы pandas определил сам: `int64` — целые числа, `str` — текст. Всё, что в главе 1 мы превращали `int(...)` руками, здесь уже сделано.

::: note Почему внизу `dtype: object`
Последняя строка вывода — `dtype: object` — это тип самого списка типов, а не какого-то столбца. На неё не обращайте внимания. И ещё: в pandas 2 (он стоит во многих рабочих Jupyter) текстовые столбцы показываются не как `str`, а как `object`. Для нас это одно и то же — текст.
:::

`info()` собирает всё сразу и показывает, сколько в каждом столбце **непустых** значений:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df.info()
```

У `client_id` непустых меньше, чем строк: не все гости — участники программы лояльности, у остальных номер пустой.

::: sql
`df.head()` — `SELECT * FROM orders LIMIT 5`, `len(df)` — `SELECT COUNT(*)`, а `df.info()` — что-то вроде просмотра схемы таблицы в базе.
:::

{{practice: load, columns}}

## Когда CSV «не такой»: sep, encoding, decimal

`orders_3m.csv` выгружен «по-программистски»: столбцы разделены запятой, дробная часть — через точку, текст в кодировке UTF-8. Именно этого `read_csv` и ждёт по умолчанию. Но поставщик кофе присылает прайс из 1С, бухгалтерия — из Excel с русскими настройками, и там всё иначе: столбцы через `;`, дроби через запятую (`92,40`), тысячи через пробел (`1 890,00`), а кириллица — в старой кодировке Windows-1251. Без нужных параметров такой файл либо не прочитается вовсе, либо прочитается молча неправильно.

::: tip Аналогия
CSV — не строгий стандарт, а договорённость, как телефонный номер: «8 (912) …» и «+7 912 …» — одно и то же, но программа, которая ждёт один формат, второй не поймёт. Перед загрузкой задайте файлу три вопроса: чем разделены столбцы, как записаны дроби, в какой кодировке текст.
:::

**Пример руками.** Три строки из прайса:

```text
товар;цена
Молоко;92,40
Сливки;118,75
```

1. Без параметров pandas режет строки по **запятой**. Запятая есть только внутри цен — и получается каша: один столбец с названием `товар;цена`.
2. С `sep=";"` столбцов два, но цена — текст `"92,40"`: для Python запятая в числе — не дробная часть.
3. С `decimal=","` цена становится числом: 92.40 + 118.75 = **211.15**.

::: figure csv-parse
Три строки прайса, прочитанные тремя способами. Без `sep` pandas режет по запятой внутри цен, с `sep` цена остаётся текстом, с `decimal` — становится числом.
:::

То же кодом (`io.StringIO` превращает строку в «файл в памяти», чтобы не создавать файл на диске):

```python
import io
import pandas as pd

text = "товар;цена\nМолоко;92,40\nСливки;118,75\n"
a = pd.read_csv(io.StringIO(text))
print(a.shape, list(a.columns))                      # шаг 1: один столбец
b = pd.read_csv(io.StringIO(text), sep=";")
print(b["цена"].tolist())                            # шаг 2: цены — текст
c = pd.read_csv(io.StringIO(text), sep=";", decimal=",")
print(c["цена"].tolist(), round(c["цена"].sum(), 2))  # шаг 3: числа
```

Что здесь происходит:

- `a` — один столбец с названием `'товар;цена'`: точка с запятой для pandas — обычный символ, а не граница столбца.
- `b` — столбцов уже два, но `tolist()` показывает строки в кавычках: `'92,40'`. Сложить их нельзя.
- `c` — `decimal=","` объясняет pandas, что запятая — дробная часть. Сумма 211.15, как руками.

**На настоящем файле.** `supplier_prices.csv` — прайс поставщика как он есть. Первая попытка падает:

```python error
import pandas as pd
prices = pd.read_csv("supplier_prices.csv")
```

`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc0` значит: файл не в UTF-8. Байт `0xc0` — это буква «А» в кодировке Windows-1251 (`cp1251`), с неё начинается заголовок «Артикул». Указываем кодировку и разделитель:

```python
import pandas as pd
prices = pd.read_csv("supplier_prices.csv", sep=";", encoding="cp1251")
print(prices.dtypes)
prices["Цена, руб."].head(3).tolist()
```

Столбцы на месте, но цена — `str`: `'1 890,00'`. Мешают сразу две вещи — запятая в дробной части и пробел между тысячами. Для пробела есть параметр `thousands`:

```python
import pandas as pd
prices = pd.read_csv("supplier_prices.csv", sep=";", encoding="cp1251",
                     decimal=",", thousands=" ")
prices["сумма"] = prices["Цена, руб."] * prices["Количество"]
print(prices.dtypes)
print("Заказ у поставщика:", round(prices["сумма"].sum(), 2), "₽")
```

Что здесь происходит:

- `encoding="cp1251"` — как перевести байты файла в буквы. Без него — `UnicodeDecodeError` или «кракозябры» вместо кириллицы.
- `sep=";"` — граница между столбцами.
- `decimal=","` и `thousands=" "` — как записаны числа. Теперь цена — `float64`, и умножение работает.
- `prices["сумма"] = …` — новый столбец: цена × количество по каждой строке. Подробно о новых столбцах — в уроке «Сортировка и новые столбцы: ORDER BY, CASE».

Как читать результат: у каждого столбца правильный тип — текст (`str`) для артикула, названия и единицы, `float64` для цены и новой суммы, `int64` для количества, — значит, файл прочитан верно. Заказ у поставщика — 187 816.80 ₽, больше всего уходит на зерно.

| параметр | что задаёт | по умолчанию | частое значение в русских выгрузках |
|---|---|---|---|
| `sep` | разделитель столбцов | `","` | `";"`, табуляция `"\t"` |
| `encoding` | кодировка текста | `"utf-8"` | `"cp1251"`; `"utf-8-sig"` — UTF-8 из Excel |
| `decimal` | дробная часть | `"."` | `","` |
| `thousands` | разделитель тысяч | нет | `" "` |

Обратная задача — сохранить таблицу так, чтобы русский Excel открыл её двойным щелчком без мастера импорта:

```python static
prices.to_csv("для_excel.csv", sep=";", decimal=",", encoding="utf-8-sig", index=False)
```

`utf-8-sig` добавляет в начало файла невидимую метку, по которой Excel узнаёт UTF-8; без неё русский Excel прочтёт файл как `cp1251`, и «Товар» превратится в «РўРѕРІР°СЂ».

::: warn Типичные ошибки
- **`UnicodeDecodeError: 'utf-8' codec can't decode byte …`** — файл не в UTF-8. Почти всегда помогает `encoding="cp1251"`.
- **Вместо кириллицы — `РўРѕРІР°СЂ` или `Òîâàð`.** Кодировку угадали неверно, но ошибки не было — проверяйте глазами первые строки `head()`.
- **Один столбец с `;` в названии.** Не указан `sep=";"`. Признак — `df.shape` вида `(N, 1)`.
- **Числа прочитались как `str`.** Смотрите `df.dtypes` после каждой загрузки: `decimal=","` и `thousands=" "` чинят это при чтении, а не потом.
- **`ParserError: Expected 3 fields in line 5, saw 4`.** Разделитель не тот: запятые внутри названий режут строку на разное число кусков.
:::

::: quiz
Прайс прочитался с `sep=";"` и `encoding="cp1251"`, но `prices["Цена, руб."].sum()` выдаёт склеенную строку `'1 890,002 450,50…'`. Что добавить в `read_csv`?

- [x] `decimal=","` и `thousands=" "`
  > Цена записана с пробелом между тысячами и запятой перед копейками. Пока pandas не знает об этом, столбец — текст, а сумма текста — склейка строк.
- [ ] `encoding="utf-8"`
  > С кодировкой всё в порядке — названия читаются. Проблема в записи чисел, а не букв.
- [ ] `sep=","`
  > Тогда столбцы снова разрежутся по запятым внутри цен и названий — станет только хуже.
- [ ] Ничего: после загрузки сделать `round(..., 2)`
  > `round` работает с числами, а здесь строки. Чинить надо при чтении.
:::

{{practice: supplier}}

## Данные по ссылке и из Google Sheets

Файл не обязательно скачивать: `read_csv` принимает и **адрес в интернете** — сам скачает и прочитает. Так удобно брать открытые данные или таблицу, которую коллеги ведут онлайн:

```python static
import pandas as pd

url = "https://example.com/open-data/coffee_prices.csv"   # любой адрес, который отдаёт CSV
df = pd.read_csv(url, sep=";", encoding="utf-8")
```

Все параметры из предыдущего раздела работают так же. В браузерной версии курса выход в интернет закрыт, поэтому этот код — для вашего Jupyter.

**Google Sheets.** План продаж «Зерна» ведут в Google Таблице. Её адрес в браузере выглядит так:

```text
https://docs.google.com/spreadsheets/d/1AbC-zerno_Plan2026/edit#gid=0
```

Это страница редактора, а не CSV. Но у каждой таблицы есть адрес **выгрузки**: часть `edit…` заменяется на `export?format=csv&gid=…`, где `gid` — номер листа (его видно в адресе после `gid=`, у первого листа обычно `0`):

```text
https://docs.google.com/spreadsheets/d/1AbC-zerno_Plan2026/export?format=csv&gid=0
```

```python static
import pandas as pd

sheet_id = "1AbC-zerno_Plan2026"
gid = 0
plan = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}")
```

Чтобы это сработало, у таблицы должен быть доступ «Все, у кого есть ссылка» (просмотр). Закрытую таблицу так не прочитать — нужен вход через API, это отдельная тема.

Собрать адрес выгрузки из обычной ссылки — чистая работа со строками, её можно делать и без интернета:

```python
link = "https://docs.google.com/spreadsheets/d/1AbC-zerno_Plan2026/edit#gid=0"

sheet_id = link.split("/d/")[1].split("/")[0]   # всё между «/d/» и следующим «/»
print(sheet_id)
export = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
print(export)
```

Что здесь происходит:

- `link.split("/d/")` режет ссылку на две части: до `/d/` и после. `[1]` — вторая часть, она начинается с идентификатора таблицы.
- `.split("/")[0]` отрезает всё после первого `/` — остаётся только идентификатор `1AbC-zerno_Plan2026`.
- f-строка подставляет его в шаблон адреса выгрузки.

::: warn Типичные ошибки
- **Ссылка на редактор вместо выгрузки.** `read_csv(".../edit#gid=0")` скачает HTML-страницу, и pandas выдаст `ParserError` или таблицу из обрывков разметки.
- **Таблица закрыта.** Вместо данных приходит страница входа в аккаунт — та же `ParserError`. Проверьте доступ по ссылке.
- **Не тот лист.** Без `gid` выгружается первый лист. Номер нужного листа — в адресе после `gid=`.
- **Данные по ссылке меняются.** Сегодняшний расчёт завтра может не повториться: для отчёта сохраните копию (`df.to_csv("plan_2026-10-09.csv")`).
:::

{{practice: sheets-url}}

## Столбец: Series

Один столбец таблицы — это **Series**: значения с индексом. Его берут по имени в квадратных скобках:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

amount = df["amount"]
print(type(amount))
amount.head()
```

У Series есть все агрегаты, которые мы писали циклами:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

print("выручка:", df["amount"].sum())
print("средний чек:", round(df["amount"].mean(), 2))
print("медиана:", df["amount"].median())
print("минимум и максимум:", df["amount"].min(), df["amount"].max())
```

`describe()` выдаёт их сразу пачкой — удобно для первого взгляда на числовой столбец:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["amount"].describe()
```

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
print(df.shape)
```

- `(2, 3)`
- [x] `(3, 2)`
- `6`

Почему: `shape` — это (строк, столбцов). Три строки, два столбца.
:::

::: quiz
`df["amount"]` и `df[["amount"]]` — в чём разница?

- [x] Первое — Series (один столбец), второе — DataFrame из одного столбца
  > Одинарные скобки берут столбец как Series: у неё есть `sum()`, `mean()` и другие методы. Двойные — список столбцов, на выходе таблица.
- [ ] Никакой, это два способа написать одно и то же
  > Результаты разные по типу, и это видно на экране: Series печатается без заголовка таблицы.
- [ ] Второе — синтаксическая ошибка
  > Это корректная запись: внутри внешних скобок — список из одного названия.
- [ ] Первое — копия, второе — ссылка на исходную таблицу
  > Дело не в копиях: различается тип результата — столбец или таблица.
:::

{{practice: p-sum, kpi}}

## Уникальные значения и частоты

Для текстовых столбцов главные вопросы — «какие значения бывают» и «сколько раз каждое»:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

print(df["channel"].unique())     # какие значения есть
print(df["drink"].nunique())      # сколько разных
df["drink"].value_counts()        # сколько раз каждое — по убыванию
```

`value_counts()` — та самая функция подсчёта, которую вы писали словарём в уроке «Словари — GROUP BY своими руками» главы 1, причём сразу отсортированная.

**Как достать первое место.** Результат `value_counts()` — это Series. Слева в выводе — её **индекс** (подписи строк): названия напитков. Справа — **значения**: сколько раз встретился каждый. Поэтому название и число берут из разных мест:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

vc = df["drink"].value_counts()
print(vc.head(3))
print(vc.index[0])    # первая подпись — название самого частого напитка
print(vc.iloc[0])     # первое значение — сколько раз его заказали
```

Что здесь происходит:

- `vc.index` — все подписи по порядку, `[0]` — первая. Это строка `'Капучино'`.
- `vc.iloc[0]` — первое **значение** по порядку (`iloc` — «по номеру позиции», как индекс у списка). Это число 365.
- `vc.head(1)` выглядит похоже, но это всё ещё Series из одной строки, а не название и не число. Его нельзя сравнить с текстом или сложить с числом как одно значение.

::: predict
```python static
import pandas as pd
vc = pd.Series(["Латте", "Раф", "Латте", "Мокко", "Латте"]).value_counts()
print(vc.index[0], vc.iloc[0])
```

- `3 Латте`
- [x] `Латте 3`
- `0 Латте`

Почему: в индексе `value_counts` — сами значения (напитки), в значениях — частоты. Латте встречается три раза и стоит первым.
:::

::: sql
`nunique()` — `COUNT(DISTINCT drink)`, `value_counts()` — `SELECT drink, COUNT(*) … GROUP BY drink ORDER BY 2 DESC`.
:::

::: predict
```python static
import pandas as pd
s = pd.Series(["Латте", "Раф", "Латте", "Мокко", "Латте"])
print(s.nunique())
```

- `5`
- [x] `3`
- `Латте`

Почему: `nunique` считает **разные** значения: Латте, Раф, Мокко.
:::

{{practice: clients, hit}}

## Пустые значения

Пустые ячейки CSV pandas превращает в специальное значение **`NaN`** («not a number») — аналог `NULL`. Агрегаты пропускают его, как и SQL: `count()` считает только непустые.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

print(df["client_id"].count(), "из", len(df))
print(df["client_id"].isna().sum(), "пустых")
```

`isna()` превращает столбец в `True`/`False` («пусто ли»), `notna()` — наоборот. А сумма или среднее столбца из `True/False` считают `True` как 1, `False` как 0. Поэтому `mean()` даёт **долю**:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
print(round(df["client_id"].notna().mean() * 100, 1), "% заказов — по карте лояльности")
```

::: sql
`count()` — это `COUNT(client_id)`, а `len(df)` — `COUNT(*)`. Разница та же, что в SQL.
:::

{{practice: records, loyalty}}

## Разберём вместе: пять заказов руками и одной строкой

Пять заказов на 450, 320, 610, 480 и 290 ₽ — посчитаем главные числа руками и сверим с pandas.

1. **Выручка** — 450 + 320 + 610 + 480 + 290 = **2 150**. В pandas — `s.sum()`.
2. **Средний чек** — 2 150 / 5 = **430**. `s.mean()`.
3. **Медиана** — сортируем: 290, 320, **450**, 480, 610; середина — третий заказ, **450**. `s.median()`.
4. **Доля заказов дороже 400** — дороже 400 три заказа (450, 610, 480), доля 3 / 5 = **0.6**. В pandas: `(s > 400).mean()` — сравнение даёт `[True, False, True, True, False]`, а среднее True/False — доля True.

::: figure bool-mean
Сравнение превращает суммы в True/False, а True/False считаются как 1 и 0. Поэтому `sum()` маски — сколько, `mean()` — какая доля.
:::

```python
import pandas as pd
s = pd.Series([450, 320, 610, 480, 290])
print(s.sum(), s.mean(), s.median())
print((s > 400).tolist(), (s > 400).mean())
```

Что получилось: всё, что в главе 1 требовало цикла и счётчика, здесь — один метод. А приём «`mean()` от сравнения — это доля» будет встречаться в курсе постоянно: доля опозданий, доля заказов по карте, доля ушедших гостей.

::: warn Типичные ошибки
- **`df.amount.sum` без скобок.** Без `()` вы получите сам метод, а не число.
- **`count()` вместо `len()`.** `count()` пропускает пустые значения; число строк — `len(df)`.
- **`unique()` вместо `nunique()`.** Первый возвращает список значений, второй — их количество.
- **Средний чек вместо типичного.** При крупных заказах среднее больше медианы; для «обычного гостя» честнее медиана.
:::

{{practice: describe}}

## Практика

## task: menu | Своя таблица | warmup

Соберите DataFrame `menu` из трёх строк со столбцами `drink` и `price`: Латте — 210, Капучино — 190, Раф — 260. Последней строкой выведите таблицу.

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
m = need('menu', _pd.DataFrame)
assert list(m.columns) == ['drink', 'price'], f'Столбцы: {list(m.columns)}, а нужны drink и price.'
assert m['drink'].tolist() == ['Латте', 'Капучино', 'Раф'] and m['price'].tolist() == [210, 190, 260], 'Проверьте значения в таблице.'
```

### hint
Словарь «название столбца → список значений»: ключи — названия столбцов, списки — значения по строкам в одном порядке.

### hint
`pd.DataFrame({"drink": [...], "price": [...]})`, последней строкой — просто `menu`.

### solution
```python
import pandas as pd

menu = pd.DataFrame({
    "drink": ["Латте", "Капучино", "Раф"],
    "price": [210, 190, 260],
})
menu
```

## task: load | Загрузка | warmup

Загрузите `orders_3m.csv` в `df` и сохраните в `n_rows` число строк таблицы.

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
d = need('df', _pd.DataFrame)
want = len(_pd.read_csv('orders_3m.csv'))
assert need('n_rows') == want, f'n_rows = {need("n_rows")}, а строк {want}.'
```

### hint
Файл лежит рядом с кодом, путь — просто имя файла в кавычках.

### hint
`df = pd.read_csv("orders_3m.csv")`, потом `len(df)` или `df.shape[0]`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
n_rows = len(df)
```

## task: p-sum | Соберите выручку | warmup

Соберите программу, которая выводит выручку за три месяца.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue = df["amount"].sum()
print(revenue)
```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv')['amount'].sum()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Сначала импорт, потом загрузка, расчёт и вывод.

### hint
Выручка — сумма столбца `amount`: `df["amount"].sum()`.

## task: columns | Какие есть столбцы | warmup

Сохраните в `cols` **список** названий столбцов таблицы.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
_c = need('cols')
assert isinstance(_c, list), f'В cols лежит {type(_c).__name__}, а нужен обычный список Python. df.columns — особый объект pandas; превратите его в список: list(...).'
assert _c == ['order_id', 'datetime', 'shop_id', 'drink', 'size', 'qty', 'amount', 'client_id', 'channel'], f'cols = {_c!r}. Нужны все названия столбцов df по порядку.'
```

### hint
`df.columns` — не список, а особый объект «индекс столбцов». Его нужно превратить в список.

### hint
`cols = list(df.columns)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
cols = list(df.columns)
```

## task: kpi | Выручка и средний чек | base

Посчитайте `revenue` — сумму всех заказов и `avg_check` — средний чек, округлённый до двух знаков.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
a = _pd.read_csv('orders_3m.csv')['amount']
assert need('revenue') == a.sum(), f'revenue = {need("revenue")}.'
assert close(need('avg_check'), round(a.mean(), 2)), f'avg_check = {need("avg_check")}, а нужно {round(a.mean(), 2)}.'
assert 'for ' not in _code, 'Обойдитесь без цикла — методами столбца.'
```

### hint
Столбец берётся по имени в квадратных скобках, у него есть методы `sum()` и `mean()`.

### hint
`df["amount"].sum()` и `round(df["amount"].mean(), 2)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue = df["amount"].sum()
avg_check = round(df["amount"].mean(), 2)
```

### explain
Выручка за осень — 710 195 ₽ на 2 089 заказов, средний чек — 339.97 ₽. Две строки кода вместо цикла со счётчиком и суммой; а главное — их невозможно «забыть обнулить».

## task: clients | Сколько гостей с картой | base

Посчитайте `n_clients` — сколько **разных** гостей с картой лояльности делали заказы (пустые `client_id` не считаются).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('orders_3m.csv')['client_id'].nunique()
assert need('n_clients') == want, f'n_clients = {need("n_clients")}, а нужно {want}. nunique сам пропускает пустые значения.'
```

### hint
«Разных гостей» — значит, каждый номер карты считаем один раз, сколько бы заказов он ни сделал.

### hint
`df["client_id"].nunique()` — пустые значения он не считает.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
n_clients = df["client_id"].nunique()
```

### explain
С картой заказывали 260 разных гостей. `count()` дал бы число заказов с картой — каждый гость считался бы столько раз, сколько он приходил; `nunique()` считает людей, а не визиты.

## task: hit | Хит продаж | base

Найдите `top_drink` — самый частый напиток — и `top_count` — сколько раз его заказывали.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
import numbers as _num
vc = _pd.read_csv('orders_3m.csv')['drink'].value_counts()
_t = need('top_drink')
assert not isinstance(_t, (_pd.Series, _pd.DataFrame)), f'В top_drink лежит {type(_t).__name__} — кусок таблицы, а нужно одно значение: название напитка. Названия — в индексе value_counts: возьмите первую подпись, .index[0].'
assert isinstance(_t, str), f'В top_drink лежит {type(_t).__name__} ({_t!r}), а нужна строка — название напитка. Название — в индексе: .index[0]; число — в значениях: .iloc[0].'
assert _t == vc.index[0], f'top_drink = {_t!r}, а это не самый частый напиток. value_counts уже сортирует по убыванию — нужна первая подпись.'
_n = need('top_count')
assert not isinstance(_n, (_pd.Series, _pd.DataFrame)), f'В top_count лежит {type(_n).__name__}, а нужно одно число. Первое значение по порядку — .iloc[0].'
assert isinstance(_n, _num.Integral), f'В top_count лежит {type(_n).__name__} ({_n!r}), а нужно целое число — сколько раз заказали напиток: .iloc[0].'
assert _n == vc.iloc[0], f'top_count = {_n}, а это не число заказов самого частого напитка.'
assert _code.count(str(vc.iloc[0])) == 0, 'Не вписывайте число руками.'
```

### hint
`value_counts()` считает, сколько раз встречается каждый напиток, и сразу сортирует по убыванию. Нужна первая строка результата: название — из индекса, число — из значений (раздел «Уникальные значения и частоты»).

### hint
`vc = df["drink"].value_counts()`. Первое название — `vc.index[0]`, первое значение — `vc.iloc[0]`. Не `vc.head(1)`: это Series, а не одно значение.

### hint
```python
vc = df["drink"].value_counts()
top_drink = vc.index[...]
top_count = vc.iloc[...]
```

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
vc = df["drink"].value_counts()
top_drink = vc.index[0]
top_count = vc.iloc[0]
```

### explain
`value_counts()` — это `GROUP BY drink ... ORDER BY COUNT(*) DESC` одной командой: на выходе Series, где индекс — напитки, значения — число заказов. Поэтому название берём из индекса (`vc.index[0]`), а количество — из значений (`vc.iloc[0]`). Самый частый напиток — капучино, 365 заказов из 2089. Вторым идёт латте с 345: разрыв небольшой, и по другому периоду лидер может смениться.

## task: describe | Типичный чек | base

Средний чек тянут вверх крупные заказы. Посчитайте `median_check` — медиану суммы заказа — и `share_big` — долю заказов дороже 600 рублей в процентах с одним знаком.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
a = _pd.read_csv('orders_3m.csv')['amount']
assert need('median_check') == a.median(), f'median_check = {need("median_check")}.'
assert close(need('share_big'), round((a > 600).mean() * 100, 1)), f'share_big = {need("share_big")}, а нужно {round((a > 600).mean() * 100, 1)}.'
```

### hint
Сравнение столбца с числом — `df["amount"] > 600` — даёт столбец из `True/False`. Его `mean()` — доля.

### hint
`share_big = round((df["amount"] > 600).mean() * 100, 1)`; медиана — `df["amount"].median()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
median_check = df["amount"].median()
share_big = round((df["amount"] > 600).mean() * 100, 1)
```

### explain
Медиана — 285 ₽, а средний чек — 340: крупные заказы (дороже 600 ₽ — 10.8 %) тянут среднее вверх. «Типичный гость тратит 285 ₽» — честнее, чем «в среднем 340».

## task: supplier | Прайс поставщика | base

Прочитайте прайс `supplier_prices.csv` в таблицу `prices` так, чтобы цена (`Цена, руб.`) стала числом. Затем посчитайте `total` — сумму заказа у поставщика: цена × количество по каждой строке, сложить и округлить до двух знаков.

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
p = need('prices', _pd.DataFrame)
assert p.shape[1] >= 5, f'В prices {p.shape[1]} столбец(а). Похоже, не указан разделитель: в этом файле столбцы разделены точкой с запятой.'
assert 'Цена, руб.' in p.columns, f'Столбцы: {list(p.columns)}. Если вместо букв странные символы — проверьте кодировку.'
assert _pd.api.types.is_numeric_dtype(p['Цена, руб.']), f'Цена прочиталась как {p["Цена, руб."].dtype}: {p["Цена, руб."].iloc[0]!r}. Подскажите read_csv, как записаны дробная часть и тысячи.'
assert close(need('total'), 187816.8, 0.01), f'total = {need("total")}. Нужна сумма произведений цены на количество по всем строкам.'
assert not has_literal(187816.8), 'Посчитайте сумму кодом, а не вписывайте готовое число.'
```

### hint
Задайте файлу три вопроса: чем разделены столбцы, в какой кодировке текст, как записаны числа. Откройте его без параметров — сообщение об ошибке подскажет первый ответ.

### hint
Нужны четыре параметра: `sep=";"`, `encoding="cp1251"`, `decimal=","` и `thousands=" "`.

### hint
```python
prices = pd.read_csv("supplier_prices.csv", sep=..., encoding=..., decimal=..., thousands=...)
total = round((prices["Цена, руб."] * prices[...]).sum(), 2)
```

### solution
```python
import pandas as pd
prices = pd.read_csv("supplier_prices.csv", sep=";", encoding="cp1251",
                     decimal=",", thousands=" ")
total = round((prices["Цена, руб."] * prices["Количество"]).sum(), 2)
```

### explain
Заказ — 187 816.80 ₽. Все четыре параметра здесь нужны: без `encoding` файл не откроется, без `sep` получится один столбец, без `decimal` и `thousands` цена останется текстом `'1 890,00'`, и умножение строки на число склеит её саму с собой несколько раз: `'1 890,00' * 2` — это `'1 890,001 890,00'`. Такая ошибка не падает — поэтому после каждой загрузки смотрите `dtypes`.

## task: sheets-url | Ссылка на выгрузку Google Sheets | base

Напишите функцию `sheet_csv_url(link)`: она получает обычную ссылку на Google Таблицу и возвращает адрес выгрузки в CSV вида `https://docs.google.com/spreadsheets/d/<id>/export?format=csv&gid=<gid>`.

- `<id>` — часть ссылки между `/d/` и следующим `/`;
- `<gid>` — номер листа: то, что стоит после **последнего** `gid=` в ссылке. Если `gid=` в ссылке нет, лист первый — `0`.

Примеры: ссылка `https://docs.google.com/spreadsheets/d/1Xy_menu/edit?gid=418#gid=418` → `https://docs.google.com/spreadsheets/d/1Xy_menu/export?format=csv&gid=418`.

### starter
```python
def sheet_csv_url(link):
    ...

print(sheet_csv_url("https://docs.google.com/spreadsheets/d/1AbC-zerno_Plan2026/edit#gid=0"))
```

### check
```python
f = need('sheet_csv_url')
assert callable(f), 'sheet_csv_url должна быть функцией.'
_base = 'https://docs.google.com/spreadsheets/d/'
for _link, _id, _gid in [
    (_base + '1AbC-zerno_Plan2026/edit#gid=0', '1AbC-zerno_Plan2026', '0'),
    (_base + '1Xy_menu/edit?gid=418#gid=418', '1Xy_menu', '418'),
    (_base + '1Qq_shops/edit', '1Qq_shops', '0'),
    (_base + '9Zz-staff/edit?usp=sharing#gid=77', '9Zz-staff', '77'),
]:
    _got = f(_link)
    _want = f'{_base}{_id}/export?format=csv&gid={_gid}'
    assert _got is not None, 'Функция ничего не возвращает — нужен return.'
    assert _got == _want, f'Для ссылки {_link}\nфункция вернула {_got!r},\nа нужно       {_want!r}.'
```

### hint
Обе части достаются через `split`: идентификатор — между `"/d/"` и `"/"`, номер листа — после `"gid="`. «После последнего» — значит, берём последний кусок: индекс `[-1]`.

### hint
`sheet_id = link.split("/d/")[1].split("/")[0]`. Для листа: если `"gid=" in link`, то `gid = link.split("gid=")[-1]`, иначе `gid = "0"`.

### hint
```python
def sheet_csv_url(link):
    sheet_id = link.split("/d/")[1].split("/")[0]
    gid = link.split("gid=")[-1] if "gid=" in link else ...
    return f"https://docs.google.com/spreadsheets/d/{...}/export?format=csv&gid={...}"
```

### solution
```python
def sheet_csv_url(link):
    sheet_id = link.split("/d/")[1].split("/")[0]
    gid = link.split("gid=")[-1] if "gid=" in link else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

print(sheet_csv_url("https://docs.google.com/spreadsheets/d/1AbC-zerno_Plan2026/edit#gid=0"))
```

### explain
Ссылки на одну и ту же таблицу бывают разными: с `#gid=`, с `?gid=…#gid=…`, с хвостом `?usp=sharing` или совсем без номера листа. Если брать **первый** кусок после `gid=`, для `edit?gid=418#gid=418` получится `'418#'` — и выгрузка сломается. `[-1]` берёт последний кусок, и в таких ссылках это чистый номер. (Бывают и ссылки с хвостом после номера, например `#gid=418&range=A1`, — тогда номер пришлось бы ещё отрезать по `&`.) Дальше такой адрес передают в `pd.read_csv(sheet_csv_url(link))` — в своём Jupyter, где есть интернет.

## task: records | Из списка словарей: пропуск | plus

Заказы пришли из API списком словарей. В одном заказе суммы нет вовсе — ключа `amount` в словаре не хватает. Соберите DataFrame `t` из `orders` и посчитайте:

- `n_no_amount` — сколько заказов без суммы;
- `total` — выручку по заказам с суммой;
- `avg_check` — средний чек по заказам **с суммой** (без округления).

### starter
```python
import pandas as pd
orders = [
    {"city": "Пермь", "drink": "Латте", "amount": 450},
    {"city": "Казань", "drink": "Раф"},
    {"city": "Пермь", "drink": "Раф", "amount": 610},
    {"city": "Уфа", "drink": "Мокко", "amount": 480},
    {"city": "Казань", "drink": "Латте", "amount": 320},
]

```

### check
```python
import pandas as _pd
assert isinstance(need('t'), _pd.DataFrame), f'В t лежит {type(need("t")).__name__}, а нужен DataFrame: pd.DataFrame(orders).'
assert len(need('t')) == 5, f'В t {len(need("t"))} строк, а заказов 5.'
assert need('n_no_amount') == 1, f'n_no_amount = {need("n_no_amount")}. Посмотрите на t: у заказа без ключа amount в ячейке NaN. Посчитайте такие ячейки.'
assert close(need('total'), 1860), f'total = {need("total")}, а нужно 1860.'
_a = need('avg_check')
assert not close(_a, 372), f'avg_check = {_a} — это 1860 / 5: заказ без суммы попал в знаменатель. Средний чек считают только по заказам с суммой.'
assert close(_a, 465), f'avg_check = {_a}, а нужно 465.'
assert not has_literal(1860) and not has_literal(465), 'Посчитайте числа методами столбца, а не вписывайте их.'
```

### hint
`pd.DataFrame(orders)` сам сделает столбцы из ключей. Где ключа нет, pandas поставит пустое значение — `NaN` (раздел «Пустые значения»).

### hint
Пустые — `t["amount"].isna().sum()`. А `sum()` и `mean()` пропуски пропускают сами: среднее считается по непустым значениям.

### hint
```python
t = pd.DataFrame(orders)
n_no_amount = t["amount"].isna()....
total = t["amount"]....
avg_check = t["amount"]....
```

### solution
```python
import pandas as pd
orders = [
    {"city": "Пермь", "drink": "Латте", "amount": 450},
    {"city": "Казань", "drink": "Раф"},
    {"city": "Пермь", "drink": "Раф", "amount": 610},
    {"city": "Уфа", "drink": "Мокко", "amount": 480},
    {"city": "Казань", "drink": "Латте", "amount": 320},
]
t = pd.DataFrame(orders)
n_no_amount = t["amount"].isna().sum()
total = t["amount"].sum()
avg_check = t["amount"].mean()
```

### explain
Список словарей — частый формат данных из API и JSON. `pd.DataFrame(orders)` делает столбцы из ключей, а там, где ключа не хватает, ставит `NaN`. Из-за этого `amount` стал дробным (`450.0`): `NaN` — дробное «число», и целым столбец быть уже не может. Выручка — 1 860, средний чек — 465: `mean()` делит на 4 заказа с суммой, а не на 5. Если посчитать `t["amount"].sum() / len(t)`, получится 372 — заказ без суммы молча занизит чек. Это та же разница, что между `count()` и `len()`.

## task: loyalty | Доля заказов по карте | star

Посчитайте `loyalty_share` — долю заказов, сделанных по карте лояльности, в процентах с одним знаком, и `orders_per_client` — сколько в среднем заказов приходится на одного гостя с картой (с одним знаком).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
c = _pd.read_csv('orders_3m.csv')['client_id']
assert close(need('loyalty_share'), round(c.notna().mean() * 100, 1)), f'loyalty_share = {need("loyalty_share")}.'
assert close(need('orders_per_client'), round(c.count() / c.nunique(), 1)), f'orders_per_client = {need("orders_per_client")}, а нужно {round(c.count() / c.nunique(), 1)}.'
```

### hint
Доля — `notna().mean()`. Заказы с картой — `count()` (непустые), гостей — `nunique()`.

### hint
Заказов на гостя — деление: `df["client_id"].count() / df["client_id"].nunique()`; округление — в конце.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
loyalty_share = round(df["client_id"].notna().mean() * 100, 1)
orders_per_client = round(df["client_id"].count() / df["client_id"].nunique(), 1)
```

### explain
У заказов без карты `client_id` пустой, поэтому `notna()` даёт True/False, а среднее от них — долю заказов с картой: 59.7 %. Для второго числа нужны два разных счётчика: `count()` — сколько заказов с непустым номером карты (1247), `nunique()` — сколько разных карт (260). Их отношение, 4.8 заказа на гостя, — это частота визитов участника программы за три месяца. В SQL это `COUNT(client_id) / COUNT(DISTINCT client_id)`.
