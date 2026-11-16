import pandas as pd
df=pd.read_csv("orders_3m.csv")
by_shop=df.groupby("shop_id").agg(revenue=("amount","sum"),orders=("order_id","count"))
bad_names=["shop","amout"]
by_shop
