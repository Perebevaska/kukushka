from pathlib import Path
import re,json,random,shutil,hashlib,subprocess,collections,datetime
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');W=Path('/private/tmp/kuch15round');D=R/'docs/reaudit-2026-11-16/ch15';T=W/'student'
for p in [D/'technical',D/'student',T,W/'jobs',W/'original']:p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
source=list((R/'content/ch15').glob('*.md'))+list((R/'site/ch15').glob('*.html'))+[R/'content/course.yaml',R/'site/assets/app.css',R/'site/assets/harness.py',R/'site/assets/app.js',R/'site/notebooks/ch15-practice.ipynb',R/'site/notebooks/project-template.ipynb',R/'site/notebooks/dsc.py',R/'site/notebooks/check_notebook.py',R/'tools/build.py',R/'tools/verify.mjs']
source=[p for p in source if p.exists()]
for p in source:
 q=W/'original'/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
exp=json.loads((W/'course.json').read_text());chapter=[x for x in exp if x['lesson'].startswith('ch15/')];dump(D/'technical/baseline-export.json',chapter)
files=sorted({f for x in chapter for f in x['files']})
for name in files:
 for folder in [W/'original/site/data',D/'technical/data-baseline',T/'data']:
  folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'site/data'/name,folder/name)
block=(R/'content/course.yaml').read_text().split('  - id: ch15\n')[1]
lessons=['intro']+re.findall(r'- \{id: ([^,]+),',block)+['test'];keys={};hints={};inventory={};figs=[]
for lesson in lessons:
 p=W/'original/content/ch15'/(lesson+'.md');s=p.read_text();parts=re.split(r'(?m)(?=^## task: )',s);counts={}
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
extra=T/'extra';extra.mkdir(exist_ok=True)
shutil.copyfile(R/'site/notebooks/project-template.ipynb',extra/'project-template.ipynb')
shutil.copyfile(R/'site/notebooks/requirements.txt',extra/'requirements.txt')
# Only visible theory, before any task marker: native snippets are public reading material.
for lesson in lessons:
 if lesson in ['intro','test']:continue
 theory=(W/'original/content/ch15'/(lesson+'.md')).read_text().split('## task: ')[0]
 blocks=re.findall(r'```(python|bash|dockerfile)[^\n]*\n(.*?)```',theory,re.S)
 for j,(lang,body) in enumerate(blocks,1):
  (extra/(lesson+'-visible-'+str(j)+{'python':'.py','bash':'.sh','dockerfile':'.Dockerfile'}[lang])).write_text(body)
(extra/'README.md').write_text('Публичные примеры извлечены дословно из теории до первой карточки. Зависимости/контекст берите из урока; это отдельные фрагменты, не самостоятельные полные скрипты. project-template.ipynb — опубликованный пустой шаблон, не практика с решениями. Собственный выпускной проект создавайте самостоятельно.\n')
for src,name in [(R/'docs/reaudit-2026-11-16/ch14/student/knowledge.md','knowledge-ch14.md'),(R/'docs/reaudit-2026-11-16/ch14/fixes/student/retest/knowledge.md','knowledge-ch14-retest.md'),(R/'docs/reaudit-2026-11-16/ch14/fixes/student/retest/holdout-correction.md','knowledge-ch14-accuracy.md')]:
 assert src.exists(),src;shutil.copyfile(src,T/name)
for old in ['/private/tmp/kuch14round/student/cognitive-walkthrough']:
 if Path(old).exists():shutil.copytree(old,T/'cognitive-walkthrough',dirs_exist_ok=True);break
else:raise RuntimeError('missing cognitive walkthrough')
helper=(Path('/private/tmp/kuch14round/student/submit.py')).read_text().replace('kuch14round','kuch15round');(T/'submit.py').write_text(helper)
dump(W/'keys.json',keys);dump(W/'hints.json',hints);dump(W/'figures.json',figs);dump(D/'technical/inventory.json',inventory)
baseline={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':{str(p.relative_to(R)):sha(p) for p in source},'data_sha256':{f:sha(R/'site/data'/f) for f in files},'full_export_sha256':sha(W/'course.json'),'technical_kinds':dict(collections.Counter(x['kind'] for x in chapter)),'student_kinds':dict(collections.Counter(inventory.values())),'lesson_order':lessons,'figures':figs,'local_examples':[str(p.relative_to(T)) for p in extra.iterdir()],'execution':'stdlib-only preparation; no browser/ML/notebook execution'};dump(D/'technical/baseline.json',baseline)
(T/'README.md').write_text("""# Самостоятельное прохождение главы 15

Порядок: intro,01-artifact,02-service,02b-service-run,03-experiments,04-deploy,05-project,06-final-project,test-open,test. Основной маршрут после главы8:01-artifact+06-final-project; остальные уроки — полный маршрут. Прочтите весь видимый материал и PNG figures/, пройдите все уровни карточек, predict,quiz и итоговый тест. Скрытые setup/check/solution/explain и ключи удалены, Parsons и варианты перемешаны. Данные лежат в data/, публичные фрагменты/шаблон в extra/. Practice notebook не передаётся: содержит решения.

Cognitive Walkthrough: cognitive-walkthrough/, исходник https://github.com/mastepanoski/claude-skills/blob/main/skills/cognitive-walkthrough/SKILL.md . До отправки сохраните Q1 цель,Q2 доступное действие и где объяснено,Q3 ожидаемые значения/ключи/формы/единицы; после Q4 полную реакцию и следующий шаг. До вариантов test.md запишите ответ на test-open.md. Не выдумывайте ошибки или человеческое время.

Сохраняйте собственные попытки/дневник/knowledge/report и независимый выпускной в docs/reaudit-2026-11-16/ch15/student/. JSONL задачи:lesson,task,code,expect,Q1,Q2,Q3; вопрос:question вида 01-artifact/predict/1 или /quiz/1,choice по нумерации пакета,expect,Q1–Q3. Отправка python3 /private/tmp/kuch15round/student/submit.py input.jsonl > feedback.jsonl . Код целиком заменяет редактор, включите импорты/starter. action=hint только по одной после собственной попытки, помощь учтите. Bridge ведёт отдельный initial-attempts.jsonl: не редактировать. Собственные рисунки открывайте по visible_images.

Обязательно создайте полный самостоятельный final_project.ipynb и локальный репозиторий B2B из office.db: общий код признаков/цели, честный выбор минимум трёх семейств моделей и ориентир, поздний тест, календарные границы и зрелость меток, денежное решение, собственные пояснения/графики/README, score.py, окружение, модель/паспорт/20 golden строк/список. Выполните публичный бриф 06-final-project целиком; семь браузерных разминок не являются сдачей репозитория. Подготовьте комплект к передаче другому аналитику с новым лимитом3 без исходного блокнота. Отдельно сохраните собственную записку по инциденту. Определяйте политику и критерий до раскрытия позднего теста.

Только собственные knowledge-ch14*.md доступны как перенос. До любых сдач и локального ML дождитесь окна root: одна тяжёлая задача, OMP/OPENBLAS/MKL=1. Среда /private/tmp/ku-audit/nb-env/bin/python. Не запускать параллельные ML, новые сетевые установки или загрузки. Нативные FastAPI/MLflow и Docker фиксируйте раздельно по фактическому исполнению. GitHub публикацию не выполнять. После главы до чужих выводов назовите три вещи, которые изменили бы начиная курс заново: пример главы и ожидаемый эффект следующему ученику.
""")
# Metadata stays outside public student directory.
dump(W/'public-package-manifest.json',{'files':{str(p.relative_to(T)):sha(p) for p in T.rglob('*') if p.is_file()},'png_status':'pending root light render'})
print(json.dumps({k:baseline[k] for k in ['head','technical_kinds','student_kinds','lesson_order','data_sha256','local_examples']},ensure_ascii=False,indent=2));print('figures',len(figs))
