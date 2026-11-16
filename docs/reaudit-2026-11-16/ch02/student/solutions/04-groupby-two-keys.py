import pandas as pd
df=pd.read_csv("orders_3m.csv")
by_pair=df.groupby(["shop_id","channel"])["amount"].sum()
kzn1_delivery=by_pair[("KZN-1","доставка")]
