from pathlib import Path
import re,json,hashlib,shutil
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch15';W=Path('/private/tmp/kuch15round');T=W/'student-retest-v3-delta';M=D/'technical/release-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def parse(s):
 parts=re.split(r'(?m)(?=^## task: )',s);tasks={}
 for part in parts[1:]:
  z=re.split(r'(?m)^### (prompt|starter|setup|check|hint|solution|explain|parsons)[ \t]*$',part);i=z[0].split('## task: ')[1].split(' |')[0];item={'prompt':[z[0]]}
  for k,v in zip(z[1::2],z[2::2]):item.setdefault(k,[]).append(v)
  tasks[i]=item
 return parts[0],tasks
assert sha(W/'final-v3.json')=='14cca3e5bd70a4631b07932e8d774d39aeafd14d9fc14e86113189f9619b69fe'
assert not T.exists()and not M.exists();T.mkdir();M.mkdir()
before=(W/'retest-source/content/ch15/06-final-project.md').read_text();actual=(R/'content/ch15/06-final-project.md').read_text();bt,bs=parse(before);at,ass=parse(actual);assert bt==at;assert set(bs)==set(ass)
changes={i:sorted(k for k in set(bs[i])|set(ass[i])if bs[i].get(k)!=ass[i].get(k))for i in ass if bs[i]!=ass[i]};assert set(changes)=={'profit'};assert changes['profit']==['check','hint','prompt','solution','starter'];assert bs['profit']['setup']==ass['profit']['setup'];assert len(ass['profit']['hint'])==3
v2=json.loads((W/'final-v2.json').read_text());v3=json.loads((W/'final-v3.json').read_text());key=lambda r:(r['lesson'],r['kind'],r['id']);a={key(r):r for r in v2};b={key(r):r for r in v3};assert set(a)==set(b);ed={str(k):sorted(f for f in set(a[k])|set(b[k])if a[k].get(f)!=b[k].get(f))for k in a if a[k]!=b[k]};assert list(ed)==[str(('ch15/06-final-project','task','profit'))];assert list(ed.values())==[['check','solution','starter']]
public=ass['profit']['prompt'][0]+'\n### Заготовка\n'+''.join(ass['profit']['starter']);assert not re.search(r'^### (setup|check|hint|solution|explain)\s*$',public,re.M);assert '- [x]'not in public;(T/'06-profit.md').write_text(public)
(T/'README.md').write_text('''# Узкая замена карточки profit: v3

Основной208файловый пакет student-retest и отдельный139файловый student-project-revision остаются неизменными. Для единственной карточки06-final-project/profit используйте только условие и заготовку из06-profit.md вместо прежней карточки в основном пакете. Другие46браузерных целей и все перемешанные вопросы/нумерация прежние. Новых ключей или авторских решений здесь нет.

До первой отправки сохраните собственныеQ1–Q3 по обновлённому условию, после — полный ответ иQ4. Своё прежнее решение можно использовать явно, пересмотрев необходимое по новому контракту. Отправляйте прежнимsubmit.py из student-retest; код полностью заменяет редактор. Начинайте только после командыroot иCPUокна. Подсказки открываются по одной в интерфейсе после собственной попытки; в этом пакете их нет.
''')
# Only root hint metadata changes; public208 and answerkeys remain byte-identical.
hints=W/'hints-retest.json';oldh=json.loads(hints.read_text());newh=dict(oldh);newh['06-final-project/profit']=[v.strip()for v in ass['profit']['hint']];oldhsha=sha(hints);shutil.copyfile(hints,M/'hints-retest-before-v3.json');dump(hints,newh);assert {k for k in oldh if oldh[k]!=newh[k]}=={'06-final-project/profit'}
files={str(p.relative_to(T)):sha(p)for p in T.rglob('*')if p.is_file()};dump(M/'public-delta-manifest.json',{'status':'SEALED prepared delta only; root awaits11probe acceptance and owns dispatch','root':str(T),'files':files,'count':len(files),'replaces_only':'06-final-project/profit prompt+starter','new_answerkeys':False})
paths=list((R/'content/ch15').glob('*.md'))+list((R/'site/ch15').glob('*.html'))+list((R/'site/assets').glob('*'))+[R/'content/course.yaml',R/'site/notebooks/ch15-practice.ipynb',R/'site/notebooks/project-template.ipynb',R/'site/notebooks/dsc.py',R/'site/notebooks/check_notebook.py',R/'tools/build.py',R/'tools/build_notebooks.py']+[R/'site/data'/f for f in ['guests_churn.csv','office.db','service_log.jsonl']]
paths+=list((R/'content/figures').glob('service*.svg'))+[R/'content/figures/incident-timeline.svg'];paths=sorted(set(p for p in paths if p.is_file()))
dump(M/'release-manifest.json',{'publication':'v3','export_sha256':sha(W/'final-v3.json'),'sourceHTMLNBdataassets_sha256':{str(p.relative_to(R)):sha(p)for p in paths},'delta_source_fields':changes,'delta_export_fields':ed,'setup_identical':True,'neighbor_tasks_identical':True,'all_other_export_records_identical':True,'hints_count':3,'hints_root_only':{'before_sha256':oldhsha,'after_sha256':sha(hints),'changed_ids':['06-final-project/profit']},'bridge_addendum':{'bridge_sha256':sha(W/'bridge-retest.cjs'),'keys_retest_sha256':sha(W/'keys-retest.json'),'keys_unchanged':True,'public208_unchanged':'verified separately below','behavior':'same47targets;reload published profit card v3 before first send; root owns restart'},'student_project_revision139':'untouched','native_project95':'owned by student separate freeze; not modified/read here'})
for name,h in json.loads((D/'technical/retest-package/public-package-manifest.json').read_text())['files'].items():assert sha(W/'student-retest'/name)==h,name
manifest=json.loads((D/'technical/retest-package/project-revision-input.json').read_text());assert manifest['count']==139
for name,h in manifest['files'].items():assert sha(Path(manifest['root'])/name)==h,name
for f in json.loads((D/'student/initial-freeze-manifest.json').read_text())['files']:assert sha(D/'student'/f['path'])==f['sha256'],f['path']
for name,h in json.loads((D/'technical/public-package-manifest.json').read_text())['files'].items():assert sha(W/'student'/name)==h,name
print('SEALED2filev3delta;exactprofit-onlyscope verified; root-hintsonlyprofit; original83/128+208+139immutable; no browser/ML')
