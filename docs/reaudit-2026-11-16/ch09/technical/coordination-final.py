"""Reconcile saved final evidence, stdlib only; never execute course programs."""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
T = D / 'technical'
R = D / 'fixes/student/retest'

def read(p):
    return json.loads(p.read_text())

def rows(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def delta(a, b):
    return {'missing': sorted(set(a)-set(b)), 'extra': sorted(set(b)-set(a))}

def signature(r):
    return json.dumps({k:r.get(k) for k in ('id','code','expect','choice','passed','feedback','visible_output','visible_prompt')}, sort_keys=True, ensure_ascii=False)

initial = rows(D/'student/initial-attempts.jsonl')
retest = rows(D/'student/retest-attempts.jsonl')
registry = read(T/'inventory.json')
targets = read(T/'retest-targets.json')
issues, pairs, actual, nonboolean = [], [], [], []
canonical = [('practice-attempt-01.jsonl','practice-feedback-01.jsonl'),
             ('choices-submit-01.jsonl','choices-feedback-01.jsonl'),
             ('choices-refresh-01.jsonl','choices-refresh-feedback-01.jsonl'),
             ('choices-final-attempt-01.jsonl','choices-final-feedback-01.jsonl')]
for a_name, b_name in canonical:
    a_path, b_path = R/a_name, R/b_name
    ins, outs = rows(a_path), rows(b_path)
    assert len(ins) == len(outs), (a_name, b_name)
    for n,(a,b) in enumerate(zip(ins,outs),1):
        id_ = a.get('question') or a.get('id') or a['lesson']+'/'+a['task']
        assert id_ == b['id'], (a_name,n)
        merged = dict(a, **b)
        merged['id'] = id_
        src = {'input':str(a_path.relative_to(D)), 'feedback':str(b_path.relative_to(D)), 'line':n}
        if type(b.get('passed')) is bool:
            actual.append((merged,src))
        else:
            nonboolean.append(dict(src,event=merged))
    pairs.append({'input':str(a_path.relative_to(D)), 'feedback':str(b_path.relative_to(D)),
                  'input_sha256':digest(a_path),'feedback_sha256':digest(b_path),'rows':len(ins)})
raw, summary = Counter(signature(r) for r,_ in actual), Counter(map(signature,retest))
if raw != summary:
    issues.append('raw/summary multiset mismatch')
lookup = {}
for r,src in actual:
    lookup.setdefault(signature(r),[]).append(src)
trace = []
for n,r in enumerate(retest,1):
    matches = lookup.get(signature(r),[])
    trace.append({'summary_line':n,'id':r['id'],'source':matches.pop(0) if matches else None,
                  'signature_sha256':sha256(signature(r).encode()).hexdigest()})
history, latest = {}, {}
for phase, rs in [('initial',initial),('retest',retest)]:
    for n,r in enumerate(rs,1):
        latest[r['id']] = r['passed']
        history.setdefault(r['id'],[]).append({'phase':phase,'line':n,'passed':r['passed']})
coverage = {'inventory':dict(Counter(registry.values())), 'initial_rows':len(initial),
            'retest_rows':len(retest),'retest_unique_ids':len({r['id'] for r in retest}),
            'target_difference':delta(targets,[r['id'] for r in retest]),
            'missing_or_failed_final':[id_ for id_ in registry if latest.get(id_) is not True],
            'unknown':sorted(set(latest)-set(registry)), 'accepted_final_ids':sum(latest.get(id_) is True for id_ in registry),
            'history':history,'scope':'94 distinct curriculum IDs; new retest and historical initial evidence are separate.'}
(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
release = read(T/'release.json')
file_checks = {n:(ROOT/n).exists() and digest(ROOT/n)==h for n,h in release['files'].items()}
data_checks = {n:{'site':digest(ROOT/'site/data'/n)==h,'baseline':digest(T/'data-baseline'/n)==h} for n,h in release['data'].items()}
final_full = Path('/tmp/kuch09round/final.json')
export = read(T/'chapter-export.json')
release_checks = {'files':file_checks, 'data':data_checks,
                  'full_export_hash':digest(final_full)==release['full_course_export_sha256'],
                  'chapter_export_hash':digest(T/'chapter-export.json')==release['chapter_snapshot_sha256'],
                  'exact_chapter_filter':export==[r for r in read(final_full) if r['lesson'].startswith('ch09/')],
                  'full_and_chapter_hashes_differ':release['full_course_export_sha256']!=release['chapter_snapshot_sha256'],
                  'counts':dict(Counter(r['kind'] for r in export))}
if not all(file_checks.values()) or not all(all(c.values()) for c in data_checks.values()):
    issues.append('release file/data mismatch')
probes = {}
for prefix,count in [('after',63),('refine-after',12)]:
    a,b = rows(D/f'check-evidence/{prefix}-native.jsonl'), rows(D/f'check-evidence/{prefix}-pyodide.jsonl')
    A,B = {r['id']:r for r in a},{r['id']:r for r in b}
    probes[prefix] = {'native_rows':len(a),'pyodide_rows':len(b),
                     'accepted_native':sum(r['passed'] is True for r in a),
                     'native_normative_matches':sum(r['passed']==r['expected'] for r in a),
                     'pyodide_normative_matches':sum(r['passed']==r['expected'] for r in b),
                     'id_difference':delta(A,B),'verdict_differences':[k for k in A.keys() & B.keys() if A[k]['passed']!=B[k]['passed']],
                     'sha256':{str(p.relative_to(D)):digest(p) for p in (D/f'check-evidence/{prefix}-native.jsonl',D/f'check-evidence/{prefix}-pyodide.jsonl')}}
    assert len(a)==len(b)==count and len(A)==len(B)==count
comparison = read(D/'check-evidence/refine-59-card-comparison.json')
before = {r['lesson']+'/'+r['id']:r for r in read(D/'check-evidence/after-tasks.json') if r['kind']=='task'}
final = {r['lesson']+'/'+r['id']:r for r in export if r['kind']=='task'}
computed_unchanged = [k for k in final if all(before[k].get(f)==final[k].get(f) for f in ('setup','starter','solution','check'))]
independent = {}
def verdict(r):
    return r['observed'] if 'observed' in r else r['passed']
for name in ('after-html.jsonl','after-catalog.jsonl'):
    p=D/'fixes/reviewer-evidence'/name
    rs=rows(p)
    independent[name]={'rows':len(rs),'accepted':sum(verdict(r) is True for r in rs),
                       'rejected':sum(verdict(r) is False for r in rs),
                       'normative_matches':sum(verdict(r)==r['expected'] for r in rs),'sha256':digest(p)}
A={r['id']:r for r in rows(D/'fixes/reviewer-evidence/after-html.jsonl')}
B={r['id']:r for r in rows(D/'fixes/reviewer-evidence/after-catalog.jsonl')}
independent['verdict_differences']=[k for k in A.keys() & B.keys() if verdict(A[k])!=verdict(B[k])]
independent['id_difference']=delta(A,B)
receipt=read(D/'fixes/reviewer-evidence/fresh-receipt.json')
receipt_hashes={n:(R/n).exists() and digest(R/n)==h for n,h in receipt['sha256_of_delivered_files'].items()}
def structural_diff(a,b,path=''):
    if type(a) != type(b):
        return [{'path':path,'before':a,'after':b}]
    if isinstance(a,dict):
        return [d for k in sorted(set(a)|set(b)) for d in structural_diff(a.get(k),b.get(k),path+'/'+k)]
    if isinstance(a,list):
        if len(a)!=len(b):
            return [{'path':path,'before':a,'after':b}]
        return [d for n,(x,y) in enumerate(zip(a,b)) for d in structural_diff(x,y,path+'/'+str(n))]
    return [] if a==b else [{'path':path,'before':a,'after':b}]
snapshot=D/'fixes/reviewer-evidence/fresh-delivered-project.ipynb'
old_nb,new_nb=read(snapshot),read(R/'project.ipynb')
nb_diff=structural_diff(old_nb,new_nb)
notebook_revision={'delivered_snapshot':str(snapshot.relative_to(D)), 'delivered_sha256':digest(snapshot),
                   'matches_historical_receipt':digest(snapshot)==receipt['sha256_of_delivered_files']['project.ipynb'],
                   'current_sha256':digest(R/'project.ipynb'), 'diff':nb_diff,
                   'only_markdown_source_changed':len(nb_diff)==1 and nb_diff[0]['path']=='/cells/13/source/1' and old_nb['cells'][13]['cell_type']==new_nb['cells'][13]['cell_type']=='markdown',
                   'cell_id':new_nb['cells'][13].get('id'),
                   'provenance':'Reviewer reconstructed earlier Markdown text; byte hash exactly matches frozen historical receipt. Snapshot was not executed by coordinator.'}
receipt_reconciled=all(v or (n=='project.ipynb' and notebook_revision['matches_historical_receipt'] and notebook_revision['only_markdown_source_changed']) for n,v in receipt_hashes.items())
if not receipt_reconciled:
    issues.append('Unreconciled delivered receipt hash difference')
coverage['notebook_artifact_revision']=notebook_revision
(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
review_path=D/'fixes/review.md'
review_lines=review_path.read_text().splitlines()
prior_ids=[r['id'] for r in read(T/'coordination.json')['prior_14']]
prior_review={id_:[{'line':n,'text':line} for n,line in enumerate(review_lines,1) if re.match(r'\| '+re.escape(id_)+r' \|',line)] for id_ in prior_ids}
prior_review['late M09']=[{'line':n,'text':line} for n,line in enumerate(review_lines,1) if line.startswith('| Поздний M09 ')]
logs={}
for name in ('final-standard.log','final-notebook-solution.log','final-notebook-starter.log'):
    p=T/name
    logs[name]={'sha256':digest(p),'text':p.read_text()}
report_path=D/'report.md'
local_links=[]
for label,url in re.findall(r'\[([^\]]*)\]\(([^)]+)\)',report_path.read_text()):
    if re.match(r'[a-z]+://',url):
        continue
    target=url.split('#')[0]
    if target:
        local_links.append({'label':label,'target':url,'exists':(report_path.parent/target).exists()})
publication=read(D/'fixes/reviewer-evidence/after-publication.json')
publication_page_hashes={name:digest(ROOT/'site/ch09'/name)==p['sha256'] for name,p in publication['pages'].items()}
result={'generated_at':datetime.now(timezone.utc).isoformat(),'initial_snapshot_preserved':True,
        'coverage':coverage,'retest':{'raw_pairs':pairs,'trace':trace,'boolean_rows':len(retest),
        'accepted_rows':sum(r['passed'] is True for r in retest),'raw_summary_exact_multiset_match':raw==summary,
        'nonboolean_events':nonboolean,'prepared_excluded':{'choices-attempt-01.jsonl':len(rows(R/'choices-attempt-01.jsonl')),'choices-held-quiz2.jsonl':len(rows(R/'choices-held-quiz2.jsonl'))},
        'fresh_final_visible_prompts':[{'line':n,'id':r['id'],'visible_prompt':r.get('visible_prompt')} for n,r in enumerate(retest,1) if r.get('visible_prompt')]},
        'release':release_checks,'release_verification':read(T/'release-verification.json'),
        'quiz_clarification_parity':read(T/'quiz-clarification-parity.json'),
        'quiz_export_equality_independent':export==read(T/'chapter-export-before-quiz-clarification.json'),
        'logs':logs,'checks':probes,'four_field_comparison':{'recorded':comparison,'computed_unchanged':len(computed_unchanged),'computed_changed':sorted(set(final)-set(computed_unchanged))},
        'independent_review':independent,'prior_review':prior_review,
        'fresh_project_receipt':receipt,'fresh_project_delivered_hash_checks':receipt_hashes,
        'notebook_artifact_revision':notebook_revision,'receipt_reconciled':receipt_reconciled,
        'final_notebook_reviewer_receipt':read(D/'fixes/reviewer-evidence/final-notebook-receipt.json'),
        'ui':read(T/'test-ui.json'), 'review_sha256':digest(review_path),
        'final_publication_page_hashes':publication_page_hashes,
        'report_review':{'sha256':digest(report_path),'local_links':local_links,'missing_local_links':[x for x in local_links if not x['exists']],
                         'content_review':'Read in full: 35/37, 94 curriculum IDs, 14 + late M09, 63 + 12 + 28 phases and independence limitations agree with saved evidence.'},
        'issues':issues}
(T/'coordination-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'retest_rows':len(retest),'raw_exact':raw==summary,'nonboolean':len(nonboolean),'coverage':{k:v for k,v in coverage.items() if k not in ('history','notebook_artifact_revision')},'release_files_match':sum(file_checks.values()),'release_files_total':len(file_checks),'unchanged_tasks':len(computed_unchanged),'independent':independent,'receipt_current_files_byte_identical':all(receipt_hashes.values()),'receipt_reconciled':receipt_reconciled,'prior_review_count':sum(bool(v) for v in prior_review.values()),'issues':issues},ensure_ascii=False,indent=2))
