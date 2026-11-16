---
title: "Мини-проект: отчёт по заказам"
lead: "Руководитель сети просит короткий отчёт за сентябрь. Собираем его шаг за шагом из выгрузки orders.csv — всем, что было в главе: файлы, исключения, множества, словари, сортировки и функции."
files: [orders.csv]
recap:
  - "Анализ начинается с загрузки и чистки: привести типы, отбросить битые строки, убрать дубли — и посчитать, сколько выброшено."
  - "Сначала цифры, потом слова: KPI → разрезы (города, напитки, дни недели) → выводы."
  - "Функция собирает отчёт по списку принятых заказов. Для нового месяца запустите ту же программу с новой выгрузкой orders.csv."
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
5. **Передать отчёт.** На шаге 7 функция возвращает текст по уже принятым заказам. На шаге 8 начните с исходного CSV за нужный месяц, добавьте журнал нечитаемых сумм, точных повторов и конфликтующих записей. Запишите файл и откройте его для сверки.

::: quiz
В выгрузке одна и та же строка заказа встречается два раза. Где в плане правильнее её убрать?

- [x] До всех расчётов — сразу после загрузки и чистки
  > Повтор Z-1038 прибавил бы один заказ и 450 ₽ к выручке Перми и сети. Уберите его до группировки, чтобы учесть каждый заказ один раз.
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

1. Какую сумму можно назвать руководителю? По 37 принятым заказам учтено 16 370 ₽. В одной строке сумма пустая, в другой стоит прочерк. В третьей записано `1 250` с пробелом. У владельца выгрузки можно уточнить, означает ли эта запись 1 250 ₽. Пока полная выручка за месяц неизвестна.
2. Если бы мы не убрали дубль, выручка была бы завышена на сумму этого заказа — а средний чек почти не изменился бы: 16 820 / 38 ≈ 443 ₽ против 442 ₽. По среднему чеку дубль не заметить — только по журналу.
3. Строки 2–3 таблицы — готовый ответ на вопрос руководителя «есть ли в данных проблемы»: 3 битых суммы и 1 дубль.

По этому журналу руководитель сможет сверить 41 строку кассовой выгрузки с 37 заказами в отчёте.

::: warn Типичные ошибки проекта
- **Дубли до чистки.** Считайте дубли после чистки сумм: иначе битая строка может оказаться и «дублем», и «битой», и журнал «было → стало» не сойдётся. Фиксируйте, что ушло на каком шаге.
- **Средний чек по всем строкам.** Битые и повторные строки в знаменателе занижают или искажают чек.
- **Лучший день по числу заказов.** Вопрос — про выручку; самый «людный» день и самый «денежный» могут различаться.
- **Отчёт с ручными цифрами.** Если число вписано руками, отчёт за октябрь окажется с сентябрьскими цифрами.
:::

На шагах 2–7 курс готовит промежуточные данные, чтобы вы могли отработать каждый расчёт отдельно. На шаге 8 у вас будет только исходный CSV. Вы соедините свой код и откроете готовый файл глазами руководителя.

::: tip
Это повторение всей главы. Если на каком-то шаге трудно — откройте урок, на который он опирается (указан в подсказке), и шпаргалку. Подсказки здесь можно брать смело.
:::

::: sql
Основным расчётам соответствуют `COUNT(*)`, `SUM(amount)` и группировка `GROUP BY city`. Три напитка в PostgreSQL выбираются через `GROUP BY drink ORDER BY COUNT(*) DESC, drink ASC LIMIT 3`. Второй ключ задаёт порядок названий при равенстве. Порядок строк зависит от правил сравнения: здесь используем обычное сравнение Python, а в базе оно может зависеть от настроек сортировки. Для группировки выручки по дням недели в Python используем `date.weekday()`, в PostgreSQL — `EXTRACT(ISODOW FROM date) - 1`. В обоих случаях понедельник получит номер 0, воскресенье — 6.
:::

## Практика

## task: load | Шаг 1. Загрузка и чистка | base

Загрузите `orders.csv` в список словарей `orders` в исходном порядке. Преобразуйте `amount` в `int`, а `date` в `dt.date`. Сохраните значения остальных полей. Строки, где сумму не удалось превратить в число, в `orders` не кладите, а посчитайте в `n_bad`. Как и в уроке «Файлы, CSV и модули», `1 250` с пробелом тоже считаем проблемой выгрузки: формат нарушен, поэтому строку не чиним, а показываем в журнале.

### starter
```python
import csv
import datetime as dt

```

### check
```python
import csv as _csv
import datetime as _dt

good, bad = [], 0
with open('orders.csv', encoding='utf-8', newline='') as source:
    for row in _csv.DictReader(source):
        try:
            row['amount'] = int(row['amount'])
        except ValueError:
            bad += 1
            continue
        row['date'] = _dt.date.fromisoformat(row['date'])
        good.append(row)
loaded = need('orders', list)
assert len(loaded) == len(good), f'В orders {len(loaded)} записей, а годных строк в CSV {len(good)}.'
assert need('n_bad') == bad, f'n_bad = {need("n_bad")}, а битых строк {bad}.'
for expected, actual in zip(good, loaded):
    order_id = expected['order_id']
    assert isinstance(actual, dict), f'Заказ {order_id} должен быть словарём.'
    for field, value in expected.items():
        assert field in actual, f'У заказа {order_id} отсутствует поле {field}.'
        assert actual[field] == value and type(actual[field]) is type(value), (
            f'Заказ {order_id}, поле {field}: получено {actual[field]!r}, по CSV ожидается {value!r}.')
    assert actual.keys() == expected.keys(), f'Проверьте названия полей заказа {order_id} по заголовку CSV.'
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

В `orders` уже лежат загруженные заказы. Найдите повторённые номера заказов: в `n_dupes` — сколько лишних строк, в `clean` — список заказов, где каждый `order_id` встречается один раз. Оставляйте **первую строку с читаемой суммой** в исходном порядке: битые суммы уже исключены в шаге 1. Даже если более поздняя строка отличается суммой, датой, городом или напитком, здесь сохраняйте первую. Это учебное правило отбора, а не доказательство верности первой записи.

Точный повтор совпадает со всей принятой записью; конфликт — тот же ID, но хотя бы одно другое поле отличается. Пока посчитайте оба случая в `n_dupes`. В шаге 8 отдельно предупредите получателя о конфликтах.

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
# include-check: ch01_order_sample.py
_other = rerun_with(orders=[row.copy() for row in _sample_duplicates])
assert _other.get('clean') == [_sample_duplicates[0], _sample_duplicates[1]], (
    'На другом месяце оставьте первую читаемую запись ID, даже если у следующей другая сумма или дата.')
assert _other.get('n_dupes') == 2, 'Считайте каждую лишнюю читаемую строку, включая конфликтующую.'
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
_amounts = tuple(row['amount'] for row in clean)
```

### starter
```python
# clean уже готов
```

### check
```python
assert need('n_orders') == len(_amounts), f'n_orders = {need("n_orders")}.'
assert need('revenue') == sum(_amounts), f'revenue = {need("revenue")}.'
assert need('avg_check') == round(sum(_amounts) / len(_amounts)), f'avg_check = {need("avg_check")}.'
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
_city_amounts = tuple((row['city'], row['amount']) for row in clean)
```

### starter
```python
# clean уже готов
```

### check
```python
want = {}
for city, amount in _city_amounts:
    want[city] = want.get(city, 0) + amount
rank = [tuple(x) for x in need('city_rank')]
assert len(rank) == len(want) and dict(rank) == want, 'Проверьте города и сумму для каждого из них.'
amounts = [amount for city, amount in rank]
assert amounts == sorted(amounts, reverse=True), 'Расположите города по убыванию выручки.'
# include-check: ch01_order_sample.py
other = rerun_with(clean=_sample_orders)
assert [tuple(pair) for pair in other.get('city_rank', [])] == [('Омск', 700), ('Киров', 170)], (
    'Город с большим числом заказов может получить меньше денег. Упорядочьте города по сумме выручки.')
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

Составьте `top3` — три пары `(напиток, число заказов)` по убыванию числа заказов. При равенстве сравните названия обычным способом Python: «Ёжевичный чай» в таком порядке идёт перед «Американо». По одному заказу получили «Дарджилинг», «Бабл-ти», «Американо» и «Ёжевичный чай». Запишите свою тройку, затем проверьте её кодом.

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
_drink_names = tuple(row['drink'] for row in clean)
```

### starter
```python
# clean уже готов
```

### check
```python
cnt = {}
for drink in _drink_names:
    cnt[drink] = cnt.get(drink, 0) + 1
want = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
assert [tuple(x) for x in need('top3')] == want, f'top3 = {need("top3")}, а должно быть {want}.'
_names = ['Дарджилинг', 'Бабл-ти', 'Американо', 'Ёжевичный чай']
_ctrl = [dict(order_id=f'T-{i}', date=_dt.date(2027, 2, 1), city='Пермь', drink=name, amount=300)
         for i, name in enumerate(_names, 1)]
_ns = rerun_with(clean=_ctrl)
_got = [tuple(x) for x in _ns.get('top3', [])]
assert _got == [('Ёжевичный чай', 1), ('Американо', 1), ('Бабл-ти', 1)], f'На контрольных данных с равными количествами получилось {_got}. При равенстве используйте обычное сравнение Python: «Ё» перед «А», key=lambda kv: (-kv[1], kv[0]).'
```

### hint
Подсчёт словарём, затем сортировка. Чтобы при равенстве сравнивать названия по правилам Python, признак может быть кортежем: `key=lambda kv: (-kv[1], kv[0])` — минус даёт убывание по количеству.

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
Сортировка по кортежу сравнивает сначала первые элементы, при равенстве — вторые. Для четырёх равных частот получатся «Ёжевичный чай», «Американо», «Бабл-ти». «Дарджилинг» останется четвёртым. В SQL это тот же принцип, что у `ORDER BY cnt DESC, drink ASC`; порядок самих строк зависит от настройки сортировки.

## task: weekday | Шаг 6. День недели | plus

Найдите `best_day` — **название** дня недели с наибольшей выручкой и `best_day_revenue` — эту выручку. Названия дней даны в списке `DAYS` (индекс = `weekday()`). При равенстве сумм можно указать любой день с максимальной выручкой.

Сохраните расчёт вместе со списком `DAYS`. В шаге 7 из этих двух значений вы соберёте последнюю строку отчёта.

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
_weekday_amounts = tuple((row['date'].weekday(), row['amount']) for row in clean)
```

### starter
```python
DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
# clean уже готов, date — это dt.date

```

### check
```python
w = {}
for day, amount in _weekday_amounts:
    w[day] = w.get(day, 0) + amount
maximum = max(w.values())
D = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
assert need('best_day') in {D[day] for day, amount in w.items() if amount == maximum}, 'Проверьте день максимальной выручки.'
assert need('best_day_revenue') == maximum, f'best_day_revenue = {need("best_day_revenue")}.'
# include-check: ch01_order_sample.py
other = rerun_with(clean=_sample_orders, DAYS=D)
assert (other.get('best_day'), other.get('best_day_revenue')) == ('вторник', 700), (
    'Сравните суммы по дням. Один заказ на 700 ₽ приносит больше, чем два заказа на 50 и 120 ₽.')
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
Больше всего учтено по средам (5 070 ₽), затем по субботам (4 630 ₽). Принятые заказы охватывают три разные среды и четыре субботы. Эти суммы описывают данную выгрузку. Чтобы судить об обычной среде, понадобятся сопоставимые данные за большее число недель.

## task: report | Шаг 7. Текст отчёта | plus

Вернитесь к письму руководителя. На каких данных основана выручка? Что чаще заказывали? Какой день принёс больше всего денег? Напишите `build_report(orders)`, которая получает **список принятых заказов за один месяц** и возвращает текст. Каждый ответ поместите в отдельную подписанную строку, как в примере.

1. **Запустите заготовку.** На сайте нажмите «Запустить», в блокноте выполните ячейку и посмотрите вывод над результатом проверки. Появятся первые две строки образца ниже. В этой карточке список `clean` уже подготовлен.
2. Возьмите свой расчёт выручки и среднего чека [из шага 3](#task-kpi). Поместите его внутрь функции перед `return`. Там список заказов называется `orders`. Добавьте две подписи с суммами в список `lines` через `append` и запустите код ещё раз. Сверьте первые четыре строки.
3. Так же добавьте по одной строке для [города](#task-cities), [напитков](#task-drinks) и [дня недели](#task-weekday). Добавьте число заказов остальных напитков: `len(orders) - sum(count for drink, count in top3)`. Когда все восемь строк готовы, проверьте задачу.

```text
# Отчёт за 2026-09
Принято заказов: 37
Учтённая выручка: 16 370 ₽
Средний чек: 442 ₽
Лучший город: Казань (5 770 ₽)
Топ-3 напитка по числу принятых заказов: Американо (9), Раф (8), Флэт уайт (8)
Заказов остальных напитков: 12
День с наибольшей выручкой: среда (5 070 ₽)
```

Год и месяц возьмите из даты заказа. Подойдёт и «Отчёт за сентябрь 2026». Суммы можно писать с пробелами между тысячами или без них, менять порядок показателей, отделять числа скобками или тире. Для автоматической сверки используйте подписи образца. Подойдут также «Средний чек по принятым заказам», «Город с наибольшей выручкой» и «Топ-3 напитков по количеству заказов».

Для напитков выведите до трёх пар в порядке шага 5 и подпишите, что это **топ-3 по числу принятых заказов**. Отдельно выведите число заказов остальных напитков (0, если напитков не больше трёх). Например, из 5 заказов на Чай (2), Какао (1), Кофе (1) и Морс (1) тройка покрывает 4 заказа, остальные — 1. Если у нескольких городов или дней одинаковая максимальная выручка, можно указать любой из них. Если список пуст, верните заголовок `# Отчёт` и строку `Нет принятых заказов`: в таком списке нет даты для заголовка и знаменателя для среднего.

### setup
```python
import csv as _csv
import datetime as _dt

clean, _seen = [], set()
with open('orders.csv', encoding='utf-8', newline='') as _source:
    for _row in _csv.DictReader(_source):
        try:
            _row['amount'] = int(_row['amount'])
        except ValueError:
            continue
        if _row['order_id'] in _seen:
            continue
        _seen.add(_row['order_id'])
        _row['date'] = _dt.date.fromisoformat(_row['date'])
        clean.append(_row)
```

### starter
```python
def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"

    period = orders[0]["date"].isoformat()[:7]
    lines = [f"# Отчёт за {period}", f"Принято заказов: {len(orders)}"]
    # Добавляйте сюда расчёты и новые строки отчёта.
    return "\n".join(lines)

print(build_report(clean))
```

### check
```python
# include-check: ch01_order_report.py

_fn = need('build_report')
_source_orders, _, _ = _read_orders('orders.csv')
_check_report(_fn([row.copy() for row in _source_orders]), _source_orders)
# include-check: ch01_order_sample.py
_check_report(_fn([row.copy() for row in _sample_orders]), _sample_orders)
_check_report(_fn([row.copy() for row in _sample_ties]), _sample_ties)
_check_report(_fn([]), [])
```

### hint
Внутри функции можно повторить знакомые части по очереди. Сначала проверьте заголовок, число заказов, сумму и среднее. Затем добавьте расчёты по городам, напиткам и дням из шагов 4–6. Для названия дня пригодится список `DAYS` из шага 6.

### hint
Из `top3` получится строка с парами: `", ".join(f"{drink} ({count})" for drink, count in top3)`. Для форматирования рублей подойдёт `f"{amount:,}".replace(",", " ")`. Число заказов за пределами тройки — `len(orders) - sum(count for drink, count in top3)`. В конце соедините все строки с помощью `"\n".join(lines)`.

### solution
```python
def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"

    def rub(amount):
        return f"{amount:,}".replace(",", " ") + " ₽"

    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    by_city = {}
    by_day = {}
    drinks = {}
    for row in orders:
        city, drink = row["city"], row["drink"]
        day = row["date"].weekday()
        by_city[city] = by_city.get(city, 0) + row["amount"]
        by_day[day] = by_day.get(day, 0) + row["amount"]
        drinks[drink] = drinks.get(drink, 0) + 1

    period = orders[0]["date"].isoformat()[:7]
    revenue = sum(row["amount"] for row in orders)
    best_city = max(by_city, key=by_city.get)
    best_day = max(by_day, key=by_day.get)
    top3 = sorted(drinks.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
    drink_line = ", ".join(f"{drink} ({count})" for drink, count in top3)
    lines = [
        f"# Отчёт за {period}",
        f"Принято заказов: {len(orders)}",
        f"Учтённая выручка: {rub(revenue)}",
        f"Средний чек: {rub(round(revenue / len(orders)))}",
        f"Лучший город: {best_city} ({rub(by_city[best_city])})",
        f"Топ-3 напитка по числу принятых заказов: {drink_line}",
        f"Заказов остальных напитков: {len(orders) - sum(count for drink, count in top3)}",
        f"День с наибольшей выручкой: {days[best_day]} ({rub(by_day[best_day])})",
    ]
    return "\n".join(lines)

print(build_report(clean))
```

### explain
Читатель видит, почему к сумме 16 370 ₽ стоит добавить слово «учтённая». Это выручка по тем же 37 заказам, для которых рассчитаны средний чек и рейтинги. У двух напитков по восемь заказов, поэтому «Раф» и «Флэт уайт» стоят в порядке сравнения строк Python. Тройка покрывает 25 заказов; остальные напитки — ещё 12.

## task: file | Шаг 8. Отчёт в файл и проблемы данных | plus

В шаге 7 функция получила готовый список `clean`. Теперь на входе только `orders.csv`. Соберите из своих решений программу, которая за любой месяц заново записывает `report.md` в UTF-8. Сохраните исходный CSV для сверки.

1. **От CSV к списку.** Перенесите [чтение CSV](#task-load) и [удаление дублей](#task-dedupe) вместе с импортами. Раскомментируйте первый `print`. В сентябре получится `37 3 1`: принято заказов, строк с битой суммой, лишних дублей.
2. **От списка к тексту.** Перенесите [свою функцию из шага 7](#task-report). Раскомментируйте `text = build_report(clean)` и `print(text)`. Сверьте показатели с предыдущим шагом.
3. **От текста к файлу.** Запишите отчёт и добавьте журнал. Вот результат для сентября:

```text
## Качество данных
- Строк в выгрузке: 41
- Битых строк: 3
- Дублей: 1
- Точных повторов: 1
- Конфликтующих строк: 0
- Нечитаемые суммы: Z-1009, Z-1004, Z-1010. Запросить читаемые суммы из первичных чеков.
- Полная выручка неизвестна: исключены строки с нечитаемой суммой.
```

**Проверьте журнал.** В сентябре `41 = 37 + 3 + 1`. Лишние дубли разделите на точные повторы и конфликты. Сравнивайте каждую следующую читаемую строку с первой читаемой записью того же ID по всем полям. Для битых строк выпишите ID из своего CSV.

**Объясните спорную сумму.** Например, у двух записей V-13 различаются сумма и напиток. Получателю нужна отдельная строка для каждого конфликта:

```text
- Конфликт V-13: учтена первая сумма 175 ₽, другая сумма 999 ₽. Если поменять строки местами, итог вырастет на 824 ₽. Запросить первичный чек.
```

Подпишите обе суммы. Если они равны, назовите поле, которое изменится при перестановке. При нечитаемых суммах или конфликте поясните своими словами, почему полная выручка неизвестна и чем её сверить. Один точный повтор сам по себе не мешает подтвердить сумму.

**Если ни одного заказа не принято.** Все даты одной выгрузки корректны и относятся к одному месяцу. Сохраните месяц из исходной даты до попытки прочитать сумму. Если датированные строки есть, начните файл с `# Отчёт за YYYY-MM`. Если в CSV только заголовок, начните с `# Отчёт`. Дальше в обоих случаях напишите `Нет принятых заказов` и журнал. Средний чек и рейтинги здесь не определены.

Скачайте `report.md` или откройте его в рабочей папке Jupyter. Прочтите файл глазами коллеги без доступа к CSV: какую сумму можно использовать и какие чеки ещё нужны?

### starter
```python
# 1. Здесь ваш код чтения и удаления дублей.
# print(len(clean), n_bad, n_dupes)

# 2. Здесь ваше определение build_report.
# text = build_report(clean)
# print(text)

# 3. Здесь запись текста и журнала в report.md.
```

### setup
```python
from pathlib import Path as _InputPath
_original_csv = _InputPath('orders.csv').read_bytes()
```

### check
```python
# include-check: ch01_order_report.py

from pathlib import Path as _Path
from tempfile import TemporaryDirectory as _TemporaryDirectory
import os as _os

def _check_file(original_csv):
    source = _Path('orders.csv')
    if not source.is_file() or source.read_bytes() != original_csv:
        source.write_bytes(original_csv)
        raise AssertionError('Исходная выгрузка orders.csv изменилась. Откройте её для чтения, а результат запишите отдельно в report.md.')
    output = _Path('report.md')
    assert output.is_file(), 'После запуска должен появиться файл report.md. Проверьте путь и режим записи.'
    rows, bad, duplicates = _read_orders('orders.csv')
    _check_report(output.read_text(encoding='utf-8'), rows, (bad, duplicates), _quality_details('orders.csv'))

_check_file(_original_csv)
# Во временной папке следующий запуск должен заменить предыдущий отчёт.
# include-check: ch01_order_sample.py
_original_dir = _Path.cwd()
with _TemporaryDirectory() as _folder:
    try:
        _os.chdir(_folder)
        _Path('report.md').write_bytes((_original_dir / 'report.md').read_bytes())
        for _case, _csv_text in _project_file_cases:
            _Path('orders.csv').write_text(_csv_text, encoding='utf-8')
            _input = _Path('orders.csv').read_bytes()
            try:
                exec(_code, {'__name__': '__main__'})
                _check_file(_input)
            except Exception as _error:
                raise AssertionError(f'Повторный запуск ({_case}): {_error}') from _error
    finally:
        _os.chdir(_original_dir)
```

### hint
Скопируйте первые два шага и проверьте, что `len(clean) + n_bad + n_dupes` даёт число записей из CSV после заголовка. Затем добавьте определение функции и временно выполните `print(build_report(clean))`. Так удобно найти шаг, на котором расходятся цифры. Для сравнения повторов удобно хранить словарь `first_by_id`: номер → первая принятая запись. При повторе сравните словари: `row == first_by_id[row["order_id"]]`. Точный повтор увеличивает отдельный счётчик; иначе добавьте предупреждение с обеими суммами. Сохраняйте ID битых строк в список до `continue`.

### hint
Откройте файл через `with open("report.md", "w", encoding="utf-8") as f:`. Сначала получите `text = build_report(clean)`. Если `clean` пуст, но сохранён `period`, замените в `text` заголовок через `text.replace("# Отчёт", f"# Отчёт за {period}", 1)`. Затем запишите текст, перевод строки и журнал. Пример строки журнала: `f"- Битых строк: {n_bad}"`.

### solution
```python
import csv
import datetime as dt

def build_report(orders):
    if not orders:
        return "# Отчёт\nНет принятых заказов"

    def rub(amount):
        return f"{amount:,}".replace(",", " ") + " ₽"

    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    by_city = {}
    by_day = {}
    drinks = {}
    for row in orders:
        city, drink = row["city"], row["drink"]
        day = row["date"].weekday()
        by_city[city] = by_city.get(city, 0) + row["amount"]
        by_day[day] = by_day.get(day, 0) + row["amount"]
        drinks[drink] = drinks.get(drink, 0) + 1

    period = orders[0]["date"].isoformat()[:7]
    revenue = sum(row["amount"] for row in orders)
    best_city = max(by_city, key=by_city.get)
    best_day = max(by_day, key=by_day.get)
    top3 = sorted(drinks.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
    drink_line = ", ".join(f"{drink} ({count})" for drink, count in top3)
    lines = [
        f"# Отчёт за {period}",
        f"Принято заказов: {len(orders)}",
        f"Учтённая выручка: {rub(revenue)}",
        f"Средний чек: {rub(round(revenue / len(orders)))}",
        f"Лучший город: {best_city} ({rub(by_city[best_city])})",
        f"Топ-3 напитка по числу принятых заказов: {drink_line}",
        f"Заказов остальных напитков: {len(orders) - sum(count for drink, count in top3)}",
        f"День с наибольшей выручкой: {days[best_day]} ({rub(by_day[best_day])})",
    ]
    return "\n".join(lines)

orders = []
n_bad = 0
bad_ids = []
period = None
with open("orders.csv", encoding="utf-8", newline="") as source:
    for row in csv.DictReader(source):
        period = row["date"][:7]
        try:
            row["amount"] = int(row["amount"])
        except ValueError:
            n_bad += 1
            bad_ids.append(row["order_id"])
            continue
        row["date"] = dt.date.fromisoformat(row["date"])
        orders.append(row)

clean = []
first_by_id = {}
n_dupes = 0
n_exact = 0
conflict_notes = []
for row in orders:
    order_id = row["order_id"]
    if order_id not in first_by_id:
        first_by_id[order_id] = row
        clean.append(row)
    else:
        n_dupes += 1
        first = first_by_id[order_id]
        if row == first:
            n_exact += 1
        else:
            changed = ", ".join(key for key in row if row[key] != first[key])
            consequence = "итог тоже может измениться. "
            if row["amount"] == first["amount"]:
                consequence = "сумма этого заказа не изменится. "
            conflict_notes.append(
                f"- Конфликт {order_id}: учтена первая читаемая запись {first['amount']} ₽; "
                f"другая запись {row['amount']} ₽ (отличаются {changed}). "
                "Изменение порядка записей меняет выбранные поля; "
                + consequence + "Запросить первичный чек."
            )

journal = [
    "## Качество данных",
    f"- Строк в выгрузке: {len(orders) + n_bad}",
    f"- Битых строк: {n_bad}",
    f"- Дублей: {n_dupes}",
    f"- Точных повторов: {n_exact}",
    f"- Конфликтующих строк: {len(conflict_notes)}",
]
journal.extend(conflict_notes)
if bad_ids:
    journal.append(
        "- Нечитаемые суммы: " + ", ".join(bad_ids)
        + ". Запросить читаемые суммы из первичных чеков."
    )
if n_bad or conflict_notes:
    journal.append("- Полная выручка неизвестна: есть битые суммы или конфликты.")

text = build_report(clean)
if not clean and period:
    text = text.replace("# Отчёт", f"# Отчёт за {period}", 1)
with open("report.md", "w", encoding="utf-8") as output:
    output.write(text + "\n\n" + "\n".join(journal) + "\n")

with open("report.md", encoding="utf-8") as result:
    print(result.read())
```

### explain
Для сентября журнал сходится: 41 = 37 + 3 + 1. Если заменить содержимое `orders.csv` и запустить тот же код с начала, программа возьмёт период из новых дат, пересчитает все строки и перезапишет файл. Так руководитель получит ответы и сможет проверить, какие заказы в них учтены.
