---
title: "Контрольная точка: уроки 1–9"
lead: "12 задач на всё, что было в уроках 1–9: числа, строки, списки, циклы, условия, словари и функции. Подсказки и решения откроются, когда завершите контрольную."
mode: exam
---

## task: shift | Выручка смены | base | 02-numbers

За смену продали 96 чашек по 215 рублей. Сохраните выручку в `revenue` и выведите её.

### starter
```python
cups = 96
price = 215

```

### check
```python
assert need('revenue') == 96 * 215, f'revenue = {need("revenue")}.'
assert not has_literal(20640), 'Посчитайте из переменных.'
assert printed('20640'), 'Выведите выручку.'
```

### hint
Выручка — количество × цена.

### hint
`revenue = cups * price`, затем `print(revenue)` — без чисел в коде.

### solution
```python
cups = 96
price = 215
revenue = cups * price
print(revenue)
```

## task: wh-code | Код склада | base | 03-strings

Код склада устроен как `WH-<город>-<номер>`. Сохраните в `city_code` три буквы города (`"PRM"`), а в `number` — номер **числом** (`42`).

### starter
```python
code = "WH-PRM-0042"

```

### check
```python
assert need('city_code') == 'PRM', f'city_code = {need("city_code")!r}.'
n = need('number')
assert n == 42 and isinstance(n, int), f'number = {n!r}. Нужно целое число 42.'
_other = rerun_with(code='WH-KZN-0105')
assert (_other.get('city_code'), _other.get('number')) == ('KZN', 105), 'Для WH-KZN-0105 должны получиться KZN и число 105. Извлеките обе части из code.'
```

### hint
Выпишите индексы: `W H - P R M - 0 0 4 2` → `0 1 2 3 4 5 6 7 8 9 10`.

### hint
Срезы `[3:6]` и `[7:]`; `int("0042")` даёт 42.

### solution
```python
code = "WH-PRM-0042"
city_code = code[3:6]
number = int(code[7:])
```

## task: top2 | Два крупнейших чека | base | 04-lists

Посчитайте `top2_sum` — сумму двух самых крупных чеков.

### starter
```python
checks = [450, 1280, 320, 990, 610, 1150]

```

### check
```python
assert need('top2_sum') == 2430, f'top2_sum = {need("top2_sum")}. Два крупнейших — 1280 и 1150.'
assert rerun_with(checks=[300, 110, 520, 470]).get('top2_sum') == 990, 'Для чеков 300, 110, 520 и 470 сумма двух крупнейших равна 990. Получайте её из текущего списка checks.'
```

### hint
Отсортируйте по убыванию и возьмите срез из двух элементов.

### hint
`top2_sum = sum(sorted(checks, reverse=True)[:2])`.

### solution
```python
checks = [450, 1280, 320, 990, 610, 1150]
top2_sum = sum(sorted(checks, reverse=True)[:2])
```

## task: thousands | Выручка в тысячах | base | 05-for

Постройте список `in_k` — выручка в тысячах рублей, округлённая до одного знака: `41200` → `41.2`.

### starter
```python
revenue = [41200, 38950, 45130, 39870]

```

### check
```python
assert need('in_k') == [41.2, 39.0, 45.1, 39.9], f'in_k = {need("in_k")}.'
assert rerun_with(revenue=[12340, 9810]).get('in_k') == [12.3, 9.8], 'Для выручки [12340, 9810] нужны [12.3, 9.8]. Пересчитайте каждый элемент revenue.'
```

### hint
Новый список через цикл и `append(round(r / 1000, 1))`.

### hint
`round(41200 / 1000, 1)` — `41.2`: второй аргумент `round` — сколько знаков оставить после точки.

### solution
```python
revenue = [41200, 38950, 45130, 39870]
in_k = []
for r in revenue:
    in_k.append(round(r / 1000, 1))
```

## task: labels | Метки дней | base | 06-if

Для каждого дня поставьте метку: `"план"`, если выручка не меньше 45 000, иначе `"ниже плана"`. Сохраните метки списком в `labels`.

### starter
```python
revenue = [41200, 45000, 52300, 44999, 61700]

```

### check
```python
assert need('labels') == ['ниже плана', 'план', 'план', 'ниже плана', 'план'], f'labels = {need("labels")}. 45 000 — это уже «план».'
assert rerun_with(revenue=[45001, 0, 45000]).get('labels') == ['план', 'ниже плана', 'план'], 'Проверьте код на днях с выручкой 45 001, 0 и 45 000. Порядок меток должен совпадать с порядком дней в revenue.'
```

### hint
«Не меньше» — `>=`: ровно 45 000 — это «план».

### hint
Цикл, внутри `if r >= 45000: … else: …`, и `append`.

### solution
```python
revenue = [41200, 45000, 52300, 44999, 61700]
labels = []
for r in revenue:
    if r >= 45000:
        labels.append("план")
    else:
        labels.append("ниже плана")
```

## task: price-growth | Когда латте подорожает | base | 06-if

Латте стоит `price` рублей, цена растёт на 10 рублей в год. Через сколько лет (`years`) цена впервые станет **больше** 250? Посчитайте циклом `while`. Начните с 200 рублей. Ваш расчёт должен работать и при другой начальной цене, в том числе если порог уже пройден.

### starter
```python
price = 200

```

### check
```python
assert need('years') == 6, f'years = {need("years")}. Через 5 лет цена ровно 250 — это ещё не «больше 250»; больше она станет через 6 лет (260).'
for _start, _expected in [(230, 3), (249, 1), (250, 1), (251, 0)]:
    _got = rerun_with(price=_start, _require_while=_expected > 1).get('years')
    assert _got == _expected, f'При начальной цене {_start} ₽ ваш расчёт даёт {_got!r} лет. При росте на 10 ₽ в год нужно {_expected}.'
```

### hint
«Впервые больше 250» — цикл идёт, пока цена ещё не больше 250.

### hint
Пока `price <= 250`: прибавляем к цене 10 и прибавляем год. Ровно 250 — ещё не «больше».

### solution
```python
price = 200
years = 0
while price <= 250:
    price += 10
    years += 1
```

## task: kazan | Выручка Казани | base | 07-tables

В каждой строке `sales` указаны город, число чашек и цена за чашку. Посчитайте `kazan_revenue` — суммарную выручку всех строк Казани. Строки могут идти в любом порядке.

### starter
```python
sales = [
    ["Пермь", 412, 205],
    ["Казань", 538, 198],
    ["Казань", 301, 210],
    ["Тюмень", 297, 214],
]

```

### check
```python
assert need('kazan_revenue') == 538 * 198 + 301 * 210, f'kazan_revenue = {need("kazan_revenue")}.'
_other = rerun_with(sales=[['Казань', 2, 180], ['Пермь', 9, 300], ['Уфа', 3, 220], ['Казань', 1, 220]])
assert _other.get('kazan_revenue') == 580, f'В другой таблице Казань продала 2 чашки по 180 ₽ и одну за 220 ₽. Получено {_other.get("kazan_revenue")!r}, ожидается 580 ₽. Проверьте отбор строк по городу и умножение на число чашек.'
```

### hint
Распакуйте строку в цикле и прибавляйте `cups * price`, только если город — Казань.

### hint
`for city, cups, price in sales: if city == "Казань": kazan_revenue += cups * price`.

### solution
```python
sales = [
    ["Пермь", 412, 205],
    ["Казань", 538, 198],
    ["Казань", 301, 210],
    ["Тюмень", 297, 214],
]
kazan_revenue = 0
for city, cups, price in sales:
    if city == "Казань":
        kazan_revenue += cups * price
```

## task: sizes | Самый ходовой размер | base | 08-dicts

Посчитайте в `counts`, сколько раз заказывали каждый размер, и сохраните в `top_size` самый частый.

### starter
```python
sizes = ["S", "M", "M", "L", "M", "S", "L", "M"]

```

### check
```python
assert need('counts') == {'S': 2, 'M': 4, 'L': 2}, f'counts = {need("counts")}.'
assert need('top_size') == 'M', f'top_size = {need("top_size")!r}.'
_other = rerun_with(sizes=['L', 'S', 'L', 'L', 'M'])
assert _other.get('counts') == {'L': 3, 'S': 1, 'M': 1} and _other.get('top_size') == 'L', 'Для размеров L, S, L, L, M лидирует L с тремя заказами. Проверьте counts и поиск самого частого размера.'
```

### hint
Сначала подсчёт словарём, потом поиск максимума циклом по `items()`.

### hint
Подсчёт: `counts[s] = counts.get(s, 0) + 1`; максимум — как поиск лучшего в уроке про условия: храните лучший размер и его число, обновляйте при `n > best`.

### solution
```python
sizes = ["S", "M", "M", "L", "M", "S", "L", "M"]
counts = {}
for s in sizes:
    counts[s] = counts.get(s, 0) + 1
top_size = ""
best = 0
for size, n in counts.items():
    if n > best:
        best = n
        top_size = size
```

## task: price-update | Новый прайс | base | 08-dicts

Примените изменения к прайсу: каждая пара из `changes` либо меняет цену существующей позиции, либо добавляет новую. Измените сам словарь `prices`.

### starter
```python
prices = {"Латте": 210, "Капучино": 190, "Раф": 260}
changes = {"Латте": 220, "Мокко": 240}

```

### check
```python
assert need('prices') == {'Латте': 220, 'Капучино': 190, 'Раф': 260, 'Мокко': 240}, f'prices = {need("prices")}.'
_prices = {'Эспрессо': 130, 'Латте': 240}
_other = rerun_with(prices=_prices, changes={'Эспрессо': 150, 'Фильтр': 210})
assert _other.get('prices') is _prices, 'Измените существующий словарь prices. Для этого подойдут присваивания по ключу или prices.update(changes).'
assert _prices == {'Эспрессо': 150, 'Латте': 240, 'Фильтр': 210}, 'Во втором прайсе нужно обновить Эспрессо, добавить Фильтр и сохранить прежнюю цену Латте.'
```

### hint
Запись `prices[ключ] = значение` и меняет существующую цену, и добавляет новую позицию.

### hint
`for name, price in changes.items(): prices[name] = price`.

### solution
```python
prices = {"Латте": 210, "Капучино": 190, "Раф": 260}
changes = {"Латте": 220, "Мокко": 240}
for name, price in changes.items():
    prices[name] = price
```

## task: share-fn | Функция доли | base | 09-functions

Напишите `share(part, total)` — долю `part` в `total` в процентах, округлённую до одного знака. Если `total` равен 0, функция возвращает 0.

### starter
```python
def share(part, total):
    ...

```

### check
```python
f = need('share')
for args, want in [((241, 2545), 9.5), ((1, 3), 33.3), ((5, 5), 100.0), ((3, 0), 0)]:
    try:
        got = f(*args)
    except ZeroDivisionError:
        raise AssertionError(f'share{args} падает с делением на ноль.')
    assert got == want, f'share{args} = {got!r}, а нужно {want}.'
```

### hint
Сначала проверка `total == 0`, потом `round(part / total * 100, 1)`.

### hint
В обоих случаях — `return`, а не `print`.

### solution
```python
def share(part, total):
    if total == 0:
        return 0
    return round(part / total * 100, 1)
```

## task: revenue-by | Выручка по любому полю | plus | 09-functions

Напишите `revenue_by(orders, field)`: заказы — список словарей, функция возвращает словарь «значение поля → сумма `amount`». Одна функция должна работать и для `"city"`, и для `"drink"`. Для пустого списка верните `{}`. Для сдачи достаточно определения функции. Данные и вызовы ниже можно использовать для самопроверки.

### starter
```python
def revenue_by(orders, field):
    ...

orders = [
    {"city": "Пермь", "drink": "Латте", "amount": 450},
    {"city": "Казань", "drink": "Раф", "amount": 320},
    {"city": "Пермь", "drink": "Раф", "amount": 610},
]
print(revenue_by(orders, "city"))
print(revenue_by(orders, "drink"))
```

### check
```python
f = need('revenue_by')
sample = [
    {'city': 'Томск', 'drink': 'Чай', 'amount': 120},
    {'city': 'Омск', 'drink': 'Чай', 'amount': 80},
    {'city': 'Томск', 'drink': 'Какао', 'amount': 250},
]
for field, totals in [('city', {'Томск': 370, 'Омск': 80}), ('drink', {'Чай': 200, 'Какао': 250})]:
    actual = f([row.copy() for row in sample], field)
    assert actual == totals, f'Сгруппируйте переданные заказы по полю {field!r} и сложите amount в каждой группе. Получено {actual!r}.'
assert f([{'city': 'Томск', 'drink': 'Чай', 'amount': 15}], 'city') == {'Томск': 15}, 'При новом вызове считайте только заказы из нового списка.'
assert f([], 'city') == {}, 'Для пустого списка — пустой словарь.'
```

### hint
Ключ группы — `o[field]`: имя поля приходит параметром.

### hint
Словарь создаётся внутри функции: `result[o[field]] = result.get(o[field], 0) + o["amount"]`, в конце — `return result`.

### solution
```python
def revenue_by(orders, field):
    result = {}
    for o in orders:
        key = o[field]
        result[key] = result.get(key, 0) + o["amount"]
    return result

orders = [
    {"city": "Пермь", "drink": "Латте", "amount": 450},
    {"city": "Казань", "drink": "Раф", "amount": 320},
    {"city": "Пермь", "drink": "Раф", "amount": 610},
]
print(revenue_by(orders, "city"))
print(revenue_by(orders, "drink"))
```

## task: parse | Разбор выгрузки | star | 07-tables

Напишите `parse_line(line)`, которая превращает строку `"Пермь;412;205"` в список `["Пермь", 412, 205]` (числа — `int`). Затем с её помощью посчитайте `total` — общую выручку (чашки × цена) по всей выгрузке `text`. Пустые строки в выгрузке пропускайте.

### starter
```python
def parse_line(line):
    ...

text = "Пермь;412;205\nКазань;538;198\n\nТюмень;297;214\n"

```

### check
```python
f = need('parse_line')
assert f('Уфа;10;200') == ['Уфа', 10, 200], f'parse_line("Уфа;10;200") = {f("Уфа;10;200")!r}.'
assert need('total') == 412 * 205 + 538 * 198 + 297 * 214, f'total = {need("total")}. Пустые строки нужно пропускать.'
import ast as _ast
_sample = 'Уфа;7;113\n\nОмск;11;127\nСамара;3;149\n'
_seen = []
def _record(_fn):
    def _wrapped(*args, **kwargs):
        _seen.append(args[0] if args else next(iter(kwargs.values())))
        return _fn(*args, **kwargs)
    return _wrapped
class _Probe(_ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id == 'parse_line' and isinstance(node.ctx, _ast.Load):
            return _ast.copy_location(_ast.Call(func=_ast.Name(id='_record', ctx=_ast.Load()), args=[node], keywords=[]), node)
        return node
    def visit_Assign(self, node):
        self.generic_visit(node)
        if any(isinstance(t, _ast.Name) and t.id == 'text' for t in node.targets) and not any(isinstance(n, _ast.Name) and n.id == 'text' for n in _ast.walk(node.value)):
            override = _ast.parse('text = _probe_inputs.pop("text", text)').body[0]
            return [node, _ast.copy_location(override, node)]
        return node
    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if isinstance(node.target, _ast.Name) and node.target.id == 'text' and node.value is not None and not any(isinstance(n, _ast.Name) and n.id == 'text' for n in _ast.walk(node.value)):
            override = _ast.parse('text = _probe_inputs.pop("text", text)').body[0]
            return [node, _ast.copy_location(override, node)]
        return node
_env = {'__name__': '__main__', '_record': _record, 'text': _sample, '_probe_inputs': {'text': _sample}}
try:
    exec(compile(_ast.fix_missing_locations(_Probe().visit(_ast.parse(_code))), '<parse-probe>', 'exec'), _env)
except Exception as _e:
    raise AssertionError(f'На новой выгрузке с пустой строкой код не завершился: {_e}') from None
assert _env.get('total') == 7 * 113 + 11 * 127 + 3 * 149, 'На новой выгрузке total неверен: обработайте все непустые строки, не вписывайте сумму.'
assert all(line in _seen for line in _sample.splitlines() if line.strip()), 'Используйте parse_line для обработки каждой непустой строки. Подойдут цикл, map и генератор.'
```

### hint
Пустую строку легко узнать: после `strip()` от неё остаётся `""`. Обработайте строку, только если она не пустая: всё тело цикла — внутри `if line.strip() != "":`.

### hint
Внутри функции: `city, cups, price = line.split(";")`, затем верните список с `int(...)`.

### solution
```python
def parse_line(line):
    city, cups, price = line.split(";")
    return [city, int(cups), int(price)]

text = "Пермь;412;205\nКазань;538;198\n\nТюмень;297;214\n"
total = 0
for line in text.split("\n"):
    if line.strip() != "":
        city, cups, price = parse_line(line)
        total += cups * price
```

### explain
Пустая строка после `strip()` — это `""`, поэтому условие `line.strip() != ""` её пропускает. Короче то же самое пишут `if line.strip():` — пустая строка в условии считается ложью. Позже (в уроке про исключения) встретится и другая запись: `if not line.strip(): continue` — «пропусти остаток тела и переходи к следующей строке».
