---
title: "Свои шаги конвейера: порядок категорий, функции и свой класс"
lead: "Готовых кодировщиков и заполнителей хватает не всегда. Учимся передавать конвейеру порядок категорий, встраивать в него свои признаки функцией и писать собственный шаг-трансформер — класс с fit и transform, который ведёт себя как родной для sklearn."
files: [guests_churn.csv, guest_tiers.csv]
recap:
  - "`OrdinalEncoder(categories=[[\"базовая\", \"серебряная\", \"золотая\"]], handle_unknown=\"use_encoded_value\", unknown_value=-1)` — порядковые категории одним столбцом. Без `categories=` порядок алфавитный, и смысл ломается молча."
  - "`FunctionTransformer(функция)` встраивает в конвейер свои признаки. Функция должна считать каждую строку по ней самой, без статистик по всей таблице."
  - "Свой трансформер — класс `(TransformerMixin, BaseEstimator)`: `__init__` только сохраняет настройки под теми же именами, `fit` учит статистики в атрибуты с `_` и возвращает `self`, `transform` применяет их к копии таблицы."
---

Конвейер из урока «Pipeline: предобработка и модель вместе» уже умеет заполнять пропуски, делать флаги и масштабировать. Здесь — три способа научить его своему.

## Порядковые категории: OrdinalEncoder

**Зачем.** В CRM у каждого гостя есть уровень карты лояльности: «базовая», «серебряная» или «золотая». Это категория, но у неё есть **порядок**: золотая выше серебряной, серебряная выше базовой. `OneHotEncoder` сделает три флага и этот порядок выбросит — модели придётся заново выяснять, что флаги как-то связаны. **OrdinalEncoder** (порядковый кодировщик) превращает уровни в числа 0, 1, 2 в одном столбце — порядок сохраняется, а столбец один.

::: tip Аналогия
Размеры одежды S, M, L. Продавец, раскладывая стопки, кладёт их по росту, а не по алфавиту: по алфавиту вышло бы L, M, S — большой размер первым. OrdinalEncoder по умолчанию раскладывает именно по алфавиту, поэтому порядок нужно задать ему явно.
:::

Уровни лежат в отдельной выгрузке CRM `guest_tiers.csv` (`guest_id`, `card_tier`) — присоединим её к гостям по `guest_id`.

### Игрушечный пример: четыре гостя

У гостей уровни: серебряная, базовая, золотая, базовая. Что хотим получить: базовая → 0, серебряная → 1, золотая → 2, то есть столбец 1, 0, 2, 0.

```python
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder

toy = pd.DataFrame({"card_tier": ["серебряная", "базовая", "золотая", "базовая"]})

alpha = OrdinalEncoder().fit(toy)
print("по умолчанию:", alpha.categories_[0], "→", alpha.transform(toy).ravel())

TIERS = ["базовая", "серебряная", "золотая"]
enc = OrdinalEncoder(categories=[TIERS], handle_unknown="use_encoded_value", unknown_value=-1).fit(toy)
print("с порядком:  ", enc.transform(toy).ravel())
print("новый уровень:", enc.transform(pd.DataFrame({"card_tier": ["платиновая"]})).ravel())
```

Что здесь происходит:

- `OrdinalEncoder()` без настроек сортирует категории **по алфавиту**: «базовая» → 0, «золотая» → 1, «серебряная» → 2. Золотая оказалась ниже серебряной — порядок сломан, хотя ошибки никто не покажет;
- `categories=[TIERS]` — список списков: по одному списку порядка на каждый кодируемый столбец. Здесь столбец один, поэтому внешний список из одного элемента;
- `.ravel()` превращает таблицу из одного столбца в плоский массив — так его удобнее печатать;
- `handle_unknown="use_encoded_value", unknown_value=-1` — что делать с уровнем, которого не было при `fit`: вместо ошибки поставить −1. Без этих параметров новая «платиновая» карта уронила бы прогноз с `ValueError: Found unknown categories`.

::: figure ordinal-tiers
Коды уровней карты при алфавитном и при смысловом порядке. Доли ушедших по уровням — 36.4 % у базовой, 17.4 % у серебряной, 13.0 % у золотой: при смысловом порядке они монотонно падают с кодом, при алфавитном — скачут.
:::

::: predict
```python static
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
sizes = pd.DataFrame({"size": ["M", "L", "S"]})
print(OrdinalEncoder().fit_transform(sizes).ravel())
```

- `[1. 2. 0.]`
- [x] `[1. 0. 2.]`
- `[0. 1. 2.]`

Почему: без `categories=` порядок алфавитный — L → 0, M → 1, S → 2. Поэтому M, L, S превращаются в 1, 0, 2, и «большой» размер получает самый маленький код.
:::

### В ColumnTransformer

Порядковый кодировщик встаёт в `ColumnTransformer` третьей тройкой, рядом с числовыми и номинальными столбцами:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder

g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guest_tiers.csv"), on="guest_id")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]
TIERS = ["базовая", "серебряная", "золотая"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ("tier", OrdinalEncoder(categories=[TIERS], handle_unknown="use_encoded_value", unknown_value=-1),
     ["card_tier"]),
])
Xt = pre.fit_transform(X_train)
print(Xt.shape, pre.get_feature_names_out()[-1])

new = X_test.head(2).copy()
new["card_tier"] = ["золотая", "платиновая"]   # второй уровень CRM ввела вчера
print(pre.transform(new)[:, -1])
```

Что здесь происходит:

- тройка `("tier", OrdinalEncoder(...), ["card_tier"])` — имя шага, кодировщик и список из одного столбца;
- было 15 столбцов после подготовки, стал 16: уровень карты занял **один** столбец `tier__card_tier`, а не три;
- новый уровень «платиновая» не уронил `transform`, а получил код −1.

Добавляет ли уровень карты что-то к полной модели? Если сравнить кросс-валидацией тот же конвейер без тройки `tier` и с ней, AUC — 0.8773 и 0.8778: разница в четвёртом знаке. Причина в данных: CRM присваивает уровень по стажу и тратам, а эти признаки у модели уже есть. Новый признак полезен, только если несёт новую информацию, — это стоит проверять каждый раз.

**Когда что выбирать:**

| Категория | Пример | Кодирование |
|---|---|---|
| с естественным порядком, эффект идёт в ту же сторону | уровень карты, размер S/M/L, оценка 1–5 текстом | `OrdinalEncoder(categories=[...])` |
| без порядка | город, любимая категория | `OneHotEncoder` для линейных моделей |
| без порядка, много значений, модель — деревья | 300 улиц | `OrdinalEncoder` допустим: дерево разрежет коды порогами, а one-hot раздул бы таблицу |

::: warn Типичные ошибки
- **Алфавитный порядок вместо смыслового.** `OrdinalEncoder()` без `categories=` молча ставит «золотая» между «базовая» и «серебряная». Всегда задавайте порядок явно и проверяйте `enc.categories_`.
- **`categories=TIERS` вместо `categories=[TIERS]`.** Нужен список списков — по одному на столбец. С плоским списком будет `ValueError: Shape mismatch: if categories is an array, it has to be of shape (n_features,)`.
- **Порядковое кодирование для городов в линейной модели.** Коды 0, 1, 2, 3 для Казани, Перми, Тюмени и Уфы заставят модель считать, что Уфа «втрое больше» Перми. Для номинальных категорий — one-hot.
:::

{{practice: ord-tier}}

## Свои признаки внутри конвейера: FunctionTransformer

В уроке «Новые признаки» мы придумывали признаки: флаг новичка, произведение жалоб на долю доставки. Чтобы они тоже считались автоматически — и для теста, и для новых гостей, — функцию оборачивают в **FunctionTransformer**. Он ничего не учит (`fit` пустой), а `transform` просто вызывает функцию.

```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def add_features(df):
    df = df.copy()
    df["is_new"] = (df["tenure_months"] <= 3).astype(int)
    df["compl_x_deliv"] = df["complaints"] * df["delivery_share"]
    return df

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints", "is_new", "compl_x_deliv"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([
    ("feat", FunctionTransformer(add_features)),
    ("prep", pre),
    ("model", LogisticRegression(max_iter=2000)),
])
f1 = cross_val_score(pipe, X_train, y_train, cv=kf, scoring="f1")
auc = cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc")
print(f"F1 {f1.mean():.3f}, AUC {auc.mean():.3f}")
```

Шаг `feat` стоит первым: он добавляет два столбца к сырой таблице, а `prep` уже знает их по именам (они дописаны в список `num`). С новыми признаками F1 вырос примерно с 0.62 до 0.67, AUC — с 0.88 до 0.90. Логистическая регрессия сама не умеет перемножать признаки, и взаимодействие «жалобы × доставка», подсказанное вручную, ей заметно помогает.

::: warn Функция — только по строке
Внутри `add_features` каждое значение считается по своей строке: «новичок ли этот гость», «его жалобы × его доля доставки». Если написать там `df["avg_check"] - df["avg_check"].mean()`, среднее будет пересчитываться по **той таблице, которую подали**: по фолду при CV, по трём гостям при прогнозе. Это и утечка, и разные признаки на обучении и в работе. Всё, что требует статистик по данным, делайте шагами sklearn с `fit` (как `StandardScaler`).
:::

::: deep
`df.copy()` в начале функции — не формальность: без него функция дописала бы столбцы прямо в `X_train` снаружи конвейера, и при втором вызове данные уже были бы другими.
:::

::: warn Типичные ошибки
- **`fit` конвейера на всей таблице.** Тогда и масштаб, и список категорий «видели» тест. Учим на train, тест — только `predict`.
- **Столбец не попал в списки.** `remainder="drop"` молча выбрасывает его; сверяйте `get_feature_names_out()`.
- **Подготовка до конвейера.** Если `get_dummies` или масштаб сделаны заранее руками, конвейер не защитит от утечки в кросс-валидации.
- **Параметры в GridSearch без префикса.** Внутри конвейера параметр модели называется `model__C`, а не `C` (урок «Подбор гиперпараметров»).
:::

::: quiz
Коллега хочет добавить в `add_features` признак «чек минус средний чек»: `df["avg_check"] - df["avg_check"].mean()`. Что с ним не так?

- [x] Среднее будет считаться по той таблице, которую подали: по фолду при кросс-валидации, по трём гостям при прогнозе — признак везде разный
  > `FunctionTransformer` ничего не запоминает при `fit`. Статистику по данным должен выучить шаг с `fit` на обучающей части, например `StandardScaler`.
- [ ] Ничего: функция внутри конвейера, значит, утечки быть не может
  > Конвейер защищает только шаги, которые учатся через `fit`. Функция в `FunctionTransformer` вызывается заново на любой поданной таблице.
- [ ] Только то, что признак дублирует средний чек и модели не нужен
  > Дублирование — меньшая беда. Главное — признак на обучении и в работе считается по разным «средним».
- [ ] `FunctionTransformer` не умеет возвращать новые столбцы
  > Умеет: в уроке `add_features` добавляет два столбца. Проблема в статистике по всей таблице, а не в столбцах.
:::

{{practice: feat-step, own-feature}}

## Свой трансформер: класс с fit и transform

**Зачем.** Хочется признак «чек гостя относительно среднего чека в его городе»: в Казани чеки выше, и 400 ₽ там — обычный гость, а в Перми — щедрый. В `FunctionTransformer` такой признак писать нельзя: среднее по городу — статистика по данным, и функция пересчитывала бы её на каждой поданной таблице (это разобрано выше). Нужен шаг, который **запоминает** средние по городам при `fit` на обучающей части и **применяет** их при `transform` к любым новым строкам — как `StandardScaler` запоминает среднее и разброс. Такой шаг можно написать самому.

::: tip Аналогия
Новый бариста в первую неделю записывает в блокнот, какой напиток обычно берёт каждый постоянный гость (`fit`), а потом по блокноту встречает их у стойки (`transform`). Блокнот заполняется один раз, на «обучении»; гость, которого в блокноте нет, получает стандартное «что вам предложить?» — значение по умолчанию.
:::

### Устройство: три метода и два родителя

Трансформер sklearn — это класс с тремя методами:

| Метод | Что делает | Что возвращает |
|---|---|---|
| `__init__(self, ...)` | только запоминает настройки как есть | ничего |
| `fit(self, X, y=None)` | учит статистики **по X** и сохраняет их в атрибуты с `_` на конце | `self` |
| `transform(self, X)` | применяет выученное к X, не меняя исходную таблицу | новую таблицу |

Два «родителя» дают остальное бесплатно: `BaseEstimator` — методы `get_params` и `set_params` (без них класс не сможет работать в `GridSearchCV` и `clone`), `TransformerMixin` — метод `fit_transform`. Миксин пишут первым, `BaseEstimator` — последним: так sklearn правильно узнаёт, что это трансформер (в новых версиях от порядка зависят служебные «теги» модели).

### Игрушечный пример: пять гостей

Пять гостей: в Казани чеки 420 и 300, в Перми — 330, 270 и 300. Что должен выучить `fit`:

1. Среднее по Казани: (420 + 300) / 2 = **360**.
2. Среднее по Перми: (330 + 270 + 300) / 3 = **300**.
3. Общее среднее — на случай нового города: (420 + 300 + 330 + 270 + 300) / 5 = 1 620 / 5 = **324**.

Новые гости: казанский с чеком 450 → 450 / 360 = **1.25** (на четверть выше своего города); гость из Уфы с чеком 243 — Уфы в «блокноте» нет, берём общее среднее: 243 / 324 = **0.75**.

::: figure custom-fit
Свой трансформер на пяти гостях: `fit` запоминает средние чеки по городам и общее среднее, `transform` делит чек нового гостя на среднее его города или, если город новый, на общее.
:::

```python
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class CheckVsCity(TransformerMixin, BaseEstimator):
    """Добавляет столбец «чек / средний чек города», средние учит на fit."""

    def __init__(self, col="avg_check", by="city"):
        self.col = col                     # настройки — как есть, без вычислений
        self.by = by

    def fit(self, X, y=None):
        self.means_ = X.groupby(self.by)[self.col].mean()   # выучили средние по городам
        self.overall_ = X[self.col].mean()                   # и общее — для новых городов
        return self

    def transform(self, X):
        X = X.copy()                                         # не портим исходную таблицу
        base = X[self.by].map(self.means_).fillna(self.overall_)
        X[self.col + "_vs_" + self.by] = X[self.col] / base
        return X

toy = pd.DataFrame({"city": ["Казань", "Казань", "Пермь", "Пермь", "Пермь"],
                    "avg_check": [420, 300, 330, 270, 300]})
t = CheckVsCity().fit(toy)
print(t.means_.to_dict(), t.overall_)
print(t.transform(pd.DataFrame({"city": ["Казань", "Уфа"], "avg_check": [450, 243]})))
print(t.get_params())
```

Что здесь происходит:

- `class CheckVsCity(TransformerMixin, BaseEstimator)` — новый класс с двумя родителями; всё, что они умеют, у него уже есть;
- `__init__` только сохраняет аргументы под **теми же именами** (`self.col = col`): по этим именам `BaseEstimator.get_params()` находит настройки — последняя строка вывода;
- `fit` считает средние через знакомый `groupby` и кладёт их в `self.means_` и `self.overall_`. Подчёркивание на конце — договорённость sklearn: «выучено на данных»;
- `return self` в `fit` позволяет писать `CheckVsCity().fit(toy)` в одну строку и нужен конвейеру;
- `transform`: `map(self.means_)` ставит каждой строке среднее её города из выученной таблицы, `fillna(self.overall_)` — общее среднее для города, которого не было при обучении;
- `X.copy()` — по той же причине, что в `add_features`: не дописывать столбцы в чужую таблицу.

Как читать результат: средние 360 и 300, общее 324 — как в расчёте руками; у новых гостей признак 1.25 и 0.75.

::: predict
```python static
from sklearn.base import BaseEstimator, TransformerMixin

class MaxOf(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None):
        self.max_ = max(X)
        return self
    def transform(self, X):
        return [x / self.max_ for x in X]

t = MaxOf().fit([2, 4, 8])
print(t.transform([4]))
print(t.fit([2]) is t, t.max_)
```

- `[1.0] | True 8`
- [x] `[0.5] | True 2`
- `[0.5] | False 8`

Почему: `fit` на [2, 4, 8] запомнил максимум 8, и `transform([4])` делит на него: 0.5 — выученное применяется к новым данным, а не пересчитывается по ним. `fit` возвращает сам объект, поэтому `t.fit([2]) is t` — `True`; повторный `fit` переучивает трансформер с нуля, и максимум становится 2.
:::

### В конвейере

Свой трансформер встаёт в `Pipeline` так же, как встроенные. При кросс-валидации конвейер на каждом фолде заново вызывает `fit` — средние по городам каждый раз считаются только по обучающей части фолда:

```python
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

class CheckVsCity(TransformerMixin, BaseEstimator):
    def __init__(self, col="avg_check", by="city"):
        self.col = col
        self.by = by
    def fit(self, X, y=None):
        self.means_ = X.groupby(self.by)[self.col].mean()
        self.overall_ = X[self.col].mean()
        return self
    def transform(self, X):
        X = X.copy()
        X[self.col + "_vs_" + self.by] = X[self.col] / X[self.by].map(self.means_).fillna(self.overall_)
        return X

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints", "avg_check_vs_city"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("ratio", CheckVsCity()), ("prep", pre), ("model", LogisticRegression(max_iter=2000))])
auc = cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc")
print(f"AUC {auc.mean():.4f}")
pipe.fit(X_train, y_train)
print(pipe.named_steps["ratio"].means_.round(1).to_dict())
```

Что здесь происходит:

- шаг `ratio` стоит первым и дописывает столбец `avg_check_vs_city`; `prep` уже знает его по имени — он добавлен в список `num`;
- пропуски в `avg_check` дают пропуск и в новом признаке — их заполняет `SimpleImputer` следующего шага;
- `pipe.named_steps["ratio"]` — доступ к шагу по имени; после `fit` у него есть выученные `means_`.

Как читать результат: средние чеки, выученные на обучающей части, — 370.3 ₽ в Казани и около 326–329 ₽ в остальных городах. AUC почти не изменился: 0.8775 против 0.8773 без признака — чек относительно своего города об уходе не говорит ничего нового. Зато признак теперь считается честно: и в кросс-валидации, и для завтрашних гостей средние берутся только из обучения.

::: quiz
Коллега написал свой трансформер с параметром `min_count`, и `GridSearchCV` (перебор настроек — урок «Подбор гиперпараметров») падает с `AttributeError: ... object has no attribute 'min_count'`. В `__init__` у него `self.threshold = min_count * 2`. В чём дело?

- [x] `__init__` должен только сохранять аргументы под теми же именами; `get_params` ищет атрибут `min_count` и не находит его
  > `BaseEstimator` строит `get_params` по именам аргументов `__init__`. Вычисления переносят в `fit`: там можно завести `self.threshold_ = self.min_count * 2`.
- [ ] Нужно унаследовать класс ещё и от `Pipeline`
  > `Pipeline` — контейнер шагов, а не родитель для трансформера. Родителей два: `TransformerMixin` и `BaseEstimator`.
- [ ] `GridSearchCV` вообще не работает со своими классами
  > Работает — если класс соблюдает договорённости sklearn: настройки в `__init__` как есть, обучение в `fit`, `fit` возвращает `self`.
- [ ] Не хватает метода `fit_transform`
  > Его даёт `TransformerMixin` — писать самому не нужно. Проблема в `__init__`.
:::

::: warn Типичные ошибки
- **`fit` не возвращает `self`.** Конвейер вызывает `fit(...).transform(...)` и падает с `AttributeError: 'NoneType' object has no attribute 'transform'`. Последняя строка `fit` — `return self`.
- **Статистики в `transform`.** Если среднее по городу посчитано внутри `transform`, вернулась проблема `FunctionTransformer`: статистика по каждой поданной таблице. Всё, что зависит от данных, — в `fit`, в атрибуты с `_`.
- **Вычисления в `__init__`.** `__init__` только сохраняет аргументы под их именами — иначе ломаются `get_params` и копирование шага: `cross_val_score` и `GridSearchCV` (урок «Подбор гиперпараметров») создают свежие копии трансформера по `get_params`, поэтому настройки должны лежать в атрибутах с теми же именами, что аргументы.
- **Новая категория при прогнозе.** `map` по выученной таблице даёт `NaN` для города, которого не было при `fit`. Решите заранее, что ставить (`fillna(self.overall_)`), — иначе пропуск уйдёт дальше по конвейеру.
- **Изменение входной таблицы.** Без `X = X.copy()` трансформер дописывает столбцы в `X_train` снаружи конвейера.
:::

{{practice: p-transformer, group-ratio}}

## Практика

## task: ord-tier | Уровень карты по порядку | base

Сырые `X_train`, `y_train` (уже с уровнем карты `card_tier`) и список `TIERS = ["базовая", "серебряная", "золотая"]` готовы. Обучите на `X_train[["card_tier"]]` порядковый кодировщик `enc` с этим порядком, который ставит −1 вместо неизвестного уровня. Сохраните:

- `codes` — коды уровня для `X_train` плоским массивом;
- `rate_by_code` — список долей ушедших (`y_train`) для кодов 0, 1, 2 по порядку (3 знака);
- `new_code` — код, который `enc` даёт уровню «платиновая» (число).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv").merge(pd.read_csv("guest_tiers.csv"), on="guest_id")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
TIERS = ["базовая", "серебряная", "золотая"]
```

### starter
```python
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder

```

### check
```python
import numpy as _np
from sklearn.preprocessing import OrdinalEncoder as _OE
e = need('enc')
_cats = list(e.categories_[0])
if _cats == sorted(TIERS):
    raise AssertionError(f'Порядок категорий {_cats} — алфавитный: золотая оказалась ниже серебряной. Задайте categories=[TIERS].')
assert _cats == TIERS, f'enc.categories_ = {_cats}, а нужен порядок {TIERS}.'
_c = _OE(categories=[TIERS]).fit_transform(X_train[['card_tier']]).ravel()
cd = _np.asarray(need('codes'))
assert cd.ndim == 1 and len(cd) == len(X_train), f'codes — плоский массив длиной {len(X_train)}: transform(...).ravel().'
assert (cd == _c).all(), 'codes не совпадают с кодами уровня для X_train.'
_r = y_train.groupby(_c).mean().round(3).tolist()
r = [float(v) for v in need('rate_by_code')]
assert len(r) == 3 and all(close(a, b, 0.0011) for a, b in zip(r, _r)), f'rate_by_code = {r}, а ожидалось {_r}: доля y_train == 1 для кодов 0, 1, 2.'
nc = need('new_code')
assert close(float(nc), -1), f'new_code = {nc}. Для неизвестного уровня нужны handle_unknown="use_encoded_value" и unknown_value=-1.'
```

### hint
`OrdinalEncoder(categories=[TIERS], handle_unknown="use_encoded_value", unknown_value=-1)` и `.fit(X_train[["card_tier"]])` — двойные скобки, кодировщику нужна таблица.

### hint
`codes = enc.transform(X_train[["card_tier"]]).ravel()`; доли по кодам — `y_train.groupby(codes).mean()`.

### hint
Новый уровень подайте таблицей: `enc.transform(pd.DataFrame({"card_tier": ["платиновая"]}))[0, 0]`.

### solution
```python
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
enc = OrdinalEncoder(categories=[TIERS], handle_unknown="use_encoded_value", unknown_value=-1)
enc.fit(X_train[["card_tier"]])
codes = enc.transform(X_train[["card_tier"]]).ravel()
rate_by_code = y_train.groupby(codes).mean().round(3).tolist()
new_code = enc.transform(pd.DataFrame({"card_tier": ["платиновая"]}))[0, 0]
print(rate_by_code, new_code)
```

### explain
Доли ушедших по кодам 0, 1, 2 — 0.364, 0.174 и 0.13: чем выше код, тем реже уходят, и одного числового столбца хватает, чтобы модель это увидела. С алфавитным порядком тот же список выглядел бы как 0.364, 0.13, 0.174 — «золотая» посередине, и линейной модели пришлось бы описывать зависимость, которая то падает, то растёт. Код −1 для «платиновой» — компромисс: прогноз не упадёт, но модель воспримет новую карту как «ниже базовой». Когда в CRM появляется новый уровень, конвейер переобучают с обновлённым списком `TIERS`.

## task: p-transformer | Собери свой трансформер | warmup

Сырые `X_train` и `X_test` уже готовы. Соберите трансформер `Clipper`: при `fit` он запоминает для каждого столбца квантиль уровня `q` (по обучающей части), а при `transform` обрезает значения сверху по этим порогам. Затем обучите его с `q=0.95` на столбцах `visits_90d` и `promo_used` обучающей части.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
```

### parsons
```python
from sklearn.base import BaseEstimator, TransformerMixin
class Clipper(TransformerMixin, BaseEstimator):
    def __init__(self, q=0.99):
        self.q = q
    def fit(self, X, y=None):
        self.upper_ = X.quantile(self.q)
        return self
    def transform(self, X):
        return X.clip(upper=self.upper_, axis=1)
clip = Clipper(q=0.95).fit(X_train[["visits_90d", "promo_used"]])
print(clip.upper_.to_dict())
```

### check
```python
c = need('clip')
assert hasattr(c, 'upper_'), 'У clip нет выученного upper_: строка с .fit(...) должна выполниться, а fit — сохранить self.upper_.'
assert c.get_params() == {'q': 0.95}, f'get_params() = {c.get_params()}. В __init__ — только self.q = q, а трансформер создан с q=0.95.'
_cols = ['visits_90d', 'promo_used']
_u = need('X_train')[_cols].quantile(0.95)
assert (c.upper_ == _u).all(), 'upper_ — квантили 0.95 обучающей части по двум столбцам.'
_t = c.transform(need('X_test')[_cols])
assert (_t.max() <= _u).all(), 'transform должен обрезать значения сверху по выученным порогам: X.clip(upper=self.upper_, axis=1).'
```

### hint
Порядок внутри класса: `__init__` → `fit` → `transform`; `return self` — последняя строка `fit`.

### hint
Отступы: методы — внутри класса (4 пробела), их тела — ещё на 4 пробела глубже. Создание `clip` и `print` — снаружи класса, без отступа.

## task: feat-step | Признаки в конвейере | plus

Сырые `X_train`, `y_train` и `kf` уже готовы. Напишите функцию `add_features(df)`, которая возвращает **копию** таблицы с двумя новыми столбцами:

- `is_new` — 1, если `tenure_months <= 3`, иначе 0;
- `compl_x_deliv` — `complaints * delivery_share`.

Соберите конвейер `pipe`: шаг `"feat"` — `FunctionTransformer(add_features)`, шаг `"prep"` — ColumnTransformer как в теории, но с новыми столбцами в числовом списке, шаг `"model"` — `LogisticRegression(max_iter=2000)`. Посчитайте кросс-валидацией на `X_train` средний F1 (`scoring="f1"`, `cv=kf`): `f1_feat` — для нового конвейера и `f1_base` — для конвейера без шага `feat` и без новых столбцов. Оба — 3 знака.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]

def add_features(df):
    return df
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS, FunctionTransformer as _FT
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints']
_fn = need('add_features')
_s = _Xtr.head(50).copy()
_o = _fn(_s)
assert 'is_new' in _o.columns and 'compl_x_deliv' in _o.columns, 'add_features должна вернуть таблицу со столбцами is_new и compl_x_deliv.'
assert 'is_new' not in _s.columns, 'add_features изменила исходную таблицу — начните функцию с df = df.copy().'
assert (_o['is_new'] == (_s['tenure_months'] <= 3).astype(int)).all(), 'is_new посчитан неверно: 1 при tenure_months <= 3, иначе 0.'
assert ((_o['compl_x_deliv'] - _s['complaints'] * _s['delivery_share']).abs() < 1e-9).all(), 'compl_x_deliv — произведение complaints и delivery_share.'
def _mk(cols, feat):
    _pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), cols), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
    _st = [('prep', _pre), ('model', _LR(max_iter=2000))]
    return _P(([('feat', _FT(_fn))] if feat else []) + _st)
_b = round(_cvs(_mk(_n, False), _Xtr, _ytr, cv=_k, scoring='f1').mean(), 3)
_f = round(_cvs(_mk(_n + ['is_new', 'compl_x_deliv'], True), _Xtr, _ytr, cv=_k, scoring='f1').mean(), 3)
assert close(need('f1_base'), _b, 0.0011), f'f1_base = {need("f1_base")}, а ожидалось {_b}: конвейер без feat, scoring="f1", cv=kf, на X_train.'
assert close(need('f1_feat'), _f, 0.0011), f'f1_feat = {need("f1_feat")}, а ожидалось {_f}. Добавьте is_new и compl_x_deliv в список числовых столбцов — иначе ColumnTransformer их выбросит.'
_p = need('pipe')
assert list(_p.named_steps) == ['feat', 'prep', 'model'], f'Шаги pipe: {list(_p.named_steps)}, а нужны feat, prep, model.'
```

### hint
Функция: `df = df.copy()`, затем два новых столбца, `return df`. Флаг — `(df["tenure_months"] <= 3).astype(int)`.

### hint
Для нового конвейера числовой список — `num + ["is_new", "compl_x_deliv"]`. Если новые столбцы туда не добавить, ColumnTransformer их молча отбросит, и F1 не изменится.

### solution
```python
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints"]
cat = ["city", "fav_category"]

def add_features(df):
    df = df.copy()
    df["is_new"] = (df["tenure_months"] <= 3).astype(int)
    df["compl_x_deliv"] = df["complaints"] * df["delivery_share"]
    return df

def make_prep(num_cols):
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ])

base = Pipeline([("prep", make_prep(num)), ("model", LogisticRegression(max_iter=2000))])
pipe = Pipeline([
    ("feat", FunctionTransformer(add_features)),
    ("prep", make_prep(num + ["is_new", "compl_x_deliv"])),
    ("model", LogisticRegression(max_iter=2000)),
])
f1_base = round(cross_val_score(base, X_train, y_train, cv=kf, scoring="f1").mean(), 3)
f1_feat = round(cross_val_score(pipe, X_train, y_train, cv=kf, scoring="f1").mean(), 3)
print(f1_base, f1_feat)
```

### explain
Два признака из урока «Новые признаки» добавляют к F1 около 5 п.п., причём F1 вырос на каждом из пяти фолдов (фолды одни и те же — `kf`), так что это не случайность нарезки. И теперь они считаются сами для любых новых гостей: отдельный шаг «не забыть посчитать признаки» исчез.

## task: group-ratio | Визиты относительно своей категории | plus

Сырые `X_train` и `X_test` уже готовы. Напишите трансформер `DiffFromGroup(col, by)` с родителями `TransformerMixin` и `BaseEstimator` (в этом порядке):

- `fit` запоминает средние `col` по значениям `by` (`means_`) и общее среднее `col` (`overall_`) — только по поданной таблице;
- `transform` возвращает **копию** таблицы с новым столбцом `f"{col}_minus_{by}"` = значение `col` минус выученное среднее его группы; для группы, которой не было при `fit`, — минус общее среднее.

Обучите `t = DiffFromGroup(col="visits_90d", by="fav_category")` на `X_train` и сохраните `out = t.transform(X_test)`.

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
```

### starter
```python
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class DiffFromGroup(TransformerMixin, BaseEstimator):
    def __init__(self, col="visits_90d", by="fav_category"):
        ...

    def fit(self, X, y=None):
        ...

    def transform(self, X):
        ...

```

### check
```python
import pandas as _pd
t = need('t')
assert t.get_params() == {'by': 'fav_category', 'col': 'visits_90d'}, f'get_params() = {t.get_params()}. В __init__ сохраните аргументы под теми же именами: self.col = col, self.by = by.'
assert hasattr(t, 'means_') and hasattr(t, 'overall_'), 'После fit у трансформера должны быть means_ и overall_.'
_m = X_train.groupby('fav_category')['visits_90d'].mean()
assert all(close(t.means_[k], _m[k], 1e-9) for k in _m.index), 'means_ — средние visits_90d по fav_category на той таблице, что подали в fit (X_train).'
assert close(t.overall_, X_train['visits_90d'].mean(), 1e-9), 'overall_ — среднее visits_90d по всей таблице из fit.'
o = need('out', _pd.DataFrame)
col = 'visits_90d_minus_fav_category'
assert col in o.columns, f'В out нет столбца {col!r}. Имя — f"{{col}}_minus_{{by}}".'
assert col not in X_test.columns, 'transform изменил X_test: начните transform с X = X.copy().'
_exp = X_test['visits_90d'] - X_test['fav_category'].map(_m)
if all(close(a, b, 1e-9) for a, b in zip(o[col], X_test['visits_90d'] - X_test.groupby('fav_category')['visits_90d'].transform('mean'))):
    raise AssertionError('Средние посчитаны по X_test, а не взяты из fit. В transform используйте self.means_.')
assert all(close(a, b, 1e-9) for a, b in zip(o[col], _exp)), 'Новый столбец — visits_90d минус среднее его fav_category из обучения.'
_new = t.transform(_pd.DataFrame({'visits_90d': [10], 'fav_category': ['десерты']}))
assert close(_new[col].iloc[0], 10 - X_train['visits_90d'].mean(), 1e-9), 'Для категории, которой не было при fit, вычитайте общее среднее: fillna(self.overall_).'
```

### hint
Образец — `CheckVsCity` из теории: те же три метода, только вместо деления — вычитание, и имя столбца из `col` и `by`.

### hint
В `fit`: `self.means_ = X.groupby(self.by)[self.col].mean()`, `self.overall_ = X[self.col].mean()`, `return self`.

### hint
В `transform`: `X = X.copy()`, `base = X[self.by].map(self.means_).fillna(self.overall_)`, `X[f"{self.col}_minus_{self.by}"] = X[self.col] - base`, `return X`.

### solution
```python
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class DiffFromGroup(TransformerMixin, BaseEstimator):
    def __init__(self, col="visits_90d", by="fav_category"):
        self.col = col
        self.by = by

    def fit(self, X, y=None):
        self.means_ = X.groupby(self.by)[self.col].mean()
        self.overall_ = X[self.col].mean()
        return self

    def transform(self, X):
        X = X.copy()
        base = X[self.by].map(self.means_).fillna(self.overall_)
        X[f"{self.col}_minus_{self.by}"] = X[self.col] - base
        return X

t = DiffFromGroup(col="visits_90d", by="fav_category").fit(X_train)
out = t.transform(X_test)
print(t.means_.round(2).to_dict())
out[["fav_category", "visits_90d", "visits_90d_minus_fav_category"]].head()
```

### explain
Трансформер запомнил средние визиты по любимой категории на обучающей части и применяет их к тесту без пересчёта — так же поступит и с завтрашними гостями. Проверка ловит две частые ошибки. Первая — среднее, посчитанное внутри `transform` по поданной таблице (`groupby(...).transform("mean")`): на тесте числа выйдут похожими, но это уже другой признак, а для одного нового гостя «среднее группы» — его собственное значение, и разность всегда 0. Вторая — забытый `X.copy()`: тогда `transform(X_test)` тихо дописывает столбец в сам `X_test`, и следующая ячейка работает уже с изменённой таблицей.

## task: own-feature | Свой признак | star

Сырые `X_train`, `y_train`, `kf` и функция `add_features` из прошлой задачи (флаг новичка и жалобы × доставка) уже готовы. Конвейер с ней даёт средний CV-AUC около 0.905.

Напишите функцию `add_more(df)`: она вызывает `add_features(df)` и добавляет **один** новый числовой столбец с именем `extra`. Добейтесь, чтобы CV-AUC конвейера (`scoring="roc_auc"`, `cv=kf`, числовые столбцы — 8 исходных + `is_new`, `compl_x_deliv`, `extra`) вырос хотя бы на 0.004 по сравнению с конвейером без `extra` (это примерно столько, сколько дал логарифм давности в уроке «Форма связи и важность признаков», где он выигрывал на всех фолдах). Ожидаемый путь — `log_days` из того урока; флаг «давно не был» тоже подойдёт, если удачно выбрать порог. В `auc_more` сохраните получившийся средний AUC (3 знака).

Признак должен считаться по строке (никаких `.mean()` по столбцу) и не использовать `churned`.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = g.drop(columns=["guest_id", "churned", "card_blocked"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
def add_features(df):
    df = df.copy()
    df["is_new"] = (df["tenure_months"] <= 3).astype(int)
    df["compl_x_deliv"] = df["complaints"] * df["delivery_share"]
    return df
```

### starter
```python
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression

def add_more(df):
    df = add_features(df)
    df["extra"] = 0
    return df
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.compose import ColumnTransformer as _CT
from sklearn.pipeline import Pipeline as _P, make_pipeline as _mp
from sklearn.impute import SimpleImputer as _SI
from sklearn.preprocessing import OneHotEncoder as _OHE, StandardScaler as _SS, FunctionTransformer as _FT
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_X = _g.drop(columns=['guest_id', 'churned', 'card_blocked'])
_Xtr, _Xte, _ytr, _yte = _tts(_X, _g['churned'], test_size=0.25, random_state=42, stratify=_g['churned'])
_k = _KF(n_splits=5, shuffle=True, random_state=42)
def _af(df):
    df = df.copy()
    df['is_new'] = (df['tenure_months'] <= 3).astype(int)
    df['compl_x_deliv'] = df['complaints'] * df['delivery_share']
    return df
_fn = need('add_more')
_o = _fn(_Xtr.head(40))
assert 'extra' in _o.columns, 'add_more должна добавить столбец extra.'
assert 'churned' not in _o.columns, 'В признаках не должно быть churned.'
_one = _fn(_Xtr.head(40).iloc[[7]])
assert close(float(_one['extra'].iloc[0]), float(_o['extra'].iloc[7]), 1e-9), 'extra для гостя зависит от того, какие ещё строки в таблице. Признак должен считаться только по своей строке — без статистик по столбцу.'
_n = ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints', 'is_new', 'compl_x_deliv']
def _mk(fn, cols):
    _pre = _CT([('num', _mp(_SI(strategy='constant', fill_value=0), _SS()), cols), ('cat', _OHE(handle_unknown='ignore'), ['city', 'fav_category'])])
    return _P([('feat', _FT(fn)), ('prep', _pre), ('model', _LR(max_iter=2000))])
_base = _cvs(_mk(_af, _n), _Xtr, _ytr, cv=_k, scoring='roc_auc').mean()
_more = _cvs(_mk(_fn, _n + ['extra']), _Xtr, _ytr, cv=_k, scoring='roc_auc').mean()
assert _more - _base >= 0.004, f'С extra средний AUC {_more:.4f}, без него {_base:.4f}: прирост {_more - _base:+.4f}, а нужно хотя бы +0.004. Поищите признак, связь которого с уходом не прямая линия.'
assert close(need('auc_more'), round(_more, 3), 0.0011), f'auc_more = {need("auc_more")}, а конвейер с вашим extra даёт {_more:.3f}.'
```

### hint
Логистическая регрессия ищет связь вида «чем больше признак, тем выше риск — равномерно». Посмотрите, как доля ушедших меняется с `days_since_last` (группировка по интервалам из урока «Форма связи и важность признаков»): равномерно ли она растёт?

### hint
Риск быстро растёт в первые недели без визита и потом почти не меняется. Такую «сжатую» шкалу даёт логарифм — признак `log_days` из урока «Форма связи и важность признаков»: `np.log1p(df["days_since_last"])`. Подойдёт и флаг «давно не был», если удачно выбрать порог.

### solution
```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression

def add_more(df):
    df = add_features(df)
    df["extra"] = np.log1p(df["days_since_last"])
    return df

num = ["tenure_months", "app", "visits_90d", "days_since_last", "avg_check",
       "delivery_share", "promo_used", "complaints", "is_new", "compl_x_deliv", "extra"]
cat = ["city", "fav_category"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="constant", fill_value=0), StandardScaler()), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
pipe = Pipeline([("feat", FunctionTransformer(add_more)), ("prep", pre), ("model", LogisticRegression(max_iter=2000))])
auc_more = round(cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc").mean(), 3)
print(auc_more)
```

### explain
Логарифм давности визита поднимает AUC примерно до 0.91: для линейной модели разница между 2 и 20 днями без визита теперь значит больше, чем между 80 и 98. Деревьям и лесу такие преобразования почти не нужны — они сами ставят пороги, а линейной модели форму связи приходится подсказывать.
