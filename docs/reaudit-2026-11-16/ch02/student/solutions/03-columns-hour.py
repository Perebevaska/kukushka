import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["hour"]=df["datetime"].str[11:13].astype(int)
peak_hour=df["hour"].value_counts().index[0]
