import pandas as pd
df=pd.read_csv("orders_3m.csv")
n_clients=df["client_id"].nunique()
