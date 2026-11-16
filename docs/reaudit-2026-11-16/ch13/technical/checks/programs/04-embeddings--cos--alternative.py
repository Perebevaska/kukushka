import numpy as np

def cosine(a, b):
    return (a/np.linalg.norm(a)) @ (b/np.linalg.norm(b))

s_latte = cosine(vec["кофе"], vec["латте"])
s_late = cosine(vec["курьер"], vec["опоздал"])