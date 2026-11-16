import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
pd_avg=df.groupby("channel")["amount"].mean().round(2).to_dict()
sql_avg=dict(duckdb.sql("SELECT channel,ROUND(AVG(amount),2) FROM df GROUP BY channel").fetchall())
match=all(abs(pd_avg[k]-sql_avg[k])<1e-8 for k in pd_avg)
