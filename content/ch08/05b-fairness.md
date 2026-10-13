---
title: "Этика данных и справедливость модели"
lead: "Модель, которая хорошо работает в среднем, может систематически недодавать одной группе гостей — даже если возраста или пола среди признаков нет. Разбираемся, какие данные брать нельзя, как проверить справедливость по группам на честных прогнозах и как найти признаки-заместители."
files: [guests_churn.csv, guests_age.csv]
recap:
  - "Этика данных: чувствительные признаки (здоровье, национальность, взгляды) в модель не берут; пол и возраст — только осознанным решением с юристом. Убрать признак мало: признаки-заместители (приложение → возраст) его восстанавливают."
  - "Справедливость проверяют по группам: доля отобранных, полнота, точность. Одинаковая доля отобранных не значит, что уходящие гости группы получают бонус одинаково часто; для групп берут прогнозы вне выборки (`cross_val_predict`)."
---

Модель — логистическая регрессия на масштабированных признаках гостей из урока «Объяснить модель бизнесу».

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
Охраннику запретили не пускать людей по возрасту, но разрешили — по тому, есть ли у человека смартфон. Формально правило соблюдено, а на деле пожилых снова не пускают. Прокси работает так же: модель не видит возраст, но видит то, что с ним тесно связано. Где аналогия хромает: охранник может делать это нарочно, а модель — нет, она просто находит связи в данных. Поэтому проверять приходится нам.
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

Маркетинг предлагает снизить порог до 0.25, «чтобы старшие гости тоже получали бонусы». Проверьте. По прогнозам вне выборки `p` (уже посчитаны в заготовке) отправьте бонус при `p > 0.25` и соберите таблицу `fair25` по `age_group` со столбцами `selected` (доля получивших бонус) и `recall` (доля получивших среди уходящих), 3 знака. Сохраните в `gap25` разницу между наибольшей и наименьшей полнотой групп (3 знака), а в `extra_bonuses` — на сколько бонусов больше, чем при пороге 1/3.

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
```

### explain
Полнота выросла у всех: у старших с 0.64 до 0.71, у остальных до 0.87–0.89. Разрыв почти не изменился — 0.18 против 0.20 при пороге 1/3, а бонусов стало больше на 127, и только 25 из них достались старшим гостям. Общий порог — плохой инструмент против перекоса: он двигает все группы сразу. Разрыв закрывают другие шаги — признаки «тихого ухода», другой канал удержания или, по решению бизнеса и юриста, отдельный порог.

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
