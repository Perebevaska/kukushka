---
title: "Проект: разбор инцидента в сервисе модели"
files: [guests_churn.csv, service_log.jsonl]
revisions: {c1: content-v2}
lead: "9 ноября команда CRM получила жалобы на задержки и пропавшие предложения. Сначала исследуйте синтетический журнал 2–8 ноября. Отдельным этапом 1 декабря выполните ретроспективный эксперимент с двумя демонстрационными моделями, подготовьте рекомендацию и план проверки."
recap:
  - "Разбор инцидента начинают с картины по времени: что и когда изменилось (запросы, ошибки, время ответа по дням и часам)."
  - "Каждую аномалию разрезают по измерениям журнала: версия модели, клиент, текст ошибки, входные данные. Одна жалоба может скрывать несколько независимых причин."
  - "Самые опасные поломки — тихие: сервис отвечает 200, но вход изменился (средний чек в копейках). Их ловит только мониторинг входных данных."
  - "Направление экстраполяции линейной модели зависит от обученного веса; дерево может направлять два больших значения в один лист."
  - "Перед откатом проверяют, как старая версия поведёт себя на входах из журнала, — по журналу, пересчитав ответы."
  - "Итог разбора — хронология, причины, влияние на бизнес и план: что чинить у себя, что у клиентов, какие проверки добавить, чтобы не повторилось."
---

## Задача

> Коллеги, за прошлую неделю несколько жалоб на сервис оттока:
>
> 1. Продукт: «Приложение стало заметно тормозить на экране бонусов, примерно с середины недели».
> 2. Веб-команда: «С пятницы вечером сайт перестал показывать персональные предложения».
> 3. Маркетинг: «Всё ли в порядке с моделью? В новой версии приложения предложения видят как будто не те гости».
>
> Команда модели предлагает откатиться на версию 1.0, которая работала до 5 ноября без проблем. Прежде чем решать — разберитесь по журналу, что произошло, и дайте рекомендацию.
>
> *Руководитель направления CRM*

Что известно о сервисе:

- журнал `service_log.jsonl` — все запросы со 2 по 8 ноября 2026, в формате из раздела «Журнал сервиса» урока «Упаковка и запуск: окружение, Docker, расписание, журнал»;
- **5 ноября** выкатили модель **1.1** — лес вместо логистической регрессии 1.0 (AUC выше — как в разделе «Версии и что меняется для бизнеса» урока «Модель как артефакт: файл, паспорт, контрольный набор»);
- клиенты сервиса: мобильное приложение версии 3.1, новая версия приложения **3.2** (вышла 6 ноября) и сайт;
- SLO сервиса: p95 времени **успешных** запросов ≤ 100 мс; доля 500 от **всех** запросов дня ≤ 2 %. Отдельно измеряйте 422 / все и (422 + 500) / все. Для последнего показателя отметьте первый день, когда доля превысила 2 %.

## План

1. Картина по дням: запросы, ошибки, время ответа.
2. Тормоза: время ответа по версиям модели, проверка требования.
3. Сайт: ошибки 500 — с какого момента, у кого, почему.
4. Приложение 3.2: что изменилось во входных данных.
5. Декабрьский пересчёт на ноябрьских входах: сравнить решения демонстрационной v10 на исходном и исправленном среднем чеке.
6. Проверка входа, которая поймала бы проблему, и её цена.
7. Быстрее, но не хуже: можно ли ускорить 1.1.
8. Рекомендация: откатываться или нет и что чинить.

9 ноября 2026 года доступны сам журнал, статусы, версии и задержки. Поздний анализ проведите на **1 декабря 2026 года**. У анкет гостей признаки на 1 октября, а метка за следующие 60 дней созрела 30 ноября. В заготовках `v10` — учебная логистическая регрессия, `v11` — учебный лес из 150 деревьев; они обучены для позднего пересчёта всех исторических входов. Чтобы воспроизвести решения действительно развёрнутых 5 ноября версий, понадобились бы их исходные артефакты, паспорта с датами обучения и исторические данные с уже созревшей к тому моменту меткой либо журнал выданных решений.

**Что передать руководителю.** До выбора готовой рекомендации напишите собственную записку: дата первого наблюдаемого симптома, клиент и версия, пример поля и единица; числитель, знаменатель и период каждой доли; что наблюдалось, что вычислено позднее, какую гипотезу проверит владелец и по какому критерию можно выпускать изменение. Образец откройте после своей попытки.

::: quiz
После выпуска новой версии мобильного приложения выросла доля ответов 422 от него. Где искать причину в первую очередь?

- [x] Сравнить прежний и новый payload с действующим контрактом сервиса и историей версий проверки
  > 422 показывает отказ при проверке входа. Причину установят сравнение запроса и схемы и воспроизведение на конкретном поле.
- [ ] В модели: она стала хуже
  > Модель до этих запросов даже не доходит.
- [ ] В сервере: не хватает памяти
  > Тогда были бы 500 или таймауты.
- [ ] Ответы 422 — это нормально, ничего не делать
  > Единичные — нормально. Рост — сигнал, что что-то сломалось.
:::

## task: timeline | Шаг 1. Картина по дням | base

Прочитайте журнал в `log` (`ts` — дата-время). Постройте `daily` — DataFrame по датам со столбцами `n`, `share_500`, `share_422` (доли от всех запросов дня, 3 знака) и `p95_ms` (по успешным запросам, 1 знак). Сохраните `first_slow_day` — первую дату, когда `p95_ms > 100`, и `first_err_day` — первую дату, когда `share_500 > 0.02` (обе — строки `"ГГГГ-ММ-ДД"`).

### starter
```python
import json
import pandas as pd

```

### check
```python
import json as _j
import pandas as _pd
L = _pd.DataFrame([_j.loads(x) for x in open('service_log.jsonl', encoding='utf-8')]); L['ts'] = _pd.to_datetime(L['ts'])
L['d'] = L['ts'].dt.date
w = _pd.DataFrame({'n': L.groupby('d').size(),
                   'share_500': L.groupby('d')['status'].apply(lambda s: (s == 500).mean()).round(3),
                   'share_422': L.groupby('d')['status'].apply(lambda s: (s == 422).mean()).round(3),
                   'p95_ms': L[L['status'] == 200].groupby('d')['latency_ms'].quantile(0.95).round(1)})
l = need('log', _pd.DataFrame)
assert len(l) == len(L) and _pd.api.types.is_datetime64_any_dtype(l['ts']), 'log — весь журнал, ts — дата-время.'
d = need('daily', _pd.DataFrame)
assert len(d) == 7 and {'n', 'share_500', 'share_422', 'p95_ms'} <= set(d.columns), f'daily: 7 дней и 4 столбца. Сейчас {d.shape}, {list(d.columns)}.'

_dates = _pd.Index([_pd.Timestamp(v).date() for v in d.index])
assert _dates.is_unique and set(_dates)==set(w.index), 'Индекс daily — семь дат исходного журнала, по одной строке на дату.'
_aligned=d.copy(); _aligned.index=_dates; _aligned=_aligned.loc[w.index]
for c,tol in [('n',0),('share_500',.0011),('share_422',.0011),('p95_ms',.051)]:
    assert all(abs(a-b)<=tol for a,b in zip(_aligned[c],w[c])), f'{c}: значения должны совпадать по дате; перестановка одних подписей меняет смысл.'
assert str(need('first_slow_day')) == str(w.index[(w['p95_ms'] > 100).values][0]), f'first_slow_day = {need("first_slow_day")}.'
assert str(need('first_err_day')) == str(w.index[(w['share_500'] > 0.02).values][0]), f'first_err_day = {need("first_err_day")}.'
```

### hint
Чтение — как в задаче «Журнал в таблицу» урока «Упаковка и запуск: окружение, Docker, расписание, журнал». Для группировки удобно добавить столбец `log["date"] = log["ts"].dt.date`.

### hint
Доли кодов за день: `log.groupby("date")["status"].apply(lambda s: (s == 500).mean())`. p95 — по `log[log["status"] == 200]`.

### hint
Первая дата по условию: `str(daily.index[daily["p95_ms"] > 100][0])`.

### solution
```python
import json
import pandas as pd

with open("service_log.jsonl", encoding="utf-8") as f:
    log = pd.DataFrame([json.loads(line) for line in f])
log["ts"] = pd.to_datetime(log["ts"])
log["date"] = log["ts"].dt.date

daily = pd.DataFrame({
    "n": log.groupby("date").size(),
    "share_500": log.groupby("date")["status"].apply(lambda s: (s == 500).mean()).round(3),
    "share_422": log.groupby("date")["status"].apply(lambda s: (s == 422).mean()).round(3),
    "p95_ms": log[log["status"] == 200].groupby("date")["latency_ms"].quantile(0.95).round(1),
})
first_slow_day = str(daily.index[daily["p95_ms"] > 100][0])
first_err_day = str(daily.index[daily["share_500"] > 0.02][0])
print(daily)
print(first_slow_day, first_err_day)
```

### explain
С 5 ноября выросла задержка успешных запросов. Доля 500 впервые превысила 2 % 7 ноября (25/241). Более широкий показатель 422 + 500 впервые превысил 2 % 6 ноября: из 291 запроса шесть отклонены с 422, ни одного 500. Это разные показатели с общим знаменателем.

## task: slow | Шаг 2. Тормоза | base

Таблица `log` — в заготовке. Для успешных запросов посчитайте `lat` — DataFrame с индексом-версией модели и столбцами `p50`, `p95` (1 знак) и `n`. Сохраните `sla_ok` — словарь `{версия: p95 <= 100}` и `switch_time` — время первого запроса версии 1.1 (строка `"ГГГГ-ММ-ДД ЧЧ:ММ"`). Нарисуйте время ответа успешных запросов по времени (точками), цветом разделив версии.

### setup
```python
import json
import pandas as pd
with open("service_log.jsonl", encoding="utf-8") as _f:
    log = pd.DataFrame([json.loads(x) for x in _f])
log["ts"] = pd.to_datetime(log["ts"])
```

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt

ok = log[log["status"] == 200]

```

### check
```python
import pandas as _pd
l = need('log'); ok = l[l['status'] == 200]
g = ok.groupby('model_version')['latency_ms']
w = _pd.DataFrame({'p50': g.quantile(0.5).round(1), 'p95': g.quantile(0.95).round(1), 'n': g.size()})
t = need('lat', _pd.DataFrame)
assert list(t.index.astype(str)) == ['1.0', '1.1'], f'Индекс lat — версии модели: {list(t.index)}.'
for c in ['p50', 'p95', 'n']:
    assert all(abs(a - b) < 0.051 for a, b in zip(t[c].values, w[c].values)), f'{c}: {list(t[c])}, а нужно {list(w[c])}.'
s = {str(k): bool(v) for k, v in need('sla_ok', dict).items()}
assert s == {'1.0': True, '1.1': False}, f'sla_ok = {s}.'
assert need('switch_time') == l.loc[l['model_version'] == '1.1', 'ts'].min().strftime('%Y-%m-%d %H:%M'), f'switch_time = {need("switch_time")}.'
assert len(figs) >= 1, 'Нарисуйте время ответа по времени.'
assert len(ax_of(0).collections) >= 2, 'Нужны две группы точек — по одной на версию модели: ax.scatter(...) в цикле по версиям.'
```

### hint
`ok.groupby("model_version")["latency_ms"]` и от неё `.quantile(0.5)`, `.quantile(0.95)`, `.size()` — три Series, которые собираются в DataFrame.

### hint
График: в цикле по версиям `ax.scatter(part["ts"], part["latency_ms"], s=4, label=version)`; линия требования — `ax.axhline(100, color="red")`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

ok = log[log["status"] == 200]
g = ok.groupby("model_version")["latency_ms"]
lat = pd.DataFrame({"p50": g.quantile(0.5).round(1), "p95": g.quantile(0.95).round(1), "n": g.size()})
sla_ok = {v: bool(r["p95"] <= 100) for v, r in lat.iterrows()}
switch_time = log.loc[log["model_version"] == "1.1", "ts"].min().strftime("%Y-%m-%d %H:%M")
print(lat, sla_ok, switch_time, sep="\n")

fig, ax = plt.subplots(figsize=(10, 3.5))
for v, part in ok.groupby("model_version"):
    ax.scatter(part["ts"], part["latency_ms"], s=4, label=f"модель {v}")
ax.axhline(100, color="red", lw=1, label="требование p95")
ax.set_ylabel("мс"); ax.legend()
```

### explain
По журналу рост задержки совпал с началом версии 1.1 5 ноября около 10:00. Медиана успешных запросов выросла примерно втрое, p95 вышел за 100 мс. Число деревьев — одна из проверяемых гипотез. Чтобы отделить вычисление модели от очереди и нагрузки, сравните времена этапов при одних входах и нагрузке.

## task: web500 | Шаг 3. Ошибки сайта | base

Таблица `log` — в заготовке. Найдите ошибки 500: сохраните `err_by_client` — число ошибок 500 по клиентам (Series), `first_500` — время первой ошибки 500 (строка `"ГГГГ-ММ-ДД ЧЧ:ММ"`), `messages` — список уникальных текстов ошибок 500. Затем выясните, чего не хватает во входе: для запросов сайта посчитайте `has_ds_before` и `has_ds_after` — долю запросов, где в `payload` есть ключ `delivery_share`, до и после `first_500` (3 знака). В `web_fail_after` — долю ответов 500 у сайта после `first_500` (3 знака).

### setup
```python
import json
import pandas as pd
with open("service_log.jsonl", encoding="utf-8") as _f:
    log = pd.DataFrame([json.loads(x) for x in _f])
log["ts"] = pd.to_datetime(log["ts"])
```

### starter
```python
import pandas as pd

e500 = log[log["status"] == 500]

```

### check
```python
import pandas as _pd
l = need('log'); e = l[l['status'] == 500]
w = e['client'].value_counts()
g = need('err_by_client', _pd.Series)
assert dict(g) == dict(w), f'err_by_client = {dict(g)}.'
f0 = e['ts'].min()
assert need('first_500') == f0.strftime('%Y-%m-%d %H:%M'), f'first_500 = {need("first_500")}.'
assert sorted(need('messages', list)) == sorted(e['error'].unique()), f'messages = {need("messages")}.'
web = l[l['client'] == 'web']; has = web['payload'].apply(lambda p: 'delivery_share' in p)
b, a = round(has[web['ts'] < f0].mean(), 3), round(has[web['ts'] >= f0].mean(), 3)
assert close(need('has_ds_before'), b, 0.0011) and close(need('has_ds_after'), a, 0.0011), f'has_ds_before = {need("has_ds_before")}, has_ds_after = {need("has_ds_after")}: доли запросов сайта с ключом delivery_share.'
wf = round((web.loc[web['ts'] >= f0, 'status'] == 500).mean(), 3)
assert close(need('web_fail_after'), wf, 0.0011), f'web_fail_after = {need("web_fail_after")}.'
```

### hint
`e500["client"].value_counts()`; время первой ошибки — `e500["ts"].min()`; тексты — `e500["error"].unique()`.

### hint
Есть ли ключ в словаре входа: `web["payload"].apply(lambda p: "delivery_share" in p)` — получится столбец `True/False`; его `.mean()` — доля.

### hint
До и после — фильтры `web["ts"] < t0` и `web["ts"] >= t0`, где `t0 = e500["ts"].min()`.

### solution
```python
import pandas as pd

e500 = log[log["status"] == 500]
err_by_client = e500["client"].value_counts()
t0 = e500["ts"].min()
first_500 = t0.strftime("%Y-%m-%d %H:%M")
messages = list(e500["error"].unique())

web = log[log["client"] == "web"]
has_ds = web["payload"].apply(lambda p: "delivery_share" in p)
has_ds_before = round(has_ds[web["ts"] < t0].mean(), 3)
has_ds_after = round(has_ds[web["ts"] >= t0].mean(), 3)
web_fail_after = round((web.loc[web["ts"] >= t0, "status"] == 500).mean(), 3)
print(err_by_client, first_500, messages, has_ds_before, has_ds_after, web_fail_after, sep="\n")
```

### explain
Первый 500 — **суббота, 7 ноября, 18:02:31**. В жалобе прозвучала пятница. Все 89 ответов 500 относятся к web; проверьте `KeyError: delivery_share` и поле в исходных запросах до и после первой ошибки. Для установления точного события релиза потребуется история изменений клиента и сервиса.

## task: kopecks | Шаг 4. Что прислало приложение 3.2 | plus

Таблица `log` — в заготовке. Разложите `payload` успешных запросов в столбцы (`pd.json_normalize`) и добавьте клиента. Сохраните `check_by_client` — медиану `avg_check` по клиентам (Series), `ratio_32` — во сколько раз медиана у `"app 3.2"` больше, чем у `"app 3.1"` (округлить до целого), и `share_over_3000` — долю запросов с `avg_check > 3000` по клиентам (Series, 3 знака). Сравните со средним чеком в обучающих данных: `train_max` — максимальный `avg_check` в `guests_churn.csv`.

### setup
```python
import json
import pandas as pd
with open("service_log.jsonl", encoding="utf-8") as _f:
    log = pd.DataFrame([json.loads(x) for x in _f])
log["ts"] = pd.to_datetime(log["ts"])
```

### starter
```python
import pandas as pd

ok = log[log["status"] == 200].reset_index(drop=True)

```

### check
```python
import pandas as _pd
l = need('log'); ok = l[l['status'] == 200].reset_index(drop=True)
P = _pd.json_normalize(ok['payload'].tolist()); P['client'] = ok['client']
w = P.groupby('client')['avg_check'].median()
g = need('check_by_client', _pd.Series)
assert all(close(g[k], w[k], 0.51) for k in w.index), f'check_by_client:\n{g}\nа нужно\n{w}'
assert need('ratio_32') == round(w['app 3.2'] / w['app 3.1']), f'ratio_32 = {need("ratio_32")}.'
s = (P['avg_check'] > 3000).groupby(P['client']).mean().round(3)
gs = need('share_over_3000', _pd.Series)
assert all(close(gs[k], s[k], 0.0011) for k in s.index), f'share_over_3000:\n{gs}\nа нужно\n{s}'
assert close(need('train_max'), _pd.read_csv('guests_churn.csv')['avg_check'].max()), f'train_max = {need("train_max")}.'
```

### hint
`P = pd.json_normalize(ok["payload"].tolist())`, затем `P["client"] = ok["client"]` — индексы совпадают, потому что `ok` пронумерован заново (`reset_index`).

### hint
Медианы — `P.groupby("client")["avg_check"].median()`; доля больших чеков — `(P["avg_check"] > 3000).groupby(P["client"]).mean()`.

### solution
```python
import pandas as pd

ok = log[log["status"] == 200].reset_index(drop=True)
P = pd.json_normalize(ok["payload"].tolist())
P["client"] = ok["client"]
check_by_client = P.groupby("client")["avg_check"].median()
ratio_32 = round(check_by_client["app 3.2"] / check_by_client["app 3.1"])
share_over_3000 = (P["avg_check"] > 3000).groupby(P["client"]).mean().round(3)
train_max = pd.read_csv("guests_churn.csv")["avg_check"].max()
print(check_by_client, ratio_32, share_over_3000, train_max, sep="\n")
```

### explain
Медианный средний чек у приложения 3.2 — 34 100, ровно в 100 раз больше, чем у 3.1 и сайта. Это не богатые гости, а **копейки вместо рублей**: новая версия приложения стала передавать сумму в копейках. В обучающих данных самый большой средний чек — 661 ₽, так что 34 100 лежит далеко за пределами всего, что модель видела. Доля запросов с чеком больше 3000 не 100 %, а около 94 %: у остальных гостей чека просто нет (`null` — визитов не было). Сервис на все эти запросы ответил 200 — он не проверял диапазон. Это тихая поломка, и именно о ней третья жалоба.

## task: rollback | Шаг 5. А если откатиться? | plus

Демонстрационные модели `v10`, `v11` для пересчёта на 1 декабря и таблица успешных запросов с входами `P` (столбец `client` и все признаки) — в заготовке. Посчитайте решения (`proba >= 1/3`) обеих версий на **этих же входах как есть** и на исправленных (у `app 3.2` средний чек делится на 100). Сохраните `campaign_share` — DataFrame с индексом-клиентом и столбцами `v10_as_is`, `v10_fixed`, `v11_as_is`, `v11_fixed` (доли расчётных решений об участии среди успешных запросов данного клиента, 3 знака). Сохраните `rollback_harm` — число успешных запросов приложения 3.2, для которых 1 декабря демонстрационная v10 дала расчётное решение «включить» на исходном чеке и «не включать» после исправления единиц.

### setup
```python
import json
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
_g = pd.read_csv("guests_churn.csv")
_X = _g.drop(columns=["guest_id", "churned", "card_blocked"])
FEATURES = list(_X.columns)
_NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
def _mk(e):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), _NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), ["city", "fav_category"])])
    return Pipeline([("prep", pre), ("model", e)])
v10 = _mk(LogisticRegression(max_iter=2000)).fit(_X, _g["churned"])
v11 = _mk(RandomForestClassifier(150, min_samples_leaf=5, random_state=0)).fit(_X, _g["churned"])
with open("service_log.jsonl", encoding="utf-8") as _f:
    _log = pd.DataFrame([json.loads(x) for x in _f])
_ok = _log[_log["status"] == 200].reset_index(drop=True)
P = pd.json_normalize(_ok["payload"].tolist())
P["client"] = _ok["client"]
```

### starter
```python
import pandas as pd

fixed = P.copy()
fixed.loc[fixed["client"] == "app 3.2", "avg_check"] = fixed["avg_check"] / 100

```

### check
```python
import pandas as _pd
P0, F, a, b = need('P'), need('FEATURES'), need('v10'), need('v11')
fx = P0.copy(); m = fx['client'] == 'app 3.2'; fx.loc[m, 'avg_check'] = fx.loc[m, 'avg_check'] / 100
d = {'v10_as_is': a.predict_proba(P0[F])[:, 1] >= 1 / 3, 'v10_fixed': a.predict_proba(fx[F])[:, 1] >= 1 / 3,
     'v11_as_is': b.predict_proba(P0[F])[:, 1] >= 1 / 3, 'v11_fixed': b.predict_proba(fx[F])[:, 1] >= 1 / 3}
w = _pd.DataFrame(d).groupby(P0['client']).mean().round(3)
c = need('campaign_share', _pd.DataFrame)
assert list(c.columns) == list(w.columns), f'Столбцы: {list(c.columns)}, а нужно {list(w.columns)}.'
assert ((c.loc[w.index] - w).abs() < 0.0011).all().all(), f'campaign_share:\n{c}\nа нужно\n{w}'
h = int((d['v10_as_is'] & ~d['v10_fixed'] & m.values).sum())
assert need('rollback_harm') == h, f'rollback_harm = {need("rollback_harm")}, а нужно {h}.'
```

### hint
Решения: `v10.predict_proba(P[FEATURES])[:, 1] >= 1/3` — и так для четырёх сочетаний «модель × данные». Сложите четыре столбца `True/False` в один DataFrame.

### hint
Доли по клиентам: `pd.DataFrame({...}).groupby(P["client"]).mean().round(3)`.

### hint
В декабрьском эксперименте сосчитайте смены расчётного решения v10 с «включить» на «не включать» среди успешных запросов приложения 3.2 (`P["client"] == "app 3.2"`), где `v10_as_is` — `True`, а `v10_fixed` — `False`: `(as_is & ~fixed & mask).sum()`.

### solution
```python
import pandas as pd

fixed = P.copy()
fixed.loc[fixed["client"] == "app 3.2", "avg_check"] = fixed["avg_check"] / 100

dec = pd.DataFrame({
    "v10_as_is": v10.predict_proba(P[FEATURES])[:, 1] >= 1 / 3,
    "v10_fixed": v10.predict_proba(fixed[FEATURES])[:, 1] >= 1 / 3,
    "v11_as_is": v11.predict_proba(P[FEATURES])[:, 1] >= 1 / 3,
    "v11_fixed": v11.predict_proba(fixed[FEATURES])[:, 1] >= 1 / 3,
})
campaign_share = dec.groupby(P["client"]).mean().round(3)
is32 = (P["client"] == "app 3.2").values
rollback_harm = int((dec["v10_as_is"] & ~dec["v10_fixed"] & is32).sum())
print(campaign_share)
print(rollback_harm)
```

### explain
Знаменатель у app 3.2 — 353 успешных запроса от 331 уникального гостя; у 21 запроса средний чек отсутствует. В позднем сценарии для `v10` доля решений об участии составила 1,000 на исходных входах и 0,190 после исправления. В 286 запросах ошибочная единица добавила решение об участии. Для `v11` соответствующие доли — 0,252 и 0,258. Сравните решения для каждой строки и посчитайте изменения в каждую сторону: одинаковые доли могут скрывать разные адресаты. В данной регрессии вес стандартизованного чека положителен, поэтому ошибка ×100 резко повышает балл у части запросов. Дерево использует пороги и может отправить два больших значения в один лист. Для утверждения о фактических показах, людях или расходах нужны отдельные журналы предложений и использования скидок.

## task: guard | Шаг 6. Проверка, которая бы спасла | base

Таблица успешных запросов `P` (входы + `client`) — в заготовке. Здесь числовые типы уже проверены при разборе входа; эта функция проверяет диапазоны. В сыром API булевы значения, обязательность полей и типы проверяет схема. Напишите `range_problems(row)` — список нарушений диапазонов для одной строки входа: `avg_check` — пропуск или 50–3000, `delivery_share` — 0–1, `visits_90d` ≥ 0 (сообщения — любые строки, начинающиеся с имени поля). Примените ко всем строкам `P` и сохраните `would_reject` — долю запросов, которые получили бы 422, по клиентам (Series, 3 знака), `rejected_32` — сколько запросов приложения 3.2 было бы отклонено и `first_bad` — время первого такого запроса (строка `"ГГГГ-ММ-ДД ЧЧ:ММ"`, время — в столбце `ts`).

### setup
```python
import json
import pandas as pd
with open("service_log.jsonl", encoding="utf-8") as _f:
    _log = pd.DataFrame([json.loads(x) for x in _f])
_ok = _log[_log["status"] == 200].reset_index(drop=True)
P = pd.json_normalize(_ok["payload"].tolist())
P["client"] = _ok["client"]
P["ts"] = pd.to_datetime(_ok["ts"])
```

### starter
```python
import pandas as pd

def range_problems(row):
    problems = []
    ...
    return problems

```

### check
```python
import pandas as _pd
P0 = need('P')
f = need('range_problems')
def _rp(r):
    out = []
    v = r['avg_check']
    if not (_pd.isna(v) or 50 <= v <= 3000): out.append('avg_check')
    if not 0 <= r['delivery_share'] <= 1: out.append('delivery_share')
    if r['visits_90d'] < 0: out.append('visits_90d')
    return out
bad = P0.apply(lambda r: len(_rp(r)) > 0, axis=1)
w = bad.groupby(P0['client']).mean().round(3)
g = need('would_reject', _pd.Series)
assert all(close(g[k], w[k], 0.0011) for k in w.index), f'would_reject:\n{g}\nа нужно\n{w}'
assert need('rejected_32') == int((bad & (P0['client'] == 'app 3.2')).sum()), f'rejected_32 = {need("rejected_32")}.'
assert need('first_bad') == P0.loc[bad, 'ts'].min().strftime('%Y-%m-%d %H:%M'), f'first_bad = {need("first_bad")}.'
r0 = P0.iloc[0].copy(); r0['avg_check'] = float('nan')
assert f(r0) == [], 'Пропуск среднего чека — допустим (визитов не было): pd.isna(v).'
r1 = P0.iloc[0].copy(); r1['delivery_share'] = 3.0
assert any(str(x).startswith('delivery_share') for x in f(r1)), 'delivery_share = 3.0 — нарушение.'
for _visits, _delivery, _check in [(0, .5, 800), (-1, .5, 800), (-1, 3., 800), (-1, 3., 4000)]:
    _row = _pd.Series(dict(avg_check=_check, delivery_share=_delivery, visits_90d=_visits))
    _problems = f(_row)
    assert isinstance(_problems, list) and all(isinstance(v, str) for v in _problems), 'range_problems возвращает список строк с именами полей.'
    _expected = set(_rp(_row))
    assert all(any(v.startswith(k) for v in _problems) for k in _expected), f'Для {_row.to_dict()} нужны все нарушения: {sorted(_expected)}. Не прекращайте проверку после первого поля.'
    assert all(any(v.startswith(k) for k in _expected) for v in _problems), f'Для {_row.to_dict()} лишние нарушения: {_problems}; ноль визитов допустим.'
```

### hint
В строке таблицы пропуск чека — это `NaN`, а не `None`: проверяйте `pd.isna(row["avg_check"])`.

### hint
Отказ по строке: `bad = P.apply(lambda r: len(range_problems(r)) > 0, axis=1)`; доли по клиентам — `bad.groupby(P["client"]).mean()`.

### hint
Первое время: `P.loc[bad, "ts"].min().strftime("%Y-%m-%d %H:%M")`.

### solution
```python
import pandas as pd

def range_problems(row):
    problems = []
    v = row["avg_check"]
    if not (pd.isna(v) or 50 <= v <= 3000):
        problems.append("avg_check: ожидается 50–3000 ₽ или пропуск")
    if not 0 <= row["delivery_share"] <= 1:
        problems.append("delivery_share: ожидается доля 0–1")
    if row["visits_90d"] < 0:
        problems.append("visits_90d: ожидается ≥ 0")
    return problems

bad = P.apply(lambda r: len(range_problems(r)) > 0, axis=1)
would_reject = bad.groupby(P["client"]).mean().round(3)
rejected_32 = int((bad & (P["client"] == "app 3.2")).sum())
first_bad = P.loc[bad, "ts"].min().strftime("%Y-%m-%d %H:%M")
print(would_reject, rejected_32, first_bad, sep="\n")
```

### explain
Из 353 успешных запросов приложения 3.2 диапазон не прошли бы 332 (94,1 %), первый — 6 ноября в 07:03. Успешные запросы 3.1 и web этот фильтр пропускал. По журналу можно оценить число потенциальных отказов, а реальные показы и доход потребовали бы других наблюдений.

## task: faster | Шаг 7. Быстрее, но не хуже | star

В карточке даны `X_train, y_train, X_test, y_test` и `make(estimator)`. Какая учебная конфигурация подходит для последующей нагрузочной проверки? Обучите на `X_train` леса `RandomForestClassifier(n, min_samples_leaf=5, random_state=0)` (в конвейере `make`) с `n` из `[150, 60, 20]`. Для каждого посчитайте AUC на `X_test` (4 знака) и медиану времени `predict_proba` на одной строке по первым 40 строкам `X_test` (мс). Сохраните `speed` — DataFrame с индексом `n` и столбцами `auc`, `ms`; `best_small` — наименьшее `n`, у которого AUC не ниже AUC 150 деревьев более чем на 0.002, и `speedup` — во сколько раз `ms` у `best_small` меньше, чем у 150 деревьев.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
_g = pd.read_csv("guests_churn.csv")
X = _g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, _g["churned"], test_size=0.25, random_state=42, stratify=_g["churned"])
_NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
def make(e):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), _NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), ["city", "fav_category"])])
    return Pipeline([("prep", pre), ("model", e)])
```

### starter
```python
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

rows = []

```

### check
```python
import pandas as _pd
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import roc_auc_score as _auc
mk, Xt, yt, Xs, ys = need('make'), need('X_train'), need('y_train'), need('X_test'), need('y_test')
sp = need('speed', _pd.DataFrame)
assert sorted(int(i) for i in sp.index) == [20, 60, 150] and {'auc', 'ms'} <= set(sp.columns), f'speed: индекс 150, 60, 20 и столбцы auc, ms. Сейчас: {list(sp.index)}, {list(sp.columns)}.'
wa = {n: round(_auc(ys, mk(_RF(n, min_samples_leaf=5, random_state=0)).fit(Xt, yt).predict_proba(Xs)[:, 1]), 4) for n in [150, 60, 20]}
assert all(close(sp.loc[n, 'auc'], wa[n], 0.0012) for n in wa), f'auc: {dict(sp["auc"])}, а нужно {wa}.'
assert all(sp.loc[n, 'ms'] > 0 for n in wa), 'ms — положительное время в миллисекундах.'
bs = min(n for n in wa if wa[n] >= wa[150] - 0.002)
assert int(need('best_small')) == bs, f'best_small = {need("best_small")}, а нужно {bs}.'
assert close(need('speedup'), sp.loc[150, 'ms'] / sp.loc[bs, 'ms'], 1e-6), 'speedup = ms(150) / ms(best_small).'
```

### hint
Для каждого `n`: обучить, посчитать AUC на тесте, затем в цикле по 40 строкам замерить `predict_proba(X_test.iloc[[i]])` и взять `np.median` времён.

### hint
Таблица: список словарей `{"n": n, "auc": ..., "ms": ...}` → `pd.DataFrame(rows).set_index("n")`.

### hint
`best_small = min(n for n in speed.index if speed.loc[n, "auc"] >= speed.loc[150, "auc"] - 0.002)`; `speedup = speed.loc[150, "ms"] / speed.loc[best_small, "ms"]`.

### solution
```python
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

rows = []
for n in [150, 60, 20]:
    m = make(RandomForestClassifier(n, min_samples_leaf=5, random_state=0)).fit(X_train, y_train)
    auc = round(roc_auc_score(y_test, m.predict_proba(X_test)[:, 1]), 4)
    times = []
    for i in range(40):
        t0 = time.perf_counter()
        m.predict_proba(X_test.iloc[[i]])
        times.append((time.perf_counter() - t0) * 1000)
    rows.append({"n": n, "auc": auc, "ms": float(np.median(times))})
speed = pd.DataFrame(rows).set_index("n")
best_small = min(n for n in speed.index if speed.loc[n, "auc"] >= speed.loc[150, "auc"] - 0.002)
speedup = speed.loc[150, "ms"] / speed.loc[best_small, "ms"]
print(speed, best_small, round(speedup, 2), sep="\n")
```

### explain
В учебной выборке 60 деревьев проходят допуск по AUC относительно 150. Медиана отдельного вызова модели в миллисекундах характеризует локальное вычисление. Перед выпуском измерьте сетевой p95 всего запроса на стенде при сопоставимой нагрузке; решение о соблюдении SLO принимает команда по этому замеру.

## task: advice | Шаг 8. Рекомендация | base

Вернитесь к собственной записке. Для каждого действия назовите дату, пример запроса, единицу и знаменатель. Один HTTP-статус показывает, где начать диагностику. В `advice` запишите номер рекомендации, которую проверите по своим данным:

1. Откатиться на 1.0: она работала до 5 ноября без проблем.
2. Восстановить контракт сайта и приложения 3.2, проверить обязательные поля и диапазоны на сервере. Перед решением об откате сверить исходные ноябрьские артефакты. Кандидата с 60 деревьями проверить по качеству и сетевому p95 при сопоставимой нагрузке.
3. Ничего не менять в сервисе: попросить веб-команду вернуть `delivery_share`, остальное само пройдёт.
4. Откатить и приложение 3.2, и модель — к состоянию до 5 ноября.

### starter
```python
advice = ...
print(advice)
```

### check
```python
a = need('advice')
assert a in (1, 2, 3, 4), 'advice — номер варианта: 1, 2, 3 или 4.'
assert a != 1, 'В пересчёте 1 декабря демонстрационная v10 на исходных чеках дала решение об участии для 353 из 353 успешных запросов app 3.2. Для решения об откате проверьте исходные ноябрьские артефакты.'
assert a != 3, 'Сайт починится, но тормоза из шага 2 и копейки из шага 4 останутся, а следующую ошибку входа сервис снова пропустит молча.'
assert a != 4, 'Откат версий не восстанавливает отсутствующее поле сайта и проверку входа. Влияние изменения на задержку проверьте по сетевому p95 при сопоставимой нагрузке.'
assert a == 2
```

### hint
Пройдитесь по трём жалобам и шагу 5. Какой вариант закрывает все три проблемы и не создаёт новую?

### solution
```python
advice = 2
print(advice)
```

### explain
Вариант 2 объединяет исправление входа и проверку скорости перед выпуском. Обоснование сценария относится к повторному расчёту на исторических запросах после созревания меток.

## Итог: разбор инцидента

> **Сервис оттока. Журнал 2–8 ноября 2026 года; поздний модельный эксперимент — 1 декабря.**
>
> **Хронология**
> - 5.11, ~10:00 — выкатили модель 1.1 (лес из 150 деревьев). Время ответа выросло втрое, p95 ~135 мс при требовании 100 мс.
> - 6.11, утро — вышло приложение 3.2: средний чек передаётся в копейках (×100). Сервис отвечал 200, проверки диапазона не было.
> - 7.11, ~18:00 — сайт перестал передавать `delivery_share`. Почти все запросы сайта — ошибка 500 (`KeyError`), около 26 % всех запросов 8.11.
>
> **Влияние**
> - Задержка ответов сервиса возросла; для времени открытия экрана нужна клиентская телеметрия.
> - Первая наблюдаемая ошибка сайта — в субботу 7 ноября в 18:02:31. Для числа затронутых пользователей и показов потребуется журнал клиентского приложения.
> - В повторном расчёте на 353 успешных запросах app 3.2 от 331 гостя итог зависел от масштаба чека и конкретной модели. Сравните попарные решения по запросам. Фактическое число показов и стоимость акций журнал не содержит.
>
> **Рекомендация.** Сначала исправить единицы и проверку входа. Перед откатом проверить исходные артефакты двух выпусков на проблемных запросах, перед новой выкаткой — измерить p95 на стенде.
>
> **План**
> 1. Веб-команда — вернуть `delivery_share` в запросы (сегодня).
> 2. Команда приложения — передавать средний чек в рублях (ближайший релиз 3.2.1).
> 3. Команда модели:
>    - проверить обязательные поля и диапазоны; при повторе исторических входов guard отклонил бы 332 из 353 ранее успешных запросов app 3.2 по диапазону. В журнале новой версии следить за 422 по клиентам;
>    - лес из 60 деревьев прошёл заданный допуск по AUC на учебной выборке. На стенде сравнить качество и сетевой p95 с действующей версией при сопоставимой нагрузке, затем решить вопрос о выпуске;
>    - ежедневный отчёт: доля 422/500 по клиентам, p95 по версиям, медианы входных признаков по клиентам — с порогами и оповещением.
> 4. Отдельно: к каждой выкатке модели и клиентов — проверка контрольного набора и тесты входа (уроки «Модель как артефакт: файл, паспорт, контрольный набор» и «Сервис в работе: пакет, время ответа, FastAPI, тесты»).

::: tip
Разбор инцидента пишут **без поиска виноватых**: цель — понять, какой проверки не хватило, а не кто ошибся. Каждый пункт плана — это проверка, которая поймала бы проблему раньше. Такой документ команда перечитывает перед следующими выкатками.
:::

::: figure incident-timeline
Итог разбора на одной шкале: три проблемы начались в разные дни и у разных клиентов. Жалобы, которые казались одной поломкой модели, разошлись по трём полосам.
:::

::: figure extrapolation
Иллюстрация позднего пересчёта одного входа. Направление вклада стандартизованного чека определяется знаком веса в обученной регрессии. Для дерева два больших чека могут оказаться по одну сторону одних и тех же порогов.
:::
