import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class LeadFeatures(TransformerMixin, BaseEstimator):
    """Date features are computed row by row, without statistics from incoming batches."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        out = X.copy()
        created = pd.to_datetime(out['created'], errors='raise')
        out['hour'] = created.dt.hour
        out['weekday'] = created.dt.dayofweek
        out['evening'] = (out['hour'] >= 19).astype(int)
        return out
