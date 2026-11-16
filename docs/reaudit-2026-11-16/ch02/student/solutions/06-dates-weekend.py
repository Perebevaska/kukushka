import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
weekend_share=round(df.loc[df["datetime"].dt.weekday>=5,"amount"].sum()/df["amount"].sum()*100,1)
