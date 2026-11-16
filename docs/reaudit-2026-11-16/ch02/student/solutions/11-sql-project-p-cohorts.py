import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
ret=duckdb.sql("WITH f AS (SELECT guest_id,date_trunc('month',MIN(ordered_at)) AS cohort FROM orders WHERE guest_id IS NOT NULL GROUP BY guest_id),a AS (SELECT DISTINCT o.guest_id,cohort,date_diff('month',cohort,date_trunc('month',ordered_at)) AS k FROM orders o JOIN f USING(guest_id)),c AS (SELECT cohort,k,COUNT(*) AS guests FROM a GROUP BY cohort,k) SELECT cohort,k,guests,ROUND(100*guests/FIRST_VALUE(guests) OVER (PARTITION BY cohort ORDER BY k),1) AS pct FROM c ORDER BY cohort,k").df()
march_m1=ret.loc[(ret["cohort"].dt.month==3) & (ret["k"]==1),"pct"].iloc[0]
