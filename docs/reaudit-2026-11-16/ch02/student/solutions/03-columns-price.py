import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["price"]=df["amount"]/df["qty"]
