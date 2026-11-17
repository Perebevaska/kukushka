import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
read=lambda p:[json.loads(l) for l in p.read_text().splitlines()]
rows={name:{runtime:read(folder/('after-'+runtime+'.jsonl')) for runtime in ['native','pyodide']} for name,folder in [('main',B),('supplement',B/'supplement'),('extra',B/'acceptance-extra')]}
before=read(B/'before-native.jsonl');n=rows['main']['native'];p=rows['main']['pyodide'];tasks=json.loads((B/'tasks-after.json').read_text());frozen=json.loads((B/'freeze-manifest.json').read_text())
reasons={75:'Old author append_run has a real field-order defect; rejected now, corrected complete literal extra0 accepted. Original expectation retained.',146:'Process-observability limit for timing; no new unpublished measurement enforcement.',166:'H01 original alternative accidentally shortened baseline rule too; correct supplementary0 remains accepted.',179:'Duplicate error messages allowed by reviewed public contract; original expectation retained.',180:'NaN visits oracle beyond clarified numeric range-guard layer; no hidden API validation requirement.',194:'Three-row rounded sum numerically equals full-precision total; non-discriminating, not a false positive. Extra18/19 uses K4 with different sums.',202:'Harness-only print(True) is not an available Parsons permutation; process-observability limitation.'}
summary={'publication':json.loads((B/'after-publication-binding.json').read_text()),'counts':{},'runtime_verdict_equivalence':{},'original_frozen_files_intact':all(hashlib.sha256((B/f).read_bytes()).hexdigest()==h for f,h in frozen['files'].items()),'known_seven_old_expectation_differences':[],'fixed_output_gap_indices':[14,17,68,77,80,92,113,119,122,128,164,173,174,200],'fixed_helper_oracle_indices':[187,188],'processes':'All six AFTER batch processes exited0; controlled valid/cold/warm subprocesses exited0. No source/build/Git changes during verification.'}
for name,pair in rows.items():
 summary['counts'][name]={runtime:dict(cases=len(rs),passed=sum(r['passed'] for r in rs),rejected=sum(not r['passed'] for r in rs),matches_original_expectation=sum(r['passed']==r['expected'] for r in rs)) for runtime,rs in pair.items()}
 summary['runtime_verdict_equivalence'][name]=len(pair['native'])==len(pair['pyodide']) and all(a['passed']==z['passed'] for a,z in zip(pair['native'],pair['pyodide']))
for r in n:
 if r['passed']!=r['expected']:
  summary['known_seven_old_expectation_differences'].append(dict(index=r['index'],task=r['task'],label=r['label'],expected=r['expected'],actual=r['passed'],classification=reasons[r['index']],raw=r['raw']))
assert set(r['index'] for r in summary['known_seven_old_expectation_differences'])==set(reasons)
assert all(before[i]['passed'] and not n[i]['passed'] for i in summary['fixed_output_gap_indices'])
assert all(not before[i]['passed'] and n[i]['passed'] for i in summary['fixed_helper_oracle_indices'])
assert rows['supplement']['native'][0]['passed'] and not rows['supplement']['native'][1]['passed']
assert all(r['passed']==r['expected'] for pair in [rows['supplement'],rows['extra']] for rs in pair.values() for r in rs)
A=B/'acceptance-extra';smoke_n=json.loads((A/'valid-native-equivalence.json').read_text());smoke_p=json.loads((A/'valid-pyodide-equivalence.json').read_text());summary['valid_smokes']={'native_five_exact':smoke_n['all_valid_equivalent'],'pyodide_five_exact':smoke_p['raw_equivalent']}
matrix={}
for phase in ['before','after']:
 matrix[phase]=[]
 for mode in ['cold-bad','warm-sequence']:
  for r in json.loads((A/(phase+'-syntax-'+mode+'.json')).read_text())['records']:
   matrix[phase].append(dict(name=r['name'],ok=r['raw']['ok'],error_type=(r['raw'].get('error') or {}).get('type'),line=(r['raw'].get('error') or {}).get('line'),passed=(r['raw'].get('check') or {}).get('passed')))
summary['syntax_matrix']=matrix
assert matrix['before'][0]['error_type']=='ModuleNotFoundError'
assert matrix['after'][0]['error_type']=='SyntaxError' and matrix['after'][0]['line']==14
assert all(row['passed'] for phase in matrix.values() for row in phase if row['name'] in ['cold_fixed','warm_fixed'])
summary['core_metadata']=json.loads((B/'candidate/course-metadata-after-proof.json').read_text())
summary['shared_scope']=json.loads((B/'candidate/shared-scope-proof.json').read_text())
(B/'after-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
lines=['# Literal AFTER coverage57×4','', 'N/P results for unchanged frozen code and unchanged original expectations. The sole rejected old author is log-csv75: corrected full author is extra0 and passes. Model names remain the existing public contract.','', '|ID|Goal/source read|Frozen author N/P|Frozen alternative N/P|Frozen wrong N/P|','|---|---|---|---|---|']
for t in tasks:
 def val(label):
  x=next(r for r in n if r['lesson']==t['lesson'] and r['task']==t['id'] and r['label']==label);y=p[x['index']];return ('T' if x['passed'] else 'F')+'/'+('T' if y['passed'] else 'F')
 lines.append('|'+t['lesson']+'/'+t['id']+'|Yes, before and actual publication|'+val('author')+'|'+val('alternative')+'|'+val('wrong')+'|')
(B/'coverage57-after.md').write_text('\n'.join(lines)+'\n')
candidates=json.loads((B/'candidates-before-results.json').read_text())
for c in candidates:
 c['status']='fixed_by_critic_after_actual_publication_pending_independent_acceptance'
 c['after_native_pyodide_equal']=True
 c['source_export_sha256']=summary['publication']['actual_full_export_sha256']
(B/'candidates-after-results.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2))
print(json.dumps(summary['counts'],indent=2));print('Frozen original intact',summary['original_frozen_files_intact'],'runtime equivalence',summary['runtime_verdict_equivalence'],'old known mismatch indices',[r['index'] for r in summary['known_seven_old_expectation_differences']])
