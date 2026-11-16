import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
s=pd.read_csv('site/data/app_orders.csv',parse_dates=['datetime'],index_col='datetime').orders
x=pd.DataFrame(index=s.index)
x['hour']=x.index.hour;x['dow']=x.index.dayofweek;x['weekend']=(x.dow>=5).astype(int)
x['promo']=(x.index.normalize().isin(pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24','2026-08-21'])) & x.hour.between(10,20)).astype(int)
for k in [48,168]: x[f'lag_{k}']=s.shift(k)
x['roll']=s.shift(28).rolling(24).mean()
hist=pd.concat([s.shift(k*168) for k in range(1,5)],axis=1)
x['mean4w']=hist.mean(axis=1);x=x.dropna()
print('Доступны n недель в начале обучения:',hist.count(axis=1).loc[x.index].value_counts().sort_index().to_dict())
test=x.loc['2026-08']; y=s.loc[test.index].to_numpy(); ix=test.hour.between(7,22)
for asof in ['2026-07-31 23:00','2026-07-31 19:00']:
 train=x.loc[:asof]
 for q in [0,0.8]:
  model=HistGradientBoostingRegressor(max_depth=3,learning_rate=.05,random_state=0,**({'loss':'quantile','quantile':q} if q else {})).fit(train,s.loc[train.index])
  p=model.predict(test).clip(0)
  needed=np.maximum(1,np.ceil(y[ix]/6)); plan=np.maximum(1,np.ceil(p[ix]/6))
  print(asof,q,'n=',len(y[ix]),'RMSE=',np.sqrt(np.mean((p-y)**2)),'дефицит-часы',int(sum(needed>plan)),'человеко-часы нехватки',sum(np.maximum(needed-plan,0)),'лишние',sum(np.maximum(plan-needed,0)),'покрытие',np.mean(y<=p),'в часы работы',np.mean(y[ix]<=p[ix]))
