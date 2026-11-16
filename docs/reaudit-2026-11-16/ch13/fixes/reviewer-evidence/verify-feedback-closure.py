"""The two unchanged submissions isolate the feedback change in the published parser."""
import json
from pathlib import Path

d = Path(__file__).resolve().parent
full = json.loads((d/'combined-after.json').read_bytes())
cases = json.loads((d/'feedback-closure-cases.json').read_bytes())
assert cases == [r for r in full if r['id'] in ('R01','R26')]
msg = ('None здесь означает отсутствие текста от SDK. Верните негодную запись: '
       'sentiment=None, topic=None, ok=False; допустима и последовательность этих трёх значений.')
for runtime in ('native','pyodide'):
    meta = json.loads((d/f'feedback-closure-{runtime}-meta.json').read_bytes())
    assert meta['export'] == '681571ca57c423abd8148c43d07607ab8a9f0f3c3b6b8e7975a54b95e0f4b8d3'
    raw = [json.loads(line) for line in (d/f'feedback-closure-{runtime}.jsonl').read_text().splitlines()]
    assert [r['id'] for r in raw] == ['R01','R26'] and all(r['ok'] for r in raw)
    assert raw[0]['check'] == dict(passed=False, msg=msg)
    assert raw[1]['check'] == dict(passed=True, msg='')
    print(runtime, 'R01 correct SDK feedback; R26 passed')
