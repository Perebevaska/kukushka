import json,sys,joblib
from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent
model=joblib.load(D/'digits_model.joblib')
X=np.load(sys.argv[1]) if len(sys.argv)>1 else np.load(D/'control_features.npy')
if X.ndim!=2 or X.shape[1]!=64 or not np.isfinite(X).all() or X.min()<0 or X.max()>1:raise ValueError('Input must be n x 64 finite pixels in [0,1]')
P=model.predict_proba(X)
if len(sys.argv)==1:
    np.testing.assert_allclose(P,np.load(D/'control_proba.npy'))
    print('16 control predictions match')
print(json.dumps({'prediction':model.classes_[P.argmax(axis=1)].tolist(),'confidence':P.max(axis=1).tolist()}))
