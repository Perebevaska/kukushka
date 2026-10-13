---
title: "Регуляризация: штраф за большие веса"
lead: "Линейная модель может раздуть вес признака, который на обучающих данных случайно хорошо работает. Регуляризация штрафует большие веса: разбираемся, как параметр C держит веса в узде, почему он работает «наоборот» и как штраф L1 сам отбирает признаки."
files: [guests_churn.csv]
recap:
  - "Регуляризация штрафует большие веса. `C` — обратная сила штрафа: меньше `C` — веса меньше. L2 (по умолчанию) сжимает все веса, L1 (`l1_ratio=1, solver=\"liblinear\"`) обнуляет лишние."
  - "L1 (`l1_ratio=1, solver=\"liblinear\"`) обнуляет слабые признаки и сам отбирает признаки; L2 (по умолчанию) сжимает все веса понемногу."
---

Признаки — таблица гостей из урока «Масштабирование и ближайшие соседи», стандартизированная `StandardScaler`, обученным на train.

## Регуляризация: штраф за большие веса

Линейная модель может подогнать веса под случайные особенности обучающих данных: дать огромный вес признаку, который на train «случайно» хорошо разделяет классы. Защита — **регуляризация** (regularization): к ошибке модели при обучении добавляется штраф за величину весов. Модель ищет компромисс: хорошо объяснить данные, но небольшими весами.

::: tip Аналогия
Бариста разрешили менять базовый рецепт, но каждое отступление от него стоит ему «штрафных баллов». Без штрафа он подогнал бы рецепт под вкусы трёх сегодняшних гостей; со штрафом меняет только то, что заметно нравится многим. Веса модели — это и есть отступления от нулевого «базового рецепта», а штраф не даёт раздувать их ради случайностей обучающей выборки.
:::

В `LogisticRegression` силу штрафа задаёт параметр `C`, причём **наоборот**: `C` — это «сколько свободы дать модели». Маленький `C` — сильный штраф, веса прижаты к нулю. Большой `C` — штраф слабый. По умолчанию `C=1`. Именно об этом «придерживании весов» мы упоминали в главе 6.

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

for C in [0.001, 0.01, 0.1, 1, 10]:
    m = LogisticRegression(C=C).fit(Xs_train, y_train)
    p = m.predict_proba(Xs_test)[:, 1]
    print(f"C={C:<6} сумма |весов| {np.abs(m.coef_).sum():5.2f}  "
          f"AUC {roc_auc_score(y_test, p):.3f}  F1 {f1_score(y_test, m.predict(Xs_test)):.3f}")
```

Что видно:

- чем меньше `C`, тем меньше веса: при `C=0.001` их сумма в пять раз меньше, чем при `C=1`;
- AUC почти не меняется — порядок гостей по риску сохраняется, даже когда веса сжаты;
- а F1 при `C=0.001` падает примерно до 0.18: сжатые веса тянут все вероятности к средней доле ушедших (около 0.22), и до порога 0.5 почти никто не дотягивает. Но AUC тот же — значит, порядок гостей верный, и с более низким порогом (урок «Порог по деньгам») такая модель работала бы не хуже.

От `C=0.1` и выше результат почти одинаковый. Это нормально: у нас 1800 гостей и всего 15 признаков, переобучиться линейной модели здесь трудно. Регуляризация по-настоящему спасает, когда признаков много, а строк мало — например, сотни флагов товаров на пару тысяч гостей. Подбирать `C` по кросс-валидации научимся в уроке «Подбор гиперпараметров».

::: note Масштаб и регуляризация связаны
Штраф одинаково давит на все веса. Если признаки в разных единицах, штраф получается нечестным: вес «за рубль» маленький сам по себе и почти не штрафуется, а вес «за флаг» — штрафуется сильно. Поэтому перед регуляризованной моделью признаки всегда масштабируют.
:::

::: quiz
Аналитик уменьшил `C` у логистической регрессии с 1 до 0.001. Что произойдёт с моделью?

- [x] Штраф станет сильнее: веса прижмутся к нулю, вероятности стянутся к средней доле ушедших
  > `C` — обратная сила штрафа. При очень маленьком `C` модели «дороже» любой заметный вес, и её оценки стягиваются к общей доле ухода: до порога 0.5 почти никто не дотягивает.
- [ ] Штраф ослабнет, веса вырастут, модель сильнее подстроится под train
  > Это частая путаница: у `LogisticRegression` `C` работает наоборот. Слабый штраф — большой `C`.
- [ ] Порядок гостей по риску перемешается, и AUC упадёт до 0.5
  > В уроке AUC почти не менялся даже при сильном сжатии весов: порядок сохраняется, страдают ответы при пороге 0.5 — F1 падает.
- [ ] Ничего: на 15 признаках регуляризация не действует
  > Действует всегда: веса при `C=0.001` в пять раз меньше по сумме. Слабо меняются лишь метрики при `C` от 0.1 и выше.
:::

{{practice: c-sweep}}

## L1: регуляризация, которая отбирает признаки

Штраф по умолчанию называется **L2**: он считается по квадратам весов и сжимает их все понемногу, но почти никогда не делает ровно нулём. Другой вид штрафа — **L1** — считается по модулям весов. У него полезное свойство: слабые признаки он обнуляет совсем. Получается модель, которая сама отбирает признаки.

В sklearn 1.8 вид штрафа задаёт параметр `l1_ratio`: 0 — L2, 1 — L1. `solver` — алгоритм, которым sklearn подбирает веса. Алгоритм по умолчанию (`lbfgs`) рассчитан на гладкий штраф по квадратам и штраф по модулям не берёт, поэтому для L1 указываем другой — `solver="liblinear"`:

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

for C in [0.005, 0.01, 0.03, 0.1]:
    m = LogisticRegression(C=C, l1_ratio=1, solver="liblinear").fit(Xs_train, y_train)
    w = pd.Series(m.coef_[0], index=X.columns)
    kept = list(w[w != 0].index)
    auc = roc_auc_score(y_test, m.predict_proba(Xs_test)[:, 1])
    print(f"C={C}: признаков {len(kept):2}, AUC {auc:.3f}, {kept[:4]}")
```

При `C=0.01` от 15 признаков остаются три — давность визита, число визитов и жалобы, — а AUC почти такой же, как у полной модели (около 0.895 против 0.897). Для отдела лояльности это ценный вывод: три понятных числа объясняют уход почти так же хорошо, как вся таблица.

::: figure l1-l2
Веса восьми самых сильных признаков. L2 при сильном штрафе (C = 0.01) уменьшает все веса, но оставляет их ненулевыми; L1 при том же C обнуляет всё, кроме давности визита, числа визитов и жалоб.
:::

::: warn Старое написание
В статьях и старом коде вы встретите `LogisticRegression(penalty="l1", solver="liblinear")`. В sklearn 1.8 параметр `penalty` объявлен устаревшим и выдаёт предупреждение `FutureWarning`, а в будущих версиях его уберут. Смысл тот же: `penalty="l1"` → `l1_ratio=1`, `penalty="l2"` → `l1_ratio=0`.
:::

::: deep Ridge и Lasso
Для регрессии (предсказание чисел, урок «Регрессия: сколько минут» главы 6) те же штрафы встроены в отдельные модели из `sklearn.linear_model`: **Ridge** — линейная регрессия с L2, **Lasso** — с L1. Сила штрафа у них задаётся параметром `alpha`, и он работает прямо: больше `alpha` — сильнее штраф (у `LogisticRegression` наоборот, `C`). Смесь L1 и L2 называется ElasticNet — у логистической регрессии это `l1_ratio` между 0 и 1 с `solver="saga"`.
:::

::: warn Типичные ошибки
- **`C` читают как силу штрафа.** У `LogisticRegression` всё наоборот: маленький `C` — сильный штраф.
- **Регуляризация без масштаба.** Штраф давит на все веса одинаково, поэтому признаки сначала приводят к одному масштабу.
:::

{{practice: lasso}}

## Практика

## task: c-sweep | Сила регуляризации | base

Для `C` из списка `[0.001, 0.01, 0.1, 1, 10]` обучите `LogisticRegression(C=C)` на стандартизированных признаках. Соберите таблицу `res` с индексом — значениями `C` (в том же порядке) и столбцами:

- `coef_sum` — сумма модулей весов;
- `auc` — ROC-AUC на тесте;
- `f1` — F1 на тесте при пороге по умолчанию.

Округлять не нужно. В `best_c` сохраните `C` с наибольшим F1.

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

rows = []
for C in [0.001, 0.01, 0.1, 1, 10]:
    pass
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import f1_score as _f1, roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_s = _SS().fit(_a)
_tr, _te = _s.transform(_a), _s.transform(_b)
_Cs = [0.001, 0.01, 0.1, 1, 10]
_ref = {}
for _C in _Cs:
    _m = _LR(C=_C).fit(_tr, _c)
    _ref[_C] = (_np.abs(_m.coef_).sum(), _auc(_d, _m.predict_proba(_te)[:, 1]), _f1(_d, _m.predict(_te)))
_t = need('res', _pd.DataFrame)
assert {'coef_sum', 'auc', 'f1'} <= set(_t.columns), f'Столбцы res: {list(_t.columns)}. Нужны coef_sum, auc и f1.'
assert [float(v) for v in _t.index] == _Cs, f'Индекс res: {list(_t.index)}. Нужны значения C по порядку: {_Cs}.'
for _C in _Cs:
    _cs, _au, _ff = _ref[_C]
    assert close(float(_t.loc[_C, 'coef_sum']), _cs, 1e-3), f'При C={_C} coef_sum = {float(_t.loc[_C, "coef_sum"]):.3f}, а ожидалось {_cs:.3f}. Это сумма модулей: np.abs(model.coef_).sum().'
    assert close(float(_t.loc[_C, 'auc']), _au, 1e-3), f'При C={_C} auc = {float(_t.loc[_C, "auc"]):.4f}, а ожидалось {_au:.4f}.'
    assert close(float(_t.loc[_C, 'f1']), _ff, 1e-3), f'При C={_C} f1 = {float(_t.loc[_C, "f1"]):.4f}, а ожидалось {_ff:.4f}.'
_bc = max(_Cs, key=lambda k: _ref[k][2])
assert close(float(need('best_c')), _bc), f'best_c = {need("best_c")}, а наибольший F1 у C={_bc}. Подойдёт res["f1"].idxmax().'
```

### hint
В цикле: `m = LogisticRegression(C=C).fit(Xs_train, y_train)`, затем `rows.append({"C": C, "coef_sum": ..., "auc": ..., "f1": ...})`.

### hint
`res = pd.DataFrame(rows).set_index("C")`, `best_c = res["f1"].idxmax()`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

rows = []
for C in [0.001, 0.01, 0.1, 1, 10]:
    m = LogisticRegression(C=C).fit(Xs_train, y_train)
    rows.append({
        "C": C,
        "coef_sum": np.abs(m.coef_).sum(),
        "auc": roc_auc_score(y_test, m.predict_proba(Xs_test)[:, 1]),
        "f1": f1_score(y_test, m.predict(Xs_test)),
    })
res = pd.DataFrame(rows).set_index("C")
best_c = res["f1"].idxmax()
print(res.round(3))
```

### explain
AUC от `C` почти не зависит, а F1 — очень: при сильном штрафе вероятности сжимаются к средней доле ушедших и не дотягивают до 0.5. Выбирать `C` по тесту, как здесь, можно только для учебной картинки — честно это делают кросс-валидацией (урок «Подбор гиперпараметров»).

## task: lasso | Три признака вместо пятнадцати | plus

Обучите логистическую регрессию с L1-штрафом и `C=0.01` (`solver="liblinear"`) на стандартизированных признаках. Сохраните:

- `kept` — список названий признаков с ненулевым весом (в порядке столбцов `X`);
- `auc_l1` — ROC-AUC этой модели на тесте (3 знака);
- `auc_l2` — ROC-AUC `LogisticRegression()` на тех же признаках (3 знака).

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
scaler = StandardScaler().fit(X_train)
Xs_train, Xs_test = scaler.transform(X_train), scaler.transform(X_test)

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
_tr, _te = _s.transform(_a), _s.transform(_b)
_m1 = _LR(C=0.01, l1_ratio=1, solver='liblinear').fit(_tr, _c)
_k = list(_X.columns[_m1.coef_[0] != 0])
_got = list(need('kept'))
assert len(_got) < len(_X.columns), f'В kept {len(_got)} признаков — все. Похоже, штраф L2: для L1 нужен l1_ratio=1 и solver="liblinear".'
assert _got == _k, f'kept = {_got}, а ожидалось {len(_k)} признака. Проверьте C=0.01 и что модель обучена на отмасштабированных признаках.'
_v1 = round(_auc(_d, _m1.predict_proba(_te)[:, 1]), 3)
_v2 = round(_auc(_d, _LR().fit(_tr, _c).predict_proba(_te)[:, 1]), 3)
assert close(need('auc_l1'), _v1), f'auc_l1 = {need("auc_l1")}, а ожидалось {_v1}.'
assert close(need('auc_l2'), _v2), f'auc_l2 = {need("auc_l2")}, а ожидалось {_v2}. Это обычная LogisticRegression() на тех же Xs_train и Xs_test.'
```

### hint
`LogisticRegression(C=0.01, l1_ratio=1, solver="liblinear")`.

### hint
Веса с названиями: `w = pd.Series(model.coef_[0], index=X.columns)`; ненулевые — `list(w[w != 0].index)`.

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

l1 = LogisticRegression(C=0.01, l1_ratio=1, solver="liblinear").fit(Xs_train, y_train)
w = pd.Series(l1.coef_[0], index=X.columns)
kept = list(w[w != 0].index)
auc_l1 = round(roc_auc_score(y_test, l1.predict_proba(Xs_test)[:, 1]), 3)
auc_l2 = round(roc_auc_score(y_test, LogisticRegression().fit(Xs_train, y_train).predict_proba(Xs_test)[:, 1]), 3)
print(kept, auc_l1, auc_l2)
```

### explain
Три признака — давность, частота визитов и жалобы — дают почти тот же AUC, что все пятнадцать. Такую модель легко объяснить и легко внедрить: её можно посчитать даже формулой в Excel. Но «L1 обнулил признак» не значит «признак не связан с уходом» — он может просто дублировать оставшиеся.
