import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
r = pd.read_csv("reviews_text.csv")
X_train, X_test, y_train, y_test = train_test_split(r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])

model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)
acc_topic = round((pred == y_test).mean(), 3)
cm = pd.crosstab(y_test, pred)
recall = pd.Series({t: cm.loc[t, t] / cm.loc[t].sum() for t in cm.index})
worst_topic = recall.idxmin()
cm.index = list(reversed(cm.index))
