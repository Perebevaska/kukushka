import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

cv = CountVectorizer()
X = cv.fit_transform(r["text"])
shape = X.shape
density = round(X.nnz / (X.shape[0] * X.shape[1]), 4)
n_kofe = int(X.sum(axis=0)[0,cv.vocabulary_["кофе"]])