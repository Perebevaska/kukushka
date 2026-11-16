"""Initial chapter 9 reconciliation. Stdlib only; no course execution or mutation."""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
T, S = D / 'technical', D / 'student'

def read(p):
    return json.loads(p.read_text())

def rows(p):
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def delta(a, b):
    return {'missing': sorted(set(a) - set(b)), 'extra': sorted(set(b) - set(a))}

def ident(r):
    return r.get('id') or r.get('question') or r['lesson'] + '/' + r['task']

def signature(r):
    # Keep the actual types of visible_output (list versus str) and choice.
    return json.dumps({k: r.get(k) for k in
                       ('id', 'code', 'expect', 'choice', 'passed', 'feedback', 'visible_output')},
                      sort_keys=True, ensure_ascii=False)

base = read(T / 'baseline.json')
registry = read(T / 'inventory.json')
current = {}
for p in sorted((ROOT / 'content/ch09').glob('*.md')):
    txt = p.read_text()
    for task in re.findall(r'^## task: ([\w-]+)\s*\|', txt, re.M):
        key = p.stem + '/' + task
        assert key not in current, key
        current[key] = 'task'
    for kind in ('predict', 'quiz'):
        for n, _ in enumerate(re.finditer(r'^::: ' + kind + r'\b', txt, re.M), 1):
            current[f'{p.stem}/{kind}/{n}'] = 'final_quiz' if p.stem == 'test' else kind
export = read(T / 'baseline-export.json')
export_ids = [r['lesson'].removeprefix('ch09/') + '/' +
              ('predict/' + str(int(r['id'][1:])) if r['kind'] == 'predict' else r['id'])
              for r in export if r['kind'] != 'cell']
issues, pairs, merged, hints = [], [], [], []
for inp in sorted(S.glob('*/*.jsonl')):
    if inp.name.startswith('attempt-'):
        fb = inp.with_name(inp.name.replace('attempt-', 'feedback-', 1))
    elif inp.name.startswith('choices-') and not inp.name.startswith('choices-feedback-'):
        fb = inp.with_name(inp.name.replace('choices-', 'choices-feedback-', 1))
    elif inp.name.startswith('hint-') and not inp.name.startswith('hint-feedback-'):
        fb = inp.with_name(inp.name.replace('hint-', 'hint-feedback-', 1))
    else:
        continue
    ins, outs = rows(inp), rows(fb) if fb.exists() else []
    checks = []
    for n in range(max(len(ins), len(outs))):
        a, b = (ins[n] if n < len(ins) else None), (outs[n] if n < len(outs) else None)
        ok = a is not None and b is not None and ident(a) == b.get('id')
        checks.append({'line': n+1, 'id': ident(a) if a else None, 'matches': ok})
        if not ok:
            issues.append(f'{inp.relative_to(D)}:{n+1}: input/feedback mismatch')
            continue
        m = dict(a, **b)
        m['id'] = ident(a)
        source = {'input': str(inp.relative_to(D)), 'feedback': str(fb.relative_to(D)), 'line': n+1}
        if type(m.get('passed')) is bool:
            merged.append((m, source))
        else:
            hints.append(dict(source, event=m))
    pairs.append({'input': str(inp.relative_to(D)), 'feedback': str(fb.relative_to(D)),
                  'input_sha256': digest(inp), 'feedback_sha256': digest(fb) if fb.exists() else None,
                  'input_rows': len(ins), 'feedback_rows': len(outs), 'checks': checks})
initial = rows(S / 'initial-attempts.jsonl')
raw_counts, summary_counts = Counter(signature(r) for r, _ in merged), Counter(map(signature, initial))
exact = raw_counts == summary_counts
if not exact:
    issues.append('raw/summary multiset mismatch')
lookup = {}
for r, src in merged:
    lookup.setdefault(signature(r), []).append(src)
trace = []
for n, r in enumerate(initial, 1):
    matches = lookup.get(signature(r), [])
    trace.append({'summary_line': n, 'id': r['id'], 'passed': r.get('passed'),
                  'source': matches.pop(0) if matches else None,
                  'signature_sha256': sha256(signature(r).encode()).hexdigest()})
latest = {r['id']: r for r in initial}
first = {r['id']: r for r in reversed(initial)}
failures = [dict(summary_line=n, **r) for n, r in enumerate(initial, 1) if r.get('passed') is False]
prior = []
for name, pattern in [('student.md', r'S09-\d+'), ('expert.md', r'E9-\d+'), ('methodist.md', r'M09-\d+')]:
    path = ROOT / 'docs/audit-2026-11-13/ch09' / name
    found = set()
    for n, line in enumerate(path.read_text().splitlines(), 1):
        for id_ in re.findall(pattern, line):
            if id_ not in found and ('**'+id_ in line):
                found.add(id_)
                prior.append({'id': id_, 'source': str(path.relative_to(ROOT)), 'line': n, 'full_text': line})
historical_path = ROOT / 'docs/course-improvements/reaudit/fixes/technical-results.jsonl'
historical = [dict(line=n, **r) for n, r in enumerate(rows(historical_path), 1) if r['task'].startswith('ch09/')]
result = {
    'phase': 'initial snapshot; final retest and release reconciled in follow-up',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'baseline_head': base['head'], 'baseline_counts': base['counts'],
    'baseline_export_sha256': digest(T/'baseline-export.json'),
    'baseline_export_hash_is_full_export_hash': digest(T/'baseline-export.json') == base['export_sha256'],
    'full_export': {'path': '/tmp/kuch09round/course.json',
                    'sha256': digest(Path('/tmp/kuch09round/course.json')),
                    'matches_baseline_full_hash': digest(Path('/tmp/kuch09round/course.json')) == base['export_sha256'],
                    'chapter_exact_filter': export == [r for r in read(Path('/tmp/kuch09round/course.json')) if r['lesson'].startswith('ch09/')]},
    'inventory_counts': dict(Counter(registry.values())),
    'registry_current_difference': delta(registry, current),
    'export_counts': dict(Counter(r['kind'] for r in export)),
    'export_task_predict_difference': delta([k for k,v in registry.items() if v in ('task','predict')], export_ids),
    'initial': {'rows': len(initial), 'boolean_rows': sum(type(r.get('passed')) is bool for r in initial),
                'unique_ids': len(latest), 'accepted_ids': sum(r['passed'] is True for r in latest.values()),
                'first_try_accepted_ids': sum(r['passed'] is True for r in first.values()),
                'failures': failures, 'inventory_difference': delta(registry, latest),
                'raw_summary_exact_multiset_match': exact,
                'missing_raw_rows': sum((summary_counts - raw_counts).values()),
                'extra_raw_rows': sum((raw_counts-summary_counts).values()),
                'expect_nonempty': sum(bool(r.get('expect')) for r in initial)},
    'raw_pairs': pairs, 'trace': trace,
    'help': {'instrumented_hint_events': hints, 'instrumented_assisted_ids': sorted({h['event']['id'] for h in hints}),
             'summary_has_help_field': any('help' in r for r in initial),
             'limitation': 'One hint is evidenced positively. No solution reveal is the student declaration; absence of an event does not prove absence of all UI use. Theory use is not counted as hint assistance.'},
    'prior_14': prior, 'historical_ch09_program_rows': historical,
    'late_M09': {'id': 'M09', 'source': 'docs/course-improvements/reaudit/review.md', 'line': 54,
                 'acceptance_source': 'docs/course-improvements/reaudit/fixes/review/ch09.md', 'line': 5},
    'source_hashes_now': {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/'content/ch09').glob('*.md'))},
    'baseline_source_hashes': base['sources'],
    'release': 'Final publication pending by workflow; absence is not a finding.',
    'issues': issues,
}
(T / 'coordination.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('inventory_counts','export_counts','registry_current_difference','export_task_predict_difference','issues')}, ensure_ascii=False, indent=2))
print(json.dumps({'raw_pairs': len(pairs), 'matched_rows': len(merged), 'hints': len(hints), 'exact_summary':exact,
                  'prior_ids':len(prior), 'historical_rows': len(historical), 'initial_rows':len(initial)}, indent=2))
