import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

sizes = {}
sizes["1"] = len(CountVectorizer().fit(r["text"]).vocabulary_)
sizes["1-2"] = len(CountVectorizer(ngram_range=(1, 2)).fit(r["text"]).vocabulary_)
cv3 = CountVectorizer(ngram_range=(1, 2), min_df=5).fit(r["text"])
sizes["1-2 min5"] = len(cv3.vocabulary_)
has_ne_pridu = "не приду" in set(cv3.get_feature_names_out())