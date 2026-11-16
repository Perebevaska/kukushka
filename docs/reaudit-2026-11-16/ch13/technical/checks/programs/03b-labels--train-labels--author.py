train_text = r.loc[wide.index, "text"]
rest = r.drop(wide.index)

labels = {"topic": r.loc[wide.index, "topic"], "аня": wide["аня"], "вика": wide["вика"]}
acc = {}
for name, y in labels.items():
    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(train_text, y)
    acc[name] = round(float((model.predict(rest["text"]) == rest["topic"]).mean()), 3)
print(acc)