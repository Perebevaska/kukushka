import duckdb
query = "SELECT COUNT(*) FROM 'orders_3m.csv' WHERE size = 'L'"
n = duckdb.sql(query).fetchone()[0]
print(n)
