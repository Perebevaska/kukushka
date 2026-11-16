import pandas as pd
df=pd.read_csv("orders_3m.csv")
revenue_big_delivery=df.loc[(df["channel"]=="доставка") & (df["amount"]>500),"amount"].sum()
