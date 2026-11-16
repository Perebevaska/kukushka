from pathlib import Path
import json,ast
ROOT=Path('/Users/dmitriikormin/Documents/Projects/ds-course')
old=ROOT/'docs/reaudit-2026-11-16/ch08/student'
out=ROOT/'docs/reaudit-2026-11-16/ch08/fixes/student/retest'
# Read only strings authored in the first pass; no course checker source is opened.
m=ast.parse((old/'final_cards.py').read_text())
ns={}
for node in m.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
  try:ns[node.targets[0].id]=eval(compile(ast.Expression(node.value),'own source','eval'),{},ns)
  except Exception:pass
assembly=ns['assembly'];modelsetup=ns['modelsetup'];curvefun=ns['curvefun']
base=assembly+modelsetup
frozen='''best_t=.22  # Same policy frozen in my first independent-control notebook.
'''
final='''final=lr_model().fit(X,y)
rest=data[(~data.guest_id.isin(pilot.guest_id))&(data.orders_n>0)&(data.reg_date<'2026-06-01')].copy()
rest['p']=final.predict_proba(rest[num+cat])[:,1]
rest['send']=rest.p>best_t
ctrl=pilot[pilot.group_name=='контроль'].merge(data,on='guest_id',validate='one_to_one')
'''
code={}
code['fp-eda']=assembly+'''from sklearn.model_selection import train_test_split
train_off,_=train_test_split(off,test_size=.25,random_state=42,stratify=off.bought)
off=train_off
labels=['до 0.2','0.2–0.5','выше 0.5']
groups=pd.cut(off.morning_share,[0,.2,.5,1],include_lowest=True,labels=labels)
by_morning=off.groupby(groups,observed=True).bought.mean().round(3)
by_source=off.groupby('source').bought.mean().round(3)
by_city=off.groupby('city').bought.mean().round(3)
n_top=int((groups=='выше 0.5').sum())
lift_top=round(off.loc[groups=='выше 0.5','bought'].mean()/off.bought.mean(),2)
'''
code['fp-money']=base+frozen+curvefun+'''best=lr_model()
oof=cross_val_predict(best,X_train,y_train,cv=cv,method='predict_proba',n_jobs=1)[:,1]
curve=profit_curve(oof,y_train)
best.fit(X_train,y_train)
ctrl=pilot[pilot.group_name=='контроль'].merge(data,on='guest_id',validate='one_to_one')
p_ctrl=best.predict_proba(ctrl[num+cat])[:,1]
rows=[]
for _,r in curve.iterrows():
    cs=p_ctrl>r.threshold
    rate=ctrl.loc[cs,'bought'].mean() if cs.any() else np.nan
    rows.append({'threshold':r.threshold,'control_n':int(cs.sum()),'organic_share':rate,'margin':r.profit-1600*r.sent*rate})
incr=pd.DataFrame(rows)
assert incr.loc[incr.threshold==best_t,'control_n'].iloc[0]>0
assert incr.loc[incr.threshold==best_t,'margin'].iloc[0]>=0
p=best.predict_proba(X_test)[:,1]
send=p>best_t
test_sent=int(send.sum())
test_buyers=int(y_test[send].sum())
test_profit=1600*test_buyers-150*test_sent
all_profit=1600*int(y_test.sum())-150*len(y_test)
'''
code['fp-portrait']=base+frozen+final+'''n_rest=len(rest)
n_send=int(rest.send.sum())
cols=['orders_per_week','morning_share','delivery_share','recency_days','coffee_share','app_sessions']
portrait=rest.groupby('send')[cols].mean().round(3)
app_share=round((rest.loc[rest.send,'source']=='приложение').mean(),3)
'''
code['fp-groups']=base+frozen+'''p=cross_val_predict(lr_model(),X,y,cv=cv,method='predict_proba',n_jobs=1)[:,1]
off['send']=p>best_t
sel_by_city=off.groupby('city').send.mean().round(3)
recall_by_city=off[off.bought==1].groupby('city').send.mean().round(3)
weak_city=recall_by_city.idxmin()
age=2026-off.birth_year.mask(off.birth_year==1900)
off['age_group']=pd.cut(age,[0,29,49,200],labels=['до 30','30–49','50+'])
recall_by_age=off[off.bought==1].groupby('age_group',observed=True).send.mean().round(3)
'''
code['fp-honest']=base+frozen+final+'''best_t_incr=best_t
n_send=int(rest.send.sum())
pc=final.predict_proba(ctrl[num+cat])[:,1]
cs=pc>best_t
organic_raw=ctrl.loc[cs,'bought'].mean() if cs.any() else np.nan
organic=round(organic_raw,3)
buyers_raw=rest.loc[rest.send,'p'].sum()
exp_buyers=round(buyers_raw,1)
naive_profit=round(1600*buyers_raw-150*n_send)
honest_profit=round(1600*(buyers_raw-organic_raw*n_send)-150*n_send) if cs.any() else np.nan
honest_all=round(1600*(rest.p.sum()-ctrl.bought.mean()*len(rest))-150*len(rest))
'''
expect={
'fp-eda':('Описать связь покупок с утром, источником регистрации и городом на1350обучающих ID, сохранив450тестовыхзакрытыми.','Вновомшаге2нашёлуказаниеразделитьoffпередEDA; первымдействиемtrain_test_splitсамойтаблицыгостейвтомжепорядке.','РазмерEDA1350; верхняяутренняягруппаконвертируетсяоколо26.3%,непрежние27.3%пополномупилоту.'),
'fp-money':('Зафиксироватьвыгодныйпорогподополнительноймарже,аиз450тестовыхполучателейузнатьмаржупослерасходов.','Вновойкарточкепрямопросятincrсчисленностьюконтроляиорганическойдолей. Строюполнуюконтрольнуюпоправку,переношусвойранееобоснованныйпорог.22,несчитаюновыйпобедительпотесту.','best_t=.22снаблюдаемымконтролеминеотрицательнойдоп.маржой; test_sentожидаю70,денежныеполяtest_profit/all_profitваловые,этоещёнеэффект.'),
'fp-portrait':('Датьмаркетингупортретреальновыбранныхисторическихадресатоввобластипилота.','Вшаге6/условиипоявилосьreg_date<2026-06-01;добавляюэтотфильтрдоpredictиприменяюединый.22.','Кандидатовбудетменьшепрежних1987;каждыйIDвнепилота,сзаказомирегистрациейдо1июня. Портретибюджетзависятоттойжемаски.'),
'fp-groups':('Диагностироватьраспределениеотбораиполнотупокупателейпоcity/ageдлязафиксированнойполитики.','Вусловиитеперьявноуказаныpd.cutграницы0,29,49,200. ИспользуюихиOOFвсех1800,неподбираюновыегрупповыепорогипослерезультата.','Неизвестныйвозраствнегрупп;среднийselectedиrecallразныепоказатели;weak_cityпоrecall,порог.22тотже.'),
'fp-honest':('Сопоставитьрассылкувыбранным,всемподходящимкандидатамиотказврубляхдополнительноймаржи3месяцев.','Изновойкарточкипереношуbest_tизfp-money,алиасbest_t_incr=.22;отдельноподсчитываюкупивших/числоконтролейиработаюснеокруглённойорганикой.','naive_profitвышеhonest_profitнасуммумаржиорганическихпокупок;кандидатыимеютreg<June1,тотжесписокдлярасхода/письма. ПустойконтрольозначаетNaN,не0.')}
rows=[]
with (out/'walkthrough.md').open('a') as f:
 for task,s in code.items():
  q1,q2,q3=expect[task]
  r={'lesson':'07-final-project','task':task,'code':s,'expect':q3};rows.append(r)
  f.write('\n### S08-07-final-project/'+task+' — retest до сдачи\nQ1: '+q1+'\nQ2: '+q2+'\nQ3: '+q3+'\nQ4: Ещё не отправлено; CPU-окно у координатора.\n')
(out/'final-prepared.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
