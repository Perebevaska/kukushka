import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
checks=duckdb.sql("WITH totals AS (SELECT order_id,SUM(qty*price) AS total FROM items GROUP BY order_id) SELECT o.channel,CASE WHEN o.guest_id IS NULL THEN 'без карты' ELSE 'с картой' END AS card,COUNT(*) AS orders,ROUND(AVG(total),1) AS avg_check FROM orders o JOIN totals USING(order_id) GROUP BY channel,card ORDER BY channel,card").df()
a=duckdb.sql("WITH t AS (SELECT order_id,SUM(qty*price) AS total FROM items GROUP BY order_id) SELECT guest_id IS NOT NULL AS card,AVG(total) AS avg_check FROM orders JOIN t USING(order_id) GROUP BY card").df().set_index("card")["avg_check"]
diff_pct=round((a.loc[True]/a.loc[False]-1)*100,1)
