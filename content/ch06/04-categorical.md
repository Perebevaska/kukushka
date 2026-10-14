---
title: Категориальные признаки и утечки
lead: "Главная причина опозданий — тип курьера, но `courier` — текст, а sklearn понимает только числа. В уроке «Решающее дерево изнутри» мы сделали вручную один флаг «пеший»; теперь учимся превращать в числа любые категории, готовить новые данные так же, как обучающие, и ловить утечки — признаки, которые подсказывают модели ответ из будущего."
files: [deliveries.csv]
recap:
  - "Модели sklearn принимают только числа. Категорию превращают в столбцы-флаги 0/1: `pd.get_dummies(df, dtype=int)` — по столбцу на каждое значение (one-hot кодирование)."
  - "Коды 0/1/2 для категорий без естественного порядка придумывают порядок, которого нет: модель ищет пороги «больше-меньше» и путается. Особенно страдают линейные модели."
  - "`drop_first=True` убирает один флаг из каждой группы: он однозначно восстанавливается из остальных. Нужен линейной модели без регуляризации; деревьям — не обязательно (подробнее — в уроке «Логистическая регрессия и вероятности»)."
  - "Новые данные кодируют так же, а затем выравнивают по столбцам обучения: `X_new.reindex(columns=X_train.columns, fill_value=0)`."
  - "Утечка — признак, который известен только после события (`rating`, `actual_min`) или пересчитан с подглядыванием в тест. Всё, что считается по данным (доли, средние, заполнение пропусков), считают только по обучающей части."
  - "Подозрительно хорошее качество — повод проверить важность признаков и спросить про каждый: «знаем ли мы это в момент прогноза?»"
---

## Текст в числа

Попробуем дать дереву тип курьера как есть:

```python error
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[["distance_km", "courier"]], y)
```

Ошибка `could not convert string to float`: модели в sklearn работают только с числами. Текстовые столбцы с небольшим набором значений — `courier`, `weather`, `shop_id` — называют **категориальными признаками**, и их нужно закодировать.

Самый надёжный способ — **one-hot кодирование**: для каждого значения категории заводится свой столбец-флаг, где 1 — «да, это оно», 0 — «нет». В pandas это делает `pd.get_dummies`:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
pd.get_dummies(d[["distance_km", "courier"]].head(4), dtype=int)
```

Числовые столбцы `get_dummies` оставляет как есть, а текстовые заменяет флагами с именами `столбец_значение`. `dtype=int` — флаги числами 0/1 (без него будут `True/False`; модели примут и их, но 0/1 нагляднее).

::: figure onehot-flags
Первые четыре доставки до и после `get_dummies`: столбец `courier` превратился в три флага — по одному на каждое значение.
:::

::: sql
То же самое руками: `CASE WHEN courier = 'пеший' THEN 1 ELSE 0 END AS courier_пеший` — и так для каждого значения. `get_dummies` пишет все эти `CASE` за вас.
:::

{{practice: dummies}}

## Почему не 0, 1, 2

Кажется, проще пронумеровать: вело = 0, пеший = 1, авто = 2. Один столбец вместо трёх. Но так мы сообщаем модели то, чего нет: что «пеший» находится **между** «вело» и «авто», а «авто» — вдвое «больше» пешего. Дерево задаёт вопросы «признак ≤ порога?» и честно ищет пороги на этой выдуманной шкале:

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]

codes = ok[num].assign(courier=ok["courier"].map({"вело": 0, "пеший": 1, "авто": 2}))
dummies = pd.get_dummies(ok[num + ["courier"]], dtype=int)

for name, X in [("коды 0/1/2", codes), ("флаги", dummies)]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train)
    print(f"{name}: {model.score(X_test, y_test):.3f}")
```

С флагами дереву хватает одного вопроса «`courier_пеший` ≤ 0.5?», чтобы отделить пеших. С кодами пешие оказались в середине шкалы, и одним порогом их не вырезать — дерево глубины 2 тратит вопросы впустую и теряет около 9 п.п.

::: note
При другом порядке кодов (например, пеший = 0) дереву могло и повезти. Но качество модели не должно зависеть от случайной нумерации. Линейные модели (урок «Логистическая регрессия и вероятности») страдают сильнее: для них код 2 буквально значит «вдвое больше, чем 1».
:::

### Разберём вместе: какие группы может вырезать один вопрос

Доли опозданий по типам курьера: вело — 0.13 (872 доставки), пеший — 0.74 (403), авто — 0.05 (566).

**Коды вело = 0, пеший = 1, авто = 2.** Один вопрос «код ≤ порог» может разрезать шкалу только в двух местах:

- «≤ 0.5»: слева вело (0.13), справа пеший + авто. Опозданий справа (298 + 30) / (403 + 566) = 328 / 969 ≈ **0.34**;
- «≤ 1.5»: слева вело + пеший — (113 + 298) / (872 + 403) = 411 / 1275 ≈ **0.32**, справа авто (0.05).

Ни один вопрос не отделяет пеших: они «зажаты» в середине шкалы и всегда смешиваются с соседями. Группа с долей 0.74 растворяется до 0.32–0.34.

**Флаг `courier_пеший`.** Вопрос «флаг ≤ 0.5» сразу даёт две группы: пешие — **0.74**, все остальные — (113 + 30) / 1438 ≈ **0.10**.

Что получилось: флаги позволяют дереву вырезать любую категорию одним вопросом, коды — только «кусок шкалы слева или справа». Поэтому для категорий без настоящего порядка — флаги.

::: figure codes-cut
Коды 0/1/2 ставят курьеров на одну шкалу, и любой порог отрезает кусок слева или справа — пешие всегда смешаны с соседями. Флаг `courier_пеший` отделяет их одним вопросом.
:::

Номера уместны, только когда порядок в категории настоящий: размер стакана S < M < L, уровень лояльности. Тогда `map({"S": 0, "M": 1, "L": 2})` передаёт модели реальную информацию.

{{practice: codes}}

## Лишний флаг: drop_first

У трёх флагов курьера в каждой строке ровно одна единица. Значит, третий флаг всегда восстанавливается из двух других: если не вело и не авто — значит пеший. Параметр `drop_first=True` выбрасывает первый флаг из каждой группы:

::: predict
```python static
import pandas as pd
df = pd.DataFrame({"km": [1.0, 3.5, 2.0], "courier": ["пеший", "авто", "вело"]})
print(pd.get_dummies(df, dtype=int).shape[1], pd.get_dummies(df, drop_first=True, dtype=int).shape[1])
```

- `3 3`
- [x] `4 3`
- `4 2`

Почему: без `drop_first` — `km` и три флага, итого 4 столбца. С `drop_first=True` пропадает флаг первого по алфавиту значения (`courier_авто`), остаётся 3. Выброшенное значение кодируется нулями во всех оставшихся флагах.
:::

Деревьям лишний флаг не вредит, а иногда помогает: вопрос «пеший?» задаётся напрямую. Поэтому в этой главе оставляем все флаги. Когда `drop_first` нужен и как читать модель без него — разберём в уроке «Логистическая регрессия и вероятности», там появятся веса признаков.

{{practice: drop-first}}

## Модель видит курьера

Добавим к числовым признакам курьера, погоду и кофейню и сравним с прошлыми уроками на тех же обучающей и тестовой частях:

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]

X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
print(X.shape[1], "признаков")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

only_num = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train[num], y_train)
full = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
rule = X_test["courier_пеший"] == 1
print(f"только числа:  {only_num.score(X_test[num], y_test):.3f}")
print(f"с категориями: {full.score(X_test, y_test):.3f}")
print(f"правило «пеший»: {(rule == y_test).mean():.3f}")
pd.Series(full.feature_importances_, index=X.columns).sort_values(ascending=False).head(4)
```

Скачок с 78 % до 90 % — как с флагом `walk` в уроке «Решающее дерево изнутри»: модель видит главную причину, и по важности `courier_пеший` далеко впереди остальных. Но обратите внимание: правило «пеший — опоздает» на тесте почти так же хорошо. Пока модель в основном переоткрыла то, что аналитик знал и так. Сможет ли ансамбль деревьев выжать больше — в уроке «Случайный лес».

{{practice: p-dummies, gain}}

## Новые данные — те же столбцы

Модель обучена на определённом наборе столбцов в определённом порядке. Новые заказы приходят по одному или небольшими пачками, и `get_dummies` по ним создаст только те флаги, которые в них встретились:

```python error
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = pd.get_dummies(ok[["distance_km", "courier", "weather"]], dtype=int)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, ok["actual_min"] > ok["promised_min"])

new = pd.DataFrame({"distance_km": [1.2, 6.0], "courier": ["пеший", "авто"], "weather": ["снег", "туман"]})
X_new = pd.get_dummies(new, dtype=int)
print(list(X_new.columns))
model.predict(X_new)
```

Не хватает флагов `courier_вело`, `weather_ясно` и других, зато появился `weather_туман`, которого модель не видела. sklearn сверяет имена столбцов с обучением и отказывается работать. Лекарство — **выровнять** столбцы по обучающей таблице:

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = pd.get_dummies(ok[["distance_km", "courier", "weather"]], dtype=int)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, ok["actual_min"] > ok["promised_min"])

new = pd.DataFrame({"distance_km": [1.2, 6.0], "courier": ["пеший", "авто"], "weather": ["снег", "туман"]})
X_new = pd.get_dummies(new, dtype=int).reindex(columns=X.columns, fill_value=0)
print(X_new)
print(model.predict(X_new))
```

`reindex(columns=X.columns, fill_value=0)` делает три вещи сразу: ставит столбцы в порядок обучения, добавляет недостающие флаги нулями и выбрасывает незнакомые (`weather_туман`). Туман для модели теперь — «ни одна из известных погод». Это разумное поведение по умолчанию, но если новых значений много, модель пора переобучить.

::: figure dummies-reindex
Слева — флаги двух новых заказов, справа — столбцы, на которых училась модель. `reindex` берёт правый список: совпавшие столбцы переносит, недостающие заполняет нулями, незнакомый `weather_туман` выбрасывает.
:::

::: tip
Правило: всё, что делалось с обучающими данными (фильтры, новые столбцы вроде `hour`, кодирование), нужно повторить для новых данных **тем же кодом**. Удобно завернуть подготовку в функцию и вызывать её в обоих местах. В главе 7 для этого будет готовый инструмент — `Pipeline`.
:::

{{practice: new-orders, prepare}}

## Утечки: подсказки из будущего

В уроке «Что такое машинное обучение» мы видели, что `actual_min` в признаках — **утечка**: модель получает информацию, которой в момент прогноза ещё нет. Утечки бывают менее очевидными. Возьмём `rating` — оценку гостя. Она выглядит как обычная характеристика заказа, но гость ставит её **после** доставки, уже зная, опоздал ли курьер:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = ok["actual_min"] > ok["promised_min"]
print(late.groupby(ok["rating"]).mean().round(2))
```

Все оценки 1 и 2 — опоздавшие доставки. Модель с `rating` выглядела бы лучше, но в момент отправки курьера оценки нет и быть не может. Перед тем как брать столбец в признаки, задайте вопрос: **известно ли это значение в момент, когда нужен прогноз?**

::: tip Аналогия
Утечка — это как «предсказывать», понравится ли гостю латте, по его отзыву в приложении. Точность почти идеальная, но прогноз нужен, пока бариста ещё не налил молоко, а отзыва в этот момент не существует. В исторической таблице «будущее» уже записано рядом с прошлым, поэтому модель с утечкой блестит на тесте и бесполезна в работе.
:::

Если утечка сильная, её выдаёт подозрительно хорошее качество. Вернём `actual_min` к признакам и посмотрим, что скажет модель:

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "actual_min", "courier"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

model = DecisionTreeClassifier(max_depth=5, random_state=0).fit(X_train, y_train)
print(f"на тесте: {model.score(X_test, y_test):.3f}")
pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False).head(3)
```

Почти 100 % на тесте там, где честная модель даёт около 90 %, — не победа, а сигнал тревоги. Порядок проверки:

1. Сравнить с базовой моделью и правилом аналитика. Скачок с 90 % до 99–100 % почти всегда означает утечку.
2. Посмотреть `feature_importances_`: какой признак тянет модель.
3. Про этот признак спросить: когда он появляется в базе и откуда берётся.

::: warn Утечка через предобработку
Утечку можно внести, даже не добавляя подозрительных столбцов. Например, признак «доля опозданий в этой кофейне», посчитанный по **всем** данным, использует ответы тестовых доставок — модель заранее подсмотрела часть экзамена. То же со средним для заполнения пропусков и с любой другой статистикой. Правило: сначала разбить, потом считать статистики **только по обучающей части** и применять их к тесту.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[["shop_id"]], y, test_size=0.25, random_state=42)

shop_rate = y_train.groupby(X_train["shop_id"]).mean()     # только по обучающей части
all_rate = y.groupby(ok["shop_id"]).mean()                 # «нечестно»: вместе с тестом
X_train = X_train.assign(shop_rate=X_train["shop_id"].map(shop_rate))
X_test = X_test.assign(shop_rate=X_test["shop_id"].map(shop_rate))
print(pd.concat([shop_rate, all_rate], axis=1, keys=["по обучающей", "по всем"]).round(3))
```

Здесь разница с «нечестным» вариантом невелика — доли расходятся на 0.1–1.2 п.п.: кофеен всего шесть, и по каждой много доставок. Но чем мельче группы (отдельный курьер, отдельный гость), тем сильнее такая утечка завышает качество.

::: warn Типичные ошибки
- **`get_dummies` отдельно на train и test.** Наборы столбцов разойдутся, если в тесте нет какой-то категории; выравнивайте `reindex(columns=..., fill_value=0)`.
- **Коды для неупорядоченных категорий.** Модель увидит порядок, которого нет.
- **`drop_first` для деревьев.** Не ошибка, но и не нужно.
- **Утечка через признак.** Оценка гостя, фактическое время, статус «опоздал» в CRM — всё это появляется после события.
- **Статистика по всем данным.** Доля опозданий кофейни, посчитанная вместе с тестом, — тоже подглядывание.
:::

::: quiz
Аналитик добавил признак «доля опозданий этого курьера за всю историю»: посчитал по всем доставкам, затем разбил данные на обучающую и тестовую части. Качество на тесте выросло с 90 % до 94 %. Что не так?

- [x] Это утечка через предобработку: в долю курьера вошли и тестовые доставки, модель заранее подсмотрела часть ответов
  > Долю нужно считать только по обучающей части и применять к тесту. У отдельных курьеров доставок мало, поэтому подсмотренные ответы сильно сдвигают долю — и качество на тесте завышается.
- [ ] Всё честно: доля опозданий курьера известна до выезда
  > Как идея — да, это честный признак. Но посчитать его нужно без тестовых строк, иначе тест перестаёт быть экзаменом.
- [ ] Утечка в самом признаке «курьер»: тип курьера знают после доставки
  > Курьера назначают до выезда — сам по себе признак честный. Проблема в том, по каким строкам посчитана доля.
- [ ] Ничего: рост на 4 п.п. показывает, что признак полезный
  > Рост может быть и честным, но при таком расчёте его нельзя отличить от подглядывания. Сначала разбить — потом считать.
:::

{{practice: rating-leak, suspicious, shop-rate}}

## Практика

## task: dummies | Флаги курьера | warmup

Закодируйте столбец `courier` флагами (0/1) и сохраните таблицу в `dm`. В `n_walk` сохраните число пеших доставок — сумму соответствующего флага.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
dm = need('dm', _pd.DataFrame)
want = ['courier_авто', 'courier_вело', 'courier_пеший']
assert sorted(dm.columns) == want, f'Столбцы dm: {list(dm.columns)}, а ожидались флаги {want}. Кодируйте только столбец courier.'
assert len(dm) == len(ok), f'В dm {len(dm)} строк, а доставок с временем 1–299 минут — {len(ok)}.'
assert set(_pd.unique(dm.to_numpy().ravel())) <= {0, 1} and dm.to_numpy().dtype.kind in 'iu', 'Флаги должны быть числами 0/1 — не забыли dtype=int?'
assert need('n_walk') == (ok['courier'] == 'пеший').sum(), f'n_walk = {need("n_walk")}. Сложите флаг courier_пеший.'
```

### hint
`pd.get_dummies(ok[["courier"]], dtype=int)` — двойные скобки, чтобы получилась таблица.

### hint
Сумма флага — число единиц в нём: `dm["courier_пеший"].sum()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
dm = pd.get_dummies(ok[["courier"]], dtype=int)
n_walk = dm["courier_пеший"].sum()
```

## task: drop-first | Сколько столбцов | warmup

Закодируйте `courier`, `weather` и `shop_id` (только их) двумя способами: со всеми флагами и с `drop_first=True`. Сохраните число столбцов в `n_full` и `n_drop`.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
cats = ok[["courier", "weather", "shop_id"]]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
c = ok[['courier', 'weather', 'shop_id']]
a = _pd.get_dummies(c).shape[1]
b = _pd.get_dummies(c, drop_first=True).shape[1]
assert need('n_full') == a, f'n_full = {need("n_full")}. Флагов должно быть столько, сколько всего разных значений в трёх столбцах.'
assert need('n_drop') == b, f'n_drop = {need("n_drop")}. С drop_first=True из каждой группы пропадает по одному флагу.'
```

### hint
Число столбцов таблицы — `.shape[1]`.

### hint
`drop_first=True` выбрасывает по одному флагу у каждого закодированного столбца: выброшенное значение и так восстанавливается, когда все остальные флаги равны нулю. Столбцов три, поэтому `n_drop` должно получиться ровно на 3 меньше `n_full` — проверьте себя этим.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
cats = ok[["courier", "weather", "shop_id"]]
n_full = pd.get_dummies(cats, dtype=int).shape[1]
n_drop = pd.get_dummies(cats, drop_first=True, dtype=int).shape[1]
```

### explain
3 + 4 + 6 = 13 значений — 13 флагов. Без первого флага в каждой из трёх групп — 10.

## task: p-dummies | Модель с курьером | warmup

Соберите программу: закодировать признаки, разбить данные, обучить дерево глубины 3 и вывести долю правильных ответов на тесте (3 знака).

### parsons
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "promised_min", "courier"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
print(round(model.score(X_test, y_test), 3))
```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'promised_min', 'courier']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
w = str(round(_T(max_depth=3, random_state=0).fit(a, ya).score(b, yb), 3))
assert _lines == [w], f'Программа вывела {_lines}, а ожидалось [{w!r}]. Кодирование — до разбиения, обучение — на обучающей части, оценка — на тестовой.'
```

### hint
Порядок: данные → `y` → `X` с флагами → разбиение → обучение → оценка.

## task: gain | Что дают погода и кофейня | base

В теории курьер поднял точность с 78 % до 90 %. А что добавляют другие категории? Признаки — `distance_km`, `items`, `promised_min`, `hour` и флаги `courier`. Обучите `DecisionTreeClassifier(max_depth=3, random_state=0)` трижды и сохраните долю правильных ответов на тесте (3 знака):

- `acc_courier` — числа и курьер;
- `acc_weather` — то же плюс флаги `weather`;
- `acc_shop` — числа, курьер и флаги `shop_id` (без погоды).

В `gain_weather` и `gain_shop` — прирост к `acc_courier` в процентных пунктах (1 знак). Разбиение — `train_test_split(..., test_size=0.25, random_state=42)` для всех вариантов. Прирост может оказаться нулевым — это тоже ответ.

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
num = ['distance_km', 'items', 'promised_min', 'hour']
def _acc(cols):
    X = _pd.get_dummies(ok[num + cols], dtype=int)
    a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
    return round(_T(max_depth=3, random_state=0).fit(a, ya).score(b, yb), 3)
c, w, sh = _acc(['courier']), _acc(['courier', 'weather']), _acc(['courier', 'shop_id'])
assert close(need('acc_courier'), c), f'acc_courier = {need("acc_courier")}, а ожидалось {c}. Числовые признаки плюс флаги courier.'
assert close(need('acc_weather'), w), f'acc_weather = {need("acc_weather")}, а ожидалось {w}. Добавьте к ним флаги weather.'
assert close(need('acc_shop'), sh), f'acc_shop = {need("acc_shop")}, а ожидалось {sh}. Числа, курьер и флаги shop_id, без погоды.'
assert close(need('gain_weather'), round((w - c) * 100, 1)) and close(need('gain_shop'), round((sh - c) * 100, 1)), 'gain_* — разница с acc_courier, умноженная на 100.'
```

### hint
Удобно написать функцию `test_acc(cols)`: она строит `pd.get_dummies(ok[num + cols], dtype=int)`, разбивает, обучает дерево и возвращает долю на тесте. Вызовите её с `["courier"]`, `["courier", "weather"]` и `["courier", "shop_id"]`.

### hint
`gain_weather = round((acc_weather - acc_courier) * 100, 1)`, так же для кофейни.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]

def test_acc(cols):
    X = pd.get_dummies(ok[num + cols], dtype=int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
    return round(model.score(X_test, y_test), 3)

acc_courier = test_acc(["courier"])
acc_weather = test_acc(["courier", "weather"])
acc_shop = test_acc(["courier", "shop_id"])
gain_weather = round((acc_weather - acc_courier) * 100, 1)
gain_shop = round((acc_shop - acc_courier) * 100, 1)
```

### explain
Все три варианта дают 0.898: ни погода, ни кофейня не добавили ни одного верного ответа. Дело не в том, что они ни на что не влияют — в снег опаздывают чаще (глава 4), — а в том, что у дерева глубины 3 всего три вопроса подряд, и выгоднее потратить их на курьера, обещание и расстояние. Нулевой прирост — тоже вывод: новые признаки стоит добавлять, если они дают модели то, чего у неё ещё нет.

## task: codes | Коды против флагов | base

Сравните два способа подать модели курьера. Признаки — `distance_km`, `promised_min` и курьер:

- `acc_codes` — курьер одним столбцом `courier` с кодами `{"авто": 0, "пеший": 1, "вело": 2}` (порядок другой, чем в теории, но пеший снова в середине);
- `acc_flags` — курьер флагами `get_dummies`;
- `acc_lucky` — снова коды, но в другом порядке: `{"пеший": 0, "авто": 1, "вело": 2}`.

Модель — `DecisionTreeClassifier(max_depth=2, random_state=0)`, оценка на тесте (разбиение 0.25 / 42), доли — 3 знака.

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
def _acc(X):
    a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
    return round(_T(max_depth=2, random_state=0).fit(a, ya).score(b, yb), 3)
c = _acc(ok[['distance_km', 'promised_min']].assign(courier=ok['courier'].map({'авто': 0, 'пеший': 1, 'вело': 2})))
f = _acc(_pd.get_dummies(ok[['distance_km', 'promised_min', 'courier']], dtype=int))
assert close(need('acc_codes'), c), f'acc_codes = {need("acc_codes")}, а ожидалось {c}. Проверьте словарь кодов: авто 0, пеший 1, вело 2.'
assert close(need('acc_flags'), f), f'acc_flags = {need("acc_flags")}, а ожидалось {f}.'
l = _acc(ok[['distance_km', 'promised_min']].assign(courier=ok['courier'].map({'пеший': 0, 'авто': 1, 'вело': 2})))
assert close(need('acc_lucky'), l), f'acc_lucky = {need("acc_lucky")}, а ожидалось {l}. Коды: пеший 0, авто 1, вело 2.'
```

### hint
Коды: `ok["courier"].map({"авто": 0, "пеший": 1, "вело": 2})`. Добавить столбец к таблице признаков удобно через `.assign(courier=...)`.

### hint
Удобно написать одну функцию `test_acc(X)`, которая разбивает данные, обучает дерево и возвращает долю на тесте, и вызвать её дважды. Для флагов передайте в `get_dummies` таблицу из трёх столбцов: числовые `distance_km` и `promised_min` она оставит как есть, а `courier` развернёт во флаги.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]

def test_acc(X):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    return round(DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train).score(X_test, y_test), 3)

codes = ok[["distance_km", "promised_min"]].assign(courier=ok["courier"].map({"авто": 0, "пеший": 1, "вело": 2}))
acc_codes = test_acc(codes)
acc_flags = test_acc(pd.get_dummies(ok[["distance_km", "promised_min", "courier"]], dtype=int))
lucky = ok[["distance_km", "promised_min"]].assign(courier=ok["courier"].map({"пеший": 0, "авто": 1, "вело": 2}))
acc_lucky = test_acc(lucky)
```

### explain
С кодами пешие (1) зажаты между авто (0) и вело (2): чтобы их выделить, нужно два порога, а у дерева глубины 2 вопросов в обрез — 0.805. Флаг `courier_пеший` отделяет их одним вопросом — 0.896. А с кодами «пеший = 0» дереву повезло: пешие на краю шкалы, порог «≤ 0.5» их вырезает, и качество то же, что у флагов. Это и есть проблема кодов: результат зависит от случайной нумерации, а флаги работают при любой.

## task: new-orders | Заказы с новой погодой | base

Модель обучена на флагах признаков `distance_km`, `promised_min`, `courier`, `weather`. Подготовьте таблицу `X_new` для трёх новых заказов так, чтобы её столбцы совпадали со столбцами `X`, и сохраните предсказания списком `True/False` в `preds`.

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = pd.get_dummies(ok[["distance_km", "promised_min", "courier", "weather"]], dtype=int)
model = DecisionTreeClassifier(max_depth=4, random_state=0).fit(X, ok["actual_min"] > ok["promised_min"])

new = pd.DataFrame({"distance_km": [1.5, 1.8, 7.5],
                    "promised_min": [30, 30, 60],
                    "courier": ["пеший", "вело", "авто"],
                    "weather": ["гроза", "снег", "ясно"]})

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = _pd.get_dummies(ok[['distance_km', 'promised_min', 'courier', 'weather']], dtype=int)
m = _T(max_depth=4, random_state=0).fit(X, ok['actual_min'] > ok['promised_min'])
new = _pd.DataFrame({'distance_km': [1.5, 1.8, 7.5], 'promised_min': [30, 30, 60], 'courier': ['пеший', 'вело', 'авто'], 'weather': ['гроза', 'снег', 'ясно']})
w = _pd.get_dummies(new, dtype=int).reindex(columns=X.columns, fill_value=0)
xn = need('X_new', _pd.DataFrame)
assert list(xn.columns) == list(X.columns), f'Столбцы X_new не совпадают со столбцами X: лишние {sorted(set(xn.columns) - set(X.columns))}, недостающие {sorted(set(X.columns) - set(xn.columns))}. Помогут reindex и fill_value.'
assert len(xn) == 3 and (xn.to_numpy() == w.to_numpy()).all(), 'Столбцы верные, но значения не те: флаги новых заказов должны быть 0/1, недостающие — нулями.'
got = [bool(x) for x in need('preds')]
want = [bool(x) for x in m.predict(w)]
assert got == want, f'preds = {got}, а ожидалось {want}.'
```

### hint
Сначала `pd.get_dummies(new, dtype=int)`, затем выравнивание по `X.columns`.

### hint
`.reindex(columns=X.columns, fill_value=0)`; предсказания в список — `[bool(x) for x in model.predict(X_new)]`.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = pd.get_dummies(ok[["distance_km", "promised_min", "courier", "weather"]], dtype=int)
model = DecisionTreeClassifier(max_depth=4, random_state=0).fit(X, ok["actual_min"] > ok["promised_min"])

new = pd.DataFrame({"distance_km": [1.5, 1.8, 7.5],
                    "promised_min": [30, 30, 60],
                    "courier": ["пеший", "вело", "авто"],
                    "weather": ["гроза", "снег", "ясно"]})
X_new = pd.get_dummies(new, dtype=int).reindex(columns=X.columns, fill_value=0)
preds = [bool(x) for x in model.predict(X_new)]
```

### explain
У первого заказа погода «гроза» незнакома модели: все флаги погоды у него нули. Для модели это «ни одна из известных погод», и она отвечает по остальным признакам — пеший курьер с обещанием 30 минут. Если таких заказов станет много, модель пора переобучить на данных, где гроза уже есть.

## task: rating-leak | Оценка гостя | base

Проверьте, можно ли брать `rating` в признаки.

- `late_by_rating` — доля опозданий для каждой оценки (Series: индекс — оценка, значения округлите до 2 знаков);
- `leaks` — список столбцов из `["distance_km", "rating", "weather", "actual_min", "items", "courier"]`, которые **нельзя** брать в признаки для прогноза опоздания в момент отправки курьера.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
late = ok['actual_min'] > ok['promised_min']
w = late.groupby(ok['rating']).mean().round(2)
s = need('late_by_rating', _pd.Series)
assert len(s) == len(w) and [float(i) for i in s.index] == [float(i) for i in w.index], f'Индекс late_by_rating: {list(s.index)}, а нужны оценки {list(w.index)}. Группируйте по rating.'
assert all(close(a, b) for a, b in zip(s.to_numpy(), w.to_numpy())), f'Доли не совпали: {list(s.round(2))}. Нужна доля опозданий (среднее late) по каждой оценке.'
lk = need('leaks', list)
assert set(lk) == {'rating', 'actual_min'}, f'leaks = {lk}. Для каждого столбца спросите: известно ли это значение до того, как курьер выехал?'
```

### hint
`late.groupby(ok["rating"]).mean()` — Series с индексом-оценкой. Пропуски в `rating` при группировке отбрасываются.

### hint
Для `leaks` задайте себе вопрос: «Известно ли это значение в момент, когда курьер выезжает?». Расстояние, состав заказа, погода и тип курьера известны. Фактическое время и оценку гость ставит после доставки — это знания из будущего.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
late = ok["actual_min"] > ok["promised_min"]
late_by_rating = late.groupby(ok["rating"]).mean().round(2)
leaks = ["rating", "actual_min"]
```

### explain
Низкие оценки почти всегда означают опоздание, потому что гость ставит их, уже зная исход. Погода, расстояние, число позиций и курьер известны в момент заказа.

## task: suspicious | Подозрительно хорошо | plus

Коллега добавил к признакам столбец `delay` = `actual_min − promised_min` («отклонение от обещания») и радуется результату. Повторите его модель: флаги признаков `distance_km`, `items`, `promised_min`, `courier`, `weather` плюс `delay`, разбиение 0.25 / 42, `DecisionTreeClassifier(max_depth=3, random_state=0)`.

Сохраните `acc_test` — долю правильных ответов на тесте (3 знака) и `top` — название признака с наибольшей важностью.

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["delay"] = ok["actual_min"] - ok["promised_min"]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)].copy()
ok['delay'] = ok['actual_min'] - ok['promised_min']
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'courier', 'weather', 'delay']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
m = _T(max_depth=3, random_state=0).fit(a, ya)
assert close(need('acc_test'), round(m.score(b, yb), 3)), f'acc_test = {need("acc_test")}, а ожидалось {round(m.score(b, yb), 3)}. Проверьте состав признаков и разбиение.'
t = X.columns[m.feature_importances_.argmax()]
assert need('top') == t, f'top = {need("top")!r}. Возьмите признак с наибольшим значением feature_importances_.'
```

### hint
Важности — `pd.Series(model.feature_importances_, index=X.columns)`, наибольшая — `.idxmax()`.

### hint
Сначала создайте `ok = d[...].copy()` и столбец `ok["delay"]`, потом флаги через `pd.get_dummies(ok[[...]], dtype=int)`. Если `top` окажется `delay`, а доля правильных — подозрительно высокой, всё получилось: так выглядит утечка, ведь опоздание — это и есть `delay > 0`.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["delay"] = ok["actual_min"] - ok["promised_min"]
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "courier", "weather", "delay"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
acc_test = round(model.score(X_test, y_test), 3)
top = pd.Series(model.feature_importances_, index=X.columns).idxmax()
```

### explain
Опоздание — это ровно `delay > 0`, и дерево находит этот вопрос первым же разбиением. 100 % на тесте и один признак с важностью 1 — классическая картина утечки. Новое имя столбца не меняет сути: `delay` посчитан из `actual_min`, а его в момент заказа нет.

## task: shop-rate | Доля опозданий кофейни без подглядывания | plus

Сделайте признак «доля опозданий в кофейне» честно. Разбейте `ok[["shop_id"]]` и `y` (0.25 / 42). Посчитайте долю опозданий по кофейням **только по обучающей части** — `shop_rate` (Series: индекс — `shop_id`). Добавьте в `X_train` и `X_test` столбец `shop_rate` с этой долей для кофейни строки.

Сохраните также `diff` — наибольшее по модулю расхождение (по всем кофейням) между долей по обучающей части и долей по всем данным, в п.п., 2 знака.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
a, b, ya, yb = _tts(ok[['shop_id']], y, test_size=0.25, random_state=42)
r = ya.groupby(a['shop_id']).mean()
s = need('shop_rate', _pd.Series)
assert set(s.index) == set(r.index), f'Индекс shop_rate: {sorted(s.index)}. Нужны кофейни (shop_id).'
allr = y.groupby(ok['shop_id']).mean()
if all(close(s[k], allr[k], 1e-9) for k in r.index) and not all(close(s[k], r[k], 1e-9) for k in r.index):
    assert False, 'Доли посчитаны по всем данным — это и есть подглядывание. Группируйте только y_train по X_train["shop_id"].'
assert all(close(s[k], r[k], 1e-9) for k in r.index), 'shop_rate — доля опозданий по кофейням в обучающей части.'
xa, xb = need('X_train', _pd.DataFrame), need('X_test', _pd.DataFrame)
assert 'shop_rate' in xa.columns and 'shop_rate' in xb.columns, 'Добавьте столбец shop_rate и в X_train, и в X_test.'
assert len(xb) == len(b) and (xb['shop_rate'].to_numpy() == b['shop_id'].map(r).to_numpy()).all(), 'В X_test shop_rate должен браться из долей обучающей части: map по shop_id.'
assert (xa['shop_rate'].to_numpy() == a['shop_id'].map(r).to_numpy()).all(), 'В X_train shop_rate не совпал с долями по обучающей части.'
w = round(((r - allr).abs().max()) * 100, 2)
assert close(need('diff'), w), f'diff = {need("diff")}, а ожидалось {w}.'
```

### hint
`y_train.groupby(X_train["shop_id"]).mean()` — доли по обучающей части. Перенести на строки — `X_test["shop_id"].map(shop_rate)`.

### hint
Доли по всем данным — `y.groupby(ok["shop_id"]).mean()`. Разница двух Series выравнивается по индексу: `(shop_rate - all_rate).abs().max()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(ok[["shop_id"]], y, test_size=0.25, random_state=42)
shop_rate = y_train.groupby(X_train["shop_id"]).mean()
X_train = X_train.assign(shop_rate=X_train["shop_id"].map(shop_rate))
X_test = X_test.assign(shop_rate=X_test["shop_id"].map(shop_rate))
all_rate = y.groupby(ok["shop_id"]).mean()
diff = round((shop_rate - all_rate).abs().max() * 100, 2)
```

### explain
Расхождение — около процентного пункта: на шести крупных группах подглядывание почти незаметно. Но привычка важна — на мелких группах (гость, курьер) разница станет огромной, и модель покажет на тесте качество, которого в жизни не будет.

## task: prepare | Одна подготовка для всех данных | star

Напишите функцию `prepare(df, columns=None)`, которая готовит признаки из таблицы доставок в формате `deliveries.csv`:

- добавляет `hour` — час из `created` (в `df` он строкой или датой — функция должна работать с обоими вариантами);
- берёт столбцы `distance_km`, `items`, `promised_min`, `hour`, `courier`, `weather` и кодирует их флагами (`dtype=int`);
- если передан `columns` — выравнивает результат по этим столбцам (недостающие — нулями, лишние — убрать).

Проверка вызовет `prepare` на обучающих данных, а затем на новых заказах с `columns=` столбцами обучения — и сравнит результат с эталоном. Исходную таблицу функция менять не должна.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

def prepare(df, columns=None):
    ...

X = prepare(d)
X.head()
```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
def _ref(df, columns=None):
    df = df.assign(hour=_pd.to_datetime(df['created']).dt.hour)
    X = _pd.get_dummies(df[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather']], dtype=int)
    return X if columns is None else X.reindex(columns=columns, fill_value=0)
prepare = need('prepare')
d0 = d.copy()
X = prepare(d)
assert isinstance(X, _pd.DataFrame), 'prepare должна возвращать DataFrame.'
assert list(d.columns) == list(d0.columns), 'prepare изменила исходную таблицу — работайте с копией или через assign.'
w = _ref(d)
assert list(X.columns) == list(w.columns), f'Столбцы prepare(d): {list(X.columns)}, а ожидались {list(w.columns)}.'
assert (X.to_numpy() == w.to_numpy()).all(), 'Столбцы верные, но значения отличаются — проверьте hour и dtype=int.'
new = _pd.DataFrame({'delivery_id': ['N1', 'N2'], 'created': _pd.to_datetime(['2026-12-01 08:15', '2026-12-01 19:40']), 'shop_id': ['EKB-1', 'PRM-1'], 'courier': ['самокат', 'пеший'], 'distance_km': [2.0, 1.1], 'weather': ['снег', 'туман'], 'items': [3, 1], 'amount': [900, 400], 'promised_min': [30, 30]})
Xn = prepare(new, columns=w.columns)
wn = _ref(new, w.columns)
assert list(Xn.columns) == list(wn.columns), 'prepare(new, columns=...) должна вернуть ровно столбцы обучения в том же порядке.'
assert (Xn.to_numpy() == wn.to_numpy()).all(), f'Для новых заказов значения отличаются от ожидаемых. Сейчас:\n{Xn}'
```

### hint
`pd.to_datetime(df["created"]).dt.hour` работает и со строками, и с датами.

### hint
`df.assign(hour=...)` возвращает новую таблицу и не трогает исходную.

### hint
В конце: `if columns is not None: X = X.reindex(columns=columns, fill_value=0)`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")

def prepare(df, columns=None):
    df = df.assign(hour=pd.to_datetime(df["created"]).dt.hour)
    X = pd.get_dummies(df[["distance_km", "items", "promised_min", "hour", "courier", "weather"]], dtype=int)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0)
    return X

X = prepare(d)
X.head()
```

### explain
Одна функция для обучения и для новых данных исключает целый класс ошибок: забыли добавить `hour`, перепутали порядок столбцов, получили незнакомый флаг. В главе 7 ту же идею воплощает `Pipeline`.
