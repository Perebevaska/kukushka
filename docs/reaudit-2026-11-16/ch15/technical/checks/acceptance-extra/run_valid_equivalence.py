import hashlib,importlib.util,json,os,sys,tempfile
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[5];P=B.parent
inputs=json.loads((B/'syntax-inputs.json').read_text())
paths={'before':P/'frozen_harness.py','after':ROOT/'site/assets/harness.py'}
records=[];modules={}
for label,path in paths.items():
 spec=importlib.util.spec_from_file_location('_syntax_'+label,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);modules[label]=mod
for probe in inputs['valid_smokes']:
 row={'name':probe['name'],'results':{}}
 for phase,mod in modules.items():
  with tempfile.TemporaryDirectory() as folder:
   old=os.getcwd();os.chdir(folder)
   try:raw=mod.run(probe['code'],None,probe['setup'],probe['show_last'])
   finally:os.chdir(old)
  row['results'][phase]=raw
 row['exactly_equal']=row['results']['before']==row['results']['after']
 actual=row['results']['after'];expected=probe['expected'];checks=[]
 for key,value in expected.items():
  checks.append((len(actual['figs'])==value) if key=='figures' else ((actual.get('error') or {}).get('type')==value) if key=='error_type' else ((actual.get('error') or {}).get('line')==value) if key=='line' else actual[key]==value)
 row['expected_matches']=all(checks);records.append(row)
out=dict(python=sys.version,paths={key:dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for key,path in paths.items()},records=records,all_valid_equivalent=all(r['exactly_equal'] and r['expected_matches'] for r in records))
(B/'valid-native-equivalence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('valid-equivalence',len(records),out['all_valid_equivalent']);sys.exit(0 if out['all_valid_equivalent'] else 1)
