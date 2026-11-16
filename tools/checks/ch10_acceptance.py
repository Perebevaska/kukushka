from acceptance_runner import Chapter, ROOT
import pandas as pd
import numpy as np
import shutil

with Chapter('ch10') as c:
    c.probe('05-project','split','X["temp"]=s["revenue_k"]')
    c.probe('05-project','split','tr=~tr')
    c.probe('01-gradient','stop-rule',expected=True)
    c.probe('01b-numeric','promise-levels',expected=True)
    item=c.tasks['05-project','baselines']
    for f in item['files']: shutil.copy(ROOT/'site/data'/f,f)
    ns={};exec(item['setup'],ns);exec(item['solution'],ns)
    X0=ns['X'].copy();lag0=ns['lag7'].copy()
    data=pd.read_csv('daily_sales.csv')
    future=data.date>='2025-07-01'
    data.loc[future,'revenue_k']=1_000_000
    data.loc[future,'temp']=99;data.loc[future,'rain']=1
    data.to_csv('daily_sales.csv',index=False)
    ns={};exec(item['setup'],ns);exec(item['solution'],ns)
    assert np.allclose(ns['X'],X0) and np.allclose(ns['lag7'],lag0)
    print('OK one-shot plan unchanged after future revenue/weather mutation')
    anchor = c.tasks['05-project', 'release-row']['solution']
    c.probe('05-project', 'release-row', expected=True)
    c.probe('05-project', 'release-row', code=anchor.replace('< pd.Timestamp(as_of)', '<= pd.Timestamp(as_of)'))
    c.probe('05-project', 'release-row', code=anchor.replace('float(last["revenue_k"])', '69.6'))
