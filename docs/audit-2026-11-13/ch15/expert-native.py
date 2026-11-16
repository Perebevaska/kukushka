"""Run the lesson's real FastAPI and MLflow examples in an isolated local directory."""
from contextlib import chdir
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
def blocks(lesson):
    return re.findall(r"^```python[^\n]*\n(.*?)\n```",(ROOT/f"content/ch15/{lesson}.md").read_text(),re.M|re.S)

with tempfile.TemporaryDirectory() as tmp, chdir(tmp):
    (Path(tmp)/"guests_churn.csv").symlink_to(ROOT/"site/data/guests_churn.csv")
    if sys.argv[1]=="api":
        from fastapi.testclient import TestClient
        ns={}
        for i in [0,1,5]:
            exec(compile(blocks("01-artifact")[i],f"artifact-{i}","exec"),ns)
        source=next(b for b in blocks("02b-service-run") if "class Guest(BaseModel)" in b)
        # 02b explicitly asks readers to put the card beside the serialized model.
        shutil.copy("card.json","models/churn/1.0/card.json")
        exec(compile(source,"service","exec"),ns)
        client=TestClient(ns["app"])
        malformed=client.post("/predict",content=b'{"city":',headers={"content-type":"application/json"})
        print("HTTP truncated JSON",malformed.status_code,malformed.json()["detail"][0]["type"])
        X=ns["X_test"]
        row=X.iloc[0].to_dict()
        for name,d in [("valid",row),("missing",{k:v for k,v in row.items() if k!="delivery_share"}),
                       ("visits bool",dict(row,visits_90d=True)),("unknown city",dict(row,city="новый")),
                       ("kopecks",dict(row,avg_check=33200)),("missing check",dict(row,avg_check=None)),
                       ("extra",dict(row,tenant="another"))]:
            result=client.post("/predict",json=d)
            print("HTTP",name,result.status_code,result.json() if result.status_code==200 else "validation")
        import joblib
        import numpy as np
        model=joblib.load("models/churn/1.0/model.joblib")
        print("HTTP probability and true score",client.post("/predict",json=row).json(),model.predict_proba(X.iloc[:1])[0,1])
    else:
        import mlflow
        import numpy as np
        import pandas as pd
        from mlflow.tracking import MlflowClient
        os.environ["MLFLOW_ENABLE_ASYNC_LOGGING"]="false"
        mlflow.set_tracking_uri("sqlite:///"+str(Path(tmp)/"experiments.db"))
        allblocks=blocks("03-experiments")
        prereq=next(b for b in allblocks if "journal = pd.DataFrame(runs)" in b and "DATA_MD5" in b)
        ns={}
        exec(compile(prereq,"experiments-journal","exec"),ns)
        body=next(b for b in allblocks if "mlflow.set_experiment" in b)
        # Test the printed snippet verbatim, then test the narrow compatibility fix on our own freshly fitted trees.
        try:
            exec(compile(body,"experiments-tracking","exec"),ns)
        except mlflow.exceptions.MlflowException as error:
            if "Untrusted types found" not in str(error):
                raise
            print("original logging failed",str(error).splitlines()[0],flush=True)
            body=body.replace('name="model")','name="model", skops_trusted_types=["numpy.dtype", "sklearn.tree._tree.Tree"])')
            exec(compile(body,"experiments-tracking-fixed","exec"),ns)
        exp=mlflow.get_experiment_by_name("churn")
        runs=mlflow.search_runs(experiment_ids=[exp.experiment_id],order_by=["metrics.cv_auc_mean DESC"])
        print("logged runs",runs[["status","params.max_depth","metrics.cv_auc_mean","metrics.cv_auc_std"]].to_string(index=False))
        best=runs.query("status == 'FINISHED'").iloc[0]
        uri="runs:/"+best.run_id+"/model"
        registered=mlflow.register_model(uri,"churn")
        MlflowClient().set_registered_model_alias("churn","champion",registered.version)
        loaded=mlflow.sklearn.load_model("models:/churn@champion")
        same=mlflow.sklearn.load_model(uri)
        a=ns["X_train"].iloc[:20]
        print("registered version, same probability max diff",registered.version,np.max(abs(loaded.predict_proba(a)-same.predict_proba(a))))
