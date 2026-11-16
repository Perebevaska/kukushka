"""Extract probes verbatim from a local published HTML site or notebook catalog."""
import argparse,hashlib,json,re
from pathlib import Path
from probes import cases
here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('site',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--surface',choices=['html','catalog'],required=True)
args=parser.parse_args()
if args.surface=='catalog':
    source=args.site/'notebooks/tasks/ch08.json'
    tasks=json.loads(source.read_text())['tasks'].values()
else:
    tasks=[]
    for page in sorted((args.site/'ch08').glob('*.html')):
        match=re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>',page.read_text(),re.S)
        if match:
            lesson=json.loads(match[1])
            tasks.extend({**t,'files':lesson['files']} for t in lesson['tasks'])
tasks={t['id']:t for t in tasks if t.get('check')}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps([dict(id=name,key=key,expected=ok,code=code,
    setup=tasks[key].get('setup') or '',check=tasks[key]['check'],files=tasks[key]['files'],
    check_sha256=hashlib.sha256(tasks[key]['check'].encode()).hexdigest()) for name,key,ok,code in cases(tasks)],ensure_ascii=False))
