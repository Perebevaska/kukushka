import pandas as pd
df=pd.read_csv("orders_3m.csv")
def shop_kpi(df,shop_id):
    t=df.loc[df["shop_id"]==shop_id,"amount"]
    return {"orders":len(t),"revenue":t.sum(),"avg_check":round(t.mean(),1)}
kpi=pd.DataFrame({sid:shop_kpi(df,sid) for sid in df["shop_id"].unique()}).T
kpi.index.name="shop_id"
best_check=kpi["avg_check"].idxmax()
