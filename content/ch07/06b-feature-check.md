---
title: "Форма связи и важность признаков"
lead: "Признак придуман — но помогает ли он на самом деле? Учимся подсказывать модели форму связи логарифмом и интервалами, отличать устойчивый прирост от шума сравнением по фолдам, честно мерить важность признаков перестановкой и ловить признаки из будущего."
files: [guests_churn.csv]
recap:
  - "`np.log1p(x)` сжимает длинный хвост; `pd.cut` + `get_dummies` разбивает число на интервалы, и у каждого интервала свой вес."
  - "Пользу признака проверяют кросс-валидацией на обучающей части, на одних и тех же фолдах, и сравнивают прирост с разбросом между фолдами."
  - "Лесу новые признаки помогают меньше, чем логистической регрессии: пороги и сочетания деревья находят сами."
  - "`feature_importances_` леса завышает важность признаков с множеством разных значений, даже случайного шума. `permutation_importance` на тесте честнее: насколько падает качество, если перемешать признак."
  - "Каждый признак проверяйте вопросом: известно ли его значение на момент прогноза? Если нет — это утечка из будущего."
---

Продолжаем с таблицей гостей и функцией `cv_auc` из урока «Новые признаки»: она готовит признаки, откладывает тот же тест (`random_state=42`) и считает ROC-AUC логистической регрессии по пяти фолдам обучающей части — одним и тем же `kf` для всех вариантов. Метрику задаёт `scoring`. Отправная точка — AUC около 0.877; флаг новичка `is_new` (стаж ≤ 3 месяцев) и произведение `compl_x_deliv` (жалобы × доля доставки) поднимали его примерно до 0.904.

## Форма связи: логарифм и интервалы

Давность последнего визита — самый сильный признак, но связь с уходом у неё не прямая. Посмотрим по интервалам, как в главе 3:

```python
import pandas as pd

g = pd.read_csv("guests_churn.csv")
g["recency"] = pd.cut(g["days_since_last"], [-1, 14, 30, 60, 1000],
                      labels=["до 2 недель", "2–4 недели", "1–2 месяца", "больше 2 месяцев"])
print(g.groupby("recency", observed=True)["churned"].agg(["mean", "size"]).round(3))
```

Риск растёт от 11 % до 84 %, но неравномерно: первые недели без визита значат много, а разница между 100 и 150 днями — почти ничего, такие гости уже почти все ушли. При этом у столбца длинный хвост: около половины гостей были у нас за последнюю неделю, а у некоторых — до 200 дней.

Есть два способа объяснить это модели.

**Логарифм.** `np.log1p(x)` — это натуральный логарифм от (1 + x). Единица добавлена, чтобы ноль дней не давал ошибку: log1p(0) = 0. Логарифм растягивает маленькие значения и сжимает большие:

::: predict
```python static
import numpy as np
print([round(float(v), 2) for v in np.log1p([0, 9, 99])])
```

- `[0.0, 9.0, 99.0]`
- [x] `[0.0, 2.3, 4.61]`
- `[1.0, 10.0, 100.0]`

Почему: log1p(9) = ln 10 ≈ 2.3, log1p(99) = ln 100 ≈ 4.61. Между 0 и 9 днями — 2.3 «логарифмических единицы», а между 9 и 99 — столько же ещё: в десять раз больше дней — плюс 2.3.
:::

**Интервалы.** `pd.cut` разбивает число на группы, а `get_dummies` превращает группу во флаги — по одному на интервал. Тогда у каждого интервала свой вес, и форма связи может быть любой. Наша функция `cv_auc` вызывает `get_dummies` для всей таблицы, поэтому столбец `recency` она превратит во флаги сама.

::: figure recency-shape
Давность визита тремя способами. Сверху — доля ушедших по интервалам: риск растёт быстро в первые недели и медленно потом. Снизу — те же дни после `np.log1p`: первые недели растянуты, длинный хвост сжат.
:::

```python
import numpy as np
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
    return cross_val_score(LogisticRegression(max_iter=2000), Xs, y_train, cv=kf, scoring=scoring)   # 5 оценок, по фолду

g_log = g.copy()
g_log["log_days"] = np.log1p(g_log["days_since_last"])
g_bins = g.copy()
g_bins["recency"] = pd.cut(g_bins["days_since_last"], [-1, 14, 30, 60, 1000],
                           labels=["до 2 недель", "2–4 недели", "1–2 месяца", "больше 2 месяцев"])
base, log, bins = cv_auc(g), cv_auc(g_log), cv_auc(g_bins)
print(f"исходные:   {base.mean():.3f} ± {base.std():.3f}")
print(f"логарифм:   {log.mean():.3f}")
print(f"интервалы:  {bins.mean():.3f}")
print("логарифм − исходные по фолдам: ", (log - base).round(3))
print("интервалы − исходные по фолдам:", (bins - base).round(3))
```

`g.copy()` нужен, чтобы варианты не мешали друг другу: каждый добавляет свой столбец к своей копии.

В среднем оба способа прибавляют 0.004–0.006 — меньше, чем разброс между фолдами (0.012). По одним средним не понять, находка это или шум. Но фолды у всех вариантов **одни и те же**, поэтому их можно сравнить попарно — на каждом фолде отдельно, как парный тест в главе 5. Логарифм выигрывает на всех пяти фолдах (от +0.001 до +0.012): прирост маленький, но устойчивый — это находка. Интервалы выигрывают на двух фолдах, а на трёх идут вровень с исходными: прирост держится на двух нарезках — сомнительно. Правило: **признак полезен, если на тех же фолдах он выигрывает почти везде**, а не только в среднем.

Соберём лучшие находки — флаг новичка, взаимодействие и логарифм давности — и сравним, сколько они дают логистической регрессии и лесу:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def scores(df):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    lr = cross_val_score(LogisticRegression(max_iter=2000), StandardScaler().fit_transform(X_train), y_train, cv=kf, scoring="roc_auc")
    rf = cross_val_score(RandomForestClassifier(n_estimators=50, random_state=0), X_train, y_train, cv=kf, scoring="roc_auc")
    return lr, rf

new = g.copy()
new["is_new"] = (new["tenure_months"] <= 3).astype(int)
new["compl_x_deliv"] = new["complaints"] * new["delivery_share"]
new["log_days"] = np.log1p(new["days_since_last"])

for name, df in [("исходные", g), ("с новыми", new)]:
    lr, rf = scores(df)
    print(f"{name:9} логрегрессия {lr.mean():.3f} ± {lr.std():.3f}   лес {rf.mean():.3f} ± {rf.std():.3f}")
```

У логистической регрессии AUC вырос примерно с 0.877 до 0.911 — она обогнала лес. А лес прибавил меньше 0.01 — это меньше разброса между фолдами (около 0.016), то есть почти ничего. Дерево само задаёт вопросы «стаж ≤ 3?» и «жалобы > 0, и если да — доставка > 0.5?», поэтому ступеньки и взаимодействия ему подсказывать не нужно. Конструирование признаков сильнее всего помогает простым моделям — а простые модели проще объяснять и быстрее считать.

::: warn Сравнивайте с разбросом
Прирост меньше разброса между фолдами по одному среднему не оценить: на другой нарезке он может смениться падением. Сравнивайте варианты на одних и тех же фолдах (один `kf` на всё) и смотрите разницу по каждому фолду: устойчивый прирост виден на всех или почти всех фолдах, шум — то плюс, то минус.
:::

{{practice: p-recency, bins, combo, rf-gain}}

## Какие признаки важны: два способа

У случайного леса есть встроенная важность — `feature_importances_` из главы 6: насколько в среднем каждый признак уменьшал «перемешанность» листьев при разбиениях. Посчитать её дёшево, но у неё есть известный перекос. Проверим: добавим столбец чистого шума — случайные числа, никак не связанные с уходом.

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X["noise"] = np.random.RandomState(0).rand(len(X))
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

forest = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
print(pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False).round(3).head(8))
```

`np.random.RandomState(0).rand(n)` — n случайных чисел от 0 до 1, с фиксированным зерном, чтобы результат повторялся. Это старый способ получить случайные числа; новый — `default_rng`, глава 5. Шум получил важность около 0.09 и обогнал промоакции, приложение, города и категории. А средний чек — на втором месте, хотя, как покажет перестановка, модель на него почти не опирается. Причина: у шума и чека почти все значения разные, и дерево находит среди них множество порогов, которые на обучающих данных случайно что-то разделяют. Встроенная важность меряет, **как часто признак пригодился при обучении**, а не насколько он полезен на новых гостях.

::: warn Перекос встроенной важности
Чем больше разных значений у признака, тем выше его встроенная важность — даже у чистого шума. Флаг можно разрезать один раз, а число с тысячей значений — где угодно.
:::

Честнее **важность перестановкой** (permutation importance). Идея простая: берём обученную модель и тест, перемешиваем значения одного столбца — связь признака с ответом разрушена, остальное как было. Если качество заметно упало — модель на этот признак действительно опиралась. Если нет — признак ей не нужен.

::: figure perm-imp
Важность перестановкой на условных числах: перемешиваем один столбец теста, остальные не трогаем, и смотрим, насколько упал AUC той же модели.
:::

::: tip Аналогия
Чтобы понять, насколько важен бариста в утренней смене, его на день меняют случайным сотрудником с кухни, а всё остальное оставляют как было. Очередь выросла вдвое — бариста был важен; ничего не изменилось — смена держалась не на нём. Перестановка столбца делает то же с признаком: заменяет его значения «чужими» и смотрит на результат.
:::

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X["noise"] = np.random.RandomState(0).rand(len(X))
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)

pi = permutation_importance(forest, X_test, y_test, scoring="roc_auc", n_repeats=5, random_state=0)
imp = pd.DataFrame({"падение AUC": pi.importances_mean, "разброс": pi.importances_std}, index=X.columns)
print(imp.sort_values("падение AUC", ascending=False).round(3).head(8))
```

- `permutation_importance(модель, X, y, ...)` из `sklearn.inspection` работает с любой обученной моделью;
- `scoring` — по какой метрике мерить падение; `n_repeats=5` — перемешать каждый столбец пять раз и усреднить, `random_state` — для повторяемости;
- `importances_mean` — среднее падение качества, `importances_std` — его разброс.

Картина другая: впереди давность визита и жалобы (перемешаешь любой из них — AUC падает больше чем на 0.1), за ними стаж. Шум и средний чек — около нуля. Небольшие отрицательные значения тоже бывают: перемешивание бесполезного столбца иногда случайно чуть улучшает результат.

::: tip Где считать
Важность перестановкой считают на тесте или на валидации — там, где модель не училась. На обучающих данных переобученная модель «опирается» и на шум, и перестановка это покажет как важность.
:::

{{practice: perm, noise-rank}}

## Признаки из будущего

Самая опасная ошибка при конструировании — признак, которого не будет в момент прогноза. В главе 6 мы нашли `card_blocked`: карту блокируют **после** ухода гостя. Вот что будет, если её не убрать:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)
X = pd.get_dummies(g.drop(columns=["guest_id", "churned"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
auc = cross_val_score(LogisticRegression(max_iter=2000), StandardScaler().fit_transform(X_train), y_train, cv=kf, scoring="roc_auc")
print(f"AUC с card_blocked: {auc.mean():.3f}")
```

AUC почти 0.99 — и ноль пользы: 1 октября, когда нужно решать, кому дать бонус, ни у кого из ещё не ушедших гостей карта не заблокирована.

Когда признаки придумываешь сам, утечку сделать ещё проще. Несколько типичных ловушек:

- **окно данных шире среза**: «визитов за 90 дней», посчитанные на дату выгрузки 1 декабря, а не на 1 октября, уже включают те 60 дней, за которые мы определяем уход;
- **признак, посчитанный по ответу**: «доля ушедших в городе гостя» по всей таблице — в ней сидит `churned` того же гостя. Такие признаки считают только по обучающей части: доли по городам — по `X_train` и `y_train` (`y_train.groupby(X_train["city"]).mean()`), а в тест подставляют через `map` по городу. В кросс-валидации — заново в каждом обучающем фолде. Как упаковать это в шаг конвейера, чтобы фолды считались сами, — в уроке «Свои шаги конвейера: порядок категорий, функции и свой класс» (углубление после «Pipeline»);
- **последствия ухода**: звонок в поддержку с просьбой удалить карту, отписка от рассылки, возврат подарочного сертификата.

::: figure window-leak
Окно признака должно заканчиваться в момент среза. «Визиты за 90 дней», посчитанные на 1 декабря, захватывают окно ответа: ноль визитов в октябре–ноябре — это почти и есть «ушёл».
:::

Проверка одна: для каждого признака спросите «будет ли это значение известно в тот момент, когда модель должна дать прогноз?». Если ответ «нет» или «не уверен» — признак не берём.

::: warn Подозрительно хорошо
Если новый признак резко поднял качество — с 0.88 до 0.97, — сначала ищите утечку, а уже потом радуйтесь. Честные признаки обычно дают прибавки в сотые доли, как флаг новичка.
:::

::: warn Типичные ошибки
- **Вывод по одному среднему.** Прирост меньше разброса между фолдами без сравнения по каждому фолду — не находка; `kf` — один на все сравнения.
- **Важность по `feature_importances_`.** Встроенная важность леса завышает признаки с множеством разных значений; для рейтинга пользы берите перестановку на тесте или валидации.
- **Перестановка на обучающих данных.** Переобученная модель «опирается» и на шум — считайте там, где модель не училась.
- **Признак из будущего.** Перед добавлением спросите: известно ли значение в момент прогноза?
:::

::: quiz
Встроенная важность леса ставит `avg_check` на второе место, а важность перестановкой — почти в ноль. Какой рейтинг показать отделу лояльности?

- [x] Перестановку: она меряет, насколько модель опирается на признак на новых гостях; встроенная важность завышает признаки с множеством разных значений
  > Средний чек почти у всех разный, и деревья находят в нём много порогов, которые случайно что-то разделяют на train. Перестановка на тесте показывает, что модель на него не опирается.
- [ ] Встроенную: её посчитала сама модель, значит, она точнее
  > Модель посчитала, как часто признак использовался при обучении, — а это не то же, что польза. Шум в этом рейтинге тоже оказался высоко.
- [ ] Оба: пусть отдел сам выберет
  > Два противоречащих рейтинга без объяснения запутают. Объясните, почему один из них честнее.
- [ ] Никакой: важность у леса считать нельзя
  > Можно — перестановкой. Она работает с любой моделью.
:::

## Практика

## task: p-recency | Давность по интервалам | warmup

Соберите программу: разбить давность визита на интервалы и посчитать долю ушедших в каждом интервале. Результат — Series `rates`.

### parsons
```python
import pandas as pd
g = pd.read_csv("guests_churn.csv")
bins = [-1, 14, 30, 60, 1000]
labels = ["до 2 недель", "2–4 недели", "1–2 месяца", "больше 2 месяцев"]
g["recency"] = pd.cut(g["days_since_last"], bins, labels=labels)
rates = g.groupby("recency", observed=True)["churned"].mean()
print(rates.round(3))
```

### check
```python
import pandas as _pd
_g = _pd.read_csv('guests_churn.csv')
_r = _g.groupby(_pd.cut(_g['days_since_last'], [-1, 14, 30, 60, 1000]), observed=True)['churned'].mean()
_s = need('rates', _pd.Series)
assert len(_s) == 4, f'В rates {len(_s)} значений, а интервалов четыре.'
assert all(close(float(a), float(b), 1e-9) for a, b in zip(_s, _r)), 'Доли ушедших по интервалам не совпадают. Сначала столбец recency, потом группировка по нему.'
assert [str(v) for v in _s.index] == ['до 2 недель', '2–4 недели', '1–2 месяца', 'больше 2 месяцев'], 'Индекс rates — названия интервалов из labels, по порядку.'
```

### hint
Порядок: данные → границы и названия → столбец `recency` через `pd.cut` → группировка → вывод.

## task: bins | Интервалы давности в модели | base

Добавьте в копию таблицы столбец `recency` — давность визита по интервалам `[-1, 14, 30, 60, 1000]` (названия интервалов — любые). Посчитайте `auc_bins` — средний CV-AUC с этим столбцом (3 знака) и `n_cols` — сколько столбцов получается в таблице признаков после `get_dummies` (столько признаков видит модель).

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

b = g.copy()
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
_b = _g.copy()
_b['recency'] = _pd.cut(_b['days_since_last'], [-1, 14, 30, 60, 1000])
_X = _pd.get_dummies(_b.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _bb, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = round(_cvs(_LR(max_iter=2000), _SS().fit_transform(_a), _c, cv=_kf, scoring='roc_auc').mean(), 3)
assert int(need('n_cols')) == _X.shape[1], f'n_cols = {need("n_cols")}, а ожидалось {_X.shape[1]}: 15 исходных признаков и по флагу на каждый из четырёх интервалов.'
assert close(need('auc_bins'), _w), f'auc_bins = {need("auc_bins")}, а ожидалось {_w}. Границы — [-1, 14, 30, 60, 1000], столбец recency добавлен к копии таблицы.'
```

### hint
`b["recency"] = pd.cut(b["days_since_last"], [-1, 14, 30, 60, 1000])` — без `labels` интервалы назовутся сами.

### hint
Число столбцов: `pd.get_dummies(b.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).shape[1]`.

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

b = g.copy()
b["recency"] = pd.cut(b["days_since_last"], [-1, 14, 30, 60, 1000])
n_cols = pd.get_dummies(b.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).shape[1]
auc_bins = round(cv_auc(b), 3)
```

### explain
Интервал из `pd.cut` — категория, и `get_dummies` превращает его в четыре флага, как город. Флаги интервалов добавлены к исходному `days_since_last`, поэтому модель может описать и общий рост риска, и «ступеньки» между интервалами.

## task: combo | Три признака вместе | base

Добавьте в копию таблицы три признака: `is_new` (стаж ≤ 3 месяцев, 0/1), `compl_x_deliv` (жалобы × доля доставки) и `log_days` (`np.log1p` от давности визита). Посчитайте средний CV-AUC `auc_all` и средний CV-F1 `f1_all` (оба — 3 знака), а также прирост F1 по сравнению с исходной таблицей `f1_gain` (3 знака, считайте по неокруглённым значениям).

### starter
```python
import numpy as np
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
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_kf = _KF(n_splits=5, shuffle=True, random_state=42)
def _cv(df, sc):
    X = _pd.get_dummies(df.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
    a, b, c, d = _tts(X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _cvs(_LR(max_iter=2000), _SS().fit_transform(a), c, cv=_kf, scoring=sc).mean()
_n = _g.copy()
_n['is_new'] = (_n['tenure_months'] <= 3).astype(int)
_n['compl_x_deliv'] = _n['complaints'] * _n['delivery_share']
_n['log_days'] = _np.log1p(_n['days_since_last'])
_au, _f, _f0 = _cv(_n, 'roc_auc'), _cv(_n, 'f1'), _cv(_g, 'f1')
assert close(need('auc_all'), round(_au, 3)), f'auc_all = {need("auc_all")}, а ожидалось {round(_au, 3)}. Проверьте все три признака: стаж <= 3, произведение жалоб на долю доставки, np.log1p давности.'
assert close(need('f1_all'), round(_f, 3)), f'f1_all = {need("f1_all")}, а ожидалось {round(_f, 3)}. Для F1 передайте в cv_auc scoring="f1".'
assert close(need('f1_gain'), round(_f - _f0, 3)), f'f1_gain = {need("f1_gain")}, а ожидалось {round(_f - _f0, 3)} — разница F1 с новыми признаками и на исходной таблице.'
```

### hint
Второй аргумент функции — метрика: `cv_auc(new, "f1")`.

### hint
`f1_gain = round(cv_auc(new, "f1") - cv_auc(g, "f1"), 3)` — вычитайте неокруглённые значения.

### solution
```python
import numpy as np
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

new = g.copy()
new["is_new"] = (new["tenure_months"] <= 3).astype(int)
new["compl_x_deliv"] = new["complaints"] * new["delivery_share"]
new["log_days"] = np.log1p(new["days_since_last"])
auc_all = round(cv_auc(new), 3)
f1_new = cv_auc(new, "f1")
f1_all = round(f1_new, 3)
f1_gain = round(f1_new - cv_auc(g, "f1"), 3)
```

### explain
F1 вырос почти на 0.07 — без смены модели и без подбора настроек. Для отдела лояльности это значит меньше лишних бонусов и меньше пропущенных уходящих гостей при том же пороге.

## task: rf-gain | Кому нужны новые признаки | plus

Сравните, сколько дают три признака из задачи «Три признака вместе» (`is_new`, `compl_x_deliv`, `log_days`) двум моделям. Посчитайте средний CV-AUC на обучающей части (одни и те же фолды `kf`) для таблиц без и с новыми признаками:

- логистическая регрессия — как в `cv_auc` (масштаб + `LogisticRegression(max_iter=2000)`);
- лес — `RandomForestClassifier(n_estimators=50, random_state=0)` без масштабирования.

Сохраните приросты `lr_gain` и `rf_gain` (новые минус исходные, 3 знака, по неокруглённым средним) и `rf_std` — разброс (`std`) AUC леса по фолдам на исходной таблице (3 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

new = g.copy()
new["is_new"] = (new["tenure_months"] <= 3).astype(int)
new["compl_x_deliv"] = new["complaints"] * new["delivery_share"]
new["log_days"] = np.log1p(new["days_since_last"])

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_kf = _KF(n_splits=5, shuffle=True, random_state=42)
_n = _g.copy()
_n['is_new'] = (_n['tenure_months'] <= 3).astype(int)
_n['compl_x_deliv'] = _n['complaints'] * _n['delivery_share']
_n['log_days'] = _np.log1p(_n['days_since_last'])
def _sc(df):
    X = _pd.get_dummies(df.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
    a, b, c, d = _tts(X, _y, test_size=0.25, random_state=42, stratify=_y)
    lr = _cvs(_LR(max_iter=2000), _SS().fit_transform(a), c, cv=_kf, scoring='roc_auc')
    rf = _cvs(_RF(n_estimators=50, random_state=0), a, c, cv=_kf, scoring='roc_auc')
    return lr, rf
_l0, _r0 = _sc(_g)
_l1, _r1 = _sc(_n)
assert close(need('lr_gain'), round(_l1.mean() - _l0.mean(), 3)), f'lr_gain = {need("lr_gain")}, а ожидалось {round(_l1.mean() - _l0.mean(), 3)}. Логистическая регрессия — на отмасштабированной обучающей части.'
assert close(need('rf_gain'), round(_r1.mean() - _r0.mean(), 3)), f'rf_gain = {need("rf_gain")}, а ожидалось {round(_r1.mean() - _r0.mean(), 3)}. Лес — RandomForestClassifier(n_estimators=50, random_state=0) на X_train без масштаба, cv=kf.'
assert close(need('rf_std'), round(_r0.std(), 3)), f'rf_std = {need("rf_std")}, а ожидалось {round(_r0.std(), 3)}. Это .std() массива из cross_val_score леса на исходной таблице.'
```

### hint
Напишите функцию, которая по таблице возвращает два массива оценок: `get_dummies` → `train_test_split` → `cross_val_score` для логистической регрессии (на `StandardScaler().fit_transform(X_train)`) и для леса (на `X_train`).

### hint
Прирост — разница средних: `lr_new.mean() - lr_old.mean()`; разброс — `rf_old.std()`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
kf = KFold(n_splits=5, shuffle=True, random_state=42)

new = g.copy()
new["is_new"] = (new["tenure_months"] <= 3).astype(int)
new["compl_x_deliv"] = new["complaints"] * new["delivery_share"]
new["log_days"] = np.log1p(new["days_since_last"])

def scores(df):
    X = pd.get_dummies(df.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    lr = cross_val_score(LogisticRegression(max_iter=2000), StandardScaler().fit_transform(X_train), y_train, cv=kf, scoring="roc_auc")
    rf = cross_val_score(RandomForestClassifier(n_estimators=50, random_state=0), X_train, y_train, cv=kf, scoring="roc_auc")
    return lr, rf

lr_old, rf_old = scores(g)
lr_new, rf_new = scores(new)
lr_gain = round(lr_new.mean() - lr_old.mean(), 3)
rf_gain = round(rf_new.mean() - rf_old.mean(), 3)
rf_std = round(rf_old.std(), 3)
print(lr_gain, rf_gain, rf_std)
```

### explain
Логистическая регрессия прибавила больше 0.03 — в разы больше разброса. Прирост леса меньше разброса между фолдами: сказать, что признаки ему помогли, нельзя. Признаки, придуманные для одной модели, стоит проверять отдельно для каждой.

## task: perm | Важность перестановкой | base

Обучите `RandomForestClassifier(n_estimators=50, random_state=0)` на обучающей части и посчитайте важность перестановкой на **тесте**: `scoring="roc_auc"`, `n_repeats=5`, `random_state=0`. Сохраните:

- `pi_s` — Series средних падений AUC с названиями признаков в индексе, отсортированную по убыванию;
- `top3` — список трёх самых важных признаков;
- `check_pi` — важность `avg_check` по перестановке (3 знака);
- `check_place` — место `avg_check` (1 — первое) по встроенной `feature_importances_` того же леса.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

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
from sklearn.inspection import permutation_importance as _pi
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_f = _RF(n_estimators=50, random_state=0).fit(_a, _c)
_p = _pd.Series(_pi(_f, _b, _d, scoring='roc_auc', n_repeats=5, random_state=0).importances_mean, index=_X.columns).sort_values(ascending=False)
_fi = _pd.Series(_f.feature_importances_, index=_X.columns).sort_values(ascending=False)
_s = need('pi_s', _pd.Series)
assert set(_s.index) == set(_X.columns), 'В индексе pi_s должны быть названия признаков: index=X.columns.'
assert (_s - _p).abs().max() < 1e-6, 'pi_s не совпадает с ожидаемым. Важность считается на X_test, y_test с scoring="roc_auc", n_repeats=5, random_state=0; берите importances_mean.'
assert list(_s.index[:3]) == list(_p.index[:3]), 'pi_s не отсортирована по убыванию: .sort_values(ascending=False).'
assert list(need('top3')) == list(_p.index[:3]), f'top3 = {need("top3")}. Это первые три названия в pi_s.'
assert close(need('check_pi'), round(_p['avg_check'], 3)), f'check_pi = {need("check_pi")}, а ожидалось {round(_p["avg_check"], 3)}.'
_pl = list(_fi.index).index('avg_check') + 1
assert int(need('check_place')) == _pl, f'check_place = {need("check_place")}, а ожидалось {_pl}. Отсортируйте feature_importances_ по убыванию и найдите позицию avg_check (с 1).'
```

### hint
`pi = permutation_importance(forest, X_test, y_test, scoring="roc_auc", n_repeats=5, random_state=0)`, затем `pd.Series(pi.importances_mean, index=X.columns)`.

### hint
Место во встроенной важности: `list(fi.index).index("avg_check") + 1`, где `fi` — `feature_importances_` в Series, отсортированная по убыванию.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

forest = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
pi = permutation_importance(forest, X_test, y_test, scoring="roc_auc", n_repeats=5, random_state=0)
pi_s = pd.Series(pi.importances_mean, index=X.columns).sort_values(ascending=False)
top3 = list(pi_s.index[:3])
check_pi = round(pi_s["avg_check"], 3)
fi = pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False)
check_place = list(fi.index).index("avg_check") + 1
print(pi_s.round(3).head(5))
```

### explain
Встроенная важность ставит средний чек в число лидеров, а перестановка показывает, что без него модель на тесте работает так же. Если отдел лояльности спросит «на что смотрит модель?», показывайте важность перестановкой.

## task: noise-rank | Шум в рейтинге | plus

В заготовке к признакам добавлен столбец случайного шума `noise`. Обучите `RandomForestClassifier(n_estimators=100, random_state=0)` и сравните два рейтинга важности. Сохраните место столбца `noise` (1 — первое): `noise_fi` — по `feature_importances_`, `noise_pi` — по важности перестановкой на тесте (`scoring="roc_auc"`, `n_repeats=5`, `random_state=0`). В `below_noise` — список признаков, которые по `feature_importances_` стоят **ниже** шума (в порядке рейтинга).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X["noise"] = np.random.RandomState(0).rand(len(X))
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.inspection import permutation_importance as _pi
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_X['noise'] = _np.random.RandomState(0).rand(len(_X))
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_f = _RF(n_estimators=100, random_state=0).fit(_a, _c)
_fi = list(_pd.Series(_f.feature_importances_, index=_X.columns).sort_values(ascending=False).index)
_p = list(_pd.Series(_pi(_f, _b, _d, scoring='roc_auc', n_repeats=5, random_state=0).importances_mean, index=_X.columns).sort_values(ascending=False).index)
assert int(need('noise_fi')) == _fi.index('noise') + 1, f'noise_fi = {need("noise_fi")}, а ожидалось {_fi.index("noise") + 1}. Сортируйте feature_importances_ по убыванию; место считается с 1.'
assert int(need('noise_pi')) == _p.index('noise') + 1, f'noise_pi = {need("noise_pi")}, а ожидалось {_p.index("noise") + 1}. Важность перестановкой — на X_test, y_test, scoring="roc_auc", n_repeats=5, random_state=0.'
_below = _fi[_fi.index('noise') + 1:]
assert list(need('below_noise')) == _below, f'below_noise = {need("below_noise")}. Нужны признаки, которые в рейтинге feature_importances_ идут после noise, — их {len(_below)}.'
```

### hint
Отсортированный список названий: `list(pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False).index)`. Место — `.index("noise") + 1`.

### hint
Признаки ниже шума — срез списка после позиции шума: `names[names.index("noise") + 1:]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X["noise"] = np.random.RandomState(0).rand(len(X))
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

forest = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
fi = list(pd.Series(forest.feature_importances_, index=X.columns).sort_values(ascending=False).index)
pi = permutation_importance(forest, X_test, y_test, scoring="roc_auc", n_repeats=5, random_state=0)
pr = list(pd.Series(pi.importances_mean, index=X.columns).sort_values(ascending=False).index)
noise_fi = fi.index("noise") + 1
noise_pi = pr.index("noise") + 1
below_noise = fi[noise_fi:]
print(noise_fi, noise_pi, below_noise)
```

### explain
По встроенной важности шум обогнал промоакции, приложение, города и категории — признаки, которые с уходом действительно связаны (приложение, например, снижает риск). Перестановка ставит шум в нижнюю половину рейтинга, с важностью около нуля. Простое правило: если сомневаетесь в признаке, добавьте столбец шума и посмотрите, обгоняет ли признак шум по важности перестановкой.
