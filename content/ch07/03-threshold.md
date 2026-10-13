---
title: Порог, PR- и ROC-кривые
lead: "Модель выдаёт вероятность ухода, а решение «дать бонус или нет» принимает порог. Учимся двигать порог и видеть, как меняются точность и полнота, рисовать PR- и ROC-кривые и понимать, что на самом деле измеряет ROC-AUC. Как выбрать порог по деньгам — в следующем уроке."
files: [guests_churn.csv]
recap:
  - "Порог — решение бизнеса, а не свойство модели: `pred = p >= t`. Ниже порог — выше полнота и ниже точность."
  - "`precision_recall_curve(y_true, p)` → precision, recall, thresholds; в precision и recall на одну точку больше, чем порогов."
  - "ROC-кривая: по оси X — доля ложных тревог FPR = FP / (FP + TN), по оси Y — полнота TPR. `roc_curve(y_true, p)` → fpr, tpr, thresholds."
  - "`roc_auc_score(y_true, p)` — площадь под ROC-кривой. 0.5 — монетка, 1 — идеальное ранжирование. Не зависит от порога."
  - "AUC = вероятность, что случайный ушедший гость получит оценку выше случайного оставшегося (ничьи — за половину)."
---

## Порог — ручка, которую крутит бизнес

В прошлом уроке мы оценивали лес по ответам `predict`: точность около 0.8, полнота около 0.67 — треть уходящих гостей модель не замечает. Но лес умеет больше, чем «да / нет»: `predict_proba` (глава 6, урок «Логистическая регрессия и вероятности») выдаёт вероятность ухода, а ответ получается сравнением вероятности с **порогом** (threshold). Порог 0.5 — просто значение по умолчанию. Отдел лояльности может выбрать любой другой.

Подготовка данных — как в проекте главы 6:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

for t in [0.3, 0.5, 0.7]:
    pred = p >= t
    print(f"порог {t}: бонусов {pred.sum()}, precision {precision_score(y_test, pred):.2f}, "
          f"recall {recall_score(y_test, pred):.2f}, F1 {f1_score(y_test, pred):.2f}")
```

**Что здесь происходит:**

- `model.predict_proba(X_test)` — таблица 600 × 2: вероятности «останется» и «уйдёт»; `[:, 1]` берёт второй столбец.
- `pred = p >= t` — свой ответ для каждого порога, модель при этом не переобучается.
- `pred.sum()` — сколько гостей получат бонус: `True` считается за 1.

Метрики из урока «Precision, recall и F1» принимают и массив `True / False` — sklearn считает `True` за 1.

- **Порог 0.3**: бонус получат 187 гостей из 600, модель ловит около 87 % уходящих, но только около 62 % бонусов достаются тем, кто действительно ушёл бы.
- **Порог 0.7**: бонусов всего 56, и почти все (93 %) по адресу, зато поймано меньше 40 % уходящих.

Это тот же компромисс, что и в главе 6 с тревогами диспетчера, только теперь у него есть строгие названия. Чем ниже порог, тем больше «да»: полнота растёт (или стоит на месте), точность обычно падает.

::: figure thr-move
Двенадцать условных гостей по убыванию вероятности ухода. Порог — вертикальная черта: всё левее получает бонус. Опускаем порог с 0.5 до 0.3 — бонусов больше, пойманы все уходящие, но и лишних бонусов прибавилось.
:::

::: note Ровно 0.5
Вероятность леса — доля деревьев, проголосовавших за «уйдёт». Из 100 деревьев может проголосовать ровно 50, и тогда p = 0.5. `predict` в такой ничьей отвечает «останется», а `p >= 0.5` — «уйдёт». Поэтому при пороге 0.5 цифры здесь на несколько гостей отличаются от прошлого урока. Дальше везде используем `p >= t`.
:::

::: predict
```python static
y = [1, 0, 1, 1, 0]
p = [0.9, 0.6, 0.4, 0.2, 0.1]
for t in [0.5, 0.3]:
    caught = sum(1 for yi, pi in zip(y, p) if yi == 1 and pi >= t)
    print(t, round(caught / sum(y), 2))
```

- `0.5 0.67 | 0.3 0.67`
- [x] `0.5 0.33 | 0.3 0.67`
- `0.5 0.33 | 0.3 1.0`

Почему: при пороге 0.5 из трёх ушедших пойман только гость с 0.9 — полнота 1/3. При 0.3 добавляется гость с 0.4 — 2/3. Гость с 0.2 остаётся незамеченным, пока порог выше 0.2.
:::

Посмотрите, как порог меняет ответы леса на тестовых гостях:

::: widget threshold
Матрица ошибок леса на тестовой выборке (600 гостей, из них 134 ушли) при выбранном пороге. Порог двигает гостей между колонками, но сами вероятности не меняются.
:::

::: quiz
При пороге 0.3 лес из примера выдаёт 187 бонусов: точность 0.62, полнота 0.87. Отдел лояльности может позволить себе не больше 100 бонусов. Что делать?

- [x] Поднять порог: бонусов станет меньше, точность вырастет, а полнота упадёт — часть уходящих останется без бонуса
  > Выше черта — меньше «да». На этих данных 100 бонусов получается около порога 0.55: точность около 0.81, полнота около 0.63.
- [ ] Опустить порог: так бонусы получат самые рискованные
  > Ниже порог — больше бонусов, а их и так слишком много. Самых рискованных отбирает как раз высокий порог.
- [ ] Поднять порог: и точность, и полнота вырастут
  > Полнота при более высоком пороге не растёт: уходящие, которые не дотянули до нового порога, бонус больше не получат.
- [ ] Порог не поможет — нужна другая модель
  > Порог и есть способ подстроить модель под бюджет. Другая модель может сдвинуть весь компромисс, но эта задача решается порогом.
:::

{{practice: thr-30, rates}}

## Кривая точность — полнота

Перебирать пороги руками не нужно: `precision_recall_curve` перебирает **все** пороги, при которых меняется ответ, и для каждого считает точность и полноту. Соединив точки, получаем **PR-кривую** (precision-recall curve).

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

precision, recall, thresholds = precision_recall_curve(y_test, p)
print(len(precision), len(recall), len(thresholds))

fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(recall, precision)
ax.axhline(y_test.mean(), color="grey", linestyle="--")
ax.set_xlabel("recall (поймали уходящих)")
ax.set_ylabel("precision (бонусы по адресу)")
ax.set_title("PR-кривая леса")
```

Как читать:

- каждая точка — один порог. Слева (высокий порог) мало бонусов и высокая точность, справа (низкий порог) почти все уходящие пойманы, но точность падает;
- пунктир — доля ушедших в тесте (около 0.22). Это точность модели «бонус всем». У хорошей модели кривая идёт выше пунктира; если на каких-то порогах она ныряет под него, на этих порогах модель отбирает гостей не лучше случайного выбора (на самых высоких порогах точность считается по нескольким гостям и может прыгать);
- чем ближе кривая к правому верхнему углу, тем лучше модель: высокая полнота без потери точности.

В `precision` и `recall` на один элемент больше, чем в `thresholds`: в конце sklearn добавляет точку «порог выше всех оценок» — никому не даём бонус, полнота 0, точность условно 1. Чтобы сложить всё в таблицу, последний элемент отбрасываем.

Так кривая отвечает на конкретный вопрос. Отдел лояльности говорит: «Нужно поймать хотя бы 80 % уходящих. Какой порог даст при этом самую высокую точность?»

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

precision, recall, thresholds = precision_recall_curve(y_test, p)
curve = pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1]})
ok = curve[curve["recall"] >= 0.8]
print(ok.sort_values("precision").tail(1).round(3))
```

::: sql
Это обычный запрос к таблице порогов: `WHERE recall >= 0.8 ORDER BY precision DESC LIMIT 1`.
:::

{{practice: recall80}}

## ROC-кривая

Вторая популярная кривая смотрит на ошибки с другой стороны. По оси Y — та же полнота, которую здесь называют **TPR** (true positive rate, доля пойманных уходящих). По оси X — **FPR** (false positive rate) — доля **оставшихся** гостей, которым бонус дали зря:

FPR = FP / (FP + TN).

Перебирая пороги от высокого к низкому, мы идём из точки (0, 0) — никому бонус — в точку (1, 1) — бонус всем. Это **ROC-кривая** (от receiver operating characteristic — термин пришёл из радиолокации).

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

fpr, tpr, thresholds = roc_curve(y_test, p)
print(thresholds[:3])

fig, ax = plt.subplots(figsize=(4.5, 4.5))
ax.plot(fpr, tpr, label="лес")
ax.plot([0, 1], [0, 1], color="grey", linestyle="--", label="случайный порядок")
ax.set_xlabel("FPR (зря дали бонус)")
ax.set_ylabel("TPR (поймали уходящих)")
ax.set_title("ROC-кривая")
ax.legend()
```

Первый порог — `inf` (бесконечность): это точка «никому», выше любой оценки. Диагональ — модель, которая раздаёт вероятности наугад: какую бы долю гостей она ни выбрала, уходящих среди них столько же, сколько в среднем, и TPR равен FPR. Чем сильнее кривая выгибается к левому верхнему углу, тем лучше модель отделяет уходящих от остальных.

{{practice: roc-plot}}

## Разберём вместе: ROC-кривая на пяти гостях

Возьмём гостей из задачки выше: факт `[1, 0, 1, 1, 0]`, вероятности `[0.9, 0.6, 0.4, 0.2, 0.1]`. Ушедших трое, оставшихся двое. Опускаем порог от гостя к гостю и считаем две доли:

| порог | бонус получили | TPR = пойманные / 3 | FPR = зря / 2 |
|---|---|---|---|
| выше 0.9 | никто | 0 | 0 |
| 0.9 | первый (ушёл) | 1/3 | 0 |
| 0.6 | + второй (остался) | 1/3 | 1/2 |
| 0.4 | + третий (ушёл) | 2/3 | 1/2 |
| 0.2 | + четвёртый (ушёл) | 1 | 1/2 |
| 0.1 | + пятый (остался) | 1 | 1 |

Каждый ушедший поднимает кривую вверх на 1/3, каждый оставшийся сдвигает её вправо на 1/2. Площадь под этой «лесенкой»: от FPR 0 до 1/2 высота 1/3, потом от 1/2 до 1 высота 1. Итого 1/2 × 1/3 + 1/2 × 1 = **0.667**.

Сверим с парами: пар «ушедший — оставшийся» 3 × 2 = 6, верно упорядочены четыре (0.9 выше обоих, 0.4 и 0.2 выше только 0.1). 4 / 6 = **0.667** — площадь и пары дают одно и то же.

::: figure roc-toy
Разбор с пятью гостями. Слева — «лесенка» ROC: каждый ушедший поднимает кривую на 1/3, каждый оставшийся сдвигает вправо на 1/2; закрашенная площадь — 0.667. Справа — те же 0.667 как доля верно упорядоченных пар.
:::

```python
from sklearn.metrics import roc_curve, roc_auc_score
y = [1, 0, 1, 1, 0]
p = [0.9, 0.6, 0.4, 0.2, 0.1]
fpr, tpr, thr = roc_curve(y, p, drop_intermediate=False)
print("FPR:", fpr.round(2).tolist())
print("TPR:", tpr.round(2).tolist())
print(round(roc_auc_score(y, p), 3))
```

Что получилось: ROC-кривая — это просто путь по отсортированному списку гостей. Хорошая модель ставит ушедших в начало списка, и кривая сначала идёт вверх, а уже потом вправо.

::: tip Какую кривую смотреть
Когда редкий класс — главное (уходящие гости, мошенничество, брак), PR-кривая честнее: в ней сразу видно, сколько бонусов уйдёт впустую. ROC-кривая на сильном дисбалансе выглядит оптимистично — FPR делится на большое число оставшихся гостей и растёт медленно.
:::

## ROC-AUC: одно число вместо кривой

Площадь под ROC-кривой называют **ROC-AUC** (area under curve). У идеальной модели кривая проходит через левый верхний угол, площадь равна 1. У случайной кривая — диагональ, площадь 0.5.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

p_rf = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]
p_lr = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]
print(f"лес: {roc_auc_score(y_test, p_rf):.3f}")
print(f"логистическая регрессия: {roc_auc_score(y_test, p_lr):.3f}")
```

Обратите внимание: `roc_auc_score` получает **вероятности**, а не ответы `predict`. AUC не зависит от порога — он оценивает, насколько хорошо модель **упорядочивает** гостей по риску. У леса около 0.91, у логистической регрессии около 0.90.

У AUC есть простой смысл без всяких площадей: **это вероятность того, что случайно выбранный ушедший гость получит оценку выше, чем случайно выбранный оставшийся.**

::: tip Аналогия
Представьте парную дегустацию вслепую: дегустатору ставят две чашки — одну из удачной партии зерна, другую из неудачной — и просят показать, какая лучше. Если повторить это на сотнях пар, доля верных выборов и есть аналог AUC: оценивается не то, сколько баллов поставлено каждой чашке, а умение расставить их по порядку. Аналогия хромает в одном: модель ничего не выбирает, мы просто сравниваем две её оценки, и одинаковые оценки засчитываются за половину.
:::

Проверим на 10 000 случайных пар:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

left = p[y_test == 1]     # оценки ушедших
stayed = p[y_test == 0]   # оценки оставшихся
rng = np.random.default_rng(0)
a = rng.choice(left, 10_000)
b = rng.choice(stayed, 10_000)
share = (a > b).mean() + 0.5 * (a == b).mean()
print(f"пары: {share:.3f}, roc_auc_score: {roc_auc_score(y_test, p):.3f}")
```

`rng.choice(массив, n)` выбирает n случайных элементов с повторами (генератор случайных чисел — глава 5). Одинаковые оценки (ничьи) засчитываются за половину. Две цифры почти совпадают — разница только от случайности выборки пар.

Отсюда понятно, почему AUC не зависит от порога и почему он так удобен для **ранжирования**: список «кому бонус в первую очередь» хорош ровно настолько, насколько часто уходящие оказываются в нём выше оставшихся.

::: predict
```python static
from sklearn.metrics import roc_auc_score
print(roc_auc_score([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]))
```

- `0.5`
- [x] `0.75`
- `1.0`

Почему: пар «ушедший — оставшийся» четыре. Ушедший с 0.8 выше обоих оставшихся, ушедший с 0.35 выше 0.1, но ниже 0.4. Верно упорядочены 3 пары из 4.
:::

::: warn
Высокий AUC не значит, что порог 0.5 хорош. AUC говорит о порядке, а не о том, где провести черту. Модель с AUC 0.91 при неудачном пороге может давать полноту 0.4.
:::

::: quiz
У модели ROC-AUC = 0.5. Что это значит?

- [x] Она ранжирует гостей не лучше случайного угадывания
  > AUC — вероятность, что случайный уходящий получит больший риск, чем случайный остающийся. 0.5 — подбрасывание монетки.
- [ ] Она права в половине случаев
  > AUC — про порядок вероятностей, а не про долю верных ответов при каком-то пороге.
- [ ] Порог нужно поставить 0.5
  > AUC не зависит от порога: он считается по всем порогам сразу.
- [ ] Это хороший результат для несбалансированных данных
  > Лес из урока даёт около 0.91, а 0.5 — это отсутствие ранжирования.
:::

{{practice: p-auc, three-auc, pairs}}

::: warn Типичные ошибки
- **`predict` вместо `predict_proba`.** `roc_auc_score(y, model.predict(X))` считает AUC по нулям и единицам — получится заниженная «двухточечная» оценка.
- **Не тот столбец.** `predict_proba(X)[:, 0]` — вероятность «останется»; AUC выйдет 1 − настоящий.
- **`>` и `>=`.** У леса вероятности — доли деревьев, ровные значения вроде 0.5 встречаются часто; договоритесь об одном знаке и используйте его везде.
- **Порог выбран на тесте и отчитан на нём же.** Прибыль на тесте после подбора — оптимистичная оценка.
:::

::: deep Площадь под PR-кривой
У PR-кривой тоже есть «площадь» — `average_precision_score(y_true, p)` (средняя точность). Она полезна, когда сравнивают модели для редкого класса. Но если известны деньги, лучше считать деньги: никакая метрика не знает цену бонуса.
:::


## Практика

## task: thr-30 | Порог 0.3 | warmup

Отдел лояльности решил давать бонус всем, у кого вероятность ухода 0.3 и выше. Посчитайте для тестовых гостей: `n_bonus` — сколько бонусов раздадут (целое число), `prec` и `rec` — точность и полноту при таком пороге (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_score as _ps, recall_score as _rs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_pr = _p >= 0.3
assert need('n_bonus') == int(_pr.sum()), f'n_bonus = {need("n_bonus")}, а ожидалось {int(_pr.sum())}. Это число тестовых гостей с p ≥ 0.3.'
assert close(need('prec'), round(_ps(_d, _pr), 3)), f'prec = {need("prec")}, а ожидалось {round(_ps(_d, _pr), 3)}. Порог 0.3, сравнение «больше или равно», первый аргумент — y_test.'
assert close(need('rec'), round(_rs(_d, _pr), 3)), f'rec = {need("rec")}, а ожидалось {round(_rs(_d, _pr), 3)}.'
```

### hint
Ответы модели при пороге: `pred = p >= 0.3` — массив `True / False`. Число бонусов — `int(pred.sum())`.

### hint
`precision_score(y_test, pred)` и `recall_score(y_test, pred)`; не забудьте `round(..., 3)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]

pred = p >= 0.3
n_bonus = int(pred.sum())
prec = round(precision_score(y_test, pred), 3)
rec = round(recall_score(y_test, pred), 3)
```

## task: p-auc | ROC-AUC логистической регрессии | warmup

Соберите программу: обучить логистическую регрессию и вывести ROC-AUC на тесте (3 знака).

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)
p = model.predict_proba(X_test)[:, 1]
print(round(roc_auc_score(y_test, p), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = round(_auc(_d, _LR(max_iter=2000).fit(_a, _c).predict_proba(_b)[:, 1]), 3)
assert _lines == [str(_w)], f'Программа вывела {_lines}, а должна вывести одно число — ROC-AUC на тесте.'
```

### hint
Порядок: данные → `y` и `X` → разбиение → модель → вероятности → AUC.

## task: rates | TPR и FPR | warmup

Для порога 0.4 разложите матрицу ошибок на тесте в четыре числа `tn, fp, fn, tp` (урок «Матрица ошибок») и посчитайте `tpr` — долю пойманных уходящих и `fpr` — долю оставшихся гостей, которым зря дали бонус (обе — 3 знака). Это одна точка ROC-кривой.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import confusion_matrix as _cm
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_tn, _fp, _fn, _tp = _cm(_d, _p >= 0.4).ravel()
_t, _f = round(_tp / (_tp + _fn), 3), round(_fp / (_fp + _tn), 3)
assert close(need('tpr'), _t), f'tpr = {need("tpr")}, а ожидалось {_t}. TPR = TP / (TP + FN) — это полнота.'
assert close(need('fpr'), _f), f'fpr = {need("fpr")}, а ожидалось {_f}. FPR = FP / (FP + TN): делим на всех оставшихся гостей, а не на все бонусы.'
```

### hint
`tn, fp, fn, tp = confusion_matrix(y_test, p >= 0.4).ravel()` — порядок как в раскладке `[[TN, FP], [FN, TP]]`.

### hint
TPR = TP / (TP + FN), FPR = FP / (FP + TN).

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

tn, fp, fn, tp = confusion_matrix(y_test, p >= 0.4).ravel()
tpr = round(tp / (tp + fn), 3)
fpr = round(fp / (fp + tn), 3)
```

### explain
При пороге 0.4 модель ловит больше трёх четвертей уходящих, а зря тревожит лишь около 10 % оставшихся. На ROC-кривой это точка, где кривая уже высоко, но ещё близко к левому краю.

## task: recall80 | Порог под план по полноте | base

Отдел лояльности хочет поймать **не меньше 85 %** уходящих гостей. По PR-кривой леса на тесте найдите порог, который при этом даёт самую высокую точность. Сохраните `best_t` — этот порог (3 знака), `best_prec` — точность при нём (3 знака) и `curve` — таблицу DataFrame со столбцами `threshold`, `precision`, `recall` (все пороги кривой).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_recall_curve as _prc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_pr, _rc, _th = _prc(_d, _p)
_cv = _pd.DataFrame({'threshold': _th, 'precision': _pr[:-1], 'recall': _rc[:-1]})
_t = need('curve', _pd.DataFrame)
assert {'threshold', 'precision', 'recall'} <= set(_t.columns), f'Столбцы curve: {list(_t.columns)}. Нужны threshold, precision и recall.'
assert len(_t) == len(_cv), f'В curve {len(_t)} строк, а порогов у кривой {len(_cv)}. В precision и recall на один элемент больше — последний отбросьте: [:-1].'
_ok = _cv[_cv['recall'] >= 0.85]
_best = _ok.loc[_ok['precision'].idxmax()]
assert close(need('best_t'), round(_best['threshold'], 3)), f'best_t = {need("best_t")}, а ожидалось {round(_best["threshold"], 3)}. Оставьте строки с recall ≥ 0.85 и возьмите ту, где precision наибольшая.'
assert close(need('best_prec'), round(_best['precision'], 3)), f'best_prec = {need("best_prec")}, а ожидалось {round(_best["precision"], 3)}.'
```

### hint
`precision, recall, thresholds = precision_recall_curve(y_test, p)`, затем `pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1]})`.

### hint
Отфильтруйте `curve[curve["recall"] >= 0.85]` и возьмите строку с наибольшей точностью: `.sort_values("precision").iloc[-1]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

precision, recall, thresholds = precision_recall_curve(y_test, p)
curve = pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1]})
best = curve[curve["recall"] >= 0.85].sort_values("precision").iloc[-1]
best_t = round(best["threshold"], 3)
best_prec = round(best["precision"], 3)
```

### explain
Чтобы поймать 85 % уходящих, порог приходится опускать примерно до 0.3, и тогда по адресу попадает лишь около 60 % бонусов. План по полноте всегда оплачивается точностью.

## task: roc-plot | Нарисовать ROC-кривую | base

Нарисуйте ROC-кривую леса на тесте: первая линия на графике — сама кривая (`fpr` по X, `tpr` по Y), вторая — диагональ от (0, 0) до (1, 1). Подпишите оси (любой текст) и дайте заголовок, в котором есть слово `ROC`. Сохраните `auc` — ROC-AUC леса на тесте (3 знака).

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import roc_curve as _rc, roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_f, _t, _ = _rc(_d, _p)
ax = ax_of()
assert len(ax.lines) >= 2, f'На графике линий: {len(ax.lines)}. Нужны две: ROC-кривая и диагональ.'
_l = ax.lines[0]
_lx, _ly = _np.asarray(_l.get_xdata(), dtype=float), _np.asarray(_l.get_ydata(), dtype=float)
assert len(_lx) == len(_f) and _np.allclose(_lx, _f) and _np.allclose(_ly, _t), 'Первая линия — не ROC-кривая леса. Рисуйте ax.plot(fpr, tpr): сначала FPR, потом TPR.'
_dx, _dy = _np.asarray(ax.lines[1].get_xdata(), dtype=float), _np.asarray(ax.lines[1].get_ydata(), dtype=float)
assert _np.allclose([_dx[0], _dy[0], _dx[-1], _dy[-1]], [0, 0, 1, 1]), 'Вторая линия должна идти из (0, 0) в (1, 1): ax.plot([0, 1], [0, 1]).'
assert ax.get_xlabel() and ax.get_ylabel(), 'Подпишите обе оси: set_xlabel и set_ylabel.'
assert 'ROC' in ax.get_title(), f'Заголовок «{ax.get_title()}» — в нём должно быть слово ROC.'
assert close(need('auc'), round(_auc(_d, _p), 3)), f'auc = {need("auc")}, а ожидалось {round(_auc(_d, _p), 3)}. roc_auc_score получает вероятности, не ответы predict.'
```

### hint
`fpr, tpr, thresholds = roc_curve(y_test, p)`, затем `fig, ax = plt.subplots()` и `ax.plot(fpr, tpr)`.

### hint
Диагональ: `ax.plot([0, 1], [0, 1], linestyle="--")`. AUC: `round(roc_auc_score(y_test, p), 3)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]

fpr, tpr, thresholds = roc_curve(y_test, p)
fig, ax = plt.subplots(figsize=(4.5, 4.5))
ax.plot(fpr, tpr)
ax.plot([0, 1], [0, 1], color="grey", linestyle="--")
ax.set_xlabel("FPR")
ax.set_ylabel("TPR")
ax.set_title("ROC-кривая леса")
auc = round(roc_auc_score(y_test, p), 3)
```

### explain
Каждая точка ROC-кривой — один порог: по X доля ложных тревог среди оставшихся гостей (FPR), по Y доля найденных уходящих (TPR). `roc_curve` сама перебирает все пороги, поэтому для графика достаточно передать вероятности, а не готовые метки. Диагональ — модель, которая угадывает наугад: она находит уходящих ровно в той же доле, в какой ложно тревожит. Кривая леса идёт заметно выше диагонали. AUC = 0.913 — площадь под кривой; её можно читать так: случайно взятый уходящий гость получит от модели больший риск, чем случайный остающийся, примерно в 91 % пар.

## task: three-auc | Три модели по AUC | base

Сравните три модели по ROC-AUC на тесте: базовую `DummyClassifier(strategy="most_frequent")` из урока «Матрица ошибок», `LogisticRegression(max_iter=2000)` и `RandomForestClassifier(n_estimators=100, random_state=0)`. Сохраните `auc_dummy`, `auc_lr`, `auc_rf` (3 знака) и в `best` — строку `"dummy"`, `"lr"` или `"rf"` — у какой модели AUC выше.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
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
from sklearn.dummy import DummyClassifier as _DC
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = {}
for _k, _m in [('dummy', _DC(strategy='most_frequent')), ('lr', _LR(max_iter=2000)), ('rf', _RF(n_estimators=100, random_state=0))]:
    _w[_k] = round(_auc(_d, _m.fit(_a, _c).predict_proba(_b)[:, 1]), 3)
assert close(need('auc_dummy'), _w['dummy']), f'auc_dummy = {need("auc_dummy")}, а ожидалось {_w["dummy"]}. У базовой модели все вероятности одинаковые — какой тогда порядок?'
assert close(need('auc_lr'), _w['lr']), f'auc_lr = {need("auc_lr")}, а ожидалось {_w["lr"]}. Берите predict_proba(...)[:, 1], а не predict.'
assert close(need('auc_rf'), _w['rf']), f'auc_rf = {need("auc_rf")}, а ожидалось {_w["rf"]}.'
_bw = max(_w, key=_w.get)
assert need('best') == _bw, f'best = {need("best")!r}, а лучшая по AUC модель — другая. Сравните три числа.'
```

### hint
Для каждой модели: `.fit(X_train, y_train).predict_proba(X_test)[:, 1]` → `roc_auc_score(y_test, ...)`. У `DummyClassifier` тоже есть `predict_proba`.

### hint
`best` можно выбрать через словарь: `max(aucs, key=aucs.get)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

models = {
    "dummy": DummyClassifier(strategy="most_frequent"),
    "lr": LogisticRegression(max_iter=2000),
    "rf": RandomForestClassifier(n_estimators=100, random_state=0),
}
aucs = {}
for name, m in models.items():
    p = m.fit(X_train, y_train).predict_proba(X_test)[:, 1]
    aucs[name] = round(roc_auc_score(y_test, p), 3)
auc_dummy, auc_lr, auc_rf = aucs["dummy"], aucs["lr"], aucs["rf"]
best = max(aucs, key=aucs.get)
```

### explain
У базовой модели AUC ровно 0.5: она всем выдаёт одну и ту же вероятность, все пары — ничьи. Accuracy у неё 0.78, а ранжировать она не умеет вовсе. Лес и логистическая регрессия близки, у леса чуть выше.

## task: pairs | AUC через пары | plus

Посчитайте ROC-AUC леса на тесте **без** `roc_auc_score` — по определению через пары. Переберите **все** пары «ушедший гость — оставшийся гость»: пара засчитывается за 1, если оценка ушедшего выше, и за 0.5, если оценки равны. Сохраните `n_pairs` — число пар, `auc_pairs` — долю «выигранных» пар (3 знака). Для сверки сохраните `auc_sk` — то же через `roc_auc_score` (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]
left = p[y_test == 1]
stayed = p[y_test == 0]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p = _RF(n_estimators=100, random_state=0).fit(_a, _c).predict_proba(_b)[:, 1]
_w = round(_auc(_d, _p), 3)
_n = int((_d == 1).sum()) * int((_d == 0).sum())
assert int(need('n_pairs')) == _n, f'n_pairs = {need("n_pairs")}, а ожидалось {_n}: ушедших × оставшихся.'
assert close(need('auc_sk'), _w), f'auc_sk = {need("auc_sk")}, а ожидалось {_w}.'
assert calls('roc_auc_score') <= 1, 'roc_auc_score вызван больше одного раза — используйте его только для auc_sk, а auc_pairs считайте через пары.'
assert close(need('auc_pairs'), _w), f'auc_pairs = {need("auc_pairs")}, а ожидалось {_w}. Проверьте, что ничьи засчитаны за 0.5 и делите на число пар.'
```

### hint
Два вложенных цикла: `for a in left: for b in stayed:` — и счётчик: `+1`, если `a > b`, `+0.5`, если `a == b`.

### hint
Пар `len(left) * len(stayed)` — около 62 тысяч, цикл справится за пару секунд.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
p = RandomForestClassifier(n_estimators=100, random_state=0).fit(X_train, y_train).predict_proba(X_test)[:, 1]
left = p[y_test == 1]
stayed = p[y_test == 0]

wins = 0
for a in left:
    for b in stayed:
        if a > b:
            wins += 1
        elif a == b:
            wins += 0.5
n_pairs = len(left) * len(stayed)
auc_pairs = round(wins / n_pairs, 3)
auc_sk = round(roc_auc_score(y_test, p), 3)
```

### explain
Числа совпали до третьего знака: площадь под ROC-кривой и доля верно упорядоченных пар — одно и то же. Без ничьих вышло бы чуть меньше: у леса из 100 деревьев одинаковые оценки встречаются часто.
