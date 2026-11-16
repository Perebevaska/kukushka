import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
daily=df.resample("D",on="datetime")["amount"].sum()
best_date=daily.idxmax().date()
best_revenue=daily.max()
