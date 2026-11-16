from pathlib import Path
import re,json,html,math,hashlib
r=Path(__file__).resolve().parents[3];d=Path(__file__).parent
s=(r/'content/ch10/test.md').read_text();h=(r/'site/ch10/test.html').read_text()
course=json.JSONDecoder().raw_decode((r/'site/assets/course.js').read_text().removeprefix('window.DSC_COURSE = '))[0]
ch=next(x for x in course if x['id']=='ch10');rev=ch['test']['revisions']
changed=json.loads((d/'technical/test-revisions.json').read_text())['changed']
blocks=re.findall(r'^::: quiz[^\n]*\n(.*?)^:::',s,re.M|re.S)
hblocks=re.split(r'<div class="quiz-c"',h)[1:]
def plain(t):
 t=re.sub(r'`([^`]+)`',r'\1',t);t=re.sub(r'\$([^$]+)\$',r'\1',t);t=html.unescape(re.sub('<[^>]*>','',t));return ' '.join(t.split())
rows=[]
for i,(b,hb) in enumerate(zip(blocks,hblocks),1):
 q=b.split('\n- [')[0].strip();opts=re.findall(r'^- \[([x ])\] (.*)\n  > (.*)$',b,re.M)
 hp=re.findall(r'<li>\[([x ])\] (.*?)<blockquote>\s*<p>(.*?)</p>\s*</blockquote>\s*</li>',hb,re.S)
 assert len(opts)==len(hp)==4,(i,len(opts),len(hp))
 assert plain(q)==plain(re.search(r'</div>\s*<p>(.*?)</p>',hb,re.S)[1]),i
 for (key,t,fb),(hk,ht,hfb) in zip(opts,hp): assert (key,plain(t),plain(fb))==(hk,plain(ht),plain(hfb)),(i,t)
 lengths=[len(re.sub(r'`([^`]+)`',r'\1',t)) for _,t,_ in opts];mx=max(lengths);winners=[j+1 for j,x in enumerate(lengths) if x==mx];key=next(j+1 for j,(k,_,_) in enumerate(opts) if k=='x')
 assert key==1 and sum(k=='x' for k,_,_ in opts)==1
 rows.append(dict(question=i,lengths=lengths,correct=key,longest=winners,unique=len(winners)==1,guaranteed=len(winners)==1 and winners[0]==key))
 assert rev[f'c{i}']==('reaudit-20261116-v4' if i in changed else 'balanced-v3'),i
assert len(blocks)==len(hblocks)==14
result=dict(metric='Visible Unicode characters; inline code delimiters removed; feedback excluded',count=14,options=56,feedback=56,source_html_match=True,revision_source='site/assets/course.js linked from actual test.html',revisions=rev,rows=rows,unique_longest_correct=sum(x['guaranteed'] for x in rows),ties=[x['question'] for x in rows if not x['unique']],threshold=next(k for k in range(15) if math.floor(100*k/14+.5)>=80),html_sha256=hashlib.sha256(h.encode()).hexdigest())
(d/'test-lengths-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
