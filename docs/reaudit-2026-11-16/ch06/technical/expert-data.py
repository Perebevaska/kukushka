"""Independent chapter 6 probes for the bundled Pyodide, launched by expert-run.mjs."""
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

report = {"versions": [platform.python_version(), pd.__version__, np.__version__, sklearn.__version__]}
frames = {}
profiles = {}
for name, key in {
    'deliveries': 'delivery_id', 'guest_orders': 'order_id', 'guests_churn': 'guest_id',
    'guests_churn_dates': 'guest_id', 'guests_current': 'guest_id'
}.items():
    frame = frames[name] = pd.read_csv(name + '.csv')
    profiles[name] = dict(rows=len(frame), duplicate_keys=int(frame[key].duplicated().sum()),
                          duplicate_rows=int(frame.duplicated().sum()), nulls=frame.isna().sum().loc[lambda x:x>0].to_dict())
report['files'] = profiles
d = frames['deliveries']
ok = d.loc[d.actual_min.between(1,299)].copy()
ok['hour'] = pd.to_datetime(ok.created).dt.hour
y = ok.actual_min > ok.promised_min
a,b = train_test_split(ok.index, test_size=.25, random_state=42)
x = pd.get_dummies(ok[['distance_km','items','promised_min','hour','courier','weather','shop_id']],dtype=int)
ya = y.loc[a]
shops = ok.shop_id.copy()
rates = ya.groupby(shops.loc[a]).mean()
train,valid = train_test_split(a, test_size=1/3,random_state=42)
lr = LogisticRegression(max_iter=2000).fit(x.loc[train], y.loc[train])
pv = lr.predict_proba(x.loc[valid])[:,1]
t = next(t for t in np.arange(.1,.9,.05).round(2) if y.loc[valid][pv>=t].mean()>=.8)
def hit(model,ids,t):
    mask=model.predict_proba(x.loc[ids])[:,1]>=t
    return [int(y.loc[ids][mask].sum()),int(mask.sum()),int(y.loc[ids].sum())]
m_all = LogisticRegression(max_iter=2000).fit(x.loc[a],ya)
contrib=x.loc[1590]*pd.Series(m_all.coef_[0],index=x.columns)
report['logit_1590']={'b0':float(m_all.intercept_[0]), 'coef': {k:round(float(v),3) for k,v in zip(x.columns, m_all.coef_[0])},'contrib':contrib[contrib.ne(0)].round(3).to_dict()}
report['threshold'] = dict(sizes=[len(train),len(valid),len(b)],threshold=t,valid=hit(lr,valid,t),test=hit(lr,b,t),
                           selected_on_test=hit(LogisticRegression(max_iter=2000).fit(x.loc[a],ya),b,.60))
unknown = b[0]
singleton = a[0]
shops.loc[unknown]='new-test'
shops.loc[singleton]='singleton'
rest = a[a!=singleton]
single_rate = float(ya.groupby(shops.loc[a]).mean().loc['singleton'])
report['shop'] = dict(train_mean=ya.mean(), test_mean=y.loc[b].mean(), global_mean=y.mean(), diff_pp=float(100*(rates-y.groupby(ok.shop_id).mean()).abs().max()), unknown_row=int(unknown), singleton_row=int(singleton), own=int(y.loc[singleton]), self_included=single_rate, other_mean=y.loc[rest].mean(), new_test_rate=shops.loc[b].map(ya.groupby(shops.loc[a]).mean()).fillna(ya.mean()).loc[unknown])
columns=['distance_km','items','promised_min','hour']
xx=ok[columns]
sub, val=train_test_split(a,test_size=.25,random_state=43)
widget=json.loads(Path('depth.json').read_text())
for row in widget['rows']:
    model=DecisionTreeClassifier(max_depth=row['depth'],random_state=0).fit(xx.loc[sub],y.loc[sub])
    assert round(model.score(xx.loc[val], y.loc[val]),4)==row['validation']
    assert round(model.score(xx.loc[sub], y.loc[sub]),4)==row['train']
model=DecisionTreeClassifier(max_depth=3,random_state=0).fit(xx.loc[a],ya)
report['delivery'] = dict(usable=len(ok), late=int(y.sum()), days=[d.created.min(),d.created.max()],
                          shop_count=d.shop_id.nunique(), fourth_id=int(b[3]), fourth_leaf=model.predict_proba(xx.loc[[b[3]]])[0].tolist(),
                          calibrated_boundaries=[int(pd.cut(pd.Series([0,.25,.5,.75,1]),[0,.25,.5,.75,1],include_lowest=flag).count()) for flag in [False,True]],
                          widget_checked=len(widget['rows']))
o=frames['guest_orders']
tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=4).split(o,groups=o.guest_id))
report['orders'] = dict(guests=o.guest_id.nunique(),dates=[o.datetime.min(),o.datetime.max()],range_per_guest=[o.groupby('guest_id').size().min(),o.groupby('guest_id').size().max()],test_orders=len(te),test_guests=o.guest_id.iloc[te].nunique(), overlap=len(set(o.guest_id.iloc[te]) & set(o.guest_id.iloc[tr])))
g=frames['guests_churn'].set_index('guest_id')
dates=frames['guests_churn_dates'].set_index('guest_id').loc[g.index]
assert len(dates.drop_duplicates())==1
current=frames['guests_current'].set_index('guest_id')
overlap=g.index.intersection(current.index)
last=pd.Timestamp('2026-12-01')-pd.to_timedelta(current.loc[overlap,'days_since_last'],unit='D')
hist=g.loc[overlap,'churned']
bad_gone=last.between('2026-10-01','2026-11-29') & hist.eq(1)
bad_stayed=last.lt('2026-10-01') & hist.eq(0)
report['dates']=dict(history=dates.iloc[0].to_dict(),current=current.snapshot_date.unique().tolist(),
                      mature=str((pd.Timestamp(current.snapshot_date.iloc[0])+pd.Timedelta(days=60)).date()),
                      overlap=len(overlap),gone_with_later_visit=int(bad_gone.sum()),stayed_last_too_early=int(bad_stayed.sum()),
                      examples={str(i):str(v.date()) for i,v in last[bad_gone|bad_stayed].head(3).items()})
gx=pd.get_dummies(g.drop(columns=['card_blocked','churned']).fillna({'avg_check':0}),dtype=int)
gy=g.churned
ga,gb=train_test_split(g.index,test_size=.25,random_state=42,stratify=gy)
rf=RandomForestClassifier(n_estimators=100,min_samples_leaf=3,random_state=0).fit(gx.loc[ga],gy.loc[ga])
risk=pd.Series(rf.predict_proba(gx.loc[gb])[:,1],index=gb)
def top(s,k):
    return s.sort_index().sort_values(ascending=False,kind='stable').head(k).index
def compare(ids):
    k=len(ids)//10
    return [len(ids),k,int(gy.loc[ids].sum()),int(gy.loc[top(risk.loc[ids],k)].sum()),int(gy.loc[top(g.loc[ids,'days_since_last'],k)].sum())]
report['churn']=dict(positives=int(gy.sum()), blocked_by_churn=pd.crosstab(g.card_blocked,gy).to_dict(), historical=compare(gb),quiet=compare(gb[g.loc[gb,'days_since_last']<=45]), rf_accuracy=rf.score(gx.loc[gb],gy.loc[gb]), current_budget=len(current)//10)
models={'forest':rf,'tree4':DecisionTreeClassifier(max_depth=4,random_state=0),'logreg':LogisticRegression(max_iter=2000)}
kf=KFold(5,shuffle=True,random_state=42)
for name,m in models.items():
    scores=[]; rates=[]
    for tr,va in kf.split(ga):
        train_ids,val_ids=ga[tr],ga[va]
        m.fit(gx.loc[train_ids],gy.loc[train_ids])
        scores.append(m.score(gx.loc[val_ids],gy.loc[val_ids]))
        rp=pd.Series(m.predict_proba(gx.loc[val_ids])[:,1],index=val_ids)
        rates.append(gy.loc[top(rp,len(rp)//10)].mean())
    report['churn'][name]=dict(acc_mean=np.mean(scores),acc_std=np.std(scores),precision_at_10pct=np.mean(rates))
from sklearn.metrics import accuracy_score
orig = frames['guests_churn'].copy()
orig['avg_check'] = orig['avg_check'].fillna(0)
XX = pd.get_dummies(orig.drop(columns=['guest_id','card_blocked','churned']), dtype=int)
yy = orig.churned
XA, XB, YA, YB = train_test_split(XX, yy, test_size=.25, random_state=42, stratify=yy)
mf = RandomForestClassifier(n_estimators=100,min_samples_leaf=3,random_state=0).fit(XA,YA)
rr = pd.Series(mf.predict_proba(XB)[:,1],index=XB.index)
days = XB.days_since_last
rank_order = orig.loc[XB.index].sort_values('guest_id').index
sorted_r=rr.loc[rank_order].sort_values(ascending=False,kind='stable').head(60).index
sorted_d=days.loc[rank_order].sort_values(ascending=False,kind='stable').head(60).index
report['course_order'] = dict(accuracy=mf.score(XB,YB),hits=int(YB.loc[sorted_r].sum()),day_hits=int(YB.loc[sorted_d].sum()), threshold45=int((days>45).sum()), rule_overlap=int((days.loc[sorted_r]>45).sum()), cv=cross_val_score(mf,XA,YA,cv=kf).tolist())
json.dumps(report,indent=2,ensure_ascii=False,default=lambda v:v.item())
