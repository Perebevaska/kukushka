---
title: "Стиль кода: PEP 8"
lead: "Код читают чаще, чем пишут. Разбираем общий для Python стиль PEP 8 — имена, отступы, пробелы, длинные строки — и один раз приводим к нему код руками, чтобы потом понимать, что делает форматтер."
recap:
  - "PEP 8: имена — `snake_case`, константы — `ЗАГЛАВНЫМИ`, отступ 4 пробела, пробелы вокруг `=` и операторов, но `ndigits=2` в аргументе — слитно. Пробелы расставит форматтер, имена — ваша работа."
  - "Длинное выражение переносят внутри круглых скобок: Python не считает перенос концом строки, пока скобка не закрыта."
---

Функции вы уже пишете — урок «Функции». Теперь о том, как оформлять код, чтобы его было легко читать.

## Зачем общий стиль

Код читают чаще, чем пишут: коллега, ревьюер вашего проекта, вы сами через месяц. Если в одном файле встречаются `TotalRevenue`, `total_rev` и `totalrevenue`, отступы то по два пробела, то по четыре, а `if` то в одну строку, то в две, — читатель тратит внимание на форму вместо смысла. Поэтому у Python есть общий для всех стиль — **PEP 8** (*Python Enhancement Proposal* № 8, документ-соглашение о том, как оформлять код).

::: tip Аналогия
Отчёт по корпоративному шаблону: те же цифры, но заголовки, шрифты и таблицы на привычных местах, и глаз сразу находит нужное. Код «не по шаблону» тоже работает: PEP 8 — про удобство чтения, а не про правильность.
:::

## Пример руками: одна функция в двух стилях

Две версии одной функции — среднего чека. Обе работают и выводят одно и то же:

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

## Главные правила одной таблицей

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

Следить за пробелами руками на своём компьютере не придётся: пробелы, отступы и переносы умеет расставлять специальная программа — форматтер. О ней — в уроке «Своё рабочее место — uv и Jupyter» главы 2. Имена форматтер не трогает: `AvgCheck` останется `AvgCheck`, переименовать — решение человека. Поэтому правила полезно один раз пройти руками.

{{practice: spaces, snake}}

## Длинная строка: перенос внутри скобок

Строку длиннее 79–88 символов приходится прокручивать вбок, а в соседнем окне она не помещается. Python считает конец строки концом команды — но только если не осталось **открытой скобки**. Пока скобка не закрыта, перенос строки ничего не значит, и длинное выражение можно разложить на несколько строк:

```python
perm_revenue = 84460
kazan_revenue = 106524
tyumen_revenue = 63558
ufa_revenue = 71230
ekb_revenue = 98410

total_revenue = (
    perm_revenue + kazan_revenue + tyumen_revenue
    + ufa_revenue + ekb_revenue
)
print(total_revenue)
```

Внутри скобок отступ — тоже 4 пробела, а оператор `+` по PEP 8 ставят в начало новой строки: так сразу видно, что строка продолжает сумму. То же работает в вызове функции и в списке: аргументы и элементы можно переносить после запятой, не добавляя лишних скобок.

{{practice: long-line}}

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

{{practice: tidy, review}}

## Практика

## task: spaces | Расставьте пробелы | warmup

Код считает выручку Перми и её долю в выручке сети, но записан «в одну кашу». Расставьте пробелы по PEP 8: вокруг `=` присваивания и вокруг `*` и `/`, после каждой запятой; у именованного аргумента `ndigits=1` пробелов вокруг `=` быть не должно. Числа и расчёт не меняйте.

### starter
```python
cups=412
price=205
revenue=cups*price
share=round(revenue/1314000*100,ndigits = 1)
print(revenue,share)
```

### check
```python
import io as _io, tokenize as _tk
assert need('revenue') == 84460 and need('share') == 6.4, f'Расчёт изменился: revenue = {need("revenue")!r}, share = {need("share")!r}. Должно быть 84460 и 6.4 — меняются только пробелы.'
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
    if _t.string in ('*', '/', '+', '-') and _prev is not None and _prev.type in (_tk.NAME, _tk.NUMBER) or _t.string in ('*', '/', '+', '-') and _prev is not None and _prev.string == ')':
        assert _gap_l and _gap_r, f'{_where}: вокруг {_t.string} нужны пробелы с обеих сторон.'
    if _t.string == '=' and _depth > 0:
        assert not _gap_l and not _gap_r, f'{_where}: у именованного аргумента пробелов вокруг = нет: ndigits=1.'
    if _t.string == '=' and _depth == 0:
        assert _gap_l and _gap_r, f'{_where}: вокруг = в присваивании нужны пробелы.'
```

### hint
По таблице: `x = a * b` — пробелы вокруг `=` и арифметики, `f(a, b)` — пробел после запятой.

### hint
Единственное слитное `=` — в аргументе: `round(..., ndigits=1)`. Строка с долей целиком: `share = round(revenue / 1314000 * 100, ndigits=1)`.

### solution
```python
cups = 412
price = 205
revenue = cups * price
share = round(revenue / 1314000 * 100, ndigits=1)
print(revenue, share)
```

### explain
Пермь дала 84 460 ₽ — 6.4 % выручки сети. Пробелы ничего не изменили в расчёте, зато в последней строке теперь видно, где деление, где умножение, а где аргумент функции. Слитное `ndigits=1` — сигнал глазу: это не присваивание, а имя аргумента.

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

## task: long-line | Длинная сумма | base

Строка с итогом сети длиннее 79 символов. Перенесите выражение на несколько строк **внутри круглых скобок**, чтобы ни одна строка кода не была длиннее 79 символов. Обратную косую черту `\` для переноса не используйте. Итог не должен измениться.

### starter
```python
perm_revenue = 84460
kazan_revenue = 106524
tyumen_revenue = 63558
ufa_revenue = 71230
ekb_revenue = 98410
total_revenue = perm_revenue + kazan_revenue + tyumen_revenue + ufa_revenue + ekb_revenue
print(total_revenue)
```

### check
```python
_long = [(i, len(ln)) for i, ln in enumerate(_code.splitlines(), 1) if len(ln) > 79]
assert not _long, f'Слишком длинные строки (номер, длина): {_long}. По PEP 8 — не длиннее 79 символов.'
assert '\\' not in _code, 'Перенос через обратную косую черту не нужен: откройте круглую скобку, и Python сам поймёт, что выражение продолжается.'
assert need('total_revenue') == 424182, f'total_revenue = {need("total_revenue")!r}, а должно быть 424182. Перенос не должен терять слагаемые.'
assert 'total_revenue = (' in _code or 'total_revenue=(' in _code, 'Сумму нужно взять в круглые скобки: total_revenue = ( ... ).'
```

### hint
Сразу после `=` откройте скобку `(` и закончите строку. Слагаемые — на следующих строках с отступом 4 пробела, в конце — закрывающая `)` на отдельной строке.

### hint
```python
total_revenue = (
    perm_revenue + kazan_revenue + tyumen_revenue
    + ...
)
```

### solution
```python
perm_revenue = 84460
kazan_revenue = 106524
tyumen_revenue = 63558
ufa_revenue = 71230
ekb_revenue = 98410
total_revenue = (
    perm_revenue + kazan_revenue + tyumen_revenue
    + ufa_revenue + ekb_revenue
)
print(total_revenue)
```

### explain
Итог тот же — 424 182 ₽: пока скобка открыта, Python читает несколько строк как одно выражение. Исходная строка занимала 89 символов; после переноса каждая часть читается без прокрутки, а `+` в начале строки сразу показывает, что это продолжение суммы.

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
Логика не изменилась — функция по-прежнему возвращает 325.12, — а читается заметно легче: имя говорит, что считается, отступы показывают вложенность, пробелы отделяют операнды. Пробелы и отступы на работе расставляет форматтер, но имена ни один форматтер за вас не придумает. Если бы вы переименовали функцию только в `def`, а в вызове оставили `AvgCheck(...)`, код упал бы с `NameError: name 'AvgCheck' is not defined` — переименование всегда делают во всех местах сразу.

## task: review | Найдите нарушения | plus

Коллега прислал код на проверку. Все строки работают, но некоторые нарушают PEP 8. Запишите в список `bad` номера строк с нарушениями.

```text
1  VAT_RATE = 0.2
2  avgCheck = 325.12
3  vat = round(avg_check * VAT_RATE / (1 + VAT_RATE), ndigits = 2)
4  cities = ["Пермь", "Казань", "Тюмень"]
5  if vat > 50: print("крупный НДС")
6  month_total = sum(daily_revenue)
```

### starter
```python
bad = []
```

### check
```python
_b = need('bad')
assert isinstance(_b, (list, tuple, set)), 'bad — список номеров строк, например [1, 4].'
_got = sorted(int(x) for x in _b)
_hint = {
    1: 'Строка 1 в порядке: константа заглавными, пробелы вокруг =.',
    2: 'Строка 2: avgCheck — имя не в snake_case, нужно avg_check.',
    3: 'Строка 3: у именованного аргумента ndigits = 2 лишние пробелы — нужно ndigits=2.',
    4: 'Строка 4 в порядке: пробел после каждой запятой.',
    5: 'Строка 5: if и действие в одной строке — print нужно перенести на новую строку с отступом.',
    6: 'Строка 6 в порядке: имена в snake_case.',
}
for _n in [1, 2, 3, 4, 5, 6]:
    if (_n in _got) != (_n in (2, 3, 5)):
        raise AssertionError(_hint[_n] + f' Сейчас bad = {_got}.')
assert _got == [2, 3, 5], f'bad = {_got}. Каждый номер — один раз.'
```

### hint
Пройдите по таблице правил строка за строкой: имена, пробелы вокруг `=` в присваивании и в аргументе, запятые, `if` в одну строку.

### hint
Нарушений три. Одно — в имени, одно — в пробелах у именованного аргумента, одно — в записи `if`.

### solution
```python
bad = [2, 3, 5]
```

### explain
Строка 2 — имя в стиле других языков (`avgCheck` → `avg_check`). Строка 3 — пробелы вокруг `=` у именованного аргумента (`ndigits=2`). Строка 5 — условие и действие в одной строке. Строки 1, 4 и 6 оформлены верно: `VAT_RATE` — константа, поэтому заглавными. Найти нарушения глазами — тот же навык, что нужен на ревью чужого кода: форматтер исправил бы пробелы в строках 3 и 5, но имя в строке 2 осталось бы прежним.
