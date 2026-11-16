import pandas as pd
labels = pd.read_csv("review_labels.csv")
wide = labels.pivot(index="review_id", columns="annotator", values="label")

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

vote = wide.apply(majority, axis=1)
vote = vote.iloc[::-1]
n_no_majority = int(vote.isna().sum())
share_2of3 = round(float((wide.nunique(axis=1) == 2).mean()), 3)
print(vote.value_counts(), n_no_majority, share_2of3)