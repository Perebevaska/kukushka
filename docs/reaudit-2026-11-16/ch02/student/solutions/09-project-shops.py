import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
by_shop=full.groupby("shop_id").agg(city=("city","first"),revenue=("amount","sum"),seats=("seats","first"))
by_shop["per_seat"]=(by_shop["revenue"]/by_shop["seats"]).round()
by_shop=by_shop.sort_values("per_seat",ascending=False)
leader=by_shop["per_seat"].idxmax()
leader_by_revenue=by_shop["revenue"].idxmax()

