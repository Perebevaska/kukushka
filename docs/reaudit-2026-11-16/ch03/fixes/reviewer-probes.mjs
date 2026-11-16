import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const dir = 'docs/reaudit-2026-11-16/ch03';
const final = readFileSync(process.argv[2]);
const entries = JSON.parse(final);
const initial = JSON.parse(readFileSync(dir + '/check-evidence/tasks-before.json'));
const cases = JSON.parse(readFileSync(dir + '/check-evidence/probes-before.json'))
  .filter(c => c.case !== 'empty-answer');
const runtime = resolve('site/assets/vendor/pyodide') + '/';
const { loadPyodide } = await import(pathToFileURL(runtime + 'pyodide.mjs'));
const py = await loadPyodide({ indexURL: runtime });
await py.loadPackage(['pandas','openpyxl','matplotlib']);
py.FS.writeFile('/home/pyodide/harness.py',readFileSync('site/assets/harness.py'));
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import harness, pandas');
const run = py.pyimport('harness').run;
console.log('export', createHash('sha256').update(final).digest('hex'), 'Pyodide', py.version, py.runPython('sys.version.split()[0]+" pandas "+pandas.__version__'));
function invoke(t, c) {
  for (const f of t.files) py.FS.writeFile('/home/pyodide/' + f,readFileSync('site/data/' + f));
  if (c.prepare) py.runPython(c.prepare);
  const result = run(c.code, t.check, t.setup ?? null, false);
  const js = result.toJs({dict_converter:Object.fromEntries});
  result.destroy();
  if (!js.check && !js.error) throw Error('Нет вердикта');
  return !!js.check?.passed;
}
for (const [name, snapshot] of [['start',initial],['final',entries]]) {
  let mismatches = 0;
  for (const c of cases) {
    const t = snapshot.find(t=>t.kind==='task' && t.lesson==='ch03/'+c.lesson && t.id===c.task);
    const passed = invoke(t,c);
    if (passed !== c.expected) mismatches++;
    console.log(name,c.lesson+'/'+c.task,c.case,'expected',c.expected,'actual',passed);
  }
  console.log(name, 'match',cases.length-mismatches,'of',cases.length);
  if(name==='final' && mismatches)process.exitCode=1;
}
const t = entries.find(t=>t.kind==='task' && t.lesson==='ch03/03b-excel' && t.id==='plan-fact');
const setupCode = `import pandas as pd
m = "Янв Фев Мар Апр Май Июн Июл Авг Сен".split()
def body(df):
    return df.set_index("Код").drop(index="Итого")[m]
p = body(pd.read_excel("zerno_finance.xlsx", sheet_name="План", header=3))
f = body(pd.read_csv("finance_fact.csv", sep=";", decimal=",", header=4))
ps, fs = p.sum(axis="columns"), f.sum(axis="columns")
`;
const full = 'p.count(axis=1).eq(9) & f.count(axis=1).eq(9) & ps.gt(0)';
const variants = [
  ['полная проверка count',full,true],
  ['сумма неполного факта','p.count(axis=1).eq(9) & ps.gt(0)',false],
  ['ноль ошибочно означает пропуск',full+' & f.ne(0).all(axis=1)',false],
];
const mutation = `import csv, openpyxl
with open("finance_fact.csv",encoding="utf-8-sig") as s: rr=list(csv.reader(s,delimiter=";"))
rows=[r for r in rr[5:] if r and r[0]!="Итого"]
for month in "Янв Фев Мар Апр Май Июн Июл Авг Сен".split(): rows[0][rr[4].index(month)]="0"
rows[1][rr[4].index("Июн")]=""
rows[2][rr[4].index("Авг")]="0"
with open("finance_fact.csv","w",newline="",encoding="utf8") as s: csv.writer(s,delimiter=";").writerows(rr[:5]+list(reversed(rr[5:])))
b=openpyxl.load_workbook("zerno_finance.xlsx"); sheet=b["План"]
target=next(i for i in range(5,sheet.max_row+1) if sheet.cell(i,1).value==rows[3][0]);sheet.cell(target,7).value=None
b.save("zerno_finance.xlsx")
`;
for(const [name,filter,expected] of variants){
  const code=setupCode+'ok = '+filter+'\ndone = (fs[ok].div(ps[ok])*100).round(1).sort_index(ascending=False)\nworst = done.idxmin()';
  const actual=invoke(t,{code,prepare:mutation});
  console.log('перенос plan-fact',name,'expected',expected,'actual',actual);
  if(actual!==expected)process.exitCode=1;
}
const headers = entries.find(t=>t.kind==='task' && t.lesson==='ch03/03b-excel' && t.id==='auto-header');
const shifted = `import openpyxl
w=openpyxl.load_workbook('zerno_finance.xlsx')
for s,k in [('План',5),('Факт',2)]:
    w[s].insert_rows(1,k)
w.save('zerno_finance.xlsx')`;
const readHeaders = `import pandas as pd
months="Янв Фев Мар Апр Май Июн Июл Авг Сен".split()
heads={}
sums={}
for s in ['Факт','План']:
    raw=pd.read_excel('zerno_finance.xlsx', sheet_name=s,header=None)
    heads[s]=next(i for i,x in raw.iloc[:,0].items() if x=='Код')
    frame=pd.read_excel('zerno_finance.xlsx', sheet_name=s,header=heads[s]).set_index('Код').drop('Итого')
    sums[s.lower()]=frame[months].T.sum()
pf=pd.DataFrame(sums).round(1).iloc[::-1]`;
const logTask=entries.find(t=>t.kind==='task' && t.lesson==='ch03/08-pipeline' && t.id==='log');
const changedLog = `import pandas as pd
src=pd.read_csv('clients_raw.csv').iloc[:2].copy()
latest=src.iloc[[0]].assign(signup_date='2026-12-25', city='Другой город')
pd.concat([latest,src,latest],ignore_index=True).to_csv('clients_raw.csv',index=False)`;
const cleanLog = `def clean_with_log(raw):
    unique=raw.drop_duplicates()
    norm=unique.assign(client_id=unique.client_id.str.strip().str.upper())
    latest=norm.loc[norm.groupby('client_id')['signup_date'].idxmax()].copy()
    log=list(zip(['загрузка','копии','ключ','версия'],map(len,[raw,unique,norm,latest])))
    return latest,log`;
for(const [task, name, code, prepare, expected] of [
  [headers,'разные шапки +5/+2, обратный порядок',readHeaders,shifted,true],
  [headers,'найден один заголовок для всех',readHeaders.replace("header=heads[s]","header=heads['Факт']"),shifted,false],
  [logTask,'журнал сохраняется с новой версией',cleanLog,changedLog,true],
  [logTask,'журнал правильный, выбрана старая версия',cleanLog.replace(".idxmax()",".idxmin()"),changedLog,false],
]){
  const actual=invoke(task,{code,prepare});
  console.log('собственный перенос',task.id,name,'expected',expected,'actual',actual);
  if(actual!==expected)process.exitCode=1;
}
