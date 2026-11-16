---
title: "Файлы, CSV и модули"
lead: "Подключаем готовые модули стандартной библиотеки, читаем и пишем файлы, разбираем CSV-выгрузку заказов сети «Зерно». После этого урока данные больше не нужно вписывать в код руками."
files: [orders.csv, menu.txt]
recap:
  - "`import math`, `from statistics import median`, `import datetime as dt` — подключить модуль целиком, одно имя или под коротким именем."
  - "Файл открывают через `with open(\"файл\", encoding=\"utf-8\") as f:` — после блока `with` он закрывается сам."
  - "`for line in f:` — читать построчно (не забывайте `strip()`); режим `\"w\"` — записать, файл при этом перезаписывается."
  - "`csv.DictReader(f)` — каждая строка CSV становится словарём «столбец → значение». Все значения — строки: числа превращайте сами."
  - "`dt.date.fromisoformat(\"2026-09-15\")` — дата из текста; `.weekday()` — день недели (0 — понедельник)."
---

## Модули: готовый код из коробки

Python поставляется с большой **стандартной библиотекой** — набором модулей для математики, дат, файлов, CSV и многого другого. Чтобы использовать модуль, его подключают командой `import`:

```python
import math
print(math.sqrt(16))
print(math.ceil(2.1), math.floor(2.9))
```

Обращение идёт через точку: `math.sqrt` — функция `sqrt` из модуля `math`. Если нужна одна-две функции, их можно подключить по имени — тогда точка не нужна:

```python
from statistics import mean, median
revenue = [41200, 38900, 45100, 39800, 52300, 61700, 58400]
print(round(mean(revenue)), median(revenue))
```

::: predict
```python static
import math
print(math.ceil(2.1))
```

- `2`
- [x] `3`
- `2.1`

Почему: `ceil` — округление вверх до целого («потолок»). Вниз округляет `floor`.
:::


Длинное имя модуля можно сократить через `as` — так принято для pandas (`import pandas as pd`), и вы увидите это во второй главе:

```python
import datetime as dt
d = dt.date(2026, 9, 15)
print(d, d.weekday())
```

::: predict
```python static
from statistics import median
print(median([1, 9, 3]))
```

- `4.33`
- [x] `3`
- `9`

Почему: медиана — значение посередине после сортировки: [1, 3, 9] → 3. Это не среднее (оно было бы 4.33).
:::

::: tip
Импорты принято писать в самом начале программы, по одному на строку.
:::

{{practice: mean}}

## Чтение текстового файла

Рядом с уроком лежит файл `menu.txt` — меню, по позиции на строку. Прочитаем его:

```python
with open("menu.txt", encoding="utf-8") as f:
    for line in f:
        print(repr(line))  # repr показывает строку как она записана в коде — с кавычками и \n
```

Разберём:

- `open("menu.txt", encoding="utf-8")` открывает файл. Кодировку указывайте всегда, иначе на разных компьютерах русские буквы могут прочитаться по-разному;
- `with … as f:` — файл доступен как `f` внутри блока и сам закроется, когда блок кончится;
- `for line in f:` идёт по строкам файла.

`repr` показал правду: в конце каждой строки есть невидимый символ перевода строки `\n`, а в конце файла — пустая строка. Поэтому строки почти всегда чистят через `strip()` и пропускают пустые:

```python
menu = []
with open("menu.txt", encoding="utf-8") as f:
    for line in f:
        name = line.strip()
        if name:
            menu.append(name)
print(menu)
```

::: figure file-lines
Что происходит с каждой строкой `menu.txt`: в конце — перевод строки `\n`, `strip()` его убирает, пустую строку `if name:` пропускает.
:::

`if name:` — короткая проверка «строка не пустая»: пустая строка считается ложью.

{{practice: menu}}

## Запись в файл

Режим `"w"` (*write*) открывает файл для записи. Если файл существовал, он **перезаписывается** целиком:

```python
with open("report.txt", "w", encoding="utf-8") as f:
    f.write("Отчёт за сентябрь\n")
    f.write("Выручка: 16 820 ₽\n")

with open("report.txt", encoding="utf-8") as f:
    print(f.read())
```

`write` не добавляет перевод строки сам — `\n` пишем явно. `f.read()` читает весь файл одной строкой.

::: note
В курсе файлы живут в браузере, внутри Python этой страницы: созданный файл исчезнет, когда вы закроете вкладку. Когда будете работать на своём компьютере (глава 2), файл появится в рабочей папке проекта.
:::

## CSV: таблица в текстовом файле

CSV (*comma-separated values*) хранит таблицу в тексте. Поля разделены запятыми. Если поле содержит запятую или перевод строки, его заключают в кавычки. Поэтому одна запись может занимать несколько строк файла. Посмотрим на начало `orders.csv` — заказы сети за сентябрь:

```python
with open("orders.csv", encoding="utf-8") as f:
    for i, line in enumerate(f):
        print(line.strip())
        if i == 4:
            break
```

Резать строки через `split(",")` руками опасно: в CSV значение может само содержать запятую в кавычках. Для чтения есть модуль `csv`. Удобнее всего `DictReader`: он берёт названия столбцов из первой строки и превращает каждую следующую строку в словарь:

```python
import csv

with open("orders.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(len(rows))
print(rows[0])
print(rows[0]["city"], rows[0]["amount"])
```

::: warn
Все значения из CSV — **строки**, даже `"260"`. Перед расчётами превращайте их в числа: `int(row["amount"])`. А в выгрузке, как в жизни, бывает мусор — тут пригодится урок про исключения.
:::

::: sql
`list(csv.DictReader(f))` — это `SELECT * FROM orders`: вся таблица в памяти, строка — словарь «столбец → значение». Дальше фильтры, группировки и суммы вы уже умеете делать циклами и словарями. Во второй главе то же самое будет одной строкой pandas: `pd.read_csv("orders.csv")`.
:::

Записать CSV — `csv.writer`:

```python
import csv

with open("by_city.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["city", "revenue"])
    w.writerow(["Пермь", 1450])
    w.writerow(["Казань", 600])

print(open("by_city.csv", encoding="utf-8").read())
```

`newline=""` оставляет обработку переводов строк модулю `csv`. Это пригодится и при чтении полей с переносами, и при записи файла в Windows.

{{practice: write}}

### Разберём вместе: одна строка CSV — один словарь

Файл `orders.csv` начинается так:

```text
order_id,date,city,drink,amount
Z-1006,2026-09-03,Пермь,Раф,260
```

Что делает `csv.DictReader` с этими двумя строками:

1. Первая строка — **заголовок**: имена ключей `order_id`, `date`, `city`, `drink`, `amount`. Строкой данных она не считается.
2. Вторая строка режется по запятым и превращается в словарь: `{"order_id": "Z-1006", "date": "2026-09-03", "city": "Пермь", "drink": "Раф", "amount": "260"}`.
3. Все значения — **строки**, даже `"260"`. Чтобы считать, нужен `int(row["amount"])`.

::: figure csv-dictreader
Заголовок CSV становится ключами словаря, строка данных — значениями. Все значения — текст, поэтому сумму сначала превращают в число.
:::

```python
import csv
with open("orders.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    first = next(reader)    # next — взять одну следующую строку, не читая весь файл
print(first)
print(type(first["amount"]), int(first["amount"]) + 100)
```

`next(reader)` вернул первый словарь. Следующий вызов внутри `with` прочитает следующую запись. Чтобы собрать всю таблицу в список, можно сразу написать `rows = list(csv.DictReader(f))`. Обращение по имени столбца (`row["amount"]`) работает и при другом порядке столбцов.

::: quiz
`csv.DictReader` прочитал строку `{"city": "Пермь", "amount": "450"}`. Что нужно сделать, прежде чем складывать суммы?

- [x] Превратить `amount` в число: `int(row["amount"])`
  > CSV — текстовый файл, поэтому все значения приходят строками. Без `int` «сложение» склеит строки.
- [ ] Ничего: `DictReader` сам распознаёт числа
  > Не распознаёт, в отличие от pandas. Каждое значение — строка.
- [ ] Удалить заголовок файла
  > `DictReader` сам берёт заголовок как названия ключей, он в данные не попадает.
- [ ] Открыть файл в режиме `"w"`
  > Режим `"w"` — для записи, и он стирает файл.
:::

### Какую сумму считаем битой

В `orders.csv` три суммы, которые `int()` не берёт: пустая строка, прочерк `—` и `1 250` с пробелом. Последнюю можно было бы починить — `replace(" ", "")` из урока «Строки и f-строки» превратит её в 1250. Но пробел внутри числа значит, что выгрузка нарушила свой же формат, и молча чинить такое — значит прятать проблему от того, кто отвечает за выгрузку. Поэтому в задачах этого урока и в мини-проекте правило одно: **битая сумма — всё, что `int()` не превращает в число как есть**, включая `1 250`. Такую строку не чиним, а пропускаем и считаем — в отчёте она будет видна в строке «не разобрано».

{{practice: p-dictreader, count-rows, total, by-city}}

## Даты

В `orders.csv` даты записаны как `2026-09-15` — это стандартный формат ISO. Модуль `datetime` превращает такой текст в дату, с которой можно работать:

```python
import datetime as dt

d = dt.date.fromisoformat("2026-09-15")
print(d.year, d.month, d.day)
print(d.weekday())                          # 0 — понедельник, 6 — воскресенье
print(d + dt.timedelta(days=7))             # через неделю
print((dt.date(2026, 9, 30) - d).days)      # дней между датами
```

Что здесь происходит:

- `fromisoformat` превращает текст `2026-09-15` в дату; у неё есть год, месяц и день по отдельности.
- `weekday()` — номер дня недели: понедельник — 0, воскресенье — 6. Он понадобится в задаче про выручку по дням недели.
- `dt.timedelta(days=7)` — промежуток «7 дней»; дата плюс промежуток — новая дата.
- Разность двух дат — тоже промежуток, а `.days` даёт его длину в днях.

Теперь возьмём дату прямо из словаря, который вернул `DictReader`. Для первой записи `row["date"]` — строка `"2026-09-03"`. Вызов `dt.date.fromisoformat(row["date"])` даст дату 3 сентября. У следующей записи текст берётся из той же колонки.

::: predict
```python static
import datetime as dt
d = dt.date.fromisoformat("2026-09-15")
print((dt.date(2026, 9, 20) - d).days)
```

- `20`
- [x] `5`
- `2026-09-05`

Почему: разность двух дат — промежуток; `.days` достаёт из него число дней.
:::

::: warn Типичные ошибки
- **Нет `encoding="utf-8"`.** Если кодировка по умолчанию отличается от UTF-8, русские буквы могут отобразиться неверно или чтение прервётся.
- **Числа из CSV остались строками.** `"260" + "460"` — это `"260460"`.
- **Запись без `newline=""`.** В Windows между строками CSV появятся пустые строки.
- **Режим `"w"` по ошибке.** Открытие на запись стирает файл — читать нужно в режиме по умолчанию.
:::

{{practice: weekdays, loader}}

## Практика

## task: mean | Средняя выручка | warmup

С помощью функции `mean` из модуля `statistics` посчитайте `avg` — среднюю выручку, округлённую до целого.

### starter
```python
revenue = [41200, 38900, 45100, 39800, 52300, 61700, 58400]

```

### check
```python
assert need('avg') == 48200, f'avg = {need("avg")}.'
assert 'statistics' in _code and calls('mean'), 'Подключите mean из statistics.'
```

### hint
Функцию из модуля импортируют строкой `from модуль import функция`.

### hint
`from statistics import mean`, затем `round(mean(revenue))`.

### solution
```python
from statistics import mean
revenue = [41200, 38900, 45100, 39800, 52300, 61700, 58400]
avg = round(mean(revenue))
```

## task: menu | Меню из файла | warmup

Прочитайте `menu.txt` в список `menu` — без переводов строк и без пустых строк.

### starter
```python

```

### check
```python
want = [l.strip() for l in open('menu.txt', encoding='utf-8') if l.strip()]
assert need('menu') == want, f'menu = {need("menu")!r}. Уберите \\n через strip() и пропустите пустые строки.'
assert 'open(' in _code, 'Прочитайте файл через open.'
```

### hint
Открывайте файл через `with open("menu.txt", encoding="utf-8") as f:` — он сам закроется.

### hint
Цикл по файлу, `name = line.strip()`, `if name: menu.append(name)`.

### solution
```python
menu = []
with open("menu.txt", encoding="utf-8") as f:
    for line in f:
        name = line.strip()
        if name:
            menu.append(name)
```

## task: p-dictreader | Соберите чтение CSV | warmup

Соберите программу, которая считает, сколько заказов было в Перми.

### parsons
```python
import csv
count = 0
with open("orders.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["city"] == "Пермь":
            count += 1
print(count)
```

### check
```python
import csv as _csv
want = sum(1 for r in _csv.DictReader(open('orders.csv', encoding='utf-8')) if r['city'] == 'Пермь')
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
`import` — первой строкой. Счётчик создаётся до `with`, вывод — после него, без отступа.

### hint
Внутри цикла по `DictReader`: `if row["city"] == "Пермь": count += 1`.

## task: count-rows | Сколько записей в выгрузке | base

Посчитайте `n_orders` — число записей в `orders.csv`. Прочитайте UTF-8-файл модулем `csv`. Заголовок пропустите, а повторяющиеся записи и строки с испорченной суммой пока учитывайте.

### starter
```python
import csv

```

### check
```python
import ast as _ast
import csv as _csv
with open('orders.csv', encoding='utf-8', newline='') as _source:
    _count = sum(1 for _row in _csv.DictReader(_source))
assert need('n_orders') == _count, f'n_orders = {need("n_orders")}, а записей без заголовка {_count}.'
_imports = [n for n in _ast.walk(_ast.parse(_code)) if isinstance(n, (_ast.Import, _ast.ImportFrom))]
assert any(getattr(n, 'module', None) == 'csv' or any(a.name == 'csv' for a in n.names) for n in _imports), 'Для чтения таблицы подключите модуль csv или импортируйте из него reader либо DictReader.'
```

### hint
`len(list(csv.DictReader(f)))` — DictReader сам пропускает строку заголовка.

### hint
Всё чтение — внутри `with open("orders.csv", encoding="utf-8") as f:`.

### solution
```python
import csv
with open("orders.csv", encoding="utf-8", newline="") as f:
    n_orders = len(list(csv.DictReader(f)))
```

### explain
В файле 41 запись и 40 разных `order_id`. Заказ `Z-1038` выгрузился дважды. В проекте после исключения трёх строк с испорченной суммой и одного повтора для расчёта останется 37 заказов.

## task: total | Выручка за месяц | base

Посчитайте `total` — сумму столбца `amount` по всем заказам. В выгрузке есть строки с битой суммой — пропускайте их и посчитайте их количество в `bad`. Битая — любая сумма, которую `int()` не берёт как есть, в том числе `1 250` с пробелом.

### starter
```python
import csv

```

### check
```python
import csv as _csv
t, b = 0, 0
for r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        t += int(r['amount'])
    except ValueError:
        b += 1
assert need('total') != t + 1250, f'total = {need("total")}: похоже, сумма «1 250» починена и учтена. В этом уроке её считаем битой — пропустите и посчитайте в bad.'
assert need('total') == t, f'total = {need("total")}, а должно быть {t}.'
assert need('bad') == b, f'bad = {need("bad")}, а битых сумм {b}.'
```

### hint
Сумма — строка: `int(row["amount"])`. Обёртка `try/except ValueError` из прошлого урока.

### hint
Два накопителя до `with`: `total = 0`, `bad = 0`; в `except` — `bad += 1`.

### solution
```python
import csv
total = 0
bad = 0
with open("orders.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            total += int(row["amount"])
        except ValueError:
            bad += 1
```

### explain
В 38 записях сумму удалось прочитать. Вместе они дают 16 820 ₽. Три значения пришлось пропустить — пустое, прочерк и `1 250`. В 16 820 ₽ ещё включена повторная запись на 450 ₽. В проекте вы удалите повтор и получите 16 370 ₽ по 37 принятым заказам.

## task: by-city | Выручка по городам из файла | base

Посчитайте словарь `by_city`: город → сумма заказов. Строки с битой суммой (её не берёт `int()` как есть, включая `1 250`) пропускайте.

### starter
```python
import csv

```

### check
```python
import csv as _csv
want = {}
for r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        a = int(r['amount'])
    except ValueError:
        continue
    want[r['city']] = want.get(r['city'], 0) + a
_alt = dict(want); _alt['Тюмень'] += 1250
assert need('by_city') != _alt, f'by_city = {need("by_city")}: у Тюмени учтена сумма «1 250». В этом уроке её считаем битой (int() не берёт её как есть) — пропустите строку.'
assert need('by_city') == want, f'by_city = {need("by_city")}, а должно быть {want}.'
```

### hint
Словарь-накопитель из урока «Словари — GROUP BY своими руками» + `try/except` вокруг `int`.

### hint
В `except ValueError:` — `continue`: перейти к следующей строке, не трогая словарь.

### solution
```python
import csv
by_city = {}
with open("orders.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            amount = int(row["amount"])
        except ValueError:
            continue
        by_city[row["city"]] = by_city.get(row["city"], 0) + amount
```

### explain
Казань — 5 770, Пермь — 5 720, Уфа — 3 020, Тюмень — 2 310. Тот же приём, что в уроке «Словари — GROUP BY своими руками», только данные пришли из файла, а битые строки отсеяны `continue`.

## task: write | Записать отчёт | base

Запишите словарь `by_city` в UTF-8-файл `by_city.csv` с заголовком `city,revenue` и отдельной записью для каждого города в порядке словаря. Используйте `csv.writer`, чтобы код работал и с другими названиями, в том числе с запятой.

### starter
```python
import csv
by_city = {"Пермь": 1450, "Казань": 600, "Тюмень": 715}

```

### check
```python
import csv as _csv
import os as _os
from tempfile import TemporaryDirectory as _TemporaryDirectory

def _check_file(source):
    assert _os.path.isfile('by_city.csv'), 'Файл by_city.csv не создан.'
    with open('by_city.csv', encoding='utf-8', newline='') as file:
        try:
            rows = list(_csv.reader(file, strict=True))
        except _csv.Error as error:
            raise AssertionError(f'Не удалось прочитать записи CSV. Проверьте разделители и кавычки. {error}')
    assert len(rows) == len(source) + 1, f'В by_city.csv прочитано записей: {len(rows)}. Нужны заголовок и отдельная запись для каждого из {len(source)} городов.'
    assert rows[0] == ['city', 'revenue'], f'Проверьте заголовок. Прочитаны поля {rows[0]!r}.'
    for number, (city, revenue) in enumerate(source.items(), 1):
        assert rows[number] == [city, str(revenue)], f'Запись {number} после заголовка: {rows[number]!r}. Ожидались город {city!r} и выручка {revenue}.'

_check_file({'Пермь': 1450, 'Казань': 600, 'Тюмень': 715})
_other = {'Нижний Новгород': 320, 'Казань, центр': 140}
with _TemporaryDirectory() as _tmp:
    _previous = _os.getcwd()
    try:
        _os.chdir(_tmp)
        rerun_with(by_city=dict(_other))
        _check_file(_other)
    finally:
        _os.chdir(_previous)
```

### hint
`open("by_city.csv", "w", encoding="utf-8", newline="")`, затем `w = csv.writer(f)`, `w.writerow([...])`.

### hint
Сначала `w.writerow(["city", "revenue"])` — заголовок, потом цикл по `by_city.items()`.

### solution
```python
import csv
by_city = {"Пермь": 1450, "Казань": 600, "Тюмень": 715}
with open("by_city.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["city", "revenue"])
    for city, revenue in by_city.items():
        w.writerow([city, revenue])
```

### explain
Получился CSV, который откроет Excel или pandas: заголовок и строка на город. Запись результатов в файл — последний шаг любой обработки: отчёт можно передать дальше без вашего кода.

## task: weekdays | Выручка по дням недели | plus

Посчитайте `by_weekday`: номер дня недели (0 — понедельник) → сумма заказов. Битые суммы (те, что не берёт `int()`, включая `1 250`) пропускайте. Затем найдите `best_weekday` — номер самого выручального дня недели.

### starter
```python
import csv
import datetime as dt

```

### check
```python
import csv as _csv, datetime as _dt
want = {}
for r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        a = int(r['amount'])
    except ValueError:
        continue
    k = _dt.date.fromisoformat(r['date']).weekday()
    want[k] = want.get(k, 0) + a
_alt = dict(want); _alt[_dt.date(2026, 9, 24).weekday()] += 1250
assert need('by_weekday') != _alt, 'В by_weekday учтена сумма «1 250» (четверг, 24 сентября). В этом уроке её считаем битой — пропустите строку.'
assert need('by_weekday') == want, f'by_weekday = {need("by_weekday")}, а должно быть {want}.'
assert need('best_weekday') == max(want, key=want.get), f'best_weekday = {need("best_weekday")}.'
```

### hint
`dt.date.fromisoformat(row["date"]).weekday()` — ключ словаря.

### hint
Самый выручальный — `max(by_weekday, key=by_weekday.get)`, как в уроке «Генераторы списков, zip, sorted».

### solution
```python
import csv
import datetime as dt
by_weekday = {}
with open("orders.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            amount = int(row["amount"])
        except ValueError:
            continue
        day = dt.date.fromisoformat(row["date"]).weekday()
        by_weekday[day] = by_weekday.get(day, 0) + amount
best_weekday = max(by_weekday, key=by_weekday.get)
```

### explain
Ключ словаря — не дата, а номер дня недели: все понедельники складываются в одну корзину 0, все вторники — в 1 и так далее. Это то же GROUP BY, только группа вычисляется на лету через `.weekday()`. Битые суммы отбрасываются через `try`/`continue` до того, как попасть в словарь, иначе одна строка «—» уронила бы весь подсчёт. `max(by_weekday, key=by_weekday.get)` перебирает ключи (номера дней), а сравнивает их по значениям — суммам.

## task: loader | Функция загрузки | star

Напишите `load_orders(path)`. Функция читает CSV по переданному пути и возвращает список словарей в порядке записей файла. Сохраните все пять полей каждой записи. Преобразуйте `amount` в `int`, а `date` — в `dt.date`. Строки с битой суммой (её не берёт `int()` как есть, включая `1 250`) пропускайте. Повторы пока сохраняйте. Затем посчитайте `avg_check` — средний чек по записям, загруженным из `orders.csv`, округлённый до целого.

### starter
```python
import csv
import datetime as dt

def load_orders(path):
    ...

orders = load_orders("orders.csv")

```

### setup
```python
import csv as _source_csv
with open('orders.csv', encoding='utf-8', newline='') as _source_file:
    _source_records = list(_source_csv.DictReader(_source_file))
```

### check
```python
import csv as _csv
import datetime as _dt
from pathlib import Path as _Path
from tempfile import TemporaryDirectory as _TemporaryDirectory

def _expected_rows(records):
    result = []
    for row in records:
        try:
            amount = int(row['amount'])
        except ValueError:
            continue
        result.append(dict(row, amount=amount, date=_dt.date.fromisoformat(row['date'])))
    return result

def _compare_rows(actual, expected, label):
    assert isinstance(actual, list), f'{label}: верните список словарей.'
    assert len(actual) == len(expected), f'{label}: загружено {len(actual)} записей, с читаемой суммой — {len(expected)}. Повторы здесь сохраняются.'
    for row, original in zip(actual, expected):
        order_id = original['order_id']
        assert isinstance(row, dict), f'{label}, {order_id}: запись должна быть словарём.'
        for field, value in original.items():
            assert field in row, f'{label}, {order_id}: пропущено поле {field}.'
            assert type(row[field]) is type(value) and row[field] == value, f'{label}, {order_id}: проверьте {field}. Получено {row[field]!r}, в исходной записи после преобразования {value!r}.'

_load = need('load_orders')
_original = _expected_rows(_source_records)
_compare_rows(need('orders'), _original, 'orders')
assert need('avg_check') == round(sum(r['amount'] for r in _original) / len(_original)), f'avg_check = {need("avg_check")}.'
with _TemporaryDirectory() as _tmp:
    _other = _Path(_tmp) / 'october.csv'
    with _other.open('w', encoding='utf-8', newline='') as _file:
        _csv.writer(_file).writerows([
            ['order_id', 'date', 'city', 'drink', 'amount'],
            ['O-1', '2026-10-18', 'Нижний Новгород', 'Кофе, фильтр', '375'],
            ['O-2', '2026-10-19', 'Уфа', 'Раф', '—'],
            ['O-3', '2026-10-20', 'Уфа', 'Чай', '130'],
        ])
    with _other.open(encoding='utf-8', newline='') as _file:
        _expected = _expected_rows(_csv.DictReader(_file))
    _compare_rows(_load(str(_other)), _expected, 'load_orders(другой путь)')
```

### hint
У следующей записи своя дата. Как получить её из `row["date"]`? Вспомните вызов `dt.date.fromisoformat(...)` в разделе «Даты». Когда сумма успешно прочитана, замените текст даты в словаре и добавьте эту запись в список.

### hint
Средний чек — `sum(o["amount"] for o in orders) / len(orders)`, затем `round`.

### solution
```python
import csv
import datetime as dt

def load_orders(path):
    result = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["amount"] = int(row["amount"])
            except ValueError:
                continue
            row["date"] = dt.date.fromisoformat(row["date"])
            result.append(row)
    return result

orders = load_orders("orders.csv")
avg_check = round(sum(o["amount"] for o in orders) / len(orders))
```

### explain
Такая функция — обычное начало любого анализа: один раз загрузить и привести типы, дальше работать с чистыми данными. В следующем уроке на её основе соберём отчёт.
