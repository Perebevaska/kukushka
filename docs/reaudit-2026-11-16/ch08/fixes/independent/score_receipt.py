"""Independent score and effect reconstruction for the student's documented protocol.

Inner training includes the same 1,350 offer recipients and 400 controls.
The published candidate CSV supplies only the comparison target, never inputs.
"""
import argparse,json,sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold,train_test_split,cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.metrics import roc_auc_score
parser=argparse.ArgumentParser()
parser.add_argument('data',type=Path);parser.add_argument('student',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
con=sqlite3.connect(args.data/'final1.db')
data=pd.read_sql_query("""
WITH ordered AS (SELECT * FROM orders WHERE ordered_at<'2026-07-01'),
 agg AS (SELECT guest_id,COUNT(*) AS orders_n,AVG(amount) AS avg_check,AVG(channel='доставка') AS delivery_share,
 AVG(CAST(strftime('%H',ordered_at) AS int)<10 AND strftime('%w',ordered_at) BETWEEN '1' AND '5') AS morning_share,
 COUNT(DISTINCT shop_id) AS shops_n,julianday('2026-07-01')-julianday(MAX(ordered_at)) AS recency_days
 FROM ordered GROUP BY guest_id),
 coffee AS (SELECT guest_id,AVG(category='кофе') AS coffee_share FROM ordered JOIN order_items USING(order_id)
 JOIN menu USING(item_id) GROUP BY guest_id),
 sessions AS (SELECT guest_id,SUM(sessions) AS app_sessions FROM app_sessions WHERE month<'2026-07' GROUP BY guest_id),
 issues AS (SELECT guest_id,COUNT(*) AS complaints_n FROM complaints WHERE created_at<'2026-07-01' GROUP BY guest_id)
SELECT g.guest_id,g.reg_date,g.source,s.city,
 julianday('2026-07-01')-julianday(g.reg_date) AS tenure_days,
 COALESCE(a.orders_n,0) AS orders_n,COALESCE(a.orders_n,0)*7.0/MIN(julianday('2026-07-01')-julianday(g.reg_date),122) AS orders_per_week,
 a.recency_days,a.avg_check,a.delivery_share,a.morning_share,COALESCE(a.shops_n,0) AS shops_n,c.coffee_share,
 COALESCE(sessions.app_sessions,0) AS app_sessions, COALESCE(issues.complaints_n,0) AS complaints_n
FROM guests g JOIN shops s ON g.home_shop_id=s.shop_id
 LEFT JOIN agg a USING(guest_id) LEFT JOIN coffee c USING(guest_id) LEFT JOIN sessions USING(guest_id) LEFT JOIN issues USING(guest_id)
""",con).set_index('guest_id')
p=pd.read_sql_query('select guest_id,group_name,bought from pilot order by rowid',con).set_index('guest_id')
offer=p[p.group_name.eq('предложение')];ctrl=p[p.group_name.eq('контроль')]
train,test=train_test_split(offer,test_size=.25,random_state=42,stratify=offer.bought)
train0,test0=train_test_split(ctrl,test_size=1/3,random_state=42,stratify=ctrl.bought)
num='orders_n orders_per_week recency_days avg_check delivery_share morning_share shops_n tenure_days coffee_share app_sessions complaints_n'.split()
cat=['source','city']
def fit(ids):
    prep=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median'),StandardScaler()),num),('cat',OneHotEncoder(handle_unknown='ignore'),cat)])
    return make_pipeline(prep,LogisticRegression(max_iter=1000)).fit(data.loc[ids.index],ids.bought)
def probabilities(model,ids):return model.predict_proba(data.loc[ids])[:,1]
m=fit(train)
oof=cross_val_predict(m,data.loc[train.index],train.bought,cv=StratifiedKFold(5,shuffle=True,random_state=42),method='predict_proba')[:,1]
pc=probabilities(m,train0.index)
rows=[]
for threshold in [v/100 for v in range(2,41,2)]:
    pick,control=oof>threshold,pc>threshold
    n,k=int(pick.sum()),int(control.sum())
    gain=1600*(train.bought.iloc[pick].sum()-n*train0.bought.iloc[control].mean())-150*n
    if n<=300 and k>=20 and gain>=0: rows.append((gain,threshold,n,k))
gain,t,n,k=max(rows,key=lambda a:(a[0],-a[1]))
pt,pt0=probabilities(m,test.index),probabilities(m,test0.index)
pick,control=pt>t,pt0>t
nt,nb=int(pick.sum()),int(test.bought.iloc[pick].sum())
k0,b0=int(control.sum()),int(test0.bought.iloc[control].sum())
eda=train.join(data.morning_share).query('morning_share>.5')
dep=fit(offer)
deliver=pd.read_csv(args.student/'subscription-artifacts/candidate-decisions.csv').set_index('guest_id')
ps=probabilities(dep,deliver.index)
mask=ps>t
pcs=probabilities(dep,ctrl.index)>t
nc,bc=int(pcs.sum()),int(ctrl.bought.iloc[pcs].sum())
maxdiff=float(np.max(np.abs(ps-deliver.p)))
result=dict(threshold=t,OOF_margin=gain,training_sent=n,training_control=k,training_eda=[len(eda),int(eda.bought.sum())],test_auc=roc_auc_score(test.bought,pt),test_contacts=nt,test_buyers=nb,
 test_control=k0,test_control_buyers=b0,test_margin=1600*(nb-nt*b0/k0)-150*nt,
 full_control_n=nc,full_control_buyers=bc,candidate_contact=int(mask.sum()),candidate_sum_p=float(ps[mask].sum()),
 candidate_margin=float(1600*(ps[mask].sum()-mask.sum()*bc/nc)-150*mask.sum()),candidate_max_abs_probability_error=maxdiff,
 decision_id_mismatches=int((deliver.send!=mask).sum()),cohort_june_reg_selected=int((data.loc[deliver.index].reg_date.ge('2026-06-01') & mask).sum()))
split_errors={}
for key,grp in [('offer-train',train),('offer-test',test),('control-train',train0),('control-test',test0)]:
    file=args.student/'subscription-artifacts'/(key+'-ids.csv')
    if file.exists():
        supplied=pd.read_csv(file).guest_id
        split_errors[key]={'expected':len(grp),'duplicates':int(supplied.duplicated().sum()),'wrong_ids':len(set(supplied)^set(grp.index))}
result['split_id_checks']=split_errors
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
