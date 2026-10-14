---
title: Дубликаты — явные и неявные
lead: "Одна и та же запись дважды — значит, выручка посчитана дважды, а гость учтён как двое. Ищем полные копии строк, повторы по ключу и неявные дубли, которые прячутся за разным написанием. И решаем, какую из копий оставить."
files: [clients_raw.csv, pos_december.csv, orders_3m.csv, delivery_flat.csv]
recap:
  - "`df.duplicated()` — `True` у каждой строки, которая уже встречалась выше. `df.duplicated().sum()` — сколько лишних копий."
  - "`df.drop_duplicates()` — убрать полные дубли. `subset=[\"client_id\"]` — дубли только по ключу."
  - "`keep=\"first\"` (по умолчанию) / `\"last\"` — какую копию оставить; `keep=False` в `duplicated` помечает все копии."
  - "Неявные дубли: сначала привести ключ к одному виду (`str.strip().str.upper()`), потом искать повторы."
  - "Оставить самую свежую запись: `sort_values(\"signup_date\").drop_duplicates(\"client_id\", keep=\"last\")` — как `ROW_NUMBER() … = 1` в SQL."
  - "После удаления проверьте: ключ уникален (`is_unique`), сколько строк было и стало."
  - "Справочник из плоской выгрузки: `flat[[\"shop_id\", \"city\", \"manager\"]].drop_duplicates()` → нормализовать написание → самую свежую версию на ключ → `assert ref[\"shop_id\"].is_unique`."
---

## Откуда берутся дубли

- **Двойная выгрузка.** Одну и ту же порцию данных выгрузили или загрузили дважды — получаются полные копии строк.
- **Повторный ввод.** Гость заполнил анкету ещё раз, касса повторно отправила заказ после сбоя связи.
- **Разное написание.** «C1012» и « c1012» — для человека одно, для pandas — разные значения. Это **неявные** дубли: простой поиск копий их не находит.

Чем опасны дубли: в анкетах один гость посчитается дважды, в заказах — выручка завысится. И снова никакой ошибки: просто неверные цифры.

## Полные копии строк

`duplicated()` проходит по таблице сверху вниз и помечает `True` строку, если точно такая же уже встречалась выше. Первое появление остаётся `False`:

```python
import pandas as pd
t = pd.DataFrame({"id": ["A", "B", "A", "A"], "v": [1, 2, 1, 5]})
t["dup"] = t.duplicated()
t
```

Строка 2 — полная копия строки 0. Строка 3 повторяет `id`, но `v` другое, поэтому это не полный дубль.

::: predict
```python static
import pandas as pd
s = pd.Series(["a", "b", "a", "a"])
print(s.duplicated().sum())
```

- `3`
- [x] `2`
- `1`

Почему: первое «a» — оригинал, два следующих — повторы. `duplicated().sum()` показывает, сколько строк **лишние**, а не сколько всего строк участвуют в повторах.
:::

В анкетах:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
print("полных дублей:", df.duplicated().sum())
df[df.duplicated(keep=False)].sort_values("client_id").head(6)
```

`keep=False` помечает **все** копии, включая оригинал, — удобно, чтобы посмотреть на повторы целиком.

::: figure dup-keep
Одна таблица — три ответа `duplicated()`. `True` — строка, которую считают лишней; от `keep` зависит, какую из копий считать оригиналом.
:::

Удаляет полные дубли `drop_duplicates()`. Индексы у оставшихся строк сохраняются старые, с дырками; если нужна нумерация по порядку, добавьте `reset_index(drop=True)`:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
clean = df.drop_duplicates().reset_index(drop=True)
print(len(df), "→", len(clean))
```

::: sql
`drop_duplicates()` — это `SELECT DISTINCT * FROM clients`.
:::

{{practice: n-exact, drop-exact}}

## Повторы по ключу

Полные дубли убраны. Проверим ключ — номер карты. `subset` говорит, по каким столбцам сравнивать строки:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
print("номера уникальны:", df["client_id"].is_unique)
print("повторов номера:", df.duplicated(subset=["client_id"]).sum())
```

Номера уникальны — кажется, всё в порядке. Но `duplicated` и `is_unique` сравнивают значения как есть, символ в символ. Посмотрим на номера, которые записаны не так, как остальные:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
ids = df["client_id"]
ids[ids.str.strip().str.upper() != ids].tolist()
```

Вот они — неявные дубли: «c1012» строчными, номера с пробелами по краям.

{{practice: p-pos}}

## Неявные дубли: сначала нормализовать

Правило: **прежде чем искать дубли, приведите ключ к одному виду**. Для номера карты — убрать пробелы и перевести в верхний регистр:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
df["client_id"] = df["client_id"].str.strip().str.upper()
print("повторов номера:", df.duplicated(subset=["client_id"]).sum())
df[df.duplicated(subset=["client_id"], keep=False)].sort_values("client_id").head(6)
```

У пар одинаковые номера, но разные даты анкеты и балансы бонусов: гость заполнил анкету повторно.

::: tip Аналогия
Список гостей на свадьбу, который вели три родственника: «Иванова А.», «А. Иванова» и «иванова анна». Чтобы увидеть, что это один человек, сначала всех переписывают в одном виде — «Иванова А.», — и только потом вычёркивают повторы. Только человек догадается и без переписывания, а pandas сравнивает строки символ в символ.
:::

::: predict
```python static
import pandas as pd
s = pd.Series(["x1", " x1", "X1"])
print(s.nunique(), s.str.strip().str.lower().nunique())
```

- `1 1`
- `3 3`
- [x] `3 1`

Почему: до нормализации три разные строки, после `strip()` и `lower()` — одна.
:::

{{practice: norm-id, versions}}

## Какую копию оставить

Когда дубли по ключу отличаются в других полях, нужно решить, какую строку оставить. Частое правило — **самую свежую**: отсортировать по дате и оставить последнюю копию (`keep="last"`):

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
df["client_id"] = df["client_id"].str.strip().str.upper()
clients = (df.sort_values("signup_date")
             .drop_duplicates(subset=["client_id"], keep="last")
             .reset_index(drop=True))
print(len(df), "→", len(clients), "| уникальны:", clients["client_id"].is_unique)
```

Даты в `signup_date` записаны как «2026-03-10» — год, месяц, день. Такие строки сортируются правильно даже без превращения в даты. Для дат вида «10.03.2026» это не так: сначала `to_datetime`.

::: sql
В SQL то же самое делают оконной функцией:

```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY signup_date DESC) AS rn
  FROM clients
) t WHERE rn = 1
```
:::

::: warn
Ищите дубли только по **ключу** — по тому, что действительно определяет запись. Два гостя по имени Анна из Перми — это, скорее всего, два разных человека. Если искать повторы по имени и городу, вы склеите разных людей.
:::

### Разберём вместе: от 307 анкет к 293 гостям

Проследим, как меняется число строк на каждом шаге.

1. **Сырая выгрузка** — 307 анкет.
2. **Полные дубли** — 8 строк совпадают целиком (анкету отправили дважды). `drop_duplicates()` → **299**.
3. **Повторы номера карты до нормализации** — 0. Кажется, всё чисто.
4. **Нормализация** `client_id`: `.str.strip().str.upper()` — « C1012» и «c1012» становятся «C1012». Повторов номера — уже **6**.
5. **По одной анкете на гостя** → 299 − 6 = **293** гостя.

Какую из двух анкет оставить? Возьмём гостя C1012:

| анкета | дата | бонусы |
|---|---|---|
| первая | 2024-04-21 | 80 |
| вторая | 2024-07-11 | 640 |

Если оставить первую (`keep="first"` без сортировки), у гостя 80 бонусов, если самую свежую — 640. Разница в 8 раз — для рассылки «у вас скоро сгорят бонусы» это совсем разные письма. Правило «оставляем самую свежую по `signup_date`» нужно сформулировать до удаления, а не после.

Что получилось: шаг 3 показывает главную ловушку — «повторов нет» до нормализации ничего не значит. Сначала приводим ключ к одному виду, потом ищем повторы.

::: figure dedup-latest
Две пары повторных анкет из `clients_raw.csv`. Без нормализации повторов не видно, без сортировки `keep="last"` берёт последнюю по порядку в файле, а не по дате.
:::

::: quiz
Гость заполнял анкету дважды: в марте и в сентябре, и номера телефона в анкетах разные. Какую анкету оставить?

- [x] Сентябрьскую: отсортировать по дате анкеты и `drop_duplicates(subset=["client_id"], keep="last")`
  > Самая свежая анкета вероятнее всего содержит актуальные данные. Сортировка нужна, чтобы «последняя» значило «по дате», а не «по порядку в файле».
- [ ] Любую — они про одного человека
  > Данные в них различаются, и от выбора зависит, на какой номер уйдёт SMS.
- [ ] Обе: это не дубль, раз телефоны разные
  > Номер карты один, значит и гость один. Две строки на гостя задвоят его во всех подсчётах.
- [ ] Первую, `keep="first"`, без сортировки
  > «Первая» будет первой по порядку в файле, а он не обязательно идёт по датам.
:::

{{practice: keep-last, dedupe-fn}}

## Дубли в заказах

В кассовой выгрузке ключ — номер заказа `id`. Касса иногда отправляет заказ повторно:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
print("повторов id:", pos.duplicated(subset=["id"]).sum())
print("полных дублей:", pos.duplicated().sum())
pos[pos.duplicated(subset=["id"], keep=False)]
```

Здесь повторы по ключу совпадают с полными дублями — это технический сбой, удаляем смело. Если бы у одного `id` были разные суммы, удалять вслепую было бы нельзя: сначала выяснить, какая версия правильная.

::: warn Типичные ошибки
- **`drop_duplicates()` на сырых ключах.** Пробелы и регистр прячут повторы.
- **`keep="first"` без сортировки.** «Первая» строка — какая попалась в выгрузке, а не самая старая и не самая свежая.
- **Удалили и не посчитали.** Сколько строк ушло на каждом шаге — часть отчёта.
- **Дубли по неполному ключу.** Два заказа одного гостя в один день — не дубль; ключ заказа — его номер.
:::

::: note Чек-лист работы с дублями
1. Убрать полные копии строк: `drop_duplicates()`.
2. Нормализовать ключ: пробелы, регистр, лишние символы.
3. Найти повторы ключа: `duplicated(subset=[ключ], keep=False)` — и посмотреть на них глазами.
4. Решить, какую копию оставить (самую свежую, самую полную) — и записать правило.
5. Проверить: `is_unique` для ключа, сколько строк было и стало.
:::

::: quiz
В кассовой выгрузке у двух строк один и тот же `id`, но суммы разные: 250 и 350 ₽. Что делать?

- [x] Не удалять вслепую: выяснить у кофейни, какая версия правильная, и записать решение
  > Это уже не технический повтор, а две разные версии заказа. Любой автоматический выбор — догадка.
- [ ] `drop_duplicates()` — и одна из строк уйдёт
  > Полный дубль ищется по всем столбцам, а суммы разные — `drop_duplicates()` оставит обе строки.
- [ ] Оставить обе: раз суммы разные, это два разных заказа
  > Номер заказа — ключ, и он один. Если оставить обе строки, выручка по этому заказу задвоится.
- [ ] `drop_duplicates(subset=["id"])` — оставит первую, этого достаточно
  > Оставит ту, что первой попалась в файле. Правильная ли она — неизвестно.
:::

{{practice: dup-ids, overcount}}

## Справочник из плоской выгрузки

Партнёр по доставке присылает заказы одной широкой таблицей — `delivery_flat.csv`. Отдельного справочника кофеен у него нет, поэтому в каждой из 801 строки заново записаны адрес кофейни, город и управляющий. Нам нужен **справочник**: одна строка на кофейню. С ним можно соединять другие таблицы по `shop_id` (как `merge` в главе 2), отвечать на вопрос «кто управляющий в Казани» и не хранить восемьсот копий одного адреса.

Собрать справочник — та же работа с дублями, что и выше, только дубли ищем не среди заказов, а среди **атрибутов кофейни**: из каждой строки берём столбцы кофейни, убираем повторы и проверяем, что ключ `shop_id` стал уникальным.

::: sql
`SELECT DISTINCT shop_id, shop_address, city, manager FROM delivery` — и затем проверка `GROUP BY shop_id HAVING COUNT(*) > 1`: у ключа не должно остаться двух версий. В Excel — скопировать столбцы кофейни на новый лист и нажать «Удалить дубликаты».
:::

### Игрушечный пример: пять заказов — две кофейни

| заказ | shop_id | город | управляющий |
|---|---|---|---|
| 1 | A | Пермь | Ольга |
| 2 | B | Казань | Рустам |
| 3 | A | Пермь | Ольга |
| 4 | B | казань | Рустам |
| 5 | B | Казань | Тимур |

1. **Убрать повторы атрибутов.** Заказ 3 повторяет заказ 1 — остаются 4 строки: A–Пермь–Ольга, B–Казань–Рустам, B–казань–Рустам, B–Казань–Тимур. Ключ B встречается трижды — это ещё не справочник.
2. **Нормализовать написание.** «казань» → «Казань», и строки 2 и 4 совпали. Осталось 3 строки, но у B по-прежнему две версии: Рустам и Тимур.
3. **Разобраться с настоящим различием.** Это уже не опечатка: управляющий сменился. Правило — взять самую свежую версию (заказ 5). Итог — 2 строки: A–Пермь–Ольга и B–Казань–Тимур, ключ уникален.

::: figure ref-from-flat
Игрушка из пяти заказов: убрать повторы атрибутов, нормализовать написание, взять самую свежую версию — и проверить, что ключ уникален.
:::

### На настоящей выгрузке

Те же три шага. Сначала просто убираем повторы атрибутов:

```python
import pandas as pd
flat = pd.read_csv("delivery_flat.csv")
cols = ["shop_id", "shop_address", "city", "manager"]
ref = flat[cols].drop_duplicates()
print("строк:", len(flat), "| версий кофеен:", len(ref), "| shop_id уникален:", ref["shop_id"].is_unique)
ref.sort_values("shop_id")
```

Что здесь происходит:

- `flat[cols]` — только столбцы кофейни: всё, что относится к заказу (напиток, цена, дата), в справочник не идёт.
- `drop_duplicates()` оставляет по одной строке на каждую **разную** комбинацию атрибутов.
- `is_unique` по ключу — главная проверка справочника. Здесь `False`: из 801 строки получилось 10 версий на 7 кофеен.

Как читать результат: у KZN-1 город записан и «Казань», и «казань», у TMN-1 — «Тюмень» и «Тюмень » с пробелом в конце. Это грязь написания — её нормализуем, как в уроке про неявные дубли:

```python
import pandas as pd
flat = pd.read_csv("delivery_flat.csv")
cols = ["shop_id", "shop_address", "city", "manager"]
flat["city"] = flat["city"].str.strip().str.capitalize()
ref = flat[cols].drop_duplicates()
print("версий:", len(ref), "| shop_id уникален:", ref["shop_id"].is_unique)
print(ref[ref["shop_id"].duplicated(keep=False)])
flat.groupby(["shop_id", "manager"])["date"].agg(["min", "max"]).loc["KZN-2"]
```

Что здесь происходит:

- `str.strip().str.capitalize()` убирает пробелы по краям и делает первую букву заглавной, остальные — строчными. Для городов из одного слова этого хватает; «нижний новгород» превратился бы в «Нижний новгород», и для таких названий нужен `str.title()` — заглавная буква у каждого слова.
- `duplicated(keep=False)` показывает **все** версии ключа, у которого их больше одной.
- `groupby(["shop_id", "manager"])["date"].agg(["min", "max"])` — с какой по какую дату встречается каждый управляющий.
- После группировки по двум столбцам индекс **двухуровневый** (такой же получался в уроке «Группировки: GROUP BY и HAVING» главы 2, а в уроке «Сводные таблицы: широкий и длинный формат» он назывался `MultiIndex`): у каждой строки пара «кофейня, управляющий». `.loc["KZN-2"]` задаёт только первый уровень и поэтому возвращает все строки, где кофейня — KZN-2, сколько бы управляющих там ни было.

Осталось 8 версий: у KZN-2 два управляющих. Даты показывают, что это не опечатка: Алина Сафина — с 1 октября по 9 ноября, Тимур Гарипов — с 10 ноября. Управляющий сменился. Для справочника «как сейчас» берём самую свежую версию — как самую свежую анкету выше:

```python
import pandas as pd
flat = pd.read_csv("delivery_flat.csv")
cols = ["shop_id", "shop_address", "city", "manager"]
flat["city"] = flat["city"].str.strip().str.capitalize()
shops = (flat.sort_values("date")
             .drop_duplicates(subset=["shop_id"], keep="last")[cols]
             .sort_values("shop_id")
             .reset_index(drop=True))
assert shops["shop_id"].is_unique, "в справочнике повторяется код кофейни"
shops
```

Что получилось: 7 строк — по одной на кофейню, ключ уникален, у KZN-2 текущий управляющий. Даты в `date` записаны как «2026-10-01 09:44» — год впереди, поэтому строки сортируются правильно и без перевода в даты.

::: deep История изменений
Справочник «как сейчас» теряет историю: по нему уже не узнать, кто руководил KZN-2 в октябре. Если история нужна, в справочнике оставляют все версии и добавляют столбцы «действует с» и «действует по» — это те самые `min` и `max` дат из примера выше. В хранилищах данных такой справочник называют медленно меняющимся измерением (SCD, тип 2).
:::

::: warn Типичные ошибки
- **Справочник без проверки ключа.** `drop_duplicates()` по атрибутам не гарантирует одну строку на кофейню: любая опечатка в городе даёт вторую версию. Симптом — после `merge` с таким справочником строк становится больше, чем было заказов. Проверка — `assert shops["shop_id"].is_unique`.
- **В справочник попали атрибуты заказа.** Если взять в `cols` напиток или дату, «версий» кофейни станут сотни.
- **Склеили настоящие изменения как опечатки.** Смена управляющего — не грязь. Сначала посмотрите на даты версий, потом решайте: оставить самую свежую или хранить историю.
:::

{{practice: price-list, shops-ref}}

## Практика

## task: n-exact | Полные копии | warmup

Сохраните в `n_exact` число полных дублей строк в анкетах.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
want = _pd.read_csv('clients_raw.csv').duplicated().sum()
got = need('n_exact')
assert got != 2 * want, f'n_exact = {got} — похоже, посчитаны и оригиналы (keep=False). Нужно число лишних копий.'
assert got == want, f'n_exact = {got}, а нужно {want}.'
```

### hint
`duplicated()` помечает `True` каждую строку, которая уже встречалась выше целиком.

### hint
`n_exact = df.duplicated().sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
n_exact = df.duplicated().sum()
```

## task: drop-exact | Убрать копии | warmup

Сохраните в `clean` анкеты без полных дублей, с индексом по порядку от 0.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('clients_raw.csv')
c = need('clean', _pd.DataFrame)
assert len(c) == len(d.drop_duplicates()), f'В clean {len(c)} строк, а нужно {len(d.drop_duplicates())}.'
assert list(c.index) == list(range(len(c))), 'Индекс должен идти 0, 1, 2, … — добавьте reset_index(drop=True).'
```

### hint
После удаления строк индекс идёт с пропусками (0, 1, 3, …) — его нужно пересобрать.

### hint
`df.drop_duplicates().reset_index(drop=True)`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
clean = df.drop_duplicates().reset_index(drop=True)
```

## task: p-pos | Касса без повторов | warmup

Соберите программу, которая убирает повторно отправленные заказы и выводит, сколько заказов осталось.

### parsons
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
pos = pos.drop_duplicates(subset=["id"])
print(len(pos))
```

### check
```python
import pandas as _pd
want = _pd.read_csv('pos_december.csv', sep=';')['id'].nunique()
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Загрузка → удаление дублей → вывод.

### hint
Повтор заказа — одинаковый `id`: `drop_duplicates(subset=["id"])`, затем `print(len(...))`.

## task: norm-id | Нормализовать номер карты | base

Уберите полные дубли, затем приведите `client_id` к одному виду: без пробелов по краям, буквы — заглавные. Таблицу сохраните в `df`, а в `n_id_dups` — сколько после этого осталось повторов номера.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
d0 = _pd.read_csv('clients_raw.csv').drop_duplicates()
ids = d0['client_id'].str.strip().str.upper()
d = need('df', _pd.DataFrame)
assert len(d) == len(d0), f'В df {len(d)} строк — уберите только полные дубли, их должно остаться {len(d0)}.'
assert (d['client_id'].str.strip().str.upper() == d['client_id']).all(), 'В client_id остались пробелы по краям или строчные буквы.'
assert need('n_id_dups') == ids.duplicated().sum(), f'n_id_dups = {need("n_id_dups")}, а нужно {ids.duplicated().sum()}.'
```

### hint
`df["client_id"] = df["client_id"].str.strip().str.upper()`.

### hint
Повторы номера — `df.duplicated(subset=["client_id"]).sum()`. Полные дубли убирайте до этого.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
df["client_id"] = df["client_id"].str.strip().str.upper()
n_id_dups = df.duplicated(subset=["client_id"]).sum()
```

### explain
До нормализации повторов номера 0, после — 6. Пробел в начале и строчная «c» превращали одного гостя в двух. Это типичный результат ручного ввода: номер карты набирали на кассе.

## task: keep-last | Самая свежая анкета | base

Оставьте по одной анкете на гостя — самую свежую по `signup_date`. Порядок: полные дубли → нормализация номера → сортировка → удаление повторов. Результат — в `clients` с индексом по порядку.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
d0 = _pd.read_csv('clients_raw.csv').drop_duplicates()
d0['client_id'] = d0['client_id'].str.strip().str.upper()
want = d0.sort_values('signup_date').drop_duplicates('client_id', keep='last')
c = need('clients', _pd.DataFrame)
assert c['client_id'].is_unique, 'Номера карт в clients должны быть уникальны.'
assert len(c) == len(want), f'В clients {len(c)} строк, а нужно {len(want)}. Номер нормализовали?'
w = want.set_index('client_id')['signup_date']
g = c.set_index('client_id')['signup_date']
bad = [k for k in w.index if g.get(k) != w[k]]
assert not bad, f'Для {bad[0]} осталась анкета от {g.get(bad[0])}, а нужна самая свежая — {w[bad[0]]}.'
assert list(c.index) == list(range(len(c))), 'Индекс должен идти по порядку — reset_index(drop=True).'
```

### hint
`df.sort_values("signup_date").drop_duplicates(subset=["client_id"], keep="last")`.

### hint
Не забудьте нормализовать `client_id` до удаления повторов — иначе « C1012» и «C1012» останутся разными гостями.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
df["client_id"] = df["client_id"].str.strip().str.upper()
clients = (df.sort_values("signup_date")
             .drop_duplicates(subset=["client_id"], keep="last")
             .reset_index(drop=True))
```

### explain
Сортировка перед удалением делает правило явным: `keep="last"` после `sort_values("signup_date")` — это «самая свежая анкета». Без сортировки `keep="last"` значило бы «последняя в файле», а порядок строк в выгрузке ничего не гарантирует.

## task: dup-ids | Какие заказы повторились | base

Сохраните в `dup_ids` отсортированный **список** номеров заказов (`id`), которые встречаются в кассовой выгрузке больше одного раза. Каждый номер — один раз.

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")

```

### check
```python
import pandas as _pd
p = _pd.read_csv('pos_december.csv', sep=';')
want = sorted(p.loc[p['id'].duplicated(), 'id'].unique())
assert need('dup_ids') == want, f'dup_ids = {need("dup_ids")}, а нужно {want}.'
```

### hint
`pos[pos.duplicated(subset=["id"])]["id"]` — номера лишних копий.

### hint
Или через подсчёт: `vc = pos["id"].value_counts()`, затем `vc[vc > 1].index`.

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
vc = pos["id"].value_counts()
dup_ids = sorted(vc[vc > 1].index)
```

### explain
Четыре номера заказов повторились — скорее всего, касса отправила их повторно. Список номеров полезнее числа: его можно передать в бухгалтерию, чтобы проверить чеки.

## task: price-list | Прайс из заказов | base

В `orders_3m.csv` нет отдельного прайса, но цена чашки есть в каждом заказе: `amount / qty`. Соберите из заказов справочник цен `prices` — таблицу со столбцами `drink`, `size`, `price`, по одной строке на пару «напиток + размер». В `ok` сохраните `True`, если пара «напиток + размер» в `prices` действительно не повторяется (получите это проверкой, а не впишите).

### starter
```python
import pandas as pd
orders = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
o = _pd.read_csv('orders_3m.csv')
o['price'] = o['amount'] / o['qty']
want = o[['drink', 'size', 'price']].drop_duplicates()
pr = need('prices', _pd.DataFrame)
assert list(pr.columns) == ['drink', 'size', 'price'], f'Столбцы prices: {list(pr.columns)}. Нужны drink, size, price — в этом порядке.'
assert len(pr) != len(o), f'В prices {len(pr)} строк — столько же, сколько заказов. Уберите повторы.'
assert len(pr) == len(want), f'В prices {len(pr)} строк, а разных пар «напиток + размер» — {len(want)}.'
m = pr.merge(want, on=['drink', 'size'], suffixes=('', '_w'))
assert len(m) == len(want) and (m['price'] - m['price_w']).abs().max() < 1e-9, 'Цены не совпадают с amount / qty.'
assert bool(need('ok')) is True, 'ok должен получиться True: проверьте, что пары drink + size не повторяются.'
import ast as _ast
_lit = [n for n in _ast.walk(_ast.parse(_code)) if isinstance(n, _ast.Assign) and isinstance(n.value, _ast.Constant)
        and any(isinstance(t, _ast.Name) and t.id == 'ok' for t in n.targets)]
assert not _lit, 'Получите ok проверкой (duplicated или is_unique), а не вписывайте True.'
```

### hint
Цена чашки — новый столбец: `orders["price"] = orders["amount"] / orders["qty"]`. Дальше — те же шаги, что для справочника кофеен. Ключ здесь **составной** — пара `drink` + `size`, поэтому и уникальность проверяют по паре: `duplicated(subset=["drink", "size"])`.

### hint
`orders[["drink", "size", "price"]].drop_duplicates()` — по строке на каждую разную тройку. Если у пары окажется две цены, пара повторится.

### hint
Проверка: `ok = not prices.duplicated(subset=["drink", "size"]).any()`.

### solution
```python
import pandas as pd
orders = pd.read_csv("orders_3m.csv")
orders["price"] = orders["amount"] / orders["qty"]
prices = orders[["drink", "size", "price"]].drop_duplicates()
ok = not prices.duplicated(subset=["drink", "size"]).any()
```

### explain
Из 2089 заказов получилось 33 строки: 11 напитков × 3 размера, и у каждой пары ровно одна цена — `ok` равен `True`. Проверку нельзя пропускать: если бы в середине осени подняли цену на раф, пара «Раф + M» встретилась бы дважды, с двумя ценами. Тогда `merge` заказов с таким прайсом удвоил бы заказы рафа, а справочнику понадобилась бы дата начала действия цены. Цена здесь дробная (`190.0`), потому что деление `/` в pandas всегда даёт `float`.

## task: overcount | Цена дублей | plus

Насколько повторно отправленные заказы завышают выручку кассы? Сохраните в `overcount` разницу между суммой `price × qty` по сырой выгрузке и по выгрузке без повторов `id`, округлённую до двух знаков.

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")

```

### check
```python
import pandas as _pd
p = _pd.read_csv('pos_december.csv', sep=';', decimal=',')
r = lambda t: (t['price'] * t['qty']).sum()
want = round(r(p) - r(p.drop_duplicates(subset=['id'])), 2)
assert close(need('overcount'), want), f'overcount = {need("overcount")}, а нужно {want}.'
```

### hint
Посчитайте выручку дважды: по `pos` и по `pos.drop_duplicates(subset=["id"])`.

### hint
`(pos["price"] * pos["qty"]).sum()` — для каждой таблицы; разница — `round(..., 2)`.

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
raw_rev = (pos["price"] * pos["qty"]).sum()
uniq = pos.drop_duplicates(subset=["id"])
overcount = round(raw_rev - (uniq["price"] * uniq["qty"]).sum(), 2)
```

### explain
Четыре повторных заказа завысили выручку на 1 220 ₽ — около 1 % недели. Мало для одной недели, но такая ошибка повторяется каждый день, и за год набегает заметная сумма в отчёте, которой не было на счёте.

## task: dedupe-fn | Функция дедупликации | plus

Напишите функцию `dedupe(df, key, by)`: оставляет по одной строке на каждое значение столбца `key` — ту, у которой значение столбца `by` наибольшее (самая свежая дата, самая большая сумма). Индекс результата — по порядку от 0. Исходная таблица меняться не должна.

### starter
```python
import pandas as pd

def dedupe(df, key, by):
    ...

t = pd.DataFrame({"id": ["A", "B", "A"], "d": ["2026-01-05", "2026-02-01", "2026-03-10"], "v": [1, 2, 3]})
dedupe(t, "id", "d")
```

### check
```python
import pandas as _pd
f = need('dedupe')
t = _pd.DataFrame({'id': ['A', 'B', 'A', 'C', 'B'], 'd': ['2026-01-05', '2026-02-01', '2026-03-10', '2026-01-01', '2025-12-31'], 'v': [1, 2, 3, 4, 5]})
before = t.copy()
r = f(t, 'id', 'd')
assert isinstance(r, _pd.DataFrame), 'dedupe должна возвращать DataFrame.'
assert t.equals(before), 'Исходная таблица изменилась — функция должна возвращать новую.'
assert sorted(r['id']) == ['A', 'B', 'C'], f'Ключи в результате: {sorted(r["id"])}.'
assert dict(zip(r['id'], r['v'])) == {'A': 3, 'B': 2, 'C': 4}, f'Оставлены не те строки: {dict(zip(r["id"], r["v"]))}. Нужна строка с наибольшим by.'
assert list(r.index) == list(range(len(r))), 'Индекс — по порядку от 0.'
r2 = f(_pd.DataFrame({'k': [1, 1, 2], 'amount': [500, 900, 100]}), 'k', 'amount')
assert dict(zip(r2['k'], r2['amount'])) == {1: 900, 2: 100}, 'Функция должна работать с любыми названиями столбцов.'
```

### hint
Внутри — та же цепочка, что в задаче про свежую анкету, только вместо названий столбцов — параметры `key` и `by`.

### hint
`return df.sort_values(by).drop_duplicates(subset=[key], keep="last").reset_index(drop=True)` — `sort_values` возвращает новую таблицу, исходная не меняется.

### solution
```python
import pandas as pd

def dedupe(df, key, by):
    return (df.sort_values(by)
              .drop_duplicates(subset=[key], keep="last")
              .reset_index(drop=True))

t = pd.DataFrame({"id": ["A", "B", "A"], "d": ["2026-01-05", "2026-02-01", "2026-03-10"], "v": [1, 2, 3]})
dedupe(t, "id", "d")
```

### explain
`sort_values` и `drop_duplicates` возвращают новые таблицы, поэтому исходная не меняется. Такую функцию можно применять к любой выгрузке — это первый кирпичик воспроизводимой очистки из урока «Очистка целиком: функция и проверки».

## task: shops-ref | Справочник кофеен | plus

Соберите из `delivery_flat.csv` справочник кофеен `shops` — по одной строке на `shop_id` со столбцами `shop_id`, `shop_address`, `city`, `manager`:

- город приведите к одному виду: без пробелов по краям, с заглавной буквы;
- если у кофейни сменился управляющий, оставьте самого свежего (по дате заказа).

В `n_changed` сохраните, у скольких кофеен **после нормализации города** осталось больше одной версии атрибутов.

### starter
```python
import pandas as pd
flat = pd.read_csv("delivery_flat.csv")
cols = ["shop_id", "shop_address", "city", "manager"]
shops = flat[cols].drop_duplicates()
```

### check
```python
import pandas as _pd
f = _pd.read_csv('delivery_flat.csv')
cols = ['shop_id', 'shop_address', 'city', 'manager']
f['city'] = f['city'].str.strip().str.capitalize()
want = f.sort_values('date').drop_duplicates('shop_id', keep='last')[cols].set_index('shop_id').sort_index()
v = f[cols].drop_duplicates()
want_changed = int(v['shop_id'].duplicated().groupby(v['shop_id']).any().sum())
s = need('shops', _pd.DataFrame)
assert set(cols) <= set(s.columns), f'В shops нужны столбцы {cols}, сейчас {list(s.columns)}.'
assert len(s.columns) == 4, f'В shops лишние столбцы: {[c for c in s.columns if c not in cols]}. Атрибуты заказа в справочник не идут.'
assert s['shop_id'].is_unique, f'shop_id повторяется: {sorted(s.loc[s["shop_id"].duplicated(), "shop_id"].unique())}. Нормализуйте город и оставьте самую свежую версию.'
g = s.set_index('shop_id').sort_index()[want.columns]
assert list(g.index) == list(want.index), f'Коды в shops: {list(g.index)}, а нужны {list(want.index)}.'
bad_city = g.index[g['city'] != want['city']].tolist()
assert not bad_city, f'Город не совпадает у {bad_city}: уберите пробелы по краям и сделайте первую букву заглавной.'
bad_mgr = g.index[g['manager'] != want['manager']].tolist()
assert not bad_mgr, f'Управляющий у {bad_mgr} не самый свежий. Отсортируйте по date перед drop_duplicates(keep="last").'
assert need('n_changed') == want_changed, f'n_changed = {need("n_changed")}. Посчитайте кофейни, у которых после нормализации города больше одной версии.'
```

### hint
Порядок важен: сначала нормализуйте город во всей выгрузке, потом смотрите версии. Иначе опечатка «Тюмень » выглядит как изменение.

### hint
Версии после нормализации: `v = flat[cols].drop_duplicates()`; кофейни с несколькими версиями — `v["shop_id"].value_counts()` больше 1.

### hint
Самая свежая версия: `flat.sort_values("date").drop_duplicates(subset=["shop_id"], keep="last")[cols]`. `n_changed = (v["shop_id"].value_counts() > 1).sum()`.

### solution
```python
import pandas as pd
flat = pd.read_csv("delivery_flat.csv")
cols = ["shop_id", "shop_address", "city", "manager"]
flat["city"] = flat["city"].str.strip().str.capitalize()
versions = flat[cols].drop_duplicates()
n_changed = (versions["shop_id"].value_counts() > 1).sum()
shops = (flat.sort_values("date")
             .drop_duplicates(subset=["shop_id"], keep="last")[cols]
             .reset_index(drop=True))
```

### explain
До нормализации у трёх кофеен было по две версии, после — только у KZN-2: там с 10 ноября новый управляющий. Это единственное настоящее изменение, остальное — грязь написания. Порядок шагов решает всё. Если искать «последнюю версию» до чистки города, у TMN-1 случайно останется «Тюмень » с пробелом — смотря какой заказ оказался последним. Если взять первую версию вместо последней, справочник назовёт управляющей KZN-2 Алину Сафину, которая там больше не работает. Готовый справочник проверяют так же, как в задаче про прайс: ключ уникален, строк столько, сколько кофеен.

## task: versions | Все версии анкет | star

Для проверки маркетинг просит показать все анкеты гостей, которые заполняли её больше одного раза. Уберите полные дубли, нормализуйте номер карты и сохраните в `versions` **все** строки с повторяющимся номером, отсортированные по номеру и дате анкеты. В `n_guests` — сколько таких гостей.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
d0 = _pd.read_csv('clients_raw.csv').drop_duplicates()
d0['client_id'] = d0['client_id'].str.strip().str.upper()
want = d0[d0.duplicated('client_id', keep=False)].sort_values(['client_id', 'signup_date'])
v = need('versions', _pd.DataFrame)
assert len(v) == len(want), f'В versions {len(v)} строк, а нужно {len(want)} — по две и больше на гостя, включая первую анкету.'
assert list(v['client_id']) == list(want['client_id']) and list(v['signup_date']) == list(want['signup_date']), 'Порядок строк не тот: сначала по номеру, внутри — по дате.'
assert need('n_guests') == want['client_id'].nunique(), f'n_guests = {need("n_guests")}.'
```

### hint
Все копии, включая первую, помечает `duplicated(subset=["client_id"], keep=False)`.

### hint
Сортировка по двум столбцам — списком: `sort_values(["client_id", "signup_date"])`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv").drop_duplicates()
df["client_id"] = df["client_id"].str.strip().str.upper()
versions = (df[df.duplicated(subset=["client_id"], keep=False)]
              .sort_values(["client_id", "signup_date"]))
n_guests = versions["client_id"].nunique()
```

### explain
Порядок шагов важен. Сначала удаляем полные копии строк, потом нормализуем номер карты: только после этого «c1023 » и «C1023» становятся одним гостем. `keep=False` помечает все строки повторяющегося номера, а не только вторую и следующие, поэтому маркетинг видит каждую версию анкеты. Получается 12 строк от 6 гостей. Сортировка по номеру и дате ставит версии одного гостя рядом в хронологическом порядке: сразу видно, что он поменял между анкетами.
