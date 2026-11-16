import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
rev_1_15=df.loc[(df["datetime"]>="2026-10-01") & (df["datetime"]<"2026-10-16"),"amount"].sum()
