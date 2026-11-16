import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split,GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import f1_score,confusion_matrix,precision_score,recall_score
import json
import matplotlib
matplotlib.use('Agg')
out=Path(__file__).resolve().parent
os.chdir(out.parents[2]/'site/data')
rows=[json.loads(i) for i in (out/'student.jsonl').read_text().splitlines()]
for row in rows:
    if row['lesson']=='05-project' and 'code' in row:
        exec(row['code'],globals())
print('holdout acc/macro',acc_sent,acc_topic,macro_f1,rarest,worst,count_ratio,f1_rare_balanced)
print(by_shop)
print('before/after cause',cause,kzn.loc[cause].round(3).to_dict(),others.loc[cause].round(3).to_dict())
print('quotes',quotes)
print('by week',weekly['KZN-2'].round(3).to_dict())
print('adjust',tpr,fpr,adj)
print('counts',n[n.shop_id=='KZN-2'].groupby('period').neg.agg(['sum','size']))
v=r.text
for target in (y,r.topic):
    tr,te=train_test_split(r.index,test_size=.25,random_state=42,stratify=target)
    overlap=r.text[te].isin(r.text[tr])
    print('duplicate overlap',overlap.sum(),len(te),'of',len(set(v)))
    m=new_model().fit(v[tr],target[tr])
    print('seen vs unseen',m.score(v[te][overlap],target[te][overlap]),m.score(v[te][~overlap],target[te][~overlap]))
# Проверяю на исходном holdout порог, выбранный только на validation.
xtr,xte,ytr,yte=train_test_split(r.text,y,test_size=.25,random_state=42,stratify=y)
xa,xv,ya,yv=train_test_split(xtr,ytr,test_size=.25,random_state=42,stratify=ytr)
m=make_pipeline(TfidfVectorizer(),LogisticRegression(max_iter=1000)).fit(xa,ya)
grid=np.arange(.05,.96,.01)
pv=m.predict_proba(xv)[:,1]
thr=max(t for t in grid if recall_score(yv,pv>=t)>=.95)
print('threshold-from-valid',round(thr,2),recall_score(yv,pv>=thr),recall_score(yte,m.predict_proba(xte)[:,1]>=thr))
