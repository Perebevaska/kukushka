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

RECIPE={'name':'trend_hgb','max_iter':200,'max_depth':3,'learning_rate':.05,'random_state':11,'weather':'excluded','origin':'2024-01-01'}
def validate_request(request,as_of):
    required=['date','shop_id','format','holiday','promo']
    if any(c not in request for c in required): raise ValueError('Required columns: '+str(required))
    if request[required].isna().any().any(): raise ValueError('Request contains missing required values')
    if request.duplicated(['date','shop_id']).any(): raise ValueError('Duplicate forecast keys')
    if (request.date<pd.Timestamp(as_of)).any(): raise ValueError('Forecast date precedes issue date')
def plan_frame(bundle,request,as_of):
    validate_request(request,as_of)
    plan=request[['date','shop_id']].copy(); plan.insert(0,'as_of',str(as_of))
    plan['prediction_k']=predict(bundle,request)
    return plan
def make_issue(source,request,as_of):
    history=source.loc[source.date<pd.Timestamp(as_of)].copy()
    if history.empty: raise ValueError('No completed-day history before issue')
    categories={c:sorted(history[c].unique()) for c in CATS}
    start=time.perf_counter(); bundle=fit('trend_hgb',history,categories); fit_s=time.perf_counter()-start
    start=time.perf_counter(); plan=plan_frame(bundle,request,as_of); predict_ms=(time.perf_counter()-start)*1000
    metadata={'as_of':as_of,'last_available_observation':str(history.date.max().date()),'history_rows':len(history),'horizon_start':str(request.date.min().date()),'horizon_end':str(request.date.max().date()),'recipe':RECIPE,'selection':'Fixed previous own recipe; no new selection on final period','weather':'Excluded; no scenario or future weather consumed','calendar':'Request holiday/promo assumed approved at issue; source has no approval log','keys':['date','shop_id'],'units':'thousand RUB per shop-day','fit_s':fit_s,'predict_ms':predict_ms,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__},'threads':1}
    return bundle,plan,metadata

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='mode',required=True)
    saved=sub.add_parser('saved'); saved.add_argument('--model',type=Path,default=Path('model.joblib')); saved.add_argument('--metadata',type=Path,default=Path('metadata.json')); saved.add_argument('--request',type=Path,required=True); saved.add_argument('--output',type=Path,required=True)
    issue=sub.add_parser('issue'); issue.add_argument('--as-of',required=True); issue.add_argument('--history',type=Path,required=True); issue.add_argument('--request',type=Path,required=True); issue.add_argument('--output',type=Path,required=True); issue.add_argument('--model-out',type=Path,required=True); issue.add_argument('--metadata-out',type=Path,required=True); issue.add_argument('--verify-future-invariance',action='store_true')
    args=ap.parse_args(); request=pd.read_csv(args.request,parse_dates=['date'])
    if args.mode=='saved':
        metadata=json.loads(args.metadata.read_text()); bundle=joblib.load(args.model)
        plan=plan_frame(bundle,request,metadata['as_of']); plan.to_csv(args.output,index=False)
        print('saved model: no fit; rows',len(plan),'as_of',metadata['as_of']);return
    source=pd.read_csv(args.history,parse_dates=['date'])
    # Protocol is created outside this command before first fit. Only completed history enters make_issue.
    bundle,plan,metadata=make_issue(source,request,args.as_of)
    if args.verify_future_invariance:
        mutated=source.copy(); future=mutated.date>=pd.Timestamp(args.as_of)
        mutated.loc[future,'revenue_k']=mutated.loc[future,'revenue_k']*1000+12345
        mutated['temp']=mutated['temp'].astype(float); mutated.loc[future,'temp']=-999.
        mutated.loc[future,'rain']=1-mutated.loc[future,'rain']
        _,changed,_=make_issue(mutated,request,args.as_of)
        assert np.allclose(plan.prediction_k,changed.prediction_k,atol=1e-9,rtol=0)
        metadata['future_fact_mutation_check']='passed: future revenue/weather changed, calendar/request unchanged, max delta <=1e-9'
    joblib.dump(bundle,args.model_out); plan.to_csv(args.output,index=False)
    args.metadata_out.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('new issue: fixed recipe',args.as_of,'rows',len(plan),'history through',metadata['last_available_observation'])
    print(json.dumps(metadata,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
