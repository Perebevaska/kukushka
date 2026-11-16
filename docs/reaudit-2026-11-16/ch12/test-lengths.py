"""Lightweight stdlib audit of visible quiz text. Run from repository root."""
import hashlib, html, json, math, re, sys
from pathlib import Path
from html.parser import HTMLParser
class QuizParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.questions=[]; self.q=None; self.li=None; self.in_quote=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='div' and 'quiz-c' in a.get('class','').split():
            self.q={'id':a['data-q'],'variants':[]}; self.questions.append(self.q)
        if self.q and tag=='li': self.li={'text':'','feedback':''}; self.q['variants'].append(self.li)
        if self.li and tag=='blockquote': self.in_quote+=1
    def handle_endtag(self, tag):
        if self.li and tag=='blockquote': self.in_quote-=1
        if tag=='li': self.li=None
    def handle_data(self,data):
        if self.li: self.li['feedback' if self.in_quote else 'text']+=data
norm=lambda x:re.sub(r'\s+',' ',x).strip()
path=Path('site/ch12/test.html'); p=QuizParser(); p.feed(path.read_text())
for q in p.questions:
    for v in q['variants']:
        v['text']=norm(v['text']); v['correct']=v['text'].startswith('[x]'); v['text']=re.sub(r'^\[[x ]\]\s*','',v['text']); v['feedback']=norm(v['feedback']); v['length']=len(v['text'])
    ls=[v['length'] for v in q['variants']]; mx=max(ls); mn=min(ls)
    q['correct_index']=next(i for i,v in enumerate(q['variants']) if v['correct'])
    q['max_indices']=[i for i,l in enumerate(ls) if l==mx]; q['min_indices']=[i for i,l in enumerate(ls) if l==mn]
    q['unique_longest_correct']=len(q['max_indices'])==1 and q['correct_index'] in q['max_indices']
    q['unique_shortest_correct']=len(q['min_indices'])==1 and q['correct_index'] in q['min_indices']
n=len(p.questions); mx=sum(q['unique_longest_correct'] for q in p.questions); mn=sum(q['unique_shortest_correct'] for q in p.questions)
out={'html_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'measurement':'Unicode characters, visible HTML text, blockquote and correctness marker excluded, whitespace normalized; code backticks excluded because HTML does not display them','tie_policy':'unique maximum required for guaranteed success; random tie expectation and favourable tie upper bound reported separately','n_questions':n,'n_variants':sum(len(q['variants']) for q in p.questions),'n_feedback':sum(bool(v['feedback']) for q in p.questions for v in q['variants']),'unique_longest_correct':mx,'unique_shortest_correct':mn,'longest_random_ties_expected':sum((1/len(q['max_indices']) if q['correct_index'] in q['max_indices'] else 0) for q in p.questions),'longest_favourable_ties_upper_bound':sum(q['correct_index'] in q['max_indices'] for q in p.questions),'ui_passing_min':next(k for k in range(n+1) if math.floor(100*k/n+0.5)>=80),'questions':p.questions}
target=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('test-lengths-before.json'); target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='questions'},ensure_ascii=False,indent=2))
print([(q['id'],[v['length'] for v in q['variants']],q['unique_longest_correct']) for q in p.questions])
