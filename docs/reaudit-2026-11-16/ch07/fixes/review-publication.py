"""Match runnable content of the 93 HTML/catalog cards and record the delta after the 81 originals."""
from hashlib import sha256
from pathlib import Path
import json
import re

chapter=Path(__file__).resolve().parent.parent
site=chapter.parents[2]/'site'
prior={r['lesson']+'/'+r['id']:r for r in json.loads((chapter/'check-evidence/tasks-reviewed.json').read_text()) if r['lesson']!='ch07/contracts'}
cat=json.loads((site/'notebooks/tasks/ch07.json').read_text())['tasks']
html={}
for f in (site/'ch07').glob('*.html'):
    match=re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>',f.read_text(),re.S)
    if match:
        d=json.loads(match[1])
        html.update({d['lesson']+'/'+t['id']:t for t in d['tasks']})
assert set(prior)==set(cat)==set(html) and len(html)==93
fields=['check','setup','solution','starter']
value=lambda row,k:(row.get(k) or '').strip()
changed={}
for k in prior:
    delta=[f for f in fields if value(prior[k],f)!=value(cat[k],f)]
    if delta: changed[k]=delta
    assert all(value(html[k],f)==value(cat[k],f) for f in fields)
assert changed=={'ch07/09-project/pipe':['check'],'ch07/03-threshold/roc-plot':['check']}
revision=json.loads((chapter/'technical/release.json').read_text())
for name,digest in revision['files'].items():
    assert sha256((site.parent/name).read_bytes()).hexdigest()==digest
summary={'release_sha256':sha256((chapter/'technical/release.json').read_bytes()).hexdigest(),'all_release_files_match':len(revision['files']),'published_html_cards':len(html),'published_notebook_cards':len(cat),'mismatched_html_notebook_fields':[],'fields_compared':fields,'delta_from_81_programs_snapshot':changed,'chapter_export_sha256':revision['chapter_snapshot_sha256']}
(chapter/'fixes/review-publication.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
