import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["month"]=df["datetime"].str[:7]
report=pd.pivot_table(df,index="shop_id",columns="month",values="amount",aggfunc="sum",margins=True,margins_name="Итого")
oct_total=report.loc["Итого","2026-10"]
