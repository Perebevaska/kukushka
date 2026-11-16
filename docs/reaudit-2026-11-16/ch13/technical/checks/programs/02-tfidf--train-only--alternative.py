import re
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
r = pd.read_csv("reviews_text.csv")
text_train, text_test = train_test_split(r["text"], test_size=0.25, random_state=42)

tf = TfidfVectorizer()
X_train = tf.fit_transform(text_train)
X_test = tf.transform(text_test)
test_words = {w for t in text_test for w in re.findall(r"(?u)\b\w\w+\b", t.lower())}
n_unseen = len(test_words - set(tf.get_feature_names_out()))
empty_test = int((X_test.getnnz(axis=1) == 0).sum())