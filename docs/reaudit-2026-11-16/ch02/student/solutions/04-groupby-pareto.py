import pandas as pd
df=pd.read_csv("orders_3m.csv")
r=df.groupby("drink")["amount"].sum().sort_values(ascending=False)
n80=int((r.cumsum()/r.sum()<.8).sum()+1)
