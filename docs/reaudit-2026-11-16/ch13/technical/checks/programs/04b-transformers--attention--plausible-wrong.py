import numpy as np
X = np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0], [2.0, 2.0, 2.0], [2.0, 2.0, 2.0]])
mask = np.array([1, 1, 1, 0, 0])

scores = X @ X.T
masked = scores.copy()
masked[:, mask == 0] = -np.inf
W = np.exp(masked) / np.exp(masked).sum(axis=1, keepdims=True)
out = W @ X
W_raw = np.exp(scores) / np.exp(scores).sum(axis=1, keepdims=True)
pad_weight = round(float(W_raw[0, 3:].sum()), 3)
print(W.round(3), out.round(3), pad_weight, sep="\n")
W = W_raw; out=W@X
