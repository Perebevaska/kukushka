import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
r = pd.read_csv("reviews_text.csv")

vocab_by_min_df = {m: len(CountVectorizer(min_df=m).fit(r["text"]).vocabulary_) for m in [1, 2, 5, 20]}
full = CountVectorizer().fit(r["text"])
cut = CountVectorizer(min_df=5).fit(r["text"])
kept_share = round(cut.transform(r["text"]).sum() / full.transform(r["text"]).sum(), 4)
dropped_examples = sorted(w for w in full.vocabulary_ if w not in cut.vocabulary_)[:5]
print(vocab_by_min_df, kept_share, dropped_examples)