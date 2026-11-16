import pandas as pd
ev=pd.read_csv("app_events.csv")
kzn = ev[ev["shop_id"].str.startswith("KZN")].copy()
kzn["utc"] = pd.to_datetime(kzn["ts"], unit="ms")
kzn["local"] = kzn["utc"].dt.tz_localize("UTC").dt.tz_convert("+03:00")
print(kzn["local"].dt.hour.value_counts().idxmax())
