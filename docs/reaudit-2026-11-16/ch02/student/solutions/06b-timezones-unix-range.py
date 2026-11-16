import pandas as pd
ev=pd.read_csv("app_events.csv")
utc=pd.to_datetime(ev["ts"],unit="ms")
first_utc=utc.min()
last_utc=utc.max()
