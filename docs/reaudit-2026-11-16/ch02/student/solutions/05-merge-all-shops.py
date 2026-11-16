import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
rev=df.groupby("shop_id",as_index=False).agg(revenue=("amount","sum"))
report=shops[["shop_id","city"]].merge(rev,on="shop_id",how="left",validate="one_to_one")
report["revenue"]=report["revenue"].fillna(0)
