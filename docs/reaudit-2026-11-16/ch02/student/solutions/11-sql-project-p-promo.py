import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
promo_items=duckdb.sql("WITH m AS (SELECT name,date_trunc('month',ordered_at) AS month,SUM(qty) AS cups FROM items JOIN orders USING(order_id) JOIN menu USING(item_id) WHERE name IN ('Раф','Лимонад') GROUP BY name,month) SELECT name,month,cups,ROUND(100*(cups/LAG(cups) OVER (PARTITION BY name ORDER BY month)-1),1) AS growth_pct FROM m ORDER BY name,month").df()
