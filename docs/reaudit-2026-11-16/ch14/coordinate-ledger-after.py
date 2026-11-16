"""Attach publication review to every historical/current observation; learner retake pending."""
from pathlib import Path
import json,re
D=Path(__file__).resolve().parent;o=json.loads((D/'source-ledger.json').read_text());text=(D/'fixes/review.md').read_text();chunks=re.split(r'(?m)^## ',text);historical={};current={}
for chunk in chunks:
 table=historical if chunk.startswith('Старые записи') else current
 for line in chunk.splitlines():
  if not line.startswith('| '):continue
  c=[s.strip() for s in line.strip('|').split('|')]
  if len(c)<3:continue
  key=c[0].replace('Эксперт ','').split(',',1)[0].strip()
  if re.fullmatch(r'(?:[SME]14-\d+|REVIEW-S14-\d+|E14-03/\w+|E14-FEWSHOT|OCT14-\w+|REV14-LIGHT|RET14-[A-Z-]+|S14|REAUDIT14-[A-Z-]+|M14-26-\d+|B14-\d+|A14-\d+|REVIEW14-FLAT|Q14-\d+|ST-14-(?:H)?\d+)',key):table[key]={'decision':c[1],'evidence':c[2],'source':'fixes/review.md'}
for group,lookup in [('historical',historical),('current',current)]:
 for r in o[group]:
  r['publication_after_review']=lookup.get(r['id'],{'decision':'pending explicit mapping','evidence':'not silently accepted','source':'fixes/review.md'});r['after']='publication reviewed; addressed learner retake and final acceptance pending'
o['stage']='publication technical checks complete; learner38 active and excluded from final acceptance'
(D/'source-ledger.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
lines=['# Поимённая сверка главы 14','','Исторические и нынешние номера E14 имеют разные версии. Все сообщения, аспекты и повторные наблюдения сохранены. Сводный реестр не является числом уникальных дефектов. Техническая публикация проверена, адресное прохождение 38 целей ещё не закрыто.','','| Версия / источник | ID | Before | Проверка опубликованной редакции |','|---|---|---|---|']
for g in ['historical','current']:
 for r in o[g]:lines.append('| '+g+'/'+r['source']+' | '+r['id']+' | '+r['current_before_review']['before_decision']+' | '+r['publication_after_review']['decision']+': '+r['publication_after_review']['evidence']+' |')
(D/'source-ledger.md').write_text('\n'.join(lines)+'\n');coverage=json.loads((D/'coverage.json').read_text());coverage['historical_source_ledger']=o['historical'];coverage['current_source_ledger']=o['current'];coverage['completed_technical_after']='coordination-after.json';coverage['pending']=['student retake38 immutable freeze and full input/feedback/aggregate/Q1–4 reconciliation','new openparking/test answers and letter review','own holdout numerical appendix','methodist/business/reviewer final learner evidence acceptance'];(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print({g:{'rows':len(o[g]),'mapped':sum(r['publication_after_review']['decision']!='pending explicit mapping' for r in o[g])} for g in ['historical','current']})
