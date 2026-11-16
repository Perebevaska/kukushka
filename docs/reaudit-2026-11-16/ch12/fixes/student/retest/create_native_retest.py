from pathlib import Path
import json,shutil
D=Path(__file__).parent
PUB=Path('/private/tmp/kuch12round/student-retest')
(D/'data').mkdir(exist_ok=True)
shutil.copy(PUB/'data/app_orders.csv',D/'data/app_orders.csv')
spec=json.loads((PUB/'own-previous-model-spec.json').read_text())
spec['family']='HistGradientBoostingRegressor'
spec['source_round']='original student FREEZE; fixed before retest calculations'
spec['new_public_calendar']=['2026-04-17','2026-05-22','2026-06-19','2026-07-24','2026-08-21']
(D/'own-fixed-before-run.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
nb=json.loads((PUB/'own-previous-project.ipynb').read_text())
for c in nb['cells']:
 if c['cell_type']=='code':c['outputs']=[];c['execution_count']=None
srcs=[''.join(c['source']) for c in nb['cells']]
for i,c in enumerate(nb['cells']):
 s=srcs[i]
 if c['cell_type']=='markdown':
  if s.startswith('# Завтрашняя'):s='# Исправленный пересчёт: доступный календарь и выпуск в20:00\nНовая копия своей прежней работы. Прежний отрицательный результат сохраняется. Август уже известен: это механическое исправление входа/отсечек, не новый слепой тест.'
  elif s.startswith('## 1.'):s='''## 1. Цель и фиксация
Момент выпуска20:00, завершённая метка19:00;24часа завтра. Фиксирую прежние HGB,learning_rate.05,max_depth3,random_state0,полные4недели,quantile.8,цены3/1,мощность6. Новый публичный календарь добавляет21августа10–20. Июльскую оценку ограничиваю740ответами, доступными31июля20:00. Семейство/параметры заново не выбираю; требование августа≤4.3 и лучше mean4w остаётся.'''
  elif s.startswith('## 3.'):s='''## 3. Доступность и новая информация
Сохраняю полные4недели: первые672часа не используются для модели. Календарь маркетинга — заранее известный вход, проверенный до чтения фактов. Пустой будущий y не удаляется вместе со строкой. В промежутке от20:00 до полуночи остаются неизвестные позиции регулярной сетки. При недостатке4недель модель не выпускается; до её готовности контрольный резерв — недельный лаг, затем среднее только известного префикса; в августе резерв не нужен.'''
  elif s.startswith('**Вывод по предобработке'):s='''**Вывод по предобработке.** Начало модели29марта сохраняется. Для выбора июльский fit заканчивается30июня19:00; июльский score заканчивается31июля19:00 и имеет740строк. Финальный fit имеет ту же последнюю доступную метку31июля19:00. Текущий интервал20–21 и позднейшие факты неизвестны в момент выпуска; будущие партии сохраняются по24строки до присоединения y.'''
  elif s.startswith('## 4.'):s='''## 4. Исправленный пересчёт без нового подбора
Показываю июльскую ошибку только прежнего выбранного семейства/параметров. GridSearch заново не запускаю. Финальный fit выполняется на доступном марте–июле. Августовские выпуски строю из отдельного префикса каждого дня, с фиксированной обученной моделью; затем присоединяю факты.'''
  elif s.startswith('**Вывод по анализу'):s='''**Вывод по анализу.** Входы исправлены механически: полный опубликованный календарь и доступная июльская оценка740. Значения нового результата напечатаются после выполнения. Менять историю, семейство и параметры по августовскому результату не буду.'''
  elif s.startswith('**Вывод для руководителя'):s='''**Вывод для руководителя.** Новый результат и его отличие от исходного отрицательного опыта будут добавлены после исполнения. Проверяю ошибку спроса, покрытие, дефицит и избыток отдельно. Это повтор уже увиденного августа, причинный эффект кадрового плана на очередь не измерен.'''
 else:
  if 'RANDOM_STATE=0' in s:
   s += '''\nspec=json.loads(Path('own-fixed-before-run.json').read_text())
assert spec['params']=={'learning_rate':.05,'max_depth':3}
assert spec['history_weeks']==4 and spec['quantile']==.8
best_params=spec['params'].copy()
promo_days=pd.to_datetime(spec['new_public_calendar'])
def make_promo(index):
    return pd.Series((index.normalize().isin(promo_days)&(index.hour>=10)&(index.hour<=20)).astype(int),index=index)
future_calendar_index=pd.to_datetime(['2026-08-21 09:00','2026-08-21 10:00','2026-08-21 20:00','2026-08-21 21:00'])
future_calendar=pd.DataFrame({'promo':make_promo(future_calendar_index)})
assert future_calendar['promo'].tolist()==[0,1,1,0]
assert 'y' not in future_calendar
future_calendar.to_csv('future-calendar-before-orders.csv')
print('Календарь без y перед чтением заказов',future_calendar)
'''
  if s.startswith('promo_days='):
   s=s[s.index('def build_X'):]
   s=s.replace("f['promo']=(f.index.normalize().isin(promo_days)&(f.index.hour>=10)&(f.index.hour<=20)).astype(int)","f['promo']=make_promo(f.index)")
   s=s.replace("fit_valid=train&(X.index<'2026-06-30 20:00')","valid_score=valid&(X.index<'2026-07-31 20:00')\nassert valid_score.sum()==740\nfit_valid=train&(X.index<'2026-06-30 20:00')")
   s=s.replace("print('Положительный и три отрицательных теста доступности пройдены')",'''# Два знака и порча текущего20:00 плюс всего неизвестного хвоста
for sign in (1,-1):
    z=s.astype(float).copy()
    n=unknown.sum()
    z.loc[unknown]+=sign*(1000+np.arange(n)**2+19*np.arange(n))
    assert np.allclose(build_X(z,future),future_X)
    assert (bad(z).loc[future]!=bad(s).loc[future]).any().all()
assert prefix.index.max()==pd.Timestamp('2026-07-31 19:00')
assert pd.Timestamp('2026-07-31 20:00') not in prefix.index
print('Префикс/полная история, текущие/будущие неизвестные, два знака и отрицательные контроли пройдены')''')
  if s.startswith('daily='):
   s=s[:s.index("models={'linear'")]+'''fixed_validation=HistGradientBoostingRegressor(random_state=RANDOM_STATE,**best_params).fit(X[fit_valid],y[fit_valid])
valid_rmse_fixed=error(y[valid_score],np.clip(fixed_validation.predict(X[valid_score]),0,None))
print('July score740 fixed params',valid_rmse_fixed)
model=HistGradientBoostingRegressor(random_state=RANDOM_STATE,**best_params).fit(X[fit_final],y[fit_final])
qmodel=HistGradientBoostingRegressor(loss='quantile',quantile=.8,random_state=RANDOM_STATE,**best_params).fit(X[fit_final],y[fit_final])
# Каждый дневной выпуск сохраняется без y до присоединения фактов
Path('issued').mkdir(exist_ok=True)
issued_frames=[]
for day in pd.date_range('2026-08-01','2026-08-31',freq='D'):
    cutoff=day-pd.Timedelta(hours=5)
    index=pd.date_range(day,periods=24,freq='h')
    history=s.loc[:cutoff]
    assert history.index.max()==cutoff
    release_X=build_X(history,index)
    assert len(release_X)==24 and release_X.notna().all().all()
    assert np.allclose(release_X,X.loc[index])
    frame=pd.DataFrame({'model':np.clip(model.predict(release_X),0,None),'quantile':np.clip(qmodel.predict(release_X),0,None),'baseline':release_X.mean4w,'cutoff':cutoff,'issue':day-pd.Timedelta(hours=4)},index=index)
    assert 'fact' not in frame.columns
    frame.to_csv(Path('issued')/(day.strftime('%Y-%m-%d')+'.csv'))
    issued_frames.append(frame)
issued_forecasts=pd.concat(issued_frames)
assert len(issued_forecasts)==744 and issued_forecasts.index.is_unique
# Факты присоединяются только к уже сохранённым выпускам
scored=issued_forecasts.join(s.rename('fact'))
pred_test=scored.model.to_numpy()
pq=scored['quantile'].to_numpy()
rmse_base=error(scored.fact,scored.baseline)
rmse_final=error(scored.fact,pred_test)
meets=bool(rmse_final<=4.3 and rmse_final<rmse_base)
print('August baseline/model/meets',rmse_base,rmse_final,meets)
'''
  if s.startswith('yt=y[test]'):
   s=s.replace("qmodel=HistGradientBoostingRegressor(loss='quantile',quantile=.8,random_state=RANDOM_STATE,**best_params).fit(X[fit_final],y[fit_final])\npq=np.clip(qmodel.predict(X[test]),0,None)\n",'')
   s=s.replace("future_plan=pd.DataFrame({'orders':np.clip(issued,0,None)},index=future)","future_plan=pd.DataFrame({'orders':scored.loc[future,'model']},index=future)")
   start=s.index("metrics={'sizes'")
   s=s[:start]+'''metrics={'sizes':sizes,'score_hours':int(valid_score.sum()),'valid_rmse_fixed':valid_rmse_fixed,'best_params':best_params,'rmse_base':rmse_base,'rmse_final':rmse_final,'meets':meets,'plans':plans,'coverage_q':float(np.mean(pq>=yt.to_numpy())),'work_hours':int(work.sum())}
Path('native-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
print(future_plan)
# Открытый перенос и кадровые границы проверяются самостоятельно
def staff(a,capacity): return np.maximum(1,np.ceil(np.asarray(a)/capacity)).astype(int)
assert staff([0],6).tolist()==[1]
assert np.where([False],staff([0],6),0).tolist()==[0]
assert staff([8,11],6).tolist()==[2,2]
assert staff([6,7],6).tolist()==[1,2]
assert staff([5,6],5).tolist()==[1,2]
assert staff([5,6],6).tolist()==[1,1]
transfer=[]
for capacity,D,E in [(6,300,100),(5,180,100)]:
    demand=np.array([13,0,10])
    need=staff(demand,capacity)
    for count in [2,3]:
        delta=count-need
        deficit=int(np.maximum(-delta,0).sum())
        extra=int(np.maximum(delta,0).sum())
        transfer.append({'capacity':capacity,'D':D,'E':E,'count':count,'needed':need.tolist(),'deficit':deficit,'extra':extra,'cost':D*deficit+E*extra})
assert [r['cost'] for r in transfer]==[400,300,280,300]
Path('own-transfer-results.json').write_text(json.dumps(transfer,ensure_ascii=False,indent=2))
print('Свой перенос',transfer)
'''
 c['source']=s.splitlines(True)
(D/'own-native-input-correction.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
print('Prepared new notebook; no ML executed')
