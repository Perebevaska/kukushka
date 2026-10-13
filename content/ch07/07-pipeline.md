---
title: "Pipeline: предобработка и модель вместе"
lead: "До сих пор мы готовили данные руками: `get_dummies`, `fillna`, масштабирование — и повторяли то же самое для теста и новых гостей. Соберём всю подготовку и модель в один объект-конвейер: он сам учится на обучающей части, одинаково обрабатывает любые новые строки и честно проходит кросс-валидацию."
files: [guests_churn.csv]
recap:
  - "Предобработка тоже «учится» на данных: заполнитель пропусков запоминает значение, масштабирование — среднее и разброс, кодировщик — список категорий. Учить её можно только на обучающей части."
  - "`SimpleImputer(strategy=...)` заполняет пропуски, `OneHotEncoder(handle_unknown=\"ignore\")` делает флаги категорий и не падает на новых значениях (у новой категории все флаги — 0)."
  - "`ColumnTransformer([(имя, обработка, столбцы), ...])` применяет разную обработку к разным столбцам и склеивает результат."
  - "`Pipeline([(\"prep\", ...), (\"model\", ...)])` — цепочка шагов: `fit` учит все шаги по очереди, `predict` прогоняет новые строки через те же шаги. `make_pipeline` придумывает имена шагов сам."
  - "Конвейер принимает «сырую» таблицу — такую, какой её выгружают из базы. Новые гости обрабатываются ровно так же, как обучающие."
  - "`cross_val_score(pipe, X, y, cv=kf)` переобучает всю предобработку на каждом фолде — утечки из проверочной части нет."
---

## Подготовка данных тоже учится

Вспомним стандартную подготовку гостей из главы 6:

```python static
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
```

Здесь три действия: убрать лишние столбцы, превратить категории в флаги, заполнить пропуски. А в уроке «Масштабирование и ближайшие соседи» добавилось четвёртое — масштабирование, и там же мы выяснили, что `StandardScaler` нужно учить только на обучающей части, а к тесту применять готовым. Получается целая инструкция, которую надо повторять для теста, для кросс-валидации и для каждой новой выгрузки гостей — и где легко ошибиться.

Вот типичная ошибка. Модель училась на `get_dummies` от всей таблицы, а завтра пришли три новых гостя — и в их выгрузке нет, например, Уфы:

```python error
import pandas as pd
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
model = LogisticRegression(max_iter=2000).fit(X, y)

new = g.drop(columns=["guest_id", "churned", "card_blocked"]).head(3)
print(new["city"].tolist())
X_new = pd.get_dummies(new, dtype=int).fillna({"avg_check": 0})
model.predict(X_new)
```

`get_dummies` сделал флаги только для городов, которые есть в трёх строках, — столбцов стало меньше, и модель отказывается работать. В главе 6 мы чинили это `reindex(columns=X_train.columns, fill_value=0)`. Работает, но это ещё одна ручная операция, о которой надо помнить.

Идея этого урока: у каждого шага подготовки, как у модели, есть `fit` (запомнить что-то по обучающим данным) и `transform` (применить запомненное к любым строкам). Тогда всю подготовку можно склеить с моделью в один объект.

::: figure prep-learns
Что каждый шаг подготовки запоминает на `fit` и что делает на `transform`. Запоминают — только по обучающей части, применяют — ко всем таблицам одинаково.
:::

{{practice: median-imp}}

## Пропуски и категории: SimpleImputer и OneHotEncoder

Для пропусков в sklearn есть **SimpleImputer** — «простой заполнитель». Стратегия задаёт, чем заполнять: `"mean"` (среднее), `"median"` (медиана), `"most_frequent"` (самое частое) или `"constant"` (заданное число `fill_value`). Средний чек пуст у гостей без визитов, и честное значение там — 0 (проект главы 6):

```python
import pandas as pd
from sklearn.impute import SimpleImputer

g = pd.read_csv("guests_churn.csv")
imp = SimpleImputer(strategy="constant", fill_value=0)
filled = imp.fit_transform(g[["avg_check"]])
print(g["avg_check"].isna().sum(), "пропусков было")
print(filled[:3])
```

`fit_transform` возвращает массив numpy, а не таблицу. Двойные скобки `g[["avg_check"]]` — потому что преобразователи sklearn ждут таблицу (даже из одного столбца), а не отдельный столбец.

Со стратегией `"median"` разница между `fit` и `transform` видна лучше: `fit` запоминает медиану обучающих данных в `imp.statistics_`, `transform` подставляет именно её — в любые строки, хоть в тест, хоть в завтрашнюю выгрузку.

Категории превращает во флаги **OneHotEncoder** — «one-hot кодировщик», аналог `get_dummies`. Разница в том, что он запоминает список категорий при `fit`:

```python
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

train = pd.DataFrame({"city": ["Пермь", "Казань", "Тюмень", "Уфа", "Пермь"]})
new = pd.DataFrame({"city": ["Уфа", "Екатеринбург"]})

ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
ohe.fit(train)
print(ohe.get_feature_names_out())
print(ohe.transform(new))
```

- `handle_unknown="ignore"` — если в новых данных встретилась категория, которой не было при обучении (Екатеринбург), не падать, а поставить все флаги в 0. Без этого параметра будет ошибка;
- `sparse_output=False` — вернуть обычный массив. По умолчанию кодировщик возвращает «разреженную» матрицу (хранит только единицы — экономит память, когда категорий тысячи), а её неудобно печатать;
- `get_feature_names_out()` — имена получившихся столбцов, как у `get_dummies`: `столбец_значение`.

::: predict
```python static
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
ohe.fit(pd.DataFrame({"fav": ["кофе", "еда", "кофе"]}))
print(ohe.transform(pd.DataFrame({"fav": ["чай"]})).sum())
```

- `1.0`
- [x] `0.0`
- `Ошибка ValueError`

Почему: кодировщик знает только «еда» и «кофе». «Чай» — новая категория, и с `handle_unknown="ignore"` оба флага получают 0, сумма — 0.
:::

{{practice: ohe-new}}

## ColumnTransformer: каждому столбцу — своя обработка

В таблице гостей два вида столбцов: числовые (их заполняем и масштабируем) и категориальные (их кодируем). **ColumnTransformer** — «преобразователь по столбцам» — принимает список троек `(имя, обработка, столбцы)`, применяет каждую обработку к своим столбцам и склеивает результаты бок о бок.

Числовым столбцам нужны два шага подряд — заполнить, потом масштабировать. Цепочку шагов собирает `make_pipeline`:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]

pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
Xt = pre.fit_transform(X_train)
print(X_train.shape, "→", Xt.shape)
print(pre.get_feature_names_out()[[0, 7, 8, 14]])
```

Обратите внимание: `X` теперь «сырой» — без `get_dummies` и `fillna`, с текстовыми городами и пропусками. Всю подготовку делает `pre`:

- 8 числовых столбцов → заполнены нулём и отмасштабированы → 8 столбцов;
- 2 категориальных → 4 флага городов + 3 флага любимой категории → 7 столбцов;
- итого 15 столбцов; к именам добавлена приставка шага: `num__…`, `cat__…`.

::: figure col-transformer
`ColumnTransformer` из примера: числовые столбцы заполняются и масштабируются, текстовые превращаются во флаги, результаты склеиваются в 15 столбцов. Всё, что не попало ни в один список, выбрасывается.
:::

`pre.fit_transform(X_train)` учит все шаги на обучающей части. Для теста — только `pre.transform(X_test)`: средние, разбросы и списки категорий берутся из обучения.

::: warn
Столбцы, которые не попали ни в один список, ColumnTransformer по умолчанию **выбрасывает** (`remainder="drop"`). Это удобно для `guest_id`, но если забыть добавить в список новый признак, модель его просто не увидит — без всякой ошибки. После сборки проверяйте `get_feature_names_out()`.
:::

::: sql
ColumnTransformer похож на `SELECT` с выражениями для разных столбцов: `COALESCE(avg_check, 0)` для одних, `CASE WHEN city = ... THEN 1 ELSE 0 END` для других — и всё в одной строке результата.
:::

{{practice: prep-shape}}

## Pipeline: подготовка и модель — один объект

**Pipeline** (конвейер) — цепочка шагов, где последний шаг — модель. Шаги задаются списком пар `(имя, объект)`:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])

pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
pipe.fit(X_train, y_train)
print("доля правильных на тесте:", round(pipe.score(X_test, y_test), 3))
```

Что происходит внутри:

- `pipe.fit(X_train, y_train)` — `prep` учится на `X_train` и преобразует его, потом модель учится на результате;
- `pipe.predict(X_test)`, `pipe.predict_proba(X_test)`, `pipe.score(X_test, y_test)` — `X_test` проходит через **уже обученный** `prep` (только `transform`), потом через модель.

Снаружи конвейер выглядит как обычная модель: у него те же `fit`, `predict`, `predict_proba`, `score`. Доля правильных — около 0.88, как у логистической регрессии на признаках из `get_dummies` (уроки «Порог, PR- и ROC-кривые» и «Дисбаланс классов»): мы ничего не поменяли в модели, только упаковали подготовку.

Добраться до шага можно по имени: `pipe.named_steps["model"].coef_` — коэффициенты модели, `pipe.named_steps["prep"].get_feature_names_out()` — имена признаков, к которым они относятся.

`make_pipeline(шаг1, шаг2, ...)` — короткая запись без имён: шаги называются по классу маленькими буквами. Мы уже пользовались ей для числовых столбцов.

::: predict
```python static
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
print(list(make_pipeline(StandardScaler(), LogisticRegression()).named_steps))
```

- `['scaler', 'model']`
- [x] `['standardscaler', 'logisticregression']`
- `['step0', 'step1']`

Почему: `make_pipeline` называет шаги по имени класса в нижнем регистре. Если нужны свои короткие имена (`prep`, `model`) — используйте `Pipeline([...])`.
:::

### Прогноз по сырой таблице

Главная польза — новых гостей можно подавать в том виде, в каком их выгружают из базы: с текстовыми городами, пропусками и даже с городом, которого не было в обучении.

```python
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X, y)

new = pd.DataFrame({
    "city": ["Казань", "Екатеринбург", "Тюмень"],
    "tenure_months": [24, 2, 10],
    "app": [1, 0, 0],
    "visits_90d": [9, 1, 0],
    "days_since_last": [3, 40, 95],
    "avg_check": [380, 250, None],
    "delivery_share": [0.1, 0.6, 0.0],
    "fav_category": ["кофе", "еда", "не кофе"],
    "promo_used": [2, 0, 0],
    "complaints": [0, 2, 0],
})
new["risk"] = pipe.predict_proba(new)[:, 1].round(2)
new[["city", "visits_90d", "days_since_last", "risk"]]
```

Пропуск среднего чека заполнился нулём, Екатеринбург получил нули во всех флагах городов, и никакого `reindex` не понадобилось. Постоянный гость из Казани — почти без риска. Гость из Тюмени без визитов за 90 дней и новичок из Екатеринбурга с двумя жалобами и большой долей доставки — в зоне высокого риска.

::: tip
Здесь конвейер обучен на всех 2400 гостях: это модель «для работы», которую применяют к новым данным. Оценивать качество по-прежнему нужно на отложенном тесте или кросс-валидацией.
:::

::: figure pipeline
Конвейер из урока: числа и категории готовятся по-разному, затем модель. Всё, что подготовка «выучила», берётся только из обучающих данных.
:::

{{practice: p-pipe, pipe-metrics, new-guests}}

## Разберём вместе: путь одного гостя через конвейер

Возьмём из теста гостя с индексом 494: Казань, с нами 48 месяцев, без приложения, ни одного визита за 90 дней, 113 дней без визита, средний чек пустой (визитов нет), доставки нет, любимая категория — кофе, промокодов и жалоб нет. Проследим, что с ним делает конвейер.

**1. Заполнение пропусков.** `SimpleImputer(strategy="constant", fill_value=0)` ставит в пустой чек 0. Остальные числа не трогает.

**2. Масштаб.** `StandardScaler` вычитает средние **обучающей части** и делит на её разбросы. Три признака руками:

- давность: (113 − 20.44) / 35.36 = **2.62** — гость на два с половиной разброса «дальше» среднего;
- визиты: (0 − 6.36) / 5.09 = **−1.25**;
- чек: (0 − 322.07) / 119.62 = **−2.69** — ноль после заполнения выглядит как очень маленький чек.

**3. Категории.** `OneHotEncoder` превращает «Казань» в 1 в столбце `cat__city_Казань` и нули в остальных городах, «кофе» — в 1 в `cat__fav_category_кофе`.

**4. Модель.** Логистическая регрессия получает 15 чисел и выдаёт вероятность ухода **0.76**.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)

guest = X_test.loc[[494]]
print(pipe["prep"].transform(guest).round(2))     # pipe["prep"] — короче, чем pipe.named_steps["prep"]
print("риск:", round(pipe.predict_proba(guest)[0, 1], 2))
```

Что получилось: все четыре шага выполнились одной строкой `pipe.predict_proba(guest)` — с теми средними, медианами и списками категорий, которые конвейер запомнил при обучении. Ни одного ручного `fillna` или `reindex`.

## Кросс-валидация без утечки

`cross_val_score` принимает конвейер как обычную модель. На каждом фолде он обучает **весь** конвейер заново — и заполнитель, и масштабирование, и кодировщик видят только обучающие строки этого фолда. Проверочный фолд для них — такие же «новые данные», как тест.

Метрику задаёт `scoring`: `"roc_auc"`, `"f1"` и т. д. — что считать на каждом фолде (по умолчанию accuracy), как в уроке «Новые признаки».

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

f1 = cross_val_score(pipe, X_train, y_train, cv=kf, scoring="f1")
auc = cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc")
print(f"F1 {f1.mean():.3f} ± {f1.std():.3f}")
print(f"AUC {auc.mean():.3f} ± {auc.std():.3f}")
```

F1 — около 0.62, AUC — около 0.88. Это честные оценки: ни одна статистика подготовки не подсмотрена в проверочных строках.

А как было бы без конвейера? Обычно масштабируют всю обучающую часть один раз, а потом запускают кросс-валидацию на готовом массиве. Тогда на каждом фолде среднее и разброс уже «знают» проверочные строки — маленькая утечка:

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
kf = KFold(n_splits=5, shuffle=True, random_state=42)

leaky = cross_val_score(LogisticRegression(max_iter=2000), pre.fit_transform(X_train), y_train, cv=kf, scoring="roc_auc")
honest = cross_val_score(Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]),
                         X_train, y_train, cv=kf, scoring="roc_auc")
print(f"подготовка до CV: {leaky.mean():.4f}, внутри конвейера: {honest.mean():.4f}")
```

Здесь разница — в четвёртом знаке: среднее и разброс по 1800 гостям почти не зависят от того, входят ли в них 360 проверочных. Но привычка важнее цифры. Когда подготовка смотрит на ответ — отбор признаков по связи с `churned`, балансировка классов из урока «Дисбаланс классов», кодирование категорий долей ушедших, — утечка до кросс-валидации завышает оценку уже на заметные пункты. Конвейер закрывает весь класс таких ошибок разом.

::: figure cv-pipeline
Слева подготовка обучена один раз на всей обучающей части — проверочный фолд уже повлиял на средние. Справа конвейер на каждом фолде учит подготовку заново только по четырём частям обучения.
:::

::: tip Аналогия
Представьте конкурс бариста, где эталонную крепость эспрессо вычислили, попробовав все чашки — и конкурсные тоже. Конкурсантов судят линейкой, в которую уже подмешаны их собственные чашки. Пока эталон — просто средняя крепость, сдвиг крошечный; а если эталон составляли, уже зная, какие чашки победили, судейство заметно подсуживает. Конвейер в кросс-валидации на каждом фолде составляет эталон заново — только по «тренировочным» чашкам.
:::

::: note
Upsampling (повтор строк редкого класса) из урока «Дисбаланс классов» в стандартный `Pipeline` не встраивается: шаги конвейера меняют столбцы, но не число строк. Для этого есть отдельная библиотека `imbalanced-learn` со своим конвейером, а в sklearn проще использовать `class_weight="balanced"`.
:::

::: quiz
Почему кросс-валидацию запускают на всём конвейере, а не на заранее подготовленной таблице?

- [x] Тогда подготовка (масштаб, категории) учится заново на каждом фолде и не видит проверочную часть
  > Если подготовить таблицу целиком заранее, параметры масштаба уже знают проверочные строки — маленькая, но утечка.
- [ ] Так работает быстрее
  > Медленнее, но честнее.
- [ ] `cross_val_score` не принимает таблицы
  > Принимает. Дело в честности оценки.
- [ ] Чтобы модель была одинаковой на всех фолдах
  > Модель на каждом фолде обучается своя — в этом суть кросс-валидации.
:::

{{practice: cv-models}}

## Практика

## task: median-imp | Медиана из обучения | warmup

`X_train` и `X_test` (сырые, с пропусками в `avg_check`) уже готовы. Создайте `imp = SimpleImputer(strategy="median")`, обучите его на `X_train[["avg_check"]]` и заполните пропуски в `X_test[["avg_check"]]`. Сохраните:

- `med` — медиану, которую запомнил заполнитель (число из `imp.statistics_`);
- `test_filled` — результат `transform` для теста.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
def _ref():
    import pandas as _p
    from sklearn.model_selection import train_test_split as _tts
    _g = _p.read_csv('guests_churn.csv')
    _X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
    return _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
```

### starter
```python
from sklearn.impute import SimpleImputer
```

### check
```python
import numpy as _np
_Xtr, _Xte, _ytr, _yte = _ref()
_m = _Xtr['avg_check'].median()
_g = float(_np.ravel(need('med'))[0])
assert close(_g, _m, 0.01), f'med = {_g}, а медиана avg_check в обучающей части — {_m}. Обучайте заполнитель на X_train, а не на тесте или всей таблице.'
_t = _np.asarray(need('test_filled'), dtype=float).ravel()
assert len(_t) == len(_Xte), f'В test_filled {len(_t)} значений, а в тесте {len(_Xte)} гостей.'
assert not _np.isnan(_t).any(), 'В test_filled остались пропуски — примените imp.transform к X_test[["avg_check"]].'
assert _np.allclose(_t, _Xte['avg_check'].fillna(_m).to_numpy()), 'Пропуски в test_filled заполнены не медианой обучающей части. Тест — только transform, без нового fit.'
```

### hint
`imp.fit(X_train[["avg_check"]])`, потом `imp.transform(X_test[["avg_check"]])`.

### hint
Запомненная медиана — `imp.statistics_[0]` (массив, по числу на столбец).

### solution
```python
from sklearn.impute import SimpleImputer
imp = SimpleImputer(strategy="median")
imp.fit(X_train[["avg_check"]])
med = imp.statistics_[0]
test_filled = imp.transform(X_test[["avg_check"]])
print(med, test_filled[:5].ravel())
```

### explain
Медиана здесь — чек обычного гостя. Для пропусков в `avg_check` она неуместна (у этих гостей не было визитов, честное значение — 0), но сам приём «запомнить на обучении — применить к тесту» одинаков для любых заполнителей.

## task: ohe-new | Флаги для новых городов | warmup

`X_train` уже готов. Обучите `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` на столбце `X_train[["city"]]`. Закодируйте таблицу `new_cities` (готова, в ней Уфа, Екатеринбург и Пермь) и сохраните результат в `codes`, а имена столбцов (`get_feature_names_out()`) списком — в `names`. В `unknown_rows` — сколько строк `codes` целиком из нулей.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
new_cities = pd.DataFrame({"city": ["Уфа", "Екатеринбург", "Пермь"]})
```

### starter
```python
from sklearn.preprocessing import OneHotEncoder
```

### check
```python
import numpy as _np
_w = _np.array([[0, 0, 0, 1], [0, 0, 0, 0], [0, 1, 0, 0]], dtype=float)
_n = [str(v) for v in need('names')]
assert _n == ['city_Казань', 'city_Пермь', 'city_Тюмень', 'city_Уфа'], f'names = {_n}. Кодировщик обучается на X_train[["city"]] — в именах должны быть четыре города обучения.'
_c = _np.asarray(need('codes'), dtype=float)
assert _c.shape == (3, 4), f'Форма codes — {_c.shape}, а ожидалось (3, 4): три новые строки и четыре города обучения. Не обучайте кодировщик на new_cities.'
assert (_c == _w).all(), f'codes = {_c.tolist()}, а ожидалось {_w.tolist()}.'
assert need('unknown_rows') == 1, f'unknown_rows = {need("unknown_rows")}: посчитайте строки, где сумма флагов равна 0.'
```

### hint
`ohe.fit(X_train[["city"]])`, затем `codes = ohe.transform(new_cities)`.

### hint
Строки из нулей: `(codes.sum(axis=1) == 0).sum()`.

### solution
```python
from sklearn.preprocessing import OneHotEncoder
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
ohe.fit(X_train[["city"]])
codes = ohe.transform(new_cities)
names = list(ohe.get_feature_names_out())
unknown_rows = int((codes.sum(axis=1) == 0).sum())
print(names)
print(codes)
print(unknown_rows)
```

## task: p-pipe | Собери конвейер | warmup

`X_train`, `X_test`, `y_train`, `y_test` (сырые) и списки столбцов `num`, `cat` уже готовы. Соберите программу: подготовка по столбцам, конвейер с логистической регрессией, обучение и доля правильных на тесте (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
```

### parsons
```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
pipe.fit(X_train, y_train)
print(round(pipe.score(X_test, y_test), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_w = str(round(_P([('prep', _pre), ('model', _LR(max_iter=2000))]).fit(_Xtr, _ytr).score(_Xte, _yte), 3))
assert _lines == [_w], f'Программа вывела {_lines}, а ожидалась одна строка {_w}.'
```

### hint
Сначала импорты, потом `pre`, потом `pipe` из `pre` и модели. Обучение — до оценки.

## task: prep-shape | Что получается после подготовки | base

Сырые `X_train`, `X_test` и списки `num`, `cat` уже готовы. Соберите `pre` — ColumnTransformer как в теории (числовые: заполнить нулём и масштабировать; категориальные: `OneHotEncoder(handle_unknown="ignore")`). Обучите его на `X_train` и преобразуйте обе части: `Xt_train`, `Xt_test`. Сохраните:

- `n_cols` — сколько столбцов получилось;
- `names` — список имён столбцов (`get_feature_names_out()`);
- `test_mean` — среднее по тесту в столбце `num__days_since_last` (2 знака). У обучающей части среднее этого столбца ровно 0 — а у теста?

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
```

### starter
```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_a = _pre.fit_transform(_Xtr)
_b = _pre.transform(_Xte)
_names = list(_pre.get_feature_names_out())
assert need('n_cols') == _a.shape[1], f'n_cols = {need("n_cols")}, а после подготовки {_a.shape[1]} столбцов: 8 числовых и флаги категорий.'
assert [str(v) for v in need('names')] == _names, f'names не совпадают с get_feature_names_out() эталонной подготовки. Порядок шагов: сначала "num", потом "cat".'
_t = _np.asarray(need('Xt_test'), dtype=float)
assert _t.shape == _b.shape, f'Форма Xt_test — {_t.shape}, а ожидалось {_b.shape}.'
assert _np.allclose(_t, _b), 'Xt_test отличается от ожидаемого. Для теста — только pre.transform(X_test), без нового fit.'
_m = round(float(_b[:, _names.index('num__days_since_last')].mean()), 2)
assert close(need('test_mean'), _m, 0.006), f'test_mean = {need("test_mean")}, а ожидалось {_m}. Возьмите столбец Xt_test с номером names.index("num__days_since_last").'
```

### hint
`Xt_train = pre.fit_transform(X_train)`, `Xt_test = pre.transform(X_test)`; число столбцов — `Xt_train.shape[1]`.

### hint
Номер нужного столбца — `names.index("num__days_since_last")`, среднее — `Xt_test[:, i].mean()`.

### solution
```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
Xt_train = pre.fit_transform(X_train)
Xt_test = pre.transform(X_test)
n_cols = Xt_train.shape[1]
names = list(pre.get_feature_names_out())
i = names.index("num__days_since_last")
test_mean = round(Xt_test[:, i].mean(), 2)
print(n_cols, test_mean)
```

### explain
У теста среднее не ровно 0: масштабирование вычитает среднее **обучающей** части. Так и должно быть — тест играет роль новых данных, и подстраивать под него масштаб нельзя.

## task: pipe-metrics | Конвейер на тесте | base

Сырые `X_train`, `X_test`, `y_train`, `y_test` и готовый (не обученный) ColumnTransformer `pre` уже есть. Соберите `pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])`, обучите на обучающей части и посчитайте на тесте `test_f1` и `test_auc` (3 знака). В `top_feature` сохраните имя признака с наибольшим по модулю коэффициентом модели (имена — из шага `prep`).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
```

### starter
```python
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import f1_score as _f1, roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_p = _P([('prep', _pre), ('model', _LR(max_iter=2000))]).fit(_Xtr, _ytr)
_f = round(_f1(_yte, _p.predict(_Xte)), 3)
_a = round(_auc(_yte, _p.predict_proba(_Xte)[:, 1]), 3)
assert close(need('test_f1'), _f), f'test_f1 = {need("test_f1")}, а ожидалось {_f}. F1 считается по predict на X_test.'
assert close(need('test_auc'), _a), f'test_auc = {need("test_auc")}, а ожидалось {_a}. Для AUC нужны вероятности: predict_proba(X_test)[:, 1].'
_names = _p.named_steps['prep'].get_feature_names_out()
_top = _names[int(_np.argmax(_np.abs(_p.named_steps['model'].coef_[0])))]
assert need('top_feature') == _top, f'top_feature = {need("top_feature")!r}, а ожидался другой признак. Коэффициенты — pipe.named_steps["model"].coef_[0], сравнивайте по модулю.'
```

### hint
Метрики: `f1_score(y_test, pipe.predict(X_test))`, `roc_auc_score(y_test, pipe.predict_proba(X_test)[:, 1])`.

### hint
`coefs = pipe.named_steps["model"].coef_[0]`, `names = pipe.named_steps["prep"].get_feature_names_out()`, номер наибольшего по модулю — `np.argmax(np.abs(coefs))`.

### solution
```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
pipe.fit(X_train, y_train)
test_f1 = round(f1_score(y_test, pipe.predict(X_test)), 3)
test_auc = round(roc_auc_score(y_test, pipe.predict_proba(X_test)[:, 1]), 3)
coefs = pipe.named_steps["model"].coef_[0]
names = pipe.named_steps["prep"].get_feature_names_out()
top_feature = names[np.argmax(np.abs(coefs))]
print(test_f1, test_auc, top_feature)
```

### explain
Самый сильный признак — давность последнего визита: чем дольше гостя не было, тем выше риск. Коэффициенты можно сравнивать между собой, потому что все числовые признаки внутри конвейера отмасштабированы (урок «Масштабирование и ближайшие соседи»).

## task: new-guests | Риск для новых гостей | base

Конвейер `pipe` (подготовка + логистическая регрессия) уже обучен на всех гостях. Пришла выгрузка `new` — 5 новых гостей в «сыром» виде: среди них гость из нового города Екатеринбург и гости с пустым средним чеком.

Сохраните в `risk` вероятности ухода для этих гостей (список, 3 знака), в `flag` — предсказания 0/1 (список), а в `riskiest` — `guest_id` гостя с наибольшим риском. Столбец `guest_id` в конвейер подавать не нужно, но и удалять его не обязательно — проверьте, что получится.

### setup
```python
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))]).fit(X, y)
new = pd.DataFrame({
    "guest_id": ["N-1", "N-2", "N-3", "N-4", "N-5"],
    "city": ["Екатеринбург", "Пермь", "Уфа", "Тюмень", "Казань"],
    "tenure_months": [2, 30, 14, 6, 1],
    "app": [0, 1, 0, 0, 1],
    "visits_90d": [1, 12, 0, 2, 3],
    "days_since_last": [55, 2, 80, 30, 12],
    "avg_check": [310, 420, None, 280, None],
    "delivery_share": [0.7, 0.05, 0.0, 0.5, 0.3],
    "fav_category": ["еда", "кофе", "кофе", "не кофе", "кофе"],
    "promo_used": [0, 4, 0, 1, 1],
    "complaints": [2, 0, 0, 1, 0],
})
def _ref():
    import pandas as _p
    from sklearn.compose import ColumnTransformer as _CT
    from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
    from sklearn.impute import SimpleImputer as _SI
    from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
    from sklearn.linear_model import LogisticRegression as _LR
    _g = _p.read_csv('guests_churn.csv')
    _X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
    _n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
    _pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
    return _P([('prep', _pre), ('model', _LR(max_iter=2000))]).fit(_X, _g['churned'])
```

### starter
```python
# pipe уже обучен, new — сырая таблица новых гостей
```

### check
```python
import pandas as _pd
_p = _ref()
_new = need('new', _pd.DataFrame)
assert len(_new) == 5, 'Таблицу new не нужно менять.'
_pr = _p.predict_proba(_new)[:, 1]
_r = [float(v) for v in need('risk')]
assert len(_r) == 5, f'В risk {len(_r)} чисел, а гостей 5.'
assert all(close(a, round(b, 3)) for a, b in zip(_r, _pr)), f'risk = {_r}, а ожидалось {[round(float(v), 3) for v in _pr]}. Нужна вероятность класса 1: predict_proba(new)[:, 1].'
_f = [int(v) for v in need('flag')]
assert _f == [int(v) for v in _p.predict(_new)], f'flag = {_f}, а ожидалось {[int(v) for v in _p.predict(_new)]}. Используйте pipe.predict(new).'
_top = _new['guest_id'].iloc[int(_pr.argmax())]
assert need('riskiest') == _top, f'riskiest = {need("riskiest")!r}, а самый высокий риск у другого гостя.'
```

### hint
`pipe.predict_proba(new)[:, 1]` — вероятности ухода. Конвейер сам выберет нужные столбцы по именам, лишний `guest_id` ColumnTransformer отбросит.

### hint
Самый рискованный: `new["guest_id"].iloc[proba.argmax()]` — или добавьте столбец риска и отсортируйте.

### solution
```python
proba = pipe.predict_proba(new)[:, 1]
risk = [round(float(p), 3) for p in proba]
flag = [int(v) for v in pipe.predict(new)]
riskiest = new["guest_id"].iloc[proba.argmax()]
print(risk, flag, riskiest)
```

### explain
Конвейер принял таблицу как есть: пропуски чека заполнил нулём, Екатеринбургу поставил нули во всех флагах городов, лишний `guest_id` отбросил — он не входит ни в `num`, ни в `cat`. Самый высокий риск — у новичка из Екатеринбурга: два месяца в сети, давно не был, две жалобы при большой доле доставки. Город модель не знает, но ей хватило остальных признаков.

## task: cv-models | Одна подготовка — три модели | plus

Сырые `X_train`, `y_train`, ColumnTransformer `pre` и фолды `kf = KFold(n_splits=5, shuffle=True, random_state=42)` уже готовы. Сравните кросс-валидацией по `scoring="roc_auc"` три конвейера с одной и той же подготовкой `pre`:

- `"логрегрессия"` — `LogisticRegression(max_iter=2000)`;
- `"соседи"` — `KNeighborsClassifier(n_neighbors=25)`;
- `"лес"` — `RandomForestClassifier(n_estimators=50, random_state=0)`.

Сохраните словарь `cv_auc`: название → средний AUC по фолдам (3 знака) и `best_model` — название лучшего.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
cv_auc = {}
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.neighbors import KNeighborsClassifier as _KN
from sklearn.ensemble import RandomForestClassifier as _RF
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), _n), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_w = {}
for _nm, _m in (('логрегрессия', _LR(max_iter=2000)), ('соседи', _KN(n_neighbors=25)), ('лес', _RF(n_estimators=50, random_state=0))):
    _w[_nm] = round(_cvs(_P([('prep', _pre), ('model', _m)]), _Xtr, _ytr, cv=_k, scoring='roc_auc').mean(), 3)
_c = dict(need('cv_auc'))
assert set(_c) == set(_w), f'Ключи cv_auc: {sorted(_c)}, а нужны {sorted(_w)}.'
for _nm in _w:
    assert close(_c[_nm], _w[_nm], 0.0011), f'{_nm}: средний AUC {_c[_nm]}, а ожидалось {_w[_nm]}. Конвейер с pre, cross_val_score на X_train, y_train, cv=kf, scoring="roc_auc".'
assert need('best_model') == max(_w, key=_w.get), f'best_model = {need("best_model")!r}, а лучший AUC у другой модели.'
```

### hint
Словарь моделей и цикл: `cv_auc[name] = round(cross_val_score(Pipeline([("prep", pre), ("model", m)]), X_train, y_train, cv=kf, scoring="roc_auc").mean(), 3)`.

### hint
Один и тот же `pre` можно класть в разные конвейеры: `cross_val_score` каждый раз обучает его копию.

### solution
```python
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
models = {
    "логрегрессия": LogisticRegression(max_iter=2000),
    "соседи": KNeighborsClassifier(n_neighbors=25),
    "лес": RandomForestClassifier(n_estimators=50, random_state=0),
}
cv_auc = {}
for name, m in models.items():
    pipe = Pipeline([("prep", pre), ("model", m)])
    cv_auc[name] = round(cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc").mean(), 3)
best_model = max(cv_auc, key=cv_auc.get)
print(cv_auc, best_model)
```

### explain
Подготовка написана один раз, а модели меняются одной строкой — в этом удобство конвейера. Соседям масштабирование внутри `pre` обязательно (урок «Масштабирование и ближайшие соседи»); лесу оно не мешает и не помогает.
