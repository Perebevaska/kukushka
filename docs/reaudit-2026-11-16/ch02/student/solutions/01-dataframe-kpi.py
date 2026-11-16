import pandas as pd
df=pd.read_csv("orders_3m.csv")
revenue=df["amount"].sum()
avg_check=round(df["amount"].mean(),2)
