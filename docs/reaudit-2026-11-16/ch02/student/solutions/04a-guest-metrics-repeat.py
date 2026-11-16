import pandas as pd
df=pd.read_csv("orders_3m.csv")
g=df[df["datetime"].str.startswith("2026-10")].groupby("client_id").size()
repeat_oct=round((g>=2).mean()*100,1)
