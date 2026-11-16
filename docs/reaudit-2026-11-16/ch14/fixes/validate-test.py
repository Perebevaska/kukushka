"""Light stdlib validation; run from repository root; never mutates course files."""
from pathlib import Path
import hashlib, html, json, re
root=Path.cwd()
out=root/'docs/reaudit-2026-11-16/ch14/fixes/test-validation.json'
s=(root/'content/ch14/test.md').read_text()
h=(root/'site/ch14/test.html').read_text()
course=(root/'site/assets/course.js').read_text()
chapters=json.JSONDecoder().raw_decode(course.split('=',1)[1].lstrip())[0]
chapter=next(c for c in chapters if c['id']=='ch14')
print('Published test metadata:',json.dumps(chapter['test'],ensure_ascii=False))
norm=lambda t: re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',t)).replace('`','')).strip()
blocks=re.findall(r'::: quiz ([^\n]+)\n(.*?)\n:::',s,re.S)
ht=re.split(r'<div class="quiz-c"',h)[1:]
revisions=dict(re.findall(r'(c\d+): ([\w-]+)',s.split('---',2)[1]))
rows=[]
for i,((lesson,b),hb) in enumerate(zip(blocks,ht),1):
 so=re.findall(r'^- \[([x ])\] (.*?)\n  > (.*)',b,re.M)
 ho=re.findall(r'<li>\[([x ])\] (.*?)\n<blockquote>(.*?)</blockquote>',hb,re.S)
 stem=b.split('\n- [',1)[0].strip()
 publishedstem=re.search(r'</div>\s*<p>(.*?)</p>',hb,re.S).group(1)
 chars=[len(norm(t)) for c,t,w in so]
 row={'id':f'Q14-{i:02d}','public_id':f'ch14/test/c{i}','lesson':lesson,'n_options':len(so),'n_explanations':len(ho),'key_source':next(j+1 for j,(c,t,w) in enumerate(so) if c=='x'),'stem_equal':norm(stem)==norm(publishedstem),'all_options_equal':len(so)==len(ho) and all(c==c2 and norm(t)==norm(t2) for (c,t,w),(c2,t2,w2) in zip(so,ho)),'all_explanations_equal':len(so)==len(ho) and all(norm(w)==norm(w2) for (c,t,w),(c2,t2,w2) in zip(so,ho)),'chars':chars,'key_strict_longest':chars[0]>max(chars[1:]),'revision':revisions[f'c{i}']}
 assert row['n_options']==4 and len([c for c,t,w in so if c=='x'])==1
 assert row['stem_equal'] and row['all_options_equal'] and row['all_explanations_equal']
 rows.append(row)
assert len(blocks)==len(ht)==len(rows)==15
first=root/'docs/reaudit-2026-11-16/ch14/test-first-answers.md'
firsthash=hashlib.sha256(first.read_bytes()).hexdigest()
assert firsthash=='bdc5c464094adb872af63b72c99b16340d778991c1bfecb3df107a68b7e384e5'
metadata=chapter['test']
assert metadata['revisions']==revisions
assert sum(v=='reaudit-20261117-v4' for v in revisions.values())==14
result={'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'published_sha256':hashlib.sha256(h.encode()).hexdigest(),'blind_answers_sha256':firsthash,'metadata_revisions_equal':True,'questions':rows,'totals':{'questions':len(rows),'options':sum(r['n_options'] for r in rows),'explanations':sum(r['n_explanations'] for r in rows),'keys':15,'distractors':45,'strict_longest_keys':sum(r['key_strict_longest'] for r in rows),'updated_revisions':14,'all_equal':True}}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result['totals'],ensure_ascii=False));print('SHA source',result['source_sha256']);print('SHA published',result['published_sha256'])
