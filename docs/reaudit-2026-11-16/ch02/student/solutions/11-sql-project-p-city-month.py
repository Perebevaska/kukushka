import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
city_month=duckdb.sql("SELECT s.city,date_trunc('month',o.ordered_at) AS month,COUNT(DISTINCT o.order_id) AS orders,SUM(i.qty*i.price) AS revenue FROM orders o JOIN items i USING(order_id) JOIN shops s USING(shop_id) GROUP BY city,month ORDER BY city,month").df()
aug=city_month[city_month["month"].dt.month==8]
best_city=aug.loc[aug["revenue"].idxmax(),"city"]
