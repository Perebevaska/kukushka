import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
revenue=duckdb.sql("SELECT SUM(amount) FROM df").fetchone()[0]
