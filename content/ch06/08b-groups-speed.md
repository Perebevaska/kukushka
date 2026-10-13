---
title: "Групповое разбиение и цена модели"
lead: "Две проверки, без которых сравнение моделей нечестно. Если один гость встречается во многих строках, модель может запомнить его, а не выучить закономерность, — и обычная кросс-валидация этого не заметит. А если лучшая модель учится в сто раз дольше, это тоже часть её цены."
files: [guest_orders.csv, deliveries.csv]
recap:
  - "Если объект повторяется в строках (гость, кофейня, курьер), а модель будут применять к новым таким объектам, — групповое разбиение: `GroupKFold(5)` с `groups=` в `cross_val_score`, `GroupShuffleSplit` для одного теста. Обычное разбиение тогда завышает оценку за счёт «памяти» об объектах."
  - "Время обучения и предсказания: `t0 = time.perf_counter()` до и разница после; в Jupyter — `%%time` и `%timeit`. Сравнивайте модели на одной машине."
---

## Групповое разбиение: один гость — в одной части

**Зачем.** Приложение «Зерна» хочет предлагать десерт к заказу тем, кто, скорее всего, его возьмёт. Модель будут показывать **всем** гостям, в том числе новым, которых она никогда не видела. Значит, честная проверка отвечает на вопрос «как модель работает на незнакомом госте». Обычное разбиение на это не отвечает: заказы одного гостя попадают и в обучение, и в проверку, и модель «узнаёт» гостя.

В файле `guest_orders.csv` — 2 332 заказа 240 гостей, у каждого от 3 до 19 заказов. Столбец `dessert` — взял ли гость десерт (1 или 0), признаки — день недели, час, число позиций, сумма и расстояние доставки. У каждого гостя свой адрес, поэтому `distance_km` (с точностью до 10 метров) почти однозначно указывает на гостя — модель может запомнить «гость с 3.47 км любит десерты» вместо общих закономерностей.

::: tip Аналогия
Учитель готовит класс к экзамену и проверяет себя пробником. Если в пробник попали те же задачи, что разбирали на уроке, — только с переставленными словами, — результат завышен: ученики помнят ответы, а не умеют решать. Честный пробник — из задач, которых класс не видел. Гость с его привычками — такая «задача»: его заказы должны целиком оказаться либо на уроке, либо на пробнике.
:::

### Игрушечный пример: три гостя, десять заказов

Гость A сделал 4 заказа, B и C — по 3. Нарежем три фолда двумя способами и посмотрим, чьи заказы попадают в проверку:

```python
import pandas as pd
from sklearn.model_selection import KFold, GroupKFold

toy = pd.DataFrame({"guest": list("AAAABBBCCC")})
print("KFold — строки вперемешку:")
for tr, te in KFold(3, shuffle=True, random_state=0).split(toy):
    print("  проверка:", "".join(toy["guest"].iloc[te]), "| обучение:", "".join(toy["guest"].iloc[tr]))
print("GroupKFold — гость целиком:")
for tr, te in GroupKFold(3).split(toy, groups=toy["guest"]):
    print("  проверка:", "".join(toy["guest"].iloc[te]), "| обучение:", "".join(toy["guest"].iloc[tr]))
```

Что здесь происходит:

- `KFold` режет **строки**: в первом фолде проверяются заказы A, B, C, C, а в обучении остались другие заказы тех же A, B и C;
- `GroupKFold(3)` режет **группы**: аргумент `groups=` говорит, какой строке какой гость соответствует, и все заказы гостя уходят в один фолд;
- в групповом варианте проверка «AAAA» означает: модель учится только на B и C и проверяется на госте, которого не видела.

Как читать результат: при `KFold` ни в одном фолде нет «незнакомого» гостя; при `GroupKFold` в каждом фолде проверяется ровно тот случай, ради которого модель делают, — новый гость.

::: figure group-folds
Тот же игрушечный пример: `KFold` режет строки, и в каждой проверке гости уже знакомы модели по обучению. `GroupKFold` отправляет все заказы гостя в один фолд — проверка идёт на незнакомом госте.
:::

### На реальных данных: метрика при двух разбиениях

```python
import pandas as pd
from sklearn.model_selection import KFold, GroupKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

o = pd.read_csv("guest_orders.csv")
X = o[["weekday", "hour", "items", "amount", "distance_km"]]
y = o["dessert"]
groups = o["guest_id"]
print(f"заказов {len(o)}, гостей {groups.nunique()}, «всегда да» права в {y.mean():.3f}")

models = {
    "дерево без ограничений": DecisionTreeClassifier(random_state=0),
    "лес, 50 деревьев": RandomForestClassifier(n_estimators=50, random_state=0),
    "логистическая регрессия": LogisticRegression(max_iter=2000),
}
rows = {}
for name, model in models.items():
    plain = cross_val_score(model, X, y, cv=KFold(5, shuffle=True, random_state=42))
    group = cross_val_score(model, X, y, cv=GroupKFold(5), groups=groups)
    rows[name] = [plain.mean(), group.mean(), plain.mean() - group.mean()]
pd.DataFrame(rows, index=["KFold", "GroupKFold", "разница"]).T.round(3)
```

Что здесь происходит:

- `groups = o["guest_id"]` — столбец групп: по одному значению на строку, той же длины, что `X` и `y`;
- `cross_val_score(..., cv=GroupKFold(5), groups=groups)` — та же кросс-валидация, но фолды режутся по гостям; `groups=` передаётся в `cross_val_score`, а он отдаёт его разбиению;
- `rows[name]` — среднее по фолдам при обычном и групповом разбиении и их разница.

Как читать результат: при обычном разбиении лучше всех выглядят дерево и лес — около 0.59 против 0.507 у «всегда да». При групповом их качество падает почти до базового (дерево и лес — около 0.51; точные цифры немного зависят от версии sklearn): то, что они «умели», было памятью о конкретных гостях. Логистическая регрессия не умеет запоминать отдельные адреса и почти не теряет (0.569 → около 0.56) — по честной проверке она лучшая. **Победитель сменился** от одного только способа разбиения.

Бизнес-вывод тоже меняется: по свойствам одного заказа десерт у незнакомого гостя предсказывается слабо — на 5–6 п.п. лучше ответа «всегда да». Если запускать функцию для новых гостей, хватит простой модели или правила; для постоянных гостей полезнее явный признак «доля десертов в его прошлых заказах».

### Одно разбиение: `GroupShuffleSplit`

Для отложенной выборки — аналога `train_test_split` — есть `GroupShuffleSplit`: он случайно выбирает **гостей** в тест, а не строки.

```python
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

o = pd.read_csv("guest_orders.csv")
X = o[["weekday", "hour", "items", "amount", "distance_km"]]
y, groups = o["dessert"], o["guest_id"]

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=groups))
g_train, g_test = set(groups.iloc[train_idx]), set(groups.iloc[test_idx])
print(f"строк: обучение {len(train_idx)}, тест {len(test_idx)}")
print(f"гостей: обучение {len(g_train)}, тест {len(g_test)}, общих {len(g_train & g_test)}")

gr_tr, gr_te = train_test_split(groups, test_size=0.2, random_state=42)   # те же строки, что ушли бы в train и test
print(f"обычный train_test_split: гостей в тесте {gr_te.nunique()}, из них есть и в обучении {len(set(gr_tr) & set(gr_te))}")
```

Что здесь происходит:

- `GroupShuffleSplit(n_splits=1, test_size=0.2, ...)` — одно разбиение, в тест уходит около 20 % **гостей** (не строк: число строк зависит от того, сколько заказов у попавших гостей);
- `gss.split(...)` — генератор пар номеров строк, `next(...)` берёт первую (и единственную) пару;
- `set(...) & set(...)` — пересечение множеств: гости, которые есть в обеих частях;
- `train_test_split(groups, ...)` с тем же `random_state` разрезает строки так же, как разрезал бы `X` и `y`, — так мы узнаём, каким гостям принадлежат строки обычного теста.

Как читать результат: в групповом разбиении в тесте 48 гостей и 454 строки, общих гостей с обучением — **0**. В обычном — все 206 гостей теста встречаются и в обучении: проверка «на новых гостях» там просто не происходит.

::: sql
Групповое разбиение в SQL — это выбор тестовых гостей подзапросом: `WHERE guest_id IN (SELECT guest_id FROM guests WHERE random() < 0.2)`, а не `WHERE random() < 0.2` по заказам.
:::

::: quiz
Модель предсказывает, опоздает ли доставка, и её будут применять во всех тех же шести кофейнях, на которых она училась. Нужно ли групповое разбиение по `shop_id`?

- [x] Нет: модель не встретит незнакомую кофейню, поэтому проверка «на новой кофейне» отвечает не на тот вопрос
  > Группы выбирают по тому, как модель будут применять. Кофейни те же — значит, их заказы законно есть и в обучении, и в проверке. А вот для новой кофейни, которая откроется в Екатеринбурге, честнее было бы групповое разбиение.
- [ ] Да: строки одной кофейни похожи, а похожие строки всегда нужно держать в одной части
  > Похожесть сама по себе не повод. Повод — когда в работе модель встретит объект, которого не было в обучении.
- [ ] Да: групповое разбиение всегда честнее обычного
  > Оно отвечает на другой вопрос — про новые группы. Если новых групп не будет, оно занизит оценку и может отбраковать хорошую модель.
- [ ] Нет: групповое разбиение нужно только для гостей
  > Группой может быть что угодно, что повторяется в строках: кофейня, курьер, устройство, день.
:::

::: deep А если модель будут применять к тем же гостям?
Тогда «узнать гостя» — законное преимущество, но его надо дать модели честно: явным признаком «доля десертов в прошлых заказах гостя», посчитанным только по заказам **до** текущего. И проверять модель по времени: учить на сентябре, проверять на октябре. Так устроены проверки во временных рядах — в главе 12.
:::

::: warn Типичные ошибки
- **Забыли `groups=`.** `cross_val_score(model, X, y, cv=GroupKFold(5))` падает с `ValueError: The 'groups' parameter should not be None.` Передайте столбец групп: `groups=o["guest_id"]`.
- **Группы не той длины.** `groups` — значение для **каждой строки** `X`, а не список уникальных гостей. Если отфильтровали `X`, отфильтруйте и `groups` той же маской.
- **Ждали ровно 20 % строк.** `GroupShuffleSplit(test_size=0.2)` берёт 20 % групп; строк в тесте будет больше или меньше — смотря сколько заказов у попавших гостей.
- **Группа в признаках.** Если в `X` остался `guest_id` закодированным числом или почти уникальный признак гостя (точный адрес), обычное разбиение даёт «память», а групповое — честную, но низкую оценку. Разница двух оценок — хороший детектор такой утечки.
:::

{{practice: group-split, group-cv}}

## Сколько времени учится и предсказывает модель

**Зачем.** Модель выбирают не только по качеству. Предсказание в приложении должно приходить за доли секунды, а переобучение каждую ночь — укладываться в отведённое окно. Если лес лучше логистической регрессии на 0.5 п.п., но учится в сто раз дольше, это аргумент в обсуждении. Поэтому в таблицу сравнения моделей добавляют два столбца: время `fit` и время `predict`.

::: tip Аналогия
Выбирая кофемашину, смотрят не только на вкус эспрессо, но и на то, сколько она греется утром и сколько секунд готовит одну чашку. Вкус — качество модели, прогрев — `fit`, чашка — `predict`.
:::

### Секундомер в коде: `time.perf_counter()`

`time.perf_counter()` возвращает показания точных часов в секундах. Само число смысла не имеет — смысл имеет **разница** двух показаний:

```python
import time
t0 = time.perf_counter()          # засекли
total = sum(range(1_000_000))     # работа, которую измеряем
t1 = time.perf_counter()          # остановили
print(f"прошло {t1 - t0:.4f} с")
```

Что здесь происходит:

- `t0` и `t1` — два показания часов до и после работы;
- `t1 - t0` — сколько секунд заняла работа между ними;
- формат `:.4f` — четыре знака после запятой: короткие операции длятся тысячные доли секунды.

Число у вас будет своим: время зависит от компьютера, его загрузки и даже от того, первый ли это запуск. Python в браузере заметно медленнее, чем на компьютере, поэтому сравнивают модели **между собой** на одной машине, а не абсолютные секунды.

### Таблица «модель | качество | fit | predict»

```python
import time
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
y = ok["actual_min"] > ok["promised_min"]
num = ["distance_km", "items", "promised_min", "hour"]
X = pd.get_dummies(ok[num + ["courier", "weather", "shop_id"]], dtype=int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = {
    "дерево, глубина 3": DecisionTreeClassifier(max_depth=3, random_state=0),
    "лес, 50 деревьев": RandomForestClassifier(n_estimators=50, random_state=0),
    "логистическая регрессия": LogisticRegression(max_iter=2000),
}
rows = []
for name, model in models.items():
    t0 = time.perf_counter()
    model.fit(X_train, y_train)
    t1 = time.perf_counter()
    pred = model.predict(X_test)
    t2 = time.perf_counter()
    rows.append({"модель": name, "accuracy": (pred == y_test).mean(),
                 "fit, с": t1 - t0, "predict, с": t2 - t1})
pd.DataFrame(rows).set_index("модель").round(4)
```

Что здесь происходит:

- три показания часов на модель: до `fit`, между `fit` и `predict`, после `predict`;
- `rows` — список словарей, по одному на модель; `pd.DataFrame(rows)` превращает его в таблицу, где ключи словарей — столбцы;
- измеряем только сами `fit` и `predict`: чтение файла и `get_dummies` — вне секундомера, они одинаковы для всех моделей.

Как читать результат: по качеству модели близки, а по времени — нет: лес из 50 деревьев учится в десятки раз дольше одного дерева и предсказывает тоже медленнее — каждое из 50 деревьев отвечает отдельно. На 1 841 строке это доли секунды или секунды, на миллионе строк — уже минуты и часы. Дерево и логистическая регрессия предсказывают почти мгновенно — для приложения с ответом «на лету» это довод в их пользу.

::: predict
```python static
import time
t0 = time.perf_counter()
t1 = time.perf_counter()
print(t1 >= t0, t1 - t0 < 1)
```

- `False True`
- [x] `True True`
- `True False`

Почему: часы `perf_counter` не идут назад, поэтому второе показание не меньше первого; между двумя соседними вызовами проходит ничтожная доля секунды.
:::

::: tip В своём Jupyter
Там для замеров есть магические команды (в редакторе курса они не работают): `%%time` в первой строке ячейки замеряет всю ячейку один раз и печатает `Wall time` — время «по настенным часам», то же, что разница `perf_counter`; `%timeit выражение` запускает строку много раз и показывает среднее ± разброс — так короткие операции измеряются надёжнее. Подробнее — в уроке «Jupyter: руки на клавиатуре» главы 2.
:::

::: warn Типичные ошибки
- **Один замер короткой операции.** Тысячные доли секунды сильно скачут от запуска к запуску. Повторите замер несколько раз и смотрите на типичное значение, а не на один запуск (`%timeit` сам повторяет строку и показывает среднее ± разброс).
- **В секундомер попала подготовка.** Чтение файла или `get_dummies` внутри замера делают время всех моделей похожим. Засекайте только `fit` и `predict`.
- **Сравнение секунд с разных машин.** Время в браузере и на ноутбуке коллеги несравнимо. Сравнивайте модели на одной машине, в одном запуске.
- **`time.time()` вместо `perf_counter()`.** Обычные часы могут подводиться системой и грубее для коротких интервалов; для замеров есть `perf_counter`.
- **Магия в обычном Python.** `%%time` в `.py`-файле или в редакторе курса — `SyntaxError`. В коде используйте `time.perf_counter()`.
:::

{{practice: p-timer, speed-table}}

## Практика

## task: group-split | Новые гости в тесте | base

Отложите тест по гостям: `GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=4)` по `guest_orders.csv` с группами `guest_id`. Сохраните `n_test_rows` — число строк в тесте, `n_test_guests` — число гостей в тесте и `common` — сколько гостей есть и в обучении, и в тесте. Для сравнения сделайте обычный `train_test_split(..., test_size=0.25, random_state=4)` и сохраните `common_plain` — сколько гостей оказалось в обеих частях там.

### starter
```python
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split
o = pd.read_csv("guest_orders.csv")
X = o[["weekday", "hour", "items", "amount", "distance_km"]]
y, groups = o["dessert"], o["guest_id"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import GroupShuffleSplit as _G, train_test_split as _tts
_o = _pd.read_csv('guest_orders.csv')
_X = _o[['weekday', 'hour', 'items', 'amount', 'distance_km']]
_y, _g = _o['dessert'], _o['guest_id']
_tr, _te = next(_G(n_splits=1, test_size=0.25, random_state=4).split(_X, _y, groups=_g))
_a, _b = _tts(_g, test_size=0.25, random_state=4)
nr = need('n_test_rows')
if nr == len(_b):
    raise AssertionError(f'n_test_rows = {nr} — ровно четверть строк. Так делит обычный train_test_split; GroupShuffleSplit берёт четверть гостей, и строк выходит другое число.')
assert nr == len(_te), f'n_test_rows = {nr}. Число номеров во втором массиве из gss.split(...).'
assert need('n_test_guests') == _g.iloc[_te].nunique(), f'n_test_guests = {need("n_test_guests")}. Уникальные guest_id среди строк теста: groups.iloc[test_idx].nunique().'
assert need('common') == 0, f'common = {need("common")}. При групповом разбиении у частей не должно быть общих гостей — проверьте, что передали groups=.'
assert need('common_plain') == len(set(_a) & set(_b)), f'common_plain = {need("common_plain")}. Пересечение множеств гостей обучения и теста при обычном train_test_split.'
```

### hint
`gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=4)`, `train_idx, test_idx = next(gss.split(X, y, groups=groups))`.

### hint
Гости по номерам строк — `groups.iloc[test_idx]`; общие гости — пересечение множеств: `len(set(...) & set(...))`.

### hint
Для обычного разбиения достаточно разделить сам столбец гостей: `g_tr, g_te = train_test_split(groups, test_size=0.25, random_state=4)`.

### solution
```python
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split
o = pd.read_csv("guest_orders.csv")
X = o[["weekday", "hour", "items", "amount", "distance_km"]]
y, groups = o["dessert"], o["guest_id"]

gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=4)
train_idx, test_idx = next(gss.split(X, y, groups=groups))
n_test_rows = len(test_idx)
n_test_guests = groups.iloc[test_idx].nunique()
common = len(set(groups.iloc[train_idx]) & set(groups.iloc[test_idx]))

g_tr, g_te = train_test_split(groups, test_size=0.25, random_state=4)
common_plain = len(set(g_tr) & set(g_te))
print(n_test_rows, n_test_guests, common, common_plain)
```

### explain
В групповом тесте ровно четверть гостей — 60 из 240, а строк 618 вместо 583 (четверти от 2 332): у попавших гостей заказов в среднем чуть больше. Общих гостей — ноль, это и есть смысл разбиения. В обычном разбиении все 216 гостей теста встречаются и в обучении — модель проверяется только на «знакомых». Если `common` у вас не ноль, скорее всего, разбиение сделано не тем способом: `GroupShuffleSplit` без `groups=` падает с ошибкой, а нарезка по строкам — молча смешивает гостей.

## task: group-cv | Победитель зависит от разбиения | plus

Сравните на `guest_orders.csv` лес `RandomForestClassifier(n_estimators=50, random_state=0)` и `LogisticRegression(max_iter=2000)` двумя кросс-валидациями: `KFold(5, shuffle=True, random_state=42)` и `GroupKFold(5)` с группами `guest_id`. Сохраните `gap_forest` и `gap_lr` — насколько среднее accuracy при обычном разбиении выше, чем при групповом (3 знака), и `winner_plain`, `winner_group` — строку `"лес"` или `"логрегрессия"`: у кого выше среднее при каждом способе.

### starter
```python
import pandas as pd
from sklearn.model_selection import KFold, GroupKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
o = pd.read_csv("guest_orders.csv")
X = o[["weekday", "hour", "items", "amount", "distance_km"]]
y, groups = o["dessert"], o["guest_id"]

```

### check
```python
import pandas as _pd
from sklearn.model_selection import KFold as _KF, GroupKFold as _GKF, cross_val_score as _cvs
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.linear_model import LogisticRegression as _LR
_o = _pd.read_csv('guest_orders.csv')
_X = _o[['weekday', 'hour', 'items', 'amount', 'distance_km']]
_y, _g = _o['dessert'], _o['guest_id']
_m = {'лес': _RF(n_estimators=50, random_state=0), 'логрегрессия': _LR(max_iter=2000)}
_p = {n: _cvs(m, _X, _y, cv=_KF(5, shuffle=True, random_state=42)).mean() for n, m in _m.items()}
_q = {n: _cvs(m, _X, _y, cv=_GKF(5), groups=_g).mean() for n, m in _m.items()}
gf, gl = need('gap_forest'), need('gap_lr')
if close(gf, round(_q['лес'] - _p['лес'], 3), 0.0011):
    raise AssertionError('gap_forest с обратным знаком: из обычного разбиения вычтите групповое.')
assert close(gf, round(_p['лес'] - _q['лес'], 3), 0.0011), f'gap_forest = {gf}. Среднее KFold минус среднее GroupKFold для леса.'
assert close(gl, round(_p['логрегрессия'] - _q['логрегрессия'], 3), 0.0011), f'gap_lr = {gl}. То же для логистической регрессии.'
assert need('winner_plain') == max(_p, key=_p.get), f'winner_plain = {need("winner_plain")!r}. У кого выше среднее при KFold?'
assert need('winner_group') == max(_q, key=_q.get), f'winner_group = {need("winner_group")!r}. У кого выше среднее при GroupKFold?'
```

### hint
Для каждой модели — два вызова `cross_val_score`: с `cv=KFold(...)` и с `cv=GroupKFold(5), groups=groups`. Берите `.mean()`.

### hint
Удобно собрать словари `plain = {"лес": ..., "логрегрессия": ...}` и `group = {...}`; победитель — `max(plain, key=plain.get)`.

### hint
`gap_forest = round(plain["лес"] - group["лес"], 3)` — по неокруглённым средним.

### solution
```python
import pandas as pd
from sklearn.model_selection import KFold, GroupKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
o = pd.read_csv("guest_orders.csv")
X = o[["weekday", "hour", "items", "amount", "distance_km"]]
y, groups = o["dessert"], o["guest_id"]

models = {
    "лес": RandomForestClassifier(n_estimators=50, random_state=0),
    "логрегрессия": LogisticRegression(max_iter=2000),
}
plain, group = {}, {}
for name, model in models.items():
    plain[name] = cross_val_score(model, X, y, cv=KFold(5, shuffle=True, random_state=42)).mean()
    group[name] = cross_val_score(model, X, y, cv=GroupKFold(5), groups=groups).mean()
gap_forest = round(plain["лес"] - group["лес"], 3)
gap_lr = round(plain["логрегрессия"] - group["логрегрессия"], 3)
winner_plain = max(plain, key=plain.get)
winner_group = max(group, key=group.get)
print(plain, group)
```

### explain
Лес при обычном разбиении теряет при переходе к групповому около 7 п.п. (0.589 → 0.522), логистическая регрессия — меньше 2 п.п. (0.569 → 0.554). Победитель меняется: по обычной проверке лучше лес, по честной для новых гостей — регрессия. Лес запоминает точные адреса гостей и их привычки; регрессия рисует одну плавную зависимость и запоминать отдельных гостей не умеет — поэтому ей нечего терять. Большой разрыв между обычной и групповой оценкой — сигнал: модель выезжает на «памяти» об объектах. Если бы мы выбрали лес по обычной кросс-валидации, в приложении для новых гостей он работал бы почти как ответ «всегда да».

## task: p-timer | Секундомер для fit | warmup

`X_train` и `y_train` уже готовы. Соберите код, который засекает, сколько секунд учится дерево глубины 3, и сохраняет это время в `fit_s`.

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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

### parsons
```python
import time
from sklearn.tree import DecisionTreeClassifier
model = DecisionTreeClassifier(max_depth=3, random_state=0)
t0 = time.perf_counter()
model.fit(X_train, y_train)
fit_s = time.perf_counter() - t0
print(f"обучение: {fit_s:.4f} с")
```

### check
```python
fs = need('fit_s')
assert isinstance(fs, float), f'fit_s должно быть числом секунд (float), сейчас {type(fs).__name__}.'
assert hasattr(need('model'), 'tree_'), 'Модель не обучена: строка model.fit(...) должна выполниться.'
assert fs > 1e-4, f'fit_s = {fs:.6f} с — слишком мало: похоже, секундомер запущен уже после fit. t0 — до обучения, разница — сразу после.'
assert fs < 60, f'fit_s = {fs} — подозрительно много: в замер попало что-то лишнее.'
```

### hint
Порядок: импорты → создать модель → засечь `t0` → `fit` → разница показаний.

### hint
Секундомер оборачивает только `model.fit(...)`: `t0` — строкой выше, `fit_s = time.perf_counter() - t0` — строкой ниже.

## task: speed-table | Качество и скорость | base

`X_train`, `X_test`, `y_train`, `y_test` уже готовы. Сравните дерево `DecisionTreeClassifier(max_depth=3, random_state=0)` и лес `RandomForestClassifier(n_estimators=100, random_state=0)`. Соберите таблицу `speed`: индекс — `"дерево"` и `"лес"`, столбцы `accuracy` (доля правильных на тесте, 3 знака), `fit_s` и `predict_s` (секунды, замер `time.perf_counter()`). В `fit_ratio` сохраните, во сколько раз лес учится дольше дерева.

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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

### starter
```python
import time
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
from sklearn.ensemble import RandomForestClassifier as _RF
_d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
from sklearn.model_selection import train_test_split as _tts
_o = _d[_d['actual_min'].between(1, 299)].copy()
_o['hour'] = _o['created'].dt.hour
_y = _o['actual_min'] > _o['promised_min']
_X = _pd.get_dummies(_o[['distance_km', 'items', 'promised_min', 'hour', 'courier', 'weather', 'shop_id']], dtype=int)
_a, _b, _c, _e = _tts(_X, _y, test_size=0.2, random_state=42)
_acc = {'дерево': round((_T(max_depth=3, random_state=0).fit(_a, _c).predict(_b) == _e).mean(), 3),
        'лес': round((_RF(n_estimators=100, random_state=0).fit(_a, _c).predict(_b) == _e).mean(), 3)}
t = need('speed', _pd.DataFrame)
assert set(t.index) == {'дерево', 'лес'}, f'Индекс speed: {list(t.index)}, а нужны «дерево» и «лес».'
assert {'accuracy', 'fit_s', 'predict_s'} <= set(t.columns), f'Столбцы speed: {list(t.columns)}, нужны accuracy, fit_s, predict_s.'
for n in _acc:
    assert close(t.loc[n, 'accuracy'], _acc[n], 0.0011), f'{n}: accuracy = {t.loc[n, "accuracy"]}, а ожидалось {_acc[n]}. Доля совпадений predict(X_test) и y_test.'
assert (t[['fit_s', 'predict_s']] > 0).all().all(), 'Времена должны быть положительными: разница показаний perf_counter после и до.'
assert calls('perf_counter') >= 2, 'Замеряйте время через time.perf_counter().'
assert t.loc['лес', 'fit_s'] > t.loc['дерево', 'fit_s'], 'Лес из 100 деревьев не может учиться быстрее одного дерева — проверьте, что в fit_s попал именно fit своей модели.'
assert close(need('fit_ratio'), t.loc['лес', 'fit_s'] / t.loc['дерево', 'fit_s'], 0.05 * need('fit_ratio') + 0.01), 'fit_ratio — fit_s леса, делённое на fit_s дерева.'
```

### hint
Для каждой модели — три показания `time.perf_counter()`: до `fit`, после `fit` (оно же до `predict`), после `predict`. Результаты — в словарь, словари — в список.

### hint
`rows.append({"модель": name, "accuracy": round((pred == y_test).mean(), 3), "fit_s": t1 - t0, "predict_s": t2 - t1})`, затем `pd.DataFrame(rows).set_index("модель")`.

### hint
`fit_ratio = speed.loc["лес", "fit_s"] / speed.loc["дерево", "fit_s"]`.

### solution
```python
import time
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

models = {
    "дерево": DecisionTreeClassifier(max_depth=3, random_state=0),
    "лес": RandomForestClassifier(n_estimators=100, random_state=0),
}
rows = []
for name, model in models.items():
    t0 = time.perf_counter()
    model.fit(X_train, y_train)
    t1 = time.perf_counter()
    pred = model.predict(X_test)
    t2 = time.perf_counter()
    rows.append({"модель": name, "accuracy": round((pred == y_test).mean(), 3),
                 "fit_s": t1 - t0, "predict_s": t2 - t1})
speed = pd.DataFrame(rows).set_index("модель")
fit_ratio = speed.loc["лес", "fit_s"] / speed.loc["дерево", "fit_s"]
print(f"лес учится в {fit_ratio:.0f} раз дольше")
speed
```

### explain
Качество на этом тесте почти одинаковое (0.892 у дерева и 0.905 у леса), а время отличается в десятки раз: лес строит сто деревьев, и каждое из них ещё и отвечает при `predict`. Точное число у вас своё — оно зависит от компьютера и его загрузки, поэтому проверка смотрит только на то, что лес медленнее. Вывод для отчёта: «лес лучше на 1 п.п. и в N раз медленнее» — и решение зависит от того, что дороже в этой задаче. Частая ошибка — засечь `t0` один раз перед циклом: тогда время каждой следующей модели включает время всех предыдущих.
