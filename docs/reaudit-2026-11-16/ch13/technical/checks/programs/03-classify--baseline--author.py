import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

dummy = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
pd_ = dummy.predict(X_test)
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pm = model.predict(X_test)
acc_dummy = round(accuracy_score(y_test, pd_), 3)
f1_dummy = round(f1_score(y_test, pd_, zero_division=0), 3)
acc_model = round(accuracy_score(y_test, pm), 3)
f1_model = round(f1_score(y_test, pm), 3)
share_bad = round(y.mean(), 3)