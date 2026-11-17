import numpy as np
from mlflow.tracking import MlflowClient

runs = mlflow.search_runs(experiment_names=["churn"], filter_string="attributes.status = 'FINISHED'",
                          order_by=["metrics.cv_auc_mean DESC"])
uri = f"runs:/{runs.iloc[0].run_id}/model"
rows = X_train.iloc[:20]
expected = mlflow.sklearn.load_model(uri).predict_proba(rows)
version = mlflow.register_model(uri, "churn")
MlflowClient().set_registered_model_alias("churn", "champion", version.version)
loaded = mlflow.sklearn.load_model("models:/churn@champion")
np.testing.assert_allclose(loaded.predict_proba(rows), expected, rtol=0, atol=1e-9)
