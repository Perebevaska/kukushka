import json
from pathlib import Path
B=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch14/technical/checks');tasks=json.loads((B/'tasks.json').read_text());runs={}
for phase in ['before','after']:
 for rt in ['native','pyodide']:
  p=B/f'{phase}-{rt}.jsonl';runs[phase,rt]=list(map(json.loads,p.read_text().splitlines())) if p.exists() else []
result=[];md=['# Покрытие 61 task до и после редакции','','`N/P` — CPython/Pyodide; `T` зачёт, `F` отказ. Автор/ALT ожидают T/T, ошибочная программа ожидает F/F. У Parsons изменённый код — harness-only. Старые программы и ожидания не менялись.','','| Task | Публичная цель/метод сверены | Author N/P before → after | ALT N/P before → after | Ошибка N/P before → after |','|---|---|---|---|---|']
def pair(key,label,phase):
 found=[]
 for rt in ['native','pyodide']:
  r=next((r for r in runs[phase,rt] if (r['lesson'],r['task'],r['label'])==(*key,label)),None);found.append('—' if r is None else 'T' if r['passed'] else 'F')
 return '/'.join(found)
for t in tasks:
 key=(t['lesson'],t['id']);row={'lesson':key[0],'task':key[1],'public_condition_hint_method_reviewed':True,'programs':{}}
 for label in ['author','other_correct','plausible_wrong']:
  row['programs'][label]={phase:{rt:next(({'index':r['index'],'passed':r['passed'],'expected':r['expected'],'stage':r['stage']} for r in runs[phase,rt] if (r['lesson'],r['task'],r['label'])==(*key,label)),None) for rt in ['native','pyodide']} for phase in ['before','after']}
 result.append(row);md.append('| '+key[0]+'/'+key[1]+(' H' if key[1].startswith('p-') else '')+' | Да | '+' | '.join(pair(key,label,'before')+' → '+pair(key,label,'after') for label in ['author','other_correct','plausible_wrong'])+' |')
(B/'coverage61-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(B/'coverage61-after.md').write_text('\n'.join(md)+'\n');print('after coverage61 updated')
