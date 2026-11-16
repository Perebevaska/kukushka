import hashlib
import json
from pathlib import Path

d = Path(__file__).resolve().parent
read = lambda f: json.loads((d/f).read_bytes())
lines = lambda f: [json.loads(row) for row in (d/f).read_text().splitlines()]
code = read('combined-after.json')
assert code[:25] == read('cases-before.json') and code[25:] == read('extra-after.json')
expect = {r['id']:r['expected_current'] for r in read('expectations-after.json')}
assert len(expect) == len(code) == 33
result = {}
for runtime in ['native','pyodide']:
    raw = lines('after-'+runtime+'.jsonl')
    metadata = read('after-'+runtime+'-meta.json')
    assert metadata['export']=='81332cd15b12605f8a1b78bf6e72ab9ee25dcc62ab3463a28d9e379e382cff86'
    assert metadata['harness']=='1e7024f6e6767b70810efc17c52322d88e6eaa3977369d4cae81b79581071af8'
    assert metadata['cases']==hashlib.sha256((d/'combined-after.json').read_bytes()).hexdigest()
    assert [r['id'] for r in raw] == list(expect)
    assert all(r['ok'] and r.get('error') is None and expect[r['id']]==r['check']['passed'] for r in raw)
    result[runtime] = dict(matched=len(raw), passed=sum(r['check']['passed'] for r in raw),
                           rejected=sum(not r['check']['passed'] for r in raw),
                           migrated=[r['id'] for r in raw[:25] if r['check']['passed'] != r['expected']])
print(json.dumps(result,indent=2)+'\n',end='')
