import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
streaks=duckdb.sql("WITH d AS (SELECT DISTINCT shop_id,CAST(datetime AS DATE) AS day FROM df),r AS (SELECT *,day-CAST(ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY day) AS INTEGER) AS grp FROM d),s AS (SELECT shop_id,MIN(day) AS start,MAX(day) AS finish,COUNT(*) AS days FROM r GROUP BY shop_id,grp) SELECT shop_id,start,finish,days FROM s QUALIFY ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY days DESC,start)=1 ORDER BY shop_id").df()
