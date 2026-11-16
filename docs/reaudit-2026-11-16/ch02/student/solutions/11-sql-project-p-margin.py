import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
margin=duckdb.sql('SELECT category,SUM(i.qty*i.price) AS revenue,SUM(i.qty*(i.price-m.cost)) AS margin,ROUND(100*SUM(i.qty*(i.price-m.cost))/SUM(i.qty*i.price),1) AS margin_pct FROM items i JOIN menu m USING(item_id) GROUP BY category ORDER BY margin_pct DESC').df()
