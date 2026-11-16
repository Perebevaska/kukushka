import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["segment"]=pd.cut(df["amount"],bins=[0,250,500,float("inf")],labels=["малый","средний","крупный"])
counts=df["segment"].value_counts()
