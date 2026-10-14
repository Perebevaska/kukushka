---
title: "Учёт экспериментов и воспроизводимость"
files: [guests_churn.csv]
lead: "За месяц работы над моделью набираются десятки запусков: разные модели, параметры, признаки, версии данных. Без журнала через неделю не вспомнить, какой запуск был лучшим и можно ли его повторить. Ведём журнал экспериментов руками, учимся отличать настоящее улучшение от случайного шума и знакомимся с MLflow — инструментом, который делает то же самое автоматически."
recap:
  - "Запуск (run) = параметры + метрики + отпечаток данных + seed + время + артефакт. Записывайте каждый запуск, а не только удачные."
  - "Журнал — обычная таблица: список словарей → DataFrame → CSV с дозаписью (`mode='a'`, заголовок один раз)."
  - "Фиксируйте `random_state`: одинаковый seed → одинаковый результат. Разброс метрики по разным seed — мера шума."
  - "Разница между моделями значима, только если она больше шума: смотрите на разброс по фолдам и на парные разности по тем же фолдам."
  - "Чем больше вариантов вы перебрали на одной валидации, тем оптимистичнее лучший результат. Финальную оценку делают один раз на тесте."
  - "MLflow: `mlflow.start_run()`, `log_params`, `log_metrics`, `sklearn.log_model` — тот же журнал с веб-интерфейсом и реестром моделей."
---

## Зачем журнал экспериментов

Представьте неделю работы над моделью оттока. Понедельник: логистическая регрессия, AUC 0.876. Вторник: добавили признак, 0.881. Среда: лес, 0.902. Четверг: лес поглубже, 0.905, но вы случайно обучили его на обновлённой выгрузке. Пятница: руководитель спрашивает: «Какая лучшая модель, с какими параметрами, на каких данных — и можно ли её повторить?»

Без записей ответ — «кажется, вот эта». Хуже того: если не зафиксирован seed и не записан файл данных, повторить результат невозможно даже с правильными параметрами.

**Учёт экспериментов** (experiment tracking) — привычка записывать каждый запуск: что запускали, с какими настройками, на каких данных и что получилось.

::: sql
Аналогия из инженерии данных: журнал запусков ETL-задач — время старта, параметры, сколько строк загружено, статус. Когда отчёт показал странную цифру, первым делом смотрят журнал: какая загрузка, когда, с какими параметрами. Журнал экспериментов — то же самое для моделей.
:::

## Что записывать про запуск

| Поле | Пример | Зачем |
|---|---|---|
| `run_id` | `run-007` | ссылаться на запуск |
| `time` | `2026-12-03 14:20` | порядок и «когда» |
| `model` | `RandomForest` | что обучали |
| `params` | `max_depth=6, n_estimators=200` | чтобы повторить |
| `seed` | `0` | чтобы повторить точно |
| `data_md5` | `1d0b70…` | на каких данных |
| `sklearn` | `1.8.0` | какой версией библиотеки: от неё зависят параметры по умолчанию и результат |
| `cv_auc_mean`, `cv_auc_std` | `0.905`, `0.013` | результат и его разброс |
| `note` | «добавил признак is_new» | что изменилось и зачем |

Последнее поле кажется лишним, но через месяц именно оно отвечает на вопрос «а что я тут проверял?».

{{practice: run-dict}}

## Журнал руками

Сделаем журнал из самых простых средств: каждый запуск — словарь, журнал — список словарей, на диске — CSV-файл.

```python
import time
import json
import hashlib
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
DATA_MD5 = hashlib.md5(open("guests_churn.csv", "rb").read()).hexdigest()
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)       # одни и те же фолды для всех запусков

def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])

runs = []

def log_run(name, estimator, note=""):
    scores = cross_val_score(make(estimator), X_train, y_train, cv=CV, scoring="roc_auc")
    run = {"run_id": f"run-{len(runs) + 1:03d}", "time": time.strftime("%Y-%m-%d %H:%M"),
           "model": name, "params": json.dumps(estimator.get_params(), default=str), "data_md5": DATA_MD5[:8],
           "sklearn": sklearn.__version__,
           "cv_auc_mean": round(scores.mean(), 4), "cv_auc_std": round(scores.std(), 4), "note": note}
    runs.append(run)
    return run

log_run("LogReg", LogisticRegression(C=1.0, max_iter=2000), "база")
log_run("LogReg", LogisticRegression(C=0.01, max_iter=2000), "сильнее регуляризация")
log_run("Forest", RandomForestClassifier(100, min_samples_leaf=5, random_state=0), "лес")
journal = pd.DataFrame(runs)
print(journal[["run_id", "model", "cv_auc_mean", "cv_auc_std", "note"]])
```

**Что здесь происходит:**

- `CV = StratifiedKFold(..., shuffle=True, random_state=0)` — разбиение на фолды задаём **один раз** и используем во всех запусках. Тогда все модели проверяются на одних и тех же кусках данных, и их можно честно сравнивать.
- `make(estimator)` — конвейер собирается заново для каждого запуска; меняется только модель.
- `estimator.get_params()` — словарь всех параметров модели (включая значения по умолчанию). `json.dumps(...)` превращает его в JSON-строку, чтобы он поместился в одну ячейку таблицы. Именно JSON, а не `str(...)`: у `str` получатся одинарные кавычки и `None`, это не JSON, и `json.loads` такую строку не прочитает. А из JSON-строки модель можно восстановить: `LogisticRegression(**json.loads(строка))` — это задача «Повторить запуск по журналу». `default=str` — страховка: если среди параметров окажется объект, который JSON не знает, он запишется строкой, а не уронит запуск. Набор параметров зависит от версии sklearn: в новых версиях у логистической регрессии появляются и исчезают параметры, и строка `params` для той же модели выйдет другой. Поэтому версию sklearn тоже пишут в журнал.
- `DATA_MD5[:8]` — первых восьми символов отпечатка хватает, чтобы различать версии данных на глаз.
- `cv_auc_std` — разброс AUC по пяти фолдам. Без него среднее мало что значит (ниже увидим почему).
- `pd.DataFrame(runs)` — список словарей превращается в таблицу; ключи стали столбцами.

**Что получилось:** таблица из трёх запусков. Лес заметно лучше логистической регрессии (около 0.90 против 0.88), а разница между двумя регрессиями — в третьем знаке.

Журнал в памяти пропадёт при перезапуске. На диск его дописывают по одной строке:

```python
import os
import pandas as pd

def append_run(run, path="runs.csv"):
    pd.DataFrame([run]).to_csv(path, mode="a", header=not os.path.exists(path), index=False)

if os.path.exists("runs.csv"):
    os.remove("runs.csv")                      # для примера начинаем с чистого журнала
append_run({"run_id": "run-001", "model": "LogReg", "cv_auc_mean": 0.8753})
append_run({"run_id": "run-002", "model": "Forest", "cv_auc_mean": 0.9012})
print(pd.read_csv("runs.csv"))
```

**Что здесь происходит:**

- `mode="a"` (append) — дописать в конец файла, а не перезаписать.
- `header=not os.path.exists(path)` — заголовок пишем, только если файла ещё нет. Иначе строка заголовка повторялась бы перед каждым запуском.

::: warn
Если в следующем запуске у словаря окажутся другие ключи (добавили поле `note`), `to_csv` с дозаписью **не** проверит заголовок: столбцы съедут. Держите набор полей постоянным — заведите функцию `log_run`, которая всегда формирует словарь одного вида, и не собирайте его руками каждый раз.
:::

{{practice: log-csv, grid}}

## Случайность и воспроизводимость

У многих моделей есть случайность: лес выбирает случайные подвыборки и признаки, разбиение на фолды перемешивает строки. Параметр `random_state` (его ещё называют **seed**, «зерно») фиксирует генератор случайных чисел: одинаковое зерно — одинаковая «случайность».

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
X = g[["tenure_months", "visits_90d", "days_since_last", "complaints", "promo_used"]]
y = g["churned"]

a = RandomForestClassifier(50, random_state=1).fit(X, y).predict_proba(X.head(5))[:, 1]
b = RandomForestClassifier(50, random_state=1).fit(X, y).predict_proba(X.head(5))[:, 1]
c = RandomForestClassifier(50, random_state=2).fit(X, y).predict_proba(X.head(5))[:, 1]
print("seed 1:", a.round(3))
print("seed 1:", b.round(3), "— совпадает:", np.array_equal(a, b))
print("seed 2:", c.round(3), "— совпадает:", np.array_equal(a, c))
```

С одинаковым seed результат совпал до последнего знака, с другим — немного отличается. Это два вывода сразу:

1. **Всегда фиксируйте seed** и записывайте его в журнал — иначе результат не повторить.
2. **Разные seed дают разные метрики**, хотя модель «та же». Этот разброс — шум. Улучшение, меньшее шума, — не улучшение.

::: predict
```python static
import numpy as np
r1 = np.random.default_rng(42).random(3)
r2 = np.random.default_rng(42).random(3)
print(np.array_equal(r1, r2))
```

- [x] `True`
- `False`
- `Зависит от компьютера`

Почему: генератор случайных чисел детерминирован — при одинаковом зерне он выдаёт одну и ту же последовательность. «Случайные» числа в компьютере — псевдослучайные. Результат совпадёт и на другом компьютере при той же версии numpy.
:::

{{practice: seed, reproduce}}

## Настоящее улучшение или шум

Сколько шума в нашей оценке? Два источника:

- **разброс по фолдам**: на одних кусках данных модель угадывает лучше, на других хуже — это `cv_auc_std`, у нас около 0.01–0.02;
- **разброс по seed**: та же модель с другим зерном.

Разберём вместе: сравним лес и логистическую регрессию **по одним и тем же фолдам** и посмотрим на разности.

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])

lr = cross_val_score(make(LogisticRegression(max_iter=2000)), X_train, y_train, cv=CV, scoring="roc_auc")
rf = cross_val_score(make(RandomForestClassifier(100, min_samples_leaf=5, random_state=0)), X_train, y_train, cv=CV, scoring="roc_auc")
diff = rf - lr
print("логрег по фолдам:", lr.round(3))
print("лес по фолдам:   ", rf.round(3))
print("разность:        ", diff.round(3))
print(f"средняя разность {diff.mean():.3f}, лес лучше в {(diff > 0).sum()} фолдах из 5")
```

**Что здесь происходит:**

- Обе модели проверены на **одних и тех же** пяти фолдах (одинаковый `CV`). Поэтому их можно сравнивать попарно: фолд 1 с фолдом 1 и т. д.
- `rf - lr` — разность по каждому фолду. Если лес действительно лучше, разность будет положительной почти везде, а не «в среднем».

**Что получилось:** AUC от фолда к фолду гуляет на несколько сотых у обеих моделей — фолды бывают «лёгкие» и «трудные». Но разность устойчиво положительная во всех фолдах: лес лучше на каждом куске данных. Это убедительнее, чем сравнение двух средних с разбросом ±0.02.

::: figure paired-folds
AUC двух моделей на тех же пяти фолдах: точки скачут вверх-вниз вместе, а разность «лес − регрессия» положительна на каждом фолде.
:::

::: note
Почему парное сравнение сильнее. Разброс по фолдам у каждой модели большой, потому что сами фолды разные по трудности. Но на трудном фолде хуже *обе* модели. Разность убирает эту общую часть, и остаётся то, что относится именно к моделям. Это та же идея, что у парного t-теста из урока «Статистические тесты: какой выбрать» главы 5: сравнивают разности у одних и тех же объектов (здесь — фолдов), а не две независимые выборки.
:::

::: quiz
Новая версия модели дала ROC-AUC 0.842 против 0.839 у старой, на одном зерне. Можно ли говорить об улучшении?

- [x] Пока нет: нужно сравнить на нескольких зёрнах или фолдах и посмотреть, больше ли разница шума
  > Разброс от зерна бывает больше 0.003. Парное сравнение на одних и тех же фолдах показывает, устойчив ли выигрыш.
- [ ] Да: 0.842 больше 0.839
  > Больше на одном запуске, но это может быть удача.
- [ ] Нет: улучшение должно быть хотя бы 0.1
  > Порога нет — важно сравнить разницу с шумом.
- [ ] Да, если запуск записан в MLflow
  > Журнал помогает воспроизвести, но не доказывает улучшение.
:::

{{practice: p-cv, paired, seed-noise}}

## Ловушка множественных попыток

Ещё одна опасность — перебрать много вариантов и выбрать лучший по одной и той же валидации. Даже если все варианты одинаково плохи, лучший из них случайно покажется хорошим. Проверим на крайнем случае: 40 «моделей», которые выдают случайные числа.

```python
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y_val = g["churned"].values[:100]          # маленькая валидация — 100 гостей
y_new = g["churned"].values[100:1100]      # «новые данные» — 1000 гостей

seeds = list(range(40))
val_auc = [roc_auc_score(y_val, np.random.default_rng(s).random(100)) for s in seeds]
best = int(np.argmax(val_auc))
new_auc = roc_auc_score(y_new, np.random.default_rng(best).random(1000))
print(f"лучшая из 40 пустышек на валидации: AUC {max(val_auc):.3f}")
print(f"она же на новых данных:            AUC {new_auc:.3f}")
```

::: figure max-of-many
40 пустышек на валидации из 100 гостей: AUC рассыпаны вокруг 0.5, но самая удачная дотянулась до 0.63. На новых данных она же — 0.49.
:::

::: tip Аналогия
Попросите 40 человек подбросить монету по десять раз — кто-нибудь выбросит восемь орлов. Это не талант к монетам, а следствие того, что попыток было много. Лучший результат из многих попыток всегда выше типичного; проверить «талант» можно только новой серией бросков.
:::

**Что получилось:** лучшая «модель» из 40 пустышек показала на валидации AUC выше 0.6 — как будто что-то угадывает. На новых данных — около 0.5, то есть ничего. Это не баг, а статистика: из сорока случайных чисел максимальное всегда заметно больше среднего.

Как защищаются:

1. Финальную проверку делают **один раз** на тесте, который не участвовал в выборе (глава 6).
2. Чем больше вариантов перебираете, тем больше нужна валидация. На 100 гостях различия в 0.03 AUC — шум.
3. Журнал помогает и здесь: в нём видно, сколько попыток было сделано, прежде чем «нашлось» улучшение.

::: quiz
Вы перебрали 40 вариантов модели на валидации из 100 гостей, и лучший показал AUC выше 0.6. Как к этому относиться?

- [x] Как к возможной удаче: максимум из многих случайных результатов всегда выше среднего; честную оценку даст один прогон на тесте, который не участвовал в выборе
  > Именно так пустышки из примера получили выше 0.6 на валидации и около 0.5 на новых данных.
- [ ] Модель точно лучше случайной: 0.6 больше 0.5
  > Пустышки, которые выдают случайные числа, на той же маленькой валидации тоже дали выше 0.6.
- [ ] Нужно перебрать ещё больше вариантов, чтобы найти по-настоящему хороший
  > Чем больше вариантов перебрано на одной валидации, тем сильнее завышен лучший результат.
- [ ] Перепроверить лучший вариант ещё раз на той же валидации
  > Те же 100 гостей повторят ту же удачу — нужна оценка на данных, которые в выборе не участвовали.
:::

{{practice: lucky, honest}}

## MLflow

Всё, что мы сделали руками, делает **MLflow** — самый распространённый открытый инструмент учёта экспериментов. Он хранит запуски, параметры, метрики и файлы моделей и показывает их в веб-интерфейсе с таблицами и графиками. В браузере его нет, код — для вашего компьютера.

```python static
# uv add mlflow scikit-learn pandas
# продолжение примера из раздела «Журнал руками»: запускайте в том же файле после него —
# оттуда берутся make, X_train, y_train, CV, DATA_MD5 и импорт RandomForestClassifier
import mlflow
import mlflow.sklearn
from sklearn.model_selection import cross_val_score

mlflow.set_experiment("churn")                       # группа запусков; создастся, если её нет

for depth in [3, 6, None]:
    est = RandomForestClassifier(200, max_depth=depth, min_samples_leaf=5, random_state=0)
    with mlflow.start_run(run_name=f"forest-depth-{depth}"):
        scores = cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc")
        mlflow.log_params({"model": "forest", "max_depth": depth, "seed": 0, "data_md5": DATA_MD5})
        mlflow.log_metrics({"cv_auc_mean": scores.mean(), "cv_auc_std": scores.std()})
        final = make(est).fit(X_train, y_train)
        mlflow.sklearn.log_model(final, name="model")   # файл модели сохранится рядом с запуском

# в терминале: uv run mlflow ui   → открыть http://127.0.0.1:5000
```

**Что здесь происходит:**

- `mlflow.set_experiment("churn")` — все запуски попадут в эксперимент «churn».
- `with mlflow.start_run(...)` — всё, что залогировано внутри блока `with`, относится к одному запуску. Время, длительность и уникальный идентификатор MLflow запишет сам.
- `log_params` — параметры (что задавали), `log_metrics` — метрики (что получилось). Разделение важно: по метрикам MLflow строит графики и сортирует.
- `mlflow.sklearn.log_model` — сохраняет модель как артефакт запуска вместе с описанием окружения (версии библиотек). Это и есть артефакт из урока «Модель как артефакт: файл, паспорт, контрольный набор», собранный автоматически.
- `mlflow ui` — веб-интерфейс: таблица всех запусков, сортировка по метрике, сравнение нескольких запусков на одном графике.

Что вы увидите, открыв `http://127.0.0.1:5000` (адрес на своём компьютере, порт 5000): слева список экспериментов, справа — таблица запусков эксперимента «churn». Одна строка — один запуск: имя (`forest-depth-6`), время, а в столбцах — параметры (`max_depth`, `seed`) и метрики (`cv_auc_mean`, `cv_auc_std`). Щелчок по заголовку `cv_auc_mean` сортирует запуски, а отметив несколько строк и нажав «Compare», вы получите их параметры и метрики рядом и график. По сути, это наша таблица `journal`, только она пополняется сама и не теряется.

::: tip
У MLflow есть `mlflow.sklearn.autolog()`: одна строка перед обучением, и параметры, метрики на обучении и сама модель логируются автоматически. Удобно для старта, но метрики кросс-валидации и отпечаток данных всё равно лучше логировать явно.
:::

Ещё одна часть MLflow — **реестр моделей** (Model Registry): у выбранного запуска модель получает имя и версию (`churn`, версия 3) и **псевдоним** (alias) — например, `champion`, «та, что сейчас в работе». Сервис на FastAPI из урока «Сервис в работе: пакет, время ответа, FastAPI, тесты» загружает не файл по пути, а модель по псевдониму: `mlflow.sklearn.load_model("models:/churn@champion")`. Выкатить новую версию или откатиться — значит переставить псевдоним на другую версию, не трогая код сервиса. В старых версиях MLflow вместо псевдонимов были стадии (Staging, Production); сейчас они объявлены устаревшими.

## Практика

## task: run-dict | Первая запись журнала | warmup

Создайте пустой список `runs`, добавьте в него два словаря-запуска с ключами `run_id`, `model`, `cv_auc` — `("run-001", "LogReg", 0.875)` и `("run-002", "Forest", 0.901)` — и превратите в таблицу `journal`. В `best_id` — `run_id` строки с наибольшим `cv_auc`.

### starter
```python
import pandas as pd

runs = []

```

### check
```python
import pandas as _pd
r = need('runs', list)
assert len(r) == 2 and all(isinstance(x, dict) for x in r), 'runs — список из двух словарей.'
j = need('journal', _pd.DataFrame)
assert {'run_id', 'model', 'cv_auc'} <= set(j.columns) and len(j) == 2, f'Столбцы journal: {list(j.columns)}.'
assert need('best_id') == 'run-002', f'best_id = {need("best_id")!r}.'
```

### hint
`runs.append({"run_id": "run-001", "model": "LogReg", "cv_auc": 0.875})` — и так же второй. Таблица — `pd.DataFrame(runs)`.

### hint
Строка с максимумом: `journal.loc[journal["cv_auc"].idxmax(), "run_id"]`.

### solution
```python
import pandas as pd

runs = []
runs.append({"run_id": "run-001", "model": "LogReg", "cv_auc": 0.875})
runs.append({"run_id": "run-002", "model": "Forest", "cv_auc": 0.901})
journal = pd.DataFrame(runs)
best_id = journal.loc[journal["cv_auc"].idxmax(), "run_id"]
print(journal, best_id)
```

## task: p-cv | Метрика кросс-валидации | warmup

Соберите код, который оценивает логистическую регрессию кросс-валидацией с фиксированными фолдами и печатает среднее AUC (3 знака).

### setup
```python
import pandas as pd
_g = pd.read_csv("guests_churn.csv")
X = _g[["tenure_months", "visits_90d", "days_since_last", "complaints"]]
y = _g["churned"]
```

### parsons
```python
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_val_score(LogisticRegression(max_iter=1000), X, y, cv=cv, scoring="roc_auc")
print(round(scores.mean(), 3))
```

### check
```python
from sklearn.model_selection import StratifiedKFold as _SK, cross_val_score as _cvs
from sklearn.linear_model import LogisticRegression as _LR
w = round(_cvs(_LR(max_iter=1000), need('X'), need('y'), cv=_SK(n_splits=5, shuffle=True, random_state=0), scoring='roc_auc').mean(), 3)
assert _lines == [str(w)], f'Сейчас: {_lines}.'
```

### hint
Сначала импорты, потом фолды, потом оценка, потом печать.

## task: seed | Одно зерно — один результат | warmup

Обучите три леса `RandomForestClassifier(30, random_state=...)` на `X`, `y` из заготовки: два с `random_state=7` и один с `random_state=8`. Сохраните `same_7` — совпадают ли (`np.array_equal`) их вероятности на первых 20 гостях у двух лесов с зерном 7, и `same_7_8` — у лесов с зёрнами 7 и 8. В `max_gap` — наибольшую разницу вероятностей между лесами 7 и 8 на этих 20 гостях (3 знака).

### setup
```python
import pandas as pd
_g = pd.read_csv("guests_churn.csv")
X = _g[["tenure_months", "visits_90d", "days_since_last", "complaints", "promo_used"]]
y = _g["churned"]
```

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

```

### check
```python
import numpy as _np
from sklearn.ensemble import RandomForestClassifier as _RF
X0, y0 = need('X'), need('y')
a = _RF(30, random_state=7).fit(X0, y0).predict_proba(X0.head(20))[:, 1]
b = _RF(30, random_state=8).fit(X0, y0).predict_proba(X0.head(20))[:, 1]
assert need('same_7') is True or need('same_7') == True, 'same_7: два леса с зерном 7 должны совпасть.'
assert not need('same_7_8'), 'same_7_8: леса с разными зёрнами отличаются.'
assert close(need('max_gap'), round(float(_np.abs(a - b).max()), 3), 0.0011), f'max_gap = {need("max_gap")}.'
```

### hint
Вероятности на первых 20: `модель.predict_proba(X.head(20))[:, 1]`.

### hint
`np.array_equal(p1, p2)` — полное совпадение. Наибольшая разница — `np.abs(p1 - p3).max()`.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

p1 = RandomForestClassifier(30, random_state=7).fit(X, y).predict_proba(X.head(20))[:, 1]
p2 = RandomForestClassifier(30, random_state=7).fit(X, y).predict_proba(X.head(20))[:, 1]
p3 = RandomForestClassifier(30, random_state=8).fit(X, y).predict_proba(X.head(20))[:, 1]
same_7 = np.array_equal(p1, p2)
same_7_8 = np.array_equal(p1, p3)
max_gap = round(float(np.abs(p1 - p3).max()), 3)
print(same_7, same_7_8, max_gap)
```

## task: log-csv | Журнал на диске | base

Напишите `append_run(run, path)`: дописать словарь `run` одной строкой в CSV (`mode="a"`, заголовок — только если файла ещё нет, без индекса). Удалите старый `journal.csv`, если он есть, и запишите в него три запуска из заготовки (`r1`, `r2`, `r3`). Прочитайте файл в `back`. В `n_header_lines` — сколько строк файла начинается с `run_id` (должна быть одна).

### setup
```python
r1 = {"run_id": "run-001", "model": "LogReg", "cv_auc_mean": 0.8753, "note": "база"}
r2 = {"run_id": "run-002", "model": "LogReg", "cv_auc_mean": 0.8811, "note": "C=0.01"}
r3 = {"run_id": "run-003", "model": "Forest", "cv_auc_mean": 0.9012, "note": "лес"}
```

### starter
```python
import os
import pandas as pd

def append_run(run, path):
    ...

if os.path.exists("journal.csv"):
    os.remove("journal.csv")

```

### check
```python
import pandas as _pd
f = need('append_run')
b = need('back', _pd.DataFrame)
assert list(b['run_id']) == ['run-001', 'run-002', 'run-003'], f'В journal.csv должны быть три запуска по порядку, а сейчас: {list(b.get("run_id", []))}.'
assert 'Unnamed: 0' not in b.columns, 'В файле лишний столбец индекса: index=False.'
lines = open('journal.csv', encoding='utf-8').read().splitlines()
assert sum(l.startswith('run_id') for l in lines) == 1, 'Заголовок должен быть в файле один раз: header=not os.path.exists(path).'
assert need('n_header_lines') == 1, f'n_header_lines = {need("n_header_lines")}.'
```

### hint
Одна строка-таблица — `pd.DataFrame([run])`. Дописать: `.to_csv(path, mode="a", header=..., index=False)`.

### hint
Заголовок нужен только для первой записи: `header=not os.path.exists(path)` — до того, как файл создан, условие истинно.

### hint
Подсчёт строк заголовка: `open("journal.csv", encoding="utf-8").read().splitlines()` и `sum(l.startswith("run_id") for l in lines)`.

### solution
```python
import os
import pandas as pd

def append_run(run, path):
    pd.DataFrame([run]).to_csv(path, mode="a", header=not os.path.exists(path), index=False)

if os.path.exists("journal.csv"):
    os.remove("journal.csv")
for r in [r1, r2, r3]:
    append_run(r, "journal.csv")
back = pd.read_csv("journal.csv")
lines = open("journal.csv", encoding="utf-8").read().splitlines()
n_header_lines = sum(l.startswith("run_id") for l in lines)
print(back)
```

### explain
Без `header=not os.path.exists(path)` заголовок повторится перед каждой строкой, и при чтении pandas примет повторные заголовки за данные — в числовом столбце окажется текст «cv_auc_mean». Без `index=False` в файле появится столбец номеров, который при каждом чтении будет превращаться в `Unnamed: 0`. Обе ошибки встречаются в рабочих журналах постоянно.

## task: grid | Серия запусков | base

Функции `make(estimator)` (конвейер) и фолды `CV` — в заготовке. Проведите серию запусков и соберите журнал `journal` (DataFrame) со столбцами `model`, `param`, `cv_auc_mean`, `cv_auc_std` (4 знака) — по строке на запуск:

- логистическая регрессия с `C` из `[0.01, 0.1, 1, 10]` (`max_iter=2000`), `param` — значение `C`;
- лес `RandomForestClassifier(100, max_depth=d, min_samples_leaf=5, random_state=0)` с `d` из `[3, 6]`, `param` — глубина.

Оценка — `cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc")`. Сохраните `best` — строку журнала (Series) с наибольшим средним.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])
```

### starter
```python
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

runs = []

def log(model_name, param, est):
    ...

```

### check
```python
import pandas as _pd
from sklearn.model_selection import cross_val_score as _cvs
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.ensemble import RandomForestClassifier as _RF
mk, Xt, yt, cv = need('make'), need('X_train'), need('y_train'), need('CV')
w = []
for C in [0.01, 0.1, 1, 10]:
    s = _cvs(mk(_LR(C=C, max_iter=2000)), Xt, yt, cv=cv, scoring='roc_auc'); w.append(('LogReg', C, s.mean(), s.std()))
for d in [3, 6]:
    s = _cvs(mk(_RF(100, max_depth=d, min_samples_leaf=5, random_state=0)), Xt, yt, cv=cv, scoring='roc_auc'); w.append(('Forest', d, s.mean(), s.std()))
j = need('journal', _pd.DataFrame)
assert len(j) == 6 and {'model', 'param', 'cv_auc_mean', 'cv_auc_std'} <= set(j.columns), f'journal: 6 строк и столбцы model, param, cv_auc_mean, cv_auc_std. Сейчас: {j.shape}, {list(j.columns)}.'
got = sorted(round(float(v), 4) for v in j['cv_auc_mean'])
want = sorted(round(m, 4) for _, _, m, _ in w)
assert all(abs(a - b) < 0.0012 for a, b in zip(got, want)), f'Средние AUC не совпадают: {got}, а нужно {want}.'
bw = max(w, key=lambda r: r[2])
b = need('best', _pd.Series)
assert close(b['cv_auc_mean'], round(bw[2], 4), 0.0012) and close(float(b['param']), float(bw[1])) and b['model'] == bw[0], f'best — строка с наибольшим cv_auc_mean: {bw[0]} {bw[1]}.'
```

### hint
Функция `log` повторяет одно и то же для любой модели: оценка `cross_val_score` → словарь → `runs.append(...)`. Её вызывают в двух циклах: по `C` и по глубине.

### hint
```python
def log(model_name, param, est):
    s = cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc")
    runs.append({"model": model_name, "param": param, "cv_auc_mean": round(s.mean(), 4), "cv_auc_std": round(s.std(), 4)})
```

### hint
Лучшая строка: `journal.loc[journal["cv_auc_mean"].idxmax()]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

runs = []

def log(model_name, param, est):
    s = cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc")
    runs.append({"model": model_name, "param": param,
                 "cv_auc_mean": round(s.mean(), 4), "cv_auc_std": round(s.std(), 4)})

for C in [0.01, 0.1, 1, 10]:
    log("LogReg", C, LogisticRegression(C=C, max_iter=2000))
for d in [3, 6]:
    log("Forest", d, RandomForestClassifier(100, max_depth=d, min_samples_leaf=5, random_state=0))

journal = pd.DataFrame(runs)
best = journal.loc[journal["cv_auc_mean"].idxmax()]
print(journal)
print(best)
```

### explain
Посмотрите на столбец `cv_auc_std`: у всех запусков он около 0.01–0.02, а разница между регрессиями с разным `C` — меньше 0.01. Значит, выбирать «лучшее C» здесь бессмысленно — это шум. А вот разрыв между лесом и регрессией (около 0.02–0.03) уже стоит проверить парным сравнением — это следующая задача.

## task: paired | Парное сравнение | base

Сравните лес `RandomForestClassifier(100, max_depth=6, min_samples_leaf=5, random_state=0)` и логистическую регрессию (`max_iter=2000`) по одним и тем же фолдам `CV`. Сохраните `diff` — массив разностей AUC «лес − регрессия» по 5 фолдам, `mean_diff` (4 знака), `wins` — в скольких фолдах лес лучше, и `sd_lr` — разброс AUC регрессии по фолдам (`std`, 4 знака). В `paired_clear` — `True`, если лес лучше во всех пяти фолдах.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])
```

### starter
```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

```

### check
```python
import numpy as _np
from sklearn.model_selection import cross_val_score as _cvs
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.ensemble import RandomForestClassifier as _RF
mk, Xt, yt, cv = need('make'), need('X_train'), need('y_train'), need('CV')
l = _cvs(mk(_LR(max_iter=2000)), Xt, yt, cv=cv, scoring='roc_auc')
r = _cvs(mk(_RF(100, max_depth=6, min_samples_leaf=5, random_state=0)), Xt, yt, cv=cv, scoring='roc_auc')
d = r - l
assert _np.allclose(_np.asarray(need('diff')), d, atol=1e-3), 'diff — поэлементная разность AUC по фолдам: лес − регрессия (одинаковые фолды CV!).'
assert close(need('mean_diff'), round(d.mean(), 4), 0.0012), f'mean_diff = {need("mean_diff")}.'
assert need('wins') == int((d > 0).sum()), f'wins = {need("wins")}.'
assert close(need('sd_lr'), round(l.std(), 4), 0.0012), f'sd_lr = {need("sd_lr")}.'
assert bool(need('paired_clear')) == bool((d > 0).all()), 'paired_clear — лес лучше во всех фолдах.'
```

### hint
Две оценки `cross_val_score` с **одним и тем же** `cv=CV` — результаты придут в одинаковом порядке фолдов. Разность массивов — поэлементная.

### hint
`wins = int((diff > 0).sum())`, `paired_clear = bool((diff > 0).all())`.

### solution
```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

lr = cross_val_score(make(LogisticRegression(max_iter=2000)), X_train, y_train, cv=CV, scoring="roc_auc")
rf = cross_val_score(make(RandomForestClassifier(100, max_depth=6, min_samples_leaf=5, random_state=0)),
                     X_train, y_train, cv=CV, scoring="roc_auc")
diff = rf - lr
mean_diff = round(diff.mean(), 4)
wins = int((diff > 0).sum())
sd_lr = round(lr.std(), 4)
paired_clear = bool((diff > 0).all())
print(diff.round(3), mean_diff, wins, sd_lr, paired_clear)
```

### explain
Разброс AUC регрессии по фолдам сопоставим со средней разницей между моделями — по двум средним «с плюс-минусом» не скажешь, кто лучше. Но парные разности положительны во всех фолдах: на каждом куске данных лес выигрывает. Это и есть аргумент для журнала и для руководителя: «лес лучше устойчиво, а не в среднем». Типичная ошибка — задать фолды числом (`cv=5`) у одной модели и объектом `CV` у другой: тогда фолды разные и парное сравнение теряет смысл.

## task: seed-noise | Шум от зерна | plus

Оцените, сколько «шумит» лес из-за случайности. Для `random_state` от 0 до 5 посчитайте среднее AUC кросс-валидации леса `RandomForestClassifier(60, min_samples_leaf=5, random_state=s)` (фолды `CV`). Сохраните `by_seed` — список из 6 средних, `seed_sd` — их стандартное отклонение (4 знака), `seed_range` — размах (макс − мин, 4 знака). Затем сравните с разницей двух глубин из журнала: `depth_gap` — разность средних AUC лесов с `max_depth=6` и `max_depth=3` (оба `random_state=0`, 60 деревьев, `min_samples_leaf=5`), 4 знака. В `gap_within_range` — `True`, если `abs(depth_gap)` меньше `seed_range`, то есть разница глубин укладывается в размах от смены зерна.

Здесь обучается 8 лесов по 5 фолдов — 40 моделей. В браузере расчёт может занять около минуты: это не зависание, дождитесь вывода.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])
```

### starter
```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

def cv_auc(est):
    return cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc").mean()

```

### check
```python
import numpy as _np
from sklearn.model_selection import cross_val_score as _cvs
from sklearn.ensemble import RandomForestClassifier as _RF
mk, Xt, yt, cv = need('make'), need('X_train'), need('y_train'), need('CV')
f = lambda e: _cvs(mk(e), Xt, yt, cv=cv, scoring='roc_auc').mean()
bs = [f(_RF(60, min_samples_leaf=5, random_state=s)) for s in range(6)]
assert _np.allclose(need('by_seed'), bs, atol=1e-3), 'by_seed — средние AUC для random_state 0…5.'
assert close(need('seed_sd'), round(float(_np.std(bs)), 4), 0.0006) and close(need('seed_range'), round(max(bs) - min(bs), 4), 0.0012), 'seed_sd — np.std(by_seed), seed_range — max − min.'
dg = f(_RF(60, max_depth=6, min_samples_leaf=5, random_state=0)) - f(_RF(60, max_depth=3, min_samples_leaf=5, random_state=0))
assert close(need('depth_gap'), round(dg, 4), 0.0012), f'depth_gap = {need("depth_gap")}, а нужно {dg:.4f}.'
assert bool(need('gap_within_range')) == bool(abs(dg) < max(bs) - min(bs)), 'gap_within_range = abs(depth_gap) < seed_range.'
```

### hint
Список по зёрнам: `[cv_auc(RandomForestClassifier(60, min_samples_leaf=5, random_state=s)) for s in range(6)]`.

### hint
Размах — `max(by_seed) - min(by_seed)`. Разница глубин — две оценки `cv_auc` с `max_depth=6` и `max_depth=3`.

### solution
```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

def cv_auc(est):
    return cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc").mean()

by_seed = [cv_auc(RandomForestClassifier(60, min_samples_leaf=5, random_state=s)) for s in range(6)]
seed_sd = round(float(np.std(by_seed)), 4)
seed_range = round(max(by_seed) - min(by_seed), 4)
depth_gap = round(cv_auc(RandomForestClassifier(60, max_depth=6, min_samples_leaf=5, random_state=0))
                  - cv_auc(RandomForestClassifier(60, max_depth=3, min_samples_leaf=5, random_state=0)), 4)
gap_within_range = abs(depth_gap) < seed_range
print(np.round(by_seed, 4), seed_sd, seed_range, depth_gap, gap_within_range)
```

### explain
Смена одного только зерна двигает AUC леса на 0.0044 (от худшего зерна до лучшего). Разница между глубинами 6 и 3 — 0.005, поэтому `gap_within_range = False`: разница чуть больше размаха. Но это не значит «точно не шум». Размах шести зёрен — мягкая граница: на других шести зёрнах он мог выйти и больше 0.005. Да и сама разница посчитана при одном зерне. 0.005 и 0.0044 — числа одного порядка, поэтому честный вывод: «глубина 6, возможно, немного лучше, но уверенности нет». Если «улучшение» от нового параметра такого же размера, как шум от зерна, — вы, возможно, просто нашли удачное зерно. Хорошая практика для важных решений: повторить сравнение на 3–5 зёрнах и смотреть, сохраняется ли разница. В журнале для этого и нужно поле `seed`.

## task: lucky | Удачливая пустышка | plus

Повторите опыт с 40 случайными «моделями» на маленькой валидации и проверьте, как меняется иллюзия с размером валидации. Для `n` из `[50, 200, 1000]`: валидация — первые `n` значений `churned`; «модель» с номером `s` выдаёт `np.random.default_rng(s).random(n)`, `s` от 0 до 39. Сохраните `best_by_n` — словарь `{n: наибольший AUC среди 40 пустышек}` (3 знака). В `shrinks` — `True`, если значения убывают с ростом `n`.

### setup
```python
import pandas as pd
y_all = pd.read_csv("guests_churn.csv")["churned"].values
```

### starter
```python
import numpy as np
from sklearn.metrics import roc_auc_score

```

### check
```python
import numpy as _np
from sklearn.metrics import roc_auc_score as _auc
ya = need('y_all')
w = {n: round(max(_auc(ya[:n], _np.random.default_rng(s).random(n)) for s in range(40)), 3) for n in [50, 200, 1000]}
got = {int(k): v for k, v in need('best_by_n', dict).items()}
assert got == w or all(close(got[k], w[k], 0.0011) for k in w), f'best_by_n = {got}, а нужно {w}.'
assert bool(need('shrinks')) == (w[50] > w[200] > w[1000]), 'shrinks — значения убывают с ростом n.'
```

### hint
Двойной цикл: внешний по `n`, внутренний — по `s in range(40)`. Внутри — `roc_auc_score(y_all[:n], np.random.default_rng(s).random(n))`.

### hint
`best_by_n = {n: round(max(roc_auc_score(...) for s in range(40)), 3) for n in [50, 200, 1000]}`; убывание — `best_by_n[50] > best_by_n[200] > best_by_n[1000]`.

### solution
```python
import numpy as np
from sklearn.metrics import roc_auc_score

best_by_n = {n: round(max(roc_auc_score(y_all[:n], np.random.default_rng(s).random(n)) for s in range(40)), 3)
             for n in [50, 200, 1000]}
shrinks = best_by_n[50] > best_by_n[200] > best_by_n[1000]
print(best_by_n, shrinks)
```

### explain
На 50 гостях лучшая из сорока пустышек выглядит как вполне рабочая модель, на 1000 — иллюзия почти исчезает. Вывод для журнала экспериментов: чем меньше валидация и чем больше попыток, тем меньше доверия к «лучшему» результату. Поэтому кросс-валидацию делают на всей обучающей части, а тест держат нетронутым до самого конца.

## task: reproduce | Повторить запуск по журналу | plus

В заготовке — журнал `journal` (DataFrame) с тремя запусками: у каждого есть `model`, `params` (строка JSON с параметрами), `seed` и `cv_auc_mean`. Напишите `rebuild(row)`, которая по строке журнала создаёт модель: для `"LogReg"` — `LogisticRegression(**params)`, для `"Forest"` — `RandomForestClassifier(**params, random_state=seed)`. Для каждой строки пересчитайте среднее AUC (`make`, `CV` — в заготовке) и сохраните `check_df` — DataFrame со столбцами `run_id`, `logged`, `reproduced` (4 знака) и `ok` (`abs(разница) < 0.0005`). Один из запусков в журнале записан с ошибкой — его `run_id` положите в `broken`.

### setup
```python
import json
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])
_cv = lambda e: round(cross_val_score(make(e), X_train, y_train, cv=CV, scoring="roc_auc").mean(), 4)
journal = pd.DataFrame([
    {"run_id": "run-011", "model": "LogReg", "params": json.dumps({"C": 0.1, "max_iter": 2000}), "seed": 0,
     "cv_auc_mean": _cv(LogisticRegression(C=0.1, max_iter=2000))},
    {"run_id": "run-012", "model": "Forest", "params": json.dumps({"n_estimators": 60, "max_depth": 6, "min_samples_leaf": 5}), "seed": 3,
     "cv_auc_mean": _cv(RandomForestClassifier(60, max_depth=6, min_samples_leaf=5, random_state=3))},
    {"run_id": "run-013", "model": "Forest", "params": json.dumps({"n_estimators": 60, "max_depth": 8, "min_samples_leaf": 5}), "seed": 1,
     "cv_auc_mean": _cv(RandomForestClassifier(60, max_depth=8, min_samples_leaf=5, random_state=4))},
])
```

### starter
```python
import json
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def rebuild(row):
    params = json.loads(row["params"])
    ...

```

### check
```python
import pandas as _pd
c = need('check_df', _pd.DataFrame)
assert list(c.columns)[:4] == ['run_id', 'logged', 'reproduced', 'ok'], f'Столбцы: {list(c.columns)}.'
assert list(c['run_id']) == ['run-011', 'run-012', 'run-013'], 'По строке на каждый запуск журнала, в том же порядке.'
assert list(c['ok']) == [True, True, False], f'ok = {list(c["ok"])}: первые два запуска должны воспроизвестись.'
assert need('broken') == 'run-013', f'broken = {need("broken")!r}.'
r = need('rebuild'); j = need('journal')
assert type(r(j.iloc[1])).__name__ == 'RandomForestClassifier' and r(j.iloc[1]).random_state == 3, 'Для леса передайте random_state=seed из журнала.'
```

### hint
`json.loads(row["params"])` вернёт словарь параметров. Распаковка словаря в аргументы — `**params`: `LogisticRegression(**params)`.

### hint
Для леса зерно лежит в отдельном столбце: `RandomForestClassifier(**params, random_state=int(row["seed"]))`. Пересчёт — `cross_val_score(make(rebuild(row)), X_train, y_train, cv=CV, scoring="roc_auc").mean()`.

### hint
Таблицу удобно собрать циклом `for _, row in journal.iterrows():` в список словарей, а `broken` — `check_df.loc[~check_df["ok"], "run_id"].iloc[0]`.

### solution
```python
import json
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def rebuild(row):
    params = json.loads(row["params"])
    if row["model"] == "LogReg":
        return LogisticRegression(**params)
    return RandomForestClassifier(**params, random_state=int(row["seed"]))

rows = []
for _, row in journal.iterrows():
    rep = round(cross_val_score(make(rebuild(row)), X_train, y_train, cv=CV, scoring="roc_auc").mean(), 4)
    rows.append({"run_id": row["run_id"], "logged": row["cv_auc_mean"], "reproduced": rep,
                 "ok": abs(rep - row["cv_auc_mean"]) < 0.0005})
check_df = pd.DataFrame(rows)
broken = check_df.loc[~check_df["ok"], "run_id"].iloc[0]
print(check_df)
```

### explain
Запуск `run-013` не воспроизвёлся: в журнале записано зерно 1, а модель на самом деле обучали с другим (так бывает, когда журнал заполняют руками, а не той же функцией, что запускает обучение). Разница маленькая, но это именно та ситуация, когда «лучшую модель» невозможно повторить. Лекарство — записывать параметры из самого объекта модели (`get_params()`) в момент запуска, а не переписывать их в журнал отдельно. MLflow делает это автоматически.

## task: honest | Честная финальная оценка | star

Проведите полный цикл выбора, как в работе: на обучающей части кросс-валидацией (`CV`) выберите лучшую из моделей словаря `candidates` (заготовка), затем **один раз** обучите её на всём `X_train` и оцените на `X_test`. Сохраните `cv_table` — Series средних AUC по именам кандидатов, `chosen` — имя лучшего, `cv_best` (4 знака), `test_auc` (4 знака) и `optimism` = `cv_best − test_auc` (4 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
def make(estimator):
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", estimator)])
candidates = {
    "logreg C=0.01": LogisticRegression(C=0.01, max_iter=2000),
    "logreg C=1": LogisticRegression(C=1, max_iter=2000),
    "forest d=4": RandomForestClassifier(80, max_depth=4, min_samples_leaf=5, random_state=0),
    "forest d=8": RandomForestClassifier(80, max_depth=8, min_samples_leaf=5, random_state=0),
}
```

### starter
```python
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score

```

### check
```python
import pandas as _pd
from sklearn.model_selection import cross_val_score as _cvs
from sklearn.metrics import roc_auc_score as _auc
mk, cands, cv = need('make'), need('candidates'), need('CV')
Xt, yt, Xs, ys = need('X_train'), need('y_train'), need('X_test'), need('y_test')
w = _pd.Series({k: _cvs(mk(e), Xt, yt, cv=cv, scoring='roc_auc').mean() for k, e in cands.items()})
ct = need('cv_table', _pd.Series)
assert set(ct.index) == set(w.index) and all(close(ct[k], w[k], 0.0012) for k in w.index), f'cv_table:\n{ct}\nа нужно\n{w.round(4)}'
ch = w.idxmax()
assert need('chosen') == ch, f'chosen = {need("chosen")!r}, а нужно {ch!r}.'
ta = _auc(ys, mk(cands[ch]).fit(Xt, yt).predict_proba(Xs)[:, 1])
assert close(need('cv_best'), round(w.max(), 4), 0.0012), f'cv_best = {need("cv_best")}.'
assert close(need('test_auc'), round(ta, 4), 0.0012), f'test_auc = {need("test_auc")}: обучите выбранную модель на всём X_train и оцените на X_test.'
assert close(need('optimism'), round(w.max() - ta, 4), 0.0025), f'optimism = {need("optimism")}.'
```

### hint
Шаг 1 — таблица: `pd.Series({name: cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc").mean() for name, est in candidates.items()})`.

### hint
Шаг 2 — выбор: `chosen = cv_table.idxmax()`. Шаг 3 — финал: `make(candidates[chosen]).fit(X_train, y_train)` и `roc_auc_score(y_test, ...predict_proba(X_test)[:, 1])`.

### hint
`optimism = round(cv_best - test_auc, 4)` — может оказаться и отрицательным: тест — тоже выборка со своим шумом.

### solution
```python
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score

cv_table = pd.Series({name: cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc").mean()
                      for name, est in candidates.items()})
chosen = cv_table.idxmax()
cv_best = round(cv_table.max(), 4)
final = make(candidates[chosen]).fit(X_train, y_train)
test_auc = round(roc_auc_score(y_test, final.predict_proba(X_test)[:, 1]), 4)
optimism = round(cv_best - test_auc, 4)
print(cv_table.round(4), chosen, cv_best, test_auc, optimism, sep="\n")
```

### explain
Здесь «оптимизм» получился даже отрицательным: на тесте AUC выше, чем на кросс-валидации (около 0.93 против 0.90). Это не значит, что модель «стала лучше» — тестовые 600 гостей просто оказались чуть легче для модели, а разброс AUC между фолдами у нас как раз около ±0.02. Кандидатов всего четыре, и тест подтверждает выбор с точностью до шума. При сотне перебранных вариантов и маленькой выборке он был бы заметным, как в задаче про пустышки. В журнал финального запуска записывают обе цифры: `cv_best` (по ней выбирали) и `test_auc` (честная оценка). Если после теста вы вернулись и поменяли модель — тест «использован», и для честной оценки нужны новые данные.
