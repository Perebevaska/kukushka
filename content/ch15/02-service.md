---
title: "Модель как сервис: запрос, проверка, ответ"
files: [guests_churn.csv]
lead: "Приложение «Зерна» хочет спрашивать модель про одного гостя прямо в момент, когда он открывает экран бонусов. Значит, модель должна стать сервисом: принимать запрос в JSON, проверять его и отвечать понятным кодом, а не падать от кривых данных. Строим такой обработчик по шагам как обычную функцию Python. Пакет запросов, время ответа, FastAPI и тесты — в следующем уроке."
recap:
  - "Онлайн-режим — ответ на один запрос сразу; пакетный — расчёт по всей таблице по расписанию. Модель в обоих режимах одна, различается обвязка; онлайн нужен, когда решение принимается «здесь и сейчас»."
  - "Запрос и ответ передают в JSON: `json.loads(текст)` → словарь, `json.dumps(словарь, ensure_ascii=False)` → текст."
  - "Обработчик = проверка входа → подготовка строки → модель → ответ. Ответ всегда одного формата: `status` и либо результат, либо список ошибок."
  - "Коды: 200 — всё хорошо, 400 — не JSON, 422 — JSON, но данные не прошли проверку (виноват клиент), 500 — сломался сам сервис."
  - "`True` в Python — тоже `int`: в проверке типа отсекайте `bool` явно."
---

## Два режима работы модели

В уроке «Модель как артефакт: файл, паспорт, контрольный набор» модель отвечала на всю таблицу сразу: раз в неделю берём выгрузку гостей, считаем вероятности, отдаём список в CRM. Это **пакетный режим** (batch). Но есть задачи, где ответ нужен про одного гостя и немедленно:

- гость открыл в приложении экран бонусов — показать ли ему предложение «вернись за 200 ₽»?
- бариста пробивает заказ — подсказать ли «предложите карту лояльности»?

Это **онлайн-режим**: приходит запрос про одного гостя — через десятки миллисекунд уходит ответ.

| | Пакетный | Онлайн |
|---|---|---|
| Когда считаем | по расписанию (каждый понедельник) | в момент запроса |
| Сколько строк | все сразу | одна |
| Что важно | чтобы отработал до утра | чтобы ответил быстро и не упал |
| Чем запускается | скрипт по расписанию | веб-сервис, к которому обращается приложение |
| Пример в «Зерне» | список гостей для рассылки | бонус на экране приложения |

Модель в обоих режимах одна и та же — тот же конвейер из прошлого урока. Различается обвязка вокруг неё. Этот урок — про онлайн-обвязку.

::: figure batch-vs-online
Сверху — пакетный режим: выгрузка всех гостей по расписанию, модель, список в CRM. Снизу — онлайн: один гость в запросе, проверка входа, та же модель, ответ за миллисекунды.
:::

::: sql
Аналогия: пакетный режим — это `INSERT INTO campaign SELECT ... FROM guests` раз в неделю. Онлайн — это хранимая процедура `get_churn(@guest)`, которую приложение вызывает на каждом открытии экрана. Логика одна, а требования к скорости и к обработке ошибок — разные.
:::

## JSON: язык запросов и ответов

Приложение написано не на Python, поэтому общаться с моделью оно будет текстом в формате **JSON** — тем же, в котором мы сохраняли паспорт. JSON очень похож на словарь Python:

| JSON | Python |
|---|---|
| `{"city": "Пермь"}` | словарь `dict` |
| `[1, 2, 3]` | список `list` |
| `"текст"` | строка `str` |
| `12`, `0.35` | `int`, `float` |
| `true`, `false` | `True`, `False` |
| `null` | `None` |

Модуль `json`: `json.loads(текст)` превращает JSON-текст в объект Python, `json.dumps(объект)` — обратно.

```python
import json

request_text = '{"city": "Пермь", "visits_90d": 4, "avg_check": null, "app": true}'
payload = json.loads(request_text)
print(type(payload), payload)
print(payload["avg_check"] is None, payload["app"] is True)

answer = {"status": 200, "proba": 0.27, "in_campaign": False}
print(json.dumps(answer, ensure_ascii=False))
```

**Что здесь происходит:**

- `json.loads` прочитал текст и вернул обычный словарь. `null` стал `None`, `true` — `True`.
- `json.dumps` сделал обратное: `False` стал `false`. Так ответ уйдёт приложению.
- `ensure_ascii=False` — чтобы русские буквы, если они будут в ответе, остались читаемыми.

::: predict
```python static
import json
print(json.dumps({"ok": True, "x": None}))
```

- `{"ok": True, "x": None}`
- [x] `{"ok": true, "x": null}`
- `Ошибка TypeError`

Почему: `json.dumps` пишет по правилам JSON, а там логические значения — с маленькой буквы, а пустое значение называется `null`. Если отправить приложению `True` с большой буквы, оно не сможет прочитать ответ.
:::

{{practice: json-rt, p-json, http}}

## Обработчик: от запроса к ответу

Сердце сервиса — функция, которая получает словарь с данными гостя и возвращает словарь-ответ. Начнём с простейшей версии, без проверок.

```python
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
CARD = {"version": "1.0", "features": list(X.columns), "threshold": 1 / 3}

def predict_one(payload):
    row = pd.DataFrame([payload])[CARD["features"]]      # словарь → таблица из одной строки
    p = float(model.predict_proba(row)[0, 1])            # вероятность ухода этого гостя
    return {"status": 200, "proba": round(p, 3), "in_campaign": p >= CARD["threshold"],
            "model_version": CARD["version"]}

guest = {"city": "Тюмень", "tenure_months": 19, "app": 1, "visits_90d": 0, "days_since_last": 108,
         "avg_check": None, "delivery_share": 0.0, "fav_category": "кофе", "promo_used": 0, "complaints": 0}
print(predict_one(guest))
```

**Что здесь происходит:**

- `pd.DataFrame([payload])` — список из одного словаря превращается в таблицу из одной строки: ключи становятся столбцами. Модель обучена на таблице, поэтому и на вход хочет таблицу.
- `[CARD["features"]]` — оставляем столбцы ровно из паспорта и в его порядке. Если в запросе есть что-то лишнее (например, `guest_id`), оно отрежется.
- `[0, 1]` — первая (единственная) строка, второй столбец — вероятность класса «уйдёт».
- `float(...)` — превращаем `np.float64` в обычное число. Сам `np.float64` JSON бы принял, но сравнение `p >= порог` с ним дало бы `np.bool_`, а на `np.bool_` `json.dumps` падает (предупреждение об этом — в разделе «Паспорт модели» прошлого урока).
- `avg_check: None` — пропуск. Его заполнит `SimpleImputer` внутри конвейера, как при обучении.
- В ответ кладём версию модели: когда что-то пойдёт не так, по журналу будет видно, какая версия отвечала.

**Что получилось:** гость из Тюмени, 108 дней без визитов, — вероятность ухода около 0.87, в акцию. Функция работает. Но что будет, если приложение пришлёт что-то не то?

```python error
import pandas as pd

FEATURES = ["city", "tenure_months", "app", "visits_90d", "days_since_last",
            "avg_check", "delivery_share", "fav_category", "promo_used", "complaints"]

def predict_one(payload):                      # та же первая строка обработчика, что выше
    row = pd.DataFrame([payload])[FEATURES]
    return row

predict_one({"city": "Тюмень", "visits_90d": "много"})    # забыли поля, перепутали тип
```

Обработчик упал с `KeyError` (нет нужных столбцов) — для приложения это «ошибка 500, сервер сломался», хотя виноват запрос. Хуже, когда сервис **не падает**: например, `"visits_90d": -5` или `"delivery_share": 40` (проценты вместо доли) модель посчитает без единой жалобы и выдаст бессмысленную вероятность. Поэтому перед моделью нужна проверка входа.

## Проверка входа

Договоримся о правилах — это **контракт** сервиса, его записывают в документацию для разработчиков приложения:

| Поле | Тип | Допустимые значения |
|---|---|---|
| `city` | строка | Казань, Пермь, Тюмень, Уфа |
| `fav_category` | строка | кофе, не кофе, еда |
| `tenure_months` | целое | 1–120 |
| `app` | целое | 0 или 1 |
| `visits_90d`, `promo_used`, `complaints` | целое | ≥ 0 |
| `days_since_last` | целое | 0–3650 |
| `avg_check` | число или `null` | 50–3000 ₽ (`null` — визитов не было) |
| `delivery_share` | число | 0–1 |

Все поля обязательны (у `avg_check` значение может быть `null`, но сам ключ должен быть).

Прежде чем писать проверку, одна ловушка Python:

```python
print(isinstance(5, int), isinstance(True, int), isinstance(2.5, (int, float)))
```

`True` — это `int`! Исторически в Python логический тип сделан как частный случай целого (`True == 1`). Если проверять «число ли это» через `isinstance(x, int)`, то `"visits_90d": true` пройдёт проверку. Поэтому `bool` отсекают явно:

```python
def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)

def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

print(is_int(5), is_int(True), is_int(5.0), is_number(5.0), is_number("5"))
```

Разберём вместе функцию проверки. Она, как и проверка контракта в прошлом уроке, не падает на первой ошибке, а собирает список всех проблем в формате `"поле: что не так"`:

```python
CITIES = ["Казань", "Пермь", "Тюмень", "Уфа"]
CATEGORIES = ["кофе", "не кофе", "еда"]
INT_RANGES = {"tenure_months": (1, 120), "app": (0, 1), "visits_90d": (0, None),
              "days_since_last": (0, 3650), "promo_used": (0, None), "complaints": (0, None)}

def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)

def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def validate(p):
    errors = []
    required = ["city", "fav_category", "avg_check", "delivery_share"] + list(INT_RANGES)
    for f in required:
        if f not in p:
            errors.append(f"{f}: обязательное поле")
    if "city" in p and p["city"] not in CITIES:
        errors.append(f"city: неизвестный город {p['city']!r}")
    if "fav_category" in p and p["fav_category"] not in CATEGORIES:
        errors.append(f"fav_category: неизвестная категория {p['fav_category']!r}")
    for f, (lo, hi) in INT_RANGES.items():
        if f not in p:
            continue                                     # об отсутствии уже сказали
        v = p[f]
        if not is_int(v):
            errors.append(f"{f}: ожидается целое число")
        elif v < lo or (hi is not None and v > hi):
            errors.append(f"{f}: вне диапазона {lo}–{hi if hi is not None else '∞'}")
    if "avg_check" in p and p["avg_check"] is not None:
        v = p["avg_check"]
        if not is_number(v) or not 50 <= v <= 3000:
            errors.append("avg_check: ожидается число 50–3000 или null")
    if "delivery_share" in p:
        v = p["delivery_share"]
        if not is_number(v) or not 0 <= v <= 1:
            errors.append("delivery_share: ожидается доля 0–1")
    return errors

good = {"city": "Пермь", "tenure_months": 12, "app": 0, "visits_90d": 4, "days_since_last": 8,
        "avg_check": 446, "delivery_share": 0.04, "fav_category": "кофе", "promo_used": 1, "complaints": 0}
print(validate(good))
print(validate(dict(good, visits_90d=-1, delivery_share=40, app=True)))
print(validate({"city": "Москва"}))
```

**Что здесь происходит:**

- `required` — все обязательные поля. Сначала проверяем, есть ли они вообще.
- Для каждого целого поля из `INT_RANGES` — сначала тип, потом диапазон. `elif` важен: если тип не тот (например, строка), сравнивать её с числом нельзя — `"много" < 0` упадёт с `TypeError`.
- `hi is not None` — у некоторых полей нет верхней границы (`None` в словаре значит «без ограничения»).
- `continue` — если поля нет, об этом уже сказано, дальше по нему не проверяем, чтобы не писать две ошибки на одно поле.
- `dict(good, visits_90d=-1, ...)` — копия словаря `good` с заменёнными полями. Удобно для тестовых случаев.

**Что получилось:** хороший запрос — пустой список. Во втором — три ошибки сразу: отрицательные визиты, доставка «40» (кто-то прислал проценты) и `app=True` вместо 0/1. В третьем — неизвестный город и куча отсутствующих полей.

::: warn Не исправляйте данные молча
Велик соблазн «помочь» клиенту: увидели `delivery_share=40` — поделили на 100, увидели `"12"` строкой — превратили в число. Не делайте этого в сервисе. Сегодня вы угадали, а завтра пришлют `delivery_share=0.5` в процентах (то есть полпроцента), и вы не узнаете. Правильно — вернуть ошибку 422 с понятным текстом: разработчик приложения исправит у себя один раз. Молчаливые исправления превращаются в инциденты, которые ищут неделями (в проекте главы вы такой разберёте).
:::

::: quiz
Приложение прислало `"delivery_share": 40` (проценты вместо доли). Что должен сделать сервис?

- [x] Вернуть 422: значение вне диапазона 0–1
  > Ошибка понятна разработчику приложения, и он исправит её у себя. «Угадывать» за клиента опасно: завтра пришлют 0.5 в процентах, и сервис молча посчитает чепуху.
- [ ] Поделить на 100 и посчитать
  > Сегодня угадали, завтра нет — и никто не узнает.
- [ ] Вернуть 500
  > 500 — ошибка самого сервиса. Здесь виноват запрос.
- [ ] Посчитать как есть
  > Модель выдаст бессмысленную вероятность без единого предупреждения.
:::

{{practice: is-int, validate}}

## Коды ответа

Чтобы приложение понимало, что произошло, ответ сопровождают кодом. Коды — часть **HTTP**: правил, по которым браузер и приложения общаются с серверами. Первая цифра кода говорит главное: 2xx — всё хорошо, 4xx — виноват запрос, 5xx — виноват сервер. Нам хватит четырёх кодов:

| Код | Значение | Кто виноват | Что делать приложению |
|---|---|---|---|
| **200** | всё хорошо, вот ответ | — | использовать ответ |
| **400** | прислали не JSON | клиент | исправить формирование запроса |
| **422** | JSON, но данные не прошли проверку | клиент | показать ошибки разработчику, исправить данные |
| **500** | сервис сломался | сервис | повторить позже, сообщить команде модели |

Разница между 422 и 500 очень важна для мониторинга: рост 422 — проблема у тех, кто присылает данные; рост 500 — проблема у нас. Если все ошибки превращаются в 500 (как в примере с `KeyError`), команда модели будет искать баг у себя, хотя сломалось приложение.

Соберём полный обработчик: проверка → модель → ответ, с правильными кодами.

::: figure service
Путь запроса: проверка входа отделяет ошибки клиента (422) от ошибок сервиса (500), а успешный ответ — 200.
:::

```python
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
CARD = {"version": "1.0", "features": list(X.columns), "threshold": 1 / 3}

def validate(p):                                   # сокращённая версия для примера
    errors = [f"{f}: обязательное поле" for f in CARD["features"] if f not in p]
    if not errors and not (isinstance(p["visits_90d"], int) and p["visits_90d"] >= 0):
        errors.append("visits_90d: ожидается целое ≥ 0")
    return errors

def predict_one(payload):
    errors = validate(payload)
    if errors:
        return {"status": 422, "errors": errors}
    try:
        row = pd.DataFrame([payload])[CARD["features"]]
        p = float(model.predict_proba(row)[0, 1])
    except Exception as e:                         # непредвиденная поломка — честно 500
        return {"status": 500, "errors": [f"{type(e).__name__}: {e}"]}
    return {"status": 200, "proba": round(p, 3), "in_campaign": p >= CARD["threshold"],
            "model_version": CARD["version"]}

good = {"city": "Пермь", "tenure_months": 12, "app": 0, "visits_90d": 4, "days_since_last": 8,
        "avg_check": 446, "delivery_share": 0.04, "fav_category": "кофе", "promo_used": 1, "complaints": 0}
print(predict_one(good))
print(predict_one({"city": "Пермь"}))
print(predict_one(dict(good, visits_90d=-3)))
```

**Что здесь происходит:**

- Сначала проверка. Если есть ошибки — сразу возвращаем 422, до модели дело не доходит.
- `try ... except Exception as e` — ловим любую ошибку внутри модели и превращаем в ответ 500 с типом и текстом ошибки. Сервис не «падает» целиком: следующий запрос обработается нормально.
- `type(e).__name__` — имя типа ошибки (`KeyError`, `ValueError`), полезно в журнале.

::: tip
`except Exception` — широкая сеть. Её ставят только на самом верхнем уровне обработчика, чтобы сервис пережил непредвиденное. Внутри обычного кода ловите конкретные ошибки (`except KeyError`), иначе спрячете баги.
:::

{{practice: handler, reasons}}

## Практика

## task: json-rt | Туда и обратно | warmup

Строка `request_text` — запрос от приложения. Превратите её в словарь `payload`, измените в нём `visits_90d` на 5 и превратите обратно в JSON-текст `out_text` с русскими буквами без экранирования. В `has_null` — есть ли в `out_text` подстрока `null`.

### setup
```python
request_text = '{"city": "Уфа", "visits_90d": 2, "avg_check": null}'
```

### starter
```python
import json

```

### check
```python
import json as _j
p = need('payload', dict)
assert p.get('visits_90d') == 5 and p.get('city') == 'Уфа', f'payload = {p}: visits_90d должен стать 5.'
t = need('out_text', str)
assert _j.loads(t) == {'city': 'Уфа', 'visits_90d': 5, 'avg_check': None}, f'out_text = {t}.'
assert 'Уфа' in t, 'Русские буквы экранированы: добавьте ensure_ascii=False.'
assert need('has_null') is True, 'has_null = "null" in out_text.'
```

### hint
Текст → словарь: `json.loads`. Словарь → текст: `json.dumps`.

### hint
`out_text = json.dumps(payload, ensure_ascii=False)`, `has_null = "null" in out_text`.

### solution
```python
import json

payload = json.loads(request_text)
payload["visits_90d"] = 5
out_text = json.dumps(payload, ensure_ascii=False)
has_null = "null" in out_text
print(out_text, has_null)
```

## task: p-json | Достать поле из запроса | warmup

Соберите код, который читает JSON-запрос и печатает город гостя и то, что средний чек не указан.

### parsons
```python
import json
text = '{"city": "Казань", "avg_check": null}'
payload = json.loads(text)
print(payload["city"])
print(payload["avg_check"] is None)
```

### check
```python
assert _lines == ['Казань', 'True'], f'Сейчас: {_lines}.'
```

### hint
Сначала текст, потом разбор `json.loads`, потом обращение к полям.

## task: is-int | Ловушка с True | warmup

Напишите функции `is_int(x)` (целое, но не логическое) и `is_number(x)` (целое или дробное, но не логическое). Посчитайте `results` — список значений `is_int` для `[5, True, 5.0, "5", -2, False]`.

### starter
```python
def is_int(x):
    ...

def is_number(x):
    ...

results = [is_int(v) for v in [5, True, 5.0, "5", -2, False]]
print(results)
```

### check
```python
f, g = need('is_int'), need('is_number')
assert [f(v) for v in [5, True, 5.0, '5', -2, False, None]] == [True, False, False, False, True, False, False], 'is_int: True только для настоящих целых (не bool, не float, не строк).'
assert [g(v) for v in [5, 2.5, True, '5', None, -0.1]] == [True, True, False, False, False, True], 'is_number: int или float, но не bool.'
assert need('results', list) == [True, False, False, False, True, False], f'results = {need("results")}.'
```

### hint
`isinstance(x, int)` для `True` вернёт `True` — нужно второе условие, которое отсечёт `bool`.

### hint
`return isinstance(x, int) and not isinstance(x, bool)`; для чисел — `isinstance(x, (int, float))`.

### solution
```python
def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)

def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

results = [is_int(v) for v in [5, True, 5.0, "5", -2, False]]
print(results)
```

## task: validate | Проверка запроса | base

Напишите `validate(p)` по контракту из урока (таблица в разделе «Проверка входа»): вернуть список строк вида `"поле: ..."`, по одной на каждое нарушение, пустой — если всё в порядке. Обязательно: отсутствующие поля, неизвестные город и категория, целые поля (тип и диапазон), `avg_check` (`None` или число 50–3000), `delivery_share` (число 0–1). Константы `CITIES`, `CATEGORIES`, `INT_RANGES` и функции `is_int`, `is_number` — в заготовке. Проверка прогонит вашу функцию на десятке запросов и посмотрит, **какие поля** названы в ошибках.

### setup
```python
CITIES = ["Казань", "Пермь", "Тюмень", "Уфа"]
CATEGORIES = ["кофе", "не кофе", "еда"]
INT_RANGES = {"tenure_months": (1, 120), "app": (0, 1), "visits_90d": (0, None),
              "days_since_last": (0, 3650), "promo_used": (0, None), "complaints": (0, None)}
def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)
def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)
GOOD = {"city": "Пермь", "tenure_months": 12, "app": 0, "visits_90d": 4, "days_since_last": 8,
        "avg_check": 446, "delivery_share": 0.04, "fav_category": "кофе", "promo_used": 1, "complaints": 0}
```

### starter
```python
def validate(p):
    errors = []
    ...
    return errors

print(validate(GOOD))
print(validate(dict(GOOD, visits_90d=-1)))
```

### check
```python
f = need('validate'); G = need('GOOD')
def fields(errs):
    return sorted({e.split(':')[0].strip() for e in errs})
cases = [
    (G, []),
    (dict(G, avg_check=None), []),
    (dict(G, visits_90d=-1), ['visits_90d']),
    (dict(G, app=True), ['app']),
    (dict(G, app=2), ['app']),
    (dict(G, tenure_months='12'), ['tenure_months']),
    (dict(G, delivery_share=40), ['delivery_share']),
    (dict(G, avg_check=44600), ['avg_check']),
    (dict(G, city='Москва', fav_category='десерты'), ['city', 'fav_category']),
    ({k: v for k, v in G.items() if k != 'complaints'}, ['complaints']),
    ({k: v for k, v in G.items() if k != 'avg_check'}, ['avg_check']),
    (dict(G, days_since_last=5000, promo_used=-2), ['days_since_last', 'promo_used']),
]
for p, want in cases:
    try:
        got = f(p)
    except Exception as e:
        raise AssertionError(f'validate упала с {type(e).__name__} на запросе {p}. Проверяйте тип до сравнения с числами.')
    assert isinstance(got, list), 'validate должна возвращать список.'
    assert fields(got) == want, f'Для запроса с изменениями {dict(set(p.items()) ^ set(G.items())) or "(без изменений)"} ошибки должны быть про {want or "ничего"}, а сейчас: {got}.'
```

### hint
Разбейте на шаги: 1) обязательные поля; 2) город и категория; 3) цикл по `INT_RANGES`; 4) `avg_check`; 5) `delivery_share`. Каждый шаг — несколько строк, добавляющих в `errors`.

### hint
В цикле по целым полям: если поля нет — `continue`; если `not is_int(v)` — ошибка типа; иначе (`elif`) — проверка диапазона. Порядок важен: строку нельзя сравнивать с числом.

### hint
```python
for f, (lo, hi) in INT_RANGES.items():
    if f not in p:
        continue
    v = p[f]
    if not is_int(v):
        errors.append(f"{f}: ожидается целое число")
    elif v < lo or (hi is not None and v > hi):
        errors.append(f"{f}: вне диапазона")
```

### solution
```python
def validate(p):
    errors = []
    required = ["city", "fav_category", "avg_check", "delivery_share"] + list(INT_RANGES)
    for f in required:
        if f not in p:
            errors.append(f"{f}: обязательное поле")
    if "city" in p and p["city"] not in CITIES:
        errors.append(f"city: неизвестный город {p['city']!r}")
    if "fav_category" in p and p["fav_category"] not in CATEGORIES:
        errors.append(f"fav_category: неизвестная категория {p['fav_category']!r}")
    for f, (lo, hi) in INT_RANGES.items():
        if f not in p:
            continue
        v = p[f]
        if not is_int(v):
            errors.append(f"{f}: ожидается целое число")
        elif v < lo or (hi is not None and v > hi):
            errors.append(f"{f}: вне диапазона {lo}–{hi if hi is not None else '∞'}")
    if "avg_check" in p and p["avg_check"] is not None:
        v = p["avg_check"]
        if not is_number(v) or not 50 <= v <= 3000:
            errors.append("avg_check: ожидается число 50–3000 или null")
    if "delivery_share" in p:
        v = p["delivery_share"]
        if not is_number(v) or not 0 <= v <= 1:
            errors.append("delivery_share: ожидается доля 0–1")
    return errors

print(validate(GOOD))
print(validate(dict(GOOD, visits_90d=-1)))
```

### explain
Самые частые ошибки в этой задаче: забыть про `bool` (тогда `app=True` пройдёт), сравнить строку `"12"` с числом (функция упадёт с `TypeError` — а значит, сервис ответит 500 вместо 422) и написать две ошибки на одно поле. Обратите внимание на `avg_check=44600`: это средний чек в копейках. Проверка диапазона ловит его, хотя тип правильный, — запомните этот случай, он понадобится в проекте.

## task: handler | Обработчик с кодами | base

Модель `model`, паспорт `CARD` и готовая `validate` — в заготовке. Напишите `predict_one(payload)`:

- ошибки проверки → `{"status": 422, "errors": [...]}`;
- иначе посчитать вероятность; если при этом возникло исключение → `{"status": 500, "errors": ["<ИмяОшибки>: <текст>"]}`;
- успех → `{"status": 200, "proba": <3 знака>, "in_campaign": <bool>, "model_version": CARD["version"]}`.

Сохраните `r_good`, `r_bad` — ответы для `GOOD` и для `GOOD` без поля `city`.

### setup
```python
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
    return [f"{f}: обязательное поле" for f in CARD["features"] if f not in p]
GOOD = {"city": "Пермь", "tenure_months": 12, "app": 0, "visits_90d": 4, "days_since_last": 8,
        "avg_check": 446, "delivery_share": 0.04, "fav_category": "кофе", "promo_used": 1, "complaints": 0}
```

### starter
```python
import pandas as pd

def predict_one(payload):
    ...

r_good = predict_one(GOOD)
r_bad = predict_one({k: v for k, v in GOOD.items() if k != "city"})
print(r_good, r_bad, sep="\n")
```

### check
```python
import json as _j
import pandas as _pd
f, m, C, G = need('predict_one'), need('model'), need('CARD'), need('GOOD')
p = float(m.predict_proba(_pd.DataFrame([G])[C['features']])[0, 1])
r = need('r_good', dict)
assert r.get('status') == 200 and close(r.get('proba'), round(p, 3), 1e-9), f'r_good = {r}: status 200 и proba с 3 знаками.'
assert r.get('in_campaign') is (p >= C['threshold']) and r.get('model_version') == C['version'], f'r_good = {r}: in_campaign — bool по порогу из CARD, model_version из CARD.'
_j.dumps(r)
rb = need('r_bad', dict)
assert rb.get('status') == 422 and any('city' in e for e in rb.get('errors', [])), f'r_bad = {rb}: 422 и ошибка про city.'
r5 = f(dict(G, visits_90d='четыре'))
assert r5.get('status') == 500 and isinstance(r5.get('errors'), list) and r5['errors'], f'Если модель упала (visits_90d строкой не ловит учебная validate), нужен ответ 500 с текстом ошибки, а сейчас: {r5}.'
assert ':' in r5['errors'][0], 'Текст ошибки 500: "<ИмяОшибки>: <сообщение>" — type(e).__name__.'
```

### hint
Скелет: `errors = validate(payload)` → `if errors: return {...422...}` → `try:` модель `except Exception as e: return {...500...}` → `return {...200...}`.

### hint
Ответ должен пережить `json.dumps`: вероятность — `float(...)`, решение — `bool` (результат сравнения обычного `float` с порогом — уже `bool`).

### hint
```python
try:
    row = pd.DataFrame([payload])[CARD["features"]]
    p = float(model.predict_proba(row)[0, 1])
except Exception as e:
    return {"status": 500, "errors": [f"{type(e).__name__}: {e}"]}
```

### solution
```python
import pandas as pd

def predict_one(payload):
    errors = validate(payload)
    if errors:
        return {"status": 422, "errors": errors}
    try:
        row = pd.DataFrame([payload])[CARD["features"]]
        p = float(model.predict_proba(row)[0, 1])
    except Exception as e:
        return {"status": 500, "errors": [f"{type(e).__name__}: {e}"]}
    return {"status": 200, "proba": round(p, 3), "in_campaign": p >= CARD["threshold"],
            "model_version": CARD["version"]}

r_good = predict_one(GOOD)
r_bad = predict_one({k: v for k, v in GOOD.items() if k != "city"})
print(r_good, r_bad, sep="\n")
```

### explain
Проверка отправила в ваш обработчик запрос с `visits_90d="четыре"`: учебная `validate` в заготовке проверяет только наличие полей, поэтому запрос дошёл до модели и та упала. Обработчик честно ответил 500 — сервис цел, а в журнале видно `ValueError`. Это и показывает, зачем нужна полная проверка из прошлой задачи: с ней тот же запрос получил бы 422 — «виноват клиент», и разбираться пошли бы в правильное место.

## task: http | Текст на входе, текст на выходе | base

Сервис получает не словарь, а **текст** запроса. Напишите `handle(text)`: разобрать JSON; если текст — не JSON или не объект (`{...}`) → вернуть текст `{"status": 400, "errors": ["тело запроса — не JSON-объект"]}`; иначе вызвать готовую `predict_one` и вернуть её ответ как JSON-текст (`ensure_ascii=False`). Сохраните ответы на три запроса из заготовки: `a1`, `a2`, `a3` (строки).

### setup
```python
import json
def predict_one(p):
    if "visits_90d" not in p:
        return {"status": 422, "errors": ["visits_90d: обязательное поле"]}
    return {"status": 200, "proba": 0.25, "in_campaign": False, "model_version": "1.0"}
q1 = '{"visits_90d": 3}'
q2 = '{"visits_90d": 3'
q3 = '[1, 2, 3]'
```

### starter
```python
import json

def handle(text):
    ...

a1, a2, a3 = handle(q1), handle(q2), handle(q3)
print(a1, a2, a3, sep="\n")
```

### check
```python
import json as _j
f = need('handle')
for nm in ['a1', 'a2', 'a3']:
    assert isinstance(need(nm), str), f'{nm} должен быть строкой — JSON-текстом ответа.'
assert _j.loads(need('a1'))['status'] == 200, f'a1 = {need("a1")}.'
assert _j.loads(need('a2'))['status'] == 400, f'a2 = {need("a2")}: обрезанный JSON → 400.'
assert _j.loads(need('a3'))['status'] == 400, f'a3 = {need("a3")}: список — не объект → 400.'
assert _j.loads(f('{"city": "Уфа"}'))['status'] == 422, 'Для объекта без visits_90d — ответ predict_one (422).'
assert 'обязательное' in f('{"x": 1}') and 'тело запроса' in f('oops'), 'Добавьте ensure_ascii=False — русские буквы в ответе должны остаться буквами.'
```

### hint
`json.loads` на испорченном тексте бросает `json.JSONDecodeError` — поймайте её через `try/except`. Отдельно проверьте, что результат — словарь: `isinstance(payload, dict)`.

### hint
```python
try:
    payload = json.loads(text)
except json.JSONDecodeError:
    payload = None
if not isinstance(payload, dict):
    return json.dumps({"status": 400, ...}, ensure_ascii=False)
```

### solution
```python
import json

def handle(text):
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if not isinstance(payload, dict):
        return json.dumps({"status": 400, "errors": ["тело запроса — не JSON-объект"]}, ensure_ascii=False)
    return json.dumps(predict_one(payload), ensure_ascii=False)

a1, a2, a3 = handle(q1), handle(q2), handle(q3)
print(a1, a2, a3, sep="\n")
```

### explain
`[1, 2, 3]` — вполне корректный JSON, но не объект: у него нет полей, и `predict_one` упал бы на `"visits_90d" not in p` (для списка это сработает, но дальше обращение `p["..."]` сломается). Поэтому проверяют обе вещи: что текст разбирается и что получился словарь. FastAPI делает это за вас — но понимать, что происходит внутри, полезно: так читают его ответы 400 и 422.

## task: reasons | Ответ с причинами | star

Оператор поддержки видит в CRM «вероятность ухода 0.87» и спрашивает: почему? Для логистической регрессии ответ можно посчитать: вклад признака = значение признака после подготовки × его вес (глава 8). Напишите `explain_one(payload, k=2)`, которая возвращает список из `k` названий признаков с наибольшим **положительным** вкладом (те, что сильнее всего тянут к уходу), по убыванию вклада. Названия — как в `get_feature_names_out()` подготовки, но без префикса до `__` (`"num__days_since_last"` → `"days_since_last"`, `"cat__city_Тюмень"` → `"city_Тюмень"`). Сохраните `top_guest` — ответ для гостя `GUEST` из заготовки.

### setup
```python
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
FEATURES = list(_X.columns)
GUEST = {"city": "Тюмень", "tenure_months": 19, "app": 1, "visits_90d": 0, "days_since_last": 108,
         "avg_check": None, "delivery_share": 0.0, "fav_category": "кофе", "promo_used": 0, "complaints": 0}
```

### starter
```python
import numpy as np
import pandas as pd

def explain_one(payload, k=2):
    prep = model.named_steps["prep"]
    lr = model.named_steps["model"]
    ...

top_guest = explain_one(GUEST)
print(top_guest)
```

### check
```python
import numpy as _np
import pandas as _pd
f, m, F = need('explain_one'), need('model'), need('FEATURES')
def _ref(p, k):
    pr, lr = m.named_steps['prep'], m.named_steps['model']
    z = pr.transform(_pd.DataFrame([p])[F]); z = z.toarray() if hasattr(z, 'toarray') else _np.asarray(z)
    c = _pd.Series(z[0] * lr.coef_[0], index=[n.split('__', 1)[1] for n in pr.get_feature_names_out()])
    c = c[c > 0].sort_values(ascending=False)
    return list(c.index[:k])
G = need('GUEST')
assert need('top_guest', list) == _ref(G, 2), f'top_guest = {need("top_guest")}, а нужно {_ref(G, 2)}.'
G2 = dict(G, complaints=2, delivery_share=0.8, days_since_last=5, visits_90d=10, city='Пермь')
assert list(f(G2, 3)) == _ref(G2, 3), f'Для другого гостя с k=3 ответ {f(G2, 3)}, а нужно {_ref(G2, 3)}.'
```

### hint
Подготовленная строка: `z = prep.transform(pd.DataFrame([payload])[FEATURES])`. Она может оказаться разреженной матрицей — тогда `z.toarray()`. Веса — `lr.coef_[0]`.

### hint
Вклады удобно положить в Series с именами `prep.get_feature_names_out()`; префикс отрезается `name.split("__", 1)[1]`. Дальше — оставить положительные и отсортировать по убыванию.

### hint
```python
contrib = pd.Series(z[0] * lr.coef_[0], index=[n.split("__", 1)[1] for n in prep.get_feature_names_out()])
contrib = contrib[contrib > 0].sort_values(ascending=False)
return list(contrib.index[:k])
```

### solution
```python
import numpy as np
import pandas as pd

def explain_one(payload, k=2):
    prep = model.named_steps["prep"]
    lr = model.named_steps["model"]
    z = prep.transform(pd.DataFrame([payload])[FEATURES])
    z = z.toarray() if hasattr(z, "toarray") else np.asarray(z)
    names = [n.split("__", 1)[1] for n in prep.get_feature_names_out()]
    contrib = pd.Series(z[0] * lr.coef_[0], index=names)
    contrib = contrib[contrib > 0].sort_values(ascending=False)
    return list(contrib.index[:k])

top_guest = explain_one(GUEST)
print(top_guest)
```

### explain
Для гостя из примера главные причины — давность последнего визита и ноль визитов за 90 дней; Тюмень добавляет третьей. Оператору это понятнее, чем 0.87: «давно не был — предложите бонус». Важно: это объяснение работает для **линейной** модели. Для леса или бустинга вклады так не считаются — там используют SHAP или permutation importance (глава 8), и в онлайн-сервисе это заметно дороже по времени.
