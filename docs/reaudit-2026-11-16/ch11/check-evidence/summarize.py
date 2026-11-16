import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent;phase=sys.argv[1]
summary={'phase':phase,'bundles':{}}
for suffix in ['', '-supplement']:
 names=[phase+suffix+'-'+env for env in ['native','pyodide']]
 if not all((p/(n+'.jsonl')).exists() for n in names):continue
 rows=[[json.loads(s) for s in (p/(n+'.jsonl')).read_text().splitlines()] for n in names]
 assert len(rows[0])==len(rows[1])
 parity=[]
 for a,b in zip(*rows):
  assert a['id']==b['id'] and a['code']==b['code'] and a['expected']==b['expected']
  parity.append(dict(id=a['id'],expected=a['expected'],native=a['passed'],pyodide=b['passed'],same=a['passed']==b['passed']))
 summary['bundles'][suffix or 'main']={'count':len(parity),'normative_matches':{env:sum(r['expected']==r[env] for r in parity) for env in ['native','pyodide']},'verdict_parity':sum(r['same'] for r in parity),'mismatches':[r for r in parity if r['native']!=r['expected'] or r['pyodide']!=r['expected']], 'public_helper_guard_rejections':{env:[dict(id=r['id'],error_type=r['error'].get('type'),source='public helper open_blur_labels',message=r['error'].get('text'),expected_rejection=r['expected'] is False) for r in results if isinstance(r.get('error'),dict) and r['error'].get('type')=='AssertionError' and 'open_blur_labels(' in r['error'].get('text','')] for env,results in zip(['native','pyodide'],rows)}}
(p/(phase+'-summary.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
