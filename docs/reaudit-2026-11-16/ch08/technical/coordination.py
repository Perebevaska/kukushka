"""Read-only reconciliation; writes only coordination.json. No course execution."""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
T = D / 'technical'
S = D / 'student'
ORIGINAL = Path('/private/tmp/kuch08round/original/content/ch08')
def read(path):
    return json.loads(path.read_text())
def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
def digest(path):
    return sha256(path.read_bytes()).hexdigest()
def inventory(folder):
    result = {}
    for p in sorted(folder.glob('*.md')):
        txt = p.read_text()
        for task in re.findall(r'^## task: ([\w-]+)\s*\|', txt, re.M):
            key = f'{p.stem}/{task}'
            assert key not in result, key
            result[key] = 'task'
        for kind in ('predict', 'quiz'):
            for n, _ in enumerate(re.finditer(r'^::: ' + kind + r'\b', txt, re.M), 1):
                result[f'{p.stem}/{kind}/{n}'] = 'final_quiz' if p.stem == 'test' else kind
    return result

def input_id(row):
    return row.get('question') or row.get('id') or row['lesson'] + '/' + row['task']
def difference(a, b):
    return {'missing': sorted(set(a)-set(b)), 'extra': sorted(set(b)-set(a))}
base = read(T/'baseline.json')
current = inventory(ROOT/'content/ch08')
original = inventory(ORIGINAL) if ORIGINAL.exists() else None
registry = read(T/'inventory.json')
registry = {k: ('final_quiz' if k.startswith('test/quiz/') else v) for k,v in registry.items()}
export = read(T/'baseline-export.json')
export_ids = [r['lesson'].removeprefix('ch08/') + '/' + ('predict/' + str(int(r['id'][1:])) if r['kind'] == 'predict' else str(r['id'])) for r in export if r['kind'] != 'cell']
base_inventory = original or registry
issues = []
pairs = []
matched = []
for inp in sorted((S/'attempts').glob('*.jsonl')):
    if 'feedback' in inp.name:
        continue
    fb = inp.with_name(inp.stem + '-feedback.jsonl')
    ins = lines(inp)
    outs = lines(fb) if fb.exists() else []
    checks = []
    for n in range(max(len(ins), len(outs))):
        a = ins[n] if n < len(ins) else None
        b = outs[n] if n < len(outs) else None
        ok = a is not None and b is not None and input_id(a) == b.get('id')
        checks.append({'line': n+1, 'id': input_id(a) if a else None, 'feedback_id': b.get('id') if b else None, 'matches': ok})
        if ok:
            matched.append({'id': input_id(a), 'payload': a, 'feedback': b, 'input': str(inp.relative_to(D)), 'line': n+1})
        else:
            issues.append(f'{inp.name}:{n+1}: input/feedback mismatch')
    pairs.append({'input': str(inp.relative_to(D)), 'feedback': str(fb.relative_to(D)), 'input_sha256':digest(inp), 'feedback_sha256':digest(fb) if fb.exists() else None, 'input_rows':len(ins), 'feedback_rows':len(outs), 'checks':checks})
initial = lines(S/'initial-attempts.jsonl')
# Match multiset, preserving repeated ID attempts and their actual code/choice/expect/feedback.
def signature(r):
    return json.dumps({k:v for k,v in r.items() if k not in ('at','source')}, ensure_ascii=False, sort_keys=True)
raw_rows = []
for m in matched:
    raw_rows.append(dict(m['payload'], **m['feedback']))
raw_count = Counter(map(signature, raw_rows))
summary_count = Counter(map(signature, initial))
summary_match = raw_count == summary_count
if not summary_match:
    issues.append('raw input + feedback multiset differs from initial summary')
latest = {}
history = {}
for n,r in enumerate(initial,1):
    latest[r['id']] = r['passed']
    history.setdefault(r['id'],[]).append({'phase':'initial','line':n,'passed':r['passed']})
retest_path = S/'retest-attempts.jsonl'
retest = lines(retest_path) if retest_path.exists() else []
for n,r in enumerate(retest,1):
    latest[r['id']] = r['passed']
    history.setdefault(r['id'],[]).append({'phase':'retest','line':n,'passed':r['passed']})
target_path = T/'retest-targets.json'
targets = read(target_path) if target_path.exists() else []
if isinstance(targets,dict):
    targets = targets.get('ids', targets.get('targets', []))
ids = {r['id'] for r in initial}
failures = [{'line':n,'id':r['id'],'feedback':r.get('feedback'),'visible_output':r.get('visible_output')} for n,r in enumerate(initial,1) if r['passed'] is False]
generic = [{'input':m['input'],'line':m['line'],'id':m['id'],'expect':m['payload'].get('expect')} for m in matched if re.match(r'Код вычислит .* по формуле и данным условия; проверка примет нужные переменные\.|Выбран ответ \d+ по изученному объяснению и собственному расчёту\.', m['payload'].get('expect',''))]
for key, val in [('baseline_registry', difference(base_inventory,registry)), ('current_inventory',difference(base_inventory,current)), ('initial_inventory',difference(base_inventory,ids)), ('export_task_predict',difference([k for k,v in base_inventory.items() if v in ('task','predict')],export_ids))]:
    if val['missing'] or val['extra']:
        issues.append(key + ' ID set mismatch')
result = {
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'scope':'Chapter 8 only; no execution or student contact; historical code is not counted as a fresh attempt.',
 'baseline_head':base['head'], 'baseline_note':base['note'],
 'baseline_source_hashes_match_snapshot':{name: digest(ORIGINAL/Path(name).name)==h for name,h in base['sources'].items()} if ORIGINAL.exists() else None,
 'baseline_export_sha256_match': digest(T/'baseline-export.json')==base['export_sha256'],
 'current_source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'content/ch08').glob('*.md'))},
 'baseline_counts':dict(Counter(base_inventory.values())), 'current_counts':dict(Counter(current.values())),
 'baseline_inventory':base_inventory,
 'baseline_registry_difference':difference(base_inventory,registry),
 'current_inventory_difference':difference(base_inventory,current),
 'export_counts':dict(Counter(r['kind'] for r in export)),
 'export_task_predict_difference':difference([k for k,v in base_inventory.items() if v in ('task','predict')],export_ids),
 'export_duplicate_task_predict_ids':[k for k,v in Counter(export_ids).items() if v>1],
 'initial':{'rows':len(initial),'unique_ids':len(ids),'passed_rows':sum(r['passed'] is True for r in initial),'failed_rows':len(failures),'latest_accepted_ids':sum(latest0['passed'] is True for latest0 in {r['id']:r for r in initial}.values()),'inventory_difference':difference(base_inventory,ids),'raw_summary_exact_multiset_match':summary_match,'raw_summary_missing_rows':sum((raw_count-summary_count).values()),'raw_summary_extra_rows':sum((summary_count-raw_count).values()),'failures':failures},
 'raw_pairs':pairs,'generic_expectations':generic,
 'traceback_visible_output':[{'id':r['id'],'line':n} for n,r in enumerate(initial,1) if 'Traceback' in str(r.get('visible_output',''))],
 'hint_and_solution_evidence':{'validation':read(S/'validation.json'),'limitation':'0 hints/reveals are a student declaration; submission schema has no click event ledger. Blank visible_output is preserved, not evidence that stdout was never available.'},
 'retest':{'present':retest_path.exists(),'rows':len(retest),'unique_ids':len({r['id'] for r in retest}),'targets_file_present':target_path.exists(),'targets':targets,'missing_targets':sorted(set(targets)-{r['id'] for r in retest}),'latest_failed':[k for k,r in {r['id']:r for r in retest}.items() if r['passed'] is not True]},
 'combined_missing_or_failed':[k for k in base_inventory if latest.get(k) is not True], 'history':history,
 'release':{'present':(T/'release.json').exists(), 'recorded_source_hashes_match_current': {name: digest(ROOT/name)==h for name,h in read(T/'release.json').get('files',{}).items() if name.startswith('content/ch08/')} if (T/'release.json').exists() else None,'note':'Absent before final build is pending, not an error; revised/full export alone does not establish final release.'},
 'issues':issues,
}
# Final evidence is reconciled independently of initial-phase files.
retest_pairs = []
retest_raw = []
for inp in sorted((D/'fixes/student/retest/attempts').glob('*.jsonl')):
    if 'feedback' in inp.name:
        continue
    fb = inp.with_name(inp.stem + '-feedback.jsonl')
    ins, outs = lines(inp), lines(fb) if fb.exists() else []
    checks = []
    for n in range(max(len(ins), len(outs))):
        a = ins[n] if n < len(ins) else None
        b = outs[n] if n < len(outs) else None
        ok = a is not None and b is not None and input_id(a) == b.get('id')
        checks.append({'line':n+1,'id':input_id(a) if a else None,'feedback_id':b.get('id') if b else None,'matches':ok})
        if ok:
            retest_raw.append(dict(a, **b))
        else:
            issues.append(f'retest {inp.name}:{n+1}: input/feedback mismatch')
    retest_pairs.append({'input':str(inp.relative_to(D)),'feedback':str(fb.relative_to(D)),'input_sha256':digest(inp),'feedback_sha256':digest(fb) if fb.exists() else None,'input_rows':len(ins),'feedback_rows':len(outs),'checks':checks})
retest_exact = Counter(map(signature,retest_raw)) == Counter(map(signature,retest))
if not retest_exact:
    issues.append('retest raw/summary mismatch')
result['retest'].update({'raw_pairs':retest_pairs,'raw_summary_exact_multiset_match':retest_exact,'passed_rows':sum(r['passed'] is True for r in retest),'failed_rows':sum(r['passed'] is False for r in retest),'target_difference':difference(targets,[r['id'] for r in retest]),'first_attempt_passed_ids':sum(r['passed'] is True for r in {r['id']:r for r in reversed(retest)}.values())})
release_path=T/'release.json'
if release_path.exists():
    release=read(release_path)
    file_checks={name:{'exists':(ROOT/name).exists(),'matches':(ROOT/name).exists() and digest(ROOT/name)==h} for name,h in release['files'].items()}
    data_checks={name:{'exists':(ROOT/'site/data'/name).exists(),'matches':(ROOT/'site/data'/name).exists() and digest(ROOT/'site/data'/name)==h,'baseline_matches':(T/'data-baseline'/name).exists() and digest(T/'data-baseline'/name)==h} for name,h in release['data'].items()}
    full=Path('/tmp/kuch08round/final.json')
    chapter=T/'chapter-export.json'
    full_rows=read(full) if full.exists() else []
    chapter_rows=read(chapter) if chapter.exists() else []
    filtered=[r for r in full_rows if r['lesson'].startswith('ch08/')]
    result['release'].update({'files_count':len(file_checks),'file_checks':file_checks,'data_count':len(data_checks),'data_checks':data_checks,'full_course_export_path':str(full),'full_course_export_sha256':digest(full) if full.exists() else None,'full_course_export_matches':full.exists() and digest(full)==release['full_course_export_sha256'],'chapter_export_sha256':digest(chapter) if chapter.exists() else None,'chapter_export_matches':chapter.exists() and digest(chapter)==release['chapter_snapshot_sha256'],'full_and_chapter_hashes_distinct':release['full_course_export_sha256']!=release['chapter_snapshot_sha256'],'chapter_export_is_exact_full_filter':chapter_rows==filtered,'chapter_export_counts':dict(Counter(r['kind'] for r in chapter_rows))})
    for name,check in {**file_checks,**data_checks}.items():
        if not check['matches']:
            issues.append('release mismatch: '+name)
    for key in ('full_course_export_matches','chapter_export_matches','full_and_chapter_hashes_distinct','chapter_export_is_exact_full_filter'):
        if not result['release'][key]:
            issues.append('release '+key+' failed')
    # Confirm final export retains all task/predict identities after editing.
    final_ids=[r['lesson'].removeprefix('ch08/')+'/'+('predict/'+str(int(r['id'][1:])) if r['kind']=='predict' else str(r['id'])) for r in chapter_rows if r['kind']!='cell']
    result['release']['final_export_task_predict_difference']=difference([k for k,v in current.items() if v in ('task','predict')],final_ids)
# Audit local Markdown link destinations (anchors recorded, existence checked).
report=D/'report.md'
link_checks=[]
for label,url in re.findall(r'\[([^\]]*)\]\(([^)]+)\)',report.read_text()):
    if re.match(r'[a-z]+://',url):
        continue
    target=url.split('#')[0]
    if not target:
        continue
    path=report.parent/target
    link_checks.append({'label':label,'target':url,'exists':path.exists()})
result['report_local_links']=link_checks
result['report_missing_local_links']=[r for r in link_checks if not r['exists']]
result['test_ui_evidence']=read(T/'test-ui.json') if (T/'test-ui.json').exists() else None
result['independent_reviewer_probes']={}
for name in ('after-html.jsonl','after-catalog.jsonl'):
    path=D/'fixes/independent'/name
    rows=lines(path)
    result['independent_reviewer_probes'][name]={'rows':len(rows),'expected_matches_observed':sum(r['expected']==r['observed'] for r in rows),'sha256':digest(path)}
result['final_notebooks']={}
for name in ('sites-project.ipynb','final-project.ipynb'):
    notebook=read(S/name)
    cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    result['final_notebooks'][name]={'code_cells':len(cells),'execution_counts':[c.get('execution_count') for c in cells],'error_outputs':sum(o.get('output_type')=='error' for c in cells for o in c.get('outputs',[]))}
result['state']='final_mechanical_reconciliation' if retest and not issues and not result['combined_missing_or_failed'] and not result['retest']['missing_targets'] else 'pending_or_mismatch'
(T/'coordination.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'generated_at':result['generated_at'],'state':result['state'],'issues':issues,'initial_rows':len(initial),'initial_ids':len(ids),'initial_raw_exact':summary_match,'generic_expectations':len(generic),'retest_rows':len(retest),'retest_ids':result['retest']['unique_ids'],'retest_raw_exact':retest_exact,'release_files':result['release'].get('files_count'),'release_data':result['release'].get('data_count'),'missing_report_links':result['report_missing_local_links']},ensure_ascii=False,indent=2))
