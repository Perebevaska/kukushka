"""Freeze separately approved contract migrations and discriminating oracles, without execution."""
import json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=[json.loads(s) for s in (HERE/'programs.jsonl').read_text().splitlines()]
tasks={x['lesson']+'/'+x['id']:x for x in json.loads((HERE/'proposal-tasks.json').read_text())}
def row(id,key,description,code,expected,**extras):
 l,t=key.rsplit('/',1)
 return dict(id=id,lesson=l,task=t,description=description,code=code,expected=expected,code_sha256=hashlib.sha256(code.encode()).hexdigest(),**extras)
key='ch12/03b-time-split/check-order';original=next(x for x in old if x['id']=='C066')
oracle='''
_i=_pd.date_range('2026-01-01',periods=6,freq='h')
_z=_pd.DataFrame({'v':range(6)},index=_i)
assert bool(is_time_split(_z.iloc[[5,0]],_z.iloc[[4,3]])) is False, 'max(train)=05:00 is not before min(test)=03:00'
'''
supplement=[row('S001',key,'independent adversarial oracle for correct max/min',tasks[key]['solution'],True,oracle=oracle,oracle_expected=True),row('S002',key,'same C066 full code, independent oracle establishes wrong last/first result',original['code'],False,oracle=oracle,oracle_expected=False,original_id='C066')]
(HERE/'supplement-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in supplement))
rows=[]
def add(key,description,code,expected=True,**extra):rows.append(row('M'+str(len(rows)+1).zfill(3),key,description,code,expected,group='explicit-contract-migration',**extra))
for key in ['ch12/05-project/baseline','ch12/05-project/select','ch12/05-project/grid','ch12/03-features/leak-test','ch12/03b-time-split/month-folds','ch12/03-features/promo-feature']:
 add(key,'author adapted to explicit current public contract',tasks[key]['solution'])
key='ch12/05-project/select';s=tasks[key]['solution']
add(key,'unavailable last four July validation labels included',s.replace('y.index < "2026-07-31 20:00"','y.index < "2026-08-01"'),False)
add(key,'unavailable June fit labels included',s.replace('y.index < "2026-06-30 20:00"','y.index < "2026-07-01"'),False)
key='ch12/03-features/promo-feature';s=tasks[key]['solution']
add(key,'future Aug21 promo missing despite correct July scores',s.replace(', "2026-08-21"',''),False)
add(key,'10:00 incorrectly excluded',s.replace('(index.hour >= 10)','(index.hour > 10)'),False)
add(key,'20:00 incorrectly excluded',s.replace('(index.hour <= 20)','(index.hour < 20)'),False)
add(key,'alternative list-comprehension helper on future keys',s.replace('flags = index.normalize().isin(promo_days) & (index.hour >= 10) & (index.hour <= 20)\n    return pd.Series(flags.astype(int), index=index)','return pd.Series([int(t.normalize() in promo_days and 10 <= t.hour <= 20) for t in index],index=index)'),True)
add(key,'whole helper result rows permuted, timestamps preserved',s.replace('return pd.Series(flags.astype(int), index=index)','return pd.Series(flags.astype(int), index=index).iloc[::-1]'),True)
add(key,'timestamp labels permuted without their values',s.replace('return pd.Series(flags.astype(int), index=index)','out = pd.Series(flags.astype(int), index=index)\n    out.index = out.index[::-1]\n    return out'),False)
(HERE/'migration-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
# An additional contract phase is explicit; frozen expectations remain unchanged.
changes={
'C061':('promo helper now explicitly required',False),
'C095':('baseline now July740 rather than August',False),
'C097':('select now named availability masks and July740 score',False),
'C099':('grid now CV only, with no August rows supplied',False),
'C120':('leak_test now explicitly perturbs whole unknown tail',False),
'C121':('gap28 now explicit and grid has no August rows',False),
'C122':('month keys clarified as05/06/07',False)}
phase={r['id']:{'expected_original':r['expected'],'expected_current_contract':changes.get(r['id'],('',r['expected']))[1],'contract_change':changes.get(r['id'],('',r['expected']))[0] or None,'code_sha256':r['code_sha256']} for r in old}
(HERE/'expected-phase.json').write_text(json.dumps(phase,ensure_ascii=False,indent=2)+'\n')
files=['supplement-programs.jsonl','migration-programs.jsonl','expected-phase.json','proposal-tasks.json']
(HERE/'supplement-frozen.sha256').write_text(json.dumps({f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in files},indent=2)+'\n')
(HERE/'supplement-expected-before-execution.json').write_text(json.dumps({r['id']:{k:r.get(k) for k in ['expected','oracle_expected','code_sha256']} for r in supplement+rows},indent=2)+'\n')
print('Frozen separately',len(supplement),'oracles and',len(rows),'migrations; no program executed')
