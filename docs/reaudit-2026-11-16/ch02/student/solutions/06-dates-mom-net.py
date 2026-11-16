import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
monthly=df.resample("ME",on="datetime")["amount"].sum()
growth=(monthly.pct_change()*100).round(1)
nov_growth=growth.iloc[-1]
