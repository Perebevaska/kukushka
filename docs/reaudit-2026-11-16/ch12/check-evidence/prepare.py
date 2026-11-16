"""Freeze checks evidence with stdlib only. Course source and original data are immutable."""
import json,hashlib,shutil,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
items=[x for x in json.loads(Path('/private/tmp/kuch12round/course.json').read_text()) if x['lesson'].startswith('ch12/') and x['kind']=='task']
(HERE/'before-tasks.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
tasks={x['lesson']+'/'+x['id']:x for x in items};rows=[]
def add(key,desc,code,expected,group='new',**extra):
 l,t=key.rsplit('/',1);rows.append(dict(id=f'C{len(rows)+1:03}',lesson=l,task=t,description=desc,code=code,expected=expected,group=group,code_sha256=hashlib.sha256(code.encode()).hexdigest(),**extra))
def sol(key):return tasks[key]['solution']
def case(key,desc,suffix,expected=False,**extra):add(key,desc,sol(key)+'\n'+suffix,expected,**extra)
# Two literal original programs are the entire chapter12 portion of both the old35 and current69 pack.
for r in map(json.loads,(ROOT/'tools/checks/fixtures/reaudit_20261115.jsonl').read_text().splitlines()):
 if r['lesson'].startswith('ch12/'):
  add(r['lesson']+'/'+r['task'],r['description'],r['code'],r['expected'],'historical-35-and-69',migration='none; WAPE contract unchanged')
# Exact acceptance probe author programs frozen at baseline; suffixes preserve historical bytes.
key='ch12/05-project/split';case(key,'historical probe expression on frozen current author: rotated test mask','import numpy as np\ntest=np.roll(test,744)',group='historical-driver-current-author')
for key in ('ch12/03-features/leak-test','ch12/05-project/staffing'):
 add(key,'historical probe expression on frozen current author: positive',sol(key)+'\n',True,'historical-driver-current-author')
case('ch12/05-project/staffing','historical probe expression on frozen current author: zeros needed','needed = np.zeros_like(needed)',group='historical-driver-current-author')
# All 50 authored implementations plus one plausible wrong declared output per card.
negative={
'load':'s[:] = 0','slice':'morning = day_total','daily':'week_days.index = week_days.index + pd.Timedelta(days=1)',
'p-roll':'','by-hour':'profile.index = list(reversed(profile.index))','growth':'trend28[:] = 0','months':'monthly.index = monthly.index + pd.offsets.MonthBegin(1)',
'zeros':'n_day_zeros += 1','anomalies':'bad_days = []','friday':'all_fridays = not all_fridays','decompose':'trend_growth += 10','toy-trend':'seasonal_week.iloc[1] += 10','p-acf':'',
'diff':'d1[:] = 0; d7[:] = 0','adf':'p_daily = 0.75','hour-season':'season24.index = list(reversed(season24.index))','seasonal-diff':'gain += 1','multiplicative':'amp_growth += 1',
'acf-plot':'ax.patches[50].set_height(1.0)','residual-days':'kinds = ["провал"] * len(kinds)',
'calendar':'df.loc[df.index[10], "y"] += 1','p-lags':'','leak-check':'leaky = ["b"]','make-features':'df.iloc[10, df.columns.get_loc("lag_24")] += 100',
'feature-sets':'rmse["лаги"] += 1','leak-test':'leaking = []','onehot-hours':'n_onehot_cols -= 1','promo-feature':'promo_with += 1',
'noshuffle':'test_start = test_start + pd.Timedelta(hours=1)','check-order':'is_time_split = lambda a,b: a.index[-1] < b.index[0]',
'same-period':'n_tail += 1','folds':'test_starts[0] += pd.Timedelta(hours=1)','tscv':'scores[1] += 1','month-folds':'month_mean["05"] += 1',
'naive':'mae[24] += 1','metrics':'wape = lambda a,b: np.abs(a[a!=0]-b[a!=0]).sum()/a.sum()',
'wape':'zeros += 1','p-horizon':'','bias':'bias = -bias','mean4w':'rmse_k[8] += 1','horizon-gap':'gap_pct += 10',
'leak-horizon':'fooled = not fooled','by-hour-error':'mae_by_hour.index = list(reversed(mae_by_hour.index))',
'split':'df.loc[df.index[10], "y"] += 1','baseline':'base_meets = not base_meets','select':'valid_rmse["linear"] += 1',
'grid':'best_params = {}','final':'pred_test = pred_test[::-1]','staffing':'plans["модель"]["coverage_work"] = plans["модель"]["short"]','quantile':'deficit_q += 1'}
for x in items:
 key=x['lesson']+'/'+x['id'];add(key,'authored baseline',x['solution'],True,'baseline')
 suffix=negative[x['id']]
 if suffix:case(key,'one declared output or relation corrupted',suffix)
 else:
  # Parsons code is a selected permutation of supplied lines; first required import moved after use.
  lines=x['solution'].splitlines(); imp=next(i for i,z in enumerate(lines) if z.startswith('import pandas'))
  line=lines.pop(imp);lines.append(line);add(key,'Parsons import placed after first use','\n'.join(lines),False,'parsons-error',expected_error=True)
# Public-contract false negatives and keyed table equivalences.
for key,vars in {
'ch12/01-resample/daily':['daily','weekly_mean','week_days'],
'ch12/01-resample/by-hour':['profile'],'ch12/01-resample/months':['monthly','growth','per_day','growth_per_day'],
'ch12/01-resample/zeros':['zero_by_hour'],'ch12/01-resample/friday':['dow_mean'],
'ch12/02-decompose/toy-trend':['trend7','seasonal_week'],'ch12/02-decompose/hour-season':['season24'],
'ch12/03-features/calendar':['df'],'ch12/04-forecast/by-hour-error':['mae_by_hour']}.items():
 case(key,'whole output rows reversed with keys preserved','\n'.join(v+' = '+v+'.iloc[::-1]' for v in vars),True,group='keyed-alternative')
# Numeric alternate implementations based on public formulas.
for key,replacements in {
'ch12/04-forecast/metrics': [('np.abs(fact - pred).mean()','sum(abs(a-b) for a,b in zip(fact,pred))/len(fact)'),('np.abs(fact - pred).sum() / fact.sum()','sum(abs(a-b) for a,b in zip(fact,pred))/sum(fact)')],
'ch12/03b-time-split/check-order':[('X_tr.index.max() < X_te.index.min()','all(a < b for a in X_tr.index for b in X_te.index)')],
'ch12/01-resample/growth':[('(t.iloc[-1] / t.iloc[0] - 1) * 100','100 * (t.iloc[-1] - t.iloc[0]) / t.iloc[0]')],
'ch12/05-project/staffing':[('np.ceil(y_test.values / 6)','-np.floor(-y_test.values / 6)'),('np.ceil(p / 6)','-np.floor(-p / 6)')],
}.items():
 code=sol(key)
 for a,b in replacements:assert a in code;code=code.replace(a,b)
 add(key,'equivalent alternate formula',code,True,'alternative-algorithm')
key='ch12/03-features/leak-test'
visible='''import pandas as pd
import numpy as np
def leak_test(features,s,t):
    changed=s.copy()
    changed.loc[t]+=1000
    a,b=features(s).loc[t],features(changed).loc[t]
    same=(a==b)|(a.isna()&b.isna())
    return sorted(same.index[~same])
leaking=leak_test(features,s,pd.Timestamp("2026-07-15 12:00"))
'''
add(key,'literal public single timestamp perturbation',visible,True,'public-contract')
key='ch12/05-project/grid';add(key,'literal public TimeSeriesSplit three folds without gap',sol(key).replace('n_splits=3, gap=28','n_splits=3'),True,'public-contract')
key='ch12/03b-time-split/month-folds';case(key,'values for publicly named May July, dictionary keys as publicly listed','month_rmse = {str(int(k)+1).zfill(2):v for k,v in month_rmse.items()}\nmonth_mean = {str(int(k)+1).zfill(2):v for k,v in month_mean.items()}\nrel_error = {str(int(k)+1).zfill(2):v for k,v in rel_error.items()}',True,group='ambiguous-public-contract')
# Missing outputs and non-first-row function validation.
key='ch12/03-features/make-features'
code=sol(key).replace('return df.dropna()','df = df.dropna()\n    df.loc[df.index[1:], "lag_1"] = s.reindex(df.index[1:]).values\n    return df')
add(key,'function leaks current target in lag1 after first row',code,False)
case(key,'function drops all rows except first after correct first_ts','original_make_features = make_features\ndef make_features(s):\n    return original_make_features(s).iloc[:1]',False)
case(key,'first_ts correct but requested df missing','del df',False)
case('ch12/05-project/split','requested df missing but X y masks correct','del df',False)
# All-shapes collection count: zip must not silently accept shorter outputs.
case('ch12/01-resample/months','growth vectors empty but totals summaries correct','growth=growth.iloc[:0]\ngrowth_per_day=growth_per_day.iloc[:0]\nper_day=per_day.iloc[:0]',False)
# Source/date availability and semantic units are separate oracles, not extra hidden requirements.
key='ch12/05-project/staffing'
case(key,'one worker omitted on zero demand at any hour','needed = np.ceil(y_test.values/6)',False)
case(key,'coverage wrongly uses sufficient rounded staffing','\nfor name,p in [("модель",pred_test),("ориентир",X.loc[test,"mean4w"].values)]:\n    plans[name]["coverage_work"]=round(float((np.maximum(1,np.ceil(p/6))[open_hours]>=needed[open_hours]).mean()),3)',False)
case(key,'short measures forecast underdemand rather than shortage','\nfor name,p in [("модель",pred_test),("ориентир",X.loc[test,"mean4w"].values)]:\n    plans[name]["short"]=round(float((p[open_hours]<y_test.values[open_hours]).mean()),3)',False)
case(key,'deficit sums missing orders instead of missing barista hours','plans["модель"]["deficit"]=float(np.clip(y_test.values-pred_test,0,None)[open_hours].sum())',False)
# Model future availability acceptance; main grading unchanged, appended assertion is a technical oracle.
key='ch12/05-project/final'
oracle='''
_raw=pd.read_csv("app_orders.csv")
_mask=(_raw.datetime>="2026-07-31 20:00")&(_raw.datetime<"2026-08-01")
_raw.loc[_mask,"orders"]+=1000
_z=pd.Series(_raw.orders.values,index=pd.to_datetime(_raw.datetime))
_dx=make(_z);_xx=_dx.drop(columns="y");_yy=_dx.y
_fit=(_dx.index<"2026-07-31 20:00")&_yy.notna()
_pp=np.clip(HistGradientBoostingRegressor(random_state=0,**best_params).fit(_xx[_fit],_yy[_fit]).predict(_xx[_dx.index>="2026-08-01"]),0,None)
assert np.allclose(pred_test[:24],_pp[:24]), "last unavailable four labels changed issued forecast"
_hidden=s.copy();_hidden.loc[_hidden.index>="2026-07-31 20:00"]=np.nan
_future=make(_hidden).loc["2026-08-01":"2026-08-01 23:00"]
assert len(_future)==24 and _future.y.isna().all() and _future.drop(columns="y").notna().all().all()
'''
add(key,'literal historical unavailable labels and24 unknown future targets',sol(key),True,'historical-acceptance-equivalent-driver',oracle=oracle,migration='driver isolation only; historical assertions unchanged semantically, original source SHA retained')
# Frozen pure transfer programs may be run with no course check; no claim that capacity/cost are task inputs.
transfer='''import math
rows=[(7,11),(6,7),(0,0),(18,7)]
for capacity in (4,6,8):
    counts=[(max(1,math.ceil(p/capacity)),max(1,math.ceil(y/capacity))) for p,y in rows]
    deficit=sum(max(n-p,0) for p,n in counts); extra=sum(max(p-n,0) for p,n in counts)
    for cost in (300,1200):
        print(capacity,cost,deficit,extra,cost*deficit+300*extra)
assert max(1,math.ceil(7/6))==max(1,math.ceil(11/6))==2
assert max(1,math.ceil(6/6))<max(1,math.ceil(7/6))
assert max(1,math.ceil(0/6))==1
'''
(HERE/'transfer_staffing.py').write_text(transfer)
(HERE/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(HERE/'expected-before-execution.json').write_text(json.dumps({r['id']:{'expected':r['expected'],'code_sha256':r['code_sha256'],'group':r['group']} for r in rows},ensure_ascii=False,indent=2)+'\n')
# Preserve evidence hashes including full historical files; never call regenerated code literal old code.
paths=['content/ch12','site/assets/harness.py','site/assets/vendor/pyodide','tools/checks/ch12_acceptance.py','docs/course-improvements/reaudit/expert_probes.py','tools/checks/fixtures/reaudit_20261115.jsonl','tools/checks/reaudit_technical.py','docs/course-improvements/reaudit/fixes/technical-results.jsonl']
hashes={}
for p in paths:
 p=ROOT/p
 for f in p.rglob('*') if p.is_dir() else [p]:
  if f.is_file():hashes[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
(HERE/'before-source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
(HERE/'data-baseline').mkdir(exist_ok=True)
shutil.copy(ROOT/'site/data/app_orders.csv',HERE/'data-baseline/app_orders.csv')
freeze={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [HERE/'programs.jsonl',HERE/'expected-before-execution.json',HERE/'before-tasks.json',HERE/'visible-contracts.json',HERE/'pre-check-promises.md',HERE/'transfer_staffing.py',HERE/'data-baseline/app_orders.csv']}
(HERE/'frozen.sha256').write_text(json.dumps(freeze,indent=2)+'\n')
print('Frozen',len(rows),'programs; tasks',len(set(r['lesson']+'/'+r['task'] for r in rows)));print(json.dumps(freeze))
