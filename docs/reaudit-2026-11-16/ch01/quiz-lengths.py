from html.parser import HTMLParser
from pathlib import Path
import re,json,hashlib
class Parse(HTMLParser):
 def __init__(self): super().__init__(); self.q=None;self.li=False;self.bq=0;self.rows=[];self.parts=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='div' and 'quiz-c' in d.get('class','').split():self.q=d['data-q']
  if t=='li' and self.q:self.li=True;self.parts=[]
  if t=='blockquote' and self.li:self.bq+=1
 def handle_endtag(self,t):
  if t=='blockquote' and self.li:self.bq-=1
  if t=='li' and self.li:
   raw=' '.join(''.join(self.parts).split()); m=re.match(r'\[([x ])\]\s*(.*)',raw)
   if m:self.rows.append({'q':self.q,'correct':m[1]=='x','text':m[2],'length':len(m[2])})
   self.li=False
 def handle_data(self,d):
  if self.li and not self.bq:self.parts.append(d)
p=Parse(); data=Path('site/ch01/test.html').read_text();p.feed(data)
res=[]
for i in range(1,16):
 r=[x for x in p.rows if x['q']==f'c{i}']; ls=[x['length'] for x in r]; k=next(j for j,x in enumerate(r) if x['correct'])
 res.append({'question':i,'lengths':ls,'correct_option_html':k+1,'unique_long_correct':ls.count(max(ls))==1 and ls[k]==max(ls),'unique_short_correct':ls.count(min(ls))==1 and ls[k]==min(ls),'options':r})
out={'sha256_html':hashlib.sha256(data.encode()).hexdigest(),'method':'Visible option text, code retained, HTML decoded, blockquotes and [x]/[ ] removed, whitespace normalized, Unicode code points; ties do not count','questions':res,'unique_long_correct':sum(x['unique_long_correct'] for x in res),'unique_short_correct':sum(x['unique_short_correct'] for x in res)}
Path('docs/reaudit-2026-11-16/ch01/quiz-lengths.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for r in res:print(r['question'],r['lengths'],'key',r['correct_option_html'],'max',r['unique_long_correct'],'min',r['unique_short_correct'])
print('TOTAL',out['unique_long_correct'],out['unique_short_correct'])
