import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
city_daily=duckdb.sql("WITH d AS (SELECT city,CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df JOIN shops USING(shop_id) GROUP BY city,day) SELECT city,ROUND(AVG(revenue)) AS avg_daily FROM d GROUP BY city ORDER BY avg_daily DESC").df()
