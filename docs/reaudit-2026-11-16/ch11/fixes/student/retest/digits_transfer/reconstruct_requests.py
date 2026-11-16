"""Восстановление входов собственного прежнего проекта без обучения модели."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
D = Path(__file__).resolve().parent
digits = load_digits()
X = digits.data / 16
_, final_idx = train_test_split(np.arange(len(X)), test_size=.25,
                                random_state=42, stratify=digits.target)
clean = X[final_idx]
blur = np.array([gaussian_filter(im.reshape(8,8), sigma=.65,
                 mode='constant', cval=0) for im in clean]).reshape(-1,64)
np.save(D/'clean_request.npy', clean)
np.save(D/'blur_request.npy', blur)
pd.DataFrame({'position': np.arange(len(clean)), 'original_index': final_idx}).to_csv(D/'request_ids.csv', index=False)
np.testing.assert_allclose(clean[:16], np.load(D/'control_features.npy'))
old = pd.read_csv(D/'evaluation.csv')
assert np.array_equal(final_idx, old['original_index'])
print('reconstructed shapes', clean.shape, blur.shape, 'IDs match saved evaluation')
