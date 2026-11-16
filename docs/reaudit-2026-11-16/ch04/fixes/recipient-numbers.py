"""Recalculate both delivery files from individual records, independently of the notebook."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
from math import ceil, floor
from pathlib import Path
from statistics import mean, median

base = Path(__file__).resolve().parents[1]

def quantile(seq, probability):
    ordered = sorted(seq)
    index = (len(seq) - 1) * probability
    return ordered[floor(index)] + (ordered[ceil(index)] - ordered[floor(index)]) * (index % 1)

def counts(rows):
    return [sum(r['late'] for r in rows), len(rows)]

def stats(path):
    with path.open() as io:
        raw = list(csv.DictReader(io))
    ok, invalid = [], Counter()
    for r in raw:
        if not r['actual_min']:
            invalid['missing'] += 1
            continue
        t = float(r['actual_min'])
        if not 1 <= t <= 299:
            invalid[str(t)] += 1
            continue
        promise = int(r['promised_min'])
        ok.append(dict(t=t,promise=promise,late=t>promise,delay=t-promise, courier=r['courier'],
                       km=float(r['distance_km']), items=int(r['items']), shop=r['shop_id'],
                       day=datetime.fromisoformat(r['created']), weather=r['weather'],rating=float(r['rating']) if r['rating'] else None))
    groups = {k:[r for r in ok if r['courier']==k] for k in sorted({r['courier'] for r in ok})}
    winner = max(groups, key=lambda k:mean(r['late'] for r in groups[k]))
    scenarios = {}
    for p in [30,45]:
        rows = [r for r in groups[winner] if r['promise']==p]
        p80 = quantile([r['t'] for r in rows],.8)
        threshold = ceil(p80/5)*5
        scenarios[p] = dict(stats=counts(rows), others=counts([r for r in ok if r['promise']==p and r['courier']!=winner]),
                            p80=p80, candidate=threshold, meet=sum(r['t']<=threshold for r in rows))
    findings={}
    for condition, select in [('items>=5',lambda r:r['items']>=5),('distance_km<=2',lambda r:r['km']<=2)]:
        findings[condition] = {key:[counts([r for r in rows if select(r)]),counts([r for r in rows if not select(r)])]
                               for key,rows in {'all':ok,**groups}.items()}
    weeks=defaultdict(list)
    for r in ok:
        d=r['day'].date()
        weeks[d+timedelta(days=6-d.weekday())].append(r)
    ratings={}
    for k, rows in [('on time',[r for r in ok if not r['late']]),('late',[r for r in ok if r['late']]),('delay>10',[r for r in ok if r['delay']>10])]:
        values=[r['rating'] for r in rows if r['rating'] is not None]
        ratings[k]=dict(n=len(rows),rated=len(values),low=sum(v<=3 for v in values),mean=mean(values))
    edges=list(range(-40,41,5))
    histogram=[sum(left <= r['delay'] < right or right==40 and r['delay']==40 for r in ok) for left,right in zip(edges,edges[1:])]
    promises={k:{deadline:counts([r for r in rows if r['promise']==deadline]) for deadline in [30,45,60]} for k,rows in groups.items()}
    cut=[-60,-10,0,10,20,60]
    rating_bins=[]
    for left,right in zip(cut,cut[1:]):
        values=[r['rating'] for r in ok if left<r['delay']<=right and r['rating'] is not None]
        rating_bins.append([len(values),mean(values)])
    return dict(raw=len(raw),invalid=dict(invalid),late=counts(ok),group={k:counts(v) for k,v in groups.items()},
                histogram=histogram,promises=promises,rating_bins=rating_bins,
                leader=winner,scenarios=scenarios,findings=findings,ratings=ratings,median_actual=median(r['t'] for r in ok),
                weeks={str(k):[sum(r['late'] for r in weeks[k]),sum(r['weather']=='снег' for r in weeks[k]),len(weeks[k])] for k in sorted(weeks)[1:-1]})
if __name__=='__main__':
    print(json.dumps({f.name:stats(f) for f in sorted((base/'fixes/student/data').glob('*.csv'))},ensure_ascii=False,indent=2))
