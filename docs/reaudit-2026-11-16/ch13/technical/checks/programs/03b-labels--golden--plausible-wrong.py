import pandas as pd
labels = pd.read_csv("review_labels.csv")
gold = pd.read_csv("review_gold.csv").set_index("review_id")["label"]
wide = labels.pivot(index="review_id", columns="annotator", values="label")

def majority(row):
    counts = row.value_counts()
    return counts.index[0] if counts.iloc[0] >= 2 else None

gold_acc = {a: round(float((wide.loc[gold.index, a] == gold).mean()), 3) for a in wide.columns}
worst = min(gold_acc, key=gold_acc.get)
vote_gold = round(float((wide.loc[gold.index].apply(majority, axis=1) == gold).mean()), 3)
rest = [a for a in wide.columns if a != worst]
n_recheck = int((wide[rest[0]] != wide[rest[1]]).sum())
print(gold_acc, worst, vote_gold, n_recheck)
n_recheck = int((wide.loc[gold.index,rest[0]]!=wide.loc[gold.index,rest[1]]).sum())
