---
title: Честное сравнение моделей
lead: "У нас уже есть правило аналитика, дерево, лес и логистическая регрессия. Какая модель лучше — и насколько можно верить цифре? Учимся подбирать настройки так, чтобы не обманывать себя: делим данные на три части, не подглядываем в тест и сравниваем модели кросс-валидацией. Групповое разбиение и время обучения — в следующем уроке."
files: [deliveries.csv]
recap:
  - "Три части данных: обучающая (train) — учим модель, валидационная (valid) — выбираем настройки и модель, тестовая (test) — один раз проверяем итог. 60/20/20 — два вызова `train_test_split`."
  - "Если выбирать лучшее по тесту, оценка на тесте становится завышенной: мы отбираем то, чему повезло именно на этих строках."
  - "Кросс-валидация: данные делят на k частей (фолдов), модель k раз учится на k − 1 частях и проверяется на оставшейся. `cross_val_score(model, X, y, cv=kf)` возвращает k оценок."
  - "`KFold(n_splits=5, shuffle=True, random_state=42)` — правило нарезки. Сравнивайте модели на одних и тех же фолдах."
  - "Смотрите не только на среднее, но и на разброс (`std`): разница меньше разброса — не повод для громких выводов."
  - "Перебор настроек кросс-валидацией автоматизирует `GridSearchCV` — в главе 7."
---

## Одного теста мало

В уроке «Обучающая и тестовая выборки» мы научились честно проверять модель: учить на одной части данных, проверять на другой. Но с тестом легко сделать больше, чем просто проверить: перебрать глубину дерева, число деревьев в лесу, порог вероятности — и выбрать то, что лучше **на тесте**. Каждый такой выбор немного подгоняет модель под тестовые строки. Тест превращается во второй обучающий набор, и его оценка перестаёт быть честной.

Выход — разделить данные на **три** части:

| Часть | Доля | Зачем |
|---|---|---|
| обучающая, train | 60 % | модель учится |
| валидационная, valid | 20 % | сравниваем настройки и модели, выбираем лучшую |
| тестовая, test | 20 % | один раз проверяем выбранную модель — это цифра для отчёта |

`train_test_split` делит только на две части, поэтому вызываем его дважды: сначала откладываем тест, потом остаток делим на обучение и валидацию.

```python
import pandas as pd
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)

X_rest, X_test, y_rest, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_valid, y_train, y_valid = train_test_split(X_rest, y_rest, test_size=0.25, random_state=42)
print(len(X_train), len(X_valid), len(X_test))
```

Во втором вызове `test_size=0.25`: четверть от оставшихся 80 % — это 20 % от всех данных.

::: figure split-three
Два вызова `train_test_split` на наших доставках: первый откладывает тест, второй делит остаток на обучение и валидацию.
:::

::: predict
```python static
from sklearn.model_selection import train_test_split
rows = list(range(1000))
rest, test = train_test_split(rows, test_size=0.2, random_state=1)
train, valid = train_test_split(rest, test_size=0.25, random_state=1)
print(len(train), len(valid), len(test))
```

- `550 250 200`
- [x] `600 200 200`
- `800 200 200`

Почему: сначала 20 % (200 строк) уходит в тест. Второй вызов делит оставшиеся 800 строк: четверть (200) — в валидацию, 600 — в обучение.
:::

::: sql
Похоже на разделение окружений: на dev экспериментируем сколько угодно, на stage проверяем кандидата, в prod выкатываем один раз. Тест — это prod: на нём не отлаживаются.
:::

{{practice: three-parts}}

## Подбор глубины по валидации

Подберём глубину дерева честно: учим на train, сравниваем на valid, а тест трогаем один раз — для выбранной модели.

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
X_rest, X_test, y_rest, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_valid, y_train, y_valid = train_test_split(X_rest, y_rest, test_size=0.25, random_state=42)

valid_acc = {}
for depth in range(1, 11):
    model = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    valid_acc[depth] = model.score(X_valid, y_valid)
    print(depth, round(model.score(X_train, y_train), 3), round(valid_acc[depth], 3))

best = max(valid_acc, key=valid_acc.get)
final = DecisionTreeClassifier(max_depth=best, random_state=0).fit(X_train, y_train)
print("лучшая глубина:", best, "| на тесте:", round(final.score(X_test, y_test), 3))
```

`max(valid_acc, key=valid_acc.get)` — ключ словаря с наибольшим значением, то есть глубина с лучшей долей правильных ответов на валидации.

Картина знакома по уроку «Обучающая и тестовая выборки»: на обучении доля правильных растёт с глубиной, а на валидации после 3–4 вопросов падает — дерево переобучается. Лучшая глубина — 4 (0.880 на валидации), но глубина 3 почти не хуже. На тесте выбранное дерево даёт 0.892, и это число можно писать в отчёт: при выборе мы его не видели.

::: tip
После выбора настроек модель часто переобучают на train + valid вместе (`X_rest`, `y_rest`) — данных больше, модель чуть точнее. Тест при этом по-прежнему остаётся нетронутым до самого конца.
:::

{{practice: pick-depth}}

## Почему нельзя подглядывать в тест

Насколько завышается оценка, если выбирать по тому же набору, на котором отчитываемся? Проведём опыт с заведомо бесполезными «моделями»: 200 монеток, каждая наугад отвечает «опоздает» или «нет». Любая из них в среднем права в половине случаев. Выберем лучшую по валидации и посмотрим, как она покажет себя на новых данных — тесте.

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
y_rest, y_test = train_test_split(y, test_size=0.2, random_state=42)
y_train, y_valid = train_test_split(y_rest, test_size=0.25, random_state=42)

rng = np.random.default_rng(0)
valid_acc, test_acc = [], []
for i in range(200):
    valid_acc.append(((rng.random(len(y_valid)) < 0.5) == y_valid).mean())
    test_acc.append(((rng.random(len(y_test)) < 0.5) == y_test).mean())

best = int(np.argmax(valid_acc))
print(f"в среднем монетка права: {np.mean(valid_acc):.3f}")
print(f"лучшая на валидации: {valid_acc[best]:.3f}, она же на тесте: {test_acc[best]:.3f}")
```

`rng.random(n) < 0.5` — n случайных `True/False`, `np.argmax` — номер наибольшего элемента списка.

Лучшая монетка «угадывает» почти 59 % — заметно выше честных 50 %. На тесте она возвращается к случайным 51–52 %: никакого умения не было, мы просто отобрали ту, которой повезло на этих 368 строках. С настоящими моделями происходит то же самое, только мягче: чем больше вариантов мы сравниваем на одном наборе, тем сильнее победитель завышен **на этом наборе**. Поэтому выбирают по валидации, а отчитываются по тесту, который в выборе не участвовал.

::: figure peek-coins
Двести бесполезных «монеток»: их доли угаданных на валидации разбросаны вокруг 0.5. Лучшую выбрали по валидации — на тесте она показывает обычные для монетки 0.515.
:::

::: warn
Если вы посмотрели на тест, остались недовольны и поменяли модель — тест «испорчен»: он стал валидацией. Честно в таком случае сказать в отчёте, сколько раз вы туда заглядывали, или отложить новый тест (например, данные следующего месяца).
:::

::: quiz
Аналитик перебрал 50 вариантов модели и выбрал лучший по качеству на тесте. Что не так с итоговой цифрой?

- [x] Она завышена: тест стал частью выбора, и победитель отчасти просто удачно совпал с этим тестом
  > Выбирают по валидации или кросс-валидации, а тест открывают один раз — для итоговой честной оценки.
- [ ] Ничего: тест не участвовал в обучении
  > В `fit` не участвовал, но участвовал в выборе — это тоже подгонка.
- [ ] Она занижена: 50 вариантов — слишком много
  > Многократный выбор по одной выборке завышает, а не занижает результат.
- [ ] Проблема только если вариантов больше 100
  > Чем больше вариантов, тем сильнее эффект, но он есть и при нескольких.
:::

{{practice: peek}}

## Кросс-валидация

::: figure kfold
Пять фолдов: модель обучается пять раз, и каждый раз проверяется на новой пятой части данных.
:::

У трёх частей есть минус: валидация и тест маленькие. В тесте 369 доставок, и случайность разбиения легко сдвигает оценку на 2–3 п.п. (урок «Обучающая и тестовая выборки»). Например, в нашем тесте доля опозданий 22 %, а во всех данных — 24 %: тест немного «проще» среднего.

**Кросс-валидация** (cross-validation, CV) использует данные экономнее. Строки делят на k равных частей — **фолдов** (fold, «складка»). Модель обучают k раз: каждый раз одна часть служит проверочной, остальные k − 1 — обучающими. Каждая строка ровно один раз оказывается в проверке, и получается k оценок вместо одной.

::: note Где здесь тест
Рабочий протокол такой: тест откладывают **до** всего, кросс-валидацию крутят на остальных данных — ею выбирают модель и настройки, — а на тесте один раз в конце проверяют победителя. Так устроены задачи «Итоговая таблица» и «Две настройки и отложенный тест» и проект главы. В примерах теории ниже для простоты кросс-валидируем на всех данных: так нагляднее видно, как работают фолды, а модели мы только сравниваем между собой, не обещая никому итоговую цифру.
:::

::: tip Аналогия
Новый рецепт напитка проверяют на постоянных гостях «Зерна». Гостей делят на пять групп: рецепт настраивают по отзывам четырёх, а вслепую пробует пятая — и так по кругу, пока каждая группа не побудет дегустаторами. Итог — средняя оценка пяти дегустаций, а их разброс показывает, насколько вердикт зависит от того, кто пробовал. Хромает аналогия в одном: рецепт обычно дорабатывают от круга к кругу, а модель в кросс-валидации каждый раз учится заново, с нуля.
:::

```python
from sklearn.model_selection import KFold
kf = KFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, valid_idx in kf.split(range(20)):
    print(valid_idx)
```

- `KFold(n_splits=5)` — правило нарезки на 5 фолдов;
- `shuffle=True, random_state=42` — перемешать строки перед нарезкой (воспроизводимо);
- `kf.split(X)` выдаёт пары массивов: номера строк для обучения и для проверки. Проверочную часть фолда мы называем `valid_idx` (коротко `va`): по роли это валидация, а не отложенный тест. В документации sklearn и в чужом коде её часто зовут `test_idx` — это та же проверочная часть фолда, отложенного теста она не касается.

::: predict
```python static
from sklearn.model_selection import KFold
kf = KFold(n_splits=5)
for train_idx, valid_idx in kf.split(range(10)):
    print(len(train_idx), len(valid_idx))
```

- `2 8 | 2 8 | 2 8 | 2 8 | 2 8`
- [x] `8 2 | 8 2 | 8 2 | 8 2 | 8 2`
- `8 2`

Почему: 10 строк на 5 фолдов — по 2 строки в каждом. Пять раз 2 строки идут в проверку, остальные 8 — в обучение.
:::

Сам цикл «обучить — проверить» за нас делает `cross_val_score`:

```python
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)

kf = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(DecisionTreeClassifier(max_depth=3, random_state=0), X, y, cv=kf)
print(scores.round(3))
print(f"среднее {scores.mean():.3f}, разброс (std) {scores.std():.3f}")
```

`cross_val_score(model, X, y, cv=kf)` сам обучает модель на каждом фолде и возвращает массив из 5 долей правильных ответов. Среднее — оценка качества, стандартное отклонение — насколько она дрожит от фолда к фолду. Здесь разброс — около 2 п.п.: одно разбиение могло показать и 0.83, и 0.90. Цифра 0.892 из прошлого раздела — удачный тест, а не настоящее качество дерева: честнее говорить «около 87 %».

::: deep
Можно написать просто `cv=5`. Тогда для классификации sklearn режет строки **по порядку**, без перемешивания, сохраняя долю классов в каждом фолде. Наши доставки отсортированы по времени, поэтому фолды станут периодами: это тоже осмысленная проверка («как модель работает на другом отрезке времени»), но цифры будут другими. Явный `KFold(..., shuffle=True, random_state=...)` делает нарезку понятной и одинаковой для всех моделей.
:::

### Разберём вместе: кросс-валидация на девяти строках

Девять доставок, три фолда по три строки (номера 0–8, без перемешивания):

| прогон | обучение на строках | проверка на строках | верно в проверке |
|---|---|---|---|
| 1 | 3–8 | 0, 1, 2 | 2 из 3 |
| 2 | 0–2, 6–8 | 3, 4, 5 | 3 из 3 |
| 3 | 0–5 | 6, 7, 8 | 2 из 3 |

1. Каждая строка ровно один раз побывала в проверке и дважды — в обучении.
2. Оценки по фолдам: 0.67, 1.00, 0.67. Среднее — **0.78**.
3. Разброс между фолдами (от 0.67 до 1.0) — честное напоминание, насколько оценка зависит от того, какие строки попали в проверку.

Что получилось: вместо одной оценки по трём строкам у нас среднее по всем девяти, и видно, насколько оно «дрожит». Именно разброс между фолдами потом подскажет, значима ли разница двух моделей: если модели отличаются на 0.01, а фолды гуляют на 0.05 — разницы, скорее всего, нет.

```python
from sklearn.model_selection import KFold
kf = KFold(n_splits=3)
for i, (train_idx, valid_idx) in enumerate(kf.split(range(9)), start=1):
    print(i, "обучение:", train_idx.tolist(), "проверка:", valid_idx.tolist())
```

{{practice: p-cv, folds, cv-depth, rule-cv, grid-cv}}

## Сравнение моделей

Теперь сравним всё, что построили в главе, на **одних и тех же** фолдах. Отложенного теста в этом примере нет: мы только сравниваем модели между собой (как с ним — в задаче «Итоговая таблица»). Модели sklearn оценивает `cross_val_score`. Правило «пеший — опоздает» обучать не нужно, поэтому проверим его вручную на тех же частях — циклом по `kf.split`:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

rule = ok["courier"] == "пеший"
results = {
    "всегда вовремя": [(~y.iloc[va]).mean() for tr, va in kf.split(X)],
    "правило «пеший»": [(rule.iloc[va] == y.iloc[va]).mean() for tr, va in kf.split(X)],
}
models = {
    "дерево, глубина 3": DecisionTreeClassifier(max_depth=3, random_state=0),
    "дерево без ограничений": DecisionTreeClassifier(random_state=0),
    "лес, 50 деревьев": RandomForestClassifier(n_estimators=50, random_state=0),
    "логистическая регрессия": LogisticRegression(max_iter=2000),
}
for name, model in models.items():
    results[name] = cross_val_score(model, X, y, cv=kf)

table = pd.DataFrame({name: [np.mean(s), np.std(s)] for name, s in results.items()},
                     index=["mean", "std"]).T.round(3)
table.sort_values("mean", ascending=False)
```

`y.iloc[va]` — строки по номерам из фолда (`kf.split` выдаёт номера позиций, а не метки индекса).

Что видно в итоговой таблице:

- все модели заметно лучше базовой «всегда вовремя» (0.76);
- дерево глубины 3 и логистическая регрессия (около 0.87) — на уровне правила аналитика: по сути, они его и выучили;
- дерево без ограничений хуже всех моделей (около 0.85) — переобучение видно и на кросс-валидации;
- лес — лучший (около 0.88), но обгоняет правило лишь на 1–2 п.п., а разброс между фолдами — около 2 п.п.

Честный вывод: на опозданиях машинное обучение почти ничего не добавляет к правилу аналитика. Одна причина — пеший курьер — объясняет большую часть опозданий, и её легко найти глазами. ML выигрывает там, где причин много и они переплетаются: в уроке «Регрессия: сколько минут» регрессия минут заметно обогнала медиану, а в проекте этой главы предсказать уход гостя простым правилом не получится.

::: note
Перебирать настройки кросс-валидацией — частая задача, и для неё в sklearn есть `GridSearchCV`: он сам перебирает сетку значений и запоминает лучшие. Разберём его в главе 7, а пока делаем перебор циклом — так видно, что происходит внутри.
:::

::: warn Типичные ошибки
- **Выбор и отчёт по одному набору.** Победитель на тесте завышен — как лучшая из 200 монеток.
- **Тест внутри кросс-валидации.** CV делают на обучающей части; отложенный тест — один раз в конце.
- **Разные фолды для разных моделей.** Сравнение честное, только если `KFold` один и тот же.
- **Одно число без разброса.** Среднее по фолдам без стандартного отклонения не говорит, значима ли разница.
- **Подготовка до разбиения.** Медианы, средние, доли по кофейням, посчитанные на всех данных, — утечка в CV (глава 7, урок «Pipeline: предобработка и модель вместе»).
:::

::: quiz
На одних и тех же пяти фолдах лес набрал в среднем около 0.88, правило «пеший» — около 0.87, а разброс оценок между фолдами — около 2 п.п. Какой вывод честный?

- [x] Лес, возможно, чуть лучше, но разница меньше разброса между фолдами — уверенно говорить о преимуществе нельзя
  > Разница в 1 п.п. тонет в колебаниях от фолда к фолду. Для громкого вывода она должна быть заметно больше разброса.
- [ ] Лес однозначно лучше: среднее выше
  > Среднее без разброса не говорит, значима ли разница. При другой нарезке на фолды порядок мог бы и поменяться.
- [ ] Лес бесполезен в любых задачах — правило не хуже
  > Вывод касается только опозданий, где одна причина объясняет почти всё. В регрессии минут лес заметно обогнал и медиану, и линейную модель.
- [ ] Стоит подобрать `random_state` у `KFold`, при котором лес выигрывает сильнее
  > Это подгонка нарезки под желаемый ответ — то же подглядывание, что и выбор по тесту.
:::

{{practice: table, repeat-cv}}

## Практика

## task: three-parts | Три части | warmup

`X` (признаки с `get_dummies`) и `y` (опоздание) уже готовы — как в теории. Разделите данные на три части 60/20/20:

1. `train_test_split(X, y, test_size=0.2, random_state=42)` → `X_rest`, `X_test`, `y_rest`, `y_test`;
2. `train_test_split(X_rest, y_rest, test_size=0.25, random_state=42)` → `X_train`, `X_valid`, `y_train`, `y_valid`.

### setup
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
def _ref():
    import pandas as _p
    _d = _p.read_csv('deliveries.csv', parse_dates=['created'])
    _o = _d[_d['actual_min'].between(1, 299)].copy()
    _o['hour'] = _o['created'].dt.hour
    _y = _o['actual_min'] > _o['promised_min']
    _X = _p.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
    return _o, _X, _y
```

### starter
```python
from sklearn.model_selection import train_test_split
# X и y уже готовы
```

### check
```python
from sklearn.model_selection import train_test_split as _tts
_o, _X, _y = _ref()
_Xr, _Xte, _yr, _yte = _tts(_X, _y, test_size=0.2, random_state=42)
_Xtr, _Xva, _ytr, _yva = _tts(_Xr, _yr, test_size=0.25, random_state=42)
for _nm, _w in (('X_train', _Xtr), ('X_valid', _Xva), ('X_test', _Xte), ('y_train', _ytr), ('y_valid', _yva), ('y_test', _yte)):
    _g = need(_nm)
    assert len(_g) == len(_w), f'В {_nm} {len(_g)} строк, а ожидалось {len(_w)}. Проверьте test_size в обоих вызовах.'
    assert list(_g.index) == list(_w.index), f'В {_nm} нужное число строк, но не те строки: random_state=42 в обоих вызовах, а второй вызов делит X_rest, а не X.'
```

### hint
Первый вызов делит `X, y`, второй — уже `X_rest, y_rest`.

### hint
Порядок результатов: `X_rest, X_test, y_rest, y_test = train_test_split(...)`.

### solution
```python
from sklearn.model_selection import train_test_split
X_rest, X_test, y_rest, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_valid, y_train, y_valid = train_test_split(X_rest, y_rest, test_size=0.25, random_state=42)
print(len(X_train), len(X_valid), len(X_test))
```

## task: p-cv | Кросс-валидация дерева | warmup

`X` и `y` уже готовы. Соберите программу: оценить дерево глубины 3 пятикратной кросс-валидацией и вывести среднюю долю правильных ответов (3 знака).

### setup
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
```

### parsons
```python
from sklearn.model_selection import KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
kf = KFold(n_splits=5, shuffle=True, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=0)
scores = cross_val_score(model, X, y, cv=kf)
print(round(scores.mean(), 3))
```

### check
```python
import pandas as _pd
from sklearn.model_selection import KFold as _KF, cross_val_score as _cvs
from sklearn.tree import DecisionTreeClassifier as _T
_d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
_o = _d[_d['actual_min'].between(1, 299)].copy()
_o['hour'] = _o['created'].dt.hour
_y = _o['actual_min'] > _o['promised_min']
_X = _pd.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
_w = str(round(_cvs(_T(max_depth=3, random_state=0), _X, _y, cv=_KF(n_splits=5, shuffle=True, random_state=42)).mean(), 3))
assert _lines == [_w], f'Программа вывела {_lines}, а ожидалась одна строка {_w}.'
```

### hint
Сначала правило нарезки `kf` и модель, потом `cross_val_score`, в конце — среднее.

## task: folds | Размеры фолдов | warmup

`X` уже готов. Нарежьте его `KFold(n_splits=5, shuffle=True, random_state=42)`. Сохраните в `sizes` список размеров проверочных частей (по одному числу на фолд) и в `total` — их сумму. Сравните `total` с числом строк `X`.

### setup
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
```

### starter
```python
from sklearn.model_selection import KFold
```

### check
```python
from sklearn.model_selection import KFold as _KF
_w = [len(va) for tr, va in _KF(n_splits=5, shuffle=True, random_state=42).split(range(1841))]
_s = [int(v) for v in need('sizes')]
assert len(_s) == 5, f'В sizes {len(_s)} чисел, а фолдов 5 — по одному числу на фолд.'
assert _s == _w, f'sizes = {_s}, а ожидалось {_w}. Нужны размеры проверочных частей (второй массив из kf.split).'
assert need('total') == sum(_w), f'total = {need("total")}, а должна быть сумма sizes.'
```

### hint
`for train_idx, valid_idx in kf.split(X):` — в цикле добавляйте `len(valid_idx)` в список.

### hint
`kf.split(X)` выдаёт пары массивов номеров строк — обучающих и проверочных. Каждая строка попадает в проверочную часть ровно один раз, поэтому `total` должен совпасть с `len(X)`. Размеры фолдов могут отличаться на одну строку, если число строк не делится на 5.

### solution
```python
from sklearn.model_selection import KFold
kf = KFold(n_splits=5, shuffle=True, random_state=42)
sizes = []
for train_idx, valid_idx in kf.split(X):
    sizes.append(len(valid_idx))
total = sum(sizes)
print(sizes, total, len(X))
```

### explain
Сумма размеров равна числу строк: каждая доставка ровно один раз побывала в проверке. 1841 не делится на 5 нацело, поэтому один фолд на строку больше.

## task: pick-depth | Настройка леса по валидации | base

Данные уже разделены на `X_train`, `X_valid`, `X_test` (и `y_…`) — как в первой задаче. Повторите приём из теории для другой модели и другой настройки: лес `RandomForestClassifier(n_estimators=50, min_samples_leaf=leaf, random_state=0)` для `leaf` из `[1, 5, 20, 50]`. Обучайте на обучающей части и сохраните словарь `valid_acc`: `leaf` → доля правильных на валидации. В `best_leaf` — значение с лучшей валидацией (при равенстве — меньшее). Обучите лес с этим `min_samples_leaf` на обучающей части и **один раз** посчитайте `test_acc` — долю правильных на тесте (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
X_rest, X_test, y_rest, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_valid, y_train, y_valid = train_test_split(X_rest, y_rest, test_size=0.25, random_state=42)
def _ref():
    import pandas as _p
    _d = _p.read_csv('deliveries.csv', parse_dates=['created'])
    _o = _d[_d['actual_min'].between(1, 299)].copy()
    _o['hour'] = _o['created'].dt.hour
    _y = _o['actual_min'] > _o['promised_min']
    _X = _p.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
    _Xr, _Xte, _yr, _yte = train_test_split(_X, _y, test_size=0.2, random_state=42)
    _Xtr, _Xva, _ytr, _yva = train_test_split(_Xr, _yr, test_size=0.25, random_state=42)
    return _Xtr, _Xva, _Xte, _ytr, _yva, _yte
```

### starter
```python
from sklearn.ensemble import RandomForestClassifier
# X_train, X_valid, X_test, y_train, y_valid, y_test уже готовы
valid_acc = {}
```

### check
```python
from sklearn.ensemble import RandomForestClassifier as _RF
_Xtr, _Xva, _Xte, _ytr, _yva, _yte = _ref()
_va = {_k: _RF(n_estimators=50, min_samples_leaf=_k, random_state=0).fit(_Xtr, _ytr).score(_Xva, _yva) for _k in [1, 5, 20, 50]}
_g = dict(need('valid_acc'))
assert sorted(_g) == [1, 5, 20, 50], f'Ключи valid_acc: {sorted(_g)}, а нужны значения min_samples_leaf 1, 5, 20, 50.'
for _k in _va:
    assert close(_g[_k], _va[_k], 0.0006), f'Для min_samples_leaf={_k} в valid_acc {_g[_k]}, а ожидалось около {_va[_k]:.3f}. Учите на X_train, проверяйте на X_valid; n_estimators=50, random_state=0.'
_b = max(_va, key=_va.get)
assert need('best_leaf') == _b, f'best_leaf = {need("best_leaf")}, а лучшее значение на валидации — другое. Выбирайте по valid_acc, не по тесту.'
_t = round(_RF(n_estimators=50, min_samples_leaf=_b, random_state=0).fit(_Xtr, _ytr).score(_Xte, _yte), 3)
assert close(need('test_acc'), _t), f'test_acc = {need("test_acc")}, а ожидалось {_t}: лес с лучшим min_samples_leaf, обученный на X_train, на X_test.'
```

### hint
Цикл `for leaf in [1, 5, 20, 50]:` — внутри `model = RandomForestClassifier(n_estimators=50, min_samples_leaf=leaf, random_state=0).fit(X_train, y_train)` и `valid_acc[leaf] = model.score(X_valid, y_valid)`.

### hint
`max(valid_acc, key=valid_acc.get)` вернёт первое из лучших значений — то есть меньшее, потому что словарь заполнялся по возрастанию.

### solution
```python
from sklearn.ensemble import RandomForestClassifier
valid_acc = {}
for leaf in [1, 5, 20, 50]:
    model = RandomForestClassifier(n_estimators=50, min_samples_leaf=leaf, random_state=0).fit(X_train, y_train)
    valid_acc[leaf] = model.score(X_valid, y_valid)
best_leaf = max(valid_acc, key=valid_acc.get)
final = RandomForestClassifier(n_estimators=50, min_samples_leaf=best_leaf, random_state=0).fit(X_train, y_train)
test_acc = round(final.score(X_test, y_test), 3)
print(valid_acc, best_leaf, test_acc)
```

### explain
Валидация выбрала `min_samples_leaf=5` (0.878), рядом 20 (0.872) — разница в две доставки из 368. Лес без ограничений (1) отстаёт сильнее — 0.859, а при 50 листья слишком крупные, и лес недообучается (0.834 и на валидации, и около 0.82 на обучении). На тесте выбранный лес дал 0.900. Точные цифры могут чуть отличаться между версиями sklearn — проверка считает их заново. Главное — порядок действий: перебор только по валидации, тест один раз в конце.

## task: cv-depth | Короткое и глубокое дерево | base

`X`, `y` и `kf = KFold(n_splits=5, shuffle=True, random_state=42)` уже готовы. Оцените кросс-валидацией два дерева (`random_state=0`): глубины 3 и без ограничения глубины. Сохраните средние `mean3`, `mean_full` и разбросы (std) `std3`, `std_full` — всё с 3 знаками.

### setup
```python
import pandas as pd
from sklearn.model_selection import KFold
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
```

### check
```python
import pandas as _pd
from sklearn.model_selection import KFold as _KF, cross_val_score as _cvs
from sklearn.tree import DecisionTreeClassifier as _T
_d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
_o = _d[_d['actual_min'].between(1, 299)].copy()
_o['hour'] = _o['created'].dt.hour
_y = _o['actual_min'] > _o['promised_min']
_X = _pd.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_a = _cvs(_T(max_depth=3, random_state=0), _X, _y, cv=_k)
_b = _cvs(_T(random_state=0), _X, _y, cv=_k)
assert close(need('mean3'), round(_a.mean(), 3)), f'mean3 = {need("mean3")}, а ожидалось {round(_a.mean(), 3)}. Передайте cv=kf.'
assert close(need('std3'), round(_a.std(), 3)), f'std3 = {need("std3")}, а ожидалось {round(_a.std(), 3)}.'
assert close(need('mean_full'), round(_b.mean(), 3)), f'mean_full = {need("mean_full")}, а ожидалось {round(_b.mean(), 3)}. Дерево без ограничений — без max_depth.'
assert close(need('std_full'), round(_b.std(), 3)), f'std_full = {need("std_full")}, а ожидалось {round(_b.std(), 3)}.'
```

### hint
`scores = cross_val_score(DecisionTreeClassifier(max_depth=3, random_state=0), X, y, cv=kf)`, затем `scores.mean()` и `scores.std()`.

### hint
`cross_val_score` возвращает массив из 5 долей — по одной на фолд. Среднее показывает уровень качества, `std` — насколько он прыгает от фолда к фолду. Ожидайте, что дерево без ограничения глубины проиграет по среднему: оно переобучается на каждом фолде.

### solution
```python
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
s3 = cross_val_score(DecisionTreeClassifier(max_depth=3, random_state=0), X, y, cv=kf)
sf = cross_val_score(DecisionTreeClassifier(random_state=0), X, y, cv=kf)
mean3, std3 = round(s3.mean(), 3), round(s3.std(), 3)
mean_full, std_full = round(sf.mean(), 3), round(sf.std(), 3)
print(mean3, std3, mean_full, std_full)
```

### explain
Дерево без ограничений хуже на каждом из пяти фолдов, в среднем примерно на 2 п.п. — переобучение, которое мы видели на одном разбиении в уроке «Обучающая и тестовая выборки», подтверждается и кросс-валидацией.

## task: rule-cv | Правило на тех же фолдах | base

`ok`, `y` и `kf` уже готовы. Посчитайте долю правильных ответов правила «пеший — опоздает» на каждом проверочном фолде `kf.split(X)`. Сохраните список `rule_scores` (5 чисел, 3 знака) и среднее `rule_mean` (3 знака). Так же для «всегда вовремя» — только среднее `base_mean` (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import KFold
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
import numpy as np
rule = ok["courier"] == "пеший"
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import KFold as _KF
_d = _pd.read_csv('deliveries.csv')
_o = _d[_d['actual_min'].between(1, 299)]
_y = (_o['actual_min'] > _o['promised_min']).to_numpy()
_r = (_o['courier'] == 'пеший').to_numpy()
_f = list(_KF(n_splits=5, shuffle=True, random_state=42).split(_y))
_rs = [round((_r[va] == _y[va]).mean(), 3) for tr, va in _f]
_g = [float(v) for v in need('rule_scores')]
assert len(_g) == 5, f'В rule_scores {len(_g)} чисел, а фолдов 5.'
assert all(close(a, b) for a, b in zip(_g, _rs)), f'rule_scores = {_g}, а ожидалось {_rs}. Берите строки фолда по номерам: .iloc[va].'
_m = round(_np.mean([(_r[va] == _y[va]).mean() for tr, va in _f]), 3)
assert close(need('rule_mean'), _m, 0.0011), f'rule_mean = {need("rule_mean")}, а ожидалось {_m}.'
_b = round(_np.mean([(~_y[va]).mean() for tr, va in _f]), 3)
assert close(need('base_mean'), _b, 0.0011), f'base_mean = {need("base_mean")}, а ожидалось {_b}. «Всегда вовремя» права там, где y == False.'
```

### hint
`for tr, va in kf.split(X):` — внутри `(rule.iloc[va] == y.iloc[va]).mean()`.

### hint
Для «всегда вовремя» — `(~y.iloc[va]).mean()`.

### solution
```python
import numpy as np
rule = ok["courier"] == "пеший"
rule_scores, base_scores = [], []
for tr, va in kf.split(X):
    rule_scores.append(round((rule.iloc[va] == y.iloc[va]).mean(), 3))
    base_scores.append((~y.iloc[va]).mean())
rule_mean = round(np.mean(rule_scores), 3)
base_mean = round(np.mean(base_scores), 3)
print(rule_scores, rule_mean, base_mean)
```

### explain
Правило в среднем право примерно в 86–87 % случаев — почти как дерево глубины 3 из прошлой задачи. И у правила тоже есть разброс между фолдами: от 82 до 90 %.

## task: table | Итоговая таблица с отложенным тестом | base

`X`, `y`, `ok` и `kf` уже готовы. Сделайте сравнение по рабочему протоколу:

1. Отложите тест: `train_test_split(X, y, test_size=0.2, random_state=42)` → `X_rest`, `X_test`, `y_rest`, `y_test`.
2. На фолдах `kf` по `X_rest` сравните правило и три модели:
   - `"правило"` — «пеший — опоздает»: флаг `courier_пеший` в `X_rest`;
   - `"дерево"` — `DecisionTreeClassifier(max_depth=3, random_state=0)`;
   - `"лес"` — `RandomForestClassifier(n_estimators=50, random_state=0)`;
   - `"логрегрессия"` — `LogisticRegression(max_iter=2000)`.
3. Сохраните таблицу `table`: индекс — эти названия, столбцы `mean` и `std` (3 знака), строки по убыванию `mean`. В `winner` — название лучшей строки.
4. Один раз проверьте победителя на тесте: обучите его на всём `X_rest` и сохраните долю правильных на `X_test` в `winner_test` (3 знака), а долю правила на тесте — в `rule_test` (3 знака).

### setup
```python
import pandas as pd
from sklearn.model_selection import KFold
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
```

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import KFold as _KF, cross_val_score as _cvs, train_test_split as _tts
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.linear_model import LogisticRegression as _LR
_d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
_o = _d[_d['actual_min'].between(1, 299)].copy()
_o['hour'] = _o['created'].dt.hour
_y = _o['actual_min'] > _o['promised_min']
_X = _pd.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_Xr, _Xt, _yr, _yt = _tts(_X, _y, test_size=0.2, random_state=42)
_r = _Xr['courier_пеший'] == 1
_M = {'дерево': _T(max_depth=3, random_state=0), 'лес': _RF(n_estimators=50, random_state=0), 'логрегрессия': _LR(max_iter=2000)}
_res = {'правило': [(_r.iloc[va] == _yr.iloc[va]).mean() for tr, va in _k.split(_Xr)]}
for _n, _m in _M.items():
    _res[_n] = _cvs(_m, _Xr, _yr, cv=_k)
_w = {n: (round(_np.mean(s), 3), round(_np.std(s), 3)) for n, s in _res.items()}
_t = need('table', _pd.DataFrame)
assert set(_t.index) == set(_w), f'В индексе table: {list(_t.index)}, а нужны {list(_w)}.'
assert {'mean', 'std'} <= set(_t.columns), f'Столбцы table: {list(_t.columns)}, а нужны mean и std.'
for n, (m, s) in _w.items():
    if abs(_t.loc[n, 'mean'] - m) > 0.0011:
        raise AssertionError(f'{n}: mean = {_t.loc[n, "mean"]}, а ожидалось {m}. Кросс-валидация — только на X_rest, тест отложен.')
    assert close(_t.loc[n, 'std'], s, 0.0011), f'{n}: std = {_t.loc[n, "std"]}, а ожидалось {s}.'
assert list(_t['mean']) == sorted(_t['mean'], reverse=True), 'Строки table должны идти по убыванию mean: sort_values("mean", ascending=False).'
_best = max(_w, key=lambda n: _w[n][0])
assert need('winner') == _best, f'winner = {need("winner")!r}, а лучшая строка таблицы — другая.'
_wt = round(((_Xt['courier_пеший'] == 1) == _yt).mean(), 3) if _best == 'правило' else round(_M[_best].fit(_Xr, _yr).score(_Xt, _yt), 3)
assert close(need('winner_test'), _wt), f'winner_test = {need("winner_test")}, а ожидалось {_wt}. Победителя обучают на всём X_rest и один раз проверяют на X_test.'
assert close(need('rule_test'), round(((_Xt['courier_пеший'] == 1) == _yt).mean(), 3)), f'rule_test = {need("rule_test")}. Правило на X_test.'
```

### hint
Сначала `X_rest, X_test, y_rest, y_test = train_test_split(...)`. Дальше всё, как в разделе «Сравнение моделей», только вместо `X`, `y` — `X_rest`, `y_rest`: для правила — цикл по `kf.split(X_rest)`, для моделей — `cross_val_score(..., X_rest, y_rest, cv=kf)`.

### hint
Таблица — `pd.DataFrame({name: [np.mean(s), np.std(s)] for name, s in results.items()}, index=["mean", "std"]).T.round(3)`, затем `sort_values`. Победитель — `table.index[0]`; его модель возьмите из словаря моделей, обучите на `X_rest, y_rest` и вызовите `.score(X_test, y_test)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

X_rest, X_test, y_rest, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rule = X_rest["courier_пеший"] == 1
results = {"правило": [(rule.iloc[va] == y_rest.iloc[va]).mean() for tr, va in kf.split(X_rest)]}
models = {
    "дерево": DecisionTreeClassifier(max_depth=3, random_state=0),
    "лес": RandomForestClassifier(n_estimators=50, random_state=0),
    "логрегрессия": LogisticRegression(max_iter=2000),
}
for name, model in models.items():
    results[name] = cross_val_score(model, X_rest, y_rest, cv=kf)

table = pd.DataFrame({name: [np.mean(s), np.std(s)] for name, s in results.items()},
                     index=["mean", "std"]).T.round(3)
table = table.sort_values("mean", ascending=False)
winner = table.index[0]

rule_test = round(((X_test["courier_пеший"] == 1) == y_test).mean(), 3)
if winner == "правило":
    winner_test = rule_test
else:
    winner_test = round(models[winner].fit(X_rest, y_rest).score(X_test, y_test), 3)
table
```

### explain
По кросс-валидации на `X_rest` лес впереди (0.875), но его отрыв от правила — около 1.5 п.п., примерно как разброс между фолдами. На отложенном тесте лес набрал 0.905, правило — 0.892. На тесте у обоих выше, чем по фолдам: этот тест «лёгкий» (опозданий в нём 22 % против 24 % в среднем), поэтому сравнивать лес с правилом нужно на одном и том же наборе — 0.905 против 0.892, а не 0.905 против 0.859 по фолдам. Это число и идёт в отчёт: модель выбрали, не глядя в тест, и проверили один раз. Для бизнеса вывод прежний: правило «пеший — опоздает» уже даёт почти всю пользу, а модель стоит внедрять, только если эти полтора пункта чего-то стоят.

## task: peek | Цена подглядывания | plus

`y_valid` и `y_test` уже готовы (разбиение 60/20/20 из теории). Повторите опыт с монетками, но с другим зерном: `rng = np.random.default_rng(7)`, 300 монеток. Для каждой монетки **по порядку**: сначала случайные ответы для валидации `rng.random(len(y_valid)) < 0.5`, потом для теста `rng.random(len(y_test)) < 0.5`. Сохраните:

- `best_valid` — лучшую долю правильных на валидации (3 знака);
- `its_test` — долю правильных **этой же** монетки на тесте (3 знака);
- `gap` — `best_valid − its_test` в п.п. (1 знак).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
y_rest, y_test = train_test_split(y, test_size=0.2, random_state=42)
y_train, y_valid = train_test_split(y_rest, test_size=0.25, random_state=42)
```

### starter
```python
import numpy as np
rng = np.random.default_rng(7)
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
_d = _pd.read_csv('deliveries.csv')
_o = _d[_d['actual_min'].between(1, 299)]
_y = _o['actual_min'] > _o['promised_min']
_yr, _yte = _tts(_y, test_size=0.2, random_state=42)
_ytr, _yva = _tts(_yr, test_size=0.25, random_state=42)
_g = _np.random.default_rng(7)
_va, _te = [], []
for _i in range(300):
    _va.append(((_g.random(len(_yva)) < 0.5) == _yva).mean())
    _te.append(((_g.random(len(_yte)) < 0.5) == _yte).mean())
_b = int(_np.argmax(_va))
assert close(need('best_valid'), round(_va[_b], 3)), f'best_valid = {need("best_valid")}, а ожидалось {round(_va[_b], 3)}. Проверьте зерно 7, число монеток 300 и порядок: сначала валидация, потом тест.'
assert close(need('its_test'), round(_te[_b], 3)), f'its_test = {need("its_test")}, а ожидалось {round(_te[_b], 3)}. Нужна доля на тесте той же монетки, что лучшая на валидации.'
assert close(need('gap'), round((_va[_b] - _te[_b]) * 100, 1), 0.11), f'gap = {need("gap")} п.п. Это (best_valid − its_test) · 100 по неокруглённым долям, 1 знак.'
```

### hint
Как в теории: два списка, `valid_acc` и `test_acc`, в цикле `for i in range(300)`. Лучшая — `int(np.argmax(valid_acc))`.

### hint
Порядок вызовов `rng` важен: в одной итерации сначала валидация, потом тест. Если сгенерировать сначала все 300 валидаций, а потом все тесты, числа выйдут другие. После цикла номер лучшей монетки — `int(np.argmax(valid_acc))`, а её результат на тесте — `test_acc[best]`.

### solution
```python
import numpy as np
rng = np.random.default_rng(7)
valid_acc, test_acc = [], []
for i in range(300):
    valid_acc.append(((rng.random(len(y_valid)) < 0.5) == y_valid).mean())
    test_acc.append(((rng.random(len(y_test)) < 0.5) == y_test).mean())
best = int(np.argmax(valid_acc))
best_valid = round(valid_acc[best], 3)
its_test = round(test_acc[best], 3)
gap = round((valid_acc[best] - test_acc[best]) * 100, 1)
print(best_valid, its_test, gap)
```

### explain
Победитель отбора на валидации выглядит примерно на 5–6 п.п. лучше, чем есть: это чистое везение, отобранное перебором. Именно поэтому финальную цифру берут с набора, который в отборе не участвовал.

## task: grid-cv | Две настройки и отложенный тест | plus

`X` и `y` уже готовы. Отложите тест: `train_test_split(X, y, test_size=0.2, random_state=42)` → `X_rest`, `X_test`, `y_rest`, `y_test`. Валидационную часть отдельно не выделяйте — вместо неё кросс-валидация на `X_rest` с `kf = KFold(n_splits=5, shuffle=True, random_state=42)`.

Переберите деревья `DecisionTreeClassifier(max_depth=md, min_samples_leaf=ml, random_state=0)` для `md` из `[2, 3, 4, 5, 6]` и `ml` из `[1, 20, 50]`. Сохраните:

- `cv_scores` — словарь `(md, ml)` → средняя доля правильных по фолдам;
- `best_params` — кортеж `(md, ml)` с наибольшим средним;
- `test_acc` — доля правильных на `X_test` дерева с лучшими настройками, обученного на всём `X_rest` (3 знака).

### setup
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
```

### starter
```python
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
cv_scores = {}
```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts, KFold as _KF, cross_val_score as _cvs
from sklearn.tree import DecisionTreeClassifier as _T
_d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
_o = _d[_d['actual_min'].between(1, 299)].copy()
_o['hour'] = _o['created'].dt.hour
_y = _o['actual_min'] > _o['promised_min']
_X = _pd.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
_Xr, _Xte, _yr, _yte = _tts(_X, _y, test_size=0.2, random_state=42)
_k = _KF(n_splits=5, shuffle=True, random_state=42)
_s = {(a, b): _cvs(_T(max_depth=a, min_samples_leaf=b, random_state=0), _Xr, _yr, cv=_k).mean() for a in [2, 3, 4, 5, 6] for b in [1, 20, 50]}
_g = dict(need('cv_scores'))
assert len(_g) == 15, f'В cv_scores {len(_g)} пар настроек, а нужно 5 × 3 = 15.'
for _p, _v in _s.items():
    assert _p in _g, f'В cv_scores нет ключа {_p}: ключи — кортежи (max_depth, min_samples_leaf).'
    assert close(_g[_p], _v, 0.0006), f'Для {_p} в cv_scores {_g[_p]}, а ожидалось около {_v:.3f}. Кросс-валидация — на X_rest, y_rest с cv=kf.'
_b = max(_s, key=_s.get)
assert tuple(need('best_params')) == _b, f'best_params = {need("best_params")}, а лучшие настройки по кросс-валидации — другие.'
_t = round(_T(max_depth=_b[0], min_samples_leaf=_b[1], random_state=0).fit(_Xr, _yr).score(_Xte, _yte), 3)
assert close(need('test_acc'), _t), f'test_acc = {need("test_acc")}, а ожидалось {_t}: лучшее дерево, обученное на всём X_rest, на X_test.'
```

### hint
Два вложенных цикла: `for md in [2, 3, 4, 5, 6]:` и внутри `for ml in [1, 20, 50]:`. Ключ словаря — `(md, ml)`.

### hint
Лучшие настройки — `max(cv_scores, key=cv_scores.get)`; дальше `DecisionTreeClassifier(max_depth=best_params[0], min_samples_leaf=best_params[1], random_state=0).fit(X_rest, y_rest)`.

### solution
```python
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
X_rest, X_test, y_rest, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = {}
for md in [2, 3, 4, 5, 6]:
    for ml in [1, 20, 50]:
        model = DecisionTreeClassifier(max_depth=md, min_samples_leaf=ml, random_state=0)
        cv_scores[(md, ml)] = cross_val_score(model, X_rest, y_rest, cv=kf).mean()
best_params = max(cv_scores, key=cv_scores.get)
final = DecisionTreeClassifier(max_depth=best_params[0], min_samples_leaf=best_params[1], random_state=0).fit(X_rest, y_rest)
test_acc = round(final.score(X_test, y_test), 3)
print(best_params, round(cv_scores[best_params], 3), test_acc)
```

### explain
Это самая частая схема на практике: тест отложен с самого начала, настройки выбираются кросс-валидацией на остальном, финальная модель учится на всём остатке и один раз проверяется на тесте. Ровно это в одну строку делает `GridSearchCV` из главы 7. Заметьте: все 15 вариантов дают около 86 %, разница между ними — около одного пункта — на этих данных настройки дерева почти ничего не решают.

## task: repeat-cv | Лес против правила: устойчивость | star

`X`, `y` и `ok` уже готовы. Отрыв леса от правила «пеший» — 1–2 п.п. Не случайность ли это нарезки? Повторите сравнение 10 раз, меняя только нарезку: `KFold(n_splits=5, shuffle=True, random_state=rs)` для `rs` от 0 до 9. В каждом повторе посчитайте среднюю по фолдам долю правильных у `RandomForestClassifier(n_estimators=30, random_state=0)` и у правила — на **одних и тех же** фолдах.

Сохраните `gaps` — список из 10 разниц «лес − правило» в п.п. (1 знак), `wins` — в скольких повторах лес лучше правила, и `mean_gap` — среднюю разницу (п.п., 1 знак).

### setup
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
```

### starter
```python
import numpy as np
from sklearn.model_selection import KFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
rule = ok["courier"] == "пеший"
```

### check
```python
import numpy as _np
import pandas as _pd
from sklearn.model_selection import KFold as _KF, cross_val_score as _cvs
from sklearn.ensemble import RandomForestClassifier as _RF
_d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
_o = _d[_d['actual_min'].between(1, 299)].copy()
_o['hour'] = _o['created'].dt.hour
_y = _o['actual_min'] > _o['promised_min']
_X = _pd.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
_r = _o['courier'] == 'пеший'
_raw = []
for _rs in range(10):
    _k = _KF(n_splits=5, shuffle=True, random_state=_rs)
    _f = _cvs(_RF(n_estimators=30, random_state=0), _X, _y, cv=_k).mean()
    _q = _np.mean([(_r.iloc[va] == _y.iloc[va]).mean() for tr, va in _k.split(_X)])
    _raw.append((_f - _q) * 100)
_g = [float(v) for v in need('gaps')]
assert len(_g) == 10, f'В gaps {len(_g)} чисел, а повторов 10 (random_state от 0 до 9).'
for _i, (a, b) in enumerate(zip(_g, _raw)):
    assert close(a, round(b, 1), 0.11), f'Повтор rs={_i}: разница {a} п.п., а ожидалось {b:.1f}. Лес и правило — на одних фолдах, в п.п.'
assert need('wins') == sum(v > 0 for v in _raw), f'wins = {need("wins")}: посчитайте, сколько разниц больше нуля.'
assert close(need('mean_gap'), round(_np.mean(_raw), 1), 0.11), f'mean_gap = {need("mean_gap")}, а ожидалось около {_np.mean(_raw):.1f}.'
```

### hint
Внешний цикл `for rs in range(10):`, внутри — новый `kf`, `cross_val_score` для леса и цикл по `kf.split(X)` для правила, как в задаче «Итоговая таблица».

### hint
`wins = sum(g > 0 for g in gaps)`; `mean_gap = round(np.mean(gaps), 1)`.

### solution
```python
import numpy as np
from sklearn.model_selection import KFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
rule = ok["courier"] == "пеший"
gaps = []
for rs in range(10):
    kf = KFold(n_splits=5, shuffle=True, random_state=rs)
    forest = cross_val_score(RandomForestClassifier(n_estimators=30, random_state=0), X, y, cv=kf).mean()
    by_rule = np.mean([(rule.iloc[va] == y.iloc[va]).mean() for tr, va in kf.split(X)])
    gaps.append(round((forest - by_rule) * 100, 1))
wins = sum(g > 0 for g in gaps)
mean_gap = round(np.mean(gaps), 1)
print(gaps, wins, mean_gap)
```

### explain
Лес выигрывает при любой нарезке, но всего на 1–2 п.п. Значит, преимущество настоящее, но маленькое. Кроме типа курьера, модель учитывает расстояние, погоду и размер заказа — это и даёт ей пару пунктов. Сравнение «на одних и тех же фолдах» здесь важно: оно убирает шум от того, какие доставки попали в проверку, и оставляет только разницу между подходами.
