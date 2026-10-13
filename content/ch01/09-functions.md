---
title: Функции
lead: Упаковываем повторяющиеся расчёты в функции — свои маленькие «формулы», которые можно вызывать по имени с разными данными.
recap:
  - "`def имя(параметры):` — объявить функцию; тело с отступом; `return` — вернуть результат."
  - "`print` в функции только показывает значение; чтобы использовать результат дальше, нужен `return`. Без `return` функция возвращает `None`."
  - "Параметры по умолчанию: `def fmt(x, decimals=0)` — второй аргумент можно не передавать."
  - "Переменные внутри функции — локальные: снаружи их не видно."
  - "Аннотации типов `def avg(revenue: float, orders: int) -> float:` — подсказка для людей и редактора, Python их не проверяет."
  - "PEP 8: имена — `snake_case`, константы — `ЗАГЛАВНЫМИ`, отступ 4 пробела, пробелы вокруг `=` и операторов, но `ndigits=2` в аргументе — слитно. `ruff format` расставит пробелы сам, имена — ваша работа."
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
Попросили коллегу посчитать средний чек. `print` — он прочитал число вслух: вы услышали, но вставить в отчёт нечего. `return` — он отдал листок с числом: его можно сложить, сравнить, передать дальше. Хромает аналогия в одном: функция может и сказать вслух, и отдать листок — `print` и `return` друг другу не мешают.
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

{{practice: rub}}

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

## Стиль кода: PEP 8

Код читают чаще, чем пишут: коллега, ревьюер вашего проекта, вы сами через месяц. Если в одном файле встречаются `TotalRevenue`, `total_rev` и `totalrevenue`, отступы то по два пробела, то по четыре, а `if` то в одну строку, то в две, — читатель тратит внимание на форму вместо смысла. Поэтому у Python есть общий для всех стиль — **PEP 8** (*Python Enhancement Proposal* № 8, документ-соглашение о том, как оформлять код).

::: tip Аналогия
Отчёт по корпоративному шаблону: те же цифры, но заголовки, шрифты и таблицы на привычных местах, и глаз сразу находит нужное. Хромает аналогия в одном: код «не по шаблону» всё равно работает — PEP 8 нарушает только удобство, а не правильность.
:::

**Пример руками.** Две версии одной функции — среднего чека. Обе работают и выводят одно и то же:

```python
def AvgCheck(Revenue,Orders):
  if Orders==0: return 0
  return round(Revenue/Orders,ndigits = 2)
print(AvgCheck(84530,260))
```

```python
def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, ndigits=2)


print(avg_check(84530, 260))
```

Что изменилось во второй версии — по строкам:

- `AvgCheck(Revenue,Orders)` → `avg_check(revenue, orders)`: имена функций и переменных — маленькими буквами через подчёркивание (*snake_case*). Слова с заглавной буквы (`AvgCheck`) в Python оставляют для особых случаев, в своих функциях их не используют. После запятой — пробел.
- Отступ — **4 пробела**, а не 2.
- `if Orders==0: return 0` → две строки: условие отдельно, действие с отступом под ним. Вокруг `==` — пробелы.
- `Revenue/Orders` → `revenue / orders`: пробелы вокруг арифметики делают выражение читаемым.
- `ndigits = 2` → `ndigits=2`: у **именованного аргумента** пробелов вокруг `=` как раз нет. Это единственное место, где `=` пишут слитно.
- Две пустые строки после функции отделяют её от остального кода.

Главные правила одной таблицей:

| что | не так | так |
|---|---|---|
| имена переменных и функций | `TotalRevenue`, `avgCheck` | `total_revenue`, `avg_check` |
| константы — значения, которые не меняются | `vat = 0.2` | `VAT_RATE = 0.2` (заглавные) |
| отступ | 2 пробела или табуляция | 4 пробела |
| присваивание и сравнение | `x=a+b`, `if x==0:` | `x = a + b`, `if x == 0:` |
| именованный аргумент | `round(x, ndigits = 2)` | `round(x, ndigits=2)` |
| запятая | `f(a,b)` | `f(a, b)` |
| инструкции | `if x: return 0` | `if x:` и `return 0` на новой строке |
| длина строки | 150 символов | до 79–88 символов; длинное выражение — в скобках на несколько строк |

Следить за пробелами руками на своём компьютере не придётся: это делает программа-форматтер **ruff** — она расставит пробелы, отступы и переносы сама. Её поставим в уроке «Своё рабочее место — uv и Jupyter», где появится терминал. Имена форматтер не трогает: `AvgCheck` останется `AvgCheck`, переименовать — решение человека. Поэтому правила полезно один раз пройти руками — для этого задачи ниже.

::: warn Типичные ошибки
- **Пробелы вокруг `=` в аргументе.** `round(x, ndigits = 2)` работает, но нарушает PEP 8 — правильно `ndigits=2`. Для присваивания наоборот: `x = 2`.
- **Смешанные отступы.** Табуляция в одной строке и пробелы в соседней дают `TabError` или `IndentationError: unindent does not match any outer indentation level`.
- **«Красивый, значит правильный».** Стиль не проверяет логику: аккуратно оформленная функция может считать неверно.
:::

::: quiz
Какая строка написана по PEP 8?

- [x] `month_revenue = round(total / days, ndigits=2)`
  > Имя в snake_case, пробелы вокруг `=` присваивания и `/`, у именованного аргумента `ndigits=2` пробелов нет.
- [ ] `MonthRevenue = round(total / days, ndigits=2)`
  > Слова с заглавной буквы в своих переменных не используют; переменная — `month_revenue`.
- [ ] `month_revenue=round(total/days, ndigits = 2)`
  > Наоборот: вокруг присваивания и `/` пробелы нужны, а вокруг `=` именованного аргумента — нет.
- [ ] `month_revenue = round(total / days,ndigits=2)`
  > После запятой нужен пробел.
:::

{{practice: snake, tidy}}

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

## task: rub | Рубли для отчёта | base

Напишите `rub(amount, decimals=0)` — строку с пробелами между тысячами и знаком рубля. По умолчанию без копеек:

- `rub(1314000.456)` → `"1 314 000 ₽"`;
- `rub(1314000.456, 2)` → `"1 314 000.46 ₽"`.

### starter
```python
def rub(amount, decimals=0):
    ...

```

### check
```python
f = need('rub')
assert f(1314000.456) == '1 314 000 ₽', f'rub(1314000.456) = {f(1314000.456)!r}.'
assert f(1314000.456, 2) == '1 314 000.46 ₽', f'rub(1314000.456, 2) = {f(1314000.456, 2)!r}.'
assert f(950) == '950 ₽', f'rub(950) = {f(950)!r}.'
```

### hint
Ширину дробной части можно подставить внутрь формата: `f"{amount:,.{decimals}f}"`. Пример есть в теории.

### hint
Далее `.replace(",", " ")` и `+ " ₽"` — или всё одной f-строкой.

### solution
```python
def rub(amount, decimals=0):
    text = f"{amount:,.{decimals}f}".replace(",", " ")
    return text + " ₽"
```

### explain
Параметр по умолчанию `decimals=0` делает частый случай коротким (`rub(x)`), а редкий — возможным (`rub(x, 2)`). Так устроены почти все функции pandas.

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

## task: snake | Имена по PEP 8 | warmup

Код считает средний чек правильно, но имена переменных написаны в стиле других языков. Переименуйте их по PEP 8: `TotalRevenue` → `total_revenue`, `OrdersCount` → `orders_count`, `avgCheck` → `avg_check`. Число `0.2` — ставка НДС, она не меняется: сделайте его константой `VAT_RATE` и посчитайте через неё `vat` — НДС, входящий в средний чек (`avg_check * VAT_RATE / (1 + VAT_RATE)`, округлить до двух знаков).

### starter
```python
TotalRevenue = 84530
OrdersCount = 260
avgCheck = round(TotalRevenue / OrdersCount, 2)
vat = round(avgCheck * 0.2 / (1 + 0.2), 2)
print(avgCheck, vat)
```

### check
```python
import ast as _ast
_tree = _ast.parse(_code)
_names = {n.id for n in _ast.walk(_tree) if isinstance(n, _ast.Name) and isinstance(n.ctx, _ast.Store)}
_bad = sorted(x for x in _names if x != x.lower() and x != x.upper())
assert not _bad, f'Остались имена не в snake_case: {_bad}. Маленькие буквы и подчёркивание между словами.'
assert {'total_revenue', 'orders_count', 'avg_check', 'VAT_RATE', 'vat'} <= _names, f'Нужны переменные total_revenue, orders_count, avg_check, VAT_RATE и vat. Сейчас присваиваются: {sorted(_names)}.'
assert need('VAT_RATE') == 0.2, f'VAT_RATE = {need("VAT_RATE")!r}. Ставка НДС — 0.2.'
assert need('avg_check') == 325.12, f'avg_check = {need("avg_check")!r}. Переименование не должно менять расчёт.'
assert need('vat') == 54.19, f'vat = {need("vat")!r}. Формула та же, только вместо 0.2 — VAT_RATE.'
assert '0.2' not in _code.replace('VAT_RATE = 0.2', '').replace('VAT_RATE=0.2', ''), 'Число 0.2 должно встречаться только один раз — в объявлении VAT_RATE. Дальше используйте константу.'
```

### hint
Переменные — snake_case: маленькие буквы, слова через `_`. Константы — заглавными: `VAT_RATE`. Переименовывать нужно везде, где имя встречается, а не только при объявлении.

### hint
Первой строкой объявите `VAT_RATE = 0.2`, а в формуле НДС замените оба `0.2` на `VAT_RATE`.

### hint
```python
VAT_RATE = 0.2
total_revenue = 84530
orders_count = ...
avg_check = round(... / ..., 2)
vat = round(avg_check * VAT_RATE / (1 + ...), 2)
```

### solution
```python
VAT_RATE = 0.2
total_revenue = 84530
orders_count = 260
avg_check = round(total_revenue / orders_count, 2)
vat = round(avg_check * VAT_RATE / (1 + VAT_RATE), 2)
print(avg_check, vat)
```

## task: tidy | Причешите функцию | base

Функция работает, но оформлена против всех правил PEP 8. Приведите её к PEP 8 и переименуйте по правилам. Один раз руками — чтобы запомнить правила; дальше на своём компьютере это будет делать форматтер.

- функция — `avg_check`, параметры — `revenue` и `orders`;
- отступы — по 4 пробела;
- `if` и `return 0` — на разных строках;
- пробел после каждой запятой и вокруг `==`, `/` и `=` присваивания; у именованного аргумента `ndigits=2` пробелов вокруг `=` нет.

Логику не меняйте: `avg_check(84530, 260)` → `325.12`, `avg_check(500, 0)` → `0`.

### starter
```python
def AvgCheck(Revenue,Orders):
  if Orders==0: return 0
  return round(Revenue/Orders,ndigits = 2)
result=AvgCheck(84530,260)
print(result)
```

### check
```python
import ast as _ast, io as _io, tokenize as _tk
try:
    _tree = _ast.parse(_code)
except SyntaxError as _e:
    raise AssertionError(f'Код не разбирается: {_e.msg} (строка {_e.lineno}). Проверьте отступы и двоеточия.')
_fns = [n for n in _ast.walk(_tree) if isinstance(n, _ast.FunctionDef)]
assert len(_fns) == 1, 'Должна остаться одна функция — переименованная AvgCheck.'
_f = _fns[0]
assert _f.name == 'avg_check', f'Функция называется {_f.name}. По PEP 8 — avg_check.'
assert [a.arg for a in _f.args.args] == ['revenue', 'orders'], f'Параметры: {[a.arg for a in _f.args.args]}. Нужны revenue и orders.'
_g = need('avg_check')
assert _g(84530, 260) == 325.12 and _g(500, 0) == 0, 'Логика функции изменилась: avg_check(84530, 260) должна вернуть 325.12, avg_check(500, 0) — 0.'
for _n in _ast.walk(_tree):
    if isinstance(_n, _ast.If):
        assert _n.body[0].lineno != _n.lineno, f'Строка {_n.lineno}: условие и действие в одной строке. Перенесите return 0 на новую строку с отступом.'
for _i, _ln in enumerate(_code.splitlines(), 1):
    if not _ln.strip():
        continue
    assert '\t' not in _ln[:len(_ln) - len(_ln.lstrip())], f'Строка {_i}: в отступе табуляция. Нужны пробелы.'
    _ind = len(_ln) - len(_ln.lstrip(' '))
    assert _ind % 4 == 0, f'Строка {_i}: отступ {_ind} пробела. По PEP 8 — кратно 4.'
_toks = [t for t in _tk.generate_tokens(_io.StringIO(_code).readline) if t.type not in (_tk.COMMENT, _tk.NL, _tk.NEWLINE, _tk.INDENT, _tk.DEDENT, _tk.ENDMARKER)]
_depth = 0
for _k, _t in enumerate(_toks):
    if _t.type != _tk.OP:
        continue
    if _t.string in '([{':
        _depth += 1
    elif _t.string in ')]}':
        _depth -= 1
    _prev = _toks[_k - 1] if _k else None
    _next = _toks[_k + 1] if _k + 1 < len(_toks) else None
    _gap_l = _prev is not None and _prev.end[0] == _t.start[0] and _prev.end[1] < _t.start[1]
    _gap_r = _next is not None and _next.start[0] == _t.end[0] and _next.start[1] > _t.end[1]
    _where = f'Строка {_t.start[0]}'
    if _t.string == ',' and _next is not None and _next.string not in ')]}' and _next.start[0] == _t.end[0]:
        assert _gap_r, f'{_where}: после запятой нужен пробел.'
    if _t.string in ('==', '!=', '/', '<', '>', '<=', '>='):
        assert _gap_l and _gap_r, f'{_where}: вокруг {_t.string} нужны пробелы с обеих сторон.'
    if _t.string == '=' and _depth > 0:
        assert not _gap_l and not _gap_r, f'{_where}: у именованного аргумента пробелов вокруг = нет: ndigits=2.'
    if _t.string == '=' and _depth == 0:
        assert _gap_l and _gap_r, f'{_where}: вокруг = в присваивании нужны пробелы.'
```

### hint
Начните с имён: `def avg_check(revenue, orders):` — и не забудьте переименовать их в теле и в вызове. Потом — отступы по 4 пробела.

### hint
`if orders == 0:` — отдельной строкой, под ней с отступом `return 0`. В `round(...)` — пробелы вокруг `/`, после запятой, а `ndigits=2` пишется слитно.

### hint
```python
def avg_check(revenue, orders):
    if orders == 0:
        return ...
    return round(revenue / orders, ndigits=2)


result = avg_check(..., ...)
print(result)
```

### solution
```python
def avg_check(revenue, orders):
    if orders == 0:
        return 0
    return round(revenue / orders, ndigits=2)


result = avg_check(84530, 260)
print(result)
```

### explain
Логика не изменилась — функция по-прежнему возвращает 325.12, — а читается заметно легче: имя говорит, что считается, отступы показывают вложенность, пробелы отделяют операнды. Пробелы и отступы на работе расставляет `ruff format`, но имена ни один форматтер за вас не придумает. Если бы вы переименовали функцию только в `def`, а в вызове оставили `AvgCheck(...)`, код упал бы с `NameError: name 'AvgCheck' is not defined` — переименование всегда делают во всех местах сразу.

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
