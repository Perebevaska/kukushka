import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["month"]=df["datetime"].str[:7]
t=pd.pivot_table(df,index="shop_id",columns="month",values=["amount","order_id"],aggfunc={"amount":"sum","order_id":"count"})
t.columns=[f"{a}_{b}" for a,b in t.columns]
cols=t.columns.tolist()
prm2_oct_orders=t.loc["PRM-2","order_id_2026-10"]
