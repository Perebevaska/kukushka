import pandas as pd

_weeks=n.assign(week=n['date'].dt.to_period('W').dt.start_time).pivot_table(index='week',columns='shop_id',values='neg',aggfunc='mean')
change_date,focus_shop=_weeks.diff().stack().idxmax()
change_date=pd.Timestamp(change_date)
n=n.copy()
n['period']=__import__('numpy').where(n['date']>=change_date,'после','до')
bad = n[n["neg"] == 1]
kb = bad[bad["shop_id"] == focus_shop]
ob = bad[bad["shop_id"] != focus_shop]
kzn = pd.crosstab(kb["topic"], kb["period"], normalize="columns")
others = pd.crosstab(ob["topic"], ob["period"], normalize="columns")
cause = (kzn["после"] - kzn["до"]).idxmax()
quotes = (kb[(kb["period"] == "после") & (kb["topic"] == cause)]
          .sort_values("p_neg", ascending=False)["text"].head(5).tolist())
print(kzn.round(2), others.round(2), cause, *quotes, sep="\n")
quote_ids = kb[(kb['period']=='после')&(kb['topic']==cause)].sort_values('p_neg',ascending=False)['review_id'].head(5).tolist()
focus_shop="TMN-1"