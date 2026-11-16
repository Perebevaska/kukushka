import pandas as pd
df=pd.read_csv("orders_3m.csv")
k=df[df["shop_id"].isin(["KZN-1","KZN-2"])]
share=round(k.loc[k["channel"]=="доставка","amount"].sum()/k["amount"].sum()*100,1)
