"""Compare the release consumed by the independent runners to the actual public cards."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

here = Path(__file__).resolve().parent
chapter = here.parents[1]
root = here.parents[4]
export = Path(sys.argv[1])
fields = ('setup', 'starter', 'solution', 'check')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def index(rows):
    return {row['lesson'] + '/' + row['id']: row for row in rows if row['kind'] == 'task'}

chapter_rows = [t for t in read(export) if t['lesson'].startswith('ch11/')]
cards = index(chapter_rows)
surfaces = {
    'html': {},
    'notebook_tasks': read(root/'site/notebooks/tasks/ch11.json')['tasks'],
    'critic_actual_after': index(read(chapter/'check-evidence/after-tasks.json')),
    'archived_release': index(read(chapter/'technical/chapter-export.json')),
}
pages = {}
for path in (root/'site/ch11').glob('*.html'):
    markup = path.read_text()
    match = re.search(r'id="lesson-data">(.*?)</script>', markup, re.S)
    pages[path.stem] = markup.split('<script type="application/json"', 1)[0]
    if match:
        page = json.loads(match[1])
        for task in page.get('tasks', []):
            surfaces['html'][page['lesson']+'/'+task['id']] = task

for source in surfaces.values():
    assert set(source) == set(cards)
    for key in cards:
        for field in fields:
            assert (source[key][field] or '') == (cards[key][field] or ''), (key, field)

practice = root/'site/notebooks/ch11-practice.ipynb'
cell_ids = set()
for cell in read(practice)['cells']:
    code = ''.join(cell['source'])
    match = re.fullmatch(r'%%task (\S+)\n(.*)', code, re.S)
    if match:
        key, body = match.groups()
        assert key not in cell_ids
        cell_ids.add(key)
        assert body.strip() == (cards[key]['starter'].strip() or '# ваш код')
parsons = {key for key, task in surfaces['notebook_tasks'].items() if task['parsons']}
assert set(cards) == cell_ids | parsons and cell_ids.isdisjoint(parsons)

mlp = pages['03-mlp']
figures = {}
for name in ('nn-alpha', 'nn-overfit-epochs', 'nn-tabular-vs-raw'):
    svg = root/f'content/figures/{name}.svg'
    assert svg.read_text().strip() in mlp
    figures[name] = sha(svg)
for literal in ('1 800', '600 валидационн', '1 620', '180', '1 350', '450 сравнивают',
                'AUC валидация', 'обучение 0.945', 'валидация 0.911'):
    assert literal in mlp, literal
mlp_tasks = surfaces['html']
for name, needle in (
    ('03-mlp/alpha-sweep', 'при alpha = 1 получено 0.876'),
    ('03-mlp/depth', '0.869, 0.876 и 0.853'),
    ('04c-debug/dropout-net', '0.879, 0.874 и 0.872'),
):
    assert needle in mlp_tasks['ch11/'+name]['explain']
project = pages['05-project']
assert 'пиксели этой партии' in project
assert 'missed_example_position' in project
assert 'Что сообщить руководителю' in project
assert project.index('Архив оцифровывает') < project.index('nn-operator-flow')
assert 'Сравнение с ближайшими соседями' in project
assert 'Сравним оставшиеся вне очереди ошибки' in project
assert 'Обе модели выдают оценки классов' in mlp_tasks['ch11/05-project/mlp']['explain']
assert 'nn-operator-flow' not in mlp_tasks['ch11/05-project/blur-transfer']['explain']
native = root/'site/notebooks/extra/ch11-pytorch-tabular.ipynb'
nb = read(native)['cells']
native_prose = {idx: ''.join(nb[idx]['source']) for idx in (0,8,18,25)}
for idx, needle in [(0, 'версии библиотек и устройство'), (8, 'после секундомера'),
                    (18, 'не измеряет разброс'), (25, 'разность средних ошибок')]:
    assert needle in native_prose[idx]
baseline = read(chapter/'technical/baseline.json')['data']
for name, digest in baseline.items():
    assert sha(root/'site/data'/name) == sha(chapter/'technical/data-baseline'/name) == digest
with (here.parent/'ledger.csv').open() as f:
    ledger = list(csv.DictReader(f))
assert len(ledger) == len({r['id'] for r in ledger}) == 41
assert ledger[-1]['id'] == 'RCP11-01'
summary = dict(full_export_sha256=sha(export), counts=Counter(t['kind'] for t in chapter_rows),
               compared_fields=fields, identical_task_counts={k: len(v) for k,v in surfaces.items()},
               public_notebook_code_tasks=len(cell_ids), browser_parsons=len(parsons), practice_notebook_sha256=sha(practice),
               native_notebook_sha256=sha(native), project_html_sha256=sha(root/'site/ch11/05-project.html'),
               public_letter_after_archive_prompt=True, public_letter_removed_from_optional_explanation=True,
               verified_figure_hashes=figures, data_sha256=baseline, ledger_ids=len(ledger))
(here/'release-parity.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(summary, ensure_ascii=False))
