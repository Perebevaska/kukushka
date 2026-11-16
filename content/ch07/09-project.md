---
title: "Проект: какие заявки довести до договора"
lead: "Финал главы. У «Зерна» есть кофе-кейтеринг для компаний, и заявок больше, чем менеджеры успевают вести. Строим модель-приоритизатор: от осмотра данных и утечки до конвейера, подбора настроек и ответа на вопрос коммерческого директора — сколько договоров окажется в верхних 30 % списка."
files: [catering_leads.csv]
recap:
  - "При сильном дисбалансе доля правильных ничего не говорит: «никто не купит» права в 87 % случаев. Смотрите на полноту, F1, AUC и на метрику, которая повторяет решение бизнеса."
  - "Метрика под задачу: если менеджеры успевают вести 30 % заявок, качество модели — доля договоров, которые попадают в верхние 30 % её списка."
  - "Пропуск — тоже сигнал: заявки без размера компании и без бюджета конвертируются хуже. Категориальный пропуск удобно сделать отдельной категорией «не указан»."
  - "Столбец, который заполняется только после результата (сумма договора), — утечка, даже если выглядит как обычное число."
  - "Из даты-времени получаются признаки: час, день недели, флаг вечерней заявки. Их можно посчитать по каждой строке отдельно, без утечки."
  - "Конвейер + GridSearchCV на обучающей части, затем одна проверка на тесте — схема, которая не обманывает."
  - "Модель находит связь, а не причину: то, что быстрые ответы чаще заканчиваются договором, ещё не доказывает, что ускорение ответа даст договоры. Это проверяет только эксперимент."
---

## Задача

Записка коммерческого директора:

> Заявок на кейтеринг стало много, а менеджеров пять. Плотно вести — созваниваться, готовить меню, возить дегустацию — они успевают примерно 30 % заявок, остальные получают типовое предложение по почте. Сейчас каждый выбирает сам, по ощущению; негласное правило — «сначала повторные клиенты и те, кто пришёл по рекомендации». Нужна модель, которая после первого ответа клиенту ставит заявке приоритет. Сколько прошлых договоров оказалось бы в первых 30 % по модели? И сколько — в двух списках при одинаковом числе звонков?

Учебная CRM синтетическая. В `catering_leads.csv` собраны 3000 заявок компаний на кофе-кейтеринг за январь–сентябрь 2026 года.

Столбцы: `lead_id` — номер заявки, `created` — дата и время заявки, `channel` — откуда пришла (сайт, звонок, рекомендация, соцсети, выставка, тендер), `event_type` — тип мероприятия, `city`, `company_size` — размер компании (до 50 / 50–250 / 250–1000 / 1000+ сотрудников), `guests` — число гостей, `budget_pp` — бюджет на гостя, ₽, `days_to_event` — дней от заявки до мероприятия, `manager` — кто ведёт, `response_hours` — сколько часов прошло до первого ответа менеджера, `repeat_client` — компания уже заказывала (1/0), `tasting` — просили дегустацию (1/0), `contract_rub` — сумма договора. Цель `converted` равна 1, если договор подписан в течение 30 дней после заявки. Время подписи в CSV отсутствует. Для учебного скоринга считаем, что поля заявки, назначенный менеджер и просьба о дегустации фиксируются при регистрации. В рабочей CRM это проверяют по журналу изменений. Длительность ожидания `response_hours` известна к первому ответу.

## Как измерить пользу

В главе 6 модель оценивали долей правильных ответов, а в этой главе выяснили, что при редком классе это обманчиво (урок «Матрица ошибок»). Здесь договор — редкость, и обычные метрики тоже не совсем про вопрос директора. Директору не нужен ответ «да/нет» по каждой заявке: ему нужен **порядок**. Менеджеры возьмут верхние 30 % списка, и важно одно — какая доля всех договоров окажется в этих 30 %.

Назовём это **долей пойманных договоров в топ-30 %**. Это полнота (урок «Precision, recall и F1»), но при пороге, который задан не числом 0.5, а объёмом работы: «сколько заявок мы успеваем». Ориентиры:

- случайные 30 % заявок поймают около 30 % договоров;
- идеальная модель — все 100 %, если договоров меньше 30 % заявок;
- для правила директора отдельно посчитаем, сколько мест оно занимает и сколько договоров охватывает.

Качество ранжирования по всем парам положительных и отрицательных заявок измеряет ROC-AUC (урок «Порог, PR- и ROC-кривые»): насколько часто заявка с договором стоит в списке выше заявки без него. Поэтому настройки будем подбирать по AUC, а отчитываться перед директором — долей пойманных договоров.

::: quiz
Менеджеры обзванивают заявки на кейтеринг по списку из модели и успевают позвонить в 30 % заявок. Какая метрика лучше всего описывает пользу модели?

- [x] Доля всех будущих договоров, которая попала в верхние 30 % списка
  > Так метрика отвечает на вопрос директора: сколько сделок мы поймаем при том же числе звонков.
- [ ] Accuracy на всех заявках
  > Менеджеры звонят не всем, а качество ниже 30 % списка не влияет на результат.
- [ ] ROC-AUC
  > Полезная общая мера ранжирования, но она смотрит на весь список, а не на верхушку.
- [ ] Число заявок в базе
  > Это объём данных, а не качество модели.
:::

## Разберём вместе: метрика директора на десяти заявках

Десять заявок, три закончились договором. Менеджеры успевают 30 % — три заявки. Модель поставила оценки:

| заявка | оценка | договор |
|---|---|---|
| 1 | 0.81 | да |
| 2 | 0.64 | нет |
| 3 | 0.55 | да |
| 4 | 0.40 | нет |
| 5 | 0.33 | да |
| 6 | 0.20 | нет |
| 7–10 | ниже 0.15 | нет |

1. Сортируем по оценке и берём верхние 30 %: заявки 1, 2, 3.
2. Договоров среди них два (1 и 3).
3. Всего договоров три — доля пойманных **2 / 3 ≈ 0.67**.

Случайные три заявки в среднем поймали бы 3 × 3 / 10 = 0.9 договора, то есть **30 %**. Идеальная модель поставила бы наверх все три договора — **100 %**.

::: figure top30-toy
Разбор с десятью заявками: менеджеры берут верхние 30 % списка. Модель ловит два договора из трёх; случайный выбор — в среднем 30 %, идеальная модель — все 100 %.
:::

**Проверьте знаменатели на другом варианте.** Оценки и первые три выбранные заявки те же, но среди неотобранных договор также заключила заявка 8. Сколько договоров поймано из всех договоров и какая доля выбранных заявок закончилась договором? Запишите две дроби. Почему случайная очередь из трёх мест по-прежнему имеет ожидаемый охват 30 %?

Заметьте, что порога 0.5 здесь нет: заявка 4 с оценкой 0.40 не попала в работу не потому, что «меньше половины», а потому, что менеджеров не хватает. Если завтра наймут шестого, топ станет шире, и та же модель даст другую долю. Поэтому метрику считают для того объёма работы, который реально есть.

```python
import numpy as np
score = np.array([0.81, 0.64, 0.55, 0.40, 0.33, 0.20, 0.12, 0.10, 0.08, 0.05])
deal = np.array([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
top = np.argsort(-score)[:int(0.3 * len(score))]
print(deal[top].sum() / deal.sum())
```

Для самостоятельной работы скачайте [каркас блокнота](../notebooks/project-template.ipynb) и [check_notebook.py](../notebooks/check_notebook.py). Поместите `catering_leads.csv` в `data/` рядом с блокнотом. В отчёте сохраните временные границы, выбранные до теста настройки, одну итоговую оценку и две поимённые очереди одинакового размера. Передайте блокнот с выводами, сохранённый `.joblib` и модуль своих шагов подготовки, если они использованы. Проверьте загрузку в новом процессе на сырой строке с новой датой и незнакомой категорией. Рядом укажите версии библиотек и точный порядок выбора при одинаковых рисках.

## План

1. Осмотреть данные: конверсия, пропуски, подозрительные столбцы.
2. Конверсия по каналам и скорости ответа.
3. Что значат пропуски.
4. Признаки из даты и времени заявки.
5. Конвейер и честная оценка кросс-валидацией.
6. Ловушка дисбаланса: доля правильных против F1.
7. Метрика директора и его правило.
8. Подбор настроек `GridSearchCV`.
9. Финальная проверка на тесте: сколько договоров в топ-30 %.
10. Скорость ответа: причина или следствие?

До исследования связей с `converted` зарезервируйте последние 750 заявок по created: первая дата финальной партии 2026-07-21 10:58. Метка созревает через 30 дней; обучение берёт только заявки до 2026-06-21 10:58 (1869 строк), промежуток 381 строк к старту финальной партии ещё не созрел и в fit не входит. Граница определяется датой, а не меткой. В паспорте фиксируйте доступность цели created+30 дней; финальные ответы открываются после их созревания.

В шаге 5 вы соберёте конвейер для сырой заявки. Начиная с шага 6, заготовки получают его подготовку и календарное разбиение. Пять перемешанных фолдов внутри 1869 уже созревших заявок помогают выбрать настройки для одного фиксированного выпуска. Качество на следующем календарном периоде измерим отдельно, после созревания последней метки 25 октября в 21:48.

::: warn Типичные ошибки проекта
- **Сумма договора как признак.** `contract_rub` известна только после подписания — это утечка, модель «угадает» всё.
- **Топ-30 % от всех заявок вместо теста.** Метрику считаем на тех же отложенных заявках, что и прогноз.
- **Отчёт долей правильных.** «87 %» здесь набирает модель «никто не купит».
- **Скорость ответа как рычаг.** Сильный признак ≠ причина; решение о найме дежурного — после A/B-теста.
:::

::: tip
Это повторение всей главы: метрики (уроки «Матрица ошибок», «Precision, recall и F1» и «Порог, PR- и ROC-кривые»), дисбаланс (урок «Дисбаланс классов»), масштабирование (урок «Масштабирование и ближайшие соседи»), признаки (урок «Новые признаки»), конвейер (урок «Pipeline: предобработка и модель вместе») и подбор настроек (урок «Подбор гиперпараметров»). В подсказках указано, на какой урок опирается шаг.
:::

## Вопрос из другой области

Ремонтная служба может осмотреть семь устройств в день. Две модели оценили одни и те же устройства, у нескольких оценок есть ничья на седьмом месте. Задайте порядок по ID до просмотра исходов и составьте две очереди ровно по семь мест. Как сравнить охват реальных поломок на историческом дне с известными исходами всех устройств? Какие данные потребуются для сравнения политик в новом рабочем дне?

## Практика

## task: look | Шаг 1. Осмотр | base

Прочитайте `catering_leads.csv`, преобразуйте `created` в дату со временем и оставьте в `d` 1869 заявок, поступивших до 21 июня 2026 года, 10:58. Все показатели шага относятся к этим зрелым заявкам. Сохраните:

- `conv_rate` — долю заявок с договором (3 знака);
- `n_contracts` — сколько всего договоров;
- `budget_na` — долю заявок с пустым `budget_pp` (3 знака);
- `size_na` — сколько заявок с пустым `company_size`;
- `contract_match` — `True`, если `contract_rub` заполнен **ровно** у тех заявок, где `converted == 1` (и пуст у всех остальных).

### setup
```python

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0().iloc[:1869].copy()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
```

### starter
```python
import pandas as pd
```

### check
```python
_d = _pd0.read_csv('catering_leads.csv').iloc[:1869].copy()
_x = need('d', _pd0.DataFrame)
assert len(_x) == len(_d) and list(_x.columns) == list(_d.columns), 'd — разрешённые1869 зрелых строк разработки.'
assert close(need('conv_rate'), round(_d['converted'].mean(), 3)), f'conv_rate = {need("conv_rate")}, а ожидалось {round(_d["converted"].mean(), 3)}.'
assert need('n_contracts') == _d['converted'].sum(), f'n_contracts = {need("n_contracts")}: это сумма столбца converted.'
assert close(need('budget_na'), round(_d['budget_pp'].isna().mean(), 3)), f'budget_na = {need("budget_na")}, а ожидалось {round(_d["budget_pp"].isna().mean(), 3)}. Доля, а не количество: .isna().mean().'
assert need('size_na') == _d['company_size'].isna().sum(), f'size_na = {need("size_na")}: посчитайте пропуски в company_size.'
_w = bool((_d['contract_rub'].notna() == (_d['converted'] == 1)).all())
assert need('contract_match') == _w, f'contract_match должно быть {_w}: сравните маску «contract_rub заполнен» с converted == 1 по всем строкам.'
```

### hint
Глава 3: `d["budget_pp"].isna().mean()` — доля пропусков, `.sum()` — их число.

### hint
Маска «заполнен» — `d["contract_rub"].notna()`. Сравните её с `d["converted"] == 1` и проверьте, что совпадают все строки: `(… == …).all()`.

### solution
```python
import pandas as pd
d = pd.read_csv("catering_leads.csv").iloc[:1869].copy()
conv_rate = round(d["converted"].mean(), 3)
n_contracts = d["converted"].sum()
budget_na = round(d["budget_pp"].isna().mean(), 3)
size_na = d["company_size"].isna().sum()
contract_match = bool((d["contract_rub"].notna() == (d["converted"] == 1)).all())
print(conv_rate, n_contracts, budget_na, size_na, contract_match)
```

### explain
Договором заканчивается примерно одна заявка из восьми (13 %) — классы несбалансированы сильнее, чем в оттоке гостей. Пропусков много: бюджет на гостя не указан в каждой четвёртой заявке.

А `contract_rub` заполнен ровно у заявок с договором. Сумма договора появляется **после** того, как договор подписан, — в момент, когда менеджер решает, вести ли заявку плотно, её ещё нет. Модель с этим столбцом показала бы почти 100 % и была бы бесполезна: это утечка (глава 6, урок «Категориальные признаки и утечки»). Вместе с `lead_id` (номер ничего не говорит о клиенте) этот столбец в признаки не берём.

## task: groups | Шаг 2. Кто покупает | base

`d` уже загружена. Посчитайте конверсию (долю `converted == 1`):

- `by_channel` — Series: конверсия по каналам `channel`, 3 знака, по убыванию;
- `repeat_rate` и `new_rate` — у повторных (`repeat_client == 1`) и новых клиентов (3 знака);
- `fast_rate` — у заявок, где первый ответ пришёл за час или быстрее (`response_hours <= 1`), и `slow_rate` — где ответа ждали больше 8 часов (3 знака).

### setup
```python

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0().iloc[:1869].copy()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
d = pd.read_csv("catering_leads.csv").iloc[:1869].copy()
```

### starter
```python
# d — таблица заявок
```

### check
```python
_d = _pd0.read_csv('catering_leads.csv').iloc[:1869].copy()
_b = _d.groupby('channel')['converted'].mean().round(3).sort_values(ascending=False)
_x = need('by_channel', _pd0.Series)
assert set(_x.index) == set(_b.index), f'В индексе by_channel: {list(_x.index)}, а нужны все каналы: {list(_b.index)}.'
assert all(close(_x[k], _b[k]) for k in _b.index), 'Конверсия по каналам не совпадает с ожидаемой: groupby("channel")["converted"].mean(), 3 знака.'
assert list(_x.values) == sorted(_x.values, reverse=True), 'by_channel нужно отсортировать по убыванию конверсии.'
_r, _n = round(_d.loc[_d['repeat_client'] == 1, 'converted'].mean(), 3), round(_d.loc[_d['repeat_client'] == 0, 'converted'].mean(), 3)
assert close(need('repeat_rate'), _r) and close(need('new_rate'), _n), f'repeat_rate, new_rate = {need("repeat_rate")}, {need("new_rate")}, а ожидалось {_r}, {_n}.'
_f, _s = round(_d.loc[_d['response_hours'] <= 1, 'converted'].mean(), 3), round(_d.loc[_d['response_hours'] > 8, 'converted'].mean(), 3)
assert close(need('fast_rate'), _f), f'fast_rate = {need("fast_rate")}, а ожидалось {_f}. Заявки с response_hours <= 1.'
assert close(need('slow_rate'), _s), f'slow_rate = {need("slow_rate")}, а ожидалось {_s}. Заявки с response_hours > 8 (строго больше).'
```

### hint
Глава 3: `d.groupby("channel")["converted"].mean()` — среднее от 0/1 и есть доля договоров. Дальше `.round(3).sort_values(ascending=False)`.

### hint
Для остальных — маска и среднее: `d.loc[d["response_hours"] <= 1, "converted"].mean()`.

### solution
```python
by_channel = d.groupby("channel")["converted"].mean().round(3).sort_values(ascending=False)
repeat_rate = round(d.loc[d["repeat_client"] == 1, "converted"].mean(), 3)
new_rate = round(d.loc[d["repeat_client"] == 0, "converted"].mean(), 3)
fast_rate = round(d.loc[d["response_hours"] <= 1, "converted"].mean(), 3)
slow_rate = round(d.loc[d["response_hours"] > 8, "converted"].mean(), 3)
print(by_channel)
print(repeat_rate, new_rate, fast_rate, slow_rate)
```

### explain
Правило директора не на пустом месте: по рекомендации договором заканчивается больше трети заявок, у повторных клиентов — почти 40 %, а у тендеров и соцсетей — меньше 5 %. Но самый резкий перепад — по скорости ответа: при ответе в течение часа договоров около 23 %, при ожидании дольше 8 часов — около 3 %, почти в восемь раз меньше. К этой цифре вернёмся в шаге 10: она выглядит как готовый совет «отвечайте быстрее», но из таблицы этого вывода сделать нельзя.

## task: missing | Шаг 3. Что значат пропуски | base

`d` уже загружена. Прежде чем заполнять пропуски, посмотрим, случайны ли они. Сохраните конверсию (3 знака):

- `size_na_rate` — у заявок с пустым `company_size`, `size_ok_rate` — с заполненным;
- `budget_na_rate` — с пустым `budget_pp`, `budget_ok_rate` — с заполненным;
- `budget_high` — среди заявок с бюджетом **от 450 ₽** на гостя, `budget_low` — с бюджетом меньше 450 ₽ (пустой бюджет не входит ни туда, ни туда).

### setup
```python

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0().iloc[:1869].copy()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
d = pd.read_csv("catering_leads.csv").iloc[:1869].copy()
```

### starter
```python
# d — таблица заявок
```

### check
```python
_d = _pd0.read_csv('catering_leads.csv').iloc[:1869].copy()
def _r(m):
    return round(_d.loc[m, 'converted'].mean(), 3)
_sn, _so = _r(_d['company_size'].isna()), _r(_d['company_size'].notna())
assert close(need('size_na_rate'), _sn) and close(need('size_ok_rate'), _so), f'size_na_rate, size_ok_rate = {need("size_na_rate")}, {need("size_ok_rate")}, а ожидалось {_sn}, {_so}.'
_bn, _bo = _r(_d['budget_pp'].isna()), _r(_d['budget_pp'].notna())
assert close(need('budget_na_rate'), _bn) and close(need('budget_ok_rate'), _bo), f'budget_na_rate, budget_ok_rate = {need("budget_na_rate")}, {need("budget_ok_rate")}, а ожидалось {_bn}, {_bo}.'
_h, _l = _r(_d['budget_pp'] >= 450), _r(_d['budget_pp'] < 450)
assert close(need('budget_high'), _h), f'budget_high = {need("budget_high")}, а ожидалось {_h}. Условие — budget_pp >= 450.'
assert close(need('budget_low'), _l), f'budget_low = {need("budget_low")}, а ожидалось {_l}. Условие — budget_pp < 450; пропуски в сравнении дают False и сами не попадут.'
```

### hint
Глава 3: маски `d["company_size"].isna()` и `.notna()`; конверсия — `d.loc[маска, "converted"].mean()`.

### hint
Сравнение с пропуском (`NaN >= 450`, `NaN < 450`) даёт `False`, поэтому пустой бюджет сам выпадет из обеих групп.

### solution
```python
size_na_rate = round(d.loc[d["company_size"].isna(), "converted"].mean(), 3)
size_ok_rate = round(d.loc[d["company_size"].notna(), "converted"].mean(), 3)
budget_na_rate = round(d.loc[d["budget_pp"].isna(), "converted"].mean(), 3)
budget_ok_rate = round(d.loc[d["budget_pp"].notna(), "converted"].mean(), 3)
budget_high = round(d.loc[d["budget_pp"] >= 450, "converted"].mean(), 3)
budget_low = round(d.loc[d["budget_pp"] < 450, "converted"].mean(), 3)
print(size_na_rate, size_ok_rate, budget_na_rate, budget_ok_rate, budget_high, budget_low)
```

### explain
На обучающей части заявки с пропущенным размером компании реже заканчиваются договором (10 % против 13,8 %). Причины пропуска из выгрузки неизвестны. Поэтому пропуск размера не заменяем самой частой категорией, а делаем **отдельной категорией** «не указан» — так модель сможет учесть, что пустое поле само по себе сигнал. С бюджетом разница меньше (12 % против 14 %), зато сам бюджет говорит много: от 450 ₽ на гостя договоров втрое больше, чем при меньшем бюджете. Пропуск бюджета заполним медианой обучающей части — это нейтральное значение, а не «бюджет ноль»: в отличие от среднего чека гостей без визитов (глава 6), для пустой ячейки точная сумма неизвестна.

## task: time | Шаг 4. Признаки из времени заявки | base

`d` уже загружена. В `created` — дата и время заявки строкой. Сделайте из неё три признака и **добавьте их в `d`**:

- `hour` — час заявки (`created.dt.hour`);
- `weekday` — день недели (`created.dt.dayofweek`, 0 — понедельник);
- `evening` — 1, если заявка пришла в 19:00 или позже, иначе 0 (целые числа).

Затем сохраните:

- `evening_share` — долю вечерних заявок (3 знака);
- `evening_rate` и `day_rate` — конверсию вечерних и остальных заявок (3 знака);
- `evening_wait` и `day_wait` — медиану `response_hours` у вечерних и остальных заявок (1 знак).

### setup
```python

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0().iloc[:1869].copy()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
d = pd.read_csv("catering_leads.csv").iloc[:1869].copy()
```

### starter
```python
import pandas as pd
created = pd.to_datetime(d["created"])
```

### check
```python
_d = _leads0().iloc[:1869].copy()
_x = need('d', _pd0.DataFrame)
for _c in ['hour', 'weekday', 'evening']:
    assert _c in _x.columns, f'В d нет столбца {_c!r} — добавьте его: d["{_c}"] = ...'
assert (_x['hour'] == _d['hour']).all(), 'hour не совпадает: нужен час из pd.to_datetime(d["created"]).dt.hour.'
assert (_x['weekday'] == _d['weekday']).all(), 'weekday не совпадает: .dt.dayofweek (понедельник — 0).'
assert (_x['evening'] == _d['evening']).all(), 'evening не совпадает: 1 для заявок с hour >= 19, иначе 0.'
assert _x['evening'].dtype.kind in 'iu', 'evening должен быть целым (0/1): .astype(int).'
_ev = _d['evening'] == 1
assert close(need('evening_share'), round(_ev.mean(), 3)), f'evening_share = {need("evening_share")}, а ожидалось {round(_ev.mean(), 3)}.'
_e, _o = round(_d.loc[_ev, 'converted'].mean(), 3), round(_d.loc[~_ev, 'converted'].mean(), 3)
assert close(need('evening_rate'), _e) and close(need('day_rate'), _o), f'evening_rate, day_rate = {need("evening_rate")}, {need("day_rate")}, а ожидалось {_e}, {_o}.'
_we, _wo = round(_d.loc[_ev, 'response_hours'].median(), 1), round(_d.loc[~_ev, 'response_hours'].median(), 1)
assert close(need('evening_wait'), _we) and close(need('day_wait'), _wo), f'evening_wait, day_wait = {need("evening_wait")}, {need("day_wait")}, а ожидалось {_we}, {_wo}. Медиана response_hours, 1 знак.'
```

### hint
Глава 3: у даты-времени есть «аксессор» `.dt`: `created.dt.hour`, `created.dt.dayofweek`. Флаг — `(d["hour"] >= 19).astype(int)`.

### hint
Маска вечерних — `d["evening"] == 1`; конверсия — `d.loc[маска, "converted"].mean()`, ожидание — `d.loc[маска, "response_hours"].median()`.

### solution
```python
import pandas as pd
created = pd.to_datetime(d["created"])
d["hour"] = created.dt.hour
d["weekday"] = created.dt.dayofweek
d["evening"] = (d["hour"] >= 19).astype(int)
ev = d["evening"] == 1
evening_share = round(ev.mean(), 3)
evening_rate = round(d.loc[ev, "converted"].mean(), 3)
day_rate = round(d.loc[~ev, "converted"].mean(), 3)
evening_wait = round(d.loc[ev, "response_hours"].median(), 1)
day_wait = round(d.loc[~ev, "response_hours"].median(), 1)
print(evening_share, evening_rate, day_rate, evening_wait, day_wait)
```

### explain
Каждая девятая заявка приходит вечером, и из них договором заканчиваются единицы — 2,5 % против 14,7 % днём. Одновременно наблюдается более долгое ожидание: вечерняя заявка ждёт ответа до утра, медиана — 13 часов против двух днём. Это гипотеза для эксперимента с вечерним дежурством, а не измеренный эффект ускорения: состав клиентов мог отличаться. Признаки времени считаются по самой строке (урок «Новые признаки»), поэтому их можно добавить в `d` до разбиения — утечки нет. День недели, как увидим, почти ничего не меняет, но модели это выяснять самой.

::: note
Почему отдельный флаг `evening`, если есть `hour`? Логистическая регрессия считает влияние часа одинаковым на каждый час: «каждый час позже — на столько-то хуже». А здесь не плавный спад, а ступенька в 19:00. Флаг ловит её одним коэффициентом.
:::

Общий конвейер должен принимать исходную CRM, включая строковый `created`: преобразуйте дату в hour/weekday/evening **внутри** подготовки до заполнения пропусков и кодирования. На 18:59 evening=0, на 19:00 evening=1. После загрузки модели вызовите её на новых каналах, пропусках, неизвестных категориях и переставленных столбцах; ID строк должны сохраниться.

## task: pipe | Шаг 5. Конвейер | base

В `d` доступна таблица заявок. Соберите модель, которую можно вызвать на сырой строке CRM.

- В `y` возьмите `converted`. В `X` оставьте исходные поля заявки, включая строковый `created`. Удалите `lead_id`, `contract_rub`, `converted` и ранее вычисленные `hour`, `weekday`, `evening`, если они есть.
- По времени `created` сформируйте `X_train`, `y_train` из строк до 21 июня 10:58 и `X_test`, `y_test` из строк начиная с 21 июля 10:58. Между границами проходят 30 дней. Проверьте размеры 1869 и 750 и сохраните исходные индексы.
- В начале `pre` поставьте `FunctionTransformer` с функцией, которая копирует таблицу и добавляет час, день недели и флаг вечера из `created`. Следом в `ColumnTransformer` подготовьте списки из заготовки. Для чисел нужны медиана и `StandardScaler`, для категорий — заполнение строкой «не указан» и `OneHotEncoder(handle_unknown="ignore")`.
- Соедините шаги в `Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])` и сохраните его в `pipe`.

Сохраните `n_features` — сколько столбцов получается после `pre` на обучающей части, и `cv_auc` — средний ROC-AUC конвейера на фолдах `kf` по обучающей части (3 знака).

### setup
```python

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
d = _leads0()
```

### starter
```python
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
```

### check
```python
_d, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_x = need('X', _pd0.DataFrame)
assert 'contract_rub' not in _x.columns, 'contract_rub в X — это утечка из шага 1: сумма договора известна только после договора.'
assert 'converted' not in _x.columns and 'lead_id' not in _x.columns , 'Уберите из X lead_id и сам ответ converted; created остаётся для конвейера.'
assert _x.columns.is_unique and set(_x.columns) == set(_X.columns), f'Столбцы X: {list(_x.columns)}, а ожидались {list(_X.columns)}. Без get_dummies — сырые столбцы.'
from pandas.testing import assert_frame_equal as _frame_equal, assert_series_equal as _series_equal
for _name, _expected in [('X', _X), ('X_train', _Xtr), ('X_test', _Xte)]:
    _submitted = need(_name, _pd0.DataFrame)
    assert _submitted.columns.is_unique and set(_submitted.columns) == set(_expected.columns), f'{_name}: сохраните исходные столбцы CRM; их порядок можно менять.'
    assert _submitted.index.is_unique and set(_submitted.index) == set(_expected.index), f'{_name}: строки должны соответствовать своим исходным ID и календарной части.'
    try:
        _frame_equal(_submitted.reindex(index=_expected.index, columns=_expected.columns), _expected,
                     check_dtype=False, check_names=False, check_exact=False, rtol=1e-9, atol=1e-10)
    except AssertionError:
        raise AssertionError(f'{_name}: содержимое сырых строк не совпадает с их исходными ID; проверьте значения, пропуски и календарное разбиение.') from None
for _name, _expected in [('y', _y), ('y_train', _ytr), ('y_test', _yte)]:
    _submitted = need(_name, _pd0.Series)
    assert _submitted.index.is_unique and set(_submitted.index) == set(_expected.index), f'{_name}: метки должны быть связаны с исходными ID своей календарной части.'
    try:
        _series_equal(_submitted.reindex(_expected.index), _expected,
                      check_dtype=False, check_names=False, check_exact=False, rtol=0, atol=0)
    except AssertionError:
        raise AssertionError(f'{_name}: значения converted не совпадают с исходными ID. Сохраните метки без инверсии и перестановки только ответов.') from None
_p = need('pipe', _P0)
assert list(_p.named_steps) == ['prep', 'model'], f'Шаги pipe: {list(_p.named_steps)}, а нужны ["prep", "model"].'
assert isinstance(_p.named_steps['model'], _LR0), 'Последний шаг pipe — LogisticRegression(max_iter=2000).'
_nf = _pre0().fit_transform(_Xtr).shape[1]
from sklearn.base import clone as _clone
_prep = _p.named_steps['prep']
assert callable(getattr(_prep, 'fit_transform', None)), 'prep должен преобразовывать сырые столбцы.'
_sample = _Xtr.iloc[:120]
_got = _clone(_prep).fit_transform(_sample)
_want = _pre0().fit_transform(_sample)
assert _got.shape == _want.shape, 'Проверьте, что подготовка внутри pipe включает категории и числовые столбцы.'
assert need('n_features') == _nf, f'n_features = {need("n_features")}, а после подготовки получается {_nf} столбцов. Проверьте списки num и cat и fit_transform(X_train).'
_a = round(_cvs0(_P0([('prep', _pre0()), ('model', _LR0(max_iter=2000))]), _Xtr, _ytr, cv=_k, scoring='roc_auc').mean(), 3)
_actual_cv = round(_cvs0(_clone(_p), _Xtr, _ytr, cv=_k, scoring='roc_auc').mean(), 3)
assert close(_actual_cv, _a, .0011), 'Переданный pipe должен выполнять ту же подготовку в каждом CV-фолде: сверьте календарные признаки и состав столбцов.'
_sample_raw = _Xte.iloc[:2].copy()
_sample_raw['created'] = ['2026-10-01 18:59', '2026-10-01 19:00']
_sample_raw['channel'] = ['новый канал', None]
_sample_raw['budget_pp'] = _np0.nan
_actual_model = _clone(_p).fit(_Xtr, _ytr)
_expected_model = _P0([('prep', _pre0()), ('model', _LR0(max_iter=2000))]).fit(_Xtr, _ytr)
assert _np0.allclose(_actual_model.predict_proba(_sample_raw[_sample_raw.columns[::-1]]), _expected_model.predict_proba(_sample_raw), atol=1e-6, rtol=1e-6), 'Проверьте фактический pipe на сырой CRM: даты 18:59/19:00, новая категория, пропуск и другой порядок входных колонок.'
assert close(need('cv_auc'), _a), f'cv_auc = {need("cv_auc")}, а ожидалось {_a}. cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc").mean().'
```

### hint
Урок «Pipeline: предобработка и модель вместе»: для категорий два шага подряд — `make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore"))`.

### hint
`pre.fit_transform(X_train).shape[1]` — число столбцов после подготовки. Метрику задаёт `scoring="roc_auc"`.

### solution
```python
import pandas as pd

from sklearn.preprocessing import FunctionTransformer
def lead_time(frame):
    frame = frame.copy()
    stamp = pd.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]

y = d["converted"]
X = d.drop(columns=["lead_id", "contract_rub", "converted", "hour", "weekday", "evening"])
X_train, X_test, y_train, y_test = (X[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], X[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"], y[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], y[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"])
pre = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
n_features = pre.fit_transform(X_train).shape[1]
cv_auc = round(cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc").mean(), 3)
print(n_features, cv_auc)
```

### explain
9 числовых столбцов и 27 флагов категорий — включая флаг «не указан» для размера компании. Медиану бюджета конвейер на каждом фолде считает заново по обучающим строкам — утечки нет (урок «Pipeline: предобработка и модель вместе»). Средний AUC на фолдах — 0,878. Тест (750 заявок) отложен до шага 9.

## task: trap | Шаг 6. Ловушка дисбаланса | plus

Курс подготовил `X_train`, `y_train`, фолды `kf` и необученный `pre` из шага 5. Посчитайте на фолдах `kf` по обучающей части (все — среднее, 3 знака):

- `dummy_acc` — долю правильных `DummyClassifier(strategy="most_frequent")`;
- `forest_acc` и `forest_f1` — долю правильных и F1 конвейера `pre` + `RandomForestClassifier(n_estimators=50, min_samples_leaf=5, random_state=0)`;
- `balanced_f1` — F1 того же конвейера, но с лесом `class_weight="balanced"`.

### setup
```python
import pandas as pd

from sklearn.preprocessing import FunctionTransformer
def lead_time(frame):
    frame = frame.copy()
    stamp = pd.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv")
created = pd.to_datetime(d["created"])
d["hour"] = created.dt.hour
d["weekday"] = created.dt.dayofweek
d["evening"] = (d["hour"] >= 19).astype(int)
y = d["converted"]
X = d.drop(columns=["lead_id", "contract_rub", "converted", "hour", "weekday", "evening"])
X_train, X_test, y_train, y_test = (X[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], X[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"], y[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], y[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
```

### starter
```python
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
```

### check
```python
from sklearn.ensemble import RandomForestClassifier as _RF
from sklearn.dummy import DummyClassifier as _DC
_d, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_da = round(_cvs0(_DC(strategy='most_frequent'), _Xtr, _ytr, cv=_k).mean(), 3)
assert close(need('dummy_acc'), _da), f'dummy_acc = {need("dummy_acc")}, а ожидалось {_da}. DummyClassifier(strategy="most_frequent") на X_train с cv=kf.'
_p = _P0([('prep', _pre0()), ('model', _RF(n_estimators=50, min_samples_leaf=5, random_state=0))])
_fa = round(_cvs0(_p, _Xtr, _ytr, cv=_k).mean(), 3)
assert close(need('forest_acc'), _fa), f'forest_acc = {need("forest_acc")}, а ожидалось {_fa}. Лес внутри конвейера с pre, без scoring (доля правильных).'
_ff = round(_cvs0(_p, _Xtr, _ytr, cv=_k, scoring='f1').mean(), 3)
assert close(need('forest_f1'), _ff), f'forest_f1 = {need("forest_f1")}, а ожидалось {_ff}. Тот же конвейер со scoring="f1".'
_pb = _P0([('prep', _pre0()), ('model', _RF(n_estimators=50, min_samples_leaf=5, class_weight='balanced', random_state=0))])
_bf = round(_cvs0(_pb, _Xtr, _ytr, cv=_k, scoring='f1').mean(), 3)
assert close(need('balanced_f1'), _bf), f'balanced_f1 = {need("balanced_f1")}, а ожидалось {_bf}. Лес с class_weight="balanced", scoring="f1".'
```

### hint
Урок «Матрица ошибок» — `DummyClassifier`; урок «Pipeline: предобработка и модель вместе» — конвейер `Pipeline([("prep", pre), ("model", RandomForestClassifier(...))])`; урок «Дисбаланс классов» — `class_weight="balanced"`.

### hint
`cross_val_score(forest, X_train, y_train, cv=kf)` — доля правильных; с `scoring="f1"` — F1.

### solution
```python
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
dummy_acc = round(cross_val_score(DummyClassifier(strategy="most_frequent"), X_train, y_train, cv=kf).mean(), 3)
forest = Pipeline([("prep", pre), ("model", RandomForestClassifier(n_estimators=50, min_samples_leaf=5, random_state=0))])
forest_acc = round(cross_val_score(forest, X_train, y_train, cv=kf).mean(), 3)
forest_f1 = round(cross_val_score(forest, X_train, y_train, cv=kf, scoring="f1").mean(), 3)
balanced = Pipeline([("prep", pre), ("model", RandomForestClassifier(n_estimators=50, min_samples_leaf=5,
                                                                      class_weight="balanced", random_state=0))])
balanced_f1 = round(cross_val_score(balanced, X_train, y_train, cv=kf, scoring="f1").mean(), 3)
print(dummy_acc, forest_acc, forest_f1, balanced_f1)
```

### explain
Вот ловушка из урока «Матрица ошибок» в чистом виде. Лес прав почти в 88 % случаев — и это всего на один пункт лучше, чем «никто не купит». F1 около 0.2 объясняет почему: при пороге 0.5 лес почти никогда не говорит «купит», он находит лишь малую часть договоров. С `class_weight="balanced"` F1 вырастает больше чем до 0.5: лес начинает отмечать редкий класс.

Но директору не нужен ответ «да/нет» при пороге 0.5: менеджеры всё равно возьмут 30 % заявок, сколько бы модель ни назвала «покупателями». Значит, и выбирать модель нужно по тому, как хорошо она **упорядочивает** заявки, — это следующий шаг.

## task: metric | Шаг 7. Метрика директора | base

Напишите функцию `catch_rate(y_true, scores, share=0.3, k=None)` — долю всех договоров, которые попадают в верхние `share` заявок по оценке; при переданном целом `k` отбирайте ровно `k` мест. Долю для показа округляют после определения списка:

1. Свяжите оценку с ключом строки из индекса `y_true`. На этой выгрузке исходный индекс идёт в порядке возрастания `lead_id`.
2. При заданном `k` возьмите ровно столько заявок, иначе вычислите `int(len(y_true) * share)`. Сначала выбирайте большую оценку, при равной оценке — меньший ключ.
3. Разделите число договоров у выбранных заявок на число договоров во всей группе.

Затем посчитайте точку сравнения — правило директора на **обучающей** части: правило отмечает заявку, если клиент повторный **или** пришёл по рекомендации. Правило — не оценка, а отметка 0/1, и отмечает оно не 30 % заявок, поэтому `catch_rate` к нему не применяйте. Сохраните:

- `rule_share` — какую долю заявок `X_train` отмечает правило (3 знака);
- `rule_catch` — какую долю договоров `y_train` оно ловит: договоры среди отмеченных правилом заявок, делённые на все договоры `y_train` (3 знака);
- `random_catch` — `catch_rate` для случайных оценок `np.random.default_rng(0).random(len(y_train))` (3 знака).

### setup
```python
import pandas as pd

from sklearn.preprocessing import FunctionTransformer
def lead_time(frame):
    frame = frame.copy()
    stamp = pd.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv")
created = pd.to_datetime(d["created"])
d["hour"] = created.dt.hour
d["weekday"] = created.dt.dayofweek
d["evening"] = (d["hour"] >= 19).astype(int)
y = d["converted"]
X = d.drop(columns=["lead_id", "contract_rub", "converted", "hour", "weekday", "evening"])
X_train, X_test, y_train, y_test = (X[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], X[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"], y[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], y[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
```

### starter
```python
import numpy as np
import pandas as pd

def catch_rate(y_true, scores, share=0.3, k=None):
    ...
```

### check
```python
_d, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_f = need('catch_rate')
assert callable(_f), 'catch_rate должна быть функцией.'
_yt = _pd0.Series([1, 0, 1, 0, 0, 1, 0, 0, 0, 0], index=range(10, 20))
_sc = _np0.array([0.9, 0.8, 0.7, 0.1, 0.2, 0.05, 0.3, 0.4, 0.0, 0.15])
_got = _f(_yt, _sc)
assert _got is not None, 'catch_rate ничего не возвращает — допишите return.'
assert close(_got, 2 / 3), f'На маленьком примере (10 заявок, договоры у 1-й, 3-й и 6-й) catch_rate вернула {_got}, а ожидалось 0.667: в верхние 3 попали два договора из трёх. Проверьте, что индекс Series берётся из y_true.'
assert close(_f(_yt, _sc, share=0.2), 1 / 3) and close(_f(_yt, _sc, share=1.0), 1.0), 'catch_rate неверно работает с другим share: число заявок — int(len(...) * share).'
_r = (_Xtr['repeat_client'] == 1) | (_Xtr['channel'] == 'рекомендация')
assert close(need('rule_share'), round(_r.mean(), 3)), f'rule_share = {need("rule_share")}, а ожидалось {round(_r.mean(), 3)}. Правило: repeat_client == 1 или channel == "рекомендация", на X_train.'
_rc = round(_ytr[_r].sum() / _ytr.sum(), 3)
assert close(need('rule_catch'), _rc), f'rule_catch = {need("rule_catch")}, а ожидалось {_rc}. Договоры в отмеченных заявках делить на все договоры y_train.'
_rnd = round(_catch0(_ytr, _np0.random.default_rng(0).random(len(_ytr))), 3)
assert close(need('random_catch'), _rnd), f'random_catch = {need("random_catch")}, а ожидалось {_rnd}. Оценки — np.random.default_rng(0).random(len(y_train)).'
_boundary_y = _pd0.Series([0]*9 + [1] + [0]*20)
_boundary_s = _np0.arange(30,0,-1)
from inspect import signature as _signature
try:
    _signature(_f).bind(_boundary_y, _boundary_s, k=10)
except TypeError:
    raise AssertionError('Добавьте к catch_rate аргумент k для точного числа мест. При k=10 в очередь входит десятая заявка.') from None
assert close(_f(_boundary_y, _boundary_s, k=10), 1), 'При k=10 десятая заявка входит, даже если показанная доля 0.333 дала бы только9.'

```

### hint
Если `k is None`, вычислите число мест из доли. Сначала упорядочите оценки по ключу через `sort_index()`, затем по убыванию оценки с `kind="stable"`. Первые `k` индексов выбирают строки из `y_true`.

### hint
«Или» для масок — `|`, каждое условие в скобках: `(X_train["repeat_client"] == 1) | (X_train["channel"] == "рекомендация")`.

### solution
```python
import numpy as np
import pandas as pd

def catch_rate(y_true, scores, share=0.3, k=None):
    s = pd.Series(scores, index=y_true.index)
    top = s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(s)*share) if k is None else int(k)).index
    return y_true.loc[top].sum() / y_true.sum()

rule = (X_train["repeat_client"] == 1) | (X_train["channel"] == "рекомендация")
rule_share = round(rule.mean(), 3)
rule_catch = round(y_train[rule].sum() / y_train.sum(), 3)
random_catch = round(catch_rate(y_train, np.random.default_rng(0).random(len(y_train))), 3)
print(rule_share, rule_catch, random_catch)
```

### explain
Случайная очередь из 30 % заявок охватывает в среднем около 30 % договоров. В конкретном розыгрыше с seed 0 получилось 35,9 %. Правило директора отмечает чуть больше пятой части заявок и ловит в них почти 60 % договоров — примерно в 2.5 раза больше, чем случайный выбор того же объёма. Это планка для модели. Сравнивать с правилом честно при одинаковом объёме работы: правило отмечает меньше 30 % заявок, поэтому на тесте посчитаем и топ-30 %, и топ такого же размера, как у правила.

## task: grid | Шаг 8. Подбор настроек | plus

Курс подготовил `pipe` из шага 5 (подготовка + `LogisticRegression(max_iter=2000)`, не обучен). Подберите настройки модели `GridSearchCV` (урок «Подбор гиперпараметров») по сетке

- `C`: 0.01, 0.1, 1, 10;
- `class_weight`: `None`, `"balanced"`

с `cv=kf` и `scoring="roc_auc"` на обучающей части. AUC использует пары по всему списку. В первом фолде 374 заявки и 41 договор. Базовая модель нашла 34 договора в первых 112 заявках. Полнота равна 34/41, точность списка — 34/112. По другим фолдам число договоров и состав верхушки меняются. Можно подбирать модель непосредственно по полноте при фиксированном бюджете, если именно он определяет решение. Сохраните обученный поиск в `grid`, а также:

- `best_params` — лучшие настройки (`best_params_`);
- `best_auc` — лучший средний AUC (3 знака);
- `res` — `pd.DataFrame(grid.cv_results_)`;
- `spread` — разницу между лучшим и худшим `mean_test_score` из `res` (3 знака).

### setup
```python
import pandas as pd

from sklearn.preprocessing import FunctionTransformer
def lead_time(frame):
    frame = frame.copy()
    stamp = pd.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv")
created = pd.to_datetime(d["created"])
d["hour"] = created.dt.hour
d["weekday"] = created.dt.dayofweek
d["evening"] = (d["hour"] >= 19).astype(int)
y = d["converted"]
X = d.drop(columns=["lead_id", "contract_rub", "converted", "hour", "weekday", "evening"])
X_train, X_test, y_train, y_test = (X[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], X[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"], y[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], y[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
```

### starter
```python
import pandas as pd
from sklearn.model_selection import GridSearchCV
```

### check
```python
from sklearn.model_selection import GridSearchCV as _GS
_d, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_g = need('grid', _GS)
assert hasattr(_g, 'best_params_'), 'grid не обучен: вызовите grid.fit(X_train, y_train).'
assert len(_g.cv_results_['params']) == 8, f'В сетке {len(_g.cv_results_["params"])} комбинаций, а нужно 8: четыре C × два class_weight. Имена параметров — model__C и model__class_weight.'
_w = _GS(_P0([('prep', _pre0()), ('model', _LR0(max_iter=2000))]),
         {'model__C': [0.01, 0.1, 1, 10], 'model__class_weight': [None, 'balanced']},
         cv=_k, scoring='roc_auc').fit(_Xtr, _ytr)
assert dict(need('best_params')) == _w.best_params_, f'best_params = {need("best_params")}, а ожидалось {_w.best_params_}. Проверьте scoring="roc_auc" и cv=kf.'
assert close(need('best_auc'), round(_w.best_score_, 3)), f'best_auc = {need("best_auc")}, а ожидалось {round(_w.best_score_, 3)}: это grid.best_score_.'
_rr = need('res', _pd0.DataFrame)
assert 'mean_test_score' in _rr.columns and len(_rr) == 8, 'res — pd.DataFrame(grid.cv_results_): 8 строк, есть столбец mean_test_score.'
assert 'params' in _rr and len(_rr['params']) == len(_w.cv_results_['params']), 'В res сохраните сочетания параметров.'
_key = lambda p: tuple(sorted(p.items()))
_expected_scores = {_key(p): v for p, v in zip(_w.cv_results_['params'], _w.cv_results_['mean_test_score'])}
_scores = {_key(p): v for p, v in zip(_rr['params'], _rr['mean_test_score'])}
assert set(_scores) == set(_expected_scores) and all(close(_scores[k], v, .0006) for k, v in _expected_scores.items()), 'Оценка mean_test_score в представленной таблице должна соответствовать сочетанию параметров.'
_m = _w.cv_results_['mean_test_score']
assert close(need('spread'), round(_m.max() - _m.min(), 3)), f'spread = {need("spread")}, а ожидалось {round(_m.max() - _m.min(), 3)}: max − min столбца mean_test_score.'
```

### hint
Урок «Подбор гиперпараметров»: имена параметров шага — через два подчёркивания: `{"model__C": [...], "model__class_weight": [None, "balanced"]}`.

### hint
`grid = GridSearchCV(pipe, params, cv=kf, scoring="roc_auc").fit(X_train, y_train)`; дальше `grid.best_params_`, `grid.best_score_`, `res["mean_test_score"].max() - ...min()`.

### solution
```python
import pandas as pd
from sklearn.model_selection import GridSearchCV
params = {"model__C": [0.01, 0.1, 1, 10], "model__class_weight": [None, "balanced"]}
grid = GridSearchCV(pipe, params, cv=kf, scoring="roc_auc").fit(X_train, y_train)
best_params = grid.best_params_
best_auc = round(grid.best_score_, 3)
res = pd.DataFrame(grid.cv_results_)
spread = round(res["mean_test_score"].max() - res["mean_test_score"].min(), 3)
print(best_params, best_auc, spread)
res[["param_model__C", "param_model__class_weight", "mean_test_score"]].round(3)
```

### explain
Лучшие настройки — `C=1` без весов, то есть обычная логистическая регрессия; диапазон средних AUC по сетке составил 0,031. Это нормальный и полезный результат: подбор показал, что настройки здесь почти не важны, и дальше можно не тратить на них время. Обратите внимание на `class_weight`: в шаге 6 он поднял F1 леса больше чем вдвое, а AUC почти не меняет (урок «Дисбаланс классов»). Веса сдвигают оценки к редкому классу, а для списка «верхние 30 %» важно проверить, как изменился порядок заявок.

::: note
Для сравнения: лес из шага 6 с `class_weight="balanced"` на тех же фолдах даёт средний AUC 0,870, логрегрессия — 0,878. Для проекта берём логрегрессию. Близость двух средних сама по себе не доказывает равенство моделей.
:::

При сравнении с правилом сначала получите целое `k = int(rule.sum())`. Например, если правило отметило 175 из 750 заявок, модели тоже выделяется 175, а не 174 после восстановления места из округлённой доли 23.3 %. Это пример ошибки округления; на новой календарной партии число мест вычислите заново. При ничьих используйте lead_id по возрастанию.

## task: final | Шаг 9. Сколько договоров в топ-30 % | base

Перед отбором можете записать для диспетчера одну строку решения: чью заявку оцениваем, в какой момент, какие признаки уже известны, сколько контактов можно взять и по какому исходу позже сравним две очереди.

Сохраните `model_ids` и `rule_ids` — списки исходных lead_id одинаковой длины `k=int(rule.sum())`. Для модели сортируйте score по убыванию, lead_id по возрастанию; для правила отсортируйте все выбранные ID по возрастанию. Строки и прогнозы связывайте по ID, включая последний допустимый контакт.

Курс обучил лучший конвейер из шага 8 на всей обучающей части — он в `best`, — и определил функцию `catch_rate` из шага 7. Теперь — один раз — проверьте на тесте (3 знака):

- `test_auc` — ROC-AUC `best` на `X_test`;
- `model_catch` — `catch_rate` вероятностей `best` на тесте (топ-30 %);
- `rule_share_test` и `rule_catch_test` — какую долю тестовых заявок отмечает правило директора и какую долю договоров оно ловит;
- `model_same` — доля договоров, которую модель охватывает при том же числе мест. Передайте в `catch_rate` целое `k=int(rule.sum())`. Округлённая доля нужна для отчёта.

### setup
```python
import pandas as pd

from sklearn.preprocessing import FunctionTransformer
def lead_time(frame):
    frame = frame.copy()
    stamp = pd.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv")
created = pd.to_datetime(d["created"])
d["hour"] = created.dt.hour
d["weekday"] = created.dt.dayofweek
d["evening"] = (d["hour"] >= 19).astype(int)
y = d["converted"]
X = d.drop(columns=["lead_id", "contract_rub", "converted", "hour", "weekday", "evening"])
X_train, X_test, y_train, y_test = (X[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], X[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"], y[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], y[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
best = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000, C=1, class_weight=None))]).fit(X_train, y_train)
def catch_rate(y_true, scores, share=0.3, k=None):
    s = pd.Series(scores, index=y_true.index)
    top = s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(s)*share) if k is None else int(k)).index
    return y_true.loc[top].sum() / y_true.sum()
```

### starter
```python
from sklearn.metrics import roc_auc_score
```

### check
```python
from sklearn.metrics import roc_auc_score as _auc
_d, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_reference_model = _P0([('prep', _pre0()), ('model', _LR0(max_iter=2000))]).fit(_Xtr, _ytr)
_s = _reference_model.predict_proba(_Xte)[:, 1]
_a = round(_auc(_yte, _s), 3)
assert close(need('test_auc'), _a), f'test_auc = {need("test_auc")}, а ожидалось {_a}. roc_auc_score(y_test, best.predict_proba(X_test)[:, 1]).'
_by_id = _pd0.Series(_yte.to_numpy(), index=_d.loc[_Xte.index, 'lead_id'])
_mc = round(_catch0(_by_id, _s), 3)
assert close(need('model_catch'), _mc), f'model_catch = {need("model_catch")}, а ожидалось {_mc}. catch_rate(y_test, вероятности на X_test).'
_r = (_Xte['repeat_client'] == 1) | (_Xte['channel'] == 'рекомендация')
_rs, _rc = round(_r.mean(), 3), round(_yte[_r].sum() / _yte.sum(), 3)
assert close(need('rule_share_test'), _rs) and close(need('rule_catch_test'), _rc), f'rule_share_test, rule_catch_test = {need("rule_share_test")}, {need("rule_catch_test")}, а ожидалось {_rs}, {_rc}. Правило — на X_test, договоры — y_test.'
_ms = round(_catch0(_by_id, _s, k=int(_r.sum())), 3)
assert close(need('model_same'), _ms, 0.0011), f'model_same = {need("model_same")}, а ожидалось {_ms}. catch_rate(y_test, вероятности, k=int(rule.sum())).'
_best = need('best')
assert isinstance(_best, _P0), 'best должен быть обученным Pipeline с подготовкой сырых строк и моделью.'
_raw = _pd0.read_csv('catering_leads.csv').loc[_Xte.index].drop(columns=['converted','contract_rub'])
_actual = _best.predict_proba(_raw)[:,1]
assert _np0.allclose(_actual, _s), 'best должен принимать исходные даты CRM и давать прогнозы той же модели.'
_new = _raw.iloc[:2].copy()
_new['created'] = ['2026-10-01 18:59','2026-10-01 19:00']
_new['channel'] = ['новый канал', None]
_new['budget_pp'] = _np0.nan
_pred = _best.predict_proba(_new[_new.columns[::-1]])[:,1]
assert len(_pred)==2 and _np0.isfinite(_pred).all(), 'Конвейер должен обрабатывать новые категории, пропуски и иной порядок колонок.'
_expected_new = _reference_model.predict_proba(_new)[:,1]
assert _np0.allclose(_pred, _expected_new, atol=1e-8, rtol=1e-7), 'На новых датах, категориях и пропусках best должен выполнять ту же подготовку, что при обучении.'

_rank = _pd0.DataFrame({'score': _s, 'lead_id': _d.loc[_Xte.index, 'lead_id']}, index=_Xte.index).sort_values(['score','lead_id'], ascending=[False,True])
assert list(need('model_ids')) == _rank.head(int(_r.sum()))['lead_id'].tolist(), 'model_ids: ровно k мест, риск по убыванию, ID по возрастанию при ничьей.'
assert list(need('rule_ids')) == sorted(_d.loc[_Xte.index[_r], 'lead_id'].tolist()), 'rule_ids: все ID под маской правила, по lead_id по возрастанию.'

```

### hint
Вероятности: `scores = best.predict_proba(X_test)[:, 1]`. Свяжите метки с ID: `labels_by_id = pd.Series(y_test.to_numpy(), index=d.loc[X_test.index, "lead_id"])`. Тогда `catch_rate(labels_by_id, scores)` — топ-30 % с развязкой ничьих по ID.

### hint
Правило на тесте — та же маска, что в шаге 7, только по `X_test`; для `model_same` передайте `k=int(rule.sum())`. При шести заявках и двух местах маска должна выбрать две строки, даже если напечатанная доля равна 0,333.

### solution
```python
from sklearn.metrics import roc_auc_score
scores = best.predict_proba(X_test)[:, 1]
test_auc = round(roc_auc_score(y_test, scores), 3)
labels_by_id = pd.Series(y_test.to_numpy(), index=d.loc[X_test.index, "lead_id"])
model_catch = round(catch_rate(labels_by_id, scores), 3)
rule = (X_test["repeat_client"] == 1) | (X_test["channel"] == "рекомендация")
rule_share_test = round(rule.mean(), 3)
rule_catch_test = round(y_test[rule].sum() / y_test.sum(), 3)
model_same = round(catch_rate(labels_by_id, scores, k=int(rule.sum())), 3)
print(test_auc, model_catch, rule_share_test, rule_catch_test, model_same)
rank = pd.DataFrame({'score': scores, 'lead_id': d.loc[X_test.index, 'lead_id']}, index=X_test.index).sort_values(['score', 'lead_id'], ascending=[False, True])
model_ids = rank.head(int(rule.sum()))['lead_id'].tolist()
rule_ids = sorted(d.loc[X_test.index[rule], 'lead_id'].tolist())

```

### explain
В следующих по времени 750 заявках заключено 94 договора. Первые 225 по модели охватывают 72 договора (76,6 %), случайная очередь такой длины в среднем охватила бы 30 %. Правило директора выделяет 166 заявок и находит 57 договоров. Из 166 заявок, выбранных моделью, договор заключили 64. На этом периоде AUC составил 0,858, после среднего 0,878 при подборе. Для сравнения очередей знаменатель один и тот же — 94 договора.

Кроме канала и повторности модель учитывает бюджет, срок до мероприятия, просьбу о дегустации и часы до первого ответа. Как изменится очередь, если менеджеру нужен прогноз ещё до ответа, проверим в шаге 10.

## task: speed | Шаг 10. Скорость ответа: причина или следствие? | star

Один из самых сильных сигналов модели — `response_hours`, и вывод «отвечайте быстрее — будет больше договоров» напрашивается. Проверим две вещи.

**Модель без скорости.** Если ставить приоритет **в момент прихода** заявки, скорости ответа ещё нет. Соберите такую же подготовку без `response_hours` (список `num_now`), конвейер с `LogisticRegression(max_iter=2000)`, обучите на `X_train` и сохраните `catch_now` — `catch_rate` на тесте (3 знака).

**Менеджер Олег.** У Олега конверсия ниже, чем у коллег. Сохраните по всей таблице `d` (3 знака):

- `oleg_wait` и `others_wait` — медиану `response_hours` у Олега и у остальных менеджеров (1 знак);
- `oleg_fast` и `others_fast` — конверсию заявок с ответом за 2 часа или быстрее (`response_hours <= 2`) у Олега и у остальных.

Подготовка `pre`, списки `num` и `cat` и функция `catch_rate` — уже есть.

### setup
```python
import pandas as pd

from sklearn.preprocessing import FunctionTransformer
def lead_time(frame):
    frame = frame.copy()
    stamp = pd.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame

from sklearn.preprocessing import FunctionTransformer as _FT0
def _lead_time0(frame):
    frame = frame.copy()
    stamp = _pd0.to_datetime(frame['created'])
    frame['hour'] = stamp.dt.hour
    frame['weekday'] = stamp.dt.dayofweek
    frame['evening'] = (stamp.dt.hour >= 19).astype(int)
    return frame
import pandas as _pd0
import numpy as _np0
from sklearn.model_selection import train_test_split as _tts0, KFold as _KF0, cross_val_score as _cvs0
from sklearn.compose import ColumnTransformer as _CT0
from sklearn.pipeline import Pipeline as _P0, make_pipeline as _mp0
from sklearn.impute import SimpleImputer as _SI0
from sklearn.preprocessing import OneHotEncoder as _OHE0, StandardScaler as _SS0
from sklearn.linear_model import LogisticRegression as _LR0
_NUM0 = ['guests', 'budget_pp', 'days_to_event', 'response_hours', 'repeat_client', 'tasting', 'hour', 'weekday', 'evening']
_CAT0 = ['channel', 'event_type', 'city', 'company_size', 'manager']
def _leads0():
    _d = _pd0.read_csv('catering_leads.csv')
    _t = _pd0.to_datetime(_d['created'])
    _d['hour'] = _t.dt.hour
    _d['weekday'] = _t.dt.dayofweek
    _d['evening'] = (_d['hour'] >= 19).astype(int)
    return _d
def _ref():
    _d = _leads0()
    _y = _d['converted']
    _X = _d.drop(columns=['lead_id', 'contract_rub', 'converted', 'hour', 'weekday', 'evening'])
    _Xtr, _Xte, _ytr, _yte = (_X[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _X[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'], _y[_pd0.to_datetime(_d['created']) < '2026-06-21 10:58'], _y[_pd0.to_datetime(_d['created']) >= '2026-07-21 10:58'])
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _mp0(_FT0(_lead_time0), _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ]))
def _catch0(yt, s, share=0.3, k=None):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(_s)*share) if k is None else int(k)).index].sum() / yt.sum()
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
d = pd.read_csv("catering_leads.csv")
created = pd.to_datetime(d["created"])
d["hour"] = created.dt.hour
d["weekday"] = created.dt.dayofweek
d["evening"] = (d["hour"] >= 19).astype(int)
y = d["converted"]
X = d.drop(columns=["lead_id", "contract_rub", "converted", "hour", "weekday", "evening"])
X_train, X_test, y_train, y_test = (X[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], X[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"], y[pd.to_datetime(d["created"]) < "2026-06-21 10:58"], y[pd.to_datetime(d["created"]) >= "2026-07-21 10:58"])
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
def catch_rate(y_true, scores, share=0.3, k=None):
    s = pd.Series(scores, index=y_true.index)
    top = s.sort_index().sort_values(ascending=False, kind="stable").head(int(len(s)*share) if k is None else int(k)).index
    return y_true.loc[top].sum() / y_true.sum()
```

### starter
```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
num_now = [c for c in num if c != "response_hours"]
```

### check
```python
_d, _X, _y, _Xtr, _Xte, _ytr, _yte, _k = _ref()
_nn = [c for c in _NUM0 if c != 'response_hours']
_s = _P0([('prep', _pre0(_nn)), ('model', _LR0(max_iter=2000))]).fit(_Xtr, _ytr).predict_proba(_Xte)[:, 1]
_c = round(_catch0(_yte, _s), 3)
assert close(need('catch_now'), _c), f'catch_now = {need("catch_now")}, а ожидалось {_c}. Нужна новая подготовка, где в числовых столбцах нет response_hours, — остальное как в шаге 5.'
_o = _d['manager'] == 'Олег'
_ow, _rw = round(_d.loc[_o, 'response_hours'].median(), 1), round(_d.loc[~_o, 'response_hours'].median(), 1)
assert close(need('oleg_wait'), _ow) and close(need('others_wait'), _rw), f'oleg_wait, others_wait = {need("oleg_wait")}, {need("others_wait")}, а ожидалось {_ow}, {_rw}.'
_f = _d['response_hours'] <= 2
_of, _rf = round(_d.loc[_o & _f, 'converted'].mean(), 3), round(_d.loc[~_o & _f, 'converted'].mean(), 3)
assert close(need('oleg_fast'), _of) and close(need('others_fast'), _rf), f'oleg_fast, others_fast = {need("oleg_fast")}, {need("others_fast")}, а ожидалось {_of}, {_rf}. Две маски через &: менеджер и response_hours <= 2.'
```

### hint
Новая подготовка — копия `pre` из условия шага 5, только в первой тройке вместо `num` стоит `num_now`. Объект `pre` переиспользовать нельзя: в нём зашит старый список.

### hint
Маски: `oleg = d["manager"] == "Олег"`, `fast = d["response_hours"] <= 2`; конверсия быстрых у Олега — `d.loc[oleg & fast, "converted"].mean()`, у остальных — `~oleg & fast`.

### solution
```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
num_now = [c for c in num if c != "response_hours"]
pre_now = make_pipeline(FunctionTransformer(lead_time), ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_now),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
]))
now = Pipeline([("prep", pre_now), ("model", LogisticRegression(max_iter=2000))]).fit(X_train, y_train)
catch_now = round(catch_rate(y_test, now.predict_proba(X_test)[:, 1]), 3)

oleg = d["manager"] == "Олег"
fast = d["response_hours"] <= 2
oleg_wait = round(d.loc[oleg, "response_hours"].median(), 1)
others_wait = round(d.loc[~oleg, "response_hours"].median(), 1)
oleg_fast = round(d.loc[oleg & fast, "converted"].mean(), 3)
others_fast = round(d.loc[~oleg & fast, "converted"].mean(), 3)
print(catch_now, oleg_wait, others_wait, oleg_fast, others_fast)
```

### explain
В нашем сценарии ранняя модель получает только поля, известные при регистрации. В верхние 30 % также попали 72 из 94 договоров. Чтобы выяснить, у каких заявок изменился приоритет после ответа, нужно сравнить их ID.

Олег отвечает медленнее всех: медиана около 6 часов против двух у коллег. Но когда он отвечает за два часа, его заявки заканчиваются договором не реже, чем у остальных (около 21 % против 20 %). Это совместимо с гипотезой о скорости; причинный вывод из такого среза пока не следует.

**Похоже — но не доказано.** Это наблюдение, а не эксперимент (глава 5). Быстрый ответ может быть причиной договора, а может быть и следствием: менеджер сразу отвечает тем, кто звонит сам, пишет подробную заявку и явно готов покупать, а «холодные» заявки откладывает. Вечерние заявки ждут дольше и покупают реже — но вечером могут писать и менее решительные клиенты. Модели для ранжирования эта разница не важна: признак честно известен к моменту решения и помогает упорядочить заявки. А вот для управленческого решения — «нанять дежурного на вечер, чтобы отвечать за час» — важна. Проверить её можно только A/B-тестом: случайной половине заявок отвечать быстро, второй — как обычно, и сравнить конверсию.

### Итог для коммерческого директора

- Данные без утечки: сумма договора известна только после подписания, поэтому в модель она не входит.
- Доля правильных здесь бесполезна: «никто не купит» права в 87 % случаев. Мерили тем, что важно бизнесу, — долей договоров в верхних 30 % списка.
- В календарной проверке модель нашла 72 из 94 договоров в 225 заявках. При одинаковой очереди из 166 заявок модель нашла 64 договора, правило — 57.
- Разница в семь исторических договоров показывает, как договоры распределились по очередям. Чтобы измерить дополнительные договоры от звонков, заранее назначьте сопоставимым группам две политики при одинаковом бюджете и сравните долю договоров среди всех заявок каждой группы через 30 дней.
- Для ранней очереди до первого ответа также получено 72 из 94 в топ-30 %. После получения ответа приоритет можно пересчитать.
- Быстрый ответ — один из самых сильных сигналов договора, а у Олега и у вечерних заявок ответ медленный. Прежде чем перестраивать график, проверьте эффект скорости A/B-тестом.
- Ограничения: девять месяцев одного года; качество модели нужно перепроверять на новых заявках, а список — пересчитывать.

Глава 7 пройдена: теперь вы умеете выбирать метрику под задачу, работать с дисбалансом, собирать подготовку и модель в конвейер и честно подбирать настройки.
