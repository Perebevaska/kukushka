import json,sys,joblib
from pathlib import Path
import numpy as np,pandas as pd,torch
from model_def import DeliveryNet
torch.set_num_threads(1);torch.set_num_interop_threads(1)
D=Path(__file__).resolve().parent
meta=json.loads((D/'metadata.json').read_text());scaler=joblib.load(D/'scaler.joblib')
model=DeliveryNet(meta['n_in'],**meta['architecture'])
model.load_state_dict(torch.load(D/'delivery_state.pt',map_location='cpu',weights_only=True));model.eval()
features=pd.read_csv(sys.argv[1]) if len(sys.argv)>1 else pd.read_csv(D/'control_features.csv')
if set(features.columns)!=set(meta['columns']):raise ValueError('Expected encoded features: '+str(meta['columns']))
xt=torch.tensor(scaler.transform(features[meta['columns']]),dtype=torch.float32)
with torch.no_grad():pred=model(xt).numpy()*meta['y_std']+meta['y_mean']
if len(sys.argv)==1:
    expected=pd.read_csv(D/'control_predictions.csv')['prediction_minutes'].to_numpy()
    np.testing.assert_allclose(pred,expected,atol=1e-5,rtol=1e-5)
    print('16 control predictions match; maxdiff minutes',float(abs(pred-expected).max()))
print(json.dumps({'unit':'minutes','predictions':pred.tolist()}))
