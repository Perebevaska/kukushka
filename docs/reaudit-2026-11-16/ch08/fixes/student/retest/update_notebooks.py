from pathlib import Path
import json
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch08/student')
p=root/'final-project.ipynb';n=json.loads(p.read_text())
def src(c):return ''.join(c['source'])
def setsrc(c,s):c['source']=s.splitlines(True)
# Preserve all original content in archived copies managed by the coordinator; this changes current submission only.
for c in n['cells']:
 s=src(c)
 if c['cell_type']=='markdown':
  s=s.replace('## 2. Данные и 3. Предобработка','## 2. Данные\n\nОдна строка — гость с картой. Пилот включает только регистрацию до 1 июня и заказ до 1 июля. Июньские регистрации требуют отдельного эксперимента.\n\n## 3. Предобработка')
  s=s.replace('Возрастные границы <30/30–49/50+ определены мной, поскольку в пакете они не заданы численно.','Возрастные границы теперь явно заданы новой редакцией: pd.cut(age,[0,29,49,200]); неизвестный возраст вне групп.')
  s=s.replace('Из контроля заранее отложена треть для независимого финального сравнения.','Из контроля заранее отложена треть для независимого финального сравнения. Пилот применим к регистрациям до 1 июня с заказом до 1 июля. В редакторском повторе исправляю порядок EDA и применимость списка; модель, прежнее правило мощности и протокол .22 сохраняются. Те же исторические holdout-исходы уже были просмотрены в первом проходе: повторное выполнение не является новой независимой валидацией.')
 elif "con=sqlite3.connect(DATA/'final1.db')" in s:
  start=s.index('agg=pd.read_sql_query(')
  end=s.index('\ncoffee=pd.read_sql_query',start)
  q=s[start:end].replace('agg=pd.read_sql_query(', 'return pd.read_sql_query(').replace('COUNT(*) AS orders_n,','COUNT(*) AS orders_n,SUM(amount) AS amount_sum,').replace('con,params=params)','connection,params={\'cutoff\':cutoff})')
  fn='def order_aggregates(connection,cutoff):\n'+''.join('    '+line+'\n' for line in q.splitlines())+'agg=order_aggregates(con,CUTOFF)'
  s=s[:start]+fn+s[end:]
  s+='''
train_off,test_off=train_test_split(off,test_size=.25,random_state=42,stratify=off.bought)
assert set(train_off.guest_id).isdisjoint(test_off.guest_id)
assert len(train_off)==1350 and len(test_off)==450
assert off.reg_date.lt('2026-06-01').all() and off.orders_n.gt(0).all()
pd.DataFrame({'guest_id':train_off.guest_id,'role':'offer_train'}).to_csv(OUT/'offer-train-ids.csv',index=False)
pd.DataFrame({'guest_id':test_off.guest_id,'role':'offer_test'}).to_csv(OUT/'offer-test-ids.csv',index=False)
'''
 elif s.startswith('groups=pd.cut(off.morning_share'):
  # Only training ID slices used for all target-conditioned EDA.
  s=s.replace('groups=pd.cut(off.morning_share','groups=pd.cut(train_off.morning_share').replace("off.groupby(groups", "train_off.groupby(groups").replace("off.groupby('source')", "train_off.groupby('source')").replace("off.groupby('city')", "train_off.groupby('city')").replace('off.loc[off.bought==bought,col]','train_off.loc[train_off.bought==bought,col]')
  s=s.replace("leak_off=off.merge(leak", "leak_off=train_off.merge(leak")
  s=s.replace('roc_auc_score(off.bought,off.orders_per_week)','roc_auc_score(train_off.bought,train_off.orders_per_week)')
  s=s.replace("    ax.set_title(col);ax.legend(title='bought')","    ax.set_title(col);ax.set_xlabel(col);ax.set_ylabel('плотность');ax.legend(title='bought')")
  s=s.replace("print('Диагностика утечки'", "print('Диагностика известной утечки только на обучении'")
  s=s.replace('весь пилот предложения — {conv_offer:.1%}', 'обучение — {train_off.bought.mean():.1%}')
  s+='''
qgroups=pd.qcut(train_off.orders_per_week,4,duplicates='drop')
by_frequency=train_off.groupby(qgroups,observed=True).bought.agg(['size','mean'])
display(by_frequency.round(3))
by_morning.to_csv(OUT/'eda-train-morning.csv')
by_source.to_csv(OUT/'eda-train-source.csv')
by_city.to_csv(OUT/'eda-train-city.csv')
by_frequency.to_csv(OUT/'eda-train-frequency.csv')
'''
 elif s.startswith("num=['orders_n'"):
  s=s.replace('X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)',"X_train,X_test=train_off[num+cat],test_off[num+cat]\ny_train,y_test=train_off.bought,test_off.bought")
 elif s.startswith('# Split the 600 controls'):
  s=s.replace("ctrl_train,ctrl_test=train_test_split(ctrl_all,test_size=1/3,random_state=42,stratify=ctrl_all.bought)","ctrl_train,ctrl_test=train_test_split(ctrl_all,test_size=1/3,random_state=42,stratify=ctrl_all.bought)\nassert set(ctrl_train.guest_id).isdisjoint(ctrl_test.guest_id)\npd.DataFrame({'guest_id':ctrl_train.guest_id,'role':'control_train'}).to_csv(OUT/'control-train-ids.csv',index=False)\npd.DataFrame({'guest_id':ctrl_test.guest_id,'role':'control_test'}).to_csv(OUT/'control-test-ids.csv',index=False)")
  s=s.replace("curve.to_csv(OUT/'policy-curve.csv',index=False)","curve.to_csv(OUT/'policy-curve.csv',index=False)\n(OUT/'frozen-policy.json').write_text(json.dumps({'threshold':best_t,'training_contacts_limit':300,'training_candidates':1350,'min_selected_controls':20,'contact_cost':C,'cutoff':CUTOFF,'eligible_registration_before':'2026-06-01'},ensure_ascii=False,indent=2))")
 elif s.startswith('# Refit the fixed chosen pipeline'):
  s=s.replace("(~data.guest_id.isin(pilot.guest_id))&(data.orders_n>0)","(~data.guest_id.isin(pilot.guest_id))&(data.orders_n>0)&(data.reg_date<'2026-06-01')")
  s=s.replace("right=False,labels=['до 30','30–49','50+']", "labels=['до 30','30–49','50+']").replace("[0,30,50,200]", "[0,29,49,200]")
  s=s.replace("output.to_csv(OUT/'candidate-decisions.csv',index=False)","assert output.guest_id.is_unique\nassert set(output.guest_id)==set(rest.guest_id)\nassert rest.reg_date.lt('2026-06-01').all() and rest.orders_n.gt(0).all()\nassert int(output.send.sum())==n_send and C*n_send<=C*cap\noutput.to_csv(OUT/'candidate-decisions.csv',index=False)")
  s=s.replace("'median_frequency':float(selected.orders_per_week.median()),'versions':versions", "'median_frequency':float(selected.orders_per_week.median()),'control_selected_n':int(sc.sum()),'control_selected_buyers':int(ctrl_all.loc[sc,'bought'].sum()),'eligible_reg_before':'2026-06-01','versions':versions")
  s=s.replace("'контакты',", "'контакты',")
  s=s.replace("print('Кандидаты',len(rest)","print('Контроль финальной рекомендации: купили / выбранных',int(ctrl_all.loc[sc,'bought'].sum()),'/',int(sc.sum()))\nprint('Кандидаты',len(rest)")
  s=s.replace('**Рекомендация на историческую дату {CUTOFF}.**','**Рекомендация на историческую дату {CUTOFF} для регистраций до 1 июня.**')
  s+='''
# One ID mask drives list, portrait, and letter economics.
selected_ids=set(output.loc[output.send,'guest_id'])
assert selected_ids==set(selected.guest_id)
assert len(selected_ids)==n_send
assert np.isclose(C*len(selected_ids),summary['contact_cost'])
print('Проверки применимости/ID/маски/затрат: PASS')
display(Markdown(f'**Перенос на контроль.** В отобранном контроле {int(ctrl_all.loc[sc,"bought"].sum())} покупок из {int(sc.sum())}, органическая доля {organic_rate:.3f}. Прогноз прибыли относится к исходной области пилота; июньские регистрации не включены и требуют отдельной проверки.'))
'''
 setsrc(c,s)
 if c['cell_type']=='code':c['execution_count']=None;c['outputs']=[]
# Mini-SQL test uses the same function as feature assembly.
mini='''# Expected before this run: count=1 and amount_sum=400 both before and after the July insert.
small=sqlite3.connect(':memory:')
small.execute('CREATE TABLE orders (guest_id TEXT,ordered_at TEXT,amount REAL,channel TEXT,shop_id TEXT)')
small.execute("INSERT INTO orders VALUES ('G1','2026-06-30 12:00:00',400,'зал','S1')")
before=order_aggregates(small,CUTOFF)
small.execute("INSERT INTO orders VALUES ('G1','2026-07-01 00:00:00',9000,'зал','S1')")
after=order_aggregates(small,CUTOFF)
small.close()
assert before.loc[0,'orders_n']==1 and before.loc[0,'amount_sum']==400
pd.testing.assert_frame_equal(before,after)
display(before,after)
print('SQL boundary invariance: PASS; 1 order and 400 rubles, July 1 excluded')
'''
idx=next(i for i,c in enumerate(n['cells']) if c['cell_type']=='code' and src(c).startswith('print(\'Гостей'))
n['cells'].insert(idx,{'cell_type':'markdown','metadata':{},'source':['### Мини-проверка среза до выполнения\n','Ожидание: один заказ 30 июня на 400 ₽ даёт count=1, sum=400 на 1 июля. Вставка ровно 1 июля на 9000 ₽ не меняет признаки. Тот же order_aggregates используется для настоящей базы и маленькой копии.\n']})
n['cells'].insert(idx+1,{'cell_type':'code','metadata':{},'source':mini.splitlines(True),'outputs':[],'execution_count':None})
p.write_text(json.dumps(n,ensure_ascii=False,indent=1))
# Small presentational repair of the sites notebook, same data and protocol.
p=root/'sites-project.ipynb';n=json.loads(p.read_text())
for c in n['cells']:
 s=src(c)
 if c['cell_type']=='code':
  s=s.replace("ax.set_ylabel('Годовая маржа 40 автоматов, тыс. ₽')","ax.set_ylabel('Годовая маржа 40 автоматов, тыс. ₽')\nax.set_xlabel('город')\nax.set_title('Сценарии обследования 300 адресов и выбора 40')")
  c['execution_count']=None;c['outputs']=[]
 setsrc(c,s)
p.write_text(json.dumps(n,ensure_ascii=False,indent=1))
