---
title: "Блокнот в git и портфолио на GitHub"
lead: "Репозиторий с историей уже есть — пора сделать так, чтобы его было не стыдно показать. Учим git дружить с блокнотами (выводы и номера запусков засоряют diff), выкладываем проект на GitHub с README и issue и заводим привычку: каждый проект курса — в портфолио."
files: [zerno_draft.ipynb, zerno_rerun.ipynb]
recap:
  - "В `.ipynb` выводы и номера запусков меняются при каждом перезапуске и засоряют diff. `nbstripout --install` вырезает их при коммите."
  - "`git remote add origin <адрес>` и `git push -u origin main` — выложить на GitHub. README — лицо проекта: вопрос, данные, главные цифры, как запустить."
  - "Привычка: каждый проект курса — отдельный репозиторий с README, `.gitignore`, `pyproject.toml` и блокнотом, прошедшим Restart & Run All."
  - "Вложенный объект (JSON блокнота, словарь со списками), который будут менять, копируют через `copy.deepcopy`: `.copy()` копирует только верхний уровень."
  - "Issue — задача в репозитории с номером; `Fixes #3` в подписи коммита закрывает её после `push` в `main`."
---

Репозиторий, коммиты, история и `.gitignore` — из урока «Git: коммиты, история, ветки и .gitignore». Здесь продолжим с того же проекта `zerno-analytics`.

## Блокнот в git: выводы шумят

Зачем: вы исправили одну строку в блокноте, перезапустили его и смотрите `git diff`. А там десятки изменённых строк: номера запусков, выводы, ошибки. Найти среди них свою правку трудно.

Причина — в устройстве `.ipynb` (урок про Jupyter): это JSON, где вместе с кодом лежат `outputs` и `execution_count`. Возьмём черновик `zerno_draft.ipynb` и его же после исправления пути и Restart & Run All — `zerno_rerun.ipynb`. В коде поменялась **одна строка**. Посмотрим, что увидит git:

```python
import difflib

old = open("zerno_draft.ipynb", encoding="utf-8").read().splitlines()
new = open("zerno_rerun.ipynb", encoding="utf-8").read().splitlines()

diff = list(difflib.unified_diff(old, new, lineterm=""))
changed = [l for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---"))]
print(len(changed), "изменённых строк JSON")
for l in changed[:6]:
    print(l)
```

Что здесь происходит:

- `difflib.unified_diff` строит такой же diff, как git: строки с `-` и `+`;
- `changed` — только изменённые строки, без заголовков `+++` и `---`;
- печатаем первые шесть, чтобы увидеть, что именно изменилось.

Как читать результат: 14 изменённых строк, а по существу правка одна — путь к файлу. Остальное — номера запусков и выводы. В настоящем проекте с графиками (картинка внутри JSON — тысячи символов) шум ещё больше.

::: figure nb-strip
Сверху — из чего состоят 14 изменённых строк: 2 строки кода (путь «было» и «стало»), 8 строк номеров запуска и 4 строки выводов. Снизу — как это лечит nbstripout (о нём ниже): при `git add` фильтр вырезает выводы и номера, и в коммит уходит только код.
:::

**Что с этим делать.**

1. **nbstripout** — вырезает выводы и номера запусков при каждом коммите. Файл на диске остаётся с выводами, а в историю уходит только код и текст:

   ```sh
   uv add --dev nbstripout
   uv run nbstripout --install      # настроить git в этом репозитории
   ```

2. **Разово** очистить выводы: `uv run jupyter nbconvert --clear-output --inplace report.ipynb`.
3. **Сравнивать блокноты по-человечески** умеет `nbdime` (`nbdiff old.ipynb new.ipynb`) и встроенный diff в VS Code.

А как же портфолио? GitHub показывает `.ipynb` как страницу — с таблицами и графиками, но только если выводы сохранены. Рабочее правило: в рабочем репозитории команды — nbstripout; в репозитории-портфолио фильтр не ставят, а финальную версию коммитят **только после Restart & Run All**. Тогда номера идут 1, 2, 3…, выводы свежие, и diff между версиями остаётся честным.

::: warn Типичные ошибки
- **Коммит блокнота, который запускали вразнобой.** В историю уйдут выводы, не соответствующие коду, — та самая выручка 710 195 ₽ вместо 128 198 ₽.
- **«nbstripout стёр мои графики».** Команда `nbstripout файл.ipynb`, запущенная вручную, чистит сам файл на диске. Фильтр после `--install` работает иначе: чистит только то, что уходит в коммит, а ваш файл не трогает.
- **Конфликт слияния в `.ipynb`.** Два человека правили один блокнот в разных ветках — JSON сливается плохо. Договоритесь: один блокнот — один автор, общий код — в `.py`.
:::

::: note Сделайте в своём терминале
1. В своём проекте выполните `uv add --dev nbstripout` и `uv run nbstripout --install`.
2. Перезапустите блокнот, выполните `git diff` — изменений в выводах там быть не должно.
3. Поменяйте одну строку кода и снова `git diff` — теперь видна только она.
:::

### Почему копию блокнота делают через deepcopy

Если очищать блокнот кодом (так вы сделаете в задаче), нужна его копия — исходник портить нельзя. Но блокнот из `json.load` — это **вложенные** словари и списки, а обычная копия `nb.copy()` копирует только верхний уровень. Вложенные списки остаются общими у копии и оригинала: меняете ячейки копии — меняются ячейки оригинала.

```python
import copy

nb = {"cells": [{"outputs": ["710195"]}]}
shallow = nb.copy()                       # копия только верхнего словаря
shallow["cells"][0]["outputs"] = []       # чистим «копию»…
print(nb["cells"][0]["outputs"])          # …а пустой стал и оригинал

nb = {"cells": [{"outputs": ["710195"]}]}
deep = copy.deepcopy(nb)                  # копия со всеми вложенными списками
deep["cells"][0]["outputs"] = []
print(nb["cells"][0]["outputs"])          # оригинал цел
```

Что здесь происходит:

- `nb.copy()` создаёт новый словарь, но значение `"cells"` в нём — **тот же самый** список, что в `nb`. Это как два ярлыка на одну папку;
- `copy.deepcopy(nb)` проходит по всем уровням и копирует каждый список и словарь. Модуль `copy` встроен в Python.

Правило: если объект вложенный (словарь со списками, JSON, список списков) и копию будут менять — `copy.deepcopy`.

{{practice: strip, diff-noise}}

## GitHub: push, README и issue

Зачем: локальная история защищает от «что я поменял», но не от сгоревшего ноутбука. А ещё её не видят коллеги и работодатель. **GitHub** — сайт, где хранится копия репозитория и где его можно показать.

Выложить проект:

1. Зарегистрируйтесь на github.com и создайте **пустой** репозиторий `zerno-analytics` (без README — он уже есть у вас).
2. Свяжите папку с ним и отправьте историю:

```sh
git remote add origin https://github.com/<ваш-логин>/zerno-analytics.git
git push -u origin main
```

`origin` — короткое имя удалённого репозитория, `-u` запоминает связь, и дальше достаточно `git push`. Пароль GitHub для `push` не подойдёт — нужен вход через одну из программ:

- **GitHub CLI** — команда `gh`. Поставить: на Mac `brew install gh`, на Windows `winget install GitHub.cli` в PowerShell (затем откройте терминал заново). Войти: `gh auth login` — команда задаст пару вопросов и откроет браузер для подтверждения. С `gh` репозиторий создаётся и выкладывается одной командой: `gh repo create zerno-analytics --public --source=. --push`.
- **GitHub Desktop** — программа с окнами вместо команд (desktop.github.com). Войдите в ней в свой аккаунт, и `git push` из терминала тоже заработает.

**README.md** — первое, что видит человек, открывший репозиторий. Хороший README аналитического проекта:

```text
# Итоги осени сети «Зерно»

## Вопрос
За счёт чего выросла выручка ноября и какие кофейни работают эффективнее?

## Данные
2089 заказов 6 кофеен за сентябрь–ноябрь 2026. Файлы не в репозитории:
скачайте orders_3m.csv, shops.csv, menu.csv и положите в data/.

## Главное
- Выручка ноября +9.6 % к октябрю: заказов +5.4 %, средний чек +4.0 %.
- Лидер по выручке на посадочное место — PRM-1.

## Как запустить
uv sync
uv run jupyter lab   # открыть report.ipynb
```

Порядок важен: сначала вопрос и результат, потом технические детали. Работодатель смотрит README 30 секунд.

**Issue** — задача или замечание внутри репозитория: «Проверить рост чека в декабре», «Ревьюер: нет вывода после раздела 3». У каждой issue есть номер. Если в подписи коммита написать `Fixes #3`, после `push` в `main` GitHub сам закроет задачу 3 и свяжет её с коммитом. Так история проекта рассказывает не только *что* поменяли, но и *зачем*.

::: quiz
После первого `push` вы поправили README прямо на сайте GitHub. Потом дома закоммитили правку блокнота и выполнили `git push`. Git ответил `! [rejected] main -> main (fetch first)`. Что делать?

- [x] Забрать коммит с GitHub командой `git pull --rebase`, затем снова `git push`
  > На GitHub есть коммит с правкой README, которого нет у вас. `git pull --rebase` скачивает его и ставит ваш коммит поверх; после этого `push` проходит. Просто `git pull` в свежих версиях git остановится с `Need to specify how to reconcile divergent branches` — он просит выбрать способ соединения, `--rebase` и есть такой выбор.
- [ ] `git push --force`
  > Сработает, но затрёт историю на GitHub: коммит с правкой README пропадёт. В общем репозитории так можно стереть чужую работу.
- [ ] Удалить папку `.git` и начать заново
  > Вся ваша локальная история пропадёт, а проблема останется: на GitHub по-прежнему есть коммит, которого нет у вас.
- [ ] Сделать ещё один `git commit` и повторить `push`
  > Новый коммит не добавит в вашу историю коммит с GitHub — отказ повторится.
:::

::: warn Типичные ошибки
- **`rejected … fetch first` при push.** На GitHub есть коммиты, которых нет у вас: например, README поправили на сайте. Сначала `git pull --rebase`, потом `git push`. Если же репозиторий создали на сайте с галочкой «Add a README», у него своя, отдельная история, и `pull` упрётся в конфликт двух README. Проще удалить такой репозиторий на GitHub и создать заново пустым.
- **README из одной строки «Проект по курсу».** Без вопроса и результатов репозиторий для работодателя пустой.
- **Данные и `.env` на GitHub.** Проверьте `git status` и `.gitignore` *до* первого `push` — потом будет поздно.
:::

::: note Сделайте в своём терминале
1. Поставьте `gh` (`brew install gh` или `winget install GitHub.cli`) и войдите: `gh auth login`. Или поставьте GitHub Desktop и войдите в нём.
2. Создайте пустой репозиторий на сайте и выполните `git remote add origin …` и `git push -u origin main`. Обновите страницу репозитория — коммиты на месте.
3. Допишите в README разделы «Вопрос», «Данные», «Главное», «Как запустить», сделайте коммит и `git push`.
4. Заведите на GitHub issue «Добавить вывод по часам пик» и закройте её коммитом с подписью `… Fixes #1` (номер — ваш).
:::

{{practice: p-first-commit, readme}}

## Привычка: каждый проект — в портфолио

С этого урока каждый проект курса выкладывается в репозиторий: проект главы 2 про три месяца продаж, затем проекты следующих глав. К концу курса у вас будет 10+ репозиториев с настоящим анализом. Это сильнее любой строчки «знаю pandas» в резюме.

Что должно быть в каждом репозитории-проекте:

| файл | зачем |
|---|---|
| `README.md` | вопрос, данные, 2–4 главных вывода с цифрами, как запустить |
| `.gitignore` | `.venv/`, `data/`, `.ipynb_checkpoints/`, `.env` |
| `pyproject.toml` и `uv.lock` | точные версии библиотек — `uv sync` поставит то же самое |
| `report.ipynb` | блокнот-отчёт после Restart & Run All, с выводами |
| `report.html` (по желанию) | экспорт для тех, у кого нет Jupyter |

Чего в репозитории быть **не должно**: данных с персональной информацией, `.env`, папки `.venv`, файлов вида `Untitled3.ipynb` и `report_old_v2.ipynb` — для старых версий есть история.

::: tip
На GitHub в профиле можно закрепить до шести репозиториев (**Customize your pins**). Закрепите лучшие проекты, а у каждого заполните описание (**About**) одной фразой с результатом: «Разбор осенних продаж сети кофеен: +9.6 % за счёт заказов и чека».
:::

::: note Сделайте в своём терминале
1. Создайте репозиторий для проекта главы 2 «Три месяца продаж» — блокнот по шаблону из урока «Проект: три месяца продаж».
2. Добавьте `.gitignore`, README по образцу и `uv.lock`; выполните Restart & Run All.
3. Сделайте коммит, выложите на GitHub и откройте страницу репозитория — блокнот должен показываться с таблицами.
4. Заведите issue «Проверить рост чека в декабре» — это задел для следующей итерации.
:::

{{practice: portfolio}}

## Практика

## task: strip | Свой nbstripout | base

Сделайте то же, что nbstripout: из черновика `zerno_draft.ipynb` получите `clean` — копию блокнота, где у каждой **кодовой** ячейки `outputs` — пустой список, а `execution_count` — `None`. Markdown-ячейки и всё остальное не меняйте; исходный `nb` должен остаться прежним. Сохраните `n_removed` — сколько выводов удалено всего.

### starter
```python
import copy
import json

nb = json.load(open("zerno_draft.ipynb", encoding="utf-8"))

```

### check
```python
import json as _j
src = _j.load(open('zerno_draft.ipynb', encoding='utf-8'))
nb_, cl = need('nb', dict), need('clean', dict)
assert nb_ == src, 'Исходный nb изменился. Сделайте глубокую копию: copy.deepcopy(nb) — обычная копия словаря делит с оригиналом вложенные списки.'
assert len(cl['cells']) == len(src['cells']), 'Число ячеек в clean не должно меняться.'
for a, b in zip(cl['cells'], src['cells']):
    if b['cell_type'] == 'code':
        assert a['outputs'] == [] and a['execution_count'] is None, 'У кодовых ячеек outputs = [] и execution_count = None.'
        assert a['source'] == b['source'], 'Код ячеек трогать нельзя.'
    else:
        assert a == b, 'Markdown-ячейки должны остаться как были.'
assert cl['metadata'] == src['metadata'], 'metadata блокнота не меняйте.'
assert need('n_removed') == sum(len(c.get('outputs', [])) for c in src['cells']), f'n_removed = {need("n_removed")}. Посчитайте выводы до очистки.'
```

### hint
`clean = copy.deepcopy(nb)` — независимая копия со всеми вложенными списками. Дальше цикл по `clean["cells"]`.

### hint
Внутри цикла: `if cell["cell_type"] == "code":` — сначала прибавьте `len(cell["outputs"])` к счётчику, потом обнулите поля.

### solution
```python
import copy
import json

nb = json.load(open("zerno_draft.ipynb", encoding="utf-8"))

clean = copy.deepcopy(nb)
n_removed = 0
for cell in clean["cells"]:
    if cell["cell_type"] == "code":
        n_removed += len(cell["outputs"])
        cell["outputs"] = []
        cell["execution_count"] = None
print(n_removed)
```

### explain
Ушли два вывода: устаревшее число 710 195 и ошибка `KeyError`. Именно они и номера запусков меняются при каждом перезапуске, а код остаётся. Если вместо `copy.deepcopy` написать `clean = nb.copy()` или `dict(nb)`, скопируется только верхний словарь, а список ячеек останется общим — и очистка `clean` молча испортит `nb`. Проверка ловит именно это.

## task: diff-noise | Шум до и после очистки | plus

Сравните черновик и его перезапуск (`zerno_rerun.ipynb`) так, как это сделал бы git. Посчитайте `raw_changed` — сколько строк изменилось в исходных файлах, и `clean_changed` — сколько изменится, если оба блокнота сначала очистить от выводов и номеров запусков, а потом записать в JSON через `json.dumps(…, ensure_ascii=False, indent=1)`. Изменённая строка — строка unified diff, которая начинается с `+` или `-`, кроме заголовков `+++` и `---`.

### starter
```python
import copy
import difflib
import json

def changed_lines(a, b):
    ...

def strip(nb):
    ...

old = open("zerno_draft.ipynb", encoding="utf-8").read()
new = open("zerno_rerun.ipynb", encoding="utf-8").read()

```

### check
```python
import json as _j, difflib as _d, copy as _c
def _ch(a, b):
    return sum(1 for l in _d.unified_diff(a, b, lineterm='') if l[:1] in '+-' and not l.startswith(('+++', '---')))
def _s(nb):
    nb = _c.deepcopy(nb)
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            c['outputs'] = []; c['execution_count'] = None
    return nb
o = open('zerno_draft.ipynb', encoding='utf-8').read(); n = open('zerno_rerun.ipynb', encoding='utf-8').read()
raw = _ch(o.splitlines(), n.splitlines())
cl = _ch(_j.dumps(_s(_j.loads(o)), ensure_ascii=False, indent=1).splitlines(), _j.dumps(_s(_j.loads(n)), ensure_ascii=False, indent=1).splitlines())
assert need('raw_changed') == raw, f'raw_changed = {need("raw_changed")}, а нужно {raw}. Сравнивайте списки строк исходных файлов; заголовки +++ и --- не считайте.'
assert need('clean_changed') == cl, f'clean_changed = {need("clean_changed")}, а нужно {cl}. Очистите оба блокнота, превратите в текст через json.dumps(..., ensure_ascii=False, indent=1) и сравните построчно.'
assert calls('unified_diff') >= 1, 'Сравнивайте через difflib.unified_diff, как git.'
```

### hint
`changed_lines(a, b)` получает два списка строк: `difflib.unified_diff(a, b, lineterm="")` и подсчёт строк на `+`/`-` без `+++`/`---` — как в задаче про `git diff`.

### hint
`strip(nb)` — то же, что в прошлой задаче: `copy.deepcopy`, затем обнулить `outputs` и `execution_count` у кодовых ячеек, вернуть копию.

### hint
Чистый текст: `json.dumps(strip(json.loads(old)), ensure_ascii=False, indent=1).splitlines()`; то же для `new`, затем `changed_lines(...)`.

### solution
```python
import copy
import difflib
import json

def changed_lines(a, b):
    diff = difflib.unified_diff(a, b, lineterm="")
    return sum(1 for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---")))

def strip(nb):
    nb = copy.deepcopy(nb)
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
    return nb

old = open("zerno_draft.ipynb", encoding="utf-8").read()
new = open("zerno_rerun.ipynb", encoding="utf-8").read()

raw_changed = changed_lines(old.splitlines(), new.splitlines())
as_text = lambda s: json.dumps(strip(json.loads(s)), ensure_ascii=False, indent=1).splitlines()
clean_changed = changed_lines(as_text(old), as_text(new))
print(raw_changed, clean_changed)
```

### explain
Было 14 изменённых строк, осталось 2: одна строка с `-` и одна с `+` — старый и новый путь к файлу. Ровно эту правку аналитик и сделал, а остальные 12 строк — номера запусков и выводы. Так nbstripout превращает diff блокнота из шума в понятную историю. Важно сравнивать оба файла, записанные одинаково (`indent=1`, `ensure_ascii=False`): если записать их по-разному, diff покажет разницу в форматировании, а не в содержании.

## task: p-first-commit | Первый коммит и push | warmup

Строки ниже собирают в список `cmds` команды для нового проекта: создать репозиторий, сохранить первую версию и выложить её на GitHub. Расставьте их в правильном порядке.

### parsons
```python
cmds = []
cmds.append("git init")
cmds.append("git status")
cmds.append("git add README.md .gitignore report.ipynb")
cmds.append('git commit -m "Первая версия отчёта"')
cmds.append("git remote add origin https://github.com/anya/zerno-analytics.git")
cmds.append("git push -u origin main")
print(len(cmds))
```

### check
```python
c = need('cmds', list)
assert len(c) == 6, f'Команд {len(c)}, а нужно 6: строка cmds = [] — первая, print — последний.'
assert c[0] == 'git init', 'Сначала репозиторий нужно создать.'
pos = {x.split()[1]: i for i, x in enumerate(c)}
assert pos['add'] < pos['commit'], 'Коммит забирает только то, что добавлено в индекс: add — раньше commit.'
assert pos['status'] < pos['add'], 'Посмотрите, что изменилось, до того как добавлять: status — перед add.'
assert pos['commit'] < pos['push'] and pos['remote'] < pos['push'], 'Отправлять на GitHub можно только готовые коммиты и только когда указан адрес (remote).'
assert c.index('git push -u origin main') == 5, 'push — последний шаг.'
```

### hint
Сначала репозиторий создают, потом смотрят, что в папке, потом отбирают файлы, сохраняют версию, указывают адрес GitHub и отправляют.

### hint
`init` → `status` → `add` → `commit` → `remote add` → `push`.

## task: readme | README из словаря | base

Напишите `make_readme(info)` — функцию, которая собирает текст README из словаря с ключами `title`, `question`, `data`, `findings` (список строк) и `run` (список команд). Формат — строки, соединённые `\n`:

```text
# {title}

## Вопрос
{question}

## Данные
{data}

## Главное
- {finding 1}
- {finding 2}

## Как запустить
    {команда 1}
    {команда 2}
```

Команды — с отступом в 4 пробела (так Markdown покажет их как код). Соберите `readme` для словаря `autumn`.

### starter
```python
autumn = {
    "title": "Итоги осени сети «Зерно»",
    "question": "За счёт чего выросла выручка ноября?",
    "data": "2089 заказов 6 кофеен за сентябрь–ноябрь; файлы — в папке data/, в репозиторий не входят.",
    "findings": ["Выручка ноября +9.6 % к октябрю.", "Заказов +5.4 %, средний чек +4.0 %."],
    "run": ["uv sync", "uv run jupyter lab"],
}

def make_readme(info):
    ...

readme = make_readme(autumn)
print(readme)
```

### check
```python
def _mk(i):
    L = [f"# {i['title']}", '', '## Вопрос', i['question'], '', '## Данные', i['data'], '', '## Главное']
    L += [f'- {x}' for x in i['findings']]
    L += ['', '## Как запустить'] + [f'    {c}' for c in i['run']]
    return '\n'.join(L)
f = need('make_readme')
assert need('readme', str) == _mk(need('autumn')), 'readme не совпадает с образцом. Сравните построчно: пустые строки между разделами, «- » перед выводами, 4 пробела перед командами, без пустой строки в конце.'
other = {'title': 'Тест', 'question': 'Q?', 'data': 'D.', 'findings': ['один', 'два', 'три'], 'run': ['make']}
assert f(other) == _mk(other), f'На другом словаре функция даёт неверный текст: {f(other)!r}. Не вписывайте число выводов и команд — берите их из списков.'
```

### hint
Собирайте список строк и в конце склейте: `"\n".join(lines)`. Пустая строка между разделами — элемент `""`.

### hint
Выводы: `lines += [f"- {x}" for x in info["findings"]]`; команды: `[f"    {c}" for c in info["run"]]`.

### hint
Начало: `lines = [f"# {info['title']}", "", "## Вопрос", info["question"], "", "## Данные", info["data"], "", "## Главное"]`.

### solution
```python
autumn = {
    "title": "Итоги осени сети «Зерно»",
    "question": "За счёт чего выросла выручка ноября?",
    "data": "2089 заказов 6 кофеен за сентябрь–ноябрь; файлы — в папке data/, в репозиторий не входят.",
    "findings": ["Выручка ноября +9.6 % к октябрю.", "Заказов +5.4 %, средний чек +4.0 %."],
    "run": ["uv sync", "uv run jupyter lab"],
}

def make_readme(info):
    lines = [f"# {info['title']}", "", "## Вопрос", info["question"], "",
             "## Данные", info["data"], "", "## Главное"]
    lines += [f"- {x}" for x in info["findings"]]
    lines += ["", "## Как запустить"] + [f"    {c}" for c in info["run"]]
    return "\n".join(lines)

readme = make_readme(autumn)
print(readme)
```

### explain
Функция задаёт **структуру**, а содержание приходит из словаря — так README десятка проектов курса будут одинаково устроены, и читатель быстро найдёт главное. Порядок разделов выбран для читателя: вопрос и результат — раньше инструкций. Пустая строка перед `##` нужна Markdown: без неё в некоторых редакторах заголовок приклеится к предыдущему абзацу. Частая ошибка — склеивать через `+` и `"\n"` в каждой строке: легко потерять или задвоить перевод строки, а список + `join` от этого защищает.

## task: portfolio | Ревизия портфолио | plus

У вас три репозитория-проекта, у каждого — список файлов. Напишите `review(repos)` — функцию, которая возвращает словарь «имя репозитория → список проблем» (только для репозиториев с проблемами). Коды проблем, в таком порядке:

- `"no_readme"` — нет `README.md` в корне;
- `"no_gitignore"` — нет `.gitignore` в корне;
- `"no_notebook"` — нет ни одного `.ipynb` (в любой папке);
- `"secrets"` — есть файл с именем `.env` (в любой папке);
- `"data"` — есть файлы в папке `data/` в корне.

Посчитайте `problems` для словаря `repos`.

### starter
```python
repos = {
    "zerno-analytics": ["README.md", ".gitignore", "pyproject.toml", "uv.lock", "report.ipynb"],
    "zerno-cleaning": ["README.md", "cleaning.ipynb", "data/clients_raw.csv", ".env"],
    "zerno-sql": [".gitignore", "README.md", "queries/top_shops.sql", "config/.env"],
}

def review(repos):
    ...

problems = review(repos)
problems
```

### check
```python
def _rv(repos):
    out = {}
    for name, files in repos.items():
        names = [f.split('/')[-1] for f in files]
        p = []
        if 'README.md' not in files: p.append('no_readme')
        if '.gitignore' not in files: p.append('no_gitignore')
        if not any(f.endswith('.ipynb') for f in files): p.append('no_notebook')
        if '.env' in names: p.append('secrets')
        if any(f.startswith('data/') for f in files): p.append('data')
        if p: out[name] = p
    return out
f = need('review')
assert need('problems', dict) == _rv(need('repos')), f'problems = {need("problems")}, а нужно {_rv(need("repos"))}.'
t = {'a': ['docs/README.md', 'x.py'], 'b': ['README.md', '.gitignore', 'nb/a.ipynb', 'mydata/x.csv'], 'c': ['README.md', '.gitignore', 'r.ipynb', '.env.example']}
assert f(t) == _rv(t), f'review({t}) = {f(t)}, а нужно {_rv(t)}. README и .gitignore ищем только в корне; .env — точное имя; data/ — только папка в корне.'
```

### hint
Для каждого репозитория соберите список проблем по очереди, пятью `if`. В словарь результата добавляйте репозиторий, только если список не пуст.

### hint
«В корне» — точное совпадение пути: `"README.md" in files`. «В любой папке» — по имени файла: `f.split("/")[-1] == ".env"`. Блокнот — `f.endswith(".ipynb")`, данные — `f.startswith("data/")`.

### solution
```python
repos = {
    "zerno-analytics": ["README.md", ".gitignore", "pyproject.toml", "uv.lock", "report.ipynb"],
    "zerno-cleaning": ["README.md", "cleaning.ipynb", "data/clients_raw.csv", ".env"],
    "zerno-sql": [".gitignore", "README.md", "queries/top_shops.sql", "config/.env"],
}

def review(repos):
    result = {}
    for name, files in repos.items():
        names = [f.split("/")[-1] for f in files]
        p = []
        if "README.md" not in files:
            p.append("no_readme")
        if ".gitignore" not in files:
            p.append("no_gitignore")
        if not any(f.endswith(".ipynb") for f in files):
            p.append("no_notebook")
        if ".env" in names:
            p.append("secrets")
        if any(f.startswith("data/") for f in files):
            p.append("data")
        if p:
            result[name] = p
    return result

problems = review(repos)
problems
```

### explain
`zerno-analytics` в порядке. У `zerno-cleaning` нет `.gitignore`, и как следствие в репозиторий попали и пароли, и сырые данные клиентов — три проблемы из-за одного забытого файла. У `zerno-sql` нет блокнота, и `.env` лежит в подпапке `config/`: проверка только корня его бы пропустила, а боты на GitHub ищут такие файлы по всему репозиторию. Такую ревизию полезно делать перед тем, как отправить ссылку на портфолио работодателю.
