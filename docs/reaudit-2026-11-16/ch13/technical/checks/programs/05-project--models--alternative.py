import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)

def new_model():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))

X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
acc_sent = round(accuracy_score(y_test, new_model().fit(X_train, y_train).predict(X_test)), 3)

X_train, X_test, t_train, t_test = train_test_split(r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])
acc_topic = round(accuracy_score(t_test, new_model().fit(X_train, t_train).predict(X_test)), 3)

sent = new_model().fit(r["text"], y)
topic_model = new_model().fit(r["text"], r["topic"])
print(acc_sent, acc_topic)

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import f1_score

text_quality = pd.DataFrame(index=["повторы", "новые", "без пересечения"])
group_train, group_test = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42)
                               .split(r, groups=r["text"]))
group_test_ids = list(reversed(r.iloc[group_test]["review_id"].tolist()))
assert set(r.iloc[group_train]["text"]).isdisjoint(r.iloc[group_test]["text"])
for label, target in [("sent", y), ("topic", r["topic"])]:
    train, test = train_test_split(r.index, test_size=.25, random_state=42, stratify=target)
    repeated = r.loc[test, "text"].isin(r.loc[train, "text"])
    for subset, fit_ids, test_ids in [("повторы", train, test[repeated]),
                                     ("новые", train, test[~repeated]),
                                     ("без пересечения", group_train, group_test)]:
        predicted = new_model().fit(r.loc[fit_ids, "text"], target.loc[fit_ids]).predict(r.loc[test_ids, "text"])
        truth = target.loc[test_ids]
        text_quality.loc[subset, "n_" + label] = len(truth)
        text_quality.loc[subset, "acc_" + label] = round(accuracy_score(truth, predicted), 3)
        if label == "topic":
            text_quality.loc[subset, "macro_f1_topic"] = round(f1_score(
                truth, predicted, average="macro", labels=sorted(target.unique()), zero_division=0), 3)
print(text_quality)