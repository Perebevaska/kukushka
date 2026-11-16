import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
docs = ["кофе вкусный", "кофе горький и холодный"]
T = TfidfVectorizer().fit_transform(docs).toarray()
norms = T.sum(axis=1)
print(np.allclose(norms, 1))