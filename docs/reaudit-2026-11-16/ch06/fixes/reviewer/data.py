"""Independent checks of data provenance, calendar boundaries and grouped validation."""
import json
import shutil
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import check_cv

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
DATA=ROOT/"site/data"
sys.path.insert(0,str(ROOT/"tools"))
from gen_ch06_snapshots import write_snapshots
h=pd.read_csv(DATA/"guests_churn.csv")
fresh=pd.read_csv(DATA/"guests_current.csv")
d=pd.read_csv(DATA/"guests_churn_dates.csv")
assert h.guest_id.is_unique and fresh.guest_id.is_unique and d.guest_id.is_unique
assert set(h.guest_id)==set(d.guest_id)
assert set(h.guest_id).isdisjoint(fresh.guest_id)
assert list(fresh.guest_id)==[f"G-{n}" for n in range(30001,32401)]
assert not {"churned","card_blocked"}&set(fresh.columns)
assert d.snapshot_date.eq("2026-10-01").all() and d.target_start.eq(d.snapshot_date).all()
date_fields=["target_end_exclusive","target_available_at","card_blocked_available_at"]
assert d[date_fields].eq("2026-11-30").all().all()
assert fresh.snapshot_date.eq("2026-12-01").all()
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    for trial in ["unmodified","flipped"]:
        if trial=="unmodified":
            shutil.copyfile(DATA/"guests_churn.csv",tmp/"guests_churn.csv")
        else:
            modified=h.copy()
            for col in ["churned","card_blocked"]:
                modified[col]=1-modified[col]
            modified.to_csv(tmp/"guests_churn.csv",index=False,na_rep="")
        write_snapshots(tmp)
        assert (tmp/"guests_current.csv").read_bytes()==(DATA/"guests_current.csv").read_bytes()
deliv=pd.read_csv(DATA/"deliveries.csv",parse_dates=['created'])
orders=deliv.loc[deliv.actual_min.between(1,299)].copy()
labels=orders.actual_min.gt(orders.promised_min)
splits=list(check_cv(5,labels,classifier=True).split(orders,labels))
dates=orders.created.dt.date
spans=[{"fold":i+1,"rows":len(va),"position_span":int(va.max()-va.min()+1),
        "first_test":str(dates.iloc[va].min()),"last_test":str(dates.iloc[va].max()),
        "last_train":str(dates.iloc[tr].max())} for i,(tr,va) in enumerate(splits)]
prob=pd.Series([0,.25,.5,.75,1])
bins=pd.cut(prob,[0,.25,.5,.75,1],include_lowest=True)
bounds={t:str((pd.Timestamp(t)+pd.Timedelta(days=60)).date()) for t in ["2026-10-01","2026-12-01","2027-02-01"]}
assert list(bounds.values())==["2026-11-30","2027-01-30","2027-04-02"]
assert bins.notna().all() and bins.value_counts(sort=False).tolist()==[2,1,1,1]
out=dict(historical=len(h),fresh=len(fresh),overlap=0,stable_after_flipping_both_labels=True,dates=bounds,calibration_counts=bins.value_counts(sort=False).tolist(),stratified_cv=spans,paired_deltas=np.round(np.array([.81,.91,.86,.96,.76])-np.array([.8,.9,.85,.95,.75]),3).tolist())
(HERE/"data.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
