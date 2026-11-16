import os
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
folder=Path(__file__).resolve().parent
rows=[json.loads(i) for i in (folder/'student.jsonl').read_text().splitlines()]
os.chdir(folder.parents[2]/'site/data')
for row in rows:
    if row['lesson']!='05-project' or 'code' not in row: continue
    if row['id']=='hours':pred=pred_norm
    exec(row['code'],globals())
print('images',len(tm),len(np.unique(tm)),acc_day,acc_evening,n_found_evening,n_empty_evening)
print('brightness',ratio,step_time,acc_day_n,acc_evening_n,recall_empty,precision_empty)
print('hours',empty_hours)
print('alert_count correct missed',n_alerts,n_correct,n_missed)
print('actual episodes',int((T&~T.shift(fill_value=False)).sum().sum()))
print('half',half_empty,'potential',saved_hours,saved_by_product)
print('empty count at hours before/after restock')
print(pd.DataFrame({p:T.loc[:,product==p].sum(axis=1) for p in np.unique(product)}).loc[['10:45','11:00','12:45','13:00','15:00','16:00','16:45','17:00','21:45','22:00']])
print('first half empty after 13',[(p,next((t for t,v in T.loc['13:00':,product==p].sum(axis=1).items() if v>=2),None)) for p in np.unique(product)])
print('slot shortage before second bake',T.loc['13:00':'16:45'].sum().groupby(product).sum()*.25)
