"""Read-only independent validation of the received release; no fit/train calls."""
from pathlib import Path
from datetime import date,timedelta
from collections import defaultdict
import csv,json,hashlib,sqlite3,sys,importlib.metadata as im,math
import pandas as pd,numpy as np,joblib
sys.path.insert(0,str(Path.cwd()))
from src.features import read_tables,build_features
OUT=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch15/recipient')
ROOT=Path.cwd(); ART=ROOT/'models/office_churn/1.0'; card=json.loads((ART/'passport.json').read_text()); names=card['features']
checks=[]
def check(name,condition,detail=None):
 checks.append({'check':name,'pass':bool(condition),'detail':detail})
 if not condition: print('FAIL',name,detail)
versions={'python':sys.version,'packages':{line.split('==')[0]:im.version(line.split('==')[0]) for line in (ROOT/'requirements.txt').read_text().splitlines() if '==' in line}}
versions['requirements_match']={line.split('==')[0]:im.version(line.split('==')[0])==line.split('==')[1] for line in (ROOT/'requirements.txt').read_text().splitlines() if '==' in line}
check('requirements versions match',all(versions['requirements_match'].values()),versions)
check('passport Python version matches',sys.version.split()[0]==card['python'])
check('passport sklearn version matches',im.version('scikit-learn')==card['sklearn'])
model=joblib.load(ART/'model.joblib');gold=pd.read_csv(ART/'golden.csv');f=build_features(read_tables(ROOT/'data/office.db'),'2026-09-30')
check('model feature key/order matches',list(model.feature_names_in_)==names)
check('built feature key/order matches',list(f.columns)==names)
check('golden key/order and 20 unique controls',list(gold.columns)==['client_id']+names+['expected'] and len(gold)==20 and gold.client_id.nunique()==20)
types={n:str(f[n].dtype) for n in names};check('all actual feature types match passport',types==card['feature_types'],types)
catinfo={}
for n in card['categories']:
 actual=sorted(f[n].dropna().unique().tolist()); declared=card['categories'][n]
 catinfo[n]={'working':actual,'declared':declared,'all_known':set(actual)<=set(declared)}
check('working categorical values known',all(x['all_known'] for x in catinfo.values()),catinfo)
cat_pipeline=model.named_steps['preprocess'] if 'preprocess' in model.named_steps else None
print('pipeline',model)
gp=model.predict_proba(gold[names])[:,1];goldmax=float(np.max(np.abs(gp-gold.expected.to_numpy())))
check('20 golden probabilities below tolerance',goldmax<card['golden_tolerance'],{'max_delta':goldmax,'tolerance':card['golden_tolerance']})
check('database fingerprint matches release',hashlib.md5((ROOT/'data/office.db').read_bytes()).hexdigest()==card['data_md5'])
# Independently rebuild all 16 features from raw SQLite rows with stdlib, without using project transforms.
con=sqlite3.connect(f'file:{ROOT}/data/office.db?mode=ro',uri=True);con.row_factory=sqlite3.Row
raw={t:[dict(r) for r in con.execute('SELECT * FROM '+t)] for t in ['clients','contracts','orders','tickets','invoices']};con.close()
clients={r['client_id']:r for r in raw['clients'] if not r['is_test']};cut=date(2026,9,30);d90=cut-timedelta(days=90);d180=cut-timedelta(days=180)
active={r['client_id']:r for r in raw['contracts'] if r['client_id'] in clients and date.fromisoformat(r['start_date'])<=cut and (r['end_date'] is None or date.fromisoformat(r['end_date'])>cut)}
check('active source IDs unique',len(active)==len([r for r in raw['contracts'] if r['client_id'] in clients and date.fromisoformat(r['start_date'])<=cut and (r['end_date'] is None or date.fromisoformat(r['end_date'])>cut)]))
byorders=defaultdict(list);bytickets=defaultdict(list);byinv=defaultdict(list)
for r in raw['orders']:
 if r['client_id'] in active and date.fromisoformat(r['order_date'])<=cut and r['status']!='отменён':byorders[r['client_id']].append(r)
seen=set()
for r in raw['tickets']:
 if r['ticket_id'] in seen:continue
 seen.add(r['ticket_id'])
 if r['client_id'] in active and d90<date.fromisoformat(r['created_at'])<=cut:bytickets[r['client_id']].append(r)
for r in raw['invoices']:
 if r['client_id'] in active and date.fromisoformat(r['due_date'])<=cut:byinv[r['client_id']].append(r)
ind={}
for cid,contract in active.items():
 c=clients[cid];orders=byorders[cid];recent=[r for r in orders if date.fromisoformat(r['order_date'])>d90];previous=[r for r in orders if d180<date.fromisoformat(r['order_date'])<=d90]
 revenue=math.fsum(r['amount'] for r in recent);old=math.fsum(r['amount'] for r in previous);delivered=[r for r in recent if r['status']=='доставлен'];invoices=byinv[cid];last3=sorted(invoices,key=lambda r:(r['due_date'],r['invoice_id']))[-3:];tenure=(cut-date.fromisoformat(contract['start_date'])).days
 def known_paid(r):return date.fromisoformat(r['paid_date']) if r['paid_date'] and date.fromisoformat(r['paid_date'])<=cut else None
 lates=[max(0,((known_paid(r) or cut)-date.fromisoformat(r['due_date'])).days) for r in last3]
 ind[cid]={'plan':contract['plan'],'city':c['city'],'industry':c['industry'] or 'нет данных','employees':c['employees'],'has_manager':contract['has_manager'],'own_machine':contract['own_machine'],'tenure_days':tenure,'orders_90':len(recent),'revenue_90':revenue,'revenue_trend':(revenue-old)/(revenue+old+1),'days_since_order':(cut-max(date.fromisoformat(r['order_date']) for r in orders)).days if orders else tenure,'late_share_90':sum(r['late_min']>0 for r in delivered)/len(delivered) if delivered else 0.0,'tickets_90':len(bytickets[cid]),'tickets_bill_90':sum(r['category']=='счёт' for r in bytickets[cid]),'pay_late_last3':sum(lates)/len(lates) if lates else 0.0,'overdue_now':sum(date.fromisoformat(r['due_date'])<cut and known_paid(r) is None for r in invoices)}
check('built IDs match independent active source',set(f.index)==set(ind) and f.index.is_unique,{'rows':len(f),'independent':len(ind)})
featureerrors=[];maxfeaturedelta={n:0 for n in names if n not in card['categories']}
for cid in f.index:
 for n in names:
  a=f.loc[cid,n];b=ind[cid][n]
  if n in card['categories']:
   if a!=b:featureerrors.append([cid,n,str(a),str(b)])
  else:
   maxfeaturedelta[n]=max(maxfeaturedelta[n],abs(float(a)-float(b)))
   if not math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-9):featureerrors.append([cid,n,str(a),str(b)])
check('all features agree with independent raw-source reconstruction',not featureerrors,{'errors':featureerrors[:20],'max_deltas':maxfeaturedelta})
goldsourceerrors=[]
for row in gold.to_dict('records'):
 for n in names:
  a=row[n];b=ind[row['client_id']][n]
  if isinstance(b,str):ok=a==b
  else:ok=math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-9)
  if not ok:goldsourceerrors.append([row['client_id'],n])
check('20 golden input rows agree with database features',not goldsourceerrors,goldsourceerrors)
# Score the independently reconstructed frame; economics recomputed as scalar Python arithmetic.
indf=pd.DataFrame.from_dict(ind,orient='index')[names];p=model.predict_proba(indf)[:,1];eco=card['economics'];rows=[]
for cid,prob in zip(indf.index,p):
 rev=ind[cid]['revenue_90']/3
 profit=float(prob)*eco['save_rate']*eco['margin']*eco['months']*rev-eco['contact_cost']-eco['discount']*rev
 if profit>0:rows.append({'client_id':cid,'city':clients[cid]['city'],'p_churn':float(prob),'exp_profit':profit})
rows.sort(key=lambda r:(-r['exp_profit'],r['client_id']))
result={}
for limit in [card['call_limit'],3]:
 desired=rows[:limit];stem=f'call_list_2026-09-30_limit{limit}';actual=pd.read_csv(ROOT/'reports/rescore'/f'{stem}.csv');meta=json.loads((ROOT/'reports/rescore'/f'{stem}.json').read_text());total=math.fsum(r['exp_profit'] for r in desired)
 check(f'limit{limit} ordered IDs match independently scored source',actual.client_id.tolist()==[r['client_id'] for r in desired] and actual.client_id.is_unique)
 check(f'limit{limit} cities match raw client table',actual.city.tolist()==[r['city'] for r in desired])
 check(f'limit{limit} probabilities and money match display rounding',actual.p_churn.tolist()==[round(r['p_churn'],3) for r in desired] and actual.exp_profit.tolist()==[round(r['exp_profit']) for r in desired])
 check(f'limit{limit} full precision sum and metadata',abs(meta['full_precision_profit_sum']-total)<1e-8 and meta['expected_profit']==round(total) and meta['n_calls']==len(desired) and meta['version']==card['version'] and meta['call_limit']==limit and meta['data_md5']==card['data_md5'] and meta['artifact_data_md5']==card['data_md5'],{'independent_total':total,'metadata_total':meta['full_precision_profit_sum'],'delta':meta['full_precision_profit_sum']-total})
 result[str(limit)]={'count':len(desired),'independent_full_precision_sum':total,'metadata_full_precision_sum':meta['full_precision_profit_sum'],'expected_profit':meta['expected_profit'],'cities':meta['cities'],'ids':[r['client_id'] for r in desired]}
 if limit==3:
  check('capacity3 CSV matches handed reference byte-for-byte',(ROOT/'reports/reference-rescore'/f'{stem}.csv').read_bytes()==(ROOT/'reports/rescore'/f'{stem}.csv').read_bytes())
  check('capacity3 JSON matches handed reference byte-for-byte',(ROOT/'reports/reference-rescore'/f'{stem}.json').read_bytes()==(ROOT/'reports/rescore'/f'{stem}.json').read_bytes())
  (OUT/'independent-top3-full-precision.json').write_text(json.dumps(desired,ensure_ascii=False,indent=2))
 else:
  check('baseline CSV matches handed release byte-for-byte',(ROOT/'reports/call_list_2026-09-30.csv').read_bytes()==(ROOT/'reports/rescore'/f'{stem}.csv').read_bytes())
# Check no submitted source/model/database/original reports changed.
manifest=json.loads((OUT/'receipt-input-manifest.json').read_text());incoming=ROOT.parent/'incoming';changed=[];workingchanged=[]
for entry in manifest:
 rel=entry['path'];expected=entry['sha256'];src=incoming/rel
 if hashlib.sha256(src.read_bytes()).hexdigest()!=expected:changed.append(rel)
 if rel.startswith('reports/rescore/'):continue
 if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:workingchanged.append(rel)
check('all 53 original incoming files unchanged',not changed,changed)
check('working original sources/model/db/reports unchanged except preserved rescore move',not workingchanged,workingchanged)
report={'environment':versions,'model_pipeline':str(model),'golden_max_delta':goldmax,'feature_types':types,'independent_source_rows':len(ind),'results':result,'checks':checks,'all_pass':all(x['pass'] for x in checks),'training_calls':0,'limitation':'Existing environment used. No fresh pip install or fresh kernel notebook execution performed by this receiving analyst.'}
(OUT/'receipt-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['all_pass'] else 1)
