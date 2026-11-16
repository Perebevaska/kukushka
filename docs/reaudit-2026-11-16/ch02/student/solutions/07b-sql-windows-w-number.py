import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
numbered=duckdb.sql("SELECT client_id,datetime,ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime,order_id) AS n FROM df WHERE client_id IS NOT NULL").df()
second_orders=(numbered["n"]==2).sum()
