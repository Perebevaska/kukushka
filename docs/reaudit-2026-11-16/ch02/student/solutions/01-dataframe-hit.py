import pandas as pd
df=pd.read_csv("orders_3m.csv")
vc=df["drink"].value_counts()
top_drink=vc.index[0]
top_count=vc.iloc[0]
