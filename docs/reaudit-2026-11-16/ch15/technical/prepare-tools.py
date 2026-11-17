from pathlib import Path
import json,re,shutil,hashlib,subprocess,datetime
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');W=Path('/private/tmp/kuch15round');D=R/'docs/reaudit-2026-11-16/ch15'
s=Path('/private/tmp/kuch14round/bridge.cjs').read_text().replace('kuch14round','kuch15round').replace('ch14','ch15').replace('55584','55585')
s=s.replace("const w='/private/tmp/kuch15round',", "const w='/private/tmp/kuch15round', jobdir=w+'/jobs',")
s=s.replace("fs.readdirSync(w+'/jobs')","fs.readdirSync(jobdir)").replace("const job=w+'/jobs/'+f","const job=jobdir+'/'+f")
assert "card.locator('.task-ui .CodeMirror').first()" in s
assert 'assert.equal(await cm.evaluate(e=>e.CodeMirror.getValue()),r.code)' in s
(W/'bridge.cjs').write_text(s)
s=Path('/private/tmp/kuch14round/public-figures.cjs').read_text().replace('kuch14round','kuch15round');(W/'public-figures.cjs').write_text(s)
for src,name in [(W/'prepare.py','prepare-package.py'),(W/'bridge.cjs','bridge-initial.cjs'),(W/'public-figures.cjs','public-figures.cjs')]:shutil.copyfile(src,D/'technical'/name)
origins=sorted((R/'docs/audit-2026-11-13/ch15').glob('*.md'))+sorted((R/'docs/course-improvements/ch15').glob('*.md'))+[R/'docs/course-improvements/reaudit'/x for x in ['expert.md','review.md','methodist.md','report.md','student/feedback.md','fixes/report.md','fixes/review/ch15.md']]
origins += list((R/'docs/audit-2026-10-15').glob('15-*.md'))
rows=[]
def add(i,role,p,text):
 rows.append({'id':i,'role':role,'source':str(p.relative_to(R)),'full_finding':text,'historical_status':'See full historical finding and later acceptance; not current execution','current_status':'pending independent current evidence'})
for p in origins:
 text=p.read_text();dest=D/'historical'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 if p.parent==R/'docs/audit-2026-11-13/ch15':
  if p.name=='student.md':
   for match in re.finditer(r'(?ms)^- \*\*(S15-\d+).*?(?=^- \*\*S15-|\Z)',text):add(match[1],'student',p,match[0].strip())
  elif p.name=='review.md':
   for match in re.finditer(r'(?ms)^### (S15-\d+).*?(?=^### |^## |\Z)',text):add('REVIEW-'+match[1],'reviewer',p,match[0].strip())
  elif p.name=='methodist.md':
   for match in re.finditer(r'(?ms)^\d+\. \*\*(M15-\d+).*?(?=^\d+\. \*\*M15-|^## |\Z)',text):add(match[1],'methodist',p,match[0].strip())
  elif p.name=='expert.md':
   # Original expert did not assign IDs: retain every finding paragraph, not just P headings.
   paras=[x.strip() for x in text.split('\n\n') if x.strip() and not x.startswith('#') and not x.startswith('```')]
   for j,paragraph in enumerate(paras,1):add('E15-P%02d'%j,'expert',p,paragraph)
  elif p.name=='project-review.md':
   for j,part in enumerate(re.split(r'(?m)(?=^## )',text),1):add('PROJECT15-REVIEW-%02d'%j,'reviewer',p,part.strip())
 elif 'course-improvements/ch15' in str(p):
  for j,part in enumerate(re.split(r'(?m)(?=^## )',text),1):add('RETEST15-'+p.stem+'-%02d'%j,{'methodist':'methodist','review':'reviewer','student-retest':'student'}.get(p.stem,'editor/checks'),p,part.strip())
 else:
  # Multi-chapter sources remain complete in historical. Include own chapter sections/rows in ledger.
  if p.name=='feedback.md':
   parts=[line for line in text.splitlines() if line.startswith('|15|')]
  elif p.name=='methodist.md':
   sections=re.split(r'(?m)(?=^#{2,3} )',text)
   parts=[part for part in sections if re.search(r'^#{2,3} .*15[. ]',part)]
  else:parts=[part for part in text.split('\n\n') if re.search(r'ch15|Гл\. 15|S15\b|T12\b|15\. Выпуск|15\. От журнала',part)]
  for j,part in enumerate(parts,1):add('REAUDIT15-'+p.parent.name+'-'+p.stem+'-%02d'%j,'mixed historical independent roles',p,part.strip())
(D/'previous.json').write_text(json.dumps({'meaning':'Per-role original IDs and full finding excerpts, no inherited closed verdicts; unnumbered expert paragraphs use local stable IDs. Full sources archived.','rows':rows,'full_sources':[str(p.relative_to(R)) for p in origins]},ensure_ascii=False,indent=2)+'\n')
lines=['# Предыдущие замечания главы 15','','Только глава15, baseline740b115. Исторические решения не заменяют текущую проверку. Сохраняются отдельно сообщения ученика, решения рецензента, замечания методиста и полные предметные наблюдения. Ненумерованные предметные абзацы получили локальные E15-P IDs; строки таблиц не считаются отдельными уникальными дефектами. Полные источники в historical/ и полные фрагменты в previous.json. Ученик их не получает.','','| ID | Роль | Источник |','|---|---|---|']
for row in rows:lines.append('| '+row['id']+' | '+row['role']+' | ['+row['source']+'](historical/'+row['source']+') |')
lines+=['','Особенно сохранены: S15-01…05; M15-01…05; исходное project-review до/после реальной сдачи; передача control20 в другом процессе; неизвестные метки; собственный поздний тест; сценарии фиксированного списка и переотбора; T12 guard0/−1/две ошибки; пакет с лимитом3; отдельно неподтверждённый Docker и эффект звонков.','', '[Полный построчный реестр](previous.json).']
(D/'previous.md').write_text('\n'.join(lines)+'\n')
# No heavy imports: package version metadata only.
code="import importlib.metadata as m,json,platform;print(json.dumps({'python':platform.python_version(),'packages':{p:m.version(p) for p in ['pandas','numpy','scikit-learn','joblib','mlflow','skops','fastapi','pydantic','httpx','uvicorn']}},indent=2))"
metadata=json.loads(subprocess.check_output(['/private/tmp/ku-audit/nb-env/bin/python','-c',code],text=True))
metadata.update({'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution':'metadata only, no imported ML libraries','docker_cli':shutil.which('docker'),'podman_cli':shutil.which('podman'),'colima_cli':shutil.which('colima')})
(D/'technical/environment-before.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('historical files',len(origins),'full finding rows',len(rows));print(json.dumps(metadata,indent=2))
