"""Compute the course model's result independently inside the shipped Pyodide."""
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold,train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
hist=pd.read_csv("guests_churn.csv")
fields=hist.drop(columns=["guest_id","card_blocked","churned"]).fillna({"avg_check":0})
X=pd.get_dummies(fields,dtype=int)
y=hist.churned
dev,test=train_test_split(hist.index,test_size=.25,stratify=y,random_state=42)
def ordered(rows,signal,k):
    candidates=hist.loc[rows,["guest_id"]].assign(score=np.asarray(signal))
    return candidates.sort_values(["score","guest_id"],ascending=[False,True]).head(k).index
models={"tree":DecisionTreeClassifier(max_depth=4,random_state=0),"forest":RandomForestClassifier(n_estimators=100,min_samples_leaf=3,random_state=0),"logit":LogisticRegression(max_iter=2000)}
r={}
for name, model in models.items():
    scores=[]
    hits=[]
    for ti,vi in KFold(5,shuffle=True,random_state=42).split(dev):
        tr,va=dev[ti],dev[vi]
        model.fit(X.loc[tr],y.loc[tr])
        scores.append(model.score(X.loc[va],y.loc[va]))
        hits.append(int(y.loc[ordered(va,model.predict_proba(X.loc[va])[:,1],len(va)//10)].sum()))
    r[name]={"accuracy":float(np.mean(scores)),"std":float(np.std(scores)),"hits":hits}
forest=models["forest"].fit(X.loc[dev],y.loc[dev])
risk=forest.predict_proba(X.loc[test])[:,1]
model_ids=ordered(test,risk,60)
rule_ids=ordered(test,hist.loc[test,"days_since_last"],60)
r["historical"]={"accuracy":forest.score(X.loc[test],y.loc[test]),"total":len(test),"positive":int(y.loc[test].sum()),"model_hits":int(y.loc[model_ids].sum()),"rule_hits":int(y.loc[rule_ids].sum()),"queue_overlap":len(set(model_ids)&set(rule_ids)),"threshold45":int((hist.loc[test,"days_since_last"]>45).sum()),"model_already_over45":int((hist.loc[model_ids,"days_since_last"]>45).sum())}
orders=pd.read_csv("deliveries.csv")
orders=orders.loc[orders.actual_min.between(1,299)].copy()
r["first_tree_rule_accuracy"]=float((orders.courier.eq("пеший")==orders.actual_min.gt(orders.promised_min)).mean())
assert (r["historical"]["model_hits"],r["historical"]["rule_hits"])==(56,52)
assert [sum(r[k]["hits"]) for k in models]==[151,151,151]
json.dumps(r,ensure_ascii=False,indent=2)
