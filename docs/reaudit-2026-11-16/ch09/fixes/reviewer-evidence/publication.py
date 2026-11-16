"""Verify the published lesson, notebook catalog, tests, and reviewer-facing text."""
import hashlib
import html
import json
import re
import sys
from pathlib import Path
here=Path(__file__).resolve().parent
site=Path(sys.argv[1])
catalog=json.loads((site/'notebooks/tasks/ch09.json').read_text())['tasks']
pages={}
seen=set()
def plain(s):
    return ' '.join(html.unescape(re.sub('<[^>]+>',' ',s)).split())
for page in sorted((site/'ch09').glob('*.html')):
    src=page.read_text()
    m=re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>',src,re.S)
    if not m: continue
    lesson=json.loads(m[1])
    keys=[]
    for task in lesson['tasks']:
        key=lesson['lesson']+'/'+task['id']
        seen.add(key); keys.append(key)
        for field in ['setup','starter','solution','check']:
            assert (task.get(field) or '')==(catalog[key].get(field) or ''),(key,field)
    pages[page.name]=dict(sha256=hashlib.sha256(page.read_bytes()).hexdigest(),tasks=keys)
assert seen==set(catalog)
page=(site/'ch09/test.html').read_text()
questions=re.split(r'<div class="quiz-c" data-q="(c\d+)"[^>]*>',page)[1:]
cases={}
for label,content in zip(questions[::2],questions[1::2]):
    prompt=re.search(r'</div>\s*<p>(.*?)</p>',content,re.S)[1]
    options=re.findall(r'<li>\[([x ])\] (.*?)\s*<blockquote>(.*?)</blockquote>',content,re.S)
    assert len(options)==4 and sum(flag=='x' for flag,_,_ in options)==1,label
    cases[label]=dict(prompt=plain(prompt),options=[plain(s) for _,s,_ in options],feedback=[plain(s) for _,_,s in options],
                      correct=next(i+1 for i,(flag,_,_) in enumerate(options) if flag=='x'))
report=dict(tasks=len(seen),parity_fields=['setup','starter','solution','check'],pages=pages,test=cases)
(here/(sys.argv[2]+'-publication.json')).write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
