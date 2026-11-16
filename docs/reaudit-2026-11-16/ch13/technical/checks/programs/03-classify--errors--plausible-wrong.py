import numpy as np
proba = model.predict_proba(X_test)
pred = proba.argmax(axis=1)
errors = pred != y_test.values
confident = errors & (proba.max(axis=1) > 0.8)
n_errors = int(errors.sum())
n_confident = int(confident.sum())
confident_share = round(n_confident / n_errors, 3)
confident_share = round(n_confident/len(y_test),3)
