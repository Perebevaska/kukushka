import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
monthly=full.groupby(full["datetime"].dt.to_period("M")).agg(revenue=("amount","sum"),orders=("order_id","size"),avg_check=("amount","mean"),clients=("client_id","nunique"))
monthly["avg_check"]=monthly["avg_check"].round(1)
nov_vs_oct=round((monthly["revenue"].iloc[-1]/monthly["revenue"].iloc[-2]-1)*100,1)

