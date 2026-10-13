"""Основной путь: какие основные уроки ссылаются на углубления (по названию в «…»)."""
import re, sys, yaml
from pathlib import Path
C = Path(__file__).resolve().parent.parent / 'content'
course = yaml.safe_load((C / 'course.yaml').read_text(encoding='utf-8'))
titles = {}
for ch in course['chapters']:
    for l in ch.get('lessons', []):
        titles[l['title']] = (ch['id'], l['id'], bool(l.get('core')))
only = sys.argv[1:]
bad = 0
for ch in course['chapters']:
    if only and ch['id'] not in only:
        continue
    for l in ch.get('lessons', []):
        if not l.get('core'):
            continue
        text = (C / ch['id'] / f"{l['id']}.md").read_text(encoding='utf-8')
        for t in sorted(set(re.findall(r'«([^»]+)»', text))):
            if t in titles and not titles[t][2]:
                n = text.count(f'«{t}»')
                print(f"{ch['id']}/{l['id']} → «{t}» ({titles[t][0]}/{titles[t][1]}, углубление) ×{n}")
                bad += 1
print('итого ссылок основного пути на углубления:', bad)
