"""Run with the pre-edit course export as argv[1] from the repository root."""
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys

for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[variable] = '1'
import numpy as np
import pandas as pd
import sklearn
from scipy.stats import binomtest
from sklearn.model_selection import train_test_split

base = Path.cwd()
cards = {r['id']: r for r in json.loads(Path(sys.argv[1]).read_text())
         if r['lesson'].startswith('ch08/') and r['kind'] == 'task'}
os.chdir(base / 'site/data')
out = {'versions': [sys.version.split()[0], np.__version__, pd.__version__, sklearn.__version__]}

def author(card):
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(cards[card]['setup'] or '', ns)
        exec(cards[card]['solution'], ns)
    return ns

def rates(df, by):
    return df.groupby(by, observed=True).bought.agg(['sum','size','mean']).round(5).to_dict('index')

fp = author('fp-honest')
off = fp['off']
train = off.loc[fp['X_train'].index]
eda = {}
for name, frame in [('training', train), ('all_offers', off)]:
    morning = pd.cut(frame.morning_share,[0,.2,.5,1],include_lowest=True,labels=['low','middle','high'])
    eda[name] = {'purchases': int(frame.bought.sum()), 'count': len(frame), 'morning':rates(frame,morning),
                 'quartile': rates(frame, pd.qcut(frame.orders_per_week,4,labels=['1','2','3','4'])),
                 'source':rates(frame,'source'), 'city':rates(frame,'city'),
                 'lift_morning_top': frame.loc[morning=='high','bought'].mean() / frame.bought.mean()}
out['eda'] = eda
rest, ctrl = fp['rest'], fp['ctrl']
t = fp['best_t_incr']
picked = rest.loc[rest['send']]
organic = ctrl.loc[fp['hi'],'bought']
recent = rest.reg_date >= '2026-06-01'
wi = binomtest(organic.sum(),len(organic)).proportion_ci(method='wilson')
eb = picked.p.sum()
gross = eb * 1600 - len(picked)*150
out['subscription'] = dict(t=t, rest=len(rest), recent=int(recent.sum()),
                           chosen=len(picked), recent_chosen=int((recent & rest.send).sum()),
                           eligible_chosen=int((~recent & rest.send).sum()), expected=eb,
                           cost=len(picked)*150, visited7=int((picked.recency_days<=7).sum()),
                           gross=gross, extra=int(fp['honest_profit']), all=int(fp['honest_all']),
                           organic=[int(organic.sum()),len(organic)], alt_margin=gross-3100*len(picked)*organic.mean(),
                           partial_wilson=[gross-1600*len(picked)*p for p in [wi.high,wi.low]],
                           eligible_reg_max=off.reg_date.max(), empty_baseline=int(fp['incr'].margin.isna().sum()),
                           grid=fp['incr'].sort_values('margin', ascending=False).head(2).to_dict('records'))
out['cities'] = author('boot')['risk'].to_dict('index')
rf_card = next(k for k in cards if 'same_choice =' in str(cards[k]['solution']))
out['cities_forest'] = author(rf_card)['rf_risk'].to_dict('index')
con = sqlite3.connect('file:final1.db?mode=ro', uri=True)
out['tables'] = {r[0]: con.execute('SELECT count(*) FROM '+r[0]).fetchone()[0]
                 for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
queries = {'last_order': 'SELECT MAX(ordered_at) FROM orders',
           'first_order': 'SELECT MIN(ordered_at) FROM orders',
           'complaints_before_registration':'SELECT count(*) FROM complaints c JOIN guests g USING(guest_id) WHERE c.created_at<g.reg_date',
           'multiple_free_drinks_per_day':"""SELECT COUNT(*) FROM (SELECT guest_id, DATE(ordered_at),SUM(qty) n FROM orders JOIN order_items USING(order_id) WHERE price=0 GROUP BY 1,2 HAVING n>1)""",
           'pilot_june_reg':"""SELECT count(*) FROM pilot JOIN guests USING(guest_id) WHERE reg_date >= '2026-06-01'""",
           'pilot_cohort':"""SELECT group_name,COUNT(*),SUM(bought),MIN(reg_date),MAX(reg_date) FROM pilot JOIN guests USING(guest_id) GROUP BY 1""",
           'pilot_purchase_window': 'SELECT min(bought_at), max(bought_at) FROM pilot',
           'dob_missing_placeholder':'SELECT SUM(birth_year IS NULL),SUM(birth_year=1900) FROM guests',
           'eligible_addresses':"""SELECT COUNT(DISTINCT g.guest_id) FROM guests g JOIN orders o USING(guest_id) WHERE g.reg_date<'2026-06-01' AND o.ordered_at<'2026-07-01'"""}
out['db'] = {k:con.execute(s).fetchall() for k,s in queries.items()}
for file in ['guests_churn','guests_age','catering_leads','sites','bonus_pilot','shop_funnel']:
    path=Path(file+'.csv')
    df=pd.read_csv(path)
    key={'shop_funnel':['month','shop_id'],'catering_leads':['lead_id'],'sites':['site_id']}.get(file,['guest_id'])
    out[file]={'rows':len(df), 'duplicate_keys':int(df.duplicated(key).sum()), 'missing':df.isna().sum()[df.isna().any()].to_dict(),
               'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
with open('bonus_pilot.csv') as f:
    pilot=list(csv.DictReader(f))
out['bonus_churn']={g:sum(int(r['churned']) for r in pilot if r['group']==g) for g in {'бонус','контроль'}}
funnel=pd.read_csv('shop_funnel.csv').groupby('month')[['visitors','checks','revenue']].sum()
out['funnel']=funnel.to_dict('index')
print(json.dumps(out, ensure_ascii=False, indent=2, default=lambda x: x.item()))
