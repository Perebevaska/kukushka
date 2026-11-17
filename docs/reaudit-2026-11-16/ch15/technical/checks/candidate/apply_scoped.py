"""Preview only by default. --apply requires coordinator's explicit ROOT APPLY."""
import ast,difflib,hashlib,json,re,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[5]
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
changes=json.loads((BASE/'task-field-replacements.json').read_text())
byfile={}
for item in changes:byfile.setdefault(ROOT/'content'/(item['lesson']+'.md'),[]).append(item)
patch=[];proof=[];prepared={}
for path,items in byfile.items():
 before=path.read_text();updates=[]
 for item in items:
  task=re.search(r'^## task: '+re.escape(item['task'])+r'\s*\|.*?(?=^## task:|\Z)',before,re.M|re.S)
  assert task,(path,item['task'])
  field=re.search(r'^### '+re.escape(item['field'])+r'\s*\n```python\n(.*?)\n```',task.group(),re.M|re.S)
  assert field,(path,item['task'],item['field'])
  actual=field.group(1)
  assert actual.strip()==item['old'].strip(),f'{path.name}/{item["task"]}/{item["field"]}: code changed since freeze; review instead of overwriting'
  ast.parse(item['new'])
  start,end=task.start()+field.start(1),task.start()+field.end(1)
  updates.append((start,end,item['new'].rstrip(),item))
 after=before
 for start,end,new,item in sorted(updates,key=lambda x:x[0],reverse=True):after=after[:start]+new+after[end:]
 before_outer=before;after_outer=after
 # Redact exactly the authorized code fields in both texts; every other byte must match.
 for item in items:
  def redact(text):
   task=re.search(r'^## task: '+re.escape(item['task'])+r'\s*\|.*?(?=^## task:|\Z)',text,re.M|re.S)
   field=re.search(r'^### '+re.escape(item['field'])+r'\s*\n```python\n(.*?)\n```',task.group(),re.M|re.S)
   a,b=task.start()+field.start(1),task.start()+field.end(1)
   return text[:a]+'<AUTHORIZED-CODE-FIELD>'+text[b:]
  before_outer=redact(before_outer);after_outer=redact(after_outer)
 assert before_outer==after_outer,'Prose outside authorized fields changed'
 prepared[path]=after
 proof.append(dict(path=str(path.relative_to(ROOT)),before_sha256=sha(before),after_sha256=sha(after),outside_authorized_fields_sha256=sha(before_outer),outside_authorized_fields_identical=True,fields=[dict(task=i['task'],field=i['field']) for i in items]))
 patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+str(path.relative_to(ROOT)),tofile='b/'+str(path.relative_to(ROOT))))
for relative,stem in [('site/assets/harness.py','harness'),('tools/build.py','build')]:
 path=ROOT/relative;before=path.read_text();expected=(BASE/(stem+'-before.py')).read_text();after=(BASE/(stem+'-after.py')).read_text();assert before==expected,f'{relative}: changed since preparation; review needed';ast.parse(after);prepared[path]=after
 proof.append(dict(path=relative,before_sha256=sha(before),after_sha256=sha(after),task_fields=False,scope='run precompilation only' if stem=='harness' else 'add ch15 to existing coreQuestions chapter allowlist'))
 patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
(BASE/'technical-proposed.patch').write_text(''.join(patch));(BASE/'changed-fields.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
if '--apply' in sys.argv:
 for path,after in prepared.items():path.write_text(after)
 (BASE/'apply-proof.json').write_text(json.dumps(dict(applied=True,files=proof),ensure_ascii=False,indent=2))
 print('APPLIED',len(prepared),'files after explicit coordinator authorization')
else:print('PREVIEW ONLY',len(prepared),'files;',len(changes),'task fields; all prose preserved')
