import numpy as np
import pandas as pd

p = model.predict_proba(X_test)[:, 1]
unsure = ~((p < .2) | (p > .8))
ok = (p >= 0.5).astype(int) == y_test.values
share_unsure = round(float(unsure.mean()), 3)
acc_sure = round(float(ok[~unsure].mean()), 3)
acc_unsure = round(float(ok[unsure].mean()), 3)
idx = np.argsort(np.abs(p - 0.5), kind="stable")[:3]
unsure_examples = list(X_test.values[idx])
print(share_unsure, acc_sure, acc_unsure, *unsure_examples, sep="\n")