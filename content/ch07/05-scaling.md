---
title: "Масштабирование и ближайшие соседи"
lead: "В таблице гостей средний чек измеряется сотнями рублей, а жалобы — единицами. Для дерева это неважно, а для моделей, которые складывают и сравнивают числа, — очень. Учимся приводить признаки к одному масштабу без утечки и видим, как это меняет метод ближайших соседей и логистическую регрессию. Регуляризация — в следующем уроке."
files: [guests_churn.csv]
recap:
  - "Масштаб важен моделям, которые считают расстояния или складывают взвешенные признаки (ближайшие соседи, логистическая регрессия). Деревьям и лесу он почти безразличен."
  - "`StandardScaler`: z = (x − среднее) / стандартное отклонение. Учим (`fit`) только на train, применяем (`transform`) и к train, и к test — иначе утечка."
  - "`MinMaxScaler` сжимает признак в диапазон 0…1 по минимуму и максимуму train; на новых данных значения могут выйти за границы."
  - "`KNeighborsClassifier(n_neighbors=15)` голосует 15 ближайшими гостями из train; без масштабирования «ближайших» выбирает средний чек."
  - "После стандартизации логистическая регрессия сходится за десяток шагов, а веса `coef_` можно сравнивать между собой как важность признаков."
---

## Разные единицы — разные расстояния

Начнём с новой модели — **метода ближайших соседей** (k nearest neighbors, kNN). Он устроен как совет «спроси у похожих»: чтобы оценить нового гостя, модель находит в обучающей таблице k самых похожих на него гостей и смотрит, сколько из них ушли. Если из 15 соседей ушли 9, вероятность ухода — 9/15 = 0.6.

«Похожесть» модель меряет **расстоянием** между строками: разность по каждому признаку возводится в квадрат, квадраты складываются, из суммы берётся корень — как теорема Пифагора, только для 15 признаков. Посмотрим, из чего складывается расстояние между двумя гостями:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

a, b = X_train.iloc[0], X_train.iloc[1]
print(pd.concat([a, b], axis=1).head(8))
print()
print("вклад в квадрат расстояния:")
print(((a - b) ** 2).sort_values(ascending=False).head(5))
```

Чеки гостей отличаются на 48 ₽ — это даёт 2304 в сумме квадратов. Давность визита отличается на неделю — 49. А то, что один гость пользуется приложением, а другой нет, — всего 1. Расстояние почти целиком решает средний чек, просто потому что он измеряется в рублях, а не потому что важен для ухода. Поменяй мы рубли на копейки — и «похожих» гостей модель выбирала бы совсем иначе.

Модель с таким расстоянием обучается и даже что-то предсказывает:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score, recall_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

knn = KNeighborsClassifier(n_neighbors=15).fit(X_train, y_train)
pred = knn.predict(X_test)
p = knn.predict_proba(X_test)[:, 1]
print(f"recall {recall_score(y_test, pred):.3f}, F1 {f1_score(y_test, pred):.3f}, AUC {roc_auc_score(y_test, p):.3f}")
```

`n_neighbors` — сколько соседей спрашивать. Интерфейс — как у всех моделей sklearn: `fit`, `predict`, `predict_proba`. Результат слабый: AUC около 0.77 при 0.9 у леса и логистической регрессии, а полнота — около 40 %. Модель ищет соседей «по чеку», а не по поведению.

## Разберём вместе: кто кому сосед

Три гостя, у всех приложение, отличаются чеком и давностью визита:

| гость | средний чек, ₽ | дней без визита |
|---|---|---|
| A | 400 | 10 |
| B | 480 | 12 |
| C | 410 | 70 |

По смыслу B похож на A: оба ходят регулярно, чек отличается на 80 ₽. C почти не отличается чеком, но не появлялся два месяца — типичный кандидат на уход.

**Сырые признаки.** Расстояние A–B = √(80² + 2²) = √6404 ≈ **80.0**; A–C = √(10² + 60²) = √3700 ≈ **60.8**. Ближайший сосед A — **C**: 60 дней разницы «весят» меньше, чем 80 рублей.

**В стандартных отклонениях.** Пусть разброс чека 120 ₽, давности — 35 дней (примерно как у наших гостей). Делим разности на разброс: A–B = √((80/120)² + (2/35)²) = √(0.444 + 0.003) ≈ **0.67**; A–C = √((10/120)² + (60/35)²) = √(0.007 + 2.94) ≈ **1.72**. Теперь ближайший — **B**.

Что получилось: от единиц измерения зависит, кого модель считает похожим. Стандартизация переводит все признаки в одну «валюту» — отклонения от среднего, — и разница в 60 дней становится тем, чем она и является: огромной.

::: figure knn-abc
Разбор с тремя гостями. Слева — расстояние в рублях и днях: 80 ₽ «длиннее» 60 дней, и ближайшим к A оказывается C. Справа — те же гости в стандартных отклонениях: ближе B, как и подсказывает здравый смысл.
:::

{{practice: knn-hand}}

## StandardScaler: один масштаб для всех

Лечение — **стандартизация** (standardization): из каждого признака вычитаем его среднее и делим на стандартное отклонение.

z = (x − среднее) / стандартное отклонение

После этого у каждого признака среднее 0 и разброс 1, а значение читается одинаково: «на сколько отклонений гость выше или ниже среднего». Чек 400 ₽ и 30 дней без визита превращаются в сравнимые числа вроде 0.6 и 0.3.

::: predict
```python static
import numpy as np
x = np.array([10, 20, 30])
z = (x - x.mean()) / x.std()
print([round(float(v), 2) for v in z])
```

- `[-10.0, 0.0, 10.0]`
- [x] `[-1.22, 0.0, 1.22]`
- `[0.0, 0.5, 1.0]`

Почему: среднее 20, стандартное отклонение около 8.16. Крайние значения отстоят от среднего на 10 — это примерно 1.22 отклонения. `[0.0, 0.5, 1.0]` — это другое преобразование, MinMax, о нём ниже.
:::

В sklearn стандартизацию делает `StandardScaler` из `sklearn.preprocessing`. У него, как у модели, два шага:

- `fit(X_train)` — **запомнить** среднее и отклонение каждого столбца (лежат в `scaler.mean_` и `scaler.scale_`);
- `transform(X)` — **применить** запомненное к любой таблице.

::: figure scaler-fit
`fit` смотрит только на обучающую часть и запоминает средние и разбросы; `transform` применяет их к train, тесту и новым гостям одинаково. Любой `fit` на данных с тестом — утечка.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

scaler = StandardScaler().fit(X_train)
Xs_train = scaler.transform(X_train)
Xs_test = scaler.transform(X_test)

print(pd.Series(scaler.mean_, index=X.columns).round(2).head(4))
print("train, среднее:", Xs_train.mean(axis=0)[:4].round(3))
print("test, среднее: ", Xs_test.mean(axis=0)[:4].round(3))
```

Если считаете z руками, помните: `std()` в pandas по умолчанию делит на n − 1, а StandardScaler — на n. Чтобы совпасть со StandardScaler, пишите `.std(ddof=0)` (подробности — в блоке «Почему не совпадает с pandas» ниже).

Результат `transform` — массив numpy, без названий столбцов (порядок столбцов прежний). На train средние ровно 0, на тесте — около нуля, но не ровно: тест преобразован **чужими**, обучающими средними. Так и должно быть.

::: warn Учим только на train
Нельзя делать `StandardScaler().fit(X)` по всей таблице до разбиения или отдельно `fit` на тесте. Среднее и отклонение — тоже знания о данных. Если они посчитаны с участием теста, тест перестаёт быть «новыми гостями» — это утечка, как в главе 6. Правило: `fit` — только на обучающей части; `transform` — на всём остальном. Для train есть сокращение `scaler.fit_transform(X_train)` — то же, что `fit`, потом `transform`.
:::

::: deep Почему не совпадает с pandas
`X_train["days_since_last"].std()` в pandas даст 35.37, а `scaler.scale_` — 35.36. Pandas по умолчанию делит на n − 1 (выборочная оценка из главы 5, `ddof=1`), а StandardScaler — на n (`ddof=0`). Чтобы повторить StandardScaler руками, пишите `.std(ddof=0)`. На 1800 строках разница в четвёртом знаке, на маленьких таблицах — заметнее.
:::

Есть и другой способ — **MinMaxScaler**: (x − минимум) / (максимум − минимум). Признак сжимается в отрезок от 0 до 1 по минимуму и максимуму train. Он удобен, когда нужен понятный диапазон, но чувствителен к выбросам: один гость с 57 визитами «сплющивает» всех остальных к нулю. И на новых данных значения могут выйти за границы:

::: predict
```python static
from sklearn.preprocessing import MinMaxScaler
mm = MinMaxScaler().fit([[0], [50], [100]])
print(mm.transform([[120]])[0][0])
```

- `1.0`
- [x] `1.2`
- `Ошибка ValueError`

Почему: минимум и максимум запомнены по обучающим данным (0 и 100). Новое значение 120 больше максимума, и после преобразования получается 1.2 — MinMaxScaler ничего не обрезает.
:::

::: quiz
Почему `StandardScaler` обучают (`fit`) только на `X_train`, а к `X_test` применяют `transform`?

- [x] Средние и разбросы — тоже «знания»; если взять их с теста, информация о тесте просочится в подготовку
  > На новых данных средних заранее не будет: модель должна работать с параметрами, известными на момент обучения.
- [ ] `fit` на тесте вызывает ошибку
  > Технически сработает, но оценка станет нечестной.
- [ ] Чтобы train и test получили разные масштабы
  > Наоборот: масштаб должен быть один — тот, что выучен на train.
- [ ] Так быстрее
  > Скорость тут ни при чём.
:::

{{practice: scale-fit, zscore}}

## Ближайшие соседи после масштабирования

Повторим kNN на стандартизированных признаках. Модель та же, данные — `Xs_train` и `Xs_test`:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score, recall_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

for name, A, B in [("без масштаба", X_train, X_test), ("StandardScaler", Xs_train, Xs_test)]:
    knn = KNeighborsClassifier(n_neighbors=15).fit(A, y_train)
    pred = knn.predict(B)
    p = knn.predict_proba(B)[:, 1]
    print(f"{name:15} recall {recall_score(y_test, pred):.3f}, F1 {f1_score(y_test, pred):.3f}, AUC {roc_auc_score(y_test, p):.3f}")
```

Та же модель, те же гости — а полнота выросла примерно с 40 % до 52 %, F1 — с 0.53 до 0.64, AUC — с 0.77 до 0.86. Мы ничего не добавили в данные, только перестали мерить похожесть в рублях.

Лесу и дереву масштаб почти безразличен: дерево задаёт вопросы «чек больше 350?», и если все чеки поделить на 100, вопрос станет «больше 3.5?» — разбиение то же (с точностью до округлений: в задаче увидите 0.998 вместо ровно 1). Масштабирование нужно моделям, которые **складывают или сравнивают** признаки между собой: ближайшие соседи, логистическая и линейная регрессия.

::: note
kNN здесь — учебный пример модели, чувствительной к масштабу. На наших гостях он уступает лесу и логистической регрессии даже после масштабирования. Зато хорошо видно, зачем нужен этот шаг.
:::

{{practice: p-knn, knn-scale, who-cares}}

## Масштаб и логистическая регрессия

В главе 6 логистическая регрессия на сырых признаках выдавала предупреждение `ConvergenceWarning`, и мы лечили его большим `max_iter`. Теперь понятна причина: алгоритм подбора весов делает маленькие шаги, и когда один признак измеряется сотнями, а другой долями, «настроить» их одновременно трудно. Сравним, сколько шагов понадобилось (`n_iter_`):

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

raw = LogisticRegression(max_iter=2000).fit(X_train, y_train)
scaled = LogisticRegression().fit(Xs_train, y_train)
print("шагов без масштаба:", raw.n_iter_[0], " AUC", round(roc_auc_score(y_test, raw.predict_proba(X_test)[:, 1]), 3))
print("шагов с масштабом: ", scaled.n_iter_[0], " AUC", round(roc_auc_score(y_test, scaled.predict_proba(Xs_test)[:, 1]), 3))
```

Без масштаба — около 1200 шагов (1242), с масштабом — 11, и даже стандартного `max_iter=100` с запасом хватает. Качество почти одинаковое (AUC 0.898 и 0.897): модель в обоих случаях находит одно и то же решение, просто с масштабом — быстрее.

Второй подарок — веса можно сравнивать. В главе 6 мы оговаривались: вес «за один рубль» и вес «за одну жалобу» сравнивать нельзя. После стандартизации каждый вес означает «на сколько меняется линейная оценка, если признак вырос на одно стандартное отклонение» — единица у всех одна.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
Xs_train = StandardScaler().fit(X_train).transform(X_train)

w = pd.DataFrame({
    "сырые": LogisticRegression(max_iter=2000).fit(X_train, y_train).coef_[0],
    "после масштаба": LogisticRegression().fit(Xs_train, y_train).coef_[0],
}, index=X.columns)
print(w.round(3).sort_values("после масштаба"))
```

На сырых признаках у давности визита вес 0.035 — кажется, что она почти не важна, а жалобы (3.1) — главное. Но 0.035 — это «за один день», а дней бывает до 200. После масштабирования давность визита выходит на первое место (около 1.2), за ней жалобы и число визитов. Это и есть честный рейтинг: самый сильный признак для ухода — сколько дней гостя не было.

::: warn
Сравнивать веса как важность можно, только если признаки отмасштабированы и не дублируют друг друга. Если два признака почти одинаковы (например, визиты за 90 дней и визиты в месяц), модель может поделить вес между ними как угодно, и по отдельности их веса ничего не значат.
:::

::: warn Типичные ошибки
- **`fit` масштаба на всей таблице или на тесте.** Средние и разбросы — знание о данных; учим только на train.
- **Масштабируют для леса.** Не вредно, но бесполезно: деревьям важен порядок значений, а не единицы.
- **Сравнивают веса сырой модели.** «0.035 за день» и «3.1 за жалобу» несравнимы; рейтинг признаков — только после масштаба.
- **Забывают, что `transform` возвращает массив.** Названия столбцов пропадают; для отчёта оборачивайте обратно в DataFrame с `columns=X.columns`.
:::

{{practice: iters, coef-rank}}

## Практика

## task: scale-fit | Обучить масштаб | warmup

Отмасштабируйте признаки `StandardScaler`, не допуская утечки. Сохраните:

- `Xs_train`, `Xs_test` — преобразованные обучающую и тестовую таблицы;
- `days_mean` — среднее `days_since_last`, которое запомнил масштабировщик (2 знака);
- `test_mean` — среднее стандартизированного `days_since_last` на тесте (3 знака). Столбец `days_since_last` — четвёртый, индекс 3; его номер можно не считать глазами: `list(X.columns).index("days_since_last")`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

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
from sklearn.preprocessing import StandardScaler as _SS
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
_tr, _te = _s.transform(_a), _s.transform(_b)
_u = _np.asarray(need('Xs_train'), dtype=float)
_v = _np.asarray(need('Xs_test'), dtype=float)
assert _u.shape == _tr.shape, f'Xs_train формы {_u.shape}, а должна быть {_tr.shape} — та же таблица X_train, только отмасштабированная.'
assert _v.shape == _te.shape, f'Xs_test формы {_v.shape}, а должна быть {_te.shape}.'
assert _np.allclose(_u, _tr, atol=1e-6), 'Xs_train не совпадает с ожидаемым. Масштабировщик учится (fit) на X_train и только на нём.'
_full = _SS().fit(_X).transform(_b)
_own = _SS().fit(_b).transform(_b)
assert not _np.allclose(_v, _own, atol=1e-6), 'Похоже, для теста масштабировщик обучен заново на X_test — это утечка. Тест нужно преобразовать тем же scaler, что обучен на X_train: scaler.transform(X_test).'
assert not _np.allclose(_v, _full, atol=1e-6), 'Похоже, масштабировщик обучен на всей таблице X. Учите его только на X_train.'
assert _np.allclose(_v, _te, atol=1e-6), 'Xs_test не совпадает с ожидаемым: нужен transform обученным на X_train масштабировщиком.'
assert close(need('days_mean'), round(_s.mean_[3], 2)), f'days_mean = {need("days_mean")}, а ожидалось {round(_s.mean_[3], 2)}. Запомненные средние лежат в scaler.mean_.'
assert close(need('test_mean'), round(_te[:, 3].mean(), 3)), f'test_mean = {need("test_mean")}, а ожидалось {round(_te[:, 3].mean(), 3)}. Возьмите столбец 3 массива Xs_test: Xs_test[:, 3].'
```

### hint
`scaler = StandardScaler().fit(X_train)`, затем `scaler.transform(...)` для обеих таблиц.

### hint
Среднее, запомненное при обучении, — `scaler.mean_[3]`. Столбец массива numpy — `Xs_test[:, 3]`, его среднее — `.mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

scaler = StandardScaler().fit(X_train)
Xs_train = scaler.transform(X_train)
Xs_test = scaler.transform(X_test)
days_mean = round(scaler.mean_[3], 2)
test_mean = round(Xs_test[:, 3].mean(), 3)
```

### explain
На тесте среднее давности — не ноль, и это правильно: тест преобразован средним и отклонением обучающих гостей. Если бы на тесте вышел ровно ноль, это значило бы, что масштабировщик подсмотрел в тест.

## task: p-knn | Соседи после масштаба | warmup

Соберите программу: отмасштабировать признаки, обучить метод ближайших соседей на 15 соседях и вывести F1 на тесте (3 знака).

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
knn = KNeighborsClassifier(n_neighbors=15)
knn.fit(scaler.transform(X_train), y_train)
pred = knn.predict(scaler.transform(X_test))
print(round(f1_score(y_test, pred), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neighbors import KNeighborsClassifier as _KNN
from sklearn.metrics import f1_score as _f1
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
_w = round(_f1(_d, _KNN(n_neighbors=15).fit(_s.transform(_a), _c).predict(_s.transform(_b))), 3)
assert _lines == [str(_w)], f'Программа вывела {_lines}, а должна вывести одно число — F1 на тесте после масштабирования.'
```

### hint
Порядок: данные → разбиение → масштабировщик учится на train → модель учится на преобразованном train → прогноз на преобразованном test → F1.

## task: zscore | Стандартизация руками | warmup

Повторите `StandardScaler` для одного столбца без sklearn. Посчитайте по **обучающим** гостям среднее `mu` и стандартное отклонение `sd` столбца `avg_check` так, как это делает StandardScaler, и сохраните в `z_test` стандартизированный `avg_check` тестовых гостей (Series). Подсказка про отклонение — в разделе «Почему не совпадает с pandas».

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

mu = X_train["avg_check"].mean()
sd = X_train["avg_check"].std()
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a[['avg_check']])
assert close(need('mu'), _s.mean_[0], 1e-6), f'mu = {need("mu"):.3f}, а среднее обучающих чеков {_s.mean_[0]:.3f}. Среднее считается по X_train.'
assert not close(need('sd'), _a['avg_check'].std(), 1e-6), f'sd = {need("sd"):.4f} — это отклонение pandas по умолчанию (деление на n − 1). StandardScaler делит на n: нужен параметр ddof=0.'
assert close(need('sd'), _s.scale_[0], 1e-6), f'sd = {need("sd"):.4f}, а ожидалось {_s.scale_[0]:.4f}. Отклонение считается по X_train с ddof=0.'
_z = need('z_test')
assert len(_z) == len(_b), f'В z_test {len(_z)} значений, а тестовых гостей {len(_b)}. Стандартизировать нужно X_test.'
assert _np.allclose(_np.asarray(_z, dtype=float), _s.transform(_b[['avg_check']])[:, 0], atol=1e-6), 'z_test не совпадает с результатом StandardScaler. Формула: (x − mu) / sd, где mu и sd — обучающие.'
```

### hint
`.std(ddof=0)` — отклонение с делением на n, как у StandardScaler.

### hint
`z_test = (X_test["avg_check"] - mu) / sd` — тестовые чеки, но обучающие `mu` и `sd`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

mu = X_train["avg_check"].mean()
sd = X_train["avg_check"].std(ddof=0)
z_test = (X_test["avg_check"] - mu) / sd
```

## task: knn-scale | Соседи до и после | base

Обучите `KNeighborsClassifier(n_neighbors=15)` дважды: на сырых признаках и на стандартизированных (`StandardScaler`, обученный на train). Сохраните для тестовых гостей F1 при пороге по умолчанию и ROC-AUC (все — 3 знака): `f1_raw`, `auc_raw` — без масштаба, `f1_sc`, `auc_sc` — с масштабом.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neighbors import KNeighborsClassifier as _KNN
from sklearn.metrics import f1_score as _f1, roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
def _m(A, B):
    k = _KNN(n_neighbors=15).fit(A, _c)
    return round(_f1(_d, k.predict(B)), 3), round(_auc(_d, k.predict_proba(B)[:, 1]), 3)
_fr, _ar = _m(_a, _b)
_fs, _as = _m(_s.transform(_a), _s.transform(_b))
assert close(need('f1_raw'), _fr), f'f1_raw = {need("f1_raw")}, а ожидалось {_fr}. Модель на сырых X_train, F1 — по predict на X_test.'
assert close(need('auc_raw'), _ar), f'auc_raw = {need("auc_raw")}, а ожидалось {_ar}. Для AUC нужны вероятности: predict_proba(...)[:, 1].'
assert close(need('f1_sc'), _fs), f'f1_sc = {need("f1_sc")}, а ожидалось {_fs}. Масштабировщик учится на X_train, тест — через transform.'
assert close(need('auc_sc'), _as), f'auc_sc = {need("auc_sc")}, а ожидалось {_as}.'
```

### hint
Сначала `scaler = StandardScaler().fit(X_train)`, затем две модели: одна на `X_train`, другая на `scaler.transform(X_train)`. Тест для второй — тоже через `scaler.transform`.

### hint
`f1_score(y_test, knn.predict(B))` и `roc_auc_score(y_test, knn.predict_proba(B)[:, 1])`, где `B` — тестовая таблица в том же виде, что и обучающая.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

raw = KNeighborsClassifier(n_neighbors=15).fit(X_train, y_train)
f1_raw = round(f1_score(y_test, raw.predict(X_test)), 3)
auc_raw = round(roc_auc_score(y_test, raw.predict_proba(X_test)[:, 1]), 3)

sc = KNeighborsClassifier(n_neighbors=15).fit(Xs_train, y_train)
f1_sc = round(f1_score(y_test, sc.predict(Xs_test)), 3)
auc_sc = round(roc_auc_score(y_test, sc.predict_proba(Xs_test)[:, 1]), 3)
```

### explain
F1 вырос с 0.53 до 0.64, AUC — с 0.77 до 0.86. Ни одного нового признака, ни одной новой строки — только другая «линейка» для похожести. Если бы в отчёте сравнивали kNN без масштаба с лесом, kNN был бы отброшен несправедливо: сравнивать модели имеет смысл только после того, как каждая получила подходящую ей подготовку данных.

## task: iters | Сколько шагов до решения | base

Сравните, как обучается логистическая регрессия с масштабом и без. Сохраните:

- `it_raw` — число шагов (`n_iter_[0]`, целое) у `LogisticRegression(max_iter=2000)` на сырых признаках;
- `it_sc` — у `LogisticRegression()` на стандартизированных;
- `diff_auc` — модуль разницы их ROC-AUC на тесте (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
_r = _LR(max_iter=2000).fit(_a, _c)
_m = _LR().fit(_s.transform(_a), _c)
assert int(need('it_raw')) == int(_r.n_iter_[0]), f'it_raw = {need("it_raw")}, а ожидалось {int(_r.n_iter_[0])}. Модель с max_iter=2000 на сырых X_train, число шагов — n_iter_[0].'
assert int(need('it_sc')) == int(_m.n_iter_[0]), f'it_sc = {need("it_sc")}, а ожидалось {int(_m.n_iter_[0])}. Модель с настройками по умолчанию на отмасштабированном X_train.'
_dv = round(abs(_auc(_d, _r.predict_proba(_b)[:, 1]) - _auc(_d, _m.predict_proba(_s.transform(_b))[:, 1])), 3)
assert close(need('diff_auc'), _dv), f'diff_auc = {need("diff_auc")}, а ожидалось {_dv}. Модуль разницы — abs(...); тест для второй модели тоже нужно отмасштабировать.'
```

### hint
`model.n_iter_` — массив из одного числа; `int(model.n_iter_[0])`.

### hint
`diff_auc = round(abs(auc1 - auc2), 3)`, где AUC считается по `predict_proba(...)[:, 1]` на тесте в том же виде, на каком училась модель.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

raw = LogisticRegression(max_iter=2000).fit(X_train, y_train)
sc = LogisticRegression().fit(Xs_train, y_train)
it_raw = int(raw.n_iter_[0])
it_sc = int(sc.n_iter_[0])
auc_raw = roc_auc_score(y_test, raw.predict_proba(X_test)[:, 1])
auc_sc = roc_auc_score(y_test, sc.predict_proba(Xs_test)[:, 1])
diff_auc = round(abs(auc_raw - auc_sc), 3)
```

### explain
Шагов — в сотню раз меньше (1242 против 11), а AUC отличается лишь на 0.001. Масштаб не делает логистическую регрессию умнее, он делает её обучение быстрым и надёжным. На больших таблицах это разница между секундами и минутами.

## task: coef-rank | Рейтинг признаков | base

Обучите `LogisticRegression()` на стандартизированных признаках. Сохраните:

- `imp` — Series модулей весов с названиями признаков в индексе, отсортированную по убыванию;
- `top3` — список из трёх самых сильных признаков;
- `raw_place` — какое место (1 — первое) занимает `days_since_last` по модулю веса у модели `LogisticRegression(max_iter=2000)` на **сырых** признаках.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = _pd.Series(_LR().fit(_SS().fit_transform(_a), _c).coef_[0], index=_X.columns).abs().sort_values(ascending=False)
_r = _pd.Series(_LR(max_iter=2000).fit(_a, _c).coef_[0], index=_X.columns).abs().sort_values(ascending=False)
_s = need('imp', _pd.Series)
assert set(_s.index) == set(_X.columns), 'В индексе imp должны быть названия признаков: index=X.columns.'
assert (_s >= 0).all(), 'В imp есть отрицательные значения. Нужны модули весов: .abs().'
assert list(_s.index) == list(_w.index), 'Порядок imp не совпадает с ожидаемым: отсортируйте по убыванию, а модель обучите на отмасштабированном X_train.'
assert (_s - _w).abs().max() < 1e-3, 'Значения imp не совпадают с модулями coef_[0] модели на отмасштабированных признаках.'
assert list(need('top3')) == list(_w.index[:3]), f'top3 = {need("top3")}. Это первые три названия в отсортированной imp.'
_pl = list(_r.index).index('days_since_last') + 1
assert int(need('raw_place')) == _pl, f'raw_place = {need("raw_place")}, а ожидалось {_pl}. Отсортируйте модули весов сырой модели по убыванию и найдите позицию days_since_last (считая с 1).'
```

### hint
`pd.Series(model.coef_[0], index=X.columns).abs().sort_values(ascending=False)`.

### hint
Место в списке: `list(raw_imp.index).index("days_since_last") + 1` — Python считает позиции с нуля.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

Xs_train = StandardScaler().fit_transform(X_train)
model = LogisticRegression().fit(Xs_train, y_train)
imp = pd.Series(model.coef_[0], index=X.columns).abs().sort_values(ascending=False)
top3 = list(imp.index[:3])

raw = LogisticRegression(max_iter=2000).fit(X_train, y_train)
raw_imp = pd.Series(raw.coef_[0], index=X.columns).abs().sort_values(ascending=False)
raw_place = list(raw_imp.index).index("days_since_last") + 1
```

### explain
По сырым весам давность визита оказывается в самом хвосте рейтинга — её вес «за один день» маленький. После масштабирования это самый сильный признак. Если строить рейтинг важности по сырым весам, отдел лояльности получил бы прямо противоположный вывод.

## task: who-cares | Кому важен масштаб | plus

Проверьте на деле, какие модели замечают масштабирование. Обучите каждую модель дважды — на сырых и на стандартизированных признаках — и сравните прогнозы `predict` на тесте. Сохраните долю тестовых гостей, для которых прогнозы совпали (3 знака):

- `same_tree` — для `DecisionTreeClassifier(max_depth=5, random_state=0)`;
- `same_knn` — для `KNeighborsClassifier(n_neighbors=15)`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.tree import DecisionTreeClassifier as _DT
from sklearn.neighbors import KNeighborsClassifier as _KNN
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
_tr, _te = _s.transform(_a), _s.transform(_b)
_st = round(float((_DT(max_depth=5, random_state=0).fit(_a, _c).predict(_b) == _DT(max_depth=5, random_state=0).fit(_tr, _c).predict(_te)).mean()), 3)
_sk = round(float((_KNN(n_neighbors=15).fit(_a, _c).predict(_b) == _KNN(n_neighbors=15).fit(_tr, _c).predict(_te)).mean()), 3)
assert close(need('same_tree'), _st), f'same_tree = {need("same_tree")}, а ожидалось {_st}. Сравните predict дерева на X_test и на Xs_test: (p1 == p2).mean().'
assert close(need('same_knn'), _sk), f'same_knn = {need("same_knn")}, а ожидалось {_sk}.'
```

### hint
Для каждой модели: `p1 = Model(...).fit(X_train, y_train).predict(X_test)`, `p2 = Model(...).fit(Xs_train, y_train).predict(Xs_test)`.

### hint
`(p1 == p2).mean()` — доля совпадений. Оберните в `round(float(...), 3)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

t1 = DecisionTreeClassifier(max_depth=5, random_state=0).fit(X_train, y_train).predict(X_test)
t2 = DecisionTreeClassifier(max_depth=5, random_state=0).fit(Xs_train, y_train).predict(Xs_test)
k1 = KNeighborsClassifier(n_neighbors=15).fit(X_train, y_train).predict(X_test)
k2 = KNeighborsClassifier(n_neighbors=15).fit(Xs_train, y_train).predict(Xs_test)
same_tree = round(float((t1 == t2).mean()), 3)
same_knn = round(float((k1 == k2).mean()), 3)
```

### explain
Дерево почти не заметило перемены: вопросы «больше порога?» после масштабирования задают те же разбиения. Единичные расхождения — из-за округлений чисел с плавающей точкой и порогов, которые попадают ровно между значениями. А у ближайших соседей прогноз изменился для заметной доли гостей: поменялось само понятие «похожий гость».

## task: knn-hand | Соседи руками | star

Повторите метод ближайших соседей без `KNeighborsClassifier`. Для **первых пяти** тестовых гостей (строки 0–4 массива `Xs_test`) найдите 15 ближайших обучающих гостей по обычному (евклидову) расстоянию в стандартизированных признаках и посчитайте долю ушедших среди них. Сохраните список из пяти долей в `hand`. Затем сравните с моделью: в `model_p` — список вероятностей ухода `KNeighborsClassifier(n_neighbors=15)` для тех же пяти гостей.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

hand = []
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.neighbors import KNeighborsClassifier as _KNN
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
_tr, _te = _s.transform(_a), _s.transform(_b)
_mp = [float(v) for v in _KNN(n_neighbors=15).fit(_tr, _c).predict_proba(_te[:5])[:, 1]]
_h = need('hand')
assert len(_h) == 5, f'В hand {len(_h)} значений, а нужно пять — по одному на каждого из первых пяти тестовых гостей.'
_h = [float(v) for v in _h]
assert all(0 <= v <= 1 for v in _h), f'hand = {_h}: доли должны быть от 0 до 1. Нужна доля ушедших среди соседей — среднее y_train по ним.'
assert all(close(v, w, 1e-9) for v, w in zip(_h, _mp)), f'hand = {[round(v, 3) for v in _h]}, а модель даёт {[round(v, 3) for v in _mp]}. Расстояние — по отмасштабированным признакам, соседи — 15 строк с наименьшим расстоянием, доля — среднее y_train по ним (.iloc).'
_m = need('model_p')
assert len(_m) == 5 and all(close(float(v), w, 1e-9) for v, w in zip(_m, _mp)), f'model_p не совпадает с вероятностями ухода модели для первых пяти тестовых гостей: predict_proba(Xs_test[:5])[:, 1].'
```

### hint
Расстояния от гостя `x = Xs_test[i]` до всех обучающих: `np.sqrt(((Xs_train - x) ** 2).sum(axis=1))` — numpy сам «растягивает» строку на все строки массива и вычитает её из каждой (это называется broadcasting).

### hint
`np.argsort(d)[:15]` — позиции 15 самых маленьких расстояний. Доля ушедших среди них — `y_train.iloc[...].mean()`: позиции, а не метки индекса, поэтому `.iloc`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

hand = []
for i in range(5):
    d = np.sqrt(((Xs_train - Xs_test[i]) ** 2).sum(axis=1))
    near = np.argsort(d)[:15]
    hand.append(float(y_train.iloc[near].mean()))

knn = KNeighborsClassifier(n_neighbors=15).fit(Xs_train, y_train)
model_p = [float(v) for v in knn.predict_proba(Xs_test[:5])[:, 1]]
print(hand)
print(model_p)
```

### explain
Вся «модель» kNN — это таблица обучающих гостей и правило голосования: при `fit` она ничего не вычисляет, а всю работу делает при прогнозе. Поэтому на больших таблицах kNN медленно предсказывает, а масштаб признаков определяет в нём буквально всё.
