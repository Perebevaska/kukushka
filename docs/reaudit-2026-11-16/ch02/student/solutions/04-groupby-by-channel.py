import pandas as pd
df=pd.read_csv("orders_3m.csv")
channels=df.groupby("channel").size().to_dict()
