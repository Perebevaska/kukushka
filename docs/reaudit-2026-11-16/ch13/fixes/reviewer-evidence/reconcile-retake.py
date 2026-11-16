"""Verify the student's frozen retake, the raw grades, the shared join, and all five quotes."""
import csv
import hashlib
import json
from pathlib import Path
from collections import defaultdict

d = Path(__file__).resolve().parent
root = d.parent.parent
s = root/'fixes/student/retest'
files = (s/'SHA256SUMS').read_text().splitlines()
for line in files:
    digest, name = line.split('  ',1)
    assert hashlib.sha256((s/name).read_bytes()).hexdigest()==digest
attempts = [json.loads(line) for f in sorted(s.glob('*feedback.jsonl')) for line in f.read_text().splitlines()]
per_id = defaultdict(list)
for a in attempts:
    per_id[a['id']].append(a['passed'])
assert list(k for k,v in per_id.items() if v != [True]) == ['05-project/weekly']
assert per_id['05-project/weekly'] == [False,True]
read = lambda f:list(csv.DictReader(f.open()))
data = root/'technical/data-baseline'
source = {r['review_id']:r for r in read(data/'reviews_new.csv')}
gold = {r['review_id']:r for r in read(data/'reviews_new_gold.csv')}
scored = {r['review_id']:r for r in read(s/'own-scored.csv')}
assert set(source)==set(scored)==set(gold) and len(scored)==4800
periods = defaultdict(lambda: [0,0,0,0])
for k,row in source.items():
    p = scored[k]
    assert all(p[col]==val for col,val in row.items())
    assert int(p['neg'])==(float(p['p_neg'])>=.5)
    if row['shop_id']=='KZN-2':
        block = periods['после' if row['date']>='2026-10-05' else 'до']
        for i,num in enumerate([1,int(p['neg']),int(p['neg'])*(p['topic']=='доставка'),int(gold[k]['complaint'])]):
            block[i] += num
assert periods == {'до':[440,162,39,161], 'после':[372,222,129,222]}
quotes = read(s/'own-quotes.csv')
top = sorted([r for r in scored.values() if r['shop_id']=='KZN-2' and r['date']>='2026-10-05' and r['neg']=='1' and r['topic']=='доставка'],key=lambda r:-float(r['p_neg']))[:5]
letter=(s/'letter-retest.md').read_text()
assert [(r['review_id'],r['text']) for r in quotes] == [(r['review_id'],r['text']) for r in top]
assert all(r['review_id'] in letter for r in quotes)
cells = [c for c in json.loads((s/'project-retest.ipynb').read_bytes())['cells'] if c['cell_type']=='code']
assert [c['execution_count'] for c in cells]==list(range(1,7)) and all(c['outputs'] for c in cells)
assert any('image/png' in o.get('data',{}) for c in cells for o in c['outputs'])
print(json.dumps(dict(verified_files=len(files),raw_grades=len(attempts),unique=len(per_id),
  passed=sum(a['passed'] for a in attempts),first_pass=sum(v[0] for v in per_id.values()), cells=6,
  review_ids=len(scored),period_counts_in_order=['all','signals','delivery_signals','synthetic_complaints'],
  periods=periods,quotes=[r['review_id'] for r in quotes]),ensure_ascii=False,indent=2))
