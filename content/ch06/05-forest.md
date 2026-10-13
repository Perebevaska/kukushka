---
title: Случайный лес
lead: "Одно глубокое дерево запоминает обучающие данные вместе со случайным шумом. Но если вырастить сотню разных деревьев и дать им проголосовать, их ошибки во многом взаимно гасятся. Так устроен случайный лес — одна из самых надёжных моделей для табличных данных. Строим лес сначала руками, потом в sklearn, и честно сравниваем его с правилом аналитика."
files: [deliveries.csv]
recap:
  - "Бутстрэп-выборка — случайный выбор строк с возвращением того же размера: `df.sample(frac=1, replace=True)`. В неё попадает около 63 % разных строк."
  - "Случайный лес = много деревьев, каждое на своей бутстрэп-выборке и со случайным набором признаков на каждом разбиении. Ответ — усреднение (голосование) деревьев."
  - "`RandomForestClassifier(n_estimators=..., max_depth=..., min_samples_leaf=..., random_state=0)`: `n_estimators` — число деревьев, остальное — как у дерева."
  - "Лес переобучается намного меньше одного глубокого дерева: на обучении почти 100 %, но и на тесте заметно выше дерева."
  - "`feature_importances_` у леса — средняя важность по всем деревьям, устойчивее, чем у одного дерева."
  - "Сложная модель должна выиграть у простого правила на нескольких разбиениях, а не на одном. На опозданиях лес лишь чуть лучше правила «пеший — опоздает»."
---

## Одно дерево — ненадёжный эксперт

В уроке «Обучающая и тестовая выборки» мы видели, что дерево без ограничения глубины выучивает обучающие данные почти наизусть, а на тесте проигрывает неглубокому. У глубокого дерева есть и вторая беда — **нестабильность**: немного другие обучающие данные дают заметно другое дерево с другими ответами.

Похоже на прогноз одного эксперта: он может ошибиться из-за личного опыта. Если опросить много экспертов, которые учились на разном опыте, и усреднить их мнения, случайные ошибки отдельных людей во многом гасятся. Модель из многих моделей называют **ансамблем**.

Где взять много разных деревьев, если данные одни? Из урока «Доверительные интервалы» главы 5 мы знаем приём **бутстрэп**: новая выборка того же размера, где строки выбираются **с возвращением**. В pandas это `sample(frac=1, replace=True)`:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
boot = d.sample(frac=1, replace=True, random_state=0)
print(len(d), len(boot))
print(f"разных строк в выборке: {boot['delivery_id'].nunique() / len(d):.1%}")
boot["delivery_id"].value_counts().head(3)
```

Строк столько же, но часть доставок попала несколько раз, а примерно треть — ни разу. Каждая бутстрэп-выборка — немного другой «опыт», и дерево на ней вырастет немного другим.

::: predict
```python static
import pandas as pd
s = pd.Series(range(1000))
b = s.sample(frac=1, replace=True, random_state=1)
print(len(b), b.nunique() < 1000)
```

- `1000 False`
- [x] `1000 True`
- `632 True`

Почему: размер бутстрэп-выборки всегда равен исходному — `frac=1`. Но при выборе с возвращением повторы почти неизбежны, поэтому разных значений меньше тысячи (обычно около 632).
:::

{{practice: boot}}

## Пять деревьев и голосование

Соберём крошечный ансамбль руками: пять глубоких деревьев, каждое на своей бутстрэп-выборке из обучающей части. Ответ ансамбля — то, за что проголосовало большинство.

```python
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

votes = []
for i in range(5):
    Xb = X_train.sample(frac=1, replace=True, random_state=i)
    tree = DecisionTreeClassifier(random_state=0).fit(Xb, y_train.loc[Xb.index])
    votes.append(tree.predict(X_test))
    print(f"дерево {i}: {tree.score(X_test, y_test):.3f}")

majority = np.mean(votes, axis=0) > 0.5
print(f"голосование: {(majority == y_test).mean():.3f}")
```

`y_train.loc[Xb.index]` — ответы для строк бутстрэп-выборки: индекс у повторённых строк повторяется, и `loc` выдаст ответ столько же раз. `np.mean(votes, axis=0)` — доля деревьев, сказавших «опоздает», по каждой доставке.

Каждое дерево по отдельности угадывает 81–85 % тестовых доставок, а их голосование — около 87 %. Деревья ошибаются на разных доставках, и большинство часто оказывается правым там, где отдельное дерево ошиблось.

### Разберём вместе: когда голосование помогает

Три дерева, пять доставок. Каждое дерево право в 4 случаях из 5 — 80 %.

| доставка | правда | дерево 1 | дерево 2 | дерево 3 | большинство |
|---|---|---|---|---|---|
| a | опоздала | ✓ | ✓ | ✗ | ✓ |
| b | вовремя | ✓ | ✗ | ✓ | ✓ |
| c | опоздала | ✗ | ✓ | ✓ | ✓ |
| d | вовремя | ✓ | ✓ | ✓ | ✓ |
| e | вовремя | ✓ | ✓ | ✓ | ✓ |

Деревья ошибаются **на разных** доставках, и на каждой двое правых перевешивают одного неправого: голосование право в 5 из 5.

Теперь пусть все три дерева ошибаются на одной и той же доставке a. Большинство тоже ошибётся на a — и останется 80 %. Голосование ничего не дало.

Что получилось: ансамбль сильнее отдельных моделей ровно настолько, насколько различаются их ошибки. Поэтому лес нарочно делает деревья разными — свой бутстрэп и случайные признаки для каждого вопроса. Копии одного дерева, сколько их ни бери, голосуют одинаково.

::: figure vote-errors
Тот же разбор таблицами. Слева деревья ошибаются на разных доставках, и большинство право везде. Справа все трое ошибаются на доставке a — и голосование повторяет их ошибку.
:::

::: quiz
Почему лес из 100 деревьев обычно точнее на тесте, чем одно глубокое дерево?

- [x] Деревья учатся на разных бутстрэп-выборках и ошибаются по-разному, а голосование гасит случайные ошибки
  > Одно глубокое дерево запоминает шум своей выборки. У сотни деревьев шум разный, а общая закономерность одна.
- [ ] Каждое дерево в лесу точнее одного глубокого
  > Наоборот: отдельные деревья леса часто хуже. Выигрыш — от усреднения.
- [ ] Лес видит больше данных
  > Данные те же. Бутстрэп лишь по-разному выбирает из них строки — с повторами.
- [ ] Лес не может переобучиться
  > Может, но голосование заметно снижает разрыв между обучением и тестом.
:::

{{practice: vote}}

## Случайный лес в sklearn

**Случайный лес** (random forest) добавляет к этой идее вторую случайность: на каждом разбиении дерево выбирает лучший вопрос не из всех признаков, а из случайного подмножества (по умолчанию — из √(число признаков), у нас 4 из 17). Так деревья становятся ещё разнообразнее: даже самый сильный признак `courier_пеший` доступен не на каждом шаге, и деревья учатся использовать остальные.

::: figure forest-bagging
Схема случайного леса на восьми условных строках: у каждого дерева своя бутстрэп-выборка (повторы — жёлтые, часть строк не попала) и свой случайный набор признаков на каждом вопросе. Ответ леса — среднее вероятностей деревьев.
:::

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
tree = DecisionTreeClassifier(random_state=0).fit(X_train, y_train)
print(f"дерево: обучение {tree.score(X_train, y_train):.3f}, тест {tree.score(X_test, y_test):.3f}")
print(f"лес:    обучение {forest.score(X_train, y_train):.3f}, тест {forest.score(X_test, y_test):.3f}")
```

Интерфейс тот же, что у дерева: `fit`, `predict`, `score`, `predict_proba`. Главные настройки:

- `n_estimators` — число деревьев. Больше — стабильнее, но дольше. В браузере держим 50–100;
- `max_depth`, `min_samples_leaf` — ограничения для **каждого** дерева, как в уроке «Решающее дерево изнутри»;
- `max_features` — сколько признаков пробовать на каждом вопросе; по умолчанию √(число признаков), у нас √17 ≈ 4;
- `random_state` — фиксирует и бутстрэп, и выбор признаков, чтобы результат повторялся.

Обе модели почти без ошибок на обучении — каждое дерево леса тоже глубокое. Но на тесте лес выигрывает у одного дерева около 5 п.п.: переобучение отдельных деревьев усреднилось.

`predict_proba` у леса — среднее вероятностей всех деревьев. Класс выбирается по этому среднему, а не простым подсчётом голосов, поэтому результат может отличаться от голосования «большинством»:

::: predict
```python static
p = [0.9, 0.4, 0.4]          # вероятность опоздания у трёх деревьев
print(sum(x > 0.5 for x in p), round(sum(p) / len(p), 2))
```

- `2 0.57`
- [x] `1 0.57`
- `1 0.43`

Почему: «за опоздание» только одно дерево из трёх, большинство говорит «вовремя». Но среднее вероятностей 0.57 > 0.5, и лес sklearn ответит «опоздает»: уверенность первого дерева перевесила сомнения двух других.
:::

::: figure proba-avg
Тот же пример схемой: по голосам большинство за «вовремя», а лес sklearn усредняет вероятности — и 0.57 даёт ответ «опоздает».
:::

{{practice: p-forest, first-forest, gap, avg-proba}}

## Сколько деревьев и какой глубины

Посмотрим, как качество на тесте зависит от числа деревьев:

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

sizes = [1, 5, 10, 25, 50, 100]
accs = [RandomForestClassifier(n_estimators=n, random_state=0).fit(X_train, y_train).score(X_test, y_test) for n in sizes]

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(sizes, accs, marker="o")
ax.set_xscale("log")
ax.set_xlabel("число деревьев")
ax.set_ylabel("accuracy на тесте")
ax.set_title("Больше деревьев — стабильнее лес")
plt.show()
```

Лес из одного дерева — просто дерево на бутстрэп-выборке. Первые десятки деревьев дают основной прирост, дальше кривая выходит на плато. Лишние деревья почти никогда не вредят качеству — только тратят время.

Ограничения глубины дереву помогали сильно, а лесу — мало: усреднение уже сделало основную работу.

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

for leaf in [1, 5, 20]:
    f = RandomForestClassifier(n_estimators=50, min_samples_leaf=leaf, random_state=0).fit(X_train, y_train)
    print(f"min_samples_leaf={leaf:>2}: обучение {f.score(X_train, y_train):.3f}, тест {f.score(X_test, y_test):.3f}")
```

С ростом `min_samples_leaf` разрыв между обучением и тестом сокращается, а тест держится около 90 %. Ограничения у леса полезны другим: модель становится меньше и быстрее, а её вероятности — осторожнее.

::: quiz
Что обычно происходит, если увеличить число деревьев в лесу с 50 до 500?

- [x] Качество на тесте почти не меняется, а обучение идёт заметно дольше: кривая уже вышла на плато
  > Основной прирост дают первые десятки деревьев. Дальше голосование почти не меняется — добавляются лишь вычисления.
- [ ] Лес сильно переобучится: больше деревьев — сложнее модель
  > Новые деревья усредняются с остальными, а не углубляют модель. Лишние деревья почти никогда не вредят качеству.
- [ ] Качество заметно вырастет: каждое новое дерево исправляет ошибки предыдущих
  > Деревья леса строятся независимо и друг друга не исправляют. После плато новые деревья лишь повторяют голоса уже имеющихся.
- [ ] Каждое дерево станет глубже и точнее
  > Глубину задают `max_depth` и `min_samples_leaf`. Число деревьев на устройство отдельного дерева не влияет.
:::

{{practice: n-trees}}

## Что важно для леса

`feature_importances_` у леса — средняя важность признака по всем деревьям. Она устойчивее, чем у одного дерева: случайность отдельных разбиений усредняется.

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

forest = RandomForestClassifier(n_estimators=50, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
imp = pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False)
imp.head(6).round(3)
```

Первым ожидаемо идёт `courier_пеший`, за ним расстояние. Обратите внимание: важность «размазана» по флагам курьера — `courier_вело` и `courier_авто` несут почти ту же информацию, что `courier_пеший`, и в тех деревьях, где флаг пешего не попал в случайный набор, его роль играют они.

::: deep Почему у глубокого леса первым выходит расстояние
Уберите `min_samples_leaf=5` — и на первое место выйдет `distance_km`: у числового признака много порогов, и глубокие деревья набирают ему важность на шуме в крошечных листьях, а флаг можно разрезать только один раз. Смотрите на важность при ограниченной глубине или листе; более надёжный способ — в главе 7.
:::

{{practice: importance}}

## Честное сравнение с правилом

Лес на тесте — около 90 %. Правило «пеший — опоздает» на том же тесте — тоже около 90 %. Одного разбиения мало, чтобы судить, кто лучше: из урока «Обучающая и тестовая выборки» мы знаем, что оценка зависит от того, какие доставки попали в тест. Повторим сравнение на нескольких разбиениях:

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)

rows = []
for seed in range(5):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
    rule = X_test["courier_пеший"] == 1
    rows.append({"разбиение": seed, "лес": forest.score(X_test, y_test), "правило": (rule == y_test).mean()})

cmp = pd.DataFrame(rows).set_index("разбиение")
cmp["разница, п.п."] = (cmp["лес"] - cmp["правило"]) * 100
print(cmp.round(3))
print(f"в среднем лес лучше на {cmp['разница, п.п.'].mean():.1f} п.п.")
```

Лес выигрывает на каждом разбиении, но немного — в среднем около 1.5 п.п. Почему так мало? В этих данных одна причина опозданий (пеший курьер) объясняет почти всё. Правило аналитика её уже нашло, а остальные признаки — погода, час, число позиций — добавляют лишь немного. Модели некуда расти.

::: note Когда лес действительно нужен
Машинное обучение сильно выигрывает у ручных правил там, где причин много и они переплетаются: «пеший + снег + час пик + большой заказ». Такие задачи будут дальше: предсказание минут доставки (урок «Регрессия: сколько минут») и проект с оттоком гостей (урок «Проект: кто из гостей уйдёт»). А в задачах вроде нашей честный вывод для бизнеса звучит так: «главный фактор — пеший курьер; модель подтверждает правило и уточняет его на несколько процентов».
:::

::: warn Типичные ошибки
- **Ждать чуда от числа деревьев.** После нескольких десятков деревьев качество почти не растёт; время обучения — растёт.
- **Сравнивать на одном разбиении.** Разница в 1 п.п. между лесом и правилом может быть случайностью разбиения — проверяйте на нескольких.
- **Читать важность как причину.** Важность показывает, на какие признаки опирался лес, а не что вызывает опоздания.
- **`random_state` только у разбиения.** У леса своя случайность; без `random_state=0` в модели результат будет «гулять».
:::

{{practice: vs-rule, disagree}}

## Практика

## task: boot | Бутстрэп-выборка | warmup

Сделайте из `ok` бутстрэп-выборку `boot` (`random_state=0`) и сохраните в `share_unique` долю разных доставок (`delivery_id`) в ней от числа строк `ok` (3 знака).

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
b = ok.sample(frac=1, replace=True, random_state=0)
boot = need('boot', _pd.DataFrame)
assert len(boot) == len(ok), f'В boot {len(boot)} строк, а должно быть столько же, сколько в ok ({len(ok)}): frac=1.'
assert boot['delivery_id'].nunique() < len(ok), 'В boot нет повторов — выбор должен быть с возвращением (replace=True).'
w = round(b['delivery_id'].nunique() / len(ok), 3)
assert close(need('share_unique'), w), f'share_unique = {need("share_unique")}, а ожидалось {w}. Проверьте random_state=0 и что делите на len(ok).'
```

### hint
`ok.sample(frac=1, replace=True, random_state=0)`; разных значений — `.nunique()`.

### hint
Выборка с возвращением того же размера повторяет одни строки и пропускает другие. Поэтому разных доставок в ней меньше, чем строк: ожидайте долю около 0.63. Это известное свойство бутстрэпа — примерно треть строк в каждую выборку не попадает.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
boot = ok.sample(frac=1, replace=True, random_state=0)
share_unique = round(boot["delivery_id"].nunique() / len(ok), 3)
```

### explain
Около 63 % — и это почти не зависит от размера данных: доля строк, не попавших в выборку ни разу, стремится к 1/e ≈ 37 %.

## task: p-forest | Первый лес | warmup

Соберите программу: подготовить признаки, разбить данные, обучить лес из 50 деревьев и вывести долю правильных ответов на тесте (3 знака).

### parsons
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "courier", "weather"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
print(round(forest.score(X_test, y_test), 3))
```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'courier', 'weather']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
w = str(round(_RF(n_estimators=50, random_state=0).fit(a, ya).score(b, yb), 3))
assert _lines == [w], f'Программа вывела {_lines}, а ожидалось [{w!r}]. Лес обучается на обучающей части, оценивается на тестовой.'
```

### hint
Тот же порядок, что с деревом: данные → признаки → разбиение → обучение → оценка.

## task: first-forest | Лес на всех признаках | warmup

Обучите `RandomForestClassifier(n_estimators=50, random_state=0)` на `X_train` и сохраните модель в `forest`, а долю правильных ответов на тесте — в `acc_test` (3 знака).

### setup
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
```

### starter
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
f = need('forest')
assert isinstance(f, _RF), 'forest должен быть RandomForestClassifier.'
assert f.n_estimators == 50 and f.random_state == 0, f'У леса n_estimators={f.n_estimators}, random_state={f.random_state}, а нужно 50 и 0.'
assert hasattr(f, 'estimators_'), 'Лес создан, но не обучен — вызовите fit.'
w = round(_RF(n_estimators=50, random_state=0).fit(a, ya).score(b, yb), 3)
assert close(need('acc_test'), w), f'acc_test = {need("acc_test")}, а ожидалось {w}. Обучение — на X_train, оценка — на X_test.'
```

### hint
`forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)`, затем `forest.score(X_test, y_test)`.

### hint
`X` — флаги для `courier`, `weather` и `shop_id` плюс числовые признаки, разбиение 0.25 / 42. Лесу не нужно масштабирование и подбор порога: обучение — `.fit(X_train, y_train)`, качество — `.score(X_test, y_test)`.

### solution
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
acc_test = round(forest.score(X_test, y_test), 3)
```

## task: gap | Кто переобучился сильнее | base

Обучите на одних и тех же данных дерево без ограничения глубины (`DecisionTreeClassifier(random_state=0)`) и лес `RandomForestClassifier(n_estimators=50, random_state=0)`. Для каждой модели посчитайте разрыв «обучение − тест» в процентных пунктах (1 знак): `gap_tree` и `gap_forest`. В `winner` сохраните `"лес"` или `"дерево"` — у кого выше доля правильных ответов на тесте.

### setup
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
```

### starter
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
t = _T(random_state=0).fit(a, ya)
f = _RF(n_estimators=50, random_state=0).fit(a, ya)
gt = round((t.score(a, ya) - t.score(b, yb)) * 100, 1)
gf = round((f.score(a, ya) - f.score(b, yb)) * 100, 1)
assert close(need('gap_tree'), gt), f'gap_tree = {need("gap_tree")}, а ожидалось {gt}. Это (accuracy на обучении − accuracy на тесте) × 100.'
assert close(need('gap_forest'), gf), f'gap_forest = {need("gap_forest")}, а ожидалось {gf}.'
assert need('winner') == ('лес' if f.score(b, yb) > t.score(b, yb) else 'дерево'), f'winner = {need("winner")!r}. Сравните accuracy на тесте.'
```

### hint
`model.score(X_train, y_train)` и `model.score(X_test, y_test)` — для обеих моделей.

### hint
Разрыв — `(доля на обучении − доля на тесте) * 100`, округление в конце. Дерево без ограничения глубины почти идеально запоминает обучение, поэтому его разрыв будет большим. Победителя выбирайте по тесту, а не по обучению.

### solution
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

tree = DecisionTreeClassifier(random_state=0).fit(X_train, y_train)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
gap_tree = round((tree.score(X_train, y_train) - tree.score(X_test, y_test)) * 100, 1)
gap_forest = round((forest.score(X_train, y_train) - forest.score(X_test, y_test)) * 100, 1)
winner = "лес" if forest.score(X_test, y_test) > tree.score(X_test, y_test) else "дерево"
```

### explain
На обучении обе модели почти безошибочны, но у дерева разрыв около 16 п.п., у леса — около 10. Лес не перестаёт подгоняться под обучающие данные, но его ошибки на новых данных заметно меньше.

## task: n-trees | Кривая числа деревьев | base

Для числа деревьев из списка `sizes` обучите `RandomForestClassifier(n_estimators=n, random_state=0)` и сохраните доли правильных ответов на тесте в список `accs` (без округления). Нарисуйте линию: по оси X — `sizes`, по Y — `accs`, подпишите ось X `"число деревьев"`.

### setup
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
sizes = [1, 3, 10, 30, 60]
```

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
w = [_RF(n_estimators=n, random_state=0).fit(a, ya).score(b, yb) for n in [1, 3, 10, 30, 60]]
got = list(need('accs'))
assert len(got) == 5, f'В accs {len(got)} значений, а размеров леса пять.'
assert all(close(g, v, 1e-6) for g, v in zip(got, w)), f'accs = {[round(float(g), 3) for g in got]}, а ожидалось {[round(v, 3) for v in w]}. Проверьте n_estimators=n и random_state=0.'
ax = ax_of()
assert ax.lines, 'На графике нет линии — нужен ax.plot(sizes, accs).'
ln = ax.lines[0]
assert list(ln.get_xdata()) == [1, 3, 10, 30, 60] and all(close(g, v, 1e-6) for g, v in zip(ln.get_ydata(), w)), 'Линия должна идти по точкам (sizes, accs).'
assert ax.get_xlabel() == 'число деревьев', f'Подпись оси X: {ax.get_xlabel()!r}, а нужна "число деревьев".'
```

### hint
Цикл `for n in sizes:` с `accs.append(...)` или список `[... for n in sizes]`.

### hint
`fig, ax = plt.subplots()`, `ax.plot(sizes, accs, marker="o")`, `ax.set_xlabel("число деревьев")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
sizes = [1, 3, 10, 30, 60]
accs = [RandomForestClassifier(n_estimators=n, random_state=0).fit(X_train, y_train).score(X_test, y_test) for n in sizes]

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(sizes, accs, marker="o")
ax.set_xlabel("число деревьев")
ax.set_ylabel("accuracy на тесте")
plt.show()
```

### explain
Одно дерево — 0.824, три — 0.859, десять — 0.885, тридцать — 0.889, шестьдесят — 0.898. Первые десять деревьев дают почти весь выигрыш, дальше кривая выходит на «полку». Лишние деревья лес не портят (переобучения от их числа нет), но и не улучшают — только замедляют.

## task: importance | Главные признаки леса | base

Обучите `RandomForestClassifier(n_estimators=50, min_samples_leaf=5, random_state=0)` на `X_train`. Сохраните `imp` — Series важностей признаков (индекс — названия столбцов), отсортированную по убыванию, и `top3` — список названий трёх самых важных признаков. В `courier_share` — суммарную важность трёх флагов курьера (3 знака).

### setup
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
```

### starter
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
w = _pd.Series(_RF(n_estimators=50, min_samples_leaf=5, random_state=0).fit(a, ya).feature_importances_, index=X.columns).sort_values(ascending=False)
imp = need('imp', _pd.Series)
assert set(imp.index) == set(X.columns), 'Индекс imp — названия признаков: pd.Series(..., index=X.columns).'
assert all(close(imp[k], w[k], 1e-9) for k in w.index), 'Значения важностей не совпали с ожидаемыми — проверьте настройки леса (n_estimators=50, min_samples_leaf=5, random_state=0).'
assert list(imp.index) == list(w.index), 'Важности верные, но imp не отсортирована по убыванию.'
assert list(need('top3', list)) == list(w.index[:3]), f'top3 = {need("top3")}. Три первых названия отсортированной imp.'
cs = round(w[['courier_авто', 'courier_вело', 'courier_пеший']].sum(), 3)
assert close(need('courier_share'), cs), f'courier_share = {need("courier_share")}, а ожидалось {cs}.'
```

### hint
`pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False)`; три первых названия — `list(imp.index[:3])`.

### hint
Флаги курьера можно выбрать по списку названий: `imp[["courier_авто", "courier_вело", "courier_пеший"]].sum()`.

### solution
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=50, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
imp = pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False)
top3 = list(imp.index[:3])
courier_share = round(imp[["courier_авто", "courier_вело", "courier_пеший"]].sum(), 3)
```

### explain
Вместе флаги курьера дают около половины всей важности: тип курьера — главный фактор, просто лес «раздал» его по трём столбцам.

## task: vote | Ансамбль своими руками | base

Повторите ручной ансамбль из теории, но из 7 деревьев: дерево `i` (от 0 до 6) — `DecisionTreeClassifier(random_state=0)` на бутстрэп-выборке `X_train.sample(frac=1, replace=True, random_state=i)`. Сохраните:

- `tree_accs` — список долей правильных ответов каждого дерева на тесте;
- `acc_vote` — долю правильных ответов голосования большинством (3 знака);
- `acc_forest7` — долю правильных ответов настоящего леса из тех же семи деревьев: `RandomForestClassifier(n_estimators=7, random_state=0)` (3 знака).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
votes, accs = [], []
for i in range(7):
    s = a.sample(frac=1, replace=True, random_state=i)
    t = _T(random_state=0).fit(s, ya.loc[s.index])
    votes.append(t.predict(b)); accs.append(t.score(b, yb))
got = list(need('tree_accs'))
assert len(got) == 7, f'В tree_accs {len(got)} значений, а деревьев семь.'
assert all(close(g, v, 1e-6) for g, v in zip(got, accs)), f'tree_accs = {[round(float(g), 3) for g in got]}. Дерево i — на выборке с random_state=i, ответы — y_train.loc[индекс выборки].'
w = round(((_np.mean(votes, axis=0) > 0.5) == yb).mean(), 3)
assert close(need('acc_vote'), w), f'acc_vote = {need("acc_vote")}, а ожидалось {w}. Голос большинства: доля «опоздает» среди деревьев > 0.5.'
from sklearn.ensemble import RandomForestClassifier as _RF
f7 = round(_RF(n_estimators=7, random_state=0).fit(a, ya).score(b, yb), 3)
assert close(need('acc_forest7'), f7), f'acc_forest7 = {need("acc_forest7")}, а ожидалось {f7}. RandomForestClassifier(n_estimators=7, random_state=0), обучение на X_train.'
```

### hint
Код из раздела «Пять деревьев и голосование» почти подходит — поменяйте число деревьев и сохраняйте доли в список.

### hint
Бутстрэп по `X_train` перемешивает индексы, поэтому ответы для дерева берите по тем же индексам: `y_train.loc[Xb.index]`. Голоса — список массивов True/False: `np.mean(votes, axis=0) > 0.5` даёт решение большинства для каждой доставки. Деревьев 7, нечётное число, поэтому ничьих не бывает.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

votes, tree_accs = [], []
for i in range(7):
    Xb = X_train.sample(frac=1, replace=True, random_state=i)
    tree = DecisionTreeClassifier(random_state=0).fit(Xb, y_train.loc[Xb.index])
    votes.append(tree.predict(X_test))
    tree_accs.append(tree.score(X_test, y_test))
acc_vote = round(((np.mean(votes, axis=0) > 0.5) == y_test).mean(), 3)

from sklearn.ensemble import RandomForestClassifier
acc_forest7 = round(RandomForestClassifier(n_estimators=7, random_state=0).fit(X_train, y_train).score(X_test, y_test), 3)
```

### explain
Деревья по отдельности дают 0.81–0.85, голосование — 0.870: лучше любого из них. Настоящий лес из тех же семи деревьев — 0.874: чуть лучше, хотя деревьев столько же. Разница в двух вещах: лес на каждом вопросе выбирает из случайных признаков (деревья разнообразнее) и усредняет вероятности, а не голоса. Лес — это не просто голосование, а голосование разных и уверенных по-разному экспертов.

## task: vs-rule | Кто выигрывает стабильно | plus

В теории лес обыгрывал правило «пеший — опоздает» на каждом из пяти разбиений. А простое дерево? Сравните три модели на разбиениях с `random_state` от 0 до 4 (`test_size=0.25`): лес `RandomForestClassifier(n_estimators=50, random_state=0)`, дерево `DecisionTreeClassifier(max_depth=3, random_state=0)` и правило.

Сохраните таблицу `cmp` (индекс — номер разбиения 0–4) со столбцами `forest`, `tree` и `rule` — доли правильных ответов на тесте, а также `forest_always` и `tree_always` — `True`, если модель обыграла правило на **всех** пяти разбиениях.

### setup
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
```

### starter
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
fr, tr, rr = [], [], []
for s in range(5):
    a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=s)
    fr.append(_RF(n_estimators=50, random_state=0).fit(a, ya).score(b, yb))
    tr.append(_T(max_depth=3, random_state=0).fit(a, ya).score(b, yb))
    rr.append(((b['courier_пеший'] == 1) == yb).mean())
cmp = need('cmp', _pd.DataFrame)
assert {'forest', 'tree', 'rule'} <= set(cmp.columns), f'Столбцы cmp: {list(cmp.columns)}, а нужны forest, tree и rule.'
assert len(cmp) == 5 and [int(i) for i in cmp.index] == [0, 1, 2, 3, 4], f'Индекс cmp: {list(cmp.index)}, а нужны разбиения 0–4.'
assert all(close(g, v, 1e-6) for g, v in zip(cmp['rule'], rr)), f'Столбец rule не совпал: {list(cmp["rule"].round(3))}. Правило: флаг courier_пеший == 1, сравнение с y_test.'
assert all(close(g, v, 1e-6) for g, v in zip(cmp['forest'], fr)), f'Столбец forest не совпал: {list(cmp["forest"].round(3))}. Новый лес на каждом разбиении.'
assert all(close(g, v, 1e-6) for g, v in zip(cmp['tree'], tr)), f'Столбец tree не совпал: {list(cmp["tree"].round(3))}. Дерево max_depth=3, random_state=0 на каждом разбиении.'
assert need('forest_always') == all(f > r for f, r in zip(fr, rr)), 'forest_always — лес лучше правила на всех пяти разбиениях?'
assert need('tree_always') == all(t > r for t, r in zip(tr, rr)), 'tree_always — дерево лучше правила на всех пяти разбиениях?'
```

### hint
В цикле по `seed` соберите словари `{"forest": ..., "tree": ..., "rule": ...}` в список, затем `pd.DataFrame(rows)` — индекс 0–4 получится сам. Правило на тесте: `((X_test["courier_пеший"] == 1) == y_test).mean()`.

### hint
«На всех разбиениях»: `bool((cmp["forest"] > cmp["rule"]).all())`.

### solution
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)

rows = []
for seed in range(5):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
    tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
    rule = X_test["courier_пеший"] == 1
    rows.append({"forest": forest.score(X_test, y_test), "tree": tree.score(X_test, y_test), "rule": (rule == y_test).mean()})
cmp = pd.DataFrame(rows)
forest_always = bool((cmp["forest"] > cmp["rule"]).all())
tree_always = bool((cmp["tree"] > cmp["rule"]).all())
```

### explain
Лес обыгрывает правило на всех пяти разбиениях, хоть и на 1–2 п.п. Дерево глубины 3 — нет: на двух разбиениях лучше правила, на трёх хуже. Выигрыш дерева на одном разбиении — случайность, а выигрыш леса — устойчивый, хоть и маленький. Так и проверяют «лучше ли модель»: не на одном тесте, а на нескольких — в уроке «Честное сравнение моделей» это станет кросс-валидацией.

## task: disagree | Где лес спорит с правилом | plus

Лес (`n_estimators=50, random_state=0`, разбиение 0.25 / 42) и правило «пеший — опоздает» отвечают одинаково на большинстве тестовых доставок. Найдите доставки, где ответы **различаются**, и сохраните:

- `n_disagree` — сколько таких доставок в тесте;
- `forest_right` — на скольких из них прав лес;
- `walk_share` — доля пеших среди них (3 знака).

### setup
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
```

### starter
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test, forest

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
p = _RF(n_estimators=50, random_state=0).fit(a, ya).predict(b)
r = (b['courier_пеший'] == 1).to_numpy()
m = p != r
assert need('n_disagree') == m.sum(), f'n_disagree = {need("n_disagree")}, а ожидалось {m.sum()}. Сравните предсказания леса с маской правила.'
assert need('forest_right') == (p[m] == yb.to_numpy()[m]).sum(), f'forest_right = {need("forest_right")}. Среди расхождений посчитайте, где предсказание леса совпало с y_test.'
assert close(need('walk_share'), round(r[m].mean(), 3)), f'walk_share = {need("walk_share")}. Доля пеших среди спорных доставок.'
```

### hint
`pred = forest.predict(X_test)`, `rule = (X_test["courier_пеший"] == 1).to_numpy()`, маска расхождений — `pred != rule`.

### hint
Внутри маски `m`: `(pred[m] == y_test.to_numpy()[m]).sum()` и `rule[m].mean()`.

### solution
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)

pred = forest.predict(X_test)
rule = (X_test["courier_пеший"] == 1).to_numpy()
m = pred != rule
n_disagree = m.sum()
forest_right = (pred[m] == y_test.to_numpy()[m]).sum()
walk_share = round(rule[m].mean(), 3)
```

### explain
Спорных доставок — всего около 30 из 461, и лес прав примерно в половине из них: на спорных доставках он угадывает как монетка. Весь выигрыш леса над правилом — внутри этих нескольких десятков строк: где-то лес замечает пешую доставку, которая успеет (короткое расстояние, мало позиций), где-то — рискованную поездку на велосипеде.

## task: avg-proba | Лес — это среднее деревьев | star

Убедитесь, что вероятности леса — среднее вероятностей его деревьев. Обученные деревья леса лежат в списке `forest.estimators_`. Сохраните:

- `manual` — массив вероятности опоздания для `X_test`, усреднённый по всем деревьям леса (столбец 1 из `predict_proba` каждого дерева);
- `max_diff` — наибольшее абсолютное расхождение `manual` с `forest.predict_proba(X_test)[:, 1]`.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=30, random_state=0).fit(X_train, y_train)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
# данные подготовлены, как в теории: d, ok, y, X, X_train, X_test, y_train, y_test, forest

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.model_selection import train_test_split as _tts
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, ya, yb = _tts(X, y, test_size=0.25, random_state=42)
f = _RF(n_estimators=30, random_state=0).fit(a, ya)
w = _np.mean([t.predict_proba(b.to_numpy())[:, 1] for t in f.estimators_], axis=0)
man = _np.asarray(need('manual'), dtype=float)
assert man.shape == (len(b),), f'manual должен быть одномерным массивом длины {len(b)} (по доставке теста), а сейчас форма {man.shape}.'
assert _np.allclose(man, w), 'manual не совпал со средним вероятностей деревьев. Нужен столбец 1 predict_proba каждого дерева и среднее по деревьям (axis=0).'
md = float(_np.abs(w - f.predict_proba(b)[:, 1]).max())
assert close(need('max_diff'), md, 1e-9), f'max_diff = {need("max_diff")}. Сравните manual с forest.predict_proba(X_test)[:, 1].'
```

### hint
`for tree in forest.estimators_:` — обычные `DecisionTreeClassifier`. Они обучены на массиве без имён столбцов, поэтому передавайте им `X_test.to_numpy()`, чтобы не было предупреждения.

### hint
Список из 30 массивов → `np.mean(список, axis=0)` — среднее по деревьям для каждой доставки.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
forest = RandomForestClassifier(n_estimators=30, random_state=0).fit(X_train, y_train)

probs = [tree.predict_proba(X_test.to_numpy())[:, 1] for tree in forest.estimators_]
manual = np.mean(probs, axis=0)
max_diff = float(np.abs(manual - forest.predict_proba(X_test)[:, 1]).max())
```

### explain
Расхождение — ноль (в худшем случае — ошибки округления порядка 1e-16): лес действительно просто усредняет деревья. Поэтому вероятности леса принимают много разных значений, а у одного глубокого дерева — почти только 0 и 1. Это пригодится в уроке «Логистическая регрессия и вероятности», когда будем ранжировать доставки по риску.
