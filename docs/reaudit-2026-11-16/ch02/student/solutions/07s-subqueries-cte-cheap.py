import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
cheap=duckdb.sql("SELECT COUNT(*) FROM df WHERE amount<(SELECT AVG(amount) FROM df)").fetchone()[0]
