"""Составить инвентаризацию программы для сверки итогов. Читает только открытое оглавление."""
from pathlib import Path
import re
import yaml
data = yaml.safe_load(Path('content/course.yaml').read_text())
for c in data['chapters']:
    ls = c['lessons']
    core = [x for x in ls if x.get('core', False)]
    exams=c.get('exams') or []
    print(c['id'],c['title'], f"уроков {len(ls)}, обязательных {len(core)}, контрольных {len(exams)}; ",
          'проекты: '+', '.join(x['title'] for x in ls if re.search(r'(?:проект|^project)',x['title'],re.I)))
