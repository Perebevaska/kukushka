"""Воспроизводит исходную главу по CSV, независимо от setup и решения карточек."""
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import statsmodels
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, train_test_split
from statsmodels.tsa.stattools import adfuller

here = Path(__file__).resolve().parent
s = pd.read_csv(here/'data-baseline'/'app_orders.csv', index_col=0, parse_dates=[0]).orders
promos=pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24','2026-08-21'])
def features(history):
    idx=history.index
    out=pd.DataFrame(index=idx)
    out['hour'],out['dow']=idx.hour,idx.dayofweek
    out['weekend']=(idx.dayofweek>=5).astype(int)
    out['promo']=(idx.normalize().isin(promos)&(idx.hour>=10)&(idx.hour<=20)).astype(int)
    for k in (48,168):
        out[f'lag_{k}']=history.shift(k)
    out['roll']=history.rolling(24).mean().shift(28)
    out['mean4w']=pd.concat([history.shift(168*k) for k in range(1,5)],axis=1).mean(axis=1)
    return out.dropna()
def rmse(a,b):
    return float(np.sqrt(np.mean(np.square(a-b))))
def human(y,p,capacity):
    need=np.maximum(1,np.ceil(y/capacity))
    plan=np.maximum(1,np.ceil(p/capacity))
    diff=need-plan
    deficit=int(np.maximum(diff,0).sum())
    extra=int(np.maximum(-diff,0).sum())
    return dict(n=len(y),covered=int((y<=p).sum()),short_hours=int((diff>0).sum()),deficit=deficit,extra=extra,
                employee_hours=int(plan.sum()),cost_equal=deficit+extra,cost_three=3*deficit+extra)

X=features(s)
y=s.loc[X.index]
july=X.loc['2026-07']
aug=X.loc['2026-08']
fittable=X.loc[:'2026-07-31 19:00']
out={'versions':dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,sklearn=sklearn.__version__,statsmodels=statsmodels.__version__)}
models={'linear':LinearRegression(),'hgb':HGB(random_state=0),'hgb_depth3':HGB(max_depth=3,random_state=0),'hgb_l2':HGB(l2_regularization=1,random_state=0)}
select={}
for label,model in models.items():
    scores={}
    for end in ('2026-06-30 19:00','2026-06-30 23:00'):
        tr=X.loc[:end]
        yt=y.loc[tr.index]
        disturbed=yt.copy()
        disturbed.loc['2026-06-30 20:00':]+=1000
        pred=model.fit(tr,yt).predict(july)
        shifted=model.fit(tr,disturbed).predict(july)
        scores[end]={'rmse':rmse(y.loc[july.index],pred),'labels':len(yt),'corrupt_last4_mean_abs_change':float(np.abs(shifted-pred).mean())}
    select[label]=scores
out['select']=select
aug_y=y.loc[aug.index]
scorer='neg_root_mean_squared_error'
out['grid']={}
for gap in (0,28):
    gs=GridSearchCV(HGB(random_state=0),dict(max_depth=[2,3,None],learning_rate=[.05,.1]),cv=TimeSeriesSplit(n_splits=3,gap=gap),scoring=scorer)
    gs.fit(fittable,y.loc[fittable.index])
    out['grid'][gap]={'best':gs.best_params_,'rmse':-gs.best_score_}
params=out['grid'][28]['best']
visibility=[]
for date in aug.index.normalize().unique():
    batch=aug.loc[str(date.date())]
    cutoff=date-pd.Timedelta(hours=4)
    concealed=s.mask(s.index>=cutoff)
    future=features(concealed).reindex(batch.index)
    assert len(batch)==24 and future.notna().all().all()
    assert np.allclose(batch,future)
    visibility.append([str(date.date()),len(batch),str(cutoff-pd.Timedelta(hours=1))])
out['visibility']=visibility
predictions={'mean':np.maximum(0,HGB(**params,random_state=0).fit(fittable,y.loc[fittable.index]).predict(aug)),
             'q80':np.maximum(0,HGB(**params,random_state=0,loss='quantile',quantile=.8).fit(fittable,y.loc[fittable.index]).predict(aug)),
             'weeks4':aug.mean4w.to_numpy(),'weeks8':pd.concat([s.shift(168*k) for k in range(1,9)],axis=1).mean(axis=1).reindex(aug.index).to_numpy()}
out['plans']={}
for label,p in predictions.items():
    i=aug.index
    subsets={'open':(i.hour>=7)&(i.hour<=22),'18:00':i.hour==18,'22:00':i.hour==22,'promo':aug.promo.eq(1).to_numpy(),'all':np.ones(len(i),dtype=bool)}
    out['plans'][label]={'august_rmse':rmse(aug_y,p),'subsets':{k:{c:human(aug_y.to_numpy()[mask],p[mask],c) for c in (6,8)} for k,mask in subsets.items()}}
hourly=s['2026-08']
daily=s.resample('D').sum()
phase=np.tile([0,10,20,10],60)+np.random.default_rng(73).normal(0,.2,240)
out['adf']={k:float(adfuller(series)[1]) for k,series in {'august':hourly,'aug_diff24':hourly.diff(24).dropna(),'daily':daily,'daily_diff':daily.diff().dropna(),'phased':phase}.items()}
out['phase_means']=[float(np.mean(phase[j::4])) for j in range(4)]
t=s.loc[:'2026-07-31']
xx=pd.DataFrame({'hour':t.index.hour,'dow':t.index.dayofweek,'weekend':(t.index.dayofweek>=5).astype(int)},index=t.index)
for k in (1,24,168):
    xx[f'lag_{k}']=t.shift(k)
xx['roll_24']=t.shift(1).rolling(24).mean()
xx=xx.dropna()
out['split_example']={}
for shuffle in (False,True):
    tr,te=train_test_split(xx,test_size=.2,shuffle=shuffle,random_state=0 if shuffle else None)
    out['split_example'][str(shuffle)]=dict(time=str(te.index.min()),later=int((tr.index>te.index.min()).sum()),train=len(tr),test=len(te),rmse=rmse(y.loc[te.index],HGB(random_state=0).fit(tr,y.loc[tr.index]).predict(te)))
(here/'expert-model.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
