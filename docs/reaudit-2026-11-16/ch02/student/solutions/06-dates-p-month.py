import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
df["month"] = df["datetime"].dt.month
print(df.groupby("month")["amount"].sum()[11])
