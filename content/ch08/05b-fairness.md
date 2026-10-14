---
title: "Этика данных и справедливость модели"
lead: "Модель, которая хорошо работает в среднем, может систематически недодавать одной группе гостей — даже если возраста или пола среди признаков нет. Разбираемся, какие данные брать нельзя, как проверить справедливость по группам на честных прогнозах и как найти признаки-заместители."
files: [guests_churn.csv, guests_age.csv]
recap:
  - "Этика данных: чувствительные признаки (здоровье, национальность, взгляды) в модель не берут; пол и возраст — только осознанным решением с юристом. Убрать признак мало: признаки-заместители (приложение → возраст) его восстанавливают."
  - "Справедливость проверяют по группам: доля отобранных, полнота, точность. Одинаковая доля отобранных не значит, что уходящие гости группы получают бонус одинаково часто; для групп берут прогнозы вне выборки (`cross_val_predict`)."
---

Модель — лес оттока из прошлых уроков (те же признаки гостей, что в уроке «Объяснить модель бизнесу»). Логистическую регрессию в этом уроке используем только один раз — чтобы проверить признаки-заместители.

## Этика данных: кому модель недодаёт

Модель оттока решает, кому достанется бонус, — то есть распределяет деньги между гостями. Поэтому кроме вопросов «почему у гостя такой риск» директору нужно отвечать и на два неудобных:

1. **Какие данные модели брать нельзя**, даже если они повышают качество?
2. **Одинаково ли модель работает для разных групп гостей** — или кому-то бонусы систематически не достаются?

### Что не берут в признаки

- **Чувствительные данные:** здоровье, национальность, религиозные и политические взгляды. В законе о персональных данных (152-ФЗ) это специальные категории, обрабатывать их можно только в особых случаях; в маркетинговой модели им не место.
- **Пол и возраст** — обычные персональные данные, но разные условия (бонус, цена, скидка) в зависимости от них легко становятся дискриминацией и скандалом. Решение «использовать или нет» принимают вместе с юристом и записывают, а не «потому что AUC выше».
- **Данные, собранные для другой цели или без согласия:** записи камер, геолокация телефона, переписка с поддержкой. То, что технически доступно, не значит, что гость разрешил так этим пользоваться.
- **Признаки-заместители (прокси).** Признак, который сам по себе нейтрален, но «выдаёт» чувствительный: район проживания — доход, имя — пол, пользование приложением — возраст. Убрать из модели возраст мало, если его почти точно восстанавливают другие признаки.

::: tip Аналогия
Охраннику запретили не пускать людей по возрасту, но разрешили — по тому, есть ли у человека смартфон. Формально правило соблюдено, а на деле пожилых снова не пускают. Прокси работает так же: модель не видит возраст, но видит то, что с ним тесно связано. Разница в том, что охранник может делать это нарочно, а модель — нет, она просто находит связи в данных. Поэтому проверять приходится нам.
:::

### Справедливость: смотрим по группам

Проверка простая — те же метрики, что в главе 7, но **отдельно для каждой группы**:

- **доля получивших бонус** — сколько гостей группы модель отбирает;
- **полнота** — какую долю **уходящих** гостей группы модель ловит (то есть сколько из тех, кому бонус нужен, его получат);
- **точность** — какая доля отобранных действительно уходила.

Игрушечный пример. Уходящих гостей 10: шесть младше 50 лет, четыре старше. Модель отправила бонус пятерым из первых шести и двоим из последних четырёх. Полнота: 5/6 ≈ **0.83** против 2/4 = **0.50**. Даже если доля получивших бонус по группам одинаковая, уходящий гость старшей группы получает бонус заметно реже.

::: figure fair-recall-toy
Полноту считают только среди уходящих гостей группы: у младших бонус получили пятеро из шести, у старших — двое из четырёх.
:::

```python
import numpy as np
churned_young = np.array([1, 1, 1, 1, 1, 1])    # шестеро уходящих младше 50
sent_young = np.array([1, 1, 1, 1, 1, 0])       # бонус получили пятеро
churned_old = np.array([1, 1, 1, 1])
sent_old = np.array([1, 1, 0, 0])
print(round(sent_young.mean(), 2), round(sent_old.mean(), 2))   # полнота по группам
```

{{practice: fair-toy}}

### На гостях «Зерна»

В анкете программы лояльности гости указывают возраст; группа лежит в `guests_age.csv`. В модель она **не входит** — используем её только для проверки. В тесте из урока всего 600 гостей и 35 уходящих старше 50 — полнота по такой группе прыгает на десятки процентов. Поэтому возьмём прогнозы **вне выборки** для всех 2 400 гостей. Это делает `cross_val_predict` — родственник `cross_val_score` из главы 6: он так же обучает лес пять раз на четырёх пятых данных, но возвращает не пять оценок качества, а прогноз для каждого гостя — от той модели, которая этого гостя не видела.

::: figure oof-predict
`cross_val_predict` с пятью фолдами: каждая модель учится на 1 920 гостях и делает прогноз для оставшихся 480. Из пяти кусков собирается столбец прогнозов вне выборки для всех 2 400.
:::

```python
import pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)
p = cross_val_predict(forest, X, y, cv=cv, method="predict_proba")[:, 1]
g["send"] = p > 1 / 3                           # бонус по порогу безубыточности

def fair(t):
    return pd.Series({"guests": len(t), "churners": t["churned"].sum(),
                      "selected": t["send"].mean(),                      # доля получивших бонус
                      "recall": t.loc[t["churned"] == 1, "send"].mean(), # доля пойманных уходящих
                      "precision": t.loc[t["send"], "churned"].mean()})  # доля уходящих среди получивших

g.groupby("age_group")[["churned", "send"]].apply(fair).round(3)
```

**Что здесь происходит:**

- `merge(..., validate="one_to_one")` — к каждому гостю ровно одна строка возраста; если в файле дубль, будет ошибка, а не тихое размножение строк.
- `X` собирается **без** `age_group`: проверяем модель, которая возраста не видит.
- `cross_val_predict(..., method="predict_proba")` — для каждого из 2 400 гостей прогноз модели, обученной на остальных четырёх пятых.
- `fair(t)` — три метрики по куску таблицы одной группы. `t.loc[t["churned"] == 1, "send"].mean()` — среди уходящих доля получивших бонус, это и есть полнота.

**Что получилось.** Доля получивших бонус почти одинаковая — 24–28 % во всех группах, точность тоже (65–69 %). По этим числам модель выглядит справедливой. Но полнота у гостей 50+ — **0.64** против 0.84 и 0.80 у остальных: модель пропускает больше трети уходящих старших гостей. Из 120 пропущенных уходящих 48 — старшие, хотя их всего 18 % в базе.

Почему так? Посмотрим на уходящих гостей разных групп: у старших медианная пауза перед уходом 22 дня (у 30–49 лет — 32), а жалобу оставили только 10 % из них (у остальных — 29–37 %). Они уходят **тихо** — без тех сигналов, на которые опирается модель.

Что с этим делать — решение не только аналитика:

- искать признаки «тихого ухода», которые есть у всех (например, падение частоты визитов по сравнению с прошлым кварталом);
- проверить, не нужен ли для этой группы другой канал удержания — бонус в приложении не дойдёт до тех, у кого его нет;
- если компания решает выравнивать полноту отдельным порогом для группы, это осознанное решение с юристом, записанное в документации модели.

{{practice: missed, quiet-churn}}

### Признаки-заместители

Модель не видит возраст. Но можно ли его восстановить по её признакам? Обучим логистическую регрессию предсказывать «50+» по тем же признакам, что у модели оттока:

```python
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
old = (g["age_group"] == "50+").astype(int)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
auc = cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)), X, old, cv=cv, scoring="roc_auc")
print("ROC-AUC восстановления «50+»:", round(auc.mean(), 3))
print("доля с приложением: 50+", round(g.loc[old == 1, "app"].mean(), 3), "| остальные", round(g.loc[old == 0, "app"].mean(), 3))
```

ROC-AUC 0.71: возраст восстанавливается заметно лучше, чем наугад (0.5), хотя и не точно. Главный заместитель — приложение: им пользуются 18 % старших гостей и 50 % остальных. Вывод не «выбросить приложение из модели» — это важный признак оттока, — а «проверять результат по группам», потому что убрать чувствительный признак из `X` не значит сделать модель к нему слепой.

::: quiz
Доля получивших бонус у гостей 50+ и у остальных почти одинаковая — 28 % и 24–27 %. Можно ли сказать, что модель к старшим гостям справедлива?

- [x] Нет: важно ещё, какую долю уходящих она ловит в каждой группе; у старших гостей полнота 0.64 против 0.80–0.84
  > Разные метрики справедливости отвечают на разные вопросы. Одинаковая доля отобранных не гарантирует, что нуждающимся в бонусе он достаётся одинаково часто.
- [ ] Да: одинаковая доля отобранных — главный критерий справедливости
  > Это один из критериев, и здесь он выполнен. Но среди старших гостей больше уходящих, и треть из них бонуса не получает.
- [ ] Нет, потому что возраст не входит в модель
  > Как раз наоборот: возраста в модели нет, а перекос есть — через признаки-заместители и разное поведение групп.
- [ ] Вопрос бессмысленный: модель не знает возраста, значит, не может быть к нему несправедлива
  > Модель может не видеть возраст и всё равно работать по-разному для групп. Это и проверяют таблицей по группам.
:::

::: warn Типичные ошибки
- **«Убрали пол и возраст — значит, модель честная».** Признаки-заместители восстанавливают их; проверяют результат по группам, а не только список признаков.
- **Одна метрика справедливости.** Одинаковая доля отобранных и одинаковая полнота — разные требования, и обычно оба одновременно не выполняются. Какое важнее, решает бизнес; аналитик показывает оба.
- **Группы на тесте из 600 строк.** 35 уходящих в группе — полнота «гуляет» на ±15 п. п. Для проверки по группам берите прогнозы вне выборки по всем данным (`cross_val_predict`) и пишите число объектов.
- **Чувствительный признак в модель «для точности».** Даже если ROC-AUC растёт, решение принимают с юристом и бизнесом и документируют. В нашем случае возраст добавляет к ROC-AUC около 0.01 — решение всё равно принимают не по этому числу.
:::

{{practice: fair-recall, proxy-check}}

## Практика

## task: fair-recall | Справедливость при другом пороге | base

Маркетинг предлагает снизить порог до 0.25, «чтобы старшие гости тоже получали бонусы». Проверьте. По прогнозам вне выборки `p` (уже посчитаны в заготовке) отправьте бонус при `p > 0.25` и соберите таблицу `fair25` по `age_group` со столбцами `selected` (доля получивших бонус) и `recall` (доля получивших среди уходящих), 3 знака. Сохраните в `gap25` разницу между наибольшей и наименьшей полнотой групп (3 знака), в `extra_bonuses` — на сколько бонусов больше, чем при пороге 1/3, а в `fixes_gap` — ответ маркетингу: `True`, если при пороге 0.25 разрыв полноты стал меньше 0.1 (то есть перекос почти исчез).

### starter
```python
import pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)
p = cross_val_predict(forest, X, y, cv=cv, method="predict_proba")[:, 1]

```

### check
```python
import pandas as _pd
G = need('g', _pd.DataFrame)
P = need('p')
s = _pd.Series(P > 0.25, index=G.index)
sel = s.groupby(G['age_group']).mean().round(3)
rec = s[G['churned'] == 1].groupby(G.loc[G['churned'] == 1, 'age_group']).mean().round(3)
t = need('fair25', _pd.DataFrame)
assert {'selected', 'recall'} <= set(t.columns), f'Столбцы fair25: {list(t.columns)}, нужны selected и recall.'
assert sorted(t.index) == sorted(sel.index), f'Индекс fair25: {list(t.index)} — нужны возрастные группы.'
for a in sel.index:
    assert close(t.loc[a, 'selected'], sel[a]), f'{a}: selected = {t.loc[a, "selected"]}, ожидалось {sel[a]}. Доля получивших среди всех гостей группы.'
    assert close(t.loc[a, 'recall'], rec[a]), f'{a}: recall = {t.loc[a, "recall"]}, ожидалось {rec[a]}. Считайте только среди уходящих (churned == 1).'
assert close(need('gap25'), round(rec.max() - rec.min(), 3), 0.0015), f'gap25 = {need("gap25")}: наибольшая полнота минус наименьшая.'
assert need('extra_bonuses') == int((P > 0.25).sum() - (P > 1 / 3).sum()), f'extra_bonuses = {need("extra_bonuses")}: сравните число бонусов при 0.25 и при 1/3.'
assert need('fixes_gap') == bool(rec.max() - rec.min() < 0.1), f'fixes_gap = {need("fixes_gap")}. Сравните gap25 с 0.1.'
```

### hint
Добавьте в `g` столбец `send = p > 0.25` и примените функцию `fair` из теории (или посчитайте два столбца отдельно через `groupby`).

### hint
Полнота — среднее `send` только по уходящим: `g[g["churned"] == 1].groupby("age_group")["send"].mean()`. Разница — `recall.max() - recall.min()`.

### hint
```python
g["send"] = p > 0.25
fair25 = pd.DataFrame({
    "selected": g.groupby("age_group")["send"].mean(),
    "recall": g[g["churned"] == 1].groupby("age_group")["send"].mean(),
}).round(3)
gap25 = round(fair25["recall"].max() - ..., 3)
extra_bonuses = int((p > 0.25).sum() - ...)
fixes_gap = bool(gap25 < 0.1)
```

### solution
```python
import pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)
p = cross_val_predict(forest, X, y, cv=cv, method="predict_proba")[:, 1]

g["send"] = p > 0.25
fair25 = pd.DataFrame({
    "selected": g.groupby("age_group")["send"].mean(),
    "recall": g[g["churned"] == 1].groupby("age_group")["send"].mean(),
}).round(3)
gap25 = round(fair25["recall"].max() - fair25["recall"].min(), 3)
extra_bonuses = int((p > 0.25).sum() - (p > 1 / 3).sum())
fixes_gap = bool(gap25 < 0.1)
```

### explain
Полнота выросла у всех: у старших с 0.64 до 0.71, у остальных до 0.87–0.89. Разрыв почти не изменился — 0.18 против 0.20 при пороге 1/3, а бонусов стало больше на 127, и только 25 из них достались старшим гостям. Поэтому `fixes_gap = False`: ответ маркетингу — «снижение порога перекос не лечит, а бонусов стало больше». Общий порог — плохой инструмент против перекоса: он двигает все группы сразу. Разрыв закрывают другие шаги — признаки «тихого ухода», другой канал удержания или, по решению бизнеса и юриста, отдельный порог.

## task: proxy-check | Заместители возраста | plus

Найдите, какой признак модели сильнее всего «выдаёт» группу 50+. Для каждого столбца `X` посчитайте ROC-AUC восстановления `old` по одному этому признаку; направление неважно, поэтому берите `max(auc, 1 − auc)`. Сохраните Series `single` (индекс — названия столбцов, 3 знака) и имя лучшего в `top_proxy`. Затем сравните качество модели оттока с возрастом и без: средний ROC-AUC по 5 фолдам (`cross_val_score` с `cv` и `forest` из заготовки) для `X` — в `auc_without`, для `X` плюс one-hot возраста (`pd.get_dummies(g["age_group"], prefix="age", dtype=int)`) — в `auc_with`, оба 3 знака.

### starter
```python
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
old = (g["age_group"] == "50+").astype(int)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)

```

### check
```python
import pandas as _pd
from sklearn.metrics import roc_auc_score as _auc
from sklearn.model_selection import cross_val_score as _cvs, StratifiedKFold as _SKF
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv').merge(_pd.read_csv('guests_age.csv'), on='guest_id')
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked', 'age_group']), dtype=int).fillna({'avg_check': 0})
_o = (_g['age_group'] == '50+').astype(int)
ref = _pd.Series({c: round(max(_auc(_o, _X[c]), 1 - _auc(_o, _X[c])), 3) for c in _X.columns})
s = need('single', _pd.Series)
assert set(s.index) == set(ref.index), 'Индекс single — все столбцы X.'
bad = [c for c in ref.index if not close(s[c], ref[c])]
assert not bad, f'Не совпадают значения для {bad[:3]}. Для каждого столбца: roc_auc_score(old, X[col]), затем max(a, 1 − a).'
assert need('top_proxy') == ref.idxmax(), f'top_proxy = {need("top_proxy")!r} — у какого признака single наибольший?'
cv = _SKF(n_splits=5, shuffle=True, random_state=0)
f = _RF(n_estimators=100, min_samples_leaf=5, random_state=0)
w0 = round(_cvs(f, _X, _g['churned'], cv=cv, scoring='roc_auc').mean(), 3)
w1 = round(_cvs(f, _X.join(_pd.get_dummies(_g['age_group'], prefix='age', dtype=int)), _g['churned'], cv=cv, scoring='roc_auc').mean(), 3)
assert close(need('auc_without'), w0, 0.0015), f'auc_without = {need("auc_without")}, ожидалось {w0}.'
assert close(need('auc_with'), w1, 0.0015), f'auc_with = {need("auc_with")}, ожидалось {w1}. Добавьте к X столбцы get_dummies(g["age_group"], prefix="age", dtype=int).'
```

### hint
Цикл по `X.columns`: для каждого столбца `a = roc_auc_score(old, X[c])`, в словарь кладите `max(a, 1 - a)`; потом `pd.Series(словарь).round(3)` и `.idxmax()`.

### hint
Качество модели: `cross_val_score(forest, X, y, cv=cv, scoring="roc_auc").mean()`. Таблица с возрастом: `X.join(pd.get_dummies(g["age_group"], prefix="age", dtype=int))` — индексы у `X` и `g` одинаковые, поэтому `join` ставит строки на места.

### hint
```python
single = pd.Series({c: max(roc_auc_score(old, X[c]), 1 - roc_auc_score(old, X[c])) for c in X.columns}).round(3)
top_proxy = single.idxmax()
X_age = X.join(pd.get_dummies(g["age_group"], prefix="age", dtype=int))
auc_without = round(cross_val_score(forest, X, y, cv=cv, scoring="roc_auc").mean(), 3)
auc_with = round(cross_val_score(forest, ..., y, cv=cv, scoring="roc_auc").mean(), 3)
```

### solution
```python
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
old = (g["age_group"] == "50+").astype(int)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)

single = pd.Series({c: max(roc_auc_score(old, X[c]), 1 - roc_auc_score(old, X[c])) for c in X.columns}).round(3)
top_proxy = single.idxmax()
X_age = X.join(pd.get_dummies(g["age_group"], prefix="age", dtype=int))
auc_without = round(cross_val_score(forest, X, y, cv=cv, scoring="roc_auc").mean(), 3)
auc_with = round(cross_val_score(forest, X_age, y, cv=cv, scoring="roc_auc").mean(), 3)
```

### explain
Сильнее всего возраст выдаёт приложение (0.66), за ним доля доставки (0.63) и стаж в программе (0.59): старшие реже ставят приложение и реже заказывают доставку. Возраст добавляет к ROC-AUC модели около 0.01 (0.908 → 0.918) — и, как можно проверить тем же `fair`, поднимает полноту старших гостей примерно с 0.64 до 0.70. Получается неудобная развилка: чувствительный признак немного помогает именно той группе, которую модель обделяет. Механического ответа нет: это решение бизнеса и юриста, а задача аналитика — положить на стол оба числа и описать риски.

## task: fair-toy | Три метрики на двенадцати гостях | warmup

В таблице `t` двенадцать гостей двух групп: ушёл ли гость (`churned`) и отправила ли ему модель бонус (`send`). Посчитайте по группам `selected` — долю получивших бонус среди всех гостей группы, `recall` — долю получивших среди уходящих и `precision` — долю уходящих среди получивших. Сохраните их тремя Series (индекс — группа, 2 знака).

### starter
```python
import pandas as pd

t = pd.DataFrame({
    "group":   ["A"] * 6 + ["B"] * 6,
    "churned": [1, 1, 1, 0, 0, 0,   1, 1, 1, 0, 0, 0],
    "send":    [1, 1, 1, 0, 0, 0,   1, 0, 0, 1, 1, 0],
})

```

### check
```python
import pandas as _pd
_t = _pd.DataFrame({"group": ["A"] * 6 + ["B"] * 6,
                    "churned": [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0],
                    "send": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]})
_w = {'selected': _t.groupby('group')['send'].mean(),
      'recall': _t[_t['churned'] == 1].groupby('group')['send'].mean(),
      'precision': _t[_t['send'] == 1].groupby('group')['churned'].mean()}
_how = {'selected': 'среднее send по всем гостям группы',
        'recall': 'среднее send только по уходящим (churned == 1)',
        'precision': 'среднее churned только по получившим (send == 1)'}
for name, ref in _w.items():
    got = need(name, _pd.Series)
    assert sorted(got.index) == ['A', 'B'], f'Индекс {name}: {list(got.index)} — нужны группы A и B.'
    for k in ['A', 'B']:
        assert close(got[k], ref[k], 0.006), f'{name}[{k!r}] = {got[k]}, а нужно {round(float(ref[k]), 2)}: {_how[name]}.'
```

### hint
Все три метрики — среднее одного столбца 0/1, но по разным строкам: `selected` — по всем, `recall` — по строкам `t["churned"] == 1`, `precision` — по строкам `t["send"] == 1`.

### hint
```python
selected = t.groupby("group")["send"].mean().round(2)
recall = t[t["churned"] == 1].groupby("group")["send"].mean().round(2)
precision = ...
```

### solution
```python
import pandas as pd

t = pd.DataFrame({
    "group":   ["A"] * 6 + ["B"] * 6,
    "churned": [1, 1, 1, 0, 0, 0,   1, 1, 1, 0, 0, 0],
    "send":    [1, 1, 1, 0, 0, 0,   1, 0, 0, 1, 1, 0],
})
selected = t.groupby("group")["send"].mean().round(2)
recall = t[t["churned"] == 1].groupby("group")["send"].mean().round(2)
precision = t[t["send"] == 1].groupby("group")["churned"].mean().round(2)
```

### explain
Обе группы получили бонус поровну — половина гостей (0.5 и 0.5). Но в группе A бонус достался всем трём уходящим (полнота 1.0, точность 1.0), а в группе B — одному из трёх (0.33 и 0.33): два бонуса ушли тем, кто и так остался бы. По одной доле отобранных модель выглядит справедливой, по полноте — нет. Поэтому в отчёте по группам всегда три числа, а не одно.

## task: missed | Кого модель пропускает | base

Проверьте утверждение из теории «из 120 пропущенных уходящих 48 — старшие, хотя их всего 18 % в базе». Прогнозы вне выборки уже посчитаны, бонус — `g["send"]` (порог 1/3). Сохраните `missed_n` — сколько уходящих не получили бонус, Series `missed_share` — доли групп среди них (индекс — `age_group`, 3 знака) и `base_old` — долю гостей 50+ во всей базе (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked", "age_group"]), dtype=int).fillna({"avg_check": 0})
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0)
p = cross_val_predict(forest, X, y, cv=cv, method="predict_proba")[:, 1]
g["send"] = p > 1 / 3
```

### starter
```python
import pandas as pd
# готово, как в теории: g (с age_group и send), p — прогнозы вне выборки

```

### check
```python
import pandas as _pd
_m = g[(g['churned'] == 1) & (~g['send'])]
assert need('missed_n') == len(_m), f'missed_n = {need("missed_n")}, а нужно {len(_m)}: уходящие (churned == 1), которым send == False.'
_s = _m['age_group'].value_counts(normalize=True)
s = need('missed_share', _pd.Series)
assert sorted(s.index) == sorted(_s.index), f'Индекс missed_share: {list(s.index)} — нужны три возрастные группы.'
for k in _s.index:
    assert close(s[k], _s[k], 0.0015), f'{k}: {s[k]}, а нужно {round(float(_s[k]), 3)} — доля группы среди пропущенных уходящих.'
_b = (g['age_group'] == '50+').mean()
assert close(need('base_old'), _b, 0.0015), f'base_old = {need("base_old")}, а нужно {round(float(_b), 3)}: доля 50+ среди всех 2 400 гостей.'
```

### hint
Пропущенные — строки, где одновременно `g["churned"] == 1` и `~g["send"]` (знак `~` — «не»). Доли групп — `value_counts(normalize=True)`.

### hint
```python
missed = g[(g["churned"] == 1) & (~g["send"])]
missed_n = len(missed)
missed_share = missed["age_group"].value_counts(normalize=True).round(3)
base_old = round(..., 3)
```

### solution
```python
import pandas as pd

missed = g[(g["churned"] == 1) & (~g["send"])]
missed_n = len(missed)
missed_share = missed["age_group"].value_counts(normalize=True).round(3)
base_old = round((g["age_group"] == "50+").mean(), 3)
```

### explain
Модель пропускает 120 уходящих, и 40 % из них — гости 50+ (48 человек), хотя в базе их 18 %. Доля старших среди пропущенных вдвое с лишним больше их доли в базе. Такое сравнение «доля среди пропущенных против доли в базе» понятно без слова «полнота» — его удобно показывать бизнесу.

## task: quiet-churn | Тихий уход | base

Почему модель пропускает старших? Сравните уходящих гостей разных групп. Возьмите только `churned == 1` и сохраните DataFrame `quiet` (индекс — `age_group`) со столбцами `med_days` — медиана `days_since_last` и `complained` — доля гостей с жалобой (`complaints > 0`, 3 знака). В `quietest` — группу с наименьшей долей жалоб. Модель здесь не нужна, только `guests_churn.csv` и `guests_age.csv`.

### starter
```python
import pandas as pd

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")

```

### check
```python
import pandas as _pd
_g = _pd.read_csv('guests_churn.csv').merge(_pd.read_csv('guests_age.csv'), on='guest_id')
_c = _g[_g['churned'] == 1]
_md = _c.groupby('age_group')['days_since_last'].median()
_cp = (_c['complaints'] > 0).groupby(_c['age_group']).mean()
q = need('quiet', _pd.DataFrame)
assert {'med_days', 'complained'} <= set(q.columns), f'Столбцы quiet: {list(q.columns)}, нужны med_days и complained.'
assert sorted(q.index) == sorted(_md.index), f'Индекс quiet: {list(q.index)} — нужны три возрастные группы.'
for k in _md.index:
    assert close(q.loc[k, 'med_days'], _md[k], 0.01), f'{k}: med_days = {q.loc[k, "med_days"]}, а нужно {float(_md[k])}. Медиана только по уходящим гостям группы.'
    assert close(q.loc[k, 'complained'], _cp[k], 0.0015), f'{k}: complained = {q.loc[k, "complained"]}, а нужно {round(float(_cp[k]), 3)}: доля complaints > 0 среди уходящих.'
assert need('quietest') == _cp.idxmin(), f'quietest = {need("quietest")!r}, а нужно {_cp.idxmin()!r}.'
```

### hint
Сначала отфильтруйте уходящих: `c = g[g["churned"] == 1]`. Флаг жалобы — `c["complaints"] > 0`; его среднее по группе — доля.

### hint
```python
c = g[g["churned"] == 1].copy()
c["complained"] = c["complaints"] > 0
quiet = c.groupby("age_group").agg(med_days=("days_since_last", "median"),
                                   complained=("complained", "mean")).round(3)
quietest = ...
```

### solution
```python
import pandas as pd

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guests_age.csv"), on="guest_id", validate="one_to_one")
c = g[g["churned"] == 1].copy()
c["complained"] = c["complaints"] > 0
quiet = c.groupby("age_group").agg(med_days=("days_since_last", "median"),
                                   complained=("complained", "mean")).round(3)
quietest = quiet["complained"].idxmin()
```

### explain
Медианная пауза у уходящих гостей 50+ — 22 дня (у 30–49 лет — 32, у младших — 24), и жалобу оставили только 9.8 % из них против 29–37 % у остальных. Два самых сильных сигнала модели — давность и жалоба — у старших слабее, поэтому лес их и пропускает. Вывод для бизнеса: нужен признак, который ловит тихий уход, — например, падение частоты визитов относительно прошлого квартала.
