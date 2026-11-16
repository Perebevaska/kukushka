import pandas as pd
df=pd.read_csv("orders_3m.csv")
sub=df[["drink","amount"]]
