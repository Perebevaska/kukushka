#!/usr/bin/env python3
"""Самопроверка проектного блокнота — то, что ревьюер смотрит первым делом.

    python check_notebook.py мой-проект.ipynb
    python check_notebook.py мой-проект.ipynb --timeout 1200    # долгие ячейки (обучение моделей)
    python check_notebook.py мой-проект.ipynb --no-run          # только статические проверки, без запуска
    python check_notebook.py мой-проект.ipynb --project ch04/09-project   # + сверка чисел с эталонами задач урока

Что проверяется:
  1. блокнот выполняется с чистого ядра сверху вниз без ошибок (nbclient; ваш файл не меняется);
  2. ячейки в сохранённом блокноте запускались по порядку;
  3. нет абсолютных путей (C:\\..., /Users/..., /home/..., ~/...);
  4. нет закомментированного кода;
  5. после каждого раздела «## …» с кодом есть markdown-вывод;
  6. в первой ячейке кода — импорты и RANDOM_STATE; не осталось пометок ✎ из шаблона;
  7. с --project глава/урок: после запуска в том же ядре выполняются проверки задач этого урока
     (те же, что у %%task и на сайте) — по переменным блокнота, без запуска кода задач. Поэтому
     называйте переменные так, как просят задачи урока в браузере. Для сверки нужна папка курса:
     скрипт ищет site/notebooks (dsc.py, tasks/) рядом с собой и с блокнотом, иначе укажите --course ПАПКА_КУРСА.

Нужны пакеты nbformat, nbclient и ipykernel (есть в site/notebooks/requirements.txt).
Запускайте в том же окружении, где работает Jupyter, например:
    uv run --with-requirements requirements.txt python check_notebook.py мой-проект.ipynb
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
import sys
import time
import tokenize
from pathlib import Path

try:
    import nbformat
except ImportError:
    sys.exit('Нет пакета nbformat. Запустите скрипт в окружении курса: '
             'uv run --with-requirements requirements.txt python check_notebook.py файл.ipynb')

ABS_PATH = re.compile(r'''^(?:[A-Za-z]:[\\/]|\\\\|~[\\/]|/(?:Users|home|mnt|Volumes|tmp|var|opt|content|root|media|data|srv)/)''')
SECTION = re.compile(r'^##\s+(?!#)(.+)$', re.M)
CODE_START = re.compile(r'^(import |from \S+ import |print\(|for |if |while |def |class |return\b|with |try:|except\b|'
                        r'[A-Za-z_][\w.]*\s*(\[.*\])?\s*[-+*/]?=[^=]|[A-Za-z_][\w.]*\(|plt\.|df\b|display\()')
MAGIC = re.compile(r'^\s*[%!]')


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.notes: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def cell_label(i: int, cell) -> str:
    first = next((l.strip() for l in cell.source.splitlines() if l.strip()), '')
    if len(first) > 60:
        first = first[:57] + '…'
    return f'ячейка {i + 1} ({first})' if first else f'ячейка {i + 1}'


def strip_magics(src: str) -> str:
    """Строки с %magic и !командами заменяем на pass, чтобы код разбирался как Python (номера строк сохраняются)."""
    return '\n'.join('pass' if MAGIC.match(l) else l for l in src.splitlines())


# ---------- статические проверки ----------

def check_order(nb, rep: Report) -> None:
    code = [(i, c) for i, c in enumerate(nb.cells) if c.cell_type == 'code' and c.source.strip()]
    counts = [(i, c.get('execution_count')) for i, c in code]
    run = [(i, n) for i, n in counts if n is not None]
    if not run:
        rep.note('В сохранённом блокноте нет выводов — ячейки не запускались. Перед сдачей сделайте '
                 'Restart Kernel and Run All Cells и сохраните блокнот вместе с выводами: ревьюер читает их, не запуская код.')
        return
    skipped = [i for i, n in counts if n is None]
    if skipped:
        rep.note('Не запускались ячейки: ' + ', '.join(str(i + 1) for i in skipped[:10]) + (' …' if len(skipped) > 10 else '')
                 + '. Выполните весь блокнот (Run All), чтобы выводы были у всех ячеек.')
    bad = [(a, b) for a, b in zip(run, run[1:]) if b[1] <= a[1]]
    if bad:
        (i1, n1), (i2, n2) = bad[0]
        rep.err(f'Ячейки запускались не по порядку: {cell_label(i1, nb.cells[i1])} — In [{n1}], '
                f'а ниже {cell_label(i2, nb.cells[i2])} — In [{n2}]'
                + (f' (и ещё {len(bad) - 1} таких мест)' if len(bad) > 1 else '')
                + '. Результат мог зависеть от порядка запуска. Сделайте Restart Kernel and Run All Cells и сохраните.')
    elif run[0][1] != 1 or any(b[1] - a[1] != 1 for a, b in zip(run, run[1:])):
        rep.note('Номера In [ ] идут с пропусками — какие-то ячейки запускались по несколько раз или были удалены. '
                 'Перед сдачей полезно сделать Restart Kernel and Run All Cells: номера станут 1, 2, 3, …')


def string_tokens(src: str):
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.STRING:
                yield tok.start[0], tok.string
            elif tok.type == getattr(tokenize, 'FSTRING_MIDDLE', -1):
                yield tok.start[0], tok.string
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return


def check_paths(nb, rep: Report) -> None:
    found = []
    for i, c in enumerate(nb.cells):
        if c.cell_type != 'code':
            continue
        for line, s in string_tokens(strip_magics(c.source)):
            body = re.sub(r'^[rRbBuUfF]{0,2}(\'\'\'|"""|\'|")', '', s)
            if ABS_PATH.match(body):
                found.append(f'{cell_label(i, c)}, строка {line}: {s[:70]}')
    for f in found:
        rep.err(f'Абсолютный путь — {f}. На другом компьютере такого пути нет. Пишите путь относительно блокнота: '
                "Path('../data') / 'файл.csv' или просто 'файл.csv'.")


def looks_like_code(text: str) -> bool:
    text = text.strip()
    if not text or not CODE_START.match(text):
        return False
    try:
        tree = ast.parse(text)
    except SyntaxError:
        # строка внутри блока: «for x in y:», «if a:» — разбираем с телом-заглушкой
        try:
            tree = ast.parse(text + '\n    pass') if text.endswith(':') else None
        except SyntaxError:
            return False
        if tree is None:
            return False
    body = tree.body
    return bool(body) and not all(isinstance(n, ast.Expr) and isinstance(n.value, (ast.Name, ast.Constant)) for n in body)


def check_commented_code(nb, rep: Report) -> None:
    for i, c in enumerate(nb.cells):
        if c.cell_type != 'code':
            continue
        lines = []
        for n, raw in enumerate(c.source.splitlines(), 1):
            s = raw.strip()
            if s.startswith('#') and not s.startswith('#!') and looks_like_code(s.lstrip('#').strip()):
                lines.append(n)
        if lines:
            where = ', '.join(map(str, lines[:6])) + (' …' if len(lines) > 6 else '')
            rep.err(f'Закомментированный код — {cell_label(i, c)}, {"строка" if len(lines) == 1 else "строки"} {where}. Удалите его: старые варианты '
                    'хранит git, а в отчёте они путают читателя. Если код нужен — раскомментируйте и объясните, зачем.')


def check_sections(nb, rep: Report) -> None:
    sections = []           # [заголовок, [ячейки раздела]]
    for i, c in enumerate(nb.cells):
        heads = SECTION.findall(c.source) if c.cell_type == 'markdown' else []
        if heads:
            sections.append([heads[-1].strip(), [], i])
            rest = SECTION.split(c.source)[-1].strip()
            if rest and len(sections) > 0:
                sections[-1][1].append((i, 'md-text'))
            continue
        if sections:
            kind = c.cell_type if c.cell_type == 'code' else ('md-text' if c.source.strip() else 'empty')
            if c.cell_type == 'code' and not c.source.strip():
                kind = 'empty'
            sections[-1][1].append((i, kind))
    if not sections:
        rep.err('В блокноте нет разделов «## …». Нужна структура: ## Цель → ## Данные → ## Предобработка → '
                '## Анализ и модели → ## Выводы (возьмите project-template.ipynb).')
        return
    for title, cells, start in sections:
        kinds = [k for _, k in cells if k != 'empty']
        if 'code' not in kinds:
            continue
        last_code = max(j for j, k in enumerate(kinds) if k == 'code')
        if 'md-text' not in kinds[last_code + 1:]:
            rep.err(f'Раздел «{title}» заканчивается кодом без вывода. Добавьте после последней ячейки кода '
                    'markdown-ячейку: что показал код (с числами) и что это значит для бизнеса.')
    last_title, last_cells, _ = sections[-1]
    if not re.search(r'вывод|итог|рекоменд|заключ', last_title, re.I):
        rep.note(f'Последний раздел — «{last_title}». Обычно блокнот заканчивается разделом «Выводы и рекомендации» '
                 'с ответом на вопрос из «Цели».')


def check_first_cell(nb, rep: Report) -> None:
    code = [c for c in nb.cells if c.cell_type == 'code' and c.source.strip()]
    if not code:
        rep.err('В блокноте нет ни одной ячейки кода.')
        return
    first = code[0].source
    if not re.search(r'^\s*(import|from)\s', first, re.M):
        rep.note('Первая ячейка кода — не импорты. Соберите все import в первой ячейке: читателю сразу видно, '
                 'какие библиотеки нужны.')
    late = [i for i, c in enumerate(nb.cells) if c.cell_type == 'code' and c is not code[0]
            and re.search(r'^(import|from)\s+\S+', c.source, re.M)]
    if late:
        rep.note('Импорты не только в первой ячейке (' + ('ячейка ' if len(late) == 1 else 'ячейки ') + ', '.join(str(i + 1) for i in late[:8])
                 + '). Перенесите их наверх — так видно все зависимости сразу.')
    all_code = '\n'.join(c.source for c in code)
    random_use = re.search(r'random_state|np\.random|sample\(|train_test_split|KFold|RandomForest|shuffle', all_code)
    if random_use and 'RANDOM_STATE' not in first:
        rep.err('В коде есть случайность (разбиение, выборка или модель), а в первой ячейке нет RANDOM_STATE. '
                'Задайте RANDOM_STATE = 42 в начале и передавайте random_state=RANDOM_STATE — иначе числа в выводах '
                'изменятся при следующем запуске.')
    for m in re.finditer(r'random_state\s*=\s*(\d+)', all_code):
        rep.note(f'random_state={m.group(1)} записан числом. Используйте общую константу random_state=RANDOM_STATE.')
        break


def check_placeholders(nb, rep: Report) -> None:
    left = [i for i, c in enumerate(nb.cells) if '✎' in c.source]
    if left:
        rep.err('Остались пометки ✎ из шаблона — ячейки ' + ', '.join(str(i + 1) for i in left[:12])
                + '. Замените их своим текстом (и удалите врезку «Как работать с шаблоном»).')


# ---------- сверка с эталонами задач урока ----------

PROJECT_MARK = '@@dsc-project@@'          # та же метка, что в dsc._project_json
LESSON = re.compile(r'^ch\d\d/[\w.-]+$')
MARKS = {'ok': '✓', 'partial': '✓', 'fail': '✗', 'error': '✗', 'skip': '–'}


def find_course(course: str | None, nb_path: Path) -> Path | None:
    """Папка site/notebooks курса (там dsc.py и tasks/): из --course, рядом со скриптом или блокнотом, выше по папкам."""
    def as_notebooks(p: Path) -> Path | None:
        for cand in (p, p / 'notebooks', p / 'site' / 'notebooks'):
            if (cand / 'dsc.py').is_file() and (cand / 'tasks').is_dir():
                return cand.resolve()
        return None
    if course:
        return as_notebooks(Path(course).expanduser())
    starts = [Path(__file__).resolve().parent, nb_path.resolve().parent]
    for start in starts:
        for p in (start, *start.parents):
            found = as_notebooks(p)
            if found:
                return found
    return None


def lesson_tasks(notebooks: Path, lesson: str) -> tuple[list, str]:
    """Задачи урока из tasks/chNN.json и текст ошибки, если урока нет."""
    ch = lesson.split('/')[0]
    path = notebooks / 'tasks' / f'{ch}.json'
    if not path.exists():
        return [], f'Нет файла задач {path}. Глава пишется как ch04.'
    tasks = json.loads(path.read_text(encoding='utf-8'))['tasks']
    keys = [k for k in tasks if k.rsplit('/', 1)[0] == lesson]
    if keys:
        return keys, ''
    lessons = sorted({k.rsplit('/', 1)[0] for k in tasks})
    projects = [l for l in lessons if 'project' in l] or lessons
    return [], f'В {ch} нет задач урока «{lesson}». Уроки-проекты главы: {", ".join(projects)}.'


def project_cell(notebooks: Path, lesson: str):
    src = (f'import sys as _dsc_sys\n'
           f'if {str(notebooks)!r} not in _dsc_sys.path:\n'
           f'    _dsc_sys.path.insert(0, {str(notebooks)!r})\n'
           f'import dsc as _dsc_mod\n'
           f'_dsc_mod._project_json({lesson!r})')
    return nbformat.v4.new_code_cell(src)


def read_project(cell, rep: Report) -> list | None:
    """Результаты сверки из вывода добавленной ячейки."""
    for o in cell.get('outputs', []):
        if o.get('output_type') == 'error':
            rep.err(f'Сверка с эталонами не выполнилась: {o.get("ename", "")}: {o.get("evalue", "")[:300]}')
            return None
        if o.get('output_type') == 'stream':
            for line in o.get('text', '').splitlines():
                if line.startswith(PROJECT_MARK):
                    data = json.loads(line[len(PROJECT_MARK):])
                    if 'error' in data:
                        rep.err(f'Сверка с эталонами не выполнилась: {data["error"]}')
                        return None
                    return data['results']
    rep.err('Сверка с эталонами не выполнилась: блокнот не дошёл до конца (остановка по времени или падение ядра).')
    return None


def print_project(lesson: str, results: list, rep: Report) -> None:
    title = f'Сверка с эталонами задач урока {lesson}'
    print(f'\n{title}\n' + '-' * len(title))
    for r in results:
        line = f'  {MARKS.get(r["status"], "?")} {r["id"]} — {r["title"]}'
        print(line + (f': {r["msg"]}' if r['msg'] else ''))
    n = len(results)
    ok = sum(r['status'] in ('ok', 'partial') for r in results)
    bad = [r for r in results if r['status'] in ('fail', 'error')]
    skip = [r for r in results if r['status'] == 'skip']
    summary = f'Совпало с эталоном: {ok} из {n}'
    summary += f', не совпало: {len(bad)}' if bad else ''
    summary += f', не проверено: {len(skip)}' if skip else ''
    print(summary + '.')
    if bad:
        rep.err('Не совпали с эталоном задачи урока: ' + ', '.join(r['id'] for r in bad)
                + '. Сообщения — в «Сверке с эталонами» выше; имена переменных должны быть такими, как в задачах урока.')
    if skip:
        rep.note('Без ячейки задачи не проверить: ' + ', '.join(r['id'] for r in skip)
                 + '. Их проверка смотрит на печать, код или график самой задачи — решите их на сайте или в практикуме главы.')


# ---------- запуск ----------

def run_notebook(path: Path, nb, timeout: int, kernel: str, rep: Report, extra=None):
    """Выполнить копию блокнота; extra — ячейка, которую выполнить последней в том же ядре (сверка проекта).
    Возвращает (выполненный блокнот без extra, выполненная extra) или None."""
    try:
        from nbclient import NotebookClient
        from nbclient.exceptions import CellTimeoutError, DeadKernelError
    except ImportError:
        rep.err('Нет пакета nbclient — блокнот не запущен. Поставьте пакеты из requirements.txt.')
        return None
    run_nb = nbformat.from_dict(nb)
    if extra is not None:
        run_nb.cells.append(extra)
    client = NotebookClient(run_nb, timeout=timeout, kernel_name=kernel, allow_errors=True,
                            resources={'metadata': {'path': str(path.parent.resolve())}})
    t0 = time.time()
    print(f'Запускаю блокнот с чистого ядра ({kernel})…', flush=True)
    try:
        # служебные сообщения ядра (например, «Kernel is running over TCP…») к проверке не относятся
        client.execute(stderr=subprocess.DEVNULL)
    except CellTimeoutError:
        rep.err(f'Ячейка выполнялась дольше {timeout} с и была остановлена. Если обучение действительно долгое — '
                'запустите проверку с --timeout 1800 или уменьшите данные для черновика.')
    except DeadKernelError:
        rep.err('Ядро Python упало во время выполнения (часто — не хватило памяти).')
    except Exception as e:  # noqa: BLE001
        rep.err(f'Не удалось запустить блокнот: {type(e).__name__}: {e}')
        return None
    secs = time.time() - t0
    done_extra = run_nb.cells.pop() if extra is not None else None
    failed = []
    warn_cells = []
    for i, c in enumerate(run_nb.cells):
        if c.cell_type != 'code':
            continue
        for o in c.get('outputs', []):
            if o.get('output_type') == 'error':
                failed.append((i, c, o.get('ename', ''), o.get('evalue', '')))
            elif o.get('output_type') == 'stream' and o.get('name') == 'stderr' and 'Warning' in o.get('text', ''):
                warn_cells.append(i)
    if failed:
        i, c, ename, evalue = failed[0]
        rep.err(f'Ошибка при запуске с чистого ядра — {cell_label(i, c)}: {ename}: {evalue[:300]}')
    if len(failed) > 1:
        rest = ', '.join(f'{i + 1} ({ename})' for i, _, ename, _ in failed[1:9]) + (' …' if len(failed) > 9 else '')
        rep.err(f'Следом упали ещё ячейки ({len(failed) - 1}): {rest}. Часто это следствие первой ошибки — '
                'исправьте её и запустите проверку снова.')
    if failed:
        rep.note('Ошибки при запуске с чистого ядра часто значат, что переменная создавалась в ячейке, которую потом '
                 'удалили или изменили. В Jupyter проверьте: Kernel → Restart Kernel and Run All Cells.')
    if warn_cells:
        rep.note('Предупреждения (Warning) в ячейках ' + ', '.join(str(i + 1) for i in sorted(set(warn_cells))[:10])
                 + '. Прочитайте их: часто это будущая ошибка (устаревший параметр, SettingWithCopy). '
                 'Исправьте причину, а не прячьте предупреждение.')
    print(f'Выполнено за {secs:.0f} с.', flush=True)
    return run_nb, done_extra


def main() -> int:
    ap = argparse.ArgumentParser(description='Самопроверка проектного блокнота курса.')
    ap.add_argument('notebook', help='файл .ipynb')
    ap.add_argument('--timeout', type=int, default=600, help='лимит на одну ячейку, секунд (по умолчанию 600)')
    ap.add_argument('--kernel', default='python3', help='имя ядра Jupyter (по умолчанию python3 — текущее окружение)')
    ap.add_argument('--no-run', action='store_true', help='не запускать блокнот, только статические проверки')
    ap.add_argument('--project', metavar='ГЛАВА/УРОК',
                    help='сверить переменные блокнота с эталонами задач урока, например ch04/09-project')
    ap.add_argument('--course', metavar='ПАПКА',
                    help='папка курса (или её site/notebooks) — если скрипт и блокнот лежат вне неё')
    args = ap.parse_args()
    path = Path(args.notebook)
    if not path.exists():
        print(f'Нет файла {path}.')
        return 2
    extra = None
    lesson = (args.project or '').strip().strip('/')
    if args.project:
        if args.no_run:
            print('--project сверяет числа после запуска блокнота — уберите --no-run.')
            return 2
        if not LESSON.match(lesson):
            print(f'--project {args.project}: нужен адрес урока вида ch04/09-project (глава/урок, как в адресах задач).')
            return 2
        notebooks = find_course(args.course, path)
        if notebooks is None:
            where = f'в {args.course}' if args.course else 'рядом со скриптом, с блокнотом и выше по папкам'
            print(f'Для --project нужна папка курса: не нашёл site/notebooks с dsc.py и tasks/ {where}. '
                  'Укажите её: --course ПАПКА_КУРСА (папка распакованного архива курса).')
            return 2
        keys, problem = lesson_tasks(notebooks, lesson)
        if problem:
            print(problem)
            return 2
        extra = project_cell(notebooks, lesson)
    try:
        nb = nbformat.read(path, as_version=4)
    except Exception as e:  # noqa: BLE001
        print(f'Не получилось прочитать {path} как блокнот: {e}')
        return 2
    rep = Report()
    check_order(nb, rep)
    check_first_cell(nb, rep)
    check_paths(nb, rep)
    check_commented_code(nb, rep)
    check_sections(nb, rep)
    check_placeholders(nb, rep)
    project = None
    if not args.no_run:
        ran = run_notebook(path, nb, args.timeout, args.kernel, rep, extra)
        if extra is not None:
            project = read_project(ran[1], rep) if ran else None
            if ran is None:
                rep.err('Сверка с эталонами не выполнилась: блокнот не запустился.')

    print(f'\nПроверка блокнота {path.name}')
    print('=' * (17 + len(path.name)))
    if project is not None:
        print_project(lesson, project, rep)
    if rep.errors:
        print('\nНадо исправить:')
        for k, e in enumerate(rep.errors, 1):
            print(f'  {k}. {e}')
    if rep.notes:
        print('\nСтоит посмотреть:')
        for n in rep.notes:
            print(f'  • {n}')
    if not rep.errors and not rep.notes:
        print('\nЗамечаний нет.')
    verdict = ('Можно отправлять на ревью.' if not rep.errors else 'Исправьте пункты из «Надо исправить» и запустите проверку снова.')
    print(f'\nИтог: исправить — {len(rep.errors)}, посмотреть — {len(rep.notes)}. {verdict}')
    if args.no_run:
        print('(Блокнот не запускался: проверка с --no-run.)')
    return 1 if rep.errors else 0


if __name__ == '__main__':
    sys.exit(main())
