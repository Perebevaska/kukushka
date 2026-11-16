"""Read-only artifact comparison; writes only this acceptance evidence directory."""
import collections
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import build
import make_notebooks as nb

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

course, built, errors = build.load_course()
assert errors == 0
chapter = json.loads((OUT / 'current-export-ch01.json').read_text())
with tempfile.TemporaryDirectory() as td:
    comparison_export = Path(td) / 'source-export.json'
    build.export(built, comparison_export)
    export_hash = sha(comparison_export)
    source_items = json.loads(comparison_export.read_text())
    assert [x for x in source_items if x['lesson'].startswith('ch01/')] == chapter
tasks = {(x['lesson'], x['id']): x for x in chapter if x['kind'] == 'task'}
diffs = []
html_tasks = 0
for (ch, ls), lesson in built.items():
    if ch != 'ch01':
        continue
    page = (ROOT / 'site' / ch / f'{ls}.html').read_text()
    data = json.loads(re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>', page, re.S)[1])
    source = {x['id']: x for x in lesson['tasks']}
    assert set(source) == {x['id'] for x in data['tasks']}
    for t in data['tasks']:
        html_tasks += 1
        exp = tasks[(f'{ch}/{ls}', t['id'])]
        for key in ('check', 'setup', 'starter', 'solution'):
            if not (t[key] == source[t['id']][key] == exp[key]):
                diffs.append([ch, ls, t['id'], key])
        for key in ('title', 'level', 'hints', 'explain', 'parsons'):
            if t[key] != source[t['id']][key]:
                diffs.append([ch, ls, t['id'], key])

for lesson in built.values():
    for t in lesson['tasks']:
        nb.SHORT_IDS[t['id']] = nb.SHORT_IDS.get(t['id'], 0) + 1
ch = next(c for c in course['chapters'] if c['id'] == 'ch01')
expected_nb, expected_tasks, n = nb.make_chapter(ch, built, nb.uv_ref(course))
actual_nb = json.loads((ROOT / 'site/notebooks/ch01-practice.ipynb').read_text())
actual_tasks = json.loads((ROOT / 'site/notebooks/tasks/ch01.json').read_text())
assert expected_nb == actual_nb
assert expected_tasks == actual_tasks
for key, record in actual_tasks['tasks'].items():
    lesson, taskid = key.rsplit('/', 1)
    for field in ('check', 'setup', 'starter', 'solution'):
        assert record[field] == tasks[(lesson, taskid)][field], (key, field)

def normalize_versions(s):
    s = re.sub(r'(?<=\?v=)[0-9a-f]{10}', '<ASSET_VERSION>', s)
    return re.sub(r'(?<=data-v=")[0-9a-f]{10}(?=")', '<ASSET_VERSION>', s)

other = []
unexpected = []
changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
for path in changed:
    if re.match(r'site/ch(?:0[2-9]|1[0-5])/', path):
        before = subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT).decode()
        same = normalize_versions(before) == normalize_versions((ROOT / path).read_text())
        other.append({'path': path, 'only_asset_version': same})
        if not same:
            unexpected.append(path)
    if re.match(r'content/ch(?:0[2-9]|1[0-5])/', path):
        unexpected.append(path)

native = json.loads((OUT / 'core-native.json').read_text())
pyodide = json.loads((OUT / 'core-pyodide.json').read_text())
assert len(native) == len(pyodide) == 61
matrix = []
for i, (a, b) in enumerate(zip(native, pyodide), 1):
    for key in ('lesson', 'task', 'description', 'code', 'expected'):
        assert a[key] == b[key], (i, key)
    task = tasks[(a['lesson'], a['task'])]
    matrix.append({'n': i, **{k: a[k] for k in ('lesson', 'task', 'description', 'code', 'expected')},
                   'current_check_sha256': hashlib.sha256(task['check'].encode()).hexdigest(),
                   'native_actual': a['actual'], 'pyodide_actual': b['actual'],
                   'native_check': a['result'].get('check'), 'pyodide_check': b['result'].get('check')})
(OUT / 'core-matrix.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in matrix))
assert 'проверено: 344, проблем: 0' in (OUT / 'standard.log').read_text()
assert 'ch01 [solution]: задач 149, проблем 0' in (OUT / 'notebooks.log').read_text()
assert 'ch01 [starter]: задач 149, проблем 0' in (OUT / 'notebooks.log').read_text()
paths = sorted((ROOT / 'content/ch01').glob('*'))
paths += [ROOT / p for p in ('content/course.yaml', 'tools/build.py', 'tools/make_notebooks.py', 'tools/verify.mjs', 'tools/serve.py', 'site/assets/core.js', 'site/assets/lesson.js', 'site/assets/search.js', 'site/notebooks/dsc.py', 'site/notebooks/ch01-practice.ipynb', 'site/notebooks/tasks/ch01.json')]
paths += sorted((ROOT / 'tools/checks').glob('ch01*.py'))
paths += sorted((OUT / 'student/transfer').glob('*'))
paths += sorted((ROOT / 'site/ch01').glob('*.html'))
paths += [OUT / p for p in ('standard.log', 'notebooks.log', 'current-export-ch01.json', 'core-native.json', 'core-pyodide.json', 'core-matrix.jsonl')]
hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
journal = OUT / 'student/attempts.jsonl'
student_rows = [json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
expected = {
    '07-tables/cell', '07-tables/best-city', '08-dicts/top', '09b-style/long-line',
    '11-comprehensions/top-key', '11-comprehensions/lessonquiz', '12-errors/skip-bad',
    'exam-1/parse', '14-project/dedupe', '14-project/drinks', '14-project/report',
    '14-project/file', '14-project/lessonquiz', 'test/c2', 'test/c6',
}
last = {r['id']: r['passed'] for r in student_rows}
assert set(last) == expected and all(last.values())
assert all(r['id'] == '09b-style/long-line' for r in student_rows if not r['passed'])
assert not diffs and not unexpected
assert all(row['native_actual'] == row['expected'] == row['pyodide_actual'] for row in matrix)
save('verification.json', {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'base_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'algorithm': 'Read current source with build.load_course; compare every HTML task JSON to source and current export; create notebook objects in memory and compare whole JSON plus exported checks; normalize only 10-digit asset versions in other-chapter HTML versus HEAD. Does not build pages or execute earlier evidence again.',
    'export': {'source': 'tools/build.py --check --export', 'sha256': export_hash, 'chapter_copy': str((OUT / 'current-export-ch01.json').relative_to(ROOT)), 'chapter_records': len(chapter), 'kinds': dict(collections.Counter(x['kind'] for x in chapter))},
    'artifact_comparison': {'all_344_export_records_equal_to_current_source': True, 'html_tasks': html_tasks, 'differences': diffs, 'notebook_tasks': n, 'notebook_whole_json_equal': True, 'notebook_task_registry_equal': True, 'notebook_registry_checks_equal_to_export': True},
    'other_chapters': {'files': other, 'unexpected': unexpected},
    'retained_runs': {'standard': {'path': str((OUT / 'standard.log').relative_to(ROOT)), 'records': 344, 'problems': 0}, 'notebooks': {'path': str((OUT / 'notebooks.log').relative_to(ROOT)), 'solution': 149, 'starter': 149, 'problems': 0}, 'probes': {'matrix': str((OUT / 'core-matrix.jsonl').relative_to(ROOT)), 'per_environment': len(matrix), 'expected_matches_native': sum(x['native_actual'] == x['expected'] for x in matrix), 'expected_matches_pyodide': sum(x['pyodide_actual'] == x['expected'] for x in matrix), 'environment_agreement': sum(x['native_actual'] == x['pyodide_actual'] for x in matrix), 'scope': 'Retained supplied runs; current check hashes attached by lesson/task. This comparison itself does not rerun probes.'}},
    'student': {'journal': str(journal.relative_to(ROOT)), 'observed_rows': len(student_rows), 'observed_ids': sorted({r['id'] for r in student_rows if 'id' in r}), 'status': 'Accepted. Latest browser verdict per ID matches all 15 expected IDs.', 'code_submissions': sum('code' in r for r in student_rows), 'quiz_submissions': sum('choice' in r for r in student_rows), 'prescribed_or_deliberate_rejections': sum(not r['passed'] for r in student_rows), 'journal_sha256': sha(journal)},
    'sha256': hashes,
})
print(json.dumps({'html_tasks': html_tasks, 'diffs': diffs, 'notebook_tasks': n, 'other_pages': len(other), 'unexpected': unexpected, 'probes': len(matrix)}, ensure_ascii=False))
