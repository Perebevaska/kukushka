---
title: Объяснить модель бизнесу
lead: "Директор по лояльности спрашивает: «Почему модель считает, что этот гость уйдёт? И от чего уход вообще зависит?» Учимся отвечать на оба вопроса — о модели в целом и об одном гостевом прогнозе — и не выдавать связь за причину. Справедливость модели по группам гостей — в следующем уроке."
files: [guests_churn.csv]
recap:
  - "Два вопроса — два инструмента: «от чего зависит прогноз в целом» (глобальное объяснение) и «почему такой прогноз у этого гостя» (локальное)."
  - "Зависимость прогноза от признака (partial dependence): всем гостям ставим одно значение признака, считаем средний прогноз, повторяем для сетки значений."
  - "У логистической регрессии на масштабированных признаках вклад признака в оценку гостя = вес × (значение − среднее) / стандартное отклонение."
  - "«Что если» (what-if): меняем признак у конкретных гостей и смотрим, как меняется прогноз модели."
  - "Модель показывает связи, а не причины. «Если гость установит приложение, риск упадёт» — гипотеза для эксперимента, а не вывод модели."
  - "Объяснение для бизнеса — 2–3 понятные причины словами, без весов и логитов."
---

## Два разных вопроса

О модели спрашивают двумя способами:

- **глобально** — «от чего вообще зависит уход?» Ответ — про всех гостей сразу: какие признаки важны и как прогноз меняется вместе с ними;
- **локально** — «почему у гостя G-11606 риск 98 %?» Ответ — про одного гостя.

Важность признаков (`feature_importances_`, `permutation_importance` из главы 7) отвечает только на часть первого вопроса: **насколько** признак важен, но не **как** он влияет. Для «как» нужен другой инструмент.

::: quiz
Важность признака «давность визита» в лесу — самая высокая. Что из этого следует?

- [x] Модель чаще всего опирается на давность, но направление и форму связи показывает частичная зависимость
  > Важность отвечает на вопрос «насколько признак нужен модели», а не «как он влияет». Для формы связи строят кривую.
- [ ] Чем больше давность, тем выше риск — всегда
  > Важность не говорит о направлении. Его показывают кривые зависимости и вклады.
- [ ] Если снизить давность у гостя, он не уйдёт
  > Это причинный вывод: модель показывает связь в данных, а не результат вмешательства.
- [ ] Остальные признаки можно удалить
  > Остальные тоже что-то дают. Удаление проверяют по качеству на валидации.
:::

## Как прогноз зависит от признака

Идея простая. Возьмём всех гостей теста и сделаем вид, что все они не были у нас ровно 0 дней. Посчитаем средний прогноз. Потом — что все не были 7 дней, 14, 30 и так далее. Получим кривую «давность → средний риск». Это **частичная зависимость** (partial dependence): влияние одного признака при реальных значениях всех остальных.

::: figure pd-steps
Одна точка кривой на трёх гостях: в копии таблицы всем ставим 30 дней, остальные признаки не трогаем, усредняем прогноз. Повторяем для каждого значения сетки — получаем кривую.
:::

::: tip Аналогия
Представьте, что в кассовой программе у всех вчерашних чеков разом поменяли одну строку — «гость пришёл в 8 утра» — и попросили программу пересчитать прогноз выручки. Всё остальное в чеках настоящее, меняется только одна ручка. Частичная зависимость делает то же с моделью: крутит один признак и смотрит, куда в среднем уходит прогноз. Только пересчитывает модель, а не жизнь — настоящие гости в 8 утра могли бы и вести себя иначе.
:::

```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)

grid = [0, 7, 14, 30, 45, 60, 90, 120, 180]
risk = []
for v in grid:
    X_v = X_test.copy()
    X_v["days_since_last"] = v           # всем гостям одно и то же значение
    risk.append(forest.predict_proba(X_v)[:, 1].mean())

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(grid, risk, marker="o")
ax.set_xlabel("дней с последнего визита")
ax.set_ylabel("средний прогноз ухода")
plt.show()
```

**Что здесь происходит:**

- `grid` — значения давности, в которых считаем кривую. Брать каждый день не нужно: 9 точек хватает, чтобы увидеть форму.
- `X_v = X_test.copy()` — копия на каждом шаге: исходные признаки должны остаться нетронутыми.
- `X_v["days_since_last"] = v` — у всех 600 гостей одна и та же давность, все остальные признаки — их собственные.
- `.mean()` — средний прогноз по 600 гостям: одна точка кривой.

По-аналитически это эксперимент «при прочих равных», только проведённый над моделью, а не над гостями.

Кривая читается сразу: до двух недель риск почти не растёт (14–18 %), между 14 и 30 днями — скачок до 38 %, дальше рост замедляется и выходит на 50 %. Для бизнеса это конкретная подсказка: **окно для удерживающего касания — третья-четвёртая неделя без визита**.

::: note
В sklearn есть готовые `sklearn.inspection.partial_dependence` и `PartialDependenceDisplay` — они делают то же самое и умеют рисовать. Мы считаем руками, чтобы было видно, что внутри нет магии.
:::

Тем же способом для других признаков:

| признак | значение → средний прогноз |
|---|---|
| `complaints` | 0 → 0.19, 1 → 0.57 |
| `tenure_months` | 1–2 → 0.47, 3 → 0.42, 4 и больше → 0.21–0.23 |
| `app` | 0 → 0.24, 1 → 0.22 |

Жалоба утраивает прогноз, первые три месяца в программе — вдвое опаснее остальных, а приложение для леса почти ничего не значит.

::: warn
Частичная зависимость — про **модель**, а не про мир. «Если бы у гостя не было жалобы, модель дала бы риск ниже» — верно. «Если мы решим жалобу, гость не уйдёт» — гипотеза: возможно, жалобщики уходят не из-за жалобы, а из-за того, что вызвало жалобу (например, плохой доставки). Проверить это может только эксперимент.
:::

{{practice: pd-one, p-pd, pd-tenure, pd-two}}

## Почему у этого гостя такой риск

Для одного гостя проще всего объяснять логистическую регрессию. Вспомним главу 6: модель складывает оценку z = свободный член + Σ вес × признак и превращает её в вероятность сигмоидой. Если признаки масштабированы (`StandardScaler`, глава 7), каждое слагаемое — **вклад признака**: насколько этот признак у гостя сдвигает оценку относительно «среднего гостя».

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)

scaler, lr = logit[0], logit[-1]
guest = X_test.loc[1605]                              # индекс 1605 в файле = guest_id G-11606 (нумерация с G-10001)
z = (guest - scaler.mean_) / scaler.scale_            # признаки гостя в «стандартных отклонениях»
contrib = pd.Series(z * lr.coef_[0], index=X.columns).sort_values(ascending=False)
print("риск:", round(float(logit.predict_proba(X_test.loc[[1605]])[0, 1]), 3))
print(contrib.round(2).head(4))
```

- `logit[0]` и `logit[-1]` — первый и последний шаги конвейера: масштаб и сама регрессия.
- `scaler.mean_` и `scaler.scale_` — средние и стандартные отклонения, которые масштаб запомнил на обучении.
- `X_test.loc[1605]` — гость по **индексу** таблицы (номер строки в исходном файле), а не по позиции в тесте.
- `z * lr.coef_[0]` — вклад каждого признака; сумма всех вкладов плюс свободный член — это оценка гостя до сигмоиды.

### Разберём вместе: вклад руками

Проверим три главных вклада вручную. Нужны четыре числа на признак: значение у гостя, среднее и разброс на обучении (из масштаба) и вес.

| признак | у гостя | среднее | разброс | вес | z = (знач. − ср.) / разброс | вклад = z × вес |
|---|---|---|---|---|---|---|
| `complaints` | 1 | 0.091 | 0.290 | +0.95 | (1 − 0.091) / 0.290 = 3.13 | **+2.97** |
| `days_since_last` | 66 | 20.4 | 35.4 | +1.24 | (66 − 20.4) / 35.4 = 1.29 | **+1.59** |
| `visits_90d` | 3 | 6.36 | 5.09 | −0.74 | (3 − 6.36) / 5.09 = −0.66 | **+0.49** |

Обратите внимание на последнюю строку: вес отрицательный (чем больше визитов, тем ниже риск), значение ниже среднего — минус на минус даёт **плюс**. Мало визитов повышает риск.

Главные вклады: жалоба (+3.0), 66 дней без визита (+1.6), всего 3 визита за квартал (+0.5). Это и есть ответ директору, переведённый на человеческий язык:

> Риск ухода очень высокий (98 %). Главные причины: жалоба, больше двух месяцев без визитов и редкие визиты до этого.

::: figure contrib-guest
Оценка гостя G-11606 по слагаемым: свободный член — это «средний гость» (риск около 15 %), дальше каждый признак добавляет свой вклад. Сумма 4.17 после сигмоиды даёт 98 %.
:::

::: tip Аналогия
Это как чек за такси: базовый тариф плюс строки «ночь», «пробка», «багаж». По строкам видно, за что вы заплатили больше обычного. Вклады — те же строки чека, только для оценки риска. Одно отличие: итог чека — сама сумма, а оценка риска потом проходит через сигмоиду. Поэтому +1 к оценке «среднего» гостя заметно двигает вероятность, а гостю, у которого риск уже 98 %, почти ничего не добавляет.
:::

::: tip
Для леса и бустинга вклады считают методом SHAP (библиотека `shap`). Идея та же — разложить прогноз на вклады признаков, — но расчёт сложнее. В браузере этой библиотеки нет; на своём компьютере её стоит попробовать.

Здесь кривые частичной зависимости мы строили для леса, а карточку гостя — по логистической регрессии, потому что её вклады считаются на калькуляторе. В рабочем отчёте так делать не стоит: директор спросит, почему риск 98 %, если в отчёте лес. Прогноз и объяснение должны быть от одной модели — либо карточку считают по той же регрессии, которой и отбирают гостей, либо для леса используют SHAP.
:::

::: quiz
Почему, объясняя прогноз конкретного гостя, смотрят на вклад признака — вес × (значение − среднее) / разброс, — а не просто на вес?

- [x] Вес одинаков для всех гостей, а вклад учитывает, насколько признак у этого гостя отличается от среднего: при среднем значении вклад около нуля при любом весе
  > Вес — свойство модели, вклад — свойство пары «модель + гость». На вопрос «почему у него такой риск» отвечает вклад.
- [ ] У каждого гостя модель подбирает свои веса
  > Веса логистической регрессии общие — их выучили один раз на обучении.
- [ ] Вклад — это вероятность ухода из-за этого признака
  > Вклады измеряются в единицах оценки до сигмоиды, а не в вероятностях; складываются именно они, а не проценты.
- [ ] Так считать быстрее, чем смотреть на веса
  > Скорость тут ни при чём: вопрос в том, что именно объясняет число.
:::

::: warn Линейная модель на краях
Логистическая регрессия линейна в логите: она продолжает прямую и на краях данных преувеличивает. По таблице выше вклад давности — (дни − 20.4) / 35.4 × 1.24: 96 дней без визита дают +2.6, а 192 дня — уже +6.0, больше чем вдвое. Если всем 600 гостям теста поставить 90 дней, средний прогноз регрессии 0.62, а 180 дней — 0.96. Лес на тех же гостях выходит на «полку»: 0.48 при 90 днях и 0.51 при 180 (кривая из первого раздела урока). Кто прав, данные почти не говорят: гостей с давностью больше 180 дней в обучении всего 21 из 1 800. Если модели расходятся на крайних значениях, проверьте, сколько таких гостей было в обучении.
:::

{{practice: coefs, contrib-hand, guest-card, top-guest, sum-check}}

## Что если

Самый понятный бизнесу приём — **что если**: меняем признак у реальных гостей и смотрим на прогноз. Возьмём гостей теста с жалобой и долей доставки выше 40 % и «уберём» жалобу:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)

group = X_test[(X_test["complaints"] > 0) & (X_test["delivery_share"] > 0.4)]
fixed = group.copy()
fixed["complaints"] = 0
print("гостей:", len(group))
print("прогноз сейчас:", round(float(forest.predict_proba(group)[:, 1].mean()), 3))
print("прогноз без жалобы:", round(float(forest.predict_proba(fixed)[:, 1].mean()), 3))
print("факт:", round(float(y_test[group.index].mean()), 3))
```

**Что здесь происходит:**

- `group` — реальные гости с жалобой и большой долей доставки; на них и задаём вопрос.
- `fixed = group.copy()` и `fixed["complaints"] = 0` — те же гости, но «без жалобы». Всё остальное у них прежнее.
- Сравниваем средний прогноз до и после, а для справки — фактическую долю ушедших.

16 гостей, модель даёт им в среднем 65 %, ушли 94 %. Без жалобы — 13 %. Это сильный аргумент, чтобы **проверить** гипотезу «быстрое решение жалоб на доставку удерживает гостей» экспериментом: половине жалобщиков — компенсация в тот же день, половине — как обычно.

::: predict
```python static
import pandas as pd
X = pd.DataFrame({"days": [3, 40, 90]})
X_v = X.copy()
X_v["days"] = 30
print(X["days"].tolist(), X_v["days"].tolist())
```

- `[30, 30, 30] [30, 30, 30]`
- [x] `[3, 40, 90] [30, 30, 30]`
- `[3, 40, 90] [3, 40, 90]`

Почему: `copy()` создаёт независимую таблицу. Без неё мы бы испортили исходные признаки — частая ошибка при расчёте частичной зависимости.
:::

::: predict
```python static
value, mean, scale, coef = 10, 30, 20, 0.8
print(round((value - mean) / scale * coef, 2))
```

- `0.8`
- [x] `-0.8`
- `-16.0`

Почему: гость на одно стандартное отклонение ниже среднего (z = −1), вес положительный — вклад −0.8: этот признак **снижает** риск гостя относительно среднего.
:::

::: warn Типичные ошибки
- **Меняют `X_test` без копии.** После первой точки сетки все признаки испорчены, и остальные точки считаются по чужим данным.
- **Сравнивают веса без масштаба.** Вес 0.01 у «бюджета в рублях» и 1.5 у флага «жалоба» несравнимы; сравнивают веса на масштабированных признаках.
- **`loc` и `iloc`.** `X_test.loc[1605]` — гость с индексом 1605; `X_test.iloc[1605]` — 1606-я строка теста, которой нет (в тесте 600 строк).
- **Невозможные комбинации.** Частичная зависимость ставит «3 дня без визита» и гостю с нулём визитов за квартал. Модель отвечает, но о таких гостях она ничего не знает — читайте края кривой осторожно.
- **Связь = причина.** «Без жалобы риск 13 %» — свойство модели, а не обещание результата.
:::

{{practice: what-if-app}}

## Практика

## task: pd-one | Одна точка кривой | warmup

Поставьте всем гостям теста `days_since_last = 30` и сохраните средний прогноз леса в `risk_30` (3 знака). Исходную таблицу `X_test` не меняйте.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
f = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c)
assert (need('X_test')['days_since_last'] == b['days_since_last']).all(), 'X_test изменилась — работайте с копией: X_v = X_test.copy().'
bv = b.copy(); bv['days_since_last'] = 30
w = round(f.predict_proba(bv)[:, 1].mean(), 3)
assert close(need('risk_30'), w), f'risk_30 = {need("risk_30")}, а нужно {w}.'
```

### hint
Измените не `X_test`, а его копию — в условии сказано, что исходная таблица должна остаться прежней.

### hint
`X_v = X_test.copy()`, `X_v["days_since_last"] = 30`, `forest.predict_proba(X_v)[:, 1].mean()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)

X_v = X_test.copy()
X_v["days_since_last"] = 30
risk_30 = round(forest.predict_proba(X_v)[:, 1].mean(), 3)
```

## task: contrib-hand | Вклад на калькуляторе | warmup

Повторите таблицу из «Разберём вместе» для гостя с 12 визитами за квартал (`visits_90d`): среднее 6.36, разброс 5.09, вес −0.74. Сохраните `z` и `contrib` (2 знака) и `direction` — `"повышает"` или `"снижает"` риск.

### starter
```python
value, mean, scale, coef = 12, 6.36, 5.09, -0.74

```

### check
```python
assert close(need('z'), round((12 - 6.36) / 5.09, 2), 0.011), f'z = {need("z")}. z = (значение − среднее) / разброс.'
assert close(need('contrib'), round((12 - 6.36) / 5.09 * -0.74, 2), 0.011), f'contrib = {need("contrib")}. Вклад = z × вес.'
assert need('direction') == 'снижает', f'direction = {need("direction")!r}. Вклад отрицательный — риск ниже среднего.'
```

### hint
z = (12 − 6.36) / 5.09 — гость на сколько разбросов выше среднего.

### hint
`contrib = round(z * coef, 2)`; если вклад меньше нуля — признак снижает риск.

### solution
```python
value, mean, scale, coef = 12, 6.36, 5.09, -0.74
z = round((value - mean) / scale, 2)
contrib = round((value - mean) / scale * coef, 2)
direction = "повышает" if contrib > 0 else "снижает"
```

### explain
z ≈ 1.11: визитов больше среднего на один разброс. Вес отрицательный, значит, вклад −0.82 — частые визиты снижают риск. У G-11606 тот же признак давал +0.49: знак вклада зависит не только от веса, но и от того, по какую сторону от среднего гость.

## task: p-pd | Функция частичной зависимости | warmup

Соберите функцию, которая возвращает список средних прогнозов для сетки значений признака.

### parsons
```python
def partial(model, X, col, grid):
    out = []
    for v in grid:
        X_v = X.copy()
        X_v[col] = v
        out.append(round(float(model.predict_proba(X_v)[:, 1].mean()), 3))
    return out
```

### check
```python
import pandas as _pd
class _M:
    def predict_proba(self, X):
        import numpy as np
        p = (X['a'].values / 10).clip(0, 1)
        return np.c_[1 - p, p]
f = need('partial')
X0 = _pd.DataFrame({'a': [1, 5, 9]})
assert f(_M(), X0, 'a', [0, 5, 10]) == [0.0, 0.5, 1.0], f'partial вернула {f(_M(), X0, "a", [0, 5, 10])}.'
assert list(X0['a']) == [1, 5, 9], 'Функция испортила исходную таблицу — копия должна создаваться внутри цикла.'
```

### hint
Копия создаётся для каждого значения сетки, внутри цикла.

### hint
После `for` — копия, затем присваивание признаку, затем `append` среднего прогноза. `return` — после цикла.

## task: pd-tenure | Новички | base

С помощью частичной зависимости по `tenure_months` для сетки `[1, 2, 3, 4, 6, 12, 24]` сохраните список средних прогнозов `pd_tenure` (3 знака) и в `newbie_ratio` — во сколько раз прогноз при 2 месяцах больше прогноза при 12 (2 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
grid = [1, 2, 3, 4, 6, 12, 24]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
f = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c)
w = []
for v in [1, 2, 3, 4, 6, 12, 24]:
    bv = b.copy(); bv['tenure_months'] = v; w.append(round(f.predict_proba(bv)[:, 1].mean(), 3))
got = [round(float(x), 3) for x in need('pd_tenure')]
assert got == w, f'pd_tenure = {got}, а нужно {w}.'
assert close(need('newbie_ratio'), round(w[1] / w[5], 2)), f'newbie_ratio = {need("newbie_ratio")}: прогноз при 2 / прогноз при 12.'
```

### hint
Цикл из теории с признаком `tenure_months`. Значения 2 и 12 стоят на позициях 1 и 5 сетки.

### hint
Отношение — `risk[1] / risk[5]`; округляйте в самом конце.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
grid = [1, 2, 3, 4, 6, 12, 24]

pd_tenure = []
for v in grid:
    X_v = X_test.copy()
    X_v["tenure_months"] = v
    pd_tenure.append(round(forest.predict_proba(X_v)[:, 1].mean(), 3))
newbie_ratio = round(pd_tenure[1] / pd_tenure[5], 2)
```

### explain
Новичок в программе для модели примерно вдвое рискованнее «старожила». Граница — между 3 и 4 месяцами. Для бизнеса это идея отдельного сценария приветствия на первые три месяца.

## task: coefs | Веса для людей | base

Обучите `make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))` и сохраните Series весов `w` с индексом — названиями признаков. В `top_up` сохраните список трёх признаков с самыми большими положительными весами (по убыванию), а в `top_down` — трёх с самыми отрицательными (от самого отрицательного).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
ww = _pd.Series(_mp(_SS(), _LR(max_iter=1000)).fit(a, c)[-1].coef_[0], index=X.columns)
w = need('w', _pd.Series)
assert set(w.index) == set(X.columns), 'Индекс w — названия признаков X.columns.'
assert all(close(w[k], ww[k], 0.01) for k in X.columns), 'Веса не совпадают с ожидаемыми — масштаб и регрессия в одном конвейере?'
assert list(need('top_up')) == list(ww.sort_values(ascending=False).index[:3]), f'top_up = {need("top_up")}.'
assert list(need('top_down')) == list(ww.sort_values().index[:3]), f'top_down = {need("top_down")}.'
```

### hint
Веса — `model[-1].coef_[0]`; превратите в Series с `index=X.columns` и отсортируйте.

### hint
Положительный вес — признак повышает риск, отрицательный — снижает. Отсортируйте веса один раз по убыванию и один раз по возрастанию: сверху окажутся признаки, сильнее всего повышающие и снижающие риск.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
w = pd.Series(logit[-1].coef_[0], index=X.columns)
top_up = list(w.sort_values(ascending=False).index[:3])
top_down = list(w.sort_values().index[:3])
```

### explain
Риск повышают давность визита, жалобы и доля доставки, снижают — частые визиты, приложение и использованные промокоды. Веса масштабированных признаков сравнимы между собой: это изменение оценки при росте признака на одно стандартное отклонение.

## task: guest-card | Карточка гостя | base

Для гостя с индексом 1605 (G-11606) посчитайте вклады признаков в оценку логистической регрессии: (значение − среднее) / стандартное отклонение × вес. Сохраните Series `contrib` (индекс — признаки) и строку `card` вида `"риск 98%: complaints, days_since_last, visits_90d"` — риск в целых процентах и три признака с наибольшим положительным вкладом через запятую.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
m = _mp(_SS(), _LR(max_iter=1000)).fit(a, c)
z = (b.loc[1605] - m[0].mean_) / m[0].scale_
cc = _pd.Series(z * m[-1].coef_[0], index=X.columns)
ct = need('contrib', _pd.Series)
assert all(close(ct[k], cc[k], 0.01) for k in X.columns), 'Вклады не совпадают: (значение − mean_) / scale_ × coef_.'
pr = round(m.predict_proba(b.loc[[1605]])[0, 1] * 100)
want = f'риск {pr}%: ' + ', '.join(cc.sort_values(ascending=False).index[:3])
assert need('card') == want, f'card = {need("card")!r}, а нужно {want!r}.'
```

### hint
Как в теории: `scaler, lr = logit[0], logit[-1]`. Риск: `logit.predict_proba(X_test.loc[[1605]])[0, 1]` — двойные скобки, чтобы получилась таблица из одной строки.

### hint
Строка: `f"риск {round(p * 100)}%: " + ", ".join(top3)`.

### hint
Три признака с наибольшим вкладом — `contrib.sort_values(ascending=False).index[:3]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)

scaler, lr = logit[0], logit[-1]
guest = X_test.loc[1605]
contrib = pd.Series((guest - scaler.mean_) / scaler.scale_ * lr.coef_[0], index=X.columns)
p = logit.predict_proba(X_test.loc[[1605]])[0, 1]
top3 = contrib.sort_values(ascending=False).index[:3]
card = f"риск {round(p * 100)}%: " + ", ".join(top3)
```

### explain
Карточка — заготовка для CRM: менеджер видит не «0.98», а «риск 98 %: жалоба, давность, мало визитов». Названия признаков стоит заменить словами («была жалоба», «66 дней без визита») — для этого достаточно словаря-переводчика.

## task: top-guest | Самый рискованный гость | base

Найдите в тесте гостя с наибольшим прогнозом логистической регрессии. Сохраните его индекс `top_idx`, риск `top_risk` (3 знака), Series вкладов `contrib` и `top3` — список трёх признаков с наибольшим вкладом. В `days_contrib` — вклад `days_since_last` (2 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
m = _mp(_SS(), _LR(max_iter=1000)).fit(a, c)
pr = _pd.Series(m.predict_proba(b)[:, 1], index=b.index); ti = pr.idxmax()
cc = _pd.Series((b.loc[ti] - m[0].mean_) / m[0].scale_ * m[-1].coef_[0], index=X.columns)
assert need('top_idx') == ti, f'top_idx = {need("top_idx")}, а нужно {ti}. Индекс таблицы, а не позиция.'
assert close(need('top_risk'), round(pr[ti], 3)), f'top_risk = {need("top_risk")}.'
assert list(need('top3')) == list(cc.sort_values(ascending=False).index[:3]), f'top3 = {need("top3")}, а нужно {list(cc.sort_values(ascending=False).index[:3])}.'
assert close(need('days_contrib'), round(cc['days_since_last'], 2), 0.011), f'days_contrib = {need("days_contrib")}.'
```

### hint
Прогнозы в Series с индексом теста: `risk = pd.Series(logit.predict_proba(X_test)[:, 1], index=X_test.index)`, затем `risk.idxmax()`.

### hint
Вклады — как в теории, только для `X_test.loc[top_idx]`. `top3 = list(contrib.sort_values(ascending=False).index[:3])`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)

risk = pd.Series(logit.predict_proba(X_test)[:, 1], index=X_test.index)
top_idx = risk.idxmax()
top_risk = round(risk[top_idx], 3)
scaler, lr = logit[0], logit[-1]
contrib = pd.Series((X_test.loc[top_idx] - scaler.mean_) / scaler.scale_ * lr.coef_[0], index=X.columns)
top3 = list(contrib.sort_values(ascending=False).index[:3])
days_contrib = round(contrib["days_since_last"], 2)
```

### explain
Это гость G-12165: 192 дня без визита, ноль визитов за квартал, Тюмень, нет приложения. Риск 99.5 %, и почти весь он — от давности: вклад +6.0. Здесь видна особенность линейной модели: она продолжает прямую, и 192 дня дают вклад больше чем вдвое выше, чем 96. Лес на кривой частичной зависимости, наоборот, выходит на «полку» около 50 %. Для объяснения это не страшно, но если модели расходятся в крайних значениях, стоит посмотреть, сколько таких гостей было в обучении.

## task: sum-check | Вклады складываются в прогноз | plus

Проверьте, что объяснение «честное»: свободный член плюс сумма вкладов гостя 1605 равны оценке z, а сигмоида от неё — прогнозу модели. Сохраните `z` (свободный член + сумма вкладов), `p_manual` = 1 / (1 + e^(−z)) и `p_model` — прогноз `predict_proba` (оба 4 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
scaler, lr = logit[0], logit[-1]
contrib = (X_test.loc[1605] - scaler.mean_) / scaler.scale_ * lr.coef_[0]

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.pipeline import make_pipeline as _mp
from sklearn.preprocessing import StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
m = _mp(_SS(), _LR(max_iter=1000)).fit(a, c)
zz = m[-1].intercept_[0] + ((b.loc[1605] - m[0].mean_) / m[0].scale_ * m[-1].coef_[0]).sum()
assert close(need('z'), zz, 0.01), f'z = {need("z")}, а нужно {round(zz, 3)}: intercept_[0] + сумма вкладов.'
pm = round(1 / (1 + _np.exp(-zz)), 4)
assert close(need('p_manual'), pm, 0.0002), f'p_manual = {need("p_manual")}, а нужно {pm}.'
assert close(need('p_model'), round(m.predict_proba(b.loc[[1605]])[0, 1], 4), 0.0002), f'p_model = {need("p_model")}.'
```

### hint
Свободный член — `lr.intercept_[0]`. Сигмоида: `1 / (1 + np.exp(-z))`.

### hint
Оценка гостя — `lr.intercept_[0] + contrib.sum()`; её сигмоида должна совпасть с `predict_proba`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
scaler, lr = logit[0], logit[-1]
contrib = (X_test.loc[1605] - scaler.mean_) / scaler.scale_ * lr.coef_[0]

z = lr.intercept_[0] + contrib.sum()
p_manual = round(1 / (1 + np.exp(-z)), 4)
p_model = round(logit.predict_proba(X_test.loc[[1605]])[0, 1], 4)
```

### explain
Совпадение до знака — это и есть главное достоинство такого объяснения: ничего не спрятано, прогноз ровно равен сумме вкладов. У леса такого простого разложения нет, поэтому для него используют SHAP.

## task: what-if-app | Что если поставить приложение | plus

Маркетинг хочет уговаривать гостей поставить приложение. Возьмите гостей теста без приложения с прогнозом леса выше 0.3, поставьте им `app = 1` и посчитайте средний прогноз до и после. Сохраните `n_group`, `before`, `after` (3 знака) и `drop_pp` — снижение в процентных пунктах (1 знак).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = pd.Series(forest.predict_proba(X_test)[:, 1], index=X_test.index)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
f = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c)
pp = _pd.Series(f.predict_proba(b)[:, 1], index=b.index)
grp = b[(b['app'] == 0) & (pp > 0.3)]
fx = grp.copy(); fx['app'] = 1
bf, af = round(f.predict_proba(grp)[:, 1].mean(), 3), round(f.predict_proba(fx)[:, 1].mean(), 3)
assert need('n_group') == len(grp), f'n_group = {need("n_group")}, а нужно {len(grp)}: app == 0 и прогноз > 0.3.'
assert close(need('before'), bf) and close(need('after'), af), f'before, after = {need("before")}, {need("after")}, а нужно {bf}, {af}.'
assert close(need('drop_pp'), round((bf - af) * 100, 1), 0.15), f'drop_pp = {need("drop_pp")}.'
```

### hint
Маска по двум условиям: `(X_test["app"] == 0) & (p > 0.3)`. Для «после» — копия с `app = 1`.

### hint
`group = X_test[mask]`, `changed = group.copy()`, `changed["app"] = 1`; средние прогнозы — `forest.predict_proba(...)[:, 1].mean()` для `group` и для `changed`. Имя `after` оставьте для числа — среднего прогноза после изменения.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
p = pd.Series(forest.predict_proba(X_test)[:, 1], index=X_test.index)

group = X_test[(X_test["app"] == 0) & (p > 0.3)]
fixed = group.copy()
fixed["app"] = 1
n_group = len(group)
before = round(forest.predict_proba(group)[:, 1].mean(), 3)
after = round(forest.predict_proba(fixed)[:, 1].mean(), 3)
drop_pp = round((before - after) * 100, 1)
```

### explain
Модель обещает снижение всего на несколько пунктов — у рискованных гостей приложение мало что меняет. И даже это не обещание: гости с приложением могут уходить реже, потому что они и так лояльнее (поэтому и поставили приложение). Если идея всё же важна бизнесу — её проверяют A/B-тестом.

## task: pd-two | Две кривые | star

Постройте частичную зависимость по давности визита (`grid = [0, 7, 14, 21, 30, 45, 60, 90]`) отдельно для новичков (`tenure_months <= 3`) и остальных гостей теста — две линии на одном графике с легендой «новички» и «остальные», ось X — `"дней с последнего визита"`. Сохраните списки `pd_new` и `pd_old` (3 знака) и в `max_gap_day` — значение сетки, при котором разница «новички − остальные» наибольшая.

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
grid = [0, 7, 14, 21, 30, 45, 60, 90]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
g = _pd.read_csv('guests_churn.csv'); y = g['churned']
X = _pd.get_dummies(g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
a, b, c, d = _tts(X, y, test_size=0.25, random_state=42, stratify=y)
f = _RF(n_estimators=100, min_samples_leaf=5, random_state=0).fit(a, c)
G = [0, 7, 14, 21, 30, 45, 60, 90]
def _pdv(part):
    out = []
    for v in G:
        pv = part.copy(); pv['days_since_last'] = v; out.append(round(f.predict_proba(pv)[:, 1].mean(), 3))
    return out
wn, wo = _pdv(b[b['tenure_months'] <= 3]), _pdv(b[b['tenure_months'] > 3])
assert [round(float(x), 3) for x in need('pd_new')] == wn, f'pd_new: ожидалось {wn}.'
assert [round(float(x), 3) for x in need('pd_old')] == wo, f'pd_old: ожидалось {wo}.'
gaps = [n - o for n, o in zip(wn, wo)]
assert need('max_gap_day') == G[gaps.index(max(gaps))], f'max_gap_day = {need("max_gap_day")}.'
ax = ax_of(0)
assert len(ax.lines) >= 2, 'На графике должно быть две линии.'
assert ax.get_xlabel() == 'дней с последнего визита', 'Подпишите ось X: «дней с последнего визита».'
labels = [t.get_text() for t in ax.get_legend().get_texts()] if ax.get_legend() else []
assert 'новички' in labels and 'остальные' in labels, f'Легенда: {labels}, нужны «новички» и «остальные».'
```

### hint
Напишите функцию, которая считает кривую для части `X_test`, и вызовите её для двух масок.

### hint
Разницы: `[n - o for n, o in zip(pd_new, pd_old)]`; позиция максимума — `.index(max(...))`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=0).fit(X_train, y_train)
grid = [0, 7, 14, 21, 30, 45, 60, 90]

def curve(part):
    out = []
    for v in grid:
        part_v = part.copy()
        part_v["days_since_last"] = v
        out.append(round(forest.predict_proba(part_v)[:, 1].mean(), 3))
    return out

pd_new = curve(X_test[X_test["tenure_months"] <= 3])
pd_old = curve(X_test[X_test["tenure_months"] > 3])
gaps = [n - o for n, o in zip(pd_new, pd_old)]
max_gap_day = grid[gaps.index(max(gaps))]

fig, ax = plt.subplots()
ax.plot(grid, pd_new, marker="o", label="новички")
ax.plot(grid, pd_old, marker="o", label="остальные")
ax.set_xlabel("дней с последнего визита")
ax.set_ylabel("средний прогноз ухода")
ax.legend()
plt.show()
```

### explain
У новичков риск высокий уже при недавнем визите, и кривая лежит выше на всей сетке. Новичков в тесте мало (около 6 %), поэтому их кривая шумнее. Вывод для бизнеса: новичкам нужно касание раньше, чем через три недели, — не дожидаясь паузы.
