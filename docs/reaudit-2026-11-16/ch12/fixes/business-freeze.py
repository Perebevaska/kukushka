"""Check both completed freezes and the RMSE populations in the manager's letter."""
import csv
import hashlib
import json
import math
from pathlib import Path

here = Path(__file__).resolve().parent
original = here.parent / 'student'
repeat = here / 'student/retest'
results = {}
for name, directory in [('original', original), ('retest', repeat)]:
    manifest = json.loads((directory / 'SHA256SUMS.json').read_text())
    for filename, expected in manifest.items():
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        assert actual == expected, filename
    results[name] = len(manifest)
with (repeat / 'native-august-predictions.csv').open() as stream:
    rows = list(csv.DictReader(stream))
for name, sample in [('all', rows), ('working', [r for r in rows if r['work'] == 'True'])]:
    scores = {}
    for plan in ('model', 'baseline', 'quantile'):
        squared = sum((float(r[plan]) - int(r['fact'])) ** 2 for r in sample)
        scores[plan] = math.sqrt(squared / len(sample))
    results[name] = dict(hours=len(sample), rmse=scores)
print(json.dumps(results, indent=2))
