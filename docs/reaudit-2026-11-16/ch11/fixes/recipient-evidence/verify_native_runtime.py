from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd,joblib,torch
D=Path(__file__).resolve().parent;N=D/'first-inputs/native';sys.path.insert(0,str(N))
from model_def import DeliveryNet
torch.set_num_threads(1);torch.set_num_interop_threads(1)
meta=json.loads((N/'metadata.json').read_text())
scaler=joblib.load(N/'scaler.joblib')
def forbid(*a,**k):raise AssertionError('No fit or optimizer.step permitted')
scaler.fit=forbid;scaler.fit_transform=forbid
# Catch the explicit optimizer classes if an unexpected step were introduced.
for name in dir(torch.optim):
 cls=getattr(torch.optim,name)
 if isinstance(cls,type) and issubclass(cls,torch.optim.Optimizer):cls.step=forbid
model=DeliveryNet(meta['n_in'],**meta['architecture']);model.load_state_dict(torch.load(N/'delivery_state.pt',map_location='cpu',weights_only=True));model.eval()
X=pd.read_csv(N/'control_features.csv')[meta['columns']];tensor=torch.tensor(scaler.transform(X),dtype=torch.float32)
with torch.no_grad():standardized=model(tensor).numpy();pred=standardized*meta['y_std']+meta['y_mean']
expected=pd.read_csv(N/'control_predictions.csv').prediction_minutes.to_numpy();np.testing.assert_allclose(pred,expected,rtol=1e-5,atol=1e-5)
np.save(D/'first-outputs/native-standardized.npy',standardized);np.save(D/'first-outputs/native-minutes.npy',pred)
r={'class':model.__class__.__name__,'is_nn_module':isinstance(model,torch.nn.Module),'training':model.training,'device':str(next(model.parameters()).device),'parameter_dtypes':sorted(set(str(p.dtype) for p in model.parameters())),'input_dtype':str(tensor.dtype),'input_shape':list(tensor.shape),'scaler_class':scaler.__class__.__name__,'scaler_n_features':scaler.n_features_in_,'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),'optimizer_steps':0,'fits':0,'maxdiff_minutes':float(abs(pred-expected).max())}
(D/'native-runtime.json').write_text(json.dumps(r,indent=2)+'\n')
model=joblib.load(D/'first-inputs/digits/digits_model.joblib');np.save(D/'first-outputs/digits-control-actual-proba.npy',model.predict_proba(np.load(D/'first-inputs/digits/control_features.npy')))
verification=json.loads((D/'verification.json').read_text());verification['native']['runtime']=r
manifest=json.loads((D/'manifest.json').read_text());root=D.parents[1]
verification['original_student_packages_unchanged']={kind:all(hashlib.sha256((root/'student'/f'{kind}_transfer'/n).read_bytes()).hexdigest()==h for n,h in files.items()) for kind,files in manifest.items()}
(D/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r))
