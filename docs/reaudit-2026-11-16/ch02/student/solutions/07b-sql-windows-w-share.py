import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
by_shop = duckdb.sql("SELECT shop_id, SUM(amount) AS revenue FROM df GROUP BY shop_id").df()
shares = duckdb.sql("SELECT shop_id, revenue, ROUND(100 * revenue / SUM(revenue) OVER (), 1) AS pct FROM by_shop ORDER BY pct DESC").df()
print(shares)
