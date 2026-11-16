from pathlib import Path
import json,re,hashlib,ast
p=Path('/private/tmp/kuch13round/checks');d=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch13/technical/checks');rows=list(map(json.loads,(p/'programs.jsonl').read_text().splitlines()));m=[];reclassification=[]
for i,r in enumerate(rows):
 if r['task']=='parse-llm' and r['expected']:
  code,n=re.subn(r'(?m)^(    bad = .*)$',r'\1\n    if not isinstance(answer, str):\n        return bad',r['code'],count=1);assert n,(i,r['label']);why='SDK→parser: None явно объявлен негодным ответом; прежняя формулировка для строк не задавала этот случай однозначно.'
 elif r['label']=='only-public-task-outputs':
  code=r['code']+'\np_test=model.predict_proba(X_test)[:,1]\ntest_recall=round(recall_score(y_test,p_test>=thr),3)\ntest_flagged=int((p_test>=thr).sum())\n';why='В условии теперь явно объявлены test_recall/test_flagged и новый p_test.'
 elif r['task']=='llm-check' and r['expected']:
  code=r['code'].replace('clearly_better','above_reference').replace('above_reference = low > 0.79','above_reference = bool(acc - 2 * se > 0.79)');why='T13-01: above_reference означает сравнение интервала одной accuracy с фиксированным числом0.79, а не превосходство над моделью.'
 else:continue
 ast.parse(code);m.append(dict(r,source_program_index=i,source_code_sha256=r['code_sha256'],label='migration--'+r['label'],code=code,expected=True,code_sha256=hashlib.sha256(code.encode()).hexdigest(),migration_reason=why))
 reclassification.append(dict(index=i,label=r['label'],old_expected=True,new_expected_original_code=False,reason=why))
(d/'migration-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in m));(d/'output-contract-migrations.json').write_text(json.dumps({'original_programs235_sha256':hashlib.sha256((p/'programs.jsonl').read_bytes()).hexdigest(),'original_extra18_sha256':hashlib.sha256((p/'extra-programs.jsonl').read_bytes()).hexdigest(),'migrations_sha256':hashlib.sha256((d/'migration-programs.jsonl').read_bytes()).hexdigest(),'reclassifications':reclassification,'non_discriminating_original_probe':{'index':44,'frozen_expected':False,'correct_for_same_fixture_result':True,'reason':'Оба способа дают n_barista=146 на данной fixture; не использовать как доказательство дефекта.'}},ensure_ascii=False,indent=2))
print('MIGRATIONS',len(m));print('original current expectations changed only in separate manifest, not original code/expected')
