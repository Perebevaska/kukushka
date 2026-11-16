import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

tokens = [w for t in r["text"] for w in tokenize(t)]
to_lemma = dict(zip(lem["word"], lem["lemma"]))
known = dict(zip(lem["word"], lem["known"]))

n_changed = sum(1 for w in set(tokens) if to_lemma[w] != w)
share_known = round(sum(known[w] for w in tokens) / len(tokens), 3)
print(n_changed, share_known)