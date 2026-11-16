from pathlib import Path
import json,ast,hashlib
p=Path('/private/tmp/kuch13round/checks');tasks=json.loads((p/'tasks.json').read_text());rows=[json.loads(l) for l in (p/'programs.jsonl').read_text().splitlines()];tm={t['id']:t for t in tasks}
def emit(id,label,code,expected,description,origin='new targeted program'):
 t=tm[id];ast.parse(code);name=f'{t["lesson"].split("/")[-1]}--{id}--{label}.py';(p/'programs'/name).write_text(code);rows.append(dict(lesson=t['lesson'],task=id,label=label,code=code,expected=expected,description=description,origin=origin,reachability='editor',code_sha256=hashlib.sha256(code.encode()).hexdigest(),program_file='programs/'+name))
def extra(id,label,suffix,expected,desc):emit(id,label,tm[id]['solution']+'\n'+suffix,expected,desc)
s=tm['parse-llm']['solution']
for topic in ['кофе','еда','обслуживание','доставка','цена','атмосфера']:
 # Recompute original table with author parse, then change only callable's enum. New-input probes distinguish it.
 extra('parse-llm','exclude-'+topic,'_original_parse=parse\ndef parse(answer):\n    r=_original_parse(answer)\n    return {"sentiment":None,"topic":None,"ok":False} if r["topic"]=='+repr(topic)+' else r',False,'Отсутствует одна из шести допустимых тем на новом входе')
emit('parse-llm','tuple-return',s.replace('bad = {"sentiment": None, "topic": None, "ok": False}','bad = (None,None,False)').replace('return {"sentiment": d["sentiment"], "topic": d["topic"], "ok": True}','return d["sentiment"], d["topic"], True').replace('pd.DataFrame([parse(a) for a in raw])','pd.DataFrame([parse(a) for a in raw],columns=["sentiment","topic","ok"])'),True,'Разрешённая тройка полей вместо словаря')
extra('parse-llm','accept-invalid-enum','_original_parse=parse\ndef parse(answer):\n    d=json.loads(answer) if answer.strip().startswith("{") else None\n    if d and d.get("sentiment")=="neutral": return {"sentiment":"neutral","topic":d.get("topic"),"ok":True}\n    return _original_parse(answer)',False,'Neutral не входит в разрешённую тональность')
extra('parse-llm','empty-strings','_original_parse=parse\ndef parse(answer):\n    return ("","",False) if not answer else _original_parse(answer)',False,'Пустой строковый ответ возвращает пустые строки вместо None')
extra('bigrams','unrelated-tail','top_bad = top_bad[:3]+[("кофе","кофе"),("да","ладно")]',False,'Последние две биграммы не входят в требуемый top5')
extra('keywords','reverse-function','_original_keywords=keywords\ndef keywords(i,k=3): return list(reversed(_original_keywords(i,k)))',False,'Правильное множество ключевых слов, нарушен порядок весов')
extra('keywords','wrong-keyed-table','kw={i:["неверное"] for i in range(5)}',False,'Ключи kw правильные, значения не соответствуют отзывам')
extra('weekly','permuted-keyed-rows','weekly=weekly.iloc[::-1]',True,'Корректные даты/доли, иной физический порядок строк; явного требования сортировки нет')
extra('weekly','wrong-plot','plt.close("all")\nax=plt.subplots()[1]\nax.bar(range(len(weekly)), [0]*len(weekly))\nax.set_ylabel("рубли")',False,'Таблица верна, график рисует нули и неверные единицы')
extra('weekly','equivalent-bar-plot','plt.close("all")\nax=plt.subplots()[1]\nax.bar(weekly.index,weekly[focus_shop],width=5,label=focus_shop)\nax.set_ylabel("доля сигналов модели");ax.legend()',True,'Те же недельные доли выбранной точки столбцами вместо линии')
extra('weekly','wrong-one-plot-value','ax.lines[-1].set_ydata(weekly[focus_shop].values+.1)',False,'График выбранной точки завышен на .1 при верной таблице')
extra('why','swapped-point','focus_shop="TMN-1"',False,'Название точки подменено после расчёта цитат и тем')
extra('why','swapped-date','change_date=pd.Timestamp("2026-10-01")',False,'Дата границы подменена после расчёта тем/цитат')
# Compute any admissible focus independently from the maximum growth, then whole keyed reports retain content.
extra('why','permuted-topic-rows','kzn=kzn.iloc[::-1];others=others.iloc[::-1]',True,'Те же ключи тем и доли, иной порядок строк')
extra('score','swapped-source-text','n.loc[n.index[0],"text"]="Другой отзыв"',False,'Подмена текста при сохранении review_id')
extra('score','id-reordered-source','n=n.sample(frac=1,random_state=19).set_index("review_id",drop=False)',True,'Перемешаны целые строки, индекс по review_id; принадлежность сохранена')
extra('adjust','swapped-period-numerators','audit["complaints"]=audit["complaints"].iloc[::-1].to_numpy()',False,'Числители жалоб переставлены между периодами')
extra('adjust','wrong-denominators','audit["manual"]=audit.complaints/audit.n.sum()',False,'Общий знаменатель двух периодов вместо отдельного')
extra('adjust','permuted-period-rows','audit=audit.iloc[::-1]',True,'Значения и ключи периодов сохранены')
emit('adjust','positional-gold',tm['adjust']['solution'].replace("labeled = n.merge(gold[['review_id','complaint']],on='review_id',validate='one_to_one')","labeled=n.copy()\nlabeled['complaint']=gold['complaint'].to_numpy()"),False,'Позиционная склейка разных порядков вместо review_id')
extra('adjust','incorrect-boundary','n["period"]=__import__("numpy").where(n.date>="2026-10-01","после","до")',False,'Граница в готовой n подменена с Oct5 на Oct1 после расчёта')
extra('masked-pool','new-padding-evidence','print("new_padding_pool",mean_pool(np.array([[[1.,3.],[3.,1.],[100.,-100.]]]),np.array([[1,1,0]])).tolist())',True,'Дополнительный новый padded пакет; ожидаемо [[2,2]]')
# Strict public-card-only program: no omitted final-test variables.
s=tm['recall95']['solution'];s=s[:s.index('\np_test=')]
emit('recall95','only-public-task-outputs',s,True,'Выполнены все требования карточки; test_recall/test_flagged в условии отсутствуют')
# Exact current69 additional program generated literally by the historical driver.
s=tm['parse-llm']['solution']+'\nparsed.iloc[[0,1]] = parsed.iloc[[1,0]].to_numpy()'
emit('parse-llm','historical69-additional',s,False,'Литерал additional выражения из reaudit_technical.py на current author; сверить SHA с историческим журналом','historical additional expression / current author')
(p/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
# This manifest is final before execution; no model/library import or Python program execution was used during construction.
(p/'freeze-manifest.json').write_text(json.dumps({'baseline':'563d774b125387aca7b004c086603e02900a18b1','program_count':len(rows),'card_count':65,'files':{str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file() and f.name!='freeze-manifest.json'}},indent=2))
print(len(rows),hashlib.sha256((p/'programs.jsonl').read_bytes()).hexdigest())
