import sqlite3
import pandas as pd
con=sqlite3.connect("zerno.db")
orders_cols=pd.read_sql_query("SELECT * FROM orders LIMIT 0",con).columns.tolist()
n_items=pd.read_sql_query("SELECT COUNT(*) AS n FROM order_items",con)["n"].iloc[0]
con.close()
