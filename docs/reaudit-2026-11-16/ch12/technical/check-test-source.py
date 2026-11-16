"""Check edited quiz structure and visible lengths without building HTML."""
from pathlib import Path
import hashlib,json,re,math
D=Path(__file__).resolve().parent.parent
p=Path('content/ch12/test.md'); s=p.read_text(); old=(D/'technical/test-source-before.md').read_text()
blocks=lambda t: re.findall(r'::: quiz ([^\n]+)\n(.*?)\n:::',t,re.S)
a,b=blocks(old),blocks(s); assert len(a)==len(b)==13
changed=[i+1 for i,(x,y) in enumerate(zip(a,b)) if x!=y]; assert changed==[3,4,5,6,8,9,10,11,12]
qs=[]
for i,(_,block) in enumerate(b,1):
    found=re.findall(r'^- \[([x ])\] (.*?)\n  > (.*)$',block,re.M); assert len(found)==4
    assert [k for k,_,_ in found]==['x',' ',' ',' ']
    variants=[]
    for key,text,feedback in found:
        visible=re.sub(r'\s+',' ',text.replace('`','')).strip()
        variants.append({'text':visible,'length':len(visible),'correct':key=='x','feedback':feedback})
    ls=[v['length'] for v in variants]; mx=max(ls); maximum=[j for j,l in enumerate(ls) if l==mx]
    qs.append({'id':f'c{i}','variants':variants,'max_indices':maximum,'unique_longest_correct':maximum==[0]})
n=len(qs); out={'stage':'edited source, provisional until actual HTML rebuilt','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'changed_questions':changed,'questions_count':n,'variants_count':sum(len(q['variants']) for q in qs),'feedback_count':sum(bool(v['feedback']) for q in qs for v in q['variants']),'keys_unchanged':True,'unchanged_questions':[1,2,7,13],'unique_longest_correct':sum(q['unique_longest_correct'] for q in qs),'random_max_ties_expected':sum(1/len(q['max_indices']) if 0 in q['max_indices'] else 0 for q in qs),'favourable_max_ties_upper_bound':sum(0 in q['max_indices'] for q in qs),'ui_passing_min':next(k for k in range(n+1) if math.floor(100*k/n+0.5)>=80),'questions':qs}
(D/'test-lengths-after-source.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='questions'},ensure_ascii=False,indent=2))
print([(q['id'],[v['length'] for v in q['variants']],q['max_indices']) for q in qs])
