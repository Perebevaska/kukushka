"""Сверка итогов курса из исходных заданий, первичных журналов и оценок всех глав.

Запуск из корня: .venv/bin/python docs/audit-2026-11-13/checks/course_totals.py
Можно передать номер последней закрытой главы для промежуточной сверки.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
import re
import sys
import yaml

base = Path(__file__).resolve().parents[1]
root = base.parents[1]
catalog = yaml.safe_load((root/'content/course.yaml').read_text())['chapters']
limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(catalog)
assert 1 <= limit <= len(catalog)
totals = Counter()
ratings = []
for ch in catalog[:limit]:
    code = ch['id']
    d = base/code
    rows = lambda f: [json.loads(line) for line in (d/f).read_text().splitlines() if line]
    student, browser = rows('student.jsonl'), rows('browser.jsonl')
    events = defaultdict(list)
    qs = {}
    for row in browser:
        if 'id' in row:
            events[row['lesson'],row['id']].append(row)
        else:
            key = row['lesson'],row['kind'],row['index']
            assert key not in qs, (code,key)
            qs[key] = row
    wanted, questions = set(), set()
    for lesson in (root/'content'/code).glob('*.md'):
        content = lesson.read_text()
        for task in re.findall(r'^## task:\s*([^|\s]+)',content,re.M):
            key=(lesson.stem,task)
            assert key not in wanted,(code,key)
            wanted.add(key)
        for kind in ('predict','quiz'):
            for i,_ in enumerate(re.finditer(r'^::: '+kind+r'\b',content,re.M),1):
                questions.add((lesson.stem,kind,i))
    assert set(events)==wanted and set(qs)==questions, code
    assert Counter((r['lesson'],r['id']) for r in student if 'id' in r)==Counter({k:len(v) for k,v in events.items()})
    assert {(r['lesson'],r['kind'],r['index'],r['choice']) for r in student if 'kind' in r}=={(*k,v['choice']) for k,v in qs.items()}
    assisted={ (r['lesson'],r['id']) for r in student if r.get('hint_level') or r.get('help_before') }
    passed={k for k,v in events.items() if v[-1]['passed']}
    stats = dict(tasks=len(events),attempts=sum(map(len,events.values())),first=sum(r[0]['passed'] for r in events.values()),passed=len(passed),independent=len(passed-assisted),questions=len(qs),correct=sum(r['passed'] for r in qs.values()))
    if code!='ch01':
        coverage=json.loads((d/'coverage.json').read_text())
        assert all(coverage[k]==v for k,v in stats.items()),code
        assert (d/'acceptance.md').is_file(), code
    numeric=[]
    for line in (d/'report.md').read_text().split('## Пути улучшения подачи')[0].splitlines():
        if line.startswith('|') and len(line.split('|'))>3:
            score=re.fullmatch(r'\s*\**([1-5])(?:/5)?\**\s*',line.split('|')[2])
            if score: numeric.append(int(score[1]))
    assert len(numeric)==5,(code,numeric)
    ratings.append(numeric)
    totals.update(stats)
    print(code, ' '.join(f'{k}={v}' for k,v in stats.items()),'оценки='+','.join(map(str,numeric)))
print(dict(totals))
print('Средние по критериям с равным весом глав:',[round(sum(column)/len(column),2) for column in zip(*ratings)])
