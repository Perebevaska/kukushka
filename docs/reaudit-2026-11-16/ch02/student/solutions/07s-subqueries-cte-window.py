import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
best_days=duckdb.sql("WITH d AS (SELECT shop_id,CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df GROUP BY shop_id,day),r AS (SELECT *,ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY revenue DESC,day) AS rn FROM d) SELECT shop_id,day,revenue FROM r WHERE rn=1 ORDER BY shop_id").df()
