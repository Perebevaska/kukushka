import sys
from pathlib import Path
import yaml
ch=sys.argv[1]
config=yaml.safe_load(Path('content/course.yaml').read_text())
chapter=next(c for c in config['chapters'] if c['id']==ch)
route=['intro']
for l in chapter['lessons']:
    route.append(l['id'])
    route.extend(e['id'] for e in chapter.get('exams',[]) if e['after']==l['id'])
route+=['test']
(Path('/tmp/ku-audit')/ch/'student'/'order.txt').write_text('\n'.join(route)+'\n')
