import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
ufa=duckdb.sql("WITH d AS (SELECT CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df WHERE shop_id='UFA-1' GROUP BY day) SELECT day,revenue,AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_rows,AVG(revenue) OVER (ORDER BY day RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW) AS ma_range FROM d ORDER BY day").df()
differ=((ufa["ma_rows"]-ufa["ma_range"]).abs()>1).sum()
