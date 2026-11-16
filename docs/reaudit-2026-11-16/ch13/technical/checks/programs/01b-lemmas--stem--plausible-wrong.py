import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

def stem(word, n=5):
    return word[:n] if len(word) > n else word

all_words = {w for t in r["text"] for w in tokenize(t)}
n_raw = len(all_words)
n_stem = len({stem(w) for w in all_words})
merged = sorted(w for w in all_words if stem(w) == stem("курьер"))
def stem(word,n=5):
    return word[:5]
