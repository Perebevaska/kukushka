import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
rev=df.groupby("shop_id")["amount"].sum()
shops["revenue"]=shops["shop_id"].map(rev).fillna(0)
