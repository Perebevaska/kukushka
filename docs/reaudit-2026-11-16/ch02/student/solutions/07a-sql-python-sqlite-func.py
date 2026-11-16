import sqlite3
import pandas as pd
def city_revenue(con, city, month):
    q="SELECT COALESCE(SUM(i.qty*i.price),0) AS revenue FROM orders o JOIN order_items i USING(order_id) JOIN shops s USING(shop_id) WHERE s.city=? AND substr(o.ordered_at,1,7)=?"
    return int(pd.read_sql_query(q,con,params=(city,month))["revenue"].iloc[0])
con=sqlite3.connect("zerno.db")
print(city_revenue(con,"Казань","2026-06"))
con.close()
