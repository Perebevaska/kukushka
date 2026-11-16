import numpy as np

def mean_pool(H, mask):
    return np.stack([a[m.astype(bool)].mean(axis=0) for a,m in zip(H,mask)])

pooled = mean_pool(H, attention_mask)
naive = H.mean(axis=1)
a, b = pooled[2], naive[2]
cos_short = round(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b))), 3)
same = bool(np.allclose(mean_pool(H_long, mask_long), pooled))
print(pooled.shape, cos_short, same)