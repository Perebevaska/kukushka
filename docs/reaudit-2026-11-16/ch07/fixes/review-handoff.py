"""Run with the student environment, first on fixes/student/original, then on student."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from hashlib import sha256

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
chapter = HERE.parent
script = '''import ast, json, joblib, sys, os
from pathlib import Path
import numpy as np, pandas as pd, sklearn
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.pipeline import Pipeline
source=Path(sys.argv[1])
sys.path.insert(0,str(source))
doc=json.loads((source/'model_passport.json').read_text())
m=joblib.load(source/doc['model_file'])
assert isinstance(m,Pipeline)
d=pd.read_csv(source/'data/catering_leads.csv').sort_values(['created','lead_id']).set_index('lead_id')
cut=pd.Timestamp(d.iloc[-750].created)
dt=pd.to_datetime(d.created)
groups={'train':d.index[dt+pd.Timedelta(days=30)<cut], 'embargo':d.index[(dt<cut)&(dt+pd.Timedelta(days=30)>=cut)], 'final':d.index[dt>=cut]}
for key,idx in groups.items(): assert list(pd.read_csv(source/(key+'_ids.csv')).lead_id)==list(idx)
assert doc['train_rows']==len(groups['train']) and doc['final_rows']==len(groups['final'])
test=d.loc[groups['final']]; y=test.converted; x=test.drop(columns=['converted','contract_rub'])
s=m.predict_proba(x)[:,1]; assert np.allclose(m.predict_proba(x[x.columns[::-1]])[:,1],s)
rank=pd.Series(s,index=y.index,name='score').reset_index().sort_values(['score','lead_id'],ascending=[False,True])
stored=pd.read_csv(source/'final_ranking.csv');assert list(rank.lead_id)==list(stored.lead_id) and np.allclose(rank.score,stored.score)
rule=(test.repeat_client==1)|(test.channel=='рекомендация')
rid=sorted(test.index[rule]);mid=list(rank.head(len(rid)).lead_id)
metrics=json.loads((source/'metrics.json').read_text())
assert np.isclose(metrics['roc_auc'],roc_auc_score(y,s)) and np.isclose(metrics['f1_at_05'],f1_score(y,m.predict(x)))
assert metrics['final_contracts']==y.sum()
for label,ids in [('model',mid),('rule',rid)]:
 q=pd.read_csv(source/(label+'_queue.csv'));assert list(q.lead_id)==ids and list(q.position)==list(range(1,len(ids)+1))
for group,ids in [('rule_equal_budget',rid),('model_equal_budget',mid),('model_top30',list(rank.iloc[:int(.3*len(y))].lead_id))]:
 rec=metrics[group];tp=int(y.loc[ids].sum())
 assert (rec['places'],rec['contracts'])==(len(ids),tp) and np.isclose(rec['precision'],tp/len(ids)) and np.isclose(rec['recall'],tp/y.sum())
table=pd.read_csv(source/'cv_results.csv');cols=[c for c in table if c.startswith('split') and c.endswith('_test_score')]
assert np.allclose(table[cols].mean(axis=1),table.mean_test_score)
assert doc['parameters']==ast.literal_eval(table.sort_values('rank_test_score').iloc[0].params)
assert all(m.get_params()[k]==v for k,v in doc['parameters'].items())
if 'versions' in doc:
 import platform
 assert json.loads((source/'versions.json').read_text())==doc['versions']
 assert doc['versions']=={'python':platform.python_version(),'scikit-learn':sklearn.__version__,'pandas':pd.__version__,'numpy':np.__version__,'joblib':joblib.__version__}
new=pd.read_csv(source/'new_raw.csv').set_index('lead_id'); stand=float(m.predict_proba(new)[:,1][0])
batch=pd.concat([new,new,new]);batch.index=['ZZ-3','ZZ-1','ZZ-2']; batch.created=['2027-02-03 18:59','2027-02-03 19:00','2027-02-03 19:00'];batch.city='невиданный город';batch.budget_pp=np.nan
out=m.predict_proba(batch[batch.columns[::-1]])[:,1]; assert np.isfinite(out).all() and out[1]==out[2]
ordered=pd.DataFrame({'score':out[1:], 'lead_id':batch.index[1:]}).iloc[::-1].sort_values(['score','lead_id'],ascending=[False,True])
assert ordered.iloc[0].lead_id=='ZZ-1'
print(json.dumps({'sklearn':sklearn.__version__,'split':{k:len(v) for k,v in groups.items()},'earliest_final':str(cut),'latest_train_label_ready':str((dt.loc[groups['train']]+pd.Timedelta(days=30)).max()),'metrics':metrics,'last_ids':[mid[-1],rid[-1]],'next_model_id':rank.iloc[len(mid)].lead_id,'cv_folds':cols,'parameters':doc['parameters'],'probability_sent_new_raw':stand,'unknown_city_new_date_1859_1900_and_duplicate':out.tolist(),'tie_ids':list(ordered.lead_id),'raw_columns':list(x.columns)},ensure_ascii=False))'''
phase=sys.argv[1]
source=(HERE/'student/original' if phase=='before' else chapter/'student').resolve()
out={'phase':phase, 'submitted_files':{str(p.relative_to(source)):sha256(p.read_bytes()).hexdigest() for pattern in ('pipeline.ipynb','versions.json','data/catering_leads.csv','*.joblib','model_passport.json','catering_features.py','*_queue.csv','metrics.json','*_ids.csv','cv_results.csv','new_raw.csv','final_ranking.csv') for p in source.glob(pattern)}}
with tempfile.TemporaryDirectory() as temp:
    tmp=Path(temp)
    (tmp/'data').mkdir()
    for name in ['pipeline.ipynb','data/catering_leads.csv','catering_features.py']:
        shutil.copy(source/name,tmp/name)
    out['fresh_process_submitted']=json.loads(subprocess.check_output([sys.executable,'-c',script,str(source)],cwd=tmp))
    nb=nbformat.read(tmp/'pipeline.ipynb',as_version=4)
    for cell in nb.cells:
        if cell.cell_type=='code': cell.outputs=[];cell.execution_count=None
    os.environ['JUPYTER_RUNTIME_DIR']=str(tmp/'runtime')
    os.environ['IPYTHONDIR']=str(tmp/'ipython')
    os.environ['JUPYTER_DATA_DIR']=str(tmp/'jupyter')
    NotebookClient(nb,timeout=90,kernel_name='python3',resources={'metadata':{'path':str(tmp)}}).execute()
    out['kernel_cells']=[dict(execution=c.execution_count,stdout=''.join(str(o.get('text','')) for o in c.outputs)) for c in nb.cells if c.cell_type=='code']
    out['fresh_process_rebuilt']=json.loads(subprocess.check_output([sys.executable,'-c',script,str(tmp)],cwd=tmp))
    assert out['fresh_process_submitted']==out['fresh_process_rebuilt']
    out['model_bytes_match']=sha256((tmp/'catering_model.joblib').read_bytes()).hexdigest()==out['submitted_files']['catering_model.joblib']
(HERE/f'review-handoff-{phase}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Hand-off verified', phase,out['fresh_process_rebuilt']['metrics'])
