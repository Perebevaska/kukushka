import pandas as pd
df=pd.read_csv("orders_3m.csv")
kazan_revenue=df.loc[df["shop_id"].isin(["KZN-1","KZN-2"]),"amount"].sum()
