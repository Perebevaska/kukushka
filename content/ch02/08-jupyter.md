---
title: Своё рабочее место — uv и Jupyter
files: [orders_3m.csv, zerno_draft.ipynb, zerno_rerun.ipynb]
lead: "Браузерный Python курса удобен для учёбы, но настоящий анализ делают в Jupyter на своём компьютере. Ставим окружение одной командой и форматтер кода ruff, разбираемся, как устроен блокнот и что лежит в файле `.ipynb`, учимся не попадать в главную ловушку — порядок выполнения ячеек. Как собрать из блокнота отчёт, который читают сверху вниз, — в следующем уроке."
recap:
  - "uv — менеджер Python-окружений: `uv init` — новый проект, `uv add pandas` — библиотека, `uv run jupyter lab` — запуск Jupyter."
  - "Блокнот (`.ipynb`) — ячейки кода и текста. <kbd>Shift</kbd>+<kbd>Enter</kbd> — выполнить ячейку и перейти к следующей."
  - "Файл `.ipynb` — это JSON: у каждой ячейки код (`source`), выводы (`outputs`) и номер запуска (`execution_count`). Вывод в файле — снимок прошлого запуска, а не результат текущего кода."
  - "Переменные живут в ядре, пока оно запущено, — в том порядке, в котором вы выполняли ячейки, а не в каком они стоят."
  - "Перед тем как отдать блокнот: **Restart Kernel and Run All Cells**. Если он прошёл сверху вниз без ошибок — блокнот воспроизводим."
  - "Пути к данным — относительные, от папки проекта: `pd.read_csv(\"data/orders_3m.csv\")`; собирать их удобно через `pathlib`: `Path(\"data\") / \"orders_3m.csv\"`."
---

## Зачем своё окружение

В курсе Python работает прямо в браузере — ничего ставить не нужно. Но у браузерного Python есть пределы: он медленнее, файлы живут только до закрытия вкладки, и не все библиотеки в нём доступны. Для настоящей работы аналитики используют **Jupyter** — блокноты, в которых код, результаты, таблицы, графики и пояснения лежат в одном файле.

Проекты курса, начиная с этой главы, сдаются именно блокнотом: так их проверяет ревьюер и так их увидит работодатель в вашем портфолио.

В своём окружении первым делом полезно знать, **какие версии** стоят: поведение библиотек меняется от версии к версии, и коллега с другой версией может получить другой результат. Версии видны из самого Python:

```python
import sys
import pandas as pd

print(sys.version)                                      # полная строка версии Python
print(sys.version_info.major, sys.version_info.minor)   # те же части числами: 3 и 12, например
print(pd.__version__)                                   # версия pandas
```

Что здесь происходит:

- `sys` — встроенный модуль со сведениями о самом Python; ставить его не нужно.
- `sys.version` — длинная строка вроде `3.12.7 (main, …)`; `sys.version_info` — та же версия по частям: `major` — главный номер (3), `minor` — второй (12).
- `pd.__version__` — версия pandas строкой. Такой атрибут есть почти у любой библиотеки.

{{practice: env}}

## Установка: uv

Самый простой способ поставить Python и библиотеки в 2026 году — **uv**. Он сам скачивает нужную версию Python, создаёт изолированное окружение для проекта и ставит библиотеки за секунды.

::: tip Аналогия
Окружение — как отдельная коробка с инструментами под каждый ремонт. В коробке для кухни лежат свои свёрла и свой клей, и, если вы купили для ванной новый клей, кухонный ремонт от этого не сломается. Где аналогия хромает: коробки uv почти ничего не весят — одинаковые библиотеки он хранит один раз и раздаёт по ссылкам.
:::

### Где вводить команды

Команды установки и создания проекта вводят не в Python, а в **терминал** — окно, где компьютеру пишут команды текстом.

- **Mac:** программа «Терминал» (<kbd>Cmd</kbd>+<kbd>Space</kbd>, наберите «Терминал»).
- **Windows:** PowerShell (<kbd>Win</kbd>+<kbd>X</kbd> → «Терминал» или «Windows PowerShell»). Команды `mkdir` и `cd` работают в нём так же, как на Mac. После установки uv закройте окно и откройте новое — иначе PowerShell ещё не знает команду `uv`.

Набрали команду — нажмите <kbd>Enter</kbd>. Подробнее о терминале — в уроке «Терминал и память: заглянуть в файл, не открывая его». А для этого урока хватит команд, которые показаны здесь.

### Установить uv

На Mac с Homebrew:

```text
brew install uv
```

На Mac без Homebrew:

```text
curl -LsSf https://astral.sh/uv/install.sh | sh
```

На Windows — в PowerShell:

```text
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Проект за пять команд

В терминале, по одной строке:

```text
mkdir zerno-analytics
cd zerno-analytics
uv init --python 3.12
uv add pandas duckdb matplotlib jupyterlab
uv run jupyter lab
```

Что произошло:

1. `mkdir` создал папку проекта, `cd` перешёл в неё — дальше все команды работают внутри этой папки. `uv init` создал проект: файл `pyproject.toml` со списком зависимостей и закрепил версию Python.
2. `uv add` поставил библиотеки в окружение проекта (папка `.venv`) и записал их в `pyproject.toml`. Так проект можно воспроизвести на другом компьютере командой `uv sync`.
3. `uv run jupyter lab` запустил Jupyter внутри этого окружения — откроется вкладка браузера.

::: figure uv-project
Что появляется в папке проекта и что из этого уходит коллеге. Описание окружения (`pyproject.toml`, `.python-version`, `uv.lock`) лёгкое и передаётся, а саму `.venv` коллега собирает у себя командой `uv sync`.
:::

Положите в проект папку `data` и скопируйте туда учебные файлы курса из `site/data/` (`orders_3m.csv`, `shops.csv`, `menu.csv`).

В коде путь к данным пишут **относительно папки проекта**: `pd.read_csv("data/orders_3m.csv")`, а не `/Users/имя/...` — тогда проект запустится у коллеги. Пути удобно собирать модулем `pathlib` — он сам ставит правильные разделители на Mac и Windows:

```python
from pathlib import Path
DATA = Path("data")
path = DATA / "orders_3m.csv"
print(path, path.name, path.suffix)
```

Что здесь происходит:

- `Path("data")` — путь к папке как объект, а не строка;
- `DATA / "orders_3m.csv"` — оператор `/` склеивает части пути: на Mac и Linux получится `data/orders_3m.csv`, на Windows — `data\orders_3m.csv`;
- `name` — имя файла с расширением, `suffix` — само расширение. У `Path` есть и другие части: папка (`parent`), имя без расширения и так далее.

::: tip
Каждому проекту — своё окружение. Тогда обновление библиотек в одном проекте не сломает другой. `uv` делает это по умолчанию.
:::

::: note
Вместо Jupyter Lab можно работать в **VS Code** с расширением Jupyter: те же блокноты, плюс подсказки кода. Выберите в правом верхнем углу блокнота ядро из `.venv` вашего проекта.
:::

### ruff: стиль наводит программа

В уроке «Функции» вы приводили код к PEP 8 руками. На своём компьютере это делает **ruff** — быстрый «форматтер» (переписывает оформление) и «линтер» (находит подозрительные места) для Python. Команды — для терминала:

```sh
uv tool install ruff         # установить один раз
ruff format отчёт.py         # переписать файл в едином стиле
ruff check отчёт.py          # найти проблемы, которые нельзя исправить форматированием
ruff format проект.ipynb     # то же для блокнота Jupyter
```

Возьмём функцию, оформленную против всех правил PEP 8, — файл `отчёт.py`:

```python static
def AvgCheck(Revenue,Orders):
  if Orders==0: return 0
  return round(Revenue/Orders,ndigits = 2)
print(AvgCheck(84530,260))
```

- `ruff format` сам расставляет пробелы и отступы, разбивает `if x: return 0` на две строки и добавляет пустые строки. После `ruff format` функция станет такой:

```python static
def AvgCheck(Revenue, Orders):
    if Orders == 0:
        return 0
    return round(Revenue / Orders, ndigits=2)


print(AvgCheck(84530, 260))
```

- Имена `ruff format` **не трогает**: переименовать `AvgCheck` — решение человека, а не программы. Подсказку даст `ruff check` с правилами об именах (`N`) и стиле (`E`). Для исходного файла **до** форматирования вывод такой:

```text
$ ruff check --select E,N --output-format concise отчёт.py
отчёт.py:1:5: N802 Function name `AvgCheck` should be lowercase
отчёт.py:1:14: N803 Argument name `Revenue` should be lowercase
отчёт.py:1:22: N803 Argument name `Orders` should be lowercase
отчёт.py:2:15: E701 Multiple statements on one line (colon)
Found 4 errors.
```

Как читать: `файл:строка:столбец: код описание`. `N802`/`N803` — имя функции или параметра не в snake_case; `E701` — две инструкции в одной строке. Часть замечаний `ruff check --fix` исправляет сам — например, удаляет неиспользуемый `import`.

В VS Code и PyCharm ruff подключается как расширение и форматирует файл при каждом сохранении — после этого о пробелах можно не думать вовсе.

::: warn Типичные ошибки
- **`jupyter: command not found`.** Jupyter стоит в окружении проекта, а не «в системе». Запускайте его через `uv run jupyter lab` из папки проекта.
- **`ModuleNotFoundError: No module named 'pandas'` в блокноте.** Блокнот работает с другим ядром — не из `.venv` проекта. В JupyterLab это видно в правом верхнем углу; в VS Code выберите ядро `.venv`.
- **Проект в папке «Загрузки».** Через месяц его не найти. Заведите одну папку для всех проектов, например `~/projects/`.
:::

::: note Сделайте в своём терминале
1. Поставьте uv и выполните пять команд выше.
2. Убедитесь, что в папке `zerno-analytics` появились `pyproject.toml` и `.venv`.
3. Создайте папку `data` и положите туда `orders_3m.csv`.
4. Запустите `uv run jupyter lab` и создайте блокнот **Python 3 (ipykernel)**.
:::

{{practice: path}}

## Как устроен блокнот

Зачем знать устройство: без него непонятно, почему блокнот «помнит» то, чего в нём уже нет, и что именно уйдёт коллеге, когда вы отправите файл.

Блокнот состоит из **ячеек** двух видов:

- **Code** — код. <kbd>Shift</kbd>+<kbd>Enter</kbd> выполняет ячейку; результат (последнее выражение — как в этом курсе) появляется под ней;
- **Markdown** — текст: заголовки `#`, списки, пояснения. Хороший блокнот читается как отчёт: что делаем, что получили, какой вывод.

Код выполняет **ядро** — запущенный процесс Python. Все переменные, которые вы создали, живут в ядре, пока его не перезапустят.

::: tip Аналогия
Блокнот — это листок с записями, а ядро — калькулятор с памятью. На листке видно, что вы *записали*, а в памяти калькулятора — то, что вы на самом деле *нажимали*. Сотрёте строчку на листке — число в памяти калькулятора останется. Где аналогия хромает: у ядра «ячеек памяти» сколько угодно, по одной на каждую переменную.
:::

### Что лежит в файле .ipynb

Файл блокнота — обычный текст в формате **JSON** (словари и списки, как в Python). Упрощённо одна кодовая ячейка выглядит так:

```text
{
  "cell_type": "code",
  "execution_count": 3,
  "source": ["df[\"amount\"].sum()"],
  "outputs": [{"output_type": "execute_result",
               "data": {"text/plain": ["710195"]}}]
}
```

У ячейки три главных поля:

| поле | что хранит | пример |
|---|---|---|
| `source` | текст ячейки — список строк | `["df[\"amount\"].sum()"]` |
| `execution_count` | номер запуска — тот самый `[3]` слева | `3`, у невыполненной ячейки `null` |
| `outputs` | вывод **последнего** запуска | число, таблица, картинка или ошибка |

Важное следствие: вывод сохраняется в файле вместе с кодом. Если код потом изменили, а ячейку не перезапустили, в файле останется старое число — и коллега увидит именно его.

::: figure nb-kernel
Две памяти блокнота. <kbd>Shift</kbd>+<kbd>Enter</kbd> отправляет `source` в ядро, а ответ записывается в `outputs` вместе с номером запуска. Файл и ядро дальше живут отдельно: в файле у ячейки 4 черновика — 710 195, а в ядре `df` уже отфильтрована до доставки.
:::

В данных урока лежит черновик аналитика `zerno_draft.ipynb` — блокнот, который запускали вразнобой. Прочитаем его как JSON:

```python
import json

with open("zerno_draft.ipynb", encoding="utf-8") as f:
    nb = json.load(f)             # весь блокнот — один словарь

print("формат:", nb["nbformat"], "· ячеек:", len(nb["cells"]))
for i, cell in enumerate(nb["cells"]):
    first = "".join(cell["source"]).splitlines()[0]     # первая строка ячейки
    n = cell.get("execution_count")                      # у markdown этого поля нет
    print(i, cell["cell_type"], n, first)
```

Что здесь происходит:

- `json.load(f)` читает файл и превращает JSON в обычный словарь Python;
- `nb["cells"]` — список ячеек сверху вниз, каждая ячейка — словарь;
- `"".join(cell["source"])` склеивает список строк в один текст, `.splitlines()[0]` берёт первую строку;
- `cell.get("execution_count")` — номер запуска; у markdown-ячеек такого поля нет, и `.get` вернёт `None` без ошибки.

Как читать результат: номера запуска идут 1, 2, 6, 3, 7 — ячейки выполняли не сверху вниз. Ячейка 6 не запускалась ни разу (`None`): весь её код закомментирован. А в выводе ячейки 4 лежит 710 195 ₽ — выручка **всей сети**, хотя выше стоит фильтр доставки. Её посчитали раньше фильтра (номер 3 меньше 6), и это число аналитик переписал в markdown-вывод в конце.

::: predict
```python static
import json
nb = json.load(open("zerno_draft.ipynb", encoding="utf-8"))
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
print(len(nb["cells"]), len(code))
```

- `8 8`
- [x] `8 6`
- `6 6`

Почему: в блокноте 8 ячеек, из них 2 markdown (заголовок и выводы) и 6 кодовых. Закомментированная ячейка — тоже кодовая.
:::

::: warn Типичные ошибки
- **«В файле написано 710 195 — значит, так и есть».** Вывод в `.ipynb` — снимок прошлого запуска. Верить можно только выводу после Restart & Run All.
- **Правка `.ipynb` руками в текстовом редакторе.** Одна лишняя запятая — и Jupyter не откроет файл. Читать JSON можно, править лучше в Jupyter.
- **Блокнот на 50 МБ.** В выводах сохранились огромные таблицы и графики. Печатайте `head()` и агрегаты, а не таблицу целиком.
:::

::: note Сделайте в своём блокноте
1. Скачайте `zerno_draft.ipynb` (плашка «Данные урока» вверху) и откройте его в JupyterLab — посмотрите на номера `[ ]` слева.
2. Откройте тот же файл как текст: правый клик → **Open With → Editor**. Найдите `"execution_count"` и `"outputs"`.
:::

{{practice: run-order, ipynb-json}}

## Главная ловушка: порядок выполнения

Ячейки можно выполнять в любом порядке и сколько угодно раз. Ядро помнит не «что написано в блокноте», а «что и в каком порядке вы выполнили». Номер `[5]` слева от ячейки — её порядковый номер выполнения.

Пример. Две ячейки:

```python static
# ячейка 1
x = 1
```

```python static
# ячейка 2
x = x + 1
print(x)
```

::: predict
```python static
x = 1        # выполнили ячейку 1
x = x + 1    # выполнили ячейку 2
x = x + 1    # и ещё раз ячейку 2
print(x)
```

- `2`
- [x] `3`
- `1`

Почему: ядро помнит все выполнения. Ячейку 2 запустили дважды — `x` увеличился дважды. В блокноте при этом видна только последняя версия вывода, и по коду этого не понять.
:::

Отсюда типичные беды:

- ячейку с загрузкой данных изменили, но не перезапустили — дальше считается по старым данным;
- переменную удалили из кода, но она живёт в ядре — у вас всё работает, у коллеги падает;
- результат зависит от того, сколько раз нажали <kbd>Shift</kbd>+<kbd>Enter</kbd>.

::: predict
```python static
# Kernel → Restart (ядро перезапущено, ячейки не выполнялись)
print(x)
```

- `3`
- `1`
- [x] `Ошибка NameError`

Почему: после перезапуска ядро чистое. `x` появится, только когда снова выполнят ячейку 1.
:::

::: warn
Перед тем как отправить блокнот или сделать выводы: **Kernel → Restart Kernel and Run All Cells**. Если блокнот прошёл сверху вниз без ошибок, результат воспроизводим. Это первое, что проверяет любой ревьюер.
:::

### Разберём вместе: блокнот, который «работал вчера»

Это тот самый черновик `zerno_draft.ipynb`. Номер ячейки здесь и выше — её индекс в `nb["cells"]`, как в выводе кода: счёт с нуля, markdown-ячейки тоже считаются.

| ячейка | тип | код | номер выполнения |
|---|---|---|---|
| 0 | markdown | `# Осень` | — |
| 1 | код | `import pandas as pd` | [1] |
| 2 | код | `df = pd.read_csv(…)` | [2] |
| 3 | код | `df = df[df["channel"] == "доставка"]` | [6] |
| 4 | код | `df["amount"].sum()` | [3] |
| 5 | код | `df.groupby("shop")["amount"].sum()` | [7] — ошибка |
| 6 | код | `# import matplotlib…` (всё закомментировано) | не запускалась |
| 7 | markdown | `## Выводы` … «710 195 ₽» | — |

1. Сначала он выполнил 1, 2 и 4 — получил выручку **всей сети**: 710 195 ₽ — и написал в выводах «выручка доставки — 710 195 ₽».
2. Потом дописал фильтр доставки в ячейку 3 и выполнил её [6]. Ячейку 4 он не перезапускал — её вывод остался старым.
3. После «Restart and Run All» ячейки идут по порядку, фильтр срабатывает раньше суммы, и ячейка 4 показывает 128 198 ₽ — выручку доставки. Код не менялся, менялся только порядок выполнения. Но вывод в тексте уже ушёл руководителю.

::: figure run-order
Пять выполненных кодовых ячеек, выстроенные по номерам запуска. Слева черновик: сумма [3] выполнена раньше фильтра [6] и посчитана по всей сети. Справа Restart & Run All: фильтр идёт раньше суммы, и получается выручка доставки.
:::

Тот же блокнот после исправления пути и перезапуска лежит в файле `zerno_rerun.ipynb` (он понадобится ещё и в уроке про git). Проверим цифры прямо по данным:

```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
all_ = df["amount"].sum()                                        # ячейка 4, выполненная ДО фильтра
delivery = df.loc[df["channel"] == "доставка", "amount"].sum()   # ячейка 4 ПОСЛЕ фильтра
print(all_, delivery, round(all_ / delivery, 1), round(delivery / all_ * 100, 1))
```

Что получилось: в отчёт ушло число в 5.5 раза больше настоящего — доставка даёт только 18.1 % выручки. Номера `[1]…[7]` слева выдают историю: если они идут не по порядку сверху вниз, блокнот надо перезапустить и проверить, что каждый вывод — тот, который вы собираетесь показывать. А фильтры лучше сохранять в новую переменную (`delivery = df[...]`), а не перезаписывать `df`: тогда повторный запуск ячейки ничего не испортит.

::: warn Типичные ошибки
- **Перезапись исходной таблицы.** `df = df[...]` при повторном запуске фильтрует уже отфильтрованное.
- **Абсолютные пути.** `C:/Users/…/orders.csv` или `/Users/anya/Downloads/…` не откроется у коллеги; путь — от папки проекта.
- **Блокнот без перезапуска перед отправкой.** Работает только у вас и только сейчас.
- **Числа в тексте вписаны руками.** После перезапуска код даёт 128 198, а в выводах всё ещё 710 195.
- **Библиотеки «где-то установлены».** Без `uv add` коллега не узнает, что нужно поставить, и какой версии.
:::

::: quiz
Блокнот у автора работал, а после «Restart & Run All» упал с `NameError`. Что, скорее всего, произошло?

- [x] Ячейки запускали не по порядку: переменная создавалась ниже места, где её используют, или в ячейке, которую потом удалили
  > Ядро помнило переменные из прошлых запусков. После перезапуска блокнот выполняется сверху вниз, и всё, что держалось «на памяти», ломается.
- [ ] Перезапуск стирает файлы с данными
  > Файлы на диске остаются. Сбрасывается только память ядра — переменные.
- [ ] В Jupyter нельзя создавать переменные в одной ячейке, а использовать в другой
  > Можно — ядро общее для всех ячеек. Важен только порядок выполнения.
- [ ] Не хватило оперативной памяти
  > Тогда была бы другая ошибка. `NameError` значит, что имени просто нет.
:::

::: note Сделайте в своём блокноте
1. Откройте `zerno_draft.ipynb`, исправьте путь на `data/orders_3m.csv`.
2. Выполните **Kernel → Restart Kernel and Run All Cells**. Сравните вывод ячейки 4 с текстом в «Выводах».
3. Исправьте блокнот: фильтр — в переменную `delivery`, `groupby` — по `shop_id`, вывод — из посчитанного числа.
:::

{{practice: p-order, fix-order, safe-filter, nb-audit}}

## Практика

## task: env | Отчёт об окружении | warmup

Напишите `env_report()`, которая возвращает словарь с версиями: `"python"` — строка вида `"3.14"` (major.minor) и `"pandas"` — `pd.__version__`. Такая ячейка полезна в начале любого блокнота.

### starter
```python
import sys
import pandas as pd

def env_report():
    ...

env_report()
```

### check
```python
import sys as _s, pandas as _pd
r = need('env_report')()
assert r == {'python': f'{_s.version_info.major}.{_s.version_info.minor}', 'pandas': _pd.__version__}, f'env_report() = {r}.'
```

### hint
Части версии Python лежат в `sys.version_info` (раздел «Зачем своё окружение»): `major` и `minor` — числа. Соберите из них строку f-строкой.

### hint
`return {"python": f"{v.major}.{v.minor}", "pandas": pd.__version__}`, где `v = sys.version_info`.

### solution
```python
import sys
import pandas as pd

def env_report():
    v = sys.version_info
    return {"python": f"{v.major}.{v.minor}", "pandas": pd.__version__}

env_report()
```

### explain
Такая ячейка в начале блокнота отвечает на первый вопрос при любой ошибке у коллеги: «а у тебя какая версия?». Поведение pandas меняется между версиями — например, тип текстовых столбцов в pandas 3 стал `str`.

## task: path | Путь к данным | base

Соберите путь к файлу через `pathlib`: в `path` должен оказаться путь `data/orders_3m.csv` (объект `Path`), а в `stem` — имя файла без расширения.

### starter
```python
from pathlib import Path
DATA = Path("data")

```

### check
```python
from pathlib import Path as _P
p = need('path')
assert isinstance(p, _P), f'path — {type(p).__name__}, а нужен Path. Соберите его через DATA / "имя".'
assert p.as_posix() == 'data/orders_3m.csv', f'path = {p}.'
assert need('stem') == 'orders_3m', f'stem = {need("stem")!r}.'
```

### hint
Оператор `/` у `Path` склеивает части пути — так путь работает и на Windows, и на Mac.

### hint
`path = DATA / "orders_3m.csv"`; имя без расширения — `path.stem`.

### solution
```python
from pathlib import Path
DATA = Path("data")
path = DATA / "orders_3m.csv"
stem = path.stem
```

### explain
`Path("data") / "orders_3m.csv"` даёт `data/orders_3m.csv` на Mac и Linux и `data\orders_3m.csv` на Windows — один и тот же код работает у всех. `stem` удобен, чтобы назвать файл результата по исходному: `orders_3m_clean.csv`.

## task: run-order | Порядок выполнения | warmup

В блокноте три ячейки: 1) `x = 10`, 2) `x = x * 2`, 3) `x = x + 5`. Сохраните в `top_down` значение `x`, если выполнить их сверху вниз, а в `shuffled` — если выполнить в порядке 1, 3, 2. Посчитайте кодом, повторив присваивания.

### starter
```python
# сверху вниз


# порядок 1, 3, 2

```

### check
```python
assert need('top_down') == 25, f'top_down = {need("top_down")}. Сверху вниз: 10 → 20 → 25.'
assert need('shuffled') == 30, f'shuffled = {need("shuffled")}. Порядок 1, 3, 2: 10 → 15 → 30.'
```

### hint
Повторите три присваивания в нужном порядке и сохраните результат: `x = 10`, `x = x * 2`, `x = x + 5`, `top_down = x`.

### hint
Для второго случая начните заново с `x = 10`, затем `+ 5`, затем `* 2`.

### solution
```python
x = 10
x = x * 2
x = x + 5
top_down = x

x = 10
x = x + 5
x = x * 2
shuffled = x
```

### explain
Одни и те же три ячейки дали 25 и 30. Ядро не знает, в каком порядке ячейки стоят в файле, — только в каком их выполнили. Поэтому финальная проверка любого блокнота — перезапуск и выполнение всех ячеек сверху вниз.

## task: ipynb-json | Заглянуть внутрь .ipynb | base

Прочитайте черновик `zerno_draft.ipynb` как JSON и сохраните:

- `n_md` и `n_code` — сколько в нём markdown- и кодовых ячеек;
- `counts` — список номеров запуска (`execution_count`) кодовых ячеек сверху вниз; у невыполненной ячейки — `None`;
- `in_order` — `True`, если номера выполненных ячеек (без `None`) строго растут сверху вниз, иначе `False`.

### starter
```python
import json

with open("zerno_draft.ipynb", encoding="utf-8") as f:
    nb = json.load(f)

```

### check
```python
import json as _j
_nb = _j.load(open('zerno_draft.ipynb', encoding='utf-8'))
_code = [c for c in _nb['cells'] if c['cell_type'] == 'code']
_cnt = [c['execution_count'] for c in _code]
assert need('n_md', int) == len(_nb['cells']) - len(_code), f'n_md = {need("n_md")}. Считайте ячейки с cell_type == "markdown".'
assert need('n_code', int) == len(_code), f'n_code = {need("n_code")}. Считайте ячейки с cell_type == "code".'
assert need('counts', list) == _cnt, f'counts = {need("counts")}. Нужны execution_count только кодовых ячеек, в порядке сверху вниз, вместе с None.'
_done = [x for x in _cnt if x is not None]
assert need('in_order') == all(a < b for a, b in zip(_done, _done[1:])), 'in_order посчитан неверно: сравните каждый номер со следующим (None пропустите).'
assert isinstance(need('in_order'), bool), 'in_order должен быть True или False.'
```

### hint
Ячейки — `nb["cells"]`, тип ячейки — `cell["cell_type"]`. Сначала отберите кодовые ячейки в отдельный список.

### hint
`counts = [c["execution_count"] for c in code_cells]`; выполненные — `done = [x for x in counts if x is not None]`.

### hint
Строго растут, если каждый следующий больше предыдущего: `in_order = all(a < b for a, b in zip(done, done[1:]))`.

### solution
```python
import json

with open("zerno_draft.ipynb", encoding="utf-8") as f:
    nb = json.load(f)

code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
n_code = len(code_cells)
n_md = len(nb["cells"]) - n_code
counts = [c["execution_count"] for c in code_cells]
done = [x for x in counts if x is not None]
in_order = all(a < b for a, b in zip(done, done[1:]))
print(n_md, n_code, counts, in_order)
```

### explain
Номера `[1, 2, 6, 3, 7, None]` — история черновика: ячейку с фильтром выполняли шестой, а сумму — третьей, то есть до фильтра. `in_order = False` — сигнал «перезапусти блокнот перед тем, как верить выводам». `zip(done, done[1:])` даёт пары соседей (1, 2), (2, 6), (6, 3), (3, 7) — на паре (6, 3) проверка и падает. Если забыть убрать `None`, сравнение `7 < None` упадёт с `TypeError`.

## task: p-order | Соберите блокнот по порядку | warmup

Строки ниже — ячейки блокнота, перемешанные при копировании. Расставьте их так, чтобы блокнот прошёл «Restart and Run All» и вывел выручку лучшей кофейни.

### parsons
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
by_shop = df.groupby("shop_id")["amount"].sum()
best = by_shop.idxmax()
print(best, by_shop[best])
```

### check
```python
import pandas as _pd
b = _pd.read_csv('orders_3m.csv').groupby('shop_id')['amount'].sum()
assert _lines == [f'{b.idxmax()} {b.max()}'], f'Сейчас: {_lines}'
```

### hint
Каждая ячейка использует только то, что создано выше неё.

### hint
Импорт → загрузка → группировка → выбор максимума → вывод.

## task: fix-order | Блокнот падает после перезапуска | base

У автора блокнот работал, а после «Restart and Run All» упал. Переставьте строки так, чтобы код выполнялся сверху вниз, ничего не удаляя и не меняя.

### starter
```python
avg_check = round(revenue / n, 2)
import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue = df["amount"].sum()
n = len(df)
print(avg_check)
```

### check
```python
import pandas as _pd
a = _pd.read_csv('orders_3m.csv')['amount']
assert close(need('avg_check'), round(a.sum() / len(a), 2)), f'avg_check = {need("avg_check")}.'
assert sorted(l.strip() for l in _code.strip().splitlines()) == sorted(['avg_check = round(revenue / n, 2)', 'import pandas as pd', 'df = pd.read_csv("orders_3m.csv")', 'revenue = df["amount"].sum()', 'n = len(df)', 'print(avg_check)']), 'Строки нужно только переставить — без изменений и удалений.'
```

### hint
Прочитайте ошибку: какой переменной Python не знает? Строка, которая её создаёт, должна стоять выше.

### hint
Цепочка зависимостей: `df` → `revenue` и `n` → `avg_check` → `print`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue = df["amount"].sum()
n = len(df)
avg_check = round(revenue / n, 2)
print(avg_check)
```

### explain
Ошибка `NameError` после перезапуска почти всегда значит «ячейка, создающая переменную, стоит ниже той, что её использует». У автора всё работало, потому что он когда-то выполнил нижнюю ячейку раньше — и ядро это помнило.

## task: safe-filter | Фильтр, который можно перезапускать | base

Ячейка `df = df[df["channel"] == "доставка"]` ломает блокнот при повторном запуске. Перепишите расчёт так, чтобы `df` оставался полным: сохраните доставку в `delivery`, посчитайте `revenue_all` и `revenue_delivery`. Затем «запустите ячейку дважды» — повторите строку фильтра ещё раз — и убедитесь, что `len(df)` не изменился: сохраните его в `n_rows`.

### starter
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")

```

### check
```python
import pandas as _pd
d = _pd.read_csv('orders_3m.csv')
assert need('n_rows') == len(d), f'n_rows = {need("n_rows")}, а в исходной таблице {len(d)} строк — df не должен меняться.'
assert need('revenue_all') == d['amount'].sum(), 'revenue_all — выручка всей таблицы.'
assert need('revenue_delivery') == d.loc[d['channel'] == 'доставка', 'amount'].sum(), 'revenue_delivery — выручка доставки.'
assert len(need('delivery', _pd.DataFrame)) == (d['channel'] == 'доставка').sum(), 'delivery — только строки доставки.'
```

### hint
Новое имя для отфильтрованной таблицы: `delivery = df[df["channel"] == "доставка"]`.

### hint
Повторите строку с `delivery` ещё раз — `df` при этом не меняется; `n_rows = len(df)`.

### solution
```python
import pandas as pd
df = pd.read_csv("orders_3m.csv")
delivery = df[df["channel"] == "доставка"]
delivery = df[df["channel"] == "доставка"]
revenue_all = df["amount"].sum()
revenue_delivery = delivery["amount"].sum()
n_rows = len(df)
```

### explain
Повторный запуск ячейки с новым именем безопасен: фильтр каждый раз применяется к полной `df`. Правило для блокнотов — исходные данные загружаются один раз и больше не перезаписываются; всё производное — в новые переменные.

## task: nb-audit | Ревьюер-робот | star

Напишите `audit(nb)` — функцию, которая проверяет блокнот (словарь из `json.load`) и возвращает список пар `(номер ячейки, проблема)` в порядке ячеек. Номер — индекс в `nb["cells"]`, считая и markdown. Проблемы:

- `"order"` — кодовая ячейка выполнена, но её номер запуска меньше, чем у какой-то выполненной ячейки выше;
- `"abs_path"` — в коде есть абсолютный путь: кавычка, сразу за ней `/` или буква диска с двоеточием (`"/Users/…`, `'C:/…`, `"D:\…`);
- `"error"` — среди выводов ячейки есть ошибка (`output_type == "error"`);
- `"commented"` — в ячейке есть непустые строки, и все они начинаются с `#`.

У одной ячейки может быть несколько проблем — тогда несколько пар, в порядке, как в списке выше. Проверка запустит функцию на обоих блокнотах урока: черновике и `zerno_rerun.ipynb`.

### starter
```python
import json
import re

def audit(nb):
    problems = []
    ...
    return problems

nb = json.load(open("zerno_draft.ipynb", encoding="utf-8"))
audit(nb)
```

### check
```python
import json as _j, re as _re
def _audit(nb):
    out, best = [], None
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] != 'code':
            continue
        src = ''.join(c['source'])
        n = c.get('execution_count')
        if n is not None:
            if best is not None and n < best:
                out.append((i, 'order'))
            best = n if best is None else max(best, n)
        if _re.search(r'["\'](/|[A-Za-z]:[\\/])', src):
            out.append((i, 'abs_path'))
        if any(o.get('output_type') == 'error' for o in c.get('outputs', [])):
            out.append((i, 'error'))
        lines = [l.strip() for l in src.splitlines() if l.strip()]
        if lines and all(l.startswith('#') for l in lines):
            out.append((i, 'commented'))
    return out
f = need('audit')
for name in ('zerno_draft.ipynb', 'zerno_rerun.ipynb'):
    nb = _j.load(open(name, encoding='utf-8'))
    got = [tuple(x) for x in (f(nb) or [])]
    assert got == _audit(nb), f'{name}: audit вернула {got}, а нужно {_audit(nb)}.'
_t = {'cells': [{'cell_type': 'code', 'execution_count': 2, 'source': ['x = 1'], 'outputs': []},
                {'cell_type': 'code', 'execution_count': 1, 'source': ["pd.read_csv('C:/data/a.csv')"], 'outputs': []},
                {'cell_type': 'code', 'execution_count': None, 'source': ['# старое\n', '\n', '# df.plot()'], 'outputs': []}]}
got = [tuple(x) for x in (f(_t) or [])]
assert got == _audit(_t), f'На маленьком тестовом блокноте audit вернула {got}, а нужно {_audit(_t)}: проверьте путь с буквой диска и пустые строки среди комментариев.'
```

### hint
Идите по `enumerate(nb["cells"])`, пропускайте markdown. Для `"order"` храните наибольший номер запуска среди выполненных ячеек выше: если текущий номер меньше — проблема.

### hint
Абсолютный путь ищется регулярным выражением: `re.search(r'["\'](/|[A-Za-z]:[\\/])', src)`, где `src = "".join(cell["source"])`.

### hint
Закомментированная ячейка: `lines = [l.strip() for l in src.splitlines() if l.strip()]`, затем `lines and all(l.startswith("#") for l in lines)`. Ошибка: `any(o["output_type"] == "error" for o in cell["outputs"])`.

### solution
```python
import json
import re

def audit(nb):
    problems = []
    best = None                                   # наибольший номер запуска выше текущей ячейки
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        n = cell.get("execution_count")
        if n is not None:
            if best is not None and n < best:
                problems.append((i, "order"))
            best = n if best is None else max(best, n)
        if re.search(r'["\'](/|[A-Za-z]:[\\/])', src):
            problems.append((i, "abs_path"))
        if any(o["output_type"] == "error" for o in cell["outputs"]):
            problems.append((i, "error"))
        lines = [l.strip() for l in src.splitlines() if l.strip()]
        if lines and all(l.startswith("#") for l in lines):
            problems.append((i, "commented"))
    return problems

nb = json.load(open("zerno_draft.ipynb", encoding="utf-8"))
audit(nb)
```

### explain
На черновике функция находит четыре проблемы: абсолютный путь (ячейка 2), сумму, посчитанную раньше фильтра (4), ошибку `KeyError` (5) и закомментированный код (6). После Restart & Run All (`zerno_rerun.ipynb`) порядок и путь исправлены, а ошибка и комментарии остались — перезапуск чинит историю, но не код. Примерно так работает и скрипт самопроверки проектов курса: он ищет в блокноте то же, что ищет живой ревьюер, только быстрее. Частая ошибка — сравнивать номер только с соседней ячейкой выше: если между ними есть невыполненная ячейка, нарушение пропадёт.

