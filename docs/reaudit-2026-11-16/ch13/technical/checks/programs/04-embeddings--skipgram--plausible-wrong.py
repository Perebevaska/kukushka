import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

def skipgram_pairs(tokens, window=2):
    pairs = []
    for i, center in enumerate(tokens):
        for j in range(max(0, i - window), min(len(tokens), i + window + 1)):
            if j != i:
                pairs.append((center, tokens[j]))
    return pairs

pairs = [p for t in r["text"] for p in skipgram_pairs(tokenize(t))]
n_pairs = len(pairs)

def top(w, k):
    return [c for c, _ in Counter(c for x, c in pairs if x == w).most_common(k)]

top_courier = top("курьер", 3)
shared = set(top("дороговато", 3)) & set(top("недорого", 3))
print(n_pairs, top_courier, shared)
_pairs_original=skipgram_pairs
def skipgram_pairs(tokens,window=2):
    return [p for p in _pairs_original(tokens,window) if p[0]!=p[1]]
