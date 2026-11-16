from pathlib import Path
import sys,re,random,json
ch=sys.argv[1]
folder=Path('/tmp/ku-audit')/ch
target=folder/'student'
target.mkdir(parents=True,exist_ok=True)
Path('docs/audit-2026-11-13',ch).mkdir(exist_ok=True)
mapping={}
for p in Path('content',ch).glob('*.md'):
    text=p.read_text()
    parts=re.split(r'(?m)(?=^## task: )',text)
    counts={}
    def question(m):
        block=m[0]
        kind=m[1]
        index=counts[kind]=counts.get(kind,0)+1
        lines=[l for l in block.splitlines() if not l.strip().startswith('>') and not l.startswith('Почему:')]
        opts=[i for i,l in enumerate(lines) if re.match(r'^- ',l)]
        choices=[re.sub(r'^- \[[ x]\] ','- ',lines[i]) for i in opts]
        order=list(range(len(opts)))
        random.Random((ch,p.stem,kind,index).__repr__()).shuffle(order)
        for i,j in zip(opts,order): lines[i]=choices[j]
        mapping[f'{p.stem}/{kind}/{index}']=[v+1 for v in order]
        return '\n'.join(lines)
    out=re.sub(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',question,parts[0])
    for task in parts[1:]:
        seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',task)
        out+='\n'+seg[0]
        for kind,body in zip(seg[1::2],seg[2::2]):
            if kind=='starter': out+='\n### Заготовка\n'+body
            if kind=='parsons':
                ls=[l.strip() for l in body.splitlines() if l.strip() and not l.startswith('```')]
                random.Random(seg[0]).shuffle(ls)
                out+='\nСтроки для сборки с отступами:\n'+'\n'.join(ls)+'\n'
    (target/p.name).write_text(out)
(folder/'choices.json').write_text(json.dumps(mapping))
