import numpy as np
batch = [[2, 5, 8, 3], [2, 22, 3], [2, 4, 14, 15, 3]]
L = max(len(ids) for ids in batch)
input_ids = np.array([ids + [0] * (L - len(ids)) for ids in batch])
attention_mask = np.not_equal(input_ids,0).astype(int)
print(attention_mask.sum(axis=1))