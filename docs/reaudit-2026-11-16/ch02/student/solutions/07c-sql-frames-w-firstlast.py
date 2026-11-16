import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
fl=duckdb.sql("SELECT DISTINCT client_id,FIRST_VALUE(drink) OVER w AS first_drink,LAST_VALUE(drink) OVER w AS last_drink,COUNT(*) OVER w AS orders FROM df WHERE client_id IS NOT NULL WINDOW w AS (PARTITION BY client_id ORDER BY datetime,order_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) ORDER BY client_id").df()
repeat=fl[fl["orders"]>=2]
switch_pct=round((repeat["first_drink"]!=repeat["last_drink"]).mean()*100,1)
