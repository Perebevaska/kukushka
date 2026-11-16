import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
ret_src=duckdb.sql("WITH f AS (SELECT guest_id,date_trunc('month',MIN(ordered_at)) AS cohort FROM orders WHERE guest_id IS NOT NULL GROUP BY guest_id),a AS (SELECT DISTINCT o.guest_id,date_diff('month',cohort,date_trunc('month',ordered_at)) AS k FROM orders o JOIN f USING(guest_id) WHERE cohort<DATE '2026-07-01'),g AS (SELECT f.guest_id,source,MAX(CASE WHEN a.k=1 THEN 1 ELSE 0 END) AS m1,MAX(CASE WHEN a.k=2 THEN 1 ELSE 0 END) AS m2 FROM f JOIN guests USING(guest_id) LEFT JOIN a USING(guest_id) WHERE cohort<DATE '2026-07-01' GROUP BY f.guest_id,source) SELECT source,COUNT(*) AS cohort_size,ROUND(100*AVG(m1),1) AS m1,ROUND(100*AVG(m2),1) AS m2 FROM g GROUP BY source ORDER BY source").df()
s=ret_src.set_index("source")["m2"]
m2_gap=round(s.loc["приложение"]-s.loc["касса"],1)
