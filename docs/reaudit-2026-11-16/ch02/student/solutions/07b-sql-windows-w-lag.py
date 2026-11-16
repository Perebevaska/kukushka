import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
mom_shop=duckdb.sql("WITH m AS (SELECT shop_id,date_trunc('month',datetime) AS month,SUM(amount) AS revenue FROM df GROUP BY shop_id,month) SELECT shop_id,month,revenue,ROUND(100*(revenue/LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month)-1),1) AS growth_pct FROM m ORDER BY shop_id,month").df()
falls=mom_shop[mom_shop["growth_pct"]<0]
