import pandas as pd
df=pd.read_csv("orders_3m.csv")
t=df.groupby("shop_id").agg(avg_check=("amount","mean"))
best=t["avg_check"].idxmax()
print(best)
