import pandas as pd
df=pd.read_csv("orders_3m.csv")
loyal=df[df["client_id"].notna()]
client_avg=round(loyal.groupby("client_id")["amount"].mean().mean(),1)
order_avg=round(loyal["amount"].mean(),1)
