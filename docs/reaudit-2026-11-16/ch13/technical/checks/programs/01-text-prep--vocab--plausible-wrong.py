import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

words = Counter()
for text in r["text"]:
    words.update(re.findall(r"[а-яё]+", text.lower()))
n_words = len(words)
total = sum(words.values())
top5 = [w for w, _ in words.most_common(5)]
total = n_words
