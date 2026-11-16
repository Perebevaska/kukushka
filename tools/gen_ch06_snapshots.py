"""Dated synthetic snapshots for chapter 6, without changing the legacy feature schema."""
import csv
from pathlib import Path
import numpy as np


def write_snapshots(directory):
    directory=Path(directory)
    with (directory/'guests_churn.csv').open() as stream:
        reader=csv.DictReader(stream); rows=list(reader); columns=reader.fieldnames
    with (directory/'guests_churn_dates.csv').open('w') as stream:
        writer=csv.writer(stream)
        writer.writerow(['guest_id','snapshot_date','target_start','target_end_exclusive','target_available_at','card_blocked_available_at'])
        writer.writerows((r['guest_id'],'2026-10-01','2026-10-01','2026-11-30','2026-11-30','2026-11-30') for r in rows)
    # A separate synthetic candidate pool uses historical feature profiles.
    # Distinct IDs avoid implying an event history shared with the labelled cohort.
    # No churned/card_blocked values are read.
    rng=np.random.default_rng(61201)
    features=[c for c in columns if c not in ('churned','card_blocked')]
    with (directory/'guests_current.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['snapshot_date']+features, lineterminator='\n'); writer.writeheader()
        for candidate_id, row in enumerate(rows, 30001):
            r={c:row[c] for c in features}; r['snapshot_date']='2026-12-01'
            r['guest_id']=f'G-{candidate_id}'
            r['tenure_months']=int(r['tenure_months'])+2
            visits=max(0,int(rng.poisson(max(0.3,float(r['visits_90d'])))))
            r['visits_90d']=visits
            r['days_since_last']=int(rng.integers(91,200)) if not visits else min(90,int(rng.exponential(max(2,75/(visits+1)))))
            r['avg_check']='' if not visits else int(max(120,float(r['avg_check'] or 330)+rng.normal(0,25)))
            r['delivery_share']=float(r['delivery_share']) if visits else 0
            r['promo_used']=min(visits,int(r['promo_used']))
            r['complaints']=int(rng.random()<0.08)
            writer.writerow(r)


if __name__=='__main__':
    write_snapshots(Path(__file__).resolve().parents[1]/'site/data')
