---
title: "Бустинг: каждое дерево исправляет ошибки предыдущих"
files: [deliveries.csv]
lead: "Случайный лес строит много деревьев независимо и усредняет. Бустинг устроен иначе: деревья строятся по очереди, и каждое следующее учится на ошибках всех предыдущих. Собираем бустинг руками из маленьких деревьев, а потом сверяем с sklearn."
recap:
  - "Бустинг — сумма многих слабых моделей (обычно неглубоких деревьев), построенных последовательно."
  - "Старт — константа (среднее). Каждое следующее дерево обучается предсказывать остатки: факт − текущий прогноз."
  - "Прогноз обновляется маленьким шагом: прогноз += learning_rate × прогноз дерева. Маленький шаг + много деревьев = точнее и устойчивее."
  - "Остатки — это антиградиент MSE: бустинг — градиентный спуск, где шаг делается не по весам, а «деревьями»."
  - "В sklearn: `GradientBoostingRegressor(n_estimators, learning_rate, max_depth)`; для классификации — `GradientBoostingClassifier`."
  - "Лес снижает разброс (усредняет переобученные деревья), бустинг снижает смещение (наращивает недообученные)."
---

## Идея: учиться на ошибках

Представим аналитика, который прогнозирует время доставки. Сначала он говорит «в среднем 34 минуты» — грубо. Потом смотрит, где ошибся сильнее всего, и добавляет поправку: «пешим +15». Потом снова смотрит на ошибки — уже с поправкой — и добавляет следующую: «в снег +5». Каждая поправка простая, но вместе они дают точный прогноз.

Это и есть **бустинг** (boosting, «усиление»). Формально:

1. начальный прогноз $F_0$ — среднее $y$;
2. считаем **остатки** $r = y - F$ (на сколько ошиблись);
3. обучаем маленькое дерево предсказывать остатки;
4. обновляем прогноз: $F \leftarrow F + \eta \cdot \text{дерево}(X)$, где $\eta$ — шаг обучения (learning rate);
5. повторяем 2–4 много раз.

## Бустинг на четырёх доставках

Сначала — без компьютера. Четыре доставки, один признак «пеший курьер» (0 или 1), шаг $\eta = 0.5$:

| доставка | пеший | минут ($y$) |
|---|---|---|
| A | 0 | 20 |
| B | 0 | 24 |
| C | 1 | 38 |
| D | 1 | 42 |

**Шаг 0.** Старт — среднее: F = (20 + 24 + 38 + 42) / 4 = **31** для всех.

**Шаг 1.** Остатки $y - F$: −11, −7, +7, +11. Дерево-«пень» делит по признаку «пеший» и в каждом листе прогнозирует средний остаток: для непеших (−11 − 7) / 2 = −9, для пеших (7 + 11) / 2 = +9. Обновление: F = 31 + 0.5 · (−9) = **26.5** для A и B, 31 + 0.5 · 9 = **35.5** для C и D.

**Шаг 2.** Новые остатки: −6.5, −2.5, +2.5, +6.5. Пень снова делит по «пеший»: −4.5 и +4.5. F = 26.5 − 2.25 = **24.25** и 35.5 + 2.25 = **37.75**.

С каждым шагом прогнозы приближаются к средним групп (22 и 40), но не прыгают туда сразу: каждый раз сдвигаемся на половину оставшейся ошибки. Деревья берут на себя то, что ещё не объяснено.

::: figure boosting
Таблица из примера: каждый шаг пень учит остатки, а прогноз сдвигается на половину найденной поправки.
:::

{{practice: toy-boost}}

## Бустинг руками

Возьмём доставки со всеми признаками (как в главе 6) и сделаем 50 шагов с деревьями глубины 3:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

lr = 0.1
f_train = np.full(len(y_train), y_train.mean())     # старт — среднее
f_test = np.full(len(y_test), y_train.mean())
print("старт: MAE на тесте", round(mean_absolute_error(y_test, f_test), 2))
for k in range(1, 51):
    residual = y_train - f_train                     # на сколько ошибаемся сейчас
    tree = DecisionTreeRegressor(max_depth=3, random_state=0).fit(X_train, residual)
    f_train += lr * tree.predict(X_train)
    f_test += lr * tree.predict(X_test)
    if k in (1, 5, 10, 20, 50):
        print(f"{k} деревьев: MAE на тесте {mean_absolute_error(y_test, f_test):.2f}")
```

**Что здесь происходит:**

- `pd.get_dummies(...)` — курьер, погода и кофейня превращаются в столбцы 0/1; дерево может делить по ним.
- `f_train`, `f_test` — текущие прогнозы для обучения и теста; старт — среднее обучающих `y` (и для теста тоже — тест мы не подглядываем).
- В цикле: остатки → дерево глубины 3 на остатках → обе части прогноза сдвигаются на 0.1 прогноза дерева.
- Тестовый прогноз обновляется тем же деревом, что и обучающий: так модель применяется к новым данным.

Ошибка падает с каждым деревом: 8.3 минуты у среднего, 6.0 после десяти деревьев, 4.2 после пятидесяти. Каждое дерево глубины 3 — грубое правило из восьми листьев, но вместе они складываются в тонкую модель.

::: note
Обратите внимание: дерево обучается не на `y`, а на `residual`. Прогноз первого дерева — «на сколько среднее ошиблось для таких доставок». Прогноз десятого — «что ещё не учли первые девять».

:::

::: warn Типичные ошибки
- **Дерево учат на `y`, а не на остатках.** Тогда каждое дерево заново предсказывает время доставки целиком, и сумма «прогноз + η × прогноз» уходит вверх. Симптом — ошибка растёт с каждым деревом. В цикле на вход дерева идёт `y_train - f_train`.
- **Старт теста — среднее теста.** `np.full(len(y_test), y_test.mean())` подглядывает в ответы. Старт и для обучения, и для теста — среднее обучающих `y`.
- **Остатки пересчитали один раз до цикла.** Тогда все деревья учат одно и то же. Остатки считаются заново на каждом шаге, по текущему прогнозу.
- **Шаг 1 «чтобы быстрее».** На доставках с $\eta = 1$ ошибка на тесте падает до 4.15 уже к 12-му дереву, а дальше растёт: 4.68 к сотому. Каждое дерево целиком подгоняется под остатки конкретных строк, то есть под их шум. С $\eta = 0.1$ те же 100 деревьев дают 3.83.
:::

{{practice: residuals, one-step, p-boost, manual-boost}}

## Зачем маленький шаг

Можно было бы прибавлять прогноз дерева целиком ($\eta = 1$): тогда первое же дерево исправило бы почти всё, что может. Но каждое дерево обучено на конкретных строках и немного переобучено; маленький шаг «доверяет» ему лишь на 10 %, а остальное оставляет следующим деревьям. Это то же правило, что в градиентном спуске: маленький шаг и много шагов надёжнее одного большого.

Цена — нужно больше деревьев. Шаг обучения и число деревьев всегда подбирают вместе: уменьшили $\eta$ вдвое — деревьев нужно примерно вдвое больше.

::: figure boost-curve
Ручной бустинг из раздела выше, продлённый до 100 деревьев, с двумя шагами. При η = 0.05 кривая идёт медленнее и к 100 деревьям приходит туда же, куда η = 0.1 пришёл за 50.
:::

::: quiz
Шаг бустинга уменьшили с 0.1 до 0.05, а число деревьев оставили прежним — 50. Чего ждать на тесте?

- [x] Ошибка, скорее всего, вырастет: каждое дерево теперь вносит вдвое меньшую поправку, и 50 деревьев не успевают дойти до прежнего результата
  > Шаг и число деревьев подбирают вместе: уменьшили шаг вдвое — деревьев нужно примерно вдвое больше.
- [ ] Ошибка уменьшится: маленький шаг всегда надёжнее
  > Маленький шаг надёжнее при достаточном числе деревьев. Без них модель просто недоучена.
- [ ] Ничего не изменится: деревья те же, меняется только множитель
  > Деревья как раз будут другими: каждое учится на остатках, а остатки зависят от того, сколько исправили предыдущие.
- [ ] Модель сильнее переобучится
  > Переобучению способствуют, наоборот, большой шаг и слишком много деревьев. С маленьким шагом и тем же числом деревьев модель скорее недообучена.
:::

{{practice: lr-trees}}

## Почему «градиентный»

В уроке «Градиентный спуск: шаг за шагом к минимуму» мы брали производную потери по весу $w$. Здесь возьмём её по самому **прогнозу** $F$ — как будто прогноз каждой строки и есть вес, который можно двигать.

Одна доставка: факт $y = 40$, прогноз $F = 31$. Потеря $(40 - 31)^2 = 81$. Сдвинем прогноз на 1 вверх: $(40 - 32)^2 = 64$ — потеря упала на 17, почти на $2 \cdot 9 = 18$. Производная потери $(y - F)^2$ по $F$ равна $-2 \cdot (y - F) = -18$. Шаг против неё — вверх, в сторону остатка $y - F = +9$.

Значит, для MSE остаток $y - F$ — это (с точностью до множителя 2) производная потери по прогнозу со знаком минус. Бустинг делает тот же градиентный спуск, только шаг делается не по весам, а по прогнозам: «сдвинь прогноз каждой строки против градиента». Дерево нужно, чтобы этот сдвиг можно было применить к новым строкам, которых не было в обучении.

Если потеря другая (MAE, логистическая для классификации), меняется только формула «остатка» — антиградиента. Поэтому метод и называется **градиентным бустингом**.

::: tip Аналогия
Бариста каждое утро пробует эспрессо и смотрит, куда ушёл вкус: кислит — помол мельче, горчит — крупнее. Он не ищет идеальную настройку заново, а подкручивает текущую на небольшую долю в сторону, противоположную ошибке. Остатки в бустинге — это и есть «куда и насколько ушёл вкус» у каждой строки. Хромает аналогия в одном: у бариста одна ручка на все чашки, а дерево делает разные поправки для разных групп строк — пешим одну, дальним заказам другую.
:::

::: predict
```python static
import numpy as np
y = np.array([30.0, 40.0, 50.0])
f = np.full(3, y.mean())
print((y - f).tolist())
```

- `[30.0, 40.0, 50.0]`
- [x] `[-10.0, 0.0, 10.0]`
- `[0.0, 0.0, 0.0]`

Почему: старт — среднее 40, остатки — отклонения от него. Первое дерево будет учиться предсказывать именно их.
:::

{{practice: mae-boost}}

## То же в sklearn

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

for n in (50, 300):
    gb = GradientBoostingRegressor(n_estimators=n, learning_rate=0.1, max_depth=3, random_state=0).fit(X_train, y_train)
    print(f"бустинг, {n} деревьев: MAE {mean_absolute_error(y_test, gb.predict(X_test)):.2f}")
rf = RandomForestRegressor(n_estimators=100, random_state=0).fit(X_train, y_train)
print(f"случайный лес: MAE {mean_absolute_error(y_test, rf.predict(X_test)):.2f}")
```

**Что здесь происходит:**

- `GradientBoostingRegressor(n_estimators=n, learning_rate=0.1, max_depth=3)` — ровно наш цикл: n деревьев глубины 3, шаг 0.1, старт — среднее.
- Для сравнения — случайный лес из 100 деревьев с настройками по умолчанию.

50 деревьев sklearn дают ту же ошибку, что наш ручной бустинг (около 4.2) — внутри та же схема. 300 деревьев — около 3.8 минуты, заметно лучше леса (около 4.6). На табличных данных градиентный бустинг чаще всего и оказывается лучшей моделью.

{{practice: vs-sklearn}}

## Лес и бустинг: в чём разница

| | случайный лес | градиентный бустинг |
|---|---|---|
| деревья строятся | независимо, параллельно | по очереди, каждое — на ошибках предыдущих |
| деревья | глубокие, переобученные | неглубокие (глубина 3–8), недообученные |
| что снижает | разброс (усреднение) | смещение (наращивание) |
| много деревьев | не вредит | может переобучить — нужна ранняя остановка |
| настройка | почти работает «из коробки» | важны learning_rate, число деревьев, глубина |

::: figure forest-vs-boost
Слева деревья леса учатся независимо, каждое на своей выборке, и прогнозы усредняются. Справа деревья бустинга идут цепочкой: каждое учит остатки текущего прогноза F, и F сдвигается на η × прогноз дерева.
:::

::: quiz
В чём главная разница между лесом и бустингом?

- [x] Деревья леса строятся независимо и усредняются, а деревья бустинга — по очереди, и каждое исправляет ошибки предыдущих
  > Лес уменьшает разброс за счёт усреднения. Бустинг уменьшает смещение, постепенно доучивая то, что не объяснено.
- [ ] В лесу деревья глубже — больше ничем
  > Глубина разная, но суть — в независимости против последовательности.
- [ ] Бустинг не использует деревья
  > Использует, обычно неглубокие.
- [ ] Лес работает только для классификации
  > Есть и `RandomForestRegressor`, и классификаторы-бустинги.
:::

{{practice: depth-one}}

## Разберём вместе: на что опирается бустинг

У бустинга, как у леса, есть `feature_importances_` — сколько каждый признак суммарно уменьшил ошибку во всех деревьях. Посмотрим, что важно для времени доставки:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

gb = GradientBoostingRegressor(n_estimators=300, learning_rate=0.1, max_depth=3, random_state=0).fit(X_train, y_train)
imp = pd.Series(gb.feature_importances_, index=X.columns).sort_values(ascending=False)
print(imp.head(6).round(3))
print("сумма важностей:", round(imp.sum(), 3))
```

**Что здесь происходит:**

- `feature_importances_` — доля вклада каждого столбца, в сумме 1.
- `pd.Series(..., index=X.columns)` — подписываем важности именами столбцов и сортируем.

**Что получилось:** половина важности — у расстояния, почти четверть — у пешего курьера, дальше час заказа и число позиций. Это совпадает со здравым смыслом и с весами линейной модели из урока «Спуск для многих признаков» — хороший знак, что модель учит закономерности, а не шум. Помните ограничение из главы 8: важность показывает, на что модель **опирается**, а не что на самом деле **влияет** на время доставки.

## Практика

## task: toy-boost | Бустинг на бумаге | warmup

Повторите пример с четырьмя доставками кодом, но с шагом η = 0.3 и тремя шагами. «Пень» здесь — просто средний остаток в каждой группе по признаку `walk`. Сохраните `history` — список прогнозов после каждого шага (каждый прогноз — список из 4 чисел, 2 знака), начиная со старта (всего 4 списка), и `gap_left` — сколько минут ещё не хватает группе пеших до их среднего (40) после трёх шагов (2 знака).

### setup
```python
import numpy as np
walk = np.array([0, 0, 1, 1])
y = np.array([20.0, 24.0, 38.0, 42.0])
```

### starter
```python
import numpy as np

lr = 0.3
f = np.full(4, y.mean())
history = [f.round(2).tolist()]

```

### check
```python
import numpy as _np
w0, y0 = need('walk'), need('y')
f = _np.full(4, y0.mean()); h = [f.round(2).tolist()]
for _ in range(3):
    r = y0 - f; step = _np.where(w0 == 1, r[w0 == 1].mean(), r[w0 == 0].mean()); f = f + 0.3 * step; h.append(f.round(2).tolist())
g = need('history', list)
assert len(g) == 4, 'history — старт и три шага: 4 списка.'
assert all(_np.allclose(a, b, atol=0.006) for a, b in zip(g, h)), f'history = {g}, а нужно {h}.'
assert close(need('gap_left'), round(40 - f[2], 2), 0.006), f'gap_left = {need("gap_left")}.'
```

### hint
Прогноз «пня» для каждой доставки — средний остаток её группы: `np.where(walk == 1, r[walk == 1].mean(), r[walk == 0].mean())`.

### hint
В цикле на 3 шага: остатки `r = y - f`, прогноз пня, `f = f + lr * пень`, добавить `f.round(2).tolist()` в историю.

### solution
```python
import numpy as np

lr = 0.3
f = np.full(4, y.mean())
history = [f.round(2).tolist()]
for _ in range(3):
    r = y - f
    stump = np.where(walk == 1, r[walk == 1].mean(), r[walk == 0].mean())
    f = f + lr * stump
    history.append(f.round(2).tolist())
gap_left = round(40 - f[2], 2)
print(history, gap_left)
```

### explain
Каждый шаг закрывает 30 % оставшегося разрыва: от 9 минут (31 → 40) остаётся 9 · 0.7³ ≈ 3.1. С шагом 0.3 разрыв убывает в геометрической прогрессии и никогда не закрывается полностью за конечное число шагов — но на настоящих данных это и не нужно: «закрыть до конца» означало бы подогнать модель под шум обучающих строк.

## task: residuals | Остатки | warmup

Прогноз `f` — пока просто среднее `y`. Сохраните остатки `r = y - f` и `mae0` — среднюю абсолютную ошибку такого прогноза.

### starter
```python
import numpy as np
y = np.array([22.0, 35.0, 41.0, 28.0, 54.0])

```

### check
```python
import numpy as _np
y0 = _np.array([22.0, 35.0, 41.0, 28.0, 54.0])
assert _np.allclose(need('r'), y0 - y0.mean()), f'r = {need("r")}.'
assert close(need('mae0'), _np.abs(y0 - y0.mean()).mean()), f'mae0 = {need("mae0")}.'
```

### hint
Начальный прогноз одинаков для всех строк — среднее; остатки — факт минус прогноз.

### hint
`f = np.full(len(y), y.mean())`, `r = y - f`, `mae0 = np.abs(r).mean()`.

### solution
```python
import numpy as np
y = np.array([22.0, 35.0, 41.0, 28.0, 54.0])
f = np.full(len(y), y.mean())
r = y - f
mae0 = np.abs(r).mean()
```

## task: one-step | Один шаг бустинга | warmup

Сделайте один шаг бустинга руками: «дерево» уже обучено и предсказывает поправки `tree_pred`. Обновите прогноз `f` с шагом 0.1 и сохраните новый прогноз `f1` и его MAE `mae1`.

### starter
```python
import numpy as np
y = np.array([22.0, 35.0, 41.0, 28.0, 54.0])
f = np.full(5, y.mean())
tree_pred = np.array([-12.0, -2.0, 4.0, -8.0, 16.0])

```

### check
```python
import numpy as _np
y0 = _np.array([22.0, 35.0, 41.0, 28.0, 54.0]); f0 = _np.full(5, y0.mean()) + 0.1 * _np.array([-12.0, -2.0, 4.0, -8.0, 16.0])
assert _np.allclose(need('f1'), f0), f'f1 = {need("f1")}, а нужно {f0}.'
assert close(need('mae1'), _np.abs(y0 - f0).mean()), f'mae1 = {need("mae1")}.'
```

### hint
Новый прогноз — старый плюс шаг × поправка дерева.

### hint
`f1 = f + 0.1 * tree_pred`.

### solution
```python
import numpy as np
y = np.array([22.0, 35.0, 41.0, 28.0, 54.0])
f = np.full(5, y.mean())
tree_pred = np.array([-12.0, -2.0, 4.0, -8.0, 16.0])
f1 = f + 0.1 * tree_pred
mae1 = np.abs(y - f1).mean()
```

## task: p-boost | Цикл бустинга | warmup

Соберите цикл бустинга из пяти шагов.

### parsons
```python
import numpy as np
from sklearn.tree import DecisionTreeRegressor
X = np.array([[1], [2], [3], [4], [5], [6]])
y = np.array([10.0, 12.0, 20.0, 22.0, 40.0, 42.0])
f = np.full(len(y), y.mean())
for _ in range(5):
    tree = DecisionTreeRegressor(max_depth=1).fit(X, y - f)
    f = f + 0.5 * tree.predict(X)
print(round(float(np.abs(y - f).mean()), 2))
```

### check
```python
import numpy as _np
from sklearn.tree import DecisionTreeRegressor as _T
X0 = _np.array([[1], [2], [3], [4], [5], [6]]); y0 = _np.array([10.0, 12.0, 20.0, 22.0, 40.0, 42.0]); f0 = _np.full(6, y0.mean())
for _ in range(5): f0 = f0 + 0.5 * _T(max_depth=1).fit(X0, y0 - f0).predict(X0)
assert _lines == [str(round(float(_np.abs(y0 - f0).mean()), 2))], f'Сейчас: {_lines}.'
```

### hint
Дерево учится на остатках `y - f`, и только потом прогноз обновляется.

### hint
Порядок внутри цикла: остатки → дерево → обновление прогноза.

## task: manual-boost | Бустинг руками | base

Напишите функцию `boost(X_tr, y_tr, X_te, n, lr, depth)`, которая делает `n` шагов бустинга с деревьями `DecisionTreeRegressor(max_depth=depth, random_state=0)` и возвращает прогноз для `X_te`. Посчитайте MAE на тесте для `(n=30, lr=0.1, depth=3)` и `(n=30, lr=0.3, depth=3)` и сохраните `mae_01`, `mae_03` (2 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeRegressor as _T
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
def _b(lr):
    ft = _np.full(len(c), c.mean()); fe = _np.full(len(dd), c.mean())
    for _ in range(30):
        t = _T(max_depth=3, random_state=0).fit(a, c - ft); ft += lr * t.predict(a); fe += lr * t.predict(b)
    return round(_mae(dd, fe), 2)
assert close(need('mae_01'), _b(0.1), 0.011), f'mae_01 = {need("mae_01")}, а нужно {_b(0.1)}.'
assert close(need('mae_03'), _b(0.3), 0.011), f'mae_03 = {need("mae_03")}, а нужно {_b(0.3)}.'
```

### hint
Старт — среднее `y_tr` и для обучения, и для теста. В цикле дерево учится на `y_tr − f_tr`, а обновляются оба прогноза одним и тем же деревом. Вернуть нужно прогноз для `X_te`.

### hint
Скопируйте цикл из теории в функцию: два прогноза (`f_train`, `f_test`), старт — среднее `y_tr`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

def boost(X_tr, y_tr, X_te, n, lr, depth):
    f_tr = np.full(len(y_tr), y_tr.mean())
    f_te = np.full(len(X_te), y_tr.mean())
    for _ in range(n):
        tree = DecisionTreeRegressor(max_depth=depth, random_state=0).fit(X_tr, y_tr - f_tr)
        f_tr = f_tr + lr * tree.predict(X_tr)
        f_te = f_te + lr * tree.predict(X_te)
    return f_te

mae_01 = round(mean_absolute_error(y_test, boost(X_train, y_train, X_test, 30, 0.1, 3)), 2)
mae_03 = round(mean_absolute_error(y_test, boost(X_train, y_train, X_test, 30, 0.3, 3)), 2)
```

### explain
При 30 деревьях больший шаг выигрывает: с шагом 0.1 модель ещё не успела «дойти». Но при большом числе деревьев маленький шаг обычно догоняет и обгоняет — это видно в следующем уроке.

## task: vs-sklearn | Сверка с sklearn | base

Сравните ваш `boost` (50 деревьев, шаг 0.1, глубина 3) с `GradientBoostingRegressor(n_estimators=50, learning_rate=0.1, max_depth=3, random_state=0)`. Сохраните `mae_mine`, `mae_sk` (2 знака) и `corr` — корреляцию прогнозов двух моделей на тесте (4 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

def boost(X_tr, y_tr, X_te, n, lr, depth):
    f_tr = np.full(len(y_tr), y_tr.mean())
    f_te = np.full(len(X_te), y_tr.mean())
    for _ in range(n):
        tree = DecisionTreeRegressor(max_depth=depth, random_state=0).fit(X_tr, y_tr - f_tr)
        f_tr = f_tr + lr * tree.predict(X_tr)
        f_te = f_te + lr * tree.predict(X_te)
    return f_te

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeRegressor as _T
from sklearn.ensemble import GradientBoostingRegressor as _GB
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
ft = _np.full(len(c), c.mean()); fe = _np.full(len(dd), c.mean())
for _ in range(50):
    t = _T(max_depth=3, random_state=0).fit(a, c - ft); ft += 0.1 * t.predict(a); fe += 0.1 * t.predict(b)
ps = _GB(n_estimators=50, learning_rate=0.1, max_depth=3, random_state=0).fit(a, c).predict(b)
assert close(need('mae_mine'), round(_mae(dd, fe), 2), 0.011), f'mae_mine = {need("mae_mine")}.'
assert close(need('mae_sk'), round(_mae(dd, ps), 2), 0.011), f'mae_sk = {need("mae_sk")}.'
assert close(need('corr'), round(_np.corrcoef(fe, ps)[0, 1], 4), 0.0011), f'corr = {need("corr")}.'
```

### hint
Обучите `GradientBoostingRegressor` с теми же параметрами, что ручной бустинг: число деревьев, шаг, глубина, `random_state=0`.

### hint
Корреляция двух массивов: `np.corrcoef(a, b)[0, 1]`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

def boost(X_tr, y_tr, X_te, n, lr, depth):
    f_tr = np.full(len(y_tr), y_tr.mean())
    f_te = np.full(len(X_te), y_tr.mean())
    for _ in range(n):
        tree = DecisionTreeRegressor(max_depth=depth, random_state=0).fit(X_tr, y_tr - f_tr)
        f_tr = f_tr + lr * tree.predict(X_tr)
        f_te = f_te + lr * tree.predict(X_te)
    return f_te

mine = boost(X_train, y_train, X_test, 50, 0.1, 3)
sk = GradientBoostingRegressor(n_estimators=50, learning_rate=0.1, max_depth=3, random_state=0).fit(X_train, y_train).predict(X_test)
mae_mine = round(mean_absolute_error(y_test, mine), 2)
mae_sk = round(mean_absolute_error(y_test, sk), 2)
corr = round(np.corrcoef(mine, sk)[0, 1], 4)
```

### explain
Прогнозы почти совпадают (корреляция около 1): `GradientBoostingRegressor` с потерей MSE делает ровно то же, что наш цикл. Отличия — в мелочах вроде того, как дерево выбирает разбиение при равенстве.

## task: depth-one | Пни против деревьев | plus

Сравните бустинг из «пней» (деревьев глубины 1) и из деревьев глубины 4: `GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=d, random_state=0)` для `d` = 1 и 4. Сохраните `mae_stumps`, `mae_deep` (2 знака) и `winner` — `"пни"` или `"глубина 4"`.

### starter
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.ensemble import GradientBoostingRegressor as _GB
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
m = {k: round(_mae(dd, _GB(n_estimators=200, learning_rate=0.1, max_depth=k, random_state=0).fit(a, c).predict(b)), 2) for k in (1, 4)}
assert close(need('mae_stumps'), m[1], 0.011) and close(need('mae_deep'), m[4], 0.011), f'mae_stumps, mae_deep = {need("mae_stumps")}, {need("mae_deep")}, а нужно {m[1]}, {m[4]}.'
assert need('winner') == ('пни' if m[1] < m[4] else 'глубина 4'), f'winner = {need("winner")!r}.'
```

### hint
Два вызова с разным `max_depth`.

### hint
Пень — дерево глубины 1: один вопрос и два листа. Ему нужно больше деревьев, чтобы описать то же, что дереву глубины 4.

### solution
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

res = {}
for depth in (1, 4):
    gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=depth, random_state=0).fit(X_train, y_train)
    res[depth] = round(mean_absolute_error(y_test, gb.predict(X_test)), 2)
mae_stumps, mae_deep = res[1], res[4]
winner = "пни" if mae_stumps < mae_deep else "глубина 4"
```

### explain
Пень задаёт один вопрос и не может уловить **взаимодействие** признаков («пеший **и** снег», «авто **и** час пик»): сумма пней — это сумма отдельных эффектов признаков. Деревья глубины 4 видят сочетания, а на доставках они важны. Глубина дерева в бустинге — это «насколько сложные сочетания признаков модель может выучить».

## task: lr-trees | Шаг и число деревьев | base

Проверьте правило «уменьшили шаг вдвое — деревьев нужно вдвое больше». Обучите `GradientBoostingRegressor(max_depth=3, random_state=0)` на доставках (данные и разбиение — в заготовке) для пар `(learning_rate, n_estimators)`: `(0.3, 100)`, `(0.1, 300)`, `(0.05, 600)` и `(0.02, 300)`. Сохраните `mae` — словарь `{"0.3x100": …, "0.1x300": …, "0.05x600": …, "0.02x300": …}` (MAE на тесте, 3 знака) и `undertrained` — ключ пары, которая заметно хуже остальных (больше чем на 0.1 минуты от лучшей).

### setup
```python
import pandas as pd
from sklearn.model_selection import train_test_split
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
```

### starter
```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

pairs = [(0.3, 100), (0.1, 300), (0.05, 600), (0.02, 300)]
mae = {}

```

### check
```python
from sklearn.ensemble import GradientBoostingRegressor as _G
from sklearn.metrics import mean_absolute_error as _mae
a, b, c, d_ = need('X_train'), need('X_test'), need('y_train'), need('y_test')
w = {f'{lr}x{n}': round(_mae(d_, _G(n_estimators=n, learning_rate=lr, max_depth=3, random_state=0).fit(a, c).predict(b)), 3) for lr, n in [(0.3, 100), (0.1, 300), (0.05, 600), (0.02, 300)]}
g = need('mae', dict)
assert set(g) == set(w), f'Ключи mae: {sorted(g)}, а нужно {sorted(w)}.'
assert all(close(g[k], w[k], 0.002) for k in w), f'mae = {g}, а нужно {w}.'
best = min(w.values())
assert need('undertrained') == [k for k in w if w[k] > best + 0.1][0], f'undertrained = {need("undertrained")!r}.'
```

### hint
Ключ из пары: `f"{lr}x{n}"` — например, `"0.1x300"`.

### hint
Цикл по `pairs`: обучить, предсказать тест, `mean_absolute_error`, округлить. «Недоученная» — та, у которой MAE больше лучшей более чем на 0.1.

### solution
```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

pairs = [(0.3, 100), (0.1, 300), (0.05, 600), (0.02, 300)]
mae = {}
for lr, n in pairs:
    gb = GradientBoostingRegressor(n_estimators=n, learning_rate=lr, max_depth=3, random_state=0).fit(X_train, y_train)
    mae[f"{lr}x{n}"] = round(mean_absolute_error(y_test, gb.predict(X_test)), 3)
best = min(mae.values())
undertrained = [k for k in mae if mae[k] > best + 0.1][0]
print(mae, undertrained)
```

### explain
Пары с одинаковым «шаг × число деревьев» (0.1 × 300 и 0.05 × 600) дают почти одинаковую ошибку — около 3.83. Большой шаг с малым числом деревьев (0.3 × 100) чуть хуже, а маленький шаг без добавки деревьев (0.02 × 300) заметно недоучен — около 4.12. Правило практики: зафиксировать умеренный шаг (0.05–0.1) и подбирать число деревьев ранней остановкой (урок «Настройка бустинга»), а не наоборот.

## task: mae-boost | Бустинг по MAE | star

Сделайте ручной бустинг по **MAE**: «остаток» для MAE — знак ошибки `np.sign(y - f)`, а не сама ошибка. Старт — **медиана** `y_train`, 100 деревьев глубины 3 (`random_state=0`), шаг 1.0 — прогноз дерева (средний знак в листе, от −1 до 1) прибавляется целиком. Сохраните `mae_l1` — MAE на тесте (2 знака) и `mae_l2` — MAE бустинга по MSE из `GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=0)` (2 знака).

### starter
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.model_selection import train_test_split as _tts
from sklearn.tree import DecisionTreeRegressor as _T
from sklearn.ensemble import GradientBoostingRegressor as _GB
from sklearn.metrics import mean_absolute_error as _mae
d = _pd.read_csv('deliveries.csv', parse_dates=['created']); ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X0 = _pd.get_dummies(ok[['distance_km', 'items', 'hour', 'courier', 'weather', 'shop_id']], dtype=int); y0 = ok['actual_min']
a, b, c, dd = _tts(X0, y0, test_size=0.25, random_state=42)
ft = _np.full(len(c), c.median()); fe = _np.full(len(dd), c.median())
for _ in range(100):
    t = _T(max_depth=3, random_state=0).fit(a, _np.sign(c - ft)); ft += t.predict(a); fe += t.predict(b)
w1 = round(_mae(dd, fe), 2)
w2 = round(_mae(dd, _GB(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=0).fit(a, c).predict(b)), 2)
assert close(need('mae_l1'), w1, 0.011), f'mae_l1 = {need("mae_l1")}, а нужно {w1}.'
assert close(need('mae_l2'), w2, 0.011), f'mae_l2 = {need("mae_l2")}, а нужно {w2}.'
```

### hint
Для MAE антиградиент — знак остатка: +1, если прогноз занижен, −1 — если завышен.

### hint
Та же схема, что в задаче «Бустинг руками», но `fit(X_train, np.sign(y_train - f_train))` и старт `y_train.median()`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = pd.get_dummies(ok[["distance_km", "items", "hour", "courier", "weather", "shop_id"]], dtype=int)
y = ok["actual_min"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

f_tr = np.full(len(y_train), y_train.median())
f_te = np.full(len(y_test), y_train.median())
for _ in range(100):
    tree = DecisionTreeRegressor(max_depth=3, random_state=0).fit(X_train, np.sign(y_train - f_tr))
    f_tr = f_tr + tree.predict(X_train)
    f_te = f_te + tree.predict(X_test)
mae_l1 = round(mean_absolute_error(y_test, f_te), 2)
gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=0).fit(X_train, y_train)
mae_l2 = round(mean_absolute_error(y_test, gb.predict(X_test)), 2)
```

### explain
Бустинг по MAE шагает «по знаку» — не больше чем на минуту за дерево, — но за 100 деревьев приходит к той же точности, что бустинг по MSE (около 3.8 минуты). Разница в другом: по MAE модель почти не реагирует на выбросы, а мы их заранее отфильтровали; на сырых данных с «забытыми» заказами на 1000 минут бустинг по MSE пострадал бы сильнее. В sklearn такой бустинг включается параметром `loss="absolute_error"`, и там шаг в листе подбирается точнее — медианой остатков.
