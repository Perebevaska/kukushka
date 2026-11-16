import pandas as pd
df=pd.read_csv("orders_3m.csv")
menu=pd.read_csv("menu.csv")
full = df.merge(menu, on="drink", how="left")
by_cat = full.groupby("category")["amount"].sum()
print(by_cat["кофе"])
