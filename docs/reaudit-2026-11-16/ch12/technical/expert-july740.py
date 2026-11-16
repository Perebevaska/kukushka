"""Корректное окно оценивания при фиксации решения 31 июля в 20:00."""
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

here = Path(__file__).resolve().parent
s = pd.read_csv(here / 'data-baseline' / 'app_orders.csv', parse_dates=['datetime'], index_col='datetime').orders
idx = s.index
cal = pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24','2026-08-21'])
weekly = pd.concat([s.shift(168*k) for k in range(1,9)], axis=1)
X = pd.DataFrame(dict(hour=idx.hour, dow=idx.dayofweek, weekend=(idx.dayofweek>=5).astype(int),
                      promo=(idx.normalize().isin(cal) & (idx.hour>=10) & (idx.hour<=20)).astype(int),
                      lag_48=s.shift(48), lag_168=s.shift(168), roll=s.shift(28).rolling(24).mean(),
                      mean4w=weekly.iloc[:,:4].mean(axis=1)), index=idx).dropna()
development = X.loc[:'2026-06-30 19:00']
july = X.loc['2026-07']
known = july.index < pd.Timestamp('2026-07-31 20:00')
y = s.loc[july.index]
spoiled = y.copy()
spoiled.loc[~known] += 1000
assert len(development)==2756 and len(y)==744 and sum(known)==740
def rmse(actual,pred):
    return float(np.sqrt(np.square(actual-pred).mean()))
def scores(p):
    result = dict(valid_740=rmse(y[known],p[known]),retrospective_744=rmse(y,p),
                  disturbed_740=rmse(spoiled[known],p[known]),disturbed_744=rmse(spoiled,p))
    assert result['valid_740']==result['disturbed_740']
    assert result['retrospective_744']!=result['disturbed_744']
    return result
models = dict(linear=LinearRegression(),hgb=HistGradientBoostingRegressor(random_state=0),
              hgb_depth3=HistGradientBoostingRegressor(random_state=0,max_depth=3),
              hgb_l2=HistGradientBoostingRegressor(random_state=0,l2_regularization=1.0))
out = dict(versions=dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,sklearn=sklearn.__version__),
           fit=[str(development.index[0]),str(development.index[-1]),len(development)],
           score=[str(july.index[known][0]),str(july.index[known][-1]),int(known.sum())])
out['models']={k:scores(m.fit(development,s.loc[development.index]).predict(july)) for k,m in models.items()}
out['weeks']={k:scores(weekly.loc[july.index].iloc[:,:k].mean(axis=1)) for k in [1,2,4,8]}
(here/'expert-july740.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
