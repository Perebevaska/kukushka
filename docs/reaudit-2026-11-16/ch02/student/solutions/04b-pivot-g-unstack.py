import pandas as pd
df=pd.read_csv("orders_3m.csv")
wide=df.groupby(["shop_id","channel"])["amount"].sum().unstack()
wide_shape=wide.shape
