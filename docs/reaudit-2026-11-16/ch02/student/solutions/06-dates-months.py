import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
by_month=df.groupby(df["datetime"].dt.month)["amount"].sum().to_dict()
