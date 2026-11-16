"""Read-only reconciliation of own frozen prose, metrics and per-key predictions/labels."""
from pathlib import Path
import csv,json,hashlib
from fractions import Fraction
W=Path('/private/tmp/kuch14round/student-retest/own-previous');D=Path(__file__).resolve().parent
P=W/'holdout-predictions/predictions.csv';J=W/'holdout-evaluation/joined.csv';M=W/'holdout-evaluation/metrics.json'
with P.open() as f:pred=list(csv.DictReader(f))
with J.open() as f:joined=list(csv.DictReader(f))
key=lambda r:(r['time'],int(r['slot']))
pr={key(r):int(r['pred']) for r in pred}
# Labels are own frozen joined.csv true column, not another agent's material.
y={key(r):int(r['true']) for r in joined}
assert len(pr)==len(pred)==len(y)==len(joined)==732
assert set(pr)==set(y)
assert all(pr[key(r)]==int(r['pred']) for r in joined)
correct=sum(pr[k]==y[k] for k in pr)
count=len(pr);accuracy=correct/count;metric=json.loads(M.read_text())
assert accuracy==metric['accuracy']
wrong_texts={}
for n in ['review.md','walkthrough-after.md']:
 p=W/'holdout-evaluation'/n
 wrong_texts[n]=[line for line in p.read_text().splitlines() if '677' in line or 'accuracy' in line.lower()]
out=dict(correct=correct,total=count,incorrect=count-correct,accuracy=accuracy,percent=accuracy*100,exact_fraction=str(Fraction(correct,count)),metrics_accuracy=metric['accuracy'],matches_metrics=True,previous_text_numerator=677,previous_text_fraction=677/count,previous_text_excerpts=wrong_texts,source_labels='own-previous/holdout-evaluation/joined.csv: true projected by(time,slot)',hashes={str(p.relative_to(W)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,J,M,W/'holdout-evaluation/review.md',W/'holdout-evaluation/walkthrough-after.md']})
(D/'holdout-reconciliation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
