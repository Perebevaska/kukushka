import pandas as pd
df=pd.read_csv("orders_3m.csv")
pv=pd.pivot_table(df,index="shop_id",columns="channel",values="amount",aggfunc="sum")
share=pv.div(pv.sum(axis=1),axis=0)
low_delivery=share["доставка"].idxmin()
low_share=round(share.loc[low_delivery,"доставка"],3)
