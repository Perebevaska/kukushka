"""Independent stdlib recalculation on submitted CSV (does not retrain model)."""
from pathlib import Path
import csv,json,collections
D=Path(__file__).resolve().parent;S=D/'student';freeze=json.loads((S/'project-freeze.json').read_text())
def load(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def minute(t):h,m=map(int,t.split(':'));return h*60+m
def measure(rr,k):
 keys={(r['time'],int(r['slot'])) for r in rr};assert len(keys)==len(rr)==732
 hits=collections.defaultdict(list);episodes=[];signals=[]
 for slot in range(12):
  items=sorted([r for r in rr if int(r['slot'])==slot],key=lambda r:minute(r['time']));run=0;prev=None;open_episode=None
  for r in items:
   t=minute(r['time']);truth=int(r['true'])==0;pred=int(r['pred'])==0
   if not truth or prev is None or t-prev!=15:open_episode=None
   if truth and open_episode is None:open_episode=len(episodes);episodes.append({'slot':slot,'start':t,'times':[]})
   if truth:episodes[open_episode]['times'].append(t)
   if pred:run=run+1 if prev is not None and t-prev==15 else 1
   else:run=0
   if run==k:
    signals.append((t,slot));
    if truth:hits[open_episode].append(t)
   prev=t
 false=sum(not any(e['slot']==s and t in e['times'] for e in episodes) for t,s in signals)
 missed=len(episodes)-len(hits);repeated=sum(len(v)-1 for v in hits.values());delay=sum(min(ts)-episodes[i]['start'] for i,ts in hits.items())
 price=freeze['prices'];return {'n_alerts':len(signals),'false':false,'missed':missed,'repeated':repeated,'delay_total':delay,'delay_minutes':delay/len(hits) if hits else None,'n_episodes':len(episodes),'cost':false*price['false']+missed*price['missed']+repeated*price['repeated']+delay*price['delay_minute']}
out={'scope':'independent stdlib events arithmetic on own submitted CSV; no model retraining or NPZ prediction verification','day1':{str(k):measure(load(S/'project-day1.csv'),k) for k in [1,2,3]},'day2':measure(load(S/'project-day2.csv'),freeze['chosen_k'])}
assert out['day1']==freeze['policy_table'];expected=json.loads((S/'project-day2-metrics.json').read_text());assert all(expected[k]==v for k,v in out['day2'].items())
(D/'coordination-events.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
