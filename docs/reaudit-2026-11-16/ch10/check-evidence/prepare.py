"""Freeze literal submissions and expectations, without executing course code."""
import json,hashlib,shutil,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
all_items=json.loads(Path('/private/tmp/kuch10round/course.json').read_text())
items={t['lesson']+'/'+t['id']:t for t in all_items if t['lesson'].startswith('ch10/')}
rows=[]
def add(lesson,task,description,code,expected,group='new',basis=None,**extra):
 row=dict(id=f'C{len(rows)+1:02}',lesson=lesson,task=task,description=description,code=code,expected=expected,group=group,basis=basis or description,code_sha256=hashlib.sha256(code.encode()).hexdigest(),**extra)
 rows.append(row)
def sol(lesson,task):return items[lesson+'/'+task]['solution']
original=[json.loads(s) for s in (ROOT/'tools/checks/fixtures/reaudit_20261115.jsonl').read_text().splitlines() if s]
original=[r for r in original if r['lesson'].startswith('ch10/')]
for r in original:
 add(r['lesson'],r['task'],r['description'],r['code'],False,'historical-original',basis='Current visible contract explicitly requires supplied timed_fit/timed_predict; original manual timer program is a contract migration, not a false reject.',expected_original=r['expected'])
for r in original:
 code=r['code'];task=r['task'];train,target,test=('X[tr]','y[tr]','X[~tr]') if task=='compare' else ('X_tr','y_tr','X_te')
 code=code.replace('    t0 = time.perf_counter()\n','').replace(f'    model.fit({train}, {target})',f'    fit_s = timed_fit(name, model, {train}, {target})').replace('    fit_s = time.perf_counter() - t0\n','').replace(f'    pred = model.predict({test})',f'    pred, predict_ms = timed_predict(name, model, {test})').replace('    predict_ms = (time.perf_counter() - t0) * 1000\n','')
 add(r['lesson'],task,r['description'],code,r['expected'],'historical-migration',basis='Mechanical migration to the explicitly required timers, preserving original semantic correctness or error.')
for lesson,task in [('ch10/05-project','compare'),('ch10/06-libraries','speed-table')]:
 s=sol(lesson,task)
 for desc,code,expect in [
 ('seconds mistakenly saved as milliseconds',s+'\ntable["predict_ms"] /= 1000',False),
 ('measured interval shifted by constant',s+'\ntable["fit_s"] += .01',False),
 ('random intervals replace measurements',s+'\ntable["fit_s"] = np.random.default_rng(17).uniform(.1, .3, len(table))',False)]:add(lesson,task,desc,code,expect,'historical-additional',basis='Visible task requires original returned timing intervals and seconds/milliseconds units.')
 for slow in (False,True):
  ticks=[]
  for i in range(5 if task=='compare' else 3):ticks.extend([i*1000.,i*1000.+(61+i if slow else .11+i*.01),i*1000.+100,i*1000.+100.002+i*.001])
  prefix='_probe_ticks=iter('+repr(ticks)+')\n_measurement_clock=lambda: next(_probe_ticks)\n'
  add(lesson,task,f'deterministic registered intervals slow={slow}',prefix+s,True,'historical-additional',basis='Test-only controlled clock preserves timer calls and tests formulas on another valid measurement outcome; this is not a genuine wall-clock benchmark.',clock_mode='historical-instrumentation')
 add(lesson,task,'own functions delegate to supplied timer','own_fit = lambda *args: timed_fit(*args)\nown_predict = lambda *args: timed_predict(*args)\n'+s.replace('timed_fit(','own_fit(').replace('timed_predict(','own_predict('),True,'historical-additional',basis='Delegation still performs the supplied timer calls and preserves returned values.')
# Independent new probes; all expectations are stated from visible task text.
l='ch10/05-project';s=sol(l,'compare')
add(l,'compare','author program, real timer',s,True,basis='All five procedures, April selection and July report, exact required timer values.')
add(l,'compare','RMSE saved in rubles instead of thousand rubles',s+'\ntable["rmse"] *= 1000',False,basis='Visible task explicitly requires thousand-ruble RMSE.')
add(l,'compare','MSE saved as RMSE',s+'\ntable["rmse"] **= 2',False,basis='RMSE is the square root of MSE, same target units.')
add(l,'compare','MAE copied from RMSE',s+'\ntable["mae"] = table["rmse"]',False,basis='Visible task asks for two distinct metrics, not a duplicated column.')
add(l,'compare','rounded April metric before selection',s.replace('validation_scores[name] = float(np.sqrt(mean_squared_error(y[validation],vp)))','validation_scores[name] = round(float(np.sqrt(mean_squared_error(y[validation],vp))), 2)'),False,basis='Visible task says val_rmse full precision, round only for printing.')
l='ch10/06-libraries';s=sol(l,'speed-table')
add(l,'speed-table','author program, real timer',s,True,basis='Required three models, metrics and winner derived from measured columns.')
ticks=[]
for i,fit in enumerate([.3,.2,.1]):ticks.extend([i*1000.,i*1000.+fit,i*1000.+100,i*1000.+100.002])
add(l,'speed-table','controlled reverse speed order',s,True,basis='Visible condition chooses fastest from own table; no model name is inherently fastest. Clock is injected by runner, outside submission.',clock_ticks=ticks)
add(l,'speed-table','pick slowest fit as fastest',s+'\nfastest_fit = table["fit_s"].idxmax()',False,basis='fastest_fit must minimize fit_s.')
l='ch10/01-gradient';s=sol(l,'history')
add(l,'history','same learning curve drawn via numpy steps',s.replace('ax.plot(range(1, 41), history)','ax.plot(np.arange(1, 41), np.array(history))'),True,basis='Same 40 MSE observations and step numbers in another equivalent representation.')
add(l,'history','plot one incorrect MSE while preserving history',s.replace('ax.plot(range(1, 41), history)','shown = list(history)\nshown[10] += 100\nax.plot(range(1, 41), shown)'),False,basis='Task asks to draw history itself; the eleventh plotted MSE must equal history[10].')
l='ch10/02-gd-many';s=sol(l,'decay')
add(l,'decay','empty last-five lists after valid computation',s+'\nlast5_const = []\nlast5_decay = []',False,basis='Task explicitly requires lists containing MSE of the last five epochs, not empty lists.')
l='ch10/05-project';s=sol(l,'release-row')
add(l,'release-row','sort eligible history descending',s.replace('last = same_day.loc[same_day["date"].idxmax()]','last = same_day.sort_values("date", ascending=False).iloc[0]'),True,basis='Latest eligible weekday is independent of input row order or algorithm.')
add(l,'release-row','include unfinished release day',s.replace('< pd.Timestamp(as_of)','<= pd.Timestamp(as_of)'),False,basis='Cash and actual weather for release day are unavailable until day end.')
s=sol(l,'split')
future='''\n_before = X.copy()\n_changed = s.copy()\n_future = _changed.date >= "2025-07-01"\n_changed.loc[_future,"revenue_k"] += 1000000\n_changed.loc[_future,"temp"] = 99\n_changed.loc[_future,"rain"] = 1\nassert prep(_changed).equals(_before), "Future facts changed issued features"\n'''
add(l,'split','future cash and weather altered, feature frame invariant',s+future,True,basis='One-shot July issue uses history-only weather scenario; future cash must not enter features.')
add(l,'split','future weather leaks directly into X',s+'\nX.loc[~tr,"temp"] = s.loc[~tr,"temp"]',False,basis='Task requires historical monthly scenario for unknown future weather.')
s=sol(l,'baselines')
add(l,'baselines','calendar forecast invariant after future fact revisions',s+'''\n_saved_X = X.copy()\n_saved_lag = lag7.copy()\n_changed = s.copy()\n_future = _changed.date >= "2025-07-01"\n_changed.loc[_future,"revenue_k"] += 1000000\n_changed.loc[_future,"temp"] = 99\n_changed.loc[_future,"rain"] = 1\nassert prep(_changed).equals(_saved_X), "Future facts changed issued features"\n_changed_history = _changed[~_future].assign(weekday=_changed.loc[~_future,"date"].dt.weekday).sort_values("date")\n_changed_last = _changed_history.groupby(["shop_id","weekday"])["revenue_k"].last()\n_changed_lag = pd.Series([_changed_last.loc[(r.shop_id,r.date.weekday())] for r in _changed.itertuples()],index=_changed.index)\nassert _changed_lag.equals(_saved_lag), "Future cash changed issued calendar forecast"\n''',True,basis='Both December and July forecasts use history through June; future actuals only affect evaluation errors.')
assert len(rows)==36
(HERE/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(HERE/'before-tasks.json').write_text(json.dumps(list(items.values()),ensure_ascii=False,indent=2))
(HERE/'expected-before-execution.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='code'} for r in rows],ensure_ascii=False,indent=2))
# Confirm exactly recovered historical code hashes, including all twelve additional programs.
old=[json.loads(s) for s in (ROOT/'docs/course-improvements/reaudit/fixes/technical-results.jsonl').read_text().splitlines()]
sha={r['code_sha256'] for r in old if r['task'].startswith('ch10/')}
assert all(r['code_sha256'] in sha for r in rows[:20])
(HERE/'frozen.sha256').write_text(''.join(hashlib.sha256((HERE/f).read_bytes()).hexdigest()+'  '+f+'\n' for f in ['programs.jsonl','expected-before-execution.json','before-tasks.json','visible-contracts.json']))
data=HERE/'data-baseline';data.mkdir(exist_ok=True)
for name in sorted({f for t in items.values() for f in t.get('files',[])}):shutil.copyfile(ROOT/'site/data'/name,data/name)
print('Frozen 36 programs, 20 exact historical hashes, 16 new, 88 task/cell/predict items')
