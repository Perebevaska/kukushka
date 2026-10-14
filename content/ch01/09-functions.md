---
title: Функции
lead: Упаковываем повторяющиеся расчёты в функции — свои маленькие «формулы», которые можно вызывать по имени с разными данными.
recap:
  - "`def имя(параметры):` — объявить функцию; тело с отступом; `return` — вернуть результат."
  - "`print` в функции только показывает значение; чтобы использовать результат дальше, нужен `return`. Без `return` функция возвращает `None`."
  - "Параметры по умолчанию: `def fmt(x, decimals=0)` — второй аргумент можно не передавать."
  - "Переменные внутри функции — локальные: снаружи их не видно."
  - "Аннотации типов `def avg(revenue: float, orders: int) -> float:` — подсказка для людей и редактора, Python их не проверяет."
---

## Зачем свои функции

Вы уже пользовались функциями: `print`, `len`, `round`, `sum`. Это готовые действия с именем: передаём значения в скобках — получаем результат.

Свои функции нужны, когда один и тот же расчёт встречается несколько раз. Средний чек считается в десятке мест отчёта. Если формула изменится (например, решили не учитывать возвраты), без функции придётся искать и править все места. С функцией — одно.

::: sql
Функция — как пользовательская функция в SQL (`CREATE FUNCTION`) или именованная формула в Excel: один раз описали логику, дальше вызываем по имени.
:::

## Как объявить функцию

```python
def avg_check(revenue, orders):
    return round(revenue / orders, 2)

print(avg_check(84530, 260))
print(avg_check(41200, 130))
```

Разберём по частям:

- `def` — «определить» (*define*), дальше имя функции по тем же правилам, что у переменных;
- в скобках — **параметры**: имена, под которыми функция получит переданные значения;
- двоеточие и тело с отступом — как у `for` и `if`;
- `return` — что функция **возвращает** тому, кто её вызвал.

Объявление само по себе ничего не считает: оно только запоминает рецепт. Код внутри выполнится, когда функцию **вызовут**: `avg_check(84530, 260)`. Значения в скобках при вызове называют **аргументами**: `revenue` получит 84530, `orders` — 260.

{{practice: greet, discount}}

## return и print — не одно и то же

Это главная ловушка новичков. `print` показывает значение на экране, но не отдаёт его в программу. `return` отдаёт значение — его можно сохранить в переменную, сложить, передать дальше.

```python
def avg_print(revenue, orders):
    print(round(revenue / orders, 2))

def avg_return(revenue, orders):
    return round(revenue / orders, 2)

a = avg_print(84530, 260)     # напечатает, но вернёт None
b = avg_return(84530, 260)    # вернёт число
print("a =", a)
print("b =", b)
```

Функция без `return` возвращает специальное значение `None` — «ничего». Попытка с ним считать даст `TypeError`.

::: figure return-print
`print` только выводит число на экран, в переменную попадает `None`. `return` отдаёт число туда, где функцию вызвали.
:::

После `return` функция сразу завершается: строки ниже в ней не выполнятся.

::: tip Аналогия
Попросили коллегу посчитать средний чек. `print` — он прочитал число вслух: вы услышали, но вставить в отчёт нечего. `return` — он отдал листок с числом: его можно сложить, сравнить, передать дальше. Одно другому не мешает: функция может и прочитать вслух, и отдать листок.
:::

::: predict
```python static
def f(x):
    print(x * 2)

r = f(5)
print(r)
```

- `10 | 10`
- [x] `10 | None`
- `None`

Почему: функция печатает 10, но ничего не возвращает, поэтому в `r` попадает `None` — его и выводит второй `print`.
:::

::: quiz
Функция `avg_check` считает средний чек и печатает его через `print`, но не делает `return`. Что окажется в `x` после `x = avg_check(84530, 260)`?

- [x] `None`
  > Без `return` функция ничего не отдаёт наружу: число только показано на экране, в `x` оно не попадёт.
- [ ] Средний чек, 325.12
  > На экране он появится, но сохранить его в переменную нельзя — для этого нужен `return`.
- [ ] Строка, которую напечатал `print`
  > `print` ничего не возвращает в вызывающий код, он только выводит текст.
- [ ] Ошибка при вызове
  > Вызов пройдёт без ошибки. Ошибка появится позже, если попробовать с `x` что-то посчитать.
:::

{{practice: p-func, fix-return, report-line}}

## Условия внутри функции

В теле функции можно использовать всё, что уже знаете: условия, циклы, другие функции. Например, защита от деления на ноль:

```python
def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, 2)

print(avg_check(84530, 260))
print(avg_check(0, 0))
```

Второй `return` не нужно прятать в `else`: если сработал первый, до второго дело не дойдёт.

### Разберём вместе: что происходит при вызове

```python
def discounted(price, pct):
    new_price = price * (1 - pct / 100)
    return round(new_price)

a = discounted(250, 10)
b = discounted(190, 5)
print(a, b)
```

Проследим первый вызов `discounted(250, 10)`:

1. Python находит функцию и создаёт её «рабочую комнату»: `price = 250`, `pct = 10` — значения встают в параметры по порядку.
2. `new_price = 250 × (1 − 10 / 100) = 250 × 0.9 = 225.0`.
3. `return round(225.0)` — функция отдаёт **225** и заканчивает работу. Рабочая комната с `price`, `pct`, `new_price` исчезает.
4. 225 попадает в `a`.

::: figure func-call
Вызов `discounted(250, 10)`: аргументы встают в параметры, функция считает в своей «рабочей комнате» и наружу отдаёт только результат `return`.
:::

Второй вызов — новая комната: `price = 190`, `pct = 5`, `new_price = 180.5`, `round(180.5)` = **180**.

::: warn round округляет половинки к чётному
`round(0.5)` = 0, `round(1.5)` = 2, `round(2.5)` = 2, `round(180.5)` = 180. Excel и SQL Server округляют половинки вверх (181), поэтому при сверке отчёта с Python копейки и рубли могут разойтись. Если нужно «как в Excel», округляйте явно: `int(x + 0.5)` для положительных чисел.
:::

Вывод: `225 180`. Снаружи функции `new_price` не существует — `print(new_price)` дал бы `NameError`.

Что получилось: функция — это маленькая программа с входами (параметры) и выходом (`return`). Всё, что внутри, — её личное дело; наружу выходит только то, что вернули.

{{practice: avg-zero, segment-fn}}

## Параметры по умолчанию

Параметру можно задать значение по умолчанию — тогда аргумент при вызове можно пропустить:

```python
def rub(amount, decimals=0):
    text = f"{amount:,.{decimals}f}".replace(",", " ")
    return text + " ₽"

print(rub(1314000.456))
print(rub(1314000.456, 2))
print(rub(1314000.456, decimals=1))
```

Последний вызов передаёт аргумент **по имени**. Так понятнее, что значит число, особенно когда параметров много.

{{practice: pct}}

## Локальные переменные

Переменные, созданные внутри функции, живут только внутри неё. Снаружи их не видно:

```python error
def revenue_of(cups, price):
    result = cups * price
    return result

print(revenue_of(412, 205))
print(result)
```

Это не неудобство, а защита: функции не мешают друг другу и основной программе своими промежуточными переменными. Всё, что нужно снаружи, функция должна вернуть через `return`.

::: predict
```python static
x = 1

def g():
    x = 5
    return x

print(g(), x)
```

- `5 5`
- [x] `5 1`
- `1 1`

Почему: `x` внутри функции — своя, локальная переменная. Внешний `x` она не меняет.
:::

## Функция для списка

Параметром может быть что угодно, в том числе список или словарь:

```python
def total_above(values, threshold):
    total = 0
    for v in values:
        if v > threshold:
            total += v
    return total

revenue = [41200, 38900, 45100, 39800, 52300, 61700, 58400]
print(total_above(revenue, 50000))
print(total_above(revenue, 40000))
```

{{practice: count-above, count-by}}

## Подсказки типов и описание

В современном Python к параметрам и результату принято дописывать **аннотации типов**, а первой строкой тела — короткое описание в тройных кавычках (*docstring*):

```python
def avg_check(revenue: float, orders: int) -> float:
    """Средний чек, округлённый до копеек. Если заказов нет — 0."""
    if orders == 0:
        return 0.0
    return round(revenue / orders, 2)

print(avg_check(84530, 260))
```

Python аннотации **не проверяет** — они подсказка для людей и редактора кода. В задачах курса они необязательны.

::: warn Типичные ошибки
- **`print` вместо `return`.** Функция печатает, но возвращает `None` — дальше считать нечем.
- **Код после `return`.** Он не выполнится: `return` сразу завершает функцию.
- **Вызов до объявления.** `def` должен стоять выше первого вызова.
- **Ожидание доступа к внутренним переменным.** Локальные переменные исчезают после вызова — нужное возвращайте.
:::

{{practice: clean-city}}

## Практика

## task: greet | Первая функция | warmup

Напишите функцию `greet(city)`, которая **возвращает** строку `Привет, <город>!`. Например, `greet("Пермь")` → `"Привет, Пермь!"`.

### starter
```python
def greet(city):
    ...

print(greet("Пермь"))
```

### check
```python
f = need('greet')
assert callable(f), 'greet должна быть функцией (def greet(city): …).'
r = f('Пермь')
assert r is not None, 'Функция ничего не возвращает. Нужен return, а не print.'
assert r == 'Привет, Пермь!', f'greet("Пермь") вернула {r!r}.'
assert f('Уфа') == 'Привет, Уфа!', f'greet("Уфа") вернула {f("Уфа")!r} — функция должна работать для любого города.'
```

### hint
Функция должна **вернуть** строку, а не напечатать её.

### hint
Вместо `...` напишите `return f"Привет, {city}!"`.

### solution
```python
def greet(city):
    return f"Привет, {city}!"

print(greet("Пермь"))
```

## task: p-func | Соберите функцию | warmup

Соберите функцию среднего чека с защитой от нуля и её вызов. Программа выводит `325.12`.

### parsons
```python
def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, 2)
print(avg_check(84530, 260))
```

### check
```python
assert printed_line('325.12'), f'Должно вывестись 325.12. Сейчас: {_lines}'
assert need('avg_check')(1, 0) == 0, 'avg_check(1, 0) должна вернуть 0 — проверьте отступ у return 0.'
```

### hint
Вызов функции — без отступа, после её объявления. `return 0` — внутри `if`.

### hint
Порядок: `def` → `if orders == 0:` → `return 0` → `return round(...)` → вызов и `print`.

## task: fix-return | Где результат? | warmup

Функция «считает», но `total` оказывается `None`, а следующая строка падает. Исправьте функцию, не трогая код после неё.

### starter
```python
def revenue_of(cups, price):
    print(cups * price)

total = revenue_of(412, 205) + revenue_of(538, 198)
print(total)
```

### check
```python
assert need('total') == 190984, f'total = {need("total")!r}.'
r = need('revenue_of')(10, 20)
assert r == 200, f'revenue_of(10, 20) вернула {r!r}.'
```

### hint
Посмотрите, что возвращает функция без `return`: `None`.

### hint
`print` показывает значение, но не возвращает его. Замените на `return`.

### solution
```python
def revenue_of(cups, price):
    return cups * price

total = revenue_of(412, 205) + revenue_of(538, 198)
print(total)
```

### explain
С `print` функция возвращала `None`, и `None * 2` падало. Правило: функция, результат которой нужен дальше, всегда заканчивается `return`.

## task: discount | Цена со скидкой | warmup

Напишите `discounted(price, pct)` — цену после скидки `pct` процентов, округлённую до целого. `discounted(250, 10)` → `225`.

### starter
```python
def discounted(price, pct):
    ...

```

### check
```python
f = need('discounted')
for args, want in [((250, 10), 225), ((199, 15), 169), ((100, 0), 100), ((310, 33), 208)]:
    got = f(*args)
    assert got == want, f'discounted{args} вернула {got!r}, а нужно {want}.'
```

### hint
Скидка 10 % — это умножение на 0.9, то есть на `1 - 10 / 100`.

### hint
Цена со скидкой: `price * (1 - pct / 100)`. Не забудьте `round` и `return`.

### solution
```python
def discounted(price, pct):
    return round(price * (1 - pct / 100))
```

### explain
250 × 0.9 = 225. Параметры позволяют один раз записать формулу и применять её к любой цене и скидке.

## task: avg-zero | Средний чек без падений | base

Напишите `avg_check(revenue, orders)`: средний чек, округлённый до двух знаков. Если заказов 0, функция возвращает 0, а не падает.

### starter
```python
def avg_check(revenue, orders):
    ...

```

### check
```python
f = need('avg_check')
assert close(f(84530, 260), 325.12), f'avg_check(84530, 260) = {f(84530, 260)!r}.'
try:
    z = f(0, 0)
except ZeroDivisionError:
    raise AssertionError('avg_check(0, 0) падает с делением на ноль. Проверьте orders перед делением.')
assert z == 0, f'avg_check(0, 0) = {z!r}, а нужно 0.'
```

### hint
Первой строкой тела: `if orders == 0: return 0`.

### hint
Иначе — `return round(revenue / orders, 2)`.

### solution
```python
def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, 2)
```

### explain
Проверка на ноль — первой строкой: если заказов нет, до деления дело не доходит. «Защитные» проверки в начале функции избавляют от `ZeroDivisionError` в отчёте за пустой день.

## task: pct | Доля в процентах | base

Напишите `pct(part, total, decimals=1)` — строку с долей `part` от `total` в процентах. Знаков после точки — `decimals`, по умолчанию один; после числа — пробел и `%`. Если `total` равен 0, делить нельзя: верните строку `"—"`.

- `pct(412, 1247)` → `"33.0 %"`;
- `pct(412, 1247, 0)` → `"33 %"`;
- `pct(412, 1247, decimals=2)` → `"33.04 %"`;
- `pct(5, 0)` → `"—"`.

### starter
```python
def pct(part, total, decimals=1):
    ...

```

### check
```python
f = need('pct')
assert f(412, 1247) == '33.0 %', f'pct(412, 1247) = {f(412, 1247)!r}, а нужно "33.0 %". Доля — part / total * 100, по умолчанию один знак.'
assert f(412, 1247, 0) == '33 %', f'pct(412, 1247, 0) = {f(412, 1247, 0)!r}. Число знаков должно браться из параметра decimals.'
assert f(412, 1247, decimals=2) == '33.04 %', f'pct(412, 1247, decimals=2) = {f(412, 1247, decimals=2)!r}.'
assert f(1, 3, 2) == '33.33 %', f'pct(1, 3, 2) = {f(1, 3, 2)!r}.'
assert f(5, 0) == '—', f'pct(5, 0) = {f(5, 0)!r}. При total == 0 верните "—" до деления.'
```

### hint
Сначала условие: `if total == 0: return "—"` — до деления. Потом доля `part / total * 100` и f-строка.

### hint
Число знаков подставляется внутрь формата так же, как в `rub` из теории: `f"{x:.{decimals}f} %"`.

### solution
```python
def pct(part, total, decimals=1):
    if total == 0:
        return "—"
    return f"{part / total * 100:.{decimals}f} %"
```

### explain
Параметр по умолчанию `decimals=1` делает частый случай коротким (`pct(a, b)`), а редкий — возможным (`pct(a, b, 2)` или понятнее — `pct(a, b, decimals=2)`). Так устроены почти все функции pandas. Проверка на ноль стоит до деления: `return "—"` сразу завершает функцию, и до `part / total` дело не доходит.

## task: count-above | Сколько дней выше порога | base

Напишите `days_above(values, threshold)` — сколько значений в списке строго больше порога.

### starter
```python
def days_above(values, threshold):
    ...

revenue = [41200, 38900, 45100, 39800, 52300, 61700, 58400]
print(days_above(revenue, 50000))
```

### check
```python
f = need('days_above')
_r = f([41200, 38900, 45100, 39800, 52300, 61700, 58400], 50000)
assert _r == 3, f'Для порога 50 000 должно быть 3 дня, а функция вернула {_r!r}. Если 0 или 1 — проверьте, что return стоит после цикла, а не внутри.'
assert f([1, 2, 3], 3) == 0, 'days_above([1, 2, 3], 3) должна вернуть 0 — «строго больше».'
assert f([], 10) == 0, 'Для пустого списка — 0.'
```

### hint
Внутри функции — тот же счётчик с циклом и `if`, что в уроке про условия. В конце — `return count`.

### hint
`return` — после цикла, без отступа цикла; иначе функция вернёт результат уже на первом шаге.

### solution
```python
def days_above(values, threshold):
    count = 0
    for v in values:
        if v > threshold:
            count += 1
    return count

revenue = [41200, 38900, 45100, 39800, 52300, 61700, 58400]
print(days_above(revenue, 50000))
```

### explain
Счётчик внутри функции — тот же, что в уроке «Условия и цикл while», но теперь его можно вызвать для любого списка и порога одной строкой.

## task: segment-fn | Сегмент как функция | base

Оформите правило сегментации из урока «Условия и цикл while» функцией `segment(avg_check)`: меньше 300 — `"низкий"`, меньше 600 — `"средний"`, иначе — `"высокий"`. Затем постройте список `segments` для всех чеков.

### starter
```python
def segment(avg_check):
    ...

checks = [250, 410, 600, 299, 880]

```

### check
```python
f = need('segment')
for v, want in [(250, 'низкий'), (299, 'низкий'), (300, 'средний'), (599, 'средний'), (600, 'высокий')]:
    assert f(v) == want, f'segment({v}) = {f(v)!r}, а нужно «{want}».'
assert need('segments') == ['низкий', 'средний', 'высокий', 'низкий', 'высокий'], f'segments = {need("segments")}.'
```

### hint
В функции вместо присваивания `segment = …` сразу `return "низкий"` и т. д. Список — циклом с `append(segment(c))`.

### hint
Порядок проверок: `< 300`, потом `< 600`, иначе — «высокий».

### solution
```python
def segment(avg_check):
    if avg_check < 300:
        return "низкий"
    elif avg_check < 600:
        return "средний"
    return "высокий"

checks = [250, 410, 600, 299, 880]
segments = []
for c in checks:
    segments.append(segment(c))
```

### explain
`return` внутри `if` сразу выходит из функции — поэтому `elif` и `else` можно и не писать. Функция `segment` пригодится в pandas: её можно применить к целому столбцу.

## task: clean-city | Нормализация названий | plus

Напишите `clean_city(raw)`: убрать пробелы по краям, привести к виду «Каждое Слово С Большой». Сокращения из словаря `ALIASES` заменить на полное название (сравнивайте без учёта регистра).

- `clean_city("  пермь ")` → `"Пермь"`
- `clean_city("СПБ")` → `"Санкт-Петербург"`
- `clean_city("нижний тагил")` → `"Нижний Тагил"`

### starter
```python
ALIASES = {"спб": "Санкт-Петербург", "екб": "Екатеринбург", "мск": "Москва"}

def clean_city(raw):
    ...

```

### check
```python
f = need('clean_city')
cases = [('  пермь ', 'Пермь'), ('СПБ', 'Санкт-Петербург'), ('нижний тагил', 'Нижний Тагил'),
         (' Екб', 'Екатеринбург'), ('санкт-петербург', 'Санкт-Петербург')]
for raw, want in cases:
    got = f(raw)
    assert got == want, f'clean_city({raw!r}) = {got!r}, а нужно {want!r}.'
```

### hint
Сначала `key = raw.strip().lower()`. Если `key in ALIASES` — вернуть значение из словаря. Иначе — `key.title()`.

### hint
Проверка словаря — до `title()`: ключи `ALIASES` записаны строчными.

### solution
```python
ALIASES = {"спб": "Санкт-Петербург", "екб": "Екатеринбург", "мск": "Москва"}

def clean_city(raw):
    key = raw.strip().lower()
    if key in ALIASES:
        return ALIASES[key]
    return key.title()
```

### explain
Имя `ALIASES` написано большими буквами — так в Python принято называть константы: значения, которые задают один раз и не меняют.

Функция собирает три приёма: чистку, словарь сокращений и форматирование. В главе 3 тот же подход будет применяться к столбцу из тысяч городов сразу.

## task: report-line | Функция использует функцию | plus

Напишите `report_line(city, revenue, orders)`, которая возвращает строку отчёта вида

```text
Пермь: выручка 84 530 ₽, средний чек 325.12 ₽
```

Внутри используйте функции `rub` и `avg_check` — они уже даны.

### starter
```python
def rub(amount, decimals=0):
    return f"{amount:,.{decimals}f}".replace(",", " ") + " ₽"

def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, 2)

def report_line(city, revenue, orders):
    ...

print(report_line("Пермь", 84530, 260))
```

### check
```python
f = need('report_line')
assert f('Пермь', 84530, 260) == 'Пермь: выручка 84 530 ₽, средний чек 325.12 ₽', f'Сейчас: {f("Пермь", 84530, 260)!r}'
assert f('Уфа', 0, 0) == 'Уфа: выручка 0 ₽, средний чек 0.00 ₽', f'Для нулей: {f("Уфа", 0, 0)!r}'
```

### hint
Средний чек тоже оформите через `rub` — с двумя знаками: `rub(avg_check(revenue, orders), 2)`.

### hint
`return f"{city}: выручка {rub(revenue)}, средний чек {rub(avg_check(revenue, orders), 2)}"`.

### solution
```python
def rub(amount, decimals=0):
    return f"{amount:,.{decimals}f}".replace(",", " ") + " ₽"

def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, 2)

def report_line(city, revenue, orders):
    return f"{city}: выручка {rub(revenue)}, средний чек {rub(avg_check(revenue, orders), 2)}"

print(report_line("Пермь", 84530, 260))
```

### explain
Функция `report_line` ничего не считает сама: денежный формат даёт `rub`, деление с защитой от нуля — `avg_check`. Если завтра формат денег поменяется (например, понадобятся копейки через запятую), правка будет в одном месте, а все отчёты подхватят её автоматически. Обратите внимание на `return`, а не `print`: функция отдаёт строку, и дальше её можно напечатать, записать в файл или склеить с другими строками.

## task: count-by | Универсальный подсчёт | star

Напишите `count_by(items)` — функцию, которая для любого списка возвращает словарь «значение → сколько раз встретилось». Затем с её помощью посчитайте `drinks` по списку заказов и `cities` по списку городов.

### starter
```python
def count_by(items):
    ...

orders = ["Латте", "Раф", "Латте", "Капучино", "Латте"]
order_cities = ["Пермь", "Казань", "Пермь"]

```

### check
```python
f = need('count_by')
assert f([]) == {}, 'Для пустого списка — пустой словарь.'
assert f(['a', 'b', 'a']) == {'a': 2, 'b': 1}, f'count_by(["a", "b", "a"]) = {f(["a", "b", "a"])}.'
assert need('drinks') == {'Латте': 3, 'Раф': 1, 'Капучино': 1}, f'drinks = {need("drinks")}.'
assert need('cities') == {'Пермь': 2, 'Казань': 1}, f'cities = {need("cities")}.'
assert calls('count_by') >= 2, 'Используйте функцию для обоих подсчётов.'
```

### hint
Тело функции — подсчёт из урока про словари, только словарь создаётся внутри функции и возвращается через `return`.

### hint
После функции: `drinks = count_by(orders)`, `cities = count_by(город_список)` — одна функция, два применения.

### solution
```python
def count_by(items):
    counts = {}
    for x in items:
        counts[x] = counts.get(x, 0) + 1
    return counts

orders = ["Латте", "Раф", "Латте", "Капучино", "Латте"]
order_cities = ["Пермь", "Казань", "Пермь"]
drinks = count_by(orders)
cities = count_by(order_cities)
```

### explain
Вы только что написали упрощённую версию `value_counts()` из pandas и `Counter` из стандартной библиотеки. Хорошая функция решает задачу для любых данных, а не для одного списка.
