from common import *
from pathlib import Path
import joblib,json,sklearn,numpy as np
from sklearn.metrics import roc_auc_score
art=Path('models/churn/1.0');art.mkdir(parents=True,exist_ok=True)
model=make(LogisticRegression(max_iter=2000)).fit(X_train,y_train)
joblib.dump(model,art/'model.joblib')
card={'name':'churn','version':'1.0','features':list(model.feature_names_in_),'threshold':1/3,'auc_test':float(roc_auc_score(y_test,model.predict_proba(X_test)[:,1])),'n_train':len(X_train),'data_md5':DATA_MD5,'sklearn':sklearn.__version__}
(art/'card.json').write_text(json.dumps(card,ensure_ascii=False,indent=2))
gold=X_test.head(20).copy();gold['expected']=model.predict_proba(gold)[:,1];gold.to_csv(art/'golden.csv',index=False)
back=pd.read_csv(art/'golden.csv');diff=float(np.abs(joblib.load(art/'model.joblib').predict_proba(back[card['features']])[:,1]-back.expected).max())
assert diff<1e-9
print(card,'golden_max_diff',diff)
