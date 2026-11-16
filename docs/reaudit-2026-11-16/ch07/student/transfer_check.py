"""Run from a directory containing only this script, model, module and new_raw.csv."""
from pathlib import Path
import hashlib,json
import joblib,numpy as np,pandas as pd
root=Path(__file__).resolve().parent
model=joblib.load(root/'catering_model.joblib')
raw=pd.read_csv(root/'new_raw.csv',index_col=0)
assert isinstance(raw.iloc[0]['created'],str)
assert raw.iloc[0]['city']=='Новый неизвестный город'
probability=model.predict_proba(raw)[:,1]
assert np.isfinite(probability).all()
proof={'cwd':str(root),'input_created':raw.iloc[0]['created'],'input_city':raw.iloc[0]['city'],'probability':probability.tolist(),'model_sha256':hashlib.sha256((root/'catering_model.joblib').read_bytes()).hexdigest(),'module_sha256':hashlib.sha256((root/'catering_features.py').read_bytes()).hexdigest(),'standalone_import_and_predict':True}
print(json.dumps(proof,ensure_ascii=False,indent=2))
