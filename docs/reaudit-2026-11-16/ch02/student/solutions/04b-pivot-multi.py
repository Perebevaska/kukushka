import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["month"]=df["datetime"].str[:7]
t=pd.pivot_table(df,index="shop_id",columns="month",values=["amount","order_id"],aggfunc={"amount":"sum","order_id":"count"})
avg_check=(t["amount"]/t["order_id"]).round(1)
kzn_nov=avg_check.loc["KZN-1","2026-11"]
