from pathlib import Path
import re,json,random,shutil,hashlib,subprocess,collections,datetime
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');W=Path('/private/tmp/kuch14round');D=R/'docs/reaudit-2026-11-16/ch14';T=W/'student'
for p in [D/'technical',D/'student',T,W/'jobs',W/'original']:p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
source=list((R/'content/ch14').glob('*.md'))+list((R/'site/ch14').glob('*.html'))+[R/'content/course.yaml',R/'site/assets/app.css',R/'site/assets/harness.py',R/'site/assets/app.js',R/'site/notebooks/ch14-practice.ipynb',R/'site/notebooks/compare_showcase_features.py']
source=[p for p in source if p.exists()]
for p in source:
 q=W/'original'/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
exp=json.loads((W/'course.json').read_text());chapter=[x for x in exp if x['lesson'].startswith('ch14/')];dump(D/'technical/baseline-export.json',chapter)
files=sorted({f for x in chapter for f in x['files']})
for name in files:
 for folder in [W/'original/site/data',D/'technical/data-baseline',T/'data']:
  folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'site/data'/name,folder/name)
block=(R/'content/course.yaml').read_text().split('  - id: ch14\n')[1].split('  - id: ch15\n')[0]
lessons=['intro']+re.findall(r'- \{id: ([^,]+),',block)+['test'];keys={};hints={};inventory={};figs=[]
for lesson in lessons:
 p=W/'original/content/ch14'/(lesson+'.md');s=p.read_text();parts=re.split(r'(?m)(?=^## task: )',s);counts={}
 def question(m):
  kind=m[1];k=counts[kind]=counts.get(kind,0)+1;ident=f'{lesson}/{kind}/{k}';inventory[ident]='final' if lesson=='test' else kind
  lines=[l for l in m[0].splitlines() if not l.strip().startswith('>') and not l.startswith('Почему:')];pos=[j for j,v in enumerate(lines) if re.match('^- ',v)]
  options=[re.sub(r'^- (?:\[[ x]\] )?','',lines[j]) for j in pos];marked=[k for k,j in enumerate(pos) if lines[j].startswith('- [x] ')];assert len(marked)==1,(ident,marked)
  order=list(range(len(pos)));random.Random('nov17'+ident).shuffle(order);keys[ident]={'answer':order.index(marked[0])+1,'original_order':[z+1 for z in order]}
  for k,j in enumerate(pos):lines[j]=str(k+1)+'. '+options[order[k]]
  lines[0]='Вопрос '+ident;return '\n'.join(lines[:-1])
 text=re.sub(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',question,parts[0])
 if lesson=='test':
  at=text.index('Вопрос test/');(T/'test-open.md').write_text(text[:at]);text=text[at:]
 for part in parts[1:]:
  seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',part);text+='\n'+seg[0];ident=seg[0].split('## task: ')[1].split(' |')[0];inventory[lesson+'/'+ident]='task';hh=[]
  for kind,body in zip(seg[1::2],seg[2::2]):
   if kind=='starter':text+='\n### Заготовка\n'+body
   if kind=='hint':hh.append(body.strip())
   if kind=='parsons':
    ls=[l.strip() for l in body.splitlines() if l.strip() and not l.startswith('```')];random.Random('nov17'+ident).shuffle(ls);text+='\nДоступные строки для сборки с отступами:\n'+'\n'.join(ls)+'\n'
  hints[lesson+'/'+ident]=hh
 for figure in re.findall(r'^::: figure\s+([^\s|]+)',text,re.M):figs.append({'lesson':lesson,'figure':figure})
 assert not re.search(r'^### (check|hint|solution|setup|explain)\s*$',text,re.M),lesson
 assert '- [x]' not in text,lesson
 (T/p.name).write_text(text)
for x in figs:
 p=R/'content/figures'/(x['figure']+'.svg');q=W/'original/content/figures'/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);source.append(p)
extra=T/'extra';extra.mkdir(exist_ok=True);shutil.copyfile(R/'site/notebooks/compare_showcase_features.py',extra/'compare_showcase_features.py')
# The local CNN is a visible teaching example, not a hidden task solution.
s=(W/'original/content/ch14/04-cnn.md').read_text().split('## task: ')[0]
blocks=re.findall(r'```python[^\n]*\n(.*?)```',s,re.S);cnn=[b for b in blocks if 'import torch' in b and '25' in b];assert len(cnn)==1
(extra/'cnn-visible-example.py').write_text(cnn[0]);(extra/'README.md').write_text('Публичные локальные опыты: cnn-visible-example.py дословно извлечён из теории 04-cnn; compare_showcase_features.py скачивается из 04b-transfer. Для них используются NPZ из ../data. Собственные выводы и выполненные части сохраняйте отдельно. До исполнения дождитесь CPU-окна; сеть для новых загрузок не используйте.\n')
for src,name in [(R/'docs/reaudit-2026-11-16/ch13/fixes/student/retest/knowledge.md','knowledge-ch13.md'),(R/'docs/reaudit-2026-11-16/ch13/fixes/student/weekly-closure-2/knowledge-addendum.md','knowledge-ch13-addendum.md')]:
 assert src.exists(),src;shutil.copyfile(src,T/name)
for old in ['/private/tmp/kuch13round/student/cognitive-walkthrough','/private/tmp/kuch12round/student/cognitive-walkthrough']:
 if Path(old).exists():shutil.copytree(old,T/'cognitive-walkthrough',dirs_exist_ok=True);break
else:raise RuntimeError('missing cognitive walkthrough')
helper=(Path('/private/tmp/kuch13round/student/submit.py')).read_text().replace('kuch13round','kuch14round');(T/'submit.py').write_text(helper)
dump(W/'keys.json',keys);dump(W/'hints.json',hints);dump(W/'figures.json',figs);dump(D/'technical/inventory.json',inventory)
baseline={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':{str(p.relative_to(R)):sha(p) for p in source},'data_sha256':{f:sha(R/'site/data'/f) for f in files},'full_export_sha256':sha(W/'course.json'),'technical_kinds':dict(collections.Counter(x['kind'] for x in chapter)),'student_kinds':dict(collections.Counter(inventory.values())),'lesson_order':lessons,'figures':figs,'local_examples':['extra/cnn-visible-example.py','extra/compare_showcase_features.py'],'execution':'stdlib-only preparation; no browser/ML/notebook execution'};dump(D/'technical/baseline.json',baseline)
(T/'README.md').write_text('''# Самостоятельное прохождение главы 14

Порядок: '''+', '.join(lessons[:-1])+''', test-open, test. Прочитайте теорию и все PNG в figures/, пройдите все уровни карточек, predict, встроенные вопросы и итоговый тест. Авторские проверки, setup, решения и объяснения убраны; Parsons и варианты перемешаны. Открытые примеры теории сохранены. Данные NPZ находятся в data/. Локальные дополнительные опыты — в extra/; отдельного опубликованного extra14.ipynb нет.

Применяйте Cognitive Walkthrough из cognitive-walkthrough/. До каждой отправки сохраните Q1: цель; Q2: доступное действие и где объяснено; Q3: ожидаемые значения, ключи, формы и единицы. После сохраните Q4: полную реакцию и следующий шаг. Не выдумывайте ошибки или время человека. До вариантов test.md запишите свой ответ на test-open.md.

Свои code/input/feedback, walkthrough, knowledge и отчёт сохраняйте в docs/reaudit-2026-11-16/ch14/student/. Первые попытки не переписывайте. JSONL задания: lesson, task, code, expect, Q1, Q2, Q3; вопрос: question вида 01-pixels/predict/1 или /quiz/1, choice из этого пакета, expect, Q1–Q3. Отправка: python3 /private/tmp/kuch14round/student/submit.py input.jsonl > feedback.jsonl. Code целиком заменяет редактор, поэтому включите импорты и видимый starter. Подсказку action=hint открывайте по одной после собственной попытки и учитывайте помощь. Bridge ведёт отдельный initial-attempts.jsonl; его не редактируйте. Собственный рисунок откройте по visible_images перед описанием.

Используйте только свои перенесённые знания ch13. До любых сдач и локальных ML/CNN/ResNet дождитесь CPU-окна root; одновременно только одна тяжёлая задача, OMP/OPENBLAS/MKL=1 и torch threads1. Новые большие загрузки весов не запускайте. Отделите прочитанное от реально исполненного. Кроме карточек сделайте собственную работу по публичному брифу 05-project: выбор правила до второго дня, оценка событий по времени и ячейке, сценарии целого дня, письмо пекарю с ограничениями. Сохраните свой код/выводы/рисунки. Публикуемый practice notebook содержит решения, поэтому вам не передаётся.
''')
# Metadata stays outside public student directory.
dump(W/'public-package-manifest.json',{'files':{str(p.relative_to(T)):sha(p) for p in T.rglob('*') if p.is_file()},'png_status':'pending root light render'})
print(json.dumps({k:baseline[k] for k in ['head','technical_kinds','student_kinds','lesson_order','data_sha256','local_examples']},ensure_ascii=False,indent=2));print('figures',len(figs))
