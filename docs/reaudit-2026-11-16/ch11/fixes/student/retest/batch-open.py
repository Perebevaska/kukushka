import numpy as np

def batches(X, y, size, rng):
    order = rng.permutation(len(y))
    for start in range(0, len(y), size):
        idx = order[start:start + size]
        yield X[idx], y[idx]

X = np.column_stack((np.arange(101, 112), np.arange(11)*2,
                     np.arange(11)*3, np.arange(11)*4, np.arange(11)*5))
y = np.array([8, 2, 7, 1, 9, 4, 0, 6, 3, 5, 2])
expected = dict(zip(X[:, 0].tolist(), y.tolist()))
parts = list(batches(X, y, 3, np.random.default_rng(17)))
print('sizes', [len(yb) for xb, yb in parts])
for xb, yb in parts:
    for row, label in zip(xb, yb):
        print('pair', int(row[0]), int(label), 'correct', expected[int(row[0])] == int(label))
print('tail row', parts[-1][0][-1].tolist(), 'label', int(parts[-1][1][-1]))
assert all(expected[int(row[0])] == int(label) for xb,yb in parts for row,label in zip(xb,yb))
assert sorted(int(row[0]) for xb,yb in parts for row in xb) == X[:,0].tolist()
# Нарушение: сдвинуть y на одну строку при тех же X. Размеры и coverage
# останутся прежними, а проверка ID -> исходная метка обнаружит рассогласование.
wrong = np.roll(y, 1)
wrong_parts = list(batches(X, wrong, 3, np.random.default_rng(17)))
print('negative sizes', [len(yb) for xb,yb in wrong_parts])
print('negative pairing passes', all(expected[int(row[0])] == int(label) for xb,yb in wrong_parts for row,label in zip(xb,yb)))
