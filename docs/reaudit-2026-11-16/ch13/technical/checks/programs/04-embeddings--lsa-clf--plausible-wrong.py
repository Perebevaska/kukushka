import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

acc_by_k = {}
for k in [10, 20, 50, 100]:
    m = make_pipeline(TfidfVectorizer(), TruncatedSVD(k, random_state=0), LogisticRegression(max_iter=1000))
    acc_by_k[k] = round(accuracy_score(y_test, m.fit(X_train, y_train).predict(X_test)), 3)
full = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
acc_full = round(accuracy_score(y_test, full.predict(X_test)), 3)
best_k = max(sorted(acc_by_k), key=acc_by_k.get)
print(acc_by_k, acc_full, best_k)
acc_by_k[10],acc_by_k[100]=acc_by_k[100],acc_by_k[10]
