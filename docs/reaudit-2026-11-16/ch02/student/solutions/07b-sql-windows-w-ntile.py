import duckdb
import pandas as pd
df=pd.read_csv("orders_3m.csv")
quart=duckdb.sql("WITH g AS (SELECT client_id,SUM(amount) AS spent FROM df WHERE client_id IS NOT NULL GROUP BY client_id),q AS (SELECT *,NTILE(4) OVER (ORDER BY spent DESC,client_id) AS quartile FROM g) SELECT quartile,COUNT(*) AS guests,SUM(spent) AS revenue,ROUND(100*SUM(spent)/SUM(SUM(spent)) OVER (),1) AS pct FROM q GROUP BY quartile ORDER BY quartile").df()
top_pct=quart.loc[quart["quartile"]==1,"pct"].iloc[0]
