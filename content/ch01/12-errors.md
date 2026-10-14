---
title: Исключения — как не падать на грязных данных
lead: "В реальных выгрузках всегда есть мусор: пустые суммы, прочерки, опечатки. Учимся ловить ошибки, пропускать плохие строки и считать, сколько их было, — вместо того чтобы падать на первой."
recap:
  - "`try:` — попробовать; `except ValueError:` — что делать, если случилась именно эта ошибка. Остальной код продолжит работать."
  - "Ловите конкретные ошибки (`ValueError`, `KeyError`, `ZeroDivisionError`), а не всё подряд: голый `except:` прячет настоящие баги."
  - "`except ValueError as e:` — сообщение ошибки в переменной `e`; `type(e).__name__` — её тип."
  - "Несколько типов сразу: `except (ValueError, ZeroDivisionError):`."
  - "`continue` — пропустить остаток шага цикла и перейти к следующему."
  - "`raise ValueError(\"…\")` — сообщить об ошибке из своей функции, если данные недопустимы."
---

## Ошибка останавливает программу

Вот суммы заказов из выгрузки. Одна из них — прочерк:

```python error
raw = ["450", "320", "—", "275"]
total = 0
for x in raw:
    total += int(x)
print(total)
```

На третьем элементе `int("—")` падает с `ValueError`, и программа останавливается целиком: итог не посчитан, даже по хорошим строкам. Ошибки такого рода в Python называются **исключениями**, и их можно перехватывать.

## try / except

Код, который может упасть, кладут в блок `try`. В блоке `except` пишут, что делать, если случилась ошибка указанного типа:

```python
raw = ["450", "320", "—", "275"]
total = 0
bad = 0
for x in raw:
    try:
        total += int(x)
    except ValueError:
        bad += 1
print("Итого:", total, "плохих строк:", bad)
```

Как это работает:

1. Python выполняет строки внутри `try`.
2. Если ошибки нет, блок `except` пропускается.
3. Если случилась ошибка `ValueError`, Python сразу прыгает в `except` — остаток блока `try` не выполняется — и идёт дальше, как будто ничего не случилось.

::: figure try-flow
Без ошибки `except` пропускается. При `ValueError` выполнение прыгает в `except`, а затем продолжается после блока. Ошибку другого типа этот `except` не ловит — программа падает.
:::

::: tip Аналогия
Кассир проверяет купюры: подозрительную откладывает в сторону и отмечает в журнале, а очередь обслуживает дальше. Без такой проверки одна плохая купюра остановила бы кассу на весь день. Но этот кассир проверяет только одну примету: `except ValueError` откладывает ошибки одного вида, а ошибку другого типа пропустит — и программа остановится.
:::

::: predict
```python static
try:
    print(int("12a"))
    print("готово")
except ValueError:
    print("плохое число")
```

- `12a | готово`
- [x] `плохое число`
- `плохое число | готово`

Почему: `int("12a")` падает, и Python сразу переходит в `except`. Строка `print("готово")` внутри `try` уже не выполняется.
:::

::: sql
В SQL Server похожее делает `TRY_CAST(x AS int)`: вместо ошибки вернёт `NULL`. В Python такую «безопасную» функцию легко написать самому — см. ниже.
:::

{{practice: not-number, zero}}

## Ловите конкретную ошибку

После `except` указывают **тип** ошибки. Это важно: ловить нужно только то, что ожидаете. Если поймать всё подряд (`except:` без типа или `except Exception:`), то спрячете и настоящие ошибки — например, опечатку в имени переменной:

```python error
raw = ["450", "320", "—"]
total = 0
for x in raw:
    try:
        totl += int(x)        # опечатка!
    except ValueError:
        pass
print(total)
```

Здесь опечатка честно падает с `NameError` — и вы её заметите. Будь там `except:` без типа, программа «тихо» выдала бы 0, и ошибку пришлось бы искать долго.

`pass` — «ничего не делать». Он нужен, потому что блок не может быть пустым.

Самые частые типы при работе с данными:

| Тип | Когда возникает |
|---|---|
| `ValueError` | значение не подходит: `int("—")`, `float("")` |
| `KeyError` | нет такого ключа в словаре |
| `IndexError` | нет такого индекса в списке |
| `ZeroDivisionError` | деление на ноль |
| `TypeError` | операция не для этого типа: `"5" + 1` |

Несколько типов можно поймать одним `except`, перечислив их в скобках:

```python
def avg_check(revenue_text, orders_text):
    try:
        return round(int(revenue_text) / int(orders_text), 2)
    except (ValueError, ZeroDivisionError):
        return None

print(avg_check("84530", "260"))
print(avg_check("84530", "0"))
print(avg_check("—", "260"))
```

::: predict
```python static
try:
    x = 1 / 0
    print("A")
except ZeroDivisionError:
    print("B")
print("C")
```

- `A | C`
- [x] `B | C`
- `B`

Почему: деление на ноль сразу переносит выполнение в `except` («B»), а после блока `try/except` программа продолжается («C»).
:::

::: quiz
Почему не стоит писать голое `except:` (без типа ошибки), чтобы «ничего не падало»?

- [x] Оно поймает и ошибки в самом коде, например опечатку в имени переменной, — баг спрячется
  > `except ValueError:` ловит только ожидаемую проблему данных, а `NameError` от опечатки по-прежнему покажется.
- [ ] Голое `except:` работает медленнее
  > Скорость тут ни при чём: проблема в том, что оно ловит слишком много.
- [ ] Python запрещает `except` без типа
  > Синтаксически это допустимо — потому ошибка и коварная.
- [ ] Оно не ловит `ValueError`
  > Ловит, и вместе с ним всё остальное.
:::

{{practice: keyerror, two-errors}}

## Сообщение ошибки: as e

Чтобы узнать, что именно пошло не так, ошибку можно сохранить в переменную:

```python
for x in ["450", "—", "1 250"]:
    try:
        print(int(x))
    except ValueError as e:
        print("Пропускаю:", e)
```

`type(e).__name__` даёт название типа ошибки строкой — удобно для отчёта «сколько ошибок какого вида». `__name__` — служебное поле, где Python хранит имя; двойные подчёркивания — просто часть его названия.

{{practice: error-report}}

## «Безопасное» превращение в число

Типичный приём — функция, которая возвращает число или `None`, если превратить не получилось:

```python
def to_int(text):
    try:
        return int(text)
    except ValueError:
        return None

amounts = [to_int(x) for x in ["450", "", "—", "320"]]
print(amounts)
print(sum(a for a in amounts if a is not None))
```

`None` — это «нет значения», аналог `NULL`. Проверять на него принято через `is None` / `is not None`.

### continue: пропустить строку и идти дальше

Внутри цикла часто удобно сказать «эту строку пропускаем» — для этого есть `continue`: он сразу переходит к следующему шагу цикла, остаток тела не выполняется.

```python
total = 0
for x in ["450", "—", "320"]:
    try:
        amount = int(x)
    except ValueError:
        continue          # плохая строка — к следующей
    total += amount
print(total)
```

{{practice: p-toint, to-float}}

## raise: сообщить об ошибке самому

Иногда ошибку нужно не ловить, а **вызвать**: если в функцию передали недопустимые данные, честнее упасть сразу с понятным сообщением, чем молча посчитать ерунду.

```python error
def apply_discount(price, pct):
    if not 0 <= pct <= 50:
        raise ValueError(f"скидка {pct}% вне допустимых 0–50%")
    return round(price * (1 - pct / 100))

print(apply_discount(250, 10))
print(apply_discount(250, 80))
```

{{practice: raise}}

## Разберём вместе: try в цикле по выгрузке

Пять сумм из выгрузки: `"450"`, `""`, `"1180"`, `"—"`, `"275"`. Код:

```python
raw = ["450", "", "1180", "—", "275"]
total = 0
bad = 0
for x in raw:
    try:
        total += int(x)
    except ValueError:
        bad += 1
print(total, bad)
```

| шаг | `x` | что в `try` | `total` | `bad` |
|---|---|---|---|---|
| 1 | "450" | `int` = 450, прибавили | 450 | 0 |
| 2 | "" | `int("")` → `ValueError`, прибавление не случилось | 450 | **1** |
| 3 | "1180" | прибавили | 1 630 | 1 |
| 4 | "—" | `ValueError` | 1 630 | **2** |
| 5 | "275" | прибавили | **1 905** | 2 |

::: figure try-loop
Пять значений выгрузки: три превратились в числа и сложились, два вызвали `ValueError` и попали в счётчик `bad`.
:::

1. Ошибка внутри `try` прерывает только этот проход: строка `total += …` не выполнилась, управление ушло в `except`.
2. Цикл продолжается со следующего элемента — программа не падает.
3. Счётчик `bad` — честная пометка «сколько выбросили». Без него отчёт молча показывал бы 1 905 как всю выручку.

Что получилось: `try` внутри цикла превращает «упасть на первой плохой строке» в «пропустить и посчитать, сколько пропущено».

::: warn Типичные ошибки
- **Голый `except:`.** Ловит всё, включая опечатки в вашем же коде; ловите конкретный тип — `ValueError`, `KeyError`.
- **Слишком большой `try`.** Чем больше кода внутри, тем труднее понять, какая строка упала.
- **Молчаливый пропуск.** `except: pass` прячет проблему; хотя бы посчитайте, сколько пропущено.
- **`try` вместо проверки.** Для «заказов 0» понятнее `if orders == 0`; `try` — для ошибок, которые заранее не проверить.
:::

{{practice: skip-bad, bad-lines}}

## Практика

## task: not-number | Не число | warmup

Превратите `text` в число `n` через `int`. Если не получается, вместо падения выведите `Не число`.

### starter
```python
text = "двадцать"

```

### check
```python
assert printed_line('Не число'), 'Для «двадцать» должно вывестись «Не число».'
assert 'except ValueError' in _code, 'Ловите именно ValueError.'
g = {}
exec(_code.replace('"двадцать"', '"20"', 1), g)
assert g.get('n') == 20, 'Для text = "20" в n должно оказаться число 20.'
```

### hint
Опасная строка — превращение `int(text)`; её кладут в `try`.

### hint
```python static
try:
    n = int(text)
except ValueError:
    print("Не число")
```

### solution
```python
text = "двадцать"
try:
    n = int(text)
except ValueError:
    print("Не число")
```

## task: zero | Деление без падения | warmup

Посчитайте `avg` — средний чек, но если заказов 0, пусть `avg` будет `None`. В жизни здесь понятнее `if orders == 0`, но потренируем ловушку для `ZeroDivisionError`: используйте `try/except`, а не `if`.

### starter
```python
revenue = 0
orders = 0

```

### check
```python
assert need('avg') is None, f'avg = {need("avg")!r}, а для 0 заказов нужно None.'
assert 'except ZeroDivisionError' in _code, 'Ловите ZeroDivisionError.'
```

### hint
Деление на ноль вызывает `ZeroDivisionError`.

### hint
В `try` — деление, в `except ZeroDivisionError:` — `avg = None`.

### solution
```python
revenue = 0
orders = 0
try:
    avg = revenue / orders
except ZeroDivisionError:
    avg = None
```

## task: p-toint | Соберите «безопасный int» | warmup

Соберите функцию, которая возвращает число или `None`, и её проверку. Программа выводит `[450, None, 320]`.

### parsons
```python
def to_int(text):
    try:
        return int(text)
    except ValueError:
        return None
print([to_int(x) for x in ["450", "—", "320"]])
```

### check
```python
assert _lines == ['[450, None, 320]'], f'Должно вывестись [450, None, 320]. Сейчас: {_lines}'
```

### hint
`try` и `except` стоят на одном уровне внутри функции, а `return` — внутри каждого из них.

### hint
Порядок: `def` → `try:` → `return int(x)` → `except ValueError:` → `return None` → проверка списком.

## task: skip-bad | Пропустить мусор | base

Посчитайте `total` по хорошим суммам и `bad` — сколько строк не удалось превратить в число. Ничего не чистите: битой считается любая строка, которую `int` не берёт как есть.

### starter
```python
raw = ["450", "320", "", "1180", "—", "275", "1 250", "640"]

```

### check
```python
assert need('total') == 2865, f'total = {need("total")}, а должно быть 2865. Битыми считаются все строки, которые не превращаются в int как есть — и «1 250» тоже.'
assert need('bad') == 3, f'bad = {need("bad")}. Плохих три: пустая строка, прочерк и «1 250» (с пробелом int не справится).'
```

### hint
Это пример из «Разберём вместе».

### hint
Цикл, в нём `try: total += int(x)` и `except ValueError: bad += 1`.

### solution
```python
raw = ["450", "320", "", "1180", "—", "275", "1 250", "640"]
total = 0
bad = 0
for x in raw:
    try:
        total += int(x)
    except ValueError:
        bad += 1
```

### explain
Хорошие суммы — 450, 320, 1 180, 275, 640: итого 2 865. Плохих строк три: пустая, прочерк и «1 250» с пробелом. Последнюю можно было бы починить через `replace`, как в уроке «Строки и f-строки», но пробел внутри числа значит, что выгрузка нарушила свой формат. Молча чинить такое — прятать проблему, поэтому условие просит отложить строку и посчитать её; так же поступим в уроке «Файлы, CSV и модули» и в мини-проекте.

## task: to-float | Цена из любого текста | base

Напишите `to_float(text)`: убирает пробелы, меняет запятую на точку и возвращает `float`. Если превратить не получилось — `None`.

- `to_float("1 250,50")` → `1250.5`
- `to_float("210")` → `210.0`
- `to_float("—")` → `None`, `to_float("")` → `None`

### starter
```python
def to_float(text):
    ...

```

### check
```python
f = need('to_float')
for x, want in [('1 250,50', 1250.5), ('210', 210.0), (' 99,9 ', 99.9), ('—', None), ('', None), ('abc', None)]:
    got = f(x)
    assert got == want, f'to_float({x!r}) = {got!r}, а нужно {want!r}.'
```

### hint
Сначала очистить строку (`replace` дважды), потом `try: return float(clean)`.

### hint
`except ValueError: return None` — пустая строка и прочерк дадут именно `ValueError`.

### solution
```python
def to_float(text):
    clean = text.replace(" ", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None
```

### explain
Одна функция обрабатывает и «1 250,50», и «210», и мусор. Возврат `None` вместо падения позволяет применить её к целому списку и потом посчитать, сколько значений не разобралось.

## task: keyerror | Цена или «нет в меню» | base

Напишите `price_of(name)`: возвращает цену из словаря `PRICES`, а если такого напитка нет — строку `"нет в меню"`. Используйте `try/except KeyError` (не `get`).

### starter
```python
PRICES = {"Латте": 210, "Капучино": 190, "Раф": 260}

def price_of(name):
    ...

print(price_of("Раф"), price_of("Матча"))
```

### check
```python
f = need('price_of')
assert f('Раф') == 260 and f('Латте') == 210, 'Для существующих напитков — цена из словаря.'
assert f('Матча') == 'нет в меню', f'price_of("Матча") = {f("Матча")!r}.'
assert 'KeyError' in _code, 'Ловите KeyError.'
```

### hint
Обращение к отсутствующему ключу словаря вызывает `KeyError`.

### hint
В `try` — `return PRICES[name]`, в `except KeyError:` — `return "нет в меню"`.

### solution
```python
PRICES = {"Латте": 210, "Капучино": 190, "Раф": 260}

def price_of(name):
    try:
        return PRICES[name]
    except KeyError:
        return "нет в меню"

print(price_of("Раф"), price_of("Матча"))
```

### explain
`get` здесь короче, но `try/except KeyError` показывает общий приём: попробовать, а если ключа нет — сделать запасной вариант. Он работает и там, где `get` нет.

## task: raise | Своя проверка | base

Напишите `set_discount(pct)`: если `pct` от 0 до 50 включительно, вернуть его; иначе — вызвать `ValueError` с понятным сообщением.

### starter
```python
def set_discount(pct):
    ...

```

### check
```python
f = need('set_discount')
assert f(0) == 0 and f(15) == 15 and f(50) == 50, 'Допустимые значения 0–50 функция возвращает как есть.'
for bad in (-5, 51, 100):
    try:
        f(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f'set_discount({bad}) должна вызвать ValueError.')
```

### hint
`raise` сам создаёт ошибку — так функция отказывается работать с неверными данными.

### hint
`if not 0 <= pct <= 50: raise ValueError(f"…")`, затем `return pct`.

### solution
```python
def set_discount(pct):
    if not 0 <= pct <= 50:
        raise ValueError(f"скидка {pct}% вне допустимых 0–50%")
    return pct
```

### explain
Скидка 70 % — скорее опечатка, чем решение маркетинга. `raise` останавливает программу с понятным сообщением сразу, а не через неделю, когда отчёт покажет убыток.

## task: bad-lines | Номера плохих строк | plus

Разберите выгрузку: в `rows` — хорошие строки вида `["Пермь", 412, 205]` (числа — `int`), в `bad_lines` — **номера** строк (с 1), которые разобрать не удалось. Плохая строка — та, где не три значения или числа не превращаются в `int`. Напоминание из урока «Таблица из списков»: распаковка на другое число имён (`city, cups, price = ["Казань", "538"]`) — тоже `ValueError`, так что один `except ValueError` ловит оба случая. Многострочный текст в заготовке записан в тройных кавычках `"""…"""` — так строка может занимать несколько строк кода.

### starter
```python
text = """Пермь;412;205
Казань;538
Тюмень;297;214
Уфа;—;189
Пермь;300;210"""

```

### check
```python
assert need('rows') == [['Пермь', 412, 205], ['Тюмень', 297, 214], ['Пермь', 300, 210]], f'rows = {need("rows")}.'
assert need('bad_lines') == [2, 4], f'bad_lines = {need("bad_lines")}. Номера строк начинаются с 1.'
```

### hint
`for n, line in enumerate(text.split("\n"), 1):` — и вся обработка строки в `try`.

### hint
Если значений не три, распаковка `city, cups, price = line.split(";")` сама даст `ValueError` — его и ловите.

### solution
```python
text = """Пермь;412;205
Казань;538
Тюмень;297;214
Уфа;—;189
Пермь;300;210"""
rows = []
bad_lines = []
for n, line in enumerate(text.split("\n"), 1):
    try:
        city, cups, price = line.split(";")
        rows.append([city, int(cups), int(price)])
    except ValueError:
        bad_lines.append(n)
```

### explain
Тройные кавычки `"""…"""` позволяют записать строку в несколько строк — удобно для небольших примеров данных.

## task: two-errors | Средний чек из текста | plus

Посчитайте список `checks` — средний чек по каждой паре «выручка, заказы» (строками), округлённый до целого. Если выручка не число или заказов 0 — в списке должно оказаться `None`.

### starter
```python
pairs = [("84530", "260"), ("—", "120"), ("41200", "0"), ("38900", "121")]

```

### check
```python
assert need('checks') == [325, None, None, 321], f'checks = {need("checks")}.'
```

### hint
Один `except (ValueError, ZeroDivisionError):` на обе беды.

### hint
В `try`: `checks.append(round(int(r) / int(o)))`; в `except`: `checks.append(None)`.

### solution
```python
pairs = [("84530", "260"), ("—", "120"), ("41200", "0"), ("38900", "121")]
checks = []
for r, o in pairs:
    try:
        checks.append(round(int(r) / int(o)))
    except (ValueError, ZeroDivisionError):
        checks.append(None)
```

### explain
Средние чеки: 325, `None`, `None`, 321. Вторая пара не разобралась из-за прочерка, третья — из-за нуля заказов; одна ветка `except` закрывает обе причины, и цикл не падает.

## task: error-report | Отчёт об ошибках | star

Для каждого значения попробуйте посчитать `100 / int(x)`. Соберите словарь `errors`: тип ошибки → сколько раз встретился. Успешные значения не учитываются.

### starter
```python
values = ["5", "—", "0", "", "20", "0", "abc"]

```

### check
```python
_e = need('errors')
assert all(isinstance(k, str) for k in _e), 'Ключами должны быть названия типов — строки, а не сами ошибки: type(e).__name__.'
assert _e == {'ValueError': 3, 'ZeroDivisionError': 2}, f'errors = {_e}.'
```

### hint
Ловите обе ошибки сразу и сохраните её в переменную: `except (ValueError, ZeroDivisionError) as e:`.

### hint
Имя типа — `type(e).__name__`. Дальше подсчёт словарём, как в уроке «Словари — GROUP BY своими руками».

### solution
```python
values = ["5", "—", "0", "", "20", "0", "abc"]
errors = {}
for x in values:
    try:
        100 / int(x)
    except (ValueError, ZeroDivisionError) as e:
        name = type(e).__name__
        errors[name] = errors.get(name, 0) + 1
```

### explain
В списке три значения, которые не превращаются в число («—», пустая строка и «abc»), и два нуля. Поэтому `errors == {"ValueError": 3, "ZeroDivisionError": 2}`. Ловить ошибки кортежем `(ValueError, ZeroDivisionError)` и записывать в переменную `e` удобно для отчёта о качестве данных: видно не только сколько строк пропущено, но и почему. А вот голое `except:` здесь было бы вредно — оно спрятало бы и опечатку в коде.
