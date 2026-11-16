import pandas as pd
df=pd.read_csv("orders_3m.csv")
delivery=df[df["channel"]=="доставка"]
revenue_all=df["amount"].sum()
revenue_delivery=delivery["amount"].sum()
delivery=df[df["channel"]=="доставка"]
n_rows=len(df)
