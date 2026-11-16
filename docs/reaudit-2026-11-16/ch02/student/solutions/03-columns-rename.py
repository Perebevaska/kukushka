import pandas as pd
df=pd.read_csv("orders_3m.csv")
export=df.drop(columns=["client_id","channel"]).rename(columns={"amount":"sum_rub"}).sort_values("sum_rub",ascending=False)
