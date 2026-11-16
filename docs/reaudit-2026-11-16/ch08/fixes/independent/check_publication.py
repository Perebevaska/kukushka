"""Record lesson/notebook parity, public free-text rubric, and quiz-length signals."""
from html import unescape
from pathlib import Path
import json,re,sys,hashlib
site,output=map(Path,sys.argv[1:])
def hashbytes(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(s):
    return ' '.join(unescape(re.sub('<[^>]+>',' ',s)).split())
html={}
for f in sorted((site/'ch08').glob('*.html')):
    m=re.search(r'id="lesson-data">(.*?)</script>',f.read_text(),re.S)
    if m:
        d=json.loads(m[1]);html.update({d['lesson']+'/'+r['id']:r for r in d['tasks']})
catalog=json.loads((site/'notebooks/tasks/ch08.json').read_text())['tasks']
delta={}
for k in sorted(set(catalog)|set(html)):
    diff=[field for field in ['check','setup','starter','solution'] if
         (catalog.get(k,{}).get(field) or '').strip()!=(html.get(k,{}).get(field) or '').strip()]
    if diff:delta[k]=diff
quiz=(site/'ch08/test.html').read_text()
q={}
for m in re.finditer(r'<div class="quiz-c" data-q="([^"]+)" data-lesson="([^"]+)">([\s\S]*?)</ul>',quiz):
    ns=[(flag,len(plain(text))) for flag,text in re.findall(r'<li>\[([ x])\] (.*?)\s*<blockquote>',m[3],re.S)]
    if len(ns)!=4:raise ValueError((m[1],ns))
    counts=[n for _,n in ns];top=max(counts); true_i=next(i for i,p in enumerate(ns) if p[0]=='x')
    q[m[1]]=dict(lesson=m[2],lengths=counts,longest_guarantees_correct=top==counts[true_i] and counts.count(top)==1)
core={'01-value','01a-pilot','02-budget','05-explain','05b-fairness','06-project','07-final-project'}
coreq=[k for k,r in q.items() if r['lesson'] in core]
rpage=(site/'ch08/04b-segments.html').read_text()
at=rpage.index('id="task-report-text"') if 'id="task-report-text"' in rpage else rpage.index('Метрику мало посчитать')
snippet=plain(rpage[at:at+4500])[:1500]
nb=json.loads((site/'notebooks/ch08-practice.ipynb').read_text())
magic=[re.search(r'^%%task\s+(\S+)', ''.join(c['source'])) for c in nb['cells'] if c['cell_type']=='code']
ids={x[1] for x in magic if x}
output.write_text(json.dumps(dict(html=len(html),catalog=len(catalog),catalog_missing=sorted(set(html)-set(catalog)),html_missing=sorted(set(catalog)-set(html)),
    deltas=delta,magic_targets=len(ids),catalog_without_magic=sorted(set(catalog)-ids),quiz=q,core_ids=coreq,
    correct_by_length_all=sum(r['longest_guarantees_correct'] for r in q.values()),correct_by_length_core=sum(q[k]['longest_guarantees_correct'] for k in coreq),
    rubric=snippet,files={k:hashbytes(site/k) for k in ['ch08/test.html','ch08/02-budget.html','ch08/07-final-project.html','notebooks/ch08-practice.ipynb','notebooks/tasks/ch08.json']}),ensure_ascii=False,indent=2)+'\n')
