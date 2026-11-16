import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

w_vec = TfidfVectorizer()
W = w_vec.fit_transform(r["text"])
c_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4))
C = c_vec.fit_transform(r["text"])

def search(vec, T, q, k=5):
    sim = (T @ vec.transform([q]).T).toarray().ravel()
    idx = np.argsort(-sim, kind="stable")[:k]
    return list(r["text"].values[idx])

top_words = search(w_vec, W, "курьер опоздал")
top_chars = search(c_vec, C, "курьер опоздал")
share_late_words = sum("опоздал" in t.lower() for t in top_words) / 5
share_late_chars = sum("опоздал" in t.lower() for t in top_chars) / 5
print(top_words, top_chars, share_late_words, share_late_chars, sep="\n")
print("new_query",search(w_vec,W,"цены адекватные",3))