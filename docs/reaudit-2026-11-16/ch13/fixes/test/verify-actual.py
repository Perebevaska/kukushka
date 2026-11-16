"""Read-only verification of generated HTML and linked runtime; stdlib only."""
from pathlib import Path
import json,re,hashlib,html
base=Path(__file__).resolve().parent
source=Path('content/ch13/test.md').read_text(); rendered=Path('site/ch13/test.html').read_text()
before=json.loads(Path('docs/reaudit-2026-11-16/ch13/test-lengths-before.json').read_text())
after=json.loads((base/'test-lengths-after.json').read_text())
prepared=json.loads((base/'after-source.json').read_text())
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def plain(s):return html.unescape(re.sub('<[^>]+>','',s)).strip()
def mdplain(s):return s.replace('`','')
blocks=re.findall(r'::: quiz [^\n]+\n(.*?)\n:::',source,re.S)
questions=re.findall(r'<div class="quiz-c" data-q="(c\d+)"[^>]*>(.*?)(?=<div class="quiz-c"|</details>)',rendered,re.S)
assert len(questions)==len(blocks)==14
rows=[]
for n,((qid,q),b,old,actual,prep) in enumerate(zip(questions,blocks,before['questions'],after['questions'],prepared['rows']),1):
 condition=b.split('\n\n',1)[0]
 p=plain(re.search(r'<p>(.*?)</p>',q,re.S).group(1));assert mdplain(condition)==p,(qid,condition,p)
 assert qid==actual['id']==prep['id']==old['id']
 assert [mdplain(x) for x in prep['options']]==[o['text'] for o in actual['options']],qid
 assert [mdplain(x) for x in prep['feedback']]==[o['feedback'] for o in actual['options']],qid
 assert [i+1 for i,o in enumerate(actual['options']) if o['correct']]==prep['correct_indices']==[1],qid
 changed=qid in prepared['changed']
 if not changed:assert old['options']==actual['options'],qid
 rows.append({'id':qid,'source_html_condition_equal':True,'all_options_feedback_equal':True,'key':1,'unchanged_options_feedback':not changed})
linked=re.findall(r'<script src="([^"]+)"',rendered)
resources={}
for rel in linked:
 f=(Path('site/ch13')/rel.split('?')[0]).resolve();resources[rel]=sha(f.read_text())
course=Path('site/assets/course.js').read_text(); chapters=json.JSONDecoder().raw_decode(course.split('=',1)[1].lstrip())[0];ch=next(c for c in chapters if c['id']=='ch13')
assert ch['test']['n']==14 and ch['test']['revisions']==prepared['revisions']
assert not ch['test'].get('coreQuestions')
lesson=Path('site/assets/lesson.js').read_text();core=Path('site/assets/core.js').read_text()
assert 'pct = Math.round(100 * ok / qs.length)' in lesson and 'pct >= 80' in lesson and 'st.score >= 80' in core
assert 'seededShuffle($$(\':scope > .qrow\', opts), key)' in lesson
assert (after['n'],after['variants'],after['feedback'],after['minpassing'])==(14,56,56,12)
llm=Path('content/ch13/04c-llm.md').read_text(); llmhtml=Path('site/ch13/04c-llm.html').read_text()
assert 'clearly_better' not in llm and 'clearly_better' not in llmhtml
assert llm.count('above_reference')>=5 and llmhtml.count('above_reference')>=5
assert 'above_reference = bool(acc - 2 * se > 0.79)' in llm
assert 'интервала одной доли' in llm and 'paired_lower' in llm and 'within_margin' in llm
out={'status':'accepted actual files; UI independently owned by coordinator','html_sha256':sha(rendered),'source_sha256':sha(source),'resource_version':re.search('data-v="([^"]+)"',rendered).group(1),'linked_resources_sha256':resources,'counts':{'conditions':14,'options':56,'feedback':56,'keys':14},'new_revisions':prepared['changed'],'ten_other_source_blocks_byte_identical':prepared['unchanged_byte_identical'],'ten_other_html_options_feedback_equal_to_baseline':10,'revisions':ch['test']['revisions'],'unique_longest_correct':after['unique_longest_correct'],'longest_ties':after['longest_ties'],'unique_shortest_correct':after['unique_shortest_correct'],'shortest_ties':after['shortest_ties'],'minpassing':12,'llm_context':'above_reference fixed-number exercise; paired comparison follows; clearly_better absent','rows':rows}
(base/'actual-acceptance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','linked_resources_sha256','revisions']},ensure_ascii=False,indent=2))
