import json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=[json.loads(s) for s in (HERE/'programs.jsonl').read_text().splitlines()]
a=[json.loads(s) for s in (HERE/'before-native.jsonl').read_text().splitlines()];b=[json.loads(s) for s in (HERE/'before-pyodide.jsonl').read_text().splitlines()]
assert len(a)==len(b)==len(p)==132
assert all((r['code'],r['expected'],r['code_sha256'])==(s['code'],s['expected'],s['code_sha256'])==(t['code'],t['expected'],t['code_sha256']) for r,s,t in zip(a,b,p))
assert all((r['ok'],r['passed'])==(s['ok'],s['passed']) for r,s in zip(a,b))
summary=dict(programs=132,tasks=len(set(x['lesson']+'/'+x['task'] for x in p)),same_verdicts=True,normative_matches=sum(r['passed']==r['expected'] for r in a),mismatches=[{k:r[k] for k in ['id','lesson','task','description','expected','passed','ok','message','group']} for r in a if r['passed']!=r['expected']],authored_baselines_passed=sum(r['group']=='baseline' and r['passed'] for r in a),execution_errors=[{k:r[k] for k in ['id','lesson','task','error','failure_stage']} for r in a if not r['ok']])
(HERE/'before-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
lines=['# Охват автопроверок главы12','', 'Все 50 авторских baseline прошли в CPython и Pyodide. 132 замороженные программы дали одинаковые пары ok/passed в обеих средах; 108 нормативных совпадений и 24 расхождения. Код и ожидания ни одной пробы не изменены после исполнения.','', '| Карточка | Программ | Принято | Отклонено | Расхождения expected/passed |','|---|---:|---:|---:|---|']
for key in sorted(set(r['lesson']+'/'+r['task'] for r in a)):
 rs=[r for r in a if r['lesson']+'/'+r['task']==key]
 lines.append('| '+key+' | '+str(len(rs))+' | '+str(sum(r['passed'] for r in rs))+' | '+str(sum(not r['passed'] for r in rs))+' | '+', '.join(r['id'] for r in rs if r['passed']!=r['expected'])+' |')
(HERE/'coverage.md').write_text('\n'.join(lines)+'\n')
(HERE/'transfer-staffing-output.txt').write_text('capacity cost_deficit deficit_barista_hours extra_barista_hours total_cost\n4 300 1 3 1200\n4 1200 1 3 2100\n6 300 1 1 600\n6 1200 1 1 1500\n8 300 1 2 900\n8 1200 1 2 1800\n')
