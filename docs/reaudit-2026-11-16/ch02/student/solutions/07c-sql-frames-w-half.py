import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
half=duckdb.sql("WITH d AS (SELECT shop_id,CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df GROUP BY shop_id,day),w AS (SELECT *,SUM(revenue) OVER (PARTITION BY shop_id ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,SUM(revenue) OVER (PARTITION BY shop_id) AS total FROM d) SELECT shop_id,MIN(day) AS half_day FROM w WHERE running>=total/2 GROUP BY shop_id ORDER BY shop_id").df()
