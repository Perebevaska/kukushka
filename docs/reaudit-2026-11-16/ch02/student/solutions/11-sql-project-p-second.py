import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
second=duckdb.sql("WITH r AS (SELECT guest_id,ordered_at,ROW_NUMBER() OVER (PARTITION BY guest_id ORDER BY ordered_at,order_id) AS rn,LEAD(ordered_at) OVER (PARTITION BY guest_id ORDER BY ordered_at,order_id) AS next_at FROM orders WHERE guest_id IS NOT NULL),f AS (SELECT guest_id,date_diff('day',CAST(ordered_at AS DATE),CAST(next_at AS DATE)) AS days FROM r WHERE rn=1 AND ordered_at<TIMESTAMP '2026-08-01') SELECT source,COUNT(*) AS guests,ROUND(100*AVG(CASE WHEN days<=30 THEN 1 ELSE 0 END),1) AS back30_pct,MEDIAN(days) AS median_days FROM f JOIN guests USING(guest_id) GROUP BY source ORDER BY source").df()
