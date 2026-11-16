import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: os.environ[name]='1'
from pathlib import Path
import argparse,json,time,platform
import numpy as np,pandas as pd,joblib,sklearn
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error
ROOT=Path(__file__).resolve().parent
CATS=['shop_id','format']
def features(s,categories):
 a=s.copy(); a['weekday']=a.date.dt.weekday; a['month']=a.date.dt.month; a['weekend']=(a.weekday>=5).astype(int)
 a['day_n']=(a.date-pd.Timestamp('2024-01-01')).dt.days
 for c in CATS: a[c]=pd.Categorical(a[c],categories=categories[c])
 a['off']=((a.weekend+a.holiday)>0).astype(int)
 a['bc_off']=(a['format']=='бизнес-центр')*a.off; a['mall_off']=(a['format']=='ТЦ')*a.off
 return pd.get_dummies(a[['holiday','promo','weekday','month','weekend','day_n','shop_id','format','bc_off','mall_off']],columns=CATS,dtype=int)
def fit(name,history,categories):
 X=features(history,categories); y=history.revenue_k
 if name=='frozen_week':
  a=history.assign(weekday=history.date.dt.weekday).sort_values('date').groupby(['shop_id','weekday']).tail(1)
  return {'name':name,'lookup':a.set_index(['shop_id','weekday']).revenue_k.to_dict(),'categories':categories}
 if name=='linear_interactions': m=LinearRegression().fit(X,y); trend=None
 else:
  trend=LinearRegression().fit(X[['day_n']],np.log(y))
  target=y/np.exp(trend.predict(X[['day_n']]))
  m=HistGradientBoostingRegressor(max_iter=200,max_depth=3,learning_rate=.05,early_stopping=False,random_state=11).fit(X.drop(columns='day_n'),target)
 return {'name':name,'model':m,'trend':trend,'columns':X.columns.tolist(),'categories':categories}
def predict(bundle,rows):
 if bundle['name']=='frozen_week': return np.array([bundle['lookup'][(r.shop_id,r.date.weekday())] for r in rows.itertuples()])
 X=features(rows,bundle['categories']).reindex(columns=bundle['columns'],fill_value=0)
 if bundle['trend'] is None: return bundle['model'].predict(X)
 trend=np.exp(bundle['trend'].predict(X[['day_n']]))
 return bundle['model'].predict(X.drop(columns='day_n'))*trend

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--predict',type=Path); ap.add_argument('--output',type=Path,default=ROOT/'recomputed.csv'); args=ap.parse_args()
 if args.predict:
  b=joblib.load(ROOT/'model.joblib'); s=pd.read_csv(args.predict,parse_dates=['date'])
  s['prediction_k']=predict(b,s); s.to_csv(args.output,index=False); print(args.output); return
 s=pd.read_csv(ROOT/'data/daily_sales.csv',parse_dates=['date']).sort_values(['date','shop_id']).reset_index(drop=True)
 dev=s[s.date<'2025-04-01']; val=s[(s.date>='2025-04-01')&(s.date<'2025-07-01')]
 history=s[s.date<'2025-07-01']; test=s[s.date>='2025-07-01']
 categories={c:sorted(dev[c].unique()) for c in CATS}
 names=['frozen_week','linear_interactions','trend_hgb']; rows=[]
 for name in names:
  start=time.perf_counter(); m=fit(name,dev,categories); selection_fit_s=time.perf_counter()-start
  p=predict(m,val)
  rows.append({'model':name,'val_rmse_k':float(np.sqrt(mean_squared_error(val.revenue_k,p))),'selection_fit_s':selection_fit_s})
 chosen=min(rows,key=lambda r:r['val_rmse_k'])['model']
 (ROOT/'selection.json').write_text(json.dumps({'as_of':'2025-04-01','metric':'RMSE, thousand RUB','families':names,'chosen':chosen,'weather':'excluded','budget':'3 predeclared families; HGB 200 iterations, depth3, lr.05; one CPU thread','rows':rows},ensure_ascii=False,indent=2))
 final={}
 for row in rows:
  name=row['model']; start=time.perf_counter(); m=fit(name,history,categories); row['final_fit_s']=time.perf_counter()-start
  start=time.perf_counter(); p=predict(m,test); row['predict_ms']=(time.perf_counter()-start)*1000
  row.update(test_rmse_k=float(np.sqrt(mean_squared_error(test.revenue_k,p))),test_mae_k=float(mean_absolute_error(test.revenue_k,p)),bias_k=float(np.mean(test.revenue_k-p)))
  final[name]=(m,p)
 bundle,p=final[chosen]; joblib.dump(bundle,ROOT/'model.joblib')
 plan=test[['date','shop_id']].copy(); plan['prediction_k']=p; plan.to_csv(ROOT/'plan.csv',index=False)
 request=test.drop(columns=['revenue_k','temp','rain']); request.to_csv(ROOT/'request.csv',index=False)
 table=pd.DataFrame(rows).set_index('model').sort_values('val_rmse_k'); table.to_csv(ROOT/'metrics.csv')
 # Независимый пересчёт одиночной строки и целого пакета из сохранённого артефакта.
 loaded=joblib.load(ROOT/'model.joblib'); check=predict(loaded,request); one=predict(loaded,request.iloc[[0]])
 assert np.allclose(check,p) and np.allclose(one,p[:1])
 print('chosen by validation:',chosen); print(table.to_string()); print('reloaded model and single-row agreement: OK')
 (ROOT/'versions.json').write_text(json.dumps({'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__,'threads':1},indent=2))
if __name__=='__main__': main()
