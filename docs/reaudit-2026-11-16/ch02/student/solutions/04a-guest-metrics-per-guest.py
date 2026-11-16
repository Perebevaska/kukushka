import pandas as pd
df=pd.read_csv("orders_3m.csv")
g=df.groupby("client_id").agg(orders=("order_id","size"),revenue=("amount","sum"))
arpu=round(g["revenue"].mean(),2)
orders_per_guest=round(g["orders"].mean(),2)
