---
title: "Git: коммиты, история, ветки и .gitignore"
lead: "«отчёт_финал_v3_точно_последний.ipynb» — знакомо? git хранит историю версий проекта: кто, когда и что поменял, и как вернуть вчерашний вариант. Разбираем основные команды — коммит, историю, diff и ветки — и учимся не пускать в репозиторий данные и пароли. Как выложить проект на GitHub — в следующем уроке."
recap:
  - "`git init` — новый репозиторий; `git add файл` — положить изменения в следующий коммит; `git commit -m \"что сделано\"` — сохранить версию."
  - "`git status` — что изменилось; `git log --oneline` — история; `git diff` — построчные изменения (`-` — было, `+` — стало)."
  - "`git switch -c ветка` — попробовать идею отдельно, `git merge ветка` — забрать результат в `main`."
  - "`.gitignore` — что git не трогает: `.venv/`, `data/`, `.ipynb_checkpoints/`, `.env` с паролями. Секрет, попавший в коммит, остаётся в истории — его меняют, а не просто удаляют."
---

## Первый репозиторий: init, add, commit

Зачем: блокнот «Итоги осени» вы правите неделю. Во вторник выручка доставки была 128 198 ₽, в четверг — другая. Что поменялось? Без истории версий ответ — «не помню». **git** запоминает каждую сохранённую версию проекта, и любую из них можно открыть, сравнить или вернуть.

::: tip Аналогия
git — как история версий в Google Docs, только версии вы сохраняете сами и каждую подписываете: «добавил выручку по месяцам». Но Google Docs сохраняет всё автоматически, а git — только то, что вы явно положили в версию. Зато каждая версия осмысленна.
:::

Словарик:

| слово | что значит |
|---|---|
| репозиторий | папка проекта, за которой следит git; история лежит в скрытой папке `.git` |
| коммит | сохранённая версия: снимок файлов + подпись + автор + время |
| хэш | номер коммита — 40 знаков, обычно показывают первые 7: `3efd677` |
| индекс (staging) | «коробка» изменений, которые уйдут в следующий коммит |
| ветка | отдельная линия истории; основная называется `main` |
| удалённый репозиторий | копия на сервере, например на GitHub |

**Три места, где живут изменения.** Это главное, что нужно понять про git.

1. **Рабочая папка** — файлы, как они лежат на диске прямо сейчас.
2. **Индекс** — то, что вы отобрали для следующего коммита командой `git add`.
3. **История** — коммиты, которые сделаны командой `git commit`.

::: figure git-areas
Три места на вашем компьютере и четвёртое — копия на GitHub (о ней — в уроке «Блокнот в git и портфолио на GitHub»). Сплошные стрелки двигают изменения вперёд, пунктирные возвращают назад. Буквы под блоками — то, что показывает `git status --short`, о нём ниже.
:::

::: tip Аналогия
Коммит — как посылка. `git add` кладёт вещь в коробку, `git commit -m "…"` заклеивает коробку и подписывает, что внутри. В коробку можно положить не всё, что лежит на столе: черновик заметок остаётся на столе, а отчёт уходит в посылку.
:::

Установка: на Mac — `xcode-select --install` (или `brew install git`), на Windows — **Git for Windows** с сайта git-scm.com (с ним приходит Git Bash). Один раз представьтесь — имя и почта попадут в каждый коммит:

```sh
git config --global user.name "Аня Петрова"
git config --global user.email "anya@example.com"
git config --global init.defaultBranch main
```

Последняя строка называет основную ветку новых репозиториев `main`, как на GitHub. Без этой настройки git версий 2.x называет её `master`, и команды урока с `main` не сработают.

Первый репозиторий в папке проекта. Пусть в ней для начала лежат два маленьких файла — заголовок будущего README и `.gitignore` (что это, разберём в разделе «.gitignore»). Создадим их прямо из терминала: `echo "текст" > файл` записывает строку в новый файл.

```sh
$ cd ~/projects/zerno-analytics
$ echo "# Итоги осени" > README.md
$ echo ".venv/" > .gitignore
$ git init
Initialized empty Git repository in ~/projects/zerno-analytics/.git/

$ git status
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.gitignore
	README.md

nothing added to commit but untracked files present (use "git add" to track)

$ git add README.md .gitignore
$ git commit -m "Структура проекта: README и .gitignore"
[main (root-commit) 8c3c173] Структура проекта: README и .gitignore
 2 files changed, 2 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 README.md
```

Что здесь происходит:

- два `echo` создали файлы по одной строке — отсюда в коммите `2 insertions(+)`;
- `git init` создал скрытую папку `.git` — в ней будет вся история;
- `git status` перечисляет новые файлы как **Untracked** — git их видит, но не следит за ними;
- `git add` положил оба файла в индекс;
- `git commit -m "…"` сохранил версию с подписью; `8c3c173` — начало её хэша, `root-commit` — первый коммит в истории. Этот же коммит будет самой нижней строкой истории в следующем разделе.

::: note Если папку создал `uv init`
В уроке «Своё рабочее место — uv и Jupyter» папку проекта создавала команда `uv init`. Если git к тому моменту уже стоял, uv сам сделал в ней `README.md`, `.gitignore` (в нём уже есть `.venv`) и репозиторий `.git`. Тогда пропустите оба `echo`, чтобы не затереть эти файлы, и `git init`: репозиторий уже есть. Начните с `git status` — в списке будут и `pyproject.toml`, `main.py`, ваш блокнот. Это нормально: добавьте их `git add` и сделайте первый коммит.
:::

Короткая форма статуса — `git status --short`. Две буквы слева: первая — что лежит в индексе, вторая — что изменено в рабочей папке, но не добавлено:

```text
 M report.py      изменён, но не добавлен в коммит
M  report.py      изменён и добавлен (git add)
A  README.md      новый файл, добавлен
?? notes.md       git за этим файлом не следит
```

Такой вывод удобно разбирать кодом — например, чтобы проверить, что в коммит не уходит ничего лишнего:

```python
status = """ M report.py
?? notes.md
A  README.md"""

for line in status.splitlines():
    staged, changed, path = line[0], line[1], line[3:]
    print(f"{path:10} в индексе: {staged!r}, в папке: {changed!r}")
```

Что здесь происходит:

- в каждой строке `--short` первые два символа — коды состояния, третий — пробел, дальше путь;
- `line[0]` — индекс, `line[1]` — рабочая папка, `line[3:]` — путь;
- пробел в коде значит «ничего»: у ` M report.py` индекс пуст, а файл изменён в папке.

Как читать результат: в коммит сейчас уйдёт только `README.md` — у него буква в первой колонке. `report.py` изменён, но не добавлен, а `notes.md` git вообще не отслеживает.

**Подпись коммита** читают через полгода, когда ищут, где сломалось. Плохо: `fix`, `1`, `правки`. Хорошо: «Фильтр доставки в отдельной переменной», «Выручка по месяцам». Одно изменение — один коммит.

::: quiz
Вы изменили `report.ipynb` и сразу выполнили `git commit -m "Выручка по месяцам"`. git ответил `no changes added to commit`. Почему?

- [x] Изменения не добавлены в индекс: перед коммитом нужен `git add report.ipynb`
  > Коммит забирает только то, что лежит в индексе. Изменённый файл в рабочей папке сам туда не попадает.
- [ ] Блокнот не сохранён в Jupyter
  > Тогда git просто не увидел бы изменений, но сообщение было бы другим — «nothing to commit, working tree clean».
- [ ] git не умеет работать с `.ipynb`
  > Умеет: для git это обычный текстовый файл в формате JSON.
- [ ] Подпись коммита должна быть на английском
  > Язык подписи не важен — главное, чтобы она была понятной.
:::

::: warn Типичные ошибки
- **`git add .` не глядя.** Точка добавляет всё, в том числе данные, `.env` с паролями и `.ipynb_checkpoints`. Сначала `.gitignore` и `git status`, потом `add`.
- **Коммит раз в неделю «всё сразу».** Его невозможно откатить по частям. Коммитьте каждый законченный шаг анализа.
- **`fatal: not a git repository`.** Вы не в папке проекта: проверьте `pwd`.
- **Коммиты от «root» или чужого имени.** Не выполнили `git config --global user.name/user.email`.
:::

::: note Сделайте в своём терминале
1. Представьтесь git и задайте ветку `main` по умолчанию — три команды `git config --global …` выше.
2. В папке проекта из урока про uv выполните `git init` и `git status`.
3. Создайте `README.md` с одной строкой `# Итоги осени`, выполните `git add README.md` и `git commit -m "README"`.
4. Посмотрите `git status --short` до и после `add`.
:::

{{practice: status-sim}}

## История и ветки: log, diff, switch

Зачем: «вчера выручка доставки была другой — что я поменял?». История коммитов и построчное сравнение отвечают на это за секунду.

`git log --oneline` — короткая история, сверху самый новый коммит:

```text
f0dd728 Выводы в README
a74c250 Слияние ветки loyalty
3e746ee Гипотеза: гости с картой тратят больше
5ae82cb Выручка по месяцам
3efd677 Фильтр доставки в отдельной переменной
375c1e4 Загрузка заказов и выручка
8c3c173 Структура проекта: README и .gitignore
```

Формат можно задать самому — например, хэш, дату, автора и подпись через `|`, чтобы потом прочитать в pandas:

```sh
git log --format="%h|%ad|%an|%s" --date=short
```

`git diff` показывает, что именно поменялось. Без аргументов — несохранённые изменения; `git diff 375c1e4 3efd677` — между двумя коммитами. Вот исправление фильтра доставки:

```text
diff --git a/report.py b/report.py
index fbaa5fc..40c6ec4 100644
--- a/report.py
+++ b/report.py
@@ -1,6 +1,7 @@
 import pandas as pd
 
 df = pd.read_csv("data/orders_3m.csv", parse_dates=["datetime"])
-df = df[df["channel"] == "доставка"]
-revenue = df["amount"].sum()
-print(revenue)
+delivery = df[df["channel"] == "доставка"]
+revenue_all = df["amount"].sum()
+revenue_delivery = delivery["amount"].sum()
+print(revenue_all, revenue_delivery)
```

Как читать diff:

1. `diff --git a/report.py b/report.py` — какой файл; `---` и `+++` — его версии «до» и «после»;
2. `@@ -1,6 +1,7 @@` — кусок файла: в старой версии 6 строк начиная с первой, в новой — 7;
3. строка с `-` — удалена, с `+` — добавлена, с пробелом — не менялась (это контекст).

Итого здесь 3 строки удалены и 4 добавлены. Именно так и видно, что «вчерашнее» число считалось по перезаписанной `df`.

::: predict
```python static
diff = """--- a/report.py
+++ b/report.py
@@ -1,2 +1,2 @@
-revenue = df["amount"].sum()
+revenue_all = df["amount"].sum()"""
print(sum(l.startswith("+") for l in diff.splitlines()))
```

- `1`
- [x] `2`
- `3`

Почему: с `+` начинается не только добавленная строка, но и заголовок `+++ b/report.py`. Считая изменения, заголовки `+++` и `---` нужно пропускать.
:::

Вернуть старое:

| команда | что делает |
|---|---|
| `git restore report.ipynb` | выбросить несохранённые изменения файла — вернуть, как в последнем коммите |
| `git restore --staged report.ipynb` | вынуть файл из индекса, сами правки остаются |
| `git show 3efd677` | показать коммит целиком |
| `git restore --source 375c1e4 report.py` | достать файл из старого коммита |

### Ветки

Хочется проверить гипотезу «гости с картой тратят больше», но не ломать рабочий отчёт. Для этого делают **ветку** — отдельную линию истории.

::: tip Аналогия
Ветка — как копия презентации «на попробовать»: вы правите копию, а основной файл, который видит руководитель, остаётся нетронутым. Удачные правки потом переносят в основной файл, неудачную копию просто бросают. Только git не копирует весь проект — ветка лишь отмечает, с какого коммита пошла отдельная линия, поэтому создаётся мгновенно.
:::

Команды:

```sh
git switch -c loyalty        # создать ветку loyalty и перейти в неё
# ... правки, git add, git commit ...
git switch main              # вернуться в main — файлы снова как были
git merge loyalty            # забрать коммиты ветки в main
```

`git log --oneline --graph` рисует это так:

```text
* f0dd728 Выводы в README
*   a74c250 Слияние ветки loyalty
|\  
| * 3e746ee Гипотеза: гости с картой тратят больше
|/  
* 5ae82cb Выручка по месяцам
* 3efd677 Фильтр доставки в отдельной переменной
* 375c1e4 Загрузка заказов и выручка
* 8c3c173 Структура проекта: README и .gitignore
```

::: figure git-branch
Тот же граф, развёрнутый слева направо: от коммита «по месяцам» отходит ветка `loyalty` с одним коммитом, а коммит слияния `a74c250` собирает обе линии обратно в `main`.
:::

Гипотеза не подтвердилась? Тогда ветку просто не сливают, и в `main` ничего не меняется.

Историю тоже можно разбирать кодом. Например, сколько коммитов и какой из них последний:

```python
log = """f0dd728 Выводы в README
a74c250 Слияние ветки loyalty
3e746ee Гипотеза: гости с картой тратят больше
5ae82cb Выручка по месяцам
3efd677 Фильтр доставки в отдельной переменной
375c1e4 Загрузка заказов и выручка
8c3c173 Структура проекта: README и .gitignore"""

commits = [line.split(" ", 1) for line in log.splitlines()]   # [хэш, подпись]
print(len(commits), commits[0])
print([h for h, msg in commits if "Гипотеза" in msg])
```

Что здесь происходит:

- `split(" ", 1)` режет строку по **первому** пробелу: слева хэш, справа вся подпись, даже если в ней много слов;
- `commits[0]` — первая строка лога, то есть самый новый коммит;
- генератор с условием находит хэши коммитов, в подписи которых есть слово «Гипотеза».

::: warn Типичные ошибки
- **Считать `+++` добавленной строкой.** Заголовки файла в diff начинаются с тех же знаков.
- **`git switch` с несохранёнными правками.** git откажется переключать ветку или перенесёт правки с собой. Сначала коммит.
- **`git restore` «на пробу».** Несохранённые изменения пропадут навсегда — их не было ни в одном коммите.
- **Первая строка `git log` — самый старый коммит.** Наоборот: самый новый.
:::

::: quiz
Вы поправили `report.ipynb`, выполнили `git add report.ipynb` и хотите перед коммитом посмотреть правку. `git diff` ничего не выводит. Что происходит?

- [x] Правки уже в индексе, а `git diff` без аргументов сравнивает рабочую папку с индексом. Изменения в индексе показывает `git diff --staged`
  > Три места изменений: `git add` перенёс правку из рабочей папки в индекс, и между ними разницы больше нет. `--staged` сравнивает индекс с последним коммитом.
- [ ] `git add` сохранил правку в историю, коммит больше не нужен
  > `git add` только кладёт изменения в «коробку». В историю они попадут после `git commit`.
- [ ] Файл не изменился: git сравнивает только код, а не выводы
  > git сравнивает весь текст файла, выводы тоже. Дело в том, с чем сравнивает `git diff`.
- [ ] Правка пропала, её надо вернуть `git restore report.ipynb`
  > Правка цела, она в индексе. `git restore report.ipynb` берёт файл из индекса, так что здесь ничего не изменит. Но в общем случае он выбрасывает несохранённые правки рабочей папки — с ним осторожно.
:::

::: note Сделайте в своём терминале
1. Сделайте ещё два коммита в своём проекте и посмотрите `git log --oneline`.
2. Поменяйте строку в README и посмотрите `git diff` до коммита.
3. Создайте ветку `git switch -c experiment`, сделайте в ней коммит, вернитесь в `main` и посмотрите `git log --oneline --graph --all`.
:::

{{practice: log-count, my-log, log-pandas, diff-stat}}

## .gitignore: что не кладут в репозиторий

Зачем: в папке проекта лежат файлы, которым не место в истории. Тяжёлые данные раздувают репозиторий навсегда. Персональные данные гостей нельзя публиковать. А пароль от базы данных в публичном репозитории найдут боты за минуты.

Файл `.gitignore` в корне проекта перечисляет шаблоны того, что git не должен замечать:

```text
# окружение и служебное
.venv/
__pycache__/
.ipynb_checkpoints/
.DS_Store

# данные — по ссылке в README, не в репозитории
data/
*.csv

# секреты: пароли, токены
.env
```

Правила шаблонов:

| шаблон | что игнорирует |
|---|---|
| `data/` | папку `data` целиком, где бы она ни лежала |
| `*.csv` | любой файл с окончанием `.csv` в любой папке |
| `.env` | файл с таким именем |
| `!sample.csv` | исключение из правил выше: этот файл всё-таки отслеживать |
| `# текст` | комментарий |

Похожие шаблоны с `*` и `?` понимает функция `fnmatch` из стандартной библиотеки Python:

```python
from fnmatch import fnmatch

for name in ["orders_3m.csv", "report.ipynb", ".env", "README.md"]:
    ignored = fnmatch(name, "*.csv") or fnmatch(name, ".env")
    print(f"{name:15} {'игнорируется' if ignored else 'в репозиторий'}")
```

Что здесь происходит:

- `fnmatch(имя, шаблон)` проверяет, подходит ли имя под шаблон: `*` — любые символы, `?` — один символ;
- имя игнорируется, если подошло хотя бы под один шаблон — отсюда `or`.

::: predict
```python static
from fnmatch import fnmatch
print(fnmatch("data/orders_3m.csv", "*.csv"))
```

- [x] `True`
- `False`
- `Ошибка ValueError`

Почему: в `fnmatch` звёздочка подходит под любые символы, включая `/`. Строка заканчивается на `.csv` — значит, подходит. В `.gitignore` шаблон `*.csv` тоже ловит csv-файлы в любой папке.
:::

**А где тогда данные?** Варианты: ссылка в README («скачайте `orders_3m.csv` отсюда и положите в `data/`»), маленький обезличенный образец (`!data/sample.csv`) или скрипт, который скачивает данные.

**Секреты** — пароли, токены, ключи — хранят в файле `.env`, который сразу вписан в `.gitignore`. В коде их читают из переменных окружения (`os.environ["DB_PASSWORD"]`), а не пишут строкой. Рядом кладут `.env.example` — тот же список имён, но без значений, чтобы коллега знал, что заполнить.

::: quiz
Аналитик закоммитил `.env` с паролем от базы и выложил на GitHub. Через час заметил, удалил файл и сделал новый коммит. Что теперь?

- [x] Пароль всё ещё в истории — его нужно срочно сменить, а `.env` добавить в `.gitignore`
  > Старый коммит с файлом никуда не делся: любой может открыть его по хэшу. Удаление из следующей версии не стирает прошлые, поэтому единственная надёжная мера — новый пароль.
- [ ] Всё в порядке: файла больше нет
  > Его нет в последней версии, но он есть в истории. Боты сканируют GitHub как раз в поисках таких коммитов.
- [ ] Достаточно сделать репозиторий приватным
  > Час он был публичным — пароль мог уже утечь. И доступ к приватному репозиторию тоже бывает у многих.
- [ ] Нужно удалить репозиторий и создать заново — тогда пароль менять не надо
  > Копии могли уже сделать. Скомпрометированный пароль меняют в любом случае.
:::

::: warn Типичные ошибки
- **`.gitignore` после первого коммита.** Файлы, которые git уже отслеживает, `.gitignore` не скрывает. Уберите их из индекса: `git rm --cached -r data/`, затем коммит.
- **Данные в репозитории «пока маленькие».** Через месяц там 300 МБ, а из истории их не выкинуть простым удалением.
- **Опечатка в шаблоне.** `.venv` без точки (`venv/`) не сработает. Проверяйте `git status` после правки `.gitignore` — лишнего там быть не должно.
:::

::: note Сделайте в своём терминале
1. Создайте `.gitignore` с шаблонами из примера.
2. Положите в `data/` файл `orders_3m.csv` и выполните `git status` — его там быть не должно.
3. Если данные уже попали в коммит: `git rm --cached -r data/` и новый коммит.
:::

{{practice: ignore}}

## Практика

## task: log-count | Читаем git log | warmup

Разберите вывод `git log --oneline` и сохраните: `n_commits` — сколько коммитов, `last_hash` — хэш самого нового коммита, `first_message` — подпись самого первого (старого) коммита.

### starter
```python
log = """f0dd728 Выводы в README
a74c250 Слияние ветки loyalty
3e746ee Гипотеза: гости с картой тратят больше
5ae82cb Выручка по месяцам
3efd677 Фильтр доставки в отдельной переменной
375c1e4 Загрузка заказов и выручка
8c3c173 Структура проекта: README и .gitignore"""

```

### check
```python
rows = [l.split(' ', 1) for l in need('log').splitlines()]
assert need('n_commits') == len(rows), f'n_commits = {need("n_commits")}. Одна строка лога — один коммит.'
assert need('last_hash') == rows[0][0], f'last_hash = {need("last_hash")!r}. Самый новый коммит в git log — сверху.'
assert need('first_message') == rows[-1][1], f'first_message = {need("first_message")!r}. Нужна подпись нижней строки целиком — без хэша.'
```

### hint
`log.splitlines()` — список строк; каждую режьте по первому пробелу: `line.split(" ", 1)`.

### hint
Самый новый — `lines[0]`, самый старый — `lines[-1]`.

### solution
```python
log = """f0dd728 Выводы в README
a74c250 Слияние ветки loyalty
3e746ee Гипотеза: гости с картой тратят больше
5ae82cb Выручка по месяцам
3efd677 Фильтр доставки в отдельной переменной
375c1e4 Загрузка заказов и выручка
8c3c173 Структура проекта: README и .gitignore"""

rows = [line.split(" ", 1) for line in log.splitlines()]
n_commits = len(rows)
last_hash = rows[0][0]
first_message = rows[-1][1]
print(n_commits, last_hash, first_message)
```

## task: my-log | Ваша история из терминала | base

Задачи в браузере проверяют, как вы читаете вывод git. Эта — что вы сами сделали коммиты. В своём проекте `zerno-analytics` сделайте **минимум два коммита** (раздел «Первый репозиторий»), затем выполните в терминале:

```sh
git log --oneline --no-decorate
```

Вставьте весь вывод в `my_log` между тройными кавычками. Сохраните `n_mine` — число ваших коммитов и `messages` — список их подписей сверху вниз (без хэшей).

### starter
```python
my_log = """
"""

```

### check
```python
import re as _re
_ls = [l.strip() for l in need('my_log', str).splitlines() if l.strip()]
assert len(_ls) >= 2, f'В my_log строк с коммитами: {len(_ls)}. Сделайте в своём проекте минимум два коммита и вставьте весь вывод git log --oneline --no-decorate.'
_bad = [l for l in _ls if not _re.match(r'^[0-9a-f]{7,40} \S', l)]
assert not _bad, f'Строка не похожа на вывод git log --oneline: {_bad[0]!r}. Каждая строка — хэш (7 и больше знаков 0–9, a–f), пробел и подпись. Если видите (HEAD -> main), добавьте --no-decorate.'
_lesson = {'f0dd728', 'a74c250', '3e746ee', '5ae82cb', '3efd677', '375c1e4', '8c3c173'}
assert not ({l.split()[0][:7] for l in _ls} & _lesson), 'Это хэши из примера урока. Вставьте вывод своего git log — у ваших коммитов свои хэши.'
assert need('n_mine') == len(_ls), f'n_mine = {need("n_mine")}, а строк с коммитами в my_log {len(_ls)}. Пустые строки не считайте.'
assert [str(m).strip() for m in need('messages', list)] == [l.split(' ', 1)[1].strip() for l in _ls], 'messages не совпадает: нужны подписи всех коммитов сверху вниз, без хэша — всё, что после первого пробела.'
```

### hint
Коммиты делаются в терминале, не здесь: `git add файл`, затем `git commit -m "подпись"` — дважды, с разными правками. Потом `git log --oneline --no-decorate` и скопируйте вывод.

### hint
Разбор — как в задаче «Читаем git log»: `my_log.strip().splitlines()`, каждую строку — `split(" ", 1)`. `strip()` уберёт пустые строки по краям, которые появляются из-за переносов после `"""`.

### hint
```python
rows = [line.split(" ", 1) for line in my_log.strip().splitlines()]
n_mine = ...
messages = [msg for h, msg in ...]
```

### solution
```python
my_log = """
4b1e9a2 Вывод по выручке доставки
c07d5f1 Структура проекта: README и .gitignore
"""

rows = [line.split(" ", 1) for line in my_log.strip().splitlines()]
n_mine = len(rows)
messages = [msg for h, msg in rows]
print(n_mine, messages)
```

### explain
Хэши в эталоне — для примера, у вас они свои: хэш считается из содержимого коммита, автора и времени, поэтому совпасть не может. Если задача прошла, значит, на вашем компьютере есть репозиторий как минимум с двумя версиями — это первый шаг к портфолио. Без `--no-decorate` в терминале у верхней строки появится пометка `(HEAD -> main)` — она показывает, где сейчас ветка, и в подпись коммита не входит. Типичная ошибка — вставить вывод `git log` без `--oneline`: там у каждого коммита по 5–6 строк (автор, дата, пустые строки), и проверка скажет, какая строка не похожа на формат.

## task: log-pandas | История проекта в pandas | base

Вывод `git log --format="%h|%ad|%an|%s" --date=short` — это почти CSV с разделителем `|`. Прочитайте его в таблицу `commits` со столбцами `hash`, `date`, `author`, `message` (дата — `datetime`), посчитайте `per_day` — число коммитов по дням (Series, индекс — дата, по возрастанию) и `busiest` — день с наибольшим числом коммитов (если таких несколько — самый ранний).

### starter
```python
import io
import pandas as pd

log = """f0dd728|2026-11-26|Аня Петрова|Выводы в README
a74c250|2026-11-25|Аня Петрова|Слияние ветки loyalty
3e746ee|2026-11-25|Аня Петрова|Гипотеза: гости с картой тратят больше
5ae82cb|2026-11-25|Аня Петрова|Выручка по месяцам
3efd677|2026-11-24|Аня Петрова|Фильтр доставки в отдельной переменной
375c1e4|2026-11-24|Аня Петрова|Загрузка заказов и выручка
8c3c173|2026-11-24|Аня Петрова|Структура проекта: README и .gitignore"""

```

### check
```python
import io as _io, pandas as _pd
w = _pd.read_csv(_io.StringIO(need('log')), sep='|', names=['hash', 'date', 'author', 'message'], parse_dates=['date'])
c = need('commits', _pd.DataFrame)
assert list(c.columns) == ['hash', 'date', 'author', 'message'], f'Столбцы commits: {list(c.columns)}. У лога нет строки заголовка — имена задайте через names=.'
assert len(c) == len(w), f'В commits {len(c)} строк, а коммитов {len(w)}. Первая строка лога — это коммит, а не заголовок.'
assert _pd.api.types.is_datetime64_any_dtype(c['date']), 'date должен быть датой: parse_dates=["date"].'
p = need('per_day', _pd.Series)
wp = w.groupby('date').size()
assert [int(x) for x in p.values] == [int(x) for x in wp.values] and list(_pd.to_datetime(p.index)) == list(wp.index), f'per_day не совпадает: нужно число коммитов по дням, индекс — дата по возрастанию.'
assert _pd.Timestamp(need('busiest')) == wp.idxmax(), f'busiest = {need("busiest")}, а нужно {wp.idxmax().date()}.'
```

### hint
Текст в переменной читается как файл через `io.StringIO(log)`. В `pd.read_csv` укажите `sep="|"`, `names=[...]` и `parse_dates=["date"]`.

### hint
По дням — `commits.groupby("date").size()`: индекс сразу отсортирован по возрастанию.

### hint
`idxmax()` возвращает первую из максимальных меток — при сортировке по возрастанию это самый ранний день.

### solution
```python
import io
import pandas as pd

log = """f0dd728|2026-11-26|Аня Петрова|Выводы в README
a74c250|2026-11-25|Аня Петрова|Слияние ветки loyalty
3e746ee|2026-11-25|Аня Петрова|Гипотеза: гости с картой тратят больше
5ae82cb|2026-11-25|Аня Петрова|Выручка по месяцам
3efd677|2026-11-24|Аня Петрова|Фильтр доставки в отдельной переменной
375c1e4|2026-11-24|Аня Петрова|Загрузка заказов и выручка
8c3c173|2026-11-24|Аня Петрова|Структура проекта: README и .gitignore"""

commits = pd.read_csv(io.StringIO(log), sep="|", names=["hash", "date", "author", "message"],
                      parse_dates=["date"])
per_day = commits.groupby("date").size()
busiest = per_day.idxmax()
per_day
```

### explain
24 и 25 ноября — по три коммита, 26-го — один; `idxmax` вернул 24 ноября, потому что среди равных берётся первый. Без `names=` pandas сделал бы заголовком первый коммит — и в таблице осталось бы шесть строк вместо семи. Разделитель `|` выбран не случайно: в подписях коммитов бывают запятые, и с `sep=","` подпись «Структура проекта: README и .gitignore» не пострадала бы, а «Фильтр, выручка» — развалилась бы на столбцы. Такая таблица — основа отчётов «кто и когда работал над проектом».

## task: diff-stat | Сколько строк поменялось | base

Ниже настоящий вывод `git diff` между двумя коммитами. Посчитайте, как `git diff --stat`: `files` — список изменённых файлов (из строк `diff --git a/… b/…`, путь после `b/`), `added` и `removed` — сколько строк добавлено и удалено во всех файлах. Заголовки `+++` и `---` — не изменения.

### starter
```python
diff = """diff --git a/README.md b/README.md
index 9ea5733..8a2292f 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,7 @@
 # Итоги осени
 
 Анализ продаж сети «Зерно» за сентябрь–ноябрь.
+
+## Выводы
+
+- Рост ноября: +9.6 % к октябрю.
diff --git a/report.py b/report.py
index fbaa5fc..e7ddf43 100644
--- a/report.py
+++ b/report.py
@@ -1,6 +1,13 @@
 import pandas as pd
 
 df = pd.read_csv("data/orders_3m.csv", parse_dates=["datetime"])
-df = df[df["channel"] == "доставка"]
-revenue = df["amount"].sum()
-print(revenue)
+delivery = df[df["channel"] == "доставка"]
+revenue_all = df["amount"].sum()
+revenue_delivery = delivery["amount"].sum()
+print(revenue_all, revenue_delivery)
+
+monthly = df.groupby(df["datetime"].dt.to_period("M"))["amount"].sum()
+print(monthly)
+
+card = df["client_id"].notna()
+print(df.loc[card, "amount"].mean(), df.loc[~card, "amount"].mean())"""

```

### check
```python
L = need('diff').splitlines()
wf = [l.split(' b/', 1)[1] for l in L if l.startswith('diff --git ')]
wa = sum(1 for l in L if l.startswith('+') and not l.startswith('+++'))
wr = sum(1 for l in L if l.startswith('-') and not l.startswith('---'))
assert need('files', list) == wf, f'files = {need("files")}, а нужно {wf}.'
assert need('added') == wa, f'added = {need("added")}. Пропустите заголовки +++; пустая добавленная строка — это просто «+», её считать нужно.'
assert need('removed') == wr, f'removed = {need("removed")}. Пропустите заголовки ---.'
```

### hint
Идите по `diff.splitlines()`. Добавленная строка начинается с `+`, но не с `+++`; удалённая — с `-`, но не с `---`.

### hint
`startswith` принимает и кортеж: `l.startswith("+") and not l.startswith("+++")`. Файл — `l.split(" b/", 1)[1]` у строк, которые начинаются с `"diff --git "`.

### solution
```python
diff = """diff --git a/README.md b/README.md
index 9ea5733..8a2292f 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,7 @@
 # Итоги осени
 
 Анализ продаж сети «Зерно» за сентябрь–ноябрь.
+
+## Выводы
+
+- Рост ноября: +9.6 % к октябрю.
diff --git a/report.py b/report.py
index fbaa5fc..e7ddf43 100644
--- a/report.py
+++ b/report.py
@@ -1,6 +1,13 @@
 import pandas as pd
 
 df = pd.read_csv("data/orders_3m.csv", parse_dates=["datetime"])
-df = df[df["channel"] == "доставка"]
-revenue = df["amount"].sum()
-print(revenue)
+delivery = df[df["channel"] == "доставка"]
+revenue_all = df["amount"].sum()
+revenue_delivery = delivery["amount"].sum()
+print(revenue_all, revenue_delivery)
+
+monthly = df.groupby(df["datetime"].dt.to_period("M"))["amount"].sum()
+print(monthly)
+
+card = df["client_id"].notna()
+print(df.loc[card, "amount"].mean(), df.loc[~card, "amount"].mean())"""

lines = diff.splitlines()
files = [l.split(" b/", 1)[1] for l in lines if l.startswith("diff --git ")]
added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
print(files, added, removed)
```

### explain
Два файла, 14 строк добавлено и 3 удалены — ровно столько же печатает `git diff --stat`: `2 files changed, 14 insertions(+), 3 deletions(-)`. Если забыть про заголовки, выйдет 16 и 5: по одному `+++` и `---` на каждый файл. Ещё одна ловушка — строка `- Рост ноября…` внутри README: она начинается с `+`, потому что добавлена целиком, а дефис — уже часть текста. Знак изменения — только первый символ строки.

## task: ignore | Мини-.gitignore | base

Напишите `is_ignored(path, patterns)` — упрощённую проверку `.gitignore`. Путь игнорируется, если хотя бы один шаблон подходит:

- шаблон, который оканчивается на `/`, — это папка: подходит, если одна из папок в пути (всё, кроме последней части) называется так же;
- иначе шаблон сравнивается через `fnmatch` с **именем файла** — последней частью пути.

Части пути разделены `/`. Посчитайте `tracked` — список файлов из `files`, которые git будет отслеживать, в том же порядке.

### starter
```python
from fnmatch import fnmatch

patterns = [".venv/", "data/", ".ipynb_checkpoints/", "*.csv", ".env"]
files = ["README.md", "report.ipynb", "data/orders_3m.csv", ".env", "pyproject.toml",
         ".ipynb_checkpoints/report-checkpoint.ipynb", "export/kpi.csv", "notes/.env.example",
         ".venv/lib/pandas/__init__.py", "src/zerno_utils.py"]

def is_ignored(path, patterns):
    ...

tracked = ...
tracked
```

### check
```python
from fnmatch import fnmatch as _fm
def _ig(path, patterns):
    parts = path.split('/')
    for p in patterns:
        if p.endswith('/'):
            if p[:-1] in parts[:-1]:
                return True
        elif _fm(parts[-1], p):
            return True
    return False
f = need('is_ignored')
pats, fs = need('patterns'), need('files')
assert need('tracked', list) == [x for x in fs if not _ig(x, pats)], f'tracked = {need("tracked")}, а нужно {[x for x in fs if not _ig(x, pats)]}.'
for path, pp in (('data', ['data/']), ('a/data/b.txt', ['data/']), ('report.ipynb', ['*.ipynb']), ('x/y.CSV', ['*.csv']),
                 ('.env.example', ['.env']), ('deep/.venv/x.py', ['.venv/'])):
    assert bool(f(path, pp)) == _ig(path, pp), f'is_ignored({path!r}, {pp}) = {f(path, pp)}, а нужно {_ig(path, pp)}. Папочный шаблон проверяют только по папкам пути, не по имени файла.'
```

### hint
Разбейте путь: `parts = path.split("/")`. Папки — `parts[:-1]`, имя файла — `parts[-1]`.

### hint
Для шаблона-папки: `p[:-1] in parts[:-1]` (срез убирает `/` в конце). Для остальных: `fnmatch(parts[-1], p)`.

### hint
`tracked = [f for f in files if not is_ignored(f, patterns)]`.

### solution
```python
from fnmatch import fnmatch

patterns = [".venv/", "data/", ".ipynb_checkpoints/", "*.csv", ".env"]
files = ["README.md", "report.ipynb", "data/orders_3m.csv", ".env", "pyproject.toml",
         ".ipynb_checkpoints/report-checkpoint.ipynb", "export/kpi.csv", "notes/.env.example",
         ".venv/lib/pandas/__init__.py", "src/zerno_utils.py"]

def is_ignored(path, patterns):
    parts = path.split("/")
    for p in patterns:
        if p.endswith("/"):
            if p[:-1] in parts[:-1]:
                return True
        elif fnmatch(parts[-1], p):
            return True
    return False

tracked = [f for f in files if not is_ignored(f, patterns)]
tracked
```

### explain
В репозиторий попадут README, блокнот, `pyproject.toml`, `notes/.env.example` и модуль `src/zerno_utils.py`. `export/kpi.csv` отсеян шаблоном `*.csv`, хотя папки `export` в списке нет. А `.env.example` проходит: шаблон `.env` требует точного имени — так обычно и делают, чтобы выложить пример настроек без паролей. Настоящий git сложнее (шаблоны с `/` в середине, исключения `!`, `**`), но суть та же. Если сравнивать папочный шаблон и с именем файла, файл с именем `data` без расширения ошибочно пропадёт из репозитория.

## task: status-sim | Свой git status | star

Напишите `status(committed, working, ignore)` — упрощённый `git status`. `committed` — словарь «путь → содержимое» в последнем коммите, `working` — то же для рабочей папки сейчас, `ignore` — список шаблонов для `fnmatch` по **имени файла** (последней части пути). Верните словарь с ключами `"new"`, `"modified"`, `"deleted"` — отсортированные списки путей:

- `new` — есть в папке, нет в коммите, и имя файла не подходит ни под один шаблон;
- `modified` — есть и там, и там, но содержимое разное;
- `deleted` — был в коммите, а в папке его нет.

Шаблоны действуют только на новые файлы: то, что уже в коммите, git продолжает отслеживать.

### starter
```python
from fnmatch import fnmatch

committed = {"README.md": "# Итоги осени", "report.py": "print(1)", "old.ipynb": "{}"}
working = {"README.md": "# Итоги осени", "report.py": "print(2)", "notes.md": "черновик",
           "data/orders_3m.csv": "...", ".env": "PASSWORD=..."}
ignore = ["*.csv", ".env"]

def status(committed, working, ignore):
    ...

status(committed, working, ignore)
```

### check
```python
from fnmatch import fnmatch as _fm
def _st(c, w, ig):
    ign = lambda p: any(_fm(p.split('/')[-1], x) for x in ig)
    return {'new': sorted(p for p in w if p not in c and not ign(p)),
            'modified': sorted(p for p in w if p in c and w[p] != c[p]),
            'deleted': sorted(p for p in c if p not in w)}
f = need('status')
cases = [(need('committed'), need('working'), need('ignore')),
         ({'a.csv': '1'}, {'a.csv': '2', 'b.csv': '3'}, ['*.csv']),
         ({}, {'x/y/report.ipynb': '{}', 'z.py': ''}, []),
         ({'b.md': 'x', 'a.md': 'y'}, {}, ['*.md'])]
for c, w, ig in cases:
    got = f(c, w, ig)
    assert got is not None and {k: list(v) for k, v in got.items()} == _st(c, w, ig), f'status({c}, {w}, {ig}) = {got}, а нужно {_st(c, w, ig)}.'
```

### hint
Три множества путей: в папке и не в коммите, в обоих, в коммите и не в папке. Каждое — генератор по одному из словарей.

### hint
Игнор — функция от пути: `any(fnmatch(path.split("/")[-1], p) for p in ignore)`. Применяйте её только к новым файлам.

### hint
`"modified": sorted(p for p in working if p in committed and working[p] != committed[p])`; удалённые — `sorted(p for p in committed if p not in working)`.

### solution
```python
from fnmatch import fnmatch

committed = {"README.md": "# Итоги осени", "report.py": "print(1)", "old.ipynb": "{}"}
working = {"README.md": "# Итоги осени", "report.py": "print(2)", "notes.md": "черновик",
           "data/orders_3m.csv": "...", ".env": "PASSWORD=..."}
ignore = ["*.csv", ".env"]

def status(committed, working, ignore):
    def ignored(path):
        return any(fnmatch(path.split("/")[-1], p) for p in ignore)
    return {
        "new": sorted(p for p in working if p not in committed and not ignored(p)),
        "modified": sorted(p for p in working if p in committed and working[p] != committed[p]),
        "deleted": sorted(p for p in committed if p not in working),
    }

status(committed, working, ignore)
```

### explain
Результат: новый `notes.md`, изменённый `report.py`, удалённый `old.ipynb`; данные и `.env` git не видит благодаря шаблонам. Второй тестовый случай показывает тонкость, о которой говорилось в разделе про `.gitignore`: `a.csv` уже в коммите, поэтому его изменение видно, несмотря на шаблон `*.csv`, — `.gitignore` не скрывает отслеживаемые файлы. Настоящий git сравнивает не содержимое целиком, а хэши файлов, но логика трёх списков та же.
