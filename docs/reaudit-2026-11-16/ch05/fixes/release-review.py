"""Cross-check the chapter hash manifest, shipped contracts, attempt IDs and numerical replay."""
from hashlib import sha256
import json
from pathlib import Path
import re
from html.parser import HTMLParser
import sys

here=Path(__file__).resolve().parent
chapter=here.parent
root=chapter.parents[2]
def j(path):
    return json.loads(path.read_text())
def digest(path):
    return sha256(path.read_bytes()).hexdigest()
def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
release=j(chapter/'technical/release.json')
assert digest(chapter/'technical/chapter-export.json') == release['chapter_snapshot_sha256']
for name, expected in release['files'].items():
    assert digest(root/name)==expected, name
for name, expected in release['data'].items():
    assert digest(root/'site/data'/name)==expected, name
source=j(chapter/'technical/chapter-export.json')
catalog=j(root/'site/notebooks/tasks/ch05.json')['tasks']
matches=0
seen=set()
for page in (root/'site/ch05').glob('[0-9]*.html'):
    html=page.read_text()
    data=json.loads(re.search(r'id="lesson-data">(.*?)</script>',html,re.S)[1])
    for item in data['tasks']:
        short=data['lesson'][5:]+'/'+item['id']
        full='ch05/'+short
        seen.add(short)
        old=next(x for x in source if x['kind']=='task' and x['lesson']+'/'+x['id']==full)
        for field in ('check','setup','solution'):
            assert (item[field] or '')==(old[field] or ''), (short,field)
            if full in catalog:
                assert (item[field] or '')==(catalog[full][field] or ''), (short,field,'notebook')
        matches+=full in catalog
assert len(seen)==90 and matches==90 and sum(not t['parsons'] for t in catalog.values())==82
for path in (root/'content/ch05').glob('*.md'):
    for kind in ('predict','quiz'):
        seen.update(f'{path.stem}/{kind}/{n+1}' for n,_ in enumerate(re.finditer('^::: '+kind+r'\b',path.read_text(),re.M)))
initial=rows(chapter/'student/initial-attempts.jsonl')
retry=rows(chapter/'student/retest-attempts.jsonl')
assert seen=={r['id'] for r in initial if r['passed']} and len(seen)==135
expected=j(chapter/'technical/retest-targets.json')
assert set(expected)=={r['id'] for r in retry if r['passed']}
for attempt in (initial,retry):
    assert all(x['expect'] for x in attempt)
class VisibleCopy(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden=False
        self.chunks=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden=True
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=False
    def handle_data(self, data):
        if not self.hidden: self.chunks.append(data)
copy=VisibleCopy()
copy.feed((root/'site/ch05/05-hypotheses.html').read_text())
visible=' '.join(copy.chunks)
assert 'примерно в 0.14 % случаев' in visible and '99.86 % эффект есть' in visible
assert 'примерно в 0.12 % случаев' not in visible
# Quiz contents, rendered policy and actual threshold observations are separate evidence.
quiz_src=(root/'content/ch05/test.md').read_text()
quiz=re.findall(r'(?ms)^::: quiz.*?\n(.*?)^:::',quiz_src)
options=[re.findall(r'(?m)^- \[([x ])\] (.*)\n  > (.*)$',q) for q in quiz]
assert len(options)==13 and all(len(opts)==4 and sum(flag=='x' for flag,_,_ in opts)==1 and all(r for _,_,r in opts) for opts in options)
unique=0
for opts in options:
    key=next(len(value) for flag,value,_ in opts if flag=='x')
    unique+=int(all(key>len(value) for flag,value,_ in opts if flag==' '))
assert unique==4
assert [r['correct'] for r in j(chapter/'technical/test-ui.json')]==[10,11]
results=j(Path(sys.argv[1]))
previous=j(chapter/'technical/expert-results.json')
numeric_fields=[k for k in results if k!='examples']
assert all(results[k]==previous[k] for k in numeric_fields)
assert len(results['examples'])==77 and all(r['ok'] for r in results['examples'])
changed=[(r['lesson'],r['id']) for r,old in zip(results['examples'],previous['examples']) if r!=old]
newbook=j(here/'notebook-received.json')
assert digest(chapter/'student/promise.ipynb')==newbook['notebook_sha256']
assert 'каждого города' in (root/'site/notebooks/ch05-project-template.ipynb').read_text()
for file in ['review-probes-final.json','review-notebook-final.json','historical-probes-final.json','historical-notebook-final.json']:
    evidence=j(here/file)
    assert all(x['actual']==x['expected'] for x in evidence['rows']), file
    for x in evidence['rows']:
        task=next(t for t in source if t['kind']=='task' and t['lesson']=='ch05/'+x['lesson'] and t['id']==x['id'])
        assert sha256(task['check'].encode()).hexdigest()==x['check_sha256'], (file,x['id'])
repeated=rows(here/'repeated-current.jsonl')[1:]
assert len(repeated)==37 and all(x['matches'] for x in repeated)
print(json.dumps(dict(verified_publication_files=len(release['files']),verified_datasets=len(release['data']),
  revised_example_explanation_percent=0.14,release_manifest=digest(chapter/'technical/release.json'),browser_export_contracts=len([r for r in source if r['kind']=='task']),
  notebook_catalog_contracts=matches,non_parsons_notebook_cards=82,accepted_unique_items=len(seen),second_pass=len(retry),second_pass_distinct=len(set(x['id'] for x in retry)),
  tests=len(options),options=sum(map(len,options)),correct_unique_longest=unique,
  numerical_profiles_identical=numeric_fields,example_or_prediction_runs=77,changed_example_outputs=changed,
  expected_verdicts={'original_critic_cases':37,'independent_html':21,'independent_notebook':21,'historical_html':7,'historical_notebook':7},
  binding={'notebook_digest':newbook['notebook_sha256'],'expert_replay_digest':digest(Path(sys.argv[1]))}),ensure_ascii=False,indent=2))
