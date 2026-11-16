import json,hashlib
from pathlib import Path
W=Path('/private/tmp/kuch14round/student-retest');O=W/'own-previous/initial';D=Path(__file__).resolve().parent
wanted=json.loads((W/'targets.json').read_text());target=set(wanted['tasks']);rows=[]
lessons=['01-pixels','02-filters','03-classic','04-cnn','04b-transfer','04c-detection','05-project']
for l in lessons:
    old=[json.loads(x) for x in (O/(l+'-input.jsonl')).read_text().splitlines()]
    for r in old:
        if r.get('question') or l+'/'+r.get('task','') not in target:continue
        t=r['task'];a=dict(r)
        if t=='alerts':a=json.loads((O/'05-project-retry-input.jsonl').read_text())
        if t=='alerts':
            a['code']+='''\nimport json
signals=alert_table(df,2)
own_tables={"time":list(P.index),"slots":[int(x) for x in P.columns],"P":P.astype(int).values.tolist(),"T":T.astype(int).values.tolist(),"signals":signals.astype(int).values.tolist(),"alerts":alerts.to_dict(orient="records"),"policy_table":policy_table.to_dict(orient="index"),"chosen_k":chosen_k,"prices":{"false":120,"missed":300,"repeated":30,"delay_minute":1},"next_metrics":next_metrics}
print("OWN_TABLES_JSON "+json.dumps(own_tables,ensure_ascii=False))
print("SHAPES",P.shape,T.shape,signals.shape,alerts.shape)
'''
        sec=(W/(l+'.md')).read_text().split('## task: '+t+' |')[1].split('## task:')[0]
        a['Q1']='Повторяю знакомую задачу '+l+'/'+t+': '+sec.splitlines()[0].split('|')[0].strip()+'. Хочу получить указанные формы и величины своим кодом.'
        a['Q2']='Явно переиспользую собственный ранее принятый код из own-previous/initial. Перечитал текущее условие и заготовку; запускаю полный код с импортами. '+('Теперь прямо указан episode_metrics(frame, wide_bool_signals); передаю alert_table, список alerts только для отчёта. Мой прежний успех/ошибка уже известны, это повтор.' if t=='alerts' else 'Текущий текст описывает требуемую операцию; это не первая встреча с ней.')
        a['Q3']=a['expect']
        a['provenance']='Own previous accepted code, revised Q1–Q3; alerts adds explicit output tables.'
        rows.append(a)
    qs=[]
    if l=='04-cnn':qs=[('04-cnn/quiz/2',4,'После раннего global останется одно число на фильтр, деталей недостаточно; карта и входной сдвиг различаются.')]
    if l=='04b-transfer':qs=[('04b-transfer/quiz/1',1,'Сначала подбирается голова на готовых признаках. requires_grad фиксирует веса; eval дополнительно фиксирует буферы BatchNorm тела.')]
    for q,ch,reason in qs:rows.append(dict(question=q,choice=ch,expect=reason,Q1='Ответить по смыслу новой формулировки, до отправки.',Q2='Вижу варианты в текущем публичном уроке, выбираю '+str(ch)+'.',Q3=reason))
    batch=[r for r in rows if r.get('lesson')==l or r.get('question','').startswith(l+'/')]
    if batch:(D/(l+'-input.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in batch))
choices=[1,4,3,1,1,2,2,2,3,4,1,1,2,3,4]
reasons=['Форма RGB(H,W,C)=(64,64,3).','uint8 переполняется после255.','10000*1920*1080*3=62.208ГБ после распаковки.','PNG хранит точные метки без потерь.','32-5+1=28, шаг1.','Девять равных1/9усредняют окно.','Сдвиги только обучения и пулинг; тестовые копии не попадают вfit.','Проверяю отложенные кадры со сдвигом и серым краем, а неroll.','Локальные веса общие по положениям при одинаковом числе выходов.','Перенос — готовые предобученные признаки либо адаптация их слоёв.','Малый пилот и цена прироста вместо линейной экстраполяции.','Область исходного изображения, влияющая на нейрон.','Площади пересечения50/объединения150=.333<.5.','Одна trueрамка максимумодинраз; дубликатFP.','Нормировку и вечерние примеры проверяют на независимых условиях.']
qs=[]
for i,(c,r) in enumerate(zip(choices,reasons),1):qs.append(dict(question='test/quiz/'+str(i),choice=c,expect=r,Q1='Ответить на итоговый вопрос'+str(i)+' по пониманию, сохранив выбор до проверки.',Q2='В текущем test.md вижу варианты, выбираю '+str(c)+'. Открытый ответ уже сохранён.',Q3=r))
(D/'test-input.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in qs));rows+=qs
assert len(rows)==38
(D/'prepared-targets.json').write_text(json.dumps([r.get('question',r.get('lesson','')+'/'+r.get('task','')) for r in rows],indent=2))
print('Prepared',len(rows),'targets')
