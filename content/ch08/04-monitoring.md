---
title: "Модель в работе: мониторинг"
lead: "Модель приоритизации заявок из проекта главы 7 запустили в мае. Через три месяца менеджеры жалуются: «модель перестала выделять хорошие заявки». Учимся следить за моделью после запуска — по входам, выходам и качеству — находить поломку раньше, чем её заметит бизнес, и решать, когда модель переобучать. Качество по сегментам и отчёт о метрике — в следующем уроке."
files: [catering_leads.csv]
recap:
  - "После запуска модель проверяют регулярно (например, раз в месяц) по трём группам признаков здоровья: входы, выходы, качество."
  - "Входы: доли пропусков, медианы и распределения признаков, новые категории — сравнивают с обучающей выборкой."
  - "Выходы: средний прогноз и доля заявок выше порога. Резкий скачок — повод разбираться, даже если ответов ещё нет."
  - "Качество (AUC, калибровка «прогноз против факта») можно считать только когда известны ответы — часто с задержкой."
  - "AUC меряет порядок внутри месяца и может не заметить, что вероятности «уехали»: решения по порогу уже сломаны."
  - "Частая причина поломки — не мир, а данные: смена единиц измерения, формы, справочника. Проверки входов ловят её в первый же день."
  - "Переобучение на свежих данных полезно, но только после того, как найдена и исправлена причина сбоя."
---

## Модель запущена — что дальше

Обучение — только половина работы. После запуска мир и данные меняются: появляются новые каналы, меняются цены, кто-то в CRM переименовывает поле. Модель об этом не знает и продолжает уверенно выдавать прогнозы. Задача аналитика — **мониторинг**: регулярно проверять, что модель всё ещё работает.

::: tip Аналогия
Модель похожа на бариста, который выучил рецепт по весам в граммах. Если весы тихо перенастроить на унции, он продолжит уверенно отмерять «18» — и кофе испортится, хотя сам бариста ничего не забыл. Мониторинг входов — регулярно класть на весы контрольную гирьку. Где аналогия хромает: сдвиг бывает и настоящим, когда меняются сами клиенты и их привычки, — тогда весы исправны, и помогает уже переобучение модели.
:::

Возьмём заявки на кейтеринг. Модель обучим на январе–апреле, а май–сентябрь будем считать «жизнью после запуска». Конвейер — как в главе 7: пропуски чисел — медианой (`add_indicator=True` добавляет флаг «здесь был пропуск»), пропуски категорий — значением «не указан», дальше масштаб, one-hot и логистическая регрессия.

```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]

prep = make_column_transformer(
    (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
    (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                   OneHotEncoder(handle_unknown="ignore")), cat),
)
model = make_pipeline(prep, LogisticRegression(max_iter=1000))

train = d[d["month"] <= 4]
model.fit(train[num + cat], train["converted"])
print("обучение:", len(train), "заявок, конверсия", round(train["converted"].mean(), 3))
```

**Что здесь происходит:**

- `parse_dates=["created"]` — дата заявки сразу читается как дата, `.dt.month` достаёт номер месяца.
- `num` и `cat` — списки числовых и категориальных признаков; модель увидит только их.
- Числовая ветка: пропуск → медиана обучения (+ флаг «был пропуск») → масштаб. Категориальная: пропуск → «не указан» → one-hot; `handle_unknown="ignore"` — незнакомая категория станет нулями, а не ошибкой. Запомните это: ниже это свойство сыграет против нас.
- `train` — январь–апрель; всё, что запомнит модель (медианы, средние, веса), запоминается отсюда.

`make_column_transformer` и `make_pipeline` — короткие версии `ColumnTransformer` и `Pipeline` из главы 7: имена шагов они придумывают сами.

{{practice: month-col, p-monitor}}

## Качество по месяцам

Ответ (заключили договор или нет) становится известен через несколько недель. Когда он есть, считаем качество за каждый месяц: AUC, средний прогноз и фактическую конверсию.

```python
# шапка та же, что в первом примере урока «Модель в работе: мониторинг»: данные и модель на январе–апреле
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
prep = make_column_transformer(
    (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
    (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                   OneHotEncoder(handle_unknown="ignore")), cat),
)
model = make_pipeline(prep, LogisticRegression(max_iter=1000))
train = d[d["month"] <= 4]
model.fit(train[num + cat], train["converted"])

# ↓ новое в этом примере
rows = []
for m, part in d[d["month"] >= 5].groupby("month"):
    p = model.predict_proba(part[num + cat])[:, 1]
    rows.append({"month": m, "leads": len(part), "fact": part["converted"].mean(),
                 "predicted": p.mean(), "auc": roc_auc_score(part["converted"], p)})
pd.DataFrame(rows).round(3)
```

Всё спокойно: AUC держится в районе 0.82–0.86, средний прогноз (0.11–0.12) близок к фактической конверсии (0.11–0.15). Колебания от месяца к месяцу — обычный шум: в месяце всего 300–400 заявок и около 45 договоров.

::: tip
Разброс AUC между месяцами полезно сравнить с разбросом между фолдами кросс-валидации (глава 6). Если месячные колебания того же размера — это шум, а не деградация.
:::

{{practice: monthly-auc, auc-blind}}

## Поломка, которую не видно сразу

Теперь смоделируем частую историю. С августа в CRM обновили форму: поле «время ответа» стало записываться **в минутах**, а не в часах. Никто не предупредил аналитика.

```python
# шапка та же, что в первом примере урока «Модель в работе: мониторинг»: данные и модель на январе–апреле
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
prep = make_column_transformer(
    (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
    (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                   OneHotEncoder(handle_unknown="ignore")), cat),
)
model = make_pipeline(prep, LogisticRegression(max_iter=1000))
train = d[d["month"] <= 4]
model.fit(train[num + cat], train["converted"])

# ↓ новое в этом примере
live = d.copy()
aug = live["month"] >= 8
live.loc[aug, "response_hours"] = (live.loc[aug, "response_hours"] * 60).round()   # теперь минуты

for m, part in live[live["month"] >= 6].groupby("month"):
    p = model.predict_proba(part[num + cat])[:, 1]
    print(m, "средний прогноз", round(p.mean(), 3), "| выше 0.3:", round((p > 0.3).mean(), 3),
          "| AUC", round(roc_auc_score(part["converted"], p), 3))
```

**Что здесь происходит:**

- `live = d.copy()` — копия «как в продакшене»; исходная `d` нужна, чтобы потом сравнить.
- `live.loc[aug, "response_hours"] = ... * 60` — имитация сбоя: с августа то же поле в минутах.
- Модель не переобучаем: в жизни она так и работает со старыми весами и старыми средними.

С августа модель «решила», что на все заявки отвечают по 2–3 суток, — а медленный ответ в обучении означал почти гарантированный провал. Средний прогноз упал с 0.12 до 0.01, а заявок с прогнозом выше 0.3 почти не осталось: около 1 % в августе и ни одной в сентябре. Менеджеры, которые брали в работу заявки «выше порога», получили пустой список.

### Почему прогноз упал почти до нуля

Посчитаем руками, что видит модель. StandardScaler запомнил по обучению среднее `response_hours` ≈ **4.6** часа и разброс ≈ **5.4** часа. Вес логистической регрессии у масштабированного признака ≈ **−2.0** на одно стандартное отклонение.

- Ответ за 2 часа: z = (2 − 4.6) / 5.4 ≈ **−0.48** — чуть быстрее среднего, вклад в логит ≈ +1.
- Те же 2 часа, записанные как 120 минут: z = (120 − 4.6) / 5.4 ≈ **21.3** — «на 21 стандартное отклонение медленнее». Вклад в логит ≈ −43.

Разница в логите — около 44. Даже заявка с прогнозом 0.9 после такого сдвига получает вероятность порядка 10⁻¹⁸. Модель не «ошиблась» — она честно применила свою формулу к числам, смысл которых поменялся.

::: figure unit-shift
Те же два часа ответа, записанные в минутах, превращаются для модели в «на 21 стандартное отклонение медленнее среднего» — и вклад признака уносит прогноз к нулю.
:::

AUC тоже упал — до 0.65–0.71, но это бы мы узнали только через месяц-два, когда станут известны договоры. А средний прогноз и медиана `response_hours` изменились **в первый же день**.

::: figure monitor-timeline
Три группы проверок на одной оси времени. Входы и выход показывают сбой 1 августа, а качество — только когда станут известны договоры.
:::

::: warn
AUC меряет только порядок заявок внутри месяца. Если бы сбой сдвинул все прогнозы одинаково, AUC не изменился бы вовсе, а решения по порогу сломались бы полностью. Поэтому одного AUC для мониторинга мало.
:::

::: predict
```python static
import numpy as np
from sklearn.metrics import roc_auc_score
y = np.array([0, 1, 0, 1, 1])
p = np.array([0.2, 0.7, 0.4, 0.6, 0.9])
print(roc_auc_score(y, p) == roc_auc_score(y, p / 10))
```

- [x] `True`
- `False`
- ошибка

Почему: AUC зависит только от порядка прогнозов. Разделили все на 10 — порядок тот же, AUC тот же. А вот с порогом 0.3 раньше отбирались четыре заявки, а теперь ни одной.
:::

::: quiz
Ответы на заявки ещё не пришли, а модель уже месяц работает. Как заметить поломку до того, как упадёт качество?

- [x] Следить за входами и выходом: доли пропусков, медианы признаков, новые категории, средний прогноз
  > Качество можно посчитать только когда известны ответы. Сдвиг во входных данных виден сразу.
- [ ] Никак: без ответов проверить ничего нельзя
  > Без ответов нельзя посчитать AUC, но вход и выход модели видны каждый день.
- [ ] Переобучать модель каждый день на всякий случай
  > Это дорого и не ловит поломку в данных — модель переобучится на испорченных.
- [ ] Посмотреть ROC-AUC за прошлый год
  > Старое качество ничего не говорит о новых данных.
:::

{{practice: output-alarm}}

## Проверки входов

Большинство поломок видно ещё до ответов — по входным данным. Простой набор проверок на каждый месяц:

- **медианы числовых признаков** против обучения;
- **доли пропусков**;
- **новые категории**, которых не было в обучении;
- **доли категорий** (например, каналов).

```python
import pandas as pd

d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
live = d.copy()
aug = live["month"] >= 8
live.loc[aug, "response_hours"] = (live.loc[aug, "response_hours"] * 60).round()
num = ["guests", "budget_pp", "days_to_event", "response_hours"]

base = live[live["month"] <= 4][num].median()
by_month = live[live["month"] >= 5].groupby("month")[num].median()
(by_month / base).round(2)
```

::: predict
```python static
import pandas as pd
base = pd.Series({"guests": 40, "response_hours": 3})
month = pd.Series({"guests": 44, "response_hours": 180})
print((month / base).round(1).tolist())
```

- `[4.0, 177.0]`
- [x] `[1.1, 60.0]`
- `[0.9, 0.02]`

Почему: деление Series выравнивается по названиям. 44 / 40 = 1.1 — норма, 180 / 3 = 60 — ровно «минуты вместо часов».
:::

Отношение медианы к обучающей — около 1 у всех признаков, кроме `response_hours` в августе и сентябре: там она в 55–58 раз больше — ровно множитель 60 (минуты вместо часов) с поправкой на то, что состав заявок от месяца к месяцу немного другой. Такую проверку легко автоматизировать: «если отношение медиан вышло за 0.5–2 — прислать письмо».

::: deep Индекс стабильности (PSI)
Для сравнения целых распределений в банках и ритейле часто считают **PSI** (population stability index): делят признак на интервалы, считают доли в обучении (a) и в новом месяце (b) и складывают (b − a) × ln(b / a). Распространённое эмпирическое правило: меньше 0.1 — стабильно, 0.1–0.25 — заметный сдвиг, больше 0.25 — серьёзный. Пороги условные, их подбирают под свою задачу.
:::

{{practice: miss-share, median-alarm, psi}}

## Когда переобучать

Допустим, сбой нашли и исправили (перевели минуты обратно в часы). Стоит ли заодно переобучить модель на свежих данных? Сравним на августе–сентябре модель, обученную на январе–апреле, и модель, обученную на январе–июле: AUC 0.84 против 0.87. В наших данных мир не менялся — выигрыш дали просто лишние три месяца примеров.

Практичное правило:

1. сначала найти причину сбоя — модель на сломанных данных переобучать нельзя, она выучит поломку;
2. переобучать по расписанию (например, раз в квартал) на последних данных;
3. новую модель выпускать, только если на свежем отложенном месяце она не хуже старой.

::: quiz
Новая модель, переобученная на январе–июле, на своих обучающих данных даёт AUC 0.91. Старая на отложенном августе — 0.84. Аналитик предлагает заменить старую новой: «0.91 больше 0.84». Что не так?

- [x] Числа посчитаны на разных данных, и одно из них — на обучении. Нужно сравнить обе модели на одном свежем месяце, которого не видела ни одна
  > На своём обучении любая модель выглядит лучше, чем есть, а разные выборки делают сравнение бессмысленным. Честно — один и тот же отложенный месяц для обеих.
- [ ] Ничего: 0.91 заметно больше 0.84, модель лучше
  > Разница может быть целиком переобучением: на новых заявках 0.91 может превратиться в те же 0.84 или меньше.
- [ ] Нужно сравнивать не AUC, а точность
  > Метрика тут ни при чём — дело в том, на каких данных её посчитали.
- [ ] Новую модель выпускать нельзя: свежие данные могут быть сломаны
  > Проверить данные действительно нужно (минуты вместо часов!), но это не повод отказаться от переобучения. Повод — если на честном сравнении новая хуже.
:::

{{practice: fix-retrain}}

## Разберём вместе: тихая поломка категорий

Сбой в числах виден по медианам. С категориями хитрее. Пусть в сентябре в CRM переименовали канал «сайт» в «website». Ошибки не будет: `OneHotEncoder(handle_unknown="ignore")` превратит незнакомое значение в нули по всем каналам. Что это значит для прогноза?

Веса каналов в модели (логит, относительно среднего):

| канал | вес |
|---|---|
| рекомендация | +1.77 |
| звонок | +1.03 |
| выставка | +0.40 |
| сайт | **−0.47** |
| тендер | −1.04 |
| соцсети | −1.70 |

У «сайта» вес отрицательный — заявки с сайта конвертируются хуже. После переименования вес −0.47 просто исчезает (нули вместо единицы), и прогноз для 108 сентябрьских заявок с сайта **вырастает**: в среднем с 0.073 до 0.100. Никакой ошибки, никакого падения — модель тихо стала оптимистичнее к худшему каналу, а это 39 % заявок месяца.

::: figure onehot-unknown
Как OneHotEncoder с `handle_unknown="ignore"` видит переименованный канал: строка из одних нулей. Ошибки нет, а отрицательный вес «сайта» исчезает из прогноза.
:::

Что получилось: проверка «нет ли новых категорий» должна стоять рядом с проверкой медиан. Это одна строка — разность множеств `set(месяц) - set(обучение)`.

::: warn Типичные ошибки мониторинга
- **Ждать ответов.** Качество известно через месяц-два, а входы и выходы — в день запуска. Начинайте с них.
- **Смотреть только AUC.** Он не видит сдвига всех прогнозов и не видит, что список «выше порога» опустел.
- **`handle_unknown="ignore"` без проверки новых категорий.** Он спасает от падения, но прячет переименования.
- **Переобучить на сломанных данных.** Модель выучит, что «120 часов» — норма, и сбой станет невидимым.
- **Тревога на каждый шорох.** Пороги проверок подбирают по разбросу «спокойных» месяцев, иначе письма перестанут читать.
:::

{{practice: new-category}}

## Практика

## task: month-col | Месяц заявки | warmup

Добавьте в таблицу `d` столбец `month` — номер месяца из `created`, и сохраните в `per_month` число заявок по месяцам (Series, индекс — месяц).

### starter
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])

```

### check
```python
import pandas as _pd
w = _pd.read_csv('catering_leads.csv', parse_dates=['created'])['created'].dt.month.value_counts().sort_index()
dd = need('d', _pd.DataFrame)
assert 'month' in dd.columns, 'В d нет столбца month.'
pm = need('per_month', _pd.Series).sort_index()
assert list(pm.index) == list(w.index) and list(pm.values) == list(w.values), f'per_month не совпадает: ожидалось {w.to_dict()}.'
```

### hint
`d["month"] = d["created"].dt.month` — столбец добавляется прямо в `d`.

### hint
`per_month = d.groupby("month").size()` (или `d["month"].value_counts().sort_index()`).

### solution
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
per_month = d.groupby("month").size()
```

## task: p-monitor | Сводка по месяцу | warmup

Соберите функцию, которая возвращает сводку по одному месяцу: число заявок, средний прогноз и долю прогнозов выше порога.

### parsons
```python
def month_report(p, threshold=0.3):
    return {
        "leads": len(p),
        "mean_pred": round(float(p.mean()), 3),
        "above": round(float((p > threshold).mean()), 3),
    }
```

### check
```python
import numpy as _np
f = need('month_report')
r = f(_np.array([0.1, 0.5, 0.2, 0.4]))
assert r == {'leads': 4, 'mean_pred': 0.3, 'above': 0.5}, f'month_report вернула {r}.'
```

### hint
Тело функции — один `return` со словарём.

### hint
Порядок ключей: `leads`, `mean_pred`, `above`; закрывающая скобка словаря — последняя строка.

## task: miss-share | Доля пропусков по месяцам | warmup

Посчитайте долю пропусков `budget_pp` по месяцам (3 знака) и сохраните Series `miss`. В `max_month` — месяц с наибольшей долей.

### starter
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month

```

### check
```python
import pandas as _pd
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
w = dd['budget_pp'].isna().groupby(dd['month']).mean().round(3)
m = need('miss', _pd.Series).sort_index()
assert list(m.index) == list(w.index), f'Индекс miss: {list(m.index)}, нужны месяцы 1–9.'
assert all(close(a, b) for a, b in zip(m.values, w.values)), 'Доли пропусков не совпадают — проверьте .isna() и группировку по month.'
assert need('max_month') == int(w.idxmax()), f'max_month = {need("max_month")}, а нужно {int(w.idxmax())}.'
```

### hint
`.isna()` даёт True/False для каждой заявки, а среднее True/False — доля пропусков.

### hint
`d["budget_pp"].isna().groupby(d["month"]).mean()`. Месяц с максимумом — `miss.idxmax()`.

### solution
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
miss = d["budget_pp"].isna().groupby(d["month"]).mean().round(3)
max_month = int(miss.idxmax())
```

### explain
Доля пропусков гуляет от 24 % до 29 % — без скачков. Такой разброс при 300 заявках в месяц ожидаем; тревожным был бы скачок до 50 %.

## task: monthly-auc | Качество по месяцам | base

В заготовке модель обучена на январе–апреле (переменные `d`, `num`, `cat`, `model` уже есть). Посчитайте для мая–сентября DataFrame `quality` со столбцами `month`, `fact` (конверсия), `predicted` (средний прогноз), `auc` — все дробные значения с 3 знаками. В `worst_month` сохраните месяц с наименьшим AUC.

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
def _make():
    prep = make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
        (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore")), cat))
    return make_pipeline(prep, LogisticRegression(max_iter=1000))
_train = d[d["month"] <= 4]
model = _make().fit(_train[num + cat], _train["converted"])
_ref_model = _make().fit(_train[num + cat], _train["converted"])
```

### starter
```python
# уже есть: d (со столбцом month), num, cat, model (обучена на январе–апреле)
from sklearn.metrics import roc_auc_score

```

### check
```python
import pandas as _pd
from sklearn.metrics import roc_auc_score as _auc
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
want = []
for m, part in dd[dd['month'] >= 5].groupby('month'):
    pp = _ref_model.predict_proba(part[num + cat])[:, 1]
    want.append((m, round(part['converted'].mean(), 3), round(pp.mean(), 3), round(_auc(part['converted'], pp), 3)))
q = need('quality', _pd.DataFrame)
assert list(q['month']) == [5, 6, 7, 8, 9], f'Месяцы в quality: {list(q["month"])}, нужны 5–9.'
for (m, f, pr, a), (_, row) in zip(want, q.iterrows()):
    assert close(row['fact'], f) and close(row['predicted'], pr) and close(row['auc'], a), f'Месяц {m}: ожидалось fact {f}, predicted {pr}, auc {a}; у вас {row["fact"]}, {row["predicted"]}, {row["auc"]}.'
assert need('worst_month') == min(want, key=lambda w: w[3])[0], f'worst_month = {need("worst_month")}.'
```

### hint
Цикл `for m, part in d[d["month"] >= 5].groupby("month")`, внутри `p = model.predict_proba(part[num + cat])[:, 1]`.

### hint
AUC — `roc_auc_score(part["converted"], p)`. Соберите строки-словари в список и сделайте DataFrame.

### solution
```python
from sklearn.metrics import roc_auc_score
import pandas as pd

rows = []
for m, part in d[d["month"] >= 5].groupby("month"):
    p = model.predict_proba(part[num + cat])[:, 1]
    rows.append({"month": m, "fact": round(part["converted"].mean(), 3),
                 "predicted": round(p.mean(), 3), "auc": round(roc_auc_score(part["converted"], p), 3)})
quality = pd.DataFrame(rows)
worst_month = int(quality.loc[quality["auc"].idxmin(), "month"])
```

### explain
Худший месяц — июнь (около 0.82), но это в пределах обычного шума: модель не сломалась, просто в месяце мало договоров. Поэтому тревогу поднимают не по одному месяцу ниже среднего, а по устойчивому падению или по резкому скачку.

## task: new-category | Новые категории | base

Смоделируйте переименование из «Разберём вместе»: в копии `live` замените в сентябре канал «сайт» на «website». Сохраните словарь `new_cats` — для каждого месяца с мая список каналов (отсортированный), которых не было в обучении (`train`), число переименованных заявок `n_renamed` и средний прогноз для них до (`pred_before`, по `d`) и после переименования (`pred_after`, по `live`), оба — 3 знака.

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
def _make():
    prep = make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
        (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore")), cat))
    return make_pipeline(prep, LogisticRegression(max_iter=1000))
train = d[d["month"] <= 4]
model = _make().fit(train[num + cat], train["converted"])
_ref_model = _make().fit(train[num + cat], train["converted"])
```

### starter
```python
# уже есть: d, train (январь–апрель), num, cat, model
live = d.copy()

```

### check
```python
import pandas as _pd
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
tr = dd[dd['month'] <= 4]
lv = dd.copy(); m9 = (lv['month'] == 9) & (lv['channel'] == 'сайт'); lv.loc[m9, 'channel'] = 'website'
known = set(tr['channel'].dropna())
w = {int(m): sorted(set(p['channel'].dropna()) - known) for m, p in lv[lv['month'] >= 5].groupby('month')}
nc = {int(k): sorted(v) for k, v in need('new_cats', dict).items()}
assert nc == w, f'new_cats = {nc}, а нужно {w}.'
assert need('n_renamed') == int(m9.sum()), f'n_renamed = {need("n_renamed")}, а нужно {int(m9.sum())}.'
pb = round(_ref_model.predict_proba(dd[m9][num + cat])[:, 1].mean(), 3); pa = round(_ref_model.predict_proba(lv[m9][num + cat])[:, 1].mean(), 3)
assert close(need('pred_before'), pb) and close(need('pred_after'), pa), f'pred_before, pred_after = {need("pred_before")}, {need("pred_after")}, а нужно {pb}, {pa}.'
```

### hint
Маска переименования: `m9 = (live["month"] == 9) & (live["channel"] == "сайт")`, затем `live.loc[m9, "channel"] = "website"`.

### hint
Известные каналы — `set(train["channel"].dropna())`. Для каждого месяца: `sorted(set(part["channel"].dropna()) - known)`.

### hint
Прогноз до — `model.predict_proba(d[m9][num + cat])[:, 1].mean()`, после — то же по `live[m9]`. Маска `m9` подходит к обеим таблицам: индексы совпадают.

### solution
```python
live = d.copy()
m9 = (live["month"] == 9) & (live["channel"] == "сайт")
live.loc[m9, "channel"] = "website"

known = set(train["channel"].dropna())
new_cats = {int(m): sorted(set(part["channel"].dropna()) - known)
            for m, part in live[live["month"] >= 5].groupby("month")}
n_renamed = int(m9.sum())
pred_before = round(model.predict_proba(d[m9][num + cat])[:, 1].mean(), 3)
pred_after = round(model.predict_proba(live[m9][num + cat])[:, 1].mean(), 3)
```

### explain
Проверка нашла «website» в сентябре и ничего в другие месяцы — ложных тревог нет. А прогноз для 108 заявок с сайта вырос с 0.073 до 0.100, примерно на треть: модель перестала знать, что канал слабый. По выходу модели (средний прогноз месяца) такой сдвиг почти незаметен, по входу — виден сразу.

## task: median-alarm | Тревога по медианам | base

В заготовке `live` — данные, где с августа время ответа записано в минутах. Для каждого месяца с мая посчитайте отношение медианы признака к медиане за январь–апрель по признакам `guests`, `budget_pp`, `days_to_event`, `response_hours`. Сохраните DataFrame `ratio` (строки — месяцы, столбцы — признаки) и список `alarms` — пары `(месяц, признак)`, где отношение меньше 0.5 или больше 2, в порядке месяцев, а внутри месяца — в порядке признаков.

### starter
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
live = d.copy()
aug = live["month"] >= 8
live.loc[aug, "response_hours"] = (live.loc[aug, "response_hours"] * 60).round()
cols = ["guests", "budget_pp", "days_to_event", "response_hours"]

```

### check
```python
import pandas as _pd
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
a = dd['month'] >= 8; dd.loc[a, 'response_hours'] = (dd.loc[a, 'response_hours'] * 60).round()
cs = ['guests', 'budget_pp', 'days_to_event', 'response_hours']
w = dd[dd['month'] >= 5].groupby('month')[cs].median() / dd[dd['month'] <= 4][cs].median()
r = need('ratio', _pd.DataFrame)
assert list(r.index) == list(w.index), f'Строки ratio: {list(r.index)}, нужны месяцы 5–9.'
assert all(close(r.loc[m, c], w.loc[m, c], 0.01) for m in w.index for c in cs), 'Отношения медиан не совпадают. Делите медианы по месяцам на медианы января–апреля.'
want = [(m, c) for m in w.index for c in cs if w.loc[m, c] < 0.5 or w.loc[m, c] > 2]
got = [(int(m), c) for m, c in need('alarms')]
assert got == want, f'alarms = {got}, а нужно {want}.'
```

### hint
`base = live[live["month"] <= 4][cols].median()`; деление DataFrame на Series выравнивается по столбцам.

### hint
Двойной цикл по `ratio.index` и `cols` со сравнением `< 0.5 or > 2`.

### solution
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
live = d.copy()
aug = live["month"] >= 8
live.loc[aug, "response_hours"] = (live.loc[aug, "response_hours"] * 60).round()
cols = ["guests", "budget_pp", "days_to_event", "response_hours"]

base = live[live["month"] <= 4][cols].median()
ratio = live[live["month"] >= 5].groupby("month")[cols].median() / base
alarms = [(m, c) for m in ratio.index for c in cols if ratio.loc[m, c] < 0.5 or ratio.loc[m, c] > 2]
```

### explain
Отношение к эталонному периоду — простой и устойчивый сигнал. Медиана не реагирует на единичные крупные заказы, а отношение не зависит от единиц признака: 1.07 у гостей и 0.88 у времени ответа читаются одинаково — «примерно как раньше». С августа медиана `response_hours` выросла в 55–58 раз — множитель 60 с поправкой на состав заявок. Так выглядит не изменение поведения клиентов, а смена единиц измерения в источнике (часы → минуты). Модель такой сдвиг не заметит сама: она молча посчитает новые «часы» и выдаст неверные прогнозы. Поэтому такие проверки ставят перед моделью.

## task: auc-blind | Слепое пятно AUC | base

Покажите, что AUC не видит общего сдвига. Возьмите сентябрьские заявки из `d` (без сбоя), прогнозы `p` модели и сдвиньте все логиты на −2: `p2 = 1 / (1 + np.exp(-(np.log(p / (1 - p)) - 2)))`. Логит — это `log(p / (1 − p))`, логарифм шансов (глава 6, урок «Логистическая регрессия и вероятности»); обратно его переводит сигмоида. Вычесть 2 из логита — значит уменьшить шансы каждой заявки в e² ≈ 7 раз: все вероятности падают, но порядок заявок не меняется. Так выглядит общий сдвиг, когда поломка задевает всех одинаково. Сохраните `auc_p`, `auc_p2` (3 знака), долю заявок выше 0.3 `above_p`, `above_p2` и средние прогнозы `mean_p`, `mean_p2` (все — 3 знака).

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
def _make():
    prep = make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
        (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore")), cat))
    return make_pipeline(prep, LogisticRegression(max_iter=1000))
train = d[d["month"] <= 4]
model = _make().fit(train[num + cat], train["converted"])
_ref_model = _make().fit(train[num + cat], train["converted"])
```

### starter
```python
import numpy as np
from sklearn.metrics import roc_auc_score
# уже есть: d, num, cat, model
sep = d[d["month"] == 9]

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.metrics import roc_auc_score as _auc
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
sp = dd[dd['month'] == 9]; p = _ref_model.predict_proba(sp[num + cat])[:, 1]
p2 = 1 / (1 + _np.exp(-(_np.log(p / (1 - p)) - 2)))
w = {'auc_p': _auc(sp['converted'], p), 'auc_p2': _auc(sp['converted'], p2), 'above_p': (p > 0.3).mean(), 'above_p2': (p2 > 0.3).mean(), 'mean_p': p.mean(), 'mean_p2': p2.mean()}
for k, v in w.items():
    assert close(need(k), round(v, 3)), f'{k} = {need(k)}, а нужно {round(v, 3)}.'
```

### hint
`p = model.predict_proba(sep[num + cat])[:, 1]`; логит — `np.log(p / (1 - p))`.

### hint
AUC — `roc_auc_score(sep["converted"], p)`; доля выше порога — `(p > 0.3).mean()`.

### solution
```python
import numpy as np
from sklearn.metrics import roc_auc_score
sep = d[d["month"] == 9]

p = model.predict_proba(sep[num + cat])[:, 1]
p2 = 1 / (1 + np.exp(-(np.log(p / (1 - p)) - 2)))
auc_p = round(roc_auc_score(sep["converted"], p), 3)
auc_p2 = round(roc_auc_score(sep["converted"], p2), 3)
above_p = round((p > 0.3).mean(), 3)
above_p2 = round((p2 > 0.3).mean(), 3)
mean_p = round(p.mean(), 3)
mean_p2 = round(p2.mean(), 3)
```

### explain
AUC 0.837 в обоих случаях — до последнего знака. А доля «горячих» заявок упала с 13.8 % до 1.5 %, средний прогноз — с 0.114 до 0.027 при фактической конверсии около 0.13. Менеджеры получили бы в 10 раз меньше заявок в работу, а дашборд с одним AUC показывал бы «всё в порядке». Поэтому в мониторинге всегда есть калибровка (средний прогноз против факта) и доля выше порога.

## task: output-alarm | Тревога по выходу модели | base

На данных `live` (минуты с августа) посчитайте для каждого месяца с мая долю заявок с прогнозом выше 0.3. Сравните с той же долей на обучающих данных (`train_share`, 3 знака). Сохраните Series `above` (индекс — месяц, 3 знака) и список `alarm_months` — месяцы, где доля отличается от обучающей больше чем вдвое (меньше половины или больше двух).

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
def _make():
    prep = make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
        (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore")), cat))
    return make_pipeline(prep, LogisticRegression(max_iter=1000))
train = d[d["month"] <= 4]
model = _make().fit(train[num + cat], train["converted"])
_ref_model = _make().fit(train[num + cat], train["converted"])
live = d.copy()
live.loc[live["month"] >= 8, "response_hours"] = (live.loc[live["month"] >= 8, "response_hours"] * 60).round()
```

### starter
```python
# уже есть: d, live (минуты с августа), train (январь–апрель), num, cat, model

```

### check
```python
import pandas as _pd
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
tr = dd[dd['month'] <= 4]
lv = dd.copy(); lv.loc[lv['month'] >= 8, 'response_hours'] = (lv.loc[lv['month'] >= 8, 'response_hours'] * 60).round()
ts = round((_ref_model.predict_proba(tr[num + cat])[:, 1] > 0.3).mean(), 3)
w = {m: round((_ref_model.predict_proba(part[num + cat])[:, 1] > 0.3).mean(), 3) for m, part in lv[lv['month'] >= 5].groupby('month')}
assert close(need('train_share'), ts), f'train_share = {need("train_share")}, а нужно {ts}.'
ab = need('above', _pd.Series)
assert all(close(ab[m], v) for m, v in w.items()), f'above: ожидалось {w}.'
want = [m for m, v in w.items() if v < ts / 2 or v > ts * 2]
assert [int(m) for m in need('alarm_months')] == want, f'alarm_months = {need("alarm_months")}, а нужно {want}.'
```

### hint
Для обучения: `(model.predict_proba(train[num + cat])[:, 1] > 0.3).mean()`. Для месяцев — тот же расчёт в `groupby("month")` по `live`.

### hint
`above = live[live["month"] >= 5].groupby("month").apply(lambda part: (model.predict_proba(part[num + cat])[:, 1] > 0.3).mean()).round(3)`, тревога — `v < train_share / 2 or v > train_share * 2`.

### solution
```python
import pandas as pd

train_share = round((model.predict_proba(train[num + cat])[:, 1] > 0.3).mean(), 3)
above = pd.Series({m: round((model.predict_proba(part[num + cat])[:, 1] > 0.3).mean(), 3)
                   for m, part in live[live["month"] >= 5].groupby("month")})
alarm_months = [m for m, v in above.items() if v < train_share / 2 or v > train_share * 2]
```

### explain
Проверка по выходу сработала в августе — в тот же месяц, что и проверка по медианам, и на месяц-два раньше, чем стали бы известны договоры. Ей даже не нужно знать, какой признак сломался: достаточно, что модель стала вести себя иначе.

## task: fix-retrain | Починить и переобучить | plus

Сбой нашли: с августа минуты переводим обратно в часы. Сравните на августе–сентябре (данные `d`, уже без сбоя) две модели: `old` — обучена на январе–апреле (есть в заготовке как `model`), `new` — такая же, обученная на январе–июле (создайте функцией `make_model()`). Сохраните `auc_old`, `auc_new` (3 знака) и `use_new` — `True`, если новая модель лучше.

### setup
```python
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
def make_model():
    prep = make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), num),
        (make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore")), cat))
    return make_pipeline(prep, LogisticRegression(max_iter=1000))
model = make_model().fit(d[d["month"] <= 4][num + cat], d[d["month"] <= 4]["converted"])
```

### starter
```python
# уже есть: d, num, cat, make_model() — новый необученный конвейер, model — обучена на январе–апреле
from sklearn.metrics import roc_auc_score

```

### check
```python
from sklearn.metrics import roc_auc_score as _auc
import pandas as _pd
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
late = dd[dd['month'] >= 8]
o = make_model().fit(dd[dd['month'] <= 4][num + cat], dd[dd['month'] <= 4]['converted'])
n = make_model().fit(dd[dd['month'] <= 7][num + cat], dd[dd['month'] <= 7]['converted'])
ao = round(_auc(late['converted'], o.predict_proba(late[num + cat])[:, 1]), 3)
an = round(_auc(late['converted'], n.predict_proba(late[num + cat])[:, 1]), 3)
assert close(need('auc_old'), ao), f'auc_old = {need("auc_old")}, а нужно {ao}.'
assert close(need('auc_new'), an), f'auc_new = {need("auc_new")}, а нужно {an}. Новая модель — на месяцах 1–7.'
assert need('use_new') == (an > ao), f'use_new = {need("use_new")}.'
```

### hint
`late = d[d["month"] >= 8]`; `new = make_model().fit(d[d["month"] <= 7][num + cat], d[d["month"] <= 7]["converted"])`.

### hint
Обе модели проверяйте на одних и тех же заявках `late`: `roc_auc_score(late["converted"], model.predict_proba(late[num + cat])[:, 1])`.

### solution
```python
from sklearn.metrics import roc_auc_score

late = d[d["month"] >= 8]
early = d[d["month"] <= 7]
new = make_model().fit(early[num + cat], early["converted"])
auc_old = round(roc_auc_score(late["converted"], model.predict_proba(late[num + cat])[:, 1]), 3)
auc_new = round(roc_auc_score(late["converted"], new.predict_proba(late[num + cat])[:, 1]), 3)
use_new = auc_new > auc_old
```

### explain
Новая модель лучше (0.87 против 0.84) — не потому, что мир изменился, а потому, что у неё почти вдвое больше примеров. Разница в 0.03 на 620 заявках с 77 договорами всё же невелика; перед заменой модели в реальной работе её проверяют на ещё одном свежем месяце.

## task: psi | Индекс стабильности | star

Напишите функцию `psi(a, b, bins)`: доли значений `a` и `b` по интервалам `pd.cut(..., bins)` (`value_counts(normalize=True, sort=False)`), к каждой доле прибавьте 0.0001 (чтобы не делить на ноль), и верните сумму (b − a) × ln(b / a). Посчитайте PSI `response_hours` между январём–апрелем и каждым месяцем с мая на данных `live` (минуты с августа), интервалы `[0, 1, 2, 4, 8, 100000]`. Сохраните Series `psi_by_month` (3 знака) и список `serious` — месяцы с PSI больше 0.25.

### starter
```python
import numpy as np
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
live = d.copy()
aug = live["month"] >= 8
live.loc[aug, "response_hours"] = (live.loc[aug, "response_hours"] * 60).round()
bins = [0, 1, 2, 4, 8, 100000]

```

### check
```python
import numpy as _np, pandas as _pd
dd = _pd.read_csv('catering_leads.csv', parse_dates=['created']); dd['month'] = dd['created'].dt.month
a = dd['month'] >= 8; dd.loc[a, 'response_hours'] = (dd.loc[a, 'response_hours'] * 60).round()
bs = [0, 1, 2, 4, 8, 100000]
def _psi(x, y):
    px = _pd.cut(x, bs).value_counts(normalize=True, sort=False) + 1e-4
    py = _pd.cut(y, bs).value_counts(normalize=True, sort=False) + 1e-4
    return float(((py - px) * _np.log(py / px)).sum())
base = dd[dd['month'] <= 4]['response_hours']
w = {m: round(_psi(base, part['response_hours']), 3) for m, part in dd[dd['month'] >= 5].groupby('month')}
s = need('psi_by_month', _pd.Series)
assert all(close(s[m], v, 0.002) for m, v in w.items()), f'psi_by_month: ожидалось {w}.'
assert [int(m) for m in need('serious')] == [m for m, v in w.items() if v > 0.25], f'serious = {need("serious")}.'
```

### hint
Внутри функции: `pa = pd.cut(a, bins).value_counts(normalize=True, sort=False) + 0.0001`, так же `pb`, затем `((pb - pa) * np.log(pb / pa)).sum()`.

### hint
Заметьте: значение 0 не попадает ни в один интервал `(0, 1]` — это ок, `value_counts` по интервалам его просто не посчитает.

### solution
```python
import numpy as np
import pandas as pd
d = pd.read_csv("catering_leads.csv", parse_dates=["created"])
d["month"] = d["created"].dt.month
live = d.copy()
aug = live["month"] >= 8
live.loc[aug, "response_hours"] = (live.loc[aug, "response_hours"] * 60).round()
bins = [0, 1, 2, 4, 8, 100000]

def psi(a, b, bins):
    pa = pd.cut(a, bins).value_counts(normalize=True, sort=False) + 0.0001
    pb = pd.cut(b, bins).value_counts(normalize=True, sort=False) + 0.0001
    return float(((pb - pa) * np.log(pb / pa)).sum())

base = live[live["month"] <= 4]["response_hours"]
psi_by_month = pd.Series({m: round(psi(base, part["response_hours"], bins), 3)
                          for m, part in live[live["month"] >= 5].groupby("month")})
serious = [m for m, v in psi_by_month.items() if v > 0.25]
```

### explain
До августа PSI около 0.01 — распределение стабильно. С августа почти все значения попадают в последний интервал, и PSI взлетает на порядки выше порога 0.25. Медианы ловят такой сбой не хуже, но PSI замечает и более тонкие сдвиги формы распределения, при которых медиана почти не меняется.
