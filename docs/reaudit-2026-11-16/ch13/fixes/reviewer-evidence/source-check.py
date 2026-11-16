"""Reconcile original keys, fixed labels, derived scores and quote IDs with the stdlib."""
import csv
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

out = Path(__file__).resolve().parent
chapter = out.parent.parent
data = chapter / 'technical/data-baseline'


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def keyed(path):
    rows = read(path)
    keyed_rows = {row['review_id']: row for row in rows}
    assert len(rows) == len(keyed_rows)
    return keyed_rows


new = keyed(data/'reviews_new.csv')
gold = keyed(data/'reviews_new_gold.csv')
scored = keyed(chapter/'student/own-scored.csv')
assert len(new) == len(gold) == len(scored) == 4800
assert new.keys() == gold.keys() == scored.keys()
groups = defaultdict(Counter)
months = defaultdict(list)
weeks = defaultdict(list)
for id_, row in new.items():
    pred = scored[id_]
    assert all(row[k] == pred[k] for k in row)
    assert gold[id_]['label_source'] == 'synthetic_kind_neg_or_mixed'
    signal = int(pred['neg'])
    assert signal == (float(pred['p_neg']) >= .5)
    day = date.fromisoformat(row['date'])
    shop = row['shop_id']
    months[shop,day.month].append(signal)
    weeks[shop,day - timedelta(days=day.weekday())].append(signal)
    if shop == 'KZN-2':
        period = 'после' if row['date'] >= '2026-10-05' else 'до'
        g = groups[period]
        complaint = int(gold[id_]['complaint'])
        g.update(n=1, complaints=complaint, signals=signal,
                 tp=complaint*signal, fp=(1-complaint)*signal)
        g['signal_delivery'] += signal*(pred['topic']=='доставка')
mean = lambda a: sum(a)/len(a)
shops = sorted({sh for sh,m in months})
focus = max(shops, key=lambda sh:mean(months[sh,10])-mean(months[sh,9]))
dates = sorted({w for sh,w in weeks if sh == focus})
a,b = max(zip(dates,dates[1:]), key=lambda pair:mean(weeks[focus,pair[1]])-mean(weeks[focus,pair[0]]))
pool = [r for r in scored.values() if r['shop_id']==focus and r['date'] >= b.isoformat() and r['neg']=='1' and r['topic']=='доставка']
top = sorted(pool,key=lambda r:-float(r['p_neg']))[:5]
quotes = read(chapter/'student/own-quotes.csv')
assert [(r['review_id'],r['text']) for r in quotes] == [(r['review_id'],r['text']) for r in top]
old = keyed(data/'reviews_text.csv')
old_gold = keyed(data/'review_gold.csv')
all_votes = defaultdict(dict)
for row in read(data/'review_labels.csv'):
    all_votes[row['review_id']][row['annotator']] = row['label']
agree = {k:v['аня'] for k,v in all_votes.items() if v['аня']==v['борис']}
result = dict(focus=focus,change_week=b.isoformat(),week_counts=[len(weeks[focus,x]) for x in (a,b)],
              week_signals=[sum(weeks[focus,x]) for x in (a,b)], periods=groups,
              quotes=[r['review_id'] for r in top],n_agree=len(agree),
              shared_error=sorted(k for k,v in agree.items() if v!=old[k]['topic']),
              gold_equals_topic=sum(r['label']==old[k]['topic'] for k,r in old_gold.items()),
              vika_correct=sum(r['label']==all_votes[k]['вика'] for k,r in old_gold.items()))
print(json.dumps(result,indent=2,ensure_ascii=False))
