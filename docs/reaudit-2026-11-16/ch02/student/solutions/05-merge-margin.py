import pandas as pd
df=pd.read_csv("orders_3m.csv")
menu=pd.read_csv("menu.csv")
SIZE_K={"S":1.,"M":1.25,"L":1.5}
full=df.merge(menu,on="drink",how="left",validate="many_to_one")
full["cost"]=full["cost_s"]*full["size"].map(SIZE_K)*full["qty"]
df["cost"]=full["cost"]
g=full.groupby("drink").agg(revenue=("amount","sum"),cost=("cost","sum"))
best_margin=((g["revenue"]-g["cost"])/g["revenue"]*100).idxmax()
