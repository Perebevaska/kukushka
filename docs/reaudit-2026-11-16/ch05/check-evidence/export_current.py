import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root/'tools/checks'))
from acceptance_runner import Chapter
c=Chapter('ch05')
Path(__file__).with_name('current-course.json').write_text(json.dumps(list(c.tasks.values()),ensure_ascii=False,indent=2))
