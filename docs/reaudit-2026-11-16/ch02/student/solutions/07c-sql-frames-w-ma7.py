import duckdb
import pandas as pd
ds=pd.read_csv("daily_sales.csv",parse_dates=["date"])
dec=duckdb.sql("WITH w AS (SELECT date,revenue_k,ROUND(AVG(revenue_k) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),1) AS ma7 FROM ds WHERE shop_id='TMN-1') SELECT * FROM w WHERE date>=DATE '2025-12-01' AND date<DATE '2026-01-01' ORDER BY date").df()
peak_date=dec.loc[dec["ma7"].idxmax(),"date"]
