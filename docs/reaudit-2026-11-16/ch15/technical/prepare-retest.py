"""LIGHT stdlib generator. No args: HOLD and no writes. Root must build/publish first.
--prepare --source-ready --export PATH; root render; --finalize --source-ready --export PATH.
Never launches browser/ML, changes course sources, or dispatches student.
"""
from pathlib import Path
import argparse,collections,hashlib,json,random,re,shutil
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch15';W=Path('/private/tmp/kuch15round');T=W/'student-retest';M=D/'technical/retest-package'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def require(c,m):
 if not c:raise AssertionError(m)
def immutable():
 manifest=read(D/'student/initial-freeze-manifest.json')
 require(len(manifest['files'])==128,'initial128')
 for f in manifest['files']:require(sha(D/'student'/f['path'])==f['sha256'],'initial frozen '+f['path'])
 for p,h in read(D/'technical/public-package-manifest.json')['files'].items():require(sha(W/'student'/p)==h,'original public '+p)
def parse(s,lesson):
 pp=re.split(r'(?m)(?=^## task: )',s);tasks={};questions={};n=collections.Counter()
 for part in pp[1:]:
  seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',part);ident=lesson+'/'+seg[0].split('## task: ')[1].split(' |')[0];item={'prompt':[seg[0]]}
  for k,v in zip(seg[1::2],seg[2::2]):item.setdefault(k,[]).append(v)
  tasks[ident]=item
 for m in re.finditer(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',pp[0]):
  n[m[1]]+=1;questions[f'{lesson}/{m[1]}/{n[m[1]]}']=m[0]
 return pp,tasks,questions
p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--finalize',action='store_true');p.add_argument('--source-ready',action='store_true');p.add_argument('--export',type=Path);a=p.parse_args()
if not a.prepare and not a.finalize:print('HOLD generator only: root sourceREADY+build/export required; no writes');raise SystemExit
require(a.source_ready and a.export and a.export.exists(),'root sourceREADY and actual final export required');immutable()
if a.finalize:
 ref=read(M/'reference.json');require(sha(a.export)==ref['export_sha256'],'export unchanged')
 for path,h in ref['source_sha256'].items():require(sha(R/path)==h,'source unchanged '+path)
 for path,h in ref['HTML_sha256'].items():require(sha(R/path)==h,'HTML unchanged '+path)
 for f in read(W/'figures-retest.json'):require((T/'figures'/(f['figure']+'.png')).exists(),'root PNG render '+f['figure'])
 files={str(p.relative_to(T)):sha(p)for p in T.rglob('*')if p.is_file()};dump(M/'public-package-manifest.json',{'status':'READY pending root dispatch','files':files,'count':len(files),'root':str(T),'export_sha256':sha(a.export)});print('FINALREADY',len(files));raise SystemExit
require(not (M/'reference.json').exists(),'do not refresh a delivered cut silently')
for folder in [T,M,W/'jobs-retest',W/'retest-source/content/ch15',W/'retest-source/content/figures',W/'retest-source/site/assets',D/'fixes/student/retest']:folder.mkdir(parents=True,exist_ok=True)
old={};new={};oq={};nq={};keys={};hints={};figs=[];hashes={};theory=[]
for lesson in read(D/'technical/baseline.json')['lesson_order']:
 path=R/'content/ch15'/(lesson+'.md');actual=path.read_text();before=(W/'original/content/ch15'/path.name).read_text();op,ot,oquestions=parse(before,lesson);np,nt,nquestions=parse(actual,lesson);old.update(ot);new.update(nt);oq.update(oquestions);nq.update(nquestions)
 hashes[str(path.relative_to(R))]=sha(path);shutil.copyfile(path,W/'retest-source/content/ch15'/path.name)
 if op[0]!=np[0]:theory.append(lesson)
 counters=collections.Counter()
 def sanitize(m):
  kind=m[1];counters[kind]+=1;ident=f'{lesson}/{kind}/{counters[kind]}';lines=[l for l in m[0].splitlines()if not l.strip().startswith('>')and not l.startswith('Почему:')];pos=[j for j,l in enumerate(lines)if re.match(r'^- \[[ x]\] ',l)];correct=[i for i,j in enumerate(pos)if lines[j].startswith('- [x] ')];require(len(correct)==1,'one answer '+ident);options=[re.sub(r'^- \[[ x]\] ','',lines[j])for j in pos];order=list(range(len(pos)));random.Random('ch15-retake-final-'+ident).shuffle(order);keys[ident]={'answer':order.index(correct[0])+1,'original_order':[i+1 for i in order]}
  for i,j in enumerate(pos):lines[j]=f'{i+1}. '+options[order[i]]
  lines[0]='Вопрос '+ident;return '\n'.join(lines[:-1])
 def visible(s):return re.sub(r'(?s)<details\b.*?</details>','[Разбор скрыт до собственного ответа.]',s)
 public=re.sub(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',sanitize,visible(np[0]))
 if lesson=='test':
  start=public.index('Вопрос test/');(T/'test-open.md').write_text(public[:start]);public=public[start:]
 for ident,item in nt.items():
  public+='\n'+visible(item['prompt'][0]);hints[ident]=[v.strip()for v in item.get('hint',[])]
  for v in item.get('starter',[]):public+='\n### Заготовка\n'+v
  for v in item.get('parsons',[]):
   lines=[l.strip()for l in v.splitlines()if l.strip()and not l.startswith('```')];random.Random('ch15-retake-'+ident).shuffle(lines);public+='\nДоступные строки для сборки с отступами:\n'+'\n'.join(lines)+'\n'
 figs.extend({'lesson':lesson,'figure':f}for f in re.findall(r'^::: figure\s+([^\s|]+)',public,re.M))
 require(not re.search(r'^### (check|hint|setup|solution|explain)\s*$',public,re.M),'private section '+lesson);require('- [x]'not in public and '- [ ]'not in public,'answer key '+lesson);(T/path.name).write_text(public)
 if lesson=='06-final-project':
  for phrase in ['Критерии приёмки','Итог для руководителя']:
   require(phrase in np[0],'mandatory public criterion before first task: '+phrase)
   html=(R/'site/ch15/06-final-project.html').read_text();require(phrase in html[:html.index('id="task-')],'built public criterion before first card '+phrase)
require(set(old)==set(new)and len(new)==57,'57taskIDs retained');require(set(oq)==set(nq)and len(nq)==32,'32questionIDs retained')
ae=[r for r in read(a.export)if r['lesson'].startswith('ch15/')];require(collections.Counter(r['kind']for r in ae)=={'task':57,'cell':29,'predict':3},'89technical export')
require({r['lesson'][5:]+'/'+r['id']for r in ae if r['kind']=='task'}==set(new),'source/export task IDs')
changes=[{'id':i,'sections':sorted(k for k in set(old[i])|set(new[i])if old[i].get(k)!=new[i].get(k))}for i in new if old[i]!=new[i]]
# Selection comes only from actual final diff; shared harness changes alone add no targets.
selected={x['id']for x in changes};related={}
anchors={'01-artifact':['golden','release','contract'],'02-service':['reasons','handler','http'],'02b-service-run':['tests'],'03-experiments':['lucky','reproduce'],'04-deploy':['stats','cron'],'05-project':['timeline','guard','advice'],'06-final-project':['target','models','profit','package']}
for lesson in theory:
 for name in anchors.get(lesson,[]):
  ident=lesson+'/'+name
  if ident in new and ident not in selected:related[ident]='concept carrying task for changed visible theory '+lesson;selected.add(ident)
qselected={i for i in nq if oq[i]!=nq[i]}|{i for i in nq if i.startswith('test/')}
require(sum(i.startswith('test/')for i in qselected)==17,'full17test')
(T/'data').mkdir(exist_ok=True)
for name,h in read(D/'technical/baseline.json')['data_sha256'].items():require(sha(R/'site/data'/name)==h,'canonical raw data unchanged '+name);shutil.copyfile(R/'site/data'/name,T/'data'/name)
# Own evidence only; global interview remains reserved, no reading/copying its prose.
for f in read(D/'student/initial-freeze-manifest.json')['files']:
 if f['path']=='global-improvements-own.md':continue
 target=T/'own-previous'/f['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(D/'student'/f['path'],target)
shutil.copytree(W/'student/cognitive-walkthrough',T/'cognitive-walkthrough',dirs_exist_ok=True)
(T/'submit.py').write_text((W/'student/submit.py').read_text().replace('kuch15round/jobs','kuch15round/jobs-retest'))
extra=T/'extra';extra.mkdir(exist_ok=True)
for name in ['project-template.ipynb','requirements.txt']:shutil.copyfile(R/'site/notebooks'/name,extra/name)
for lesson in read(D/'technical/baseline.json')['lesson_order']:
 if lesson in ['intro','test']:continue
 text=(R/'content/ch15'/(lesson+'.md')).read_text().split('## task: ')[0]
 for i,(lang,body) in enumerate(re.findall(r'```(python|bash|dockerfile)[^\n]*\n(.*?)```',text,re.S),1):(extra/(lesson+'-visible-'+str(i)+{'python':'.py','bash':'.sh','dockerfile':'.Dockerfile'}[lang])).write_text(body)
dump(T/'targets.json',{'tasks':sorted(selected),'questions':sorted(qselected),'counts':{'tasks':len(selected),'questions':len(qselected),'total':len(selected)+len(qselected)},'related_tasks':related,'core_track_UI_separate':{'question_ids':['c1','c2','c3','c16','c17'],'purpose':'root verifies visible core denominator5 independently of full17 quiz'},'reason':'actual changed task sections, questions, conceptual carrying anchors and full17test; shared harness change alone adds no replay'})
(T/'README.md').write_text('''# Повторное прохождение главы15

HOLD до rootREADY и CPUокна. Вход — только этот публичный каталог и свои own-previous. Работайте в docs/reaudit-2026-11-16/ch15/fixes/student/retest; исходную128файловую заморозку не меняйте. Полный порядок intro,01,02,02b,03,04,05,06,test-open,test. Прочтите публичные критерии, чек-лист и пустую форму письма до первой задачи финала. Рассмотрите figuresPNG. Пройдите только цели targets.json: фактически изменённые карточки и связанные навыки, изменённые вопросы и все17итоговых. Отдельный coreUIпроверяет root, не смешивайте его знаменатель5 с полным17. Сначала ответtest-open, потом варианты. Parsons/варианты заново перемешаны.

До каждой отправки Q1цель,Q2действие и где объяснено,Q3ожидаемые значения/ключи/единицы; после полныйfeedback,Q4следующий шаг. JSONLкак ранее:lesson,task,code,expect,Q1–Q3; вопросquestion,choice. python3 /private/tmp/kuch15round/student-retest/submit.py input.jsonl > feedback.jsonl . Код целиком заменяет редактор; импорты/starter включить. Подсказки по одной только после своей попытки. Прежний свой код можно переиспользовать, явно отличая новый код и повтор. Не делайте искусственных миграций старых frozen программ, сохраняйте первоначальный отказ и фактический следующий шаг.

Обновите собственный полный выпускной notebook+repo там, где новые публичные требования меняют содержательный вывод: OOF/калибровка/исторические денежные сценарии и фактический размер каждой очереди, ограничения данных/причинности, паспорт/контроль20/очередь3/план пилота. Не читайте чужих критиков. Семь браузерных разминок отдельно от содержательного проекта. Перенос и новый чистый CLI проверит получатель. Не требуется заново учить все модели только из-за прозы; разделите прежнее исполнение и новое. Нативные API/MLflow и Docker отмечайте раздельно. Один CPUпроцесс,OMP/OPENBLAS/MKL=1, только после rootокна. Первоначальное личное интервью зарезервировано отдельно и не входит в пакет.
''')
(T/'project-guiding-questions.md').write_text('# Вопросы к собственной выпускной работе\n\nСначала создайте НОВУЮ рабочую копию своего own-previous/own-project в docs/reaudit-2026-11-16/ch15/fixes/student/retest/own-project. Исходную заморозку и копию own-previous не изменяйте. Ответьте собственным кодом и пояснениями; это вопросы для самостоятельной доработки, не готовые решения.\n\n**PS15-01.** Как должна вести себя общая функция тренда при нулевом знаменателе, если возврат сохраняется? Проверьте обычную пару, нетто-возврат за пределом привычного диапазона и пару последних/предыдущих поступлений (−1,0). Как убедиться, что предобработка получает допустимые значения, а исходная очередь и паспортная сумма на той же CRM по-прежнему воспроизводятся?\n\n**PS15-02.** На каком наборе до позднего теста сравнить показатели одиночных признаков на общих фолдах? Как обработать категориальный признак без произвольного порядка, сохранить направление связи и проверить доступность сильнейшего сигнала на дату? Как проверить даты обращения относительно создания клиента и начала договора? Если исключить сомнительные записи, у каких офисов меняется именно число обращений? Какие ограничения фиксированного симулятора нужно назвать в выводе?\n\n**PS15-03.** Как собственным воспроизводимым шагом получить дополнительный отраслевой вывод, который заявлен в тексте, либо ясно ограничить результат и предоставить отдельную команду? Как проверить, что Restart & Run All или указанная команда пересоздаёт соответствующий артефакт? Сохраните первоначальный выбор модели и протокол до позднего теста; последующий дополнительный анализ обозначьте отдельно.\n')
with (T/'README.md').open('a') as stream:stream.write('\nОтдельная обязательная доработка полного проекта — project-guiding-questions.md. Работайте в НОВОЙ копии own-project, первоначальную128файловую заморозку и own-previous не редактируйте.\n')
for f in figs:
 path=R/'content/figures'/(f['figure']+'.svg');hashes[str(path.relative_to(R))]=sha(path);shutil.copyfile(path,W/'retest-source/content/figures'/path.name)
css=R/'site/assets/app.css';hashes[str(css.relative_to(R))]=sha(css);shutil.copyfile(css,W/'retest-source/site/assets/app.css');dump(W/'keys-retest.json',keys);dump(W/'hints-retest.json',hints);dump(W/'figures-retest.json',figs)
(W/'public-figures-retest.cjs').write_text((W/'public-figures.cjs').read_text().replace('/original/','/retest-source/').replace('/figures.json','/figures-retest.json').replace('/student/','/student-retest/'))
bridge=(W/'bridge.cjs').read_text().replace("path.resolve('docs/reaudit-2026-11-16/ch15/student')","path.resolve('docs/reaudit-2026-11-16/ch15/fixes/student/retest')").replace("log=out+'/'+phase+'-attempts.jsonl'","log=out+'/attempts.jsonl'").replace("w+'/keys.json'","w+'/keys-retest.json'").replace("jobdir=w+'/jobs'","jobdir=w+'/jobs-retest'").replace("out+'/initial-images'","out+'/images'").replace("w+'/stop'","w+'/stop-retest'")
require("jobdir=w+'/jobs-retest'"in bridge and 'fs.readdirSync(jobdir)'in bridge and "const job=jobdir+'/'+f"in bridge,'ONEjobdir scan/open');require("card.locator('.task-ui .CodeMirror').first()"in bridge and 'assert.equal(await cm.evaluate(e=>e.CodeMirror.getValue()),r.code)'in bridge,'strict CodeMirror readback');(W/'bridge-retest.cjs').write_text(bridge)
dump(M/'reference.json',{'status':'HOLD root PNG render and finalize gate required','source_sha256':hashes,'HTML_sha256':{str(p.relative_to(R)):sha(p)for p in (R/'site/ch15').glob('*.html')},'export_sha256':sha(a.export),'changed_tasks':changes,'changed_questions':[i for i in nq if oq[i]!=nq[i]],'changed_theory':theory,'selection':{'task':len(selected),'question':len(qselected),'total':len(selected)+len(qselected)},'related_tasks':related,'figures':len(figs)});immutable();print('HOLD prepared',len(changes),'changed tasks,',len(selected)+len(qselected),'selected; root render/finalize required')
