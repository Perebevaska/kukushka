#!/usr/bin/env python3
"""Сборка сайта курса: content/*.md → site/*.html.

    uv run tools/build.py            # собрать всё
    uv run tools/build.py --check    # только разобрать уроки и показать ошибки формата

Формат урока — content/<глава>/<урок>.md, см. content/README.md.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / 'content'
SITE = ROOT / 'site'

LEVELS = {
    'warmup': 'Разминка',
    'base': 'База',
    'plus': 'Посложнее',
    'star': 'Со звёздочкой',
}
CALLOUTS = {
    'sql': 'Как в SQL',
    'note': 'Заметка',
    'warn': 'Частая ошибка',
    'tip': 'Совет',
    'deep': 'Для любопытных',
}


# ---------- Markdown ----------

def _callout_render(name):
    def render(self, tokens, idx, _options, env):
        tok = tokens[idx]
        if tok.nesting == 1:
            title = tok.info.strip()[len(name):].strip() or CALLOUTS[name]
            return (f'<aside class="callout callout-{name}"><div class="callout-title">'
                    f'{html.escape(title)}</div>\n')
        return '</aside>\n'
    return render


def make_md() -> MarkdownIt:
    md = MarkdownIt('commonmark', {'html': True, 'typographer': False}).enable('table')
    md.use(front_matter_plugin)
    md.use(dollarmath_plugin, allow_space=True, double_inline=True)   # формулы: $…$ и $$…$$ → KaTeX в браузере
    for name in CALLOUTS:
        md.use(container_plugin, name=name, render=_callout_render(name))

    def predict_render(self, tokens, idx, _options, env):
        if tokens[idx].nesting == 1:
            env['predict'] = env.get('predict', 0) + 1
            return (f'<div class="predict" data-q="q{env["predict"]}"><div class="predict-title">Предскажите вывод</div>'
                    '<p class="predict-ask">Что выведет этот код? Сначала ответьте, потом запустите.</p>\n')
        return '</div>\n'
    md.use(container_plugin, name='predict', render=predict_render)

    def quiz_render(self, tokens, idx, _options, env):
        if tokens[idx].nesting == 1:
            env['quiz'] = env.get('quiz', 0) + 1
            ref = tokens[idx].info.strip()[len('quiz'):].strip()
            attr = f' data-lesson="{html.escape(ref)}"' if ref else ''
            title = f'Вопрос {env["quiz"]}' if env.get('test') else 'Проверьте себя'
            return (f'<div class="quiz-c" data-q="c{env["quiz"]}"{attr}><div class="predict-title">{title}</div>\n')
        return '</div>\n'
    md.use(container_plugin, name='quiz', render=quiz_render)

    def figure_render(self, tokens, idx, _options, env):
        tok = tokens[idx]
        if tok.nesting == 1:
            name = tok.info.strip()[len('figure'):].strip()
            path = CONTENT / 'figures' / f'{name}.svg'
            if not path.exists():
                raise FormatError(f'нет схемы content/figures/{name}.svg')
            svg = path.read_text(encoding='utf-8')
            svg = re.sub(r'<\?xml[^>]*>\s*', '', svg)
            return f'<figure class="fig" data-fig="{html.escape(name)}"><div class="fig-scroll">{svg}</div><figcaption>\n'
        return '</figcaption></figure>\n'
    md.use(container_plugin, name='figure', render=figure_render)

    def widget_render(self, tokens, idx, _options, env):
        tok = tokens[idx]
        if tok.nesting == 1:
            name = tok.info.strip()[len('widget'):].strip()
            path = CONTENT / 'widgets' / f'{name}.json'
            data = path.read_text(encoding='utf-8') if path.exists() else '{}'
            if name not in WIDGETS:
                raise FormatError(f'неизвестный виджет «{name}» (есть: {", ".join(WIDGETS)})')
            return (f'<figure class="fig widget" id="widget-{html.escape(name)}" data-widget="{html.escape(name)}">'
                    f'<script type="application/json" class="widget-data">{data}</script>'
                    f'<div class="widget-body"></div><figcaption>\n')
        return '</figcaption></figure>\n'
    md.use(container_plugin, name='widget', render=widget_render)

    def fence(self, tokens, idx, options, env):
        tok = tokens[idx]
        info = tok.info.strip().split()
        lang = info[0] if info else ''
        flags = set(info[1:])
        code = tok.content.rstrip('\n')
        esc = html.escape(code)
        if lang == 'python' and 'static' not in flags:
            env.setdefault('cells', 0)
            env['cells'] += 1
            attrs = ' data-expect-error="1"' if 'error' in flags else ''
            if 'llm' in flags:
                attrs += ' data-llm="1"'
            files = [f[6:] for f in flags if f.startswith('files=')]
            if files:
                attrs += f' data-files="{html.escape(files[0])}"'
            return (f'<div class="cell"{attrs}><pre class="cell-src"><code>{esc}</code></pre></div>\n')
        cls = f' class="lang-{lang}"' if lang else ''
        kind = 'output' if lang in ('text', 'output') else 'code'
        return f'<pre class="static {kind}"><code{cls}>{esc}</code></pre>\n'

    md.add_render_rule('fence', fence)
    return md


MD = make_md()


def render(text: str, env: dict | None = None) -> str:
    return MD.render(text, env if env is not None else {})


def inline(text: str) -> str:
    return MD.renderInline(text)


# ---------- Разбор урока ----------

TASK_RE = re.compile(r'^## task:\s*(.+?)\s*$', re.M)
SUB_RE = re.compile(r'^### (starter|setup|check|hint|solution|explain|parsons)\s*$', re.M)
PREDICT_RE = re.compile(r'^::: predict\s*\n(.*?)^:::\s*$', re.S | re.M)
QUIZ_RE = re.compile(r'^::: quiz[^\n]*\n(.*?)^:::\s*$', re.S | re.M)
PRACTICE_RE = re.compile(r'^\{\{practice:\s*(.*?)\}\}\s*$', re.M)
CODE_RE = re.compile(r'^```[a-z]*\s*\n(.*?)^```\s*$', re.S | re.M)


class FormatError(Exception):
    pass


def _code_of(block: str, where: str) -> str:
    m = CODE_RE.search(block)
    if not m:
        raise FormatError(f'{where}: ожидался блок кода ```python … ```')
    return m.group(1).rstrip('\n')


def parse_task(head: str, body: str, where: str) -> dict:
    parts = [p.strip() for p in head.split('|')]
    if len(parts) not in (3, 4):
        raise FormatError(f'{where}: заголовок задачи — «## task: id | Название | уровень»')
    tid, title, level = parts[:3]
    topic = parts[3] if len(parts) == 4 else ''
    if level not in LEVELS:
        raise FormatError(f'{where}: уровень «{level}» — допустимы {", ".join(LEVELS)}')
    pieces = SUB_RE.split(body)
    task = {'id': tid, 'title': title, 'level': level, 'text': pieces[0].strip(),
            'starter': '', 'setup': '', 'check': '', 'hints': [], 'solution': '', 'explain': '', 'parsons': '',
            'topic': topic, 'hints_md': [], 'explain_md': ''}
    for name, block in zip(pieces[1::2], pieces[2::2]):
        w = f'{where} / {tid} / {name}'
        if name == 'hint':
            task['hints'].append(render(block.strip()))
            task['hints_md'].append(block.strip())      # исходник — для блокнотов (tools/make_notebooks.py)
        elif name == 'explain':
            task['explain'] = render(block.strip())
            task['explain_md'] = block.strip()
        else:
            task[name] = _code_of(block, w) if block.strip() else ''
    if task['parsons']:
        task['solution'] = task['solution'] or task['parsons']
    for req in ('check', 'solution'):
        if not task[req]:
            raise FormatError(f'{where} / {tid}: нет раздела ### {req}')
    return task


def parse_lesson(path: Path) -> dict:
    src = path.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n', src, re.S)
    if not m:
        raise FormatError(f'{path}: нет шапки --- … ---')
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise FormatError(f'{path.name}: ошибка в шапке (значения с «: » берите в кавычки): {e}')
    rest = src[m.end():]
    chunks = TASK_RE.split(rest)
    theory, tasks = chunks[0], []
    seen = set()
    for head, body in zip(chunks[1::2], chunks[2::2]):
        t = parse_task(head, body, path.name)
        if t['id'] in seen:
            raise FormatError(f'{path.name}: повторяется id задачи {t["id"]}')
        seen.add(t['id'])
        tasks.append(t)
    # «Практика» — заголовок перед задачами, пишется в конце теории; убираем, рисуем сами
    theory = re.sub(r'\n## Практика\s*\n?(.*)\Z', lambda mm: '\n' + mm.group(1), theory, flags=re.S)
    ids = {t['id'] for t in tasks}
    def practice(mm):
        tids = [x.strip() for x in mm.group(1).split(',') if x.strip()]
        bad = [x for x in tids if x not in ids]
        if bad:
            raise FormatError(f'{path.name}: в {{{{practice}}}} нет таких задач: {", ".join(bad)}')
        return f'\n<div class="practice-link" data-tasks="{",".join(tids)}"></div>\n'
    theory = PRACTICE_RE.sub(practice, theory)
    for q in QUIZ_RE.findall(theory):
        opts = re.findall(r'^- \[( |x)\] ', q, re.M)
        quotes = re.findall(r'^  > ', q, re.M)
        if opts.count('x') != 1 or len(opts) < 2 or len(quotes) < len(opts):
            raise FormatError(f'{path.name}: в ::: quiz нужен ровно один «- [x]», минимум два варианта и объяснение «  > …» у каждого')
    env: dict = {}
    return {'meta': meta, 'theory_md': theory, 'theory': render(theory, env), 'tasks': tasks,
            'cells': env.get('cells', 0)}


# ---------- Шаблоны ----------

def _build_version() -> str:
    """Версия для ?v= у ассетов: меняется, только когда меняются ассеты или содержание курса.
    Без неё Safari показывает страницы со старыми стилями и скриптами из кэша."""
    import hashlib
    h = hashlib.sha1()
    files = sorted(p for p in (SITE / 'assets').glob('*') if p.suffix in ('.css', '.js', '.py', '.svg')
                   and p.name not in ('course.js', 'search.js'))
    files += sorted(CONTENT.rglob('*.md')) + sorted(CONTENT.rglob('*.yaml')) + [Path(__file__)]
    for f in files:
        h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:10]


V = _build_version()


DATA_DIR = SITE / 'data'


def _data_info(name: str) -> str:
    p = DATA_DIR / name
    if not p.exists():
        return ''
    kb = max(1, round(p.stat().st_size / 1024))
    if p.suffix == '.csv':
        # считаем строки по байтам: учебные файлы бывают и не в UTF-8 (урок про кодировки)
        rows = sum(1 for _ in p.open('rb')) - 1
        return f'{rows} строк · {kb} КБ'
    return f'{kb} КБ'


def data_files_block(root: str, files: list) -> str:
    """Плашка «Данные урока» со ссылками на скачивание файлов из site/data."""
    items = [f for f in files if (DATA_DIR / f).exists()]
    if not items:
        return ''
    links = ''.join(f'<a class="data-file" href="{root}data/{html.escape(f)}" download title="Скачать {html.escape(f)}">'
                    f'<span class="df-name">{html.escape(f)}</span><span class="df-info">{_data_info(f)}</span></a>'
                    for f in items)
    return (f'<div class="data-files"><span class="df-label">Данные урока</span>{links}'
            '<span class="df-note">В примерах файлы уже подключены — скачивать нужно, только чтобы открыть их у себя.</span></div>')


_DATA_CODE_RE = re.compile(r'(?<!<pre>)<code>([\w.-]+\.(?:csv|txt))</code>')


def link_data(root: str, html_text: str) -> str:
    """Имена файлов данных в тексте (`orders.csv`) становятся ссылками на скачивание."""
    def sub(m):
        name = m.group(1)
        if not (DATA_DIR / name).exists():
            return m.group(0)
        return f'<a class="data-link" href="{root}data/{name}" download title="Скачать {name}"><code>{name}</code></a>'
    return _DATA_CODE_RE.sub(sub, html_text)


def A(root: str, rel: str) -> str:
    """URL ассета с версией."""
    return f'{root}assets/{rel}?v={V}'


WIDGETS = ('gd-lr', 'threshold', 'tree-depth', 'lm-studio')
KATEX_HEAD = '<link rel="stylesheet" href="{css}">\n'
KATEX_JS = ('<script src="{js}"></script>\n<script>document.querySelectorAll(".math").forEach(function(e){{'
            'try{{katex.render(e.textContent.trim(),e,{{displayMode:e.classList.contains("block"),throwOnError:false}})}}catch(x){{}}}});</script>')

def page(title: str, body: str, root: str, body_attrs: str = '', extra_head: str = '',
         scripts: str = '') -> str:
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="icon" href="{A(root, 'favicon.svg')}">
{extra_head}{KATEX_HEAD.format(css=A(root, 'vendor/katex/katex.min.css')) if 'class="math ' in body else ''}<link rel="stylesheet" href="{A(root, 'app.css')}">
<script>try{{var t=localStorage.getItem('dsc.theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head>
<body {body_attrs} data-v="{V}">
{body}
{scripts}
{KATEX_JS.format(js=A(root, 'vendor/katex/katex.min.js')) if 'class="math ' in body else ''}
{f'<script src="{A(root, "widgets.js")}"></script>' if 'data-widget=' in body else ''}
</body>
</html>
'''


def topbar(root: str, crumbs: str, with_menu: bool, with_py: bool = True) -> str:
    menu = ('<button class="icon-btn only-narrow" id="menu-btn" aria-label="Содержание главы" '
            'aria-expanded="false">' + ICON_MENU + '</button>') if with_menu else ''
    py = ('<span class="py-pill" id="py-pill" data-state="idle" title="Состояние Python в браузере"><i></i><span>Python</span></span>'
          if with_py else '')
    return f'''<header class="topbar">
  {menu}
  <a class="brand" href="{root}index.html">{ICON_LOGO}<span>DS для аналитиков</span></a>
  <span class="crumbs">{crumbs}</span>
  <span class="spacer"></span>
  <button class="search-btn" id="search-btn" aria-label="Поиск по курсу">{ICON_SEARCH}<span>Поиск</span><kbd class="mod">Ctrl</kbd><kbd>K</kbd></button>
  <nav class="topnav" aria-label="Разделы">
    <a href="{root}cheatsheet.html" title="Шпаргалка SQL ↔ Python">{ICON_SHEET}<span>Шпаргалка</span></a>
    <a href="{root}notes.html" title="Мои заметки">{ICON_NOTE}<span>Заметки</span></a>
    <a href="{root}stats.html" title="Статистика и повторение">{ICON_STATS}<span>Статистика</span></a>
  </nav>
  {py}
  <span class="save-pill" id="save-pill" data-state="browser" title=""><i></i><span>В браузере</span></span>
  <button class="icon-btn" id="theme-btn" aria-label="Сменить тему">{ICON_THEME}</button>
</header>'''


ICON_LOGO = ('<svg class="logo" width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="12" width="4" height="9" rx="1"/>'
             '<rect x="10" y="7" width="4" height="14" rx="1"/><rect x="17" y="3" width="4" height="18" rx="1"/></svg>')
ICON_MENU = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>')
ICON_SEARCH = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>'
ICON_SHEET = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/>'
              '<path d="M4 10h16M10 10v10"/></svg>')
ICON_NOTE = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/><path d="M9 11h7M9 15h7M9 7h4"/></svg>')
ICON_STATS = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h16"/><path d="M7 16v-4M12 16V7M17 16v-7"/></svg>')
ICON_THEME = ('<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/>'
              '<path d="M12 4a8 8 0 0 0 0 16z" class="fill"/></svg>')


def lesson_url(ch: dict, ls: dict) -> str:
    return f'{ch["id"]}/{ls["id"]}.html'


CELL_RE = re.compile(r'^```python([^\n]*)\n(.*?)^```\s*$', re.S | re.M)


CH_DISPLAY: dict = {}


def export(built: dict, path: Path) -> None:
    """Задачи и примеры всех уроков — для tools/verify.mjs."""
    items = []
    for (ch, ls), L in built.items():
        files = L['meta'].get('files', [])
        disp = bool(L['meta'].get('display', CH_DISPLAY.get(ch, False)))
        for i, m in enumerate(CELL_RE.finditer(L['theory_md']), 1):
            flags = m.group(1).split()
            if 'static' in flags or 'llm' in flags:   # llm — нужен LM Studio на компьютере, в проверке не запускаем
                continue
            items.append({'lesson': f'{ch}/{ls}', 'kind': 'cell', 'id': f'cell{i}', 'code': m.group(2).rstrip('\n'),
                          'expect_error': 'error' in flags, 'files': files, 'display': disp})
        for i, m in enumerate(PREDICT_RE.finditer(L['theory_md']), 1):
            body = m.group(1)
            code = re.search(r'```python[^\n]*\n(.*?)^```', body, re.S | re.M)
            right = re.findall(r'^- \[x\] (.+)$', body, re.M)
            if not code or len(right) != 1:
                raise FormatError(f'{ch}/{ls}: вопрос «предскажите вывод» №{i} — нужен блок кода и ровно один вариант «- [x]»')
            items.append({'lesson': f'{ch}/{ls}', 'kind': 'predict', 'id': f'q{i}', 'code': code.group(1).rstrip('\n'),
                          'answer': right[0].strip(), 'files': files, 'display': disp})
        for t in L['tasks']:
            items.append({'lesson': f'{ch}/{ls}', 'kind': 'task', 'id': t['id'], 'starter': t['starter'],
                          'setup': t['setup'], 'check': t['check'], 'solution': t['solution'], 'files': files, 'display': disp})
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Экспорт для проверки: {len(items)} записей → {path}')


# ---------- рамка главы: введение и итоговый тест ----------

def check_quizzes(text: str, where: str) -> int:
    qs = QUIZ_RE.findall(text)
    for q in qs:
        opts = re.findall(r'^- \[( |x)\] ', q, re.M)
        quotes = re.findall(r'^  > ', q, re.M)
        if opts.count('x') != 1 or len(opts) < 2 or len(quotes) < len(opts):
            raise FormatError(f'{where}: в ::: quiz нужен ровно один «- [x]», минимум два варианта и объяснение «  > …» у каждого')
    return len(qs)


def parse_chapter_extra(ch: dict) -> dict:
    """content/chNN/intro.md и test.md — необязательные; если есть, у главы появляются страницы «О главе» и «Итоговый тест»."""
    out = {}
    for name in ('intro', 'test'):
        path = CONTENT / ch['id'] / f'{name}.md'
        if not path.exists():
            continue
        src = path.read_text(encoding='utf-8')
        m = re.match(r'^---\n(.*?)\n---\n', src, re.S)
        meta = (yaml.safe_load(m.group(1)) or {}) if m else {}
        body = src[m.end():] if m else src
        env: dict = {'test': name == 'test'}
        n = check_quizzes(body, path.name)
        if name == 'test':
            lessons = {ls['id'] for ls in ch.get('lessons', [])}
            for ref in re.findall(r'^::: quiz\s+(\S+)', body, re.M):
                if ref not in lessons:
                    raise FormatError(f'{ch["id"]}/test.md: ссылка на урок {ref}, которого нет в главе')
        out[name] = {'meta': meta, 'html': render(body, env), 'n': n}
    return out


def chapter_minutes(ch: dict) -> int:
    return sum(ls.get('minutes') or 0 for ls in ch.get('lessons', [])) + sum(ex.get('minutes') or 0 for ex in ch.get('exams', []))


def _lessons_word(n: int) -> str:
    """«1 урок», «3 урока», «62 урока», «95 уроков»."""
    w = 'урок' if n % 10 == 1 and n % 100 != 11 else ('урока' if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else 'уроков')
    return f'{n} {w}'


def fmt_minutes(m: int) -> str:
    h, mm = divmod(m, 60)
    return (f'{h} ч ' if h else '') + (f'{mm} мин' if mm else '').strip() if m else '?'


# ---------- практика в Jupyter (блокноты из tools/make_notebooks.py) ----------

NB_DIR = SITE / 'notebooks'
NB_CMD = 'uv run --with-requirements site/notebooks/requirements.txt jupyter lab site/notebooks'


def _nb_tasks(cid: str) -> int:
    path = NB_DIR / f'{cid}-practice.ipynb'
    try:
        nb = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return 0
    return sum(1 for c in nb['cells'] if c['cell_type'] == 'code' and ''.join(c['source']).startswith('%%task '))


def _nb_tools(root: str) -> str:
    if not (NB_DIR / 'project-template.ipynb').exists():
        return ''
    return (f'<p>Для проектов — <a href="{root}notebooks/project-template.ipynb" download>шаблон проектного блокнота</a> '
            '(цель → данные → предобработка → анализ и модели → выводы, с чек-листом) и '
            f'<a href="{root}notebooks/check_notebook.py" download>check_notebook.py</a> — самопроверка перед ревью: '
            'выполняет блокнот с чистого ядра и ищет ошибки, абсолютные пути, закомментированный код и разделы без выводов. '
            'Запуск: <code>python check_notebook.py проект.ipynb</code>.</p>')


def jupyter_chapter_block(root: str, cid: str) -> str:
    """Блок «Практика в Jupyter» на странице «О главе»: коротко, шаги — под спойлером."""
    n = _nb_tasks(cid)
    if not n:
        return ''
    name = f'{cid}-practice.ipynb'
    early = ('<p class="muted">Jupyter ставим в главе 2, в уроке «Своё рабочее место — uv и Jupyter». '
             'В первой главе удобнее решать прямо на сайте.</p>') if cid == 'ch01' else ''
    return f'''<section class="prose theory jupyter-block" id="jupyter">
    <h2>Практика в Jupyter</h2>
    <p>Это по желанию: все задачи главы решаются прямо на сайте. Блокнот <code>{name}</code> нужен, если хотите решать их в своём Jupyter. В нём {n} задач — те же, что на сайте, с той же проверкой (кроме «собери код из строк»).</p>
    {early}
    <details class="jupyter-howto">
      <summary>Как решать задачи главы в Jupyter</summary>
      <ol>
        <li>Откройте терминал в папке курса и запустите Jupyter:
          <pre class="static"><code>{NB_CMD}</code></pre></li>
        <li>В Jupyter откройте <code>{name}</code>: он уже лежит в папке <code>site/notebooks</code>.</li>
        <li>Выполните первую ячейку <code>%load_ext dsc</code> — она подключает проверку.</li>
        <li>Каждая задача — ячейка, которая начинается с <code>%%task глава/урок/id</code>. Допишите код и нажмите Shift+Enter: под выводом появится «✓ Верно» или что исправить.</li>
        <li>Подсказка — <code>dsc.hint('id')</code>, решение — <code>dsc.solution('id', sure=True)</code>.</li>
      </ol>
      <p>Если блокнот испортился, скачайте свежий и положите в <code>site/notebooks</code>: <a class="btn" href="{root}notebooks/{name}" download>Скачать {name}</a> <a class="btn" href="{root}notebooks/dsc.py" download>Скачать dsc.py</a></p>
      <p class="muted">Скачанные файлы работают только внутри папки курса: <code>dsc.py</code> берёт проверки из <code>site/notebooks/tasks</code>, данные — из <code>site/data</code>.</p>
      {_nb_tools(root)}
    </details>
  </section>'''


def jupyter_home_block(root: str, index_data: list) -> str:
    """Блок со ссылками на все блокноты — на главной."""
    links = [f'<a href="{root}notebooks/{ch["id"]}-practice.ipynb" download>Глава {ch["n"]}</a>'
             for ch in index_data if _nb_tasks(ch['id'])]
    if not links:
        return ''
    return f'''<section class="map jupyter-home" id="jupyter">
    <h2>Практика в Jupyter</h2>
    <p class="muted">Задачи каждой главы есть и в блокноте Jupyter — с той же проверкой, что на сайте. Блокноты лежат в папке курса <code>site/notebooks</code>; запуск из папки курса: <code>{NB_CMD}</code>. Подробности — на странице «О главе».</p>
    <p>Блокноты глав: {" · ".join(links)}</p>
    {_nb_tools(root)}
  </section>'''


def write_chapter_pages(course, ch, extra, index_data):
    root = '../'
    chs = [c for c in course['chapters'] if c.get('lessons')]
    k = next(i for i, c in enumerate(chs) if c['id'] == ch['id'])
    prev_ch = chs[k - 1] if k > 0 else None
    next_ch = chs[k + 1] if k + 1 < len(chs) else None
    ready = [ls for ls in ch.get('lessons', []) if ls.get('status') in ('ready', 'draft')]
    side = (f'<div class="side-head"><div class="eyebrow">Глава {ch["n"]}</div>'
            f'<div class="side-title">{html.escape(ch["title"])}</div>'
            f'<div class="meter" id="chapter-meter"><i></i></div></div>')
    crumbs = f'<a href="{root}index.html#{ch["id"]}">Глава {ch["n"]}. {html.escape(ch["title"])}</a>'

    def link(href, cls, label, text):
        return f'<a class="{cls}" href="{href}"><span class="pl">{label}</span><span class="pt">{html.escape(text)}</span></a>'

    def shell(page_id, title, eyebrow, inner, pager, lesson_json=None):
        tree = course_tree(root, index_data, ch['id'], page_id)
        body = f'''<a class="skip" href="#main">К содержанию</a>
{topbar(root, crumbs, True)}
<div class="layout">
  <nav class="sidebar" id="sidebar" aria-label="Уроки главы">{side}{tree}</nav>
  <div class="scrim" id="scrim"></div>
  <main id="main" class="lesson chapter-page">
    <div class="lesson-head"><div class="eyebrow">{eyebrow}</div><h1>{html.escape(title)}</h1></div>
    {inner}
    <nav class="pager">{pager}</nav>
  </main>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>'''
        scripts = common_scripts(root)
        if lesson_json is not None:
            data_json = json.dumps(lesson_json, ensure_ascii=False).replace('</', '<\\/')
            scripts = f'<script type="application/json" id="lesson-data">{data_json}</script>\n' + scripts + f'\n<script src="{A(root, "lesson.js")}"></script>'
        out = SITE / ch['id'] / ('index.html' if page_id == '_intro' else 'test.html')
        out.parent.mkdir(parents=True, exist_ok=True)
        intro_attr = f' data-chintro-page="{ch["id"]}"' if page_id == '_intro' else ''
        out.write_text(page(f'{title} — DS для аналитиков', body, root, f'class="page-lesson page-chapter" data-root="{root}"{intro_attr}', '', scripts), encoding='utf-8')

    first = ready[0] if ready else None
    last = ready[-1] if ready else None
    if 'intro' in extra:
        meta = extra['intro']['meta']
        # пункт с «: » без кавычек YAML читает как словарь — склеиваем обратно и предупреждаем
        learn_items = []
        for x in meta.get('learn', []):
            if isinstance(x, dict):
                print(f'! {ch["id"]}/intro.md: пункт learn с двоеточием возьмите в кавычки: {x}')
                x = '; '.join(f'{k}: {v}' for k, v in x.items())
            learn_items.append(str(x))
        learn = ''.join(f'<li>{inline(x)}</li>' for x in learn_items)
        rows = []
        for ls in ready:
            rows.append(f'<li{core_attr(ls)}><a class="row" href="{ls["id"]}.html" data-lesson="{ch["id"]}/{ls["id"]}"><span class="dot"></span>'
                        f'<span class="num">{ls["n"]}</span><span class="t">{html.escape(ls["title"])}{deep_tag(ls)}</span>'
                        f'<span class="m">{ls.get("minutes", "?")} мин</span><span class="p" data-p></span></a></li>')
            for ex in ch.get('exams', []):
                if ex.get('after') == ls['id']:
                    rows.append(f'<li><a class="row exam-row" href="{ex["id"]}.html" data-exam="{ch["id"]}/{ex["id"]}"><span class="dot"></span>'
                                f'<span class="num">✓</span><span class="t">{html.escape(ex["title"])}</span>'
                                f'<span class="m">{ex.get("minutes", "?")} мин</span><span class="p" data-p></span></a></li>')
        if 'test' in extra:
            rows.append(f'<li><a class="row exam-row" href="test.html" data-ctest="{ch["id"]}" data-n="{extra["test"]["n"]}"><span class="dot"></span>'
                        f'<span class="num">?</span><span class="t">Итоговый тест главы</span>'
                        f'<span class="m">{extra["test"]["n"]} вопросов</span><span class="p" data-p></span></a></li>')
        n_tasks = sum(len(x['tasks']) for c in index_data if c['id'] == ch['id'] for x in c['lessons'])
        inner = f'''<p class="lead">{inline(ch.get("goal", ""))}</p>
    <div class="ch-facts"><div><b>{len(ready)}</b>уроков</div><div><b>{n_tasks}</b>задач</div><div><b>≈ {fmt_minutes(chapter_minutes(ch))}</b>на главу</div></div>
    {f'<aside class="ch-question"><div class="eyebrow">Бизнес-вопрос главы</div><p>{inline(meta["question"])}</p></aside>' if meta.get("question") else ''}
    <article class="prose theory">{extra["intro"]["html"]}
    {f'<h2>Чему вы научитесь</h2><ul>{learn}</ul>' if learn else ''}
    <h2>Уроки главы</h2></article>
    <ol class="lesson-rows ch-rows">{"".join(rows)}</ol>
    {f'<p><a class="btn primary" href="{first["id"]}.html">Начать с урока 1 →</a></p>' if first else ''}
    {jupyter_chapter_block(root, ch['id'])}'''
        prev = (link(f'{root}{prev_ch["id"]}/test.html' if (CONTENT / prev_ch['id'] / 'test.md').exists() else f'{root}index.html#{prev_ch["id"]}', 'prev', '← Глава ' + str(prev_ch['n']), prev_ch['title'])
                if prev_ch else '<span class="prev empty"></span>')
        nxt = link(f'{first["id"]}.html', 'next', 'Урок 1 →', first['title']) if first else '<span class="next empty"></span>'
        shell('_intro', f'Глава {ch["n"]}. {ch["title"]}', f'О главе · ≈ {fmt_minutes(chapter_minutes(ch))}', inner, prev + nxt)
    if 'test' in extra:
        t = extra['test']
        inner = f'''<p class="lead">{t["n"]} вопросов по всей главе — на понимание, без кода. После каждого ответа — объяснение всех вариантов, в конце — итог и уроки, которые стоит повторить.</p>
    <article class="prose theory test-body">{t["html"]}</article>
    <section class="test-result" id="test-result" aria-live="polite"></section>'''
        prev = link(f'{last["id"]}.html', 'prev', '← Последний урок', last['title']) if last else '<span class="prev empty"></span>'
        if next_ch:
            nh = f'{root}{next_ch["id"]}/index.html' if (CONTENT / next_ch['id'] / 'intro.md').exists() else f'{root}index.html#{next_ch["id"]}'
            nxt = link(nh, 'next', f'Глава {next_ch["n"]} →', next_ch['title'])
        else:
            nxt = link(f'{root}index.html', 'next', 'Курс пройден →', 'К карте курса')
        lj = {'lesson': f'{ch["id"]}/test', 'title': f'Итоговый тест: {ch["title"]}', 'chapter': ch['title'], 'tasks': [],
              'files': [], 'mode': 'test', 'display': False, 'topics': {}}
        shell('_test', f'Итоговый тест: {ch["title"]}', f'Глава {ch["n"]} · {t["n"]} вопросов', inner, prev + nxt, lj)


def load_course() -> tuple[dict, dict, int]:
    """Разобрать course.yaml и все уроки: (course, {(глава, урок): урок}, число ошибок).
    Нужна и сборке сайта, и генератору блокнотов tools/make_notebooks.py."""
    course = yaml.safe_load((CONTENT / 'course.yaml').read_text(encoding='utf-8'))
    errors = 0
    built = {}
    for ci, ch in enumerate(course['chapters'], 1):
        ch['n'] = ci
        CH_DISPLAY[ch['id']] = bool(ch.get('display', False))
        for li, ls in enumerate(ch.get('lessons', []), 1):
            ls['n'] = li
            path = CONTENT / ch['id'] / f'{ls["id"]}.md'
            if ls.get('status') in ('ready', 'draft'):
                if not path.exists():
                    print(f'! нет файла {path}'); errors += 1; continue
                try:
                    built[(ch['id'], ls['id'])] = parse_lesson(path)
                except FormatError as e:
                    print(f'! {e}'); errors += 1
        try:
            ch['_extra'] = parse_chapter_extra(ch)
        except FormatError as e:
            print(f'! {e}'); errors += 1; ch['_extra'] = {}
        for ex in ch.get('exams', []):
            ex['exam'] = True
            try:
                built[(ch['id'], ex['id'])] = parse_lesson(CONTENT / ch['id'] / f'{ex["id"]}.md')
            except (FormatError, FileNotFoundError) as e:
                print(f'! {e}'); errors += 1
    return course, built, errors


def build(check_only: bool = False, export_path: Path | None = None) -> int:
    course, built, errors = load_course()
    index_data = []   # для карты курса и прогресса
    if export_path and not errors:
        export(built, export_path)
        return 0
    if errors or check_only:
        n = sum(len(v['tasks']) for v in built.values())
        print(f'Уроков разобрано: {len(built)}, задач: {n}, ошибок: {errors}')
        return 1 if errors else 0

    for ch in course['chapters']:
        index_data.append({
            'id': ch['id'], 'n': ch['n'], 'title': ch['title'], 'goal': ch.get('goal', ''),
            'lessons': [{
                'id': ls['id'], 'n': ls['n'], 'title': ls['title'], 'minutes': ls.get('minutes'),
                'status': ls.get('status', 'planned'), 'url': lesson_url(ch, ls),
                'core': bool(ls.get('core')),
                'tasks': [{'id': t['id'], 'level': t['level'], 'title': t['title']}
                          for t in built.get((ch['id'], ls['id']), {}).get('tasks', [])],
                # разделы теории (id заголовков h2) — для отметок «прочитано»
                'secs': [sid for sid, _ in with_toc(built[(ch['id'], ls['id'])]['theory'])[1]]
                        if (ch['id'], ls['id']) in built and not ls['id'].startswith('exam') else [],
            } for ls in ch.get('lessons', [])],
            'exams': [{
                'id': ex['id'], 'title': ex['title'], 'after': ex.get('after'), 'minutes': ex.get('minutes'),
                'url': lesson_url(ch, ex),
                'tasks': [{'id': t['id'], 'level': t['level'], 'title': t['title'], 'topic': t['topic']}
                          for t in built[(ch['id'], ex['id'])]['tasks']],
            } for ex in ch.get('exams', []) if (ch['id'], ex['id']) in built],
            'intro': f'{ch["id"]}/index.html' if 'intro' in ch.get('_extra', {}) else None,
            'test': {'url': f'{ch["id"]}/test.html', 'n': ch['_extra']['test']['n']} if 'test' in ch.get('_extra', {}) else None,
        })

    for ch in course['chapters']:
        avail = [ls for ls in ch.get('lessons', []) if (ch['id'], ls['id']) in built]
        for ls in avail:
            write_lesson(course, ch, ls, built[(ch['id'], ls['id'])], avail, index_data)
        for ex in ch.get('exams', []):
            if (ch['id'], ex['id']) in built:
                write_lesson(course, ch, ex, built[(ch['id'], ex['id'])], avail, index_data)
        if ch.get('_extra'):
            write_chapter_pages(course, ch, ch['_extra'], index_data)
    write_index(course, index_data)
    write_aux(course, index_data)
    # задачи, переехавшие при делении урока: старый ключ прогресса → новый.
    # Исторические переезды хранятся в content/moved.json и не теряются при пересборке;
    # к ним добавляются новые из split_from в course.yaml.
    moved = json.loads((CONTENT / 'moved.json').read_text(encoding='utf-8'))
    for ch in course['chapters']:
        tasks_of = {l['id']: l.get('tasks', []) for c in index_data if c['id'] == ch['id'] for l in c['lessons']}
        for ls in ch.get('lessons', []):
            m = re.match(r'(\S+)', str(ls.get('split_from', '')))
            if m:
                for t in tasks_of.get(ls['id'], []):
                    moved[f"{ch['id']}/{m.group(1)}/{t['id']}"] = f"{ch['id']}/{ls['id']}/{t['id']}"
    moved = resolve_moved(moved, {f"{c['id']}/{l['id']}/{t['id']}"
                                  for c in index_data for l in c['lessons'] for t in l.get('tasks', [])})
    (SITE / 'assets' / 'course.js').write_text(
        'window.DSC_COURSE = ' + json.dumps(index_data, ensure_ascii=False) + ';\n'
        'window.DSC_MOVED = ' + json.dumps(moved, ensure_ascii=False) + ';\n', encoding='utf-8')
    n = sum(len(v['tasks']) for v in built.values())
    print(f'Готово: уроков {len(built)}, задач {n} → site/')
    return 0


def resolve_moved(moved: dict, live: set) -> dict:
    """Схлопывает цепочки переездов (a→b→c ⇒ a→c) и проверяет карту.

    Старый ключ не должен совпадать с существующей задачей (иначе её прогресс
    перезапишется), а конечный ключ должен существовать.
    """
    out = {}
    for old in moved:
        seen, cur = {old}, moved[old]
        while cur in moved:
            if cur in seen:
                raise SystemExit(f'moved.json: цикл переездов через {cur}')
            seen.add(cur)
            cur = moved[cur]
        if old in live:
            raise SystemExit(f'moved.json: старый ключ {old} совпадает с существующей задачей')
        if cur not in live:
            raise SystemExit(f'moved.json: задача-адресат {cur} (для {old}) не найдена')
        out[old] = cur
    return dict(sorted(out.items()))


def _slug(text: str, used: set) -> str:
    base = re.sub(r'[^\w]+', '-', re.sub(r'<[^>]+>', '', text).lower()).strip('-')[:48] or 's'
    slug, i = base, 2
    while slug in used:
        slug, i = f'{base}-{i}', i + 1
    used.add(slug)
    return slug


def with_toc(theory_html: str):
    used, toc = set(), []

    def sub(m):
        sid = _slug(m.group(1), used)
        toc.append((sid, re.sub(r'<[^>]+>', '', m.group(1))))
        return f'<h2 id="{sid}">{m.group(1)}</h2>'
    return re.sub(r'<h2>(.*?)</h2>', sub, theory_html), toc


FB = ('<div class="fb" data-sec="{sid}"><span>Понятно объяснено?</span>'
      '<button type="button" class="fb-btn" data-v="1">Да</button>'
      '<button type="button" class="fb-btn" data-v="-1">Не очень</button></div>')


def add_feedback(theory_html: str, toc) -> str:
    """В конце каждого раздела теории — «Понятно объяснено? Да / Не очень»."""
    parts = re.split(r'(?=<h2 id=")', theory_html)
    out = [parts[0]]
    for part, (sid, _t) in zip(parts[1:], toc):
        out.append(part + FB.format(sid=sid))
    return ''.join(out)


def side_list(ch, current, avail):
    have = {a['id'] for a in avail}
    items = []
    exams = {ex.get('after'): ex for ex in ch.get('exams', [])}
    for x in ch['lessons']:
        cur = ' aria-current="page"' if x is current else ''
        if x['id'] in have:
            items.append(f'<li><a href="{x["id"]}.html"{cur} data-lesson="{ch["id"]}/{x["id"]}">'
                         f'<span class="dot"></span><span class="num">{x["n"]}</span>'
                         f'<span class="t">{html.escape(x["title"])}</span></a></li>')
        else:
            items.append(f'<li class="soon"><span class="dot"></span><span class="num">{x["n"]}</span>'
                         f'<span class="t">{html.escape(x["title"])}</span><span class="tag">скоро</span></li>')
        ex = exams.get(x['id'])
        if ex:
            cur = ' aria-current="page"' if ex is current else ''
            items.append(f'<li class="exam-item"><a href="{ex["id"]}.html"{cur} data-exam="{ch["id"]}/{ex["id"]}">'
                         f'<span class="dot"></span><span class="num">✓</span>'
                         f'<span class="t">{html.escape(ex["title"])}</span></a></li>')
    return ''.join(items)


DEEP_TITLE = 'Углубление: не входит в основной путь курса. Можно пропустить и вернуться позже.'


def deep_tag(ls) -> str:
    return '' if ls.get('core') else f'<span class="tag deep" title="{DEEP_TITLE}">углубл.</span>'


def core_attr(ls) -> str:
    return f' data-core="{1 if ls.get("core") else 0}"'


def course_tree(root: str, index_data: list, cur_ch: str | None = None, cur_id: str | None = None) -> str:
    """Раскрываемое оглавление всего курса: главы — <details>, внутри — уроки (и контрольные)."""
    out = ['<div class="tree-head"><span class="eyebrow">Оглавление курса</span>'
           '<button class="linklike tree-toggle" type="button" data-tree-toggle>Развернуть всё</button></div>'
           '<label class="core-only-toggle"><input type="checkbox" data-core-only> Только основной путь</label>'
           '<ul class="course-tree">']
    for ch in index_data:
        ready = [x for x in ch['lessons'] if x['status'] in ('ready', 'draft')]
        num = f'<span class="tree-num">{ch["n"]:02d}</span><span class="tree-t">{html.escape(ch["title"])}</span>'
        if not ready:
            out.append(f'<li class="tree-ch tree-soon"><div class="tree-sum">{num}<span class="tag">скоро</span></div></li>')
            continue
        items = []
        exams = {ex.get('after'): ex for ex in ch.get('exams', [])}
        for x in ch['lessons']:
            key = f'{ch["id"]}/{x["id"]}'
            cur = ' aria-current="page"' if ch['id'] == cur_ch and x['id'] == cur_id else ''
            if x in ready:
                items.append(f'<li{core_attr(x)}><a href="{root}{x["url"]}"{cur} data-lesson="{key}"><span class="dot"></span>'
                             f'<span class="num">{x["n"]}</span><span class="t">{html.escape(x["title"])}</span>{deep_tag(x)}</a></li>')
            else:
                items.append(f'<li class="soon"><span class="dot"></span><span class="num">{x["n"]}</span>'
                             f'<span class="t">{html.escape(x["title"])}</span><span class="tag">скоро</span></li>')
            ex = exams.get(x['id'])
            if ex:
                cur = ' aria-current="page"' if ch['id'] == cur_ch and ex['id'] == cur_id else ''
                items.append(f'<li class="exam-item"><a href="{root}{ex["url"]}"{cur} data-exam="{ch["id"]}/{ex["id"]}">'
                             f'<span class="dot"></span><span class="num">✓</span><span class="t">{html.escape(ex["title"])}</span></a></li>')
        if ch.get('intro'):
            cur = ' aria-current="page"' if ch['id'] == cur_ch and cur_id == '_intro' else ''
            items.insert(0, f'<li class="intro-item"><a href="{root}{ch["intro"]}"{cur} data-chintro="{ch["id"]}"><span class="dot"></span>'
                            f'<span class="num">i</span><span class="t">О главе</span></a></li>')
        if ch.get('test'):
            cur = ' aria-current="page"' if ch['id'] == cur_ch and cur_id == '_test' else ''
            items.append(f'<li class="exam-item"><a href="{root}{ch["test"]["url"]}"{cur} data-ctest="{ch["id"]}" data-n="{ch["test"]["n"]}">'
                         f'<span class="dot"></span><span class="num">?</span><span class="t">Итоговый тест главы</span></a></li>')
        op = ' open' if ch['id'] == cur_ch else ''
        out.append(f'<li><details class="tree-ch" data-ch="{ch["id"]}"{op}><summary class="tree-sum">{num}'
                   f'<span class="tree-c" data-chp="{ch["id"]}">{len(ready)}</span></summary>'
                   f'<ol class="side-list">{"".join(items)}</ol></details></li>')
    out.append('</ul>')
    return ''.join(out)


PRACTICE_INTRO = ('<h2>Практика</h2>\n      <p class="legend">Задачи идут от простых к сложным. Для урока достаточно решить все, кроме задач '
                  '<span class="lvl lvl-star">со звёздочкой</span>.\n      <kbd class="mod">Ctrl</kbd>+<kbd>Enter</kbd> — запустить, '
                  '<kbd>Shift</kbd>+<kbd>Enter</kbd> — проверить.</p>')
EXAM_INTRO = ('<h2>Задачи</h2>\n      <p class="legend">Решайте в любом порядке. «Проверить» говорит только «верно» или «нет» — без подсказок. '
              'Когда закончите, нажмите «Завершить» внизу: появится результат, разбор по темам, подсказки и решения. '
              'Контрольную можно пройти заново.</p>')


def write_lesson(course, ch, ls, L, avail, index_data):
    root = '../'
    is_exam = bool(ls.get('exam'))
    theory_html, toc = with_toc(L['theory'])
    theory_html = add_feedback(theory_html, toc)
    num = {t['id']: (i, t['title']) for i, t in enumerate(L['tasks'], 1)}
    task_sec = {}
    sec_parts = re.split(r'(?=<h2 id=")', theory_html)
    for k, part in enumerate(sec_parts):
        hm = re.match(r'<h2 id="([^"]+)">(.*?)</h2>', part)
        def fill(mm, hm=hm):
            tids = mm.group(1).split(',')
            for tid in tids:
                if hm and tid not in task_sec:
                    task_sec[tid] = (hm.group(1), re.sub(r'<[^>]+>', '', hm.group(2)))
            links = ''.join(f'<a href="#task-{tid}"><b>{num[tid][0]}</b> {inline(num[tid][1])}</a>' for tid in tids)
            word = 'задача' if len(tids) == 1 else 'задачи'
            return f'<div class="practice-link"><span>Потренироваться — {word}:</span>{links}</div>'
        sec_parts[k] = re.sub(r'<div class="practice-link" data-tasks="([^"]+)"></div>', fill, part)
    theory_html = ''.join(sec_parts)
    toc.append(('practice', 'Задачи' if is_exam else 'Практика'))
    if L['meta'].get('recap'):
        toc.append(('recap', 'Что запомнить'))
    if not is_exam:
        toc.append(('notes', 'Мои заметки'))
        collect_lesson(ch, ls, L, theory_html)
    toc_html = ('<nav class="toc" aria-label="На этой странице"><div class="toc-title">На странице</div><ol>' +
                ''.join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in toc) + '</ol></nav>')
    meta = L['meta']
    title = meta.get('title', ls['title'])
    if is_exam:
        after = next((a for a in avail if a['id'] == ls.get('after')), None)
        pos = avail.index(after) if after else len(avail) - 1
        prev_ls = avail[pos] if avail else None
        next_ls = avail[pos + 1] if pos + 1 < len(avail) else None
    else:
        pos = avail.index(ls)
        prev_ls = avail[pos - 1] if pos > 0 else None
        nxt_ex = next((e for e in ch.get('exams', []) if e.get('after') == ls['id']), None)
        next_ls = nxt_ex or (avail[pos + 1] if pos + 1 < len(avail) else None)

    side = [f'<div class="side-head"><div class="eyebrow">Глава {ch["n"]}</div>'
            f'<div class="side-title">{html.escape(ch["title"])}</div>'
            f'<div class="meter" id="chapter-meter"><i></i></div></div>',
            course_tree(root, index_data, ch['id'], ls['id'])]

    tasks_html = []
    for i, t in enumerate(L['tasks'], 1):
        tasks_html.append(f'''<section class="task" id="task-{t["id"]}" data-task="{t["id"]}" data-level="{t["level"]}" data-kind="{'parsons' if t['parsons'] else 'code'}">
  <header class="task-head">
    <span class="task-num">{i}</span>
    <h3 class="task-title">{inline(t["title"])}</h3>
    <span class="lvl lvl-{t["level"]}">{LEVELS[t["level"]]}</span>
    <span class="task-state" aria-hidden="true"></span>
  </header>
  {('<a class="task-ref" href="#' + task_sec[t["id"]][0] + '">↑ К теории: ' + html.escape(task_sec[t["id"]][1]) + '</a>') if t["id"] in task_sec else ''}
  <div class="task-text prose">{render(t["text"])}</div>
  <div class="task-ui"></div>
</section>''')

    data = {
        'lesson': f'{ch["id"]}/{ls["id"]}', 'title': title, 'chapter': ch['title'],
        'tasks': [{k: t[k] for k in ('id', 'title', 'level', 'starter', 'setup', 'check', 'hints',
                                       'solution', 'explain', 'parsons')} for t in L['tasks']],
        'files': meta.get('files', []),
        'mode': 'exam' if is_exam else 'lesson',
        'display': bool(meta.get('display', ch.get('display', False))),
        'topics': {t['id']: t['topic'] for t in L['tasks'] if t['topic']},
    }
    recap = meta.get('recap') or []
    recap_html = ''
    if recap:
        recap_html = ('<section class="recap" id="recap"><h2>Что запомнить</h2><ul>' +
                      ''.join(f'<li>{inline(r)}</li>' for r in recap) + '</ul></section>')

    def pager_link(x, cls, label):
        if not x:
            return f'<span class="{cls} empty"></span>'
        num = '' if x.get('exam') else f'{x["n"]}. '
        return (f'<a class="{cls}" href="{x["id"]}.html"><span class="pl">{label}</span>'
                f'<span class="pt">{num}{html.escape(x["title"])}</span></a>')
    extra = ch.get('_extra', {})
    if next_ls:
        nxt = pager_link(next_ls, 'next', 'Контрольная точка →' if next_ls.get('exam') else 'Следующий урок →')
    elif 'test' in extra:
        nxt = '<a class="next" href="test.html"><span class="pl">Итоговый тест главы →</span><span class="pt">' + str(extra['test']['n']) + ' вопросов на понимание</span></a>'
    else:
        nxt = f'<a class="next" href="{root}index.html"><span class="pl">Глава пройдена →</span><span class="pt">К карте курса</span></a>'
    prv = pager_link(prev_ls, 'prev', '← Предыдущий') if prev_ls or 'intro' not in extra else \
        '<a class="prev" href="index.html"><span class="pl">← О главе</span><span class="pt">' + html.escape(ch['title']) + '</span></a>'

    n_base = sum(1 for t in L['tasks'] if t['level'] != 'star')
    data_html = data_files_block(root, meta.get('files', []))
    theory_html = link_data(root, theory_html)
    tasks_html = [link_data(root, t) for t in tasks_html]
    body = f'''<a class="skip" href="#main">К уроку</a>
{topbar(root, f'<a href="{root}index.html#{ch["id"]}">Глава {ch["n"]}. {html.escape(ch["title"])}</a>', True, True)}
<div class="layout">
  <nav class="sidebar" id="sidebar" aria-label="Уроки главы">{''.join(side)}</nav>
  <div class="scrim" id="scrim"></div>
  <main id="main" class="lesson">
    <div class="lesson-head">
      <div class="eyebrow">{'Контрольная точка' if is_exam else f'Урок {ls["n"]}'}{'' if is_exam else (' · основной путь' if ls.get('core') else f' · <span class="deep-eb" title="{DEEP_TITLE}">углубление</span>')} · ≈ {ls.get("minutes", "?")} мин · задач: {len(L["tasks"])}</div>
      <h1>{html.escape(title)}</h1>
      {f'<p class="lead">{inline(meta["lead"])}</p>' if meta.get("lead") else ''}
      {data_html}
      <div class="lesson-meter" id="lesson-meter"><div class="meter"><i></i></div><span>0 из {n_base}</span></div>
    </div>
    <article class="prose theory">{theory_html}</article>
    <section class="practice" id="practice">
      {EXAM_INTRO if is_exam else PRACTICE_INTRO}
      {''.join(tasks_html)}
    </section>
    {recap_html}
    {'<section class="exam-finish" id="exam-finish"></section>' if is_exam else ''}
    <section class="notes" id="notes"{' hidden' if is_exam else ''}>
      <div class="notes-head"><h2>Мои заметки</h2><span class="muted" id="notes-state"></span></div>
      <textarea id="notes-text" placeholder="Что было непонятно, что хочется запомнить своими словами, вопросы на потом… Сохраняется само." spellcheck="true"></textarea>
      <p class="muted small">Все заметки — на странице <a href="{root}notes.html">«Заметки»</a>, их можно выгрузить в Markdown.</p>
    </section>
    <nav class="pager">{prv}{nxt}</nav>
    <footer class="foot">Текст курса — CC BY-SA 4.0. Нашли ошибку или непонятное место — <button class="linklike" id="ask-lesson">скопировать вопрос для ИИ-репетитора</button>.</footer>
  </main>
  {toc_html}
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>'''
    data_json = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    scripts = (f'<script type="application/json" id="lesson-data">{data_json}</script>\n'
               f'<script src="{A(root, 'vendor/codemirror/codemirror.js')}"></script>\n'
               f'<script src="{A(root, 'vendor/codemirror/python.js')}"></script>\n'
               f'<script src="{A(root, 'vendor/codemirror/matchbrackets.js')}"></script>\n'
               f'<script src="{A(root, 'vendor/codemirror/closebrackets.js')}"></script>\n'
               + common_scripts(root) + f'\n<script src="{A(root, "lesson.js")}"></script>')
    out = SITE / ch['id'] / f'{ls["id"]}.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(f'{title} — DS для аналитиков', body, root,
                        f'class="page-lesson" data-root="{root}"',
                        f'<link rel="stylesheet" href="{A(root, 'vendor/codemirror/codemirror.css')}">\n',
                        scripts), encoding='utf-8')


def common_scripts(root: str) -> str:
    return (f'<script src="{A(root, "course.js")}"></script>\n'
            f'<script src="{A(root, "search.js")}" defer></script>\n'
            f'<script src="{A(root, "core.js")}"></script>')


# ---------- материал для шпаргалки и поиска ----------

COLLECT: list[dict] = []


def _plain(h: str) -> str:
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


def collect_lesson(ch, ls, L, theory_html):
    parts = re.split(r'<h2 id="([^"]+)">(.*?)</h2>', theory_html)
    sections, sql = [], []
    intro = parts[0]
    for i in range(1, len(parts), 3):
        sid, stitle, body = parts[i], _plain(parts[i + 1]), parts[i + 2]
        sections.append({'id': sid, 'title': stitle, 'text': _plain(body)[:700]})
        for m in re.finditer(r'<aside class="callout callout-sql">(.*?)</aside>', body, re.S):
            inner = re.sub(r'<div class="callout-title">.*?</div>', '', m.group(1), count=1, flags=re.S)
            sql.append({'sec': sid, 'sec_title': stitle, 'html': inner.strip()})
    COLLECT.append({'ch': ch, 'ls': ls, 'url': f'{ch["id"]}/{ls["id"]}.html', 'lead': L['meta'].get('lead', ''),
                    'intro': _plain(intro)[:300], 'sections': sections, 'sql': sql,
                    'recap': L['meta'].get('recap') or [], 'tasks': L['tasks']})


CS_FILTER = ('<div class="cs-filter"><input type="search" id="cs-filter" placeholder="Фильтр: GROUP BY, срез, round…" '
             'aria-label="Фильтр шпаргалки"></div>\n<p class="muted" id="cs-empty" hidden>Ничего не нашлось.</p>')
NOTES_INNER = ('<p><button class="btn" id="notes-export" hidden>Скачать все заметки (.md)</button></p>\n'
               '<div id="notes-list"></div>')
STATS_INNER = '''<div class="tiles" id="tiles"></div>
  <section class="panel"><h2>Решено задач по дням</h2><p class="muted small">Последние 30 дней, считается первое решение задачи.</p>
    <div class="chart" id="chart"></div>
    <details class="chart-table"><summary>Таблицей</summary><div id="chart-table"></div></details></section>
  <section class="panel"><h2>Темп</h2><p id="forecast"></p></section>
  <section class="panel"><h2>По главам</h2><div id="chapters"></div></section>
  <section class="panel"><div id="hard"></div></section>
  <section class="panel"><div id="review"></div></section>'''


def write_aux(course, index_data):
    root = ''
    # --- поисковый индекс ---
    idx = []
    for c in COLLECT:
        where = f'Урок {c["ls"]["n"]}. {c["ls"]["title"]}'
        idx.append({'k': 'lesson', 't': c['ls']['title'], 'x': _plain(inline(c['lead'])) + ' ' + c['intro'],
                    'u': c['url'], 'w': f'Глава {c["ch"]["n"]}. {c["ch"]["title"]}'})
        for sec in c['sections']:
            idx.append({'k': 'section', 't': sec['title'], 'x': sec['text'], 'u': f'{c["url"]}#{sec["id"]}', 'w': where})
        for q in c['sql']:
            idx.append({'k': 'sql', 't': f'{q["sec_title"]} — как в SQL', 'x': _plain(q['html']),
                        'u': f'{c["url"]}#{q["sec"]}', 'w': where})
        for t in c['tasks']:
            idx.append({'k': 'task', 't': t['title'], 'x': _plain(render(t['text']))[:300],
                        'u': f'{c["url"]}#task-{t["id"]}', 'w': where})
        for r in c['recap']:
            idx.append({'k': 'recap', 't': _plain(inline(r))[:90], 'x': _plain(inline(r)), 'u': f'{c["url"]}#recap', 'w': where})
    (SITE / 'assets' / 'search.js').write_text('window.DSC_SEARCH = ' + json.dumps(idx, ensure_ascii=False) + ';\n',
                                               encoding='utf-8')

    def shell(title, inner, page_id, lead=''):
        lead_html = f'<p class="lead">{lead}</p>' if lead else ''
        body = (f'{topbar(root, html.escape(title), False)}\n<main class="home page-{page_id}">\n'
                f'  <h1 class="page-title">{html.escape(title)}</h1>\n  {lead_html}\n  {inner}\n</main>\n'
                '<div class="toast" id="toast" role="status" aria-live="polite"></div>')
        scripts = common_scripts(root) + f'\n<script src="{A(root, "pages.js")}"></script>'
        (SITE / f'{page_id}.html').write_text(
            page(f'{title} — DS для аналитиков', body, root, f'class="page-aux" data-root="" data-page="{page_id}"',
                 scripts=scripts), encoding='utf-8')

    # --- шпаргалка ---
    blocks, cur_ch = [], None
    for c in COLLECT:
        if not c['sql'] and not c['recap']:
            continue
        if c['ch'] is not cur_ch:
            cur_ch = c['ch']
            blocks.append(f'<h2 class="cs-ch">Глава {cur_ch["n"]}. {html.escape(cur_ch["title"])}</h2>')
        cards = []
        if c['recap']:
            cards.append('<article class="cs-card cs-recap"><div class="cs-kind">Что запомнить</div><ul>' +
                         ''.join(f'<li>{inline(r)}</li>' for r in c['recap']) +
                         f'</ul><a class="cs-link" href="{c["url"]}#recap">к уроку →</a></article>')
        for q in c['sql']:
            cards.append(f'<article class="cs-card cs-sql"><div class="cs-kind">Как в SQL · {html.escape(q["sec_title"])}</div>'
                         f'<div class="prose">{q["html"]}</div><a class="cs-link" href="{c["url"]}#{q["sec"]}">к разделу →</a></article>')
        blocks.append(f'<section class="cs-lesson"><h3><a href="{c["url"]}">{c["ls"]["n"]}. {html.escape(c["ls"]["title"])}</a></h3>'
                      f'<div class="cs-grid">{"".join(cards)}</div></section>')
    shell('Шпаргалка', CS_FILTER + '\n' + ''.join(blocks), 'cheatsheet',
          'Всё главное из уроков в одном месте: итоги «Что запомнить» и сравнения с SQL. Собирается из уроков автоматически.')
    shell('Мои заметки', NOTES_INNER, 'notes', 'Заметки, которые вы писали в конце уроков.')
    shell('Статистика', STATS_INNER, 'stats')


def core_path_block(index_data) -> str:
    core = [(ch, ls) for ch in index_data for ls in ch['lessons'] if ls.get('core') and ls['status'] == 'ready']
    allr = [(ch, ls) for ch in index_data for ls in ch['lessons'] if ls['status'] == 'ready']
    mins = sum(ls.get('minutes') or 0 for _, ls in core)
    keys = ' '.join(f'{ch["id"]}/{ls["id"]}' for ch, ls in core)
    return (f'<div class="core-path" data-core-keys="{keys}"><div class="eyebrow">Основной путь</div>'
            f'<p><b>{_lessons_word(len(core))}, ≈ {fmt_minutes(mins)}</b> — Python, pandas и SQL, git, очистка данных, EDA, '
            f'статистика и A/B, первые модели, метрики, перевод модели в деньги и два обязательных проекта: итоговый в главе 8 '
            f'и финальный в главе 15. Этого хватает для работы аналитиком с ML-задачами. '
            f'Остальные {_lessons_word(len(allr) - len(core))} помечены «углубл.» — оконные функции SQL, линейная алгебра, '
            f'бустинг, нейросети, временные ряды, тексты, зрение, сервис и развёртывание модели: к ним можно вернуться по необходимости.</p>'
            f'<div class="core-meter"><div class="meter"><i></i></div><span id="core-progress"></span></div>'
            f'<label class="core-only-toggle"><input type="checkbox" data-core-only> Показывать только основной путь</label></div>')


def write_index(course, index_data):
    root = ''
    chapters = []
    for ch in index_data:
        rows = []
        for ls in ch['lessons']:
            ready = ls['status'] in ('ready', 'draft') and ls['tasks'] is not None and ls['status'] != 'planned'
            if ready:
                rows.append(f'<li{core_attr(ls)}><a class="row" href="{ls["url"]}" data-lesson="{ch["id"]}/{ls["id"]}">'
                            f'<span class="dot"></span><span class="num">{ls["n"]}</span>'
                            f'<span class="t">{html.escape(ls["title"])}{deep_tag(ls)}</span>'
                            f'<span class="m">{ls["minutes"]} мин</span><span class="p" data-p></span></a></li>')
            else:
                rows.append(f'<li><span class="row soon"><span class="dot"></span><span class="num">{ls["n"]}</span>'
                            f'<span class="t">{html.escape(ls["title"])}</span><span class="m">скоро</span></span></li>')
            for ex in ch.get('exams', []):
                if ex['after'] == ls['id']:
                    rows.append(f'<li><a class="row exam-row" href="{ex["url"]}" data-exam="{ch["id"]}/{ex["id"]}">'
                                f'<span class="dot"></span><span class="num">✓</span><span class="t">{html.escape(ex["title"])}</span>'
                                f'<span class="m">{ex["minutes"]} мин</span><span class="p" data-p></span></a></li>')
        if ch.get('test'):
            rows.append(f'<li><a class="row exam-row" href="{ch["test"]["url"]}" data-ctest="{ch["id"]}" data-n="{ch["test"]["n"]}">'
                        f'<span class="dot"></span><span class="num">?</span><span class="t">Итоговый тест главы</span>'
                        f'<span class="m">{ch["test"]["n"]} вопросов</span><span class="p" data-p></span></a></li>')
        n_ready = sum(1 for ls in ch['lessons'] if ls['status'] in ('ready', 'draft'))
        body = (f'<ol class="lesson-rows">{"".join(rows)}</ol>' if ch['lessons'] else
                '<p class="muted">Глава в плане.</p>')
        state = 'open' if n_ready else ''
        chapters.append(f'''<details class="chapter" id="{ch["id"]}" {state}>
  <summary><span class="ch-num">{ch["n"]:02d}</span><span class="ch-title">{html.escape(ch["title"])}</span>
  <span class="ch-meta" data-ch="{ch["id"]}">{n_ready and f"{n_ready} из {len(ch['lessons'])} уроков готовы" or "в плане"}</span></summary>
  {f'<p class="ch-goal">{html.escape(ch["goal"])}' + (f' <a class="ch-intro-link" href="{ch["intro"]}">О главе →</a>' if ch.get("intro") else '') + '</p>' if ch.get("goal") else ''}
  {body}
</details>''')

    body = f'''{topbar(root, '', True)}
<div class="layout layout-home">
<nav class="sidebar" id="sidebar" aria-label="Оглавление курса">{course_tree(root, index_data)}</nav>
<div class="scrim" id="scrim"></div>
<main class="home">
  <section class="hero">
    <h1>{html.escape(course["title"])}</h1>
    <p class="lead">{html.escape(course["subtitle"])}</p>
    <div class="resume" id="resume" hidden>
      <div><div class="eyebrow">Продолжить</div><div class="resume-title" id="resume-title"></div><div class="resume-where muted" id="resume-where"></div></div>
      <a class="btn primary" id="resume-link" href="#">Открыть урок</a>
    </div>
    <div class="stats" id="stats"></div>
    {core_path_block(index_data)}
  </section>
  <div id="review"></div>
  <section class="howto">
    <div><b>Читайте и запускайте.</b> Каждый пример в тексте можно изменить и выполнить прямо на странице.</div>
    <div><b>Решайте лестницу.</b> Разминка → база → посложнее → со звёздочкой. Проверка скажет, что не так.</div>
    <div><b>Застряли?</b> Подсказки открываются по одной. Кнопка «Спросить» готовит вопрос для ИИ-репетитора.</div>
  </section>
  <section class="map">
    <h2>Программа</h2>
    <p class="muted">{html.escape(course["story"])}</p>
    {''.join(chapters)}
  </section>
  {jupyter_home_block(root, index_data)}
  <footer class="foot">
    <span id="storage-note"></span><br><button class="linklike" id="export-btn">Скачать копию прогресса</button> ·
    <label class="linklike">Загрузить из файла<input type="file" id="import-file" accept="application/json" hidden></label>
    <br>Текст курса — CC BY-SA 4.0, код — MIT.
  </footer>
</main>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>'''
    scripts = common_scripts(root) + f'\n<script src="{A(root, "pages.js")}"></script>'
    (SITE / 'index.html').write_text(page(course['title'], body, root, 'class="page-home" data-root="" data-page="home"',
                                          scripts=scripts), encoding='utf-8')


if __name__ == '__main__':
    exp = None
    if '--export' in sys.argv:
        exp = Path(sys.argv[sys.argv.index('--export') + 1]).resolve()
    sys.exit(build('--check' in sys.argv, exp))
