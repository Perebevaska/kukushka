---
title: "Проект: спрятать анкеты и не потерять модель"
files: [family_members.csv]
lead: "Финал главы. «Зерно» хочет отдать подрядчику данные семейной программы лояльности, чтобы он построил модель трат. В анкетах — пол, возраст, доход и размер семьи гостей. Нужно преобразовать признаки так, чтобы по ним нельзя было прочитать анкету, но линейная модель работала так же хорошо. Доказываем это формулами и проверяем на данных."
recap:
  - "Умножение признаков на случайную обратимую матрицу P прячет значения, но сохраняет всю информацию: с ключом P данные восстанавливаются."
  - "Линейная регрессия на X @ P даёт те же прогнозы и то же качество, что на X: оптимальные веса просто становятся P⁻¹ @ w."
  - "Ключ проверяют на обратимость (ранг) и обусловленность: почти вырожденная P портит точность вычислений."
  - "Вырожденный ключ безвозвратно теряет информацию, и качество модели падает."
  - "Это защита от случайного взгляда, а не криптография: зная несколько пар «исходная строка — спрятанная», P восстанавливается решением системы."
---

## Задача

> Мы хотим заказать у подрядчика модель, которая предсказывает годовые траты участника семейной программы. Но анкеты — персональные данные: пол, возраст, доход, число членов семьи. Передавать их в открытом виде нельзя.
>
> Предложите способ преобразовать признаки так, чтобы по ним нельзя было «прочитать» анкету, а качество линейной регрессии не ухудшилось. Обоснуйте, почему качество не изменится, и проверьте на наших данных. Отдельно оцените, насколько надёжна такая защита.
>
> *Руководитель отдела данных*

## Данные

`family_members.csv` — 5000 анкет:

| столбец | что это |
|---|---|
| `member_id` | номер участника (подрядчику не передаём) |
| `gender` | пол (1 — женщина, 0 — мужчина) |
| `age` | возраст |
| `income_k` | доход по анкете, тыс. ₽ в месяц |
| `family_size` | членов семьи в программе |
| `spend_k` | траты за год, тыс. ₽ (целевой признак) |

## Идея и обоснование

Передаём подрядчику не X, а X @ P, где P — случайная квадратная матрица 4 × 4, которую знаем только мы. Каждый столбец X @ P — смесь пола, возраста, дохода и семьи с непонятными весами: числа ничего не говорят. Ответ `spend_k` передаём как есть.

::: figure hide-flow
Схема проекта: что остаётся у «Зерна» и что уходит подрядчику. R² посчитан на тестовой части с ключом `default_rng(42)` из шага 3 — на открытых и на спрятанных данных он одинаковый.
:::

Почему линейная регрессия не пострадает. Обучение на X находит веса w, при которых ошибка прогнозов X @ w минимальна. На спрятанных данных модель ищет веса w' для прогнозов (X @ P) @ w' = X @ (P @ w'). Любой прогноз, доступный одной модели, доступен и другой: если на X лучший вектор весов — w, на X @ P можно взять w' = P⁻¹ @ w и получить ровно X @ w. И наоборот. Поэтому минимальная ошибка, а с ней и прогнозы, совпадают.

Условие одно: **P обратима** — иначе P⁻¹ не существует и информация теряется. Ниже проверим рассуждение на игрушке руками, а для желающих — выведем то же из формулы.

::: quiz
Почему ключ P для «спрятанных» анкет должен быть обратимым?

- [x] Иначе часть информации теряется и модель на спрятанных данных станет хуже
  > Необратимая матрица склеивает признаки — восстановить исходные значения и качество уже нельзя.
- [ ] Чтобы злоумышленник не восстановил данные
  > Наоборот: обратимость — условие сохранить качество, а защиту обеспечивает секретность ключа.
- [ ] Так быстрее считать
  > Скорость тут ни при чём.
- [ ] Иначе нельзя умножить матрицы
  > Умножить можно на любую подходящую по форме матрицу — обратимость нужна для качества.
:::

## Разберём вместе: формула на игрушке

Две колонки, четыре строки, ответ подобран точно: y = x₁ + 2x₂.

| x₁ | x₂ | y |
|---|---|---|
| 1 | 2 | 5 |
| 2 | 1 | 4 |
| 3 | 4 | 11 |
| 4 | 3 | 10 |

Веса на открытых данных: **w = [1, 2]**.

Ключ P = [[1, 1], [0, 1]]. Новые признаки: f₁ = x₁ (первый столбец P: 1, 0), f₂ = x₁ + x₂ (второй столбец: 1, 1). Строки превращаются в [1, 3], [2, 3], [3, 7], [4, 7].

Обратная: P⁻¹ = [[1, −1], [0, 1]] (проверьте: P @ P⁻¹ = I). По формуле w' = P⁻¹ @ w = [1 · 1 − 1 · 2, 0 · 1 + 1 · 2] = **[−1, 2]**.

Проверим подстановкой: −1 · f₁ + 2 · f₂ = −x₁ + 2x₁ + 2x₂ = x₁ + 2x₂. Ровно тот же прогноз. Первая строка: −1 · 1 + 2 · 3 = 5 ✓.

```python
import numpy as np
X = np.array([[1, 2], [2, 1], [3, 4], [4, 3.]])
y = np.array([5, 4, 11, 10.])
P = np.array([[1, 1], [0, 1.]])
print(np.linalg.lstsq(X, y, rcond=None)[0])          # [1. 2.]
print(np.linalg.lstsq(X @ P, y, rcond=None)[0])      # [-1. 2.]
print(np.linalg.inv(P) @ [1, 2])                     # [-1. 2.]
```

Что получилось: веса изменились до неузнаваемости — у первого признака даже знак другой, — а прогнозы те же. Именно поэтому подрядчик по весам своей модели тоже ничего не узнает про анкеты.

::: figure key-toy
Игрушка из разбора: таблица после умножения на P другая, веса другие (у первого даже знак сменился), а все четыре прогноза совпадают с прогнозами на открытых данных.
:::

::: note
Свободный член модели тоже не меняется: умножение на P перемешивает признаки, но не сдвигает их. А столбец единиц, если вы добавляете его вручную, умножать на P не нужно.
:::

::: deep То же через нормальное уравнение
Для тех, кто хочет формулу. Подставим X @ P в нормальное уравнение из урока «Как обучается линейная регрессия»:

w' = ((XP)ᵀ XP)⁻¹ (XP)ᵀ y = (Pᵀ XᵀX P)⁻¹ Pᵀ Xᵀ y = P⁻¹ (XᵀX)⁻¹ (Pᵀ)⁻¹ Pᵀ Xᵀ y = P⁻¹ (XᵀX)⁻¹ Xᵀ y = P⁻¹ w.

Здесь два новых правила, оба легко проверить в numpy на случайных матрицах через `np.allclose`:

- (XP)ᵀ = PᵀXᵀ — транспонирование произведения меняет порядок множителей.
- (Pᵀ XᵀX P)⁻¹ = P⁻¹ (XᵀX)⁻¹ (Pᵀ)⁻¹ — обратная произведения: обращаем каждый множитель и тоже меняем порядок. Для этого все три должны быть обратимы.

Дальше (Pᵀ)⁻¹ Pᵀ = I сокращается, остаётся P⁻¹ · (XᵀX)⁻¹ Xᵀ y, а это P⁻¹ · w.
:::

## План

1. Осмотреть данные.
2. Обучить линейную регрессию на исходных признаках — это эталон качества.
3. Создать ключ P и проверить, что он обратим и что данные восстанавливаются. Заодно посчитать **число обусловленности** `np.linalg.cond(P)` — во сколько раз матрица может усилить ошибки округления при обращении. Десятки и сотни — нормально, миллионы и больше — плохой ключ: формально он обратим, но восстановление и обучение станут неточными.
4. Обучить модель на спрятанных признаках и сравнить качество.
5. Проверить связь весов w' = P⁻¹ @ w и совпадение прогнозов для каждого гостя.
6. Показать, что будет с плохим (вырожденным) ключом.
7. Оценить надёжность защиты.

::: warn Типичные ошибки проекта
- **Спрятали только train.** Подрядчик обучит модель на `X_train @ P`, а проверять её надо на `X_test @ P` — тест тоже уходит в спрятанном виде.
- **Новый ключ для новых анкет.** Модель подрядчика работает только с тем P, на котором обучена. Ключ генерируется один раз и хранится.
- **Спрятали и ответ.** `spend_k` передаём как есть — иначе подрядчик будет предсказывать смесь, которую не с чем сравнить.
- **Передали `member_id`.** Идентификатор не нужен модели и сводит на нет всю идею.
:::

Разбиение везде одно: `train_test_split(X, y, test_size=0.25, random_state=42)`, где `X` — четыре признака в порядке `gender, age, income_k, family_size`.

Проект решается прямо на этой странице: каждый шаг плана — задача с проверкой. Блокнот сдавать не нужно: сдача блокнотом со сверкой эталонов — только у итоговых проектов курса.

## task: look | Шаг 1. Осмотр | base

Сохраните число анкет `n`, среднюю трату `mean_spend` (1 знак) и `same_profile` — сколько анкет полностью повторяют признаки (пол, возраст, доход, семья) какой-то предыдущей анкеты (`duplicated` по четырём столбцам). В `max_income` — наибольший доход.

### starter
```python
import pandas as pd
f = pd.read_csv("family_members.csv")
cols = ["gender", "age", "income_k", "family_size"]

```

### check
```python
import pandas as _pd
f0 = _pd.read_csv('family_members.csv'); c0 = ['gender', 'age', 'income_k', 'family_size']
assert need('n') == len(f0), f'n = {need("n")}.'
assert close(need('mean_spend'), round(f0['spend_k'].mean(), 1)), f'mean_spend = {need("mean_spend")}.'
assert need('same_profile') == int(f0.duplicated(subset=c0).sum()), f'same_profile = {need("same_profile")}, а нужно {int(f0.duplicated(subset=c0).sum())}: f.duplicated(subset=cols).sum().'
assert need('max_income') == f0['income_k'].max(), f'max_income = {need("max_income")}.'
```

### hint
`n = len(f)`, `mean_spend = round(f["spend_k"].mean(), 1)`, `max_income = f["income_k"].max()`.

### hint
`f.duplicated(subset=cols).sum()` — повторы только по указанным столбцам. Первое появление профиля не считается, только повторные.

### solution
```python
import pandas as pd
f = pd.read_csv("family_members.csv")
cols = ["gender", "age", "income_k", "family_size"]
n = len(f)
mean_spend = round(f["spend_k"].mean(), 1)
same_profile = int(f.duplicated(subset=cols).sum())
max_income = f["income_k"].max()
```

### explain
Почти 450 анкет совпадают по всем четырём признакам с другими — это разные люди с одинаковыми ответами (например, двое 35-летних с доходом 90 тыс. и семьёй из трёх). Дубликатами в смысле ошибок данных они не являются, удалять их не нужно.

## task: baseline | Шаг 2. Эталонное качество | base

Обучите `LinearRegression` на исходных признаках и сохраните R² на тесте `r2_base` (4 знака) и модель `model`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import r2_score as _r2
f0 = _pd.read_csv('family_members.csv')
a, b, c, d = _tts(f0[['gender', 'age', 'income_k', 'family_size']].values, f0['spend_k'].values, test_size=0.25, random_state=42)
w = round(_r2(d, _LR().fit(a, c).predict(b)), 4)
assert close(need('r2_base'), w), f'r2_base = {need("r2_base")}, а нужно {w}.'
```

### hint
Обучайте только на `X_train, y_train`, качество меряйте на `X_test`.

### hint
`model = LinearRegression().fit(X_train, y_train)`, затем `r2_score(y_test, model.predict(X_test))`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

model = LinearRegression().fit(X_train, y_train)
r2_base = round(r2_score(y_test, model.predict(X_test)), 4)
```

### explain
R² около 0.37: траты зависят не только от анкеты. Для проекта важно не само число, а то, что после «пряток» оно должно остаться ровно таким же.

## task: key | Шаг 3. Ключ | base

Создайте ключ `P = np.random.default_rng(42).normal(size=(4, 4))`. Сохраните его ранг `rank`, `invertible` (`True`, если ранг 4) и число обусловленности `cond = np.linalg.cond(P)` (1 знак) — во сколько раз ключ может усилить ошибки округления (см. план, шаг 3). Спрячьте все признаки `hidden = X @ P` и проверьте восстановление: `restore_ok` — `True`, если `hidden @ np.linalg.inv(P)` совпадает с `X` (`np.allclose`).

### starter
```python
import numpy as np
import pandas as pd
f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values

```

### check
```python
import numpy as _np, pandas as _pd
P0 = _np.random.default_rng(42).normal(size=(4, 4))
assert _np.allclose(need('P'), P0), 'P = np.random.default_rng(42).normal(size=(4, 4)) — создайте генератор и сразу вызовите normal.'
assert need('rank') == 4 and need('invertible') == True, f'rank = {need("rank")}, invertible = {need("invertible")}.'
assert close(need('cond'), round(_np.linalg.cond(P0), 1), 0.11), f'cond = {need("cond")}.'
X0 = _pd.read_csv('family_members.csv')[['gender', 'age', 'income_k', 'family_size']].values
assert _np.allclose(need('hidden'), X0 @ P0), 'hidden = X @ P.'
assert need('restore_ok') == True, 'restore_ok должно быть True.'
```

### hint
Ранг — `np.linalg.matrix_rank(P)`, обратная — `np.linalg.inv(P)`.

### hint
`invertible = rank == 4`, `cond = round(np.linalg.cond(P), 1)`, `restore_ok = bool(np.allclose(hidden @ np.linalg.inv(P), X))`.

### solution
```python
import numpy as np
import pandas as pd
f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values

P = np.random.default_rng(42).normal(size=(4, 4))
rank = int(np.linalg.matrix_rank(P))
invertible = rank == 4
cond = round(np.linalg.cond(P), 1)
hidden = X @ P
restore_ok = bool(np.allclose(hidden @ np.linalg.inv(P), X))
```

### explain
**Число обусловленности** показывает, во сколько раз матрица может усилить ошибки округления при обращении. У нашего ключа около 27 — безопасно (проблемы начинаются с миллионов и выше). Ключ с огромным числом обусловленности формально обратим, но восстановление и обучение станут неточными. Если такой ключ попался, просто сгенерируйте другой.

## task: hidden-quality | Шаг 4. Качество на спрятанных данных | base

Обучите `LinearRegression` на `X_train @ P` и проверьте на `X_test @ P`. Сохраните `r2_hidden` (4 знака) и `same` — `True`, если он совпадает с эталонным R² (`r2_base` уже посчитан в заготовке) с точностью до 1e-9.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
r2_base = r2_score(y_test, LinearRegression().fit(X_train, y_train).predict(X_test))
P = np.random.default_rng(42).normal(size=(4, 4))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import r2_score as _r2
f0 = _pd.read_csv('family_members.csv')
a, b, c, d = _tts(f0[['gender', 'age', 'income_k', 'family_size']].values, f0['spend_k'].values, test_size=0.25, random_state=42)
P0 = _np.random.default_rng(42).normal(size=(4, 4))
w = _r2(d, _LR().fit(a @ P0, c).predict(b @ P0))
assert close(need('r2_hidden'), round(w, 4)), f'r2_hidden = {need("r2_hidden")}, а нужно {round(w, 4)}. Тестовые признаки тоже надо умножить на P.'
assert need('same') == True, 'same должно быть True: R² совпадают до 1e-9.'
```

### hint
Важно умножить на P и обучающие, и тестовые признаки — подрядчик получает всё в спрятанном виде.

### hint
Для `same` сравнивайте с `r2_base` неокруглённый R² спрятанной модели, а не `r2_hidden`: `abs(r2 - r2_base) < 1e-9`, где `r2` — результат `r2_score` до `round`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
r2_base = r2_score(y_test, LinearRegression().fit(X_train, y_train).predict(X_test))
P = np.random.default_rng(42).normal(size=(4, 4))

hidden_model = LinearRegression().fit(X_train @ P, y_train)
r2_full = r2_score(y_test, hidden_model.predict(X_test @ P))
r2_hidden = round(r2_full, 4)
same = bool(abs(r2_full - r2_base) < 1e-9)
```

### explain
R² 0.3713 и на открытых, и на спрятанных данных — совпадение до девятого знака и дальше. Это и есть главный результат проекта: доказательство из раздела «Идея» подтвердилось на 1250 тестовых анкетах.

## task: weights | Шаг 5. Веса и прогнозы | plus

Проверьте обоснование на числах. Сохраните `w` (веса модели на исходных данных), `w_hidden` (веса модели на спрятанных), `match` — `True`, если `w_hidden` совпадает с `np.linalg.inv(P) @ w`, и `max_diff` — наибольшую разницу прогнозов двух моделей на тестовых гостях.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
P = np.random.default_rng(42).normal(size=(4, 4))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
f0 = _pd.read_csv('family_members.csv')
a, b, c, d = _tts(f0[['gender', 'age', 'income_k', 'family_size']].values, f0['spend_k'].values, test_size=0.25, random_state=42)
P0 = _np.random.default_rng(42).normal(size=(4, 4))
m1 = _LR().fit(a, c); m2 = _LR().fit(a @ P0, c)
assert _np.allclose(need('w'), m1.coef_) and _np.allclose(need('w_hidden'), m2.coef_, atol=1e-6), 'w и w_hidden — coef_ двух моделей.'
assert need('match') == True, 'match должно быть True.'
assert need('max_diff') < 1e-6, f'max_diff = {need("max_diff")}.'
```

### hint
Две модели: `m1` на `X_train`, `m2` на `X_train @ P`. Веса — `coef_`.

### hint
`match = np.allclose(w_hidden, np.linalg.inv(P) @ w, atol=1e-6)`. Прогнозы `m2` — на `X_test @ P`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
P = np.random.default_rng(42).normal(size=(4, 4))

m1 = LinearRegression().fit(X_train, y_train)
m2 = LinearRegression().fit(X_train @ P, y_train)
w, w_hidden = m1.coef_, m2.coef_
match = bool(np.allclose(w_hidden, np.linalg.inv(P) @ w, atol=1e-6))
max_diff = np.abs(m1.predict(X_test) - m2.predict(X_test @ P)).max()
```

### explain
Совпадают не только R², но и прогноз для каждого гостя — до миллиардных долей. Подрядчик может обучить и отдать нам модель на спрятанных признаках, а мы будем применять её к новым анкетам, сначала умножив их на тот же ключ P.

## task: new-member | Шаг 5б. Новая анкета | base

Подрядчик вернул модель, обученную на спрятанных данных (`m_hidden` в заготовке). Пришла новая анкета: женщина, 34 года, доход 95 тыс., семья из 3 человек. Сохраните `pred_open` — прогноз открытой модели `m_open` для этой анкеты, `pred_hidden` — прогноз `m_hidden`, если анкету умножить на тот же ключ `P`, и `pred_wrong` — прогноз `m_hidden`, если по ошибке взять новый ключ `np.random.default_rng(43).normal(size=(4, 4))` (все — 2 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
P = np.random.default_rng(42).normal(size=(4, 4))
m_open = LinearRegression().fit(X_train, y_train)
m_hidden = LinearRegression().fit(X_train @ P, y_train)

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
f0 = _pd.read_csv('family_members.csv')
a, b, c, d = _tts(f0[['gender', 'age', 'income_k', 'family_size']].values, f0['spend_k'].values, test_size=0.25, random_state=42)
P0 = _np.random.default_rng(42).normal(size=(4, 4)); W = _np.random.default_rng(43).normal(size=(4, 4))
new = _np.array([[1, 34, 95, 3]])
m1 = _LR().fit(a, c); m2 = _LR().fit(a @ P0, c)
po = round(float(m1.predict(new)[0]), 2); ph = round(float(m2.predict(new @ P0)[0]), 2); pw = round(float(m2.predict(new @ W)[0]), 2)
assert close(need('pred_open'), po), f'pred_open = {need("pred_open")}, а нужно {po}.'
assert close(need('pred_hidden'), ph), f'pred_hidden = {need("pred_hidden")}, а нужно {ph}. Анкету надо умножить на P.'
assert close(need('pred_wrong'), pw, 0.02), f'pred_wrong = {need("pred_wrong")}, а нужно {pw}.'
```

### hint
Анкета — двумерный массив из одной строки в порядке признаков: `new = np.array([[1, 34, 95, 3]])`. `predict` возвращает массив — берите `[0]`.

### hint
`m_hidden.predict(new @ P)[0]` — правильный путь; с чужим ключом — `new @ np.random.default_rng(43).normal(size=(4, 4))`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
P = np.random.default_rng(42).normal(size=(4, 4))
m_open = LinearRegression().fit(X_train, y_train)
m_hidden = LinearRegression().fit(X_train @ P, y_train)

new = np.array([[1, 34, 95, 3]])
pred_open = round(float(m_open.predict(new)[0]), 2)
pred_hidden = round(float(m_hidden.predict(new @ P)[0]), 2)
wrong = np.random.default_rng(43).normal(size=(4, 4))
pred_wrong = round(float(m_hidden.predict(new @ wrong)[0]), 2)
```

### explain
С правильным ключом прогноз 21.27 тыс. ₽ — ровно как у открытой модели. С чужим ключом — −2144 тыс. ₽: отрицательные траты, явная бессмыслица. Здесь ошибку видно сразу, но с другим seed она могла бы дать правдоподобное и неверное число. Поэтому ключ хранят вместе с моделью как часть релиза, а не генерируют заново.

## task: bad-key | Шаг 6. Плохой ключ | plus

Испортим ключ: в копии `P` замените последний столбец на сумму первых двух (`bad[:, 3] = bad[:, 0] + bad[:, 1]`). Сохраните ранг `bad_rank`, R² линейной регрессии на `X_train @ bad` → `X_test @ bad` (`r2_bad`, 4 знака) и `loss` — на сколько он меньше эталонного (4 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
r2_base = r2_score(y_test, LinearRegression().fit(X_train, y_train).predict(X_test))
P = np.random.default_rng(42).normal(size=(4, 4))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import r2_score as _r2
f0 = _pd.read_csv('family_members.csv')
a, b, c, d = _tts(f0[['gender', 'age', 'income_k', 'family_size']].values, f0['spend_k'].values, test_size=0.25, random_state=42)
P0 = _np.random.default_rng(42).normal(size=(4, 4)); B = P0.copy(); B[:, 3] = B[:, 0] + B[:, 1]
base = _r2(d, _LR().fit(a, c).predict(b)); rb = _r2(d, _LR().fit(a @ B, c).predict(b @ B))
assert need('bad_rank') == 3, f'bad_rank = {need("bad_rank")}, должен быть 3.'
assert close(need('r2_bad'), round(rb, 4)), f'r2_bad = {need("r2_bad")}, а нужно {round(rb, 4)}.'
assert close(need('loss'), round(base - rb, 4)), f'loss = {need("loss")}.'
```

### hint
`bad = P.copy()` — без `copy` вы испортите и исходный ключ.

### hint
`bad[:, 3]` — весь последний столбец. Ранг — `np.linalg.matrix_rank(bad)`; модель обучайте на `X_train @ bad`, проверяйте на `X_test @ bad`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
r2_base = r2_score(y_test, LinearRegression().fit(X_train, y_train).predict(X_test))
P = np.random.default_rng(42).normal(size=(4, 4))

bad = P.copy()
bad[:, 3] = bad[:, 0] + bad[:, 1]
bad_rank = int(np.linalg.matrix_rank(bad))
r2_bad = round(r2_score(y_test, LinearRegression().fit(X_train @ bad, y_train).predict(X_test @ bad)), 4)
loss = round(r2_base - r2_bad, 4)
```

### explain
Четвёртый столбец спрятанных данных теперь повторяет сумму первых двух — по сути у подрядчика осталось три признака вместо четырёх. Часть информации стёрта навсегда, и модель стала хуже. Поэтому ключ всегда проверяют на ранг.

## task: tree-hidden | Шаг 6б. А если подрядчик выберет дерево | plus

Ниже, в итоге для руководителя, будет сказано, что для деревьев гарантии нет. Проверьте это заранее: обучите `DecisionTreeRegressor(max_depth=d, random_state=0)` для глубин 3, 5 и 8 на открытых и на спрятанных (`@ P`) признаках и посчитайте R² на тесте. Сохраните DataFrame `trees` (индекс — глубина, столбцы `open` и `hidden`, 4 знака), `best_open` — лучший R² дерева на открытых данных и `best_hidden` — на спрятанных.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
P = np.random.default_rng(42).normal(size=(4, 4))

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeRegressor as _T
from sklearn.metrics import r2_score as _r2
f0 = _pd.read_csv('family_members.csv')
a, b, c, d = _tts(f0[['gender', 'age', 'income_k', 'family_size']].values, f0['spend_k'].values, test_size=0.25, random_state=42)
P0 = _np.random.default_rng(42).normal(size=(4, 4))
t = need('trees', _pd.DataFrame)
assert sorted(int(i) for i in t.index) == [3, 5, 8], f'Индекс trees: {list(t.index)}, нужны глубины 3, 5, 8.'
bo, bh = [], []
for dep in [3, 5, 8]:
    o = round(_r2(d, _T(max_depth=dep, random_state=0).fit(a, c).predict(b)), 4)
    h = round(_r2(d, _T(max_depth=dep, random_state=0).fit(a @ P0, c).predict(b @ P0)), 4)
    bo.append(o); bh.append(h)
    assert close(t.loc[dep, 'open'], o, 0.0002) and close(t.loc[dep, 'hidden'], h, 0.0002), f'глубина {dep}: {t.loc[dep, "open"]}, {t.loc[dep, "hidden"]}, а нужно {o}, {h}.'
assert close(need('best_open'), max(bo), 0.0002) and close(need('best_hidden'), max(bh), 0.0002), f'best_open, best_hidden = {need("best_open")}, {need("best_hidden")}.'
```

### hint
Цикл по `[3, 5, 8]`, в нём два дерева: одно на `X_train`, другое на `X_train @ P`; прогнозы — на `X_test` и `X_test @ P` соответственно.

### hint
`trees = pd.DataFrame(rows).T`, где `rows[dep] = {"open": ..., "hidden": ...}`; `best_open = trees["open"].max()`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import r2_score

f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values
y = f["spend_k"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
P = np.random.default_rng(42).normal(size=(4, 4))

rows = {}
for dep in [3, 5, 8]:
    t_open = DecisionTreeRegressor(max_depth=dep, random_state=0).fit(X_train, y_train)
    t_hid = DecisionTreeRegressor(max_depth=dep, random_state=0).fit(X_train @ P, y_train)
    rows[dep] = {"open": round(r2_score(y_test, t_open.predict(X_test)), 4),
                 "hidden": round(r2_score(y_test, t_hid.predict(X_test @ P)), 4)}
trees = pd.DataFrame(rows).T
best_open = trees["open"].max()
best_hidden = trees["hidden"].max()
```

### explain
Лучшее дерево на открытых анкетах — 0.32 (глубина 5), на спрятанных — 0.16, вдвое хуже. Причина та же, что в уроке «Преобразовать признаки матрицей»: дерево задаёт вопросы вроде «доход > 100?», а в смесях дохода с возрастом и полом таких чистых порогов нет. Вывод для договора: если передаём данные «перемешанными», модель подрядчика должна быть линейной, иначе мы заплатим за худшее качество. Заметьте и другое: линейная регрессия (0.37) здесь лучше любого дерева даже на открытых данных.

## task: attack | Шаг 7. Насколько надёжна защита | star

Представим, что подрядчик знает четыре настоящие анкеты (например, своих сотрудников) и видит их спрятанные версии. Возьмите первые 4 строки `X` как известные (`known`) и их спрятанные версии `hidden[:4]`. Восстановите ключ, решив систему `known @ P_found = hidden[:4]` (`np.linalg.solve`), и с его помощью раскройте все анкеты. Сохраните `P_found`, `key_found` (`True`, если `P_found` совпадает с `P`) и `leaked` — долю анкет, которые восстановились с точностью до 0.01 по всем признакам.

### starter
```python
import numpy as np
import pandas as pd
f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values.astype(float)
P = np.random.default_rng(42).normal(size=(4, 4))
hidden = X @ P

```

### check
```python
import numpy as _np, pandas as _pd
X0 = _pd.read_csv('family_members.csv')[['gender', 'age', 'income_k', 'family_size']].values.astype(float)
P0 = _np.random.default_rng(42).normal(size=(4, 4)); H = X0 @ P0
pf = _np.asarray(need('P_found'))
assert pf.shape == (4, 4), f'Форма P_found: {pf.shape}.'
assert _np.allclose(pf, _np.linalg.solve(X0[:4], H[:4])), 'P_found — решение np.linalg.solve(X[:4], hidden[:4]).'
assert need('key_found') == bool(_np.allclose(pf, P0)), f'key_found = {need("key_found")}.'
rec = H @ _np.linalg.inv(pf)
lk = float(_np.mean(_np.all(_np.abs(rec - X0) < 0.01, axis=1)))
assert close(need('leaked'), lk), f'leaked = {need("leaked")}, а нужно {lk}.'
```

### hint
Система с матрицей в правой части тоже решается `np.linalg.solve(known, hidden[:4])` — каждый столбец P независимо.

### hint
Раскрытые анкеты: `hidden @ np.linalg.inv(P_found)`; совпадение по строкам — `np.all(np.abs(... - X) < 0.01, axis=1)`.

### solution
```python
import numpy as np
import pandas as pd
f = pd.read_csv("family_members.csv")
X = f[["gender", "age", "income_k", "family_size"]].values.astype(float)
P = np.random.default_rng(42).normal(size=(4, 4))
hidden = X @ P

known = X[:4]
P_found = np.linalg.solve(known, hidden[:4])
key_found = bool(np.allclose(P_found, P))
restored = hidden @ np.linalg.inv(P_found)
leaked = float(np.mean(np.all(np.abs(restored - X) < 0.01, axis=1)))
```

### explain
Четырёх известных анкет хватило, чтобы раскрыть все 5000. Это та же задача, что цены по чекам в уроке «Как обучается линейная регрессия»: P — четыре неизвестных столбца по четыре числа, а четыре независимые строки дают систему, которая решается однозначно. Для настоящей защиты персональных данных нужны другие инструменты: обезличивание, агрегирование, дифференциальная приватность, а в идеале — модель обучается там, где данные уже лежат.

## Итог для руководителя отдела данных

> **Способ.** Умножаем четыре признака анкеты на случайную обратимую матрицу 4 × 4, которую храним у себя. Подрядчик видит только смеси признаков, по которым анкету не прочитать.
>
> **Качество.** Для линейной регрессии оно не меняется: доказано через нормальное уравнение и проверено — R² и прогноз каждого гостя совпадают с моделью на открытых данных. Для деревьев и kNN такой гарантии нет: лучшее дерево на спрятанных данных вдвое хуже (R² 0.16 против 0.32), поэтому в договоре фиксируем линейную модель.
>
> **Условия.** Ключ генерируем один раз и храним вместе с моделью — новые анкеты умножаем на тот же ключ. Ключ обязательно проверяем на обратимость и обусловленность; вырожденный ключ стирает часть информации и ухудшает модель.
>
> **Ограничение.** Это защита от случайного взгляда, а не шифрование: если у подрядчика окажутся хотя бы четыре известные анкеты, он восстановит ключ и все данные. Для чувствительных данных метод годится только вместе с договором о неразглашении и минимизацией передаваемых полей.
