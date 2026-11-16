import numpy as np

def cosine(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

s_latte = cosine(vec["кофе"], vec["латте"])
s_late = cosine(vec["курьер"], vec["опоздал"])