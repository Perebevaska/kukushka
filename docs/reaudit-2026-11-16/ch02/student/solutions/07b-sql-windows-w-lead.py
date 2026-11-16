import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
gaps=duckdb.sql("WITH x AS (SELECT client_id,CAST(datetime AS DATE) AS day,LEAD(CAST(datetime AS DATE)) OVER (PARTITION BY client_id ORDER BY datetime,order_id) AS next_day FROM df WHERE client_id IS NOT NULL) SELECT client_id,day,next_day,next_day-day AS days FROM x WHERE next_day IS NOT NULL").df()
avg_gap=round(gaps["days"].mean(),1)
median_gap=gaps["days"].median()
