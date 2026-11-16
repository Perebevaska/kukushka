from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).parent;P=Path('/private/tmp/kuch13round/student-retest')
lessons=['01-text-prep','01b-lemmas','02-tfidf','03-classify','03b-labels','04-embeddings','04b-transformers','04c-llm','05-project','questions']
text=['# Cognitive Walkthrough адресного повтора\n\nЗнакомая глава; использованы только текущий публичный пакет и собственные прежние результаты. Q1–Q3 сохранены до отправки, ниже полная Q4. Это аналитическое прохождение AI-агента, не эмпирический тест с людьми.\n']
feedback_all=[]
for lesson in lessons+['05-project.weekly-retry']:
 iname='04c-llm.submit' if lesson=='04c-llm' else lesson
 inputs=[json.loads(x) for x in (D/(iname+'.input.jsonl')).read_text().splitlines()]
 feedback=[json.loads(x) for x in (D/(lesson+'.feedback.jsonl')).read_text().splitlines()]
 assert len(inputs)==len(feedback)
 feedback_all+=feedback
 for r,f in zip(inputs,feedback):
  text.append('\n## '+f['id']+' — '+iname+'\n\n')
  for q in ['Q1','Q2','Q3']:text.append('**'+q+'.** '+r[q]+'\n\n')
  text.append('**Q4 — полный фактический ответ.**\n\n```json\n'+json.dumps(f,ensure_ascii=False,indent=2)+'\n```\n\n')
  if f.get('passed'):
   step='Принято, продолжить.'
   if f['id']=='05-project/weekly':step+=' Реальный PNG открыт: столбцы показывают повышение доли KZN-2 с недели 5 октября. Даты и доли сохранены.'
  else:step='Мой pandas bar вызвал ValueError Must supply freq for datetime value. PNG открыт: пустые оси. Без подсказки использую прямой ax.bar; исходная попытка сохраняется, исправление отдельное. Причину внутри библиотеки не исследовал, дефектом курса не объявляю.'
  text.append('**Следующий шаг.** '+step+'\n')
  for path in f.get('visible_images',[]):
   out=D/'images'/Path(path).name;out.parent.mkdir(exist_ok=True);shutil.copy2(path,out)
(D/'walkthrough.md').write_text(''.join(text))
ids={f['id'] for f in feedback_all};first={}
for f in feedback_all:first.setdefault(f['id'],f)
stats=dict(unique=len(ids),graded_attempts=sum(isinstance(f.get('passed'),bool) for f in feedback_all),raw=len(feedback_all),true=sum(f.get('passed') is True for f in feedback_all),false=sum(f.get('passed') is False for f in feedback_all),first_pass=sum(f.get('passed') is True for f in first.values()),hints=0,transport=sum('browserError' in f for f in feedback_all))
assert set(json.loads((P/'targets.json').read_text())['tasks']+json.loads((P/'targets.json').read_text())['questions'])==ids
(D/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(stats)
# evidence hashes of current sources and reused own previous notebooks, no external reads
sources=[P/'intro.md',P/'targets.json',P/'transfer-open.md',P/'test-open.md',P/'test.md']+sorted(P.glob('0*.md'))+sorted((P/'extra').glob('*.ipynb'))
(D/'public-source-sha256.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p)+'\n' for p in sources))
