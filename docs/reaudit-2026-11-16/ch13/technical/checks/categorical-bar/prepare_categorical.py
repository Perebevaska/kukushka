from pathlib import Path
import json,re,hashlib,ast,shutil
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course');d=root/'docs/reaudit-2026-11-16/ch13/technical/checks';c=d/'categorical-bar';c.mkdir(exist_ok=True)
source_export=Path('/private/tmp/kuch13round/final.json');assert hashlib.sha256(source_export.read_bytes()).hexdigest()=='681571ca57c423abd8148c43d07607ab8a9f0f3c3b6b8e7975a54b95e0f4b8d3';shutil.copy2(source_export,c/'export-before.json');tasks=[t for t in json.loads(source_export.read_text()) if t['kind']=='task' and t['lesson'].startswith('ch13/')];(c/'tasks-before.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2))
source=root/'content/ch13/05-project.md';(c/'05-project-before.md').write_text(source.read_text())
attempts=list(map(json.loads,(root/'docs/reaudit-2026-11-16/ch13/student/retest-attempts.jsonl').read_text().splitlines()));attempts=[r for r in attempts if r.get('id')=='05-project/weekly'];literal=next(r['code'] for r in attempts if 'plot(kind="bar")' in r.get('code',''));direct=next(r['code'] for r in attempts if 'ax.bar(weekly.index.to_pydatetime()' in r.get('code',''));prefix=literal[:literal.index('ax=weekly[focus_shop].plot')]
cat=prefix+'''import numpy as np
fig,ax=plt.subplots()
positions=np.arange(len(weekly))
ax.bar(positions,weekly[focus_shop].to_numpy(),label=focus_shop)
labels=[date.strftime('%Y-%m-%d') for date in weekly.index]
ax.set_xticks(positions,labels)
ax.set(title=str(focus_shop),ylabel='Доля сигналов')
'''
orig=list(map(json.loads,(d/'programs.jsonl').read_text().splitlines()));gray=next(r['code'] for r in orig if r['task']=='weekly' and r['label']=='wrong-one-plot-value')
cases=[]
def emit(label,code,expected,why):
 ast.parse(code);cases.append(dict(lesson='ch13/05-project',task='weekly',label=label,code=code,expected=expected,description=why,code_sha256=hashlib.sha256(code.encode()).hexdigest()))
emit('literal-pandas-datetimeindex-bar',literal,True,'Буквальный код ученика; правильный график. Pyodide renderer может упасть до check: отдельно считать stage/error, не ложным отказом guard.')
emit('explicit-categorical-bar',cat,True,'Центры0..8, реальные календарные даты в ticklabels, высоты по соответствующей неделе')
emit('categorical-swapped-tickdates',cat+"labels[0],labels[1]=labels[1],labels[0]\nax.set_xticklabels(labels)\n",False,'Переставлены только подписи первых двух дат')
emit('categorical-wrong-height',cat+'ax.patches[2].set_height(0)\n',False,'При правильных датах одна высота подменена нулём')
emit('categorical-wrong-shop',cat+'ax.set_title("TMN-1")\nax.containers[0].set_label("TMN-1")\n',False,'Значения KZN-2 подписаны как другая точка')
emit('gray-correct-wrong-highlight',gray,False,'Прежний literal219: верная серая линия не оправдывает ошибочную выделенную')
emit('direct-datetime-matplotlib-bar',direct,True,'Буквальная успешная адаптация ученика на прямой matplotlib datetime bar')
(c/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in cases));(c/'freeze.json').write_text(json.dumps({'count':len(cases),'program_sha256':hashlib.sha256((c/'programs.jsonl').read_bytes()).hexdigest(),'before_export_sha256':hashlib.sha256((c/'export-before.json').read_bytes()).hexdigest(),'before_tasks65_sha256':hashlib.sha256((c/'tasks-before.json').read_bytes()).hexdigest(),'before_source_sha256':hashlib.sha256((c/'05-project-before.md').read_bytes()).hexdigest(),'normative_expected_before_execution':True},indent=2));print(len(cases),(c/'freeze.json').read_text())
