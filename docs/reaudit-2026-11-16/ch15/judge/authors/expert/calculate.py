from pathlib import Path
import csv
from decimal import Decimal as D
import hashlib
import json

base = Path(__file__).resolve().parents[2]
for name, digest in json.loads((base / 'input-sha256.json').read_text()).items():
    assert hashlib.sha256((base / name).read_bytes()).hexdigest() == digest
with (base / 'shared-input.csv').open() as f:
    raw = list(csv.DictReader(f))
pool = {r['client_id']: (r['city'], D(r['revenue_90']) / 3, D(r['revenue_trend']), D(r['p'])) for r in raw}
assert len(pool) == len(raw) == 965

def value(i, s, p):
    revenue = pool[i][1]
    return p*s*D('.35')*12*revenue - 1500 - D('.2')*revenue

def ranked(s):
    gain = {i: value(i, s, row[3]) for i, row in pool.items()}
    return sorted((i for i in gain if gain[i] > 0), key=lambda i: (-gain[i], i))[:3]

strengths = list(map(D, ['.3', '.5', '.7']))
trend = sorted(pool, key=lambda i: (pool[i][2], i))[:3]
fixed = ranked(D('.5'))
menus = [(s, trend, fixed, ranked(s)) for s in strengths]
observed = {r['client_id']: D(r['churn']) for r in raw}
for i in trend + fixed:
    city, rev, slope, p = pool[i]
    print(i, city, f'trend={slope:.5f} p={p:.9f} expected={value(i,D(".5"),p):.2f} churn={observed[i]}')
for s, old, locked, new in menus:
    for name, ids in [('trend',old),('fixed',locked),('rerank',new)]:
        model = sum(value(i, s, pool[i][3]) for i in ids)
        scenario = sum(value(i,s,observed[i]) for i in ids)
        print(s,name,','.join(ids),f'{model:.2f}',f'{scenario:.2f}')
for name, ids in [('fixed',fixed),('trend',trend)]:
    cost = sum(1500 + D('.2')*pool[i][1] for i in ids)
    denom = sum(D('4.2')*pool[i][1]*pool[i][3] for i in ids)
    histdenom = sum(D('4.2')*pool[i][1]*observed[i] for i in ids)
    print(name,f'cost={cost:.2f} model_den={denom:.2f} model_s={cost/denom:.6f}',f'hist_s={cost/histdenom:.6f}' if histdenom else 'no observed churn')
