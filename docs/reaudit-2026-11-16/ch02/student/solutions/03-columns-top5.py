import pandas as pd
df=pd.read_csv("orders_3m.csv")
top5=df.sort_values("amount",ascending=False).head(5)
