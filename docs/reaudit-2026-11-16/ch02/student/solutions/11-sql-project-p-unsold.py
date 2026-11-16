import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
unsold=[r[0] for r in duckdb.sql("SELECT name FROM menu m WHERE NOT EXISTS (SELECT 1 FROM items i WHERE i.item_id=m.item_id) ORDER BY name").fetchall()]
lemonade_first=duckdb.sql("SELECT CAST(MIN(ordered_at) AS DATE) FROM orders JOIN items USING(order_id) JOIN menu USING(item_id) WHERE name='Лимонад'").fetchone()[0]
