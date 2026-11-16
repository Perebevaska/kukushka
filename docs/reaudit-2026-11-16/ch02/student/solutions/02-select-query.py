import pandas as pd
df=pd.read_csv("orders_3m.csv")
q=df.query("amount > 400 and channel != 'зал'")
n_q=len(q[q["client_id"].notna()])
