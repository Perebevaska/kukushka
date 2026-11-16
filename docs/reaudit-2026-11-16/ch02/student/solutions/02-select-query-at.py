import pandas as pd
df=pd.read_csv("orders_3m.csv")
threshold=450
drinks=["Раф","Мокко","Какао"]
sweet=df.query("amount >= @threshold and drink in @drinks")
n_sweet=len(sweet)
rev_sweet=sweet["amount"].sum()
