"""Read-only static comparison of revised source, generated HTML and metadata."""
from pathlib import Path
from html import unescape
import re,json,hashlib
root=Path(__file__).resolve().parents[4]
s=(root/'content/ch09/test.md').read_text();h=(root/'site/ch09/test.html').read_text()
bs=re.findall(r'::: quiz[^\n]*\n(.*?)\n:::',s,re.S)
cs=re.findall(r'<div class="quiz-c" data-q="(c\d+)"[^>]*>(.*?)(?=<div class="quiz-c"|</details>)',h,re.S)
def txt(x):return ' '.join(unescape(re.sub(r'<[^>]*>','',x)).split())
def md(x):return ' '.join(x.replace('`','').split())
rows=[]
for n,(b,(qid,c)) in enumerate(zip(bs,cs),1):
    q=b.split('\n',1)[0];htmlq=re.search(r'<p>(.*?)</p>',c,re.S)[1]
    opts=re.findall(r'^- \[([x ])\] (.*?)\n  > (.*?)$',b,re.M)
    lis=re.findall(r'<li>(.*?)</li>',c,re.S)
    checks=[]
    for (key,o,e),li in zip(opts,lis):
        parts=re.split(r'<blockquote>',li,maxsplit=1);visible=txt(parts[0]);explain=txt(parts[1].split('</blockquote>')[0])
        checks.append({'option':md(o)==visible[4:].strip(),'key':visible.startswith('[x]')==(key=='x'),'explanation':md(e)==explain})
    rows.append({'id':qid,'question_match':md(q)==txt(htmlq),'options':checks})
rev=dict(re.findall(r'(c\d+): ([\w-]+)',s.split('---')[1]));j=(root/'site/assets/course.js').read_text();course,_=json.JSONDecoder().raw_decode(j[j.index('['):]);meta=next(c['test'] for c in course if c['id']=='ch09')
out={'sha256':hashlib.sha256(s.encode()).hexdigest(),'source_count':len(bs),'html_count':len(cs),'options':sum(len(r['options']) for r in rows),'single_key_each':all(len(re.findall(r'^- \[x\]',b,re.M))==1 for b in bs),'metadata_revisions_match':rev==meta.get('revisions'),'metadata_count':meta['n'],'has_coreQuestions':'coreQuestions' in meta,'all_text_equal':all(r['question_match'] and all(all(c.values()) for c in r['options']) for r in rows),'rows':rows}
print(json.dumps(out,ensure_ascii=False,indent=2))
