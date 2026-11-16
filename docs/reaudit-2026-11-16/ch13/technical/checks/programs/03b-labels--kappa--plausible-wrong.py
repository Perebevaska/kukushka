import pandas as pd
from sklearn.metrics import cohen_kappa_score
wide = pd.read_csv("review_labels.csv").pivot(index="review_id", columns="annotator", values="label")

def kappa(x, y):
    x, y = list(x), list(y)
    n = len(x)
    p_o = sum(a == b for a, b in zip(x, y)) / n
    p_e = sum((x.count(c) / n) * (y.count(c) / n) for c in set(x) | set(y))
    return (p_o - p_e) / (1 - p_e)

kappa_ab = round(kappa(wide["аня"], wide["борис"]), 3)
kappa_av = round(kappa(wide["аня"], wide["вика"]), 3)
print(kappa_ab, kappa_av, round(cohen_kappa_score(wide["аня"], wide["вика"]), 3))
def kappa(x,y):
    return sum(a==b for a,b in zip(x,y))/len(x)
