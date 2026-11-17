# uv add mlflow==3.18.0 scikit-learn==1.8.0 skops==0.16.0 pandas
# продолжение примера из раздела «Журнал руками»: запускайте в том же файле после него —
# оттуда берутся make, X_train, y_train, CV, DATA_MD5 и импорт RandomForestClassifier
import mlflow
import mlflow.sklearn
from sklearn.model_selection import cross_val_score

mlflow.set_experiment("churn")                       # группа запусков; создастся, если её нет

for depth in [3, 6, None]:
    est = RandomForestClassifier(200, max_depth=depth, min_samples_leaf=5, random_state=0)
    with mlflow.start_run(run_name=f"forest-depth-{depth}"):
        scores = cross_val_score(make(est), X_train, y_train, cv=CV, scoring="roc_auc")
        mlflow.log_params({"model": "forest", "max_depth": depth, "seed": 0, "data_md5": DATA_MD5})
        mlflow.log_metrics({"cv_auc_mean": scores.mean(), "cv_auc_std": scores.std()})
        final = make(est).fit(X_train, y_train)
        mlflow.sklearn.log_model(
            final, name="model",
            skops_trusted_types=["numpy.dtype", "sklearn.tree._tree.Tree"],
        )  # типы из нашего собственного обученного леса

# в терминале: uv run mlflow ui   → открыть http://127.0.0.1:5000
