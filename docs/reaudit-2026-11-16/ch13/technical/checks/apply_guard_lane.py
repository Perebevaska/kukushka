from pathlib import Path
import re,json,hashlib,ast,difflib,shutil
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course');p=Path('/private/tmp/kuch13round/checks');d=root/'docs/reaudit-2026-11-16/ch13/technical/checks';d.mkdir(exist_ok=True)
# Execute generator only to load named candidate mappings. It touches private files, not course source.
ns={};exec(compile((p/'propose_patch.py').read_text(),str(p/'propose_patch.py'),'exec'),ns)
collections={k:ns[k] for k in ['changes','setups','solutions','texts']};applied=[];before={};after={};diff=[]
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
def fields(content):
 result={}
 for segment in re.split(r'(?m)(?=^## task: )',content)[1:]:
  id=segment.split(' |',1)[0].split('## task: ')[1];f={}
  for kind in ['setup','starter','check','solution']:
   match=re.search(r'(?ms)^### '+kind+r'\s*\n```python[^\n]*\n(.*?)\n```',segment)
   val=match[1] if match else '';ast.parse(val)
   f[kind]={'sha256':sha(val),'ast_sha256':sha(ast.dump(ast.parse(val),include_attributes=False)),'code':val}
  result[id]=f
 return result
for f in sorted((root/'content/ch13').glob('*.md')):
 old=f.read_text();before[f.name]={'sha256':sha(old),'tasks':fields(old)}
 parts=re.split(r'(?m)(?=^## task: )',old);new=parts[0]
 for segment in parts[1:]:
  id=segment.split(' |',1)[0].split('## task: ')[1];key=f.stem,id
  for field,collection in [('check',collections['changes']),('setup',collections['setups']),('solution',collections['solutions'])]:
   if key in collection:
    pattern=r'(?ms)(^### '+field+r'\s*\n```python[^\n]*\n)(.*?)(\n```\s*(?=\n### |\Z))'
    segment,n=re.subn(pattern,lambda m:m[1]+collection[key].rstrip()+m[3],segment,count=1);assert n,(key,field);applied.append([f.name,id,field])
  if key in collections['texts']:
   i=segment.index('\n### ');segment=segment[:i]+collections['texts'][key]+segment[i:];applied.append([f.name,id,'condition-addition'])
  if key==('03-classify','recall95'):
   segment=segment.replace('`recall_score(y_test, (p >= t).astype(int))`','`recall_score(y_validation, (p >= t).astype(int))`').replace('if recall_score(y_test, (p >= t).astype(int)) >= 0.95','if recall_score(y_validation, (p >= t).astype(int)) >= 0.95');applied.append([f.name,id,'two-hints'])
  new+=segment
 after[f.name]={'sha256':sha(new),'tasks':fields(new)}
 if new!=old:
  snapshot=d/'editor-before'/f.name;snapshot.parent.mkdir(exist_ok=True);snapshot.write_text(old)
  f.write_text(new);diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/content/ch13/'+f.name,tofile='b/content/ch13/'+f.name))
assert sum(len(v['tasks']) for v in before.values())==65
assert sum(len(v['tasks']) for v in after.values())==65
changed=[]
for name,v in before.items():
 for id,f in v['tasks'].items():
  for field,b in f.items():
   a=after[name]['tasks'][id][field]
   if a['sha256']!=b['sha256']:changed.append([name,id,field])
expected=[v for v in applied if v[2] in ['check','setup','solution']]
assert sorted(changed)==sorted(expected),(changed,expected)
assert before['04c-llm.md']['tasks']['parse-llm']==after['04c-llm.md']['tasks']['parse-llm'],'SDK parse blocks changed unexpectedly'
# Hints/conditions and field replacements must commute with unchanged expert prose.
proof={'before':before,'after':after,'applied':applied,'actual_changed_65x4':changed,'all_65x4_ast_valid':True,'sdk_parse_4fields_unchanged':True,'harness_untouched_sha256':hashlib.sha256((root/'site/assets/harness.py').read_bytes()).hexdigest(),'expected_changes_equal_actual':True}
(d/'guard-editor-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));(d/'guards-applied.patch').write_text(''.join(diff))
# Portable evidence: authoritative artifacts do not depend on the scratch folder for code/data imports.
for f in ['programs.jsonl','extra-programs.jsonl','freeze-manifest.json','extra-freeze.json','run_native.py','run_pyodide.mjs','run_native_extra.py','run_pyodide_extra.mjs','frozen_harness.py','public-contracts-before-checks.json','source-manifest.json']:
 shutil.copy2(p/f,d/f)
for folder in ['programs','extra-programs','data','historical','proposal']:
 shutil.copytree(p/folder,d/folder,dirs_exist_ok=True)
print('APPLIED',len(changed),'code fields;',len(collections['changes']),'checks; SDK parse unchanged; harness not touched')
