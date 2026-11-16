import re
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

tokens = r["text"].map(lambda t: set(tokenize(t)))
rule = tokens.map(lambda s: int("не" in s or "но" in s))
only_ne = tokens.map(lambda s: int("не" in s))
acc_rule, f1_rule = round(accuracy_score(y, rule), 3), round(f1_score(y, rule), 3)
acc_ne, f1_ne = round(accuracy_score(y, only_ne), 3), round(f1_score(y, only_ne), 3)