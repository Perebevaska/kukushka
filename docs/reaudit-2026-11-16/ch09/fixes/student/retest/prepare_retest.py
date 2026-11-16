from pathlib import Path
import json,re
BASE=Path('/private/tmp/kuch09round/student-retest')
OUT=Path(__file__).parent
OLD=OUT/'../../../student'
TIMER='''import time
def best_time(f, repeats=5):
    times=[]
    for _ in range(repeats):
        t0=time.perf_counter()
        f()
        times.append(time.perf_counter()-t0)
    return float(min(times))
'''
MODEL='''class MyLinearRegression(RegressorMixin, BaseEstimator):
    def fit(self, X, y):
        A=np.asarray(X,dtype=float)
        X1=np.column_stack([np.ones(len(A)),A])
        w=np.linalg.lstsq(X1,np.asarray(y,dtype=float),rcond=None)[0]
        self.intercept_,self.coef_=w[0],w[1:]
        return self
    def predict(self,X):
        return np.asarray(X,dtype=float) @ self.coef_ + self.intercept_
'''
sol={}
def set_(q,s,goal,where,expect):sol[q]=(s,goal,where,expect)
set_('01-vectors/neighbors-scale','''def nearest(A,i,k=5):
    distance=np.linalg.norm(A-A[i],axis=1)
    distance[i]=np.inf
    return np.argsort(distance)[:k].tolist()
near_raw=nearest(G,0)
near_scaled=nearest((G-G.mean(axis=0))/G.std(axis=0),0)
common=len(set(near_raw)&set(near_scaled))
dominant=["visits_90d","days_since_last","tenure_months"][int(G.std(axis=0).argmax())]''','Найти пять соседей гостя0 в двух масштабах и сохранить функцию для любого номера строки.','Новое условие прямо требует произвольные i и k; G выдан тренажёром.','Два списка без самого гостя, число совпадений и самый широкий сырой признак; nearest не привязана к0или5.')
set_('02-matrices/predict-df','''manual=X.values @ model.coef_ + model.intercept_
max_diff=float(np.abs(manual-model.predict(X)).max())
same=bool(max_diff<1e-9)''','Сверить ручной пакетный прогноз с сохранённой обученной моделью, способной ответить по новой доставке.','В условии уточнён model.predict на исходных и новых строках; fit уже в заготовке.','same=True; model не подменяю готовым массивом, новые признаки умножаются на её веса.')
set_('02b-vectorize/best-of',TIMER+'\nt_sum=best_time(lambda:sum(range(1_000_000)))','Получить минимальную длительность пяти реальных вызовов суммы.','Знакомая карточка best-of, perf_counter вокруг f().','Вернётся float минимум измерений, без подстановки константы и без догадки о секундах.')
set_('02b-vectorize/apply-col','''def fee_col(d):
    return np.where(d["amount"]>1500,0,np.where(d["items"]>=4,60,15*d["items"]))
a,t_apply=timed_call("apply",lambda table:table.apply(fee_apply,axis=1),d)
b,t_col=timed_call("col",fee_col,d)
assert np.allclose(a,b)
speedup=t_apply/t_col if t_col else None
total=int(b.sum())
print("t_apply",t_apply,"t_col",t_col,"speedup",speedup)''','Вычислить упаковку каждого заказа и измерить обе реальные операции с подтверждёнными входами и выходами.','Новый контракт timed_call в карточке apply-col даёт точные labels apply/col и аргумент d.','a и b совпадут; функция fee_col считает переданную таблицу, не замыкается на старый массив. При нуле t_col отношение None.')
set_('02b-vectorize/vectorize','''def pay_vec(km,rain):
    p=60+14*km+np.where(km>8,100,0)
    return np.where(rain,p*1.3,p)
a,t_loop=timed_call("loop",pay_loop,km,rain)
b,t_vec=timed_call("vec",pay_vec,km,rain)
same=bool(np.allclose(a,b))
speedup=t_loop/t_vec if t_vec else None
total=int(round(float(b.sum())))
print("same",same,"total",total,"t_loop",t_loop,"t_vec",t_vec,"speedup",speedup)''','Посчитать фонд выплат с дождём после дальнего бонуса и получить наблюдаемое отношение длительностей.','Новый timed_call требует labels loop/vec, функции и полные km/rain. Это новый способ подтверждения измерения после прежнего отказа helper.','same=True,total19281182 по знакомому набору; времена заранее неизвестны, ноль даст None. pay_vec использует свои аргументы и работает на другом наборе.')
set_('02b-vectorize/nearest-shop','''def nearest_vec(orders,shops):
    dist=np.column_stack([np.abs(orders-shop).sum(axis=1) for shop in shops])
    return dist.argmin(axis=1)
a,t_loop=timed_call("loop",nearest_loop,orders,shops)
b,t_vec=timed_call("vec",nearest_vec,orders,shops)
assert np.array_equal(a,b)
speedup=t_loop/t_vec if t_vec else None
load=np.bincount(b,minlength=len(shops))
busiest=int(load.argmax())
print("t_loop",t_loop,"t_vec",t_vec,"speedup",speedup)''','Распределить30000заказов по ближайшим кофейням и проверить правило ничьей.','В новом условии ничья решается меньшим номером; argmin выбирает первый столбец. Для времени указан timed_call loop/vec.','Номера совпадут с циклом, load суммируется в30000; функция пересчитает расстояния на новых orders/shops, а не вернёт старый результат.')
set_('03-normal-equation/dup-receipt','''rank=int(np.linalg.matrix_rank(A))
det_abs=round(float(abs(np.linalg.det(A))),6)
unique=bool(rank==A.shape[1])
A2=np.array([[2,1],[1,3]])
rank2=int(np.linalg.matrix_rank(A2))
prices2=np.linalg.solve(A2,np.array([590,820]))''','Отличить отсутствие единственной пары цен от отсутствия решений вообще.','Новый флаг unique и открытый пример двух допустимых пар190/210и200/190 перед карточкой.','rank1,det_abs0,uniqueFalse, хотя система совместна. После исправления rank2=2 и prices2=[190,210].')
set_('03b-own-model/my-class','''from sklearn.base import RegressorMixin,BaseEstimator
'''+MODEL+'''model=MyLinearRegression().fit(X,y)
w_all=np.r_[model.intercept_,model.coef_].round(3)
pred_new=model.predict(new).round(1)''','Получить новую доставку после обучения и сохранить точность при почти постоянном или повторном признаке.','Условие теперь требует МНК на расширенной матрице через lstsq, произвольное число признаков и новый fit.','Знакомые веса и минуты двух доставок сохранятся. На дублях lstsq выберет один вектор, прогноз корректен; повторный fit заменит старые веса, не добавит их.')
set_('03b-own-model/group-mean','''class CourierMean(RegressorMixin,BaseEstimator):
    def fit(self,X,y):
        self.means_=pd.DataFrame({"courier":X["courier"].to_numpy(),"minutes":np.asarray(y)}).groupby("courier")["minutes"].mean()
        return self
    def predict(self,X):
        return X["courier"].map(self.means_).to_numpy()
cv_courier=-cross_val_score(CourierMean(),Xc,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
cv_courier_mean=round(float(cv_courier.mean()),2)
walk_mean=round(float(CourierMean().fit(Xc,y).means_["пеший"]),1)
beats_mean=bool(cv_courier.mean()<8.24)''','Проверить средние типов курьера и оценить, выигрывает ли диспетчер у общего среднего.','Видимые Xc,y выдаёт тренажёр; использую их вместо прежнего восстановления ndarray. groupby/map описаны в теории.','Пять положительных MAE, среднее пеших и сравнение8.24. fit строит словарь из переданного y, predict использует тип каждой новой строки.')
set_('03b-own-model/class-cv',MODEL+'''cv_mine=-cross_val_score(MyLinearRegression(),X,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
cv_sklearn=-cross_val_score(LinearRegression(),X,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
same_cv=bool(np.allclose(cv_mine,cv_sklearn))
pipe=make_pipeline(StandardScaler(),MyLinearRegression()).fit(X,y)
r2_pipe=round(float(pipe.score(X,y)),4)
top_feature=X.columns[int(np.abs(pipe[-1].coef_).argmax())]''','Убедиться, что собственный lstsq-класс копируется по фолдам и работает после масштабирования.','В новой заготовке lstsq; родители RegressorMixin,BaseEstimator из раздела совместимости.','same_cv=True; r2_pipe получен настоящим score, самый большой стандартизованный вес определяет top_feature.')
set_('04-transform/attack','''P_found=np.linalg.solve(known,hidden[:3])
restored=hidden @ np.linalg.inv(P_found)
max_err=float(np.abs(restored-X).max())
leaked=bool(max_err<1e-6)''','Проверить, раскроются ли все доставки по трём независимым известным парам.','Знакомая система known@P=hidden[:3] из карточки attack.','Ошибка восстановления мала, leaked=True; повтор одной строки не заменяет независимые уравнения.')
set_('04-transform/same-quality','''a=LinearRegression().fit(X,y)
b=LinearRegression().fit(X @ P,y)
pred_x=a.predict(X)
pred_p=b.predict(X @ P)
r2_x=round(float(r2_score(y,pred_x)),4)
r2_p=round(float(r2_score(y,pred_p)),4)
max_pred_diff=float(np.abs(pred_x-pred_p).max())''','Сравнить каждый исходный прогноз и прогноз смеси в одном порядке строк.','Новое условие явно требует pred_x,pred_p, а не только итоговые оценки.','R² одинаков, max_pred_diff около машинного округления; массивы настоящие результаты обученных моделей.')
set_('05-project/key','''P=np.random.default_rng(42).normal(size=(4,4))
rank=int(np.linalg.matrix_rank(P))
invertible=bool(rank==4)
cond=round(float(np.linalg.cond(P)),1)
hidden=X @ P
restore_ok=bool(np.allclose(hidden @ np.linalg.inv(P),X))''','Проверить обратимость и численное восстановление ключа анкет.','План05 теперь не обещает универсально безопасные десятки/сотни cond, требует проверки на данных.','rank4,cond26.9,restore_ok=True на нашем наборе. Само cond не доказывает приватность.')
set_('05-project/hidden-quality','''def quality_equal(base,hidden,tol=1e-9):
    return bool(abs(base-hidden)<=tol)
hidden_model=LinearRegression().fit(X_train @ P,y_train)
r2_full=r2_score(y_test,hidden_model.predict(X_test @ P))
same=quality_equal(r2_base,r2_full)
r2_hidden=round(float(r2_full),4)''','Сравнить исходные R² до округления и иметь функцию для другого допуска в обоих порядках аргументов.','Новый quality_equal(base,hidden,tol) прямо отделён от отчётного r2_hidden.','same=True,r2_hidden0.3713; abs делает порядок безразличным. Разность чуть выше tol не пройдёт даже при одинаковом четырёхзначном округлении.')
set_('05-project/tree-hidden','''rows=[]
for depth in [3,5,8]:
    a=DecisionTreeRegressor(max_depth=depth,random_state=0).fit(X_train,y_train)
    b=DecisionTreeRegressor(max_depth=depth,random_state=0).fit(X_train @ P,y_train)
    rows.append([r2_score(y_test,a.predict(X_test)),r2_score(y_test,b.predict(X_test @ P))])
trees=pd.DataFrame(rows,index=[3,5,8],columns=["open","hidden"]).round(4)
best_open=float(trees.open.max())
best_hidden=float(trees.hidden.max())''','Проверить численно отсутствие гарантии для дерева на трёх глубинах.','Знакомый шаг6б, та же P и те же train/test.','R² исходных и скрытых признаков различатся; выбор лучшей из этих глубин на просмотренном тесте не новая независимая оценка.')
set_('05-project/attack','''known=X[:4]
P_found=np.linalg.solve(known,hidden[:4])
key_found=bool(np.allclose(P_found,P))
restored=hidden @ np.linalg.inv(P_found)
leaked=float((np.abs(restored-X)<=0.01).all(axis=1).mean())''','Проверить, действительно ли известные пары дают доступ ко всем четырём полям анкеты.','Система шага7 и уточнение, что нужны независимые пары, а не четыре копии.','key_found=True,leaked1 на знакомых первых строках. Даже отсутствие полного ключа не доказывает, что отдельное поле не раскрывается.')
# Only visible scaffolds; leave all trainer-provided objects intact.
entries=[]
for q in json.loads((BASE/'targets.json').read_text()):
 if q not in sol:continue
 lesson,task=q.split('/',1)
 block=next(b for b in re.split(r'^## task: ',(BASE/(lesson+'.md')).read_text(),flags=re.M)[1:] if b.split(' | ',1)[0]==task)
 scaffold=re.search(r'```python\n(.*?)```',block,re.S).group(1)
 if task=='best-of':scaffold=''
 elif task=='my-class':scaffold=scaffold[:scaffold.index('class MyLinearRegression')]
 elif task=='class-cv':scaffold=scaffold[:scaffold.index('class MyLinearRegression')]
 elif task=='group-mean':scaffold=scaffold[:scaffold.index('class CourierMean')]
 elif task=='hidden-quality':scaffold=scaffold[:scaffold.index('def quality_equal')]
 elif task=='neighbors-scale':scaffold=scaffold[:scaffold.index('def nearest')]
 elif task=='apply-col':scaffold=scaffold[:scaffold.index('def fee_col')]
 elif task=='vectorize':scaffold=scaffold[:scaffold.index('def pay_vec')]
 elif task=='nearest-shop':scaffold=scaffold[:scaffold.index('def nearest_vec')]
 s,goal,where,expect=sol[q]
 entries.append({'lesson':lesson,'task':task,'code':scaffold.rstrip()+'\n'+s,'expect':f'Q1: {goal} Q2: {where} Q3: {expect} Это повтор ранее освоенного, кроме прямо отмеченных новых контрактов.'})
(OUT/'practice-attempt-01.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in entries))
(OUT/'practice-before.md').write_text('\n\n'.join('## '+e['lesson']+'/'+e['task']+'\n'+e['expect'] for e in entries))
# Choices remain familiar; options are read only after the open answer is written.
questions={}
for lesson in ['04-transform','05-project','test']:
 for part in re.split(r'^Вопрос ',(BASE/(lesson+'.md')).read_text(),flags=re.M)[1:]:questions[part.split('\n',1)[0]]=part.split('\n',1)[1]
choices={'04-transform/quiz/1':3,'04-transform/quiz/2':4,'05-project/quiz/1':3}
choices.update({f'test/quiz/{i}':c for i,c in enumerate([3,2,4,2,2,4,2,4,4,3,2,4,1,4,3,1],1)})
qe=[]
for q,c in choices.items():
 selected=re.search(r'^'+str(c)+r'\. (.*)$',questions[q],re.M).group(1)
 qe.append({'question':q,'choice':c,'expect':f'Q1: Выбрать вывод: {selected} Q2: Видимый вопрос {q}; опираюсь на знакомые формулы главы и уточнённые в вопросе условия. Q3: Ожидаю принятие варианта {c}; это повтор знаний после первого прохода, а не независимое измерение первичного усвоения.'})
(OUT/'choices-attempt-01.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in qe))
(OUT/'choices-before.md').write_text('\n\n'.join('## '+e['question']+'\n'+e['expect'] for e in qe))
assert len(entries)+len(qe)==35
print('Prepared',len(entries),'practices and',len(qe),'choices; not submitted')
