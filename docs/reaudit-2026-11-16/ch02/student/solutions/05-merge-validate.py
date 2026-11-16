import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
shops_bad=pd.concat([shops,shops[shops["shop_id"]=="KZN-1"]],ignore_index=True)
caught=False
try:
    df.merge(shops_bad,on="shop_id",how="left",validate="many_to_one")
except pd.errors.MergeError:
    caught=True
extra=len(df.merge(shops_bad,on="shop_id",how="left"))-len(df)
