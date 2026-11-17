"""Recompute calls using the released model and shared as-of features."""
import argparse,hashlib,json
from pathlib import Path
import joblib,numpy as np,pandas as pd
from src.features import read_tables,build_features

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--cutoff',required=True)
 p.add_argument('--db',default='data/office.db')
 p.add_argument('--artifact',default='models/office_churn/1.0')
 p.add_argument('--call-limit',type=int,default=None)
 p.add_argument('--out-dir',default='reports/rescore')
 a=p.parse_args();art=Path(a.artifact);card=json.loads((art/'passport.json').read_text())
 limit=card['call_limit'] if a.call_limit is None else a.call_limit
 if not 0<=limit<=150:p.error('--call-limit must be between 0 and 150')
 model=joblib.load(art/'model.joblib');gold=pd.read_csv(art/'golden.csv');features=card['features']
 if list(model.feature_names_in_)!=features:raise ValueError('Model feature order differs from passport')
 diff=float(np.abs(model.predict_proba(gold[features])[:,1]-gold.expected).max())
 if not diff<card['golden_tolerance']:raise ValueError(f'Golden mismatch: {diff}')
 tables=read_tables(a.db);f=build_features(tables,a.cutoff);prob=model.predict_proba(f[features])[:,1];e=card['economics'];r=f.revenue_90/3
 profit=prob*e['save_rate']*e['margin']*e['months']*r-e['contact_cost']-e['discount']*r
 queue=pd.DataFrame({'client_id':f.index,'city':f.city.to_numpy(),'p_churn':prob,'exp_profit':profit.to_numpy()})
 queue=queue.loc[queue.exp_profit>0].sort_values(['exp_profit','client_id'],ascending=[False,True]).head(limit)
 rawsum=float(queue.exp_profit.sum());shown=queue.copy();shown.p_churn=shown.p_churn.round(3);shown.exp_profit=shown.exp_profit.round().astype(int)
 out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);stem=f'call_list_{a.cutoff}_limit{limit}'
 shown.to_csv(out/f'{stem}.csv',index=False)
 meta={'cutoff':a.cutoff,'call_limit':limit,'n_calls':len(shown),'expected_profit':round(rawsum),'full_precision_profit_sum':rawsum,'golden_max_diff':diff,'model':card['model'],'version':card['version'],'data_md5':hashlib.md5(Path(a.db).read_bytes()).hexdigest(),'artifact_data_md5':card['data_md5'],'features':features,'economics':e,'cities':shown.city.value_counts().to_dict()}
 (out/f'{stem}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
