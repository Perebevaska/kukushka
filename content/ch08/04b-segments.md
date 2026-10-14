---
title: "Качество по сегментам и отчёт о метрике"
lead: "Одно число качества на всю сеть прячет слабые места: модель может хорошо ранжировать заявки в целом и при этом путаться внутри каждого канала. Считаем качество по сегментам с доверительными интервалами и учимся писать о метрике так, чтобы из отчёта нельзя было сделать неправильный вывод."
files: [catering_leads.csv]
recap:
  - "Качество смотрят и по сегментам (каналы, города): AUC внутри сегмента, средний прогноз против факта, число объектов и положительных. Общий AUC может быть выше любого сегментного — часть его модель получает, различая сегменты."
  - "Привычка «отчёт о метрике»: что и на чём (n, положительные), с чем сравнить, интервал (бутстрэп), худший сегмент, калибровка, что значит для бизнеса."
---

Модель и данные — те же, что в уроке «Модель в работе: мониторинг»: приоритизация заявок кейтеринга, обученная на январе–апреле и работающая с мая.

## Качество по сегментам

Общий AUC за май–сентябрь — 0.846. Хорошая новость для отчёта, но менеджер, который ведёт тендеры, спрашивает другое: «А на **моих** заявках модель работает?» Одно число по всем заявкам может прятать сегмент, где модель ошибается систематически. Поэтому качество смотрят ещё и **по сегментам** — каналам, городам, типам клиентов.

::: tip Аналогия
«Средняя температура по больнице» — 36.6, а в одной палате у всех жар. Общий показатель честно посчитан, но про палату ничего не говорит. У AUC всё ещё хитрее — общий может быть **выше** любого из частных, это разберём на примере ниже.
:::

### Игрушечный пример: общий AUC выше, чем в каждом сегменте

Шесть заявок из двух каналов, прогноз и факт:

| канал | прогноз | договор? |
|---|---|---|
| рекомендация | 0.60 | да |
| рекомендация | 0.50 | нет |
| рекомендация | 0.40 | да |
| соцсети | 0.20 | нет |
| соцсети | 0.10 | да |
| соцсети | 0.05 | нет |

Вспомним главу 7: AUC — доля пар «договор — не договор», в которых у договора прогноз выше.

- **Внутри «рекомендаций»** две пары: 0.60 против 0.50 — верно, 0.40 против 0.50 — неверно. AUC = 1/2 = **0.5**.
- **Внутри «соцсетей»** тоже две пары: 0.10 против 0.20 — неверно, 0.10 против 0.05 — верно. AUC = **0.5**.
- **Все вместе** — 3 × 3 = 9 пар. Верно упорядочены 6: у 0.60 — все три, у 0.40 — две (0.20 и 0.05), у 0.10 — одна (0.05). AUC = 6/9 ≈ **0.67**.

Внутри каналов модель угадывает не лучше монетки, а в целом выглядит прилично. Весь её «успех» — в том, что она отличает рекомендации от соцсетей. Это тоже полезно, но менеджеру, который получил сто заявок из соцсетей, модель не поможет выбрать лучшие.

::: figure seg-auc-pairs
Все девять пар «договор — не договор» из примера. Внутри каждого канала (выделенные клетки) модель права в половине пар; правильные пары между каналами поднимают общий AUC до 0.67.
:::

```python
from sklearn.metrics import roc_auc_score
y = [1, 0, 1, 0, 1, 0]
p = [0.6, 0.5, 0.4, 0.2, 0.1, 0.05]
print(roc_auc_score(y, p), roc_auc_score(y[:3], p[:3]), roc_auc_score(y[3:], p[3:]))
```

{{practice: seg-toy}}

### На заявках кейтеринга

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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]

def seg(t):                                   # одна строка отчёта для одного сегмента
    return pd.Series({"leads": len(t), "deals": t["converted"].sum(),
                      "fact": t["converted"].mean(), "pred": t["p"].mean(),
                      "auc": roc_auc_score(t["converted"], t["p"])})

live.groupby("channel")[["converted", "p"]].apply(seg).round(3)
```

**Что здесь происходит:**

- `live` — заявки после запуска (май–сентябрь), `p` — прогноз модели для каждой.
- `seg(t)` получает кусок таблицы одного канала и возвращает Series из пяти чисел: заявок, договоров, фактическая конверсия, средний прогноз, AUC внутри канала.
- `groupby("channel")[...].apply(seg)` — применить функцию к каждому каналу; строки Series становятся столбцами таблицы. Это `GROUP BY channel` с самодельной агрегатной функцией.

**Как читать таблицу.** Смотрим на три вещи.

1. **AUC внутри каналов разный:** 0.77 у рекомендаций и 0.78 у звонков — заметно ниже общего 0.846, а у сайта 0.87. Общий AUC — не среднее этих чисел: часть его модель получает, отличая каналы друг от друга, как в игрушечном примере. Поэтому «внутри канала хуже, чем в целом» — не поломка.
2. **Размер сегмента.** У тендеров 3 договора на 60 заявок, у выставок — 8. AUC 0.92 у выставок на восьми договорах — почти ничего не значит: одна-две заявки меняют его на десятые.
3. **Прогноз против факта.** Для соцсетей модель обещает в среднем 0.025, а договоры заключают 6.8 % заявок — в 2.7 раза больше. Для сайта 0.076 против 0.104. Если менеджеры берут в работу заявки с прогнозом выше 0.3, из 324 заявок соцсетей туда попадают 2. Канал фактически выключен — не потому, что он плохой, а потому, что модель его недооценивает.

Что делать с находкой: показать её владельцу канала, проверить, не изменился ли канал после обучения (январь–апрель), и, если недооценка держится, — откалибровать модель или ставить порог отдельно для канала.

::: warn Типичные ошибки
- **Только общий AUC.** Он смешивает «модель различает каналы» и «модель различает заявки внутри канала». Менеджеру нужно второе.
- **Выводы по маленькому сегменту.** «У тендеров AUC 0.76 — модель там плохая» — на трёх договорах это шум. Рядом с метрикой сегмента всегда пишите число объектов и число положительных.
- **AUC без калибровки.** Внутри соцсетей AUC 0.85 — хороший порядок, но все вероятности занижены, и решения по общему порогу для канала неверны.
- **Сегментов слишком много.** Разрежьте данные на 50 частей — в какой-нибудь случайно окажется «провал». Сегменты выбирают заранее, по тому, как работает бизнес.
:::

{{practice: seg-table}}

## Отчёт о метрике: привычка

«AUC 0.85» — не отчёт, а заготовка для неправильных выводов. Без контекста читатель не знает, много это или мало, на каких данных и насколько число может прыгать. Сделайте привычкой писать метрику **шестью строками**:

1. **Что и на чём.** Метрика, период, сколько объектов и сколько положительных.
2. **С чем сравнить.** Случайный порядок (AUC 0.5), прошлая модель, простое правило.
3. **Разброс.** Доверительный интервал бутстрэпом (глава 5) или разброс по месяцам/фолдам.
4. **По сегментам.** Худший значимый сегмент — с числом объектов.
5. **Калибровка.** Средний прогноз против факта.
6. **Что это значит для бизнеса** и чего метрика не говорит.

::: sql
Это как подпись под графиком в отчёте BI: источник, период, фильтры, «данные за сентябрь неполные». Без подписи график выглядит убедительно и ничего не гарантирует.
:::

Разброс для AUC проще всего получить бутстрэпом: много раз выбрать заявки с возвращением, посчитать AUC и взять 2.5-й и 97.5-й процентили.

```python
# шапка та же, что в первом примере урока «Модель в работе: мониторинг»: данные и модель на январе–апреле
import numpy as np
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]

def auc_ci(y, p, n_boot=200, seed=0):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))      # выборка с возвращением
        if y[i].min() == y[i].max():             # в выборке один класс — AUC не посчитать
            continue
        aucs.append(roc_auc_score(y[i], p[i]))
    return np.percentile(aucs, [2.5, 97.5]).round(3)

print("все заявки:", round(roc_auc_score(live["converted"], live["p"]), 3), auc_ci(live["converted"], live["p"]))
for ch in ["сайт", "выставка", "тендер"]:
    t = live[live["channel"] == ch]
    print(ch, round(roc_auc_score(t["converted"], t["p"]), 3), auc_ci(t["converted"], t["p"]))
```

**Что здесь происходит:**

- `rng.integers(0, len(y), len(y))` — столько же случайных номеров строк, сколько заявок, с повторами: одна «параллельная выборка».
- Проверка `y[i].min() == y[i].max()` нужна для маленьких сегментов: в выборке из 60 тендеров могут не попасться все 3 договора, и AUC не определён.
- `np.percentile(aucs, [2.5, 97.5])` — границы, между которыми лежат 95 % бутстрэп-значений.

**Что получилось.** По всем заявкам AUC 0.846, интервал 0.82–0.87 — узкий: 1 728 заявок и 230 договоров. У сайта (71 договор) 0.84–0.91. У выставок 0.85–0.99, у тендеров 0.60–0.97 — эти интервалы такие широкие, что сравнивать каналы между собой бессмысленно.

Точку отсчёта тоже считают кодом. Правило «повторный клиент — первым» — это столбец `repeat_client` (1 у повторных, 0 у остальных), подставленный вместо прогноза: `roc_auc_score(live["converted"], live["repeat_client"])` даёт **0.671**. У правила всего два значения, поэтому большинство пар — ничьи (оба клиента новые или оба повторные), а ничья в AUC считается за половину пары. Отсюда и скромные 0.67 при том, что повторные клиенты заключают договор в 41 % случаев, а новые — в 9 %.

Так выглядит отчёт по этим числам:

::: tip Образец отчёта о метрике
**Модель приоритизации заявок, май–сентябрь 2026.** ROC-AUC 0.846 (95 % ДИ 0.82–0.87) на 1 728 заявках, 230 договоров. По месяцам — от 0.82 до 0.86. Для сравнения: правило «повторный клиент — первым» даёт 0.67. Внутри каналов AUC от 0.77 (рекомендации, 71 договор) до 0.87 (сайт, 71 договор); по тендерам и выставкам договоров меньше десяти — оценка ненадёжна. Средний прогноз 0.116 при фактической конверсии 0.133: модель немного занижает вероятности, сильнее всего — в соцсетях (0.025 против 0.068). **Что значит:** порядок заявок модель задаёт хорошо, но общий порог 0.3 почти не пропускает заявки из соцсетей; предлагаем проверить калибровку по каналам.
:::

::: quiz
В сегменте «выставка» AUC 0.92, а по всем заявкам 0.85. Какой вывод верный?

- [x] Сказать, что модель на выставках лучше, нельзя: там 8 договоров, интервал 0.85–0.99, и его нижняя граница — на уровне общего AUC
  > При восьми положительных примерах одна заявка может сдвинуть AUC больше чем на 0.1 (1/8 всех пар), а интервал шириной почти 0.15 втрое шире общего. Сначала смотрят на число положительных и интервал, потом сравнивают.
- [ ] Модель на выставках лучше — это видно по числу
  > Число без размера выборки и разброса ничего не доказывает: интервал широкий и перекрывается с общим.
- [ ] Общий AUC ошибочен: он должен быть средним AUC сегментов
  > Общий AUC считают по всем парам сразу; он не равен среднему по сегментам и может быть выше любого из них.
- [ ] Выставки надо исключить из обучения, они «слишком простые»
  > Высокий AUC на маленьком сегменте — не причина менять обучение. К тому же он ненадёжен.
:::

::: warn Типичные ошибки
- **Метрика без n.** «AUC 0.92» и «AUC 0.92 на 8 договорах» — разные утверждения.
- **Нет точки отсчёта.** 0.85 хорошо, если правило даёт 0.67, и плохо, если прошлая модель давала 0.90.
- **Интервал на обучении.** Бутстрэп по обучающим данным покажет, как хорошо модель их запомнила, а не как она работает. Интервал считают на отложенных данных.
- **Лучший сегмент в заголовке.** Выбирать «самое красивое число» из десятка сегментов — та же подгонка, что подбор порога на тесте.
:::

{{practice: metric-report, rule-base, report-text}}

## Практика

## task: seg-table | Качество по городам | base

Постройте для заявок мая–сентября таблицу `by_city` по городам (индекс — город) со столбцами `leads`, `deals`, `fact`, `pred`, `auc` (как в теории, но по `city`), округлите до 3 знаков. Затем сохраните в `gap_city` город, где модель сильнее всего **занижает** конверсию (наибольшая разность `fact − pred`), а в `gap` — эту разность (3 знака).

### starter
```python
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]

```

### check
```python
import pandas as _pd
from sklearn.metrics import roc_auc_score as _auc
L = need('live', _pd.DataFrame)
t = need('by_city', _pd.DataFrame)
for c in ['leads', 'deals', 'fact', 'pred', 'auc']:
    assert c in t.columns, f'В by_city нет столбца {c}.'
assert sorted(t.index) == sorted(L['city'].unique()), f'Индекс by_city: {list(t.index)} — нужны города заявок мая–сентября.'
for city, g in L.groupby('city'):
    r = t.loc[city]
    assert r['leads'] == len(g) and r['deals'] == g['converted'].sum(), f'{city}: leads/deals = {r["leads"]}/{r["deals"]}, ожидалось {len(g)}/{g["converted"].sum()}.'
    assert close(r['fact'], round(g['converted'].mean(), 3)) and close(r['pred'], round(g['p'].mean(), 3)), f'{city}: проверьте fact (доля договоров) и pred (средний прогноз).'
    assert close(r['auc'], round(_auc(g['converted'], g['p']), 3)), f'{city}: auc = {r["auc"]} — AUC внутри города.'
gp = L.groupby('city')['converted'].mean() - L.groupby('city')['p'].mean()
assert need('gap_city') == gp.idxmax(), f'gap_city = {need("gap_city")!r}. Ищите наибольшую разность fact − pred (не по модулю).'
assert close(need('gap'), round(gp.max(), 3), 0.0015), f'gap = {need("gap")}, а нужно около {round(gp.max(), 3)}.'
```

### hint
Скопируйте функцию `seg` из теории и примените её к `live.groupby("city")[["converted", "p"]]`.

### hint
Разность — новый столбец: `(by_city["fact"] - by_city["pred"])`; город — `.idxmax()`, значение — `.max()`.

### hint
```python
def seg(t):
    return pd.Series({"leads": len(t), "deals": t["converted"].sum(),
                      "fact": t["converted"].mean(), "pred": t["p"].mean(),
                      "auc": roc_auc_score(t["converted"], t["p"])})

by_city = live.groupby("city")[["converted", "p"]].apply(seg).round(3)
diff = by_city["fact"] - by_city["pred"]
gap_city = ...
gap = round(..., 3)
```

### solution
```python
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]

def seg(t):
    return pd.Series({"leads": len(t), "deals": t["converted"].sum(),
                      "fact": t["converted"].mean(), "pred": t["p"].mean(),
                      "auc": roc_auc_score(t["converted"], t["p"])})

by_city = live.groupby("city")[["converted", "p"]].apply(seg).round(3)
diff = by_city["fact"] - by_city["pred"]
gap_city = diff.idxmax()
gap = round(diff.max(), 3)
```

### explain
Порядок заявок модель держит во всех городах (AUC 0.81–0.87), а вот уровень — нет: в Уфе договоры заключают 19.4 % заявок, а модель ждёт 14.2 %. Уфа — самый «конверсионный» город, и общий порог отсекает там часть хороших заявок. Обратите внимание на Екатеринбург: 77 заявок и 9 договоров — по нему выводов делать нельзя, хотя числа в таблице выглядят так же уверенно, как у Казани.

## task: metric-report | Отчёт о метрике | plus

Напишите функцию `metric_report(y, p, n_boot=200, seed=0)`, которая возвращает словарь с ключами `n`, `positives`, `auc`, `ci_low`, `ci_high`, `pred`, `fact` (числа, 3 знака где дробные). Интервал — бутстрэп, как в теории: `rng = np.random.default_rng(seed)`, `n_boot` раз выбрать номера строк `rng.integers(0, len(y), len(y))`, пропустить выборки с одним классом, взять процентили 2.5 и 97.5. Примените её ко всем заявкам мая–сентября (`rep_all`) и к заявкам канала «соцсети» (`rep_social`). В `wider` сохраните, во сколько раз интервал соцсетей шире общего (`(ci_high − ci_low)` соцсетей / то же общее, 1 знак).

### starter
```python
import numpy as np
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]

def metric_report(y, p, n_boot=200, seed=0):
    ...

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.metrics import roc_auc_score as _auc
def _ref(y, p, n_boot=200, seed=0):
    y, p = _np.asarray(y), _np.asarray(p)
    rng = _np.random.default_rng(seed); a = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        a.append(_auc(y[i], p[i]))
    lo, hi = _np.percentile(a, [2.5, 97.5])
    return {'n': len(y), 'positives': int(y.sum()), 'auc': round(_auc(y, p), 3), 'ci_low': round(float(lo), 3),
            'ci_high': round(float(hi), 3), 'pred': round(float(p.mean()), 3), 'fact': round(float(y.mean()), 3)}
f = need('metric_report')
yy, pp = _np.array([1, 0, 1, 0, 1, 0, 0, 1]), _np.array([0.9, 0.2, 0.6, 0.4, 0.3, 0.35, 0.1, 0.8])
r = f(yy, pp)
assert isinstance(r, dict), 'metric_report должна возвращать словарь.'
miss = {'n', 'positives', 'auc', 'ci_low', 'ci_high', 'pred', 'fact'} - set(r)
assert not miss, f'В словаре не хватает ключей: {sorted(miss)}.'
w = _ref(yy, pp)
for k in ['n', 'positives', 'auc', 'pred', 'fact']:
    assert close(r[k], w[k]), f'На маленьком примере {k} = {r[k]}, ожидалось {w[k]}.'
assert r['ci_low'] <= r['auc'] <= r['ci_high'], 'Интервал должен содержать AUC: проверьте процентили 2.5 и 97.5.'
L = need('live', _pd.DataFrame)
for name, mask in [('rep_all', L.index == L.index), ('rep_social', L['channel'] == 'соцсети')]:
    got, ref = need(name, dict), _ref(L.loc[mask, 'converted'], L.loc[mask, 'p'])
    for k in ['n', 'positives', 'auc', 'pred', 'fact']:
        assert close(got[k], ref[k]), f'{name}[{k!r}] = {got[k]}, ожидалось {ref[k]}.'
    for k in ['ci_low', 'ci_high']:
        assert close(got[k], ref[k], 0.011), f'{name}[{k!r}] = {got[k]}, ожидалось около {ref[k]}. Бутстрэп: default_rng(seed), integers(0, len(y), len(y)).'
ra, rs = _ref(L['converted'], L['p']), _ref(L.loc[L['channel'] == 'соцсети', 'converted'], L.loc[L['channel'] == 'соцсети', 'p'])
wd = round((rs['ci_high'] - rs['ci_low']) / (ra['ci_high'] - ra['ci_low']), 1)
assert close(need('wider'), wd, 0.25), f'wider = {need("wider")}, ожидалось около {wd}.'
```

### hint
Скелет — функция `auc_ci` из теории. Добавьте к ней точечный AUC, число строк и положительных, средний прогноз и факт и верните всё одним словарем.

### hint
Внутри функции сначала `y, p = np.asarray(y), np.asarray(p)` — тогда `y[i]` с массивом номеров работает и для Series. Числа из numpy приведите к обычным: `float(lo)`, `int(y.sum())`.

### hint
```python
def metric_report(y, p, n_boot=200, seed=0):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        aucs.append(roc_auc_score(y[i], p[i]))
    lo, hi = np.percentile(aucs, [2.5, 97.5])
    return {"n": len(y), "positives": int(y.sum()), "auc": round(roc_auc_score(y, p), 3),
            "ci_low": ..., "ci_high": ..., "pred": ..., "fact": ...}

soc = live[live["channel"] == "соцсети"]
rep_social = metric_report(soc["converted"], soc["p"])
```

### solution
```python
import numpy as np
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]

def metric_report(y, p, n_boot=200, seed=0):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        aucs.append(roc_auc_score(y[i], p[i]))
    lo, hi = np.percentile(aucs, [2.5, 97.5])
    return {"n": len(y), "positives": int(y.sum()), "auc": round(roc_auc_score(y, p), 3),
            "ci_low": round(float(lo), 3), "ci_high": round(float(hi), 3),
            "pred": round(float(p.mean()), 3), "fact": round(float(y.mean()), 3)}

rep_all = metric_report(live["converted"], live["p"])
soc = live[live["channel"] == "соцсети"]
rep_social = metric_report(soc["converted"], soc["p"])
wider = round((rep_social["ci_high"] - rep_social["ci_low"]) / (rep_all["ci_high"] - rep_all["ci_low"]), 1)
```

### explain
По всем заявкам: AUC 0.846, интервал 0.819–0.866. По соцсетям: 0.852, интервал 0.79–0.92 — почти втрое шире: 22 договора против 230. Точечные AUC почти равны, но второе число знает о мире гораздо меньше. А строки `pred` и `fact` в отчёте по соцсетям (0.025 против 0.068) — главная находка: функция-отчёт выводит её автоматически, без отдельного поиска. Такую функцию стоит держать в своём модуле и вызывать для каждой метрики, которую вы показываете людям.

## task: seg-toy | Игрушечный пример своими руками | warmup

Восемь заявок из двух каналов уже лежат в таблице `t`. Посчитайте `auc_all` — AUC по всем восьми заявкам и `auc_seg` — Series с AUC внутри каждого канала (индекс — канал). Округлите до 2 знаков. В `higher` сохраните `True`, если общий AUC выше AUC в каждом из каналов.

### starter
```python
import pandas as pd
from sklearn.metrics import roc_auc_score

t = pd.DataFrame({
    "channel": ["рекомендация"] * 4 + ["соцсети"] * 4,
    "p": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
    "deal": [1, 1, 0, 1, 0, 1, 0, 0],
})

```

### check
```python
import pandas as _pd
from sklearn.metrics import roc_auc_score as _auc
_t = _pd.DataFrame({"channel": ["рекомендация"] * 4 + ["соцсети"] * 4,
                    "p": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1], "deal": [1, 1, 0, 1, 0, 1, 0, 0]})
_a = _auc(_t['deal'], _t['p'])
assert close(need('auc_all'), _a, 0.006), f'auc_all = {need("auc_all")}, а нужно около {round(_a, 2)}: roc_auc_score(t["deal"], t["p"]).'
s = need('auc_seg', _pd.Series)
assert sorted(s.index) == ['рекомендация', 'соцсети'], f'Индекс auc_seg: {list(s.index)} — нужны два канала.'
for ch, g in _t.groupby('channel'):
    _v = _auc(g['deal'], g['p'])
    assert close(s[ch], _v, 0.006), f'{ch}: {s[ch]}, а нужно около {round(_v, 2)} — AUC только по заявкам этого канала.'
assert need('higher') == True, 'higher: общий AUC 0.81 выше, чем 0.67 в каждом канале, — нужно True.'
```

### hint
AUC внутри канала — та же функция, применённая к куску таблицы: `t.groupby("channel")[["deal", "p"]].apply(...)`, как функция `seg` в теории.

### hint
```python
auc_all = round(roc_auc_score(t["deal"], t["p"]), 2)
auc_seg = t.groupby("channel")[["deal", "p"]].apply(lambda g: roc_auc_score(g["deal"], g["p"])).round(2)
higher = bool(auc_all > auc_seg.max())
```

### solution
```python
import pandas as pd
from sklearn.metrics import roc_auc_score

t = pd.DataFrame({
    "channel": ["рекомендация"] * 4 + ["соцсети"] * 4,
    "p": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
    "deal": [1, 1, 0, 1, 0, 1, 0, 0],
})
auc_all = round(roc_auc_score(t["deal"], t["p"]), 2)
auc_seg = t.groupby("channel")[["deal", "p"]].apply(lambda g: roc_auc_score(g["deal"], g["p"])).round(2)
higher = bool(auc_all > auc_seg.max())
```

### explain
Внутри каждого канала AUC 0.67 (из трёх пар верно упорядочены две), а по всем заявкам — 0.81 (13 пар из 16). Все прогнозы рекомендаций выше всех прогнозов соцсетей, а договоров в рекомендациях три из четырёх против одного из четырёх. Пары «договор из рекомендаций — отказ из соцсетей» модель упорядочивает верно всегда, и они поднимают общий AUC. `lambda g: ...` — короткая функция в одну строку, то же, что `def seg(g): return ...`.

## task: rule-base | Модель против простого правила по каналам | base

Сравните модель с правилом «повторный клиент — первым» внутри каждого канала. Заявки мая–сентября с прогнозом `p` уже лежат в `live`. Сохраните `rule_auc` — AUC правила по всем заявкам (`repeat_client` вместо прогноза, 3 знака), Series `gain` (индекс — канал) — на сколько AUC модели выше AUC правила внутри канала (3 знака), и в `least` — канал, где модель добавляет к правилу меньше всего.

### setup
```python
import numpy as np
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]
```

### starter
```python
import pandas as pd
from sklearn.metrics import roc_auc_score
# готово, как в теории: d, model, live (заявки мая–сентября, столбец p — прогноз)

```

### check
```python
from sklearn.metrics import roc_auc_score as _auc
import pandas as _pd
L = live
_r = _auc(L['converted'], L['repeat_client'])
assert close(need('rule_auc'), _r, 0.0015), f'rule_auc = {need("rule_auc")}, а нужно около {round(_r, 3)}: roc_auc_score(live["converted"], live["repeat_client"]).'
_m = L.groupby('channel')[['converted', 'p']].apply(lambda g: _auc(g['converted'], g['p']))
_q = L.groupby('channel')[['converted', 'repeat_client']].apply(lambda g: _auc(g['converted'], g['repeat_client']))
_g = _m - _q
s = need('gain', _pd.Series)
assert sorted(s.index) == sorted(_g.index), f'Индекс gain: {list(s.index)} — нужны все шесть каналов.'
for ch in _g.index:
    assert not close(s[ch], -_g[ch], 0.0015), f'{ch}: {s[ch]} — знак наоборот: из AUC модели вычитают AUC правила.'
    assert close(s[ch], _g[ch], 0.0015), f'{ch}: gain = {s[ch]}, а нужно около {round(float(_g[ch]), 3)}.'
assert need('least') == _g.idxmin(), f'least = {need("least")!r}, а нужно {_g.idxmin()!r}: наименьший gain.'
```

### hint
AUC внутри канала — как в функции `seg` из теории, только отдельно для `p` и для `repeat_client`: `live.groupby("channel")[["converted", "p"]].apply(lambda g: roc_auc_score(g["converted"], g["p"]))`.

### hint
```python
m = live.groupby("channel")[["converted", "p"]].apply(lambda g: roc_auc_score(g["converted"], g["p"]))
r = live.groupby("channel")[["converted", "repeat_client"]].apply(lambda g: roc_auc_score(g["converted"], g["repeat_client"]))
gain = (m - r).round(3)
least = ...
```

### solution
```python
import pandas as pd
from sklearn.metrics import roc_auc_score

rule_auc = round(roc_auc_score(live["converted"], live["repeat_client"]), 3)
m = live.groupby("channel")[["converted", "p"]].apply(lambda g: roc_auc_score(g["converted"], g["p"]))
r = live.groupby("channel")[["converted", "repeat_client"]].apply(lambda g: roc_auc_score(g["converted"], g["repeat_client"]))
gain = (m - r).round(3)
least = gain.idxmin()
```

### explain
По всем заявкам правило даёт 0.671, модель — 0.846. Внутри каналов модель выше правила везде: на 0.16–0.22 в пяти каналах и только на 0.085 в рекомендациях. Там 37 % заявок — от повторных клиентов (в остальных каналах 10–15 %), и правило само по себе неплохо сортирует. Для отчёта это строка «С чем сравнить»: в рекомендациях выигрыш от модели скромный, и если модель там сломается, менеджеры почти не потеряют, переключившись на правило.

## task: report-text | Отчёт словами | base

Метрику мало посчитать — её надо написать так, чтобы из текста нельзя было сделать неверный вывод. Соберите f-строку `report` для канала «соцсети» по образцу из теории. В ней должны быть: число заявок и договоров, AUC (3 знака), 95 % интервал (2 знака, функция `auc_ci` из теории), средний прогноз и фактическая конверсия (3 знака). Например: `"Соцсети: AUC 0.852 (95 % ДИ 0.79–0.92) на 324 заявках, 22 договора. Прогноз 0.025 при факте 0.068."` — но числа должны браться из переменных, а не быть вписаны руками.

### setup
```python
import numpy as np
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
live = d[d["month"] >= 5].copy()
live["p"] = model.predict_proba(live[num + cat])[:, 1]
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
# готово, как в теории: d, model, live (заявки мая–сентября, столбец p — прогноз)

def auc_ci(y, p, n_boot=200, seed=0):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        aucs.append(roc_auc_score(y[i], p[i]))
    return np.percentile(aucs, [2.5, 97.5])

soc = live[live["channel"] == "соцсети"]

```

### check
```python
from sklearn.metrics import roc_auc_score as _auc
L = live[live['channel'] == 'соцсети']
r = need('report', str)
_must = {
    'число заявок': str(len(L)),
    'число договоров': str(int(L['converted'].sum())),
    'AUC': f"{_auc(L['converted'], L['p']):.3f}",
    'средний прогноз': f"{L['p'].mean():.3f}",
    'конверсия': f"{L['converted'].mean():.3f}",
    'нижняя граница ДИ': '0.79',
    'верхняя граница ДИ': '0.92',
}
for what, val in _must.items():
    assert val in r, f'В отчёте не нашёл {what} ({val}). Сейчас report = {r!r}'
assert '{' not in r, f'В строке остались фигурные скобки — не забыли букву f перед кавычками? report = {r!r}'
```

### hint
Все числа уже есть: `len(soc)`, `soc["converted"].sum()`, `roc_auc_score(soc["converted"], soc["p"])`, `soc["p"].mean()`, `soc["converted"].mean()` и `lo, hi = auc_ci(soc["converted"], soc["p"])`. Формат «3 знака» в f-строке — `{x:.3f}`.

### hint
```python
lo, hi = auc_ci(soc["converted"], soc["p"])
auc = roc_auc_score(soc["converted"], soc["p"])
report = (f"Соцсети: AUC {auc:.3f} (95 % ДИ {lo:.2f}–{hi:.2f}) на {len(soc)} заявках, "
          f"{...} договора. Прогноз {...:.3f} при факте {...:.3f}.")
```

### solution
```python
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

def auc_ci(y, p, n_boot=200, seed=0):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        aucs.append(roc_auc_score(y[i], p[i]))
    return np.percentile(aucs, [2.5, 97.5])

soc = live[live["channel"] == "соцсети"]
lo, hi = auc_ci(soc["converted"], soc["p"])
auc = roc_auc_score(soc["converted"], soc["p"])
report = (f"Соцсети: AUC {auc:.3f} (95 % ДИ {lo:.2f}–{hi:.2f}) на {len(soc)} заявках, "
          f"{soc['converted'].sum()} договора. Прогноз {soc['p'].mean():.3f} при факте {soc['converted'].mean():.3f}.")
print(report)
```

### explain
Получилось: «Соцсети: AUC 0.852 (95 % ДИ 0.79–0.92) на 324 заявках, 22 договора. Прогноз 0.025 при факте 0.068.» Одна строка закрывает три вопроса читателя: на скольких данных (22 договора — мало), насколько число может прыгать (интервал шириной 0.13) и можно ли верить вероятностям (нет: занижены почти втрое). Строку собирают кодом, а не переписывают руками: при следующем пересчёте все числа обновятся сами, и опечатка в отчёте не появится.
