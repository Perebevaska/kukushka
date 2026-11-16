"""Capture the applied narrow revision without changing its frozen programs/expectations."""
import hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
base=json.loads((HERE/'refine-before-tasks.json').read_text());keys={t['lesson']+'/'+t['id'] for t in base}
if len(sys.argv)>1:
    source=Path(sys.argv[1]);tasks=[t for t in json.loads(source.read_text()) if t.get('kind')=='task' and t['lesson']+'/'+t['id'] in keys]
else:
    tasks=[]
    for t in base:
        t=dict(t);text=(ROOT/'content'/Path(t['lesson']).with_suffix('.md')).read_text()
        block=next(b for b in re.split(r'(?m)(?=^## task: )',text) if b.startswith('## task: '+t['id']+' |'))
        for field in ['setup','starter','check','solution']:
            m=re.search(r'(?m)^### '+field+r'\n```python\n(.*?)\n```',block,re.S);t[field]=m[1] if m else ''
        tasks.append(t)
assert len(tasks)==4
assert all("function=function" in t['setup'] for t in tasks if t['id']!='my-class')
assert any('almost' in t['check'] or 'мал' in t['check'] for t in tasks if t['id']=='my-class')
(HERE/'refine-after-tasks.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2))
info=dict(programs_sha256=hashlib.sha256((HERE/'refine-programs.jsonl').read_bytes()).hexdigest(),tasks_sha256=hashlib.sha256((HERE/'refine-after-tasks.json').read_bytes()).hexdigest(),source_files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'content/ch09/03b-own-model.md',ROOT/'content/ch09/02b-vectorize.md']})
(HERE/'refine-after-snapshot.json').write_text(json.dumps(info,indent=2))
print('Captured 4 after tasks; frozen 12 programs retained')
