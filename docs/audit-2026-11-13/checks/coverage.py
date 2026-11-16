"""Сверка первичных журналов с программой. Запуск из корня: python3 …/coverage.py ch02 /tmp/ku-audit"""
from collections import Counter, defaultdict
from pathlib import Path
import json
import re
import sys

chapter, work_root = sys.argv[1:]
folder = Path(work_root, chapter)
out = Path(__file__).resolve().parents[1] / chapter
def read(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
def write(name, data):
    (out / name).write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in data))

order = (folder / 'student/order.txt').read_text().splitlines()
export = [t for t in json.loads((folder.parent/'tasks.json').read_text()) if t['lesson'].startswith(chapter + '/')]
tasks = {(t['lesson'].split('/')[1], t['id']) for t in export if t['kind']=='task'}
expected_questions = set()
for lesson in order:
    md = Path('content', chapter, lesson+'.md').read_text()
    for kind in ('quiz', 'predict'):
        for i,_ in enumerate(re.finditer(r'^::: ' + kind + r'\b', md, re.M), 1):
            expected_questions.add((lesson, kind, i))
attempts = read(folder/'submissions.jsonl')
answers = read(folder/'answers.jsonl')
runtime = read(folder/'checks.jsonl')
browser = [r for lesson in order for p in [folder/('browser-'+lesson+'.json')] if p.exists() for r in json.loads(p.read_text())]
sub = lambda r:(r['lesson'],r['id'],r['code'])
qkey = lambda r:(r['lesson'],r['kind'],r['index'])
bt = [r for r in browser if 'id' in r]
bq = [r for r in browser if 'kind' in r]
assert set((r['lesson'],r['id']) for r in attempts)==tasks, 'Неполный охват задач'
assert Counter(map(sub,bt)) == Counter(map(sub,attempts)), 'Браузер: не все попытки'
assert Counter(map(sub,runtime)) == Counter(map(sub,attempts)), 'Среда: не все попытки'
assert set(map(qkey,answers))==expected_questions, 'Неполный охват вопросов'
assert Counter((*qkey(r),r['choice']) for r in answers)==Counter((*qkey(r),r['choice']) for r in bq), 'Браузер: не все вопросы'
assert len(answers)==len(expected_questions), 'Первая попытка не выделена'
route_pages={p.stem for p in Path('content',chapter).glob('*.md')}
assert set(order)==route_pages, ('Не все страницы главы учтены', set(order)^route_pages)
helps = defaultdict(list)
if (folder/'help.jsonl').exists():
    for r in read(folder/'help.jsonl'): helps[r['lesson'],r['id']].append(r)
run_index = {r['row']:r for r in runtime}
by_key = defaultdict(list)
for r in bt: by_key[r['lesson'],r['id']].append(r)
seq = Counter()
ledger = []
for i,a in enumerate(attempts):
    k=(a['lesson'],a['id'])
    evidence = by_key[k][seq[k]]
    assert a['code']==evidence['code']==run_index[i]['code']
    seq[k]+=1
    ledger.append(dict(**a, attempt=seq[k], runtime_passed=run_index[i]['passed'],
                       runtime_feedback=run_index[i]['msg'][:1800], browser_passed=evidence['passed'],
                       help_before=[h['help'] for h in helps.get(k,[]) if h.get('after_attempt',0)<seq[k]]))
write('student.jsonl',ledger+answers)
for r in bt:
    r['message']=r['message'].split('Что это значит:')[0].split('Следующая задача')[0].strip()[:1800]
write('browser.jsonl',browser)
if helps:
    write('help.jsonl',read(folder/'help.jsonl'))
unresolved = [f'{l}/{i}' for (l,i),v in by_key.items() if not v[-1]['passed']]
assisted = [f'{l}/{i}' for l,i in helps if by_key[l,i][-1]['passed']]
stats = dict(tasks=len(tasks), attempts=len(attempts), passed=len(tasks)-len(unresolved),
  first=sum(v[0]['passed'] for v in by_key.values()), unanswered=unresolved, assisted=assisted,
  independent=len(tasks)-len(unresolved)-len(assisted), questions=len(bq), correct=sum(r['passed'] for r in bq),
  test=[sum(r['passed'] for r in bq if r['lesson']=='test'),sum(1 for r in bq if r['lesson']=='test')],
  export=dict(Counter(t['kind'] for t in export)), browser_runtime_disagreements=sum(r['runtime_passed']!=r['browser_passed'] for r in ledger),
  by_lesson={l:dict(tasks=sum(k[0]==l for k in tasks), first=sum(k[0]==l and v[0]['passed'] for k,v in by_key.items()),questions=sum(r['lesson']==l for r in bq)) for l in order})
(out/'coverage.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print({k:v for k,v in stats.items() if k!='by_lesson'})
