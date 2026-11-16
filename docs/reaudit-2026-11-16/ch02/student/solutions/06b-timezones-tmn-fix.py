import pandas as pd
ev=pd.read_csv("app_events.csv")
tmn=ev[ev["shop_id"].str.startswith("TMN")].copy()
tmn["utc"]=pd.to_datetime(tmn["ts"],unit="ms")
tmn["local"]=tmn["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")
tmn_morning=round((tmn["local"].dt.hour<10).mean()*100,1)
print(tmn_morning)
