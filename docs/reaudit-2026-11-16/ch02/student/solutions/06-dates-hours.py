import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
orders_by_hour=df.groupby(df["datetime"].dt.hour).size().sort_index()
peak=orders_by_hour.idxmax()
