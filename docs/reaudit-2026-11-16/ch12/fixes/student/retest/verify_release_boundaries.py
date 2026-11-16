from pathlib import Path
from datetime import datetime,timedelta
import csv,json
D=Path(__file__).parent
cutoff=datetime(2026,7,31,19)
release=datetime(2026,7,31,20)
start=datetime(2026,8,1)
end=start+timedelta(hours=23)
known={datetime.fromisoformat(r['datetime']):int(r['orders']) for r in csv.DictReader((D/'data/app_orders.csv').open()) if datetime.fromisoformat(r['datetime'])<=cutoff}
rows=[]
t=min(known)
while t<=end:
 rows.append({'datetime':t.isoformat(sep=' '),'y':known.get(t,''),'future_target':int(start<=t<=end)})
 t+=timedelta(hours=1)
future=[r for r in rows if r['future_target']]
unknown=[r for r in rows if r['y']=='']
assert len(future)==24 and all(r['y']=='' for r in future)
assert len(unknown)==28 and unknown[0]['datetime']=='2026-07-31 20:00:00'
assert all(start+timedelta(hours=h)-timedelta(hours=k)<=cutoff for h in range(24) for k in [28,48,168])
with (D/'own-release-grid-y-unknown.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['datetime','y','future_target']);writer.writeheader();writer.writerows(rows)
# Независимый перенос момента выпуска18:00
release18=datetime(2026,7,31,18)
last18=release18-timedelta(hours=1)
horizons={}
for hour in [0,18,23]:
 target=datetime(2026,8,1,hour)
 lag=int((target-last18).total_seconds()/3600)
 assert target-timedelta(hours=lag)==last18
 horizons[str(hour)]={'target':str(target),'last_fact':str(last18),'minimum_lag':lag}
assert horizons['0']['minimum_lag']==7 and horizons['18']['minimum_lag']==25 and horizons['23']['minimum_lag']==30
(D/'own-release-boundary-results.json').write_text(json.dumps({'release':str(release),'last_fact':str(cutoff),'future_rows':len(future),'unknown_grid_rows':len(unknown),'current_release_hour_unknown':unknown[0]['datetime'],'release18':horizons},ensure_ascii=False,indent=2))
print('24 future y unknown;28 unknown positions including release hour; release18 horizons7/25/30 verified')
