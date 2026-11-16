"""Compare released hashes and compiled tasks with their public HTML payloads."""
import hashlib
import json
import re
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
chapter = here.parents[1]
root = chapter.parents[2]
snapshot = chapter/'technical/chapter-export.json'
records = json.loads(snapshot.read_text())
manifest = json.loads((chapter/'technical/release.json').read_text())
full_export = Path(sys.argv[1])
assert records == [r for r in json.loads(full_export.read_text()) if r['lesson'].startswith('ch10/')]
tasks = {(r['lesson'],r['id']):r for r in records if r['kind']=='task'}

def mismatched_hashes(base, expected):
    return [name for name, sha in expected.items() if hashlib.sha256((base/name).read_bytes()).hexdigest()!=sha]

seen=set()
bad=[]
order=[]
for path in sorted((root/'site/ch10').glob('*.html')):
    html=path.read_text()
    match=re.search(r'<script[^>]*id="lesson-data"[^>]*>(.*?)</script>',html,re.S)
    if not match:
        continue
    page=json.loads(match[1])
    for card in page['tasks']:
        key=(page['lesson'],card['id'])
        seen.add(key)
        diff=[field for field in ('setup','starter','check','solution') if (tasks[key][field] or '').strip()!=(card[field] or '').strip()]
        if diff:bad.append(dict(key=key,fields=diff))
    if path.stem=='05-project':
        order=[card['id'] for card in page['tasks']]
        visible=re.sub(r'<[^>]+>',' ',html[:match.start()])
        letter='После расчётов самостоятельно напишите короткое письмо директору.' in visible
assert seen==tasks.keys()
result=dict(export_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),full_export_sha256=hashlib.sha256(full_export.read_bytes()).hexdigest(),records=len(records),html_cards_checked=len(seen),four_field_mismatches=bad,release_files_checked=len(manifest['files']),release_data_checked=len(manifest['data']),file_hash_mismatches=mismatched_hashes(root,manifest['files']),data_hash_mismatches=mismatched_hashes(root/'site/data',manifest['data']),letter_before_grader=letter,published_order=order)
(here/'published-final.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(result)
