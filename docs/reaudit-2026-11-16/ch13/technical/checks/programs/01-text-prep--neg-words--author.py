import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

neg = r[r["rating"] <= 2]
pos = r[r["rating"] >= 4]
ne_share_neg = round(float(neg["text"].map(lambda t: "не" in tokenize(t)).mean()), 3)
ne_share_pos = round(float(pos["text"].map(lambda t: "не" in tokenize(t)).mean()), 3)
c_neg, c_pos = Counter(), Counter()
for t in neg["text"]:
    c_neg.update(tokenize(t))
for t in pos["text"]:
    c_pos.update(tokenize(t))
top_pos = {w for w, _ in c_pos.most_common(100)}
top_neg = [w for w, _ in c_neg.most_common() if w not in top_pos][:10]