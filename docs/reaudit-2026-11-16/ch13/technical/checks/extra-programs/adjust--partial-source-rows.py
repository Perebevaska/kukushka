n=n.iloc[::2].copy()
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
pred = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)).fit(X_train, y_train).predict(X_test)
tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
tpr, fpr = tp / (tp + fn), fp / (fp + tn)

obs = n[n["shop_id"] == "KZN-2"].groupby("period")["neg"].mean()
adj = {k: round((obs[k] - fpr) / (tpr - fpr), 3) for k in ["до", "после"]}
print(round(tpr, 3), round(fpr, 3), obs.round(3).to_dict(), adj)
gold = pd.read_csv('reviews_new_gold.csv')
labeled = n.merge(gold[['review_id','complaint']],on='review_id',validate='one_to_one')
rows=[]
for period,part in labeled[labeled.shop_id=='KZN-2'].groupby('period'):
    target=part.complaint
    tpr_new=float(part.loc[target==1,'neg'].mean())
    fpr_new=float(part.loc[target==0,'neg'].mean())
    observed=float(part.neg.mean())
    rows.append(dict(period=period,n=len(part),complaints=int(target.sum()),tpr=tpr_new,fpr=fpr_new,observed=observed,manual=float(target.mean()),adjusted=(observed-fpr_new)/(tpr_new-fpr_new) if abs(tpr_new-fpr_new)>1e-6 else float("nan")))
audit=pd.DataFrame(rows).set_index('period')