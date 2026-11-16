import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
nov=full[full["datetime"].dt.month==11]
october=full[full["datetime"].dt.month==10]
new_drinks=set(nov["drink"])-set(full.loc[full["datetime"].dt.month<11,"drink"])
seasonal_share=round(nov.loc[nov["drink"].isin(new_drinks),"amount"].sum()/nov["amount"].sum()*100,1)
check_change=round((nov["amount"].mean()/october["amount"].mean()-1)*100,1)

