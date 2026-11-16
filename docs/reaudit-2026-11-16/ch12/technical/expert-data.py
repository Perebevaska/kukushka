"""Пересчёт из замороженного CSV. Запуск из корня репозитория; только stdlib."""
from collections import Counter, defaultdict
import ast
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import correlation, mean
import tempfile

here = Path(__file__).resolve().parent
data = here / "data-baseline" / "app_orders.csv"
with data.open() as f:
    rows = [(dt.datetime.fromisoformat(r['datetime']), int(r['orders'])) for r in csv.DictReader(f)]
times, values = zip(*rows)
hour = dt.timedelta(hours=1)
y = dict(rows)
assert all(b - a == hour for a,b in zip(times, times[1:]))
gen = Path('tools/gen_data.py')
fn = next(n for n in ast.parse(gen.read_text()).body if getattr(n, 'name', '') == 'gen_chapter12')
with tempfile.TemporaryDirectory() as tmp:
    scope = dict(dt=dt, csv=csv, random=random, OUT=Path(tmp))
    exec(compile(ast.Module([fn], []), str(gen), 'exec'), scope)
    scope['gen_chapter12'](random.Random(12012))
    assert (Path(tmp)/data.name).read_bytes() == data.read_bytes()

july = [t for t in times if t.month == 7]
aug = [t for t in times if t.month == 8]
day = defaultdict(int)
monthly = defaultdict(list)
for t,v in rows:
    day[t.date()] += v
    monthly[t.month].append(v)
def naive(t,k):
    return mean(y[t-hour*168*i] for i in range(1,k+1))
def scores(ticks, forecast):
    errors=[abs(y[t] - forecast(t)) for t in ticks]
    return dict(mae=mean(errors),rmse=math.sqrt(mean(e*e for e in errors)),wape=sum(errors)/sum(y[t] for t in ticks))
def crew(ticks,forecast,cap):
    data=[(y[t],forecast(t)) for t in ticks if 7<=t.hour<=22]
    diff=[max(1,math.ceil(actual/cap))-max(1,math.ceil(p/cap)) for actual,p in data]
    return dict(n=len(data), covered=sum(actual<=p for actual,p in data), short_hours=sum(d>0 for d in diff),
                deficit=sum(max(d,0) for d in diff),extra=sum(max(-d,0) for d in diff))
def raw_folds(ticks,splits,gap):
    step=len(ticks)//(splits+1)
    dates=[]
    for start in range(len(ticks)-step*splits,len(ticks),step):
        dates.append([start-gap,ticks[start-gap-1].isoformat(),ticks[start].isoformat(),ticks[start+step-1].isoformat(),step])
    return dates

proj=[t for t in times[168:] if t<dt.datetime(2026,7,31,20)]
early = [t for t in times if t.month<=7]
cut = [t for t in times[:len(early)] if t>=times[168]]
unknown_last = {}
for t in (july[0],aug[0]):
    when=t-4*hour
    unknown_last[str(when)] = [y[when+j*hour] for j in range(4)]
out = dict(
  rows=len(rows), keys=len(y), interval_hours=1, first=str(times[0]), last=str(times[-1]),
  sha256=hashlib.sha256(data.read_bytes()).hexdigest(), reproduced_generator=True,
  total=sum(values), extrema=[min(values),max(values)], zero_count=values.count(0),
  daytime_zeros=[str(t) for t,v in rows if 8<=t.hour<=20 and v==0],
  monthly_mean={k:mean(v) for k,v in monthly.items()}, june_daily_growth=100*(mean(monthly[6])/mean(monthly[5])-1),
  june_rounded_growth=100*(round(24*mean(monthly[6]),1)/round(24*mean(monthly[5]),1)-1),
  acf={k:correlation(values[k:],values[:-k]) for k in [1,24,168]},
  july_zeros=sum(y[t]==0 for t in july),july_zeros_wape=scores(july,lambda t:naive(t,1))['wape'],
  july_drop_zeros_wape=scores([t for t in july if y[t]],lambda t:naive(t,1))['wape'],
  naive_by_lag={k:scores(july,lambda t:y[t-hour*k]) for k in (1,24,168)},
  weeks_by_month={m:{k:scores(ticks,lambda t:naive(t,k)) for k in (1,2,4,8)} for m,ticks in [('07',july),('08',aug)]},
  august_crew_baselines={cap:{k:crew(aug,lambda t:naive(t,k),cap) for k in (4,8)} for cap in (6,8)},
  cv_dates=raw_folds(proj,3,28), cv_zero_gap=raw_folds(proj,3,0),lesson3b_folds=raw_folds(early,4,0),
  lesson3b_ordered=[len(cut),len(cut)-math.ceil(len(cut)*.2),math.ceil(len(cut)*.2),str(cut[-math.ceil(len(cut)*.2)])],
  unknown_last=unknown_last, warmup_available_weeks=Counter(min(4,j//168) for j in range(168,672)),
  special_date_equal_staff=[(str(t),y[t],naive(t,4)) for t in aug if 7<=t.hour<=22 and y[t]>naive(t,4)
    and max(1,math.ceil(y[t]/6))==max(1,math.ceil(naive(t,4)/6))][:3],
)
(here/'expert-data.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
