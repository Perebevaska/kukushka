---
title: "Проект: сколько бариста поставить на смену"
files: [app_orders.csv]
lead: "Финал главы. Заказы из приложения собирает отдельный бариста на выдаче, и график смен составляется накануне. Строим прогноз заказов на завтра по часам с требованием к точности, честно выбираем модель на валидации — и переводим прогноз в людей, где выясняется, что «точный в среднем» прогноз систематически оставляет смены без рук."
recap:
  - "Требование к модели формулируют заранее: метрика, порог и наивный прогноз, который нужно обогнать."
  - "Момент прогноза задаёт признаки: при решении в 20:00 последний известный час — 19:00, и для 23:00 завтра законны только лаги ≥ 28 — здесь лаги 48, 168 и среднее `s.shift(28).rolling(24)`."
  - "Июль служит для выбора, август — для финальной ретроспективной оценки зафиксированных правил. Для выпуска 1 августа финальный fit использует завершённые часы по 31 июля 19:00."
  - "В проекте три расширяющихся фолда. На регулярной часовой сетке TimeSeriesSplit(n_splits=3, gap=28) исключает 28 строк перед каждым тестовым блоком."
  - "Прогноз ряда используют для решения — здесь штатного расписания. Для решения сравните часы с нехваткой людей и лишние бариста-часы вместе с RMSE."
  - "Модель на среднее снижает квадратичную ошибку. Верхний квантиль задаёт целевой уровень для спроса. Фактическое покрытие и нехватку штата измеряют отдельно."
  - "Квантиль 0.8 задаёт цель покрытия 80 %, но фактическое покрытие на новой партии и в рабочих часах проверяют отдельно; округление до сотрудников меняет долю дефицитных часов."
---

## Задача

> График смен на выдаче заказов из приложения составляем накануне к 20:00 на весь следующий день. Сейчас ставим по среднему за этот час за 4 прошлые недели, и то бариста скучает, то очередь из курьеров.
>
> Нужна модель, которая прогнозирует число заказов на каждый час завтрашнего дня. Требование: RMSE на августе — не больше 4.3 заказа в час, и модель должна быть лучше нашего правила «среднее за этот час за 4 прошлые недели». Один бариста на выдаче успевает около 6 заказов в час; с 7 до 22 часов на выдаче всегда хотя бы один человек.
>
> *Операционный менеджер*

## План

Момент выпуска — 20:00 накануне; последняя полностью завершённая часовая метка — 19:00. Для первой выдачи на 1 августа исключите из fit ответы 31 июля 20:00–23:00; для июльской валидации аналогично исключите 30 июня 20:00–23:00. Наличие правильных лагов не делает будущие метки доступными для fit.

Для реального выпуска запишите время решения и последнюю метку, принятую в fit. Продлите часовой индекс истории до 23:00 завтрашнего дня, оставив неизвестные заказы пустыми, в том числе промежуток от 20:00 до полуночи. Постройте признаки и выберите по индексу все 24 завтрашние строки. Сохраните партию прогнозов до присоединения фактов. При проверке следующего дня сдвиньте отсечку и заново постройте признаки. Для августовской оценки параметры и обученная модель остаются фиксированными.


0. Момент прогноза и горизонт: какие признаки законны при решении в 20:00 (раздел ниже).
1. Признаки для горизонта «завтра» (раздел «Разберём вместе» урока «Прогноз: ориентиры, горизонт и метрики») и признак акции (задача «Признак „день акции“» урока «Признаки для прогноза ряда»); разбиение по времени: обучение — март–июнь, валидация — июль, тест — август.
2. Оцените действующее правило четырёх недель на июльских ответах, которые доступны к 31 июля 20:00. Используйте тот же срез при сравнении с восьминедельным окном.
3. Выберите семейство на 740 июльских ответах до 31 июля 20:00. Четыре более поздних июльских часа ещё не завершились.
   Затем — подбор параметров победителя кросс-валидацией по времени: `GridSearchCV` с `cv=TimeSeriesSplit(n_splits=3, gap=28)` на завершённых часах до выпуска 31 июля. Обычное `cv=3` здесь — ошибка: это KFold, который не знает о времени.
4. Зафиксируйте признаки, календарь акций, правило при короткой истории, параметры модели и ставки нехватки/избытка. На августе оцените зафиксированную модель и ориентир за одни и те же 744 часа. Для каждого дня используйте сведения к 20:00 накануне; факты этого дня присоединяйте только после выпуска.
5. Сравните почасовые планы по нехватке и избытку в бариста-часах. Напишите менеджеру, какой план предпочтителен при заданных стоимости и производительности.
6. План по верхнему квантилю.

::: figure ts-project-split
Для выбора семейства используются 740 июльских часов, завершившихся до первого августовского выпуска. Подбор параметров использует три фолда внутри доступных к 31 июля 20:00 данных. Для каждого фолда между обучением и проверкой оставлены 28 часовых строк. Август используется для итоговой оценки уже выбранных правил.
:::

## Момент прогноза и признаки

Прежде чем строить признаки, ответим на три вопроса из урока «Прогноз: ориентиры, горизонт и метрики».

1. **Когда принимается решение?** В 20:00 накануне. Последний полностью известный час — 19:00 сегодня.
2. **На какой период?** Весь завтрашний день по часам: от 00:00 до 23:00 завтра.
3. **Какой лаг законен для самого дальнего часа?** От 19:00 сегодня до 23:00 завтра — 28 часов. Лаг 24 для 23:00 завтра указывает на 23:00 сегодня, а в 20:00 этого часа ещё нет. Значит, для всех часов годятся только лаги от 28.

Отсюда признаки. Календарь и флаг акции известны заранее (даты акций — в календаре маркетинга). Из лагов берём 48 (тот же час позавчера) и 168 (тот же час неделю назад). Среднее за сутки сдвигаем на 28 часов: `s.shift(28).rolling(24).mean()` — окно заканчивается не позже 19:00 сегодня для любого часа завтра. `mean4w` строится из сдвигов от 168 часов — он законен. Лаг 24 подошёл бы утренним часам завтра, но ради одной модели на все часы мы от него отказываемся.

Для единого выпуска в 20:00 выберите признаки, которые уже известны для каждого из 24 будущих часов. Лаг 24 для последнего часа завтрашнего дня обращается к сегодняшним 23:00, которых в момент выпуска ещё нет. Ошибка финального прогноза будет измерена после фиксации модели.

В заготовке `make(s)` готовит календарь, флаг известной акции, лаги 48 и 168, среднее за 24 часа со сдвигом 28 и `mean4w`. У `mean4w` заранее задан резерв: пока история короче четырёх недель, усредняем доступные сопоставимые часы. Поэтому с 8 по 28 марта используются одна, две и три недели соответственно (по 168 строк), с 29 марта — все четыре. В августе у каждой строки четыре наблюдения. В отдельном исследовании можно потребовать все четыре недели с самого начала; тогда изменятся обучение и значения метрик. Маркетинг заранее передал учебный календарь 2026 года: 17 апреля, 22 мая, 19 июня, 24 июля и 21 августа, с 10:00 по 20:00 включительно в каждый из этих дней. Это вход для прогноза даже при пустых будущих заказах. Используйте его также в самостоятельном блокноте.

## От прогноза к людям: зачем квантиль (шаги 5–6)

Шаги 1–4 отвечают на вопрос «сколько заказов будет». Менеджеру нужен другой ответ — «сколько человек поставить». В шаге 5 прогноз переводят в бариста: `max(1, ceil(заказы / 6))`. Обычная модель прогнозирует среднее: оно минимизирует квадратичную ошибку, но не обещает, в какой доле часов факт окажется выше. Это свойство медианы, а не среднего, и при скошенном спросе они расходятся. К тому же `ceil` до целого бариста даёт запас, так что факт выше прогноза ещё не значит нехватку. Долю часов с нехваткой средний прогноз не контролирует — её измеряют отдельно, это шаг 5.

Если дефицитный бариста-час дороже избыточного, стоит сравнить средний прогноз с более высоким **квантилем**. Выбор плана зависит от ставок и мощности сотрудника. Квантиль 0.8 здесь — кандидат для сравнения (глава 4: это значение, ниже которого лежит 80 % данных). Пример: в 10 прошлых пятниц в 18:00 было 12, 14, 15, 15, 16, 17, 18, 19, 21 и 24 заказа. Среднее — 17.1, по нему нужно 3 бариста (17.1 / 6 ≈ 2.85, вверх — 3), и в трёх пятницах из десяти (19, 21, 24 заказа) рук бы не хватило. Квантиль 0.8 — 19.4 (`np.quantile(x, 0.8)`), по нему 4 бариста, и их хватило бы во все десять пятниц: квантиль задаёт целевую долю часов, где заказов меньше плана (80 %), а округление вверх до человека сдвигает фактическую долю ещё выше. Цена — лишний человек в обычные пятницы.

Модель умеет прогнозировать квантиль напрямую: `HistGradientBoostingRegressor(loss="quantile", quantile=0.8)` учится выдавать значение, для которого модель оценивает условный 80-й процентиль спроса. Это шаг 6 — после того как в шаге 5 вы увидите, как часто план по среднему оставляет смены без рук.

::: quiz
Зачем сравнивать план по квантилю 0.8 с планами по среднему и действующему ориентиру?

- [x] Чтобы проверить, окупается ли снижение нехватки дополнительными бариста-часами
  > Сравните дефицит и избыток при заранее заданных ставках на тех же рабочих часах. Более дорогая нехватка сама по себе не гарантирует победу конкретного квантиля 0.8.
- [ ] Чтобы выбрать прогноз с наименьшей RMSE для почасовых заказов
  > RMSE оценивает ошибку прогноза. Здесь выбирают кадровый план по стоимости недостающих и лишних бариста-часов.
- [ ] Чтобы обеспечить людей ровно в 80 % новых рабочих часов
  > Целевой квантиль не гарантирует такое покрытие на новых данных. Округление до работников и мощность одного человека также меняют обеспеченность.
- [ ] Чтобы учесть дорогую нехватку без расчёта стоимости избытка
  > Дополнительный штат может снизить дефицит и увеличить избыток. Для выбора нужны обе заранее заданные ставки.
:::


## Что отправить менеджеру

До просмотра августовских фактов запишите момент выпуска, ставку за недостающий и за лишний бариста-час, норматив заказов в час и правила сравнения. Для базовой работы в этой главе достаточно готовых прогнозов модели на среднее и действующего ориентира. В карточке «Прогноз в людях» сравните эти два плана. Квантильный прогноз можно добавить отдельно.

{{practice: split, baseline, select, grid, final, staffing, quantile}}

Подготовьте письмо на три предложения. Укажите период проверки, рабочие часы и норматив. Приведите число недостающих и избыточных бариста-часов для двух вариантов и сравните их стоимость по заранее записанным ставкам. Какой почасовой план вы предложите для пилота и что потребуется менеджеру, чтобы назначить конкретные смены?

### Перенос на колл-центр

Смену с 09:00 до 13:00 сократили на час, начало прежнее. Диспетчер назначает на всю смену двух или трёх операторов. Один оператор принимает 6 звонков в час; даже при нулевом спросе нужен один дежурный. В сопоставимый день с 08:00 по 13:00 включительно поступило по часам 17, 13, 0, 10, 17 и 24 звонка. Метка часа — его начало, звонки между часами не переносятся. Дефицит операторо-часа стоит 300 условных единиц, избыток — 100. Какие часы войдут в расчёт? Выберите состав и покажите, при какой цене выбор изменится. Если план нужен завтра, что диспетчер уже знает в момент выпуска? Запишите решение до чтения примера для кофейни.

<details>
<summary>Сверить письмо после проверки на августе</summary>

> На 496 рабочих часов августа (07:00–22:00 включительно) при мощности 6 заказов на человека в час я предложил бы проверить квантильный план в пилоте, если дефицит стоит 3 условные единицы за бариста-час, а избыток — 1. У четырёхнедельного правила 185 недостающих и 142 лишних бариста-часа (697 единиц), у модели на среднее 192 и 118 (694), у квантиля 90 и 296 (566). При равной цене из этих трёх вариантов выгоднее модель на среднее: 310 против 327 у правила и 386 у квантиля.
>
> За 744 часа августа RMSE модели на среднее равна 4,216 заказа в час, у действующего правила — 4,353. Ранее выбранное на июле восьминедельное окно даёт 4,140, но для его почасового плана дефицит равен 198, избыток — 121, стоимость при ставках 3 и 1 — 715. Для рабочих часов квантиль покрыл спрос прогнозом в 346 из 496, после округления сотрудников хватило в 422 из 496. В 18:00 нехватка была в 11 из 31 часов, поэтому в пилоте отдельно проверим вечер. Перед переходом к персональному расписанию нужны фактическая производительность, местные ставки, длительность смен и перерывы.

::: figure ts-staffing
Пример отдельного часа и итоги по 496 рабочим часам августа. Сравните ошибку прогноза заказов и разницу в бариста-часах после округления штата.
:::

</details>

## task: split | Шаг 1. Разбиение по времени | base

Постройте `df = make(s)`, `X`, `y` и три маски: `train` (до 2026-07-01), `valid` (июль), `test` (август). Сохраните `sizes` — словарь `{"train": ..., "valid": ..., "test": ...}` с числом строк.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
```

### starter
```python
# уже есть: make(s) — таблица признаков для прогноза на завтра
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
d = make(s0)
w = {'train': int((d.index < '2026-07-01').sum()), 'valid': int(((d.index >= '2026-07-01') & (d.index < '2026-08-01')).sum()), 'test': int((d.index >= '2026-08-01').sum())}
assert dict(need('sizes')) == w, f'sizes = {need("sizes")}, а нужно {w}.'
_df = need('df'); _X = need('X'); _y = need('y')
assert _X.index.equals(d.index) and list(_X.columns)==list(d.columns.drop('y')), 'X: сверяем схему и даты, target не должен быть признаком.'
assert _X.equals(d.drop(columns='y')) and _y.equals(d['y']), 'Сверьте все значения признаков/меток по времени.'
for _name,_mask in [('train',d.index<'2026-07-01'),('valid',(d.index>='2026-07-01')&(d.index<'2026-08-01')),('test',d.index>='2026-08-01')]:
    assert (need(_name)==_mask).all(), f'{_name}: состав строк не соответствует временной границе.'
_hidden=s0.copy(); _hidden.loc[_hidden.index>='2026-07-31 20:00']=float('nan')
_future=make(_hidden).loc['2026-08-01':'2026-08-01 23:00']
assert len(_future)==24 and _future.drop(columns='y').notna().all().all(), 'make должен строить24 будущие строки без y на1августа.'
import numpy as _np, pandas as _pd
def _same_frame(got, expected):
    assert isinstance(got, _pd.DataFrame), 'Сохраните DataFrame.'
    assert set(expected.columns)<=set(got.columns), 'Не хватает заявленных столбцов.'
    assert got.index.is_unique and len(got)==len(expected), 'Проверьте число строк и уникальность дат.'
    assert got.index.sort_values().equals(expected.index.sort_values()), 'Даты результата не совпадают.'
    assert _np.allclose(got.reindex(expected.index)[expected.columns].to_numpy(), expected.to_numpy(), atol=1e-8, rtol=0, equal_nan=True), 'Сверьте все значения по временным ключам.'

_same_frame(need('df'),d)
```

### hint
Таблица признаков — `df = make(s)`, ответ — `y = df["y"]`, признаки — `X = df.drop(columns="y")`.

### hint
Маски — сравнения индекса со строками-датами: `df.index < "2026-07-01"`. Июль: `(df.index >= "2026-07-01") & (df.index < "2026-08-01")`.

### hint
Размеры — `int(train.sum())` и т. д.: сумма `True` в маске — число строк.

### solution
```python
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]

df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
sizes = {"train": int(train.sum()), "valid": int(valid.sum()), "test": int(test.sum())}
```

### explain
Для временного ряда части берутся по времени, а не случайно: обучение — март–июнь (2760 часов), валидация — июль (744 часа = 31 × 24), тест — август (744 часа). Случайное разбиение позволило бы модели «подсмотреть» соседние часы из будущего, и оценка вышла бы завышенной. Обучение начинается с 8 марта, а не с 1-го: первую неделю съедают лаги. Валидация нужна для выбора модели и параметров, тест — только для финальной проверки один раз.

## task: baseline | Шаг 2. Ориентир на июле | base

Посчитайте `rmse_base` — RMSE прогноза `mean4w` на 740 июльских ответах, доступных в 20:00 31 июля, по маске `valid_score = valid & (y.index < "2026-07-31 20:00") & y.notna()` (3 знака). Сохраните в `base_meets`, укладывается ли июльская оценка в 4,3 заказа в час. Требование менеджера относится к августу; его проверим в шаге 4.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
```

### starter
```python
# уже есть: df, X, y и маски train, valid, test
import numpy as np
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
# rmse_base — 740 известных июльских часов; base_meets не является приёмкой августа.
```

### check
```python
vm = (valid & (y.index < '2026-07-31 20:00') & y.notna())
import numpy as _np
w = round(float(_np.sqrt(((y[vm] - X.loc[vm, 'mean4w']) ** 2).mean())), 3)
assert close(need('rmse_base'), w, 0.002), f'rmse_base = {need("rmse_base")}, а нужно {w}.'
assert need('base_meets') == (w <= 4.3), f'base_meets = {need("base_meets")}.'
```

### hint
Ориентир уже лежит среди признаков: столбец `mean4w` — это и есть прогноз «среднее за 4 недели».

### hint
`np.sqrt(((y[valid_score] - X.loc[valid_score, "mean4w"]) ** 2).mean())`.

### solution
```python
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
import numpy as np
rmse_base = round(float(np.sqrt(((y[valid_score] - X.loc[valid_score, "mean4w"]) ** 2).mean())), 3)
base_meets = rmse_base <= 4.3
```

### explain
На доступных 740 июльских часах RMSE действующего правила равна 4,240 заказа в час, у окна из восьми недель — 4,091. В предыдущем уроке в ретроспективе по полному июлю получались 4,239 и 4,089. Сохраните оба результата и зафиксируйте, что требование заказчика сравнивает модель именно с действующим четырёхнедельным правилом.

## task: select | Шаг 3. Выбор на валидации | plus

Для первого июльского выпуска в 20:00 30 июня обучите модели на известных ответах: `train & (y.index < "2026-06-30 20:00") & y.notna()`. Сохраните эту маску как `fit_mask`. В 20:00 31 июля выберите семейство по 740 доступным ответам: сохраните `valid_score = valid & (y.index < "2026-07-31 20:00") & y.notna()`. С этими одинаковыми срезами сравните четыре модели: `LinearRegression()`, `HistGradientBoostingRegressor(random_state=0)`, `HistGradientBoostingRegressor(max_depth=3, random_state=0)`, `HistGradientBoostingRegressor(l2_regularization=1.0, random_state=0)`. Сохраните словарь `valid_rmse` с ключами `"linear"`, `"hgb"`, `"hgb_depth3"`, `"hgb_l2"` (3 знака) и `best` — ключ лучшей.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
```

### starter
```python
# уже есть: df, X, y и маски train, valid, test
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
fit_mask = (train & (y.index < "2026-06-30 20:00") & y.notna())
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
```

### check
```python
import numpy as _np
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import HistGradientBoostingRegressor as _H
ms = {'linear': _LR(), 'hgb': _H(random_state=0), 'hgb_depth3': _H(max_depth=3, random_state=0), 'hgb_l2': _H(l2_regularization=1.0, random_state=0)}
fm = (train & (y.index < '2026-06-30 20:00') & y.notna())
vm = (valid & (y.index < '2026-07-31 20:00') & y.notna())
assert _np.array_equal(need('fit_mask'),fm), 'fit_mask исключает неизвестные ответы 30 июня 20:00–23:00.'
assert _np.array_equal(need('valid_score'),vm), 'valid_score — 740 июльских часов до 31 июля 20:00.'
w = {k: round(float(_np.sqrt(((y[vm] - m.fit(X[fm], y[fm]).predict(X[vm])) ** 2).mean())), 3) for k, m in ms.items()}
got = need('valid_rmse', dict)
assert all(k in got and close(got[k], v, 0.002) for k, v in w.items()), f'valid_rmse = {got}, а нужно {w}.'
assert need('best') == min(w, key=w.get), f'best = {need("best")!r}.'
# Check that unavailable fit labels and unavailable validation labels cannot affect selection.
for _start,_end in [('2026-06-30 20:00','2026-07-01'),('2026-07-31 20:00','2026-08-01')]:
    for _sign in (1,-1):
        _probe=dict(globals())
        _probe['X']=X.copy(); _probe['y']=y.copy()
        _unknown=(_probe['y'].index>=_start)&(_probe['y'].index<_end)
        _probe['y'].loc[_unknown]+=_sign*1000
        exec(_code,_probe)
        assert all(close(_probe['valid_rmse'][k],got[k],0.002) for k in w), 'Выбор модели зависит от ответов, неизвестных к моменту выпуска: исключите последние четыре часа из fit и из оценки июля.'
```

### hint
Календарная маска train включает 30 июня целиком. Последний закрытый час для этого выпуска помечен 19:00. Примените к каждой модели один и тот же срез обучения. Для июльской оценки отсеките всё начиная с 31 июля 20:00.

### hint
Словарь моделей и цикл; лучшая — `min(valid_rmse, key=valid_rmse.get)`.

### solution
```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor

models = {
    "linear": LinearRegression(),
    "hgb": HistGradientBoostingRegressor(random_state=0),
    "hgb_depth3": HistGradientBoostingRegressor(max_depth=3, random_state=0),
    "hgb_l2": HistGradientBoostingRegressor(l2_regularization=1.0, random_state=0),
}
fit_mask = (train & (y.index < "2026-06-30 20:00") & y.notna())
valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())
valid_rmse = {}
for name, m in models.items():
    p = m.fit(X[fit_mask], y[fit_mask]).predict(X[valid_score])
    valid_rmse[name] = round(float(np.sqrt(((y[valid_score] - p) ** 2).mean())), 3)
best = min(valid_rmse, key=valid_rmse.get)
```

### explain
На доступных 740 июльских часах RMSE линейной регрессии — 4,086, HGB по умолчанию — 4,303, HGB с глубиной 3 — 4,063, HGB с L2=1 — 4,350. Неглубокий бустинг выигрывает на этой валидации на 0,023 заказа в час у линейной регрессии. Проверьте, переносится ли выбранная настройка на ранние временные фолды.

## task: grid | Шаг 3 б. Подбор параметров по времени | plus

В шаге 3 модель выбрана на одном месяце (июль): впереди неглубокий бустинг, но его параметры взяты наугад. Надёжнее проверить параметры на нескольких кусках прошлого — кросс-валидацией **по времени**. Подберите параметры бустинга по известным к 31 июля 20:00 ответам, используя `fit_mask` из заготовки — найденные `best_params` станут параметрами финальной модели в шаге 4:

```python static
GridSearchCV(HistGradientBoostingRegressor(random_state=0),
             {"max_depth": [2, 3, None], "learning_rate": [0.05, 0.1]},
             cv=TimeSeriesSplit(n_splits=3, gap=28), scoring="neg_root_mean_squared_error")
```

Сохраните обученный объект в `gs`, лучшие параметры — в `best_params`, положительное среднее RMSE трёх проверочных блоков — в `cv_rmse` (3 знака). Между концом обучения и началом проверки исключите ровно 28 строк. В часовой таблице это консервативный разрыв для выпуска всего завтрашнего дня. Например, первый проверочный час — 13 апреля 11:00: решение принято 12 апреля в 20:00, последняя метка обучения при таком разрыве — 12 апреля 06:00. Для этого шага используются только март–июль.

### setup
```python
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
s = s[s.index < '2026-08-01']
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
```

### starter
```python
# уже есть: df, X, y и маски train, valid, test
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
# cv=TimeSeriesSplit(n_splits=3, gap=28); август здесь не оцениваем.
```

### check
```python
import numpy as _np
from sklearn.model_selection import GridSearchCV as _GS, TimeSeriesSplit as _TS, cross_val_score as _cvs
from sklearn.ensemble import HistGradientBoostingRegressor as _H
g = need('gs', _GS)
assert hasattr(g, 'best_params_'), 'gs ещё не обучен: вызовите gs.fit(X[fit_mask], y[fit_mask]).'
assert isinstance(g.cv, _TS) and g.cv.n_splits == 3 and g.cv.gap == 28, f'cv = {g.cv!r}. Для ряда нужен TimeSeriesSplit(n_splits=3, gap=28), а не число фолдов: cv=3 означает обычный KFold без учёта времени.'
assert g.scoring == 'neg_root_mean_squared_error', f'scoring = {g.scoring!r}; нужен "neg_root_mean_squared_error".'
pg = {k: list(v) for k, v in g.param_grid.items()}
assert pg == {'max_depth': [2, 3, None], 'learning_rate': [0.05, 0.1]}, f'Сетка параметров: {pg}.'
fm = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
assert g.n_features_in_ == X.shape[1] and len(g.cv_results_['split0_test_score']) == 6, 'Обучайте gs на X[fit_mask], y[fit_mask].'
bp = dict(g.best_params_)
ref = -_cvs(_H(random_state=0, **bp), X[fm], y[fm], cv=_TS(n_splits=3,gap=28), scoring='neg_root_mean_squared_error').mean()
assert close(-g.best_score_, ref, 1e-6), 'gs обучен не на ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna()): лучший результат не совпадает с пересчётом на марте–июле.'
assert dict(need('best_params', dict)) == bp, f'best_params = {need("best_params")}, а у gs — {bp}.'
assert close(need('cv_rmse'), round(float(ref), 3), 0.002), f'cv_rmse = {need("cv_rmse")}, а нужно {ref:.3f}. best_score_ отрицательный — поменяйте знак.'
```

### hint
Объект `GridSearchCV` из условия создаётся как есть, потом `gs.fit(X[fit_mask], y[fit_mask])`. Он сам переберёт 6 сочетаний на 3 фолдах по времени и переобучит лучшее на всех данных `fit_mask` (`refit=True` по умолчанию).

### hint
Словарь параметров находится в `gs.best_params_`. Для `cv_rmse` поменяйте знак у `gs.best_score_` и округлите результат до трёх знаков.

### hint
```python
gs = GridSearchCV(..., cv=TimeSeriesSplit(n_splits=3, gap=28), scoring="neg_root_mean_squared_error")
gs.fit(X[fit_mask], y[fit_mask])
best_params = gs.best_params_
cv_rmse = round(-gs.best_score_, 3)
```

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
gs = GridSearchCV(
    HistGradientBoostingRegressor(random_state=0),
    {"max_depth": [2, 3, None], "learning_rate": [0.05, 0.1]},
    cv=TimeSeriesSplit(n_splits=3, gap=28),
    scoring="neg_root_mean_squared_error",
)
gs.fit(X[fit_mask], y[fit_mask])
best_params = gs.best_params_
cv_rmse = round(float(-gs.best_score_), 3)
print(best_params, cv_rmse)
```

### explain
Три тестовых блока содержат по 875 часов. Первый — с 13 апреля 11:00 по 19 мая 21:00, второй — с 19 мая 22:00 по 25 июня 08:00, третий — с 25 июня 09:00 по 31 июля 19:00. Обучающая метка в каждом фолде отстоит от первого тестового часа на 29 часов. Параметры победителя — глубина 3 и шаг 0,05, CV RMSE 3,878 заказа в час.

При нулевом зазоре на тех же 3 500 строках выбраны глубина 2 и шаг 0,1, CV RMSE 3,882. До вечера выпуска в обучение такой модели попадают ещё неизвестные ответы. Направление разницы в RMSE само по себе не говорит, допустим ли способ оценки.

## task: final | Шаг 4. Финальная проверка | base

В заготовке `best_params` — параметры бустинга, найденные по времени в шаге 3 б. Обучите `HistGradientBoostingRegressor(random_state=0, **best_params)` на известных метках марта–июля по 31 июля 19:00 включительно, обрежьте прогноз снизу нулём (`np.clip(p, 0, None)`) и посчитайте RMSE на тесте — `rmse_final` (3 знака). Сохраните `pred_test` (массив прогнозов) и `meets` — выполнено ли требование целиком: RMSE ≤ 4.3 **и** лучше четырёхнедельного ориентира за те же августовские часы (`rmse_base` в заготовке этой карточки).

### setup
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
rmse_base = float(np.sqrt(((y[test] - X.loc[test, "mean4w"]) ** 2).mean()))
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
_ref_model = HistGradientBoostingRegressor(random_state=0, learning_rate=0.05, max_depth=3)
```

### starter
```python
# уже есть: X, y, маски train/valid/test, rmse_base и best_params из шага 3б
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
# В этом шаге rmse_base уже рассчитан на августе: сравниваем две зафиксированные политики.
# fit_mask исключает 31 июля 20:00–23:00; эти ответы на первую дату выпуска неизвестны.
```

### check
```python
import numpy as _np
fit = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
p = _np.clip(_ref_model.fit(X[fit], y[fit]).predict(X[test]), 0, None)
r = round(float(_np.sqrt(((y[test] - p) ** 2).mean())), 3)
assert _np.allclose(need('pred_test'), p, atol=1e-6), 'pred_test — прогноз HistGradientBoostingRegressor(random_state=0, **best_params), обученного на ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna()), обрезанный нулём.'
assert close(need('rmse_final'), r, 0.002), f'rmse_final = {need("rmse_final")}, а нужно {r}.'
assert need('meets') == (r <= 4.3 and r < rmse_base), f'meets = {need("meets")}.'
```

### hint
Последний закрытый час для финального fit — 31 июля 19:00. Ограничьте этим моментом строки марта–июля, у которых известен ответ.

### hint
`fit_mask = (train | valid) & (y.index < "2026-07-31 20:00") & y.notna()`. Обучите модель с `**best_params` на этих строках, затем получите прогнозы августа и обрежьте их снизу нулём.

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
model = HistGradientBoostingRegressor(random_state=0, **best_params)
pred_test = np.clip(model.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)
rmse_final = round(float(np.sqrt(((y[test] - pred_test) ** 2).mean())), 3)
meets = (rmse_final <= 4.3) and (rmse_final < rmse_base)
```

### explain
На августе RMSE зафиксированной модели — 4,216 заказа в час, у среднего четырёх прошлых недель — 4,353. Разница около 0,14 заказа в час. Для решения по сменам ещё предстоит сравнить нехватку людей и лишние бариста-часы.

## task: staffing | Шаг 5. Прогноз в людях | base

Одна строка — час работы. Мощность одного бариста — шесть заказов в час. Если в 10:00 прогноз равен 7, а спрос — 11 заказам, план предусматривает двух бариста, и фактически нужны двое. План смены достаточен, хотя сам прогноз ниже спроса. Что произойдёт при прогнозе 6 и спросе 7?

Переведите прогноз в бариста: нужно `max(1, ceil(заказы / 6))` человек в час (с 7 до 22 включительно; ночью выдачу не планируем). Посчитайте для теста:

- `needed` — сколько бариста нужно было по факту;
- план по модели (`pred_test` в заготовке) и план по ориентиру (`mean4w`).

Для каждого плана сохраните в словарь `plans` (`{"модель": {...}, "ориентир": {...}}`) долю часов с нехваткой людей `short` (план < нужного, 3 знака) и число лишних бариста-часов `extra` (сумма положительных `план − нужно`). Добавьте `deficit` — суммарное число недостающих бариста-часов и `coverage_work` — долю рабочих часов, когда прогноз заказов покрыл наблюдаемый спрос (3 знака). Сохраните `needed` для каждого часа теста по порядку; при подсчёте четырёх показателей применяйте маску рабочих часов.

В этой карточке `needed` — вспомогательный вектор для всех 744 часов: примените `max(1, ceil(заказы / 6))` к каждому значению, в том числе вне рабочих часов. Для выдаваемого расписания оставьте часы 07:00–22:00 включительно, а за их пределами поставьте 0. Все четыре показателя сравнивайте только по 496 рабочим часам. Значения вспомогательного вектора за пределами этого окна в показатели не входят.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
pred_test = np.clip(HistGradientBoostingRegressor(random_state=0, **best_params).fit(X[((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())], y[((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())]).predict(X[test]), 0, None)
_ref_pred = pred_test.copy()
```

### starter
```python
# уже есть: X, y, маски и pred_test — прогноз модели на август
import numpy as np

y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)

```

### check
```python
import numpy as _np
yt = y[test]; oh = (yt.index.hour >= 7) & (yt.index.hour <= 22)
nd = _np.maximum(1, _np.ceil(yt.values / 6))
assert _np.array_equal(need('needed'), nd), 'Проверьте needed для каждого часа теста по порядку: фактические заказы делим на шесть, округляем вверх и берём не меньше одного.'
w = {}
for k, p in [('модель', _ref_pred), ('ориентир', X.loc[test, 'mean4w'].values)]:
    pl = _np.maximum(1, _np.ceil(p / 6))
    w[k] = (round(float(((pl < nd) & oh).sum() / oh.sum()), 3), float(_np.clip(pl - nd, 0, None)[oh].sum()))
got = need('plans', dict)
for k, (sh, ex) in w.items():
    assert k in got, f'Нет ключа {k!r} в plans.'
    assert close(got[k]['short'], sh, 0.002) and close(got[k]['extra'], ex, 0.5), f'{k}: short, extra = {got[k]["short"]}, {got[k]["extra"]}, а нужно {sh}, {ex}.'
for _name,_p in [('модель',_ref_pred),('ориентир',X.loc[test,'mean4w'].values)]:
    _plan=_np.maximum(1,_np.ceil(_p/6))
    assert close(got[_name]['deficit'],float(_np.clip(nd-_plan,0,None)[oh].sum())), 'deficit: нехватка человеко-часов в рабочее время.'
    assert close(got[_name]['coverage_work'],round(float((yt.values[oh]<=_p[oh]).mean()),3)), 'coverage_work: покрытие спроса прогнозом в рабочие часы.'

```

### hint
Бариста нужно столько, чтобы обслужить все заказы часа: заказы / 6, округлённые вверх; в часы работы — не меньше одного.

### hint
Нужно по факту: `needed = np.maximum(1, np.ceil(y_test.values / 6))`. План — та же формула от прогноза. Считайте только по маске `open_hours`.

### solution
```python
import numpy as np

y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)
needed = np.maximum(1, np.ceil(y_test.values / 6))
plans = {}
for name, p in [("модель", pred_test), ("ориентир", X.loc[test, "mean4w"].values)]:
    plan = np.maximum(1, np.ceil(p / 6))
    short = round(float(((plan < needed) & open_hours).sum() / open_hours.sum()), 3)
    extra = float(np.clip(plan - needed, 0, None)[open_hours].sum())
    plans[name] = {"short": short, "extra": extra, "deficit": float(np.clip(needed-plan,0,None)[open_hours].sum()), "coverage_work": round(float((y_test.values[open_hours]<=p[open_hours]).mean()),3)}
```

### explain
Неожиданный результат: по RMSE модель лучше, а нехватка людей у неё случается почти в трети рабочих часов — даже чаще, чем у ориентира. Причина в самой постановке: модель прогнозирует среднее и никак не ограничивает долю часов, где факт выше прогноза, а округление вверх лишь частично это компенсирует. К тому же в августе заказов больше, чем в среднем в обучающих месяцах. Точность в среднем не равна хорошему решению — дальше шаг 6.

## task: quantile | Шаг 6. План по верхнему квантилю | star

Перед сравнением почасовых планов задайте стоимость дефицитного и избыточного человеко-часа. Рядом с покрытием спроса и долей часов нехватки покажите суммарную нехватку мощности и лишние бариста-часы **в рабочих часах**; лучшая RMSE сама по себе не выбирает самый выгодный план. Если дефицитный бариста-час дороже избыточного, можно сравнить средний прогноз с **верхним квантилем**: прогноз условного 80-го процентиля спроса. Обучите `HistGradientBoostingRegressor(loss="quantile", quantile=0.8, random_state=0, **best_params)` (параметры из шага 3 б есть в заготовке) на завершённых метках марта–июля по 31 июля 19:00 включительно, обрежьте нулём и постройте план как в шаге 5. Сохраните `coverage` — долю часов теста, где факт не выше прогноза (3 знака), `short_q` (доля часов нехватки, 3 знака) и `extra_q` (лишние бариста-часы) — по рабочим часам.

Для рабочих часов с 07:00 до 22:00 включительно отдельно сохраните `coverage_work` — долю исходных фактов не выше квантильного прогноза (три знака) и `deficit_q` — суммарное число недостающих бариста-часов после округления плана до работников. При мощности шесть заказов в час сравните нужное и запланированное число людей отдельно для каждого часа.

### setup
```python
import numpy as np
import pandas as pd
_promo_days = pd.to_datetime(["2026-04-17", "2026-05-22", "2026-06-19", "2026-07-24", "2026-08-21"])
def make(s):
    s = s.asfreq("h")
    df = pd.DataFrame({"y": s})
    df["hour"] = df.index.hour
    df["dow"] = df.index.dayofweek
    df["weekend"] = (df["dow"] >= 5).astype(int)
    df["promo"] = (df.index.normalize().isin(_promo_days) & (df.index.hour >= 10) & (df.index.hour <= 20)).astype(int)
    for k in (48, 168):
        df[f"lag_{k}"] = s.shift(k)
    df["roll"] = s.shift(28).rolling(24).mean()
    df["mean4w"] = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return df.dropna(subset=df.columns.drop("y"))
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
df = make(s)
X, y = df.drop(columns="y"), df["y"]
train = df.index < "2026-07-01"
valid = (df.index >= "2026-07-01") & (df.index < "2026-08-01")
test = df.index >= "2026-08-01"
best_params = {"learning_rate": 0.05, "max_depth": 3}   # результат шага 3б
```

### starter
```python
# уже есть: X, y, маски train, valid, test и best_params
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

```

### check
```python
import numpy as _np
from sklearn.ensemble import HistGradientBoostingRegressor as _H
fm = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
pq = _np.clip(_H(loss='quantile', quantile=0.8, learning_rate=0.05, max_depth=3, random_state=0).fit(X[fm], y[fm]).predict(X[test]), 0, None)
yt = y[test]; oh = (yt.index.hour >= 7) & (yt.index.hour <= 22)
nd = _np.maximum(1, _np.ceil(yt.values / 6)); pl = _np.maximum(1, _np.ceil(pq / 6))
assert close(need('coverage'), round(float((yt.values <= pq).mean()), 3), 0.002), f'coverage = {need("coverage")}.'
assert close(need('short_q'), round(float(((pl < nd) & oh).sum() / oh.sum()), 3), 0.002), f'short_q = {need("short_q")}.'
assert close(need('extra_q'), float(_np.clip(pl - nd, 0, None)[oh].sum()), 0.5), f'extra_q = {need("extra_q")}.'
assert close(need('deficit_q'),float(_np.clip(nd-pl,0,None)[oh].sum())), 'deficit_q — нехватка человеко-часов.'
assert close(need('coverage_work'),round(float((yt.values[oh]<=pq[oh]).mean()),3)), 'coverage_work — рабочие часы, а не все24.'

```

### hint
Квантильная модель — `HistGradientBoostingRegressor(loss="quantile", quantile=0.8, ...)`; обучение — на тех же данных, что финальная модель.

### hint
Покрытие: `(y_test.values <= p).mean()`. План и подсчёт — как в шаге 5.

### solution
```python
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

fit_mask = ((train | valid) & (y.index < "2026-07-31 20:00") & y.notna())
q = HistGradientBoostingRegressor(loss="quantile", quantile=0.8, random_state=0, **best_params)
p = np.clip(q.fit(X[fit_mask], y[fit_mask]).predict(X[test]), 0, None)
y_test = y[test]
open_hours = (y_test.index.hour >= 7) & (y_test.index.hour <= 22)
coverage = round(float((y_test.values <= p).mean()), 3)
needed = np.maximum(1, np.ceil(y_test.values / 6))
plan = np.maximum(1, np.ceil(p / 6))
short_q = round(float(((plan < needed) & open_hours).sum() / open_hours.sum()), 3)
extra_q = float(np.clip(plan - needed, 0, None)[open_hours].sum())
deficit_q = float(np.clip(needed-plan,0,None)[open_hours].sum())
coverage_work = round(float((y_test.values[open_hours]<=p[open_hours]).mean()),3)

```

### explain
В августе квантильный прогноз покрывает фактический спрос в 73,9 % всех часов и в 69,8 % рабочих. После пересчёта прогнозов в целое число людей нехватка осталась в 14,9 % рабочих часов. Суммарно недоставало 90 бариста-часов, а избыточно было запланировано 296. Цель квантиля, фактическое покрытие и доля обеспеченных людьми часов здесь различаются.
