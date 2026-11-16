"""Rebuild ch04 coverage from course sources and actual immutable submission logs.
Run from any directory: python3 /absolute/path/to/aggregate_coverage.py [--export FILE]
--export validates and stores a chapter-only snapshot; later runs need no /tmp.
Own journal mirrors initial submissions and is validated, never counted twice.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
ROOT = HERE.parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'{path}:{n}: incomplete/invalid JSON; rerun after writer finishes') from exc
        row['_source'] = str(path.relative_to(ROOT))
        row['_line'] = n
        rows.append(row)
    return rows


def row_id(row):
    return row.get('id') or row.get('question') or f"{row['lesson']}/{row['task']}"


def passed(row):
    return row.get('passed', row.get('verdict', {}).get('passed'))


def stats(rows):
    return {'submissions': len(rows), 'distinct_ids': len({row_id(r) for r in rows}),
            'passed': sum(passed(r) is True for r in rows),
            'failed': sum(passed(r) is False for r in rows),
            'without_verdict': sum(passed(r) is None for r in rows),
            'with_explicit_expect': sum(bool(r.get('expect')) for r in rows),
            'missing_expect_ids': sorted({row_id(r) for r in rows if not r.get('expect')}),
            'note': 'expect means a saved pre-submission expectation, never inferred from reflection/feedback'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path)
    args = parser.parse_args()
    course_text = (ROOT / 'content/course.yaml').read_text()
    section = course_text.split('  - id: ch04\n', 1)[1].split('\n  - id: ', 1)[0]
    route = [(m.group(1), 'core: true' in m.group(0)) for m in re.finditer(r'^      - \{id: ([\w-]+),[^\n]+', section, re.M)]
    inventory = {}
    for lesson, core in route + [('test', True)]:
        path = ROOT / 'content/ch04' / f'{lesson}.md'
        text = path.read_text()
        for match in re.finditer(r'^## task: ([\w-]+)\s*\|[^\n]+\|\s*(\w+)\s*$', text, re.M):
            ident = lesson + '/' + match.group(1)
            inventory[ident] = {'kind': 'program', 'level': match.group(2),
                                'route': 'main' if core else 'deepening'}
        for kind in ('predict', 'quiz'):
            for n, _ in enumerate(re.finditer(r'^::: '+kind+r'\b', text, re.M), 1):
                inventory[f'{lesson}/{kind}/{n}'] = {
                    'kind': 'final_quiz' if lesson == 'test' else kind,
                    'route': 'main' if core else 'deepening'}
    snapshot = HERE / 'chapter-export.json'
    if args.export:
        records = [r for r in json.loads(args.export.read_text()) if r['lesson'].startswith('ch04/')]
        snapshot.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    export_info = {'snapshot': str(snapshot.relative_to(ROOT)), 'present': snapshot.exists()}
    if snapshot.exists():
        records = json.loads(snapshot.read_text())
        exported = {r['lesson'].split('/', 1)[1] + '/' + (r['id'] if r['kind'] == 'task' else 'predict/' + r['id'][1:])
                    for r in records if r['kind'] in ('task', 'predict')}
        expected = {i for i, v in inventory.items() if v['kind'] in ('program', 'predict')}
        export_info.update(sha256=digest(snapshot), counts=dict(Counter(r['kind'] for r in records)),
                           missing_ids=sorted(expected-exported), unexpected_ids=sorted(exported-expected))
        assert exported == expected, export_info
    initial = read_rows(AUDIT / 'student/initial-attempts.jsonl')
    own = read_rows(AUDIT / 'student/attempts-own.jsonl')
    retest = read_rows(AUDIT / 'student/retest-attempts.jsonl')
    mirror_errors = []
    for n, (a, b) in enumerate(zip(initial, own), 1):
        if (row_id(a), a.get('code'), a.get('choice'), passed(a)) != (row_id(b), b.get('code'), b.get('choice'), passed(b)):
            mirror_errors.append(n)
    targets = json.loads((HERE / 'retest-targets.json').read_text())
    grouped = defaultdict(list)
    for row in initial + retest:
        grouped[row_id(row)].append(row)
    details = {}
    for ident, entry in inventory.items():
        rows = grouped.get(ident, [])
        latest = rows[-1] if rows else None
        details[ident] = dict(entry, submissions=len(rows),
            initial_submissions=sum(row_id(r) == ident for r in initial),
            retest_submissions=sum(row_id(r) == ident for r in retest),
            latest_passed=passed(latest) if latest else None,
            ever_passed=any(passed(r) is True for r in rows),
            assistance='not_machine_classified; see student/walkthrough.md',
            history=[{'file': r['_source'], 'line': r['_line'], 'passed': passed(r),
                      'expect_logged': bool(r.get('expect')), 'at': r.get('at')} for r in rows])
    retest_ids = {row_id(r) for r in retest}
    latest_retest = {row_id(r): passed(r) for r in retest}
    counts = Counter(v['kind'] for v in inventory.values())
    assert counts == {'program':112, 'predict':16, 'quiz':15, 'final_quiz':15}, counts
    source_files = [ROOT/'content/course.yaml'] + sorted((ROOT/'content/ch04').glob('*.md'))
    source_files += [AUDIT/'student'/name for name in ('initial-attempts.jsonl','attempts-own.jsonl','retest-attempts.jsonl')]
    result = {'schema': 1, 'chapter': 'ch04', 'route': [i for i, _ in route],
        'inventory_counts': dict(counts), 'total_distinct_expected':len(inventory),
        'route_counts': {route:dict(Counter(v['kind'] for v in inventory.values() if v['route']==route)) for route in ('main','deepening')},
        'sources_sha256':{str(p.relative_to(ROOT)):digest(p) for p in source_files},
        'export_validation':export_info,
        'initial':stats(initial), 'own_mirror':dict(stats(own), same_length=len(initial)==len(own), mismatched_line_numbers=mirror_errors),
        'retest':stats(retest),
        'combined':stats(initial+retest),
        'missing_initial_ids':sorted(set(inventory)-{row_id(r) for r in initial}),
        'unknown_submission_ids':sorted(set(grouped)-set(inventory)),
        'latest_failed_or_unsubmitted_ids':[i for i,v in details.items() if v['latest_passed'] is not True],
        'retest_targets':{'count':len(targets),'distinct_count':len(set(targets)),
            'unknown_ids':sorted(set(targets)-set(inventory)), 'submitted_ids':sorted(set(targets)&retest_ids),
            'not_yet_submitted_ids':sorted(set(targets)-retest_ids),
            'latest_failed_ids':sorted(i for i in targets if i in latest_retest and latest_retest[i] is not True),
            'extra_submitted_ids':sorted(retest_ids-set(targets))},
        'ids':details,
        'limits':['Own journal is a mirror, not additional submissions.',
                  'Initial pass predates edits; only recorded retests evidence personal resubmission.',
                  'Passing is the actual system verdict, not proof of conceptual correctness.',
                  'No expectations, hints, duration or authorship are fabricated from feedback.']}
    (AUDIT/'coverage.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('inventory_counts','initial','retest','retest_targets','latest_failed_or_unsubmitted_ids')},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
