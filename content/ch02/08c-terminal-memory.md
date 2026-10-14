---
title: "Терминал и память: заглянуть в файл, не открывая его"
lead: "Выгрузка на 2 ГБ не открывается в Excel и долго грузится в pandas. Заглядываем в неё из терминала — первые строки, число строк, поиск по тексту — и учимся видеть, сколько памяти занимает таблица и как её уменьшить."
files: [orders_3m.csv, shops.csv, menu.csv]
recap:
  - "Терминал: `head -3 файл`, `wc -l файл` (строк вместе с заголовком), `grep -c текст файл`; в ячейке — с `!` впереди. Экспорт: `jupyter nbconvert --to html блокнот.ipynb`."
  - "Память: `df.memory_usage(deep=True)`; текст с немногими значениями → `astype(\"category\")`; `del df` или перезапуск ядра освобождают память."
---

## Терминал за 20 минут

Зачем: прислали выгрузку на 2 ГБ. Excel её не откроет, а `pd.read_csv` будет читать минуту и съест память. Терминал за секунду покажет первые строки, число строк и найдёт нужное.

::: tip Аналогия
Терминал — как разговор с компьютером короткими приказами вместо кликов по папкам. Каждая команда — глагол («покажи», «посчитай», «найди») плюс то, с чем работать. Приказы компьютер понимает буквально: опечатка в имени файла даёт ошибку, а не догадку.
:::

На Mac — приложение **Терминал**. На Windows команд `head`, `wc` и `grep` в обычном PowerShell нет; их даёт **Git Bash**. Он ставится вместе с Git for Windows: установщик — на сайте git-scm.com, или одной командой в PowerShell `winget install Git.Git`. После установки Git Bash появится в меню «Пуск». Тот же git понадобится в уроке «Git: коммиты, история, ветки и .gitignore», так что ставить его стоит в любом случае.

::: deep Windows без Git Bash
Если ставить Git Bash не хочется, у PowerShell есть свои аналоги: `Get-Content файл -Head 3 -Encoding UTF8` вместо `head -3`, `(Get-Content файл | Measure-Object -Line).Lines` вместо `wc -l`, `(Select-String "доставка" файл).Count` вместо `grep -c`.
:::

| команда | что делает |
|---|---|
| `pwd` | где я: текущая папка |
| `ls`, `ls -l` | что в папке; `-l` — с размерами в байтах |
| `cd data` | перейти в папку `data` (`cd ..` — на уровень выше) |
| `head -3 файл` | первые 3 строки |
| `wc -l файл` | число строк |
| `grep текст файл` | строки, где есть текст; `-c` — только их число, `-i` — без учёта регистра |
| `команда1 \| команда2` | передать вывод первой команды на вход второй |

Посмотрим на данные курса:

```sh
$ head -3 data/orders_3m.csv
order_id,datetime,shop_id,drink,size,qty,amount,client_id,channel
O-00001,2026-09-01 10:31,PRM-1,Капучино,S,2,380,C1237,зал
O-00002,2026-09-01 13:34,PRM-1,Чай,S,2,240,C1074,с собой

$ wc -l data/orders_3m.csv
2090 data/orders_3m.csv

$ grep -c "доставка" data/orders_3m.csv
380

$ grep "Сезонный" data/orders_3m.csv | grep -c "доставка"
11
```

Игрушечный пример, как читать `wc -l`: в файле строка заголовка и 2 089 заказов — всего 2 090 строк. Значит, заказов — `2090 − 1`. Последняя команда сначала отбирает строки с «Сезонный», а потом среди них считает доставку: из 380 доставок 11 — с сезонным напитком.

::: figure shell-pipe
Цепочка из двух `grep`: первый оставляет 82 строки с сезонным напитком, `|` передаёт их второму, и тот считает среди них строки с доставкой. Каждая команда делает одно простое дело, а `|` собирает из них цепочку.
:::

В ячейке Jupyter любую команду терминала можно выполнить с `!` впереди: `!head -3 data/orders_3m.csv`. Ответ появится под ячейкой.

В браузере курса терминала нет, но каждая из этих команд — пара строк на Python:

```python
with open("orders_3m.csv", encoding="utf-8") as f:
    lines = f.read().splitlines()          # весь файл — список строк

print(lines[:3])                           # head -3
print(len(lines))                          # wc -l
print(sum("доставка" in l for l in lines)) # grep -c "доставка"
print(sum("доставка" in l for l in lines if "Сезонный" in l))   # grep … | grep -c …
```

Что здесь происходит:

- `f.read().splitlines()` читает файл целиком и режет на строки; концы строк отбрасываются;
- `lines[:3]` — первые три строки, как `head -3`;
- `sum("доставка" in l for l in lines)` — `True` считается как 1, поэтому сумма — число строк, где встречается слово. Это ровно `grep -c`: строки, а не вхождения;
- последний `sum` с условием `if "Сезонный" in l` повторяет цепочку из двух `grep`.

::: predict
```python static
n = sum(1 for _ in open("orders_3m.csv", encoding="utf-8"))
print(n)
```

- `2089`
- [x] `2090`
- `9`

Почему: файл читается построчно, а первая строка — заголовок со списком столбцов. 2 089 заказов + 1 заголовок = 2 090 — столько же покажет `wc -l`.
:::

### Экспорт блокнота — тоже команда терминала

Руководителю не нужен `.ipynb`: ему нужна страница, которая открывается в браузере. Её делает **nbconvert**, который приходит вместе с Jupyter:

```sh
uv run jupyter nbconvert --to html report.ipynb                     # report.html рядом
uv run jupyter nbconvert --to html --execute report.ipynb           # сначала выполнить с чистого ядра
uv run jupyter nbconvert --to html --no-input report.ipynb          # без кода — только текст, таблицы, графики
uv run jupyter nbconvert --to script report.ipynb                   # код в report.py
```

`--execute` — заодно проверка воспроизводимости: если блокнот падает с чистого ядра, HTML не соберётся. То же есть в меню: **File → Save and Export Notebook As → HTML**.

::: warn Типичные ошибки
- **«В файле 2 090 заказов».** `wc -l` считает и заголовок.
- **`grep -c` считает строки, а не слова.** Если слово дважды в одной строке, это всё равно 1.
- **`grep "доставка"` не нашёл «Доставка».** `grep` различает регистр; без учёта регистра — `grep -i`.
- **`!cd data` в ячейке «не сработал».** Каждая `!`-команда идёт в отдельном процессе, и переход в папку забывается. Для смены папки в Jupyter есть `%cd data` — но лучше вовсе не менять папку, а писать относительные пути.
- **Экспорт без `--execute` блокнота, который запускали вразнобой.** В HTML уйдут старые выводы — ровно те, что были в файле.
:::

::: note Сделайте в своём терминале
1. Перейдите в папку проекта (`cd ~/projects/zerno-analytics`) и выполните `pwd` и `ls -l data`.
2. Выполните `head`, `wc -l` и `grep -c` из примера. Совпадают ли числа с теми, что в уроке?
3. В блокноте выполните `!wc -l data/orders_3m.csv`.
4. Экспортируйте свой блокнот: `uv run jupyter nbconvert --to html --execute ваш-блокнот.ipynb` — и откройте HTML в браузере.
:::

{{practice: w-lines, grep-count, ls-parse}}

## Память: сколько весит таблица

Зачем: на выгрузке в десятки миллионов строк Jupyter однажды пишет «Kernel died» — ядро упало, потому что кончилась оперативная память. Чтобы этого не случилось, полезно знать, сколько весит таблица и как сделать её легче.

`df.memory_usage(deep=True)` показывает вес каждого столбца в байтах. `deep=True` важен: без него pandas не заглядывает внутрь текстовых значений и сильно занижает их вес.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
mem = df.memory_usage(deep=True)
print(mem.sort_values(ascending=False).head(5))
print("всего, КБ:", round(mem.sum() / 1024))
```

Как читать: тяжелее всего текстовые столбцы — `drink`, `channel`, `datetime`. Числовые `qty` и `amount` весят по 8 байт на строку.

**Категориальный тип.** В столбце `channel` 2 089 строк, но всего 3 разных значения. Хранить каждую строку текстом — расточительно.

::: tip Аналогия
Категория — как справочник в базе данных. Вместо того чтобы в каждой строке заказа писать «доставка», в таблице лежит короткий код 0, 1 или 2, а расшифровка кодов хранится один раз. Это то же самое, что вынести названия в отдельную таблицу и соединять по ключу. Только «справочник» pandas прячет — вы по-прежнему видите и фильтруете текст.
:::

Игрушечный пример: 5 заказов с каналами «зал, зал, доставка, с собой, зал».

1. Справочник: `["доставка", "зал", "с собой"]` — три строки, по алфавиту.
2. Коды заказов: `1, 1, 0, 2, 1` — номер в справочнике, по одному байту на заказ.
3. При 2 089 заказах справочник по-прежнему из трёх строк, а кодов — 2 089 байт.

::: figure category-codes
Игрушечный пример: пять заказов. Слева текст в каждой строке, после `astype("category")` — короткий код в каждой строке и справочник из трёх значений, записанный один раз. Код 1 означает «зал».
:::

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

ch = df["channel"].astype("category")
print(ch.cat.categories.tolist())        # справочник
print(ch.cat.codes.head(5).tolist())     # коды первых заказов
print(df["channel"].memory_usage(deep=True), "→", ch.memory_usage(deep=True), "байт")
```

Что здесь происходит:

- `astype("category")` строит справочник уникальных значений и заменяет текст кодами;
- `.cat.categories` — справочник, `.cat.codes` — коды строк;
- `memory_usage(deep=True)` у Series — вес столбца вместе с индексом.

Как читать результат: столбец похудел в десятки раз. Фильтры (`ch == "доставка"`), `groupby` и `value_counts` работают как раньше. Числа в браузере курса и в вашем Jupyter будут разными — способ хранения строк зависит от версии pandas и установленных библиотек, — но выигрыш того же порядка.

Когда категория **не** помогает: если почти все значения разные. У `order_id` 2 089 уникальных значений на 2 089 строк, и справочник выйдет таким же, как сам столбец, да ещё с кодами сверху. Правило: категория выгодна, когда уникальных значений мало относительно числа строк.

**Освободить память.** `del df` удаляет имя, и, если таблица больше нигде не нужна, Python освобождает её память. `%whos` в Jupyter покажет, какие большие объекты ещё живут в ядре. Самый надёжный способ — перезапустить ядро: память очищается целиком, а блокнот, который проходит Restart & Run All, ничего при этом не теряет.

::: quiz
В каком столбце заказов перевод в `category` **не** сэкономит память?

- [x] `order_id` — номер заказа
  > Все 2 089 значений разные: справочник получится размером со столбец, и к нему ещё добавятся коды. Столбец станет тяжелее.
- [ ] `channel` — канал продажи
  > Три значения на 2 089 строк — идеальный кандидат: вес падает в десятки раз.
- [ ] `size` — размер стакана
  > Три значения S, M, L — категория экономит почти всю память столбца.
- [ ] `shop_id` — код кофейни
  > Шесть кофеен на все заказы — категория сильно экономит.
:::

::: warn Типичные ошибки
- **`memory_usage()` без `deep=True`.** Для текстовых столбцов это заниженная оценка.
- **`del df`, а память не освободилась.** На ту же таблицу ссылается другое имя (`orders = df`) или вывод ячейки. Перезапуск ядра решает всё.
- **Категория для уникальных значений.** Номера заказов, телефоны, тексты отзывов — категория только утяжелит.
- **Новое значение в категориальный столбец.** Присвоить значение, которого нет в справочнике, нельзя — сначала `cat.add_categories`, или верните тип `str`.
:::

::: note Сделайте в своём блокноте
1. Выполните `df.info(memory_usage="deep")` — внизу будет общий вес таблицы.
2. Переведите `shop_id`, `drink`, `size`, `channel` в `category` и сравните вес до и после.
3. Выполните `%whos`, затем `del df` и снова `%whos`.
:::

{{practice: cat-codes, mem-category}}

## Практика

## task: w-lines | wc -l на Python | warmup

Посчитайте, сколько строк в трёх файлах урока — так, как это сделал бы `wc -l`. Сохраните словарь `lines` вида `{"orders_3m.csv": …, "shops.csv": …, "menu.csv": …}` и два числа: `n_orders` — сколько заказов и `n_shops` — сколько кофеен (без строк-заголовков).

### starter
```python
files = ["orders_3m.csv", "shops.csv", "menu.csv"]

```

### check
```python
want = {f: sum(1 for _ in open(f, encoding='utf-8')) for f in ('orders_3m.csv', 'shops.csv', 'menu.csv')}
got = need('lines', dict)
assert got == want, f'lines = {got}, а wc -l даёт {want}. Считайте все строки файла, вместе с заголовком.'
assert need('n_orders') == want['orders_3m.csv'] - 1, f'n_orders = {need("n_orders")}. Первая строка файла — заголовок, это не заказ.'
assert need('n_shops') == want['shops.csv'] - 1, f'n_shops = {need("n_shops")}. Вычтите строку заголовка.'
assert not has_literal(2090) and not has_literal(2089), 'Не вписывайте числа руками — посчитайте строки кодом.'
```

### hint
Число строк файла: `sum(1 for _ in open(имя, encoding="utf-8"))` или `len(open(имя, encoding="utf-8").read().splitlines())`.

### hint
Словарь собирается одной строкой: `lines = {f: … for f in files}`; заказов — `lines["orders_3m.csv"] - 1`.

### solution
```python
files = ["orders_3m.csv", "shops.csv", "menu.csv"]
lines = {f: sum(1 for _ in open(f, encoding="utf-8")) for f in files}
n_orders = lines["orders_3m.csv"] - 1
n_shops = lines["shops.csv"] - 1
print(lines, n_orders, n_shops)
```

## task: grep-count | head и grep на Python | base

Повторите на Python три команды терминала для `orders_3m.csv`:

- `head3` — `head -3`: список первых трёх строк файла (без символов конца строки);
- `n_delivery` — `grep -c "доставка"`: сколько строк содержат слово «доставка»;
- `n_seasonal_delivery` — `grep "Сезонный" | grep -c "доставка"`: сколько строк содержат оба слова.

### starter
```python
with open("orders_3m.csv", encoding="utf-8") as f:
    lines = f.read().splitlines()

```

### check
```python
L = open('orders_3m.csv', encoding='utf-8').read().splitlines()
assert need('head3', list) == L[:3], f'head3 = {need("head3")}. Нужны первые три строки, включая заголовок.'
assert need('n_delivery') == sum('доставка' in l for l in L), f'n_delivery = {need("n_delivery")}. Считайте строки, в которых есть слово.'
assert need('n_seasonal_delivery') == sum('доставка' in l for l in L if 'Сезонный' in l), f'n_seasonal_delivery = {need("n_seasonal_delivery")}. Отберите строки с «Сезонный», а среди них посчитайте «доставку».'
```

### hint
`head -3` — это срез `lines[:3]`.

### hint
`grep -c` — `sum("доставка" in l for l in lines)`: `True` считается как 1.

### hint
Цепочка из двух `grep` — условие в генераторе: `sum("доставка" in l for l in lines if "Сезонный" in l)`.

### solution
```python
with open("orders_3m.csv", encoding="utf-8") as f:
    lines = f.read().splitlines()

head3 = lines[:3]
n_delivery = sum("доставка" in l for l in lines)
n_seasonal_delivery = sum("доставка" in l for l in lines if "Сезонный" in l)
print(n_delivery, n_seasonal_delivery)
```

### explain
380 строк с доставкой — столько же, сколько заказов с `channel == "доставка"` в pandas: слово «доставка» встречается только в этом столбце. Но так бывает не всегда: `grep` ищет текст во всей строке, и, если бы в меню был напиток «Доставка дня», он попал бы в счёт. Поэтому `grep` — для быстрой разведки, а точные числа для отчёта — через pandas по нужному столбцу.

## task: ls-parse | Что занимает место | star

Коллега прислал вывод `ls -l data` из своего терминала. Разберите его на Python: `sizes` — словарь «имя файла → размер в байтах», `biggest` — имя самого большого файла, `total_kb` — общий размер в килобайтах (байты / 1024, округлить до целого). Строку `total …` в начале пропустите — это не файл.

### starter
```python
listing = """total 1076
-rw-r--r--  1 anya  staff  257933 Nov 20 09:15 daily_sales.csv
-rw-r--r--  1 anya  staff     379 Nov 20 09:15 menu.csv
-rw-r--r--  1 anya  staff  144308 Nov 20 09:15 orders_3m.csv
-rw-r--r--  1 anya  staff   11646 Nov 20 09:15 reviews.csv
-rw-r--r--  1 anya  staff  673576 Nov 20 09:15 service_log.jsonl
-rw-r--r--  1 anya  staff     387 Nov 20 09:15 shops.csv"""

```

### check
```python
L = [l.split() for l in need('listing').splitlines()[1:]]
w = {p[-1]: int(p[4]) for p in L}
s = need('sizes', dict)
assert set(s) == set(w), f'В sizes файлы {sorted(s)}, а нужны {sorted(w)}. Строка total — не файл.'
assert {k: int(v) for k, v in s.items()} == w, 'Размеры не совпадают: размер — пятое поле строки (индекс 4), число байт.'
assert need('biggest') == max(w, key=w.get), f'biggest = {need("biggest")!r}.'
assert need('total_kb') == round(sum(w.values()) / 1024), f'total_kb = {need("total_kb")}. Сумма байт / 1024, округлить.'
```

### hint
Разбейте текст на строки (`splitlines()`), пропустите первую, а каждую строку — на поля через `split()`: пробелы любой длины считаются одним разделителем.

### hint
В строке `ls -l` размер — поле с индексом 4, имя — последнее поле: `parts[4]`, `parts[-1]`.

### hint
`biggest = max(sizes, key=sizes.get)`; `total_kb = round(sum(sizes.values()) / 1024)`.

### solution
```python
listing = """total 1076
-rw-r--r--  1 anya  staff  257933 Nov 20 09:15 daily_sales.csv
-rw-r--r--  1 anya  staff     379 Nov 20 09:15 menu.csv
-rw-r--r--  1 anya  staff  144308 Nov 20 09:15 orders_3m.csv
-rw-r--r--  1 anya  staff   11646 Nov 20 09:15 reviews.csv
-rw-r--r--  1 anya  staff  673576 Nov 20 09:15 service_log.jsonl
-rw-r--r--  1 anya  staff     387 Nov 20 09:15 shops.csv"""

sizes = {}
for line in listing.splitlines()[1:]:
    parts = line.split()
    sizes[parts[-1]] = int(parts[4])

biggest = max(sizes, key=sizes.get)
total_kb = round(sum(sizes.values()) / 1024)
print(biggest, total_kb)
```

### explain
Больше всего весит журнал `service_log.jsonl` — 658 КБ из 1 063. Разбор такого вывода — частая мини-задача: «что съело диск», «какие выгрузки не пришли». `split()` без аргументов здесь ключевой: столбцы `ls -l` выровнены пробелами разной длины, и `split(" ")` дал бы кучу пустых строк. Ловушка — имя файла с пробелом (`daily sales.csv`): тогда `parts[-1]` вернёт только последнее слово. Надёжнее `line.split(maxsplit=8)[-1]` — первые 8 полей отрезаются, а остаток строки целиком становится именем.

## task: cat-codes | Справочник и коды | warmup

Переведите размеры стаканов из списка `sizes` в категорию и сохраните `cats` — справочник категорий списком, и `codes` — коды всех шести заказов списком целых чисел.

### starter
```python
import pandas as pd
sizes = pd.Series(["M", "S", "M", "L", "M", "S"])

```

### check
```python
assert [str(x) for x in need('cats')] == ['L', 'M', 'S'], f'cats = {list(need("cats"))}. Справочник — .cat.categories, значения в нём по алфавиту.'
assert [int(x) for x in need('codes')] == [1, 2, 1, 0, 1, 2], f'codes = {[int(x) for x in need("codes")]}. Код — номер значения в справочнике, с нуля: .cat.codes.'
```

### hint
Сначала `sizes.astype("category")`, затем у результата — `.cat.categories` и `.cat.codes`, оба через `.tolist()`.

### hint
```python
c = sizes.astype("category")
cats = c.cat.categories.tolist()
codes = c.cat.codes.tolist()
```

### solution
```python
import pandas as pd
sizes = pd.Series(["M", "S", "M", "L", "M", "S"])
c = sizes.astype("category")
cats = c.cat.categories.tolist()
codes = c.cat.codes.tolist()
```

### explain
Справочник — три значения по алфавиту: L — код 0, M — 1, S — 2. Шесть заказов хранятся шестью маленькими кодами, а буквы записаны один раз. Порядок по алфавиту здесь не совпадает с порядком размеров (S < M < L) — для группировок это неважно, а если нужен «правильный» порядок, его задают `pd.Categorical(..., categories=["S", "M", "L"], ordered=True)`.

## task: mem-category | Таблица на диете | plus

Напишите `shrink(df)` — функцию, которая возвращает **копию** таблицы, где каждый текстовый столбец (`dtype` равен `str`; в pandas 2 — `object`) с долей уникальных значений меньше 5 % (`nunique() / len(df) < 0.05`) переведён в `category`. Остальные столбцы не трогайте. Примените её к заказам: результат — `small`, список переведённых столбцов — `converted` (в порядке столбцов таблицы), экономию памяти в процентах (`deep=True`, 1 знак) — `saved_pct`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

def shrink(df):
    ...

small = shrink(df)
```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
txt = [c for c in d.columns if not _pd.api.types.is_numeric_dtype(d[c])]
want_cols = [c for c in txt if d[c].nunique() / len(d) < 0.05]
sm = need('small', _pd.DataFrame)
assert need('converted', list) == want_cols, f'converted = {need("converted")}, а по правилу < 5 % уникальных выходит {want_cols}.'
for c in d.columns:
    is_cat = isinstance(sm[c].dtype, _pd.CategoricalDtype)
    assert is_cat == (c in want_cols), f'Столбец {c}: {"переведён" if is_cat else "не переведён"} в category, а должен {"" if c in want_cols else "не "}быть.'
assert len(sm) == len(d) and (sm['amount'] == d['amount']).all(), 'Данные в small должны остаться прежними — меняется только тип.'
dd = need('df', _pd.DataFrame)
assert not any(isinstance(dd[c].dtype, _pd.CategoricalDtype) for c in dd.columns), 'Исходная df изменилась: shrink должна работать с копией (df.copy()).'
before, after = d.memory_usage(deep=True).sum(), sm.memory_usage(deep=True).sum()
assert close(need('saved_pct'), round((before - after) / before * 100, 1), 0.051), f'saved_pct = {need("saved_pct")}, а нужно {round((before - after) / before * 100, 1)}.'
```

### hint
Сначала `out = df.copy()`, затем цикл по столбцам. Текстовый столбец — тот, что не числовой: `not pd.api.types.is_numeric_dtype(out[c])`.

### hint
Условие перевода: `out[c].nunique() / len(out) < 0.05`, перевод — `out[c] = out[c].astype("category")`. Список переведённых столбцов удобно собирать прямо в этом цикле.

### hint
Экономия: `before = df.memory_usage(deep=True).sum()`, `after = small.memory_usage(deep=True).sum()`, `saved_pct = round((before - after) / before * 100, 1)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

def shrink(df):
    out = df.copy()
    for c in out.columns:
        if not pd.api.types.is_numeric_dtype(out[c]) and out[c].nunique() / len(out) < 0.05:
            out[c] = out[c].astype("category")
    return out

small = shrink(df)
converted = [c for c in small.columns if isinstance(small[c].dtype, pd.CategoricalDtype)]
before = df.memory_usage(deep=True).sum()
after = small.memory_usage(deep=True).sum()
saved_pct = round((before - after) / before * 100, 1)
print(converted, saved_pct)
```

### explain
В категорию ушли `shop_id`, `drink`, `size` и `channel`: у них от 3 до 11 значений на 2 089 строк. `client_id` (260 гостей — 12 %), `datetime` и `order_id` остались текстом — для них справочник почти не короче самого столбца. Таблица похудела больше чем вдвое: экономия — около 60 % (точное число зависит от версии pandas). Порог 5 % — рабочее правило, а не закон: на таблице в миллионы строк категория выгодна и при тысячах значений. Если забыть `df.copy()`, функция испортит исходную таблицу — и это заметно только позже, когда к столбцу добавится новое значение.
