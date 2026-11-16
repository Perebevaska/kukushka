from pathlib import Path
import json,re,hashlib,ast,difflib
root=Path('/Users/dmitriikormin/Documents/Projects/ds-course');d=root/'docs/reaudit-2026-11-16/ch13/technical/checks';f=root/'content/ch13/04c-llm.md';old=f.read_text();parts=re.split(r'(?m)(?=^## task: )',old);new=parts[0]
for segment in parts[1:]:
 if segment.startswith('## task: llm-check |'):
  previous=segment
  segment=segment.replace('clearly_better','above_reference')
  segment=segment.replace('`above_reference` — `True`, только если даже нижняя граница выше 0.79 (точность модели тем из урока «Классификация текстов»).','`above_reference` — `True`, только если неокруглённая нижняя граница интервала этой одной доли правильных выше фиксированного числа 0.79. Это сравнение с числом, а не доказательство разницы между моделями: парная проверка двух систем на одних отзывах будет в следующей задаче.')
  segment=segment.replace('ans = pd.Series(llm_topic)\ntrue = check["topic"]\n\n```','ans = pd.Series(llm_topic)\ntrue = check["topic"]\n# above_reference: нижняя граница одного интервала выше фиксированного числа 0.79\n\n```',1)
  segment=segment.replace("'above_reference: сравните с 0.79 нижнюю границу low, а не саму долю.'", "'above_reference: сравните неокруглённую нижнюю границу с фиксированным числом0.79; это не парная разница моделей.'")
  segment=segment.replace('above_reference = low > 0.79','above_reference = bool(acc - 2 * se > 0.79)')
  segment=segment.replace('Погрешность — `se = math.sqrt(acc * (1 - acc) / len(true))` по неокруглённой доле.', 'Погрешность — `se = math.sqrt(acc * (1 - acc) / len(true))` по неокруглённой доле. Для `above_reference` сравните `acc - 2 * se` с 0.79. Такое сравнение не оценивает разницу двух моделей.')
  segment=segment.replace('В этом синтетическом опыте верны 82,5 % ответов. Доля 0,79 попадает в приближённый интервал 0,771–0,879. Для вывода о допустимом проигрыше задайте границу заранее и сравните две системы на одних и тех же отзывах.', 'В этом синтетическом опыте верны 82,5 % ответов. Фиксированное число 0,79 попадает в приближённый интервал 0,771–0,879, поэтому `above_reference` равно `False`. Даже значение `True` означало бы только, что нижняя граница интервала одной доли выше этого числа. Разницу качества двух моделей оценивают по парным ответам на одни и те же отзывы; такая проверка будет дальше.')
  assert 'clearly_better' not in segment
  assert segment!=previous
 new+=segment
(d/'llm-reference-before.md').write_text(old);f.write_text(new);(d/'llm-reference-applied.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/content/ch13/04c-llm.md',tofile='b/content/ch13/04c-llm.md')))
# Capture final65x4 and verify SDK parser fields survived both lanes.
proof={'cards':[],'source_sha256':{},'harness_sha256':hashlib.sha256((root/'site/assets/harness.py').read_bytes()).hexdigest()}
for source in sorted((root/'content/ch13').glob('*.md')):
 text=source.read_text();proof['source_sha256'][source.name]=hashlib.sha256(text.encode()).hexdigest()
 for segment in re.split(r'(?m)(?=^## task: )',text)[1:]:
  id=segment.split(' |',1)[0].split('## task: ')[1];fields={}
  for k in ['setup','starter','check','solution']:
   m=re.search(r'(?ms)^### '+k+r'\s*\n```python[^\n]*\n(.*?)\n```',segment);code=m[1] if m else '';ast.parse(code);fields[k]={'sha256':hashlib.sha256(code.encode()).hexdigest(),'ast_sha256':hashlib.sha256(ast.dump(ast.parse(code),include_attributes=False).encode()).hexdigest(),'code':code}
  condition=segment.split('\n### ',1)[0]
  proof['cards'].append(dict(lesson='ch13/'+source.stem,id=id,fields=fields,public_condition=condition,public_names=re.findall(r'`([^`]+)`',condition)))
assert len(proof['cards'])==65
original=json.loads((d/'guard-editor-proof.json').read_text())['before']['04c-llm.md']['tasks']['parse-llm'];current=next(t for t in proof['cards'] if t['id']=='parse-llm')['fields'];assert original==current
proof['sdk_parse_4fields_byte_unchanged']=True;proof['all65x4_ast_valid']=True
(d/'actual-source65x4-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print('LLM renamed above_reference; final65x4 AST and SDK parse invariance verified')
