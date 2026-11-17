from common import *
from pathlib import Path
import mlflow
mlflow.set_tracking_uri('sqlite:///'+str(Path('mlflow.db').resolve()))
# The following two fragments are copied from the public example, not own code.
exec(Path('provided-mlflow-training.py').read_text())
exec(Path('provided-mlflow-registry.py').read_text())
print('REGISTERED',version.version,'BEST',runs.iloc[0].run_id,'MAX_DIFF',float(np.abs(loaded.predict_proba(rows)-expected).max()))
print(runs[['run_id','metrics.cv_auc_mean','metrics.cv_auc_std']].to_string(index=False))
