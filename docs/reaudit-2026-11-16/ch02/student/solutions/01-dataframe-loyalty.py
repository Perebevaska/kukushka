import pandas as pd
df=pd.read_csv("orders_3m.csv")
loyalty_share=round(df["client_id"].notna().mean()*100,1)
orders_per_client=round(df["client_id"].count()/df["client_id"].nunique(),1)
