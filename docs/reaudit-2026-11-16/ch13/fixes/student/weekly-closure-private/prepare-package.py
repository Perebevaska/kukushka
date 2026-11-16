"""One-ID public weekly closure generator; run only after root build/explicit SHA.
Never refresh student-retest or the72/73 frozen files. No ML/browser execution.
"""
import hashlib,json,re,shutil,sys
from pathlib import Path
ROOT=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=ROOT/'docs/reaudit-2026-11-16/ch13';W=Path('/private/tmp/kuch13round')
T=W/'student-weekly-closure';PRIVATE=D/'fixes/student/weekly-closure-private';OLD=D/'fixes/student/retest'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
if len(sys.argv) not in [2,3]:raise SystemExit('Usage: prepare-package.py ROOT_APPROVED_FINAL_EXPORT_SHA256 [EXPORT_PATH] (after build)')
expected=sys.argv[1];export=Path(sys.argv[2]) if len(sys.argv)==3 else W/'final.json';assert sha(export)==expected,'root-approved current export only'
# Snapshot source after root build; select exactly one public card.
p=ROOT/'content/ch13/05-project.md';s=p.read_text();parts=re.split(r'(?m)(?=^## task: )',s)
card=[b for b in parts[1:] if b.startswith('## task: weekly |')];assert len(card)==1
seg=re.split(r'(?m)^### (check|hint|solution|setup|explain|starter|parsons)[ \t]*$',card[0]);public=seg[0];hints=[]
for kind,body in zip(seg[1::2],seg[2::2]):
 if kind=='starter':public+='\n### Заготовка\n'+body
 if kind=='hint':hints.append(body.strip())
assert not re.search(r'(?m)^### (check|hint|solution|setup|explain)',public)
T.mkdir(exist_ok=True);(T/'weekly.md').write_text(public)
(T/'data').mkdir(exist_ok=True);(T/'own-previous').mkdir(exist_ok=True)
for q in (D/'technical/data-baseline').glob('*.csv'):shutil.copyfile(q,T/'data'/q.name)
# Only the learner's own selected files, never private keys/reports in frozen72.
for name in ['knowledge.md','05-project.input.jsonl','05-project.feedback.jsonl','05-project.weekly-retry.input.jsonl','05-project.weekly-retry.feedback.jsonl','own-scored.csv','own-weekly.csv']:
 shutil.copyfile(OLD/name,T/'own-previous'/name)
shutil.copyfile(W/'student-retest/submit.py',T/'submit.py')
(T/'targets.json').write_text('{"tasks":["05-project/weekly"],"questions":[]}\n')
(T/'README.md').write_text('''# Отдельная проверка weekly главы 13

После FINALREADY координатора прочитайте текущие weekly.md и starter, затем самостоятельно отправьте одну новую программу 05-project/weekly. Используйте только этот каталог, данные и свои прежние записи own-previous. Прежние input/feedback не изменяйте. Сохраните новую работу в отдельном fixes/student/weekly-closure.

До отправки Q1: цель; Q2: доступное действие и где объяснено; Q3: ожидаемые ключи/формы/единицы. После — полный Q4, следующий шаг и собственный вывод о текущем примере. Helper целиком заменяет редактор: включите все нужные imports и видимые строки starter. Формат JSONL lesson/task/code/expect/Q1/Q2/Q3. python3 submit.py input.jsonl > feedback.jsonl. Сохраните полный raw и реально откройте returned PNG перед его описанием. При затруднении после собственной попытки допустима одна UI hint; помощь учтите явно.

Перечитайте текущее условие и используйте опубликованный способ построения графика. Свой прежний код можно адаптировать, прямо указав повтор знакомого задания. Новое обучение или инференс не требуется: свои прежние прогнозы доступны в own-previous, а runtime даёт текущую карточку. Платные API и загрузки весов не нужны. Дождитесь CPU-окна и одной разрешённой сдачи от координатора. Не открывайте служебные файлы и чужие заключения; эта отдельная попытка не переписывает завершённый ретест.
''')
js(PRIVATE/'hints-private.json',{'05-project/weekly':hints})
manifest={str(q.relative_to(T)):sha(q) for q in T.rglob('*') if q.is_file()}
js(PRIVATE/'public-package-manifest.json',{'status':'HOLD until root FINALREADY/new bridge phase','export_sha256':expected,'export_path':str(export),'source_sha256':sha(p),'html_sha256':sha(ROOT/'site/ch13/05-project.html'),'tasks':['05-project/weekly'],'file_count':len(manifest),'files':manifest})
for base in [D/'student',OLD]:
 mm={l.split('  ',1)[1]:l.split('  ',1)[0] for l in (base/'SHA256SUMS').read_text().splitlines() if l.strip()};assert all(sha(base/n)==h for n,h in mm.items())
print('Prepared only05-project/weekly; preserved73+72; HOLD',expected)
