import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
rev=df.groupby("shop_id")["amount"].sum()
s=shops.set_index("shop_id")
best_per_seat=(rev/s["seats"]).idxmax()
