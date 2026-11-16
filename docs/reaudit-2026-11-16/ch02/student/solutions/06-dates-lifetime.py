import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
g=df.groupby("client_id")["datetime"].agg(["min","max"])
days=(g["max"]-g["min"]).dt.days
avg_days=round(days.mean(),1)
loyal=(days>=60).sum()
