import pandas as pd
df=pd.read_csv("orders_3m.csv")
revenue=df["amount"].sum()
print(revenue)
