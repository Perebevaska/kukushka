---
title: "Модель как артефакт: файл, паспорт, контрольный набор"
files: [guests_churn.csv]
lead: "Модель, которая живёт только в ноутбуке аналитика, бизнесу не помогает. Чтобы ей пользовались другие — CRM, разработчики, коллега через полгода, — её выпускают как артефакт: файл модели, паспорт с описанием, контрольный набор для проверки и номер версии. Разбираем каждую часть по шагам на модели оттока гостей «Зерна»."
recap:
  - "Артефакт модели = файл модели (`joblib`) + паспорт (JSON: версия, признаки, порог, метрики, отпечаток данных, версия sklearn) + контрольный набор (несколько строк и ожидаемые ответы)."
  - "Отпечаток данных — `hashlib.md5(байты_файла).hexdigest()`: любое изменение файла меняет его полностью. Так видно, на каких именно данных обучена модель."
  - "`json.dump` не понимает `np.int64` и `np.bool_` (например, `y.sum()`, `(p > 0.5).any()`): перед записью приводите к `int`, `float`, `bool`, `list`."
  - "Контрольный набор проверяет, что загруженная модель отвечает так же, как при обучении: максимальная разница вероятностей должна быть ~0."
  - "Входной контракт — какие столбцы, типы и категории ждёт модель. Проверка контракта ловит поломки раньше, чем модель молча выдаст чушь."
  - "Версию не перезаписывают: новая модель — новый номер. Перед выпуском сравнивают, у скольких гостей изменится решение."
  - "`joblib.load` выполняет код из файла — открывайте только свои файлы моделей."
---

## Зачем это нужно

В главах 6–8 мы обучили модель оттока: она по анкете гостя оценивает вероятность, что он не придёт ближайшие 60 дней, и по порогу 1/3 решает, давать ли ему бонус удержания. В ноутбуке всё работает. Теперь маркетинг хочет, чтобы каждый понедельник CRM сама получала список гостей для акции.

Вот что обычно ломается при переходе «из ноутбука в работу» — все четыре истории типовые:

1. **Модель не та.** Через три месяца никто не помнит, какой файл — последний, на каких данных он обучен и какая у него была точность. В папке лежат `model.joblib`, `model_new.joblib` и `model_final2.joblib`.
2. **Модель загрузилась, но отвечает иначе.** Её открыли другой версией sklearn — и вероятности сдвинулись. Никто не заметил.
3. **Пришли не те данные.** В выгрузке переименовали столбец или средний чек стал в копейках. Модель молча посчитала ответ — и он бессмысленный.
4. **Порог потерялся.** Разработчик взял `predict()` с порогом 0.5, а экономика кампании требовала 1/3. В акцию попала половина нужных гостей.

От всех четырёх защищает одно: выпускать модель не голым файлом, а **артефактом** — набором из нескольких файлов с описанием.

::: sql
Аналогия из BI: отчёт в Power BI или Superset — это не только сам отчёт. Рядом есть описание источников, дата последнего обновления данных, ответственный, история версий. Без этого через полгода никто не скажет, откуда цифры. С моделью — то же самое.
:::

## Из чего состоит артефакт

| Часть | Что это | От какой беды защищает |
|---|---|---|
| Файл модели | весь конвейер (подготовка + модель), сохранённый `joblib.dump` | не нужно обучать заново |
| Паспорт | JSON-файл: имя, версия, признаки, порог, метрики, отпечаток данных, версия sklearn, дата | «какая это модель и на чём обучена» (беды 1 и 4) |
| Контрольный набор | 20 строк входных данных и ответы модели на них | «загрузилась, но отвечает иначе» (беда 2) |
| Входной контракт | какие столбцы, типы и значения модель ждёт (часть паспорта) | «пришли не те данные» (беда 3) |

::: figure artifact-parts
Папка версии 1.0 и что лежит внутри. Каждая часть закрывает свою беду из списка в начале урока: паспорт — «какая это модель» и «какой порог», контракт в паспорте — «пришли не те данные», контрольный набор — «загрузилась, но отвечает иначе».
:::

Дальше соберём каждую часть руками. Никаких специальных библиотек — только `joblib`, `json` и `hashlib` из стандартной поставки Python.

## Модель, которую выпускаем

Сначала обучим ту самую модель — конвейер из главы 7: пропуски среднего чека заполняем медианой, числа масштабируем, города и любимые категории кодируем, сверху логистическая регрессия.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])     # card_blocked — утечка (глава 6)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
    ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
])
model = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)

proba = model.predict_proba(X_test)[:, 1]
print("AUC на тесте:", round(roc_auc_score(y_test, proba), 3))
print("доля гостей в акции при пороге 1/3:", round((proba >= 1 / 3).mean(), 3))
```

**Что здесь происходит:**

- `X = g.drop(...)` — убираем идентификатор, ответ и утечку. Остаётся 10 признаков — это и будет входом модели в работе.
- `ColumnTransformer` — разная подготовка для числовых (`NUM`) и категориальных (`CAT`) столбцов. Важно: подготовка — **внутри** конвейера, поэтому она сохранится вместе с моделью, и в работе не придётся повторять её руками.
- `predict_proba(X_test)[:, 1]` — вероятность класса 1 (уйдёт) для каждого тестового гостя.
- `proba >= 1 / 3` — решение по порогу из главы 8 (бонус 200 ₽ окупается, если гость уйдёт с вероятностью выше трети).

**Что получилось:** AUC около 0.90 — модель хорошо отличает уходящих от остающихся. В акцию попадает около 21 % гостей. Эти два числа запишем в паспорт: по ним потом будем проверять, не испортилось ли что-то.

Каждый пример урока запускается отдельно, поэтому дальше в трёх примерах повторяется та же подготовка: чтение данных и обучение этого конвейера. Она помечена строкой `# шапка та же, что в разделе «Модель, которую выпускаем»`, а новый код начинается после строки `# ↓ новое в этом примере`. Шапку можно пролистать.

## Файл модели

Напоминание из главы 7: `joblib.dump(объект, имя_файла)` записывает обученный конвейер целиком, `joblib.load(имя_файла)` возвращает его обратно.

```python
# шапка та же, что в разделе «Модель, которую выпускаем»
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
model = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)

# ↓ новое в этом примере
os.makedirs("models/churn/1.0", exist_ok=True)              # папка под версию 1.0
joblib.dump(model, "models/churn/1.0/model.joblib")
print("размер файла:", os.path.getsize("models/churn/1.0/model.joblib"), "байт")

loaded = joblib.load("models/churn/1.0/model.joblib")
print("признаки, которые ждёт модель:", list(loaded.feature_names_in_))
```

**Что здесь происходит:**

- `os.makedirs(путь, exist_ok=True)` создаёт папки (и вложенные), а если они уже есть — не ругается.
- Путь `models/churn/1.0/model.joblib` — договорённость: *модели / задача / версия / файл*. Для версии 1.1 появится соседняя папка, а 1.0 останется как была.
- `os.path.getsize` — размер файла в байтах. Логистическая регрессия весит несколько килобайт, лес из сотен деревьев — мегабайты.
- `loaded.feature_names_in_` — конвейер, обученный на таблице pandas, помнит имена и порядок столбцов. Это готовая основа для входного контракта.

::: warn
`joblib.load` — это `pickle`: при загрузке файл может выполнить любой код. Поэтому открывайте только файлы моделей, которые сохранили вы или ваша команда, из своего хранилища. Файл модели «из интернета» — как макрос в чужом Excel-файле.
:::

{{practice: p-save, size}}

## Отпечаток данных

Как через полгода доказать, что модель обучена именно на этом файле, а не на соседней выгрузке с похожим именем? Записать **отпечаток** (хеш) файла данных. Хеш-функция превращает любые байты в короткую строку, причём:

- одинаковые данные → всегда одинаковая строка;
- изменение хотя бы одного символа → совершенно другая строка.

Посмотрим на игрушечном примере:

```python
import hashlib

for text in ["Зерно", "Зерно", "Зерна"]:
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    print(f"{text!r:8} → {h}")
```

**Что здесь происходит:**

- `text.encode("utf-8")` превращает строку в байты — хеш считается от байтов, а не от букв.
- `hashlib.md5(байты)` — алгоритм MD5; `.hexdigest()` — результат как строка из 32 шестнадцатеричных символов.
- Первые две строки одинаковые — отпечатки совпали. Третья отличается одной буквой — отпечаток не похож вообще.

::: figure md5-fingerprint
Настоящие отпечатки трёх строк из примера: одинаковые строки — одинаковые хеши, одна изменённая буква — хеш не похож вообще.
:::

Для файла — то же самое, только байты берём из файла, открытого в двоичном режиме `"rb"`:

```python
import hashlib

with open("guests_churn.csv", "rb") as f:
    data_md5 = hashlib.md5(f.read()).hexdigest()
print(data_md5)
```

::: predict
```python static
import hashlib
a = hashlib.md5("1,2,3\n".encode()).hexdigest()
b = hashlib.md5("1,2,3".encode()).hexdigest()
print(a == b)
```

- `True`
- [x] `False`
- `Ошибка TypeError`

Почему: строки отличаются невидимым символом перевода строки `\n` в конце, а для хеша важен каждый байт. Поэтому, например, файл, пересохранённый в Excel (другие переводы строк, кодировка), получит другой отпечаток, даже если цифры те же.
:::

::: note
MD5 не годится для защиты паролей — его можно подделать нарочно. Но чтобы заметить случайное изменение файла, его хватает с запасом. Если требуют «по-взрослому», используйте `hashlib.sha256` — интерфейс тот же.
:::

{{practice: md5-text, data-md5}}

## Паспорт модели

Паспорт (в англоязычных командах — *model card*) — обычный словарь Python, сохранённый в JSON. JSON читается и человеком, и любой программой: CRM на Java, сайтом на JavaScript, вами через год.

```python
import json
import hashlib
import sklearn
from datetime import date

card = {
    "name": "churn",
    "version": "1.0",
    "task": "вероятность, что гость не придёт 60 дней",
    "features": ["city", "tenure_months", "app", "visits_90d", "days_since_last",
                 "avg_check", "delivery_share", "fav_category", "promo_used", "complaints"],
    "threshold": 1 / 3,
    # в жизни метрики берут из переменных расчёта: float(auc), float(share);
    # здесь, чтобы пример был коротким, подставлены числа из раздела выше
    "metrics": {"auc_test": 0.896, "share_in_campaign": 0.207},
    "data_md5": hashlib.md5(open("guests_churn.csv", "rb").read()).hexdigest(),
    "sklearn": sklearn.__version__,
    "trained_at": date.today().isoformat(),      # дата обучения, строкой ГГГГ-ММ-ДД
}

with open("card.json", "w", encoding="utf-8") as f:
    json.dump(card, f, ensure_ascii=False, indent=2)

with open("card.json", encoding="utf-8") as f:
    print(f.read()[:300])
```

**Что здесь происходит:**

- `features` — список признаков **в том порядке**, в каком их ждёт модель. Это ядро входного контракта.
- `threshold` — порог решения хранится рядом с моделью. Тот, кто будет её вызывать, возьмёт порог отсюда, а не придумает свой.
- `metrics` — метрики на тесте в момент выпуска. Если в работе модель покажет заметно хуже — это сигнал.
- `sklearn.__version__` — версия библиотеки. Загружать модель стоит той же версией.
- `date.today().isoformat()` — сегодняшняя дата строкой вида `2026-10-13`. Паспорт заполняет код в момент обучения, а не человек руками.
- `json.dump(..., ensure_ascii=False, indent=2)` — без `ensure_ascii=False` русские буквы превратятся в `з...`; `indent=2` делает файл читаемым.

::: warn Ошибка «Object of type int64 is not JSON serializable»
Числа, посчитанные pandas или numpy, — это не обычные `int`, `float` и `bool` Python, а `np.int64`, `np.float64`, `np.bool_`. Модуль `json` знает только стандартные типы. На `np.int64` и `np.bool_` он падает с этой ошибкой: например, `"n_churned": y.sum()` или `"has_vip": (p > 0.5).any()`. `np.float64` — исключение: он наследует обычный `float`, и `json.dumps(np.float64(0.5))` сработает. Лечение одно — привести явно: `int(n)`, `float(x)`, `bool(b)`, `массив.tolist()`. Для `float` это тоже полезно: в паспорте сразу видно, что все числа обычные, и проверки типов вроде `type(x) is float` пройдут. А `len(X_train)` и так обычный `int`.
:::

{{practice: card, decide}}

## Контрольный набор

Паспорт говорит, *какая* это модель. Но как проверить, что загруженный файл отвечает **так же**, как модель в момент обучения? Сохранить несколько строк входных данных вместе с ответами — **контрольный набор** (golden set). После любой загрузки — на сервере, у коллеги, через год — прогоняем эти строки и сравниваем ответы.

::: tip Аналогия
Так обжарщик проверяет новую кофемашину в другой кофейне сети: варит эспрессо из того же зерна по той же рецептуре и сравнивает с эталонной чашкой. Если вкус другой — машину настроили не так, и разбираться надо до того, как кофе пойдёт гостям. Только вкус оценивают на язык, приблизительно, а ответы модели сравнивают числами, с жёстким допуском вроде 1e-9.
:::

```python
# шапка та же, что в разделе «Модель, которую выпускаем»
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
model = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)

# ↓ новое в этом примере
# 1. В момент выпуска: 20 строк + ответы модели
golden = X_test.head(20).copy()
golden["expected"] = model.predict_proba(golden)[:, 1]      # ответы — новым столбцом
golden.to_csv("golden.csv", index=False)

# 2. После загрузки: те же строки → сравнить
joblib.dump(model, "model.joblib")
loaded = joblib.load("model.joblib")
gold = pd.read_csv("golden.csv")
got = loaded.predict_proba(gold.drop(columns=["expected"]))[:, 1]
print("наибольшее расхождение:", np.abs(got - gold["expected"]).max())
```

**Что здесь происходит:**

- `X_test.head(20).copy()` — берём 20 гостей. Лучше включить разные случаи: с пропуском среднего чека, из каждого города. Для примера хватит первых двадцати.
- `golden["expected"] = model.predict_proba(golden)[:, 1]` — в этот момент столбца `expected` ещё нет, поэтому модель получает ровно 10 нужных столбцов. Ответы дописываем новым столбцом.
- При проверке столбец `expected` нужно **убрать** (`drop(columns=["expected"])`): конвейер на таблице pandas проверяет набор столбцов и на лишний столбец ругается.
- `np.abs(got - expected).max()` — наибольшее расхождение по 20 строкам. При правильной загрузке оно порядка 1e-16 (это ошибки округления при записи чисел в CSV) или ровно 0.

::: figure golden-check
Два момента жизни контрольного набора: при выпуске ответы модели записывают рядом со строками, после любой загрузки те же строки прогоняют снова и сравнивают наибольшее расхождение с порогом.
:::

**Что получилось:** расхождение практически нулевое — модель загрузилась корректно. Если бы файл открыли другой версией sklearn и она посчитала иначе, расхождение было бы заметным — например, 0.01 и больше. Порог «нормального» расхождения задают с запасом: например, 1e-9.

::: quiz
Зачем вместе с файлом модели хранить «контрольный набор» — несколько строк с ожидаемыми прогнозами?

- [x] Чтобы после загрузки в новом окружении убедиться, что модель отвечает так же, как при обучении
  > Другая версия библиотеки или испорченный файл могут тихо изменить прогнозы. Контрольный набор ловит это сразу.
- [ ] Чтобы дообучать модель
  > Он для проверки, а не для обучения.
- [ ] Чтобы считать качество модели
  > Качество считают на тесте, а здесь — совпадение прогнозов.
- [ ] Это требование формата файла
  > Формат его не требует — это хорошая практика.
:::

{{practice: golden, release}}

## Входной контракт

Модель ждёт 10 столбцов определённых типов. Что, если в выгрузке столбец переименовали, или вместо чисел пришёл текст, или появился новый город? Часть таких проблем sklearn поймает с ошибкой, а часть — **проглотит молча**: например, `OneHotEncoder(handle_unknown="ignore")` превратит незнакомый город в «никакой город», и модель спокойно посчитает ответ. Поэтому перед моделью ставят проверку контракта.

Разберём вместе: напишем функцию, которая возвращает список проблем (пустой список — всё в порядке).

```python
import pandas as pd

FEATURES = ["city", "tenure_months", "app", "visits_90d", "days_since_last",
            "avg_check", "delivery_share", "fav_category", "promo_used", "complaints"]
KNOWN = {"city": ["Казань", "Пермь", "Тюмень", "Уфа"], "fav_category": ["еда", "кофе", "не кофе"]}

def check_input(df):
    problems = []
    missing = [c for c in FEATURES if c not in df.columns]
    extra = [c for c in df.columns if c not in FEATURES]
    if missing:
        problems.append(f"нет столбцов: {missing}")
    if extra:
        problems.append(f"лишние столбцы: {extra}")
    for c in FEATURES:
        if c in df.columns and c not in KNOWN and not pd.api.types.is_numeric_dtype(df[c]):
            problems.append(f"{c}: ожидаются числа")
    for c, values in KNOWN.items():
        if c in df.columns:
            new = sorted(set(df[c].dropna()) - set(values))
            if new:
                problems.append(f"{c}: незнакомые значения {new}")
    return problems

ok = pd.read_csv("guests_churn.csv").drop(columns=["guest_id", "churned", "card_blocked"]).head(5)
bad = ok.rename(columns={"avg_check": "check"}).assign(city=["Пермь", "Екатеринбург", "Уфа", "Уфа", "Казань"])
print("хорошая выгрузка:", check_input(ok))
print("плохая выгрузка:", check_input(bad))
```

**Что здесь происходит:**

- `missing` и `extra` — списковые выражения: какие нужные столбцы отсутствуют и какие лишние пришли. Переименованный `avg_check` → `check` даст сразу обе проблемы.
- `pd.api.types.is_numeric_dtype(столбец)` — `True`, если столбец числовой. Если в выгрузке среди чисел затесался текст («—», «нет данных»), pandas прочитает весь столбец как текст — и проверка это поймает.
- `set(df[c].dropna()) - set(values)` — разность множеств: значения из выгрузки, которых не было при обучении. `dropna()` — пропуски не считаем «новым значением».
- Функция не падает на первой проблеме, а собирает **все**: так сразу видно, что починить.

**Что получилось:** для хорошей выгрузки — пустой список, для плохой — три проблемы: нет `avg_check`, лишний `check`, незнакомый город «Екатеринбург». Без проверки первая проблема дала бы ошибку sklearn, а третья прошла бы молча.

::: tip
Список известных категорий не надо вписывать руками: обученный `OneHotEncoder` хранит их в `categories_`. Достать можно так: `model.named_steps["prep"].named_transformers_["cat"].categories_`. Их и кладут в паспорт.
:::

{{practice: contract}}

## Версии и что меняется для бизнеса

Правило простое: **файл выпущенной версии не перезаписывают никогда**. Любое изменение — новые данные, другие признаки, другая модель — новая версия в новой папке. Тогда всегда можно ответить «какая модель решала в октябре» и откатиться назад.

Номер обычно из двух-трёх чисел: `1.0` → `1.1` (переобучили на свежих данных, вход тот же) → `2.0` (изменился вход: добавили признак — тем, кто вызывает модель, нужно что-то поменять у себя).

Перед выпуском новой версии полезно посчитать не только метрику, но и **сколько решений изменится**. Допустим, версия 1.1 — лес вместо логистической регрессии. AUC у леса выше, но маркетинг спросит: «а сколько гостей теперь попадут в акцию и сколько выпадут?»

```python
# шапка та же, что в разделе «Модель, которую выпускаем»
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
v10 = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)

# ↓ новое в этом примере: версия 1.1 — лес на тех же данных
v11 = Pipeline([("prep", pre), ("model", RandomForestClassifier(300, min_samples_leaf=5, random_state=0))]).fit(X_train, y_train)

p10, p11 = v10.predict_proba(X_test)[:, 1], v11.predict_proba(X_test)[:, 1]
in10, in11 = p10 >= 1 / 3, p11 >= 1 / 3
print("AUC 1.0:", round(roc_auc_score(y_test, p10), 3), "| AUC 1.1:", round(roc_auc_score(y_test, p11), 3))
print("в акции: 1.0 —", in10.sum(), "гостей, 1.1 —", in11.sum())
print("решение изменилось у", round((in10 != in11).mean() * 100, 1), "% гостей")
```

**Что здесь происходит:**

- Один и тот же `pre` вставлен в оба конвейера — sklearn при `fit` обучит его копию в каждом заново, так что модели независимы.
- `in10 != in11` — поэлементное сравнение двух массивов `True/False`: `True` там, где версии решили по-разному.

**Что получилось:** AUC леса выше (около 0.92 против 0.90), но при том же пороге лес отправляет в акцию заметно больше гостей — у него вероятности по-другому распределены. Решение меняется примерно у каждого одиннадцатого гостя. Значит, перед выпуском 1.1 порог нужно пересчитать (как в главе 8), а маркетинг — предупредить, что бюджет акции изменится.

::: figure version-decisions
Тестовые 600 гостей по решениям двух версий при пороге 1/3: на диагонали решения совпали, в красных клетках — изменились. Лес добавляет в акцию 49 гостей и убирает 5.
:::

::: quiz
У версии 1.1 (лес) AUC выше, чем у 1.0. Что сделать перед выпуском?

- [x] Посчитать, у скольких гостей изменится решение, и пересчитать порог
  > При том же пороге лес отправляет в акцию заметно больше гостей. Метрика ранжирования не говорит, сколько гостей попадёт в акцию, — а бюджет кампании зависит именно от этого.
- [ ] Перезаписать файл версии 1.0 новой моделью — она же лучше
  > Файл выпущенной версии не перезаписывают никогда: иначе не ответить, какая модель решала раньше, и некуда откатиться.
- [ ] Ничего: раз AUC выше, решения останутся те же, только точнее
  > Решение меняется примерно у каждого одиннадцатого гостя — у леса вероятности распределены по-другому.
- [ ] Выпустить под тем же номером 1.0, ведь вход модели не изменился
  > Любое изменение — новая версия. Неизменный вход означает лишь, что это 1.1, а не 2.0.
:::

{{practice: versions}}

## Практика

## task: md5-text | Отпечаток строки | warmup

Посчитайте MD5-отпечатки строк `"Зерно"` и `"зерно"` (с маленькой буквы): `h1` и `h2` — строки из 32 символов (`hexdigest`). В `same` — равны ли они.

### starter
```python
import hashlib

h1 = ...
h2 = ...
same = ...
print(h1, h2, same)
```

### check
```python
import hashlib as _h
w1 = _h.md5('Зерно'.encode('utf-8')).hexdigest(); w2 = _h.md5('зерно'.encode('utf-8')).hexdigest()
assert isinstance(need('h1'), str) and len(need('h1')) == 32, 'h1 — строка из 32 символов: не забудьте .hexdigest().'
assert need('h1') == w1, 'h1 не совпадает: хешируйте "Зерно".encode("utf-8").'
assert need('h2') == w2, 'h2 не совпадает: строка "зерно" с маленькой буквы.'
assert need('same') is False, 'same = (h1 == h2) — они должны отличаться.'
```

### hint
Хеш считается от байтов: сначала строку превращают в байты методом `.encode("utf-8")`.

### hint
`hashlib.md5(байты).hexdigest()` — готовая строка-отпечаток.

### hint
`h1 = hashlib.md5("Зерно".encode("utf-8")).hexdigest()`, аналогично `h2`; `same = h1 == h2`.

### solution
```python
import hashlib

h1 = hashlib.md5("Зерно".encode("utf-8")).hexdigest()
h2 = hashlib.md5("зерно".encode("utf-8")).hexdigest()
same = h1 == h2
print(h1, h2, same)
```

## task: p-save | Сохранить и загрузить | warmup

Соберите код: обучить простую модель, сохранить её в файл, загрузить и напечатать, совпадают ли предсказания.

### setup
```python
import pandas as pd
_g = pd.read_csv("guests_churn.csv")
X = _g[["visits_90d", "days_since_last", "complaints"]]
y = _g["churned"]
```

### parsons
```python
import joblib
from sklearn.linear_model import LogisticRegression
m = LogisticRegression(max_iter=1000).fit(X, y)
joblib.dump(m, "small.joblib")
m2 = joblib.load("small.joblib")
print((m2.predict(X) == m.predict(X)).all())
```

### check
```python
assert _lines == ['True'], f'Сейчас: {_lines}.'
```

### hint
Порядок жизни модели: импорт → обучение → сохранение → загрузка → сравнение.

### hint
Загрузить можно только то, что уже сохранено: `joblib.load` идёт после `joblib.dump`.

## task: size | Сколько весит модель | warmup

Модели `small` (логистическая регрессия) и `big` (лес из 200 деревьев с `min_samples_leaf=5`) обучены в заготовке. Сохраните их в файлы `small.joblib` и `big.joblib` и запишите в `kb_small` и `kb_big` их размеры в килобайтах (байты / 1024, округлить до 1 знака). В `ratio` — во сколько раз лес тяжелее (целое, `round`).

### setup
```python
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
_g = pd.read_csv("guests_churn.csv")
X = _g[["visits_90d", "days_since_last", "complaints", "tenure_months"]]
y = _g["churned"]
small = LogisticRegression(max_iter=1000).fit(X, y)
big = RandomForestClassifier(200, min_samples_leaf=5, random_state=0).fit(X, y)
```

### starter
```python
import os
import joblib

```

### check
```python
import os as _os
assert _os.path.exists('small.joblib') and _os.path.exists('big.joblib'), 'Сохраните обе модели: joblib.dump(small, "small.joblib") и т. д.'
ws, wb = round(_os.path.getsize('small.joblib') / 1024, 1), round(_os.path.getsize('big.joblib') / 1024, 1)
assert close(need('kb_small'), ws, 0.11), f'kb_small = {need("kb_small")}, а файл весит {ws} КБ.'
assert close(need('kb_big'), wb, 0.11), f'kb_big = {need("kb_big")}, а файл весит {wb} КБ.'
assert abs(need('ratio') - round(wb / ws)) <= 1, f'ratio = {need("ratio")}.'
```

### hint
Сначала `joblib.dump(модель, "имя.joblib")`, потом `os.path.getsize("имя.joblib")` — размер в байтах.

### hint
Килобайты: `round(os.path.getsize("small.joblib") / 1024, 1)`. Отношение: `round(kb_big / kb_small)`.

### solution
```python
import os
import joblib

joblib.dump(small, "small.joblib")
joblib.dump(big, "big.joblib")
kb_small = round(os.path.getsize("small.joblib") / 1024, 1)
kb_big = round(os.path.getsize("big.joblib") / 1024, 1)
ratio = round(kb_big / kb_small)
print(kb_small, kb_big, ratio)
```

### explain
Логистическая регрессия хранит несколько чисел-весов — это килобайт. Лес хранит каждое дерево целиком, со всеми узлами, — мегабайты: здесь около 4 МБ, в тысячи раз больше. И это лес с ограничением `min_samples_leaf=5`, как в разделе «Версии». Без него каждое дерево растёт до листьев с одним-двумя гостями, и тот же лес весил бы около 11 МБ. Для одной модели разница не важна, но если сервис держит в памяти десяток моделей или файл нужно передавать по сети каждый день, лучше знать, сколько весит артефакт.

## task: data-md5 | Отпечаток файла | base

Напишите функцию `file_md5(path)`, которая возвращает MD5-отпечаток файла (строка `hexdigest`). Сохраните `data_md5` — отпечаток `guests_churn.csv`. Затем создайте копию файла `guests_copy.csv`, в которой изменено одно число: сохраните `pd.read_csv("guests_churn.csv")` с `tenure_months` первой строки, увеличенным на 1, через `to_csv(..., index=False)`. В `copy_md5` — её отпечаток, в `changed` — отличаются ли отпечатки.

### starter
```python
import hashlib
import pandas as pd

def file_md5(path):
    ...

```

### check
```python
import hashlib as _h
f = need('file_md5')
w = _h.md5(open('guests_churn.csv', 'rb').read()).hexdigest()
assert f('guests_churn.csv') == w, 'file_md5: откройте файл в режиме "rb" и хешируйте f.read().'
assert need('data_md5') == w, 'data_md5 — отпечаток guests_churn.csv.'
import pandas as _pd
c = _pd.read_csv('guests_copy.csv'); o = _pd.read_csv('guests_churn.csv')
assert len(c) == len(o) and c.loc[0, 'tenure_months'] == o.loc[0, 'tenure_months'] + 1, 'В guests_copy.csv у первой строки tenure_months должно быть на 1 больше.'
assert need('copy_md5') == _h.md5(open('guests_copy.csv', 'rb').read()).hexdigest(), 'copy_md5 — отпечаток guests_copy.csv.'
assert need('changed') is True, 'changed = data_md5 != copy_md5.'
```

### hint
Двоичный режим: `with open(path, "rb") as f:` — тогда `f.read()` вернёт байты, которые можно сразу передать в `hashlib.md5`.

### hint
Копия: `g = pd.read_csv(...)`, `g.loc[0, "tenure_months"] += 1`, `g.to_csv("guests_copy.csv", index=False)`.

### hint
```python
def file_md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
```

### solution
```python
import hashlib
import pandas as pd

def file_md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

data_md5 = file_md5("guests_churn.csv")
g = pd.read_csv("guests_churn.csv")
g.loc[0, "tenure_months"] += 1
g.to_csv("guests_copy.csv", index=False)
copy_md5 = file_md5("guests_copy.csv")
changed = data_md5 != copy_md5
print(data_md5, copy_md5, changed)
```

### explain
Одно число из 26 тысяч — и отпечаток другой. Ровно это и нужно: по отпечатку в паспорте модели можно точно сказать, на каком файле она обучена. Обратите внимание: даже без изменения чисел `read_csv` → `to_csv` может дать другой отпечаток (например, `412.0` вместо `412` в столбце с пропусками). Поэтому отпечаток считают от того файла, который действительно подали в обучение.

## task: card | Паспорт модели | base

Модель `model` обучена в заготовке (как в уроке), `X_test`, `y_test` — тест. Соберите словарь `card` с ключами:

- `"name"`: `"churn"`, `"version"`: `"1.0"`;
- `"features"`: список имён признаков из `model.feature_names_in_` (обычный список строк);
- `"threshold"`: `1 / 3`;
- `"auc_test"`: AUC на тесте (3 знака, обычный `float`); для простоты — прямо в `card`, без вложенного словаря `"metrics"`, как в теории;
- `"n_train"`: число обучающих строк (обычный `int`);
- `"data_md5"`: отпечаток `guests_churn.csv`;
- `"sklearn"`: версия sklearn.

Сохраните его в `card.json` (`ensure_ascii=False, indent=2`), загрузите обратно в `card2` и проверьте `card2 == card` — результат в `same`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
model = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)
```

### starter
```python
import json
import hashlib
import sklearn
from sklearn.metrics import roc_auc_score

card = {
    "name": "churn",
    "version": "1.0",
    ...
}

```

### check
```python
import json as _j, hashlib as _h, sklearn as _sk
from sklearn.metrics import roc_auc_score as _auc
c = need('card', dict)
for k in ['name', 'version', 'features', 'threshold', 'auc_test', 'n_train', 'data_md5', 'sklearn']:
    assert k in c, f'В card нет ключа "{k}".'
m, Xt, yt = need('model'), need('X_test'), need('y_test')
assert c['features'] == list(m.feature_names_in_), 'features — list(model.feature_names_in_).'
assert type(c['features']) is list and all(type(s) is str for s in c['features']), 'features — обычный список строк.'
assert close(c['threshold'], 1 / 3), 'threshold = 1 / 3.'
assert type(c['auc_test']) is float and close(c['auc_test'], round(_auc(yt, m.predict_proba(Xt)[:, 1]), 3), 0.0011), f'auc_test = {c["auc_test"]!r}: обычный float с 3 знаками.'
assert type(c['n_train']) is int and c['n_train'] == 1800, f'n_train = {c["n_train"]!r}: обычный int, число строк X_train.'
assert c['data_md5'] == _h.md5(open('guests_churn.csv', 'rb').read()).hexdigest(), 'data_md5 — отпечаток guests_churn.csv.'
assert c['sklearn'] == _sk.__version__, 'sklearn — sklearn.__version__.'
assert _j.load(open('card.json', encoding='utf-8')) == c, 'card.json должен содержать ровно card.'
assert need('same') is True, 'same = card2 == card.'
```

### hint
Признаки: `list(model.feature_names_in_)`. Если проверка скажет «обычный список строк», приведите каждый элемент: `[str(f) for f in model.feature_names_in_]`.

### hint
AUC: `round(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]), 3)`. Если проверка скажет «обычный float», оберните в `float(...)`. Число строк — `len(X_train)`, это уже обычный `int`.

### hint
Запись: `with open("card.json", "w", encoding="utf-8") as f: json.dump(card, f, ensure_ascii=False, indent=2)`. Чтение: `with open("card.json", encoding="utf-8") as f: card2 = json.load(f)`.

### solution
```python
import json
import hashlib
import sklearn
from sklearn.metrics import roc_auc_score

card = {
    "name": "churn",
    "version": "1.0",
    "features": [str(f) for f in model.feature_names_in_],
    "threshold": 1 / 3,
    "auc_test": float(round(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]), 3)),
    "n_train": int(len(X_train)),
    "data_md5": hashlib.md5(open("guests_churn.csv", "rb").read()).hexdigest(),
    "sklearn": sklearn.__version__,
}
with open("card.json", "w", encoding="utf-8") as f:
    json.dump(card, f, ensure_ascii=False, indent=2)
with open("card.json", encoding="utf-8") as f:
    card2 = json.load(f)
same = card2 == card
print(same)
```

### explain
`card2 == card` проверяет, что паспорт пережил запись и чтение без потерь. Он бы не пережил, если положить туда кортеж: JSON вернёт список, и `card2 == card` даст `False`. А `np.int64` (например, `y_train.sum()`) или `np.bool_` запись не переживёт вовсе — ошибка «not JSON serializable». `np.float64` JSON примет, потому что это наследник `float`. В этой версии sklearn `roc_auc_score` и так возвращает обычный `float`, поэтому `float(...)` в эталоне — страховка. Всё, что идёт в JSON, приводят к обычным типам Python — это самая частая ошибка при сохранении паспорта.

## task: golden | Контрольный набор | base

Модель `model` и тест `X_test` — в заготовке. Сохраните контрольный набор `golden.csv`: первые 20 строк `X_test` и столбец `expected` с вероятностью ухода. Сохраните модель в `model.joblib`, загрузите в `loaded` и посчитайте `max_diff` — наибольшую абсолютную разницу между ответами `loaded` на строки из `golden.csv` и столбцом `expected`. В `passed` — `max_diff < 1e-9`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
model = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)
```

### starter
```python
import numpy as np
import pandas as pd
import joblib

```

### check
```python
import numpy as _np
import pandas as _pd
gd = _pd.read_csv('golden.csv')
Xt = need('X_test')
assert len(gd) == 20 and 'expected' in gd.columns, 'golden.csv: 20 строк и столбец expected.'
assert list(gd.drop(columns=['expected']).columns) == list(Xt.columns), 'Кроме expected, в golden.csv должны быть ровно столбцы X_test (index=False при записи).'
w = need('model').predict_proba(Xt.head(20))[:, 1]
assert _np.allclose(gd['expected'], w, atol=1e-12), 'expected — вероятности ухода (predict_proba(...)[:, 1]) для первых 20 строк X_test.'
assert need('max_diff') < 1e-9, f'max_diff = {need("max_diff")}: слишком большая разница — проверьте, что сравниваете со столбцом expected.'
assert need('passed') is True or need('passed') == True, 'passed = max_diff < 1e-9.'
assert 'loaded' in _code and calls('load') >= 1, 'Загрузите модель из файла: loaded = joblib.load("model.joblib").'
```

### hint
Сначала набор: `golden = X_test.head(20).copy()`, потом `golden["expected"] = model.predict_proba(golden)[:, 1]` и `golden.to_csv("golden.csv", index=False)`.

### hint
При проверке уберите столбец ответов, иначе модель не узнает таблицу: `gold.drop(columns=["expected"])`.

### hint
`max_diff = float(np.abs(loaded.predict_proba(gold.drop(columns=["expected"]))[:, 1] - gold["expected"]).max())`.

### solution
```python
import numpy as np
import pandas as pd
import joblib

golden = X_test.head(20).copy()
golden["expected"] = model.predict_proba(golden)[:, 1]
golden.to_csv("golden.csv", index=False)

joblib.dump(model, "model.joblib")
loaded = joblib.load("model.joblib")
gold = pd.read_csv("golden.csv")
got = loaded.predict_proba(gold.drop(columns=["expected"]))[:, 1]
max_diff = float(np.abs(got - gold["expected"]).max())
passed = max_diff < 1e-9
print(max_diff, passed)
```

### explain
Почему расхождение не всегда ровно 0: при записи в CSV число превращается в текст с ограниченным числом знаков, и последний знак может округлиться. Это 1e-16 — в миллиард раз меньше, чем любое значимое изменение. А вот если бы модель загрузили с другим препроцессингом или другой версией библиотеки, расхождения были бы на уровне 1e-3 и больше. Типичная ошибка — забыть `index=False` при записи: тогда в CSV появится столбец `Unnamed: 0`, и модель откажется принимать таблицу с лишним столбцом.

## task: contract | Проверка входа | base

Напишите `check_input(df)` по образцу из урока: вернуть список строк-проблем (пустой — всё хорошо). Проверьте: отсутствующие столбцы (сообщение начинается с `"нет столбцов"`), лишние (`"лишние столбцы"`), нечисловые числовые признаки (`"<столбец>: ожидаются числа"`), незнакомые значения в `city` и `fav_category` (`"<столбец>: незнакомые значения"`). Известные значения возьмите из обученного кодировщика `model` (заготовка). Примените к трём выгрузкам из заготовки: `p_ok`, `p_bad1`, `p_bad2` — списки проблем.

### setup
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
ok = X.head(10).copy()
bad1 = X.head(10).drop(columns=["complaints"]).assign(source="crm")
bad2 = X.head(10).copy()
bad2["avg_check"] = bad2["avg_check"].astype(str).str.replace(".0", " ₽", regex=False)
bad2.loc[3, "fav_category"] = "десерты"
```

### starter
```python
import pandas as pd

FEATURES = [str(f) for f in model.feature_names_in_]
enc = model.named_steps["prep"].named_transformers_["cat"]
KNOWN = {name: [str(v) for v in cats] for name, cats in zip(CAT, enc.categories_)}

def check_input(df):
    problems = []
    ...
    return problems

```

### check
```python
f = need('check_input')
o, b1, b2 = need('ok'), need('bad1'), need('bad2')
r0, r1, r2 = f(o), f(b1), f(b2)
assert r0 == [], f'Для хорошей выгрузки проблем быть не должно, а сейчас: {r0}.'
assert any(s.startswith('нет столбцов') and 'complaints' in s for s in r1), f'bad1: нужна проблема «нет столбцов» с complaints. Сейчас: {r1}.'
assert any(s.startswith('лишние столбцы') and 'source' in s for s in r1), f'bad1: нужна проблема «лишние столбцы» с source. Сейчас: {r1}.'
assert any(s.startswith('avg_check') and 'числа' in s for s in r2), f'bad2: avg_check стал текстом — нужна проблема «avg_check: ожидаются числа». Сейчас: {r2}.'
assert any(s.startswith('fav_category') and 'десерты' in s for s in r2), f'bad2: нужна проблема про незнакомое значение «десерты». Сейчас: {r2}.'
assert len(r1) == 2 and len(r2) == 2, f'Лишние проблемы: bad1 → {r1}, bad2 → {r2}.'
assert need('p_ok') == r0 and need('p_bad1') == r1 and need('p_bad2') == r2, 'p_ok, p_bad1, p_bad2 — результаты check_input для трёх выгрузок.'
```

### hint
Четыре проверки по очереди: отсутствующие (`[c for c in FEATURES if c not in df.columns]`), лишние (наоборот), типы (для числовых признаков — `pd.api.types.is_numeric_dtype(df[c])`), категории (`set(df[c].dropna()) - set(KNOWN[c])`).

### hint
Числовые признаки — те, что есть в `FEATURES`, но нет в `KNOWN`. Не проверяйте тип у столбца, которого нет в таблице: `if c in df.columns`.

### hint
Шаблон одной проверки: `missing = [...]`, затем `if missing: problems.append(f"нет столбцов: {missing}")`. Остальные — так же.

### solution
```python
import pandas as pd

FEATURES = [str(f) for f in model.feature_names_in_]
enc = model.named_steps["prep"].named_transformers_["cat"]
KNOWN = {name: [str(v) for v in cats] for name, cats in zip(CAT, enc.categories_)}

def check_input(df):
    problems = []
    missing = [c for c in FEATURES if c not in df.columns]
    extra = [c for c in df.columns if c not in FEATURES]
    if missing:
        problems.append(f"нет столбцов: {missing}")
    if extra:
        problems.append(f"лишние столбцы: {extra}")
    for c in FEATURES:
        if c in df.columns and c not in KNOWN and not pd.api.types.is_numeric_dtype(df[c]):
            problems.append(f"{c}: ожидаются числа")
    for c, values in KNOWN.items():
        if c in df.columns:
            new = sorted(set(df[c].dropna()) - set(values))
            if new:
                problems.append(f"{c}: незнакомые значения {new}")
    return problems

p_ok, p_bad1, p_bad2 = check_input(ok), check_input(bad1), check_input(bad2)
print(p_ok, p_bad1, p_bad2, sep="\n")
```

### explain
Посмотрите, что сделала бы модель без проверки. `bad1` — sklearn упадёт с ошибкой про столбцы: неприятно, но заметно. `bad2` — средний чек «412 ₽» текстом: sklearn упадёт на масштабировании. А «десерты» — `OneHotEncoder(handle_unknown="ignore")` молча закодирует нулями, и модель посчитает вероятность так, будто любимой категории нет. Это самый опасный тип поломки — без ошибок. Проверка контракта превращает его в явное сообщение.

## task: decide | Решение по паспорту | plus

Напишите `decide(model, card, df)`: на вход — модель, паспорт (словарь) и таблица гостей **с** `guest_id`. Вернуть DataFrame с колонками `guest_id`, `proba` (вероятность ухода, 3 знака) и `in_campaign` (`True`, если `proba` без округления ≥ `card["threshold"]`), отсортированный по `proba` по убыванию. Признаки берите строго из `card["features"]` в этом порядке. Примените к первым 300 гостям файла — результат в `campaign`, и сохраните `n_in` — сколько гостей попало в акцию.

### setup
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
card = {"name": "churn", "version": "1.0", "features": list(X.columns), "threshold": 1 / 3}
new_guests = g.drop(columns=["churned", "card_blocked"]).head(300)
```

### starter
```python
import pandas as pd

def decide(model, card, df):
    ...

campaign = decide(model, card, new_guests)
n_in = ...
print(campaign.head(), n_in)
```

### check
```python
import pandas as _pd
f = need('decide')
m, c, ng = need('model'), need('card', dict), need('new_guests')
p = m.predict_proba(ng[c['features']])[:, 1]
w = _pd.DataFrame({'guest_id': ng['guest_id'].values, 'proba': p}).sort_values('proba', ascending=False)
r = need('campaign', _pd.DataFrame)
assert list(r.columns)[:3] == ['guest_id', 'proba', 'in_campaign'], f'Колонки: {list(r.columns)}.'
assert sorted(r['guest_id']) == sorted(w['guest_id']) and len(r) == len(w), 'В результате должны быть все гости из таблицы, по одному разу.'
assert (r['proba'].diff().dropna() <= 1e-12).all(), 'Порядок гостей: по убыванию вероятности.'
ww = w.set_index('guest_id'); rr = r.set_index('guest_id').loc[ww.index]
assert (abs(rr['proba'].values - ww['proba'].round(3).values) < 1e-9).all(), 'proba — вероятность, округлённая до 3 знаков.'
assert (rr['in_campaign'].values == (ww['proba'] >= c['threshold']).values).all(), 'in_campaign — сравнение неокруглённой вероятности с card["threshold"].'
c2 = dict(c, threshold=0.5)
assert int(f(m, c2, ng)['in_campaign'].sum()) == int((p >= 0.5).sum()), 'Порог берите из паспорта: card["threshold"], а не числом в коде.'
assert need('n_in') == int((p >= c['threshold']).sum()), f'n_in = {need("n_in")}.'
```

### hint
Выбор признаков по паспорту: `df[card["features"]]` — и столбцы нужные, и порядок правильный, а `guest_id` в модель не попадёт.

### hint
Сначала посчитайте неокруглённую вероятность `p`, по ней — `in_campaign = p >= card["threshold"]`, и только потом округляйте для показа: `p.round(3)`.

### hint
```python
p = model.predict_proba(df[card["features"]])[:, 1]
out = pd.DataFrame({"guest_id": df["guest_id"].values, "proba": p.round(3), "in_campaign": p >= card["threshold"]})
return out.sort_values("proba", ascending=False)
```

### solution
```python
import pandas as pd

def decide(model, card, df):
    p = model.predict_proba(df[card["features"]])[:, 1]
    out = pd.DataFrame({"guest_id": df["guest_id"].values, "proba": p.round(3), "in_campaign": p >= card["threshold"]})
    return out.sort_values("proba", ascending=False, kind="stable")

campaign = decide(model, card, new_guests)
n_in = int(campaign["in_campaign"].sum())
print(campaign.head(), n_in)
```

### explain
Два важных места. Признаки берутся по списку из паспорта — значит, лишние столбцы выгрузки (здесь `guest_id`) не попадут в модель, а порядок всегда верный. Решение сравнивается с порогом **до** округления: гость с вероятностью 0.3334 в акции, а округлённое 0.333 < 1/3 его бы выкинуло. Такие ошибки на границе незаметны в отчёте, но меняют списки.

## task: versions | Что изменит новая версия | plus

В заготовке обучены `v10` (логистическая регрессия) и `v11` (лес). Для тестовых гостей посчитайте решения обеих версий при пороге 1/3. Сохраните `auc10`, `auc11` (3 знака), `n10`, `n11` — сколько гостей в акции у каждой версии, `flip` — долю гостей, у которых решение изменилось (3 знака), `newly_in` — сколько гостей попадёт в акцию только в 1.1, и `thr11` — порог для версии 1.1, при котором в акцию попадёт столько же гостей, сколько в 1.0 (возьмите `n10`-ю по величине вероятность версии 1.1, 3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
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
pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
v10 = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)
v11 = Pipeline([("prep", pre), ("model", RandomForestClassifier(300, min_samples_leaf=5, random_state=0))]).fit(X_train, y_train)
```

### starter
```python
import numpy as np
from sklearn.metrics import roc_auc_score

p10 = v10.predict_proba(X_test)[:, 1]
p11 = v11.predict_proba(X_test)[:, 1]

```

### check
```python
import numpy as _np
from sklearn.metrics import roc_auc_score as _auc
a, b, yt = need('v10').predict_proba(need('X_test'))[:, 1], need('v11').predict_proba(need('X_test'))[:, 1], need('y_test')
i10, i11 = a >= 1 / 3, b >= 1 / 3
assert close(need('auc10'), round(_auc(yt, a), 3), 0.0011) and close(need('auc11'), round(_auc(yt, b), 3), 0.0011), 'auc10, auc11 — roc_auc_score на тесте, 3 знака.'
assert need('n10') == int(i10.sum()) and need('n11') == int(i11.sum()), f'n10 = {need("n10")}, n11 = {need("n11")}: число True в решениях.'
assert close(need('flip'), round(float((i10 != i11).mean()), 3), 0.0011), f'flip = {need("flip")}.'
assert need('newly_in') == int((i11 & ~i10).sum()), f'newly_in = {need("newly_in")}: в акции у 1.1, но не у 1.0.'
t = round(float(_np.sort(b)[::-1][int(i10.sum()) - 1]), 3)
assert close(need('thr11'), t, 0.0011), f'thr11 = {need("thr11")}, а нужно {t}.'
```

### hint
Решения: `in10 = p10 >= 1 / 3`, `in11 = p11 >= 1 / 3`. Изменилось — `in10 != in11`; «только в 1.1» — `in11 & ~in10` (`~` — «не»).

### hint
Порог с тем же числом гостей: отсортируйте вероятности 1.1 по убыванию — `np.sort(p11)[::-1]` — и возьмите элемент с номером `n10 - 1` (нумерация с нуля).

### hint
`thr11 = round(float(np.sort(p11)[::-1][n10 - 1]), 3)`.

### solution
```python
import numpy as np
from sklearn.metrics import roc_auc_score

p10 = v10.predict_proba(X_test)[:, 1]
p11 = v11.predict_proba(X_test)[:, 1]
in10, in11 = p10 >= 1 / 3, p11 >= 1 / 3
auc10, auc11 = round(roc_auc_score(y_test, p10), 3), round(roc_auc_score(y_test, p11), 3)
n10, n11 = int(in10.sum()), int(in11.sum())
flip = round(float((in10 != in11).mean()), 3)
newly_in = int((in11 & ~in10).sum())
thr11 = round(float(np.sort(p11)[::-1][n10 - 1]), 3)
print(auc10, auc11, n10, n11, flip, newly_in, thr11)
```

### explain
Лес ранжирует гостей лучше (AUC выше), но его вероятности распределены иначе: при том же пороге 1/3 в акцию попадает заметно больше людей, и бюджет вырастет. Если маркетинг хочет прежний размер акции, порог для 1.1 нужно поднять до `thr11`. Это и есть главный вывод: «новая модель лучше по метрике» — не повод молча подменить файл. Новая версия — новый паспорт с новым порогом, и разговор с теми, кто пользуется решениями.

## task: release | Проверка перед выпуском | star

Соберите функцию `release_check(model, card, golden_path, X_test, y_test)`, которая возвращает словарь из трёх проверок (`True`/`False`):

- `"features"` — `list(model.feature_names_in_)` совпадает с `card["features"]`;
- `"golden"` — расхождение с контрольным набором из `golden_path` меньше `1e-9`;
- `"auc"` — AUC модели на тесте не ниже `card["auc_test"] − 0.01`.

В заготовке есть модель `good`, её паспорт `card` и контрольный набор `golden.csv`, а также модель `retrained` — та же схема, но обученная на другой половине данных (кто-то «случайно» переобучил и положил в ту же папку). Сохраните `res_good = release_check(good, ...)` и `res_bad = release_check(retrained, ...)`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
g = pd.read_csv("guests_churn.csv")
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, g["churned"], test_size=0.25, random_state=42, stratify=g["churned"])
NUM = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check", "delivery_share", "promo_used", "complaints"]
CAT = ["city", "fav_category"]
def _make():
    pre = ColumnTransformer([("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    return Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
good = _make().fit(X_train, y_train)
retrained = _make().fit(X_train.iloc[::2], y_train.iloc[::2])
card = {"features": list(X.columns), "auc_test": round(roc_auc_score(y_test, good.predict_proba(X_test)[:, 1]), 3)}
_gold = X_test.head(20).copy()
_gold["expected"] = good.predict_proba(_gold)[:, 1]
_gold.to_csv("golden.csv", index=False)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

def release_check(model, card, golden_path, X_test, y_test):
    ...

```

### check
```python
f = need('release_check')
rg, rb = need('res_good', dict), need('res_bad', dict)
assert set(rg) == {'features', 'golden', 'auc'}, f'Ключи словаря: {sorted(rg)}.'
assert all(bool(v) for v in rg.values()), f'Для good все проверки должны пройти, а сейчас: {rg}.'
assert bool(rb['features']) and not bool(rb['golden']), f'retrained: признаки те же, а контрольный набор должен не пройти. Сейчас: {rb}.'
m, c, Xt, yt = need('good'), dict(need('card')), need('X_test'), need('y_test')
c2 = dict(c, auc_test=0.99)
assert not bool(f(m, c2, 'golden.csv', Xt, yt)['auc']), 'Проверка auc: AUC на тесте >= card["auc_test"] - 0.01 (с паспортом auc_test=0.99 должна не пройти).'
c3 = dict(c, features=list(reversed(c['features'])))
assert not bool(f(m, c3, 'golden.csv', Xt, yt)['features']), 'Проверка features: важен и порядок признаков.'
```

### hint
Каждая проверка — одно сравнение. Начните со скелета: `return {"features": ..., "golden": ..., "auc": ...}`.

### hint
Контрольный набор — как в задаче «Контрольный набор»: прочитать CSV, убрать `expected`, сравнить вероятности, взять максимум модуля разницы.

### hint
```python
gold = pd.read_csv(golden_path)
diff = np.abs(model.predict_proba(gold.drop(columns=["expected"]))[:, 1] - gold["expected"]).max()
auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
```
Сравнения дают `np.bool_` — оберните их в `bool(...)`, как в паспорте: `"golden": bool(diff < 1e-9)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

def release_check(model, card, golden_path, X_test, y_test):
    gold = pd.read_csv(golden_path)
    diff = np.abs(model.predict_proba(gold.drop(columns=["expected"]))[:, 1] - gold["expected"]).max()
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    return {
        "features": [str(f) for f in model.feature_names_in_] == list(card["features"]),
        "golden": bool(diff < 1e-9),
        "auc": bool(auc >= card["auc_test"] - 0.01),
    }

res_good = release_check(good, card, "golden.csv", X_test, y_test)
res_bad = release_check(retrained, card, "golden.csv", X_test, y_test)
print(res_good, res_bad, sep="\n")
```

### explain
Переобученная на половине данных модель по качеству почти такая же — проверка AUC её, скорее всего, пропустит, и признаки у неё те же. Но контрольный набор сразу показывает: это **другая** модель, её ответы отличаются. Ровно этого мы и хотели — заметить подмену файла, а не только явную порчу. Такую функцию запускают автоматически перед каждой выкладкой; в больших командах её роль играют тесты в CI (об этом — в уроке «Упаковка и запуск: окружение, Docker, расписание, журнал»).
