---
title: "Строки: чистим и ищем по тексту"
lead: "Большая часть грязи — в тексте: регистр, пробелы, приставки вроде «г.», синонимы и опечатки, телефоны в пяти форматах. Учимся приводить текст к одному виду методами .str, заменять по словарю и искать по словам — и немного регулярных выражений, без которых в чистке не обойтись."
files: [clients_raw.csv, reviews.csv, pos_december.csv, menu.csv]
recap:
  - "`.str` применяет строковый метод к каждому значению столбца: `s.str.strip().str.lower()`. Пропуски остаются пропусками."
  - "`str.replace(\"г.\", \"\")` — замена **части** строки; `replace({\"Екб\": \"Екатеринбург\"})` — замена **значения целиком** по словарю."
  - "`str.removeprefix(\"г.\")` — убрать начало строки, только если оно там есть."
  - "Поиск: `s.str.contains(\"холодн\", case=False, na=False)`. `|` внутри шаблона — «или»: `\"долг|очеред\"`."
  - "Регулярные выражения: `\\d` — цифра, `\\D` — не цифра, `+` — одна или больше. `str.replace(r\"\\D\", \"\", regex=True)` оставит одни цифры."
  - "`str.extract(r\"(\\d)\", expand=False)` — вытащить кусок строки по шаблону."
  - "После чистки сверяйте значения со справочником: `set(s.dropna()) - set(menu[\"drink\"])` — что не нашлось."
---

## Методы .str

Со строками в Python мы работали в главе 1: `strip()`, `lower()`, `replace()`. У столбца pandas есть те же методы — через `.str`. Они применяются к каждому значению сразу, без цикла:

```python
import pandas as pd
s = pd.Series([" Пермь", "пермь ", "ПЕРМЬ", None])
s.str.strip().str.lower()
```

Методы можно соединять в цепочку: каждый получает результат предыдущего. Пропуск проходит через цепочку без ошибок и остаётся пропуском.

| Метод | Что делает |
|---|---|
| `str.strip()` | убрать пробелы по краям |
| `str.lower()`, `str.upper()` | строчные / заглавные |
| `str.capitalize()` | первая буква заглавная, остальные строчные |
| `str.replace(a, b)` | заменить кусок строки |
| `str.removeprefix(a)` | убрать `a` в начале, если оно там есть |
| `str.len()` | длина строки |
| `str[0]`, `str[-10:]` | символ или срез, как у обычной строки |
| `str.split(" ")` | разбить на части |

::: sql
`TRIM`, `LOWER`, `UPPER`, `REPLACE`, `LENGTH`, `SUBSTRING` — те же операции в SQL.
:::

{{practice: city-lower}}

## Чистим город

Вспомним варианты из урока «Первый осмотр: что не так с данными»: «Пермь», «пермь», « Пермь», «г. Пермь», «г.Пермь», а ещё «Екб» и «ЕКБ». План:

1. убрать пробелы по краям и перевести в строчные — исчезнут различия в регистре;
2. убрать приставку «г.» и снова пробелы — она бывает с пробелом и без;
3. заменить сокращения по словарю;
4. вернуть заглавную первую букву.

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
city = (df["city"]
        .str.strip()
        .str.lower()
        .str.removeprefix("г.")
        .str.strip()
        .replace({"екб": "екатеринбург"})
        .str.capitalize())
city.value_counts(dropna=False)
```

Из нескольких десятков вариантов осталось шесть городов и пропуски. Каждый шаг цепочки простой; вместе они справляются со всей грязью.

::: figure city-chain
Пять настоящих написаний из анкет проходят цепочку методов. Зелёным — что изменил шаг; внизу — сколько разных значений во всём столбце `city` после шага.
:::

::: tip
Длинную цепочку удобно писать по одному методу на строке. Чтобы Python понял, что выражение продолжается, оберните его в круглые скобки.
:::

{{practice: city-clean}}

## replace и str.replace — не одно и то же

Это частая ловушка. `str.replace("a", "b")` заменяет **кусок** внутри каждой строки. `replace({"a": "b"})` (без `.str`) заменяет **значение целиком** — только если всё значение равно ключу словаря.

::: predict
```python static
import pandas as pd
s = pd.Series(["Екб", "Екб-Сити"])
print(s.replace({"Екб": "Екатеринбург"}).tolist())
```

- `['Екатеринбург', 'Екатеринбург-Сити']`
- [x] `['Екатеринбург', 'Екб-Сити']`
- `['Екб', 'Екб-Сити']`

Почему: `replace` по словарю меняет только значения, которые **целиком** равны «Екб». Чтобы заменить кусок внутри строки, нужен `str.replace`.
:::

Для синонимов и сокращений обычно нужен именно словарь: «Екб» → «Екатеринбург», но не трогать «Екб» внутри других слов.

::: figure replace-vs-str
`replace` меняет клетку, только если она целиком равна ключу; `str.replace` меняет кусок внутри любой строки. Зелёным — изменённые значения.
:::

Похоже работает и `map(словарь)` из главы 2, но с одним отличием: значения, которых нет в словаре, `map` превратит в `NaN`, а `replace` оставит как есть. Для чистки безопаснее `replace`.

::: quiz
Чем `s.replace("г.", "")` отличается от `s.str.replace("г.", "", regex=False)` для Series городов?

- [x] Первое заменяет только клетки, равные «г.» целиком, второе — кусок «г.» внутри каждой строки
  > `Series.replace` подменяет значения целиком (как словарь). Для правки текста внутри строки нужен `.str.replace`.
- [ ] Ничем, это синонимы
  > Результаты разные: «г. Пермь» первое оставит как есть.
- [ ] Первое работает быстрее, а результат одинаковый
  > Дело не в скорости: первое просто не тронет «г. Пермь».
- [ ] Второе изменит исходную Series на месте
  > Оба метода возвращают новую Series; без присваивания изменения пропадут.
:::

## Сверка со справочником

Как убедиться, что чистка закончена? Сравнить результат со справочником — списком правильных значений. В кассовой выгрузке названия напитков набраны вручную. Справочник — меню:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
menu = pd.read_csv("menu.csv")
drink = pos["drink"].str.strip().str.capitalize()
set(drink) - set(menu["drink"])
```

Разность множеств (урок «Кортежи и множества» главы 1) показывает, каких названий нет в меню. После регистра и пробелов остались опечатки — их исправляет словарь:

```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
menu = pd.read_csv("menu.csv")
typos = {"Каппучино": "Капучино", "Флет уайт": "Флэт уайт", "Амерекано": "Американо"}
drink = pos["drink"].str.strip().str.capitalize().replace(typos)
print(set(drink) - set(menu["drink"]))
drink.value_counts()
```

Пустое множество — значит, все названия есть в меню.

{{practice: drinks, shop-code}}

## Поиск по тексту: contains

В отзывах гости пишут, что их порадовало или расстроило. `str.contains` ищет кусок текста в каждой строке:

```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
cold = reviews["text"].str.contains("холодн", case=False, na=False)
print("отзывов про холодный напиток:", cold.sum())
reviews.loc[cold, ["shop_id", "rating", "text"]].head()
```

- `case=False` — не различать регистр: найдутся и «Холодный», и «холодный»;
- `na=False` — что ответить для пустого текста; без этого пропуск дал бы `NaN` в маске.

Ищем по основе слова — «холодн», а не «холодный»: так найдутся и «холодный», и «холодная», и «холодно».

::: sql
`WHERE LOWER(text) LIKE '%холодн%'`.
:::

Искать сразу несколько слов («холодн» **или** «остыл») тоже можно одним `contains` — для этого нужен символ `|` из регулярных выражений, о них следующий раздел.

## Чуть-чуть регулярных выражений

**Регулярное выражение** — шаблон для поиска в тексте. Полная тема большая, но для чистки хватает нескольких символов:

| Шаблон | Что значит | Пример |
|---|---|---|
| `\d` | любая цифра | `\d\d` — две цифры подряд |
| `\D` | любой символ, кроме цифры | пробел, скобка, «+» |
| `+` | предыдущее — один раз или больше | `\d+` — число из любого числа цифр |
| `a\|b` | `a` или `b` | `долг\|очеред` |
| `( )` | часть, которую нужно вытащить | `(\d)` |

Шаблоны записывают в строках с буквой `r` перед кавычкой: `r"\d"`. Так Python не трогает обратную косую черту.

### Телефон: оставить только цифры

Телефоны записаны в пяти форматах: «+7 912 345-67-89», «8 (912) 345-67-89», «89123456789»… Общее у них одно — цифры. Удалим всё, что не цифра, и возьмём последние 10 — номер без кода страны:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
digits = df["phone"].str.replace(r"\D", "", regex=True)
phone10 = digits.str[-10:]
pd.DataFrame({"было": df["phone"], "стало": phone10}).head(8)
```

`regex=True` говорит, что первый аргумент — шаблон, а не обычный текст.

::: predict
```python static
import pandas as pd
s = pd.Series(["+7 (912) 00-11"])
print(s.str.replace(r"\D", "", regex=True)[0])
```

- `+7912)0011`
- [x] `79120011`
- `912 00 11`

Почему: `\D` — любой не-цифровой символ: плюс, пробелы, скобки, дефис. Все они заменены на пустую строку, остались только цифры.
:::

### Несколько слов: «или»

Жалобы на ожидание пишут по-разному: «долго», «очередь», «ждали». Шаблон с `|` найдёт любое из слов:

```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
wait = reviews["text"].str.contains("долг|очеред|ждал", case=False, na=False)
print(wait.sum())
reviews.loc[wait, "text"].head()
```

`|` внутри шаблона — «или»: строка подходит, если в ней есть хотя бы одно из слов. Пробелов вокруг `|` не ставят: `"долг | очеред"` искал бы «долг » с пробелом на конце.

{{practice: cold, themes}}

### Вытащить кусок: extract

`str.extract` возвращает часть строки, которая попала в круглые скобки шаблона. Оценка в отзывах — первая цифра в `rating` («5», «4/5», «3 из 5»):

```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
reviews["stars"] = reviews["rating"].str.extract(r"(\d)", expand=False).astype("Int64")
reviews[["rating", "stars"]].drop_duplicates().head(8)
```

`expand=False` — вернуть Series, а не таблицу. В уроке «Типы: из текста в числа и даты» мы брали первый символ `str[0]`; `extract` надёжнее: найдёт цифру, даже если перед ней пробел или звёздочка.

{{practice: p-phone, phone10, shared-phone}}

## Разберём вместе: три телефона — один формат

В анкетах телефон записан как угодно. Возьмём три реальных значения и проведём их через два шага.

| исходное | шаг 1: убрать всё, кроме цифр | шаг 2: последние 10 |
|---|---|---|
| `+7 (991) 6085441` | `79916085441` | `9916085441` |
| `89632143044` | `89632143044` | `9632143044` |
| `+7 973 263-65-59` | `79732636559` | `9732636559` |

1. Шаг 1 — `str.replace(r"\D", "", regex=True)`: `\D` — «любой символ, кроме цифры». Скобки, пробелы, дефисы и плюс исчезают.
2. Шаг 2 — `str[-10:]`: код страны бывает «7» или «8», а последние 10 цифр — сам номер у всех одинаково.
3. Проверка — **до** шага 2: цифр должно быть 10, или 11 с кодом 7 или 8 впереди. Проверять длину после `str[-10:]` бесполезно: срез из любой длинной строки даёт ровно 10 цифр, и номер с добавочным «доб. 12» или лишней цифрой превратится в правдоподобный, но чужой номер. Всё, что не подошло, оставляют пропуском и смотрят глазами. В наших анкетах таких нет: 269 номеров по 11 цифр и 21 по 10.

::: figure phone-regex
Два телефона из анкет посимвольно: `\D` находит всё, что не цифра, и `str.replace` убирает это; `str[-10:]` отрезает код страны, будь то 7 или 8.
:::

```python
import pandas as pd
phones = pd.Series(["+7 (991) 6085441", "89632143044", "+7 973 263-65-59", "+7 912 345-67-89 доб. 12", None])
digits = phones.str.replace(r"\D", "", regex=True)
ok = digits.str.fullmatch(r"[78]?\d{10}")     # 10 цифр или 11 с кодом 7/8
p10 = digits.where(ok).str[-10:]
print(digits.tolist())
print(p10.tolist())
```

Что получилось: три записи одного вида данных стали сравнимыми, а номер с добавочным (13 цифр) стал пропуском, а не номером `2345678912`, который дал бы голый `str[-10:]`. `str.fullmatch` проверяет, что шаблону соответствует **вся** строка: `[78]?` — необязательный код страны, `\d{10}` — ровно десять цифр. Теперь по телефону можно искать дубли гостей и сверять анкеты с CRM. Пропуск остался пропуском — методы `.str` его не трогают.

С городами то же самое, только шагов больше: 29 написаний → после `strip().lower()` — 13 → после снятия «г.» и замены «екб» — 6 настоящих городов.

::: warn Типичные ошибки
- **`replace` вместо `str.replace`.** `df["x"].replace("г.", "")` меняет только ячейки, равные «г.» целиком; заменить часть строки — `str.replace`.
- **Точка в регулярном выражении.** В `regex=True` точка — «любой символ»; буквальная точка — `\.` или `regex=False`.
- **`contains` с пропусками.** Без `na=False` маска будет с `NaN`, и фильтр упадёт.
- **`capitalize()` для составных названий.** «флэт уайт» → «Флэт уайт» — правильно, но «санкт-петербург» → «Санкт-петербург»; сверяйте со справочником.
:::

## Практика

## task: city-lower | Регистр и пробелы | warmup

Сохраните в `n_after` число разных значений города после `strip()` и `lower()` (без пропусков). Сравните с тем, что было до.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
print("до:", df["city"].nunique())

```

### check
```python
import pandas as _pd
c = _pd.read_csv('clients_raw.csv')['city']
want = c.str.strip().str.lower().nunique()
assert need('n_after') == want, f'n_after = {need("n_after")}, а нужно {want}.'
```

### hint
Методы `.str` применяются цепочкой: каждый получает результат предыдущего.

### hint
`df["city"].str.strip().str.lower().nunique()`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
print("до:", df["city"].nunique())
n_after = df["city"].str.strip().str.lower().nunique()
```

## task: cold | Холодный кофе | warmup

Сохраните в `n_cold` число отзывов, где упоминается холодный или остывший напиток: ищите «холодн» **или** «остыл», без учёта регистра.

### starter
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")

```

### check
```python
import pandas as _pd
t = _pd.read_csv('reviews.csv')['text']
want = t.str.contains('холодн|остыл', case=False, na=False).sum()
only = t.str.contains('холодн', case=False, na=False).sum()
got = need('n_cold')
assert not (got == only and only != want), f'n_cold = {got} — это только «холодн». Добавьте «или остыл»: шаблон "холодн|остыл".'
assert got == want, f'n_cold = {got}, а нужно {want}. Регистр учли (case=False)?'
```

### hint
Вертикальная черта `|` в шаблоне значит «или»; `case=False` — без учёта регистра.

### hint
`reviews["text"].str.contains("холодн|остыл", case=False, na=False).sum()`.

### solution
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
n_cold = reviews["text"].str.contains("холодн|остыл", case=False, na=False).sum()
```

## task: p-phone | Телефон цифрами | warmup

Соберите программу, которая выводит первый телефон из анкет в виде 10 цифр.

### parsons
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
digits = df["phone"].str.replace(r"\D", "", regex=True)
phone10 = digits.str[-10:]
print(phone10[0])
```

### check
```python
import pandas as _pd
want = _pd.read_csv('clients_raw.csv')['phone'].str.replace(r'\D', '', regex=True).str[-10:][0]
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Сначала убрать не-цифры, потом взять последние 10 символов.

### hint
Сначала цифры (`digits`), потом последние 10 (`phone10`), и только потом печатаем первый элемент: `phone10[0]`.

## task: city-clean | Город начисто | base

Приведите город к каноническому виду: «Пермь», «Казань», «Тюмень», «Уфа», «Екатеринбург», «Москва» (пропуски оставьте пропусками). Сохраните результат в столбец `city` таблицы `df`.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

df["city"].value_counts(dropna=False)
```

### check
```python
import pandas as _pd
c0 = _pd.read_csv('clients_raw.csv')['city']
want = c0.str.strip().str.lower().str.removeprefix('г.').str.strip().replace({'екб': 'екатеринбург'}).str.capitalize()
got = need('df', _pd.DataFrame)['city']
extra = sorted(set(got.dropna()) - {'Пермь', 'Казань', 'Тюмень', 'Уфа', 'Екатеринбург', 'Москва'})
assert not extra, f'Остались неканонические значения: {extra}.'
assert got.isna().sum() == c0.isna().sum(), 'Число пропусков изменилось — пустые города заполнять не нужно.'
assert (got.fillna('-') == want.fillna('-')).all(), 'Значения не совпадают с ожидаемыми.'
```

### hint
Цепочка: `str.strip()` → `str.lower()` → `str.removeprefix("г.")` → `str.strip()`.

### hint
После этого — словарь для сокращения `replace({"екб": "екатеринбург"})` и `str.capitalize()`. Проверка: `df["city"].value_counts(dropna=False)`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
df["city"] = (df["city"]
              .str.strip()
              .str.lower()
              .str.removeprefix("г.")
              .str.strip()
              .replace({"екб": "екатеринбург"})
              .str.capitalize())
df["city"].value_counts(dropna=False)
```

### explain
Из 29 написаний осталось 6 городов. Самые частые проблемы — «г.» в начале (23 анкеты) и сокращение «екб» (8). Без чистки отчёт «гости по городам» показал бы Пермь четырьмя строками и занизил бы её почти в 1.3 раза.

## task: phone10 | Телефон в одном формате | base

Сохраните в столбец `phone10` телефон из 10 цифр (без кода страны). Пустые телефоны оставьте пропусками. В `n_bad` — число непустых `phone10`, у которых длина не 10 (должно быть 0).

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
p0 = _pd.read_csv('clients_raw.csv')['phone']
want = p0.str.replace(r'\D', '', regex=True).str[-10:]
d = need('df', _pd.DataFrame)
assert 'phone10' in d.columns, 'Нет столбца phone10.'
got = d['phone10']
assert got.isna().sum() == p0.isna().sum(), 'Число пропусков изменилось.'
assert (got.fillna('-') == want.fillna('-')).all(), f'phone10 не совпадает с ожидаемым. Например, {p0[got.fillna("-") != want.fillna("-")].iloc[0]!r} → {got[got.fillna("-") != want.fillna("-")].iloc[0]!r}.'
assert need('n_bad') == (want.dropna().str.len() != 10).sum(), f'n_bad = {need("n_bad")}.'
```

### hint
`df["phone"].str.replace(r"\D", "", regex=True).str[-10:]`.

### hint
Длина — `str.len()`. Пропуски перед подсчётом уберите: `df["phone10"].dropna()`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
df["phone10"] = df["phone"].str.replace(r"\D", "", regex=True).str[-10:]
n_bad = (df["phone10"].dropna().str.len() != 10).sum()
```

### explain
Все непустые телефоны после двух шагов — ровно по 10 цифр. Это хорошая проверка самой чистки: если бы где-то осталось 9 или 11 цифр, значит, в анкете опечатка или чужие данные.

## task: drinks | Напитки по меню | base

Приведите названия напитков в кассовой выгрузке к названиям из меню: пробелы, регистр и три опечатки («Каппучино», «Флет уайт», «Амерекано»). Сохраните результат в `pos["drink"]`, а в `unknown` — множество названий, которых нет в меню (должно получиться пустое).

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
menu = pd.read_csv("menu.csv")

```

### check
```python
import pandas as _pd
p0 = _pd.read_csv('pos_december.csv', sep=';')
m = set(_pd.read_csv('menu.csv')['drink'])
p = need('pos', _pd.DataFrame)
left = set(p['drink']) - m
assert not left, f'Не нашлись в меню: {sorted(left)}.'
assert need('unknown') == set(), f'unknown = {need("unknown")} — должно быть пустое множество.'
want = p0['drink'].str.strip().str.capitalize().replace({'Каппучино': 'Капучино', 'Флет уайт': 'Флэт уайт', 'Амерекано': 'Американо'})
assert (p['drink'] == want).all(), 'Названия не совпадают с ожидаемыми.'
```

### hint
`str.strip().str.capitalize()`, затем `replace` со словарём опечаток.

### hint
`unknown = set(pos["drink"]) - set(menu["drink"])`.

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
menu = pd.read_csv("menu.csv")
typos = {"Каппучино": "Капучино", "Флет уайт": "Флэт уайт", "Амерекано": "Американо"}
pos["drink"] = pos["drink"].str.strip().str.capitalize().replace(typos)
unknown = set(pos["drink"]) - set(menu["drink"])
```

### explain
Пробелы в конце («Латте »), регистр («латте») и три опечатки давали 34 разных названия для 11 напитков меню. Проверка разностью множеств — универсальный приём: всё, что осталось в `unknown`, — ещё не исправлено.

## task: shop-code | Код кофейни | base

В кассовой выгрузке код кофейни записан как «PRM-1», «prm-1» или «PRM 1». Приведите `shop` к виду «PRM-1» и сохраните в `n_shops` число разных кофеен после чистки.

### starter
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('pos_december.csv', sep=';')['shop']
want = s0.str.strip().str.upper().str.replace(' ', '-')
p = need('pos', _pd.DataFrame)
assert (p['shop'] == want).all(), f'Остались значения: {sorted(set(p["shop"]) - set(want))}.'
assert need('n_shops') == want.nunique(), f'n_shops = {need("n_shops")}, а нужно {want.nunique()}.'
```

### hint
Заглавные буквы — `str.upper()`; пробел внутри заменить на дефис — `str.replace(" ", "-")`.

### hint
Пробелы по краям уберите до замены пробела на дефис, иначе « PRM-1» превратится в «-PRM-1».

### solution
```python
import pandas as pd
pos = pd.read_csv("pos_december.csv", sep=";", decimal=",")
pos["shop"] = pos["shop"].str.strip().str.upper().str.replace(" ", "-")
n_shops = pos["shop"].nunique()
```

### explain
До чистки в столбце 19 разных написаний, после — 7 кофеен. Каждый шаг цепочки снимает одну причину расхождений: `strip` — пробелы по краям, `upper` — регистр («ekb-1»), `replace(" ", "-")` — пробел вместо дефиса («KZN 2»). Без чистки группировка по `shop` разбила бы одну кофейню на несколько строк, и выручка «PRM-1» оказалась бы заниженной.

## task: themes | Темы жалоб | plus

Посчитайте, сколько отзывов относится к каждой теме, и сохраните словарь `themes`:

- `"холодно"` — «холодн» или «остыл»;
- `"долго"` — «долг», «очеред» или «ждал»;
- `"дорого"` — «дорог».

Регистр не важен. Один отзыв может попасть в несколько тем.

### starter
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")

```

### check
```python
import pandas as _pd
t = _pd.read_csv('reviews.csv')['text']
c = lambda p: int(t.str.contains(p, case=False, na=False).sum())
want = {'холодно': c('холодн|остыл'), 'долго': c('долг|очеред|ждал'), 'дорого': c('дорог')}
got = {k: int(v) for k, v in dict(need('themes')).items()}
assert set(got) == set(want), f'Ключи: {sorted(got)}, а нужны {sorted(want)}.'
for k in want:
    assert got[k] == want[k], f'Тема «{k}»: {got[k]}, а нужно {want[k]}.'
```

### hint
Шаблоны тем удобно держать в словаре: `{"холодно": "холодн|остыл", ...}`, а потом пройти по нему циклом.

### hint
Внутри цикла: `themes[name] = int(reviews["text"].str.contains(pattern, case=False, na=False).sum())`. Без `int()` число напечатается как `np.int64(14)` — это то же число 14, просто тип из библиотеки numpy, на которой построен pandas. `int()` делает из него обычное число Python.

### solution
```python
import pandas as pd
reviews = pd.read_csv("reviews.csv")
patterns = {"холодно": "холодн|остыл", "долго": "долг|очеред|ждал", "дорого": "дорог"}
themes = {}
for theme, pattern in patterns.items():
    themes[theme] = int(reviews["text"].str.contains(pattern, case=False, na=False).sum())
```

### explain
Это простейший анализ текстов — поиск по ключевым словам. Он грубый: «недорого» попадёт в тему «дорого». Методы точнее будут в главе про тексты, но для первого взгляда на отзывы этого часто хватает.

На 150 отзывов — 14 про холодный напиток, 14 про ожидание и 13 про цену: три темы почти поровну. Простые шаблоны ловят большинство жалоб, но не все: «чуть тёплый» или «пришлось стоять» они пропустят. Для отчёта это честная нижняя оценка.

## task: shared-phone | Один телефон — разные карты | star

Некоторые гости завели новую карту, не закрыв старую. Найдите телефоны (в виде 10 цифр), на которые записано **больше одной** разной карты. Номер карты предварительно нормализуйте (пробелы, регистр). Сохраните в `shared` отсортированный список таких телефонов.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('clients_raw.csv')
d['client_id'] = d['client_id'].str.strip().str.upper()
d['p'] = d['phone'].str.replace(r'\D', '', regex=True).str[-10:]
n = d.dropna(subset=['p']).groupby('p')['client_id'].nunique()
want = sorted(n[n > 1].index)
got = need('shared')
assert isinstance(got, list), 'shared должен быть списком.'
assert got == want, f'shared = {got[:5]}…, а нужно {len(want)} телефонов. Дубли анкет одного гостя (одна карта) не считаются — нужны разные карты.'
```

### hint
Нормализуйте и номер карты, и телефон. Затем сгруппируйте по телефону и посчитайте **разные** карты: `nunique()`.

### hint
Повторные анкеты с той же картой дадут один телефон дважды, но `nunique()` по карте для них будет 1 — они в ответ не попадут.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
df["client_id"] = df["client_id"].str.strip().str.upper()
df["phone10"] = df["phone"].str.replace(r"\D", "", regex=True).str[-10:]
cards = df.groupby("phone10")["client_id"].nunique()
shared = sorted(cards[cards > 1].index)
```

### explain
Без нормализации телефоны «+7 912…» и «8 (912)…» не совпали бы, и ни одного совпадения не нашлось бы. Объединять такие карты автоматически не стоит: это решение бизнеса (вдруг телефон семейный). Задача аналитика — найти и показать.
