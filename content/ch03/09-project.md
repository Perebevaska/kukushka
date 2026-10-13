---
title: "Проект: кто наши гости"
lead: "Финал главы. Маркетинг хочет понять гостей программы лояльности: сколько их на самом деле, кто они по возрасту и городу, откуда о нас узнают и кто приносит выручку. Данные — грязные анкеты из старой CRM и заказы за осень."
files: [clients_raw.csv, orders_3m.csv, shops.csv]
recap:
  - "Сначала очистка и журнал: сколько строк было, сколько осталось и почему."
  - "После очистки — отчёт о качестве: по каким полям выводы строятся не по всем гостям."
  - "Соединяя таблицы, проверяйте обе стороны: анкеты без заказов (нормально) и заказы без анкет (повод искать ошибку)."
  - "Средние по группам показывайте вместе с размером группы."
  - "Отчёт — функция от сырых данных: новая выгрузка пересчитывается одной строкой."
  - "Проект сдают блокнотом по шаблону: очистка функцией с журналом и контрактом, раздел «Качество данных» с тикетами для владельца CRM, вывод после каждого раздела, Restart & Run All и `check_notebook.py`."
---

## Задача

> Нам нужно понять, кто наши гости. Сколько живых участников в программе лояльности, какого они возраста, из каких городов, откуда узнают о нас и кто из них приносит деньги. Анкеты выгрузили из старой CRM — там, говорят, бардак. Заказы — за сентябрь–ноябрь.

Данные: анкеты `clients_raw.csv`, заказы `orders_3m.csv`, кофейни `shops.csv`.

## План

1. Очистить анкеты и записать журнал потерь.
2. Оценить качество: где после очистки пропуски.
3. Портрет: возраст и города.
4. Соединить анкеты с заказами: кто активен, нет ли заказов без анкет.
5. Источники: сколько гостей и денег приносит каждый.
6. Возраст и деньги: кто из активных гостей тратит больше.
7. Проверка между таблицами: в своём ли городе заказывают гости.
8. Отчёт одной функцией.

::: figure project-guests
Поток данных проекта: из каких файлов какие таблицы получаются и какой шаг на какой таблице строится.
:::

::: quiz
Анкеты соединяют с заказами. У части гостей в анкете нет ни одного заказа, а у части заказов нет анкеты (гости без карты). Какое соединение нужно для вопроса «сколько тратят гости из каждого возрастного сегмента»?

- [x] Анкеты слева, заказы справа, `how="left"`: гости без заказов останутся с нулевой выручкой
  > Вопрос про гостей, поэтому все анкеты должны остаться. Заказы без карты к анкетам не относятся.
- [ ] `inner`: только пары
  > Гости без заказов пропадут, и сегменты будут выглядеть активнее, чем есть.
- [ ] `outer`: всё со всеми
  > В результат попадут заказы без анкеты — без возраста их нельзя отнести к сегменту.
- [ ] Заказы слева, анкеты справа, `left`
  > Тогда главная таблица — заказы, а гости без заказов в неё не попадут.
:::

## Разберём вместе: две стороны соединения

Шаг 4 — самый коварный, поэтому разберём его на игрушке. Три анкеты: C1, C2, C3. Четыре заказа: два от C1, один от C4, один без карты.

| заказ | client_id | сумма |
|---|---|---|
| 1 | C1 | 300 |
| 2 | C1 | 250 |
| 3 | C4 | 400 |
| 4 | — | 200 |

1. **Сколько заказов у каждой анкеты** (анкеты слева, `how="left"`): C1 — 2 заказа на 550 ₽, C2 и C3 — по 0. Анкеты без заказов — нормально: гость завёл карту и не пришёл осенью.
2. **Заказы без анкеты** — заказ 3 от C4. Такой карты в анкетах нет. Это уже повод искать ошибку: опечатка в номере, анкета потерялась при выгрузке или удалена при очистке дублей.
3. **Заказ без карты** (заказ 4) — не ошибка, гость просто не показал карту. В анализ «кто наши гости» он не входит, но в выручку сети — входит.

::: figure join-two-sides
Три анкеты и четыре заказа. Анкеты без заказов — нормально, заказ с несуществующей картой — повод искать ошибку, заказ без карты — не ошибка, но и не про гостей.
:::

Итог: выручка гостей с анкетой — 550 ₽ из 1 150 ₽. Если бы мы посчитали «выручку гостей» после внутреннего соединения и забыли про заказ C4, потеряли бы 400 ₽ — и не узнали бы о проблеме с номером карты.

Что получилось: соединение проверяют с обеих сторон — «у кого нет заказов» отвечает на вопрос бизнеса, «у каких заказов нет анкеты» — на вопрос о качестве данных.

::: warn Типичные ошибки проекта
- **Средние по маленьким группам.** «Гости из Москвы тратят больше всех» по 8 анкетам — не вывод; рядом со средним — размер группы.
- **Внутреннее соединение без проверки.** `merge` по умолчанию `how="inner"` молча выбрасывает обе «сироты».
- **Очистка заказов по правилам анкет.** Номер карты в заказах тоже надо нормализовать, иначе « c1012» не найдёт свою анкету.
- **Отчёт без журнала.** Директор спросит, почему гостей 293, а не 307, — ответ должен быть в отчёте.
:::

## Сдайте проект блокнотом

Шаги в браузере ниже — тренировка: каждый проверяется сразу. Но маркетингу нужен не набор зелёных галочек, а отчёт, который можно открыть, перезапустить на январской выгрузке и прочитать. Поэтому после шагов соберите проект в Jupyter — так же, как проект главы 2.

1. **Скачайте шаблон** [project-template.ipynb](../notebooks/project-template.ipynb) в папку проекта из урока про uv и положите рядом папку `data/` с тремя файлами: `clients_raw.csv`, `orders_3m.csv`, `shops.csv`. Переименуйте шаблон, например, в `guests.ipynb`.
2. **Поправьте первую ячейку.** У вас `data/` рядом с блокнотом — `DATA = Path('data')`. Шаблон общий для всех глав, поэтому в нём есть импорты `sklearn` (библиотеки машинного обучения — она понадобится в главах про модели) и пример модели в разделе 4. В этом проекте моделей нет: удалите эти импорты и пример, вы ничего не пропустили.
3. **Раздел «2. Данные»** — загрузка трёх файлов и осмотр по чек-листу из урока «Первый осмотр: что не так с данными»: размер и типы, пропуски, варианты написания, дубли. Сырые файлы не меняйте.
4. **Раздел «3. Предобработка»** — функция очистки анкет из шага 1, журнал потерь и контракт из урока «Очистка целиком: функция и проверки». Очищенные анкеты сохраните в `clients_clean.csv`. В выводе — журнал словами: «из 307 строк выгрузки осталось 293 анкеты: 8 полных дублей, 6 повторных анкет».
5. **Раздел «3.1. Качество данных»** — отдельный `## 3.1. Качество данных` сразу после предобработки: что после очистки осталось неизвестным (шаг 2) и какие проблемы надо исправлять в самой CRM. Для каждой такой проблемы — тикет-словарь из урока «Аномалии и проверка на здравый смысл»: где, правило, сколько строк, примеры номеров карт, как найти. Персональные данные гостей в тикеты не попадают.
6. **Раздел «4. Анализ»** — шаги 3–7, по своему `##` на каждый, например `## 4.3. Откуда приходят гости`: скрипт самопроверки ищет вывод после каждого `##`, а подзаголовки `###` он не проверяет. После каждого раздела — markdown-вывод с цифрами и размером групп.
7. **Раздел «5. Выводы и рекомендации»** — отчёт из шага 8 и три части: что сделали, что нашли, что предлагаем маркетингу и владельцу CRM. Все пометки ✎ замените своим текстом.
8. **Самопроверка.** **Kernel → Restart Kernel and Run All Cells**, затем [check_notebook.py](../notebooks/check_notebook.py) рядом с блокнотом:

   ```sh
   uv run python check_notebook.py guests.ipynb
   ```

   Исправьте всё, что скрипт нашёл, и запустите снова — до чистого результата. Сверка чисел с эталонами шагов — по желанию, команда в блоке «Для любопытных» ниже.
9. **В портфолио.** Выложите блокнот в отдельный репозиторий, как в уроке про git в главе 2. Папку `data/` добавьте в `.gitignore`: в анкетах имена и телефоны гостей, им не место в открытом репозитории. В README опишите, откуда взять данные.

::: deep Сверка чисел с эталонами шагов
Если переменные в блокноте названы как в шагах ниже (`clients`, `guests`, `home_pct`…), скрипт может сверить ваши числа с эталонами курса:

```sh
uv run python check_notebook.py guests.ipynb --project ch03/09-project --course ПАПКА_КУРСА
```

`ПАПКА_КУРСА` — путь к распакованному архиву курса. Если блокнот лежит внутри папки курса, `--course` можно не писать.
:::

::: note Сделайте в своём блокноте
1. Пройдите шаги 1–8 в браузере.
2. Перенесите решения в шаблон: очистка — функцией, журнал и контракт — в предобработку, тикеты — в «3.1. Качество данных».
3. Restart & Run All, затем `check_notebook.py` — до чистого результата.
4. Проверка на повторяемость: замените в первой ячейке имя файла анкет на копию с другим именем и перезапустите — отчёт должен пересчитаться без единой правки в коде.
:::

Начиная со второго шага, перед задачей курс сам готовит очищенные анкеты `clients` и заказы `orders` (с датой в `datetime`), а с пятого — и таблицу `guests` с заказами и выручкой гостя. Ошибка на одном шаге не мешает следующим.

::: tip
Это повторение всей главы. В подсказках указано, на какой урок опирается шаг. Если что-то забылось — шпаргалка в шапке и поиск (<kbd class="mod">Ctrl</kbd>+<kbd>K</kbd>).
:::

## Практика

## task: clean | Шаг 1. Очистка анкет | base

Очистите анкеты так же, как в уроке «Очистка целиком: функция и проверки»: функции для столбцов уже в заготовке, допишите `clean_clients(raw)` (или перенесите свою из урока «Очистка целиком: функция и проверки»). Результат — `clients`. Заодно соберите `log` — словарь с тремя числами:

- `"выгрузка"` — строк в сыром файле;
- `"без полных дублей"` — после удаления полных копий;
- `"анкет"` — строк в `clients`.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
```

### starter
```python
import pandas as pd

SYNONYMS = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

def clean_city(s):
    return (s.str.strip().str.lower().str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"}).str.capitalize())

def clean_phone(s):
    return s.str.replace(r"\D", "", regex=True).str[-10:]

def clean_gender(s):
    return s.str.strip().str.lower().str[0].map({"м": "М", "ж": "Ж"})

def parse_birth(s):
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    ru = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    born = iso.fillna(ru)
    return born.where(born.between("1926-12-01", "2012-12-01"))

def clean_bonus(s):
    b = pd.to_numeric(s.str.replace(" ", ""), errors="coerce")
    return b.mask((b < 0) | (b > 10_000))

def clean_clients(raw):
    ...

raw = pd.read_csv("clients_raw.csv")
clients = clean_clients(raw)
log = {}
log
```

### check
```python
import pandas as _pd
want = _ref_clients().set_index('client_id').sort_index()
c = need('clients', _pd.DataFrame)
assert c['client_id'].is_unique and len(c) == len(want), f'В clients {len(c)} строк, а нужно {len(want)} уникальных анкет.'
g = c.set_index('client_id').sort_index()
for col in ['gender', 'birth_date', 'city', 'phone', 'signup_date', 'bonus', 'source']:
    a, w = g[col], want[col]
    same = (a.isna() == w.isna()) & ((a == w) | w.isna())
    assert same.all(), f'Столбец {col} не совпадает, например у {g.index[~same][0]}: {a[~same].iloc[0]!r}, а нужно {w[~same].iloc[0]!r}.'
r = _pd.read_csv('clients_raw.csv')
wl = {'выгрузка': len(r), 'без полных дублей': len(r.drop_duplicates()), 'анкет': len(want)}
got = {k: int(v) for k, v in dict(need('log')).items()}
assert got == wl, f'log = {got}, а нужно {wl}.'
```

### hint
Урок «Очистка целиком: функция и проверки»: та же функция `clean_clients`. Полные дубли → нормализация номера и столбцов → самая свежая анкета.

### hint
Журнал: `{"выгрузка": len(raw), "без полных дублей": len(raw.drop_duplicates()), "анкет": len(clients)}`.

### solution
```python
import pandas as pd

SYNONYMS = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

def clean_city(s):
    return (s.str.strip().str.lower().str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"}).str.capitalize())

def clean_phone(s):
    return s.str.replace(r"\D", "", regex=True).str[-10:]

def clean_gender(s):
    return s.str.strip().str.lower().str[0].map({"м": "М", "ж": "Ж"})

def parse_birth(s):
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    ru = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    born = iso.fillna(ru)
    return born.where(born.between("1926-12-01", "2012-12-01"))

def clean_bonus(s):
    b = pd.to_numeric(s.str.replace(" ", ""), errors="coerce")
    return b.mask((b < 0) | (b > 10_000))

def clean_clients(raw):
    df = raw.drop_duplicates().copy()
    df["client_id"] = df["client_id"].str.strip().str.upper()
    df["name"] = df["name"].str.strip().str.capitalize()
    df["gender"] = clean_gender(df["gender"])
    df["birth_date"] = parse_birth(df["birth_date"])
    df["city"] = clean_city(df["city"])
    df["phone"] = clean_phone(df["phone"])
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["bonus"] = clean_bonus(df["bonus"])
    df["source"] = df["source"].str.strip().str.lower().replace(SYNONYMS)
    return (df.sort_values("signup_date")
              .drop_duplicates(subset=["client_id"], keep="last")
              .reset_index(drop=True))

raw = pd.read_csv("clients_raw.csv")
clients = clean_clients(raw)
log = {"выгрузка": len(raw), "без полных дублей": len(raw.drop_duplicates()), "анкет": len(clients)}
log
```

### explain
Журнал показывает путь данных: 307 строк в выгрузке → 299 после удаления полных копий → 293 анкеты, когда у каждого гостя осталась одна самая свежая версия. Такие три числа стоит класть в отчёт: заказчик сразу видит, что 14 строк убраны не случайно и по какой причине. Если в следующем месяце числа резко изменятся (например, полных дублей станет сотня), это сигнал проверить саму выгрузку.

## task: quality | Шаг 2. Качество после очистки | base

Таблица `clients` уже очищена. Сохраните в `missing_pct` долю пропусков по столбцам в процентах (1 знак), отсортированную по убыванию, и в `usable_age` — долю анкет, по которым известен возраст (то есть есть `birth_date`), в процентах с одним знаком.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
clients = _ref_clients()
orders = _ref_orders()
```

### starter
```python
import pandas as pd
# clients — очищенные анкеты, orders — заказы за осень (datetime — дата)
clients.head(3)
```

### check
```python
import pandas as _pd
c = _ref_clients()
want = (c.isna().mean() * 100).round(1).sort_values(ascending=False)
got = need('missing_pct', _pd.Series)
assert got.to_dict() == want.to_dict(), f'missing_pct = {got.head(3).to_dict()}…'
assert list(got.values) == sorted(got.values, reverse=True), 'Отсортируйте по убыванию.'
assert close(need('usable_age'), round(c['birth_date'].notna().mean() * 100, 1)), f'usable_age = {need("usable_age")}.'
```

### hint
Урок «Первый осмотр: что не так с данными»: `(clients.isna().mean() * 100).round(1)`.

### hint
Доля известных — `notna().mean()`.

### solution
```python
import pandas as pd
missing_pct = (clients.isna().mean() * 100).round(1).sort_values(ascending=False)
usable_age = round(clients["birth_date"].notna().mean() * 100, 1)
missing_pct
```

### explain
Пропусков в `birth_date` после очистки стало больше, чем в сырых данных: туда добавились заглушки и невозможные даты. Это честнее, чем считать возраст по 1900 году. Цифру `usable_age` стоит указать в отчёте: портрет по возрасту построен не по всем гостям.

## task: age | Шаг 3. Портрет по возрасту и городам | base

Добавьте в `clients` столбцы `age` (полных лет на 1 декабря 2026: `дни // 365.25`) и `age_group` (`pd.cut` с `right=False`, границы 14, 25, 35, 45, 60, 100 и подписи `"14–24"`, `"25–34"`, `"35–44"`, `"45–59"`, `"60–99"`). Сохраните:

- `median_age` — медианный возраст;
- `age_counts` — словарь «группа → число анкет»;
- `by_city` — словарь «город → число анкет» (без пропусков).

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
clients = _ref_clients()
orders = _ref_orders()
```

### starter
```python
import pandas as pd
```

### check
```python
import pandas as _pd
c = _ref_clients()
a, g = _ref_age(c)
cc = need('clients', _pd.DataFrame)
assert 'age' in cc.columns and 'age_group' in cc.columns, 'Добавьте в clients столбцы age и age_group.'
assert close(need('median_age'), a.median()), f'median_age = {need("median_age")}, а нужно {a.median()}.'
got = {str(k): int(v) for k, v in dict(need('age_counts')).items()}
assert got == {k: int(v) for k, v in g.value_counts().items()}, f'age_counts = {got}.'
gc = {k: int(v) for k, v in dict(need('by_city')).items()}
assert gc == {k: int(v) for k, v in c['city'].value_counts().items()}, f'by_city = {gc}.'
```

### hint
Уроки «Типы: из текста в числа и даты» и «Категоризация: CASE WHEN в pandas»: `(pd.Timestamp("2026-12-01") - clients["birth_date"]).dt.days // 365.25`, затем `pd.cut(...)`.

### hint
Словари — `dict(clients["age_group"].value_counts())` и то же для города.

### solution
```python
import pandas as pd
clients["age"] = (pd.Timestamp("2026-12-01") - clients["birth_date"]).dt.days // 365.25
clients["age_group"] = pd.cut(clients["age"], bins=[14, 25, 35, 45, 60, 100],
                              labels=["14–24", "25–34", "35–44", "45–59", "60–99"], right=False)
median_age = clients["age"].median()
age_counts = dict(clients["age_group"].value_counts())
by_city = dict(clients["city"].value_counts())
age_counts
```

### explain
`right=False` делает интервалы вида [14, 25): 24 года попадает в «14–24», а 25 — уже в «25–34». Подписи групп именно поэтому заканчиваются на 24, 34 и так далее. Медианный возраст — 39 лет, самая большая группа — 45–59 (84 анкеты). В сумме групп меньше, чем анкет, потому что у 42 гостей нет правдоподобной даты рождения — их не стоит молча считать ни в какую группу. Из городов лидируют Пермь (89) и Казань (88).

## task: guests | Шаг 4. Анкеты и заказы | base

Соедините анкеты с заказами. Посчитайте по каждому гостю число заказов `orders` и выручку `revenue` и присоедините к `clients` (LEFT JOIN — гости без заказов остаются, у них `orders` и `revenue` равны 0). Результат — `guests`. Сохраните:

- `active_pct` — долю гостей хотя бы с одним заказом, %, 1 знак;
- `n_orphans` — сколько разных номеров карт есть в заказах, но нет в анкетах (проверка между таблицами). Ноль — тоже возможный ответ: значит, проверка ничего не нашла.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
clients = _ref_clients()
orders = _ref_orders()
```

### starter
```python
import pandas as pd
```

### check
```python
import pandas as _pd
w = _ref_guests()
g = need('guests', _pd.DataFrame)
assert len(g) == len(w), f'В guests {len(g)} строк, а анкет {len(w)}. LEFT JOIN не должен ни терять, ни размножать строки.'
assert {'orders', 'revenue'} <= set(g.columns), 'В guests нужны столбцы orders и revenue.'
assert g['orders'].notna().all() and g['revenue'].notna().all(), 'У гостей без заказов orders и revenue должны быть 0, а не NaN.'
gg = g.set_index('client_id')
ww = w.set_index('client_id')
assert (gg['revenue'].reindex(ww.index) == ww['revenue']).all(), 'revenue не совпадает с суммой заказов гостя.'
assert close(need('active_pct'), round((w['orders'] > 0).mean() * 100, 1)), f'active_pct = {need("active_pct")}.'
o = _ref_orders()
assert need('n_orphans') == len(set(o['client_id'].dropna()) - set(w['client_id'])), f'n_orphans = {need("n_orphans")}.'
```

### hint
Глава 2, уроки «Группировки: GROUP BY и HAVING» и «Соединения: JOIN и UNION»: `stats = orders.groupby("client_id").agg(orders=("order_id", "count"), revenue=("amount", "sum"))`, затем `clients.merge(stats, on="client_id", how="left")`.

### hint
После LEFT JOIN у гостей без заказов — `NaN`. Здесь пусто действительно значит ноль: `fillna(0)`.

### hint
Номера без анкеты — разность множеств: `set(orders["client_id"].dropna()) - set(clients["client_id"])`.

### solution
```python
import pandas as pd
stats = orders.groupby("client_id").agg(orders=("order_id", "count"), revenue=("amount", "sum"))
guests = clients.merge(stats, on="client_id", how="left")
guests[["orders", "revenue"]] = guests[["orders", "revenue"]].fillna(0)
active_pct = round((guests["orders"] > 0).mean() * 100, 1)
n_orphans = len(set(orders["client_id"].dropna()) - set(clients["client_id"]))
guests.head()
```

### explain
`n_orphans = 0` — хороший знак: у каждой карты из заказов есть анкета. Проверку всё равно оставляют в блокноте: в следующей выгрузке «сироты» могут появиться, и она их сразу поймает. Если бы такие номера нашлись, это была бы либо ошибка нормализации (« c1012» не совпал с «C1012»), либо потерянные анкеты. А вот обратное — анкеты без заказов — нормально: гость зарегистрировался, но осенью не заходил.

## task: sources | Шаг 5. Откуда приходят гости | base

В `guests` уже есть заказы и выручка гостя. Подготовьте источник: пропуски → «не указано», затем редкие значения (меньше 10 анкет) → «прочее» (функция `lump` из урока «Категоризация: CASE WHEN в pandas»). Соберите `by_source` — таблицу по источникам со столбцами:

- `clients` — число анкет;
- `active_pct` — доля гостей с заказами, % (1 знак);
- `avg_revenue` — средняя выручка на гостя за осень, включая гостей без заказов (округлить до целого).

Отсортируйте по `clients` по убыванию. В `best_source` сохраните источник с наибольшей `avg_revenue` среди групп, где **не меньше 20 гостей**.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
clients = _ref_clients()
orders = _ref_orders()
guests = _ref_guests()
guests['source'] = clients['source'].values
```

### starter
```python
import pandas as pd
# guests — анкеты + orders и revenue; source — после словаря синонимов
guests["source"].value_counts(dropna=False)
```

### check
```python
import pandas as _pd
w = _ref_guests()
t = w.groupby('source').agg(clients=('client_id', 'count'), act=('orders', lambda x: (x > 0).mean() * 100), avg=('revenue', 'mean'))
b = need('by_source', _pd.DataFrame)
if 'source' in b.columns:
    b = b.set_index('source')
assert list(b.columns) == ['clients', 'active_pct', 'avg_revenue'], f'Столбцы: {list(b.columns)}.'
assert set(b.index) == set(t.index), f'Источники: {sorted(b.index)}, а нужны {sorted(t.index)}. Пропуски → «не указано», редкие → «прочее».'
assert b['clients'].to_dict() == t['clients'].to_dict(), 'clients не совпадает.'
assert (b['active_pct'] - t['act'].round(1)).abs().max() < 1e-9, 'active_pct не совпадает.'
assert (b['avg_revenue'] - t['avg'].round(0)).abs().max() < 1e-9, 'avg_revenue не совпадает — среднее по всем гостям источника, с нулями.'
assert list(b['clients']) == sorted(b['clients'], reverse=True), 'Отсортируйте по clients по убыванию.'
assert need('best_source') == t.loc[t['clients'] >= 20, 'avg'].idxmax(), f'best_source = {need("best_source")!r}.'
```

### hint
Урок «Категоризация: CASE WHEN в pandas»: сначала `fillna("не указано")`, потом `where(s.isin(частые), "прочее")`.

### hint
Доля активных — среднее от `orders > 0` по группе. Удобно добавить столбец `active = guests["orders"] > 0` и взять `("active", "mean")` в `agg`.

### solution
```python
import pandas as pd

def lump(s, min_count):
    counts = s.value_counts()
    frequent = counts[counts >= min_count].index
    return s.where(s.isin(frequent) | s.isna(), "прочее")

guests["source"] = lump(guests["source"].fillna("не указано"), 10)
guests["active"] = guests["orders"] > 0
by_source = guests.groupby("source").agg(
    clients=("client_id", "count"),
    active_pct=("active", "mean"),
    avg_revenue=("revenue", "mean"),
)
by_source["active_pct"] = (by_source["active_pct"] * 100).round(1)
by_source["avg_revenue"] = by_source["avg_revenue"].round(0)
by_source = by_source.sort_values("clients", ascending=False)
big = by_source[by_source["clients"] >= 20]
best_source = big["avg_revenue"].idxmax()
by_source
```

### explain
Почему порог в 20 гостей: в «прочее» всего 8 человек. Уберите оттуда одного самого активного гостя — средняя упадёт с 1340 до 1188 ₽, уберите самого слабого — вырастет до 1464 ₽. Один человек двигает среднюю группы на 10 %, и такую группу нельзя ставить в лидеры или аутсайдеры. Выводы по маленьким группам ненадёжны.

Средняя выручка на гостя — с нулями у неактивных. Так метрика отвечает на вопрос маркетинга «сколько в среднем приносит гость из этого источника», а не «сколько приносит гость, который всё-таки пришёл». Это разные вопросы, и подписывать нужно, какой из них вы посчитали.

## task: age-money | Шаг 6. Возраст и деньги | plus

Среди **активных** гостей (хотя бы один заказ) с известной возрастной группой посчитайте по группам `age_group`: число гостей `guests_n`, среднее число заказов `avg_orders` и среднюю выручку `avg_revenue` (оба — 1 знак). Таблица — `by_age`, в `best_group` — группа с наибольшей средней выручкой.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
clients = _ref_clients()
orders = _ref_orders()
guests = _ref_guests()
```

### starter
```python
import pandas as pd
# в guests уже есть age, age_group, orders, revenue
guests[["client_id", "age", "age_group", "orders", "revenue"]].head()
```

### check
```python
import pandas as _pd
w = _ref_guests()
a = w[w['orders'] > 0]
t = a.groupby('age_group', observed=True).agg(n=('client_id', 'count'), o=('orders', 'mean'), r=('revenue', 'mean'))
b = need('by_age', _pd.DataFrame)
if 'age_group' in b.columns:
    b = b.set_index('age_group')
assert list(b.columns) == ['guests_n', 'avg_orders', 'avg_revenue'], f'Столбцы: {list(b.columns)}.'
b.index = b.index.astype(str)
t.index = t.index.astype(str)
assert set(b.index) == set(t.index), f'Группы: {sorted(b.index)}. Пустые категории уберите: observed=True.'
assert b['guests_n'].to_dict() == t['n'].to_dict(), f'guests_n = {b["guests_n"].to_dict()}. Только активные гости!'
assert (b['avg_orders'] - t['o'].round(1).reindex(b.index)).abs().max() < 1e-9, 'avg_orders не совпадает.'
assert (b['avg_revenue'] - t['r'].round(1).reindex(b.index)).abs().max() < 1e-9, 'avg_revenue не совпадает.'
assert str(need('best_group')) == t['r'].idxmax(), f'best_group = {need("best_group")!r}.'
```

### hint
Сначала маска `guests["orders"] > 0`. Гости без возрастной группы в `groupby` не попадут сами.

### hint
Урок «Категоризация: CASE WHEN в pandas»: у столбца из `cut` тип `category`, поэтому `groupby("age_group", observed=True)`.

### solution
```python
import pandas as pd
active = guests[guests["orders"] > 0]
by_age = active.groupby("age_group", observed=True).agg(
    guests_n=("client_id", "count"),
    avg_orders=("orders", "mean"),
    avg_revenue=("revenue", "mean"),
).round(1)
best_group = by_age["avg_revenue"].idxmax()
by_age
```

### explain
Посмотрите на `guests_n`: в некоторых группах гостей немного. Разница в средней выручке между маленькими группами может быть случайной — проверять такие различия статистически научимся в главе 5. А пока в отчёте стоит указывать размер группы рядом со средним.

## task: home | Шаг 7. Свой город или в гостях | plus

Гость из Перми может заказать кофе и в Казани. Для заказов с картой определите город кофейни (из `shops.csv`) и город гостя (из анкеты). Среди заказов, где известны оба города, посчитайте `home_pct` — долю заказов в городе гостя (%, 1 знак). В `travelers` сохраните число гостей, которые заказывали в двух и более городах.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
clients = _ref_clients()
orders = _ref_orders()
```

### starter
```python
import pandas as pd
shops = pd.read_csv("shops.csv")
```

### check
```python
import pandas as _pd
o = _ref_orders()
s = _pd.read_csv('shops.csv')[['shop_id', 'city']].rename(columns={'city': 'shop_city'})
c = _ref_clients()[['client_id', 'city']].rename(columns={'city': 'home_city'})
t = o.dropna(subset=['client_id']).merge(s, on='shop_id', how='left').merge(c, on='client_id', how='left')
k = t.dropna(subset=['shop_city', 'home_city'])
assert close(need('home_pct'), round((k['shop_city'] == k['home_city']).mean() * 100, 1)), f'home_pct = {need("home_pct")}, а нужно {round((k["shop_city"] == k["home_city"]).mean() * 100, 1)}.'
n = t.groupby('client_id')['shop_city'].nunique()
assert need('travelers') == int((n >= 2).sum()), f'travelers = {need("travelers")}, а нужно {int((n >= 2).sum())}.'
```

### hint
Два `merge`: заказы + кофейни (город кофейни) и + анкеты (город гостя). Чтобы столбцы `city` не перепутались, переименуйте их: `rename(columns={"city": "shop_city"})`.

### hint
Странники: `groupby("client_id")["shop_city"].nunique()` и маска `>= 2`.

### hint
```python
shop_city = shops[["shop_id", "city"]].rename(columns={"city": "shop_city"})
home_city = clients[["client_id", "city"]].rename(columns={"city": ...})
t = (orders.dropna(subset=["client_id"])
           .merge(shop_city, on="shop_id", how="left")
           .merge(home_city, on="client_id", how="left"))
known = t.dropna(subset=[..., ...])          # оба города известны
home_pct = round((known["shop_city"] == known[...]).mean() * 100, 1)
travelers = (t.groupby("client_id")["shop_city"].nunique() >= 2).sum()
```

### solution
```python
import pandas as pd
shops = pd.read_csv("shops.csv")
shop_city = shops[["shop_id", "city"]].rename(columns={"city": "shop_city"})
home_city = clients[["client_id", "city"]].rename(columns={"city": "home_city"})
t = (orders.dropna(subset=["client_id"])
           .merge(shop_city, on="shop_id", how="left")
           .merge(home_city, on="client_id", how="left"))
known = t.dropna(subset=["shop_city", "home_city"])
home_pct = round((known["shop_city"] == known["home_city"]).mean() * 100, 1)
cities = t.groupby("client_id")["shop_city"].nunique()
travelers = (cities >= 2).sum()
home_pct
```

### explain
«Свой город» — 85.1 % заказов (1007 из 1183, где известны оба города), «странников» — 73 из 260 гостей с заказами. Сеть живёт на местных гостях: акции и рекламу разумно планировать по городам, а продажи в каждом городе прогнозировать по его жителям. Интереснее остальные 176 заказов «в гостях». 117 из них сделали 27 гостей из Екатеринбурга и Москвы: кофеен с заказами там нет, и эти люди пьют кофе «Зерна» в поездках, чаще всего в Казани (99 заказов). Гости из Екатеринбурга — готовая аудитория для кофейни EKB-1: им можно написать ещё до её открытия. Ещё одна деталь: среди 73 странников 14 гостей без города в анкете. В `home_pct` их заказы не вошли — сравнивать не с чем, а в `travelers` вошли: там город анкеты не нужен. Когда два показателя считаются по разным подмножествам, это стоит подписать в отчёте.

## task: report | Шаг 8. Отчёт одной функцией | star

Напишите `report(raw, orders)`: принимает **сырые** анкеты и заказы, очищает анкеты (функцией `clean_clients` из шага 1, она уже в заготовке) и возвращает словарь:

- `"clients"` — число анкет после очистки;
- `"active_pct"` — доля гостей хотя бы с одним заказом, % (1 знак);
- `"median_age"` — медианный возраст на 1 декабря 2026;
- `"avg_revenue_active"` — средняя выручка активного гостя (1 знак).

Функция должна работать на любом периоде заказов — например, только на ноябре.

### setup
```python
import pandas as _pd0
def _ref_clean(raw):
    syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
    d = raw.drop_duplicates().copy()
    d['client_id'] = d['client_id'].str.strip().str.upper()
    d['name'] = d['name'].str.strip().str.capitalize()
    d['gender'] = d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
    b = _pd0.to_datetime(d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(
        _pd0.to_datetime(d['birth_date'], format='%d.%m.%Y', errors='coerce'))
    d['birth_date'] = b.where(b.between('1926-12-01', '2012-12-01'))
    d['city'] = (d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip()
                 .replace({'екб': 'екатеринбург'}).str.capitalize())
    d['phone'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
    d['signup_date'] = _pd0.to_datetime(d['signup_date'])
    n = _pd0.to_numeric(d['bonus'].str.replace(' ', ''), errors='coerce')
    d['bonus'] = n.mask((n < 0) | (n > 10_000))
    d['source'] = d['source'].str.strip().str.lower().replace(syn)
    return d.sort_values('signup_date').drop_duplicates('client_id', keep='last').reset_index(drop=True)
def _ref_clients():
    return _ref_clean(_pd0.read_csv('clients_raw.csv'))
def _ref_orders():
    return _pd0.read_csv('orders_3m.csv', parse_dates=['datetime'])
def _ref_age(c):
    a = (_pd0.Timestamp('2026-12-01') - c['birth_date']).dt.days // 365.25
    g = _pd0.cut(a, bins=[14, 25, 35, 45, 60, 100], labels=['14–24', '25–34', '35–44', '45–59', '60–99'], right=False)
    return a, g
def _ref_lump(s):
    vc = s.value_counts()
    return s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
def _ref_guests(c=None, o=None):
    c = _ref_clients() if c is None else c.copy()
    o = _ref_orders() if o is None else o
    st = o.groupby('client_id').agg(orders=('order_id', 'count'), revenue=('amount', 'sum'))
    g = c.merge(st, left_on='client_id', right_index=True, how='left')
    g['orders'] = g['orders'].fillna(0)
    g['revenue'] = g['revenue'].fillna(0)
    g['age'], g['age_group'] = _ref_age(g)
    g['source'] = _ref_lump(g['source'].fillna('не указано'))
    return g
```

### starter
```python
import pandas as pd

SYNONYMS = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

def clean_city(s):
    return (s.str.strip().str.lower().str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"}).str.capitalize())

def clean_phone(s):
    return s.str.replace(r"\D", "", regex=True).str[-10:]

def clean_gender(s):
    return s.str.strip().str.lower().str[0].map({"м": "М", "ж": "Ж"})

def parse_birth(s):
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    ru = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    born = iso.fillna(ru)
    return born.where(born.between("1926-12-01", "2012-12-01"))

def clean_bonus(s):
    b = pd.to_numeric(s.str.replace(" ", ""), errors="coerce")
    return b.mask((b < 0) | (b > 10_000))

def clean_clients(raw):
    df = raw.drop_duplicates().copy()
    df["client_id"] = df["client_id"].str.strip().str.upper()
    df["name"] = df["name"].str.strip().str.capitalize()
    df["gender"] = clean_gender(df["gender"])
    df["birth_date"] = parse_birth(df["birth_date"])
    df["city"] = clean_city(df["city"])
    df["phone"] = clean_phone(df["phone"])
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["bonus"] = clean_bonus(df["bonus"])
    df["source"] = df["source"].str.strip().str.lower().replace(SYNONYMS)
    return (df.sort_values("signup_date")
              .drop_duplicates(subset=["client_id"], keep="last")
              .reset_index(drop=True))

def report(raw, orders):
    ...

raw = pd.read_csv("clients_raw.csv")
orders = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
report(raw, orders)
```

### check
```python
import pandas as _pd
raw = _pd.read_csv('clients_raw.csv')
o = _ref_orders()
f = need('report')
for part, name in ((o, 'вся осень'), (o[o['datetime'].dt.month == 11], 'только ноябрь')):
    g = _ref_guests(o=part)
    act = g[g['orders'] > 0]
    want = {'clients': len(g), 'active_pct': round((g['orders'] > 0).mean() * 100, 1),
            'median_age': float(g['age'].median()), 'avg_revenue_active': round(act['revenue'].mean(), 1)}
    got = f(raw.copy(), part.copy())
    assert isinstance(got, dict), 'report должна возвращать словарь.'
    got = {k: round(float(v), 1) for k, v in got.items()}
    want = {k: round(float(v), 1) for k, v in want.items()}
    assert got == want, f'Для «{name}» report = {got}, а нужно {want}.'
```

### hint
Внутри: `clients = clean_clients(raw)`, затем выручка и заказы по гостям из `orders` и LEFT JOIN, как в шаге 4.

### hint
Возраст — как в шаге 3. Средняя выручка активного — `revenue` по маске `orders > 0`.

### solution
```python
import pandas as pd

SYNONYMS = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

def clean_city(s):
    return (s.str.strip().str.lower().str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"}).str.capitalize())

def clean_phone(s):
    return s.str.replace(r"\D", "", regex=True).str[-10:]

def clean_gender(s):
    return s.str.strip().str.lower().str[0].map({"м": "М", "ж": "Ж"})

def parse_birth(s):
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    ru = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    born = iso.fillna(ru)
    return born.where(born.between("1926-12-01", "2012-12-01"))

def clean_bonus(s):
    b = pd.to_numeric(s.str.replace(" ", ""), errors="coerce")
    return b.mask((b < 0) | (b > 10_000))

def clean_clients(raw):
    df = raw.drop_duplicates().copy()
    df["client_id"] = df["client_id"].str.strip().str.upper()
    df["name"] = df["name"].str.strip().str.capitalize()
    df["gender"] = clean_gender(df["gender"])
    df["birth_date"] = parse_birth(df["birth_date"])
    df["city"] = clean_city(df["city"])
    df["phone"] = clean_phone(df["phone"])
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["bonus"] = clean_bonus(df["bonus"])
    df["source"] = df["source"].str.strip().str.lower().replace(SYNONYMS)
    return (df.sort_values("signup_date")
              .drop_duplicates(subset=["client_id"], keep="last")
              .reset_index(drop=True))

def report(raw, orders):
    clients = clean_clients(raw)
    stats = orders.groupby("client_id").agg(orders=("order_id", "count"), revenue=("amount", "sum"))
    guests = clients.merge(stats, on="client_id", how="left")
    guests[["orders", "revenue"]] = guests[["orders", "revenue"]].fillna(0)
    age = (pd.Timestamp("2026-12-01") - guests["birth_date"]).dt.days // 365.25
    active = guests[guests["orders"] > 0]
    return {
        "clients": len(guests),
        "active_pct": round((guests["orders"] > 0).mean() * 100, 1),
        "median_age": age.median(),
        "avg_revenue_active": round(active["revenue"].mean(), 1),
    }

raw = pd.read_csv("clients_raw.csv")
orders = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
report(raw, orders)
```

### explain
Глава 3 пройдена. Теперь отчёт по гостям пересчитывается одной строкой на любой новой выгрузке: очистка, проверки и метрики собраны в функции. Следующая глава — исследовательский анализ и графики: научимся смотреть на распределения и связи глазами.
