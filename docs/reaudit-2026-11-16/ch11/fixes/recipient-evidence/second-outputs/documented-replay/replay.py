"""Перезагрузка и независимое восстановление всей очереди из пикселей."""
from pathlib import Path
import json, joblib
import numpy as np
import pandas as pd
D = Path(__file__).resolve().parent
model = joblib.load(D/'digits_model.joblib')
rule = json.loads((D/'decision_before_labels.json').read_text())
ids = pd.read_csv(D/'request_ids.csv')
for name in ['clean','blur']:
    X = np.load(D/(name+'_request.npy'))
    assert X.shape == (450,64) and np.isfinite(X).all() and X.min()>=0 and X.max()<=1
    P = model.predict_proba(X)
    by_parts = np.concatenate([model.predict_proba(X[i:i+17]) for i in range(0,len(X),17)])
    perm = np.random.default_rng(43).permutation(len(X))
    restored = model.predict_proba(X[perm])[np.argsort(perm)]
    np.testing.assert_allclose(P, by_parts, atol=1e-12)
    np.testing.assert_allclose(P, restored, atol=1e-12)
    frame = ids.copy()
    frame['prediction'] = model.classes_[P.argmax(axis=1)]
    frame['confidence'] = P.max(axis=1)
    queue = np.lexsort((ids['position'].to_numpy(), P.max(axis=1)))[:rule['capacity_digits']]
    frame['review'] = frame['position'].isin(queue)
    frame.to_csv(D/(name+'_replayed.csv'), index=False)
    np.save(D/(name+'_proba.npy'),P)
    if name=='blur':
        assert queue.tolist()==rule['queue']
        prior = pd.read_csv(D/'evaluation.csv')
        assert np.array_equal(frame.prediction, prior.prediction)
        np.testing.assert_allclose(frame.confidence,prior.confidence)
    print(name,'rows',len(X),'batch maxdiff',float(abs(P-by_parts).max()),'permutation maxdiff',float(abs(P-restored).max()),'queue',queue.tolist())
print('full blur queue and predictions match saved pre-existing decision and evaluation; no fit')
