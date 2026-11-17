from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import statistics

root = Path(__file__).resolve().parents[5]
data = root/'site/data'
for name in ('guests_churn.csv','service_log.jsonl','office.db'):
    print(name,'sha256',hashlib.sha256((data/name).read_bytes()).hexdigest())
guests=list(csv.DictReader((data/'guests_churn.csv').open()))
print('guests ids, unique',len(guests), len({r['guest_id'] for r in guests}))
for col in ['churned','card_blocked','city']:
    print(col,dict(Counter(r[col] for r in guests)))
print('missing check',sum(not r['avg_check'] for r in guests),'with at least 1 visit',sum(not r['avg_check'] and int(r['visits_90d'])>0 for r in guests))
rows=[json.loads(l) for l in (data/'service_log.jsonl').open()]
print('requests',len(rows),'unique requests',len({r['request_id'] for r in rows}),'guests',len({r['payload']['guest_id'] for r in rows}), 'time',rows[0]['ts'],rows[-1]['ts'])
print('status',dict(Counter(r['status'] for r in rows)))
print('status by client',dict(Counter((r['client'],r['status']) for r in rows)))
for ver in ('1.0','1.1'):
    a=[r['latency_ms'] for r in rows if r['model_version']==ver and r['status']==200]
    print('ms p50/p95(status200)',ver,len(a),statistics.median(a),statistics.quantiles(a,n=100,method='inclusive')[94])
con=sqlite3.connect(f'file:{data/"office.db"}?mode=ro',uri=True)
for table,key in [('clients','client_id'),('contracts','client_id'),('orders','order_id'),('tickets','ticket_id'),('invoices','invoice_id')]:
    sql=f'SELECT count(*), count(distinct {key}), sum(client_id not in (select client_id from clients)) from {table}'
    print('rows,unique key,orphans',table,con.execute(sql).fetchone())
for title,sql in [('client flags and missing industry','select sum(is_test),sum(industry is null) from clients'),('statuses and money','select status,count(*),round(sum(amount),2),min(amount),max(amount) from orders group by status'),('latest dates','select max(order_date),(select max(created_at) from tickets),(select max(due_date) from invoices),(select max(paid_date) from invoices),(select max(end_date) from contracts) from orders'),('open ends and payments','select (select count(*) from contracts where end_date is null), (select count(*) from invoices where paid_date is null)'),('ticket before contract','select count(distinct ticket_id) from tickets join contracts using(client_id) where created_at<start_date')]:
    print(title,con.execute(sql).fetchall())
for cut in ['2025-09-30','2025-12-31','2026-03-31','2026-06-30','2026-09-30']:
    print('cutoff',cut,con.execute("""with active as (select c.client_id from clients c join contracts k using(client_id) where not c.is_test and start_date<=? and (end_date is null or end_date>?)),
      rev as (select a.client_id,coalesce(sum(o.amount),0) r from active a left join orders o on a.client_id=o.client_id and o.status!='отменён' and o.order_date<=? and o.order_date>date(?,'-90 days') group by 1)
      select count(*),sum(r<0),sum(r=0),min(r) from rev""",(cut,)*4).fetchone())
assets=root/'site/notebooks'
nb=json.loads((assets/'ch15-practice.ipynb').read_text())
published=json.loads((assets/'tasks/ch15.json').read_text())['tasks']
exp=json.loads((root/'docs/reaudit-2026-11-16/ch15/technical/baseline-export.json').read_text())
print('published notebook cells',Counter(c['cell_type'] for c in nb['cells']))
for t in exp:
    if t['kind']=='task':
        entry=published['/'.join([t['lesson'],t['id']])]
        if t['check'].strip()!=entry['check'].strip():print('different published check',t['id'])
names=[r['lesson'] for r in exp]
by=defaultdict(Counter)
for r in exp:by[r['lesson'].split('/')[-1]][r['kind']]+=1
print('export',dict(by))
qry="""from tickets t join contracts k using(client_id) join clients c using(client_id)
 where t.created_at<c.created_at and not c.is_test"""
print('pre-enrolment unique tickets',con.execute('select count(distinct t.ticket_id) '+qry).fetchone()[0])
print('first case',con.execute('select t.ticket_id,t.client_id,t.created_at,c.created_at,k.start_date '+qry+' order by t.created_at limit 1').fetchone())
for cut in ['2025-09-30','2025-12-31','2026-03-31','2026-06-30','2026-09-30']:
    print('pre-enrolment tickets affecting 90d counts',cut,con.execute('select count(distinct t.ticket_id),count(distinct t.client_id) '+qry+" and start_date<=? and (end_date is null or end_date>?) and t.created_at>date(?,'-90 days') and t.created_at<=?",(cut,)*4).fetchone())
