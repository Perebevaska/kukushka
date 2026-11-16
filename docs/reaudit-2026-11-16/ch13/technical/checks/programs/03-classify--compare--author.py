import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)

models = {
    "words": make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)),
    "bigrams": make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000)),
    "chars": make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)), LogisticRegression(max_iter=1000)),
    "nb": make_pipeline(CountVectorizer(), MultinomialNB()),
}
cv_f1 = {k: round(cross_val_score(m, X_train, y_train, cv=5, scoring="f1").mean(), 3) for k, m in models.items()}
best = max(cv_f1, key=cv_f1.get)