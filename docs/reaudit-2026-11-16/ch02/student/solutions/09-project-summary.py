import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
def summary(full):
    monthly=full.groupby(full["datetime"].dt.to_period("M"))["amount"].sum()
    return {"revenue":full["amount"].sum(),"orders":len(full),"avg_check":round(full["amount"].mean(),1),"best_city":full.groupby("city")["amount"].sum().idxmax(),"top_drink":full["drink"].value_counts().idxmax(),"growth_pct":round((monthly.iloc[-1]/monthly.iloc[-2]-1)*100,1)}
summary(full)
