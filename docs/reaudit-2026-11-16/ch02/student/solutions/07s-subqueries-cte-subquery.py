import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
shops=pd.read_csv("shops.csv")
big_kzn=duckdb.sql("SELECT COUNT(*) FROM df WHERE shop_id IN (SELECT shop_id FROM shops WHERE city='Казань') AND amount>(SELECT AVG(amount) FROM df)").fetchone()[0]
