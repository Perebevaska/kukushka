"""Audit dates only. Read-only baseline, no training or writes to the teaching DB."""
import csv
import hashlib
import sqlite3
from datetime import date,timedelta
from pathlib import Path

out = Path(__file__).resolve().parent
baseline=out.parent/'data-baseline/office.db'
assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='ec4fae8730a68fb4f2508ece2003efc017f19ff5457c1c87eee12dcb083c019f'
db=sqlite3.connect(f'file:{baseline}?mode=ro',uri=True)
db.row_factory=sqlite3.Row
rows=db.execute("""select distinct t.ticket_id,t.client_id,t.category,t.created_at as ticket_at,c.created_at as client_at,k.start_date,k.end_date,
 case when t.created_at<c.created_at then 'A: before CRM' else 'B: CRM to contract' end as timing
 from tickets t join clients c using(client_id) join contracts k using(client_id)
 where not c.is_test and t.created_at<k.start_date order by t.created_at,t.ticket_id""").fetchall()
assert len(rows)==len(set(r['ticket_id'] for r in rows))
with (out/'ticket-ids.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(rows[0].keys());w.writerows(rows)
for timing in ('A: before CRM','B: CRM to contract'):
    selected=[r for r in rows if r['timing']==timing]
    print(timing,'unique tickets',len(selected),'unique offices',len({r['client_id'] for r in selected}))
for cut in ['2025-09-30','2025-12-31','2026-03-31','2026-06-30','2026-09-30']:
    low=(date.fromisoformat(cut)-timedelta(days=90)).isoformat()
    active=[r for r in rows if low<r['ticket_at']<=cut and r['start_date']<=cut and (not r['end_date'] or r['end_date']>cut)]
    for tag,selected in [('exclude_A',[r for r in active if r['timing'].startswith('A')]),('exclude_A_and_B',active)]:
        print(cut,tag,'ticket_count_delta',len(selected),'billing_count_delta',sum(r['category']=='счёт' for r in selected),'affected_offices',len({r['client_id'] for r in selected}))
