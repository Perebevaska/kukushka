"""Build a private executable proposal. Does not alter repository course sources."""
from pathlib import Path
import json,difflib,re,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
items=json.loads((HERE/'before-tasks.json').read_text()); tasks={i['lesson']+'/'+i['id']:i for i in items}
changes={}
def put(key,field,value):
 changes.setdefault(key,{})[field]=value;tasks[key][field]=value

def append(key,extra):put(key,'check',tasks[key]['check']+'\n'+extra.strip()+'\n')
series_helper='''import numpy as _np, pandas as _pd
def _same_series(got, expected, atol=1e-8):
    assert isinstance(got, _pd.Series), 'Сохраните Series с исходными ключами.'
    assert got.index.is_unique and len(got)==len(expected), 'Проверьте число строк и уникальность ключей.'
    assert got.index.sort_values().equals(expected.index.sort_values()), 'Ключи/даты результата не совпадают.'
    assert _np.allclose(got.reindex(expected.index).to_numpy(), expected.to_numpy(), atol=atol, rtol=0, equal_nan=True), 'Проверьте значения по каждому ключу/дате.'
'''
frame_helper='''import numpy as _np, pandas as _pd
def _same_frame(got, expected):
    assert isinstance(got, _pd.DataFrame), 'Сохраните DataFrame.'
    assert set(expected.columns)<=set(got.columns), 'Не хватает заявленных столбцов.'
    assert got.index.is_unique and len(got)==len(expected), 'Проверьте число строк и уникальность дат.'
    assert got.index.sort_values().equals(expected.index.sort_values()), 'Даты результата не совпадают.'
    assert _np.allclose(got.reindex(expected.index)[expected.columns].to_numpy(), expected.to_numpy(), atol=1e-8, rtol=0, equal_nan=True), 'Сверьте все значения по временным ключам.'
'''
key='ch12/01-resample/load';append(key,series_helper+"\n_same_series(need('s'),s0)\n")
key='ch12/01-resample/daily';s=tasks[key]['check'];s=series_helper+s
s=s.replace("assert need('daily', _pd.Series).equals(d0), 'daily — s.resample(\"D\").sum().'","_same_series(need('daily'),d0)")
s=s.replace("assert _pd.Series(need('weekly_mean')).round(6).equals(w0.round(6)), 'weekly_mean — daily.resample(\"W\").mean().'","_same_series(need('weekly_mean'),w0,1e-6)")
s=s.replace("assert list(_pd.Series(need('week_days')).values) == list(c0.values), 'week_days — daily.resample(\"W\").count().'","_same_series(need('week_days'),c0)")
put(key,'check',s)
key='ch12/01-resample/by-hour';put(key,'check',tasks[key]['check'].replace("p = need('profile', _pd.DataFrame)","p = need('profile', _pd.DataFrame).sort_index()"))
key='ch12/01-resample/growth';append(key,series_helper+"\n_same_series(need('trend28'),s0.resample('D').sum().rolling(28).mean())")
key='ch12/01-resample/months'
put(key,'check',series_helper+'''s0 = _pd.read_csv('app_orders.csv', parse_dates=['datetime'], index_col='datetime')['orders']
m = s0.resample('MS').sum(); g = (m.pct_change() * 100).round(1)
raw_daily = s0.resample('D').sum().resample('MS').mean()
pdm=raw_daily.round(1); gp=(raw_daily.pct_change()*100).round(1)
_same_series(need('monthly'),m)
_same_series(need('growth'),g,0.06)
_same_series(need('per_day'),pdm,0.06)
_same_series(need('growth_per_day'),gp,0.06)
assert need('slowest_month') == g.idxmin().month and need('slowest_month_per_day') == gp.idxmin().month, 'Выберите месяц минимального роста отдельно для сумм и среднего за день.'
''')
key='ch12/01-resample/zeros';put(key,'check',tasks[key]['check'].replace("g = need('zero_by_hour', _pd.Series)","g = need('zero_by_hour', _pd.Series).sort_index()"))
key='ch12/02-decompose/toy-trend';s=series_helper+tasks[key]['check'];s=s.replace("assert _pd.Series(need('trend7')).round(6).equals(tr.round(6)), 'trend7 — toy.rolling(7, center=True).mean().'","_same_series(need('trend7'),tr,1e-6)").replace("g = need('seasonal_week', _pd.Series)","g = need('seasonal_week', _pd.Series).sort_index()")
put(key,'check',s)
key='ch12/02-decompose/diff';append(key,series_helper+"\n_same_series(need('d1'),d0.diff())\n_same_series(need('d7'),d0.diff(7))")
key='ch12/02-decompose/hour-season';put(key,'check',tasks[key]['check'].replace("got = need('season24', _pd.Series)","got = need('season24', _pd.Series).sort_index()"))
key='ch12/02-decompose/acf-plot';append(key,'''bars=sorted(ax.patches,key=lambda p:p.get_x()+p.get_width()/2)
assert _np.allclose([p.get_x()+p.get_width()/2 for p in bars],range(1,201),rtol=0,atol=1e-8), 'Ось X столбцов должна соответствовать лагам 1…200.'
assert _np.allclose([p.get_height() for p in bars],v,rtol=0,atol=1e-8), 'Высота каждого столбца должна равняться автокорреляции соответствующего лага.'
''')
key='ch12/03-features/calendar';put(key,'check',tasks[key]['check'].replace("d = need('df', _pd.DataFrame)","d = need('df', _pd.DataFrame).sort_index()").replace('календарь и порядок строк','календарь и состав строк'))
key='ch12/03-features/make-features'
put(key,'check',frame_helper+'''s0 = _pd.read_csv('app_orders.csv',parse_dates=['datetime'],index_col='datetime')['orders']
s0=s0[s0.index<'2026-08-01']
def _reference(z):
    d=_pd.DataFrame({'y':z,'hour':z.index.hour,'dow':z.index.dayofweek,'weekend':(z.index.dayofweek>=5).astype(int)})
    for k in (1,24,168):d[f'lag_{k}']=z.shift(k)
    d['roll_24']=z.shift(1).rolling(24).mean()
    return d.dropna()
f=need('make_features')
_same_frame(f(s0.copy()),_reference(s0))
_same_frame(need('df'),_reference(s0))
assert need('first_ts')==s0.index[168], 'first_ts — первый час после 168 часов истории.'
for n in (200,400):
    z=_pd.Series((_np.arange(n)*17)%71,index=_pd.date_range('2027-02-01 03:00',periods=n,freq='h'))
    _same_frame(f(z.copy()),_reference(z))
''')
key='ch12/03b-time-split/check-order';append(key,'''assert bool(f(_a.iloc[[5,0]],_a.iloc[[4,3]])) is False, 'Порядок внутри частей не важен: max(train)=05:00 позже min(test)=03:00.'
assert bool(f(_a.iloc[[0,1]],_a.iloc[[1,2]])) is False, 'Одинаковая временная метка в train и test не удовлетворяет условию «раньше».'
''')
key='ch12/04-forecast/metrics';append(key,'''assert close(need('wape')(_np.array([10.,0.,20.]),_np.array([12.,1.,18.])),5/30), 'WAPE включает ошибки часов с нулевым фактом в числитель.'
''')
key='ch12/05-project/split';append(key,frame_helper+"\n_same_frame(need('df'),d)\n")
# Explicitly approved public protocol: only labels available at the July31 20:00 selection date.
key='ch12/05-project/baseline'
score_mask='valid_score = (valid & (y.index < "2026-07-31 20:00") & y.notna())\n'
put(key,'check',tasks[key]['check'].replace('y[test]','y[vm]').replace("X.loc[test, 'mean4w']","X.loc[vm, 'mean4w']"))
put(key,'check',"vm = (valid & (y.index < '2026-07-31 20:00') & y.notna())\n"+tasks[key]['check'])
put(key,'solution',score_mask+tasks[key]['solution'].replace('y[test]','y[valid_score]').replace('X.loc[test, "mean4w"]','X.loc[valid_score, "mean4w"]'))
put(key,'starter',tasks[key]['starter']+'\n'+score_mask+'# rmse_base — 740 известных июльских часов; base_meets не является приёмкой августа.\n')
key='ch12/05-project/select'
fit_mask='fit_mask = (train & (y.index < "2026-06-30 20:00") & y.notna())\n'
put(key,'solution',tasks[key]['solution'].replace('valid_rmse = {}',fit_mask+score_mask+'valid_rmse = {}').replace('m.fit(X[train], y[train])','m.fit(X[fit_mask], y[fit_mask])').replace('y[valid]','y[valid_score]').replace('X[valid]','X[valid_score]'))
put(key,'check',tasks[key]['check'].replace("w = {k:","fm = (train & (y.index < '2026-06-30 20:00') & y.notna())\nvm = (valid & (y.index < '2026-07-31 20:00') & y.notna())\nassert _np.array_equal(need('fit_mask'),fm), 'fit_mask исключает неизвестные ответы 30 июня 20:00–23:00.'\nassert _np.array_equal(need('valid_score'),vm), 'valid_score — 740 июльских часов до 31 июля 20:00.'\nw = {k:").replace('m.fit(X[train], y[train])','m.fit(X[fm], y[fm])').replace('y[valid]','y[vm]').replace('X[valid]','X[vm]'))
put(key,'starter',tasks[key]['starter']+'\n'+fit_mask+score_mask)
append(key,'''
# Check that unavailable fit labels and unavailable validation labels cannot affect selection.
for _start,_end in [('2026-06-30 20:00','2026-07-01'),('2026-07-31 20:00','2026-08-01')]:
    for _sign in (1,-1):
        _probe=dict(globals())
        _probe['X']=X.copy(); _probe['y']=y.copy()
        _unknown=(_probe['y'].index>=_start)&(_probe['y'].index<_end)
        _probe['y'].loc[_unknown]+=_sign*1000
        exec(_code,_probe)
        assert all(close(_probe['valid_rmse'][k],got[k],0.002) for k in w), 'Выбор модели зависит от ответов, неизвестных к моменту выпуска: исключите последние четыре часа из fit и из оценки июля.'
''')
key='ch12/05-project/grid'
put(key,'setup',tasks[key]['setup'].replace('df = make(s)',"s = s[s.index < '2026-08-01']\ndf = make(s)"))
put(key,'check',tasks[key]['check'].split('pt = _np.clip(')[0].replace('g.cv.gap >= 28','g.cv.gap == 28'))
put(key,'solution',tasks[key]['solution'].split('p = np.clip(')[0]+'print(best_params, cv_rmse)\n')
# The task uses already prepared X/y but the CV endpoint and gap are visible in starter.
put(key,'starter',tasks[key]['starter']+'\n# cv=TimeSeriesSplit(n_splits=3, gap=28); август здесь не оцениваем.\n')
key='ch12/05-project/final'
put(key,'starter',tasks[key]['starter']+'\n# В этом шаге rmse_base уже рассчитан на августе: сравниваем две зафиксированные политики.\n# fit_mask исключает 31 июля 20:00–23:00; эти ответы на первую дату выпуска неизвестны.\n')
# Explicit helper interface for the future-known marketing calendar, independent of future y.
key='ch12/03-features/promo-feature'
old='"2026-07-24", "2026-07-24"'
new='"2026-07-24", "2026-08-21"'
starter=tasks[key]['starter'].replace(old,new)+'''

def make_promo(index):
    # Верните Series 0/1 с часовыми ключами index; даты известны из promo_days.
    # Акция действует с 10:00 до 20:00 включительно. Будущие orders не нужны.
    pass

future_index = pd.to_datetime(["2026-08-21 09:00", "2026-08-21 10:00", "2026-08-21 20:00", "2026-08-21 21:00"])
# make_promo(future_index) должен дать 0, 1, 1, 0 по этим временным ключам.
# Для текущей таблицы: df["promo"] = make_promo(df.index).
'''
put(key,'starter',starter)
solution=tasks[key]['solution'].replace(old,new)
marker='\ndf = make_features(s)'
assert marker in solution
solution=solution.replace(marker,'''
def make_promo(index):
    flags = index.normalize().isin(promo_days) & (index.hour >= 10) & (index.hour <= 20)
    return pd.Series(flags.astype(int), index=index)

''' + marker.lstrip(),1)
solution=solution.replace('hours = df.index.hour\ndf["promo"] = (df.index.normalize().isin(promo_days) & (hours >= 10) & (hours <= 20)).astype(int)','df["promo"] = make_promo(df.index)')
put(key,'solution',solution)
put(key,'check',tasks[key]['check'].replace("'2026-07-24', '2026-07-24'","'2026-07-24', '2026-08-21'"))
append(key,frame_helper+series_helper+'''
_same_frame(need('df'),d)
f=need('make_promo')
dates=_pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24','2026-08-21'])
future=_pd.DatetimeIndex([day+_pd.Timedelta(hours=h) for day in dates for h in (9,10,20,21)]+[_pd.Timestamp('2026-08-20 10:00'),_pd.Timestamp('2026-08-22 10:00')])
expected=_pd.Series((future.normalize().isin(dates)&(future.hour>=10)&(future.hour<=20)).astype(int),index=future)
_same_series(f(future),expected)
permuted=future[::-1]
_same_series(f(permuted),expected.reindex(permuted))
''')

# Runtime proposal plus exact four-field source patch; prose/hints/explain managed independently by expert.
(HERE/'proposal-tasks.json').write_text(json.dumps(list(tasks.values()),ensure_ascii=False,indent=2)+'\n')
(HERE/'proposed-fields.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
patch=[]
for filename in sorted({k.split('/')[1] for k in changes}):
 relative='content/ch12/'+filename+'.md';old=(ROOT/relative).read_text();new=old
 for key,fields in changes.items():
  if key.split('/')[1]!=filename:continue
  task=key.rsplit('/',1)[1]
  pattern=r'(^## task: '+re.escape(task)+r'\s*\|.*?)(?=^## task: |\Z)'
  m=re.search(pattern,new,re.M|re.S);assert m,key
  section=m.group(1)
  for field,value in fields.items():
   pattern2=r'(^### '+field+r'\n```python\n)(.*?)(^```)' 
   sm=re.search(pattern2,section,re.M|re.S)
   assert sm,(key,field)
   section=section[:sm.start(2)]+value.rstrip()+'\n'+section[sm.end(2):]
  new=new[:m.start(1)]+section+new[m.end(1):]
 target=HERE/'proposal-content'/'ch12'/(filename+'.md');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(new)
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
(HERE/'proposal.patch').write_text(''.join(patch))
print('Prepared',len(changes),'task changes;',len(patch),'patch lines; no source writes')
