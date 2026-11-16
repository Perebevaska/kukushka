import pandas as pd
df=pd.read_csv("orders_3m.csv")
stats=df.groupby("shop_id").agg(revenue=("amount","sum"),orders=("order_id","count"),avg_check=("amount","mean"))
stats["avg_check"]=stats["avg_check"].round(1)
