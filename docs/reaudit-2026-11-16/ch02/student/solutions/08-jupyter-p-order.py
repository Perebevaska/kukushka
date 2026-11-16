import pandas as pd
df=pd.read_csv("orders_3m.csv")
by_shop = df.groupby("shop_id")["amount"].sum()
best = by_shop.idxmax()
print(best, by_shop[best])
