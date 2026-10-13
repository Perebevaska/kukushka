---
title: "Проект: три месяца продаж"
lead: "Финал главы. Сеть кофеен просит разобрать осень. Вместо «посчитаем всё подряд» мы заранее формулируем шесть гипотез, решаем, какая цифра подтвердит или опровергнет каждую, и проверяем их на pandas — с проверкой на каждом шаге. В конце — таблица вердиктов и проект, сданный блокнотом по шаблону."
files: [orders_3m.csv, shops.csv, menu.csv]
recap:
  - "Сначала гипотезы и правила решения, потом расчёт: «гипотеза → метрика → порог → вердикт». Порог назначают до того, как увидели цифру."
  - "Начинайте с загрузки и соединения со справочниками — с `validate` и сверкой числа строк."
  - "Помесячные KPI — `groupby` по `dt.to_period(\"M\")` с именованными агрегатами; рост раскладывают на заказы × средний чек."
  - "Сравнения «до и после» и «одни против других» — это группировка по признаку и доля/разница в процентах. Совпадение во времени — ещё не причина."
  - "Сводная таблица «день недели × час» — быстрый способ найти пики нагрузки."
  - "«Не подтвердилась» — тоже результат: о нём пишут в выводе так же честно, как о находках."
  - "Проект сдаётся блокнотом по шаблону: разделы по гипотезам, markdown-вывод после каждого, общий вывод; перед сдачей — Restart & Run All и `check_notebook.py`."
---

## Задача

> Подведи итоги осени по сети: динамику по месяцам, сравнение городов и кофеен с учётом их размера, эффект сезонного напитка (он появился в ноябре), разницу между гостями с картой и без, часы пик и маржу по категориям. В конце — короткая сводка ключевых цифр.

Данные — те же три файла: заказы `orders_3m.csv`, кофейни `shops.csv`, меню `menu.csv`.

## Гипотезы вместо «посчитаем всё»

Зачем: запрос звучит как список из шести тем. Можно посчитать по каждой десяток таблиц — и утонуть в них. Аналитик поступает иначе: превращает каждую тему в **гипотезу** — утверждение, которое данные могут подтвердить или опровергнуть, — и заранее решает, какая цифра это покажет.

::: tip Аналогия
Гипотеза с порогом — как ставка до начала матча: «наши выиграют с разницей в два гола». Если сформулировать ставку после матча, она всегда «сыграет». Так и с данными: порог, придуманный после того, как увидели цифру, подгоняется под цифру. Где аналогия хромает: в анализе «проигранная ставка» — не потеря, а полноценный результат.
:::

Хорошая гипотеза состоит из трёх частей:

1. **Утверждение** — конкретное и проверяемое: «гости с картой тратят за заказ больше», а не «карта — это хорошо».
2. **Метрика** — какое число её проверяет: разница среднего чека с картой и без, в процентах.
3. **Правило решения** — порог, назначенный заранее: «подтвердилась, если разница не меньше 5 %».

Игрушечный пример. Гипотеза: «гости с картой тратят больше». Порог — 5 %. Пусть средний чек с картой 315 ₽, без карты — 300 ₽. Разница: (315 − 300) / 300 = 0.05, то есть 5 % — ровно на пороге, гипотеза подтвердилась. При 309 ₽ разница была бы 3 % — «не подтвердилась», хотя чек с картой и выше. Почему порог не ноль: небольшая разница в среднем бывает и случайно. Честно отделять случайность от эффекта мы научимся в главе 5, а пока порог — договорённость о том, какая разница вообще интересна бизнесу.

::: figure hypothesis-flow
Гипотеза как цепочка из пяти шагов. Первые три записывают в блокнот до расчёта, поэтому вердикт следует из правила, а не из впечатления от цифры. Внизу — игрушечный пример: при чеке 315 ₽ гипотеза подтвердилась, при 309 ₽ — нет.
:::

Шесть гипотез проекта и правила решения:

| | гипотеза | шаг | метрика | подтвердилась, если |
|---|---|---|---|---|
| H1 | Сеть растёт: каждый месяц выручка выше предыдущего | 2 | рост выручки месяц к месяцу | оба прироста больше 0 |
| H2 | Чем больше мест, тем больше выручка: лидер по выручке — самая большая кофейня | 3 | кофейня с максимумом мест и лидер по выручке | это одна и та же кофейня |
| H3 | Рост ноября дал сезонный напиток | 4 | доля напитка в выручке ноября, изменение чека | наблюдением не проверить — см. ниже |
| H4 | Гости с картой тратят за заказ больше | 5 | разница среднего чека, % | разница не меньше 5 % |
| H5 | Пик нагрузки — утро выходных | 6 | клетка «день × час» с максимумом заказов | суббота или воскресенье, до 12:00 |
| H6 | «Не кофе» выгоднее кофе по марже | 7 | разница маржи, процентные пункты | «не кофе» выше на 3 п. п. и больше |

H3 — особая: это гипотеза о **причине**. Данные покажут, что напиток продавался и чек вырос одновременно, но не докажут, что одно вызвало другое. Её вердикт в проекте — «не опровергнута, нужен эксперимент» (глава 5). Остальные пять проверяются правилом, и в шаге 8 вы соберёте по ним таблицу вердиктов.

::: quiz
Какая формулировка — проверяемая гипотеза для этого проекта?

- [x] «Средний чек заказов с картой лояльности минимум на 5 % выше, чем без карты»
  > Есть метрика (средний чек), сравнение (с картой против без) и порог (5 %). По данным можно однозначно сказать «да» или «нет».
- [ ] «Карта лояльности полезна для сети»
  > «Полезна» — не метрика. Непонятно, какое число подтвердит или опровергнет такое утверждение.
- [ ] «Посмотрим, как ведут себя гости с картой»
  > Это тема исследования, а не гипотеза: в ней нет утверждения, которое могло бы оказаться ложным.
- [ ] «Гости с картой лучше»
  > Лучше по чему — по чеку, частоте, марже? Без метрики и порога любой результат можно истолковать как подтверждение.
:::

::: quiz
Выручка в ноябре выросла. Какой вопрос нужно задать первым, прежде чем хвалить кофейни?

- [x] Из чего сложился рост: больше заказов, выше средний чек или новые позиции и кофейни?
  > Рост раскладывают на составляющие: так видно, что сработало, а что — разовый эффект вроде сезонного напитка.
- [ ] Какая кофейня заработала больше всех?
  > Полезная цифра, но она не объясняет, откуда взялся рост сети.
- [ ] Можно ли округлить выручку до тысяч?
  > Оформление важно, но сначала смысл.
- [ ] Сколько строк в выгрузке?
  > Объём данных проверяют при загрузке, причину роста он не объясняет.
:::

## Разберём вместе: из чего сложился рост ноября

Шаг 2 покажет, что выручка ноября выросла к октябрю на 9.6 %. Директор спросит: «за счёт чего?» Выручка = число заказов × средний чек, поэтому рост раскладывается на два множителя:

| | октябрь | ноябрь | изменение |
|---|---|---|---|
| заказов | 700 | 738 | 738 / 700 = **1.054** (+5.4 %) |
| средний чек, ₽ | 333.9 | 347.2 | 347.2 / 333.9 = **1.040** (+4.0 %) |
| выручка, ₽ | 233 756 | 256 198 | 1.054 × 1.040 ≈ **1.096** (+9.6 %) |

::: figure growth-decomp
Выручка — это площадь прямоугольника «заказы × средний чек». Октябрь — серый прямоугольник, ноябрь — он же с двумя полосами и уголком. Полоса справа — рубли от новых заказов, полоса сверху — от подорожания чека, уголок — от обоих сразу. Вместе они дают 22 442 ₽ прироста.
:::

1. Примерно половина роста — больше заказов, половина — дороже чек.
2. Рост чека совпал с появлением сезонного напитка — он стоит дороже обычного (шаг 4 покажет его долю: около 16 % выручки ноября).
3. Но совпадение во времени — не доказательство: в ноябре и без нового напитка мог вырасти спрос на крупные стаканы. Поэтому H3 и получает вердикт «нужен эксперимент» (глава 5).

Что получилось: одно число «+9.6 %» превратилось в два понятных рычага. Такая декомпозиция — одна строка кода на шаге 2, а вывод для директора становится содержательным.

::: warn Типичные ошибки проекта
- **Порог придумали после расчёта.** «Разница 2.4 % — ну, это заметно» — так подтверждается любая гипотеза. Правило решения записывают в блокнот до расчёта.
- **«Не подтвердилась» выкинули из отчёта.** Опровергнутая гипотеза экономит деньги: не нужно запускать акцию для владельцев карт ради чека.
- **Не проверили строки после соединения.** Дубль в справочнике размножит заказы и выручку.
- **Сравнение кофеен в рублях без размера.** Большая кофейня всегда «лучше» маленькой; честнее — выручка на место.
- **Эффект сезонного напитка = вся разница ноября.** Ноябрь отличается от октября не только меню.
- **Средний чек гостей без карты как «средний гость».** Без карты — это заказы, а не гости: один человек может быть и там, и там.
:::

## Сдайте проект блокнотом

Шаги в браузере ниже — тренировка: каждый проверяется сразу. Но настоящий проект аналитика — это блокнот-отчёт, который можно открыть, перезапустить и прочитать. Поэтому после шагов соберите проект в Jupyter.

1. **Скачайте шаблон** [project-template.ipynb](../notebooks/project-template.ipynb) в папку проекта из урока про uv — рядом с папкой `data/`, где лежат три файла. Переименуйте его, например, в `autumn.ipynb`.
2. **Поправьте шаблон под свой проект.** Шаблон один на весь курс, в том числе на главы с моделями машинного обучения, поэтому в нём есть лишнее для этого проекта. Поправить нужно ровно три места:
   - в первой ячейке — строки со словом `sklearn` (библиотека для моделей: `import sklearn` и четыре строки `from sklearn…`) и `sklearn` из списка в последней строке, чтобы осталось `for lib in (pd, np, matplotlib):`. Моделей в проекте нет, и в окружении проекта этой библиотеки нет;
   - там же замените `DATA = Path('../data')` на `DATA = Path('data')`: шаблон рассчитан на папку курса, а у вас `data/` лежит рядом с блокнотом;
   - в разделе «4. Анализ и модели» — две кодовые ячейки примера: график «по формату точки» и ячейку с `train_test_split`. Это образец на чужом файле `daily_sales.csv`, на их место встанет ваш анализ.

   Остальные ячейки — заготовки с пометками ✎, их не удаляют, а заполняют.
3. **Заполните разделы шаблона.** Цель — шесть гипотез с правилами решения из таблицы выше. Данные — загрузка и проверка соединения (шаг 1). Анализ — по разделу `##` на каждую гипотезу, например `## 4.1. H1: сеть растёт`: скрипт самопроверки ищет вывод после каждого `##`, а подзаголовки `###` он не проверяет. Все пометки ✎ замените своим текстом.
4. **После каждого раздела — markdown-вывод с вердиктом:** «H4 не подтвердилась: чек с картой выше на 2.4 %, порог — 5 %». Цифры — из переменных, как в уроке про Jupyter.
5. **Общий вывод** — таблица вердиктов (шаг 8) и три части: что сделали, что нашли, что предлагаем.
6. **Самопроверка.** **Kernel → Restart Kernel and Run All Cells**, затем скрипт [check_notebook.py](../notebooks/check_notebook.py) — положите его рядом с блокнотом и запустите в терминале:

   ```sh
   uv run python check_notebook.py autumn.ipynb
   ```

   Скрипт выполняет блокнот с чистого ядра, как ревьюер, и ищет то же, что вы искали руками в уроке про Jupyter: ошибки, абсолютные пути, закомментированный код, разделы без вывода. Исправьте всё, что он нашёл, и запустите снова.

   **Необязательно: сверка чисел.** Скрипт умеет сверить и сами числа с эталонами шагов. Для этого ему нужны файлы проверок курса — они лежат в архиве курса, том самом, который запускают файлами «Курс-Windows.bat» или «Курс.command». Если вы открываете курс из такой папки, назовите переменные как в шагах выше и запустите:

   ```sh
   uv run python check_notebook.py autumn.ipynb --project ch02/09-project --course ПАПКА_КУРСА
   ```

   `ПАПКА_КУРСА` — путь к этой папке, например `~/Downloads/ds-course`. Если вы учитесь на сайте и архива у вас нет, пропустите этот шаг: без `--project` скрипт проверит устройство блокнота, а числа вы уже сверили в задачах на сайте.
7. **В портфолио.** В следующем уроке вы научитесь выкладывать проект в git и на GitHub — этот блокнот станет первым репозиторием портфолио.

::: note Сделайте в своём блокноте
1. Пройдите шаги 1–8 в браузере.
2. Перенесите решения в шаблон: один шаг — один раздел, после раздела — вердикт гипотезы.
3. Restart & Run All, затем `check_notebook.py` — до «чистого» результата.
4. Перечитайте только markdown-ячейки: понятен ли из них весь проект без кода?
:::

Начиная со второго шага, перед задачей курс сам собирает таблицу `full` — заказы, соединённые со справочниками, с настоящей датой в `datetime`. Так ошибка на одном шаге не мешает следующим.

::: figure project-flow
Путь проекта целиком: три файла соединяются в `full` (шаг 1), по ней проверяются шесть гипотез (шаги 2–7), из результатов собираются вердикты и сводка (шаги 8–9). Затем всё переносится в блокнот по шаблону и проходит самопроверку.
:::

::: tip
Это повторение всей главы. В подсказках указано, на какой урок опирается шаг. Если что-то забылось — шпаргалка в шапке и поиск (<kbd class="mod">Ctrl</kbd>+<kbd>K</kbd>).
:::

## Практика

## task: load | Шаг 1. Загрузка и соединение | base

Загрузите три файла (у заказов `datetime` — сразу датой), присоедините к заказам кофейни по `shop_id` и меню по `drink` (LEFT JOIN с `validate="many_to_one"`). Результат — `full`. Сохраните `same_rows = True`, если строк столько же, сколько заказов.

### starter
```python
import pandas as pd

```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
f = need('full', _pd.DataFrame)
assert _pd.api.types.is_datetime64_any_dtype(f['datetime']), 'datetime должен быть датой: parse_dates=["datetime"].'
for c in ('city', 'seats', 'category', 'cost_s'):
    assert c in f.columns, f'В full нет столбца {c} — присоедините оба справочника.'
assert len(f) == len(_f), f'В full {len(f)} строк, а заказов {len(_f)}.'
assert need('same_rows') == True, 'same_rows должно быть True.' 
```

### hint
Уроки «Соединения: JOIN и UNION» и «Даты и время»: `pd.read_csv(..., parse_dates=["datetime"])`, затем два `merge` подряд.

### hint
`full = df.merge(shops, on="shop_id", how="left", validate="many_to_one").merge(menu, on="drink", how="left", validate="many_to_one")`; `same_rows = len(full) == len(df)`.

### solution
```python
import pandas as pd
orders = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
shops = pd.read_csv("shops.csv")
menu = pd.read_csv("menu.csv")
full = (orders.merge(shops, on="shop_id", how="left", validate="many_to_one")
              .merge(menu, on="drink", how="left", validate="many_to_one"))
same_rows = len(full) == len(orders)
```

### explain
Строк после двух соединений столько же, сколько заказов, — справочники без дублей. Эту проверку стоит оставлять в коде навсегда: справочники меняют другие люди.

## task: monthly | Шаг 2. KPI по месяцам | base

Гипотеза H1: выручка растёт каждый месяц. Соберите `monthly` — таблицу по месяцам (`dt.to_period("M")`) со столбцами `revenue`, `orders`, `avg_check` (округлите до 1 знака) и `clients` (разных гостей с картой). Сохраните `nov_vs_oct` — рост выручки ноября к октябрю в процентах с одним знаком.

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
full.head(3)
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
m = need('monthly', _pd.DataFrame)
assert list(m.columns) == ['revenue', 'orders', 'avg_check', 'clients'], f'Столбцы: {list(m.columns)}.'
g = _f.groupby(_f['datetime'].dt.to_period('M'))
assert [int(x) for x in m['revenue']] == [int(x) for x in g['amount'].sum()], 'revenue не совпадает.'
assert [int(x) for x in m['clients']] == [int(x) for x in g['client_id'].nunique()], 'clients не совпадает.'
r = g['amount'].sum().tolist()
assert close(need('nov_vs_oct'), round((r[2] - r[1]) / r[1] * 100, 1)), f'nov_vs_oct = {need("nov_vs_oct")}.' 
```

### hint
Урок «Группировки: GROUP BY и HAVING» (agg с именами) и урок «Даты и время» (`to_period`): `full.groupby(full["datetime"].dt.to_period("M")).agg(...)`.

### hint
Разных гостей — `clients=("client_id", "nunique")`: пустые номера `nunique` не считает.

### hint
Выручка ноября и октября — `monthly["revenue"].iloc[2]` и `.iloc[1]`.

### solution
```python
import pandas as pd
monthly = full.groupby(full["datetime"].dt.to_period("M")).agg(
    revenue=("amount", "sum"),
    orders=("order_id", "count"),
    avg_check=("amount", "mean"),
    clients=("client_id", "nunique"),
)
monthly["avg_check"] = monthly["avg_check"].round(1)
r = monthly["revenue"]
nov_vs_oct = round((r.iloc[2] - r.iloc[1]) / r.iloc[1] * 100, 1)
monthly
```

### explain
Выручка: 220 тыс. в сентябре, 234 тыс. в октябре, 256 тыс. в ноябре; прирост +6.1 % и +9.6 % — оба больше нуля, **H1 подтвердилась**. Число гостей с картой почти не меняется (201–214): рост дают не новые гости, а заказы и чек. Типичная ошибка — делить на ноябрь, а не на октябрь: база роста — прошлый период.

## task: shops | Шаг 3. Кофейни с учётом размера | base

Гипотеза H2: чем больше мест, тем больше выручка. Здесь нужны две метрики с разными ролями:

- **вердикт H2** выносится по правилу из таблицы гипотез: совпадает ли кофейня с наибольшим числом мест с лидером по выручке. Само правило вы примените в шаге 8, а здесь посчитайте `leader_by_revenue`;
- **выручка на место** `per_seat` — не для вердикта, а для вывода в блокноте: какая кофейня лучше использует свои места, если сравнивать честно, с поправкой на размер.

Соберите `by_shop` — таблицу по кофейням (`shop_id` в индексе) со столбцами `city`, `revenue`, `seats`, `per_seat` (выручка на место, округлить до целого), отсортированную по `per_seat` по убыванию. Сохраните `leader` — кофейню-лидера по выручке на место и `leader_by_revenue` — лидера по просто выручке.

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
full.head(3)
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
b = need('by_shop', _pd.DataFrame)
assert list(b.columns) == ['city', 'revenue', 'seats', 'per_seat'], f'Столбцы: {list(b.columns)}.'
g = _f.groupby('shop_id').agg(revenue=('amount', 'sum'), seats=('seats', 'first'))
ps = (g['revenue'] / g['seats']).round()
assert b.index.tolist() == ps.sort_values(ascending=False).index.tolist(), 'Порядок кофеен не совпадает с сортировкой по per_seat.'
assert need('leader') == ps.idxmax() and need('leader_by_revenue') == g['revenue'].idxmax(), f'leader = {need("leader")}, leader_by_revenue = {need("leader_by_revenue")}.' 
```

### hint
Город и места у кофейни одни на все её заказы: в `agg` берите `("city", "first")` и `("seats", "first")`.

### hint
Затем `by_shop["per_seat"] = (by_shop["revenue"] / by_shop["seats"]).round()` и сортировка.

### solution
```python
import pandas as pd
by_shop = full.groupby("shop_id").agg(
    city=("city", "first"),
    revenue=("amount", "sum"),
    seats=("seats", "first"),
)
by_shop["per_seat"] = (by_shop["revenue"] / by_shop["seats"]).round()
by_shop = by_shop.sort_values("per_seat", ascending=False)
leader = by_shop.index[0]
leader_by_revenue = by_shop["revenue"].idxmax()
by_shop
```

### explain
Самая большая кофейня — KZN-1 (30 мест), а лидер и по выручке, и по выручке на место — PRM-1 (24 места, 7 757 ₽ на место): **H2 не подтвердилась**. Число мест — не главный рычаг; почему впереди PRM-1 (она старейшая в сети, открыта в 2021 году) — вопрос для новой гипотезы. На других данных лидеры по выручке и по выручке на место часто расходятся — поэтому считаем обе метрики, а какая важнее, зависит от вопроса бизнеса.

## task: seasonal | Шаг 4. Сезонный напиток | base

Гипотеза H3: рост ноября дал сезонный напиток. Напиток появился в ноябре. Посчитайте `seasonal_share` — его долю в выручке ноября (в процентах, 1 знак) и `check_change` — изменение среднего чека ноября к октябрю в процентах (1 знак).

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
full.head(3)
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
nov = _f[_f['datetime'].dt.month == 11]; octo = _f[_f['datetime'].dt.month == 10]
assert close(need('seasonal_share'), round(nov[nov['drink'] == 'Сезонный']['amount'].sum() / nov['amount'].sum() * 100, 1)), f'seasonal_share = {need("seasonal_share")}.'
assert close(need('check_change'), round((nov['amount'].mean() - octo['amount'].mean()) / octo['amount'].mean() * 100, 1)), f'check_change = {need("check_change")}.' 
```

### hint
Урок «Даты и время»: отберите ноябрь и октябрь по `dt.month`.

### hint
Доля — выручка «Сезонного» в ноябре, делённая на всю выручку ноября.

### solution
```python
import pandas as pd
nov = full[full["datetime"].dt.month == 11]
oct_ = full[full["datetime"].dt.month == 10]
seasonal_share = round(nov.loc[nov["drink"] == "Сезонный", "amount"].sum() / nov["amount"].sum() * 100, 1)
check_change = round((nov["amount"].mean() - oct_["amount"].mean()) / oct_["amount"].mean() * 100, 1)
```

### explain
Сезонный напиток — 15.6 % выручки ноября, средний чек вырос на 4 %. Новинка заметна, но часть её продаж могла «переехать» с других напитков: чтобы понять, сколько она добавила сверху, нужно смотреть, упали ли продажи остального меню. Вердикт по H3 — **не опровергнута, нужен эксперимент**: данные показывают совпадение во времени, но не причину.

## task: loyalty | Шаг 5. Гости с картой и без | base

Гипотеза H4: гости с картой тратят за заказ больше (порог — 5 %). Посчитайте `avg_card` и `avg_no_card` — средний чек заказов с картой лояльности и без (1 знак), и `diff_pct` — на сколько процентов чек с картой выше (или ниже) чека без карты, с одним знаком.

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
full.head(3)
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
c = _f['client_id'].notna()
a, b = round(_f.loc[c, 'amount'].mean(), 1), round(_f.loc[~c, 'amount'].mean(), 1)
assert close(need('avg_card'), a) and close(need('avg_no_card'), b), f'avg_card = {need("avg_card")}, avg_no_card = {need("avg_no_card")}, а нужно {a} и {b}.'
want = round((_f.loc[c, 'amount'].mean() - _f.loc[~c, 'amount'].mean()) / _f.loc[~c, 'amount'].mean() * 100, 1)
assert close(need('diff_pct'), want, 0.11), f'diff_pct = {need("diff_pct")}, а нужно около {want}.' 
```

### hint
Маска «с картой» — `full["client_id"].notna()`, без карты — `~маска` (урок «Выбор столбцов и строк: SELECT и WHERE»).

### hint
Средний чек каждой группы — `full.loc[маска, "amount"].mean()`.

### solution
```python
import pandas as pd
card = full["client_id"].notna()
avg_card = round(full.loc[card, "amount"].mean(), 1)
avg_no_card = round(full.loc[~card, "amount"].mean(), 1)
diff_pct = round((full.loc[card, "amount"].mean() - full.loc[~card, "amount"].mean()) / full.loc[~card, "amount"].mean() * 100, 1)
```

### explain
Чек с картой выше всего на 2.4 % — меньше порога 5 %, назначенного заранее: **H4 не подтвердилась**. Это тоже результат: на этих данных карта лояльности почти не меняет размер чека, и запускать акцию для владельцев карт ради чека не стоит. Честно сообщать, что эффекта нет, так же важно, как находить эффекты. Случайна ли и эта небольшая разница, научимся проверять в главе 5.

## task: heatmap | Шаг 6. Часы пик | plus

Гипотеза H5: пик нагрузки — утро выходных. Постройте сводную таблицу `load` — число заказов: строки — день недели (`dt.weekday`, 0 — понедельник), столбцы — час (`dt.hour`). Найдите `peak` — кортеж `(день недели, час)` с наибольшим числом заказов.

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
full.head(3)
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
p = _pd.pivot_table(_f, index=_f['datetime'].dt.weekday, columns=_f['datetime'].dt.hour, values='order_id', aggfunc='count')
l = need('load', _pd.DataFrame)
assert l.shape == p.shape, f'Размер load {l.shape}, а нужно {p.shape}: 7 дней × часы работы.'
s = p.stack()
assert tuple(int(x) for x in need('peak')) == tuple(int(x) for x in s.idxmax()), f'peak = {need("peak")}, а нужно {s.idxmax()}.' 
```

### hint
Нужна сводная таблица «день недели × час» со счётом заказов — как в уроке «Сводные таблицы: широкий и длинный формат». День недели и час берутся из даты через `.dt`. Пик — ячейка с наибольшим значением.

### hint
`pd.pivot_table(full, index=full["datetime"].dt.weekday, columns=full["datetime"].dt.hour, values="order_id", aggfunc="count")`. Затем `load.stack()` превращает таблицу в Series с парой (строка, столбец) в индексе — и `idxmax()` даст ту самую пару.

### hint
```python
load = pd.pivot_table(full, index=..., columns=..., values="order_id", aggfunc="count")
peak = load.stack().idxmax()
peak
```
Если увидите `(np.int32(5), np.int32(9))` — всё верно: это просто числа 5 и 9 в формате numpy, библиотеки, на которой построен pandas.

### solution
```python
import pandas as pd
load = pd.pivot_table(full, index=full["datetime"].dt.weekday, columns=full["datetime"].dt.hour,
                      values="order_id", aggfunc="count")
peak = load.stack().idxmax()
load
```

### explain
Пик — суббота в 9 утра: 56 заказов за осень в одну и ту же «клетку», **H5 подтвердилась**. Вывод `(np.int32(5), np.int32(9))` пугаться не стоит: pandas хранит числа в формате numpy, и `np.int32(5)` — это обычная пятёрка. В сравнениях (`peak[0] in (5, 6)`) она ведёт себя как число, а `int(peak[0])` превратит её в привычный вид. Сводная таблица «день × час» — готовое расписание смен: где пик, туда второго бариста.

## task: margin | Шаг 7. Маржа по категориям | plus

Гипотеза H6: «не кофе» выгоднее кофе по марже (порог — 3 процентных пункта). Себестоимость в меню — для размера S; для M она в 1,25 раза больше, для L — в 1,5. Посчитайте `margin` — Series «категория → маржа в процентах» (`(выручка − себестоимость) / выручка × 100`, 1 знак).

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
full.head(3)
SIZE_K = {"S": 1.0, "M": 1.25, "L": 1.5}
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
_f['cost'] = _f['cost_s'] * _f['size'].map({'S': 1.0, 'M': 1.25, 'L': 1.5}) * _f['qty']
g = _f.groupby('category')[['amount', 'cost']].sum()
want = ((g['amount'] - g['cost']) / g['amount'] * 100).round(1)
m = need('margin')
assert {k: round(float(v), 1) for k, v in dict(m).items()} == want.to_dict(), f'margin = {dict(m)}, а нужно {want.to_dict()}.' 
```

### hint
Урок «Соединения: JOIN и UNION», задача про маржу: сначала столбец `cost`, потом суммы двух столбцов по категориям.

### hint
`full["cost"] = full["cost_s"] * full["size"].map({"S": 1, "M": 1.25, "L": 1.5}) * full["qty"]`; затем `g = full.groupby("category")[["amount", "cost"]].sum()`.

### solution
```python
import pandas as pd
SIZE_K = {"S": 1.0, "M": 1.25, "L": 1.5}
full["cost"] = full["cost_s"] * full["size"].map(SIZE_K) * full["qty"]
g = full.groupby("category")[["amount", "cost"]].sum()
margin = ((g["amount"] - g["cost"]) / g["amount"] * 100).round(1)
margin
```

### explain
Маржа у категорий почти одинаковая: кофе — 75.9 %, не кофе — 77.3 %, разница по неокруглённым значениям — около 1.35 п. п. (77.29 − 75.94), меньше порога в 3 п. п.: **H6 не подтвердилась**. Значит, продвигать «не кофе» ради маржи особого смысла нет; важнее, какие конкретные напитки внутри категорий выгоднее (урок «Соединения: JOIN и UNION»).

## task: verdicts | Шаг 8. Таблица вердиктов | plus

Соберите итог проекта — словарь `verdicts` с ключами `"H1"`, `"H2"`, `"H4"`, `"H5"`, `"H6"` и значениями `"подтвердилась"` или `"не подтвердилась"`. Вердикт выносите **правилом из таблицы гипотез**, а не вписывайте руками:

- H1 — оба прироста выручки месяц к месяцу больше 0;
- H2 — кофейня с наибольшим числом мест (`seats`) — она же лидер по выручке;
- H4 — средний чек с картой выше чека без карты не меньше чем на 5 %;
- H5 — пиковая клетка «день недели × час» приходится на субботу или воскресенье (`weekday` 5 или 6) и час меньше 12;
- H6 — маржа «не кофе» выше маржи кофе на 3 процентных пункта и больше (маржу не округляйте).

H3 в словарь не входит: её вердикт — «нужен эксперимент».

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd
# full уже собрана: заказы + справочник кофеен + меню, datetime — дата
SIZE_K = {"S": 1.0, "M": 1.25, "L": 1.5}

def verdict(ok):
    return "подтвердилась" if ok else "не подтвердилась"

verdicts = {}
verdicts
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
_v = lambda ok: 'подтвердилась' if ok else 'не подтвердилась'
r = _f.groupby(_f['datetime'].dt.to_period('M'))['amount'].sum().pct_change().dropna()
s = _f.groupby('shop_id').agg(revenue=('amount', 'sum'), seats=('seats', 'first'))
c = _f['client_id'].notna()
d4 = (_f.loc[c, 'amount'].mean() / _f.loc[~c, 'amount'].mean() - 1) * 100
pk = _pd.pivot_table(_f, index=_f['datetime'].dt.weekday, columns=_f['datetime'].dt.hour, values='order_id', aggfunc='count').stack().idxmax()
_f['cost'] = _f['cost_s'] * _f['size'].map({'S': 1.0, 'M': 1.25, 'L': 1.5}) * _f['qty']
g = _f.groupby('category')[['amount', 'cost']].sum()
mg = (g['amount'] - g['cost']) / g['amount'] * 100
want = {'H1': _v((r > 0).all()), 'H2': _v(s['seats'].idxmax() == s['revenue'].idxmax()), 'H4': _v(d4 >= 5),
        'H5': _v(pk[0] in (5, 6) and pk[1] < 12), 'H6': _v(mg['не кофе'] - mg['кофе'] >= 3)}
v = need('verdicts', dict)
assert sorted(v) == sorted(want), f'Ключи verdicts: {sorted(v)}, а нужны {sorted(want)}.'
for k in want:
    assert v[k] == want[k], f'{k}: у вас «{v[k]}», а по правилу выходит другое. Пересчитайте метрику этой гипотезы и сравните с порогом.'
assert calls('verdict') >= 5, 'Выносите каждый вердикт функцией verdict(условие), а не вписывайте строкой.'
```

### hint
Каждый вердикт — одна строка вида `verdicts["H4"] = verdict(условие)`, где условие — сравнение метрики с порогом. Метрики вы уже считали на шагах 2–7.

### hint
H1: `full.groupby(full["datetime"].dt.to_period("M"))["amount"].sum().pct_change().dropna()` — затем `(… > 0).all()`. H2: `idxmax()` по `seats` и по выручке кофеен.

### hint
H5: `peak = load.stack().idxmax()` из шага 6, условие `peak[0] in (5, 6) and peak[1] < 12`. H6: маржа по категориям из шага 7 без `round`, условие `margin["не кофе"] - margin["кофе"] >= 3`.

### solution
```python
import pandas as pd
SIZE_K = {"S": 1.0, "M": 1.25, "L": 1.5}

def verdict(ok):
    return "подтвердилась" if ok else "не подтвердилась"

verdicts = {}

# H1: каждый месяц выручка выше предыдущего
growth = full.groupby(full["datetime"].dt.to_period("M"))["amount"].sum().pct_change().dropna()
verdicts["H1"] = verdict((growth > 0).all())

# H2: самая большая кофейня — лидер по выручке
shops = full.groupby("shop_id").agg(revenue=("amount", "sum"), seats=("seats", "first"))
verdicts["H2"] = verdict(shops["seats"].idxmax() == shops["revenue"].idxmax())

# H4: чек с картой выше минимум на 5 %
card = full["client_id"].notna()
diff_pct = (full.loc[card, "amount"].mean() / full.loc[~card, "amount"].mean() - 1) * 100
verdicts["H4"] = verdict(diff_pct >= 5)

# H5: пик — суббота или воскресенье до полудня
load = pd.pivot_table(full, index=full["datetime"].dt.weekday, columns=full["datetime"].dt.hour,
                      values="order_id", aggfunc="count")
peak = load.stack().idxmax()
verdicts["H5"] = verdict(peak[0] in (5, 6) and peak[1] < 12)

# H6: маржа «не кофе» выше на 3 п. п. и больше
full["cost"] = full["cost_s"] * full["size"].map(SIZE_K) * full["qty"]
g = full.groupby("category")[["amount", "cost"]].sum()
margin = (g["amount"] - g["cost"]) / g["amount"] * 100
verdicts["H6"] = verdict(margin["не кофе"] - margin["кофе"] >= 3)

verdicts
```

### explain
Из пяти гипотез подтвердились две: сеть растёт (H1) и пик приходится на субботнее утро (H5). Три не подтвердились: размер кофейни не определяет лидера (H2), карта почти не влияет на чек (H4), «не кофе» не заметно выгоднее (H6). Для отчёта это не «плохие новости», а ответы: куда ставить второго бариста — понятно, а акции для владельцев карт и продвижение «не кофе» ради денег сеть может не запускать. Функция `verdict` делает правило явным: поменяли порог — вердикт пересчитался сам. Типичная ошибка — сравнивать округлённые цифры: 77.3 − 75.9 = 1.4, а настоящая разница — 1.35. Здесь вердикт от этого не меняется, но при значениях у самого порога округление его переворачивает.

## task: summary | Шаг 9. Сводка-функция | star

Напишите `summary(full)` — функцию, которая возвращает словарь с ключами `revenue` (вся выручка), `orders`, `avg_check` (1 знак), `best_city` (город с наибольшей выручкой), `top_drink` (самый частый напиток) и `growth_pct` (рост выручки последнего месяца к предпоследнему, %, 1 знак). Функция должна работать на любой части данных — например, только на одном городе.

### setup
```python
import pandas as _pd0
full = (_pd0.read_csv("orders_3m.csv", parse_dates=["datetime"])
          .merge(_pd0.read_csv("shops.csv"), on="shop_id", how="left", validate="many_to_one")
          .merge(_pd0.read_csv("menu.csv"), on="drink", how="left", validate="many_to_one"))
```

### starter
```python
import pandas as pd

def summary(full):
    ...

summary(full)
```

### check
```python
import pandas as _pd
_f = (_pd.read_csv("orders_3m.csv", parse_dates=["datetime"])
        .merge(_pd.read_csv("shops.csv"), on="shop_id").merge(_pd.read_csv("menu.csv"), on="drink"))
def _w(f):
    m = f.groupby(f['datetime'].dt.to_period('M'))['amount'].sum()
    return {'revenue': int(f['amount'].sum()), 'orders': len(f), 'avg_check': round(f['amount'].mean(), 1),
            'best_city': f.groupby('city')['amount'].sum().idxmax(), 'top_drink': f['drink'].value_counts().idxmax(),
            'growth_pct': round((m.iloc[-1] - m.iloc[-2]) / m.iloc[-2] * 100, 1)}
fn = need('summary')
for part, name in ((_f, 'вся сеть'), (_f[_f['city'] == 'Казань'], 'только Казань')):
    got = fn(part.copy())
    assert got is not None, 'Функция ничего не возвращает.'
    got = {k: (v if isinstance(v, str) else round(float(v), 1)) for k, v in got.items()}
    want = {k: (v if isinstance(v, str) else round(float(v), 1)) for k, v in _w(part).items()}
    assert got == want, f'Для «{name}» summary = {got}, а нужно {want}.' 
```

### hint
Каждое значение — одна строка из прошлых шагов, только вместо `full` используйте параметр функции.

### hint
Последний и предпоследний месяц — `.iloc[-1]` и `.iloc[-2]` у помесячной выручки.

### solution
```python
import pandas as pd

def summary(full):
    monthly = full.groupby(full["datetime"].dt.to_period("M"))["amount"].sum()
    return {
        "revenue": full["amount"].sum(),
        "orders": len(full),
        "avg_check": round(full["amount"].mean(), 1),
        "best_city": full.groupby("city")["amount"].sum().idxmax(),
        "top_drink": full["drink"].value_counts().idxmax(),
        "growth_pct": round((monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100, 1),
    }

summary(full)
```

### explain
Шаги в браузере пройдены — осталось последнее: перенести их в шаблон и сдать проект блокнотом (раздел «Сдайте проект блокнотом» выше), а затем выложить его на GitHub в уроке «Блокнот в git и портфолио на GitHub». Сравните это решение с мини-проектом главы 1: те же вопросы, но вместо циклов и словарей — несколько строк pandas. Следующая глава — предобработка: что делать, когда данные не такие чистые, как эти.
