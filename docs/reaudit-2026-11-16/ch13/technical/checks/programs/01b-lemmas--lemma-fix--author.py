import re
from collections import Counter
import pandas as pd
r = pd.read_csv("reviews_text.csv")
lem = pd.read_csv("review_lemmas.csv")
fixes = {"капучиный": "капучино", "латта": "латте", "барист": "бариста", "флэта": "флэт"}

def tokenize(text):
    return re.findall(r"[а-яё]+", text.lower())

suspects = (lem[(lem["known"] == 0) & (lem["count"] >= 30)]
            .sort_values("count", ascending=False)["word"].tolist())

to_lemma = dict(zip(lem["word"], lem["lemma"]))
c = Counter(fixes.get(to_lemma[w], to_lemma[w]) for t in r["text"] for w in tokenize(t))
n_barista = c["бариста"]
top_drink = max(["кофе", "капучино", "латте", "раф"], key=lambda d: c[d])
print(suspects, n_barista, top_drink, c["кофе"], c["капучино"])