---
title: "Сервис в работе: пакет, время ответа, FastAPI, тесты"
lead: "Обработчик с проверкой входа и кодами ответа готов — теперь доводим его до работы. Пакет запросов, в котором одна плохая строка не роняет остальные; время ответа в процентилях p50 и p95 и цена одиночного вызова против пакета; та же логика как веб-сервис на FastAPI и pydantic; тесты, которые ловят дыры в проверке до выкладки."
files: [guests_churn.csv]
recap:
  - "Пакет запросов обрабатывают по одному гостю и возвращают ответ на каждого в том же порядке: ошибки — внутри ответов, а не исключениями, поэтому одна плохая строка не роняет пакет."
  - "Время ответа меряют `time.perf_counter()` и описывают процентилями p50 и p95, а не средним. Пакетом модель считает на строку в десятки-сотни раз быстрее, чем по одному вызову: если решение не нужно «здесь и сейчас», считайте пакетом."
  - "FastAPI + pydantic превращают ту же логику в веб-сервис: модель запроса с ограничениями полей, проверка и ответ 422 — автоматически."
  - "Проверку входа покрывают тестами: список случаев «название, запрос, ожидаемый код» прогоняют после каждого изменения; каждую найденную поломку добавляют в список."
---

Обработчик `predict_one` — проверка входа, модель оттока гостей, ответ с кодом 200, 422 или 500 — мы собрали в уроке «Модель как сервис: запрос, проверка, ответ». Здесь доводим его до работы: пакет запросов, время ответа, веб-сервис на FastAPI и тесты проверки.

## Пакет запросов

Иногда приложение присылает сразу несколько гостей. Главное правило: **одна плохая строка не должна ронять весь пакет**. Обрабатываем каждого гостя отдельно и возвращаем ответ на каждого — в том же порядке.

```python
import pandas as pd

def predict_batch(payloads, predict_one):
    results = [predict_one(p) for p in payloads]
    return pd.DataFrame(results)

# демонстрация с «моделью-заглушкой»: вероятность = доля визитов без жалоб
def fake_predict_one(p):
    if "visits_90d" not in p:
        return {"status": 422, "errors": ["visits_90d: обязательное поле"]}
    return {"status": 200, "proba": round(1 / (1 + p["visits_90d"]), 3)}

res = predict_batch([{"visits_90d": 0}, {"city": "Уфа"}, {"visits_90d": 3}], fake_predict_one)
print(res)
print(res["status"].value_counts().to_dict())
```

**Что здесь происходит:**

- `[predict_one(p) for p in payloads]` — ответ на каждого гостя, ошибки — внутри ответов, а не исключениями.
- `pd.DataFrame(список_словарей)` — у успешных ответов есть `proba`, у ошибочных — `errors`; pandas заполнит отсутствующие значения `NaN`.

- Здесь вместо настоящей модели — функция-заглушка. Так удобно проверять обвязку отдельно от модели.

::: figure batch-isolation
Три запроса из примера: второй без `visits_90d` получает свой 422, а первый и третий — нормальные ответы. Пакет не падает целиком.
:::

{{practice: batch}}

## Сколько длится ответ

Для онлайн-сервиса скорость — часть качества: если экран бонусов ждёт ответа секунду, гость его закроет. Время меряют `time.perf_counter()` — это точный секундомер.

```python
import time
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
model = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X, g["churned"])

times = []
for i in range(100):
    row = X.iloc[[i]]
    t0 = time.perf_counter()
    model.predict_proba(row)
    times.append((time.perf_counter() - t0) * 1000)      # миллисекунды

t0 = time.perf_counter()
model.predict_proba(X.head(100))
batch_ms = (time.perf_counter() - t0) * 1000

print(f"по одному: p50 = {np.percentile(times, 50):.2f} мс, p95 = {np.percentile(times, 95):.2f} мс")
print(f"пакетом: {batch_ms / 100:.3f} мс на гостя")
```

**Что здесь происходит:**

- Засекаем время до и после вызова; разница, умноженная на 1000, — миллисекунды.
- `np.percentile(times, 50)` — **p50**, медиана: половина запросов быстрее. `np.percentile(times, 95)` — **p95**: 95 % запросов быстрее, 5 % — медленнее.

**Что получилось:** на один запрос уходят миллисекунды (в браузерном Python — чуть дольше, чем на сервере). А пакетом то же самое считается в десятки-сотни раз быстрее на гостя: львиная доля времени — накладные расходы на сам вызов (проверки sklearn, создание таблицы), а не арифметика. Вывод: если решение не нужно «здесь и сейчас», считайте пакетом.

::: note Почему процентили, а не среднее
Время ответа почти всегда имеет «хвост»: большинство запросов быстрые, но изредка какой-то тормозит в десять раз (сборка мусора, соседняя задача на сервере). Среднее этот хвост размазывает, а пользователь его замечает. Поэтому требования пишут так: «p95 не больше 100 мс» — то есть 95 % гостей ждут не дольше 100 мс.
:::

::: figure latency-tail
Условные 100 запросов: 92 быстрых около 8 мс и 8 медленных. Медиана и среднее говорят «быстро», а p95 попадает в хвост — туда, где гость уже ждёт и раздражается.
:::

::: tip Аналогия
Время ответа — как очередь в кофейне: если в среднем гость ждёт две минуты, это ничего не говорит о том, что каждый двадцатый ждёт десять. Жалобы пишут именно эти «каждые двадцатые», поэтому управляющий смотрит не на среднее, а на «95 % гостей ждут не дольше N минут».
:::

::: quiz
Почему требование к скорости сервиса формулируют как «p95 не больше 100 мс», а не через среднее время?

- [x] У времени ответа есть хвост редких медленных запросов, который среднее размазывает
  > А гость этот хвост замечает. p95 прямо говорит, что 95 % запросов укладываются в порог. Процентиль описывает опыт большинства гостей, включая заметную долю медленных случаев, а не «среднюю температуру».
- [ ] Среднее время в миллисекундах посчитать нельзя
  > Посчитать можно, просто оно плохо описывает хвост медленных запросов.
- [ ] p95 — это 95 % от среднего времени ответа
  > p95 — процентиль: значение, быстрее которого 95 % запросов. С долей от среднего оно не связано.
- [ ] p95 всегда меньше среднего, поэтому требование получается мягче и его легче выполнить
  > Наоборот: при «хвосте» p95 обычно заметно больше и среднего, и медианы — требование по нему строже.
:::

{{practice: latency}}

## Тот же сервис на FastAPI

Обработчик и проверка входа, которые мы написали, — обычные функции. Чтобы приложение могло вызвать их по сети, их оборачивают в веб-сервис. Самый популярный инструмент для этого в Python — **FastAPI**. В браузере его не запустить, поэтому код ниже — для вашего компьютера.

Сначала несколько слов о том, как устроен веб-сервис, — без этого код читается как заклинание:

- **Веб-сервис** — программа, которая запущена и ждёт запросов по сетевому **адресу**. Адрес состоит из компьютера и порта: `127.0.0.1` — это «этот же компьютер», а **порт** `8000` — номер «двери», за которой слушает именно наш сервис (на одном компьютере их может быть много, у каждого своя дверь).
- **Путь** — часть адреса после порта: `http://127.0.0.1:8000/predict`. У одного сервиса может быть несколько путей, например `/predict` и `/docs`.
- Приложение шлёт **запрос**. У запроса есть метод: **GET** — «дай страницу», **POST** — «вот данные, обработай». Мы шлём анкету гостя в JSON, поэтому нужен POST. Сервис отвечает JSON-текстом и кодом из раздела «Коды ответа» урока «Модель как сервис: запрос, проверка, ответ».
- `@app.post("/predict")` над функцией — **декоратор**: строка с `@`, которая стоит прямо над `def` и что-то делает с функцией. Здесь она регистрирует функцию в приложении: «на POST-запрос по пути `/predict` вызывай меня». Саму функцию вызывает FastAPI, а не вы.
- **uvicorn** — программа, которая запускает приложение FastAPI и держит его включённым: принимает запросы на порту и передаёт их вашим функциям. Команда `uvicorn service:app --port 8000` значит «возьми объект `app` из файла `service.py` и слушай порт 8000».

```python static
# uv add fastapi uvicorn scikit-learn pandas joblib
# файл service.py; запуск: uv run uvicorn service:app --port 8000
import json
from typing import Literal, Optional

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

model = joblib.load("models/churn/1.0/model.joblib")            # загружается один раз при старте
card = json.load(open("models/churn/1.0/card.json", encoding="utf-8"))

class Guest(BaseModel):                                          # контракт запроса
    city: Literal["Казань", "Пермь", "Тюмень", "Уфа"]
    fav_category: Literal["кофе", "не кофе", "еда"]
    tenure_months: int = Field(ge=1, le=120)
    app: int = Field(ge=0, le=1)
    visits_90d: int = Field(ge=0)
    days_since_last: int = Field(ge=0, le=3650)
    avg_check: Optional[float] = Field(ge=50, le=3000)          # Optional — может быть null
    delivery_share: float = Field(ge=0, le=1)
    promo_used: int = Field(ge=0)
    complaints: int = Field(ge=0)

app = FastAPI(title="Отток гостей «Зерна»")

@app.post("/predict")
def predict(guest: Guest):
    row = pd.DataFrame([guest.model_dump()])[card["features"]]
    p = float(model.predict_proba(row)[0, 1])
    return {"proba": round(p, 3), "in_campaign": p >= card["threshold"], "model_version": card["version"]}
```

**Что здесь происходит:**

- `class Guest(BaseModel)` — описание запроса библиотекой **pydantic**: каждое поле с типом и ограничениями. `Field(ge=0)` — «больше или равно 0» (*greater or equal*), `le` — «меньше или равно». `Literal[...]` — только перечисленные значения. Это та же таблица контракта, только записанная кодом.
- `app = FastAPI(...)` — само приложение. `@app.post("/predict")` — декоратор: FastAPI будет вызывать `predict` на каждый POST-запрос по пути `/predict`.
- `guest: Guest` — FastAPI сам прочитает JSON, проверит его по `Guest` и при нарушении вернёт **422** со списком ошибок — функция `predict` даже не вызовется. Проверку руками писать не нужно.
- Модель загружается **один раз** при старте сервиса, а не на каждый запрос: загрузка файла — самая медленная часть.
- Ошибка внутри `predict` автоматически превращается в ответ **500**.

Запустите сервис командой из комментария в начале файла и, не закрывая этот терминал, проверьте его из второго терминала или из Python. `requests.post(адрес, json=словарь)` отправляет словарь как JSON-тело POST-запроса — так же, как это сделает приложение:

```python static
import requests   # uv add requests
r = requests.post("http://127.0.0.1:8000/predict", json={
    "city": "Пермь", "fav_category": "кофе", "tenure_months": 12, "app": 0, "visits_90d": 4,
    "days_since_last": 8, "avg_check": 446, "delivery_share": 0.04, "promo_used": 1, "complaints": 0})
print(r.status_code, r.json())
```

А по адресу `http://127.0.0.1:8000/docs` FastAPI сам построит страницу документации: все поля, их ограничения и кнопку «попробовать». Её и отдают разработчикам приложения.

::: deep
Pydantic отличается от нашей ручной проверки в мелочах. Например, по умолчанию он **приводит** типы: строку `"12"` для поля `int` примет как число 12, а `true` — как 1. Чтобы запретить это, в модели включают строгий режим (`model_config = {"strict": True}`). Решите заранее, что для вашего сервиса правильнее, и запишите в документацию.
:::

## Тесты сервиса

Проверка входа — код, в котором легко ошибиться. Поэтому для неё пишут **тесты**: набор запросов с ожидаемым результатом. Их запускают после каждого изменения.

```python
def check_status(predict_one, cases):
    failed = []
    for name, payload, expected in cases:
        got = predict_one(payload)["status"]
        if got != expected:
            failed.append((name, expected, got))
    return failed

def toy_predict(p):                       # игрушечный сервис: требует только visits_90d ≥ 0
    v = p.get("visits_90d")
    if not isinstance(v, int) or v < 0:
        return {"status": 422}
    return {"status": 200}

cases = [
    ("нормальный", {"visits_90d": 3}, 200),
    ("отрицательные визиты", {"visits_90d": -1}, 422),
    ("визиты строкой", {"visits_90d": "3"}, 422),
    ("визиты True", {"visits_90d": True}, 422),
]
print(check_status(toy_predict, cases))
```

Тест «визиты True» не прошёл: `isinstance(True, int)` — та самая ловушка из раздела «Проверка входа» урока «Модель как сервис: запрос, проверка, ответ». Без теста её бы никто не заметил, пока приложение не прислало бы `true`. В рабочих проектах тесты пишут в отдельных файлах для **pytest** — функции с именами `test_...` и `assert` внутри; запуск — `uv run pytest`.

{{practice: tests}}

## Практика

## task: batch | Пакет без падений | base

Готовая `predict_one` — в заготовке (полная версия: проверка + модель). В `requests` — 50 запросов, среди которых есть плохие. Напишите `predict_batch(payloads)`, возвращающий DataFrame ответов в том же порядке, и примените: `res`. Сохраните `status_counts` — словарь `{код: число}` и `bad_fields` — Series: сколько раз каждое поле встречается в ошибках 422 (поле — часть строки ошибки до двоеточия), по убыванию.

### setup
```python
import random
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
_g = pd.read_csv("guests_churn.csv")
_X = _g.drop(columns=["guest_id", "churned", "card_blocked"])
_NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
_pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), _NUM),
                          ("cat", OneHotEncoder(handle_unknown="ignore"), ["city", "fav_category"])])
model = Pipeline([("prep", _pre), ("model", LogisticRegression(max_iter=2000))]).fit(_X, _g["churned"])
CARD = {"version": "1.0", "features": list(_X.columns), "threshold": 1 / 3}
def validate(p):
    e = [f"{f}: обязательное поле" for f in CARD["features"] if f not in p]
    if "visits_90d" in p and not (type(p["visits_90d"]) is int and p["visits_90d"] >= 0):
        e.append("visits_90d: ожидается целое ≥ 0")
    if "delivery_share" in p and not (type(p["delivery_share"]) in (int, float) and 0 <= p["delivery_share"] <= 1):
        e.append("delivery_share: ожидается доля 0–1")
    return e
def predict_one(payload):
    errors = validate(payload)
    if errors:
        return {"status": 422, "errors": errors}
    try:
        p = float(model.predict_proba(pd.DataFrame([payload])[CARD["features"]])[0, 1])
    except Exception as e:
        return {"status": 500, "errors": [f"{type(e).__name__}: {e}"]}
    return {"status": 200, "proba": round(p, 3), "in_campaign": p >= CARD["threshold"], "model_version": "1.0"}
_rnd = random.Random(7)
requests = []
for _r in _X.head(50).to_dict("records"):
    _r = {k: (None if isinstance(v, float) and v != v else v) for k, v in _r.items()}
    for k in ["tenure_months", "app", "visits_90d", "days_since_last", "promo_used", "complaints"]:
        _r[k] = int(_r[k])
    _u = _rnd.random()
    if _u < 0.12:
        _r["delivery_share"] = round(_r["delivery_share"] * 100, 1) + 1
    elif _u < 0.2:
        _r["visits_90d"] = -1
    elif _u < 0.24:
        _r.pop("city")
    requests.append(_r)
```

### starter
```python
import pandas as pd

def predict_batch(payloads):
    ...

res = predict_batch(requests)

```

### check
```python
import pandas as _pd
f, po, rq = need('predict_batch'), need('predict_one'), need('requests')
w = _pd.DataFrame([po(p) for p in rq])
r = need('res', _pd.DataFrame)
assert len(r) == 50 and list(r['status']) == list(w['status']), 'res — ответы predict_one на каждый запрос, в том же порядке.'
sc = {int(k): int(v) for k, v in need('status_counts', dict).items()}
assert sc == {int(k): int(v) for k, v in w['status'].value_counts().items()}, f'status_counts = {sc}.'
errs = [e.split(':')[0] for es in w.loc[w['status'] == 422, 'errors'] for e in es]
wb = _pd.Series(errs).value_counts()
b = need('bad_fields', _pd.Series)
assert dict(b) == dict(wb), f'bad_fields:\n{b}\nа нужно\n{wb}'
assert list(b.values) == sorted(b.values, reverse=True), 'bad_fields — по убыванию.'
```

### hint
`predict_batch` — одна строка: список ответов → `pd.DataFrame(...)`. Коды: `res["status"].value_counts()` → `.to_dict()`.

### hint
Поля из ошибок: пройдите по спискам `errors` у строк со статусом 422 и возьмите `e.split(":")[0]` у каждой строки ошибки. Затем `pd.Series(список).value_counts()`.

### hint
```python
fields = [e.split(":")[0] for errs in res.loc[res["status"] == 422, "errors"] for e in errs]
bad_fields = pd.Series(fields).value_counts()
```

### solution
```python
import pandas as pd

def predict_batch(payloads):
    return pd.DataFrame([predict_one(p) for p in payloads])

res = predict_batch(requests)
status_counts = {int(k): int(v) for k, v in res["status"].value_counts().items()}
fields = [e.split(":")[0] for errs in res.loc[res["status"] == 422, "errors"] for e in errs]
bad_fields = pd.Series(fields).value_counts()
print(status_counts)
print(bad_fields)
```

### explain
Из 50 запросов 15 плохих — почти каждый третий, но остальные получили нормальные ответы — пакет не упал. А разбивка ошибок по полям сразу показывает, где у клиента проблема: чаще всего ломается `delivery_share` — похоже на проценты вместо доли. Это и есть ценность понятных сообщений об ошибках: без них в журнале было бы «что-то не так в 10 запросах».

## task: latency | Время ответа | plus

Модель `model` и таблица `X` — в заготовке. Замерьте время `model.predict_proba` на одной строке для первых 200 гостей (по одному вызову на гостя) и время одного вызова на всех 200 сразу. Сохраните `times` — список из 200 времён в миллисекундах, `p50`, `p95` (миллисекунды, `np.percentile`), `mean_ms` — среднее, `batch_per_row` — время пакета, делённое на 200, и `speedup` — во сколько раз пакет быстрее на строку (`p50 / batch_per_row`).

### setup
```python
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
_g = pd.read_csv("guests_churn.csv")
X = _g.drop(columns=["guest_id", "churned", "card_blocked"])
_NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
_pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), _NUM),
                          ("cat", OneHotEncoder(handle_unknown="ignore"), ["city", "fav_category"])])
model = Pipeline([("prep", _pre), ("model", LogisticRegression(max_iter=2000))]).fit(X, _g["churned"])
```

### starter
```python
import time
import numpy as np

times = []

```

### check
```python
import numpy as _np
t = need('times', list)
assert len(t) == 200 and all(x > 0 for x in t), 'times — 200 положительных времён в миллисекундах (по одному на гостя).'
assert max(t) < 5000, 'Похоже, время в секундах×1000×1000 или накоплено: каждое — (perf_counter() после − до) × 1000.'
assert close(need('p50'), _np.percentile(t, 50), 1e-6) and close(need('p95'), _np.percentile(t, 95), 1e-6), 'p50, p95 — np.percentile(times, 50) и 95.'
assert close(need('mean_ms'), _np.mean(t), 1e-6), 'mean_ms — np.mean(times).'
assert need('p95') >= need('p50'), 'p95 не может быть меньше p50.'
assert need('batch_per_row') > 0 and close(need('speedup'), need('p50') / need('batch_per_row'), 1e-6), 'speedup = p50 / batch_per_row.'
assert need('speedup') > 3, f'speedup = {need("speedup")}: пакет должен быть заметно быстрее. Проверьте, что пакет — один вызов на X.head(200).'
```

### hint
Шаблон замера: `t0 = time.perf_counter()` → действие → `(time.perf_counter() - t0) * 1000`. Одна строка таблицы как таблица — `X.iloc[[i]]` (двойные скобки!).

### hint
В цикле по `i in range(200)` замеряйте и добавляйте в `times`. Пакет — один замер вокруг `model.predict_proba(X.head(200))`.

### hint
`p50, p95 = np.percentile(times, 50), np.percentile(times, 95)`; `batch_per_row = batch_ms / 200`; `speedup = p50 / batch_per_row`.

### solution
```python
import time
import numpy as np

times = []
for i in range(200):
    row = X.iloc[[i]]
    t0 = time.perf_counter()
    model.predict_proba(row)
    times.append((time.perf_counter() - t0) * 1000)

t0 = time.perf_counter()
model.predict_proba(X.head(200))
batch_ms = (time.perf_counter() - t0) * 1000

p50, p95 = np.percentile(times, 50), np.percentile(times, 95)
mean_ms = np.mean(times)
batch_per_row = batch_ms / 200
speedup = p50 / batch_per_row
print(f"p50 {p50:.2f} мс, p95 {p95:.2f} мс, среднее {mean_ms:.2f} мс, пакет {batch_per_row:.4f} мс/строку, ×{speedup:.0f}")
```

### explain
Числа зависят от компьютера и меняются от запуска к запуску — это нормально для замеров времени. Устойчивы соотношения: p95 выше p50, а пакет быстрее одиночных вызовов в десятки-сотни раз. Среднее и медиана у вас, скорее всего, почти равны: в браузере на свободной машине хвост короткий. Длинный хвост, о котором говорит заметка «Почему процентили, а не среднее», появляется под нагрузкой — когда сервис обрабатывает много запросов одновременно и они ждут друг друга. Типичная ошибка — `X.iloc[i]` с одинарными скобками: получится Series, а не таблица из одной строки, и модель откажется её принимать.

## task: tests | Найти дыру в проверке | plus

В заготовке — функция `validate_v0` (её написал коллега) и список тестовых случаев `cases`: `(название, запрос, ожидаемый статус)`. Статус по проверке: 422, если `validate_v0` вернула ошибки, иначе 200. Прогоните все случаи и сохраните `failed` — список названий случаев, где статус не совпал с ожидаемым. Затем напишите исправленную `validate_v1` (на основе `validate_v0`), которая проходит все случаи, — `failed_v1` должен быть пустым.

### setup
```python
GOOD = {"city": "Пермь", "tenure_months": 12, "app": 0, "visits_90d": 4, "days_since_last": 8,
        "avg_check": 446, "delivery_share": 0.04, "fav_category": "кофе", "promo_used": 1, "complaints": 0}
def validate_v0(p):
    errors = []
    for f in GOOD:
        if f not in p:
            errors.append(f"{f}: обязательное поле")
    for f in ["tenure_months", "app", "visits_90d", "days_since_last", "promo_used", "complaints"]:
        if f in p and (not isinstance(p[f], int) or p[f] < 0):
            errors.append(f"{f}: ожидается целое ≥ 0")
    if "delivery_share" in p and not 0 <= p["delivery_share"] <= 100:
        errors.append("delivery_share: ожидается доля")
    if "avg_check" in p and p["avg_check"] is not None and p["avg_check"] < 50:
        errors.append("avg_check: слишком мал")
    return errors
cases = [
    ("норма", GOOD, 200),
    ("чек не указан", dict(GOOD, avg_check=None), 200),
    ("визиты −1", dict(GOOD, visits_90d=-1), 422),
    ("нет города", {k: v for k, v in GOOD.items() if k != "city"}, 422),
    ("app = True", dict(GOOD, app=True), 422),
    ("доставка в процентах", dict(GOOD, delivery_share=40), 422),
    ("чек в копейках", dict(GOOD, avg_check=44600), 422),
    ("доля доставки 1.0", dict(GOOD, delivery_share=1.0), 200),
    ("стаж 0 месяцев", dict(GOOD, tenure_months=0), 422),
]
```

### starter
```python
def status_of(validate, payload):
    return 422 if validate(payload) else 200

failed = ...

def validate_v1(p):
    ...

failed_v1 = [name for name, p, exp in cases if status_of(validate_v1, p) != exp]
print(failed, failed_v1)
```

### check
```python
v0, cs = need('validate_v0'), need('cases')
st = lambda v, p: 422 if v(p) else 200
w = [n for n, p, e in cs if st(v0, p) != e]
assert need('failed', list) == w, f'failed = {need("failed")}, а нужно {w}.'
v1 = need('validate_v1')
assert [n for n, p, e in cs if st(v1, p) != e] == [], 'validate_v1 должна проходить все случаи.'
assert need('failed_v1', list) == [], 'failed_v1 должен быть пустым.'
G = need('GOOD')
assert st(v1, dict(G, complaints=True)) == 422 and st(v1, dict(G, app=5)) == 422, 'Проверьте и другие поля: complaints=True и app=5 тоже должны давать 422.'
```

### hint
Сначала `failed` — то же списковое выражение, что для `failed_v1`, только с `validate_v0`. Посмотрите на список: каждая не прошедшая строка подсказывает, какую проверку исправить.

### hint
Сравните случаи из `failed` с таблицей контракта (раздел «Проверка входа» урока «Модель как сервис: запрос, проверка, ответ»): у каких полей границы в `validate_v0` другие или их нет вовсе? И что будет с `isinstance(True, int)`?

### hint
Четыре дыры: `bool` проходит как `int`; доля доставки проверяется до 100, а не до 1; у чека нет верхней границы; у стажа и `app` нет своих диапазонов (стаж от 1, `app` — 0 или 1). Проще всего: скопировать `validate_v0` и поправить — `isinstance(p[f], bool)` как отдельное условие ошибки, `0 <= ... <= 1`, `50 <= чек <= 3000`, словарь нижних/верхних границ для целых полей.

### solution
```python
def status_of(validate, payload):
    return 422 if validate(payload) else 200

failed = [name for name, p, exp in cases if status_of(validate_v0, p) != exp]

RANGES = {"tenure_months": (1, 120), "app": (0, 1), "visits_90d": (0, None),
          "days_since_last": (0, 3650), "promo_used": (0, None), "complaints": (0, None)}

def validate_v1(p):
    errors = []
    for f in GOOD:
        if f not in p:
            errors.append(f"{f}: обязательное поле")
    for f, (lo, hi) in RANGES.items():
        if f not in p:
            continue
        v = p[f]
        if not isinstance(v, int) or isinstance(v, bool):
            errors.append(f"{f}: ожидается целое число")
        elif v < lo or (hi is not None and v > hi):
            errors.append(f"{f}: вне диапазона")
    if "delivery_share" in p and not 0 <= p["delivery_share"] <= 1:
        errors.append("delivery_share: ожидается доля 0–1")
    if "avg_check" in p and p["avg_check"] is not None and not 50 <= p["avg_check"] <= 3000:
        errors.append("avg_check: ожидается 50–3000")
    return errors

failed_v1 = [name for name, p, exp in cases if status_of(validate_v1, p) != exp]
print(failed, failed_v1)
```

### explain
Четыре из девяти случаев прошли «не туда», и каждый — реальный инцидент в будущем: `True` вместо 0/1, проценты вместо доли, копейки вместо рублей, новичок со стажем 0. Тесты стоят пять минут, а находят такое до выкладки. Хорошая привычка: каждый раз, когда в работе находится новая поломка, добавлять её в `cases` — чтобы она не вернулась.
