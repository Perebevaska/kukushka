// Run in the repository root with the path to a fresh tools/build.py --export file.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
const read = file => readFileSync(resolve(file), 'utf8')
const tasks = JSON.parse(read(process.argv[2]))
const vendor = resolve('site/assets/vendor/pyodide') + '/'
const { loadPyodide } = await import(pathToFileURL(vendor + 'pyodide.mjs').href)
const py = await loadPyodide({ indexURL: vendor })
await py.loadPackage(['pandas','openpyxl'],{messageCallback() {}})
py.FS.writeFile('/home/pyodide/_dsc_harness.py',read('site/assets/harness.py'))
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import _dsc_harness')
const run = py.pyimport('_dsc_harness').run
console.log('Node',process.version,'Pyodide',py.version,py.runPython('import pandas, openpyxl; (sys.version.split()[0], pandas.__version__, openpyxl.__version__)').toJs())

function probe(lesson, id, name, build, editFile = null) {
    const task = tasks.find(t => t.lesson === 'ch03/' + lesson && t.kind === 'task' && t.id === id)
    for (const file of task.files) {
        py.FS.writeFile(file, readFileSync(resolve('site/data',file)))
    }
    if (editFile) py.runPython(editFile)
    const out = run(build(task.solution),task.check,task.setup,true)
    const result = out.toJs({dict_converter:Object.fromEntries})
    out.destroy()
    console.log(lesson,id,name,result.check?.passed ?? false,result.check?.msg ?? result.error?.text ?? '')
}
const same = code => code
const ext = `import pandas as pd
raw = pd.read_csv('clients_raw.csv')
raw.loc[raw.client_id == 'C1000', 'phone'] = '+7 912 345-67-89 доб. 12'
raw.to_csv('clients_raw.csv',index=False)`
probe('05-strings','phone10','base',same)
probe('05-strings','phone10','extension-accepted',same,ext)
probe('05-strings','phone10','extension-rightly-masked',code => code.replace('df["phone10"] = df["phone"].str.replace(r"\\D", "", regex=True).str[-10:]','digits = df["phone"].str.replace(r"\\D","",regex=True)\ndf["phone10"] = digits.where(digits.str.fullmatch(r"[78]?\\d{10}")).str[-10:]'),ext)
probe('09-project','clean','baseline',same)
probe('09-project','clean','correct-rejection-of-extension',same,ext)
probe('09-project','age','age-of-another-person',code=>code+'\nclients["age"] = clients["age"].shift(1)\nclients["age_group"] = clients["age_group"].shift(1)')
probe('09-project','guests','alternative-correct',code=>code.replace('("order_id", "count")','("order_id", "nunique")'))
probe('09-project','guests','cups-instead-of-orders',code=>code.replace('("order_id", "count")','("qty", "sum")'))
probe('09-project','sources','one-source-without-revenue',code=>code+'\nby_source.loc[by_source.index[0],"avg_revenue"] = float("nan")')
probe('09-project','age-money','one-age-band-without-orders',code=>code+'\nby_age.loc[by_age.index[0],"avg_orders"] = float("nan")')
probe('09-project','report','correct',same)
probe('09-project','report','ignores-raw',code=>code.replace('clients = clean_clients(raw)','clients = clean_clients(pd.read_csv("clients_raw.csv"))'))
probe('03b-excel','auto-header','dynamic-index',same)
probe('03b-excel','auto-header','hardcoded-counts',code=>code.replace('sheet[sheet[0] == "Код"].index[0]','{"План": 3, "Факт": 4}[name]'))
probe('03b-excel','auto-header','alternative-dynamic-lookup',code=>code.replace('sheet[sheet[0] == "Код"].index[0]','sheet[0].eq("Код").idxmax()'))
// Simulate the learner's extra notebook in its own in-memory folder, then reopen the file it exports.
py.FS.mkdir('expert-excel')
py.FS.chdir('expert-excel')
py.FS.writeFile('zerno_finance.xlsx', readFileSync(resolve('site/data/zerno_finance.xlsx')))
const nb = JSON.parse(read('site/notebooks/extra/ch03-excel.ipynb'))
for (const c of nb.cells.filter(c => c.cell_type === 'code')) {
    const src = c.source.join('')
        .replace('fact_h = None', 'fact_h = pd.read_excel(BOOK,sheet_name="Факт",header=4,usecols="A,D:L")')
        .replace('sheets = None', 'sheets = list(book)')
        .replace('weak = None', 'weak = [m for m in MONTHS if f"{m}" in body and body[m].sum() / plan.loc[plan["Код"] != "Итого",m].sum() < .97]')
    py.runPython(src)
}
console.log('notebook-export',py.runPython('list(pd.read_excel("plan_fact_report.xlsx",sheet_name=None))').toJs())
py.FS.chdir('/home/pyodide')
probe('02-missing','mechanism','structural-missing-correct-description',code=>code.replace('"MAR"','"средний чек не определён без визитов"'))
console.log('observed-default',py.runPython('t = pd.DataFrame({"g": pd.Categorical(["A"],categories=["A","B"]) }); (list(t.groupby("g").size().index), list(t.groupby("g",observed=False).size().index))').toJs())
const src = tasks.find(t=>t.lesson === 'ch03/09-project' && t.id==='clean').solution.split('raw = pd.read_csv(')[0]
console.log('age-edges',py.runPython(src + '\nbirth = pd.Series(["2012-12-01","1926-11-30","1926-12-01"]); age = 2026 - pd.to_datetime(birth).dt.year - (pd.to_datetime(birth).dt.strftime("%m%d") > "1201"); print(list(age), list(parse_birth(birth).notna()), list(pd.cut(age,[14,25,35,45,60,100],right=False).notna())); None'))
