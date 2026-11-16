"""Generate a sanitized retake only on root sourceREADY+build. stdlib, never dispatches.
Usage after explicit root gate: python3 .../prepare-retest.py --prepare --source-ready --export /private/tmp/kuch14round/final.json
Then root renders W/public-figures-retest.cjs; --finalize repeats source/export/HTML SHA checks.
No arguments only describe the gate; no course/source/student mutation.
"""
from pathlib import Path
import argparse,collections,hashlib,json,random,re,shutil
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch14';W=Path('/private/tmp/kuch14round');T=W/'student-retest';M=D/'technical/retest-package'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def require(x,m):
 if not x:raise AssertionError(m)
def immutable():
 for root in [D/'student',D/'fixes/student/holdout-predictions',D/'fixes/student/holdout-evaluation']:
  manifest={s.split('  ',1)[1]:s.split('  ',1)[0] for s in (root/'SHA256SUMS').read_text().splitlines() if s.strip()}
  require(all(sha(root/n)==v for n,v in manifest.items()),'immutable own evidence '+str(root))
def parse(s,lesson):
 pp=re.split(r'(?m)(?=^## task: )',s);tasks={};questions={};n=collections.Counter()
 for part in pp[1:]:
  seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',part);ident=lesson+'/'+seg[0].split('## task: ')[1].split(' |')[0];task={'prompt':[seg[0]]}
  for kind,body in zip(seg[1::2],seg[2::2]):task.setdefault(kind,[]).append(body)
  tasks[ident]=task
 for match in re.finditer(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',pp[0]):
  kind=match[1];n[kind]+=1;questions[f'{lesson}/{kind}/{n[kind]}']=match[0]
 return pp,tasks,questions

a=argparse.ArgumentParser();a.add_argument('--prepare',action='store_true');a.add_argument('--finalize',action='store_true');a.add_argument('--source-ready',action='store_true');a.add_argument('--export',type=Path);args=a.parse_args()
if not args.prepare and not args.finalize:print('HOLD: generator only; root must confirm sourceREADY and perform build/export before --prepare --source-ready --export PATH; no files written');raise SystemExit
require(args.source_ready,'explicit root sourceREADY gate required');require(bool(args.export and args.export.exists()),'root built final export required');immutable()
if args.finalize:
 reference=read(M/'reference.json');require(sha(args.export)==reference['export_sha256'],'export immutable after preparation')
 for p,v in reference['source_sha256'].items():require(sha(R/p)==v,'current source matches prepared '+p)
 for p,v in reference['HTML_sha256'].items():require(sha(R/p)==v,'built HTML matches prepared '+p)
 for f in read(W/'figures-retest.json'):
  p=T/'figures'/(f['figure']+'.png');require(p.exists() and p.stat().st_size>100,'rendered current PNG '+str(p))
 files={str(p.relative_to(T)):sha(p) for p in T.rglob('*') if p.is_file()};dump(M/'public-package-manifest.json',{'status':'READY only after root dispatch decision','root':str(T),'files':files,'count':len(files),'export_sha256':sha(args.export)});dump(W/'public-retest-input-sha256.json',files);print('FINALREADY',len(files),'public files; source/export/HTML/PNG/own immutable verified');raise SystemExit
require(not (M/'reference.json').exists(),'one prepared cut already exists; use explicit new cut instead of silently refreshing delivered package')
for folder in [T,M,W/'jobs-retest',W/'retest-source/content/ch14',W/'retest-source/content/figures',W/'retest-source/site/assets',D/'fixes/student/retest']:folder.mkdir(parents=True,exist_ok=True)
old={};new={};oq={};nq={};public_questions={};keys={};hints={};figs=[];theory_changed=[];source_hashes={};allpublic=[]
for lesson in read(D/'technical/baseline.json')['lesson_order']:
 p=R/'content/ch14'/(lesson+'.md');before=(W/'original/content/ch14'/p.name).read_text();actual=p.read_text();op,ot,q0=parse(before,lesson);np,nt,q1=parse(actual,lesson);old.update(ot);new.update(nt);oq.update(q0);nq.update(q1)
 source_hashes[str(p.relative_to(R))]=sha(p);shutil.copyfile(p,W/'retest-source/content/ch14'/p.name)
 if op[0]!=np[0]:theory_changed.append(lesson)
 count=collections.Counter()
 def sanitize(m):
  kind=m[1];count[kind]+=1;ident=f'{lesson}/{kind}/{count[kind]}';lines=[l for l in m[0].splitlines() if not l.strip().startswith('>') and not l.startswith('Почему:')];positions=[i for i,l in enumerate(lines) if re.match(r'^- \[[ x]\] ',l)];marked=[i for i,j in enumerate(positions) if lines[j].startswith('- [x] ')];require(len(marked)==1,'one quiz answer '+ident);options=[re.sub(r'^- \[[ x]\] ','',lines[j]) for j in positions];order=list(range(len(positions)));random.Random('ch14-retest-nov17-'+ident).shuffle(order);keys[ident]={'answer':order.index(marked[0])+1,'original_order':[i+1 for i in order]}
  for i,j in enumerate(positions):lines[j]=f'{i+1}. '+options[order[i]]
  lines[0]='Вопрос '+ident;return '\n'.join(lines[:-1])
 def without_details(s):return re.sub(r'(?s)<details\b.*?</details>','[Разбор скрыт до собственного ответа.]',s)
 public=without_details(np[0]);public=re.sub(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',sanitize,public);public=re.sub(r'(?m)^revisions:.*\n','',public)
 if lesson=='test':
  pos=public.index('Вопрос test/');front=re.sub(r'(?s)^---\n.*?\n---\n','',public[:pos]);(T/'test-open.md').write_text(front);public=public[pos:]
 for ident,item in nt.items():
  public+='\n'+without_details(item['prompt'][0]);hints[ident]=[s.strip() for s in item.get('hint',[])]
  for body in item.get('starter',[]):public+='\n### Заготовка\n'+body
  for body in item.get('parsons',[]):
   lines=[l.strip() for l in body.splitlines() if l.strip() and not l.startswith('```')];random.Random('ch14-retest-nov17-'+ident).shuffle(lines);public+='\nДоступные строки для сборки с отступами:\n'+'\n'.join(lines)+'\n'
 for f in re.findall(r'^::: figure\s+([^\s|]+)',public,re.M):figs.append({'lesson':lesson,'figure':f})
 require(not re.search(r'^### (?:setup|check|hint|solution|explain)\s*$',public,re.M),'hidden section '+lesson);require('- [x]' not in public and '- [ ]' not in public,'quiz keys '+lesson);require('<details' not in public,'unopened details disclosure '+lesson);(T/p.name).write_text(public)
 # Publish ONLY the new open prompt, no author explain or answer before attempt.
 if lesson=='05-project':
  parking=re.search(r'(?s)^## Самостоятельно: свободное место на парковке\n(.*?)(?=<details)',np[0],re.M);require(parking is not None,'parking MUST be in public theory before first task, not extracted from explain');
  html=(R/'site/ch14/05-project.html').read_text();require(html.index('Парковка получает фото мест')<html.index('id="task-day"'),'built public HTML parking precedes first task');require('письм' in np[0].lower(),'letter brief in public theory required');(T/'parking-open.md').write_text('# Сначала собственный ответ: парковка\n'+parking[1].strip()+'\n')
  local=re.search(r'(?s)^### Локальный опыт после проверки правила\n(.*?)(?=^## task:)',actual,re.M)
  if local:(T/'after-alerts-reading.md').write_text('# После сдачи alerts: локальное сравнение\n'+local[1].strip()+'\n')
require(set(old)==set(new),'61 task IDs retained');require(set(oq)==set(nq),'question IDs retained')
changes=[{'id':i,'changed_sections':sorted(k for k in set(old[i])|set(new[i]) if old[i].get(k)!=new[i].get(k))} for i in new if old[i]!=new[i]];qchanges=[i for i in nq if oq[i]!=nq[i]]
be={r['lesson'][5:]+'/'+r['id']:r for r in read(D/'technical/baseline-export.json') if r['kind']=='task'};ae={r['lesson'][5:]+'/'+r['id']:r for r in read(args.export) if r['kind']=='task' and r['lesson'].startswith('ch14/')};require(set(be)==set(ae)==set(new),'source/export IDs')
for i,item in new.items():
 for field,target in [('setup','setup'),('check','check'),('starter','starter'),('solution','solution'),('parsons','solution')]:
  if field in ['setup','starter','solution','parsons'] and (field!='parsons' or item.get('parsons')) and not (field=='solution' and not item.get('solution') and item.get('parsons')):
   bodies=item.get(field,[]);codes=[re.search(r'(?s)```[^\n]*\n(.*?)```',v) for v in bodies];literal='\n'.join(c[1].strip() for c in codes if c)
   require(literal.strip()==ae[i].get(target,'').strip(),'actual export source code '+i+'/'+field)
export_changes={i:sorted(k for k in set(be[i])|set(ae[i]) if be[i].get(k)!=ae[i].get(k)) for i in ae if be[i]!=ae[i]};require({c['id'] for c in changes if 'check' in c['changed_sections']}=={i for i,fs in export_changes.items() if 'check' in fs},'source/export check diff matches')
# Related tasks test conceptual carrying points from changed theory, with explicit reasons.
anchors={'01-pixels':['crop','centroid','cells'],'02-filters':['pool','global'],'03-classic':['flat','augment','stress'],'04-cnn':['layer','pool-size','out-size'],'04b-transfer':['trainable','frozen-bug','few-shot','folders'],'04c-detection':['nms','iou'],'05-project':['light','fix','hours','alerts','restock']}
selected={c['id'] for c in changes};related={}
for lesson in theory_changed:
 for name in anchors.get(lesson,[]):
  i=lesson+'/'+name
  if i in new and i not in selected:related[i]='carrying task for changed public theory in '+lesson;selected.add(i)
question_selected=set(qchanges)|{i for i in nq if i.startswith('test/')};require(len([i for i in question_selected if i.startswith('test/')])==15,'all15final')
# Current open local code only; no practice notebook or author task solutions.
(T/'extra').mkdir(exist_ok=True);compare=R/'site/notebooks/compare_showcase_features.py';shutil.copyfile(compare,T/'extra'/compare.name);source_hashes[str(compare.relative_to(R))]=sha(compare)
cnntext=(R/'content/ch14/04-cnn.md').read_text().split('## task: ')[0];blocks=re.findall(r'```python[^\n]*\n(.*?)```',cnntext,re.S);cnn=[s for s in blocks if 'import torch' in s and 'range(25)' in s];require(len(cnn)==1,'public CNNexample');(T/'extra/cnn-visible-example.py').write_text(cnn[0]);(T/'extra/README.md').write_text('Текущий открытый примерCNNи публикуемый сравнительныйскрипт. Предыдущие outputs доступны в own-previous. Не требуется повторять25эпох илиResNetвесьнабортолькорадипрозы; объясните изменённые режимы/преобразования, прежние исполнения называйте прежними. Новый запуск — только послеCPUокнаroot.\n')
(T/'data').mkdir(exist_ok=True)
for name in sorted({f for r in ae.values() for f in r['files']}):
 require(sha(R/'site/data'/name)==read(D/'technical/baseline.json')['data_sha256'][name],'published NPZ unchanged '+name);shutil.copyfile(R/'site/data'/name,T/'data'/name)
for root,name in [(D/'student','initial'),(D/'fixes/student/holdout-predictions','holdout-predictions'),(D/'fixes/student/holdout-evaluation','holdout-evaluation')]:
 dest=T/'own-previous'/name;dest.mkdir(parents=True,exist_ok=True)
 manifest={s.split('  ',1)[1]:s.split('  ',1)[0] for s in (root/'SHA256SUMS').read_text().splitlines() if s.strip()}
 for n,v in manifest.items():q=dest/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/n,q)
shutil.copytree(W/'student/cognitive-walkthrough',T/'cognitive-walkthrough',dirs_exist_ok=True)
helper=(W/'student/submit.py').read_text().replace('kuch14round/jobs','kuch14round/jobs-retest');(T/'submit.py').write_text(helper)
(T/'targets.json').write_text(json.dumps({'tasks':sorted(selected),'questions':sorted(question_selected)},ensure_ascii=False,indent=2)+'\n')
(T/'README.md').write_text('''# Адресное повторное прохождение главы 14

HOLD: начинайте только после READY и разрешённого CPU-окна. Входы — этот публичный каталог и own-previous: только ваши собственные initial, holdout-predictions и holdout-evaluation. Работайте в docs/reaudit-2026-11-16/ch14/fixes/student/retest/. Первоначальные 59 файлов и обе holdout-заморозки не меняйте. Чужие отчёты и скрытые ключи, проверки, setup и авторские решения не передаются.

Сначала сохраните самостоятельный ответ parking-open.md до разбора и до чтения 05-project. До вариантов test.md ответьте на test-open.md. Затем перечитайте текущую теорию в прежнем порядке от intro до 05-project, рассмотрите 19 PNG, выполните все цели из targets.json и все 15 итоговых вопросов. Пакет содержит справочную теорию; after-alerts-reading.md читайте после собственной сдачи alerts. Уже известный второй день не называйте новым слепым опытом. Holdout — отдельное завершённое свидетельство.

Перед отправкой сохраните Q1: цель; Q2: доступное действие и место объяснения; Q3: ожидаемые значения, ключи, формы и единицы. После сохраните полный feedback и Q4: следующий шаг. Сначала собственная попытка, потом при необходимости одна подсказка. Новые input/feedback не переписывайте. JSONL задачи: lesson, task, code, expect, Q1, Q2, Q3. Вопрос: question вида 01-pixels/predict/1 или /quiz/1, choice из этого пакета, expect и Q1–Q3. Code целиком заменяет редактор, включайте imports и starter. Отправка: python3 /private/tmp/kuch14round/student-retest/submit.py input.jsonl > feedback.jsonl. Подсказка: action=hint после своей попытки. Aggregate пишет bridge, не изменяйте его. Откройте свои PNG перед описанием.

Использовать свой прежний код можно явно. Разделяйте новые и переиспользованные программы, чтение и реальное исполнение. Для alerts сохраните собственные таблицы, формы и вызовы готовых функций. При ошибке запишите полную реакцию и точный следующий шаг. Деловой ответ пишите по своим данным, отделив наблюдение, сценарий, цену ошибки и внешние расходы.

В отдельном appendix после повторного прохождения самостоятельно сверьте текстовые числители и знаменатели своего прежнего holdout review/walkthrough с собственными metrics.json и joined.csv. Сохраните расчёт и, если нужно, уточнение. Первоначальные тексты не исправляйте. Готовый результат этой сверки в пакет не вложен.

Публичные extra обновлены; ваши прежние реальные outputs находятся в own-previous. Повторные 25 эпох и полный ResNet ради чтения не обязательны. Укажите, что исполняли ранее, что изменилось в подаче и что исполнили теперь. Для нового ML получите CPU-окно root: один процесс, OMP/OPENBLAS/MKL=1, torch threads=1. Новые загрузки не требуются. Тест агента не измеряет время и успеваемость человека. Итог: дневник, report, покрытие targets, knowledge и отдельное уточнение holdout.
''')
# Figure sources are frozen for root's light render; no browser is launched here.
for f in figs:
 p=R/'content/figures'/(f['figure']+'.svg');source_hashes[str(p.relative_to(R))]=sha(p);shutil.copyfile(p,W/'retest-source/content/figures'/p.name)
require(len(figs)==19,'19figures');(T/'figures').mkdir(exist_ok=True);css=R/'site/assets/app.css';source_hashes[str(css.relative_to(R))]=sha(css);shutil.copyfile(css,W/'retest-source/site/assets/app.css')
dump(W/'keys-retest.json',keys);dump(W/'hints-retest.json',hints);dump(W/'figures-retest.json',figs)
script=(W/'public-figures.cjs').read_text().replace('/original/','/retest-source/').replace('/figures.json','/figures-retest.json').replace('/student/','/student-retest/');(W/'public-figures-retest.cjs').write_text(script)
bridge=(W/'bridge.cjs').read_text().replace("path.resolve('docs/reaudit-2026-11-16/ch14/student')","path.resolve('docs/reaudit-2026-11-16/ch14/fixes/student/retest')").replace("log=out+'/'+phase+'-attempts.jsonl'","log=out+'/attempts.jsonl'").replace("w+'/keys.json'","w+'/keys-retest.json'").replace("w+'/jobs'","w+'/jobs-retest'").replace("w+'/jobs/'","w+'/jobs-retest/'").replace("out+'/initial-images'","out+'/images'").replace("w+'/stop'","w+'/stop-retest'");require("w+'/jobs'" not in bridge and "w+'/jobs/'" not in bridge,'both retake queue scan and open use jobs-retest');require("card.locator('.task-ui .CodeMirror').first()" in bridge and 'assert.equal(await cm.evaluate(e=>e.CodeMirror.getValue()),r.code)' in bridge,'taskeditor readback');(W/'bridge-retest.cjs').write_text(bridge)
reference={'status':'HOLD pending root light19PNG render and finalmetadata gate; never dispatch from script','source_sha256':source_hashes,'HTML_sha256':{str(p.relative_to(R)):sha(p) for p in (R/'site/ch14').glob('*.html')},'export_path':str(args.export),'export_sha256':sha(args.export),'changed_tasks':changes,'changed_questions':qchanges,'changed_theory':theory_changed,'export_changes':export_changes,'related_tasks':related,'selection':{'tasks':sorted(selected),'questions':sorted(question_selected),'task_count':len(selected),'question_count':len(question_selected),'count':len(selected)+len(question_selected)},'all_task_section_hashes':{i:{'before':{k:[digest(v) for v in vv] for k,vv in old[i].items()},'after':{k:[digest(v) for v in vv] for k,vv in new[i].items()}} for i in new}}
dump(M/'reference.json',reference);dump(M/'public-package-manifest.json',{'status':'HOLD: PNG rendering and --finalize required','root':str(T),'files':{str(p.relative_to(T)):sha(p) for p in T.rglob('*') if p.is_file()}});immutable();print(json.dumps({'status':'HOLD','changed_tasks':len(changes),'related_tasks':len(related),'selected':reference['selection'],'changed_theory':theory_changed,'PNG':len(figs)},ensure_ascii=False,indent=2))
