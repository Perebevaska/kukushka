import re
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

to_lemma = dict(zip(lem["word"], lem["lemma"]))

def lemmatize(text):
    return " ".join(to_lemma[w] for w in tokenize(text))

first = lemmatize(r.loc[0, "text"])
print(first)
def lemmatize(text):
    return " ".join(tokenize(text))
