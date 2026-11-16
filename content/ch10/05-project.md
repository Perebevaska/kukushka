---
title: "Проект: прогноз дневной выручки"
files: [daily_sales.csv]
lead: "Финал главы. Управляющие кофейнями планируют смены и закупки по ощущениям. Строим прогноз выручки каждой кофейни на каждый день: честная проверка «по времени», простые ориентиры, линейная модель с ручными взаимодействиями, бустинг с подбором по валидации — и ловушка, которую деревья не видят: рост бизнеса."
recap:
  - "Данные во времени проверяют «по времени»: обучаемся на прошлом, проверяем на будущем. Случайное разбиение подглядывает в будущее."
  - "Для разового плана ориентир строится только по истории до выпуска; lag7 с будущими фактами допустим лишь при обновлении прогноза."
  - "Линейная модель не видит взаимодействий (выходной × формат кофейни), пока их не добавить вручную. Бустинг находит их сам."
  - "Валидацию для подбора гиперпараметров тоже берут из последнего периода обучающих данных."
  - "Деревья не продолжают тренд: за пределами обучающих данных прогноз «застывает». Тренд снимают отдельно (делят на него ответ), а бустинг учит остальное."
  - "Модели сравнивают одной таблицей «модель | RMSE | MAE | fit, с | predict, мс». Время — `time.perf_counter()` вплотную вокруг `fit` и `predict`; CatBoost и LightGBM добавляют в ту же таблицу в своём Jupyter."
---

## Задача

> У нас шесть кофеен трёх форматов: на улице, в торговом центре и в бизнес-центре. Управляющие планируют смены бариста и закупку молока «на глаз», и мы то переплачиваем за лишние смены, то не успеваем обслужить гостей.
>
> Нужен прогноз выручки каждой кофейни на каждый день следующего полугодия: с учётом дня недели, праздников, погоды из прогноза и запланированных акций. Насколько точным он получится и стоит ли он того, чтобы на него переходить?
>
> *Операционный директор*

## Данные

`daily_sales.csv` — выручка по дням за 2024–2025 годы:

| столбец | что это |
|---|---|
| `date` | дата |
| `shop_id`, `city` | кофейня и город |
| `format` | формат: улица, ТЦ, бизнес-центр |
| `temp` | средняя температура дня, °C |
| `rain` | был ли дождь (1/0) |
| `holiday` | праздничный день (1/0) |
| `promo` | в этот день шла акция (1/0) |
| `revenue_k` | выручка, тыс. ₽ (целевой признак) |

Дата выпуска — утро 1 июля 2025 года. Управляющие получают сразу весь план на июль–декабрь. Для выбора модели воспроизведите более ранний выпуск утром 1 апреля на апрель–июнь. Для каждого выпуска доступны касса и наблюдавшаяся погода по предыдущий день включительно. Будущие `temp` и `rain` в CSV записаны по факту. В прогнозе используйте исторический сценарий для календарного месяца: среднюю температуру и долю дождливых дней по строкам до даты выпуска. Архива метеопрогнозов в учебных данных нет.

**Допущение проекта.** Для каждого из двух выпусков считаем значения `holiday` и `promo` на весь горизонт утверждённым к утру выпуска календарём. Эта учебная копия плана совпадает с колонками CSV. Файл не содержит даты утверждения или журнала изменений. Если позже акция была отменена, при исторической оценке используйте сохранённый план её выпуска. Для нового выпуска нужен его собственный календарь.

## Что передать управляющему и коллеге

После расчётов самостоятельно напишите короткое письмо директору. Укажите дату выпуска, горизонт и источник погоды. Сравните выбранную процедуру с недельным ориентиром по одной метрике на тех же датах. Поясните, что означает ошибка в тысячах рублей дневной выручки одной кофейни. Предложите пилот против действующего правила планирования: какие решения будут принимать управляющие и по каким данным о стоимости смен, нехватке персонала и списаниях вы оцените результат?

Для передачи проекта соберите папку с README, кодом запуска, доступной историей, календарём запроса, сохранённой моделью с подготовкой признаков и рассчитанным планом. В README укажите версии и команды из корня папки. Используйте относительные пути. У запроса нужны дата, кофейня и известные на выпуск признаки. В плане сохраните дату выпуска, дату прогноза, кофейню и дневную выручку в тыс. ₽. Покажите коллеге два запуска:

1. Загрузить сохранённую модель, подать `request.csv` и повторить `plan.csv` по ключу «дата, кофейня».
2. Выпустить новый план на другой период. Предусмотрите открытый параметр даты выпуска (например, `--as-of 2025-08-01`), входной запрос и путь результата. Команда должна пересобрать доступную историю, сценарий погоды и модель по зафиксированному рецепту без редактирования ячеек. Проверьте, что подмена будущих фактов при неизменном календаре сохраняет выданные прогнозы.

**Перенос.** Энергосбыт 1 февраля выпускает сразу квартальный план для нескольких районов. Какую информацию о погоде он может использовать для весеннего дня? Запишите дату выпуска и последнюю доступную дату наблюдений. Объясните, как проверить происхождение данных и оценить план по окончании квартала.

## План

До просмотра итогового полугодия запишите критерий выбора — минимум RMSE на апреле–июне — и пять процедур шага 8: простая линейная регрессия, лес, GradientBoosting, HistGradientBoosting с настройками по умолчанию и версия с трендом. Дату начала `day_n` и схему индикаторов кофейни и формата сохраняйте для одиночного прогноза.

1. По истории до апреля изучите выручку по формату и дню недели.
2. Подготовьте признаки с учётом даты выпуска и разметьте границу июльского выпуска.
3. Оцените недельный ориентир и линейную модель на апреле–июне из выпуска 1 апреля.
4. Исследуйте взаимодействия в линейной модели.
5. Сравните ансамбли на той же валидации.
6. В отдельной лабораторной работе подберите бустинг по MAE. Этот эксперимент и линейные взаимодействия помогают изучить методы. В управленческом сравнении участвуют пять процедур из шага 8.
7. Проверьте вариант с трендом на апреле–июне.
8. Выберите одну из пяти процедур по апрельской валидации. Затем переобучите их с теми же параметрами на истории до июля и откройте факты июля–декабря для отчёта. Для письма пересчитайте и недельный ориентир по истории до 1 июля. В дополнительном Jupyter-практикуме сравните библиотеки.

При подготовке признаков используйте температуру, дождь, праздник, акцию, день недели, месяц, выходной, номер дня от 2024-01-01 и индикаторы кофейни и формата.



::: figure sales-split
Как делим данные в шагах 2 и 6: обучение — до апреля 2025, валидация для подбора — апрель–июнь, тест — второе полугодие. Внизу для контраста — случайное разбиение, при котором тестовые дни перемешаны с обучающими.
:::

В каждом дереве все даты позднее последней даты обучения попадают по признаку `day_n` по одну сторону любого порога. Вклад времени сам по себе дальше не растёт. Другие признаки могут менять прогноз по дням. На шаге 7 сравните обычный бустинг и модель с отдельным трендом, который оценивается на данных до апреля.

::: figure trend-trap
Выпуск 1 апреля 2025. Для каждого месяца апреля–июня показана средняя дневная выручка одной кофейни и два прогноза на тех же строках, в тыс. ₽. Проверьте по графику, всегда ли добавление тренда приближает прогноз к факту.
:::

::: quiz
Прогноз дневной выручки: почему разбиение на train и test делают по времени, а не случайно?

- [x] Модель будут применять к будущим дням; при случайном разбиении она «подсматривает» соседние дни и тренд из будущего
  > Честная проверка повторяет работу: учимся на прошлом, проверяем на следующем периоде.
- [ ] Так тест получается больше
  > Размер теста задают отдельно.
- [ ] Случайное разбиение не работает с датами
  > Работает технически, но даёт завышенную оценку.
- [ ] Чтобы train был меньше
  > Размер train тут ни при чём — важен порядок во времени.
:::

Августовскую тренировку «Одна строка прогноза» выполняйте после шага 8 и итогового июльского отчёта. Это следующий выпуск с другой границей доступных фактов; для апрельского выбора его данные не используются.

## task: look | Шаг 1. Формат и выходные | base

Используйте строки до 1 апреля 2025 года. Посчитайте среднюю выручку по формату и выходным (суббота и воскресенье) — таблицу `pivot` (строки — формат, столбцы — 0/1 «выходной», 1 знак). Сохраните `weekend_ratio` — для каждого формата отношение выручки в выходной к будней (Series, 2 знака), и `most_weekday` — формат, который сильнее всего зависит от будней (наименьшее отношение).

### starter
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])
s = s.loc[s["date"] < "2025-04-01"].copy()
s["weekend"] = (s["date"].dt.weekday >= 5).astype(int)

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('daily_sales.csv', parse_dates=['date'])
s0 = s0.loc[s0['date'] < '2025-04-01'].copy()
s0['weekend'] = (s0['date'].dt.weekday >= 5).astype(int)
pv = s0.groupby(['format', 'weekend'])['revenue_k'].mean().unstack()
p = need('pivot', _pd.DataFrame)
for f in pv.index:
    for w in (0, 1):
        assert close(p.loc[f, w], round(pv.loc[f, w], 1), 0.06), f'pivot[{f}, {w}] = {p.loc[f, w]}, а нужно {round(pv.loc[f, w], 1)}.'
r = (pv[1] / pv[0]).round(2)
wr = need('weekend_ratio', _pd.Series)
assert all(close(wr[f], r[f], 0.011) for f in r.index), f'weekend_ratio: ожидалось {r.to_dict()}.'
assert need('most_weekday') == r.idxmin(), f'most_weekday = {need("most_weekday")!r}.'
```

### hint
Столбец `weekend` уже есть в заготовке. Таблица — `s.groupby(["format", "weekend"])["revenue_k"].mean().unstack()`: формат в строках, выходной в столбцах.

### hint
Отношение — столбец `1`, делённый на столбец `0`: `pivot[1] / pivot[0]`. Формат с наименьшим отношением — `.idxmin()`.

### solution
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])
s = s.loc[s["date"] < "2025-04-01"].copy()
s["weekend"] = (s["date"].dt.weekday >= 5).astype(int)

pivot = s.groupby(["format", "weekend"])["revenue_k"].mean().unstack().round(1)
weekend_ratio = (pivot[1] / pivot[0]).round(2)
most_weekday = weekend_ratio.idxmin()
```

### explain
Форматы ведут себя противоположно: кофейня в бизнес-центре в выходные теряет две трети выручки, в торговом центре — получает на треть больше, уличная — чуть больше. Средний «эффект выходного» по сети ничего не говорит ни об одной кофейне. Это и есть **взаимодействие** признаков — запомним его.

## task: split | Шаг 2. Признаки и разбиение по времени | base

Напишите функцию `prep(s)`, которая добавляет `weekday`, `month`, `weekend`, `day_n` (дней от фиксированной даты 2024-01-01) и возвращает таблицу признаков: `temp`, `rain`, `holiday`, `promo`, `weekday`, `month`, `weekend`, `day_n` плюс флаги `shop_id` и `format` (`pd.get_dummies(..., columns=["shop_id", "format"], dtype=int)`). Для этой карточки дата выпуска — 1 июля. Возьмите обучающую историю из исходного daily_sales.csv до этой даты. По ней заранее сохраните порядок столбцов категорий и месячный сценарий. Подготовка одной новой строки может использовать сохранённые значения или прочитать ту же историю из файла. Для ещё неизвестной погоды подставьте для каждого месяца среднюю температуру и долю дождливых дней из доступной истории. Одиночный день должен получить те же признаки, что и в полном пакете. Разделите данные по времени: `train` — даты до 2025-07-01, `test` — с этой даты. Сохраните `X`, маску `tr` (True для обучающих строк), `n_train`, `n_test`.

### starter
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])

```

### check
```python
import pandas as _pd
s0 = _pd.read_csv('daily_sales.csv', parse_dates=['date'])
X0 = need('X', _pd.DataFrame)
assert len(X0) == len(s0), f'В X {len(X0)} строк, а в данных {len(s0)}.'
need_cols = {'temp', 'rain', 'holiday', 'promo', 'weekday', 'month', 'weekend', 'day_n'}
assert need_cols <= set(X0.columns), f'Не хватает столбцов: {need_cols - set(X0.columns)}.'
assert any(c.startswith('shop_id_') for c in X0.columns) and any(c.startswith('format_') for c in X0.columns), 'Нужны флаги shop_id_… и format_….'
assert 'revenue_k' not in X0.columns and 'date' not in X0.columns and 'city' not in X0.columns, 'В признаках не должно быть revenue_k, date и city.'
assert X0['day_n'].min() == 0 and X0['day_n'].max() == 730, 'day_n — дней от первой даты (от 0 до 730).'
w = (s0['date'] < '2025-07-01')
assert need('n_train') == int(w.sum()) and need('n_test') == int((~w).sum()), f'n_train, n_test = {need("n_train")}, {need("n_test")}.'
_mask = need('tr')
assert _mask.index.equals(w.index) and (_mask == w).all(), 'tr: каждый ID должен соответствовать дате до01.07.2025.'
_source = s0.copy()
_source['weekday'] = _source['date'].dt.weekday
_source['month'] = _source['date'].dt.month
_source['weekend'] = (_source['weekday'] >= 5).astype(int)
_source['day_n'] = (_source['date'] - _pd.Timestamp('2024-01-01')).dt.days
for _weather in ('temp','rain'):
    _source[_weather] = _source[_weather].astype(float)
    _climate = s0[w].groupby(s0.loc[w,'date'].dt.month)[_weather].mean()
    _source.loc[~w,_weather] = _source.loc[~w,'month'].map(_climate)
_ref = _pd.get_dummies(_source[['temp','rain','holiday','promo','weekday','month','weekend','day_n','shop_id','format']], columns=['shop_id','format'],dtype=int)
assert X0.index.equals(_ref.index) and list(X0.columns)==list(_ref.columns) and (X0 == _ref).all().all(), 'X: неверные значения/индексы; не заменяйте погоду целевой выручкой.'
_f = need('prep')
_one = s0.iloc[[1000]].copy()
assert _f(_one).columns.tolist()==_ref.columns.tolist() and (_f(_one).iloc[0] == _ref.loc[_one.index[0]]).all(), 'Одиночная дата должна давать тот же day_n и схему, что в пакете.'

```

### hint
Начните с истории до выпуска: сохраните порядок флагов и таблицу «месяц → средняя температура, доля дождливых дней». Для одной будущей строки присоедините сценарий по месяцу и выровняйте флаги по сохранённым колонкам. Можно заранее собрать справочники вне prep или загрузить историю внутри функции. Для доли дождя используйте дробный тип.

### hint
`day_n = (s["date"] - pd.Timestamp("2024-01-01")).dt.days`. Маска — `s["date"] < "2025-07-01"`.

### solution
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])

def prep(s, as_of="2025-07-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)

X = prep(s)
tr = s["date"] < "2025-07-01"
n_train, n_test = int(tr.sum()), int((~tr).sum())
```

### explain
Почему не `train_test_split`: при случайном разбиении в обучении оказались бы и 10, и 12 декабря 2025, а проверяли бы мы на 11-м — модель «знала бы» соседние дни из будущего. В этом брифе прогноз на декабрь выдаётся уже 1 июля. Поэтому всё, что про время, проверяют только «прошлое → будущее».

## task: baselines | Шаг 3. Ориентиры | base

Для выпуска утром **1 апреля** посчитайте две MAE на валидации с 1 апреля по 30 июня 2025 включительно.

- `mae_lag7` — ошибка замороженного недельного ориентира. Для каждой кофейни и дня недели возьмите последнюю известную до выпуска выручку. Повторяйте эту сумму для всех таких дат валидации.
- `mae_lin` — ошибка LinearRegression на признаках апрельского выпуска. Обучите модель на строках до 1 апреля.

Округлите обе ошибки до двух знаков и сохраните в `lin_better` результат сравнения `mae_lin < mae_lag7`. Единица каждой ошибки — тыс. ₽ дневной выручки на кофейню.

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"])
s = s.loc[s["date"] < "2025-07-01"].copy()
def prep(s, as_of="2025-04-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)
```

### starter
```python
# уже есть: s (таблица) и prep(s) из шага 2
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

s = s.sort_values(["shop_id", "date"]).reset_index(drop=True)
X = prep(s, as_of="2025-04-01")
y = s["revenue_k"]
tr = s["date"] < "2025-04-01"

```

### check
```python
import pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae
s0 = _pd.read_csv('daily_sales.csv', parse_dates=['date']).sort_values(['shop_id', 'date']).reset_index(drop=True)
s0 = s0.loc[s0['date'] < '2025-07-01'].copy()
X0 = prep(s0, as_of='2025-04-01')
y0 = s0['revenue_k']
t0 = s0['date'] < '2025-04-01'
_history = s0[t0].assign(weekday=s0.loc[t0,'date'].dt.weekday).sort_values('date')
_last = _history.groupby(['shop_id','weekday'])['revenue_k'].last()
lag = _pd.Series([_last.loc[(row.shop_id,row.date.weekday())] for row in s0.itertuples()],index=s0.index)
ml = round(_mae(y0[~t0], lag[~t0]), 2)
mn = round(_mae(y0[~t0], _LR().fit(X0[t0], y0[t0]).predict(X0[~t0])), 2)
assert close(need('mae_lag7'), ml, 0.011), f'mae_lag7 = {need("mae_lag7")}, а нужно {ml}.'
assert close(need('mae_lin'), mn, 0.011), f'mae_lin = {need("mae_lin")}, а нужно {mn}.'
assert need('lin_better') == (mn < ml), f'lin_better = {need("lin_better")}.'
```

### hint
Разбейте задачу на две таблицы. В истории `s[tr]` отсортируйте даты, добавьте день недели и возьмите последнее значение по `shop_id` и дню недели. К будущим строкам присоедините этот справочник по тем же двум ключам.

### hint
Проверьте один ключ руками. Для всех будущих вторников кофейни источником служит её последняя продажа во вторник до 1 апреля. Оба ориентира сравните на одних будущих строках.

### solution
```python
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

s = s.sort_values(["shop_id", "date"]).reset_index(drop=True)
X = prep(s, as_of="2025-04-01")
y = s["revenue_k"]
tr = s["date"] < "2025-04-01"

history = s[tr].assign(weekday=s.loc[tr,'date'].dt.weekday).sort_values('date')
last = history.groupby(['shop_id','weekday'])['revenue_k'].last()
lag7 = pd.Series([last.loc[(r.shop_id,r.date.weekday())] for r in s.itertuples()], index=s.index)
mae_lag7 = round(mean_absolute_error(y[~tr], lag7[~tr]), 2)
lin = LinearRegression().fit(X[tr], y[tr])
mae_lin = round(mean_absolute_error(y[~tr], lin.predict(X[~tr])), 2)
lin_better = mae_lin < mae_lag7
```

### explain
Недельный ориентир сохраняет характер конкретной точки и дня недели. Например, все июньские субботы бизнес-центра получают одно значение из его мартовской истории. Сравните с ошибкой линейной модели на тех же датах. Разница в MAE выражена в тысячах рублей дневной выручки на кофейню.

## task: interactions | Шаг 4. Взаимодействия руками | base

Помогите линейной модели: добавьте к `X` три признака-произведения — `bc_off` (бизнес-центр × (выходной или праздник)), `mall_off` (ТЦ × (выходной или праздник)) и `street_rain` (улица × дождь). Обучите `LinearRegression` и сохраните `mae_inter` (2 знака) и `gain` — на сколько тысяч рублей ошибка меньше, чем у простой линейной модели (2 знака).

В этой карточке отложенный период — апрель–июнь. Июль–декабрь понадобится в последнем сравнении.

### setup
```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s, as_of="2025-07-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)
s = s[s["date"] < "2025-07-01"].copy()
X = prep(s, as_of="2025-04-01")
y = s["revenue_k"]
tr = s["date"] < "2025-04-01"
mae_lin = mean_absolute_error(y[~tr], LinearRegression().fit(X[tr], y[tr]).predict(X[~tr]))
```

### starter
```python
# уже есть: s, X, y, tr и mae_lin — ошибка простой линейной модели
off = ((X["weekend"] + X["holiday"]) > 0).astype(int)     # выходной или праздник

```

### check
```python
from sklearn.linear_model import LinearRegression as _LR
from sklearn.metrics import mean_absolute_error as _mae
X0 = prep(s, as_of="2025-04-01"); off0 = ((X0['weekend'] + X0['holiday']) > 0).astype(int)
X0['bc_off'] = X0['format_бизнес-центр'] * off0; X0['mall_off'] = X0['format_ТЦ'] * off0; X0['street_rain'] = X0['format_улица'] * X0['rain']
m = round(_mae(y[~tr], _LR().fit(X0[tr], y[tr]).predict(X0[~tr])), 2)
assert close(need('mae_inter'), m, 0.011), f'mae_inter = {need("mae_inter")}, а нужно {m}. Проверьте три новых признака.'
assert close(need('gain'), round(mae_lin - m, 2), 0.02), f'gain = {need("gain")}.'
```

### hint
Взаимодействие — произведение двух признаков: оно равно 1, только когда оба условия выполнены (бизнес-центр и выходной).

### hint
`X2 = X.copy()`, `X2["bc_off"] = X2["format_бизнес-центр"] * off` и так далее.

### solution
```python
off = ((X["weekend"] + X["holiday"]) > 0).astype(int)
X2 = X.copy()
X2["bc_off"] = X2["format_бизнес-центр"] * off
X2["mall_off"] = X2["format_ТЦ"] * off
X2["street_rain"] = X2["format_улица"] * X2["rain"]
lin2 = LinearRegression().fit(X2[tr], y[tr])
mae_inter = round(mean_absolute_error(y[~tr], lin2.predict(X2[~tr])), 2)
gain = round(mae_lin - mae_inter, 2)
```

### explain
Взаимодействие даёт модели отдельную поправку на выходной для бизнес-центра и для торгового центра. Сравните две MAE на своих данных и проверьте знак выигрыша. При отрицательном выигрыше дополнительные признаки ухудшили оценку.

## task: boosting | Шаг 5. Бустинг и лес | base

На исходных признаках `X` (без ручных взаимодействий) обучите `HistGradientBoostingRegressor(random_state=0)` и `RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0)`. Сохраните `mae_hgb`, `mae_rf` (2 знака) и `best_model` — `"бустинг"`, `"лес"` или `"линейная с взаимодействиями"` (её ошибка — `mae_inter` в заготовке).

В этой карточке отложенный период — апрель–июнь. Июль–декабрь понадобится в последнем сравнении.

### setup
```python
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s, as_of="2025-07-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)
s = s[s["date"] < "2025-07-01"].copy()
X = prep(s, as_of="2025-04-01")
y = s["revenue_k"]
tr = s["date"] < "2025-04-01"
_off = ((X["weekend"] + X["holiday"]) > 0).astype(int)
_X2 = X.copy(); _X2["bc_off"] = _X2["format_бизнес-центр"] * _off; _X2["mall_off"] = _X2["format_ТЦ"] * _off; _X2["street_rain"] = _X2["format_улица"] * _X2["rain"]
mae_inter = mean_absolute_error(y[~tr], LinearRegression().fit(_X2[tr], y[tr]).predict(_X2[~tr]))
```

### starter
```python
# уже есть: s, X, y, tr и mae_inter — ошибка линейной модели с взаимодействиями
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

```

### check
```python
from sklearn.ensemble import HistGradientBoostingRegressor as _H, RandomForestRegressor as _RF
from sklearn.metrics import mean_absolute_error as _mae
h = round(_mae(y[~tr], _H(random_state=0).fit(X[tr], y[tr]).predict(X[~tr])), 2)
r = round(_mae(y[~tr], _RF(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X[tr], y[tr]).predict(X[~tr])), 2)
assert close(need('mae_hgb'), h, 0.011), f'mae_hgb = {need("mae_hgb")}, а нужно {h}.'
assert close(need('mae_rf'), r, 0.011), f'mae_rf = {need("mae_rf")}, а нужно {r}.'
res = {'бустинг': h, 'лес': r, 'линейная с взаимодействиями': round(mae_inter, 2)}
assert need('best_model') == min(res, key=res.get), f'best_model = {need("best_model")!r}.'
```

### hint
Обучение на `X[tr], y[tr]`, прогноз на `X[~tr]`.

### hint
Обе модели — с `random_state=0`; MAE — `mean_absolute_error(y[~tr], pred)`.

### solution
```python
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

hgb = HistGradientBoostingRegressor(random_state=0).fit(X[tr], y[tr])
rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0).fit(X[tr], y[tr])
mae_hgb = round(mean_absolute_error(y[~tr], hgb.predict(X[~tr])), 2)
mae_rf = round(mean_absolute_error(y[~tr], rf.predict(X[~tr])), 2)
res = {"бустинг": mae_hgb, "лес": mae_rf, "линейная с взаимодействиями": round(mae_inter, 2)}
best_model = min(res, key=res.get)
```

### explain
Деревья допускают разные зависимости для сочетаний формата и дня недели. Сопоставьте MAE двух ансамблей и линейной модели при одинаковой информации о погоде. Результат на апреле–июне оценивает прогноз, но ещё не показывает экономию на сменах.

## task: tune | Шаг 6. Подбор на валидации | plus

Это отдельное исследование настройки по MAE. Для апрельского выпуска подберите бустинг по отложенным наблюдениям. Валидация — апрель–июнь 2025 (`val`: обучающие строки с датой от 2025-04-01), обучение для подбора — даты до 2025-04-01 (`fit`). Для каждой пары `learning_rate` в `[0.05, 0.1]` и `max_depth` в `[3, 6, None]` обучите `HistGradientBoostingRegressor(learning_rate=..., max_depth=..., max_iter=500, early_stopping=False, random_state=0)` на `fit`, по `staged_predict` найдите лучшее число итераций на `val` и его MAE. Сохраните DataFrame `grid` (столбцы `lr`, `depth`, `n_iter`, `val_mae`), лучшую строку — в `best` (Series), зафиксируйте выбранное число деревьев как итог этой лабораторной работы. В шаге 8 сравниваются пять заранее заданных процедур по RMSE, включая HGB с настройками по умолчанию. В `val_mae` верните ошибку лучшей строки, округлённую до двух знаков. Осторожно: в DataFrame глубина `None` превращается в `NaN`, а `HistGradientBoostingRegressor(max_depth=nan)` падает с ошибкой. Переведите её обратно: `None if pd.isna(best["depth"]) else int(best["depth"])`.

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s, as_of="2025-07-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)
X = prep(s, as_of="2025-04-01")
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"
```

### starter
```python
# уже есть: s, X, y, tr
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

fit = s["date"] < "2025-04-01"
val = tr & ~fit

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.metrics import mean_absolute_error as _mae
f0 = s['date'] < '2025-04-01'; v0 = tr & ~f0; rows = []
for lr in [0.05, 0.1]:
    for md in [3, 6, None]:
        m = _H(learning_rate=lr, max_depth=md, max_iter=500, early_stopping=False, random_state=0).fit(X[f0], y[f0])
        cv = [_mae(y[v0], p) for p in m.staged_predict(X[v0])]; k = int(_np.argmin(cv)) + 1
        rows.append((lr, md, k, cv[k - 1]))
g = need('grid', _pd.DataFrame)
assert {'lr', 'depth', 'n_iter', 'val_mae'} <= set(g.columns), 'В grid нужны столбцы lr, depth, n_iter и val_mae.'
assert len(g) == 6, f'В grid {len(g)} строк, нужно 6.'
def _grid_key(row):
    return (float(row['lr']), None if _pd.isna(row['depth']) else float(row['depth']))
_expected_rows = {(lr, md): (k, v) for lr, md, k, v in rows}
_submitted_keys = [_grid_key(row) for _, row in g.iterrows()]
assert len(set(_submitted_keys)) == 6 and set(_submitted_keys) == set(_expected_rows), 'grid: нужны ровно шесть разных пар lr из [0.05, 0.1] и depth из [3, 6, None]; каждая строка должна сохранять параметры своего расчёта. Порядок строк может быть любым.'
for _, row in g.iterrows():
    _key = _grid_key(row)
    _k, _v = _expected_rows[_key]
    assert row['n_iter'] == _k and close(row['val_mae'], _v, 0.01), f'lr={_key[0]}, depth={_key[1]}: n_iter и val_mae должны относиться к этой паре параметров.'
b = min(rows, key=lambda r: r[3])
assert close(need('val_mae'), round(b[3], 2), 0.011), 'Сохраните MAE лучшей строки на апреле–июне.'
_submitted_best = need('best', _pd.Series)
assert (_grid_key(_submitted_best) == (b[0], b[1])
        and _submitted_best['n_iter'] == b[2]
        and close(_submitted_best['val_mae'], b[3], 0.01)), 'best должна сохранять параметры, число деревьев и ошибку лучшей строки grid; не меняйте её lr/depth после расчёта.'

```

### hint
`max_depth=None` — без ограничения глубины (ограничивает число листьев). Строки grid собирайте словарями в список в порядке: lr 0.05 (depth 3, 6, None), потом lr 0.1.

### hint
Лучшая строка: `grid.loc[grid["val_mae"].idxmin()]`. Числа из неё приходят как `float`: `max_iter` переведите через `int(...)`, а глубину — как сказано в условии, через `pd.isna(...)`.

### solution
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

fit = s["date"] < "2025-04-01"
val = tr & ~fit

rows = []
for lr in [0.05, 0.1]:
    for depth in [3, 6, None]:
        m = HistGradientBoostingRegressor(learning_rate=lr, max_depth=depth, max_iter=500,
                                          early_stopping=False, random_state=0).fit(X[fit], y[fit])
        curve = [mean_absolute_error(y[val], p) for p in m.staged_predict(X[val])]
        k = int(np.argmin(curve)) + 1
        rows.append({"lr": lr, "depth": depth, "n_iter": k, "val_mae": curve[k - 1]})
grid = pd.DataFrame(rows)
best = grid.loc[grid["val_mae"].idxmin()]
val_mae = round(float(best["val_mae"]), 2)
```

### explain
В каждой строке сетки посмотрите, на какой итерации ошибка перестала уменьшаться. Если минимум оказался на последней разрешённой итерации, таблица показывает лучшую проверенную точку. Чтобы расширить сетку, используйте прежний период разработки и снова зафиксируйте результат до финальной оценки.

## task: trend | Шаг 7. Ловушка тренда | plus

Посмотрите на ошибки бустинга по умолчанию (`HistGradientBoostingRegressor(random_state=0)`) на апреле–июне по месяцам: средняя ошибка `факт − прогноз` больше нуля значит, что модель занижает прогноз. Сеть растёт, а деревья не умеют продолжать тренд за пределы обучающих данных: для всех дат после марта 2025 `day_n` «как самый поздний известный день».

Проверьте, помогает ли отдельный тренд. Оцените тренд линейной регрессией логарифма выручки на `day_n` по обучающим строкам, `trend = np.exp(модель.predict(s[["day_n"]]))`. Обучите бустинг (`random_state=0`) на признаках **без** `day_n` с ответом `y / trend`, а прогноз умножьте обратно на `trend`. Сохраните векторы прогнозов до и после поправки как `p_before` и `p_after` в порядке валидационных строк. Сохраните `bias_by_month` — среднюю ошибку `факт − прогноз` бустинга по умолчанию по месяцам валидации (Series с индексом-номером месяца, 2 знака), `bias_before` и `bias_after` — среднюю ошибку `факт − прогноз` на всей валидации до и после (2 знака), `mae_after` (2 знака) и `growth` — годовой рост по тренду (`np.exp(коэффициент × 365)`, 3 знака).

### setup
```python
import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s, as_of="2025-07-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)
s = s[s["date"] < "2025-07-01"].copy()
X = prep(s, as_of="2025-04-01")
y = s["revenue_k"]
tr = s["date"] < "2025-04-01"
s["day_n"] = X["day_n"]
```

### starter
```python
# уже есть: s (со столбцом day_n), X, y, tr
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import HistGradientBoostingRegressor as _H
from sklearn.metrics import mean_absolute_error as _mae
p0 = _H(random_state=0).fit(X[tr], y[tr]).predict(X[~tr])
tl = _LR().fit(s.loc[tr, ['day_n']], _np.log(y[tr])); trd = _np.exp(tl.predict(s[['day_n']]))
Xn = X.drop(columns=['day_n'])
p1 = _H(random_state=0).fit(Xn[tr], (y / trd)[tr]).predict(Xn[~tr]) * trd[~tr]
bm = (y[~tr] - p0).groupby(s.loc[~tr, 'date'].dt.month).mean().round(2)
for _name, _pred in [('p_before', p0), ('p_after', p1)]:
    _got = _np.asarray(need(_name))
    assert _got.shape == _pred.shape and _np.allclose(_got, _pred, atol=1e-4), f'{_name}: проверьте вектор прогнозов на валидационных строках.'
gb = need('bias_by_month', _pd.Series)
assert sorted(int(k) for k in gb.index) == sorted(int(k) for k in bm.index), f'Индекс bias_by_month — месяцы валидации, а сейчас {[int(k) for k in gb.index]}.'
assert all(close(gb[k], bm[k], 0.011) for k in bm.index), f'bias_by_month: ожидалось {({int(k): float(v) for k, v in bm.items()})}.'
assert close(need('bias_before'), round((y[~tr] - p0).mean(), 2), 0.011), f'bias_before = {need("bias_before")}.'
assert close(need('bias_after'), round((y[~tr] - p1).mean(), 2), 0.011), f'bias_after = {need("bias_after")}.'
assert close(need('mae_after'), round(_mae(y[~tr], p1), 2), 0.011), f'mae_after = {need("mae_after")}.'
assert close(need('growth'), round(_np.exp(tl.coef_[0] * 365), 3), 0.0011), f'growth = {need("growth")}.'
```

### hint
Ошибки по месяцам: `(y[~tr] - p_before).groupby(s.loc[~tr, "date"].dt.month).mean().round(2)`. Деревья не продолжают тренд: за пределами обучения прогноз «застывает» на уровне последних листьев. Поэтому тренд снимают отдельно линейной моделью, а бустинг учат на остатке.

### hint
Тренд: `tl = LinearRegression().fit(s.loc[tr, ["day_n"]], np.log(y[tr]))`. Коэффициент — `tl.coef_[0]`.

### hint
`trend` — массив numpy, поэтому его часть для теста — `trend[~tr.values]` или просто `trend[~tr]`.

### solution
```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

p_before = HistGradientBoostingRegressor(random_state=0).fit(X[tr], y[tr]).predict(X[~tr])
bias_by_month = (y[~tr] - p_before).groupby(s.loc[~tr, "date"].dt.month).mean().round(2)
bias_before = round((y[~tr] - p_before).mean(), 2)
print(bias_by_month)

tl = LinearRegression().fit(s.loc[tr, ["day_n"]], np.log(y[tr]))
trend = np.exp(tl.predict(s[["day_n"]]))
growth = round(np.exp(tl.coef_[0] * 365), 3)

Xn = X.drop(columns=["day_n"])
m = HistGradientBoostingRegressor(random_state=0).fit(Xn[tr], (y / trend)[tr])
p_after = m.predict(Xn[~tr]) * trend[~tr]
bias_after = round((y[~tr] - p_after).mean(), 2)
mae_after = round(mean_absolute_error(y[~tr], p_after), 2)
```

### explain
Посмотрите на знак месячного смещения. Положительная разница означает, что продажи были выше прогноза. Сравните одну и ту же валидацию для обычного бустинга и версии с трендом. В шаге 8 они войдут в общий выбор модели.

## task: compare | Шаг 8. Сравнение: качество и время | plus

Операционному директору нужен разовый прогноз на 1 июля. Сначала разделите два этапа:

| Этап | Дата выпуска | Обучение | Период оценки |
|---|---|---|---|
| Выбор процедуры | 1 апреля 2025 | до 1 апреля | апрель–июнь 2025 |
| Финальный отчёт | 1 июля 2025 | до 1 июля | июль–декабрь 2025 |

В словаре `models` заготовки заданы пять процедур и их параметры. Для независимых экземпляров апрельского и июльского выпусков подходит `copy.deepcopy(model)`, включая учебный TrendBoost. Используйте эти же определения при июльском переобучении. Взаимодействия шага 4 и MAE-настройка шага 6 были отдельными экспериментами. Для апрельского выпуска получите признаки через `prep(s, as_of="2025-04-01")`: погода после даты выпуска известна только как сценарий. Обучите каждую процедуру на истории до апреля, на апреле–июне рассчитайте `val_rmse` с полной точностью и выберите `best` по минимуму. Затем переобучите все процедуры на истории до июля: таблица `X` уже подготовлена для июльского выпуска. Один раз оцените их на июле–декабре. Сохраните `table` с индексом по названию процедуры, отсортированную по `val_rmse`. Округляйте `val_rmse` только при печати.

Для каждой строки сохраните `rmse` и `mae` финального периода в тыс. ₽ (2 знака). Финальное обучение выполните через `fit_s = timed_fit(name, model, X[tr], y[tr])`, пакетный прогноз — через `pred, predict_ms = timed_predict(name, model, X[~tr])`. Готовые функции сами вызывают модель и замеряют интервал непосредственно вокруг fit/predict: первая возвращает секунды, вторая — прогноз и миллисекунды. Сохраните возвращённые интервалы без округления. Апрельский выбор можно считать обычными fit/predict; замеры нужны для финального прохода.

В `gain_vs_linear` запишите, на сколько финальный RMSE выбранной процедуры ниже линейной модели (2 знака). В `nightly_ok` запишите True, если **каждый** из пяти финальных fit в отдельности занял меньше 60 секунд на вашем компьютере. Для оценки длительности полного ночного цикла понадобятся также подготовка данных, все фактически запускаемые обучения, при необходимости подбор, пакетный прогноз и выдача результата. В блокноте библиотек вы отдельно измерите подбор числа деревьев и финальное обучение.

Для замера используйте процедуры из заготовки. Допустима своя обёртка, если её fit и predict действительно вызывают соответствующие операции входящих в процедуру оценщиков. Обучение до секундомера с возвратом готовой модели внутри timed_fit не является замером обучения.

### setup
```python
from time import perf_counter as _measurement_clock
_measurements = {}
def _timed_estimator_call(method, operation):
    # Install and remove observers outside the measured interval. A delegating
    # wrapper may call any of the supplied estimators; returning a cache is not fit.
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                                  HistGradientBoostingRegressor)
    classes = (LinearRegression, RandomForestRegressor,
               GradientBoostingRegressor, HistGradientBoostingRegressor)
    originals = [(cls, getattr(cls, method), method in cls.__dict__) for cls in classes]
    calls = []
    def observe(original):
        def wrapped(estimator, *args, **kwargs):
            calls.append(estimator)
            return original(estimator, *args, **kwargs)
        return wrapped
    try:
        for cls, original, _owned in originals:
            setattr(cls, method, observe(original))
        start = _measurement_clock()
        result = operation()
        elapsed = _measurement_clock() - start
    finally:
        for cls, original, owned in originals:
            if owned:
                setattr(cls, method, original)
            else:
                delattr(cls, method)
    assert calls, ('Внутри timed_' + method + ' должен выполняться настоящий ' +
                   method + ' оценщика из процедуры. Возврат заранее готового ' +
                   'результата не измеряет эту операцию; обёртка должна делегировать вызов.')
    return result, elapsed

def timed_fit(name, model, features, target):
    """Обучить модель; вернуть длительность вызова fit в секундах."""
    _, elapsed = _timed_estimator_call('fit', lambda: model.fit(features, target))
    _measurements[name] = dict(model=model, train=features.copy(), target=target.copy(), fit_s=elapsed)
    return elapsed

def timed_predict(name, model, features):
    """Вернуть (пакетный прогноз, длительность predict в миллисекундах)."""
    prediction, elapsed = _timed_estimator_call('predict', lambda: model.predict(features))
    elapsed_ms = elapsed * 1000
    record = _measurements[name]
    assert record['model'] is model, 'Передайте в timed_predict ту же модель, что в timed_fit.'
    record.update(test=features.copy(), predict_ms=elapsed_ms)
    return prediction, elapsed_ms

import pandas as pd
s = pd.read_csv("daily_sales.csv", parse_dates=["date"]).sort_values(["shop_id", "date"]).reset_index(drop=True)
def prep(s, as_of="2025-07-01"):
    s = s.copy()
    history = pd.read_csv('daily_sales.csv', parse_dates=['date'])
    history = history[history['date'] < as_of]
    future = s['date'] >= as_of
    for weather in ('temp','rain'):
        s[weather] = s[weather].astype(float)
        climate = history.groupby(history['date'].dt.month)[weather].mean()
        s.loc[future, weather] = s.loc[future,'date'].dt.month.map(climate)
    s["weekday"] = s["date"].dt.weekday
    s["month"] = s["date"].dt.month
    s["weekend"] = (s["weekday"] >= 5).astype(int)
    s["day_n"] = (s["date"] - pd.Timestamp("2024-01-01")).dt.days
    cols = ["temp", "rain", "holiday", "promo", "weekday", "month", "weekend", "day_n", "shop_id", "format"]
    result = pd.get_dummies(s[cols], columns=["shop_id", "format"], dtype=int)
    schema = ['temp','rain','holiday','promo','weekday','month','weekend','day_n'] + ['shop_id_'+v for v in sorted(history.shop_id.unique())] + ['format_'+v for v in sorted(history['format'].unique())]
    return result.reindex(columns=schema, fill_value=0)
X = prep(s)
y = s["revenue_k"]
tr = s["date"] < "2025-07-01"

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor

class TrendBoost:
    """Процедура из шага 7 с тем же интерфейсом fit/predict."""
    def fit(self, features, target):
        self.trend = LinearRegression().fit(features[["day_n"]], np.log(target))
        level = np.exp(self.trend.predict(features[["day_n"]]))
        self.residual = HistGradientBoostingRegressor(random_state=0)
        self.residual.fit(features.drop(columns="day_n"), target / level)
        return self

    def predict(self, features):
        level = np.exp(self.trend.predict(features[["day_n"]]))
        return level * self.residual.predict(features.drop(columns="day_n"))
```

### starter
```python
# доступны s, y, tr, функция prep(s, as_of) и X для выпуска 1 июля
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

models = {
    "линейная": LinearRegression(),
    "лес": RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0),
    "GradientBoosting": GradientBoostingRegressor(random_state=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(random_state=0),
    "тренд + бустинг": TrendBoost(),
}

```

### check
```python
import numpy as _np, pandas as _pd
from sklearn.linear_model import LinearRegression as _LR
from sklearn.ensemble import GradientBoostingRegressor as _GB, HistGradientBoostingRegressor as _H, RandomForestRegressor as _RF
from sklearn.metrics import mean_absolute_error as _mae, mean_squared_error as _mse
ref = {}
for k, m in {'линейная': _LR(), 'лес': _RF(n_estimators=100, min_samples_leaf=3, random_state=0),
             'GradientBoosting': _GB(random_state=0), 'HistGradientBoosting': _H(random_state=0), 'тренд + бустинг': TrendBoost()}.items():
    p = m.fit(X[tr], y[tr]).predict(X[~tr])
    ref[k] = (round(float(_np.sqrt(_mse(y[~tr], p))), 2), round(float(_mae(y[~tr], p)), 2))
t = need('table', _pd.DataFrame)
assert set(t.index) == set(ref), f'Индекс table — названия моделей {sorted(ref)}, а сейчас {list(t.index)}.'
assert {'val_rmse', 'rmse', 'mae', 'fit_s', 'predict_ms'} <= set(t.columns), f'Нужны столбцы val_rmse, rmse, mae, fit_s, predict_ms, а сейчас {list(t.columns)}.'
for k, (r, a) in ref.items():
    assert close(t.loc[k, 'rmse'], r, 0.011), f'{k}: rmse = {t.loc[k, "rmse"]}, а нужно {r}. Обучение на tr, ошибка на ~tr.'
    assert close(t.loc[k, 'mae'], a, 0.011), f'{k}: mae = {t.loc[k, "mae"]}, а нужно {a}.'
assert t.index.is_unique, 'Названия моделей в table не должны повторяться.'
for _name in t.index:
    assert _name in _measurements, f'{_name}: вызовите timed_fit для финального обучения.'
    _record = _measurements[_name]
    assert 'predict_ms' in _record, f'{_name}: вызовите timed_predict после timed_fit.'
    assert _record['train'].equals(X[tr]) and _record['target'].equals(y[tr]), f'{_name}: timed_fit должен обучать на финальной тренировочной части.'
    assert _record['test'].equals(X[~tr]), f'{_name}: timed_predict должен получать весь финальный тест.'
    for _col in ('fit_s', 'predict_ms'):
        assert _np.isfinite(t.loc[_name, _col]) and close(t.loc[_name, _col], _record[_col], 1e-9), f'{_name}: {_col} не совпало с фактическим интервалом. Запишите результат timed_fit/timed_predict без подмены и округления.'
assert list(t.index) == list(t.sort_values('val_rmse').index), 'Строки table должны идти по возрастанию val_rmse.'
assert need('best') == t['val_rmse'].idxmin(), f'best = {need("best")!r}.'
g = round(float(t.loc['линейная', 'rmse'] - t.loc[need('best'), 'rmse']), 2)
assert close(need('gain_vs_linear'), g, 0.011), f'gain_vs_linear = {need("gain_vs_linear")}, а по таблице {g}: RMSE линейной минус RMSE лучшей.'
assert need('nightly_ok') == bool((t['fit_s'] < 60).all()), f'nightly_ok = {need("nightly_ok")}: все ли fit_s меньше 60 секунд по вашей таблице?'
_vX = prep(s, as_of='2025-04-01')
_vtrain = s['date'] < '2025-04-01'
_val = (s['date'] >= '2025-04-01') & tr
for _name, _model in {'линейная': _LR(), 'лес': _RF(n_estimators=100,min_samples_leaf=3,random_state=0), 'GradientBoosting': _GB(random_state=0), 'HistGradientBoosting': _H(random_state=0), 'тренд + бустинг': TrendBoost()}.items():
    _vp = _model.fit(_vX[_vtrain],y[_vtrain]).predict(_vX[_val])
    assert close(t.loc[_name,'val_rmse'],float(_np.sqrt(_mse(y[_val],_vp))),1e-6), f'{_name}: проверьте апрельский выпуск. Готовьте признаки для обучения и валидации через prep(s, as_of="2025-04-01"), обучайтесь до апреля и оценивайте апрель–июнь. Записывайте val_rmse без округления.'

```

### hint
Сделайте два прохода по моделям. В первом используйте признаки апрельского выпуска и найдите минимум валидационного RMSE. Во втором возьмите июльскую таблицу X, заново обучите модели и засеките финальное обучение и прогноз отдельно. Проверьте, что обе даты выпуска присутствуют в вашем коде.

### hint
`fit_s = timed_fit(name, model, X[tr], y[tr])`, затем `pred, predict_ms = timed_predict(name, model, X[~tr])`. RMSE — `np.sqrt(mean_squared_error(y[~tr], pred))`.

### hint
`table = pd.DataFrame(rows).set_index("model").sort_values("val_rmse")`, `best = table.index[0]`, `gain_vs_linear = round(float(table.loc["линейная", "rmse"] - table.loc[best, "rmse"]), 2)`, `nightly_ok = bool((table["fit_s"] < 60).all())`.

### solution
```python
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

models = {
    "линейная": LinearRegression(),
    "лес": RandomForestRegressor(n_estimators=100, min_samples_leaf=3, random_state=0),
    "GradientBoosting": GradientBoostingRegressor(random_state=0),
    "HistGradientBoosting": HistGradientBoostingRegressor(random_state=0),
    "тренд + бустинг": TrendBoost(),
}

rows = []
validation_X = prep(s, as_of='2025-04-01')
validation_train = s['date'] < '2025-04-01'
validation = (s['date'] >= '2025-04-01') & tr
validation_scores = {}
for name, model in models.items():
    vp = model.fit(validation_X[validation_train],y[validation_train]).predict(validation_X[validation])
    validation_scores[name] = float(np.sqrt(mean_squared_error(y[validation],vp)))
best = min(validation_scores, key=validation_scores.get)
for name, model in models.items():
    fit_s = timed_fit(name, model, X[tr], y[tr])
    pred, predict_ms = timed_predict(name, model, X[~tr])

    rows.append({"model": name,
                 "rmse": round(float(np.sqrt(mean_squared_error(y[~tr], pred))), 2),
                 "mae": round(float(mean_absolute_error(y[~tr], pred)), 2),
                 "fit_s": fit_s, "predict_ms": predict_ms, "val_rmse": validation_scores[name]})

table = pd.DataFrame(rows).set_index("model").sort_values("val_rmse")
gain_vs_linear = round(float(table.loc["линейная", "rmse"] - table.loc[best, "rmse"]), 2)
nightly_ok = bool((table["fit_s"] < 60).all())
print(table.round(3))
print(best, gain_vs_linear, nightly_ok)
```

### explain
Прочитайте финальные RMSE и MAE строки, выбранной в апреле–июне. Ошибки остальных процедур помогают описать устойчивость выбора. Если какая-то из них вышла вперёд в итоговом полугодии, для нового выбора потребуется следующий независимый период.

## task: release-row | Новый выпуск: одна строка августовского прогноза | star

Утром **1 августа 2025** управляющая заказывает прогноз на пятницу **8 августа** для PRM-1. Касса и фактическая погода появляются по окончании дня. Архива погодных прогнозов нет. Это тренировочный выпуск, отдельный от основного проекта.

В апрельской валидации строка решения выглядит так: **выпуск 1 апреля → последние доступные касса и фактическая погода 31 марта → на будущую дату можно взять календарь и исторический сценарий погоды**. До просмотра августовских фактов запишите такую же строку для нового выпуска. Какую последнюю пятницу уже можно использовать? При использовании календарного ориентира фактическая погода 8 августа ему не нужна.

Напишите функцию `baseline_at(sales, as_of, target, shop_id)`. Она получает таблицу с датами pandas и возвращает пару «дата источника, выручка в тыс. ₽» для последнего доступного такого же дня недели в этой кофейне. `as_of` — утро выпуска; факты самого дня ещё не поступили. Достаточно решения для случаев, когда в истории есть подходящий день. В заготовке доступна только история до выпуска. Проверка также передаст таблицу с более поздними строками и покажет, изменился ли уже выданный прогноз.

### setup
```python
import pandas as pd
_release_sales = pd.read_csv("daily_sales.csv", parse_dates=["date"])
sales = _release_sales.loc[_release_sales.date < "2025-08-01"].copy()
```

### starter
```python
import pandas as pd

def baseline_at(sales, as_of, target, shop_id):
    ...

print(baseline_at(sales, "2025-08-01", "2025-08-08", "PRM-1"))
```

### check
```python
import pandas as _pd
_forecast = need('baseline_at')
_original = _pd.read_csv('daily_sales.csv', parse_dates=['date'])
for _release, _target, _shop in [('2025-08-01', '2025-08-08', 'PRM-1'), ('2025-06-04', '2025-06-11', 'KZN-1')]:
    _history = _original.loc[_original.date < _release].copy()
    _known = _history.loc[(_history.shop_id == _shop) & (_history.date.dt.weekday == _pd.Timestamp(_target).weekday())]
    _last = _known.loc[_known.date.idxmax()]
    _revised = _original.copy()
    _future = _revised.date >= _release
    _revised.loc[_future, 'revenue_k'] += 100
    _revised.loc[_future, 'temp'] += 10
    _revised.loc[_future, 'rain'] = 1 - _revised.loc[_future, 'rain']
    for _frame in (_history, _revised):
        _result = _forecast(_frame.copy(), _release, _target, _shop)
        assert isinstance(_result, (list, tuple)) and len(_result) == 2, 'Верните дату последнего доступного такого же дня недели и выручку этой кофейни.'
        _day, _value = _result
        assert _pd.Timestamp(_day) == _last.date, f'Выпуск {_release}, кофейня {_shop}. Проверьте день недели и дату источника: касса дня выпуска ещё не закрыта.'
        assert close(_value, _last.revenue_k), f'Выпуск {_release}, кофейня {_shop}. Касса за {_last.date:%d.%m.%Y} уже известна. Выданный ориентир должен сохраниться при изменении более поздней выручки и погоды.'
```

### hint
Сначала ограничьте строки по кофейне и дате строго раньше выпуска. Затем оставьте день недели целевой даты и выберите самую позднюю из оставшихся строк.

### solution
```python
import pandas as pd

def baseline_at(sales, as_of, target, shop_id):
    weekday = pd.Timestamp(target).weekday()
    known = sales[(sales["shop_id"] == shop_id) & (sales["date"] < pd.Timestamp(as_of))]
    same_day = known[known["date"].dt.weekday == weekday]
    last = same_day.loc[same_day["date"].idxmax()]
    return last["date"], float(last["revenue_k"])

print(baseline_at(sales, "2025-08-01", "2025-08-08", "PRM-1"))
```

### explain
К утру 1 августа известны касса и фактическая погода по 31 июля. Последняя известная пятница для PRM-1 — 25 июля. Касса этого дня даёт календарный прогноз 69,6 тыс. ₽ на 8 августа. Позднее можно сравнить его с фактом и посчитать ошибку. Время выпуска задаёт ту же границу и для модели с погодой.
