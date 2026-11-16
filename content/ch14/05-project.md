---
title: "Проект: что закончилось на витрине"
files: [showcase.npz, showcase_day.npz, showcase_day_next.npz, showcase_inventory.npz]
lead: "Финал главы. Камера над витриной снимает 12 ячеек каждые 15 минут, и пекарня хочет получать сигнал, когда выпечка закончилась. Модель, обученная на дневных кадрах, отлично работает днём — и полностью слепнет вечером, когда в зале включают другой свет. Находим причину, чиним, строим правило оповещений и отвечаем пекарне, когда допекать."
recap:
  - "Тестовая выборка из того же источника, что обучение, не гарантирует работы в новых условиях: вечерний свет — сдвиг данных, который проверяют отдельно."
  - "Причину ищут в простых статистиках входа: средняя яркость кадров по времени показала ступеньку в 18:00."
  - "Нормировка каждого кадра делает модель нечувствительной к общей яркости — вечерняя точность возвращается."
  - "Число пустых кадров подряд для вызова пекаря выбирают по стоимости ложных и повторных сигналов, пропусков и ожидания. Один, два и три кадра — три кандидата."
  - "Выход проекта — не точность, а решение: когда допекать, сколько часов витрина простаивает пустой."
---

## Задача

> Над витриной в KZN-1 поставили камеру. Витрина — 12 ячеек: 0–3 круассаны, 4–7 маффины, 8–11 печенье. Камера снимает каждые 15 минут с 7:00 до 22:00, программа нарезает кадр на ячейки.
>
> Хотим: оповещение пекарю, когда ячейка опустела, и понять, правильно ли мы допекаем — сейчас в 13:00 и 17:00.
>
> У нас есть 2000 размеченных вырезок (`showcase.npz`) и два размеченных дня с камеры (`showcase_day.npz` для выбора и `showcase_day_next.npz` для проверки): кадры, номер ячейки, время и что там было на самом деле.
>
> *Управляющая KZN-1*

## План

Проследите одну ячейку по ключу (time, slot) от исходного кадра и прогноза до эпизода пустоты и первого оповещения. Перемешивание журнала не должно менять соответствие; перед соседними кадрами проверяется именно 15 минут, а не соседство строк. Пропущенный снимок не подтверждает непрерывность серии.

Нормировку и число кадров подряд выберите на первом дне. Запишите модель, цены ошибок и выбранное k. Файл `showcase_day_next.npz` откройте после этой записи. На кадрах следующего дня оцените пропуски эпизодов, ложные и повторные сигналы и задержку относительно первого истинно пустого кадра. Успех на том же дне, где правило выбрано, не является независимой проверкой.


1. Модель на размеченных вырезках, проверка на дне с камеры — отдельно днём и вечером.
2. Диагностика: что изменилось вечером.
3. Исправление нормировкой и повторная проверка.
4. Сколько часов ячейки стоят пустыми до допекания.
5. Правило оповещений и его проверка.
6. Когда допекать.

Шаги 1, 3, 4 и 5 обучают лес на 2000 вырезках прямо в задаче — в браузере это занимает до полуминуты. После запуска подождите и не нажимайте «Запустить» повторно.

::: figure showcase-pipeline
Кадр делится на 12 ячеек. Модель даёт прогноз для каждой, правило решает, когда звать пекаря. На схеме показан один из кандидатов — два пустых кадра подряд.
:::

::: figure alert-rule
Один кандидат, k=2, на примере одной ячейки. Одиночное «пусто» в 13:30 — ошибка модели или человек у витрины, оповещения нет; два «пусто» подряд в 14:30 и 14:45 — сигнал.
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

## Сколько стоит дождаться второго кадра?

В коротком учебном журнале ниже одна ячейка. Снимки идут с шагом 15 минут слева направо. Состояние в журнале подписано словами. Для данных проекта переведите предсказанный класс в признак пустоты: класс 0 → `is_empty=True`, любой из классов 1–3 → `False`.

| День 1 | 09:00 | 09:15 | 09:30 | 09:45 | 10:00 | 10:15 | 10:30 | 10:45 | 11:00 | 11:15 |
|---|---|---|---|---|---|---|---|---|---|---|
| Состояние по фото | занято | занято | занято | пусто | пусто | пусто | занято | занято | занято | занято |
| Состояние по модели | пусто | занято | занято | пусто | пусто | пусто | занято | пусто | занято | занято |

Сравните правила для одного, двух и трёх кадров подряд. Каждое подаёт один сигнал в момент, когда серия впервые достигла выбранной длины. Ложный вызов пекаря стоит 45 ₽, минута ожидания в обнаруженном эпизоде — 1 ₽, пропущенный эпизод — 300 ₽. Какое правило дешевле за первый день? Затем управляющая предложила сначала проверять снимок у монитора. Ложный вызов теперь стоит 6 ₽, остальные цены прежние.

::: quiz
Зафиксируйте правило для следующего дня вместе с причиной выбора. Что вы выберете по первому журналу при новой цене?

- [x] Один кадр. Два ложных вызова теперь обходятся дешевле, чем ожидание второго кадра.
  > Для k=1, 2, 3 раньше получалось 90, 15 и 30 ₽, теперь — 12, 15 и 30 ₽. У k=1 те же два ложных сигнала; поменялась их цена. **Теперь примените выбранное вами правило ко второму дню.** С 12:30 до 13:45 снимали каждые 15 минут. По фото: занято, пусто, пусто, занято, занято, занято. По модели: пусто, пусто, занято, занято, пусто, занято. Укажите времена сигналов, число ложных вызовов и пропущенных эпизодов. Посчитайте стоимость, сохранив свой k.
  >
  > <details><summary>Сверить свой расчёт после разбора второго дня</summary>
  >
  > При k=1 сигналы приходят в 12:30 и 13:30. Оба ложные. Когда ячейка действительно опустела в 12:45, серия модели уже началась, и нового сигнала в этом эпизоде не было. Стоимость — 312 ₽. При k=2 сигнал поступил бы в 12:45, прямо в начале эпизода, затраты — 0 ₽. При k=3 сигналов нет, один пропуск стоит 300 ₽. Выбор по первому дню и результат проверки на следующем запишите отдельно.
  >
  > </details>
- [ ] Два кадра. Раз число ложных срабатываний модели прежнее, правило тоже должно остаться прежним.
  > Два кадра по-прежнему дают 15 минут задержки. Сравните 15 ₽ с новой стоимостью двух ложных вызовов и сохраните выбранное правило при разборе второго дня.
- [ ] Три кадра. Дополнительное ожидание поможет сэкономить ещё на одном ложном вызове.
  > Оба ошибочных сигнала первого дня одиночные. Переход от двух к трём кадрам добавляет 15 минут задержки при том же числе ложных вызовов.
:::

## Самостоятельно: свободное место на парковке

Парковка получает фото мест каждые 15 минут. По месту 7 прогноз «свободно» пришёл в 16:00, 16:30 и 16:45. По месту 8 он пришёл в 16:15. Клиент платит за ошибочную поездку. При k=2 какое сообщение отправить клиенту, когда и о каком месте? Что можно сказать о пропущенном снимке? Запишите ответ и данные, которые вы запросите для сравнения цены ложного сообщения и ожидания.

<details><summary>Сверить после своей записи</summary>

По месту 7 первое подтверждение придёт в 16:45: есть пара 16:30 и 16:45. В 16:15 состояние места 7 неизвестно. Единственного кадра места 8 недостаточно для его собственного сигнала. Для оценки цены нужны проверенные статусы мест, стоимость лишней поездки и ожидания. Правило, выбранное по этим ценам на первой смене, проверяют на новой.

</details>

## Письмо управляющей KZN-1

После шага 5 подготовьте короткое письмо. Укажите, как модель различает пустую и занятую ячейку днём и вечером. Какое правило вы выбрали по затратам на первом дне? Сколько стоило применение того же правила на втором, сколько эпизодов оно пропустило и сколько минут пекарь ждал сигнала? Для решения о выпечке укажите, какой простой наблюдала камера и какие сведения о спросе и расходах ещё понадобятся. Если выполните дополнительный шаг 6, дополните письмо расчётом трёх расписаний за весь день.

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
ev = D0['time'] >= '18:00'; t = D0['y']
p = _np.asarray(need('pred_raw'))
assert p.shape == t.shape, f'pred_raw.shape = {p.shape}, а нужно {t.shape}: по ответу на каждый кадр дня.'
_st = lambda q: (round(float((q == t)[~ev].mean()), 3), round(float((q == t)[ev].mean()), 3), int(((t == 0) & (q == 0) & ev).sum()))
if _st(p) != (0.943, 0.23, 0):   # эталон: так отвечает лес из условия
    # не совпало с заранее посчитанным эталоном — обучаем лес заново (на другой версии sklearn числа могут чуть отличаться)
    p = _RF(100, random_state=0).fit(fl(d0['X'] / 255), d0['y']).predict(fl(D0['X'] / 255))
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

Посчитайте среднюю яркость каждого кадра дня и усредните по времени: `bright` — Series с индексом-временем (61 значение). Сохраните `ratio` — отношение средней яркости вечерних кадров (с 18:00) к дневным (3 знака) и `step_time` — время, в которое яркость упала сильнее всего относительно предыдущего момента. Нарисуйте ряд из 61 пары «время — яркость» по порядку съёмки. Если строите по номерам кадров, подпишите несколько делений реальным временем, чтобы по графику можно было найти вечерний спад.

Готовый массив `XD` хранит яркость от 0 до 1. В исходном `X = np.load("showcase_day.npz")["X"]` пиксели имеют тип `uint8` и шкалу 0–255. Можно усреднять исходный `X` в этой шкале или сначала разделить его на 255, чтобы получить шкалу 0–1. Стройте график в той же шкале, что и `bright`. Отношение `ratio` и момент спада от выбора шкалы не меняются.

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
# XD уже в шкале 0–1. При чтении X из файла используйте 0–255 или X / 255.
# Постройте рисунок по сохранённому bright в выбранной шкале.

```

### check
```python
import numpy as _np
import pandas as _pd
D0 = _np.load('showcase_day.npz'); X0, t0 = D0['X'] / 255, D0['time']
b = _pd.Series(X0.reshape(len(X0), -1).mean(1)).groupby(t0).mean()
g = need('bright', _pd.Series)
def _clock(value):
    if isinstance(value, _np.datetime64):
        value = _pd.Timestamp(value)
    if hasattr(value, 'strftime'):
        return value.strftime('%H:%M')
    return str(value)

times = list(b.index)
labels = [_clock(value) for value in g.index]
assert len(labels) == len(times) and set(labels) == set(times), 'Индекс bright должен содержать каждое время съёмки от 07:00 до 22:00 с шагом 15 минут ровно один раз.'
ordered = _pd.Series(g.to_numpy(), index=labels).reindex(times)
assert _pd.api.types.is_numeric_dtype(ordered.dtype) and not _np.iscomplexobj(ordered), 'В bright для каждого времени нужна одна числовая средняя яркость.'
brightness = ordered.to_numpy(dtype=float, na_value=_np.nan)
if _np.allclose(brightness, b):
    unit, other_values = '0–1', b.to_numpy() * 255
else:
    assert _np.allclose(brightness, b * 255), ('Сверьте значения bright со средними по 12 кадрам каждой съёмки. '
        'Для готового XD используйте шкалу 0–1, для исходного X — 0–255; деление исходного X на 255 переводит его в 0–1.')
    unit, other_values = '0–255', b.to_numpy()
r = round(float(X0[t0 >= '18:00'].mean() / X0[t0 < '18:00'].mean()), 3)
assert close(need('ratio'), r, 0.002), f'ratio = {need("ratio")}, а нужно {r}.'
assert _clock(need('step_time')) == str(b.diff().idxmin()), f'step_time = {need("step_time")}.'
from matplotlib.colors import to_rgba as _rgba
from matplotlib.dates import AutoDateFormatter, ConciseDateFormatter, DateFormatter, num2date as _num2date
from matplotlib.collections import PathCollection as _PathCollection

def _axis_times(ax, x):
    # Convert expected time labels through Matplotlib's actual axis converter.
    if isinstance(ax.xaxis.get_major_formatter(), (AutoDateFormatter, ConciseDateFormatter, DateFormatter)):
        # Calendar axes carry timestamps in days; use the date on this chart.
        try:
            day = _num2date(x[0]).date().isoformat()
            coords = ax.convert_xunits(_pd.to_datetime([f'{day} {t}' for t in times]))
            if _np.allclose(x, coords, rtol=0, atol=1e-8):
                return True
        except (TypeError, ValueError, OverflowError):
            pass
    # Category, integer and pandas time axes: visible tick labels identify the scale.
    points = []
    lo, hi = sorted(ax.get_xlim())
    for label in ax.get_xticklabels(which='both'):
        pos = label.get_position()[0]
        if label.get_visible() and lo <= pos <= hi and label.get_text().strip():
            points.append((pos, label.get_text().strip()))
    if len(points) < 2:
        return False
    for pos, text in points:
        i = int(_np.argmin(abs(x-pos)))
        if not _np.isclose(x[i], pos, rtol=0, atol=1e-7) or text != times[i]:
            return False
    return _np.allclose(_np.diff(x), _np.diff(x)[0], rtol=1e-7, atol=1e-9)

def _right_series(ax, xy, transform, raw_times=None):
    xy = _np.ma.asarray(xy)
    if xy.shape != (len(times), 2) or _np.ma.getmaskarray(xy).any():
        return False
    xy = ax.transData.inverted().transform(transform.transform(xy))
    if not _np.isfinite(xy).all():
        return False
    if xy[-1, 0] < xy[0, 0]:
        xy = xy[::-1]
        if raw_times is not None:
            raw_times = raw_times[::-1]
    x, y = xy.T
    if not (_np.diff(x) > 0).all():
        return False
    for coordinates, limits in ((x, ax.get_xlim()), (y, ax.get_ylim())):
        lo, hi = sorted(limits)
        if coordinates.min() < lo - 1e-7 or coordinates.max() > hi + 1e-7:
            return False
    if raw_times is not None and all(isinstance(v, _pd.Period) for v in raw_times):
        if [_clock(v) for v in raw_times] != times:
            return False
        # pandas uses minute period ordinals, with major and minor time ticks.
        for tick in ax.get_xticklabels(which='both'):
            label = tick.get_text()
            if len(label) == 5 and label[2] == ':' and x[0] <= tick.get_position()[0] <= x[-1]:
                nearest = int(_np.argmin(abs(x - tick.get_position()[0])))
                if label != times[nearest]:
                    return False
    elif not _axis_times(ax, x):
        return False
    if _np.allclose(y, brightness):
        return 'match'
    if _np.allclose(y, other_values):
        return 'different_scale'
    return False

drawn = False
checks = set()
for fig in figs:
    fig.canvas.draw()
    for ax in fig.axes:
        if not ax.get_visible():
            continue
        for line in ax.lines:
            marker = line.get_marker() not in ('None', 'none', '', ' ') and line.get_markersize() > 0
            stroke = line.get_linestyle() not in ('None', 'none', '', ' ') and line.get_linewidth() > 0
            if not (line.get_visible() and line.get_alpha() != 0 and _rgba(line.get_color())[3] > 0 and (stroke or marker) and len(line.get_xdata())):
                continue
            drawn = True
            checks.add(_right_series(ax, line.get_xydata(), line.get_transform(), line.get_xdata()))
        for cloud in ax.collections:
            if not isinstance(cloud, _PathCollection) or not cloud.get_visible() or not len(cloud.get_offsets()):
                continue
            colors = [rgba for rgba in (cloud.get_facecolors(), cloud.get_edgecolors()) if len(rgba)]
            if not colors or not any((rgba[:, 3] > 0).all() for rgba in colors) or not (cloud.get_sizes() > 0).all():
                continue
            drawn = True
            xy = cloud.get_offsets()
            checks.add(_right_series(ax, xy[_np.argsort(xy[:, 0])], cloud.get_offset_transform()))

assert drawn, f'График пуст. Значения bright в шкале {unit} верны. Нарисуйте их на осях: bright.plot() или ax.plot(bright.index, bright.values).'
assert 'match' in checks or 'different_scale' not in checks, f'Шкалы не совпали. В bright яркость в шкале {unit}, а на оси Y использована другая шкала. Передайте в график сами значения bright.'
assert 'match' in checks, 'На рисунке нужен весь ряд: 61 пара от 07:00 до 22:00. Сверьте значения и подписи времени, включая спад в 18:00. Для числовых позиций подпишите ось временем.'
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
ev = D0['time'] >= '18:00'; t = D0['y']
p = _np.asarray(need('pred_norm'))
assert p.shape == t.shape, f'pred_norm.shape = {p.shape}, а нужно {t.shape}: по ответу на каждый кадр дня.'
_st = lambda q: (round(float((q == t)[~ev].mean()), 3), round(float((q == t)[ev].mean()), 3),
                 round(float(((q == 0) & (t == 0) & ev).sum() / max(((q == 0) & ev).sum(), 1)), 3))
_expected = _RF(100,random_state=0).fit(nz(d0['X']/255),d0['y']).predict(nz(D0['X']/255))
assert _np.array_equal(p,_expected), 'pred_norm: проверяется каждый прогноз на своём кадре, сохранения общих accuracy недостаточно.'
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
Днём точность даже чуть выросла (около 0.96), вечером — около 0.86 вместо 0.23. Для оповещений главное: вечером модель находит все пустые ячейки, а около 8 % её ответов «пусто» — ложные (круассан в тусклом свете иногда принимает за пустой поднос). Виды выпечки вечером по-прежнему путаются чаще, чем днём: свет меняет не только общую яркость, но и контраст. Если вечерние ошибки обходятся дорого, можно оценить пилот: например, узнать цену разметки 100 вечерних кадров, добавить их в обучение и на других вечерних сменах сравнить полноту пустой ячейки и стоимость вызовов со старой моделью. Измеренный здесь эффект нормировки не даёт прогноза выигрыша от новой разметки.

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
# ответы нормированного леса из шага 3 — заранее посчитаны тем же кодом, чтобы не обучать лес при каждом запуске:
# RandomForestClassifier(100, random_state=0).fit(normalize(d["X"] / 255), d["y"]).predict(normalize(D["X"] / 255))
pred = np.array(list(
    "1101222213331111222233331111222233331111222233331111222233331"
    "1112222333311112222333311312222333311112222333311312222113311"
    "1122203303101122203300101122203300101122203300100122203300100"
    "1122033001000202033011000202033001000202033001000102033001000"
    "2020300030002020300010002020300010002020300013112222333311113"
    "2223333111122223333311122223333111122223333111122223333111122"
    "2233331111222203331111220203331111220203330311220203330111220"
    "2013301102202033300100202033301100202033301101202033311112222"
    "3333111122223333110122223333113122223313100123213333131112323"
    "3030101222030030101232030031100223030033101122030031001221030"
    "0010032220300010002320300030032220300000012120300000013220300"
    "0000122200000000322303000000122103000000322000000000022000000"
), dtype=int)
_ref_pred = pred.copy()

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
D0 = _np.load('showcase_day.npz'); p = _ref_pred
pr = _np.array(['круассан'] * 4 + ['маффин'] * 4 + ['печенье'] * 4)
df0 = _pd.DataFrame({'time': D0['time'], 'slot': D0['slot'], 'true': D0['y'], 'pred': p}); df0['product'] = pr[df0['slot']]
g = need('df', _pd.DataFrame)
assert {'time', 'slot', 'product', 'true', 'pred'} <= set(g.columns), f'Колонки df: {list(g.columns)}.'
assert g['product'].isin(['круассан','маффин','печенье']).all(), 'product: название товара по ключу slot.'
m = df0[df0['time'] < '13:00']
w = _pd.DataFrame({'модель': (m['pred'] == 0).groupby(m['product']).sum() * 0.25, 'факт': (m['true'] == 0).groupby(m['product']).sum() * 0.25})
e = need('empty_hours', _pd.DataFrame)
assert list(e.columns) == ['модель', 'факт'], f'Столбцы: {list(e.columns)}.'
assert ((e.loc[w.index] - w).abs() < 1e-9).all().all(), f'empty_hours:\n{e}\nа нужно\n{w}'
assert not g.duplicated(['time','slot']).any(), 'Одна пара(time,slot) — один кадр.'
assert set(map(tuple,g[['time','slot']].values))==set(map(tuple,df0[['time','slot']].values)), 'Набор кадров не совпадает.'
_actual=g.set_index(['time','slot']).reindex(df0.set_index(['time','slot']).index)
_expected=df0.set_index(['time','slot'])
for _col in ('product','true','pred'):
    assert _actual[_col].tolist()==_expected[_col].tolist(), f'{_col}: значение не соответствует паре(time,slot).'

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
Модель оценивает простой почти точно: по каждому товару она ошибается не больше чем на четверть часа, причём в разные стороны (круассаны — 8.0 часа против 7.75, печенье — 7.5 против 7.75, маффины совпали), а в сумме за утро — точно. За утро ячейки суммарно простояли пустыми около 21 часа — в среднем почти два часа на ячейку. Чтобы оценить потерянную выручку, нужен спрос в эти часы и сведения о заменах товара.

## task: alerts | Шаг 5. Как выбрать правило оповещений | base

**1. Найдите события.** Камера прислала четыре строки в таком порядке. Класс 0 означает пустую ячейку.

| Время | Ячейка | Прогноз |
|---|---:|---:|
| 09:30 | 4 | 0 |
| 09:15 | 8 | 0 |
| 09:00 | 4 | 0 |
| 09:30 | 8 | 0 |

Выпишите пары (время, ячейка), в которых при k=2 загорится сигнал. Для какой ячейки пропущен снимок? Пропуск означает, что состояние неизвестно. Возобновите счётчик при следующем пустом кадре именно этой ячейки.

Напишите `alert_table(frame, k=2)`. Вход `frame` — длинный журнал с одной строкой на пару `time, slot` и классом `pred`. Восстановите сетку через каждые 15 минут. Верните `signals` — широкую булеву таблицу: в индексе время, в столбцах номера ячеек. `True` ставьте один раз на k-м подряд кадре с прогнозом 0. Для первого дня `df` сохраните также широкие таблицы `P` и `T` с флагами пустоты по прогнозу и по факту.

Для **отчёта при k=2** нужны `alerts` — короткий список срабатываний с двумя колонками `time, slot`, `n_alerts` — число сигналов, `n_correct` — число сигналов в действительно пустой ячейке и `n_missed` — число пропущенных эпизодов. В коротком списке по строке на вызов. Для оценки задержки и пропусков нужны также *все моменты без вызова*.

**2. Выберите правило на первом дне.** Функция `episode_metrics(frame, signals)` принимает журнал с фактом и широкую булеву таблицу всех решений. Например, для одной ячейки с пустыми кадрами в 11:00 и 11:15 при k=2 у столбца этой ячейки значения `False, True`. В списке `alerts` останется только пара с 11:15. Для расчёта передайте всю таблицу: `signals = alert_table(df, k)`, затем `metrics = episode_metrics(df, signals)`.

Сравните k=1, 2 и 3. Управляющая заранее оценила ложный вызов в 120 ₽, пропуск эпизода в 300 ₽, повторный вызов в 30 ₽, минуту ожидания до первого сигнала в обнаруженном эпизоде в 1 ₽. Отсчёт начинается с первого фактически пустого кадра. В таблице `policy_table` с индексом k сохраните все поля функции: `n_alerts, false, missed, repeated, delay_minutes, delay_total`, а в столбце `cost` — стоимость. В неё входит **сумма** минут ожидания `delay_total`. Средняя задержка `delay_minutes` описывает один обнаруженный эпизод. Сохраните в `chosen_k` вариант с минимальной стоимостью, при равенстве возьмите меньшее k. Запишите в рабочие заметки нормировку, параметры леса, цены и свой выбор.

**3. Проверьте записанное правило.** Теперь вызовите `predict_next_day()`: функция применит тот же лес к другому дню. Сохраните результат в `next_df` с колонками `time, slot, true, pred`. На этих прогнозах примените `chosen_k` и передайте широкую таблицу в ту же `episode_metrics`. Её словарь сохраните в `next_metrics`. В письме сравните число пропусков, ложных вызовов и задержки двух дней. Назовите один исход, важный для пекаря. После сдачи шага в разборе можно скачать локальный скрипт и сравнить два извлекателя из урока «Перенос обучения» на этой же смене.

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
# Эти же веса используются для обоих дней.
camera_model = RandomForestClassifier(n_estimators=100, random_state=0)
camera_model.fit(normalize(d["X"] / 255), d["y"])
pred = camera_model.predict(normalize(D["X"] / 255))
product = np.array(["круассан"] * 4 + ["маффин"] * 4 + ["печенье"] * 4)
df = pd.DataFrame({"time": D["time"], "slot": D["slot"], "true": D["y"], "pred": pred})
df["product"] = product[df["slot"]]

def episode_metrics(frame, signals):
    """Оценить истинные эпизоды и сигналы по одному журналу кадров."""
    if not isinstance(signals, pd.DataFrame) or {"time", "slot"}.issubset(signals.columns):
        raise ValueError(
            "Второй аргумент episode_metrics — широкая таблица сигналов: строки — время, "
            "столбцы — номера ячеек, значения — True/False. Передайте alert_table(frame, k). "
            "Список alerts с колонками time, slot оставьте для отчёта."
        )
    signals = signals.sort_index()
    truth = frame.pivot(index="time", columns="slot", values="true").eq(0)
    truth = truth.reindex(index=signals.index, columns=signals.columns, fill_value=False)
    missed, repeated = 0, 0
    delays = []
    for slot in truth.columns:
        empty = truth[slot]
        beginnings = empty & ~empty.shift(fill_value=False)
        episode_id = beginnings.cumsum()
        for _, episode in empty[empty].groupby(episode_id[empty]):
            times = episode.index
            hits = signals.loc[times, slot]
            positions = np.flatnonzero(hits)
            if len(positions) == 0:
                missed += 1
            else:
                repeated += len(positions) - 1
                delays.append(int(positions[0]) * 15)
    return {
        "n_alerts": int(signals.to_numpy().sum()),
        "false": int((signals & ~truth).to_numpy().sum()),
        "missed": missed,
        "repeated": repeated,
        "delay_minutes": float(np.mean(delays)) if delays else None,
        "delay_total": sum(delays),
    }


def predict_next_day():
    day = np.load("showcase_day_next.npz")
    return pd.DataFrame({
        "time": day["time"], "slot": day["slot"], "true": day["y"],
        "pred": camera_model.predict(normalize(day["X"] / 255)),
    })

```

### starter
```python
import numpy as np
import pandas as pd

P = df.pivot(index="time", columns="slot", values="pred") == 0
T = df.pivot(index="time", columns="slot", values="true") == 0

def alert_table(frame, k=2):
    empty = frame.pivot(index="time", columns="slot", values="pred").eq(0)
    ticks = pd.date_range("2000-01-01 " + empty.index.min(),
                          "2000-01-01 " + empty.index.max(), freq="15min")
    empty = empty.reindex(ticks.strftime("%H:%M"), fill_value=False)
    empty.index.name = "time"
    # Какие из последних k кадров были пусты? Горел ли сигнал серии кадром раньше?
    ...

# Для каждого k: episode_metrics(df, alert_table(df, k)). Посчитайте стоимость.
# После выбора вызовите predict_next_day(), затем ту же пару функций.
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
_rule=need('alert_table')
_gap=_pd.DataFrame(dict(time=['11:00','11:30'],slot=[0,0],pred=[0,0]))
assert not _rule(_gap).any().any(), 'Пропущенный11:15: кадры11:00 и11:30 не соседние.'
_pair=_pd.DataFrame(dict(time=['11:00','11:15'],slot=[0,0],pred=[0,0]))
assert bool(_rule(_pair).loc['11:15',0]), 'Два соседних пустых кадра подтверждают сигнал.'
for _name, _expected_table in [('P', P0), ('T', T0)]:
    _given = need(_name, _pd.DataFrame)
    assert _given.index.is_unique and _given.columns.is_unique, f'{_name}: каждый time и slot должен встречаться на своей оси ровно один раз.'
    assert set(_given.index) == set(_expected_table.index), f'{_name}: сохраните все временные ключи первого дня без лишних и пропущенных.'
    assert set(_given.columns) == set(_expected_table.columns), f'{_name}: сохраните все ключи slot первого дня без лишних и пропущенных.'
    _aligned = _given.reindex(index=_expected_table.index, columns=_expected_table.columns)
    assert _np.array_equal(_aligned.to_numpy(), _expected_table.to_numpy()), f'{_name}: пустота (класс 0) должна соответствовать своей паре (time, slot). Переставлять целые строки и столбцы можно, только подписи — нельзя.'

from sklearn.ensemble import RandomForestClassifier as _RF
_nd=_np.load('showcase_day_next.npz');_base=_np.load('showcase.npz')
def _norm(z):
    z=z.reshape(len(z),-1);return (z-z.mean(1,keepdims=True))/z.std(1,keepdims=True)
_forest = _RF(100, random_state=0).fit(_norm(_base["X"] / 255), _base["y"])
_predict = _forest.predict(_norm(_nd["X"] / 255))
_frame=_pd.DataFrame(dict(time=_nd['time'],slot=_nd['slot'],true=_nd['y'],pred=_predict))

def _reference(frame, k):
    pivot = frame.pivot(index="time", columns="slot", values="pred")
    ticks = _pd.date_range("2000-01-01 " + pivot.index.min(),
                           "2000-01-01 " + pivot.index.max(), freq="15min")
    pivot = pivot.reindex(ticks.strftime("%H:%M"))
    signals = _pd.DataFrame(False, index=pivot.index, columns=pivot.columns)
    for slot in pivot:
        length = 0
        for time, label in pivot[slot].items():
            length = length + 1 if label == 0 else 0
            signals.loc[time, slot] = length == k

    truth = frame.pivot(index="time", columns="slot", values="true").eq(0)
    truth = truth.reindex(signals.index, fill_value=False)
    missed, repeated, delays = 0, 0, []
    for slot in truth:
        run = []
        for i, empty in enumerate(list(truth[slot]) + [False]):
            if empty:
                run.append(i)
            elif run:
                positions = [j for j in run if signals[slot].iloc[j]]
                if positions:
                    repeated += len(positions) - 1
                    delays.append(15 * (positions[0] - run[0]))
                else:
                    missed += 1
                run = []
    metrics = dict(n_alerts=int(signals.to_numpy().sum()),
                   false=int((signals & ~truth).to_numpy().sum()),
                   missed=missed, repeated=repeated, delay_total=sum(delays),
                   delay_minutes=float(_np.mean(delays)) if delays else None)
    return signals, metrics


_first = _np.load("showcase_day.npz")
_day = _pd.DataFrame(dict(time=_first["time"], slot=_first["slot"], true=_first["y"],
                          pred=_forest.predict(_norm(_first["X"] / 255))))
_table = need("policy_table", _pd.DataFrame)
assert _table.index.is_unique and set(_table.index) == {1, 2, 3}, "Сравните на первом дне все три k."
_costs = {}
for _k in (1, 2, 3):
    _signals, _m = _reference(_day, _k)
    _s = _rule(_day.sample(frac=1, random_state=1), _k)
    assert _s.sort_index().sort_index(axis=1).equals(_signals.sort_index().sort_index(axis=1)), f"Для k={_k} проверьте момент первого сигнала серии."
    _costs[_k] = 120 * _m["false"] + 300 * _m["missed"] + 30 * _m["repeated"] + _m["delay_total"]
    for _key, _value in {**_m, "cost": _costs[_k]}.items():
        assert close(_table.loc[_k, _key], _value), f"policy_table: первый день, k={_k}, столбец {_key}."
_best = min(_costs, key=lambda k: (_costs[k], k))
assert need("chosen_k") == _best, "Выберите k по минимальной стоимости на первом дне."
_actual = need("next_df").set_index(["time", "slot"]).sort_index()
_expected = _frame.set_index(["time", "slot"]).sort_index()
assert _actual.equals(_expected), "Сверьте исходные кадры, метки и прогноз замороженного леса следующего дня."
assert need("next_metrics", dict) == _reference(_frame, _best)[1], "Примените замороженный k к следующему дню и заново посчитайте эпизоды."
```

### hint
Для k последовательных пустых кадров объедините `empty` и её сдвиги на 1…k−1 через `&`. Подтверждение сохраняется всю длинную серию; первый сигнал — переход от отсутствия подтверждения к его появлению.

### hint
Если два обнаруженных эпизода ждали 0 и 30 минут, управляющая оплатит 30 минут всего. Средняя задержка здесь 15 минут. В строку для каждого k добавьте `cost = 120 * false + 300 * missed + 30 * repeated + delay_total`. Для `n_correct` вычтите ложные сигналы из всех. Начните сравнение с k=1: один пустой кадр вызывает сигнал сразу.

### solution
```python
import pandas as pd

def alert_table(frame, k=2):
    empty = frame.pivot(index="time", columns="slot", values="pred").eq(0)
    ticks = pd.date_range("2000-01-01 " + empty.index.min(),
                          "2000-01-01 " + empty.index.max(), freq="15min")
    empty = empty.reindex(ticks.strftime("%H:%M"), fill_value=False)
    empty.index.name = "time"
    confirmed = empty.copy()
    for lag in range(1, k):
        confirmed &= empty.shift(lag, fill_value=False)
    return confirmed & ~confirmed.shift(fill_value=False)


P = df.pivot(index="time", columns="slot", values="pred").eq(0)
T = df.pivot(index="time", columns="slot", values="true").eq(0)
signals = alert_table(df)
flags = signals.stack()
alerts = flags[flags].reset_index()[["time", "slot"]]
rows = {}
for k in (1, 2, 3):
    m = episode_metrics(df, alert_table(df, k))
    m["cost"] = 120 * m["false"] + 300 * m["missed"] + 30 * m["repeated"] + m["delay_total"]
    rows[k] = m

policy_table = pd.DataFrame.from_dict(rows, orient="index")
n_alerts = rows[2]["n_alerts"]
n_correct = n_alerts - rows[2]["false"]
n_missed = rows[2]["missed"]
chosen_k = int(policy_table["cost"].idxmin())
next_df = predict_next_day()
next_metrics = episode_metrics(next_df, alert_table(next_df, chosen_k))
print(policy_table, chosen_k, next_metrics, sep="\n")
```

### explain
Первый пустой кадр даёт быстрый сигнал, но одиночные ошибки распознавания вызывают лишние походы к витрине. Ожидание третьего кадра позволяет пропустить короткую пустоту. В сравнение включены стоимость этих исходов и суммарное ожидание пекаря. На следующем дне возможны пропуски даже у правила, которое нашло все эпизоды первого дня.

### Локальный опыт после проверки правила

Вы уже применили выбранные модель и k к другой смене. Теперь вернитесь к вопросу о переносе признаков: какой извлекатель точнее при одинаковом бюджете разметки? Для обоих использованы одни ID обучения, StandardScaler и логистическая регрессия. Обычный свет — те же 500 отложенных вырезок, другой вечер — все 204 снимка следующего дня с 18:00.

| Фото на класс | Фильтры, обычный свет | ResNet-18, обычный свет | Фильтры, другой вечер | ResNet-18, другой вечер |
|---|---:|---:|---:|---:|
| 10 | 0,752 | 0,898 | 0,324 | 0,716 |
| 25 | 0,872 | 0,958 | 0,520 | 0,716 |
| 50 | 0,908 | 0,970 | 0,711 | 0,691 |
| 100 | 0,922 | 0,974 | 0,779 | 0,725 |
| 200 | 0,940 | 0,982 | 0,804 | 0,765 |

При 200 фото на класс ResNet-18 лидирует на дневных вырезках, случайные фильтры — на другом вечере. Эти данные относятся к двум синтетическим выборкам. Для следующей камеры заранее выберите нужную метрику и бюджет, затем проверьте решение на новых сменах.

Для воспроизведения скачайте [скрипт сравнения](../notebooks/compare_showcase_features.py), [обучающие кадры](../data/showcase.npz) и [контрольный день](../data/showcase_day_next.npz). Положите оба NPZ в папку `data` рядом со скриптом. В окружении с PyTorch, torchvision, SciPy, Pillow и scikit-learn выполните `python compare_showcase_features.py --data data`. При первом запуске torchvision загружает веса ResNet-18.

## task: restock | Шаг 6. Когда допекать | star

По фактическим данным (`T` и `product` — в заготовке) найдите для каждого товара `half_empty` — первое время `t`, когда в момент `t` пусты не меньше 2 из 4 ячеек товара (Series с индексом-товаром). Посчитайте `observed_empty_hours` — сколько часов пустых ячеек (по факту, 0.25 ч за кадр) приходится на интервал 11:00–12:45 включительно: это **наблюдаемый простой** на двухчасовом интервале, а не измеренная экономия от переноса партии. И `observed_by_product` — то же по товарам (Series).

В `showcase_inventory.npz` доступны начальный запас по ячейкам `initial`, спрос на каждом четвертьчасовом шаге `demand` и две партии по ячейкам `refill`. В момент пополнения положите соответствующую партию только в пустые ячейки, затем вычтите спрос до минимума ноль и отметьте пустые ячейки. Сравните исходные 13:00 и 17:00, перенос первой партии на 11:00 и дополнительную копию первой партии в 11:00 при сохранении обеих исходных. Сдайте таблицу `schedule_scenarios` со строками `исходный`, `перенос`, `добавочная` и столбцами `morning` [11:00, 13:00), `afternoon` [13:00, 17:00), `whole_day` [07:00, 22:00). В каждой ячейке таблицы — сумма четвертьчасов пустоты по всем ячейкам витрины, переведённая в ячейко-часы. Для письма сначала запишите наблюдение по камере, затем результат расчёта за целый день при заданном спросе. Какие ещё сведения понадобятся, чтобы оценить прибыль?

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
assert close(need('observed_empty_hours'), (m['true'] == 0).sum() * 0.25), f'observed_empty_hours = {need("observed_empty_hours")}.'
sb = (m['true'] == 0).groupby(m['product']).sum() * 0.25
gs = need('observed_by_product', _pd.Series)
assert all(close(gs[p], sb[p]) for p in sb.index), f'observed_by_product:\n{gs}'
_tape=_np.load('showcase_inventory.npz')
_scenarios=need('schedule_scenarios',_pd.DataFrame)
for _name,_batches in [('исходный',{780:0,1020:1}),('перенос',{660:0,1020:1}),('добавочная',{660:0,780:0,1020:1})]:
    _stock=_tape['initial'].copy();_empty=[]
    for _step,_demand in enumerate(_tape['demand']):
        _minute=420+15*_step
        if _minute in _batches:_stock=_np.where(_stock==0,_tape['refill'][_batches[_minute]],_stock)
        _stock=_np.maximum(_stock-_demand,0);_empty.append(_stock==0)
    _empty=_np.array(_empty)[:60]
    for _key,_value in dict(morning=_empty[16:24].sum()*.25,afternoon=_empty[24:40].sum()*.25,whole_day=_empty.sum()*.25).items():
        assert close(_scenarios.loc[_name,_key],_value), f'Сценарий «{_name}», интервал {dict(morning="[11:00, 13:00)", afternoon="[13:00, 17:00)", whole_day="[07:00, 22:00)")[_key]} ({_key}): посчитайте пустоту в ячейко-часах после пополнения и вычитания спроса — 0.25 часа за пустую ячейку на каждом четвертьчасовом шаге. Это сценарный расчёт, а не измеренная экономия.'

```

### hint
`T` — таблица «время × ячейка». Чтобы сгруппировать ячейки по товару, транспонируйте её (`T.T` — строки становятся ячейками), сгруппируйте и транспонируйте обратно.

### hint
Доля пустых ячеек товара по времени: `T.T.groupby(product).mean().T` — таблица «время × товар». Первое время, где доля ≥ 0.5, — `share.index[(share[p] >= 0.5).values][0]`.

### hint
Простой между 11:00 и 13:00 по наблюдениям: `m = df[(df["time"] >= "11:00") & (df["time"] < "13:00")]`, затем `(m["true"] == 0).sum() * 0.25`. Для каждого сценария начните с копии того же `initial`. На каждом шаге сначала пополните только пустые ячейки, если по расписанию пришла партия. Затем вычтите спрос, ограничьте остаток нулём и отметьте пустоту после спроса. Один такой четвертьчас в одной ячейке даёт 0,25 ячейко-часа. Последний снимок в 22:00 завершает дневной интервал.

### solution
```python
import numpy as np
import pandas as pd

share = T.T.groupby(product).mean().T
half_empty = pd.Series({p: share.index[(share[p] >= 0.5).values][0] for p in share.columns})

m = df[(df["time"] >= "11:00") & (df["time"] < "13:00")]
observed_empty_hours = (m["true"] == 0).sum() * 0.25
observed_by_product = (m["true"] == 0).groupby(m["product"]).sum() * 0.25
print(half_empty, observed_empty_hours, observed_by_product, sep="\n\n")
_tape=np.load('showcase_inventory.npz')
def stock_scenario(batches):
    stock=_tape['initial'].copy();observations=[]
    for step,demand in enumerate(_tape['demand']):
        minute=7*60+step*15
        if minute in batches:
            stock=np.where(stock==0,_tape['refill'][batches[minute]],stock)
        stock=np.maximum(stock-demand,0)
        observations.append(stock==0)
    empty=np.asarray(observations)[:60] # [07:00,22:00), not an extra interval at22:00
    return dict(morning=float(empty[16:24].sum()*.25),afternoon=float(empty[24:40].sum()*.25),whole_day=float(empty.sum()*.25))
schedule_scenarios=pd.DataFrame({
    'исходный':stock_scenario({13*60:0,17*60:1}),
    'перенос':stock_scenario({11*60:0,17*60:1}),
    'добавочная':stock_scenario({11*60:0,13*60:0,17*60:1}),
}).T

```

### explain
К 11:00 половина ячеек каждого товара уже пуста (печенье — с 9:45), а допекают только в 13:00. Между 11:00 и 13:00 витрина набирает 15 ячейко-часов наблюдаемой пустоты — больше двух третей утреннего простоя. С 13:00 до 17:00 набирается 7,5 ячейко-часа пустоты. Половина ячеек круассанов опустела к 16:00, маффинов — к 16:15. Во всех трёх сценариях второе пополнение назначено на 17:00. Чтобы оценить другое время второй партии, добавьте сценарий с таким временем при том же спросе и сравните весь день.

## Итог для управляющей KZN-1

Пустая ячейка не означает отсутствие товара во всех ячейках и не измеряет потерю продажи. Для решения о партии сравните **весь день** в двух сценариях: перенос единственной партии с 13:00 на 11:00 и дополнительная партия в 11:00 с сохранением 13:00. При переносе утренний простой может снизиться, но запас кончится раньше и суммарный дневной простой увеличится. Нужны размер партий, остатки, спрос, время повторного опустошения, производственные ограничения и списания. Число 15 ячейко-часов нельзя назвать экономией без этих допущений.


> **Камера над витриной: один размеченный день, 732 кадра ячеек.**
>
> 1. **Модель распознаёт ячейку днём в 96 % случаев, вечером — в 86 %.** Первая версия вечером не находила пустые ячейки совсем: в 18:00 включается другой свет, и кадры становятся на треть темнее. Исправлено нормировкой яркости каждого кадра. Предлагаю оценить небольшой пилот, например разметку 100 новых вечерних снимков. До заказа узнаем стоимость съёмки и разметки. Затем на других вечерних сменах сравним полноту пустой ячейки и стоимость ложных вызовов, пропусков и задержки до и после обучения. Продолжим разметку, если выигрыш покроет расходы.
> 2. **Оповещения.** Назовите выбранное число кадров подряд, затраты на первом дне и исходы на другом. Укажите число пропущенных эпизодов и задержку относительно первого пустого кадра.
> 3. **Допекание:** к 11:00 половина ячеек каждого товара уже пустует, печенье — с 9:45. С 11:00 до 13:00 витрина набирает 15 ячейко-часов наблюдаемой пустоты. С 13:00 до 17:00 наблюдалось 7,5 ячейко-часа пустоты. Вторую партию в этом сравнении оставляли на 17:00. В симуляции перенос партии на 11:00 уменьшил утренний простой с 15 до 5 ячейко-часов, но увеличил простой за день с 49,75 до 52,25. Дополнительная партия дала 43,75 за день. До изменения расписания оценим себестоимость партии и списания. Если пробный выпуск оправдан, за 2–3 недели сравним продажи, списания и простой за весь день с сопоставимыми сменами.

::: tip
В работе модель будет видеть кадры, которых не было ни в обучении, ни в проверочном дне: новую выпечку, другую раскладку, солнце в окне. Раз в месяц размечайте день вручную и пересчитывайте точность, как в шаге 1, — это мониторинг из главы 8.
:::
