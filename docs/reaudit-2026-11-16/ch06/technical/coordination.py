"""Independent frozen-cut reconciliation; never counts reviewer probes as student attempts."""
from pathlib import Path
import collections, datetime, hashlib, json, re
D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
def read(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def counter(rows):
    return collections.Counter((r['id'], r['passed'], r.get('feedback','')) for r in rows)
initial = read(D/'student/initial-attempts.jsonl')
retest = read(D/'student/retest-attempts.jsonl')
def signature(r):
    ident = r.get('id',r.get('question')) or r.get('lesson','')+'/'+r.get('task','')
    return (ident,r.get('code'),r.get('choice'),r.get('expect'))
raw_attempts=[]
for p in sorted((D/'student').glob('*.jsonl')):
    if 'feedback' in p.name or p.name in ('initial-attempts.jsonl','retest-attempts.jsonl') or p.name.startswith('retest'): continue
    raw_attempts.extend(r for r in read(p) if 'code' in r or 'choice' in r)
missing_raw = collections.Counter(map(signature,initial))-collections.Counter(map(signature,raw_attempts))
raw, notes, feedback_files = [], [], {}
for p in sorted((D/'student').glob('*feedback*.jsonl')):
    if p.name.startswith('retest'): continue
    feedback_files[str(p.relative_to(D))] = digest(p)
    for n,r in enumerate(read(p),1):
        if type(r.get('passed')) is bool: raw.append(r)
        else: notes.append({'file':str(p.relative_to(D)), 'line':n, **r})
release = json.loads((D/'technical/release.json').read_text())
export = json.loads((D/'technical/chapter-export.json').read_text())
source = sorted((ROOT/'content/ch06').glob('*.md'))
program = (ROOT/'content/course.yaml').read_text().split('  - id: ch06\n',1)[1].split('  - id: ch07\n',1)[0]
lessons = re.findall(r'- \{id: ([\w-]+),',program)
source_tasks = {(p.stem,t) for p in source for t in re.findall(r'^## task: ([\w-]+)\s*\|',p.read_text(),re.M)}
export_tasks = {(r['lesson'].split('/')[-1],r['id']) for r in export if r['kind']=='task'}
# Export id may be task-local or qualified; normalize from the actual format.
export_tasks = {(lesson,task.rsplit('/',1)[-1]) for lesson,task in export_tasks}
probes={}
for p in sorted((D/'check-evidence').glob('*revised.jsonl')):
    rows=[r for r in read(p) if re.fullmatch('C[0-9]+',str(r.get('id','')))]; probes[p.name]={'count':len(rows),'ids':[r['id'] for r in rows], 'unexpected':[r['id'] for r in rows if r.get('expected')!=r.get('observed')]}
result={
 'cut_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'chapter 6 only; before final two student retests and refreshed release',
 'program_lessons':lessons,'program_minutes':sum(map(int,re.findall(r'minutes: (\d+)',program))),
 'source_markdown_count':len(source),'source_task_count':len(source_tasks),
 'export_counts':dict(collections.Counter(r['kind'] for r in export)),
 'export_task_missing':sorted(source_tasks-export_tasks),'export_task_unknown':sorted(export_tasks-source_tasks),
 'raw_initial_feedback_count':len(raw),'raw_initial_feedback_equal':counter(raw)==counter(initial),
 'raw_initial_attempt_count':len(raw_attempts),'initial_attempts_missing_raw':[{'id':k[0],'count':v} for k,v in missing_raw.items()],
 'retest_raw_attempts_equal':collections.Counter(map(signature,read(D/'student/retest-32-attempt1.jsonl')))==collections.Counter(map(signature,retest)),
 'nonverdict_feedback':notes,'initial_submissions':len(initial),'initial_distinct_ids':len({r['id'] for r in initial}),
 'initial_true':sum(r['passed'] is True for r in initial),'initial_false':sum(r['passed'] is False for r in initial),
 'retest_submissions':len(retest),'retest_distinct_ids':len({r['id'] for r in retest}),
 'retest_true':sum(r['passed'] is True for r in retest),
 'retest_raw_feedback_equal':counter(read(D/'student/retest-32-feedback1.jsonl'))==counter(retest),
 'release_mismatches':{group:[name for name,h in release[group].items() if not (p:=ROOT/('site/data/'+name if group=='data' else name)).exists() or digest(p)!=h] for group in ('files','data')},
 'chapter_export_hash_matches_release':digest(D/'technical/chapter-export.json')==release['chapter_snapshot_sha256'],
 'probe_revised':probes,
 'cut_hashes':{str(p.relative_to(ROOT)):digest(p) for p in source+[D/'student/initial-attempts.jsonl',D/'student/retest-attempts.jsonl',D/'technical/release.json',D/'coverage.json']},
 'raw_feedback_hashes':feedback_files,
}
(D/'technical/coordination.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('cut_hashes','raw_feedback_hashes','probe_revised','nonverdict_feedback')},ensure_ascii=False,indent=2))
