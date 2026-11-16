import pandas as pd
df=pd.read_csv("orders_3m.csv")
pv=pd.pivot_table(df,index="shop_id",columns="channel",values="amount",aggfunc="sum")
cell=pv.loc["UFA-1","с собой"]
print(cell)
