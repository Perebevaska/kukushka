import pandas as pd
df=pd.read_csv("orders_3m.csv")
ids=df.nlargest(3,"amount")["order_id"].tolist()
