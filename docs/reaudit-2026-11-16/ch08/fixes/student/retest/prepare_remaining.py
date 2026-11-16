from pathlib import Path
import json,re
ROOT=Path('/Users/dmitriikormin/Documents/Projects/ds-course')
old=ROOT/'docs/reaudit-2026-11-16/ch08/student'
package=Path('/private/tmp/kuch08round/student-retest')
out=ROOT/'docs/reaudit-2026-11-16/ch08/fixes/student/retest'
def previous(lesson,task):
    files=sorted((old/'attempts').glob(lesson+'-*.jsonl'))
    rows=[]
    for p in files:
        if 'feedback' in p.name:continue
        for l in p.read_text().splitlines():
            r=json.loads(l)
            if r.get('task')==task:rows.append(r)
    return rows[-1]['code']
def starter(lesson,task):
    t=(package/(lesson+'.md')).read_text().split('## task: '+task+' |',1)[1].split('## task: ',1)[0]
    m=re.search(r'### Заготовка\s*```python\n(.*?)```',t,re.S)
    return m.group(1) if m else ''
rows=[]
def add(lesson,task,body,goal,action,expect,include_starter=True):
    rows.append({'lesson':lesson,'task':task,'code':(starter(lesson,task) if include_starter else '')+body,'expect':expect})
    with (out/'walkthrough.md').open('a') as f:
        f.write('\n### S08-'+lesson+'/'+task+' — retest до отправки\nQ1: '+goal+'\nQ2: '+action+'\nQ3: '+expect+'\nQ4: Пока не отправлено, CPU у координатора.\n')
add('01-value','p-profit',previous('01-value','p-profit'),'Выразить ожидаемый итог кампании в рублях для любого списка получателей.','В карточке Parsons нашёл четыре строки. Ставлю def, затем TP/FP внутри и return с их разными ценами.','Вход send связывается с y одного гостя; +400 за TP и −200 за FP, стоимость бонуса не вычитается второй раз.',False)
add('02-budget','gains-plot','''score=np.asarray(risk)
yv=np.asarray(y_test)
order=np.argsort(-score)
x=np.arange(1,len(yv)+1)/len(yv)
gain=np.cumsum(yv[order])/yv.sum()
fig,ax=plt.subplots()
ax.plot(x,gain,label='модель')
ax.plot([0,1],[0,1],label='случайно')
ax.set_xlabel('доля гостей с бонусом')
ax.set_ylabel('доля пойманных уходящих')
ax.set_title('Охват уходящих при разном бюджете')
ax.legend()
at10=round(float(gain[int(.1*len(yv))-1]),3)
plt.show()
''','Показать, какую долю всех уходящих охватывают первые k% контактов при ограниченном бюджете.','В разделе gains нашёл сортировку по убыванию и накопительную сумму. Первым действием привожу риск и факты в согласованные массивы.','Линия модели выше диагонали; at10 считает найденных первых60 из всех134 уходящих, не precision. Оси выражены долями, обе линии видимы.')
add('04-monitoring','p-monitor',previous('04-monitoring','p-monitor'),'Получить доступную без меток сводку здоровья прогнозов одного месяца.','В Parsons находятся def, return и три подписанных поля; собираю только из этих строк.','leads равен len(p), mean_pred — средняя вероятность, above — доля строго выше threshold с тремя знаками.',False)
add('04b-segments','report-text','''report_metrics={'n':int(len(soc)),'deals':int(soc.converted.sum()),'auc':round(roc_auc_score(soc.converted,soc.p),3),
'pred_mean':round(soc.p.mean(),3),'fact_rate':round(soc.converted.mean(),3)}
low,high=auc_ci(soc.converted,soc.p)
report_metrics['ci_low']=round(float(low),2)
report_metrics['ci_high']=round(float(high),2)
r=report_metrics
report=(f"Соцсети: AUC {r['auc']:.3f} (95 % ДИ {r['ci_low']:.2f}–{r['ci_high']:.2f}) на {r['n']} заявках, {r['deals']} договора. "
        f"Прогноз {r['pred_mean']:.3f} при факте {r['fact_rate']:.3f}.")
''','Дать владельцу соцсетей подписанную метрику без смешения прогноза с наблюдаемой конверсией.','В новой редакции отдельное предложение требует CI словаря тоже до двух знаков; начинаю с именованных полей и CI функции заготовки.','Ожидаю 324 заявки,22 договора, AUC около.852,CI около.79–.92, прогноз.025 при факте.068. Прогноз занижен, высокая AUC сама не исправляет порог.')
add('05-explain','p-pd',previous('05-explain','p-pd'),'Описать, как средний прогноз модели меняется при фиксированном значении одного признака у всех гостей.','Собираю семь предоставленных строк Parsons: новая копия X внутри каждого шага сетки, изменение col и усреднение predict_proba.','Длина результата равна grid, X не мутирует. Это модельный сценарий, не доказательство причинности.',False)
pdcode=previous('05-explain','pd-two')
# Keep the previous authored body after its theory starter.
pdcode=pdcode[pdcode.index('def curve(group):'):]
add('05-explain','pd-two',pdcode,'Сравнить форму зависимости прогноза от давности у новичков и остальных, сохранив две кривые.','В карточке pd-two условия tenure<=3, grid и имена pd_new/pd_old. Первым действием делю тест по стажу, не меняя его, затем подставляю дни в копиях.','Две линии с легендами и корректной осью X; списки по8точек с3знаками, max_gap_day по наибольшей разнице новых минус старые. Изменение риска модели не эффект реального визита.')
add('06-project','top40','''import pandas as pd
rows={}
for city,(pred,fact) in fits.items():
    ids=pred.nlargest(K).index
    rows[city]={'model':round(fact.loc[ids].sum()-K*COST),'random':round(K*fact.mean()-K*COST)}
top=pd.DataFrame.from_dict(rows,orient='index')
''','Сравнить ценность модельного отбора40адресов с40случайными при одинаковых расходах в тыс.₽/год.','В обновлённом top40 прочёл: fact — исходные оценки profit_k, не наблюдённая эксплуатация. Начинаю с переданной fits, не перезаписываю её обучением.','Выбор по pred, сумма по fact тех же ID, расход5600тыс.₽. Сдвиг pred одной константой не меняет ранг и итог по реестру.')
add('06-project','decision',previous('06-project','decision'),'Выбрать город совета по риску<=2.5%, затем среднему, в тыс.₽/год.','Использую переданную risk; после моей исходной ошибки в первом проходе не реконструирую входные города.','Сохраняется порядок индекса passed,граница.025включена;при пустом наборе choice/cost_of_safety=None,при наличии лучший безопасный.')
add('06-project','forest','''from sklearn.linear_model import LinearRegression
rows={}
linear={}
for city in ['Пермь','Екатеринбург']:
    part=s[s.city==city]
    xt,xv,yt,yv=train_test_split(prep(part),part.profit_k,test_size=.25,random_state=42)
    m=RandomForestRegressor(n_estimators=100,min_samples_leaf=5,random_state=0,n_jobs=1).fit(xt,yt)
    pred=pd.Series(m.predict(xv),index=yv.index)
    profits=boot_city(pred,yv)
    rows[city]={'r2':round(r2_score(yv,pred),3),'mean':round(profits.mean()),'p_loss':round((profits<0).mean(),3)}
    lr=LinearRegression().fit(xt,yt)
    lp=boot_city(pd.Series(lr.predict(xv),index=yv.index),yv)
    linear[city]={'mean':lp.mean(),'p_loss':(lp<0).mean()}
rf_risk=pd.DataFrame.from_dict(rows,orient='index')
lr_risk=pd.DataFrame.from_dict(linear,orient='index')
def choose(t):
    ok=t[t.p_loss<=.025]
    return ok['mean'].idxmax() if len(ok) else None
same_choice=bool(choose(rf_risk)==choose(lr_risk))
''','Проверить устойчивость совета к замене линейного ранжирования лесом на тех же двух городах.','В условии forest параметров и разбиения не меняю; первым действием выделяю Пермь/Екатеринбург, потом считаю оба решения по одному правилу.','rf_risk содержит r2,mean,p_loss для2городов. same_choice сравнивает максимум среднего среди безопасных,включая полный отказ. Результат относится к оценкам profit_k,а не ко всем источникам эксплуатационного риска.')
# The fixed pilot aggregate is still the public task's input; it does not search for features/threshold.
add('07-final-project','fp-metric','''a=pilot.loc[pilot.group_name=='предложение','bought']
b=pilot.loc[pilot.group_name=='контроль','bought']
conv_offer=round(a.mean(),3)
conv_ctrl=round(b.mean(),3)
uplift_pp=round((a.mean()-b.mean())*100,1)
breakeven=round(C/V,3)
profit_all=int(V*a.sum()-C*len(a))
honest_per_offer=round((a.mean()-b.mean())*V-C)
''','Объяснить финансовый результат заранее заданного сравнения двух случайных групп всего пилота.','В шаге3 теперь явно разрешена фиксированная сводка всего пилота; она не выбирает признаки/порог. Начинаю с групп bought и неокруглённой разности.','Конверсии.110/.025,прирост8.5п.п.,порогэффекта.094;46800₽получателей,−14₽на контакт сверх контроля. Это средняя оценка,не точный установленный индивидуальный эффект.')
(out/'other-prepared.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
# New test answers authored after separate open answer was saved, not sent yet.
choices=[3,2,4,2,2,4,2,4,4,3,2,4,1,4,3]
exps=['Сравню прибыль модели и правила на общих допущениях.','200/(.25×2400)=1/3.','(12−10)×500−1500=−500 ₽.','Гости×конверсия×чек объясняют арифметический сдвиг.','Доля уходящих в верхушке в2.5раза выше базовой.','Gains — доля всех уходящих,охваченная верхнимиk%.','Проверяю окупаемость во всём диапазоне15–35%.','Сначала проверю единицы входа:57раз похоже на минуты/часы.','Выпуск новой модели после общего свежего отложенного сравнения.','drop=None и ignore дают[0,0]в блоке двух известных категорий,не новый столбец.','Общий AUC включает межканальные пары.','PDP усредняет прогнозы после подстановки,это не причинность.','Другие признаки могут содержать возрастные прокси.','Одинаковые40автоматов дают честный общий бюджет сравнения.','Июльские события неизвестны на дату предложения1июля.']
quizzes=[]
with (out/'walkthrough.md').open('a') as f:
 for i,(ch,e) in enumerate(zip(choices,exps),1):
    quizzes.append({'question':f'test/quiz/{i}','choice':ch,'expect':e})
    f.write(f'\n### S08-test/quiz/{i} — новая редакция до отправки\nQ1: '+e+'\nQ2: После сохранения открытого ответа прочёл вопрос '+str(i)+' в новом test.md, выбираю вариант '+str(ch)+'.\nQ3: '+e+'\nQ4: Пока не отправлено.\n')
(out/'test-prepared.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in quizzes))
