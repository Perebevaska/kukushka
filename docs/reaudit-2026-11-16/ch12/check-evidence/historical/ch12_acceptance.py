from acceptance_runner import Chapter,ROOT
import pandas as pd
import numpy as np
import shutil

with Chapter('ch12') as c:
    c.probe('05-project','split','import numpy as np\ntest=np.roll(test,744)')
    c.probe('03-features','leak-test',expected=True)
    c.probe('05-project', 'staffing', expected=True)
    c.probe('05-project', 'staffing', 'needed = np.zeros_like(needed)')
    item=c.tasks['05-project','final']
    for filename in item['files']:shutil.copy(ROOT/'site/data'/filename,filename)
    ns={};exec(item['setup'],ns);exec(item['solution'],ns)
    initial=ns['pred_test'][:24].copy()
    raw=pd.read_csv('app_orders.csv')
    mask=(raw.datetime>='2026-07-31 20:00')&(raw.datetime<'2026-08-01')
    raw.loc[mask,'orders']+=1000;raw.to_csv('app_orders.csv',index=False)
    ns={};exec(item['setup'],ns);exec(item['solution'],ns)
    assert np.allclose(initial,ns['pred_test'][:24])
    hidden=ns['s'].copy();hidden.loc[hidden.index>='2026-07-31 20:00']=np.nan
    future=ns['make'](hidden).loc['2026-08-01':'2026-08-01 23:00']
    assert len(future)==24 and future.y.isna().all() and future.drop(columns='y').notna().all().all()
    print('OK24 future rows with unknown target; first-day forecast invariant to last4 unavailable labels')
