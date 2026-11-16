import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one")
