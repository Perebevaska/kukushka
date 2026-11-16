import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
top2=duckdb.sql("SELECT shop_id,drink,COUNT(*) AS n,DENSE_RANK() OVER (PARTITION BY shop_id ORDER BY COUNT(*) DESC) AS place FROM df GROUP BY shop_id,drink QUALIFY place<=2 ORDER BY shop_id,place,drink").df()
