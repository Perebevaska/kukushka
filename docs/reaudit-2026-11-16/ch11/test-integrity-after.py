from pathlib import Path
import json,re,html,hashlib
D=Path(__file__).resolve().parent
R=D.parents[2]
a=json.loads((D/'test-lengths-after.json').read_text())
b=json.loads((D/'test-lengths-before.json').read_text())
s=(R/'site/ch11/test.html').read_text()
def clean(t): return ' '.join(html.unescape(re.sub('<[^>]+>','',t)).split())
def md(t): return ' '.join(re.sub(r'[`*]','',t).split())
blocks=re.findall(r'<div class="quiz-c" data-q="(c\d+)".*?(?=<div class="quiz-c"|</details>)',s,re.S)
bodies=re.split(r'<div class="quiz-c" data-q="c\d+"[^>]*>',s)[1:]
checks=[]
for row,ident,body in zip(a['rows'],blocks,bodies):
    body=body.split('</details>')[0]
    condition=re.search(r'</div>\s*<p>(.*?)</p>\s*<ul>',body,re.S).group(1)
    opts=re.findall(r'<li>\[([x ])\] (.*?)\s*<blockquote>\s*<p>(.*?)</p>\s*</blockquote>\s*</li>',body,re.S)
    checks.append({'id':ident,'condition_match':clean(condition)==md(row['condition']), 'options_match':[clean(o[1]) for o in opts]==row['options'],'feedback_match':[clean(o[2]) for o in opts]==[md(x) for x in row['feedback']], 'keys_match':[i+1 for i,o in enumerate(opts) if o[0]=='x']==row['correct_options'],'actual_options':len(opts),'actual_feedback':len(opts)})
assert len(checks)==12
assert all(c[k] for c in checks for k in ['condition_match','options_match','feedback_match','keys_match']),checks
script=re.search(r'<script src="([^\"]*assets/course\.js[^\"]*)"',s).group(1)
cp=(R/'site/ch11'/script.split('?')[0]).resolve()
catalog=json.JSONDecoder().raw_decode(cp.read_text().split('=',1)[1].lstrip())[0]
c=next(x for x in catalog if x['id']=='ch11')['test']
rev=c['revisions']
expect={f'c{i}':('reaudit-20261116-v5' if i==12 else 'reaudit-20261116-v4' if i in [4,5,6,8] else 'balanced-v3') for i in range(1,13)}
assert rev==expect,rev
assert not c.get('coreQuestions')
result={'html_source':'site/ch11/test.html','html_sha256':hashlib.sha256((R/'site/ch11/test.html').read_bytes()).hexdigest(),'content_sha256':a['sha256'],'catalog_script_link':script,'catalog_resolved':str(cp),'revisions':rev,'revision_check':True,'core_questions':c.get('coreQuestions'),'conditions':len(checks),'options':sum(x['actual_options'] for x in checks),'feedback':sum(x['actual_feedback'] for x in checks),'keys_preserved':all(x['correct_options']==y['correct_options'] for x,y in zip(a['rows'],b['rows'])),'rows':checks,'testQuestionKey_static_check':'core.js D.testQuestionKey reads ch.test.revisions[question], appends revision and attempt suffix; lesson.js calls this function for quiz key; no data-revision attribute required','changed_first_attempt_keys':[f'ch11/test#c{i}-{rev[f"c{i}"]}' for i in [4,5,6,8,12]]}
(D/'test-integrity-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
