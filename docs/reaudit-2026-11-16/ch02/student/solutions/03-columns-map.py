import pandas as pd
df=pd.read_csv("orders_3m.csv")
df["channel_en"]=df["channel"].map({"зал":"dine-in","с собой":"takeaway","доставка":"delivery"})
n_takeaway=(df["channel_en"]=="takeaway").sum()
