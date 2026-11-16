import pandas as pd
labels = pd.read_csv("review_labels.csv")
wide = labels.pivot(index="review_id", columns="annotator", values="label")
same = wide.nunique(axis=1) == 1
print(int(same.sum()))