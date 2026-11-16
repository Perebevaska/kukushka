from pathlib import Path
import json
D=Path(__file__).parent
lessons=['01-resample','02-decompose','03-features','03b-time-split','04-forecast','05-project','test']
first=[];events=[]
for l in lessons:
 p=D/(l+'.feedback.jsonl');r=[json.loads(x) for x in p.read_text().splitlines()]
 first.extend(r)
 files=[p]+sorted(D.glob(l+'.*.feedback.jsonl'))
 for f in files:
  inf=f.with_name(f.name.replace('.feedback.','.input.'))
  inputs=[json.loads(x) for x in inf.read_text().splitlines()] if inf.exists() else []
  for i,feedback in enumerate(json.loads(x) for x in f.read_text().splitlines()):
   inp=inputs[i] if i<len(inputs) else {}
   event={'input_file':inf.name,'raw_feedback_file':f.name,'input':inp,'Q4':feedback}
   if feedback.get('passed'): event['next_step']='Переход к следующей карточке; select contract-probe остаётся замечанием о cutoff, не корректным native решением.' if feedback.get('id')=='05-project/select' else 'Принято; перейти дальше.'
   elif 'hint' in feedback: event['next_step']='Помощь учтена; использовать только для отдельной попытки.'
   else: event['next_step']='Сохранить исходный отказ; исправление отдельно, см. diary и ownfindings.'
   events.append(event)
 # Полный Q4 по уроку; raw feedback при этом не трогаю
 out=[e for e in events if e['raw_feedback_file'].startswith(l+'.')]
 (D/(l+'.walkthrough.jsonl')).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out))
final={}
for f in D.glob('*.feedback.jsonl'):
 for line in f.read_text().splitlines():
  r=json.loads(line)
  if r.get('passed'):final[r['id']]=True
stats={'unique_initial_ids':len(first),'initial_passed_events':sum(r.get('passed') is True for r in first),'initial_browser_errors':sum('browserError' in r for r in first),'initial_graded_failures':sum(r.get('passed') is False for r in first),'initial_graded_count':sum('passed' in r for r in first),'eventual_accepted_unique':len(final),'hints_used':['05-project/select hint1','05-project/grid hint1'],'contract_probe_not_correct_solution':['05-project/select'],'per_lesson':{l:{'ids':sum(r['id'].startswith(l+'/') for r in first),'first_event_pass':sum(r['id'].startswith(l+'/') and r.get('passed') is True for r in first)} for l in lessons}}
(D/'attempt-statistics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print(json.dumps(stats,ensure_ascii=False,indent=2))
