---
title: "Своя модель: класс с fit и predict"
lead: "Формула весов уже есть — осталось упаковать её так, как это делает sklearn: в класс с методами `fit` и `predict`. Класс, `self` и атрибуты вы уже писали для своего трансформера в главе 7 — модель устроена так же, только вместо `transform` у неё `predict`. Делаем свою регрессию и модели-правила, которые работают в `cross_val_score` и `Pipeline`."
files: [deliveries.csv]
recap:
  - "Своя модель — класс с методами `fit(self, X, y)` (учит, сохраняет выученное в атрибуты `self.coef_`, возвращает `self`) и `predict(self, X)` (читает атрибуты). `self` — сам объект."
  - "Родители `(RegressorMixin, BaseEstimator)` дают `score` и `get_params`: такая модель работает в `cross_val_score`, `Pipeline`, `GridSearchCV`."
  - "Бизнес-правило («среднее по типу курьера», «столько-то минут на километр») тоже оформляют как модель и сравнивают с настоящими моделями на тех же фолдах."
---

Веса линейной регрессии мы уже считаем нормальным уравнением (урок «Как обучается линейная регрессия»). Здесь упакуем этот расчёт в класс.

## Зачем модели класс

Нормальное уравнение уложилось в три строки. Но чтобы пользоваться им как `LinearRegression`, этого мало. Нужно обучить модель один раз, потом прогнозировать на новых заказах, а ещё отдать её в `cross_val_score` или `Pipeline`. Для этого веса надо где-то хранить, а у модели должны быть те же «кнопки», что у моделей sklearn: `fit(X, y)` учит и запоминает, `predict(X)` применяет выученное.

Вы это уже делали. В уроке «Свои шаги конвейера: порядок категорий, функции и свой класс» главы 7 был раздел «Класс за пять минут» (класс, объект, атрибут, метод, `self`, родитель), а потом свой трансформер `(TransformerMixin, BaseEstimator)`: `fit` запоминал средние по городам в атрибуты с `_` на конце и возвращал `self`. Модель устроена так же, только вместо `transform` у неё `predict`, а вместо `TransformerMixin` — `RegressorMixin`. Заодно станет видно, что внутри `LinearRegression` нет ничего, кроме формулы нормального уравнения и аккуратной упаковки.

### Сначала на игрушке

Четыре заказа из игрушки урока «Как обучается линейная регрессия»: $x = 1, 2, 3, 4$ км, $y = 3, 4, 8, 9$ минут. Мы уже знаем ответ: свободный член 0.5, вес 2.2. Значит, обученная модель должна:

- после `fit` хранить `intercept_ = 0.5` и `coef_ = [2.2]`;
- для заказа на 5 км выдать 0.5 + 2.2 · 5 = **11.5** минуты, для 0 км — **0.5**.

```python
import numpy as np

class MyLinearRegression:
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])                 # столбец единиц
        w = np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))
        self.intercept_ = w[0]               # запомнили свободный член
        self.coef_ = w[1:]                   # и веса признаков
        return self                          # чтобы писать .fit(...).predict(...)

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_

X = np.array([[1.0], [2.0], [3.0], [4.0]])
y = np.array([3.0, 4.0, 8.0, 9.0])
model = MyLinearRegression()                 # собрали машину по чертежу
model.fit(X, y)                              # настроили
print(round(model.intercept_, 3), model.coef_.round(3))
print(model.predict(np.array([[5.0], [0.0]])).round(2))
```

**Что здесь происходит:** всё как в трансформере из главы 7. `fit` решает нормальное уравнение и кладёт результат в атрибуты `self.intercept_` и `self.coef_`, `predict` их читает, `return self` позволяет писать цепочкой `MyLinearRegression().fit(X, y).predict(X_new)`. `np.asarray(X, dtype=float)` нужен, чтобы модель принимала и DataFrame, и список, и массив numpy.

::: note Если подзабыли, как устроен класс
Подробно с примером чека — в разделе «Класс за пять минут» урока «Свои шаги конвейера: порядок категорий, функции и свой класс» главы 7. Здесь — коротко, на нашей модели:

- `class MyLinearRegression:` — объявление **класса**, чертежа для объектов. Имена классов пишут с большой буквы, слова слитно.
- `def fit(self, X, y):` внутри класса — **метод**, функция, которая принадлежит объекту. Первый параметр `self` — сам объект: при вызове `model.fit(X, y)` Python сам подставит `model` на место `self`, поэтому мы передаём только `X` и `y`.
- `self.intercept_ = w[0]` — **атрибут**, переменная, прикреплённая к объекту. Обычная переменная `w` исчезнет, когда `fit` закончит работу, а атрибут останется, и `predict` его прочитает. Подчёркивание в конце имени — договорённость sklearn: так называют всё, что выучено в `fit`.
- `model = MyLinearRegression()` — создание объекта по чертежу. Скобки — как у вызова функции.

Класс — как чертёж кофемашины, а объект — конкретная машина в кофейне: настроили машину на Ленина (`fit`), а машина на Мира, собранная по тому же чертежу, осталась ненастроенной.
:::

**Что получилось:** 0.5 и [2.2], прогнозы 11.5 и 0.5 — ровно то, что мы посчитали руками.

::: figure class-objects
Один класс — много объектов. `a.fit` записывает выученное в атрибуты объекта `a`; объект `b` собран по тому же чертежу, но его не обучали, и атрибутов у него нет.
:::

{{practice: p-class, my-class}}

### Совместимость со sklearn

`cross_val_score`, `GridSearchCV` и `Pipeline` перед обучением **копируют** модель, чтобы на каждом фолде учить чистую копию. Для копии нужен метод `get_params`, а для оценки по умолчанию — метод `score`. Писать их самим не нужно — их дают родители, как у трансформера в главе 7: `BaseEstimator` — `get_params`, `RegressorMixin` — `score`, то есть R² из главы 6. Миксин первым, `BaseEstimator` последним — тот же порядок, что в главе 7.

::: deep Почему порядок родителей важен
Миксин сообщает sklearn, что это регрессия. Если поставить `BaseEstimator` первым, Python раньше найдёт его служебные «теги», и `sklearn.base.is_regressor` ответит `False`: модель обучится, но инструменты, которые по-разному ведут себя для регрессии и классификации, её не узнают.
:::

```python
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score

class MyLinearRegression(RegressorMixin, BaseEstimator):     # родители — в скобках
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        w = np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))
        self.intercept_, self.coef_ = w[0], w[1:]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]

mine = MyLinearRegression().fit(X, y)
print("свои веса:", round(mine.intercept_, 3), mine.coef_.round(3))
print("R², свой и sklearn:", round(mine.score(X, y), 4), round(LinearRegression().fit(X, y).score(X, y), 4))
cv_mine = -cross_val_score(MyLinearRegression(), X, y, cv=5, scoring="neg_mean_absolute_error")
cv_sk = -cross_val_score(LinearRegression(), X, y, cv=5, scoring="neg_mean_absolute_error")
print("MAE по фолдам, свой:   ", cv_mine.round(2))
print("MAE по фолдам, sklearn:", cv_sk.round(2))
```

**Что здесь происходит:**

- `class MyLinearRegression(RegressorMixin, BaseEstimator)` — тот же класс, плюс два родителя. Свой код не изменился.
- `mine.score(X, y)` — метод, который мы не писали: он пришёл от `RegressorMixin`, вызывает наш `predict` и считает R².
- `cross_val_score(MyLinearRegression(), ...)` — кросс-валидация из главы 6. Она пять раз копирует модель (через `get_params` от `BaseEstimator`), учит копию на четырёх частях и проверяет на пятой. Минус перед ней нужен, потому что sklearn возвращает MAE со знаком минус («больше — лучше»).

**Как читать результат.** Веса — 16.013 минуты базово, 3.871 на километр, 1.608 на позицию, 13.622 надбавка пешему, как в разделе выше. R² у обеих моделей 0.5053, MAE по пяти фолдам совпадает до сотых: от 5.56 до 6.23 минуты. Значит, своя модель встраивается в инструменты sklearn наравне с родными. Так же пишут и модели, которых в sklearn нет: правило «как неделю назад», правило бизнеса, обёртку над чужой библиотекой. Достаточно `fit` и `predict`, и их можно сравнивать с остальными на тех же фолдах.

::: quiz
Создали две модели: `a = MyLinearRegression()` и `b = MyLinearRegression()`, затем обучили только одну: `a.fit(X, y)`. Что будет при вызове `b.predict(X)`?

- [x] Ошибка `AttributeError`: у `b` нет атрибута `coef_`, ведь `fit` для неё не вызывали
  > Атрибуты живут в своём объекте. `a.fit` записал `coef_` в `a`, а `b` — отдельная «машина», и её никто не настраивал.
- [ ] `b` выдаст те же прогнозы, что `a`: класс один и тот же
  > Класс общий, это чертёж. Выученные веса хранятся в каждом объекте отдельно.
- [ ] `b` выдаст нули: веса по умолчанию нулевые
  > В нашем классе нет весов по умолчанию. Атрибут `coef_` появляется только внутри `fit`.
- [ ] `b.predict` сам вызовет `fit` на тех же данных
  > `predict` не знает, на каких данных учиться, и ничего не вызывает сам. Он только читает `coef_` и `intercept_`.
:::

::: warn Типичные ошибки
- **Забыли `self` в определении метода.** `def fit(X, y):` → при вызове `model.fit(X, y)` ошибка `TypeError: ... fit() takes 2 positional arguments but 3 were given`: Python передал объект третьим аргументом, а места для него нет.
- **Веса записали в обычную переменную.** `coef_ = w[1:]` вместо `self.coef_ = w[1:]` → `predict` падает с `AttributeError: 'MyLinearRegression' object has no attribute 'coef_'`. Переменная исчезла вместе с концом `fit`.
- **`predict` до `fit`.** Та же `AttributeError`. У моделей sklearn в этом случае своя ошибка `NotFittedError`, смысл тот же.
- **Нет родителя `BaseEstimator`.** `cross_val_score` падает с длинной ошибкой: в ней есть слова `Make sure to inherit from BaseEstimator`. Добавьте родителей `(RegressorMixin, BaseEstimator)` в этом порядке.
- **`fit` ничего не возвращает.** Тогда `MyLinearRegression().fit(X, y).predict(X)` падает с `AttributeError: 'NoneType' object has no attribute 'predict'`. Последняя строка `fit` — `return self`.
:::

{{practice: fix-class, class-cv}}

## Правило бизнеса — тоже модель

Прежде чем радоваться модели, её сравнивают с тем, как решают без неё: «обещаем всем среднее время», «пешему курьеру — как обычно у пеших». Такое правило удобно оформить тем же классом с `fit` и `predict`: тогда оно проходит через `cross_val_score` на тех же фолдах, и сравнение честное. Самое простое правило — «всем одно среднее»:

```python
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin

class MeanModel(RegressorMixin, BaseEstimator):
    """Правило «всем одно среднее»."""
    def fit(self, X, y):
        self.mean_ = float(np.mean(y))         # выучили одно число
        return self

    def predict(self, X):
        return np.full(len(X), self.mean_)     # по одному и тому же числу на каждую строку

X = np.array([[1.0], [2.0], [3.0], [4.0]])
y = np.array([3.0, 4.0, 8.0, 9.0])
m = MeanModel().fit(X, y)
print(m.mean_, m.predict(X), round(m.score(X, y), 3))
```

**Что здесь происходит:**

- `fit` выучил одно число — среднее 6.0; признаки `X` правило не читает, но принимать их обязано: так его вызывает `cross_val_score`.
- `np.full(len(X), self.mean_)` — массив длины `len(X)`, заполненный одним значением: по прогнозу на каждую строку.
- `score` пришёл от `RegressorMixin` и дал R² = 0.0 — так и должно быть: R² из главы 6 как раз и сравнивает модель со средним. Положительный R² значит «лучше, чем всем среднее».

Правило может учить и больше одного числа: среднее по группам (`groupby` в `fit`, `map` в `predict`) или «минут на километр». Главное — всё выученное хранить в атрибутах с `_`, а в `predict` только читать их. В sklearn для простых ориентиров есть готовый `DummyRegressor`, но своё правило бизнеса за вас никто не напишет.

{{practice: mean-model, group-mean}}

## Практика

## task: p-class | Модель «минут на километр» | warmup

Соберите простую модель с интерфейсом sklearn — правило диспетчера «столько-то минут на километр». `fit` делит все минуты на все километры и запоминает это число в `rate_`, `predict` умножает на него километры новых заказов. Код обучает модель на трёх доставках (2, 3 и 5 км; 16, 21 и 43 минуты) и печатает прогноз для заказов на 4 и 10 км.

### parsons
```python
import numpy as np
class PerKmModel:
    def fit(self, km, minutes):
        self.rate_ = float(np.sum(minutes) / np.sum(km))
        return self
    def predict(self, km):
        return np.asarray(km) * self.rate_
model = PerKmModel().fit([2, 3, 5], [16, 21, 43])
print(model.predict([4, 10]).tolist())
```

### check
```python
assert _lines == ['[32.0, 80.0]'], f'Сейчас вывод: {_lines}. Всего 80 минут на 10 км — 8 минут на километр, значит прогнозы 4 · 8 = 32.0 и 10 · 8 = 80.0.'
```

### hint
Сначала импорт и строка `class ...:`, внутри — два метода с отступом. `return self` — последняя строка `fit`.

### hint
`self.rate_` должен появиться в `fit` раньше, чем его прочитает `predict`. Обучение и печать идут после класса, без отступа.

### explain
Это полноценная модель в смысле sklearn: `fit` учится (запоминает одно число, 80 / 10 = 8 минут на км), `predict` применяет выученное. Правила, которыми уже пользуется бизнес, удобно оформлять так же: тогда их можно поставить в одну таблицу сравнения с настоящими моделями. Если модель не обыгрывает правило диспетчера, она не нужна. Для самого простого ориентира — «всем одно среднее» — в sklearn есть готовый `DummyRegressor`.

## task: fix-class | Почините модель | warmup

Стажёр написал модель «минут на километр» из задачи «Модель «минут на километр»», но код падает. В нём три ошибки из блока «Типичные ошибки». Исправьте класс так, чтобы код ниже работал, и сохраните прогнозы для заказов на 4 и 10 км в `pred` (список или массив).

### starter
```python
import numpy as np

class PerKmModel:
    def fit(km, minutes):
        rate_ = float(np.sum(minutes) / np.sum(km))

    def predict(self, km):
        return np.asarray(km) * self.rate_

model = PerKmModel().fit([2, 3, 5], [16, 21, 43])
pred = model.predict([4, 10])
print(pred)
```

### check
```python
import numpy as _np
C = need('PerKmModel')
_m = C()
_r = _m.fit([1, 1], [5, 7])
assert _r is _m, 'fit должен возвращать сам объект: последняя строка fit — return self. Иначе цепочка PerKmModel().fit(...).predict(...) получает None.'
assert hasattr(_m, 'rate_') and close(_m.rate_, 6.0), 'После fit у объекта должен появиться атрибут rate_: self.rate_ = ...'
assert _np.allclose(need('pred'), [32.0, 80.0]), f'pred = {need("pred")}, а нужно [32.0, 80.0].'
```

### hint
Первая ошибка — в заголовке `fit`: Python передаёт объект первым аргументом, а места для него нет. Вторая — выученное число записано в обычную переменную, которая исчезнет после `fit`.

### hint
`def fit(self, km, minutes):`, внутри `self.rate_ = ...`, последней строкой — `return self`.

### solution
```python
import numpy as np

class PerKmModel:
    def fit(self, km, minutes):
        self.rate_ = float(np.sum(minutes) / np.sum(km))
        return self

    def predict(self, km):
        return np.asarray(km) * self.rate_

model = PerKmModel().fit([2, 3, 5], [16, 21, 43])
pred = model.predict([4, 10])
print(pred)
```

### explain
Ошибки чинятся по очереди, и каждая даёт своё сообщение: без `self` — `TypeError: PerKmModel.fit() takes 2 positional arguments but 3 were given`, без `return self` — `AttributeError: 'NoneType' object has no attribute 'predict'`, без `self.` перед `rate_` — `AttributeError: 'PerKmModel' object has no attribute 'rate_'`. Прогнозы 32 и 80 минут: 80 минут на 10 км — 8 минут на километр.

## task: my-class | Своя линейная регрессия | base

Напишите класс `MyLinearRegression` с двумя методами:

- `fit(self, X, y)` — добавляет столбец единиц, решает нормальное уравнение через `np.linalg.solve`, сохраняет свободный член в `self.intercept_`, веса признаков — в `self.coef_` и возвращает `self`;
- `predict(self, X)` — возвращает `X @ coef_ + intercept_`.

Обучите модель на доставках из заготовки (`X` — три признака, `y` — минуты) и сохраните объект в `model`. В `w_all` сохраните свободный член и веса одним массивом (`np.r_[...]`, 3 знака). В `pred_new` — прогнозы для двух новых заказов из `new` (1 знак). Готовый `LinearRegression` не используйте.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]
new = np.array([[3.5, 2, 1],      # 3.5 км, 2 позиции, пеший
                [8.0, 4, 0]])     # 8 км, 4 позиции, не пеший

class MyLinearRegression:
    ...

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
assert 'LinearRegression(' not in _code.replace('MyLinearRegression(', ''), 'Здесь нужен свой класс: готовый LinearRegression не используйте, решите нормальное уравнение через np.linalg.solve.'
C = need('MyLinearRegression')
_m = C()
assert hasattr(_m, 'fit') and hasattr(_m, 'predict'), 'У класса должны быть методы fit и predict.'
_r = _m.fit(_np.array([[1.0], [2.0], [3.0], [4.0]]), _np.array([3.0, 4.0, 8.0, 9.0]))
assert _r is _m, 'fit должен возвращать сам объект: последняя строка fit — return self.'
assert hasattr(_m, 'intercept_') and hasattr(_m, 'coef_'), 'После fit у объекта должны появиться атрибуты intercept_ и coef_ (через self.).'
assert close(float(_m.intercept_), 0.5, 1e-6) and _np.allclose(_m.coef_, [2.2]), f'На игрушке из урока (x = 1..4, y = 3, 4, 8, 9) нужно intercept_ = 0.5, coef_ = [2.2], а получилось {_m.intercept_}, {_m.coef_}. Не забыт ли столбец единиц?'
assert _np.allclose(_m.predict(_np.array([[5.0], [0.0]])), [11.5, 0.5]), 'predict на игрушке должен дать 11.5 и 0.5: X @ coef_ + intercept_.'
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy(); ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk']]; lr = _LR().fit(X0, ok['actual_min'])
mm = need('model')
assert isinstance(mm, C), 'model — объект вашего класса MyLinearRegression, обученный на X и y.'
assert _np.allclose(_np.r_[mm.intercept_, mm.coef_], _np.r_[lr.intercept_, lr.coef_], atol=1e-6), 'Веса model не совпадают с правильными. Обучите model на X и y из заготовки.'
assert _np.allclose(need('w_all'), _np.round(_np.r_[lr.intercept_, lr.coef_], 3)), f'w_all = {need("w_all")}. Свободный член первым, затем веса, 3 знака.'
pn = lr.predict(_pd.DataFrame([[3.5, 2, 1], [8.0, 4, 0]], columns=X0.columns)).round(1)
assert _np.allclose(need('pred_new'), pn), f'pred_new = {need("pred_new")}, а нужно {pn}.'
```

### hint
Тело `fit` — код из раздела «Откуда берутся веса»: `X1` со столбцом единиц и `np.linalg.solve(X1.T @ X1, X1.T @ y)`. Результат разложите по атрибутам через `self.`.

### hint
`self.intercept_ = w[0]`, `self.coef_ = w[1:]`, `return self`. В начале `fit` и `predict` превратите вход в массив: `np.asarray(X, dtype=float)`.

### hint
После класса: `model = MyLinearRegression().fit(X, y)`, `w_all = np.r_[model.intercept_, model.coef_].round(3)`, `pred_new = model.predict(new).round(1)`.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]
new = np.array([[3.5, 2, 1],      # 3.5 км, 2 позиции, пеший
                [8.0, 4, 0]])     # 8 км, 4 позиции, не пеший

class MyLinearRegression:
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        w = np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))
        self.intercept_ = w[0]
        self.coef_ = w[1:]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_

model = MyLinearRegression().fit(X, y)
w_all = np.r_[model.intercept_, model.coef_].round(3)
pred_new = model.predict(new).round(1)
print(w_all, pred_new)
```

### explain
Проверка сначала обучает ваш класс на игрушке из урока, где ответ известен заранее (0.5 и 2.2), а потом сверяет его с `LinearRegression` на доставках. Так тестируют любую свою модель: маленький пример с ответом, посчитанным руками, ловит ошибки, которые на большой таблице не видны. Прогнозы: 46.4 минуты для пешего курьера на 3.5 км и 53.4 минуты для 8 км на машине или велосипеде. Если бы вы забыли `return self`, цепочка `MyLinearRegression().fit(X, y)` вернула бы `None`, и в `model` оказался бы не объект, а пустое значение.

## task: mean-model | Обыгрывает ли модель среднее | warmup

Напишите `MeanModel` — правило «всем одно среднее» с родителями `(RegressorMixin, BaseEstimator)`, как в разделе «Правило бизнеса — тоже модель». На доставках из заготовки посчитайте MAE на 5 фолдах (со сменой знака на плюс) для `MeanModel` — `cv_mean` — и для `LinearRegression` — `cv_lin`. В `gain` — на сколько минут линейная модель в среднем по фолдам точнее правила (разность средних MAE, 2 знака).

### setup
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]]
y = ok["actual_min"]
```

### starter
```python
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score

# готово, как в теории: X, y (доставки)

class MeanModel(RegressorMixin, BaseEstimator):
    ...

```

### check
```python
import numpy as _np
from sklearn.base import BaseEstimator as _BE
from sklearn.dummy import DummyRegressor as _DR
from sklearn.linear_model import LinearRegression as _LR
from sklearn.model_selection import cross_val_score as _cvs
C = need('MeanModel')
assert issubclass(C, _BE), 'Добавьте родителей: class MeanModel(RegressorMixin, BaseEstimator).'
_m = C().fit(_np.zeros((4, 1)), _np.array([3.0, 4.0, 8.0, 9.0]))
assert _np.allclose(_m.predict(_np.zeros((3, 1))), 6.0), 'На игрушке y = 3, 4, 8, 9 predict должен вернуть по 6.0 на каждую строку: np.full(len(X), self.mean_).'
X0, y0 = need('X'), need('y')
rm = -_cvs(_DR(), X0, y0, cv=5, scoring='neg_mean_absolute_error')
rl = -_cvs(_LR(), X0, y0, cv=5, scoring='neg_mean_absolute_error')
cm = _np.asarray(need('cv_mean'), dtype=float)
assert cm.shape == (5,) and (cm > 0).all(), f'cv_mean — пять положительных MAE: минус перед cross_val_score, cv=5. Сейчас {cm.round(2).tolist()}.'
assert _np.allclose(cm, rm), f'cv_mean = {cm.round(2).tolist()}, а нужно {rm.round(2).tolist()}.'
assert _np.allclose(need('cv_lin'), rl), f'cv_lin = {_np.round(need("cv_lin"), 2).tolist()}, а нужно {rl.round(2).tolist()}.'
assert close(need('gain'), round(float(rm.mean() - rl.mean()), 2), 0.0051), f'gain = {need("gain")}: cv_mean.mean() - cv_lin.mean().'
```

### hint
Класс — тот же, что в разделе «Правило бизнеса — тоже модель»: в `fit` — `self.mean_ = float(np.mean(y))` и `return self`, в `predict` — `np.full(len(X), self.mean_)`.

### hint
`cv_mean = -cross_val_score(MeanModel(), X, y, cv=5, scoring="neg_mean_absolute_error")`, то же для `LinearRegression()`; `gain = round(float(cv_mean.mean() - cv_lin.mean()), 2)`.

### solution
```python
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score

class MeanModel(RegressorMixin, BaseEstimator):
    def fit(self, X, y):
        self.mean_ = float(np.mean(y))
        return self

    def predict(self, X):
        return np.full(len(X), self.mean_)

cv_mean = -cross_val_score(MeanModel(), X, y, cv=5, scoring="neg_mean_absolute_error")
cv_lin = -cross_val_score(LinearRegression(), X, y, cv=5, scoring="neg_mean_absolute_error")
gain = round(float(cv_mean.mean() - cv_lin.mean()), 2)
print(cv_mean.round(2), cv_lin.round(2), gain)
```

### explain
Правило «всем среднее» ошибается в среднем на 8.24 минуты, линейная регрессия — на 5.91: модель точнее на 2.33 минуты, и так на каждом из пяти фолдов. Проверка сверяет ваш класс с готовым `DummyRegressor` из sklearn — он делает ровно то же самое. Своя версия нужна, когда правило сложнее среднего, — как в следующей задаче.

## task: group-mean | Правило «как обычно у этого курьера» | base

Диспетчер обещает время по типу курьера: «как обычно у пеших», «как обычно у авто». Оформите это правило моделью `CourierMean(RegressorMixin, BaseEstimator)`: `fit(X, y)` запоминает в `self.means_` среднее время по значениям столбца `courier` таблицы `X`, `predict(X)` подставляет каждому заказу среднее его типа курьера (массив чисел). В заготовке `Xc` — таблица из одного столбца `courier`, `y` — минуты. Сохраните `cv_courier` — MAE на 5 фолдах (со сменой знака), `cv_courier_mean` — их среднее (2 знака), `walk_mean` — выученное среднее для пеших на всех данных (1 знак) и `beats_mean` — обыгрывает ли правило «всем среднее» (8.24 минуты из прошлой задачи): `True/False`.

### setup
```python
import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
Xc = ok[["courier"]]
y = ok["actual_min"]
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import cross_val_score

# готово, как в теории: Xc (столбец courier), y (минуты)

class CourierMean(RegressorMixin, BaseEstimator):
    ...

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.base import BaseEstimator as _BE
from sklearn.model_selection import cross_val_score as _cvs
C = need('CourierMean')
assert issubclass(C, _BE), 'Добавьте родителей: class CourierMean(RegressorMixin, BaseEstimator).'
_tx = _pd.DataFrame({'courier': ['а', 'б', 'а', 'б']}); _ty = _pd.Series([10.0, 30.0, 20.0, 50.0])
_m = C().fit(_tx, _ty)
assert hasattr(_m, 'means_'), 'После fit должен появиться атрибут means_: self.means_ = ...'
_p = _np.asarray(_m.predict(_pd.DataFrame({'courier': ['б', 'а']})), dtype=float)
assert _np.allclose(_p, [40.0, 15.0]), f'На игрушке (а: 10 и 20, б: 30 и 50) predict для [б, а] должен дать [40.0, 15.0], а дал {_p.tolist()}.'
X0, y0 = need('Xc'), need('y')
def _ref_cv():
    out = []
    from sklearn.model_selection import KFold as _KF
    for tr, te in _KF(5).split(X0):
        mm = _pd.Series(y0.values[tr]).groupby(X0['courier'].values[tr]).mean()
        out.append(_np.abs(X0['courier'].iloc[te].map(mm).values - y0.values[te]).mean())
    return _np.array(out)
ref = _ref_cv()
cc = _np.asarray(need('cv_courier'), dtype=float)
assert cc.shape == (5,) and (cc > 0).all(), f'cv_courier — пять положительных MAE, сейчас {cc.round(2).tolist()}.'
assert _np.allclose(cc, ref), f'cv_courier = {cc.round(2).tolist()}, а нужно {ref.round(2).tolist()}.'
assert close(need('cv_courier_mean'), round(float(ref.mean()), 2), 0.0051), f'cv_courier_mean = {need("cv_courier_mean")}.'
wm = round(float(y0[X0['courier'] == 'пеший'].mean()), 1)
assert close(need('walk_mean'), wm, 0.051), f'walk_mean = {need("walk_mean")}: среднее время пеших, которое модель выучила на всех данных.'
assert bool(need('beats_mean')) == bool(ref.mean() < 8.24), 'beats_mean: меньше ли средняя MAE правила, чем 8.24 у «всем среднее»?'
```

### hint
В `fit`: `self.means_ = pd.Series(np.asarray(y, dtype=float), index=X.index).groupby(X["courier"]).mean()` — среднее `y` по группам курьера (Series с ключами «авто», «вело», «пеший»). `return self`.

### hint
В `predict`: `X["courier"].map(self.means_).to_numpy(dtype=float)` — каждому заказу его среднее. Затем `cv_courier = -cross_val_score(CourierMean(), Xc, y, cv=5, scoring="neg_mean_absolute_error")`, `walk_mean = round(float(CourierMean().fit(Xc, y).means_["пеший"]), 1)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import cross_val_score

class CourierMean(RegressorMixin, BaseEstimator):
    def fit(self, X, y):
        y = pd.Series(np.asarray(y, dtype=float), index=X.index)
        self.means_ = y.groupby(X["courier"]).mean()
        return self

    def predict(self, X):
        return X["courier"].map(self.means_).to_numpy(dtype=float)

cv_courier = -cross_val_score(CourierMean(), Xc, y, cv=5, scoring="neg_mean_absolute_error")
cv_courier_mean = round(float(cv_courier.mean()), 2)
walk_mean = round(float(CourierMean().fit(Xc, y).means_["пеший"]), 1)
beats_mean = bool(cv_courier_mean < 8.24)
print(cv_courier.round(2), cv_courier_mean, walk_mean, beats_mean)
```

### explain
Правило выучило три числа: около 32.7 минуты у авто, 33.1 у вело и 39.9 у пеших. Среднее MAE по фолдам — 8.07 минуты: «всем среднее» (8.24) оно обыгрывает, но совсем немного, а линейная регрессия с расстоянием (5.91) — заметно точнее. Вывод для «Зерна»: тип курьера сам по себе почти ничего не объясняет, главное — расстояние. `pd.Series(..., index=X.index)` в `fit` нужен, чтобы `groupby` сопоставил минуты и курьеров по строкам: на каждом фолде `cross_val_score` подаёт свой кусок таблицы.

## task: class-cv | Своя модель в инструментах sklearn | plus

Сделайте `MyLinearRegression` совместимой со sklearn: добавьте родителей `RegressorMixin` и `BaseEstimator` (в этом порядке). Признаков теперь четыре, добавилась сумма заказа (`X` в заготовке). Сохраните:

- `cv_mine` и `cv_sklearn` — MAE на 5 фолдах (`cross_val_score(..., cv=5, scoring="neg_mean_absolute_error")`, со сменой знака на плюс) для своей модели и для `LinearRegression`;
- `same_cv` — совпадают ли они (`np.allclose`);
- `pipe` — конвейер `make_pipeline(StandardScaler(), MyLinearRegression())`, обученный на всех `X`, `y`, и `r2_pipe` — его `score` на тех же данных (4 знака);
- `top_feature` — имя признака с наибольшим по модулю весом внутри конвейера (`pipe[-1].coef_`).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]]
y = ok["actual_min"]

class MyLinearRegression:
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        w = np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))
        self.intercept_, self.coef_ = w[0], w[1:]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.base import BaseEstimator as _BE
from sklearn.linear_model import LinearRegression as _LR
from sklearn.model_selection import cross_val_score as _cvs
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
C = need('MyLinearRegression')
assert issubclass(C, _BE), 'Класс должен наследовать BaseEstimator: class MyLinearRegression(RegressorMixin, BaseEstimator).'
assert hasattr(C(), 'score'), 'Нет метода score: добавьте родителя RegressorMixin.'
d = _pd.read_csv('deliveries.csv'); ok = d[d['actual_min'].between(1, 299)].copy(); ok['walk'] = (ok['courier'] == 'пеший').astype(int)
X0 = ok[['distance_km', 'items', 'walk', 'amount']]; y0 = ok['actual_min']
ref = -_cvs(_LR(), X0, y0, cv=5, scoring='neg_mean_absolute_error')
cm = _np.asarray(need('cv_mine'), dtype=float)
assert cm.shape == (5,), f'cv_mine — пять чисел, по одному на фолд, а сейчас форма {cm.shape}.'
assert (cm > 0).all(), 'В cv_mine отрицательные числа: cross_val_score с neg_mean_absolute_error возвращает MAE со знаком минус. Поставьте минус перед вызовом.'
assert _np.allclose(cm, ref, atol=1e-6), f'cv_mine = {cm.round(3)}, а у LinearRegression {ref.round(3)}.'
assert _np.allclose(need('cv_sklearn'), ref, atol=1e-6), f'cv_sklearn = {_np.round(need("cv_sklearn"), 3)}, а нужно {ref.round(3)}.'
assert bool(need('same_cv')) is True, 'same_cv должно быть True: сравните cv_mine и cv_sklearn через np.allclose.'
p = need('pipe')
assert isinstance(p[-1], C) and hasattr(p[-1], 'coef_'), 'pipe — конвейер из StandardScaler и вашего класса, обученный на X и y.'
pr = _mp(_SS(), _LR()).fit(X0, y0)
assert close(need('r2_pipe'), round(pr.score(X0, y0), 4), 1e-4), f'r2_pipe = {need("r2_pipe")}, а нужно {round(pr.score(X0, y0), 4)}.'
assert need('top_feature') == X0.columns[int(_np.abs(pr[-1].coef_).argmax())], f'top_feature = {need("top_feature")!r}. Ищите наибольший |вес| в pipe[-1].coef_.'
```

### hint
Родители пишутся в скобках после имени класса: `class MyLinearRegression(RegressorMixin, BaseEstimator):`. Методы `fit` и `predict` менять не нужно.

### hint
`cv_mine = -cross_val_score(MyLinearRegression(), X, y, cv=5, scoring="neg_mean_absolute_error")`, то же с `LinearRegression()`. Конвейер обучите через `.fit(X, y)`, `r2_pipe = round(pipe.score(X, y), 4)`.

### hint
Веса внутри конвейера — `pipe[-1].coef_`. Номер наибольшего по модулю — `np.abs(...).argmax()`, имя — `X.columns[номер]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk", "amount"]]
y = ok["actual_min"]

class MyLinearRegression(RegressorMixin, BaseEstimator):
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        w = np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))
        self.intercept_, self.coef_ = w[0], w[1:]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_

cv_mine = -cross_val_score(MyLinearRegression(), X, y, cv=5, scoring="neg_mean_absolute_error")
cv_sklearn = -cross_val_score(LinearRegression(), X, y, cv=5, scoring="neg_mean_absolute_error")
same_cv = bool(np.allclose(cv_mine, cv_sklearn))

pipe = make_pipeline(StandardScaler(), MyLinearRegression()).fit(X, y)
r2_pipe = round(pipe.score(X, y), 4)
top_feature = X.columns[int(np.abs(pipe[-1].coef_).argmax())]
print(cv_mine.round(3), same_cv, r2_pipe, top_feature, pipe[-1].coef_.round(2))
```

### explain
Две строки в объявлении класса, и своя модель работает везде, где работают модели sklearn: в кросс-валидации, в конвейере, в подборе параметров. Средняя MAE по фолдам около 5.91 минуты, как у `LinearRegression`. Сумма заказа почти ничего не добавила: R² конвейера 0.5057 против 0.5053 без неё. В конвейере веса посчитаны на стандартизированных признаках, поэтому их можно сравнивать между собой: «на одно стандартное отклонение». Сильнее всех влияет расстояние (около 7.4 минуты), у суммы заказа вес около −0.7. Без `BaseEstimator` `cross_val_score` упал бы ещё до первого фолда: ему нечем ни скопировать модель, ни узнать её свойства, и ошибка прямо просит унаследовать `BaseEstimator`.
