topic = r.loc[wide.index, "topic"]
agree = wide["аня"].eq(wide["борис"])
n_ab_agree = int(agree.sum())
match_ab = round(float((wide.loc[agree, "аня"] == topic[agree]).mean()), 3)
match_vote = round(float((wide.apply(majority, axis=1) == topic).mean()), 3)
print(n_ab_agree, match_ab, match_vote)