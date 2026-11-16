"""Stdlib source/actual-HTML/catalog after audit; no browser or JS execution."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,html,json,math,re
D=Path(__file__).resolve().parent.parent
source=Path('content/ch12/test.md'); page=Path('site/ch12/test.html'); s=source.read_text(); h=page.read_text()
norm=lambda t: re.sub(r'\s+',' ',t).strip()
class Visible(HTMLParser):
    def __init__(self):super().__init__(); self.parts=[]
    def handle_data(self,t):self.parts.append(t)
def visible(t):
    p=Visible();p.feed(t);return norm(''.join(p.parts))
source_blocks=re.findall(r'::: quiz ([^\n]+)\n(.*?)\n:::',s,re.S)
html_blocks=re.findall(r'<div class="quiz-c" data-q="(c\d+)".*?<div class="predict-title">.*?</div>\s*(.*?)\n</ul>\s*</div>',h,re.S)
assert len(source_blocks)==len(html_blocks)==13
lengths=json.loads((D/'test-lengths-after.json').read_text()); checks=[]
for i,((lesson,block),(qid,hblock),q) in enumerate(zip(source_blocks,html_blocks,lengths['questions']),1):
    assert qid==q['id']==f'c{i}'
    question=norm(block.split('\n\n')[0].replace('`',''))
    assert question==visible(hblock.split('<ul>')[0]),(qid,'condition mismatch')
    variants=re.findall(r'^- \[([x ])\] (.*?)\n  > (.*)$',block,re.M)
    assert len(variants)==4
    for j,((key,text,feedback),v) in enumerate(zip(variants,q['variants'])):
        assert norm(text.replace('`',''))==v['text'],(qid,j,'variant mismatch')
        assert norm(feedback.replace('`',''))==v['feedback'],(qid,j,'feedback mismatch')
        assert (key=='x')==v['correct'],(qid,j,'key mismatch')
    assert sum(v['correct'] for v in q['variants'])==1
    checks.append({'id':qid,'condition':'PASS','four_variants':'PASS','four_feedback':'PASS','key':'PASS','source_lesson':lesson})
scripts=re.findall(r'<script[^>]+src="([^"]+)',h)
linked=next(x for x in scripts if '/course.js?' in x); cp=(page.parent/linked.split('?')[0]).resolve(); data=cp.read_text(); catalog,_=json.JSONDecoder().raw_decode(data[data.find('['):]); ch=next(x for x in catalog if x['id']=='ch12')
expected={f'c{i}':('reaudit-20261117-v5' if i in [3,4,5,6,8,9,10,11,12] else 'balanced-v3') for i in range(1,14)}
assert ch['test']['revisions']==expected
assert ch['test']['n']==13 and not ch['test'].get('coreQuestions')
for k,v in expected.items():assert f'{k}: {v}' in s
old=(D/'technical/test-source-before.md').read_text(); ob=re.findall(r'::: quiz[^\n]*\n.*?\n:::',old,re.S); nb=re.findall(r'::: quiz[^\n]*\n.*?\n:::',s,re.S)
assert all(ob[i-1]==nb[i-1] for i in [1,2,7,13])
core=Path('site/assets/core.js').read_text(); lessonjs=Path('site/assets/lesson.js').read_text()
assert 'Math.round(100 * ok / qs.length)' in lessonjs and 'pct >= 80' in lessonjs
assert "question + '-' + revision" in core and "(attempt > 1 ? '/' + attempt : '')" in core
assert 'D.testQuestionKey(LESSON.lesson, q.dataset.q, attempt)' in lessonjs
round_js=lambda x: math.floor(x+0.5)
boundaries=[{'correct':k,'total':13,'rounded':round_js(100*k/13),'pass':round_js(100*k/13)>=80} for k in [10,11]]
assert boundaries[0]['pass']==False and boundaries[1]['pass']==True
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out={'status':'PASS','scope':'static source vs actual HTML, linked catalog and UI predicate; browser persistence not executed','conditions':13,'variants':52,'feedback':52,'keys':13,'unchanged_blocks':[1,2,7,13],'revisions':expected,'linked_scripts':scripts,'source_sha256':sha(source),'html_sha256':sha(page),'course_sha256':sha(cp),'core_sha256':sha(Path('site/assets/core.js')),'lesson_sha256':sha(Path('site/assets/lesson.js')),'boundaries':boundaries,'minimum_passing_correct':11,'per_question':checks}
(D/'technical/test-after-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='per_question'},ensure_ascii=False,indent=2))
