from pathlib import Path
from html.parser import HTMLParser
import re,json,hashlib
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course')
s=(root/'content/ch15/test.md').read_text()
def norm(t): return re.sub(r'\s+',' ',re.sub(r'`([^`]*)`',r'\1',t)).strip()
source=[]
for i,m in enumerate(re.finditer(r'::: quiz ([^\n]+)\n(.*?)\n:::',s,re.S),1):
 b=m[2]; opts=[]
 for z in re.finditer(r'- \[([x ])\] (.*?)\n  > (.*?)(?=\n- \[|\Z)',b,re.S):
  opts.append(dict(correct=z[1]=='x',text=norm(z[2]),explanation=norm(z[3])))
 source.append(dict(id=f'c{i}',lesson=m[1],question=norm(b.split('\n- [')[0]),options=opts))
class H(HTMLParser):
 def __init__(self): super().__init__();self.q=[];self.cur=None;self.depth=0;self.mode=None;self.buf=[];self.op=None
 def handle_starttag(self,tag,a):
  a=dict(a)
  if tag=='div' and a.get('class')=='quiz-c':self.cur=dict(id=a['data-q'],lesson=a['data-lesson'],options=[]);self.depth=1;return
  if self.cur is None:return
  if tag=='div':self.depth+=1
  if tag=='li':self.mode='option';self.buf=[]
  elif tag=='blockquote':
   t=norm(''.join(self.buf));self.op=dict(correct=t.startswith('[x]'),text=t[3:].strip());self.mode='explanation';self.buf=[]
  elif tag=='p' and self.mode is None:self.mode='question';self.buf=[]
 def handle_data(self,d):
  if self.cur is not None and self.mode:self.buf.append(d)
 def handle_endtag(self,tag):
  if self.cur is None:return
  if tag=='p' and self.mode=='question':self.cur['question']=norm(''.join(self.buf));self.mode=None
  elif tag=='blockquote':self.op['explanation']=norm(''.join(self.buf));self.cur['options'].append(self.op);self.mode=None
  elif tag=='div':
   self.depth-=1
   if self.depth==0:self.q.append(self.cur);self.cur=None;self.mode=None
h=H();h.feed((root/'site/ch15/test.html').read_text())
rows=[]
for a,b in zip(source,h.q):
 lens=[len(o['text']) for o in a['options']]; top=[j for j,v in enumerate(lens) if v==max(lens)]
 rows.append(dict(id=a['id'],same=a==b,lengths=lens,unique_longest_correct=len(top)==1 and a['options'][top[0]]['correct'],tie=len(top)>1))
print(json.dumps(dict(source_count=len(source),html_count=len(h.q),options=sum(len(q['options']) for q in source),explanations=sum(bool(o['explanation']) for q in source for o in q['options']),all_equal=source==h.q,unique_longest_correct=sum(r['unique_longest_correct'] for r in rows),ties=sum(r['tie'] for r in rows),rows=rows),ensure_ascii=False,indent=2))
(root/'docs/reaudit-2026-11-16/ch15/technical/test-comparison.json').write_text(json.dumps(dict(source=source,html=h.q,rows=rows),ensure_ascii=False,indent=2))
