import numpy as np
import pandas as pd

def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

sims = pd.Series({w: cosine(vec["кофе"], v) for w, v in vec.items() if w != "кофе"}).sort_values(ascending=False)
top3 = list(sims.index[:3])