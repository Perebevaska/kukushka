---
title: "Jupyter: руки на клавиатуре"
files: [orders_3m.csv, shops.csv, menu.csv]
lead: "Блокнот уже установлен — теперь работаем в нём быстро. Горячие клавиши вместо мыши, настройки показа таблиц, замер времени через `%timeit`, встроенная справка и чтение длинных ошибок pandas. Терминал и память — в следующем уроке. В браузере курса тренируем то, что можно проверить, а руками в своём блокноте — по чек-листам."
recap:
  - "Два режима: <kbd>Esc</kbd> — режим команд (синяя полоска слева), <kbd>Enter</kbd> — правка. Клавиши A/B/M/Y/DD/Z работают только в режиме команд."
  - "<kbd>A</kbd> / <kbd>B</kbd> — новая ячейка выше / ниже, <kbd>M</kbd> — markdown, <kbd>Y</kbd> — код, <kbd>D</kbd><kbd>D</kbd> — удалить, <kbd>Z</kbd> — вернуть удалённую ячейку."
  - "В Jupyter показывается только последнее выражение ячейки; `display(df)` показывает таблицу из середины ячейки, `print(df)` — текстом."
  - "`pd.set_option(\"display.max_columns\", 50)` — настройка на весь блокнот, `with pd.option_context(...):` — только внутри блока. `float_format` меняет показ, а не данные."
  - "`%time` — один запуск, `%timeit` — много запусков и среднее ± разброс, `%%time` — вся ячейка. В обычном Python то же делает модуль `timeit`."
  - "`df.merge?` или <kbd>Shift</kbd>+<kbd>Tab</kbd> — справка; `inspect.signature(f)` — параметры и значения по умолчанию."
  - "Traceback читают снизу вверх: последняя строка — тип и текст ошибки, первая рамка `Cell In[…]` — ваша строка, рамки `…/pandas/…` пропускаем."
---

## Два режима и горячие клавиши

::: note Как проходить урок
Клавиши запоминаются руками, а не глазами: держите урок открытым рядом с Jupyter и выполняйте чек-листы «Сделайте в своём блокноте». Раздел «Сам себе справочник» можно открыть позже, когда понадобится.
:::

Зачем: в аналитическом блокноте десятки ячеек. Добавить ячейку, превратить её в текст, удалить неудачную — мышью это три клика и поиск кнопки, с клавиатуры — одна клавиша.

::: tip Аналогия
Режимы Jupyter — как в Excel. Когда ячейка Excel просто выделена, <kbd>Delete</kbd> стирает её целиком, а стрелки ходят по таблице. Когда вы нажали <kbd>F2</kbd> и редактируете содержимое, те же клавиши работают с текстом внутри. В Jupyter «выделена» — это **режим команд**, «редактирую» — **режим правки**. Где аналогия хромает: в Jupyter в режиме команд обычные буквы — это команды, поэтому <kbd>B</kbd> добавит ячейку, а не напечатает «b».
:::

| режим | как войти | как выглядит | что делают буквы |
|---|---|---|---|
| команд | <kbd>Esc</kbd> или клик слева от ячейки | синяя полоса слева, курсора в ячейке нет | команды над ячейками |
| правки | <kbd>Enter</kbd> или клик внутрь ячейки | мигает курсор | печатают текст |

::: figure jupyter-modes
Два режима и переходы между ними: <kbd>Enter</kbd> — в правку, <kbd>Esc</kbd> — обратно в команды. Одна и та же клавиша <kbd>B</kbd> в режиме команд добавляет ячейку, а в режиме правки печатает букву.
:::

Главные клавиши режима команд:

| клавиша | что делает |
|---|---|
| <kbd>A</kbd> / <kbd>B</kbd> | новая ячейка выше (**a**bove) / ниже (**b**elow) |
| <kbd>M</kbd> / <kbd>Y</kbd> | сделать ячейку markdown / кодом |
| <kbd>D</kbd>, <kbd>D</kbd> | удалить ячейку (нажать D дважды) |
| <kbd>Z</kbd> | вернуть удалённую ячейку |
| <kbd>X</kbd> / <kbd>C</kbd> / <kbd>V</kbd> | вырезать / копировать / вставить ячейку |
| <kbd>Shift</kbd>+<kbd>↑</kbd>/<kbd>↓</kbd>, <kbd>Shift</kbd>+<kbd>M</kbd> | выделить несколько ячеек, склеить их в одну |
| <kbd>0</kbd>, <kbd>0</kbd> | перезапустить ядро |

В обоих режимах: <kbd>Shift</kbd>+<kbd>Enter</kbd> — выполнить и перейти ниже, <kbd>Ctrl</kbd>+<kbd>Enter</kbd> — выполнить и остаться, <kbd>Alt</kbd>+<kbd>Enter</kbd> — выполнить и вставить новую ячейку ниже. На Mac вместо <kbd>Ctrl</kbd> — <kbd>Cmd</kbd>. Все команды с клавишами — в палитре <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>C</kbd>.

**Оглавление.** В левой панели JupyterLab есть значок списка — **Table of Contents**. Оно собирается из заголовков `#`, `##`, `###` в markdown-ячейках, и по нему можно прыгать по разделам. Блокнот без заголовков остаётся без оглавления.

Игрушечный пример: после ячейки с расчётом нужно добавить markdown-вывод. Курсор мигает в ячейке с кодом.

1. <kbd>Esc</kbd> — выходим в режим команд (курсор пропал, слева синяя полоса).
2. <kbd>B</kbd> — ниже появилась пустая ячейка кода, она стала текущей.
3. <kbd>M</kbd> — она стала markdown.
4. <kbd>Enter</kbd> — режим правки, печатаем «Вывод: …».
5. <kbd>Shift</kbd>+<kbd>Enter</kbd> — текст отрисован, курсор ушёл ниже.

Блокнот для Jupyter — это список ячеек, поэтому команды можно изобразить операциями со списком. Пусть `cur` — номер текущей ячейки:

```python
cells = [["code", "import pandas as pd"], ["code", "df = pd.read_csv('orders_3m.csv')"]]
cur = 1                               # текущая — ячейка с загрузкой

cells.insert(cur + 1, ["code", ""])   # B: новая ячейка ниже текущей...
cur = cur + 1                         # ...и она становится текущей
cells[cur][0] = "markdown"            # M: тип текущей ячейки — markdown
cells[cur][1] = "Вывод: 2089 заказов"
print(cur, cells)
```

Что здесь происходит:

- каждая ячейка — список `[тип, текст]`, блокнот — список ячеек;
- `cells.insert(cur + 1, …)` вставляет новую ячейку сразу под текущей — это <kbd>B</kbd>; <kbd>A</kbd> вставляла бы на место `cur`, сдвигая текущую вниз;
- `cells[cur][0] = "markdown"` меняет только тип — текст ячейки при <kbd>M</kbd> и <kbd>Y</kbd> сохраняется.

::: predict
```python static
cells = [["code", "import pandas as pd"], ["code", "df = pd.read_csv('orders_3m.csv')"]]
cur = 1
cells.insert(cur, ["code", ""])   # A: новая ячейка выше текущей, она становится текущей
print(cur, len(cells))
```

- `2 3`
- [x] `1 3`
- `0 3`

Почему: при <kbd>A</kbd> новая ячейка встаёт на место текущей, а старая сдвигается вниз. Номер текущей ячейки не меняется — просто под ним теперь новая ячейка.
:::

::: quiz
Курсор мигает внутри ячейки с кодом, и вы нажимаете <kbd>B</kbd>, чтобы добавить ячейку ниже. Что произойдёт?

- [x] В код напечатается буква «b»
  > Курсор мигает — это режим правки, и буквы печатают текст. Сначала <kbd>Esc</kbd>, потом <kbd>B</kbd>.
- [ ] Появится новая ячейка ниже
  > Так будет только в режиме команд — после <kbd>Esc</kbd>.
- [ ] Ячейка выполнится
  > Выполняет <kbd>Shift</kbd>+<kbd>Enter</kbd> или <kbd>Ctrl</kbd>+<kbd>Enter</kbd>, а не буквы.
- [ ] Ячейка станет markdown
  > Это <kbd>M</kbd> и тоже только в режиме команд.
:::

::: warn Типичные ошибки
- **«Клавиши не работают».** Вы в режиме правки: буквы ушли в код. Нажмите <kbd>Esc</kbd>.
- **<kbd>Z</kbd> вернул ячейку, но не переменные.** Удаление ячейки не трогает ядро, а возврат не выполняет её заново: переменные из удалённой ячейки живут или не живут независимо от того, видна она или нет.
- **<kbd>0</kbd>, <kbd>0</kbd> посреди работы.** Ядро перезапустится, все переменные пропадут. Это не ошибка блокнота — просто выполните ячейки сверху заново.
- **Заголовок «жирным» вместо `##`.** Оглавление его не увидит.
:::

::: note Сделайте в своём блокноте
1. Пройдите игрушечный пример руками: <kbd>Esc</kbd> → <kbd>B</kbd> → <kbd>M</kbd> → <kbd>Enter</kbd> → текст → <kbd>Shift</kbd>+<kbd>Enter</kbd>.
2. Удалите ячейку (<kbd>D</kbd>, <kbd>D</kbd>) и верните её (<kbd>Z</kbd>).
3. Склейте две ячейки: выделите их <kbd>Shift</kbd>+<kbd>↓</kbd> и нажмите <kbd>Shift</kbd>+<kbd>M</kbd>.
4. Откройте оглавление в левой панели и перейдите по нему к любому разделу.
:::

{{practice: p-keys, keys-sim}}

## Показать таблицу: display, print и настройки pandas

Зачем: в одной ячейке хочется показать две таблицы, а широкая таблица заказов обрезается многоточием `...` посередине. Обе проблемы решаются за минуту, если знать, кто и как показывает результат.

**Что показывает Jupyter.** Под ячейкой появляется значение её **последнего выражения**. Таблица pandas при этом рисуется красивой HTML-таблицей. Всё, что выше, не показывается, если не напечатать это явно:

```python static
df.head(3)        # не покажется: выражение не последнее
df.shape          # покажется: (2089, 9)
```

Чтобы показать таблицу из середины ячейки, в Jupyter есть `display()` — она рисует таблицу так же, как последнее выражение. `print(df)` выводит ту же таблицу простым текстом:

```python static
display(df.head(3))       # HTML-таблица
display(df.describe())    # и ещё одна — в той же ячейке
print(df.shape)           # текст
```

В браузере курса работает то же правило «последнее выражение — таблицей», а вот `display()` здесь нет: она часть Jupyter (модуль IPython). В своём блокноте она доступна без импорта.

**Настройки показа.** pandas сам решает, сколько строк и столбцов показать и сколько знаков после точки печатать. Решение можно поменять:

| настройка | что меняет | пример |
|---|---|---|
| `display.max_rows` | сколько строк показать, прежде чем обрезать | `60` |
| `display.max_columns` | сколько столбцов показать | `50` |
| `display.float_format` | как печатать дробные числа | `"{:.1f}".format` |
| `display.precision` | сколько знаков после точки | `2` |

Есть два способа применить настройку:

```python static
pd.set_option("display.max_columns", 50)      # на весь блокнот — ставят в первой ячейке
pd.reset_option("display.max_columns")        # вернуть как было

with pd.option_context("display.max_rows", 10):   # только внутри блока with
    print(df)
```

Игрушечный пример: средний чек 339.966 ₽. При показе хочется видеть 340.0, но считать дальше по точному числу.

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
avg = df.groupby("shop_id")["amount"].mean()     # средний чек кофеен — длинные дроби

with pd.option_context("display.float_format", "{:.1f}".format):
    print(avg)                                   # внутри блока — один знак после точки

print(avg.loc["PRM-1"])                          # само число не изменилось
print(pd.get_option("display.float_format"))     # после блока настройка снята
```

Что здесь происходит:

- `pd.option_context(имя, значение)` включает настройку только на время блока `with`;
- `"{:.1f}".format` — функция, которая превращает число в строку с одним знаком после точки; pandas вызывает её для каждого дробного числа при показе;
- `avg.loc["PRM-1"]` показывает, что данные остались точными: округлился только вывод;
- `pd.get_option(...)` — текущее значение настройки; после блока оно снова `None`, то есть «по умолчанию».

Как читать результат: таблица стала читаемой (355.3 вместо 355.272901), но расчёты по `avg` идут по точным значениям. Если же нужно округлить сами данные — например, для выгрузки в отчёт — это `avg.round(1)`.

::: predict
```python static
import pandas as pd
s = pd.Series([339.966])
with pd.option_context("display.float_format", "{:.1f}".format):
    shown = s.to_string(index=False)
print(shown, s.iloc[0])
```

- `340.0 340.0`
- [x] `340.0 339.966`
- `339.966 339.966`

Почему: `float_format` меняет только то, как число превращается в текст. Внутри блока текст — `340.0`, а значение в Series осталось прежним.
:::

::: warn Типичные ошибки
- **«Округлил через `float_format`, а в Excel ушли длинные дроби».** Настройка показа не меняет данные. Для данных — `round`.
- **`pd.set_option` в середине блокнота.** Она действует на всё, что выполняется после неё, — в том числе на ячейки выше, если их перезапустить. Вывод начинает зависеть от порядка запуска. Постоянные настройки — в первую ячейку, разовые — через `option_context`.
- **`pd.set_option("display.max_rows", None)` на большой таблице.** Jupyter попытается нарисовать миллион строк, и вкладка зависнет. Смотрите `head()`, `sample()` и агрегаты.
- **Две таблицы в ячейке, а видна одна.** Показывается только последнее выражение; первую оберните в `display()`.
:::

::: note Сделайте в своём блокноте
1. В первой ячейке после импортов: `pd.set_option("display.max_columns", 50)`.
2. В одной ячейке покажите `display(df.head(3))` и `display(df.describe())` — должны появиться две таблицы.
3. Сравните с `print(df.head(3))` — та же таблица текстом.
:::

{{practice: float-fmt}}

## Magic-команды: %time, %timeit, %pip, autoreload

Зачем: два способа посчитать одно и то же — какой быстрее? Не хватает библиотеки — как поставить, не выходя из блокнота? Для таких дел в Jupyter есть **magic-команды** — строки, которые начинаются с `%`. Это не Python, их понимает только Jupyter (точнее, IPython внутри него), поэтому в браузере курса они не работают.

- `%команда` действует на одну строку;
- `%%команда` в первой строке ячейки действует на всю ячейку.

### Замер времени

| команда | что делает | когда нужна |
|---|---|---|
| `%time выражение` | выполняет один раз, печатает время | долгая операция: загрузка, обучение модели |
| `%timeit выражение` | выполняет много раз, печатает среднее ± разброс | быстрая операция, сравнение вариантов |
| `%%time` | время всей ячейки | несколько шагов подряд |

Сравним два способа посчитать цену одной чашки. Первый — построчно через `apply`, его мы ещё не встречали:

- `df.apply(f, axis=1)` вызывает функцию `f` **для каждой строки** таблицы по очереди — как цикл `for` по строкам. `axis=1` значит «по строкам»; без него (`axis=0`) функция получала бы столбцы.
- `lambda r: r["amount"] / r["qty"]` — короткая функция без имени: получает строку `r` и делит её сумму на количество чашек.

Игрушечный пример на трёх строках — результат тот же, что у деления столбцов:

```python
import pandas as pd
t = pd.DataFrame({"amount": [300, 500, 240], "qty": [1, 2, 1]})
print(t.apply(lambda r: r["amount"] / r["qty"], axis=1).tolist())   # функция вызвана 3 раза, по разу на строку
print((t["amount"] / t["qty"]).tolist())                             # одна операция над двумя столбцами
```

Числа одинаковые: 300, 250 и 240 ₽ за чашку. Разница — в скорости: `apply` вызывает Python-функцию на каждой строке, а деление столбцов pandas выполняет одной операцией над всем массивом. Насколько это быстрее, покажет `%timeit`:

```python static
%timeit df.apply(lambda r: r["amount"] / r["qty"], axis=1)
%timeit df["amount"] / df["qty"]
```

На одном ноутбуке это выдало:

```text
13.2 ms ± 828 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)
87.5 μs ± 8.78 μs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
```

Как читать: `13.2 ms` — среднее время одного выполнения, `± 828 μs` — разброс между сериями. `7 runs, 100 loops each` — семь серий по 100 повторов. Чтобы сравнить, приведите к одним единицам: 13.2 мс = 13 200 мкс, 13 200 / 87.5 ≈ 151. Построчный `apply` медленнее в полторы сотни раз — и это всего на 2 089 строках.

::: figure timeit-runs
Что делает `%timeit` внутри, на условных числах: подбирает число запусков в серии (1, 10, 100…), пока серия не займёт не меньше 0.2 с; повторяет 7 серий; время каждой серии делит на число запусков и по этим 7 значениям печатает среднее ± стандартное отклонение. Времена серий подобраны так, что нижняя строка, собранная тем же кодом IPython, что печатает настоящий `%timeit`, совпала с первой строкой вывода выше.
:::

Единицы: `s` — секунды, `ms` — миллисекунды (тысячные), `μs` или `µs` — микросекунды (миллионные), `ns` — наносекунды.

В обычном Python, и в браузере курса тоже, то же самое делает модуль `timeit`:

```python
import timeit
import pandas as pd
df = pd.read_csv("orders_3m.csv")

n = 5
t_apply = timeit.timeit(lambda: df.apply(lambda r: r["amount"] / r["qty"], axis=1), number=n) / n
t_vec = timeit.timeit(lambda: df["amount"] / df["qty"], number=n) / n
print(f"apply: {t_apply * 1000:.2f} мс, столбцом: {t_vec * 1000:.3f} мс")
print("apply медленнее в", round(t_apply / t_vec), "раз")
```

Что здесь происходит:

- `timeit.timeit(функция, number=n)` вызывает функцию `n` раз и возвращает общее время в секундах; делим на `n` — время одного запуска;
- `lambda: …` упаковывает выражение в функцию без имени, чтобы `timeit` мог вызвать его много раз;
- `* 1000` переводит секунды в миллисекунды для печати.

Числа у вас будут свои: время зависит от компьютера, и браузерный Python медленнее обычного. Но порядок сохранится — `apply` по строкам медленнее в десятки и сотни раз.

### %pip и autoreload

`%pip install openpyxl` ставит библиотеку в окружение **текущего ядра** — в отличие от `!pip`, который может попасть в другой Python. В проекте на uv надёжнее ставить библиотеки командой `uv add openpyxl` в терминале: так она запишется в `pyproject.toml`, и коллега получит её через `uv sync`. В окружениях uv своего pip по умолчанию нет, поэтому `%pip` там может ответить `No module named pip`. После установки перезапустите ядро.

Когда повторяющиеся функции переезжают из блокнота в свой файл `zerno_utils.py`, пригодится автоперезагрузка:

```python static
%load_ext autoreload
%autoreload 2
from zerno_utils import shop_kpi     # поправили файл — новая версия подхватится сама
```

Без неё Jupyter помнит модуль таким, каким импортировал его в первый раз, и правки в `.py` не видны до перезапуска ядра.

::: quiz
Два способа посчитать одно и то же дали в `%timeit`: A — `2.1 ms ± 40 μs per loop`, B — `850 μs ± 12 μs per loop`. Что верно?

- [x] B быстрее примерно в 2.5 раза
  > 2.1 мс = 2100 мкс; 2100 / 850 ≈ 2.5. Сначала единицы, потом сравнение.
- [ ] A быстрее: 2.1 меньше 850
  > Числа в разных единицах: миллисекунды и микросекунды. 2.1 мс — это 2100 мкс, больше, чем 850.
- [ ] B быстрее примерно в 3.3 раза: 40 / 12
  > Числа после `±` — разброс между сериями, а не время. Сравнивают средние — первые числа строк.
- [ ] Сравнить нельзя: нужен `%time`
  > Наоборот: `%time` — один запуск, он шумнее. Для сравнения быстрых операций и нужен `%timeit`.
:::

::: warn Типичные ошибки
- **`%timeit` на ячейке, которая меняет данные.** `%%timeit` над `df = df[df["amount"] > 300]` выполнит фильтр сотни раз подряд — каждый раз по уже отфильтрованной таблице. Замеряйте выражения без присваивания.
- **Сравнение `ms` и `μs` как чисел.** «13.2 больше 87.5?» — нет, это разные единицы. Сначала приведите к одной.
- **`%time` вместо `%timeit` для быстрой операции.** Один запуск на 100 мкс — это шум: на результат влияет всё, что в этот момент делает компьютер.
- **Magic-команда в `.py`-файле.** `%timeit` — не Python: в скрипте это `SyntaxError`. В скриптах — модуль `timeit` или `time.perf_counter()`.
:::

::: note Сделайте в своём блокноте
1. Запустите оба `%timeit` из примера и приведите результаты к микросекундам.
2. Поставьте над ячейкой с загрузкой данных `%%time` — сколько читается `orders_3m.csv`?
3. Выполните `%who` — Jupyter покажет имена всех переменных в ядре.
:::

{{practice: timeit-read, time-it}}

## Сам себе справочник: ?, Shift+Tab и help

Зачем: какой параметр у `sort_values` отвечает за порядок? Что вернёт `value_counts` — числа или доли? Ответ есть внутри самой библиотеки, искать в интернете не обязательно.

| способ | где работает | что показывает |
|---|---|---|
| <kbd>Shift</kbd>+<kbd>Tab</kbd> внутри скобок | Jupyter, VS Code | подсказку: параметры и начало описания |
| `df.merge?` | Jupyter | полное описание (docstring) |
| `df.merge??` | Jupyter | ещё и исходный код, если он на Python |
| <kbd>Tab</kbd> после точки | Jupyter, VS Code | список методов и столбцов |
| `help(pd.Series.round)` | везде, в том числе в браузере курса | полное описание |
| `inspect.signature(f)` | везде | только параметры и значения по умолчанию |

Описание функции в pandas устроено всегда одинаково: одна фраза о том, что делает функция → **Parameters** (параметры, тип и значение по умолчанию) → **Returns** (что вернёт) → **See Also** (похожие функции) → **Examples** (примеры, которые можно скопировать). Читать стоит в таком порядке: первая фраза, Parameters, Examples.

```python
import inspect
import pandas as pd

sig = inspect.signature(pd.Series.value_counts)
print(sig)
for name, p in sig.parameters.items():
    if name != "self":
        print(f"{name:10} по умолчанию = {p.default}")
```

Что здесь происходит:

- `inspect.signature(функция)` возвращает «подпись»: все параметры с их значениями по умолчанию;
- `sig.parameters` — словарь «имя параметра → описание», у описания есть `.default`;
- `f"{name:10}"` выравнивает имя по ширине 10 символов, чтобы колонка значений шла ровно.

Как читать результат: `normalize=False` — по умолчанию `value_counts` считает штуки, а доли — только с `normalize=True`. `dropna=True` — пропуски по умолчанию не считаются, и это частая причина, почему сумма `value_counts()` меньше `len(df)`.

Полная документация — на pandas.pydata.org. Смотрите версию в правом верхнем углу сайта: она должна совпадать с вашей (`pd.__version__`), иначе параметры могут отличаться.

::: warn Типичные ошибки
- **`df.merge?` в браузере курса или в `.py`.** Знак `?` понимает только Jupyter. Везде работает `help(df.merge)`.
- **Документация другой версии.** Совет из статьи 2019 года может не работать в pandas 3 — сверяйте версию.
- **`help(df.merge())` со скобками.** Скобки вызывают функцию, и `help` получит её результат (или ошибку), а не саму функцию.
:::

::: note Сделайте в своём блокноте
1. Напишите `df.sort_values(` и нажмите <kbd>Shift</kbd>+<kbd>Tab</kbd> — найдите параметр `ascending`.
2. Выполните `pd.read_csv?` и найдите в описании параметр `usecols`.
3. Напишите `df.` и нажмите <kbd>Tab</kbd> — посмотрите список методов.
:::

{{practice: signature}}

## Читаем traceback pandas

Зачем: ошибка pandas в Jupyter занимает полэкрана, и новичок пугается. На самом деле из этих 40 строк нужны две: первая рамка и последняя строка.

Вот что Jupyter показал на опечатку в имени столбца (середина сокращена, пути укорочены):

```text
---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
Cell In[2], line 1
----> 1 by_shop = (df.groupby("shop")
      2              .agg(revenue=("amount", "sum")))
      3 by_shop

File .../pandas/core/frame.py:10835, in DataFrame.groupby(self, by, level, ...)
> 10835         return DataFrameGroupBy(
...
File .../pandas/core/groupby/grouper.py:901, in get_grouper(obj, key, level, ...)
--> 901         raise KeyError(gpr)

KeyError: 'shop'
```

Как читать — **снизу вверх**:

1. **Последняя строка** — тип ошибки и сообщение: `KeyError: 'shop'` — «не нашёл ключ `shop`».
2. **Первая рамка `Cell In[2], line 1`** — ваш код: ячейка с номером запуска 2, строка 1. Стрелка `---->` показывает строку.
3. **Рамки `File …/pandas/…`** — внутренности библиотеки: какая функция кого вызвала. Ошибку в pandas вы почти наверняка не нашли, поэтому их пропускаем.

::: figure traceback-read
Тот же traceback, разложенный на три зоны. Читаем снизу: сначала последняя строка (что случилось), затем рамку `Cell In[…]` (где в вашем коде). Средние рамки из pandas обычно пропускаем.
:::

В браузере курса то же сообщение короче — только тип, текст и ваша строка:

```python error
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_shop = df.groupby("shop").agg(revenue=("amount", "sum"))
```

Частые ошибки pandas и что они значат:

| последняя строка | что случилось | что проверить |
|---|---|---|
| `KeyError: 'shop'` | нет столбца с таким именем | `df.columns.tolist()`: опечатка, пробел, регистр |
| `KeyError: "Label(s) ['amout'] do not exist"` | то же внутри `agg` или `[[…]]` | имена в кортежах `agg` |
| `TypeError: unsupported operand type(s) for +: 'int' and 'str'` | арифметика с текстовым столбцом | `df.dtypes` |
| `AttributeError: Can only use .dt accessor with datetimelike values` | столбец с датой — ещё текст | `pd.to_datetime` или `parse_dates` |
| `ValueError: You are trying to merge on int64 and str columns` | ключи соединения разного типа | `astype` у одного из ключей |

::: predict
```python static
import pandas as pd
df = pd.read_csv("orders_3m.csv")
print(df["Amount"].sum())
```

- `710195`
- [x] `Ошибка KeyError`
- `Ошибка AttributeError`

Почему: имена столбцов чувствительны к регистру. В таблице есть `amount`, а `Amount` — другое имя, поэтому pandas не находит ключ.
:::

::: warn Типичные ошибки
- **Читать сверху и застрять в коде pandas.** Начинайте с последней строки, потом ищите `Cell In[…]`.
- **Искать в интернете весь traceback.** Ищите последнюю строку без ваших имён: `Can only use .dt accessor with datetimelike values`.
- **Чинить строку, на которую указывает стрелка, когда виновата другая.** `KeyError` в `groupby` бывает из-за того, что столбец не создан выше или был переименован. Стрелка — место, где ошибка заметна, а не обязательно её причина.
:::

{{practice: tb-fix}}

## Практика

## task: p-keys | Вывод под ячейкой — с клавиатуры | warmup

Курсор мигает в ячейке с расчётом. Соберите последовательность клавиш, которая добавит **под ней** markdown-ячейку, впишет в неё текст вывода и отрисует его.

### parsons
```python
keys = []
keys.append("Esc")
keys.append("B")
keys.append("M")
keys.append("Enter")
keys.append("напечатать: Вывод: в ноябре +9.6 %")
keys.append("Shift+Enter")
print(keys)
```

### check
```python
k = need('keys', list)
assert len(k) == 6, f'Клавиш {len(k)}, а нужно 6. Строка keys = [] — первая, print — последний.'
assert k[0] == 'Esc', 'Пока курсор мигает, буквы печатают текст. Сначала выйдите в режим команд.'
assert k.index('B') < k.index('M'), 'M меняет тип текущей ячейки: сначала создайте новую ячейку, потом меняйте её тип.'
assert k.index('Enter') < k.index('напечатать: Вывод: в ноябре +9.6 %'), 'Печатать текст можно только в режиме правки — после Enter.'
assert k[-1] == 'Shift+Enter', 'Последним шагом markdown нужно отрисовать.'
assert k == ['Esc', 'B', 'M', 'Enter', 'напечатать: Вывод: в ноябре +9.6 %', 'Shift+Enter'], f'Порядок: {k}.'
```

### hint
Буквы-команды работают только в режиме команд, а печатать текст можно только в режиме правки.

### hint
Esc → новая ячейка ниже → сделать её markdown → войти в правку → текст → отрисовать.

## task: signature | Значения по умолчанию | warmup

Не заглядывая в интернет, узнайте через `inspect.signature`, какие значения по умолчанию у трёх параметров, и сохраните их в переменные:

- `asc_default` — параметр `ascending` у `pd.DataFrame.sort_values`;
- `norm_default` — `normalize` у `pd.Series.value_counts`;
- `dropna_default` — `dropna` у `pd.Series.value_counts`.

### starter
```python
import inspect
import pandas as pd

```

### check
```python
import inspect as _i, pandas as _pd
assert need('asc_default') == _i.signature(_pd.DataFrame.sort_values).parameters['ascending'].default, 'asc_default не совпадает с подписью sort_values.'
vc = _i.signature(_pd.Series.value_counts).parameters
assert need('norm_default') == vc['normalize'].default, 'norm_default не совпадает с подписью value_counts.'
assert need('dropna_default') == vc['dropna'].default, 'dropna_default не совпадает с подписью value_counts.'
assert calls('signature') >= 1, 'Достаньте значения из inspect.signature(...), а не впишите по памяти.'
```

### hint
`inspect.signature(функция).parameters` — словарь параметров; у каждого есть `.default`.

### hint
`vc = inspect.signature(pd.Series.value_counts).parameters`, затем `norm_default = vc["normalize"].default`.

### solution
```python
import inspect
import pandas as pd

asc_default = inspect.signature(pd.DataFrame.sort_values).parameters["ascending"].default
vc = inspect.signature(pd.Series.value_counts).parameters
norm_default = vc["normalize"].default
dropna_default = vc["dropna"].default
print(asc_default, norm_default, dropna_default)
```

## task: float-fmt | Показать красиво, считать точно | base

Посчитайте `avg` — средний чек по кофейням (`groupby("shop_id")`), **не округляя** его. Напечатайте `avg` так, чтобы у чисел был ровно один знак после точки, — через `pd.option_context` и `display.float_format`. После этого настройка показа должна вернуться к значению по умолчанию.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
_ff = _pd.get_option('display.float_format')
_pd.reset_option('display.float_format')          # чтобы настройка не утекла в другие задачи
d = _pd.read_csv('orders_3m.csv')
w = d.groupby('shop_id')['amount'].mean()
a = need('avg', _pd.Series)
assert a.round(6).equals(w.round(6)), 'avg — средний чек по кофейням без округления: округлять нужно только при показе.'
assert _ff is None, 'После вашего кода display.float_format осталась включённой. Используйте with pd.option_context(...), а не set_option.'
for shop, v in w.items():
    assert printed(f'{v:.1f}'), f'В выводе нет {shop} с одним знаком после точки ({v:.1f}). Напечатайте avg внутри блока with.'
assert not printed(f'{w.max():.6f}'), 'В выводе есть длинные дроби — печатайте avg внутри блока with.'
assert calls('option_context') >= 1, 'Нужен pd.option_context("display.float_format", ...).'
```

### hint
Формат с одним знаком — функция `"{:.1f}".format`. Её и передайте в настройку `display.float_format`.

### hint
`with pd.option_context("display.float_format", "{:.1f}".format):` и внутри блока — `print(avg)`.

### hint
Полностью: `avg = df.groupby("shop_id")["amount"].mean()`, затем блок `with … : print(avg)`. Округлять `avg` не нужно.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
avg = df.groupby("shop_id")["amount"].mean()

with pd.option_context("display.float_format", "{:.1f}".format):
    print(avg)
```

### explain
Лучший средний чек — у PRM-1: на экране 355.3, а в `avg` по-прежнему 355.2729…, и все дальнейшие расчёты идут по точному числу. Если бы вы написали `avg = avg.round(1)`, проверка заметила бы потерю точности, а при `pd.set_option` формат остался бы включённым для всего блокнота. Блок `with` хорош тем, что сам возвращает настройку на место — даже если внутри блока случится ошибка.

## task: timeit-read | Кто быстрее: читаем %timeit | base

Перед вами настоящий вывод `%timeit` для двух способов посчитать цену чашки. Напишите `to_us(text)` — функцию, которая достаёт из такой строки **среднее** время и переводит его в микросекунды (единицы бывают `ns`, `µs`, `μs`, `ms`, `s`). Посчитайте `speedup` — во сколько раз второй способ быстрее первого, округлив до целого.

### starter
```python
slow = "13.2 ms ± 828 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)"
fast = "87.5 μs ± 8.78 μs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)"

def to_us(text):
    ...

speedup = ...
speedup
```

### check
```python
f = need('to_us')
def _w(t):
    v, u = t.split()[:2]
    return float(v) * {'ns': 0.001, 'µs': 1, 'μs': 1, 'ms': 1000, 's': 1_000_000}[u]
for t in ('13.2 ms ± 828 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)',
          '87.5 μs ± 8.78 μs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)',
          '1.07 s ± 12.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)',
          '412 ns ± 3.1 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)',
          '5.5 µs ± 0.2 µs per loop (mean ± std. dev. of 7 runs, 100,000 loops each)'):
    got = f(t)
    assert got is not None and close(got, _w(t), 1e-6), f'to_us("{t[:22]}…") = {got}, а нужно {_w(t)}. Берите первое число и его единицу — это среднее; разброс после ± не нужен.'
assert need('speedup') == round(_w('13.2 ms ± 828 μs') / _w('87.5 μs ± 8.78 μs')), f'speedup = {need("speedup")}. Поделите время медленного способа на время быстрого и округлите.'
```

### hint
Среднее — первое число строки, его единица — второе слово: `value, unit = text.split()[:2]`.

### hint
Словарь множителей до микросекунд: `{"ns": 0.001, "µs": 1, "μs": 1, "ms": 1000, "s": 1_000_000}`. Буквы «мю» бывают двух видов, поэтому в словаре обе.

### hint
`return float(value) * factor[unit]`, затем `speedup = round(to_us(slow) / to_us(fast))`.

### solution
```python
slow = "13.2 ms ± 828 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)"
fast = "87.5 μs ± 8.78 μs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)"

FACTOR = {"ns": 0.001, "µs": 1, "μs": 1, "ms": 1000, "s": 1_000_000}

def to_us(text):
    value, unit = text.split()[:2]
    return float(value) * FACTOR[unit]

speedup = round(to_us(slow) / to_us(fast))
speedup
```

### explain
13.2 мс — это 13 200 мкс, и построчный `apply` медленнее операции над столбцом в 151 раз. Если сравнить «на глаз» 13.2 и 87.5, вывод получится ровно наоборот. Ловушка с буквой: IPython печатает греческую «μ» (U+03BC), а на клавиатуре и в некоторых шрифтах встречается «микро» «µ» (U+00B5). Выглядят одинаково, но для Python это разные символы, поэтому в словаре нужны обе.

## task: time-it | Замер в обычном Python | base

В браузере `%timeit` нет, но есть модуль `timeit`. Замерьте два способа посчитать цену одной чашки (`amount / qty`): `t_apply` — построчно через `df.apply(..., axis=1)`, `t_vec` — делением столбцов. Время одного запуска — в секундах, по 3 запуска на способ. Сохраните `faster` — во сколько раз деление столбцов быстрее.

### starter
```python
import timeit
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
ta, tv = need('t_apply'), need('t_vec')
assert isinstance(ta, float) and isinstance(tv, float), 't_apply и t_vec — числа секунд (float), результат timeit.timeit(...) / число запусков.'
assert 0 < tv < ta, f't_apply = {ta:.5f} с, t_vec = {tv:.5f} с. Построчный apply должен выйти медленнее — проверьте, что замеряете нужные выражения.'
assert close(need('faster'), ta / tv, 1e-9 + ta / tv * 1e-9), 'faster = t_apply / t_vec.'
assert calls('timeit') >= 2, 'Замерьте оба способа через timeit.timeit(...).'
assert 'apply' in _code and 'axis=1' in _code, 'Первый способ — df.apply(..., axis=1).'
```

### hint
`timeit.timeit(lambda: выражение, number=3)` вернёт общее время трёх запусков; поделите на 3. Что делает `apply(..., axis=1)`, объяснено в разделе «Magic-команды», перед примером с `%timeit`.

### hint
Построчно: `lambda: df.apply(lambda r: r["amount"] / r["qty"], axis=1)`; столбцами: `lambda: df["amount"] / df["qty"]`.

### hint
`faster = t_apply / t_vec`.

### solution
```python
import timeit
import pandas as pd
df = pd.read_csv("orders_3m.csv")

n = 3
t_apply = timeit.timeit(lambda: df.apply(lambda r: r["amount"] / r["qty"], axis=1), number=n) / n
t_vec = timeit.timeit(lambda: df["amount"] / df["qty"], number=n) / n
faster = t_apply / t_vec
print(f"apply: {t_apply:.4f} с, столбцы: {t_vec:.5f} с, быстрее в {faster:.0f} раз")
```

### explain
Точные цифры у каждого свои, но разрыв — десятки или сотни раз: `apply(axis=1)` вызывает Python-функцию для каждой из 2 089 строк, а деление столбцов делается одной операцией над массивом. Отсюда правило pandas: сначала ищите операцию над столбцом целиком, `apply` по строкам — последнее средство. Типичная ошибка — забыть `lambda:` и написать `timeit.timeit(df["amount"] / df["qty"])`: тогда выражение вычислится один раз до замера, а `timeit` получит готовую таблицу вместо функции и упадёт.

## task: tb-fix | Две ошибки подряд | base

Код ниже должен собрать выручку и число заказов по кофейням, но падает. Запустите его, прочитайте последнюю строку ошибки, исправьте и запустите снова — ошибок две. Исправьте код и сохраните в `bad_names` список неверных имён столбцов, которые вы нашли в сообщениях об ошибках, в порядке их появления.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

by_shop = df.groupby("shop").agg(
    revenue=("amout", "sum"),
    orders=("order_id", "count"),
)
bad_names = []
by_shop
```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
w = d.groupby('shop_id').agg(revenue=('amount', 'sum'), orders=('order_id', 'count'))
b = need('by_shop', _pd.DataFrame)
assert list(b.columns) == ['revenue', 'orders'], f'Столбцы by_shop: {list(b.columns)}, а нужны revenue и orders.'
assert b.sort_index().astype(int).equals(w.astype(int)), 'by_shop не совпадает с выручкой и числом заказов по shop_id.'
assert need('bad_names', list) == ['shop', 'amout'], f'bad_names = {need("bad_names")}. Первой падает группировка, второй — agg; имена — ровно как в сообщениях KeyError.'
```

### hint
Первая ошибка — `KeyError: 'shop'`: такого столбца нет. Посмотрите настоящие имена: `print(df.columns.tolist())`.

### hint
После исправления группировки появится `KeyError: "Label(s) ['amout'] do not exist"` — опечатка внутри `agg`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

by_shop = df.groupby("shop_id").agg(
    revenue=("amount", "sum"),
    orders=("order_id", "count"),
)
bad_names = ["shop", "amout"]
by_shop
```

### explain
Обе ошибки — `KeyError`, но сообщения разные: `groupby` пишет просто `'shop'`, а `agg` — `Label(s) ['amout'] do not exist`. Python останавливается на первой ошибке, поэтому вторая видна только после исправления первой — это нормально, чините по одной. Самый быстрый способ проверить имена — `df.columns.tolist()`: опечатки, лишние пробелы (`"amount "`) и регистр (`"Amount"`) видны сразу.

## task: keys-sim | Режим команд в миниатюре | star

Напишите `press(cells, cur, keys)` — упрощённую модель режима команд. `cells` — список ячеек `[тип, текст]`, `cur` — номер текущей ячейки, `keys` — список нажатий. Функция возвращает пару `(cells, cur)` после всех нажатий:

- `"A"` — новая `["code", ""]` на место текущей (текущая сдвигается вниз), `cur` не меняется;
- `"B"` — новая `["code", ""]` сразу под текущей, `cur` переходит на неё;
- `"M"` / `"Y"` — тип текущей ячейки становится `"markdown"` / `"code"`, текст сохраняется;
- `"DD"` — удалить текущую ячейку и запомнить её вместе с номером. Если ячеек не осталось, появляется одна пустая `["code", ""]`. `cur` указывает на ячейку, вставшую на место удалённой, а если удалили последнюю — на новую последнюю;
- `"Z"` — вернуть последнюю удалённую ячейку на её прежний номер и сделать текущей; если возвращать нечего — ничего не делать.

### starter
```python
def press(cells, cur, keys):
    cells = [list(c) for c in cells]      # работаем с копией
    ...
    return cells, cur

nb = [["code", "import pandas as pd"], ["code", "df = pd.read_csv('orders_3m.csv')"]]
press(nb, 1, ["B", "M"])
```

### check
```python
def _p(cells, cur, keys):
    cells = [list(c) for c in cells]; trash = []
    for k in keys:
        if k == 'A': cells.insert(cur, ['code', ''])
        elif k == 'B': cells.insert(cur + 1, ['code', '']); cur += 1
        elif k == 'M': cells[cur][0] = 'markdown'
        elif k == 'Y': cells[cur][0] = 'code'
        elif k == 'DD':
            trash.append((cur, cells.pop(cur)))
            if not cells: cells.append(['code', ''])
            cur = min(cur, len(cells) - 1)
        elif k == 'Z' and trash:
            i, c = trash.pop(); cells.insert(i, c); cur = i
    return cells, cur
f = need('press')
nb = [['code', 'import pandas as pd'], ['code', "df = pd.read_csv('orders_3m.csv')"], ['markdown', '## Итоги']]
cases = [(nb, 1, ['B', 'M']), (nb, 0, ['A', 'A']), (nb, 2, ['DD']), (nb, 0, ['DD', 'DD', 'Z']),
         (nb, 1, ['DD', 'Z', 'Y']), ([['code', 'x = 1']], 0, ['DD']), (nb, 2, ['Y', 'DD', 'DD', 'Z', 'Z']),
         (nb, 0, ['Z']), (nb, 2, ['B', 'DD'])]
for cells, cur, keys in cases:
    before = [list(c) for c in cells]
    got = f(cells, cur, keys)
    want = _p(cells, cur, keys)
    assert got is not None and (list(map(list, got[0])), got[1]) == want, f'press(..., cur={cur}, keys={keys}) вернула {got}, а нужно {want}.'
    assert cells == before, 'Функция изменила исходный список ячеек — работайте с копией.'
```

### hint
Все действия — операции со списком: `insert`, `pop` и замена `cells[cur][0]`. Для `"Z"` нужна «корзина» — список пар `(номер, ячейка)`, куда `"DD"` кладёт удалённое.

### hint
После `"DD"`: если список опустел — добавьте пустую ячейку; затем `cur = min(cur, len(cells) - 1)` — так курсор не выйдет за конец.

### hint
`"Z"`: `if trash: i, cell = trash.pop(); cells.insert(i, cell); cur = i`. `trash.pop()` берёт последнюю удалённую — как настоящая отмена.

### solution
```python
def press(cells, cur, keys):
    cells = [list(c) for c in cells]      # работаем с копией
    trash = []                            # удалённые ячейки: (номер, ячейка)
    for k in keys:
        if k == "A":
            cells.insert(cur, ["code", ""])
        elif k == "B":
            cells.insert(cur + 1, ["code", ""])
            cur += 1
        elif k == "M":
            cells[cur][0] = "markdown"
        elif k == "Y":
            cells[cur][0] = "code"
        elif k == "DD":
            trash.append((cur, cells.pop(cur)))
            if not cells:
                cells.append(["code", ""])
            cur = min(cur, len(cells) - 1)
        elif k == "Z" and trash:
            i, cell = trash.pop()
            cells.insert(i, cell)
            cur = i
    return cells, cur

nb = [["code", "import pandas as pd"], ["code", "df = pd.read_csv('orders_3m.csv')"]]
press(nb, 1, ["B", "M"])
```

### explain
Модель показывает, почему клавиши ведут себя так, как ведут: <kbd>A</kbd> не двигает курсор, потому что новая ячейка встаёт на его место; <kbd>Z</kbd> — это стопка: две отмены подряд возвращают ячейки в обратном порядке удаления. Тонкое место — удаление последней ячейки: без `min(cur, len(cells) - 1)` курсор укажет за конец списка, и следующее <kbd>M</kbd> упадёт с `IndexError`. Вторая ловушка — изменить исходный список: строка `cells = [list(c) for c in cells]` копирует и список, и каждую ячейку внутри.
