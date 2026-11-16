from pathlib import Path
import re,json,random,shutil
w=Path('/private/tmp/kuch10round');t=w/'student'; keys={};hint={}
for p in (w/'original/content/ch10').glob('*.md'):
 s=p.read_text();parts=re.split(r'(?m)(?=^## task: )',s); counts={}
 def q(m):
  kind=m[1]; i=counts[kind]=counts.get(kind,0)+1; id=f'{p.stem}/{kind}/{i}'
  lines=[l for l in m[0].splitlines() if not l.strip().startswith('>') and not l.startswith('Почему:')]
  pos=[j for j,v in enumerate(lines) if re.match('^- ',v)]
  orig=[re.sub(r'^- (?:\[[ x]\] )?', '',lines[j]) for j in pos];marked=[k for k,j in enumerate(pos) if lines[j].startswith('- [x] ')];assert len(marked)==1,(id,marked)
  order=list(range(len(pos))); random.Random('nov16'+id).shuffle(order);keys[id]={'answer':order.index(marked[0])+1,'original_order':[z+1 for z in order]}
  for k,j in enumerate(pos):lines[j]=str(k+1)+'. '+orig[order[k]]
  lines[0]=f'Вопрос {id}'; return '\n'.join(lines[:-1])
 text=re.sub(r'(?ms)^::: (predict|quiz)\b.*?^:::[ \t]*$',q,parts[0])
 if p.stem=='test':
  a=text.index('Вопрос test/');(t/'test-open.md').write_text(text.split('---',2)[-1][:text.split('---',2)[-1].index('Вопрос test/')]);text=text[a:]
 for j,part in enumerate(parts[1:]):
  seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',part);text+='\n'+seg[0];id=seg[0].split('## task: ')[1].split(' |')[0];y=[]
  for kind,body in zip(seg[1::2],seg[2::2]):
   if kind=='starter':text+='\n### Заготовка\n'+body
   if kind=='hint':y.append(body.strip())
   if kind=='parsons':
    ls=[l.strip() for l in body.splitlines() if l.strip() and not l.startswith('```')];random.Random('nov16'+id).shuffle(ls);text+='\nДоступные строки для сборки с отступами:\n'+'\n'.join(ls)+'\n'
  hint[p.stem+'/'+id]=y
 (t/p.name).write_text(text)
(w/'keys.json').write_text(json.dumps(keys,ensure_ascii=False));(w/'hints.json').write_text(json.dumps(hint,ensure_ascii=False))
exp=json.loads((w/'course.json').read_text());files={f for it in exp if it['lesson'].startswith('ch10/') for f in it['files']};(t/'data').mkdir(exist_ok=True)
for f in sorted(files):shutil.copyfile(Path('site/data',f),t/'data'/f)
print('questions',len(keys),'files',sorted(files))
