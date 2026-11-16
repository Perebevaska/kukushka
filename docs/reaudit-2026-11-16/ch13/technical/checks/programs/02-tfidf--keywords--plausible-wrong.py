import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

tf = TfidfVectorizer()
T = tf.fit_transform(r["text"])
names = tf.get_feature_names_out()

def keywords(i, k=3):
    row = T[i].toarray()[0]
    idx = [j for j in np.argsort(-row, kind="stable") if row[j] > 0][:k]
    return [str(names[j]) for j in idx]

kw = {i: keywords(i) for i in range(5)}
share_topic_word = round(float(np.mean([bool(set(keywords(i)) & MARKERS[r.loc[i, "topic"]]) for i in range(200)])), 3)
print(kw, share_topic_word)
kw = {i:list(reversed(v)) for i,v in kw.items()}
