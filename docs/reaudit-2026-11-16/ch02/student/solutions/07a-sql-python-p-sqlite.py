import sqlite3
import pandas as pd
con = sqlite3.connect("zerno.db")
query = "SELECT COUNT(*) AS n FROM orders WHERE substr(ordered_at, 1, 7) = ?"
t = pd.read_sql_query(query, con, params=("2026-04",))
con.close()
print(t["n"].iloc[0])
