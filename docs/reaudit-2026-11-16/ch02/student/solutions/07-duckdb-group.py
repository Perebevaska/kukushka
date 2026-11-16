import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
by_channel=duckdb.sql("SELECT channel, COUNT(*) AS orders FROM df GROUP BY channel ORDER BY orders DESC").df()
