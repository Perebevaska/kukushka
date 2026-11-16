"""One-thread native challenge probes on an exported course and the same six CSVs."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

evidence = Path(__file__).resolve().parent
root = evidence.parents[3]
sys.path.insert(0, str(root / 'site/assets'))
import harness

export = Path(sys.argv[1])
tasks = {t['id']:t for t in json.loads(export.read_text()) if t['lesson'].startswith('ch13/') and t['kind']=='task'}
os.chdir(evidence / 'data-baseline')
print('version',sys.version,sklearn.__version__,pd.__version__)
adjust = tasks['adjust']
trials = [
    ('alternative-keys',True,"n = n.sample(frac=1, random_state=41)\n", "\naudit = audit.iloc[::-1]"),
    ('extra-period',False,"","\naudit.loc['весь период'] = audit.iloc[0]"),
    ('incomplete-source',False,"n = n.drop(n.index[(n['shop_id']=='KZN-2') & (n['period']=='до')][0])\n",""),
    ('wrong-join',False,"","\naudit.loc['до','complaints'] += 1")
]
for name, expected, prefix, suffix in trials:
    res = harness.run(prefix+adjust['solution']+suffix,adjust['check'],adjust['setup'],False)
    print(json.dumps(dict(trial=name,expected=expected,code_prefix=prefix,code_suffix=suffix,result=res['check'],code_ok=res['ok']),ensure_ascii=False))
rows = pd.read_csv('reviews_text.csv')
neg = rows.rating.le(3)
make = lambda ngram=(1,1), **kwargs: make_pipeline(TfidfVectorizer(ngram_range=ngram),LogisticRegression(max_iter=1000,**kwargs))
def split(ids,y,size): return train_test_split(ids,test_size=size,random_state=42,stratify=y)
dev, test = split(rows.index,neg,.25)
train,val = split(dev,neg.loc[dev],1/3)
m = make().fit(rows.text[train],neg[train])
vp,fp = (m.predict_proba(rows.text[k])[:,1] for k in (val,test))
threshold = max(t for t in np.arange(.05,.96,.01) if recall_score(neg[val],vp>=t)>=.95)
print('recall95',threshold,'validation',int((vp>=threshold).sum()),recall_score(neg[val],vp>=threshold),precision_score(neg[val],vp>=threshold),'final',int((fp>=threshold).sum()),recall_score(neg[test],fp>=threshold))
bad = [t for t in np.arange(.05,.96,.01) if recall_score(neg[test],vp>=t)>=.95]
print('hint-pairs-different-IDs',len(set(val)&set(test)), 'wrong threshold',max(bad) if bad else None)
cols = pd.read_csv('reviews_new.csv',parse_dates=['date'])
gold = pd.read_csv('reviews_new_gold.csv').sample(frac=1,random_state=78)
cols['signal']=make((1,2)).fit(rows.text,neg).predict(cols.text)
c = cols.merge(gold,on='review_id',validate='1:1')
for dt in ('2026-10-01','2026-10-05'):
    part=c[c.shop_id.eq('KZN-2')]
    for after,g in part.groupby(part.date.ge(dt)):
        print('project',dt,after,len(g),int(g.complaint.sum()),int(g.signal.sum()),'tp,fp',int((g.signal & g.complaint.eq(1)).sum()),int((g.signal & g.complaint.eq(0)).sum()))
q=tasks['llm-same']
env={}
exec(q['setup'],env)
sample=env['check']; control=rows[~rows.review_id.isin(sample.review_id)]
ok_pred=make().fit(control.text,control.topic).predict(sample.text)==sample.topic
ok_llm = env['ok_llm']
delta=ok_llm.astype(int)-ok_pred.astype(int)
print('paired n/language model/baseline/only-language/only-baseline/lower/upper',len(delta),int(ok_llm.sum()),int(ok_pred.sum()),int((delta==1).sum()),int((delta==-1).sum()),float(delta.mean()-1.96*delta.sem()),float(delta.mean()+1.96*delta.sem()))
u,v=split(rows.index,rows.topic,.25)
rare=rows.topic[v].value_counts().idxmin()
for kw in ({},{'class_weight':'balanced'}):
    pred=make((1,2),**kw).fit(rows.text[u],rows.topic[u]).predict(rows.text[v])
    known=rows.text[v].isin(rows.text[u])
    print('topics',kw,'rarest',rare,int((rows.topic[v]==rare).sum()),'predicted rare',int((pred==rare).sum()),'F1 rare',f1_score(rows.topic[v],pred,labels=[rare],average=None).tolist(),'macro',f1_score(rows.topic[v],pred,average='macro'))
    print('new',int((~known).sum()),float(np.mean(pred[~known]==rows.topic[v][~known])),f1_score(rows.topic[v][~known],pred[~known],average='macro'))
