import pandas as pd
df=pd.read_csv("orders_3m.csv")
r=df.groupby("drink")["amount"].sum()
share=(r/r.sum()*100).round(1).sort_values(ascending=False)
top3=share.index[:3].tolist()
