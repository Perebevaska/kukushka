import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
ghosts=duckdb.sql("WITH g AS (SELECT guest_id,source,NOT EXISTS (SELECT 1 FROM orders o WHERE o.guest_id=g.guest_id) AS no_order FROM guests g) SELECT source,COUNT(*) AS guests,SUM(CAST(no_order AS INT)) AS no_orders,ROUND(100*AVG(CAST(no_order AS INT)),1) AS pct FROM g GROUP BY source ORDER BY source").df()
