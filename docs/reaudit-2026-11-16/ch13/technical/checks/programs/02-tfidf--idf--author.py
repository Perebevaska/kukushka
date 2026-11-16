import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
r = pd.read_csv("reviews_text.csv")

tf = TfidfVectorizer().fit(r["text"])
idf = pd.Series(tf.idf_, index=tf.get_feature_names_out())
common3 = list(idf.sort_values().index[:3])
idf_ne = round(idf["не"], 3)