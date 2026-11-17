import csv
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

import pandas as pd
import numpy as np

root = Path(__file__).resolve().parents[5]
items = {t['id']:t for t in json.loads(Path(sys.argv[1]).read_text()) if t['lesson'].startswith('ch15/') and t['kind']=='task'}
os.chdir(tempfile.mkdtemp(prefix='ch15-expert-probes-'))
for name in ('office.db','guests_churn.csv','service_log.jsonl'):
    shutil.copy(root/'site/data'/name,name)

def scope(t):
    ns={}
    def need(name, kind=None):
        value=ns[name]
        if kind: assert isinstance(value,kind)
        return value
    ns.update(need=need,close=lambda a,b,tol: abs(a-b)<=tol)
    exec(t['setup'],ns)
    return ns

def check(t,ns,label):
    try:exec(t['check'],ns)
    except Exception as err:print(label,'REJECT',type(err).__name__,str(err).splitlines()[0])
    else: print(label,'ACCEPT')

t=items['guard']; n=scope(t); exec(t['solution'],n)
check(t,n,'guard-author')
good=n['range_problems']
for row in [(0,.5,800),(-1,.5,800), (True,.5,800),(float('nan'),.5,800),(0,.5,float('nan')),(-1,3,800)]:
    print('guard row',row,good(dict(zip(['visits_90d','delivery_share','avg_check'],row))))
n['range_problems']=lambda r:list(reversed(good(r)))
check(t,n,'guard-alt-reverse')
n['range_problems']=lambda r:good(r)[:1]
check(t,n,'guard-first-only')
t=items['log-csv']; n=scope(t); exec(t['solution'],n); check(t,n,'journal-author')
n['append_run'](n['r1'],'transfer.csv')
n['append_run'](dict(reversed(n['r2'].items())),'transfer.csv')
print('journal columns after transfer',pd.read_csv('transfer.csv').iloc[-1].to_dict())
n['append_run']=lambda run,path: None
check(t,n,'journal-no-op-after-output')
t=items['package']; n=scope(t); exec(t['solution'],n); check(t,n,'package-author')
for c in ['2025-09-30','2025-12-31','2026-03-31','2026-06-30','2026-09-30']:
    frame=n['snapshot'](c); print('snapshot',c,len(frame),frame.client_id.nunique(),frame.get('churn',pd.Series(dtype=float)).sum(min_count=1), 'raw target counts',n['build_target'](c).value_counts(dropna=False).to_dict())
cut=pd.Timestamp('2026-06-30')
before=n['build_features'](cut)
for table,col in [('orders','order_date'),('tickets','created_at'),('invoices','due_date')]:
    n[table]=n[table].loc[n[table][col]<=cut].copy()
n['invoices'].loc[n['invoices']['paid_date']>cut,'paid_date']=pd.NaT
print('future truncation cells changed',int((before!=n['build_features'](cut)).sum().sum()))
raw=scope(t); n.update({name:raw[name] for name in ['orders','tickets','invoices']})
# Closures above use raw scope. Use it throughout remaining package checks.
n=raw
s=t['solution'].replace('head(150)','head(3)').replace('"version": "1.0",','"version": "1.0", "call_limit": 3,').replace('.head(20)', '.tail(20)')
exec(s,n); check(t,n,'package-cap3-alt-golden')
files=['golden.csv','passport.json','call_list.csv']
save={name:Path(name).read_bytes() for name in files}
def probe(tag,name,transform):
    if name.endswith('.json'):
        data=json.loads(Path(name).read_text()); data=transform(data);Path(name).write_text(json.dumps(data))
    else:
        data=pd.read_csv(name); data=transform(data);data.to_csv(name,index=False)
    check(t,n,tag);Path(name).write_bytes(save[name])
probe('golden-reverse','golden.csv',lambda df:df.iloc[::-1])
probe('golden-wrong-key','golden.csv',lambda df:df.assign(client_id=df.client_id.iloc[::-1].values))
probe('golden-wrong-p','golden.csv',lambda df:df.assign(expected=.01))
probe('golden-19','golden.csv',lambda df:df.head(19))
probe('wrong-city','call_list.csv',lambda df:df.assign(city='Томск'))
probe('wrong-proba','call_list.csv',lambda df:df.assign(p_churn=.01))
probe('wrong-order','call_list.csv',lambda df:df.iloc[::-1])
probe('wrong-total','passport.json',lambda d:{**d,'expected_profit':0})
probe('wrong-date','passport.json',lambda d:{**d,'cutoff':'2026-06-30'})
probe('wrong-limit','passport.json',lambda d:{**d,'call_limit':2})
probe('wrong-feature-order','passport.json',lambda d:{**d,'features':d['features'][::-1]})
probe('wrong-database-hash','passport.json',lambda d:{**d,'data_md5':'abc'})
# A real alternate allowed classifier, fitted on all four labelled snapshots.
exec(s.replace('LogisticRegression(max_iter=2000)',"__import__('sklearn.tree',fromlist=['DecisionTreeClassifier']).DecisionTreeClassifier(max_depth=3,random_state=11)").replace('логистическая регрессия','дерево решений'),n)
check(t,n,'package-alt-tree')
cid=n['active_at'](cut).sort_values('start_date').client_id.iloc[0]
order=n['orders'].head(2).copy()
order['client_id']=cid;order['order_date']=[cut-pd.Timedelta(days=30),cut-pd.Timedelta(days=120)]
order['status']='возврат';order['amount']=[-1,0]
n['orders']=order
print('package zero denominator (-1,0) revenue trend',n['build_features'](cut).loc[cid,'revenue_trend'])
