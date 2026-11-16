import pandas as pd
df=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])
shops=pd.read_csv("shops.csv")
menu=pd.read_csv("menu.csv")
full=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")
monthly=full.groupby(full["datetime"].dt.to_period("M")).agg(revenue=("amount","sum"),orders=("order_id","size"),avg_check=("amount","mean"),clients=("client_id","nunique"))
monthly["avg_check"]=monthly["avg_check"].round(1)
nov_vs_oct=round((monthly["revenue"].iloc[-1]/monthly["revenue"].iloc[-2]-1)*100,1)
by_shop=full.groupby("shop_id").agg(city=("city","first"),revenue=("amount","sum"),seats=("seats","first"))
by_shop["per_seat"]=(by_shop["revenue"]/by_shop["seats"]).round()
by_shop=by_shop.sort_values("per_seat",ascending=False)
leader=by_shop["per_seat"].idxmax()
leader_by_revenue=by_shop["revenue"].idxmax()
card=full.loc[full["client_id"].notna(),"amount"].mean()
no_card=full.loc[full["client_id"].isna(),"amount"].mean()
avg_card=round(card,1)
avg_no_card=round(no_card,1)
diff_pct=round((card/no_card-1)*100,1)
load=pd.pivot_table(full,index=full["datetime"].dt.weekday,columns=full["datetime"].dt.hour,values="order_id",aggfunc="count",fill_value=0)
peak=load.stack().idxmax()
SIZE_K={"S":1.,"M":1.25,"L":1.5}
full["cost"]=full["cost_s"]*full["size"].map(SIZE_K)*full["qty"]
g=full.groupby("category").agg(revenue=("amount","sum"),cost=("cost","sum"))
margin_raw=(g["revenue"]-g["cost"])/g["revenue"]*100
margin=margin_raw.round(1)
def verdict(ok):
    return "подтвердилась" if ok else "не подтвердилась"
most_seats=set(by_shop.index[by_shop["seats"]==by_shop["seats"].max()])
most_revenue=set(by_shop.index[by_shop["revenue"]==by_shop["revenue"].max()])
verdicts={"H1":verdict((monthly["revenue"].pct_change().dropna()>0).all()),"H2":verdict(bool(most_seats & most_revenue)),"H4":verdict((card/no_card-1)*100>=5),"H5":verdict(peak[0] in [5,6] and peak[1]<12),"H6":verdict(margin_raw["не кофе"]-margin_raw["кофе"]>=3)}

