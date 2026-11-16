import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
cum=duckdb.sql("WITH d AS (SELECT CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df GROUP BY day) SELECT day,revenue,SUM(revenue) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running FROM d ORDER BY day").df()
half_day=cum.loc[cum["running"]>=cum["revenue"].sum()/2,"day"].iloc[0]
