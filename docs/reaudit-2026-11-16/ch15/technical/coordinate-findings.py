from pathlib import Path
import json,re,hashlib
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch15'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def chunks(s):return [x.strip()for x in s.split('\n\n')if x.strip()]
def excerpt(s,i):
 # Preserve the complete table row or complete paragraph, not a generated topical summary.
 for line in s.splitlines():
  if line.startswith('|') and i in line:return line
 return next((p for p in chunks(s)if i in p),'')
spec=[('expert.md',[f'E15-{i:02}'for i in range(1,9)]),('business.md',[f'B15-{i:02}'for i in range(1,8)]),('methodist.md',[f'M15-26-{i:02}'for i in range(1,9)]),('test-review.md',[f'Q15-{i:02}'for i in range(1,9)]),('program.md',[f'PR15-{i:02}'for i in range(1,7)]),('checks.md',[f'AC15-{i:02}'for i in range(1,15)]+['AC15-H01','AC15-H02']),('review-before.md',[f'R15-{i:02}'for i in range(1,5)]),('project-review.md',[f'PS15-{i:02}'for i in range(1,4)]),('student/report-initial.md',[f'ST-{i:02}'for i in range(1,8)]),('recipient/receipt-report.md',[f'RCP15-{i:02}'for i in range(1,7)])]
review=(D/'review-before.md').read_text();rows=[]
for filename,expected in spec:
 source=D/filename;text=source.read_text()
 pattern={'methodist.md':r'\bM15-26-\d{2}\b'}.get(filename,rf'\b{re.escape(expected[0].rsplit("-",1)[0])}-(?:\d{{2}}|H\d{{2}})\b')
 actual=set(re.findall(pattern,text));require=set(expected);assert actual==require,(filename,actual^require)
 for i in expected:
  finding=excerpt(text,i);assert finding
  decision=excerpt(review,i)
  if i.startswith('R15-'):decision=finding
  elif i.startswith('PS15-'):decision=finding
  elif i.startswith('RCP15-'):decision=finding
  elif i in ['AC15-H01','AC15-H02']:decision=finding
  assert decision,(filename,i,'no adjudication')
  if i=='RCP15-04':remaining='No blocking failure: exact replay MD5 independently matched. Optional wording: distinguish replay of original release from permitted rescoring of updated DB; no blanket mismatch-rejection contract.'
  elif i.startswith('RCP15-'):remaining='Initial recipient execution passed; preserve27actual checks and53input hashes. Rerun only affected contract/outputs after student changes; Docker and causal pilot are separate.'
  elif i in ['AC15-H01','AC15-H02']:remaining='Procedural probe/transport correction already documented; frozen programs preserved. No learner lesson failure inferred.'
  else:remaining='After-edit acceptance pending actual source/export diff and targeted evidence; do not inherit a closed verdict from prose edits. Relevant raw proof and acceptance criterion are in the complete finding/adjudication above.'
  rows.append({'id':i,'source':filename,'source_sha256':sha(source),'finding_full':finding,'adjudication_source':'review-before.md' if i not in ['AC15-H01','AC15-H02'] and not i.startswith(('PS15-','RCP15-','R15-')) else filename,'adjudication_full':decision,'evidence':{'source':filename,'review':'review-before.md','raw_links_preserved_in_full_text':True},'remaining':remaining,'status':'initial independently adjudicated; final acceptance not yet issued'})
judge=(D/'judge/decision.md').read_text()
for i,selector,remaining in [
 ('J15-CHOSEN-A','## Сравнение','Preserve independently frozen anonymous A/B inputs and chosenA; choice is not proof of company profit.'),
 ('J15-ZERO-DENOM','no observed churn','B wording is imprecise: C0516 churned but R=0 gives zero retained-margin denominator; money result unchanged.'),
 ('J15-CASE-SCOPE','965','Judge965input/independent comparison cases are not learner card attempts, probability counts or chapter quiz denominators.')]:
 full=next((p for p in chunks(judge)if selector in p),judge[:judge.find('\n\n')]);rows.append({'id':i,'source':'judge/decision.md','source_sha256':sha(D/'judge/decision.md'),'finding_full':full,'adjudication_full':full,'evidence':{'raw':'judge/recomputed.json','script':'judge/recompute.py','inputs':'judge/ (frozen original common brief and anonymous authors)'},'remaining':remaining,'status':'initial decision preserved; no rejudging solely for course edits'})
history=json.loads((D/'previous.json').read_text())['rows'];history_text=(D/'review-history.md').read_text()
for h in history:
 decision=excerpt(history_text,h['id']);assert decision
 rows.append({'id':h['id'],'scope':'historical','source':h['source'],'finding_full':h['full_finding'],'adjudication_source':'review-history.md','adjudication_full':decision,'evidence':{'original_full_source':'historical/'+h['source'],'register':'previous.json'},'remaining':'Current status per reviewer historical row; after acceptance must preserve any external owner/action rather than blanket-close historical findings.'})
meta={'scope':'EXPLICIT SET completeness by originating report, one adjudication/evidence/remaining mapping per named finding; cross-role overlaps retained, never a unique-defect count','expected_sets':{name:ids for name,ids in spec},'current_named_count':sum(len(ids)for _,ids in spec),'judge_named_count':3,'historical_count':80,'rows':rows}
(D/'coordination-findings.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
lines=['# Полный реестр решений главы15','','Единица — устойчивое замечание исходной роли; совпадающие причины не складываются в независимые дефекты. Полные исходные формулировки, решения, свидетельства и остаток находятся в [coordination-findings.json](coordination-findings.json). Это исходная adjudication, не финальная приёмка редакции.','','| Источник | Полный ожидаемый набор | Покрыто |','|---|---|---|']
for name,ids in spec:lines.append('| '+name+' | '+', '.join(ids)+' | '+str(len(ids))+'/'+str(len(ids))+' |')
lines+=['| Судья | J15-CHOSEN-A, J15-ZERO-DENOM, J15-CASE-SCOPE | 3/3 |','| История previous.json | Все80исходныхстрок/аспектов | 80/80 |','','RCP15-04 не является общим требованием отклонять изменённую базу: исходныйMD5 совпал независимо; разрешённый пересчёт новых данных отличается от воспроизведения. Точная формулировка получателя сохранена полностью. AC15-H01/H02 — ошибки конструкции пробы и передачи ресурса с документированным восстановлением, не два новых дефекта курса.','','Реестр не читает личное глобальное интервью студента. Исходные128SHA и публичные83SHA проверяются отдельно. Для конечного статуса каждому принятому изменению потребуется afterevidence; отсутствие финального вердикта здесь явно оставлено открытым.']
(D/'coordination-findings.md').write_text('\n'.join(lines)+'\n');print('EXPLICIT sets',meta['current_named_count'],'current+',3,'judge+',80,'historical; each mapped')
