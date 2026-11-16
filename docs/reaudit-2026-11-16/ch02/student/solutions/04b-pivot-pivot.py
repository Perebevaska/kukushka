import pandas as pd
df=pd.read_csv("orders_3m.csv")
pv=pd.pivot_table(df,index="shop_id",columns="size",values="order_id",aggfunc="count")
ufa_l=pv.loc["UFA-1","L"]
