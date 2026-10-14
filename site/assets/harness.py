# Исполнитель кода курса. Один и тот же файл работает в браузере (Pyodide, runner.js)
# и в проверке задач (tools/verify.mjs). Каждый запуск — в чистом пространстве имён.
import ast
import builtins
import io
import re
import os
import sys
import traceback
import warnings

# графики рисуем в картинку (в Web Worker нет страницы, куда выводить окно)
os.environ.setdefault('MPLBACKEND', 'Agg')
warnings.filterwarnings('ignore', message='.*non-interactive.*')
warnings.filterwarnings('ignore', message='.*cannot be shown.*')
warnings.filterwarnings('ignore', message='.*parameter as float was deprecated.*')
warnings.filterwarnings('ignore', message='.*as_object_map.*')   # Pyodide: threadpoolctl при первом импорте sklearn

_USER = '<ваш код>'


# ---------- local_llm: своя языковая модель в LM Studio (урок 13.4) ----------
# В браузере нет библиотеки openai и обычных сетевых запросов из Python, поэтому модуль
# ходит в LM Studio синхронным XMLHttpRequest (в Web Worker это разрешено).
# В своём Jupyter то же самое делают клиентом openai — код показан в уроке.
_LOCAL_LLM_SRC = r"""
import json as _json
import re as _re

URL = 'http://localhost:1234/v1'
_HOWTO = ('Проверьте: 1) LM Studio запущен; 2) на вкладке Developer сервер в состоянии Running (порт 1234); '
          '3) в настройках сервера включён CORS; 4) курс открыт через запускалку (адрес http://127.0.0.1:8000). '
          'Индикатор «LM Studio» вверху страницы показывает, что именно не так.')


class LocalLLMError(Exception):
    pass


def _request(method, path, body=None, timeout=180):
    try:
        from js import XMLHttpRequest
    except ImportError:
        raise LocalLLMError('Модуль local_llm работает только в браузере курса. В своём Jupyter используйте клиент openai (см. урок).') from None
    x = XMLHttpRequest.new()
    x.open(method, URL + path, False)
    x.timeout = int(timeout * 1000)
    if body is not None:
        x.setRequestHeader('Content-Type', 'application/json')
    try:
        x.send(_json.dumps(body, ensure_ascii=False) if body is not None else None)
    except Exception:
        raise LocalLLMError('LM Studio не отвечает на ' + URL + '. ' + _HOWTO) from None
    if x.status != 200:
        raise LocalLLMError(f'LM Studio ответил кодом {x.status}: {str(x.responseText)[:300]}')
    return _json.loads(x.responseText)


def models():
    # имена моделей, которые видит сервер LM Studio (без моделей эмбеддингов)
    data = _request('GET', '/models', timeout=10).get('data', [])
    return [m['id'] for m in data if 'embed' not in m['id'].lower()]


def ask(prompt, system=None, model=None, temperature=0.0, max_tokens=400):
    # один вопрос модели — ответ строкой; рассуждения вида <think>…</think> вырезаются
    if model is None:
        names = models()
        if not names:
            raise LocalLLMError('Сервер LM Studio работает, но модели нет. Скачайте модель на вкладке Discover и загрузите её (Load).')
        model = names[0]
    messages = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': prompt}]
    data = _request('POST', '/chat/completions', {'model': model, 'messages': messages,
                                                  'temperature': temperature, 'max_tokens': max_tokens})
    text = data['choices'][0]['message'].get('content') or ''
    return _re.sub(r'<think>.*?</think>', '', text, flags=_re.S).strip()
"""


def _install_local_llm():
    import types
    mod = types.ModuleType('local_llm')
    mod.__file__ = '<local_llm>'
    exec(compile(_LOCAL_LLM_SRC, '<local_llm>', 'exec'), mod.__dict__)
    sys.modules['local_llm'] = mod


_install_local_llm()
_LAST_FIGS = []

_ERR_RU = {
    'NameError': 'Python не знает такого имени. Проверьте опечатку и что переменная создана выше по коду.',
    'SyntaxError': 'Python не смог разобрать запись: незакрытая скобка или кавычка, пропущено двоеточие, лишний символ.',
    'IndentationError': 'Неверный отступ. Строки внутри блока (после двоеточия) сдвигаются на 4 пробела, остальные — нет.',
    'TabError': 'Перемешаны пробелы и табуляция в отступах. Используйте только пробелы.',
    'TypeError': 'Операция не подходит к этому типу данных: например, сложить строку и число. Проверьте типы: type(x) (для таблицы — df.dtypes).',
    'ZeroDivisionError': 'Деление на ноль.',
    'ValueError': 'Тип подходящий, а значение — нет. Например, int("десять") не превратить в число.',
    'IndexError': 'Индекс за пределами списка или строки. Помните: нумерация начинается с 0.',
    'KeyError': 'Такого ключа нет в словаре.',
    'AttributeError': 'У этого объекта нет такого метода или свойства. Проверьте написание и тип данных.',
    'UnboundLocalError': 'Переменная используется внутри функции раньше, чем ей присвоено значение.',
    'ModuleNotFoundError': 'Такой библиотеки нет в этой среде.',
    'RecursionError': 'Функция вызывает сама себя бесконечно.',
    'OverflowError': 'Число слишком большое.',
}


def _no_input(*args, **kwargs):
    raise RuntimeError('input() в курсе не используется: значения задаются прямо в коде.')


_SPECIFIC = [
    (r"feature names should match|Feature names unseen at fit time|Feature names seen at fit time, yet now missing|Feature names must be in the same order",
     'Столбцы новых данных не совпадают со столбцами, на которых модель обучали: какого-то нет, есть лишний или другой порядок. '
     'Выровняйте их: X_new = X_new.reindex(columns=X_train.columns, fill_value=0) — или соберите предобработку и модель в один Pipeline, '
     'чтобы новые данные проходили те же шаги, что и обучающие.'),
    (r"X has \d+ features?, but \w+ is expecting \d+ features?",
     'Модели подали другое число столбцов, чем при обучении. Обычно новые данные не прошли ту же предобработку '
     '(get_dummies дал другой набор столбцов, забыли масштабирование). Выровняйте столбцы через reindex(columns=X_train.columns, fill_value=0) или используйте Pipeline.'),
    (r"unterminated (triple-quoted )?string literal|EOL while scanning string literal",
     'Не закрыта кавычка: строка должна начинаться и заканчиваться кавычкой одного вида — "…" или \'…\'.'),
    (r"Maybe you meant '==' or ':=' instead of '='",
     'В условии сравнение пишется двумя знаками: ==. Одинарный = — это присваивание. Про := пока забудьте.'),
    (r"(too many|not enough) values to unpack",
     'Слева от = (или после for) имён больше или меньше, чем значений справа. Число имён и значений должно совпадать.'),
    (r"'dict' object has no attribute 'add'",
     '{} создаёт пустой словарь, а не множество. Пустое множество — set().'),
    (r"'NoneType'",
     'Одно из значений — None («ничего»). Чаще всего это результат функции без return или метода вроде .sort() / .append(), '
     'который меняет объект на месте и ничего не возвращает.'),
    (r"'(int|float)' and 'tuple'|'tuple' and '(int|float)'",
     'В выражении оказался кортеж. Частая причина — запятая вместо точки в дробном числе: 6,5 — это пара (6, 5), дробь пишется 6.5.'),
    (r"'(int|float)' and 'str'|'str' and '(int|float)'|can only concatenate str",
     'Смешаны число и текст. Если число лежит строкой (например, из CSV) — превратите его через int() или float(); '
     'если собираете текст — str(x) или f-строка.'),
    (r"could not convert string to float|invalid literal for int\(\)",
     'Внутри строки лишние символы — пробел, запятая, буква, прочерк. Посмотрите на строку в кавычках в тексте ошибки и почистите её (.replace, .strip).'),
    (r"expected at least 1 argument|missing 1 required positional argument",
     'Функцию вызвали без нужного аргумента. Если передаёте функцию в key=, пишите имя без скобок: key=len, key=counts.get.'),
    (r"The truth value of a Series is ambiguous|truth value of an array",
     'Python ждал одно значение «да/нет», а получил целый столбец (Series). Частые причины: and/or вместо & и | в маске; '
     'if по столбцу; в переменной лежит Series, а нужно одно число или строка — возьмите .iloc[0] или .item().'),
    (r"unsupported operand type\(s\) for &|unsupported operand type\(s\) for \||Cannot perform 'r?(and|or)_'",
     'Похоже, в маске забыты скобки: & и | выполняются раньше сравнений. Пишите (a > 1) & (b < 2).'),
    (r"Invalid value .* for dtype '?u?int\d*'?",
     'В столбец целых чисел записываете дробные. Округлите (.round().astype(int)) или сделайте столбец дробным заранее (* 1.0).'),
    (r"Can only use \.dt accessor",
     '.dt работает только со столбцом дат. Сначала pd.to_datetime(...), проверьте dtype.'),
    (r"Can only use \.str accessor",
     '.str работает только с текстовым столбцом. Проверьте dtype и пропуски.'),
    (r"You are trying to merge on .* columns",
     'Ключи соединения разного типа (например, текст и число). Приведите их к одному типу перед merge.'),
]


def _specific_tip(msg):
    import re as _re
    for rx, tip in _SPECIFIC:
        if _re.search(rx, msg or ''):
            return tip
    return None


def _short(msg, limit=300):
    msg = str(msg)
    return msg if len(msg) <= limit else msg[:limit].rstrip() + ' …'


def _fmt_error(e, code, ns=None):
    """Короткое понятное сообщение: тип, текст, строка, пояснение."""
    name = type(e).__name__
    msg = str(e)
    if isinstance(e, NameError) and getattr(e, 'name', None):
        import difflib
        known = [k for k in list((ns or {}).keys()) + dir(builtins) if not k.startswith('_')]
        near = difflib.get_close_matches(e.name, known, n=1, cutoff=0.75)
        if not near:
            near = [k for k in known if k.lower() == e.name.lower()]
        if near:
            msg += f'. Возможно, имелось в виду: {near[0]}'
    line_no = None
    if isinstance(e, SyntaxError) and e.filename == _USER:
        line_no = e.lineno
        msg = e.msg
    else:
        for fr in traceback.extract_tb(e.__traceback__):
            if fr.filename == _USER:
                line_no = fr.lineno
    lines = code.splitlines()
    specific = _specific_tip(msg)
    msg = _short(msg)
    parts = [f'{name}: {msg}' if msg else name]
    if line_no and 0 < line_no <= len(lines):
        parts.append(f'Строка {line_no}:  {lines[line_no - 1].strip()}')
    tip = specific or _ERR_RU.get(name)
    if tip:
        parts.append('Что это значит: ' + tip)
    return {'type': name, 'text': '\n'.join(parts), 'line': line_no}


class _Fail(AssertionError):
    pass


def _helpers(out, code, ns):
    lines = [l.strip() for l in out.splitlines() if l.strip()]

    def need(name, kind=None):
        """Переменная из кода ученика (понятная ошибка, если её нет)."""
        if name not in ns:
            raise _Fail(f'Не нашёл переменную {name}. Создайте её — имя должно совпадать точно.')
        v = ns[name]
        if kind is not None and not isinstance(v, kind):
            kinds = kind if isinstance(kind, tuple) else (kind,)
            want = ' или '.join(k.__name__ for k in kinds)
            raise _Fail(f'В {name} лежит {type(v).__name__} ({v!r}), а нужен {want}.')
        return v

    def printed(text):
        """Текст встречается в выводе."""
        return str(text) in out

    def printed_line(text):
        """Есть строка вывода, равная text (без пробелов по краям)."""
        return str(text).strip() in lines

    def calls(fn):
        """Сколько раз в коде вызывается функция/метод с этим именем."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0
        n = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if (isinstance(f, ast.Name) and f.id == fn) or (isinstance(f, ast.Attribute) and f.attr == fn):
                    n += 1
        return n

    def uses_fstring():
        try:
            return any(isinstance(n, ast.JoinedStr) for n in ast.walk(ast.parse(code)))
        except SyntaxError:
            return False

    def has_literal(value):
        """В коде прямо записано это значение (чтобы ловить «ответ вписан руками»)."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False
        return any(isinstance(n, ast.Constant) and n.value == value and type(n.value) is type(value)
                   for n in ast.walk(tree))

    def close(a, b, tol=1e-6):
        try:
            return abs(float(a) - float(b)) <= tol
        except (TypeError, ValueError):
            return False

    return {
        '_out': out, '_lines': lines, '_code': code,
        'need': need, 'printed': printed, 'printed_line': printed_line,
        'calls': calls, 'uses_fstring': uses_fstring, 'has_literal': has_literal, 'close': close,
        'figs': list(_LAST_FIGS), 'ax_of': _ax_of,
    }


def _ax_of(i=0):
    """Оси (Axes) i-го графика, нарисованного кодом ученика; понятная ошибка, если графика нет."""
    if len(_LAST_FIGS) <= i or not _LAST_FIGS[i].axes:
        raise AssertionError('График не появился. Нарисуйте его: plt.subplots() / df.plot(...) — и не закрывайте.')
    return _LAST_FIGS[i].axes[0]


def _figures():
    global _LAST_FIGS
    _LAST_FIGS = []
    plt = sys.modules.get('matplotlib.pyplot')
    if not plt:
        return []
    import base64
    figs = []
    for n in plt.get_fignums():
        fig = plt.figure(n)
        _LAST_FIGS.append(fig)
        b = io.BytesIO()
        fig.savefig(b, format='png', bbox_inches='tight', dpi=100)
        figs.append(base64.b64encode(b.getvalue()).decode())
    plt.close('all')
    return figs


_PD_READY = False


def _pandas_options():
    global _PD_READY
    if _PD_READY:
        return
    try:
        import pandas as pd
        pd.set_option('display.width', 120)
        pd.set_option('display.max_columns', 20)
        pd.set_option('display.max_rows', 30)
        _PD_READY = True
    except Exception:  # noqa: BLE001
        pass


def _split_last_expr(code):
    """Код без последнего выражения + само выражение (номера строк сохраняются)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, None
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return code, None
    last = tree.body.pop()
    if isinstance(last.value, ast.Call) and isinstance(last.value.func, ast.Name) and last.value.func.id == 'print':
        tree.body.append(last)
        return code, None
    return tree, ast.Expression(last.value)


def _display(value):
    if value is None:
        return None
    mod = type(value).__module__ or ''
    first = value[0] if isinstance(value, (list, tuple)) and value else None
    if mod.startswith('matplotlib') or (type(first).__module__ or '').startswith('matplotlib'):
        return None          # результат plt.*/ax.* — сам график покажется картинкой
    if mod.startswith('pandas'):
        try:
            import pandas as pd
            if isinstance(value, pd.Series):
                value = value.to_frame()
            if isinstance(value, pd.DataFrame):
                n = len(value)
                html = value.to_html(max_rows=20, max_cols=15, border=0, classes='df', na_rep='NaN')
                return {'html': html, 'note': f'{n} строк × {value.shape[1]} столбцов' if n > 20 else ''}
        except Exception:  # noqa: BLE001
            pass
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001
        text = '<?>'
    return {'text': text if len(text) < 5000 else text[:5000] + '…'}


def run(code, check=None, setup=None, show_last=False):
    """Выполнить код ученика (и проверку). Возвращает dict для интерфейса."""
    buf = io.StringIO()
    ns = {'__name__': '__main__', '__builtins__': builtins}
    res = {'ok': True, 'out': '', 'error': None, 'check': None, 'figs': [], 'display': None}
    old_out, old_err, old_input = sys.stdout, sys.stderr, builtins.input
    sys.stdout = sys.stderr = buf
    builtins.input = _no_input
    try:
        if 'pandas' in code or 'pandas' in (setup or ''):
            _pandas_options()
        if setup:
            exec(compile(setup, '<подготовка>', 'exec'), ns)
        # как в Jupyter: значение последнего выражения показываем (таблицы pandas — таблицей)
        body, last = _split_last_expr(code) if show_last else (code, None)
        if last is None:
            exec(compile(code, _USER, 'exec'), ns)
        else:
            exec(compile(body, _USER, 'exec'), ns)
            value = eval(compile(last, _USER, 'eval'), ns)
            res['display'] = _display(value)
    except BaseException as e:  # noqa: BLE001 — показываем ученику любую ошибку
        res['ok'] = False
        res['error'] = _fmt_error(e, code, ns)
    finally:
        sys.stdout, sys.stderr, builtins.input = old_out, old_err, old_input
    res['out'] = buf.getvalue()
    try:
        res['figs'] = _figures()
    except Exception:  # noqa: BLE001
        pass

    if check is not None:
        if not res['ok']:
            res['check'] = {'passed': False, 'msg': 'Код завершился с ошибкой — сначала исправьте её (сообщение выше).'}
        else:
            cns = dict(ns)
            cns.update(_helpers(res['out'], code, ns))
            sink, sys.stdout = sys.stdout, io.StringIO()   # print внутри функций ученика при проверке не нужен
            try:
                exec(compile(check, '<проверка>', 'exec'), cns)
                res['check'] = {'passed': True, 'msg': ''}
            except AssertionError as e:
                res['check'] = {'passed': False, 'msg': str(e) or 'Результат пока не совпадает с ожидаемым.'}
            except Exception as e:  # noqa: BLE001
                res['check'] = {'passed': False,
                                'msg': f'Проверка споткнулась: {type(e).__name__}: {_short(e, 200)}. '
                                       + (_specific_tip(str(e)) or 'Скорее всего, в переменной лежит не то, что ожидалось (проверьте тип: число, строка, список или таблица).')}
            finally:
                sys.stdout = sink
    return res


# ---------- пошаговое выполнение ----------

class _TooManySteps(Exception):
    pass


def _show(v):
    """Короткое представление значения для таблицы переменных."""
    import types
    if isinstance(v, types.FunctionType):
        return f'функция {v.__name__}()'
    if isinstance(v, types.ModuleType):
        return f'модуль {v.__name__}'
    try:
        r = repr(v)
    except Exception:  # noqa: BLE001
        r = '<?>'
    return r if len(r) <= 120 else r[:117] + '…'


def _vars(frame):
    out = []
    for k, v in frame.f_locals.items():
        if k.startswith('__') or k in ('builtins',):
            continue
        out.append([k, type(v).__name__, _show(v)])
    return out


def trace(code, max_steps=500):
    """Выполнить код по шагам. Шаг — строка, которая СЕЙЧАС будет выполнена, и переменные до неё.
    Возвращает {'steps': [...], 'error': ..., 'truncated': bool}."""
    buf = io.StringIO()
    ns = {'__name__': '__main__', '__builtins__': builtins}
    steps = []

    def snapshot(frame, line, event):
        scopes = []
        f = frame
        while f is not None and f.f_code.co_filename == _USER:
            name = f.f_code.co_name
            scopes.append({'name': 'программа' if name == '<module>' else f'{name}()', 'vars': _vars(f)})
            f = f.f_back
        scopes.reverse()
        steps.append({'line': line, 'event': event, 'scopes': scopes, 'out': buf.getvalue()})
        if len(steps) >= max_steps:
            raise _TooManySteps()

    def local(frame, event, arg):
        if event == 'line':
            snapshot(frame, frame.f_lineno, 'line')
        elif event == 'return' and frame.f_code.co_name != '<module>':
            snapshot(frame, frame.f_lineno, 'return')
            steps[-1]['ret'] = _show(arg)
        return local

    def glob(frame, event, arg):
        if frame.f_code.co_filename != _USER:
            return None
        return local

    res = {'steps': steps, 'error': None, 'truncated': False}
    old_out, old_err, old_input = sys.stdout, sys.stderr, builtins.input
    sys.stdout = sys.stderr = buf
    builtins.input = _no_input
    try:
        compiled = compile(code, _USER, 'exec')
        sys.settrace(glob)
        try:
            exec(compiled, ns)
        finally:
            sys.settrace(None)
    except _TooManySteps:
        res['truncated'] = True
    except BaseException as e:  # noqa: BLE001
        res['error'] = _fmt_error(e, code, ns)
    finally:
        sys.stdout, sys.stderr, builtins.input = old_out, old_err, old_input
    # финальное состояние
    if not res['truncated']:
        final = [[k, type(v).__name__, _show(v)] for k, v in ns.items() if not k.startswith('__')]
        steps.append({'line': None, 'event': 'end', 'scopes': [{'name': 'программа', 'vars': final}], 'out': buf.getvalue()})
    return res
