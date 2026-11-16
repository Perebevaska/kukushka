import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
svd = TruncatedSVD(n_components=50, random_state=0)
Z = svd.fit_transform(TfidfVectorizer().fit_transform(r["text"]))
explained = round(svd.explained_variance_ratio_.sum(), 2)
Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)

i = r.index[r["review_id"] == "R-40002"][0]
sim = Zn @ Zn[i]
order = [j for j in np.argsort(-sim) if j != i][:3]
neighbours = list(r.loc[order, "review_id"])
print(r.loc[i, "text"])
print(r.loc[order, "text"].tolist())