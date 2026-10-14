---
title: Матрица ошибок
lead: "Лес для оттока — такой же, как в проекте главы 6, — прав почти в 89 % случаев. Звучит отлично — пока не выясняется, что модель «никто не уйдёт» права в 78 %. Учимся раскладывать ответы модели на четыре исхода, считать их одной функцией и понимать, какие ошибки модель делает и сколько они стоят «Зерну»."
files: [guests_churn.csv]
recap:
  - "При дисбалансе классов accuracy обманывает: модель «никто не уйдёт» на наших гостях права в 78 % случаев и не находит ни одного уходящего."
  - "`DummyClassifier(strategy=\"most_frequent\")` — базовая модель, которая всегда отвечает самым частым классом. Любая модель должна быть заметно лучше неё."
  - "Четыре исхода: TP — бонус уходящему, FP — лишний бонус оставшемуся, FN — пропустили уходящего, TN — верно не тронули оставшегося."
  - "`confusion_matrix(y_true, y_pred)` — таблица [[TN, FP], [FN, TP]]: строки — факт, столбцы — прогноз; `.ravel()` раскладывает её в `tn, fp, fn, tp`."
  - "Доли ошибок по типам: FN / (FN + TP) — какую долю уходящих пропустили, FP / (FP + TN) — какой доле оставшихся дали лишний бонус. `normalize=\"true\"` считает их сразу."
  - "Ошибки стоят по-разному: лишний бонус дешевле потерянного гостя, поэтому модели сравнивают по матрице и по деньгам, а не только по accuracy."
---

## Когда 89 % — это мало

В проекте главы 6 мы строили модель оттока: кто из гостей с картой лояльности не придёт в ближайшие 60 дней. Здесь возьмём тот же лес, но с настройками по умолчанию — без `min_samples_leaf=3`. Поэтому числа чуть другие: в проекте лес был прав в 90 % случаев, здесь — почти в 89 %. Для выводов урока это не важно. Напомним подготовку: убираем `guest_id`, ответ `churned` и утечку `card_blocked`, текстовые столбцы — через `get_dummies`, пустой средний чек — это 0 визитов, значит 0.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

forest = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
print(f"лес: {forest.score(X_test, y_test):.3f}")
print(f"доля ушедших в тесте: {y_test.mean():.3f}")
```

**Что здесь происходит:**

- `drop(columns=[...])` убирает номер гостя, ответ и утечку; `get_dummies` превращает текстовые столбцы (город, любимая категория) во флаги 0/1.
- `stratify=y` — в тесте та же доля ушедших, что во всех данных; без этого при дисбалансе тест мог бы случайно получиться «лёгким».
- `forest.score(X_test, y_test)` — у классификатора это accuracy: доля совпавших ответов.
- `y_test.mean()` — среднее нулей и единиц, то есть доля ушедших.

Лес прав почти в 89 % случаев. Но уходит только 22 % гостей. Значит, «модель», которая про всех говорит «останется», права в 78 % случаев — и при этом бесполезна: она не найдёт ни одного гостя для акции удержания.

Такую ситуацию называют **дисбалансом классов** (class imbalance): один ответ встречается гораздо чаще другого. Уходят 22 % гостей, мошеннических платежей — доли процента, брака на линии — единицы процентов. При дисбалансе **accuracy** (доля правильных ответов) почти всегда высокая — её «набирают» на частом классе.

::: predict
```python static
y = [1] * 22 + [0] * 78
pred = [0] * 100
print(sum(a == b for a, b in zip(y, pred)) / len(y))
```

- `0.22`
- [x] `0.78`
- `0.0`

Почему: модель «никто не уйдёт» права для всех 78 оставшихся гостей и ошибается только на 22 ушедших. Высокая доля правильных ответов — и ни одного найденного уходящего.
:::

## Базовая модель: DummyClassifier

Чтобы не сравнивать в уме, в sklearn есть готовая «глупая» модель — `DummyClassifier`. Она не смотрит на признаки. С `strategy="most_frequent"` она запоминает при обучении самый частый класс и всегда отвечает им. Это **базовая модель** (baseline): точка отсчёта, от которой меряют пользу настоящей модели.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

dummy = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
print(dummy.predict(X_test)[:10])
print(f"accuracy: {dummy.score(X_test, y_test):.3f}")
```

Интерфейс как у любой модели: `fit`, `predict`, `score`. В главе 6 мы считали такую точку отсчёта руками («доля самого частого класса»), теперь это одна строка — и её удобно ставить в один ряд с другими моделями.

Выходит, лес лучше базовой модели на 11 пунктов accuracy. Много это или мало? По одному числу не понять: неизвестно, на каких гостях лес ошибается — на уходящих или на оставшихся. Для акции удержания это две совершенно разные ошибки.

{{practice: p-dummy, dummy-acc}}

## Четыре исхода

Модель для каждого гостя говорит «уйдёт» (1) или «останется» (0), а через 60 дней мы узнаём правду. Комбинаций четыре. Класс 1 — тот, который мы ищем, его называют **положительным** (positive), класс 0 — **отрицательным** (negative).

| | Модель: останется (0) | Модель: уйдёт (1) |
|---|---|---|
| **Факт: остался (0)** | **TN** — верно не тронули | **FP** — лишний бонус |
| **Факт: ушёл (1)** | **FN** — пропустили уходящего | **TP** — бонус по адресу |

- **TP** (true positive, верно-положительный) — модель сказала «уйдёт», и гость действительно собирался уйти. Бонус потрачен не зря.
- **FP** (false positive, ложноположительный) — «уйдёт», а гость и так бы остался. Бонус потрачен впустую. Это «ложная тревога».
- **FN** (false negative, ложноотрицательный) — «останется», а гость ушёл. Мы его даже не пытались удержать. Это «пропуск».
- **TN** (true negative, верно-отрицательный) — «останется», и гость остался. Ничего не потратили, ничего не потеряли.

Запомнить просто: второе слово (positive / negative) — что сказала модель, первое (true / false) — права ли она.

Посчитать исходы можно обычными масками pandas, как в главе 6:

```python
import pandas as pd

fact = pd.Series([1, 0, 1, 1, 0, 0, 0, 0])
pred = pd.Series([1, 1, 0, 1, 0, 0, 1, 0])
print("TP", ((fact == 1) & (pred == 1)).sum())
print("FP", ((fact == 0) & (pred == 1)).sum())
print("FN", ((fact == 1) & (pred == 0)).sum())
print("TN", ((fact == 0) & (pred == 0)).sum())
```

Руками по восьми гостям: пары (факт, прогноз) — (1,1), (0,1), (1,0), (1,1), (0,0), (0,0), (0,1), (0,0). TP — первая и четвёртая: **2**. FP — вторая и седьмая: **2**. FN — третья: **1**. TN — пятая, шестая, восьмая: **3**. Всего 2 + 2 + 1 + 3 = 8 — каждый гость попал ровно в одну клетку.

Accuracy — это (TP + TN) / все: правильные ответы обоих типов вместе. Именно поэтому она не различает, какие ошибки модель делает.

::: figure confusion
Четыре исхода для задачи об уходе гостей — в том же порядке, что у `confusion_matrix`: строки — как было на самом деле, столбцы — прогноз, сначала 0, потом 1.
:::

::: tip Аналогия
Датчик дыма в кофейне. Сработал при пожаре — TP. Сработал от подгоревшего круассана — FP, ложная тревога: неприятно, но дёшево. Промолчал при пожаре — FN, самая дорогая ошибка. Молчит в обычный день — TN. Датчик, который не срабатывает никогда, прав почти каждый день, но пользы от него ноль — как модель «никто не уйдёт».
:::

::: quiz
Модель сказала про гостя «уйдёт», ему выдали бонус, а он и без бонуса продолжил бы ходить в «Зерно». Какой это исход?

- [x] FP — ложноположительный
  > Модель ответила «положительный класс» (уйдёт) и ошиблась: бонус потрачен впустую. Это ложная тревога.
- [ ] FN — ложноотрицательный
  > FN — пропуск: модель сказала «останется», а гость ушёл. Здесь всё наоборот — модель подняла тревогу.
- [ ] TP — верно-положительный
  > Для TP гость должен был действительно собираться уйти. Этот гость остался бы и так.
- [ ] TN — верно-отрицательный
  > TN — модель сказала «останется» и оказалась права. Здесь модель сказала «уйдёт».
:::

{{practice: count-four}}

## confusion_matrix

Четыре числа сразу считает `confusion_matrix(y_true, y_pred)` из `sklearn.metrics`. Результат называют **матрицей ошибок** (confusion matrix): строки — факт, столбцы — прогноз, классы по порядку 0, 1. Получается:

```text
[[TN, FP],
 [FN, TP]]
```

Порядок легко перепутать, поэтому запомните: **строки — правда, столбцы — модель**; верные ответы — на диагонали. Метод `.ravel()` вытягивает таблицу 2×2 в строку из четырёх чисел — в том же порядке, по строкам.

::: figure cm-ravel
Восемь гостей из примера: каждая пара (факт, прогноз) попадает в одну из четырёх клеток. `confusion_matrix` раскладывает их по строкам «факт» и столбцам «прогноз», а `ravel()` читает матрицу по строкам: TN, FP, FN, TP.
:::

```python
from sklearn.metrics import confusion_matrix

fact = [1, 0, 1, 1, 0, 0, 0, 0]
pred = [1, 1, 0, 1, 0, 0, 1, 0]
cm = confusion_matrix(fact, pred)
print(cm)
tn, fp, fn, tp = cm.ravel()
print(f"TN={tn} FP={fp} FN={fn} TP={tp}")
```

::: predict
```python static
from sklearn.metrics import confusion_matrix
y_true = [1, 1, 1, 0, 0, 0, 0]
y_pred = [1, 0, 0, 0, 0, 0, 1]
print(confusion_matrix(y_true, y_pred).ravel())
```

- `[1 1 2 3]`
- [x] `[3 1 2 1]`
- `[3 2 1 1]`

Почему: порядок `ravel()` — TN, FP, FN, TP. Трёх оставшихся модель назвала оставшимися верно (TN = 3), одному дала ложную тревогу (FP = 1), двух ушедших пропустила (FN = 2), одного нашла (TP = 1).
:::

::: sql
Матрица ошибок — это обычная сводная таблица: `SELECT fact, pred, COUNT(*) FROM t GROUP BY fact, pred`. В pandas то же даёт `pd.crosstab(fact, pred)` из главы 3 — с подписями строк и столбцов, что удобно для отчёта.
:::

{{practice: forest-cm, rule-cm}}

## Матрицы трёх моделей

Теперь посмотрим, как ошибаются базовая модель, правило отдела лояльности «не был больше 45 дней — уходит» из проекта главы 6 и лес.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

preds = {
    "никто не уйдёт": DummyClassifier(strategy="most_frequent").fit(X_train, y_train).predict(X_test),
    "правило 45 дней": (X_test["days_since_last"] > 45).astype(int),
    "лес": RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict(X_test),
}
for name, pred in preds.items():
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    print(f"{name:16} TN={tn} FP={fp} FN={fn} TP={tp}")
```

**Что здесь происходит:**

- `preds` — словарь «название → прогнозы»: так три очень разные модели проходят через один и тот же цикл.
- Правило — не модель sklearn, а маска `days_since_last > 45`; `.astype(int)` превращает True/False в 1/0, чтобы его можно было сравнивать с остальными.
- `confusion_matrix(y_test, pred).ravel()` — сначала факт, потом прогноз. Перепутанный порядок аргументов меняет местами FP и FN.

В тесте 134 ушедших гостя. Что видно:

- **базовая модель** пропускает всех 134 — FN равно числу ушедших;
- **правило 45 дней** почти не ошибается тревогами (около 10 лишних бонусов), зато пропускает больше половины уходящих: гости, которые ещё ходят, но скоро перестанут, под правило не попадают;
- **лес** находит около двух третей уходящих (TP около 90) ценой двух десятков лишних бонусов.

Три модели с accuracy 78 %, 85 % и 89 % ведут себя совсем по-разному, и матрица показывает как.

::: figure cm-three
Матрицы трёх подходов на одном тесте. У базовой модели все 134 уходящих в клетке FN; правило почти не тревожит зря, но пропускает больше половины; лес находит 90 уходящих ценой 23 лишних бонусов.
:::

{{practice: two-trees}}

## Доли ошибок каждого типа

Абсолютные числа зависят от размера теста, поэтому ошибки удобно выражать долями — **внутри своей строки** матрицы:

- **доля пропущенных уходящих** — FN / (FN + TP): из всех, кто ушёл, скольких модель не заметила;
- **доля лишних бонусов** — FP / (FP + TN): из всех, кто остался, скольким модель зря подняла тревогу.

Параметр `normalize="true"` делит каждую строку матрицы на её сумму и выдаёт эти доли сразу:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pred = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict(X_test)

print(confusion_matrix(y_test, pred))
print(confusion_matrix(y_test, pred, normalize="true").round(3))
```

Во второй таблице каждая строка в сумме даёт 1. Правый верхний угол — доля лишних бонусов (около 5 % оставшихся), левый нижний — доля пропущенных уходящих (около трети). Лес почти не тревожит лояльных гостей, но каждого третьего уходящего упускает.

::: figure cm-rows
`normalize="true"` делит каждую строку на её сумму. Пропущенных уходящих 44 — это 7 % всех гостей, но треть ушедших: доля ошибок имеет смысл только внутри своей строки.
:::

::: warn Делить по строкам, а не на всех
Частая ошибка — делить FN на число всех гостей теста: получится «модель пропускает 7 %», что звучит безобидно. Но уходящих всего 22 %, и пропущена из них треть. Доля ошибки считается внутри той группы, к которой она относится.
:::

::: quiz
Уходит 22 % гостей. Модель «никто не уйдёт» даёт accuracy 78 %. Сколько уходящих она находит?

- [x] Ни одного: TP = 0
  > Accuracy высокая только потому, что большинство и так остаётся. Матрица ошибок сразу показывает, что TP = 0.
- [ ] 78 %
  > 78 % — доля верных ответов среди **всех** гостей, а не среди уходящих.
- [ ] 22 %
  > 22 % — доля уходящих в данных. Модель не отметила ни одного из них.
- [ ] Половину, раз accuracy выше 50 %
  > Accuracy не говорит, на каком классе модель права.
:::

{{practice: shares, missed-who}}

## Разберём вместе: одинаковая accuracy — разные деньги

Возьмём 100 гостей, из них 10 уходящих, и две модели.

| | TP | FN | FP | TN | accuracy |
|---|---|---|---|---|---|
| A, «осторожная» | 5 | 5 | 0 | 90 | (5 + 90) / 100 = **0.95** |
| B, «смелая» | 9 | 1 | 6 | 84 | (9 + 84) / 100 = **0.93** |

По accuracy A лучше. Теперь доли ошибок по строкам:

- A пропускает 5 / (5 + 5) = **50 %** уходящих и тревожит 0 / 90 = **0 %** оставшихся;
- B пропускает 1 / 10 = **10 %** уходящих и тревожит 6 / 90 ≈ **7 %** оставшихся.

Посчитаем деньги по одной схеме, которой будем пользоваться всю главу: **бонус платим каждому, кому его отправили** (TP и FP — 300 ₽), а **пропущенный уходящий** (FN) уносит 3 000 ₽ будущей выручки. TN ничего не стоят:

- A: (5 + 0) × 300 + 5 × 3000 = 1 500 + 15 000 = **16 500 ₽** потерь;
- B: (9 + 6) × 300 + 1 × 3000 = 4 500 + 3 000 = **7 500 ₽** потерь.

Что получилось: модель с меньшей accuracy обходится вдвое с лишним дешевле. Accuracy складывает ошибки так, будто они стоят одинаково, а матрица позволяет приписать каждой клетке её цену.

```python
from sklearn.metrics import confusion_matrix
fact = [1] * 10 + [0] * 90
pred_a = [1] * 5 + [0] * 5 + [0] * 90
pred_b = [1] * 9 + [0] * 1 + [1] * 6 + [0] * 84
for name, pred in [("A", pred_a), ("B", pred_b)]:
    tn, fp, fn, tp = confusion_matrix(fact, pred).ravel()
    print(name, "accuracy", (tp + tn) / 100, "| потери", (tp + fp) * 300 + fn * 3000)
```

::: note Цена ошибок
Лишний бонус стоит его себестоимость — скажем, 300 ₽. Ушедший гость уносит выручку за месяцы вперёд — тысячи рублей. Если FN дороже FP в несколько раз, модель с большей accuracy может обходиться «Зерну» дороже модели, которая чаще ошибается, но реже пропускает уходящих. Матрица ошибок — первый шаг к такому расчёту: умножаем каждую клетку на её цену. Как сдвигать баланс между FP и FN с помощью порога вероятности — в уроке «Порог, PR- и ROC-кривые».
:::

::: warn Типичные ошибки
- **Перепутан порядок аргументов.** `confusion_matrix(pred, fact)` транспонирует таблицу: FP и FN меняются местами, а выводы — на противоположные.
- **Порядок `ravel()`.** Это TN, FP, FN, TP — не «TP первым».
- **Сравнение без базовой модели.** «89 %» без «78 % у DummyClassifier» ничего не говорит.
- **Доли ошибок на весь тест.** Делите FN на всех ушедших, FP — на всех оставшихся.
:::

{{practice: cost}}

## Практика

## task: count-four | Четыре исхода руками | warmup

Отдел лояльности отправил бонусы по прогнозу модели десяти гостям и через 60 дней узнал правду. Посчитайте без sklearn, масками pandas, четыре исхода: `tp`, `fp`, `fn`, `tn` (целые числа). В `acc` сохраните долю правильных ответов (2 знака), посчитанную по этим четырём числам.

### starter
```python
import pandas as pd

fact = pd.Series([1, 0, 0, 1, 1, 0, 0, 0, 1, 0])
pred = pd.Series([1, 0, 1, 0, 1, 0, 0, 1, 0, 0])

```

### check
```python
_f = [1, 0, 0, 1, 1, 0, 0, 0, 1, 0]
_p = [1, 0, 1, 0, 1, 0, 0, 1, 0, 0]
_w = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
for _a, _b in zip(_f, _p):
    _w[('t' if _a == _b else 'f') + ('p' if _b == 1 else 'n')] += 1
_tips = {'tp': 'факт 1 и прогноз 1', 'fp': 'факт 0, а прогноз 1 — лишний бонус', 'fn': 'факт 1, а прогноз 0 — пропущенный гость', 'tn': 'факт 0 и прогноз 0'}
for _k, _v in _w.items():
    assert int(need(_k)) == _v, f'{_k} = {need(_k)}, а должно быть {_v}. {_k.upper()} — это {_tips[_k]}.'
assert close(need('acc'), round((_w['tp'] + _w['tn']) / 10, 2)), f'acc = {need("acc")}. Правильные ответы — TP и TN, делить на всех гостей.'
```

### hint
Маска для TP: `(fact == 1) & (pred == 1)`; `.sum()` считает число `True`.

### hint
Accuracy: `(tp + tn) / (tp + fp + fn + tn)`.

### solution
```python
import pandas as pd

fact = pd.Series([1, 0, 0, 1, 1, 0, 0, 0, 1, 0])
pred = pd.Series([1, 0, 1, 0, 1, 0, 0, 1, 0, 0])
tp = int(((fact == 1) & (pred == 1)).sum())
fp = int(((fact == 0) & (pred == 1)).sum())
fn = int(((fact == 1) & (pred == 0)).sum())
tn = int(((fact == 0) & (pred == 0)).sum())
acc = round((tp + tn) / (tp + fp + fn + tn), 2)
```

### explain
Accuracy 60 % складывается из двух верных «уйдёт» и четырёх верных «останется». Четыре ошибки делятся поровну: два лишних бонуса и два пропущенных гостя — а по одной accuracy этого не видно.

## task: p-dummy | Базовая модель | warmup

Соберите программу: обучить базовую модель «самый частый класс» и вывести её матрицу ошибок на тесте. Признаки `X_train`, `X_test`, `y_train`, `y_test` уже готовы.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
```

### parsons
```python
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix
dummy = DummyClassifier(strategy="most_frequent")
dummy.fit(X_train, y_train)
pred = dummy.predict(X_test)
print(confusion_matrix(y_test, pred))
```

### check
```python
_n0, _n1 = int((y_test == 0).sum()), int((y_test == 1).sum())
_want = [f'[[{_n0}    0]', f'[{_n1}    0]]']
assert [_l.replace(' ', '') for _l in _lines] == [_s.replace(' ', '') for _s in _want], f'Программа вывела {_lines}. Ожидалась матрица 2×2, где весь прогноз — «останется»: в левом столбце {_n0} и {_n1}, в правом нули.'
```

### hint
Сначала импорты, потом модель, `fit`, `predict` — и только затем матрица по фактическим ответам и прогнозу.

## task: dummy-acc | Сколько стоит 78 % | warmup

Обучите `DummyClassifier(strategy="most_frequent")` и сохраните:

- `acc_dummy` — её accuracy на тесте (3 знака);
- `churn_test` — долю ушедших в тесте (3 знака);
- `found` — сколько ушедших гостей теста базовая модель нашла (целое число, по матрице ошибок).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_ct = round(_e.mean(), 3)
assert close(need('churn_test'), _ct), f'churn_test = {need("churn_test")}, а нужно {_ct} — среднее y_test.'
assert close(need('acc_dummy'), round(1 - _e.mean(), 3)), f'acc_dummy = {need("acc_dummy")}, а нужно {round(1 - _e.mean(), 3)}. Это score базовой модели на X_test, y_test.'
assert int(need('found')) == 0, f'found = {need("found")}. Посмотрите на TP в матрице ошибок базовой модели: сколько гостей она назвала уходящими?'
```

### hint
`DummyClassifier` импортируется из `sklearn.dummy`; дальше как с любой моделью: `fit` и `score`.

### hint
Найденные ушедшие — это TP: `tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
dummy = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
acc_dummy = round(dummy.score(X_test, y_test), 3)
churn_test = round(y_test.mean(), 3)
tn, fp, fn, tp = confusion_matrix(y_test, dummy.predict(X_test)).ravel()
found = int(tp)
```

### explain
Accuracy базовой модели равна доле оставшихся: 1 − 0.223 ≈ 0.777. Отдел лояльности с такой моделью не отправил бы ни одного бонуса.

## task: forest-cm | Матрица леса | base

Обучите `RandomForestClassifier(n_estimators=50, random_state=0)` и сохраните его матрицу ошибок на тесте в `cm`, а её клетки — в `tn`, `fp`, `fn`, `tp` (целые числа).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import confusion_matrix as _cm
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = _cm(_e, _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b))
_m = _np.asarray(need('cm'))
assert _m.shape == (2, 2), f'cm формы {_m.shape}, а матрица ошибок для двух классов — 2×2.'
if (_m == _w.T).all() and not (_m == _w).all():
    raise AssertionError('cm перевёрнута: похоже, аргументы перепутаны местами. Сначала факт (y_test), потом прогноз.')
assert (_m == _w).all(), f'cm = {_m.tolist()}, а нужно {_w.tolist()}. Проверьте модель (n_estimators=50, random_state=0) и что прогноз сделан для X_test.'
for _k, _v in zip(['tn', 'fp', 'fn', 'tp'], _w.ravel()):
    assert int(need(_k)) == int(_v), f'{_k} = {need(_k)}, а должно быть {int(_v)}. Порядок ravel(): tn, fp, fn, tp.'
```

### hint
`confusion_matrix(y_test, forest.predict(X_test))` — сначала правда, потом прогноз.

### hint
`tn, fp, fn, tp = cm.ravel()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
cm = confusion_matrix(y_test, forest.predict(X_test))
tn, fp, fn, tp = cm.ravel()
```

### explain
Лес из 50 деревьев: 92 найденных уходящих, 42 пропущенных, 25 лишних бонусов, 441 верно не тронутый гость. Проверка суммой: 441 + 25 = 466 оставшихся и 42 + 92 = 134 ушедших — строки матрицы складываются в размеры классов. Если суммы не сходятся, порядок аргументов перепутан.

## task: rule-cm | Правило 45 дней | base

Отдел лояльности считает гостя уходящим, если `days_since_last > 45`. Превратите правило в прогноз для тестовых гостей (1 — уйдёт, 0 — останется) и сохраните:

- `rule_cm` — матрицу ошибок правила;
- `rule_missed` — сколько ушедших гостей правило пропустило (целое);
- `rule_extra` — сколько лишних бонусов оно бы раздало (целое).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.metrics import confusion_matrix as _cm
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = _cm(_e, (_b['days_since_last'] > 45).astype(int))
_m = _np.asarray(need('rule_cm'))
assert _m.shape == (2, 2), f'rule_cm формы {_m.shape}, а нужна матрица 2×2.'
assert (_m == _w).all(), f'rule_cm = {_m.tolist()}, а нужно {_w.tolist()}. Правило — строго больше 45 дней, применяется к X_test; сначала факт, потом прогноз.'
assert int(need('rule_missed')) == int(_w[1, 0]), f'rule_missed = {need("rule_missed")}. Пропущенные уходящие — FN: факт 1, прогноз 0.'
assert int(need('rule_extra')) == int(_w[0, 1]), f'rule_extra = {need("rule_extra")}. Лишние бонусы — FP: факт 0, прогноз 1.'
```

### hint
Прогноз правила: `(X_test["days_since_last"] > 45).astype(int)`.

### hint
`tn, fp, fn, tp = rule_cm.ravel()` — пропущенные это `fn`, лишние бонусы — `fp`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
rule = (X_test["days_since_last"] > 45).astype(int)
rule_cm = confusion_matrix(y_test, rule)
tn, fp, fn, tp = rule_cm.ravel()
rule_missed = int(fn)
rule_extra = int(fp)
```

### explain
Правило осторожно: лишних бонусов около десятка. Но больше половины уходящих оно пропускает — это гости, которые ещё заходят, но скоро перестанут. Их правило «45 дней» увидит, только когда будет поздно.

## task: shares | Доли ошибок | base

Для леса `RandomForestClassifier(n_estimators=50, random_state=0)` посчитайте на тесте (все — 3 знака):

- `missed_share` — долю пропущенных среди ушедших гостей;
- `extra_share` — долю лишних бонусов среди оставшихся гостей;
- `error_rate` — долю всех ошибок среди всех гостей теста.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import confusion_matrix as _cm
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_tn, _fp, _fn, _tp = _cm(_e, _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b)).ravel()
_ms, _es, _er = round(_fn / (_fn + _tp), 3), round(_fp / (_fp + _tn), 3), round((_fp + _fn) / len(_e), 3)
_got = need('missed_share')
assert not close(_got, round(_fn / len(_e), 3)) or close(_got, _ms), f'missed_share = {_got} — похоже, FN поделено на всех гостей. Делить нужно на число ушедших: FN + TP.'
assert close(_got, _ms), f'missed_share = {_got}, а нужно {_ms}. Это FN / (FN + TP).'
assert close(need('extra_share'), _es), f'extra_share = {need("extra_share")}, а нужно {_es}. Это FP / (FP + TN) — доля внутри оставшихся.'
assert close(need('error_rate'), _er), f'error_rate = {need("error_rate")}, а нужно {_er}. Все ошибки — FP и FN вместе, делить на всех гостей теста.'
```

### hint
Сначала разложите матрицу: `tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()`.

### hint
Можно проверить себя через `confusion_matrix(y_test, pred, normalize="true")`: нужные доли — вне диагонали.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pred = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train).predict(X_test)
tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
missed_share = round(fn / (fn + tp), 3)
extra_share = round(fp / (fp + tn), 3)
error_rate = round((fp + fn) / len(y_test), 3)
```

### explain
Общая доля ошибок около 11 % — но она состоит из двух очень разных частей: лишние бонусы получает около 5 % оставшихся, а пропускаем мы около 30 % уходящих. Одно число скрывает, что модель ошибается в основном на тех, ради кого её строили.

## task: two-trees | Осторожное и смелое дерево | base

Сравните два дерева: `DecisionTreeClassifier(max_depth=2, random_state=0)` и `DecisionTreeClassifier(max_depth=3, random_state=0)`. Сохраните:

- `acc2`, `acc3` — accuracy на тесте (3 знака);
- `tp2`, `tp3` — сколько уходящих нашло каждое дерево (целые);
- `fp2`, `fp3` — сколько лишних бонусов раздало каждое (целые);
- `more_found` — строку `"2"` или `"3"`: какое дерево нашло больше уходящих.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.metrics import confusion_matrix as _cm
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_r = {}
for _d in (2, 3):
    _m = _T(max_depth=_d, random_state=0).fit(_a, _c)
    _tn, _fp, _fn, _tp = _cm(_e, _m.predict(_b)).ravel()
    _r[_d] = (round(_m.score(_b, _e), 3), int(_tp), int(_fp))
    assert close(need(f'acc{_d}'), _r[_d][0]), f'acc{_d} = {need(f"acc{_d}")}, а нужно {_r[_d][0]} — accuracy дерева глубины {_d} на тесте.'
    assert int(need(f'tp{_d}')) == _r[_d][1], f'tp{_d} = {need(f"tp{_d}")}, а нужно {_r[_d][1]}. TP — правый нижний угол матрицы.'
    assert int(need(f'fp{_d}')) == _r[_d][2], f'fp{_d} = {need(f"fp{_d}")}, а нужно {_r[_d][2]}. FP — правый верхний угол матрицы.'
_mf = '2' if _r[2][1] > _r[3][1] else '3'
assert str(need('more_found')) == _mf, f'more_found = {need("more_found")!r}. Сравните tp2 и tp3.'
```

### hint
Сделайте цикл `for depth in [2, 3]:` или просто два блока кода — по одному на дерево.

### hint
`tn, fp, fn, tp = confusion_matrix(y_test, tree.predict(X_test)).ravel()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

t2 = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train)
t3 = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X_train, y_train)
acc2 = round(t2.score(X_test, y_test), 3)
acc3 = round(t3.score(X_test, y_test), 3)
tn, fp2, fn, tp2 = confusion_matrix(y_test, t2.predict(X_test)).ravel()
tn, fp3, fn, tp3 = confusion_matrix(y_test, t3.predict(X_test)).ravel()
more_found = "2" if tp2 > tp3 else "3"
```

### explain
Дерево глубины 3 точнее по accuracy, но почти никого не тревожит зря и потому находит меньше половины уходящих. Дерево глубины 2 ошибается чаще, зато находит заметно больше уходящих — ценой лишних бонусов. Какое лучше, решает не accuracy, а цена ошибок — следующая задача.

## task: cost | Сколько стоят ошибки | plus

Отдел лояльности оценил: бонус стоит 300 ₽ (платим за каждого гостя, которому его отправили, — и за TP, и за FP), а каждый пропущенный уходящий гость — это 2000 ₽ потерянной выручки (в «Разберём вместе» мы брали 3 000 ₽; отдел пересчитал и решил, что для наших гостей это 2000 ₽ — схема та же, другая цена). Посчитайте стоимость `300 × (TP + FP) + 2000 × FN` на тесте для четырёх вариантов и сохраните словарь `costs` с ключами:

- `"никто"` — `DummyClassifier(strategy="most_frequent")`;
- `"правило"` — `days_since_last > 45`;
- `"дерево"` — `DecisionTreeClassifier(max_depth=2, random_state=0)`;
- `"лес"` — `RandomForestClassifier(n_estimators=50, random_state=0)`.

Значения — целые рубли. В `cheapest` сохраните ключ самого дешёвого варианта.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.dummy import DummyClassifier as _D
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import confusion_matrix as _cm
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_preds = {
    'никто': _D(strategy='most_frequent').fit(_a, _c).predict(_b),
    'правило': (_b['days_since_last'] > 45).astype(int),
    'дерево': _T(max_depth=2, random_state=0).fit(_a, _c).predict(_b),
    'лес': _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b),
}
_w = {}
for _k, _p in _preds.items():
    _tn, _fp, _fn, _tp = _cm(_e, _p).ravel()
    _w[_k] = int(300 * (_tp + _fp) + 2000 * _fn)
_got = need('costs', dict)
assert set(_got) == set(_w), f'Ключи costs: {sorted(_got)}, а нужны {sorted(_w)}.'
for _k in _w:
    assert int(_got[_k]) == _w[_k], f'costs[{_k!r}] = {_got[_k]}, а нужно {_w[_k]}. Бонус (300 ₽) платим за TP и FP, потерю (2000 ₽) — за FN; TN ничего не стоит.'
assert need('cheapest') == min(_w, key=_w.get), f'cheapest = {need("cheapest")!r}. Найдите ключ с наименьшей стоимостью: min(costs, key=costs.get).'
```

### hint
Соберите словарь прогнозов `{"никто": ..., "правило": ..., ...}` и в цикле разложите каждую матрицу через `ravel()`.

### hint
Ключ с наименьшим значением: `min(costs, key=costs.get)`. Не забудьте `int(...)`, чтобы получить обычные целые числа.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

preds = {
    "никто": DummyClassifier(strategy="most_frequent").fit(X_train, y_train).predict(X_test),
    "правило": (X_test["days_since_last"] > 45).astype(int),
    "дерево": DecisionTreeClassifier(max_depth=2, random_state=0).fit(X_train, y_train).predict(X_test),
    "лес": RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train).predict(X_test),
}
costs = {}
for name, pred in preds.items():
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    costs[name] = int(300 * (tp + fp) + 2000 * fn)
cheapest = min(costs, key=costs.get)
print(costs, cheapest)
```

### explain
Самым дешёвым оказывается простое дерево глубины 2, хотя по accuracy оно заметно уступает лесу. Пропущенный гость стоит почти в семь раз дороже бонуса, поэтому выгоднее «перестраховаться» и раздать лишние бонусы, чем упустить уходящих. При другом соотношении цен победитель может смениться. Подбирать баланс тоньше, не меняя модель, научимся в уроке «Порог, PR- и ROC-кривые» — через порог вероятности.

## task: missed-who | Кого модель пропускает | star

Разбор ошибок — лучший способ понять модель. Возьмите лес `RandomForestClassifier(n_estimators=50, random_state=0)` и **только ушедших** гостей теста. Разделите их на найденных (TP) и пропущенных (FN) и сравните группы. Сохраните:

- `days_tp`, `days_fn` — медиану `days_since_last` у найденных и у пропущенных (1 знак);
- `visits_tp`, `visits_fn` — медиану `visits_90d` (1 знак);
- `new_tp`, `new_fn` — долю новичков (`tenure_months <= 3`) в каждой группе (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _e = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_t = _b.copy()
_t['pred'] = _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b)
_ch = _t[_e == 1]
_tp, _fn = _ch[_ch['pred'] == 1], _ch[_ch['pred'] == 0]
_w = {
    'days_tp': round(_tp['days_since_last'].median(), 1), 'days_fn': round(_fn['days_since_last'].median(), 1),
    'visits_tp': round(_tp['visits_90d'].median(), 1), 'visits_fn': round(_fn['visits_90d'].median(), 1),
    'new_tp': round((_tp['tenure_months'] <= 3).mean(), 3), 'new_fn': round((_fn['tenure_months'] <= 3).mean(), 3),
}
for _k, _v in _w.items():
    _grp = 'найденных (факт 1, прогноз 1)' if _k.endswith('tp') else 'пропущенных (факт 1, прогноз 0)'
    assert close(need(_k), _v), f'{_k} = {need(_k)}, а нужно {_v}. Это группа {_grp}; сначала оставьте только ушедших гостей теста.'
```

### hint
Скопируйте `X_test` и добавьте столбец прогноза: `t = X_test.copy(); t["pred"] = forest.predict(X_test)`. Ушедшие: `t[y_test == 1]`.

### hint
Внутри ушедших найденные — `pred == 1`, пропущенные — `pred == 0`. Доля новичков: `(group["tenure_months"] <= 3).mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)

t = X_test.copy()
t["pred"] = forest.predict(X_test)
churned = t[y_test == 1]
found = churned[churned["pred"] == 1]
missed = churned[churned["pred"] == 0]
days_tp = round(found["days_since_last"].median(), 1)
days_fn = round(missed["days_since_last"].median(), 1)
visits_tp = round(found["visits_90d"].median(), 1)
visits_fn = round(missed["visits_90d"].median(), 1)
new_tp = round((found["tenure_months"] <= 3).mean(), 3)
new_fn = round((missed["tenure_months"] <= 3).mean(), 3)
```

### explain
Найденные уходящие — те, кто уже почти пропал: давно не был, мало визитов (медиана давности 60 дней, 1.5 визита за 90 дней). Пропущенные выглядят как обычные гости — были недавно, ходят часто (медиана 14.5 дня и 4.5 визита), — и новичков среди них вдвое больше: 26 % против 13 %. Это «тихий» отток, о котором шла речь в проекте главы 6. Разбор FN подсказывает, куда двигаться: искать признаки, которые отличают таких гостей (урок «Новые признаки» — конструирование признаков), или снижать порог тревоги (урок «Порог, PR- и ROC-кривые»).
