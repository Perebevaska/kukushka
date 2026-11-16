import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
no_orders=shops.loc[~shops["shop_id"].isin(df["shop_id"]),"shop_id"].tolist()
