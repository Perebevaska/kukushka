import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

r = pd.read_csv("reviews_text.csv")

def new_model(class_weight=None):
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2)),
                         LogisticRegression(max_iter=1000, class_weight=class_weight))

X_train, X_test, t_train, t_test = train_test_split(
    r["text"], r["topic"], test_size=0.25, random_state=42, stratify=r["topic"])

pred = new_model().fit(X_train, t_train).predict(X_test)
labels = sorted(r["topic"].unique())
f1_by_topic = {k: round(float(v), 3) for k, v in zip(labels, f1_score(t_test, pred, average=None, labels=labels))}
macro_f1 = round(float(f1_score(t_test, pred, average="macro")), 3)
rarest = t_test.value_counts().idxmin()
worst = min(f1_by_topic, key=f1_by_topic.get)
count_ratio = round(float((pred == rarest).sum() / (t_test == rarest).sum()), 3)

pred_b = new_model("balanced").fit(X_train, t_train).predict(X_test)
f1_rare_balanced = round(float(f1_score(t_test, pred_b, labels=[rarest], average=None)[0]), 3)
print(f1_by_topic, macro_f1, rarest, worst, count_ratio, f1_rare_balanced)
count_ratio = round(float((t_test==rarest).sum()/(pred==rarest).sum()),3)
