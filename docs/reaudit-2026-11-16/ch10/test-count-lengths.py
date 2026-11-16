import re,json,pathlib,math
p=pathlib.Path('content/ch10/test.md')
s=p.read_text()
rows=[]
for i,b in enumerate(re.findall(r'^::: quiz[^\n]*\n(.*?)^:::',s,re.M|re.S),1):
    opts=re.findall(r'^- \[([x ])\] (.*)$',b,re.M)
    visible=[re.sub(r'`([^`]+)`',r'\1',t) for _,t in opts]
    lengths=list(map(len,visible)); mx=max(lengths); winners=[j+1 for j,x in enumerate(lengths) if x==mx]; correct=next(j+1 for j,(k,_) in enumerate(opts) if k=='x')
    rows.append(dict(question=i,lengths=lengths,correct=correct,longest=winners,unique=len(winners)==1,guaranteed=len(winners)==1 and winners[0]==correct))
result=dict(metric='Unicode code points in visible answer text; inline code delimiters removed; feedback excluded',count=len(rows),rows=rows,unique_longest_correct=sum(r['guaranteed'] for r in rows),ties=[r['question'] for r in rows if not r['unique']],threshold=next(k for k in range(len(rows)+1) if math.floor(100*k/len(rows)+.5)>=80))
pathlib.Path('docs/reaudit-2026-11-16/ch10/test-lengths-before.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
