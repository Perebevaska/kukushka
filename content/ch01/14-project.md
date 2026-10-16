---
title: "Мини-проект: отчёт по заказам"
lead: "Руководитель сети просит короткий отчёт за сентябрь. Собираем его шаг за шагом из выгрузки orders.csv — всем, что было в главе: файлы, исключения, множества, словари, сортировки и функции."
files: [orders.csv]
recap:
  - "Анализ начинается с загрузки и чистки: привести типы, отбросить битые строки, убрать дубли — и посчитать, сколько выброшено."
  - "Сначала цифры, потом слова: KPI → разрезы (города, напитки, дни недели) → выводы."
  - "Повторяющийся расчёт — в функцию: тогда отчёт за октябрь — это один вызов с другим файлом."
  - "Всё, что вы сделали циклами и словарями, в pandas будет короче. Но логика остаётся той же."
---

## Задача

> Нужен отчёт по сети за сентябрь: сколько заказов и денег, какой средний чек, какой город лучший, что пьют чаще всего и в какой день недели приходит больше всего выручки. Выгрузку из кассы прикладываю — `orders.csv`. Если в данных есть проблемы — напиши, какие.

Так обычно и выглядит работа аналитика: задача сформулирована словами, а данные не идеальны. Вот файл:

```python
with open("orders.csv", encoding="utf-8") as f:
    print(f.read()[:400])
```

Столбцы: `order_id` — номер заказа, `date` — дата, `city` — город, `drink` — напиток, `amount` — сумма заказа в рублях.

## План

1. **Загрузить и почистить.** Суммы — в числа, битые строки — отбросить и посчитать.
2. **Найти дубли** по номеру заказа и оставить по одному.
3. **Ключевые цифры:** заказы, выручка, средний чек.
4. **Разрезы:** города, напитки, дни недели.
5. **Собрать текст отчёта** функцией, чтобы его можно было повторить для любого месяца.

::: quiz
В выгрузке одна строка заказа повторилась дважды. Где в плане правильнее её убрать?

- [x] До всех расчётов — сразу после загрузки и чистки
  > Дубль завышает и выручку, и число заказов, и рейтинг городов. Убрав его первым, вы исправите все цифры отчёта сразу.
- [ ] После расчёта выручки — вычесть его сумму
  > Тогда придётся править каждую цифру отдельно, и легко что-то пропустить.
- [ ] В самом конце, в разделе «Качество данных»
  > В отчёте стоит написать, сколько дублей нашли, но убирать их нужно до расчётов.
- [ ] Не трогать: один дубль на итог не влияет
  > Влияет: заказ посчитается дважды. К тому же дублей может оказаться больше.
:::

## Разберём вместе: путь строк от файла до отчёта

Прежде чем писать код, прикинем, что станет со строками выгрузки на каждом шаге:

| шаг | строк | что произошло |
|---|---|---|
| в файле | 41 | все строки после заголовка |
| после чистки сумм | 38 | 3 строки с битой суммой отброшены: пустая, `—` и `1 250` |
| после удаления дублей | 37 | 1 заказ выгружен дважды |
| в отчёт | 37 | на них считаются все цифры |

::: figure report-funnel
Сколько строк остаётся после каждого шага подготовки и на чём держатся итоговые цифры отчёта.
:::

1. Каждое число в отчёте («37 заказов, 16 370 ₽») опирается на последнюю строку таблицы.
2. Если бы мы не убрали дубль, выручка была бы завышена на сумму этого заказа — а средний чек почти не изменился бы: 16 820 / 38 ≈ 443 ₽ против 442 ₽. По среднему чеку дубль не заметить — только по журналу.
3. Строки 2–3 таблицы — готовый ответ на вопрос руководителя «есть ли в данных проблемы»: 3 битых суммы и 1 дубль.

Что получилось: журнал «было → стало» пишется параллельно с кодом и попадает в отчёт. Без него на вопрос «почему у тебя 37 заказов, а в кассе 41?» ответить нечего.

::: warn Типичные ошибки проекта
- **Дубли до чистки.** Считайте дубли после чистки сумм: иначе битая строка может оказаться и «дублем», и «битой», и журнал «было → стало» не сойдётся. Фиксируйте, что ушло на каком шаге.
- **Средний чек по всем строкам.** Битые и повторные строки в знаменателе занижают или искажают чек.
- **Лучший день по числу заказов.** Вопрос — про выручку; самый «людный» день и самый «денежный» могут различаться.
- **Отчёт с ручными цифрами.** Если число вписано руками, отчёт за октябрь окажется с сентябрьскими цифрами.
:::

Каждый шаг — отдельная задача ниже. Чтобы ошибка на одном шаге не мешала следующим, перед каждой задачей курс сам готовит данные «как будто предыдущие шаги сделаны правильно»: переменные `orders` и `clean` уже будут на месте — там, где это указано в условии.

::: tip
Это повторение всей главы. Если на каком-то шаге трудно — откройте урок, на который он опирается (указан в подсказке), и шпаргалку. Подсказки здесь можно брать смело.
:::

::: sql
Весь проект на SQL уложился бы в несколько запросов: `SELECT COUNT(*), SUM(amount)…`, `GROUP BY city`, `GROUP BY drink ORDER BY COUNT(*) DESC LIMIT 3`, `GROUP BY EXTRACT(DOW FROM date)`. Полезно держать их в голове: на Python вы делаете то же самое.
:::

## Практика

## task: load | Шаг 1. Загрузка и чистка | base

Загрузите `orders.csv` в список словарей `orders`: `amount` — `int`, `date` — `dt.date`. Строки, где сумму не удалось превратить в число, в `orders` не кладите, а посчитайте в `n_bad`. Как и в уроке «Файлы, CSV и модули», `1 250` с пробелом тоже считаем проблемой выгрузки: формат нарушен, поэтому строку не чиним, а показываем в журнале.

### starter
```python
import csv
import datetime as dt

```

### check
```python
import csv as _csv, datetime as _dt
good, bad = [], 0
for r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        int(r['amount']); good.append(r)
    except ValueError:
        bad += 1
o = need('orders', list)
assert len(o) == len(good), f'В orders {len(o)} заказов, а хороших строк {len(good)}.'
assert need('n_bad') == bad, f'n_bad = {need("n_bad")}, а битых строк {bad}.'
assert all(isinstance(x['amount'], int) for x in o), 'amount должен быть int.'
assert all(isinstance(x['date'], _dt.date) for x in o), 'date должна быть dt.date.'
```

### hint
Урок «Файлы, CSV и модули», задача «Функция загрузки»: `csv.DictReader`, в `try` — `int(row["amount"])`, в `except ValueError` — счётчик и `continue`.

### hint
Дату превращайте после успешного `int`: `row["date"] = dt.date.fromisoformat(row["date"])`, затем `orders.append(row)`.

### solution
```python
import csv
import datetime as dt
orders = []
n_bad = 0
with open("orders.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            row["amount"] = int(row["amount"])
        except ValueError:
            n_bad += 1
            continue
        row["date"] = dt.date.fromisoformat(row["date"])
        orders.append(row)
```

### explain
Из 41 строки загрузилось 38, битых сумм — 3. Счётчик `n_bad` — первая строка будущего раздела «проблемы данных».

## task: dedupe | Шаг 2. Дубли | base

В `orders` уже лежат загруженные заказы. Найдите повторённые номера заказов: в `n_dupes` — сколько лишних строк, в `clean` — список заказов, где каждый `order_id` встречается один раз (оставляйте первое вхождение, порядок сохраните).

### setup
```python
import csv as _csv, datetime as _dt
orders = []
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    orders.append(_r)
```

### starter
```python
# orders уже загружен
print(len(orders))

```

### check
```python
import csv as _csv, datetime as _dt
# эталон строим заново из файла: правки orders в решении не должны влиять на проверку
_orig = []
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    _orig.append(_r)
_first = {}
for _o in _orig:
    _first.setdefault(_o['order_id'], _o)
ids = [o['order_id'] for o in _orig]
c = need('clean', list)
assert [o['order_id'] for o in c] == list(_first), 'В clean каждый номер заказа должен встречаться один раз, в исходном порядке.'
for _got, _want in zip(c, _first.values()):
    assert _got == _want, (f'Заказ {_want["order_id"]} в clean отличается от первого вхождения в выгрузке: '
                           f'{_got} вместо {_want}. Дедупликация должна убирать лишние строки, не меняя сами записи.')
assert need('n_dupes') == len(ids) - len(set(ids)), f'n_dupes = {need("n_dupes")}, а лишних строк {len(ids) - len(set(ids))}.'
```

### hint
Урок «Кортежи и множества»: множество `seen`. Если номер уже в `seen` — это дубль; иначе добавляем заказ в `clean` и номер в `seen`.

### hint
Счётчик дублей: `n_dupes += 1` в ветке «уже видели»; порядок `clean` сохранится сам, потому что идём по `orders` по порядку.

### solution
```python
clean = []
seen = set()
n_dupes = 0
for o in orders:
    if o["order_id"] in seen:
        n_dupes += 1
    else:
        seen.add(o["order_id"])
        clean.append(o)
```

### explain
Один заказ выгружен дважды — после чистки 37 уникальных заказов. «Оставлять первое вхождение» — правило, которое нужно назвать явно: если бы копии различались суммой, выбор копии изменил бы выручку.

## task: kpi | Шаг 3. Ключевые цифры | base

По чистым заказам `clean` посчитайте `n_orders`, `revenue` и `avg_check` (средний чек, округлённый до целого).

### setup
```python
import csv as _csv, datetime as _dt
clean, _seen = [], set()
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    if _r['order_id'] in _seen:
        continue
    _seen.add(_r['order_id'])
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    clean.append(_r)
```

### starter
```python
# clean уже готов
```

### check
```python
a = [o['amount'] for o in clean]
assert need('n_orders') == len(a), f'n_orders = {need("n_orders")}.'
assert need('revenue') == sum(a), f'revenue = {need("revenue")}.'
assert need('avg_check') == round(sum(a) / len(a)), f'avg_check = {need("avg_check")}.'
```

### hint
`len(clean)`, `sum(o["amount"] for o in clean)` — урок «Генераторы списков, zip, sorted».

### hint
`avg_check = round(revenue / n_orders)`.

### solution
```python
n_orders = len(clean)
revenue = sum(o["amount"] for o in clean)
avg_check = round(revenue / n_orders)
```

### explain
37 заказов на 16 370 ₽, средний чек — 442 ₽. Это три главные цифры отчёта, и все они посчитаны по чистым данным.

## task: cities | Шаг 4. Города | base

Получите `city_rank` — список пар `(город, выручка)`, отсортированный по выручке от большей к меньшей.

### setup
```python
import csv as _csv, datetime as _dt
clean, _seen = [], set()
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    if _r['order_id'] in _seen:
        continue
    _seen.add(_r['order_id'])
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    clean.append(_r)
```

### starter
```python
# clean уже готов
```

### check
```python
want = {}
for o in clean:
    want[o['city']] = want.get(o['city'], 0) + o['amount']
want = sorted(want.items(), key=lambda kv: kv[1], reverse=True)
assert [tuple(x) for x in need('city_rank')] == want, f'city_rank = {need("city_rank")}, а должно быть {want}.'
```

### hint
Сначала словарь «город → сумма» (урок «Словари — GROUP BY своими руками»), потом `sorted(d.items(), key=lambda kv: kv[1], reverse=True)` (урок «Генераторы списков, zip, sorted»).

### hint
Накопление: `d[o["city"]] = d.get(o["city"], 0) + o["amount"]` для каждого `o` из `clean`.

### solution
```python
by_city = {}
for o in clean:
    by_city[o["city"]] = by_city.get(o["city"], 0) + o["amount"]
city_rank = sorted(by_city.items(), key=lambda kv: kv[1], reverse=True)
```

### explain
Казань — 5 770, Пермь — 5 270, Уфа — 3 020, Тюмень — 2 310. Список пар удобен для отчёта: порядок уже готов, и название города не отрывается от его выручки.

## task: drinks | Шаг 5. Что пьют | base

Получите `top3` — три самых частых напитка **по числу заказов**: список пар `(напиток, количество)` по убыванию. При равенстве количества — по алфавиту.

### setup
```python
import csv as _csv, datetime as _dt
clean, _seen = [], set()
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    if _r['order_id'] in _seen:
        continue
    _seen.add(_r['order_id'])
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    clean.append(_r)
```

### starter
```python
# clean уже готов
```

### check
```python
cnt = {}
for o in clean:
    cnt[o['drink']] = cnt.get(o['drink'], 0) + 1
want = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
assert [tuple(x) for x in need('top3')] == want, f'top3 = {need("top3")}, а должно быть {want}.'
_ctrl = [{'drink': d} for d in ['Флэт уайт', 'Флэт уайт', 'Раф', 'Раф', 'Американо', 'Американо', 'Латте']]
_ns = {'clean': _ctrl}
exec(_code, _ns)
_got = [tuple(x) for x in _ns.get('top3', [])]
assert _got == [('Американо', 2), ('Раф', 2), ('Флэт уайт', 2)], f'На контрольных данных с равными количествами получилось {_got}. При равенстве нужен алфавит: key=lambda kv: (-kv[1], kv[0]).'
```

### hint
Подсчёт словарём, затем сортировка. Чтобы при равенстве сортировать по алфавиту, признак может быть кортежем: `key=lambda kv: (-kv[1], kv[0])` — минус даёт убывание по количеству.

### hint
Почему минус: `sorted` по умолчанию сортирует по возрастанию, а нам нужно количество по убыванию и при этом названия по возрастанию. Минус перед числом переворачивает только первую часть ключа: пары `(-5, "Латте")` и `(-5, "Капучино")` сравнятся по второй части, и «Капучино» окажется раньше.

### solution
```python
counts = {}
for o in clean:
    counts[o["drink"]] = counts.get(o["drink"], 0) + 1
top3 = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
```

### explain
Сортировка по кортежу сравнивает сначала первые элементы, при равенстве — вторые. Это как `ORDER BY cnt DESC, drink ASC`.

## task: weekday | Шаг 6. День недели | plus

Найдите `best_day` — **название** дня недели с наибольшей выручкой и `best_day_revenue` — эту выручку. Названия дней даны в списке `DAYS` (индекс = `weekday()`).

### setup
```python
import csv as _csv, datetime as _dt
clean, _seen = [], set()
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    if _r['order_id'] in _seen:
        continue
    _seen.add(_r['order_id'])
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    clean.append(_r)
```

### starter
```python
DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
# clean уже готов, date — это dt.date

```

### check
```python
w = {}
for o in clean:
    k = o['date'].weekday()
    w[k] = w.get(k, 0) + o['amount']
b = max(w, key=w.get)
D = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
assert need('best_day') == D[b], f'best_day = {need("best_day")!r}, а должно быть {D[b]!r}.'
assert need('best_day_revenue') == w[b], f'best_day_revenue = {need("best_day_revenue")}.'
```

### hint
Словарь «номер дня → сумма» по `o["date"].weekday()`, потом `max(d, key=d.get)` и `DAYS[номер]`.

### hint
`best = max(d, key=d.get)`, `best_day = DAYS[best]`, `best_day_revenue = d[best]`.

### solution
```python
DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
by_day = {}
for o in clean:
    k = o["date"].weekday()
    by_day[k] = by_day.get(k, 0) + o["amount"]
best = max(by_day, key=by_day.get)
best_day = DAYS[best]
best_day_revenue = by_day[best]
```

### explain
Самый выручальный день — среда (5 070 ₽), почти вровень с субботой (4 630 ₽). На месячной выгрузке из 37 заказов один день недели встречается 4–5 раз, так что разница между ними — повод для гипотезы, а не вывод.

## task: report | Шаг 7. Текст отчёта | plus

Напишите `build_report(orders)`: функция получает чистые заказы и **возвращает** текст отчёта из четырёх строк (через `\n`), например:

```text
Заказов: 37
Выручка: 16 370 ₽
Средний чек: 442 ₽
Лучший город: Казань (5 770 ₽)
```

Числа считайте внутри функции из `orders` — тогда функция подойдёт для любого месяца. Разделитель тысяч — пробел: `f"{x:,}"` ставит запятую (`16,370`), поэтому её заменяют: `f"{x:,}".replace(",", " ")` → `16 370`. Разделитель появляется только у чисел от 1000, так что «442 ₽» остаётся как есть.

### setup
```python
import csv as _csv, datetime as _dt
clean, _seen = [], set()
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        continue
    if _r['order_id'] in _seen:
        continue
    _seen.add(_r['order_id'])
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    clean.append(_r)
```

### starter
```python
def build_report(orders):
    ...

print(build_report(clean))
```

### check
```python
def _want(orders):
    rev = sum(o['amount'] for o in orders)
    bc = {}
    for o in orders:
        bc[o['city']] = bc.get(o['city'], 0) + o['amount']
    best = max(bc, key=bc.get)
    f = lambda x: f'{x:,}'.replace(',', ' ')
    return '\n'.join([f'Заказов: {len(orders)}', f'Выручка: {f(rev)} ₽', f'Средний чек: {f(round(rev / len(orders)))} ₽',
                      f'Лучший город: {best} ({f(bc[best])} ₽)'])
fn = need('build_report')
got = fn(clean)
assert got is not None, 'Функция ничего не возвращает — нужен return, а не print.'
assert got.strip() == _want(clean), f'Сейчас отчёт такой:\n{got}\n\nа ожидался:\n{_want(clean)}'
part = clean[:10]
assert fn(part).strip() == _want(part), 'На другом наборе заказов отчёт не совпал — проверьте, что все числа считаются из параметра orders.'
```

### hint
Посчитайте внутри функции выручку, словарь по городам и лучший город (шаги 3–4). Строки соберите f-строками в список и склейте `"\n".join(lines)`.

### hint
Разделитель тысяч: `f"{x:,}".replace(",", " ")` — урок «Строки и f-строки».

### solution
```python
def build_report(orders):
    def rub(x):
        return f"{x:,}".replace(",", " ") + " ₽"
    revenue = sum(o["amount"] for o in orders)
    by_city = {}
    for o in orders:
        by_city[o["city"]] = by_city.get(o["city"], 0) + o["amount"]
    best = max(by_city, key=by_city.get)
    lines = [
        f"Заказов: {len(orders)}",
        f"Выручка: {rub(revenue)}",
        f"Средний чек: {rub(round(revenue / len(orders)))}",
        f"Лучший город: {best} ({rub(by_city[best])})",
    ]
    return "\n".join(lines)

print(build_report(clean))
```

### explain
Внутри функции можно объявить ещё одну маленькую функцию (`rub`) — она видна только внутри `build_report`.

## task: file | Шаг 8. Отчёт в файл и проблемы данных | star

Запишите в файл `report.md` отчёт для руководителя: заголовок `# Отчёт за сентябрь`, пустая строка, затем текст из `build_report(clean)`, пустая строка и раздел `## Качество данных` со строками `- Битых строк: N` и `- Дублей: M`. Числа `n_bad` и `n_dupes` даны.

### setup
```python
import csv as _csv, datetime as _dt
clean, _seen = [], set()
n_bad = n_dupes = 0
for _r in _csv.DictReader(open('orders.csv', encoding='utf-8')):
    try:
        _r['amount'] = int(_r['amount'])
    except ValueError:
        n_bad += 1
        continue
    if _r['order_id'] in _seen:
        n_dupes += 1
        continue
    _seen.add(_r['order_id'])
    _r['date'] = _dt.date.fromisoformat(_r['date'])
    clean.append(_r)

def build_report(orders):
    rev = sum(o['amount'] for o in orders)
    bc = {}
    for o in orders:
        bc[o['city']] = bc.get(o['city'], 0) + o['amount']
    best = max(bc, key=bc.get)
    f = lambda x: f'{x:,}'.replace(',', ' ')
    return '\n'.join([f'Заказов: {len(orders)}', f'Выручка: {f(rev)} ₽', f'Средний чек: {f(round(rev / len(orders)))} ₽',
                      f'Лучший город: {best} ({f(bc[best])} ₽)'])
```

### starter
```python
# clean, n_bad, n_dupes и build_report уже есть
print(n_bad, n_dupes)

```

### check
```python
import os
assert os.path.exists('report.md'), 'Файл report.md не создан.'
got = [l.rstrip() for l in open('report.md', encoding='utf-8').read().strip().split('\n')]
want = ['# Отчёт за сентябрь', ''] + build_report(clean).split('\n') + ['', '## Качество данных', f'- Битых строк: {n_bad}', f'- Дублей: {n_dupes}']
assert got == want, 'Содержимое report.md не совпадает с ожидаемым:\n' + '\n'.join(want)
```

### hint
Соберите все строки в список, склейте через `"\n".join(...)` и запишите одним `f.write(...)` в режиме `"w"`.

### hint
Пустые строки в отчёте — это пустые элементы `""` в списке: при склейке через `"\n"` они дают пустую строку между разделами. Числа подставляйте f-строкой: `f"- Битых строк: {n_bad}"`. Чтобы проверить себя, после записи прочитайте файл обратно и напечатайте его.

### solution
```python
lines = ["# Отчёт за сентябрь", "", build_report(clean), "", "## Качество данных",
         f"- Битых строк: {n_bad}", f"- Дублей: {n_dupes}"]
with open("report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(open("report.md", encoding="utf-8").read())
```

### explain
Markdown — простая разметка: `#` — заголовок, `-` — пункт списка. Такой файл красиво откроется на GitHub, в Notion и в большинстве редакторов. Вы только что автоматизировали отчёт: в следующем месяце достаточно запустить код на новой выгрузке.
