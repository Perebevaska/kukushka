---
title: Логистическая регрессия и вероятности
lead: "Диспетчеру мало ответа «опоздает / не опоздает»: ему нужно знать, насколько рискован заказ, чтобы позвонить гостю заранее или отдать заказ вело-курьеру. Логистическая регрессия выдаёт вероятность опоздания. Учимся получать вероятности, выбирать порог тревоги, читать коэффициенты. Ранжирование по риску и проверка, можно ли вероятностям верить, — в следующем уроке."
files: [deliveries.csv]
recap:
  - "Логистическая регрессия: линейная оценка z = b₀ + w₁x₁ + … → сигмоида 1 / (1 + e⁻ᶻ) → вероятность от 0 до 1."
  - "`LogisticRegression(max_iter=2000).fit(X_train, y_train)`; предупреждение ConvergenceWarning — повод увеличить `max_iter`."
  - "`model.predict_proba(X)[:, 1]` — вероятность класса `True` (опоздания). `predict` — это «вероятность больше 0.5»."
  - "Порог тревоги выбирают под задачу: ниже порог — больше тревог и больше пойманных опозданий, но больше ложных тревог."
  - "`coef_[0]` — веса признаков: плюс повышает риск, минус снижает. Сравнивать величины весов можно только у признаков в одном масштабе (флаги 0/1)."
---

## От ответа к вероятности

Дерево и лес отвечают «да» или «нет», хотя внутри у них есть доля опозданий в листе — `predict_proba` из урока «Решающее дерево изнутри». Сегодня — модель, которая с самого начала построена вокруг вероятности: **логистическая регрессия** (logistic regression). Несмотря на слово «регрессия» в названии, это модель классификации.

Она работает в два шага.

1. Считает **линейную оценку** — взвешенную сумму признаков, как формула в Excel: $z = b_0 + w_1 \cdot \text{расстояние} + w_2 \cdot \text{позиции} + \ldots$ Веса $w$ и свободный член $b_0$ модель подбирает при обучении.
2. Превращает оценку в вероятность **сигмоидой** (sigmoid) — функцией $\dfrac{1}{1 + e^{-z}}$. Любое число она сжимает в диапазон от 0 до 1: большая положительная оценка → вероятность около 1, большая отрицательная → около 0, ноль → ровно 0.5.

::: figure sigmoid-steps
Два шага логистической регрессии и порог: признаки с весами складываются в оценку z, сигмоида переводит z в вероятность от 0 до 1, порог превращает вероятность в ответ. Точки — z = −2, 0 и 2.
:::

::: tip Аналогия
Сигмоида похожа на то, как бариста решает, хватит ли молока до вечера. Каждый признак — «за» или «против»: будний день, мало заказов с утра, свежая поставка. Он складывает их в общее впечатление z и переводит в уверенность: очень много «за» — почти наверняка хватит, поровну — «пятьдесят на пятьдесят». Но даже при очень сильных доводах он не скажет «100 %», а только «почти наверняка».
:::

```python
import numpy as np
import matplotlib.pyplot as plt

z = np.linspace(-6, 6, 100)
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(z, 1 / (1 + np.exp(-z)))
ax.axhline(0.5, color="grey", linestyle="--")
ax.set_xlabel("линейная оценка z")
ax.set_ylabel("вероятность")
ax.set_title("Сигмоида")
```

`np.exp(x)` — это $e^x$, применяется к каждому элементу массива.

::: predict
```python static
import math
for z in [-4, 0, 4]:
    print(round(1 / (1 + math.exp(-z)), 2))
```

- `0.0 | 0.5 | 1.0`
- [x] `0.02 | 0.5 | 0.98`
- `-4 | 0 | 4`

Почему: сигмоида никогда не доходит до 0 и 1 ровно, а при z = 0 даёт ровно половину. Оценки −4 и 4 одинаково далеко от нуля, поэтому вероятности симметричны: 0.02 и 1 − 0.02.
:::

{{practice: sigmoid}}

## LogisticRegression в scikit-learn

Модель устроена так же, как дерево: создать, `fit`, `predict`. Признаки — с текстовыми столбцами через `pd.get_dummies` из урока «Категориальные признаки и утечки»: линейной модели особенно важно, чтобы у категорий не было выдуманного порядка 0/1/2.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

model = LogisticRegression(max_iter=2000)
model.fit(X_train, y_train)
print(f"train {model.score(X_train, y_train):.3f}, test {model.score(X_test, y_test):.3f}")
```

Около 89 % на тесте — на уровне дерева и леса из уроков «Категориальные признаки и утечки» и «Случайный лес». На train качество даже чуть ниже, чем на тесте: у линейной модели мало «свободы», и переобучиться ей трудно. Это просто удачное разбиение — на другом `random_state` порядок может поменяться.

Обратите внимание: флаги курьера, погоды и кофейни мы оставили все, без `drop_first`, хотя в уроке «Категориальные признаки и утечки» говорили, что линейной модели лишний флаг мешает. Мешает он модели, которая подбирает веса без ограничений. `LogisticRegression` по умолчанию слегка «придерживает» веса (регуляризация, подробнее — в главе 7), и с ней полный набор флагов работает. Плюс — вес есть у каждого значения, минус — веса надо читать парами (раздел «Коэффициенты» ниже).

`max_iter` — сколько шагов разрешено сделать алгоритму, который подбирает веса. По умолчанию 100, и на наших данных этого не хватает: sklearn выведет предупреждение `ConvergenceWarning` («не сошлось»). Модель при этом обучится, но веса могут быть не лучшими. Лечение — увеличить `max_iter`.

::: note Масштаб признаков
Расстояние у нас — единицы километров, обещание — десятки минут, флаги — 0 и 1. Алгоритму подбора весов легче, когда все признаки в одном масштабе, поэтому перед логистической регрессией их обычно **стандартизируют** (приводят к среднему 0 и разбросу 1). Как это сделать аккуратно, не подглядывая в тест, — `StandardScaler` и `Pipeline` в главе 7. Пока обходимся большим `max_iter`.
:::

{{practice: p-logit, proba}}

## Вероятности и порог

Как и у дерева (урок «Решающее дерево изнутри»), `predict_proba(X)` возвращает два столбца — вероятности `False` и `True` в порядке `model.classes_`. Вероятность опоздания — второй столбец, `[:, 1]`:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)

print(model.classes_)
p = model.predict_proba(X_test)[:, 1]
print(p[:5].round(3))
print(model.predict(X_test)[:5])
print("predict — это p > 0.5:", ((p > 0.5) == model.predict(X_test)).all())
```

`predict` просто сравнивает вероятность с **порогом** 0.5. Но порог — решение бизнеса, а не модели. Если звонок гостю стоит дёшево, а опоздание без предупреждения — дорого, тревогу стоит поднимать уже при 30 %. Посмотрим, что меняется:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

for t in [0.3, 0.5, 0.7]:
    alarm = p >= t
    print(f"порог {t}: тревог {alarm.mean():.0%}, "
          f"поймали опозданий {y_test[alarm].sum() / y_test.sum():.0%}, "
          f"оправдались {y_test[alarm].mean():.0%}")
```

- **тревог** — какую долю заказов модель пометит как рискованные (столько звонков сделает диспетчер);
- **поймали опозданий** — какая доля настоящих опозданий попала в тревоги;
- **оправдались** — какая доля тревог действительно закончилась опозданием.

При пороге 0.3 модель ловит около 80 % опозданий, но звонков больше и ложных тревог больше. При 0.7 оправдываются примерно четыре тревоги из пяти, зато больше половины опозданий модель пропускает. Идеального порога нет — есть компромисс, который выбирает заказчик. Строгие названия этих метрик (precision, recall) — в главе 7.

::: predict
```python static
p = [0.15, 0.35, 0.55, 0.92]
print(sum(x >= 0.5 for x in p), sum(x >= 0.3 for x in p))
```

- `2 2`
- [x] `2 3`
- `3 2`

Почему: при пороге 0.5 тревога у двух последних заказов, при пороге 0.3 к ним добавляется заказ с 0.35. Чем ниже порог, тем больше тревог — никогда не меньше.
:::

::: quiz
При пороге 0.3 модель поднимает тревогу у 27 % доставок, ловит 81 % опозданий, оправдываются 70 % тревог. Диспетчер хочет, чтобы оправдывались не меньше 80 % тревог. Что делать?

- [x] Поднять порог: тревог станет меньше и они станут точнее, но поймаем меньшую долю опозданий
  > Выше порог — в тревоги попадают только самые рискованные доставки, поэтому они чаще оправдываются. Платим пропущенными опозданиями: на наших данных 80 % оправданий достигается около порога 0.6, а ловим там уже около 60 % опозданий.
- [ ] Опустить порог: тревог станет больше, значит, и оправданных больше
  > Оправданных тревог в штуках станет больше, а их **доля** — меньше: в тревоги попадут и менее рискованные доставки.
- [ ] Порог не поможет — нужна другая модель
  > Другая модель может сдвинуть весь компромисс, но при этой модели нужную долю оправданий даёт выбор порога.
- [ ] Поднять порог: и оправданий, и пойманных опозданий станет больше
  > Так не бывает: выше порог — меньше тревог, и часть опозданий остаётся без тревоги.
:::

{{practice: threshold}}

## Коэффициенты: что выучила модель

Веса линейной оценки лежат в `model.coef_` (по строке на класс; у нас класс один — берём `[0]`), свободный член — в `model.intercept_`. Удобно положить веса в Series с названиями признаков:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)

coefs = pd.Series(model.coef_[0], index=X.columns).sort_values()
print(coefs.round(2))
```

Как читать:

- **знак** — направление. Плюс: признак повышает линейную оценку, а значит, и вероятность опоздания. Минус — снижает. Пеший курьер и снег — плюс, авто — минус, как мы и видели в главе 4;
- **величина** — сила влияния, но сравнивать её честно можно только у признаков в одном масштабе. Флаги 0/1 между собой сравнимы: `courier_пеший` — самый сильный. А вес расстояния — «за один километр», вес обещания — «за одну минуту», и сравнивать их с флагами нельзя;
- каждый вес — эффект **при прочих равных**. Обещание (30/45/60) назначают по расстоянию, и эти признаки тесно связаны. Поэтому у `promised_min` вес отрицательный: при том же расстоянии больший запас времени снижает риск. Это не значит, что «дальние заказы опаздывают реже».

### Разберём вместе: прогноз одной доставки руками

Возьмём из теста доставку с индексом 1590: 0.8 км, одна позиция, обещали 30 минут, заказ в 21 час, пеший курьер, снег, кофейня KZN-2. Сложим линейную оценку по весам модели:

| слагаемое | вес | значение | вклад |
|---|---|---|---|
| свободный член | — | — | +1.693 |
| `distance_km` | 0.911 | 0.8 | +0.729 |
| `items` | 0.461 | 1 | +0.461 |
| `promised_min` | −0.184 | 30 | −5.508 |
| `hour` | 0.044 | 21 | +0.919 |
| `courier_пеший` | 2.488 | 1 | +2.488 |
| `weather_снег` | 1.094 | 1 | +1.094 |
| `shop_id_KZN-2` | 0.753 | 1 | +0.753 |

Флаги со значением 0 (другие курьеры, погода, кофейни) ничего не добавляют. Сумма: $z \approx$ **2.63**. Сигмоида: $1 / (1 + e^{-2.63}) \approx 1 / (1 + 0.072) \approx$ **0.93**.

::: figure logit-1590
Прогноз доставки 1590 лесенкой вкладов из таблицы: каждое слагаемое сдвигает оценку z вправо (к опозданию) или влево. Самый большой шаг влево — обещание 30 минут, но остальные вклады перевешивают: z ≈ 2.63, p ≈ 0.93.
:::

Что получилось: модель почти уверена в опоздании — пеший курьер, снег, проблемная кофейня, поздний час. Самый большой по модулю вклад — у обещания (−5.5), но это не «главный» признак: просто 30 минут — большое число, а вес «за минуту». Решают флаги, которые набрали вместе больше +4.

И ещё одна честная деталь: эта доставка на самом деле приехала **вовремя**. Вероятность 0.93 не обещает опоздание — она говорит, что из сотни таких доставок опоздали бы около 93. Эта оказалась среди остальных семи.

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)

row = X_test.loc[1590]
coefs = pd.Series(model.coef_[0], index=X.columns)
contrib = (row * coefs)[row != 0]
z = model.intercept_[0] + contrib.sum()
print(contrib.round(3))
print("z =", round(z, 2), "p =", round(1 / (1 + np.exp(-z)), 2))
print("predict_proba:", round(model.predict_proba(X_test.loc[[1590]])[0, 1], 2))
```

::: warn Веса флагов читаются парами
Флаги одного признака без `drop_first` в каждой строке в сумме дают 1: доставка либо авто, либо вело, либо пешая. Поэтому вес отдельного флага сам по себе мало что значит — смысл имеет **разница** весов внутри признака. `courier_вело` = −0.40 — это не «вело безопаснее среднего», а «вело где-то между авто (−2.09) и пешим (+2.49)»: разница пеший − вело = 2.89, вело − авто = 1.69. С `drop_first=True` вес флага сразу был бы разницей с отброшенной категорией.
:::

::: deep Веса и шансы
Отношение $p / (1 - p)$ называют **шансами** (odds): вероятность 0.8 — шансы 4 к 1. Линейная оценка $z$ — это логарифм шансов, поэтому вес $w$ означает: «+1 к признаку умножает шансы опоздания в $e^w$ раз». Вес расстояния около 0.9 → каждый километр при прочих равных умножает шансы примерно в $e^{0.9} \approx 2.5$ раза. Ещё одна тонкость: по умолчанию `LogisticRegression` немного «придерживает» веса, не давая им расти слишком сильно (регуляризация, параметр `C`) — подробнее в главе 7.
:::

{{practice: coefs, new-risk}}

## Практика

## task: sigmoid | Сигмоида | warmup

Напишите функцию `sigmoid(z)`, которая возвращает 1 / (1 + e⁻ᶻ) (для e используйте `math.exp`). Сохраните в `probs` список значений сигмоиды для z = −2, 0, 3, округлённых до 3 знаков.

### starter
```python
import math

```

### check
```python
import math as _m
f = need('sigmoid')
assert callable(f), 'sigmoid должна быть функцией: def sigmoid(z): ...'
for z in (-5, -1.5, 0, 0.7, 2):
    assert close(f(z), 1 / (1 + _m.exp(-z)), 1e-9), f'sigmoid({z}) = {f(z)}, а должно быть {1 / (1 + _m.exp(-z)):.4f}. Проверьте знак минуса в степени.'
want = [round(1 / (1 + _m.exp(-z)), 3) for z in (-2, 0, 3)]
got = need('probs')
assert len(got) == 3 and all(close(a, b) for a, b in zip(got, want)), f'probs = {got}, а нужно {want}.'
```

### hint
`return 1 / (1 + math.exp(-z))`.

### hint
`probs = [round(sigmoid(z), 3) for z in [-2, 0, 3]]`.

### solution
```python
import math

def sigmoid(z):
    return 1 / (1 + math.exp(-z))

probs = [round(sigmoid(z), 3) for z in [-2, 0, 3]]
```

## task: p-logit | Первая логистическая регрессия | warmup

Соберите программу: обучить логистическую регрессию на числовых признаках и вывести долю правильных ответов на тесте (3 знака).

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000)
model.fit(X_train, y_train)
print(round(model.score(X_test, y_test), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = ok[['distance_km', 'items', 'promised_min']]
y = ok['actual_min'] > ok['promised_min']
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = round(_LR(max_iter=2000).fit(a, c).score(b, e), 3)
assert _lines == [str(w)], f'Программа вывела {_lines}, а должна вывести одно число — долю правильных ответов на тесте.'
```

### hint
Порядок: данные → `X` и `y` → разбиение → модель → `fit` → оценка на тесте.

## task: proba | Вероятность опоздания | warmup

Обучите `LogisticRegression(max_iter=2000)` на подготовленных признаках. Сохраните в `p` вероятности опоздания для тестовых доставок (массив из одного столбца), в `mean_p` — среднюю вероятность (3 знака), в `n_alarm` — сколько тестовых доставок получили вероятность 0.5 и выше (целое число).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = _LR(max_iter=2000).fit(a, c).predict_proba(b)[:, 1]
p = _np.asarray(need('p'), dtype=float)
assert p.ndim == 1, f'p сейчас таблица формы {p.shape}. Нужен один столбец — вероятность опоздания: [:, 1].'
assert len(p) == len(w), f'В p {len(p)} значений, а тестовых доставок {len(w)}. Вероятности нужны для X_test.'
assert _np.allclose(p, w, atol=1e-4), 'p не совпадает с вероятностями опоздания. Проверьте, что взят столбец 1 (класс True), а не 0.'
assert close(need('mean_p'), round(w.mean(), 3)), f'mean_p = {need("mean_p")}, а нужно {round(w.mean(), 3)}.'
assert need('n_alarm') == int((w >= 0.5).sum()), f'n_alarm = {need("n_alarm")}. Посчитайте, у скольких вероятность ≥ 0.5.'
```

### hint
`model.predict_proba(X_test)` возвращает два столбца; вероятность опоздания — `[:, 1]`.

### hint
`(p >= 0.5).sum()` — число `True`. Оберните в `int(...)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]
mean_p = round(p.mean(), 3)
n_alarm = int((p >= 0.5).sum())
```

### explain
Средняя вероятность близка к фактической доле опозданий в тесте (около 23 %) — первый признак того, что вероятности разумные.

## task: threshold | Порог под требование диспетчера | base

Диспетчер решил поднимать тревогу, если вероятность опоздания 0.3 и выше. Для тестовых доставок посчитайте (все — 3 знака):

- `alarms` — долю доставок с тревогой;
- `caught` — долю настоящих опозданий, на которые была тревога;
- `hit` — долю тревог, которые оправдались (доставка опоздала).

Затем диспетчер требует, чтобы оправдывались не меньше 80 % тревог. Переберите пороги `np.arange(0.10, 0.90, 0.05).round(2)` и сохраните в `t80` первый (самый низкий) порог, при котором `hit` ≥ 0.8, а в `caught80` — долю пойманных опозданий при нём (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = _LR(max_iter=2000).fit(a, c).predict_proba(b)[:, 1]
al = w >= 0.3
want = {'alarms': round(al.mean(), 3), 'caught': round(e[al].sum() / e.sum(), 3), 'hit': round(e[al].mean(), 3)}
assert close(need('alarms'), want['alarms']), f'alarms = {need("alarms")}, а нужно {want["alarms"]}. Это доля всех тестовых доставок, где p ≥ 0.3.'
assert close(need('caught'), want['caught']), f'caught = {need("caught")}, а нужно {want["caught"]}. Делить нужно на число всех опозданий в тесте.'
assert close(need('hit'), want['hit']), f'hit = {need("hit")}, а нужно {want["hit"]}. Это доля опозданий среди доставок с тревогой.'
import numpy as _np
_t = next(t for t in _np.arange(0.10, 0.90, 0.05).round(2) if e[w >= t].mean() >= 0.8)
assert close(need('t80'), _t), f't80 = {need("t80")}, а нужно {_t}. Первый порог из перебора, где доля оправдавшихся тревог не меньше 0.8.'
assert close(need('caught80'), round(e[w >= _t].sum() / e.sum(), 3)), f'caught80 = {need("caught80")}. Доля пойманных опозданий при пороге t80.'
```

### hint
Маска тревог: `alarm = p >= 0.3`. Опоздания с тревогой: `y_test[alarm]`.

### hint
`caught` — `y_test[alarm].sum() / y_test.sum()`, `hit` — `y_test[alarm].mean()`.

### hint
Для `t80`: `for t in np.arange(0.10, 0.90, 0.05).round(2):` — посчитайте `hit` при пороге `t` и остановитесь (`break`) на первом, где он не меньше 0.8.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]
alarm = p >= 0.3
alarms = round(alarm.mean(), 3)
caught = round(y_test[alarm].sum() / y_test.sum(), 3)
hit = round(y_test[alarm].mean(), 3)

import numpy as np
for t in np.arange(0.10, 0.90, 0.05).round(2):
    if y_test[p >= t].mean() >= 0.8:
        t80 = t
        caught80 = round(y_test[p >= t].sum() / y_test.sum(), 3)
        break
```

### explain
При пороге 0.3 тревога у 27 % доставок; она накрывает 81 % настоящих опозданий, и 70 % тревог оправдываются. Требование «80 % оправданий» впервые выполняется при пороге 0.6 — и ловим тогда лишь 60 % опозданий: за точность тревог платим пропущенными опозданиями. Заметьте и неровность: при 0.65 доля оправданий снова опускается ниже 0.8 — на нескольких сотнях тестовых доставок она «шумит». Какой порог лучше — вопрос цены: что дороже, лишний звонок гостю или опоздание без предупреждения.

## task: coefs | Знаки коэффициентов | base

Сохраните в `coefs` веса модели — Series с названиями признаков в индексе, отсортированную по возрастанию. В `top_up` — название признака с самым большим положительным весом, в `top_down` — с самым отрицательным. В `snow_sign` — строку `"+"` или `"-"`: повышает или понижает снег риск опоздания по мнению модели.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
w = _pd.Series(_LR(max_iter=2000).fit(a, c).coef_[0], index=X.columns).sort_values()
s = need('coefs', _pd.Series)
assert set(s.index) == set(X.columns), 'В индексе coefs должны быть названия признаков: index=X.columns.'
assert list(s.index) == list(w.index), 'coefs не отсортирована по возрастанию: .sort_values().'
assert (s - w).abs().max() < 1e-3, 'Значения coefs не совпадают с model.coef_[0].'
assert need('top_up') == w.index[-1], f'top_up = {need("top_up")!r}. Это последний элемент отсортированной Series.'
assert need('top_down') == w.index[0], f'top_down = {need("top_down")!r}. Это первый элемент отсортированной Series.'
assert need('snow_sign') == ('+' if w['weather_снег'] > 0 else '-'), f'snow_sign = {need("snow_sign")!r}. Посмотрите на знак веса weather_снег.'
```

### hint
`pd.Series(model.coef_[0], index=X.columns).sort_values()`.

### hint
Первый и последний элементы индекса: `coefs.index[0]`, `coefs.index[-1]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)
coefs = pd.Series(model.coef_[0], index=X.columns).sort_values()
top_up = coefs.index[-1]
top_down = coefs.index[0]
snow_sign = "+" if coefs["weather_снег"] > 0 else "-"
```

### explain
Модель сама пришла к выводам главы 4: пеший курьер и снег повышают риск, авто — снижает. Но веса флагов и вес расстояния напрямую не сравнить: у них разные единицы.

## task: new-risk | Риск для новых заказов | plus

Оцените вероятность опоздания для трёх новых заказов. Признаки новых заказов нужно привести к столбцам обучающей таблицы, как в уроке «Категориальные признаки и утечки». Сохраните в `risk` **список** из трёх вероятностей опоздания (2 знака) в порядке заказов.

| distance_km | items | promised_min | hour | courier | weather | shop_id |
|---|---|---|---|---|---|---|
| 1.5 | 3 | 30 | 18 | пеший | снег | KZN-2 |
| 1.5 | 3 | 30 | 18 | вело | снег | KZN-2 |
| 6.0 | 2 | 45 | 12 | авто | ясно | PRM-1 |

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)

new = pd.DataFrame({
    "distance_km": [1.5, 1.5, 6.0], "items": [3, 3, 2], "promised_min": [30, 30, 45], "hour": [18, 18, 12],
    "courier": ["пеший", "вело", "авто"], "weather": ["снег", "снег", "ясно"], "shop_id": ["KZN-2", "KZN-2", "PRM-1"],
})

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
y = ok['actual_min'] > ok['promised_min']
X = _pd.get_dummies(ok[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
a, b, c, e = _tts(X, y, test_size=0.25, random_state=42)
m = _LR(max_iter=2000).fit(a, c)
nw = _pd.DataFrame({'distance_km': [1.5, 1.5, 6.0], 'items': [3, 3, 2], 'promised_min': [30, 30, 45], 'hour': [18, 18, 12],
                    'courier': ['пеший', 'вело', 'авто'], 'weather': ['снег', 'снег', 'ясно'], 'shop_id': ['KZN-2', 'KZN-2', 'PRM-1']})
nx = _pd.get_dummies(nw, dtype=int).reindex(columns=a.columns, fill_value=0)
want = [round(float(v), 2) for v in m.predict_proba(nx)[:, 1]]
got = need('risk')
assert len(got) == 3, f'В risk {len(got)} значений, а заказов три.'
got = [float(v) for v in got]
assert all(close(x, z, 0.006) for x, z in zip(got, want)), f'risk = {got}, а нужно {want}. Проверьте, что столбцы новых заказов совпадают со столбцами X_train (reindex) и что взята вероятность класса True.'
```

### hint
`pd.get_dummies(new, dtype=int)` создаст только те столбцы, что встречаются в трёх заказах. Остальные добавит `.reindex(columns=X_train.columns, fill_value=0)`.

### hint
`[round(float(v), 2) for v in model.predict_proba(new_X)[:, 1]]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
X = pd.get_dummies(ok[["distance_km", "items", "promised_min", "hour", "courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)

new = pd.DataFrame({
    "distance_km": [1.5, 1.5, 6.0], "items": [3, 3, 2], "promised_min": [30, 30, 45], "hour": [18, 18, 12],
    "courier": ["пеший", "вело", "авто"], "weather": ["снег", "снег", "ясно"], "shop_id": ["KZN-2", "KZN-2", "PRM-1"],
})
new_X = pd.get_dummies(new, dtype=int).reindex(columns=X_train.columns, fill_value=0)
risk = [round(float(v), 2) for v in model.predict_proba(new_X)[:, 1]]
```

### explain
Первые два заказа отличаются только типом курьера: вело заметно снижает риск, но в снег при обещании 30 минут он всё равно высокий. Третий заказ далёкий, но на авто и с запасом по времени — почти безопасен. Без `reindex` модель бы не приняла таблицу: в трёх заказах встречаются не все категории.
