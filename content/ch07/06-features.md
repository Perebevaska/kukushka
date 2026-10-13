---
title: Новые признаки
lead: "Модель знает о гостях только то, что лежит в столбцах таблицы. Часто самое полезное знание аналитика — «новички уходят чаще», «жалоба на доставку — плохой знак» — модель сама не найдёт. Учимся превращать такие наблюдения в новые признаки — флаги и взаимодействия — и сравнивать варианты кросс-валидацией на одних и тех же фолдах. Как проверить, что прирост не шум, и какие признаки на самом деле важны, — в следующем уроке."
files: [guests_churn.csv]
recap:
  - "Новый признак полезен, если сообщает модели то, чего она не может получить сама. Линейное пересчитывание (визиты за 90 дней → в месяц) линейной модели ничего не даёт."
  - "Флаг-порог (`tenure_months <= 3`) и произведение двух признаков (жалобы × доля доставки) дают логистической регрессии то, чего она сама не умеет: ступеньку и взаимодействие."
  - "Варианты признаков сравнивают кросс-валидацией на обучающей части, на одних и тех же фолдах (`kf` — один на все сравнения); метрику задаёт `scoring` (`\"roc_auc\"`, `\"f1\"`). Тест — один раз в конце."
---

## Модель видит только столбцы

В уроке «Масштабирование и ближайшие соседи» мы сделали признаки сравнимыми по масштабу. Теперь — сами признаки. Аналитик, глядя на гостей, многое знает «на глаз»: новички ещё не привыкли к кофейне, недовольные доставкой уходят. Модель этого не знает. Она видит только столбцы, и логистическая регрессия умеет из них одно — сложить с весами. **Конструирование признаков** (feature engineering) — это перевод знаний аналитика на язык столбцов.

Чтобы сравнивать варианты, заведём функцию: она готовит признаки как обычно, откладывает тест и возвращает средний ROC-AUC логистической регрессии по пяти фолдам обучающей части (кросс-валидация из главы 6). Признаки будем добавлять прямо в таблицу гостей `g` — функция подхватит любой новый столбец.

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

print(f"AUC {cv_auc(g):.3f}, F1 {cv_auc(g, 'f1'):.3f}")
```

**Что здесь происходит:**

- `kf` — одно и то же разбиение на 5 фолдов для всех вариантов признаков: так сравнение честное, разница не от удачных фолдов.
- Внутри `cv_auc` таблица собирается заново из `df` — поэтому достаточно добавить столбец в `g`, и функция его подхватит.
- `train_test_split` с тем же `random_state` каждый раз откладывает тех же гостей в тест; CV идёт только по обучающей части.
- Возвращается среднее по фолдам — одно число на вариант.

Параметр `scoring` говорит `cross_val_score`, какую метрику считать на каждом фолде: по умолчанию это accuracy, `"roc_auc"` — ROC-AUC из урока «Порог, PR- и ROC-кривые», `"f1"` — F1 из урока «Precision, recall и F1». Отправная точка — AUC около 0.877 и F1 около 0.62. Тест мы не трогаем: он нужен для финальной проверки, а выбирать признаки по нему — то же подглядывание, что и выбор глубины дерева (глава 6).

::: note Небольшая неточность
Здесь масштабировщик учится на всей обучающей части, а потом её режут на фолды — средние «видят» и проверочный фолд. На наших данных это сдвигает оценку в четвёртом знаке. Как убрать даже эту мелочь, покажет урок «Pipeline: предобработка и модель вместе» (Pipeline).
:::

Первая идея: визиты за 90 дней непривычны, пересчитаем их в визиты в месяц.

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

g["visits_per_month"] = g["visits_90d"] / 3
print(f"AUC {cv_auc(g):.4f}")
```

Ничего не изменилось. Для человека «2 визита в месяц» понятнее, чем «6 за квартал», но для модели это тот же столбец, умноженный на число, — а умножать на числа она умеет сама, это и есть её вес. После масштабирования оба столбца вообще становятся одинаковыми. Полезный признак должен сообщать модели то, что она **не может получить** сложением с весами.

{{practice: gain}}

## Флаги и взаимодействия

Логистическая регрессия думает так: «каждый лишний месяц с нами меняет риск на одну и ту же величину». А в данных иначе:

```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")
print(g.groupby(g["tenure_months"].clip(upper=8))["churned"].mean().round(2))
```

`clip(upper=8)` сводит всех, кто с нами 8 месяцев и дольше, в одну группу. Первые три месяца уходит больше половины гостей, а с четвёртого — от 15 до 30 %, без явного тренда. Это **ступенька**, а не плавная линия. Прямой такую ступеньку не описать, а флаг — легко:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

print(f"без флага: {cv_auc(g):.3f}")
g["is_new"] = (g["tenure_months"] <= 3).astype(int)
print(f"с флагом новичка: {cv_auc(g):.3f}")
```

Один столбец из нулей и единиц — и AUC вырос примерно с 0.877 до 0.896.

### Разберём вместе: прямая против ступеньки

Почему логистическая регрессия не нашла ступеньку сама? Обучим её на одном признаке — сначала на `tenure_months`, потом на флаге `is_new` — и сравним прогнозы с фактом:

| месяцев с нами | гостей | факт ухода | прогноз по `tenure_months` | прогноз по флагу |
|---|---|---|---|---|
| 1 | 20 | 0.70 | 0.24 | 0.57 |
| 2 | 33 | 0.67 | 0.24 | 0.57 |
| 3 | 73 | 0.52 | 0.24 | 0.57 |
| 4 | 108 | 0.16 | 0.24 | 0.20 |
| 12 | 95 | 0.20 | 0.23 | 0.20 |
| 24 | 36 | 0.17 | 0.22 | 0.20 |

Модель на `tenure_months` выдаёт почти одну и ту же вероятность всем: 0.22–0.24. Она может провести только плавную кривую, а новичков мало (126 из 2400) и стаж тянется до 60 месяцев — лучший компромисс для неё почти горизонтальная линия. Ступенька «до трёх месяцев — больше половины, потом — пятая часть» ей недоступна.

Флаг даёт ровно две вероятности — 0.57 и 0.20, — и обе близки к факту. Модель не стала умнее: мы просто дали ей столбец, в котором ступенька уже есть. Это больше, чем дают многие «умные» модели.

::: figure step-vs-line
Точки — фактическая доля ушедших по стажу из таблицы. Модель на `tenure_months` может провести только плавную линию и почти не отличает новичков; модель на флаге `is_new` даёт ступеньку, которая совпадает с данными.
:::

Вторая находка аналитика — **взаимодействие** (interaction): эффект одного признака зависит от значения другого. Посмотрим на жалобы вместе с долей доставки:

```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")
share = pd.cut(g["delivery_share"], [-0.01, 0.2, 0.5, 1])
print(g.pivot_table(index="complaints", columns=share, values="churned", aggfunc="mean", observed=True).round(2))
```

Без жалоб гости с большой долей доставки уходят даже реже остальных. С одной жалобой гости, которые мало заказывают доставку, уходят в 41 % случаев, а те, у кого доставка — больше половины заказов, — почти все. Видимо, жалуются как раз на доставку, и для тех, кто ей живёт, это повод уйти. Логистическая регрессия складывает «вклад жалоб» и «вклад доставки» по отдельности и такой эффект «вместе сильнее, чем по отдельности» поймать не может. Подскажем ей произведением:

::: figure interaction-grid
Доля ушедших по жалобам и доле доставки. Без жалоб доставка почти ни на что не влияет, с одной жалобой — уход растёт с 41 % до 97 %. Эффект одного признака зависит от другого — это взаимодействие.
:::

::: predict
```python static
complaints = [0, 1, 1, 2]
delivery = [0.9, 0.1, 0.8, 0.5]
print([c * d for c, d in zip(complaints, delivery)])
```

- `[0.9, 1.1, 1.8, 2.5]`
- [x] `[0.0, 0.1, 0.8, 1.0]`
- `[0, 1, 1, 2]`

Почему: произведение равно нулю, если жалоб нет, — какой бы ни была доставка. Большим оно становится, только когда есть **и** жалобы, **и** высокая доля доставки. Это и есть взаимодействие.
:::

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

g["compl_x_deliv"] = g["complaints"] * g["delivery_share"]
print(f"с взаимодействием: {cv_auc(g):.3f}")
g["is_new"] = (g["tenure_months"] <= 3).astype(int)
print(f"и с флагом новичка: {cv_auc(g):.3f}, F1 {cv_auc(g, 'f1'):.3f}")
```

Взаимодействие само по себе добавляет меньше (около 0.885), но вместе с флагом новичка AUC доходит до 0.904, а F1 — с 0.62 до 0.67. Два столбца, придуманных по двум группировкам, — и модель заметно лучше.

::: sql
Новые признаки — это вычисляемые столбцы в `SELECT`: `CASE WHEN tenure_months <= 3 THEN 1 ELSE 0 END AS is_new`, `complaints * delivery_share AS compl_x_deliv`. В pandas — то же самое, одной строкой на признак.
:::

::: warn Типичные ошибки
- **Признак выбран по тесту.** Сравнение вариантов — только кросс-валидацией на обучающей части; тест — один раз в конце.
- **Разные фолды для разных вариантов.** Прирост 0.005 легко получить просто от другого разбиения; `kf` — один на все сравнения.
- **Линейный пересчёт.** «В месяц вместо за квартал», «тысячи вместо рублей» линейной модели ничего не дают.
- **Порог флага подобран по ответу на всех данных.** «≤ 3 месяцев» мы взяли из группировки по всей таблице — строго говоря, это тоже подглядывание; в рабочем проекте такие пороги ищут на train.
:::

Флаги и взаимодействия подсказывают модели ступеньки и сочетания. Как подсказать ей форму плавной связи, отличить настоящий прирост от удачной нарезки фолдов и понять, какие признаки модель на самом деле использует, — в уроке «Форма связи и важность признаков».

{{practice: is-new, cxd, pairs}}

## Практика

## task: is-new | Флаг новичка | warmup

Добавьте в таблицу `g` столбец `is_new`: 1, если гость с нами 3 месяца или меньше, иначе 0 (целые числа). Сохраните долю ушедших среди новичков `rate_new` и среди остальных `rate_old` (обе — 3 знака) и число новичков `n_new`.

### starter
```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")

```

### check
```python
import pandas as _pd
_g = _pd.read_csv('guests_churn.csv')
_m = _g['tenure_months'] <= 3
_gg = need('g', _pd.DataFrame)
assert 'is_new' in _gg.columns, 'В g нет столбца is_new.'
assert set(_gg['is_new'].unique()) <= {0, 1}, 'is_new должен содержать 0 и 1 — переведите True/False в числа: .astype(int).'
assert (_gg['is_new'].astype(int).values == _m.astype(int).values).all(), 'is_new не совпадает с ожидаемым: новичок — tenure_months <= 3 (три месяца включительно).'
assert int(need('n_new')) == int(_m.sum()), f'n_new = {need("n_new")}, а новичков {int(_m.sum())}.'
assert close(need('rate_new'), round(_g.loc[_m, 'churned'].mean(), 3)), f'rate_new = {need("rate_new")}, а ожидалось {round(_g.loc[_m, "churned"].mean(), 3)}. Это среднее churned среди новичков.'
assert close(need('rate_old'), round(_g.loc[~_m, 'churned'].mean(), 3)), f'rate_old = {need("rate_old")}, а ожидалось {round(_g.loc[~_m, "churned"].mean(), 3)}.'
```

### hint
`g["is_new"] = (g["tenure_months"] <= 3).astype(int)`.

### hint
`rates = g.groupby("is_new")["churned"].mean()` — в индексе 0 и 1; `rates[1]` — новички.

### solution
```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")
g["is_new"] = (g["tenure_months"] <= 3).astype(int)
rates = g.groupby("is_new")["churned"].mean()
rate_new = round(rates[1], 3)
rate_old = round(rates[0], 3)
n_new = int(g["is_new"].sum())
```

### explain
Новичков всего около 5 % гостей, но уходит больше половины из них — почти в три раза чаще, чем остальные. Небольшая группа с резко другим поведением — типичный случай, когда флаг помогает линейной модели.

## task: cxd | Жалобы на доставку | warmup

Добавьте в `g` столбец `compl_x_deliv` — произведение `complaints` на `delivery_share`. Сохраните:

- `n_hi` — сколько гостей с `compl_x_deliv` ≥ 0.5;
- `rate_hi` — долю ушедших среди них (3 знака);
- `rate_zero` — долю ушедших среди гостей с `compl_x_deliv` = 0 (3 знака).

### starter
```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")

```

### check
```python
import pandas as _pd
_g = _pd.read_csv('guests_churn.csv')
_c = _g['complaints'] * _g['delivery_share']
_gg = need('g', _pd.DataFrame)
assert 'compl_x_deliv' in _gg.columns, 'В g нет столбца compl_x_deliv.'
assert ((_gg['compl_x_deliv'] - _c).abs() < 1e-9).all(), 'compl_x_deliv не совпадает с произведением complaints * delivery_share.'
assert int(need('n_hi')) == int((_c >= 0.5).sum()), f'n_hi = {need("n_hi")}, а ожидалось {int((_c >= 0.5).sum())}. Условие — больше или равно 0.5.'
assert close(need('rate_hi'), round(_g.loc[_c >= 0.5, 'churned'].mean(), 3)), f'rate_hi = {need("rate_hi")}, а ожидалось {round(_g.loc[_c >= 0.5, "churned"].mean(), 3)}.'
assert close(need('rate_zero'), round(_g.loc[_c == 0, 'churned'].mean(), 3)), f'rate_zero = {need("rate_zero")}, а ожидалось {round(_g.loc[_c == 0, "churned"].mean(), 3)}. Это гости, у которых произведение равно нулю.'
```

### hint
`g["compl_x_deliv"] = g["complaints"] * g["delivery_share"]`; маска — `hi = g["compl_x_deliv"] >= 0.5`.

### hint
`g.loc[hi, "churned"].mean()` — доля ушедших среди отобранных; для нулевых — маска `g["compl_x_deliv"] == 0`.

### solution
```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")
g["compl_x_deliv"] = g["complaints"] * g["delivery_share"]
hi = g["compl_x_deliv"] >= 0.5
n_hi = int(hi.sum())
rate_hi = round(g.loc[hi, "churned"].mean(), 3)
rate_zero = round(g.loc[g["compl_x_deliv"] == 0, "churned"].mean(), 3)
```

### explain
Гостей с высоким произведением всего несколько десятков, но уходят почти все. Для акции удержания это готовый сегмент: недовольные доставкой постоянные клиенты доставки. Правда, бонус на кофе им вряд ли поможет — сначала стоит разобраться с доставкой.

## task: gain | Что даёт признак | base

Функция `cv_auc` из урока уже есть в заготовке. Посчитайте средний CV-AUC (3 знака):

- `auc_base` — на исходной таблице;
- `auc_vpm` — с добавленным столбцом `visits_per_month` (визиты за 90 дней / 3);
- `auc_new` — с добавленным флагом `is_new` (без `visits_per_month`).

Каждый вариант добавляйте к своей копии таблицы (`g.copy()`), чтобы признаки не смешивались.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_kf = _KF(n_splits=5, shuffle=True, random_state=42)
def _cv(df):
    X = _pd.get_dummies(df.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
    a, b, c, d = _tts(X, _y, test_size=0.25, random_state=42, stratify=_y)
    return round(_cvs(_LR(max_iter=2000), _SS().fit_transform(a), c, cv=_kf, scoring='roc_auc').mean(), 3)
_v = _g.copy(); _v['visits_per_month'] = _v['visits_90d'] / 3
_n = _g.copy(); _n['is_new'] = (_n['tenure_months'] <= 3).astype(int)
_rb, _rv, _rn = _cv(_g), _cv(_v), _cv(_n)
assert close(need('auc_base'), _rb), f'auc_base = {need("auc_base")}, а ожидалось {_rb}. Это cv_auc на исходной таблице — до добавления столбцов.'
assert close(need('auc_vpm'), _rv), f'auc_vpm = {need("auc_vpm")}, а ожидалось {_rv}.'
assert close(need('auc_new'), _rn), f'auc_new = {need("auc_new")}, а ожидалось {_rn}. В этой копии должен быть только флаг is_new (tenure_months <= 3), без visits_per_month.'
```

### hint
`v = g.copy()`, `v["visits_per_month"] = v["visits_90d"] / 3`, `auc_vpm = round(cv_auc(v), 3)`.

### hint
Флаг новичка — во второй копии: `n = g.copy()`, `n["is_new"] = (n["tenure_months"] <= 3).astype(int)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

auc_base = round(cv_auc(g), 3)
v = g.copy()
v["visits_per_month"] = v["visits_90d"] / 3
auc_vpm = round(cv_auc(v), 3)
n = g.copy()
n["is_new"] = (n["tenure_months"] <= 3).astype(int)
auc_new = round(cv_auc(n), 3)
print(auc_base, auc_vpm, auc_new)
```

### explain
Визиты в месяц ничего не добавили — это тот же столбец в других единицах. Флаг новичка добавил почти 0.02: он описывает ступеньку, которую линейная модель сама не видит.

## task: pairs | Поиск взаимодействий перебором | star

Взаимодействие жалоб и доставки мы нашли по сводной таблице. А можно ли найти его перебором? Для всех пар столбцов из списка `cols` добавьте к копии таблицы произведение пары (один новый столбец) и посчитайте прирост среднего CV-AUC относительно исходной таблицы (функция `cv_auc` уже есть). Сохраните:

- `gains` — Series приростов; индекс — строки вида `"a*b"`, где `a` и `b` — названия столбцов в порядке, в котором их выдаёт `itertools.combinations(cols, 2)`; отсортирована по убыванию;
- `best` — индекс лучшей пары (строка `"a*b"`).

### starter
```python
import itertools
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

cols = ["tenure_months", "app", "visits_90d", "days_since_last", "delivery_share", "promo_used", "complaints"]
print(list(itertools.combinations(cols, 2))[:3])
```

### check
```python
import itertools as _it
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_kf = _KF(n_splits=5, shuffle=True, random_state=42)
def _cv(df):
    X = _pd.get_dummies(df.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
    a, b, c, d = _tts(X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _cvs(_LR(max_iter=2000), _SS().fit_transform(a), c, cv=_kf, scoring='roc_auc').mean()
_base = _cv(_g)
_cols = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'delivery_share', 'promo_used', 'complaints']
_r = {}
for _a, _b in _it.combinations(_cols, 2):
    _h = _g.copy()
    _h['pair'] = _h[_a] * _h[_b]
    _r[f'{_a}*{_b}'] = _cv(_h) - _base
_r = _pd.Series(_r).sort_values(ascending=False)
_s = need('gains', _pd.Series)
assert len(_s) == len(_r), f'В gains {len(_s)} значений, а пар из 7 столбцов — {len(_r)}.'
assert set(_s.index) == set(_r.index), f'Индекс gains не совпадает с ожидаемым. Пример нужного названия: {_r.index[0]!r} — через * без пробелов, порядок как в combinations.'
assert all(close(float(_s[k]), float(_r[k]), 1e-6) for k in _r.index), 'Значения gains не совпадают. Прирост — cv_auc(копия с произведением) − cv_auc(g); в каждой копии только один новый столбец.'
assert list(_s.index[:3]) == list(_r.index[:3]), 'gains не отсортирована по убыванию.'
assert need('best') == _r.index[0], f'best = {need("best")!r}, а ожидалось {_r.index[0]!r}.'
```

### hint
Цикл `for a, b in itertools.combinations(cols, 2):` перебирает все пары без повторов. Внутри: `h = g.copy()`, `h["pair"] = h[a] * h[b]`, `res[f"{a}*{b}"] = cv_auc(h) - base`.

### hint
Словарь превращается в Series: `pd.Series(res).sort_values(ascending=False)`; лучшая пара — `gains.index[0]`.

### solution
```python
import itertools
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def cv_auc(df, scoring="roc_auc"):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    Xs = StandardScaler().fit_transform(X_train)
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring).mean()

cols = ["tenure_months", "app", "visits_90d", "days_since_last", "delivery_share", "promo_used", "complaints"]
base = cv_auc(g)
res = {}
for a, b in itertools.combinations(cols, 2):
    h = g.copy()
    h["pair"] = h[a] * h[b]
    res[f"{a}*{b}"] = cv_auc(h) - base
gains = pd.Series(res).sort_values(ascending=False)
best = gains.index[0]
print(gains.round(4).head(5))
```

### explain
Перебор нашёл ту же пару, что и сводная таблица, — доставка × жалобы, с заметным отрывом. Остальные приросты меньше 0.003 — в пределах разброса между фолдами. Но осторожно: чем больше вариантов перебираешь, тем выше шанс, что какой-то «выиграет» случайно (как с множественными сравнениями в главе 5). Находку перебора стоит объяснить по смыслу и подтвердить на тесте один раз.
