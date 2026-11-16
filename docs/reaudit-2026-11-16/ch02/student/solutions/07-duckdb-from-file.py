import duckdb
avg_check_delivery=duckdb.sql("SELECT ROUND(AVG(amount),2) FROM 'orders_3m.csv' WHERE channel='доставка'").fetchone()[0]
