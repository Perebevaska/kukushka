import pandas as pd
ev=pd.read_csv("app_events.csv")
offset={"PRM":5,"TMN":5,"UFA":5,"KZN":3}
ev["local"]=pd.to_datetime(ev["ts"],unit="ms")+pd.to_timedelta(ev["shop_id"].str[:3].map(offset),unit="h")
o=ev[ev["event"]=="заказ"]
morning_share=round((o["local"].dt.hour<10).mean()*100,1)
