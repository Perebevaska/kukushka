import sqlite3
import pandas as pd
cat="еда"
con=sqlite3.connect("zerno.db")
food=pd.read_sql_query("SELECT name,price FROM menu WHERE category=? ORDER BY price DESC",con,params=(cat,))
con.close()
