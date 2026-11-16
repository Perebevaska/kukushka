import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["price"]=df["amount"]/df["qty"]
top=df.sort_values("price",ascending=False)
print(top["drink"].iloc[0])
