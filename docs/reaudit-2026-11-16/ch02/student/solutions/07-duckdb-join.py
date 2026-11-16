import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
by_city=duckdb.sql("SELECT city,SUM(amount) AS revenue FROM df JOIN shops USING(shop_id) GROUP BY city ORDER BY revenue DESC").df()
