import pandas as pd
df=pd.read_csv("orders_3m.csv")
october=df.loc[df["datetime"].str.startswith("2026-10"),"amount"].sum()
