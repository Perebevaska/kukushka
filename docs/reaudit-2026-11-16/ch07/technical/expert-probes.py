"""Independent Pyodide calculations. Input is the three frozen CSV snapshots."""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

g = pd.read_csv('guests_churn.csv')
t = pd.read_csv('guest_tiers.csv')
d = pd.read_csv('catering_leads.csv')
for frame, key in ((g,'guest_id'), (t,'guest_id'), (d,'lead_id')):
    print("shape/key/NA",frame.shape,frame[key].nunique(),frame.isna().sum().loc[lambda s:s>0].to_dict())
assert g.guest_id.equals(t.guest_id)
assert g.avg_check.isna().equals(g.visits_90d.eq(0))
assert d.contract_rub.notna().equals(d.converted.eq(1))
print("guests",g.churned.sum(), t.card_tier.value_counts().to_dict())
created = pd.to_datetime(d.created)
launch = created.sort_values().iloc[-750]
mature = created + pd.Timedelta(days=30) < launch
hold = created >= launch
print("calendar",created.min(),created.max(),launch, mature.sum(), sum(~mature & ~hold),hold.sum(),d.loc[mature,'converted'].sum(),d.loc[hold,'converted'].sum(), (created+pd.Timedelta(days=30)).max())
X = pd.get_dummies(g.drop(columns=['guest_id','churned','card_blocked']),dtype=int).fillna({'avg_check':0})
y = g.churned
a,b,c,e = train_test_split(X,y,stratify=y,random_state=42,test_size=.25)
fold = KFold(5,shuffle=True,random_state=42)
lr = LogisticRegression(max_iter=2000)
old = cross_validate(lr,StandardScaler().fit_transform(a),c,cv=fold,scoring=['roc_auc','f1'])
safe = cross_validate(make_pipeline(StandardScaler(),clone(lr)),a,c,cv=fold,scoring=['roc_auc','f1'],return_estimator=True)
print("scale: global -> training rows per fold", len(a),[int(est[0].n_samples_seen_) for est in safe['estimator']])
print("scale: five AUC prefit",old['test_roc_auc'].tolist(),"inside",safe['test_roc_auc'].tolist())
pa=lr.fit(a,c).predict_proba(b)[:,1]
pb=LogisticRegression(max_iter=2000,class_weight='balanced').fit(a,c).predict_proba(b)[:,1]
print("class weights: rank correlation/top100 overlap/auc",pd.Series(pa).corr(pd.Series(pb),method='spearman'),len(set(np.argsort(-pa)[:100]) & set(np.argsort(-pb)[:100])),roc_auc_score(e,pa),roc_auc_score(e,pb))
for probs in [[.4,.4,.9],[.2,.4,.4]]:
    print('tree leaf probabilities / forest decision', probs,np.mean(probs),int(np.mean(probs)>.5))
flags = pd.DataFrame({'lead_id':['R-04','R-03','R-01','R-02'],'p':[.5,.9,.5,.5],'fact':[0,1,1,0]})
for table in (flags,flags.iloc[::-1]):
    top=table.sort_values(['p','lead_id'],ascending=[False,True]).head(2)
    print('tied budget 2 IDs and count',top.lead_id.tolist(),top.fact.sum())
