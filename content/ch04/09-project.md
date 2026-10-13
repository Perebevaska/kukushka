---
title: "Проект: почему доставка опаздывает"
lead: "Финал главы. Руководитель доставки просит разобраться: почему опаздываем, где и насколько, и что с этим делать. Проходим весь путь исследования — от очистки до выводов с цифрами и функции, которая пересчитает отчёт за любой период."
files: [deliveries.csv]
recap:
  - "Исследование начинается с вопроса и метрики, а заканчивается выводами с цифрами, размерами групп и ограничениями."
  - "Сначала масштаб проблемы (как часто и насколько), потом поиск факторов, потом проверка смешения."
  - "Каждую найденную связь проверяйте вторым способом: срез внутри групп, другой разрез времени."
  - "Рекомендации формулируйте как варианты с цифрами: решение принимает бизнес."
  - "Отчёт — функция от сырых данных: пересчитывается за любой период."
  - "Свою закономерность доказывают так же, как заданную: группа условием, размер группы, доля в группе против доли вне её, проверка смешения, ограничение."
  - "Главный вывод с цифрой масштаба — в начало отчёта, сразу после цели; журнал очистки — ниже, в предобработке."
  - "Проект сдаётся блокнотом по шаблону: цель и главное → данные → предобработка → анализ → выводы; после каждого раздела — markdown-вывод; перед сдачей — Restart & Run All и `check_notebook.py`."
---

## Задача

> С осени мы возим кофе курьерами, и гости жалуются на опоздания. Разберитесь: насколько всё плохо, где и почему опаздываем и что можно сделать. Нужны цифры, а не ощущения.

Данные — `deliveries.csv`: все доставки за сентябрь–ноябрь.

## План

1. Очистить данные и записать, что убрали.
2. Масштаб: как часто и насколько опаздываем.
3. Какой признак сильнее всего связан с опозданиями.
4. Пешие курьеры и обещание: в чём причина, какое обещание реалистично и почему при обещании 45 минут пешие опаздывают ещё чаще.
5. Кофейня KZN-2: она медленнее сама по себе или из-за состава заказов.
6. Снег и динамика по неделям.
7. Что чувствует гость: оценки и опоздания.
8. **Ваш шаг:** две закономерности, которых нет в плане, — найти и доказать цифрами.
9. Отчёт одной функцией.
10. Собрать всё в блокнот-отчёт и сдать.

::: quiz
Отчёт «почему доставка опаздывает» для руководителя. Что поставить в начало?

- [x] Главный вывод одной-двумя фразами и цифру масштаба проблемы
  > Руководитель читает начало. Детали, графики и журнал очистки — ниже, для тех, кто хочет проверить.
- [ ] Журнал очистки данных
  > Он нужен для доверия к цифрам, но не первым: журнал стоит в разделе «Предобработка», после главного вывода. Руководитель заглянет в него, когда захочет проверить цифры.
- [ ] Описание всех столбцов таблицы
  > Это справочная информация, а не ответ на вопрос.
- [ ] Все графики подряд, выводы в конце
  > Без вывода в начале читатель сам не поймёт, на что смотреть.
:::

## Разберём вместе: журнал очистки как часть отчёта

Шаг 1 кажется технической мелочью. Но когда руководитель прочитает главный вывод, первым делом он спросит: «а вы ничего не выбросили?» Ответ на этот вопрос — журнал очистки. В отчёте он стоит не первым, а в разделе «Предобработка», но готовить его нужно сразу. Посчитаем заранее, что получится:

1. В выгрузке **1 877** доставок.
2. У **25** время не записано (`actual_min` пустой) — курьер не закрыл заказ в приложении.
3. У **11** время записано, но невозможное: 0 минут или больше 299 (сутки, «1440»).
4. Остаётся 1 877 − 25 − 11 = **1 841** доставка — 98 % выгрузки.

::: figure clean-journal
Журнал очистки шага 1 одной схемой: из 1 877 строк ушли 25 без времени и 11 с невозможным временем.
:::

Почему это важно записать: 36 удалённых строк — около 2 %, выводы от них не изменятся. Но если бы удалили 30 %, любой вывод «опаздываем в 24 % случаев» был бы под вопросом: а вдруг не закрытые заказы — как раз самые проблемные? Журнал очистки — это ответ на вопрос «а вы ничего не выбросили?» до того, как его зададут.

::: warn Типичные ошибки проекта
- **Очистка без журнала.** Читатель не знает, на каких данных выводы.
- **Средняя вместо медианы для времени.** Хвост долгих доставок тянет среднее вверх.
- **Вывод про кофейню без учёта состава.** KZN-2 может быть медленной из-за доли пеших курьеров, а не сама по себе.
- **Неполные недели в динамике.** Первая и последняя неделя — «провалы», которых не было.
:::

Начиная со второго шага, перед задачей курс сам готовит таблицу `ok` — доставки с временем 1–299 минут и столбцами `late`, `delay`, `hour`.

::: tip
Это повторение всей главы и уроков «Аномалии и проверка на здравый смысл» и «Очистка целиком: функция и проверки» из главы 3. В подсказках указано, на какой урок опирается шаг.
:::

## Шаг 8 — ваш: найдите две закономерности сами

В шагах 2–7 вопросы задаёт курс. В настоящей работе их никто не задаёт: руководитель ждёт, что аналитик сам заметит то, о чём не спрашивали. Поэтому в шаге 8 подсказок по содержанию нет — только правила игры.

**Что искать.** Группу доставок, где доля опозданий заметно отличается от остальных. Группу задаёте условием `query` по признакам `distance_km`, `items`, `amount`, `hour`, `created` (например, день недели — `created.dt.dayofweek`). Курьер, погода, кофейня и обещание подробно разобраны в шагах 4–6 — их можно добавлять в условие только вместе с одним из этих признаков.

`items` и `hour` вы уже видели в шаге 3, но только одной цифрой — разбросом. Здесь нужна конкретная группа с доказательством. Часы пик войдут в отчёт шага 9 сами, поэтому интереснее искать там, где план не смотрел совсем: расстояние, день недели.

**Чего не брать.** `actual_min`, `delay`, `late` — из них считается сама метрика, «закономерность» получится по определению. `rating` — следствие опоздания, а не причина.

**Когда находка засчитывается:**

1. в группе не меньше 50 доставок, и вне группы — тоже;
2. доля опозданий в группе отличается от доли вне группы хотя бы на 5 процентных пунктов;
3. у двух находок разные признаки. `amount` и `items` считаются **одним** признаком — «размер заказа»: чем больше позиций, тем больше сумма, корреляция 0.95. Группа `amount >= 1000` (291 доставка) включает 212 из 225 доставок группы `items >= 5` — по сути та же находка. Прежде чем брать два признака, проверьте, не связаны ли они: `ok[["amount", "items"]].corr()`;
4. вывод записан по четырём частям из урока «EDA по плану»: наблюдение, цифра, размер группы, ограничение.


::: figure own-pattern
Путь своей находки: группа условием → размер не меньше 50 в группе и вне её → перепад от 5 п.п. → проверка смешения → вывод из четырёх частей.
:::

**Как искать.** Пройдите признаки по одному: гистограмма, затем доля опозданий по корзинам (`pd.cut`) или по значениям. Нашли перепад — сформулируйте группу условием и посчитайте долю в группе и вне её. Потом спросите себя: не повторяет ли находка уже известное? Например, короткие расстояния — это в основном пешие курьеры; проверьте, держится ли эффект **внутри** типа курьера (урок «EDA по плану», раздел «Проверка смешения на наших данных»). Если нет — честно напишите это в ограничении.

::: note Что проверит курс
Проверка пересчитает каждую вашу группу по условию `query` и сверит размер и доли с тем, что вы записали. Содержание вывода проверить автоматически нельзя — его прочитает ревьюер вашего блокнота.
:::

## Сдайте проект блокнотом

Шаги в браузере проверяются по одному. Но руководителю нужен один документ, который открывается, перезапускается и читается сверху вниз, — блокнот-отчёт. Соберите в нём весь проект.

::: figure project-report-main
Разделы шаблона сверху вниз и самопроверка перед сдачей. Главный вывод стоит сразу после цели, журнал очистки — ниже, в предобработке.
:::

1. **Подготовьте папки и шаблон.** Шаблону нужна такая структура: блокнот лежит в папке `notebooks/`, а `deliveries.csv` — в папке `data/` рядом с ней. Тогда путь `DATA = Path('../data')` из первой ячейки шаблона сразу укажет на данные, и `pd.read_csv(DATA / "deliveries.csv")` заработает без правок.
   - **Если вы учитесь на сайте** и архива курса у вас нет: создайте папку проекта (например, `delivery/`, как в уроке про uv в главе 2), в ней — папки `notebooks/` и `data/`. Скачайте шаблон [project-template.ipynb](../notebooks/project-template.ipynb) в `notebooks/` и переименуйте, например, в `delivery_delays.ipynb`. Скачайте данные [deliveries.csv](../data/deliveries.csv) в `data/`.
   - **Если у вас есть архив курса** (папка, которую запускают файлами «Курс-Windows.bat» или «Курс.command»): нужная структура там уже есть. Положите шаблон в папку `site/notebooks` архива — `deliveries.csv` лежит в соседней `site/data`.
2. **Раздел «Цель»** — вопрос руководителя одной фразой, метрика (доля доставок позже обещанного) и сразу под ними абзац **«Главное»**: 2–3 фразы с цифрой масштаба и главной причиной. Например: «Опаздывает почти каждая четвёртая доставка (24.0 %). Главная причина — пешие курьеры с обещанием 30 минут: они опаздывают в 70 % таких доставок». Пишется этот абзац в конце работы, но стоит первым — его прочитают все.
3. **Разделы «Данные» и «Предобработка»** — загрузка и журнал очистки из шага 1 таблицей.
4. **Раздел «Анализ»** — по подразделу на каждый шаг 2–8: код, график с заголовком-выводом, под ним markdown-вывод с цифрами. Цифры в выводах — из переменных, а не переписанные руками.
5. **Раздел «Выводы и рекомендации»** — все находки по порядку важности, включая ваши две, затем варианты действий с цифрами и ограничения. Главное здесь можно повторить одной строкой.
6. **Самопроверка.** **Kernel → Restart Kernel and Run All Cells**, затем [check_notebook.py](../notebooks/check_notebook.py) — положите его рядом с блокнотом и запустите в терминале:

   ```sh
   uv run python check_notebook.py delivery_delays.ipynb
   ```

   Скрипт выполнит блокнот с чистого ядра и перечислит, что исправить: ошибки при запуске, абсолютные пути, закомментированный код, разделы без вывода. Запускайте, пока список не станет пустым. Если переменные названы как в шагах и у вас есть архив курса, `uv run python check_notebook.py delivery_delays.ipynb --project ch04/09-project --course ПАПКА_КУРСА` сверит и числа с эталонами шагов (`ПАПКА_КУРСА` — путь к архиву; если блокнот лежит внутри него, `--course` можно не писать). Без архива пропустите этот шаг: числа вы уже сверили в задачах на сайте.

::: note Сделайте в своём блокноте
1. Пройдите шаги 1–9 в браузере.
2. Перенесите решения в шаблон: один шаг — один подраздел, после каждого — вывод.
3. Перечитайте только markdown-ячейки: понятен ли из них весь отчёт без кода? Видны ли в начале главный вывод и цифра масштаба?
4. Restart & Run All и `check_notebook.py` — до чистого результата.
:::

## Практика

## task: clean | Шаг 1. Очистка и журнал | base

Загрузите `deliveries.csv` (`created` — датой) и оставьте доставки с временем от 1 до 299 минут в `ok`. Добавьте столбцы `late` (опоздание: факт больше обещанного), `delay` (факт минус обещанное) и `hour` (час заказа). Соберите журнал `log` — словарь:

- `"всего"` — строк в выгрузке;
- `"без времени"` — с пустым `actual_min`;
- `"невозможное время"` — с заполненным временем вне 1–299;
- `"осталось"` — строк в `ok`.

### starter
```python
import pandas as pd
```

### check
```python
import pandas as _pd
d = _pd.read_csv('deliveries.csv', parse_dates=['created'])
o = need('ok', _pd.DataFrame)
assert len(o) == d['actual_min'].between(1, 299).sum(), f'В ok {len(o)} строк — оставьте время 1–299.'
for c in ('late', 'delay', 'hour'):
    assert c in o.columns, f'В ok нет столбца {c}.'
assert (o['late'] == (o['actual_min'] > o['promised_min'])).all(), 'late — actual_min > promised_min.'
assert (o['hour'] == o['created'].dt.hour).all(), 'hour — час из created (created должен быть датой).'
want = {'всего': len(d), 'без времени': int(d['actual_min'].isna().sum()),
        'невозможное время': int((d['actual_min'].notna() & ~d['actual_min'].between(1, 299)).sum()),
        'осталось': int(d['actual_min'].between(1, 299).sum())}
got = {k: int(v) for k, v in dict(need('log')).items()}
assert got == want, f'log = {got}, а нужно {want}.'
```

### hint
Уроки «Аномалии и проверка на здравый смысл» и «Очистка целиком: функция и проверки» (глава 3): маска `d["actual_min"].between(1, 299)`; пропуски она тоже отбрасывает.

### hint
Невозможное время — заполненное, но вне диапазона: `d["actual_min"].notna() & ~d["actual_min"].between(1, 299)`.

### solution
```python
import pandas as pd
d = pd.read_csv("deliveries.csv", parse_dates=["created"])
ok = d[d["actual_min"].between(1, 299)].copy()
ok["late"] = ok["actual_min"] > ok["promised_min"]
ok["delay"] = ok["actual_min"] - ok["promised_min"]
ok["hour"] = ok["created"].dt.hour
log = {
    "всего": len(d),
    "без времени": d["actual_min"].isna().sum(),
    "невозможное время": (d["actual_min"].notna() & ~d["actual_min"].between(1, 299)).sum(),
    "осталось": len(ok),
}
log
```

### explain
Журнал: 1 877 строк, 25 без времени, 11 с невозможным временем, осталось 1 841. Удалено меньше 2 % — выводы на очищенных данных можно распространять на всю осень.

## task: scale | Шаг 2. Масштаб проблемы | base

Таблица `ok` уже готова (`late`, `delay`, `hour`). Сохраните:

- `late_pct` — долю опозданий, % (1 знак);
- `late_median` — медиану опоздания **среди опоздавших** доставок, мин;
- `p90_late` — квантиль 0.9 опоздания среди опоздавших.

Нарисуйте гистограмму `delay` от −40 до 40 минут с корзинами по 5 минут и линией на нуле.

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
# ok — доставки с правдоподобным временем, есть late, delay, hour
ok.head(3)
```

### check
```python
import pandas as _pd
o = _ref_ok()
assert close(need('late_pct'), round(o['late'].mean() * 100, 1)), f'late_pct = {need("late_pct")}.'
lt = o.loc[o['late'], 'delay']
assert close(need('late_median'), lt.median()), f'late_median = {need("late_median")}, а нужно {lt.median()} (только опоздавшие).'
assert close(need('p90_late'), lt.quantile(0.9)), f'p90_late = {need("p90_late")}.'
ax = ax_of()
assert len(ax.patches) == 16, 'Гистограмма: bins=16, range=(-40, 40).'
assert any(len(set(l.get_xdata())) == 1 and float(l.get_xdata()[0]) == 0 for l in ax.lines), 'Отметьте ноль: ax.axvline(0).'
```

### hint
Урок «Распределения и гистограммы»: квантили и гистограмма опоздания. Опоздавшие — `ok.loc[ok["late"], "delay"]`.

### hint
Медиана и квантиль 0.9 опоздания среди опоздавших — `late_delay.median()` и `late_delay.quantile(0.9)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
late_pct = round(ok["late"].mean() * 100, 1)
late_delay = ok.loc[ok["late"], "delay"]
late_median = late_delay.median()
p90_late = late_delay.quantile(0.9)

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.hist(ok["delay"], bins=16, range=(-40, 40), color="lightgray")
ax.axvline(0, color="tab:red")
ax.set_title(f"Опаздывает {late_pct} % доставок, обычно на {late_median:.0f} мин")
ax.set_xlabel("опоздание, мин")
```

### explain
Каждая четвёртая доставка опаздывает, но в основном ненадолго: половина опозданий — несколько минут. Длинный хвост — это редкие, но самые неприятные для гостя случаи. Обе цифры стоит дать в отчёте: «как часто» и «насколько».

## task: factors | Шаг 3. Где опаздывают | base

Сравните признаки `courier`, `weather`, `shop_id`, `items`, `hour` по разбросу доли опозданий между группами (только группы от 50 доставок), как в уроке «EDA по плану». Сохраните `ranking` (Series, процентные пункты, 1 знак, по убыванию) и `top_factor` — признак с наибольшим разбросом. Нарисуйте долю опозданий по `top_factor` столбцами по убыванию, с подписями значений.

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
```

### check
```python
import pandas as _pd
o = _ref_ok()
w = {}
for by in ['courier', 'weather', 'shop_id', 'items', 'hour']:
    g = o.groupby(by)['late'].agg(['mean', 'size'])
    g = g[g['size'] >= 50]
    w[by] = round((g['mean'].max() - g['mean'].min()) * 100, 1)
w = _pd.Series(w).sort_values(ascending=False)
r = need('ranking', _pd.Series)
assert all(close(r[k], w[k]) for k in w.index), f'ranking = {r.to_dict()}, а нужно {w.to_dict()}.'
assert need('top_factor') == w.index[0], f'top_factor = {need("top_factor")!r}.'
ax = ax_of()
h = [p.get_height() for p in ax.patches]
want = (o.groupby(w.index[0])['late'].mean() * 100).sort_values(ascending=False)
assert len(h) == len(want) and all(close(a, b) for a, b in zip(h, want.values)), 'Столбцы — доля опозданий (%) по главному признаку, по убыванию.'
assert len(ax.texts) == len(h), 'Подпишите значения: ax.bar_label(bars, fmt="%.1f").'
```

### hint
Урок «EDA по плану», задача «Какой признак важнее» — тот же цикл.

### hint
Для графика: `t = (ok.groupby(top_factor)["late"].mean() * 100).sort_values(ascending=False)`.

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
spread = {}
for by in ["courier", "weather", "shop_id", "items", "hour"]:
    g = ok.groupby(by)["late"].agg(["mean", "size"])
    g = g[g["size"] >= 50]
    spread[by] = round((g["mean"].max() - g["mean"].min()) * 100, 1)
ranking = pd.Series(spread).sort_values(ascending=False)
top_factor = ranking.index[0]

t = (ok.groupby(top_factor)["late"].mean() * 100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(5, 3))
bars = ax.bar(t.index, t.values, color=["tab:red"] + ["lightgray"] * (len(t) - 1))
ax.bar_label(bars, fmt="%.1f")
ax.set_ylabel("опозданий, %")
ax.set_title(f"Главный фактор — {top_factor}")
ranking
```

### explain
Тип курьера лидирует с огромным отрывом — разброс около 69 п.п., дальше позиции, час, погода и кофейня (13–22 п.п.). Подписи значений на столбцах превращают график в готовый слайд: «пешие опаздывают в 5–6 раз чаще вело и в 14 раз чаще машин».

## task: walkers | Шаг 4. Пешие курьеры и обещание | plus

Пешие курьеры опаздывают чаще всех. Проверим, в чём дело: в курьерах или в обещании.

1. Постройте `pv` — долю опозданий (%) по `promised_min` (строки) и `courier` (столбцы). Округлять не обязательно: проверка примет и точные значения, и округлённые до 1 знака.
2. Для пеших курьеров с обещанием 30 минут посчитайте `walk_p80` — квантиль 0.8 фактического времени: за сколько минут пешие доставляют 80 % заказов.
3. Сохраните `fair_promise` — это время, округлённое **вверх** до кратного 5 минут (например, 37 → 40). Это обещание, которое пешие выполняли бы в 80 % случаев.

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
import math
```

### check
```python
import pandas as _pd
o = _ref_ok()
pv = o.pivot_table(index='promised_min', columns='courier', values='late', aggfunc='mean') * 100
p = need('pv', _pd.DataFrame)
assert p.shape == pv.shape, f'Форма pv {p.shape}, а нужно {pv.shape}: строки — promised_min (30, 45, 60), столбцы — courier.'
_a, _b = p.fillna(-1).values.ravel(), pv.fillna(-1).values.ravel()
if all(close(a * 100, b, 0.051) for a, b in zip(_a, _b) if b >= 0):
    raise AssertionError('В pv доли от 0 до 1, а нужны проценты: умножьте на 100.')
assert all(close(a, b, 0.051) for a, b in zip(_a, _b)), 'Значения pv не совпадают. Нужна доля опозданий (aggfunc="mean" по late) × 100; строки — promised_min, столбцы — courier.'
w = o[(o['courier'] == 'пеший') & (o['promised_min'] == 30)]['actual_min'].quantile(0.8)
assert close(need('walk_p80'), w), f'walk_p80 = {need("walk_p80")}, а нужно {w}.'
assert need('fair_promise') == int(_m0.ceil(w / 5) * 5), f'fair_promise = {need("fair_promise")}, а нужно {int(_m0.ceil(w / 5) * 5)}.'
```

### hint
Урок «Срезы: сравниваем группы» — срез по двум признакам сводной таблицей. Для `walk_p80` сначала отберите пеших с обещанием 30 минут, потом возьмите квантиль 0.8 их `actual_min`.

### hint
`ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean") * 100`. Округление вверх до 5: `math.ceil(x / 5) * 5`.

### hint
```python static
pv = ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean") * 100
walk30 = ok[(ok["courier"] == "пеший") & (ok["promised_min"] == ...)]
walk_p80 = walk30["actual_min"].quantile(...)
fair_promise = math.ceil(walk_p80 / 5) * 5
```

### solution
```python
import pandas as pd
import math
pv = ok.pivot_table(index="promised_min", columns="courier", values="late", aggfunc="mean") * 100
walk30 = ok[(ok["courier"] == "пеший") & (ok["promised_min"] == 30)]
walk_p80 = walk30["actual_min"].quantile(0.8)
fair_promise = math.ceil(walk_p80 / 5) * 5
pv.round(1)
```

### explain
Пешие опаздывают при любом обещании, а вело и авто с теми же обещаниями — заметно реже. При обещании 30 минут опаздывают 69.7 % пеших доставок (317), а у вело — 24.4 %. Обещание рассчитано на скорость велосипеда: пешие доставляют 80 % таких заказов за 40 минут — это и есть реалистичное обещание.

Обратите внимание на строку 45 минут: у пеших там опозданий ещё больше — 89.5 % (86 доставок). Это не ошибка в таблице. Обещание зависит от расстояния: при 45 минутах медианное расстояние у пеших — 3 км, и везут они такие заказы около 60 минут (медиана 59.5). Пешком 3 км вовремя не довезти почти никогда.

Отсюда два рычага для бизнеса: обещать пешим реалистичное время (40 минут вместо 30) и не отдавать пешим заказы дальше 1.5 км — на таких расстояниях они опаздывают в 91.5 % доставок (106). Второй рычаг сам по себе проблему не решает: и до 1.5 км пешие опаздывают в 67.7 % доставок (297), там нужен первый. Как их сочетать, решает бизнес, а аналитик даёт цифры для обоих.

## task: kzn2 | Шаг 5. Кофейня KZN-2 | plus

KZN-2 опаздывает чаще остальных. Может, дело в составе курьеров или расстояниях? Сравните медиану фактического времени в KZN-2 и в остальных кофейнях **внутри каждого типа курьера**. Сохраните `kzn2_gap` — словарь «тип курьера → медиана KZN-2 минус медиана остальных, мин», и `same_distance` — словарь «тип курьера → медиана расстояния KZN-2 минус медиана остальных, км (1 знак)».

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
ok["kzn2"] = ok["shop_id"] == "KZN-2"
```

### check
```python
import pandas as _pd
o = _ref_ok()
o['kzn2'] = o['shop_id'] == 'KZN-2'
m = o.pivot_table(index='courier', columns='kzn2', values='actual_min', aggfunc='median')
k = o.pivot_table(index='courier', columns='kzn2', values='distance_km', aggfunc='median')
want = (m[True] - m[False]).to_dict()
wd = (k[True] - k[False]).round(1).to_dict()
got = dict(need('kzn2_gap'))
assert set(got) == set(want) and all(close(got[c], want[c]) for c in want), f'kzn2_gap = {got}, а нужно {want}.'
gd = dict(need('same_distance'))
assert set(gd) == set(wd) and all(close(gd[c], wd[c]) for c in wd), f'same_distance = {gd}, а нужно {wd}.'
```

### hint
Срез по двум признакам — урок «Срезы: сравниваем группы». Нужны две сводные таблицы с одинаковыми строками (тип курьера) и столбцами (`kzn2`): медиана времени и медиана расстояния. Ответ — разница столбцов `True` и `False`.

### hint
Время: `ok.pivot_table(index="courier", columns="kzn2", values="actual_min", aggfunc="median")`. Для `same_distance` — то же с `values="distance_km"`. Столбцы называются `True` и `False`.

### hint
```python static
m = ok.pivot_table(index="courier", columns="kzn2", values="actual_min", aggfunc="median")
k = ok.pivot_table(index="courier", columns="kzn2", values=..., aggfunc="median")
kzn2_gap = (m[True] - m[False]).to_dict()
same_distance = (k[True] - k[...]).round(1).to_dict()
```
Для вывода, в ответ не входит: состав курьеров — `pd.crosstab(ok["kzn2"], ok["courier"], normalize="index")`.

### solution
```python
import pandas as pd
ok["kzn2"] = ok["shop_id"] == "KZN-2"
m = ok.pivot_table(index="courier", columns="kzn2", values="actual_min", aggfunc="median")
k = ok.pivot_table(index="courier", columns="kzn2", values="distance_km", aggfunc="median")
kzn2_gap = (m[True] - m[False]).to_dict()
same_distance = (k[True] - k[False]).round(1).to_dict()
kzn2_gap
```

### explain
У всех типов курьеров KZN-2 медленнее: авто на 6 минут, вело на 4, пешие на 4.5. Расстояния при этом те же (разница 0.1 км или нуль), и состав курьеров тоже: и в KZN-2, и в остальных кофейнях 31 % авто, 47 % вело и 22 % пеших (`crosstab` из подсказки). Значит, дело не в составе и не в маршрутах, а в самой кофейне — скорее всего, в сборке заказа. Следующий шаг уже не для данных, а для людей: съездить и посмотреть, как собирают заказы, сколько бариста на смене в пик.

## task: weekly | Шаг 6. Снег и недели | plus

По полным неделям (без первой и последней, `resample("W")` по `created`) посчитайте долю опозданий (%) и долю доставок в снег (%). Сохраните таблицу `weeks` со столбцами `late_pct` и `snow_pct` (округлять не обязательно: проверка примет и точные значения, и округлённые до 1 знака), а в `r_weeks` — корреляцию этих двух столбцов (2 знака). Нарисуйте обе линии на одном графике с легендой.

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
import matplotlib.pyplot as plt
ok["snow"] = ok["weather"] == "снег"
```

### check
```python
import pandas as _pd
o = _ref_ok()
o['snow'] = o['weather'] == 'снег'
w = o.set_index('created').resample('W')[['late', 'snow']].mean().iloc[1:-1] * 100
t = need('weeks', _pd.DataFrame)
assert list(t.columns) == ['late_pct', 'snow_pct'], f'Столбцы: {list(t.columns)}.'
assert len(t) == len(w), f'Недель {len(t)}, а полных — {len(w)}: отбросьте первую и последнюю неделю (.iloc[1:-1]).'
if all(close(a * 100, b, 0.051) for a, b in zip(t['late_pct'], w['late'])):
    raise AssertionError('В weeks доли от 0 до 1, а нужны проценты: умножьте на 100.')
assert all(close(a, b, 0.051) for a, b in zip(t['late_pct'], w['late'])), 'late_pct не совпадает: доля опозданий за неделю × 100. Неделя — resample("W") по created.'
assert all(close(a, b, 0.051) for a, b in zip(t['snow_pct'], w['snow'])), 'snow_pct не совпадает: доля доставок в снег за неделю × 100.'
assert close(need('r_weeks'), round(w['late'].corr(w['snow']), 2)), f'r_weeks = {need("r_weeks")}.'
ax = ax_of()
assert len([l for l in ax.lines if not l.get_label().startswith('_')]) >= 2 and ax.get_legend() is not None, 'Две линии с легендой.'
```

### hint
Урок «Динамика во времени»: `resample` группирует по неделям, если дата — индекс. Среднее от `True/False` даёт долю. Первая и последняя неделя неполные — их отбрасывают.

### hint
`ok.set_index("created").resample("W")[["late", "snow"]].mean()`, полные недели — `.iloc[1:-1]`. Переименуйте столбцы: `weeks.columns = ["late_pct", "snow_pct"]`. График: `weeks.plot(ax=ax)`.

### hint
```python static
weeks = ok.set_index("created").resample("W")[["late", "snow"]].mean().iloc[...] * 100
weeks.columns = ["late_pct", "snow_pct"]
r_weeks = round(weeks["late_pct"].corr(weeks[...]), 2)
fig, ax = plt.subplots(figsize=(9, 3.5))
weeks.plot(ax=ax, marker="o")
```

### solution
```python
import pandas as pd
import matplotlib.pyplot as plt
ok["snow"] = ok["weather"] == "снег"
weeks = ok.set_index("created").resample("W")[["late", "snow"]].mean().iloc[1:-1] * 100
weeks.columns = ["late_pct", "snow_pct"]
r_weeks = round(weeks["late_pct"].corr(weeks["snow_pct"]), 2)

fig, ax = plt.subplots(figsize=(9, 3.5))
weeks.plot(ax=ax, marker="o")
ax.set_ylabel("%")
ax.set_title(f"Опоздания и снег по неделям, r = {r_weeks}")
```

### explain
Недель всего десяток, поэтому корреляцию по ним стоит воспринимать как подсказку, а не доказательство. Сильнее аргумент из урока «EDA по плану»: внутри каждого типа курьера в снег опаздывают чаще. Два независимых взгляда, указывающих в одну сторону, убедительнее одного.

## task: ratings | Шаг 7. Что чувствует гость | base

Сохраните `rating_on_time` — среднюю оценку доставок вовремя, `rating_late10` — среднюю оценку доставок с опозданием **больше 10 минут** (обе — 2 знака), и `low_share_late10` — долю оценок 3 и ниже среди доставок с опозданием больше 10 минут, % (1 знак).

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
```

### check
```python
import pandas as _pd
o = _ref_ok()
a = o.loc[~o['late'], 'rating'].mean()
b = o.loc[o['delay'] > 10, 'rating']
assert close(need('rating_on_time'), round(a, 2)), f'rating_on_time = {need("rating_on_time")}.'
assert close(need('rating_late10'), round(b.mean(), 2)), f'rating_late10 = {need("rating_late10")}.'
assert close(need('low_share_late10'), round((b.dropna() <= 3).mean() * 100, 1)), f'low_share_late10 = {need("low_share_late10")} — доля среди поставленных оценок (без пропусков).'
```

### hint
Маски: вовремя — `~ok["late"]`, сильно опоздали — `ok["delay"] > 10`.

### hint
Доля низких — среди поставленных оценок: сначала `dropna()`, потом `(r <= 3).mean()`.

### solution
```python
import pandas as pd
rating_on_time = round(ok.loc[~ok["late"], "rating"].mean(), 2)
r10 = ok.loc[ok["delay"] > 10, "rating"]
rating_late10 = round(r10.mean(), 2)
low_share_late10 = round((r10.dropna() <= 3).mean() * 100, 1)
```

### explain
Вовремя средняя оценка 4.77, при опоздании больше 10 минут — 2.80. Среди таких доставок 71 % оценок — тройка и ниже, а у доставок вовремя — всего 1 %. Гостю почти всё равно, привезли раньше или ровно в срок, но опоздание больше 10 минут почти гарантирует плохой отзыв.

## task: own | Шаг 8. Две закономерности сами | plus

Найдите две группы доставок, где доля опозданий отличается от остальных, по правилам из раздела «Шаг 8 — ваш» выше. Таблица `ok` готова (`late`, `delay`, `hour`). Запишите находки в `findings` — список из двух словарей:

- `"группа"` — условие для `ok.query(...)`, например `"amount < 500"`;
- `"n"` — сколько доставок в группе;
- `"late_pct"` — доля опозданий в группе, % (1 знак);
- `"остальные_pct"` — доля опозданий вне группы, % (1 знак);
- `"вывод"` — вывод по четырём частям: наблюдение, цифра, размер группы, ограничение.

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
ok = _ref_ok()
```

### starter
```python
import pandas as pd
# ok — доставки 1–299 минут: есть late, delay, hour
# Исследуйте признаки distance_km, items, amount, hour, created — найдите перепады.
# amount и items — один признак «размер заказа»: для двух находок возьмите разные.

findings = [
    {"группа": "...", "n": 0, "late_pct": 0.0, "остальные_pct": 0.0, "вывод": "..."},
    {"группа": "...", "n": 0, "late_pct": 0.0, "остальные_pct": 0.0, "вывод": "..."},
]
```

### check
```python
import re as _re
o = _ref_ok()
F = need('findings', list)
assert len(F) == 2, f'Находок {len(F)}, а нужно ровно две.'
allowed = {'distance_km', 'items', 'amount', 'hour', 'created'}
same = {'amount': 'items'}   # сумма и число позиций — один признак «размер заказа» (корреляция 0.95)
banned = {'actual_min', 'delay', 'late', 'rating'}
used, _raw = [], []
for i, f in enumerate(F, 1):
    for k in ('группа', 'n', 'late_pct', 'остальные_pct', 'вывод'):
        assert k in f, f'В находке {i} нет ключа «{k}».'
    q = str(f['группа'])
    words = set(_re.findall(r'[A-Za-z_]+', q))
    assert not (words & banned), f'Находка {i}: в условии {sorted(words & banned)} — из них считается сама метрика или её следствие. Ищите причины среди distance_km, items, amount, hour, created.'
    feats = words & allowed
    assert feats, f'Находка {i}: в условии нет нового признака — нужен хотя бы один из distance_km, items, amount, hour, created.'
    try:
        a = o.query(q)
    except Exception as e:
        raise AssertionError(f'Находка {i}: ok.query({q!r}) падает с ошибкой {type(e).__name__}. Проверьте условие в своём коде.')
    rest = o.drop(a.index)
    assert len(a) >= 50 and len(rest) >= 50, f'Находка {i}: в группе {len(a)} доставок, вне её {len(rest)} — нужно не меньше 50 и там, и там.'
    assert int(f['n']) == len(a), f'Находка {i}: n = {f["n"]}, а по условию {len(a)} доставок.'
    lp, rp = a['late'].mean() * 100, rest['late'].mean() * 100
    assert close(f['late_pct'], round(lp, 1), 0.051), f'Находка {i}: late_pct = {f["late_pct"]}, а по условию {lp:.1f}.'
    assert close(f['остальные_pct'], round(rp, 1), 0.051), f'Находка {i}: остальные_pct = {f["остальные_pct"]}, а вне группы {rp:.1f}.'
    assert abs(lp - rp) >= 5, f'Находка {i}: разница {abs(lp - rp):.1f} п.п. — меньше 5, это ещё не закономерность.'
    text = str(f['вывод'])
    assert len(text) >= 60 and _re.search(r'\d', text), f'Находка {i}: вывод слишком короткий или без цифр. Нужны наблюдение, цифра, размер группы и ограничение.'
    _raw.append(feats)
    used.append({same.get(x, x) for x in feats})
assert not (_raw[0] & _raw[1]), f'Обе находки используют {sorted(_raw[0] & _raw[1])}: возьмите для второй другой признак.'
assert not (used[0] & used[1]), 'Обе находки — про размер заказа: amount и items почти один признак (корреляция 0.95, большие заказы дороже). Для второй находки возьмите другой признак: distance_km, hour или created.'
```

### hint
Ищите перепады по признакам по очереди: для числовых — `ok.groupby(pd.cut(ok["distance_km"], [0, 1, 2, 3, 5, 15]))["late"].agg(["mean", "size"])`, для дня недели — `ok.groupby(ok["created"].dt.dayofweek)["late"].agg(["mean", "size"])` (0 — понедельник, 6 — воскресенье).

### hint
Нашли перепад — опишите группу условием и посчитайте: `a = ok.query(q)`, `rest = ok.drop(a.index)`, затем `len(a)`, `a["late"].mean() * 100`, `rest["late"].mean() * 100`. Удобно завернуть это в функцию.

### hint
Перед выводом проверьте смешение: `ok.assign(g=ok.index.isin(a.index)).pivot_table(index="courier", columns="g", values="late", aggfunc="mean")`. Если внутри курьеров разница исчезает, находка — это тип курьера под другим именем; напишите это в ограничении или ищите дальше.

### solution
```python
import pandas as pd

def describe(q):
    a = ok.query(q)
    rest = ok.drop(a.index)
    return len(a), round(a["late"].mean() * 100, 1), round(rest["late"].mean() * 100, 1)

findings = []
for q, about, limit in [
    ("created.dt.dayofweek == 5", "в субботу доставки",
     "Ограничение: суббот за осень 13, а день выбран после просмотра всех семи — разница может быть случайной, проверить на зиме."),
    ("items >= 5", "большие заказы (5–6 позиций)",
     "Ограничение: только осень; причину (сборка или дорога) данные не различают; amount >= 1000 даёт почти ту же группу."),
]:
    n, lp, rp = describe(q)
    findings.append({
        "группа": q, "n": n, "late_pct": lp, "остальные_pct": rp,
        "вывод": (f"{about.capitalize()} опаздывают в {lp} % случаев против {rp} % у остальных "
                  f"({n} и {len(ok) - n} доставок). Разница держится внутри каждого типа курьера. {limit}"),
    })

for f in findings:
    print(f["группа"], "→", f["вывод"])
```

### explain
Эталон нашёл две закономерности: одну там, куда план не смотрел совсем (день недели), другую — в признаке, который шаг 3 видел только одной цифрой разброса (число позиций).

1. **Суббота.** В субботу опаздывают реже: 18.6 % против 25.0 % (301 и 1 540 доставок). Разница держится внутри каждого типа курьера: у вело 9.8 % против 13.5 %, у пеших 64.6 % против 75.7 %. Ограничение важное: дней недели семь, и, перебрав все, «особенный» день легко найти случайно. Не случайна ли разница, научимся проверять в главе «Статистика и проверка гипотез».
2. **Большие заказы.** Заказы из 5–6 позиций опаздывают в 38.2 % случаев против 22.0 % (225 и 1 616 доставок), тоже внутри каждого типа курьера: у вело 26.3 % против 11.3 %. В шаге 3 число позиций было лишь цифрой разброса, здесь — конкретная группа с проверкой смешения. Группа `amount >= 1000` (37.8 % против 21.4 %) — та же находка: в неё попадают 212 из 225 больших заказов. Поэтому второй находкой она не засчитывается.

А вот соблазнительная находка «короткие доставки до 1.5 км (`distance_km < 1.5`) опаздывают в 52.4 % против 17.2 %» внутри типа курьера распадается: у вело и пеших короткие доставки опаздывают даже **реже**. Это просто пешие курьеры, которых ставят на короткие расстояния. Такую находку стоит записать в журнал как проверенную и отброшенную: это тоже результат.

## task: report | Шаг 9. Отчёт одной функцией | star

Напишите `delivery_report(raw)`: принимает **сырую** выгрузку (DataFrame с `created`-датой), сама чистит её (время 1–299) и возвращает словарь:

- `"late_pct"` — доля опозданий, % (1 знак);
- `"worst_courier"` — тип курьера с наибольшей долей опозданий;
- `"worst_shop"` — кофейня с наибольшей долей опозданий;
- `"peak_hours"` — отсортированный список часов, где доля опозданий больше 25 % (только часы, где не меньше 50 доставок);
- `"fair_promise"` — реалистичное обещание для пеших курьеров при обещании 30 минут (квантиль 0.8, вверх до кратного 5).

Функция должна работать на любом периоде — например, только на ноябре.

### setup
```python
import pandas as _pd0
import math as _m0
def _ref_ok(raw=None):
    d = _pd0.read_csv('deliveries.csv', parse_dates=['created']) if raw is None else raw.copy()
    o = d[d['actual_min'].between(1, 299)].copy()
    o['late'] = o['actual_min'] > o['promised_min']
    o['delay'] = o['actual_min'] - o['promised_min']
    o['hour'] = o['created'].dt.hour
    return o
```

### starter
```python
import pandas as pd
import math

def delivery_report(raw):
    ...

raw = pd.read_csv("deliveries.csv", parse_dates=["created"])
delivery_report(raw)
```

### check
```python
import pandas as _pd
raw = _pd.read_csv('deliveries.csv', parse_dates=['created'])
f = need('delivery_report')
for part, name in ((raw, 'вся осень'), (raw[raw['created'].dt.month == 11], 'только ноябрь')):
    o = _ref_ok(part)
    h = o.groupby('hour')['late'].agg(['mean', 'size'])
    w = o[(o['courier'] == 'пеший') & (o['promised_min'] == 30)]['actual_min'].quantile(0.8)
    want = {'late_pct': round(o['late'].mean() * 100, 1),
            'worst_courier': o.groupby('courier')['late'].mean().idxmax(),
            'worst_shop': o.groupby('shop_id')['late'].mean().idxmax(),
            'peak_hours': [int(x) for x in h[(h['size'] >= 50) & (h['mean'] > 0.25)].index],
            'fair_promise': int(_m0.ceil(w / 5) * 5)}
    got = f(part.copy())
    assert isinstance(got, dict), 'delivery_report должна возвращать словарь.'
    got = {k: ([int(x) for x in v] if k == 'peak_hours' else (round(float(v), 1) if k == 'late_pct' else (int(v) if k == 'fair_promise' else v))) for k, v in got.items()}
    assert got == want, f'Для «{name}»:\n{got}\nа нужно\n{want}'
```

### hint
Внутри — шаги 1–4 этого проекта, только вместо готовой `ok` — очистка параметра `raw`.

### hint
Часы пик: `h = ok.groupby("hour")["late"].agg(["mean", "size"])`, затем маска `(h["size"] >= 50) & (h["mean"] > 0.25)`.

### solution
```python
import pandas as pd
import math

def delivery_report(raw):
    ok = raw[raw["actual_min"].between(1, 299)].copy()
    ok["late"] = ok["actual_min"] > ok["promised_min"]
    ok["hour"] = ok["created"].dt.hour
    h = ok.groupby("hour")["late"].agg(["mean", "size"])
    walk30 = ok[(ok["courier"] == "пеший") & (ok["promised_min"] == 30)]
    return {
        "late_pct": round(ok["late"].mean() * 100, 1),
        "worst_courier": ok.groupby("courier")["late"].mean().idxmax(),
        "worst_shop": ok.groupby("shop_id")["late"].mean().idxmax(),
        "peak_hours": sorted(h[(h["size"] >= 50) & (h["mean"] > 0.25)].index),
        "fair_promise": math.ceil(walk30["actual_min"].quantile(0.8) / 5) * 5,
    }

raw = pd.read_csv("deliveries.csv", parse_dates=["created"])
delivery_report(raw)
```

### explain
Глава 4 пройдена. Итог исследования, который можно нести бизнесу: опаздывает почти каждая четвёртая доставка (24.0 %). Главная причина — пешие курьеры: обещание 30 минут они выполняют меньше чем в трети случаев, а заказы на ~3 км с обещанием 45 минут почти никогда не довозят вовремя (89.5 % опозданий). Отсюда два рычага: реалистичное обещание для пеших (40 минут) и предел расстояния для них. Дополнительно — часы пик, снег (у вело доля опозданий в снег почти утраивается) и сборка в KZN-2. Оценка гостя резко падает, когда опоздание больше 10 минут. Следующая глава — статистика: научимся проверять, не случайны ли такие различия.
