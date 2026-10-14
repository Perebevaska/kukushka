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

> Заявок на кейтеринг стало много, а менеджеров пять. Плотно вести — созваниваться, готовить меню, возить дегустацию — они успевают примерно 30 % заявок, остальные получают типовое предложение по почте. Сейчас каждый выбирает сам, по ощущению; негласное правило — «сначала повторные клиенты и те, кто пришёл по рекомендации». Нужна модель, которая после первого ответа клиенту ставит заявке приоритет. И главное: сколько договоров мы будем ловить, если плотно вести 30 % заявок по модели?

Данные — `catering_leads.csv`: 3000 заявок компаний на кофе-кейтеринг за январь–сентябрь 2026 года.

Столбцы: `lead_id` — номер заявки, `created` — дата и время заявки, `channel` — откуда пришла (сайт, звонок, рекомендация, соцсети, выставка, тендер), `event_type` — тип мероприятия, `city`, `company_size` — размер компании (до 50 / 50–250 / 250–1000 / 1000+ сотрудников), `guests` — число гостей, `budget_pp` — бюджет на гостя, ₽, `days_to_event` — дней от заявки до мероприятия, `manager` — кто ведёт, `response_hours` — сколько часов прошло до первого ответа менеджера, `repeat_client` — компания уже заказывала (1/0), `tasting` — просили дегустацию (1/0), `contract_rub` — сумма договора. Целевой признак `converted` — заявка закончилась договором (1/0).

## Как измерить пользу

В главе 6 модель оценивали долей правильных ответов, а в этой главе выяснили, что при редком классе это обманчиво (урок «Матрица ошибок»). Здесь договор — редкость, и обычные метрики тоже не совсем про вопрос директора. Директору не нужен ответ «да/нет» по каждой заявке: ему нужен **порядок**. Менеджеры возьмут верхние 30 % списка, и важно одно — какая доля всех договоров окажется в этих 30 %.

Назовём это **долей пойманных договоров в топ-30 %**. Это полнота (урок «Precision, recall и F1»), но при пороге, который задан не числом 0.5, а объёмом работы: «сколько заявок мы успеваем». Ориентиры:

- случайные 30 % заявок поймают около 30 % договоров;
- идеальная модель — все 100 %, если договоров меньше 30 % заявок;
- правило директора — где-то между, это и есть планка.

Порядок заявок целиком описывает ROC-AUC (урок «Порог, PR- и ROC-кривые»): насколько часто заявка с договором стоит в списке выше заявки без него. Поэтому настройки будем подбирать по AUC, а отчитываться перед директором — долей пойманных договоров.

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

Заметьте, что порога 0.5 здесь нет: заявка 4 с оценкой 0.40 не попала в работу не потому, что «меньше половины», а потому, что менеджеров не хватает. Если завтра наймут шестого, топ станет шире, и та же модель даст другую долю. Поэтому метрику считают для того объёма работы, который реально есть.

```python
import numpy as np
score = np.array([0.81, 0.64, 0.55, 0.40, 0.33, 0.20, 0.12, 0.10, 0.08, 0.05])
deal = np.array([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
top = np.argsort(-score)[:int(0.3 * len(score))]
print(deal[top].sum() / deal.sum())
```

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

Начиная с пятого шага, перед задачей курс сам готовит `d` (с признаками из шага 4), `X`, `y`, `X_train`, `X_test`, `y_train`, `y_test` и фолды `kf = KFold(n_splits=5, shuffle=True, random_state=42)`, а с шестого — ещё и подготовку `pre` из шага 5.

::: warn Типичные ошибки проекта
- **Сумма договора как признак.** `contract_rub` известна только после подписания — это утечка, модель «угадает» всё.
- **Топ-30 % от всех заявок вместо теста.** Метрику считаем на тех же отложенных заявках, что и прогноз.
- **Отчёт долей правильных.** «87 %» здесь набирает модель «никто не купит».
- **Скорость ответа как рычаг.** Сильный признак ≠ причина; решение о найме дежурного — после A/B-теста.
:::

::: tip
Это повторение всей главы: метрики (уроки «Матрица ошибок», «Precision, recall и F1» и «Порог, PR- и ROC-кривые»), дисбаланс (урок «Дисбаланс классов»), масштабирование (урок «Масштабирование и ближайшие соседи»), признаки (урок «Новые признаки»), конвейер (урок «Pipeline: предобработка и модель вместе») и подбор настроек (урок «Подбор гиперпараметров»). В подсказках указано, на какой урок опирается шаг.
:::

## Практика

## task: look | Шаг 1. Осмотр | base

Загрузите `catering_leads.csv` в `d`. Сохраните:

- `conv_rate` — долю заявок с договором (3 знака);
- `n_contracts` — сколько всего договоров;
- `budget_na` — долю заявок с пустым `budget_pp` (3 знака);
- `size_na` — сколько заявок с пустым `company_size`;
- `contract_match` — `True`, если `contract_rub` заполнен **ровно** у тех заявок, где `converted == 1` (и пуст у всех остальных).

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
```

### starter
```python
import pandas as pd
```

### check
```python
_d = _pd0.read_csv('catering_leads.csv')
_x = need('d', _pd0.DataFrame)
assert len(_x) == len(_d) and list(_x.columns) == list(_d.columns), 'd — вся таблица catering_leads.csv без изменений.'
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
d = pd.read_csv("catering_leads.csv")
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
import pandas as pd
d = pd.read_csv("catering_leads.csv")
```

### starter
```python
# d — таблица заявок
```

### check
```python
_d = _pd0.read_csv('catering_leads.csv')
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
import pandas as pd
d = pd.read_csv("catering_leads.csv")
```

### starter
```python
# d — таблица заявок
```

### check
```python
_d = _pd0.read_csv('catering_leads.csv')
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
Пропуски не случайны. Клиент, который не назвал размер компании, покупает реже (около 9 % против 14 %): часто это «прощупывание» без серьёзного намерения. Поэтому пропуск размера не заменяем самой частой категорией, а делаем **отдельной категорией** «не указан» — так модель сможет учесть, что пустое поле само по себе сигнал. С бюджетом разница меньше (12 % против 14 %), зато сам бюджет говорит много: от 450 ₽ на гостя договоров втрое больше, чем при меньшем бюджете. Пропуск бюджета заполним медианой обучающей части — это нейтральное значение, а не «бюджет ноль»: в отличие от среднего чека гостей без визитов (глава 6), здесь бюджет есть, его просто не назвали.

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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
import pandas as pd
d = pd.read_csv("catering_leads.csv")
```

### starter
```python
import pandas as pd
created = pd.to_datetime(d["created"])
```

### check
```python
_d = _leads0()
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
Каждая девятая заявка приходит вечером, и из них договором заканчиваются единицы — около 2 % против 15 % днём. Причина видна во втором числе: вечерняя заявка ждёт ответа до утра, медиана — больше 13 часов против двух днём. Признаки времени считаются по самой строке (урок «Новые признаки»), поэтому их можно добавить в `d` до разбиения — утечки нет. День недели, как увидим, почти ничего не меняет, но модели это выяснять самой.

::: note
Почему отдельный флаг `evening`, если есть `hour`? Логистическая регрессия считает влияние часа одинаковым на каждый час: «каждый час позже — на столько-то хуже». А здесь не плавный спад, а ступенька в 19:00. Флаг ловит её одним коэффициентом.
:::

## task: pipe | Шаг 5. Конвейер | base

`d` с признаками из шага 4 уже готова. Соберите:

- `y` — `converted`; `X` — все столбцы `d`, кроме `lead_id`, `created`, `contract_rub` и `converted` (без `get_dummies` — подготовку сделает конвейер);
- `X_train`, `X_test`, `y_train`, `y_test` — `train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)`;
- `pre` — `ColumnTransformer` (урок «Pipeline: предобработка и модель вместе»): числовые столбцы `num` — `SimpleImputer(strategy="median")`, затем `StandardScaler()`; категориальные `cat` — `SimpleImputer(strategy="constant", fill_value="не указан")` (`SimpleImputer` умеет заполнять и текст — константой: пропуск станет отдельной категорией «не указан»), затем `OneHotEncoder(handle_unknown="ignore")`;
- `pipe` — `Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])`.

Сохраните `n_features` — сколько столбцов получается после `pre` на обучающей части, и `cv_auc` — средний ROC-AUC конвейера на фолдах `kf` по обучающей части (3 знака).

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
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
assert 'converted' not in _x.columns and 'lead_id' not in _x.columns and 'created' not in _x.columns, 'Уберите из X lead_id, created (из неё уже сделаны признаки) и сам ответ converted.'
assert list(_x.columns) == list(_X.columns), f'Столбцы X: {list(_x.columns)}, а ожидались {list(_X.columns)}. Без get_dummies — сырые столбцы.'
assert list(need('X_test').index) == list(_Xte.index) and list(need('y_train').index) == list(_ytr.index), 'Разбиение не то: test_size=0.25, random_state=42, stratify=y.'
_p = need('pipe', _P0)
assert list(_p.named_steps) == ['prep', 'model'], f'Шаги pipe: {list(_p.named_steps)}, а нужны ["prep", "model"].'
assert isinstance(_p.named_steps['model'], _LR0), 'Последний шаг pipe — LogisticRegression(max_iter=2000).'
_nf = _pre0().fit_transform(_Xtr).shape[1]
assert need('n_features') == _nf, f'n_features = {need("n_features")}, а после подготовки получается {_nf} столбцов. Проверьте списки num и cat и fit_transform(X_train).'
_a = round(_cvs0(_P0([('prep', _pre0()), ('model', _LR0(max_iter=2000))]), _Xtr, _ytr, cv=_k, scoring='roc_auc').mean(), 3)
assert close(need('cv_auc'), _a), f'cv_auc = {need("cv_auc")}, а ожидалось {_a}. cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc").mean().'
```

### hint
Урок «Pipeline: предобработка и модель вместе»: для категорий два шага подряд — `make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"), OneHotEncoder(handle_unknown="ignore"))`.

### hint
`pre.fit_transform(X_train).shape[1]` — число столбцов после подготовки. Метрику задаёт `scoring="roc_auc"`.

### solution
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

y = d["converted"]
X = d.drop(columns=["lead_id", "created", "contract_rub", "converted"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
n_features = pre.fit_transform(X_train).shape[1]
cv_auc = round(cross_val_score(pipe, X_train, y_train, cv=kf, scoring="roc_auc").mean(), 3)
print(n_features, cv_auc)
```

### explain
9 числовых столбцов и 27 флагов категорий — включая флаг «не указан» для размера компании. Медиану бюджета конвейер на каждом фолде считает заново по обучающим строкам — утечки нет (урок «Pipeline: предобработка и модель вместе»). AUC около 0.86: случайная пара «заявка с договором — заявка без» упорядочена верно в шести случаях из семи. Тест (750 заявок) отложен до шага 9.

## task: trap | Шаг 6. Ловушка дисбаланса | plus

Курс подготовил `X_train`, `y_train`, фолды `kf` и необученный `pre` из шага 5. Посчитайте на фолдах `kf` по обучающей части (все — среднее, 3 знака):

- `dummy_acc` — долю правильных `DummyClassifier(strategy="most_frequent")`;
- `forest_acc` и `forest_f1` — долю правильных и F1 конвейера `pre` + `RandomForestClassifier(n_estimators=50, min_samples_leaf=5, random_state=0)`;
- `balanced_f1` — F1 того же конвейера, но с лесом `class_weight="balanced"`.

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
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
X = d.drop(columns=["lead_id", "created", "contract_rub", "converted"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
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

Напишите функцию `catch_rate(y_true, scores, share=0.3)` — долю всех договоров, которые попадают в верхние `share` заявок по оценке:

1. сделайте `pd.Series(scores, index=y_true.index)`;
2. возьмите `int(len(...) * share)` заявок с наибольшей оценкой (`nlargest`);
3. верните сумму `y_true` по ним, делённую на сумму `y_true` по всем.

Затем посчитайте точку сравнения — правило директора на **обучающей** части: правило отмечает заявку, если клиент повторный **или** пришёл по рекомендации. Правило — не оценка, а отметка 0/1, и отмечает оно не 30 % заявок, поэтому `catch_rate` к нему не применяйте. Сохраните:

- `rule_share` — какую долю заявок `X_train` отмечает правило (3 знака);
- `rule_catch` — какую долю договоров `y_train` оно ловит: договоры среди отмеченных правилом заявок, делённые на все договоры `y_train` (3 знака);
- `random_catch` — `catch_rate` для случайных оценок `np.random.default_rng(0).random(len(y_train))` (3 знака).

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
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
X = d.drop(columns=["lead_id", "created", "contract_rub", "converted"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
```

### starter
```python
import numpy as np
import pandas as pd

def catch_rate(y_true, scores, share=0.3):
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
```

### hint
Тело функции — три строки: `s = pd.Series(scores, index=y_true.index)`, `top = s.nlargest(int(len(s) * share)).index`, `return y_true.loc[top].sum() / y_true.sum()`.

### hint
«Или» для масок — `|`, каждое условие в скобках: `(X_train["repeat_client"] == 1) | (X_train["channel"] == "рекомендация")`.

### solution
```python
import numpy as np
import pandas as pd

def catch_rate(y_true, scores, share=0.3):
    s = pd.Series(scores, index=y_true.index)
    top = s.nlargest(int(len(s) * share)).index
    return y_true.loc[top].sum() / y_true.sum()

rule = (X_train["repeat_client"] == 1) | (X_train["channel"] == "рекомендация")
rule_share = round(rule.mean(), 3)
rule_catch = round(y_train[rule].sum() / y_train.sum(), 3)
random_catch = round(catch_rate(y_train, np.random.default_rng(0).random(len(y_train))), 3)
print(rule_share, rule_catch, random_catch)
```

### explain
Случайный выбор ловит долю договоров, равную доле заявок, — около 30 %. Правило директора отмечает чуть больше пятой части заявок и ловит в них почти 60 % договоров — примерно в 2.5 раза больше, чем случайный выбор того же объёма. Это планка для модели. Сравнивать с правилом честно при одинаковом объёме работы: правило отмечает меньше 30 % заявок, поэтому на тесте посчитаем и топ-30 %, и топ такого же размера, как у правила.

## task: grid | Шаг 8. Подбор настроек | plus

Курс подготовил `pipe` из шага 5 (подготовка + `LogisticRegression(max_iter=2000)`, не обучен). Подберите настройки модели `GridSearchCV` (урок «Подбор гиперпараметров») по сетке

- `C`: 0.01, 0.1, 1, 10;
- `class_weight`: `None`, `"balanced"`

с `cv=kf` и `scoring="roc_auc"` на обучающей части. Почему AUC, а не `catch_rate` из шага 7: AUC смотрит на весь порядок заявок и устойчивее на фолдах, а в топ-30 % одного фолда всего около 70 договоров — доля по ним сильно шумит. Сохраните обученный поиск в `grid`, а также:

- `best_params` — лучшие настройки (`best_params_`);
- `best_auc` — лучший средний AUC (3 знака);
- `res` — `pd.DataFrame(grid.cv_results_)`;
- `spread` — разницу между лучшим и худшим `mean_test_score` из `res` (3 знака).

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
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
X = d.drop(columns=["lead_id", "created", "contract_rub", "converted"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
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
Лучшие настройки — `C=1` без весов, то есть обычная логистическая регрессия; вся сетка уложилась в полтора пункта AUC. Это нормальный и полезный результат: подбор показал, что настройки здесь почти не важны, и дальше можно не тратить на них время. Обратите внимание на `class_weight`: в шаге 6 он поднял F1 леса больше чем вдвое, а AUC почти не меняет (урок «Дисбаланс классов»). Веса сдвигают оценки к редкому классу, но порядок заявок остаётся прежним, а для списка «верхние 30 %» важен только порядок.

::: note
Для сравнения: лес из шага 6 с `class_weight="balanced"` на тех же фолдах даёт AUC около 0.86 — столько же, сколько логистическая регрессия. Когда модели равны, берём более простую: её коэффициенты можно показать директору.
:::

## task: final | Шаг 9. Сколько договоров в топ-30 % | base

Курс обучил лучший конвейер из шага 8 на всей обучающей части — он в `best`, — и определил функцию `catch_rate` из шага 7. Теперь — один раз — проверьте на тесте (3 знака):

- `test_auc` — ROC-AUC `best` на `X_test`;
- `model_catch` — `catch_rate` вероятностей `best` на тесте (топ-30 %);
- `rule_share_test` и `rule_catch_test` — какую долю тестовых заявок отмечает правило директора и какую долю договоров оно ловит;
- `model_same` — `catch_rate` модели при `share=rule_share_test`: сколько ловит модель, если вести столько же заявок, сколько отмечает правило.

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
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
X = d.drop(columns=["lead_id", "created", "contract_rub", "converted"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
pipe = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000))])
best = Pipeline([("prep", pre), ("model", LogisticRegression(max_iter=2000, C=1, class_weight=None))]).fit(X_train, y_train)
def catch_rate(y_true, scores, share=0.3):
    s = pd.Series(scores, index=y_true.index)
    top = s.nlargest(int(len(s) * share)).index
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
_s = _P0([('prep', _pre0()), ('model', _LR0(max_iter=2000))]).fit(_Xtr, _ytr).predict_proba(_Xte)[:, 1]
_a = round(_auc(_yte, _s), 3)
assert close(need('test_auc'), _a), f'test_auc = {need("test_auc")}, а ожидалось {_a}. roc_auc_score(y_test, best.predict_proba(X_test)[:, 1]).'
_mc = round(_catch0(_yte, _s), 3)
assert close(need('model_catch'), _mc), f'model_catch = {need("model_catch")}, а ожидалось {_mc}. catch_rate(y_test, вероятности на X_test).'
_r = (_Xte['repeat_client'] == 1) | (_Xte['channel'] == 'рекомендация')
_rs, _rc = round(_r.mean(), 3), round(_yte[_r].sum() / _yte.sum(), 3)
assert close(need('rule_share_test'), _rs) and close(need('rule_catch_test'), _rc), f'rule_share_test, rule_catch_test = {need("rule_share_test")}, {need("rule_catch_test")}, а ожидалось {_rs}, {_rc}. Правило — на X_test, договоры — y_test.'
_ms = round(_catch0(_yte, _s, share=_rs), 3)
assert close(need('model_same'), _ms, 0.0011), f'model_same = {need("model_same")}, а ожидалось {_ms}. catch_rate(y_test, вероятности, share=rule_share_test).'
```

### hint
Вероятности: `scores = best.predict_proba(X_test)[:, 1]`. Тогда `catch_rate(y_test, scores)` — топ-30 %.

### hint
Правило на тесте — та же маска, что в шаге 7, только по `X_test`; для `model_same` передайте `share=rule_share_test`.

### solution
```python
from sklearn.metrics import roc_auc_score
scores = best.predict_proba(X_test)[:, 1]
test_auc = round(roc_auc_score(y_test, scores), 3)
model_catch = round(catch_rate(y_test, scores), 3)
rule = (X_test["repeat_client"] == 1) | (X_test["channel"] == "рекомендация")
rule_share_test = round(rule.mean(), 3)
rule_catch_test = round(y_test[rule].sum() / y_test.sum(), 3)
model_same = round(catch_rate(y_test, scores, share=rule_share_test), 3)
print(test_auc, model_catch, rule_share_test, rule_catch_test, model_same)
```

### explain
Ответ директору. В тесте 750 заявок и 99 договоров. Если плотно вести 30 % заявок по модели, в этот список попадают около 89 % договоров (88 из 99); случайные 30 % поймали бы около 30. Правило «повторные и рекомендации» отмечает 23 % заявок и ловит 56 % договоров, а модель на таком же объёме — около 80 %. AUC на тесте около 0.91 — выше, чем на кросс-валидации (около 0.86): тест оказался «проще», так бывает (глава 6, урок «Честное сравнение моделей»), но порядок сравнения от этого не меняется.

Модель выигрывает у правила, потому что складывает много сигналов сразу: канал и повторность, но ещё бюджет, срок до мероприятия, просьбу о дегустации и скорость первого ответа — по модулю коэффициента она на втором месте после флага канала «рекомендация» (`coef_`, урок «Масштабирование и ближайшие соседи»). О ней — в шаге 10.

## task: speed | Шаг 10. Скорость ответа: причина или следствие? | star

Один из самых сильных сигналов модели — `response_hours`, и вывод «отвечайте быстрее — будет больше договоров» напрашивается. Проверим две вещи.

**Модель без скорости.** Если ставить приоритет **в момент прихода** заявки, скорости ответа ещё нет. Соберите такую же подготовку без `response_hours` (список `num_now`), конвейер с `LogisticRegression(max_iter=2000)`, обучите на `X_train` и сохраните `catch_now` — `catch_rate` на тесте (3 знака).

**Менеджер Олег.** У Олега конверсия ниже, чем у коллег. Сохраните по всей таблице `d` (3 знака):

- `oleg_wait` и `others_wait` — медиану `response_hours` у Олега и у остальных менеджеров (1 знак);
- `oleg_fast` и `others_fast` — конверсию заявок с ответом за 2 часа или быстрее (`response_hours <= 2`) у Олега и у остальных.

Подготовка `pre`, списки `num` и `cat` и функция `catch_rate` — уже есть.

### setup
```python
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
    _X = _d.drop(columns=['lead_id', 'created', 'contract_rub', 'converted'])
    _Xtr, _Xte, _ytr, _yte = _tts0(_X, _y, test_size=0.25, random_state=42, stratify=_y)
    return _d, _X, _y, _Xtr, _Xte, _ytr, _yte, _KF0(n_splits=5, shuffle=True, random_state=42)
def _pre0(num=_NUM0):
    return _CT0([
        ('num', _mp0(_SI0(strategy='median'), _SS0()), num),
        ('cat', _mp0(_SI0(strategy='constant', fill_value='не указан'), _OHE0(handle_unknown='ignore')), _CAT0),
    ])
def _catch0(yt, s, share=0.3):
    _s = _pd0.Series(_np0.asarray(s), index=yt.index)
    return yt.loc[_s.nlargest(int(len(_s) * share)).index].sum() / yt.sum()
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
X = d.drop(columns=["lead_id", "created", "contract_rub", "converted"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
num = ["guests", "budget_pp", "days_to_event", "response_hours", "repeat_client", "tasting",
       "hour", "weekday", "evening"]
cat = ["channel", "event_type", "city", "company_size", "manager"]
pre = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
def catch_rate(y_true, scores, share=0.3):
    s = pd.Series(scores, index=y_true.index)
    top = s.nlargest(int(len(s) * share)).index
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
pre_now = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_now),
    ("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="не указан"),
                          OneHotEncoder(handle_unknown="ignore")), cat),
])
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
Без скорости ответа модель ловит в топ-30 % около 85 % договоров вместо 89 % — по-прежнему намного лучше правила. Значит, ставить приоритет можно уже в момент прихода заявки, а после первого ответа — уточнять.

Олег отвечает медленнее всех: медиана около 6 часов против двух у коллег. Но когда он отвечает за два часа, его заявки заканчиваются договором не реже, чем у остальных (около 21 % против 20 %). Похоже, дело не в Олеге, а в скорости.

**Похоже — но не доказано.** Это наблюдение, а не эксперимент (глава 5). Быстрый ответ может быть причиной договора, а может быть и следствием: менеджер сразу отвечает тем, кто звонит сам, пишет подробную заявку и явно готов покупать, а «холодные» заявки откладывает. Вечерние заявки ждут дольше и покупают реже — но вечером могут писать и менее решительные клиенты. Модели для ранжирования эта разница не важна: признак честно известен к моменту решения и помогает упорядочить заявки. А вот для управленческого решения — «нанять дежурного на вечер, чтобы отвечать за час» — важна. Проверить её можно только A/B-тестом: случайной половине заявок отвечать быстро, второй — как обычно, и сравнить конверсию.

### Итог для коммерческого директора

- Данные без утечки: сумма договора известна только после подписания, поэтому в модель она не входит.
- Доля правильных здесь бесполезна: «никто не купит» права в 87 % случаев. Мерили тем, что важно бизнесу, — долей договоров в верхних 30 % списка.
- Модель (логистическая регрессия в конвейере, настройки подобраны кросс-валидацией) на отложенном тесте ловит в топ-30 % около 89 % договоров; случайный выбор — 30 %, правило «повторные и рекомендации» — 56 % на 23 % заявок, модель на таком же объёме — около 80 %.
- Приоритет можно ставить сразу при поступлении заявки (около 85 % договоров в топ-30 %) и обновлять после первого ответа.
- Быстрый ответ — один из самых сильных сигналов договора, а у Олега и у вечерних заявок ответ медленный. Прежде чем перестраивать график, проверьте эффект скорости A/B-тестом.
- Ограничения: девять месяцев одного года; качество модели нужно перепроверять на новых заявках, а список — пересчитывать.

Глава 7 пройдена: теперь вы умеете выбирать метрику под задачу, работать с дисбалансом, собирать подготовку и модель в конвейер и честно подбирать настройки.
