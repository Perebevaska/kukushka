import pandas as pd
df=pd.read_csv("orders_3m.csv")
avg=df.groupby("shop_id")["amount"].mean()
with pd.option_context("display.float_format","{:.1f}".format):
    print(avg)
