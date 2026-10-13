---
title: "Проект: кто из гостей уйдёт"
lead: "Финал главы. Отдел лояльности хочет вернуть гостей, которые вот-вот перестанут ходить в «Зерно», — но бонусы стоят денег, и раздавать их всем подряд нельзя. Строим модель оттока от осмотра данных до списка гостей для акции: ищем утечку, подбираем модель честной валидацией и считаем, насколько модель лучше правила."
files: [guests_churn.csv]
recap:
  - "Проект ML начинается не с модели, а с вопроса: что предсказываем, к какому моменту и какие данные известны в этот момент."
  - "Пропуск — тоже информация: средний чек пуст, потому что визитов не было, и честное заполнение — 0."
  - "Подозрительно высокое качество — повод искать утечку: признак, который становится известен вместе с ответом или после него."
  - "Схема: отложить тест (stratify), выбрать модель и настройки кросс-валидацией на обучающей части, один раз проверить на тесте."
  - "Сравнивайте модель не только с «всегда нет», но и с правилом, которое бизнес уже использует."
  - "Модель полезна не только ответом «да/нет», но и ранжированием: список самых рискованных гостей для акции."
---

## Задача

> Мы хотим запустить акцию удержания: гостям, которые скорее всего перестанут к нам ходить, отправить бонус на следующий визит. Бюджет — на 10 % гостей. Сейчас мы считаем гостя «уходящим», если он не был у нас больше 45 дней, но к этому моменту возвращать его, кажется, поздно. Можно ли заранее найти тех, кто уйдёт, и насколько такой список лучше нашего правила?

Данные — `guests_churn.csv`: срез по гостям с картой лояльности на 1 октября и итог следующих 60 дней.

Столбцы: `guest_id`, `city`, `tenure_months` — сколько месяцев гость с нами, `app` — пользуется ли приложением (1/0), `visits_90d` — визитов за последние 90 дней, `days_since_last` — дней с последнего визита, `avg_check` — средний чек за 90 дней, `delivery_share` — доля заказов с доставкой, `fav_category` — что чаще берёт (кофе / не кофе / еда), `promo_used` — сколько раз пользовался акциями, `complaints` — число жалоб, `card_blocked` — заблокирована ли карта (1/0). Целевой признак `churned` — не пришёл ни разу за 60 дней после среза (1/0).

::: figure churn-timeline
Как устроен срез: признаки собраны за 90 дней до 1 октября, ответ — что гость делал следующие 60 дней. Всё, что заполняется после среза, в признаки брать нельзя — даже если столбец лежит в той же таблице.
:::

## Разберём вместе: как распознать утечку до обучения

Шаг 3 — самый коварный в проекте, поэтому разберём логику заранее на выдуманном признаке. Пусть в таблице есть столбец «анкета удалена» (1/0) — гость попросил стереть свои данные. Посмотрим на маленькую сводку:

| анкета удалена | гостей | ушли |
|---|---|---|
| 0 | 90 | 8 |
| 1 | 10 | 10 |

1. Доля ухода при 0: 8 / 90 ≈ 9 %; при 1: 10 / 10 = **100 %**. Признак идеально отделяет часть ушедших.
2. Вопрос не «сильный ли признак», а **когда он становится известен**. Анкету удаляют, когда гость решил с нами расстаться, — то есть после ухода или вместе с ним.
3. В момент, когда отдел лояльности решает, кому дать бонус, у уходящего гостя анкета ещё на месте. Значит, в прогнозе признак всегда будет 0, а модель, которая на нём выросла, ошибётся.

Что получилось: «подозрительно хорошая» доля (100 %, 98 %) — повод спросить, откуда взялся столбец и когда он заполняется. Метрики утечку не покажут — на тесте она выглядит как отличная модель.

## План

1. Осмотреть данные и долю ушедших.
2. Разобраться с пропусками среднего чека.
3. Проверить признаки на утечку.
4. Собрать признаки и отложить тест.
5. Базовая модель и правило «45 дней».
6. Дерево: подбор глубины кросс-валидацией.
7. Лес и логистическая регрессия: выбрать модель.
8. Финальная проверка на тесте.
9. Список гостей для акции.
10. Тихий риск: кого правило не видит.

Начиная с пятого шага, перед задачей курс сам готовит `g` (с заполненным `avg_check`), `X`, `y`, `X_train`, `X_test`, `y_train`, `y_test` — как в шаге 4 — и фолды `kf = KFold(n_splits=5, shuffle=True, random_state=42)`.

::: tip
Это повторение всей главы: урок «Честное сравнение моделей» — схема валидации, уроки «Категориальные признаки и утечки», «Случайный лес» и «Логистическая регрессия и вероятности» — признаки, лес и логистическая регрессия. В подсказках указано, на какой урок опирается шаг.
:::

::: warn Типичные ошибки проекта
- **Пустой чек заменён средним.** Пропуск здесь означает «визитов не было», честное значение — 0.
- **Признак-следствие.** Всё, что заполняется после ухода, — вон из `X`, как бы хорошо оно ни предсказывало.
- **Модель выбрана по тесту.** Выбор — по кросс-валидации на train, тест — один раз.
- **Отчёт одной accuracy.** Директору важно, сколько уходящих попало в список акции и сколько бонусов ушло зря.
:::

::: quiz
В шаге 5 правило «не был больше 45 дней — уйдёт» окажется право примерно в 82 % случаев, а ответ «никто не уйдёт» — в 78 %. Что из этого следует для модели?

- [x] Правило — та планка, которую модель должна побить; 82 % против 78 % — улучшение всего на 4 п.п., и модели есть куда расти
  > Базовая модель показывает, сколько даёт «ничего не делать», правило — сколько уже даёт опыт аналитика. Модель полезна, только если обгоняет правило.
- [ ] Модели достаточно побить 78 %: это и есть базовая модель
  > Побить «никто не уйдёт» умеет и правило. Если модель хуже правила, проще пользоваться правилом.
- [ ] 82 % — уже отлично, модель не нужна
  > Accuracy правила не говорит, хорошо ли оно находит уходящих заранее. Заказчик как раз жалуется, что правило ловит их поздно.
- [ ] Сравнивать модель с правилом нельзя: правило не обучалось
  > Можно и нужно — на тех же тестовых гостях. Правило — тоже модель, только придуманная человеком.
:::

## Практика

## task: look | Шаг 1. Осмотр | base

Загрузите `guests_churn.csv` в `g`. Сохраните:

- `churn_rate` — долю ушедших гостей (3 знака);
- `na_check` — сколько пропусков в `avg_check`;
- `na_no_visits` — `True`, если **у всех** гостей с пропущенным `avg_check` `visits_90d == 0`;
- `churn_no_visits` — долю ушедших среди гостей без визитов за 90 дней (3 знака).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
import pandas as pd
```

### check
```python
import pandas as _pd
_g = _pd.read_csv('guests_churn.csv')
_x = need('g', _pd.DataFrame)
assert len(_x) == len(_g) and list(_x.columns) == list(_g.columns), 'g — вся таблица guests_churn.csv без изменений.'
assert close(need('churn_rate'), round(_g['churned'].mean(), 3)), f'churn_rate = {need("churn_rate")}, а ожидалось {round(_g["churned"].mean(), 3)}.'
assert need('na_check') == _g['avg_check'].isna().sum(), f'na_check = {need("na_check")}: посчитайте пропуски в avg_check.'
_w = bool((_g.loc[_g['avg_check'].isna(), 'visits_90d'] == 0).all())
assert need('na_no_visits') == _w, f'na_no_visits должно быть {_w}: возьмите строки с пустым avg_check и проверьте visits_90d.'
_c = round(_g.loc[_g['visits_90d'] == 0, 'churned'].mean(), 3)
assert close(need('churn_no_visits'), _c), f'churn_no_visits = {need("churn_no_visits")}, а ожидалось {_c}.'
```

### hint
Глава 3: `g["avg_check"].isna().sum()`; маска пропусков — `g["avg_check"].isna()`.

### hint
«Все» — `(…== 0).all()`.

### solution
```python
import pandas as pd
g = pd.read_csv("guests_churn.csv")
churn_rate = round(g["churned"].mean(), 3)
na_check = g["avg_check"].isna().sum()
na_no_visits = bool((g.loc[g["avg_check"].isna(), "visits_90d"] == 0).all())
churn_no_visits = round(g.loc[g["visits_90d"] == 0, "churned"].mean(), 3)
print(churn_rate, na_check, na_no_visits, churn_no_visits)
```

### explain
Уходит примерно каждый пятый гость (22 %) — классы несбалансированы, базовая модель «никто не уйдёт» будет права в 78 % случаев. Пропуски в `avg_check` не случайны: это ровно гости без визитов за 90 дней, и почти все они (88 %) не вернутся.

## task: missing | Шаг 2. Пропуски среднего чека | base

`g` уже загружена. Средний чек пуст у гостей без визитов: делить сумму покупок на ноль визитов нельзя. Заполнять его средним или медианой — значит сказать модели, что эти гости тратят как обычные, хотя они не потратили ничего. Честное значение — 0.

Заполните пропуски `avg_check` нулём **в `g`** и сохраните `filled` — сколько значений заполнили. Затем сравните средний чек ушедших и оставшихся среди гостей **с визитами**: `check_churned` и `check_stayed` (0 знаков).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
g = pd.read_csv("guests_churn.csv")
```

### starter
```python
# g — исходная таблица
```

### check
```python
_g = _ref()[0]
_x = need('g')
assert _x['avg_check'].isna().sum() == 0, 'В g всё ещё есть пропуски avg_check — заполните их и сохраните результат в g["avg_check"].'
assert (_x['avg_check'] == _g['avg_check']).all(), 'Пропуски avg_check нужно заполнить нулём, остальные значения — не трогать.'
assert need('filled') == (_g['visits_90d'] == 0).sum(), f'filled = {need("filled")}: это число пропусков до заполнения.'
_v = _g[_g['visits_90d'] > 0]
_a, _b = round(_v.loc[_v['churned'] == 1, 'avg_check'].mean()), round(_v.loc[_v['churned'] == 0, 'avg_check'].mean())
assert close(need('check_churned'), _a, 0.6) and close(need('check_stayed'), _b, 0.6), f'check_churned, check_stayed = {need("check_churned")}, {need("check_stayed")}, а ожидалось {_a}, {_b}. Берите только гостей с visits_90d > 0.'
```

### hint
Глава 3: посчитайте `g["avg_check"].isna().sum()` **до** `fillna(0)`.

### hint
Гости с визитами — `g[g["visits_90d"] > 0]`; дальше `groupby("churned")["avg_check"].mean()` или две маски.

### solution
```python
filled = g["avg_check"].isna().sum()
g["avg_check"] = g["avg_check"].fillna(0)
v = g[g["visits_90d"] > 0]
check_churned = round(v.loc[v["churned"] == 1, "avg_check"].mean())
check_stayed = round(v.loc[v["churned"] == 0, "avg_check"].mean())
print(filled, check_churned, check_stayed)
```

### explain
Ноль здесь — не «неизвестно», а настоящий факт: денег за 90 дней гость не оставил. Для дерева и леса 0 — просто «меньше всех»; линейной модели он тоже скажет «визитов не было», и вместе с `visits_90d = 0` это согласованный сигнал, а не выдуманное число. Среди гостей с визитами средний чек у уходящих и остающихся почти одинаковый (около 340 ₽): сам по себе он ничего не предсказывает. Важнее, как давно и как часто гость приходит.

## task: leak | Шаг 3. Подозрительно хорошо | plus

`g` с заполненным `avg_check` уже готова. Проверим числовые признаки на утечку (урок «Категориальные признаки и утечки»). Возьмите столбцы

`tenure_months`, `app`, `visits_90d`, `days_since_last`, `avg_check`, `delivery_share`, `promo_used`, `complaints`, `card_blocked`

и разделите их и `churned`: `train_test_split(..., test_size=0.25, random_state=42, stratify=g["churned"])`. Обучите `DecisionTreeClassifier(max_depth=3, random_state=0)` и сохраните:

- `acc_all` — долю правильных на тесте (3 знака);
- `top_feature` — признак с наибольшей важностью (`feature_importances_`);
- `acc_clean` — то же дерево без этого признака (3 знака);
- `blocked_churn` — долю ушедших среди гостей с `card_blocked == 1` (3 знака).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
cols = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
        "delivery_share", "promo_used", "complaints", "card_blocked"]
```

### check
```python
from sklearn.tree import DecisionTreeClassifier as _T
_g = _ref()[0]
_c = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints', 'card_blocked']
_a, _b, _ya, _yb = _tts0(_g[_c], _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_m = _T(max_depth=3, random_state=0).fit(_a, _ya)
assert close(need('acc_all'), round(_m.score(_b, _yb), 3)), f'acc_all = {need("acc_all")}, а ожидалось {round(_m.score(_b, _yb), 3)}. Проверьте разбиение: test_size=0.25, random_state=42, stratify.'
_top = _c[int(_np0.argmax(_m.feature_importances_))]
assert need('top_feature') == _top, f'top_feature = {need("top_feature")!r}: найдите признак с наибольшим значением в feature_importances_.'
_cc = [c for c in _c if c != _top]
_w = round(_T(max_depth=3, random_state=0).fit(_a[_cc], _ya).score(_b[_cc], _yb), 3)
assert close(need('acc_clean'), _w), f'acc_clean = {need("acc_clean")}, а ожидалось {_w}: то же разбиение, тот же список без одного признака.'
assert close(need('blocked_churn'), round(_g.loc[_g['card_blocked'] == 1, 'churned'].mean(), 3)), f'blocked_churn = {need("blocked_churn")}. Доля churned == 1 среди всех гостей g с card_blocked == 1.'
```

### hint
Урок «Решающее дерево изнутри»: `pd.Series(model.feature_importances_, index=cols).idxmax()` — название самого важного признака.

### hint
Список без признака: `[c for c in cols if c != top_feature]`. Разбиение то же — используйте уже готовые части и выберите в них нужные столбцы.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
cols = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
        "delivery_share", "promo_used", "complaints", "card_blocked"]
Xa, Xb, ya, yb = train_test_split(g[cols], g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(Xa, ya)
acc_all = round(tree.score(Xb, yb), 3)
top_feature = pd.Series(tree.feature_importances_, index=cols).idxmax()
clean = [c for c in cols if c != top_feature]
acc_clean = round(DecisionTreeClassifier(max_depth=3, random_state=0).fit(Xa[clean], ya).score(Xb[clean], yb), 3)
blocked_churn = round(g.loc[g["card_blocked"] == 1, "churned"].mean(), 3)
print(acc_all, top_feature, acc_clean, blocked_churn)
```

### explain
98 % правильных от дерева из трёх вопросов — слишком хорошо, чтобы быть правдой, и почти вся важность у одного признака. Спрашиваем у владельцев данных, что такое `card_blocked`: карту блокируют автоматически после 60 дней без визитов — то есть **по итогам того же периода**, за который мы считаем отток. На 1 октября этого признака ещё нет: он почти совпадает с ответом. Это утечка, и из признаков её убираем. Честное качество — около 87 %.

## task: prepare | Шаг 4. Признаки и разбиение | base

`g` с заполненным `avg_check` уже готова. Соберите:

- `y` — столбец `churned`;
- `X` — `pd.get_dummies(..., dtype=int)` от всех столбцов `g`, кроме `guest_id`, `churned` и `card_blocked`;
- `X_train`, `X_test`, `y_train`, `y_test` — `train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)`.

Сохраните `train_rate` и `test_rate` — доли ушедших в обучающей и тестовой частях (3 знака).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
```

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
```

### check
```python
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_x = need('X', _pd0.DataFrame)
assert 'card_blocked' not in _x.columns, 'card_blocked в X — это утечка из шага 3, уберите его.'
assert 'guest_id' not in _x.columns and 'churned' not in _x.columns, 'guest_id и churned не признаки: номер гостя ничего не говорит о нём, а churned — ответ.'
assert list(_x.columns) == list(_X.columns), f'Столбцы X: {list(_x.columns)}, а ожидались {list(_X.columns)}. get_dummies от g без трёх столбцов, dtype=int.'
assert (need('y') == _y).all(), 'y — столбец churned.'
assert list(need('X_test').index) == list(_Xte.index), 'X_test — не те строки: test_size=0.25, random_state=42, stratify=y.'
assert list(need('X_train').index) == list(_Xtr.index) and list(need('y_test').index) == list(_yte.index), 'X_train / y_test не совпадают с ожидаемым разбиением.'
assert close(need('train_rate'), round(_ytr.mean(), 3)) and close(need('test_rate'), round(_yte.mean(), 3)), f'train_rate, test_rate = {need("train_rate")}, {need("test_rate")}, а ожидалось {round(_ytr.mean(), 3)}, {round(_yte.mean(), 3)}.'
```

### hint
Урок «Категориальные признаки и утечки»: `pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)`.

### hint
Урок «Обучающая и тестовая выборки»: `stratify=y` сохраняет долю ушедших одинаковой в обеих частях.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
train_rate, test_rate = round(y_train.mean(), 3), round(y_test.mean(), 3)
print(X.shape, train_rate, test_rate)
```

### explain
Тест (600 гостей) отложен и до шага 8 не используется. Всё, что дальше выбираем — модель, глубину, — выбираем кросс-валидацией на `X_train`.

## task: baseline | Шаг 5. Базовая модель и правило | base

Оцените на фолдах `kf` по **обучающей** части (`X_train`, `y_train`) две модели без обучения:

- «никто не уйдёт» — `base_cv`;
- правило заказчика «уйдёт, если не был больше 45 дней» (`days_since_last > 45`) — `rule_cv`.

Обе — средняя по фолдам доля правильных ответов (3 знака).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
import numpy as np
```

### check
```python
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_r = _Xtr['days_since_last'] > 45
_b = round(_np0.mean([(_ytr.iloc[te] == 0).mean() for tr, te in _k.split(_Xtr)]), 3)
_q = round(_np0.mean([(_r.iloc[te] == _ytr.iloc[te]).mean() for tr, te in _k.split(_Xtr)]), 3)
assert close(need('base_cv'), _b, 0.0011), f'base_cv = {need("base_cv")}, а ожидалось {_b}. Фолды — kf.split(X_train).'
assert close(need('rule_cv'), _q, 0.0011), f'rule_cv = {need("rule_cv")}, а ожидалось {_q}. Правило — X_train["days_since_last"] > 45, сравнивайте с y_train на тех же номерах.'
```

### hint
Урок «Честное сравнение моделей»: цикл `for tr, te in kf.split(X_train):` и `.iloc[te]`.

### hint
`y_train` — числа 1/0, а правило — `True/False`; сравнение `rule.iloc[te] == y_train.iloc[te]` работает, потому что `True == 1`.

### solution
```python
import numpy as np
rule = X_train["days_since_last"] > 45
base_cv = round(np.mean([(y_train.iloc[te] == 0).mean() for tr, te in kf.split(X_train)]), 3)
rule_cv = round(np.mean([(rule.iloc[te] == y_train.iloc[te]).mean() for tr, te in kf.split(X_train)]), 3)
print(base_cv, rule_cv)
```

### explain
Правило лучше базовой модели примерно на 4–5 п.п. Это и есть планка, которую должна взять модель: если она не обгонит правило, бизнесу проще продолжать считать дни.

## task: depth | Шаг 6. Глубина дерева | base

Подберите глубину дерева кросс-валидацией на обучающей части: для глубин от 1 до 10 посчитайте среднюю долю правильных `DecisionTreeClassifier(max_depth=..., random_state=0)` по фолдам `kf`. Сохраните словарь `cv_depth` (глубина → среднее), `best_depth` (при равенстве — меньшая) и `best_cv` — среднее для неё (3 знака).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
cv_depth = {}
```

### check
```python
from sklearn.tree import DecisionTreeClassifier as _T
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_w = {d: _cvs0(_T(max_depth=d, random_state=0), _Xtr, _ytr, cv=_k).mean() for d in range(1, 11)}
_c = dict(need('cv_depth'))
assert sorted(_c) == list(range(1, 11)), f'Ключи cv_depth: {sorted(_c)}, а нужны глубины от 1 до 10.'
for d in range(1, 11):
    assert close(_c[d], _w[d], 0.0006), f'Для глубины {d} в cv_depth {_c[d]}, а ожидалось около {_w[d]:.3f}. Кросс-валидация на X_train, y_train с cv=kf.'
_b = max(_w, key=_w.get)
assert need('best_depth') == _b, f'best_depth = {need("best_depth")}, а лучшая глубина по cv_depth — другая.'
assert close(need('best_cv'), round(_w[_b], 3)), f'best_cv = {need("best_cv")}, а ожидалось {round(_w[_b], 3)}.'
```

### hint
Урок «Честное сравнение моделей»: `cross_val_score(DecisionTreeClassifier(max_depth=depth, random_state=0), X_train, y_train, cv=kf).mean()`.

### hint
`max(cv_depth, key=cv_depth.get)` при равных значениях возвращает первый ключ, то есть меньшую глубину, — именно так требует условие. Округлять значения в словаре не нужно: округлите только `best_cv`.

### solution
```python
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
cv_depth = {}
for depth in range(1, 11):
    model = DecisionTreeClassifier(max_depth=depth, random_state=0)
    cv_depth[depth] = cross_val_score(model, X_train, y_train, cv=kf).mean()
best_depth = max(cv_depth, key=cv_depth.get)
best_cv = round(cv_depth[best_depth], 3)
print(best_depth, best_cv)
```

### explain
Лучшее дерево — неглубокое (4 вопроса), и оно уже обгоняет правило «45 дней» примерно на 3 п.п. Дальше качество падает: глубокое дерево запоминает обучающих гостей. Дерево без ограничения глубины на кросс-валидации даёт около 82 % — не лучше правила.

## task: models | Шаг 7. Лес и логистическая регрессия | plus

Курс сохранил лучшую глубину из шага 6 в `best_depth`. Сравните на фолдах `kf` по обучающей части три модели:

- `"дерево"` — `DecisionTreeClassifier(max_depth=best_depth, random_state=0)`;
- `"лес"` — `RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0)`;
- `"логрегрессия"` — `LogisticRegression(max_iter=2000)`.

Сохраните таблицу `table` (индекс — названия, столбцы `mean` и `std`, 3 знака, по убыванию `mean`) и `winner` — название лучшей модели.

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
_cv0 = {k: cross_val_score(DecisionTreeClassifier(max_depth=k, random_state=0), X_train, y_train, cv=kf).mean() for k in range(1, 11)}
best_depth = max(_cv0, key=_cv0.get)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
```

### check
```python
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.linear_model import LogisticRegression as _LR
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_dd = {d: _cvs0(_T(max_depth=d, random_state=0), _Xtr, _ytr, cv=_k).mean() for d in range(1, 11)}
_bd = max(_dd, key=_dd.get)
_res = {'дерево': _cvs0(_T(max_depth=_bd, random_state=0), _Xtr, _ytr, cv=_k),
        'лес': _cvs0(_RF(n_estimators=100, min_samples_leaf=3, random_state=0), _Xtr, _ytr, cv=_k),
        'логрегрессия': _cvs0(_LR(max_iter=2000), _Xtr, _ytr, cv=_k)}
_w = {n: (round(s.mean(), 3), round(s.std(), 3)) for n, s in _res.items()}
_t = need('table', _pd0.DataFrame)
assert set(_t.index) == set(_w), f'В индексе table: {list(_t.index)}, а нужны {list(_w)}.'
for n, (m, s) in _w.items():
    assert close(_t.loc[n, 'mean'], m, 0.0011) and close(_t.loc[n, 'std'], s, 0.0011), f'{n}: mean, std = {_t.loc[n, "mean"]}, {_t.loc[n, "std"]}, а ожидалось {m}, {s}. Кросс-валидация на X_train с cv=kf.'
assert list(_t['mean']) == sorted(_t['mean'], reverse=True), 'Строки table должны идти по убыванию mean.'
assert need('winner') == max(_w, key=lambda n: _w[n][0]), f'winner = {need("winner")!r}, а лучшая модель в таблице — другая.'
```

### hint
Урок «Честное сравнение моделей», раздел «Сравнение моделей»: словарь «название → оценки», затем `pd.DataFrame({...}, index=["mean", "std"]).T.round(3)`.

### hint
Лучшая строка после сортировки — `table.index[0]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
models = {
    "дерево": DecisionTreeClassifier(max_depth=best_depth, random_state=0),
    "лес": RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0),
    "логрегрессия": LogisticRegression(max_iter=2000),
}
results = {name: cross_val_score(m, X_train, y_train, cv=kf) for name, m in models.items()}
table = pd.DataFrame({name: [np.mean(s), np.std(s)] for name, s in results.items()},
                     index=["mean", "std"]).T.round(3)
table = table.sort_values("mean", ascending=False)
winner = table.index[0]
table
```

### explain
Лес впереди: около 86–87 % против 82 % у правила. Здесь, в отличие от опозданий, у оттока много причин, и они переплетаются: давность визита, частота, жалобы, стаж, приложение. Одним порогом их не охватить — и лес выигрывает у правила уже не 1–2, а около 4 п.п. А вот лес и дерево различаются меньше, чем разброс между фолдами (стандартное отклонение 2–3 п.п.): уверенно назвать лес лучше дерева нельзя. Лес берём за устойчивость — он меньше зависит от случайностей разбиения, — а не за разницу в доли пункта.

## task: final | Шаг 8. Финальная проверка на тесте | base

Победитель шага 7 — лес. Обучите `RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0)` на всей обучающей части и сохраните в `model`. Теперь — один раз — посчитайте на тесте (3 знака):

- `test_acc` — долю правильных ответов леса;
- `base_test` — модели «никто не уйдёт»;
- `rule_test` — правила `days_since_last > 45`.

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.ensemble import RandomForestClassifier
```

### check
```python
from sklearn.ensemble import RandomForestClassifier as _RF
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_m = need('model')
assert isinstance(_m, _RF) and _m.n_estimators == 100 and _m.min_samples_leaf == 3, 'model — RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0).'
assert hasattr(_m, 'n_features_in_') and _m.n_features_in_ == _Xtr.shape[1], 'model нужно обучить: .fit(X_train, y_train).'
_w = round(_RF(n_estimators=100, min_samples_leaf=3, random_state=0).fit(_Xtr, _ytr).score(_Xte, _yte), 3)
assert close(need('test_acc'), _w), f'test_acc = {need("test_acc")}, а ожидалось {_w}. Учим на X_train, проверяем на X_test.'
assert close(need('base_test'), round((_yte == 0).mean(), 3)), f'base_test = {need("base_test")}. «Никто не уйдёт» права там, где в y_test стоит 0.'
assert close(need('rule_test'), round(((_Xte['days_since_last'] > 45) == _yte).mean(), 3)), f'rule_test = {need("rule_test")}: правило на X_test, сравнение с y_test.'
```

### hint
`model.score(X_test, y_test)`; для правила — `(X_test["days_since_last"] > 45) == y_test`.

### hint
«Никто не уйдёт» — постоянный ответ 0, поэтому он прав там, где `y_test == 0`. Правило даёт маску True/False, её сравнение с `y_test` — тоже маска, и `.mean()` превращает её в долю. Тест считается один раз, в самом конце: после этого параметры модели больше не меняют.

### solution
```python
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X_train, y_train)
test_acc = round(model.score(X_test, y_test), 3)
base_test = round((y_test == 0).mean(), 3)
rule_test = round(((X_test["days_since_last"] > 45) == y_test).mean(), 3)
print(test_acc, base_test, rule_test)
```

### explain
На тесте лес прав в 90 % случаев, правило — в 85 %, «никто не уйдёт» — в 78 %. Тест оказался чуть «проще» кросс-валидации (так бывает, урок «Честное сравнение моделей»), но порядок моделей тот же. Эти цифры — для отчёта: при выборе модели тест не участвовал.

## task: top | Шаг 9. Список для акции | plus

Курс обучил лес из шага 8 — он в `model`. Бюджета хватает на 10 % гостей. Отберите их по риску на тестовой части:

- `risk` — Series с вероятностью ухода (`predict_proba(X_test)[:, 1]`) и индексом `X_test`;
- `top` — 10 % тестовых гостей с наибольшим риском: `risk.nlargest(60)`;
- `top_ids` — список их `guest_id` (из `g`) в том же порядке;
- `top_rate` — доля ушедших среди них (3 знака);
- `lift` — во сколько раз `top_rate` больше доли ушедших во всём тесте (1 знак);
- `already_gone` — доля гостей в `top`, которые не были больше 45 дней, то есть уже известны по правилу (3 знака).

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X_train, y_train)
```

### starter
```python
import pandas as pd
```

### check
```python
from sklearn.ensemble import RandomForestClassifier as _RF
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_m = _RF(n_estimators=100, min_samples_leaf=3, random_state=0).fit(_Xtr, _ytr)
_r = _pd0.Series(_m.predict_proba(_Xte)[:, 1], index=_Xte.index)
_t = _r.nlargest(60)
_x = need('risk', _pd0.Series)
assert len(_x) == len(_Xte) and list(_x.index) == list(_Xte.index), 'risk — Series длиной с X_test и с его индексом: pd.Series(..., index=X_test.index).'
assert close(float((_x - _r).abs().max()), 0, 1e-9), 'risk — вероятность класса 1 (уйдёт): второй столбец predict_proba.'
assert list(need('top_ids')) == list(_g.loc[_t.index, 'guest_id']), 'top_ids — guest_id 60 гостей с наибольшим риском, в порядке убывания риска: g.loc[top.index, "guest_id"].'
_tr = _yte.loc[_t.index].mean()
assert close(need('top_rate'), round(_tr, 3)), f'top_rate = {need("top_rate")}, а ожидалось {round(_tr, 3)}.'
assert close(need('lift'), round(_tr / _yte.mean(), 1)), f'lift = {need("lift")}, а ожидалось {round(_tr / _yte.mean(), 1)}.'
assert close(need('already_gone'), round((_Xte.loc[_t.index, 'days_since_last'] > 45).mean(), 3)), f'already_gone = {need("already_gone")}. Доля гостей из top с days_since_last > 45 (смотрите X_test по индексу top).'
```

### hint
Урок «Логистическая регрессия и вероятности»: `model.predict_proba(X_test)[:, 1]` — вероятность класса 1. Оберните в `pd.Series(..., index=X_test.index)`.

### hint
`y_test.loc[top.index].mean()` — доля ушедших в списке; `X_test.loc[top.index, "days_since_last"]` — их давность визита.

### solution
```python
import pandas as pd
risk = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)
top = risk.nlargest(60)
top_ids = list(g.loc[top.index, "guest_id"])
top_rate = round(y_test.loc[top.index].mean(), 3)
lift = round(top_rate / y_test.mean(), 1)
already_gone = round((X_test.loc[top.index, "days_since_last"] > 45).mean(), 3)
print(top_ids[:5], top_rate, lift, already_gone)
```

### explain
Из 60 самых рискованных гостей уходят больше 90 % — в 4 раза чаще, чем в среднем. Список точный. Но две трети в нём — гости, которые не были больше 45 дней, то есть те, кого правило уже нашло и кого, по словам заказчика, возвращать поздно. Самое ценное в модели может быть не в том, что она повторяет правило, а в том, что она видит среди тех, кто ещё ходит, — это следующий шаг. И ещё одна оговорка: список здесь построен по тестовым 600 гостям, чтобы знать, чего от него ждать. В работе лес обучат на всех 2 400 гостях и отранжируют всех — тогда «10 % самых рискованных» — это 240 гостей для акции.

Итог для отдела лояльности:

- данные без утечки: признак `card_blocked` появляется вместе с ответом, его в модели нет;
- лес на тесте прав в 90 % случаев против 85 % у правила «45 дней» и 78 % у «никто не уйдёт»;
- список 10 % самых рискованных гостей — больше 90 % ушедших, в 4 раза выше среднего;
- ограничения: это срез одного периода, качество нужно перепроверить на следующем; модель ранжирует риск, но не знает, вернёт ли гостя бонус, — это покажет A/B-тест акции (глава 5).

## task: quiet | Шаг 10. Тихий риск | star

Акция нужнее тем, кто **ещё ходит** — был не позже 45 дней назад: правило про них молчит. Возьмите таких гостей тестовой части (`days_since_last <= 45`) и сохраните:

- `quiet_rate` — долю ушедших среди них (3 знака);
- `k` — 10 % от их числа, `int(len(...) * 0.1)`;
- `model_rate` — долю ушедших среди `k` гостей с наибольшим риском по модели (`nlargest(k)`, 3 знака);
- `days_rate` — то же, если отобрать `k` гостей с наибольшим `days_since_last` (тоже `nlargest(k)`, 3 знака) — «правило, доведённое до предела».

Лес из шага 8 — в `model`.

### setup
```python
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
def _ref():
    _g = _pd0.read_csv('guests_churn.csv')
    _g['avg_check'] = _g['avg_check'].fillna(0)
    _y = _g['churned']
    _X = _pd0.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int)
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _g, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
g["avg_check"] = g["avg_check"].fillna(0)
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X_train, y_train)
```

### starter
```python
import pandas as pd
```

### check
```python
from sklearn.ensemble import RandomForestClassifier as _RF
_g, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_m = _RF(n_estimators=100, min_samples_leaf=3, random_state=0).fit(_Xtr, _ytr)
_q = _Xte['days_since_last'] <= 45
_xq, _yq = _Xte[_q], _yte[_q]
assert close(need('quiet_rate'), round(_yq.mean(), 3)), f'quiet_rate = {need("quiet_rate")}, а ожидалось {round(_yq.mean(), 3)}. Гости теста с days_since_last <= 45.'
_kk = int(len(_xq) * 0.1)
assert need('k') == _kk, f'k = {need("k")}, а ожидалось {_kk}.'
_r = _pd0.Series(_m.predict_proba(_xq)[:, 1], index=_xq.index).nlargest(_kk)
assert close(need('model_rate'), round(_yq.loc[_r.index].mean(), 3)), f'model_rate = {need("model_rate")}, а ожидалось {round(_yq.loc[_r.index].mean(), 3)}. Риск считайте только для «тихих» гостей и берите nlargest(k).'
_dd = _xq['days_since_last'].nlargest(_kk)
assert close(need('days_rate'), round(_yq.loc[_dd.index].mean(), 3)), f'days_rate = {need("days_rate")}, а ожидалось {round(_yq.loc[_dd.index].mean(), 3)}. nlargest(k) по days_since_last среди тех же гостей.'
```

### hint
Маска `quiet = X_test["days_since_last"] <= 45`; дальше `X_test[quiet]`, `y_test[quiet]`.

### hint
Риск — `pd.Series(model.predict_proba(Xq)[:, 1], index=Xq.index).nlargest(k)`; доля ушедших — `yq.loc[....index].mean()`.

### solution
```python
import pandas as pd
quiet = X_test["days_since_last"] <= 45
Xq, yq = X_test[quiet], y_test[quiet]
quiet_rate = round(yq.mean(), 3)
k = int(len(Xq) * 0.1)
by_model = pd.Series(model.predict_proba(Xq)[:, 1], index=Xq.index).nlargest(k)
model_rate = round(yq.loc[by_model.index].mean(), 3)
by_days = Xq["days_since_last"].nlargest(k)
days_rate = round(yq.loc[by_days.index].mean(), 3)
print(quiet_rate, k, model_rate, days_rate)
```

### explain
Среди гостей, которые ещё ходят, уходит около 15 %, и правило «45 дней» никого из них не отмечает. Если просто взять тех, кто дольше всех не был, в списке окажется около трети будущих ушедших. Модель среди тех же гостей находит список, где уходят три из четырёх, — она складывает сразу несколько сигналов: жалобы, редкие визиты, небольшой стаж, нет приложения. Это и есть место, где машинное обучение выигрывает у правила аналитика: причин много, и ни одна по отдельности не решает.

Рекомендация: бонусы — в первую очередь «тихим» гостям из верха списка модели, пока они ещё приходят; тем, кто уже пропал на 45+ дней, нужна другая, более дорогая кампания. Эффект акции проверить A/B-тестом. Глава 6 пройдена: в главе 7 научимся оценивать модели не только долей правильных ответов, а подбор настроек поручим `GridSearchCV`.
