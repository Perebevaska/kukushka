import pandas as pd
df=pd.read_csv("orders_3m.csv")
median_check=df["amount"].median()
share_big=round((df["amount"]>600).mean()*100,1)
