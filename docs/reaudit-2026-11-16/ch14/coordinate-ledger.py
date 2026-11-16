"""Reconcile named source observations against independent before review; no execution."""
from pathlib import Path
import json,re
D=Path(__file__).resolve().parent;o=json.loads((D/'coordination-initial.json').read_text());review=(D/'review-before.md').read_text();tables={}
for line in review.splitlines():
 if not line.startswith('| '):continue
 cells=[s.strip() for s in line.strip('|').split('|')]
 if len(cells)<3:continue
 key=cells[0].replace('Эксперт ','').strip()
 tables[key]={'before_decision':cells[1],'acceptance':cells[2]}
# Historical rows are reviewed in the dedicated historical section (same IDs as current expert).
historical_section=review.split('## Сверка исторического реестра')[-1]
if historical_section==review:
 # Heading wording may differ; match the section containing S14-01 and REVIEW-S14-01.
 for chunk in re.split(r'(?m)^## ',review):
  if '| REVIEW-S14-01 |' in chunk:historical_section=chunk;break
historical={}
for line in historical_section.splitlines():
 if not line.startswith('| '):continue
 c=[s.strip() for s in line.strip('|').split('|')]
 if len(c)>=3:historical[c[0]]={'before_decision':c[1],'acceptance':c[2]}
for r in o['source_ledger']['historical']:r['current_before_review']=historical.get(r['id'],{'before_decision':'pending explicit mapping','acceptance':'see source and review-before'})
# Expert IDs historically collide; current table precedes historical table.
current_tables={}
for line in review.splitlines():
 if not line.startswith('| '):continue
 c=[s.strip() for s in line.strip('|').split('|')]
 if len(c)<3:continue
 key=c[0].replace('Эксперт ','').strip();current_tables.setdefault(key,{'before_decision':c[1],'acceptance':c[2]})
for r in o['source_ledger']['current']:r['current_before_review']=current_tables.get(r['id'],{'before_decision':'pending explicit independent review','acceptance':'source observation retained, not silently closed'})
# Preserve post-initial observations separately with their actual independent source.
by_id={r['id']:r for r in o['source_ledger']['current']}
for ident,source,decision,acceptance in [
 ('ST-14-06','fixes/student/holdout-evaluation/review.md','Подтверждено деловым критиком в fixes/business.md; отдельный freshholdout','Frozen k2: singleton пустоты пропущен; метрики и ключи воспроизведены по732кадрам'),
 ('B14-05','fixes/business.md','P3: описка собственного текста ученика, не дефект source курса','Отдельный appendix самостоятельной сверки числителей с JSON/CSV без изменения первичных текстов'),
 ('E14-07','fixes/editor.md','Дополнительный предметный аспект эксперта, scoped прозовая редакция применена; независимое afterрешение pending','Убрать гарантию невозможности переобучить малую голову и безусловно огромных градиентов; проверить условную формулировку и способы контроля')]:
 if ident not in by_id:
  r={'source':source,'id':ident,'stage':'post-initial scoped evidence','after':'pending','current_before_review':{'before_decision':decision,'acceptance':acceptance}};o['source_ledger']['current'].append(r);by_id[ident]=r
by_id['ST-14-05']['current_before_review']={'before_decision':'Подтверждено бизнес-критиком с самостоятельным уточнением, fixes/business.md','acceptance':'Первый ответ45минсохранён; новый наблюдаемый эпизод после разрыва обнаружен через15мин, физическое состояние пропуска неизвестно'}
o['source_ledger']['current_count']=len(o['source_ledger']['current'])
(D/'source-ledger.json').write_text(json.dumps(o['source_ledger'],ensure_ascii=False,indent=2)+'\n')
lines=['# Поимённая сверка источников главы14','','Номер относится к источнику и версии, а не уникальному дефекту. Historical и current E14не объединяются. After пока не заявлен. Полные формулировки, основания и приёмка сохранены в JSON и review-before.','','## Исторические30','','| ID | Текущее независимое beforeрешение |','|---|---|']
for r in o['source_ledger']['historical']:lines.append('| '+r['id']+' | '+r['current_before_review']['before_decision']+' |')
lines+=['','## Нынешние'+str(len(o['source_ledger']['current'])),'','| Источник | ID | Beforeрешение рецензента |','|---|---|---|']
for r in o['source_ledger']['current']:lines.append('| '+r['source']+' | '+r['id']+' | '+r['current_before_review']['before_decision']+' |')
(D/'source-ledger.md').write_text('\n'.join(lines)+'\n');print('historical mapped',sum('pending' not in r['current_before_review']['before_decision'] for r in o['source_ledger']['historical']),'current mapped',sum('pending' not in r['current_before_review']['before_decision'] for r in o['source_ledger']['current']))

coverage=json.loads((D/'coverage.json').read_text());coverage['historical_source_ledger']=o['source_ledger']['historical'];coverage['current_source_ledger']=o['source_ledger']['current'];coverage['holdout_evidence']='coordination-holdout.json';coverage['pending']=['sourceREADY plus rootbuild/export','retake public package verified actualfinaldiff and publicHTML','same frozen guards/reviewer after','addressed student retake and own holdout numeric appendix','methodist after score and independent final review'];(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
