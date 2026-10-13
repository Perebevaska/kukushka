---
title: "SQL из Python к базе: параметры и подключения"
lead: "На работе данные лежат не в CSV, а в базе. Подключаемся к ней из Python, передаём значения в запрос безопасно — через параметры, а не f-строкой, — и прячем логин и пароль от git."
files: [zerno.db]
recap:
  - "База из Python: `con = sqlite3.connect(\"zerno.db\")`, `pd.read_sql_query(sql, con, params=(...))`, `con.close()`. Значения — только через заполнители `?`/`:имя`, не f-строкой."
  - "Даты в SQLite — текст: месяц выделяют `substr(ordered_at, 1, 7)` или `strftime('%Y-%m', ordered_at)`."
  - "Рабочая база — SQLAlchemy: `create_engine(URL.create(...))`, `text()` с `:имя`; логин и пароль — в `.env` (`load_dotenv`), а `.env` — в `.gitignore`."
---

## Данные в базе, а не в CSV

Зачем: на работе данные редко приходят файлом. Заказы, гости и меню лежат в базе — PostgreSQL, MS SQL, ClickHouse, — а CSV из неё кто-то выгружает руками, и к утру он уже устарел. Аналитик на Python не ждёт выгрузку: он сам отправляет запрос в базу и получает результат сразу датафреймом.

::: tip Аналогия
Python здесь — такой же клиент базы, как SSMS или DBeaver. Вы подключаетесь, отправляете текст запроса и получаете таблицу. Разница только в том, что таблица попадает не в окно программы, а в переменную, и дальше с ней работает pandas.
:::

Схема всегда одна и та же, какая бы ни была база:

1. **Подключение** — объект, который «держит линию» с базой: `con`.
2. **Запрос** — обычная строка с SQL.
3. **Результат** — `pd.read_sql_query(запрос, con)` возвращает DataFrame.
4. **Закрыть подключение**, когда работа закончена: `con.close()`.

::: figure db-python
Сверху — путь любого запроса из Python: подключение, текст запроса с заполнителями, `pd.read_sql_query`, DataFrame, закрытие. Меняется только первый шаг. Учебная база — файл, и подключение — одна строка `sqlite3.connect`. Рабочая база — сервер: логин и пароль лежат в `.env`, который не попадает в git, `load_dotenv` переносит их в окружение, а `URL.create` и `create_engine` собирают подключение.
:::

### SQLite: база в одном файле

Потренироваться на «настоящей» базе можно прямо здесь. **SQLite** — база данных, которая целиком хранится в одном файле и встроена в Python (модуль `sqlite3`, ничего ставить не нужно). Файл `zerno.db` — база сети «Зерно» за март–август 2026 года: кофейни, меню, гости с картой, акции, заказы и их позиции. С ней мы будем работать в SQL-проекте главы, а пока — подключимся и посмотрим, что внутри.

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("zerno.db")          # подключение к файлу базы
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type = 'table'", con
)
print(tables)

shops = pd.read_sql_query("SELECT * FROM shops", con)
print(shops)
con.close()                                 # линию с базой больше не держим
```

Что здесь происходит:

- `sqlite3.connect("zerno.db")` открывает файл базы и возвращает подключение `con`. Если файла нет, SQLite **молча создаст пустую базу** — запомните это, пригодится в «Типичных ошибках».
- `sqlite_master` — служебная таблица SQLite со списком всех таблиц. В PostgreSQL то же самое лежит в `information_schema.tables`.
- `pd.read_sql_query(текст, con)` отправляет запрос в базу и складывает ответ в DataFrame: столбцы и их имена — как в `SELECT`.

Как читать результат: в базе шесть таблиц — `shops`, `menu`, `guests`, `promos`, `orders`, `order_items`, а кофеен шесть, по две в Перми и Казани и по одной в Тюмени и Уфе.

### Даты в SQLite — это текст

Зачем: отчёты почти всегда «за месяц», а в SQLite нет отдельного типа для даты. Время заказа `ordered_at` хранится строкой: `'2026-03-01 08:36:18'`. Отсюда два правила:

1. **Сравнивать можно как строки.** Строки в формате `ГГГГ-ММ-ДД` сортируются так же, как даты, поэтому `ordered_at >= '2026-06-01'` работает правильно.
2. **Месяц — это первые 7 символов.** `substr(ordered_at, 1, 7)` вырезает 7 символов, начиная с первого: `'2026-03-01 08:36:18'` → `'2026-03'`. То же даёт `strftime('%Y-%m', ordered_at)`: `%Y` — год, `%m` — месяц.

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("zerno.db")
by_month = pd.read_sql_query("""
    SELECT substr(ordered_at, 1, 7) AS month, COUNT(*) AS orders
    FROM orders
    GROUP BY month
    ORDER BY month
""", con)
con.close()
print(by_month)
```

Как читать результат: шесть месяцев, с марта по август 2026 года. В марте 1709 заказов, дальше число растёт, и летом выходит 2600–2700 в месяц.

::: sql
В SQL Server месяц выделили бы через `FORMAT(ordered_at, 'yyyy-MM')` или `DATETRUNC`, а в DuckDB — через `date_trunc`. В SQLite таких функций нет, поэтому работают со строкой.
:::

### Параметры запроса: `params=`, а не f-строка

Частая задача — один и тот же запрос для разных значений: выручка по городу, который выбрал пользователь, заказы за месяц, который передали в функцию. Первое желание — собрать текст f-строкой: `f"... WHERE city = '{city}'"`. Так делать не надо, по двум причинам:

1. **Кавычки ломают запрос.** Значение с апострофом — например, название акции `Кофе д'Арт` — закроет кавычку раньше времени, и запрос упадёт с синтаксической ошибкой.
2. **SQL-инъекция.** Если значение пришло извне (из формы, из файла), в нём может оказаться кусок SQL: `' OR 1=1 --`. Запрос выполнит его как свой.

Правильно — оставить в тексте **заполнитель**, а значения передать отдельно в `params=`. База сама подставит их безопасно: строку как строку, число как число.

::: figure sql-params
Сверху — f-строка: значение становится частью текста запроса. Апостроф в названии акции закрывает кавычку раньше времени, а «значение» `' OR 1=1 --` превращает условие в «всегда истина». Снизу — `params=`: текст с `?` и значения уходят в базу отдельно, и значение остаётся данными, что бы в нём ни было.
:::

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("zerno.db")

query = "SELECT shop_id, name, seats FROM shops WHERE city = ? AND seats >= ?"
t = pd.read_sql_query(query, con, params=("Казань", 20))    # кортеж: по значению на каждый ?
print(t)

query_named = "SELECT name, price FROM menu WHERE category = :cat ORDER BY price DESC"
food = pd.read_sql_query(query_named, con, params={"cat": "еда"})   # словарь: имя → значение
print(food)
con.close()
```

Что здесь происходит:

- `?` — заполнитель по позиции: первый `?` получает первое значение кортежа, второй — второе.
- `:cat` — именованный заполнитель; значения передают словарём. Удобно, когда параметров много или один используется дважды.
- Заполнитель ставится **вместо значения**, без кавычек вокруг: `city = ?`, а не `city = '?'`.

Как читать результат: в Казани 20 мест и больше только у KZN-1 «Баумана» (30 мест). В меню четыре позиции еды, от сэндвича за 260 ₽ до круассана за 140 ₽.

::: predict
```python static
import sqlite3
import pandas as pd
con = sqlite3.connect("zerno.db")
t = pd.read_sql_query("SELECT * FROM shops WHERE city = ?", con, params=("Казань"))
print(len(t))
```

- `2`
- `0`
- [x] `Ошибка DatabaseError`

Почему: `("Казань")` — это не кортеж, а просто строка в скобках. Строку Python перебирает по буквам, и SQLite видит шесть значений на один `?`: `Incorrect number of bindings supplied`. Кортеж из одного элемента пишется с запятой: `("Казань",)`.
:::

::: quiz
Функция строит отчёт по городу, который аналитик выбирает в выпадающем списке. Как подставить город в запрос?

- [x] Оставить в запросе `WHERE city = ?` и передать город через `params=(city,)`
  > База получает текст запроса и значение раздельно и сама подставляет значение как строку. Апострофы и «хитрые» значения не ломают запрос.
- [ ] `f"... WHERE city = '{city}'"` — город же выбирают из списка, ничего опасного
  > Сегодня из списка, завтра функцию вызовут с другим значением. Кавычка в значении сломает запрос, а кусок SQL в нём — выполнится.
- [ ] `"... WHERE city = '?'"` с `params=(city,)`
  > В кавычках `'?'` — это строка из знака вопроса, а не заполнитель. База будет искать город с названием «?».
- [ ] Выгрузить все города и отфильтровать в pandas
  > Работать будет, но тянуть всю таблицу ради одного города — расточительно, а на больших таблицах ещё и долго. Фильтр должен выполняться в базе.
:::

### Рабочая база: SQLAlchemy и пароль в `.env`

::: note Пока только прочитайте
В браузере курса до сервера базы не дотянуться, и этот код здесь не запускается. Команда `uv add` (установка библиотек в проект) появится в уроке «Своё рабочее место — uv и Jupyter», а файл `.gitignore` — в уроке «Git: коммиты, история, ветки и .gitignore». Вернитесь к этому подразделу, когда настроите свой Jupyter. В задачах урока он не нужен.
:::

Зачем: рабочая база — это сервер с логином и паролем, а не файл. С ней — например, с PostgreSQL — всё устроено так же, только подключение создаёт библиотека **SQLAlchemy**. Библиотеки ставят в проект одной командой в терминале, из папки проекта:

```sh
uv add sqlalchemy "psycopg[binary]" python-dotenv
```

Логин и пароль **никогда не пишут в блокнот**: блокнот уходит в git, коллегам и в портфолио. Их кладут в файл `.env` рядом с блокнотом:

```text
DB_HOST=db.zerno.local
DB_PORT=5432
DB_NAME=analytics
DB_USER=analyst
DB_PASSWORD=секрет-не-для-git
```

И сразу добавляют `.env` в `.gitignore`, чтобы файл не попал в репозиторий (подробно о `.gitignore` — в уроке «Git: коммиты, история, ветки и .gitignore»):

```text
.env
```

В блокноте пароль читается из окружения:

```python static
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

load_dotenv()                      # читает .env и кладёт значения в os.environ

url = URL.create(
    "postgresql+psycopg",          # какая база и каким драйвером подключаться
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)
engine = create_engine(url)        # «фабрика» подключений; сама ещё никуда не ходит

query = text("""
    SELECT s.city, SUM(i.qty * i.price) AS revenue
    FROM orders AS o
    JOIN order_items AS i USING (order_id)
    JOIN shops AS s USING (shop_id)
    WHERE o.ordered_at >= :since
    GROUP BY s.city
""")
with engine.connect() as conn:     # подключение закроется само по выходу из with
    by_city = pd.read_sql_query(query, conn, params={"since": "2026-06-01"})
```

Что здесь происходит:

- `load_dotenv()` переносит строки из `.env` в переменные окружения; `os.environ["DB_USER"]` их читает. В коде нет ни одного секрета.
- `URL.create(...)` собирает адрес подключения. Он сам экранирует спецсимволы в пароле — в отличие от склейки строки вида `postgresql://user:pass@host/db`, где `@` или `/` в пароле всё ломают.
- `create_engine(url)` создаёт движок. Подключение открывается только в `engine.connect()`, а `with` гарантирует, что оно закроется даже при ошибке.
- `text(...)` оборачивает SQL, и в нём работают именованные заполнители `:since`, как в SQLite.

::: deep Большие таблицы
Если запрос возвращает миллионы строк, не тяните их целиком. Сначала проверьте запрос с `LIMIT 1000`, а агрегируйте в базе (`GROUP BY` в SQL, а не в pandas). Если сырые строки всё же нужны, `pd.read_sql_query(..., chunksize=100_000)` вернёт их порциями, и каждую можно обработать отдельно.
:::

::: warn Типичные ошибки
- **Опечатка в имени файла SQLite.** `sqlite3.connect("zerno.bd")` не падает, а создаёт новую пустую базу. Первый же запрос сообщит `no such table: shops`. Если видите эту ошибку, сначала проверьте путь к файлу.
- **Пароль в коде.** `create_engine("postgresql://analyst:qwerty@...")` в блокноте — и пароль навсегда в истории git, даже если потом удалить строку. Только `.env` и `.gitignore`.
- **`params=("Казань")` без запятой.** Это строка, а не кортеж: `Incorrect number of bindings supplied`. Нужно `("Казань",)` или `["Казань"]`.
- **Кавычки вокруг заполнителя.** `WHERE city = '?'` ищет город «?» и возвращает пустую таблицу без ошибки.
- **Разные заполнители у разных баз.** SQLite понимает `?` и `:имя`; в SQLAlchemy с `text()` — `:имя` для любой базы. Не смешивайте стили в одном запросе.
:::

{{practice: sqlite-read, sqlite-func}}

## Практика

## task: sqlite-read | Меню из базы | base

Подключитесь к базе `zerno.db` через `sqlite3` и получите `food` — DataFrame со столбцами `name` и `price` для позиций меню категории `cat` по убыванию цены. Категорию передайте через `params=`, не вписывая её в текст запроса. В конце закройте подключение.

### starter
```python
import sqlite3
import pandas as pd

cat = "еда"

```

### check
```python
import pandas as _pd, sqlite3 as _sq
_c = _sq.connect('zerno.db')
_w = _pd.read_sql_query("SELECT name, price FROM menu WHERE category = 'еда' ORDER BY price DESC", _c)
_c.close()
b = need('food', _pd.DataFrame)
assert list(b.columns) == ['name', 'price'], f'Столбцы: {list(b.columns)}, а нужны name и price.'
assert b['name'].tolist() == _w['name'].tolist(), f'Позиции: {b["name"].tolist()}. Нужны все позиции категории, по убыванию цены.'
assert 'params' in _code, 'Передайте категорию через params= — так запрос не сломается ни на каком значении.'
assert "'еда'" not in _code and '"еда"' in _code, 'Категория не должна быть вписана в SQL: оставьте в запросе ? или :cat, а значение — переменная cat.'
assert calls('close') >= 1, 'Закройте подключение: con.close().'
```

### hint
Схема: `con = sqlite3.connect("zerno.db")` → `pd.read_sql_query(запрос, con, params=...)` → `con.close()`.

### hint
В запросе вместо значения — заполнитель: `WHERE category = ?`, а `params=(cat,)` — кортеж из одного значения, с запятой.

### hint
```python
con = sqlite3.connect("zerno.db")
food = pd.read_sql_query(
    "SELECT name, price FROM menu WHERE category = ? ORDER BY ...",
    con, params=(...,),
)
con.close()
```

### solution
```python
import sqlite3
import pandas as pd

cat = "еда"
con = sqlite3.connect("zerno.db")
food = pd.read_sql_query(
    "SELECT name, price FROM menu WHERE category = ? ORDER BY price DESC",
    con, params=(cat,),
)
con.close()
food
```

### explain
Еды в меню четыре позиции: сэндвич (260 ₽), сырники (240 ₽), чизкейк (220 ₽) и круассан (140 ₽). Поменяйте `cat = "не кофе"` — запрос тот же, а результат другой. Так и работают параметризованные отчёты. Если написать `params=(cat)` без запятой, `sqlite3` получит строку из трёх букв и пожалуется: `Incorrect number of bindings supplied`. Тот же результат в pandas без базы дал бы `menu[menu["category"] == cat].sort_values("price", ascending=False)`, но для этого пришлось бы сначала выгрузить всё меню.

## task: sqlite-func | Функция-отчёт с параметрами | plus

Напишите функцию `city_revenue(con, city, month)`: она возвращает выручку города за месяц (`month` — строка вида `"2026-06"`) по базе `zerno.db` целым числом, а если заказов нет — `0`. Выручка — сумма `qty * price` по позициям заказов (`order_items`); город берётся из `shops`. Город и месяц передавайте через параметры — функция не должна ломаться даже на названии с апострофом. Дата заказа в базе — текст (см. «Даты в SQLite — это текст»).

### starter
```python
import sqlite3
import pandas as pd

def city_revenue(con, city, month):
    ...

con = sqlite3.connect("zerno.db")
print(city_revenue(con, "Казань", "2026-06"))
```

### check
```python
import sqlite3 as _sq
_c = _sq.connect('zerno.db')
_q = """SELECT COALESCE(SUM(i.qty * i.price), 0) FROM orders o JOIN order_items i ON i.order_id = o.order_id
        JOIN shops s ON s.shop_id = o.shop_id WHERE s.city = ? AND substr(o.ordered_at, 1, 7) = ?"""
fn = need('city_revenue')
for args in (('Казань', '2026-06'), ('Уфа', '2026-08'), ('Пермь', '2026-03')):
    want = _c.execute(_q, args).fetchone()[0]
    got = fn(_c, *args)
    assert got is not None, f'city_revenue{args} вернула None. Не забудьте return; если сумма пустая — верните 0.'
    assert int(got) == want, f'city_revenue{args} = {got}, а выручка другая. Проверьте соединение трёх таблиц и фильтр по месяцу.'
try:
    r = fn(_c, "Д'Арт", '2026-06')
except Exception as e:
    assert False, f'На городе с апострофом функция упала ({type(e).__name__}). Значения надо передавать через params, а не вставлять в текст запроса.'
assert r is not None and int(r) == 0, f'Для города без заказов нужен 0, а получилось {r!r}. SUM по пустому набору даёт NULL — замените его на 0.'
_c.close()
```

### hint
Месяц хранится внутри текста даты: `ordered_at` выглядит как `2026-06-14 09:12:45`. Первые 7 символов — это месяц: `substr(ordered_at, 1, 7)`.

### hint
Соедините `orders` с `order_items` по `order_id` и с `shops` по `shop_id`. В `WHERE` — `city = ?` и `substr(...) = ?`, а значения передайте в `params=(city, month)`. Пустую сумму превратит в 0 `COALESCE(SUM(...), 0)`.

### hint
```python
def city_revenue(con, city, month):
    query = """
        SELECT COALESCE(SUM(i.qty * i.price), 0) AS revenue
        FROM orders AS o
        JOIN order_items AS i ON i.order_id = o.order_id
        JOIN shops AS s ON s.shop_id = o.shop_id
        WHERE ... = ? AND substr(o.ordered_at, 1, 7) = ?
    """
    t = pd.read_sql_query(query, con, params=(..., ...))
    return int(t["revenue"].iloc[0])
```

### solution
```python
import sqlite3
import pandas as pd

def city_revenue(con, city, month):
    query = """
        SELECT COALESCE(SUM(i.qty * i.price), 0) AS revenue
        FROM orders AS o
        JOIN order_items AS i ON i.order_id = o.order_id
        JOIN shops AS s ON s.shop_id = o.shop_id
        WHERE s.city = ? AND substr(o.ordered_at, 1, 7) = ?
    """
    t = pd.read_sql_query(query, con, params=(city, month))
    return int(t["revenue"].iloc[0])

con = sqlite3.connect("zerno.db")
print(city_revenue(con, "Казань", "2026-06"))
```

### explain
Казань в июне — 334 400 ₽, Уфа в августе — 78 438 ₽. Функция получает подключение снаружи: так одно подключение обслуживает десятки вызовов, а закрывает его тот, кто открыл. Проверка вызвала функцию с городом `Д'Арт`. Версия на f-строке упала бы на апострофе с ошибкой синтаксиса SQL, а с `params` запрос просто не нашёл таких заказов и вернул 0. Без `COALESCE` SQLite вернул бы для пустого месяца `NULL`, в pandas это `None`, и `int(None)` упал бы с `TypeError`. В pandas без базы та же цифра — `full[(full["city"] == city) & (full["month"] == month)]["revenue"].sum()`, но сначала пришлось бы выгрузить и соединить все три таблицы.
