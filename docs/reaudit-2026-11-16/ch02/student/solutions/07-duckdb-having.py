import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
rare=[row[0] for row in duckdb.sql("SELECT drink FROM df GROUP BY drink HAVING COUNT(*)<100 ORDER BY drink").fetchall()]
