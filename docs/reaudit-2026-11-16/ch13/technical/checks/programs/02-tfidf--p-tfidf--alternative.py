from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
docs = ["кофе вкусный", "кофе горький и холодный"]
T = TfidfVectorizer().fit_transform(docs).toarray()
norms = (T ** 2).sum(axis=1)
print(np.allclose(norms, 1))