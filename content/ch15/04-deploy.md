---
title: "Упаковка и запуск: окружение, Docker, расписание, журнал"
files: [guests_churn.csv, service_log.jsonl]
lead: "«У меня в ноутбуке работает» — самая частая фраза перед тем, как модель не заработала на сервере. Разбираем, как зафиксировать окружение, как устроен пакетный скрипт, который можно спокойно запускать по расписанию, что такое Docker и cron, и как сервис ведёт журнал, по которому потом разбирают любые проблемы. Журнал сервиса оттока за неделю — наш материал для практики и для проекта главы."
recap:
  - "Окружение фиксируют списком пакетов с точными версиями: `pyproject.toml` + `uv.lock` (или `requirements.txt` с `==`). Версии смотрят `importlib.metadata.version(...)`."
  - "Пакетный скрипт: прочитать → проверить → посчитать → записать → вернуть сводку. Он должен быть идемпотентным: повторный запуск за ту же дату перезаписывает результат, а не дублирует его."
  - "Плохие строки не роняют пакет: их откладывают в отдельный файл с причиной."
  - "Docker-образ — «коробка» с Python, библиотеками, кодом и моделью; контейнер — запущенная коробка. Одинаково работает на ноутбуке и сервере."
  - "cron: пять полей — минута, час, день месяца, месяц, день недели. `30 6 * * 1` — по понедельникам в 6:30."
  - "Сервис пишет журнал по строке JSON на запрос (JSON Lines): время, клиент, версия модели, статус, время ответа, ошибка, вход. Читается `json.loads` построчно → DataFrame."
---

## «У меня работает»

Модель оттока готова: артефакт из урока «Модель как артефакт: файл, паспорт, контрольный набор», обработчик из урока «Модель как сервис: запрос, проверка, ответ», журнал экспериментов из урока «Учёт экспериментов и воспроизводимость». Осталось запустить её «по-настоящему»: на сервере, каждый понедельник, без вашего ноутбука. На этом шаге всплывают проблемы, которых в ноутбуке не было:

- на сервере другая версия sklearn — модель не загружается или считает иначе;
- скрипт упал на одной кривой строке, и список для CRM не сформировался;
- скрипт запустили дважды — в CRM ушли дубли;
- сервис полгода работал, а потом «что-то сломалось» — и нечем выяснить, что именно.

Каждая проблема закрывается своим приёмом: фиксация окружения, аккуратный пакетный скрипт, Docker, расписание и журнал. Разберём их по очереди.

## Окружение: точные версии

**Окружение** — это Python и все библиотеки нужных версий. Модель из `joblib` надёжно загружается только той же версией sklearn, на которой её сохранили (раздел «Паспорт модели» урока «Модель как артефакт: файл, паспорт, контрольный набор»). Поэтому версии записывают явно.

Посмотреть, какие версии стоят сейчас, можно из самого Python:

```python
import sys
from importlib.metadata import version
import numpy, pandas, sklearn, joblib        # в браузере пакет появляется после первого импорта

print("Python", sys.version.split()[0])
for pkg in ["numpy", "pandas", "scikit-learn", "joblib"]:
    print(f"{pkg}=={version(pkg)}")
```

**Что здесь происходит:**

- `importlib.metadata.version("имя")` — версия установленного пакета. Имя — то, под которым пакет ставят (`scikit-learn`), а не то, под которым импортируют (`sklearn`).
- Формат `пакет==версия` — так версии записывают в `requirements.txt`: два знака `=` означают «ровно эта версия».

В рабочих проектах этим занимается менеджер пакетов. В курсе мы используем **uv**: файл `pyproject.toml` перечисляет, *что* нужно проекту, а `uv.lock` — *какие точно версии* всего, включая зависимости зависимостей.

```python static
# pyproject.toml — пишется руками (или командой uv add)
[project]
name = "zerno-churn"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "scikit-learn==1.8.0",     # ровно та версия, на которой обучена модель
    "pandas>=3.0",
    "fastapi>=0.115",
    "uvicorn>=0.30",
]
```

Команды, которые нужны каждый день:

| Команда | Что делает |
|---|---|
| `uv add pandas` | добавить пакет в проект (и в `pyproject.toml`, и в `uv.lock`) |
| `uv lock` | пересчитать точные версии |
| `uv sync` | поставить ровно то, что записано в `uv.lock` (на сервере, у коллеги) |
| `uv run python score.py` | запустить скрипт в окружении проекта |

::: tip
`uv.lock` обязательно кладут в git вместе с кодом. Тогда «поставь, как у меня» — это одна команда `uv sync`, а не переписка «какая у тебя версия pandas?».
:::

{{practice: versions}}

## Пакетный скрипт

Скрипт для еженедельного расчёта — та же логика, что в уроках «Модель как артефакт: файл, паспорт, контрольный набор» и «Модель как сервис: запрос, проверка, ответ», но оформленная так, чтобы её можно было запускать без человека. Хороший пакетный скрипт:

1. **читает** вход из известного места;
2. **проверяет** строки и откладывает плохие в отдельный файл с причиной, а не падает;
3. **считает** вероятности и решения по порогу из паспорта;
4. **пишет** результат в файл с датой в имени;
5. **возвращает сводку**: сколько посчитано, сколько отложено, сколько в акции — её пишут в журнал и по ней видно, что запуск прошёл нормально;
6. **идемпотентен**: если запустить его второй раз за ту же дату, получится тот же результат, а не дубли.

::: tip Аналогия
Идемпотентный скрипт похож на меловую доску «меню дня» у кассы: бариста стирает и пишет её заново — сколько раз ни перепиши за день, меню на доске одно. Неидемпотентный — как тетрадь заказов, куда каждое «переписывание» добавляет ещё одну копию списка. Разница одна: доску стирают целиком, а скрипт перезаписывает только файл своей даты — результаты прошлых недель остаются нетронутыми.
:::

Разберём вместе такой скрипт на выгрузке, где часть строк испорчена.

```python
import os
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

# --- подготовка «окружения»: модель и паспорт (в работе — joblib.load и json.load) ---
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), ["city", "fav_category"])])
MODEL = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X, g["churned"])
CARD = {"version": "1.0", "features": list(X.columns), "threshold": 1 / 3}

# --- выгрузка на понедельник: 300 гостей, у части испорчены данные ---
week = g.drop(columns=["churned", "card_blocked"]).sample(300, random_state=1)
week.loc[week.index[:5], "visits_90d"] = -1
week.loc[week.index[5:8], "delivery_share"] = 35.0
week.to_csv("export_2026-12-07.csv", index=False)

def bad_reason(row):
    if row["visits_90d"] < 0:
        return "visits_90d < 0"
    if not 0 <= row["delivery_share"] <= 1:
        return "delivery_share вне 0–1"
    return ""

def run_batch(input_path, out_dir, date):
    df = pd.read_csv(input_path)
    reasons = df.apply(bad_reason, axis=1)                         # причина для каждой строки ("" — всё хорошо)
    good, bad = df[reasons == ""], df[reasons != ""].assign(reason=reasons[reasons != ""])
    p = MODEL.predict_proba(good[CARD["features"]])[:, 1]
    out = pd.DataFrame({"guest_id": good["guest_id"], "proba": p.round(4),
                        "in_campaign": p >= CARD["threshold"], "model_version": CARD["version"]})
    os.makedirs(out_dir, exist_ok=True)
    out.to_csv(f"{out_dir}/scores_{date}.csv", index=False)       # дата в имени → повторный запуск перезапишет
    bad.to_csv(f"{out_dir}/rejected_{date}.csv", index=False)
    return {"date": date, "n_input": len(df), "n_scored": len(out), "n_rejected": len(bad),
            "n_in_campaign": int(out["in_campaign"].sum()), "model_version": CARD["version"]}

summary = run_batch("export_2026-12-07.csv", "out", "2026-12-07")
print(summary)
print(pd.read_csv("out/rejected_2026-12-07.csv")[["guest_id", "reason"]].head())
```

**Что здесь происходит:**

- `df.apply(bad_reason, axis=1)` — функция применяется к каждой строке (`axis=1`) и возвращает причину отказа или пустую строку. Получается столбец причин той же длины, что таблица.
- `df[reasons == ""]` и `df[reasons != ""]` — делим выгрузку на годные и отложенные строки. `.assign(reason=...)` добавляет к отложенным столбец с причиной — тот, кто будет разбираться, сразу видит, что не так.
- Модель считает только годные строки. Одна плохая строка не роняет весь расчёт.
- Имя файла `scores_{date}.csv` — с датой выгрузки. Если скрипт перезапустить за ту же дату, файл перезапишется (`to_csv` по умолчанию пишет заново). Дублей не будет — это и есть **идемпотентность**.
- Возвращаем сводку — словарь из нескольких чисел. В журнале запусков по ней сразу видно аномалию: например, если однажды отложено 40 % строк вместо обычных 2 %.

::: figure batch-job
Пакетный скрипт из примера: 300 строк выгрузки делятся на годные и отложенные, годные идут в модель, оба результата пишутся в файлы с датой, а сводка — в журнал.
:::

**Что получилось:** из 300 гостей 8 отложены с понятными причинами, остальные посчитаны, в акции — около пятой части. Файл для CRM и файл отказов лежат в папке `out`.

::: warn Не дописывайте результат в общий файл
Частая ошибка — писать все недели в один `scores.csv` с `mode="a"`. Тогда повторный запуск (а его рано или поздно сделают — после сбоя, по ошибке, «на всякий случай») задвоит гостей, и CRM отправит им по два бонуса. Файл на каждую дату (или таблица в базе с перезаписью за дату — `DELETE ... WHERE date = ...; INSERT ...`) от этого защищает.
:::

::: figure idempotent
Два запуска за одну дату. Слева дозапись в общий файл: каждый гость оказался в списке дважды. Справа файл с датой в имени: второй запуск перезаписал первый, результат тот же.
:::

На сервере такой скрипт запускают из командной строки, а дату и пути передают аргументами:

```python static
# score.py
# выше в файле: импорты, загрузка модели и паспорта из models/churn/1.0/
# (joblib.load, json.load — как в уроке об артефакте) и функции bad_reason и run_batch из примера
import argparse, json

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    print(json.dumps(run_batch(a.input, a.out_dir, a.date), ensure_ascii=False))

# запуск: uv run python score.py --input export_2026-12-07.csv --date 2026-12-07
```

**Что здесь происходит:**

- `argparse` — стандартный модуль для **аргументов скрипта**: слов после имени файла в командной строке.
- `ap.add_argument("--input")` объявляет параметр. `required=True` — без него скрипт не запустится и напишет, чего не хватает; `default="out"` — значение, если параметр не передали.
- После `a = ap.parse_args()` значения доступны как атрибуты: `a.input`, `a.date`. Дефис в имени превращается в подчёркивание: `--out-dir` → `a.out_dir`.
- `if __name__ == "__main__":` — этот блок выполняется, только когда файл запускают как скрипт, а не импортируют из другого кода.

::: quiz
Ночной скрипт пересчёта рисков упал на середине, и его перезапустили. Что должно быть верно для хорошего скрипта?

- [x] Повторный запуск даёт тот же результат
  > Такой скрипт называют идемпотентным: он не дублирует записи. Перезапуски — обычное дело. Скрипт перезаписывает результат за дату, а не дописывает его второй раз.
- [ ] Скрипт должен уметь продолжить с места падения
  > Удобно, но не обязательно: проще — безопасно пересчитать всё.
- [ ] Перезапускать нельзя
  > Без перезапуска данные за ночь пропадут.
- [ ] Результаты двух запусков нужно сложить
  > Тогда каждый гость посчитается дважды.
:::

{{practice: batch-job, idempotent}}

## Docker: коробка с окружением

Даже с `uv.lock` на сервере может не оказаться нужной версии Python или системной библиотеки. **Docker** решает это радикально: вы собираете **образ** — «коробку», в которой лежит всё: операционная система, Python, библиотеки, код и файл модели. Запущенная коробка называется **контейнером**. Она работает одинаково на ноутбуке, на сервере и в облаке.

::: sql
Аналогия: образ — как резервная копия базы данных со всеми таблицами, процедурами и настройками; контейнер — база, развёрнутая из этой копии. Сколько раз ни разворачивай — получится одно и то же.
:::

Рецепт образа пишут в файле `Dockerfile`:

```dockerfile
# Dockerfile
# 1. базовый образ: Linux + Python 3.12
FROM python:3.12-slim
# 2. рабочая папка внутри коробки
WORKDIR /app
# 3. ставим менеджер пакетов
RUN pip install uv
# 4. сначала только списки пакетов…
COPY pyproject.toml uv.lock ./
# 5. …и ставим ровно их (слой кешируется)
RUN uv sync --frozen --no-dev
# 6. потом код
COPY service.py ./
# 7. и артефакт модели: файл, паспорт
COPY models/ ./models/
# 8. сервис слушает порт 8000
EXPOSE 8000
# 9. что запустить
CMD ["uv", "run", "uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
```

::: warn Комментарий в Dockerfile — только с начала строки
В Python `#` можно поставить в конце строки кода. В Dockerfile так нельзя: комментарием считается только строка, которая начинается с `#`. Строку `EXPOSE 8000  # порт` Docker прочитает как команду с лишними словами и не соберёт образ. Поэтому пояснения выше стоят на отдельных строках над командами.
:::

**Что здесь происходит (по строкам):**

1. `FROM` — с чего начинаем. `slim` — облегчённая версия без лишнего.
2. `WORKDIR` — дальше все команды выполняются в папке `/app` внутри образа.
3. `RUN` — выполнить команду при сборке образа.
4–5. Сначала копируем только `pyproject.toml` и `uv.lock` и ставим пакеты. Docker кеширует каждый шаг: если меняется только код, пакеты заново ставиться не будут — сборка займёт секунды. `--frozen` — не пересчитывать версии, ставить строго по `uv.lock`.
6–7. Копируем код сервиса (файл `service.py` из урока «Сервис в работе: пакет, время ответа, FastAPI, тесты») и папку с моделью.
8. `EXPOSE` — документирует, какой порт слушает сервис.
9. `CMD` — команда, которая выполнится при запуске контейнера: поднять FastAPI-сервис. `--host 0.0.0.0` — слушать на всех адресах. В уроке «Сервис в работе: пакет, время ответа, FastAPI, тесты» сервис слушал `127.0.0.1` — «только этот компьютер». Внутри контейнера «этот компьютер» — сам контейнер, и запросы снаружи до сервиса бы не дошли.

::: figure docker-layers
Слои образа снизу вверх. Поменяли только `service.py` — нижние слои, включая долгую установку пакетов, берутся из кеша, пересобираются только верхние.
:::

Собрать и запустить:

```sh
# в терминале, в папке проекта
docker build -t zerno-churn:1.0 .              # собрать образ с именем и версией; «.» — собирать из текущей папки, где лежит Dockerfile
docker run -p 8000:8000 zerno-churn:1.0         # запустить; порт 8000 контейнера → 8000 вашего компьютера
# сервис доступен на http://127.0.0.1:8000/docs
```

::: note
Версия образа (`:1.0`) совпадает с версией модели — так на сервере всегда понятно, что запущено. Новая модель — новый образ `:1.1`; старый остаётся, и откат — это запуск предыдущего образа.
:::

::: quiz
Зачем в `Dockerfile` сначала копируют `pyproject.toml` и `uv.lock` и ставят пакеты, а код копируют только потом?

- [x] Чтобы при правке кода не ставить пакеты заново
  > Docker кеширует каждый шаг: если поменялся только код, слой с пакетами берётся из кеша, и пересборка занимает секунды. Пакеты меняются редко, код — часто. Порядок шагов «от редко меняющегося к часто меняющемуся» экономит время на каждой сборке.
- [ ] Иначе код не увидит установленные библиотеки
  > В готовом образе есть и пакеты, и код при любом порядке шагов — дело только в скорости пересборки.
- [ ] Чтобы код не попал в образ
  > Код копируется на шаге 6 и попадает в образ — без него сервис не запустится.
- [ ] Так образ получится меньше по размеру
  > В образ попадают те же файлы при любом порядке; выигрыш — во времени сборки, а не в размере.
:::

## Расписание: cron

Пакетный скрипт нужно запускать каждый понедельник. Классический инструмент на Linux-серверах — **cron**: в специальный файл записывают строки «когда → что запустить». «Когда» — пять полей через пробел:

| Поле | Значения | Пример |
|---|---|---|
| минута | 0–59 | `30` |
| час | 0–23 | `6` |
| день месяца | 1–31 | `*` (любой) |
| месяц | 1–12 | `*` |
| день недели | 0–6 (0 — воскресенье, 1 — понедельник) | `1` |

Значки: `*` — любое значение, `1,15` — список, `1-5` — диапазон, `*/15` — каждое 15-е.

| Расписание | Строка cron |
|---|---|
| по понедельникам в 6:30 | `30 6 * * 1` |
| каждый день в полночь | `0 0 * * *` |
| каждые 15 минут | `*/15 * * * *` |
| по будням в 9:00 | `0 9 * * 1-5` |
| 1-го числа каждого месяца в 3:00 | `0 3 1 * *` |

::: figure cron-fields
Первая строка таблицы по полям: минута 30, час 6, любой день месяца, любой месяц, день недели 1 — по понедельникам в 6:30.
:::

Полная строка в crontab: `30 6 * * 1 cd /srv/churn && uv run python score.py --input ... --date $(date +\%F)`. Здесь `$(date +%F)` подставляет сегодняшнюю дату вида `2026-12-07`, а обратная косая перед `%` — не опечатка: в crontab знак процента особый, и его надо экранировать `\%`.

У cron свой урезанный набор путей (`PATH`): `uv`, установленный в `~/.local/bin`, он может не найти, и запуск молча не произойдёт. Поэтому в crontab пишут полный путь к программе (его покажет `which uv`) и сохраняют вывод в файл, чтобы видеть ошибки: `30 6 * * 1 cd /srv/churn && /home/analyst/.local/bin/uv run python score.py ... >> /srv/churn/cron.log 2>&1`. Здесь `>>` дописывает вывод в файл, а `2>&1` отправляет туда же и сообщения об ошибках.

::: quiz
Сколько раз в сутки сработает строка cron `0 */6 * * *`?

- [ ] 6
  > `*/6` — не «6 раз», а «каждый шестой»: это шаг, а не количество.
- [x] 4
  > `*/6` в поле часа — каждый шестой час, начиная с 0: 0, 6, 12, 18. Минута `0` — в начале этих часов. Итого 4 запуска.
- [ ] 24
  > Каждый час — это `0 * * * *`.
- [ ] 240
  > Так было бы при `*/6` в поле минут: `*/6 * * * *` — каждые 6 минут, 24 · 60 / 6 = 240 раз.
:::

В больших командах вместо голого cron используют оркестраторы — **Airflow**, **Prefect**, **Dagster**: они хранят историю запусков, перезапускают упавшие задачи и строят цепочки «выгрузка → расчёт → отправка в CRM». Но строку расписания там пишут в том же формате cron.

{{practice: cron, cron-match}}

## Журнал сервиса

Последний и самый важный для аналитика кусок. Работающий сервис должен записывать каждый запрос: когда, от кого, какая версия модели ответила, с каким статусом, за сколько миллисекунд, с какой ошибкой и что было на входе. Без журнала на вопрос «почему в пятницу всё сломалось?» ответить нечем.

Журнал удобно писать в формате **JSON Lines** (`.jsonl`): каждая строка файла — отдельный JSON-объект. Строки независимы, их можно дописывать по одной и читать построчно.

```python
import json

with open("service_log.jsonl", encoding="utf-8") as f:
    first = f.readline()
print(first[:300])
rec = json.loads(first)
print(list(rec))
print(rec["payload"]["city"], rec["status"], rec["latency_ms"])
```

**Что здесь происходит:**

- `f.readline()` — одна строка файла, то есть один запрос.
- `json.loads` превращает её в словарь. Внутри — вложенный словарь `payload`: вход, который прислало приложение.
- Поля записи: `ts` — время, `request_id` — номер запроса, `client` — кто прислал (приложение какой версии или сайт), `model_version`, `status`, `latency_ms`, `error`, `payload`.

Весь журнал — в таблицу:

```python
import json
import pandas as pd

with open("service_log.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

log = pd.DataFrame(records)
log["ts"] = pd.to_datetime(log["ts"])
print(log.shape)
print(log[["ts", "client", "model_version", "status", "latency_ms"]].head())
print(log["status"].value_counts())

payload_df = pd.json_normalize(log["payload"].tolist())  # вложенные словари → столбцы
print(payload_df.columns.tolist())
```

**Что здесь происходит:**

- `[json.loads(line) for line in f]` — файл читается построчно, каждая строка превращается в словарь; получаем список словарей.
- `pd.DataFrame(records)` — список словарей → таблица. Столбец `payload` пока содержит словари целиком.
- `pd.to_datetime` — время из текста в дату-время (иначе не сгруппировать по часам и дням).
- `pd.json_normalize(...)` — раскладывает вложенные словари по отдельным столбцам: `city`, `visits_90d` и т. д. Это пригодится, чтобы смотреть, *что* присылали клиенты.

::: warn Почему не `pd.read_json`
Короче было бы `pd.read_json("service_log.jsonl", lines=True)`. Но эта функция сама угадывает типы и превращает версию модели `"1.0"` в число `1.0`. А версии `"1.1"` и `"1.10"` обе станут числом `1.1` и сольются. Для журнала, где версия — главный признак, это опасно. Читайте через `json.loads`, как выше, или передайте `dtype={"model_version": str}`.
:::

::: figure jsonl-normalize
Первые три строки `service_log.jsonl` (часть полей заменена на «…»). `pd.DataFrame(records)` даёт `log` 1763 × 8 — столбец `payload` хранит словарь целиком (`ts` здесь ещё текст, до `pd.to_datetime`). `pd.json_normalize` превращает каждый такой словарь в строку отдельной таблицы `payload_df` 1763 × 11: ключ словаря → столбец.
:::

**Что получилось:** 1763 запроса за неделю 2–8 ноября 2026. Большинство — 200, но есть и 422, и 500. В практике посчитаем, как сервис работал по дням, а в проекте главы — разберём, что случилось.

::: tip Как писать такой журнал
В сервисе одна функция пишет строку журнала на каждый запрос: `f.write(json.dumps(запись, ensure_ascii=False) + "\n")` в файл, открытый на дозапись. В больших системах строки отправляют не в файл, а в хранилище журналов (ClickHouse, Elasticsearch, Loki) — но формат «одна строка — один JSON» тот же. Не пишите в журнал лишнего: персональные данные гостей (телефон, имя) туда не кладут.
:::

{{practice: p-jsonl, parse-log, latency-hours, write-log, daily}}

## Практика

## task: versions | Версии окружения | warmup

Соберите `req_text` — текст для `requirements.txt`: по строке `пакет==версия` для `numpy`, `pandas`, `scikit-learn` (именно в таком порядке, строки через `"\n"`). В `sk_version` — версия scikit-learn.

### setup
```python
import numpy, pandas, sklearn
```

### starter
```python
from importlib.metadata import version

```

### check
```python
from importlib.metadata import version as _v
w = '\n'.join(f'{p}=={_v(p)}' for p in ['numpy', 'pandas', 'scikit-learn'])
assert need('req_text', str).strip() == w, f'req_text:\n{need("req_text")}\nа нужно:\n{w}'
assert need('sk_version') == _v('scikit-learn'), 'sk_version — version("scikit-learn").'
```

### hint
`version("pandas")` — строка с версией. Имя для sklearn — `"scikit-learn"`, как при установке.

### hint
`"\n".join(f"{p}=={version(p)}" for p in ["numpy", "pandas", "scikit-learn"])`.

### solution
```python
from importlib.metadata import version

req_text = "\n".join(f"{p}=={version(p)}" for p in ["numpy", "pandas", "scikit-learn"])
sk_version = version("scikit-learn")
print(req_text)
```

## task: p-jsonl | Прочитать журнал | warmup

Соберите код, который читает журнал построчно и печатает число запросов и статус первого из них.

### parsons
```python
import json
with open("service_log.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]
print(len(records))
print(records[0]["status"])
```

### check
```python
import json as _j
n = sum(1 for _ in open('service_log.jsonl', encoding='utf-8'))
s0 = _j.loads(open('service_log.jsonl', encoding='utf-8').readline())['status']
assert _lines == [str(n), str(s0)], f'Сейчас: {_lines}.'
```

### hint
Открыть файл → прочитать все строки в список словарей → напечатать.

## task: cron | Строки расписания | warmup

Заполните словарь `crons` строками cron для расписаний: `"weekly"` — по понедельникам в 6:30; `"nightly"` — каждый день в 2:15; `"every_10"` — каждые 10 минут; `"workdays_9"` — по будням (пн–пт) в 9:00; `"monthly"` — 1-го числа в 3:00.

### starter
```python
crons = {
    "weekly": "",
    "nightly": "",
    "every_10": "",
    "workdays_9": "",
    "monthly": "",
}
```

### check
```python
c = need('crons', dict)
w = {'weekly': '30 6 * * 1', 'nightly': '15 2 * * *', 'every_10': '*/10 * * * *', 'workdays_9': '0 9 * * 1-5', 'monthly': '0 3 1 * *'}
for k, v in w.items():
    got = ' '.join(str(c.get(k, '')).split())
    assert got == v, f'{k}: «{c.get(k)}». Порядок полей: минута час день_месяца месяц день_недели.'
```

### hint
Порядок полей: **минута, час**, день месяца, месяц, день недели. Время 6:30 — это `30 6`, а не `6 30`.

### hint
Каждые 10 минут — `*/10` в поле минут; будни — `1-5` в поле дня недели; 1-е число — `1` в поле дня месяца.

### solution
```python
crons = {
    "weekly": "30 6 * * 1",
    "nightly": "15 2 * * *",
    "every_10": "*/10 * * * *",
    "workdays_9": "0 9 * * 1-5",
    "monthly": "0 3 1 * *",
}
```

## task: batch-job | Пакетный скрипт | base

Модель `MODEL`, паспорт `CARD` и испорченная выгрузка `export.csv` (300 гостей) — в заготовке. Напишите `run_batch(input_path, out_dir, date)` по образцу урока: отложить строки, где `visits_90d < 0`, или `delivery_share` вне 0–1, или `tenure_months < 1` (столбец `reason` — любой непустой текст); годные посчитать; записать `out_dir/scores_<date>.csv` (столбцы `guest_id`, `proba`, `in_campaign`, `model_version`) и `out_dir/rejected_<date>.csv`; вернуть сводку с ключами `n_input`, `n_scored`, `n_rejected`, `n_in_campaign`. Запустите для даты `"2026-12-07"` с папкой `"out"` — сводка в `summary`.

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
MODEL = Pipeline([("prep", _pre), ("model", LogisticRegression(max_iter=2000))]).fit(_X, _g["churned"])
CARD = {"version": "1.0", "features": list(_X.columns), "threshold": 1 / 3}
_w = _g.drop(columns=["churned", "card_blocked"]).sample(300, random_state=1)
_w.loc[_w.index[:5], "visits_90d"] = -1
_w.loc[_w.index[5:8], "delivery_share"] = 35.0
_w.loc[_w.index[8:10], "tenure_months"] = 0
_w.to_csv("export.csv", index=False)
```

### starter
```python
import os
import pandas as pd

def run_batch(input_path, out_dir, date):
    df = pd.read_csv(input_path)
    ...

summary = run_batch("export.csv", "out", "2026-12-07")
print(summary)
```

### check
```python
import pandas as _pd
s = need('summary', dict)
for k in ['n_input', 'n_scored', 'n_rejected', 'n_in_campaign']:
    assert k in s, f'В сводке нет ключа {k}.'
assert s['n_input'] == 300 and s['n_rejected'] == 10 and s['n_scored'] == 290, f'Сводка {s}: из 300 строк должно быть отложено 10 (5 + 3 + 2).'
sc = _pd.read_csv('out/scores_2026-12-07.csv'); rj = _pd.read_csv('out/rejected_2026-12-07.csv')
assert list(sc.columns) == ['guest_id', 'proba', 'in_campaign', 'model_version'], f'Столбцы scores: {list(sc.columns)}.'
assert len(sc) == 290 and len(rj) == 10 and 'reason' in rj.columns, 'rejected — 10 строк со столбцом reason.'
m, C = need('MODEL'), need('CARD')
ex = _pd.read_csv('export.csv').set_index('guest_id').loc[sc['guest_id']]
p = m.predict_proba(ex[C['features']])[:, 1]
assert (abs(sc['proba'].values - p) < 1e-3).all(), 'proba — вероятность ухода от MODEL.'
assert s['n_in_campaign'] == int((p >= C['threshold']).sum()) == int(sc['in_campaign'].sum()), 'n_in_campaign — число гостей с proba ≥ порога из CARD.'
```

### hint
Причины удобно собрать функцией `bad_reason(row)` и `df.apply(bad_reason, axis=1)` — как в уроке, добавив третье условие для `tenure_months`.

### hint
Деление: `good = df[reasons == ""]`, `bad = df[reasons != ""].assign(reason=reasons[reasons != ""])`. Вероятности — только для `good[CARD["features"]]`.

### hint
Запись: `os.makedirs(out_dir, exist_ok=True)`, затем `out.to_csv(f"{out_dir}/scores_{date}.csv", index=False)` и то же для `bad`.

### solution
```python
import os
import pandas as pd

def bad_reason(row):
    if row["visits_90d"] < 0:
        return "visits_90d < 0"
    if not 0 <= row["delivery_share"] <= 1:
        return "delivery_share вне 0–1"
    if row["tenure_months"] < 1:
        return "tenure_months < 1"
    return ""

def run_batch(input_path, out_dir, date):
    df = pd.read_csv(input_path)
    reasons = df.apply(bad_reason, axis=1)
    good = df[reasons == ""]
    bad = df[reasons != ""].assign(reason=reasons[reasons != ""])
    p = MODEL.predict_proba(good[CARD["features"]])[:, 1]
    out = pd.DataFrame({"guest_id": good["guest_id"], "proba": p.round(4),
                        "in_campaign": p >= CARD["threshold"], "model_version": CARD["version"]})
    os.makedirs(out_dir, exist_ok=True)
    out.to_csv(f"{out_dir}/scores_{date}.csv", index=False)
    bad.to_csv(f"{out_dir}/rejected_{date}.csv", index=False)
    return {"date": date, "n_input": len(df), "n_scored": len(out), "n_rejected": len(bad),
            "n_in_campaign": int(out["in_campaign"].sum())}

summary = run_batch("export.csv", "out", "2026-12-07")
print(summary)
```

### explain
Сводка — то, что запуск по расписанию пишет в журнал и что смотрят по утрам. В ней видно главное: сколько пришло, сколько посчитано, сколько отложено. Если в какой-то понедельник `n_rejected` вдруг станет 150 из 300, это повод не отправлять список в CRM, а сначала посмотреть файл отказов: скорее всего, изменилась выгрузка. Типичная ошибка — посчитать вероятности на всей выгрузке, включая плохие строки, а потом их отфильтровать: модель успеет посчитать мусор, а на некоторых плохих значениях может и упасть.

## task: idempotent | Повторный запуск | base

Готовая `run_batch` — в заготовке. Запустите её **дважды** за одну дату `"2026-12-14"` (папка `"out"`) и убедитесь, что файл не задвоился: `rows_after_1`, `rows_after_2` — число строк в `out/scores_2026-12-14.csv` после первого и второго запуска. Затем покажите, как ломается неидемпотентная версия: функция `run_batch_append` (в заготовке) дописывает результаты в общий `out/all_scores.csv`. Удалите этот файл, если он есть, запустите её дважды и сохраните `rows_append` — сколько строк в нём после двух запусков, и `dup_guests` — сколько `guest_id` встречается в нём больше одного раза.

### setup
```python
import os
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
MODEL = Pipeline([("prep", _pre), ("model", LogisticRegression(max_iter=2000))]).fit(_X, _g["churned"])
CARD = {"version": "1.0", "features": list(_X.columns), "threshold": 1 / 3}
_g.drop(columns=["churned", "card_blocked"]).sample(200, random_state=2).to_csv("export_14.csv", index=False)
def _score(path):
    df = pd.read_csv(path)
    p = MODEL.predict_proba(df[CARD["features"]])[:, 1]
    return pd.DataFrame({"guest_id": df["guest_id"], "proba": p.round(4), "in_campaign": p >= CARD["threshold"]})
def run_batch(input_path, out_dir, date):
    os.makedirs(out_dir, exist_ok=True)
    _score(input_path).to_csv(f"{out_dir}/scores_{date}.csv", index=False)
def run_batch_append(input_path, out_dir, date):
    os.makedirs(out_dir, exist_ok=True)
    path = f"{out_dir}/all_scores.csv"
    _score(input_path).assign(date=date).to_csv(path, mode="a", header=not os.path.exists(path), index=False)
```

### starter
```python
import os
import pandas as pd

```

### check
```python
assert need('rows_after_1') == 200 and need('rows_after_2') == 200, f'rows_after_1 = {need("rows_after_1")}, rows_after_2 = {need("rows_after_2")}: после повтора должно остаться 200.'
assert need('rows_append') == 400, f'rows_append = {need("rows_append")}: два запуска с дозаписью дают 400 строк (удалите all_scores.csv перед опытом).'
assert need('dup_guests') == 200, f'dup_guests = {need("dup_guests")}.'
```

### hint
Число строк в CSV — `len(pd.read_csv(путь))`. Считайте его сразу после каждого запуска.

### hint
Повторы: `vc = df["guest_id"].value_counts()` и `int((vc > 1).sum())`. Перед опытом с дозаписью: `if os.path.exists("out/all_scores.csv"): os.remove(...)`.

### solution
```python
import os
import pandas as pd

path = "out/scores_2026-12-14.csv"
run_batch("export_14.csv", "out", "2026-12-14")
rows_after_1 = len(pd.read_csv(path))
run_batch("export_14.csv", "out", "2026-12-14")
rows_after_2 = len(pd.read_csv(path))

if os.path.exists("out/all_scores.csv"):
    os.remove("out/all_scores.csv")
run_batch_append("export_14.csv", "out", "2026-12-14")
run_batch_append("export_14.csv", "out", "2026-12-14")
allf = pd.read_csv("out/all_scores.csv")
rows_append = len(allf)
dup_guests = int((allf["guest_id"].value_counts() > 1).sum())
print(rows_after_1, rows_after_2, rows_append, dup_guests)
```

### explain
Идемпотентная версия после повтора даёт те же 200 строк. Версия с дозаписью — 400, и каждый гость в списке дважды. В CRM это превратится в два письма и два бонуса каждому. Если общий файл всё же нужен (например, для истории), перед дозаписью удаляют строки за ту же дату — это то самое `DELETE ... WHERE date = ...` перед `INSERT`.

## task: parse-log | Журнал в таблицу | base

Прочитайте `service_log.jsonl` в DataFrame `log` (столбец `ts` — дата-время). Отдельно разложите входы в `payload_df` (`pd.json_normalize`). Сохраните `n_requests`, `status_share` — словарь `{статус: доля}` (3 знака), `clients` — отсортированный список клиентов и `period` — кортеж `(первая дата, последняя дата)` строками `"ГГГГ-ММ-ДД"`.

### starter
```python
import json
import pandas as pd

```

### check
```python
import json as _j
import pandas as _pd
L = _pd.DataFrame([_j.loads(x) for x in open('service_log.jsonl', encoding='utf-8')])
l = need('log', _pd.DataFrame)
assert len(l) == len(L) and _pd.api.types.is_datetime64_any_dtype(l['ts']), 'log — все строки журнала; ts — дата-время (pd.to_datetime).'
p = need('payload_df', _pd.DataFrame)
assert len(p) == len(L) and 'visits_90d' in p.columns, 'payload_df — pd.json_normalize(log["payload"].tolist()).'
assert need('n_requests') == len(L), f'n_requests = {need("n_requests")}.'
ws = L['status'].value_counts(normalize=True).round(3)
gs = {int(k): v for k, v in need('status_share', dict).items()}
assert all(close(gs[k], ws[k], 0.0011) for k in ws.index), f'status_share = {gs}.'
assert need('clients', list) == sorted(L['client'].unique()), f'clients = {need("clients")}.'
assert tuple(need('period')) == ('2026-11-02', '2026-11-08'), f'period = {need("period")}.'
```

### hint
Построчное чтение: `[json.loads(line) for line in f]`. Затем `pd.DataFrame(...)` и `pd.to_datetime(log["ts"])`.

### hint
Доли статусов — `value_counts(normalize=True)`. Даты строкой — `log["ts"].min().strftime("%Y-%m-%d")`.

### solution
```python
import json
import pandas as pd

with open("service_log.jsonl", encoding="utf-8") as f:
    log = pd.DataFrame([json.loads(line) for line in f])
log["ts"] = pd.to_datetime(log["ts"])
payload_df = pd.json_normalize(log["payload"].tolist())

n_requests = len(log)
status_share = {int(k): round(float(v), 3) for k, v in log["status"].value_counts(normalize=True).items()}
clients = sorted(log["client"].unique())
period = (log["ts"].min().strftime("%Y-%m-%d"), log["ts"].max().strftime("%Y-%m-%d"))
print(n_requests, status_share, clients, period)
```

### explain
За неделю около 94 % ответов — 200, около 5 % — 500 и около 1 % — 422. Пять процентов падений сервиса — много: это каждый двадцатый гость, которому приложение не смогло показать предложение. Но «в среднем за неделю» скрывает, когда именно это началось. Следующая задача — разложить по дням.

## task: latency-hours | Время ответа и нагрузка | base

Таблица `log` — в заготовке. Для успешных запросов (`status == 200`) посчитайте `p50` и `p95` времени ответа (мс, 1 знак). Посчитайте `by_hour` — число запросов по часу суток (Series с индексом 7…22), `peak_hour` — час с наибольшим числом запросов. Нарисуйте столбчатую диаграмму `by_hour`.

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

```

### check
```python
l = need('log'); ok = l[l['status'] == 200]
assert close(need('p50'), round(ok['latency_ms'].quantile(0.5), 1), 0.051), f'p50 = {need("p50")}: медиана latency_ms только по status == 200.'
assert close(need('p95'), round(ok['latency_ms'].quantile(0.95), 1), 0.051), f'p95 = {need("p95")}.'
w = l.groupby(l['ts'].dt.hour).size()
b = need('by_hour')
assert list(b.index) == list(w.index) and list(b.values) == list(w.values), 'by_hour — число запросов по log["ts"].dt.hour.'
assert need('peak_hour') == w.idxmax(), f'peak_hour = {need("peak_hour")}.'
assert len(ax_of(0).patches) == len(w), 'Нарисуйте столбцы: by_hour.plot(kind="bar").'
```

### hint
Фильтр — `log[log["status"] == 200]`, процентиль — `.quantile(0.95)`.

### hint
`log.groupby(log["ts"].dt.hour).size()` — запросы по часам; `.idxmax()` — самый нагруженный час.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt

ok = log[log["status"] == 200]
p50 = round(ok["latency_ms"].quantile(0.5), 1)
p95 = round(ok["latency_ms"].quantile(0.95), 1)
by_hour = log.groupby(log["ts"].dt.hour).size()
peak_hour = by_hour.idxmax()
print(p50, p95, peak_hour)
ax = by_hour.plot(kind="bar", figsize=(8, 3))
ax.set_xlabel("час"); ax.set_ylabel("запросов за неделю")
```

### explain
Пики нагрузки — утро (8–9), обед (13) и вечер (18–19): гости открывают приложение по пути на работу, в обед и по дороге домой. Сервис должен выдерживать именно пиковый час, а не средний. А p95 за неделю около 125 мс при медиане 56 — очень длинный хвост: похоже, часть недели сервис работал медленнее. Опять же — смотреть надо по времени.

## task: write-log | Записать строку журнала | plus

Напишите `log_request(path, request_id, client, status, latency_ms, error="")`: дописать в файл `path` одну строку JSON с полями `ts` (текущее время, `datetime.now().isoformat(timespec="seconds")`), `request_id`, `client`, `status`, `latency_ms`, `error`; русские буквы — без экранирования; строка заканчивается `"\n"`. Удалите `my_log.jsonl`, если он есть, запишите три запроса из заготовки и прочитайте файл в DataFrame `mine`.

### setup
```python
calls_to_log = [
    ("q-1", "app 3.1", 200, 41.5, ""),
    ("q-2", "web", 422, 9.1, "visits_90d: ожидается целое ≥ 0"),
    ("q-3", "app 3.2", 500, 12.0, "KeyError: 'delivery_share'"),
]
```

### starter
```python
import os
import json
from datetime import datetime
import pandas as pd

def log_request(path, request_id, client, status, latency_ms, error=""):
    ...

```

### check
```python
import json as _j
import pandas as _pd
raw = open('my_log.jsonl', encoding='utf-8').read()
lines = raw.splitlines()
assert len(lines) == 3 and raw.endswith('\n'), f'В my_log.jsonl должно быть ровно 3 строки, каждая с переводом строки в конце (сейчас {len(lines)}). Удалите старый файл перед записью.'
recs = [_j.loads(x) for x in lines]
for k in ['ts', 'request_id', 'client', 'status', 'latency_ms', 'error']:
    assert all(k in r for r in recs), f'В записях нет поля {k}.'
assert 'ожидается' in raw, 'Русские буквы экранированы: ensure_ascii=False.'
assert [r['status'] for r in recs] == [200, 422, 500], 'Статусы — числа, в том порядке, в котором записывали.'
m = need('mine', _pd.DataFrame)
assert len(m) == 3 and list(m['request_id']) == ['q-1', 'q-2', 'q-3'], 'mine — прочитанный my_log.jsonl.'
```

### hint
Дозапись: `with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")`.

### hint
Запись — словарь из всех полей; время — `datetime.now().isoformat(timespec="seconds")`. Три вызова — циклом: `for rid, client, status, ms, err in calls_to_log: log_request("my_log.jsonl", rid, client, status, ms, err)`. Для чтения обратно — тот же приём, что в задаче «Журнал в таблицу».

### solution
```python
import os
import json
from datetime import datetime
import pandas as pd

def log_request(path, request_id, client, status, latency_ms, error=""):
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "request_id": request_id, "client": client,
           "status": status, "latency_ms": latency_ms, "error": error}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

if os.path.exists("my_log.jsonl"):
    os.remove("my_log.jsonl")
for c in calls_to_log:
    log_request("my_log.jsonl", *c)
with open("my_log.jsonl", encoding="utf-8") as f:
    mine = pd.DataFrame([json.loads(line) for line in f])
print(mine)
```

### explain
В эталоне вызов короче: `log_request("my_log.jsonl", *c)`. Звёздочка `*c` распаковывает кортеж в аргументы функции по порядку — то же самое, что перечислить поля в цикле, как в подсказке. Обратите внимание на формат: статус — число, время ответа — число, ошибка — текст. Если записать статус строкой `"200"` в одних местах и числом в других, при анализе `log["status"] == 200` пропустит половину записей. Единый формат журнала — договорённость, которую стоит записать в документацию сервиса.

## task: daily | Отчёт по дням | plus

Таблица `log` — в заготовке. Постройте `daily` — DataFrame с индексом-датой (`log["ts"].dt.date`) и столбцами: `n` — число запросов, `error_rate` — доля ответов не 200 (3 знака), `p95_ms` — 95-й процентиль времени ответа по **успешным** запросам (1 знак). Сохраните `alert_days` — список дат (строки `"ГГГГ-ММ-ДД"`), где `error_rate > 0.02` или `p95_ms > 100`.

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

log["date"] = log["ts"].dt.date

```

### check
```python
import pandas as _pd
l = need('log').copy(); l['date'] = l['ts'].dt.date
n = l.groupby('date').size()
er = l.groupby('date')['status'].apply(lambda s: (s != 200).mean()).round(3)
p = l[l['status'] == 200].groupby('date')['latency_ms'].quantile(0.95).round(1)
d = need('daily', _pd.DataFrame)
assert {'n', 'error_rate', 'p95_ms'} <= set(d.columns) and len(d) == 7, f'daily: 7 строк и столбцы n, error_rate, p95_ms. Сейчас {d.shape}, {list(d.columns)}.'
assert list(d['n'].values) == list(n.values), 'n — число запросов за день.'
assert all(abs(a - b) < 0.0011 for a, b in zip(d['error_rate'].values, er.values)), f'error_rate:\n{d["error_rate"]}\nа нужно\n{er}'
assert all(abs(a - b) < 0.051 for a, b in zip(d['p95_ms'].values, p.values)), f'p95_ms — по успешным запросам:\n{d["p95_ms"]}\nа нужно\n{p}'
wa = [str(k) for k in n.index if er[k] > 0.02 or p[k] > 100]
assert [str(x) for x in need('alert_days', list)] == wa, f'alert_days = {need("alert_days")}, а нужно {wa}.'
```

### hint
Три агрегата посчитайте отдельно и соберите в одну таблицу: `pd.DataFrame({"n": ..., "error_rate": ..., "p95_ms": ...})` — pandas выровняет их по дате.

### hint
Доля ошибок за день: `log.groupby("date")["status"].apply(lambda s: (s != 200).mean())`. Процентиль — по `log[log["status"] == 200]`.

### hint
`alert_days = [str(d) for d, r in daily.iterrows() if r["error_rate"] > 0.02 or r["p95_ms"] > 100]`.

### solution
```python
import pandas as pd

log["date"] = log["ts"].dt.date
daily = pd.DataFrame({
    "n": log.groupby("date").size(),
    "error_rate": log.groupby("date")["status"].apply(lambda s: (s != 200).mean()).round(3),
    "p95_ms": log[log["status"] == 200].groupby("date")["latency_ms"].quantile(0.95).round(1),
})
alert_days = [str(d) for d, r in daily.iterrows() if r["error_rate"] > 0.02 or r["p95_ms"] > 100]
print(daily)
print(alert_days)
```

### explain
Картина по дням совсем другая, чем «в среднем за неделю»: первые три дня спокойные, с 5 ноября время ответа выросло больше чем вдвое, а 7–8 ноября резко выросла доля ошибок — до четверти запросов. Это два разных события, и у каждого своя причина. Разбирать их — проект этой главы. А такой ежедневный отчёт с порогами — простейший **мониторинг**: в работе его считают автоматически и присылают сообщение, когда порог превышен.

## task: cron-match | Проверить расписание | star

Напишите `cron_match(expr, dt)`: вернуть `True`, если момент `dt` (`datetime`) подходит под строку cron из пяти полей. Поддержите в каждом поле `*`, число, список через запятую (`1,15`), диапазон (`1-5`) и шаг (`*/15`). День недели — `dt.isoweekday() % 7` (0 — воскресенье, 1 — понедельник). Посчитайте `n_runs` — сколько раз за неделю 2–8 ноября 2026 (каждую минуту с 00:00 2.11 по 23:59 8.11) сработало бы расписание `"*/30 8-10 * * 1-5"`.

### starter
```python
from datetime import datetime, timedelta

def field_match(field, value):
    ...

def cron_match(expr, dt):
    ...

```

### check
```python
from datetime import datetime as _dt, timedelta as _td
f = need('cron_match')
cases = [
    ('30 6 * * 1', _dt(2026, 11, 2, 6, 30), True),
    ('30 6 * * 1', _dt(2026, 11, 3, 6, 30), False),
    ('0 */6 * * *', _dt(2026, 11, 4, 12, 0), True),
    ('0 */6 * * *', _dt(2026, 11, 4, 13, 0), False),
    ('0 9 * * 1-5', _dt(2026, 11, 7, 9, 0), False),
    ('0 9 * * 1-5', _dt(2026, 11, 6, 9, 0), True),
    ('15 3 1,15 * *', _dt(2026, 12, 15, 3, 15), True),
    ('15 3 1,15 * *', _dt(2026, 12, 16, 3, 15), False),
    ('0 0 * * 0', _dt(2026, 11, 8, 0, 0), True),
    ('*/20 * * 11 *', _dt(2026, 11, 2, 5, 40), True),
    ('*/20 * * 11 *', _dt(2026, 12, 2, 5, 40), False),
]
for e, d, w in cases:
    assert bool(f(e, d)) == w, f'cron_match({e!r}, {d}) должно быть {w}.'
assert need('n_runs') == 30, f'n_runs = {need("n_runs")}: по будням 8:00–10:30 каждые полчаса — 6 запусков в день × 5 дней.'
```

### hint
Разделите задачу: `field_match(field, value)` проверяет одно поле. Поле — список частей через запятую (`field.split(",")`); подходит, если подходит хоть одна часть.

### hint
Часть бывает трёх видов: `"*"` или `"*/n"` (шаг: `value % n == 0`), `"a-b"` (диапазон: `a <= value <= b`), просто число (`value == int(part)`).

### hint
```python
def cron_match(expr, dt):
    m, h, dom, mon, dow = expr.split()
    return (field_match(m, dt.minute) and field_match(h, dt.hour) and field_match(dom, dt.day)
            and field_match(mon, dt.month) and field_match(dow, dt.isoweekday() % 7))
```

### solution
```python
from datetime import datetime, timedelta

def field_match(field, value):
    for part in field.split(","):
        if part == "*":
            return True
        if part.startswith("*/"):
            if value % int(part[2:]) == 0:
                return True
        elif "-" in part:
            a, b = map(int, part.split("-"))
            if a <= value <= b:
                return True
        elif value == int(part):
            return True
    return False

def cron_match(expr, dt):
    m, h, dom, mon, dow = expr.split()
    return (field_match(m, dt.minute) and field_match(h, dt.hour) and field_match(dom, dt.day)
            and field_match(mon, dt.month) and field_match(dow, dt.isoweekday() % 7))

start = datetime(2026, 11, 2)
n_runs = sum(cron_match("*/30 8-10 * * 1-5", start + timedelta(minutes=i)) for i in range(7 * 24 * 60))
print(n_runs)
```

### explain
Расписание «каждые 30 минут с 8 до 10 по будням» срабатывает в 8:00, 8:30, 9:00, 9:30, 10:00 и 10:30 — шесть раз в день, а не четыре, как часто думают: диапазон часов `8-10` включает весь десятый час. Такие ошибки на границах — частая причина «лишних» или «пропущенных» запусков. Перед тем как ставить новое расписание, полезно прогнать его по неделе, как здесь, и посмотреть, когда именно оно сработает.
