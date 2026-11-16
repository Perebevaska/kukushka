import pandas as pd
import math
def delivery_report(raw):
    ok=raw[raw.actual_min.between(1,299)].copy()
    if ok.empty:
        return dict(late_pct=None,worst_courier=None,worst_shop=None,peak_hours=[],fair_promise=None)
    ok["late"]=ok.actual_min>ok.promised_min
    ok["hour"]=ok.created.dt.hour
    g=ok.groupby("hour").late.agg(["mean","size"])
    s=ok[(ok.courier=="пеший")&(ok.promised_min==30)].actual_min
    promise=None if s.empty else math.ceil(s.quantile(.8)/5)*5
    return dict(late_pct=round(ok.late.mean()*100,1),worst_courier=ok.groupby("courier").late.mean().sort_index().idxmax(),worst_shop=ok.groupby("shop_id").late.mean().sort_index().idxmax(),peak_hours=g[(g["size"]>=50)&(g["mean"]>.25)].index.tolist(),fair_promise=promise)
raw=pd.read_csv("deliveries.csv",parse_dates=["created"])
delivery_report(raw)
