import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
card=full.loc[full["client_id"].notna(),"amount"].mean()
no_card=full.loc[full["client_id"].isna(),"amount"].mean()
avg_card=round(card,1)
avg_no_card=round(no_card,1)
diff_pct=round((card/no_card-1)*100,1)

