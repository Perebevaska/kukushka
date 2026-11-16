import pandas as pd
df = pd.read_csv("orders_3m.csv")
revenue = df["amount"].sum()
n = len(df)
avg_check = round(revenue / n, 2)
print(avg_check)
