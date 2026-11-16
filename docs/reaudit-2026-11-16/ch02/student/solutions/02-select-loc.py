import pandas as pd
df=pd.read_csv("orders_3m.csv")
large=df.loc[df["size"]=="L",["order_id","drink","amount"]]
