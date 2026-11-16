"""Stdlib only; visible option text follows lesson.js, without blockquotes."""
from pathlib import Path
from html import unescape
import re,json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('--output',default='docs/reaudit-2026-11-16/ch13/test-lengths-before.json');a=p.parse_args()
path=Path('site/ch13/test.html'); raw=path.read_text()
def visible(s): return unescape(re.sub('<[^>]+>','',s)).strip()
rows=[]
for q,body in re.findall(r'<div class="quiz-c" data-q="(c\d+)"[^>]*>(.*?)(?=<div class="quiz-c"|</details>)',raw,re.S):
 opts=[]
 for li in re.findall(r'<li>(.*?)</li>',body,re.S):
  fb=re.findall(r'<blockquote>(.*?)</blockquote>',li,re.S)
  t=visible(re.sub(r'<blockquote>.*?</blockquote>','',li,flags=re.S))
  correct=t.startswith('[x]');t=re.sub(r'^\[[x ]\]\s*','',t)
  opts.append(dict(text=t,length=len(t),correct=correct,feedback=visible(' '.join(fb))))
 if not opts: continue
 sizes=[o['length'] for o in opts]; mx=max(sizes);mn=min(sizes)
 rows.append(dict(id=q,options=opts,longest=[i+1 for i,n in enumerate(sizes) if n==mx],shortest=[i+1 for i,n in enumerate(sizes) if n==mn],unique_longest_correct=sizes.count(mx)==1 and opts[sizes.index(mx)]['correct'],unique_shortest_correct=sizes.count(mn)==1 and opts[sizes.index(mn)]['correct']))
n=len(rows)
result=dict(html_sha256=hashlib.sha256(raw.encode()).hexdigest(),policy='Unicode code points after stripping HTML and blockquote and checkbox markers, HTML entities decoded; no guessed answer on ties',n=n,variants=sum(len(r['options']) for r in rows),feedback=sum(bool(o['feedback']) for r in rows for o in r['options']),unique_longest_correct=sum(r['unique_longest_correct'] for r in rows),longest_ties=sum(len(r['longest'])>1 for r in rows),unique_shortest_correct=sum(r['unique_shortest_correct'] for r in rows),shortest_ties=sum(len(r['shortest'])>1 for r in rows),minpassing=next(k for k in range(n+1) if int(100*k/n+.5)>=80),questions=rows)
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print({k:v for k,v in result.items() if k!='questions'})
for r in rows: print(r['id'],[o['length'] for o in r['options']],r['longest'],r['unique_longest_correct'])
