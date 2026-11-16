import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
r = pd.read_csv("reviews_text.csv")

cv = CountVectorizer(binary=True)
B = cv.fit_transform(r["text"])
df_word = int(B[:, cv.vocabulary_["доставка"]].sum())
n = len(r)
idf_manual = round(np.log((1 + n) / (1 + df_word)) + 1, 4)
tf = TfidfVectorizer().fit(r["text"])
idf_sklearn = round(tf.idf_[tf.vocabulary_["доставка"]], 4)