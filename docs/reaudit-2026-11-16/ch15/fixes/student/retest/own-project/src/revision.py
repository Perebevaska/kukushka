"""Own PS15 revision. All diagnostic CV uses only pre-June development rows.
No model selection or refitting of the released model occurs here.
"""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score,average_precision_score
from .features import *
from .analysis import choose,expected,realized,CUTS


def trend_and_transfer(root=Path('.')):
 root=Path(root);out=root/'reports/revision';out.mkdir(exist_ok=True)
 pairs=[(100,50),(-5,3),(-1,0)];values=[float(revenue_trend(a,b)) for a,b in pairs]
 assert np.allclose(values,[50/151,8,0]);assert np.isfinite(values).all()
 pd.DataFrame({'recent':[a for a,b in pairs],'previous':[b for a,b in pairs],'trend':values}).to_csv(out/'trend-boundaries.csv',index=False)
 tables=read_tables(root/'data/office.db');finite=[]
 # Integration through the actual common feature builder with one -1 return.
 integration={k:v.copy() for k,v in tables.items()}
 probe_id=build_features(tables,'2026-09-30').index[0]
 probe=tables['orders'].iloc[0].copy()
 probe['client_id']=probe_id;probe['order_id']='BOUNDARY-RETURN';probe['order_date']='2026-09-30';probe['amount']=-1;probe['status']='возврат'
 integration['orders']=pd.concat([integration['orders'].loc[integration['orders'].client_id!=probe_id],pd.DataFrame([probe])],ignore_index=True)
 integrated=build_features(integration,'2026-09-30').loc[[probe_id]]
 assert integrated.iloc[0].revenue_90 == -1
 assert integrated.iloc[0].revenue_trend == 0
 integrated.to_csv(out/'trend-boundary-feature-row.csv')
 for c in CUTS+['2026-06-30','2026-09-30']:
  f=build_features(tables,c);assert np.isfinite(f[NUM].to_numpy()).all();finite.append({'cutoff':c,'rows':len(f),'all_numeric_finite':True})
 pd.DataFrame(finite).to_csv(out/'finite-inputs.csv',index=False)
 # Score the unchanged release. Preprocessing also receives the pathological boundary row.
 art=root/'models/office_churn/1.0';model=joblib.load(art/'model.joblib');card=json.loads((art/'passport.json').read_text());f=build_features(tables,'2026-09-30')
 pathological=integrated;transformed=model.steps[0][1].transform(pathological)
 if hasattr(transformed,'toarray'):transformed=transformed.toarray()
 assert np.isfinite(transformed).all()
 p=model.predict_proba(f)[:,1];work=f.reset_index();calls=choose(work,p)
 shown=calls.copy();shown.p_churn=shown.p_churn.round(3);shown.exp_profit=shown.exp_profit.round().astype(int)
 pd.testing.assert_frame_equal(shown.reset_index(drop=True),pd.read_csv(root/'reports/call_list_2026-09-30.csv'))
 assert len(calls)==card['n_calls'];assert round(float(calls.exp_profit.sum()))==card['expected_profit']
 gold=pd.read_csv(art/'golden.csv');difference=float(np.max(np.abs(model.predict_proba(gold[FEATURES])[:,1]-gold.expected)));assert difference<1e-9
 result={'pairs':pairs,'values':values,'numeric_finite_all_cuts':True,'boundary_preprocessing_finite':True,'original_list_rows':len(calls),'passport_sum':card['expected_profit'],'golden_max_difference':difference,'model_sha256':hashlib.sha256((art/'model.joblib').read_bytes()).hexdigest(),'data_sha256':hashlib.sha256((root/'data/office.db').read_bytes()).hexdigest()}
 (out/'trend-transfer.json').write_text(json.dumps(result,indent=2));print('TREND/TRANSFER',result);return result


def single_feature_diagnostics(root=Path('.')):
 root=Path(root);out=root/'reports/revision';state=joblib.load(root/'reports/development-state.joblib');train=state['train'];folds=state['folds']
 assert set(train.cutoff)==set(CUTS)
 rows=[]
 for feat in FEATURES:
  for i,(a,b) in enumerate(folds):
   if feat in CAT:
    prep=OneHotEncoder(handle_unknown='ignore',sparse_output=False)
   else:prep=make_pipeline(SimpleImputer(strategy='median'),StandardScaler())
   m=make_pipeline(prep,LogisticRegression(max_iter=2000)).fit(train.iloc[a][[feat]],train.iloc[a].churn)
   p=m.predict_proba(train.iloc[b][[feat]])[:,1]
   row={'feature':feat,'fold':i,'roc_auc':float(roc_auc_score(train.iloc[b].churn,p)),'average_precision':float(average_precision_score(train.iloc[b].churn,p)),'n_valid':len(b)}
   if feat not in CAT:
    coefficient=float(m.steps[-1][1].coef_[0,0]);row.update(coefficient=coefficient,direction='higher risk' if coefficient>0 else 'lower risk',raw_auc=float(roc_auc_score(train.iloc[b].churn,train.iloc[b][feat].fillna(train.iloc[a][feat].median()))))
   else:
    row.update(coefficient=None,direction='category effects, not ordered',raw_auc=None)
   rows.append(row)
 full=pd.DataFrame(rows);summary=full.groupby('feature').agg(roc_auc_mean=('roc_auc','mean'),roc_auc_sd=('roc_auc','std'),ap_mean=('average_precision','mean'),raw_auc_mean=('raw_auc','mean'),positive_folds=('coefficient',lambda v:int((v>0).sum())),negative_folds=('coefficient',lambda v:int((v<0).sum()))).sort_values('roc_auc_mean',ascending=False)
 full.to_csv(out/'single-feature-folds.csv',index=False);summary.to_csv(out/'single-feature-summary.csv');print('SINGLE FEATURES',summary)
 # Availability evidence for the actual strongest signal, orders_90.
 strongest=summary.index[0]
 tables=clean_tables(read_tables(root/'data/office.db'));evidence=[];checks=[]
 for c in CUTS:
  cut=pd.Timestamp(c);ids=build_features(read_tables(root/'data/office.db'),c).index
  order=tables['orders'];used=order.loc[order.client_id.isin(ids)&(order.status!='отменён')&(order.order_date>cut-pd.Timedelta(days=90))&(order.order_date<=cut)].copy()
  used=used.merge(tables['clients'][['client_id','created_at']].rename(columns={'created_at':'client_at'}),on='client_id').merge(tables['contracts'][['client_id','start_date']],on='client_id');used['cutoff']=c;evidence.append(used)
  checks.append({'cutoff':c,'feature':strongest,'rows':len(used),'offices_with_orders':int(used.client_id.nunique()),'min_event':str(used.order_date.min().date()),'max_event':str(used.order_date.max().date()),'events_after_cutoff':int((used.order_date>cut).sum()),'events_before_client':int((used.order_date<used.client_at).sum()),'events_before_contract':int((used.order_date<used.start_date).sum()),'available_by_event_date':True,'ingestion_timestamp_observed':False})
 pd.concat(evidence,ignore_index=True).to_csv(out/'strongest-signal-order-evidence.csv',index=False)
 pd.DataFrame(checks).to_csv(out/'strongest-signal-availability.csv',index=False)
 print('STRONGEST SIGNAL DATES',pd.DataFrame(checks))
 return summary


def tickets_availability(root=Path('.')):
 root=Path(root);out=root/'reports/revision';tables=read_tables(root/'data/office.db');t=clean_tables(tables)
 raw=tables['tickets'];dups=raw[raw.ticket_id.duplicated(False)]
 meaningful=[c for c in raw.columns if c!='ticket_id'];conflicts=dups.groupby('ticket_id')[meaningful].nunique(dropna=False).gt(1).any(axis=1)
 (out/'ticket-duplicate-conflicts.json').write_text(json.dumps({'duplicate_extra_rows':int(raw.ticket_id.duplicated().sum()),'duplicate_ids':len(conflicts),'conflicting_ids':conflicts[conflicts].index.tolist()},ensure_ascii=False,indent=2))
 joined=t['tickets'].rename(columns={'created_at':'ticket_at'}).merge(t['clients'][['client_id','created_at']].rename(columns={'created_at':'client_at'}),on='client_id').merge(t['contracts'][['client_id','start_date']],on='client_id')
 joined['A']=joined.ticket_at<joined.client_at;joined['B']=(joined.client_at<=joined.ticket_at)&(joined.ticket_at<joined.start_date)
 joined.to_csv(out/'ticket-availability-all.csv',index=False)
 joined[joined.A|joined.B][['ticket_id','client_id','ticket_at','client_at','start_date','A','B','category']].to_csv(out/'ticket-availability-flags.csv',index=False)
 counts={flag:{'tickets':int(joined[flag].sum()),'offices':int(joined.loc[joined[flag],'client_id'].nunique())} for flag in ['A','B']}
 counts['A_or_B']={'tickets':int((joined.A|joined.B).sum()),'offices':int(joined.loc[joined.A|joined.B,'client_id'].nunique())}
 comparisons=[];details=[]
 for variant,mask in [('without_A',joined.A),('without_A_B',joined.A|joined.B)]:
  changed={k:v.copy() for k,v in tables.items()};remove=joined.loc[mask,'ticket_id'];changed['tickets']=changed['tickets'].loc[~changed['tickets'].ticket_id.isin(remove)]
  for c in CUTS+['2026-06-30','2026-09-30']:
   before=build_features(tables,c);after=build_features(changed,c)
   assert before.index.equals(after.index)
   diff=after[['tickets_90','tickets_bill_90']]-before[['tickets_90','tickets_bill_90']]
   altered=diff.ne(0).any(axis=1)
   # Explicitly count removed events that lie inside these active offices' window.
   event_rows=joined.loc[mask&joined.client_id.isin(before.index)&(joined.ticket_at>pd.Timestamp(c)-pd.Timedelta(days=90))&(joined.ticket_at<=pd.Timestamp(c))]
   comparisons.append({'variant':variant,'cutoff':c,'offices_changed':int(altered.sum()),'removed_events_in_window':len(event_rows),'tickets_90_delta':int(diff.tickets_90.sum()),'tickets_bill_90_delta':int(diff.tickets_bill_90.sum())})
   for id_ in before.index[altered]:details.append({'variant':variant,'cutoff':c,'client_id':id_,'before_tickets_90':int(before.loc[id_,'tickets_90']),'after_tickets_90':int(after.loc[id_,'tickets_90']),'before_tickets_bill_90':int(before.loc[id_,'tickets_bill_90']),'after_tickets_bill_90':int(after.loc[id_,'tickets_bill_90'])})
   # Save both entire aligned alternative count tables, even if no rows changed.
   before[['tickets_90','tickets_bill_90']].join(after[['tickets_90','tickets_bill_90']],lsuffix='_original',rsuffix='_'+variant).to_csv(out/f'ticket-counts_{c}_{variant}.csv')
 pd.DataFrame(comparisons).to_csv(out/'ticket-count-comparison.csv',index=False)
 pd.DataFrame(details,columns=['variant','cutoff','client_id','before_tickets_90','after_tickets_90','before_tickets_bill_90','after_tickets_bill_90']).to_csv(out/'ticket-count-changed-offices.csv',index=False)
 # Save the raw events actually used for the strongest count signal, before June only.
 evidence=[]
 for c in CUTS:
  active=build_features(tables,c).index
  events=joined.loc[joined.client_id.isin(active)&(joined.ticket_at>pd.Timestamp(c)-pd.Timedelta(days=90))&(joined.ticket_at<=pd.Timestamp(c))].copy();events['cutoff']=c;evidence.append(events)
 pd.concat(evidence,ignore_index=True).to_csv(out/'development-ticket-evidence.csv',index=False)
 (out/'ticket-availability-summary.json').write_text(json.dumps(counts,indent=2));print('TICKET FLAGS',counts);print(pd.DataFrame(comparisons));return counts


def future_event_check(root=Path('.')):
 root=Path(root);out=root/'reports/revision';tables=read_tables(root/'data/office.db');cut='2025-12-31';c=pd.Timestamp(cut);before=build_features(tables,cut);result=[]
 for name,datecol,field in [('orders','order_date','amount'),('tickets','created_at','category'),('invoices','paid_date','paid_date')]:
  copy={k:v.copy() for k,v in tables.items()};frame=copy[name]
  elig=(pd.to_datetime(frame[datecol])>c)&frame.client_id.isin(before.index)
  if name=='invoices':elig &= pd.to_datetime(frame.due_date)<=c
  i=frame.index[elig][0];id_=frame.loc[i,'client_id'];old=frame.loc[i,field]
  new=float(old)+999999 if field=='amount' else ('другое' if field=='category' else (pd.Timestamp(old)+pd.Timedelta(days=1)).date().isoformat())
  frame.loc[i,field]=new;after=build_features(copy,cut)
  pd.testing.assert_frame_equal(before,after)
  assert np.isfinite(after[NUM].to_numpy()).all()
  result.append({'table':name,'client_id':id_,'event_row':int(i),'date':str(frame.loc[i,datecol]),'field':field,'old':str(old),'new':str(new),'all_feature_rows_unchanged':True,'checked_row':id_})
 (out/'future-event-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('FUTURE MUTATIONS',result);return result


def industry_analysis(root=Path('.')):
 root=Path(root);out=root/'reports/revision';state=joblib.load(root/'reports/development-state.joblib');train=state['train'];cat=[c for c in CAT if c!='industry']
 pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),cat),('num',make_pipeline(SimpleImputer(strategy='median'),StandardScaler()),NUM)])
 m=make_pipeline(pre,LogisticRegression(max_iter=2000));scores=cross_val_score(m,train[cat+NUM],train.churn,cv=state['folds'],scoring='roc_auc',n_jobs=1)
 result={'without_industry_folds':scores.tolist(),'without_industry_mean':float(scores.mean()),'with_industry_mean':state['decision']['cv']['logreg'],'data_md5':state['decision']['data_md5'],'data_sha256':hashlib.sha256((root/'data/office.db').read_bytes()).hexdigest(),'period':'three early slices, no June rows','role':'post-freeze explanatory analysis; original model unchanged'}
 (out/'industry-ablation.json').write_text(json.dumps(result,indent=2));print('REPRODUCIBLE INDUSTRY',result);return result


def financial_checks(root=Path('.')):
 root=Path(root);out=root/'reports/revision';state=joblib.load(root/'reports/development-state.joblib');train=state['train'];oof=pd.read_csv(root/'reports/oof.csv')
 assert train[['client_id','cutoff']].equals(oof[['client_id','cutoff']])
 cal=oof.groupby(pd.qcut(oof.p,5,duplicates='drop'),observed=True).agg(offices=('p','size'),risk=('p','mean'),churn=('churn','mean'));cal.to_csv(out/'oof-calibration-public.csv');print('PUBLIC OOF',cal)
 historical=[]
 for c,f in train.assign(p=oof.p).groupby('cutoff'):
  calls=choose(f,f.p);ix=calls.index;historical.append({'cutoff':c,'n_contacts':len(ix),'caught':int(f.loc[ix,'churn'].sum()),'mean_risk_in_queue':float(f.loc[ix,'p'].mean()),'churn_rate_in_queue':float(f.loc[ix,'churn'].mean()),'expected_profit':float(calls.exp_profit.sum()),'conditional_profit':realized(f,ix),'contact_cost':1500*len(ix),'discount_cost':float((.2*f.loc[ix,'revenue_90']/3).sum()),'conditional_retained_margin':float((f.loc[ix,'churn']*.5*.35*12*f.loc[ix,'revenue_90']/3).sum())})
 pd.DataFrame(historical).to_csv(out/'historical-queue-calibration-and-money.csv',index=False);print('HISTORICAL QUEUES',pd.DataFrame(historical))
 test=pd.read_csv(root/'reports/heldout.csv');base=choose(test,test.p);rule=test.sort_values(['revenue_trend','client_id']).head(150);rule_equal=test.sort_values(['revenue_trend','client_id']).head(len(base));rows=[]
 for name,ix in [('model_max150',base.index),('trend_max150',rule.index),('trend_equal_contacts',rule_equal.index),('no_calls',test.index[:0]),('all_reference_only',test.index)]:
  f=test.loc[ix];retained=float((f.churn*.5*.35*12*f.revenue_90/3).sum());contact=1500*len(ix);discount=float((.2*f.revenue_90/3).sum());rows.append({'strategy':name,'call_limit':150,'n_contacts':len(ix),'exceeds_capacity':len(ix)>150,'contact_cost':contact,'discount_cost':discount,'total_cost':contact+discount,'conditional_retained_margin':retained,'conditional_profit':retained-contact-discount,'expected_profit':float(expected(f,f.p).sum())})
 pd.DataFrame(rows).to_csv(out/'policies-costs.csv',index=False);print('KNOWN JUNE COSTS',pd.DataFrame(rows))
 sensitivity=[]
 for save in [.3,.5,.7]:
  new=choose(test,test.p,save=save);sensitivity.append({'save':save,'call_limit':150,'fixed_contacts':len(base),'fixed_profit':realized(test,base.index,save),'reselected_contacts':len(new),'reselected_profit':realized(test,new.index,save),'same_members_as_base':set(new.client_id)==set(base.client_id),'same_order_as_base':new.client_id.tolist()==base.client_id.tolist()})
 pd.DataFrame(sensitivity).to_csv(out/'sensitivity-public.csv',index=False);print('SENSITIVITY',pd.DataFrame(sensitivity));return cal,pd.DataFrame(historical),pd.DataFrame(rows)


def run_all(root=Path('.')):
 root=Path(root);(root/'reports/revision').mkdir(exist_ok=True)
 trend_and_transfer(root);single_feature_diagnostics(root);tickets_availability(root);future_event_check(root);industry_analysis(root);financial_checks(root)
 print('REVISION COMPLETE: no selection changes, no refit of released model, known June is reproduction only.')
if __name__=='__main__':run_all()
