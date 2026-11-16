from acceptance_runner import Chapter, ROOT
import pandas as pd
import numpy as np
from sklearn.base import TransformerMixin,BaseEstimator
from sklearn.model_selection import KFold

with Chapter('ch07') as c:
    c.probe('09-project','metric',expected=True)
    c.probe('09-project','final',expected=True)
    source=c.tasks['09-project','final']['solution']
    c.probe('09-project','final',code=source+'\nbest.named_steps["prep"] = best.named_steps["prep"].steps[-1][1]') if False else None
    setup=c.tasks['09-project','final']['setup']
    ns={};exec(setup,ns)
    final=ns['X_test']; train=ns['X_train']
    assert pd.to_datetime(train.created).max()+pd.Timedelta(days=30)<pd.to_datetime(final.created).min()
    assert len(final)==750
    print('OK disjoint mature temporal windows',len(train),len(final))
source=(ROOT/'content/ch07/07b-own-steps.md').read_text()
start=source.index('class RateBy('); end=source.index('\ng = pd.read_csv',start)
ns=dict(pd=pd,np=np,TransformerMixin=TransformerMixin,BaseEstimator=BaseEstimator,KFold=KFold)
exec(source[start:end],ns)
X=pd.DataFrame({'city':['singleton'+str(i) for i in range(10)]}); y=pd.Series([0,1]*5)
t=ns['RateBy'](); a=t.fit_transform(X,y); y2=y.copy(); y2.iloc[0]=1-y2.iloc[0]
b=ns['RateBy']().fit_transform(X,y2)
assert a.loc[0,'churn_rate_city']==b.loc[0,'churn_rate_city']
assert np.isfinite(t.transform(pd.DataFrame({'city':['new',None]})).churn_rate_city).all()
print('OK OOF own-target mutation, unseen fallback')
