---
title: Что такое машинное обучение
lead: "До сих пор правила придумывали мы: «если курьер пеший — скорее опоздает». Машинное обучение переворачивает задачу: мы даём примеры с ответами, а модель сама находит правила. Знакомимся с языком ML — признаки, целевой признак, обучение, предсказание, — учимся переводить запрос заказчика в ML-задачу нужного типа и обучаем первую модель в scikit-learn."
files: [deliveries.csv]
recap:
  - "Объект — строка (доставка). Признаки `X` — то, что известно заранее. Целевой признак `y` — то, что хотим предсказать."
  - "Классификация — предсказываем категорию (опоздает / нет). Регрессия — число (сколько минут)."
  - "Типы задач: классификация, регрессия, прогноз ряда (с учителем — ответ есть в данных) и кластеризация (без учителя — ответа нет)."
  - "Снятие запроса — шесть вопросов до кода: какое решение, что объект, момент прогноза, целевой признак, с чем сравниваем, как поймём, что стало лучше. Один запрос может дать разные постановки — выбирает решение."
  - "scikit-learn: `model = DecisionTreeClassifier(...)`, `model.fit(X, y)` — обучение, `model.predict(X_new)` — предсказание."
  - "Доля правильных ответов — accuracy: `accuracy_score(y, pred)`."
  - "Сначала — базовая модель (baseline): самый частый ответ или простое правило. Модель полезна, только если её превосходит."
  - "Признаки — только то, что известно **до** события. Фактическое время доставки нельзя использовать, чтобы предсказать опоздание."
---

## Правила или примеры

В главе 4 мы нашли, почему доставки опаздывают, и могли бы написать правило: «если курьер пеший и обещали 30 минут — предупредить гостя об опоздании». Так работает классическая аналитика: человек смотрит на данные и придумывает правила.

У этого подхода есть пределы. Признаков много, они влияют вместе (пеший курьер + снег + час пик), и подобрать хорошие пороги вручную трудно. **Машинное обучение** (ML) делает обратное: мы показываем модели тысячи примеров с правильными ответами, а она сама подбирает правила, которые лучше всего их объясняют. Потом эти правила применяются к новым случаям.

## Язык машинного обучения

| Термин | Что это | У нас |
|---|---|---|
| объект | одна строка | одна доставка |
| признаки, `X` | что известно об объекте заранее | расстояние, число позиций, обещанное время, час |
| целевой признак, `y` | что хотим предсказать | опоздает ли доставка |
| обучение, `fit` | модель подбирает правила по примерам | — |
| предсказание, `predict` | модель отвечает на новых объектах | — |

Задачи бывают двух главных видов:

- **классификация** — ответ из набора категорий: опоздает / не опоздает, уйдёт гость / останется;
- **регрессия** — ответ числом: сколько минут займёт доставка, какая будет выручка.

```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["hour"] = ok["created"].dt.hour

X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["late"]
print(X.shape, y.shape)
X.head()
```

**Что здесь происходит:**

- `between(1, 299)` — отбрасываем явные ошибки во времени доставки (0 минут, сутки).
- `ok["late"]` — целевой признак: сравнение двух столбцов даёт True/False для каждой доставки.
- `ok["hour"]` — новый признак из даты: час создания заказа известен заранее, его можно брать.
- `X` — четыре столбца, `y` — один; `.shape` показывает, что строк в них поровну: по одной на доставку.

Принято: `X` — таблица признаков (заглавная буква — «матрица»), `y` — столбец ответов.

::: warn
В признаки нельзя брать то, чего мы не знаем в момент предсказания. Фактическое время `actual_min` становится известно, только когда доставка уже приехала, — а предсказывать опоздание нужно **до** отправки курьера. Если взять `actual_min` в признаки, модель будет угадывать почти идеально — и бесполезно. Это называется **утечкой** (leakage), подробнее — в уроке «Категориальные признаки и утечки».
:::

::: figure ml-scheme
Обучение с учителем: модель учится на прошлых доставках, где известен ответ, и предсказывает его для новых.
:::

{{practice: xy}}

## Типы задач и снятие запроса

**Зачем.** Заказчик никогда не приходит со словами «обучите бинарный классификатор». Он приходит с болью: «гости жалуются на опоздания», «уходят постоянные гости», «не знаем, сколько круассанов печь». Прежде чем писать код, аналитик переводит такую фразу в ML-задачу: что предсказываем, для кого, в какой момент и что с ответом будут делать. Этот разговор называют **снятием запроса**. Ошибка на этом шаге обходится дороже любой ошибки в коде: можно отлично решить не ту задачу.

::: tip Аналогия
Портной не начинает с ножниц. Сначала он снимает мерки и спрашивает, куда костюм: на свадьбу или в офис. Снятие запроса — те же мерки: без них выйдет хорошо сшитая вещь не по размеру.
:::

### Карта типов задач

| Тип | Что на выходе | Есть ли ответ в данных | Пример в «Зерне» |
|---|---|---|---|
| бинарная классификация | одна из двух категорий | да | опоздает ли доставка; уйдёт ли гость |
| многоклассовая классификация | одна из нескольких категорий | да | какой напиток гость закажет следующим; тема отзыва |
| регрессия | число | да | сколько минут займёт доставка; выручка завтра |
| прогноз временного ряда | числа на будущие даты | да, из прошлого ряда | заказы в приложении по часам на неделю вперёд |
| кластеризация | группы похожих объектов | **нет** | какие бывают гости — для разных рассылок |

Первые четыре — **обучение с учителем**: в прошлых данных есть правильный ответ (опоздала или нет), и модель учится его воспроизводить. Кластеризация — **обучение без учителя**: готовых ответов нет, модель ищет структуру сама. Главный вопрос для выбора — «есть ли в данных столбец с ответом и какого он типа».

::: figure task-types
Карта типов задач как цепочка вопросов: есть ли в прошлых данных правильный ответ, что это за ответ и нужен ли он на будущие даты.
:::

### Шесть вопросов к запросу

Запрос логиста: «Гости жалуются на опоздания, сделайте что-нибудь». Задаём вопросы по порядку и записываем ответы:

1. **Какое решение примут по ответу модели?** — Предупредить гостя и сразу дать купон, если доставка, скорее всего, опоздает.
2. **Объект — что одна строка?** — Один заказ доставки.
3. **Момент прогноза — когда модель отвечает?** — Когда заказ передают курьеру. Значит, в признаки идёт только то, что известно в этот момент: расстояние, позиции, сумма, обещание, погода, тип курьера. `actual_min` и `rating` появляются после доставки — это утечка.
4. **Целевой признак — что предсказываем?** — Опоздает ли: `actual_min > promised_min`. Ответ «да/нет» — бинарная классификация.
5. **С чем сравниваем?** — С базовой моделью «всегда вовремя» и с правилом «пеший — опоздает» (следующий раздел).
6. **Как поймём, что стало лучше?** — Метрика модели (пока — доля правильных ответов) и бизнес-метрика: число жалоб на опоздания.

::: figure predict-moment
Жизнь одного заказа доставки на оси времени. Модель отвечает в момент передачи курьеру, поэтому в признаки идёт только то, что известно левее синей линии. `actual_min` станет ответом, а оценка гостя появится ещё позже — в признаках это утечка.
:::

Тот же запрос можно поставить иначе. Если решение — **показывать гостю честное время доставки**, целевой признак — минуты (`actual_min`), и это регрессия. Одна жалоба — две разные задачи; выбирает их не аналитик, а решение, которое будут принимать.

::: sql
Карточка задачи похожа на постановку отчёта: «по какой таблице, на каком уровне детализации (`GROUP BY`), за какой период и какой показатель». Разница в одном: в отчёте показатель уже есть, а в ML мы учимся предсказывать его заранее.
:::

::: quiz
Маркетолог: «Хотим понять, какие у нас бывают гости, чтобы писать им разные рассылки. Групп заранее не знаем». Какая это задача?

- [x] Кластеризация — обучение без учителя: готового столбца с «типом гостя» нет, группы ищет сама модель
  > Ключевая фраза — «групп заранее не знаем». Нет правильных ответов в данных — нет и обучения с учителем.
- [ ] Многоклассовая классификация: каждый гость относится к одному из типов
  > Классификации нужен столбец с правильным типом у прошлых гостей, а его нет — типы как раз и надо найти.
- [ ] Регрессия: предскажем, сколько гость потратит
  > Это другой вопрос. Сумма трат может стать признаком для группировки, но запрос — о группах, а не о числе.
- [ ] Это не задача ML — достаточно отчёта по среднему чеку
  > Отчёт по одному показателю не найдёт группы, которые различаются сразу по многим привычкам: времени визитов, напиткам, доставке.
:::

::: warn Типичные ошибки
- **Цель не та, что нужна решению.** Модель «сколько минут» не скажет, кому дать купон, без дополнительного порога; модель «опоздает ли» не подскажет гостю время. Сначала решение — потом цель.
- **Момент прогноза не зафиксирован.** Не договорились, когда модель отвечает, — в признаки легко попадает будущее: `actual_min`, оценка гостя, «заказ отменён».
- **Нет точки отсчёта.** Без базовой модели и текущего процесса нельзя сказать, принесла ли модель пользу.
- **ML там, где хватит отчёта.** Если решение принимается по одному порогу («больше 3 км — давать 45 минут»), часто достаточно `GROUP BY` и правила. Модель нужна, когда признаков много и они действуют вместе.
:::

{{practice: task-kind}}

## Базовая модель: с чем сравнивать

Прежде чем обучать что-то сложное, посчитаем, насколько хорош самый глупый способ — всегда отвечать «не опоздает»:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
always_no = (y == False).mean()
print(f"всегда «вовремя»: правы в {always_no:.1%} случаев")
```

Три четверти правильных ответов без всякого ума — просто потому, что опозданий меньше. Это **базовая модель** (baseline). Любая настоящая модель должна быть заметно лучше, иначе она не нужна.

::: predict
```python static
import pandas as pd
y = pd.Series([True] * 10 + [False] * 90)
print((y == False).mean())
```

- `0.1`
- [x] `0.9`
- `0.5`

Почему: если отвечать «нет» всегда, мы правы на всех 90 объектах с ответом «нет». Когда классы несбалансированны, высокая доля правильных ответов ещё ничего не говорит о качестве модели.
:::

Правило аналитика из главы 4 — тоже модель, только написанная вручную:

```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
rule = ok["courier"] == "пеший"
print(f"правило «пеший — опоздает»: {(rule == y).mean():.1%}")
```

Простое правило уже заметно лучше базовой модели. Посмотрим, сможет ли машинное обучение больше.

### Разберём вместе: откуда берутся 86.5 %

Разложим правило по четырём группам — `pd.crosstab(ok["courier"] == "пеший", y)`:

| | вовремя | опоздала |
|---|---|---|
| **не пеший** | 1295 | 143 |
| **пеший** | 105 | 298 |

Правило говорит «опоздает» ровно для пеших. Оно право в двух клетках: не пеший и вовремя (1295) плюс пеший и опоздал (298). Итого 1593 из 1841 доставки — **86.5 %**.

Ошибается правило тоже двумя способами: 143 опоздания у машин и велосипедов оно пропустило, а 105 пеших доставок, приехавших вовремя, зря назвало опоздавшими. Запомните эти два вида ошибок — в главе 7 у них появятся имена, и окажется, что они стоят по-разному.

Что получилось: «доля правильных ответов» — это сумма двух клеток таблицы, делённая на все строки. Никакой магии в метрике нет — это та же группировка, что в главе 2.

::: note Базовая модель для регрессии
Если ответ — число (сколько минут займёт доставка), «самый частый ответ» не подходит. Простейшая модель регрессии всегда отвечает одним и тем же числом — средним или медианой. Ошибку такой модели меряют **средней абсолютной ошибкой** (MAE, mean absolute error): для каждой доставки берут разницу «факт − прогноз», отбрасывают знак (`.abs()`) и усредняют. MAE = 8 читается как «ошибаемся в среднем на 8 минут». Подробно метрики регрессии разобраны в уроке «Регрессия: сколько минут»; задача «Регрессия: базовая модель» ниже — первая проба.
:::

::: quiz
Модель угадывает опоздание в 78 % доставок. Хороший ли это результат?

- [x] Пока неизвестно: сначала сравнить с базовой моделью «всегда вовремя» — она права в 76 % случаев
  > Доля правильных без точки отсчёта ничего не говорит. Если опаздывает лишь четверть доставок, «всегда вовремя» уже даёт около 76 %.
- [ ] Да: 78 % — больше трёх четвертей
  > Больше трёх четвертей, но и тупое правило даёт почти столько же.
- [ ] Нет: хорошая модель угадывает 95 % и больше
  > Достижимое качество зависит от задачи. Где-то и 60 % — успех.
- [ ] Хороший, если модель — дерево
  > Тип модели не делает результат хорошим. Сравнивают с базовой моделью.
:::

{{practice: baseline, rule, mae-base}}

## Первая модель в scikit-learn

**scikit-learn** (`sklearn`) — главная библиотека классического ML в Python. Все модели в ней устроены одинаково:

1. создать модель с настройками;
2. `fit(X, y)` — обучить на примерах;
3. `predict(X_new)` — получить ответы.

Начнём с **решающего дерева** — модели, которая учит набор вложенных правил «если — то» (подробно — в уроке «Решающее дерево изнутри»):

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]

model = DecisionTreeClassifier(max_depth=3, random_state=0)
model.fit(X, y)
pred = model.predict(X)
print(f"доля правильных ответов: {accuracy_score(y, pred):.1%}")
```

- `max_depth=3` — дерево задаёт не больше трёх вопросов подряд;
- `random_state=0` — когда два вопроса одинаково хороши, дерево выбирает между ними случайно; `random_state` закрепляет этот выбор, чтобы результат повторялся;
- `accuracy_score(y, pred)` — доля совпадений правильных ответов и предсказаний (accuracy).

Модель лучше базовой (около 80 % против 76 %), но **проигрывает** правилу «пеший — опоздает» (87 %). Дело не в модели, а в признаках: тип курьера мы ей не дали, а это главная причина опозданий. Модель не может быть умнее данных, которые ей показали. Как подать ей текстовые признаки вроде `courier`, разберём в уроке «Категориальные признаки и утечки».

И ещё одно наблюдение. Дерево глубины 1 — всего один вопрос — даёт ровно базовые 76 %: опозданий меньше половины по обе стороны от его вопроса, поэтому в обеих ветках оно отвечает «вовремя». Хороший вопрос ещё не значит другой ответ — в задаче со звёздочкой «Первый вопрос дерева» это видно руками.

::: warn
Мы проверили модель на тех же данных, на которых она училась. Это как проверять ученика на задачах, решения которых он видел: оценка завышена. Как проверять честно — в следующем уроке.
:::

{{practice: p-fit, first-tree, leak, first-split}}

## Предсказание для новых доставок

Обученная модель отвечает на новые объекты. Сначала угадайте сами:

::: predict
```python static
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[cols], ok["actual_min"] > ok["promised_min"])
# два заказа отличаются только числом позиций
new = pd.DataFrame({"distance_km": [1.2, 1.2], "items": [2, 4], "promised_min": [30, 30], "hour": [13, 13]})
print(model.predict(new))
```

- `[False False]`
- [x] `[False  True]`
- `[ True  True]`

Почему: заказы отличаются только числом позиций. Для модели большой заказ на короткое обещание — рискованный, маленький — нет.
:::

Теперь подробнее. Признаки нужно передать таблицей с теми же столбцами в том же порядке:

```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[cols], ok["actual_min"] > ok["promised_min"])

new = pd.DataFrame({"distance_km": [1.2, 1.2, 4.0], "items": [2, 4, 1], "promised_min": [30, 30, 45], "hour": [13, 13, 10]})
print(model.predict(new))
```

Первые два заказа отличаются только числом позиций — и модель отвечает по-разному: большой заказ на короткое обещание она считает рискованным.

`fit` возвращает саму модель, поэтому создание и обучение можно записать одной строкой.

::: warn Типичные ошибки
- **Признак из будущего.** `actual_min`, оценка гостя, статус «доставлено» — всё, что появляется после события, в `X` брать нельзя.
- **Нет сравнения с базовой моделью.** «80 % правильных» без «76 % у ответа всегда нет» ничего не значит.
- **Проверка на обучающих данных.** Модель «помнит» эти строки; честная проверка — на новых (урок «Обучающая и тестовая выборки»).
- **Новые данные в другом виде.** Для `predict` нужны те же столбцы в том же порядке, что при `fit`.
- **`y` в `X`.** Если целевой признак случайно остался в таблице признаков, модель «угадает» всё.
:::

{{practice: new-orders}}

## Разберём вместе: карточка задачи

Вернёмся к запросу логиста из раздела «Шесть вопросов к запросу». Теперь, когда модель обучена, запишем «карточку задачи» и соберём обе постановки кодом — так начинается блокнот любого ML-проекта:

```python
import pandas as pd

card = {
    "решение": "предупредить гостя и дать купон",
    "объект": "заказ доставки",
    "момент прогноза": "передача курьеру",
    "цель": "опоздает ли: actual_min > promised_min",
    "тип": "бинарная классификация",
    "сравнение": "«всегда вовремя», правило «пеший — опоздает»",
}
for k, v in card.items():
    print(f"{k:>16}: {v}")

d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
after_event = ["actual_min", "rating"]           # станут известны после доставки
features = [c for c in d.columns if c not in after_event + ["delivery_id"]]
print("признаки-кандидаты:", features)

y_cls = ok["actual_min"] > ok["promised_min"]    # классификация: да/нет
y_reg = ok["actual_min"] - ok["promised_min"]    # регрессия: на сколько минут
print("доля опозданий:", round(y_cls.mean(), 3))
print(y_reg.describe().round(1))
```

Что здесь происходит:

- `card` — обычный словарь: ответы на шесть вопросов. Его удобно положить в начало блокнота проекта — первым разделом «Цель»;
- `features` — генератор списка оставляет столбцы, которые известны в момент прогноза: убираем то, что появится после доставки, и `delivery_id` — номер заказа ничего не говорит о риске опоздания. Кандидаты ещё не готовы для модели: из `created` позже возьмём час, а `shop_id` — номер кофейни, то есть категория (как подать категории модели — в уроке «Категориальные признаки и утечки»);
- `y_cls` и `y_reg` — два целевых признака для двух постановок одного запроса: True/False и число минут (отрицательное — приехали раньше обещанного).

Как читать результат: в классификации опаздывает 24 % заказов — классы неравные, и это сразу подсказывает, что «доля правильных» будет обманчивой (об этом — глава 7). В регрессии средняя доставка приезжает на 7 минут **раньше** обещанного, а четверть — на 15 минут раньше и больше. Для решения «предупредить гостя» хватит «да/нет»; для решения «показать честное время» нужна регрессия.

{{practice: frame}}

## Практика

## task: xy | Признаки и цель | warmup

Соберите `X` — таблицу из признаков `distance_km`, `items`, `promised_min` (в этом порядке) и `y` — Series с опозданием (`actual_min > promised_min`). Доставки — с временем 1–299 минут.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X, y = need('X', _pd.DataFrame), need('y', _pd.Series)
assert list(X.columns) == ['distance_km', 'items', 'promised_min'], f'Столбцы X: {list(X.columns)}, а нужны distance_km, items, promised_min — в этом порядке.'
assert len(X) == len(ok) == len(y), 'X и y — по всем доставкам с временем 1–299 минут.'
assert y.sum() == (ok['actual_min'] > ok['promised_min']).sum(), 'y — опоздание: actual_min > promised_min.'
assert 'actual_min' not in X.columns, 'actual_min в признаках — утечка.'
```

### hint
`X = ok[["distance_km", "items", "promised_min"]]`, `y = ok["actual_min"] > ok["promised_min"]`.

### hint
Двойные квадратные скобки дают таблицу (DataFrame), одинарные — один столбец (Series): `X` — это таблица признаков, `y` — один столбец ответов. Сначала отфильтруйте `ok`, и только потом берите из него и `X`, и `y`, — тогда строки в них совпадут.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "items", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
```

## task: baseline | Базовая модель | warmup

Сохраните в `base_acc` долю правильных ответов модели «всегда вовремя» (3 знака).

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
assert close(need('base_acc'), round((~y).mean(), 3)), f'base_acc = {need("base_acc")}. Нужна доля доставок без опоздания (где y равно False), округлённая до 3 знаков.'
```

### hint
«Всегда вовремя» права там, где `y == False`: `(~y).mean()`.

### hint
Модель «всегда вовремя» на каждый заказ отвечает False. Она права ровно там, где опоздания не было, поэтому её доля правильных — это доля доставок без опоздания. `~y` переворачивает True/False, а среднее от булевой Series — доля True.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
base_acc = round((~y).mean(), 3)
```

## task: p-fit | Обучить и предсказать | warmup

Соберите программу: обучить дерево глубины 2 и вывести долю правильных ответов (3 знака).

### parsons
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
X = ok[["distance_km", "promised_min"]]
y = ok["actual_min"] > ok["promised_min"]
model = DecisionTreeClassifier(max_depth=2, random_state=0)
model.fit(X, y)
print(round(accuracy_score(y, model.predict(X)), 3))
```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
X = ok[['distance_km', 'promised_min']]
y = ok['actual_min'] > ok['promised_min']
m = _T(max_depth=2, random_state=0).fit(X, y)
assert _lines == [str(round((m.predict(X) == y).mean(), 3))], f'Сейчас: {_lines}'
```

### hint
Сначала данные, потом модель, обучение и только потом предсказание.

## task: task-kind | Какой это тип задачи | warmup

Определите тип задачи для каждого запроса. Заполните словарь `kinds`: ключ — номер запроса, значение — одна из строк `"классификация"`, `"регрессия"`, `"кластеризация"`.

1. «Уйдёт ли гость в ближайшие 90 дней?»
2. «Сколько выручки сделает кофейня на Баумана завтра?»
3. «Разбейте гостей на группы по привычкам — сколько групп, не знаем».
4. «Какой из пяти напитков гость закажет следующим?»
5. «Через сколько минут приедет курьер?»

### starter
```python
kinds = {
    1: "...",
    2: "...",
    3: "...",
    4: "...",
    5: "...",
}
```

### check
```python
k = need('kinds', dict)
ok = {1: 'классификация', 2: 'регрессия', 3: 'кластеризация', 4: 'классификация', 5: 'регрессия'}
assert set(k) == set(ok), f'Ключи словаря — номера запросов 1–5, сейчас {sorted(k)}.'
allowed = {'классификация', 'регрессия', 'кластеризация'}
bad = [i for i in k if k[i] not in allowed]
assert not bad, f'В запросах {bad} значение не из списка: пишите «классификация», «регрессия» или «кластеризация» строчными буквами.'
wrong = [i for i in sorted(ok) if k[i] != ok[i]]
assert not wrong, f'Не тот тип в запросах {wrong}. Спросите себя: ответ — категория, число или группы, которых в данных нет?'
```

### hint
Смотрите на ответ: категория (да/нет, один из напитков) — классификация; число — регрессия; группы без готовых ответов в данных — кластеризация.

### hint
«Какой из пяти напитков» — тоже классификация, только классов пять, а не два.

### solution
```python
kinds = {
    1: "классификация",
    2: "регрессия",
    3: "кластеризация",
    4: "классификация",
    5: "регрессия",
}
```

## task: rule | Правило аналитика | base

Сравните два ручных правила: «опоздает, если курьер пеший» и «опоздает, если обещали 30 минут». Сохраните `acc_walk` и `acc_30` — доли правильных ответов каждого правила (3 знака), и `better` — название лучшего правила: `"пеший"` или `"30 минут"`.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
a = round(((ok['courier'] == 'пеший') == y).mean(), 3)
b = round(((ok['promised_min'] == 30) == y).mean(), 3)
assert close(need('acc_walk'), a) and close(need('acc_30'), b), f'acc_walk, acc_30 = {need("acc_walk")}, {need("acc_30")}, а нужно {a}, {b}.'
assert need('better') == ('пеший' if a > b else '30 минут'), f'better = {need("better")!r}. Сравните acc_walk и acc_30 и запишите название правила с большей долей.'
```

### hint
Правило — маска `True/False`. Доля правильных — `(rule == y).mean()`.

### hint
Маска «пеший» — `ok["courier"] == "пеший"`, маска «30 минут» — `ok["promised_min"] == 30`. Сравните каждую с `y` через `==` и возьмите `.mean()`: так получится доля заказов, где правило угадало. В `better` — строка, которую выберет обычный `if … else`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
acc_walk = round(((ok["courier"] == "пеший") == y).mean(), 3)
acc_30 = round(((ok["promised_min"] == 30) == y).mean(), 3)
better = "пеший" if acc_walk > acc_30 else "30 минут"
```

### explain
«Пеший» — 0.865, «30 минут» — 0.726. Второе правило даже хуже базовой модели (0.760): обещание 30 минут дают 36 % заказов, а опаздывает всего 24 %, и правило называет опоздавшими слишком многих. Правило должно не просто «звучать разумно» — его нужно посчитать.

## task: first-tree | Первое дерево | base

Обучите `DecisionTreeClassifier(max_depth=3, random_state=0)` на признаках `distance_km`, `items`, `promised_min`, `hour` (час из `created`). Сохраните модель в `model` и долю правильных ответов на тех же данных в `train_acc` (3 знака).

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
X = ok[['distance_km', 'items', 'promised_min', 'hour']]
y = ok['actual_min'] > ok['promised_min']
m = need('model')
assert isinstance(m, _T) and m.max_depth == 3, 'model — DecisionTreeClassifier(max_depth=3, random_state=0).'
assert list(m.feature_names_in_) == ['distance_km', 'items', 'promised_min', 'hour'], f'Признаки модели: {list(m.feature_names_in_)}.'
w = round((_T(max_depth=3, random_state=0).fit(X, y).predict(X) == y).mean(), 3)
assert close(need('train_acc'), w), f'train_acc = {need("train_acc")}, а нужно {w}.'
```

### hint
`model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)`; `accuracy_score(y, model.predict(X))`.

### hint
Час — новый столбец: `ok["hour"] = ok["created"].dt.hour`, и не забудьте `parse_dates=["created"]` при чтении. Чтобы не было предупреждения про копию, сначала сделайте `ok = d[...].copy()`. Качество «на тех же данных» — это предсказание по тому же `X`, на котором учили.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
X = ok[["distance_km", "items", "promised_min", "hour"]]
y = ok["actual_min"] > ok["promised_min"]
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
train_acc = round(accuracy_score(y, model.predict(X)), 3)
```

### explain
0.798 — лучше базовой модели (0.760), но хуже правила «пеший» (0.865). Дерево выбирало вопросы только из четырёх числовых признаков: первым — обещанное время, потом позиции и расстояние. Типа курьера среди них нет, а без него главную причину опозданий не увидеть.

## task: new-orders | Предсказание для новых заказов | base

Обучите то же дерево и предскажите опоздание для трёх новых заказов. Сохраните **список** ответов `True/False` в `preds`. `predict` возвращает массив numpy, и его элементы печатаются как `np.True_` / `np.False_`; обычные `True/False` получаются через `bool(x)`.

| distance_km | items | promised_min | hour |
|---|---|---|---|
| 1.0 | 1 | 30 | 18 |
| 1.2 | 4 | 30 | 13 |
| 11.0 | 2 | 60 | 19 |

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[cols], ok["actual_min"] > ok["promised_min"])

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
cols = ['distance_km', 'items', 'promised_min', 'hour']
m = _T(max_depth=3, random_state=0).fit(ok[cols], ok['actual_min'] > ok['promised_min'])
new = _pd.DataFrame({'distance_km': [1.0, 1.2, 11.0], 'items': [1, 4, 2], 'promised_min': [30, 30, 60], 'hour': [18, 13, 19]})
want = [bool(x) for x in m.predict(new)]
got = [bool(x) for x in need('preds')]
assert got == want, f'preds = {got}, а нужно {want}.'
```

### hint
`new = pd.DataFrame({"distance_km": [...], "items": [...], "promised_min": [...], "hour": [...]})`, затем `list(model.predict(new))`.

### hint
Названия столбцов и их порядок в `new` должны совпадать с теми, на которых учили модель, иначе sklearn выдаст ошибку. `model.predict` возвращает массив numpy; список обычных True/False получится через `[bool(x) for x in model.predict(new)]`.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
model = DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[cols], ok["actual_min"] > ok["promised_min"])
new = pd.DataFrame({"distance_km": [1.0, 1.2, 11.0], "items": [1, 4, 2],
                    "promised_min": [30, 30, 60], "hour": [18, 13, 19]})
preds = [bool(x) for x in model.predict(new)]
```

### explain
Ответы: нет, да, да. Если напечатать `list(model.predict(new))`, увидите `np.False_` и `np.True_` — это те же False и True, только в «упаковке» numpy; `bool(x)` превращает их в обычные. Первый заказ — 1 позиция на 1 км: дерево идёт по ветке «обещали ≤ 37.5 минут, позиций ≤ 2.5» — вовремя. Второй — 4 позиции дальше 0.75 км при обещании 30 минут — опоздает. Третий — 11 км, обещали час, заказ в 19:00 — ветка «дальше 10.45 км и раньше 19:30» — опоздает. Если бы тот же заказ пришёл в 20:00, дерево сказало бы «вовремя»: в обучающих данных дальние заказы после 19:30 чаще приезжали в срок.

## task: frame | Две постановки одного запроса | base

Запрос логиста: «В момент передачи заказа курьеру хочу знать, опоздает ли он и на сколько минут». Для доставок с временем 1–299 минут сохраните:

- `leaks` — список столбцов `deliveries.csv`, которые становятся известны только **после** доставки (отсортированный по алфавиту);
- `y_cls` — целевой признак классификации: опоздает ли (True/False);
- `y_reg` — целевой признак регрессии: на сколько минут фактическое время больше обещанного (отрицательное — приехали раньше);
- `late_share` — долю опозданий (3 знака) и `late_median` — медиану опоздания в минутах **среди опоздавших** доставок.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
print(d.columns.tolist())

```

### check
```python
import pandas as _pd
_d = _pd.read_csv('deliveries.csv')
_ok = _d[_d['actual_min'].between(1, 299)]
lk = need('leaks', list)
if 'delivery_id' in lk:
    raise AssertionError('delivery_id известен сразу — это номер заказа. Он бесполезен как признак, но не утечка.')
assert sorted(lk) == ['actual_min', 'rating'], f'leaks = {lk}. Какие столбцы заполняются только после того, как курьер приехал?'
assert lk == sorted(lk), 'Отсортируйте список leaks по алфавиту: sorted(...).'
yc, yr = need('y_cls', _pd.Series), need('y_reg', _pd.Series)
assert len(yc) == len(_ok) and len(yr) == len(_ok), f'Целевые признаки — по {len(_ok)} доставкам с временем 1–299 минут.'
assert yc.dtype == bool and yc.sum() == (_ok['actual_min'] > _ok['promised_min']).sum(), 'y_cls — True, если actual_min > promised_min.'
_r = _ok['actual_min'] - _ok['promised_min']
if (yr == -_r).all():
    raise AssertionError('y_reg с обратным знаком: вычитайте обещанное из фактического, чтобы опоздание было положительным.')
assert (yr == _r).all(), 'y_reg — actual_min − promised_min.'
assert close(need('late_share'), round((_r > 0).mean(), 3)), f'late_share = {need("late_share")}. Доля True в y_cls, 3 знака.'
lm = need('late_median')
if close(lm, _r.median()):
    raise AssertionError(f'late_median = {lm} — это медиана по всем доставкам. Нужна медиана только среди опоздавших: y_reg[y_cls].')
assert close(lm, _r[_r > 0].median()), f'late_median = {lm}. Медиана y_reg среди строк, где y_cls == True.'
```

### hint
Пройдите по столбцам и для каждого спросите: «знаю ли я это, когда курьер забирает заказ?» Два столбца появляются только после доставки.

### hint
`y_cls = ok["actual_min"] > ok["promised_min"]`, `y_reg = ok["actual_min"] - ok["promised_min"]`.

### hint
Медиана среди опоздавших — фильтр по логической маске: `y_reg[y_cls].median()`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
leaks = sorted(["actual_min", "rating"])
y_cls = ok["actual_min"] > ok["promised_min"]
y_reg = ok["actual_min"] - ok["promised_min"]
late_share = round(y_cls.mean(), 3)
late_median = y_reg[y_cls].median()
```

### explain
Утечек две: фактическое время и оценка гостя — обе появляются, когда заказ уже доставлен. Опаздывает 24 % заказов, медиана опоздания среди опоздавших — 7 минут: половина из них опаздывает на 7 минут и больше. Это подсказка для решения: если купон дают «за любое опоздание», классификации достаточно; если гостю показывают честное время или купон зависит от величины опоздания — нужна регрессия. Частая ошибка — медиана `y_reg` по всем доставкам (−8 минут): она отвечает на вопрос «насколько раньше обещанного приезжает типичная доставка», а не «насколько опаздывают опоздавшие».

## task: leak | Утечка | plus

Обучите дерево глубины 3 дважды: на признаках `distance_km`, `items`, `promised_min` (`acc_fair`) и на них же плюс `actual_min` (`acc_leak`). Обе доли — 3 знака. В `gap` — разница (п.п., 1 знак).

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv')
ok = d[d['actual_min'].between(1, 299)]
y = ok['actual_min'] > ok['promised_min']
f = ['distance_km', 'items', 'promised_min']
a = round((_T(max_depth=3, random_state=0).fit(ok[f], y).predict(ok[f]) == y).mean(), 3)
b = round((_T(max_depth=3, random_state=0).fit(ok[f + ['actual_min']], y).predict(ok[f + ['actual_min']]) == y).mean(), 3)
assert close(need('acc_fair'), a) and close(need('acc_leak'), b), f'acc_fair, acc_leak = {need("acc_fair")}, {need("acc_leak")}, а нужно {a}, {b}.'
assert close(need('gap'), round((b - a) * 100, 1)), f'gap = {need("gap")}. Это (acc_leak − acc_fair) · 100, 1 знак.'
```

### hint
Список признаков с утечкой: `cols + ["actual_min"]`. `random_state=0` в обоих деревьях.

### hint
Обе модели сравниваются на своих же признаках: `fair` предсказывает по `ok[cols]`, `leak` — по `ok[cols + ["actual_min"]]`. Разница в п.п. — `(acc_leak - acc_fair) * 100`. Ожидайте, что вторая модель окажется намного точнее: зная фактическое время, «предсказать» опоздание легко — именно это и называется утечкой.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)]
y = ok["actual_min"] > ok["promised_min"]
cols = ["distance_km", "items", "promised_min"]
fair = DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[cols], y)
leak = DecisionTreeClassifier(max_depth=3, random_state=0).fit(ok[cols + ["actual_min"]], y)
acc_fair = round(accuracy_score(y, fair.predict(ok[cols])), 3)
acc_leak = round(accuracy_score(y, leak.predict(ok[cols + ["actual_min"]])), 3)
gap = round((acc_leak - acc_fair) * 100, 1)
```

### explain
Модель с утечкой почти идеальна: зная фактическое время и обещание, «предсказать» опоздание тривиально. Но в момент заказа фактического времени нет, и такая модель бесполезна. Подозрительно хорошее качество — первый признак утечки.

## task: mae-base | Регрессия: базовая модель | plus

Для регрессии (предсказать `actual_min` — минуты) самая простая модель — всегда отвечать средним. Сохраните `mae_mean` — среднюю абсолютную ошибку такой модели (среднее модулей «факт − прогноз», 2 знака) и `mae_median` — то же, если отвечать медианой.

### starter
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]

```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv')
t = d.loc[d['actual_min'].between(1, 299), 'actual_min']
assert close(need('mae_mean'), round((t - t.mean()).abs().mean(), 2)), f'mae_mean = {need("mae_mean")}. Среднее модулей (t − t.mean()), 2 знака.'
assert close(need('mae_median'), round((t - t.median()).abs().mean(), 2)), f'mae_median = {need("mae_median")}. То же, но вместо среднего — медиана t.'
```

### hint
`(t - t.mean()).abs().mean()`.

### hint
Ряд — только доставки с временем 1–299 минут: `t = d.loc[d["actual_min"].between(1, 299), "actual_min"]`. Для медианы та же формула с `t.median()`. Ожидайте, что медиана даст ошибку чуть меньше: среднее абсолютное отклонение минимально именно для медианы.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv")
t = d.loc[d["actual_min"].between(1, 299), "actual_min"]
mae_mean = round((t - t.mean()).abs().mean(), 2)
mae_median = round((t - t.median()).abs().mean(), 2)
```

### explain
Медиана даёт меньшую среднюю абсолютную ошибку — это её математическое свойство. «Ошибаемся в среднем примерно на 8 минут, просто отвечая медианой» — планка, которую должна побить модель в уроке «Регрессия: сколько минут».

## task: first-split | Первый вопрос дерева | star

Обучите `DecisionTreeClassifier(max_depth=1, random_state=0)` на признаках `distance_km`, `items`, `promised_min`, `hour`. Дерево глубины 1 задаёт ровно один вопрос. Сохраните `feature` — название признака в этом вопросе, `threshold` — порог (2 знака) и `acc` — долю правильных ответов (3 знака).

### starter
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]

```

### check
```python
import pandas as _pd
from sklearn.tree import DecisionTreeClassifier as _T
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
ok = d[d['actual_min'].between(1, 299)].copy()
ok['hour'] = ok['created'].dt.hour
cols = ['distance_km', 'items', 'promised_min', 'hour']
y = ok['actual_min'] > ok['promised_min']
m = _T(max_depth=1, random_state=0).fit(ok[cols], y)
assert need('feature') == cols[m.tree_.feature[0]], f'feature = {need("feature")!r} — это не тот признак, о котором спрашивает корень дерева.'
assert close(need('threshold'), round(m.tree_.threshold[0], 2)), f'threshold = {need("threshold")}. Порог корня — model.tree_.threshold[0], 2 знака.'
assert close(need('acc'), round((m.predict(ok[cols]) == y).mean(), 3)), f'acc = {need("acc")}. Доля правильных ответов дерева глубины 1 на тех же данных, 3 знака.'
```

### hint
Устройство дерева — в `model.tree_`: `model.tree_.feature[0]` — номер признака в корне, `model.tree_.threshold[0]` — порог.

### hint
Номер превращается в название через список: `cols[model.tree_.feature[0]]`.

### solution
```python
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["hour"] = ok["created"].dt.hour
cols = ["distance_km", "items", "promised_min", "hour"]
y = ok["actual_min"] > ok["promised_min"]
model = DecisionTreeClassifier(max_depth=1, random_state=0).fit(ok[cols], y)
feature = cols[model.tree_.feature[0]]
threshold = round(model.tree_.threshold[0], 2)
acc = round((model.predict(ok[cols]) == y).mean(), 3)
```

### explain
Дерево само выбрало вопрос «обещали ли 30 минут?» (порог 37.5 отделяет 30 минут от 45 и 60) — среди доставок с обещанием 30 минут опаздывает 45 %, среди остальных — 12 %. Но доля правильных ответов не выросла и равна базовой: в обеих ветках опозданий меньше половины, и дерево в обеих отвечает «вовремя». Вопрос хорошо разделил доставки по риску, а ответы остались прежними. Поэтому одной accuracy мало — другие метрики будут в главе 7.
