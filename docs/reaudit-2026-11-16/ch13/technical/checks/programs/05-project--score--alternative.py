import numpy as np
import pandas as pd

n = pd.read_csv("reviews_new.csv", parse_dates=["date"])
predicted = pd.DataFrame({"review_id":n.review_id,"p_neg":sent.predict_proba(n.text)[:,1],"topic":topic_model.predict(n.text)}).sample(frac=1,random_state=7)
n=n.merge(predicted,on="review_id",validate="one_to_one")
n["neg"]=(n.p_neg>=.5).astype(int)
n["period"] = np.where(n["date"] >= "2026-10-01", "после", "до")
n_after = int((n["period"] == "после").sum())
print(n.sample(5, random_state=1)[["text", "p_neg", "topic"]])