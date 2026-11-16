from pathlib import Path
import json
D=Path(__file__).parent
OLD=D.parents[2]/'student'
# OLD resolves ch12/student explicitly to avoid overwriting anything there
OLD=Path('docs/reaudit-2026-11-16/ch12/student')
PUB=Path('/private/tmp/kuch12round/student-retest')
targets=json.loads((PUB/'targets-public.json').read_text())
prior={}
for l in ['01-resample','02-decompose','03-features','03b-time-split','04-forecast','05-project']:
 for line in (OLD/(l+'.input.jsonl')).read_text().splitlines():
  r=json.loads(line)
  if 'task' in r: prior[l+'/'+r['task']]=r
common='''import numpy as np
import pandas as pd
s = pd.read_csv("app_orders.csv", parse_dates=["datetime"], index_col="datetime")["orders"]
'''
err='''def error(a,b): return float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))
'''
promo='''promo_days = pd.to_datetime(["2026-04-17","2026-05-22","2026-06-19","2026-07-24","2026-08-21"])
def make_promo(index):
    return pd.Series((index.normalize().isin(promo_days)&(index.hour>=10)&(index.hour<=20)).astype(int),index=index)
'''
codes={}
codes['02-decompose/toy-trend']='import pandas as pd\n'+prior['02-decompose/toy-trend']['code']
codes['03-features/leak-check']=common+'''s=s[s.index<'2026-08-01']
features={'a':s.shift(1),'b':s.rolling(3).mean(),'c':s.shift(1).rolling(3).mean(),'d':s.shift(-1)}
leaky=['b','d']
'''
codes['03-features/leak-test']='''import numpy as np
import pandas as pd
def leak_test(features,s,t):
    base=features(s).loc[t]
    unknown=s.index>=t
    delta=1000+17*np.arange(unknown.sum())+np.arange(unknown.sum())**2
    names=set()
    for sign in (1,-1):
        z=s.astype(float).copy()
        z.loc[unknown]=z.loc[unknown]+sign*delta
        changed=features(z).loc[t]
        same=base.eq(changed)|(base.isna()&changed.isna())
        names.update(base.index[~same])
    return sorted(names)
leaking=leak_test(features,s,pd.Timestamp('2026-07-15 12:00'))
'''
# Own existing make_features is reused, new calendar function is public-input-only.
codes['03-features/promo-feature']=prior['03-features/promo-feature']['code']
a=codes['03-features/promo-feature']
start=a.index("X['promo']=")
end=a.index('\np1=',start)
a=a[:start]+promo+"df['promo']=make_promo(df.index)\nX['promo']=df['promo']\nfuture_index=pd.to_datetime(['2026-08-21 09:00','2026-08-21 10:00','2026-08-21 20:00','2026-08-21 21:00'])\nassert make_promo(future_index).tolist()==[0,1,1,0]"+a[end:]
codes['03-features/promo-feature']=a
project='''df=make(s)
X,y=df.drop(columns='y'),df['y']
train=df.index<'2026-07-01'
valid=(df.index>='2026-07-01')&(df.index<'2026-08-01')
test=df.index>='2026-08-01'
'''
codes['05-project/split']=common+project+"sizes={'train':int(train.sum()),'valid':int(valid.sum()),'test':int(test.sum())}"
codes['05-project/baseline']='import numpy as np\n'+err+'''valid_score=valid&(y.index<'2026-07-31 20:00')&y.notna()
rmse_base=round(error(y[valid_score],df.loc[valid_score,'mean4w']),3)
base_meets=bool(rmse_base<=4.3)
'''
codes['05-project/select']='import numpy as np\n'+prior['05-project/select']['code'].replace("fit=train&(y.index<'2026-06-30 20:00')&y.notna()","fit_mask=train&(y.index<'2026-06-30 20:00')&y.notna()\nvalid_score=valid&(y.index<'2026-07-31 20:00')&y.notna()").replace('X[fit],y[fit]','X[fit_mask],y[fit_mask]').replace('X[valid]','X[valid_score]').replace('y[valid]','y[valid_score]')
grid=prior['05-project/grid']['code'].replace('TimeSeriesSplit(n_splits=3)','TimeSeriesSplit(n_splits=3,gap=28)')
grid=grid[:grid.index('\nrmse_test_grid=')]
codes['05-project/grid']='import numpy as np\n'+grid
for t in ['final','staffing','quantile']:
 codes['05-project/'+t]='import numpy as np\n'+prior['05-project/'+t]['code']
expects={
'03-features/leak-test':'Два разнонаправленных опыта по всему хвосту; prev не меняется, текущий/future/future-difference обнаруживаются; NaN==NaN.',
'03-features/promo-feature':'Пустая будущая сетка9/10/20/21 августа21 →0/1/1/0; четыре июльских RMSE, акция11ч.',
'05-project/split':'valid744/test744; принадлежность месяцу отдельно от доступности fit/score.',
'05-project/baseline':'740 доступных июльских часов, rmse_base в заказах/час; август не смотрю.',
'05-project/select':'fit не позже30июня19:00; score740 не позже31июля19:00;4 RMSE, choose best на них.',
'05-project/grid':'6 кандидатов×3фолда,gap28;только доступный март–июль;best_params2ключа,cv_rmse положителен;без августа.',
'05-project/final':'fit не позже31июля19:00;744 прогноза>=0,meets=RMSE<=4.3 И лучше Augustbaseline.',
'05-project/staffing':'needed744 с минимум1; сравнение только496 рабочих часов; выданное ночное расписание должно иметь0.',
'05-project/quantile':'fit до31июля19:00;all coverage744/work coverage496,short/extra/deficit отдельно,цены3:1 зафиксированы.',
}
choices={'02-decompose/quiz/1':(4,'Высокий lag24 — суточный ритм, не доказательство стационарности.'),'05-project/quiz/1':(1,'Недостаток дороже избытка; квантиль не гарантирует лучшую RMSE.')}
cs=[2,2,4,3,4,4,4,4,4,4,2,1,1]
meanings=['Суммирует часы за сутки','Тренд+сезонность+остаток','Постоянное среднее,ковариация от лага','Кандидаты лаги1/24/168','shift1 перед rolling24','Лаги известны к выпуску','Обучение прошлое,проверка будущее','Выигрыш над дешёвым baseline','48/168 доступны на весь день','Сумма ошибок/общий спрос;ноль суммы не определён','Август после фиксации без настройки','RMSE симметрична,дефицит направлен','Цена сотрудника vs ущерб очереди4']
for i,(c,e) in enumerate(zip(cs,meanings),1):choices[f'test/quiz/{i}']=(c,e)
rows={}
for target in targets:
 id=target['id'];l,t=id.split('/',1)
 if target['kind']=='task':
  r=prior[id].copy()
  r['code']=codes.get(id,r['code'])
  r['expect']=expects.get(id,r['expect'])
  r['Q1']='Самостоятельно повторить исправленную задачу '+id
  r['Q2']='Публичное условие/видимая заготовка '+l+'; полный code заменяет редактор, импорты сохранены.'
  r['Q3']=r['expect']
 else:
  c,e=choices[id]
  r=dict(question=id,choice=c,expect=e,Q1='Ответить по смыслу на '+id,Q2=f'Видны варианты в новом публичном пакете; выбираю номер{c}',Q3=e)
 rows.setdefault(l,[]).append(r)
for l,rs in rows.items():
 p=D/(l+'.input.jsonl')
 if p.exists():raise RuntimeError('input already exists')
 p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs))
print({l:len(rs) for l,rs in rows.items()},'total',sum(map(len,rows.values())))
