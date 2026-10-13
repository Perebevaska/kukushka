"""Задачи курса «Data Science для аналитиков» в своём Jupyter.

Подключение — в первой ячейке блокнота из папки site/notebooks:

    %load_ext dsc

Задача решается в ячейке, первая строка которой — магия с адресом задачи:

    %%task ch02/04-groupby/top-shop
    by_shop = orders.groupby('shop')['total'].sum()
    by_shop

Ячейка выполняется как обычная ячейка блокнота (переменные остаются для следующих
ячеек), а потом та же проверка, что и на сайте, пишет «✓ Верно» или что не так. Переменные-ответы
задачи перед запуском стираются: проверка смотрит на результат именно этого запуска.

    dsc.hint('top-shop')                 # следующая подсказка (или dsc.hint('top-shop', 2))
    dsc.solution('top-shop', sure=True)  # эталонное решение и разбор
    dsc.progress()                       # что решено в этом сеансе
    dsc.check_project('ch04/09-project') # сверить переменные проектного блокнота с эталонами задач урока

Сверка проекта не запускает код задач: проверки урока смотрят на переменные, которые уже посчитал
блокнот (их имена — как в задачах урока на сайте). То же делает python check_notebook.py проект.ipynb --project ch04/09-project.

Проверки и помощники (need, printed, calls, ax_of …) берутся из site/assets/harness.py —
того же файла, что работает в браузере. Данные из site/data копируются в рабочую папку
site/notebooks/_work, и код запускается в ней: `pd.read_csv('orders.csv')` работает,
как на сайте, а файлы, которые создаёт ваш код, не попадают в данные курса.
"""
from __future__ import annotations

import ast
import builtins
import difflib
import html
import importlib.util
import io
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # site/notebooks
SITE = HERE.parent                              # site
DATA = SITE / 'data'
TASKS_DIR = HERE / 'tasks'
WORK = HERE / '_work'
HARNESS = SITE / 'assets' / 'harness.py'

LEVELS = {'warmup': 'разминка', 'base': 'база', 'plus': 'посложнее', 'star': 'со звёздочкой'}

_harness = None
_tasks: dict = {}           # 'chNN/урок/id' → задача
_loaded: set = set()        # какие главы уже прочитаны
_hint_shown: dict = {}      # сколько подсказок открыто
_results: dict = {}         # результат последнего запуска задачи в этом сеансе


# ---------- загрузка ----------

def _load_harness():
    """harness.py курса как модуль. Он ставит MPLBACKEND=Agg для браузера — в Jupyter это не нужно:
    графики должны показываться под ячейкой, поэтому переменную окружения возвращаем как было."""
    global _harness
    if _harness is not None:
        return _harness
    if not HARNESS.exists():
        raise FileNotFoundError(f'Не нашёл {HARNESS}. Блокнот должен лежать в папке site/notebooks курса.')
    before = os.environ.get('MPLBACKEND')
    spec = importlib.util.spec_from_file_location('_dsc_harness', HARNESS)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    finally:
        if before is None:
            os.environ.pop('MPLBACKEND', None)
        else:
            os.environ['MPLBACKEND'] = before
    sys.modules['_dsc_harness'] = mod
    _harness = mod
    return mod


def _load_chapter(ch: str) -> None:
    if ch in _loaded:
        return
    path = TASKS_DIR / f'{ch}.json'
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        _tasks.update(data['tasks'])
    _loaded.add(ch)


def _load_all() -> None:
    for p in sorted(TASKS_DIR.glob('ch*.json')):
        _load_chapter(p.stem)


def _find(key: str) -> tuple[str, dict]:
    """Задача по полному адресу 'ch02/04-groupby/top-shop' или по короткому id 'top-shop'."""
    key = key.strip().strip('\'"')
    if key.count('/') == 2:
        _load_chapter(key.split('/')[0])
        if key in _tasks:
            return key, _tasks[key]
    _load_all()
    if key in _tasks:
        return key, _tasks[key]
    same = [k for k in _tasks if k.rsplit('/', 1)[-1] == key.rsplit('/', 1)[-1]]
    if len(same) == 1 and '/' not in key:
        return same[0], _tasks[same[0]]
    if len(same) > 1:
        raise LookupError(f'Задача «{key}» есть в нескольких уроках: {", ".join(same)}. Укажите полный адрес.')
    near = difflib.get_close_matches(key, list(_tasks), n=3, cutoff=0.5)
    tip = f' Может быть: {", ".join(near)}?' if near else ''
    raise LookupError(f'Не нашёл задачу «{key}».{tip} Адрес задачи — как в первой строке её ячейки: глава/урок/id.')


def _ref(key: str) -> str:
    """Как сослаться на задачу в подсказке: короткий id, если он не повторяется в курсе, иначе полный адрес."""
    _load_all()
    short = key.rsplit('/', 1)[-1]
    return short if sum(1 for k in _tasks if k.rsplit('/', 1)[-1] == short) == 1 else key


def _sync_data() -> None:
    """Копия site/data в рабочей папке: копируем только файлы, которые отличаются от исходных.
    Копия, которую изменил код (например, df.to_csv('orders.csv')), перед следующей задачей
    возвращается к исходной — как на сайте, где каждый запуск получает свежие файлы."""
    WORK.mkdir(exist_ok=True)
    if not DATA.exists():
        return
    for src in DATA.iterdir():
        if not src.is_file() or src.name.startswith('.'):
            continue
        dst = WORK / src.name
        st = src.stat()
        try:
            dt = dst.stat()
            if dt.st_size == st.st_size and dt.st_mtime == st.st_mtime:
                continue
        except OSError:
            pass
        # сначала во временный файл, потом подмена: другое ядро (второй открытый блокнот)
        # никогда не увидит наполовину скопированную базу
        tmp = WORK / f'.{src.name}.{os.getpid()}.tmp'
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)


_OUT_EXT = {'csv', 'md', 'txt', 'json', 'jsonl', 'parquet', 'pkl', 'joblib', 'png', 'xlsx', 'sqlite', 'db', 'html'}


def _output_files(t: dict) -> list:
    """Файлы, которые задача должна создать сама: имя есть строкой в проверке и в эталоне,
    но его нет в подготовке и в данных курса."""
    try:
        tree = ast.parse(t['check'])
    except SyntaxError:
        return []
    names = []
    for node in ast.walk(tree):
        name = node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ''
        if ('.' not in name or len(name) > 80 or '/' in name or '\\' in name or ' ' in name
                or name.rsplit('.', 1)[-1] not in _OUT_EXT or name not in t['solution'] or name in t['setup']):
            continue
        if (DATA / name).exists() or name in names:
            continue
        names.append(name)
    return names


def _forget_outputs(t: dict) -> None:
    """Файлы, которые задача должна создать сама (проверка смотрит на них, эталон их пишет),
    удаляем из рабочей папки перед запуском. Иначе файл от прошлой удачной попытки
    засчитал бы и неверный код: проверка должна видеть файл, созданный именно этим запуском."""
    for name in _output_files(t):
        try:
            (WORK / name).unlink()
        except OSError:
            pass


class _TopNames(ast.NodeVisitor):
    """Имена, которым код присваивает значение на верхнем уровне (без тел функций, классов и генераторов)."""

    def __init__(self):
        self.names: set = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_FunctionDef(self, node):
        self.names.add(node.name)

    visit_AsyncFunctionDef = visit_ClassDef = visit_FunctionDef

    def visit_Lambda(self, node):
        pass

    visit_ListComp = visit_SetComp = visit_DictComp = visit_GeneratorExp = visit_Lambda


def _forget_vars(t: dict, ns: dict) -> None:
    """Переменные-результаты задачи (их создаёт эталон, на них смотрит проверка) убираем перед запуском.
    На сайте каждый запуск идёт с чистого листа; в блокноте без этого значение от прошлой удачной
    попытки осталось бы в памяти, и ячейку с неверным или пустым кодом проверка засчитала бы.
    Подготовка задачи выполняется уже после очистки, поэтому её переменные на месте."""
    try:
        sol, chk = ast.parse(t['solution']), ast.parse(t['check'])
    except SyntaxError:
        return
    v = _TopNames()
    v.visit(sol)
    used = {n.id for n in ast.walk(chk) if isinstance(n, ast.Name)}
    strs = {n.value for n in ast.walk(chk) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value.isidentifier()}
    prefixes = tuple(s for s in strs if len(s) > 1 and s.endswith('_'))   # need('p_' + nm) → p_all, p_short …
    for name in v.names:
        if name.startswith('__'):
            continue
        if name in used or name in strs or (prefixes and name.startswith(prefixes)):
            ns.pop(name, None)


# ---------- вывод ----------

def _show(plain: str, html_text: str | None = None) -> None:
    try:
        from IPython.display import display
        bundle = {'text/plain': plain}
        if html_text:
            bundle['text/html'] = html_text
        display(bundle, raw=True)
    except ImportError:
        print(plain)


def _box(plain: str, kind: str) -> None:
    colors = {'ok': ('#1b7f3b', '#e8f5ec'), 'err': ('#b3261e', '#fdecea'), 'info': ('#5b5b5b', '#f2f2f2')}
    fg, bg = colors[kind]
    body = html.escape(plain).replace('\n', '<br>')
    _show(plain, f'<div style="border-left:4px solid {fg};background:{bg};color:#1d1d1d;padding:8px 12px;'
                 f'margin:6px 0;font-family:system-ui,sans-serif;font-size:14px;line-height:1.45">{body}</div>')


def _markdown(text: str) -> None:
    try:
        from IPython.display import Markdown, display
        display(Markdown(text))
    except ImportError:
        print(text)


class _Tee(io.TextIOBase):
    """Пишет и в ячейку (вывод виден сразу), и в буфер — для проверки (_out, printed …)."""

    def __init__(self, stream, buf):
        self.stream, self.buf = stream, buf

    def write(self, s):
        self.buf.write(s)
        return self.stream.write(s)

    def flush(self):
        self.stream.flush()

    def isatty(self):
        return False

    @property
    def encoding(self):
        return getattr(self.stream, 'encoding', 'utf-8')


def _is_mpl(value) -> bool:
    mod = type(value).__module__ or ''
    first = value[0] if isinstance(value, (list, tuple)) and value else None
    return mod.startswith('matplotlib') or (type(first).__module__ or '').startswith('matplotlib')


# ---------- запуск задачи ----------

def _later_show(*args, **kwargs):
    """plt.show() внутри задачи: график покажем после проверки (см. _flush_figures)."""


def _flush_figures():
    plt = sys.modules.get('matplotlib.pyplot')
    if plt and plt.get_fignums():
        sys.stdout.flush()
        plt.show()       # inline-бэкенд Jupyter рисует графики под ячейкой и закрывает их


def _import_pyplot():
    """pyplot заранее — чтобы перехватить plt.show и в ячейке, где он импортируется впервые."""
    try:
        import matplotlib.pyplot  # noqa: F401
    except ImportError:
        pass


def run_task(key: str, cell: str, ns: dict, transformed: str | None = None) -> dict:
    """Выполнить код ячейки в пространстве имён блокнота и проверить задачу.
    Возвращает {'passed': bool, 'msg': str, 'error': str | None}."""
    h = _load_harness()
    key, t = _find(key)
    code = cell if transformed is None else transformed
    _sync_data()
    os.chdir(WORK)
    _forget_outputs(t)
    _forget_vars(t, ns)
    if 'pandas' in code or 'pandas' in t['setup']:
        h._pandas_options()
    res = {'passed': False, 'msg': '', 'error': None}
    # строка 1 ячейки — «%%task …», поэтому код сдвигаем на строку: номера строк в ошибках совпадут с ячейкой
    src = '\n' + code
    buf = io.StringIO()
    old_out = sys.stdout
    sys.stdout = _Tee(old_out, buf)
    # plt.show() в браузере ничего не закрывает, а в Jupyter показывает и закрывает график —
    # тогда проверке было бы нечего смотреть. Пока идёт код задачи, show только откладываем.
    plt = sys.modules.get('matplotlib.pyplot')
    real_show = plt.show if plt else None
    if plt:
        plt.show = _later_show
    ok = True
    try:
        if t['setup']:
            exec(compile(t['setup'], '<подготовка>', 'exec'), ns)
        body, last = h._split_last_expr(src)
        if last is None:
            exec(compile(src, h._USER, 'exec'), ns)
        else:
            exec(compile(body, h._USER, 'exec'), ns)
            value = eval(compile(last, h._USER, 'eval'), ns)
            if value is not None and not _is_mpl(value):
                sys.stdout.flush()
                try:
                    from IPython.display import display
                    display(value)
                except ImportError:
                    print(repr(value))
    except BaseException as e:  # noqa: BLE001 — любую ошибку показываем понятным текстом
        ok = False
        err = h._fmt_error(e, src, ns)
        res['error'] = err['text']
    finally:
        sys.stdout = old_out
        if plt:
            plt.show = real_show
    out = buf.getvalue()
    if not ok:
        _box(res['error'], 'err')
        res['msg'] = 'Код завершился с ошибкой — сначала исправьте её (сообщение выше).'
    else:
        plt = sys.modules.get('matplotlib.pyplot')
        h._LAST_FIGS = [plt.figure(n) for n in plt.get_fignums()] if plt else []
        cns = dict(ns)
        cns.update(h._helpers(out, cell.strip('\n') if transformed is None else code, ns))
        sink, sys.stdout = sys.stdout, io.StringIO()   # print внутри функций ученика при проверке не нужен
        try:
            exec(compile(t['check'], '<проверка>', 'exec'), cns)
            res['passed'] = True
        except AssertionError as e:
            res['msg'] = str(e) or 'Результат пока не совпадает с ожидаемым.'
        except Exception as e:  # noqa: BLE001
            res['msg'] = (f'Проверка споткнулась: {type(e).__name__}: {e}. '
                          'Скорее всего, в переменной лежит не то, что ожидалось.')
        finally:
            sys.stdout = sink
            h._LAST_FIGS = []
    _flush_figures()                       # графики — под выводом кода, перед вердиктом
    _results[key] = res['passed']
    if res['passed']:
        _box('✓ Верно', 'ok')
    elif t.get('exam'):
        _box('✗ Пока не верно. В контрольной проверка говорит только «верно» или «нет».', 'err')
    else:
        n = len(t['hints'])
        more = f'\nПодсказка: dsc.hint({_ref(key)!r})' if n else ''
        _box(f'✗ Пока не верно. {res["msg"]}{more}', 'err')
    return res


def hint(task: str, n: int | None = None) -> None:
    """Показать подсказку: следующую по порядку или с номером n (с 1)."""
    key, t = _find(task)
    hints = t['hints']
    if not hints:
        _box('У этой задачи нет подсказок.', 'info')
        return
    if n is None:
        n = min(_hint_shown.get(key, 0) + 1, len(hints))
    if not 1 <= n <= len(hints):
        _box(f'У задачи {len(hints)} подсказк{"а" if len(hints) == 1 else "и"}: номер от 1 до {len(hints)}.', 'info')
        return
    _hint_shown[key] = max(_hint_shown.get(key, 0), n)
    tail = f' Следующая: dsc.hint({_ref(key)!r}).' if n < len(hints) else ''
    _markdown(f'**Подсказка {n} из {len(hints)}** · {t["title"]}\n\n{hints[n - 1]}')
    if tail:
        _box(tail.strip(), 'info')


def solution(task: str, sure: bool = False) -> None:
    """Эталонное решение и разбор. Чтобы не подсмотреть случайно, нужен аргумент sure=True."""
    key, t = _find(task)
    short = _ref(key)
    if not sure:
        _box('Решение откроется, если вызвать его ещё раз с подтверждением:\n'
             f'    dsc.solution({short!r}, sure=True)\n'
             f'Сначала попробуйте подсказки: dsc.hint({short!r}). Решение, найденное самому, запоминается лучше.', 'info')
        return
    text = f'**Решение** · {t["title"]}\n\n```python\n{t["solution"]}\n```'
    if t.get('explain'):
        text += f'\n\n**Разбор.** {t["explain"]}'
    _markdown(text)


def progress() -> None:
    """Что решено в этом сеансе Jupyter (прогресс сайта и блокнотов хранится отдельно)."""
    if not _results:
        _box('В этом сеансе ещё не запускалась ни одна задача.', 'info')
        return
    by_ch: dict = {}
    for k, ok in _results.items():
        by_ch.setdefault(k.split('/')[0], []).append(ok)
    lines = [f'{ch}: верно {sum(v)} из {len(v)} запущенных' for ch, v in sorted(by_ch.items())]
    wrong = [k for k, ok in _results.items() if not ok]
    if wrong:
        lines.append('Ещё не решены: ' + ', '.join(wrong))
    _box('\n'.join(lines), 'info')


def tasks(chapter: str) -> list:
    """Адреса всех задач главы, например dsc.tasks('ch03')."""
    _load_chapter(chapter)
    return [k for k in _tasks if k.startswith(chapter + '/')]


# ---------- проверка проекта по эталонам ----------

# Помощники проверки, которым нужна ячейка задачи (её печать, код или график). В проектном
# блокноте такой ячейки нет: части проверки с ними пропускаются и помечаются «не проверено».
_CELL_HELPERS = {
    '_out': 'печать', '_lines': 'печать', 'printed': 'печать', 'printed_line': 'печать',
    '_code': 'код ячейки', 'calls': 'код ячейки', 'uses_fstring': 'код ячейки', 'has_literal': 'код ячейки',
    'figs': 'график', 'ax_of': 'график',
}


class _NeedCell(Exception):
    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


def _needs_cell(kind: str):
    def helper(*args, **kwargs):
        raise _NeedCell(kind)
    return helper


def _produced(t: dict) -> set:
    """Имена, которые создаёт или меняет код задачи (эталон): присваивание на верхнем уровне,
    а также df['x'] = … и obj.attr = … — их значение берём из блокнота ученика, а не из подготовки."""
    try:
        tree = ast.parse(t['solution'])
    except SyntaxError:
        return set()
    v = _TopNames()
    v.visit(tree)
    names = set(v.names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        else:
            continue
        for tg in targets:
            for sub in ast.walk(tg):
                if isinstance(sub, (ast.Subscript, ast.Attribute)):
                    base = sub.value
                    while isinstance(base, (ast.Subscript, ast.Attribute)):
                        base = base.value
                    if isinstance(base, ast.Name):
                        names.add(base.id)
    return names


def _stmt_names(stmt) -> tuple[set, set, set]:
    """Все имена инструкции, читаемые имена и имена, которым она присваивает значение."""
    every, loads, stores = set(), set(), set()
    for n in ast.walk(stmt):
        if isinstance(n, ast.Name):
            every.add(n.id)
            (stores if isinstance(n.ctx, (ast.Store, ast.Del)) else loads).add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            stores.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            stores.update((a.asname or a.name).split('.')[0] for a in n.names)
    return every, loads, stores


def _check_in_namespace(t: dict, ns: dict, h, later: dict | None = None) -> dict:
    """Проверка задачи по готовым переменным ns — без запуска кода задачи.
    status: ok — всё сошлось; partial — значения сошлись, но часть проверки требует ячейки задачи;
    skip — проверить нечего без ячейки; fail — не совпало; error — не выполнилась подготовка."""
    try:
        tree = ast.parse(t['check'])
    except SyntaxError as e:
        return {'status': 'error', 'msg': f'Проверка задачи не разбирается: {e}.', 'skipped': []}
    sns = {'__name__': '__main__', '__builtins__': builtins}
    if t['setup']:
        try:
            exec(compile(t['setup'], '<подготовка>', 'exec'), sns)
        except Exception as e:  # noqa: BLE001
            return {'status': 'error', 'skipped': [],
                    'msg': f'Не выполнилась подготовка проверки: {type(e).__name__}: {e}.'}
    # то, что задача получает готовым (подготовка), — эталонное; то, что создаёт её код, — из блокнота
    produced = _produced(t)
    env = dict(ns)
    for k, v in sns.items():
        if k.startswith('__'):
            continue
        if k not in produced or k not in env:
            env[k] = v
    cns = dict(env)
    cns.update(h._helpers('', '', env))
    for name, kind in _CELL_HELPERS.items():
        cns[name] = _needs_cell(kind)
    tainted: set = set()
    skipped: list = []
    checked = 0
    deps: dict = {}        # имя внутри проверки → переменные блокнота, от которых зависит его значение
    for stmt in tree.body:
        every, loads, stores = _stmt_names(stmt)
        # need('x') — переменная блокнота; имя, которое уже присвоила сама проверка, — её локальное значение
        refs = {n.value for n in ast.walk(stmt) if isinstance(n, ast.Constant)
                and isinstance(n.value, str) and n.value.isidentifier()}
        for n in loads:
            refs |= deps[n] if n in deps else {n}
        for n in stores:
            deps[n] = refs
        kinds = sorted({_CELL_HELPERS[n] for n in every if n in _CELL_HELPERS})
        if kinds or loads & tainted:
            skipped.extend(k for k in kinds if k not in skipped)
            tainted |= stores
            continue
        try:
            exec(compile(ast.Module(body=[stmt], type_ignores=[]), '<проверка>', 'exec'), cns)
        except _NeedCell as e:
            if e.kind not in skipped:
                skipped.append(e.kind)
            tainted |= stores
            continue
        except Exception as e:  # noqa: BLE001
            # «не проверено» — только если споткнулась инструкция, читающая переписанную позже переменную
            clash = _clash(refs & produced, ns, later or {})
            if clash:
                # переменную задачи потом переписала другая задача урока: в блокноте её значение уже другое
                return {'status': 'skip', 'skipped': skipped,
                        'msg': 'не проверено: ' + '; '.join(f'{v} позже пересчитывает задача «{w}»'
                                                            for v, w in clash.items())}
            if isinstance(e, FileNotFoundError) and e.filename:
                return {'status': 'fail', 'skipped': skipped,
                        'msg': f'Нет файла {e.filename}. Его создаёт код задачи — сохраните файл в папку блокнота '
                               'под этим именем.'}
            if isinstance(e, AssertionError):
                return {'status': 'fail', 'msg': str(e) or 'Результат пока не совпадает с ожидаемым.', 'skipped': skipped}
            return {'status': 'fail', 'skipped': skipped,
                    'msg': f'Проверка споткнулась: {type(e).__name__}: {e}. '
                           'Скорее всего, в переменной лежит не то, что ожидалось.'}
        if 'need' in loads or any(isinstance(n, ast.Assert) for n in ast.walk(stmt)):
            checked += 1
    if not skipped:
        return {'status': 'ok', 'msg': '', 'skipped': []}
    what = ', '.join(skipped)
    if checked:
        return {'status': 'partial', 'skipped': skipped,
                'msg': f'значения верны; не проверено: нужен вывод ячейки ({what})'}
    return {'status': 'skip', 'skipped': skipped, 'msg': f'не проверено: нужен вывод ячейки ({what})'}


def _clash(names: set, ns: dict, later: dict) -> dict:
    """Из переменных, на которых споткнулась проверка (их создаёт эта задача), — те, что есть в блокноте
    и которые снова создаёт задача ниже по уроку: в блокноте осталось только её значение.
    Переменной нет в блокноте или ошибка в другой переменной — это обычное несовпадение, а не конфликт имён."""
    return {v: later[v] for v in sorted(names) if v in later and v in ns and not v.startswith('_')}


def _lesson_keys(lesson: str) -> list:
    lesson = lesson.strip().strip('\'"').strip('/')
    ch = lesson.split('/')[0]
    _load_chapter(ch)
    keys = [k for k in _tasks if k.rsplit('/', 1)[0] == lesson]
    if not keys:
        lessons = sorted({k.rsplit('/', 1)[0] for k in _tasks if k.startswith(ch + '/')})
        near = difflib.get_close_matches(lesson, lessons, n=3, cutoff=0.5)
        tip = f' Может быть: {", ".join(near)}?' if near else ''
        raise LookupError(f'Не нашёл задач урока «{lesson}».{tip} Адрес урока — глава/урок, '
                          'например ch04/09-project.')
    return keys


_MARK = {'ok': '✓', 'partial': '✓', 'fail': '✗', 'error': '✗', 'skip': '–'}


class _ProjectResults(list):
    """Список результатов сверки: в Jupyter не печатается вторым разом под рамкой."""

    def __repr__(self):
        return project_summary(self)

    def _ipython_display_(self):
        pass


def check_project(lesson: str, ns: dict | None = None, show: bool = True) -> list:
    """Сверить переменные проектного блокнота с эталонами задач урока, например
    dsc.check_project('ch04/09-project') в последней ячейке блокнота.

    Код задач не выполняется: проверки урока (те же, что у %%task и на сайте) смотрят на переменные,
    которые уже посчитал ваш блокнот, — поэтому называйте их так, как просят задачи урока.
    Части проверок, которым нужна сама ячейка задачи (печать, код, график), помечаются «не проверено».
    Возвращает список {'key', 'id', 'title', 'status', 'msg', 'skipped'}."""
    keys = _lesson_keys(lesson)
    if ns is None:
        try:
            from IPython import get_ipython
            ip = get_ipython()
        except ImportError:
            ip = None
        ns = ip.user_ns if ip is not None else sys._getframe(1).f_globals
    h = _load_harness()
    cwd = os.getcwd()
    try:
        in_work = Path(cwd).resolve() == WORK.resolve()
    except OSError:
        in_work = False
    plt = sys.modules.get('matplotlib.pyplot')
    figs_before = set(plt.get_fignums()) if plt else set()
    results = _ProjectResults()
    old_out = sys.stdout
    try:
        _sync_data()
        os.chdir(WORK)       # проверки читают данные курса из рабочей папки, как в %%task
        for i, key in enumerate(keys):
            t = _tasks[key]
            later = {}                 # имя → задача ниже по уроку, которая тоже его создаёт
            for k2 in reversed(keys[i + 1:]):
                later.update(dict.fromkeys(_produced(_tasks[k2]), _tasks[k2]['id']))
            # файлы, которые задача создаёт сама (отчёт, модель), проверка ищет в рабочей папке:
            # берём их из папки блокнота, а не от прошлых запусков задач
            if not in_work:
                for name in _output_files(t):
                    try:
                        (WORK / name).unlink()
                    except OSError:
                        pass
                    src = Path(cwd) / name
                    if src.is_file():
                        shutil.copy2(src, WORK / name)
            sys.stdout = io.StringIO()            # print внутри подготовки и функций ученика не нужен
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    r = _check_in_namespace(t, ns, h, later)
            finally:
                sys.stdout = old_out
            r.update(key=key, id=t['id'], title=t['title'])
            results.append(r)
            _sync_data()     # подготовка могла изменить копию данных
    finally:
        sys.stdout = old_out
        os.chdir(cwd)
        plt = sys.modules.get('matplotlib.pyplot')
        if plt:
            for n in set(plt.get_fignums()) - figs_before:
                plt.close(n)
    if show:
        _show_project(lesson, results)
    return results


def project_summary(results: list) -> str:
    n = len(results)
    ok = sum(r['status'] in ('ok', 'partial') for r in results)
    bad = sum(r['status'] in ('fail', 'error') for r in results)
    skip = sum(r['status'] == 'skip' for r in results)
    text = f'Совпало с эталоном: {ok} из {n}'
    if bad:
        text += f', не совпало: {bad}'
    if skip:
        text += f', не проверено: {skip}'
    return text + '.'


def _show_project(lesson: str, results: list) -> None:
    lines = [f'Сверка с эталонами задач урока {lesson.strip().strip("/")}:']
    for r in results:
        line = f'{_MARK[r["status"]]} {r["id"]} — {r["title"]}'
        if r['msg']:
            line += f': {r["msg"]}'
        lines.append(line)
    lines.append(project_summary(results))
    bad = any(r['status'] in ('fail', 'error') for r in results)
    _box('\n'.join(lines), 'err' if bad else 'ok')


_JSON_MARK = '@@dsc-project@@'


def _project_json(lesson: str) -> None:
    """Для check_notebook.py --project: результаты одной строкой JSON с меткой."""
    try:
        payload = {'results': check_project(lesson, show=False)}
    except Exception as e:  # noqa: BLE001
        payload = {'error': f'{type(e).__name__}: {e}' if not isinstance(e, LookupError) else str(e)}
    print(_JSON_MARK + json.dumps(payload, ensure_ascii=False), flush=True)


# ---------- расширение IPython ----------

def _task_magic(line, cell):
    from IPython import get_ipython
    ip = get_ipython()
    key = line.strip()
    if not key:
        _box('После %%task нужен адрес задачи: %%task глава/урок/id (он уже стоит в ячейках блокнота).', 'err')
        return
    try:
        _find(key)
    except LookupError as e:
        _box(str(e), 'err')
        return
    py = ip.transform_cell(cell)           # %time, !команды и т. п. внутри ячейки — как в обычной ячейке
    transformed = None if py.strip() == cell.strip() else py
    run_task(key, cell, ip.user_ns, transformed)


def load_ipython_extension(ip):
    if str(HERE) not in sys.path:          # после chdir в _work модуль должен находиться и для %reload_ext dsc
        sys.path.insert(0, str(HERE))
    _load_harness()
    _sync_data()
    os.chdir(WORK)
    _import_pyplot()
    ip.register_magic_function(_task_magic, magic_kind='cell', magic_name='task')
    ip.push({'dsc': sys.modules[__name__]})
    _load_all()
    n = len(_tasks)
    _box(f'Курс подключён: задач — {n}. Рабочая папка: {WORK}\n'
         'Решайте в ячейках с %%task и запускайте Shift+Enter. '
         'Подсказка — dsc.hint("id"), решение — dsc.solution("id", sure=True).', 'info')


def unload_ipython_extension(ip):
    pass
