import pandas as pd
ev=pd.read_csv("app_events.csv")
perm=ev[ev["shop_id"].str.startswith("PRM")].copy()
perm["utc"]=pd.to_datetime(perm["ts"],unit="ms")
perm["local"]=perm["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")
perm_peak=perm["local"].dt.hour.value_counts().idxmax()
