from pathlib import Path
import re,json,hashlib,math,sys
root=Path(__file__).resolve().parents[3]
source=root/'content/ch11/test.md'
s=source.read_text()
rows=[]
for i,b in enumerate(re.findall(r'^::: quiz ([^\n]+)\n(.*?)^:::',s,re.M|re.S),1):
    lesson,body=b
    opts=re.findall(r'^- \[([x ])\] (.*)\n  > (.*)$',body,re.M)
    assert len(opts)==4,(i,opts)
    texts=[re.sub(r'[`*]','',x[1]) for x in opts]
    lengths=[len(x) for x in texts]
    mx=max(lengths); longest=[j+1 for j,n in enumerate(lengths) if n==mx]
    keys=[j+1 for j,x in enumerate(opts) if x[0]=='x']
    rows.append({'question':i,'lesson':lesson,'condition':body.split('\n\n')[0],'options':texts,'feedback':[x[2] for x in opts],'lengths':lengths,'longest_options':longest,'correct_options':keys,'unique_longest_correct':len(longest)==1 and longest==keys})
k=sum(x['unique_longest_correct'] for x in rows)
result={'source':'content/ch11/test.md','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'measurement':'Unicode code points in visible option, backticks/emphasis markers removed, feedback excluded; no astral characters so equal to JS string.length','conditions':len(rows),'options':sum(len(x['options']) for x in rows),'feedback':sum(len(x['feedback']) for x in rows),'rows':rows,'unique_longest_correct':k,'ties':[x['question'] for x in rows if len(x['longest_options'])>1],'score_math_round':math.floor(100*k/len(rows)+.5),'minimum_correct_for_80':next(k for k in range(13) if math.floor(100*k/12+.5)>=80)}
(root/('docs/reaudit-2026-11-16/ch11/test-lengths-'+(sys.argv[1] if len(sys.argv)>1 else 'before')+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))
print([(x['question'],x['lengths'],x['longest_options'],x['unique_longest_correct']) for x in rows])
