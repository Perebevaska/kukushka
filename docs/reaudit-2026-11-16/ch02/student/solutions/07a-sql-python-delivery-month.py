import sqlite3
import pandas as pd
month="2026-08"
con=sqlite3.connect("zerno.db")
t=pd.read_sql_query("SELECT channel FROM orders WHERE substr(ordered_at,1,7)=?",con,params=(month,))
share=round((t["channel"]=="доставка").mean()*100,1)
con.close()
