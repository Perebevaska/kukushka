import pandas as pd
guests=pd.read_csv("zdb_guests.csv")
orders=pd.read_csv("zdb_orders.csv")
guests["ordered"]=guests["guest_id"].isin(orders["guest_id"])
conv_all=round(guests["ordered"].mean(),3)
conv=guests.groupby("source")["ordered"].mean().round(3).to_dict()
lost_app=((guests["source"]=="приложение") & ~guests["ordered"]).sum()
