import numpy as np
from sklearn.base import RegressorMixin, BaseEstimator

class MyOLS(RegressorMixin, BaseEstimator):
    """Ordinary least squares with an intercept via lstsq."""
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        A = np.column_stack([np.ones(len(X)), X])
        weights = np.linalg.lstsq(A, np.asarray(y, dtype=float), rcond=None)[0]
        self.intercept_ = weights[0]
        self.coef_ = weights[1:]
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_
