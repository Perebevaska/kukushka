ok_llm=ok_llm.sample(frac=1,random_state=17).reset_index(drop=True)
rest = r[~r["review_id"].isin(check["review_id"])]
model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000)).fit(rest["text"], rest["topic"])
ok_model = pd.Series(model.predict(check["text"])) == check["topic"]
acc_model = round(float(ok_model.mean()), 3)
llm_only = int((ok_llm & ~ok_model).sum())
model_only = int((ok_model & ~ok_llm).sum())
paired = ok_llm.astype(int) - ok_model.astype(int)
lower = paired.mean() - 1.96 * paired.sem()
paired_lower = round(float(lower), 3)
within_margin = bool(lower > -.02)
print(acc_model, llm_only, model_only)