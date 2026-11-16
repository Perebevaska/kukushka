import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

r = pd.read_csv("reviews_text.csv")
tfidf = TfidfVectorizer()
svd = TruncatedSVD(n_components=50, random_state=0)
Z = svd.fit_transform(tfidf.fit_transform(r["text"]))
Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)
D = svd.transform(tfidf.transform(list(desc.values())))
Dn = D / np.linalg.norm(D, axis=1, keepdims=True)

zs_pred = np.array(list(desc))[np.argmax(Zn @ Dn.T, axis=1)]
zs_acc = round(float((zs_pred == r["topic"]).mean()), 3)
base_acc = round(float(r["topic"].value_counts(normalize=True).iloc[0]), 3)
print(zs_acc, base_acc)
print(pd.crosstab(r["topic"], zs_pred))