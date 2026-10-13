---
title: "Проект: что закончилось на витрине"
files: [showcase.npz, showcase_day.npz]
lead: "Финал главы. Камера над витриной снимает 12 ячеек каждые 15 минут, и пекарня хочет получать сигнал, когда выпечка закончилась. Модель, обученная на дневных кадрах, отлично работает днём — и полностью слепнет вечером, когда в зале включают другой свет. Находим причину, чиним, строим правило оповещений и отвечаем пекарне, когда допекать."
recap:
  - "Тестовая выборка из того же источника, что обучение, не гарантирует работы в новых условиях: вечерний свет — сдвиг данных, который проверяют отдельно."
  - "Причину ищут в простых статистиках входа: средняя яркость кадров по времени показала ступеньку в 18:00."
  - "Нормировка каждого кадра делает модель нечувствительной к общей яркости — вечерняя точность возвращается."
  - "Ошибку модели гасит правило над её ответами: оповещать, только если ячейка пуста два кадра подряд."
  - "Выход проекта — не точность, а решение: когда допекать, сколько часов витрина простаивает пустой."
---

## Задача

> Над витриной в KZN-1 поставили камеру. Витрина — 12 ячеек: 0–3 круассаны, 4–7 маффины, 8–11 печенье. Камера снимает каждые 15 минут с 7:00 до 22:00, программа нарезает кадр на ячейки.
>
> Хотим: оповещение пекарю, когда ячейка опустела, и понять, правильно ли мы допекаем — сейчас в 13:00 и 17:00.
>
> У нас есть 2000 размеченных вырезок (`showcase.npz`) и один полностью размеченный день с камеры (`showcase_day.npz`): кадры, номер ячейки, время и что там было на самом деле.
>
> *Управляющая KZN-1*

## План

1. Модель на размеченных вырезках, проверка на дне с камеры — отдельно днём и вечером.
2. Диагностика: что изменилось вечером.
3. Исправление нормировкой и повторная проверка.
4. Сколько часов ячейки стоят пустыми до допекания.
5. Правило оповещений и его проверка.
6. Когда допекать.

::: figure showcase-pipeline
Как будет работать система: кадр витрины режется на 12 ячеек, модель называет содержимое каждой, а правило поверх модели решает, когда звать пекаря.
:::

::: figure alert-rule
Условный пример для одной ячейки: одиночное «пусто» в 13:30 — ошибка модели или человек у витрины, оповещения нет; два «пусто» подряд в 14:30 и 14:45 — сигнал.
:::

В `showcase_day.npz`: `X` — 732 кадра 32 × 32 (61 момент × 12 ячеек), `slot` — номер ячейки, `time` — время `"ЧЧ:ММ"`, `y` — что было на самом деле (0 — пусто, 1 — круассан, 2 — маффин, 3 — печенье).

::: quiz
Оповещение «витрина пустая» срабатывает по одному кадру. Почему стоит требовать несколько пустых кадров подряд?

- [x] Одиночные ошибки модели (блик, человек перед витриной) не будут дёргать бариста, а настоящая пустота повторится
  > Правило поверх модели снижает ложные тревоги ценой небольшой задержки.
- [ ] Модель не умеет работать с одним кадром
  > Умеет — проблема в цене её ошибок.
- [ ] Так модель станет точнее
  > Модель та же, меняется правило реакции на её ответы.
- [ ] Кадров слишком много для обработки
  > Обработка тут ни при чём.
:::

## task: day | Шаг 1. День и вечер | base

Обучите `RandomForestClassifier(100, random_state=0)` на всех 2000 вырезках (`X / 255`, вытянутые в строки). Предскажите классы для кадров дня (`XD / 255`). Сохраните `pred_raw`, `acc_day` и `acc_evening` — доли верных до 18:00 и с 18:00 (3 знака), `n_empty_evening` — сколько вечерних кадров на самом деле пустые и `n_found_evening` — сколько из них модель назвала пустыми.

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
D = np.load("showcase_day.npz")
XD, slot, tm, yD = D["X"] / 255, D["slot"], D["time"], D["y"]
flat = lambda Z: Z.reshape(len(Z), -1)

```

### check
```python
import numpy as _np
from sklearn.ensemble import RandomForestClassifier as _RF
d0 = _np.load('showcase.npz'); D0 = _np.load('showcase_day.npz')
fl = lambda Z: Z.reshape(len(Z), -1)
p = _RF(100, random_state=0).fit(fl(d0['X'] / 255), d0['y']).predict(fl(D0['X'] / 255))
ev = D0['time'] >= '18:00'; t = D0['y']
assert (_np.asarray(need('pred_raw')) == p).mean() > 0.99, 'pred_raw — предсказания леса для всех 732 кадров дня.'
assert close(need('acc_day'), round(float((p == t)[~ev].mean()), 3), 0.006), f'acc_day = {need("acc_day")}.'
assert close(need('acc_evening'), round(float((p == t)[ev].mean()), 3), 0.006), f'acc_evening = {need("acc_evening")}.'
assert need('n_empty_evening') == int(((t == 0) & ev).sum()), f'n_empty_evening = {need("n_empty_evening")}.'
assert abs(need('n_found_evening') - int(((t == 0) & (p == 0) & ev).sum())) <= 1, f'n_found_evening = {need("n_found_evening")}.'
```

### hint
Лес обучается на всех вырезках `showcase.npz` (вытянутых в строки `flat(X)`), а предсказывает кадры дня `flat(XD)`. Оба набора — в долях 0–1.

### hint
Вечер — `ev = tm >= "18:00"` (строки времени сравниваются как текст, и это работает для формата «ЧЧ:ММ»). Доля верных днём — `(pred_raw == yD)[~ev].mean()`.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
D = np.load("showcase_day.npz")
XD, slot, tm, yD = D["X"] / 255, D["slot"], D["time"], D["y"]
flat = lambda Z: Z.reshape(len(Z), -1)

forest = RandomForestClassifier(100, random_state=0).fit(flat(X), y)
pred_raw = forest.predict(flat(XD))
ev = tm >= "18:00"
acc_day = round(float((pred_raw == yD)[~ev].mean()), 3)
acc_evening = round(float((pred_raw == yD)[ev].mean()), 3)
n_empty_evening = int(((yD == 0) & ev).sum())
n_found_evening = int(((yD == 0) & (pred_raw == 0) & ev).sum())
print(acc_day, acc_evening, n_empty_evening, n_found_evening)
```

### explain
Днём — около 0.94, как на тесте. Вечером — около 0.23, хуже случайного угадывания из четырёх классов. А главное: из 94 вечерних пустых ячеек модель не нашла ни одной (или одну — лес на вашем компьютере может чуть отличаться) — пустой поднос она почти всегда называет печеньем. Если бы систему запустили по результатам обычного теста, вечером пекарь не получил бы ни одного оповещения, и никто бы не понял почему.

## task: light | Шаг 2. Что изменилось | base

Посчитайте среднюю яркость каждого кадра дня и усредните по времени: `bright` — Series с индексом-временем (61 значение). Сохраните `ratio` — отношение средней яркости вечерних кадров (с 18:00) к дневным (3 знака) и `step_time` — время, в которое яркость упала сильнее всего относительно предыдущего момента. Нарисуйте `bright`.

### setup
```python
import numpy as np
D = np.load("showcase_day.npz")
XD, slot, tm, yD = D["X"] / 255, D["slot"], D["time"], D["y"]
```

### starter
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

```

### check
```python
import numpy as _np
import pandas as _pd
D0 = _np.load('showcase_day.npz'); X0, t0 = D0['X'] / 255, D0['time']
b = _pd.Series(X0.reshape(len(X0), -1).mean(1)).groupby(t0).mean()
g = need('bright', _pd.Series)
assert len(g) == 61 and _np.allclose(g.values, b.values), 'bright: средняя яркость кадров, сгруппированная по времени.'
r = round(float(X0[t0 >= '18:00'].mean() / X0[t0 < '18:00'].mean()), 3)
assert close(need('ratio'), r, 0.002), f'ratio = {need("ratio")}, а нужно {r}.'
assert str(need('step_time')) == str(b.diff().idxmin()), f'step_time = {need("step_time")}.'
assert len(figs) >= 1, 'Нарисуйте bright.'
```

### hint
`pd.Series(XD.reshape(len(XD), -1).mean(axis=1)).groupby(tm).mean()`; самое сильное падение — `bright.diff().idxmin()`.

### hint
Отношение вечера к дню: `XD[tm >= "18:00"].mean() / XD[tm < "18:00"].mean()` — среднее по всем пикселям всех кадров каждой части дня.

### solution
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

bright = pd.Series(XD.reshape(len(XD), -1).mean(axis=1)).groupby(tm).mean()
ratio = round(float(XD[tm >= "18:00"].mean() / XD[tm < "18:00"].mean()), 3)
step_time = bright.diff().idxmin()
print(ratio, step_time)
ax = bright.plot(figsize=(9, 3), marker=".")
ax.set_ylabel("средняя яркость кадра")
```

### explain
Ступенька ровно в 18:00: кадры стали на треть темнее — в зале включили вечерний свет. Днём яркость тоже немного колеблется (выпечку раскупают — светлого подноса становится больше), но это плавные изменения в пределах того, что модель видела при обучении. Вечерних кадров в обучающих данных не было вовсе. Это типичная история: модель ломает не сложный случай, а простое изменение условий съёмки, о котором никто не подумал.

## task: fix | Шаг 3. Нормировка | plus

Обучите такой же лес на нормированных вырезках: каждая строка (кадр) минус её среднее, делённое на её стандартное отклонение. Предскажите нормированные кадры дня: `pred_norm`. Сохраните `acc_day_n`, `acc_evening_n` (3 знака) и для вечера — `recall_empty` (доля пустых ячеек, которые модель нашла) и `precision_empty` (доля верных среди ответов «пусто»), 3 знака.

### setup
```python
import numpy as np
d = np.load("showcase.npz")
X, y = d["X"] / 255, d["y"]
D = np.load("showcase_day.npz")
XD, slot, tm, yD = D["X"] / 255, D["slot"], D["time"], D["y"]
ev = tm >= "18:00"
```

### starter
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def normalize(Z):
    ...

```

### check
```python
import numpy as _np
from sklearn.ensemble import RandomForestClassifier as _RF
d0 = _np.load('showcase.npz'); D0 = _np.load('showcase_day.npz')
fl = lambda Z: Z.reshape(len(Z), -1)
nz = lambda Z: (fl(Z) - fl(Z).mean(1, keepdims=True)) / fl(Z).std(1, keepdims=True)
p = _RF(100, random_state=0).fit(nz(d0['X'] / 255), d0['y']).predict(nz(D0['X'] / 255))
ev = D0['time'] >= '18:00'; t = D0['y']
assert (_np.asarray(need('pred_norm')) == p).mean() > 0.99, 'pred_norm — предсказания леса на нормированных кадрах дня.'
w = {'acc_day_n': (p == t)[~ev].mean(), 'acc_evening_n': (p == t)[ev].mean(),
     'recall_empty': ((p == 0) & (t == 0) & ev).sum() / ((t == 0) & ev).sum(),
     'precision_empty': ((p == 0) & (t == 0) & ev).sum() / ((p == 0) & ev).sum()}
for k, v in w.items():
    assert close(need(k), round(float(v), 3), 0.008), f'{k} = {need(k)}, а нужно {v:.3f}.'
```

### hint
`normalize` — та же функция, что в задаче «Вечерний свет» урока «Модели на пикселях: ошибки, аугментация, устойчивость»: каждая строка минус её среднее, делённая на её отклонение (`axis=1, keepdims=True`).

### hint
Обучение — `normalize(X)`, предсказание — `normalize(XD)`. Полнота «пусто» вечером: `((pred_norm == 0) & (yD == 0) & ev).sum() / ((yD == 0) & ev).sum()`.

### solution
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def normalize(Z):
    A = Z.reshape(len(Z), -1)
    return (A - A.mean(axis=1, keepdims=True)) / A.std(axis=1, keepdims=True)

forest_n = RandomForestClassifier(100, random_state=0).fit(normalize(X), y)
pred_norm = forest_n.predict(normalize(XD))
acc_day_n = round(float((pred_norm == yD)[~ev].mean()), 3)
acc_evening_n = round(float((pred_norm == yD)[ev].mean()), 3)
found = ((pred_norm == 0) & (yD == 0) & ev).sum()
recall_empty = round(float(found / ((yD == 0) & ev).sum()), 3)
precision_empty = round(float(found / ((pred_norm == 0) & ev).sum()), 3)
print(acc_day_n, acc_evening_n, recall_empty, precision_empty)
```

### explain
Днём точность даже чуть выросла (около 0.96), вечером — около 0.86 вместо 0.23. Для оповещений главное: вечером модель находит все пустые ячейки, а около 8 % её ответов «пусто» — ложные (круассан в тусклом свете иногда принимает за пустой поднос). Виды выпечки вечером по-прежнему путаются чаще, чем днём: свет меняет не только общую яркость, но и контраст. Следующий шаг для пекарни — доразметить сотню вечерних кадров и добавить их в обучение.

Почему лес на пикселях, а не признаки из фильтров уроков «Свёртка и фильтры» и «Свёрточные нейросети»? Мы проверили: 16 случайных фильтров с той же нормировкой кадров и логистической регрессией дают днём около 0.94, а вечером — около 0.65 против 0.86 у леса. Представление, которое лучше на дневном тесте, не обязательно лучше в новых условиях, поэтому выбирали по вечерним кадрам.

## task: hours | Шаг 4. Часы пустой витрины | base

Ответы нормированной модели — в `pred` (заготовка). Соберите таблицу `df` с колонками `time`, `slot`, `product` (название товара ячейки: 0–3 круассан, 4–7 маффин, 8–11 печенье), `true`, `pred`. Посчитайте для утра (до 13:00, когда допекают) сколько часов ячейки каждого товара стояли пустыми: каждый пустой кадр — 0.25 часа. Сохраните `empty_hours` — DataFrame с индексом-товаром и столбцами `модель` и `факт`.

### setup
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
d = np.load("showcase.npz")
D = np.load("showcase_day.npz")
XD, slot, tm, yD = D["X"] / 255, D["slot"], D["time"], D["y"]
def normalize(Z):
    A = Z.reshape(len(Z), -1)
    return (A - A.mean(axis=1, keepdims=True)) / A.std(axis=1, keepdims=True)
pred = RandomForestClassifier(100, random_state=0).fit(normalize(d["X"] / 255), d["y"]).predict(normalize(XD))
```

### starter
```python
import numpy as np
import pandas as pd

product = np.array(["круассан"] * 4 + ["маффин"] * 4 + ["печенье"] * 4)

```

### check
```python
import numpy as _np
import pandas as _pd
D0 = _np.load('showcase_day.npz'); p = need('pred')
pr = _np.array(['круассан'] * 4 + ['маффин'] * 4 + ['печенье'] * 4)
df0 = _pd.DataFrame({'time': D0['time'], 'slot': D0['slot'], 'true': D0['y'], 'pred': p}); df0['product'] = pr[df0['slot']]
g = need('df', _pd.DataFrame)
assert {'time', 'slot', 'product', 'true', 'pred'} <= set(g.columns), f'Колонки df: {list(g.columns)}.'
assert (g['product'].values == df0['product'].values).all(), 'product: по номеру ячейки (0–3 круассан, 4–7 маффин, 8–11 печенье).'
m = df0[df0['time'] < '13:00']
w = _pd.DataFrame({'модель': (m['pred'] == 0).groupby(m['product']).sum() * 0.25, 'факт': (m['true'] == 0).groupby(m['product']).sum() * 0.25})
e = need('empty_hours', _pd.DataFrame)
assert list(e.columns) == ['модель', 'факт'], f'Столбцы: {list(e.columns)}.'
assert ((e.loc[w.index] - w).abs() < 1e-9).all().all(), f'empty_hours:\n{e}\nа нужно\n{w}'
```

### hint
Начните с таблицы: `pd.DataFrame({"time": tm, "slot": slot, "true": yD, "pred": pred})`.

### hint
`product[df["slot"]]` раздаст названия по номеру ячейки. Утро — `df[df["time"] < "13:00"]`; часы — `(m["pred"] == 0).groupby(m["product"]).sum() * 0.25`.

### solution
```python
import numpy as np
import pandas as pd

product = np.array(["круассан"] * 4 + ["маффин"] * 4 + ["печенье"] * 4)
df = pd.DataFrame({"time": tm, "slot": slot, "true": yD, "pred": pred})
df["product"] = product[df["slot"]]

m = df[df["time"] < "13:00"]
empty_hours = pd.DataFrame({
    "модель": (m["pred"] == 0).groupby(m["product"]).sum() * 0.25,
    "факт": (m["true"] == 0).groupby(m["product"]).sum() * 0.25,
})
print(empty_hours)
```

### explain
Модель оценивает простой почти точно: расхождение с фактом — четверть часа. За утро ячейки суммарно простояли пустыми около 21 часа — в среднем почти два часа на ячейку. Пустая ячейка в часы пик — недополученная выручка.

## task: alerts | Шаг 5. Правило оповещений | plus

Одиночная ошибка модели не должна будить пекаря. Правило: оповещение по ячейке в момент `t`, когда ячейка пуста по модели второй кадр подряд — «пусто» в `t` и в `t − 15 мин`, но не в `t − 30 мин`. Так на каждую серию пустых кадров приходится одно оповещение, в её начале, а не по оповещению на каждый следующий кадр. Если серию прервал хотя бы один кадр «не пусто», следующая серия даст новое оповещение. Таблица `df` — в заготовке.

Постройте `P` и `T` — таблицы «время × ячейка» из `True/False`: пусто по модели и по факту. Сохраните `alerts` — DataFrame с колонками `time`, `slot` (по одной строке на оповещение), `n_alerts`, `n_correct` — сколько оповещений пришлось на действительно пустую ячейку, и `n_missed` — сколько эпизодов пустоты по факту (серий подряд идущих пустых кадров ячейки) прошли без единого оповещения.

### setup
```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
d = np.load("showcase.npz")
D = np.load("showcase_day.npz")
def normalize(Z):
    A = Z.reshape(len(Z), -1)
    return (A - A.mean(axis=1, keepdims=True)) / A.std(axis=1, keepdims=True)
pred = RandomForestClassifier(100, random_state=0).fit(normalize(d["X"] / 255), d["y"]).predict(normalize(D["X"] / 255))
product = np.array(["круассан"] * 4 + ["маффин"] * 4 + ["печенье"] * 4)
df = pd.DataFrame({"time": D["time"], "slot": D["slot"], "true": D["y"], "pred": pred})
df["product"] = product[df["slot"]]
```

### starter
```python
import numpy as np
import pandas as pd

P = df.pivot(index="time", columns="slot", values="pred") == 0
T = df.pivot(index="time", columns="slot", values="true") == 0

```

### check
```python
import numpy as _np
import pandas as _pd
d0 = need('df', _pd.DataFrame)
P0 = d0.pivot(index='time', columns='slot', values='pred') == 0
T0 = d0.pivot(index='time', columns='slot', values='true') == 0
p1, p2 = P0.shift(1, fill_value=False), P0.shift(2, fill_value=False)
A0 = P0 & p1 & ~(p1 & p2)
want = sorted((str(t), int(s)) for t, s in A0.stack()[A0.stack()].index)
a = need('alerts', _pd.DataFrame)
got = sorted((str(t), int(s)) for t, s in zip(a['time'], a['slot']))
assert not (len(got) > len(want) and set(want) <= set(got)), f'Оповещений {len(got)}, а нужно {len(want)}. Похоже, оповещения повторяются внутри одной серии — нужно только её начало: «пусто» в t и t − 15, но не в t − 30.'
assert got == want, f'Оповещений {len(got)}, а нужно {len(want)}. Первые нужные: {want[:5]}.'
assert need('n_alerts') == len(want), f'n_alerts = {need("n_alerts")}.'
assert need('n_correct') == int(sum(bool(T0.loc[t, s]) for t, s in want)), f'n_correct = {need("n_correct")}.'
miss = 0
for s in T0.columns:
    col, run = T0[s].values, []
    for i, v in enumerate(list(col) + [False]):
        if v: run.append(i)
        elif run:
            if not A0[s].values[run].any(): miss += 1
            run = []
assert need('n_missed') == miss, f'n_missed = {need("n_missed")}, а нужно {miss}.'
```

### hint
Таблица «время × ячейка» — `df.pivot(index="time", columns="slot", values="pred") == 0`. Строки идут по времени, поэтому `shift(1)` сдвигает на один кадр (15 минут) назад.

### hint
`P.shift(1, fill_value=False)` — «пусто в предыдущем кадре». Оповещения: `A = P & p1 & ~(p1 & p2)`; список — `A.stack()` и отбор `True`. Для пропусков пройдите по каждой ячейке и найдите серии подряд идущих `True` в `T`; эпизод пропущен, если в его кадрах `A` нигде не `True`.

### solution
```python
import numpy as np
import pandas as pd

P = df.pivot(index="time", columns="slot", values="pred") == 0
T = df.pivot(index="time", columns="slot", values="true") == 0
p1, p2 = P.shift(1, fill_value=False), P.shift(2, fill_value=False)
A = P & p1 & ~(p1 & p2)

st = A.stack()
alerts = st[st].reset_index()[["time", "slot"]]
n_alerts = len(alerts)
n_correct = int(sum(T.loc[t, s] for t, s in zip(alerts["time"], alerts["slot"])))

n_missed = 0
for s in T.columns:
    run = []
    for i, v in enumerate(list(T[s].values) + [False]):
        if v:
            run.append(i)
        elif run:
            if not A[s].values[run].any():
                n_missed += 1
            run = []
print(n_alerts, n_correct, n_missed)
print(alerts.head(10))
```

### explain
За день — 24 оповещения на 22 эпизода пустоты: все эпизоды пойманы, ложное одно (вечерний круассан). Ещё одно оповещение — повторное: модель на один кадр «увидела» печенье в пустой ячейке, серия прервалась и началась заново. Цена правила «два кадра подряд» — задержка: пекарь узнаёт о пустой ячейке через 15 минут после того, как камера её впервые увидела. Для выпечки это приемлемо; для чего-то срочного правило было бы другим.

## task: restock | Шаг 6. Когда допекать | star

По фактическим данным (`T` и `product` — в заготовке) найдите для каждого товара `half_empty` — первое время `t`, когда в момент `t` пусты не меньше 2 из 4 ячеек товара (Series с индексом-товаром). Посчитайте `saved_hours` — сколько часов пустых ячеек (по факту, 0.25 ч за кадр) приходится на интервал 11:00–12:45 включительно: столько простоя убрало бы допекание в 11:00 вместо 13:00 (при условии, что пекарня успеет). И `saved_by_product` — то же по товарам (Series).

### setup
```python
import numpy as np
import pandas as pd
D = np.load("showcase_day.npz")
product = np.array(["круассан"] * 4 + ["маффин"] * 4 + ["печенье"] * 4)
df = pd.DataFrame({"time": D["time"], "slot": D["slot"], "true": D["y"]})
df["product"] = product[df["slot"]]
T = df.pivot(index="time", columns="slot", values="true") == 0
```

### starter
```python
import numpy as np
import pandas as pd

```

### check
```python
import numpy as _np
import pandas as _pd
T0, pr, d0 = need('T'), need('product'), need('df')
share = T0.T.groupby(pr).mean().T
w = _pd.Series({p: share.index[(share[p] >= 0.5).values][0] for p in share.columns})
g = need('half_empty', _pd.Series)
assert all(str(g[p]) == str(w[p]) for p in w.index), f'half_empty:\n{g}\nа нужно\n{w}'
m = d0[(d0['time'] >= '11:00') & (d0['time'] < '13:00')]
assert close(need('saved_hours'), (m['true'] == 0).sum() * 0.25), f'saved_hours = {need("saved_hours")}.'
sb = (m['true'] == 0).groupby(m['product']).sum() * 0.25
gs = need('saved_by_product', _pd.Series)
assert all(close(gs[p], sb[p]) for p in sb.index), f'saved_by_product:\n{gs}'
```

### hint
`T` — таблица «время × ячейка». Чтобы сгруппировать ячейки по товару, транспонируйте её (`T.T` — строки становятся ячейками), сгруппируйте и транспонируйте обратно.

### hint
Доля пустых ячеек товара по времени: `T.T.groupby(product).mean().T` — таблица «время × товар». Первое время, где доля ≥ 0.5, — `share.index[(share[p] >= 0.5).values][0]`.

### hint
Простой между 11:00 и 13:00: `m = df[(df["time"] >= "11:00") & (df["time"] < "13:00")]`, затем `(m["true"] == 0).sum() * 0.25`.

### solution
```python
import numpy as np
import pandas as pd

share = T.T.groupby(product).mean().T
half_empty = pd.Series({p: share.index[(share[p] >= 0.5).values][0] for p in share.columns})

m = df[(df["time"] >= "11:00") & (df["time"] < "13:00")]
saved_hours = (m["true"] == 0).sum() * 0.25
saved_by_product = (m["true"] == 0).groupby(m["product"]).sum() * 0.25
print(half_empty, saved_hours, saved_by_product, sep="\n\n")
```

### explain
К 11:00 половина ячеек каждого товара уже пуста (печенье — с 9:45), а допекают только в 13:00. Между 11:00 и 13:00 витрина набирает 15 часов пустых ячеек — больше двух третей утреннего простоя. Это один день, и вывод стоит подтвердить за 2–3 недели — но камера с моделью как раз и даёт такие данные каждый день.

## Итог для управляющей KZN-1

> **Камера над витриной: один размеченный день, 732 кадра ячеек.**
>
> 1. **Модель распознаёт ячейку днём в 96 % случаев, вечером — в 86 %.** Первая версия вечером не находила пустые ячейки совсем: в 18:00 включается другой свет, и кадры становятся на треть темнее. Исправлено нормировкой яркости каждого кадра. Чтобы поднять вечернюю точность, нужна сотня размеченных вечерних кадров.
> 2. **Оповещения:** сигнал, если ячейка пуста на двух кадрах подряд (через 15 минут после того, как опустела). За проверочный день пойманы все 22 случая пустоты, ложных сигналов — один.
> 3. **Допекание:** к 11:00 половина ячеек каждого товара уже пустует, печенье — с 9:45. С 11:00 до 13:00 витрина набирает 15 часов пустых ячеек. **Предложение:** перенести утреннее допекание на 11:00 (печенье — раньше) и проверить на 2–3 неделях данных с камеры, как изменится выручка выпечки.

::: tip
В работе модель будет видеть кадры, которых не было ни в обучении, ни в проверочном дне: новую выпечку, другую раскладку, солнце в окне. Раз в месяц размечайте день вручную и пересчитывайте точность, как в шаге 1, — это мониторинг из главы 8.
:::
