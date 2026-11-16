#!/usr/bin/env python3
"""Блокноты курса: практикумы глав site/notebooks/chNN-practice.ipynb (+ tasks/chNN.json)
и шаблон проекта site/notebooks/project-template.ipynb.

    python3 tools/make_notebooks.py          # все главы; файлы переписываются, только если изменились
    python3 tools/make_notebooks.py --test solution [ch01 ...]   # прогон: эталоны вместо заготовок → «✓ Верно»
    python3 tools/make_notebooks.py --test starter  [ch01 ...]   # прогон заготовок → ни одна не проходит

Источник — те же уроки, что у сайта (tools/build.py: load_course). В блокнот главы идут кодовые
задачи всех уровней, кроме «собери код из строк» (это упражнение на порядок строк, в блокноте
его нечем проверять). Задачи контрольных точек — отдельным разделом. Проверки, подготовка,
подсказки и решения лежат в tasks/chNN.json; их читает расширение site/notebooks/dsc.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
OUT = TOOLS.parent / 'site' / 'notebooks'
TASKS = OUT / 'tasks'
SHORT_IDS: dict = {}     # id задачи → сколько раз встречается в курсе
UV_LESSON = '08-jupyter'  # урок, где ставят uv и Jupyter: ссылка на него в начале каждого практикума
LEVEL_RU = {'warmup': 'разминка', 'base': 'база', 'plus': 'посложнее', 'star': 'со звёздочкой'}

START = '''# Глава {n}. {title} — практика в Jupyter

Те же задачи, что на сайте курса, но в своём Jupyter: так вы привыкаете к блокноту, горячим клавишам и своему окружению. Проверка — та же, что в браузере.

**Как запустить** (один раз поставьте [uv](https://docs.astral.sh/uv/){uv_ref}). В терминале, в папке курса:

```sh
uv run --with-requirements site/notebooks/requirements.txt jupyter lab site/notebooks
```

Без uv: `python3 -m venv .venv`, затем `.venv/bin/pip install -r site/notebooks/requirements.txt` (в Windows — `.venv\\Scripts\\pip`) и `.venv/bin/jupyter lab site/notebooks`. Откройте этот файл в папке `site/notebooks` — рядом с ним лежит расширение `dsc.py`, без него проверка не заработает.

**Как решать**

1. Запустите ячейку ниже с `%load_ext dsc` — она подключает проверку. После перезапуска ядра запустите её снова.
2. В ячейке задачи первая строка — `%%task глава/урок/id`. Её не трогайте, пишите код ниже и запускайте **Shift+Enter**. Под выводом появится «✓ Верно» или подсказка, что не так.
3. Переменные живут между ячейками, как в любом блокноте. Исключение — переменные, в которые задача просит положить ответ: перед запуском ячейки они стираются, чтобы проверка видела результат именно этого запуска. Подготовка задачи (если она есть) выполняется перед вашим кодом при каждом запуске.
4. Застряли — `dsc.hint('id')` покажет следующую подсказку, `dsc.solution('id', sure=True)` — эталон с разбором. `dsc.progress()` — что решено в этом сеансе.
5. Файлы данных берутся по имени, как на сайте: `pd.read_csv('orders.csv')`. Код работает в папке `site/notebooks/_work` — там копия `site/data`, и туда же попадает всё, что сохраняет ваш код.

Прогресс сайта и блокнота не связаны: отметки о решённых задачах на сайте ставятся только там. Чтобы начать с чистого листа, скачайте блокнот заново или возьмите его из архива курса.'''

EXAM_NOTE = ('Задачи контрольной точки. Проверка отвечает только «верно» или «нет» — как на сайте, '
             'пока контрольная не завершена. Подсказки и решения есть, но откройте их после попытки решить всё самостоятельно.')


def cell_id(*parts: str) -> str:
    return hashlib.sha1('/'.join(parts).encode()).hexdigest()[:12]


def md(src: str, *key: str) -> dict:
    return {'cell_type': 'markdown', 'id': cell_id('md', *key), 'metadata': {}, 'source': _lines(src)}


def code(src: str, *key: str) -> dict:
    return {'cell_type': 'code', 'execution_count': None, 'id': cell_id('code', *key), 'metadata': {},
            'outputs': [], 'source': _lines(src)}


def _lines(src: str) -> list:
    src = src.rstrip('\n')
    parts = src.split('\n')
    return [p + '\n' for p in parts[:-1]] + [parts[-1]] if src else []


def notebook(cells: list) -> dict:
    return {'cells': cells, 'metadata': {
        'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}


def task_record(ch: str, ls_id: str, ls_title: str, t: dict, files: list, display: bool, exam: bool) -> dict:
    return {'chapter': ch, 'lesson': ls_id, 'lesson_title': ls_title, 'id': t['id'], 'title': t['title'],
            'level': t['level'], 'exam': exam, 'parsons': bool(t['parsons']), 'files': files, 'display': display,
            'setup': t['setup'], 'check': t['check'], 'starter': t['starter'], 'solution': t['solution'],
            'hints': t['hints_md'], 'explain': t['explain_md']}


def in_notebook(t: dict) -> bool:
    return not t['parsons']


def task_cells(ch: str, ls_id: str, t: dict, exam: bool) -> list:
    key = f'{ch}/{ls_id}/{t["id"]}'
    level = LEVEL_RU[t['level']]
    nh = len(t['hints_md'])
    foot = []
    if nh and not exam:
        ref = t['id'] if SHORT_IDS.get(t['id'], 0) == 1 else key   # короткий id — только если он один на весь курс
        foot.append(f'Подсказки ({nh}): `dsc.hint({ref!r})`')
    if t['level'] == 'star':
        foot.append('задача по желанию')
    text = f'### {t["title"]} · {level}\n\n{t["text"]}'
    if (ch, ls_id) == ('ch01', '14-project') or key == 'ch10/05-project/release-row':
        text = f'<a id="task-{t["id"]}"></a>\n\n' + text
    if foot:
        text += '\n\n*' + ' · '.join(foot) + '*'
    starter = t['starter'].rstrip('\n') or '# ваш код'   # у магии %%task тело ячейки не может быть пустым
    return [md(text, key), code(f'%%task {key}\n{starter}', key)]


def chapter_items(ch: dict, built: dict) -> list:
    """Уроки и контрольные точки главы в порядке курса: [(урок из course.yaml, разобранный урок, exam?)]."""
    items = []
    exams = ch.get('exams', [])
    for ls in ch.get('lessons', []):
        if (ch['id'], ls['id']) in built:
            items.append((ls, built[(ch['id'], ls['id'])], False))
        for ex in exams:
            if ex.get('after') == ls['id'] and (ch['id'], ex['id']) in built:
                items.append((ex, built[(ch['id'], ex['id'])], True))
    return items


def uv_ref(course: dict) -> str:
    """«, см. урок «…» главы 2» — название урока про uv берётся из course.yaml: номера уроков меняются при делении."""
    for ch in course['chapters']:
        for ls in ch.get('lessons', []):
            if ls['id'] == UV_LESSON:
                return f', см. урок «{ls["title"]}» главы {ch["n"]}'
    return ''


def make_chapter(ch: dict, built: dict, uv: str = '') -> tuple[dict, dict, int]:
    cid = ch['id']
    cells = [md(START.format(n=ch['n'], title=ch['title'], uv_ref=uv), cid, 'start'),
             code('%load_ext dsc', cid, 'load')]
    records = {}
    n_cells = 0
    disp_ch = bool(ch.get('display', False))
    for ls, L, exam in chapter_items(ch, built):
        files = L['meta'].get('files', []) or []
        disp = bool(L['meta'].get('display', disp_ch))
        for t in L['tasks']:
            records[f'{cid}/{ls["id"]}/{t["id"]}'] = task_record(cid, ls['id'], ls['title'], t, files, disp, exam)
        shown = [t for t in L['tasks'] if in_notebook(t)]
        if not shown:
            continue
        if exam:
            head = f'## {ls["title"]}\n\n{EXAM_NOTE}'
        else:
            lead = L['meta'].get('lead', '')
            head = (f'## Урок {ls["n"]}. {ls["title"]}\n\n{lead}\n\n'
                    f'Теория — на сайте курса: `{cid}/{ls["id"]}.html`.').replace('\n\n\n\n', '\n\n')
            skipped = len(L['tasks']) - len(shown)
            if skipped:
                head += f' Задачи «собери код из строк» ({skipped}) остались на сайте.'
        cells.append(md(head, cid, ls['id']))
        for t in shown:
            cells += task_cells(cid, ls['id'], t, exam)
            n_cells += 1
    cells.append(md('## Готово\n\nЗапустите `dsc.progress()` — увидите, какие задачи этого сеанса ещё не решены. '
                    'Перед тем как закрыть блокнот, полезно сделать **Kernel → Restart Kernel and Run All Cells**: '
                    'если всё проходит сверху вниз, решения не зависят от случайного порядка запуска ячеек.', cid, 'end'))
    cells.append(code('dsc.progress()', cid, 'progress'))
    data = {'chapter': cid, 'title': ch['title'], 'tasks': records}
    return notebook(cells), data, n_cells


# ---------- шаблон проектного блокнота ----------

TEMPLATE = [
    ('md', """# Проект: ✎ название

> **Как работать с шаблоном** (эту врезку удалите перед сдачей)
>
> 1. Скопируйте файл и переименуйте по проекту, например `ch05-project.ipynb`. Положите его в `site/notebooks` — тогда путь к данным `../data` в первой ячейке подойдёт без правок. Пути к файлам — только относительные: блокнот должен запускаться на любом компьютере.
> 2. Заполните разделы по порядку: цель → данные → предобработка → анализ и модели → выводы. Всё, что помечено ✎, замените своим текстом. Код-пример посчитан на `daily_sales.csv` — замените его кодом своего проекта.
> 3. После каждого раздела — markdown-ячейка **«Вывод»**: что увидели (с числами из вывода кода) и что это значит для «Зерна». Код без вывода — это черновик, а не отчёт.
> 4. Переменные с результатами называйте так, как просят задачи проекта в браузере (`monthly`, `late_pct`, `best_t` …): по этим именам скрипт самопроверки сверит ваши числа с эталонами.
> 5. Перед сдачей: **Kernel → Restart Kernel and Run All Cells**, затем в терминале, в папке блокнота: `python check_notebook.py my.ipynb --project chNN/<урок>` — например, `--project ch04/09-project`. Скрипт выполнит блокнот с чистого ядра, перечислит, что поправить в оформлении, и проверит переменные блокнота проверками задач урока: ✓ или ✗ с подсказкой по каждой. Если блокнот лежит вне папки курса, добавьте `--course ПАПКА_КУРСА`.
>
> **Чек-лист самопроверки**
>
> - [ ] блокнот выполняется сверху вниз с чистого ядра без ошибок;
> - [ ] `check_notebook.py … --project` — задачи урока сошлись с эталонами (✓);
> - [ ] первая ячейка — импорты, версии библиотек и `RANDOM_STATE`; случайность везде через `random_state=RANDOM_STATE`;
> - [ ] пути к данным относительные, нет `C:\\…` и `/Users/…`;
> - [ ] нет закомментированного кода и отладочных ячеек;
> - [ ] после каждого раздела есть вывод с числами, а в конце — ответ на вопрос из «Цели»;
> - [ ] у графиков есть заголовок и подписи осей;
> - [ ] модель сравнивается с простым ориентиром (среднее, самый частый класс, «как вчера»)."""),
    ('code', """# Импорты, версии и общие настройки — всё в одном месте, в начале блокнота
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
try:                       # sklearn нужен только проектам с моделями (с главы 6)
    import sklearn
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import train_test_split
except ImportError:
    sklearn = None

RANDOM_STATE = 42          # одно число для всей случайности: разбиения, модели, выборки
# папка с данными: data/ рядом с блокнотом (свой проект) или ../data (блокнот в папке курса)
DATA = next((p for p in (Path('data'), Path('../data')) if p.exists()), Path('data'))

pd.set_option('display.max_columns', 30)
print('Python', sys.version.split()[0], '| данные:', DATA.resolve())
for lib in (pd, np, matplotlib, sklearn):
    if lib is None:
        continue
    print(f'{lib.__name__:<11}{lib.__version__}')"""),
    ('md', """## 1. Цель

✎ **Бизнес-вопрос.** Какой вопрос «Зерна» решает проект и кто примет решение по результату.

✎ **Что будет результатом.** Таблица, график, модель, рекомендация — и в каком виде её получит заказчик.

✎ **Как поймём, что получилось.** Метрика и порог: например, «ошибка прогноза меньше, чем у прогноза „как в среднем“».

✎ **Главное (допишите в конце работы).** 2–3 фразы для руководителя: ответ на вопрос с цифрой масштаба и что предлагаем. Подробности и журнал очистки — ниже, в своих разделах."""),
    ('md', """## 2. Данные

✎ Откуда данные, за какой период, что описывает одна строка, какие столбцы важны для вопроса."""),
    ('code', """df = pd.read_csv(DATA / 'daily_sales.csv', parse_dates=['date'])   # ✎ замените на файл своего проекта
print(df.shape)
df.info()"""),
    ('code', """df.head()"""),
    ('md', """**Вывод по данным.** ✎ Сколько строк и столбцов, за какой период, какие типы надо поправить, что вызывает вопросы."""),
    ('md', """## 3. Предобработка

Сначала смотрим на проблемы, потом исправляем — и каждое исправление объясняем."""),
    ('code', """print('Пропуски по столбцам:')
print(df.isna().sum()[lambda s: s > 0])
print('Полных дублей строк:', df.duplicated().sum())
df.describe()"""),
    ('code', """clean = df.drop_duplicates().copy()
print(f'Было строк: {len(df)}, стало: {len(clean)}')"""),
    ('md', """**Вывод по предобработке.** ✎ Что нашли (пропуски, дубли, выбросы, типы), что сделали с каждой проблемой и почему, сколько строк осталось."""),
    ('md', """## 4. Анализ и модели

✎ Коротко: какие гипотезы проверяем и какие модели сравниваем."""),
    ('code', """by_format = clean.groupby('format')['revenue_k'].mean().sort_values()
ax = by_format.plot(kind='barh', figsize=(7, 3))
ax.set_title('Средняя дневная выручка по формату точки')
ax.set_xlabel('тыс. руб. в день')
ax.set_ylabel('')
plt.show()
by_format.round(1)"""),
    ('code', """# Модели — в проектах с главы 6; в проектах глав 2–4 эту ячейку удалите.
features = ['temp', 'rain', 'holiday', 'promo']
X_train, X_test, y_train, y_test = train_test_split(
    clean[features], clean['revenue_k'], test_size=0.25, random_state=RANDOM_STATE)

results = []
for name, model in [('среднее (ориентир)', DummyRegressor()), ('линейная регрессия', LinearRegression())]:
    model.fit(X_train, y_train)
    results.append({'модель': name, 'MAE на тесте': mean_absolute_error(y_test, model.predict(X_test))})
pd.DataFrame(results).round(2)"""),
    ('md', """**Вывод по анализу.** ✎ Что показали графики и таблицы, какая модель лучше ориентира и насколько — в единицах бизнеса."""),
    ('md', """## 5. Выводы и рекомендации

✎ 3–5 пунктов:

1. Ответ на вопрос из раздела «Цель» — с числами.
2. Что рекомендуем сделать «Зерну» и какой эффект ожидаем.
3. Ограничения: чего данные не показывают, где выводы могут не сработать.
4. Что проверить или сделать дальше."""),
]


ANALYTICS_IMPORTS = """import sys
from pathlib import Path

import pandas as pd

def data_folder(*files):
    for folder in (Path("data"), Path("../data")):
        if all((folder / filename).is_file() for filename in files):
            print("Папка данных:", folder.resolve())
            return folder
    raise FileNotFoundError("В data/ и ../data/ нет полного набора: " + ", ".join(files))

print("Python", sys.version.split()[0], "| pandas", pd.__version__)"""


CH02_TEMPLATE = [
    ('md', """# ✎ Название отчёта

Для осеннего проекта сохраните копию как `autumn.ipynb`, для SQL-проекта — как `loyalty.ipynb`. Скопируйте нужные файлы из урока в папку `data/` рядом с блокнотом. В архиве курса также подходит `../data/`. Запустите первую ячейку. В разделе «Данные» укажите файлы своего проекта.

Заполняйте разделы ниже. После каждого расчёта добавьте Markdown-вывод с числом и его смыслом. Повторите раздел «Анализ» для каждой гипотезы или вопроса. При сдаче удалите подсказки и пометки ✎.

Перед передачей выполните **Restart Kernel and Run All Cells**, сохраните выводы и запустите `python check_notebook.py имя_файла.ipynb`. Дополнительная сверка переменных доступна в архиве курса; команды приведены в уроке проекта."""),
    ('code', ANALYTICS_IMPORTS),
    ('md', """## 1. Цель

✎ Кому нужен отчёт? Для осеннего проекта запишите шесть гипотез и правила решения до расчётов. Для SQL-проекта перечислите пять вопросов руководителя."""),
    ('md', """## 2. Данные и проверка качества

В первой ячейке этого раздела выберите строку для своих файлов.

- Осенний отчёт: `DATA = data_folder("orders_3m.csv", "shops.csv", "menu.csv")`.
- SQL с SQLite: `DATA = data_folder("zerno.db")`.
- SQL с шестью CSV: `DATA = data_folder("zdb_shops.csv", "zdb_menu.csv", "zdb_guests.csv", "zdb_promos.csv", "zdb_orders.csv", "zdb_items.csv")`.

✎ Назовите период и источники. Что означает одна строка каждой таблицы? По каким ключам вы соединяете таблицы и как узнаете, что заказ учтён один раз?"""),
    ('code', ''),
    ('md', '✎ Вывод о качестве данных и границах выгрузки.'),
    ('md', """## 3. Предобработка

✎ Укажите, как учли типы, пропуски и повторы и как проверили соединение."""),
    ('md', """## 4. Анализ — ✎ гипотеза или вопрос

✎ Запишите вопрос, посчитайте показатель в следующей ячейке и объясните результат. Для следующего вопроса создайте новый раздел уровня `##`."""),
    ('code', ''),
    ('md', '✎ Вывод по этому вопросу с числом и его ограничением.'),
    ('md', """## 5. Выводы и рекомендации

✎ Какие решения поддерживают расчёты? Какие данные потребуются для следующего решения? Для осеннего проекта добавьте таблицу вердиктов, для SQL-проекта — ответы на пять вопросов."""),
]


CH03_TEMPLATE = [
    ('md', """# ✎ Портрет гостей сети

Сохраните копию как `guests.ipynb`. Положите три CSV из задания в одну папку `data/` рядом с блокнотом или в `../data/`. Запустите первую ячейку. Для каждого раздела оставьте воспроизводимый расчёт и короткий вывод. Перед передачей выполните **Restart Kernel and Run All Cells** и сохраните блокнот с выводами. Удалите пометки ✎."""),
    ('code', ANALYTICS_IMPORTS + '\nCLIENTS_FILE = "clients_raw.csv"\nDATA = data_folder(CLIENTS_FILE, "orders_3m.csv", "shops.csv")'),
    ('md', """## 1. Цель

✎ Кто получит отчёт? За какой период наблюдаются покупки? Объясните, кого можно включить в портрет и кого эти данные не охватывают."""),
    ('md', """## 2. Данные

✎ Загрузите анкеты, заказы и справочник кофеен. Покажите размер таблиц, названия и типы полей, количество пропусков и дубликатов. Перед передачей проверьте сохранённые выводы ячеек: публикуйте сводные числа без строк анкет."""),
    ('code', 'raw = pd.read_csv(DATA / CLIENTS_FILE)\norders = pd.read_csv(DATA / "orders_3m.csv", parse_dates=["datetime"])\nshops = pd.read_csv(DATA / "shops.csv")'),
    ('md', '✎ Вывод об исходных данных.'),
    ('md', """## 3. Предобработка

✎ Вызовите свою функцию очистки. Сохраните в блокноте журнал с исходным числом строк, числом удалённых полных дублей и повторных анкет, итогом. Проверьте равенство этих чисел и уникальность ключа. Очищенные анкеты оставьте в закрытой папке `private/`."""),
    ('code', ''),
    ('md', '✎ Объясните, на каком шаге изменилось число анкет и почему.'),
    ('md', """## 3.1. Качество данных

✎ Для каждой проблемы укажите поле, нарушенное правило, число строк и способ повторить поиск. Примеры ключей можно передать владельцу CRM в отдельном внутреннем тикете. В публичном блокноте достаточно числа и правила поиска."""),
    ('md', """## 4. Анализ

✎ Для каждого вопроса из шагов 3–7 создайте свой раздел уровня `##`. Приведите результат и знаменатель. Укажите, что получится у карты без покупок."""),
    ('code', ''),
    ('md', '✎ Какое сравнение поддерживают эти данные?'),
    ('md', """## 5. Выводы и рекомендации

✎ Какие выводы можно передать маркетингу? Какое исправление нужно владельцу CRM? Для чисел в выводе используйте рассчитанные переменные или укажите, к какой выгрузке относится ручной комментарий. После смены CLIENTS_FILE перепроверьте текст. Назовите ограничение, от которого зависит рекомендация."""),
]


CH04_TEMPLATE = [
    ('md', """# ✎ Опоздания доставок

Сохраните копию как `delivery_delays.ipynb`. Поместите `deliveries.csv` в папку `data/` рядом с блокнотом или на уровень выше. Для другой выгрузки измените `DELIVERIES_FILE` в первой ячейке. Перед передачей выполните **Restart Kernel and Run All Cells**, сохраните выводы и запустите `python check_notebook.py delivery_delays.ipynb`."""),
    ('code', ANALYTICS_IMPORTS + '\nimport matplotlib.pyplot as plt\nfrom IPython.display import Markdown, display\n\nDELIVERIES_FILE = "deliveries.csv"\nDATA = data_folder(DELIVERIES_FILE)\nraw = pd.read_csv(DATA / DELIVERIES_FILE, parse_dates=["created"])'),
    ('md', """## Цель и главное

✎ Какое решение предстоит руководителю? Подготовьте здесь числа для резюме, используя выбранный файл. Можно поместить определение и вызов своей функции перед резюме, а подробный разбор расчёта показать ниже. Назовите знаменатель доли, границы при неизвестном статусе и результат сравнения при одинаковом обещанном сроке."""),
    ('code', ''),
    ('md', '✎ Сформулируйте главный вывод по текущей выгрузке.'),
    ('md', """## Данные и предобработка

✎ Назовите период и единицу наблюдения. Покажите журнал из шага 1 и объясните исключения. Какими были бы границы доли опозданий, если бы все заказы с неизвестным статусом уложились в срок или все опоздали?"""),
    ('code', ''),
    ('md', '✎ Вывод о качестве данных.'),
    ('md', """## Масштаб и сравнение групп

✎ Для шагов 2–7 создайте отдельные разделы. У каждой доли укажите числитель и знаменатель, у графика — единицы и заголовок с выводом. Для выбранной группы покажите сравнение при одинаковом обещании и объясните, что остаётся несопоставимым."""),
    ('code', ''),
    ('md', '✎ Что можно заключить из этого сравнения?'),
    ('md', """## Две собственные находки

✎ Проверьте свои условия отбора. Для каждой находки сравните размер и долю в группе и вне её. Уточните, сохраняется ли наблюдение внутри сопоставимых групп."""),
    ('code', ''),
    ('md', '✎ Для каждой находки укажите ограничение.'),
    ('md', """## Выводы и рекомендации

✎ Какую меру вы предложите руководителю проверить? Какой результат заставит вас пересмотреть её? После смены входного файла сверьте текст и графики с новыми расчётами. Для чисел в пояснениях используйте `display(Markdown(f"..."))` после расчёта либо подпишите, к какой выгрузке относится ручной комментарий."""),
]


def make_template(sections=TEMPLATE, name='template') -> dict:
    cells = []
    for i, (kind, src) in enumerate(sections):
        cells.append(md(src, name, str(i)) if kind == 'md' else code(src, name, str(i)))
    return notebook(cells)


def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
    path.write_text(text, encoding='utf-8')
    return True


def main() -> int:
    # build — только для генерации: прогону --test хватает готовых блокнотов и библиотек из requirements.txt
    sys.path.insert(0, str(TOOLS))
    import build
    course, built, errors = build.load_course()
    if errors:
        print(f'Внимание: в уроках ошибки формата ({errors}), см. tools/build.py --check. '
              'Блокноты собраны из того, что удалось разобрать.')
    for L in built.values():
        for t in L['tasks']:
            SHORT_IDS[t['id']] = SHORT_IDS.get(t['id'], 0) + 1
    OUT.mkdir(parents=True, exist_ok=True)
    TASKS.mkdir(exist_ok=True)
    total, changed = 0, 0
    for ci, ch in enumerate(course['chapters'], 1):
        ch['n'] = ci
        for li, ls in enumerate(ch.get('lessons', []), 1):
            ls['n'] = li
    uv = uv_ref(course)
    for ch in course['chapters']:
        if not any((ch['id'], ls['id']) in built for ls in ch.get('lessons', [])):
            continue
        nb, data, n = make_chapter(ch, built, uv)
        nb_text = json.dumps(nb, ensure_ascii=False, indent=1) + '\n'
        data_text = json.dumps(data, ensure_ascii=False, indent=1) + '\n'
        c1 = write_if_changed(OUT / f'{ch["id"]}-practice.ipynb', nb_text)
        c2 = write_if_changed(TASKS / f'{ch["id"]}.json', data_text)
        changed += c1 + c2
        total += n
        print(f'{ch["id"]}: задач в блокноте {n} из {len(data["tasks"])}{" — обновлён" if c1 or c2 else ""}')
    tpl = json.dumps(make_template(), ensure_ascii=False, indent=1) + '\n'
    if write_if_changed(OUT / 'project-template.ipynb', tpl):
        changed += 1
        print('project-template.ipynb — обновлён')
    for cid, sections in [('ch02', CH02_TEMPLATE), ('ch03', CH03_TEMPLATE), ('ch04', CH04_TEMPLATE)]:
        name = f'{cid}-project-template.ipynb'
        chapter_template = make_template(sections, f'{cid}-template')
        if write_if_changed(OUT / name, json.dumps(chapter_template, ensure_ascii=False, indent=1) + '\n'):
            changed += 1
            print(f'{name} — обновлён')
    print(f'Готово: {total} задач в блокнотах, изменено файлов: {changed} → site/notebooks/')
    return 0


# ---------- прогон блокнотов (проверка инфраструктуры) ----------

def _verdicts(cell) -> tuple[list, str | None, list]:
    texts, err = [], None
    for o in cell.outputs:
        if o.output_type == 'error':
            err = f'{o.ename}: {o.evalue}'
        elif o.output_type in ('display_data', 'execute_result'):
            texts.append(o.data.get('text/plain', ''))
        elif o.output_type == 'stream':
            texts.append(o.text)
    return [t for t in texts if t.startswith(('✓ Верно', '✗'))], err, texts


def test(mode: str, chapters: list) -> int:
    """Выполнить копии практикумов через nbclient: с эталонами (mode='solution') или с заготовками ('starter')."""
    import subprocess
    import time
    import nbformat
    from nbclient import NotebookClient
    if mode not in ('solution', 'starter'):
        print('Режим --test: solution или starter.')
        return 2
    # как в браузере — один поток: на занятой машине OpenMP-потоки бустингов только мешают друг другу
    for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ.setdefault(var, '1')
    chapters = chapters or sorted(p.name.split('-')[0] for p in OUT.glob('ch*-practice.ipynb'))
    total_bad = 0
    for ch in chapters:
        tasks = json.loads((TASKS / f'{ch}.json').read_text(encoding='utf-8'))['tasks']
        nb = nbformat.read(OUT / f'{ch}-practice.ipynb', as_version=4)
        keys = {}
        for i, c in enumerate(nb.cells):
            if c.cell_type == 'code' and c.source.startswith('%%task '):
                key = c.source.split('\n', 1)[0].split(' ', 1)[1].strip()
                keys[i] = key
                if mode == 'solution':
                    c.source = f'%%task {key}\n' + tasks[key]['solution']
        t0 = time.time()
        client = NotebookClient(nb, timeout=900, kernel_name='python3', allow_errors=True,
                                resources={'metadata': {'path': str(OUT)}})
        client.execute(stderr=subprocess.DEVNULL)
        bad = []
        for i, key in keys.items():
            verdict, err, texts = _verdicts(nb.cells[i])
            if err:
                bad.append((key, 'магия упала: ' + err))
            elif not verdict:
                bad.append((key, 'нет вердикта: ' + ' | '.join(texts)[:300]))
            elif mode == 'solution' and not verdict[-1].startswith('✓'):
                bad.append((key, verdict[-1][:400] + ' || ' + ' '.join(t for t in texts if not t.startswith('✗'))[-300:]))
            elif mode == 'starter' and verdict[-1].startswith('✓'):
                bad.append((key, 'заготовка прошла проверку'))
        total_bad += len(bad)
        print(f'{ch} [{mode}]: задач {len(keys)}, проблем {len(bad)}, {time.time() - t0:.0f} с', flush=True)
        for k, m in bad:
            print('   ✗', k, '—', m.replace('\n', ' ')[:700], flush=True)
    print(f'Итого проблем: {total_bad}')
    return 1 if total_bad else 0


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--test':
        sys.exit(test(sys.argv[2], sys.argv[3:]))
    sys.exit(main())
