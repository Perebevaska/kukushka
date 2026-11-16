"""Prepare a HOLD-only sanitized ch13 retake. stdlib; no course/ML execution."""
from pathlib import Path
import collections
import hashlib
import json
import random
import re
import shutil

ROOT=Path('/Users/dmitriikormin/Documents/Projects/ds-course')
D=ROOT/'docs/reaudit-2026-11-16/ch13'
P=D/'fixes/student/retest'
W=Path('/private/tmp/kuch13round')
T=W/'student-retest'
T.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def source(p):return ''.join(p) if isinstance(p,list) else p
def read(p):return json.loads(p.read_text())
def require(x,m):
 if not x:raise AssertionError(m)

def parse(s,lesson):
 parts=re.split(r'(?m)(?=^## task: )',s); tasks={}
 for part in parts[1:]:
  seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',part)
  ident=lesson+'/'+seg[0].split('## task: ')[1].split(' |')[0]
  item={'prompt':[seg[0]]}
  for kind,body in zip(seg[1::2],seg[2::2]):item.setdefault(kind,[]).append(body)
  tasks[ident]=item
 questions={}; n=collections.Counter()
 for m in re.finditer(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',parts[0]):
  kind=m[1];n[kind]+=1;questions[f'{lesson}/{kind}/{n[kind]}']=m[0]
 return parts,tasks,questions

orig={};new={};oq={};nq={};source_hashes={};theory_changes=[];figures=[];keys={};hints={}
for p in sorted((ROOT/'content/ch13').glob('*.md')):
 old=(W/'original/content/ch13'/p.name).read_text();actual=p.read_text()
 op,ot,qq=parse(old,p.stem);np,nt,qqn=parse(actual,p.stem)
 orig.update(ot);new.update(nt);oq.update(qq);nq.update(qqn)
 source_hashes[str(p.relative_to(ROOT))]=sha(p)
 if op[0]!=np[0]:theory_changes.append(p.stem)
 for m in re.finditer(r'(?ms)^::: figure ([\w-]+)\s*\n(.*?)^:::[ \t]*$',np[0]):figures.append({'lesson':p.stem,'figure':m[1],'caption':m[2].strip()})
 # Suppress disclosure until the separate open answer is written.
 public=re.sub(r'(?s)<details>.*?</details>','\n[Разбор скрыт до собственного ответа.]\n',np[0])
 count=collections.Counter()
 def question(m):
  kind=m[1];count[kind]+=1;ident=f'{p.stem}/{kind}/{count[kind]}'
  lines=[l for l in m[0].splitlines() if not l.strip().startswith('>') and not l.startswith('Почему:')]
  positions=[j for j,v in enumerate(lines) if re.match(r'^- \[[ x]\] ',v)]
  choices=[re.sub(r'^- \[[ x]\] ', '',lines[j]) for j in positions]
  marked=[k for k,j in enumerate(positions) if lines[j].startswith('- [x] ')]
  require(len(marked)==1,'exactly one answer '+ident)
  order=list(range(len(positions)));random.Random('nov17-retake-'+ident).shuffle(order)
  keys[ident]={'answer':order.index(marked[0])+1,'original_order':[i+1 for i in order]}
  for k,j in enumerate(positions):lines[j]=f'{k+1}. '+choices[order[k]]
  lines[0]='Вопрос '+ident
  return '\n'.join(lines[:-1])
 public=re.sub(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',question,public)
 if p.stem=='test':
  pos=public.index('Вопрос test/'); front=public[:pos];front=re.sub(r'(?s)^---\n.*?\n---\n','',front)
  (T/'test-open.md').write_text(front);public=public[pos:]
 for ident,item in nt.items():
  public+='\n'+item['prompt'][0]
  for body in item.get('starter',[]):public+='\n### Заготовка\n'+body
  for body in item.get('parsons',[]):
   blocks=[l.strip() for l in body.splitlines() if l.strip() and not l.startswith('```')]
   random.Random('nov17-retake-'+ident).shuffle(blocks)
   public+='\nДоступные строки для сборки с отступами:\n'+'\n'.join(blocks)+'\n'
  hints[ident]=[b.strip() for b in item.get('hint',[])]
 require(not re.search(r'(?m)^### (?:setup|check|hint|solution|explain)\b',public),'private sections leaked')
 require('- [x]' not in public and '- [ ]' not in public,'quiz markings leaked')
 (T/p.name).write_text(public)
require(set(orig)==set(new),'task ID sets unchanged')
require(set(oq)==set(nq),'question ID sets unchanged')
changes=[]
for ident in sorted(new):
 fields=sorted(k for k in set(orig[ident])|set(new[ident]) if orig[ident].get(k)!=new[ident].get(k))
 if fields:changes.append({'id':ident,'changed_sections':fields,'before':{k:[digest(v) for v in orig[ident].get(k,[])] for k in fields},'after':{k:[digest(v) for v in new[ident].get(k,[])] for k in fields}})
qchanges=[{'id':k,'before_sha256':digest(oq[k]),'after_sha256':digest(nq[k])} for k in sorted(nq) if oq[k]!=nq[k]]
def qfields(text):
 lines=text.splitlines();positions=[i for i,l in enumerate(lines) if re.match(r'^- \[[ x]\] ',l)]
 choices=[];explanations=[];right=[]
 for j,i in enumerate(positions):
  choices.append(re.sub(r'^- \[[ x]\] ','',lines[i]))
  explanations.append('\n'.join(lines[i+1:positions[j+1] if j+1<len(positions) else len(lines)-1]))
  if lines[i].startswith('- [x] '):right.append(j)
 return {'header':lines[0],'prompt':'\n'.join(lines[1:positions[0]]),'choices':choices,'explanations':explanations,'right_positions':right}
question_inventory=[]
for ident in sorted(nq):
 a,c=qfields(oq[ident]),qfields(nq[ident])
 question_inventory.append({'id':ident,'changed_fields':[k for k in a if a[k]!=c[k]],'before':a,'after':c,'selected':ident in {x['id'] for x in qchanges} or ident.startswith('test/')})
# Independently compare executable task field names in the actual export.
be={r['lesson'][5:]+'/'+r['id']:r for r in read(D/'technical/baseline-export.json') if r['kind']=='task'}
export_path=W/'final.json'
require(sha(export_path)=='681571ca57c423abd8148c43d07607ab8a9f0f3c3b6b8e7975a54b95e0f4b8d3','root final export SHA')
ae={r['lesson'][5:]+'/'+r['id']:r for r in read(export_path) if r['kind']=='task' and r['lesson'].startswith('ch13/')}
require(set(be)==set(ae)==set(new),'export/source task sets')
export_changes={k:sorted(f for f in set(be[k])|set(ae[k]) if be[k].get(f)!=ae[k].get(f)) for k in be if be[k]!=ae[k]}
source_check={x['id'] for x in changes if 'check' in x['changed_sections']}
export_check={k for k,v in export_changes.items() if 'check' in v}
require(source_check==export_check,'source/export check diff parity')
# Every final question is an addressable retake target even if unchanged.
selected_tasks=[x['id'] for x in changes]
selected_questions=sorted({x['id'] for x in qchanges}|{k for k in nq if k.startswith('test/')})
selection={'status':'HOLD pending root FINALREADY; never dispatch from this script','task_IDs':selected_tasks,'question_IDs':selected_questions,'count':len(selected_tasks)+len(selected_questions),'task_count':len(selected_tasks),'question_count':len(selected_questions),'reason':'every task with changed prompt/setup/starter/check/solution/hints/explain/Parsons; every changed embedded/predict; all 14 final questions','source_sha256':source_hashes,'final_export_sha256':sha(export_path),'export_path':str(export_path),'revised_export_sha256':sha(W/'revised.json')}
# Extra code cell sources must stay literally identical to the frozen baseline.
extra={}
(T/'extra').mkdir(exist_ok=True);(T/'own-previous').mkdir(exist_ok=True)
for name in ['ch13-pymorphy3.ipynb','ch13-transformers.ipynb']:
 old=read(W/'original/site/notebooks/extra'/name);now=read(ROOT/'site/notebooks/extra'/name)
 oc=[source(c['source']) for c in old['cells'] if c['cell_type']=='code'];nc=[source(c['source']) for c in now['cells'] if c['cell_type']=='code']
 require(oc==nc,'extra code source exact '+name)
 extra[name]={'code_cells':len(nc),'all_code_source_byte_equal_baseline':True,'old_code_sha256':[digest(c) for c in oc],'current_markdown_sha256':digest('\n'.join(source(c['source']) for c in now['cells'] if c['cell_type']=='markdown'))}
 shutil.copyfile(ROOT/'site/notebooks/extra'/name,T/'extra'/name)
 shutil.copyfile(D/'student'/name,T/'own-previous'/name)
for name in ['project-template.ipynb','knowledge.md','own-letter.md','own-scored.csv','own-monthly.csv','own-weekly.csv','own-audit.csv','own-quotes.csv']:
 shutil.copyfile(D/'student'/name,T/'own-previous'/name)
for name in ['requirements.txt','check_notebook.py','project-template.ipynb','submit.py']:
 shutil.copyfile(W/'student'/name,T/name)
shutil.copyfile(D/'student/knowledge.md',T/'previous-knowledge.md')
shutil.copyfile(D/'business-transfer-prompt.md',T/'transfer-open.md')
(T/'data').mkdir(exist_ok=True)
for p in sorted((D/'technical/data-baseline').glob('*.csv')):shutil.copyfile(p,T/'data'/p.name)
# No secret result expectations in the public target list.
(T/'targets.json').write_text(json.dumps({'tasks':selected_tasks,'questions':selected_questions},ensure_ascii=False,indent=2)+'\n')
js(W/'keys-retest.json',keys);js(W/'hints-retest.json',hints);js(W/'figures-retest.json',figures)
require(len(figures)==19 and len({f['figure'] for f in figures})==19,'19 current figures')
(T/'figures').mkdir(exist_ok=True)
(T/'figures/README.md').write_text('# Актуальные опубликованные схемы главы 13\n\n'+'\n'.join('- '+f['lesson']+': '+f['figure']+'.png — '+f['caption'] for f in figures)+'\n')
(T/'README.md').write_text('''# Адресное повторное прохождение главы 13

Начинайте только после сообщения координатора о готовности пакета и свободном CPU. Работайте в новом fixes/student/retest, исходный student не меняйте. Входы: этот публичный каталог и собственные прошлые записи в own-previous. Не читайте отчёты критиков, служебные каталоги, ключи, проверки и авторские решения вне пакета.

Сначала сохраните собственное решение transfer-open.md, прежде чем читать 05-project.md. До вариантов test.md сохраните самостоятельный ответ test-open.md. Затем прочитайте актуальные intro и девять уроков в порядке 01-text-prep, 01b-lemmas, 02-tfidf, 03-classify, 03b-labels, 04-embeddings, 04b-transformers, 04c-llm, 05-project. Откройте 19 текущих PNG из figures и подписи. Просмотрите новую подачу обоих extra. Цели повторной сдачи перечислены в targets.json: выполните все указанные задачи, вопросы и весь итоговый тест. Остальная теория доступна как справка.

До каждой отправки запишите Q1 (цель), Q2 (какое действие доступно и где объяснено), Q3 (ожидаемые значения, ключи, формы или единицы), после — полный Q4 и следующий шаг. Сначала собственная попытка; затем при необходимости одна UI-подсказка и новое действие. Первые input/feedback не переписывайте. Отличайте свою ошибку от дефекта курса и ограничение среды от учебной ошибки; не выдумывайте эмоции или темп человека.

Helper submit.py целиком заменяет содержимое редактора. В code включайте нужные imports и видимые строки starter: отдельного автоматического дополнения ими нет. Формат JSONL задачи: lesson, task, code, expect, Q1, Q2, Q3. Формат вопроса: question (например, 01-text-prep/predict/1), choice из ЭТОГО пакета, expect и Q1–Q3. Запуск: python3 submit.py input.jsonl > feedback.jsonl. Подсказка: action=hint после собственной попытки. Сохраните полный raw feedback и картинки; откройте собственный график прежде описания. Оценочный aggregate пишет bridge, его не редактируйте.

В 04c/llm-check имя above_reference означает только сравнение нижней границы интервала ОДНОЙ accuracy с объявленной константой reference; это не интервал парной разницы двух моделей. Для парного сравнения следуйте отдельной карточке llm-same. Прежде сдачи перечитайте актуальные имена выходов и условия, даже если используете свой старый код.

Создайте НОВУЮ копию собственного проекта по текущему публичному брифу 05-project и сохраните исполнимый код с outputs, сводные и отдельное письмо. В письме обязательны оба периода с включением границы, числители и объёмы всех отзывов до/после, отдельные знаменатели тем, цитаты с исходным review_id и точное объяснение того, что они подтверждают. Проверьте смысл самого текста, включая дополнительные темы. Назовите операционное действие и ограничения источника меток. Независимая человеческая разметка реальных отзывов обоих периодов остаётся внешним ограничением, если таких данных нет. Выберите точку/неделю по собственной сводной. Своё прежнее решение можно использовать явно, не называть его новым слепым экспериментом.

Оба extra опубликованы с новой подачей, кодовые ячейки не изменились. Повторный инференс всех текстов и новое обучение для этого повтора НЕ требуются. Можно перенести свои прошлые выполненные outputs из own-previous в новую копию текущего extra и прямо подписать: расчёт выполнен ранее, новая подача прочитана сейчас. Различайте прежний расчёт, новые текстовые ответы и новые исполнения. Не приписывайте прежнему выводу статус нового запуска. Текстовые самостоятельные опыты выполняйте лишь если решите это сделать и явно укажите охват.

Платные API, новые загрузки весов и живой SDK не требуются. Для своего проекта дождитесь CPU-окна координатора, один процесс за раз, OMP/OPENBLAS/MKL=1. Статический check_notebook.py --no-run проверяет оформление, не заменяет реальное исполнение и приёмку делового вывода. Сохраните дневник, таблицу прочитано/переиспользовано/исполнено, собственные находки с устойчивыми ID, отчёт и обновлённую карточку знаний.
''')
js(P/'selection.json',selection)
js(P/'targets.json',{'baseline':read(D/'technical/baseline.json'),'source_sha256':source_hashes,'final_export_sha256':sha(export_path),'export_path':str(export_path),'current_HTML_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'site/ch13').glob('*.html'))},'changed_tasks':changes,'changed_questions':qchanges,'changed_theory_lessons':theory_changes,'export_changed_task_fields':export_changes,'source_export_check_diff_equal':True,'check_changed_IDs':sorted(source_check),'source_task_count':len(new),'student_inventory':{**{k:'task' for k in new},**{k:('final_quiz' if k.startswith('test/') else 'predict' if '/predict/' in k else 'quiz') for k in nq}},'all_task_fields_before_after_sha256':{k:{'before':{f:[digest(v) for v in vv] for f,vv in orig[k].items()},'after':{f:[digest(v) for v in vv] for f,vv in new[k].items()}} for k in sorted(new)},'all_questions':question_inventory,'question_count':len(nq),'extra_notebook_proof':extra,'selection':selection,'current_figure_sources':{f['figure']:sha(ROOT/'content/figures'/(f['figure']+'.svg')) for f in figures}})
manifest={str(p.relative_to(T)):sha(p) for p in T.rglob('*') if p.is_file()}
js(P/'public-package-manifest.json',{'status':'HOLD pending root FINALREADY; manifest reflects files existing at refresh time','root':str(T),'files':manifest,'file_count':len(manifest),'excluded_private':['keys-retest.json','hints-retest.json','private README','targets diff hashes','critic reports']})
# Confirm the original frozen learner artifacts after preparation.
original_manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (D/'student/SHA256SUMS').read_text().splitlines()}
require(all(sha(D/'student'/name)==h for name,h in original_manifest.items()),'73 original learner SHA remain unchanged')
print(json.dumps({'task_changes':len(changes),'changed_section_counts':dict(collections.Counter(k for x in changes for k in x['changed_sections'])),'check_changed_count':len(source_check),'check_changed_IDs':sorted(source_check),'question_changes':[x['id'] for x in qchanges],'selection':{'tasks':len(selected_tasks),'questions':len(selected_questions),'total':selection['count']},'extra_code_cells':{k:v['code_cells'] for k,v in extra.items()},'figures':len(figures),'files_before_render':len(manifest)},ensure_ascii=False,indent=2))
