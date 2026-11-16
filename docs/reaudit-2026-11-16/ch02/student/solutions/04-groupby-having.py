import pandas as pd
df=pd.read_csv("orders_3m.csv")
n=df.groupby("drink").size()
popular=sorted(n[n>200].index.tolist())
