import pandas as pd
df=pd.read_csv("orders_3m.csv")
big=df[df["amount"]>800]
n_big=len(big)
