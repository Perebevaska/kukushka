import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
sizes={name:duckdb.sql(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in names}
empty_orders=duckdb.sql("SELECT COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM items i WHERE i.order_id=o.order_id)").fetchone()[0]
