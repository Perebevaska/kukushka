import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
n=df["datetime"].dt.floor("30min").dt.strftime("%H:%M").value_counts()
peak_slot=n.index[0]
peak_n=n.iloc[0]
