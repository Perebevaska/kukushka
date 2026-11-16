"""Summarize verdicts and assert that the independent submission bytes still match."""
import hashlib
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
phase = sys.argv[1]
programs = here/'programs.jsonl'
sha = hashlib.sha256(programs.read_bytes()).hexdigest()
assert sha in (here/'expectations.md').read_text()

def read(filename):
    return {r['id']: r for r in map(json.loads, (here/filename).read_text().splitlines())}

probes = read('programs.jsonl')
results = {}
observed = {}
for engine in ['native', 'pyodide']:
    observed[engine] = read(f'{phase}-{engine}.jsonl')
    assert set(observed[engine]) == set(probes)
    fp, fn = [], []
    for k, row in observed[engine].items():
        expected = probes[k]['expected_'+phase]
        if row['passed'] and not expected:
            fp.append(k)
        elif not row['passed'] and expected:
            fn.append(k)
    results[engine] = dict(total=len(probes), matched=len(probes)-len(fp)-len(fn), false_accepts=fp, false_rejects=fn)

summary = dict(phase=phase, sha256=sha, results=results, engine_agreement=sum(observed['native'][k]['passed']==observed['pyodide'][k]['passed'] for k in probes))
(here/f'{phase}-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, ensure_ascii=False))
