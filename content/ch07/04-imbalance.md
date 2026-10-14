---
title: Дисбаланс классов
lead: "Уходящих гостей в данных «Зерна» лишь около 22 %, и модель по умолчанию тянется к большинству: недооценивает отток и пропускает уходящих. Учимся выравнивать классы весами, размножением и прореживанием строк, не устраивать при этом утечку и понимать, что балансировка на самом деле меняет, а что нет."
files: [guests_churn.csv]
recap:
  - "Дисбаланс классов — один класс встречается намного реже другого. Модель снижает общее число ошибок, поэтому смещается к частому классу: полнота по редкому классу проседает."
  - "`class_weight=\"balanced\"` — ошибка на редком классе весит больше: вес класса = n / (2 × n_класса). Работает у `LogisticRegression`, деревьев и леса."
  - "Upsampling — повторить строки редкого класса (`sample(n=..., replace=True)`) до размера частого; downsampling — случайно оставить из частого класса столько строк, сколько в редком."
  - "Балансируют **только обучающую часть**, после разбиения. Размножение до разбиения кладёт копии одних и тех же гостей и в train, и в test — метрики завышены."
  - "Балансировка двигает precision, recall и F1 (полнота растёт, точность падает), а ROC-AUC почти не меняет: порядок гостей по риску остаётся прежним."
  - "Тот же эффект даёт сдвиг порога у обычной модели. Вероятности после балансировки завышены — для расчёта денег им верить как числам нельзя."
---

## Модель тянется к большинству

Уходящих гостей в наших данных около 22 % — это **дисбаланс классов** из урока «Матрица ошибок». Здесь он умеренный, бывает и сильнее: мошеннических платежей доли процента, бракованных деталей — единицы на тысячу.

Чем дисбаланс мешает? При обучении модель старается сделать как можно меньше ошибок **в сумме**, и ошибка на оставшемся госте стоит для неё столько же, сколько ошибка на ушедшем. Оставшихся в обучающей части примерно в 3.5 раза больше, поэтому модели выгоднее быть осторожной с ответом «уйдёт». Посмотрим на логистическую регрессию:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

print(y_train.value_counts())
model = LogisticRegression(max_iter=2000).fit(X_train, y_train)
pred = model.predict(X_test)
print(f"ушли на самом деле: {y_test.mean():.1%}, модель говорит «уйдёт»: {pred.mean():.1%}")
print(f"recall: {recall_score(y_test, pred):.2f}")
```

**Что здесь происходит:**

- `y_train.value_counts()` — сколько в обучении оставшихся и ушедших: это и есть дисбаланс, который «видит» модель.
- `pred.mean()` — доля ответов «уйдёт» (среднее нулей и единиц); сравниваем её с реальной долей ушедших `y_test.mean()`.
- `:.1%` — формат f-строки: умножает на 100 и добавляет знак процента.

Модель называет уходящими лишь 16.5 % гостей, хотя на самом деле уходят 22 %, и пропускает 40 % уходящих. Это не «плохая модель», а следствие того, что все ошибки для неё одинаковы. Но отделу лояльности пропущенный уходящий гость обходится дороже лишнего бонуса (урок «Матрица ошибок»).

В прошлом уроке мы чинили это порогом. Сегодня — три способа изменить само обучение, чтобы редкий класс весил больше.

{{practice: share-pred}}

## Веса классов: class_weight="balanced"

Самый простой способ — сказать модели, что ошибка на уходящем госте дороже. У `LogisticRegression`, дерева и леса для этого есть параметр **`class_weight`** (вес класса). Значение `"balanced"` (сбалансированный) считает веса так, чтобы оба класса в сумме весили одинаково:

вес класса = n / (2 × n_класса),

где n — число строк в обучающей части, n_класса — сколько из них в этом классе, 2 — число классов.

::: predict
```python static
y = [0] * 8 + [1] * 2
n = len(y)
print(n / (2 * y.count(0)), n / (2 * y.count(1)))
```

- `0.5 0.5`
- `0.8 0.2`
- [x] `0.625 2.5`

Почему: 10 / (2 × 8) = 0.625 и 10 / (2 × 2) = 2.5. Восемь строк по 0.625 весят 5, две строки по 2.5 — тоже 5: классы уравнены.
:::

У наших гостей вес уходящих около 2.24, оставшихся — около 0.64: ошибка на уходящем «штрафует» модель примерно в 3.5 раза сильнее. Сравним обычную и взвешенную модели:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

print("веса:", (len(y_train) / (2 * y_train.value_counts())).round(2).to_dict())
for cw in [None, "balanced"]:
    model = LogisticRegression(max_iter=2000, class_weight=cw).fit(X_train, y_train)
    pred = model.predict(X_test)
    print(f"class_weight={cw}: «уйдёт» у {pred.mean():.0%}, precision {precision_score(y_test, pred):.2f}, "
          f"recall {recall_score(y_test, pred):.2f}, F1 {f1_score(y_test, pred):.2f}")
```

`None` — значение по умолчанию, все строки весят одинаково. Со взвешиванием модель ловит уже около 79 % уходящих вместо 60 %, но точность падает примерно с 0.81 до 0.62: бонусов раздаём больше, и часть уходит впустую. F1 почти не изменился — модель не стала умнее, она сдвинулась вдоль того же компромисса, что и при снижении порога.

{{practice: lr-bal, forest-bal, thr-match}}

## Разберём вместе: как вес меняет решение в листе

Возьмём один лист дерева, в который попали 9 гостей обучения: 6 оставшихся и 3 ушедших. Без весов лист отвечает большинством — «останется», и вероятность ухода в нём 3 / 9 = **0.33**.

Теперь веса `"balanced"` для наших гостей: оставшийся весит 0.64, ушедший — 2.24.

- «Голоса» оставшихся: 6 × 0.64 = **3.84**.
- «Голоса» ушедших: 3 × 2.24 = **6.72**.
- Взвешенная доля ухода: 6.72 / (3.84 + 6.72) ≈ **0.64** — лист теперь отвечает «уйдёт».

Что получилось: в листе ничего не поменялось — те же 9 гостей, но решение перевернулось. Именно так веса работают в смешанных листьях. А в «чистом» листе (скажем, 4 оставшихся и 0 ушедших) никакой вес не сделает долю ухода больше нуля — поэтому у глубокого леса без `min_samples_leaf` веса действуют слабее: в основном через выбор вопросов по пути к листьям.

::: figure weight-leaf
Разбор с одним листом: те же девять гостей, но с весами `balanced` голоса трёх ушедших (6.72) перевешивают голоса шести оставшихся (3.84), и ответ листа переворачивается.
:::

::: tip Аналогия
Экскурсовод спрашивает группу, не идёт ли он слишком быстро. Двадцать бодрых туристов кричат «нормально», пятеро пожилых тихо говорят «быстро» — по большинству всё хорошо. Опытный экскурсовод прислушивается к тихой пятёрке внимательнее: её голос для него «весит» больше. Веса классов делают то же с редким классом.
:::

У логистической регрессии то же самое, только вместо листа — штраф за ошибку: промах на ушедшем госте стоит в 2.24 / 0.64 = 3.5 раза дороже, и модель сдвигает границу в сторону ответа «уйдёт».

::: tip Свои веса
Вместо `"balanced"` можно задать веса словарём: `class_weight={0: 1, 1: 3}` — ошибка на уходящем втрое дороже. Так удобно, когда известна реальная цена ошибок.
:::

::: note Лес и веса
У леса `class_weight="balanced"` тоже работает, но слабее, чем у линейной модели: глубокие деревья доращивают листья до «чистых», где все гости одного класса, и в таких листьях вес ответа не меняет. Но веса влияют на выбор вопросов по пути: дерево охотнее отделяет уходящих, и листья получаются другими. Ограничение `min_samples_leaf=5` (не меньше 5 гостей в листе, глава 6) оставляет листья смешанными, и веса начинают ещё и решать, какой класс в листе победит, — эффект усиливается. В задаче на трёх лесах полнота растёт ступеньками: 0.69 у обычного леса, 0.78 с одними весами, 0.86 с весами и `min_samples_leaf=5`.
:::

{{practice: w-hand}}

## Upsampling: размножить редкий класс

Второй способ — изменить сами данные. **Upsampling** (увеличение выборки, его ещё называют oversampling) — повторить строки редкого класса столько раз, чтобы классов стало поровну. Для модели повтор строки — почти то же, что вес 2: ошибка на ней считается дважды.

Делаем руками в pandas. Собираем обучающую часть в одну таблицу, делим по классам и добираем недостающих уходящих выборкой **с возвращением** — как бутстрэп в уроке «Случайный лес» главы 6:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

train = X_train.copy()
train["churned"] = y_train
left = train[train["churned"] == 1]
stayed = train[train["churned"] == 0]

extra = left.sample(n=len(stayed) - len(left), replace=True, random_state=0)
train_up = pd.concat([train, extra])
print(len(train), "→", len(train_up))
print(train_up["churned"].value_counts())
X_up = train_up.drop(columns="churned")
y_up = train_up["churned"]
```

- `sample(n=..., replace=True)` выбирает n строк с возвращением: одна строка может попасть несколько раз. Без `replace=True` нельзя взять 998 строк из 401;
- `pd.concat([train, extra])` — `UNION ALL` из главы 2: исходные строки плюс копии;
- индексы копий совпадают с индексами оригиналов — по ним видно, что это один и тот же гость.

Дальше обычное обучение на `X_up, y_up` и проверка на **нетронутом** тесте. Тест не балансируем никогда: он должен быть похож на реальный поток гостей, где уходящих 22 %.

{{practice: upsample}}

## Downsampling: проредить частый класс

Обратный путь — **downsampling** (уменьшение выборки, undersampling): случайно оставить из частого класса столько строк, сколько в редком. Повторов нет, но часть данных выбрасывается.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

train = X_train.copy()
train["churned"] = y_train
left = train[train["churned"] == 1]
stayed = train[train["churned"] == 0]

train_down = pd.concat([left, stayed.sample(n=len(left), random_state=0)])
print("строк для обучения:", len(train_down), "из", len(train))

model = LogisticRegression(max_iter=2000).fit(train_down.drop(columns="churned"), train_down["churned"])
pred = model.predict(X_test)
print(f"precision {precision_score(y_test, pred):.2f}, recall {recall_score(y_test, pred):.2f}")
```

Обучаемся всего на 802 гостях из 1800, а результат примерно как у весов: полнота около 0.77, точность около 0.62.

Когда что брать:

- **веса** — первый выбор: данные не меняются, ничего не выбрасывается, одна строка кода;
- **upsampling** — когда у модели нет `class_weight`. Минус: копии одних и тех же гостей, гибкая модель может их просто запомнить;
- **downsampling** — когда данных очень много и обучение медленное: миллион строк частого класса можно проредить почти без потерь. На наших 1800 гостях выбрасывать данные жалко.

::: figure up-down
Обучающая часть до и после балансировки: upsampling добирает 998 копий ушедших, downsampling оставляет 401 случайного из 1 399 оставшихся. Тест в обоих случаях не трогаем.
:::

::: sql
Downsampling в SQL — `UNION ALL` из всех уходящих и случайной выборки оставшихся: `SELECT * FROM stayed ORDER BY RANDOM() LIMIT 401`.
:::

{{practice: p-down}}

## Балансировка до разбиения — утечка

Соблазнительно сбалансировать всю таблицу сразу, а потом разбить на train и test — кода меньше. Это ошибка. При upsampling копии одного и того же гостя разлетаются по обеим частям: модель видела гостя на обучении, а потом «угадывает» его же на тесте. Посмотрим, что выходит у леса:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})

# НЕПРАВИЛЬНО: размножаем уходящих во всей таблице, а потом делим
full = X.copy()
full["churned"] = y
left = full[full["churned"] == 1]
stayed = full[full["churned"] == 0]
full_up = pd.concat([full, left.sample(n=len(stayed) - len(left), replace=True, random_state=0)])
Xa, Xb, ya, yb = train_test_split(full_up.drop(columns="churned"), full_up["churned"],
                                  test_size=0.25, random_state=42, stratify=full_up["churned"])

model = RandomForestClassifier(n_estimators=50, random_state=0).fit(Xa, ya)
pb = model.predict_proba(Xb)[:, 1]
print(f"F1 {f1_score(yb, pb >= 0.5):.2f}, ROC-AUC {roc_auc_score(yb, pb):.3f}")
print(f"уходящих в тесте, чья копия есть в train: {yb.index[yb == 1].isin(Xa.index).mean():.0%}")
```

F1 около 0.94 и AUC около 0.99 — «почти идеальная» модель. На самом деле около 90 % уходящих гостей теста лес уже видел на обучении — их копии лежат в train. Метод `index.isin(...)` проверяет, есть ли каждый индекс в другом списке. Вдобавок в таком тесте уходящих 50 %, а не 22 %, как в жизни, — его precision ничего не говорит о реальной рассылке.

::: figure balance-leak
Слева копии одного и того же ушедшего гостя после разбиения оказались и в train, и в test — модель «узнаёт» их, и метрики завышены. Справа копии появляются только внутри обучающей части, тест остаётся честным.
:::

::: warn Сначала разбиение, потом балансировка
Любые действия, которые смотрят на данные целиком, — балансировка, заполнение пропусков средним, масштабирование — делаются **после** разбиения и **только по обучающей части**. Это та же утечка, что и в главе 6: в обучение попадает информация из теста. В кросс-валидации правило то же: размножать строки нужно в обучающих фолдах внутри каждого прохода, а не во всей таблице заранее (задача со звёздочкой). У `class_weight` такой проблемы нет: веса пересчитываются при каждом обучении по тем строкам, на которых модель учится, — ещё один плюс весов.
:::

::: quiz
Аналитик сделал upsampling редкого класса, а потом разбил данные на train и test. Что не так?

- [x] Копии одних и тех же уходящих гостей попали и в train, и в test — модель «узнаёт» их, и оценка завышена
  > Балансируют только обучающую часть, после разбиения, а внутри кросс-валидации — на каждом фолде заново.
- [ ] Ничего: порядок шагов не важен
  > Важен: копии строк по разные стороны разбиения — та же утечка, что и подглядывание в тест.
- [ ] Upsampling всегда портит модель
  > На обучающей части он бывает полезен, вред — от неверного порядка.
- [ ] Тест стал слишком большим
  > Дело не в размере, а в повторах строк в train и test.
:::

{{practice: leak, cv-up}}

## Что меняется, а что почти нет

Сведём все способы в одну таблицу. Последняя строка — обычная модель без всякой балансировки, но с порогом 0.3 вместо 0.5, как в прошлом уроке:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

train = X_train.copy()
train["churned"] = y_train
left = train[train["churned"] == 1]
stayed = train[train["churned"] == 0]
train_up = pd.concat([train, left.sample(n=len(stayed) - len(left), replace=True, random_state=0)])
train_down = pd.concat([left, stayed.sample(n=len(left), random_state=0)])

def fit_p(Xt, yt, cw=None):
    """Обучить на (Xt, yt) и вернуть вероятности ухода на общем тесте X_test."""
    model = LogisticRegression(max_iter=2000, class_weight=cw).fit(Xt, yt)
    return model.predict_proba(X_test)[:, 1]      # X_test берём из кода выше: тест у всех вариантов один

p_plain = fit_p(X_train, y_train)
variants = [
    ("как есть", p_plain, 0.5),
    ("balanced", fit_p(X_train, y_train, "balanced"), 0.5),
    ("upsampling", fit_p(train_up.drop(columns="churned"), train_up["churned"]), 0.5),
    ("downsampling", fit_p(train_down.drop(columns="churned"), train_down["churned"]), 0.5),
    ("порог 0.3", p_plain, 0.3),
]
rows = []
for name, p, t in variants:
    pred = p >= t
    rows.append({"способ": name, "precision": precision_score(y_test, pred), "recall": recall_score(y_test, pred),
                 "F1": f1_score(y_test, pred), "AUC": roc_auc_score(y_test, p), "средняя p": p.mean()})
print(pd.DataFrame(rows).round(3))
```

Что видно:

- **precision и recall** меняются сильно: все три способа балансировки поднимают полноту примерно с 0.60 до 0.77–0.79 и опускают точность примерно до 0.62;
- **F1** почти стоит на месте (0.69–0.71) — компромисс сдвинулся, а не улучшился;
- **AUC** почти не меняется (около 0.90): балансировка не учит модель лучше отличать уходящих от оставшихся, порядок гостей по риску остаётся почти тем же;
- **обычная модель с порогом 0.3** даёт результат того же уровня — без переобучения модели.

Почему так? Балансировка в основном сдвигает вероятности вверх: модель «думает», что уходящих половина, и средняя вероятность ухода у неё около 0.38, хотя на самом деле уходят 22 %. Сдвиг вероятностей вверх при пороге 0.5 — почти то же, что порог ниже 0.5 у обычной модели.

::: predict
```python static
from sklearn.metrics import roc_auc_score
y = [0, 1, 0, 1]
p = [0.1, 0.3, 0.4, 0.8]
p_up = [x + 0.15 for x in p]
print(roc_auc_score(y, p), roc_auc_score(y, p_up))
```

- `0.75 0.95`
- [x] `0.75 0.75`
- `0.75 1.0`

Почему: AUC зависит только от порядка оценок (прошлый урок). Прибавка 0.15 ко всем оценкам порядок не меняет — значит, и AUC тот же. А ответы при пороге 0.5 изменятся: у p «да» только у одного гостя, у p_up — уже у двух.
:::

::: warn Вероятности после балансировки завышены
Правило из прошлого урока «бонус выгоден при p > 200 / 1000» требует честных вероятностей. После балансировки средняя p в 1.7 раза выше реальной доли уходящих (около 0.38 против 0.22) — считать по ней деньги нельзя. Если порог выбирается по деньгам, удобнее обычная модель плюс подбор порога.
:::

::: warn Типичные ошибки
- **Балансировка до разбиения.** Копии одного гостя попадают и в обучение, и в тест — метрики завышены (раздел про утечку выше).
- **Балансировка теста.** Тест должен оставаться таким, каким будет реальный поток гостей: 22 % ушедших, а не 50 %.
- **Деньги по вероятностям после балансировки.** Средняя p 0.38 при реальных 22 % — для расчёта прибыли такие числа не годятся.
- **Ожидание чуда.** Балансировка двигает компромисс точность/полнота, но почти не меняет AUC. Если нужна модель лучше — нужны признаки, а не веса.
:::

::: quiz
После `class_weight="balanced"` полнота логистической регрессии выросла примерно с 0.60 до 0.79. Стала ли модель лучше отличать уходящих гостей от оставшихся?

- [x] Почти нет: AUC остался около 0.90, модель просто чаще говорит «уйдёт»
  > Веса сдвинули вероятности вверх, и при пороге 0.5 бонусов стало больше. Порядок гостей по риску почти тот же — это движение вдоль компромисса точность/полнота, как при снижении порога.
- [ ] Да: полнота выросла, значит, модель стала умнее
  > Полнота выросла ценой точности, а F1 почти не изменился. Рост одной метрики за счёт другой — не улучшение модели.
- [ ] Да, и её вероятностям теперь можно верить точнее
  > Наоборот: после балансировки вероятности завышены — модель «думает», что уходящих половина. Для расчёта денег они хуже.
- [ ] Нет, она стала хуже: AUC заметно упал
  > AUC почти не меняется: балансировка в основном сдвигает оценки, а не переставляет гостей местами.
:::

## Практика

## task: w-hand | Веса руками | warmup

Посчитайте веса классов, которые выставит `class_weight="balanced"` для обучающей части: `w0` — вес оставшихся гостей, `w1` — вес уходящих (оба — 3 знака). Формула: n / (2 × n_класса).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.utils.class_weight import compute_class_weight as _ccw
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_w = _ccw('balanced', classes=_np.array([0, 1]), y=_c)
_w0, _w1 = round(float(_w[0]), 3), round(float(_w[1]), 3)
_tw = (len(_y) / (2 * _y.value_counts())).round(3)
_got0, _got1 = need('w0'), need('w1')
if close(_got1, _tw[1]) and not close(_got1, _w1):
    raise AssertionError(f'w1 = {_got1} — похоже, вы считали по всей таблице. Веса считаются только по обучающей части: y_train.')
assert close(_got0, _w0), f'w0 = {_got0}, а ожидалось {_w0}. n — число строк в y_train, n_класса — сколько из них с churned = 0.'
assert close(_got1, _w1), f'w1 = {_got1}, а ожидалось {_w1}.'
```

### hint
Число строк в каждом классе — `y_train.value_counts()`; `n` — `len(y_train)`.

### hint
`w1 = round(len(y_train) / (2 * (y_train == 1).sum()), 3)` — и так же для класса 0.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

n = len(y_train)
w0 = round(n / (2 * (y_train == 0).sum()), 3)
w1 = round(n / (2 * (y_train == 1).sum()), 3)
```

### explain
Вес уходящего гостя примерно в 3.5 раза больше: ровно во столько раз оставшихся больше, чем уходящих. Проверить себя можно функцией `compute_class_weight("balanced", classes=..., y=y_train)` из `sklearn.utils.class_weight` — она считает то же самое.

## task: share-pred | Модель недооценивает отток | warmup

Обучите `LogisticRegression(max_iter=2000)` без весов и сохраните: `share_true` — долю ушедших в тесте, `share_pred` — долю тестовых гостей, которым модель (`predict`) отвечает «уйдёт» (обе — 3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_t = round(float(_d.mean()), 3)
_p = round(float(_LR(max_iter=2000).fit(_a, _c).predict(_b).mean()), 3)
assert close(need('share_true'), _t), f'share_true = {need("share_true")}, а ожидалось {_t}. Это среднее y_test — доля единиц.'
assert close(need('share_pred'), _p), f'share_pred = {need("share_pred")}, а ожидалось {_p}. Это среднее ответов predict на X_test (модель без class_weight).'
```

### hint
Среднее столбца из 0 и 1 — доля единиц: `y_test.mean()`.

### hint
`model.predict(X_test).mean()` — доля ответов «уйдёт». Не забудьте `round(..., 3)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = LogisticRegression(max_iter=2000).fit(X_train, y_train)
share_true = round(float(y_test.mean()), 3)
share_pred = round(float(model.predict(X_test).mean()), 3)
```

## task: p-down | Собрать downsampling | warmup

Соберите программу: проредить оставшихся гостей в обучающей части до числа уходящих и вывести размер новой таблицы и долю уходящих в ней.

### parsons
```python
import pandas as pd
from sklearn.model_selection import train_test_split
g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
train = X_train.copy()
train["churned"] = y_train
left = train[train["churned"] == 1]
stayed = train[train["churned"] == 0]
train_down = pd.concat([left, stayed.sample(n=len(left), random_state=0)])
print(len(train_down), train_down["churned"].mean())
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_n = 2 * int(_c.sum())
assert _lines == [f'{_n} 0.5'], f'Программа вывела {_lines}, а должна вывести одну строку: {_n} 0.5. Разбиение — до балансировки, прореживаем только оставшихся.'
```

### hint
Сначала данные и разбиение, потом таблица `train` с целевым столбцом, потом деление на классы и прореживание.

## task: lr-bal | Взвешенная логистическая регрессия | base

Обучите `LogisticRegression(max_iter=2000, class_weight="balanced")` и посчитайте на тесте `prec`, `rec`, `f1` (по ответам `predict`) и `auc` (по вероятностям) — все с 3 знаками. Затем сохраните `auc_plain` — ROC-AUC такой же модели **без** весов (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import precision_score as _ps, recall_score as _rs, f1_score as _fs, roc_auc_score as _auc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_m = _LR(max_iter=2000, class_weight='balanced').fit(_a, _c)
_pr = _m.predict(_b)
_w = {'prec': _ps(_d, _pr), 'rec': _rs(_d, _pr), 'f1': _fs(_d, _pr), 'auc': _auc(_d, _m.predict_proba(_b)[:, 1])}
_w = {k: round(float(v), 3) for k, v in _w.items()}
_ap = round(float(_auc(_d, _LR(max_iter=2000).fit(_a, _c).predict_proba(_b)[:, 1])), 3)
assert close(need('rec'), _w['rec']), f'rec = {need("rec")}, а ожидалось {_w["rec"]}. Модель — с class_weight="balanced", ответы — predict(X_test).'
assert close(need('prec'), _w['prec']), f'prec = {need("prec")}, а ожидалось {_w["prec"]}.'
assert close(need('f1'), _w['f1']), f'f1 = {need("f1")}, а ожидалось {_w["f1"]}.'
assert close(need('auc'), _w['auc']), f'auc = {need("auc")}, а ожидалось {_w["auc"]}. ROC-AUC считается по predict_proba(X_test)[:, 1], а не по ответам predict.'
assert close(need('auc_plain'), _ap), f'auc_plain = {need("auc_plain")}, а ожидалось {_ap}. Это та же логистическая регрессия, но без class_weight.'
```

### hint
`model = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X_train, y_train)`, затем `pred = model.predict(X_test)` и `p = model.predict_proba(X_test)[:, 1]`.

### hint
Метрики: `precision_score(y_test, pred)`, …, `roc_auc_score(y_test, p)`. Для `auc_plain` обучите вторую модель без `class_weight`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

model = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X_train, y_train)
pred = model.predict(X_test)
prec = round(precision_score(y_test, pred), 3)
rec = round(recall_score(y_test, pred), 3)
f1 = round(f1_score(y_test, pred), 3)
auc = round(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]), 3)

plain = LogisticRegression(max_iter=2000).fit(X_train, y_train)
auc_plain = round(roc_auc_score(y_test, plain.predict_proba(X_test)[:, 1]), 3)
```

### explain
Полнота выросла почти до 0.8, точность упала примерно до 0.62, а AUC обеих моделей около 0.90 и отличается лишь в третьем знаке. Веса передвинули модель вдоль кривой «точность — полнота», но не подняли саму кривую.

## task: upsample | Upsampling руками | base

Сделайте upsampling обучающей части:

1. Таблица `train` — `X_train` плюс столбец `churned` из `y_train`.
2. `extra` — недостающие уходящие: `sample(n=..., replace=True, random_state=0)` из уходящих гостей `train`, столько, чтобы классов стало поровну.
3. `train_up = pd.concat([train, extra])`.

Обучите на `train_up` модель `LogisticRegression(max_iter=2000)` (без весов) и сохраните `rec_up` и `prec_up` — полноту и точность на тесте (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import precision_score as _ps, recall_score as _rs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_tr = _a.copy()
_tr['churned'] = _c
_l, _s = _tr[_tr['churned'] == 1], _tr[_tr['churned'] == 0]
_up = _pd.concat([_tr, _l.sample(n=len(_s) - len(_l), replace=True, random_state=0)])
_t = need('train_up', _pd.DataFrame)
assert 'churned' in _t.columns, 'В train_up нет столбца churned — добавьте его в train до размножения.'
assert len(_t) == len(_up), f'В train_up {len(_t)} строк, а ожидалось {len(_up)}: все {len(_tr)} строк train плюс копии уходящих, пока классов не станет поровну. Размножайте только обучающую часть.'
assert int(_t['churned'].sum()) == len(_s), f'Уходящих в train_up {int(_t["churned"].sum())}, а должно быть столько же, сколько оставшихся: {len(_s)}.'
assert _t.index.isin(_a.index).all(), 'В train_up есть гости не из обучающей части. Размножайте только train, тест не трогайте.'
_m = _LR(max_iter=2000).fit(_up.drop(columns='churned'), _up['churned'])
_pr = _m.predict(_b)
_wr, _wp = round(float(_rs(_d, _pr)), 3), round(float(_ps(_d, _pr)), 3)
assert close(need('rec_up'), _wr, 0.0015), f'rec_up = {need("rec_up")}, а ожидалось {_wr}. Модель — на train_up без столбца churned, проверка — на X_test.'
assert close(need('prec_up'), _wp, 0.0015), f'prec_up = {need("prec_up")}, а ожидалось {_wp}.'
```

### hint
Сколько добрать: `len(stayed) - len(left)`, где `left` и `stayed` — уходящие и оставшиеся из `train`.

### hint
Признаки и ответы из `train_up`: `train_up.drop(columns="churned")` и `train_up["churned"]`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

train = X_train.copy()
train["churned"] = y_train
left = train[train["churned"] == 1]
stayed = train[train["churned"] == 0]
extra = left.sample(n=len(stayed) - len(left), replace=True, random_state=0)
train_up = pd.concat([train, extra])

model = LogisticRegression(max_iter=2000).fit(train_up.drop(columns="churned"), train_up["churned"])
pred = model.predict(X_test)
rec_up = round(recall_score(y_test, pred), 3)
prec_up = round(precision_score(y_test, pred), 3)
```

### explain
Результат почти совпал с `class_weight="balanced"`: повторить строку уходящего гостя два-три раза — почти то же самое, что дать ей вес 2–3. Разница только в случайности: какие именно гости повторились чаще.

## task: forest-bal | Веса у леса | base

Сравните три леса из 50 деревьев с `random_state=0`, меняя по одной настройке: обычный, с `class_weight="balanced"` и с `class_weight="balanced", min_samples_leaf=5`. Сохраните точность и полноту на тесте по ответам `predict` (3 знака): `prec_plain`, `rec_plain`, `prec_w`, `rec_w`, `prec_bal`, `rec_bal`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import precision_score as _ps, recall_score as _rs
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_p0 = _RF(n_estimators=50, random_state=0).fit(_a, _c).predict(_b)
_pw = _RF(n_estimators=50, random_state=0, class_weight='balanced').fit(_a, _c).predict(_b)
_p1 = _RF(n_estimators=50, random_state=0, class_weight='balanced', min_samples_leaf=5).fit(_a, _c).predict(_b)
_w = {'prec_plain': _ps(_d, _p0), 'rec_plain': _rs(_d, _p0), 'prec_w': _ps(_d, _pw), 'rec_w': _rs(_d, _pw), 'prec_bal': _ps(_d, _p1), 'rec_bal': _rs(_d, _p1)}
_how = {'plain': ', без весов.', 'w': ', class_weight="balanced", без min_samples_leaf.', 'bal': ', class_weight="balanced", min_samples_leaf=5.'}
for _k, _v in _w.items():
    _v = round(float(_v), 3)
    assert close(need(_k), _v), f'{_k} = {need(_k)}, а ожидалось {_v}. Проверьте настройки леса: n_estimators=50, random_state=0' + _how[_k.split('_')[1]]
```

### hint
Второй лес — `RandomForestClassifier(n_estimators=50, random_state=0, class_weight="balanced")`, третий — то же плюс `min_samples_leaf=5`.

### hint
Для каждого леса: `.fit(X_train, y_train).predict(X_test)`, затем `precision_score` и `recall_score`.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

plain = RandomForestClassifier(n_estimators=50, random_state=0).fit(X_train, y_train)
w = RandomForestClassifier(n_estimators=50, random_state=0, class_weight="balanced").fit(X_train, y_train)
bal = RandomForestClassifier(n_estimators=50, random_state=0, class_weight="balanced", min_samples_leaf=5).fit(X_train, y_train)
p0, pw, p1 = plain.predict(X_test), w.predict(X_test), bal.predict(X_test)
prec_plain, rec_plain = round(precision_score(y_test, p0), 3), round(recall_score(y_test, p0), 3)
prec_w, rec_w = round(precision_score(y_test, pw), 3), round(recall_score(y_test, pw), 3)
prec_bal, rec_bal = round(precision_score(y_test, p1), 3), round(recall_score(y_test, p1), 3)
```

### explain
Полнота растёт ступеньками: 0.69 у обычного леса, 0.78 с весами, 0.86 с весами и `min_samples_leaf=5`; точность падает так же — 0.79, 0.67, 0.62. Веса у леса работают и сами по себе, а ограничение листа их усиливает. Картина та же, что у логистической регрессии: веса двигают компромисс в сторону полноты, а не делают модель лучше.

## task: leak | Утечка через балансировку | plus

Повторите ошибку из теории и сравните с честным подходом. Лес везде — `RandomForestClassifier(n_estimators=50, random_state=0)`.

1. **Неправильно**: таблица `full` — `X` плюс столбец `churned`; размножьте уходящих во всей таблице (`sample(n=..., replace=True, random_state=0)`, классов поровну), затем разбейте `train_test_split(..., test_size=0.25, random_state=42, stratify=...)`. Сохраните `f1_leak` — F1 леса на такой «тестовой» части (3 знака) и `share_copies` — долю уходящих гостей этой тестовой части, чей индекс встречается в её обучающей части (3 знака).
2. **Правильно**: возьмите обычное разбиение (оно уже в заготовке), размножьте уходящих только в обучающей части тем же способом и сохраните `f1_honest` — F1 леса на обычном тесте (3 знака).

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import f1_score as _f1
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
def _up(df):
    l, s = df[df['churned'] == 1], df[df['churned'] == 0]
    return _pd.concat([df, l.sample(n=len(s) - len(l), replace=True, random_state=0)])
_full = _X.copy()
_full['churned'] = _y
_fu = _up(_full)
_xa, _xb, _ya, _yb = _tts(_fu.drop(columns='churned'), _fu['churned'], test_size=0.25, random_state=42, stratify=_fu['churned'])
_wl = round(float(_f1(_yb, _RF(n_estimators=50, random_state=0).fit(_xa, _ya).predict(_xb))), 3)
_ws = round(float(_yb.index[_yb == 1].isin(_xa.index).mean()), 3)
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_tr = _a.copy()
_tr['churned'] = _c
_tu = _up(_tr)
_wh = round(float(_f1(_d, _RF(n_estimators=50, random_state=0).fit(_tu.drop(columns='churned'), _tu['churned']).predict(_b))), 3)
assert close(need('f1_leak'), _wl, 0.0015), f'f1_leak = {need("f1_leak")}, а ожидалось {_wl}. Сначала размножение всей таблицы, потом разбиение со stratify по размноженному столбцу churned.'
assert close(need('share_copies'), _ws, 0.0015), f'share_copies = {need("share_copies")}, а ожидалось {_ws}. Берите индексы уходящих гостей тестовой части и проверяйте .isin(индекс обучающей части).'
assert close(need('f1_honest'), _wh, 0.0015), f'f1_honest = {need("f1_honest")}, а ожидалось {_wh}. Размножайте только train из обычного разбиения, проверяйте на X_test.'
```

### hint
Удобно написать функцию `upsample(df)`, которая делит таблицу по `churned`, добирает уходящих и возвращает `pd.concat([df, extra])`, — она нужна дважды.

### hint
Доля копий: `yb.index[yb == 1].isin(Xa.index).mean()`, где `Xa, Xb, ya, yb` — результат разбиения размноженной таблицы.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

def upsample(df):
    left = df[df["churned"] == 1]
    stayed = df[df["churned"] == 0]
    extra = left.sample(n=len(stayed) - len(left), replace=True, random_state=0)
    return pd.concat([df, extra])

full = X.copy()
full["churned"] = y
full_up = upsample(full)
Xa, Xb, ya, yb = train_test_split(full_up.drop(columns="churned"), full_up["churned"],
                                  test_size=0.25, random_state=42, stratify=full_up["churned"])
model = RandomForestClassifier(n_estimators=50, random_state=0).fit(Xa, ya)
f1_leak = round(f1_score(yb, model.predict(Xb)), 3)
share_copies = round(float(yb.index[yb == 1].isin(Xa.index).mean()), 3)

train = X_train.copy()
train["churned"] = y_train
train_up = upsample(train)
model = RandomForestClassifier(n_estimators=50, random_state=0).fit(train_up.drop(columns="churned"), train_up["churned"])
f1_honest = round(f1_score(y_test, model.predict(X_test)), 3)
```

### explain
F1 около 0.94 против около 0.70 — разница целиком из-за утечки: копии девяти из десяти уходящих гостей «теста» лес уже видел. Такую модель на реальных новых гостях ждёт разочарование.

## task: thr-match | Веса или порог | plus

Проверьте, что сдвиг порога у обычной модели даёт почти то же, что веса.

1. Взвешенная модель `LogisticRegression(max_iter=2000, class_weight="balanced")`: `rec_bal` и `prec_bal` — полнота и точность на тесте при пороге 0.5 (3 знака).
2. Обычная модель `LogisticRegression(max_iter=2000)`: по её PR-кривой на тесте (`precision_recall_curve`, прошлый урок) найдите порог `t_match` с наибольшей точностью среди тех, где полнота **не ниже** `rec_bal`, и `prec_match` — точность при нём (оба — 3 знака).

Для сравнения с `rec_bal` берите неокруглённую полноту.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, precision_recall_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.linear_model import LogisticRegression as _LR
from sklearn.metrics import precision_score as _ps, recall_score as _rs, precision_recall_curve as _prc
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_pb = _LR(max_iter=2000, class_weight='balanced').fit(_a, _c).predict_proba(_b)[:, 1] >= 0.5
_rb, _pbv = _rs(_d, _pb), _ps(_d, _pb)
_p0 = _LR(max_iter=2000).fit(_a, _c).predict_proba(_b)[:, 1]
_pr, _rc, _th = _prc(_d, _p0)
_cv = _pd.DataFrame({'threshold': _th, 'precision': _pr[:-1], 'recall': _rc[:-1]})
_best = _cv[_cv['recall'] >= _rb].sort_values('precision').iloc[-1]
assert close(need('rec_bal'), round(_rb, 3)), f'rec_bal = {need("rec_bal")}, а ожидалось {round(_rb, 3)}. Взвешенная модель, порог 0.5 (обычный predict).'
assert close(need('prec_bal'), round(_pbv, 3)), f'prec_bal = {need("prec_bal")}, а ожидалось {round(_pbv, 3)}.'
assert close(need('t_match'), round(float(_best['threshold']), 3), 0.0015), f't_match = {need("t_match")}, а ожидалось {round(float(_best["threshold"]), 3)}. Кривая — по вероятностям обычной модели; среди порогов с recall ≥ rec_bal берите тот, где precision наибольшая.'
assert close(need('prec_match'), round(float(_best['precision']), 3), 0.0015), f'prec_match = {need("prec_match")}, а ожидалось {round(float(_best["precision"]), 3)}.'
```

### hint
Таблица порогов, как в прошлом уроке: `pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1]})`.

### hint
Сохраните неокруглённую полноту взвешенной модели в отдельную переменную, отфильтруйте `curve[curve["recall"] >= r]` и возьмите строку с наибольшей точностью.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, precision_recall_curve

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

pred_bal = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X_train, y_train).predict(X_test)
r = recall_score(y_test, pred_bal)
rec_bal = round(r, 3)
prec_bal = round(precision_score(y_test, pred_bal), 3)

p = LogisticRegression(max_iter=2000).fit(X_train, y_train).predict_proba(X_test)[:, 1]
precision, recall, thresholds = precision_recall_curve(y_test, p)
curve = pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1]})
best = curve[curve["recall"] >= r].sort_values("precision").iloc[-1]
t_match = round(best["threshold"], 3)
prec_match = round(best["precision"], 3)
```

### explain
Обычной модели для той же полноты хватает порога чуть выше 0.2 — и точность при нём почти такая же, как у взвешенной (разница около 0.01). Веса и порог — два способа сдвинуть один и тот же компромисс. Порог удобнее: модель не нужно переобучать, а вероятности остаются честными.

## task: cv-up | Балансировка внутри кросс-валидации | star

Upsampling и кросс-валидация: где утечка? Работаем только с `X_train, y_train`, лес `RandomForestClassifier(n_estimators=50, random_state=0)`, фолды `kf = KFold(n_splits=5, shuffle=True, random_state=42)` (глава 6, урок «Честное сравнение моделей»).

1. **Неправильно**: размножьте уходящих во всей обучающей части (`train_up`, как в задаче про upsampling) и оцените лес через `cross_val_score(model, X_up, y_up, cv=kf, scoring="f1")`. Параметр `scoring` говорит, какую метрику считать на каждом фолде: по умолчанию accuracy, `"f1"` — F1. Сохраните `f1_wrong` — среднее (3 знака).
2. **Правильно**: циклом `for tr, va in kf.split(X_train):` размножайте уходящих только в обучающих фолдах (`train.iloc[tr]`, тот же `sample(..., random_state=0)`) — столько, чтобы внутри обучающего фолда классов стало поровну, обучайте лес и считайте F1 на валидационном фолде **без** размножения. Сохраните `f1_right` — среднее по фолдам (3 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
train = X_train.copy()
train["churned"] = y_train
kf = KFold(n_splits=5, shuffle=True, random_state=42)

```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.metrics import f1_score as _f1
_g = _pd.read_csv('guests_churn.csv')
_y = _g['churned']
_X = _pd.get_dummies(_g.drop(columns=['guest_id', 'churned', 'card_blocked']), dtype=int).fillna({'avg_check': 0})
_a, _b, _c, _d = _tts(_X, _y, test_size=0.25, random_state=42, stratify=_y)
_tr = _a.copy()
_tr['churned'] = _c
_kf = _KF(n_splits=5, shuffle=True, random_state=42)
def _up(df):
    l, s = df[df['churned'] == 1], df[df['churned'] == 0]
    return _pd.concat([df, l.sample(n=len(s) - len(l), replace=True, random_state=0)])
_u = _up(_tr)
_ww = round(float(_cvs(_RF(n_estimators=50, random_state=0), _u.drop(columns='churned'), _u['churned'], cv=_kf, scoring='f1').mean()), 3)
_sc = []
for _i, _j in _kf.split(_a):
    _uu = _up(_tr.iloc[_i])
    _m = _RF(n_estimators=50, random_state=0).fit(_uu.drop(columns='churned'), _uu['churned'])
    _sc.append(_f1(_c.iloc[_j], _m.predict(_a.iloc[_j])))
_wr = round(float(_np.mean(_sc)), 3)
assert close(need('f1_wrong'), _ww, 0.0015), f'f1_wrong = {need("f1_wrong")}, а ожидалось {_ww}. Размножьте всю обучающую часть, потом cross_val_score(..., cv=kf, scoring="f1").'
assert close(need('f1_right'), _wr, 0.0015), f'f1_right = {need("f1_right")}, а ожидалось {_wr}. Размножайте только train.iloc[tr]; F1 считайте на X_train.iloc[va] и y_train.iloc[va] без копий.'
```

### hint
`scoring="f1"` — метрика для каждого фолда (см. условие). Функция `upsample(df)` из задачи про утечку пригодится и здесь.

### hint
Внутри цикла: `u = upsample(train.iloc[tr])`, лес на `u.drop(columns="churned"), u["churned"]`, затем `f1_score(y_train.iloc[va], model.predict(X_train.iloc[va]))`. Список F1 усредните через `np.mean`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

g = pd.read_csv("guests_churn.csv")
y = g["churned"]
X = pd.get_dummies(g.drop(columns=["guest_id", "churned", "card_blocked"]), dtype=int).fillna({"avg_check": 0})
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
train = X_train.copy()
train["churned"] = y_train
kf = KFold(n_splits=5, shuffle=True, random_state=42)

def upsample(df):
    left = df[df["churned"] == 1]
    stayed = df[df["churned"] == 0]
    return pd.concat([df, left.sample(n=len(stayed) - len(left), replace=True, random_state=0)])

train_up = upsample(train)
wrong = cross_val_score(RandomForestClassifier(n_estimators=50, random_state=0),
                        train_up.drop(columns="churned"), train_up["churned"], cv=kf, scoring="f1")
f1_wrong = round(float(wrong.mean()), 3)

scores = []
for tr, va in kf.split(X_train):
    u = upsample(train.iloc[tr])
    model = RandomForestClassifier(n_estimators=50, random_state=0).fit(u.drop(columns="churned"), u["churned"])
    scores.append(f1_score(y_train.iloc[va], model.predict(X_train.iloc[va])))
f1_right = round(float(np.mean(scores)), 3)
```

### explain
Неправильная кросс-валидация обещает F1 около 0.94, честная — около 0.68: в первом случае копии уходящих гостей попадают и в обучающие, и в проверочные фолды. Ручной цикл громоздкий, а с весами цикл не нужен: задайте модели `RandomForestClassifier(class_weight="balanced")` и передайте её в `cross_val_score` как есть — веса посчитаются заново на каждом обучающем фолде. Похожим образом в уроке «Pipeline: предобработка и модель вместе» `Pipeline` встроит в модель заполнение пропусков и масштабирование.
