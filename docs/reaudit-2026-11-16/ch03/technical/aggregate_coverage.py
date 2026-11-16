#!/usr/bin/env python3
"""Reconcile chapter 3 evidence; never infer browser submissions from authored code.

Run from any directory. Only technical/coverage.json is written. Re-run after the
student finishes: inputs, their SHA-256 and the pending retest IDs are refreshed.
"""
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

CHAPTER = Path(__file__).resolve().parents[1]
ROOT = CHAPTER.parents[2]


def read_jsonl(path):
    if not path.exists():
        return []
    return [dict(json.loads(line), _line=i) for i, line in
            enumerate(path.read_text().splitlines(), 1) if line.strip()]


def key(row):
    return row.get('id') or row.get('question') or f"{row['lesson']}/{row['task']}"


def category(identifier):
    if identifier.startswith('test/'):
        return 'final_quiz'
    if '/predict/' in identifier:
        return 'predict'
    if '/quiz/' in identifier:
        return 'lesson_quiz'
    return 'task'


def summarize(ids, rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    submitted = set(grouped) & set(ids)
    passed = {i for i in submitted if grouped[i][-1].get('passed') is True}
    return dict(expected=len(ids), submitted_unique=len(submitted),
                passed_unique=len(passed), missing=sorted(set(ids)-submitted),
                not_passed=sorted(submitted-passed),
                verdict_events=sum(type(r.get('passed')) is bool for r in rows
                                   if key(r) in set(ids)))


baseline = json.loads((CHAPTER/'technical/baseline.json').read_text())
expected = set(baseline['expected_ids'])
lessons = baseline['lessons']
initial = read_jsonl(CHAPTER/'student/initial-attempts.jsonl')
authored = read_jsonl(CHAPTER/'student/attempts.jsonl')
browser = read_jsonl(CHAPTER/'student/browser-journal.jsonl')
retest = read_jsonl(CHAPTER/'student/retest-attempts.jsonl')
targets = json.loads((CHAPTER/'technical/retest-targets.json').read_text())
errors = []
levels = {}
current_ids = set()
source_counts = {}
for lesson in lessons+['test']:
    text = (ROOT/f'content/ch03/{lesson}.md').read_text()
    tasks = re.findall(r'^## task: ([^|\s]+)\s*\|[^\n]*\|\s*(\w+)\s*$', text, re.M)
    for identifier, level in tasks:
        levels[f'{lesson}/{identifier}'] = level
        current_ids.add(f'{lesson}/{identifier}')
    # Question IDs are positional in visible blocks, not inferred from answers.
    for kind in ('predict', 'quiz'):
        n = len(re.findall(r'^:::\s+'+kind+r'(?:\s|$)', text, re.M))
        current_ids.update(f'{lesson}/{kind}/{i}' for i in range(1, n+1))
    source_counts[lesson] = {'tasks': len(tasks)}

if current_ids != expected:
    errors.append({'scope': 'source_vs_baseline', 'missing': sorted(expected-current_ids),
                   'extra': sorted(current_ids-expected)})

authored_by_id = defaultdict(list)
browser_by_id = defaultdict(list)
for row in authored:
    authored_by_id[key(row)].append(row)
for row in browser:
    browser_by_id[key(row)].append(row)

schema = Counter()
for phase, rows in [('initial', initial), ('retest', retest)]:
    for row in rows:
        identifier = key(row)
        issues = []
        if identifier not in expected:
            issues.append('unknown_id')
        if type(row.get('passed')) is not bool:
            issues.append('non_boolean_verdict')
        if not isinstance(row.get('feedback'), str) or not row['feedback'].strip():
            issues.append('missing_feedback')
        if not isinstance(row.get('expect'), str) or not row['expect'].strip():
            issues.append('missing_expectation')
        try:
            datetime.fromisoformat(row['at'].replace('Z', '+00:00'))
        except (ValueError, KeyError, TypeError):
            issues.append('invalid_timestamp')
        if category(identifier) == 'task':
            schema[f'{phase}_programs'] += 1
            if f"{row.get('lesson')}/{row.get('task')}" != identifier:
                issues.append('lesson_task_id_disagree')
            try:
                if not row.get('code', '').strip():
                    raise SyntaxError('empty')
                ast.parse(row['code'])
            except (SyntaxError, TypeError):
                issues.append('missing_or_unparseable_code')
        else:
            schema[f'{phase}_choices'] += 1
            if row.get('question') != identifier or type(row.get('choice')) is not int or not 1 <= row['choice'] <= 4:
                issues.append('invalid_choice_or_question_id')
        if phase == 'initial':
            payload = 'code' if category(identifier) == 'task' else 'choice'
            if not any(r.get(payload) == row.get(payload) for r in authored_by_id[identifier]):
                issues.append('no_matching_authored_payload')
            if not any(r.get('passed') is row.get('passed') and r.get('feedback') == row.get('feedback')
                       for r in browser_by_id[identifier]):
                issues.append('no_matching_browser_verdict')
        if issues:
            errors.append(dict(phase=phase, line=row['_line'], id=identifier, issues=issues))

duplicates = {phase: sorted(i for i, n in Counter(key(r) for r in rows).items() if n > 1)
              for phase, rows in [('initial', initial), ('retest', retest)]}
if duplicates['initial']:
    errors.append({'scope': 'initial_duplicate_ids', 'ids': duplicates['initial']})

latest = {key(r): r for r in initial}
latest.update({key(r): r for r in retest})
export = json.loads((CHAPTER/'check-evidence/tasks-after.json').read_text())
export = [r for r in export if r['lesson'].startswith('ch03/')]
export_tasks = {r['lesson'].removeprefix('ch03/')+'/'+r['id'] for r in export if r['kind']=='task'}
if export_tasks != set(levels):
    errors.append({'scope': 'export_tasks_vs_current_sources',
                   'missing': sorted(set(levels)-export_tasks), 'extra': sorted(export_tasks-set(levels))})

inputs = [CHAPTER/'technical/baseline.json', CHAPTER/'technical/retest-targets.json',
          CHAPTER/'check-evidence/tasks-after.json', *(CHAPTER/'student'/f for f in
          ('initial-attempts.jsonl', 'attempts.jsonl', 'browser-journal.jsonl', 'retest-attempts.jsonl')),
          *(ROOT/f'content/ch03/{l}.md' for l in lessons+['intro', 'test'])]
inputs.extend(CHAPTER/'fixes/student'/name for name in (
    'check-notebook.txt', 'check-notebook-selected.txt',
    'control-examples.json', 'transfer-answers.md'))
result = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'chapter': 'ch03', 'baseline_head': baseline['head'],
    'snapshot_status': 'complete_retest' if not summarize(targets, retest)['missing'] else 'retest_in_progress',
    'scope': {'lesson_materials': len(lessons), 'intro': 1, 'final_test': 1,
              'total_markdown_materials': len(lessons)+2, 'expected_unique': len(expected),
              'source_ids_unique': len(current_ids),
              'export_records': len(export), 'export_kinds': dict(Counter(r['kind'] for r in export))},
    'initial': summarize(expected, initial),
    'initial_by_category': {c: summarize([i for i in expected if category(i)==c], initial)
                            for c in ('task', 'predict', 'lesson_quiz', 'final_quiz')},
    'initial_by_task_level': {l: summarize([i for i in levels if levels[i]==l], initial)
                             for l in ('warmup', 'base', 'plus', 'star')},
    'initial_by_lesson': {l: summarize([i for i in expected if i.split('/')[0]==l], initial)
                          for l in lessons+['test']},
    'retest': summarize(targets, retest), 'retest_events': len(retest),
    'retest_extra_ids': sorted({key(r) for r in retest}-set(targets)),
    'latest_observed': summarize(expected, list(latest.values())),
    'browser': {'events': len(browser), 'verdict_events': sum(type(r.get('passed')) is bool for r in browser),
                'already_answered': sum(bool(r.get('already_answered')) for r in browser),
                'browser_errors': sum('browserError' in r for r in browser),
                'verdict_unique': len({key(r) for r in browser if type(r.get('passed')) is bool}),
                'authored_events': len(authored),
                'join_rule': 'Match id plus payload, and id plus verdict/feedback; do not zip files by line number.'},
    'schema': dict(schema), 'duplicate_ids': duplicates, 'validation_errors': errors,
    'assistance': {'source': 'student/walkthrough.md', 'hints_requested_reported': 0,
                   'note': 'Theory/starter use is reported; not inferred from a pass. No machine-readable help field.'},
    'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in inputs if p.exists()},
}
destination = CHAPTER/'technical/coverage.json'
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'output': str(destination), 'status': result['snapshot_status'],
                  'initial': result['initial'], 'retest': result['retest'],
                  'validation_errors': errors}, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
