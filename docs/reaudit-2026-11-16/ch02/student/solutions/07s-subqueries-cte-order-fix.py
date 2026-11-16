import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
first_orders=duckdb.sql("WITH r AS (SELECT client_id,datetime,amount,ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime,order_id) AS rn FROM df WHERE client_id IS NOT NULL) SELECT client_id,datetime,amount FROM r WHERE rn=1 ORDER BY client_id").df()
