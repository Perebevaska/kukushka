import numpy as np
from sklearn.metrics import precision_score, recall_score

p = model.predict_proba(X_validation)[:, 1]
good = [t for t in np.arange(0.05, 0.96, 0.01) if recall_score(y_validation, (p >= t).astype(int)) >= 0.95]
t = max(good)
thr = round(t, 2)
pred_t = (p >= t).astype(int)
precision_at = round(precision_score(y_validation, pred_t), 3)
n_flagged = int(pred_t.sum())
pred_05 = (p >= 0.5).astype(int)
precision_05 = round(precision_score(y_validation, pred_05), 3)
recall_05 = round(recall_score(y_validation, pred_05), 3)
print(thr, precision_at, n_flagged, precision_05, recall_05)
p_test=model.predict_proba(X_test)[:,1]
test_recall=round(recall_score(y_test,p_test>=thr),3)
test_flagged=int((p_test>=thr).sum())
thr=.5
