import numpy as np
vec = {"латте": np.array([0.8, 0.0, 0.1, 0.5]), "капучино": np.array([0.8, 0.1, 0.0, 0.4]), "вкусно": np.array([0.4, 0.0, 0.0, 0.9])}
words = "капучино вкусно".split()
v = np.sum([vec[w] for w in words], axis=0)/len(words)
v = v / np.linalg.norm(v)
latte = vec["латте"] / np.linalg.norm(vec["латте"])
print(round(float(v @ latte), 2))