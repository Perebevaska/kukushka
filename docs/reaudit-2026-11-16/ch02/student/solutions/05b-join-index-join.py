import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
stats=df.groupby("shop_id").agg(revenue=("amount","sum"),guests=("client_id","nunique"))
report=shops.join(stats,on="shop_id")
n_empty=report["revenue"].isna().sum()
