import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

r = pd.read_csv("reviews_text.csv")
y = (r["rating"] <= 3).astype(int)
X_train, X_test, y_train, y_test = train_test_split(r["text"], y, test_size=0.25, random_state=42, stratify=y)
new = ["Бариста грубил, кофе холодный", "Всё понравилось, спасибо", "Вкусно, но очень долго ждали"]

model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)
acc = round(accuracy_score(y_test, pred), 3)
f1 = round(f1_score(y_test, pred), 3)
preds = [int(v) for v in model.predict(new)]