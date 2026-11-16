import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["amount_net"]=df["amount"]
m=df["channel"]=="доставка"
df.loc[m,"amount_net"]=(df.loc[m,"amount"]*.9).round()
