from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.linear_model import LinearRegression

repo=Path(__file__).resolve().parents[3]
rows=[json.loads(i) for i in Path(__file__).with_name('student.jsonl').read_text().splitlines()]
submitted={r['id']:r['code'] for r in rows if r['lesson']=='05-project' and 'code' in r}
s=pd.read_csv(repo/'site/data/app_orders.csv',parse_dates=['datetime'],index_col='datetime').orders
def make(s):
    idx=s.index
    df=pd.DataFrame({'y':s,'hour':idx.hour,'dow':idx.dayofweek,'weekend':(idx.dayofweek>=5).astype(int)})
    df['promo']=(idx.normalize().isin(pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24','2026-08-21'])) & (idx.hour>=10) & (idx.hour<=20)).astype(int)
    for j in [48,168]:
        df[f'lag_{j}']=s.shift(j)
    df['roll_24']=s.shift(28).rolling(24).mean()
    df['mean4w']=pd.concat([s.shift(168*j) for j in range(1,5)],axis=1).mean(axis=1)
    return df.dropna()

import os
os.chdir(repo/"site/data")
for stage,code in submitted.items():
    if stage=='grid':fit_mask=train|valid
    if stage=='staffing':
        y_test=y[test]
        open_hours=(y_test.index.hour>=7)&(y_test.index.hour<=22)
    exec(code,globals())
print(sizes,valid_rmse,best_params,cv_rmse,rmse_base,rmse_final,meets)
print(plans,coverage,short_q,extra_q)
last_known=pd.Timestamp('2026-07-31 19:00')
print('unavailable train hours',X.index[(train|valid)&(X.index>last_known)].tolist())
early=X.index<=last_known
m=HistGradientBoostingRegressor(random_state=0,**best_params).fit(X[early],y[early])
first_day=X.index.normalize()==pd.Timestamp('2026-08-01')
a1=np.clip(m.predict(X[first_day]),0,None)
print('first day mean absolute difference',np.abs(a1-pred_test[:24]).mean())
daily=s.resample('D').sum().resample('MS').mean()
print(pd.DataFrame({'raw':(daily.pct_change()*100).round(1),'rounded':(daily.round(1).pct_change()*100).round(1)}))
t=pd.Timestamp('2026-07-15 12:00')
bad=s.copy()
bad.loc[t]+=1000
print('lead current-only check',s.shift(-1).loc[t],bad.shift(-1).loc[t])
bad.loc[t:]+=1000
print('lead tail check',s.shift(-1).loc[t],bad.shift(-1).loc[t])
