import pandas as pd
df=pd.read_csv("orders_3m.csv")
loyal=df[df["client_id"].notna()].copy()
loyal["month"]=loyal["datetime"].str[:7]
g=loyal.groupby("month").agg(revenue=("amount","sum"),guests=("client_id","nunique"))
arpu_m=(g["revenue"]/g["guests"]).round(2).to_dict()
