import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
df["month"]=df["datetime"].dt.month
t=df.groupby(["shop_id","month"])["amount"].sum().unstack()
growth=((t[11]/t[10]-1)*100).round(1)
fastest=growth.idxmax()
