---
title: "Очистка целиком: функция и проверки"
lead: "Через месяц маркетинг пришлёт новую выгрузку анкет — и всю очистку придётся повторять. Собираем шаги прошлых уроков в функции, которые запускаются одной строкой, ведём журнал потерь, проверяем результат автоматически и сохраняем чистые данные."
files: [clients_raw.csv]
recap:
  - "Каждый шаг очистки — маленькая функция «столбец → столбец» или «таблица → таблица». Вся очистка — функция, которая их вызывает."
  - "`raw.pipe(f).pipe(g)` — то же, что `g(f(raw))`, но читается сверху вниз."
  - "Сырые данные не меняем: функция возвращает новую таблицу, файл `*_raw` остаётся как есть."
  - "Менять часть таблицы — одной операцией: `df.loc[df[\"bonus\"] < 0, \"bonus\"] = 0`. Цепочка `df[условие][\"col\"] = v` меняет копию (в pandas 3 — `ChainedAssignmentError`, в старых версиях — `SettingWithCopyWarning`)."
  - "Copy-on-Write (pandas 3): таблица, полученная из другой, ведёт себя как копия. Но функция получает ту же таблицу — внутри нужен `df = df.copy()`."
  - "Журнал потерь: сколько строк было до и после каждого шага."
  - "Контракт — проверки результата через `assert`: ключ уникален и без пропусков, значения из допустимого списка, числа в разумных границах."
  - "Сохранение: `df.to_csv(\"clients_clean.csv\", index=False)`. Даты при чтении CSV снова станут текстом — `parse_dates=[…]`."
---

## Проблема: очистка в двадцати ячейках

За прошлые уроки главы мы научились чистить каждый столбец анкет. Если всё это лежит в блокноте двадцатью ячейками вперемешку с экспериментами, через месяц будет трудно:

- вспомнить, какие ячейки нужны, а какие были пробой;
- запустить их в правильном порядке (ловушка из урока «Своё рабочее место — uv и Jupyter» главы 2);
- убедиться, что новая выгрузка очищена так же, как старая.

Решение — собрать очистку в **функции**. Тогда новая выгрузка очищается одной строкой: `clients = clean_clients(raw)`.

## Шаг очистки — функция

Начнём с функций для отдельных столбцов. Каждая получает Series и возвращает очищенную Series:

```python
import pandas as pd

def clean_city(s):
    return (s.str.strip().str.lower()
             .str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"})
             .str.capitalize())

def clean_phone(s):
    return s.str.replace(r"\D", "", regex=True).str[-10:]

test = pd.Series([" г. Пермь", "ЕКБ", None])
print(clean_city(test).tolist())
print(clean_phone(pd.Series(["8 (912) 345-67-89"])).tolist())
```

### Разберём вместе: значение проходит через функцию

Проследим, что `clean_city` делает с каждым из трёх тестовых значений, шаг за шагом:

| шаг | « г. Пермь» | «ЕКБ» | None |
|---|---|---|---|
| `str.strip()` | «г. Пермь» | «ЕКБ» | None |
| `str.lower()` | «г. пермь» | «екб» | None |
| `str.removeprefix("г.")` | « пермь» | «екб» | None |
| `str.strip()` | «пермь» | «екб» | None |
| `replace({"екб": …})` | «пермь» | «екатеринбург» | None |
| `str.capitalize()` | **«Пермь»** | **«Екатеринбург»** | **None** |

1. Второй `strip()` нужен, потому что после «г.» остался пробел.
2. `replace` со словарём меняет только ячейку целиком — «екб» заменилось, а «пермь» прошла насквозь.
3. Пропуск проходит через все методы `.str` без ошибки и остаётся пропуском.

Три тестовых значения выбраны не случайно: пробел + префикс, сокращение и пропуск — это три разные ветки логики. Хороший тест проверяет каждую ветку хотя бы одним значением.

Маленькие функции удобно проверять по отдельности: подали несколько хитрых значений — посмотрели на ответ. Если в следующей выгрузке появится новый вариант написания, исправлять придётся в одном месте.

{{practice: fn-city, fn-gender, fn-bonus}}

## Таблица → таблица: pipe

Шаги, которые работают со всей таблицей (удалить дубли, нормализовать ключ, оставить свежие анкеты), оформляем как функции «таблица → таблица». Соединяет их метод `pipe`:

```python
import pandas as pd

def drop_exact(df):
    return df.drop_duplicates()

def fix_ids(df):
    df = df.copy()
    df["client_id"] = df["client_id"].str.strip().str.upper()
    return df

def keep_latest(df):
    return (df.sort_values("signup_date")
              .drop_duplicates(subset=["client_id"], keep="last")
              .reset_index(drop=True))

raw = pd.read_csv("clients_raw.csv")
clients = raw.pipe(drop_exact).pipe(fix_ids).pipe(keep_latest)
print(len(raw), "→", len(clients))
```

`raw.pipe(drop_exact)` — то же самое, что `drop_exact(raw)`. Польза в том, что цепочка читается сверху вниз в порядке выполнения, а не изнутри наружу: `keep_latest(fix_ids(drop_exact(raw)))`.

`df.copy()` в начале `fix_ids` — привычка: функция работает с копией и не меняет таблицу, которую ей передали. Сырые данные остаются нетронутыми, и любой шаг можно перезапустить.

::: sql
Цепочка `pipe` похожа на цепочку CTE в SQL: `WITH a AS (…), b AS (SELECT … FROM a), c AS (SELECT … FROM b) SELECT * FROM c`. Каждый шаг берёт результат предыдущего.
:::

{{practice: p-pipe}}

## Изменить часть таблицы: .loc, копии и Copy-on-Write

В очистке постоянно нужно «исправить значение в строках, где выполнено условие»: отрицательный баланс → 0, заглушку → пропуск. Хочется написать так, как говорим: «возьми строки, где бонус меньше нуля, и поставь в столбце bonus ноль» — `df[df["bonus"] < 0]["bonus"] = 0`. Код выполнится, но таблица **не изменится**. Это одна из самых частых ловушек pandas.

::: tip Аналогия
`df[df["bonus"] < 0]` — это ксерокопия нужных страниц журнала. `["bonus"] = 0` — исправление, сделанное ручкой на ксерокопии. Сам журнал остался прежним. `df.loc[условие, "bonus"] = 0` — исправление прямо в журнале. Где аналогия хромает: pandas не всегда делает «ксерокопию» на самом деле, но в pandas 3 ведёт себя так, будто сделал.
:::

::: sql
`UPDATE clients SET bonus = 0 WHERE bonus < 0` — одна команда: где, что и на что. В pandas ей соответствует одна операция `df.loc[df["bonus"] < 0, "bonus"] = 0`, а не цепочка из двух квадратных скобок.
:::

### Игрушечный пример: три баланса

Балансы 100, −50, 300.

1. **Цепочка** `df[df["bonus"] < 0]["bonus"] = 0`. Шаг первый: `df[df["bonus"] < 0]` создаёт **новую** таблицу из одной строки (−50). Шаг второй: в этой новой таблице баланс становится 0. Новую таблицу никто не сохранил, а `df` по-прежнему 100, −50, 300.
2. **`.loc`** `df.loc[df["bonus"] < 0, "bonus"] = 0` — один шаг: в самой `df` строки по условию, столбец `bonus`, значение 0. Получается 100, 0, 300.

```python
import pandas as pd
df = pd.DataFrame({"bonus": [100, -50, 300]})
df[df["bonus"] < 0]["bonus"] = 0          # цепочка: меняем копию
print("цепочка:", df["bonus"].tolist())
df.loc[df["bonus"] < 0, "bonus"] = 0      # .loc: меняем саму таблицу
print(".loc:   ", df["bonus"].tolist())
```

Что здесь происходит:

- В выводе сначала появится предупреждение `ChainedAssignmentError`: pandas заметил присваивание в цепочке и подсказывает `.loc[row_indexer, col_indexer] = value`. Это именно предупреждение, а не ошибка: код продолжает работать дальше.
- `цепочка: [100, -50, 300]` — таблица не изменилась.
- `.loc[условие, "bonus"]` — строки по маске и столбец по имени в одних скобках; присваивание идёт в саму `df`.

::: figure chained-assign
Три баланса и два способа «поставить 0 там, где минус». Цепочка скобок правит новую таблицу, которую никто не сохранил; `.loc` правит саму `df`.
:::

### Что изменилось в pandas 3: Copy-on-Write

В pandas 3 (он работает и в браузере курса) включён режим **Copy-on-Write** — «копировать при записи». Правило одно: любая таблица или столбец, полученные из другой таблицы (`df[маска]`, `df["bonus"]`, `df.head()`), ведут себя как **независимая копия**. Меняете её — исходная таблица не меняется, и наоборот. Поэтому присваивание через цепочку скобок не срабатывает никогда.

В старых версиях было запутаннее, и вы встретите это в чужих блокнотах и ответах на форумах:

| код | pandas 1.x–2.x | pandas 3 |
|---|---|---|
| `df[маска]["col"] = v` | `SettingWithCopyWarning`, таблица не меняется | `ChainedAssignmentError`, таблица не меняется |
| `df["col"][маска] = v` | часто срабатывало, иногда с предупреждением | `ChainedAssignmentError`, таблица не меняется |
| `sub = df[маска]`, затем `sub["col"] = v` | `SettingWithCopyWarning`, меняется только `sub` | без предупреждений, меняется только `sub` |
| `df.loc[маска, "col"] = v` | работает | работает |

Текст старого предупреждения — «A value is trying to be set on a copy of a slice from a DataFrame». Оба предупреждения лечатся одинаково: присваивать через `.loc` одной операцией. Версию pandas покажет `pd.__version__`.

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"bonus": [100, -50, 300]})
neg = df[df["bonus"] < 0]
neg["bonus"] = 0
print(df["bonus"].tolist(), neg["bonus"].tolist())
```

- `[100, 0, 300] [0]`
- [x] `[100, -50, 300] [0]`
- `[100, -50, 300] [-50]`

Почему: `neg` — отдельная таблица из одной строки. Её столбец поменялся, а `df` — нет: при Copy-on-Write изменения не перетекают между таблицами. Если вам нужна именно отдельная таблица для правок, напишите это явно — `neg = df[df["bonus"] < 0].copy()`: так понятнее читателю, и старый pandas не будет предупреждать.
:::

### А вот функция меняет то, что ей дали

Copy-on-Write защищает от изменений через **другую** таблицу. Если в функцию передали саму таблицу, функция работает с ней же, а не с копией, — и присваивание столбца изменит исходные данные:

```python
import pandas as pd

def add_flag(t):
    t["flag"] = True        # t — это та же таблица, что raw
    return t

raw = pd.DataFrame({"a": [1, 2]})
out = add_flag(raw)
print(raw.columns.tolist())
```

`raw` получил столбец `flag`, хотя мы его не трогали. Поэтому в функциях очистки выше стоит `df = df.copy()` в начале: функция возвращает новую таблицу, а сырые данные остаются как были.

::: tip Аналогия
Передать функции таблицу — как дать коллеге не копию файла, а ссылку на общий документ: всё, что он поправит, увидят все, у кого есть ссылка. `t = t.copy()` в начале функции — «сначала сделай себе копию и правь её». Где аналогия хромает: в документе видна история правок, а в таблице следов не останется — столбец просто появится.
:::

::: figure func-copy
Слева функция правит ту же таблицу, что лежит в `raw`; справа `t.copy()` делает отдельную таблицу, и `raw` остаётся как был.
:::

::: warn Типичные ошибки
- **Цепочка скобок при присваивании.** `df[условие]["col"] = v` или `df["col"][условие] = v` — таблица не меняется, в выводе `ChainedAssignmentError` (в старом pandas — `SettingWithCopyWarning`). Исправление — `df.loc[условие, "col"] = v`.
- **Игнорировать предупреждение.** Оно не роняет код, поэтому его легко пролистать — а потом искать, почему отрицательные бонусы остались в отчёте. Предупреждение о копии — всегда повод переписать строку.
- **Править срез и ждать изменений в исходной таблице.** `top = df.head(10)` и `top["x"] = 0` меняют только `top`.
- **Функция без `copy()`.** Присваивание столбца внутри функции меняет переданную таблицу — перезапуск ячейки даст другой результат.
:::

{{practice: fix-chain}}

## Журнал потерь

На каждом шаге очистки строки могут пропадать. Нужно знать, сколько и где: если шаг «удалить дубли» вдруг выбросил половину таблицы — что-то пошло не так. Простой журнал — список пар «шаг, сколько строк осталось»:

```python
import pandas as pd
raw = pd.read_csv("clients_raw.csv")
log = [("загрузка", len(raw))]

df = raw.drop_duplicates()
log.append(("полные дубли", len(df)))

df = df.assign(client_id=df["client_id"].str.strip().str.upper())
df = df.sort_values("signup_date").drop_duplicates(subset=["client_id"], keep="last")
log.append(("повторные анкеты", len(df)))

for step, n in log:
    print(f"{step:<20}{n:>5}")
```

`assign(столбец=значение)` возвращает новую таблицу с добавленным или заменённым столбцом — удобная замена `df["col"] = …`, когда не хочется менять `df` на месте.

Журнал стоит положить в отчёт: «из 307 строк выгрузки после очистки осталось 293 анкеты: 8 полных дублей, 6 повторных анкет».

::: figure clean-pipeline
Очистка анкет как цепочка шагов. Под каждым шагом — сколько строк осталось.
:::

{{practice: log}}

## Контракт: проверки результата

После очистки данные должны удовлетворять правилам — **контракту**. Например, для анкет:

- номер карты есть у всех и уникален;
- пол — только «М», «Ж» или пропуск;
- город — один из известных или пропуск;
- бонусы — от 0 до 10 000 или пропуск.

Каждое правило — одна строка `assert` (урок «Исключения — как не падать на грязных данных» главы 1). Если правило нарушено, проверка остановит выполнение с понятным сообщением:

```python
import pandas as pd

def check_clients(df):
    assert df["client_id"].notna().all(), "есть анкеты без номера карты"
    assert df["client_id"].is_unique, "номера карт повторяются"
    assert df["gender"].dropna().isin(["М", "Ж"]).all(), "неизвестные значения пола"
    assert df["bonus"].dropna().between(0, 10_000).all(), "бонусы вне границ"

good = pd.DataFrame({"client_id": ["C1", "C2"], "gender": ["М", None], "bonus": [100, None]})
check_clients(good)
print("контракт выполнен")
```

А вот что будет с плохими данными:

```python error
import pandas as pd

def check_clients(df):
    assert df["client_id"].is_unique, "номера карт повторяются"

bad = pd.DataFrame({"client_id": ["C1", "C1"]})
check_clients(bad)
```

Проверки контракта запускают в конце очистки — каждый раз, на каждой новой выгрузке. Лучше упасть с понятной ошибкой сразу, чем через неделю найти в отчёте гостя, посчитанного дважды.

::: figure contract-gate
Контракт стоит между очисткой и сохранением: файл `clients_clean.csv` появляется, только если все проверки прошли.
:::

::: tip
Пишите в контракт то, что **точно** должно выполняться, и подписывайте каждую проверку. Сообщение «номера карт повторяются» сразу говорит, куда смотреть.
:::

::: quiz
Зачем функции очистки «контракт» — проверки через `assert` в конце?

- [x] Чтобы конвейер остановился с понятным сообщением, если новая выгрузка нарушает правила, а не выдал тихо испорченный отчёт
  > Очистку пишут под знакомые данные. Контракт ловит то, что в них раньше не встречалось, — например, новый город или отрицательный бонус.
- [ ] Чтобы исправлять ошибки в данных
  > `assert` ничего не исправляет: он только проверяет и останавливает.
- [ ] Чтобы ускорить очистку
  > Проверки добавляют немного работы, а не убирают её.
- [ ] Контракт нужен только для больших таблиц
  > Ошибка в данных одинаково портит отчёт и на 300, и на 300 тысячах строк.
:::

{{practice: contract}}

## Сохранить результат

Чистые данные сохраняют в отдельный файл, чтобы дальше анализировать их без повторной очистки:

```python
import pandas as pd
df = pd.DataFrame({"client_id": ["C1", "C2"], "signup_date": pd.to_datetime(["2026-01-05", "2026-02-10"])})
df.to_csv("clients_clean.csv", index=False)
back = pd.read_csv("clients_clean.csv")
print(back.dtypes)
```

Два подвоха:

1. **Индекс.** Без `index=False` pandas запишет номера строк отдельным столбцом, и при чтении появится лишний столбец «Unnamed: 0».
2. **Типы.** CSV — просто текст. Даты при чтении снова станут строками, их нужно разобрать заново: `pd.read_csv(..., parse_dates=["signup_date"])`.

::: predict
```python static
import pandas as pd
pd.DataFrame({"a": [1, 2]}).to_csv("t.csv")
print(pd.read_csv("t.csv").columns.tolist())
```

- `['a']`
- [x] `['Unnamed: 0', 'a']`
- `['index', 'a']`

Почему: без `index=False` в файл записался и индекс — безымянным первым столбцом. При чтении pandas назвал его «Unnamed: 0».
:::

::: deep Форматы, которые помнят типы
Для обмена между блокнотами аналитики часто используют формат **Parquet**: `df.to_parquet("clients.parquet")`. Он хранит типы столбцов (даты остаются датами), сжимает данные и читается в разы быстрее CSV. В браузерной версии курса он недоступен, а на своём компьютере — `uv add pyarrow`, и он работает.
:::

::: warn Типичные ошибки
- **Функция меняет входную таблицу.** Без `df.copy()` присваивание столбца испортит сырые данные, и перезапуск шага даст другой результат.
- **Порядок шагов.** Нормализовать ключ нужно до удаления повторов, флаг пропуска — до заполнения.
- **Нет журнала потерь.** Если шаг молча выбросил половину строк, вы узнаете об этом только по странному отчёту.
- **Контракт без проверки границ.** «Бонус от 0 до 10 000» стоит проверить в коде (`assert`), а не держать в голове.
:::

{{practice: save}}

## Вся очистка анкет

Соберём всё вместе. Эта функция — итог главы 3: каждая строка в ней знакома по одному из уроков.

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
    return born.where(born.between("1926-12-01", "2012-12-01"))   # возраст 14–100

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

clients = clean_clients(pd.read_csv("clients_raw.csv"))
clients.info()
clients.head()
```

В `parse_birth` возраст проверяется через даты, а не через годы, как в уроке «Аномалии и проверка на здравый смысл»: «родился не раньше 1926-12-01 и не позже 2012-12-01» — это и есть возраст от 14 до 100 лет на 1 декабря 2026 (2026 − 100 = 1926, 2026 − 14 = 2012). На наших анкетах оба фильтра оставляют одни и те же 263 даты, зато здесь не нужно отдельно считать возраст.

Сравните `info()` с уроком «Первый осмотр: что не так с данными»: даты стали датами, бонусы — числами, анкеты не повторяются. Пропусков стало больше — это заглушки и невозможные значения, честно превращённые в `NaN`.

{{practice: full, january}}

## Практика

## task: fn-city | Функция для города | warmup

Напишите `clean_city(s)`: получает Series с городами и возвращает очищенную (как в уроке «Строки: чистим и ищем по тексту»).

### starter
```python
import pandas as pd

def clean_city(s):
    ...

clean_city(pd.Series([" г. Пермь", "ЕКБ", "казань ", None]))
```

### check
```python
import pandas as _pd
f = need('clean_city')
t = _pd.Series([' г. Пермь', 'ЕКБ', 'казань ', None, 'г.Уфа', 'Екб', 'Тюмень'])
got = f(t)
assert isinstance(got, _pd.Series), 'clean_city должна возвращать Series.'
want = ['Пермь', 'Екатеринбург', 'Казань', None, 'Уфа', 'Екатеринбург', 'Тюмень']
g = [None if _pd.isna(x) else x for x in got]
assert g == want, f'clean_city({t.tolist()}) = {g}, а нужно {want}.'
```

### hint
Тело функции — цепочка из урока «Строки: чистим и ищем по тексту»: `strip` → `lower` → `removeprefix("г.")` → `strip` → `replace` → `capitalize`. Не забудьте `return`.

### hint
Шаблон: `def clean_city(s):`, на следующей строке `return (s.str.strip().str.lower() ...)` — длинную цепочку удобно взять в скобки и переносить по строкам. Проверьте функцию на примере из заготовки: « г. Пермь» должен стать «Пермь», «ЕКБ» — «Екатеринбург», пропуск — остаться пропуском.

### solution
```python
import pandas as pd

def clean_city(s):
    return (s.str.strip().str.lower()
             .str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"})
             .str.capitalize())

clean_city(pd.Series([" г. Пермь", "ЕКБ", "казань ", None]))
```

## task: fn-gender | Функция для пола | warmup

Напишите `clean_gender(s)`: «М», «м», «муж» → «М»; «Ж», «ж», «жен» → «Ж»; пропуски и всё прочее → пропуск.

### starter
```python
import pandas as pd

def clean_gender(s):
    ...

clean_gender(pd.Series(["М", "муж", "ж", None, "жен "]))
```

### check
```python
import pandas as _pd
f = need('clean_gender')
t = _pd.Series(['М', 'муж', 'ж', None, 'жен ', 'Ж', 'м', 'x'])
g = [None if _pd.isna(x) else x for x in f(t)]
want = ['М', 'М', 'Ж', None, 'Ж', 'Ж', 'М', None]
assert g == want, f'clean_gender({t.tolist()}) = {g}, а нужно {want}.'
```

### hint
Достаточно первой буквы в нижнем регистре: `s.str.strip().str.lower().str[0]`.

### hint
Дальше — словарь через `map`: всё, чего нет в словаре, станет пропуском. Здесь это и нужно.

### solution
```python
import pandas as pd

def clean_gender(s):
    return s.str.strip().str.lower().str[0].map({"м": "М", "ж": "Ж"})

clean_gender(pd.Series(["М", "муж", "ж", None, "жен "]))
```

## task: p-pipe | Цепочка шагов | warmup

Соберите программу: функции-шаги определены, нужно соединить их через `pipe` в правильном порядке и вывести число анкет.

### parsons
```python
import pandas as pd
def fix_ids(df):
    return df.assign(client_id=df["client_id"].str.strip().str.upper())
def keep_latest(df):
    return df.sort_values("signup_date").drop_duplicates(subset=["client_id"], keep="last")
raw = pd.read_csv("clients_raw.csv")
clients = raw.drop_duplicates().pipe(fix_ids).pipe(keep_latest)
print(len(clients))
```

### check
```python
import pandas as _pd
d = _pd.read_csv('clients_raw.csv').drop_duplicates()
want = d['client_id'].str.strip().str.upper().nunique()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Функции нужно определить до того, как их вызывать. Номер карты нормализуют до удаления повторов.

### hint
Цепочка читается сверху вниз: `raw.pipe(первый_шаг).pipe(второй).pipe(третий)`; печать длины — последней.

## task: fn-bonus | Функция для бонусов | base

Напишите `clean_bonus(s)`: убирает пробелы, превращает в число (не-числа → `NaN`) и заменяет на `NaN` значения меньше 0 и больше 10 000.

### starter
```python
import pandas as pd

def clean_bonus(s):
    ...

clean_bonus(pd.Series(["1 250", "—", "-50", "99999", "320", None]))
```

### check
```python
import pandas as _pd
f = need('clean_bonus')
t = _pd.Series(['1 250', '—', '-50', '99999', '320', None, '0', '10 000'])
g = [None if _pd.isna(x) else float(x) for x in f(t)]
want = [1250.0, None, None, None, 320.0, None, 0.0, 10000.0]
assert g == want, f'clean_bonus({t.tolist()}) = {g}, а нужно {want}.'
```

### hint
`b = pd.to_numeric(s.str.replace(" ", ""), errors="coerce")`.

### hint
Затем `b.mask((b < 0) | (b > 10_000))`. Ноль и ровно 10 000 — допустимые значения.

### solution
```python
import pandas as pd

def clean_bonus(s):
    b = pd.to_numeric(s.str.replace(" ", ""), errors="coerce")
    return b.mask((b < 0) | (b > 10_000))

clean_bonus(pd.Series(["1 250", "—", "-50", "99999", "320", None]))
```

### explain
Функция собрала в одном месте три решения из уроков «Типы: из текста в числа и даты» и «Аномалии и проверка на здравый смысл»: пробел-разделитель, прочерк как пропуск и невозможные балансы. Проверка нарочно включает границы — 0 и ровно 10 000: они допустимы, и именно на границах чаще всего ошибаются, перепутав `<` и `<=`.

## task: fix-chain | Почините присваивание | base

Коллега хотел исправить бонусы: отрицательные заменить на 0, а заглушки больше 10 000 — на пропуск. Код выполняется, выводит предупреждения, но таблица не меняется. Исправьте его так, чтобы менялась сама `df`. В `n_fixed` сохраните, сколько значений бонусов изменилось (посчитайте до исправления).

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
df["bonus"] = pd.to_numeric(df["bonus"].str.replace(" ", ""), errors="coerce")

df[df["bonus"] < 0]["bonus"] = 0
df[df["bonus"] > 10_000]["bonus"] = None
n_fixed = 0
```

### check
```python
import pandas as _pd
b = _pd.to_numeric(_pd.read_csv('clients_raw.csv')['bonus'].str.replace(' ', ''), errors='coerce')
want = b.copy()
want[b < 0] = 0
want[b > 10_000] = float('nan')
d = need('df', _pd.DataFrame)
assert (d['bonus'] < 0).sum() == 0, f'В df ещё {(d["bonus"] < 0).sum()} отрицательных бонусов — присваивание через цепочку скобок не меняет таблицу. Используйте .loc[условие, "bonus"].'
assert (d['bonus'] > 10_000).sum() == 0, 'В df остались бонусы больше 10 000.'
assert len(d) == len(b), f'В df {len(d)} строк, а было {len(b)}: строки удалять не нужно, меняйте значения.'
assert d['bonus'].isna().sum() == want.isna().sum(), f'Пропусков в bonus {d["bonus"].isna().sum()}, а должно быть {want.isna().sum()}: заглушки — в NaN, отрицательные — в 0.'
assert (d['bonus'].fillna(-1) == want.fillna(-1)).all(), 'Значения bonus не совпадают с ожидаемыми: отрицательные → 0, больше 10 000 → NaN, остальные без изменений.'
assert need('n_fixed') == ((b < 0) | (b > 10_000)).sum(), f'n_fixed = {need("n_fixed")}. Посчитайте строки, попавшие под любое из двух условий, до исправления.'
assert not has_literal(int(((b < 0) | (b > 10_000)).sum())), 'Посчитайте n_fixed кодом, а не впишите.'
```

### hint
Каждая строка вида `df[условие]["bonus"] = ...` меняет копию. Нужна одна операция: строки и столбец в одних скобках `.loc`.

### hint
`df.loc[df["bonus"] < 0, "bonus"] = 0` — и так же для заглушек с `None`. `n_fixed` считайте **до** присваиваний: потом отрицательных уже не будет.

### hint
`n_fixed = ((df["bonus"] < 0) | (df["bonus"] > 10_000)).sum()` — две маски через `|`, каждая в скобках.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
df["bonus"] = pd.to_numeric(df["bonus"].str.replace(" ", ""), errors="coerce")

n_fixed = ((df["bonus"] < 0) | (df["bonus"] > 10_000)).sum()
df.loc[df["bonus"] < 0, "bonus"] = 0
df.loc[df["bonus"] > 10_000, "bonus"] = None
```

### explain
Исправлено 3 значения: два отрицательных баланса стали нулями, заглушка 99 999 — пропуском. В исходном коде обе строки меняли временные копии, а `df` оставалась прежней: pandas честно предупреждал `ChainedAssignmentError`, но код не падал. Порядок важен в двух местах. `n_fixed` считают до присваиваний: после них отрицательных и заглушек уже нет, и получится 0. А каждое следующее присваивание видит данные, изменённые предыдущим. Здесь это не мешает — новый 0 не больше 10 000, — но если правила пересекаются, порядок строк меняет результат. Ту же задачу решают и без присваивания: `df["bonus"] = df["bonus"].clip(lower=0).mask(df["bonus"] > 10_000)` — новый столбец целиком, как в уроке «Аномалии и проверка на здравый смысл».

## task: save | Сохранить и прочитать | base

Таблица `clients` уже очищена. Сохраните её в `clients_clean.csv` без индекса и прочитайте обратно в `back` так, чтобы `signup_date` снова был датой.

### setup
```python
import pandas as pd
clients = pd.DataFrame({
    "client_id": ["C1000", "C1001", "C1002"],
    "city": ["Пермь", "Казань", None],
    "signup_date": pd.to_datetime(["2025-03-14", "2026-01-20", "2024-11-02"]),
})
```

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
b = need('back', _pd.DataFrame)
assert list(b.columns) == ['client_id', 'city', 'signup_date'], f'Столбцы back: {list(b.columns)}. Лишний «Unnamed: 0» — значит, индекс записался в файл: нужно index=False.'
assert _pd.api.types.is_datetime64_any_dtype(b['signup_date']), f'signup_date прочитался как {b["signup_date"].dtype}. Добавьте parse_dates=["signup_date"].'
f = _pd.read_csv('clients_clean.csv')
assert len(f) == 3, 'В файле clients_clean.csv должно быть 3 строки.'
```

### hint
`clients.to_csv("clients_clean.csv", index=False)`.

### hint
`pd.read_csv("clients_clean.csv", parse_dates=["signup_date"])`.

### solution
```python
import pandas as pd
clients.to_csv("clients_clean.csv", index=False)
back = pd.read_csv("clients_clean.csv", parse_dates=["signup_date"])
```

### explain
CSV хранит только текст: тип «дата» при сохранении теряется, и без `parse_dates` дата вернётся строкой. А без `index=False` в файл попадёт лишний столбец номеров строк, который при чтении превратится в «Unnamed: 0». Обе мелочи ломают следующий шаг тихо — поэтому сразу после сохранения полезно прочитать файл обратно и проверить `dtypes`.

## task: log | Очистка с журналом | base

Напишите `clean_with_log(raw)`, которая возвращает пару `(df, log)`: `df` — анкеты после трёх шагов (полные дубли → нормализация номера → самая свежая анкета), `log` — список пар `(название шага, число строк после шага)`, начиная с `("загрузка", len(raw))`. Всего в журнале 4 записи.

### starter
```python
import pandas as pd

def clean_with_log(raw):
    log = [("загрузка", len(raw))]
    ...

df, log = clean_with_log(pd.read_csv("clients_raw.csv"))
log
```

### check
```python
import pandas as _pd
raw = _pd.read_csv('clients_raw.csv')
before = raw.copy()
res = need('clean_with_log')(raw)
assert isinstance(res, tuple) and len(res) == 2, 'Функция должна возвращать пару: return df, log.'
df, log = res
assert raw.equals(before), 'Функция изменила исходную таблицу — работайте с копией.'
d1 = raw.drop_duplicates()
d2 = d1.assign(client_id=d1['client_id'].str.strip().str.upper())
d3 = d2.sort_values('signup_date').drop_duplicates('client_id', keep='last')
want = [len(raw), len(d1), len(d2), len(d3)]
assert len(log) == 4, f'В журнале {len(log)} записей, а нужно 4.'
assert [n for _, n in log] == want, f'Числа в журнале: {[n for _, n in log]}, а нужно {want}.'
assert log[0][0] == 'загрузка', 'Первая запись — ("загрузка", len(raw)).'
assert df['client_id'].is_unique and len(df) == len(d3), 'В df должны остаться уникальные анкеты.'
```

### hint
После каждого шага добавляйте запись: `log.append(("полные дубли", len(df)))`.

### hint
Нормализацию номера удобно сделать через `assign` — тогда `raw` точно не изменится.

### solution
```python
import pandas as pd

def clean_with_log(raw):
    log = [("загрузка", len(raw))]
    df = raw.drop_duplicates()
    log.append(("полные дубли", len(df)))
    df = df.assign(client_id=df["client_id"].str.strip().str.upper())
    log.append(("нормализация номера", len(df)))
    df = (df.sort_values("signup_date")
            .drop_duplicates(subset=["client_id"], keep="last")
            .reset_index(drop=True))
    log.append(("повторные анкеты", len(df)))
    return df, log

df, log = clean_with_log(pd.read_csv("clients_raw.csv"))
log
```

### explain
Нормализация номера не меняет число строк — и это тоже полезная запись в журнале: шаг отработал и ничего не потерял. Если на новой выгрузке там окажется другое число, значит, что-то пошло не так.

## task: contract | Контракт анкет | plus

Напишите `check_clients(df)` с проверками через `assert`:

- `client_id` без пропусков и уникален;
- `gender` — только «М», «Ж» или пропуск;
- `city` — только «Пермь», «Казань», «Тюмень», «Уфа», «Екатеринбург», «Москва» или пропуск;
- `bonus` — от 0 до 10 000 или пропуск.

Если всё в порядке, функция ничего не возвращает; если нет — падает с `AssertionError`.

### starter
```python
import pandas as pd

def check_clients(df):
    ...

ok = pd.DataFrame({"client_id": ["C1", "C2"], "gender": ["М", None],
                   "city": ["Пермь", None], "bonus": [100.0, None]})
check_clients(ok)
print("контракт выполнен")
```

### check
```python
import pandas as _pd
f = need('check_clients')
base = dict(client_id=['C1', 'C2'], gender=['М', None], city=['Пермь', None], bonus=[100.0, None])
f(_pd.DataFrame(base))
bads = {
    'повтор номера': dict(base, client_id=['C1', 'C1']),
    'пустой номер': dict(base, client_id=['C1', None]),
    'пол «муж»': dict(base, gender=['муж', None]),
    'город «пермь»': dict(base, city=['пермь', None]),
    'бонус −5': dict(base, bonus=[-5.0, None]),
    'бонус 20000': dict(base, bonus=[20000.0, None]),
}
for name, data in bads.items():
    try:
        f(_pd.DataFrame(data))
    except AssertionError:
        continue
    raise AssertionError(f'check_clients не заметила проблему: {name}.')
```

### hint
Значение из списка: `df["gender"].dropna().isin(["М", "Ж"]).all()`. Пропуски убираем, потому что они допустимы.

### hint
Границы: `df["bonus"].dropna().between(0, 10_000).all()`.

### solution
```python
import pandas as pd

CITIES = ["Пермь", "Казань", "Тюмень", "Уфа", "Екатеринбург", "Москва"]

def check_clients(df):
    assert df["client_id"].notna().all(), "есть анкеты без номера карты"
    assert df["client_id"].is_unique, "номера карт повторяются"
    assert df["gender"].dropna().isin(["М", "Ж"]).all(), "неизвестные значения пола"
    assert df["city"].dropna().isin(CITIES).all(), "неизвестный город"
    assert df["bonus"].dropna().between(0, 10_000).all(), "бонусы вне границ"

ok = pd.DataFrame({"client_id": ["C1", "C2"], "gender": ["М", None],
                   "city": ["Пермь", None], "bonus": [100.0, None]})
check_clients(ok)
print("контракт выполнен")
```

### explain
Каждый `assert` — одно правило бизнеса, записанное кодом, а текст после запятой объясняет, какое правило нарушено. `dropna()` перед `isin` и `between` нужен потому, что пропуск по контракту допустим, а `NaN` не входит ни в список, ни в диапазон. Такую функцию вызывают сразу после очистки: если завтра в выгрузке появится «г. Самара» или бонус −50, конвейер остановится с понятным сообщением, а не выдаст тихо испорченный отчёт.

## task: full | Вся очистка одной функцией | plus

Соберите `clean_clients(raw)` — полную очистку анкет. Функции для отдельных столбцов уже написаны в заготовке. Функция должна:

1. убрать полные дубли;
2. нормализовать `client_id` (пробелы, регистр), `name` (пробелы, первая буква заглавная);
3. почистить `gender`, `birth_date`, `city`, `phone`, `bonus` готовыми функциями; `signup_date` превратить в дату; `source` — `strip`, `lower` и словарь `SYNONYMS`;
4. оставить по одной, самой свежей анкете на гостя; индекс — по порядку.

Сохраните результат для `clients_raw.csv` в `clients`.

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

clients = clean_clients(pd.read_csv("clients_raw.csv"))
clients.head()
```

### check
```python
import pandas as _pd
_r = _pd.read_csv('clients_raw.csv')
_d = _r.drop_duplicates().copy()
_d['client_id'] = _d['client_id'].str.strip().str.upper()
_d['name'] = _d['name'].str.strip().str.capitalize()
_d['gender'] = _d['gender'].str.strip().str.lower().str[0].map({'м': 'М', 'ж': 'Ж'})
_b = _pd.to_datetime(_d['birth_date'], format='%Y-%m-%d', errors='coerce').fillna(_pd.to_datetime(_d['birth_date'], format='%d.%m.%Y', errors='coerce'))
_d['birth_date'] = _b.where(_b.between('1926-12-01', '2012-12-01'))
_d['city'] = _d['city'].str.strip().str.lower().str.removeprefix('г.').str.strip().replace({'екб': 'екатеринбург'}).str.capitalize()
_d['phone'] = _d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
_d['signup_date'] = _pd.to_datetime(_d['signup_date'])
_n = _pd.to_numeric(_d['bonus'].str.replace(' ', ''), errors='coerce')
_d['bonus'] = _n.mask((_n < 0) | (_n > 10_000))
_d['source'] = _d['source'].str.strip().str.lower().replace({'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'})
want = _d.sort_values('signup_date').drop_duplicates('client_id', keep='last').set_index('client_id').sort_index()
c = need('clients', _pd.DataFrame)
assert c['client_id'].is_unique, 'Номера карт в clients повторяются.'
assert len(c) == len(want), f'В clients {len(c)} строк, а нужно {len(want)}.'
assert list(c.index) == list(range(len(c))), 'Индекс — по порядку: reset_index(drop=True).'
assert _r.equals(_pd.read_csv('clients_raw.csv')), 'Файл изменился?'
g = c.set_index('client_id').sort_index()
for col in ['name', 'gender', 'birth_date', 'city', 'phone', 'signup_date', 'bonus', 'source']:
    a, w = g[col], want[col]
    same = (a.isna() == w.isna()) & ((a == w) | w.isna())
    assert same.all(), f'Столбец {col} не совпадает, например у {g.index[~same][0]}: {a[~same].iloc[0]!r}, а нужно {w[~same].iloc[0]!r}.'
```

### hint
Начните с `df = raw.drop_duplicates().copy()`, затем столбец за столбцом: `df["gender"] = clean_gender(df["gender"])` и т. д.

### hint
Последний шаг — сортировка по `signup_date`, `drop_duplicates(subset=["client_id"], keep="last")` и `reset_index(drop=True)`. Номер карты нормализуйте до него.

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

clients = clean_clients(pd.read_csv("clients_raw.csv"))
clients.head()
```

### explain
Порядок шагов не случаен. Полные дубли удаляются первыми — это дешёвый шаг, и дальше меньше работы. Номер карты нормализуется до выбора свежей анкеты, иначе «c1023 » и «C1023» посчитались бы разными гостями. Последний шаг — сортировка по дате и `keep="last"`: из версий одного гостя остаётся самая свежая. Итог — 293 анкеты по одной на гостя. Пустых дат рождения 42: это исходные пропуски, «не указано», заглушки и невозможные даты. Пропуск честнее, чем мусор в столбце.

## task: january | Новая выгрузка | star

Пришла январская выгрузка `clients_raw_jan.csv`. В ней появились новые написания города: «гор. Уфа» и «Пермь, Россия». Доработайте `clean_city`, чтобы она справлялась и с ними (и по-прежнему со старыми вариантами), и сохраните в `jan_cities` множество городов январской выгрузки после очистки (без пропусков).

### setup
```python
import pandas as pd
pd.DataFrame({"city": ["гор. Уфа", "Пермь, Россия", " г. Казань", "ЕКБ", "тюмень", None,
                       "Гор. Пермь", "Казань, Россия", "Москва"]}).to_csv("clients_raw_jan.csv", index=False)
```

### starter
```python
import pandas as pd

def clean_city(s):
    return (s.str.strip().str.lower().str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"}).str.capitalize())

jan = pd.read_csv("clients_raw_jan.csv")
jan_cities = set(clean_city(jan["city"]).dropna())
jan_cities
```

### check
```python
import pandas as _pd
f = need('clean_city')
old = _pd.Series([' г. Пермь', 'ЕКБ', 'казань ', 'г.Уфа', 'Екб', 'Тюмень'])
assert [x for x in f(old)] == ['Пермь', 'Екатеринбург', 'Казань', 'Уфа', 'Екатеринбург', 'Тюмень'], f'Старые варианты сломались: {f(old).tolist()}.'
new = _pd.Series(['гор. Уфа', 'Пермь, Россия', 'Гор. Пермь', 'Казань, Россия'])
assert f(new).tolist() == ['Уфа', 'Пермь', 'Пермь', 'Казань'], f'Новые варианты: {f(new).tolist()}.'
assert need('jan_cities') == {'Уфа', 'Пермь', 'Казань', 'Екатеринбург', 'Тюмень', 'Москва'}, f'jan_cities = {need("jan_cities")}.'
```

### hint
«Пермь, Россия»: всё после запятой не нужно — `str.split(",").str[0]`.

### hint
«гор.» убирайте **до** «г.»: иначе от «гор. Уфа» останется «ор. уфа».

### solution
```python
import pandas as pd

def clean_city(s):
    return (s.str.strip().str.lower()
             .str.split(",").str[0]
             .str.removeprefix("гор.").str.removeprefix("г.").str.strip()
             .replace({"екб": "екатеринбург"}).str.capitalize())

jan = pd.read_csv("clients_raw_jan.csv")
jan_cities = set(clean_city(jan["city"]).dropna())
jan_cities
```

### explain
Так и живёт очистка: каждая новая выгрузка приносит пару новых вариантов. Если очистка собрана в функции, правка — две строки в одном месте, а контракт сразу скажет, если что-то пропустили.
