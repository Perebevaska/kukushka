from pathlib import Path
import json, shutil
D=Path(__file__).parent
(D/'data').mkdir(exist_ok=True)
shutil.copy('/private/tmp/kuch12round/student/data/app_orders.csv',D/'data/app_orders.csv')
template=json.loads(Path('/private/tmp/kuch12round/student/project-template.ipynb').read_text())
cells=[]
def md(s): cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(True)})
def code(s): cells.append({'cell_type':'code','metadata':{},'source':s.splitlines(True),'execution_count':None,'outputs':[]})
md('# Завтрашняя выдача заказов: спрос и число бариста\nСамостоятельная работа по главе 12. Браузерные карточки проверяются отдельно от этого блокнота.')
code('''import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
import sys,json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sklearn
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV,TimeSeriesSplit
RANDOM_STATE=0
DATA=Path('data')
for lib in (np,pd,sklearn,matplotlib): print(lib.__name__,lib.__version__)
print(sys.version)
''')
md('''## 1. Цель
Выпуск прогноза в 20:00 сегодня на все 24 часа завтра. Последний известный час 19:00, горизонт 5–28 часов. Управляющему нужна таблица заказов и числа бариста в 07–22. Заранее фиксирую RMSE≤4.3 и лучше среднего четырёх прошлых недель. Выбор модели — июль, окончательная проверка — август. Меньшая RMSE не заменяет сравнение планов: условная цена дефицитного бариста-часа 3, избыточного 1. Это сценарий предпочтений, а не измеренные рубли.''')
md('## 2. Данные\nОдна строка — завершённый час и число заказов приложения. Проверяю индекс, полноту и нули, а не считаю ноль пропуском.')
code('''raw=pd.read_csv(DATA/'app_orders.csv',parse_dates=['datetime'])
s=raw.set_index('datetime')['orders'].sort_index()
print('shape',raw.shape,'range',s.index.min(),s.index.max())
print('NaN',s.isna().sum(),'duplicate dates',s.index.duplicated().sum(),'zeros',s.eq(0).sum())
assert s.index.is_unique and s.index.is_monotonic_increasing
assert s.index.equals(pd.date_range(s.index.min(),s.index.max(),freq='h'))
print(raw.head())
print('дневные нули',s[(s.index.hour>=8)&(s.index.hour<=20)&s.eq(0)])
''')
md('**Вывод по данным.** 4416 часовых строк за март–август. Ряд непрерывный; июньские дневные нули отмечаю как подозрительные, но факты не исправляю по будущей информации.')
md('## 3. Предобработка и доступность\nСтрою X отдельно от y. История для ориентира обязана содержать все четыре недели: иначе резерв — недельный лаг, затем прошлый доступный средний. Основное обучение после 672 часов; это честная плата за сопоставимость. В августе резерв не нужен. Календарь акций известен заранее; августовскую акцию не изобретаю.')
code('''promo_days=pd.to_datetime(['2026-04-17','2026-05-22','2026-06-19','2026-07-24'])
def build_X(history,index):
    # index включает будущий день; неизвестные y остаются NaN, не удаляются
    full_index=pd.date_range(history.index.min(),max(history.index.max(),index.max()),freq='h')
    z=history.reindex(full_index)
    f=pd.DataFrame(index=z.index)
    f['hour']=f.index.hour
    f['dow']=f.index.dayofweek
    f['weekend']=(f.dow>=5).astype(int)
    f['promo']=(f.index.normalize().isin(promo_days)&(f.index.hour>=10)&(f.index.hour<=20)).astype(int)
    for k in (48,168): f[f'lag_{k}']=z.shift(k)
    f['roll_28']=z.shift(28).rolling(24).mean()
    weeks=pd.concat([z.shift(168*k) for k in range(1,5)],axis=1)
    f['mean4w']=weeks.mean(axis=1).where(weeks.notna().all(axis=1))
    return f.reindex(index)
X=build_X(s,s.index).dropna()
y=s.reindex(X.index)
train=X.index<'2026-07-01'
valid=(X.index>='2026-07-01')&(X.index<'2026-08-01')
test=X.index>='2026-08-01'
fit_valid=train&(X.index<'2026-06-30 20:00')
fit_final=(train|valid)&(X.index<'2026-07-31 20:00')
sizes={k:int(v.sum()) for k,v in [('train',train),('valid',valid),('test',test)]}
print(sizes,'fit last',y[fit_valid].index.max(),y[fit_final].index.max())
# Выпуск первого августа из доступного префикса, без будущей цели
future=pd.date_range('2026-08-01',periods=24,freq='h')
prefix=s.loc[:'2026-07-31 19:00']
future_X=build_X(prefix,future)
assert len(future_X)==24 and future_X.notna().all().all()
print('future rows',len(future_X),'first/last',future_X.index.min(),future_X.index.max())
# Независимая порча всего неизвестного хвоста не меняет ни один признак выпуска
spoiled=s.astype(float).copy()
unknown=spoiled.index>prefix.index.max()
spoiled.loc[unknown]=np.random.default_rng(17).normal(1000,300,unknown.sum())
assert np.allclose(build_X(spoiled,future),future_X)
assert np.allclose(build_X(s,future),future_X)
# Отрицательные контрпримеры не должны проходить эту же проверку
bad=lambda z: pd.DataFrame({'current':z,'future':z.shift(-1),'future_difference':z.shift(-1)-z.shift(-2)})
assert (bad(spoiled).loc[future]!=bad(s).loc[future]).any().all()
for t in future:
    for lag in [48,168,28]: assert t-pd.Timedelta(hours=lag)<=prefix.index.max()
print('Положительный и три отрицательных теста доступности пройдены')
''')
md('**Вывод по предобработке.** Не использую неизвестный спрос ни как признак, ни как обучающую метку. Полная история четырёх недель означает начало модели 29 марта; строки 31 июля 20–23 исключены из fit первого августа. Прогноз на 1 августа содержит 24 строки без известного y.')
md('## 4. Анализ и модели\nСравню линейную регрессию и три сложности бустинга на одних июльских часах. Параметры бустинга проверю только внутри прошлого тремя временными фолдами; gap=28 дополнительно отделяет обучающие метки от начала следующего выпуска.')
code('''daily=s.resample('D').sum()
fig,ax=plt.subplots(figsize=(9,3))
daily.plot(ax=ax,label='дневной спрос')
daily.rolling(7).mean().plot(ax=ax,label='среднее 7 дней')
ax.set(title='Заказы приложения за март–август',xlabel='дата',ylabel='заказов за день')
ax.legend()
fig.tight_layout()
fig.savefig('native-demand.png')
plt.show()
def error(a,b): return float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))
models={'linear':LinearRegression(),'hgb':HistGradientBoostingRegressor(random_state=RANDOM_STATE),'hgb_depth3':HistGradientBoostingRegressor(max_depth=3,random_state=RANDOM_STATE),'hgb_l2':HistGradientBoostingRegressor(l2_regularization=1,random_state=RANDOM_STATE)}
valid_rmse={}
for name,m in models.items():
    valid_rmse[name]=error(y[valid],np.clip(m.fit(X[fit_valid],y[fit_valid]).predict(X[valid]),0,None))
best=min(valid_rmse,key=valid_rmse.get)
print('July validation',valid_rmse,'winner',best)
gs=GridSearchCV(HistGradientBoostingRegressor(random_state=RANDOM_STATE),{'max_depth':[2,3,None],'learning_rate':[.05,.1]},cv=TimeSeriesSplit(n_splits=3,gap=28),scoring='neg_root_mean_squared_error',n_jobs=1)
gs.fit(X[fit_final],y[fit_final])
best_params=gs.best_params_
print('best params',best_params,'CV RMSE',-gs.best_score_)
# Фиксация спецификации до итогового расчёта
spec={'cutoff':'2026-07-31 19:00','columns':X.columns.tolist(),'params':best_params,'random_state':RANDOM_STATE,'history_weeks':4,'cost_deficit':3,'cost_extra':1,'quantile':.8}
Path('native-model-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
model=gs.best_estimator_
pred_test=np.clip(model.predict(X[test]),0,None)
rmse_base=error(y[test],X.loc[test,'mean4w'])
rmse_final=error(y[test],pred_test)
meets=bool(rmse_final<=4.3 and rmse_final<rmse_base)
print('August baseline',rmse_base,'model',rmse_final,'meets',meets)
# Повторное получение первого выпуска только по доступному префиксу
issued=model.predict(future_X)
assert np.allclose(np.clip(issued,0,None),pred_test[:24])
''')
md('**Вывод по анализу.** Календарь и доступная история отражают суточный ритм и рост. Конкретные июльские и августовские показатели записаны в выводе выше; финальные числа добавлю в заключение после исполнения, без изменения спецификации по августу.')
md('## 5. Штат и рекомендация\nОдин человек обслуживает 6 заказов в час; минимум один в 07–22. Сравниваю исходное покрытие спроса и нехватку после ceil отдельно. Квантиль .8 обучается с уже выбранными параметрами; его фактическое покрытие проверяю, а не объявляю равным 80%.')
code('''yt=y[test]
work=(yt.index.hour>=7)&(yt.index.hour<=22)
needed=np.maximum(1,np.ceil(yt.to_numpy()/6)).astype(int)
qmodel=HistGradientBoostingRegressor(loss='quantile',quantile=.8,random_state=RANDOM_STATE,**best_params).fit(X[fit_final],y[fit_final])
pq=np.clip(qmodel.predict(X[test]),0,None)
plans={}
for name,p in [('модель',pred_test),('ориентир',X.loc[test,'mean4w'].to_numpy()),('квантиль',pq)]:
    plan=np.maximum(1,np.ceil(p/6)).astype(int)
    delta=(plan-needed)[work]
    short=float(np.mean(delta<0));extra=int(np.maximum(delta,0).sum());deficit=int(np.maximum(-delta,0).sum())
    plans[name]={'short':short,'extra':extra,'deficit':deficit,'coverage_work':float(np.mean(p[work]>=yt.to_numpy()[work])),'cost':3*deficit+extra}
print(pd.DataFrame(plans).T)
print('Все часы: quantile coverage',np.mean(pq>=yt.to_numpy()))
predictions=pd.DataFrame({'fact':yt,'model':pred_test,'baseline':X.loc[test,'mean4w'],'quantile':pq,'needed':needed,'work':work})
for name,p in [('model',pred_test),('baseline',X.loc[test,'mean4w']),('quantile',pq)]: predictions['staff_'+name]=np.where(work,np.maximum(1,np.ceil(np.asarray(p)/6)),0).astype(int)
predictions.to_csv('native-august-predictions.csv')
future_plan=pd.DataFrame({'orders':np.clip(issued,0,None)},index=future)
future_plan['staff']=np.where((future.hour>=7)&(future.hour<=22),np.maximum(1,np.ceil(future_plan.orders/6)),0).astype(int)
future_plan.to_csv('native-issued-2026-08-01.csv')
metrics={'sizes':sizes,'valid_rmse':valid_rmse,'best':best,'best_params':best_params,'cv_rmse':float(-gs.best_score_),'rmse_base':rmse_base,'rmse_final':rmse_final,'meets':meets,'plans':plans,'coverage_q':float(np.mean(pq>=yt.to_numpy())),'work_hours':int(work.sum())}
Path('native-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
print(future_plan)
''')
md('''**Вывод для руководителя.** Сравнение планов и итоговое требование выводятся выше. Обсуждаю стоимость ошибок до выбора плана, а не приравниваю точность спроса к качеству штата. Август — одна проверка на исторических данных; здесь нет фактического эксперимента с очередями, стоимостью человека и сезонностью сентября. Дальше нужен пилот: измерить ущерб очереди и цену резервного сотрудника, затем проверить покрытие и дефицит на следующем периоде. Ночные сотрудники в итоговой таблице равны нулю согласно постановке.''')
template['cells']=cells
(D/'project-template.ipynb').write_text(json.dumps(template,ensure_ascii=False,indent=1))
