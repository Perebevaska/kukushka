from pathlib import Path
import hashlib,json,platform
import numpy as np,pandas as pd,matplotlib.pyplot as plt,joblib,sklearn
from scipy.stats import fisher_exact
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import GroupKFold,cross_validate,cross_val_predict
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss
from .features import *
CUTS=['2025-09-30','2025-12-31','2026-03-31']
ECON={'save_rate':.5,'margin':.35,'months':12,'contact_cost':1500,'discount':.2,'call_limit':150}
def make_models():
 def pre(scale=True):
  num=make_pipeline(SimpleImputer(strategy='median'),StandardScaler()) if scale else SimpleImputer(strategy='median')
  return ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT),('num',num,NUM)])
 return {'dummy':make_pipeline(pre(),DummyClassifier(strategy='prior')),'logreg':make_pipeline(pre(),LogisticRegression(max_iter=2000)),'boosting':make_pipeline(pre(False),HistGradientBoostingClassifier(max_depth=3,learning_rate=.05,max_iter=200,random_state=42)),'knn':make_pipeline(pre(),KNeighborsClassifier(n_neighbors=25))}
def expected(frame,p,save=.5):
 R=frame.revenue_90/3
 return pd.Series(np.asarray(p)*save*.35*12*R.to_numpy()-1500-.2*R.to_numpy(),index=frame.index)
def choose(frame,p,save=.5,limit=150):
 v=frame[['client_id','city']].copy();v['p_churn']=np.asarray(p);v['exp_profit']=expected(frame,p,save)
 return v[v.exp_profit>0].sort_values(['exp_profit','client_id'],ascending=[False,True]).head(limit)
def realized(frame,idx,save=.5):return float(expected(frame.loc[idx],frame.loc[idx,'churn'],save).sum())
def develop(root=Path('.')):
 root=Path(root);out=root/'reports';out.mkdir(exist_ok=True);tables=read_tables(root/'data/office.db')
 audit={n:len(f) for n,f in tables.items()};audit.update(n_test=int(tables['clients'].is_test.sum()),duplicates_tickets=int(tables['tickets'].ticket_id.duplicated().sum()),returns=int((tables['orders'].status=='возврат').sum()),missing_industry=int(tables['clients'].industry.isna().sum()))
 train=pd.concat([snapshot(tables,c,True) for c in CUTS],ignore_index=True);train.to_csv(out/'development.csv',index=False)
 rates=train.groupby('cutoff').churn.agg(n='size',rate='mean');rates.to_csv(out/'development-rates.csv');print('AUDIT',audit,'TRAIN',train.shape,train.client_id.nunique());print(rates)
 for col in ['city','plan']:
  tab=train.groupby(col).churn.agg(rate='mean',n='size');tab.to_csv(out/f'churn-by-{col}.csv')
  ax=tab.rate.plot.bar(figsize=(7,4));ax.set_xticklabels([f'{i} (n={int(r.n)})' for i,r in tab.iterrows()],rotation=20);ax.set(title=f'Уход за квартал по {col}: ранние срезы',ylabel='Доля уходов',xlabel=col);plt.tight_layout();plt.savefig(out/f'churn-by-{col}.png');plt.close()
 ax=train.boxplot(column='orders_90',by='churn',figsize=(7,4));ax.set(title='Заказы за90дней; ранние срезы n='+str(len(train)),xlabel='Наблюдаемый churn',ylabel='Число заказов');plt.suptitle('');plt.tight_layout();plt.savefig(out/'orders-by-churn.png');plt.close()
 last=train[train.cutoff==CUTS[-1]];ct=pd.crosstab(last.city=='Уфа',last.churn);odds,pval=fisher_exact(ct)
 hypothesis={'cutoff':CUTS[-1],'hypothesis':'Частота ухода в Уфе равна остальным городам','n':len(last),'contingency':ct.to_dict(),'odds_ratio':float(odds),'p_value':float(pval),'limitation':'Наблюдательная ассоциация; один квартал, без причинной идентификации.'};(out/'hypothesis.json').write_text(json.dumps(hypothesis,ensure_ascii=False,indent=2));print('HYPOTHESIS',hypothesis)
 assert build_target(tables,'2026-09-30').isna().all()
 before=build_features(tables,'2025-12-31');mutated={k:v.copy() for k,v in tables.items()};mask=pd.to_datetime(mutated['orders'].order_date)>pd.Timestamp('2025-12-31');mutated['orders'].loc[mask,'amount']*=1000;pd.testing.assert_frame_equal(before,build_features(mutated,'2025-12-31'))
 X=train[FEATURES];y=train.churn;groups=train.client_id;folds=list(GroupKFold(5).split(X,y,groups));assert all(set(groups.iloc[a]).isdisjoint(groups.iloc[b]) for a,b in folds)
 pd.DataFrame([(i,len(a),len(b)) for i,(a,b) in enumerate(folds)],columns=['fold','train_n','valid_n']).to_csv(out/'folds.csv',index=False)
 models=make_models();rows=[]
 for name,m in models.items():
  scores=cross_validate(m,X,y,cv=folds,scoring={'auc':'roc_auc','ap':'average_precision'},n_jobs=1)
  for i in range(5):rows.append({'model':name,'fold':i,'roc_auc':float(scores['test_auc'][i]),'average_precision':float(scores['test_ap'][i])})
 cv=pd.DataFrame(rows);cv.to_csv(out/'cv-folds.csv',index=False);print(cv.groupby('model')[['roc_auc','average_precision']].agg(['mean','std']))
 means=cv.groupby('model').roc_auc.mean();winner=means.drop('dummy').idxmax()
 if means[winner]-means.logreg<.005:winner='logreg'
 p=cross_val_predict(models[winner],X,y,cv=folds,method='predict_proba',n_jobs=1)[:,1]
 oof=train[['client_id','cutoff','churn','city','revenue_90']].copy();oof['p']=p;oof.to_csv(out/'oof.csv',index=False)
 cal=oof.groupby(pd.qcut(p,5,duplicates='drop'),observed=True).agg(n=('p','size'),mean_p=('p','mean'),observed=('churn','mean'));cal.to_csv(out/'calibration-oof.csv');print('OOF CALIBRATION',cal,'BRIER',brier_score_loss(y,p))
 money=[]
 for c,f in train.assign(p=p).groupby('cutoff'):
  calls=choose(f,f.p);money.append({'cutoff':c,'n_calls':len(calls),'expected':float(calls.exp_profit.sum()),'conditional_observed':realized(f,calls.index)})
 pd.DataFrame(money).to_csv(out/'development-money.csv',index=False);print('PAST MONEY',money)
 if winner=='logreg':
  selected=clone(models[winner]).fit(X,y);pre=selected.steps[0][1];lr=selected.steps[-1][1];pd.Series(lr.coef_[0],index=pre.get_feature_names_out()).sort_values().to_csv(out/'coefficients.csv')
 decision={'chosen':winner,'criterion':'meanGroupKFoldROCAUC;preferLogRegwithin.005','cv':{k:float(v) for k,v in means.items()},'oof_brier':float(brier_score_loss(y,p)),'probabilities':'raw;OOF inspected,no adjustment selected','policy':ECON,'test_opened':False,'features':FEATURES,'data_md5':hashlib.md5((root/'data/office.db').read_bytes()).hexdigest()};(root/'selection-before-test.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2));joblib.dump({'train':train,'folds':folds,'decision':decision},out/'development-state.joblib');return decision

def evaluate(root=Path('.')):
 root=Path(root);out=root/'reports';state=joblib.load(out/'development-state.joblib');train=state['train'];decision=state['decision'];tables=read_tables(root/'data/office.db');test=snapshot(tables,'2026-06-30',True)
 m=make_models()[decision['chosen']].fit(train[FEATURES],train.churn);p=m.predict_proba(test[FEATURES])[:,1];test['p']=p;calls=choose(test,p);idx=calls.index
 metrics={'roc_auc':float(roc_auc_score(test.churn,p)),'average_precision':float(average_precision_score(test.churn,p)),'brier':float(brier_score_loss(test.churn,p)),'n':len(test),'churn_rate':float(test.churn.mean()),'mean_p':float(p.mean()),'n_calls':len(calls),'caught':int(test.loc[idx,'churn'].sum()),'expected':float(calls.exp_profit.sum()),'conditional_profit':realized(test,idx),'rule_profit':realized(test,test.sort_values(['revenue_trend','client_id']).head(150).index),'all_profit':realized(test,test.index),'no_calls':0}
 test['known']=test.client_id.isin(train.client_id);sub=[]
 for known,f in test.groupby('known'):
  ix=f.index.intersection(idx);sub.append({'known':bool(known),'n':len(f),'rate':float(f.churn.mean()),'mean_p':float(f.p.mean()),'queue_n':len(ix),'queue_mean_p':float(f.loc[ix,'p'].mean()),'queue_churn_rate':float(f.loc[ix,'churn'].mean())})
 pd.DataFrame(sub).to_csv(out/'test-known-new.csv',index=False);sens=[]
 for s in [.3,.5,.7]:
  changed=choose(test,p,save=s);sens.append({'save_rate':s,'fixed_profit':realized(test,idx,s),'reselected_n':len(changed),'reselected_profit':realized(test,changed.index,s)})
 pd.DataFrame(sens).to_csv(out/'sensitivity.csv',index=False);test.to_csv(out/'heldout.csv',index=False);calls.to_csv(out/'heldout-calls-full.csv',index=False);(out/'test-metrics.json').write_text(json.dumps(metrics,indent=2));print('FROZEN CHOICE',decision['chosen'],'TEST',metrics,'KNOWN/NEW',sub,'SENSITIVITY',sens);return metrics

def package(root=Path('.')):
 root=Path(root);out=root/'reports';state=joblib.load(out/'development-state.joblib');train=state['train'];decision=state['decision'];test=pd.read_csv(out/'heldout.csv');tables=read_tables(root/'data/office.db');alltrain=pd.concat([train,test],ignore_index=True)
 model=make_models()[decision['chosen']].fit(alltrain[FEATURES],alltrain.churn);final=build_features(tables,'2026-09-30');p=model.predict_proba(final)[:,1];work=final.reset_index();calls=choose(work,p);art=root/'models/office_churn/1.0';art.mkdir(parents=True,exist_ok=True);joblib.dump(model,art/'model.joblib')
 golden=final.iloc[:20].copy();golden['expected']=model.predict_proba(golden)[:,1];golden.reset_index().to_csv(art/'golden.csv',index=False);loaded=joblib.load(art/'model.joblib');gold=pd.read_csv(art/'golden.csv');diff=float(np.abs(loaded.predict_proba(gold[FEATURES])[:,1]-gold.expected).max());assert diff<1e-9
 shown=calls.copy();shown.p_churn=shown.p_churn.round(3);shown.exp_profit=shown.exp_profit.round().astype(int);shown.to_csv(out/'call_list_2026-09-30.csv',index=False)
 card={'model':decision['chosen'],'version':'1.0','cutoff':'2026-09-30','data_asof':'2026-09-30','features':FEATURES,'feature_types':{c:str(final[c].dtype) for c in FEATURES},'categories':{c:sorted(final[c].unique().tolist()) for c in CAT},'train_rows':len(alltrain),'data_md5':decision['data_md5'],'python':platform.python_version(),'sklearn':sklearn.__version__,'cv':decision['cv'],'test':json.loads((out/'test-metrics.json').read_text()),'economics':ECON,'call_limit':150,'n_calls':len(calls),'expected_profit':round(float(calls.exp_profit.sum())),'threshold':'per-client exp>0;rankexpdescending,client_idascending','golden_tolerance':1e-9,'golden_max_diff':diff,'probability_calibration':'raw;groupOOF inspected;futurecalibrationmaydrift','target':'activeatcutoff,endsbycutoff+MonthEnd3;unknownafterextract','feature_window':'(cutoff-90d,cutoff],previous90d;due<=cutoff;paymentaftercutoffunknown','full_precision_profit_sum':float(calls.exp_profit.sum())}
 (art/'passport.json').write_text(json.dumps(card,ensure_ascii=False,indent=2));work['known']=work.client_id.isin(alltrain.client_id);pd.DataFrame({'known':work.known,'p':p}).groupby('known').agg(n=('p','size'),mean_p=('p','mean')).to_csv(out/'working-known-new.csv');print('PACKAGE',len(final),len(calls),card['expected_profit'],'goldendiff',diff);return card
