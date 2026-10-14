---
title: "Категоризация: CASE WHEN в pandas"
lead: "Отчёты часто строят не по точным значениям, а по группам: возрастные группы, «маленький — средний — крупный» заказ, редкие и частые гости. Учимся раскладывать числа и текст по категориям — функцией, интервалами и словарём — и собирать редкие значения в «прочее»."
files: [orders_3m.csv, clients_raw.csv]
recap:
  - "Своя логика: функция `def size_group(x): …` и `s.apply(size_group)` — как `CASE WHEN` в SQL."
  - "Интервалы: `pd.cut(s, bins=[0, 300, 600, 10_000], labels=[…], right=False)`. `right=False` — интервал `[от, до)`, левая граница включена."
  - "Равные по размеру группы: `pd.qcut(s, 4, labels=[…])` — квартили, как `NTILE(4)`."
  - "Текст → группа: словарь и `replace` (или `map`, если все значения есть в словаре)."
  - "Редкие значения в «прочее»: `s.where(s.isin(частые), \"прочее\")`."
  - "Правило по нескольким столбцам: функция от строки и `df.apply(f, axis=1)`."
---

## Зачем категории

«Средний чек гостей 25–34 лет», «доля крупных заказов», «выручка по времени суток» — в таких отчётах группируют не по точному значению, а по **категории**. Возраст 27 и 31 попадают в одну группу, сумма 640 и 980 — в «крупный заказ».

В SQL для этого пишут `CASE WHEN … THEN … END`. В pandas способов несколько — выбираем по задаче.

## Функция и apply

Самый гибкий способ — написать функцию для одного значения и применить её ко всему столбцу методом `apply`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

def size_group(amount):
    if amount < 300:
        return "малый"
    elif amount < 600:
        return "средний"
    else:
        return "крупный"

df["check"] = df["amount"].apply(size_group)
df["check"].value_counts()
```

`apply` вызывает функцию для каждого значения и собирает ответы в новый столбец. Внутри функции — обычный Python из главы 1: `if`, `elif`, `else`.

В задачах урока счётчики `value_counts()` часто нужно сохранить словарём «категория → число»: это `dict(df["check"].value_counts())` или `df["check"].value_counts().to_dict()` — результат одинаковый.

::: sql
```sql
CASE WHEN amount < 300 THEN 'малый'
     WHEN amount < 600 THEN 'средний'
     ELSE 'крупный' END
```
:::

Если в столбце бывают пропуски, функция должна их предусмотреть — иначе сравнение `NaN < 300` даст `False`, и пропуск тихо уйдёт в последнюю ветку:

::: predict
```python static
import pandas as pd

def size_group(amount):
    if amount < 300:
        return "малый"
    return "крупный"

print(pd.Series([150, None]).apply(size_group).tolist())
```

- `['малый', nan]`
- [x] `['малый', 'крупный']`
- `Ошибка TypeError`

Почему: любое сравнение с `NaN` даёт `False`, поэтому пропуск прошёл мимо первого условия и попал в «крупный». Проверяйте пропуск первой строкой функции: `if pd.isna(amount): return None`.
:::

{{practice: check-size}}

## Интервалы: pd.cut

Когда категории — это просто интервалы чисел, удобнее `pd.cut`. Ему передают границы (`bins`) и названия (`labels`) — названий на одно меньше, чем границ:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
hour = df["datetime"].dt.hour
df["part"] = pd.cut(hour, bins=[0, 12, 17, 24], labels=["утро", "день", "вечер"], right=False)
df.groupby("part", observed=True)["amount"].agg(["count", "sum"])   # observed=True — только встречающиеся группы
```

`right=False` значит, что интервал включает левую границу и не включает правую: `[0, 12)`, `[12, 17)`, `[17, 24)`. Заказ в 12:00 — уже «день».

::: tip Аналогия
Табличка в музее: «дети до 7 лет — бесплатно, с 7 лет — детский билет». Ребёнку, которому ровно 7, по словам «с 7 лет» нужен детский билет: граница открывает новую группу — это `right=False`. Если бы было написано «до 7 лет включительно — бесплатно», семилетний прошёл бы бесплатно — это `right=True`. Разница в том, что в музее спорный случай решит кассир, а `pd.cut` молча применит то, что задано параметром.
:::

`observed=True` в `groupby` — просьба показывать только встречающиеся категории. У столбцов, созданных через `cut`, особый тип `category`, и без этого параметра pandas покажет и пустые группы.

::: predict
```python static
import pandas as pd
s = pd.Series([10])
print(pd.cut(s, bins=[0, 10, 20], labels=["до 10", "больше 10"])[0])
```

- [x] `до 10`
- `больше 10`
- `nan`

Почему: по умолчанию интервалы у `cut` закрыты справа: `(0, 10]` и `(10, 20]`. Значение 10 — правая граница первого интервала. Именно поэтому для «от и до» удобнее `right=False`.
:::

Значения за пределами всех интервалов станут `NaN`. Чтобы последний интервал был открытым вверх, правой границей ставят бесконечность — `float("inf")`.

### Разберём вместе: куда попадает граница

Пять гостей сделали 3, 4, 6, 7 и 12 заказов. Делим на «редких», «обычных» и «частых» с границами `[1, 4, 7, ∞]` двумя способами.

**По умолчанию (`right=True`)** — правая граница входит в интервал: (1, 4], (4, 7], (7, ∞).

| заказов | интервал | группа |
|---|---|---|
| 3 | (1, 4] | редкие |
| 4 | (1, 4] | редкие |
| 6 | (4, 7] | обычные |
| 7 | (4, 7] | обычные |
| 12 | (7, ∞) | частые |

**С `right=False`** — левая граница входит: [1, 4), [4, 7), [7, ∞).

| заказов | интервал | группа |
|---|---|---|
| 3 | [1, 4) | редкие |
| 4 | [4, 7) | обычные |
| 6 | [4, 7) | обычные |
| 7 | [7, ∞) | частые |
| 12 | [7, ∞) | частые |

Гости с 4 и 7 заказами «переехали» в соседние группы. По словам «1–3 — редкие, 4–6 — обычные, 7 и больше — частые» правильный второй вариант: число на границе начинает новую группу.

::: figure cut-right
Те же пять гостей на числовой оси. Отличаются только значения на границах — 4 и 7: при `right=True` граница закрывает группу слева, при `right=False` открывает группу справа.
:::

```python
import pandas as pd
n = pd.Series([3, 4, 6, 7, 12])
bins = [1, 4, 7, float("inf")]
labels = ["редкие", "обычные", "частые"]
print(pd.cut(n, bins=bins, labels=labels).tolist())
print(pd.cut(n, bins=bins, labels=labels, right=False).tolist())
```

Что получилось: в целых числах (заказы, часы, возраст) граница почти всегда совпадает с реальными значениями, и выбор `right` меняет ответ. Перед `cut` проговорите границы словами и проверьте их на значениях-границах.

::: warn Типичные ошибки
- **`right` по умолчанию.** `pd.cut` включает правую границу; для «от 17 часов — вечер» нужен `right=False`.
- **Значения за пределами границ.** Число меньше первой или больше последней границы станет `NaN`; последней границей удобно ставить `float("inf")`.
:::

{{practice: parts, p-cut, age-groups}}

## Равные группы: pd.qcut

Иногда границы заранее неизвестны, а нужно разделить гостей на четыре **равные по численности** группы: 25 % самых активных, следующие 25 % и так далее. Это квартили, и для них есть `pd.qcut`:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
spend = df.groupby("client_id")["amount"].sum()
q = pd.qcut(spend, 4, labels=["Q1", "Q2", "Q3", "Q4"])
pd.DataFrame({"гостей": q.value_counts(), "выручка": spend.groupby(q, observed=True).sum()})
```

Гостей в группах поровну, а выручка — нет: верхняя четверть приносит заметно больше.

::: tip Аналогия
Учитель физкультуры делит класс на четыре команды. Можно по росту отрезками — до 140 см, 140–150, 150–160, выше — и в одной команде окажется двенадцать человек, а в другой двое: это `cut`. А можно выстроить всех по росту и отсчитать по семь — команды равные, но границы роста у них неровные: это `qcut`. Если у многих учеников одинаковый рост, поровну не разделить — `qcut` в таком случае жалуется на повторяющиеся границы.
:::

::: figure cut-qcut
Траты 260 гостей за три месяца. `cut(spend, 4)` режет ось на четыре равных отрезка — гостей в группах от 9 до 132; `qcut(spend, 4)` даёт по 65 гостей, а границы ставит по квартилям.
:::

::: sql
`NTILE(4) OVER (ORDER BY spend)` — то же разбиение на четверти.
:::

::: quiz
Чем `pd.qcut(x, 4)` отличается от `pd.cut(x, 4)`?

- [x] `qcut` делит на группы с примерно равным **числом** наблюдений, `cut` — на интервалы равной **ширины**
  > Квартили (`qcut`) удобны для сегментов «верхние 25 % гостей». Равные интервалы (`cut`) при перекосе данных дают почти пустые группы.
- [ ] Ничем, `q` — просто сокращение
  > Результаты разные: при перекошенных данных `cut` положит почти всех в одну группу.
- [ ] `qcut` работает только с целыми числами
  > Работает с любыми числами.
- [ ] `cut` нельзя использовать с подписями групп
  > У обеих функций есть `labels=`.
:::

::: warn Типичная ошибка
**`qcut` на значениях с повторами.** Если много одинаковых значений, равных групп не получится — `qcut` выдаст ошибку о дублирующихся границах (`Bin edges must be unique`). Выход — меньше групп или `duplicates="drop"` (тогда групп станет меньше, чем просили).
:::

{{practice: quartiles, freq}}

## Текст → группа: словарь

Для текстовых значений категория задаётся словарём. В анкетах источник записан по-разному: «соцсети», «соц. сети», «Соцсети». Сначала нормализуем регистр и пробелы, потом сводим синонимы словарём:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
synonyms = {
    "соц. сети": "соцсети",
    "от друзей": "друзья",
    "проходил мимо": "мимо",
    "2гис": "карты",
    "яндекс карты": "карты",
}
src = df["source"].str.strip().str.lower().replace(synonyms)
src.value_counts(dropna=False)
```

Тот же приём работает для укрупнения: «соцсети», «карты», «реклама» → «онлайн»; «друзья», «мимо» → «офлайн». Словарь — это и есть правило категоризации, записанное явно. Его легко показать коллегам и поправить.

Словарь можно применить двумя методами. `replace(словарь)` меняет только то, что нашлось в словаре, остальное оставляет как было. `map(словарь)` превращает в `NaN` всё, чего в словаре нет.

::: warn Типичная ошибка
**`map` без «прочего».** Значения, которых нет в словаре, после `map` станут `NaN` и смешаются с настоящими пропусками. Их нужно заметить и обработать: `s.map(groups).fillna("другое")`.
:::

::: quiz
`s = pd.Series(["соцсети", "мимо", "реклама"])`, `groups = {"соцсети": "онлайн", "мимо": "офлайн"}`. Что даст `s.map(groups).tolist()`?

- [x] `['онлайн', 'офлайн', nan]`
  > «Реклама» нет в словаре, и `map` превратил её в пропуск. Его легко принять за настоящий пустой источник — поэтому после `map` проверяют, сколько стало `NaN`.
- [ ] `['онлайн', 'офлайн', 'реклама']`
  > Так сработал бы `replace(groups)`: он оставляет без изменений то, чего нет в словаре.
- [ ] Ошибка `KeyError`: «реклама» нет в словаре
  > Обычный словарь Python так бы и упал (`groups["реклама"]`), а `map` молча ставит `NaN`.
- [ ] `['онлайн', 'офлайн', 'другое']`
  > «Другое» появится, только если явно добавить `.fillna("другое")`.
:::

{{practice: online}}

## Редкие значения — в «прочее»

После словаря остались единичные ответы: «коллега», «бариста посоветовал». В отчёте десяток строк по одному гостю только мешает. Их собирают в «прочее» методом `where`: он оставляет значение там, где условие верно, а в остальных местах подставляет замену:

```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
synonyms = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}
src = df["source"].str.strip().str.lower().replace(synonyms)
counts = src.value_counts()
frequent = counts[counts >= 10].index
src = src.where(src.isin(frequent) | src.isna(), "прочее")
src.value_counts(dropna=False)
```

`| src.isna()` в условии нужен, чтобы пропуски остались пропусками, а не превратились в «прочее».

::: figure where-rare
Источники из анкет после словаря синонимов. Всё, что встретилось реже 10 раз, `where` заменяет на «прочее»; пропуски остаются пропусками.
:::

::: predict
```python static
import pandas as pd
s = pd.Series(["a", "b", "c"])
print(s.where(s == "a", "x").tolist())
```

- `['x', 'b', 'c']`
- [x] `['a', 'x', 'x']`
- `['a']`

Почему: `where` **оставляет** значения, где условие верно, и заменяет остальные. Запомнить: «оставь, где…».
:::

{{practice: rare}}

## Правило по нескольким столбцам

Иногда категория зависит от нескольких полей сразу. Тогда функция получает целую строку, а `apply` вызывается у таблицы с `axis=1` — «по строкам»:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
df["weekend"] = df["datetime"].dt.dayofweek >= 5

def slot(row):
    if row["weekend"]:
        return "выходные"
    if row["datetime"].hour < 12:
        return "будни, утро"
    return "будни, день"

df["slot"] = df.apply(slot, axis=1)
df.groupby("slot")["amount"].agg(["count", "mean"]).round(1)
```

`row["weekend"]` — значение столбца в текущей строке. Такой `apply` медленнее, чем `cut` или словарь, но для десятков тысяч строк это незаметно.

::: note Что выбрать
- Интервалы чисел с известными границами — `pd.cut`.
- Равные по численности группы — `pd.qcut`.
- Текст и синонимы — словарь и `replace`.
- Сложная логика или несколько столбцов — функция и `apply`.
:::

{{practice: vip}}

## Практика

## task: check-size | Размер заказа | warmup

Напишите функцию `check_size(amount)`: до 300 ₽ — «малый», от 300 до 600 — «средний», от 600 — «крупный». Добавьте столбец `check` через `apply` и сохраните в `sizes` словарь «категория → число заказов».

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

def check_size(amount):
    ...

```

### check
```python
import pandas as _pd
f = need('check_size')
for v, w in [(299, 'малый'), (300, 'средний'), (599, 'средний'), (600, 'крупный'), (2000, 'крупный')]:
    assert f(v) == w, f'check_size({v}) = {f(v)!r}, а нужно {w!r}. Проверьте границы: 300 и 600 уже относятся к следующей категории.'
a = _pd.read_csv('orders_3m.csv')['amount']
want = {k: int(v) for k, v in a.apply(lambda x: 'малый' if x < 300 else 'средний' if x < 600 else 'крупный').value_counts().items()}
got = {k: int(v) for k, v in dict(need('sizes')).items()}
assert got == want, f'sizes = {got}.'
```

### hint
`if amount < 300: … elif amount < 600: … else: …`

### hint
`df["check"] = df["amount"].apply(check_size)`, затем `dict(df["check"].value_counts())`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

def check_size(amount):
    if amount < 300:
        return "малый"
    elif amount < 600:
        return "средний"
    else:
        return "крупный"

df["check"] = df["amount"].apply(check_size)
sizes = dict(df["check"].value_counts())
```

## task: parts | Время суток | warmup

Разбейте заказы по времени суток через `pd.cut`: утро — с 0 до 12 часов, день — с 12 до 17, вечер — с 17 до 24 (левая граница включается). Сохраните в `evening` число вечерних заказов.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])

```

### check
```python
import pandas as _pd
h = _pd.to_datetime(_pd.read_csv('orders_3m.csv')['datetime']).dt.hour
want = int((h >= 17).sum())
got = need('evening')
if got != want and got == int((h > 17).sum()):
    raise AssertionError(f'evening = {got} — заказы в 17 часов не попали в вечер. Нужно right=False.')
assert got == want, f'evening = {got}, а нужно {want}.'
```

### hint
Час — `df["datetime"].dt.hour`. «Левая граница включается» — это `right=False`: заказ в 17:00 уже вечерний.

### hint
`pd.cut(df["datetime"].dt.hour, bins=[0, 12, 17, 24], labels=["утро", "день", "вечер"], right=False)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
df["part"] = pd.cut(df["datetime"].dt.hour, bins=[0, 12, 17, 24],
                    labels=["утро", "день", "вечер"], right=False)
evening = (df["part"] == "вечер").sum()
```

## task: p-cut | Дорогие напитки | warmup

Соберите программу, которая делит заказы на «до 400» и «400 и больше» и выводит число заказов во второй группе.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
bins = [0, 400, float("inf")]
df["band"] = pd.cut(df["amount"], bins=bins, labels=["до 400", "400+"], right=False)
print((df["band"] == "400+").sum())
```

### check
```python
import pandas as _pd
want = int((_pd.read_csv('orders_3m.csv')['amount'] >= 400).sum())
assert _lines == [str(want)], f'Должно вывестись {want}. Сейчас: {_lines}'
```

### hint
Границы объявляются до `cut`, вывод — в конце.

### hint
`float("inf")` — бесконечность: самая дорогая покупка всё равно попадёт в последний интервал.

## task: freq | Частота визитов | base

Посчитайте число заказов у каждого гостя с картой и разложите гостей по группам через `pd.cut`: 1–3 заказа — «редкие», 4–6 — «обычные», 7 и больше — «частые». Сохраните в `segments` словарь «группа → число гостей».

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
n = _pd.read_csv('orders_3m.csv').groupby('client_id').size()
want = {'редкие': int((n <= 3).sum()), 'обычные': int(n.between(4, 6).sum()), 'частые': int((n >= 7).sum())}
got = {str(k): int(v) for k, v in dict(need('segments')).items()}
assert set(got) == set(want), f'Ключи: {sorted(got)}.'
assert got == want, f'segments = {got}, а нужно {want}. Проверьте границы интервалов.'
```

### hint
Заказы на гостя — `df.groupby("client_id").size()`. Пропуски `client_id` в `groupby` не попадут.

### hint
Границы для `right=False`: `[1, 4, 7, float("inf")]` — интервалы `[1, 4)`, `[4, 7)`, `[7, ∞)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
n = df.groupby("client_id").size()
seg = pd.cut(n, bins=[1, 4, 7, float("inf")], labels=["редкие", "обычные", "частые"], right=False)
segments = dict(seg.value_counts())
```

### explain
Границы `[1, 4, 7, ∞)` с `right=False` в точности повторяют слова задачи: 4 заказа — уже «обычный» гость, 7 — уже «частый». С границами по умолчанию гости с 4 и 7 заказами попали бы на группу ниже — разница незаметна в коде и заметна в отчёте.

## task: quartiles | Верхняя четверть | base

Разбейте гостей с картой на 4 равные группы по сумме покупок (`pd.qcut`) и сохраните в `top_share` долю выручки верхней четверти (в процентах от выручки всех гостей с картой, один знак).

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
sp = _pd.read_csv('orders_3m.csv').groupby('client_id')['amount'].sum()
q = _pd.qcut(sp, 4, labels=[1, 2, 3, 4])
want = round(sp[q == 4].sum() / sp.sum() * 100, 1)
assert close(need('top_share'), want), f'top_share = {need("top_share")}, а нужно {want}.'
```

### hint
`spend = df.groupby("client_id")["amount"].sum()`, `q = pd.qcut(spend, 4, labels=["Q1", "Q2", "Q3", "Q4"])`.

### hint
Выручка верхней четверти — `spend[q == "Q4"].sum()`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
spend = df.groupby("client_id")["amount"].sum()
q = pd.qcut(spend, 4, labels=["Q1", "Q2", "Q3", "Q4"])
top_share = round(spend[q == "Q4"].sum() / spend.sum() * 100, 1)
```

### explain
Четверть гостей приносит больше четверти выручки — это нормально и ожидаемо. Насколько больше — важная метрика для программы лояльности: чем сильнее перекос, тем дороже потерять одного гостя из верхней группы.

## task: online | Онлайн или офлайн | base

Сведите источник к двум группам. Сначала нормализуйте (`strip`, `lower`) и примените словарь синонимов из урока, затем укрупните: «соцсети», «карты», «реклама» → «онлайн»; «друзья», «мимо» → «офлайн». Остальные значения и пропуски — «другое». Результат — в столбец `channel`, в `channels` — словарь «группа → число анкет».

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
synonyms = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

```

### check
```python
import pandas as _pd
syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
s = _pd.read_csv('clients_raw.csv')['source'].str.strip().str.lower().replace(syn)
grp = {'соцсети': 'онлайн', 'карты': 'онлайн', 'реклама': 'онлайн', 'друзья': 'офлайн', 'мимо': 'офлайн'}
want = s.map(grp).fillna('другое')
d = need('df', _pd.DataFrame)
assert 'channel' in d.columns, 'Нет столбца channel.'
assert d['channel'].isna().sum() == 0, 'В channel остались пропуски — они тоже «другое».'
assert (d['channel'] == want).all(), f'channel не совпадает. Например, {s[d["channel"] != want].iloc[0]!r} → {d["channel"][d["channel"] != want].iloc[0]!r}.'
got = {k: int(v) for k, v in dict(need('channels')).items()}
assert got == {k: int(v) for k, v in want.value_counts().items()}, f'channels = {got}.'
```

### hint
Сначала приведите источник к одному виду: `s = df["source"].str.strip().str.lower().replace(synonyms)`.

### hint
Здесь удобен `map`: значения, которых нет в словаре групп, станут `NaN`. А дальше — `fillna("другое")`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
synonyms = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}
groups = {"соцсети": "онлайн", "карты": "онлайн", "реклама": "онлайн",
          "друзья": "офлайн", "мимо": "офлайн"}
src = df["source"].str.strip().str.lower().replace(synonyms)
df["channel"] = src.map(groups).fillna("другое")
channels = dict(df["channel"].value_counts())
```

### explain
Здесь `map` и `fillna` работают вместе: всё, что не попало в словарь, — «другое». Это та самая разница `map` и `replace`: `map` превращает незнакомые значения в `NaN`. Иногда это ошибка, а иногда — ровно то, что нужно.

## task: rare | Собрать редкие | plus

Напишите функцию `lump(s, min_count)`: значения, которые встречаются меньше `min_count` раз, заменяются на «прочее»; частые значения и пропуски остаются как есть. Сохраните в `src` очищенный источник (нормализация + синонимы) после `lump(..., 10)`.

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
synonyms = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

def lump(s, min_count):
    ...

src = lump(df["source"].str.strip().str.lower().replace(synonyms), 10)
src.value_counts(dropna=False)
```

### check
```python
import pandas as _pd
f = need('lump')
t = _pd.Series(['a', 'a', 'b', None, 'c', 'a'])
r = f(t, 2)
assert r.tolist()[:3] == ['a', 'a', 'прочее'] and _pd.isna(r[3]) and r[4] == 'прочее', f'lump(["a","a","b",None,"c","a"], 2) = {r.tolist()}. Пропуск должен остаться пропуском.'
assert f(t, 1).tolist()[:3] == ['a', 'a', 'b'], 'При min_count=1 ничего заменять не нужно.'
syn = {'соц. сети': 'соцсети', 'от друзей': 'друзья', 'проходил мимо': 'мимо', '2гис': 'карты', 'яндекс карты': 'карты'}
s = _pd.read_csv('clients_raw.csv')['source'].str.strip().str.lower().replace(syn)
vc = s.value_counts()
want = s.where(s.isin(vc[vc >= 10].index) | s.isna(), 'прочее')
got = need('src', _pd.Series)
assert (got.fillna('-') == want.fillna('-')).all(), 'src не совпадает с ожидаемым.'
```

### hint
Внутри: `counts = s.value_counts()`, частые — `counts[counts >= min_count].index`.

### hint
`s.where(s.isin(frequent) | s.isna(), "прочее")`.

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
synonyms = {"соц. сети": "соцсети", "от друзей": "друзья", "проходил мимо": "мимо",
            "2гис": "карты", "яндекс карты": "карты"}

def lump(s, min_count):
    counts = s.value_counts()
    frequent = counts[counts >= min_count].index
    return s.where(s.isin(frequent) | s.isna(), "прочее")

src = lump(df["source"].str.strip().str.lower().replace(synonyms), 10)
src.value_counts(dropna=False)
```

### explain
`where` оставляет значение, если условие истинно, и подставляет «прочее», если ложно. Условие `isin(frequent) | isna()` защищает пропуски: без второй части они тоже превратились бы в «прочее», и мы бы смешали «гость не ответил» с «редкий ответ». После объединения синонимов в `src` остаются пять частых источников (друзья, соцсети, мимо, карты, реклама), 27 пропусков и 9 анкет «прочее» — это три редких ответа, каждый реже 10 раз. Функция с параметром `min_count` пригодится для любого столбца с длинным хвостом категорий.

## task: age-groups | Возрастные группы | plus

Посчитайте возраст гостей на 1 декабря 2026 года, как в уроке «Типы: из текста в числа и даты» (дата рождения в двух форматах, `дни // 365.25`). Разложите по группам через `pd.cut` с `right=False`: 14–24, 25–34, 35–44, 45–59, 60–99 — с подписями `"14–24"`, `"25–34"` и т. д. (можно писать через обычный дефис: `"14-24"`, проверка примет оба варианта). Возрасты вне этих интервалов станут пропусками. Сохраните в `groups` словарь «группа → число анкет».

### starter
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
iso = pd.to_datetime(df["birth_date"], format="%Y-%m-%d", errors="coerce")
ru = pd.to_datetime(df["birth_date"], format="%d.%m.%Y", errors="coerce")
born = iso.fillna(ru)

```

### check
```python
import pandas as _pd
b = _pd.read_csv('clients_raw.csv')['birth_date']
born = _pd.to_datetime(b, format='%Y-%m-%d', errors='coerce').fillna(_pd.to_datetime(b, format='%d.%m.%Y', errors='coerce'))
age = (_pd.Timestamp('2026-12-01') - born).dt.days // 365.25
labels = ['14–24', '25–34', '35–44', '45–59', '60–99']
g = _pd.cut(age, bins=[14, 25, 35, 45, 60, 100], labels=labels, right=False)
want = {k: int(v) for k, v in g.value_counts().items()}
got = {str(k).replace('-', '–'): int(v) for k, v in dict(need('groups')).items()}
assert set(got) == set(labels), f'Ключи: {sorted(got)}, а нужны {labels}.'
assert got == want, f'groups = {got}, а нужно {want}.'
```

### hint
Границы: `[14, 25, 35, 45, 60, 100]` — на одну больше, чем подписей.

### hint
Возраст: `age = (pd.Timestamp("2026-12-01") - born).dt.days // 365.25`. С `right=False` гость 25 лет попадает уже в «25–34», а не в «14–24».

### solution
```python
import pandas as pd
df = pd.read_csv("clients_raw.csv")
iso = pd.to_datetime(df["birth_date"], format="%Y-%m-%d", errors="coerce")
ru = pd.to_datetime(df["birth_date"], format="%d.%m.%Y", errors="coerce")
born = iso.fillna(ru)
age = (pd.Timestamp("2026-12-01") - born).dt.days // 365.25
df["age_group"] = pd.cut(age, bins=[14, 25, 35, 45, 60, 100],
                         labels=["14–24", "25–34", "35–44", "45–59", "60–99"], right=False)
groups = dict(df["age_group"].value_counts())
```

### explain
Даты-заглушки 1900-01-01 и дата из будущего дали возраст вне всех интервалов, и `cut` сам превратил их в пропуски. Удобно, но молча: в отчёте стоит написать, сколько анкет не попало ни в одну группу.

## task: vip | Сегменты гостей | star

Для каждого гостя с картой посчитайте `orders` (число заказов) и `avg_check` (средний чек). Присвойте сегмент функцией от строки:

- «VIP» — 7 и больше заказов **и** средний чек не ниже медианы средних чеков всех гостей;
- «частый» — 7 и больше заказов, чек ниже медианы;
- «щедрый» — меньше 7 заказов, чек не ниже медианы;
- «обычный» — остальные.

Таблицу гостей с столбцом `segment` сохраните в `guests`, а в `n_vip` — число VIP.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
g = _pd.read_csv('orders_3m.csv').groupby('client_id').agg(orders=('order_id', 'count'), avg_check=('amount', 'mean'))
m = g['avg_check'].median()
f, h = g['orders'] >= 7, g['avg_check'] >= m
want = _pd.Series('обычный', index=g.index)
want[f & h] = 'VIP'
want[f & ~h] = 'частый'
want[~f & h] = 'щедрый'
gg = need('guests', _pd.DataFrame)
if 'client_id' in gg.columns:
    gg = gg.set_index('client_id')
assert 'segment' in gg.columns, 'Нет столбца segment.'
got = gg['segment'].reindex(want.index)
assert (got == want).all(), f'Сегменты не совпадают, например у {want.index[got != want][0]}: {got[got != want].iloc[0]!r}, а нужно {want[got != want].iloc[0]!r}.'
assert need('n_vip') == int((want == 'VIP').sum()), f'n_vip = {need("n_vip")}.'
```

### hint
`guests = df.groupby("client_id").agg(orders=("order_id", "count"), avg_check=("amount", "mean"))`, медиана — `guests["avg_check"].median()`.

### hint
Функция `def segment(row):` читает `row["orders"]` и `row["avg_check"]`. Медиану посчитайте до функции и используйте внутри. Применение — `guests.apply(segment, axis=1)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
guests = df.groupby("client_id").agg(orders=("order_id", "count"), avg_check=("amount", "mean"))
med = guests["avg_check"].median()

def segment(row):
    frequent = row["orders"] >= 7
    generous = row["avg_check"] >= med
    if frequent and generous:
        return "VIP"
    if frequent:
        return "частый"
    if generous:
        return "щедрый"
    return "обычный"

guests["segment"] = guests.apply(segment, axis=1)
n_vip = (guests["segment"] == "VIP").sum()
```

### explain
Это упрощённая RFM-сегментация — классика маркетинговой аналитики: Recency (давность), Frequency (частота), Monetary (деньги). Мы взяли две буквы из трёх. Пороги («7 заказов», «медиана») — договорённость с бизнесом, а не закон природы: их стоит обсудить и записать.
