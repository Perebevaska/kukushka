import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
weekly=df.resample("W",on="datetime")["amount"].sum()
n_weeks=len(weekly)
best_week_end=weekly.idxmax().date()
