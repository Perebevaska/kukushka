"""Text-only audit: no course runtime, keys/explanations excluded from lengths."""
from pathlib import Path
import re, json, hashlib
p=Path('content/ch09/test.md')
s=p.read_text()
rows=[]
for i,b in enumerate(re.findall(r'::: quiz[^\n]*\n(.*?)\n:::', s, re.S),1):
    options=re.findall(r'^- \[([ x])\] (.*)$',b,re.M)
    assert len(options)==4
    # Inline Markdown delimiters removed; visible characters remain.
    texts=[re.sub(r'[`*_]','',t) for _,t in options]
    lengths=list(map(len,texts)); lo=min(lengths); hi=max(lengths)
    key=[j+1 for j,(k,t) in enumerate(options) if k=='x']
    longest=[j+1 for j,n in enumerate(lengths) if n==hi]
    shortest=[j+1 for j,n in enumerate(lengths) if n==lo]
    rows.append(dict(id=f'c{i}',lengths=lengths,key=key,unique_longest=longest if len(longest)==1 else None,longest_tie=longest if len(longest)>1 else None,unique_shortest=shortest if len(shortest)==1 else None,shortest_tie=shortest if len(shortest)>1 else None,longest_correct=longest==key,shortest_correct=shortest==key))
assert len(rows)==16
out={'source':str(p),'sha256':hashlib.sha256(s.encode()).hexdigest(),'unit':'Unicode characters in visible option, stripped inline Markdown delimiters; spaces/punctuation included','questions':rows,'correct_unique_longest':sum(r['longest_correct'] for r in rows),'correct_unique_shortest':sum(r['shortest_correct'] for r in rows),'threshold':next(k for k in range(17) if int(100*k/16+0.5)>=80),'longest_ties':[r['id'] for r in rows if r['longest_tie']],'shortest_ties':[r['id'] for r in rows if r['shortest_tie']]}
print(json.dumps(out,ensure_ascii=False,indent=2))
