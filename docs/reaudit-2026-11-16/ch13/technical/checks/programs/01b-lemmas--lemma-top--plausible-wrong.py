import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
to_lemma = dict(zip(lem["word"], lem["lemma"]))

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

tokens = [w for t in r.loc[r["rating"] <= 3, "text"] for w in tokenize(t)]
c = Counter(to_lemma[w] for w in tokens)
top10 = [l for l, _ in c.most_common(10)]
n_byt = c["быть"]
forms_byt = sorted({w for w in tokens if to_lemma[w] == "быть"})
print(top10, n_byt, forms_byt)
n_byt = len(forms_byt)
