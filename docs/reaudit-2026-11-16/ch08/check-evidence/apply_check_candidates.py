"""Print a proposed Markdown diff; only --apply writes selected check blocks.

Default excludes the final project, whose implementation belongs to the expert.
Usage: python apply_check_candidates.py [--apply] [lesson/id ...]
"""
import difflib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
apply='--apply' in sys.argv
keys=[x for x in sys.argv[1:] if not x.startswith('--')]
if not keys:keys=['01-value/p-profit','02-budget/gains-plot','04-monitoring/p-monitor','05-explain/p-pd']
tasks={t['lesson'].split('/')[-1]+'/'+t['id']:t for t in json.loads((HERE/'tasks-proposed.json').read_text())}
grouped={}
for key in keys:grouped.setdefault(key.split('/')[0],[]).append(key)
for lesson,items in grouped.items():
    path=ROOT/'content/ch08'/f'{lesson}.md'
    old=path.read_text();new=old
    for key in items:
        task_id=key.split('/')[1]
        pattern=r'(^## task: '+re.escape(task_id)+r'\s*\|.*?^### check\s*\n```python\n)(.*?)(\n```)'
        compiled=re.compile(pattern,re.M|re.S)
        assert len(list(compiled.finditer(new)))==1,key
        new=compiled.sub(lambda m:m.group(1)+tasks[key]['check'].rstrip()+m.group(3),new,count=1)
    if apply:path.write_text(new)
    else:sys.stdout.writelines(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(path),tofile=str(path)))
