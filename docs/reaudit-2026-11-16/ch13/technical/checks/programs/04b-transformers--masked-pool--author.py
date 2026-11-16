import numpy as np

def mean_pool(H, mask):
    return (H * mask[:, :, None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)

pooled = mean_pool(H, attention_mask)
naive = H.mean(axis=1)
a, b = pooled[2], naive[2]
cos_short = round(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b))), 3)
same = bool(np.allclose(mean_pool(H_long, mask_long), pooled))
print(pooled.shape, cos_short, same)