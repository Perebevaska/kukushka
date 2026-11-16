import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
load=pd.pivot_table(full,index=full["datetime"].dt.weekday,columns=full["datetime"].dt.hour,values="order_id",aggfunc="count",fill_value=0)
peak=load.stack().idxmax()

