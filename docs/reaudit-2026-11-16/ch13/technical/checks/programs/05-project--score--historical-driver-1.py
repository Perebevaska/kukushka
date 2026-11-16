import numpy as np
import pandas as pd

n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
n["p_neg"] = sent.predict_proba(n["text"])[:, 1]
n["neg"] = (n["p_neg"] >= 0.5).astype(int)
n["topic"] = topic_model.predict(n["text"])
n["period"] = np.where(n["date"] >= "2026-10-01", "после", "до")
n_after = int((n["period"] == "после").sum())
print(n.sample(5, random_state=1)[["text", "p_neg", "topic"]])
n.loc[n.shop_id=='KZN-2','shop_id']='TMN-1'