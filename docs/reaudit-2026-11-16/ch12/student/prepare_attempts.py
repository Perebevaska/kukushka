from pathlib import Path
import json
D=Path(__file__).parent
common='''import pandas as pd
import numpy as np
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
'''
make='''def make_features(s):
    df = pd.DataFrame({'y':s})
    df['hour']=df.index.hour
    df['dow']=df.index.dayofweek
    df['weekend']=(df['dow']>=5).astype(int)
    for k in (1,24,168): df[f'lag_{k}']=s.shift(k)
    df['roll_24']=s.shift(1).rolling(24).mean()
    return df.dropna()
'''
horizon='''def make(s,lags,roll_shift):
    df=pd.DataFrame({'y':s})
    df['hour']=df.index.hour
    df['dow']=df.index.dayofweek
    df['weekend']=(df['dow']>=5).astype(int)
    for k in lags: df[f'lag_{k}']=s.shift(k)
    df['roll']=s.shift(roll_shift).rolling(24).mean()
    df['mean4w']=pd.concat([s.shift(168*k) for k in range(1,5)],axis=1).mean(axis=1)
    return df.dropna()
'''
err='''def error(a,b): return float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))
'''
learn='from sklearn.ensemble import HistGradientBoostingRegressor\nfrom sklearn.linear_model import LinearRegression\n'
rows={}
def add(lesson,task,code,expect,source):
    rows.setdefault(lesson,[]).append(dict(lesson=lesson,task=task,code=code,expect=expect,Q1=f'Получить {task}: {expect}',Q2=f'В публичном уроке {lesson}: {source}; ввожу код в карточку {task}.',Q3=expect))
l='01-resample'
add(l,'load',common+'''n=len(s)
start=s.index.min()
end=s.index.max()
zero_hours=int(s.eq(0).sum())''','Series datetime, n=4416, start=1 марта 00:00, end=31 августа 23:00, zero_hours неотрицательное целое','Дата как индекс')
add(l,'slice',common+'''day_total=s['2026-05-22'].sum()
morning=s['2026-05-22 08:00':'2026-05-22 10:00'].sum()
share_morning=round(morning/day_total,3)''','day_total сумма 24 часов; morning сумма 3 часов, доля 0..1','срез включает правую границу')
add(l,'daily',common+'''daily=s.resample('D').sum()
weekly_mean=daily.resample('W').mean()
week_days=daily.resample('W').count()
best_week=weekly_mean[week_days.eq(7)].idxmax()
best_mean=round(weekly_mean[best_week],1)''','daily 184 строки; первая/последняя недели 1 день; best_week воскресенье полной недели','resample W и неполные корзины')
add(l,'p-roll',common+'''daily=s.resample('D').sum()
trend=daily.rolling(7).mean()
print(int(trend.isna().sum()))''','вывод 6, ряд остаётся 184 строки','скользящее среднее')
add(l,'by-hour',common+'''wd=s.index.dayofweek<5
profile=pd.DataFrame({'будни':s[wd].groupby(s[wd].index.hour).mean(),'выходные':s[~wd].groupby(s[~wd].index.hour).mean()}).round(1)
peak_weekday=profile['будни'].idxmax()
peak_weekend=profile['выходные'].idxmax()''','profile (24,2), индексы 0..23, максимумы в часах','части индекса и группировка')
add(l,'growth',common+'''daily=s.resample('D').sum()
trend28=daily.rolling(28).mean()
a=trend28.dropna().iloc[0]
b=trend28.iloc[-1]
first_value=round(a)
last_value=round(b)
growth_pct=round((b/a-1)*100,1)''','trend28 первые 27 NaN, рост положительный %, first/last целые','rolling')
add(l,'months',common+'''monthly=s.resample('MS').sum()
growth=(monthly.pct_change()*100).round(1)
raw=s.resample('D').sum().resample('MS').mean()
per_day=raw.round(1)
growth_per_day=(raw.pct_change()*100).round(1)
slowest_month=growth.idxmin().month
slowest_month_per_day=growth_per_day.idxmin().month''','6 месячных строк, первые росты NaN, per_day в заказах за день','pct_change и месяцы')
add(l,'zeros',common+'''zero_by_hour=s.eq(0).groupby(s.index.hour).mean().round(2)
night_hours=zero_by_hour[zero_by_hour>0.3].index.tolist()
z=s[(s.index.hour>=8)&(s.index.hour<=20)&s.eq(0)]
n_day_zeros=len(z)
outage_dates=sorted(set(z.index.date))''','24 доли 0..1, дневной сбой включает 3 июня','нулевые часы и группировка')
add(l,'anomalies',common+'''usual=pd.concat([s.shift(168*k) for k in range(1,5)],axis=1).median(axis=1)
bad_hours=s.index[(s.index.hour>=10)&(s.index.hour<=20)&(usual>=8)&(s<0.2*usual)].tolist()
bad_days=sorted(set(t.date() for t in bad_hours))''','список Timestamp и уникальных date; ниже 20% медианы прошлых недель','лаги и медиана по строке в условии')
add(l,'friday',common+'''daily=s.resample('D').sum()
dow_mean=daily.groupby(daily.index.dayofweek).mean().round(1)
ratio=daily/daily.shift(1).rolling(7).mean()
spikes=list(ratio.nlargest(5).index.date)
all_fridays=all(t.weekday()==4 for t in spikes)''','5 дат по убыванию отношения; проверю все пятницы, dow_mean 7 строк','разбор недельного ритма')
l='02-decompose'
season='from statsmodels.tsa.seasonal import seasonal_decompose\n'
add(l,'decompose',common+season+'''daily=s.resample('D').sum()
parts=seasonal_decompose(daily,period=7)
t=parts.trend.dropna()
trend_growth=round(t.iloc[-1]-t.iloc[0],1)
best_dow=parts.seasonal.groupby(parts.seasonal.index.dayofweek).mean().idxmax()''','положительный рост тренда, best_dow=4 по видимой теории','Три части ряда')
add(l,'toy-trend','''trend7=toy.rolling(7,center=True).mean()
seasonal_week=(toy-trend7).groupby(toy.index.dayofweek).mean().round(1)
pattern_sum=round(seasonal_week.sum(),1)''','21 значение тренда, 6 NaN, 7 сезонных поправок; сумма около нуля если узор центрирован','центрированное окно')
add(l,'p-acf',common+'''lags=[1,24,168]
values=[s.autocorr(k) for k in lags]
best=lags[values.index(max(values))]
print(best)''','вывод 168','Автокорреляция')
add(l,'diff',common+'''daily=s.resample('D').sum()
d1=daily.diff()
d7=daily.diff(7)
mean_d1=round(d1.mean(),2)
mean_d7=round(d7.mean(),2)
std_ratio=round(daily.std()/d1.std(),2)''','184 строки, 1/7 NaN; средние в заказах/день, ratio безразмерный','разности')
add(l,'adf',common+'''from statsmodels.tsa.stattools import adfuller
a=s['2026-08']
pvals=[adfuller(a)[1],adfuller(a.diff(24).dropna())[1],adfuller(s.resample('D').sum())[1]]
p_hour_aug,p_hour_diff24,p_daily=[round(p,4) for p in pvals]
stationary=[name for name,p in zip(['часы август','часы разность 24','дни'],pvals) if p<0.05]''','p в 0..1; дневной p около .8; stationary это метка по порогу ADF, не полное доказательство','ADF')
add(l,'hour-season',common+season+'''parts=seasonal_decompose(s['2026-08-03':'2026-08-16'],period=24)
raw=parts.seasonal.iloc[:24]
season24=pd.Series(raw.to_numpy(),index=raw.index.hour).round(1)
night_min=season24.idxmin()
amplitude=round(raw.max()-raw.min(),1)''','24 сезонные поправки; минимум ночью, амплитуда в заказах','суточная сезонность')
add(l,'seasonal-diff',common+'''raw={k:s.diff(k).std() for k in (1,24,168)}
std_level=round(s.std(),2)
std_by_lag={k:round(v,2) for k,v in raw.items()}
best_lag=min(raw,key=raw.get)
gain=round(s.std()/raw[best_lag],2)''','best_lag ожидаю 168, gain>1','какая разность спокойнее')
add(l,'multiplicative',common+'''ar={m:s['2026-'+m].groupby(s['2026-'+m].index.hour).mean() for m in ['03','08']}
a={m:v.max()-v.min() for m,v in ar.items()}
u={m:s['2026-'+m].mean() for m in ar}
amp={m:round(v,1) for m,v in a.items()}
level={m:round(v,2) for m,v in u.items()}
amp_growth=round(a['08']/a['03'],2)
level_growth=round(u['08']/u['03'],2)
model_type='multiplicative' if abs(amp_growth/level_growth-1)<0.1 else 'additive' ''','два ключа 03/08; сравнение относительных ростов размаха и уровня','мультипликативная модель')
add(l,'acf-plot',common+'''import matplotlib.pyplot as plt
acf_vals=[s.autocorr(k) for k in range(1,201)]
fig,ax=plt.subplots()
ax.bar(range(1,201),acf_vals)
ax.set_xlabel('лаг, часов')
top3=sorted(range(1,201),key=lambda k:acf_vals[k-1],reverse=True)[:3]
near_day=max(range(20,29),key=lambda k:acf_vals[k-1])
plt.show()''','200 корреляций; near_day около 24; график с осью в часах','ACF и условие bar')
add(l,'residual-days',common+season+'''parts=seasonal_decompose(s.resample('D').sum(),period=7)
r=parts.resid
out=r[r.abs()>3*r.std()].sort_index()
outliers=list(out.index.date)
kinds=['всплеск' if v>0 else 'провал' for v in out]''','одинаковые длины dates/kinds; возможны акции и сбой','остаток')
l='03-features'
pre=common+"s=s[s.index<'2026-08-01']\n"
add(l,'calendar',pre+'''df=pd.DataFrame({'y':s})
df['hour']=df.index.hour
df['dow']=df.index.dayofweek
df['weekend']=(df['dow']>=5).astype(int)
weekend_share=round(df.weekend.mean(),3)''','3672 строки, 4 столбца, доля выходных около 2/7','Календарь')
add(l,'p-lags',common+'''df=pd.DataFrame({'y':s})
df['lag_1']=s.shift(1)
df['lag_24']=s.shift(24)
df=df.dropna()
print(len(df))''','4416-24=4392 строки','лаги')
add(l,'leak-check',"leaky=['b','d']",'b включает y, d следующий y; список b,d','утечка через окно')
add(l,'make-features',pre+make+'''df=make_features(s)
first_ts=df.index[0]''','3504 строки, 8 столбцов, first_ts=8 марта 00:00','ряд как таблица')
add(l,'feature-sets',pre+make+learn+err+'''df=make_features(s)
train=df.index<'2026-07-01'
calendar=['hour','dow','weekend']
sets={'календарь':calendar,'лаги':calendar+['lag_1','lag_24','lag_168'],'всё':list(df.columns.drop('y'))}
rmse={}
for name,cols in sets.items():
    p=HistGradientBoostingRegressor(random_state=0).fit(df.loc[train,cols],df.loc[train,'y']).predict(df.loc[~train,cols])
    rmse[name]=round(error(df.loc[~train,'y'],p),3)''','3 RMSE в заказах/час; календарь около 4.25, лаги около 4.01 по теории','сравнение признаков')
add(l,'leak-test','''def leak_test(features,s,t):
    spoiled=s.copy()
    spoiled.loc[t]+=1000
    changed=features(spoiled).loc[t]!=features(s).loc[t]
    return sorted(changed.index[changed].tolist())
leaking=leak_test(features,s,pd.Timestamp('2026-07-15 12:00'))''','отсортированный список реально изменившихся названий; лаги не изменятся','тест на утечку')
add(l,'onehot-hours',pre+learn+err+'''df=pd.DataFrame({'y':s,'hour':s.index.hour,'dow':s.index.dayofweek})
tr=df.index<'2026-07-01'
a=df[['hour','dow']]
b=pd.get_dummies(a.astype(str))
c=b.copy()
c['t']=np.arange(len(df))
n_onehot_cols=b.shape[1]
rmse={}
for name,X in [('num',a),('onehot',b),('onehot_trend',c)]:
    p=LinearRegression().fit(X[tr],df.y[tr]).predict(X[~tr])
    rmse[name]=round(error(df.y[~tr],p),3)''','31 onehot-столбец; onehot лучше числа, добавление времени учитывает тренд','час как категория')
add(l,'promo-feature',pre+make+learn+err+'''df=make_features(s)
tr=df.index<'2026-07-01'
X=df.drop(columns='y')
y=df.y
p0=HistGradientBoostingRegressor(random_state=0).fit(X[tr],y[tr]).predict(X[~tr])
X['promo']=(X.index.normalize().isin(pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24']))&(X.index.hour>=10)&(X.index.hour<=20)).astype(int)
p1=HistGradientBoostingRegressor(random_state=0).fit(X[tr],y[tr]).predict(X[~tr])
pm=X.loc[~tr,'promo'].eq(1).to_numpy()
rmse_without=round(error(y[~tr],p0),3)
rmse_with=round(error(y[~tr],p1),3)
promo_without=round(error(y[~tr][pm],p0[pm]),3)
promo_with=round(error(y[~tr][pm],p1[pm]),3)''','4 RMSE; акция отдельно 11 часов; проверю улучшение, не считаю гарантированным','признак известной акции')
l='03b-time-split'
pref=pre+make+learn+err+'''from sklearn.model_selection import train_test_split,TimeSeriesSplit,KFold,cross_val_score
df=make_features(s)
X,y=df.drop(columns='y'),df.y
'''
splits='''a,b,c,d=train_test_split(X,y,test_size=.2,shuffle=False)
e,f,g,h=train_test_split(X,y,test_size=.2,random_state=0)
'''
models='''p=HistGradientBoostingRegressor(random_state=0).fit(a,c).predict(b)
q=HistGradientBoostingRegressor(random_state=0).fit(e,g).predict(f)
rmse_time=round(error(d,p),3)
rmse_shuffled=round(error(h,q),3)
'''
add(l,'noshuffle',pref+splits+models+'''test_start=b.index.min()
gap=round(rmse_time-rmse_shuffled,3)''','хвост=701 час для 3504 строк; дата в начале июля, gap положителен ожидаемо','shuffle=False')
add(l,'check-order',pref+splits+'''def is_time_split(X_tr,X_te): return bool(X_tr.index.max()<X_te.index.min())
honest_ok=is_time_split(a,b)
shuffled_ok=is_time_split(e,f)
n_later=int((e.index>f.index.min()).sum())''','True/False, n_later>0 при перемешивании','проверка max<min')
add(l,'same-period',pref+splits+models+'''tail=f.index>=b.index.min()
n_tail=int(tail.sum())
rmse_shuffled_tail=round(error(h[tail],q[tail]),3)
part_period=round(rmse_shuffled_tail-rmse_shuffled,3)
part_shuffle=round(rmse_time-rmse_shuffled_tail,3)''','две компоненты складываются в разрыв с погрешностью округления; общий период не гарантирует причинной изоляции','тот же период')
add(l,'folds',pre+'''from sklearn.model_selection import TimeSeriesSplit
train_sizes=[]
test_starts=[]
for tr,te in TimeSeriesSplit(n_splits=4).split(s):
    train_sizes.append(len(tr))
    test_starts.append(s.index[te[0]])
    assert s.index[te[0]]-s.index[tr[-1]]==pd.Timedelta(hours=1)''','4 растущих длины; train_sizes [736,1470,2204,2938] на 3672 строках','границы folds')
add(l,'tscv',pref+'''v=-cross_val_score(HistGradientBoostingRegressor(random_state=0),X,y,cv=TimeSeriesSplit(n_splits=5),scoring='neg_root_mean_squared_error',n_jobs=1)
scores=np.round(v,2)
mean_rmse=round(v.mean(),3)
w=-cross_val_score(HistGradientBoostingRegressor(random_state=0),X,y,cv=KFold(5,shuffle=True,random_state=0),scoring='neg_root_mean_squared_error',n_jobs=1)
mean_rmse_kfold=round(w.mean(),3)''','5 положительных ошибок; KFold предположительно оптимистичнее','TimeSeriesSplit и cross_val_score')
add(l,'month-folds',pref+'''month_rmse={}
month_mean={}
rel_error={}
for m in ['05','06','07']:
    start=pd.Timestamp('2026-'+m+'-01')
    tr=X.index<start
    te=(X.index>=start)&(X.index<start+pd.offsets.MonthBegin(1))
    p=HistGradientBoostingRegressor(random_state=0).fit(X[tr],y[tr]).predict(X[te])
    r=error(y[te],p)
    avg=y[te].mean()
    month_rmse[m]=round(r,3)
    month_mean[m]=round(avg,2)
    rel_error[m]=round(r/avg,3)''','считаю явно заданные май/июнь/июль с ключами 05/06/07; ключ 08 противоречит данным','тесты по месяцам')
l='04-forecast'
add(l,'naive',pre+'''test=s['2026-07-01':]
mae={k:round((test-s.shift(k).loc[test.index]).abs().mean(),3) for k in (1,24,168)}
best_lag=min(mae,key=mae.get)''','3 MAE в заказах; best_lag ожидаю 168','наивные прогнозы')
add(l,'metrics','''import numpy as np
def mae(fact,pred): return float(np.abs(fact-pred).mean())
def rmse(fact,pred): return float(np.sqrt(np.mean((fact-pred)**2)))
def wape(fact,pred): return float(np.abs(fact-pred).sum()/fact.sum())
m={name:round(fun(fact,pred),3) for name,fun in [('mae',mae),('rmse',rmse),('wape',wape)]}''','RMSE>=MAE; WAPE безразмерна, факты берутся из заготовки','метрики своими руками')
add(l,'wape',pre+'''def wape(fact,pred): return float(np.abs(fact-pred).sum()/fact.sum())
test=s['2026-07-01':]
pred=s.shift(168).loc[test.index]
w=round(wape(test,pred),3)
zeros=int(test.eq(0).sum())''','w в долях около .376, zeros>0','WAPE')
add(l,'p-horizon',common+'''df=pd.DataFrame({'y':s})
for k in (24,48,168):
    df[f'lag_{k}']=s.shift(k)
df['roll']=s.shift(24).rolling(24).mean()
print(list(df.columns[1:]))''',"['lag_24','lag_48','lag_168','roll']",'признаки при выпуске в полночь')
add(l,'bias','''bias=round((test-m4.loc[test.index]).mean(),3)
share_under=round((m4.loc[test.index]<test).mean(),3)
ratio=round(test.sum()/m4.loc[test.index].sum(),3)
bias_adj=round((test-adj.loc[test.index]).mean(),3)
rmse_m4=round(float(np.sqrt(((test-m4.loc[test.index])**2).mean())),3)
rmse_adj=round(float(np.sqrt(((test-adj.loc[test.index])**2).mean())),3)''','bias положителен при росте; share 0..1; adj уже задана, результат не гарантирую','систематический недопрогноз')
add(l,'mean4w',pre+err+'''test=s['2026-07-01':]
rmse_k={}
for k in (1,2,4,8):
    p=pd.concat([s.shift(168*j) for j in range(1,k+1)],axis=1).mean(axis=1)
    rmse_k[k]=round(error(test,p.loc[test.index]),3)
best_k=min(rmse_k,key=rmse_k.get)''','4 значения RMSE; 8 недель имеют полную историю на июле','сильный ориентир')
compare=pre+horizon+learn+err+'''def evaluate(lags,shift,cls):
    df=make(s,lags,shift)
    tr=df.index<'2026-07-01'
    X=df.drop(columns='y')
    p=cls.fit(X[tr],df.y[tr]).predict(X[~tr])
    return error(df.y[~tr],p),df.y[~tr],p
'''
add(l,'horizon-gap',compare+'''a,_,_=evaluate((1,24,168),1,HistGradientBoostingRegressor(random_state=0))
b,_,_=evaluate((24,48,168),24,HistGradientBoostingRegressor(random_state=0))
rmse_hour=round(a,3)
rmse_day=round(b,3)
gap_pct=round((b/a-1)*100,1)''','две RMSE; горизонт сутки лишён свежего лага, процент может быть положителен','цена горизонта')
add(l,'leak-horizon',compare+'''a,_,_=evaluate((1,24,48,168),1,LinearRegression())
b,_,_=evaluate((24,48,168),24,LinearRegression())
rmse_leak=round(a,3)
rmse_fair=round(b,3)
fooled=bool(a<b)''','fooled сравнение двух RMSE; lag1 недоступен на весь день','утечка из-за горизонта')
add(l,'by-hour-error',compare+'''_,y,p=evaluate((24,48,168),24,LinearRegression())
e=pd.Series(np.abs(y-p),index=y.index)
mae_by_hour=e.groupby(e.index.hour).mean().round(2)
worst_hour=mae_by_hour.idxmax()
night_share=round(e[e.index.hour<6].sum()/e.sum(),3)''','24 средние ошибки, доля ночи 0..1','где ошибается модель')
l='05-project'
# публичная make уже подаётся карточками; использую её и сохраняю отсечки fit отдельно
project='''df=make(s)
X,y=df.drop(columns='y'),df['y']
train=df.index<'2026-07-01'
valid=(df.index>='2026-07-01')&(df.index<'2026-08-01')
test=df.index>='2026-08-01'
'''
add(l,'split',project+'''sizes={'train':int(train.sum()),'valid':int(valid.sum()),'test':int(test.sum())}''','valid/test по 744 часа; train зависит от минимальной истории make','разбиение по времени')
add(l,'baseline',err+'''rmse_base=round(error(y[test],df.loc[test,'mean4w']),3)
base_meets=bool(rmse_base<=4.3)''','RMSE в заказах/час; base_meets сравнение с 4.3','ориентир')
add(l,'select',learn+err+'''models={'linear':LinearRegression(),'hgb':HistGradientBoostingRegressor(random_state=0),'hgb_depth3':HistGradientBoostingRegressor(max_depth=3,random_state=0),'hgb_l2':HistGradientBoostingRegressor(l2_regularization=1,random_state=0)}
fit=train&(y.index<'2026-06-30 20:00')&y.notna()
valid_rmse={}
for name,model in models.items():
    p=model.fit(X[fit],y[fit]).predict(X[valid])
    valid_rmse[name]=round(error(y[valid],p),3)
best=min(valid_rmse,key=valid_rmse.get)''','4 RMSE; выбор только на июле, labels после выпуска исключены','выбор на валидации')
add(l,'grid',learn+err+'''from sklearn.model_selection import GridSearchCV,TimeSeriesSplit
fit_mask=(train|valid)&(y.index<'2026-07-31 20:00')&y.notna()
gs=GridSearchCV(HistGradientBoostingRegressor(random_state=0),{'max_depth':[2,3,None],'learning_rate':[.05,.1]},cv=TimeSeriesSplit(n_splits=3),scoring='neg_root_mean_squared_error',n_jobs=1)
gs.fit(X[fit_mask],y[fit_mask])
best_params=gs.best_params_
cv_rmse=round(-gs.best_score_,3)
rmse_test_grid=round(error(y[test],np.clip(gs.predict(X[test]),0,None)),3)''','6 кандидатов×3 folds, best_params два ключа; один зафиксированный августовский результат','grid по времени')
add(l,'final',learn+err+'''fit=(train|valid)&(y.index<'2026-07-31 20:00')&y.notna()
model=HistGradientBoostingRegressor(random_state=0,**best_params).fit(X[fit],y[fit])
pred_test=np.clip(model.predict(X[test]),0,None)
rmse_final=round(error(y[test],pred_test),3)
meets=bool(rmse_final<=4.3 and rmse_final<rmse_base)''','744 прогноза >=0, требование: порог И лучше baseline','финальная проверка')
add(l,'staffing','''y_test=y[test]
open_hours=(y_test.index.hour>=7)&(y_test.index.hour<=22)
needed=np.maximum(1,np.ceil(y_test.to_numpy()/6)).astype(int)
plans={}
for name,p in [('модель',pred_test),('ориентир',df.loc[test,'mean4w'].to_numpy())]:
    plan=np.maximum(1,np.ceil(p/6)).astype(int)
    delta=(plan-needed)[open_hours]
    plans[name]={'short':round(np.mean(delta<0),3),'extra':int(np.maximum(delta,0).sum()),'deficit':int(np.maximum(-delta,0).sum()),'coverage_work':round(np.mean(np.asarray(p)[open_hours]>=y_test.to_numpy()[open_hours]),3)}''','needed длина744, сравнение на496 рабочих часах; нехватка при прогноз6/факте7 =1 человек','ceil и план смен')
add(l,'quantile',learn+'''fit=(train|valid)&(y.index<'2026-07-31 20:00')&y.notna()
q=HistGradientBoostingRegressor(loss='quantile',quantile=.8,random_state=0,**best_params).fit(X[fit],y[fit])
p=np.clip(q.predict(X[test]),0,None)
yt=y[test].to_numpy()
work=(y[test].index.hour>=7)&(y[test].index.hour<=22)
needed=np.maximum(1,np.ceil(yt/6))
plan=np.maximum(1,np.ceil(p/6))
delta=(plan-needed)[work]
coverage=round(np.mean(yt<=p),3)
coverage_work=round(np.mean(yt[work]<=p[work]),3)
short_q=round(np.mean(delta<0),3)
extra_q=int(np.maximum(delta,0).sum())
deficit_q=int(np.maximum(-delta,0).sum())
cost_deficit=3
cost_extra=1
cost_q=cost_deficit*deficit_q+cost_extra*extra_q''','coverage около .8 не обещано; 496 рабочих часов отдельно; цена дефицита3/избытка1 условная','квантиль и цена решения')
questions={
'01-resample':[("predict",1,3,'[nan,15,25,35]'),('quiz',1,1,'rolling ежедневно, resample еженедельно'),('predict',2,1,'diff [nan,2,-1,4], shift(-1) [5,4,8,nan]'),('quiz',2,4,'предыдущий час')],
'02-decompose':[('predict',1,1,'корреляция совпадающих повторов=1'),('quiz',1,2,'суточный ритм'),('quiz',2,1,'разность с тем же часом вчера')],
'03-features':[('predict',1,1,'[nan,nan,6,8]'),('quiz',1,2,'окно включает текущий ответ')],
'03b-time-split':[('predict',1,3,'[10,20,30] [40,50]'),('quiz',1,3,'учится на будущем относительно теста')],
'04-forecast':[('quiz',1,3,'измеряем прирост над ориентиром'),('predict',1,2,'5/30=.17'),('quiz',2,2,'деление на нулевой факт'),('predict',2,1,'[48,168]')],
'05-project':[('quiz',1,3,'нехватка дороже избытка')],
 'test':[('quiz',i,c,e) for i,c,e in zip(range(1,14),[3,2,4,2,2,4,2,4,4,3,2,4,1],['сумма часов за сутки','тренд сезонность остаток','постоянное среднее и ковариация только от лага','кандидаты лаги','shift перед rolling','известные лаги 1,24,168','прошлое перед будущим','прирост над дешёвым baseline','известные к выпуску 48/168','нет деления на каждый ноль','август финальная оценка','RMSE не цена нехватки','сравнить цену часа с очередью4'])]}
for lesson,items in questions.items():
    for kind,n,choice,e in items:
        rows.setdefault(lesson,[]).append(dict(question=f'{lesson}/{kind}/{n}',choice=choice,expect=e,Q1=f'Ответить на {kind}/{n} по смыслу',Q2=f'Видны нумерованные варианты в {lesson}; выбираю {choice}',Q3=e))
for lesson,items in rows.items():
    path=D/(lesson+'.input.jsonl')
    if path.exists(): raise RuntimeError('не перезаписывать input')
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in items))
print({k:len(v) for k,v in rows.items()})
