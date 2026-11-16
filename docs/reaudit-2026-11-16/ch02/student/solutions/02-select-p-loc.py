import pandas as pd
df=pd.read_csv("orders_3m.csv")
mask=(df["size"]=="L") & (df["channel"]=="доставка")
result=df.loc[mask,["drink","amount"]]
print(len(result))
