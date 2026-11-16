import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
r = pd.read_csv("reviews_text.csv")

words = TfidfVectorizer().fit(r["text"])
chars = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4)).fit(r["text"])
sim_words = round(float(cosine_similarity(words.transform(["выпечка"]), words.transform(["ыпечка"]))[0, 0]), 3)
sim_chars = round(float(cosine_similarity(chars.transform(["выпечка"]), chars.transform(["ыпечка"]))[0, 0]), 3)
vocab_chars = len(chars.vocabulary_)