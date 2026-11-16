from pathlib import Path
import pandas as pd
import json
DATA=Path('/private/tmp/kuch03round/student-retest/data')
OUT=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch03/fixes/student')
# Один заказ и три объявленных интервала.
toy=pd.DataFrame({'hour':[9],'amount':[200]})
toy['part']=pd.cut(toy.hour,bins=[0,12,17,24],labels=['утро','день','вечер'],right=False)
counts={
 'default':toy.groupby('part').amount.sum().to_dict(),
 'observed_true':toy.groupby('part',observed=True).amount.sum().to_dict(),
 'observed_false':toy.groupby('part',observed=False).amount.sum().to_dict()}
assert len(counts['default'])==1 and len(counts['observed_true'])==1 and len(counts['observed_false'])==3
# Самая ранняя анкета карты, не последняя версия.
raw=pd.read_csv(DATA/'clients_raw.csv')
orders=pd.read_csv(DATA/'orders_3m.csv',parse_dates=['datetime'])
raw['client_id']=raw.client_id.str.strip().str.upper()
orders['client_id']=orders.client_id.str.strip().str.upper()
first=pd.to_datetime(raw.signup_date).groupby(raw.client_id).min()
early=orders.datetime.dt.normalize()<orders.client_id.map(first)
result={'pandas':pd.__version__,'observed_control':counts,'observed_group_counts':{k:len(v) for k,v in counts.items()},'before_earliest_form':{'orders':int(early.sum()),'amount':float(orders.loc[early,'amount'].sum()),'cards':int(orders.loc[early,'client_id'].nunique())}}
(OUT/'control-examples.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
