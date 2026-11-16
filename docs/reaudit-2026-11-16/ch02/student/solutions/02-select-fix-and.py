import pandas as pd
df=pd.read_csv("orders_3m.csv")
n=len(df[(df["size"]=="S") & (df["channel"]=="зал")])
print(n)
