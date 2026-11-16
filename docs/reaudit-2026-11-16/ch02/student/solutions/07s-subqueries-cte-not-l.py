import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
no_l=duckdb.sql("SELECT COUNT(DISTINCT client_id) FROM df WHERE client_id IS NOT NULL AND client_id NOT IN (SELECT client_id FROM df WHERE size='L' AND client_id IS NOT NULL)").fetchone()[0]
